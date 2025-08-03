#!/usr/bin/env python3
"""
Debug VENOM engine to understand why it's not generating signals
"""

import sys
import numpy as np
from datetime import datetime, timedelta
sys.path.append('/root/HydraX-v2')
from venom_engine import VenomTradingEngine

def debug_venom():
    """Debug VENOM signal generation"""
    print("🐍 DEBUGGING VENOM ENGINE")
    print("=" * 40)
    
    engine = VenomTradingEngine()
    
    # Create realistic market data similar to real validation
    market_data = []
    base_price = 1.0850
    
    # Generate 60 data points (sufficient for analysis)
    for i in range(60):
        # Add some trend and volatility
        trend = 0.0001 * np.sin(i * 0.1)  # Gentle trend
        noise = np.random.normal(0, 0.0001)  # Market noise
        base_price += trend + noise
        
        market_data.append({
            'timestamp': int(datetime.now().timestamp()) + i * 3600,
            'open': base_price - np.random.uniform(0, 0.00005),
            'high': base_price + np.random.uniform(0.00005, 0.0002),
            'low': base_price - np.random.uniform(0.00005, 0.0002),
            'close': base_price,
            'volume': np.random.randint(1000, 3000)
        })
    
    print(f"📊 Generated {len(market_data)} market data points")
    print(f"💰 Price range: {min(d['close'] for d in market_data):.5f} - {max(d['close'] for d in market_data):.5f}")
    
    # Analyze market structure
    structure = engine.analyze_market_structure(market_data)
    print(f"\n🔍 MARKET STRUCTURE ANALYSIS:")
    print(f"   Regime: {structure.regime}")
    print(f"   Support: {structure.support_level:.5f}")
    print(f"   Resistance: {structure.resistance_level:.5f}")
    print(f"   Trend Strength: {structure.trend_strength:.6f}")
    print(f"   Volatility Percentile: {structure.volatility_percentile:.1f}%")
    print(f"   Structure Break Probability: {structure.structure_break_probability:.1%}")
    print(f"   Liquidity Zones: {len(structure.liquidity_zones)}")
    
    # Check thresholds
    print(f"\n⚖️ THRESHOLD CHECKS:")
    print(f"   Structure Break Prob >= 0.45: {structure.structure_break_probability >= 0.45}")
    
    if structure.structure_break_probability < 0.45:
        print("❌ FAILED: Structure break probability too low")
        print("🔧 SOLUTION: Lower threshold or improve probability calculation")
        return False
    
    # Test signal direction
    current_price = market_data[-1]['close']
    direction, confidence = engine._determine_signal_direction(structure, current_price)
    
    print(f"\n🎯 SIGNAL DIRECTION ANALYSIS:")
    print(f"   Direction: {direction}")
    print(f"   Confidence: {confidence:.1f}%")
    print(f"   Min Confidence Threshold: {engine.signal_thresholds['min_confidence']}")
    print(f"   Confidence >= Threshold: {confidence >= engine.signal_thresholds['min_confidence']}")
    
    if not direction or confidence < engine.signal_thresholds['min_confidence']:
        print("❌ FAILED: Confidence too low or no direction")
        print("🔧 SOLUTION: Improve confidence calculation or lower threshold")
        return False
    
    # Test entry levels
    entry_levels = engine._calculate_entry_levels(direction, structure, current_price)
    
    print(f"\n📊 ENTRY LEVELS ANALYSIS:")
    if entry_levels:
        print(f"   Entry: {entry_levels['entry']:.5f}")
        print(f"   Stop Loss: {entry_levels['stop_loss']:.5f}")
        print(f"   Take Profit 1: {entry_levels['tp1']:.5f}")
        print(f"   Risk: {entry_levels['risk']:.5f}")
        print(f"   Reward: {entry_levels['reward']:.5f}")
        print(f"   Risk:Reward: 1:{entry_levels['reward']/entry_levels['risk']:.2f}")
        print(f"   Min R:R Threshold: {engine.signal_thresholds['min_risk_reward']}")
        
        risk_reward = entry_levels['reward'] / entry_levels['risk']
        print(f"   R:R >= Threshold: {risk_reward >= engine.signal_thresholds['min_risk_reward']}")
        
        if risk_reward < engine.signal_thresholds['min_risk_reward']:
            print("❌ FAILED: Risk:reward ratio too low")
            print("🔧 SOLUTION: Improve entry level calculation or lower R:R requirement")
            return False
    else:
        print("❌ FAILED: No valid entry levels calculated")
        print("🔧 SOLUTION: Fix entry level calculation logic")
        return False
    
    # Generate final signal
    signal = engine.generate_signal("EURUSD", market_data)
    
    print(f"\n🎯 FINAL SIGNAL:")
    if signal:
        print(f"✅ Signal generated successfully!")
        print(f"   Symbol: {signal.symbol}")
        print(f"   Direction: {signal.direction}")
        print(f"   Confidence: {signal.confidence:.1f}%")
        print(f"   Strength: {signal.strength.value}")
        print(f"   Risk:Reward: 1:{signal.risk_reward_ratio:.2f}")
        return True
    else:
        print("❌ No signal generated - check logic above")
        return False

if __name__ == "__main__":
    success = debug_venom()
    exit(0 if success else 1)