#!/usr/bin/env python3
"""
JWT Token Manager for Mission Session Architecture
Handles token generation, validation, and key rotation
"""

import logging
import os
import secrets
import time
from pathlib import Path
from typing import Dict, List, Optional

import jwt

logger = logging.getLogger(__name__)


class JWTManager:
    """Manages JWT token generation and validation for mission sessions"""

    def __init__(self):
        # Load configuration from environment
        self.private_key_path = os.getenv("JWT_PRIVATE_KEY_PATH", "/root/HydraX-v2/keys/jwt_private.pem")
        self.public_key_path = os.getenv("JWT_PUBLIC_KEY_PATH", "/root/HydraX-v2/keys/jwt_public.pem")
        self.key_id = os.getenv("JWT_KEY_ID", "key-2025-10")
        self.algorithm = os.getenv("JWT_ALGORITHM", "RS256")
        self.issuer = os.getenv("JWT_ISSUER", "bitten-backend")
        self.audience = os.getenv("JWT_AUDIENCE", "bitten-ui")

        # Load keys
        self._load_keys()

    def _load_keys(self):
        """Load RSA keys for signing and verification"""
        try:
            # Load private key for signing
            if os.path.exists(self.private_key_path):
                with open(self.private_key_path, "r") as f:
                    self.private_key = f.read()
                logger.info(f"✅ Loaded JWT private key from {self.private_key_path}")
            else:
                logger.warning(f"⚠️ Private key not found at {self.private_key_path}")
                self.private_key = None

            # Load public key for verification
            if os.path.exists(self.public_key_path):
                with open(self.public_key_path, "r") as f:
                    self.public_key = f.read()
                logger.info(f"✅ Loaded JWT public key from {self.public_key_path}")
            else:
                logger.warning(f"⚠️ Public key not found at {self.public_key_path}")
                self.public_key = None

        except Exception as e:
            logger.error(f"❌ Error loading JWT keys: {e}")
            self.private_key = None
            self.public_key = None

    def generate_mission_token(
        self,
        user_id: str,
        mission_session_id: str,
        alert_id: int,
        scopes: List[str],
        pair: Optional[str] = None,
        timeframe: Optional[str] = None,
        risk_max_usd: Optional[float] = None,
        ttl_seconds: int = 28800,  # 8 hours default (8 * 3600)
    ) -> str:
        """
        Generate a signed JWT token for a mission session

        Args:
            user_id: User identifier
            mission_session_id: Mission session ID (ms_xxx)
            alert_id: Alert/signal ID
            scopes: List of scopes (e.g., ["mission:view", "order:execute"])
            pair: Trading pair (optional hint)
            timeframe: Timeframe (optional hint)
            risk_max_usd: Maximum risk in USD (optional fuse)
            ttl_seconds: Token lifetime in seconds

        Returns:
            Signed JWT token string
        """
        if not self.private_key:
            raise ValueError("Private key not loaded - cannot generate tokens")

        now = int(time.time())
        nonce = secrets.token_urlsafe(32)  # Cryptographically secure nonce

        # Build claims
        claims = {
            # Standard claims
            "iss": self.issuer,
            "aud": self.audience,
            "sub": user_id,
            "iat": now,
            "exp": now + ttl_seconds,
            # Custom claims
            "ms": mission_session_id,
            "aid": alert_id,
            "scopes": scopes,
            "nonce": nonce,
        }

        # Add optional hints
        if pair:
            claims["pair"] = pair
        if timeframe:
            claims["tf"] = timeframe
        if risk_max_usd is not None:
            claims["riskMaxUsd"] = risk_max_usd

        # Generate token with header
        token = jwt.encode(claims, self.private_key, algorithm=self.algorithm, headers={"kid": self.key_id})

        logger.info(f"✅ Generated JWT for user {user_id}, session {mission_session_id}, expires in {ttl_seconds}s")
        return token

    def validate_token(self, token: str) -> Dict:
        """
        Validate and decode a JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded claims dictionary

        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        if not self.public_key:
            raise ValueError("Public key not loaded - cannot validate tokens")

        try:
            # Decode and verify
            claims = jwt.decode(
                token, self.public_key, algorithms=[self.algorithm], audience=self.audience, issuer=self.issuer
            )

            # Additional validation
            required_claims = ["sub", "ms", "aid", "scopes", "nonce"]
            for claim in required_claims:
                if claim not in claims:
                    raise jwt.InvalidTokenError(f"Missing required claim: {claim}")

            # Validate scopes is a list
            if not isinstance(claims["scopes"], list):
                raise jwt.InvalidTokenError("Scopes must be a list")

            logger.info(f"✅ Validated JWT for user {claims['sub']}, session {claims['ms']}")
            return claims

        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ Token expired")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"⚠️ Invalid token: {e}")
            raise

    def has_scope(self, claims: Dict, required_scope: str) -> bool:
        """Check if token has a required scope"""
        scopes = claims.get("scopes", [])
        return required_scope in scopes

    def extract_token_from_header(self, auth_header: Optional[str]) -> Optional[str]:
        """
        Extract JWT token from Authorization header

        Args:
            auth_header: Authorization header value (e.g., "Bearer <token>")

        Returns:
            Token string or None
        """
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]

    def get_nonce(self, claims: Dict) -> str:
        """Extract nonce from claims"""
        return claims.get("nonce", "")


# Global instance
_jwt_manager = None


def get_jwt_manager() -> JWTManager:
    """Get or create global JWT manager instance"""
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    return _jwt_manager


# Key generation utility
def generate_rsa_keypair(output_dir: str = "/root/HydraX-v2/keys"):
    """
    Generate RSA key pair for JWT signing

    Usage:
        python -c "from src.security.jwt_manager import generate_rsa_keypair; generate_rsa_keypair()"
    """
    import subprocess
    from pathlib import Path

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    private_key_path = f"{output_dir}/jwt_private.pem"
    public_key_path = f"{output_dir}/jwt_public.pem"

    # Generate private key
    subprocess.run(["openssl", "genrsa", "-out", private_key_path, "2048"], check=True)

    # Extract public key
    subprocess.run(["openssl", "rsa", "-in", private_key_path, "-pubout", "-out", public_key_path], check=True)

    print(f"✅ Generated RSA key pair:")
    print(f"   Private: {private_key_path}")
    print(f"   Public:  {public_key_path}")
    print(f"\nAdd to .env:")
    print(f"JWT_PRIVATE_KEY_PATH={private_key_path}")
    print(f"JWT_PUBLIC_KEY_PATH={public_key_path}")


if __name__ == "__main__":
    # Test token generation
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "keygen":
        generate_rsa_keypair()
    else:
        # Test
        manager = get_jwt_manager()

        # Generate test token
        token = manager.generate_mission_token(
            user_id="user_test",
            mission_session_id="ms_test123",
            alert_id=999,
            scopes=["mission:view", "order:execute"],
            pair="EURUSD",
            risk_max_usd=150.0,
        )

        print(f"Generated token: {token[:50]}...")

        # Validate it
        claims = manager.validate_token(token)
        print(f"Validated claims: {claims}")

        # Check scope
        has_execute = manager.has_scope(claims, "order:execute")
        print(f"Has order:execute scope: {has_execute}")
