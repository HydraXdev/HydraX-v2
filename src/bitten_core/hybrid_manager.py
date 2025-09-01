#!/usr/bin/env python3
"""
BITMODE Hybrid Position Manager - Server Side Controller
Fixes the pips vs points confusion and manages partial closes properly
"""

import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class HybridState(Enum):
    """Position lifecycle states for hybrid management"""
    ENTERED = "entered"
    TP1_DONE = "tp1_done"
    TP2_DONE = "tp2_done"
    TRAILING = "trailing"
    EXITED = "exited"

@dataclass
class SymbolConfig:
    """Symbol-specific configuration for proper pip/point conversion"""
    pip_size: float           # Price value of 1 pip (e.g., 0.0001 for EURUSD)
    points_per_pip: int       # MT5 points in 1 pip (e.g., 10 for 5-digit broker)
    min_stop_distance: int    # Minimum stop distance in pips
    spread_buffer: float      # Extra pips to add for spread protection
    
class HybridManager:
    """
# [DISABLED BITMODE]     Manages BITMODE hybrid position management with proper pip/point conversion
    and state tracking to prevent premature exits
    """
    
    # Symbol configurations with CORRECT pip definitions
    SYMBOL_CONFIGS = {
        "EURUSD": SymbolConfig(0.0001, 10, 5, 2.0),
        "GBPUSD": SymbolConfig(0.0001, 10, 5, 2.0),
        "USDJPY": SymbolConfig(0.01, 10, 5, 2.0),
        "EURJPY": SymbolConfig(0.01, 10, 8, 3.0),
        "GBPJPY": SymbolConfig(0.01, 10, 10, 3.0),
        "USDCHF": SymbolConfig(0.0001, 10, 5, 2.0),
        "USDCAD": SymbolConfig(0.0001, 10, 5, 2.0),
        "AUDUSD": SymbolConfig(0.0001, 10, 5, 2.0),
        "XAUUSD": SymbolConfig(0.1, 10, 20, 5.0),   # Gold: 1 pip = $0.10
        "XAGUSD": SymbolConfig(0.001, 10, 10, 3.0),  # Silver: 1 pip = $0.001
        # Default for unknown symbols
        "DEFAULT": SymbolConfig(0.0001, 10, 5, 2.0)
    }
    
# [DISABLED BITMODE]     # Safe BITMODE configuration with proper R:R milestones
    DEFAULT_CONFIG = {
        "tp1_r": 1.5,          # First partial at 1.5R (not 0.5R!)
        "tp1_pct": 0.25,       # Close 25%
        "tp2_r": 2.0,          # Second partial at 2R
        "tp2_pct": 0.25,       # Close another 25%
        "move_be_at": "TP2",   # Only move to BE after TP2 (not TP1!)
        "be_offset_pips": 3,   # Offset from entry for BE (minimum)
        "trail_enabled": True,
        "trail_method": "FIXED",  # FIXED or ATR
        "trail_distance_pips": 15,  # Reasonable trail distance (not 5!)
        "min_cmd_gap_ms": 500,  # Minimum gap between commands
    }
    
    def __init__(self):
        self.positions: Dict[str, Dict] = {}  # fire_id -> position state
        self.last_command_time: Dict[str, float] = {}  # fire_id -> timestamp
        
    def get_symbol_config(self, symbol: str) -> SymbolConfig:
        """Get configuration for symbol with fallback to default"""
        return self.SYMBOL_CONFIGS.get(symbol, self.SYMBOL_CONFIGS["DEFAULT"])
    
    def pips_to_price(self, symbol: str, entry: float, pips: float, direction: str) -> float:
        """Convert pips to actual price level"""
        config = self.get_symbol_config(symbol)
        pip_value = pips * config.pip_size
        
        if direction.upper() == "BUY":
            return round(entry + pip_value, 5 if config.pip_size < 0.01 else 2)
        else:  # SELL
            return round(entry - pip_value, 5 if config.pip_size < 0.01 else 2)
    
    def price_to_pips(self, symbol: str, price1: float, price2: float) -> float:
        """Calculate pip distance between two prices"""
        config = self.get_symbol_config(symbol)
        return abs(price1 - price2) / config.pip_size
    
    def calculate_hybrid_levels(self, symbol: str, entry: float, sl: float, 
                              direction: str, risk_reward: float = 1.5) -> Dict:
        """
        Calculate proper TP1, TP2, BE levels with correct pip math
        """
        config = self.get_symbol_config(symbol)
        
        # Calculate risk in pips
        risk_pips = self.price_to_pips(symbol, entry, sl)
        
        # Calculate milestone levels based on R:R
        tp1_pips = risk_pips * self.DEFAULT_CONFIG["tp1_r"]  # 1.5R
        tp2_pips = risk_pips * self.DEFAULT_CONFIG["tp2_r"]  # 2.0R
        
        # Calculate actual price levels
        tp1_price = self.pips_to_price(symbol, entry, tp1_pips, direction)
        tp2_price = self.pips_to_price(symbol, entry, tp2_pips, direction)
        
        # BE with proper offset (add spread buffer)
        be_offset_pips = max(
            self.DEFAULT_CONFIG["be_offset_pips"],
            config.spread_buffer,
            config.min_stop_distance
        )
        be_price = self.pips_to_price(symbol, entry, be_offset_pips, direction)
        
        # Trail distance with safety margin
        trail_pips = max(
            self.DEFAULT_CONFIG["trail_distance_pips"],
            config.min_stop_distance + config.spread_buffer
        )
        
        return {
            "tp1_price": tp1_price,
            "tp1_pips": tp1_pips,
            "tp2_price": tp2_price, 
            "tp2_pips": tp2_pips,
            "be_price": be_price,
            "be_offset_pips": be_offset_pips,
            "trail_distance_pips": trail_pips,
            "risk_pips": risk_pips
        }
    
    def create_bitmode_config(self, symbol: str, entry: float, sl: float, 
                            direction: str, user_id: str) -> Dict:
        """
# [DISABLED BITMODE]         Create proper BITMODE configuration for fire command
        This REPLACES the broken configuration in enqueue_fire.py
        """
        levels = self.calculate_hybrid_levels(symbol, entry, sl, direction)
        
        # Build configuration with CORRECT pip values (not points!)
        config = {
            "enabled": True,
            "partial1": {
                "trigger": levels["tp1_pips"],  # In PIPS not points!
                "percent": self.DEFAULT_CONFIG["tp1_pct"] * 100,  # 25%
                "move_sl_breakeven": False  # NOT at TP1!
            },
            "partial2": {
                "trigger": levels["tp2_pips"],  # In PIPS not points!
                "percent": self.DEFAULT_CONFIG["tp2_pct"] * 100,  # 25%
                "move_sl_breakeven": True   # YES at TP2
            },
            "trail": {
                "distance": levels["trail_distance_pips"],  # Reasonable distance
                "enabled": self.DEFAULT_CONFIG["trail_enabled"]
            },
            "be_offset_pips": levels["be_offset_pips"],
            "levels": {
                "tp1_price": levels["tp1_price"],
                "tp2_price": levels["tp2_price"],
                "be_price": levels["be_price"]
            }
        }
        
# [DISABLED BITMODE]         logger.info(f"🎯 BITMODE Config for {symbol} {direction}:")
        logger.info(f"   Entry: {entry:.5f}, SL: {sl:.5f}")
        logger.info(f"   Risk: {levels['risk_pips']:.1f} pips")
        logger.info(f"   TP1: {levels['tp1_price']:.5f} (+{levels['tp1_pips']:.1f} pips @ 1.5R)")
        logger.info(f"   TP2: {levels['tp2_price']:.5f} (+{levels['tp2_pips']:.1f} pips @ 2.0R)")
        logger.info(f"   BE: {levels['be_price']:.5f} (+{levels['be_offset_pips']:.1f} pips offset)")
        logger.info(f"   Trail: {levels['trail_distance_pips']:.1f} pips")
        
        return config
    
    def validate_command_timing(self, fire_id: str) -> bool:
        """Check if enough time has passed since last command"""
        now = time.time() * 1000  # milliseconds
        last = self.last_command_time.get(fire_id, 0)
        
        if now - last < self.DEFAULT_CONFIG["min_cmd_gap_ms"]:
            logger.warning(f"⚠️ Command rate limited for {fire_id}: {now - last:.0f}ms < {self.DEFAULT_CONFIG['min_cmd_gap_ms']}ms")
            return False
            
        self.last_command_time[fire_id] = now
        return True
    
    def track_position(self, fire_id: str, symbol: str, entry: float, 
                      sl: float, direction: str, lot_size: float):
        """Initialize position tracking with proper state"""
        if fire_id not in self.positions:
            levels = self.calculate_hybrid_levels(symbol, entry, sl, direction)
            self.positions[fire_id] = {
                "state": HybridState.ENTERED,
                "symbol": symbol,
                "entry": entry,
                "sl_original": sl,
                "sl_current": sl,
                "direction": direction,
                "lot_size_original": lot_size,
                "lot_size_remaining": lot_size,
                "levels": levels,
                "partials_done": [],
                "created_at": time.time(),
                "events": []
            }
            logger.info(f"📊 Tracking position {fire_id}: {symbol} {direction} @ {entry}")
    
    def should_trigger_tp1(self, fire_id: str, current_price: float) -> bool:
        """Check if TP1 should trigger based on current price"""
        if fire_id not in self.positions:
            return False
            
        pos = self.positions[fire_id]
        if pos["state"] != HybridState.ENTERED:
            return False
            
        tp1_price = pos["levels"]["tp1_price"]
        direction = pos["direction"]
        
        # Check if price has reached TP1
        if direction.upper() == "BUY":
            return current_price >= tp1_price
        else:  # SELL
            return current_price <= tp1_price
    
    def should_trigger_tp2(self, fire_id: str, current_price: float) -> bool:
        """Check if TP2 should trigger based on current price"""
        if fire_id not in self.positions:
            return False
            
        pos = self.positions[fire_id]
        if pos["state"] != HybridState.TP1_DONE:
            return False
            
        tp2_price = pos["levels"]["tp2_price"]
        direction = pos["direction"]
        
        # Check if price has reached TP2
        if direction.upper() == "BUY":
            return current_price >= tp2_price
        else:  # SELL
            return current_price <= tp2_price
    
    def get_partial_command(self, fire_id: str, milestone: str) -> Optional[Dict]:
        """Generate partial close command if conditions are met"""
        if not self.validate_command_timing(fire_id):
            return None
            
        pos = self.positions.get(fire_id)
        if not pos:
            return None
            
        if milestone == "TP1" and pos["state"] == HybridState.ENTERED:
            partial_lots = pos["lot_size_original"] * self.DEFAULT_CONFIG["tp1_pct"]
            pos["state"] = HybridState.TP1_DONE
            pos["partials_done"].append("TP1")
            pos["lot_size_remaining"] -= partial_lots
            
            return {
                "type": "partial_close",
                "fire_id": fire_id,
                "lots": round(partial_lots, 2),
                "milestone": "TP1"
            }
            
        elif milestone == "TP2" and pos["state"] == HybridState.TP1_DONE:
            partial_lots = pos["lot_size_original"] * self.DEFAULT_CONFIG["tp2_pct"]
            pos["state"] = HybridState.TP2_DONE
            pos["partials_done"].append("TP2")
            pos["lot_size_remaining"] -= partial_lots
            
            # Also prepare BE move after TP2
            be_command = {
                "type": "modify_sl",
                "fire_id": fire_id,
                "new_sl": pos["levels"]["be_price"],
                "milestone": "BE_AFTER_TP2"
            }
            
            return {
                "type": "partial_close",
                "fire_id": fire_id,
                "lots": round(partial_lots, 2),
                "milestone": "TP2",
                "follow_up": be_command  # Queue BE move after partial
            }
            
        return None
    
    def get_diagnostic_info(self, fire_id: str) -> Dict:
        """Get diagnostic information for a position"""
        pos = self.positions.get(fire_id)
        if not pos:
            return {"error": "Position not found"}
            
        return {
            "fire_id": fire_id,
            "state": pos["state"].value,
            "symbol": pos["symbol"],
            "entry": pos["entry"],
            "sl_current": pos["sl_current"],
            "direction": pos["direction"],
            "lot_remaining": pos["lot_size_remaining"],
            "partials_done": pos["partials_done"],
            "tp1_price": pos["levels"]["tp1_price"],
            "tp2_price": pos["levels"]["tp2_price"],
            "be_price": pos["levels"]["be_price"],
            "trail_pips": pos["levels"]["trail_distance_pips"],
            "age_seconds": time.time() - pos["created_at"]
        }

# Singleton instance
hybrid_manager = HybridManager()