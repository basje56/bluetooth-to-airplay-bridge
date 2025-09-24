"""Media player platform for Bluetooth to AirPlay Bridge."""
from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.media_player import (  # type: ignore
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.helpers.entity_platform import AddEntitiesCallback  # type: ignore

from . import BluetoothAirPlayCoordinator
from .const import (
    ATTR_AIRPLAY_NAME,
    ATTR_AIRPLAY_VERSION,
    ATTR_BLUETOOTH_ADDRESS,
    ATTR_BLUETOOTH_NAME,
    ATTR_CONNECTION_STATE,
    ATTR_LAST_SEEN,
    DOMAIN,
    STATE_CONNECTED,
    STATE_CONNECTING,
    STATE_DISCONNECTED,
    STATE_ERROR,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the media player platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([BluetoothAirPlayMediaPlayer(coordinator)])


class BluetoothAirPlayMediaPlayer(MediaPlayerEntity):
    """Representation of a Bluetooth to AirPlay Bridge media player."""

    def __init__(self, coordinator: BluetoothAirPlayCoordinator) -> None:
        """Initialize the media player."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_{coordinator.bluetooth_address}"
        self._attr_name = f"AirPlay Bridge ({coordinator.bluetooth_name})"
        self._attr_device_info = coordinator.device_info

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        return (
            MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.VOLUME_SET
        )

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the media player."""
        coordinator_state = self._coordinator.state
        
        if coordinator_state == STATE_CONNECTED:
            return MediaPlayerState.ON
        elif coordinator_state == STATE_CONNECTING:
            return MediaPlayerState.ON  # Show as on while connecting
        elif coordinator_state == STATE_DISCONNECTED:
            return MediaPlayerState.OFF
        elif coordinator_state == STATE_ERROR:
            return MediaPlayerState.OFF
        else:
            return MediaPlayerState.UNKNOWN

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.state != STATE_ERROR

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            ATTR_BLUETOOTH_ADDRESS: self._coordinator.bluetooth_address,
            ATTR_BLUETOOTH_NAME: self._coordinator.bluetooth_name,
            ATTR_AIRPLAY_NAME: self._coordinator.airplay_name,
            ATTR_AIRPLAY_VERSION: self._coordinator.airplay_version,
            ATTR_CONNECTION_STATE: self._coordinator.state,
            ATTR_LAST_SEEN: self._coordinator.last_seen.isoformat() if self._coordinator.last_seen else None,
        }

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self.state == MediaPlayerState.ON:
            return "mdi:cast-connected"
        elif self._coordinator.state == STATE_CONNECTING:
            return "mdi:cast-variant"
        else:
            return "mdi:cast-off"

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        _LOGGER.debug("Turning on AirPlay bridge")
        await self._coordinator.async_start()

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        _LOGGER.debug("Turning off AirPlay bridge")
        await self._coordinator.async_stop()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        _LOGGER.debug("Setting volume level to %s", volume)
        # In a real implementation, this would control the AirPlay volume
        # For now, this is a placeholder

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute (true) or unmute (false) media player."""
        _LOGGER.debug("Setting mute to %s", mute)
        # In a real implementation, this would control the AirPlay mute
        # For now, this is a placeholder

    async def async_update(self) -> None:
        """Update the entity."""
        # The coordinator handles the state updates
        pass

    async def async_remove(self) -> None:
        """Remove the entity and disconnect Bluetooth device."""
        _LOGGER.info("Removing media player entity and disconnecting Bluetooth device")
        await self._coordinator.async_stop()
        await super().async_remove()