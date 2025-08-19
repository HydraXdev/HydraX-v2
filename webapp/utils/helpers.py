"""
Utility functions for BITTEN webapp
Extracted from webapp_server_optimized.py for better modularity
"""

import sqlite3
from contextlib import contextmanager
import json
import logging

logger = logging.getLogger(__name__)

# Database connection helper
@contextmanager
def get_bitten_db():
    """Database connection context manager"""
    conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def pip_size(symbol):
    """Calculate pip size for a given symbol"""
    s = symbol.upper()
    if s.endswith("JPY"): 
        return 0.01
    if s.startswith("XAU"): 
        return 0.1
    if s.startswith("XAG"): 
        return 0.01
    return 0.0001

def calculate_sl_tp(symbol, side, entry, stop_pips, target_pips):
    """Calculate absolute stop loss and take profit from pips"""
    pip = pip_size(symbol)
    
    if side.upper() == "BUY":
        sl = entry - (stop_pips * pip) if stop_pips > 0 else 0
        tp = entry + (target_pips * pip) if target_pips > 0 else 0
    elif side.upper() == "SELL":
        sl = entry + (stop_pips * pip) if stop_pips > 0 else 0
        tp = entry - (target_pips * pip) if target_pips > 0 else 0
    else:
        sl = tp = 0
    
    return round(sl, 6), round(tp, 6)

def get_user_tier(user_id):
    """Get user tier from database"""
    try:
        with get_bitten_db() as conn:
            result = conn.execute(
                'SELECT tier FROM users WHERE user_id = ?',
                (str(user_id),)
            ).fetchone()
            
            if result:
                return result['tier']
            
            # Default tier if user not found
            return 'GRUNT' if str(user_id) != '7176191872' else 'COMMANDER'
    except Exception as e:
        logger.error(f"Error getting user tier: {e}")
        return 'GRUNT'

def get_user_balance(user_id):
    """Get user's latest balance from EA instances"""
    try:
        with get_bitten_db() as conn:
            result = conn.execute('''
                SELECT last_balance, last_equity, last_seen
                FROM ea_instances 
                WHERE user_id = ? 
                ORDER BY last_seen DESC 
                LIMIT 1
            ''', (str(user_id),)).fetchone()
            
            if result:
                return {
                    'balance': result['last_balance'],
                    'equity': result['last_equity'],
                    'last_seen': result['last_seen']
                }
            return None
    except Exception as e:
        logger.error(f"Error getting user balance: {e}")
        return None

def is_user_auto(user_id):
    """Check if user is in AUTO fire mode"""
    # For now, commander is always in auto mode
    if str(user_id) == '7176191872':
        return True
    return False

def get_signal_class(pattern_type):
    """Classify signal as RAPID or SNIPER based on pattern type"""
    rapid_patterns = ['VCB_BREAKOUT', 'SWEEP_RETURN']
    sniper_patterns = ['LIQUIDITY_SWEEP_REVERSAL', 'ORDER_BLOCK_BOUNCE', 'FAIR_VALUE_GAP_FILL']
    
    if pattern_type in rapid_patterns:
        return 'RAPID'
    elif pattern_type in sniper_patterns:
        return 'SNIPER'
    else:
        return 'UNKNOWN'

def can_user_fire(user_id, signal_class):
    """Check if user tier allows firing this signal class"""
    tier = get_user_tier(user_id)
    
    # COMMANDER can fire everything
    if tier == 'COMMANDER':
        return True
    
    # RAPID signals available to all tiers
    if signal_class == 'RAPID':
        return True
    
    # SNIPER signals require PRO or higher
    if signal_class == 'SNIPER':
        return tier in ['PRO', 'ELITE', 'COMMANDER']
    
    return False