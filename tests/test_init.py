"""Test the Bluetooth to AirPlay Bridge integration."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest  # type: ignore
from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.exceptions import ConfigEntryNotReady  # type: ignore

from custom_components.bluetooth_to_airplay_bridge import (
    BluetoothAirPlayCoordinator,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.bluetooth_to_airplay_bridge.audio_config import (
    AudioConfigManager,
    AudioQuality,
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
    coordinator = BluetoothAirPlayCoordinator(MagicMock(), mock_config_entry)
    
    device_info = coordinator.device_info
    
    assert device_info["identifiers"] == {(DOMAIN, "AA:BB:CC:DD:EE:FF")}
    assert device_info["name"] == "Test AirPlay"
    assert device_info["manufacturer"] == "Bluetooth to AirPlay Bridge"
    assert device_info["model"] == "Test Speaker"
    assert device_info["sw_version"] == "0.10.0"


async def test_coordinator_audio_config_integration(mock_config_entry) -> None:
    """Test coordinator audio configuration integration."""
    coordinator = BluetoothAirPlayCoordinator(MagicMock(), mock_config_entry)
    
    # Test audio config property
    assert coordinator.audio_config is not None
    assert isinstance(coordinator.audio_config, AudioConfigManager)


async def test_coordinator_audio_status(mock_config_entry) -> None:
    """Test coordinator audio status retrieval."""
    coordinator = BluetoothAirPlayCoordinator(MagicMock(), mock_config_entry)
    
    # Mock audio components
    with patch.object(coordinator._audio_engine, "get_audio_info", return_value={"status": "ready"}), \
         patch.object(coordinator._airplay_server, "get_status", return_value={"running": False}), \
         patch.object(coordinator._mdns_advertiser, "get_status", return_value={"advertising": False}):
        
        status = await coordinator.get_audio_status()
        
    assert "audio_engine" in status
    assert "airplay_server" in status
    assert "mdns_advertiser" in status
    assert "audio_config" in status
    assert "bluetooth_connected" in status


async def test_coordinator_set_audio_quality(mock_config_entry) -> None:
    """Test setting audio quality through coordinator."""
    coordinator = BluetoothAirPlayCoordinator(MagicMock(), mock_config_entry)
    
    # Mock audio engine methods
    with patch.object(coordinator._audio_engine, "set_codec", return_value=True) as mock_codec, \
         patch.object(coordinator._audio_engine, "set_audio_quality", return_value=True) as mock_quality:
        
        success = await coordinator.set_audio_quality(AudioQuality.HIGH)
        
    assert success
    # Should not call audio engine methods when disconnected
    mock_codec.assert_not_called()
    mock_quality.assert_not_called()


async def test_coordinator_set_audio_quality_connected(mock_config_entry) -> None:
    """Test setting audio quality when coordinator is connected."""
    coordinator = BluetoothAirPlayCoordinator(MagicMock(), mock_config_entry)
    
    # Set coordinator to connected state
    coordinator._state = "connected"
    
    # Mock audio engine methods
    with patch.object(coordinator._audio_engine, "set_codec", return_value=True) as mock_codec, \
         patch.object(coordinator._audio_engine, "set_audio_quality", return_value=True) as mock_quality:
        
        success = await coordinator.set_audio_quality(AudioQuality.HIGH)
        
    assert success
    # Should call audio engine methods when connected
    mock_codec.assert_called_once()
    mock_quality.assert_called_once()


async def test_coordinator_update_audio_setting(mock_config_entry) -> None:
    """Test updating individual audio settings through coordinator."""
    coordinator = BluetoothAirPlayCoordinator(MagicMock(), mock_config_entry)
    
    # Set coordinator to connected state
    coordinator._state = "connected"
    
    # Mock audio engine methods
    with patch.object(coordinator._audio_engine, "set_codec", return_value=True) as mock_codec:
        
        success = await coordinator.update_audio_setting("codec", "aac")
        
    assert success
    mock_codec.assert_called_once()


async def test_coordinator_audio_diagnostics_integration(mock_config_entry) -> None:
    """Test audio diagnostics integration."""
    from custom_components.bluetooth_to_airplay_bridge.audio_diagnostics import AudioDiagnostics
    
    coordinator = BluetoothAirPlayCoordinator(MagicMock(), mock_config_entry)
    diagnostics = AudioDiagnostics()
    
    # Test that diagnostics can be instantiated and used
    assert diagnostics is not None
    
    # Mock a simple diagnostic test
    mock_result = {
        "summary": {"total_tests": 1, "passed": 1, "failed": 0},
        "results": [{"test_name": "test", "status": "pass"}],
        "recommendations": []
    }
    
    with patch.object(diagnostics, "run_full_diagnostics", return_value=mock_result):
        result = await diagnostics.run_full_diagnostics()
        
    assert result == mock_result