# __init__.py
# USER CONTROL AND DISCLAIMER SYSTEM

"""
BITTEN User Control System

This system provides:
1. Legal disclaimers and risk warnings
2. User consent management
3. Bot control toggles
4. Immersion level settings

All features respect user choice and provide transparency.
"""

from .disclaimer_manager import (
    DisclaimerManager,
    UserConsent
)

__all__ = [
    'DisclaimerManager',
    'UserConsent'
]