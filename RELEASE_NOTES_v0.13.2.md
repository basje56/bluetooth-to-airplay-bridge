# Release Notes - v0.13.2

## Critical Error Fixes

This patch release addresses several critical runtime errors that were preventing the integration from functioning properly in Home Assistant.

### 🐛 Bug Fixes

#### Config Flow Fixes
- **Fixed BluetoothServiceInfoBleak attribute error**: Updated `async_step_bluetooth` method to properly handle both dictionary and `BluetoothServiceInfoBleak` object types when extracting device information
- **Fixed missing `async_discovered_devices` attribute**: Updated Bluetooth device scanning to use the correct Home Assistant Bluetooth API (`async_get_scanner`) instead of the deprecated `async_discovered_devices` method
- **Enhanced device filtering**: Improved audio device detection with better keyword filtering for speakers, headphones, and AirPods

#### Zeroconf Integration Fixes
- **Fixed shared Zeroconf instance usage**: Updated `mDNSAdvertiser` to use Home Assistant's shared Zeroconf instance via `async_get_instance()` instead of creating a new instance
- **Eliminated Zeroconf warnings**: Resolved the "attempted to create another Zeroconf instance" warning by properly integrating with HA's Zeroconf component
- **Updated constructor**: Modified `mDNSAdvertiser` to accept and use the HomeAssistant instance for proper integration

### 🔧 Technical Improvements

- **Better error handling**: Enhanced exception handling in Bluetooth device discovery with more descriptive error messages
- **Improved API compatibility**: Updated to use current Home Assistant Bluetooth component APIs for better stability
- **Enhanced logging**: Added more detailed debug logging for device discovery and Zeroconf operations

### 📋 Files Modified

- `config_flow.py`: Fixed Bluetooth discovery and device attribute handling
- `mdns_advertiser.py`: Updated to use shared Zeroconf instance
- `__init__.py`: Updated mDNSAdvertiser instantiation with hass parameter
- `manifest.json`: Version bump to 0.13.2

### 🚀 What's Fixed

These fixes resolve the following error messages:
- `'BluetoothServiceInfoBleak' object has no attribute 'get'`
- `module 'homeassistant.components.bluetooth' has no attribute 'async_discovered_devices'`
- `Detected that custom integration 'bluetooth_to_airplay_bridge' attempted to create another Zeroconf instance`
- Various pairing and discovery failures

### 📦 Installation

For HACS users, this update will be available automatically. For manual installations, replace the integration files and restart Home Assistant.

---

**Full Changelog**: https://github.com/jhaleit/bluetooth-to-airplay-bridge/compare/v0.13.1...v0.13.2