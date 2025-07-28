#!/usr/bin/env python3
"""
Launch script for Real Data Validation
Tests production engine against real market data
NEVER affects production - completely isolated
"""

import sys
import os
import subprocess

def main():
    print("🧪 REAL DATA VALIDATION LAUNCHER")
    print("=" * 50)
    print()
    print("🎯 PURPOSE: Test production engine against REAL historical data")
    print("🛡️ SAFETY: Completely isolated - never affects production")
    print("📊 DATA: Real MT5 historical prices + spreads + execution")
    print("🔬 OUTPUT: Mathematical integrity report")
    print()
    
    # Check if MT5 is available
    try:
        import MetaTrader5 as mt5
        print("✅ MetaTrader5 library available")
    except ImportError:
        print("❌ MetaTrader5 library not available")
        print("💡 Install with: pip install MetaTrader5")
        return False
    
    # Check if testing engine exists
    if not os.path.exists('/root/HydraX-v2/apex_testing_v6_real_data.py'):
        print("❌ Testing engine not found")
        return False
    
    print("✅ Testing engine available")
    
    # Check if validator exists
    if not os.path.exists('/root/HydraX-v2/apex_real_data_validator.py'):
        print("❌ Real data validator not found")
        return False
    
    print("✅ Real data validator available")
    
    print()
    print("🚀 STARTING REAL DATA VALIDATION...")
    print("📊 This will test the engine against 30 days of real market data")
    print("⏱️ Expected runtime: 2-5 minutes")
    print()
    
    try:
        # Run the validation
        result = subprocess.run([
            sys.executable, 
            '/root/HydraX-v2/apex_real_data_validator.py'
        ], capture_output=True, text=True, cwd='/root/HydraX-v2')
        
        print("📋 VALIDATION OUTPUT:")
        print("=" * 30)
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ WARNINGS/ERRORS:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ VALIDATION COMPLETED SUCCESSFULLY")
            print()
            print("📄 Check the full report at:")
            print("   /root/HydraX-v2/apex_mathematical_integrity_report.txt")
        else:
            print("❌ VALIDATION FAILED")
            print(f"Exit code: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error running validation: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)