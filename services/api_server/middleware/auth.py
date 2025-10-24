"""
Firebase Authentication Middleware
Secures API endpoints with Firebase ID token verification
"""
import os
from typing import Optional
from fastapi import Header, HTTPException, Depends
from firebase_admin import credentials, auth, initialize_app
import firebase_admin
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK (if not already initialized)
def init_firebase_admin():
    """Initialize Firebase Admin SDK for backend authentication"""
    try:
        # Check if already initialized
        firebase_admin.get_app()
        logger.info("Firebase Admin SDK already initialized")
    except ValueError:
        # Not initialized, initialize now
        service_account_path = os.getenv(
            "FIREBASE_SERVICE_ACCOUNT",
            "/root/bitten-firebase-sa.json"
        )

        if not os.path.exists(service_account_path):
            logger.warning(f"Firebase service account not found at {service_account_path}")
            logger.warning("API authentication will be DISABLED - development mode only")
            return False

        cred = credentials.Certificate(service_account_path)
        initialize_app(cred)
        logger.info("✅ Firebase Admin SDK initialized successfully")
        return True

# Initialize on module load
FIREBASE_ENABLED = init_firebase_admin()


async def verify_firebase_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Verify Firebase ID token from Authorization header

    Returns:
        str: Firebase UID of authenticated user

    Raises:
        HTTPException: 401 if token missing/invalid, 403 if verification fails
    """
    # Development mode: Allow bypass if Firebase not initialized
    if not FIREBASE_ENABLED:
        logger.warning("⚠️ Firebase auth disabled - returning default UID for development")
        return "wlJ5lafBqRSLwHIUBxJQMr4SBtk1"  # Default commander for dev

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Provide: Authorization: Bearer <token>"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected: Bearer <token>"
        )

    token = authorization.replace("Bearer ", "").strip()

    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)
        user_uid = decoded_token["uid"]

        logger.info(f"✅ Authenticated user: {user_uid}")
        return user_uid

    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid Firebase ID token"
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Firebase ID token has expired"
        )
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=403,
            detail="Token verification failed"
        )


async def verify_user_access(
    user_id: str,
    current_user: str = Depends(verify_firebase_token)
) -> str:
    """
    Verify that authenticated user can only access their own data

    Args:
        user_id: User ID from URL path parameter
        current_user: Authenticated user's Firebase UID

    Returns:
        str: Verified user_id

    Raises:
        HTTPException: 403 if user tries to access another user's data
    """
    if current_user != user_id:
        logger.warning(f"🚫 Access denied: User {current_user} tried to access {user_id}'s data")
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You can only access your own data"
        )

    return user_id


async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Optional authentication - returns UID if authenticated, None otherwise
    Use for endpoints that are public but want to customize response for logged-in users

    Returns:
        Optional[str]: Firebase UID if authenticated, None if not
    """
    if not authorization or not FIREBASE_ENABLED:
        return None

    try:
        return await verify_firebase_token(authorization)
    except HTTPException:
        return None
