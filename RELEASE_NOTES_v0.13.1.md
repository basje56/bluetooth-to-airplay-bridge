# Release Notes - v0.13.1

## 🔧 Bug Fixes & Improvements

This patch release completes the GStreamer migration cleanup and improves the configuration flow integration with Home Assistant.

### Configuration Flow Enhancements
- **Fixed missing domain declaration** in ConfigFlow class for proper Home Assistant integration
- **Improved Bluetooth device discovery** with native Home Assistant Bluetooth component integration
- **Enhanced device filtering** for better audio device detection during setup
- **Better error handling** and logging for Bluetooth operations

### GStreamer Migration Cleanup
- **Removed obsolete GStreamer references** from all remaining files:
  - Removed `get_gstreamer_caps()` method from `audio_config.py`
  - Replaced GStreamer `gst-launch-1.0` commands in `audio_diagnostics.py` with PulseAudio equivalents
  - Updated error handling suggestions to remove GStreamer installation recommendations
- **Updated audio diagnostics** to use PulseAudio commands:
  - Latency testing now uses `pactl info` instead of GStreamer pipeline
  - Audio pipeline testing uses `pactl list sinks short`

### Technical Improvements
- **Enhanced Bluetooth scanning** with fallback mechanism (HA Bluetooth → bluetoothctl)
- **Improved error classification** for async audio libraries (aiohttp, aiofiles)
- **Better integration** with Home Assistant's native components

## 🔄 Migration Notes

This is a patch release that requires no user action. The integration will automatically use the improved configuration flow and cleaned-up codebase.

## 🐛 Bug Fixes
- Fixed config flow domain registration issue
- Removed all remaining GStreamer dependencies and references
- Improved Bluetooth device discovery reliability

---

**Full Changelog**: [v0.13.0...v0.13.1](https://github.com/jhaleit/bluetooth-to-airplay-bridge/compare/v0.13.0...v0.13.1)