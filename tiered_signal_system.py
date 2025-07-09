#!/usr/bin/env python3
"""
BITTEN Tiered Signal System
Military-grade tactical alert formatting
"""

# Signal Tiers Configuration
SIGNAL_TIERS = {
    "NIBBLER": {
        "min_confidence": 0.75,
        "max_confidence": 0.85,
        "emoji": "🔫",  # Pistol for basic shots
        "max_daily": 6,
        "description": "PISTOL",
        "access": ["nibbler", "fang", "commander", "apex"]
    },
    "FANG": {
        "min_confidence": 0.85,
        "max_confidence": 0.92,
        "emoji": "🎯",  # Precision target
        "max_daily": 4,
        "description": "SNIPER",
        "access": ["fang", "commander", "apex"]
    },
    "COMMANDER": {
        "min_confidence": 0.92,
        "max_confidence": 0.96,
        "emoji": "⚡",  # Lightning strike
        "max_daily": 3,
        "description": "STRIKE",
        "access": ["commander", "apex"]
    },
    "APEX": {
        "min_confidence": 0.96,
        "max_confidence": 1.0,
        "emoji": "🚨",  # Critical alert
        "max_daily": 2,
        "description": "CRITICAL",
        "access": ["apex"]
    }
}

def format_tactical_signal(signal_data, tier):
    """
    Format signal for Telegram - 2 lines MAX
    Tactical, clean, professional
    """
    
    tier_config = SIGNAL_TIERS[tier]
    direction = "BUY" if signal_data['direction'] == 'BUY' else "SELL"
    
    # Line 1: Tier emoji + pair + direction + confidence
    # Line 2: Entry price + tier name
    
    message = f"{tier_config['emoji']} {signal_data['symbol']} {direction} [{int(signal_data['confidence']*100)}%]\n"
    message += f"@ {signal_data['entry_price']:.5f} • {tier_config['description']}"
    
    return message

def get_signal_tier(confidence):
    """Determine which tier a signal belongs to"""
    for tier_name, config in SIGNAL_TIERS.items():
        if config['min_confidence'] <= confidence < config['max_confidence']:
            return tier_name
    return None

# Example signals for each tier
EXAMPLE_SIGNALS = {
    "NIBBLER": """🔫 EURUSD BUY [78%]
@ 1.08453 • PISTOL""",
    
    "FANG": """🎯 GBPUSD SELL [87%]
@ 1.26789 • SNIPER""",
    
    "COMMANDER": """⚡ USDJPY BUY [94%]
@ 149.234 • STRIKE""",
    
    "APEX": """🚨 AUDUSD SELL [97%]
@ 0.65432 • CRITICAL"""
}

# Updated filtering logic
def apply_tiered_filters(symbol, bid, ask, spread, indicators):
    """
    Apply multi-tier filtering based on signal strength
    Returns: (tier, confidence, filters_passed)
    """
    
    confidence = 0.0
    filters_passed = []
    
    # Base filters (required for all tiers)
    if spread > 0.0001 and spread < 0.0005:
        confidence += 0.20
        filters_passed.append("spread")
    
    # Momentum filter
    if abs(indicators.get('momentum', 0)) > 0.0002:
        confidence += 0.25
        filters_passed.append("momentum")
    
    # RSI filter
    rsi = indicators.get('rsi', 50)
    if (rsi < 30 and indicators.get('direction') == 'BUY') or \
       (rsi > 70 and indicators.get('direction') == 'SELL'):
        confidence += 0.20
        filters_passed.append("rsi")
    
    # Volume filter
    if indicators.get('volume', 0) > 1000000:
        confidence += 0.15
        filters_passed.append("volume")
    
    # Session optimization
    if indicators.get('optimal_session', False):
        confidence += 0.15
        filters_passed.append("session")
    
    # Advanced filters for higher tiers
    if indicators.get('macd_confirmation', False):
        confidence += 0.10
        filters_passed.append("macd")
    
    if indicators.get('support_resistance', False):
        confidence += 0.10
        filters_passed.append("s/r")
    
    # Determine tier
    tier = get_signal_tier(confidence)
    
    return tier, confidence, filters_passed

# Session configuration for optimal trading
SESSION_SCHEDULE = {
    "EURUSD": {"start": 7, "end": 16},    # Frankfurt/London
    "GBPUSD": {"start": 8, "end": 16},    # London
    "USDJPY": {"start": 0, "end": 9},     # Tokyo
    "USDCHF": {"start": 7, "end": 16},    # European
    "AUDUSD": {"start": 22, "end": 6},    # Sydney/Tokyo
    "USDCAD": {"start": 13, "end": 21},   # New York
    "NZDUSD": {"start": 21, "end": 5},    # Wellington/Sydney
    "EURGBP": {"start": 7, "end": 16}     # European overlap
}

def check_session_active(symbol):
    """Check if current time is within optimal session"""
    from datetime import datetime
    
    current_hour = datetime.now().hour
    if symbol in SESSION_SCHEDULE:
        session = SESSION_SCHEDULE[symbol]
        start = session['start']
        end = session['end']
        
        # Handle sessions that cross midnight
        if start > end:
            return current_hour >= start or current_hour <= end
        else:
            return start <= current_hour <= end
    
    return True

if __name__ == "__main__":
    print("=== BITTEN TACTICAL SIGNAL FORMAT ===\n")
    
    for tier, example in EXAMPLE_SIGNALS.items():
        print(f"{tier} Tier Example:")
        print("-" * 30)
        print(example)
        print(f"Access: {', '.join(SIGNAL_TIERS[tier]['access'])}")
        print(f"Max daily: {SIGNAL_TIERS[tier]['max_daily']} signals")
        print()
    
    print("\n=== CONFIGURED PAIRS ===")
    for i, pair in enumerate(["EURUSD", "GBPUSD", "USDJPY", "USDCHF", 
                             "AUDUSD", "USDCAD", "NZDUSD", "EURGBP"], 1):
        session = SESSION_SCHEDULE.get(pair, {})
        print(f"{i}. {pair} - Best hours: {session.get('start', 'Any')}-{session.get('end', 'Any')} UTC")