#!/usr/bin/env python3
"""
Debug Proven Winner Engine to see why signals are filtered out
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys

sys.path.append('/root/HydraX-v2')

from bitten.core.bitten_proven_winner_engine import create_proven_winner_engine

# Simple test data generation
def create_simple_test_data():
    """Create simple test data that should generate signals"""
    
    mt5_data = {}
    
    # Simple trending data for USDJPY (proven performer)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    
    # Create strong uptrend for USDJPY
    base_price = 149.50
    trend_increment = 0.05  # Strong trend
    
    closes = []
    for i in range(100):
        price = base_price + (i * trend_increment) + np.random.randn() * 0.02
        closes.append(price)
    
    opens = [closes[0]] + closes[:-1]
    highs = [c + abs(np.random.randn() * 0.03) for c in closes]
    lows = [c - abs(np.random.randn() * 0.03) for c in closes]
    volumes = [15000 + np.random.randint(-2000, 2000) for _ in range(100)]
    
    mt5_data['USDJPY'] = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    }, index=dates)
    
    print(f"Generated USDJPY data: {closes[0]:.2f} -> {closes[-1]:.2f} (trend: {closes[-1] - closes[0]:.2f})")
    
    return mt5_data

def debug_signal_generation():
    """Debug the signal generation process"""
    
    print("🔍 DEBUGGING PROVEN WINNER ENGINE")
    print("="*50)
    
    # Create engine
    engine = create_proven_winner_engine()
    
    # Create simple test data
    mt5_data = create_simple_test_data()
    
    # Debug step by step
    current_time = datetime(2024, 1, 1, 14, 0)
    
    print(f"\n📊 Testing JPY Excellence model for USDJPY...")
    
    # Test JPY signals directly
    jpy_signals = engine._generate_jpy_excellence_signals(mt5_data, current_time)
    print(f"JPY Excellence generated: {len(jpy_signals)} signals")
    
    for signal in jpy_signals:
        print(f"  - {signal['type']} {signal['pair']} {signal['direction']}: {signal['tcs']:.1f}% TCS")
        print(f"    Risk-Eff: {signal.get('risk_efficiency', 'Not calculated')}")
        print(f"    Reasoning: {signal['reasoning']}")
    
    # Test risk-efficiency filtering
    print(f"\n⚡ Testing risk-efficiency filtering...")
    filtered_signals = engine._apply_risk_efficiency_filter(jpy_signals)
    print(f"After filtering: {len(filtered_signals)} signals")
    
    if len(jpy_signals) > len(filtered_signals):
        print(f"❌ {len(jpy_signals) - len(filtered_signals)} signals were filtered out!")
        
        # Show what was filtered
        for signal in jpy_signals:
            if signal not in filtered_signals:
                eff = signal.get('risk_efficiency', 0)
                min_eff = engine.config['risk_efficiency']['rapid_min_efficiency'] if signal['type'] == 'RAPID_ASSAULT' else engine.config['risk_efficiency']['sniper_min_efficiency']
                print(f"  Filtered: {signal['pair']} - Risk-Eff {eff:.2f} < {min_eff:.2f} required")
    
    # Test full generation
    print(f"\n🔄 Testing full signal generation...")
    all_signals = engine.generate_signals(mt5_data, current_time)
    print(f"Final signals: {len(all_signals)}")
    
    # Show configuration
    print(f"\n🔧 ENGINE CONFIGURATION:")
    config = engine.config
    print(f"JPY RAPID TCS: {config['quality_thresholds']['jpy_rapid_tcs']}%")
    print(f"JPY SNIPER TCS: {config['quality_thresholds']['jpy_sniper_tcs']}%")
    print(f"Min Risk-Efficiency RAPID: {config['risk_efficiency']['rapid_min_efficiency']}")
    print(f"Min Risk-Efficiency SNIPER: {config['risk_efficiency']['sniper_min_efficiency']}")
    
    return all_signals

if __name__ == "__main__":
    signals = debug_signal_generation()
    print(f"\n🏁 DEBUG COMPLETE: {len(signals)} final signals")