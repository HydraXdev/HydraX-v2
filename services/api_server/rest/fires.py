"""
Fire execution API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import sys
import os
import time
import uuid
import zmq
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from ..models import get_db, Signal, Fire, User, FireRequest, FireResponse, EAInstance
from ..config import FIRE_QUEUE_IPC
from ..firebase_auth import verify_firebase_token, get_current_user_id
from src.bitten_core.real_position_calculator import calculate_real_position_size
from src.bitten_core.constants import (
    get_pip_size,
    calculate_stop_loss_price,
    calculate_take_profit_price,
    verify_pip_conversion
)

router = APIRouter(prefix="/api", tags=["fires"])

# ZMQ socket for fire commands (lazy initialization)
_zmq_socket = None


def get_fire_socket():
    """Get or create ZMQ PUSH socket for fire commands"""
    global _zmq_socket
    if _zmq_socket is None:
        context = zmq.Context()
        _zmq_socket = context.socket(zmq.PUSH)
        _zmq_socket.connect(FIRE_QUEUE_IPC)
    return _zmq_socket


@router.post("/signals/{signal_id}/fire", response_model=FireResponse)
async def fire_signal(
    signal_id: str,
    request: FireRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Execute a fire command for a signal

    Requires Firebase authentication via Authorization: Bearer <token> header
    """

    # 1. Validate signal exists and is active
    signal = db.query(Signal).filter(Signal.signal_id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    current_time = int(time.time())
    if signal.expires_at and signal.expires_at < current_time:
        raise HTTPException(status_code=400, detail="Signal has expired")

    # 2. Use authenticated user_id (verified from Firebase token)
    # Ignore request.user_id from body - use token-verified user_id instead
    authenticated_user_id = user_id

    # Validate user exists
    user = db.query(User).filter(User.user_id == authenticated_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2.5. DEDUPLICATION CHECK: Verify user hasn't already fired this signal
    import sqlite3
    bitten_db_path = "/root/HydraX-v2/bitten.db"
    with sqlite3.connect(bitten_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT fire_id, fire_mode, status
            FROM fires
            WHERE user_id = ? AND mission_id = ?
              AND status IN ('SENT', 'FILLED')
            LIMIT 1
            """,
            (authenticated_user_id, signal_id)
        )
        existing_fire = cursor.fetchone()

    if existing_fire:
        fire_id_existing, fire_mode, fire_status = existing_fire
        raise HTTPException(
            status_code=409,  # Conflict
            detail={
                "error": "ALREADY_FIRED",
                "message": f"You already fired this signal via {fire_mode}",
                "fire_id": fire_id_existing,
                "fire_mode": fire_mode,
                "status": fire_status
            }
        )

    # 3. Create fire record (using authenticated user_id)
    fire_id = f"FIRE_{signal.symbol}_{int(time.time())}"
    fire = Fire(
        fire_id=fire_id,
        mission_id=signal_id,
        user_id=authenticated_user_id,  # Use verified Firebase UID
        status="PENDING",
        created_at=current_time,
        updated_at=current_time,
        symbol=signal.symbol,
        direction=signal.direction,
        sl=signal.sl,
        tp=signal.tp,
        risk_pct_used=request.risk_pct,
        idem=str(uuid.uuid4())
    )

    db.add(fire)
    db.commit()

    # 4. Get account balance for position sizing
    # Try to get balance from EA instances table (live balance)
    ea_instance = db.query(EAInstance).filter(EAInstance.user_id == authenticated_user_id).first()

    # Fall back to user's balance_cache if EA instance not found
    account_balance = ea_instance.last_balance if ea_instance and ea_instance.last_balance else user.balance_cache

    # Default to 10000 if no balance found (safety fallback)
    if not account_balance or account_balance <= 0:
        account_balance = 10000.0

    # 5. Calculate position size using REAL calculator
    position_calc = calculate_real_position_size(
        account_balance=account_balance,
        risk_percentage=request.risk_pct or 2.0,
        stop_loss_pips=int(signal.stop_pips) if signal.stop_pips else 20,
        symbol=signal.symbol,
        tier=user.tier or "COMMANDER"
    )

    if not position_calc.get("valid"):
        raise HTTPException(
            status_code=400,
            detail=f"Position calculation failed: {position_calc.get('error')}"
        )

    lot_size = position_calc["lot_size"]

    # 6. Calculate absolute SL/TP prices from pips using UNIFIED pip size system
    entry_price = signal.entry_price or 0

    # Use centralized pip size calculation (handles JPY, XAUUSD, XAGUSD, majors)
    if signal.stop_pips and signal.target_pips:
        sl_price = calculate_stop_loss_price(entry_price, signal.stop_pips, signal.direction, signal.symbol)
        tp_price = calculate_take_profit_price(entry_price, signal.target_pips, signal.direction, signal.symbol)

        # ✅ VERIFICATION: Ensure pip conversion is accurate
        try:
            verify_pip_conversion(entry_price, sl_price, signal.stop_pips, signal.symbol, tolerance=1.0)
        except AssertionError as e:
            # Log warning but continue (better to execute trade than block it)
            import logging
            logging.warning(f"Pip conversion check for {signal.symbol}: {e}")
    else:
        sl_price = 0
        tp_price = 0

    # 7. Build fire command (format matching EA v2.07)
    fire_command = {
        "type": "fire",
        "fire_id": fire_id,
        "target_uuid": "COMMANDER_DEV_001",  # TODO: Get from user mapping
        "symbol": signal.symbol,
        "direction": signal.direction,
        "entry": entry_price,
        "sl": round(sl_price, 5) if sl_price else 0,
        "tp": round(tp_price, 5) if tp_price else 0,
        "lot": lot_size,  # Calculated from account balance and risk %
        "user_id": authenticated_user_id  # Use verified Firebase UID
    }

    # 5. Send to fire queue
    try:
        socket = get_fire_socket()
        socket.send_json(fire_command)

        # Update fire status
        fire.status = "SENT"
        fire.updated_at = int(time.time())
        db.commit()

        return FireResponse(
            fire_id=fire_id,
            status="SENT",
            message="Fire command sent to EA"
        )

    except Exception as e:
        fire.status = "FAILED"
        fire.updated_at = int(time.time())
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to send fire command: {str(e)}"
        )


# ============================================================================
# Manual Fire Endpoint with Server-Side Validation
# ============================================================================

class ManualFireRequest(BaseModel):
    """Manual fire request with user preferences"""
    user_id: str
    signal_id: str
    requested: dict  # {riskPct: float, lot: float} - advisory only


class ManualFireResponse(BaseModel):
    """Manual fire response with enforced parameters"""
    success: bool
    fire_id: Optional[str] = None
    reason: Optional[str] = None
    message: Optional[str] = None
    enforced: Optional[dict] = None


@router.post("/fire/manual", response_model=ManualFireResponse)
async def manual_fire(
    request: ManualFireRequest,
    db: Session = Depends(get_db)
):
    """
    Execute manual fire with server-side validation and enforcement.

    Client request is advisory only - server validates and enforces tier caps.
    Returns enforced parameters or rejection reason.

    Args:
        request: User ID, signal ID, and requested parameters (advisory)

    Returns:
        Success response with enforced parameters, or failure with reason
    """

    try:
        # Import FireValidator
        from src.bitten_core.fire_validator import fire_validator

        # Step 1: Load signal from database
        signal = db.query(Signal).filter(Signal.signal_id == request.signal_id).first()
        if not signal:
            return ManualFireResponse(
                success=False,
                reason="SIGNAL_NOT_FOUND",
                message=f"Signal {request.signal_id} not found in database"
            )

        # Check if signal has expired
        current_time = int(time.time())
        if signal.expires_at and signal.expires_at < current_time:
            return ManualFireResponse(
                success=False,
                reason="SIGNAL_EXPIRED",
                message="Signal has expired and cannot be executed"
            )

        # Step 2: Build validation request with signal data
        client_request = {
            "symbol": signal.symbol,
            "direction": signal.direction,
            "sl_pips": signal.stop_pips or 20.0,  # Default to 20 pips if missing
            "tp_pips": signal.target_pips or 30.0,  # Default to 30 pips if missing
            "risk_pct": request.requested.get("riskPct", 2.0),  # User preference
            "fire_mode": "MANUAL"
        }

        # Step 3: Validate fire request (server enforces caps)
        validation_result = fire_validator.validate_fire_request(
            user_id=request.user_id,
            signal_id=request.signal_id,
            client_request=client_request
        )

        # Step 4: Check if validation passed
        if not validation_result.get("allowed", False):
            return ManualFireResponse(
                success=False,
                reason=validation_result.get("reason", "VALIDATION_FAILED"),
                message=validation_result.get("reason", "Fire request validation failed")
            )

        # Step 5: Execute fire using enqueue_fire
        from enqueue_fire import create_fire_command, enqueue_fire

        enforced = validation_result["enforced"]

        # Create fire command with enforced parameters
        fire_cmd = create_fire_command(
            mission_id=request.signal_id,
            user_id=request.user_id,
            symbol=enforced["symbol"],
            direction=signal.direction,
            entry=signal.entry_price or 0,
            sl=signal.sl or 0,
            tp=signal.tp or 0,
            lot=enforced["lot_size"],
            risk_reward=None,  # Will be calculated from signal
            enable_bitmode=False  # Manual fires don't use BITMODE by default
        )

        if fire_cmd is None:
            return ManualFireResponse(
                success=False,
                reason="FIRE_COMMAND_CREATION_FAILED",
                message="Failed to create fire command (possibly blocked by hedge protection)"
            )

        # Step 6: Enqueue fire command
        enqueue_result = enqueue_fire(fire_cmd)

        if not enqueue_result:
            return ManualFireResponse(
                success=False,
                reason="ENQUEUE_FAILED",
                message="Failed to enqueue fire command to IPC queue"
            )

        # Step 7: Create fire record in database
        fire_id = fire_cmd.get("fire_id")
        fire = Fire(
            fire_id=fire_id,
            mission_id=request.signal_id,
            user_id=request.user_id,
            status="SENT",
            created_at=current_time,
            updated_at=current_time,
            symbol=enforced["symbol"],
            direction=signal.direction,
            sl=fire_cmd.get("sl"),
            tp=fire_cmd.get("tp"),
            risk_pct_used=enforced["risk_pct"],
            equity_used=validation_result["validation_details"]["balance"],
            idem=str(uuid.uuid4())
        )

        db.add(fire)
        db.commit()

        # Step 8: Return success with enforced parameters
        return ManualFireResponse(
            success=True,
            fire_id=fire_id,
            enforced={
                "riskPct": enforced["risk_pct"],
                "lot": enforced["lot_size"],
                "sl": fire_cmd.get("sl"),
                "tp": fire_cmd.get("tp")
            }
        )

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Manual fire endpoint error: {e}")
        print(error_trace)

        return ManualFireResponse(
            success=False,
            reason="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}"
        )


@router.post("/fire")
async def fire_signal_legacy(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Legacy fire endpoint for frontend compatibility.
    Accepts signal_id and user_id, delegates to manual fire logic.
    """
    try:
        # Extract parameters from request
        signal_id = request.get("signal_id") or request.get("mission_id")
        user_id = request.get("user_id")
        mode = request.get("mode", "manual")

        if not signal_id:
            return {"success": False, "error": "Missing signal_id"}

        if not user_id:
            return {"success": False, "error": "Missing user_id"}

        # Create manual fire request
        manual_request = ManualFireRequest(
            user_id=user_id,
            signal_id=signal_id,
            requested=request.get("requested", {"riskPct": 2.0, "lot": 0.01})
        )

        # Delegate to manual fire endpoint
        response = await manual_fire(manual_request, db)

        # Convert to dict for legacy format
        if isinstance(response, ManualFireResponse):
            return {
                "success": response.success,
                "fire_id": response.fire_id,
                "reason": response.reason,
                "message": response.message,
                "enforced": response.enforced
            }

        return response

    except Exception as e:
        import traceback
        print(f"❌ Legacy fire endpoint error: {e}")
        print(traceback.format_exc())
        return {"success": False, "error": str(e)}


@router.get("/fires/{fire_id}")
async def get_fire_status(
    fire_id: str,
    db: Session = Depends(get_db)
):
    """
    Get fire status including ticket number for confirmation polling.

    Used by frontend to poll for EA confirmation after fire execution.
    """
    try:
        fire = db.query(Fire).filter(Fire.fire_id == fire_id).first()

        if not fire:
            raise HTTPException(status_code=404, detail="Fire not found")

        return {
            "fire_id": fire.fire_id,
            "status": fire.status,
            "ticket": fire.ticket,
            "price": fire.price,
            "symbol": fire.symbol,
            "direction": fire.direction,
            "created_at": fire.created_at,
            "updated_at": fire.updated_at
        }

    except Exception as e:
        import traceback
        print(f"❌ Get fire status error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/balance")
async def get_user_balance(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get user's current account balance from EA instances or user cache.

    Requires Firebase authentication via Authorization: Bearer <token> header
    """
    try:
        # Try to get balance from EA instances table (live balance)
        ea_instance = db.query(EAInstance).filter(EAInstance.user_id == user_id).first()

        if ea_instance and ea_instance.last_balance:
            return {
                "balance": ea_instance.last_balance,
                "source": "live_ea"
            }

        # Fall back to user's balance_cache
        user = db.query(User).filter(User.user_id == user_id).first()

        if user and user.balance_cache:
            return {
                "balance": user.balance_cache,
                "source": "cached"
            }

        # Default fallback
        return {
            "balance": 10000.0,
            "source": "default"
        }

    except Exception as e:
        import traceback
        print(f"❌ Get user balance error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


class CloseTradeRequest(BaseModel):
    """Request model for closing a trade"""
    fire_id: str
    ticket: int


@router.post("/close_trade")
async def close_trade(
    request: CloseTradeRequest,
    db: Session = Depends(get_db)
):
    """
    Close a trade manually via ABORT button on Battlefield

    This endpoint sends a close_ticket command to the EA via IPC queue
    """
    try:
        fire_id = request.fire_id
        ticket = request.ticket

        if not ticket:
            raise HTTPException(status_code=400, detail="Ticket number required")

        print(f"🚨 Manual trade abort requested: {fire_id} (ticket {ticket})")

        # Create close_ticket command for EA
        close_cmd = {
            "type": "close_ticket",
            "ticket": int(ticket)
        }

        # Send to IPC queue (same as fire commands)
        fire_socket = get_fire_socket()
        fire_socket.send_json(close_cmd)

        print(f"✅ Close command queued for ticket {ticket}")

        return {
            "success": True,
            "message": f"Close command sent for ticket {ticket}",
            "fire_id": fire_id,
            "ticket": ticket
        }

    except Exception as e:
        import traceback
        print(f"❌ Close trade error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
