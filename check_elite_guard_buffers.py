#!/usr/bin/env python3
"""
Check Elite Guard buffer status and force pattern detection
"""
import json
import time
import logging

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('buffer_check')

# Import Elite Guard to check its state
import sys
sys.path.append('/root/HydraX-v2')

try:
    # Find the running Elite Guard instance via its log
    import subprocess
    import os
    
    # Check if Elite Guard is running
    result = subprocess.run(['pgrep', '-f', 'elite_guard_with_citadel'], capture_output=True, text=True)
    if not result.stdout:
        print("❌ Elite Guard is not running!")
        sys.exit(1)
    
    pid = result.stdout.strip()
    print(f"✅ Elite Guard running (PID: {pid})")
    
    # Create a test script to inject into Elite Guard's namespace
    test_code = """
import elite_guard_with_citadel
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('buffer_test')

# Try to access the global engine instance
try:
    # Look for the engine in the module
    for name, obj in vars(elite_guard_with_citadel).items():
        if isinstance(obj, elite_guard_with_citadel.EliteGuardWithCitadel):
            engine = obj
            print(f"\\n🔍 Found engine instance: {name}")
            
            # Check buffer sizes
            print("\\n📊 Buffer Status:")
            for symbol in engine.trading_pairs:
                m1_len = len(engine.m1_data.get(symbol, []))
                m5_len = len(engine.m5_data.get(symbol, []))
                m15_len = len(engine.m15_data.get(symbol, []))
                tick_len = len(engine.tick_data.get(symbol, []))
                
                print(f"\\n{symbol}:")
                print(f"  Ticks: {tick_len}")
                print(f"  M1: {m1_len} (need 20 for liquidity sweep)")
                print(f"  M5: {m5_len} (need 30 for order block)")
                print(f"  M15: {m15_len} (need 50 for FVG)")
                
                # Force pattern detection if we have enough data
                if m1_len >= 20:
                    print(f"  Testing liquidity sweep detection...")
                    result = engine.detect_liquidity_sweep_reversal(symbol)
                    if result:
                        print(f"  ✅ PATTERN FOUND: {result}")
                    else:
                        print(f"  ❌ No liquidity sweep detected")
                        
                if m5_len >= 30:
                    print(f"  Testing order block detection...")
                    result = engine.detect_order_block_bounce(symbol)
                    if result:
                        print(f"  ✅ PATTERN FOUND: {result}")
                    else:
                        print(f"  ❌ No order block detected")
            
            # Check scan timing
            print(f"\\n⏱️ Last scan: {engine.last_scan_time}")
            print(f"📊 Signals generated: {engine.signals_generated}")
            print(f"🎯 Daily signals: {engine.daily_signal_count}")
            
            break
    else:
        print("❌ Could not find engine instance")
        
except Exception as e:
    print(f"❌ Error accessing engine: {e}")
    import traceback
    traceback.print_exc()
"""
    
    # Write test code
    with open('/tmp/elite_buffer_test.py', 'w') as f:
        f.write(test_code)
    
    # Execute in Elite Guard's context (this won't work directly, need different approach)
    print("\n🔧 Alternative approach - checking via logs and forcing detection...")
    
    # Let's add extensive logging to Elite Guard instead
    print("\n📝 Adding debug logging to pattern detection...")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Alternative: Monitor the actual log output
print("\n📋 Checking recent Elite Guard activity...")
try:
    with subprocess.Popen(['tail', '-f', '/tmp/elite_guard_50.log'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         universal_newlines=True) as proc:
        
        print("Monitoring for 10 seconds...")
        start_time = time.time()
        buffer_info = {}
        
        while time.time() - start_time < 10:
            line = proc.stdout.readline()
            if line:
                # Look for buffer size info
                if "len(" in line or "buffer" in line or "data[" in line:
                    print(f"Buffer info: {line.strip()}")
                elif "Scanning" in line or "pattern" in line:
                    print(f"Pattern scan: {line.strip()}")
                elif "detected" in line or "found" in line:
                    print(f"Detection: {line.strip()}")
                    
        proc.terminate()
        
except Exception as e:
    print(f"Log monitoring error: {e}")

print("\n💡 To force pattern detection, we need to:")
print("1. Add debug logging to see buffer sizes")
print("2. Lower pattern detection thresholds temporarily")
print("3. Add forced test patterns")