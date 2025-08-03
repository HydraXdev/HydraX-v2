#!/usr/bin/env python3
"""
Create a test fire.txt signal to verify EA is reading files
"""

import json
import time

test_signal = {
    "signal_id": f"PYTHON_TEST_{int(time.time())}",
    "symbol": "EURUSD",
    "type": "buy",
    "lot": 0.01,
    "sl": 50,
    "tp": 100,
    "comment": "Test from Python"
}

print("🔥 Creating test fire.txt signal")
print(f"📄 Signal: {json.dumps(test_signal, indent=2)}")

# Write to file - this would normally be in MT5's Files directory
with open('test_fire.txt', 'w') as f:
    json.dump(test_signal, f)

print("\n✅ Created test_fire.txt")
print("\n📋 To use in MT5:")
print("1. Copy the following JSON to your clipboard:")
print("-" * 60)
print(json.dumps(test_signal))
print("-" * 60)
print("\n2. In MT5, go to File → Open Data Folder")
print("3. Navigate to MQL5\\Files\\BITTEN\\")
print("4. Create/edit fire.txt and paste the JSON")
print("5. Save the file")
print("6. Watch the Experts tab - you should see:")
print("   - '📨 SIGNAL FOUND at BITTEN\\fire.txt!'")
print("   - Signal processing messages")
print("   - File should be cleared after processing")
print("\n7. Check trade_result.txt in the same folder for the result")