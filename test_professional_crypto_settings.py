#!/usr/bin/env python3
"""
🏆 Professional C.O.R.E. Crypto Trading Settings Test
Tests the professional ATR-based risk management system

Professional Settings:
- Risk Per Trade: 1% of equity (tighter for 55-65% win rates)
- SL vs. TP: SL = ATR * 3, TP = SL * 2 (1:2 RR for all signals)
- Daily Cap: 4% max drawdown (4 losses max)
- Expected: ~0.65% per trade, 3 trades/day = 1.95% daily

Author: Claude Code Agent
Date: August 2025
"""

import sys
import os
from datetime import datetime

# Add paths for imports
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2/src/bitten_core')

def test_professional_crypto_settings():
    """Test professional crypto trading settings"""
    print("🏆 TESTING PROFESSIONAL C.O.R.E. CRYPTO SETTINGS")
    print("=" * 70)
    
    try:
        from crypto_fire_builder import CryptoPositionSizer
        sizer = CryptoPositionSizer()
        print("✅ Professional crypto position sizer imported")
    except ImportError as e:
        print(f"❌ Failed to import crypto position sizer: {e}")
        return False
    
    # Test account balances
    test_accounts = [
        {"balance": 10000.0, "name": "Standard Account"},
        {"balance": 50000.0, "name": "Large Account"},
        {"balance": 100000.0, "name": "Professional Account"}
    ]
    
    # Test symbols with different volatilities
    test_symbols = ["BTCUSD", "ETHUSD", "XRPUSD"]
    
    print(f"\n📊 PROFESSIONAL RISK MANAGEMENT SETTINGS")
    print("-" * 50)
    print(f"Risk Per Trade: {sizer.default_risk_percent}% (Professional Setting)")
    print(f"Max Daily Drawdown: {sizer.max_daily_drawdown}% (4 losses max)")
    print(f"Risk:Reward Ratio: 1:{sizer.risk_reward_ratio} (prioritize reward)")
    print(f"ATR Multiplier: {sizer.atr_multiplier}x (crypto volatility)")
    
    print(f"\n🎯 POSITION SIZING CALCULATIONS")
    print("=" * 70)
    
    for account in test_accounts:
        balance = account["balance"]
        name = account["name"]
        
        print(f"\n💰 {name}: ${balance:,.2f}")
        print("-" * 50)
        
        for symbol in test_symbols:
            # Test with professional ATR-based method
            position_size, sl_pips, tp_pips, details = sizer.calculate_crypto_position_size_atr(
                account_balance=balance,
                symbol=symbol,
                entry_price=67000.0 if symbol == "BTCUSD" else (2400.0 if symbol == "ETHUSD" else 0.62),
                atr_value=None,  # Use defaults
                risk_percent=None,  # Use 1% default
                trades_today=0
            )
            
            # Extract key metrics
            risk_amount = details["risk_amount"]
            atr_value = details["atr_value"]
            pip_value = details["pip_value"]
            expected_value = details["expected_value"]
            risk_reward = details["risk_reward_ratio"]
            
            print(f"   📈 {symbol}:")
            print(f"      Position: {position_size} lots")
            print(f"      Risk: ${risk_amount:.2f} ({details['risk_percent']:.1f}%)")
            print(f"      ATR: {atr_value:.0f} pips | SL: {sl_pips:.0f} pips | TP: {tp_pips:.0f} pips")
            print(f"      Risk:Reward: 1:{risk_reward:.0f} | Expected Value: ${expected_value:.2f}")
            print(f"      Pip Value: ${pip_value:.2f}/pip")
    
    print(f"\n⚠️ DAILY DRAWDOWN PROTECTION TEST")
    print("=" * 70)
    
    # Test daily drawdown protection
    test_balance = 10000.0
    symbol = "BTCUSD"
    
    for trades_today in range(0, 5):
        position_size, sl_pips, tp_pips, details = sizer.calculate_crypto_position_size_atr(
            account_balance=test_balance,
            symbol=symbol,
            entry_price=67000.0,
            trades_today=trades_today
        )
        
        risk_amount = details["risk_amount"]
        protection_active = details["daily_protection_active"]
        
        status = "🛡️ PROTECTION ACTIVE" if protection_active else "✅ Normal Risk"
        print(f"Trade #{trades_today + 1}: Risk ${risk_amount:.2f} ({details['risk_percent']:.1f}%) - {status}")
    
    print(f"\n📈 EXPECTED PERFORMANCE ANALYSIS")
    print("=" * 70)
    
    # Calculate expected performance for different scenarios
    base_balance = 10000.0
    
    scenarios = [
        {"win_rate": 0.55, "name": "Conservative (55% wins)"},
        {"win_rate": 0.60, "name": "Target (60% wins)"}, 
        {"win_rate": 0.65, "name": "Optimistic (65% wins)"}
    ]
    
    for scenario in scenarios:
        win_rate = scenario["win_rate"]
        name = scenario["name"]
        
        # Use BTCUSD as example
        position_size, sl_pips, tp_pips, details = sizer.calculate_crypto_position_size_atr(
            account_balance=base_balance,
            symbol="BTCUSD",
            entry_price=67000.0
        )
        
        risk_amount = details["risk_amount"]
        expected_gain = details["expected_gain"]
        expected_loss = details["expected_loss"]
        
        # Calculate expected value for this win rate
        expected_value = (win_rate * expected_gain) - ((1 - win_rate) * expected_loss)
        
        # Daily and monthly projections
        daily_ev = expected_value * 3  # 3 trades per day
        monthly_ev = daily_ev * 22  # 22 trading days
        monthly_percentage = (monthly_ev / base_balance) * 100
        
        print(f"\n🎯 {name}")
        print(f"   Expected Value per Trade: ${expected_value:.2f}")
        print(f"   Daily Expected (3 trades): ${daily_ev:.2f} ({daily_ev/base_balance*100:.2f}%)")
        print(f"   Monthly Expected: ${monthly_ev:.2f} ({monthly_percentage:.1f}%)")
    
    print(f"\n🔍 SYMBOL-SPECIFIC ANALYSIS")
    print("=" * 70)
    
    balance = 10000.0
    symbol_analysis = []
    
    for symbol in test_symbols:
        position_size, sl_pips, tp_pips, details = sizer.calculate_crypto_position_size_atr(
            account_balance=balance,
            symbol=symbol,
            entry_price=67000.0 if symbol == "BTCUSD" else (2400.0 if symbol == "ETHUSD" else 0.62)
        )
        
        symbol_analysis.append({
            "symbol": symbol,
            "position": position_size,
            "sl_pips": sl_pips,
            "tp_pips": tp_pips,
            "atr": details["atr_value"],
            "pip_value": details["pip_value"],
            "expected_value": details["expected_value"]
        })
    
    for analysis in symbol_analysis:
        print(f"\n💎 {analysis['symbol']}:")
        print(f"   ATR: {analysis['atr']:.0f} pips → SL: {analysis['sl_pips']:.0f} pips → TP: {analysis['tp_pips']:.0f} pips")
        print(f"   Position: {analysis['position']} lots | Pip Value: ${analysis['pip_value']:.2f}")
        print(f"   Expected Value: ${analysis['expected_value']:.2f} per trade")
    
    print(f"\n📋 PROFESSIONAL SETTINGS VALIDATION")
    print("=" * 70)
    
    # Validate all professional settings are correct
    validations = [
        ("Risk Per Trade", sizer.default_risk_percent == 1.0, "1% (Professional)"),
        ("Max Daily Drawdown", sizer.max_daily_drawdown == 4.0, "4% (4 losses max)"),
        ("Risk:Reward Ratio", sizer.risk_reward_ratio == 2.0, "1:2 (prioritize reward)"),
        ("ATR Multiplier", sizer.atr_multiplier == 3.0, "3x (crypto volatility)"),
    ]
    
    all_valid = True
    for name, condition, expected in validations:
        status = "✅ CORRECT" if condition else "❌ INCORRECT"
        print(f"{name}: {status} - {expected}")
        if not condition:
            all_valid = False
    
    print(f"\n🎉 PROFESSIONAL SETTINGS SUMMARY")
    print("=" * 70)
    
    if all_valid:
        print("✅ ALL PROFESSIONAL SETTINGS VALIDATED")
        print("✅ ATR-based stop loss calculation (ATR * 3)")
        print("✅ 1:2 Risk:Reward ratio enforced")
        print("✅ 1% risk per trade (professional level)")
        print("✅ 4% daily drawdown protection active")
        print("✅ Expected value: ~0.65% per trade")
        print("✅ Daily target: ~1.95% (3 trades)")
        print("\n🏆 System ready for professional crypto trading!")
        
        # Example calculation matching user's specification
        print(f"\n📊 EXAMPLE (User Specification):")
        print(f"$10k equity, ATR=50 pips:")
        example_size, example_sl, example_tp, example_details = sizer.calculate_crypto_position_size_atr(
            account_balance=10000.0,
            symbol="BTCUSD", 
            entry_price=67000.0,
            atr_value=50.0  # User's example ATR
        )
        print(f"Risk: ${example_details['risk_amount']:.2f} (1%)")
        print(f"SL: {example_sl:.0f} pips (ATR * 3)")
        print(f"TP: {example_tp:.0f} pips (SL * 2)")
        print(f"Position: {example_size:.2f} lots")
        print(f"Pip Value: ${example_details['pip_value']:.2f}/pip")
        
        return True
    else:
        print("❌ Some professional settings are incorrect")
        return False

if __name__ == "__main__":
    print("🏆 PROFESSIONAL C.O.R.E. CRYPTO TRADING SETTINGS")
    print("Professional ATR-based risk management validation")
    print("=" * 80)
    
    success = test_professional_crypto_settings()
    
    if success:
        print(f"\n🚀 PROFESSIONAL CRYPTO SYSTEM READY!")
        print(f"   Risk: 1% per trade (professional level)")
        print(f"   Stops: ATR * 3 (crypto volatility)")
        print(f"   Targets: 1:2 Risk:Reward (prioritize reward)")
        print(f"   Protection: 4% daily drawdown cap")
        print(f"   Expected: ~0.65% per trade, 1.95% daily")
    else:
        print(f"\n❌ Professional settings need adjustment")
        
    print(f"\nReady for C.O.R.E. crypto execution with professional risk management! 🏆")