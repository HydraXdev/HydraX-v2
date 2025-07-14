"""
BITTEN Press Pass Manager
Handles Press Pass claims, email capture, and conversion tracking
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json
import random
import asyncio
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, JSON, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import IntegrityError
import redis
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://bitten_app:password@localhost/bitten_production')
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis configuration
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connection established for Press Pass manager")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@joinbitten.com')

# Constants
WEEKLY_PRESS_PASS_LIMIT = 200
DAILY_URGENCY_RESET_HOUR = 0  # UTC
PRESS_PASS_DURATION_DAYS = 7
PRESS_PASS_DAILY_LIMIT = 30  # Display limit for urgency
INITIAL_XP_BONUS = 50

class PressPassClaim(Base):
    """Press Pass claims table"""
    __tablename__ = 'press_pass_claims'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    claim_token = Column(String(255), unique=True, nullable=False)
    
    # Tracking
    claimed_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    activated = Column(Boolean, default=False)
    activated_at = Column(DateTime)
    
    # Conversion tracking
    converted = Column(Boolean, default=False)
    converted_at = Column(DateTime)
    conversion_tier = Column(String(50))
    
    # Analytics
    source = Column(String(100))
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    referral_code = Column(String(50))
    
    # Email engagement
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    last_email_sent_at = Column(DateTime)
    
    # A/B testing
    ab_variant = Column(String(50))
    
    # User agent and IP for analytics
    user_agent = Column(String(500))
    ip_address = Column(String(50))

class EmailCampaign(Base):
    """Email campaign tracking"""
    __tablename__ = 'email_campaigns'
    
    id = Column(Integer, primary_key=True)
    press_pass_claim_id = Column(Integer, ForeignKey('press_pass_claims.id'))
    campaign_type = Column(String(50))  # welcome, day1, day3, day6, day7
    
    # Tracking
    sent_at = Column(DateTime, default=datetime.utcnow)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    
    # Content variant for A/B testing
    content_variant = Column(String(50))
    
    # Performance
    cta_clicked = Column(String(100))

class ConversionEvent(Base):
    """Conversion event tracking"""
    __tablename__ = 'conversion_events'
    
    id = Column(Integer, primary_key=True)
    press_pass_claim_id = Column(Integer, ForeignKey('press_pass_claims.id'))
    event_type = Column(String(100))  # page_view, cta_click, signup_start, etc.
    event_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Session tracking
    session_id = Column(String(255))
    page_url = Column(String(500))

# Create tables
Base.metadata.create_all(bind=engine)

class PressPassManager:
    """Manages Press Pass claims, limits, and conversions"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.ab_variants = ['A', 'B']  # For A/B testing
        
    def get_weekly_remaining(self) -> int:
        """Get remaining Press Passes for this week"""
        try:
            # Get Monday of current week
            today = datetime.utcnow().date()
            monday = today - timedelta(days=today.weekday())
            
            # Count claims this week
            week_claims = self.db.query(PressPassClaim).filter(
                PressPassClaim.claimed_at >= monday
            ).count()
            
            remaining = max(0, WEEKLY_PRESS_PASS_LIMIT - week_claims)
            
            # Cache in Redis
            if redis_client:
                redis_client.setex(
                    'press_pass:weekly_remaining',
                    300,  # 5 minute cache
                    remaining
                )
            
            return remaining
            
        except Exception as e:
            logger.error(f"Error getting weekly remaining: {e}")
            return 100  # Default fallback
    
    def get_daily_remaining(self) -> int:
        """Get remaining Press Passes for today (for urgency display)"""
        try:
            # Check Redis cache first
            if redis_client:
                cached = redis_client.get('press_pass:daily_remaining')
                if cached:
                    return int(cached)
            
            # Calculate based on time of day
            now = datetime.utcnow()
            hours_passed = now.hour
            
            # Start with daily limit and decrease throughout the day
            # Add some randomness for realism
            base_remaining = PRESS_PASS_DAILY_LIMIT - (hours_passed * 1.2)
            remaining = max(3, int(base_remaining + random.randint(-2, 2)))
            
            # Cache for 5 minutes
            if redis_client:
                redis_client.setex('press_pass:daily_remaining', 300, remaining)
            
            return remaining
            
        except Exception as e:
            logger.error(f"Error getting daily remaining: {e}")
            return 7  # Default fallback
    
    def claim_press_pass(self, email: str, name: str, **kwargs) -> Dict[str, Any]:
        """Claim a Press Pass"""
        try:
            # Check if email already claimed
            existing = self.db.query(PressPassClaim).filter_by(email=email).first()
            if existing:
                return {
                    'success': False,
                    'error': 'email_already_claimed',
                    'message': 'This email has already claimed a Press Pass'
                }
            
            # Check weekly limit
            if self.get_weekly_remaining() <= 0:
                return {
                    'success': False,
                    'error': 'weekly_limit_reached',
                    'message': 'Weekly Press Pass limit reached. Try again next week!'
                }
            
            # Generate claim token
            claim_token = hashlib.sha256(f"{email}{datetime.utcnow()}".encode()).hexdigest()[:32]
            
            # Select A/B variant
            ab_variant = random.choice(self.ab_variants)
            
            # Create claim
            claim = PressPassClaim(
                email=email,
                name=name,
                claim_token=claim_token,
                expires_at=datetime.utcnow() + timedelta(days=PRESS_PASS_DURATION_DAYS),
                ab_variant=ab_variant,
                **kwargs  # utm params, source, etc.
            )
            
            self.db.add(claim)
            self.db.commit()
            
            # Send welcome email
            self.send_welcome_email(claim)
            
            # Track conversion event
            self.track_conversion_event(claim.id, 'press_pass_claimed', {
                'ab_variant': ab_variant
            })
            
            # Update daily counter
            self._decrement_daily_counter()
            
            return {
                'success': True,
                'claim_token': claim_token,
                'expires_at': claim.expires_at.isoformat(),
                'ab_variant': ab_variant
            }
            
        except Exception as e:
            logger.error(f"Error claiming Press Pass: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': 'system_error',
                'message': 'Unable to process request. Please try again.'
            }
    
    def activate_press_pass(self, claim_token: str, telegram_id: int) -> Dict[str, Any]:
        """Activate a Press Pass after email signup"""
        try:
            claim = self.db.query(PressPassClaim).filter_by(
                claim_token=claim_token,
                activated=False
            ).first()
            
            if not claim:
                return {
                    'success': False,
                    'error': 'invalid_token',
                    'message': 'Invalid or already activated Press Pass'
                }
            
            if claim.expires_at < datetime.utcnow():
                return {
                    'success': False,
                    'error': 'expired',
                    'message': 'This Press Pass has expired'
                }
            
            # Activate the pass
            claim.activated = True
            claim.activated_at = datetime.utcnow()
            self.db.commit()
            
            # Create user with PRESS_PASS tier
            # This would integrate with your main user creation system
            
            # Track activation
            self.track_conversion_event(claim.id, 'press_pass_activated', {
                'telegram_id': telegram_id
            })
            
            return {
                'success': True,
                'message': 'Press Pass activated successfully!',
                'expires_at': claim.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error activating Press Pass: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': 'system_error'
            }
    
    def send_welcome_email(self, claim: PressPassClaim):
        """Send welcome email with Press Pass activation link"""
        try:
            # Load email template
            template_path = '/root/HydraX-v2/templates/emails/press_pass_welcome.html'
            with open(template_path, 'r') as f:
                html_content = f.read()
            
            # Replace variables
            activation_link = f"https://t.me/bitten_bot?start=pp_{claim.claim_token}"
            html_content = html_content.replace('{{name}}', claim.name)
            html_content = html_content.replace('{{activation_link}}', activation_link)
            html_content = html_content.replace('{{expires_date}}', claim.expires_at.strftime('%B %d, %Y'))
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "🎯 Your BITTEN Press Pass is Ready!"
            msg['From'] = FROM_EMAIL
            msg['To'] = claim.email
            
            # Add tracking pixel
            tracking_pixel = f'<img src="https://joinbitten.com/track/email/open/{claim.id}/welcome" width="1" height="1" />'
            html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            if SMTP_USER and SMTP_PASSWORD:
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.send_message(msg)
                
                # Update email sent count
                claim.emails_sent += 1
                claim.last_email_sent_at = datetime.utcnow()
                self.db.commit()
                
                # Track campaign
                campaign = EmailCampaign(
                    press_pass_claim_id=claim.id,
                    campaign_type='welcome',
                    content_variant=claim.ab_variant
                )
                self.db.add(campaign)
                self.db.commit()
                
            logger.info(f"Welcome email sent to {claim.email}")
            
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
    
    def check_expiring_passes(self):
        """Check for expiring Press Passes and send reminders"""
        try:
            # Find passes expiring in 24 hours
            tomorrow = datetime.utcnow() + timedelta(days=1)
            expiring = self.db.query(PressPassClaim).filter(
                PressPassClaim.activated == True,
                PressPassClaim.converted == False,
                PressPassClaim.expires_at <= tomorrow,
                PressPassClaim.expires_at > datetime.utcnow()
            ).all()
            
            for claim in expiring:
                # Send urgency email
                self.send_expiry_reminder(claim)
            
            logger.info(f"Sent {len(expiring)} expiry reminders")
            
        except Exception as e:
            logger.error(f"Error checking expiring passes: {e}")
    
    def track_conversion_event(self, claim_id: int, event_type: str, event_data: Dict = None):
        """Track conversion events for analytics"""
        try:
            event = ConversionEvent(
                press_pass_claim_id=claim_id,
                event_type=event_type,
                event_data=event_data or {}
            )
            self.db.add(event)
            self.db.commit()
            
            # Also send to analytics platforms
            if redis_client:
                redis_client.publish('analytics:events', json.dumps({
                    'event': event_type,
                    'claim_id': claim_id,
                    'data': event_data,
                    'timestamp': datetime.utcnow().isoformat()
                }))
                
        except Exception as e:
            logger.error(f"Error tracking conversion event: {e}")
    
    def get_conversion_metrics(self) -> Dict[str, Any]:
        """Get Press Pass conversion metrics"""
        try:
            total_claims = self.db.query(PressPassClaim).count()
            activated = self.db.query(PressPassClaim).filter_by(activated=True).count()
            converted = self.db.query(PressPassClaim).filter_by(converted=True).count()
            
            # Calculate rates
            activation_rate = (activated / total_claims * 100) if total_claims > 0 else 0
            conversion_rate = (converted / activated * 100) if activated > 0 else 0
            
            # Get variant performance
            variant_stats = {}
            for variant in self.ab_variants:
                variant_claims = self.db.query(PressPassClaim).filter_by(ab_variant=variant).count()
                variant_converted = self.db.query(PressPassClaim).filter_by(
                    ab_variant=variant,
                    converted=True
                ).count()
                
                variant_stats[variant] = {
                    'claims': variant_claims,
                    'conversions': variant_converted,
                    'rate': (variant_converted / variant_claims * 100) if variant_claims > 0 else 0
                }
            
            return {
                'total_claims': total_claims,
                'activated': activated,
                'converted': converted,
                'activation_rate': round(activation_rate, 2),
                'conversion_rate': round(conversion_rate, 2),
                'variant_performance': variant_stats,
                'weekly_remaining': self.get_weekly_remaining(),
                'daily_remaining': self.get_daily_remaining()
            }
            
        except Exception as e:
            logger.error(f"Error getting conversion metrics: {e}")
            return {}
    
    def _decrement_daily_counter(self):
        """Decrement the daily counter for urgency display"""
        try:
            if redis_client:
                current = int(redis_client.get('press_pass:daily_remaining') or PRESS_PASS_DAILY_LIMIT)
                new_value = max(3, current - 1)  # Never go below 3 for urgency
                redis_client.setex('press_pass:daily_remaining', 300, new_value)
        except Exception as e:
            logger.error(f"Error decrementing daily counter: {e}")
    
    def close(self):
        """Close database connection"""
        self.db.close()

# Singleton instance
press_pass_manager = PressPassManager()