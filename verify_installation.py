#!/usr/bin/env python3
"""
Verification script for Bluetooth to AirPlay Bridge integration.
This script helps diagnose installation and loading issues.
"""

import os
import sys
import json
from pathlib import Path

def find_installation_paths():
    """Find all possible installation paths for the integration."""
    paths = []
    
    # Check HACS installations
    hacs_path = Path.home() / ".homeassistant" / "custom_components" / "bluetooth_to_airplay_bridge"
    alt_hacs_path = Path("/config/custom_components/bluetooth_to_airplay_bridge")
    
    if hacs_path.exists():
        paths.append(("HACS", hacs_path))
    if alt_hacs_path.exists():
        paths.append(("HACS", alt_hacs_path))
    
    # Check manual installation in current directory
    manual_path = Path.cwd() / "custom_components" / "bluetooth_to_airplay_bridge"
    if manual_path.exists():
        paths.append(("Manual", manual_path))
    
    return paths

def check_file_structure():
    """Check if all required files exist."""
    print("🔍 Checking file structure...")
    
    # Find all installation paths
    installation_paths = find_installation_paths()
    
    if not installation_paths:
        print("  ❌ No installation found!")
        print("  📍 Checked locations:")
        print(f"    - HACS: {Path.home() / '.homeassistant' / 'custom_components' / 'bluetooth_to_airplay_bridge'}")
        print(f"    - HACS: /config/custom_components/bluetooth_to_airplay_bridge")
        print(f"    - Manual: {Path.cwd() / 'custom_components' / 'bluetooth_to_airplay_bridge'}")
        return False
    
    print(f"  📍 Found {len(installation_paths)} installation(s):")
    for install_type, path in installation_paths:
        print(f"    - {install_type}: {path}")
    
    # Check each installation
    all_valid = True
    for install_type, base_path in installation_paths:
        print(f"\n  🔍 Checking {install_type} installation at {base_path}:")
        
        required_files = [
            "__init__.py",
            "config_flow.py", 
            "manifest.json",
            "const.py",
            "media_player.py",
            "strings.json",
            "translations/en.json",
        ]
        
        missing_files = []
        for file_name in required_files:
            file_path = base_path / file_name
            if not file_path.exists():
                missing_files.append(file_name)
            else:
                print(f"    ✅ {file_name}")
        
        if missing_files:
            print(f"    ❌ Missing files: {missing_files}")
            all_valid = False
        else:
            print(f"    ✅ All required files present in {install_type} installation")
    
    return all_valid

def check_manifest():
    """Check manifest.json for correct configuration."""
    print("\n📋 Checking manifest.json...")
    
    installation_paths = find_installation_paths()
    
    if not installation_paths:
        print("  ❌ No installation found to check manifest")
        return False
    
    all_valid = True
    for install_type, base_path in installation_paths:
        print(f"\n  🔍 Checking {install_type} manifest at {base_path}:")
        
        manifest_path = base_path / "manifest.json"
        
        if not manifest_path.exists():
            print(f"    ❌ Manifest not found: {manifest_path}")
            all_valid = False
            continue
        
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            
            # Check required fields
            required_fields = ["domain", "name", "version", "documentation_url", "issue_tracker"]
            for field in required_fields:
                if field not in manifest:
                    print(f"    ❌ Missing required field: {field}")
                    all_valid = False
                else:
                    print(f"    ✅ {field}: {manifest[field]}")
            
            # Check domain matches directory name
            if manifest.get("domain") != "bluetooth_to_airplay_bridge":
                print(f"    ❌ Domain mismatch: {manifest.get('domain')} != bluetooth_to_airplay_bridge")
                all_valid = False
            else:
                print(f"    ✅ Domain matches directory name")
            
            if all([field in manifest for field in required_fields]) and manifest.get("domain") == "bluetooth_to_airplay_bridge":
                print(f"    ✅ {install_type} manifest configuration is valid")
            
        except json.JSONDecodeError as e:
            print(f"    ❌ Invalid JSON in manifest: {e}")
            all_valid = False
        except Exception as e:
            print(f"    ❌ Error reading manifest: {e}")
            all_valid = False
    
    return all_valid

def check_syntax():
    """Check Python syntax of all files."""
    print("\n🐍 Checking Python syntax...")
    
    installation_paths = find_installation_paths()
    
    if not installation_paths:
        print("  ❌ No installation found to check syntax")
        return False
    
    all_valid = True
    for install_type, base_path in installation_paths:
        print(f"\n  🔍 Checking {install_type} Python syntax at {base_path}:")
        
        python_files = [
            "__init__.py",
            "config_flow.py",
            "const.py", 
            "media_player.py",
        ]
        
        for file_name in python_files:
            file_path = base_path / file_name
            if not file_path.exists():
                print(f"    ⚠️  {file_name} not found")
                continue
                
            try:
                with open(file_path, "r") as f:
                    compile(f.read(), str(file_path), "exec")
                print(f"    ✅ {file_name}")
            except SyntaxError as e:
                print(f"    ❌ Syntax error in {file_name}: {e}")
                all_valid = False
            except Exception as e:
                print(f"    ❌ Error checking {file_name}: {e}")
                all_valid = False
        
        if all_valid:
            print(f"    ✅ All {install_type} Python files have valid syntax")
    
    return all_valid

def check_imports():
    """Check if imports work correctly."""
    print("\n📦 Checking imports...")
    
    installation_paths = find_installation_paths()
    
    if not installation_paths:
        print("  ❌ No installation found to check imports")
        return False
    
    all_valid = True
    for install_type, base_path in installation_paths:
        print(f"\n  🔍 Checking {install_type} imports at {base_path}:")
        
        # Add the custom_components directory to Python path temporarily
        custom_components_path = base_path.parent
        if str(custom_components_path) not in sys.path:
            sys.path.insert(0, str(custom_components_path))
        
        try:
            # Try importing the integration
            import importlib.util
            
            # Check const.py first as it's usually imported by others
            const_path = base_path / "const.py"
            if const_path.exists():
                try:
                    spec = importlib.util.spec_from_file_location("const", const_path)
                    if spec and spec.loader:
                        const_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(const_module)
                        print(f"    ✅ const.py imports successfully")
                    else:
                        print(f"    ❌ Could not create spec for const.py")
                        all_valid = False
                except Exception as e:
                    print(f"    ❌ Error importing const.py: {e}")
                    all_valid = False
            
            # Check __init__.py
            init_path = base_path / "__init__.py"
            if init_path.exists():
                try:
                    spec = importlib.util.spec_from_file_location("__init__", init_path)
                    if spec and spec.loader:
                        init_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(init_module)
                        print(f"    ✅ __init__.py imports successfully")
                    else:
                        print(f"    ❌ Could not create spec for __init__.py")
                        all_valid = False
                except Exception as e:
                    print(f"    ❌ Error importing __init__.py: {e}")
                    all_valid = False
            
        except Exception as e:
            print(f"    ❌ General import error: {e}")
            all_valid = False
        finally:
            # Remove from path
            if str(custom_components_path) in sys.path:
                sys.path.remove(str(custom_components_path))
    
    if all_valid:
        print("  ✅ All imports work correctly")
    
    return all_valid

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