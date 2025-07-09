#!/usr/bin/env python3
"""
Test script for Cross-Asset Correlation System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import json
from src.bitten_core.strategies.cross_asset_correlation import (
    CrossAssetCorrelationSystem,
    AssetData,
    AssetClass,
    RiskSentiment
)

def test_correlation_system():
    """Test the cross-asset correlation system"""
    
    print("=" * 80)
    print("CROSS-ASSET CORRELATION SYSTEM TEST")
    print("=" * 80)
    print()
    
    # Initialize system
    print("Initializing correlation system...")
    system = CrossAssetCorrelationSystem()
    print("✓ System initialized")
    print()
    
    # Test 1: Bond Yield Differential Calculator
    print("TEST 1: Bond Yield Differential Calculator")
    print("-" * 40)
    
    # Add bond yield data
    bonds = [
        ('US10Y', 4.25),
        ('US2Y', 4.85),
        ('BUND10Y', 2.45),
        ('JGB10Y', 0.75)
    ]
    
    for bond, yield_val in bonds:
        system.bond_calculator.update_yield(bond, yield_val, datetime.now())
        print(f"✓ Added {bond} yield: {yield_val}%")
    
    # Calculate differentials
    us_german_spread = system.bond_calculator.calculate_yield_differential('US10Y', 'BUND10Y')
    yield_curve = system.bond_calculator.get_yield_curve_slope('US2Y', 'US10Y')
    
    print(f"\nUS-German 10Y Spread: {us_german_spread:.2f}%")
    print(f"US Yield Curve (10Y-2Y): {yield_curve:.2f}%")
    print(f"Interpretation: {'Inverted' if yield_curve < 0 else 'Normal'} yield curve")
    print()
    
    # Test 2: Commodity Currency Correlations
    print("TEST 2: Commodity Currency Correlations")
    print("-" * 40)
    
    # Add commodity and currency data
    commodities = [
        ('GOLD', 2050.00),
        ('OIL', 78.50),
        ('COPPER', 3.85)
    ]
    
    currencies = [
        ('AUD', 0.6550),
        ('CAD', 0.7450),
        ('NZD', 0.6050)
    ]
    
    # Simulate historical data for correlation
    for i in range(50):
        timestamp = datetime.now() - timedelta(hours=50-i)
        
        for commodity, base_price in commodities:
            # Add some variation
            price = base_price * (1 + (i - 25) * 0.001)
            system.commodity_analyzer.update_commodity_price(commodity, price, timestamp)
        
        for currency, base_price in currencies:
            # Correlate AUD with GOLD
            if currency == 'AUD':
                gold_factor = (i - 25) * 0.0005
                price = base_price * (1 + gold_factor)
            else:
                price = base_price * (1 + (i - 25) * 0.0002)
            system.commodity_analyzer.update_currency_price(currency, price, timestamp)
    
    # Get commodity currency signals
    signals = system.commodity_analyzer.get_commodity_currency_signals()
    
    for currency, data in signals.items():
        if data['signal'] != 'neutral':
            print(f"\n{currency}:")
            print(f"  Signal: {data['signal']}")
            print(f"  Strength: {data['strength']:.3f}")
            for commodity, corr in data['correlations'].items():
                print(f"  {commodity} correlation: {corr:.3f}")
    print()
    
    # Test 3: Equity Risk On/Off Detection
    print("TEST 3: Equity Risk On/Off Detection")
    print("-" * 40)
    
    # Add equity market data
    risk_on_assets = [
        ('SPX', 4500.00, 2000000),
        ('NDX', 15500.00, 1500000),
        ('DAX', 15800.00, 1000000)
    ]
    
    risk_off_assets = [
        ('GOLD', 2050.00, 500000),
        ('JPY', 150.50, 1000000),
        ('US_BONDS', 100.00, 800000)
    ]
    
    # Simulate risk-on scenario
    for asset, base_price, base_volume in risk_on_assets:
        for i in range(20):
            timestamp = datetime.now() - timedelta(hours=20-i)
            price = base_price * (1 + i * 0.001)  # Rising prices
            volume = base_volume * (1 + i * 0.02)  # Increasing volume
            system.equity_detector.update_asset_data(asset, price, volume, timestamp)
    
    for asset, base_price, base_volume in risk_off_assets:
        for i in range(20):
            timestamp = datetime.now() - timedelta(hours=20-i)
            price = base_price * (1 - i * 0.0005)  # Falling prices
            volume = base_volume * (1 - i * 0.01)  # Decreasing volume
            system.equity_detector.update_asset_data(asset, price, volume, timestamp)
    
    risk_sentiment = system.equity_detector.calculate_risk_sentiment()
    sector_signals = system.equity_detector.get_sector_rotation_signals()
    
    print(f"Current Risk Sentiment: {risk_sentiment.value}")
    print(f"Recommended Sectors: {', '.join(sector_signals['recommended_sectors'])}")
    print(f"Avoid Sectors: {', '.join(sector_signals['avoid_sectors'])}")
    print()
    
    # Test 4: Dollar Index Analysis
    print("TEST 4: Dollar Index Analysis")
    print("-" * 40)
    
    # Add currency rates for DXY calculation
    dxy_currencies = [
        ('EUR', 1.0850),   # EUR/USD
        ('JPY', 0.00665),  # USD/JPY inverted
        ('GBP', 1.2650),   # GBP/USD
        ('CAD', 0.7450),   # USD/CAD inverted
        ('SEK', 0.0950),   # USD/SEK inverted
        ('CHF', 1.1050)    # USD/CHF inverted
    ]
    
    for currency, rate in dxy_currencies:
        system.dollar_analyzer.update_currency_rate(currency, rate, datetime.now())
    
    dollar_analysis = system.dollar_analyzer.analyze_dollar_strength()
    
    if dollar_analysis['status'] == 'active':
        print(f"DXY Value: {dollar_analysis['current_value']:.2f}")
        print(f"Trend: {dollar_analysis['trend']}")
        print(f"Signal: {dollar_analysis['signal']}")
    print()
    
    # Test 5: Intermarket Divergence Detection
    print("TEST 5: Intermarket Divergence Detection")
    print("-" * 40)
    
    # Create a divergence scenario: GOLD up, DXY up (should be negative correlation)
    for i in range(50):
        timestamp = datetime.now() - timedelta(hours=50-i)
        
        # GOLD trending up
        gold_price = 2000 + i * 2
        system.divergence_detector.update_market_data('GOLD', gold_price, timestamp)
        
        # DXY also trending up (divergence!)
        dxy_value = 100 + i * 0.1
        system.divergence_detector.update_market_data('DXY', dxy_value, timestamp)
        
        # EURUSD trending down (normal correlation with DXY)
        eurusd_price = 1.10 - i * 0.001
        system.divergence_detector.update_market_data('EURUSD', eurusd_price, timestamp)
    
    divergences = system.divergence_detector.detect_divergences()
    
    if divergences:
        print(f"Found {len(divergences)} divergence(s):")
        for div in divergences[:3]:
            print(f"\n  Assets: {' vs '.join(div.assets)}")
            print(f"  Type: {div.divergence_type}")
            print(f"  Severity: {div.severity:.1f}/100")
            print(f"  Expected Resolution: {div.expected_resolution}")
    else:
        print("No significant divergences detected")
    print()
    
    # Test 6: Correlation Matrix
    print("TEST 6: Correlation Matrix Calculation")
    print("-" * 40)
    
    # Add more data for correlation matrix
    assets = ['EURUSD', 'GBPUSD', 'GOLD', 'SPX', 'OIL', 'DXY']
    
    for i in range(50):
        timestamp = datetime.now() - timedelta(hours=50-i)
        
        # Create some correlations
        base_factor = (i - 25) / 25  # -1 to 1
        
        system.correlation_calculator.update_asset_price('EURUSD', 1.08 + base_factor * 0.02, timestamp)
        system.correlation_calculator.update_asset_price('GBPUSD', 1.26 + base_factor * 0.03, timestamp)
        system.correlation_calculator.update_asset_price('GOLD', 2050 + base_factor * 50, timestamp)
        system.correlation_calculator.update_asset_price('SPX', 4500 - base_factor * 100, timestamp)
        system.correlation_calculator.update_asset_price('OIL', 78 + base_factor * 5, timestamp)
        system.correlation_calculator.update_asset_price('DXY', 103 - base_factor * 2, timestamp)
    
    matrix = system.correlation_calculator.calculate_correlation_matrix()
    strongest = system.correlation_calculator.get_strongest_correlations(threshold=0.5)
    
    if matrix is not None:
        print("Correlation Matrix calculated successfully")
        print(f"Assets included: {', '.join(matrix.columns)}")
        print(f"\nStrongest correlations (|r| > 0.5):")
        for corr in strongest[:5]:
            print(f"  {corr.asset1}/{corr.asset2}: {corr.correlation:.3f} ({corr.strength})")
    print()
    
    # Test 7: Comprehensive Analysis
    print("TEST 7: Comprehensive Market Analysis")
    print("-" * 40)
    
    analysis = system.get_comprehensive_analysis()
    
    print(f"Risk Sentiment: {analysis['risk_sentiment']}")
    print(f"\nDollar Analysis:")
    if analysis['dollar_analysis']['status'] == 'active':
        print(f"  Signal: {analysis['dollar_analysis']['signal']}")
    
    print(f"\nTrading Bias:")
    for market, bias in analysis['trading_bias'].items():
        print(f"  {market.capitalize()}: {bias}")
    
    print(f"\nMarket Regime: {analysis['regime_status']['market_regime']}")
    
    if analysis['divergences']:
        print(f"\nActive Divergences: {len(analysis['divergences'])}")
    
    print()
    
    # Test 8: Pair-Specific Analysis
    print("TEST 8: Pair-Specific Analysis (EURUSD)")
    print("-" * 40)
    
    eurusd_analysis = system.get_pair_specific_analysis('EURUSD')
    
    if eurusd_analysis['correlations']['status'] == 'calculated':
        print("Key correlations found")
        
    implications = eurusd_analysis['trading_implications']
    print(f"\nTrading Implications:")
    print(f"  Optimal Timeframe: {implications['optimal_timeframe']}")
    print(f"  Position Sizing: {implications['position_sizing']}")
    if implications['primary_drivers']:
        print(f"  Primary Drivers: {', '.join(implications['primary_drivers'])}")
    
    print()
    print("=" * 80)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    test_correlation_system()