#!/usr/bin/env python3
"""
Mission & Fire Packet API
Generates mission briefings with fire packets for signals
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

def generate_fire_packet(signal_data: Dict) -> Dict:
    """Generate fire command packet from signal data"""

    # Calculate position sizing (simplified - 2% risk)
    account_balance = 1000.0  # Default, should come from EA
    risk_percent = 0.02

    # Get stop loss distance in pips
    entry = signal_data.get('entry_price', 0)
    sl = signal_data.get('sl', signal_data.get('stop_loss', 0))

    # Calculate pip distance
    symbol = signal_data.get('symbol', '')
    if 'JPY' in symbol:
        pip_size = 0.01
    elif 'XAU' in symbol or 'GOLD' in symbol:
        pip_size = 0.1
    elif 'XAG' in symbol or 'SILVER' in symbol:
        pip_size = 0.001
    else:
        pip_size = 0.0001

    sl_pips = abs(entry - sl) / pip_size if entry and sl else 20

    # Calculate lot size (simplified)
    risk_amount = account_balance * risk_percent
    pip_value = 10.0  # $10 per standard lot per pip
    lot_size = round(risk_amount / (sl_pips * pip_value), 2)
    lot_size = max(0.01, min(lot_size, 1.0))  # Clamp between 0.01 and 1.0

    fire_packet = {
        "type": "fire",
        "fire_id": signal_data.get('signal_id'),
        "target_uuid": "COMMANDER_DEV_001",  # Default EA
        "symbol": symbol,
        "direction": signal_data.get('direction', 'BUY'),
        "entry": entry,
        "sl": sl,
        "tp": signal_data.get('tp', signal_data.get('take_profit', 0)),
        "lot": lot_size,
        "user_id": "7176191872",  # Commander user
        "signal_class": signal_data.get('signal_class', 'RAPID'),
        "pattern_type": signal_data.get('pattern_type', 'UNKNOWN'),
        "confidence": signal_data.get('confidence', 75.0)
    }

    return fire_packet

def generate_mission_brief(signal_id: str) -> Optional[Dict]:
    """Generate complete mission briefing with fire packet"""

    try:
        # Fetch signal from database
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT signal_id, symbol, direction, confidence, entry_price, stop_pips, target_pips,
                   created_at, payload_json, pattern_type
            FROM signals
            WHERE signal_id = ?
        ''', (signal_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Parse signal data
        payload_data = json.loads(row[8]) if row[8] else {}

        # Parse raw values
        symbol = row[1]
        direction = row[2]
        entry_price = float(row[4]) if row[4] else 0.0
        stop_pips = float(row[5]) if row[5] else 0.0
        target_pips = float(row[6]) if row[6] else 0.0

        # Calculate pip size
        if 'JPY' in symbol:
            pip_size = 0.01
        elif 'XAU' in symbol or 'GOLD' in symbol:
            pip_size = 0.1
        elif 'XAG' in symbol or 'SILVER' in symbol:
            pip_size = 0.001
        else:
            pip_size = 0.0001

        # Convert pips to price levels based on direction
        if direction == 'BUY':
            sl_price = entry_price - (stop_pips * pip_size) if entry_price and stop_pips else 0.0
            tp_price = entry_price + (target_pips * pip_size) if entry_price and target_pips else 0.0
        else:  # SELL
            sl_price = entry_price + (stop_pips * pip_size) if entry_price and stop_pips else 0.0
            tp_price = entry_price - (target_pips * pip_size) if entry_price and target_pips else 0.0

        signal_data = {
            'signal_id': row[0],
            'symbol': symbol,
            'direction': direction,
            'confidence': float(row[3]) if row[3] else 75.0,
            'entry_price': entry_price,
            'sl': sl_price,
            'tp': tp_price,
            'stop_pips': stop_pips,
            'target_pips': target_pips,
            'created_at': row[7],
            'pattern_type': row[9] or payload_data.get('pattern_type', 'UNKNOWN'),
            'signal_class': payload_data.get('signal_class', 'RAPID'),
            'timeframe': payload_data.get('timeframe', 'M5')
        }

        # Generate fire packet
        fire_packet = generate_fire_packet(signal_data)

        # Calculate expiry (15 minutes from now)
        expires_at = int(time.time()) + (15 * 60)

        # Build mission brief
        mission = {
            "signal_id": signal_data['signal_id'],
            "mission_type": "RAPID_ASSAULT" if signal_data['signal_class'] == 'RAPID' else "SNIPER_OPS",
            "status": "ACTIVE",
            "symbol": signal_data['symbol'],
            "direction": signal_data['direction'],
            "pattern_type": signal_data['pattern_type'],
            "confidence": signal_data['confidence'],
            "timeframe": signal_data['timeframe'],
            "session": "LONDON",  # Default session

            # Trade levels
            "entry_price": signal_data['entry_price'],
            "stop_loss": signal_data['sl'],
            "take_profit": signal_data['tp'],
            "sl": signal_data['sl'],  # Alias for compatibility
            "tp": signal_data['tp'],  # Alias for compatibility
            "stop_pips": signal_data['stop_pips'],
            "target_pips": signal_data['target_pips'],

            # Fire packet
            "fire_packet": fire_packet,

            # Timing
            "created_at": signal_data['created_at'],
            "expires_at": expires_at,
            "time_remaining": max(0, expires_at - int(time.time())),

            # Mission briefing text
            "briefing": f"""
🎯 {signal_data['pattern_type']} Pattern Detected

📍 Symbol: {signal_data['symbol']}
📊 Direction: {signal_data['direction']}
💯 Confidence: {signal_data['confidence']:.1f}%
⏰ Timeframe: {signal_data['timeframe']}

🎯 TRADE LEVELS:
Entry: {signal_data['entry_price']:.5f}
Stop Loss: {signal_data['sl']:.5f}
Take Profit: {signal_data['tp']:.5f}

⚡ Ready to execute - Fire when ready!
            """.strip(),

            # HUD data
            "hud_url": f"/signal?id={signal_data['signal_id']}",
            "can_fire": True
        }

        return mission

    except Exception as e:
        print(f"❌ Error generating mission brief: {e}")
        return None

def get_mission_api(signal_id: str) -> Dict:
    """API endpoint handler for mission briefings"""
    mission = generate_mission_brief(signal_id)

    if mission:
        return {"success": True, "mission": mission}
    else:
        return {"success": False, "error": "Signal not found"}

if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) > 1:
        signal_id = sys.argv[1]
        result = get_mission_api(signal_id)
        print(json.dumps(result, indent=2))
