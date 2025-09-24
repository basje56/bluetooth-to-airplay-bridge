"""Test the Device Manager functionality."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest  # type: ignore
from typing import Any, Dict, List
from homeassistant.core import HomeAssistant  # type: ignore

from custom_components.bluetooth_to_airplay_bridge.device_manager import (
    DeviceManager,
    BluetoothDevice,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    return MagicMock(spec=HomeAssistant)


@pytest.fixture
def mock_bluetooth_scanner():
    """Mock Bluetooth scanner."""
    with patch("homeassistant.components.bluetooth.async_scanner_count", return_value=1):
        with patch("homeassistant.components.bluetooth.async_get_scanner") as mock_scanner:
            scanner_instance = MagicMock()
            mock_scanner.return_value = scanner_instance
            yield scanner_instance


class TestBluetoothDevice:
    """Test BluetoothDevice class."""

    def test_bluetooth_device_creation(self):
        """Test creating a BluetoothDevice."""
        device = BluetoothDevice(
            address="AA:BB:CC:DD:EE:FF",
            name="Test Speaker"
        )
        
        assert device.address == "AA:BB:CC:DD:EE:FF"
        assert device.name == "Test Speaker"
        assert device.is_connected is False
        assert device.is_paired is False
        assert device.signal_strength is None
        assert device.device_class is None
        assert device.services == []

    def test_bluetooth_device_properties(self):
        """Test BluetoothDevice properties."""
        device = BluetoothDevice(
            address="AA:BB:CC:DD:EE:FF",
            name="Test Speaker"
        )
        
        # Test to_dict method
        device_dict = device.to_dict()
        assert device_dict["address"] == "AA:BB:CC:DD:EE:FF"
        assert device_dict["name"] == "Test Speaker"
        assert device_dict["is_connected"] is False
        assert device_dict["is_paired"] is False
        assert device_dict["signal_strength"] is None

    def test_bluetooth_device_connection_states(self):
        """Test BluetoothDevice connection state changes."""
        device = BluetoothDevice(
            address="AA:BB:CC:DD:EE:FF",
            name="Test Speaker"
        )
        
        # Test state changes
        device.is_connected = True
        assert device.is_connected is True
        
        device.is_paired = True
        assert device.is_paired is True

    def test_bluetooth_device_string_representation(self):
        """Test string representation of BluetoothDevice."""
        device = BluetoothDevice(
            address="AA:BB:CC:DD:EE:FF",
            name="Test Speaker"
        )
        
        str_repr = str(device)
        assert "Test Speaker" in str_repr
        assert "AA:BB:CC:DD:EE:FF" in str_repr


class TestDeviceManager:
    """Test DeviceManager class."""

    def test_device_manager_creation(self, mock_hass):
        """Test creating a device manager."""
        manager = DeviceManager(mock_hass)
        assert manager.devices == {}
        assert manager.active_device is None
        assert manager.connected_devices == []
        assert manager.paired_devices == []

    def test_device_manager_properties(self, mock_hass):
        """Test device manager properties."""
        manager = DeviceManager(mock_hass)
        
        # Add a device to test properties
        device = BluetoothDevice("AA:BB:CC:DD:EE:FF", "Test Speaker")
        device.is_connected = True
        device.is_paired = True
        manager._devices["AA:BB:CC:DD:EE:FF"] = device
        
        # Test connected devices
        connected = manager.connected_devices
        assert len(connected) == 1
        assert connected[0].name == "Test Speaker"
        
        # Test paired devices
        paired = manager.paired_devices
        assert len(paired) == 1
        assert paired[0].name == "Test Speaker"

    def test_add_remove_callbacks(self, mock_hass):
        """Test adding and removing callbacks."""
        manager = DeviceManager(mock_hass)
        device_callback = MagicMock()
        connection_callback = MagicMock()
        
        # Add callbacks
        manager.add_device_callback(device_callback)
        manager.add_connection_callback(connection_callback)
        
        # Remove callbacks
        manager.remove_device_callback(device_callback)
        manager.remove_connection_callback(connection_callback)

    @pytest.mark.asyncio
    async def test_start_scanning(self, mock_hass):
        """Test starting device scanning."""
        manager = DeviceManager(mock_hass)
        
        # Mock the scanning process
        with patch.object(manager, '_update_device_list', new_callable=AsyncMock):
            await manager.start_scanning(duration=1)

    @pytest.mark.asyncio
    async def test_stop_scanning(self, mock_hass):
        """Test stopping device scanning."""
        manager = DeviceManager(mock_hass)
        
        # Start scanning first
        manager._scanning = True
        manager._scan_task = MagicMock()
        manager._scan_task.cancel = MagicMock()
        
        await manager.stop_scanning()
        assert manager._scanning is False

    @pytest.mark.asyncio
    async def test_connect_device_success(self, mock_hass):
        """Test successful device connection."""
        manager = DeviceManager(mock_hass)
        
        # Add a device
        device = BluetoothDevice("AA:BB:CC:DD:EE:FF", "Test Speaker")
        manager._devices["AA:BB:CC:DD:EE:FF"] = device
        
        # Mock successful connection
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = await manager.connect_device("AA:BB:CC:DD:EE:FF")
            assert result is True
            assert device.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_device_not_found(self, mock_hass):
        """Test connecting to non-existent device."""
        manager = DeviceManager(mock_hass)
        
        result = await manager.connect_device("AA:BB:CC:DD:EE:FF")
        assert result is False

    @pytest.mark.asyncio
    async def test_disconnect_device_success(self, mock_hass):
        """Test successful device disconnection."""
        manager = DeviceManager(mock_hass)
        
        # Add a connected device
        device = BluetoothDevice("AA:BB:CC:DD:EE:FF", "Test Speaker")
        device.is_connected = True
        manager._devices["AA:BB:CC:DD:EE:FF"] = device
        
        # Mock successful disconnection
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = await manager.disconnect_device("AA:BB:CC:DD:EE:FF")
            assert result is True
            assert device.is_connected is False

    @pytest.mark.asyncio
    async def test_pair_device_success(self, mock_hass):
        """Test successful device pairing."""
        manager = DeviceManager(mock_hass)
        
        # Add a device
        device = BluetoothDevice("AA:BB:CC:DD:EE:FF", "Test Speaker")
        manager._devices["AA:BB:CC:DD:EE:FF"] = device
        
        # Mock successful pairing
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = await manager.pair_device("AA:BB:CC:DD:EE:FF")
            assert result is True
            assert device.is_paired is True

    @pytest.mark.asyncio
    async def test_unpair_device_success(self, mock_hass):
        """Test successful device unpairing."""
        manager = DeviceManager(mock_hass)
        
        # Add a paired device
        device = BluetoothDevice("AA:BB:CC:DD:EE:FF", "Test Speaker")
        device.is_paired = True
        manager._devices["AA:BB:CC:DD:EE:FF"] = device
        
        # Mock successful unpairing
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = await manager.unpair_device("AA:BB:CC:DD:EE:FF")
            assert result is True
            assert device.is_paired is False

    def test_active_device_property(self, mock_hass):
        """Test active device property."""
        manager = DeviceManager(mock_hass)
        
        # Test with no active device
        assert manager.active_device is None
        
        # Add a device and set as active
        device = BluetoothDevice("AA:BB:CC:DD:EE:FF", "Test Speaker")
        manager._devices["AA:BB:CC:DD:EE:FF"] = device
        manager._active_device = "AA:BB:CC:DD:EE:FF"
        
        # Test getting active device
        active = manager.active_device
        assert active == device

    @pytest.mark.asyncio
    async def test_refresh_devices(self, mock_hass):
        """Test refreshing device list."""
        manager = DeviceManager(mock_hass)
        
        # Mock the update process
        with patch.object(manager, '_update_device_list', new_callable=AsyncMock):
            await manager.refresh_devices()

    def test_device_callbacks(self, mock_hass):
        """Test device callback functionality."""
        manager = DeviceManager(mock_hass)
        callback = MagicMock()
        manager.add_device_callback(callback)
        
        # Test that callback is added
        assert callback in manager._device_callbacks

    def test_connection_callbacks(self, mock_hass):
        """Test connection callback functionality."""
        manager = DeviceManager(mock_hass)
        callback = MagicMock()
        manager.add_connection_callback(callback)
        
        # Test that callback is added
        assert callback in manager._connection_callbacks

    def test_device_management_edge_cases(self, mock_hass):
        """Test edge cases in device management."""
        manager = DeviceManager(mock_hass)
        
        # Test operations on empty device list
        assert manager.devices == {}
        assert manager.connected_devices == []
        assert manager.paired_devices == []
        assert manager.active_device is None

    @pytest.mark.asyncio
    async def test_device_operations_error_handling(self, mock_hass):
        """Test error handling in device operations."""
        manager = DeviceManager(mock_hass)
        
        # Test operations that should handle errors gracefully
        result = await manager.connect_device("INVALID:ADDRESS")
        assert result is False
        
        result = await manager.disconnect_device("INVALID:ADDRESS")
        assert result is False
        
        result = await manager.pair_device("INVALID:ADDRESS")
        assert result is False
        
        result = await manager.unpair_device("INVALID:ADDRESS")
        assert result is False