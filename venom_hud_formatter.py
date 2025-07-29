#!/usr/bin/env python3
"""
VENOM HUD Formatter - Converts engine output to HUD-compatible format
CRITICAL: Only adds price calculations, never changes engine logic
"""

import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_current_price(symbol: str) -> float:
    """Get current market price from tick data - fallback to reasonable defaults"""
    try:
        # Try to get real tick data
        tick_file = f"/tmp/ea_raw_data.json"
        with open(tick_file, 'r') as f:
            data = json.load(f)
            if symbol in data:
                return float(data[symbol].get('bid', get_fallback_price(symbol)))
    except:
        pass
    
    # Fallback to reasonable current prices
    return get_fallback_price(symbol)

def get_fallback_price(symbol: str) -> float:
    """Fallback prices for common pairs"""
    fallback_prices = {
        'EURUSD': 1.0900,
        'GBPUSD': 1.2800,
        'USDJPY': 155.00,
        'GBPJPY': 198.40,
        'EURJPY': 169.00,
        'GBPCHF': 1.1200,
        'EURGBP': 0.8500,
        'AUDUSD': 0.6650,
        'NZDUSD': 0.6100,
        'USDCAD': 1.3800,
        'USDCHF': 0.8750,
        'GBPAUD': 1.9250,
        'EURAUD': 1.6400,
        'GBPNZD': 2.1000,
        'AUDJPY': 103.00
    }
    return fallback_prices.get(symbol, 1.0000)

def get_pip_value(symbol: str) -> float:
    """Get pip value for symbol"""
    if 'JPY' in symbol:
        return 0.01  # JPY pairs
    else:
        return 0.0001  # Standard pairs

def convert_venom_to_hud_format(venom_signal: dict) -> dict:
    """
    Convert VENOM engine output to HUD-compatible format
    Input: {target_pips, stop_pips, symbol, direction, ...}
    Output: {entry_price, stop_loss, take_profit, enhanced_signal, ...}
    """
    try:
        # Extract VENOM data (don't modify this!)
        symbol = venom_signal.get('symbol', 'EURUSD')
        direction = venom_signal.get('direction', 'BUY')
        target_pips = venom_signal.get('target_pips', 20)
        stop_pips = venom_signal.get('stop_pips', 10)
        signal_id = venom_signal.get('signal_id', 'VENOM_DEFAULT')
        
        # Get current market price
        current_price = get_current_price(symbol)
        pip_value = get_pip_value(symbol)
        
        # Calculate actual price levels
        if direction.upper() == 'BUY':
            entry_price = current_price
            stop_loss = current_price - (stop_pips * pip_value)
            take_profit = current_price + (target_pips * pip_value)
        else:  # SELL
            entry_price = current_price
            stop_loss = current_price + (stop_pips * pip_value)
            take_profit = current_price - (target_pips * pip_value)
        
        # Create HUD-compatible mission format
        hud_mission = {
            # Keep all original VENOM data
            **venom_signal,
            
            # Add required HUD fields
            'mission_id': signal_id,
            'signal': {
                'id': signal_id,
                'symbol': symbol,
                'direction': direction,
                'entry_price': round(entry_price, 5),
                'stop_loss': round(stop_loss, 5),
                'take_profit': round(take_profit, 5),
                'tcs_score': venom_signal.get('confidence', 85),
                'signal_type': venom_signal.get('signal_type', 'RAPID_ASSAULT'),
                'risk_reward_ratio': round(target_pips / stop_pips, 2),
                'stop_loss_pips': stop_pips,
                'take_profit_pips': target_pips,
                'countdown_minutes': 35  # Standard VENOM timing
            },
            
            # Mission metadata
            'mission': {
                'title': f"⚡ {venom_signal.get('signal_type', 'RAPID_ASSAULT')} - {symbol}",
                'description': f"VENOM v7 Signal - {direction} @ {venom_signal.get('confidence', 85)}%",
                'urgency': 'HIGH' if venom_signal.get('confidence', 85) >= 90 else 'MEDIUM',
                'tactical_notes': [
                    f"🐍 VENOM v7.0 Engine: {venom_signal.get('confidence', 85)}% confidence",
                    f"🛡️ CITADEL Shield: {venom_signal.get('shield_score', 6.0)}/10",
                    f"⚡ Target: {target_pips} pips | Risk: {stop_pips} pips"
                ]
            },
            
            # User context (demo values - will be replaced by actual user data)
            'user': {
                'id': 'demo_user',
                'tier': 'COMMANDER',
                'stats': {
                    'last_7d_pips': 0.0,
                    'win_rate': 84.3,
                    'trades_today': 0,
                    'total_fires': 0,
                    'streak_days': 0,
                    'rank': 'VENOM_OPERATIVE',
                    'last_fire_time': 'Never'
                }
            },
            
            # Account context
            'account': {
                'balance': 10000.0,
                'equity': 10000.0,
                'margin_free': 9900.0,
                'currency': 'USD'
            },
            
            # Timing
            'timing': {
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now().replace(second=0, microsecond=0) + 
                              timedelta(minutes=35)).isoformat(),
                'time_remaining': 35 * 60
            },
            
            # Enhanced signal (required by HUD)
            'enhanced_signal': {
                'symbol': symbol,
                'direction': direction,
                'entry_price': round(entry_price, 5),
                'stop_loss': round(stop_loss, 5),
                'take_profit': round(take_profit, 5),
                'risk_reward_ratio': round(target_pips / stop_pips, 2),
                'signal_type': venom_signal.get('signal_type', 'RAPID_ASSAULT'),
                'tcs_score': venom_signal.get('confidence', 85),
                'volume': 1.0,
                'comment': f"VENOM_{signal_id}"
            }
        }
        
        logger.info(f"✅ Converted VENOM signal {signal_id} to HUD format: {symbol} {direction} @ {entry_price}")
        return hud_mission
        
    except Exception as e:
        logger.error(f"❌ Error converting VENOM signal to HUD format: {e}")
        # Return original signal if conversion fails
        return venom_signal

def process_venom_mission_file(mission_file_path: str):
    """
    Process a VENOM mission file and convert it to HUD format
    This is a safe wrapper that only adds formatting
    """
    try:
        # Read original VENOM mission
        with open(mission_file_path, 'r') as f:
            venom_data = json.load(f)
        
        # Convert to HUD format
        hud_data = convert_venom_to_hud_format(venom_data)
        
        # Save back to same file (HUD compatible)
        with open(mission_file_path, 'w') as f:
            json.dump(hud_data, f, indent=2)
            
        logger.info(f"✅ Processed mission file: {mission_file_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error processing mission file {mission_file_path}: {e}")
        return False

if __name__ == "__main__":
    # Test the formatter
    test_venom_signal = {
        "signal_id": "VENOM_UNFILTERED_EURUSD_TEST001",
        "symbol": "EURUSD",
        "direction": "BUY",
        "confidence": 89,
        "shield_score": 7.5,
        "shield_class": "SHIELD_ACTIVE",
        "signal_type": "RAPID_ASSAULT",
        "target_pips": 24,
        "stop_pips": 12,
        "risk_reward": 2.0,
        "timestamp": 1753674000,
        "source": "VENOM_CITADEL_LIVE"
    }
    
    print("=== TESTING VENOM HUD FORMATTER ===")
    hud_format = convert_venom_to_hud_format(test_venom_signal)
    print(f"Original: target_pips={test_venom_signal['target_pips']}, stop_pips={test_venom_signal['stop_pips']}")
    print(f"HUD Format: entry_price={hud_format['enhanced_signal']['entry_price']}")
    print(f"HUD Format: stop_loss={hud_format['enhanced_signal']['stop_loss']}")
    print(f"HUD Format: take_profit={hud_format['enhanced_signal']['take_profit']}")
    print("✅ Conversion successful!")