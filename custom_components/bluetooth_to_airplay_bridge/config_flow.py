"""Config flow for Bluetooth to AirPlay Bridge integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import voluptuous as vol  # type: ignore

from homeassistant import config_entries  # type: ignore
try:
    from homeassistant.components import bluetooth  # type: ignore
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    bluetooth = None
from homeassistant.const import CONF_NAME  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.data_entry_flow import FlowResult  # type: ignore
from homeassistant.exceptions import HomeAssistantError  # type: ignore

from .const import (
    AIRPLAY_VERSIONS,
    CONF_AIRPLAY_NAME,
    CONF_AIRPLAY_VERSION,
    CONF_BLUETOOTH_ADDRESS,
    CONF_BLUETOOTH_NAME,
    DEFAULT_AIRPLAY_NAME,
    DEFAULT_SCAN_TIMEOUT,
    DOMAIN,
    ERROR_BLUETOOTH_NOT_AVAILABLE,
    ERROR_DEVICE_NOT_FOUND,
    ERROR_PAIRING_FAILED,
)

_LOGGER = logging.getLogger(__name__)

# Log that the config flow module is being loaded
_LOGGER.info("Bluetooth to AirPlay Bridge config flow module loaded successfully")


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bluetooth to AirPlay Bridge."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: list[dict[str, Any]] = []
        self._selected_device: dict[str, Any] | None = None

    async def async_step_bluetooth(
        self, discovery_info: dict[str, Any]
    ) -> FlowResult:
        """Handle Bluetooth discovery."""
        _LOGGER.info("Bluetooth discovery step called with info: %s", discovery_info)
        
        if not BLUETOOTH_AVAILABLE:
            return self.async_abort(reason="bluetooth_not_available")
        
        # Extract device information from discovery
        device_address = discovery_info.get("address")
        device_name = discovery_info.get("name", "Unknown Device")
        
        if not device_address:
            return self.async_abort(reason="no_device_address")
        
        # Check if already configured
        await self.async_set_unique_id(device_address)
        self._abort_if_unique_id_configured()
        
        # Store discovered device info
        self._selected_device = {
            "address": device_address,
            "name": device_name,
        }
        
        # Set the title for the flow
        self.context["title_placeholders"] = {"name": device_name}
        
        # Go directly to configuration step since device is already discovered
        return await self.async_step_configure()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - discovery instructions."""
        if user_input is not None:
            return await self.async_step_scan()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "instructions": "Put the Bluetooth speaker into discover mode. Then click Next."
            },
        )

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the scanning step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if "selected_device" in user_input:
                # Device selected, move to pairing
                device_address = user_input["selected_device"]
                self._selected_device = next(
                    (d for d in self._discovered_devices 
                     if isinstance(d, dict) and d.get("address") == device_address),
                    None,
                )
                if self._selected_device is not None and isinstance(self._selected_device, dict):
                    device_address = str(self._selected_device.get("address", ""))
                    device_name = str(self._selected_device.get("name", ""))
                    if device_address:
                        return await self.async_step_pair()
                    else:
                        errors["base"] = ERROR_DEVICE_NOT_FOUND
                else:
                    errors["base"] = ERROR_DEVICE_NOT_FOUND

        # Check if Bluetooth is available
        if not BLUETOOTH_AVAILABLE or not bluetooth or not bluetooth.async_scanner_count(self.hass):
            errors["base"] = ERROR_BLUETOOTH_NOT_AVAILABLE
            return self.async_show_form(
                step_id="scan",
                errors=errors,
            )

        # Scan for devices
        try:
            self._discovered_devices = await self._async_scan_devices()
        except Exception as err:
            _LOGGER.error("Error scanning for devices: %s", err)
            errors["base"] = "scan_failed"

        if not self._discovered_devices:
            errors["base"] = "no_devices_found"

        # Create device selection schema
        device_options = {
            device["address"]: f"{device['name']} ({device['address']})"
            for device in self._discovered_devices
        }

        data_schema = vol.Schema({})
        if device_options:
            data_schema = vol.Schema({
                vol.Required("selected_device"): vol.In(device_options)
            })

        return self.async_show_form(
            step_id="scan",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "scan_status": "Scanning..." if not self._discovered_devices else f"Found {len(self._discovered_devices)} devices"
            },
        )

    async def async_step_pair(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the pairing and configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if "pair_device" in user_input and user_input["pair_device"]:
                # Attempt to pair
                try:
                    if self._selected_device and isinstance(self._selected_device, dict):
                        device_address = str(self._selected_device.get("address", ""))
                        if device_address:
                            success = await self._async_pair_device(device_address)
                            if success:
                                return await self.async_step_configure()
                            else:
                                errors["base"] = ERROR_PAIRING_FAILED
                        else:
                            errors["base"] = ERROR_PAIRING_FAILED
                    else:
                        errors["base"] = ERROR_PAIRING_FAILED
                except Exception as err:
                    _LOGGER.error("Error pairing device: %s", err)
                    errors["base"] = ERROR_PAIRING_FAILED

        if not self._selected_device:
            return await self.async_step_scan()

        return self.async_show_form(
            step_id="pair",
            data_schema=vol.Schema({
                vol.Required("pair_device", default=False): bool,
            }),
            errors=errors,
            description_placeholders={
                "device_name": str(self._selected_device.get("name", "")) if self._selected_device and isinstance(self._selected_device, dict) else "",
                "device_address": str(self._selected_device.get("address", "")) if self._selected_device and isinstance(self._selected_device, dict) else "",
                "pair_status": "Ready to pair" if not errors else "Pairing failed, try again"
            },
        )

    async def async_step_configure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the final configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate input
            airplay_name = user_input.get(CONF_AIRPLAY_NAME, DEFAULT_AIRPLAY_NAME).strip()
            airplay_version = user_input.get(CONF_AIRPLAY_VERSION)

            if not airplay_name:
                errors[CONF_AIRPLAY_NAME] = "name_required"
            elif len(airplay_name) > 50:
                errors[CONF_AIRPLAY_NAME] = "name_too_long"

            if not errors and self._selected_device and isinstance(self._selected_device, dict):
                device_address = str(self._selected_device.get("address", ""))
                device_name = str(self._selected_device.get("name", ""))
                
                if device_address:
                    # Check for existing entries with the same device
                    await self.async_set_unique_id(device_address)
                    self._abort_if_unique_id_configured()

                    # Create the config entry
                    return self.async_create_entry(
                        title=f"AirPlay Bridge ({device_name})",
                        data={
                            CONF_BLUETOOTH_ADDRESS: device_address,
                            CONF_BLUETOOTH_NAME: device_name,
                            CONF_AIRPLAY_NAME: airplay_name,
                            CONF_AIRPLAY_VERSION: airplay_version,
                        },
                    )
                else:
                    errors["base"] = ERROR_DEVICE_NOT_FOUND

        if not self._selected_device:
            return await self.async_step_scan()

        return self.async_show_form(
            step_id="configure",
            data_schema=vol.Schema({
                vol.Required(CONF_AIRPLAY_VERSION, default=AIRPLAY_VERSIONS[1]): vol.In(
                    {version: f"AirPlay {version[-1]}" for version in AIRPLAY_VERSIONS}
                ),
                vol.Required(CONF_AIRPLAY_NAME, default=DEFAULT_AIRPLAY_NAME): str,
            }),
            errors=errors,
            description_placeholders={
                "device_name": str(self._selected_device.get("name", "")) if self._selected_device and isinstance(self._selected_device, dict) else "",
                "device_address": str(self._selected_device.get("address", "")) if self._selected_device and isinstance(self._selected_device, dict) else "",
            },
        )

    async def _async_scan_devices(self) -> list[dict[str, Any]]:
        """Scan for Bluetooth devices."""
        _LOGGER.debug("Starting Bluetooth device scan")
        
        try:
            # Use bluetoothctl to scan for devices
            scan_process = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                "scan",
                "on",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            # Wait a bit for scanning to start
            await asyncio.sleep(2)
            
            # Stop scanning
            await asyncio.create_subprocess_exec(
                "bluetoothctl",
                "scan",
                "off",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            # Get discovered devices
            devices_process = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                "devices",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await devices_process.communicate()
            
            devices = []
            if devices_process.returncode == 0:
                lines = stdout.decode().strip().split('\n')
                for line in lines:
                    if line.startswith('Device '):
                        parts = line.split(' ', 2)
                        if len(parts) >= 3:
                            address = parts[1]
                            name = parts[2] if len(parts) > 2 else f"Unknown Device ({address})"
                            devices.append({
                                "address": address,
                                "name": name,
                            })
            
            _LOGGER.debug("Found %d devices", len(devices))
            return devices
            
        except Exception as err:
            _LOGGER.error("Error scanning for devices: %s", err)
            raise CannotConnect from err

    async def _async_pair_device(self, address: str) -> bool:
        """Pair with a Bluetooth device."""
        _LOGGER.debug("Attempting to pair with device: %s", address)
        
        try:
            # First, try to trust the device
            trust_process = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                "trust",
                address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await trust_process.communicate()
            
            # Then pair
            pair_process = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                "pair",
                address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await pair_process.communicate()
            
            if pair_process.returncode == 0:
                _LOGGER.debug("Successfully paired with device: %s", address)
                return True
            else:
                _LOGGER.error(
                    "Failed to pair with device %s: %s", 
                    address, 
                    stderr.decode() if stderr else "Unknown error"
                )
                return False
                
        except Exception as err:
            _LOGGER.error("Error pairing with device %s: %s", address, err)
            return False


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""