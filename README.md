# Bluetooth to AirPlay Bridge

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

**Latest Release: v0.8** - Enhanced Device Management & Stability

A Home Assistant integration that bridges Bluetooth audio devices to AirPlay, allowing you to stream audio from Bluetooth speakers through AirPlay protocol.

## What's New in v0.8

🔌 **Enhanced Device Management**
- ✅ Automatic Bluetooth disconnection when speaker is removed from Home Assistant
- ✅ `disconnect_bluetooth` service for manual Bluetooth device disconnection
- ✅ Proper cleanup when integration is unloaded or entities are removed
- ✅ Enhanced device lifecycle management with automatic resource cleanup

## Features

- **3-Step Configuration Wizard**: Easy setup with guided discovery, pairing, and configuration
- **Automatic Reconnection**: Automatically reconnects when Bluetooth devices are powered back on
- **AirPlay 1 & 2 Support**: Choose between AirPlay versions based on your needs
- **Native Bluetooth Integration**: Uses Home Assistant's built-in Bluetooth functionality
- **HACS Compatible**: Easy installation through Home Assistant Community Store

## Installation

### HACS (Recommended) ✅ **Now Working!**

#### Method 1: Add as Custom Repository (Ready for Use)

1. **Open HACS** in your Home Assistant instance
2. **Go to "Integrations"** tab
3. **Click the 3-dot menu** (⋮) in the top right corner
4. **Select "Custom repositories"**
5. **Add Repository**:
   - **Repository URL**: `https://github.com/jhaleit/bluetooth-to-airplay-bridge`
   - **Category**: `Integration`
6. **Click "Add"**
7. **Search** for "Bluetooth to AirPlay Bridge" in HACS
8. **Install** the integration (v0.8 or later)
9. **Restart** Home Assistant
10. **Add Integration** via Settings → Devices & Services → Add Integration

> **Note**: After installing v0.8, the integration will properly load and appear in your Home Assistant integration list. This version includes enhanced device management and stability improvements.

#### Method 2: Default HACS Store (Coming Soon)

This integration will be submitted to the official HACS store for easier discovery. Once approved, you'll be able to find it directly in HACS without adding a custom repository.

**To submit to HACS default store:**
- Visit: https://github.com/hacs/default/issues/new/choose
- Choose "Integration" template
- Repository: `https://github.com/jhaleit/bluetooth-to-airplay-bridge`

### Manual Installation

1. Download the latest release from the [releases page][releases]
2. Extract the contents to your `custom_components` directory:
   ```
   custom_components/
   └── bluetooth_to_airplay_bridge/
       ├── __init__.py
       ├── config_flow.py
       ├── const.py
       ├── manifest.json
       ├── media_player.py
       ├── strings.json
       └── translations/
           └── en.json
   ```
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Bluetooth to AirPlay Bridge"
4. Follow the 3-step configuration wizard:

### Step 1: Discovery
- Put your Bluetooth speaker into discovery/pairing mode
- Click "Next" to proceed

### Step 2: Scan & Select
- The integration will scan for available Bluetooth devices
- Select your device from the list
- Click "Pair" to pair with the device

### Step 3: Configure
- Choose AirPlay version (1 or 2)
- Set the AirPlay server name (visible to other devices)
- Click "Finish" to complete setup

## Usage

Once configured, the integration will:

- Create a media player entity for controlling the bridge
- Automatically connect to the Bluetooth device when available
- Provide AirPlay streaming capabilities
- Reconnect automatically when the device is powered back on

### Services

The integration provides these services:

- `bluetooth_to_airplay_bridge.start_bridge`: Start the AirPlay bridge
- `bluetooth_to_airplay_bridge.stop_bridge`: Stop the AirPlay bridge  
- `bluetooth_to_airplay_bridge.reconnect`: Force reconnection to Bluetooth device

## Requirements

- Home Assistant 2023.1.0 or later
- Bluetooth adapter on the Home Assistant host
- `bluetoothctl` command available (usually part of BlueZ package)

## Troubleshooting

### Enable Debug Logging

Add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.bluetooth_to_airplay_bridge: debug
```

### Common Issues

1. **Integration not appearing in Home Assistant**:
   - **Solution**: Ensure you're using v0.8 or later
   - **Cause**: Previous versions had ConfigFlow domain property issues
   - **Verification**: Check that you can find "Bluetooth to AirPlay Bridge" in Settings → Devices & Services → Add Integration

2. **HACS not showing latest version**:
   - **Solution**: Wait 15-30 minutes for HACS to detect new releases, or force refresh HACS
   - **Note**: Use stable releases only

3. **Bluetooth not available**: Ensure your Home Assistant host has a working Bluetooth adapter

4. **Device not found**: Make sure the device is in pairing mode and within range

5. **Pairing failed**: Try resetting the Bluetooth device and clearing any existing pairings

6. **Connection drops**: Check Bluetooth signal strength and interference

### Debug Commands

```bash
# Check Bluetooth status
bluetoothctl show

# List paired devices
bluetoothctl devices

# Check device connection
bluetoothctl info [DEVICE_ADDRESS]
```

## HACS Integration

### Current Status: ✅ Fully Working as Custom Repository

This integration is **fully functional in HACS** with v0.8 and can be installed immediately using the custom repository method above. All previous integration discovery issues have been resolved.

### Submitting to Official HACS Store

To get this integration included in the default HACS store:

1. **Visit**: https://github.com/hacs/default/issues/new/choose
2. **Select**: "Integration" template
3. **Fill out**:
   - Repository: `https://github.com/jhaleit/bluetooth-to-airplay-bridge`
   - Description: Home Assistant integration that bridges Bluetooth speakers to AirPlay
4. **Submit** and wait for review
5. **Address** any feedback from HACS maintainers

### Benefits of Official HACS Store

- ✅ Automatic discovery by all HACS users
- ✅ No need to add custom repository
- ✅ Better visibility in the community
- ✅ Automatic update notifications

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork this repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

[releases-shield]: https://img.shields.io/github/release/jhaleit/bluetooth-to-airplay-bridge.svg?style=for-the-badge
[releases]: https://github.com/jhaleit/bluetooth-to-airplay-bridge/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/jhaleit/bluetooth-to-airplay-bridge.svg?style=for-the-badge
[commits]: https://github.com/jhaleit/bluetooth-to-airplay-bridge/commits/main
[license-shield]: https://img.shields.io/github/license/jhaleit/bluetooth-to-airplay-bridge.svg?style=for-the-badge
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge