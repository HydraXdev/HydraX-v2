"""
Database Models for HydraX v2 Engagement System
SQLAlchemy models for user engagement data
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.sqlite import JSON
import json
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class User(Base):
    """Basic user model"""
    __tablename__ = 'users'
    
    id = Column(String(255), primary_key=True)
    username = Column(String(255), nullable=True)
    telegram_id = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), default='en')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}')>"

class UserProfile(Base):
    """User profile information"""
    __tablename__ = 'user_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False)
    tier = Column(String(50), default='NIBBLER')
    bio = Column(Text, nullable=True)
    timezone = Column(String(50), default='UTC')
    preferences = Column(Text, default='{}')  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserProfile(user_id='{self.user_id}', tier='{self.tier}')>"

class SubscriptionStatus(Base):
    """Subscription status types"""
    __tablename__ = 'subscription_statuses'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<SubscriptionStatus(name='{self.name}')>"

class UserSubscription(Base):
    """User subscription information"""
    __tablename__ = 'user_subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False)
    status_id = Column(Integer, ForeignKey('subscription_statuses.id'), nullable=False)
    tier = Column(String(50), default='NIBBLER')
    starts_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserSubscription(user_id='{self.user_id}', tier='{self.tier}')>"

class UserLoginStreak(Base):
    """User login streak tracking"""
    __tablename__ = 'user_login_streaks'
    
    user_id = Column(String(255), primary_key=True)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_login = Column(DateTime)
    total_logins = Column(Integer, default=0)
    streak_rewards_claimed = Column(Text, default='[]')  # JSON array of claimed milestone days
    timezone = Column(String(50), default='UTC')  # User's timezone
    grace_period_used = Column(DateTime, nullable=True)  # Last time grace period was used
    streak_status = Column(String(20), default='active')  # active, grace_period, protected, broken
    comeback_eligible = Column(Boolean, default=False)  # Eligible for comeback bonus
    last_streak_break = Column(DateTime, nullable=True)  # When streak was last broken
    total_streak_days = Column(Integer, default=0)  # Total days ever logged in
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    personal_records = relationship("PersonalRecord", back_populates="user")
    daily_missions = relationship("DailyMission", back_populates="user")
    mystery_boxes = relationship("MysteryBox", back_populates="user")
    campaign_progress = relationship("UserCampaignProgress", back_populates="user")
    engagement_events = relationship("EngagementEvent", back_populates="user")
    reward_claims = relationship("RewardClaim", back_populates="user")
    streak_protections = relationship("StreakProtection", back_populates="user")
    daily_logins = relationship("DailyLoginRecord", back_populates="user")
    streak_milestones = relationship("StreakMilestone", back_populates="user")
    comeback_bonuses = relationship("ComebackBonus", back_populates="user")
    
    def __repr__(self):
        return f"<UserLoginStreak(user_id='{self.user_id}', current_streak={self.current_streak})>"
    
    @validates('streak_rewards_claimed')
    def validate_streak_rewards_claimed(self, key, value):
        """Validate that streak rewards claimed is valid JSON"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON for streak_rewards_claimed: {value}")
                return '[]'
        return value
    
    def get_claimed_rewards(self) -> List[int]:
        """Get list of claimed reward milestone days"""
        try:
            return json.loads(self.streak_rewards_claimed)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_claimed_rewards(self, rewards: List[int]):
        """Set claimed reward milestone days"""
        self.streak_rewards_claimed = json.dumps(rewards)
    
    def add_claimed_reward(self, day: int):
        """Add a claimed reward milestone day"""
        claimed = self.get_claimed_rewards()
        if day not in claimed:
            claimed.append(day)
            self.set_claimed_rewards(claimed)

class PersonalRecord(Base):
    """Personal best records for users"""
    __tablename__ = 'personal_records'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey('user_login_streaks.user_id'), nullable=False)
    record_type = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    achieved_at = Column(DateTime, nullable=False)
    details = Column(Text, default='{}')  # JSON object with additional details
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserLoginStreak", back_populates="personal_records")
    
    # Indexes
    __table_args__ = (
        Index('idx_personal_records_user_record', 'user_id', 'record_type', unique=True),
        Index('idx_personal_records_type', 'record_type'),
    )
    
    def __repr__(self):
        return f"<PersonalRecord(user_id='{self.user_id}', type='{self.record_type}', value={self.value})>"
    
    @validates('details')
    def validate_details(self, key, value):
        """Validate that details is valid JSON"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON for details: {value}")
                return '{}'
        return value
    
    def get_details(self) -> Dict[str, Any]:
        """Get details as dictionary"""
        try:
            return json.loads(self.details)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_details(self, details: Dict[str, Any]):
        """Set details from dictionary"""
        self.details = json.dumps(details)

class DailyMission(Base):
    """Daily missions for users"""
    __tablename__ = 'daily_missions'
    
    id = Column(Integer, primary_key=True)
    mission_id = Column(String(255), unique=True, nullable=False)
    user_id = Column(String(255), ForeignKey('user_login_streaks.user_id'), nullable=False)
    bot_id = Column(String(255), nullable=False)
    mission_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    target_value = Column(Integer, nullable=False)
    current_progress = Column(Integer, default=0)
    rewards = Column(Text, default='[]')  # JSON array of rewards
    is_completed = Column(Boolean, default=False)
    is_claimed = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserLoginStreak", back_populates="daily_missions")
    
    # Indexes
    __table_args__ = (
        Index('idx_daily_missions_user_id', 'user_id'),
        Index('idx_daily_missions_expires', 'expires_at'),
        Index('idx_daily_missions_type', 'mission_type'),
    )
    
    def __repr__(self):
        return f"<DailyMission(mission_id='{self.mission_id}', user_id='{self.user_id}', type='{self.mission_type}')>"
    
    @validates('rewards')
    def validate_rewards(self, key, value):
        """Validate that rewards is valid JSON"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON for rewards: {value}")
                return '[]'
        return value
    
    def get_rewards(self) -> List[Dict[str, Any]]:
        """Get rewards as list of dictionaries"""
        try:
            return json.loads(self.rewards)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_rewards(self, rewards: List[Dict[str, Any]]):
        """Set rewards from list of dictionaries"""
        self.rewards = json.dumps(rewards)
    
    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage"""
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_progress / self.target_value) * 100)
    
    @property
    def is_expired(self) -> bool:
        """Check if mission is expired"""
        return datetime.utcnow() > self.expires_at

class MysteryBox(Base):
    """Mystery boxes for users"""
    __tablename__ = 'mystery_boxes'
    
    id = Column(Integer, primary_key=True)
    box_id = Column(String(255), unique=True, nullable=False)
    user_id = Column(String(255), ForeignKey('user_login_streaks.user_id'), nullable=False)
    rarity = Column(String(50), nullable=False)
    contents = Column(Text, default='[]')  # JSON array of contents
    source = Column(String(100), nullable=False)
    opened_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserLoginStreak", back_populates="mystery_boxes")
    
    # Indexes
    __table_args__ = (
        Index('idx_mystery_boxes_user_id', 'user_id'),
        Index('idx_mystery_boxes_rarity', 'rarity'),
        Index('idx_mystery_boxes_opened', 'opened_at'),
    )
    
    def __repr__(self):
        return f"<MysteryBox(box_id='{self.box_id}', user_id='{self.user_id}', rarity='{self.rarity}')>"
    
    @validates('contents')
    def validate_contents(self, key, value):
        """Validate that contents is valid JSON"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON for contents: {value}")
                return '[]'
        return value
    
    def get_contents(self) -> List[Dict[str, Any]]:
        """Get contents as list of dictionaries"""
        try:
            return json.loads(self.contents)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_contents(self, contents: List[Dict[str, Any]]):
        """Set contents from list of dictionaries"""
        self.contents = json.dumps(contents)
    
    @property
    def is_opened(self) -> bool:
        """Check if box is opened"""
        return self.opened_at is not None
    
    def open_box(self):
        """Mark box as opened"""
        if not self.is_opened:
            self.opened_at = datetime.utcnow()

class SeasonalCampaign(Base):
    """Seasonal campaigns"""
    __tablename__ = 'seasonal_campaigns'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    milestones = Column(Text, default='[]')  # JSON array of milestones
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_progress = relationship("UserCampaignProgress", back_populates="campaign")
    
    def __repr__(self):
        return f"<SeasonalCampaign(campaign_id='{self.campaign_id}', name='{self.name}')>"
    
    @validates('milestones')
    def validate_milestones(self, key, value):
        """Validate that milestones is valid JSON"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON for milestones: {value}")
                return '[]'
        return value
    
    def get_milestones(self) -> List[Dict[str, Any]]:
        """Get milestones as list of dictionaries"""
        try:
            return json.loads(self.milestones)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_milestones(self, milestones: List[Dict[str, Any]]):
        """Set milestones from list of dictionaries"""
        self.milestones = json.dumps(milestones)
    
    @property
    def is_current(self) -> bool:
        """Check if campaign is currently active"""
        now = datetime.utcnow()
        return self.is_active and self.start_date <= now <= self.end_date
    
    @property
    def days_remaining(self) -> int:
        """Get days remaining in campaign"""
        if not self.is_current:
            return 0
        return max(0, (self.end_date - datetime.utcnow()).days)

class UserCampaignProgress(Base):
    """User progress in seasonal campaigns"""
    __tablename__ = 'user_campaign_progress'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey('user_login_streaks.user_id'), nullable=False)
    campaign_id = Column(String(255), ForeignKey('seasonal_campaigns.campaign_id'), nullable=False)
    current_progress = Column(Integer, default=0)
    completed_milestones = Column(Text, default='[]')  # JSON array of completed milestone indexes
    total_rewards_claimed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserLoginStreak", back_populates="campaign_progress")
    campaign = relationship("SeasonalCampaign", back_populates="user_progress")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_campaign_progress_user_campaign', 'user_id', 'campaign_id', unique=True),
    )
    
    def __repr__(self):
        return f"<UserCampaignProgress(user_id='{self.user_id}', campaign_id='{self.campaign_id}', progress={self.current_progress})>"
    
    @validates('completed_milestones')
    def validate_completed_milestones(self, key, value):
        """Validate that completed_milestones is valid JSON"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON for completed_milestones: {value}")
                return '[]'
        return value
    
    def get_completed_milestones(self) -> List[int]:
        """Get completed milestones as list of integers"""
        try:
            return json.loads(self.completed_milestones)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_completed_milestones(self, milestones: List[int]):
        """Set completed milestones from list of integers"""
        self.completed_milestones = json.dumps(milestones)
    
    def add_completed_milestone(self, milestone_index: int):
        """Add a completed milestone"""
        completed = self.get_completed_milestones()
        if milestone_index not in completed:
            completed.append(milestone_index)
            self.set_completed_milestones(completed)
            self.total_rewards_claimed += 1

class EngagementEvent(Base):
    """Log of engagement events"""
    __tablename__ = 'engagement_events'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey('user_login_streaks.user_id'), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_data = Column(Text, default='{}')  # JSON object with event data
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserLoginStreak", back_populates="engagement_events")
    
    # Indexes
    __table_args__ = (
        Index('idx_engagement_events_user_id', 'user_id'),
        Index('idx_engagement_events_type', 'event_type'),
        Index('idx_engagement_events_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<EngagementEvent(user_id='{self.user_id}', event_type='{self.event_type}')>"
    
    @validates('event_data')
    def validate_event_data(self, key, value):
        """Validate that event_data is valid JSON"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON for event_data: {value}")
                return '{}'
        return value
    
    def get_event_data(self) -> Dict[str, Any]:
        """Get event data as dictionary"""
        try:
            return json.loads(self.event_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_event_data(self, data: Dict[str, Any]):
        """Set event data from dictionary"""
        self.event_data = json.dumps(data)

class RewardClaim(Base):
    """Record of reward claims"""
    __tablename__ = 'reward_claims'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey('user_login_streaks.user_id'), nullable=False)
    reward_type = Column(String(100), nullable=False)
    reward_amount = Column(String(255), nullable=False)  # Can be number or string
    reward_metadata = Column(Text, default='{}')  # JSON object with additional reward info
    source = Column(String(100), nullable=False)  # Where reward came from
    claimed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserLoginStreak", back_populates="reward_claims")
    
    # Indexes
    __table_args__ = (
        Index('idx_reward_claims_user_id', 'user_id'),
        Index('idx_reward_claims_type', 'reward_type'),
        Index('idx_reward_claims_source', 'source'),
        Index('idx_reward_claims_claimed_at', 'claimed_at'),
    )
    
    def __repr__(self):
        return f"<RewardClaim(user_id='{self.user_id}', reward_type='{self.reward_type}', amount='{self.reward_amount}')>"
    
    @validates('reward_metadata')
    def validate_reward_metadata(self, key, value):
        """Validate that reward_metadata is valid JSON"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON for reward_metadata: {value}")
                return '{}'
        return value
    
    def get_reward_metadata(self) -> Dict[str, Any]:
        """Get reward metadata as dictionary"""
        try:
            return json.loads(self.reward_metadata)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_reward_metadata(self, metadata: Dict[str, Any]):
        """Set reward metadata from dictionary"""
        self.reward_metadata = json.dumps(metadata)

# Additional utility functions for database operations
def create_all_tables(engine):
    """Create all tables in the database"""
    try:
        Base.metadata.create_all(engine)
        logger.info("All engagement system tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

def drop_all_tables(engine):
    """Drop all tables in the database"""
    try:
        Base.metadata.drop_all(engine)
        logger.info("All engagement system tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        raise

class StreakProtection(Base):
    """Streak protection usage tracking"""
    __tablename__ = 'streak_protections'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey('user_login_streaks.user_id'), nullable=False)
    protection_type = Column(String(50), nullable=False)  # free_monthly, premium, weekend_pass
    used_date = Column(DateTime, nullable=False)
    streak_saved = Column(Integer, nullable=False)  # Streak value when protection was used
    days_missed = Column(Integer, default=1)  # How many days were protected
    expires_at = Column(DateTime, nullable=True)  # When protection expires (for time-based)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserLoginStreak", back_populates="streak_protections")
    
    # Indexes
    __table_args__ = (
        Index('idx_streak_protections_user_date', 'user_id', 'used_date'),
        Index('idx_streak_protections_type', 'protection_type'),
    )
    
    def __repr__(self):
        return f"<StreakProtection(user_id='{self.user_id}', type='{self.protection_type}', streak_saved={self.streak_saved})>"

class DailyLoginRecord(Base):
    """Daily login history tracking"""
    __tablename__ = 'daily_login_records'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey('user_login_streaks.user_id'), nullable=False)
    login_date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    login_timestamp = Column(DateTime, nullable=False)
    timezone = Column(String(50), nullable=False)
    streak_day = Column(Integer, nullable=False)  # Which day of streak this was
    xp_earned = Column(Integer, default=0)
    multiplier_applied = Column(Float, default=1.0)
    bonuses_applied = Column(Text, default='[]')  # JSON array of bonus types
    login_method = Column(String(50), default='manual')  # manual, auto, scheduled
    device_info = Column(Text, default='{}')  # JSON object with device details
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserLoginStreak", back_populates="daily_logins")
    
    # Indexes
    __table_args__ = (
        Index('idx_daily_login_user_date', 'user_id', 'login_date', unique=True),
        Index('idx_daily_login_timestamp', 'login_timestamp'),
        Index('idx_daily_login_streak_day', 'streak_day'),
    )
    
    def __repr__(self):
        return f"<DailyLoginRecord(user_id='{self.user_id}', date='{self.login_date}', streak_day={self.streak_day})>"
    
    @validates('bonuses_applied')
    def validate_bonuses_applied(self, key, value):
        """Validate that bonuses_applied is valid JSON"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON for bonuses_applied: {value}")
                return '[]'
        return value
    
    @validates('device_info')
    def validate_device_info(self, key, value):
        """Validate that device_info is valid JSON"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON for device_info: {value}")
                return '{}'
        return value
    
    def get_bonuses_applied(self) -> List[str]:
        """Get bonuses applied as list"""
        try:
            return json.loads(self.bonuses_applied)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_bonuses_applied(self, bonuses: List[str]):
        """Set bonuses applied from list"""
        self.bonuses_applied = json.dumps(bonuses)
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get device info as dictionary"""
        try:
            return json.loads(self.device_info)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_device_info(self, info: Dict[str, Any]):
        """Set device info from dictionary"""
        self.device_info = json.dumps(info)

class StreakMilestone(Base):
    """Streak milestone achievements"""
    __tablename__ = 'streak_milestones'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey('user_login_streaks.user_id'), nullable=False)
    milestone_day = Column(Integer, nullable=False)  # 7, 30, 90, 365, etc.
    achieved_date = Column(DateTime, nullable=False)
    rewards_claimed = Column(Text, default='[]')  # JSON array of claimed rewards
    special_rewards = Column(Text, default='[]')  # JSON array of special items/privileges
    badges_unlocked = Column(Text, default='[]')  # JSON array of badge IDs
    titles_unlocked = Column(Text, default='[]')  # JSON array of title IDs
    xp_bonus_received = Column(Integer, default=0)
    celebration_viewed = Column(Boolean, default=False)
    shared_publicly = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserLoginStreak", back_populates="streak_milestones")
    
    # Indexes
    __table_args__ = (
        Index('idx_streak_milestones_user_milestone', 'user_id', 'milestone_day', unique=True),
        Index('idx_streak_milestones_achieved_date', 'achieved_date'),
        Index('idx_streak_milestones_day', 'milestone_day'),
    )
    
    def __repr__(self):
        return f"<StreakMilestone(user_id='{self.user_id}', milestone_day={self.milestone_day})>"
    
    @validates('rewards_claimed', 'special_rewards', 'badges_unlocked', 'titles_unlocked')
    def validate_json_fields(self, key, value):
        """Validate that JSON fields are valid"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON for {key}: {value}")
                return '[]'
        return value
    
    def get_rewards_claimed(self) -> List[str]:
        """Get claimed rewards as list"""
        try:
            return json.loads(self.rewards_claimed)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_rewards_claimed(self, rewards: List[str]):
        """Set claimed rewards from list"""
        self.rewards_claimed = json.dumps(rewards)
    
    def get_badges_unlocked(self) -> List[str]:
        """Get unlocked badges as list"""
        try:
            return json.loads(self.badges_unlocked)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_badges_unlocked(self, badges: List[str]):
        """Set unlocked badges from list"""
        self.badges_unlocked = json.dumps(badges)

class ComebackBonus(Base):
    """Comeback bonus tracking for returning users"""
    __tablename__ = 'comeback_bonuses'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey('user_login_streaks.user_id'), nullable=False)
    days_away = Column(Integer, nullable=False)  # How many days user was away
    bonus_multiplier = Column(Float, nullable=False)  # XP multiplier applied
    xp_bonus_earned = Column(Integer, default=0)  # Additional XP from comeback
    special_items_received = Column(Text, default='[]')  # JSON array of bonus items
    return_date = Column(DateTime, nullable=False)
    previous_streak = Column(Integer, default=0)  # Streak before they left
    message_shown = Column(Text, nullable=True)  # Welcome back message
    celebration_level = Column(String(20), default='normal')  # normal, special, epic
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserLoginStreak", back_populates="comeback_bonuses")
    
    # Indexes
    __table_args__ = (
        Index('idx_comeback_bonuses_user_date', 'user_id', 'return_date'),
        Index('idx_comeback_bonuses_days_away', 'days_away'),
        Index('idx_comeback_bonuses_multiplier', 'bonus_multiplier'),
    )
    
    def __repr__(self):
        return f"<ComebackBonus(user_id='{self.user_id}', days_away={self.days_away}, multiplier={self.bonus_multiplier})>"
    
    @validates('special_items_received')
    def validate_special_items_received(self, key, value):
        """Validate that special_items_received is valid JSON"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON for special_items_received: {value}")
                return '[]'
        return value
    
    def get_special_items_received(self) -> List[Dict[str, Any]]:
        """Get special items as list of dictionaries"""
        try:
            return json.loads(self.special_items_received)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_special_items_received(self, items: List[Dict[str, Any]]):
        """Set special items from list of dictionaries"""
        self.special_items_received = json.dumps(items)

class StreakCalendar(Base):
    """Visual streak calendar data for UI"""
    __tablename__ = 'streak_calendar'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey('user_login_streaks.user_id'), nullable=False)
    calendar_date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    status = Column(String(20), nullable=False)  # login, missed, protected, grace, milestone
    streak_count = Column(Integer, default=0)  # Streak count on this day
    notes = Column(Text, nullable=True)  # Special notes for the day
    milestone_achieved = Column(Integer, nullable=True)  # Milestone day if achieved
    protection_used = Column(String(50), nullable=True)  # Type of protection used
    xp_earned = Column(Integer, default=0)  # XP earned on this day
    bonus_type = Column(String(50), nullable=True)  # Type of bonus applied
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_streak_calendar_user_date', 'user_id', 'calendar_date', unique=True),
        Index('idx_streak_calendar_status', 'status'),
        Index('idx_streak_calendar_milestone', 'milestone_achieved'),
    )
    
    def __repr__(self):
        return f"<StreakCalendar(user_id='{self.user_id}', date='{self.calendar_date}', status='{self.status}')>"

class UserBadge(Base):
    """User-owned badges from streak achievements"""
    __tablename__ = 'user_badges'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey('user_login_streaks.user_id'), nullable=False)
    badge_id = Column(String(100), nullable=False)  # week_warrior, monthly_master, etc.
    badge_name = Column(String(255), nullable=False)
    badge_tier = Column(String(20), nullable=False)  # common, uncommon, rare, epic, legendary, mythic
    earned_date = Column(DateTime, nullable=False)
    source_milestone = Column(Integer, nullable=True)  # Which streak milestone unlocked this
    xp_bonus = Column(Float, default=0.0)  # Permanent XP bonus
    trading_bonus = Column(Float, default=0.0)  # Trading reward bonus
    is_equipped = Column(Boolean, default=False)  # Whether badge is currently displayed
    display_order = Column(Integer, default=0)  # Order for display
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_badges_user_badge', 'user_id', 'badge_id', unique=True),
        Index('idx_user_badges_tier', 'badge_tier'),
        Index('idx_user_badges_equipped', 'is_equipped'),
    )
    
    def __repr__(self):
        return f"<UserBadge(user_id='{self.user_id}', badge_id='{self.badge_id}', tier='{self.badge_tier}')>"

class UserTitle(Base):
    """User-owned titles from streak achievements"""
    __tablename__ = 'user_titles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey('user_login_streaks.user_id'), nullable=False)
    title_id = Column(String(100), nullable=False)  # consistent_trader, elite_trader, etc.
    title_name = Column(String(255), nullable=False)
    title_rank = Column(String(20), nullable=False)  # recruit, soldier, veteran, elite, legend, mythic
    prestige_level = Column(Integer, default=1)
    earned_date = Column(DateTime, nullable=False)
    source_milestone = Column(Integer, nullable=True)  # Which streak milestone unlocked this
    is_active = Column(Boolean, default=False)  # Whether title is currently displayed
    display_color = Column(String(7), default='#FFD700')  # Hex color for display
    effects = Column(Text, default='{}')  # JSON object with title effects/bonuses
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_titles_user_title', 'user_id', 'title_id', unique=True),
        Index('idx_user_titles_rank', 'title_rank'),
        Index('idx_user_titles_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<UserTitle(user_id='{self.user_id}', title_id='{self.title_id}', rank='{self.title_rank}')>"
    
    @validates('effects')
    def validate_effects(self, key, value):
        """Validate that effects is valid JSON"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON for effects: {value}")
                return '{}'
        return value
    
    def get_effects(self) -> Dict[str, Any]:
        """Get effects as dictionary"""
        try:
            return json.loads(self.effects)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_effects(self, effects: Dict[str, Any]):
        """Set effects from dictionary"""
        self.effects = json.dumps(effects)

# Export all models for easy importing
__all__ = [
    'Base',
    'User',
    'UserProfile',
    'SubscriptionStatus',
    'UserSubscription',
    'UserLoginStreak',
    'PersonalRecord',
    'DailyMission',
    'MysteryBox',
    'SeasonalCampaign',
    'UserCampaignProgress',
    'EngagementEvent',
    'RewardClaim',
    'StreakProtection',
    'DailyLoginRecord',
    'StreakMilestone',
    'ComebackBonus',
    'StreakCalendar',
    'UserBadge',
    'UserTitle',
    'create_all_tables',
    'drop_all_tables'
]