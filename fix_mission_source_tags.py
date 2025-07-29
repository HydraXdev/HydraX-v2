#!/usr/bin/env python3
"""
Fix existing mission files missing source field
Adds "source": "venom_scalp_master" to all mission files that don't have it
"""

import json
import os
from pathlib import Path

def fix_mission_source_tags():
    """Add source field to mission files missing it"""
    
    missions_dir = Path('/root/HydraX-v2/missions')
    if not missions_dir.exists():
        print("❌ Missions directory not found")
        return
    
    # Patterns to scan
    patterns = ["mission_*.json", "5_*_USER*.json"]
    
    fixed_count = 0
    already_tagged = 0
    error_count = 0
    
    print("🔍 SCANNING MISSION FILES FOR SOURCE TAGS")
    print("=" * 50)
    
    for pattern in patterns:
        print(f"\n📁 Scanning pattern: {pattern}")
        
        for mission_file in missions_dir.glob(pattern):
            try:
                # Read existing file
                with open(mission_file, 'r') as f:
                    data = json.load(f)
                
                # Check if source field exists
                if 'source' not in data:
                    # Add source field
                    data['source'] = 'venom_scalp_master'
                    
                    # Write back to file
                    with open(mission_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    signal_id = data.get('signal_id') or data.get('mission_id', 'unknown')
                    print(f"✅ FIXED: {signal_id} - Added source tag")
                    fixed_count += 1
                    
                elif data.get('source') == 'venom_scalp_master':
                    already_tagged += 1
                    
                else:
                    signal_id = data.get('signal_id') or data.get('mission_id', 'unknown')
                    print(f"⚠️ INVALID SOURCE: {signal_id} - Source: {data.get('source')}")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ ERROR processing {mission_file}: {e}")
                error_count += 1
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"✅ Files fixed: {fixed_count}")
    print(f"✓ Already tagged: {already_tagged}")
    print(f"❌ Errors: {error_count}")
    print(f"📁 Total processed: {fixed_count + already_tagged + error_count}")
    
    if fixed_count > 0:
        print(f"\n🎉 SUCCESS: Added source tags to {fixed_count} mission files")
        print("🔍 These files are now compatible with enhanced truth tracker")
    else:
        print("\n✅ All mission files already have proper source tags")

if __name__ == "__main__":
    fix_mission_source_tags()