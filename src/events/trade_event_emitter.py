#!/usr/bin/env python3
"""
Trade Event Emitter
Emits trade lifecycle events to WebSocket clients
"""

import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TradeEventEmitter:
    """Emits trade events to Socket.IO"""

    def __init__(self, socketio=None):
        self.socketio = socketio

    def set_socketio(self, socketio):
        """Set Socket.IO instance"""
        self.socketio = socketio

    def emit_to_user(self, user_id: str, event_type: str, data: Dict):
        """
        Emit event to specific user's room

        Args:
            user_id: User identifier
            event_type: Event type (e.g., 'trades.delta', 'ops.confirmation')
            data: Event data
        """
        if not self.socketio:
            logger.warning("⚠️ Socket.IO not configured, cannot emit events")
            return

        room = f"user_{user_id}"
        self.socketio.emit(event_type, data, room=room)
        logger.info(f"✅ Emitted {event_type} to user {user_id}")

    def emit_trade_arming(
        self, user_id: str, op_id: str, pair: str, direction: str, entry: float, sl: float, tp: float, lot: float
    ):
        """
        Emit pre-position arming event

        Args:
            user_id: User ID
            op_id: Operation ID
            pair: Trading pair
            direction: BUY or SELL
            entry: Entry price
            sl: Stop loss
            tp: Take profit
            lot: Lot size
        """
        data = {
            "type": "trades.delta",
            "id": f"temp_{op_id}",
            "pair": pair,
            "direction": direction,
            "entry": entry,
            "current": entry,
            "sl": sl,
            "tp": tp,
            "lot": lot,
            "equity": 0,
            "pnl": 0,
            "status": "ARMING",
            "timestamp": int(time.time()),
        }

        self.emit_to_user(user_id, "trades.delta", data)

    def emit_trade_filled(
        self,
        user_id: str,
        fire_id: str,
        ticket: int,
        pair: str,
        direction: str,
        entry: float,
        filled_price: float,
        sl: float,
        tp: float,
        lot: float,
    ):
        """
        Emit position filled event

        Args:
            user_id: User ID
            fire_id: Fire ID
            ticket: MT5 ticket number
            pair: Trading pair
            direction: BUY or SELL
            entry: Entry price
            filled_price: Actual fill price
            sl: Stop loss
            tp: Take profit
            lot: Lot size
        """
        data = {
            "type": "trades.delta",
            "id": fire_id,
            "ticket": ticket,
            "pair": pair,
            "direction": direction,
            "entry": entry,
            "current": filled_price,
            "sl": sl,
            "tp": tp,
            "lot": lot,
            "equity": 0,  # Will be updated with P&L
            "pnl": 0,
            "status": "FILLED",
            "timestamp": int(time.time()),
        }

        self.emit_to_user(user_id, "trades.delta", data)

    def emit_operation_confirmation(
        self,
        user_id: str,
        op_id: str,
        status: str,
        ticket: Optional[int] = None,
        filled_price: Optional[float] = None,
        reason: Optional[str] = None,
    ):
        """
        Emit operation confirmation event

        Args:
            user_id: User ID
            op_id: Operation ID
            status: FILLED or REJECTED
            ticket: MT5 ticket (if filled)
            filled_price: Fill price (if filled)
            reason: Rejection reason (if rejected)
        """
        data = {"type": "ops.confirmation", "opId": op_id, "status": status, "timestamp": int(time.time())}

        if ticket is not None:
            data["ticket"] = ticket
        if filled_price is not None:
            data["filledPrice"] = filled_price
        if reason is not None:
            data["reason"] = reason

        self.emit_to_user(user_id, "ops.confirmation", data)

    def emit_position_update(
        self, user_id: str, fire_id: str, ticket: int, current_price: float, pnl: float, equity: float
    ):
        """
        Emit position P&L update

        Args:
            user_id: User ID
            fire_id: Fire ID
            ticket: MT5 ticket
            current_price: Current price
            pnl: Unrealized P&L
            equity: Current equity
        """
        data = {
            "type": "trades.delta",
            "id": fire_id,
            "ticket": ticket,
            "current": current_price,
            "pnl": pnl,
            "equity": equity,
            "status": "OPEN",
            "timestamp": int(time.time()),
        }

        self.emit_to_user(user_id, "trades.delta", data)

    def emit_position_closed(
        self, user_id: str, fire_id: str, ticket: int, close_price: float, pnl: float, reason: str
    ):
        """
        Emit position closed event

        Args:
            user_id: User ID
            fire_id: Fire ID
            ticket: MT5 ticket
            close_price: Close price
            pnl: Final P&L
            reason: Close reason (TP_HIT, SL_HIT, MANUAL, etc.)
        """
        data = {
            "type": "trades.delta",
            "id": fire_id,
            "ticket": ticket,
            "current": close_price,
            "pnl": pnl,
            "status": "CLOSED",
            "reason": reason,
            "timestamp": int(time.time()),
        }

        self.emit_to_user(user_id, "trades.delta", data)


# Global instance
_event_emitter = None


def get_event_emitter() -> TradeEventEmitter:
    """Get or create global event emitter instance"""
    global _event_emitter
    if _event_emitter is None:
        _event_emitter = TradeEventEmitter()
    return _event_emitter


if __name__ == "__main__":
    # Test
    emitter = get_event_emitter()

    # Test arming event
    emitter.emit_trade_arming(
        user_id="user_test",
        op_id="op_123",
        pair="EURUSD",
        direction="BUY",
        entry=1.05234,
        sl=1.05134,
        tp=1.05382,
        lot=0.10,
    )

    print("✅ Emitted arming event")

    # Test filled event
    emitter.emit_trade_filled(
        user_id="user_test",
        fire_id="fire_123",
        ticket=123456,
        pair="EURUSD",
        direction="BUY",
        entry=1.05234,
        filled_price=1.05236,
        sl=1.05134,
        tp=1.05382,
        lot=0.10,
    )

    print("✅ Emitted filled event")

    # Test confirmation
    emitter.emit_operation_confirmation(
        user_id="user_test", op_id="op_123", status="FILLED", ticket=123456, filled_price=1.05236
    )

    print("✅ Emitted confirmation event")
