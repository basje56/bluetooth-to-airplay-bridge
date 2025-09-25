"""Audio engine for Bluetooth to AirPlay Bridge using async libraries."""
from __future__ import annotations

import asyncio
import logging
import os
import signal
import tempfile
import time
from typing import Any, Callable, Optional
import aiohttp
import aiofiles

_LOGGER = logging.getLogger(__name__)

# Audio codecs supported
SUPPORTED_CODECS = {
    'sbc': {'name': 'SBC', 'quality': 'standard', 'bitrate': '328'},
    'aac': {'name': 'AAC', 'quality': 'high', 'bitrate': '256'},
    'aptx': {'name': 'aptX', 'quality': 'premium', 'bitrate': '352'},
    'ldac': {'name': 'LDAC', 'quality': 'premium', 'bitrate': '990'}
}

class AudioEngine:
    """Manages audio capture from Bluetooth and streaming to AirPlay using async libraries."""
    
    def __init__(self, bluetooth_address: str, airplay_name: str) -> None:
        """Initialize the audio engine."""
        self._bluetooth_address = bluetooth_address
        self._airplay_name = airplay_name
        self._is_running = False
        self._audio_callback: Optional[Callable] = None
        self._current_codec = 'sbc'
        self._sample_rate = 44100
        self._channels = 2
        self._capture_process: Optional[asyncio.subprocess.Process] = None
        self._stream_task: Optional[asyncio.Task] = None
        self._temp_audio_file: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        _LOGGER.info("Audio engine initialized with async libraries (no GStreamer dependency)")
            
    async def start_audio_capture(self) -> bool:
        """Start capturing audio from Bluetooth device using PulseAudio."""
        try:
            # Check if Bluetooth audio source is available
            if not await self.check_bluetooth_audio_available():
                _LOGGER.error("Bluetooth audio source not available")
                return False
            
            # Create temporary file for audio stream
            self._temp_audio_file = os.path.join(
                tempfile.gettempdir(), 
                f"airplay_audio_{self._airplay_name.replace(' ', '_')}.raw"
            )
            
            # Start audio capture using parec (PulseAudio record)
            source_name = f"bluez_source.{self._bluetooth_address.replace(':', '_')}.a2dp_source"
            
            cmd = [
                "parec",
                "--device", source_name,
                "--format", "s16le",
                "--rate", str(self._sample_rate),
                "--channels", str(self._channels),
                "--file-format", "raw",
                self._temp_audio_file
            ]
            
            _LOGGER.debug("Starting audio capture with command: %s", " ".join(cmd))
            
            self._capture_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Start streaming task
            self._stream_task = asyncio.create_task(self._stream_audio())
            
            self._is_running = True
            _LOGGER.info("Audio capture started successfully using PulseAudio")
            return True
            
        except Exception as err:
            _LOGGER.error("Failed to start audio capture: %s", err)
            await self._cleanup()
            return False
            
    async def stop_audio_capture(self) -> None:
        """Stop audio capture."""
        try:
            self._is_running = False
            
            # Cancel streaming task
            if self._stream_task and not self._stream_task.done():
                self._stream_task.cancel()
                try:
                    await self._stream_task
                except asyncio.CancelledError:
                    pass
            
            # Stop capture process
            if self._capture_process:
                try:
                    self._capture_process.terminate()
                    await asyncio.wait_for(self._capture_process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    _LOGGER.warning("Audio capture process did not terminate gracefully, killing")
                    self._capture_process.kill()
                    await self._capture_process.wait()
                except ProcessLookupError:
                    pass  # Process already terminated
            
            await self._cleanup()
            _LOGGER.info("Audio capture stopped")
            
        except Exception as err:
            _LOGGER.error("Error stopping audio capture: %s", err)
            
    async def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Close HTTP session
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None
            
            # Remove temporary file
            if self._temp_audio_file and os.path.exists(self._temp_audio_file):
                try:
                    os.unlink(self._temp_audio_file)
                except OSError:
                    pass
                self._temp_audio_file = None
                
        except Exception as err:
            _LOGGER.error("Error during cleanup: %s", err)
            
    async def _stream_audio(self) -> None:
        """Stream audio data to AirPlay endpoint."""
        try:
            # Create HTTP session for streaming
            self._session = aiohttp.ClientSession()
            
            # Wait for audio file to be created and have some data
            await asyncio.sleep(1)
            
            while self._is_running and self._temp_audio_file:
                try:
                    if os.path.exists(self._temp_audio_file):
                        # Read audio data from temporary file
                        async with aiofiles.open(self._temp_audio_file, 'rb') as f:
                            audio_data = await f.read(4096)  # Read in chunks
                            
                        if audio_data and self._audio_callback:
                            # Call the audio callback with the data
                            await self._audio_callback(audio_data)
                            
                    await asyncio.sleep(0.1)  # Small delay to prevent excessive CPU usage
                    
                except Exception as err:
                    _LOGGER.error("Error streaming audio: %s", err)
                    await asyncio.sleep(1)  # Wait before retrying
                    
        except Exception as err:
            _LOGGER.error("Error in audio streaming task: %s", err)
            
    async def set_codec(self, codec: str) -> bool:
        """Set the audio codec for Bluetooth connection."""
        if codec not in SUPPORTED_CODECS:
            _LOGGER.error("Unsupported codec: %s", codec)
            return False
            
        try:
            # Stop current capture
            was_running = self._is_running
            if was_running:
                await self.stop_audio_capture()
                
            self._current_codec = codec
            _LOGGER.info("Audio codec set to: %s", SUPPORTED_CODECS[codec]['name'])
            
            # Restart capture with new codec
            if was_running:
                return await self.start_audio_capture()
                
            return True
            
        except Exception as err:
            _LOGGER.error("Error setting codec: %s", err)
            return False
            
    async def set_audio_quality(self, sample_rate: int, channels: int) -> bool:
        """Set audio quality parameters."""
        try:
            if sample_rate not in [44100, 48000, 96000]:
                _LOGGER.error("Unsupported sample rate: %s", sample_rate)
                return False
                
            if channels not in [1, 2]:
                _LOGGER.error("Unsupported channel count: %s", channels)
                return False
                
            # Stop current capture
            was_running = self._is_running
            if was_running:
                await self.stop_audio_capture()
                
            self._sample_rate = sample_rate
            self._channels = channels
            
            _LOGGER.info("Audio quality set to: %dHz, %d channels", sample_rate, channels)
            
            # Restart capture with new settings
            if was_running:
                return await self.start_audio_capture()
                
            return True
            
        except Exception as err:
            _LOGGER.error("Error setting audio quality: %s", err)
            return False
            
    def get_audio_info(self) -> dict[str, Any]:
        """Get current audio configuration info."""
        return {
            'codec': self._current_codec,
            'codec_name': SUPPORTED_CODECS.get(self._current_codec, {}).get('name', 'Unknown'),
            'sample_rate': self._sample_rate,
            'channels': self._channels,
            'is_running': self._is_running,
            'bluetooth_address': self._bluetooth_address,
            'airplay_name': self._airplay_name,
            'engine_type': 'async_pulseaudio'
        }
    
    async def _check_pactl_available(self) -> bool:
        """Check if pactl command is available and working."""
        try:
            process = await asyncio.create_subprocess_exec(
                "pactl", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                version_info = stdout.decode().strip()
                _LOGGER.debug("PulseAudio pactl available: %s", version_info)
                return True
            else:
                _LOGGER.warning("pactl command failed: %s", stderr.decode())
                return False
                
        except FileNotFoundError:
            _LOGGER.error("pactl command not found - PulseAudio not installed")
            return False
        except Exception as err:
            _LOGGER.error("Error checking pactl availability: %s", err)
            return False
    
    async def _get_bluetooth_source_name(self) -> str:
        """Get the PulseAudio source name for the Bluetooth device."""
        # Standard BlueZ source naming convention
        mac_formatted = self._bluetooth_address.replace(':', '_')
        return f"bluez_source.{mac_formatted}.a2dp_source"
    
    async def _execute_pactl_command(self, args: list[str]) -> tuple[bool, str, str]:
        """Execute a pactl command and return success status, stdout, stderr."""
        try:
            if not await self._check_pactl_available():
                return False, "", "pactl not available"
            
            cmd = ["pactl"] + args
            _LOGGER.debug("Executing pactl command: %s", " ".join(cmd))
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            success = process.returncode == 0
            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()
            
            if not success:
                _LOGGER.warning("pactl command failed: %s", stderr_str)
            
            return success, stdout_str, stderr_str
            
        except Exception as err:
            _LOGGER.error("Error executing pactl command: %s", err)
            return False, "", str(err)
    
    async def check_bluetooth_audio_available(self) -> bool:
        """Check if Bluetooth audio source is available in PulseAudio."""
        try:
            success, stdout, _ = await self._execute_pactl_command(["list", "sources", "short"])
            
            if not success:
                _LOGGER.error("Failed to list PulseAudio sources")
                return False
            
            source_name = await self._get_bluetooth_source_name()
            is_available = source_name in stdout
            
            if is_available:
                _LOGGER.info("Bluetooth audio source found: %s", source_name)
            else:
                _LOGGER.warning("Bluetooth audio source not found: %s", source_name)
                _LOGGER.debug("Available sources:\n%s", stdout)
            
            return is_available
            
        except Exception as err:
            _LOGGER.error("Error checking Bluetooth audio availability: %s", err)
            return False
    
    async def get_bluetooth_volume(self) -> float:
        """Get current Bluetooth device volume (0.0-1.0)."""
        try:
            success, stdout, _ = await self._execute_pactl_command(["list", "sources"])
            
            if not success:
                _LOGGER.error("Failed to get source information")
                return 0.5
            
            source_name = await self._get_bluetooth_source_name()
            lines = stdout.split('\n')
            
            # Parse PulseAudio source list to find our device
            current_source = None
            for i, line in enumerate(lines):
                if "Source #" in line:
                    current_source = None
                elif current_source is None and f"Name: {source_name}" in line:
                    current_source = source_name
                elif current_source == source_name and "Volume:" in line:
                    # Parse volume line: "Volume: front-left: 65536 / 100% / 0.00 dB"
                    try:
                        # Find percentage values
                        parts = line.split()
                        for part in parts:
                            if part.endswith('%'):
                                volume_percent = int(part.rstrip('%'))
                                volume = max(0.0, min(1.0, volume_percent / 100.0))
                                _LOGGER.debug("Bluetooth volume: %d%% (%.2f)", volume_percent, volume)
                                return volume
                    except (ValueError, IndexError) as err:
                        _LOGGER.warning("Failed to parse volume from line '%s': %s", line, err)
                        break
            
            _LOGGER.warning("Could not find volume for Bluetooth source: %s", source_name)
            return 0.5
            
        except Exception as err:
            _LOGGER.error("Error getting Bluetooth volume: %s", err)
            return 0.5
    
    async def set_bluetooth_volume(self, volume: float) -> bool:
        """Set Bluetooth device volume (0.0-1.0)."""
        try:
            # Validate and clamp volume
            volume = max(0.0, min(1.0, volume))
            volume_percent = int(volume * 100)
            
            source_name = await self._get_bluetooth_source_name()
            
            # Set volume using pactl
            success, _, stderr = await self._execute_pactl_command([
                "set-source-volume", 
                source_name, 
                f"{volume_percent}%"
            ])
            
            if success:
                _LOGGER.info("Set Bluetooth volume to %d%% (%.2f)", volume_percent, volume)
                return True
            else:
                _LOGGER.error("Failed to set Bluetooth volume: %s", stderr)
                return False
                
        except Exception as err:
            _LOGGER.error("Error setting Bluetooth volume: %s", err)
            return False
    
    async def get_bluetooth_source_info(self) -> dict[str, Any]:
        """Get detailed information about the Bluetooth audio source."""
        try:
            success, stdout, _ = await self._execute_pactl_command(["list", "sources"])
            
            if not success:
                return {}
            
            source_name = await self._get_bluetooth_source_name()
            lines = stdout.split('\n')
            
            # Parse source information
            info = {}
            current_source = None
            
            for line in lines:
                line = line.strip()
                if "Source #" in line:
                    current_source = None
                elif current_source is None and f"Name: {source_name}" in line:
                    current_source = source_name
                    info['name'] = source_name
                elif current_source == source_name:
                    if line.startswith("Description:"):
                        info['description'] = line.split(":", 1)[1].strip()
                    elif line.startswith("Sample Specification:"):
                        info['sample_spec'] = line.split(":", 1)[1].strip()
                    elif line.startswith("Channel Map:"):
                        info['channel_map'] = line.split(":", 1)[1].strip()
                    elif line.startswith("State:"):
                        info['state'] = line.split(":", 1)[1].strip()
                    elif "Volume:" in line:
                        info['volume_line'] = line
                    elif line.startswith("Latency:"):
                        info['latency'] = line.split(":", 1)[1].strip()
            
            return info
            
        except Exception as err:
            _LOGGER.error("Error getting Bluetooth source info: %s", err)
            return {}
    
    def set_audio_callback(self, callback: Callable[[bytes], None]) -> None:
        """Set callback function for audio data."""
        self._audio_callback = callback
        
    async def get_audio_latency(self) -> float:
        """Get estimated audio latency in milliseconds."""
        try:
            source_info = await self.get_bluetooth_source_info()
            
            if 'latency' in source_info:
                latency_str = source_info['latency']
                try:
                    # Parse latency string like "123456 usec"
                    if 'usec' in latency_str:
                        usec = int(latency_str.split()[0])
                        latency_ms = usec / 1000.0
                        _LOGGER.debug("Bluetooth audio latency: %.1f ms", latency_ms)
                        return latency_ms
                except (ValueError, IndexError):
                    _LOGGER.warning("Failed to parse latency: %s", latency_str)
            
            # Default latency estimate for Bluetooth A2DP
            default_latency = 150.0
            _LOGGER.debug("Using default Bluetooth latency: %.1f ms", default_latency)
            return default_latency
            
        except Exception as err:
            _LOGGER.error("Error getting audio latency: %s", err)
            return 150.0