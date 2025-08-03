#!/usr/bin/env python3
"""
Test script for CORE signal integration
Tests the complete Stage 1 + Stage 2 pipeline
"""

import zmq
import json
import time
from datetime import datetime

def test_core_signal_delivery():
    """
    Test sending a CORE signal and verify bot receives it
    """
    
    print("🧪 Testing CORE Signal Integration")
    print("=" * 50)
    
    # Set up ZMQ publisher (simulating core_filter.py)
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://127.0.0.1:5556")
    
    # Give ZMQ time to establish connection
    print("⏳ Waiting for ZMQ connection to establish...")
    time.sleep(2)
    
    # Create test CORE signal
    test_signal = {
        "uuid": f"test-btc-mission-{int(time.time())}",
        "symbol": "BTCUSD",
        "entry": 67245.50,
        "sl": 66245.50,
        "tp": 69245.50,
        "pattern": "Test Sweep Reversal",
        "score": 78,
        "xp": 160,
        "timestamp": datetime.now().isoformat(),
        "engine": "CORE",
        "type": "CRYPTO_ASSAULT",
        "risk_reward": 2.0
    }
    
    print("📤 Sending test CORE signal:")
    print(json.dumps(test_signal, indent=2))
    
    # Send the signal
    message = f"CORE_SIGNAL {json.dumps(test_signal)}"
    publisher.send_string(message)
    
    print("✅ Signal sent! Check bot logs for delivery confirmation.")
    print("📱 Expected Telegram message format:")
    print("🔥 *C.O.R.E. SIGNAL: BTCUSD*")
    print("🕒 Test Sweep Reversal – Score: 78/100")
    print("[📄 Mission Brief] button")
    
    # Cleanup
    publisher.close()
    context.term()

def verify_components():
    """
    Verify all components are ready
    """
    print("\n🔍 Component Verification")
    print("-" * 30)
    
    # Check if core_filter.py exists
    import os
    if os.path.exists("/root/HydraX-v2/core_filter.py"):
        print("✅ core_filter.py - Present")
    else:
        print("❌ core_filter.py - Missing")
    
    # Check if bot has ZMQ support
    try:
        import zmq
        print("✅ ZMQ library - Available")
    except ImportError:
        print("❌ ZMQ library - Missing (install: pip install pyzmq)")
    
    # Check logs directory
    log_dir = "/root/HydraX-v2/logs"
    if os.path.exists(log_dir):
        print("✅ Logs directory - Present")
    else:
        print("⚠️ Logs directory - Will be created")
        os.makedirs(log_dir, exist_ok=True)
    
    print("\n📋 Integration Status:")
    print("  🎯 Stage 1: core_filter.py signal generation")
    print("  🎯 Stage 2: Telegram DM routing with eligibility")
    print("  📱 Message format: 2-line + mission brief button")
    print("  📊 Logging: core_dm_log.jsonl")

if __name__ == "__main__":
    print("🚀 BITTEN C.O.R.E. Integration Test")
    print("Testing Stage 1 + Stage 2 pipeline")
    print()
    
    verify_components()
    
    print("\n" + "="*50)
    print("Ready to test signal delivery!")
    print("1. Make sure bitten_production_bot.py is running")
    print("2. Press Enter to send test signal")
    input()
    
    test_core_signal_delivery()
    
    print("\n📋 Next Steps:")
    print("- Check bot logs for CORE signal processing")
    print("- Verify Telegram message delivery")
    print("- Check /root/HydraX-v2/logs/core_dm_log.jsonl for delivery log")
    print("- Ready for Stage 3: /givecrypto admin command")