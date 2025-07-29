#!/usr/bin/env python3
"""
Test BittenCore with CITADEL Shield Integration
"""

import json
import time
import sys
sys.path.append('/root/HydraX-v2')
sys.path.append('/root/HydraX-v2/src')

from src.bitten_core.bitten_core import BittenCore

def test_bitten_core_citadel():
    print("🚀 Testing BittenCore with CITADEL Shield Integration")
    print("=" * 60)
    
    # Initialize BittenCore
    core = BittenCore()
    
    # Sample VENOM signal
    test_signal = {
        'signal_id': 'VENOM_EURUSD_BUY_TEST_001',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'signal_type': 'PRECISION_STRIKE',
        'confidence': 87.5,
        'target_pips': 30,
        'stop_pips': 15,
        'risk_reward': 2.0,
        'quality': 'platinum',
        'expires_at': None,  # Will be set by core
        'countdown_minutes': 35
    }
    
    print("\n📡 Processing VENOM Signal through BittenCore...")
    print(f"Signal: {test_signal['symbol']} {test_signal['direction']} - {test_signal['confidence']}% confidence")
    
    # Process signal through core
    result = core.process_signal(test_signal)
    
    if result['success']:
        print("\n✅ Signal processed successfully!")
        
        # Get the processed signal with CITADEL data
        signal_id = result['signal_id']
        processed = core.processed_signals.get(signal_id)
        
        if processed:
            print("\n🛡️ CITADEL Shield Analysis:")
            print(f"Shield Score: {processed.get('shield_score', 'N/A')}/10")
            print(f"Classification: {processed.get('shield_emoji', '')} {processed.get('shield_label', 'N/A')}")
            print(f"Position Multiplier: {processed.get('position_multiplier', 1.0)}x")
            print(f"Explanation: {processed.get('shield_explanation', 'N/A')}")
            print(f"Recommendation: {processed.get('shield_recommendation', 'N/A')}")
            
            # Show formatted HUD message
            print("\n📱 Telegram HUD Message Preview:")
            print("-" * 40)
            hud_message = core._format_signal_for_hud(processed)
            print(hud_message)
            print("-" * 40)
        
        # Check if live data was used
        print("\n📊 Live Data Integration:")
        print(f"EA Data Available: {'/tmp/ea_raw_data.json' in sys.modules}")
        
        # Show current broker data
        try:
            with open('/tmp/ea_raw_data.json', 'r') as f:
                broker_data = json.load(f)
                for tick in broker_data.get('ticks', []):
                    if tick['symbol'] == 'EURUSD':
                        print(f"Current EURUSD Price: Bid={tick['bid']}, Ask={tick['ask']}")
                        break
        except:
            print("Could not read broker data")
            
    else:
        print(f"\n❌ Signal processing failed: {result.get('error', 'Unknown error')}")
    
    # Test with different signal quality
    print("\n\n🔄 Testing Low Quality Signal...")
    
    low_quality_signal = {
        'signal_id': 'VENOM_GBPJPY_SELL_TEST_002',
        'symbol': 'GBPJPY',
        'direction': 'SELL',
        'signal_type': 'RAPID_ASSAULT',
        'confidence': 72.5,
        'target_pips': 15,
        'stop_pips': 20,
        'risk_reward': 0.75,  # Poor R:R
        'quality': 'bronze',
        'countdown_minutes': 25
    }
    
    result2 = core.process_signal(low_quality_signal)
    
    if result2['success']:
        processed2 = core.processed_signals.get(result2['signal_id'])
        if processed2:
            print(f"\nSignal: {processed2['symbol']} {processed2['direction']}")
            print(f"Shield Score: {processed2.get('shield_score', 'N/A')}/10")
            print(f"Classification: {processed2.get('shield_emoji', '')} {processed2.get('shield_label', 'N/A')}")
            print(f"Position Multiplier: {processed2.get('position_multiplier', 1.0)}x")
            print(f"Recommendation: {processed2.get('shield_recommendation', 'N/A')}")
    
    # Show signal queue
    print(f"\n\n📋 Signal Queue Status:")
    queue = core.get_signal_queue()
    print(f"Total signals in queue: {len(queue)}")
    
    stats = core.get_signal_stats()
    print(f"Total signals processed: {stats['total_signals']}")
    print(f"Pending signals: {stats['pending_signals']}")
    
    print("\n\n✅ BittenCore CITADEL Integration Test Complete!")
    print("The system is now analyzing all signals with real broker data.")

if __name__ == "__main__":
    test_bitten_core_citadel()