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

# Import existing HydraX modules for integration
sys.path.append('/root/HydraX-v2/src')

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
        self.fire_router = FireRouter(bridge_url=self.config.get('bridge_url'))
        
        # User session management
        self.user_sessions: Dict[int, UserSession] = {}
        self.active_modes: Dict[int, SystemMode] = {}
        self.tactical_modes: Dict[int, TacticalMode] = {}
        
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
            
            # Simulate TCS calculation (would use real market analysis)
            import random
            base_score = random.randint(65, 95)
            
            # Adjust based on time and volatility
            current_hour = datetime.now().hour
            if 8 <= current_hour <= 17:  # London session
                base_score += 5
            elif 13 <= current_hour <= 22:  # NY session
                base_score += 3
            
            tcs_score = min(base_score, 100)
            
            confidence_level = "🔥 HIGH" if tcs_score >= 85 else "✅ GOOD" if tcs_score >= 70 else "⚠️ LOW"
            
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
                # Simulate signal generation
                import random
                signal_strength = random.randint(60, 95)
                direction = random.choice(['BUY', 'SELL'])
                
                signal_emoji = "🔥" if signal_strength >= 85 else "✅" if signal_strength >= 70 else "⚠️"
                
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
        
        # Bonus for TCS score
        if trade_request.tcs_score >= 90:
            base_xp += 15
        elif trade_request.tcs_score >= 80:
            base_xp += 10
        elif trade_request.tcs_score >= 70:
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
