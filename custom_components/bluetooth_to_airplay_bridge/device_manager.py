"""Device manager for handling multiple Bluetooth devices."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from homeassistant.core import HomeAssistant  # type: ignore

_LOGGER = logging.getLogger(__name__)

class BluetoothDevice:
    """Represents a Bluetooth device."""
    
    def __init__(self, address: str, name: str) -> None:
        """Initialize Bluetooth device."""
        self.address = address
        self.name = name
        self.last_seen: Optional[datetime] = None
        self.is_connected = False
        self.is_paired = False
        self.signal_strength: Optional[int] = None
        self.device_class: Optional[str] = None
        self.services: list[str] = []
        
    def to_dict(self) -> dict[str, Any]:
        """Convert device to dictionary."""
        return {
            "address": self.address,
            "name": self.name,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "is_connected": self.is_connected,
            "is_paired": self.is_paired,
            "signal_strength": self.signal_strength,
            "device_class": self.device_class,
            "services": self.services,
        }
        
    def __str__(self) -> str:
        """String representation of device."""
        return f"{self.name} ({self.address})"


class DeviceManager:
    """Manages multiple Bluetooth devices."""
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize device manager."""
        self._hass = hass
        self._devices: dict[str, BluetoothDevice] = {}
        self._active_device: Optional[str] = None
        self._scanning = False
        self._scan_task: Optional[asyncio.Task] = None
        self._device_callbacks: list[Callable[[dict[str, BluetoothDevice]], None]] = []
        self._connection_callbacks: list[Callable[[str, bool], None]] = []
        
    @property
    def devices(self) -> dict[str, BluetoothDevice]:
        """Get all discovered devices."""
        return self._devices.copy()
        
    @property
    def active_device(self) -> Optional[BluetoothDevice]:
        """Get the currently active device."""
        if self._active_device and self._active_device in self._devices:
            return self._devices[self._active_device]
        return None
        
    @property
    def connected_devices(self) -> list[BluetoothDevice]:
        """Get all connected devices."""
        return [device for device in self._devices.values() if device.is_connected]
        
    @property
    def paired_devices(self) -> list[BluetoothDevice]:
        """Get all paired devices."""
        return [device for device in self._devices.values() if device.is_paired]
        
    def add_device_callback(self, callback: Callable[[dict[str, BluetoothDevice]], None]) -> None:
        """Add callback for device list updates."""
        self._device_callbacks.append(callback)
        
    def add_connection_callback(self, callback: Callable[[str, bool], None]) -> None:
        """Add callback for connection status changes."""
        self._connection_callbacks.append(callback)
        
    def remove_device_callback(self, callback: Callable[[dict[str, BluetoothDevice]], None]) -> None:
        """Remove device callback."""
        if callback in self._device_callbacks:
            self._device_callbacks.remove(callback)
            
    def remove_connection_callback(self, callback: Callable[[str, bool], None]) -> None:
        """Remove connection callback."""
        if callback in self._connection_callbacks:
            self._connection_callbacks.remove(callback)
            
    async def start_scanning(self, duration: int = 10) -> None:
        """Start scanning for Bluetooth devices."""
        if self._scanning:
            _LOGGER.debug("Already scanning for devices")
            return
            
        self._scanning = True
        _LOGGER.info("Starting Bluetooth device scan for %s seconds", duration)
        
        try:
            # Start bluetoothctl scan
            await asyncio.create_subprocess_exec(
                "bluetoothctl", "scan", "on",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Scan for specified duration
            await asyncio.sleep(duration)
            
            # Stop scanning
            await asyncio.create_subprocess_exec(
                "bluetoothctl", "scan", "off",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Update device list
            await self._update_device_list()
            
        except Exception as err:
            _LOGGER.error("Error during device scan: %s", err)
        finally:
            self._scanning = False
            
    async def stop_scanning(self) -> None:
        """Stop scanning for devices."""
        if not self._scanning:
            return
            
        self._scanning = False
        
        try:
            await asyncio.create_subprocess_exec(
                "bluetoothctl", "scan", "off",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        except Exception as err:
            _LOGGER.error("Error stopping scan: %s", err)
            
    async def connect_device(self, address: str) -> bool:
        """Connect to a Bluetooth device."""
        if address not in self._devices:
            _LOGGER.error("Device %s not found", address)
            return False
            
        device = self._devices[address]
        _LOGGER.info("Connecting to device %s", device)
        
        try:
            # Disconnect current device if any
            if self._active_device and self._active_device != address:
                await self.disconnect_device(self._active_device)
                
            # Connect to new device
            result = await asyncio.create_subprocess_exec(
                "bluetoothctl", "connect", address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                device.is_connected = True
                device.last_seen = datetime.now()
                self._active_device = address
                
                # Notify callbacks
                for callback in self._connection_callbacks:
                    try:
                        callback(address, True)
                    except Exception as err:
                        _LOGGER.error("Error in connection callback: %s", err)
                        
                _LOGGER.info("Successfully connected to %s", device)
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                _LOGGER.error("Failed to connect to %s: %s", device, error_msg)
                return False
                
        except Exception as err:
            _LOGGER.error("Error connecting to device %s: %s", address, err)
            return False
            
    async def disconnect_device(self, address: str) -> bool:
        """Disconnect from a Bluetooth device."""
        if address not in self._devices:
            _LOGGER.error("Device %s not found", address)
            return False
            
        device = self._devices[address]
        _LOGGER.info("Disconnecting from device %s", device)
        
        try:
            result = await asyncio.create_subprocess_exec(
                "bluetoothctl", "disconnect", address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                device.is_connected = False
                if self._active_device == address:
                    self._active_device = None
                    
                # Notify callbacks
                for callback in self._connection_callbacks:
                    try:
                        callback(address, False)
                    except Exception as err:
                        _LOGGER.error("Error in connection callback: %s", err)
                        
                _LOGGER.info("Successfully disconnected from %s", device)
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                _LOGGER.error("Failed to disconnect from %s: %s", device, error_msg)
                return False
                
        except Exception as err:
            _LOGGER.error("Error disconnecting from device %s: %s", address, err)
            return False
            
    async def pair_device(self, address: str) -> bool:
        """Pair with a Bluetooth device."""
        if address not in self._devices:
            _LOGGER.error("Device %s not found", address)
            return False
            
        device = self._devices[address]
        _LOGGER.info("Pairing with device %s", device)
        
        try:
            result = await asyncio.create_subprocess_exec(
                "bluetoothctl", "pair", address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                device.is_paired = True
                _LOGGER.info("Successfully paired with %s", device)
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                _LOGGER.error("Failed to pair with %s: %s", device, error_msg)
                return False
                
        except Exception as err:
            _LOGGER.error("Error pairing with device %s: %s", address, err)
            return False
            
    async def unpair_device(self, address: str) -> bool:
        """Unpair from a Bluetooth device."""
        if address not in self._devices:
            _LOGGER.error("Device %s not found", address)
            return False
            
        device = self._devices[address]
        _LOGGER.info("Unpairing from device %s", device)
        
        try:
            # Disconnect first if connected
            if device.is_connected:
                await self.disconnect_device(address)
                
            result = await asyncio.create_subprocess_exec(
                "bluetoothctl", "remove", address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                device.is_paired = False
                device.is_connected = False
                if self._active_device == address:
                    self._active_device = None
                    
                _LOGGER.info("Successfully unpaired from %s", device)
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                _LOGGER.error("Failed to unpair from %s: %s", device, error_msg)
                return False
                
        except Exception as err:
            _LOGGER.error("Error unpairing from device %s: %s", address, err)
            return False
            
    async def refresh_devices(self) -> None:
        """Refresh the device list and connection status."""
        await self._update_device_list()
        
    async def _update_device_list(self) -> None:
        """Update the list of available devices."""
        try:
            # Get paired devices
            result = await asyncio.create_subprocess_exec(
                "bluetoothctl", "devices",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                _LOGGER.error("Failed to get device list: %s", stderr.decode() if stderr else "Unknown error")
                return
                
            # Parse device list
            lines = stdout.decode().strip().split('\n')
            current_devices = set()
            
            for line in lines:
                if line.startswith('Device '):
                    parts = line.split(' ', 2)
                    if len(parts) >= 3:
                        address = parts[1]
                        name = parts[2]
                        current_devices.add(address)
                        
                        if address not in self._devices:
                            self._devices[address] = BluetoothDevice(address, name)
                        else:
                            # Update name if changed
                            self._devices[address].name = name
                            
                        # Update device details
                        await self._update_device_details(address)
                        
            # Remove devices that are no longer available
            removed_devices = set(self._devices.keys()) - current_devices
            for address in removed_devices:
                del self._devices[address]
                if self._active_device == address:
                    self._active_device = None
                    
            # Notify callbacks
            for callback in self._device_callbacks:
                try:
                    callback(self._devices)
                except Exception as err:
                    _LOGGER.error("Error in device callback: %s", err)
                    
        except Exception as err:
            _LOGGER.error("Error updating device list: %s", err)
            
    async def _update_device_details(self, address: str) -> None:
        """Update detailed information for a device."""
        if address not in self._devices:
            return
            
        device = self._devices[address]
        
        try:
            result = await asyncio.create_subprocess_exec(
                "bluetoothctl", "info", address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                info = stdout.decode()
                
                # Parse connection status
                device.is_connected = "Connected: yes" in info
                device.is_paired = "Paired: yes" in info
                
                # Parse signal strength
                rssi_match = re.search(r'RSSI: (-?\d+)', info)
                if rssi_match:
                    device.signal_strength = int(rssi_match.group(1))
                    
                # Parse device class
                class_match = re.search(r'Class: (0x[0-9a-fA-F]+)', info)
                if class_match:
                    device.device_class = class_match.group(1)
                    
                # Parse services
                device.services = []
                for line in info.split('\n'):
                    if 'UUID:' in line and '(' in line and ')' in line:
                        service_match = re.search(r'\(([^)]+)\)', line)
                        if service_match:
                            device.services.append(service_match.group(1))
                            
                # Update last seen if connected
                if device.is_connected:
                    device.last_seen = datetime.now()
                    
        except Exception as err:
            _LOGGER.debug("Error getting device details for %s: %s", address, err)