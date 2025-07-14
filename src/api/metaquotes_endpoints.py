"""
MetaQuotes Demo Account API Endpoints

REST API endpoints for demo account provisioning, credential retrieval,
and account management.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from ..bitten_core.onboarding.press_pass_manager_v2 import get_press_pass_manager
from ..bitten_core.metaquotes import (
    get_demo_account_service,
    get_pool_manager,
    DeliveryMethod
)
from ..bitten_core.metaquotes.credential_delivery import SecureCredentialDelivery

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/metaquotes", tags=["metaquotes"])

# Security
security = HTTPBearer()


# Request/Response Models
class ActivatePressPassRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    real_name: str = Field(..., description="User's real name")
    delivery_method: str = Field("telegram", description="Credential delivery method")
    contact_info: Optional[str] = Field(None, description="Contact info for delivery")


class ActivatePressPassResponse(BaseModel):
    success: bool
    account: Optional[Dict[str, Any]] = None
    delivery: Optional[Dict[str, Any]] = None
    message: str
    error: Optional[str] = None


class AccountHealthResponse(BaseModel):
    success: bool
    health_status: Optional[str] = None
    account_status: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class PoolStatusResponse(BaseModel):
    healthy_available: int
    total_available: int
    assigned: int
    expired: int
    error: int
    total: int
    pool_health: str
    provisions_last_hour: int


class ResendCredentialsRequest(BaseModel):
    user_id: str
    delivery_method: str
    contact_info: str


# Helper functions
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key for authentication"""
    # TODO: Implement proper API key verification
    api_key = credentials.credentials
    if not api_key or len(api_key) < 10:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


# Endpoints
@router.post("/press-pass/activate", response_model=ActivatePressPassResponse)
async def activate_press_pass(
    request: ActivatePressPassRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Activate Press Pass with MetaQuotes demo account
    
    Creates a real MetaQuotes demo account and delivers credentials
    via the specified method.
    """
    try:
        # Validate delivery method
        try:
            delivery_method = DeliveryMethod(request.delivery_method.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid delivery method: {request.delivery_method}"
            )
            
        # Get Press Pass manager
        manager = await get_press_pass_manager()
        
        # Activate Press Pass
        result = await manager.activate_press_pass(
            user_id=request.user_id,
            real_name=request.real_name,
            delivery_method=delivery_method,
            contact_info=request.contact_info
        )
        
        if not result['success']:
            if result.get('error') == 'weekly_limit_reached':
                raise HTTPException(status_code=429, detail=result['message'])
            elif result.get('error') == 'already_has_press_pass':
                raise HTTPException(status_code=409, detail=result['message'])
            else:
                raise HTTPException(status_code=400, detail=result['message'])
                
        return ActivatePressPassResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating Press Pass: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/account/{user_id}/health", response_model=AccountHealthResponse)
async def check_account_health(
    user_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Check health status of user's demo account"""
    try:
        manager = await get_press_pass_manager()
        result = await manager.check_account_health(user_id)
        
        if not result['success']:
            if result.get('error') == 'no_active_account':
                raise HTTPException(status_code=404, detail=result['message'])
                
        return AccountHealthResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking account health: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/account/{user_id}/credentials")
async def get_account_credentials(
    user_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get demo account credentials for a user
    
    Note: This endpoint should be used carefully as it returns
    sensitive credentials. In production, use secure delivery methods.
    """
    try:
        manager = await get_press_pass_manager()
        credentials = await manager.get_account_credentials(user_id)
        
        if not credentials:
            raise HTTPException(
                status_code=404,
                detail="No active demo account found"
            )
            
        # Remove password from response for security
        safe_credentials = {
            'account_number': credentials['account_number'],
            'server': credentials['server'],
            'balance': credentials['balance'],
            'leverage': credentials['leverage'],
            'expires_at': credentials['expires_at']
        }
        
        return {
            'success': True,
            'credentials': safe_credentials,
            'message': 'Use /resend-credentials to get password securely'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting credentials: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/account/resend-credentials")
async def resend_credentials(
    request: ResendCredentialsRequest,
    api_key: str = Depends(verify_api_key)
):
    """Resend account credentials via secure delivery method"""
    try:
        # Validate delivery method
        try:
            delivery_method = DeliveryMethod(request.delivery_method.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid delivery method: {request.delivery_method}"
            )
            
        manager = await get_press_pass_manager()
        result = await manager.resend_credentials(
            user_id=request.user_id,
            delivery_method=delivery_method,
            contact_info=request.contact_info
        )
        
        if not result['success']:
            if result.get('error') == 'no_active_account':
                raise HTTPException(status_code=404, detail=result['message'])
            else:
                raise HTTPException(status_code=400, detail=result.get('message', 'Failed to resend credentials'))
                
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending credentials: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/credentials/retrieve/{delivery_id}")
async def retrieve_credentials_by_link(
    delivery_id: str,
    token: str = Query(..., description="One-time token")
):
    """
    Retrieve credentials using secure link
    
    This endpoint is used when users click on secure credential links.
    The link can only be used once and expires after 30 minutes.
    """
    try:
        delivery_service = SecureCredentialDelivery()
        credentials = await delivery_service.retrieve_credentials(delivery_id, token)
        
        if not credentials:
            raise HTTPException(
                status_code=404,
                detail="Invalid or expired credential link"
            )
            
        return {
            'success': True,
            'credentials': credentials,
            'message': 'Save these credentials securely. This link has now expired.'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving credentials: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pool/status", response_model=PoolStatusResponse)
async def get_pool_status(api_key: str = Depends(verify_api_key)):
    """Get current demo account pool status"""
    try:
        pool_manager = await get_pool_manager()
        stats = await pool_manager.get_pool_statistics()
        return PoolStatusResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting pool status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/pool/replenish")
async def replenish_pool(
    count: int = Query(10, ge=1, le=50, description="Number of accounts to provision"),
    api_key: str = Depends(verify_api_key)
):
    """Force replenishment of the demo account pool"""
    try:
        pool_manager = await get_pool_manager()
        result = await pool_manager.force_replenish(count)
        
        if not result['success']:
            if result.get('error') == 'pool_at_capacity':
                raise HTTPException(status_code=409, detail=result['message'])
            else:
                raise HTTPException(status_code=400, detail=result.get('message', 'Replenishment failed'))
                
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error replenishing pool: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/statistics")
async def get_press_pass_statistics(api_key: str = Depends(verify_api_key)):
    """Get comprehensive Press Pass and demo account statistics"""
    try:
        manager = await get_press_pass_manager()
        stats = await manager.get_press_pass_statistics()
        
        # Add pool statistics
        pool_manager = await get_pool_manager()
        pool_stats = await pool_manager.get_pool_statistics()
        
        return {
            'success': True,
            'press_pass': stats,
            'account_pool': pool_stats,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Check if MetaQuotes services are healthy"""
    try:
        # Check demo service
        demo_service = await get_demo_account_service()
        
        # Check pool manager
        pool_manager = await get_pool_manager()
        pool_stats = await pool_manager.get_pool_statistics()
        
        return {
            'status': 'healthy',
            'services': {
                'demo_service': 'active',
                'pool_manager': 'active',
                'pool_health': pool_stats['pool_health']
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }