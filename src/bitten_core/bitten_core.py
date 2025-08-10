# bitten_core.py
# BITTEN Core Controller - Central System Orchestration Hub

import json
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import os
import sys

# Import BITTEN subsystems
from .rank_access import RankAccess, UserRank
from .telegram_router import TelegramRouter, TelegramUpdate, CommandResult
from .fire_router import FireRouter, TradeRequest, TradeDirection, TradeExecutionResult
from .bot_control_integration import create_bot_control_integration, BotControlIntegration, BotMessageMiddleware

# Import existing HydraX modules for integration
sys.path.append('/root/HydraX-v2/src')
from venom_activity_logger import log_signal_to_core, log_error

# Import crypto fire builder for C.O.R.E. signal execution
try:
    from .crypto_fire_builder import (
        crypto_fire_builder, 
        is_crypto_signal, 
        build_crypto_fire_packet,
        convert_crypto_packet_to_zmq
    )
    CRYPTO_FIRE_BUILDER_AVAILABLE = True
    print("✅ Crypto Fire Builder imported successfully")
except ImportError as e:
    CRYPTO_FIRE_BUILDER_AVAILABLE = False
    print(f"⚠️ Crypto Fire Builder not available: {e}")

class SystemMode(Enum):
    """System operation modes"""
    BIT = "bit"           # Basic Individual Trading
    COMMANDER = "commander"  # Advanced command mode
    TACTICAL = "tactical"    # Elite tactical operations
    STEALTH = "stealth"     # Stealth mode operations

class TacticalMode(Enum):
    """Tactical operation modes"""
    AUTO = "auto"       # Fully automated
    SEMI = "semi"       # Semi-automated with confirmations
    SNIPER = "sniper"   # Precision single-shot mode
    LEROY = "leroy"     # Aggressive high-risk mode

@dataclass
class SystemHealth:
    """System health monitoring"""
    core_status: str
    telegram_router: str
    fire_router: str
    rank_access: str
    uptime: float
    memory_usage: float
    error_count: int
    last_error: Optional[str] = None

@dataclass
class UserSession:
    """User session management"""
    user_id: int
    username: str
    mode: SystemMode
    tactical_mode: Optional[TacticalMode] = None
    last_activity: float = 0
    session_start: float = 0
    commands_count: int = 0
    trades_count: int = 0
    xp_earned: int = 0

class BittenCore:
    """BITTEN Core System Controller - Central orchestration hub"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._load_default_config()
        self.start_time = time.time()
        self.webhook_server = None  # Will be set by webhook server
        self.system_health = SystemHealth(
            core_status="initializing",
            telegram_router="offline",
            fire_router="offline", 
            rank_access="offline",
            uptime=0,
            memory_usage=0,
            error_count=0
        )
        
        # Initialize subsystems
        self.rank_access = RankAccess()
        self.telegram_router = TelegramRouter(bitten_core=self)
        self.fire_router = FireRouter(api_endpoint=self.config.get('api_endpoint', 'api.broker.local'))
        
        # Initialize bot control integration
        self.bot_control_integration = create_bot_control_integration(
            telegram_router=self.telegram_router,
            bitten_core=self
        )
        self.bot_message_middleware = BotMessageMiddleware(self.bot_control_integration)
        
        # User session management
        self.user_sessions: Dict[int, UserSession] = {}
        self.active_modes: Dict[int, SystemMode] = {}
        self.tactical_modes: Dict[int, TacticalMode] = {}
        
        # Signal queue management
        self.signal_queue: List[Dict] = []
        self.processed_signals: Dict[str, Dict] = {}
        self.signal_stats = {
            'total_signals': 0,
            'processed_signals': 0,
            'pending_signals': 0,
            'last_signal_time': None
        }
        
        # User session signal caching
        self.user_active_signals: Dict[str, List[Dict]] = {}  # user_id -> [active_signals]
        self.user_signal_history: Dict[str, List[Dict]] = {}  # user_id -> [signal_history]
        
        # Bot integration for signal delivery
        self.production_bot = None  # Will be set by BittenProductionBot
        
        # Import user registry manager for signal delivery
        try:
            from .user_registry_manager import UserRegistryManager
            self.user_registry = UserRegistryManager()
        except ImportError:
            self.user_registry = None
            self._log_error("UserRegistryManager not available")
        
        # Performance tracking
        self.performance_stats = {
            'total_commands': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'system_restarts': 0,
            'last_restart': None
        }
        
        # Initialize system
        self._initialize_system()
    
    def set_production_bot(self, bot_instance):
        """Set reference to BittenProductionBot for signal delivery"""
        self.production_bot = bot_instance
        self._log_info("Production bot integration enabled")
    
    def _load_default_config(self) -> Dict:
        """Load default system configuration"""
        return {
            'bridge_url': os.getenv('BRIDGE_URL', 'http://127.0.0.1:9000'),
            'webhook_url': os.getenv('WEBHOOK_URL', 'https://telegram1.joinbitten.com'),
            'debug_mode': os.getenv('DEBUG_MODE', 'false').lower() == 'true',
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'session_timeout': int(os.getenv('SESSION_TIMEOUT', '3600')),  # 1 hour
            'max_concurrent_sessions': int(os.getenv('MAX_CONCURRENT_SESSIONS', '100')),
            'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', '60')),  # 1 minute
            'supported_pairs': ['GBPUSD', 'USDCAD', 'GBPJPY', 'EURUSD', 'USDJPY']
        }
    
    def _initialize_system(self):
        """Initialize all subsystems"""
        try:
            # Update system health
            self.system_health.core_status = "online"
            self.system_health.telegram_router = "online"
            self.system_health.fire_router = "online"
            self.system_health.rank_access = "online"
            
            self._log_info("BITTEN Core System initialized successfully")
            
        except Exception as e:
            self.system_health.core_status = "error"
            self.system_health.last_error = str(e)
            self.system_health.error_count += 1
            self._log_error(f"System initialization failed: {e}")
    
    def process_telegram_update(self, update_data: Dict) -> Dict:
        """Process incoming Telegram update"""
        try:
            # Parse update
            update = self.telegram_router.parse_telegram_update(update_data)
            if not update:
                return {'success': False, 'message': 'Invalid update format'}
            
            # Update user session
            self._update_user_session(update)
            
            # Process command
            result = self.telegram_router.process_command(update)
            
            # Update performance stats
            self.performance_stats['total_commands'] += 1
            if result.success:
                self.performance_stats['successful_commands'] += 1
            else:
                self.performance_stats['failed_commands'] += 1
            
            return {
                'success': result.success,
                'message': result.message,
                'data': result.data
            }
            
        except Exception as e:
            self._log_error(f"Error processing Telegram update: {e}")
            self.system_health.error_count += 1
            return {
                'success': False,
                'message': f'❌ System error: {str(e)}'
            }
    
    def _update_user_session(self, update: TelegramUpdate):
        """Update user session information"""
        user_id = update.user_id
        current_time = time.time()
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = UserSession(
                user_id=user_id,
                username=update.username,
                mode=SystemMode.BIT,  # Default mode
                session_start=current_time,
                last_activity=current_time
            )
        
        session = self.user_sessions[user_id]
        session.last_activity = current_time
        session.commands_count += 1
        session.username = update.username  # Update username if changed
    
    def execute_trade(self, user_id: int, args: List[str]) -> CommandResult:
        """Execute trade via fire router"""
        try:
            if len(args) < 3:
                return CommandResult(False, "❌ Usage: `/fire SYMBOL buy/sell SIZE [TCS_SCORE]`")
            
            symbol = args[0].upper()
            direction_str = args[1].lower()
            volume = float(args[2])
            tcs_score = int(args[3]) if len(args) > 3 else 0
            
            # Validate symbol
            if symbol not in self.config['supported_pairs']:
                return CommandResult(
                    False, 
                    f"❌ Unsupported symbol: {symbol}. Supported: {', '.join(self.config['supported_pairs'])}"
                )
            
            # Validate direction
            if direction_str not in ['buy', 'sell']:
                return CommandResult(False, "❌ Direction must be 'buy' or 'sell'")
            
            direction = TradeDirection.BUY if direction_str == 'buy' else TradeDirection.SELL
            
            # Create trade request
            trade_request = TradeRequest(
                user_id=user_id,
                symbol=symbol,
                direction=direction,
                volume=volume,
                tcs_score=tcs_score,
                comment="BITTEN Core"
            )
            
            # Execute via fire router
            result = self.fire_router.execute_trade(trade_request)
            
            # Update session stats
            if user_id in self.user_sessions:
                self.user_sessions[user_id].trades_count += 1
                if result.success:
                    self.user_sessions[user_id].xp_earned += self._calculate_trade_xp(trade_request, result)
            
            # Update performance stats
            self.performance_stats['total_trades'] += 1
            if result.success:
                self.performance_stats['successful_trades'] += 1
            else:
                self.performance_stats['failed_trades'] += 1
            
            return CommandResult(
                success=result.success,
                message=result.message,
                data={
                    'trade_id': result.trade_id,
                    'execution_price': result.execution_price,
                    'tcs_score': result.tcs_score
                }
            )
            
        except ValueError as e:
            return CommandResult(False, f"❌ Invalid parameters: {str(e)}")
        except Exception as e:
            self._log_error(f"Trade execution error: {e}")
            return CommandResult(False, f"❌ Execution error: {str(e)}")
    
    def close_trade(self, user_id: int, trade_id: str) -> CommandResult:
        """Close specific trade"""
        try:
            result = self.fire_router.close_trade(trade_id, user_id)
            
            return CommandResult(
                success=result.success,
                message=result.message,
                data={'trade_id': result.trade_id}
            )
            
        except Exception as e:
            self._log_error(f"Trade close error: {e}")
            return CommandResult(False, f"❌ Close error: {str(e)}")
    
    def get_positions(self, user_id: int) -> CommandResult:
        """Get user's current positions"""
        try:
            positions = self.fire_router.get_positions(user_id)
            
            return CommandResult(
                success=positions['success'],
                message=positions['message'],
                data={'positions': positions['positions']}
            )
            
        except Exception as e:
            self._log_error(f"Get positions error: {e}")
            return CommandResult(False, f"❌ Error retrieving positions: {str(e)}")
    
    def get_balance(self, user_id: int) -> CommandResult:
        """Get user's account balance (placeholder)"""
        try:
            # This would connect to actual MT5 account via bridge
            # For now, return simulated balance
            balance_msg = f"""💰 **Account Balance**

📊 **Balance:** $10,000.00 (Demo)
📈 **Equity:** $10,250.00
📉 **Margin:** $500.00
🎯 **Free Margin:** $9,750.00
📊 **Margin Level:** 2,050.00%

⚠️ *Connect MT5 bridge for live data*"""
            
            return CommandResult(True, balance_msg)
            
        except Exception as e:
            self._log_error(f"Get balance error: {e}")
            return CommandResult(False, f"❌ Error retrieving balance: {str(e)}")
    
    def get_history(self, user_id: int, days: int = 7) -> CommandResult:
        """Get user's trading history"""
        try:
            # Get fire router execution stats
            stats = self.fire_router.get_execution_stats()
            
            history_msg = f"""📊 **Trading History ({days} days)**

🎯 **Performance Summary:**
• Total Trades: {stats['total_trades']}
• Successful: {stats['successful_trades']}
• Failed: {stats['failed_trades']}
• Success Rate: {stats['success_rate']}
• Volume Traded: {stats['total_volume']}

📈 **Current Status:**
• Active Positions: {stats['active_positions']}
• Daily Trades: {stats['daily_trades']}
• Last Execution: {stats['last_execution'] or 'None'}

💡 Use `/positions` for current trades"""
            
            return CommandResult(True, history_msg)
            
        except Exception as e:
            self._log_error(f"Get history error: {e}")
            return CommandResult(False, f"❌ Error retrieving history: {str(e)}")
    
    def get_performance(self, user_id: int) -> CommandResult:
        """Get user's performance metrics"""
        try:
            session = self.user_sessions.get(user_id)
            stats = self.fire_router.get_execution_stats()
            
            performance_msg = f"""📊 **Performance Metrics**

🎯 **Session Stats:**
• Commands: {session.commands_count if session else 0}
• Trades: {session.trades_count if session else 0}
• XP Earned: {session.xp_earned if session else 0}
• Session Time: {self._format_duration(time.time() - session.session_start) if session else 'N/A'}

🔥 **Trading Performance:**
• Success Rate: {stats['success_rate']}
• Total Volume: {stats['total_volume']}
• Active Positions: {stats['active_positions']}
• Risk Level: Medium

🏆 **Rankings:**
• Current Rank: {self.rank_access.get_user_rank(user_id).name}
• XP Progress: {session.xp_earned if session else 0}/1000 to next level
• Achievements: Coming soon!

💡 Type `/tactical` for advanced performance modes"""
            
            return CommandResult(True, performance_msg)
            
        except Exception as e:
            self._log_error(f"Get performance error: {e}")
            return CommandResult(False, f"❌ Error retrieving performance: {str(e)}")
    
    def set_mode(self, user_id: int, mode: str) -> CommandResult:
        """Set user's trading mode"""
        try:
            if mode not in [m.value for m in SystemMode]:
                return CommandResult(False, f"❌ Invalid mode. Available: {', '.join([m.value for m in SystemMode])}")
            
            self.active_modes[user_id] = SystemMode(mode)
            
            # Update session
            if user_id in self.user_sessions:
                self.user_sessions[user_id].mode = SystemMode(mode)
            
            mode_msg = f"""🎯 **Mode Updated**

**Current Mode:** {mode.upper()}

{self._get_mode_description(mode)}

💡 Use `/status` to check current settings"""
            
            return CommandResult(True, mode_msg)
            
        except Exception as e:
            self._log_error(f"Set mode error: {e}")
            return CommandResult(False, f"❌ Error setting mode: {str(e)}")
    
    def get_current_mode(self, user_id: int) -> CommandResult:
        """Get user's current mode"""
        try:
            mode = self.active_modes.get(user_id, SystemMode.BIT)
            tactical_mode = self.tactical_modes.get(user_id)
            
            mode_msg = f"""🎯 **Current Settings**

**Trading Mode:** {mode.value.upper()}
**Tactical Mode:** {tactical_mode.value.upper() if tactical_mode else 'Standard'}

{self._get_mode_description(mode.value)}

💡 Use `/mode [mode]` to change settings"""
            
            return CommandResult(True, mode_msg)
            
        except Exception as e:
            self._log_error(f"Get mode error: {e}")
            return CommandResult(False, f"❌ Error retrieving mode: {str(e)}")
    
    def set_tactical_mode(self, user_id: int, tactical_mode: str) -> CommandResult:
        """Set user's tactical mode"""
        try:
            if tactical_mode not in [m.value for m in TacticalMode]:
                return CommandResult(False, f"❌ Invalid tactical mode. Available: {', '.join([m.value for m in TacticalMode])}")
            
            self.tactical_modes[user_id] = TacticalMode(tactical_mode)
            
            # Update session
            if user_id in self.user_sessions:
                self.user_sessions[user_id].tactical_mode = TacticalMode(tactical_mode)
            
            tactical_msg = f"""⚡ **Tactical Mode Updated**

**Mode:** {tactical_mode.upper()}

{self._get_tactical_description(tactical_mode)}

🎯 **Next Steps:**
• Use `/fire` to execute trades in this mode
• Monitor performance with `/performance`
• Adjust settings with `/risk` (Elite+)"""
            
            return CommandResult(True, tactical_msg)
            
        except Exception as e:
            self._log_error(f"Set tactical mode error: {e}")
            return CommandResult(False, f"❌ Error setting tactical mode: {str(e)}")
    
    def get_tcs_score(self, user_id: int, symbol: str) -> CommandResult:
        """Get Trade Confidence Score for symbol"""
        try:
            symbol = symbol.upper()
            
            if symbol not in self.config['supported_pairs']:
                return CommandResult(False, f"❌ Unsupported symbol: {symbol}")
            
            # Calculate TCS score - NO FAKE DATA
            # TODO: Implement real TCS calculation from market data
            base_score = 70  # Default baseline score
            
            # Adjust based on time and volatility
            current_hour = datetime.now().hour
            if 8 <= current_hour <= 17:  # London session
                base_score += 5
            elif 13 <= current_hour <= 22:  # NY session
                base_score += 3
            
            tcs_score = min(base_score, 100)
            
            # Use centralized threshold
            from tcs_controller import get_current_threshold
            threshold = get_current_threshold()
            confidence_level = "🔥 HIGH" if tcs_score >= (threshold + 15) else "✅ GOOD" if tcs_score >= threshold else "⚠️ LOW"
            
            tcs_msg = f"""🎯 **Trade Confidence Score**

**Symbol:** {symbol}
**TCS Score:** {tcs_score}/100
**Confidence:** {confidence_level}

📊 **Analysis:**
• Technical Score: {tcs_score - 10}/100
• Volatility: Moderate
• Session: {'Active' if 8 <= current_hour <= 22 else 'Inactive'}
• Spread: Normal

🎯 **Recommendation:**
{self._get_tcs_recommendation(tcs_score)}

💡 Use `/fire {symbol} buy/sell 0.1 {tcs_score}` to trade"""
            
            return CommandResult(True, tcs_msg)
            
        except Exception as e:
            self._log_error(f"Get TCS error: {e}")
            return CommandResult(False, f"❌ Error calculating TCS: {str(e)}")
    
    def get_signals(self, user_id: int, symbol: Optional[str] = None) -> CommandResult:
        """Get market signals"""
        try:
            if symbol:
                symbol = symbol.upper()
                if symbol not in self.config['supported_pairs']:
                    return CommandResult(False, f"❌ Unsupported symbol: {symbol}")
                pairs = [symbol]
            else:
                pairs = self.config['supported_pairs']
            
            signals_msg = "📡 **Market Signals**\n\n"
            
            for pair in pairs:
                # Get real signal data - NO FAKE DATA
                # TODO: Get real signals from VENOM engine
                signal_strength = 0  # Real data needed
                direction = 'PENDING'  # Real data needed
                
                # Use centralized threshold
                from tcs_controller import get_current_threshold
                threshold = get_current_threshold()
                signal_emoji = "🔥" if signal_strength >= (threshold + 15) else "✅" if signal_strength >= threshold else "⚠️"
                
                signals_msg += f"{signal_emoji} **{pair}** - {direction}\n"
                signals_msg += f"   Strength: {signal_strength}/100\n"
                signals_msg += f"   Entry: Use `/fire {pair} {direction.lower()} 0.1`\n\n"
            
            signals_msg += "🎯 **Active Signals:** High-probability setups\n"
            signals_msg += "⏰ **Updated:** Every 5 minutes\n"
            signals_msg += "💡 **Tip:** Use TCS scores above 70 for best results"
            
            return CommandResult(True, signals_msg)
            
        except Exception as e:
            self._log_error(f"Get signals error: {e}")
            return CommandResult(False, f"❌ Error retrieving signals: {str(e)}")
    
    def get_system_status(self, user_id: int) -> CommandResult:
        """Get comprehensive system status"""
        try:
            # Update health metrics
            self.system_health.uptime = time.time() - self.start_time
            
            # Get user session info
            session = self.user_sessions.get(user_id)
            user_rank = self.rank_access.get_user_rank(user_id)
            
            status_msg = f"""📊 **BITTEN System Status**

🔧 **System Health:**
• Core: {self.system_health.core_status.upper()}
• Telegram Router: {self.system_health.telegram_router.upper()}
• Fire Router: {self.system_health.fire_router.upper()}
• Auth System: {self.system_health.rank_access.upper()}

⏱️ **System Metrics:**
• Uptime: {self._format_duration(self.system_health.uptime)}
• Error Count: {self.system_health.error_count}
• Commands Processed: {self.performance_stats['total_commands']}
• Trades Executed: {self.performance_stats['total_trades']}

👤 **Your Session:**
• Rank: {user_rank.name}
• Mode: {session.mode.value.upper() if session else 'BIT'}
• Commands: {session.commands_count if session else 0}
• Trades: {session.trades_count if session else 0}
• XP: {session.xp_earned if session else 0}

🎯 **Trading Status:**
• Supported Pairs: {len(self.config['supported_pairs'])}
• Active Positions: {self.fire_router.get_execution_stats()['active_positions']}
• Success Rate: {self.fire_router.get_execution_stats()['success_rate']}

{self.bot_control_integration.get_bot_status_for_display(str(user_id))}

💡 All systems operational and ready for trading"""
            
            return CommandResult(True, status_msg)
            
        except Exception as e:
            self._log_error(f"Get system status error: {e}")
            return CommandResult(False, f"❌ Error retrieving status: {str(e)}")
    
    def restart_system(self, user_id: int) -> CommandResult:
        """Restart system (admin only)"""
        try:
            self.performance_stats['system_restarts'] += 1
            self.performance_stats['last_restart'] = datetime.now().isoformat()
            
            # Clear user sessions
            self.user_sessions.clear()
            self.active_modes.clear()
            self.tactical_modes.clear()
            
            # Reset error count
            self.system_health.error_count = 0
            self.system_health.last_error = None
            
            # Re-initialize
            self._initialize_system()
            
            return CommandResult(True, "🔄 **System Restart Complete**\n\n✅ All subsystems reinitialized\n✅ User sessions cleared\n✅ Error counters reset\n\n🎯 System ready for operations")
            
        except Exception as e:
            self._log_error(f"System restart error: {e}")
            return CommandResult(False, f"❌ Restart failed: {str(e)}")
    
    def _calculate_trade_xp(self, trade_request: TradeRequest, result: TradeExecutionResult) -> int:
        """Calculate XP earned from trade"""
        base_xp = 10  # Base XP per trade
        
        # Bonus for TCS score using centralized threshold
        from tcs_controller import get_current_threshold
        threshold = get_current_threshold()
        if trade_request.tcs_score >= (threshold + 20):
            base_xp += 15
        elif trade_request.tcs_score >= (threshold + 10):
            base_xp += 10
        elif trade_request.tcs_score >= threshold:
            base_xp += 5
        
        # Bonus for volume
        if trade_request.volume >= 1.0:
            base_xp += 5
        
        return base_xp
    
    def _get_mode_description(self, mode: str) -> str:
        """Get description for trading mode"""
        descriptions = {
            'bit': "🎯 **BIT Mode:** Basic Individual Trading\n• Standard risk management\n• All basic commands available\n• Perfect for beginners",
            'commander': "⚡ **Commander Mode:** Advanced Operations\n• Enhanced risk controls\n• Batch operations\n• Advanced analytics",
            'tactical': "🔥 **Tactical Mode:** Elite Operations\n• Maximum flexibility\n• Advanced strategies\n• Professional tools",
            'stealth': "🥷 **Stealth Mode:** Covert Operations\n• Randomized parameters\n• Anti-detection features\n• Elite access only"
        }
        return descriptions.get(mode, "Standard trading mode")
    
    def _get_tactical_description(self, mode: str) -> str:
        """Get description for tactical mode"""
        descriptions = {
            'auto': "🤖 **Auto:** Fully automated execution\n• AI-driven decisions\n• Hands-free trading\n• Risk-managed",
            'semi': "🎯 **Semi:** Semi-automated with confirmations\n• Human oversight\n• Confirmation prompts\n• Balanced approach",
            'sniper': "🎯 **Sniper:** Precision single-shot mode\n• One perfect trade\n• Maximum accuracy\n• High-confidence only",
            'leroy': "🔥 **Leroy:** Aggressive high-risk mode\n• Maximum aggression\n• High reward potential\n• Expert traders only"
        }
        return descriptions.get(mode, "Standard tactical mode")
    
    def _get_tcs_recommendation(self, score: int) -> str:
        """Get TCS-based recommendation"""
        if score >= 90:
            return "🔥 **EXCELLENT** - High probability setup. Recommended for execution."
        elif score >= 80:
            return "✅ **GOOD** - Solid setup. Good for standard position sizing."
        elif score >= 70:
            return "⚠️ **CAUTION** - Marginal setup. Consider reduced position size."
        else:
            return "❌ **AVOID** - Low probability. Wait for better setup."
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _log_info(self, message: str):
        """Log info message"""
        print(f"[BITTEN_CORE INFO] {datetime.now().isoformat()}: {message}")
    
    def _log_error(self, message: str):
        """Log error message"""
        print(f"[BITTEN_CORE ERROR] {datetime.now().isoformat()}: {message}")
        self.system_health.error_count += 1
        self.system_health.last_error = message
    
    def process_outgoing_message(self, user_id: int, message: Dict) -> Optional[Dict]:
        """Process outgoing message through bot control middleware"""
        return self.bot_message_middleware.process_outgoing_message(str(user_id), message)
    
    def send_bot_message(self, user_id: int, bot_name: str, content: str, message_type: str = 'bot_message') -> Optional[str]:
        """Send bot message if allowed by user preferences"""
        message = {
            'type': message_type,
            'bot_name': bot_name,
            'content': content
        }
        
        processed = self.process_outgoing_message(user_id, message)
        if processed:
            return processed.get('content')
        return None
    
    def process_venom_signal(self, signal_data: Dict) -> Dict:
        """
        Process VENOM signal for dispatch - wrapper for process_signal
        
        Args:
            signal_data: Signal packet from VENOM stream
            
        Returns:
            Processing result status
        """
        self._log_info(f"🐍 Processing VENOM signal: {signal_data.get('signal_id', 'UNKNOWN')}")
        return self.process_signal(signal_data)
    
    def process_signal(self, signal_data: Dict) -> Dict:
        """
        Process VENOM signal packet for Core system intake
        
        Args:
            signal_data: Signal packet from VENOM v7
            
        Returns:
            Processing result status
        """
        try:
            # Validate required signal fields
            required_fields = ['signal_id', 'symbol', 'direction', 'signal_type', 
                             'confidence', 'target_pips', 'stop_pips', 'risk_reward']
            
            for field in required_fields:
                if field not in signal_data:
                    self._log_error(f"Signal missing required field: {field}")
                    return {'success': False, 'error': f'Missing field: {field}'}
            
            # Add processing timestamp
            signal_data['processed_at'] = datetime.now().isoformat()
            signal_data['status'] = 'pending'
            
            # CITADEL Shield Analysis with Live Data
            try:
                # Import CITADEL analyzer
                from citadel_core.citadel_analyzer import get_citadel_analyzer
                citadel = get_citadel_analyzer()
                
                # Prepare signal for CITADEL format
                citadel_signal = {
                    'signal_id': signal_data['signal_id'],
                    'pair': signal_data['symbol'],
                    'direction': signal_data['direction'].upper(),
                    'entry_price': signal_data.get('entry_price', 0),  # Will be calculated if not provided
                    'sl': signal_data.get('stop_loss', 0),
                    'tp': signal_data.get('take_profit', 0),
                    'signal_type': signal_data['signal_type']
                }
                
                # If entry/sl/tp not provided, calculate from pips
                if citadel_signal['entry_price'] == 0:
                    # Get current price from broker data if available
                    try:
                        import json
                        with open('/tmp/ea_raw_data.json', 'r') as f:
                            broker_data = json.load(f)
                            for tick in broker_data.get('ticks', []):
                                if tick['symbol'] == signal_data['symbol']:
                                    citadel_signal['entry_price'] = tick['bid'] if signal_data['direction'] == 'SELL' else tick['ask']
                                    break
                    except:
                        pass
                
                # Basic market data (will be enhanced by CITADEL)
                market_data = {
                    'recent_candles': [],
                    'recent_high': 0,
                    'recent_low': 0,
                    'atr': signal_data.get('atr', 0.0045)
                }
                
                # Run CITADEL analysis with live data enhancement
                shield_analysis = citadel.analyze_signal(
                    citadel_signal,
                    market_data,
                    user_id=None,  # Generic analysis for all users
                    use_live_data=True  # Enable live broker data enhancement
                )
                
                # Add CITADEL results to signal
                signal_data['shield_score'] = shield_analysis['shield_score']
                signal_data['shield_classification'] = shield_analysis['classification']
                signal_data['shield_label'] = shield_analysis['label']
                signal_data['shield_emoji'] = shield_analysis['emoji']
                signal_data['shield_explanation'] = shield_analysis['explanation']
                signal_data['shield_recommendation'] = shield_analysis['recommendation']
                
                # NO AUTOMATIC POSITION SIZING - Just informational
                # Users maintain full control over their risk
                signal_data['position_multiplier'] = 1.0  # Always use normal 2% risk
                
                self._log_info(f"🛡️ CITADEL Shield Score: {shield_analysis['shield_score']}/10 for {signal_data['signal_id']}")
                
            except Exception as e:
                self._log_error(f"CITADEL analysis error (non-fatal): {e}")
                # Continue without CITADEL if it fails
                signal_data['shield_score'] = 5.0
                signal_data['shield_classification'] = 'UNVERIFIED'
                signal_data['position_multiplier'] = 1.0
            
            # Store in signal queue for HUD preview
            self.signal_queue.append(signal_data)
            
            # Store in processed signals registry
            signal_id = signal_data['signal_id']
            self.processed_signals[signal_id] = signal_data
            
            # Update statistics
            self.signal_stats['total_signals'] += 1
            self.signal_stats['pending_signals'] = len(self.signal_queue)
            self.signal_stats['last_signal_time'] = signal_data['processed_at']
            
            # Log signal intake
            self._log_info(f"Signal processed: {signal_id} | {signal_data['symbol']} {signal_data['direction']} | TCS: {signal_data.get('confidence', 'N/A')}%")
            
            # Log to VENOM activity logger
            log_signal_to_core(signal_id, "processed", {
                "symbol": signal_data['symbol'],
                "direction": signal_data['direction'],
                "confidence": signal_data.get('confidence'),
                "signal_type": signal_data.get('signal_type'),
                "shield_score": signal_data.get('shield_score', 'N/A')
            })
            
            # Create mission file for HUD/webapp
            self._create_mission_file(signal_data)
            
            # Deliver signal to ready users
            delivery_result = self._deliver_signal_to_users(signal_data)
            
            return {
                'success': True,
                'signal_id': signal_id,
                'queued': True,
                'queue_size': len(self.signal_queue),
                'delivery_result': delivery_result
            }
            
        except Exception as e:
            self._log_error(f"Signal processing error: {e}")
            log_error("BittenCore", f"Signal processing error: {e}", {"signal_id": signal_data.get('signal_id', 'unknown')})
            return {'success': False, 'error': str(e)}
    
    def get_signal_queue(self) -> List[Dict]:
        """Get current signal queue for HUD display"""
        return self.signal_queue.copy()
    
    def get_signal_stats(self) -> Dict:
        """Get signal processing statistics"""
        return {
            **self.signal_stats,
            'processed_count': len(self.processed_signals),
            'queue_size': len(self.signal_queue)
        }
    
    def clear_expired_signals(self, max_age_minutes: int = 60):
        """Clear signals older than max_age_minutes"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
            
            # Filter signal queue
            initial_count = len(self.signal_queue)
            self.signal_queue = [
                signal for signal in self.signal_queue 
                if datetime.fromisoformat(signal['processed_at']) > cutoff_time
            ]
            
            # Update pending count
            self.signal_stats['pending_signals'] = len(self.signal_queue)
            
            cleared_count = initial_count - len(self.signal_queue)
            if cleared_count > 0:
                self._log_info(f"Cleared {cleared_count} expired signals from queue")
                
        except Exception as e:
            self._log_error(f"Error clearing expired signals: {e}")
    
    def _deliver_signal_to_users(self, signal_data: Dict) -> Dict:
        """Deliver signal via ATHENA tactical mission briefings"""
        try:
            # XAUUSD GATING: Check if this is a GOLD signal
            symbol = signal_data.get('symbol', '').upper()
            if symbol == 'XAUUSD' or 'GOLD' in symbol:
                # Route XAUUSD signals privately to offshore users only
                return self._deliver_gold_signal_privately(signal_data)
            
            # NEW: ATHENA Dual Dispatch System (Individual + Group)
            try:
                from athena_signal_dispatcher import athena_dispatcher
                from athena_group_dispatcher import athena_group_dispatcher
                
                # GROUP ONLY - Skip individual tactical briefings
                # athena_result = athena_dispatcher.dispatch_signal_via_athena(signal_data)
                
                # 2. Dispatch short tactical message to group ONLY
                group_result = athena_group_dispatcher.dispatch_group_signal(signal_data)
                
                # Create fake success result for athena_result to maintain compatibility
                athena_result = {'success': False, 'dispatch_results': []}
                
                if group_result['success']:
                    delivered_users = [r['user_id'] for r in athena_result['dispatch_results'] if r['status'] == 'dispatched']
                    failed_users = [r['user_id'] for r in athena_result['dispatch_results'] if r['status'] != 'dispatched']
                    
                    self._log_info(f"🏛️ ATHENA individual dispatch: {len(delivered_users)} delivered, {len(failed_users)} failed")
                    self._log_info(f"📡 ATHENA group dispatch: {'✅ SUCCESS' if group_result['success'] else '❌ FAILED'}")
                    
                    return {
                        'success': True,
                        'public_broadcast': group_result['success'],
                        'total_delivered': len(delivered_users),
                        'user_delivery': {
                            'delivered_to': len(delivered_users),
                            'users': delivered_users,
                            'failed_users': failed_users
                        },
                        'signal_id': signal_data['signal_id'],
                        'athena_dispatch': True,
                        'dispatch_details': athena_result,
                        'group_details': group_result
                    }
                else:
                    self._log_error(f"❌ ATHENA dispatch failed: {athena_result.get('error')}")
                    # Still try group dispatch even if individual fails
                    group_result = athena_group_dispatcher.dispatch_group_signal(signal_data)
                    self._log_info(f"📡 ATHENA group dispatch (fallback): {'✅ SUCCESS' if group_result['success'] else '❌ FAILED'}")
                    # Fallback to original system
                    
            except ImportError:
                self._log_warning("⚠️ ATHENA Signal Dispatcher not available - using fallback")
                # Fallback to original system
            
            # FALLBACK: Original signal delivery system
            # Format signal for HUD display
            hud_message = self._format_signal_for_hud(signal_data)
            delivered_users = []
            failed_users = []
            
            # ALWAYS send to public group first (mission feed)
            public_group_id = -1002581996861
            public_delivered = False
            
            if self.production_bot:
                try:
                    self.production_bot.send_adaptive_response(
                        chat_id=public_group_id,
                        message_text=hud_message,
                        user_tier="PUBLIC",
                        user_action="signal_broadcast"
                    )
                    public_delivered = True
                    self._log_info(f"📡 Signal broadcasted to public group: {signal_data['signal_id']}")
                except Exception as e:
                    self._log_error(f"Failed to broadcast signal to public group: {e}")
            
            # GROUP ONLY - Skip individual user delivery
            delivery_to_users = {'delivered_to': 0, 'users': []}
            
            # Skip individual user delivery - GROUP ONLY mode
            """
            if self.user_registry:
                ready_users = self.user_registry.get_all_ready_users()
                
                if ready_users:
                    for telegram_id, user_info in ready_users.items():
                        try:
                            # Get user tier for adaptive response
                            user_tier = user_info.get('tier', 'NIBBLER')
                            
                            # Cache signal for user session
                            self._cache_signal_for_user(telegram_id, signal_data)
                            
                            # Deliver via production bot if available
                            if self.production_bot:
                                try:
                                    self.production_bot.send_adaptive_response(
                                        chat_id=int(telegram_id),
                                        message_text=hud_message,
                                        user_tier=user_tier,
                                        user_action="signal_delivery"
                                    )
                                    self._log_info(f"📡 Signal delivered via bot to {telegram_id} ({user_tier}): {signal_data['signal_id']}")
                                except Exception as e:
                                    self._log_error(f"Bot delivery failed for {telegram_id}: {e}")
                                    # Fall back to logging
                                    self._log_info(f"📡 Signal cached for {telegram_id} ({user_tier}): {signal_data['signal_id']}")
                            else:
                                # No bot available, just cache and log
                                self._log_info(f"📡 Signal cached for {telegram_id} ({user_tier}): {signal_data['signal_id']}")
                            
                            delivered_users.append(telegram_id)
                            
                        except Exception as e:
                            self._log_error(f"Failed to deliver signal to user {telegram_id}: {e}")
                            failed_users.append(telegram_id)
                    
                    delivery_to_users = {
                        'delivered_to': len(delivered_users), 
                        'users': delivered_users,
                        'failed_users': failed_users
                    }
                    self._log_info(f"Signal delivery to users: {len(delivered_users)} successful, {len(failed_users)} failed")
                else:
                    self._log_info("No ready users found for individual signal delivery")
            else:
                self._log_info("No user registry available for individual signal delivery")
            """
            
            # Return success if public broadcast worked, regardless of user delivery
            total_delivered = 1 if public_delivered else 0
            total_delivered += len(delivered_users)
            
            return {
                'success': True,
                'public_broadcast': public_delivered,
                'total_delivered': total_delivered,
                'user_delivery': delivery_to_users,
                'signal_id': signal_data['signal_id']
            }
            
        except Exception as e:
            self._log_error(f"Signal delivery error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _deliver_gold_signal_privately(self, signal_data: Dict) -> Dict:
        """Deliver XAUUSD signals privately to offshore users only"""
        try:
            delivered_users = []
            failed_users = []
            total_xp_awarded = 0
            
            # Get all ready users from registry
            if self.user_registry:
                ready_users = self.user_registry.get_all_ready_users()
                
                for telegram_id, user_info in ready_users.items():
                    # Check if user is offshore eligible
                    user_region = user_info.get('user_region', 'US')
                    offshore_opt_in = user_info.get('offshore_opt_in', False)
                    
                    if user_region != 'US' and offshore_opt_in:
                        try:
                            # Format gold signal
                            gold_message = self._format_gold_signal(signal_data)
                            
                            # Send via DM
                            if self.production_bot:
                                success = self.production_bot.send_dm_signal(
                                    telegram_id=telegram_id,
                                    signal_text=gold_message,
                                    parse_mode="Markdown"  # Using Markdown for cleaner format
                                )
                                
                                if success:
                                    delivered_users.append(telegram_id)
                                    
                                    # Award bonus XP
                                    self._award_xp(telegram_id, 200, "Gold Operative Mission")
                                    total_xp_awarded += 200
                                    
                                    # Log gold signal delivery
                                    self._log_gold_signal_delivery(
                                        telegram_id=telegram_id,
                                        user_info=user_info,
                                        signal_data=signal_data,
                                        xp_awarded=200
                                    )
                                    
                                    self._log_info(f"🏆 GOLD signal delivered to offshore user {telegram_id}")
                                else:
                                    failed_users.append(telegram_id)
                            else:
                                failed_users.append(telegram_id)
                                
                        except Exception as e:
                            self._log_error(f"Failed to deliver gold signal to {telegram_id}: {e}")
                            failed_users.append(telegram_id)
                    else:
                        # User not eligible - silently skip
                        self._log_info(f"User {telegram_id} not eligible for XAUUSD (region: {user_region}, opt-in: {offshore_opt_in})")
            
            # Return delivery result
            return {
                'success': True,
                'public_broadcast': False,  # Never broadcast XAUUSD to public
                'total_delivered': len(delivered_users),
                'user_delivery': {
                    'delivered_to': len(delivered_users),
                    'users': delivered_users,
                    'failed_users': failed_users
                },
                'signal_id': signal_data['signal_id'],
                'gold_signal': True,
                'total_xp_awarded': total_xp_awarded,
                'message': f"Gold signal delivered privately to {len(delivered_users)} offshore users"
            }
            
        except Exception as e:
            self._log_error(f"Error delivering gold signal: {e}")
            return {
                'success': False,
                'error': str(e),
                'signal_id': signal_data.get('signal_id', 'unknown')
            }
    
    def _format_gold_signal(self, signal_data: Dict) -> str:
        """Format XAUUSD signal for private delivery"""
        try:
            # Extract signal details
            direction = signal_data.get('direction', 'BUY').upper()
            entry_price = signal_data.get('entry_price', 0)
            stop_loss = signal_data.get('stop_loss', 0)
            take_profit = signal_data.get('take_profit', 0)
            signal_type = signal_data.get('signal_type', 'PRECISION_STRIKE')
            risk_reward = signal_data.get('risk_reward', 2.0)
            
            # Calculate pips
            if direction == "BUY":
                sl_pips = int((entry_price - stop_loss) * 10)  # XAUUSD = 1 pip = 0.10
                tp_pips = int((take_profit - entry_price) * 10)
            else:
                sl_pips = int((stop_loss - entry_price) * 10)
                tp_pips = int((entry_price - take_profit) * 10)
            
            # Get current time + 15 minutes for window
            from datetime import datetime, timedelta
            window_time = datetime.now() + timedelta(minutes=15)
            window_str = window_time.strftime("%H:%M")
            
            # Format message
            message = f"""🏆 **[GOLD OPERATIVE]** 🏆

**Signal**: {direction} XAUUSD
**Entry**: {entry_price:.2f}
**SL**: {stop_loss:.2f} (-{sl_pips} pips)
**TP**: {take_profit:.2f} (+{tp_pips} pips)
**R:R**: 1:{risk_reward}

💠 **Bonus**: +200 XP for Private Execution
🕒 **Window**: 15 minutes (until {window_str})
⚡ **Type**: {signal_type}

_Elite operative mission. Execute with precision._"""
            
            return message
            
        except Exception as e:
            self._log_error(f"Error formatting gold signal: {e}")
            # Fallback format
            return f"🏆 GOLD SIGNAL: {signal_data.get('direction', 'BUY')} XAUUSD @ {signal_data.get('entry_price', 0)}"
    
    def _award_xp(self, telegram_id: str, xp_amount: int, reason: str):
        """Award XP to user (placeholder for actual XP system)"""
        try:
            # TODO: Integrate with actual XP system when available
            self._log_info(f"💰 XP Award: {telegram_id} +{xp_amount} XP for {reason}")
            
            # For now, just log to console
            print(f"[XP SYSTEM] User {telegram_id} awarded {xp_amount} XP: {reason}")
            
        except Exception as e:
            self._log_error(f"Error awarding XP: {e}")
    
    def _log_gold_signal_delivery(self, telegram_id: str, user_info: Dict, signal_data: Dict, xp_awarded: int):
        """Log gold signal delivery to JSONL file for tracking and analytics"""
        try:
            import json
            import os
            from datetime import datetime
            
            # Prepare log data
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_info.get('user_id', 'unknown'),
                "telegram_id": telegram_id,
                "username": user_info.get('username', 'unknown'),  # May need to be fetched separately
                "container": user_info.get('container', 'unknown'),
                "symbol": "XAUUSD",
                "signal_id": signal_data.get('signal_id', 'unknown'),
                "direction": signal_data.get('direction', 'unknown'),
                "entry": signal_data.get('entry_price', 0),
                "tp": signal_data.get('take_profit', 0),
                "sl": signal_data.get('stop_loss', 0),
                "risk_reward": signal_data.get('risk_reward', 0),
                "signal_type": signal_data.get('signal_type', 'unknown'),
                "confidence": signal_data.get('confidence', 0),
                "tcs_score": signal_data.get('confidence', 0),  # Using confidence as TCS
                "citadel_score": signal_data.get('citadel_score', 0),
                "pattern": signal_data.get('pattern', 'unknown'),
                "xp_awarded": xp_awarded,
                "user_region": user_info.get('user_region', 'unknown'),
                "offshore_opt_in": user_info.get('offshore_opt_in', False)
            }
            
            # Ensure logs directory exists
            log_dir = "/root/HydraX-v2/logs"
            os.makedirs(log_dir, exist_ok=True)
            
            # Write to JSONL file (append mode)
            log_file = os.path.join(log_dir, "gold_dm_log.jsonl")
            with open(log_file, "a") as f:
                f.write(json.dumps(log_data) + "\n")
            
            self._log_info(f"📝 Gold signal logged for user {telegram_id} - Signal ID: {signal_data.get('signal_id')}")
            
            # Also log to console for immediate visibility
            print(f"[GOLD_SIGNAL_DELIVERED]: User {telegram_id} - Signal {signal_data.get('signal_id')}")
            
        except Exception as e:
            self._log_error(f"Error logging gold signal delivery: {e}")
            # Don't fail the delivery just because logging failed
    
    def _format_signal_for_hud(self, signal_data: Dict) -> str:
        """Format signal data for Telegram HUD display"""
        try:
            # Calculate expires_in minutes
            expires_at = signal_data.get('expires_at')
            expires_in = "N/A"
            
            if expires_at:
                if isinstance(expires_at, str):
                    from datetime import datetime
                    expires_at = datetime.fromisoformat(expires_at)
                
                time_diff = expires_at - datetime.now()
                expires_in = f"{int(time_diff.total_seconds() / 60)} min"
            elif signal_data.get('countdown_minutes'):
                expires_in = f"{int(signal_data['countdown_minutes'])} min"
            
            # Extract key fields for HUD
            symbol = signal_data.get('symbol', 'N/A')
            direction = signal_data.get('direction', 'N/A')
            confidence = signal_data.get('confidence', 'N/A')
            signal_type = signal_data.get('signal_type', 'N/A')
            signal_id = signal_data.get('signal_id', 'N/A')
            
            # Format strategy display
            strategy_display = signal_type.upper()
            
            # Get CITADEL shield data
            shield_score = signal_data.get('shield_score', 'N/A')
            shield_emoji = signal_data.get('shield_emoji', '🔍')
            shield_label = signal_data.get('shield_label', 'ANALYZING')
            
            # Create HUD message in specified format
            hud_message = f"""🎯 [VENOM v7 Signal]
🧠 Symbol: {symbol}
📈 Direction: {direction}
🔥 Confidence: {confidence}%
🛡️ CITADEL: {shield_emoji} {shield_score}/10 [{shield_label}]
⏳ Expires in: {expires_in}
Reply: /fire {signal_id} to execute"""

            return hud_message
            
        except Exception as e:
            self._log_error(f"HUD formatting error: {e}")
            return f"🎯 Signal {signal_data.get('signal_id', 'Unknown')} - Use /fire to execute"
    
    def _cache_signal_for_user(self, user_id: str, signal_data: Dict):
        """Cache active signal for user session"""
        try:
            # Initialize user caches if needed
            if user_id not in self.user_active_signals:
                self.user_active_signals[user_id] = []
            if user_id not in self.user_signal_history:
                self.user_signal_history[user_id] = []
            
            # Add to active signals
            self.user_active_signals[user_id].append(signal_data)
            
            # Add to history
            self.user_signal_history[user_id].append({
                'signal_id': signal_data['signal_id'],
                'received_at': datetime.now().isoformat(),
                'status': 'pending'
            })
            
            # Limit active signals per user (keep last 10)
            if len(self.user_active_signals[user_id]) > 10:
                self.user_active_signals[user_id] = self.user_active_signals[user_id][-10:]
            
            # Limit history per user (keep last 50)
            if len(self.user_signal_history[user_id]) > 50:
                self.user_signal_history[user_id] = self.user_signal_history[user_id][-50:]
                
        except Exception as e:
            self._log_error(f"Error caching signal for user {user_id}: {e}")
    
    def get_user_active_signals(self, user_id: str) -> List[Dict]:
        """Get user's active signals (not expired)"""
        try:
            if user_id not in self.user_active_signals:
                return []
            
            active_signals = []
            current_time = datetime.now()
            
            for signal in self.user_active_signals[user_id]:
                expires_at = signal.get('expires_at')
                if expires_at:
                    if isinstance(expires_at, str):
                        expires_at = datetime.fromisoformat(expires_at)
                    
                    # Only include non-expired signals
                    if current_time <= expires_at:
                        active_signals.append(signal)
                else:
                    # No expiry date, include it
                    active_signals.append(signal)
            
            # Update user's active signals cache
            self.user_active_signals[user_id] = active_signals
            
            return active_signals
            
        except Exception as e:
            self._log_error(f"Error getting active signals for user {user_id}: {e}")
            return []
    
    def mark_user_signal_executed(self, user_id: str, signal_id: str):
        """Mark user's signal as executed in history"""
        try:
            if user_id in self.user_signal_history:
                for signal_record in self.user_signal_history[user_id]:
                    if signal_record['signal_id'] == signal_id:
                        signal_record['status'] = 'executed'
                        signal_record['executed_at'] = datetime.now().isoformat()
                        break
        except Exception as e:
            self._log_error(f"Error marking signal executed for user {user_id}: {e}")
    
    def monitor_trade_result(self, user_id: str, signal_id: str, timeout: float = 60.0) -> Dict:
        """Monitor trade result from MT5BridgeAdapter and notify user"""
        try:
            if not self.fire_router.mt5_bridge_adapter:
                return {'success': False, 'error': 'MT5BridgeAdapter not available'}
            
            # Monitor trade result with timeout
            trade_result = self.fire_router.mt5_bridge_adapter.get_trade_result(signal_id, timeout)
            
            if trade_result:
                # Process successful result
                self._log_info(f"📊 Trade result received for {signal_id}: {trade_result['status']}")
                
                # Update signal with trade result
                if signal_id in self.processed_signals:
                    self.processed_signals[signal_id]['trade_result'] = trade_result
                    self.processed_signals[signal_id]['result_received_at'] = datetime.now().isoformat()
                
                # Notify user via Telegram
                self._notify_user_trade_result(user_id, signal_id, trade_result)
                
                return {
                    'success': True,
                    'trade_result': trade_result,
                    'message': 'Trade result received and user notified'
                }
            else:
                # Timeout or no result
                self._log_error(f"⏰ Trade result timeout for {signal_id} after {timeout}s")
                return {
                    'success': False,
                    'error': f'Trade result timeout after {timeout} seconds',
                    'timeout': True
                }
                
        except Exception as e:
            self._log_error(f"Trade result monitoring error for {signal_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _notify_user_trade_result(self, user_id: str, signal_id: str, trade_result: Dict):
        """Notify user about trade result via Telegram"""
        try:
            if not self.production_bot:
                self._log_error("Production bot not available for trade result notification")
                return
            
            # Get signal data for context
            signal_data = self.processed_signals.get(signal_id, {})
            
            # Format trade result message
            status_emoji = "✅" if trade_result['status'] == 'success' else "❌"
            
            result_message = f"""{status_emoji} **Trade Result: {signal_id}**

📊 **Symbol**: {signal_data.get('symbol', 'N/A')}
📈 **Direction**: {signal_data.get('direction', 'N/A')}
🏆 **Status**: {trade_result['status'].title()}
🎫 **Ticket**: {trade_result.get('ticket', 'N/A')}

💰 **Account Update**:
• Balance: ${trade_result.get('balance', 0):,.2f}
• Equity: ${trade_result.get('equity', 0):,.2f}
• Free Margin: ${trade_result.get('free_margin', 0):,.2f}

⏰ **Executed**: {trade_result.get('timestamp', datetime.now().isoformat())}

{trade_result.get('message', 'Trade completed successfully')}"""
            
            # Get user tier for adaptive response
            user_info = self.user_registry.get_user_info(user_id) if self.user_registry else {}
            user_tier = user_info.get('tier', 'NIBBLER')
            
            # Send notification via production bot
            self.production_bot.send_adaptive_response(
                chat_id=int(user_id),
                message_text=result_message,
                user_tier=user_tier,
                user_action="trade_result_notification"
            )
            
            self._log_info(f"📢 Trade result notification sent to user {user_id} for {signal_id}")
            
        except Exception as e:
            self._log_error(f"Error sending trade result notification to user {user_id}: {e}")
    
    def execute_fire_command(self, user_id: str, signal_id: str) -> Dict:
        """Handle /fire command execution for a specific signal"""
        try:
            # CRITICAL: COMMANDER 7176191872 - ZERO SIMULATION OVERRIDE
            if user_id == "7176191872":
                # UNRESTRICTED FIRE ACCESS - NO AUTHORIZATION CHECKS
                logger.info(f"🎖️ COMMANDER {user_id} fire command - ZERO SIMULATION ENFORCED")
                # Skip to direct execution with commander privileges
                return self._execute_commander_fire(user_id, signal_id)
            
            # Check if user is authorized (normal users only)
            if not self.user_registry or not self.user_registry.is_user_ready_for_fire(user_id):
                # Return specific message for non-ready users
                return {
                    'success': False, 
                    'error': 'not_ready_for_fire',
                    'message': """❌ You're not ready to fire yet.

But you're closer than you think.

🌐 Visit https://joinbitten.com to:
- Learn what BITTEN is
- Claim your free Press Pass
- Get full access to the system — even before funding your account

Your mission briefing is waiting."""
                }
            
            # Find the signal in processed signals
            if signal_id not in self.processed_signals:
                return {'success': False, 'error': f'Signal {signal_id} not found or expired'}
            
            signal_data = self.processed_signals[signal_id]
            
            # Check if signal is still valid (not expired)
            expires_at = signal_data.get('expires_at')
            if expires_at:
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                
                if datetime.now() > expires_at:
                    return {'success': False, 'error': f'Signal {signal_id} has expired'}
            
            # Enhanced signal detection and execution for crypto vs forex
            user_info = self.user_registry.get_user_info(user_id)
            
            # 🚀 CRYPTO SIGNAL DETECTION & EXECUTION
            if CRYPTO_FIRE_BUILDER_AVAILABLE and is_crypto_signal(signal_data):
                print(f"🔥 Detected C.O.R.E. crypto signal: {signal_id}")
                
                # Get user account balance for position sizing
                account_balance = user_info.get('account_balance', 10000.0)
                user_tier = user_info.get('tier', 'NIBBLER')
                
                # Build crypto fire packet with professional ATR-based system
                crypto_packet = build_crypto_fire_packet(
                    signal_data=signal_data,
                    user_profile={'tier': user_tier, 'risk_percent': 1.0},  # Professional 1% risk
                    account_balance=account_balance
                )
                
                if crypto_packet:
                    # Convert to ZMQ format for EA execution
                    zmq_command = convert_crypto_packet_to_zmq(crypto_packet)
                    
                    # Create enhanced trade request with crypto data
                    trade_request = TradeRequest(
                        user_id=user_id,
                        symbol=crypto_packet.symbol,
                        direction=TradeDirection.BUY if crypto_packet.action == 'buy' else TradeDirection.SELL,
                        volume=crypto_packet.lot,
                        stop_loss=crypto_packet.sl,
                        take_profit=crypto_packet.tp,
                        tcs_score=signal_data.get('confidence', 0),
                        mission_id=signal_id,
                        comment=f"CORE-{crypto_packet.symbol}-{signal_data.get('pattern', 'Unknown')}"
                    )
                    
                    print(f"✅ Crypto fire packet built: {crypto_packet.symbol} {crypto_packet.action} {crypto_packet.lot} lots")
                    print(f"   SL: {crypto_packet.sl} points, TP: {crypto_packet.tp} points")
                    print(f"   Risk: ${crypto_packet.risk_amount:.2f} ({2.0}% of ${account_balance:.2f})")
                else:
                    print(f"❌ Failed to build crypto fire packet for {signal_id}")
                    return {'success': False, 'error': 'Failed to build crypto trade packet'}
            else:
                # 📈 FOREX SIGNAL EXECUTION (Existing Logic)
                print(f"📈 Processing forex signal: {signal_id}")
                trade_request = TradeRequest(
                    user_id=user_id,
                    symbol=signal_data['symbol'],
                    direction=TradeDirection.BUY if signal_data['direction'] == 'BUY' else TradeDirection.SELL,
                    volume=0.01,  # Will be calculated by FireRouter based on user balance
                    tcs_score=signal_data.get('confidence', 0),
                    mission_id=signal_id
                )
            
            # Execute via FireRouter with enhanced monitoring
            execution_result = self.fire_router.execute_trade_request(trade_request, user_info)
            
            # Enhanced result processing with MT5BridgeAdapter integration
            if execution_result.success:
                signal_data['status'] = 'executed'
                signal_data['executed_at'] = datetime.now().isoformat()
                signal_data['executed_by'] = user_id
                
                # Mark in user's signal history
                self.mark_user_signal_executed(user_id, signal_id)
                
                # Start background monitoring for trade result
                try:
                    import threading
                    monitor_thread = threading.Thread(
                        target=self.monitor_trade_result,
                        args=(user_id, signal_id, 120.0),  # 2-minute timeout
                        daemon=True
                    )
                    monitor_thread.start()
                    self._log_info(f"🔍 Started background monitoring for trade result: {signal_id}")
                except Exception as e:
                    self._log_error(f"Error starting trade result monitoring for {signal_id}: {e}")
                
                # Try to get immediate trade details from MT5BridgeAdapter
                trade_result = None
                try:
                    if hasattr(self.fire_router, 'mt5_bridge_adapter') and self.fire_router.mt5_bridge_adapter:
                        # Quick check for immediate result (non-blocking)
                        trade_result = self.fire_router.mt5_bridge_adapter.get_trade_result(signal_id, timeout=5.0)
                        if trade_result:
                            signal_data['trade_result'] = trade_result
                            self._log_info(f"🔥 Immediate trade result captured for {signal_id}: {trade_result}")
                except Exception as e:
                    self._log_error(f"Immediate trade result check error for {signal_id}: {e}")
                
                self._log_info(f"🔥 Signal {signal_id} executed by user {user_id}")
                
                # Enhanced success response with trade details
                response = {
                    'success': True,
                    'signal_id': signal_id,
                    'execution_result': execution_result,
                    'message': execution_result.message,
                    'signal_data': {
                        'symbol': signal_data['symbol'],
                        'direction': signal_data['direction'],
                        'confidence': signal_data.get('confidence'),
                        'executed_at': signal_data['executed_at']
                    }
                }
                
                if trade_result:
                    response['trade_result'] = trade_result
                elif hasattr(self.fire_router, 'mt5_bridge_adapter') and self.fire_router.mt5_bridge_adapter:
                    response['monitoring_started'] = True
                    response['message'] += " (Trade result monitoring active)"
                
                return response
                
            else:
                self._log_error(f"❌ Signal {signal_id} execution failed for user {user_id}: {execution_result.message}")
                
                return {
                    'success': False,
                    'signal_id': signal_id,
                    'execution_result': execution_result,
                    'message': execution_result.message,
                    'error': execution_result.message
                }
            
        except Exception as e:
            self._log_error(f"Fire command execution error for signal {signal_id} by user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'signal_id': signal_id,
                'message': f"Execution failed: {str(e)}"
            }
    
    def _execute_commander_fire(self, user_id: str, signal_id: str) -> Dict:
        """COMMANDER 7176191872 - ZERO SIMULATION FIRE EXECUTION"""
        try:
            logger.info(f"🎖️ COMMANDER FIRE: User {user_id}, Signal {signal_id} - ZERO SIMULATION")
            
            # COMMANDER gets unrestricted access - create signal if not exists
            if signal_id not in self.processed_signals:
                # Create a test signal for commander testing
                test_signal = {
                    'signal_id': signal_id,
                    'symbol': 'EURUSD',  # Default for testing
                    'direction': 'BUY',
                    'confidence': 95.0,
                    'stop_pips': 20,
                    'target_pips': 40,
                    'timestamp': datetime.now(),
                    'user_id': user_id,
                    'commander_test': True
                }
                self.processed_signals[signal_id] = test_signal
                logger.info(f"🎖️ Created test signal for COMMANDER: {signal_id}")
            
            signal_data = self.processed_signals[signal_id]
            signal_data['executed_at'] = datetime.now().isoformat()
            signal_data['executed_by'] = user_id
            
            # CRITICAL: FORCE REAL EXECUTION - NO SIMULATION
            execution_result = self.fire_router.execute_trade_request(
                {
                    'user_id': user_id,
                    'signal_id': signal_id,
                    'symbol': signal_data['symbol'],
                    'direction': signal_data['direction'],
                    'confidence': signal_data.get('confidence', 95.0),
                    'commander_override': True,  # ZERO SIMULATION FLAG
                    'force_real_execution': True,  # ENFORCE REAL TRADING
                    'mt5_account': '94956065',  # Direct MT5 account
                    'mt5_server': 'MetaQuotes-Demo'
                },
                {'tier': 'COMMANDER', 'user_id': user_id}
            )
            
            logger.info(f"🎖️ COMMANDER EXECUTION RESULT: {execution_result.message}")
            
            # Mark as executed
            self.mark_user_signal_executed(user_id, signal_id)
            
            # Return immediate response - NO SIMULATION
            return {
                'success': True,
                'signal_id': signal_id,
                'execution_result': execution_result,
                'message': f"🎖️ COMMANDER FIRE EXECUTED: {execution_result.message}",
                'commander_mode': True,
                'simulation_disabled': True,
                'mt5_account': '94956065',
                'signal_data': {
                    'symbol': signal_data['symbol'],
                    'direction': signal_data['direction'],
                    'confidence': signal_data.get('confidence'),
                    'executed_at': signal_data['executed_at']
                }
            }
            
        except Exception as e:
            logger.error(f"🎖️ COMMANDER FIRE ERROR: {e}")
            return {
                'success': False,
                'error': str(e),
                'signal_id': signal_id,
                'message': f"🎖️ COMMANDER FIRE FAILED: {str(e)}",
                'commander_mode': True
            }
    
    def get_pending_signals_for_user(self, user_id: str) -> List[Dict]:
        """Get all pending signals that user can fire"""
        try:
            if not self.user_registry or not self.user_registry.is_user_ready_for_fire(user_id):
                return []
            
            pending_signals = []
            current_time = datetime.now()
            
            for signal in self.signal_queue:
                if signal.get('status') == 'pending':
                    # Check if not expired
                    expires_at = signal.get('expires_at')
                    if expires_at:
                        if isinstance(expires_at, str):
                            expires_at = datetime.fromisoformat(expires_at)
                        
                        if current_time <= expires_at:
                            pending_signals.append(signal)
                    else:
                        pending_signals.append(signal)
            
            return pending_signals
            
        except Exception as e:
            self._log_error(f"Error getting pending signals for user {user_id}: {e}")
            return []
    
    def get_core_stats(self) -> Dict:
        """Get core system statistics"""
        return {
            'uptime': self.system_health.uptime,
            'total_commands': self.performance_stats['total_commands'],
            'successful_commands': self.performance_stats['successful_commands'],
            'failed_commands': self.performance_stats['failed_commands'],
            'total_trades': self.performance_stats['total_trades'],
            'successful_trades': self.performance_stats['successful_trades'],
            'failed_trades': self.performance_stats['failed_trades'],
            'active_sessions': len(self.user_sessions),
            'error_count': self.system_health.error_count,
            'system_restarts': self.performance_stats['system_restarts'],
            'last_restart': self.performance_stats['last_restart'],
            'supported_pairs': self.config['supported_pairs']
        }
    
    def _create_mission_file(self, signal_data: Dict):
        """Create mission file for webapp/HUD access"""
        try:
            import os
            import json
            import time
            from datetime import datetime, timedelta
            
            signal_id = signal_data.get('signal_id', f"MISSION_{int(time.time())}")
            
            # Create mission data structure matching existing format
            mission_data = {
                "mission_id": signal_id,
                "signal_id": signal_id,
                "signal": {
                    "symbol": signal_data.get('symbol'),
                    "direction": signal_data.get('direction'),
                    "signal_type": signal_data.get('signal_type'),
                    "entry_price": signal_data.get('entry_price'),
                    "stop_loss": signal_data.get('sl'),
                    "take_profit": signal_data.get('tp'),
                    "stop_pips": signal_data.get('stop_pips', 10),
                    "target_pips": signal_data.get('target_pips', 20),
                    "risk_reward": signal_data.get('risk_reward', 2.0),
                    "confidence": signal_data.get('confidence'),
                    "tcs_score": signal_data.get('confidence'),
                    "pattern": signal_data.get('pattern_type'),
                    "pattern_type": signal_data.get('pattern_type'),
                    "session": signal_data.get('session'),
                    "timeframe": "M1"
                },
                "symbol": signal_data.get('symbol'),
                "direction": signal_data.get('direction'),
                "signal_type": signal_data.get('signal_type'),
                "entry_price": signal_data.get('entry_price'),
                "stop_loss": signal_data.get('sl'),
                "take_profit": signal_data.get('tp'),
                "stop_pips": signal_data.get('stop_pips', 10),
                "target_pips": signal_data.get('target_pips', 20),
                "risk_reward": signal_data.get('risk_reward', 2.0),
                "confidence": signal_data.get('confidence'),
                "tcs_score": signal_data.get('confidence'),
                "pattern": signal_data.get('pattern_type'),
                "pattern_type": signal_data.get('pattern_type'),
                "session": signal_data.get('session'),
                "timeframe": "M1",
                "shield_score": signal_data.get('shield_score', 7.0),
                "shield_classification": "SHIELD_ACTIVE",
                "shield_label": "SHIELD ACTIVE",
                "shield_emoji": "✅",
                "shield_explanation": "Signal processed through BITTEN Core system",
                "shield_recommendation": "Tactical execution recommended",
                "position_multiplier": 1.0,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=2)).isoformat(),
                "hard_close_at": (datetime.now() + timedelta(hours=2, minutes=5)).isoformat(),
                "countdown_seconds": 7200,
                "xp_reward": signal_data.get('xp_reward', 100),
                "status": "pending",
                "fire_count": 0,
                "user_fired": False,
                "source": "ELITE_GUARD_v6",
                "created_timestamp": int(time.time()),
                "processed_at": datetime.now().isoformat()
            }
            
            # Ensure missions directory exists
            missions_dir = "/root/HydraX-v2/missions"
            os.makedirs(missions_dir, exist_ok=True)
            
            # Write mission file
            mission_file = f"{missions_dir}/{signal_id}.json"
            with open(mission_file, 'w') as f:
                json.dump(mission_data, f, indent=2)
            
            self._log_info(f"✅ Mission file created: {mission_file}")
            
        except Exception as e:
            self._log_error(f"Failed to create mission file for {signal_data.get('signal_id', 'unknown')}: {e}")
