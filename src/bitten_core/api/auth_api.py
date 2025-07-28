"""
BITTEN Authentication API

RESTful API endpoints for user authentication and session management.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr

from ..user_management.user_manager import user_manager
from ..user_management.auth_middleware import SessionManager, AuthenticationError

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Request/Response models
class LoginRequest(BaseModel):
    telegram_id: int
    api_key: Optional[str] = None

class LoginResponse(BaseModel):
    success: bool
    session_token: Optional[str] = None
    user_data: Optional[Dict[str, Any]] = None
    message: str

class SessionValidateRequest(BaseModel):
    session_token: str

class SessionResponse(BaseModel):
    valid: bool
    user_id: Optional[int] = None
    tier: Optional[str] = None
    expires_at: Optional[datetime] = None

class TierUpgradeRequest(BaseModel):
    session_token: str
    new_tier: str
    payment_method: Optional[str] = None

class ProfileUpdateRequest(BaseModel):
    session_token: str
    updates: Dict[str, Any]

async def get_current_user(authorization: str = Header(...)):
    """Dependency to get current user from auth header"""
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization[7:]
    
    try:
        session = await SessionManager.validate_session(token)
        return session
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and create session
    """
    try:
        result = await user_manager.authenticate_user(
            telegram_id=request.telegram_id,
            api_key=request.api_key
        )
        
        if result['authenticated']:
            return LoginResponse(
                success=True,
                session_token=result['session_token'],
                user_data=result['user_data'],
                message="Authentication successful"
            )
        else:
            return LoginResponse(
                success=False,
                message=result.get('message', 'Authentication failed')
            )
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/logout")
async def logout(session: Dict = Depends(get_current_user)):
    """
    Invalidate user session
    """
    try:
        token = session['token']
        success = await user_manager.invalidate_session(token)
        
        return {
            'success': success,
            'message': 'Logged out successfully' if success else 'Logout failed'
        }
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/session/validate", response_model=SessionResponse)
async def validate_session(session: Dict = Depends(get_current_user)):
    """
    Validate session token
    """
    return SessionResponse(
        valid=True,
        user_id=session['user_id'],
        tier=session['data'].get('tier'),
        expires_at=session['expires_at']
    )

@router.post("/session/refresh")
async def refresh_session(session: Dict = Depends(get_current_user)):
    """
    Refresh session token
    """
    try:
        old_token = session['token']
        new_token = await SessionManager.refresh_session(old_token)
        
        return {
            'success': True,
            'session_token': new_token,
            'message': 'Session refreshed successfully'
        }
        
    except Exception as e:
        logger.error(f"Session refresh error: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh session")

@router.get("/user/profile")
async def get_user_profile(session: Dict = Depends(get_current_user)):
    """
    Get current user profile
    """
    try:
        context = await SessionManager.get_user_context(session['token'])
        
        return {
            'success': True,
            'profile': context['user'],
            'tier': context['tier'],
            'is_press_pass': context['is_press_pass']
        }
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")

@router.post("/user/upgrade-tier")
async def upgrade_tier(request: TierUpgradeRequest, session: Dict = Depends(get_current_user)):
    """
    Upgrade user tier
    """
    try:
        result = await user_manager.upgrade_user_tier(
            user_id=session['user_id'],
            new_tier=request.new_tier,
            payment_method=request.payment_method
        )
        
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=400, detail=result['message'])
            
    except Exception as e:
        logger.error(f"Tier upgrade error: {e}")
        raise HTTPException(status_code=500, detail="Tier upgrade failed")

@router.put("/user/profile")
async def update_profile(request: ProfileUpdateRequest, session: Dict = Depends(get_current_user)):
    """
    Update user profile
    """
    try:
        result = await user_manager.update_user_profile(
            user_id=session['user_id'],
            profile_data=request.updates
        )
        
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=400, detail=result['message'])
            
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail="Profile update failed")

@router.get("/tiers/features/{tier}")
async def get_tier_features(tier: str):
    """
    Get features available for a specific tier
    """
    from ..user_management.auth_middleware import TierGuard
    
    valid_tiers = ['PRESS_PASS', 'NIBBLER', 'FANG', 'COMMANDER', '']
    
    if tier not in valid_tiers:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    features = {
        'basic_signals': TierGuard.check_feature_access(tier, 'basic_signals'),
        'market_news': TierGuard.check_feature_access(tier, 'market_news'),
        'advanced_signals': TierGuard.check_feature_access(tier, 'advanced_signals'),
        'custom_strategies': TierGuard.check_feature_access(tier, 'custom_strategies'),
        'api_access': TierGuard.check_feature_access(tier, 'api_access'),
        'vip_support': TierGuard.check_feature_access(tier, 'vip_support'),
        'white_label': TierGuard.check_feature_access(tier, 'white_label'),
        'unlimited_trades': TierGuard.check_feature_access(tier, 'unlimited_trades')
    }
    
    limits = TierGuard.get_tier_limits(tier)
    
    return {
        'tier': tier,
        'features': features,
        'limits': limits
    }

@router.get("/press-pass/status")
async def get_press_pass_status(session: Dict = Depends(get_current_user)):
    """
    Get Press Pass status for current user
    """
    try:
        if session['data'].get('tier') != 'PRESS_PASS':
            return {
                'is_press_pass': False,
                'message': 'User is not on Press Pass tier'
            }
        
        # Get expiry info from database
        from ...database.connection import get_async_db
        
        async with get_async_db() as conn:
            user_data = await conn.fetchrow(
                """
                SELECT subscription_expires_at
                FROM users
                WHERE user_id = $1
                """,
                session['user_id']
            )
            
            if user_data and user_data['subscription_expires_at']:
                from ..onboarding.press_pass_manager import PressPassManager
                pm = PressPassManager()
                
                status = await pm.check_press_pass_expiry(
                    str(session['user_id']),
                    user_data['subscription_expires_at']
                )
                
                return {
                    'is_press_pass': True,
                    'expired': status['expired'],
                    'expires_at': user_data['subscription_expires_at'],
                    'remaining_time': status.get('remaining_time'),
                    'message': status['message']
                }
        
        return {
            'is_press_pass': True,
            'error': 'Could not retrieve Press Pass status'
        }
        
    except Exception as e:
        logger.error(f"Press Pass status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Press Pass status")

# Export router
__all__ = ['router']