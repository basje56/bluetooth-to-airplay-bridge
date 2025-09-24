#!/usr/bin/env python3
"""
Bluetooth to AirPlay Bridge - Installation Conflict Resolver

This script helps detect and resolve conflicts between HACS and manual installations
that can cause the UnknownHandler error.
"""

import os
import json
import shutil
from pathlib import Path

def check_hacs_installation():
    """Check if integration is installed via HACS."""
    hacs_path = Path.home() / ".homeassistant" / "custom_components" / "bluetooth_to_airplay_bridge"
    alt_hacs_path = Path("/config/custom_components/bluetooth_to_airplay_bridge")
    
    hacs_installed = False
    hacs_location = None
    
    if hacs_path.exists():
        hacs_installed = True
        hacs_location = hacs_path
    elif alt_hacs_path.exists():
        hacs_installed = True
        hacs_location = alt_hacs_path
    
    return hacs_installed, hacs_location

def check_manual_installation():
    """Check if integration is manually installed."""
    current_dir = Path.cwd()
    manual_path = current_dir / "custom_components" / "bluetooth_to_airplay_bridge"
    
    return manual_path.exists(), manual_path

def get_version_from_manifest(path):
    """Get version from manifest.json."""
    try:
        manifest_path = path / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                return manifest.get('version', 'unknown')
    except Exception as e:
        print(f"Error reading manifest from {path}: {e}")
    return 'unknown'

def check_config_entries():
    """Check for conflicting config entries."""
    config_paths = [
        Path.home() / ".homeassistant" / ".storage" / "core.config_entries",
        Path("/config/.storage/core.config_entries")
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    
                entries = config_data.get('data', {}).get('entries', [])
                bridge_entries = [e for e in entries if e.get('domain') == 'bluetooth_to_airplay_bridge']
                
                if bridge_entries:
                    print(f"Found {len(bridge_entries)} config entries in {config_path}")
                    for entry in bridge_entries:
                        print(f"  - Entry ID: {entry.get('entry_id')}")
                        print(f"    Title: {entry.get('title')}")
                        print(f"    State: {entry.get('state', 'unknown')}")
                        
                return len(bridge_entries) > 0, config_path
            except Exception as e:
                print(f"Error reading config entries from {config_path}: {e}")
    
    return False, None

def main():
    print("🔍 Bluetooth to AirPlay Bridge - Installation Conflict Resolver")
    print("=" * 60)
    
    # Check installations
    hacs_installed, hacs_location = check_hacs_installation()
    manual_installed, manual_location = check_manual_installation()
    
    print(f"HACS Installation: {'✅ Found' if hacs_installed else '❌ Not found'}")
    if hacs_installed:
        hacs_version = get_version_from_manifest(hacs_location)
        print(f"  Location: {hacs_location}")
        print(f"  Version: {hacs_version}")
    
    print(f"Manual Installation: {'✅ Found' if manual_installed else '❌ Not found'}")
    if manual_installed:
        manual_version = get_version_from_manifest(manual_location)
        print(f"  Location: {manual_location}")
        print(f"  Version: {manual_version}")
    
    # Check for conflicts
    print("\n🔍 Conflict Analysis:")
    
    if hacs_installed and manual_installed:
        print("⚠️  CONFLICT DETECTED: Both HACS and manual installations found!")
        print("   This can cause the UnknownHandler error.")
        
        hacs_version = get_version_from_manifest(hacs_location)
        manual_version = get_version_from_manifest(manual_location)
        
        print(f"   HACS version: {hacs_version}")
        print(f"   Manual version: {manual_version}")
        
        print("\n🛠️  RESOLUTION STEPS:")
        print("1. Choose ONE installation method:")
        print("   - For HACS: Remove manual installation")
        print("   - For Manual: Remove HACS installation")
        print("2. Restart Home Assistant")
        print("3. Verify only one installation remains")
        
        choice = input("\nRemove manual installation and keep HACS? (y/n): ").lower()
        if choice == 'y':
            try:
                shutil.rmtree(manual_location)
                print(f"✅ Removed manual installation from {manual_location}")
                print("🔄 Please restart Home Assistant now")
            except Exception as e:
                print(f"❌ Error removing manual installation: {e}")
        
    elif not hacs_installed and not manual_installed:
        print("❌ No installation found!")
        print("   Please install the integration via HACS or manually.")
        
    elif hacs_installed:
        print("✅ Only HACS installation found - Good!")
        
    elif manual_installed:
        print("✅ Only manual installation found - Good!")
    
    # Check config entries
    print("\n🔍 Config Entries Analysis:")
    has_entries, config_path = check_config_entries()
    
    if has_entries:
        print("✅ Found existing config entries")
        print("   If you're still getting UnknownHandler errors after resolving")
        print("   installation conflicts, you may need to remove and re-add")
        print("   the integration through the UI.")
    else:
        print("❌ No config entries found")
        print("   You'll need to add the integration through the UI after")
        print("   resolving any installation conflicts.")
    
    print("\n📋 Next Steps:")
    print("1. Resolve any installation conflicts shown above")
    print("2. Restart Home Assistant")
    print("3. Enable debug logging (see debug_logging.yaml)")
    print("4. Check logs for 'integration module loaded successfully'")
    print("5. Add integration through UI if needed")

if __name__ == "__main__":
    main()