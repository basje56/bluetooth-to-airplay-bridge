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
    SERVICE_CONNECT_DEVICE,
    SERVICE_DISCONNECT_BLUETOOTH,
    SERVICE_DISCONNECT_DEVICE,
    SERVICE_GET_AIRPLAY_RECEIVERS,
    SERVICE_PAIR_DEVICE,
    SERVICE_RECONNECT,
    SERVICE_REFRESH_AIRPLAY_DISCOVERY,
    SERVICE_REFRESH_DEVICES,
    SERVICE_SCAN_DEVICES,
    SERVICE_START_AIRPLAY_DISCOVERY,
    SERVICE_START_BRIDGE,
    SERVICE_STOP_AIRPLAY_DISCOVERY,
    SERVICE_STOP_BRIDGE,
    SERVICE_SWITCH_DEVICE,
    SERVICE_UNPAIR_DEVICE,
    STATE_CONNECTED,
    STATE_CONNECTING,
    STATE_DISCONNECTED,
    STATE_ERROR,
)
from .audio_engine import AudioEngine
from .airplay_server import AirPlayServer
from .mdns_advertiser import mDNSAdvertiser
from .error_handler import ErrorHandler, ErrorType, RetryConfig
from .audio_config import AudioConfigManager, AudioQuality
from .device_trigger import DeviceEventManager
from .device_manager import DeviceManager
from .volume_sync import VolumeSynchronizer
from .metadata_manager import MetadataManager
from .airplay_discovery import AirPlayDiscoveryManager

_LOGGER = logging.getLogger(__name__)

# Log that the integration module is being loaded
_LOGGER.info("Bluetooth to AirPlay Bridge integration module loaded successfully")

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]

RECONNECT_INTERVAL = timedelta(minutes=1)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Bluetooth to AirPlay Bridge integration."""
    _LOGGER.info("Setting up Bluetooth to AirPlay Bridge integration")
    
    # Initialize the domain data
    hass.data.setdefault(DOMAIN, {})
    
    return True


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

    # Set up options update listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_update_options(entry.options)


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

    async def disconnect_bluetooth_service(call: ServiceCall) -> None:
        """Disconnect the Bluetooth device."""
        await coordinator._async_disconnect_bluetooth_device()

    async def scan_devices_service(call: ServiceCall) -> None:
        """Scan for Bluetooth devices."""
        duration = call.data.get("duration", 10)
        await coordinator.device_manager.start_scanning(duration)

    async def connect_device_service(call: ServiceCall) -> None:
        """Connect to a Bluetooth device."""
        address = call.data.get("address")
        if address:
            await coordinator.device_manager.connect_device(address)

    async def disconnect_device_service(call: ServiceCall) -> None:
        """Disconnect from a Bluetooth device."""
        address = call.data.get("address")
        if address:
            await coordinator.device_manager.disconnect_device(address)

    async def pair_device_service(call: ServiceCall) -> None:
        """Pair with a Bluetooth device."""
        address = call.data.get("address")
        if address:
            await coordinator.device_manager.pair_device(address)

    async def unpair_device_service(call: ServiceCall) -> None:
        """Unpair from a Bluetooth device."""
        address = call.data.get("address")
        if address:
            await coordinator.device_manager.unpair_device(address)

    async def switch_device_service(call: ServiceCall) -> None:
        """Switch to a different Bluetooth device."""
        address = call.data.get("address")
        if address:
            # Disconnect current device and connect to new one
            await coordinator._async_disconnect_bluetooth_device()
            await coordinator.device_manager.connect_device(address)

    async def refresh_devices_service(call: ServiceCall) -> None:
        """Refresh the device list."""
        await coordinator.device_manager.refresh_devices()

    # AirPlay discovery services
    async def start_airplay_discovery_service(call: ServiceCall) -> None:
        """Start AirPlay receiver discovery."""
        await coordinator.airplay_discovery.start_discovery()

    async def stop_airplay_discovery_service(call: ServiceCall) -> None:
        """Stop AirPlay receiver discovery."""
        await coordinator.airplay_discovery.stop_discovery()

    async def refresh_airplay_discovery_service(call: ServiceCall) -> None:
        """Refresh AirPlay receiver discovery."""
        await coordinator.airplay_discovery.refresh_discovery()

    async def get_airplay_receivers_service(call: ServiceCall) -> None:
        """Get discovered AirPlay receivers."""
        receiver_type = call.data.get("receiver_type", "all")
        
        if receiver_type == "airplay2":
            receivers = coordinator.airplay_discovery.airplay2_receivers
        elif receiver_type == "audio_capable":
            receivers = coordinator.airplay_discovery.audio_receivers
        else:
            receivers = list(coordinator.airplay_discovery.receivers.values())
        
        # Convert to dict format for service response
        receiver_data = [receiver.to_dict() for receiver in receivers]
        
        # Log the results for debugging
        _LOGGER.info("Found %d AirPlay receivers of type '%s'", len(receiver_data), receiver_type)
        for receiver in receiver_data:
            _LOGGER.debug("AirPlay receiver: %s", receiver)

    hass.services.async_register(DOMAIN, SERVICE_START_BRIDGE, start_bridge_service)
    hass.services.async_register(DOMAIN, SERVICE_STOP_BRIDGE, stop_bridge_service)
    hass.services.async_register(DOMAIN, SERVICE_RECONNECT, reconnect_service)
    hass.services.async_register(DOMAIN, SERVICE_DISCONNECT_BLUETOOTH, disconnect_bluetooth_service)
    hass.services.async_register(DOMAIN, SERVICE_SCAN_DEVICES, scan_devices_service)
    hass.services.async_register(DOMAIN, SERVICE_CONNECT_DEVICE, connect_device_service)
    hass.services.async_register(DOMAIN, SERVICE_DISCONNECT_DEVICE, disconnect_device_service)
    hass.services.async_register(DOMAIN, SERVICE_PAIR_DEVICE, pair_device_service)
    hass.services.async_register(DOMAIN, SERVICE_UNPAIR_DEVICE, unpair_device_service)
    hass.services.async_register(DOMAIN, SERVICE_SWITCH_DEVICE, switch_device_service)
    hass.services.async_register(DOMAIN, SERVICE_REFRESH_DEVICES, refresh_devices_service)
    
    # Register AirPlay discovery services
    hass.services.async_register(DOMAIN, SERVICE_START_AIRPLAY_DISCOVERY, start_airplay_discovery_service)
    hass.services.async_register(DOMAIN, SERVICE_STOP_AIRPLAY_DISCOVERY, stop_airplay_discovery_service)
    hass.services.async_register(DOMAIN, SERVICE_REFRESH_AIRPLAY_DISCOVERY, refresh_airplay_discovery_service)
    hass.services.async_register(DOMAIN, SERVICE_GET_AIRPLAY_RECEIVERS, get_airplay_receivers_service)


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
        
        # Initialize error handler
        self._error_handler = ErrorHandler()
        
        # Initialize audio configuration
        self._audio_config = AudioConfigManager()
        
        # Initialize audio components
        self._audio_engine = AudioEngine(
            bluetooth_address=self._bluetooth_address,
            airplay_name=self._airplay_name
        )
        self._airplay_server = AirPlayServer(
            name=self._airplay_name,
            port=5000  # Default AirPlay port
        )
        self._mdns_advertiser = mDNSAdvertiser(
            service_name=self._airplay_name,
            port=5000,
            version=self._airplay_version
        )
        
        # Initialize device event manager
        device_registry = dr.async_get(hass)
        device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, self._bluetooth_address)},
            name=self._bluetooth_name,
            manufacturer="Bluetooth to AirPlay Bridge",
            model="Audio Bridge",
        )
        self._device_event_manager = DeviceEventManager(hass, device.id)
        
        # Initialize volume synchronizer (will be set up after start)
        self._volume_synchronizer: Optional[VolumeSynchronizer] = None
        
        # Initialize metadata manager
        self._metadata_manager = MetadataManager(
            hass=hass,
            bluetooth_address=self._bluetooth_address,
            airplay_name=self._airplay_name
        )
        
        # Initialize device manager
        self._device_manager = DeviceManager(hass)
        self._device_manager.add_connection_callback(self._on_device_connection_changed)
        
        # Initialize AirPlay discovery manager
        self._airplay_discovery = AirPlayDiscoveryManager(hass)

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
            "sw_version": "0.10.0",
        }
        
    @property
    def audio_engine(self) -> AudioEngine:
        """Return the audio engine."""
        return self._audio_engine
        
    @property
    def airplay_server(self) -> AirPlayServer:
        """Return the AirPlay server."""
        return self._airplay_server
        
    @property
    def mdns_advertiser(self) -> mDNSAdvertiser:
        """Return the mDNS advertiser."""
        return self._mdns_advertiser
        
    @property
    def audio_config(self) -> AudioConfigManager:
        """Get the audio configuration manager."""
        return self._audio_config
    
    @property
    def device_event_manager(self) -> DeviceEventManager:
        """Get the device event manager."""
        return self._device_event_manager
    
    @property
    def volume_synchronizer(self) -> Optional[VolumeSynchronizer]:
        """Get the volume synchronizer."""
        return self._volume_synchronizer
        
    @property
    def metadata_manager(self) -> MetadataManager:
        """Get the metadata manager."""
        return self._metadata_manager
        
    @property
    def device_manager(self) -> DeviceManager:
        """Get device manager."""
        return self._device_manager
        
    @property
    def airplay_discovery(self) -> AirPlayDiscoveryManager:
        """Get AirPlay discovery manager."""
        return self._airplay_discovery
        
    async def get_audio_status(self) -> dict[str, Any]:
        """Get comprehensive audio status."""
        return {
            "audio_engine": self._audio_engine.get_audio_info(),
            "airplay_server": await self._airplay_server.get_status(),
            "mdns_advertiser": self._mdns_advertiser.get_status(),
            "bluetooth_connected": self._state == STATE_CONNECTED,
            "last_seen": self._last_seen.isoformat() if self._last_seen else None,
            "audio_config": self._audio_config.get_settings_dict()
        }
        
    async def set_audio_quality(self, quality: AudioQuality) -> bool:
        """Set audio quality preset."""
        success = self._audio_config.set_quality_preset(quality)
        if success and self._state == STATE_CONNECTED:
            # Apply new settings to audio engine
            settings = self._audio_config.current_settings
            await self._audio_engine.set_codec(settings.codec.value)
            await self._audio_engine.set_audio_quality(
                settings.sample_rate.value, 
                settings.channels
            )
        return success
        
    async def update_audio_setting(self, key: str, value: Any) -> bool:
        """Update a specific audio setting."""
        try:
            success = self._audio_config.update_setting(key, value)
            if success:
                _LOGGER.info("Updated audio setting %s to %s", key, value)
                # Restart audio pipeline if needed
                if self._state == STATE_CONNECTED:
                    await self._async_stop_airplay_bridge()
                    await self._async_start_airplay_bridge()
            return success
        except Exception as err:
            _LOGGER.error("Error updating audio setting %s: %s", key, err)
            return False

    def _on_device_connection_changed(self, address: str, connected: bool) -> None:
        """Handle device connection status changes."""
        _LOGGER.info("Device %s connection changed: %s", address, connected)
        
        # If this is our configured device, update our state
        if address == self._bluetooth_address:
            if connected:
                self._state = STATE_CONNECTED
                self._last_seen = datetime.now()
            else:
                self._state = STATE_DISCONNECTED

    async def async_update_options(self, options: dict[str, Any]) -> None:
        """Update coordinator with new options."""
        _LOGGER.info("Updating options: %s", options)
        
        # Update audio quality if changed
        if "audio_quality" in options:
            try:
                quality = AudioQuality(options["audio_quality"])
                await self.set_audio_quality(quality)
            except (ValueError, KeyError) as err:
                _LOGGER.error("Invalid audio quality option: %s", err)
        
        # Update auto reconnect setting
        if "auto_reconnect" in options:
            self._auto_reconnect = options["auto_reconnect"]
            _LOGGER.info("Auto reconnect set to: %s", self._auto_reconnect)
        
        # Update connection timeout
        if "connection_timeout" in options:
            self._connection_timeout = options["connection_timeout"]
            _LOGGER.info("Connection timeout set to: %s seconds", self._connection_timeout)
        
        # Update AirPlay settings if changed (requires restart)
        airplay_changed = False
        if "airplay_name" in options and options["airplay_name"] != self.airplay_name:
            airplay_changed = True
        if "airplay_version" in options and options["airplay_version"] != self.airplay_version:
            airplay_changed = True
            
        if airplay_changed and self._state == STATE_CONNECTED:
            _LOGGER.info("AirPlay settings changed, restarting bridge")
            await self._async_stop_airplay_bridge()
            await self._async_start_airplay_bridge()

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
            
            # Initialize and start volume synchronizer
            if self._volume_synchronizer is None:
                self._volume_synchronizer = VolumeSynchronizer(
                    hass=self.hass,
                    bluetooth_volume_getter=self._audio_engine.get_bluetooth_volume,
                    bluetooth_volume_setter=self._audio_engine.set_bluetooth_volume,
                    airplay_volume_getter=self._airplay_server.get_volume,
                    airplay_volume_setter=self._airplay_server.set_volume_float,
                )
                await self._volume_synchronizer.start_sync()
                
            # Start metadata monitoring
            await self._metadata_manager.start_monitoring()
            
            # Start device manager
            await self._device_manager.start_scanning()
            
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

        # Stop volume synchronizer
        if self._volume_synchronizer:
            await self._volume_synchronizer.stop_sync()
            
        # Stop metadata monitoring
        await self._metadata_manager.stop_monitoring()
        
        # Stop device manager
        await self._device_manager.stop_scanning()

        await self._async_stop_airplay_bridge()
        await self._async_disconnect_bluetooth_device()
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
        async def _check_connection() -> bool:
            result = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                "info",
                self._bluetooth_address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                output = stdout.decode()
                connected = "Connected: yes" in output
                if connected:
                    self._last_seen = datetime.now()
                    self._state = STATE_CONNECTED
                return connected
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise RuntimeError(f"Failed to check device connection: {error_msg}")
        
        try:
            # Use error handler with minimal retry for connection checks
            retry_config = RetryConfig(max_retries=1, base_delay=0.5, max_delay=2.0)
            return await self._error_handler.retry_with_backoff(
                _check_connection,
                retry_config=retry_config,
                error_context={
                    "component": "bluetooth_connection",
                    "bluetooth_address": self._bluetooth_address,
                    "operation": "check_connection"
                }
            )
        except Exception as err:
            _LOGGER.debug("Device connection check failed: %s", err)
            return False

    async def _async_connect_device(self) -> bool:
        """Connect to the Bluetooth device with retry logic."""
        async def _connect_attempt() -> bool:
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
                
                # Fire connection event
                device_info = {
                    "name": self._bluetooth_name,
                    "address": self._bluetooth_address,
                    "connection_time": self._last_seen.isoformat(),
                }
                self._device_event_manager.fire_connection_event(True, device_info)
                
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                _LOGGER.warning("Connection attempt failed: %s", error_msg)
                raise ConnectionError(f"Failed to connect to device: {error_msg}")
        
        try:
            # Use error handler with retry logic
            retry_config = RetryConfig(max_retries=3, base_delay=2.0, max_delay=10.0)
            result = await self._error_handler.retry_with_backoff(
                _connect_attempt,
                retry_config=retry_config,
                error_context={
                    "component": "bluetooth_connection",
                    "bluetooth_address": self._bluetooth_address,
                    "operation": "connect"
                }
            )
            return result
        except Exception as err:
            _LOGGER.error("Failed to connect to device after retries: %s", err)
            self._state = STATE_ERROR
            return False

    async def _async_start_airplay_bridge(self) -> None:
        """Start the AirPlay bridge process."""
        async def _start_mdns() -> bool:
            success = await self._mdns_advertiser.start_advertising()
            if not success:
                raise RuntimeError("Failed to start mDNS advertising")
            return success
            
        async def _start_airplay() -> bool:
            success = await self._airplay_server.start()
            if not success:
                raise RuntimeError("Failed to start AirPlay server")
            return success
            
        async def _start_audio() -> bool:
            # Check if Bluetooth audio is available first
            audio_available = await self._audio_engine.check_bluetooth_audio_available()
            if not audio_available:
                raise RuntimeError("Bluetooth audio not available")
                
            success = await self._audio_engine.start_audio_capture()
            if not success:
                raise RuntimeError("Failed to start audio capture")
            return success
        
        try:
            _LOGGER.debug("Starting AirPlay bridge process")
            
            # Start mDNS advertising with retry
            retry_config = RetryConfig(max_retries=2, base_delay=1.0, max_delay=5.0)
            try:
                await self._error_handler.retry_with_backoff(
                    _start_mdns,
                    retry_config=retry_config,
                    error_context={
                        "component": "mdns_advertiser",
                        "operation": "start_advertising"
                    }
                )
            except Exception:
                _LOGGER.warning("Failed to start mDNS advertising after retries, AirPlay may not be discoverable")
            
            # Start AirPlay server with retry
            await self._error_handler.retry_with_backoff(
                _start_airplay,
                retry_config=retry_config,
                error_context={
                    "component": "airplay_server",
                    "operation": "start"
                }
            )
            
            # Start audio capture with retry (more lenient)
            audio_retry_config = RetryConfig(max_retries=3, base_delay=2.0, max_delay=10.0)
            try:
                await self._error_handler.retry_with_backoff(
                    _start_audio,
                    retry_config=audio_retry_config,
                    error_context={
                        "component": "audio_engine",
                        "operation": "start_capture"
                    }
                )
            except Exception:
                _LOGGER.warning("Failed to start audio capture after retries, will retry when audio becomes available")
            
            _LOGGER.info("AirPlay bridge started successfully")
            
            # Fire audio started event
            audio_info = {
                "codec": self._audio_config.current_settings.codec.value,
                "quality": self._audio_config.current_settings.quality.value,
                "sample_rate": self._audio_config.current_settings.sample_rate.value,
                "bit_depth": self._audio_config.current_settings.bit_depth.value,
            }
            self._device_event_manager.fire_audio_event(True, audio_info)
            
        except Exception as err:
            _LOGGER.error("Error starting AirPlay bridge: %s", err)
            # Clean up on error
            await self._airplay_server.stop()
            await self._mdns_advertiser.stop_advertising()
            await self._audio_engine.stop_audio_capture()
            raise

    async def _async_stop_airplay_bridge(self) -> None:
        """Stop the AirPlay bridge process."""
        try:
            _LOGGER.debug("Stopping AirPlay bridge")
            
            # Stop audio capture
            await self._audio_engine.stop_audio_capture()
            
            # Stop AirPlay server
            await self._airplay_server.stop()
            
            # Stop mDNS advertising
            await self._mdns_advertiser.stop_advertising()
            
            _LOGGER.info("AirPlay bridge stopped successfully")
            
            # Fire audio stopped event
            self._device_event_manager.fire_audio_event(False)
            
        except Exception as err:
            _LOGGER.error("Error stopping AirPlay bridge: %s", err)

    async def _async_disconnect_bluetooth_device(self) -> None:
        """Disconnect the Bluetooth device."""
        try:
            _LOGGER.info("Disconnecting Bluetooth device: %s", self.bluetooth_address)
            
            # Use bluetoothctl to disconnect the device
            disconnect_cmd = [
                "bluetoothctl",
                "disconnect",
                self.bluetooth_address
            ]
            
            process = await asyncio.create_subprocess_exec(
                *disconnect_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            
            if process.returncode == 0:
                _LOGGER.info("Successfully disconnected Bluetooth device: %s", self.bluetooth_address)
                self._state = STATE_DISCONNECTED
                
                # Fire disconnection event
                device_info = {
                    "name": self._bluetooth_name,
                    "address": self._bluetooth_address,
                }
                self._device_event_manager.fire_connection_event(False, device_info)
            else:
                _LOGGER.warning(
                    "Failed to disconnect Bluetooth device %s: %s", 
                    self.bluetooth_address, 
                    stderr.decode().strip()
                )
                
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout while disconnecting Bluetooth device: %s", self.bluetooth_address)
        except Exception as err:
            _LOGGER.error("Error disconnecting Bluetooth device %s: %s", self.bluetooth_address, err)