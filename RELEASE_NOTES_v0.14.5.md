# Release Notes - Version 0.14.5

## 🐛 Critical Bug Fixes for HAOS Audio Integration

This release addresses critical issues with the HAOS audio integration introduced in v0.14.4, specifically fixing `pactl` detection failures and PulseAudio source listing problems in Home Assistant Operating System environments.

### 🔧 Bug Fixes

#### Audio Engine Improvements
- **Fixed pactl detection failures in HAOS environments**
  - Improved environment detection logic to properly identify when running inside Home Assistant containers
  - Enhanced fallback mechanisms for different pactl execution methods
  - Added support for Home Assistant Supervisor API as an alternative to direct pactl access

- **Resolved PulseAudio source listing failures**
  - Fixed "Failed to list PulseAudio sources" errors
  - Improved handling of "list sources short" commands in supervisor and HA CLI methods
  - Added proper output formatting to match expected pactl format

- **Enhanced error handling and diagnostics**
  - Added comprehensive logging for pactl method detection process
  - Improved error messages with specific guidance for different failure scenarios
  - Added diagnostic information for audio source availability checks
  - Better process validation for audio capture startup

#### Specific Error Resolutions
- ✅ Fixed "No pactl method available" errors
- ✅ Fixed "Failed to list PulseAudio sources" errors  
- ✅ Fixed "Bluetooth audio not available" false negatives
- ✅ Fixed "Failed to start audio capture after retries" issues
- ✅ Fixed "Failed to get source information" errors

### 🔍 Technical Improvements

#### Environment Detection
- Reordered environment detection priority to better handle HAOS container scenarios
- Added checks for `SUPERVISOR_TOKEN` environment variable
- Improved detection of Home Assistant container vs. HAOS host environment

#### Audio Method Fallbacks
1. **Direct pactl** - Try native pactl command first
2. **Supervisor API** - Use HA Supervisor API for audio info (new)
3. **HA CLI** - Use `ha audio` commands with improved output parsing
4. **Container method** - Docker exec into hassio_audio container (fallback)

#### Enhanced Logging
- Added method-specific logging for all pactl operations
- Improved diagnostic messages for troubleshooting
- Better error context for configuration issues
- Added process validation for audio capture startup

### 🏠 HAOS Compatibility

This release specifically improves compatibility with:
- **Home Assistant Operating System (HAOS)** - Full support
- **Home Assistant Container** - Enhanced detection and fallbacks
- **Home Assistant Supervised** - Improved HA CLI integration
- **Home Assistant Core** - Maintained compatibility

### 📋 Installation & Upgrade

#### For HACS Users
1. Update through HACS interface
2. Restart Home Assistant
3. Check logs for improved diagnostic information

#### Manual Installation
1. Download the latest release
2. Replace files in `custom_components/bluetooth_to_airplay_bridge/`
3. Restart Home Assistant

### 🔧 Troubleshooting

If you continue to experience audio issues after upgrading:

1. **Check the logs** - Enhanced logging now provides specific guidance
2. **Verify Bluetooth connection** - Ensure device is connected and audio is active
3. **Check PulseAudio status** - Logs will indicate which method is being used
4. **Review environment detection** - Logs show detected HA environment type

### 🐛 Known Issues

- Some HAOS configurations may still require manual PulseAudio configuration
- Container environments may have limited audio access depending on setup
- Bluetooth device compatibility varies by hardware and drivers

### 🔮 Next Steps

- Monitor user feedback on HAOS audio integration stability
- Continue improving audio method detection and fallbacks
- Add support for additional audio backends if needed

---

**Full Changelog**: [v0.14.4...v0.14.5](https://github.com/joshuahale/bluetooth-to-airplay-bridge/compare/v0.14.4...v0.14.5)

For support, please check the [documentation](https://github.com/joshuahale/bluetooth-to-airplay-bridge/blob/main/README.md) or open an [issue](https://github.com/joshuahale/bluetooth-to-airplay-bridge/issues).