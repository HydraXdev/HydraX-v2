#!/usr/bin/env python3
"""
Automatic cleanup runner - no user input required
"""

import sys
sys.path.insert(0, '/root/HydraX-v2')

from comprehensive_cleanup_plan import BittenSystemCleaner

def main():
    cleaner = BittenSystemCleaner()
    
    print("🧹 RUNNING AUTOMATIC BITTEN SYSTEM CLEANUP")
    print("=" * 60)
    
    # Run cleanup automatically
    manifest = cleaner.run_comprehensive_cleanup(dry_run=False)
    
    print("\n✅ AUTOMATIC CLEANUP COMPLETED")
    
    return manifest

if __name__ == "__main__":
    main()