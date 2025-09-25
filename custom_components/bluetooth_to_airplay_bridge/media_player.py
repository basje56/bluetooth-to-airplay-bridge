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
from .metadata_manager import MetadataManager

# Additional attributes for audio streaming status
ATTR_AUDIO_ENGINE_STATUS = "audio_engine_status"
ATTR_AIRPLAY_SERVER_STATUS = "airplay_server_status"
ATTR_MDNS_STATUS = "mdns_status"
ATTR_AUDIO_CODEC = "audio_codec"
ATTR_AUDIO_QUALITY = "audio_quality"
ATTR_STREAMING_STATUS = "streaming_status"
ATTR_VOLUME_LEVEL = "volume_level"
ATTR_IS_MUTED = "is_muted"

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
        
        # Audio state tracking
        self._volume_level: float = 0.5
        self._is_muted: bool = False
        
        # Track metadata
        self._current_metadata: dict[str, Any] = {}
        
        # Set up metadata callback
        coordinator.metadata_manager.add_metadata_callback(self._on_metadata_update)

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        features = (
            MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.VOLUME_SET
        )
        
        # Add media control features if metadata manager is available
        if hasattr(self._coordinator, 'metadata_manager') and self._coordinator.metadata_manager:
            features |= (
                MediaPlayerEntityFeature.PLAY
                | MediaPlayerEntityFeature.PAUSE
                | MediaPlayerEntityFeature.NEXT_TRACK
                | MediaPlayerEntityFeature.PREVIOUS_TRACK
                | MediaPlayerEntityFeature.SEEK
            )
            
        return features

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the media player."""
        coordinator_state = self._coordinator.state
        
        if coordinator_state == STATE_CONNECTED:
            # Check if audio is actually streaming
            if hasattr(self._coordinator, '_audio_engine') and self._coordinator._audio_engine:
                if self._coordinator._audio_engine._is_running:
                    return MediaPlayerState.PLAYING
                else:
                    return MediaPlayerState.IDLE
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
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        return self._volume_level

    @property
    def is_volume_muted(self) -> bool | None:
        """Boolean if volume is currently muted."""
        return self._is_muted
        
    @property
    def media_title(self) -> str | None:
        """Title of current playing media."""
        return self._current_metadata.get("title")
        
    @property
    def media_artist(self) -> str | None:
        """Artist of current playing media."""
        return self._current_metadata.get("artist")
        
    @property
    def media_album_name(self) -> str | None:
        """Album name of current playing media."""
        return self._current_metadata.get("album")
        
    @property
    def media_duration(self) -> int | None:
        """Duration of current playing media in seconds."""
        return self._current_metadata.get("duration")
        
    @property
    def media_position(self) -> int | None:
        """Position of current playing media in seconds."""
        return self._current_metadata.get("position")
        
    @property
    def media_position_updated_at(self) -> Any | None:
        """When was the position of the current playing media valid."""
        return self._current_metadata.get("position_updated_at")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.state != STATE_ERROR

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attributes = {
            ATTR_BLUETOOTH_ADDRESS: self._coordinator.bluetooth_address,
            ATTR_BLUETOOTH_NAME: self._coordinator.bluetooth_name,
            ATTR_AIRPLAY_NAME: self._coordinator.airplay_name,
            ATTR_AIRPLAY_VERSION: self._coordinator.airplay_version,
            ATTR_CONNECTION_STATE: self._coordinator.state,
            ATTR_LAST_SEEN: self._coordinator.last_seen.isoformat() if self._coordinator.last_seen else None,
            ATTR_VOLUME_LEVEL: self._volume_level,
            ATTR_IS_MUTED: self._is_muted,
        }
        
        # Add audio engine status if available
        if hasattr(self._coordinator, '_audio_engine') and self._coordinator._audio_engine:
            audio_info = self._coordinator._audio_engine.get_audio_info()
            attributes.update({
                ATTR_AUDIO_ENGINE_STATUS: audio_info.get('status', 'unknown'),
                ATTR_AUDIO_CODEC: audio_info.get('codec', 'unknown'),
                ATTR_AUDIO_QUALITY: f"{audio_info.get('sample_rate', 0)}Hz/{audio_info.get('channels', 0)}ch",
                ATTR_STREAMING_STATUS: 'active' if audio_info.get('is_running', False) else 'inactive',
            })
        
        # Add AirPlay server status if available
        if hasattr(self._coordinator, '_airplay_server') and self._coordinator._airplay_server:
            attributes[ATTR_AIRPLAY_SERVER_STATUS] = (
                'running' if self._coordinator._airplay_server._server else 'stopped'
            )
        
        # Add mDNS status if available
        if hasattr(self._coordinator, '_mdns_advertiser') and self._coordinator._mdns_advertiser:
            attributes[ATTR_MDNS_STATUS] = (
                'advertising' if self._coordinator._mdns_advertiser._zeroconf else 'stopped'
            )
        
        return attributes

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
        
        # Update internal state
        self._volume_level = max(0.0, min(1.0, volume))
        
        # Control AirPlay server volume if available
        if hasattr(self._coordinator, '_airplay_server') and self._coordinator._airplay_server:
            try:
                # Convert float (0.0-1.0) to int (0-100)
                volume_percent = int(self._volume_level * 100)
                await self._coordinator._airplay_server.set_volume(volume_percent)
                _LOGGER.debug("Successfully set AirPlay volume to %s%%", volume_percent)
            except Exception as err:
                _LOGGER.warning("Failed to set AirPlay volume: %s", err)
        
        # Trigger state update
        self.async_write_ha_state()

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute (true) or unmute (false) media player."""
        _LOGGER.debug("Setting mute to %s", mute)
        
        # Update internal state
        self._is_muted = mute
        
        # Control AirPlay server mute by setting volume if available
        if hasattr(self._coordinator, '_airplay_server') and self._coordinator._airplay_server:
            try:
                # Implement mute by setting volume to 0 or restoring previous volume
                if self._is_muted:
                    await self._coordinator._airplay_server.set_volume(0)
                    _LOGGER.debug("Successfully muted AirPlay (volume set to 0)")
                else:
                    # Restore volume when unmuting
                    volume_percent = int(self._volume_level * 100)
                    await self._coordinator._airplay_server.set_volume(volume_percent)
                    _LOGGER.debug("Successfully unmuted AirPlay (volume restored to %s%%)", volume_percent)
            except Exception as err:
                _LOGGER.warning("Failed to set AirPlay mute: %s", err)
        
        # Trigger state update
        self.async_write_ha_state()
        
    async def async_media_play(self) -> None:
        """Send play command."""
        if hasattr(self._coordinator, 'metadata_manager'):
            await self._coordinator.metadata_manager.send_play_command()
            
    async def async_media_pause(self) -> None:
        """Send pause command."""
        if hasattr(self._coordinator, 'metadata_manager'):
            await self._coordinator.metadata_manager.send_pause_command()
            
    async def async_media_next_track(self) -> None:
        """Send next track command."""
        if hasattr(self._coordinator, 'metadata_manager'):
            await self._coordinator.metadata_manager.send_next_command()
            
    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        if hasattr(self._coordinator, 'metadata_manager'):
            await self._coordinator.metadata_manager.send_previous_command()
            
    async def async_media_seek(self, position: float) -> None:
        """Send seek command."""
        if hasattr(self._coordinator, 'metadata_manager'):
            await self._coordinator.metadata_manager.send_seek_command(int(position))

    async def async_update(self) -> None:
        """Update the entity."""
        # The coordinator handles the state updates
        pass

    async def async_remove(self) -> None:
        """Remove the entity and disconnect Bluetooth device."""
        _LOGGER.info("Removing media player entity and disconnecting Bluetooth device")
        await self._coordinator.async_stop()
        await super().async_remove()
        
    def _on_metadata_update(self, metadata: dict[str, Any]) -> None:
        """Handle metadata updates from the metadata manager."""
        self._current_metadata = metadata
        self.async_write_ha_state()