#!/usr/bin/env python3
"""
Deep Link Generator for Telegram Mission Alerts
Creates secure mission session links with JWT tokens
"""

import os
from typing import Dict
from urllib.parse import urlencode
import logging

from src.security.jwt_manager import get_jwt_manager
from src.mission_session.session_manager import get_session_manager

logger = logging.getLogger(__name__)

class DeepLinkGenerator:
    """Generates deep links for mission alerts"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('BITTEN_UI_URL', 'https://www.joinbitten.com')
        self.jwt_manager = get_jwt_manager()
        self.session_manager = get_session_manager()

    def generate_mission_link(
        self,
        signal_id: str,
        user_id: str,
        alert_id: int,
        pair: str = None,
        timeframe: str = None,
        risk_max_usd: float = None,
        session_ttl: int = 600  # 10 minutes
    ) -> Dict:
        """
        Generate a deep link for a mission alert

        Args:
            signal_id: Signal identifier
            user_id: User identifier
            alert_id: Alert ID
            pair: Trading pair
            timeframe: Timeframe
            risk_max_usd: Maximum risk in USD
            session_ttl: Session TTL in seconds

        Returns:
            Dictionary with deep_link, mission_session_id, and token
        """
        try:
            # Create mission session
            session = self.session_manager.create_session(
                user_id=user_id,
                signal_id=signal_id,
                alert_id=alert_id,
                pair=pair,
                timeframe=timeframe,
                risk_max_usd=risk_max_usd,
                ttl_seconds=session_ttl
            )

            # Generate JWT token
            token = self.jwt_manager.generate_mission_token(
                user_id=user_id,
                mission_session_id=session['mission_session_id'],
                alert_id=alert_id,
                scopes=["mission:view", "order:execute"],
                pair=pair,
                timeframe=timeframe,
                risk_max_usd=risk_max_usd,
                ttl_seconds=session_ttl
            )

            # Build deep link
            params = {
                'ms': session['mission_session_id'],
                'token': token
            }

            deep_link = f"{self.base_url}/mission?{urlencode(params)}"

            logger.info(f"✅ Generated deep link for user {user_id}, signal {signal_id}")

            return {
                'deep_link': deep_link,
                'mission_session_id': session['mission_session_id'],
                'token': token,
                'expires_at': session['expires_at']
            }

        except Exception as e:
            logger.error(f"❌ Error generating deep link: {e}")
            raise

    def generate_short_link(self, signal_id: str) -> str:
        """
        Generate short link format (legacy support)

        Args:
            signal_id: Signal identifier

        Returns:
            Short link URL
        """
        return f"{self.base_url}/m/{signal_id}"


# Global instance
_link_generator = None

def get_link_generator() -> DeepLinkGenerator:
    """Get or create global link generator instance"""
    global _link_generator
    if _link_generator is None:
        _link_generator = DeepLinkGenerator()
    return _link_generator


if __name__ == '__main__':
    # Add parent directory to path for imports
    import sys
    sys.path.insert(0, '/root/HydraX-v2')

    # Test
    generator = get_link_generator()

    # Generate test link
    link_data = generator.generate_mission_link(
        signal_id="ELITE_GUARD_EURUSD_123",
        user_id="user_test",
        alert_id=999,
        pair="EURUSD",
        timeframe="M5",
        risk_max_usd=150.0
    )

    print(f"Deep link: {link_data['deep_link']}")
    print(f"Session ID: {link_data['mission_session_id']}")
    print(f"Token: {link_data['token'][:50]}...")
    print(f"Expires at: {link_data['expires_at']}")
