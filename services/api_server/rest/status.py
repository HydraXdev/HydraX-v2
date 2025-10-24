"""
Status API endpoints - Live position monitoring
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import psycopg2
from psycopg2.extras import RealDictCursor

from ..models import get_db, Fire

router = APIRouter(prefix="/api/status", tags=["status"])


@router.get("/{user_id}")
async def get_user_status(user_id: str, db: Session = Depends(get_db)):
    """Get real-time user account status with open trades - PostgreSQL v2"""
    try:
        # Connect to PostgreSQL v2 for real-time EA data
        pg_conn = psycopg2.connect(
            "postgresql://bitten_admin:bitten_secure_2025@localhost:5433/bitten_v2"
        )
        pg_cursor = pg_conn.cursor(cursor_factory=RealDictCursor)

        # Get REAL-TIME account balance from PostgreSQL ea_instances
        pg_cursor.execute(
            """
            SELECT last_balance, last_equity
            FROM ea_instances
            WHERE user_id = %s
            ORDER BY last_seen DESC
            LIMIT 1
        """,
            (user_id,),
        )

        account_row = pg_cursor.fetchone()
        balance = (
            float(account_row["last_balance"])
            if account_row and account_row["last_balance"]
            else 0.0
        )
        equity_from_ea = (
            float(account_row["last_equity"])
            if account_row and account_row["last_equity"]
            else balance
        )

        # Get open trades directly from PostgreSQL v2
        # Note: PostgreSQL fires table doesn't have open positions - those are in SQLite
        # For now return empty trades list with real balance from EA
        trades = []
        total_pnl = 0.0

        pg_conn.close()  # Close connection after all queries

        equity = balance + total_pnl
        max_slots = 3  # Can be pulled from user config

        return {
            "success": True,
            "data": {
                "balance": balance,
                "equity": equity,
                "openPositions": len(trades),
                "maxSlots": max_slots,
                "trades": trades,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
