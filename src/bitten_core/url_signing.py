"""
Simple URL Generator for BITTEN Telegram Bot
Generates simple user_id URLs for HUD access
"""

import time
from typing import Any, Dict, Optional

# Base URL for the HUD interface - Using working HTTPS domain
BASE_URL = "https://joinbitten.com"


class URLSigner:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url

    def create_simple_url(self, uid: str, path: str, additional_params: Dict[str, Any] = None) -> str:
        """
        Create a simple URL with user_id parameter

        Args:
            uid: User ID
            path: Path (e.g., '/mission-brief')
            additional_params: Additional parameters like ticketId, missionId

        Returns:
            Simple URL like: http://host:3000/path?user_id=uid&param=value
        """
        # Build parameters - start with user_id
        params = {"user_id": uid}

        if additional_params:
            params.update(additional_params)

        # Build URL
        from urllib.parse import urlencode

        query_string = urlencode(params)
        return f"{self.base_url}{path}?{query_string}"

    def create_mission_brief_url(self, uid: str, mission_id: Optional[str] = None) -> str:
        """Create simple URL for mission brief"""
        params = {}
        if mission_id:
            params["missionId"] = mission_id
        return self.create_simple_url(uid, "/mission-brief", params)

    def create_live_trade_url(self, uid: str, ticket_id: Optional[str] = None) -> str:
        """Create simple URL for live trade monitor"""
        params = {}
        if ticket_id:
            params["ticketId"] = ticket_id
        return self.create_simple_url(uid, "/live-trade", params)

    def create_war_room_url(self, uid: str) -> str:
        """Create simple URL for war room"""
        return self.create_simple_url(uid, "/war-room")

    def create_notebook_url(self, uid: str) -> str:
        """Create simple URL for notebook"""
        return self.create_simple_url(uid, "/notebook")

    def create_status_url(self, uid: str) -> str:
        """Create simple URL for status board"""
        return self.create_simple_url(uid, "/status")

    def create_stats_url(self, uid: str) -> str:
        """Create simple URL for stats page"""
        return self.create_simple_url(uid, "/stats")


# Global instance
url_signer = URLSigner()


# Mission and ticket validation functions
async def get_latest_mission_for_user(user_id: str) -> Optional[str]:
    """
    Get the latest active mission for a user

    TODO: Implement actual database lookup
    Returns sample mission ID for now
    """
    return f"msn-{user_id}-{int(time.time())}"


async def validate_mission_access(user_id: str, mission_id: str) -> bool:
    """
    Validate that user has access to the specified mission

    TODO: Implement actual validation against mission database
    """
    return True


async def get_active_trades_for_user(user_id: str) -> list:
    """
    Get active trade tickets for a user

    TODO: Implement actual database lookup
    Returns sample tickets for now
    """
    return [f"84231{197 + int(user_id[-1:]) if user_id[-1:].isdigit() else 197}"]


async def validate_ticket_access(user_id: str, ticket_id: str) -> bool:
    """
    Validate that user has access to the specified ticket

    TODO: Implement actual validation against trades database
    """
    return True


def format_help_message() -> str:
    """Format help message with command examples"""
    return """🎮 **BITTEN HUD SYSTEM**

**📋 Mission Commands:**
• `/brief` - Latest mission brief
• `/brief msn-001` - Specific mission

**📊 Trading Commands:**
• `/live` - Active trades monitor
• `/live 84231197` - Specific trade

**⚔️ Command Center:**
• `/war` - War room & stats
• `/notebook` - Training & notes

**🎯 Quick Access:**
• `/hud` - All interfaces menu

*Simple and fast access - no expiration*"""
