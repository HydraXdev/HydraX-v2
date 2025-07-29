#!/usr/bin/env python3
"""
Test script to demonstrate TOC RR ratio calculation functionality
This shows how the TOC server calculates RR ratios from signals
"""

import json
from datetime import datetime

def calculate_rr_ratios(signal_data):
    """
    Calculate RR ratios based on signal type and TCS - THIS IS THE TOC'S JOB
    (NOT the engine's job)
    """
    try:
        entry_price = signal_data['entry_price']
        signal_type = signal_data.get('signal_type', 'RAPID_ASSAULT')
        tcs = signal_data.get('tcs', 70)
        direction = signal_data['direction']
        
        # Base RR ratios by signal type - capped at 90 TCS for RAPID_ASSAULT, 92 for SNIPER_OPS
        if signal_type == 'RAPID_ASSAULT':
            # 2.0 to 2.6 based on TCS, maxed at 90 TCS
            effective_tcs = min(tcs, 90)
            base_rr = 2.0 + (effective_tcs - 70) * 0.03  # 2.0 to 2.6 over 20 points (70-90)
        else:  # SNIPER_OPS
            # 2.7 to 3.25 based on TCS, maxed at 92 TCS
            effective_tcs = min(tcs, 92)
            base_rr = 2.7 + (effective_tcs - 70) * 0.025  # 2.7 to 3.25 over 22 points (70-92)
        
        # Calculate stop loss and take profit
        if direction == 'BUY':
            stop_loss = entry_price * 0.999   # 10 pips stop loss
            take_profit = entry_price + (entry_price - stop_loss) * base_rr
        else:  # SELL
            stop_loss = entry_price * 1.001   # 10 pips stop loss
            take_profit = entry_price - (stop_loss - entry_price) * base_rr
        
        return {
            'stop_loss': round(stop_loss, 5),
            'take_profit': round(take_profit, 5),
            'rr_ratio': round(base_rr, 2),
            'signal_type': signal_type,
            'tcs_used': tcs
        }
        
    except Exception as e:
        print(f"RR calculation error: {e}")
        return {
            'stop_loss': signal_data['entry_price'] * 0.999,
            'take_profit': signal_data['entry_price'] * 1.002,
            'rr_ratio': 2.0,
            'error': str(e)
        }

def test_rr_calculations():
    """Test RR calculations for different signal types and TCS values"""
    
    print("🎯 BITTEN TOC RR Ratio Calculation Test")
    print("=" * 50)
    print()
    
    # Test signals matching what would generate
    test_signals = [
        {
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'entry_price': 1.0900,
            'signal_type': 'RAPID_ASSAULT',
            'tcs': 75,
            'volume': 0.01,
            'comment': 'Signal'
        },
        {
            'symbol': 'GBPUSD',
            'direction': 'SELL',
            'entry_price': 1.2500,
            'signal_type': 'SNIPER_OPS',
            'tcs': 85,
            'volume': 0.02,
            'comment': 'Signal'
        },
        {
            'symbol': 'USDJPY',
            'direction': 'BUY',
            'entry_price': 150.50,
            'signal_type': 'RAPID_ASSAULT',
            'tcs': 99,  # Above 90 TCS cap - should get max 1:2.6
            'volume': 0.01,
            'comment': 'Signal'
        },
        {
            'symbol': 'EURJPY',
            'direction': 'SELL',
            'entry_price': 165.25,
            'signal_type': 'SNIPER_OPS',
            'tcs': 95,  # Above 92 TCS cap - should get max 1:3.25
            'volume': 0.01,
            'comment': 'Signal'
        },
        {
            'symbol': 'GBPJPY',
            'direction': 'BUY',
            'entry_price': 190.75,
            'signal_type': 'RAPID_ASSAULT',
            'tcs': 90,  # At 90 TCS cap - should get max 1:2.6
            'volume': 0.01,
            'comment': 'Signal'
        },
        {
            'symbol': 'AUDUSD',
            'direction': 'SELL',
            'entry_price': 0.6750,
            'signal_type': 'SNIPER_OPS',
            'tcs': 92,  # At 92 TCS cap - should get max 1:3.25
            'volume': 0.01,
            'comment': 'Signal'
        }
    ]
    
    for i, signal in enumerate(test_signals, 1):
        print(f"📊 Test {i}: {signal['signal_type']} - {signal['symbol']} {signal['direction']}")
        print(f"   Entry Price: {signal['entry_price']}")
        print(f"   TCS Score: {signal['tcs']}%")
        print()
        
        # Calculate RR ratios (this is what TOC does)
        rr_calculation = calculate_rr_ratios(signal)
        
        # Create enhanced signal with RR calculations
        enhanced_signal = {
            **signal,
            'stop_loss': rr_calculation['stop_loss'],
            'take_profit': rr_calculation['take_profit'],
            'risk_reward_ratio': rr_calculation['rr_ratio'],
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"   🔥 TOC Enhanced Signal:")
        print(f"   ├── Stop Loss: {enhanced_signal['stop_loss']}")
        print(f"   ├── Take Profit: {enhanced_signal['take_profit']}")
        print(f"   └── RR Ratio: 1:{enhanced_signal['risk_reward_ratio']}")
        print()
        
        # Show the risk/reward calculation
        if signal['direction'] == 'BUY':
            risk = signal['entry_price'] - enhanced_signal['stop_loss']
            reward = enhanced_signal['take_profit'] - signal['entry_price']
        else:
            risk = enhanced_signal['stop_loss'] - signal['entry_price']
            reward = signal['entry_price'] - enhanced_signal['take_profit']
        
        print(f"   📈 Risk/Reward Analysis:")
        print(f"   ├── Risk: {risk:.5f}")
        print(f"   ├── Reward: {reward:.5f}")
        print(f"   └── Actual RR: 1:{reward/risk:.2f}")
        print()
        print("-" * 50)
        print()

def show_architecture_summary():
    """Show the corrected architecture"""
    print("🏗️  CORRECTED BITTEN ARCHITECTURE")
    print("=" * 50)
    print()
    print("✅ ENGINE (Signal Generation Only):")
    print("   ├── Generates TCS scores")
    print("   ├── Identifies signal types (RAPID_ASSAULT, SNIPER_OPS)")
    print("   ├── Provides entry prices and directions")
    print("   └── NO RR ratio calculations")
    print()
    print("✅ TOC SERVER (Trade Logic & RR Calculations):")
    print("   ├── Receives clean signals from ")
    print("   ├── Calculates RR ratios based on signal type & TCS")
    print("   ├── Determines stop loss and take profit levels")
    print("   ├── Manages BITTEN_MASTER clone assignments")
    print("   └── Routes enhanced signals to user MT5 instances")
    print()
    print("✅ BITTEN_MASTER CLONE SYSTEM:")
    print("   ├── Single master template gets cloned per user")
    print("   ├── Each user gets their own MT5 instance")
    print("   ├── File-based bridge communication")
    print("   └── Replaces old 3-terminal system")
    print()

if __name__ == "__main__":
    show_architecture_summary()
    test_rr_calculations()
    
    print("🎯 Summary:")
    print("- generates clean signals with TCS scores")
    print("- TOC calculates RR ratios dynamically based on signal type and TCS")  
    print("- BITTEN_MASTER clones handle individual user execution")
    print("- Architecture separation is now properly maintained")