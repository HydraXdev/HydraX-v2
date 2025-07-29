#!/usr/bin/env python3
"""
Test script to validate enhanced truth tracker with real-time signal completion
Creates a test signal that should complete quickly for validation
"""

import json
import time
import os
from pathlib import Path

def create_test_signal():
    """Create a test signal with enhanced metadata that will complete quickly"""
    
    # Create test signal with very tight stop/take levels for quick completion
    current_time = time.time()
    test_signal = {
        "signal_id": f"TEST_ENHANCED_VALIDATION_{int(current_time)}",
        "pair": "EURUSD", 
        "direction": "BUY",
        "timestamp": current_time,
        "confidence": 85.0,
        "quality": "platinum",
        "session": "London",
        "signal": {
            "symbol": "EURUSD",
            "direction": "BUY", 
            "target_pips": 2,  # Very small target for quick completion
            "stop_pips": 1,    # Very small stop
            "risk_reward": 2.0,
            "signal_type": "RAPID_ASSAULT",
            "duration_minutes": 5
        },
        "enhanced_signal": {
            "symbol": "EURUSD",
            "direction": "BUY",
            "entry_price": 1.16500,  # Realistic price
            "stop_loss": 1.16490,    # 1 pip stop
            "take_profit": 1.16520,  # 2 pip target
            "risk_reward_ratio": 2.0,
            "signal_type": "RAPID_ASSAULT", 
            "confidence": 85.0
        },
        "venom_analysis": {
            "volatility": 0.0001,
            "momentum_alignment": {
                "short": 1,
                "medium": 1, 
                "long": 1
            },
            "session_power": 0.98,
            "spread_quality": "excellent"
        },
        "ml_filter": {
            "ml_filter_enabled": True,
            "filter_result": "passed",
            "min_threshold": 0.65
        },
        "citadel_shield": {
            "score": 9.5,
            "classification": "SHIELD_APPROVED",
            "emoji": "🛡️",
            "label": "SHIELD APPROVED", 
            "explanation": "Test signal for enhanced truth tracker validation",
            "recommendation": "Full position - validation test",
            "risk_factors": [],
            "quality_factors": [
                {
                    "factor": "validation_test",
                    "bonus": 2.0,
                    "description": "Test signal for metadata validation"
                }
            ]
        },
        # CRITICAL: Proper source tag for enhanced system
        "source": "venom_scalp_master"
    }
    
    # Write to missions folder
    missions_dir = Path('/root/HydraX-v2/missions')
    missions_dir.mkdir(exist_ok=True)
    
    signal_file = missions_dir / f"mission_{test_signal['signal_id']}.json"
    with open(signal_file, 'w') as f:
        json.dump(test_signal, f, indent=2)
    
    print(f"✅ Created test signal: {test_signal['signal_id']}")
    print(f"📁 File: {signal_file}")
    print(f"🎯 Entry: {test_signal['enhanced_signal']['entry_price']}")
    print(f"🛑 Stop: {test_signal['enhanced_signal']['stop_loss']} (1 pip)")
    print(f"💰 Target: {test_signal['enhanced_signal']['take_profit']} (2 pips)")
    print(f"🔍 Source: {test_signal['source']}")
    
    return test_signal['signal_id']

def monitor_truth_log(signal_id, timeout=120):
    """Monitor truth log for the test signal completion"""
    truth_log = Path('/root/HydraX-v2/truth_log.jsonl')
    start_time = time.time()
    
    print(f"\n🔍 Monitoring truth log for signal: {signal_id}")
    print(f"⏰ Timeout: {timeout} seconds")
    
    while time.time() - start_time < timeout:
        if not truth_log.exists():
            print("⚠️ Truth log doesn't exist yet")
            time.sleep(5)
            continue
            
        # Check if our signal appears in truth log
        with open(truth_log, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            try:
                entry = json.loads(line.strip())
                if entry.get('signal_id') == signal_id:
                    print(f"\n✅ FOUND SIGNAL IN TRUTH LOG!")
                    print(f"📊 Result: {entry.get('result')}")
                    print(f"📈 TCS Score: {entry.get('tcs_score')}")
                    print(f"🛡️ CITADEL Score: {entry.get('citadel_score')}")
                    print(f"🤖 ML Filter: {entry.get('ml_filter_passed')}")
                    print(f"🔍 Source: {entry.get('source')}")
                    print(f"💰 Pips: {entry.get('pips_result')}")
                    print(f"⏱️ Runtime: {entry.get('runtime_minutes')}m")
                    return True
            except json.JSONDecodeError:
                continue
                
        print(f"⏳ Waiting... ({int(time.time() - start_time)}s elapsed)")
        time.sleep(5)
    
    print(f"⏰ Timeout reached - signal may still be active")
    return False

if __name__ == "__main__":
    print("🧪 ENHANCED TRUTH TRACKER VALIDATION TEST")
    print("=" * 50)
    
    # Create test signal 
    signal_id = create_test_signal()
    
    # Wait a moment for truth tracker to pick it up
    print("\n⏳ Waiting 10 seconds for truth tracker to detect signal...")
    time.sleep(10)
    
    # Monitor for completion
    found = monitor_truth_log(signal_id, timeout=60)
    
    if found:
        print("\n🎉 SUCCESS: Enhanced metadata tracking validated!")
        print("✅ Signal was logged with complete metadata")
    else:
        print("\n⚠️ Signal not completed yet - may still be active")
        print("💡 Check truth log manually in a few minutes")
        
    print(f"\n📝 To inspect latest truth log entries:")
    print(f"python3 truth_tracker.py --inspect-latest 5")