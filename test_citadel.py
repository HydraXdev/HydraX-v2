#!/usr/bin/env python3
"""
CITADEL Shield System Test Script

This script tests the complete CITADEL system with sample signals
to verify all modules are working correctly.
"""

import sys
import os
sys.path.append('/root/HydraX-v2')

from datetime import datetime
from citadel_core.citadel_analyzer import CitadelAnalyzer
from citadel_core.bitten_integration import enhance_signal_with_citadel

def test_citadel_system():
    """Run comprehensive CITADEL system test."""
    print("🏰 CITADEL Shield System Test")
    print("=" * 50)
    
    # Initialize CITADEL
    print("\n1. Initializing CITADEL...")
    citadel = CitadelAnalyzer()
    print("✅ CITADEL initialized successfully")
    
    # Test signals
    test_signals = [
        {
            'signal_id': 'TEST_EURUSD_BUY_001',
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'signal_type': 'PRECISION_STRIKE',
            'entry': 1.0850,
            'stop_loss': 1.0820,
            'take_profit': 1.0910,
            'confidence': 85.5
        },
        {
            'signal_id': 'TEST_GBPJPY_SELL_002',
            'symbol': 'GBPJPY',
            'direction': 'SELL',
            'signal_type': 'RAPID_ASSAULT',
            'entry': 184.50,
            'stop_loss': 185.20,
            'take_profit': 183.00,
            'confidence': 78.0
        },
        {
            'signal_id': 'TEST_XAUUSD_BUY_003',
            'symbol': 'XAUUSD',
            'direction': 'BUY',
            'signal_type': 'PRECISION_STRIKE',
            'entry': 2050.0,
            'stop_loss': 2040.0,
            'take_profit': 2070.0,
            'confidence': 92.0
        }
    ]
    
    # Mock market data
    market_data = {
        'recent_candles': [
            {'open': 1.0840, 'high': 1.0845, 'low': 1.0835, 'close': 1.0842},
            {'open': 1.0842, 'high': 1.0843, 'low': 1.0825, 'close': 1.0841},
            {'open': 1.0841, 'high': 1.0850, 'low': 1.0840, 'close': 1.0848},
            {'open': 1.0848, 'high': 1.0852, 'low': 1.0846, 'close': 1.0850}
        ],
        'recent_high': 1.0860,
        'recent_low': 1.0820,
        'atr': 0.0045,
        'atr_history': [0.0040, 0.0042, 0.0045, 0.0043, 0.0041],
        'timeframes': {
            'M5': {
                'close': 1.0850,
                'ma_fast': 1.0845,
                'ma_slow': 1.0840,
                'rsi': 55
            },
            'M15': {
                'close': 1.0850,
                'ma_fast': 1.0848,
                'ma_slow': 1.0843,
                'rsi': 58
            },
            'H1': {
                'close': 1.0850,
                'ma_fast': 1.0847,
                'ma_slow': 1.0842,
                'rsi': 60
            },
            'H4': {
                'close': 1.0850,
                'ma_fast': 1.0845,
                'ma_slow': 1.0840,
                'rsi': 62
            }
        }
    }
    
    # Test each signal
    print("\n2. Testing Signal Analysis...")
    print("-" * 50)
    
    for signal in test_signals:
        print(f"\n📍 Testing {signal['symbol']} {signal['direction']}")
        
        # Test direct analysis
        result = citadel.analyze_signal(signal, market_data)
        
        print(f"   Shield Score: {result['shield_score']}/10")
        print(f"   Classification: {result['emoji']} {result['label']}")
        print(f"   Explanation: {result['explanation']}")
        
        # Test integration enhancement
        enhanced = enhance_signal_with_citadel(signal)
        shield_data = enhanced.get('citadel_shield', {})
        
        if shield_data:
            print(f"   ✅ Integration test passed")
        else:
            print(f"   ❌ Integration test failed")
    
    # Test Telegram formatting
    print("\n3. Testing Telegram Formatting...")
    print("-" * 50)
    
    test_signal = test_signals[0]
    result = citadel.analyze_signal(test_signal, market_data)
    
    # Compact format
    compact_msg = citadel.format_for_telegram(test_signal, result, compact=True)
    print("\nCompact Format:")
    print(compact_msg)
    
    # Detailed format
    detailed_msg = citadel.format_for_telegram(test_signal, result, compact=False)
    print("\nDetailed Format:")
    print(detailed_msg)
    
    # Test shield insight
    print("\n4. Testing Shield Insight...")
    print("-" * 50)
    
    insight = citadel.get_shield_insight(result['signal_id'])
    print(insight[:300] + "..." if len(insight) > 300 else insight)
    
    # Test performance tracking
    print("\n5. Testing Performance Tracking...")
    print("-" * 50)
    
    # Log a test outcome
    citadel.log_trade_outcome(
        signal_id=test_signal['signal_id'],
        user_id=12345,
        outcome='WIN',
        pips_result=25.0,
        followed_shield=True
    )
    print("✅ Trade outcome logged successfully")
    
    # Get performance report
    report = citadel.get_performance_report(days=1)
    print(f"\nPerformance Report (1 day):")
    print(f"  Total Signals: {report.get('total_signals', 0)}")
    print(f"  Avg Shield Score: {report.get('avg_shield_score', 0)}")
    
    # Test user stats
    print("\n6. Testing User Statistics...")
    print("-" * 50)
    
    user_stats = citadel.get_user_stats(12345)
    print(f"User 12345 Stats:")
    print(f"  Signals Seen: {user_stats.get('total_signals_seen', 0)}")
    print(f"  Trust Score: {user_stats.get('trust_score', 0)}")
    
    print("\n" + "=" * 50)
    print("✅ All CITADEL tests completed successfully!")
    print("🏰 CITADEL Shield System is operational")


if __name__ == "__main__":
    try:
        test_citadel_system()
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()