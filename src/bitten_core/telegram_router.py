# telegram_router.py
# BITTEN Telegram Command Processing Engine

import json
import time
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from .rank_access import RankAccess, UserRank, require_user, require_authorized, require_elite, require_admin

@dataclass
class TelegramUpdate:
    """Telegram update message structure"""
    update_id: int
    message_id: int
    user_id: int
    username: str
    chat_id: int
    text: str
    timestamp: int

@dataclass
class CommandResult:
    """Command execution result"""
    success: bool
    message: str
    data: Optional[Dict] = None

class TelegramRouter:
    """Advanced Telegram command processing and routing system"""
    
    def __init__(self, bitten_core=None):
        self.rank_access = RankAccess()
        self.bitten_core = bitten_core
        self.command_history: List[Dict] = []
        self.error_count = 0
        self.last_reset = time.time()
        
        # Command categories for help system
        self.command_categories = {
            'System': ['start', 'help', 'status'],
            'Trading Info': ['positions', 'balance', 'history', 'performance'],
            'Trading Commands': ['fire', 'close', 'mode'],
            'Configuration': ['risk', 'maxpos', 'notify'],
            'Elite Features': ['tactical', 'tcs', 'signals', 'closeall', 'backtest'],
            'Admin Only': ['logs', 'restart', 'backup', 'promote', 'ban']
        }
    
    def parse_telegram_update(self, update_data: Dict) -> Optional[TelegramUpdate]:
        """Parse incoming Telegram update"""
        try:
            if 'message' not in update_data:
                return None
            
            message = update_data['message']
            
            return TelegramUpdate(
                update_id=update_data.get('update_id', 0),
                message_id=message.get('message_id', 0),
                user_id=message.get('from', {}).get('id', 0),
                username=message.get('from', {}).get('username', 'unknown'),
                chat_id=message.get('chat', {}).get('id', 0),
                text=message.get('text', ''),
                timestamp=message.get('date', int(time.time()))
            )
        except Exception as e:
            self._log_error(f"Failed to parse update: {e}")
            return None
    
    def process_command(self, update: TelegramUpdate) -> CommandResult:
        """Process and route Telegram command"""
        try:
            # Extract command and arguments
            command, args = self._parse_command(update.text)
            
            if not command:
                return CommandResult(False, "❌ Invalid command format")
            
            # Log command attempt
            self._log_command(update.user_id, update.username, command, args)
            
            # Check user authorization
            required_rank = self._get_command_rank(command)
            if not self.rank_access.check_permission(update.user_id, required_rank):
                user_rank = self.rank_access.get_user_rank(update.user_id)
                return CommandResult(
                    False, 
                    f"❌ Access denied. Required: {required_rank.name}, Your rank: {user_rank.name}"
                )
            
            # Check rate limits
            if not self.rank_access.check_rate_limit(update.user_id):
                return CommandResult(False, "❌ Rate limit exceeded. Please wait before sending more commands.")
            
            # Route command to appropriate handler
            result = self._route_command(command, args, update)
            
            # Log successful command
            self.rank_access.log_command(update.user_id, command)
            
            return result
            
        except Exception as e:
            self._log_error(f"Command processing error: {e}")
            return CommandResult(False, f"❌ Internal error: {str(e)}")
    
    def _parse_command(self, text: str) -> Tuple[str, List[str]]:
        """Parse command and arguments from text"""
        if not text.startswith('/'):
            return None, []
        
        parts = text.strip().split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        return command, args
    
    def _get_command_rank(self, command: str) -> UserRank:
        """Get required rank for command"""
        from .rank_access import COMMAND_PERMISSIONS
        return COMMAND_PERMISSIONS.get(command, UserRank.ELITE)
    
    def _route_command(self, command: str, args: List[str], update: TelegramUpdate) -> CommandResult:
        """Route command to appropriate handler"""
        
        # System Commands
        if command == '/start':
            return self._cmd_start(update.user_id, update.username)
        elif command == '/help':
            return self._cmd_help(update.user_id, args)
        elif command == '/status':
            return self._cmd_status(update.user_id)
        
        # Trading Information Commands
        elif command == '/positions':
            return self._cmd_positions(update.user_id)
        elif command == '/balance':
            return self._cmd_balance(update.user_id)
        elif command == '/history':
            return self._cmd_history(update.user_id, args)
        elif command == '/performance':
            return self._cmd_performance(update.user_id)
        
        # Trading Commands
        elif command == '/fire':
            return self._cmd_fire(update.user_id, args)
        elif command == '/close':
            return self._cmd_close(update.user_id, args)
        elif command == '/mode':
            return self._cmd_mode(update.user_id, args)
        
        # Configuration Commands
        elif command == '/risk':
            return self._cmd_risk(update.user_id, args)
        elif command == '/maxpos':
            return self._cmd_maxpos(update.user_id, args)
        elif command == '/notify':
            return self._cmd_notify(update.user_id, args)
        
        # Elite Commands
        elif command == '/tactical':
            return self._cmd_tactical(update.user_id, args)
        elif command == '/tcs':
            return self._cmd_tcs(update.user_id, args)
        elif command == '/signals':
            return self._cmd_signals(update.user_id, args)
        elif command == '/closeall':
            return self._cmd_closeall(update.user_id)
        elif command == '/backtest':
            return self._cmd_backtest(update.user_id, args)
        
        # Admin Commands
        elif command == '/logs':
            return self._cmd_logs(update.user_id, args)
        elif command == '/restart':
            return self._cmd_restart(update.user_id)
        elif command == '/backup':
            return self._cmd_backup(update.user_id)
        elif command == '/promote':
            return self._cmd_promote(update.user_id, args)
        elif command == '/ban':
            return self._cmd_ban(update.user_id, args)
        
        else:
            return CommandResult(False, f"❌ Unknown command: {command}")
    
    # System Commands
    @require_user()
    def _cmd_start(self, user_id: int, username: str) -> CommandResult:
        """Handle /start command"""
        user_rank = self.rank_access.get_user_rank(user_id)
        
        # Add user if not exists
        if not self.rank_access.get_user_info(user_id):
            self.rank_access.add_user(user_id, username)
        
        welcome_msg = f"""🤖 **BITTEN Trading Operations Center**

Welcome {username}! Your access level: **{user_rank.name}**

🎯 **Quick Commands:**
• `/status` - System status
• `/help` - Command list
• `/positions` - View positions (Auth+)
• `/fire` - Execute trade (Auth+)

🔐 **Access Levels:**
👤 USER → 🔑 AUTHORIZED → ⭐ ELITE → 🛡️ ADMIN

Type `/help` for complete command list."""
        
        return CommandResult(True, welcome_msg)
    
    @require_user()
    def _cmd_help(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /help command"""
        user_rank = self.rank_access.get_user_rank(user_id)
        
        if args and args[0] in self.command_categories:
            # Show specific category
            category = args[0]
            commands = self.command_categories[category]
            msg = f"📋 **{category} Commands:**\n"
            for cmd in commands:
                required_rank = self._get_command_rank(f"/{cmd}")
                if user_rank.value >= required_rank.value:
                    msg += f"• `/{cmd}` - {self._get_command_description(cmd)}\n"
            return CommandResult(True, msg)
        
        # Show available categories
        msg = f"🤖 **BITTEN Command Categories** (Rank: {user_rank.name})\n\n"
        
        for category, commands in self.command_categories.items():
            available_commands = []
            for cmd in commands:
                required_rank = self._get_command_rank(f"/{cmd}")
                if user_rank.value >= required_rank.value:
                    available_commands.append(cmd)
            
            if available_commands:
                msg += f"📁 **{category}** ({len(available_commands)} commands)\n"
                msg += f"Use: `/help {category.replace(' ', '')}` for details\n\n"
        
        msg += "💡 Type `/help [category]` for specific command details"
        
        return CommandResult(True, msg)
    
    @require_user()
    def _cmd_status(self, user_id: int) -> CommandResult:
        """Handle /status command"""
        if self.bitten_core:
            return self.bitten_core.get_system_status(user_id)
        
        # Fallback status
        user_info = self.rank_access.get_user_info(user_id)
        uptime = time.time() - self.last_reset
        
        status_msg = f"""📊 **BITTEN System Status**

🔧 **System Health:** ✅ Operational
⏱️ **Uptime:** {int(uptime/3600)}h {int((uptime%3600)/60)}m
👤 **Your Rank:** {user_info.rank.name if user_info else 'USER'}
📈 **Commands Processed:** {len(self.command_history)}
❌ **Error Count:** {self.error_count}

🤖 **Core System:** {'✅ Active' if self.bitten_core else '⚠️ Initializing'}
🔐 **Authorization:** ✅ Active
📡 **Telegram Router:** ✅ Active

Use `/positions` to check trading status"""
        
        return CommandResult(True, status_msg)
    
    # Trading Information Commands
    @require_authorized()
    def _cmd_positions(self, user_id: int) -> CommandResult:
        """Handle /positions command"""
        if self.bitten_core and hasattr(self.bitten_core, 'get_positions'):
            return self.bitten_core.get_positions(user_id)
        return CommandResult(False, "⚠️ Trading system not available")
    
    @require_authorized()
    def _cmd_balance(self, user_id: int) -> CommandResult:
        """Handle /balance command"""
        if self.bitten_core and hasattr(self.bitten_core, 'get_balance'):
            return self.bitten_core.get_balance(user_id)
        return CommandResult(False, "⚠️ Trading system not available")
    
    @require_authorized()
    def _cmd_history(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /history command"""
        days = 7  # Default
        if args and args[0].isdigit():
            days = int(args[0])
        
        if self.bitten_core and hasattr(self.bitten_core, 'get_history'):
            return self.bitten_core.get_history(user_id, days)
        return CommandResult(False, "⚠️ Trading system not available")
    
    @require_authorized()
    def _cmd_performance(self, user_id: int) -> CommandResult:
        """Handle /performance command"""
        if self.bitten_core and hasattr(self.bitten_core, 'get_performance'):
            return self.bitten_core.get_performance(user_id)
        return CommandResult(False, "⚠️ Trading system not available")
    
    # Trading Commands
    @require_authorized()
    def _cmd_fire(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /fire command"""
        if len(args) < 3:
            return CommandResult(False, "❌ Usage: `/fire SYMBOL buy/sell SIZE [SL] [TP]`")
        
        if self.bitten_core and hasattr(self.bitten_core, 'execute_trade'):
            return self.bitten_core.execute_trade(user_id, args)
        return CommandResult(False, "⚠️ Trading system not available")
    
    @require_authorized()
    def _cmd_close(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /close command"""
        if not args:
            return CommandResult(False, "❌ Usage: `/close TRADE_ID`")
        
        if self.bitten_core and hasattr(self.bitten_core, 'close_trade'):
            return self.bitten_core.close_trade(user_id, args[0])
        return CommandResult(False, "⚠️ Trading system not available")
    
    @require_authorized()
    def _cmd_mode(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /mode command"""
        if not args:
            if self.bitten_core and hasattr(self.bitten_core, 'get_current_mode'):
                return self.bitten_core.get_current_mode(user_id)
            return CommandResult(False, "⚠️ Trading system not available")
        
        mode = args[0].lower()
        if mode not in ['bit', 'commander']:
            return CommandResult(False, "❌ Available modes: `bit`, `commander`")
        
        if self.bitten_core and hasattr(self.bitten_core, 'set_mode'):
            return self.bitten_core.set_mode(user_id, mode)
        return CommandResult(False, "⚠️ Trading system not available")
    
    # Elite Commands  
    @require_elite()
    def _cmd_tactical(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /tactical command"""
        if not args:
            return CommandResult(False, "❌ Usage: `/tactical auto/semi/sniper/leroy`")
        
        tactical_mode = args[0].lower()
        if tactical_mode not in ['auto', 'semi', 'sniper', 'leroy']:
            return CommandResult(False, "❌ Available modes: `auto`, `semi`, `sniper`, `leroy`")
        
        if self.bitten_core and hasattr(self.bitten_core, 'set_tactical_mode'):
            return self.bitten_core.set_tactical_mode(user_id, tactical_mode)
        return CommandResult(False, "⚠️ Trading system not available")
    
    @require_elite()
    def _cmd_tcs(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /tcs command"""
        if not args:
            return CommandResult(False, "❌ Usage: `/tcs SYMBOL`")
        
        if self.bitten_core and hasattr(self.bitten_core, 'get_tcs_score'):
            return self.bitten_core.get_tcs_score(user_id, args[0])
        return CommandResult(False, "⚠️ Trading system not available")
    
    @require_elite()
    def _cmd_signals(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /signals command"""
        symbol = args[0] if args else None
        
        if self.bitten_core and hasattr(self.bitten_core, 'get_signals'):
            return self.bitten_core.get_signals(user_id, symbol)
        return CommandResult(False, "⚠️ Trading system not available")
    
    # Admin Commands
    @require_admin()
    def _cmd_logs(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /logs command"""
        lines = 50
        if args and args[0].isdigit():
            lines = min(int(args[0]), 200)  # Max 200 lines
        
        recent_commands = self.command_history[-lines:]
        log_msg = f"📋 **Recent Commands ({len(recent_commands)} entries):**\n\n"
        
        for cmd in recent_commands:
            timestamp = datetime.fromtimestamp(cmd['timestamp']).strftime("%H:%M:%S")
            log_msg += f"`{timestamp}` {cmd['username']}: {cmd['command']}\n"
        
        return CommandResult(True, log_msg)
    
    @require_admin()
    def _cmd_restart(self, user_id: int) -> CommandResult:
        """Handle /restart command"""
        if self.bitten_core and hasattr(self.bitten_core, 'restart_system'):
            return self.bitten_core.restart_system(user_id)
        return CommandResult(True, "🔄 System restart initiated...")
    
    def _get_command_description(self, command: str) -> str:
        """Get command description"""
        descriptions = {
            'start': 'Initialize bot session',
            'help': 'Show available commands',
            'status': 'System health check',
            'positions': 'View open positions',
            'balance': 'Account balance',
            'history': 'Trading history',
            'performance': 'Performance metrics',
            'fire': 'Execute trade',
            'close': 'Close position',
            'mode': 'Switch trading mode',
            'risk': 'Set risk parameters',
            'maxpos': 'Max positions limit',
            'notify': 'Notification settings',
            'tactical': 'Tactical mode',
            'tcs': 'Trade confidence score',
            'signals': 'Market signals',
            'closeall': 'Close all positions',
            'backtest': 'Strategy backtest',
            'logs': 'System logs',
            'restart': 'Restart system',
            'backup': 'Create backup',
            'promote': 'Promote user',
            'ban': 'Ban user'
        }
        return descriptions.get(command, 'Command description')
    
    def _log_command(self, user_id: int, username: str, command: str, args: List[str]):
        """Log command for history"""
        self.command_history.append({
            'timestamp': time.time(),
            'user_id': user_id,
            'username': username,
            'command': command,
            'args': args
        })
        
        # Keep only recent commands
        if len(self.command_history) > 1000:
            self.command_history = self.command_history[-500:]
    
    def _log_error(self, error_msg: str):
        """Log error for monitoring"""
        self.error_count += 1
        print(f"[ERROR] {datetime.now().isoformat()}: {error_msg}")
    
    def get_router_stats(self) -> Dict:
        """Get router statistics"""
        return {
            'commands_processed': len(self.command_history),
            'error_count': self.error_count,
            'uptime': time.time() - self.last_reset,
            'users_count': len(self.rank_access.users),
            'last_command': self.command_history[-1] if self.command_history else None
        }
