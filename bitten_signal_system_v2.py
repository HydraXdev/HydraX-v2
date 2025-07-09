#!/usr/bin/env python3
"""
BITTEN Signal System v2
Two signal types: PISTOL (quick scalps) and SNIPER (longer precision)
Tiered access control, not quality differentiation
"""

# Signal Types (NOT tiers - these are trade types)
SIGNAL_TYPES = {
    "PISTOL": {
        "min_confidence": 0.75,
        "emoji": "🔫",
        "avg_duration": "1-35 min",
        "description": "Quick scalp",
        "style": "PISTOL"
    },
    "SNIPER": {
        "min_confidence": 0.85,  # Higher TCS for longer wait justification
        "emoji": "🎯",
        "avg_duration": "90-100 min",
        "description": "Precision shot",
        "style": "SNIPER"
    }
}

# Access Tiers (subscription levels)
ACCESS_TIERS = {
    "nibbler": {
        "can_view": ["PISTOL", "SNIPER"],
        "can_trade": ["PISTOL"],  # Only pistol shots
        "max_daily": 6,
        "auto_trade": False
    },
    "fang": {
        "can_view": ["PISTOL", "SNIPER"],
        "can_trade": ["PISTOL", "SNIPER"],  # ALL shots
        "max_daily": 10,  # Combined limit
        "auto_trade": False
    },
    "commander": {
        "can_view": ["PISTOL", "SNIPER"],
        "can_trade": ["PISTOL", "SNIPER"],  # ALL shots
        "max_daily": 15,
        "auto_trade": True,  # Can use AUTO mode (92%+ TCS)
        "auto_min_confidence": 0.92
    },
    "apex": {
        "can_view": ["PISTOL", "SNIPER"],
        "can_trade": ["PISTOL", "SNIPER"],  # ALL shots
        "max_daily": 20,
        "auto_trade": True,  # Can use AUTO mode
        "auto_min_confidence": 0.92
    }
}

def format_signal_alert(signal_data, signal_type):
    """
    Format signal for Telegram - 2 lines MAX
    Shows signal type clearly for quick recognition
    """
    
    config = SIGNAL_TYPES[signal_type]
    direction = signal_data['direction']
    
    # Format: Emoji + Pair + Direction + TCS
    # Second line: Entry + Signal type
    
    message = f"{config['emoji']} {signal_data['symbol']} {direction} [{int(signal_data['confidence']*100)}%]\n"
    message += f"@ {signal_data['entry_price']:.5f} • {config['style']}"
    
    return message

def determine_signal_type(confidence, indicators):
    """
    Determine if signal is PISTOL or SNIPER based on market conditions
    NOT based on subscription tier
    """
    
    # SNIPER signals require 85%+ confidence AND specific conditions
    if confidence >= 0.85 and indicators.get('strong_trend', False):
        return "SNIPER"
    
    # PISTOL for quicker opportunities
    if confidence >= 0.75:
        return "PISTOL"
        
    return None

def check_user_access(user_tier, signal_type, action="view"):
    """
    Check if user tier has access to signal type
    action: "view" or "trade"
    """
    tier_config = ACCESS_TIERS.get(user_tier)
    if not tier_config:
        return False
        
    if action == "view":
        return signal_type in tier_config['can_view']
    elif action == "trade":
        return signal_type in tier_config['can_trade']
        
    return False

def format_access_denied_message(user_tier, signal_type):
    """Message when user tries to trade beyond their tier"""
    
    if user_tier == "nibbler" and signal_type == "SNIPER":
        return (
            "⚠️ SNIPER shots require FANG tier or above\n"
            "Upgrade to access precision trades → /upgrade"
        )
    
    return "Access denied for this signal type"

# Example formatted signals
SIGNAL_EXAMPLES = {
    "PISTOL": {
        "message": "🔫 EURUSD BUY [78%]\n@ 1.08453 • PISTOL",
        "access": "All tiers can trade",
        "duration": "Quick 1-35 min scalp"
    },
    "SNIPER": {
        "message": "🎯 GBPUSD SELL [87%]\n@ 1.26789 • SNIPER",
        "access": "FANG+ can trade, NIBBLER view only",
        "duration": "Precision 90-100 min trade"
    }
}

# Commander/Apex AUTO mode
AUTO_MODE_CONFIG = {
    "enabled_tiers": ["commander", "apex"],
    "min_confidence": 0.92,  # Only auto-fire on 92%+ signals
    "max_open_trades": 3,    # Limit concurrent trades
    "risk_per_trade": 0.02,  # 2% risk per trade
}

def should_auto_execute(user_tier, confidence, open_trades):
    """
    Determine if trade should auto-execute for Commander/Apex
    """
    if user_tier not in AUTO_MODE_CONFIG['enabled_tiers']:
        return False
        
    if confidence < AUTO_MODE_CONFIG['min_confidence']:
        return False
        
    if open_trades >= AUTO_MODE_CONFIG['max_open_trades']:
        return False
        
    return True

# Trading session filters
def calculate_signal_indicators(symbol, price_data):
    """
    Calculate indicators to determine signal type and strength
    """
    indicators = {}
    
    # Momentum for quick scalps (PISTOL)
    if len(price_data) >= 10:
        recent_momentum = (price_data[-1] - price_data[-10]) / price_data[-10]
        indicators['quick_momentum'] = abs(recent_momentum) > 0.0002
    
    # Strong trend for precision shots (SNIPER)
    if len(price_data) >= 50:
        sma_20 = sum(price_data[-20:]) / 20
        sma_50 = sum(price_data[-50:]) / 50
        price_above_sma = price_data[-1] > sma_20 > sma_50
        price_below_sma = price_data[-1] < sma_20 < sma_50
        indicators['strong_trend'] = price_above_sma or price_below_sma
    
    return indicators

if __name__ == "__main__":
    print("=== BITTEN SIGNAL SYSTEM V2 ===\n")
    
    print("SIGNAL TYPES (2 types only):")
    print("-" * 40)
    for signal_type, example in SIGNAL_EXAMPLES.items():
        print(f"\n{signal_type}:")
        print(example['message'])
        print(f"Access: {example['access']}")
        print(f"Duration: {example['duration']}")
    
    print("\n\nACCESS TIERS:")
    print("-" * 40)
    for tier, config in ACCESS_TIERS.items():
        print(f"\n{tier.upper()}:")
        print(f"  Can trade: {', '.join(config['can_trade'])}")
        print(f"  Daily limit: {config['max_daily']}")
        if config['auto_trade']:
            print(f"  AUTO mode: Yes (92%+ TCS)")
    
    print("\n\nKEY POINTS:")
    print("• NIBBLER: Can only trade PISTOL shots (quick scalps)")
    print("• FANG+: Can trade ALL shots (PISTOL & SNIPER)")
    print("• COMMANDER/APEX: Same as FANG + AUTO mode option")
    print("• AUTO mode: Fires automatically on 92%+ TCS signals")
    print("• All tiers can VIEW all signals, but trading is restricted")