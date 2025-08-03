"""
MT5 ZMQ Adapter for BITTEN System
Direct ZMQ socket communication with MT5 EA v7
NO FILE-BASED FALLBACK - ZMQ ONLY
"""

# ┌──────────────────────────────────────────────────────────────┐
# │ BITTEN ZMQ SYSTEM - DO NOT FALL BACK TO FILE/HTTP ROUTES    │
# │ Persistent ZMQ architecture is required                      │
# │ EA v7 connects directly via libzmq.dll to 134.199.204.67    │
# │ All command, telemetry, and feedback must use ZMQ sockets   │
# └──────────────────────────────────────────────────────────────┘

import json
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
import threading
from zmq_bitten_controller import get_bitten_controller, TradeResult

logger = logging.getLogger(__name__)

@dataclass
class ZMQTradeRequest:
    """Trade request format for ZMQ transmission"""
    signal_id: str
    symbol: str
    action: str  # buy or sell
    lot: float
    sl: float = 0
    tp: float = 0
    user_id: str = ""
    comment: str = ""
    
    def to_zmq_payload(self) -> Dict[str, Any]:
        """Convert to ZMQ message format"""
        return {
            "type": "signal",
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "action": self.action.lower(),
            "lot": self.lot,
            "sl": self.sl,
            "tp": self.tp,
            "timestamp": datetime.utcnow().isoformat(),
            "comment": self.comment,
            "user_id": self.user_id
        }

class MT5ZMQAdapter:
    """
    ZMQ-based MT5 adapter - replaces file-based communication
    Uses persistent socket connections for real-time trading
    """
    
    def __init__(self):
        self.controller = None
        self._ensure_controller()
        
        # Track pending trades
        self.pending_trades = {}
        self.trade_results = {}
        
        logger.info("🧠 MT5 ZMQ Adapter initialized - File fallback disabled")
        
    def _ensure_controller(self):
        """Ensure ZMQ controller is running"""
        if not self.controller:
            self.controller = get_bitten_controller()
            logger.info("📡 Connected to BITTEN ZMQ Controller")
            
    def execute_trade(self, symbol: str, direction: str, volume: float, 
                     sl: Optional[float] = None, tp: Optional[float] = None,
                     user_id: str = "", comment: str = "") -> Tuple[bool, str, Optional[Dict]]:
        """
        Execute trade via ZMQ - NO FILE FALLBACK
        
        Returns:
            Tuple of (success, message, result_data)
        """
        if os.getenv("ZMQ_STRICT") == "1":
            # Strict mode - no file operations allowed
            if os.path.exists("/fire.txt") or os.path.exists("/trade_result.txt"):
                raise RuntimeError("❌ File-based execution blocked in ZMQ_STRICT mode")
        
        # Generate unique signal ID
        signal_id = f"ZMQ_{symbol}_{int(time.time() * 1000)}"
        
        # Create ZMQ trade request
        trade_request = ZMQTradeRequest(
            signal_id=signal_id,
            symbol=symbol,
            action=direction.lower(),
            lot=volume,
            sl=sl or 0,
            tp=tp or 0,
            user_id=user_id,
            comment=comment
        )
        
        # Prepare callback for result
        result_event = threading.Event()
        result_data = {"success": False, "message": "Timeout"}
        
        def on_trade_result(result: TradeResult):
            """Callback when trade result received"""
            result_data["success"] = result.status == "success"
            result_data["message"] = result.message
            result_data["ticket"] = result.ticket
            result_data["price"] = result.price
            result_event.set()
        
        # Send via ZMQ with callback
        success = self.controller.send_signal(
            trade_request.to_zmq_payload(),
            callback=on_trade_result
        )
        
        if not success:
            return False, "Failed to send trade signal via ZMQ", None
            
        # Wait for result (with timeout)
        if result_event.wait(timeout=30):  # 30 second timeout
            if result_data["success"]:
                logger.info(f"✅ Trade executed via ZMQ: {signal_id} - Ticket {result_data.get('ticket')}")
                return True, f"Trade executed: Ticket {result_data.get('ticket')}", result_data
            else:
                logger.error(f"❌ Trade failed via ZMQ: {signal_id} - {result_data['message']}")
                return False, result_data["message"], result_data
        else:
            logger.warning(f"⏱️ Trade timeout via ZMQ: {signal_id}")
            return False, "Trade execution timeout", None
            
    def get_account_info(self, user_id: str) -> Optional[Dict]:
        """Get real-time account info from telemetry"""
        telemetry = self.controller.get_user_telemetry(user_id)
        if telemetry:
            return {
                "balance": telemetry.balance,
                "equity": telemetry.equity,
                "margin": telemetry.margin,
                "free_margin": telemetry.free_margin,
                "profit": telemetry.profit,
                "positions": telemetry.positions,
                "last_update": telemetry.last_update.isoformat()
            }
        return None
        
    def close_position(self, symbol: Optional[str] = None) -> Tuple[bool, str]:
        """Close position(s) via ZMQ"""
        success = self.controller.close_positions(symbol)
        if success:
            message = f"Close command sent for {symbol}" if symbol else "Close all command sent"
            return True, message
        else:
            return False, "Failed to send close command"
            
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent trade results"""
        results = self.controller.get_trade_results(limit)
        return [asdict(r) for r in results]
        
    def ping_ea(self) -> bool:
        """Ping EA to check connectivity"""
        return self.controller.send_command("ping")

# Singleton instance
_zmq_adapter = None

def get_mt5_zmq_adapter() -> MT5ZMQAdapter:
    """Get or create singleton MT5 ZMQ adapter"""
    global _zmq_adapter
    if not _zmq_adapter:
        _zmq_adapter = MT5ZMQAdapter()
    return _zmq_adapter

# Import guard for missing os
import os