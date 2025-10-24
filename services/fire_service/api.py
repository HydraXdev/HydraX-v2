#!/usr/bin/env python3
"""
Fire Service REST API
FastAPI endpoints for fire execution and management
"""

import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from models import (
    FireRequest,
    FireResponse,
    FireDetails,
    PositionInfo,
    BitmodeToggleRequest,
    BitmodeToggleResponse,
    FireStatusEnum
)
from fire_executor import fire_executor
from position_manager import position_manager
from bitmode_manager import bitmode_manager
from confirmation_tracker import confirmation_tracker
from config import config

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="BITTEN Fire Service",
    description="Trade execution and position management service",
    version=config.VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Start background services"""
    logger.info("Starting Fire Service...")
    # DISABLED: zmq_gateway handles confirmations on port 5558
    # confirmation_tracker.start()
    logger.info("Fire Service started successfully (confirmation handling via zmq_gateway)")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop background services"""
    logger.info("Shutting down Fire Service...")
    # DISABLED: zmq_gateway handles confirmations
    # confirmation_tracker.stop()
    logger.info("Fire Service shut down")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": config.SERVICE_NAME,
        "version": config.VERSION
    }


@app.post("/api/fire", response_model=FireResponse)
async def execute_fire(request: FireRequest):
    """
    Execute fire command

    Args:
        request: Fire request with signal details

    Returns:
        Fire execution response
    """
    try:
        # Execute fire
        fire_id, status, message = fire_executor.execute_fire(request)

        if status == FireStatusEnum.REJECTED or status == FireStatusEnum.FAILED:
            return FireResponse(
                success=False,
                fire_id=fire_id,
                status=status,
                message=message,
                error_code=status.value
            )

        return FireResponse(
            success=True,
            fire_id=fire_id,
            status=status,
            message=message
        )

    except Exception as e:
        logger.error(f"Fire execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/fires/{fire_id}", response_model=FireDetails)
async def get_fire_details(fire_id: str):
    """
    Get fire execution details

    Args:
        fire_id: Fire ID

    Returns:
        Fire details
    """
    try:
        details = fire_executor.get_fire_details(fire_id)

        if not details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fire {fire_id} not found"
            )

        # Convert to response model
        return FireDetails(**details)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fire details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/fires")
async def get_user_fires(user_id: str, limit: int = 10):
    """
    Get user's recent fires

    Args:
        user_id: User ID
        limit: Maximum number of fires to return

    Returns:
        List of fire records
    """
    try:
        fires = fire_executor.get_user_fires(user_id, limit)
        return {"fires": fires, "count": len(fires)}

    except Exception as e:
        logger.error(f"Error getting user fires: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/positions")
async def get_user_positions(user_id: str):
    """
    Get user's current open positions

    Args:
        user_id: User ID

    Returns:
        List of open positions
    """
    try:
        positions = position_manager.get_user_positions(user_id)
        metrics = position_manager.get_position_metrics(user_id)

        return {
            "positions": positions,
            "metrics": metrics
        }

    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/positions/{ticket}")
async def get_position_by_ticket(ticket: int):
    """
    Get position details by ticket number

    Args:
        ticket: MT5 ticket number

    Returns:
        Position details
    """
    try:
        position = position_manager.get_position_by_ticket(ticket)

        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Position {ticket} not found"
            )

        return position

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting position: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/bitmode/toggle", response_model=BitmodeToggleResponse)
async def toggle_bitmode(request: BitmodeToggleRequest):
    """
    Toggle BITMODE for user

    Args:
        request: BITMODE toggle request

    Returns:
        Toggle response
    """
    try:
        # Get user tier (would come from database in production)
        user_tier = "COMMANDER"  # Default for testing

        success = bitmode_manager.toggle_bitmode(
            user_id=request.user_id,
            enabled=request.enabled,
            user_tier=user_tier
        )

        if not success:
            return BitmodeToggleResponse(
                success=False,
                user_id=request.user_id,
                bitmode_enabled=False,
                message="BITMODE toggle failed - FANG+ tier required",
                tier_allowed=False
            )

        return BitmodeToggleResponse(
            success=True,
            user_id=request.user_id,
            bitmode_enabled=request.enabled,
            message=f"BITMODE {'enabled' if request.enabled else 'disabled'} successfully"
        )

    except Exception as e:
        logger.error(f"BITMODE toggle error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/bitmode/status")
async def get_bitmode_status(user_id: str):
    """
    Get BITMODE status for user

    Args:
        user_id: User ID

    Returns:
        BITMODE status
    """
    try:
        enabled = bitmode_manager.is_bitmode_enabled(user_id)

        return {
            "user_id": user_id,
            "bitmode_enabled": enabled,
            "config": bitmode_manager.get_bitmode_config("EURUSD").dict() if enabled else None
        }

    except Exception as e:
        logger.error(f"Error getting BITMODE status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/stats")
async def get_service_stats():
    """Get fire service statistics"""
    try:
        # Get basic stats from database
        import sqlite3
        conn = sqlite3.connect(str(config.BITTEN_DB))
        cursor = conn.cursor()

        # Count fires by status
        cursor.execute(
            """
            SELECT status, COUNT(*) as count
            FROM fires
            GROUP BY status
            """
        )
        status_counts = dict(cursor.fetchall())

        # Count total positions
        cursor.execute("SELECT COUNT(*) FROM positions_live")
        total_positions = cursor.fetchone()[0]

        conn.close()

        return {
            "fires": status_counts,
            "positions": total_positions,
            "service": config.SERVICE_NAME,
            "version": config.VERSION
        }

    except Exception as e:
        logger.error(f"Error getting service stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
