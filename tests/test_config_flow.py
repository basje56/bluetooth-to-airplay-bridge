"""Test the Bluetooth to AirPlay Bridge config flow."""
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.bluetooth_to_airplay_bridge.const import (
    CONF_AIRPLAY_NAME,
    CONF_AIRPLAY_VERSION,
    CONF_BLUETOOTH_ADDRESS,
    CONF_BLUETOOTH_NAME,
    DEFAULT_AIRPLAY_NAME,
    DOMAIN,
)


@pytest.fixture
def mock_bluetooth_scanner():
    """Mock bluetooth scanner."""
    with patch(
        "homeassistant.components.bluetooth.async_scanner_count", return_value=1
    ):
        yield


@pytest.fixture
def mock_scan_devices():
    """Mock scanning for devices."""
    mock_devices = [
        {"address": "AA:BB:CC:DD:EE:FF", "name": "Test Speaker"},
        {"address": "11:22:33:44:55:66", "name": "Another Device"},
    ]
    
    with patch(
        "custom_components.bluetooth_to_airplay_bridge.config_flow.ConfigFlow._async_scan_devices",
        return_value=mock_devices,
    ):
        yield mock_devices


@pytest.fixture
def mock_pair_device():
    """Mock pairing with device."""
    with patch(
        "custom_components.bluetooth_to_airplay_bridge.config_flow.ConfigFlow._async_pair_device",
        return_value=True,
    ):
        yield


async def test_form_user_step(hass: HomeAssistant, mock_bluetooth_scanner) -> None:
    """Test the user step shows the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_form_scan_step(
    hass: HomeAssistant, mock_bluetooth_scanner, mock_scan_devices
) -> None:
    """Test the scan step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Submit user step
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "scan"
    assert "selected_device" in result["data_schema"].schema


async def test_form_pair_step(
    hass: HomeAssistant, mock_bluetooth_scanner, mock_scan_devices, mock_pair_device
) -> None:
    """Test the pair step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Submit user step
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    
    # Submit scan step with device selection
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"selected_device": "AA:BB:CC:DD:EE:FF"}
    )
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "pair"


async def test_form_configure_step(
    hass: HomeAssistant, mock_bluetooth_scanner, mock_scan_devices, mock_pair_device
) -> None:
    """Test the configure step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Submit user step
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    
    # Submit scan step with device selection
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"selected_device": "AA:BB:CC:DD:EE:FF"}
    )
    
    # Submit pair step
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"pair_device": True}
    )
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "configure"


async def test_complete_flow(
    hass: HomeAssistant, mock_bluetooth_scanner, mock_scan_devices, mock_pair_device
) -> None:
    """Test the complete configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Submit user step
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    
    # Submit scan step with device selection
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"selected_device": "AA:BB:CC:DD:EE:FF"}
    )
    
    # Submit pair step
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"pair_device": True}
    )
    
    # Submit configure step
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_AIRPLAY_VERSION: "airplay2",
            CONF_AIRPLAY_NAME: "My AirPlay Bridge",
        },
    )
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "AirPlay Bridge (Test Speaker)"
    assert result["data"] == {
        CONF_BLUETOOTH_ADDRESS: "AA:BB:CC:DD:EE:FF",
        CONF_BLUETOOTH_NAME: "Test Speaker",
        CONF_AIRPLAY_VERSION: "airplay2",
        CONF_AIRPLAY_NAME: "My AirPlay Bridge",
    }


async def test_bluetooth_not_available(hass: HomeAssistant) -> None:
    """Test when Bluetooth is not available."""
    with patch("homeassistant.components.bluetooth.async_scanner_count", return_value=0):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        
        # Submit user step
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "scan"
        assert result["errors"]["base"] == "bluetooth_not_available"


async def test_no_devices_found(hass: HomeAssistant, mock_bluetooth_scanner) -> None:
    """Test when no devices are found."""
    with patch(
        "custom_components.bluetooth_to_airplay_bridge.config_flow.ConfigFlow._async_scan_devices",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        
        # Submit user step
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "scan"
        assert result["errors"]["base"] == "no_devices_found"


async def test_pairing_failed(
    hass: HomeAssistant, mock_bluetooth_scanner, mock_scan_devices
) -> None:
    """Test when pairing fails."""
    with patch(
        "custom_components.bluetooth_to_airplay_bridge.config_flow.ConfigFlow._async_pair_device",
        return_value=False,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        
        # Submit user step
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        
        # Submit scan step with device selection
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"selected_device": "AA:BB:CC:DD:EE:FF"}
        )
        
        # Submit pair step
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"pair_device": True}
        )
        
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "pair"
        assert result["errors"]["base"] == "pairing_failed"