#!/usr/bin/env python3
"""
Exit profiles for different tier strategies
Implements Beginner, Plus, and Pro exit management
"""

import toml
import time
import logging
from typing import Dict, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass

from .symbols import (
    price_to_pips, price_plus_pips, be_offset_pips, 
    spread_pips, calculate_trail_distance, normalize_price
)
from .state_store import state_store, Position, PositionState
from .command_bus import command_bus
from .entitlement import entitlement_manager
from .timers import PositionTimer

logger = logging.getLogger(__name__)

# Load tier configurations
TIER_CONFIG_PATH = Path("/root/HydraX-v2/config/tiers.toml")
TIER_CONFIG = toml.load(TIER_CONFIG_PATH) if TIER_CONFIG_PATH.exists() else {}

@dataclass
class MarketData:
    """Current market data for a symbol"""
    bid: float
    ask: float
    spread: float
    atr: Optional[float] = None

class ExitProfileManager:
    """
    Manages exit strategies based on user tier
    Core logic for position lifecycle management
    """
    
    def __init__(self):
        self.tier_configs = TIER_CONFIG
        
    def on_tick(self, ticket: int, market: MarketData) -> bool:
        """
        Process tick for a position
        Main entry point for exit management
        
        Args:
            ticket: Position ticket
            market: Current market data
            
        Returns:
            True if action was taken
        """
        # Get position with lock
        lock = state_store.get_or_create_lock(ticket)
        with lock:
            pos = state_store.get_position(ticket)
            if not pos or pos.state == PositionState.CLOSED:
                return False
            
            # Get tier configuration
            tier_config = self._get_tier_config(pos.user_tier)
            if not tier_config:
                logger.error(f"No config for tier {pos.user_tier}")
                return False
            
            # Route to appropriate handler
            if pos.user_tier == "TIER_BEGINNER":
                return self._handle_beginner_tick(pos, market, tier_config)
            elif pos.user_tier in ["TIER_PLUS", "TIER_PRO"]:
                return self._handle_plus_pro_tick(pos, market, tier_config)
            
            return False
    
    def _get_tier_config(self, tier: str) -> Dict:
        """Get configuration for a tier with inheritance"""
        config = self.tier_configs.get(tier, {})
        
        # Handle inheritance
        if "INHERIT" in config:
            parent_config = self.tier_configs.get(config["INHERIT"], {})
            # Merge parent and child configs
            merged = parent_config.copy()
            merged.update(config)
            return merged
        
        return config
    
    def _handle_beginner_tick(self, pos: Position, market: MarketData, 
                             config: Dict) -> bool:
        """
        Handle Beginner tier: Fixed RR, no partials, time-boxed
        """
        # Check if target RR reached
        if self._check_rr_reached(pos, market, config["RR"]):
            logger.info(f"Beginner {pos.ticket} reached {config['RR']}R target")
            
            # Close full position
            seq = state_store.get_next_seq(pos.ticket)
            command_bus.close_all(
                ticket=pos.ticket,
                fire_id=pos.fire_id,
                seq=seq,
                reason=f"TARGET_{config['RR']}R"
            )
            
            state_store.close_position(pos.ticket)
            PositionTimer.cancel_position_timer(pos.ticket)
            return True
        
        return False
    
    def _handle_plus_pro_tick(self, pos: Position, market: MarketData, 
                              config: Dict) -> bool:
        """
        Handle Plus/Pro tier: Scalp core + runner with partials and trailing
        """
        action_taken = False
        
        # Check TP1 milestone
        if not pos.tp1_done and self._check_rr_reached(pos, market, config["TP1_R"]):
            logger.info(f"Plus/Pro {pos.ticket} reached TP1 at {config['TP1_R']}R")
            
            # Check idempotency
            if state_store.check_milestone_idempotent(pos.ticket, "TP1"):
                # Partial close
                seq = state_store.get_next_seq(pos.ticket)
                command_bus.partial_close(
                    ticket=pos.ticket,
                    fire_id=pos.fire_id,
                    seq=seq,
                    close_pct=config["TP1_CLOSE_PCT"],
                    milestone="TP1"
                )
                
                # Update position state
                remaining_lots = pos.lot_size * (1 - config["TP1_CLOSE_PCT"])
                state_store.update_position(
                    pos.ticket,
                    tp1_done=True,
                    lot_remaining=remaining_lots,
                    state=PositionState.TP1_DONE
                )
                
                # Move to BE if configured
                if config.get("MOVE_BE_AT") == "TP1":
                    self._move_to_breakeven(pos, market)
                
                # Start trailing if enabled
                if config.get("TRAIL_ENABLED", False):
                    self._start_trailing(pos, market, config)
                
                # Cancel max hold timer since we hit TP1
                PositionTimer.cancel_position_timer(pos.ticket)
                
                action_taken = True
        
        # Check if trailing stop should be adjusted
        if pos.trail_on and pos.tp1_done:
            action_taken = self._update_trailing_stop(pos, market, config) or action_taken
        
        return action_taken
    
    def _check_rr_reached(self, pos: Position, market: MarketData, 
                         target_r: float) -> bool:
        """
        Check if position has reached target R multiple
        Uses correct bid/ask side for evaluation
        """
        # Calculate target price
        target_pips = pos.r_pips * target_r
        
        # Use correct market side
        if pos.direction.upper() == "BUY":
            # For longs, use bid to check profit
            current_price = market.bid
            target_price = price_plus_pips(
                pos.symbol, pos.entry_px, "BUY", target_pips
            )
            return current_price >= target_price
        else:
            # For shorts, use ask to check profit
            current_price = market.ask
            target_price = price_plus_pips(
                pos.symbol, pos.entry_px, "SELL", target_pips
            )
            return current_price <= target_price
    
    def _move_to_breakeven(self, pos: Position, market: MarketData) -> bool:
        """Move stop loss to breakeven with appropriate offset"""
        if pos.be_set:
            return False
        
        # Calculate BE offset
        current_spread = spread_pips(pos.symbol, market.bid, market.ask)
        offset = be_offset_pips(pos.symbol, current_spread)
        
        # Calculate BE price
        if pos.direction.upper() == "BUY":
            be_price = price_plus_pips(pos.symbol, pos.entry_px, "BUY", offset)
        else:
            be_price = price_plus_pips(pos.symbol, pos.entry_px, "SELL", -offset)
        
        be_price = normalize_price(pos.symbol, be_price)
        
        # Send modify command
        seq = state_store.get_next_seq(pos.ticket)
        command_bus.modify_sl(
            ticket=pos.ticket,
            fire_id=pos.fire_id,
            seq=seq,
            new_sl=be_price,
            milestone="BE_AFTER_TP1"
        )
        
        # Update position
        state_store.update_position(
            pos.ticket,
            be_set=True,
            sl_current_px=be_price,
            state=PositionState.BE_SET
        )
        
        logger.info(f"Moved {pos.ticket} to BE at {be_price} (offset {offset:.1f} pips)")
        return True
    
    def _start_trailing(self, pos: Position, market: MarketData, 
                       config: Dict) -> bool:
        """Start trailing stop after TP1"""
        if pos.trail_on:
            return False
        
        # Calculate trail distance
        method = config.get("TRAIL_METHOD", "STEP")
        if method == "ATR" and market.atr:
            distance = calculate_trail_distance(pos.symbol, market.atr, "ATR")
        else:
            distance = config.get("TRAIL_STEP_PIPS", 20)
        
        # Send trail command
        seq = state_store.get_next_seq(pos.ticket)
        command_bus.start_trail(
            ticket=pos.ticket,
            fire_id=pos.fire_id,
            seq=seq,
            method=method,
            distance_pips=distance
        )
        
        # Update position
        state_store.update_position(
            pos.ticket,
            trail_on=True,
            state=PositionState.TRAILING
        )
        
        logger.info(f"Started {method} trailing for {pos.ticket} at {distance:.1f} pips")
        return True
    
    def _update_trailing_stop(self, pos: Position, market: MarketData, 
                              config: Dict) -> bool:
        """Update trailing stop if price has moved favorably"""
        # This would be handled by the EA's trailing logic
        # We just track the state here
        return False
    
    def on_position_open(self, ticket: int, fire_id: str, user_id: str,
                        symbol: str, direction: str, entry_px: float,
                        sl_px: float, tp_px: float, lot_size: float) -> bool:
        """
        Called when a new position is opened
        Sets up initial state and timers
        """
        # Get user tier
        user_tier = entitlement_manager.get_user_tier(user_id)
        
        # Calculate risk in pips
        r_pips = price_to_pips(symbol, entry_px, sl_px)
        
        # Create position in state store
        pos = state_store.create_position(
            ticket=ticket,
            fire_id=fire_id,
            user_id=user_id,
            user_tier=user_tier,
            symbol=symbol,
            direction=direction,
            entry_px=entry_px,
            sl_px=sl_px,
            tp_px=tp_px,
            r_pips=r_pips,
            lot_size=lot_size
        )
        
        # Set max hold timer
        def timer_callback(t: int, f: str, reason: str):
            """Callback when timer expires"""
            self.on_timer_expired(t, f, reason)
        
        PositionTimer.set_max_hold_timer(
            ticket=ticket,
            fire_id=fire_id,
            tier=user_tier,
            callback=timer_callback
        )
        
        logger.info(f"Position {ticket} opened: {symbol} {direction} @ {entry_px}, tier={user_tier}")
        return True
    
    def on_timer_expired(self, ticket: int, fire_id: str, reason: str):
        """
        Called when position timer expires
        Closes position if TP1 not reached (for Plus/Pro)
        """
        pos = state_store.get_position(ticket)
        if not pos or pos.state == PositionState.CLOSED:
            return
        
        # For Beginner, always close
        # For Plus/Pro, only close if TP1 not reached
        if pos.user_tier == "TIER_BEGINNER" or not pos.tp1_done:
            logger.info(f"Timer expired for {ticket}: {reason}, closing position")
            
            seq = state_store.get_next_seq(ticket)
            command_bus.close_all(
                ticket=ticket,
                fire_id=fire_id,
                seq=seq,
                reason=reason
            )
            
            state_store.close_position(ticket)
        else:
            logger.info(f"Timer expired for {ticket} but TP1 reached, position continues")
    
    def on_position_closed(self, ticket: int):
        """Called when position is closed"""
        state_store.close_position(ticket)
        PositionTimer.cancel_position_timer(ticket)
        logger.info(f"Position {ticket} closed")

# Singleton instance
exit_profile_manager = ExitProfileManager()