"""
BITTEN v2.0 Database Models
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, Field

from .config import DATABASE_URL

# SQLAlchemy setup - handle SQLite vs PostgreSQL
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# SQLAlchemy Models (Database)
# ============================================================================

class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    tier = Column(String, default='RECRUIT')
    risk_pct_default = Column(Float, default=2.0)
    max_concurrent = Column(Integer, default=3)
    daily_dd_limit = Column(Float, default=6.0)
    cooldown_s = Column(Integer, default=900)
    balance_cache = Column(Float, default=0)
    xp = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    last_fire_at = Column(Integer, default=0)
    telegram_id = Column(Integer, nullable=True)


class Signal(Base):
    __tablename__ = "signals"

    signal_id = Column(String, primary_key=True)
    symbol = Column(String)
    direction = Column(String)
    entry = Column(Float)
    sl = Column(Float)
    tp = Column(Float)
    confidence = Column(Float)
    timebox = Column(String)
    created_at = Column(Integer)
    expires_at = Column(Integer)
    payload_json = Column(Text)
    pattern_type = Column(String)
    outcome = Column(String)
    pips_result = Column(Float)
    target_pips = Column(Float)
    stop_pips = Column(Float)
    entry_price = Column(Float)
    resolution_time = Column(Integer)
    session = Column(String)
    calibrated_confidence = Column(Float)
    risk_reward = Column(Float)


class Mission(Base):
    __tablename__ = "missions"

    mission_id = Column(String, primary_key=True)
    signal_id = Column(String)
    payload_json = Column(Text, nullable=False)
    tg_message_id = Column(Integer)
    status = Column(String)
    expires_at = Column(Integer)
    created_at = Column(Integer)
    target_uuid = Column(String)
    user_id = Column(String)


class Fire(Base):
    __tablename__ = "fires"

    fire_id = Column(String, primary_key=True)
    mission_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    status = Column(String)
    ticket = Column(Integer)
    price = Column(Float)
    idem = Column(String, unique=True)
    created_at = Column(Integer)
    updated_at = Column(Integer)
    equity_used = Column(Float)
    risk_pct_used = Column(Float)
    closed_at = Column(Integer, default=0)
    pnl = Column(Float, default=0)
    target_uuid = Column(String)
    symbol = Column(String)
    direction = Column(String)
    sl = Column(Float)
    tp = Column(Float)
    lot = Column(Float)
    current_price = Column(Float, default=0)
    unrealized_pnl = Column(Float, default=0)
    hybrid_enabled = Column(Boolean, default=False)
    partial_closes = Column(Text)
    trail_updates = Column(Text)
    close_reason = Column(String)
    close_price = Column(Float)
    profit = Column(Float)


class LivePosition(Base):
    __tablename__ = "live_positions"

    fire_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    direction = Column(String, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float)
    sl = Column(Float)
    tp = Column(Float)
    lot_size = Column(Float)
    current_pips = Column(Float)
    current_pnl = Column(Float)
    max_pips = Column(Float)
    min_pips = Column(Float)
    duration_seconds = Column(Integer)
    last_update = Column(Integer)
    status = Column(String, default='OPEN')
    unrealized_pnl = Column(Float, default=0)
    ticket = Column(Integer)
    pnl = Column(Float)
    hybrid_status = Column(String)


class EAInstance(Base):
    __tablename__ = "ea_instances"

    target_uuid = Column(String, primary_key=True)
    user_id = Column(String)
    account_login = Column(String)
    broker = Column(String)
    currency = Column(String)
    leverage = Column(Integer)
    last_balance = Column(Float)
    last_equity = Column(Float)
    last_seen = Column(Integer)
    created_at = Column(Integer)
    updated_at = Column(Integer)
    open_positions = Column(Integer, default=0)
    position_data = Column(Text, default='{}')
    version = Column(String, default='unknown')


# ============================================================================
# Pydantic Models (API)
# ============================================================================

class SignalResponse(BaseModel):
    signal_id: str
    symbol: str
    direction: str
    entry: float
    sl: float
    tp: float
    confidence: float
    pattern_type: Optional[str] = None
    created_at: int
    expires_at: int

    class Config:
        from_attributes = True


class UserStats(BaseModel):
    user_id: str
    tier: str
    xp: int
    streak: int
    total_fires: int
    win_rate: float
    total_pnl: float

    class Config:
        from_attributes = True


class PositionResponse(BaseModel):
    fire_id: str
    symbol: str
    direction: str
    entry_price: float
    current_price: Optional[float] = None
    sl: float
    tp: float
    lot_size: float
    current_pips: Optional[float] = None
    current_pnl: Optional[float] = None
    duration_seconds: Optional[int] = None
    status: str

    class Config:
        from_attributes = True


class FireRequest(BaseModel):
    signal_id: Optional[str] = None  # Optional since it comes from URL path
    user_id: Optional[str] = None  # Optional - extracted from Firebase token if not provided
    risk_pct: Optional[float] = 2.0


class FireResponse(BaseModel):
    fire_id: str
    status: str
    message: str
    ticket: Optional[int] = None

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    timestamp: int
    version: str = "2.0.0"
    services: dict


class WSMessage(BaseModel):
    """WebSocket message format"""
    type: str  # signal, position, fire, heartbeat
    data: dict
    timestamp: int
