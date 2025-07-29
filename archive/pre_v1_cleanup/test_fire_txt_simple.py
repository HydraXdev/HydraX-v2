#!/usr/bin/env python3
"""
Simple test to create fire.txt in the correct location for MT5 EA
"""

import json
import time
from datetime import datetime

# Test signal
test_signal = {
    "signal_id": f"TEST_{int(time.time())}",
    "symbol": "EURUSD",
    "type": "buy",
    "lot": 0.01,
    "sl": 50,
    "tp": 100,
    "comment": "Test trade from Python"
}

print("🔍 FIRE.TXT TEST UTILITY")
print("=" * 60)
print(f"Signal: {json.dumps(test_signal, indent=2)}")
print("=" * 60)

# MT5 file paths
print("\n📂 MT5 File Paths to test:")
paths = [
    "C:\\Users\\{USER}\\AppData\\Roaming\\MetaQuotes\\Terminal\\{ID}\\MQL5\\Files\\fire.txt",
    "C:\\Users\\{USER}\\AppData\\Roaming\\MetaQuotes\\Terminal\\{ID}\\MQL5\\Files\\BITTEN\\fire.txt",
    "C:\\Program Files\\MetaTrader 5\\MQL5\\Files\\fire.txt",
    "C:\\Program Files\\MetaTrader 5\\MQL5\\Files\\BITTEN\\fire.txt"
]

print("\nThe EA is looking for fire.txt in the BITTEN subdirectory.")
print("Make sure to create this file:")
print("\n1. In MT5, go to File → Open Data Folder")
print("2. Navigate to MQL5\\Files\\")
print("3. Create a folder named 'BITTEN' if it doesn't exist")
print("4. Create fire.txt inside the BITTEN folder")
print("\n5. Copy this JSON into fire.txt:")
print("-" * 60)
print(json.dumps(test_signal))
print("-" * 60)

print("\n6. Save the file and watch the Experts tab")
print("7. You should see the EA process the signal within 1 second")

print("\n📋 DEBUGGING STEPS:")
print("1. Check if the EA shows 'Checking for signals' messages")
print("2. Look for 'SIGNAL FOUND' message when file has content")
print("3. Verify the BITTEN folder exists in MQL5\\Files\\")
print("4. Make sure the EA is attached (smiley face visible)")

print("\n🔧 If still not working:")
print("- Recompile the DEBUG EA and attach it")
print("- The DEBUG EA will show exactly where it's looking")
print("- It will list all files it can see")