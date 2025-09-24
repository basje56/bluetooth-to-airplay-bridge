"""Constants for the Bluetooth to AirPlay Bridge integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "bluetooth_to_airplay_bridge"

# Configuration keys
CONF_BLUETOOTH_ADDRESS: Final = "bluetooth_address"
CONF_BLUETOOTH_NAME: Final = "bluetooth_name"
CONF_AIRPLAY_VERSION: Final = "airplay_version"
CONF_AIRPLAY_NAME: Final = "airplay_name"

# AirPlay versions
AIRPLAY_VERSION_1: Final = "airplay1"
AIRPLAY_VERSION_2: Final = "airplay2"

AIRPLAY_VERSIONS: Final = [AIRPLAY_VERSION_1, AIRPLAY_VERSION_2]

# Default values
DEFAULT_AIRPLAY_NAME: Final = "HA AirPlay Bridge"
DEFAULT_SCAN_TIMEOUT: Final = 30
DEFAULT_PAIR_TIMEOUT: Final = 60

# Error codes
ERROR_BLUETOOTH_NOT_AVAILABLE: Final = "bluetooth_not_available"
ERROR_DEVICE_NOT_FOUND: Final = "device_not_found"
ERROR_PAIRING_FAILED: Final = "pairing_failed"
ERROR_CONNECTION_FAILED: Final = "connection_failed"
ERROR_AIRPLAY_SETUP_FAILED: Final = "airplay_setup_failed"

# Service names
SERVICE_START_BRIDGE: Final = "start_bridge"
SERVICE_STOP_BRIDGE: Final = "stop_bridge"
SERVICE_RECONNECT: Final = "reconnect"
SERVICE_DISCONNECT_BLUETOOTH: Final = "disconnect_bluetooth"
SERVICE_SCAN_DEVICES: Final = "scan_devices"
SERVICE_CONNECT_DEVICE: Final = "connect_device"
SERVICE_DISCONNECT_DEVICE: Final = "disconnect_device"
SERVICE_PAIR_DEVICE: Final = "pair_device"
SERVICE_UNPAIR_DEVICE: Final = "unpair_device"
SERVICE_SWITCH_DEVICE: Final = "switch_device"
SERVICE_REFRESH_DEVICES: Final = "refresh_devices"

# AirPlay discovery services
SERVICE_START_AIRPLAY_DISCOVERY: Final = "start_airplay_discovery"
SERVICE_STOP_AIRPLAY_DISCOVERY: Final = "stop_airplay_discovery"
SERVICE_REFRESH_AIRPLAY_DISCOVERY: Final = "refresh_airplay_discovery"
SERVICE_GET_AIRPLAY_RECEIVERS: Final = "get_airplay_receivers"

# Attributes
ATTR_BLUETOOTH_ADDRESS: Final = "bluetooth_address"
ATTR_BLUETOOTH_NAME: Final = "bluetooth_name"
ATTR_AIRPLAY_VERSION: Final = "airplay_version"
ATTR_AIRPLAY_NAME: Final = "airplay_name"
ATTR_CONNECTION_STATE: Final = "connection_state"
ATTR_LAST_SEEN: Final = "last_seen"

# States
STATE_CONNECTED: Final = "connected"
STATE_DISCONNECTED: Final = "disconnected"
STATE_CONNECTING: Final = "connecting"
STATE_PAIRING: Final = "pairing"
STATE_ERROR: Final = "error"