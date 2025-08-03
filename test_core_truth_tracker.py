#!/usr/bin/env python3
"""
Test C.O.R.E. Truth Tracker Integration
Demonstrates how crypto signals are tracked separately from forex
"""

import json
import time
from datetime import datetime
from core_truth_integration import CoreTruthIntegration

def test_core_integration():
    """Test the complete C.O.R.E. truth tracking integration"""
    
    print("🧪 TESTING C.O.R.E. TRUTH TRACKER INTEGRATION")
    print("=" * 60)
    
    # Create integration instance
    integration = CoreTruthIntegration()
    
    # Test signal similar to what core_filter.py generates
    test_signal = {
        "uuid": f"test-btc-mission-{int(time.time())}",
        "symbol": "BTCUSD",
        "entry": 67245.50,
        "sl": 66245.50,  # $1000 stop loss
        "tp": 69245.50,  # $2000 take profit (2:1 R:R)
        "pattern": "Test Sweep Reversal",
        "score": 78,
        "xp": 160,
        "timestamp": datetime.now().isoformat(),
        "engine": "CORE",
        "type": "CRYPTO_ASSAULT",
        "risk_reward": 2.0
    }
    
    print("📤 Testing C.O.R.E. signal integration:")
    print(f"   Signal ID: {test_signal['uuid']}")
    print(f"   Symbol: {test_signal['symbol']}")
    print(f"   Entry: ${test_signal['entry']}")
    print(f"   Stop Loss: ${test_signal['sl']} (-$1000)")
    print(f"   Take Profit: ${test_signal['tp']} (+$2000)")
    print(f"   Score: {test_signal['score']}/100")
    print()
    
    # Add signal to truth tracker
    success = integration.track_core_signal(test_signal)
    
    if success:
        print("✅ C.O.R.E. signal successfully added to truth tracker")
        
        # Get stats
        stats = integration.get_crypto_stats()
        print(f"📊 Current Tracking Stats:")
        print(f"   Crypto signals active: {stats.get('crypto_active_signals', 0)}")
        print(f"   Total signals active: {stats.get('total_active_signals', 0)}")
        print(f"   Crypto log file: {stats.get('crypto_log_path', 'N/A')}")
        print(f"   Forex log file: {stats.get('forex_log_path', 'N/A')}")
        
    else:
        print("❌ Failed to add C.O.R.E. signal to truth tracker")
        return False
    
    print()
    print("🔍 Key Features of C.O.R.E. Truth Integration:")
    print("   • Separate crypto_truth_log.jsonl file (prevents forex data skewing)")
    print("   • Dollar-based P&L tracking (not pips)")
    print("   • Real-time market data monitoring for BTCUSD")
    print("   • Automatic WIN/LOSS detection based on SL/TP")
    print("   • Complete audit trail with metadata")
    print()
    
    print("📋 Available CLI Commands:")
    print("   python3 truth_tracker.py --inspect-latest 5 --type crypto")
    print("   python3 truth_tracker.py --inspect-latest 10 --type both")
    print("   python3 core_truth_integration.py  # Test integration")
    print()
    
    print("🎯 Integration Points:")
    print("   1. core_filter.py generates signal")
    print("   2. track_core_signal(signal_data) adds to tracker")
    print("   3. Truth tracker monitors BTCUSD market data")
    print("   4. Results logged to crypto_truth_log.jsonl")
    print("   5. Separate reporting keeps crypto/forex data clean")
    
    return True

def demonstrate_cli_usage():
    """Show CLI usage examples"""
    print("\n" + "=" * 60)
    print("📋 CLI USAGE EXAMPLES")
    print("=" * 60)
    
    print("# View latest crypto signals only:")
    print("python3 truth_tracker.py --inspect-latest 3 --type crypto")
    print()
    
    print("# View latest forex signals only:")
    print("python3 truth_tracker.py --inspect-latest 5 --type forex")
    print()
    
    print("# View combined forex + crypto signals:")
    print("python3 truth_tracker.py --inspect-latest 10 --type both")
    print()
    
    print("# Start truth tracker daemon (monitors both types):")
    print("python3 truth_tracker.py")
    print()
    
    print("📊 Example Output Format:")
    print("Signal ID                      Type   Symbol   Dir  Result   TCS    CITADEL  ML Filter  Pips/$     Runtime    Source")
    print("test-btc-mission-1234567       CRYPTO BTCUSD   BUY  ✅ WIN   78.0   0.0      N/A        +$2000     45.2m      CORE")

if __name__ == "__main__":
    success = test_core_integration()
    
    if success:
        demonstrate_cli_usage()
        print("\n✅ C.O.R.E. Truth Tracker Integration test completed successfully!")
    else:
        print("\n❌ Integration test failed!")