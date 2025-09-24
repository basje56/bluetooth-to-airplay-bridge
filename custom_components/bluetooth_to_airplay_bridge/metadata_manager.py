"""Metadata manager for Bluetooth to AirPlay Bridge."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import subprocess
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from homeassistant.core import HomeAssistant, callback  # type: ignore
from homeassistant.helpers.event import async_track_time_interval  # type: ignore

_LOGGER = logging.getLogger(__name__)

# Metadata update interval
METADATA_UPDATE_INTERVAL = timedelta(seconds=2)

# Default metadata
DEFAULT_METADATA = {
    "title": "Unknown",
    "artist": "Unknown", 
    "album": "Unknown",
    "duration": 0,
    "position": 0,
    "playing": False,
    "volume": 0.5,
    "source": "unknown"
}


class MetadataManager:
    """Manages track metadata from Bluetooth and AirPlay sources."""

    def __init__(
        self,
        hass: HomeAssistant,
        bluetooth_address: str,
        airplay_name: str,
    ) -> None:
        """Initialize metadata manager."""
        self.hass = hass
        self._bluetooth_address = bluetooth_address
        self._airplay_name = airplay_name
        self._current_metadata = DEFAULT_METADATA.copy()
        self._metadata_callbacks: list[Callable[[dict[str, Any]], None]] = []
        self._update_task: Optional[asyncio.Task] = None
        self._unsub_update: Optional[Callable] = None
        self._is_running = False
        
        # Shairport-sync metadata pipe path
        self._metadata_pipe_path = f"/tmp/shairport-sync-metadata-{self._airplay_name.replace(' ', '_')}"
        
    def add_metadata_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Add callback for metadata updates."""
        self._metadata_callbacks.append(callback)
        
    def remove_metadata_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Remove metadata callback."""
        if callback in self._metadata_callbacks:
            self._metadata_callbacks.remove(callback)
            
    @callback
    def _notify_callbacks(self) -> None:
        """Notify all callbacks of metadata changes."""
        for callback in self._metadata_callbacks:
            try:
                callback(self._current_metadata.copy())
            except Exception as err:
                _LOGGER.error("Error in metadata callback: %s", err)
                
    async def start_monitoring(self) -> None:
        """Start metadata monitoring."""
        if self._is_running:
            return
            
        _LOGGER.info("Starting metadata monitoring")
        self._is_running = True
        
        # Start periodic metadata updates
        self._unsub_update = async_track_time_interval(
            self.hass, self._async_update_metadata, METADATA_UPDATE_INTERVAL
        )
        
    async def stop_monitoring(self) -> None:
        """Stop metadata monitoring."""
        if not self._is_running:
            return
            
        _LOGGER.info("Stopping metadata monitoring")
        self._is_running = False
        
        if self._unsub_update:
            self._unsub_update()
            self._unsub_update = None
            
        if self._update_task and not self._update_task.done():
            self._update_task.cancel()
            
    async def send_play_command(self) -> None:
        """Send play command to the active audio source."""
        try:
            # Try Bluetooth first
            result = await asyncio.create_subprocess_exec(
                "dbus-send", "--session", "--type=method_call",
                "--dest=org.mpris.MediaPlayer2.bluez",
                "/org/mpris/MediaPlayer2",
                "org.mpris.MediaPlayer2.Player.Play",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            _LOGGER.debug("Sent play command via Bluetooth")
        except Exception as err:
            _LOGGER.warning("Failed to send play command: %s", err)
            
    async def send_pause_command(self) -> None:
        """Send pause command to the active audio source."""
        try:
            # Try Bluetooth first
            result = await asyncio.create_subprocess_exec(
                "dbus-send", "--session", "--type=method_call",
                "--dest=org.mpris.MediaPlayer2.bluez",
                "/org/mpris/MediaPlayer2",
                "org.mpris.MediaPlayer2.Player.Pause",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            _LOGGER.debug("Sent pause command via Bluetooth")
        except Exception as err:
            _LOGGER.warning("Failed to send pause command: %s", err)
            
    async def send_next_command(self) -> None:
        """Send next track command to the active audio source."""
        try:
            # Try Bluetooth first
            result = await asyncio.create_subprocess_exec(
                "dbus-send", "--session", "--type=method_call",
                "--dest=org.mpris.MediaPlayer2.bluez",
                "/org/mpris/MediaPlayer2",
                "org.mpris.MediaPlayer2.Player.Next",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            _LOGGER.debug("Sent next track command via Bluetooth")
        except Exception as err:
            _LOGGER.warning("Failed to send next track command: %s", err)
            
    async def send_previous_command(self) -> None:
        """Send previous track command to the active audio source."""
        try:
            # Try Bluetooth first
            result = await asyncio.create_subprocess_exec(
                "dbus-send", "--session", "--type=method_call",
                "--dest=org.mpris.MediaPlayer2.bluez",
                "/org/mpris/MediaPlayer2",
                "org.mpris.MediaPlayer2.Player.Previous",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            _LOGGER.debug("Sent previous track command via Bluetooth")
        except Exception as err:
            _LOGGER.warning("Failed to send previous track command: %s", err)
            
    async def send_seek_command(self, position: int) -> None:
        """Send seek command to the active audio source."""
        try:
            # Convert position to microseconds for MPRIS
            position_us = position * 1000000
            result = await asyncio.create_subprocess_exec(
                "dbus-send", "--session", "--type=method_call",
                "--dest=org.mpris.MediaPlayer2.bluez",
                "/org/mpris/MediaPlayer2",
                "org.mpris.MediaPlayer2.Player.SetPosition",
                f"objpath:/org/mpris/MediaPlayer2/TrackList/NoTrack",
                f"int64:{position_us}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            _LOGGER.debug("Sent seek command to position %s via Bluetooth", position)
        except Exception as err:
            _LOGGER.warning("Failed to send seek command: %s", err)
            
    async def _async_update_metadata(self, now: datetime) -> None:
        """Update metadata from available sources."""
        try:
            # Try to get metadata from AirPlay first (more reliable)
            airplay_metadata = await self._get_airplay_metadata()
            if airplay_metadata and airplay_metadata.get("playing"):
                self._update_current_metadata(airplay_metadata, "airplay")
                return
                
            # Fall back to Bluetooth metadata
            bluetooth_metadata = await self._get_bluetooth_metadata()
            if bluetooth_metadata:
                self._update_current_metadata(bluetooth_metadata, "bluetooth")
                return
                
            # If no active playback, update playing status
            if self._current_metadata.get("playing"):
                self._current_metadata["playing"] = False
                self._current_metadata["source"] = "none"
                self._notify_callbacks()
                
        except Exception as err:
            _LOGGER.error("Error updating metadata: %s", err)
            
    def _update_current_metadata(self, new_metadata: dict[str, Any], source: str) -> None:
        """Update current metadata and notify callbacks if changed."""
        new_metadata["source"] = source
        
        # Check if metadata has changed significantly
        changed = False
        for key in ["title", "artist", "album", "playing", "position"]:
            if self._current_metadata.get(key) != new_metadata.get(key):
                changed = True
                break
                
        if changed:
            self._current_metadata.update(new_metadata)
            _LOGGER.debug("Metadata updated from %s: %s", source, new_metadata)
            self._notify_callbacks()
            
    async def _get_airplay_metadata(self) -> Optional[dict[str, Any]]:
        """Get metadata from AirPlay/shairport-sync."""
        try:
            if not os.path.exists(self._metadata_pipe_path):
                return None
                
            # Read from metadata pipe (non-blocking)
            metadata = await self._read_shairport_metadata()
            if metadata:
                return self._parse_shairport_metadata(metadata)
                
        except Exception as err:
            _LOGGER.debug("Error getting AirPlay metadata: %s", err)
            
        return None
        
    async def _read_shairport_metadata(self) -> Optional[str]:
        """Read metadata from shairport-sync pipe."""
        try:
            # Use timeout to avoid blocking
            proc = await asyncio.create_subprocess_exec(
                "timeout", "1", "cat", self._metadata_pipe_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await proc.communicate()
            if stdout:
                return stdout.decode('utf-8', errors='ignore')
                
        except Exception as err:
            _LOGGER.debug("Error reading shairport metadata pipe: %s", err)
            
        return None
        
    def _parse_shairport_metadata(self, metadata_text: str) -> dict[str, Any]:
        """Parse shairport-sync metadata format."""
        metadata = DEFAULT_METADATA.copy()
        metadata["playing"] = True
        
        try:
            # Parse shairport-sync metadata format
            # This is a simplified parser - real implementation would be more robust
            lines = metadata_text.strip().split('\n')
            
            for line in lines:
                if 'title' in line.lower():
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        metadata["title"] = match.group(1)
                elif 'artist' in line.lower():
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        metadata["artist"] = match.group(1)
                elif 'album' in line.lower():
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        metadata["album"] = match.group(1)
                        
        except Exception as err:
            _LOGGER.debug("Error parsing shairport metadata: %s", err)
            
        return metadata
        
    async def _get_bluetooth_metadata(self) -> Optional[dict[str, Any]]:
        """Get metadata from Bluetooth device using bluetoothctl."""
        try:
            # Get device info from bluetoothctl
            proc = await asyncio.create_subprocess_exec(
                "bluetoothctl", "info", self._bluetooth_address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return None
                
            output = stdout.decode('utf-8')
            return self._parse_bluetooth_info(output)
            
        except Exception as err:
            _LOGGER.debug("Error getting Bluetooth metadata: %s", err)
            
        return None
        
    def _parse_bluetooth_info(self, info_text: str) -> Optional[dict[str, Any]]:
        """Parse bluetoothctl info output for metadata."""
        try:
            metadata = DEFAULT_METADATA.copy()
            
            # Check if device is connected and has audio
            if "Connected: yes" in info_text:
                # Look for audio-related UUIDs
                if any(uuid in info_text for uuid in ["0000110b", "0000110d", "0000110e"]):
                    metadata["playing"] = True
                    
                    # Try to extract device name as fallback title
                    name_match = re.search(r'Name: (.+)', info_text)
                    if name_match:
                        metadata["title"] = f"Audio from {name_match.group(1).strip()}"
                        
            return metadata if metadata["playing"] else None
            
        except Exception as err:
            _LOGGER.debug("Error parsing Bluetooth info: %s", err)
            
        return None
        
    def get_current_metadata(self) -> dict[str, Any]:
        """Get current metadata."""
        return self._current_metadata.copy()
        
    async def set_position(self, position: float) -> bool:
        """Set playback position (if supported)."""
        try:
            # This would require integration with the actual media player
            # For now, just update our internal state
            self._current_metadata["position"] = position
            self._notify_callbacks()
            return True
            
        except Exception as err:
            _LOGGER.error("Error setting position: %s", err)
            return False
            
    async def play(self) -> bool:
        """Start playback (if supported)."""
        try:
            # This would require integration with the actual media player
            # For now, just update our internal state
            self._current_metadata["playing"] = True
            self._notify_callbacks()
            return True
            
        except Exception as err:
            _LOGGER.error("Error starting playback: %s", err)
            return False
            
    async def pause(self) -> bool:
        """Pause playback (if supported)."""
        try:
            # This would require integration with the actual media player
            # For now, just update our internal state
            self._current_metadata["playing"] = False
            self._notify_callbacks()
            return True
            
        except Exception as err:
            _LOGGER.error("Error pausing playback: %s", err)
            return False
            
    async def next_track(self) -> bool:
        """Skip to next track (if supported)."""
        try:
            # This would require integration with the actual media player
            _LOGGER.info("Next track requested")
            return True
            
        except Exception as err:
            _LOGGER.error("Error skipping to next track: %s", err)
            return False
            
    async def previous_track(self) -> bool:
        """Skip to previous track (if supported)."""
        try:
            # This would require integration with the actual media player
            _LOGGER.info("Previous track requested")
            return True
            
        except Exception as err:
            _LOGGER.error("Error skipping to previous track: %s", err)
            return False