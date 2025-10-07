# BITTEN Core System Package
"""
BITTEN Trading Operations Center (TOC) Implementation
High-probability trade filtering for forex markets
"""

__version__ = "1.0.0"
__author__ = "HydraX Development Team"

from .bitten_core import BittenCore, SystemMode, TacticalMode
from .bot_control_integration import BotControlIntegration, create_bot_control_integration
from .fire_router import FireRouter, TradeDirection, TradeExecutionResult, TradeRequest, TradingPairs
from .mission_briefing_generator import MissionBriefing, MissionBriefingGenerator, MissionType, UrgencyLevel

# Import core components
from .rank_access import RankAccess, UserRank, require_admin, require_authorized, require_elite, require_user
from .signal_alerts import SignalAlert, SignalAlertSystem
from .signal_display import SignalDisplay
from .telegram_bot_controls import TelegramBotControls
from .telegram_router import CommandResult, TelegramRouter, TelegramUpdate
from .trade_writer import ExportFormat, TradeRecord, TradeStatus, TradeWriter
from .xp_logger import Achievement, TradeLog, TradeOutcome, UserPerformance, XPLogger

__all__ = [
    # Core classes
    "BittenCore",
    "RankAccess",
    "TelegramRouter",
    "FireRouter",
    "XPLogger",
    "TradeWriter",
    "TelegramBotControls",
    "BotControlIntegration",
    "create_bot_control_integration",
    "MissionBriefingGenerator",
    "SignalDisplay",
    "SignalAlertSystem",
    # Enums
    "UserRank",
    "TradeDirection",
    "TradeOutcome",
    "TradeStatus",
    "SystemMode",
    "TacticalMode",
    "ExportFormat",
    "MissionType",
    "UrgencyLevel",
    # Data classes
    "TelegramUpdate",
    "CommandResult",
    "TradeRequest",
    "TradeExecutionResult",
    "TradeLog",
    "TradeRecord",
    "Achievement",
    "UserPerformance",
    "TradingPairs",
    "MissionBriefing",
    "SignalAlert",
    # Decorators
    "require_user",
    "require_authorized",
    "require_elite",
    "require_admin",
]
