#!/usr/bin/env python3
"""
Cross-Asset Correlation System Example
Demonstrates how to use the correlation system for market analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
import time
from src.bitten_core.strategies.cross_asset_correlation import (
    CrossAssetCorrelationSystem,
    AssetData,
    AssetClass
)

def generate_market_data():
    """Generate simulated market data for demonstration"""
    
    # Base prices
    base_prices = {
        # Forex
        'EURUSD': 1.0850,
        'GBPUSD': 1.2650,
        'USDJPY': 150.50,
        'USDCHF': 0.9150,
        'AUDUSD': 0.6550,
        'NZDUSD': 0.6050,
        'USDCAD': 1.3450,
        
        # Indices
        'SPX': 4500.00,
        'NDX': 15500.00,
        'DAX': 15800.00,
        'FTSE': 7500.00,
        'NKY': 32500.00,
        
        # Commodities
        'GOLD': 2050.00,
        'SILVER': 23.50,
        'OIL': 78.50,
        'COPPER': 3.85,
        'NATURAL_GAS': 2.45,
        
        # Bonds (yields)
        'US10Y': 4.25,
        'US2Y': 4.85,
        'BUND10Y': 2.45,
        'JGB10Y': 0.75,
    }
    
    # Asset class mapping
    asset_classes = {
        'EURUSD': AssetClass.FOREX,
        'GBPUSD': AssetClass.FOREX,
        'USDJPY': AssetClass.FOREX,
        'USDCHF': AssetClass.FOREX,
        'AUDUSD': AssetClass.FOREX,
        'NZDUSD': AssetClass.FOREX,
        'USDCAD': AssetClass.FOREX,
        'SPX': AssetClass.INDEX,
        'NDX': AssetClass.INDEX,
        'DAX': AssetClass.INDEX,
        'FTSE': AssetClass.INDEX,
        'NKY': AssetClass.INDEX,
        'GOLD': AssetClass.COMMODITY,
        'SILVER': AssetClass.COMMODITY,
        'OIL': AssetClass.COMMODITY,
        'COPPER': AssetClass.COMMODITY,
        'NATURAL_GAS': AssetClass.COMMODITY,
        'US10Y': AssetClass.BOND,
        'US2Y': AssetClass.BOND,
        'BUND10Y': AssetClass.BOND,
        'JGB10Y': AssetClass.BOND,
    }
    
    market_data = []
    
    for symbol, base_price in base_prices.items():
        # Add some random variation
        price = base_price * (1 + random.uniform(-0.02, 0.02))
        change_pct = random.uniform(-2.0, 2.0)
        volume = random.randint(100000, 5000000)
        
        additional_data = {}
        if symbol in ['US10Y', 'US2Y', 'BUND10Y', 'JGB10Y']:
            additional_data['yield'] = price
            
        market_data.append(AssetData(
            symbol=symbol,
            asset_class=asset_classes[symbol],
            price=price,
            change_pct=change_pct,
            volume=volume,
            timestamp=datetime.now(),
            additional_data=additional_data
        ))
    
    return market_data

def main():
    """Main demonstration function"""
    
    print("=" * 60)
    print("CROSS-ASSET CORRELATION SYSTEM DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Initialize the system
    print("Initializing Cross-Asset Correlation System...")
    correlation_system = CrossAssetCorrelationSystem()
    print("System initialized successfully!")
    print()
    
    # Generate and feed historical data
    print("Generating historical market data...")
    for i in range(100):  # Generate 100 data points
        market_data = generate_market_data()
        timestamp = datetime.now() - timedelta(minutes=100-i)
        
        for data in market_data:
            data.timestamp = timestamp
            correlation_system.update_market_data(data)
            
    print("Historical data loaded!")
    print()
    
    # Perform comprehensive analysis
    print("Performing comprehensive market analysis...")
    analysis = correlation_system.get_comprehensive_analysis()
    
    # Display results
    print("\n" + "=" * 60)
    print("MARKET ANALYSIS RESULTS")
    print("=" * 60)
    
    # Risk Sentiment
    print(f"\n1. RISK SENTIMENT: {analysis['risk_sentiment']}")
    print(f"   Sector Rotation Signals:")
    sector_signals = analysis['sector_rotation']
    print(f"   - Recommended Sectors: {', '.join(sector_signals['recommended_sectors'])}")
    print(f"   - Avoid Sectors: {', '.join(sector_signals['avoid_sectors'])}")
    
    # Dollar Analysis
    print(f"\n2. DOLLAR INDEX ANALYSIS:")
    dollar = analysis['dollar_analysis']
    if dollar.get('status') == 'active':
        print(f"   - Current DXY: {dollar['current_value']:.2f}")
        print(f"   - Trend: {dollar['trend']}")
        print(f"   - Momentum: {dollar['momentum_pct']:.2f}%")
        print(f"   - Signal: {dollar['signal']}")
    
    # Bond Analysis
    print(f"\n3. BOND MARKET ANALYSIS:")
    bonds = analysis['bond_analysis']
    print(f"   - Yield Trends: {bonds['yield_trends']}")
    if bonds['us_german_spread']:
        print(f"   - US-German Spread: {bonds['us_german_spread']:.2f}%")
    if bonds['yield_curve_slope']:
        print(f"   - Yield Curve Slope: {bonds['yield_curve_slope']:.2f}%")
    
    # Commodity-Currency Signals
    print(f"\n4. COMMODITY-CURRENCY CORRELATIONS:")
    for currency, signal in analysis['commodity_currency_signals'].items():
        if signal['signal'] != 'neutral':
            print(f"   - {currency}: {signal['signal']} (strength: {signal['strength']:.2f})")
    
    # Market Divergences
    print(f"\n5. INTERMARKET DIVERGENCES:")
    if analysis['divergences']:
        for div in analysis['divergences'][:3]:  # Top 3 divergences
            print(f"   - {'/'.join(div['assets'])}: {div['type']} divergence")
            print(f"     Severity: {div['severity']:.1f}/100")
            print(f"     Expected Resolution: {div['resolution']}")
    else:
        print("   - No significant divergences detected")
    
    # Strongest Correlations
    print(f"\n6. STRONGEST CORRELATIONS:")
    for corr in analysis['strongest_correlations'][:5]:  # Top 5
        print(f"   - {corr['pair']}: {corr['correlation']:.3f} ({corr['strength']} {corr['direction']})")
    
    # Trading Bias
    print(f"\n7. TRADING BIAS RECOMMENDATIONS:")
    bias = analysis['trading_bias']
    print(f"   - Overall: {bias['overall']}")
    print(f"   - Forex: {bias['forex']}")
    print(f"   - Equity: {bias['equity']}")
    print(f"   - Commodity: {bias['commodity']}")
    
    # Regime Analysis
    print(f"\n8. MARKET REGIME ANALYSIS:")
    regime = analysis['regime_status']
    print(f"   - Current Regime: {regime['market_regime']}")
    if regime['detected_changes']:
        print(f"   - Recent Regime Changes:")
        for change in regime['detected_changes'][:2]:
            print(f"     * {change['pair']}: {change['type']}")
    
    # Specific pair analysis
    print("\n" + "=" * 60)
    print("PAIR-SPECIFIC ANALYSIS: EURUSD")
    print("=" * 60)
    
    eurusd_analysis = correlation_system.get_pair_specific_analysis('EURUSD')
    
    if eurusd_analysis['correlations'].get('status') == 'calculated':
        print(f"\nKey Correlations:")
        print(f"  Positive: {list(eurusd_analysis['correlations']['positive_correlations'].keys())[:3]}")
        print(f"  Negative: {list(eurusd_analysis['correlations']['negative_correlations'].keys())[:3]}")
    
    implications = eurusd_analysis['trading_implications']
    print(f"\nTrading Implications:")
    print(f"  - Primary Drivers: {', '.join(implications['primary_drivers'])}")
    print(f"  - Risk Factors: {', '.join(implications['risk_factors']) if implications['risk_factors'] else 'None'}")
    print(f"  - Optimal Timeframe: {implications['optimal_timeframe']}")
    print(f"  - Position Sizing: {implications['position_sizing']}")
    
    # Real-time monitoring simulation
    print("\n" + "=" * 60)
    print("REAL-TIME MONITORING (5 updates)")
    print("=" * 60)
    
    for i in range(5):
        time.sleep(1)  # Wait 1 second
        
        # Generate new market data
        new_data = generate_market_data()
        
        # Update system
        for data in new_data:
            correlation_system.update_market_data(data)
        
        # Get quick update
        quick_analysis = correlation_system.get_comprehensive_analysis()
        
        print(f"\nUpdate {i+1}:")
        print(f"  - Risk Sentiment: {quick_analysis['risk_sentiment']}")
        print(f"  - Dollar Signal: {quick_analysis['dollar_analysis'].get('signal', 'calculating')}")
        print(f"  - Active Divergences: {len(quick_analysis['divergences'])}")
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()