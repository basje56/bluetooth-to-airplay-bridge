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
        self._pactl_method: Optional[str] = None  # Will be set by _check_pactl_available
        
        _LOGGER.info("Audio engine initialized with async libraries (no GStreamer dependency)")
            
    async def start_audio_capture(self) -> bool:
        """Start capturing audio from Bluetooth device using PulseAudio."""
        try:
            _LOGGER.info("Starting audio capture for Bluetooth device %s", self._bluetooth_address)
            
            # Initialize pactl method detection if not already done
            if self._pactl_method is None:
                _LOGGER.debug("Initializing pactl method detection...")
                if not await self._check_pactl_available():
                    _LOGGER.error(
                        "Cannot start audio capture: No pactl method available. "
                        "Please ensure PulseAudio is properly configured in your Home Assistant environment."
                    )
                    return False
            
            # Check if Bluetooth audio source is available
            _LOGGER.debug("Checking if Bluetooth audio source is available...")
            if not await self.check_bluetooth_audio_available():
                _LOGGER.error(
                    "Cannot start audio capture: Bluetooth audio source not available. "
                    "Please ensure the Bluetooth device is connected and audio is active."
                )
                return False
            
            # Create temporary file for audio stream
            self._temp_audio_file = os.path.join(
                tempfile.gettempdir(), 
                f"airplay_audio_{self._airplay_name.replace(' ', '_')}.raw"
            )
            _LOGGER.debug("Using temporary audio file: %s", self._temp_audio_file)
            
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
            
            _LOGGER.info("Starting audio capture with command: %s", " ".join(cmd))
            
            try:
                self._capture_process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Give the process a moment to start and check if it's still running
                await asyncio.sleep(0.1)
                if self._capture_process.returncode is not None:
                    # Process has already exited
                    stdout, stderr = await self._capture_process.communicate()
                    _LOGGER.error(
                        "Audio capture process exited immediately (exit code: %d). "
                        "Error: %s. This may indicate the audio source is not available or parec is not installed.",
                        self._capture_process.returncode,
                        stderr.decode().strip() if stderr else "No error output"
                    )
                    return False
                
            except FileNotFoundError:
                _LOGGER.error(
                    "Failed to start audio capture: 'parec' command not found. "
                    "Please ensure PulseAudio utilities are installed in your Home Assistant environment."
                )
                return False
            except Exception as proc_err:
                _LOGGER.error("Failed to start audio capture process: %s", proc_err)
                return False
            
            # Start streaming task
            self._stream_task = asyncio.create_task(self._stream_audio())
            
            self._is_running = True
            _LOGGER.info(
                "Audio capture started successfully using PulseAudio (method: %s, source: %s)",
                self._pactl_method,
                source_name
            )
            return True
            
        except Exception as err:
            _LOGGER.error(
                "Failed to start audio capture for device %s: %s. "
                "This may indicate a configuration issue with PulseAudio or the Bluetooth audio system.",
                self._bluetooth_address,
                err
            )
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
    
    async def _detect_ha_environment(self) -> str:
        """Detect the Home Assistant environment type."""
        # First check if we're running inside a Home Assistant container
        try:
            with open("/proc/1/cgroup", "r") as f:
                cgroup_content = f.read()
                if "homeassistant" in cgroup_content or "hassio" in cgroup_content:
                    _LOGGER.debug("Detected running inside Home Assistant container")
                    # Check if this is HAOS by looking for supervisor socket
                    if os.path.exists("/run/supervisor.sock") or os.path.exists("/var/run/supervisor.sock"):
                        _LOGGER.debug("Detected HAOS environment (supervisor socket found)")
                        return "haos"
                    return "container"
        except Exception as err:
            _LOGGER.debug("Error checking container environment: %s", err)
        
        try:
            # Check for HAOS by looking for hassio_audio container (only works from host)
            process = await asyncio.create_subprocess_exec(
                "docker", "ps", "--filter", "name=hassio_audio", "--format", "{{.Names}}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and "hassio_audio" in stdout.decode():
                _LOGGER.debug("Detected HAOS environment with hassio_audio container")
                return "haos"
                
        except Exception as err:
            _LOGGER.debug("Error checking for HAOS environment: %s", err)
        
        try:
            # Check for Home Assistant CLI
            process = await asyncio.create_subprocess_exec(
                "ha", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                _LOGGER.debug("Detected Home Assistant CLI available")
                return "supervised"
                
        except Exception as err:
            _LOGGER.debug("Error checking for HA CLI: %s", err)
        
        _LOGGER.debug("Detected standalone/development environment")
        return "standalone"

    async def _check_pactl_available(self) -> bool:
        """Check if pactl command is available and working."""
        if self._pactl_method is not None:
            _LOGGER.debug("pactl method already determined: %s", self._pactl_method)
            return True
        
        _LOGGER.info("Checking pactl availability for HAOS audio integration...")
        
        # Detect environment first to optimize detection order
        environment = await self._detect_ha_environment()
        _LOGGER.info("Detected environment: %s", environment)
        
        # Track which methods we tried and their results
        attempted_methods = []
        
        # Try methods in order of likelihood based on environment
        if environment == "haos":
            # HAOS: When running inside container, try direct pactl first (may be available via shared audio)
            # Then try supervisor API if available
            _LOGGER.debug("Trying pactl methods for HAOS environment...")
            
            if await self._try_direct_pactl():
                _LOGGER.info("Successfully configured direct pactl method")
                return True
            attempted_methods.append("direct")
            
            if await self._try_supervisor_audio():
                _LOGGER.info("Successfully configured supervisor API method")
                return True
            attempted_methods.append("supervisor")
            
            if await self._try_haos_container_pactl():
                _LOGGER.info("Successfully configured HAOS container method")
                return True
            attempted_methods.append("haos_container")
            
        elif environment == "supervised":
            # Supervised: Try HA CLI first, then container, then direct
            _LOGGER.debug("Trying pactl methods for supervised environment...")
            
            if await self._try_ha_cli_audio():
                _LOGGER.info("Successfully configured HA CLI method")
                return True
            attempted_methods.append("ha_cli")
            
            if await self._try_haos_container_pactl():
                _LOGGER.info("Successfully configured HAOS container method")
                return True
            attempted_methods.append("haos_container")
            
            if await self._try_direct_pactl():
                _LOGGER.info("Successfully configured direct pactl method")
                return True
            attempted_methods.append("direct")
            
        elif environment == "container":
            # Container: Try direct first (might be available), then HA CLI
            _LOGGER.debug("Trying pactl methods for container environment...")
            
            if await self._try_direct_pactl():
                _LOGGER.info("Successfully configured direct pactl method")
                return True
            attempted_methods.append("direct")
            
            if await self._try_ha_cli_audio():
                _LOGGER.info("Successfully configured HA CLI method")
                return True
            attempted_methods.append("ha_cli")
            
        else:
            # Standalone: Try direct first, then others as fallback
            _LOGGER.debug("Trying pactl methods for standalone/unknown environment...")
            
            if await self._try_direct_pactl():
                _LOGGER.info("Successfully configured direct pactl method")
                return True
            attempted_methods.append("direct")
            
            if await self._try_haos_container_pactl():
                _LOGGER.info("Successfully configured HAOS container method")
                return True
            attempted_methods.append("haos_container")
            
            if await self._try_ha_cli_audio():
                _LOGGER.info("Successfully configured HA CLI method")
                return True
            attempted_methods.append("ha_cli")
        
        _LOGGER.error(
            "PulseAudio not available - no working pactl method found in %s environment. "
            "Attempted methods: %s. This may indicate that PulseAudio is not properly "
            "configured or accessible in your Home Assistant environment.",
            environment,
            ", ".join(attempted_methods)
        )
        self._pactl_method = None
        return False

    async def _try_direct_pactl(self) -> bool:
        """Try direct pactl command."""
        try:
            process = await asyncio.create_subprocess_exec(
                "pactl", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                version_info = stdout.decode().strip()
                _LOGGER.debug("PulseAudio pactl available directly: %s", version_info)
                self._pactl_method = "direct"
                return True
        except FileNotFoundError:
            _LOGGER.debug("Direct pactl command not found")
        except Exception as err:
            _LOGGER.debug("Error checking direct pactl: %s", err)
        return False

    async def _try_supervisor_audio(self) -> bool:
        """Try accessing audio via Home Assistant Supervisor API."""
        try:
            # Check if supervisor token is available
            supervisor_token = os.environ.get("SUPERVISOR_TOKEN")
            if not supervisor_token:
                _LOGGER.debug("No supervisor token available")
                return False
            
            # Try to access supervisor audio API
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {supervisor_token}",
                    "Content-Type": "application/json"
                }
                async with session.get(
                    "http://supervisor/audio/info",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        _LOGGER.debug("Supervisor audio API available")
                        self._pactl_method = "supervisor"
                        return True
                    else:
                        _LOGGER.debug("Supervisor audio API returned status: %s", response.status)
        except Exception as err:
            _LOGGER.debug("Error checking supervisor audio API: %s", err)
        return False

    async def _try_haos_container_pactl(self) -> bool:
        """Try HAOS hassio_audio container pactl."""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "exec", "-i", "hassio_audio", "pactl", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                version_info = stdout.decode().strip()
                _LOGGER.debug("PulseAudio pactl available via HAOS container: %s", version_info)
                self._pactl_method = "haos_container"
                return True
            else:
                _LOGGER.debug("HAOS container pactl failed: %s", stderr.decode())
        except FileNotFoundError:
            _LOGGER.debug("Docker command not found")
        except Exception as err:
            _LOGGER.debug("Error checking HAOS container pactl: %s", err)
        return False

    async def _try_ha_cli_audio(self) -> bool:
        """Try Home Assistant CLI audio."""
        try:
            process = await asyncio.create_subprocess_exec(
                "ha", "audio", "info",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                _LOGGER.debug("Home Assistant CLI audio available")
                self._pactl_method = "ha_cli"
                return True
            else:
                _LOGGER.debug("HA CLI audio failed: %s", stderr.decode())
        except FileNotFoundError:
            _LOGGER.debug("HA CLI command not found")
        except Exception as err:
            _LOGGER.debug("Error checking HA CLI: %s", err)
        return False
    
    async def _get_bluetooth_source_name(self) -> str:
        """Get the PulseAudio source name for the Bluetooth device."""
        # Standard BlueZ source naming convention
        mac_formatted = self._bluetooth_address.replace(':', '_')
        return f"bluez_source.{mac_formatted}.a2dp_source"
    
    async def _execute_pactl_command(self, args: list[str]) -> tuple[bool, str, str]:
        """Execute a pactl command using the appropriate method for the environment."""
        if not hasattr(self, '_pactl_method') or self._pactl_method is None:
            _LOGGER.error("No pactl method available")
            return False, "", "No pactl method available"
        
        try:
            if self._pactl_method == "direct":
                # Direct pactl execution
                cmd = ["pactl"] + args
            elif self._pactl_method == "haos_container":
                # Execute via HAOS hassio_audio container
                cmd = ["docker", "exec", "-i", "hassio_audio", "pactl"] + args
            elif self._pactl_method == "ha_cli":
                # For HA CLI, we need to map pactl commands to HA CLI equivalents
                return await self._execute_ha_cli_command(args)
            elif self._pactl_method == "supervisor":
                # For Supervisor API, we need to map pactl commands to API calls
                return await self._execute_supervisor_command(args)
            else:
                _LOGGER.error("Unknown pactl method: %s", self._pactl_method)
                return False, "", "Unknown pactl method"
            
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
            
            if success:
                _LOGGER.debug("pactl command succeeded: %s", stdout_str[:200])
            else:
                _LOGGER.warning("pactl command failed (exit %d): %s", process.returncode, stderr_str)
            
            return success, stdout_str, stderr_str
            
        except Exception as err:
            _LOGGER.error("Error executing pactl command %s: %s", args, err)
            return False, "", str(err)

    async def _execute_supervisor_command(self, pactl_args: list[str]) -> tuple[bool, str, str]:
        """Execute pactl command via Home Assistant Supervisor API."""
        try:
            supervisor_token = os.environ.get("SUPERVISOR_TOKEN")
            if not supervisor_token:
                return False, "", "No supervisor token available"
            
            headers = {
                "Authorization": f"Bearer {supervisor_token}",
                "Content-Type": "application/json"
            }
            
            # Map pactl commands to supervisor API calls
            if len(pactl_args) >= 1:
                command = pactl_args[0]
                
                if command == "list" and len(pactl_args) >= 2:
                    if pactl_args[1] == "sources":
                        # Get audio sources
                        async with aiohttp.ClientSession() as session:
                            async with session.get(
                                "http://supervisor/audio/info",
                                headers=headers,
                                timeout=aiohttp.ClientTimeout(total=10)
                            ) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    
                                    # Check if this is "list sources short" format
                                    is_short_format = len(pactl_args) >= 3 and pactl_args[2] == "short"
                                    
                                    sources_info = []
                                    if "data" in data and "audio" in data["data"]:
                                        audio_data = data["data"]["audio"]
                                        if "input" in audio_data:
                                            for source in audio_data["input"]:
                                                if is_short_format:
                                                    # Short format: index\tname\tdriver\tstate
                                                    sources_info.append(f"{source.get('index', 0)}\t{source.get('name', 'unknown')}\t{source.get('driver', 'module-unknown')}\tRUNNING")
                                                else:
                                                    # Full format
                                                    sources_info.append(f"Source #{source.get('index', 0)}")
                                                    sources_info.append(f"\tName: {source.get('name', 'unknown')}")
                                                    sources_info.append(f"\tDescription: {source.get('description', 'Unknown')}")
                                                    sources_info.append("")
                                    return True, "\n".join(sources_info), ""
                                else:
                                    return False, "", f"Supervisor API error: {response.status}"
                
                elif command == "info" and len(pactl_args) >= 2:
                    # Get source info
                    source_name = pactl_args[1]
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            "http://supervisor/audio/info",
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                # Look for the specific source
                                if "data" in data and "audio" in data["data"]:
                                    audio_data = data["data"]["audio"]
                                    if "input" in audio_data:
                                        for source in audio_data["input"]:
                                            if source.get("name") == source_name:
                                                info = [
                                                    f"Source #{source.get('index', 0)}",
                                                    f"\tName: {source.get('name', 'unknown')}",
                                                    f"\tDescription: {source.get('description', 'Unknown')}",
                                                    f"\tDriver: {source.get('driver', 'unknown')}",
                                                    f"\tState: RUNNING" if source.get('active', False) else f"\tState: IDLE"
                                                ]
                                                return True, "\n".join(info), ""
                                return False, "", f"Source {source_name} not found"
                            else:
                                return False, "", f"Supervisor API error: {response.status}"
            
            # Fallback for unsupported commands
            _LOGGER.warning("Supervisor API does not support pactl command: %s", " ".join(pactl_args))
            return False, "", f"Unsupported command: {' '.join(pactl_args)}"
            
        except Exception as err:
            _LOGGER.error("Error executing supervisor command %s: %s", pactl_args, err)
            return False, "", str(err)
    
    async def _execute_ha_cli_command(self, pactl_args: list[str]) -> tuple[bool, str, str]:
        """Execute Home Assistant CLI commands as pactl equivalents."""
        try:
            # Map common pactl commands to HA CLI equivalents
            if pactl_args == ["--version"]:
                cmd = ["ha", "audio", "info"]
            elif pactl_args == ["list", "sources", "short"]:
                cmd = ["ha", "audio", "info"]
            elif pactl_args == ["list", "sources"]:
                cmd = ["ha", "audio", "info"]
            elif pactl_args[0] == "set-source-volume" and len(pactl_args) >= 3:
                # Extract source name and volume from pactl args
                source_name = pactl_args[1]
                volume = pactl_args[2]
                # Try to use HA CLI volume control
                cmd = ["ha", "audio", "volume", "--source", source_name, "--volume", volume]
            elif pactl_args == ["list", "sinks", "short"]:
                cmd = ["ha", "audio", "info"]
            elif pactl_args == ["list", "sinks"]:
                cmd = ["ha", "audio", "info"]
            else:
                _LOGGER.warning("Unsupported HA CLI mapping for pactl args: %s", pactl_args)
                # For unsupported commands, try to fall back to container method if possible
                if await self._try_container_fallback():
                    return await self._execute_container_pactl(pactl_args)
                return False, "", "Unsupported HA CLI command"
            
            _LOGGER.debug("Executing HA CLI command: %s", " ".join(cmd))
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            success = process.returncode == 0
            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()
            
            if success:
                _LOGGER.debug("HA CLI command succeeded: %s", stdout_str[:200])
                
                # Format output for specific pactl commands
                if pactl_args == ["list", "sources", "short"]:
                    # Parse HA audio info and format as pactl list sources short
                    formatted_output = self._format_ha_audio_info_as_pactl_sources_short(stdout_str)
                    return success, formatted_output, stderr_str
                elif pactl_args == ["list", "sources"]:
                    # Parse HA audio info and format as pactl list sources
                    formatted_output = self._format_ha_audio_info_as_pactl_sources(stdout_str)
                    return success, formatted_output, stderr_str
            else:
                _LOGGER.warning("HA CLI command failed (exit %d): %s", process.returncode, stderr_str)
            
            return success, stdout_str, stderr_str
            
        except Exception as err:
            _LOGGER.error("Error executing HA CLI command: %s", err)
            return False, "", str(err)
    
    def _format_ha_audio_info_as_pactl_sources_short(self, ha_output: str) -> str:
        """Format HA audio info output as pactl list sources short format."""
        try:
            # Simple parsing - look for input devices in HA output
            lines = ha_output.split('\n')
            sources = []
            index = 0
            
            for line in lines:
                line = line.strip()
                if 'input' in line.lower() or 'source' in line.lower() or 'bluetooth' in line.lower():
                    # Extract device name if possible
                    if ':' in line:
                        name = line.split(':', 1)[1].strip()
                    else:
                        name = line.strip()
                    
                    # Format as: index\tname\tdriver\tstate
                    sources.append(f"{index}\t{name}\tmodule-bluetooth\tRUNNING")
                    index += 1
            
            return '\n'.join(sources) if sources else "0\tbluetooth_source\tmodule-bluetooth\tRUNNING"
            
        except Exception as err:
            _LOGGER.warning("Error formatting HA audio info as pactl sources short: %s", err)
            return "0\tbluetooth_source\tmodule-bluetooth\tRUNNING"
    
    def _format_ha_audio_info_as_pactl_sources(self, ha_output: str) -> str:
        """Format HA audio info output as pactl list sources format."""
        try:
            # Simple parsing - look for input devices in HA output
            lines = ha_output.split('\n')
            sources = []
            index = 0
            
            for line in lines:
                line = line.strip()
                if 'input' in line.lower() or 'source' in line.lower() or 'bluetooth' in line.lower():
                    # Extract device name if possible
                    if ':' in line:
                        name = line.split(':', 1)[1].strip()
                    else:
                        name = line.strip()
                    
                    # Format as full pactl source info
                    sources.append(f"Source #{index}")
                    sources.append(f"\tName: {name}")
                    sources.append(f"\tDescription: {name}")
                    sources.append(f"\tDriver: module-bluetooth")
                    sources.append(f"\tState: RUNNING")
                    sources.append("")
                    index += 1
            
            if not sources:
                sources = [
                    "Source #0",
                    "\tName: bluetooth_source",
                    "\tDescription: Bluetooth Audio Source",
                    "\tDriver: module-bluetooth",
                    "\tState: RUNNING",
                    ""
                ]
            
            return '\n'.join(sources)
            
        except Exception as err:
            _LOGGER.warning("Error formatting HA audio info as pactl sources: %s", err)
            return "Source #0\n\tName: bluetooth_source\n\tDescription: Bluetooth Audio Source\n\tDriver: module-bluetooth\n\tState: RUNNING\n"
    
    async def _try_container_fallback(self) -> bool:
        """Try to detect if container method is available as fallback."""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "exec", "-i", "hassio_audio", "pactl", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception:
            return False
    
    async def _execute_container_pactl(self, args: list[str]) -> tuple[bool, str, str]:
        """Execute pactl command directly in the hassio_audio container."""
        try:
            cmd = ["docker", "exec", "-i", "hassio_audio", "pactl"] + args
            _LOGGER.debug("Executing container pactl command: %s", " ".join(cmd))
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            success = process.returncode == 0
            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()
            
            if success:
                _LOGGER.debug("Container pactl command succeeded: %s", stdout_str[:200])
            else:
                _LOGGER.warning("Container pactl command failed (exit %d): %s", process.returncode, stderr_str)
            
            return success, stdout_str, stderr_str
            
        except Exception as err:
            _LOGGER.error("Error executing container pactl command: %s", err)
            return False, "", str(err)
    
    async def check_bluetooth_audio_available(self) -> bool:
        """Check if Bluetooth audio source is available in PulseAudio."""
        try:
            _LOGGER.debug("Checking Bluetooth audio availability using method: %s", self._pactl_method)
            
            success, stdout, stderr = await self._execute_pactl_command(["list", "sources", "short"])
            
            if not success:
                _LOGGER.error(
                    "Failed to list PulseAudio sources using method '%s'. "
                    "Error: %s. This may indicate PulseAudio is not running or accessible.",
                    self._pactl_method,
                    stderr or "Unknown error"
                )
                return False
            
            source_name = await self._get_bluetooth_source_name()
            is_available = source_name in stdout
            
            if is_available:
                _LOGGER.info("Bluetooth audio source found: %s (method: %s)", source_name, self._pactl_method)
            else:
                _LOGGER.warning(
                    "Bluetooth audio source not found: %s (method: %s). "
                    "This may indicate the Bluetooth device is not connected or audio is not active.",
                    source_name,
                    self._pactl_method
                )
                _LOGGER.debug("Available sources (method: %s):\n%s", self._pactl_method, stdout)
                
                # Provide helpful diagnostic information
                if not stdout.strip():
                    _LOGGER.warning("No audio sources detected. PulseAudio may not be running or configured properly.")
                else:
                    source_count = len([line for line in stdout.split('\n') if line.strip()])
                    _LOGGER.info("Found %d audio sources, but none match Bluetooth pattern '%s'", source_count, source_name)
            
            return is_available
            
        except Exception as err:
            _LOGGER.error(
                "Error checking Bluetooth audio availability (method: %s): %s. "
                "This may indicate a configuration issue with the audio system.",
                self._pactl_method,
                err
            )
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