# Release Notes - Version 0.10.3

**Release Date:** September 25, 2025  
**Type:** Documentation & Troubleshooting Release  

## 🔍 Major Improvement: Config Flow Error Solution

This release provides a comprehensive solution to the persistent "Config flow could not be loaded: Invalid handler specified" error that users have been experiencing.

### 🎯 Root Cause Identified

Through extensive research and testing, we've identified that the "Invalid handler specified" error is a **generic error message** that masks the real underlying import errors. The actual issues are:

- Missing Python dependencies (`zeroconf`, `cryptography`, `pydbus`, `voluptuous`)
- Failed dependency installation during integration setup
- Network or permission issues preventing package installation

### 📋 What's New

#### ✅ Complete Error Analysis
- **CONFIG_FLOW_ERROR_SOLUTION.md**: Comprehensive troubleshooting guide
- Root cause analysis with research citations
- Step-by-step debugging instructions
- Debug logging configuration examples

#### ✅ Diagnostic Tools
- Import testing methodology
- Debug output schema and examples
- Common causes and solutions checklist

#### ✅ User-Friendly Solutions
- Clear instructions for enabling debug logging
- How to identify the real error behind "Invalid handler specified"
- Platform-specific troubleshooting steps

### 🔧 For Users Experiencing Config Flow Errors

**Immediate Action Required:**

1. **Enable Debug Logging** in your `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       homeassistant.config_entries: debug
       custom_components.bluetooth_to_airplay_bridge: debug
   ```

2. **Restart Home Assistant**

3. **Try adding the integration again**

4. **Check the logs** for the real error message:
   ```
   Error occurred loading flow for integration bluetooth_to_airplay_bridge: No module named '[missing_module]'
   ```

### 📚 Documentation Updates

- **CONFIG_FLOW_ERROR_SOLUTION.md**: Complete troubleshooting guide
- Debug logging examples and configuration
- JSON debug output schema
- Research-backed solutions with citations

### 🔍 Technical Details

**Research Sources:**
- [Home Assistant Core Issue #100622](https://github.com/home-assistant/core/issues/100622)
- [HACS AsusRouter Issue #883](https://github.com/Vaskivskyi/ha-asusrouter/issues/883)
- [Home Assistant Core Issue #127966](https://github.com/home-assistant/core/issues/127966)

**Dependencies Verified:**
- `zeroconf>=0.47.0` - mDNS/Zeroconf discovery
- `cryptography>=3.4.8` - Encryption and security
- `pydbus>=0.6.0` - D-Bus communication (Linux)

### 🚀 Installation

**HACS Users:**
1. Update the integration through HACS
2. Restart Home Assistant
3. Follow the debug logging instructions if issues persist

**Manual Installation:**
1. Download the latest release
2. Copy to `custom_components/bluetooth_to_airplay_bridge/`
3. Restart Home Assistant
4. Enable debug logging if needed

### 🐛 Known Issues

- `pydbus` dependency may not be available on all platforms (Windows/macOS)
- Network connectivity required for dependency installation
- Some environments may require manual dependency installation

### 📞 Support

If you continue experiencing issues after following the troubleshooting guide:

1. Enable debug logging as described
2. Collect the actual error message from logs
3. Report the specific dependency error (not "Invalid handler specified")
4. Include your platform information (OS, Home Assistant version)

### 🔄 Upgrade Path

**From 0.10.2:**
- No breaking changes
- Automatic dependency installation should resolve config flow issues
- Follow debug logging instructions if problems persist

**From Earlier Versions:**
- Follow the complete installation guide
- Enable debug logging to identify any remaining issues

---

**Full Changelog:**
- Added comprehensive config flow error analysis and solution
- Created detailed troubleshooting documentation
- Provided debug logging configuration examples
- Documented root cause of "Invalid handler specified" error
- Added research citations and technical background
- Version bump to 0.10.3

**Files Changed:**
- `CONFIG_FLOW_ERROR_SOLUTION.md` (new)
- `manifest.json` (version update)

**Impact:** This release significantly improves the user experience by providing clear solutions to the most common installation issue.