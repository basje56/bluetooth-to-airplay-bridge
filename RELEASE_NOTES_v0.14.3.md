# Release Notes - v0.14.3: Enhanced PulseAudio Integration

**Release Date**: January 27, 2025  
**Version**: 0.14.3  
**Compatibility**: Home Assistant 2025.x+

## 🎯 **Major Audio Engine Improvements**

This release features a complete rewrite of the PulseAudio (pactl) integration, providing more robust and reliable audio management for Bluetooth to AirPlay bridging.

### 🔧 **Core Audio Engine Enhancements**

#### **Rebuilt PulseAudio Integration**
- **Complete pactl Code Rewrite**: Removed all fallback logic and created clean, robust pactl integration
- **Centralized Command Execution**: New `_execute_pactl_command()` method for consistent pactl operations
- **Enhanced Error Handling**: Proper error detection and reporting without silent failures
- **Improved Logging**: Detailed debug information for troubleshooting audio issues

#### **Advanced Bluetooth Audio Detection**
- **Robust Source Detection**: Enhanced `check_bluetooth_audio_available()` with accurate PulseAudio source checking
- **Better Source Naming**: Improved `_get_bluetooth_source_name()` following BlueZ conventions
- **Detailed Source Information**: New `get_bluetooth_source_info()` method for comprehensive device diagnostics

#### **Enhanced Volume Control**
- **Accurate Volume Reading**: Improved `get_bluetooth_volume()` with proper PulseAudio output parsing
- **Reliable Volume Setting**: Enhanced `set_bluetooth_volume()` with validation and error reporting
- **Volume Clamping**: Proper 0.0-1.0 range validation and percentage conversion

#### **Improved Latency Detection**
- **Real Latency Parsing**: Enhanced `get_audio_latency()` that actually reads PulseAudio latency values
- **Microsecond Conversion**: Proper conversion from PulseAudio microseconds to milliseconds
- **Realistic Defaults**: More accurate default latency estimates for Bluetooth A2DP (150ms)

### 🛠️ **Technical Improvements**

#### **Code Quality Enhancements**
- **Removed Fallback Logic**: Eliminated unreliable "pactl not available" assumptions
- **Better Error Messages**: More descriptive error reporting for debugging
- **Consistent API**: Unified method signatures and return types
- **Type Safety**: Improved type hints and validation

#### **Performance Optimizations**
- **Reduced Code Duplication**: Centralized pactl command execution
- **Efficient Parsing**: Optimized PulseAudio output parsing algorithms
- **Better Resource Management**: Improved subprocess handling and cleanup

### 📊 **New Features**

#### **Enhanced Diagnostics**
- **Source Information API**: New method to get detailed Bluetooth audio source information
- **Better Debug Output**: More informative logging for troubleshooting
- **State Monitoring**: Enhanced tracking of PulseAudio source states

#### **Improved Reliability**
- **Robust Command Execution**: Better handling of pactl command failures
- **Proper Error Propagation**: Clear error reporting without masking issues
- **Enhanced Validation**: Better input validation and range checking

## 🔄 **Migration Notes**

### **For Existing Users**
- **Automatic Upgrade**: No configuration changes required
- **Improved Reliability**: Existing setups should experience better audio stability
- **Enhanced Debugging**: Better error messages for troubleshooting

### **System Requirements**
- **PulseAudio Required**: This release assumes PulseAudio/pactl is available
- **Home Assistant 2025.x+**: Continued compatibility with latest HA versions
- **Bluetooth Support**: BlueZ-based Bluetooth stack required

## 🐛 **Bug Fixes**

- **Fixed**: Inconsistent volume reading from PulseAudio sources
- **Fixed**: Silent failures in pactl command execution
- **Fixed**: Inaccurate latency reporting for Bluetooth devices
- **Fixed**: Poor error handling in audio source detection
- **Improved**: Overall stability of audio engine operations

## 📈 **Performance Improvements**

- **Faster Audio Detection**: More efficient PulseAudio source checking
- **Reduced Overhead**: Optimized command execution and parsing
- **Better Resource Usage**: Improved subprocess management
- **Enhanced Responsiveness**: Faster volume control operations

## 🔍 **Developer Notes**

### **API Changes**
- **New Method**: `get_bluetooth_source_info()` for detailed source information
- **Enhanced Methods**: All pactl-related methods now have better error handling
- **Improved Logging**: More detailed debug information throughout audio engine

### **Code Structure**
- **Cleaner Architecture**: Removed complex fallback logic
- **Better Separation**: Clear distinction between pactl operations and error handling
- **Improved Maintainability**: More readable and maintainable code structure

## 📦 **Installation & Update**

### **HACS Users**
1. **Automatic Detection**: HACS should detect v0.14.3 automatically
2. **Manual Update**: Check for updates in HACS if not detected immediately
3. **Restart Required**: Restart Home Assistant after update

### **Manual Installation**
1. **Download**: Get v0.14.3 from GitHub releases
2. **Replace Files**: Update custom_components/bluetooth_to_airplay_bridge/
3. **Restart**: Restart Home Assistant to load new version

## 🚀 **What's Next**

### **Upcoming Features**
- **Advanced Audio Codecs**: Enhanced support for aptX, LDAC, and other high-quality codecs
- **Multi-Device Support**: Improved handling of multiple Bluetooth audio sources
- **Audio Quality Optimization**: Advanced audio processing and quality enhancements

### **Compatibility**
- **Future HA Versions**: Continued compatibility improvements
- **Audio System Support**: Enhanced support for different audio backends
- **Platform Expansion**: Broader platform and hardware support

## 📞 **Support & Feedback**

- **Issues**: Report bugs via [GitHub Issues](https://github.com/jhaleit/bluetooth-to-airplay-bridge/issues)
- **Documentation**: Updated README with comprehensive guides
- **Community**: Join discussions in Home Assistant forums
- **Updates**: Follow releases for latest improvements

---

**Previous Release**: v0.14.2 - Enhanced Documentation & HACS Compatibility  
**Full Changelog**: [GitHub Releases](https://github.com/jhaleit/bluetooth-to-airplay-bridge/releases)