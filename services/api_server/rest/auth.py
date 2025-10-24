"""
Authentication middleware
"""
from fastapi import Header, HTTPException
from typing import Optional

from ..config import API_KEY_HEADER


async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key (optional for Phase 1)"""
    # Phase 1: No auth required
    # Phase 2: Implement API key validation against database
    return True
