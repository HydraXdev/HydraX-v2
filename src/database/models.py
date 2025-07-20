"""
🎯 BITTEN Database Models
SQLAlchemy ORM models for PostgreSQL database
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List, Any
from enum import Enum as PyEnum

from sqlalchemy import (
    create_engine, Column, Integer, BigInteger, String, Boolean, 
    DateTime, Numeric, ForeignKey, UniqueConstraint, Index, 
    CheckConstraint, JSON, Date, Text, INET
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

# ==========================================
# ENUMS
# ==========================================

class TierLevel(PyEnum):
    PRESS_PASS = "PRESS_PASS"  # Tier 0 - Press/Trial tier
    NIBBLER = "NIBBLER"
    FANG = "FANG"
    COMMANDER = "COMMANDER"  # Premium tier with all features

class SubscriptionStatus(PyEnum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    TRIAL = "trial"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class TradeDirection(PyEnum):
    BUY = "BUY"
    SELL = "SELL"

class TradeStatus(PyEnum):
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    ERROR = "error"

class RiskMode(PyEnum):
    DEFAULT = "default"
    BOOST = "boost"
    HIGH_RISK = "high_risk"

# ==========================================
# USER MODELS
# ==========================================

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(BigInteger, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    email = Column(String(255), unique=True)
    phone = Column(String(50))
    
    # Subscription
    tier = Column(String(50), nullable=False, default=TierLevel.NIBBLER.value, index=True)
    subscription_status = Column(String(50), nullable=False, default=SubscriptionStatus.INACTIVE.value, index=True)
    subscription_expires_at = Column(DateTime(timezone=True))
    payment_method = Column(String(50))
    
    # MT5
    mt5_account_id = Column(String(255))
    mt5_broker_server = Column(String(255))
    mt5_connected = Column(Boolean, default=False)
    
    # Security
    api_key = Column(String(255), unique=True)
    api_key_created_at = Column(DateTime(timezone=True))
    last_login_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    risk_sessions = relationship("RiskSession", back_populates="user", cascade="all, delete-orphan")
    xp_transactions = relationship("XPTransaction", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("PaymentTransaction", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username}, tier={self.tier})>"


class UserProfile(Base):
    __tablename__ = 'user_profiles'
    
    profile_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), unique=True, nullable=False)
    
    # Identity
    callsign = Column(String(50), unique=True, index=True)  # User's unique callsign
    
    # XP & Progression
    total_xp = Column(Integer, nullable=False, default=0, index=True)
    current_rank = Column(String(50), nullable=False, default='RECRUIT')
    medals_data = Column(JSONB, default=list)
    achievements_data = Column(JSONB, default=list)
    
    # Trading stats
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_profit_usd = Column(Numeric(15, 2), default=0)
    total_pips = Column(Integer, default=0)
    largest_win_usd = Column(Numeric(15, 2), default=0)
    largest_loss_usd = Column(Numeric(15, 2), default=0)
    best_streak = Column(Integer, default=0)
    worst_streak = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    
    # Recruitment
    referral_code = Column(String(50), unique=True, index=True)
    referred_by_user_id = Column(BigInteger, ForeignKey('users.user_id'))
    recruitment_count = Column(Integer, default=0)
    recruitment_xp_earned = Column(Integer, default=0)
    
    # Preferences
    notification_settings = Column(JSONB, default=dict)
    trading_preferences = Column(JSONB, default=dict)
    ui_theme = Column(String(50), default='dark')
    language_code = Column(String(10), default='en')
    
    # Metadata
    last_trade_at = Column(DateTime(timezone=True))
    profile_completed = Column(Boolean, default=False)
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="profile")
    referred_by = relationship("User", foreign_keys=[referred_by_user_id])
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, total_xp={self.total_xp}, rank={self.current_rank})>"

# ==========================================
# TRADING MODELS
# ==========================================

class Trade(Base):
    __tablename__ = 'trades'
    
    trade_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Trade identifiers
    mt5_ticket = Column(BigInteger, unique=True)
    internal_id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    
    # Trade details
    symbol = Column(String(20), nullable=False, index=True)
    direction = Column(String(10), nullable=False)
    lot_size = Column(Numeric(10, 2), nullable=False)
    
    # Prices
    entry_price = Column(Numeric(10, 5), nullable=False)
    exit_price = Column(Numeric(10, 5))
    stop_loss = Column(Numeric(10, 5))
    take_profit = Column(Numeric(10, 5))
    
    # Results
    profit_usd = Column(Numeric(15, 2))
    profit_pips = Column(Numeric(10, 2))
    commission = Column(Numeric(10, 2), default=0)
    swap = Column(Numeric(10, 2), default=0)
    
    # Risk metrics
    risk_amount = Column(Numeric(15, 2))
    risk_percent = Column(Numeric(5, 2))
    risk_reward_ratio = Column(Numeric(5, 2))
    
    # BITTEN specific
    tcs_score = Column(Integer)
    fire_mode = Column(String(50), index=True)
    tier_at_trade = Column(String(50))
    
    # Status
    status = Column(String(50), nullable=False, default=TradeStatus.PENDING.value, index=True)
    close_reason = Column(String(100))
    
    # Timing
    signal_time = Column(DateTime(timezone=True))
    open_time = Column(DateTime(timezone=True), index=True)
    close_time = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Constraints
    __table_args__ = (
        CheckConstraint(direction.in_(['BUY', 'SELL']), name='check_direction'),
        Index('idx_trades_user_profit', 'user_id', 'profit_usd'),
        Index('idx_trades_user_time', 'user_id', 'open_time'),
    )
    
    # Relationships
    user = relationship("User", back_populates="trades")
    modifications = relationship("TradeModification", back_populates="trade", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Trade(trade_id={self.trade_id}, symbol={self.symbol}, profit={self.profit_usd})>"


class TradeModification(Base):
    __tablename__ = 'trade_modifications'
    
    modification_id = Column(BigInteger, primary_key=True)
    trade_id = Column(BigInteger, ForeignKey('trades.trade_id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    
    modification_type = Column(String(50), nullable=False)
    old_value = Column(Numeric(10, 5))
    new_value = Column(Numeric(10, 5))
    reason = Column(Text)
    
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    
    # Relationships
    trade = relationship("Trade", back_populates="modifications")

# ==========================================
# RISK MANAGEMENT MODELS
# ==========================================

class RiskSession(Base):
    __tablename__ = 'risk_sessions'
    
    session_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    session_date = Column(Date, nullable=False)
    
    # Daily stats
    starting_balance = Column(Numeric(15, 2), nullable=False)
    ending_balance = Column(Numeric(15, 2))
    trades_taken = Column(Integer, default=0)
    trades_won = Column(Integer, default=0)
    trades_lost = Column(Integer, default=0)
    
    # Risk metrics
    daily_pnl = Column(Numeric(15, 2), default=0)
    daily_pnl_percent = Column(Numeric(5, 2), default=0)
    max_drawdown_percent = Column(Numeric(5, 2), default=0)
    
    # Behavioral tracking
    consecutive_losses = Column(Integer, default=0)
    consecutive_wins = Column(Integer, default=0)
    tilt_strikes = Column(Integer, default=0)
    medic_mode_activated = Column(Boolean, default=False)
    medic_activated_at = Column(DateTime(timezone=True))
    
    # Cooldowns
    cooldown_active = Column(Boolean, default=False)
    cooldown_expires_at = Column(DateTime(timezone=True))
    cooldown_reason = Column(Text)
    
    # Risk mode
    risk_mode = Column(String(50), default=RiskMode.DEFAULT.value)
    risk_percent_used = Column(Numeric(5, 2))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'session_date', name='unique_user_session_date'),
        Index('idx_risk_sessions_user_date', 'user_id', 'session_date'),
        Index('idx_risk_sessions_active', 'user_id', postgresql_where=Column('cooldown_active') == True),
    )
    
    # Relationships
    user = relationship("User", back_populates="risk_sessions")
    
    def __repr__(self):
        return f"<RiskSession(user_id={self.user_id}, date={self.session_date}, pnl={self.daily_pnl})>"

# ==========================================
# XP & GAMIFICATION MODELS
# ==========================================

class XPTransaction(Base):
    __tablename__ = 'xp_transactions'
    
    transaction_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    
    # Source tracking
    source_type = Column(String(50), nullable=False)  # trade, achievement, daily, referral, bonus
    source_id = Column(BigInteger)
    
    # Details
    description = Column(Text)
    multipliers = Column(JSONB, default=list)
    
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="xp_transactions")
    
    def __repr__(self):
        return f"<XPTransaction(user_id={self.user_id}, amount={self.amount}, source={self.source_type})>"


class Achievement(Base):
    __tablename__ = 'achievements'
    
    achievement_id = Column(BigInteger, primary_key=True)
    
    # Definition
    code = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50), index=True)
    tier = Column(String(50), index=True)  # bronze, silver, gold, platinum
    
    # Requirements
    requirements = Column(JSONB, nullable=False)
    
    # Rewards
    xp_reward = Column(Integer, default=0)
    medal_reward = Column(JSONB)
    unlock_features = Column(JSONB)
    
    # Display
    icon_url = Column(String(500))
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    
    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement")
    
    def __repr__(self):
        return f"<Achievement(code={self.code}, name={self.name}, tier={self.tier})>"


class UserAchievement(Base):
    __tablename__ = 'user_achievements'
    
    user_achievement_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    achievement_id = Column(BigInteger, ForeignKey('achievements.achievement_id'), nullable=False)
    
    earned_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    progress = Column(JSONB, default=dict)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'achievement_id', name='unique_user_achievement'),
    )
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")
    
    def __repr__(self):
        return f"<UserAchievement(user_id={self.user_id}, achievement_id={self.achievement_id})>"

# ==========================================
# NEWS & MARKET DATA MODELS
# ==========================================

class NewsEvent(Base):
    __tablename__ = 'news_events'
    
    event_id = Column(BigInteger, primary_key=True)
    
    # Event details
    external_id = Column(String(255), unique=True)
    title = Column(String(500), nullable=False)
    country = Column(String(10))
    currency = Column(String(10), index=True)
    impact = Column(String(20), index=True)
    
    # Times
    event_time = Column(DateTime(timezone=True), nullable=False, index=True)
    blackout_start = Column(DateTime(timezone=True))
    blackout_end = Column(DateTime(timezone=True))
    
    # Data
    forecast = Column(String(50))
    previous = Column(String(50))
    actual = Column(String(50))
    
    # Metadata
    source = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    def __repr__(self):
        return f"<NewsEvent(title={self.title}, currency={self.currency}, impact={self.impact})>"

# ==========================================
# SUBSCRIPTION & PAYMENT MODELS
# ==========================================

class SubscriptionPlan(Base):
    __tablename__ = 'subscription_plans'
    
    plan_id = Column(BigInteger, primary_key=True)
    
    tier = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Pricing
    price_usd = Column(Numeric(10, 2), nullable=False)
    price_crypto = Column(JSONB)
    billing_period = Column(String(50), default='monthly')
    
    # Features
    features = Column(JSONB, nullable=False)
    limits = Column(JSONB, nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    
    # Relationships
    subscriptions = relationship("UserSubscription", back_populates="plan")
    
    def __repr__(self):
        return f"<SubscriptionPlan(tier={self.tier}, price={self.price_usd})>"


class UserSubscription(Base):
    __tablename__ = 'user_subscriptions'
    
    subscription_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    plan_id = Column(BigInteger, ForeignKey('subscription_plans.plan_id'), nullable=False)
    
    # Status
    status = Column(String(50), nullable=False, default='pending', index=True)
    started_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), index=True)
    cancelled_at = Column(DateTime(timezone=True))
    
    # Payment
    payment_method = Column(String(50))
    payment_processor = Column(String(50))
    processor_subscription_id = Column(String(255))
    
    # Billing
    last_payment_at = Column(DateTime(timezone=True))
    next_payment_at = Column(DateTime(timezone=True))
    payment_failures = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=True), default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    payments = relationship("PaymentTransaction", back_populates="subscription")
    
    def __repr__(self):
        return f"<UserSubscription(user_id={self.user_id}, plan={self.plan_id}, status={self.status})>"


class PaymentTransaction(Base):
    __tablename__ = 'payment_transactions'
    
    transaction_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    subscription_id = Column(BigInteger, ForeignKey('user_subscriptions.subscription_id'))
    
    # Transaction details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False)
    payment_method = Column(String(50))
    processor = Column(String(50))
    processor_transaction_id = Column(String(255))
    
    # Status
    status = Column(String(50), nullable=False, default='pending', index=True)
    failure_reason = Column(Text)
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="payments")
    subscription = relationship("UserSubscription", back_populates="payments")
    
    def __repr__(self):
        return f"<PaymentTransaction(transaction_id={self.transaction_id}, amount={self.amount}, status={self.status})>"

# ==========================================
# AUDIT MODEL
# ==========================================

class AuditLog(Base):
    __tablename__ = 'audit_log'
    
    log_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'))
    
    action = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(100))
    entity_id = Column(BigInteger)
    
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    created_at = Column(DateTime(timezone=True), default=func.current_timestamp(), index=True)
    
    def __repr__(self):
        return f"<AuditLog(action={self.action}, user_id={self.user_id})>"