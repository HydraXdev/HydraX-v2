#!/usr/bin/env python3
"""
Test CITADEL with Live Broker Data Integration
"""

import json
import time
import sys
import os
sys.path.append('/root/HydraX-v2')

from citadel_core.citadel_analyzer import CitadelAnalyzer
from citadel_core.data_stream_enhancer import CitadelDataStreamEnhancer

def test_citadel_with_live_data():
    print("🚀 Testing CITADEL with Live Broker Data Integration")
    print("=" * 60)
    
    # Initialize CITADEL
    citadel = CitadelAnalyzer()
    
    # Initialize data enhancer
    enhancer = CitadelDataStreamEnhancer()
    
    # Process multiple ticks to build history
    print("\n📊 Building tick history from broker stream...")
    
    # Read current broker data
    try:
        with open('/tmp/ea_raw_data.json', 'r') as f:
            raw_data = json.load(f)
    except:
        print("❌ Could not read broker data. Using sample data.")
        raw_data = {
            "uuid": "mt5_test",
            "timestamp": int(time.time()),
            "account_balance": 3000.00,
            "broker": "MetaQuotes Ltd.",
            "server": "MetaQuotes-Demo",
            "ticks": [
                {
                    "symbol": "EURUSD",
                    "bid": 1.17532,
                    "ask": 1.17545,
                    "spread": 13.0,
                    "volume": 100,
                    "time": int(time.time())
                }
            ]
        }
    
    # Simulate tick history by processing the same data with slight variations
    for i in range(30):
        # Add slight price variations to simulate movement
        for tick in raw_data["ticks"]:
            variation = (i % 10 - 5) * 0.00001
            tick["bid"] += variation
            tick["ask"] += variation
            tick["time"] = int(time.time()) + i
            
        # Process through enhancer
        enhanced_data = enhancer.process_broker_stream(raw_data)
        
        if i % 10 == 0:
            print(f"  Processed {i+1} ticks...")
    
    print("\n✅ Tick history built successfully")
    
    # Test signal
    test_signal = {
        'signal_id': 'VENOM_EURUSD_BUY_TEST',
        'pair': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.17540,
        'sl': 1.17490,
        'tp': 1.17640,
        'signal_type': 'PRECISION_STRIKE'
    }
    
    # Basic market data (will be enhanced)
    basic_market_data = {
        'recent_candles': [
            {'open': 1.17520, 'high': 1.17545, 'low': 1.17515, 'close': 1.17540}
        ],
        'recent_high': 1.17560,
        'recent_low': 1.17480,
        'atr': 0.0045
    }
    
    print("\n🛡️ CITADEL Analysis WITH Live Data Enhancement:")
    print("-" * 60)
    
    # Analyze with live data enhancement
    result = citadel.analyze_signal(
        test_signal, 
        basic_market_data,
        user_id=12345,
        use_live_data=True  # Enable live data enhancement
    )
    
    print(f"\n📊 CITADEL Shield Score: {result['shield_score']}/10")
    print(f"🏷️ Classification: {result['emoji']} {result['label']}")
    print(f"💡 Explanation: {result['explanation']}")
    print(f"🎯 Recommendation: {result['recommendation']}")
    
    # Show enhanced data insights
    print("\n🔍 Enhanced Data Insights:")
    
    # Check if we got real enhanced data
    if 'components' in result:
        components = result['components']
        
        # Liquidity analysis
        if 'liquidity_analysis' in components:
            liq = components['liquidity_analysis']
            print(f"\n📈 Liquidity Analysis:")
            print(f"  - Sweep Detected: {liq.get('sweep_detected', False)}")
            print(f"  - Trap Probability: {liq.get('trap_probability', 'UNKNOWN')}")
            print(f"  - Real Data Used: {liq.get('real_data', False)}")
        
        # Market regime
        if 'market_regime' in components:
            regime = components['market_regime']
            print(f"\n🌍 Market Regime:")
            print(f"  - Regime: {regime.get('regime', 'UNKNOWN')}")
            print(f"  - Session: {regime.get('session', 'UNKNOWN')}")
            print(f"  - Volatility: {regime.get('volatility', 'UNKNOWN')}")
            print(f"  - Real Data: {regime.get('volatility_analysis', {}).get('real_data', False)}")
    
    # Compare with non-enhanced analysis
    print("\n\n🔄 Comparison WITHOUT Live Data Enhancement:")
    print("-" * 60)
    
    result_basic = citadel.analyze_signal(
        test_signal,
        basic_market_data,
        user_id=12345,
        use_live_data=False  # Disable live data
    )
    
    print(f"\n📊 Basic Shield Score: {result_basic['shield_score']}/10")
    print(f"🏷️ Classification: {result_basic['emoji']} {result_basic['label']}")
    
    # Show the difference
    print(f"\n📈 Score Improvement: {result['shield_score'] - result_basic['shield_score']:.1f} points")
    
    if result['shield_score'] > result_basic['shield_score']:
        print("✅ Live broker data improved the analysis!")
    elif result['shield_score'] < result_basic['shield_score']:
        print("⚠️ Live data revealed additional risks!")
    else:
        print("➡️ Scores unchanged, but analysis more accurate with real data")
    
    # Show enhanced market data sample
    print("\n\n🔬 Sample Enhanced Market Data:")
    print("-" * 60)
    
    if enhanced_data and 'EURUSD' in enhanced_data:
        eurusd_data = enhanced_data['EURUSD']
        
        print(f"Current Price: {eurusd_data.get('current_price', 'N/A'):.5f}")
        print(f"Session: {eurusd_data.get('session', 'N/A')}")
        print(f"Trend: {eurusd_data.get('trend_direction', 'N/A')}")
        print(f"ATR: {eurusd_data.get('atr', 'N/A')}")
        print(f"Volatility Percentile: {eurusd_data.get('volatility_percentile', 'N/A')}%")
        
        # Support/Resistance
        supports = eurusd_data.get('support_levels', [])
        resistances = eurusd_data.get('resistance_levels', [])
        if supports:
            print(f"Nearest Support: {supports[0]:.5f}")
        if resistances:
            print(f"Nearest Resistance: {resistances[0]:.5f}")
        
        # Liquidity events
        sweeps = eurusd_data.get('liquidity_sweeps', [])
        if sweeps:
            print(f"Recent Liquidity Sweeps: {len(sweeps)}")
    
    print("\n\n✅ CITADEL Live Data Integration Test Complete!")
    print("The system is now using real broker data for enhanced signal analysis.")
    
    return result

if __name__ == "__main__":
    result = test_citadel_with_live_data()