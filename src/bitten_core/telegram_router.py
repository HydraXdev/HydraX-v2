# telegram_router.py
# BITTEN Telegram Command Processing Engine

import json
import time
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from .rank_access import RankAccess, UserRank, require_user, require_authorized, require_elite, require_admin
from .user_profile import UserProfileManager
from .mission_briefing_generator import MissionBriefingGenerator, MissionBriefing
from .social_sharing import SocialSharingManager
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

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
    
    def __init__(self, bitten_core=None, hud_webapp_url="https://your-domain.com/sniper_hud"):
        self.rank_access = RankAccess()
        self.bitten_core = bitten_core
        self.profile_manager = UserProfileManager()
        self.hud_webapp_url = hud_webapp_url
        self.command_history: List[Dict] = []
        self.error_count = 0
        self.last_reset = time.time()
        self.briefing_generator = MissionBriefingGenerator()
        self.active_briefings: Dict[str, MissionBriefing] = {}
        self.social_sharing = SocialSharingManager()
        
        # Command categories for help system
        self.command_categories = {
            'System': ['start', 'help', 'status', 'me'],
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
            return self._cmd_start(update.user_id, update.username, args)
        elif command == '/help':
            return self._cmd_help(update.user_id, args)
        elif command == '/status':
            return self._cmd_status(update.user_id)
        elif command == '/me':
            return self._cmd_me(update.user_id, update.chat_id)
        
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
    def _cmd_start(self, user_id: int, username: str, args: List[str]) -> CommandResult:
        """Handle /start command with referral support"""
        user_rank = self.rank_access.get_user_rank(user_id)
        
        # Add user if not exists
        is_new_user = not self.rank_access.get_user_info(user_id)
        if is_new_user:
            self.rank_access.add_user(user_id, username)
            
            # Check for referral code
            if args and args[0].startswith('ref_'):
                try:
                    recruiter_id = int(args[0].replace('ref_', ''))
                    if recruiter_id != user_id:  # Can't recruit yourself
                        success = self.profile_manager.register_recruit(
                            recruiter_id, user_id, username
                        )
                        if success:
                            # Notify user they were recruited
                            welcome_msg = f"""🤖 **B.I.T.T.E.N. Trading Operations Center**

**Bot-Integrated Tactical Trading Engine / Network**

Welcome {username}! You've been recruited to the elite force.
Your access level: **{user_rank.name}**

*"You've been B.I.T.T.E.N. — now prove you belong."*

🎯 **Quick Commands:**
• `/status` - System status
• `/help` - Command list
• `/me` - Your profile & stats
• `/positions` - View positions (Auth+)
• `/fire` - Execute trade (Auth+)

🔐 **Access Levels:**
👤 USER → 🔑 AUTHORIZED → ⭐ ELITE → 🛡️ ADMIN

Type `/help` for complete command list."""
                            return CommandResult(True, welcome_msg)
                except:
                    pass  # Invalid referral code
        
        welcome_msg = f"""🤖 **B.I.T.T.E.N. Trading Operations Center**

**Bot-Integrated Tactical Trading Engine / Network**

Welcome {username}! Your access level: **{user_rank.name}**

*"You've been B.I.T.T.E.N. — now prove you belong."*

🎯 **Quick Commands:**
• `/status` - System status
• `/help` - Command list
• `/me` - Your profile & stats
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
        msg = f"🤖 **B.I.T.T.E.N. Command Categories** (Rank: {user_rank.name})\n"
        msg += "*The Engine is watching. The Network is evolving.*\n\n"
        
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
    
    @require_user()
    def _cmd_me(self, user_id: int, chat_id: int) -> CommandResult:
        """Handle /me command - Personal profile with WebApp"""
        # Get full profile data
        profile = self.profile_manager.get_full_profile(user_id)
        user_rank = self.rank_access.get_user_rank(user_id)
        
        # Build profile message
        profile_msg = f"""👤 **OPERATIVE PROFILE**

**Rank:** {profile['rank']} | **XP:** {profile['total_xp']:,}/{profile['next_rank_xp']:,}
**Missions:** {profile['missions_completed']} | **Success Rate:** {profile['success_rate']}%

💰 **Combat Stats:**
• Total Profit: ${profile['total_profit']:,.2f}
• Largest Victory: ${profile['largest_win']:,.2f}
• Current Streak: {profile['current_streak']} | Best: {profile['best_streak']}

🎖️ **Medals:** {profile['medals_earned']}/{profile['medals_total']}
👥 **Recruits:** {profile['recruits_count']} | **Recruit XP:** {profile['recruit_xp']}

🔗 **Your Recruitment Link:**
`https://t.me/BITTEN_bot?start=ref_{user_id}`

*Operative since {profile['joined_days_ago']} days ago*"""
        
        # Create inline keyboard with WebApp button
        webapp_data = {
            'user_id': user_id,
            'view': 'profile',
            'timestamp': int(time.time())
        }
        
        keyboard = [
            [InlineKeyboardButton(
                "📊 VIEW FULL PROFILE", 
                web_app=WebAppInfo(
                    url=f"{self.hud_webapp_url}?data={json.dumps(webapp_data)}&view=profile"
                )
            )],
            [
                InlineKeyboardButton("📤 SHARE LINK", callback_data="share_recruit_link"),
                InlineKeyboardButton("🎖️ MEDALS", callback_data="view_medals")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(
            True, 
            profile_msg,
            data={'reply_markup': reply_markup}
        )
    
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
            'me': 'Your profile & stats',
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
    
    def send_signal_alert(self, user_id: int, signal_data: Dict, market_data: Optional[Dict] = None) -> CommandResult:
        """Send signal alert with mission briefing and HUD WebApp button"""
        # Get user tier
        user_rank = self.rank_access.get_user_rank(user_id)
        user_tier = user_rank.name
        
        # Generate mission briefing
        if market_data is None:
            market_data = self._get_default_market_data()
        
        briefing = self.briefing_generator.generate_mission_briefing(
            signal_data, market_data, user_tier
        )
        
        # Store active briefing
        self.active_briefings[briefing.mission_id] = briefing
        
        # Use shortened alert format
        from .signal_display import SignalDisplay
        display = SignalDisplay()
        alert_message = display.create_shortened_telegram_alert(signal_data, briefing)
        
        # Create inline keyboard with WebApp button
        webapp_data = {
            'mission_id': briefing.mission_id,
            'user_tier': user_tier,
            'timestamp': int(time.time()),
            'view': 'mission_briefing'
        }
        
        # Encode webapp data
        import urllib.parse
        encoded_data = urllib.parse.quote(json.dumps(webapp_data))
        
        keyboard = [
            [InlineKeyboardButton(
                "🎯 OPEN MISSION HUD", 
                web_app=WebAppInfo(
                    url=f"{self.hud_webapp_url}?data={encoded_data}"
                )
            )]
        ]
        
        # Add quick action buttons based on mission type and tier
        if briefing.mission_type.value == 'arcade_scalp':
            if user_tier in ['AUTHORIZED', 'ELITE', 'ADMIN']:
                keyboard.append([
                    InlineKeyboardButton("⚡ QUICK FIRE", callback_data=f"qf_{briefing.mission_id[:8]}"),
                    InlineKeyboardButton("📊 ANALYZE", callback_data=f"an_{briefing.mission_id[:8]}")
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton("🔓 UNLOCK TRADING", callback_data="unlock_auth")
                ])
        elif briefing.mission_type.value == 'sniper_shot':
            if user_tier in ['ELITE', 'ADMIN']:
                keyboard.append([
                    InlineKeyboardButton("🎯 EXECUTE", callback_data=f"sn_{briefing.mission_id[:8]}"),
                    InlineKeyboardButton("🔍 INTEL", callback_data=f"in_{briefing.mission_id[:8]}")
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton(f"🔓 ELITE ONLY", callback_data="unlock_elite")
                ])
        
        # Add share button for achievements
        keyboard.append([
            InlineKeyboardButton("📤 SHARE", callback_data=f"sh_{briefing.mission_id[:8]}"),
            InlineKeyboardButton("📱 MY STATS", web_app=WebAppInfo(
                url=f"{self.hud_webapp_url}?view=profile"
            ))
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(
            True,
            alert_message,
            data={'reply_markup': reply_markup, 'mission_briefing': briefing}
        )
    
    def _get_default_market_data(self) -> Dict:
        """Get default market data when not provided"""
        return {
            'volatility': 'NORMAL',
            'trend': 'NEUTRAL',
            'momentum': 'STABLE',
            'volume': 'AVERAGE',
            'session': self._get_current_session(),
            'key_levels': []
        }
    
    def _get_current_session(self) -> str:
        """Determine current trading session"""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        if 7 <= hour < 16:  # 7 AM - 4 PM UTC
            return 'LONDON'
        elif 12 <= hour < 21:  # 12 PM - 9 PM UTC
            return 'NEWYORK'
        else:
            return 'ASIAN'
    
    def get_mission_briefing(self, mission_id: str) -> Optional[MissionBriefing]:
        """Get active mission briefing by ID"""
        return self.active_briefings.get(mission_id)
    
    def cleanup_expired_briefings(self) -> int:
        """Remove expired mission briefings"""
        current_time = time.time()
        expired = [
            mission_id for mission_id, briefing in self.active_briefings.items()
            if briefing.expires_at < current_time
        ]
        
        for mission_id in expired:
            del self.active_briefings[mission_id]
        
        return len(expired)
    
    def send_signal_alert_legacy(self, user_id: int, signal_data: Dict) -> CommandResult:
        """Legacy method for backwards compatibility - converts old format to new"""
        # Convert old signal_data format to new format if needed
        if 'signal_id' in signal_data and 'urgency' in signal_data:
            # Old format detected, convert to new format
            converted_data = {
                'type': 'arcade',  # Default to arcade for legacy
                'symbol': signal_data.get('symbol', 'UNKNOWN'),
                'direction': signal_data.get('direction', 'BUY'),
                'entry_price': signal_data.get('entry_price', 0.0),
                'stop_loss': signal_data.get('stop_loss', signal_data.get('entry_price', 0.0) - 0.0010),
                'take_profit': signal_data.get('take_profit', signal_data.get('entry_price', 0.0) + 0.0030),
                'tcs_score': int(signal_data.get('confidence', 0.75) * 100),
                'confidence': signal_data.get('confidence', 0.75),
                'expires_at': signal_data.get('expires_at', int(time.time()) + 600),
                'expected_duration': 45,
                'active_traders': 0,
                'total_engaged': 0,
                'squad_avg_tcs': 70.0,
                'success_rate': 0.65
            }
            return self.send_signal_alert(user_id, converted_data)
        else:
            # Already in new format or close enough
            return self.send_signal_alert(user_id, signal_data)
    
    def send_achievement_notification(self, user_id: int, achievement_data: Dict) -> CommandResult:
        """Send achievement notification with share options"""
        # Create achievement card
        card = self.social_sharing.create_achievement_card(
            achievement_data['type'],
            achievement_data
        )
        
        # Generate message
        message = f"🎉 **ACHIEVEMENT UNLOCKED!**\n\n"
        message += f"🎖️ **{card.title}**\n"
        message += f"{card.description}\n\n"
        
        if card.type == 'medal':
            message += f"✨ +{card.value.get('xp_reward', 0)} XP earned!\n"
        elif card.type == 'streak':
            message += f"🔥 {card.value} wins in a row!\n"
        elif card.type == 'profit':
            message += f"💰 Total profit: ${card.value:,.2f}\n"
        
        # Create keyboard with sharing options
        keyboard = [
            [InlineKeyboardButton(
                "📱 VIEW IN HUD",
                web_app=WebAppInfo(
                    url=f"{self.hud_webapp_url}?view=achievements"
                )
            )],
            [
                InlineKeyboardButton("📤 Share on Telegram", callback_data=f"share_tg_{card.card_id[:8]}"),
                InlineKeyboardButton("🐦 Share on Twitter", callback_data=f"share_tw_{card.card_id[:8]}")
            ],
            [
                InlineKeyboardButton("🏆 View All Medals", callback_data="view_all_medals")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(
            True,
            message,
            data={'reply_markup': reply_markup, 'achievement_card': card}
        )
    
    def handle_callback_query(self, callback_query: Dict) -> CommandResult:
        """Handle inline button callbacks"""
        data = callback_query.get('data', '')
        user_id = callback_query.get('from', {}).get('id', 0)
        
        # Parse callback data
        parts = data.split('_')
        action = parts[0]
        
        # Route to appropriate handler
        if action == 'qf':  # Quick fire
            return self._handle_quick_fire(user_id, parts[1] if len(parts) > 1 else '')
        elif action == 'an':  # Analyze
            return self._handle_analyze_signal(user_id, parts[1] if len(parts) > 1 else '')
        elif action == 'sh':  # Share
            return self._handle_share_signal(user_id, parts[1] if len(parts) > 1 else '')
        elif action == 'share':
            platform = parts[1] if len(parts) > 1 else 'tg'
            card_id = parts[2] if len(parts) > 2 else ''
            return self._handle_share_achievement(user_id, platform, card_id)
        elif action == 'unlock':
            tier = parts[1] if len(parts) > 1 else 'auth'
            return self._handle_unlock_tier(user_id, tier)
        else:
            return CommandResult(False, "Unknown action")
    
    def _handle_quick_fire(self, user_id: int, mission_id_short: str) -> CommandResult:
        """Handle quick fire button press"""
        # Find full mission ID
        mission = None
        for mid, briefing in self.active_briefings.items():
            if mid.startswith(mission_id_short):
                mission = briefing
                break
        
        if not mission:
            return CommandResult(False, "⚠️ Mission expired or not found")
        
        # Check if user can trade
        user_rank = self.rank_access.get_user_rank(user_id)
        if user_rank.value < UserRank.AUTHORIZED.value:
            return CommandResult(False, "🔒 Trading requires AUTHORIZED tier")
        
        # Execute trade (simplified)
        trade_params = {
            'symbol': mission.symbol,
            'direction': mission.direction.lower(),
            'entry': mission.entry_price,
            'sl': mission.stop_loss,
            'tp': mission.take_profit,
            'risk': 1.0  # 1% default
        }
        
        response = f"🔫 **FIRING POSITION**\n\n"
        response += f"📍 {mission.symbol} {mission.direction}\n"
        response += f"🎯 Entry: {mission.entry_price:.5f}\n"
        response += f"🛡️ SL: {mission.stop_loss:.5f}\n"
        response += f"💰 TP: {mission.take_profit:.5f}\n\n"
        response += "⚡ Order sent to market!"
        
        return CommandResult(True, response, data={'trade_params': trade_params})
    
    def _handle_share_achievement(self, user_id: int, platform: str, card_id: str) -> CommandResult:
        """Handle achievement sharing"""
        # Get referral link
        referral_link = f"https://t.me/BITTEN_bot?start=ref_{user_id}"
        
        # Generate share content
        share_data = self.social_sharing.generate_share_content(
            card_id, platform, referral_link
        )
        
        # Track share event
        self.social_sharing.track_share_event(user_id, card_id, platform)
        
        return CommandResult(
            True,
            f"✅ Shared on {platform}! +10 XP earned",
            data={'share_data': share_data}
        )
