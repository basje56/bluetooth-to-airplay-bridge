"""Test the AirPlay Discovery functionality."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest  # type: ignore
from typing import Any, Dict, List
from homeassistant.core import HomeAssistant  # type: ignore

from custom_components.bluetooth_to_airplay_bridge.airplay_discovery import (
    AirPlayDiscoveryManager,
    AirPlayReceiver,
    AirPlayServiceListener,
)


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    return MagicMock(spec=HomeAssistant)


@pytest.fixture
def mock_zeroconf():
    """Mock zeroconf being available."""
    with patch("custom_components.bluetooth_to_airplay_bridge.airplay_discovery.ZEROCONF_AVAILABLE", True):
        with patch("custom_components.bluetooth_to_airplay_bridge.airplay_discovery.AsyncZeroconf") as mock_async_zeroconf:
            with patch("custom_components.bluetooth_to_airplay_bridge.airplay_discovery.AsyncServiceBrowser") as mock_browser:
                mock_zc_instance = MagicMock()
                mock_async_zeroconf.return_value = mock_zc_instance
                mock_browser_instance = MagicMock()
                mock_browser.return_value = mock_browser_instance
                yield {
                    "zeroconf": mock_async_zeroconf,
                    "browser": mock_browser,
                    "zc_instance": mock_zc_instance,
                    "browser_instance": mock_browser_instance,
                }


class TestAirPlayReceiver:
    """Test AirPlayReceiver class."""

    def test_airplay_receiver_creation(self):
        """Test creating an AirPlayReceiver."""
        properties = {
            "features": "0x5A7FFFF7",
            "model": "AudioAccessory5,1"
        }
        receiver = AirPlayReceiver(
            name="Test AirPlay Device",
            address="192.168.1.100",
            port=7000,
            properties=properties
        )
        
        assert receiver.name == "Test AirPlay Device"
        assert receiver.address == "192.168.1.100"
        assert receiver.port == 7000
        assert receiver.device_model == "AudioAccessory5,1"
        assert receiver.is_airplay2 is True
        assert receiver.supports_audio is True

    def test_airplay_receiver_properties(self):
        """Test AirPlayReceiver properties."""
        properties = {
            "features": "0x1",
            "model": "AudioAccessory5,1"
        }
        receiver = AirPlayReceiver(
            name="Test Device",
            address="192.168.1.100",
            port=7000,
            properties=properties
        )
        
        # Test to_dict method
        device_dict = receiver.to_dict()
        assert device_dict["name"] == "Test Device"
        assert device_dict["address"] == "192.168.1.100"
        assert device_dict["port"] == 7000
        assert device_dict["device_model"] == "AudioAccessory5,1"

    def test_airplay_receiver_airplay2_detection(self):
        """Test AirPlay 2 detection logic."""
        # Test with AirPlay 2 features
        airplay2_properties = {"features": "0x5A7FFFF7"}
        receiver = AirPlayReceiver("test", "192.168.1.1", 7000, airplay2_properties)
        assert receiver.is_airplay2 is True

        # Test without AirPlay 2 features
        airplay1_properties = {"features": "0x1"}
        receiver = AirPlayReceiver("test", "192.168.1.1", 7000, airplay1_properties)
        assert receiver.is_airplay2 is False

    def test_airplay_receiver_string_representation(self):
        """Test string representation of AirPlayReceiver."""
        properties = {"model": "Test Model"}
        receiver = AirPlayReceiver("Test Device", "192.168.1.100", 7000, properties)
        
        str_repr = str(receiver)
        assert "Test Device" in str_repr
        assert "192.168.1.100:7000" in str_repr
        assert "Test Model" in str_repr


class TestAirPlayServiceListener:
    """Test AirPlayServiceListener class."""

    def test_service_listener_creation(self, mock_hass):
        """Test creating a service listener."""
        manager = AirPlayDiscoveryManager(mock_hass)
        listener = AirPlayServiceListener(manager)
        assert listener._discovery_manager == manager

    def test_service_listener_methods(self, mock_hass):
        """Test service listener methods don't raise exceptions."""
        manager = AirPlayDiscoveryManager(mock_hass)
        listener = AirPlayServiceListener(manager)
        
        # These methods should not raise exceptions
        listener.add_service(None, "_raop._tcp.local.", "Test._raop._tcp.local.")
        listener.remove_service(None, "_raop._tcp.local.", "Test._raop._tcp.local.")
        listener.update_service(None, "_raop._tcp.local.", "Test._raop._tcp.local.")


class TestAirPlayDiscoveryManager:
    """Test AirPlayDiscoveryManager class."""

    def test_discovery_manager_creation(self, mock_hass):
        """Test creating a discovery manager."""
        manager = AirPlayDiscoveryManager(mock_hass)
        assert manager.receivers == {}
        assert manager.is_discovering is False

    def test_discovery_manager_properties(self, mock_hass):
        """Test discovery manager properties."""
        manager = AirPlayDiscoveryManager(mock_hass)
        
        # Test empty lists initially
        assert manager.airplay2_receivers == []
        assert manager.audio_receivers == []

    def test_add_remove_callbacks(self, mock_hass):
        """Test adding and removing callbacks."""
        manager = AirPlayDiscoveryManager(mock_hass)
        discovery_callback = MagicMock()
        receiver_callback = MagicMock()
        
        # Add callbacks
        manager.add_discovery_callback(discovery_callback)
        manager.add_receiver_callback(receiver_callback)
        
        # Remove callbacks
        manager.remove_discovery_callback(discovery_callback)
        manager.remove_receiver_callback(receiver_callback)

    @pytest.mark.asyncio
    async def test_start_discovery_without_zeroconf(self, mock_hass):
        """Test starting discovery without zeroconf available."""
        with patch("custom_components.bluetooth_to_airplay_bridge.airplay_discovery.ZEROCONF_AVAILABLE", False):
            manager = AirPlayDiscoveryManager(mock_hass)
            
            result = await manager.start_discovery()
            assert result is False
            assert manager.is_discovering is False

    @pytest.mark.asyncio
    async def test_start_discovery_with_zeroconf(self, mock_hass, mock_zeroconf):
        """Test starting discovery with zeroconf available."""
        manager = AirPlayDiscoveryManager(mock_hass)
        
        result = await manager.start_discovery()
        assert result is True
        assert manager.is_discovering is True

    @pytest.mark.asyncio
    async def test_stop_discovery(self, mock_hass, mock_zeroconf):
        """Test stopping discovery."""
        manager = AirPlayDiscoveryManager(mock_hass)
        
        # Start discovery first
        await manager.start_discovery()
        
        # Mock async_close method
        manager._zeroconf = MagicMock()
        manager._zeroconf.async_close = AsyncMock()
        
        await manager.stop_discovery()
        assert manager.is_discovering is False

    @pytest.mark.asyncio
    async def test_refresh_discovery(self, mock_hass, mock_zeroconf):
        """Test refreshing discovery."""
        manager = AirPlayDiscoveryManager(mock_hass)
        
        # Mock the stop and start methods
        manager.stop_discovery = AsyncMock()
        manager.start_discovery = AsyncMock(return_value=True)
        
        await manager.refresh_discovery()
        
        manager.stop_discovery.assert_called_once()
        manager.start_discovery.assert_called_once()

    def test_cleanup_stale_receivers(self, mock_hass):
        """Test cleaning up stale receivers."""
        manager = AirPlayDiscoveryManager(mock_hass)
        
        # This should not raise an exception
        manager.cleanup_stale_receivers(max_age_minutes=30)

    @pytest.mark.asyncio
    async def test_get_receiver_details(self, mock_hass):
        """Test getting receiver details."""
        manager = AirPlayDiscoveryManager(mock_hass)
        
        # This should return None for non-existent receivers
        result = await manager.get_receiver_details("192.168.1.100", 7000)
        assert result is None

    def test_receiver_filtering(self, mock_hass):
        """Test receiver filtering by type."""
        manager = AirPlayDiscoveryManager(mock_hass)
        
        # Add mock receivers directly to test filtering
        airplay2_receiver = AirPlayReceiver(
            "AirPlay2 Device", "192.168.1.100", 7000, {"features": "0x5A7FFFF7"}
        )
        airplay1_receiver = AirPlayReceiver(
            "AirPlay1 Device", "192.168.1.101", 7000, {"features": "0x1"}
        )
        
        # Manually add to receivers dict for testing
        manager._receivers = {
            "airplay2": airplay2_receiver,
            "airplay1": airplay1_receiver
        }
        
        # Test AirPlay 2 filtering
        airplay2_devices = manager.airplay2_receivers
        assert len(airplay2_devices) == 1
        assert airplay2_devices[0].name == "AirPlay2 Device"
        
        # Test audio filtering (both should support audio)
        audio_devices = manager.audio_receivers
        assert len(audio_devices) == 2