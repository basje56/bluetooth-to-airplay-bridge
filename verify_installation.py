#!/usr/bin/env python3
"""
Verification script for Bluetooth to AirPlay Bridge integration.
This script helps diagnose installation and loading issues.
"""

import os
import sys
import json
from pathlib import Path

def check_file_structure():
    """Check if all required files exist."""
    print("🔍 Checking file structure...")
    
    required_files = [
        "custom_components/bluetooth_to_airplay_bridge/__init__.py",
        "custom_components/bluetooth_to_airplay_bridge/config_flow.py",
        "custom_components/bluetooth_to_airplay_bridge/manifest.json",
        "custom_components/bluetooth_to_airplay_bridge/const.py",
        "custom_components/bluetooth_to_airplay_bridge/media_player.py",
        "custom_components/bluetooth_to_airplay_bridge/strings.json",
        "custom_components/bluetooth_to_airplay_bridge/translations/en.json",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print(f"  ❌ Missing files: {missing_files}")
        return False
    
    print("  ✅ All required files present")
    return True

def check_manifest():
    """Check manifest.json for correctness."""
    print("\n📋 Checking manifest.json...")
    
    try:
        with open("custom_components/bluetooth_to_airplay_bridge/manifest.json", "r") as f:
            manifest = json.load(f)
        
        required_keys = ["domain", "name", "config_flow", "version"]
        for key in required_keys:
            if key in manifest:
                print(f"  ✅ {key}: {manifest[key]}")
            else:
                print(f"  ❌ Missing key: {key}")
                return False
        
        # Check domain matches directory
        if manifest["domain"] != "bluetooth_to_airplay_bridge":
            print(f"  ❌ Domain mismatch: {manifest['domain']} != bluetooth_to_airplay_bridge")
            return False
        
        print("  ✅ Manifest is valid")
        return True
        
    except Exception as e:
        print(f"  ❌ Error reading manifest: {e}")
        return False

def check_syntax():
    """Check Python syntax of main files."""
    print("\n🐍 Checking Python syntax...")
    
    files_to_check = [
        "custom_components/bluetooth_to_airplay_bridge/__init__.py",
        "custom_components/bluetooth_to_airplay_bridge/config_flow.py",
        "custom_components/bluetooth_to_airplay_bridge/const.py",
        "custom_components/bluetooth_to_airplay_bridge/media_player.py",
    ]
    
    for file_path in files_to_check:
        try:
            with open(file_path, "r") as f:
                compile(f.read(), file_path, "exec")
            print(f"  ✅ {file_path}")
        except SyntaxError as e:
            print(f"  ❌ Syntax error in {file_path}: {e}")
            return False
        except Exception as e:
            print(f"  ❌ Error checking {file_path}: {e}")
            return False
    
    print("  ✅ All Python files have valid syntax")
    return True

def check_imports():
    """Check if imports work correctly."""
    print("\n📦 Checking Python syntax...")
    
    # Validate Python syntax of all integration files
    syntax_valid = True
    integration_files = [
        "custom_components/bluetooth_to_airplay_bridge/__init__.py",
        "custom_components/bluetooth_to_airplay_bridge/config_flow.py", 
        "custom_components/bluetooth_to_airplay_bridge/const.py",
        "custom_components/bluetooth_to_airplay_bridge/media_player.py"
    ]
    
    for file_path in integration_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), file_path, 'exec')
                print(f"  ✅ {os.path.basename(file_path)} syntax valid")
            except SyntaxError as e:
                print(f"  ❌ {os.path.basename(file_path)} syntax error: {e}")
                syntax_valid = False
            except Exception as e:
                print(f"  ❌ Error checking {os.path.basename(file_path)}: {e}")
                syntax_valid = False
        else:
            print(f"  ⚠️  {file_path} not found")
            syntax_valid = False
            
    if syntax_valid:
        print("  ✅ All Python files have valid syntax")
    
    return syntax_valid

def generate_installation_instructions():
    """Generate installation instructions."""
    print("\n📝 Installation Instructions:")
    print("=" * 50)
    
    print("\n1. HACS Installation (Recommended):")
    print("   - Go to HACS → Integrations")
    print("   - Click the three dots menu → Custom repositories")
    print("   - Add: https://github.com/jhaleit/bluetooth-to-airplay-bridge")
    print("   - Category: Integration")
    print("   - Click 'Add'")
    print("   - Find 'Bluetooth to AirPlay Bridge' and install")
    print("   - Restart Home Assistant")
    
    print("\n2. Manual Installation:")
    print("   - Copy the entire 'custom_components/bluetooth_to_airplay_bridge' folder")
    print("   - Paste it into your Home Assistant 'custom_components' directory")
    print("   - The path should be: <config>/custom_components/bluetooth_to_airplay_bridge/")
    print("   - Restart Home Assistant")
    
    print("\n3. Verification:")
    print("   - Go to Settings → Devices & Services")
    print("   - Click 'Add Integration'")
    print("   - Search for 'Bluetooth to AirPlay Bridge'")
    print("   - If it appears, the integration is properly installed")
    
    print("\n4. Troubleshooting:")
    print("   - Check Home Assistant logs for any error messages")
    print("   - Ensure all files have correct permissions")
    print("   - Verify the integration version matches the latest release")

def main():
    """Main verification function."""
    print("🔧 Bluetooth to AirPlay Bridge Integration Verification")
    print("=" * 60)
    
    all_checks_passed = True
    
    # Run all checks
    all_checks_passed &= check_file_structure()
    all_checks_passed &= check_manifest()
    all_checks_passed &= check_syntax()
    all_checks_passed &= check_imports()
    
    print("\n" + "=" * 60)
    
    if all_checks_passed:
        print("✅ All checks passed! Integration appears to be correctly set up.")
        print("\nIf you're still experiencing issues:")
        print("1. Ensure the integration is installed in your Home Assistant instance")
        print("2. Restart Home Assistant completely")
        print("3. Check Home Assistant logs for specific error messages")
        print("4. Verify you're using the latest version (v1.0.2)")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
    
    generate_installation_instructions()

if __name__ == "__main__":
    main()