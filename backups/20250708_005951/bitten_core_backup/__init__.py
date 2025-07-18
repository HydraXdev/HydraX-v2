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
from .telegram_bot_controls import TelegramBotControls
from .bot_control_integration import BotControlIntegration, create_bot_control_integration
from .mission_briefing_generator import MissionBriefingGenerator, MissionBriefing, MissionType, UrgencyLevel
from .signal_display import SignalDisplay
from .signal_alerts import SignalAlert, SignalAlertSystem

__all__ = [
    # Core classes
    'BittenCore',
    'RankAccess',
    'TelegramRouter',
    'FireRouter',
    'XPLogger',
    'TradeWriter',
    'TelegramBotControls',
    'BotControlIntegration',
    'create_bot_control_integration',
    'MissionBriefingGenerator',
    'SignalDisplay',
    'SignalAlertSystem',
    
    # Enums
    'UserRank',
    'TradeDirection',
    'TradeOutcome',
    'TradeStatus',
    'SystemMode',
    'TacticalMode',
    'ExportFormat',
    'MissionType',
    'UrgencyLevel',
    
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
    'MissionBriefing',
    'SignalAlert',
    
    # Decorators
    'require_user',
    'require_authorized',
    'require_elite',
    'require_admin'
]