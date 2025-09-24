"""Test the Bluetooth to AirPlay Bridge integration."""
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.bluetooth_to_airplay_bridge import (
    BluetoothAirPlayCoordinator,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.bluetooth_to_airplay_bridge.const import (
    CONF_AIRPLAY_NAME,
    CONF_AIRPLAY_VERSION,
    CONF_BLUETOOTH_ADDRESS,
    CONF_BLUETOOTH_NAME,
    DOMAIN,
)


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    return ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Test AirPlay Bridge",
        data={
            CONF_BLUETOOTH_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_BLUETOOTH_NAME: "Test Speaker",
            CONF_AIRPLAY_NAME: "Test AirPlay",
            CONF_AIRPLAY_VERSION: "airplay2",
        },
        source="user",
        entry_id="test_entry_id",
        unique_id="AA:BB:CC:DD:EE:FF",
    )


@pytest.fixture
def mock_bluetooth_available():
    """Mock bluetooth being available."""
    with patch("homeassistant.components.bluetooth.async_scanner_count", return_value=1):
        yield


async def test_setup_entry_success(
    hass: HomeAssistant, mock_config_entry, mock_bluetooth_available
) -> None:
    """Test successful setup of config entry."""
    with patch(
        "custom_components.bluetooth_to_airplay_bridge.BluetoothAirPlayCoordinator.async_start"
    ) as mock_start:
        result = await async_setup_entry(hass, mock_config_entry)
        
        assert result is True
        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        assert isinstance(hass.data[DOMAIN][mock_config_entry.entry_id], BluetoothAirPlayCoordinator)
        mock_start.assert_called_once()


async def test_setup_entry_bluetooth_not_available(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Test setup when Bluetooth is not available."""
    with patch("homeassistant.components.bluetooth.async_scanner_count", return_value=0):
        with pytest.raises(Exception):  # ConfigEntryNotReady
            await async_setup_entry(hass, mock_config_entry)


async def test_unload_entry(
    hass: HomeAssistant, mock_config_entry, mock_bluetooth_available
) -> None:
    """Test unloading of config entry."""
    # First setup the entry
    with patch(
        "custom_components.bluetooth_to_airplay_bridge.BluetoothAirPlayCoordinator.async_start"
    ):
        await async_setup_entry(hass, mock_config_entry)
    
    # Then unload it
    with patch(
        "custom_components.bluetooth_to_airplay_bridge.BluetoothAirPlayCoordinator.async_stop"
    ) as mock_stop:
        with patch(
            "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
            return_value=True,
        ):
            result = await async_unload_entry(hass, mock_config_entry)
            
            assert result is True
            assert mock_config_entry.entry_id not in hass.data[DOMAIN]
            mock_stop.assert_called_once()


async def test_coordinator_properties(mock_config_entry) -> None:
    """Test coordinator properties."""
    hass = AsyncMock()
    coordinator = BluetoothAirPlayCoordinator(hass, mock_config_entry)
    
    assert coordinator.bluetooth_address == "AA:BB:CC:DD:EE:FF"
    assert coordinator.bluetooth_name == "Test Speaker"
    assert coordinator.airplay_name == "Test AirPlay"
    assert coordinator.airplay_version == "airplay2"
    assert coordinator.state == "disconnected"
    assert coordinator.last_seen is None


async def test_coordinator_device_info(mock_config_entry) -> None:
    """Test coordinator device info."""
    hass = AsyncMock()
    coordinator = BluetoothAirPlayCoordinator(hass, mock_config_entry)
    
    device_info = coordinator.device_info
    assert device_info["identifiers"] == {(DOMAIN, "AA:BB:CC:DD:EE:FF")}
    assert device_info["name"] == "AirPlay Bridge (Test Speaker)"
    assert device_info["manufacturer"] == "Bluetooth to AirPlay Bridge"
    assert device_info["model"] == "Bridge AIRPLAY2"
    assert device_info["sw_version"] == "1.0.0"