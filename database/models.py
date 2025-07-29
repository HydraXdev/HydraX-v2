"""
BITTEN Database Models - ForexVPS Architecture
Centralized data management replacing file-based storage
"""
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, DECIMAL, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://bitten:bitten_secure_2025@localhost/bitten_production")

engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=30)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class User(Base):
    """User model - centralized user management"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(100))
    tier = Column(String(20), default="NIBBLER")
    xp_points = Column(Integer, default=0)
    rank = Column(String(50), default="RECRUIT")
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    forexvps_account_id = Column(String(100))
    
    # Relationships
    missions = relationship("Mission", back_populates="user")
    trades = relationship("Trade", back_populates="user")

class Signal(Base):
    """Signal model - replace file-based signal storage"""
    __tablename__ = "signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(String(100), unique=True, nullable=False)
    symbol = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    entry_price = Column(DECIMAL(10, 5))
    stop_loss = Column(DECIMAL(10, 5))
    take_profit = Column(DECIMAL(10, 5))
    confidence = Column(Integer)
    signal_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    status = Column(String(20), default="active")
    raw_data = Column(JSONB)
    
    # Relationships
    missions = relationship("Mission", back_populates="signal")

class Mission(Base):
    """Mission model - replace /missions/ file system"""
    __tablename__ = "missions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.id"))
    mission_data = Column(JSONB, nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    fired_at = Column(DateTime)
    result = Column(JSONB)
    
    # Relationships
    user = relationship("User", back_populates="missions")
    signal = relationship("Signal", back_populates="missions")
    trades = relationship("Trade", back_populates="mission")

class Trade(Base):
    """Trade model - centralized trade execution tracking"""
    __tablename__ = "trades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"))
    symbol = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    entry_price = Column(DECIMAL(10, 5))
    stop_loss = Column(DECIMAL(10, 5))
    take_profit = Column(DECIMAL(10, 5))
    lot_size = Column(DECIMAL(8, 2))
    broker_ticket = Column(String(50))
    status = Column(String(20), default="pending")
    executed_at = Column(DateTime)
    closed_at = Column(DateTime)
    profit_loss = Column(DECIMAL(10, 2))
    pips = Column(DECIMAL(8, 1))
    forexvps_response = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="trades")
    mission = relationship("Mission", back_populates="trades")

class SystemLog(Base):
    """System logging - centralized logging"""
    __tablename__ = "system_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String(10), nullable=False)
    module = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    meta_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)

class ForexVPSRequest(Base):
    """ForexVPS integration tracking"""
    __tablename__ = "forexvps_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    endpoint = Column(String(100), nullable=False)
    request_data = Column(JSONB)
    response_data = Column(JSONB)
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text)

# Database utilities
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def get_user_by_telegram_id(db, telegram_id: str):
    """Get user by telegram ID"""
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def create_user(db, telegram_id: str, username: str = None, tier: str = "NIBBLER"):
    """Create new user"""
    user = User(telegram_id=telegram_id, username=username, tier=tier)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_signal(db, signal_data: dict):
    """Create new signal"""
    signal = Signal(**signal_data)
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal

def create_mission(db, mission_data: dict):
    """Create new mission"""
    mission = Mission(**mission_data)
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission

def get_active_missions(db, user_id: str = None):
    """Get active missions for user or all"""
    query = db.query(Mission).filter(Mission.status == "pending")
    if user_id:
        query = query.filter(Mission.user_id == user_id)
    return query.all()

def log_system_event(db, level: str, module: str, message: str, user_id: str = None, meta_data: dict = None):
    """Log system event"""
    log = SystemLog(
        level=level,
        module=module,
        message=message,
        user_id=user_id,
        meta_data=meta_data
    )
    db.add(log)
    db.commit()
    return log