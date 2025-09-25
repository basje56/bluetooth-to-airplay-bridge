# Config Flow Error Solution: "Invalid handler specified"

## 🔍 Root Cause Analysis

**Date:** 2025-09-25  
**Error:** `Config flow could not be loaded: {"message":"Invalid handler specified"}`  
**Integration:** `bluetooth_to_airplay_bridge`  

### Key Finding

The "Invalid handler specified" error is a **generic error message** that masks the real underlying import error. Based on research and testing, this error occurs when Home Assistant cannot import the `config_flow.py` module due to missing Python dependencies.

### Research Sources

- [Home Assistant Core Issue #100622](https://github.com/home-assistant/core/issues/100622) - Shows actual import errors behind "Invalid handler specified"
- [HACS AsusRouter Issue #883](https://github.com/Vaskivskyi/ha-asusrouter/issues/883) - Demonstrates missing module errors
- [Home Assistant Core Issue #127966](https://github.com/home-assistant/core/issues/127966) - Shows dependency installation failures

### Actual Error Details

The real error is logged separately in `homeassistant.config_entries` with the format:
```
Error occurred loading flow for integration bluetooth_to_airplay_bridge: No module named '[missing_module]'
```

## 🧪 Diagnostic Results

**Test Environment:** Python 3.13.2 on macOS  
**Test Date:** 2025-09-25T10:06:13.528969  

### Missing Dependencies Identified

| Module | Status | Error | Required By |
|--------|--------|-------|-------------|
| `zeroconf` | ❌ FAILED | No module named 'zeroconf' | manifest.json requirements |
| `cryptography` | ❌ FAILED | No module named 'cryptography' | manifest.json requirements |
| `pydbus` | ❌ FAILED | No module named 'pydbus' | manifest.json requirements |
| `voluptuous` | ❌ FAILED | No module named 'voluptuous' | config_flow.py imports |

### Requirements from manifest.json

```json
"requirements": [
  "zeroconf>=0.47.0",
  "cryptography>=3.4.8",
  "pydbus>=0.6.0"
]
```

## 🔧 Solution

### For Home Assistant Users

**The error will resolve automatically** when Home Assistant installs the integration's dependencies. However, if the error persists:

1. **Enable Debug Logging** to see the actual error:
   ```yaml
   # configuration.yaml
   logger:
     default: info
     logs:
       homeassistant.config_entries: debug
       custom_components.bluetooth_to_airplay_bridge: debug
   ```

2. **Check Home Assistant Logs** for the real error:
   ```
   Settings > System > Logs
   ```
   Look for: `Error occurred loading flow for integration bluetooth_to_airplay_bridge: [actual error]`

3. **Restart Home Assistant** after enabling debug logging

4. **Check Dependencies Installation** in the logs:
   ```
   homeassistant.util.package] Attempting install of zeroconf>=0.47.0
   homeassistant.util.package] Attempting install of cryptography>=3.4.8
   homeassistant.util.package] Attempting install of pydbus>=0.6.0
   ```

### For Developers

1. **Test Dependencies Locally:**
   ```bash
   python3 debug_imports.py
   ```

2. **Install Missing Dependencies:**
   ```bash
   pip install zeroconf>=0.47.0 cryptography>=3.4.8 pydbus>=0.6.0 voluptuous
   ```

3. **Verify manifest.json Requirements:**
   - Ensure all required packages are listed
   - Use proper version constraints
   - Test in clean environment

## 🚨 Common Causes

1. **Missing Dependencies:** Most common - Home Assistant failed to install requirements
2. **Version Conflicts:** Incompatible package versions
3. **Platform Issues:** Some packages (like `pydbus`) may not work on all platforms
4. **Network Issues:** Package installation failed due to connectivity
5. **Permission Issues:** Home Assistant lacks permission to install packages

## 📋 Debug Checklist

- [ ] Check Home Assistant logs for actual import error
- [ ] Enable debug logging for `homeassistant.config_entries`
- [ ] Verify all manifest.json requirements are installable
- [ ] Test imports in clean Python environment
- [ ] Check for platform-specific dependency issues
- [ ] Verify Home Assistant has internet access for package installation
- [ ] Restart Home Assistant after dependency changes

## 🔍 Debug Commands

### Enable Debug Logging
```yaml
# configuration.yaml
logger:
  default: info
  logs:
    homeassistant.config_entries: debug
    homeassistant.util.package: debug
    custom_components.bluetooth_to_airplay_bridge: debug
```

### Test Dependencies
```bash
# Run the debug script
python3 debug_imports.py

# Manual testing
python3 -c "import zeroconf; print('zeroconf OK')"
python3 -c "import cryptography; print('cryptography OK')"
python3 -c "import pydbus; print('pydbus OK')"
python3 -c "import voluptuous; print('voluptuous OK')"
```

## 📊 Debug Output Schema

```json
{
  "level": "ERROR",
  "component": "config_entries",
  "event": "import_error",
  "message": "Error occurred loading flow for integration bluetooth_to_airplay_bridge: No module named 'zeroconf'",
  "timestamp": "2025-09-25T10:06:13.528969",
  "request_id": "config-flow-load-attempt",
  "context": {
    "domain": "bluetooth_to_airplay_bridge",
    "config_flow": true,
    "missing_module": "zeroconf"
  },
  "error": {
    "type": "ModuleNotFoundError",
    "code": "IMPORT_ERROR",
    "message": "No module named 'zeroconf'",
    "suggested_actions": [
      "Check Home Assistant logs for dependency installation",
      "Verify internet connectivity",
      "Restart Home Assistant",
      "Check manifest.json requirements"
    ]
  }
}
```

## ✅ Resolution Status

- **Root Cause:** ✅ IDENTIFIED - Missing Python dependencies
- **Solution:** ✅ DOCUMENTED - Enable debug logging to see actual errors
- **Prevention:** ✅ PROVIDED - Dependency testing script and checklist

---

**Next Steps for Users:**
1. Enable debug logging in Home Assistant
2. Check logs for actual import errors
3. Restart Home Assistant to trigger dependency installation
4. Report specific dependency errors if they persist

**Next Steps for Developers:**
1. Test all dependencies in clean environment
2. Consider platform compatibility for requirements
3. Add better error handling for missing dependencies
4. Document known platform-specific issues