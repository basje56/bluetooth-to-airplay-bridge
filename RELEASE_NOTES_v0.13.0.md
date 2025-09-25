# Release Notes v0.13.0 - Async Audio Engine Migration

**Release Date**: January 2025  
**Type**: Major Release - Breaking Changes  
**Migration Required**: Yes (automatic)

## 🚀 Major Changes

### 🎵 Complete Audio Engine Rewrite

- **Migrated from GStreamer to Async Audio Processing** - Complete replacement of GStreamer-based audio pipeline with modern asynchronous implementation
- **Removed pygobject dependency** - Eliminated complex native library dependency for improved compatibility
- **Enhanced PulseAudio integration** - Direct integration with PulseAudio for better audio capture and control
- **Improved performance** - Asynchronous audio processing reduces blocking operations and improves responsiveness

### 🔧 New Dependencies

- **Added `aiohttp>=3.8.0`** - Asynchronous HTTP client for efficient audio streaming
- **Added `aiofiles>=23.0.0`** - Asynchronous file operations for better I/O performance
- **Removed `pygobject>=3.42.0`** - No longer needed with new async audio engine
- **Kept `zeroconf>=0.47.0`** - Still used for AirPlay device discovery via mDNS

### 🏗️ Architecture Improvements

- **Async-first audio processing** - All audio operations now use asyncio for better integration with Home Assistant
- **Simplified installation** - Removed complex native library requirements
- **Better error handling** - Improved error recovery and logging for audio operations
- **Enhanced diagnostics** - Updated diagnostic checks for new async libraries

## 📋 Technical Details

### Audio Engine Changes

| Component | Old Implementation | New Implementation |
|-----------|-------------------|-------------------|
| Audio Pipeline | GStreamer with pygobject | PulseAudio with asyncio subprocess |
| Audio Capture | GStreamer pipeline | `parec` command with async processing |
| Audio Streaming | GStreamer elements | aiohttp streaming with aiofiles |
| Volume Control | GStreamer volume element | PulseAudio `pactl` commands |
| Format Handling | GStreamer caps | PulseAudio format strings |

### Dependencies Comparison

| Dependency | v0.12.1 | v0.13.0 | Change |
|------------|---------|---------|--------|
| `pygobject>=3.42.0` | ✅ Required | ❌ Removed | Major simplification |
| `zeroconf>=0.47.0` | ✅ Required | ✅ Required | No change |
| `aiohttp>=3.8.0` | ❌ Not used | ✅ Required | New async HTTP client |
| `aiofiles>=23.0.0` | ❌ Not used | ✅ Required | New async file operations |

### 🏠 Home Assistant Compatibility

- **Minimum Version**: Home Assistant 2024.1.0+
- **HACS Compatibility**: Fully compatible with latest HACS requirements
- **Installation Method**: Available through HACS custom repositories
- **Update Process**: Automatic updates through HACS for existing installations

## 🔄 Migration Guide

### For Existing Installations

**Automatic Migration**: This update will automatically migrate your configuration. No manual intervention required.

1. **Update through HACS** - Standard HACS update process
2. **Restart Home Assistant** - Required to load new audio engine
3. **Verify functionality** - Check that audio streaming still works as expected

### System Requirements

**Before v0.13.0**:
- GStreamer 1.14+ with Python bindings
- PyGObject for GStreamer integration

**After v0.13.0**:
- PulseAudio for audio capture and processing
- Standard Python asyncio libraries (included with Home Assistant)

### Troubleshooting

If you experience issues after upgrading:

1. **Check PulseAudio** - Ensure PulseAudio is running on your system
2. **Verify Bluetooth audio** - Test Bluetooth audio capture with `pactl list sources`
3. **Review logs** - Check Home Assistant logs for audio engine errors
4. **Restart integration** - Reload the integration if needed

## 🐛 Bug Fixes

- **Fixed audio pipeline stability** - Async implementation provides better error recovery
- **Improved Bluetooth audio detection** - More reliable detection of Bluetooth audio sources
- **Enhanced volume synchronization** - Better volume control with direct PulseAudio integration

## ⚠️ Breaking Changes

- **GStreamer no longer supported** - Installations relying on specific GStreamer configurations may need adjustment
- **Audio format handling changed** - Now uses PulseAudio format strings instead of GStreamer caps
- **Diagnostic checks updated** - Audio diagnostics now check for async libraries instead of GStreamer

## 🔮 Future Roadmap

- **Enhanced audio codecs** - Support for additional audio codecs with async processing
- **Improved streaming protocols** - Better AirPlay protocol implementation
- **Advanced audio processing** - Real-time audio effects and processing capabilities

---

**Full Changelog**: [v0.12.1...v0.13.0](https://github.com/your-repo/bluetooth-to-airplay-bridge/compare/v0.12.1...v0.13.0)