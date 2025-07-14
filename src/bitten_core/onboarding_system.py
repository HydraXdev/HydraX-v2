"""
BITTEN Onboarding System
Seamless integration from Press Pass signup to full platform onboarding
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
import asyncio
from dataclasses import dataclass
import json
import redis

# Configure logging
logger = logging.getLogger(__name__)

# Redis for state management
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=5, decode_responses=True)
    redis_client.ping()
except Exception as e:
    logger.warning(f"Redis not available for onboarding: {e}")
    redis_client = None

class OnboardingStage(Enum):
    """Onboarding stages"""
    EMAIL_CAPTURED = "email_captured"
    TELEGRAM_CONNECTED = "telegram_connected"
    DEMO_ACCOUNT_CREATED = "demo_account_created"
    FIRST_TRADE_PLACED = "first_trade_placed"
    PROFILE_COMPLETED = "profile_completed"
    TIER_SELECTED = "tier_selected"
    PAYMENT_COMPLETED = "payment_completed"
    FULLY_ACTIVATED = "fully_activated"

@dataclass
class OnboardingUser:
    """User in onboarding process"""
    email: str
    name: str
    claim_token: Optional[str] = None
    telegram_id: Optional[int] = None
    current_stage: OnboardingStage = OnboardingStage.EMAIL_CAPTURED
    stages_completed: List[OnboardingStage] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.stages_completed is None:
            self.stages_completed = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()

class OnboardingFlow:
    """Manages the complete onboarding flow"""
    
    def __init__(self):
        self.flows = {
            'press_pass': self._create_press_pass_flow(),
            'direct_signup': self._create_direct_signup_flow(),
            'referral': self._create_referral_flow()
        }
        
    def _create_press_pass_flow(self) -> List[Dict[str, Any]]:
        """Create Press Pass onboarding flow"""
        return [
            {
                'stage': OnboardingStage.EMAIL_CAPTURED,
                'actions': ['send_welcome_email', 'create_urgency_timer'],
                'next_stages': [OnboardingStage.TELEGRAM_CONNECTED]
            },
            {
                'stage': OnboardingStage.TELEGRAM_CONNECTED,
                'actions': ['activate_press_pass', 'create_demo_account', 'send_quick_start_guide'],
                'next_stages': [OnboardingStage.DEMO_ACCOUNT_CREATED]
            },
            {
                'stage': OnboardingStage.DEMO_ACCOUNT_CREATED,
                'actions': ['enable_trading', 'show_tutorial', 'track_first_trade'],
                'next_stages': [OnboardingStage.FIRST_TRADE_PLACED]
            },
            {
                'stage': OnboardingStage.FIRST_TRADE_PLACED,
                'actions': ['award_xp', 'show_results', 'encourage_profile_completion'],
                'next_stages': [OnboardingStage.PROFILE_COMPLETED, OnboardingStage.TIER_SELECTED]
            },
            {
                'stage': OnboardingStage.TIER_SELECTED,
                'actions': ['show_tier_benefits', 'create_payment_session', 'apply_press_pass_discount'],
                'next_stages': [OnboardingStage.PAYMENT_COMPLETED]
            },
            {
                'stage': OnboardingStage.PAYMENT_COMPLETED,
                'actions': ['upgrade_account', 'preserve_xp', 'send_welcome_to_tier'],
                'next_stages': [OnboardingStage.FULLY_ACTIVATED]
            }
        ]
    
    def _create_direct_signup_flow(self) -> List[Dict[str, Any]]:
        """Create direct signup flow"""
        return [
            {
                'stage': OnboardingStage.TELEGRAM_CONNECTED,
                'actions': ['show_tier_options', 'offer_demo_mode'],
                'next_stages': [OnboardingStage.TIER_SELECTED, OnboardingStage.DEMO_ACCOUNT_CREATED]
            },
            {
                'stage': OnboardingStage.TIER_SELECTED,
                'actions': ['create_payment_session', 'show_benefits'],
                'next_stages': [OnboardingStage.PAYMENT_COMPLETED]
            },
            {
                'stage': OnboardingStage.PAYMENT_COMPLETED,
                'actions': ['create_account', 'send_welcome_package', 'enable_features'],
                'next_stages': [OnboardingStage.FULLY_ACTIVATED]
            }
        ]
    
    def _create_referral_flow(self) -> List[Dict[str, Any]]:
        """Create referral onboarding flow"""
        return [
            {
                'stage': OnboardingStage.TELEGRAM_CONNECTED,
                'actions': ['apply_referral_bonus', 'notify_referrer', 'show_special_offer'],
                'next_stages': [OnboardingStage.TIER_SELECTED]
            }
        ]

class OnboardingManager:
    """Manages user onboarding state and progression"""
    
    def __init__(self):
        self.flow_manager = OnboardingFlow()
        self.action_handlers = self._init_action_handlers()
    
    def _init_action_handlers(self) -> Dict[str, callable]:
        """Initialize action handlers"""
        return {
            'send_welcome_email': self._send_welcome_email,
            'create_urgency_timer': self._create_urgency_timer,
            'activate_press_pass': self._activate_press_pass,
            'create_demo_account': self._create_demo_account,
            'send_quick_start_guide': self._send_quick_start_guide,
            'enable_trading': self._enable_trading,
            'show_tutorial': self._show_tutorial,
            'track_first_trade': self._track_first_trade,
            'award_xp': self._award_xp,
            'show_results': self._show_results,
            'encourage_profile_completion': self._encourage_profile_completion,
            'show_tier_benefits': self._show_tier_benefits,
            'create_payment_session': self._create_payment_session,
            'apply_press_pass_discount': self._apply_press_pass_discount,
            'upgrade_account': self._upgrade_account,
            'preserve_xp': self._preserve_xp,
            'send_welcome_to_tier': self._send_welcome_to_tier
        }
    
    def start_onboarding(self, email: str, name: str, flow_type: str = 'press_pass', **kwargs) -> OnboardingUser:
        """Start onboarding for a new user"""
        try:
            user = OnboardingUser(
                email=email,
                name=name,
                claim_token=kwargs.get('claim_token'),
                metadata={
                    'flow_type': flow_type,
                    'source': kwargs.get('source', 'web'),
                    'utm_source': kwargs.get('utm_source'),
                    'utm_campaign': kwargs.get('utm_campaign'),
                    'referral_code': kwargs.get('referral_code')
                }
            )
            
            # Save to Redis
            self._save_user_state(user)
            
            # Execute initial stage actions
            self._execute_stage_actions(user, OnboardingStage.EMAIL_CAPTURED)
            
            logger.info(f"Started {flow_type} onboarding for {email}")
            return user
            
        except Exception as e:
            logger.error(f"Error starting onboarding: {e}")
            raise
    
    def progress_user(self, identifier: str, new_stage: OnboardingStage, **kwargs) -> OnboardingUser:
        """Progress user to next onboarding stage"""
        try:
            # Load user state
            user = self._load_user_state(identifier)
            if not user:
                raise ValueError(f"User not found: {identifier}")
            
            # Validate stage progression
            flow = self.flow_manager.flows.get(user.metadata.get('flow_type', 'press_pass'))
            current_stage_config = next((s for s in flow if s['stage'] == user.current_stage), None)
            
            if current_stage_config and new_stage in current_stage_config['next_stages']:
                # Update user state
                user.current_stage = new_stage
                user.stages_completed.append(new_stage)
                user.last_activity = datetime.utcnow()
                
                # Add any additional metadata
                user.metadata.update(kwargs)
                
                # Save state
                self._save_user_state(user)
                
                # Execute stage actions
                self._execute_stage_actions(user, new_stage)
                
                logger.info(f"User {identifier} progressed to {new_stage.value}")
            else:
                logger.warning(f"Invalid stage progression from {user.current_stage.value} to {new_stage.value}")
            
            return user
            
        except Exception as e:
            logger.error(f"Error progressing user: {e}")
            raise
    
    def get_user_progress(self, identifier: str) -> Dict[str, Any]:
        """Get user's onboarding progress"""
        try:
            user = self._load_user_state(identifier)
            if not user:
                return {}
            
            flow = self.flow_manager.flows.get(user.metadata.get('flow_type', 'press_pass'))
            total_stages = len(flow)
            completed_stages = len(user.stages_completed)
            
            return {
                'email': user.email,
                'name': user.name,
                'current_stage': user.current_stage.value,
                'stages_completed': [s.value for s in user.stages_completed],
                'progress_percentage': round((completed_stages / total_stages) * 100, 2),
                'last_activity': user.last_activity.isoformat(),
                'flow_type': user.metadata.get('flow_type'),
                'is_complete': user.current_stage == OnboardingStage.FULLY_ACTIVATED
            }
            
        except Exception as e:
            logger.error(f"Error getting user progress: {e}")
            return {}
    
    def get_stuck_users(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get users who haven't progressed in X hours"""
        try:
            stuck_users = []
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # In production, this would query the database
            # For now, check Redis keys
            if redis_client:
                for key in redis_client.scan_iter("onboarding:user:*"):
                    user_data = redis_client.get(key)
                    if user_data:
                        user_dict = json.loads(user_data)
                        last_activity = datetime.fromisoformat(user_dict['last_activity'])
                        
                        if last_activity < cutoff_time and user_dict['current_stage'] != 'FULLY_ACTIVATED':
                            stuck_users.append({
                                'email': user_dict['email'],
                                'current_stage': user_dict['current_stage'],
                                'last_activity': user_dict['last_activity'],
                                'hours_stuck': (datetime.utcnow() - last_activity).total_seconds() / 3600
                            })
            
            return stuck_users
            
        except Exception as e:
            logger.error(f"Error getting stuck users: {e}")
            return []
    
    def _execute_stage_actions(self, user: OnboardingUser, stage: OnboardingStage):
        """Execute actions for a stage"""
        try:
            flow = self.flow_manager.flows.get(user.metadata.get('flow_type', 'press_pass'))
            stage_config = next((s for s in flow if s['stage'] == stage), None)
            
            if stage_config:
                for action in stage_config.get('actions', []):
                    handler = self.action_handlers.get(action)
                    if handler:
                        try:
                            handler(user)
                        except Exception as e:
                            logger.error(f"Error executing action {action}: {e}")
            
        except Exception as e:
            logger.error(f"Error executing stage actions: {e}")
    
    def _save_user_state(self, user: OnboardingUser):
        """Save user state to Redis"""
        if redis_client:
            key = f"onboarding:user:{user.email}"
            data = {
                'email': user.email,
                'name': user.name,
                'claim_token': user.claim_token,
                'telegram_id': user.telegram_id,
                'current_stage': user.current_stage.value,
                'stages_completed': [s.value for s in user.stages_completed],
                'metadata': user.metadata,
                'created_at': user.created_at.isoformat(),
                'last_activity': user.last_activity.isoformat()
            }
            redis_client.setex(key, 86400 * 30, json.dumps(data))  # 30 day TTL
    
    def _load_user_state(self, identifier: str) -> Optional[OnboardingUser]:
        """Load user state from Redis"""
        if redis_client:
            # Try email first
            key = f"onboarding:user:{identifier}"
            data = redis_client.get(key)
            
            if not data:
                # Try finding by telegram_id
                for key in redis_client.scan_iter("onboarding:user:*"):
                    user_data = redis_client.get(key)
                    if user_data:
                        user_dict = json.loads(user_data)
                        if str(user_dict.get('telegram_id')) == str(identifier):
                            data = user_data
                            break
            
            if data:
                user_dict = json.loads(data)
                return OnboardingUser(
                    email=user_dict['email'],
                    name=user_dict['name'],
                    claim_token=user_dict.get('claim_token'),
                    telegram_id=user_dict.get('telegram_id'),
                    current_stage=OnboardingStage(user_dict['current_stage']),
                    stages_completed=[OnboardingStage(s) for s in user_dict['stages_completed']],
                    metadata=user_dict['metadata'],
                    created_at=datetime.fromisoformat(user_dict['created_at']),
                    last_activity=datetime.fromisoformat(user_dict['last_activity'])
                )
        
        return None
    
    # Action handler implementations
    def _send_welcome_email(self, user: OnboardingUser):
        """Send welcome email"""
        logger.info(f"Sending welcome email to {user.email}")
        # Implementation would call email service
    
    def _create_urgency_timer(self, user: OnboardingUser):
        """Create urgency timer for Press Pass"""
        if redis_client:
            redis_client.setex(
                f"urgency:press_pass:{user.email}",
                86400 * 7,  # 7 days
                json.dumps({
                    'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat()
                })
            )
    
    def _activate_press_pass(self, user: OnboardingUser):
        """Activate user's Press Pass"""
        logger.info(f"Activating Press Pass for {user.email}")
        # Implementation would activate in database
    
    def _create_demo_account(self, user: OnboardingUser):
        """Create MT5 demo account"""
        logger.info(f"Creating demo account for {user.email}")
        # Implementation would create MT5 account
    
    def _send_quick_start_guide(self, user: OnboardingUser):
        """Send quick start guide via Telegram"""
        logger.info(f"Sending quick start guide to {user.telegram_id}")
        # Implementation would send via Telegram bot
    
    def _enable_trading(self, user: OnboardingUser):
        """Enable trading features"""
        logger.info(f"Enabling trading for {user.email}")
    
    def _show_tutorial(self, user: OnboardingUser):
        """Show interactive tutorial"""
        logger.info(f"Showing tutorial to {user.telegram_id}")
    
    def _track_first_trade(self, user: OnboardingUser):
        """Track user's first trade"""
        logger.info(f"Tracking first trade for {user.email}")
    
    def _award_xp(self, user: OnboardingUser):
        """Award XP for completing actions"""
        logger.info(f"Awarding XP to {user.email}")
    
    def _show_results(self, user: OnboardingUser):
        """Show trading results"""
        logger.info(f"Showing results to {user.telegram_id}")
    
    def _encourage_profile_completion(self, user: OnboardingUser):
        """Encourage profile completion"""
        logger.info(f"Encouraging profile completion for {user.email}")
    
    def _show_tier_benefits(self, user: OnboardingUser):
        """Show tier benefits comparison"""
        logger.info(f"Showing tier benefits to {user.telegram_id}")
    
    def _create_payment_session(self, user: OnboardingUser):
        """Create Stripe payment session"""
        logger.info(f"Creating payment session for {user.email}")
    
    def _apply_press_pass_discount(self, user: OnboardingUser):
        """Apply Press Pass conversion discount"""
        logger.info(f"Applying Press Pass discount for {user.email}")
    
    def _upgrade_account(self, user: OnboardingUser):
        """Upgrade account to paid tier"""
        logger.info(f"Upgrading account for {user.email}")
    
    def _preserve_xp(self, user: OnboardingUser):
        """Preserve XP from Press Pass"""
        logger.info(f"Preserving XP for {user.email}")
    
    def _send_welcome_to_tier(self, user: OnboardingUser):
        """Send tier-specific welcome"""
        logger.info(f"Sending tier welcome to {user.email}")

# Singleton instance
onboarding_manager = OnboardingManager()