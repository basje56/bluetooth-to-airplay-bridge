# Release Notes - Version 0.14.1

## 🔧 Bug Fixes & Compatibility Updates

This release addresses several compatibility issues that emerged after the v0.14.0 update, ensuring smooth operation across different Home Assistant environments.

### Fixed Issues

#### 1. **AirPlay Server Process Attribute Error**
- **Issue**: `AttributeError: '_process' attribute access` in media_player.py
- **Fix**: Updated AirPlay server status check to use the new `_server` attribute instead of the removed `_process` attribute
- **Impact**: Resolves crashes when checking AirPlay server status

#### 2. **Bluetooth Component API Changes**
- **Issue**: `'list' object has no attribute 'items'` error in config_flow.py
- **Fix**: Updated Bluetooth device discovery to handle the new API where `discovered_devices` is a list of `BLEDevice` objects
- **Impact**: Fixes Bluetooth device scanning and pairing functionality

#### 3. **PulseAudio/pactl Dependency Issues**
- **Issue**: `[Errno 2] No such file or directory: 'pactl'` errors in audio_engine.py
- **Fix**: Added comprehensive fallback handling for environments where `pactl` is not available:
  - Added `_check_pactl_available()` helper method
  - Graceful degradation for audio availability checks
  - Default values for volume and latency when pactl is unavailable
  - Better error logging and user feedback
- **Impact**: Integration continues to function in Home Assistant OS environments without PulseAudio tools

### Technical Improvements

- **Enhanced Error Handling**: More robust error handling with informative logging
- **Environment Compatibility**: Better support for different Home Assistant deployment environments
- **Graceful Degradation**: Integration continues to function even when certain system tools are unavailable
- **API Future-Proofing**: Updated to work with latest Home Assistant component APIs

### Compatibility

- ✅ Home Assistant Core 2024.1+
- ✅ Home Assistant OS
- ✅ Home Assistant Container
- ✅ Home Assistant Supervised
- ✅ HACS Installation

### Installation

Update through HACS or manually replace the integration files. A Home Assistant restart is recommended after updating.

---

**Full Changelog**: [v0.14.0...v0.14.1](https://github.com/jhaleit/bluetooth-to-airplay-bridge/compare/v0.14.0...v0.14.1)