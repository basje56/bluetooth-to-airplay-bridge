"""Volume synchronization between Bluetooth and AirPlay."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

VOLUME_SYNC_INTERVAL = timedelta(seconds=1)
VOLUME_CHANGE_THRESHOLD = 0.02  # 2% change threshold


class VolumeSynchronizer:
    """Manages bidirectional volume synchronization."""

    def __init__(
        self,
        hass: HomeAssistant,
        bluetooth_volume_getter: Callable[[], Any],
        bluetooth_volume_setter: Callable[[float], Any],
        airplay_volume_getter: Callable[[], float],
        airplay_volume_setter: Callable[[float], None],
    ) -> None:
        """Initialize volume synchronizer."""
        self._hass = hass
        self._bluetooth_volume_getter = bluetooth_volume_getter
        self._bluetooth_volume_setter = bluetooth_volume_setter
        self._airplay_volume_getter = airplay_volume_getter
        self._airplay_volume_setter = airplay_volume_setter
        
        self._last_bluetooth_volume: Optional[float] = None
        self._last_airplay_volume: Optional[float] = None
        self._sync_enabled = True
        self._sync_direction = "both"  # "both", "bluetooth_to_airplay", "airplay_to_bluetooth"
        self._volume_offset = 0.0  # Volume offset for calibration
        self._sync_task: Optional[asyncio.Task] = None
        self._unsub_timer: Optional[Callable] = None
        
        _LOGGER.debug("Volume synchronizer initialized")

    @property
    def sync_enabled(self) -> bool:
        """Return if volume sync is enabled."""
        return self._sync_enabled

    @sync_enabled.setter
    def sync_enabled(self, enabled: bool) -> None:
        """Enable or disable volume sync."""
        self._sync_enabled = enabled
        _LOGGER.debug("Volume sync %s", "enabled" if enabled else "disabled")

    @property
    def sync_direction(self) -> str:
        """Return sync direction."""
        return self._sync_direction

    @sync_direction.setter
    def sync_direction(self, direction: str) -> None:
        """Set sync direction."""
        if direction in ["both", "bluetooth_to_airplay", "airplay_to_bluetooth"]:
            self._sync_direction = direction
            _LOGGER.debug("Volume sync direction set to: %s", direction)
        else:
            _LOGGER.warning("Invalid sync direction: %s", direction)

    @property
    def volume_offset(self) -> float:
        """Return volume offset."""
        return self._volume_offset

    @volume_offset.setter
    def volume_offset(self, offset: float) -> None:
        """Set volume offset for calibration."""
        self._volume_offset = max(-1.0, min(1.0, offset))
        _LOGGER.debug("Volume offset set to: %.2f", self._volume_offset)

    async def start_sync(self) -> None:
        """Start volume synchronization."""
        if self._unsub_timer is not None:
            return
            
        _LOGGER.debug("Starting volume synchronization")
        
        # Initialize current volumes
        try:
            bluetooth_volume_result = self._bluetooth_volume_getter()
            if asyncio.iscoroutine(bluetooth_volume_result):
                self._last_bluetooth_volume = await bluetooth_volume_result
            else:
                self._last_bluetooth_volume = bluetooth_volume_result
                
            self._last_airplay_volume = self._airplay_volume_getter()
        except Exception as err:
            _LOGGER.warning("Failed to get initial volumes: %s", err)
            self._last_bluetooth_volume = 0.5
            self._last_airplay_volume = 0.5
        
        # Start periodic sync
        self._unsub_timer = async_track_time_interval(
            self._hass, self._async_sync_volumes, VOLUME_SYNC_INTERVAL
        )

    async def stop_sync(self) -> None:
        """Stop volume synchronization."""
        if self._unsub_timer is not None:
            self._unsub_timer()
            self._unsub_timer = None
            _LOGGER.debug("Volume synchronization stopped")

    async def _async_sync_volumes(self, now) -> None:
        """Synchronize volumes between Bluetooth and AirPlay."""
        if not self._sync_enabled:
            return

        try:
            # Get current volumes
            bluetooth_volume_result = self._bluetooth_volume_getter()
            if asyncio.iscoroutine(bluetooth_volume_result):
                current_bluetooth_volume = await bluetooth_volume_result
            else:
                current_bluetooth_volume = bluetooth_volume_result
                
            current_airplay_volume = self._airplay_volume_getter()

            # Check for Bluetooth volume changes
            if (
                self._last_bluetooth_volume is not None
                and abs(current_bluetooth_volume - self._last_bluetooth_volume) > VOLUME_CHANGE_THRESHOLD
                and self._sync_direction in ["both", "bluetooth_to_airplay"]
            ):
                # Bluetooth volume changed, sync to AirPlay
                target_volume = self._apply_offset(current_bluetooth_volume)
                await self._set_airplay_volume(target_volume)
                _LOGGER.debug(
                    "Synced Bluetooth volume %.2f to AirPlay volume %.2f",
                    current_bluetooth_volume,
                    target_volume,
                )

            # Check for AirPlay volume changes
            elif (
                self._last_airplay_volume is not None
                and abs(current_airplay_volume - self._last_airplay_volume) > VOLUME_CHANGE_THRESHOLD
                and self._sync_direction in ["both", "airplay_to_bluetooth"]
            ):
                # AirPlay volume changed, sync to Bluetooth
                target_volume = self._apply_offset(current_airplay_volume, reverse=True)
                await self._set_bluetooth_volume(target_volume)
                _LOGGER.debug(
                    "Synced AirPlay volume %.2f to Bluetooth volume %.2f",
                    current_airplay_volume,
                    target_volume,
                )

            # Update last known volumes
            self._last_bluetooth_volume = current_bluetooth_volume
            self._last_airplay_volume = current_airplay_volume

        except Exception as err:
            _LOGGER.error("Error during volume synchronization: %s", err)

    def _apply_offset(self, volume: float, reverse: bool = False) -> float:
        """Apply volume offset for calibration."""
        if reverse:
            adjusted = volume - self._volume_offset
        else:
            adjusted = volume + self._volume_offset
        
        return max(0.0, min(1.0, adjusted))

    async def _set_bluetooth_volume(self, volume: float) -> None:
        """Set Bluetooth volume."""
        try:
            result = self._bluetooth_volume_setter(volume)
            if asyncio.iscoroutine(result):
                await result
        except Exception as err:
            _LOGGER.error("Failed to set Bluetooth volume: %s", err)

    async def _set_airplay_volume(self, volume: float) -> None:
        """Set AirPlay volume."""
        try:
            self._airplay_volume_setter(volume)
        except Exception as err:
            _LOGGER.error("Failed to set AirPlay volume: %s", err)

    async def force_sync_to_airplay(self) -> None:
        """Force sync current Bluetooth volume to AirPlay."""
        if not self._sync_enabled:
            return
            
        try:
            bluetooth_volume = self._bluetooth_volume_getter()
            target_volume = self._apply_offset(bluetooth_volume)
            await self._set_airplay_volume(target_volume)
            self._last_airplay_volume = target_volume
            _LOGGER.debug("Force synced Bluetooth volume %.2f to AirPlay", target_volume)
        except Exception as err:
            _LOGGER.error("Failed to force sync to AirPlay: %s", err)

    async def force_sync_to_bluetooth(self) -> None:
        """Force sync current AirPlay volume to Bluetooth."""
        if not self._sync_enabled:
            return
            
        try:
            airplay_volume = self._airplay_volume_getter()
            target_volume = self._apply_offset(airplay_volume, reverse=True)
            await self._set_bluetooth_volume(target_volume)
            self._last_bluetooth_volume = target_volume
            _LOGGER.debug("Force synced AirPlay volume %.2f to Bluetooth", target_volume)
        except Exception as err:
            _LOGGER.error("Failed to force sync to Bluetooth: %s", err)

    def get_sync_status(self) -> dict[str, Any]:
        """Get current sync status."""
        return {
            "enabled": self._sync_enabled,
            "direction": self._sync_direction,
            "offset": self._volume_offset,
            "last_bluetooth_volume": self._last_bluetooth_volume,
            "last_airplay_volume": self._last_airplay_volume,
        }