#!/usr/bin/env python3
"""Test gold signal logging functionality"""

import sys
import json
sys.path.append('/root/HydraX-v2')

from src.bitten_core.bitten_core import BittenCore
from src.bitten_core.user_registry_manager import get_user_registry_manager

def test_gold_signal_logging():
    """Test the gold signal logging system"""
    
    print("🧪 Testing Gold Signal Logging")
    print("=" * 60)
    
    # Initialize BittenCore
    core = BittenCore()
    
    # Create test gold signal
    test_signal = {
        'signal_id': 'TEST_GOLD_LOG_001',
        'symbol': 'XAUUSD',
        'direction': 'BUY',
        'entry_price': 2415.50,
        'stop_loss': 2408.00,
        'take_profit': 2430.50,
        'risk_reward': 2.0,
        'signal_type': 'PRECISION_STRIKE',
        'confidence': 88,
        'pattern': 'LIQUIDITY_SWEEP_REVERSAL',
        'citadel_score': 8.7,
        'expires_at': '2025-08-01T23:00:00Z'
    }
    
    # Test user info
    test_user_info = {
        'user_id': 'goldtest',
        'telegram_id': '7176191872',
        'username': 'goldtrader',
        'container': 'mt5_user_7176191872',
        'user_region': 'INTL',
        'offshore_opt_in': True
    }
    
    print("\n📝 Testing _log_gold_signal_delivery method...")
    
    # Call the logging method directly
    core._log_gold_signal_delivery(
        telegram_id='7176191872',
        user_info=test_user_info,
        signal_data=test_signal,
        xp_awarded=200
    )
    
    print("✅ Logging method executed")
    
    # Check if log file was created
    import os
    log_file = "/root/HydraX-v2/logs/gold_dm_log.jsonl"
    
    if os.path.exists(log_file):
        print(f"\n✅ Log file created: {log_file}")
        
        # Read and display the last entry
        with open(log_file, 'r') as f:
            lines = f.readlines()
            if lines:
                last_entry = json.loads(lines[-1])
                print("\n📋 Last Log Entry:")
                print(json.dumps(last_entry, indent=2))
            else:
                print("❌ Log file is empty")
    else:
        print(f"❌ Log file not created at: {log_file}")
    
    print("\n" + "=" * 60)
    print("✅ Gold signal logging test complete!")
    print("\nTo view all logs, run:")
    print("  python3 view_gold_logs.py")

if __name__ == "__main__":
    test_gold_signal_logging()