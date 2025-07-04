# BITTEN Core System Package
"""
BITTEN Trading Operations Center (TOC) Implementation
High-probability trade filtering for forex markets
"""

__version__ = "1.0.0"
__author__ = "HydraX Development Team"

# Import core components
from .rank_access import RankAccess, UserRank, require_user, require_authorized, require_elite, require_admin
from .telegram_router import TelegramRouter, TelegramUpdate, CommandResult
from .fire_router import FireRouter, TradeRequest, TradeDirection, TradeExecutionResult, TradingPairs
from .xp_logger import XPLogger, TradeLog, TradeOutcome, Achievement, UserPerformance
from .trade_writer import TradeWriter, TradeRecord, TradeStatus, ExportFormat
from .bitten_core import BittenCore, SystemMode, TacticalMode

__all__ = [
    # Core classes
    'BittenCore',
    'RankAccess',
    'TelegramRouter',
    'FireRouter',
    'XPLogger',
    'TradeWriter',
    
    # Enums
    'UserRank',
    'TradeDirection',
    'TradeOutcome',
    'TradeStatus',
    'SystemMode',
    'TacticalMode',
    'ExportFormat',
    
    # Data classes
    'TelegramUpdate',
    'CommandResult',
    'TradeRequest',
    'TradeExecutionResult',
    'TradeLog',
    'TradeRecord',
    'Achievement',
    'UserPerformance',
    'TradingPairs',
    
    # Decorators
    'require_user',
    'require_authorized',
    'require_elite',
    'require_admin'
]