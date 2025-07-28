#!/usr/bin/env python3
"""
Debug VENOM signal generation to see why no signals are produced
"""

import sys
from datetime import datetime

# Add paths for imports
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

from apex_venom_v7_with_smart_timer import ApexVenomV7WithTimer

def debug_signal_generation():
    """Debug signal generation step by step"""
    
    print("🐍 Debug VENOM Signal Generation")
    print("=" * 50)
    
    # Initialize VENOM
    venom = ApexVenomV7WithTimer()
    
    # Try to generate signals for different pairs
    test_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
    current_time = datetime.now()
    
    for pair in test_pairs:
        print(f"\n🎯 Testing {pair}:")
        
        # Try base signal generation first
        print("   - Attempting base signal generation...")
        base_signal = venom.generate_venom_signal(pair, current_time)
        
        if base_signal:
            print(f"   ✅ Base signal generated: {base_signal['signal_id']}")
            print(f"      Confidence: {base_signal['confidence']}%")
            print(f"      Quality: {base_signal['quality']}")
            print(f"      Signal Type: {base_signal['signal_type']}")
            
            # Try with timer integration
            print("   - Adding timer integration...")
            timer_signal = venom.generate_venom_signal_with_timer(pair, current_time)
            
            if timer_signal:
                print(f"   ✅ Timer signal generated: {timer_signal['signal_id']}")
                print(f"      Timer: {timer_signal.get('countdown_minutes', 'N/A')} minutes")
                print(f"      Has Smart Timer: {timer_signal.get('has_smart_timer', False)}")
            else:
                print("   ❌ Timer integration failed")
        else:
            print("   ❌ Base signal generation failed")
            
            # Debug why it failed
            print("   🔍 Debugging generation failure...")
            
            # Check market data generation
            market_data = venom.generate_realistic_market_data(pair, current_time)
            print(f"      Market data: Session={market_data.get('session', 'N/A')}")
            
            # Check regime detection
            regime = venom.detect_market_regime(pair, current_time)
            print(f"      Market regime: {regime.value}")
            
            # Check confidence calculation
            confidence = venom.calculate_venom_confidence(pair, market_data, regime)
            print(f"      Calculated confidence: {confidence}%")
            
            # Check quality determination
            quality = venom.determine_signal_quality(confidence, market_data.get('session', 'ASIAN'), regime)
            print(f"      Determined quality: {quality.value}")
            
            # Check should_generate decision
            should_generate = venom.should_generate_venom_signal(pair, confidence, quality, market_data.get('session', 'ASIAN'))
            print(f"      Should generate: {should_generate}")
            
            if not should_generate:
                print("      💡 Signal blocked by filters - confidence or quality too low")

if __name__ == "__main__":
    debug_signal_generation()