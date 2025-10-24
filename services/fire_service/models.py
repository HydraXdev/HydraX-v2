#!/usr/bin/env python3
"""
Fire Service Data Models
Pydantic models for request/response validation
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DirectionEnum(str, Enum):
    """Trade direction"""
    BUY = "BUY"
    SELL = "SELL"


class FireStatusEnum(str, Enum):
    """Fire execution status"""
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    SENT = "SENT"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class FireModeEnum(str, Enum):
    """Fire mode type"""
    MANUAL = "MANUAL"
    AUTO = "AUTO"


class HybridConfig(BaseModel):
    """BITMODE v2 hybrid position management configuration"""
    enabled: bool = False
    partial1: Dict[str, float] = Field(default={"trigger": 8.0, "percent": 25.0})
    partial2: Dict[str, float] = Field(default={"trigger": 12.0, "percent": 25.0})
    trail: Dict[str, float] = Field(default={"distance": 8.0})


class FireRequest(BaseModel):
    """Fire command request"""
    user_id: str
    signal_id: str
    symbol: str
    direction: DirectionEnum
    entry_price: float
    sl_price: float
    tp_price: float
    fire_mode: FireModeEnum = FireModeEnum.MANUAL
    target_uuid: Optional[str] = None
    enable_bitmode: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "7176191872",
                "signal_id": "ELITE_GUARD_EURUSD_1234567890",
                "symbol": "EURUSD",
                "direction": "BUY",
                "entry_price": 1.10500,
                "sl_price": 1.10300,
                "tp_price": 1.10800,
                "fire_mode": "MANUAL",
                "enable_bitmode": False
            }
        }


class FireResponse(BaseModel):
    """Fire command response"""
    success: bool
    fire_id: str
    status: FireStatusEnum
    message: str
    ticket: Optional[int] = None
    fill_price: Optional[float] = None
    lot_size: Optional[float] = None
    error_code: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "fire_id": "ELITE_GUARD_EURUSD_1234567890",
                "status": "FILLED",
                "message": "Trade executed successfully",
                "ticket": 12345678,
                "fill_price": 1.10505,
                "lot_size": 0.10
            }
        }


class FireDetails(BaseModel):
    """Detailed fire information"""
    fire_id: str
    user_id: str
    signal_id: str
    symbol: str
    direction: DirectionEnum
    entry_price: float
    sl_price: float
    tp_price: float
    lot_size: float
    status: FireStatusEnum
    fire_mode: FireModeEnum
    ticket: Optional[int] = None
    fill_price: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    bitmode_enabled: bool = False
    hybrid_config: Optional[HybridConfig] = None
    error_message: Optional[str] = None


class PositionInfo(BaseModel):
    """Live position information"""
    ticket: int
    fire_id: str
    symbol: str
    direction: DirectionEnum
    open_price: float
    current_price: float
    sl: float
    tp: float
    volume: float
    profit: float
    pips: float
    opened_at: datetime
    partial_closes: list = Field(default_factory=list)


class BitmodeToggleRequest(BaseModel):
    """BITMODE toggle request"""
    user_id: str
    enabled: bool

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "7176191872",
                "enabled": True
            }
        }


class BitmodeToggleResponse(BaseModel):
    """BITMODE toggle response"""
    success: bool
    user_id: str
    bitmode_enabled: bool
    message: str
    tier_allowed: bool = True
