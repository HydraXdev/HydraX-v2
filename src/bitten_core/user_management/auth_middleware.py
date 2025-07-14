"""
BITTEN Authentication Middleware

Provides authentication and session validation for all system components.
"""

import logging
from functools import wraps
from typing import Callable, Any, Optional, Dict
from datetime import datetime

from .user_manager import user_manager

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Authentication error exception"""
    pass


class AuthorizationError(Exception):
    """Authorization error exception"""
    pass


def require_auth(min_tier: Optional[str] = None):
    """
    Decorator to require authentication for a function
    
    Args:
        min_tier: Minimum tier required (None means any authenticated user)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract session token from various sources
            session_token = None
            
            # Check kwargs for session_token
            if 'session_token' in kwargs:
                session_token = kwargs['session_token']
            # Check first arg if it's a request object
            elif args and hasattr(args[0], 'session_token'):
                session_token = args[0].session_token
            # Check for auth header in request
            elif args and hasattr(args[0], 'headers'):
                auth_header = args[0].headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    session_token = auth_header[7:]
            
            if not session_token:
                raise AuthenticationError("No session token provided")
            
            # Validate session
            session = await user_manager.get_user_session(session_token)
            if not session:
                raise AuthenticationError("Invalid or expired session")
            
            # Check tier requirement
            if min_tier:
                tier_hierarchy = {
                    'PRESS_PASS': 0,
                    'NIBBLER': 1,
                    'FANG': 2,
                    'COMMANDER': 3,
                    'APEX': 4
                }
                
                user_tier = session['data'].get('tier', 'NIBBLER')
                user_tier_level = tier_hierarchy.get(user_tier, 1)
                required_tier_level = tier_hierarchy.get(min_tier, 1)
                
                if user_tier_level < required_tier_level:
                    raise AuthorizationError(f"Tier {min_tier} or higher required")
            
            # Add session to kwargs for the function
            kwargs['auth_session'] = session
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_telegram_auth(func: Callable) -> Callable:
    """
    Decorator to require Telegram authentication
    Used for Telegram bot commands
    """
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        try:
            # Extract Telegram user info
            if update.effective_user:
                telegram_id = update.effective_user.id
                
                # Authenticate user
                auth_result = await user_manager.authenticate_user(telegram_id)
                
                if not auth_result['authenticated']:
                    # User not registered, might need onboarding
                    await update.message.reply_text(
                        "🚨 **Authentication Required**\n\n"
                        "You need to complete onboarding first.\n"
                        "Use /start to begin your BITTEN journey!"
                    )
                    return
                
                # Add auth info to context
                context.user_data['auth'] = auth_result
                context.user_data['user_id'] = auth_result['user_id']
                context.user_data['session_token'] = auth_result['session_token']
                
                # Check Press Pass expiry
                if auth_result.get('press_pass_status'):
                    status = auth_result['press_pass_status']
                    if status['expired']:
                        await update.message.reply_text(
                            "⏰ **Press Pass Expired**\n\n"
                            "Your 7-day trial has ended.\n"
                            "Upgrade to continue using BITTEN!\n\n"
                            "Use /upgrade to see available plans."
                        )
                        return
                
                return await func(update, context, *args, **kwargs)
            else:
                await update.message.reply_text("Authentication failed. Please try again.")
                
        except Exception as e:
            logger.error(f"Telegram auth error: {e}")
            await update.message.reply_text("Authentication error. Please try again later.")
    
    return wrapper


class SessionManager:
    """
    Session management utilities
    """
    
    @staticmethod
    async def validate_session(session_token: str) -> Dict[str, Any]:
        """
        Validate a session token
        
        Args:
            session_token: Session token to validate
            
        Returns:
            Session data if valid
            
        Raises:
            AuthenticationError: If session is invalid
        """
        session = await user_manager.get_user_session(session_token)
        if not session:
            raise AuthenticationError("Invalid or expired session")
        
        return session
    
    @staticmethod
    async def refresh_session(session_token: str) -> str:
        """
        Refresh a session token
        
        Args:
            session_token: Current session token
            
        Returns:
            New session token
            
        Raises:
            AuthenticationError: If session cannot be refreshed
        """
        session = await user_manager.get_user_session(session_token)
        if not session:
            raise AuthenticationError("Invalid session")
        
        # Create new session with same data
        new_token = await user_manager._create_user_session(
            session['user_id'],
            session['telegram_id'],
            session['data']
        )
        
        # Invalidate old session
        await user_manager.invalidate_session(session_token)
        
        return new_token
    
    @staticmethod
    async def get_user_context(session_token: str) -> Dict[str, Any]:
        """
        Get full user context from session
        
        Args:
            session_token: Session token
            
        Returns:
            User context including profile data
        """
        session = await SessionManager.validate_session(session_token)
        
        # Get additional user data from database
        from ...database.connection import get_async_db
        
        async with get_async_db() as conn:
            user_data = await conn.fetchrow(
                """
                SELECT u.*, up.*
                FROM users u
                JOIN user_profiles up ON u.user_id = up.user_id
                WHERE u.user_id = $1
                """,
                session['user_id']
            )
            
            if user_data:
                return {
                    'session': session,
                    'user': dict(user_data),
                    'tier': session['data']['tier'],
                    'is_press_pass': session['data']['tier'] == 'PRESS_PASS'
                }
        
        return {'session': session}


class TierGuard:
    """
    Tier-based access control utilities
    """
    
    @staticmethod
    def check_feature_access(user_tier: str, feature: str) -> bool:
        """
        Check if a tier has access to a feature
        
        Args:
            user_tier: User's current tier
            feature: Feature to check
            
        Returns:
            True if user has access
        """
        feature_requirements = {
            # Basic features
            'basic_signals': ['PRESS_PASS', 'NIBBLER', 'FANG', 'COMMANDER', 'APEX'],
            'market_news': ['PRESS_PASS', 'NIBBLER', 'FANG', 'COMMANDER', 'APEX'],
            
            # Advanced features
            'advanced_signals': ['FANG', 'COMMANDER', 'APEX'],
            'custom_strategies': ['COMMANDER', 'APEX'],
            'api_access': ['COMMANDER', 'APEX'],
            
            # Premium features
            'vip_support': ['APEX'],
            'white_label': ['APEX'],
            'unlimited_trades': ['APEX']
        }
        
        allowed_tiers = feature_requirements.get(feature, [])
        return user_tier in allowed_tiers
    
    @staticmethod
    def get_tier_limits(tier: str) -> Dict[str, Any]:
        """
        Get limits for a specific tier
        
        Args:
            tier: Tier name
            
        Returns:
            Dictionary of limits
        """
        tier_limits = {
            'PRESS_PASS': {
                'daily_trades': 10,
                'max_lot_size': 0.10,
                'signal_delay_minutes': 0,
                'xp_multiplier': 1.0,
                'demo_only': True,
                'expires_days': 7
            },
            'NIBBLER': {
                'daily_trades': 20,
                'max_lot_size': 0.50,
                'signal_delay_minutes': 5,
                'xp_multiplier': 1.0,
                'demo_only': False
            },
            'FANG': {
                'daily_trades': 50,
                'max_lot_size': 2.0,
                'signal_delay_minutes': 2,
                'xp_multiplier': 1.5,
                'demo_only': False
            },
            'COMMANDER': {
                'daily_trades': 100,
                'max_lot_size': 5.0,
                'signal_delay_minutes': 0,
                'xp_multiplier': 2.0,
                'demo_only': False
            },
            'APEX': {
                'daily_trades': -1,  # Unlimited
                'max_lot_size': -1,  # Unlimited
                'signal_delay_minutes': 0,
                'xp_multiplier': 3.0,
                'demo_only': False
            }
        }
        
        return tier_limits.get(tier, tier_limits['NIBBLER'])


# Export middleware components
__all__ = [
    'require_auth',
    'require_telegram_auth',
    'SessionManager',
    'TierGuard',
    'AuthenticationError',
    'AuthorizationError'
]