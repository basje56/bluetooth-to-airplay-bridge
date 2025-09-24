"""Audio engine for Bluetooth to AirPlay Bridge."""
from __future__ import annotations

import asyncio
import logging
import subprocess
import threading
from typing import Any, Callable, Optional

try:
    import gi
    gi.require_version('Gst', '1.0')
    gi.require_version('GstAudio', '1.0')
    from gi.repository import Gst, GstAudio, GLib
    GST_AVAILABLE = True
except ImportError:
    GST_AVAILABLE = False
    Gst = None
    GstAudio = None
    GLib = None

_LOGGER = logging.getLogger(__name__)

# Audio codecs supported
SUPPORTED_CODECS = {
    'sbc': {'name': 'SBC', 'quality': 'standard', 'bitrate': '328'},
    'aac': {'name': 'AAC', 'quality': 'high', 'bitrate': '256'},
    'aptx': {'name': 'aptX', 'quality': 'premium', 'bitrate': '352'},
    'ldac': {'name': 'LDAC', 'quality': 'premium', 'bitrate': '990'}
}

class AudioEngine:
    """Manages audio capture from Bluetooth and streaming to AirPlay."""
    
    def __init__(self, bluetooth_address: str, airplay_name: str) -> None:
        """Initialize the audio engine."""
        self._bluetooth_address = bluetooth_address
        self._airplay_name = airplay_name
        self._pipeline: Optional[Any] = None
        self._loop: Optional[GLib.MainLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = False
        self._audio_callback: Optional[Callable] = None
        self._current_codec = 'sbc'
        self._sample_rate = 44100
        self._channels = 2
        
        if not GST_AVAILABLE:
            _LOGGER.error("GStreamer not available - audio functionality will be limited")
            
    async def start_audio_capture(self) -> bool:
        """Start capturing audio from Bluetooth device."""
        if not GST_AVAILABLE:
            _LOGGER.error("Cannot start audio capture - GStreamer not available")
            return False
            
        try:
            # Initialize GStreamer
            if not Gst.is_initialized():
                Gst.init(None)
                
            # Create audio pipeline
            success = await self._create_audio_pipeline()
            if not success:
                return False
                
            # Start the pipeline in a separate thread
            self._thread = threading.Thread(target=self._run_pipeline, daemon=True)
            self._thread.start()
            
            # Wait a moment for pipeline to start
            await asyncio.sleep(1)
            
            _LOGGER.info("Audio capture started successfully")
            return True
            
        except Exception as err:
            _LOGGER.error("Failed to start audio capture: %s", err)
            return False
            
    async def stop_audio_capture(self) -> None:
        """Stop audio capture."""
        try:
            self._is_running = False
            
            if self._pipeline:
                self._pipeline.set_state(Gst.State.NULL)
                
            if self._loop and self._loop.is_running():
                self._loop.quit()
                
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5)
                
            _LOGGER.info("Audio capture stopped")
            
        except Exception as err:
            _LOGGER.error("Error stopping audio capture: %s", err)
            
    async def _create_audio_pipeline(self) -> bool:
        """Create GStreamer pipeline for audio capture."""
        try:
            # Create pipeline elements
            pipeline_str = self._build_pipeline_string()
            _LOGGER.debug("Creating pipeline: %s", pipeline_str)
            
            self._pipeline = Gst.parse_launch(pipeline_str)
            if not self._pipeline:
                _LOGGER.error("Failed to create GStreamer pipeline")
                return False
                
            # Set up message handling
            bus = self._pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self._on_pipeline_message)
            
            return True
            
        except Exception as err:
            _LOGGER.error("Error creating audio pipeline: %s", err)
            return False
            
    def _build_pipeline_string(self) -> str:
        """Build GStreamer pipeline string based on codec and settings."""
        # Base pipeline for Bluetooth audio capture
        pipeline_parts = [
            # Bluetooth audio source (PulseAudio)
            f"pulsesrc device=bluez_source.{self._bluetooth_address.replace(':', '_')}.a2dp_source",
            
            # Audio conversion and processing
            "audioconvert",
            "audioresample",
            f"audio/x-raw,format=S16LE,rate={self._sample_rate},channels={self._channels}",
            
            # Audio effects and processing
            "volume volume=1.0",
            "audioconvert",
            
            # Output to AirPlay (via file sink for now, will be replaced with AirPlay sink)
            "wavenc",
            f"filesink location=/tmp/airplay_audio_{self._airplay_name.replace(' ', '_')}.wav"
        ]
        
        return " ! ".join(pipeline_parts)
        
    def _run_pipeline(self) -> None:
        """Run the GStreamer pipeline in a separate thread."""
        try:
            self._loop = GLib.MainLoop()
            self._is_running = True
            
            # Start the pipeline
            ret = self._pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                _LOGGER.error("Failed to start GStreamer pipeline")
                return
                
            _LOGGER.info("GStreamer pipeline started")
            
            # Run the main loop
            self._loop.run()
            
        except Exception as err:
            _LOGGER.error("Error running pipeline: %s", err)
        finally:
            self._is_running = False
            
    def _on_pipeline_message(self, bus: Any, message: Any) -> bool:
        """Handle GStreamer pipeline messages."""
        try:
            msg_type = message.type
            
            if msg_type == Gst.MessageType.ERROR:
                err, debug = message.parse_error()
                _LOGGER.error("Pipeline error: %s - %s", err, debug)
                if self._loop:
                    self._loop.quit()
                    
            elif msg_type == Gst.MessageType.WARNING:
                err, debug = message.parse_warning()
                _LOGGER.warning("Pipeline warning: %s - %s", err, debug)
                
            elif msg_type == Gst.MessageType.INFO:
                err, debug = message.parse_info()
                _LOGGER.info("Pipeline info: %s - %s", err, debug)
                
            elif msg_type == Gst.MessageType.EOS:
                _LOGGER.info("Pipeline reached end of stream")
                if self._loop:
                    self._loop.quit()
                    
        except Exception as err:
            _LOGGER.error("Error handling pipeline message: %s", err)
            
        return True
        
    async def set_codec(self, codec: str) -> bool:
        """Set the audio codec for Bluetooth connection."""
        if codec not in SUPPORTED_CODECS:
            _LOGGER.error("Unsupported codec: %s", codec)
            return False
            
        try:
            # Stop current capture
            if self._is_running:
                await self.stop_audio_capture()
                
            self._current_codec = codec
            _LOGGER.info("Audio codec set to: %s", SUPPORTED_CODECS[codec]['name'])
            
            # Restart capture with new codec
            if self._is_running:
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
            'airplay_name': self._airplay_name
        }
        
    async def check_bluetooth_audio_available(self) -> bool:
        """Check if Bluetooth audio source is available."""
        try:
            # Check if PulseAudio source exists for this device
            cmd = ["pactl", "list", "sources", "short"]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            
            if result.returncode == 0:
                output = stdout.decode()
                source_name = f"bluez_source.{self._bluetooth_address.replace(':', '_')}"
                return source_name in output
                
            return False
            
        except Exception as err:
            _LOGGER.error("Error checking Bluetooth audio availability: %s", err)
            return False
    
    async def get_bluetooth_volume(self) -> float:
        """Get current Bluetooth device volume (0.0-1.0)."""
        try:
            # Get volume from PulseAudio source
            source_name = f"bluez_source.{self._bluetooth_address.replace(':', '_')}"
            cmd = ["pactl", "list", "sources"]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            
            if result.returncode == 0:
                output = stdout.decode()
                lines = output.split('\n')
                
                # Find our source and get volume
                in_source = False
                for line in lines:
                    if source_name in line:
                        in_source = True
                    elif in_source and "Volume:" in line:
                        # Parse volume percentage
                        parts = line.split()
                        for part in parts:
                            if part.endswith('%'):
                                volume_percent = int(part.rstrip('%'))
                                return volume_percent / 100.0
                        break
                    elif in_source and line.strip() == "":
                        break
                        
            return 0.5  # Default volume
            
        except Exception as err:
            _LOGGER.error("Error getting Bluetooth volume: %s", err)
            return 0.5
    
    async def set_bluetooth_volume(self, volume: float) -> bool:
        """Set Bluetooth device volume (0.0-1.0)."""
        try:
            volume_percent = max(0, min(100, int(volume * 100)))
            source_name = f"bluez_source.{self._bluetooth_address.replace(':', '_')}"
            
            cmd = ["pactl", "set-source-volume", source_name, f"{volume_percent}%"]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            
            if result.returncode == 0:
                _LOGGER.debug("Set Bluetooth volume to %d%%", volume_percent)
                return True
            else:
                _LOGGER.warning("Failed to set Bluetooth volume")
                return False
                
        except Exception as err:
            _LOGGER.error("Error setting Bluetooth volume: %s", err)
            return False