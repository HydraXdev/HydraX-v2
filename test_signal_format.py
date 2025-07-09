#!/usr/bin/env python3
"""Test signal formatting"""

from tiered_signal_system import format_tactical_signal, SIGNAL_TIERS

# Test signals for each tier
test_signals = [
    # NIBBLER - Basic pistol shots
    {"symbol": "EURUSD", "direction": "BUY", "entry_price": 1.08453, "confidence": 0.78, "tier": "NIBBLER"},
    {"symbol": "GBPUSD", "direction": "SELL", "entry_price": 1.26789, "confidence": 0.82, "tier": "NIBBLER"},
    
    # FANG - Sniper precision
    {"symbol": "USDJPY", "direction": "BUY", "entry_price": 149.234, "confidence": 0.87, "tier": "FANG"},
    {"symbol": "AUDUSD", "direction": "SELL", "entry_price": 0.65432, "confidence": 0.89, "tier": "FANG"},
    
    # COMMANDER - Lightning strikes
    {"symbol": "USDCHF", "direction": "BUY", "entry_price": 0.88765, "confidence": 0.94, "tier": "COMMANDER"},
    {"symbol": "USDCAD", "direction": "SELL", "entry_price": 1.35678, "confidence": 0.93, "tier": "COMMANDER"},
    
    # APEX - Critical alerts
    {"symbol": "NZDUSD", "direction": "BUY", "entry_price": 0.59876, "confidence": 0.97, "tier": "APEX"},
    {"symbol": "EURGBP", "direction": "SELL", "entry_price": 0.85432, "confidence": 0.98, "tier": "APEX"}
]

print("=== BITTEN TACTICAL SIGNAL EXAMPLES ===\n")
print("All signals are exactly 2 lines - clean and professional\n")

for signal in test_signals:
    print(f"--- {signal['tier']} TIER ---")
    formatted = format_tactical_signal(signal, signal['tier'])
    print(formatted)
    print(f"(Access: {', '.join(SIGNAL_TIERS[signal['tier']]['access'])})")
    print()

# Show daily limits
print("\n=== DAILY SIGNAL LIMITS ===")
for tier, config in SIGNAL_TIERS.items():
    print(f"{tier}: {config['max_daily']} signals/day")

print("\n=== VISUAL IDENTIFICATION ===")
print("🔫 PISTOL = NIBBLER (entry level)")
print("🎯 SNIPER = FANG (precision)")  
print("⚡ STRIKE = COMMANDER (high value)")
print("🚨 CRITICAL = APEX (elite only)")