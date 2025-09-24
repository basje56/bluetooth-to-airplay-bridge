"""The Bluetooth to AirPlay Bridge integration."""
from __future__ import annotations

import asyncio
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Any, Optional

try:
    from homeassistant.components import bluetooth  # type: ignore
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    bluetooth = None
from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.const import Platform  # type: ignore
from homeassistant.core import HomeAssistant, ServiceCall  # type: ignore
from homeassistant.exceptions import ConfigEntryNotReady  # type: ignore
from homeassistant.helpers import device_registry as dr  # type: ignore
from homeassistant.helpers.event import async_track_time_interval  # type: ignore

from .const import (
    ATTR_BLUETOOTH_ADDRESS,
    ATTR_BLUETOOTH_NAME,
    ATTR_CONNECTION_STATE,
    CONF_AIRPLAY_NAME,
    CONF_AIRPLAY_VERSION,
    CONF_BLUETOOTH_ADDRESS,
    CONF_BLUETOOTH_NAME,
    DOMAIN,
    SERVICE_RECONNECT,
    SERVICE_START_BRIDGE,
    SERVICE_STOP_BRIDGE,
    STATE_CONNECTED,
    STATE_CONNECTING,
    STATE_DISCONNECTED,
    STATE_ERROR,
)

_LOGGER = logging.getLogger(__name__)

# Log that the integration module is being loaded
_LOGGER.info("Bluetooth to AirPlay Bridge integration module loaded successfully")

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]

RECONNECT_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bluetooth to AirPlay Bridge from a config entry."""
    _LOGGER.debug(
        "Setting up Bluetooth to AirPlay Bridge: %s",
        {
            "bluetooth_address": entry.data[CONF_BLUETOOTH_ADDRESS],
            "bluetooth_name": entry.data[CONF_BLUETOOTH_NAME],
            "airplay_name": entry.data[CONF_AIRPLAY_NAME],
            "airplay_version": entry.data[CONF_AIRPLAY_VERSION],
        },
    )

    # Check if Bluetooth is available
    if not BLUETOOTH_AVAILABLE or not bluetooth or not bluetooth.async_scanner_count(hass):
        _LOGGER.error("Bluetooth is not available or not configured")
        raise ConfigEntryNotReady("Bluetooth is not available or not configured")

    # Create coordinator
    coordinator = BluetoothAirPlayCoordinator(hass, entry)
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await _async_register_services(hass, coordinator)

    # Start the bridge
    await coordinator.async_start()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Bluetooth to AirPlay Bridge: %s", entry.entry_id)
    
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _async_register_services(
    hass: HomeAssistant, coordinator: BluetoothAirPlayCoordinator
) -> None:
    """Register services for the integration."""
    
    async def start_bridge_service(call: ServiceCall) -> None:
        """Start the bridge service."""
        await coordinator.async_start()

    async def stop_bridge_service(call: ServiceCall) -> None:
        """Stop the bridge service."""
        await coordinator.async_stop()

    async def reconnect_service(call: ServiceCall) -> None:
        """Reconnect to the Bluetooth device."""
        await coordinator.async_reconnect()

    hass.services.async_register(DOMAIN, SERVICE_START_BRIDGE, start_bridge_service)
    hass.services.async_register(DOMAIN, SERVICE_STOP_BRIDGE, stop_bridge_service)
    hass.services.async_register(DOMAIN, SERVICE_RECONNECT, reconnect_service)


class BluetoothAirPlayCoordinator:
    """Coordinator for Bluetooth to AirPlay Bridge."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self._bluetooth_address = entry.data[CONF_BLUETOOTH_ADDRESS]
        self._bluetooth_name = entry.data[CONF_BLUETOOTH_NAME]
        self._airplay_name = entry.data[CONF_AIRPLAY_NAME]
        self._airplay_version = entry.data[CONF_AIRPLAY_VERSION]
        self._state = STATE_DISCONNECTED
        self._last_seen: datetime | None = None
        self._bridge_process: asyncio.subprocess.Process | None = None
        self._reconnect_task: asyncio.Task | None = None
        self._unsub_reconnect: Any = None

    @property
    def bluetooth_address(self) -> str:
        """Return the Bluetooth address."""
        return self._bluetooth_address

    @property
    def bluetooth_name(self) -> str:
        """Return the Bluetooth name."""
        return self._bluetooth_name

    @property
    def airplay_name(self) -> str:
        """Return the AirPlay name."""
        return self._airplay_name

    @property
    def airplay_version(self) -> str:
        """Return the AirPlay version."""
        return self._airplay_version

    @property
    def state(self) -> str:
        """Return the current state."""
        return self._state

    @property
    def last_seen(self) -> datetime | None:
        """Return the last seen timestamp."""
        return self._last_seen

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._bluetooth_address)},
            "name": f"AirPlay Bridge ({self._bluetooth_name})",
            "manufacturer": "Bluetooth to AirPlay Bridge",
            "model": f"Bridge {self._airplay_version.upper()}",
            "sw_version": "1.0.0",
        }

    async def async_start(self) -> None:
        """Start the bridge."""
        _LOGGER.info("Starting Bluetooth to AirPlay Bridge")
        
        try:
            self._state = STATE_CONNECTING
            
            # Check if device is already connected
            if await self._async_is_device_connected():
                _LOGGER.debug("Device already connected")
                await self._async_start_airplay_bridge()
            else:
                _LOGGER.debug("Device not connected, attempting to connect")
                if await self._async_connect_device():
                    await self._async_start_airplay_bridge()
                else:
                    self._state = STATE_ERROR
                    _LOGGER.error("Failed to connect to Bluetooth device")
                    return

            # Start reconnection monitoring
            self._unsub_reconnect = async_track_time_interval(
                self.hass, self._async_check_connection, RECONNECT_INTERVAL
            )
            
        except Exception as err:
            _LOGGER.error("Error starting bridge: %s", err)
            self._state = STATE_ERROR

    async def async_stop(self) -> None:
        """Stop the bridge."""
        _LOGGER.info("Stopping Bluetooth to AirPlay Bridge")
        
        if self._unsub_reconnect:
            self._unsub_reconnect()
            self._unsub_reconnect = None

        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()

        await self._async_stop_airplay_bridge()
        self._state = STATE_DISCONNECTED

    async def async_reconnect(self) -> None:
        """Reconnect to the Bluetooth device."""
        _LOGGER.info("Reconnecting to Bluetooth device")
        await self.async_stop()
        await self.async_start()

    async def _async_check_connection(self, now: datetime) -> None:
        """Check connection status and reconnect if needed."""
        if not await self._async_is_device_connected():
            _LOGGER.warning("Bluetooth device disconnected, attempting reconnection")
            self._state = STATE_DISCONNECTED
            
            if not self._reconnect_task or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self._async_reconnect_device())

    async def _async_reconnect_device(self) -> None:
        """Reconnect to the device."""
        try:
            self._state = STATE_CONNECTING
            if await self._async_connect_device():
                await self._async_start_airplay_bridge()
                _LOGGER.info("Successfully reconnected to Bluetooth device")
            else:
                self._state = STATE_ERROR
                _LOGGER.error("Failed to reconnect to Bluetooth device")
        except Exception as err:
            _LOGGER.error("Error during reconnection: %s", err)
            self._state = STATE_ERROR

    async def _async_is_device_connected(self) -> bool:
        """Check if the Bluetooth device is connected."""
        try:
            result = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                "info",
                self._bluetooth_address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()
            
            if result.returncode == 0:
                output = stdout.decode()
                connected = "Connected: yes" in output
                if connected:
                    self._last_seen = datetime.now()
                    self._state = STATE_CONNECTED
                return connected
            return False
        except Exception as err:
            _LOGGER.error("Error checking device connection: %s", err)
            return False

    async def _async_connect_device(self) -> bool:
        """Connect to the Bluetooth device."""
        try:
            _LOGGER.debug("Connecting to device: %s", self._bluetooth_address)
            
            result = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                "connect",
                self._bluetooth_address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                _LOGGER.debug("Successfully connected to device")
                self._last_seen = datetime.now()
                self._state = STATE_CONNECTED
                return True
            else:
                _LOGGER.error(
                    "Failed to connect to device: %s", 
                    stderr.decode() if stderr else "Unknown error"
                )
                return False
        except Exception as err:
            _LOGGER.error("Error connecting to device: %s", err)
            return False

    async def _async_start_airplay_bridge(self) -> None:
        """Start the AirPlay bridge process."""
        try:
            _LOGGER.debug("Starting AirPlay bridge process")
            
            # This is a placeholder for the actual AirPlay bridge implementation
            # In a real implementation, you would start a process that bridges
            # Bluetooth audio to AirPlay using tools like:
            # - shairport-sync for AirPlay 1
            # - uxplay for AirPlay 2
            # - Custom audio routing using PulseAudio/ALSA
            
            # For now, we'll simulate the bridge
            cmd = [
                "python3", "-c", 
                f"import time; print('AirPlay Bridge {self._airplay_name} started'); time.sleep(3600)"
            ]
            
            self._bridge_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            _LOGGER.info("AirPlay bridge started successfully")
            
        except Exception as err:
            _LOGGER.error("Error starting AirPlay bridge: %s", err)
            raise

    async def _async_stop_airplay_bridge(self) -> None:
        """Stop the AirPlay bridge process."""
        if self._bridge_process:
            try:
                self._bridge_process.terminate()
                await asyncio.wait_for(self._bridge_process.wait(), timeout=5)
                _LOGGER.debug("AirPlay bridge process stopped")
            except asyncio.TimeoutError:
                _LOGGER.warning("AirPlay bridge process did not stop gracefully, killing")
                self._bridge_process.kill()
            except Exception as err:
                _LOGGER.error("Error stopping AirPlay bridge: %s", err)
            finally:
                self._bridge_process = None