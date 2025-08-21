#!/usr/bin/env python3
"""
Enqueue fire commands to IPC queue for command_router
"""
import zmq
import os
import json

QUEUE_ADDR = os.getenv("BITTEN_QUEUE_ADDR", "ipc:///tmp/bitten_cmdqueue")
_ctx = None
_push = None

def enqueue_fire(cmd: dict):
    """Send fire command to IPC queue"""
    global _ctx, _push
    if _ctx is None:
        _ctx = zmq.Context.instance()
        _push = _ctx.socket(zmq.PUSH)
        _push.connect(QUEUE_ADDR)
        _push.setsockopt(zmq.LINGER, 0)
    _push.send_json(cmd)
    return True

def create_fire_command(mission_id: str, user_id: str, symbol: str = None, direction: str = None, 
                       entry: float = None, sl: float = None, tp: float = None, lot: float = 0.01) -> dict:
    """Create fire command for queue with dynamic SL/TP adjustment for late entry"""
    
    # If called with just mission_id and user_id, load from mission file
    if symbol is None or direction is None or entry is None or sl is None or tp is None or sl == 0 or tp == 0:
        mission_file = f"/root/HydraX-v2/missions/{mission_id}.json"
        if os.path.exists(mission_file):
            with open(mission_file, 'r') as f:
                mission_data = json.load(f)
                signal = mission_data.get('signal', mission_data)
                
                # Extract values from mission
                symbol = symbol or signal.get('symbol')
                direction = direction or signal.get('direction', '').upper()
                entry = entry or float(signal.get('entry_price', 0))
                
                # Get SL/TP or calculate from pips if missing
                if sl is None or sl == 0:
                    sl = float(signal.get('stop_loss', 0) or signal.get('sl', 0))
                if tp is None or tp == 0:
                    tp = float(signal.get('take_profit', 0) or signal.get('tp', 0))
                    
                # If still missing, calculate from pips
                if (sl == 0 or tp == 0) and entry > 0:
                    stop_pips = float(signal.get('stop_pips', 10))
                    target_pips = float(signal.get('target_pips', 20))
                    
                    # Determine pip size
                    if 'JPY' in symbol:
                        pip_size = 0.01
                    elif symbol == 'XAUUSD':
                        pip_size = 0.10
                    else:
                        pip_size = 0.0001
                    
                    # Calculate SL/TP based on direction
                    if direction == 'BUY':
                        sl = sl if sl > 0 else entry - (stop_pips * pip_size)
                        tp = tp if tp > 0 else entry + (target_pips * pip_size)
                    else:  # SELL
                        sl = sl if sl > 0 else entry + (stop_pips * pip_size)
                        tp = tp if tp > 0 else entry - (target_pips * pip_size)
    
    # Look up the correct target_uuid from the database for this user
    import sqlite3
    try:
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()
        cursor.execute("SELECT target_uuid FROM ea_instances WHERE user_id = ? ORDER BY last_seen DESC LIMIT 1", (user_id,))
        result = cursor.fetchone()
        target_uuid = result[0] if result else "COMMANDER_DEV_001"  # Fallback to default
        conn.close()
    except Exception:
        target_uuid = "COMMANDER_DEV_001"  # Fallback if DB lookup fails
    
    # CRITICAL FIX: Adjust SL/TP for late entry to maintain risk-reward ratio
    pip_size = 0.01 if 'JPY' in symbol else 0.0001
    original_sl_pips = abs(entry - sl) / pip_size
    original_tp_pips = abs(tp - entry) / pip_size
    
    # Get current market price (simulated - in production would get real price)
    # For now, assume we're entering at the original entry price
    # But calculate what the adjustment would be if we entered late
    current_market_price = entry  # Placeholder - real implementation would get live price
    
    # Calculate price movement since signal
    price_movement_pips = abs(current_market_price - entry) / pip_size
    
    # Adjust SL/TP to maintain original pip distances from CURRENT price
    if direction.upper() == "BUY":
        adjusted_sl = current_market_price - (original_sl_pips * pip_size)
        adjusted_tp = current_market_price + (original_tp_pips * pip_size)
    else:  # SELL
        adjusted_sl = current_market_price + (original_sl_pips * pip_size)
        adjusted_tp = current_market_price - (original_tp_pips * pip_size)
    
    print(f"🔧 LATE ENTRY FIX: {symbol} {direction}")
    print(f"   Original entry: {entry}")
    print(f"   Current price: {current_market_price} (moved {price_movement_pips:.1f}p)")
    print(f"   Adjusted SL: {adjusted_sl} ({original_sl_pips:.1f}p from current)")
    print(f"   Adjusted TP: {adjusted_tp} ({original_tp_pips:.1f}p from current)")
    
    # Use adjusted levels
    sl = adjusted_sl
    tp = adjusted_tp
    
    # Round lot size to 2 decimal places for MT5 compatibility
    lot = round(lot, 2)
    
    return {
        "type": "fire",
        "fire_id": mission_id,
        "target_uuid": target_uuid,
        "symbol": symbol,
        "direction": direction,
        "entry": current_market_price,  # Current market price as entry
        "sl": sl,        # Adjusted SL maintaining pip distance
        "tp": tp,        # Adjusted TP maintaining pip distance 
        "lot": lot,
        "user_id": user_id
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python3 enqueue_fire.py <mission_id> <user_id>")
        sys.exit(1)
    
    mission_id = sys.argv[1]
    user_id = sys.argv[2]
    
    print(f"🔥 Fire command: {mission_id} for user {user_id}")
    
    try:
        # Load mission file
        mission_file = f"/root/HydraX-v2/missions/{mission_id}.json"
        if not os.path.exists(mission_file):
            raise Exception(f"Mission file not found: {mission_file}")
        
        with open(mission_file, 'r') as f:
            mission_data = json.load(f)
        
        # Extract signal data
        signal = mission_data.get('signal', mission_data)
        
        # Validate required fields
        symbol = signal.get('symbol')
        direction = signal.get('direction', '').upper()
        entry_price = float(signal.get('entry_price', 0))
        sl_price = float(signal.get('stop_loss', 0) or signal.get('sl', 0))
        tp_price = float(signal.get('take_profit', 0) or signal.get('tp', 0))
        
        if not all([symbol, direction, entry_price, sl_price, tp_price]):
            raise Exception(f"Missing required signal data: symbol={symbol}, direction={direction}, entry={entry_price}, sl={sl_price}, tp={tp_price}")
        
        # Calculate lot size based on 5% risk
        # Get stop loss distance - calculate from actual prices for accuracy
        entry_price = float(signal.get('entry_price', 0))
        stop_loss = float(signal.get('stop_loss', 0))
        
        # Calculate actual pip distance based on symbol
        if symbol == 'XAUUSD':
            # For XAUUSD, 1 pip = 0.01 price movement
            stop_pips = abs(entry_price - stop_loss) / 0.01
        elif 'JPY' in symbol:
            # For JPY pairs, 1 pip = 0.01 price movement
            stop_pips = abs(entry_price - stop_loss) / 0.01
        else:
            # For other pairs, 1 pip = 0.0001 price movement
            stop_pips = abs(entry_price - stop_loss) / 0.0001
        
        # Get pip value based on symbol (value of 1 pip movement per standard lot)
        pip_value = 10.0  # Default pip value for majors (EURUSD, GBPUSD, etc.)
        if 'JPY' in symbol:
            pip_value = 9.5  # Approximate for JPY pairs
        elif symbol == 'XAUUSD':
            # For XAUUSD, 1 pip (0.01 movement) = $1 per standard lot
            pip_value = 1.0  # Gold pip value per standard lot
        
        # Calculate risk amount (5% of balance)
        # Get user's actual balance from database - REQUIRED
        import sqlite3
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()
        cursor.execute("SELECT last_balance FROM ea_instances WHERE user_id = ? ORDER BY last_seen DESC LIMIT 1", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            print(f"❌ ERROR: No balance found for user {user_id}")
            sys.exit(1)
        
        balance = float(result[0])
        risk_amount = balance * 0.05  # 5% risk
        
        print(f"💰 Account balance: ${balance:.2f}")
        print(f"📊 Risk amount (5%): ${risk_amount:.2f}")
        
        # Calculate lot size: Risk Amount / (Stop Loss in Pips × Pip Value per Lot)
        if stop_pips > 0:
            calculated_lot = risk_amount / (stop_pips * pip_value)
            calculated_lot = round(calculated_lot, 2)  # Round to 2 decimals for MT5
            # Ensure minimum lot size
            calculated_lot = max(calculated_lot, 0.01)
        else:
            calculated_lot = 0.01  # Minimum lot size if can't calculate
        
        fire_cmd = create_fire_command(
            mission_id=mission_id,
            user_id=user_id,
            symbol=symbol,
            direction=direction,
            entry=entry_price,
            sl=sl_price,
            tp=tp_price,
            lot=calculated_lot
        )
        
        print(f"📋 Fire command created: {fire_cmd['symbol']} {fire_cmd['direction']} @ {fire_cmd['entry']}")
        print(f"   SL: {fire_cmd['sl']} | TP: {fire_cmd['tp']} | Lot: {fire_cmd['lot']}")
        
        enqueue_fire(fire_cmd)
        print(f"✅ Fire command queued successfully")
        
    except Exception as e:
        print(f"❌ Fire command failed: {e}")
        sys.exit(1)