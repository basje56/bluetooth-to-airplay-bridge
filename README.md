# Bluetooth to AirPlay Bridge

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

A Home Assistant integration that bridges Bluetooth audio devices to AirPlay, allowing you to stream audio from Bluetooth speakers through AirPlay protocol.

## Features

- **3-Step Configuration Wizard**: Easy setup with guided discovery, pairing, and configuration
- **Automatic Reconnection**: Automatically reconnects when Bluetooth devices are powered back on
- **AirPlay 1 & 2 Support**: Choose between AirPlay versions based on your needs
- **Native Bluetooth Integration**: Uses Home Assistant's built-in Bluetooth functionality
- **HACS Compatible**: Easy installation through Home Assistant Community Store

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/your-username/bluetooth-to-airplay-bridge`
6. Select "Integration" as the category
7. Click "Add"
8. Find "Bluetooth to AirPlay Bridge" in the integration list and install it
9. Restart Home Assistant

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

1. **Bluetooth not available**: Ensure your Home Assistant host has a working Bluetooth adapter
2. **Device not found**: Make sure the device is in pairing mode and within range
3. **Pairing failed**: Try resetting the Bluetooth device and clearing any existing pairings
4. **Connection drops**: Check Bluetooth signal strength and interference

### Debug Commands

```bash
# Check Bluetooth status
bluetoothctl show

# List paired devices
bluetoothctl devices

# Check device connection
bluetoothctl info [DEVICE_ADDRESS]
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

[releases-shield]: https://img.shields.io/github/release/your-username/bluetooth-to-airplay-bridge.svg?style=for-the-badge
[releases]: https://github.com/your-username/bluetooth-to-airplay-bridge/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/your-username/bluetooth-to-airplay-bridge.svg?style=for-the-badge
[commits]: https://github.com/your-username/bluetooth-to-airplay-bridge/commits/main
[license-shield]: https://img.shields.io/github/license/your-username/bluetooth-to-airplay-bridge.svg?style=for-the-badge
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge