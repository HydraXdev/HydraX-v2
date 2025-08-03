#!/usr/bin/env python3
"""
Test signal completion simulation for truth tracker
Creates a test signal and simulates it hitting SL or TP
"""
import json
import time
from pathlib import Path

def create_test_signal():
    """Create a test signal file that truth tracker can monitor"""
    test_signal = {
        "signal_id": "TEST_TRUTH_COMPLETION_001",
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0864,
        "stop_loss": 1.0854,  # 10 pips below entry
        "take_profit": 1.0884,  # 20 pips above entry
        "tcs_score": 87.5,
        "created_at": time.time(),
        "citadel_score": 8.8,
        "ml_filter_passed": "true",
        "source": "test_completion"
    }
    
    # Save to missions folder
    missions_dir = Path("/root/HydraX-v2/missions")
    missions_dir.mkdir(exist_ok=True)
    
    signal_file = missions_dir / f"TEST_TRUTH_COMPLETION_001.json"
    with open(signal_file, 'w') as f:
        json.dump(test_signal, f, indent=2)
    
    print(f"✅ Created test signal: {signal_file}")
    return test_signal

def simulate_tp_hit():
    """Inject market data that would trigger TP"""
    import requests
    
    # Inject market data showing price hit TP level
    tp_data = {
        "uuid": "test_completion_instance",
        "broker": "test_completion_broker",
        "account_balance": 10000.0,
        "ticks": [
            {
                "symbol": "EURUSD",
                "bid": 1.0884,  # At TP level
                "ask": 1.0886,
                "spread": 2.0,
                "volume": 2000,
                "timestamp": time.time()
            }
        ]
    }
    
    try:
        response = requests.post("http://localhost:8001/market-data", json=tp_data, timeout=5)
        if response.status_code == 200:
            print("✅ Injected TP hit market data")
            return True
        else:
            print(f"❌ Failed to inject TP data: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error injecting TP data: {e}")
        return False

def check_truth_log():
    """Check if the completion was logged"""
    truth_log = Path("/root/HydraX-v2/truth_log.jsonl")
    
    if not truth_log.exists():
        print("❌ truth_log.jsonl not found")
        return False
    
    print(f"\n📝 Latest truth log entries:")
    try:
        with open(truth_log, 'r') as f:
            lines = f.readlines()
            for line in lines[-3:]:  # Last 3 entries
                if line.strip():
                    entry = json.loads(line.strip())
                    signal_id = entry.get('signal_id', 'unknown')
                    result = entry.get('result', 'unknown')
                    timestamp = entry.get('timestamp', 'unknown')
                    print(f"  {timestamp}: {signal_id} -> {result}")
    except Exception as e:
        print(f"❌ Error reading truth log: {e}")
        return False
    
    return True

def main():
    print("🧪 TRUTH TRACKER COMPLETION TEST")
    print("=" * 40)
    
    # Step 1: Create test signal
    signal = create_test_signal()
    
    # Step 2: Wait for truth tracker to pick it up
    print("\n⏳ Waiting 5 seconds for truth tracker to load signal...")
    time.sleep(5)
    
    # Step 3: Simulate TP hit
    print("\n💰 Simulating Take Profit hit...")
    if not simulate_tp_hit():
        print("❌ Failed to simulate TP hit")
        return
    
    # Step 4: Wait for completion detection
    print("\n⏳ Waiting 10 seconds for truth tracker to detect completion...")
    time.sleep(10)
    
    # Step 5: Check results
    print("\n🔍 Checking truth log for completion...")
    check_truth_log()
    
    print("\n📊 Test complete. Check if TEST_TRUTH_COMPLETION_001 appears in truth log.")

if __name__ == "__main__":
    main()