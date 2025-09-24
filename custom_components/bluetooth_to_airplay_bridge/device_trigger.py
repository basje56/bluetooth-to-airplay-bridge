"""Device automation triggers for Bluetooth to AirPlay Bridge."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Trigger types
TRIGGER_CONNECTED = "connected"
TRIGGER_DISCONNECTED = "disconnected"
TRIGGER_PAIRING_STARTED = "pairing_started"
TRIGGER_PAIRING_FAILED = "pairing_failed"
TRIGGER_PAIRING_SUCCESS = "pairing_success"
TRIGGER_AUDIO_STARTED = "audio_started"
TRIGGER_AUDIO_STOPPED = "audio_stopped"
TRIGGER_ERROR = "error"

TRIGGER_TYPES = {
    TRIGGER_CONNECTED,
    TRIGGER_DISCONNECTED,
    TRIGGER_PAIRING_STARTED,
    TRIGGER_PAIRING_FAILED,
    TRIGGER_PAIRING_SUCCESS,
    TRIGGER_AUDIO_STARTED,
    TRIGGER_AUDIO_STOPPED,
    TRIGGER_ERROR,
}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device triggers for Bluetooth to AirPlay Bridge devices."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    
    if not device or device.config_entries is None:
        return []
    
    # Check if this device belongs to our integration
    config_entries = [
        entry for entry in device.config_entries
        if hass.config_entries.async_get_entry(entry).domain == DOMAIN
    ]
    
    if not config_entries:
        return []
    
    triggers = []
    for trigger_type in TRIGGER_TYPES:
        triggers.append({
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_TYPE: trigger_type,
        })
    
    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    device_id = config[CONF_DEVICE_ID]
    trigger_type = config[CONF_TYPE]
    
    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_EVENT_TYPE: f"{DOMAIN}_{trigger_type}",
            event_trigger.CONF_EVENT_DATA: {CONF_DEVICE_ID: device_id},
        }
    )
    
    return await event_trigger.async_attach_trigger(
        hass, event_config, action, trigger_info, platform_type="device"
    )


def fire_device_trigger(
    hass: HomeAssistant,
    device_id: str,
    trigger_type: str,
    extra_data: dict[str, Any] | None = None,
) -> None:
    """Fire a device trigger event."""
    if trigger_type not in TRIGGER_TYPES:
        _LOGGER.warning("Unknown trigger type: %s", trigger_type)
        return
    
    event_data = {
        CONF_DEVICE_ID: device_id,
        "trigger_type": trigger_type,
    }
    
    if extra_data:
        event_data.update(extra_data)
    
    hass.bus.async_fire(f"{DOMAIN}_{trigger_type}", event_data)
    _LOGGER.debug("Fired device trigger: %s for device %s", trigger_type, device_id)


class DeviceEventManager:
    """Manages device events and triggers."""
    
    def __init__(self, hass: HomeAssistant, device_id: str) -> None:
        """Initialize the device event manager."""
        self._hass = hass
        self._device_id = device_id
        self._last_state: str | None = None
    
    def fire_connection_event(self, connected: bool, device_info: dict[str, Any] | None = None) -> None:
        """Fire connection state change event."""
        trigger_type = TRIGGER_CONNECTED if connected else TRIGGER_DISCONNECTED
        extra_data = {}
        
        if device_info:
            extra_data.update({
                "device_name": device_info.get("name"),
                "device_address": device_info.get("address"),
                "connection_time": device_info.get("connection_time"),
            })
        
        fire_device_trigger(self._hass, self._device_id, trigger_type, extra_data)
        self._last_state = "connected" if connected else "disconnected"
    
    def fire_pairing_event(self, event_type: str, device_info: dict[str, Any] | None = None) -> None:
        """Fire pairing-related event."""
        if event_type not in {TRIGGER_PAIRING_STARTED, TRIGGER_PAIRING_FAILED, TRIGGER_PAIRING_SUCCESS}:
            _LOGGER.warning("Invalid pairing event type: %s", event_type)
            return
        
        extra_data = {}
        if device_info:
            extra_data.update({
                "device_name": device_info.get("name"),
                "device_address": device_info.get("address"),
                "error_message": device_info.get("error_message"),
            })
        
        fire_device_trigger(self._hass, self._device_id, event_type, extra_data)
    
    def fire_audio_event(self, started: bool, audio_info: dict[str, Any] | None = None) -> None:
        """Fire audio state change event."""
        trigger_type = TRIGGER_AUDIO_STARTED if started else TRIGGER_AUDIO_STOPPED
        extra_data = {}
        
        if audio_info:
            extra_data.update({
                "codec": audio_info.get("codec"),
                "quality": audio_info.get("quality"),
                "sample_rate": audio_info.get("sample_rate"),
                "bit_depth": audio_info.get("bit_depth"),
            })
        
        fire_device_trigger(self._hass, self._device_id, trigger_type, extra_data)
    
    def fire_error_event(self, error_type: str, error_message: str, error_data: dict[str, Any] | None = None) -> None:
        """Fire error event."""
        extra_data = {
            "error_type": error_type,
            "error_message": error_message,
        }
        
        if error_data:
            extra_data.update(error_data)
        
        fire_device_trigger(self._hass, self._device_id, TRIGGER_ERROR, extra_data)
    
    @property
    def last_state(self) -> str | None:
        """Get the last known connection state."""
        return self._last_state