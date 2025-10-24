"""
Firebase Authentication Middleware for API Server
Verifies Firebase ID tokens to authenticate users
"""
from fastapi import HTTPException, Header
from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth
import os

# Initialize Firebase Admin SDK (singleton pattern)
_firebase_initialized = False

def init_firebase():
    """Initialize Firebase Admin SDK once"""
    global _firebase_initialized
    if not _firebase_initialized:
        # Path to service account key
        cred_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT', '/root/bitten-firebase-sa.json')

        if not os.path.exists(cred_path):
            print(f"⚠️  Firebase service account key not found at {cred_path}")
            print("⚠️  Firebase auth will be disabled - INSECURE MODE")
            return False

        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(f"✅ Firebase Admin SDK initialized with {cred_path}")
            _firebase_initialized = True
            return True
        except Exception as e:
            # App already exists - this is fine, just reuse it
            if "already exists" in str(e):
                print(f"✅ Firebase Admin SDK already initialized (reusing existing app)")
                _firebase_initialized = True
                return True
            else:
                print(f"❌ Firebase initialization error: {e}")
                return False
    return True


async def verify_firebase_token(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> dict:
    """
    Verify Firebase ID token from Authorization header

    Args:
        authorization: "Bearer <firebase_id_token>" from header
        x_user_id: Optional X-User-ID header (for backwards compatibility)

    Returns:
        dict: Decoded token with user info (uid, email, etc.)

    Raises:
        HTTPException: If token is invalid or missing
    """

    # Check if Firebase is initialized
    if not _firebase_initialized:
        if not init_firebase():
            # Fallback to insecure mode (development only)
            if x_user_id:
                print(f"⚠️  INSECURE MODE: Trusting X-User-ID header: {x_user_id}")
                return {"uid": x_user_id, "insecure": True}
            raise HTTPException(
                status_code=401,
                detail="Firebase authentication not configured"
            )

    # Extract token from Authorization header
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Expected: Authorization: Bearer <token>"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected: Bearer <token>"
        )

    token = authorization.replace("Bearer ", "")

    # Verify token with Firebase
    try:
        decoded_token = auth.verify_id_token(token)

        # Token is valid - return user info
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "email_verified": decoded_token.get("email_verified", False),
            "auth_time": decoded_token.get("auth_time"),
            "insecure": False
        }

    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid Firebase ID token"
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Firebase ID token expired. Please sign in again."
        )
    except Exception as e:
        print(f"❌ Firebase token verification error: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication error: {str(e)}"
        )


async def get_current_user_id(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> str:
    """
    Extract and verify user ID from Firebase token

    Convenience function that just returns the user ID string
    """
    token_data = await verify_firebase_token(authorization, x_user_id)
    return token_data["uid"]
