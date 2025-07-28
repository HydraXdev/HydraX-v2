#!/usr/bin/env python3
"""
Test CITADEL Enhanced Data Stream
"""

import json
import time
from citadel_core.data_stream_enhancer import CitadelDataStreamEnhancer

def test_enhanced_citadel():
    print("🚀 Testing CITADEL Enhanced Data Stream")
    
    # Create enhancer
    enhancer = CitadelDataStreamEnhancer()
    
    # Sample broker data (simulating the real stream format)
    sample_data = {
        "uuid": "mt5_test",
        "timestamp": int(time.time()),
        "account_balance": 3000.00,
        "broker": "MetaQuotes Ltd.",
        "server": "MetaQuotes-Demo",
        "ticks": [
            {
                "symbol": "EURUSD",
                "bid": 1.17527,
                "ask": 1.17539,
                "spread": 12.0,
                "volume": 100,
                "time": int(time.time())
            },
            {
                "symbol": "GBPUSD", 
                "bid": 1.34364,
                "ask": 1.34383,
                "spread": 19.0,
                "volume": 150,
                "time": int(time.time())
            }
        ]
    }
    
    # Process multiple ticks to build history
    print("📊 Building market data history...")
    for i in range(50):
        # Simulate price movement
        for tick in sample_data["ticks"]:
            # Add small random movement
            movement = (i % 10 - 5) * 0.0001  # +/- 0.5 pips
            tick["bid"] += movement
            tick["ask"] += movement
            tick["time"] = int(time.time()) + i
            tick["volume"] = 50 + (i % 20) * 10
        
        enhanced_data = enhancer.process_broker_stream(sample_data)
        
        if i % 10 == 0:
            print(f"  Processed {i+1} ticks...")
    
    print("\n🎯 Enhanced Market Intelligence Generated:")
    
    for symbol, data in enhanced_data.items():
        print(f"\n=== {symbol} ANALYSIS ===")
        print(f"Current Price: {data.get('current_price', 'N/A'):.5f}")
        print(f"Session: {data.get('session', 'N/A')}")
        print(f"Trend Direction: {data.get('trend_direction', 'N/A')}")
        print(f"Market Structure: {data.get('market_structure', 'N/A')}")
        
        # Volatility analysis
        atr = data.get('atr', 0)
        volatility_pct = data.get('volatility_percentile', 0)
        print(f"ATR (14): {atr:.5f}")
        print(f"Volatility Percentile: {volatility_pct:.1f}%")
        
        # Support/Resistance
        support = data.get('support_levels', [])
        resistance = data.get('resistance_levels', [])
        print(f"Support Levels: {[f'{level:.5f}' for level in support[:3]]}")
        print(f"Resistance Levels: {[f'{level:.5f}' for level in resistance[:3]]}")
        
        # Timeframe analysis
        tf_data = data.get('timeframes', {})
        print(f"Timeframes Available: {list(tf_data.keys())}")
        
        # Liquidity analysis
        sweeps = data.get('liquidity_sweeps', [])
        print(f"Recent Liquidity Events: {len(sweeps)}")
        
        # Volume analysis
        avg_vol = data.get('average_volume', 0)
        vol_spikes = data.get('volume_spikes', [])
        print(f"Average Volume: {avg_vol:.0f}")
        print(f"Volume Spikes: {len(vol_spikes)}")
        
        # Confluence zones
        confluences = data.get('confluence_zones', [])
        print(f"Confluence Zones: {len(confluences)}")
        if confluences:
            top_confluence = confluences[0]
            print(f"  Top Zone: {top_confluence['price']:.5f} (Strength: {top_confluence['strength']})")
        
        # Spread analysis
        spread_analysis = data.get('spread_analysis', {})
        if spread_analysis:
            print(f"Spread Analysis:")
            print(f"  Current: {spread_analysis.get('current_spread', 'N/A')}")
            print(f"  Average: {spread_analysis.get('average_spread', 'N/A'):.1f}")
            print(f"  Trend: {spread_analysis.get('spread_trend', 'N/A')}")
        
        # Momentum
        momentum = data.get('price_momentum', {})
        if momentum:
            print(f"Price Momentum:")
            print(f"  Direction: {momentum.get('momentum_direction', 'N/A')}")
            print(f"  Strength: {momentum.get('momentum_strength', 0):.3f}%")
            print(f"  Velocity: {momentum.get('price_velocity', 0):.3f}%")
        
        print("-" * 50)
    
    return enhanced_data

if __name__ == "__main__":
    enhanced_data = test_enhanced_citadel()
    
    print("\n🛡️ CITADEL Data Enhancement Complete!")
    print(f"Enhanced data available for {len(enhanced_data)} symbols")
    print("Ready for institutional-grade signal analysis!")