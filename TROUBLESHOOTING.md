# Troubleshooting Guide: UnknownHandler Error

## 🚨 Critical Issue: UnknownHandler Error

If you're seeing this error in your Home Assistant logs:
```
homeassistant.data_entry_flow.UnknownHandler
```

This means Home Assistant detects a Bluetooth device but cannot find the integration's config flow handler.

## 🔍 Step-by-Step Resolution

### Step 1: Verify Current Installation

**Check your current version:**
1. Go to HACS → Integrations
2. Find "Bluetooth to AirPlay Bridge"
3. Verify version is **v1.0.3** or later

**Or check manually:**
```bash
cat custom_components/bluetooth_to_airplay_bridge/manifest.json | grep version
```
Should show: `"version": "1.0.3"`

### Step 2: Complete Clean Reinstallation

**If using HACS:**
1. Go to HACS → Integrations
2. Find "Bluetooth to AirPlay Bridge" → Click the 3 dots → Remove
3. Restart Home Assistant
4. Go to HACS → Integrations → + Explore & Download Repositories
5. Search for "Bluetooth to AirPlay Bridge" → Download
6. Restart Home Assistant again

**If using Manual Installation:**
1. Delete the entire folder: `custom_components/bluetooth_to_airplay_bridge/`
2. Download the latest release from GitHub
3. Extract to `custom_components/bluetooth_to_airplay_bridge/`
4. Restart Home Assistant

### Step 3: Enable Debug Logging

Add this to your `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.bluetooth_to_airplay_bridge: debug
    homeassistant.config_entries: debug
    homeassistant.helpers.discovery_flow: debug
```

**Restart Home Assistant** after adding this configuration.

### Step 4: Check Debug Logs

After restart, look for these messages in your logs:

**✅ Success indicators:**
```
INFO: Bluetooth to AirPlay Bridge integration module loaded successfully
INFO: Bluetooth to AirPlay Bridge config flow module loaded successfully
```

**❌ Failure indicators:**
- No "loaded successfully" messages = Integration not loading
- Import errors or syntax errors = File corruption or installation issue
- "Module not found" errors = Installation path issue

### Step 5: Run Installation Verification

Download and run the verification script:
```bash
curl -O https://raw.githubusercontent.com/jhaleit/bluetooth-to-airplay-bridge/main/verify_installation.py
python3 verify_installation.py
```

This will check:
- File structure
- manifest.json validity
- Python syntax
- Installation completeness

### Step 6: Manual File Verification

Ensure these files exist with correct content:

```
custom_components/bluetooth_to_airplay_bridge/
├── __init__.py          (should contain async_setup_entry)
├── config_flow.py       (should contain ConfigFlow class)
├── const.py            (should define DOMAIN = "bluetooth_to_airplay_bridge")
├── manifest.json       (should have version 1.0.3+)
├── media_player.py     (platform implementation)
└── strings.json        (translations)
```

**Check domain consistency:**
```bash
grep -r "bluetooth_to_airplay_bridge" custom_components/bluetooth_to_airplay_bridge/
```

All files should reference the same domain name.

## 🔧 Common Issues & Solutions

### Issue 1: Integration Not Loading
**Symptoms:** No "loaded successfully" messages in logs
**Solutions:**
- Verify file permissions (files should be readable)
- Check for syntax errors in Python files
- Ensure no conflicting integrations with same domain
- Try restarting Home Assistant twice

### Issue 2: Import Errors
**Symptoms:** Python import errors in logs
**Solutions:**
- Reinstall the integration completely
- Check Python syntax with: `python3 -m py_compile filename.py`
- Verify Home Assistant version compatibility

### Issue 3: HACS vs Manual Conflicts
**Symptoms:** Mixed installation causing conflicts
**Solutions:**
- Remove both HACS and manual installations
- Choose one installation method and stick with it
- Clear Home Assistant cache: delete `.storage/core.config_entries`

### Issue 4: Bluetooth Discovery Issues
**Symptoms:** Integration loads but discovery fails
**Solutions:**
- Ensure Bluetooth is enabled on your system
- Check if other Bluetooth integrations are working
- Verify the device is in pairing mode

## 🚨 Emergency Reset

If nothing else works:

1. **Stop Home Assistant**
2. **Remove integration completely:**
   ```bash
   rm -rf custom_components/bluetooth_to_airplay_bridge/
   ```
3. **Clear config entries:**
   ```bash
   # Backup first!
   cp .storage/core.config_entries .storage/core.config_entries.backup
   # Edit and remove any bluetooth_to_airplay_bridge entries
   ```
4. **Reinstall fresh from latest release**
5. **Start Home Assistant**

## 📊 Debug Information to Collect

When reporting issues, include:

1. **Home Assistant version:** `ha core info`
2. **Integration version:** From manifest.json
3. **Installation method:** HACS or Manual
4. **Full error logs** with debug enabled
5. **Output of verification script**
6. **File listing:** `ls -la custom_components/bluetooth_to_airplay_bridge/`

## 📞 Getting Help

If you're still experiencing issues:

1. **Enable debug logging** (Step 3 above)
2. **Run verification script** (Step 5 above)
3. **Collect debug information** (above section)
4. **Open an issue** on GitHub with all collected information

The debug logging in v1.0.3+ will help pinpoint exactly where the loading process fails.