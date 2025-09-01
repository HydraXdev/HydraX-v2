#!/usr/bin/env python3
"""
Integration module for tiered exit system
Bridges the new exit profiles with existing BITTEN infrastructure
"""

import json
import logging
from typing import Dict, Optional

from .exit_profiles import exit_profile_manager, MarketData
from .entitlement import entitlement_manager
from .symbols import normalize_price
from .diagnostics.sentry import sentry

logger = logging.getLogger(__name__)

def integrate_with_enqueue_fire():
    """
    Modify enqueue_fire.py to use tiered exit system
    This function shows how to integrate with existing fire command creation
    """
    integration_code = '''
# Add to enqueue_fire.py create_fire_command() function:

# Import tiered exit system
from src.bitten_core.entitlement import entitlement_manager
from src.bitten_core.exit_profiles import exit_profile_manager

# Get user tier
user_tier = entitlement_manager.get_user_tier(user_id)

# Configure fire command based on tier
if user_tier == "TIER_BEGINNER":
    # Fixed 1.5R target, no hybrid
    fire_command["exit_mode"] = "FIXED"
    fire_command["target_r"] = 1.5
    fire_command["hybrid"] = None  # No partials/trailing
    
elif user_tier in ["TIER_PLUS", "TIER_PRO"]:
    # Scalp + runner with hybrid management
    fire_command["exit_mode"] = "HYBRID_SCALP_RUNNER"
    fire_command["tier"] = user_tier
    
    # The exit_profiles system will handle the complexity
    # Just mark that this uses tiered exits
    fire_command["use_tiered_exits"] = True

print(f"🎯 Fire command configured for {user_tier}")
'''
    return integration_code

def on_new_position(fire_id: str, ticket: int, user_id: str, 
                   symbol: str, direction: str, entry: float,
                   sl: float, tp: float, lot_size: float):
    """
    Called when a new position is opened
    Registers it with the tiered exit system
    """
    try:
        # Register with exit profile manager
        exit_profile_manager.on_position_open(
            ticket=ticket,
            fire_id=fire_id,
            user_id=user_id,
            symbol=symbol,
            direction=direction,
            entry_px=entry,
            sl_px=sl,
            tp_px=tp,
            lot_size=lot_size
        )
        
        logger.info(f"Position {ticket} registered with tiered exit system")
        return True
        
    except Exception as e:
        logger.error(f"Failed to register position {ticket}: {e}")
        return False

def on_market_tick(ticket: int, bid: float, ask: float, atr: Optional[float] = None):
    """
    Called on each market tick for active positions
    Processes exit logic based on user tier
    """
    try:
        market = MarketData(
            bid=bid,
            ask=ask,
            spread=ask - bid,
            atr=atr
        )
        
        # Process tick through exit profiles
        action_taken = exit_profile_manager.on_tick(ticket, market)
        
        if action_taken:
            logger.info(f"Exit action taken for position {ticket}")
        
        return action_taken
        
    except Exception as e:
        logger.error(f"Failed to process tick for {ticket}: {e}")
        return False

def on_position_closed(ticket: int, exit_price: float, pnl: float):
    """
    Called when a position is closed
    Updates tracking and checks for violations
    """
    try:
        # Notify exit profile manager
        exit_profile_manager.on_position_closed(ticket)
        
        # Check with sentry for bad exits
        from .state_store import state_store
        pos = state_store.get_position(ticket)
        
        if pos:
            # Calculate exit R
            from .symbols import price_to_pips
            
            if pos.direction.upper() == "BUY":
                exit_pips = price_to_pips(pos.symbol, exit_price, pos.entry_px)
            else:
                exit_pips = price_to_pips(pos.symbol, pos.entry_px, exit_price)
            
            exit_r = exit_pips / pos.r_pips if pos.r_pips > 0 else 0
            
            # Check for violations
            sentry.check_bad_exit(ticket, exit_r)
        
        logger.info(f"Position {ticket} closed at {exit_price}, PnL: {pnl}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process position close for {ticket}: {e}")
        return False

def get_tier_status(user_id: str) -> Dict:
    """Get current tier status and configuration for a user"""
    tier = entitlement_manager.get_user_tier(user_id)
    features = entitlement_manager.get_tier_features(tier)
    
    # Get active positions for user
    from .state_store import state_store
    active_positions = state_store.get_active_positions(user_id)
    
    # Get timer status
    from .timers import timer_manager
    active_timers = timer_manager.get_active_timers()
    
    return {
        "user_id": user_id,
        "tier": tier,
        "tier_name": features["name"],
        "features": features["features"],
        "autofire_enabled": features["autofire"],
        "max_concurrent": features["max_concurrent"],
        "active_positions": len(active_positions),
        "positions": [
            {
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "direction": pos.direction,
                "state": pos.state.value,
                "tp1_done": pos.tp1_done,
                "be_set": pos.be_set,
                "trail_on": pos.trail_on,
                "lot_remaining": pos.lot_remaining,
                "timer_remaining": active_timers.get(pos.ticket, {}).get("remaining_seconds", 0)
            }
            for pos in active_positions.values()
        ]
    }

def drive_exits_for_active_positions(quotes: Dict) -> None:
    """
    Hook B - Drive exit FSM for all active positions with current market quotes
    
    Args:
        quotes: Dict of symbol -> {"bid": float, "ask": float}
    """
    try:
        # Get all active positions from state store
        from .state_store import state_store
        active_positions = state_store.get_active_positions()
        
        if not active_positions:
            return
        
        # Process each position
        for ticket, position in active_positions.items():
            # Check if we have quotes for this symbol
            if position.symbol not in quotes:
                continue
                
            quote = quotes[position.symbol]
            if "bid" not in quote or "ask" not in quote:
                continue
            
            # Create market data object
            market = MarketData(
                bid=float(quote["bid"]),
                ask=float(quote["ask"]),
                spread=float(quote["ask"]) - float(quote["bid"]),
                atr=None  # Could add ATR if available
            )
            
            # Drive the exit FSM
            action_taken = exit_profile_manager.on_tick(ticket, market)
            
            if action_taken:
                logger.info(f"🎯 FSM drove exit action for ticket {ticket} on {position.symbol}")
        
        # Check for timeouts (belt-and-suspenders approach)
        _check_position_timeouts()
                
    except Exception as e:
        logger.error(f"Error driving exits: {e}")

def _check_position_timeouts():
    """Check if any positions have exceeded their max hold time"""
    from datetime import datetime
    from .state_store import state_store
    from .command_bus import command_bus
    from .timers import get_timeout_meta, clear_timeout_meta
    
    try:
        active_positions = state_store.get_active_positions()
        
        if active_positions:
            logger.info(f"⏱️ Checking timeouts for {len(active_positions)} positions")
        
        for ticket, pos in active_positions.items():
            # Skip if not in entered state (no TP1 hit yet)
            if pos.state.value != "entered":
                continue
            
            # Get timeout metadata from SQLite
            meta = get_timeout_meta(ticket)
            if not meta:
                logger.debug(f"No timeout metadata for ticket {ticket}")
                continue  # No timeout data
            
            # Parse open timestamp and calculate elapsed time
            open_ts_utc = meta["open_ts_utc"]
            max_hold_min = meta["pre_tp1_max_hold_min"]
            
            # Convert ISO timestamp to datetime (handle both naive and aware)
            open_dt = datetime.fromisoformat(open_ts_utc)
            # Ensure we're comparing same timezone types
            if open_dt.tzinfo is None:
                # Naive datetime - use utcnow()
                now = datetime.utcnow()
            else:
                # Aware datetime - use now with UTC timezone
                from datetime import timezone
                now = datetime.now(timezone.utc)
            elapsed_seconds = (now - open_dt).total_seconds()
            elapsed_minutes = elapsed_seconds / 60.0
            
            logger.info(f"Ticket {ticket}: elapsed={elapsed_minutes:.2f}min, max={max_hold_min}min")
            
            # Check if timeout reached
            if elapsed_minutes >= max_hold_min:
                logger.info(f"⏱️ Position {ticket} exceeded max hold time ({max_hold_min} min, elapsed={elapsed_minutes:.1f} min) - closing")
                
                # Use close_all method from command_bus
                fire_id = getattr(pos, 'fire_id', f'timeout_{ticket}')
                seq = getattr(pos, 'last_seq', 0) + 1
                command_bus.close_all(
                    ticket=ticket,
                    fire_id=fire_id,
                    seq=seq,
                    reason=f"timeout_{max_hold_min}min"
                )
                
                # Clear timeout metadata after closing
                clear_timeout_meta(ticket)
                        
    except Exception as e:
        logger.error(f"Error checking timeouts: {e}")

def check_system_health() -> Dict:
    """Check overall system health and violations"""
    violations = sentry.get_violation_summary()
    
    # Get tier statistics
    stats = entitlement_manager.get_tier_statistics()
    
    # Get active positions by tier
    from .state_store import state_store
    all_positions = state_store.get_active_positions()
    
    positions_by_tier = {
        "TIER_BEGINNER": 0,
        "TIER_PLUS": 0,
        "TIER_PRO": 0
    }
    
    for pos in all_positions.values():
        if pos.user_tier in positions_by_tier:
            positions_by_tier[pos.user_tier] += 1
    
    return {
        "system_enabled": sentry.feature_enabled,
        "violations": violations,
        "tier_statistics": stats,
        "active_positions_by_tier": positions_by_tier,
        "health_status": "OK" if sentry.feature_enabled and violations["bad_exit_streak"] == 0 else "DEGRADED"
    }

# Example usage in existing fire execution
def enhanced_create_fire_command(mission_id: str, user_id: str, symbol: str,
                                direction: str, entry: float, sl: float,
                                tp: float, lot: float) -> Dict:
    """
    Enhanced fire command creation with tiered exit support
    This would replace/enhance the existing create_fire_command
    """
    # Get user tier
    user_tier = entitlement_manager.get_user_tier(user_id)
    tier_features = entitlement_manager.get_tier_features(user_tier)
    
    # Base fire command
    fire_command = {
        "type": "fire",
        "fire_id": mission_id,
        "symbol": symbol,
        "direction": direction,
        "entry": normalize_price(symbol, entry),
        "sl": normalize_price(symbol, sl),
        "lot": round(lot, 2),
        "user_id": user_id
    }
    
    # Configure based on tier
    if user_tier == "TIER_BEGINNER":
        # Simple fixed target
        from .symbols import price_plus_pips, price_to_pips
        
        risk_pips = price_to_pips(symbol, entry, sl)
        target_pips = risk_pips * 1.5  # Fixed 1.5R
        
        if direction.upper() == "BUY":
            tp = price_plus_pips(symbol, entry, "BUY", target_pips)
        else:
            tp = price_plus_pips(symbol, entry, "SELL", target_pips)
        
        fire_command["tp"] = normalize_price(symbol, tp)
        fire_command["exit_strategy"] = "FIXED_SCALP"
        
    else:  # TIER_PLUS or TIER_PRO
        # Set far TP for runner strategy
        from .symbols import price_plus_pips, price_to_pips
        
        risk_pips = price_to_pips(symbol, entry, sl)
        target_pips = risk_pips * 10  # Far target for runner
        
        if direction.upper() == "BUY":
            tp = price_plus_pips(symbol, entry, "BUY", target_pips)
        else:
            tp = price_plus_pips(symbol, entry, "SELL", target_pips)
        
        fire_command["tp"] = normalize_price(symbol, tp)
        fire_command["exit_strategy"] = "SCALP_RUNNER"
        fire_command["use_tiered_exits"] = True
    
    fire_command["user_tier"] = user_tier
    
    logger.info(f"Created {user_tier} fire command for {symbol}")
    return fire_command