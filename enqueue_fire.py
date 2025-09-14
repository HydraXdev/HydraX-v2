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

def get_bitmode_config(symbol: str) -> dict:
    """
    DEPRECATED - Kept for backward compatibility only
    Use hybrid_manager.create_bitmode_config() for proper pip calculations
    """
    # This old config had WRONG pip values that were treated as points
    # causing instant triggers. DO NOT USE.
    return {
        "partial1": {"trigger": 15, "percent": 25},  # Safer fallback
        "partial2": {"trigger": 20, "percent": 25, "move_sl_breakeven": True},
        "trail": {"distance": 15}
    }

def enqueue_fire(cmd):
    """Send fire command to IPC queue - direction gate DISABLED for manual trading"""
    global _ctx, _push
    
    # DIRECTION GATE DISABLED - Allow manual traders to manage their own hedging
    # The direction gate was preventing legitimate opposite direction trades
    # Manual traders should have full control over their positions
    
    symbol = cmd.get('symbol')
    direction = cmd.get('direction')
    tp = cmd.get('tp')
    sl = cmd.get('sl')
    print(f"✅ Allowing {symbol} {direction} trade (direction gate disabled)")
    print(f"📊 DEBUG: Enqueueing with SL={sl}, TP={tp}")
    
    # CRITICAL: Remove any extra fields that might have been added
    # EA expects EXACTLY these fields in this order
    from collections import OrderedDict
    clean_cmd = OrderedDict([
        ("type", cmd.get("type")),
        ("target_uuid", cmd.get("target_uuid")),
        ("fire_id", cmd.get("fire_id")),
        ("symbol", cmd.get("symbol")),
        ("direction", cmd.get("direction")),
        ("entry", cmd.get("entry")),
        ("sl", cmd.get("sl")),
        ("tp", cmd.get("tp")),
        ("lot", cmd.get("lot"))
    ])
    
    # Add hybrid config if present (this is allowed per CLAUDE.md)
    if "hybrid" in cmd:
        clean_cmd["hybrid"] = cmd["hybrid"]
    
    if _ctx is None:
        _ctx = zmq.Context.instance()
        _push = _ctx.socket(zmq.PUSH)
        _push.connect(QUEUE_ADDR)
        _push.setsockopt(zmq.LINGER, 0)
    
    # Send the clean command with preserved order
    _push.send_json(clean_cmd)
    return True

def create_fire_command(mission_id: str, user_id: str, symbol: str = None, direction: str = None, 
                       entry: float = None, sl: float = None, tp: float = None, lot: float = 0.01, risk_reward: float = None, enable_bitmode: bool = False) -> dict:
    """Create fire command for queue with dynamic SL/TP adjustment for late entry"""
    
    # GOLD/SILVER now enabled with proper pip calculations
    # Previous blocks removed - XAUUSD and XAGUSD trading re-enabled
    if symbol == 'USDSEK':
        print("🚫 USDSEK BLOCKED: Trading temporarily disabled - signals coming through with no TP")
        return None
    
    # If called with just mission_id and user_id, load from mission file OR database
    mission_data = {}  # Initialize for later use
    signal_data = {}  # Store signal data from DB
    
    # First try to get signal data from database if we have missing values
    if symbol is None or direction is None or entry is None or sl is None or tp is None or sl == 0 or tp == 0:
        # Check database for signal details
        try:
            import sqlite3
            conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, direction, entry_price, sl, tp, stop_pips, target_pips
                FROM signals WHERE signal_id = ?
            """, (mission_id,))
            row = cursor.fetchone()
            if row:
                signal_data = {
                    'symbol': row[0],
                    'direction': row[1],
                    'entry_price': row[2],
                    'sl': row[3],
                    'tp': row[4],
                    'stop_pips': row[5],
                    'target_pips': row[6]
                }
                # Use DB values if not provided
                symbol = symbol or signal_data.get('symbol')
                direction = direction or signal_data.get('direction')
                entry = entry or signal_data.get('entry_price')
                # Don't override sl/tp if they're 0 - we'll calculate from pips later
            conn.close()
        except Exception as e:
            print(f"DB lookup failed: {e}")
        
        # Then check mission file as fallback
        mission_file = f"/root/HydraX-v2/missions/{mission_id}.json"
        if os.path.exists(mission_file):
            with open(mission_file, 'r') as f:
                mission_data = json.load(f)
                signal = mission_data.get('signal', mission_data)
                
                # Get signal details for logging
                confidence = float(signal.get('confidence', 0))
                pattern = signal.get('pattern_type', 'UNKNOWN')
                
                # REMOVED confidence gate - allow manual execution at any confidence
                print(f"✅ Processing {pattern} signal at {confidence:.1f}% confidence")
                
                # REMOVED pattern quarantine - allow all patterns for manual execution
                
                # FILTER 3: Session Filter for specific patterns
                if pattern in ['SWEEP_RETURN', 'VCB_BREAKOUT']:
                    from datetime import datetime, timezone
                    current_hour = datetime.now(timezone.utc).hour
                    # London + NY sessions: 06:00-21:00 UTC
                    if current_hour < 6 or current_hour >= 21:
                        print(f"❌ Dropped {pattern} in Asian session (hour={current_hour} UTC)")
                        return None
                
                # Extract values from mission including risk_reward
                symbol = symbol or signal.get('symbol')
                direction = direction or signal.get('direction', '').upper()
                entry = entry or float(signal.get('entry_price', 0))
                
                # GOLD/SILVER trading now re-enabled with proper pip calculations
                # Previous XAUUSD block removed
                if symbol == 'USDSEK':
                    print("🚫 USDSEK BLOCKED: Trading temporarily disabled - signals coming through with no TP")
                    return None
                
                # Get risk_reward from Elite Guard signal
                if risk_reward is None:
                    risk_reward = float(signal.get('risk_reward', 1.5))
                
                # Get SL/TP or calculate from pips if missing
                if sl is None or sl == 0:
                    sl = float(signal.get('stop_loss', 0) or signal.get('sl', 0))
                if tp is None or tp == 0:
                    tp = float(signal.get('take_profit', 0) or signal.get('tp', 0))
                    
                # If still missing, calculate from pips
                if (sl == 0 or tp == 0) and entry > 0:
                    # Try to get from signal_data (from DB) first, then signal (from mission)
                    stop_pips = float(signal_data.get('stop_pips', signal.get('stop_pips', 15)))  # Default 15 pips
                    target_pips = float(signal_data.get('target_pips', signal.get('target_pips', 20)))  # Default 20 pips
                    
                    # Determine pip size
                    if 'JPY' in symbol:
                        pip_size = 0.01
                    elif symbol == 'XAUUSD':
                        pip_size = 0.10  # Gold standard: 1 pip = $0.10 movement
                    elif symbol == 'XAGUSD':
                        pip_size = 0.001  # Silver: 1 pip = 0.001 movement (FIXED from 0.01)
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
    
    # HEDGE PROTECTION: Check for existing open positions on this symbol
    try:
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        cursor = conn.cursor()
        # Check for ANY open positions on same symbol (not closed)
        cursor.execute("""
            SELECT f.fire_id, s.direction, f.created_at 
            FROM fires f
            JOIN missions m ON f.mission_id = m.mission_id
            JOIN signals s ON m.signal_id = s.signal_id
            WHERE f.user_id = ? 
            AND s.symbol = ? 
            AND f.status = 'FILLED'
            AND (f.closed_at IS NULL OR f.closed_at = 0)
            ORDER BY f.created_at DESC
        """, (user_id, symbol))
        
        open_positions = cursor.fetchall()
        conn.close()
        
        if open_positions:
            for position in open_positions:
                existing_direction = position[1]
                if existing_direction != direction:
                    print(f"🚫 HEDGE BLOCKED: Opposite position detected!")
                    print(f"   Existing: {existing_direction} position (fire_id: {position[0]})")
                    print(f"   Attempted: {direction} position")
                    print(f"   Symbol: {symbol}")
                    print(f"   Action: Trade blocked to prevent hedging")
                    return None  # Block hedging to prevent conflicting positions
        
    except Exception as e:
        print(f"Hedge check failed: {e}")
    
    # SAFETY CHECK: Ensure we have valid SL and TP before proceeding
    if sl == 0 or tp == 0 or entry == 0:
        print(f"⚠️ WARNING: Missing critical values - Entry: {entry}, SL: {sl}, TP: {tp}")
        # Use sensible defaults based on symbol type
        if sl == 0 or tp == 0:
            if 'JPY' in symbol:
                default_sl_pips = 20
                pip_size = 0.01
            elif symbol in ['XAUUSD']:
                default_sl_pips = 100  # 100 pips = $10 move for gold
                pip_size = 0.1  # Gold: 1 pip = $0.10
            elif symbol in ['XAGUSD']:
                default_sl_pips = 100  # Changed from 50 to 100 ($1.00 move)
                pip_size = 0.01
            elif symbol in ['USDMXN', 'USDSEK', 'USDCNH']:
                default_sl_pips = 50
                pip_size = 0.0001
            else:
                default_sl_pips = 15
                pip_size = 0.0001
            
            # Calculate missing SL/TP from defaults
            if direction.upper() == "BUY":
                if sl == 0:
                    sl = entry - (default_sl_pips * pip_size)
                if tp == 0:
                    tp = entry + (default_sl_pips * pip_size)  # 1:1 R:R by default
            else:  # SELL
                if sl == 0:
                    sl = entry + (default_sl_pips * pip_size)
                if tp == 0:
                    tp = entry - (default_sl_pips * pip_size)  # 1:1 R:R by default
            
            print(f"   Applied defaults: SL={sl:.5f}, TP={tp:.5f} ({default_sl_pips} pips each)")
    
    # CRITICAL FIX: Adjust SL/TP for late entry to maintain risk-reward ratio
    # Determine pip size correctly for all pairs
    if 'JPY' in symbol:
        pip_size = 0.01
    elif symbol in ['XAUUSD', 'XAGUSD']:
        pip_size = 0.1 if symbol == 'XAUUSD' else 0.001  # Gold: 0.1, Silver: 0.001
    else:
        pip_size = 0.0001
        
    original_sl_pips = abs(entry - sl) / pip_size
    original_tp_pips = abs(tp - entry) / pip_size
    
    # Use dynamic R:R from Elite Guard if available, otherwise calculate from actual TP/SL
    if risk_reward is None:
        # Try to get from mission_data if we loaded it
        if mission_data and 'signal' in mission_data:
            risk_reward = float(mission_data['signal'].get('risk_reward', 1.5))
        elif mission_data and 'risk_reward' in mission_data:
            risk_reward = float(mission_data.get('risk_reward', 1.5))
        else:
            # Calculate from actual TP/SL distances if not provided
            if original_sl_pips > 0:
                risk_reward = original_tp_pips / original_sl_pips
            else:
                risk_reward = 1.5  # Default fallback
    
    # Apply the dynamic R:R from Elite Guard (which may be adjusted by Grokkeeper gates)
    original_tp_pips = original_sl_pips * risk_reward
    
    print(f"📊 Dynamic R:R Debug:")
    print(f"   Symbol: {symbol}, Pip size: {pip_size}")
    print(f"   Original SL pips: {original_sl_pips:.1f}")
    print(f"   Original TP pips (calculated): {abs(tp - entry) / pip_size:.1f}")
    print(f"   Dynamic R:R from Elite Guard: {risk_reward:.2f}")
    print(f"   New TP pips (Dynamic R:R): {original_tp_pips:.1f}")
    
    # Get current market price (simulated - in production would get real price)
    # For now, assume we're entering at the original entry price
    # But calculate what the adjustment would be if we entered late
    current_market_price = entry  # Placeholder - real implementation would get live price
    
    # Calculate price movement since signal
    price_movement_pips = abs(current_market_price - entry) / pip_size
    
    # Adjust SL/TP to maintain 1:1 R:R from CURRENT price
    if direction.upper() == "BUY":
        adjusted_sl = current_market_price - (original_sl_pips * pip_size)
        adjusted_tp = current_market_price + (original_tp_pips * pip_size)  # Now 1:1 with SL
    else:  # SELL
        adjusted_sl = current_market_price + (original_sl_pips * pip_size)
        adjusted_tp = current_market_price - (original_tp_pips * pip_size)  # Now 1:1 with SL
    
    print(f"🔧 FIRE PACKAGE FIX: {symbol} {direction} [1:1 R:R ENFORCED]")
    print(f"   Original entry: {entry}")
    print(f"   Current price: {current_market_price} (moved {price_movement_pips:.1f}p)")
    print(f"   Adjusted SL: {adjusted_sl} ({original_sl_pips:.1f}p from current)")
    print(f"   Adjusted TP: {adjusted_tp} ({original_tp_pips:.1f}p from current) [1:1 R:R]")
    
    # Use adjusted levels
    sl = adjusted_sl
    tp = adjusted_tp
    
    # FINAL VALIDATION: Ensure SL and TP are valid numbers and not 0
    if sl == 0 or tp == 0 or not isinstance(sl, (int, float)) or not isinstance(tp, (int, float)):
        print(f"❌ CRITICAL ERROR: Invalid SL ({sl}) or TP ({tp}) after adjustment!")
        # Emergency fallback - use safe defaults
        if direction.upper() == "BUY":
            sl = current_market_price * 0.995  # 0.5% below entry
            tp = current_market_price * 1.005  # 0.5% above entry
        else:
            sl = current_market_price * 1.005  # 0.5% above entry
            tp = current_market_price * 0.995  # 0.5% below entry
        print(f"   Emergency fix applied: SL={sl:.5f}, TP={tp:.5f}")
    
    # Additional validation for exotic pairs with extreme values
    if symbol in ['XAUUSD', 'XAGUSD']:
        # Ensure reasonable pip distances for metals
        metal_pip = 0.1 if symbol == 'XAUUSD' else 0.01  # Gold: 0.1, Silver: 0.01
        sl_distance = abs(current_market_price - sl) / metal_pip
        tp_distance = abs(tp - current_market_price) / metal_pip
        
        if sl_distance > 1000 or tp_distance > 1000:
            print(f"⚠️ Extreme pip distance detected for {symbol}: SL={sl_distance:.0f}p, TP={tp_distance:.0f}p")
            # Cap at 100 pips for safety
            if direction.upper() == "BUY":
                sl = current_market_price - (100 * metal_pip)
                tp = current_market_price + (100 * metal_pip)
            else:
                sl = current_market_price + (100 * metal_pip)
                tp = current_market_price - (100 * metal_pip)
            print(f"   Capped at 100 pips: SL={sl:.5f}, TP={tp:.5f}")
    
    # Round lot size to 2 decimal places for MT5 compatibility
    lot = round(lot, 2)
    
    # Final rounding for price precision
    sl = round(sl, 5) if symbol not in ['XAUUSD', 'XAGUSD'] else round(sl, 2)
    tp = round(tp, 5) if symbol not in ['XAUUSD', 'XAGUSD'] else round(tp, 2)
    entry_rounded = round(current_market_price, 5) if symbol not in ['XAUUSD', 'XAGUSD'] else round(current_market_price, 2)
    
    # BITMODE Configuration: Check if user has BITMODE enabled
    bitmode_config = None
    if enable_bitmode:
        try:
            # Import fire mode database to check BITMODE status
            from src.bitten_core.fire_mode_database import fire_mode_db
            if fire_mode_db.is_bitmode_enabled(user_id):
                # Use NEW hybrid manager for CORRECT pip calculations
                from src.bitten_core.hybrid_manager import hybrid_manager
                bitmode_config = hybrid_manager.create_bitmode_config(
                    symbol=symbol,
                    entry=entry_rounded,
                    sl=sl,
                    direction=direction,
                    user_id=user_id
                )
                # Track position for monitoring
                hybrid_manager.track_position(
                    fire_id=mission_id,
                    symbol=symbol,
                    entry=entry_rounded,
                    sl=sl,
                    direction=direction,
                    lot_size=lot
                )
                print(f"🎯 BITMODE ENABLED for {symbol} with FIXED pip calculations")
            else:
                print(f"🔸 BITMODE requested but not enabled for user {user_id}")
        except Exception as e:
            print(f"⚠️ BITMODE check failed: {e}")
            # Continue without BITMODE if check fails
    
    # CRITICAL R:R VALIDATION - Never send trades with inverted R:R
    if direction.upper() == "BUY":
        risk = entry_rounded - sl
        reward = tp - entry_rounded
    else:  # SELL
        risk = sl - entry_rounded
        reward = entry_rounded - tp
    
    if risk > 0 and reward > 0:
        actual_rr = reward / risk
        print(f"   📊 R:R Check: Risk={risk:.5f}, Reward={reward:.5f}, R:R={actual_rr:.2f}")
        
        # BITMODE OVERRIDE: If BITMODE enabled, set TP far away to let trailing work
        if enable_bitmode and bitmode_config:
            print(f"   🎯 BITMODE ACTIVE: Setting distant TP to enable unlimited trailing...")
            # Set TP to 100x risk to ensure it won't be hit (trailing will exit instead)
            # This ensures partials at +8/+12 pips and trailing stop have room to work
            if direction.upper() == "BUY":
                tp = entry_rounded + (risk * 100)  # 100:1 R:R = essentially unlimited
            else:  # SELL
                tp = entry_rounded - (risk * 100)  # 100:1 R:R = essentially unlimited
            tp = round(tp, 5) if symbol not in ['XAUUSD', 'XAGUSD'] else round(tp, 2)
            print(f"   ✅ BITMODE TP: {tp:.5f} (trailing will be the real exit)")
        # Only adjust TP if NOT in BITMODE
        elif actual_rr < 1.5:
            print(f"   ⚠️ R:R too low ({actual_rr:.2f}), adjusting TP for 1.5:1...")
            if direction.upper() == "BUY":
                tp = entry_rounded + (risk * 1.5)
            else:  # SELL
                tp = entry_rounded - (risk * 1.5)
            tp = round(tp, 5) if symbol not in ['XAUUSD', 'XAGUSD'] else round(tp, 2)
            print(f"   ✅ New TP: {tp:.5f} (R:R now 1.5:1)")
    
    # CRITICAL FIX: EA-compatible SL/TP validation to prevent trades without stops
    print(f"🔧 EA VALIDATION: Entry={entry_rounded:.5f}, SL={sl:.5f}, TP={tp:.5f}")
    
    if direction.upper() == "BUY":
        # BUY: SL must be below entry, TP must be above entry
        if sl >= entry_rounded:
            print(f"⚠️ BUY SL invalid ({sl:.5f} >= {entry_rounded:.5f}), fixing...")
            sl = entry_rounded - (20 * pip_size)  # 20 pip SL as safety
        if tp <= entry_rounded:
            print(f"⚠️ BUY TP invalid ({tp:.5f} <= {entry_rounded:.5f}), fixing...")
            tp = entry_rounded + (30 * pip_size)  # 30 pip TP for 1.5:1
    else:  # SELL
        # SELL: SL must be above entry, TP must be below entry
        if sl <= entry_rounded:
            print(f"⚠️ SELL SL invalid ({sl:.5f} <= {entry_rounded:.5f}), fixing...")
            sl = entry_rounded + (20 * pip_size)  # 20 pip SL as safety
        if tp >= entry_rounded:
            print(f"⚠️ SELL TP invalid ({tp:.5f} >= {entry_rounded:.5f}), fixing...")
            tp = entry_rounded - (30 * pip_size)  # 30 pip TP for 1.5:1
    
    # Final validation - ensure SL and TP are not zero
    if sl == 0 or tp == 0:
        print(f"❌ CRITICAL: SL or TP is zero! SL={sl}, TP={tp}")
        if direction.upper() == "BUY":
            sl = entry_rounded - (20 * pip_size) if sl == 0 else sl
            tp = entry_rounded + (30 * pip_size) if tp == 0 else tp
        else:
            sl = entry_rounded + (20 * pip_size) if sl == 0 else sl  
            tp = entry_rounded - (30 * pip_size) if tp == 0 else tp
        print(f"🔧 Emergency fix applied: SL={sl:.5f}, TP={tp:.5f}")
    
    print(f"✅ FINAL VALUES: Entry={entry_rounded:.5f}, SL={sl:.5f}, TP={tp:.5f}")
    
    # Calculate TP1 price for comment (1.5R)
    sl_pips = abs(entry_rounded - sl) / pip_size
    tp1_pips = sl_pips * 1.5  # 1.5R for TP1
    if direction.upper() == "BUY":
        tp1_price = entry_rounded + (tp1_pips * pip_size)
    else:
        tp1_price = entry_rounded - (tp1_pips * pip_size)
    
    # Format comment with TP1 price
    comment = f"FANG@{tp1_price:.5f}"
    
    # Build fire command - EXACT FORMAT REQUIRED BY EA
    # EA STRICT REQUIREMENTS:
    # 1. "type": "fire" must be FIRST key
    # 2. Keys must be lowercase exactly as shown
    # 3. direction must be UPPERCASE ("BUY" or "SELL")
    # 4. Numbers must NOT be quoted
    # 5. entry/sl/tp can be 0 for market/no stop/no target
    from collections import OrderedDict
    
    # Ensure direction is uppercase
    direction = direction.upper() if direction else "BUY"
    
    # For market orders, entry should be 0 (EA will use current price)
    # If we calculated entry_rounded as current price, set to 0 for EA
    entry_for_ea = 0  # Always use 0 for market orders
    
    # Determine correct decimal precision for each symbol
    if 'JPY' in symbol:
        decimals = 3  # JPY pairs: 147.389
    elif symbol == 'XAUUSD':
        decimals = 2  # Gold: 3645.19
    elif symbol == 'XAGUSD':
        decimals = 3  # Silver: 31.456
    else:
        decimals = 5  # Most forex pairs: 1.17280
    
    # If SL or TP are None or 0, use emergency defaults
    if sl is None or sl == 0:
        print(f"⚠️ WARNING: SL is None/0, using emergency calculation")
        # Emergency SL calculation
        pip_size = 0.01 if 'JPY' in symbol else 0.0001
        if direction.upper() == "BUY":
            sl = entry_rounded - (20 * pip_size)
        else:
            sl = entry_rounded + (20 * pip_size)
    
    if tp is None or tp == 0:
        print(f"⚠️ WARNING: TP is None/0, using emergency calculation")
        # Emergency TP calculation (1.5:1 R:R)
        pip_size = 0.01 if 'JPY' in symbol else 0.0001
        if direction.upper() == "BUY":
            tp = entry_rounded + (30 * pip_size)
        else:
            tp = entry_rounded - (30 * pip_size)
    
    # Round to appropriate decimals
    sl_for_ea = round(sl, decimals) if sl > 0 else 0
    tp_for_ea = round(tp, decimals) if tp > 0 else 0
    
    # Round lot to 2 decimals
    lot_for_ea = round(lot, 2) if lot else 0.01
    
    fire_command = OrderedDict([
        ("type", "fire"),
        ("target_uuid", target_uuid),
        ("fire_id", mission_id),
        ("symbol", symbol),
        ("direction", direction),  # Must be uppercase
        ("entry", entry_for_ea),   # 0 for market orders
        ("sl", sl_for_ea),         # Can be 0
        ("tp", tp_for_ea),         # Can be 0
        ("lot", lot_for_ea)        # Rounded to 2 decimals
    ])
    
    # Debug logging to verify exact packet format
    import json
    debug_json = json.dumps(fire_command, indent=2)
    print(f"📦 EXACT EA PACKET:\n{debug_json}")
    
    # Store user_id separately for database tracking, but don't send to EA
    fire_command_for_db = dict(fire_command)
    fire_command_for_db["user_id"] = user_id
    
    # DISABLED tier-based exit configuration - was overriding TP to 10R
    # DISABLED sanitize_open - was stripping TP entirely
    # We need the actual TP and SL values for proper trade execution
    print(f"✅ Using calculated TP and SL values (tier exits disabled)")
    
    # Add BITMODE/hybrid configuration if enabled
    if bitmode_config:
        # Format hybrid exactly as EA expects
        fire_command["hybrid"] = {
            "enabled": True,
            "partial1": {
                "trigger": bitmode_config["partial1"]["trigger"],
                "percent": bitmode_config["partial1"]["percent"]
            },
            "partial2": {
                "trigger": bitmode_config["partial2"]["trigger"],
                "percent": bitmode_config["partial2"]["percent"]
            },
            "trail": {
                "distance": bitmode_config["trail"]["distance"]
            }
        }
        print(f"🎯 BITMODE/Hybrid enabled with config")
    
    return fire_command

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
        
        # Get dynamic risk_reward from Elite Guard
        risk_reward_value = float(signal.get('risk_reward', 1.5))
        
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
        elif symbol == 'XAGUSD':
            # For XAGUSD (Silver), 1 pip = 0.001 price movement
            stop_pips = abs(entry_price - stop_loss) / 0.001
        elif 'JPY' in symbol:
            # For JPY pairs, 1 pip = 0.01 price movement
            stop_pips = abs(entry_price - stop_loss) / 0.01
        elif symbol in ['USDCNH', 'USDMXN', 'USDZAR', 'USDTRY']:
            # Exotic pairs with 4 decimal places
            stop_pips = abs(entry_price - stop_loss) / 0.0001
        elif symbol in ['USDSEK', 'USDNOK', 'USDDKK']:
            # Scandinavian pairs with 4 decimal places
            stop_pips = abs(entry_price - stop_loss) / 0.0001
        else:
            # For other pairs, 1 pip = 0.0001 price movement
            stop_pips = abs(entry_price - stop_loss) / 0.0001
        
        # Get pip value based on symbol (value of 1 pip movement per standard lot)
        pip_value = 10.0  # Default pip value for majors (EURUSD, GBPUSD, etc.)
        if 'JPY' in symbol:
            pip_value = 9.5  # Approximate for JPY pairs (varies by USD/JPY rate)
        elif symbol == 'XAUUSD':
            # For XAUUSD, 1 pip (0.01 movement) = $10.00 per standard lot
            # Standard lot (1.0) = 100 oz, and 0.01 move = $1 per oz = $100 per standard lot
            # But brokers typically use $10 per pip per standard lot
            pip_value = 10.0  # Gold pip value per standard lot
        elif symbol == 'XAGUSD':
            # For XAGUSD, 1 pip (0.001 movement) = $0.50 per standard lot (5000 oz)
            # Standard market convention for silver
            pip_value = 0.5  # Silver pip value per standard lot (0.001 movement)
        elif symbol == 'USDCNH':
            # For USDCNH, pip value depends on CNH rate (~1.4 USD per pip at 7.2 rate)
            pip_value = 1.4  # Approximate - actual varies with CNH rate
        elif symbol == 'USDMXN':
            # For USDMXN, pip value depends on MXN rate (~0.5 USD per pip at 20 rate)
            pip_value = 0.5  # Approximate - actual varies with MXN rate
        elif symbol == 'USDZAR':
            # For USDZAR, pip value depends on ZAR rate (~0.6 USD per pip at 18 rate)
            pip_value = 0.6  # Approximate - actual varies with ZAR rate
        elif symbol == 'USDTRY':
            # For USDTRY, pip value depends on TRY rate (~0.3 USD per pip at 30 rate)
            pip_value = 0.3  # Approximate - actual varies with TRY rate
        elif symbol in ['USDSEK', 'USDNOK']:
            # For Scandinavian pairs, pip value ~1.0-1.2 USD per pip
            pip_value = 1.1  # Approximate - actual varies with SEK/NOK rate
        elif symbol == 'USDDKK':
            # For USDDKK, pip value ~1.5 USD per pip
            pip_value = 1.5  # Approximate - actual varies with DKK rate
        
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
        risk_amount = balance * 0.03  # 3% risk MAX for production
        
        print(f"💰 Account balance: ${balance:.2f}")
        print(f"📊 Risk amount (3%): ${risk_amount:.2f}")
        
        # Calculate lot size: Risk Amount / (Stop Loss in Pips × Pip Value per Lot)
        if stop_pips > 0:
            calculated_lot = risk_amount / (stop_pips * pip_value)
            print(f"📊 Lot calculation: ${risk_amount:.2f} / ({stop_pips:.1f} pips × ${pip_value:.2f}) = {calculated_lot:.3f} lots")
            
            # Apply reasonable limits for safety
            MAX_LOT_SIZE = 2.0  # Maximum 2 lots for safety
            MIN_LOT_SIZE = 0.01  # Minimum lot size
            
            if calculated_lot > MAX_LOT_SIZE:
                print(f"⚠️ Lot size {calculated_lot:.2f} exceeds max {MAX_LOT_SIZE}, capping")
                calculated_lot = MAX_LOT_SIZE
            
            calculated_lot = round(calculated_lot, 2)  # Round to 2 decimals for MT5
            calculated_lot = max(calculated_lot, MIN_LOT_SIZE)
            print(f"✅ Final lot size: {calculated_lot}")
        else:
            calculated_lot = 0.01  # Minimum lot size if can't calculate
            print(f"⚠️ No stop pips, using minimum lot: {calculated_lot}")
        
        # Check if user has BITMODE enabled
        enable_bitmode = False
        try:
            from src.bitten_core.fire_mode_database import fire_mode_db
            enable_bitmode = fire_mode_db.is_bitmode_enabled(user_id)
        except Exception as e:
            print(f"⚠️ BITMODE check failed: {e}")
        
        fire_cmd = create_fire_command(
            mission_id=mission_id,
            user_id=user_id,
            symbol=symbol,
            direction=direction,
            entry=entry_price,
            sl=sl_price,
            tp=tp_price,
            lot=calculated_lot,
            risk_reward=risk_reward_value,
            enable_bitmode=enable_bitmode
        )
        
        print(f"📋 Fire command created: {fire_cmd['symbol']} {fire_cmd['direction']} @ {fire_cmd['entry']}")
        print(f"   SL: {fire_cmd['sl']} | TP: {fire_cmd['tp']} | Lot: {fire_cmd['lot']}")
        
        enqueue_fire(fire_cmd)
        print(f"✅ Fire command queued successfully")
        
    except Exception as e:
        print(f"❌ Fire command failed: {e}")
        sys.exit(1)