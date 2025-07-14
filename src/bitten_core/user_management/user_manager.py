"""
BITTEN User Management System

Handles user registration, authentication, session management, and tier transitions.
Connects onboarding flow to actual database operations.
"""

import logging
import secrets
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from sqlalchemy import select, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.models import (
    User, UserProfile, UserSubscription, SubscriptionPlan,
    TierLevel, SubscriptionStatus
)
from ...database.connection import get_async_db
from ..onboarding.press_pass_manager import PressPassManager

logger = logging.getLogger(__name__)


class UserManager:
    """Comprehensive user management system for BITTEN"""
    
    def __init__(self):
        self.press_pass_manager = PressPassManager()
        self.session_cache = {}  # In-memory session cache
        self.session_ttl = timedelta(hours=24)  # Session timeout
        
    async def create_user_from_onboarding(
        self, 
        onboarding_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a full user account from completed onboarding session
        
        Args:
            onboarding_session: Completed onboarding session data
            
        Returns:
            User creation result with user_id and status
        """
        try:
            async with get_async_db() as conn:
                async with conn.transaction():
                    # Extract user data from onboarding session
                    telegram_id = onboarding_session.get('telegram_id')
                    first_name = onboarding_session.get('first_name', '')
                    email = onboarding_session.get('email')
                    phone = onboarding_session.get('phone')
                    callsign = onboarding_session.get('callsign')
                    is_press_pass = onboarding_session.get('is_press_pass', False)
                    selected_theater = onboarding_session.get('selected_theater', 'DEMO')
                    
                    # Determine initial tier
                    initial_tier = TierLevel.PRESS_PASS.value if is_press_pass else TierLevel.NIBBLER.value
                    
                    # Check if user already exists
                    existing_user = await conn.fetchrow(
                        "SELECT user_id FROM users WHERE telegram_id = $1",
                        telegram_id
                    )
                    
                    if existing_user:
                        return {
                            'success': False,
                            'error': 'user_exists',
                            'message': 'User already registered',
                            'user_id': existing_user['user_id']
                        }
                    
                    # Create user record
                    user_result = await conn.fetchrow(
                        """
                        INSERT INTO users (
                            telegram_id, username, first_name, last_name,
                            email, phone, tier, subscription_status,
                            api_key, created_at, is_active
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                        ) RETURNING user_id
                        """,
                        telegram_id,
                        onboarding_session.get('username'),
                        first_name,
                        onboarding_session.get('last_name', ''),
                        email,
                        phone,
                        initial_tier,
                        SubscriptionStatus.TRIAL.value if is_press_pass else SubscriptionStatus.INACTIVE.value,
                        self._generate_api_key(),
                        datetime.utcnow(),
                        True
                    )
                    
                    user_id = user_result['user_id']
                    
                    # Create user profile
                    await conn.execute(
                        """
                        INSERT INTO user_profiles (
                            user_id, callsign, total_xp, current_rank,
                            notification_settings, trading_preferences,
                            profile_completed, onboarding_completed,
                            referral_code, created_at
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                        )
                        """,
                        user_id,
                        callsign,
                        0,  # Starting XP
                        'RECRUIT',  # Starting rank
                        self._default_notification_settings(),
                        self._default_trading_preferences(selected_theater),
                        True,
                        True,
                        self._generate_referral_code(),
                        datetime.utcnow()
                    )
                    
                    # Handle Press Pass activation
                    if is_press_pass:
                        press_pass_result = await self._activate_press_pass(
                            user_id, 
                            telegram_id,
                            first_name,
                            onboarding_session
                        )
                        
                        if not press_pass_result['success']:
                            # Rollback will happen automatically
                            raise Exception(f"Press Pass activation failed: {press_pass_result['error']}")
                    
                    # Create initial subscription record
                    await self._create_initial_subscription(
                        user_id,
                        initial_tier,
                        is_press_pass
                    )
                    
                    # Create authentication session
                    session_token = await self._create_user_session(
                        user_id,
                        telegram_id,
                        {'tier': initial_tier, 'is_press_pass': is_press_pass}
                    )
                    
                    logger.info(f"Created new user {user_id} with tier {initial_tier}")
                    
                    return {
                        'success': True,
                        'user_id': user_id,
                        'tier': initial_tier,
                        'session_token': session_token,
                        'is_press_pass': is_press_pass,
                        'message': 'User account created successfully'
                    }
                    
        except IntegrityError as e:
            logger.error(f"Database integrity error creating user: {e}")
            return {
                'success': False,
                'error': 'database_error',
                'message': 'User creation failed due to data conflict'
            }
        except Exception as e:
            logger.error(f"Error creating user from onboarding: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create user account'
            }
    
    async def authenticate_user(
        self, 
        telegram_id: int,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate user and create session
        
        Args:
            telegram_id: Telegram user ID
            api_key: Optional API key for verification
            
        Returns:
            Authentication result with session token
        """
        try:
            async with get_async_db() as conn:
                # Get user data
                user = await conn.fetchrow(
                    """
                    SELECT u.user_id, u.tier, u.subscription_status,
                           u.is_active, u.is_banned, u.api_key,
                           up.callsign, up.total_xp, up.current_rank
                    FROM users u
                    JOIN user_profiles up ON u.user_id = up.user_id
                    WHERE u.telegram_id = $1
                    """,
                    telegram_id
                )
                
                if not user:
                    return {
                        'authenticated': False,
                        'error': 'user_not_found',
                        'message': 'User not registered'
                    }
                
                # Check if user is banned
                if user['is_banned']:
                    return {
                        'authenticated': False,
                        'error': 'user_banned',
                        'message': 'Account has been suspended'
                    }
                
                # Verify API key if provided
                if api_key and user['api_key'] != api_key:
                    return {
                        'authenticated': False,
                        'error': 'invalid_api_key',
                        'message': 'Invalid API key'
                    }
                
                # Update last login
                await conn.execute(
                    """
                    UPDATE users 
                    SET last_login_at = $1 
                    WHERE user_id = $2
                    """,
                    datetime.utcnow(),
                    user['user_id']
                )
                
                # Create session
                session_data = {
                    'tier': user['tier'],
                    'subscription_status': user['subscription_status'],
                    'callsign': user['callsign'],
                    'total_xp': user['total_xp'],
                    'rank': user['current_rank']
                }
                
                session_token = await self._create_user_session(
                    user['user_id'],
                    telegram_id,
                    session_data
                )
                
                # Check Press Pass expiry if applicable
                press_pass_status = None
                if user['tier'] == TierLevel.PRESS_PASS.value:
                    press_pass_status = await self._check_press_pass_status(user['user_id'])
                
                return {
                    'authenticated': True,
                    'user_id': user['user_id'],
                    'session_token': session_token,
                    'user_data': session_data,
                    'press_pass_status': press_pass_status,
                    'message': 'Authentication successful'
                }
                
        except Exception as e:
            logger.error(f"Error authenticating user {telegram_id}: {e}")
            return {
                'authenticated': False,
                'error': str(e),
                'message': 'Authentication failed'
            }
    
    async def upgrade_user_tier(
        self,
        user_id: int,
        new_tier: str,
        payment_method: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upgrade user from Press Pass or lower tier to paid tier
        
        Args:
            user_id: User database ID
            new_tier: Target tier (NIBBLER, FANG, COMMANDER, APEX)
            payment_method: Payment method used
            
        Returns:
            Upgrade result
        """
        try:
            # Validate tier
            if new_tier not in [t.value for t in TierLevel]:
                return {
                    'success': False,
                    'error': 'invalid_tier',
                    'message': f'Invalid tier: {new_tier}'
                }
            
            async with get_async_db() as conn:
                async with conn.transaction():
                    # Get current user tier
                    current_user = await conn.fetchrow(
                        """
                        SELECT tier, subscription_status, telegram_id
                        FROM users 
                        WHERE user_id = $1
                        """,
                        user_id
                    )
                    
                    if not current_user:
                        return {
                            'success': False,
                            'error': 'user_not_found',
                            'message': 'User not found'
                        }
                    
                    current_tier = current_user['tier']
                    
                    # Handle Press Pass upgrade
                    if current_tier == TierLevel.PRESS_PASS.value:
                        press_pass_result = await self.press_pass_manager.upgrade_to_paid_tier(
                            str(user_id),
                            new_tier
                        )
                        
                        if not press_pass_result['success']:
                            return press_pass_result
                    
                    # Update user tier
                    await conn.execute(
                        """
                        UPDATE users 
                        SET tier = $1,
                            subscription_status = $2,
                            payment_method = $3,
                            updated_at = $4
                        WHERE user_id = $5
                        """,
                        new_tier,
                        SubscriptionStatus.ACTIVE.value,
                        payment_method,
                        datetime.utcnow(),
                        user_id
                    )
                    
                    # Create new subscription record
                    plan = await self._get_subscription_plan(new_tier)
                    if plan:
                        await conn.execute(
                            """
                            INSERT INTO user_subscriptions (
                                user_id, plan_id, status, started_at,
                                expires_at, payment_method, created_at
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7
                            )
                            """,
                            user_id,
                            plan['plan_id'],
                            'active',
                            datetime.utcnow(),
                            datetime.utcnow() + timedelta(days=30),
                            payment_method,
                            datetime.utcnow()
                        )
                    
                    # Log the upgrade event
                    await self._log_tier_upgrade(user_id, current_tier, new_tier)
                    
                    logger.info(f"Upgraded user {user_id} from {current_tier} to {new_tier}")
                    
                    return {
                        'success': True,
                        'previous_tier': current_tier,
                        'new_tier': new_tier,
                        'message': f'Successfully upgraded to {new_tier}'
                    }
                    
        except Exception as e:
            logger.error(f"Error upgrading user {user_id} tier: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Tier upgrade failed'
            }
    
    async def update_user_profile(
        self,
        user_id: int,
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user profile information
        
        Args:
            user_id: User database ID
            profile_data: Profile fields to update
            
        Returns:
            Update result
        """
        try:
            async with get_async_db() as conn:
                # Build update query dynamically
                allowed_fields = [
                    'callsign', 'bio', 'timezone', 'notification_settings',
                    'trading_preferences', 'ui_theme', 'language_code'
                ]
                
                update_fields = []
                values = []
                param_count = 1
                
                for field, value in profile_data.items():
                    if field in allowed_fields:
                        update_fields.append(f"{field} = ${param_count}")
                        values.append(value)
                        param_count += 1
                
                if not update_fields:
                    return {
                        'success': False,
                        'error': 'no_valid_fields',
                        'message': 'No valid fields to update'
                    }
                
                # Add updated_at
                update_fields.append(f"updated_at = ${param_count}")
                values.append(datetime.utcnow())
                param_count += 1
                
                # Add user_id as last parameter
                values.append(user_id)
                
                query = f"""
                    UPDATE user_profiles 
                    SET {', '.join(update_fields)}
                    WHERE user_id = ${param_count}
                """
                
                await conn.execute(query, *values)
                
                logger.info(f"Updated profile for user {user_id}")
                
                return {
                    'success': True,
                    'updated_fields': list(profile_data.keys()),
                    'message': 'Profile updated successfully'
                }
                
        except Exception as e:
            logger.error(f"Error updating user {user_id} profile: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Profile update failed'
            }
    
    async def get_user_session(
        self,
        session_token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user session by token
        
        Args:
            session_token: Session token
            
        Returns:
            Session data if valid, None otherwise
        """
        try:
            # Check in-memory cache first
            if session_token in self.session_cache:
                session = self.session_cache[session_token]
                
                # Check if expired
                if datetime.utcnow() < session['expires_at']:
                    return session
                else:
                    # Remove expired session
                    del self.session_cache[session_token]
            
            # TODO: In production, check Redis or database for distributed sessions
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    async def invalidate_session(
        self,
        session_token: str
    ) -> bool:
        """
        Invalidate user session (logout)
        
        Args:
            session_token: Session token to invalidate
            
        Returns:
            True if invalidated successfully
        """
        try:
            if session_token in self.session_cache:
                del self.session_cache[session_token]
                return True
            
            # TODO: In production, remove from Redis or database
            
            return False
            
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
            return False
    
    # Private helper methods
    
    def _generate_api_key(self) -> str:
        """Generate secure API key"""
        return f"bk_{secrets.token_urlsafe(32)}"
    
    def _generate_referral_code(self) -> str:
        """Generate unique referral code"""
        return f"BITTEN_{secrets.token_hex(4).upper()}"
    
    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(48)
    
    def _default_notification_settings(self) -> Dict[str, Any]:
        """Get default notification settings"""
        return {
            'trades': True,
            'signals': True,
            'news': True,
            'achievements': True,
            'daily_summary': True,
            'promotional': False
        }
    
    def _default_trading_preferences(self, theater: str) -> Dict[str, Any]:
        """Get default trading preferences based on theater"""
        return {
            'theater': theater,
            'risk_mode': 'default',
            'auto_trading': False,
            'max_daily_trades': 5,
            'preferred_pairs': ['EURUSD', 'GBPUSD', 'USDJPY'],
            'trading_hours': 'all'
        }
    
    async def _activate_press_pass(
        self,
        user_id: int,
        telegram_id: int,
        first_name: str,
        onboarding_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Activate Press Pass for user"""
        try:
            # Update onboarding session with expiry
            press_pass_expiry = datetime.utcnow() + timedelta(days=7)
            
            # Provision demo account
            demo_result = await self.press_pass_manager.provision_demo_account(
                str(user_id),
                first_name
            )
            
            if not demo_result['success']:
                return demo_result
            
            # Store Press Pass activation in database
            async with get_async_db() as conn:
                await conn.execute(
                    """
                    UPDATE users
                    SET subscription_expires_at = $1,
                        mt5_account_id = $2,
                        mt5_broker_server = $3
                    WHERE user_id = $4
                    """,
                    press_pass_expiry,
                    demo_result['account']['account_number'],
                    demo_result['account']['server'],
                    user_id
                )
            
            return {
                'success': True,
                'demo_account': demo_result['account'],
                'expires_at': press_pass_expiry
            }
            
        except Exception as e:
            logger.error(f"Error activating Press Pass: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _create_initial_subscription(
        self,
        user_id: int,
        tier: str,
        is_press_pass: bool
    ) -> None:
        """Create initial subscription record"""
        try:
            async with get_async_db() as conn:
                # Get plan for tier
                plan = await self._get_subscription_plan(tier)
                if not plan:
                    return
                
                # Create subscription
                await conn.execute(
                    """
                    INSERT INTO user_subscriptions (
                        user_id, plan_id, status, started_at,
                        expires_at, created_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6
                    )
                    """,
                    user_id,
                    plan['plan_id'],
                    'trial' if is_press_pass else 'pending',
                    datetime.utcnow(),
                    datetime.utcnow() + timedelta(days=7) if is_press_pass else None,
                    datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Error creating initial subscription: {e}")
    
    async def _get_subscription_plan(self, tier: str) -> Optional[Dict[str, Any]]:
        """Get subscription plan for tier"""
        try:
            async with get_async_db() as conn:
                plan = await conn.fetchrow(
                    """
                    SELECT plan_id, tier, price_usd, features, limits
                    FROM subscription_plans
                    WHERE tier = $1 AND is_active = true
                    """,
                    tier
                )
                
                return dict(plan) if plan else None
                
        except Exception as e:
            logger.error(f"Error getting subscription plan: {e}")
            return None
    
    async def _create_user_session(
        self,
        user_id: int,
        telegram_id: int,
        session_data: Dict[str, Any]
    ) -> str:
        """Create user session and return token"""
        try:
            session_token = self._generate_session_token()
            
            session = {
                'user_id': user_id,
                'telegram_id': telegram_id,
                'token': session_token,
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + self.session_ttl,
                'data': session_data
            }
            
            # Store in cache
            self.session_cache[session_token] = session
            
            # TODO: In production, store in Redis or database
            
            return session_token
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    async def _check_press_pass_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Check Press Pass status for user"""
        try:
            async with get_async_db() as conn:
                user = await conn.fetchrow(
                    """
                    SELECT subscription_expires_at
                    FROM users
                    WHERE user_id = $1 AND tier = $2
                    """,
                    user_id,
                    TierLevel.PRESS_PASS.value
                )
                
                if user and user['subscription_expires_at']:
                    return await self.press_pass_manager.check_press_pass_expiry(
                        str(user_id),
                        user['subscription_expires_at']
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Error checking Press Pass status: {e}")
            return None
    
    async def _log_tier_upgrade(
        self,
        user_id: int,
        old_tier: str,
        new_tier: str
    ) -> None:
        """Log tier upgrade event"""
        try:
            async with get_async_db() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_log (
                        user_id, action, entity_type, entity_id,
                        old_values, new_values, created_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7
                    )
                    """,
                    user_id,
                    'tier_upgrade',
                    'user',
                    user_id,
                    {'tier': old_tier},
                    {'tier': new_tier},
                    datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Error logging tier upgrade: {e}")


# Singleton instance
user_manager = UserManager()