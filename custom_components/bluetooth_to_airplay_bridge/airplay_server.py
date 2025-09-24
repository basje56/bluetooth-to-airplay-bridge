"""AirPlay server implementation for Bluetooth to AirPlay Bridge."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class AirPlayServer:
    """Manages AirPlay server using shairport-sync."""
    
    def __init__(self, name: str, port: int = 5000) -> None:
        """Initialize AirPlay server."""
        self._name = name
        self._port = port
        self._process: Optional[subprocess.Popen] = None
        self._config_file: Optional[str] = None
        self._is_running = False
        self._audio_backend = "pulse"  # Default to PulseAudio
        self._volume = 50
        self._metadata_callback: Optional[callable] = None
        
    async def start(self) -> bool:
        """Start the AirPlay server."""
        try:
            # Check if shairport-sync is available
            if not await self._check_shairport_available():
                _LOGGER.error("shairport-sync not found - please install it first")
                return False
                
            # Create configuration file
            config_path = await self._create_config_file()
            if not config_path:
                return False
                
            # Start shairport-sync process
            cmd = [
                "shairport-sync",
                "--configfile", config_path,
                "--verbose"
            ]
            
            _LOGGER.info("Starting AirPlay server: %s", " ".join(cmd))
            
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Wait a moment to check if process started successfully
            await asyncio.sleep(2)
            
            if self._process.poll() is None:
                self._is_running = True
                _LOGGER.info("AirPlay server '%s' started successfully on port %d", 
                           self._name, self._port)
                
                # Start monitoring the process
                asyncio.create_task(self._monitor_process())
                return True
            else:
                stdout, stderr = await self._process.communicate()
                _LOGGER.error("AirPlay server failed to start: %s", stderr.decode())
                return False
                
        except Exception as err:
            _LOGGER.error("Error starting AirPlay server: %s", err)
            return False
            
    async def stop(self) -> None:
        """Stop the AirPlay server."""
        try:
            if self._process and self._is_running:
                _LOGGER.info("Stopping AirPlay server")
                
                # Send SIGTERM to the process group
                try:
                    os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass  # Process already terminated
                    
                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(self._process.wait(), timeout=10)
                except asyncio.TimeoutError:
                    # Force kill if not terminated
                    try:
                        os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                        
                self._is_running = False
                self._process = None
                
            # Clean up config file
            if self._config_file and os.path.exists(self._config_file):
                os.unlink(self._config_file)
                self._config_file = None
                
            _LOGGER.info("AirPlay server stopped")
            
        except Exception as err:
            _LOGGER.error("Error stopping AirPlay server: %s", err)
            
    async def _check_shairport_available(self) -> bool:
        """Check if shairport-sync is available."""
        try:
            result = await asyncio.create_subprocess_exec(
                "shairport-sync", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False
            
    async def _create_config_file(self) -> Optional[str]:
        """Create shairport-sync configuration file."""
        try:
            # Create temporary config file
            fd, config_path = tempfile.mkstemp(suffix=".conf", prefix="shairport_")
            self._config_file = config_path
            
            config_content = self._generate_config()
            
            with os.fdopen(fd, 'w') as f:
                f.write(config_content)
                
            _LOGGER.debug("Created config file: %s", config_path)
            return config_path
            
        except Exception as err:
            _LOGGER.error("Error creating config file: %s", err)
            return None
            
    def _generate_config(self) -> str:
        """Generate shairport-sync configuration."""
        config = f'''// Shairport Sync Configuration for {DOMAIN}
general = {{
    name = "{self._name}";
    port = {self._port};
    udp_port_base = {self._port + 1000};
    udp_port_range = 10;
    drift_tolerance_in_seconds = 0.002;
    resync_threshold_in_seconds = 0.050;
    log_verbosity = 1;
    ignore_volume_control = "no";
    volume_range_db = 60;
    regtype = "_raop._tcp";
    playback_mode = "stereo";
}};

// Audio backend configuration
{self._audio_backend} = {{
    output_device = "default";
    mixer_control_name = "Master";
    mixer_device = "default";
}};

// Session control
sessioncontrol = {{
    allow_session_interruption = "yes";
    session_timeout = 120;
}};

// Metadata
metadata = {{
    enabled = "yes";
    include_cover_art = "yes";
    pipe_name = "/tmp/shairport-sync-metadata-{self._name.replace(' ', '_')}";
    pipe_timeout = 5000;
}};

// Diagnostics
diagnostics = {{
    log_verbosity = 1;
    log_show_time_since_startup = "yes";
    log_show_time_since_last_message = "yes";
}};
'''
        return config
        
    async def _monitor_process(self) -> None:
        """Monitor the shairport-sync process."""
        try:
            if not self._process:
                return
                
            # Read output in background
            while self._is_running and self._process:
                try:
                    # Check if process is still running
                    if self._process.poll() is not None:
                        _LOGGER.warning("AirPlay server process terminated unexpectedly")
                        self._is_running = False
                        break
                        
                    await asyncio.sleep(5)  # Check every 5 seconds
                    
                except Exception as err:
                    _LOGGER.error("Error monitoring AirPlay process: %s", err)
                    break
                    
        except Exception as err:
            _LOGGER.error("Error in process monitor: %s", err)
            
    async def set_volume(self, volume: int) -> bool:
        """Set AirPlay server volume (0-100)."""
        try:
            if not 0 <= volume <= 100:
                _LOGGER.error("Invalid volume level: %d", volume)
                return False
                
            self._volume = volume
            
            # Send volume control to shairport-sync via FIFO if available
            # This is a simplified implementation
            _LOGGER.info("Volume set to %d%%", volume)
            return True
            
        except Exception as err:
            _LOGGER.error("Error setting volume: %s", err)
            return False
    
    def get_volume(self) -> float:
        """Get current AirPlay server volume (0.0-1.0)."""
        return self._volume / 100.0
    
    def set_volume_float(self, volume: float) -> None:
        """Set AirPlay server volume using float (0.0-1.0)."""
        volume_int = max(0, min(100, int(volume * 100)))
        self._volume = volume_int
            
    async def get_status(self) -> dict[str, Any]:
        """Get AirPlay server status."""
        return {
            "name": self._name,
            "port": self._port,
            "is_running": self._is_running,
            "volume": self._volume,
            "audio_backend": self._audio_backend,
            "process_id": self._process.pid if self._process else None
        }
        
    async def get_metadata(self) -> Optional[dict[str, Any]]:
        """Get current playing metadata from AirPlay."""
        try:
            if not self._is_running:
                return None
                
            # Read metadata from pipe
            pipe_path = f"/tmp/shairport-sync-metadata-{self._name.replace(' ', '_')}"
            if not os.path.exists(pipe_path):
                return None
                
            # This is a simplified implementation
            # In a real implementation, you'd parse the metadata pipe
            return {
                "title": "Unknown",
                "artist": "Unknown",
                "album": "Unknown",
                "playing": self._is_running
            }
            
        except Exception as err:
            _LOGGER.error("Error getting metadata: %s", err)
            return None
            
    def set_metadata_callback(self, callback: callable) -> None:
        """Set callback for metadata updates."""
        self._metadata_callback = callback
        
    @property
    def is_running(self) -> bool:
        """Check if AirPlay server is running."""
        return self._is_running
        
    @property
    def name(self) -> str:
        """Get AirPlay server name."""
        return self._name
        
    @property
    def port(self) -> int:
        """Get AirPlay server port."""
        return self._port