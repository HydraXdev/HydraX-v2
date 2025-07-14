#!/usr/bin/env python3
"""
Simple starter for BITTEN Bot with Intel Command Center
"""

import subprocess
import sys

def main():
    print("🎯 STARTING BITTEN BOT WITH FULL MENU SYSTEM")
    print("=" * 50)
    
    try:
        # Kill any existing bots
        subprocess.run("pkill -f BITTEN_BOT_WITH_INTEL_CENTER", shell=True)
        
        # Start the bot
        subprocess.run([
            sys.executable, 
            "/root/HydraX-v2/BITTEN_BOT_WITH_INTEL_CENTER.py"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()