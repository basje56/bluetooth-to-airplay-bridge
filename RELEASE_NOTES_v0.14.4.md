# Release Notes - v0.14.4: HAOS Audio Integration & Enhanced Compatibility

**Release Date**: January 25, 2025  
**Version**: 0.14.4  
**Compatibility**: Home Assistant 2024.1.0+ (Fully compatible with HA 2025.x)

## 🏠 Major Feature: Complete HAOS Audio Integration

This release introduces comprehensive Home Assistant Operating System (HAOS) audio integration, addressing the `pactl` detection issues and providing seamless audio control across all Home Assistant installation types.

### 🔧 **Enhanced Audio Engine**

#### **Multi-Environment Detection**
- ✅ **Automatic Environment Detection**: Detects HAOS, Supervised, Container, and Standalone installations
- ✅ **Smart Method Selection**: Optimizes audio command execution based on detected environment
- ✅ **Robust Fallback System**: Graceful degradation when audio tools are unavailable

#### **HAOS Container Integration**
- 🐳 **Container Access**: `docker exec -i hassio_audio pactl <command>` for direct PulseAudio control
- 🏠 **Home Assistant CLI**: `ha audio <command>` integration for volume control and device management
- 🔄 **Seamless Switching**: Automatic method selection with intelligent fallback

#### **Command Mapping & Compatibility**
- ✅ **PulseAudio Commands**: Full support for `pactl list sources`, `pactl set-source-volume`, etc.
- ✅ **HA CLI Integration**: Native `ha audio volume`, `ha audio info` command support
- ✅ **Cross-Platform**: Works across all Home Assistant installation methods

### 🛠️ **Technical Improvements**

#### **Audio Engine Enhancements**
- **Environment Detection**: New `_detect_ha_environment()` method for installation type identification
- **Method Optimization**: Prioritized command execution order based on environment
- **Error Handling**: Comprehensive exception handling for container access and CLI operations
- **Logging**: Detailed debug information for troubleshooting audio issues

#### **Container Integration**
- **Docker Integration**: Direct `hassio_audio` container access for HAOS environments
- **CLI Mapping**: Home Assistant CLI command mapping for audio operations
- **Fallback Mechanisms**: Multiple detection and execution methods for reliability

#### **Performance Optimizations**
- **Cached Detection**: Environment detection results cached to avoid repeated checks
- **Async Operations**: All audio operations remain asynchronous for optimal performance
- **Resource Management**: Efficient container access with proper cleanup

### 📚 **Documentation & User Experience**

#### **New Documentation**
- 📖 **HAOS_AUDIO_INTEGRATION.md**: Comprehensive guide for HAOS audio integration
  - Environment detection methods and command mapping
  - Troubleshooting guides with debug commands
  - Security considerations and performance notes
  - Requirements for different HA installation types

#### **Updated README**
- 🏠 **HAOS Integration Section**: Detailed HAOS audio requirements and capabilities
- 🔧 **Troubleshooting**: HAOS-specific troubleshooting information
- 📋 **Requirements**: Updated system compatibility information

### 🔍 **Compatibility Matrix**

| Environment | Detection Method | Audio Access | Status |
|-------------|------------------|--------------|--------|
| **HAOS** | Container detection | `docker exec hassio_audio` + `ha audio` | ✅ Full Support |
| **Supervised** | CLI + Container | `ha audio` + Container fallback | ✅ Full Support |
| **Container** | Direct + CLI | Direct `pactl` + `ha audio` | ✅ Full Support |
| **Standalone** | Direct + Fallback | Direct `pactl` + Container fallback | ✅ Full Support |

### 🚀 **User Benefits**

#### **For HAOS Users**
- **Zero Configuration**: Automatic detection and setup
- **Native Integration**: Works seamlessly with HAOS audio container
- **Better Reliability**: Robust error handling and fallback mechanisms
- **Enhanced Debugging**: Comprehensive logging and diagnostics

#### **For All Users**
- **Universal Compatibility**: Works across all Home Assistant installation types
- **Improved Stability**: Better error handling and recovery mechanisms
- **Enhanced Performance**: Optimized audio command execution
- **Better Documentation**: Comprehensive guides and troubleshooting information

## 🔧 **Technical Details**

### **New Functions & Methods**
- `_detect_ha_environment()`: Environment type detection
- `_try_haos_container_pactl()`: HAOS container audio access
- `_try_ha_cli_audio()`: Home Assistant CLI integration
- `_execute_ha_cli_command()`: HA CLI command execution
- `_execute_container_pactl()`: Container-based pactl execution

### **Enhanced Error Handling**
- Container access validation
- CLI command availability checking
- Graceful fallback when methods fail
- Detailed error logging and diagnostics

### **Command Mapping**
```bash
# HAOS Container Method
docker exec -i hassio_audio pactl list sources
docker exec -i hassio_audio pactl set-source-volume <source> <volume>

# Home Assistant CLI Method  
ha audio info
ha audio volume --source <source> --volume <volume>
```

## 🐛 **Bug Fixes**

- **Fixed**: `pactl` not detected in HAOS environments
- **Fixed**: Audio commands failing in containerized environments
- **Fixed**: Missing fallback mechanisms for different HA installations
- **Fixed**: Incomplete error handling for audio system access

## 📋 **Installation & Upgrade**

### **HACS Users**
1. Update to v0.14.4 through HACS
2. Restart Home Assistant
3. No additional configuration required - automatic HAOS detection

### **Manual Installation**
1. Download v0.14.4 from GitHub releases
2. Replace existing integration files
3. Restart Home Assistant

## 🔍 **Troubleshooting**

### **HAOS Audio Issues**
- Check `hassio_audio` container status: `docker ps | grep hassio_audio`
- Test HA CLI: `ha audio info`
- Review integration logs with debug logging enabled

### **Debug Logging**
```yaml
logger:
  logs:
    custom_components.bluetooth_to_airplay_bridge.audio_engine: debug
    custom_components.bluetooth_to_airplay_bridge.audio_diagnostics: debug
```

## 🎯 **What's Next**

- Enhanced audio quality detection for HAOS environments
- Additional HA CLI command integration
- Performance optimizations for container access
- Extended diagnostics and monitoring capabilities

---

**Full Changelog**: [v0.14.3...v0.14.4](https://github.com/jhaleit/bluetooth-to-airplay-bridge/compare/v0.14.3...v0.14.4)

**Download**: [GitHub Releases](https://github.com/jhaleit/bluetooth-to-airplay-bridge/releases/tag/v0.14.4)

**HACS**: Available for automatic update through HACS custom repositories