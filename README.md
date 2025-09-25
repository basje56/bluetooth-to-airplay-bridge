# Bluetooth to AirPlay Bridge

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

**Latest Release: v0.14.1** - Home Assistant 2025.x Compatibility & Enhanced Stability

A Home Assistant integration that bridges Bluetooth audio devices to AirPlay, allowing you to stream audio from Bluetooth speakers through AirPlay protocol with advanced audio configuration and quality control.

## What's New in v0.14.1

🔧 **Home Assistant 2025.x Compatibility Fixes**
- ✅ Fixed `AttributeError: '_process'` errors in media player and metadata manager
- ✅ Updated Bluetooth component integration for new HA API (list-based device discovery)
- ✅ Enhanced `pactl` dependency handling with graceful fallback for HAOS environments
- ✅ Improved error handling and logging throughout the integration
- ✅ Full compatibility with Home Assistant Operating System (HAOS)

🚀 **Enhanced Stability & Error Handling**
- ✅ Robust fallback mechanisms when system audio tools are unavailable
- ✅ Improved Bluetooth device scanning and discovery reliability
- ✅ Better integration lifecycle management and cleanup
- ✅ Enhanced diagnostics and troubleshooting capabilities
- ✅ Production-ready error recovery and graceful degradation

## Previous Releases

### v0.14.0 - Major Architecture Improvements & Enhanced Features

🚀 **Advanced Metadata Management**
- ✅ Complete metadata synchronization between Bluetooth and AirPlay
- ✅ Real-time track information display (title, artist, album, artwork)
- ✅ Enhanced media player controls with proper state management
- ✅ Improved audio pipeline with better error recovery

🔧 **Enhanced Device Management**
- ✅ Improved Bluetooth device lifecycle management
- ✅ Better connection state tracking and recovery
- ✅ Enhanced device discovery and pairing reliability
- ✅ Optimized resource usage and cleanup

### v0.13.x - Stability & Performance Improvements

🔧 **Enhanced Stability**
- ✅ Improved error handling and recovery mechanisms
- ✅ Better resource management and cleanup
- ✅ Enhanced logging and diagnostics
- ✅ Optimized performance for long-running operations

### v0.12 - Dependency Optimization & Enhanced Performance

🚀 **Dependency Optimization & Performance Enhancement**
- ✅ Removed unused `pycairo` dependency, reducing installation complexity
- ✅ Streamlined dependency list for faster installation and reduced resource usage
- ✅ Updated HACS compatibility requirements for latest Home Assistant versions
- ✅ Enhanced performance through dependency optimization
- ✅ Updated minimum Home Assistant version requirement to 2024.1.0 for better compatibility

## Previous Releases

### v0.10 - Complete AirPlay Discovery & Production Ready

🚀 **Production Ready Release**
- ✅ Complete AirPlay Discovery implementation with full network integration
- ✅ Comprehensive test coverage for all major components (AirPlay discovery, device management, audio streaming)
- ✅ Enhanced documentation with detailed setup guides and troubleshooting
- ✅ Full HACS compatibility with automated validation and CI/CD pipeline
- ✅ Production-grade error handling and logging throughout the codebase

🔍 **Advanced AirPlay Discovery**
- ✅ Real-time AirPlay receiver discovery and monitoring using Zeroconf/mDNS
- ✅ Support for AirPlay 1 and AirPlay 2 device detection with capability analysis
- ✅ Network service management with start/stop/refresh discovery controls
- ✅ Comprehensive device information including model, features, and audio capabilities
- ✅ Integration with Home Assistant services for programmatic control

🧪 **Comprehensive Testing & Validation**
- ✅ Full test suite covering AirPlay discovery, device management, and audio streaming
- ✅ Automated syntax validation and linting
- ✅ GitHub Actions CI/CD pipeline for continuous validation
- ✅ Production-ready code quality with proper error handling and logging

📚 **Enhanced Documentation & User Experience**
- ✅ Updated README with complete feature documentation and usage examples
- ✅ Detailed troubleshooting guides and debug logging configurations
- ✅ HACS installation instructions and GitHub submission preparation
- ✅ Clear setup guides for both manual and HACS installation methods

## Previous Releases

### v0.9 - Advanced Audio Streaming & Quality Control

🎵 **Advanced Audio Streaming**
- ✅ Comprehensive audio configuration with quality presets (Low, Medium, High, Lossless)
- ✅ Multi-codec support (SBC, AAC, aptX, LDAC) with automatic device capability detection
- ✅ Configurable sample rates (44.1kHz, 48kHz, 96kHz, 192kHz) and bit depths (16/24/32-bit)
- ✅ Dynamic audio quality adjustment during playback
- ✅ GStreamer integration for professional audio processing

🔧 **Enhanced Error Handling & Diagnostics**
- ✅ Exponential backoff retry mechanisms for robust connection handling
- ✅ Comprehensive audio diagnostics and troubleshooting tools
- ✅ Structured error reporting with detailed context and recovery suggestions
- ✅ Real-time audio pipeline monitoring and health checks

🔌 **Enhanced Device Management**
- ✅ Automatic Bluetooth disconnection when speaker is removed from Home Assistant
- ✅ `disconnect_bluetooth` service for manual Bluetooth device disconnection
- ✅ Proper cleanup when integration is unloaded or entities are removed
- ✅ Enhanced device lifecycle management with automatic resource cleanup

📡 **AirPlay Discovery & Network Integration**
- ✅ Automatic discovery of AirPlay receivers on the local network
- ✅ Real-time monitoring of AirPlay device availability and capabilities
- ✅ Support for both AirPlay 1 and AirPlay 2 device detection
- ✅ Network service management with start/stop/refresh discovery controls
- ✅ Comprehensive device information including model, features, and audio capabilities

## Features

- **3-Step Configuration Wizard**: Easy setup with guided discovery, pairing, and configuration
- **Advanced Audio Configuration**: Quality presets, codec selection, and custom audio settings
- **Multi-Codec Support**: SBC, AAC, aptX, and LDAC with automatic device capability detection
- **Audio Diagnostics**: Comprehensive troubleshooting tools and system health checks
- **Automatic Reconnection**: Automatically reconnects when Bluetooth devices are powered back on
- **AirPlay 1 & 2 Support**: Choose between AirPlay versions based on your needs
- **AirPlay Network Discovery**: Automatic discovery and monitoring of AirPlay receivers on your network
- **Native Bluetooth Integration**: Uses Home Assistant's built-in Bluetooth functionality
- **HACS Compatible**: Easy installation through Home Assistant Community Store

## Installation

### HACS (Recommended) ✅ **Fully Compatible!**

#### Method 1: Add as Custom Repository (Current Method)

1. **Open HACS** in your Home Assistant instance
2. **Go to "Integrations"** tab
3. **Click the 3-dot menu** (⋮) in the top right corner
4. **Select "Custom repositories"**
5. **Add Repository**:
   - **Repository URL**: `https://github.com/jhaleit/bluetooth-to-airplay-bridge`
   - **Category**: `Integration`
6. **Click "Add"**
7. **Search** for "Bluetooth to AirPlay Bridge" in HACS
8. **Install** the integration (v0.14.1 or later recommended)
9. **Restart** Home Assistant
10. **Add Integration** via Settings → Devices & Services → Add Integration

> **Note**: Version 0.14.1 includes important compatibility fixes for Home Assistant 2025.x and enhanced stability improvements. Always use the latest version for the best experience.

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
- Provide AirPlay streaming capabilities with configurable audio quality
- Reconnect automatically when the device is powered back on
- Monitor audio pipeline health and provide diagnostics

### Audio Configuration

The integration provides comprehensive audio configuration options:

#### Quality Presets
- **Low**: SBC codec, 128 kbps, optimized for compatibility
- **Medium**: SBC codec, 256 kbps, balanced quality and compatibility
- **High**: AAC codec, 320 kbps, high-quality audio
- **Lossless**: LDAC codec, 990 kbps, maximum quality (device dependent)

#### Custom Settings
- **Codec Selection**: SBC, AAC, aptX, LDAC (based on device capabilities)
- **Sample Rates**: 44.1kHz, 48kHz, 96kHz, 192kHz
- **Bit Depths**: 16-bit, 24-bit, 32-bit
- **Bitrate**: Custom bitrate configuration
- **Channels**: Mono or stereo output

### AirPlay Discovery

The integration includes comprehensive AirPlay network discovery capabilities:

#### Automatic Discovery
- **Real-time Detection**: Continuously monitors your network for AirPlay receivers
- **Device Information**: Automatically detects device names, models, and capabilities
- **AirPlay Version Support**: Identifies both AirPlay 1 and AirPlay 2 devices
- **Audio Capabilities**: Detects supported audio formats and features

#### Device Monitoring
- **Availability Tracking**: Real-time monitoring of device online/offline status
- **Service Information**: Detailed service information including ports and protocols
- **Network Changes**: Automatic detection when devices join or leave the network
- **Connection Status**: Monitor which devices are currently available for streaming

#### Discovery Management
- **Manual Control**: Start and stop discovery as needed to conserve resources
- **Refresh Capability**: Force refresh of device list to detect new devices
- **Filtered Results**: Option to filter by device type (AirPlay 1 vs AirPlay 2)
- **Callback Integration**: Real-time notifications when devices are discovered or lost

### Audio Diagnostics

The integration includes comprehensive diagnostic tools:

- **System Requirements Check**: Python version, dependencies
- **Bluetooth Stack Validation**: bluetoothctl availability and version
- **Audio Stack Verification**: GStreamer installation and capabilities
- **Device Compatibility**: Supported codecs and audio formats
- **Connection Testing**: Bluetooth pairing and audio pipeline validation
- **Performance Monitoring**: Latency measurement and resource usage

### Services

The integration provides these services:

#### Bridge Control
- `bluetooth_to_airplay_bridge.start_bridge`: Start the AirPlay bridge
- `bluetooth_to_airplay_bridge.stop_bridge`: Stop the AirPlay bridge  
- `bluetooth_to_airplay_bridge.reconnect`: Force reconnection to Bluetooth device
- `bluetooth_to_airplay_bridge.set_audio_quality`: Change audio quality preset
- `bluetooth_to_airplay_bridge.run_diagnostics`: Run comprehensive audio diagnostics

#### AirPlay Discovery
- `bluetooth_to_airplay_bridge.start_airplay_discovery`: Start AirPlay device discovery
- `bluetooth_to_airplay_bridge.stop_airplay_discovery`: Stop AirPlay device discovery
- `bluetooth_to_airplay_bridge.refresh_airplay_discovery`: Refresh the list of discovered AirPlay devices
- `bluetooth_to_airplay_bridge.get_airplay_receivers`: Get list of discovered AirPlay receivers with optional filtering

#### Service Examples

**Start AirPlay Discovery:**
```yaml
service: bluetooth_to_airplay_bridge.start_airplay_discovery
target:
  entity_id: media_player.your_bridge_name
```

**Get AirPlay Receivers (filtered):**
```yaml
service: bluetooth_to_airplay_bridge.get_airplay_receivers
target:
  entity_id: media_player.your_bridge_name
data:
  receiver_type: "airplay2"  # Optional: "airplay1", "airplay2", or "all"
```

## Requirements

- Home Assistant 2024.1.0 or later (v0.14.1+ fully compatible with HA 2025.x)
- Bluetooth adapter on the Home Assistant host
- `bluetoothctl` command available (usually part of BlueZ package)
- Audio system support (PulseAudio preferred, ALSA with graceful fallback)

### HAOS Audio Integration

For **Home Assistant Operating System (HAOS)** users, the integration automatically detects and uses the `hassio_audio` container for PulseAudio operations. No additional configuration is required.

**Supported HAOS Audio Methods:**
- 🐳 **Container Access**: `docker exec -i hassio_audio pactl <command>`
- 🏠 **Home Assistant CLI**: `ha audio <command>` for volume control and device management
- 🔄 **Automatic Fallback**: Graceful degradation if audio tools are unavailable

For detailed information about HAOS audio integration, see [HAOS_AUDIO_INTEGRATION.md](HAOS_AUDIO_INTEGRATION.md).

### Dependencies (Automatically Installed)

The integration automatically installs these Python dependencies:
- `aiohttp>=3.8.0` - Asynchronous HTTP client for streaming
- `aiofiles>=23.0.0` - Asynchronous file operations
- `zeroconf>=0.47.0` - AirPlay device discovery via mDNS

### System Compatibility

- ✅ **Home Assistant Operating System (HAOS)**: Fully supported with graceful fallbacks
- ✅ **Home Assistant Container**: Supported with host audio system access
- ✅ **Home Assistant Supervised**: Supported with proper audio configuration
- ✅ **Home Assistant Core**: Supported with manual dependency management

**Note**: Version 0.14.1 includes enhanced compatibility with HAOS environments, including graceful handling of missing system audio tools like `pactl`.

## Troubleshooting

### Audio Diagnostics

Run comprehensive diagnostics using the service:

```yaml
service: bluetooth_to_airplay_bridge.run_diagnostics
target:
  entity_id: media_player.your_bridge_name
```

This will check:
- System requirements and dependencies
- Bluetooth stack availability
- GStreamer installation and capabilities
- Device codec support
- Audio pipeline functionality

### Enable Debug Logging

Add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.bluetooth_to_airplay_bridge: debug
    custom_components.bluetooth_to_airplay_bridge.audio_config: debug
    custom_components.bluetooth_to_airplay_bridge.audio_diagnostics: debug
    custom_components.bluetooth_to_airplay_bridge.error_handler: debug
    custom_components.bluetooth_to_airplay_bridge.airplay_discovery: debug
    custom_components.bluetooth_to_airplay_bridge.device_manager: debug
```

### Common Issues

1. **Integration not appearing in Home Assistant**:
   - **Solution**: Ensure you're using v0.14.1 or later
   - **Cause**: Compatibility issues with newer Home Assistant versions
   - **Verification**: Check that you can find "Bluetooth to AirPlay Bridge" in Settings → Devices & Services → Add Integration

2. **HACS not showing latest version**:
   - **Solution**: Wait 15-30 minutes for HACS to detect new releases, or force refresh HACS
   - **Alternative**: Remove and re-add the custom repository
   - **Note**: Always use the latest stable release for best compatibility

3. **AttributeError: '_process' errors** (Fixed in v0.14.1):
   - **Solution**: Update to v0.14.1 or later
   - **Cause**: API changes in Home Assistant 2025.x
   - **Status**: Fully resolved with enhanced error handling

4. **Bluetooth device discovery issues** (Improved in v0.14.1):
   - **Solution**: Update to v0.14.1 for improved Bluetooth API compatibility
   - **Cause**: Changes in Home Assistant's Bluetooth component API
   - **Status**: Enhanced with better device scanning and discovery

5. **Audio system compatibility issues** (Enhanced in v0.14.1):
   - **Solution**: Update to v0.14.1 for improved HAOS compatibility
   - **Cause**: Missing `pactl` or audio system tools in some environments
   - **Status**: Graceful fallback mechanisms implemented
   - **HAOS Users**: See [HAOS_AUDIO_INTEGRATION.md](HAOS_AUDIO_INTEGRATION.md) for detailed troubleshooting

6. **Bluetooth not available**: Ensure your Home Assistant host has a working Bluetooth adapter

7. **Device not found**: Make sure the device is in pairing mode and within range

8. **Pairing failed**: Try resetting the Bluetooth device and clearing any existing pairings

9. **Connection drops**: Check Bluetooth signal strength and interference

10. **Audio quality issues**:
   - **Solution**: Use the audio diagnostics service to check codec support
   - **Try**: Different quality presets (Low/Medium/High/Lossless)
   - **Check**: Device codec capabilities and GStreamer installation

11. **No audio output**:
    - **Solution**: Verify GStreamer installation and audio pipeline
    - **Check**: Audio device permissions and ALSA/PulseAudio configuration
    - **Run**: Audio diagnostics to identify pipeline issues
    - **v0.14.1**: Enhanced fallback handling for missing audio tools

12. **High latency or audio dropouts**:
    - **Solution**: Lower audio quality preset or adjust buffer settings
    - **Check**: System resources and network performance
    - **Try**: Different codecs (SBC for compatibility, AAC for quality)

13. **Codec not supported**:
    - **Solution**: Check device capabilities using diagnostics
    - **Fallback**: Use SBC codec for maximum compatibility
    - **Upgrade**: Device firmware if available

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

### Current Status: ✅ Fully Compatible with Latest Home Assistant

This integration is **fully functional in HACS** with v0.14.1 and can be installed immediately using the custom repository method above. All compatibility issues with Home Assistant 2025.x have been resolved, including enhanced stability and error handling.

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