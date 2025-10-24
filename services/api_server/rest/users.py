"""
User API endpoints - SECURED with Firebase Authentication
All endpoints require Firebase ID token in Authorization header
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from ..models import get_db, User, Fire, LivePosition, UserStats, PositionResponse
from ..middleware.auth import verify_user_access, verify_firebase_token
import sys
import os
# Add parent directory for fire_mode_database import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.bitten_core.fire_mode_database import fire_mode_db

router = APIRouter(prefix="/api/users", tags=["users"])


# Request models for trailing toggle
class TrailingToggleRequest(BaseModel):
    user_id: str
    enabled: bool

# Request model for fire mode update
class FireModeUpdateRequest(BaseModel):
    user_id: str
    fire_mode: str  # 'SAFE', 'MANUAL', 'AUTO'


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    verified_user: str = Depends(verify_user_access)
):
    """
    Get user details - AUTHENTICATED
    Requires: Authorization: Bearer <firebase_token>
    Users can only access their own data
    """
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user.user_id,
        "telegram_id": user.telegram_id,
        "balance": user.balance or 0,
        "equity": user.equity or 0,
        "tier": user.tier or 'RECRUIT',
        "fire_mode": user.fire_mode or 'MANUAL',
        "bitmode_enabled": user.bitmode_enabled or False,
        "target_uuid": user.target_uuid,
        "account_login": user.account_login,
        "broker": user.broker,
        "currency": user.currency or 'USD',
        "leverage": user.leverage or 500
    }


@router.get("/{user_id}/stats", response_model=UserStats)
async def get_user_stats(
    user_id: str,
    db: Session = Depends(get_db),
    verified_user: str = Depends(verify_user_access)
):
    """
    Get user trading statistics - AUTHENTICATED
    Requires: Authorization: Bearer <firebase_token>
    Users can only access their own stats
    """
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get fire statistics
    total_fires = db.query(func.count(Fire.fire_id)).filter(
        Fire.user_id == user_id
    ).scalar() or 0

    filled_fires = db.query(Fire).filter(
        Fire.user_id == user_id,
        Fire.status == "FILLED"
    ).all()

    wins = sum(1 for f in filled_fires if f.pnl and f.pnl > 0)
    win_rate = (wins / len(filled_fires) * 100) if filled_fires else 0

    total_pnl = sum(f.pnl or 0 for f in filled_fires)

    return UserStats(
        user_id=user.user_id,
        tier=user.tier or "NIBBLER",
        xp=user.xp or 0,
        streak=user.streak or 0,
        total_fires=total_fires,
        win_rate=round(win_rate, 1),
        total_pnl=round(total_pnl, 2)
    )


@router.get("/{user_id}/positions", response_model=list[PositionResponse])
async def get_user_positions(
    user_id: str,
    db: Session = Depends(get_db),
    verified_user: str = Depends(verify_user_access)
):
    """
    Get user's active positions - AUTHENTICATED
    Requires: Authorization: Bearer <firebase_token>
    Users can only access their own positions
    """
    positions = db.query(LivePosition).filter(
        LivePosition.user_id == user_id,
        LivePosition.status == "OPEN"
    ).all()

    return [
        PositionResponse(
            fire_id=p.fire_id,
            symbol=p.symbol,
            direction=p.direction,
            entry_price=p.entry_price,
            current_price=p.current_price,
            sl=p.sl or 0,
            tp=p.tp or 0,
            lot_size=p.lot_size or 0,
            current_pips=p.current_pips,
            current_pnl=p.current_pnl,
            duration_seconds=p.duration_seconds,
            status=p.status
        )
        for p in positions
    ]


@router.post("/trailing/toggle")
async def toggle_trailing(
    request: TrailingToggleRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_firebase_token)
):
    """
    Toggle Smart Trailing Stops for a user - AUTHENTICATED
    Requires: Authorization: Bearer <firebase_token>
    Requires FANG or COMMANDER tier
    Users can only toggle their own trailing stops
    """
    try:
        user_id = request.user_id
        enabled = request.enabled

        # Verify user can only modify their own settings
        if current_user != user_id:
            raise HTTPException(
                status_code=403,
                detail="Forbidden: You can only modify your own settings"
            )

        # Get user from database to check tier
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_tier = user.tier or "NIBBLER"

        # Check tier eligibility - FANG and COMMANDER only
        if user_tier not in ["FANG", "COMMANDER"]:
            raise HTTPException(
                status_code=403,
                detail=f"Smart Trailing Stops require FANG or COMMANDER tier. Current tier: {user_tier}. Upgrade to unlock professional trailing stop management."
            )

        # Toggle Smart Trailing Stops using fire_mode_database
        success = fire_mode_db.toggle_trailing(user_id, enabled, user_tier)

        if success:
            return {
                "success": True,
                "enabled": enabled,
                "message": f'Smart Trailing Stops {"enabled" if enabled else "disabled"} successfully'
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update trailing stops status"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/trailing/status")
async def get_trailing_status(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_firebase_token)
):
    """
    Get Smart Trailing Stops status for a user - AUTHENTICATED
    Requires: Authorization: Bearer <firebase_token>
    Users can only check their own trailing status
    """
    try:
        # Verify user can only access their own settings
        if current_user != user_id:
            raise HTTPException(
                status_code=403,
                detail="Forbidden: You can only access your own settings"
            )

        # Get user from database
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_tier = user.tier or "NIBBLER"

        # Get trailing status from fire_mode_database
        trailing_enabled = fire_mode_db.is_trailing_enabled(user_id)

        return {
            "success": True,
            "enabled": trailing_enabled,
            "tier": user_tier,
            "eligible": user_tier in ["FANG", "COMMANDER", "COMMANDER+", "ELITE"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/slots/status")
async def get_slots_status(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_firebase_token)
):
    """
    Get user's LIVE slot availability (concurrent position limits) - AUTHENTICATED
    Uses same logic as fire_validator to check actual backend slot limits
    """
    try:
        import sqlite3

        # Verify user can only access their own data
        if current_user != user_id:
            raise HTTPException(
                status_code=403,
                detail="Forbidden: You can only access your own slot status"
            )

        # Connect to bitten.db and get live slot data
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db', timeout=5)
        cursor = conn.cursor()

        # Get user's tier and settings from user_fire_modes
        cursor.execute("""
            SELECT subscription_tier, max_manual_slots, max_auto_slots
            FROM user_fire_modes
            WHERE user_id = ?
        """, (user_id,))

        user_data = cursor.fetchone()
        if not user_data:
            conn.close()
            return {
                "success": False,
                "error": "User not found",
                "manual_slots_available": False,
                "auto_slots_available": False
            }

        tier, max_manual_slots, max_auto_slots = user_data

        # Count MANUAL open positions
        cursor.execute("""
            SELECT COUNT(*)
            FROM live_positions lp
            JOIN fires f ON lp.fire_id = f.fire_id
            WHERE lp.user_id = ?
              AND lp.status = 'OPEN'
              AND (f.fire_mode = 'MANUAL' OR f.fire_mode IS NULL)
        """, (user_id,))
        manual_open = cursor.fetchone()[0] or 0

        # Count AUTO open positions
        cursor.execute("""
            SELECT COUNT(*)
            FROM live_positions lp
            JOIN fires f ON lp.fire_id = f.fire_id
            WHERE lp.user_id = ?
              AND lp.status = 'OPEN'
              AND f.fire_mode = 'AUTO'
        """, (user_id,))
        auto_open = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "success": True,
            "user_id": user_id,
            "tier": tier or "NIBBLER",
            "manual": {
                "used": manual_open,
                "max": max_manual_slots or 1,
                "available": manual_open < (max_manual_slots or 1)
            },
            "auto": {
                "used": auto_open,
                "max": max_auto_slots or 0,
                "available": auto_open < (max_auto_slots or 0)
            },
            "total_open": manual_open + auto_open
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Slots status error: {str(e)}")


@router.get("/ammunition/status")
async def get_ammunition_status(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_firebase_token)
):
    """
    Get user's ammunition status (daily fire count) - AUTHENTICATED
    Requires: Authorization: Bearer <firebase_token>
    Users can only check their own ammunition status
    """
    try:
        from datetime import datetime, timedelta

        # Verify user can only access their own data
        if current_user != user_id:
            raise HTTPException(
                status_code=403,
                detail="Forbidden: You can only access your own ammunition status"
            )

        # Get user to check tier
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_tier = user.tier or "NIBBLER"

        # Base ammunition by tier (stored in fire_modes.db)
        import sqlite3
        fire_modes_conn = sqlite3.connect('/root/HydraX-v2/data/fire_modes.db')
        fire_modes_cursor = fire_modes_conn.cursor()

        # Get tier from fire_modes database
        fire_modes_cursor.execute(
            "SELECT subscription_tier FROM user_fire_modes WHERE user_id = ?",
            (user_id,)
        )
        tier_result = fire_modes_cursor.fetchone()
        fire_modes_conn.close()

        actual_tier = tier_result[0] if tier_result else "NIBBLER"

        BASE_AMMO = {"NIBBLER": 3, "FANG": 5, "COMMANDER": 7, "COMMANDER+": 7, "ELITE": 7}
        max_ammo = BASE_AMMO.get(actual_tier, 3)

        # Count fires in last 24 hours using raw SQLite query
        bitten_conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
        bitten_cursor = bitten_conn.cursor()

        today_start = datetime.now() - timedelta(days=1)
        bitten_cursor.execute(
            "SELECT COUNT(*) FROM fires WHERE user_id = ? AND created_at >= ?",
            (user_id, int(today_start.timestamp()))
        )
        today_fires = bitten_cursor.fetchone()[0]
        bitten_conn.close()

        remaining_ammo = max(0, max_ammo - today_fires)

        return {
            "success": True,
            "user_id": user_id,
            "tier": user_tier,
            "max_ammo": max_ammo,
            "used_today": today_fires,
            "remaining": remaining_ammo,
            "ammo_pct": (remaining_ammo / max_ammo * 100) if max_ammo > 0 else 0
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/fire-mode/update")
async def update_fire_mode(
    request: FireModeUpdateRequest,
    current_user: str = Depends(verify_firebase_token)
):
    """
    Update user's fire mode (SAFE/MANUAL/AUTO) - AUTHENTICATED
    Syncs to bitten.db for backend validation
    """
    try:
        import sqlite3
        import time

        # Verify user can only update their own mode
        if current_user != request.user_id:
            raise HTTPException(
                status_code=403,
                detail="Forbidden: You can only update your own fire mode"
            )

        # Map frontend modes to backend modes
        # Frontend: 'safe', 'semi', 'full_auto'
        # Backend: 'SAFE', 'MANUAL', 'AUTO'
        mode_mapping = {
            'safe': 'SAFE',
            'semi': 'MANUAL',
            'full_auto': 'AUTO',
            'SAFE': 'SAFE',
            'MANUAL': 'MANUAL',
            'AUTO': 'AUTO'
        }

        backend_mode = mode_mapping.get(request.fire_mode, request.fire_mode.upper())
        if backend_mode not in ['SAFE', 'MANUAL', 'AUTO']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid fire mode: {request.fire_mode}"
            )

        # Update bitten.db user_fire_modes table
        conn = sqlite3.connect('/root/HydraX-v2/bitten.db', timeout=5)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE user_fire_modes
            SET current_mode = ?, updated_at = ?
            WHERE user_id = ?
        """, (backend_mode, int(time.time()), request.user_id))

        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()

        if rows_updated == 0:
            raise HTTPException(
                status_code=404,
                detail="User not found in fire modes database"
            )

        return {
            "success": True,
            "user_id": request.user_id,
            "fire_mode": backend_mode,
            "message": f"Fire mode updated to {backend_mode}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fire mode update error: {str(e)}")
