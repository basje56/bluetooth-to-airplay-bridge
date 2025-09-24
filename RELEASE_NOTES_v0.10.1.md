# Release Notes v0.10.1: Dependency Installation Fix

## 🔧 Critical Bug Fix

This patch release resolves installation issues with system-level dependencies that were preventing the integration from installing properly in Home Assistant.

## 🐛 Issues Fixed

### Installation Dependency Errors
- **Fixed**: Removed `pygobject>=3.42.0` and `pycairo>=1.20.0` from required dependencies
- **Fixed**: Installation errors with `mesonpy.build_wheel` and permission denied errors
- **Fixed**: Integration now installs successfully without system-level compilation requirements

### Enhanced Dependency Management
- **Added**: `requirements_optional.txt` for advanced audio features
- **Improved**: Clear documentation on optional vs required dependencies
- **Enhanced**: Installation instructions with multiple installation methods

## 📋 What Changed

### Core Dependencies (Required)
The integration now only requires these Python packages that install cleanly:
- `zeroconf>=0.47.0` - For AirPlay discovery
- `cryptography>=3.4.8` - For secure connections
- `pydbus>=0.6.0` - For D-Bus communication

### Optional Dependencies (Enhanced Features)
Advanced audio processing features are now optional and can be installed separately:
- `pygobject>=3.42.0` - For GStreamer integration
- `pycairo>=1.20.0` - Cairo graphics library (dependency of pygobject)

## 🚀 Installation

### Standard Installation (Works Out of Box)
The integration now installs without any compilation or system dependencies:

1. **HACS**: Install directly from HACS - no additional setup required
2. **Manual**: Copy files and restart - works immediately

### Optional Enhanced Audio (Advanced Users)
For users who want advanced GStreamer audio processing:

```bash
# Ubuntu/Debian
sudo apt-get install gstreamer1.0-dev libgirepository1.0-dev python3-gi

# macOS
brew install gstreamer gobject-introspection pygobject3

# Or install Python packages (after system dependencies)
pip install -r requirements_optional.txt
```

## 🔄 Upgrade Instructions

### From v0.10.0
1. **Update** the integration through HACS or manually
2. **Restart** Home Assistant
3. **No configuration changes** required - existing setups continue working

### Functionality Impact
- **Core Features**: All core functionality works without optional dependencies
- **Audio Processing**: Basic audio bridging works immediately
- **Enhanced Audio**: Advanced GStreamer features require optional dependencies
- **Graceful Degradation**: Integration detects available features automatically

## 🎯 Benefits

- ✅ **Instant Installation**: No more compilation errors or permission issues
- ✅ **Broader Compatibility**: Works on more Home Assistant installations
- ✅ **Simplified Setup**: Core features work out of the box
- ✅ **Optional Enhancement**: Advanced users can still enable enhanced features
- ✅ **Better Documentation**: Clear guidance on what's required vs optional

## 🔗 Links

- **GitHub Repository**: https://github.com/jhaleit/bluetooth-to-airplay-bridge
- **Issues**: https://github.com/jhaleit/bluetooth-to-airplay-bridge/issues
- **Documentation**: https://github.com/jhaleit/bluetooth-to-airplay-bridge/blob/main/README.md

---

**Note**: This is a critical fix for users experiencing installation issues. All users are encouraged to upgrade to resolve dependency installation problems.