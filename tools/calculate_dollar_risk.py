#!/usr/bin/env python3
"""
Calculate actual dollar risk/reward based on user's real balance
"""

import sqlite3
import json

def get_user_balance(user_id: str) -> float:
    """Get user's actual account balance from EA data"""
    try:
        conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
        cur = conn.cursor()
        
        # Get latest balance from EA instances
        result = cur.execute("""
            SELECT last_balance, last_equity
            FROM ea_instances
            WHERE user_id = ?
            ORDER BY last_seen DESC
            LIMIT 1
        """, (user_id,)).fetchone()
        
        conn.close()
        
        if result and result[0]:
            return float(result[0])  # Use balance
    except:
        pass
    
    # Default balance if not found
    return 1000.0

def calculate_position_size(balance: float, risk_percent: float, stop_pips: float, symbol: str) -> float:
    """Calculate position size based on risk"""
    
    # Risk amount in dollars
    risk_amount = balance * (risk_percent / 100)
    
    # Pip value per standard lot
    if "JPY" in symbol:
        pip_value_per_lot = 1000 / 147  # Approximate USD/JPY rate
    elif symbol.startswith("XAU"):
        pip_value_per_lot = 10
    else:
        pip_value_per_lot = 10  # Standard forex
    
    # Calculate lot size
    if stop_pips > 0:
        lot_size = risk_amount / (stop_pips * pip_value_per_lot)
        # Clamp to reasonable range
        lot_size = max(0.01, min(lot_size, 1.0))
    else:
        lot_size = 0.01
    
    return round(lot_size, 2)

def calculate_dollar_amounts(user_id: str, symbol: str, stop_pips: float, target_pips: float, 
                           risk_percent: float = 2.0) -> dict:
    """Calculate actual dollar risk and reward for user"""
    
    # Get user's balance
    balance = get_user_balance(user_id)
    
    # Calculate position size
    lot_size = calculate_position_size(balance, risk_percent, stop_pips, symbol)
    
    # Calculate pip value for this position
    if "JPY" in symbol:
        pip_value_per_lot = 1000 / 147
    elif symbol.startswith("XAU"):
        pip_value_per_lot = 10
    else:
        pip_value_per_lot = 10
    
    pip_value = pip_value_per_lot * lot_size
    
    # Calculate dollar amounts
    risk_dollars = stop_pips * pip_value
    reward_dollars = target_pips * pip_value
    
    return {
        'balance': balance,
        'lot_size': lot_size,
        'risk_dollars': round(risk_dollars, 2),
        'reward_dollars': round(reward_dollars, 2),
        'risk_percent': risk_percent,
        'pip_value': round(pip_value, 2)
    }

def format_alert_with_dollars(event_data: dict, user_id: str = None) -> str:
    """Format alert with accurate dollar calculations"""
    
    symbol = event_data.get('symbol', 'EURUSD')
    stop_pips = float(event_data.get('stop_pips', 0))
    target_pips = float(event_data.get('target_pips', 0))
    
    # Get dollar amounts
    if user_id:
        amounts = calculate_dollar_amounts(user_id, symbol, stop_pips, target_pips)
    else:
        # Use defaults for group alerts
        amounts = {
            'risk_dollars': stop_pips * 1,  # $1 per pip default
            'reward_dollars': target_pips * 1,
            'lot_size': 0.01
        }
    
    # Format message
    return {
        'risk_text': f"${amounts['risk_dollars']:.0f} risk",
        'reward_text': f"${amounts['reward_dollars']:.0f} reward",
        'lot_size': amounts['lot_size'],
        'full_text': f"💰 Risk ${amounts['risk_dollars']:.0f} ({stop_pips:.0f}p) → Reward ${amounts['reward_dollars']:.0f} ({target_pips:.0f}p)"
    }

def mask_price(price: float, decimals_to_mask: int = 2) -> str:
    """Mask last digits of price for privacy"""
    price_str = f"{price:.5f}"
    
    if '.' in price_str:
        parts = price_str.split('.')
        if len(parts[1]) >= decimals_to_mask:
            masked = parts[0] + '.' + parts[1][:-decimals_to_mask] + 'X' * decimals_to_mask
        else:
            masked = parts[0] + '.XXX'
    else:
        masked = str(price)[:-decimals_to_mask] + 'X' * decimals_to_mask if len(str(price)) > decimals_to_mask else 'XXX'
    
    return masked

def format_sl_tp_with_privacy(entry: float, sl: float, tp: float, show_partial: bool = True) -> dict:
    """Format SL/TP with privacy masking"""
    
    if show_partial:
        # Show first part, mask last 2-3 digits
        return {
            'entry': mask_price(entry, 2),
            'sl': mask_price(sl, 2),
            'tp': mask_price(tp, 2)
        }
    else:
        # Full privacy - only show existence
        return {
            'entry': '•••••',
            'sl': 'Protected',
            'tp': 'Protected'
        }

if __name__ == "__main__":
    # Test with commander user
    test_event = {
        'symbol': 'EURUSD',
        'stop_pips': 20,
        'target_pips': 40,
        'entry_price': 1.0845
    }
    
    result = calculate_dollar_amounts('7176191872', 'EURUSD', 20, 40)
    print(f"Balance: ${result['balance']}")
    print(f"Lot Size: {result['lot_size']}")
    print(f"Risk: ${result['risk_dollars']}")
    print(f"Reward: ${result['reward_dollars']}")
    
    # Test price masking
    masked = mask_price(1.08456)
    print(f"Masked price: {masked}")