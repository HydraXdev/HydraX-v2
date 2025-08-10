#!/usr/bin/env python3
"""
Restore the full War Room implementation from git backup
The War Room was corrupted and replaced with a simple template
This script restores the full 900-line implementation
"""

import subprocess
import sys

def restore_war_room():
    """Restore the full War Room implementation from git"""
    
    print("🔧 Restoring War Room implementation...")
    
    # Get the full webapp from the last known good commit
    try:
        # Get the webapp content from commit b965793
        result = subprocess.run(
            ["git", "show", "b965793:webapp_server_optimized.py"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.returncode != 0:
            print(f"❌ Failed to get backup from git: {result.stderr}")
            return False
            
        backup_content = result.stdout
        backup_lines = backup_content.split('\n')
        
        # Find the War Room function (lines 1429-2328 in the backup)
        war_room_start = None
        war_room_end = None
        
        for i, line in enumerate(backup_lines):
            if "@app.route('/me')" in line:
                war_room_start = i
                print(f"Found War Room start at line {i+1}")
            elif war_room_start and "@app.route('/learn')" in line:
                war_room_end = i
                print(f"Found War Room end at line {i+1}")
                break
        
        if not war_room_start or not war_room_end:
            print("❌ Could not find War Room boundaries in backup")
            return False
            
        # Extract the War Room implementation
        war_room_code = '\n'.join(backup_lines[war_room_start:war_room_end])
        print(f"✅ Extracted {war_room_end - war_room_start} lines of War Room code")
        
        # Read current webapp file
        with open('/root/HydraX-v2/webapp_server_optimized.py', 'r') as f:
            current_content = f.read()
            current_lines = current_content.split('\n')
        
        # Find the current War Room placeholder
        current_start = None
        current_end = None
        
        for i, line in enumerate(current_lines):
            if "@app.route('/me')" in line:
                # Look back to find any comment lines before the route
                actual_start = i
                while actual_start > 0 and current_lines[actual_start-1].strip().startswith('#'):
                    actual_start -= 1
                current_start = actual_start
                print(f"Found current War Room at line {i+1}")
            elif current_start is not None and "@app.route(" in line and "/me" not in line:
                current_end = i
                print(f"Found next route at line {i+1}")
                break
        
        if current_start is None:
            print("❌ Could not find current War Room location")
            return False
            
        if current_end is None:
            current_end = len(current_lines)
            
        # Replace the placeholder with the full implementation
        new_lines = (
            current_lines[:current_start] + 
            war_room_code.split('\n') + 
            current_lines[current_end:]
        )
        
        # Write the restored file
        with open('/root/HydraX-v2/webapp_server_optimized.py', 'w') as f:
            f.write('\n'.join(new_lines))
        
        print("✅ War Room implementation restored!")
        print("📋 Features restored:")
        print("  - Military callsigns and animated rank badges")
        print("  - Live performance dashboard with real stats")
        print("  - Kill cards showing recent winning trades")
        print("  - 12 achievement badges with progress tracking")
        print("  - Squad command center with referral system")
        print("  - Social sharing to Facebook, Twitter, Instagram")
        print("  - 30-second auto-refresh with API integration")
        print("  - Mobile-responsive design")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git command failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = restore_war_room()
    sys.exit(0 if success else 1)