# telegram_router.py
# BITTEN Telegram Command Processing Engine

import json
import time
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

from .rank_access import RankAccess, UserRank, require_user, require_authorized, require_elite, require_admin
from .user_profile import UserProfileManager
from .mission_briefing_generator import MissionBriefingGenerator, MissionBriefing
from .social_sharing import SocialSharingManager
from .emergency_stop_controller import EmergencyStopController, EmergencyStopTrigger, EmergencyStopLevel
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
        self.emergency_controller = EmergencyStopController()
        
        # Command categories for help system
        self.command_categories = {
            'System': ['start', 'help', 'intel', 'status', 'me'],
            'Trading Info': ['positions', 'balance', 'history', 'performance', 'news'],
            'Trading Commands': ['fire', 'close', 'mode'],
            'Uncertainty Control': ['uncertainty', 'bitmode', 'yes', 'no', 'control', 'stealth', 'gemini', 'chaos'],
            'Configuration': ['risk', 'maxpos', 'notify'],
            'Elite Features': ['tactical', 'tcs', 'signals', 'closeall', 'backtest'],
            'Emergency Stop': ['emergency_stop', 'panic', 'halt_all', 'recover', 'emergency_status'],
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
        elif command == '/news':
            return self._cmd_news(update.user_id, args)
        
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
        
        # Uncertainty & Control Commands
        elif command == '/bitmode':
            return self._cmd_bitmode(update.user_id, args)
        elif command == '/yes':
            return self._cmd_yes(update.user_id, args)
        elif command == '/no':
            return self._cmd_no(update.user_id, args)
        elif command == '/control':
            return self._cmd_control(update.user_id, args)
        elif command == '/stealth':
            return self._cmd_stealth(update.user_id, args)
        elif command == '/gemini':
            return self._cmd_gemini(update.user_id, args)
        elif command == '/chaos':
            return self._cmd_chaos(update.user_id, args)
        elif command == '/uncertainty':
            return self._cmd_uncertainty_status(update.user_id)
        
        # Emergency Stop Commands
        elif command == '/emergency_stop':
            return self._cmd_emergency_stop(update.user_id, args)
        elif command == '/panic':
            return self._cmd_panic(update.user_id, args)
        elif command == '/halt_all':
            return self._cmd_halt_all(update.user_id, args)
        elif command == '/recover':
            return self._cmd_recover(update.user_id, args)
        elif command == '/emergency_status':
            return self._cmd_emergency_status(update.user_id)
        
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
        
        # Intel Command Center
        elif command == '/intel':
            return self._cmd_intel(update.user_id)
        
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
• `/intel` - Intel Command Center (Everything you need)
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
• `/intel` - Intel Command Center (Everything you need)
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
        msg += "💡 **TIP**: Use `/intel` for comprehensive help center\n\n"
        
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
        
        # Get risk status
        from .risk_controller import get_risk_controller, TierLevel
        risk_controller = get_risk_controller()
        
        # Map rank to tier
        tier_map = {
            'USER': TierLevel.NIBBLER,
            'AUTHORIZED': TierLevel.NIBBLER,
            'ELITE': TierLevel.FANG,
            'ADMIN': TierLevel.APEX
        }
        tier = tier_map.get(user_rank.name, TierLevel.NIBBLER)
        risk_status = risk_controller.get_user_status(user_id, tier, 10000)  # Dummy balance
        
        # Get emergency stop status
        emergency_status = self.emergency_controller.get_emergency_status()
        
        # Build profile message
        profile_msg = f"""👤 **OPERATIVE PROFILE**

**Rank:** {profile['rank']} | **XP:** {profile['total_xp']:,}/{profile['next_rank_xp']:,}
**Missions:** {profile['missions_completed']} | **Success Rate:** {profile['success_rate']}%

⚙️ **Risk Mode:** {risk_status['risk_mode']} ({risk_status['current_risk_percent']}%)
📊 **Daily:** {risk_status['daily_trades']}/{risk_status['max_daily_trades']} trades | -{risk_status['daily_drawdown_percent']:.1f}% drawdown"""

        # Add emergency status if active
        if emergency_status['is_active']:
            current_event = emergency_status.get('current_event', {})
            trigger = current_event.get('trigger', 'unknown')
            level = current_event.get('level', 'unknown')
            profile_msg += f"""

🚨 **EMERGENCY STATUS:** ACTIVE
🔴 **Level:** {level.upper()}
🔴 **Trigger:** {trigger.upper()}
🔴 **Events Today:** {emergency_status.get('events_today', 0)}"""
        else:
            profile_msg += f"""

✅ **System Status:** OPERATIONAL"""

        profile_msg += f"""

💰 **Combat Stats:**
• Total Profit: ${profile['total_profit']:,.2f}
• Largest Victory: ${profile['largest_win']:,.2f}
• Current Streak: {profile['current_streak']} | Best: {profile['best_streak']}

🎖️ **Medals:** {profile['medals_earned']}/{profile['medals_total']}
👥 **Recruits:** {profile['recruits_count']} | **Recruit XP:** {profile['recruit_xp']}

🔗 **Your Recruitment Link:**
`https://t.me/BITTEN_bot?start=ref_{user_id}`

*Operative since {profile['joined_days_ago']} days ago*"""
        
        # Add cooldown warning if active
        if risk_status['cooldown']:
            profile_msg = "🚫 **COOLDOWN ACTIVE**\n" + profile_msg
        
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
            [InlineKeyboardButton(
                "🔍 INTEL CENTER", 
                web_app=WebAppInfo(
                    url=f"{self.hud_webapp_url}/intel"
                )
            )]
        ]
        
        # Add emergency controls if active
        if emergency_status['is_active']:
            keyboard.append([
                InlineKeyboardButton("🚨 EMERGENCY STATUS", callback_data="emergency_status"),
                InlineKeyboardButton("🔄 RECOVER", callback_data=f"recover_{user_id}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("🛑 EMERGENCY STOP", callback_data=f"emergency_stop_{user_id}")
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("📤 SHARE LINK", callback_data="share_recruit_link"),
                InlineKeyboardButton("🎖️ MEDALS", callback_data="view_medals")
            ],
            [
                InlineKeyboardButton(
                    "⚙️ SETTINGS", 
                    web_app=WebAppInfo(
                        url=f"{self.hud_webapp_url}/settings.html"
                    )
                )
            ]
        ])
        
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
    
    @require_authorized()
    def _cmd_news(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /news command - Show upcoming economic events"""
        try:
            # Access news scheduler through bitten_core's webhook server reference
            if not hasattr(self.bitten_core, 'webhook_server') or not hasattr(self.bitten_core.webhook_server, 'news_scheduler'):
                return CommandResult(False, "⚠️ News service not available")
            
            news_scheduler = self.bitten_core.webhook_server.news_scheduler
            
            # Get scheduler status
            status = news_scheduler.get_status()
            
            # Check if in blackout
            is_blackout, current_event = news_scheduler.news_client.is_news_blackout_period()
            
            # Get upcoming events (next 24 hours by default)
            hours = 24
            if args and args[0].isdigit():
                hours = min(int(args[0]), 72)  # Max 72 hours
            
            events = news_scheduler.get_upcoming_events(hours=hours)
            
            # Build response message
            msg = "📰 **Economic Calendar**\n"
            msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
            
            # Show blackout status
            if is_blackout and current_event:
                msg += "🚫 **TRADING PAUSED**\n"
                msg += f"High impact news: {current_event.event_name}\n"
                msg += f"Currency: {current_event.currency}\n"
                msg += f"Resume after: {current_event.event_time.strftime('%H:%M UTC')}\n\n"
            
            # Show upcoming events
            if events:
                msg += f"📅 **Upcoming Events ({hours}h)**:\n\n"
                
                for event in events[:10]:  # Limit to 10 events
                    # Format time
                    time_str = event.event_time.strftime('%d %b %H:%M UTC')
                    
                    # Impact emoji
                    impact_emoji = "🔴" if event.impact.value == "high" else "🟡"
                    
                    msg += f"{impact_emoji} **{time_str}**\n"
                    msg += f"   {event.currency} - {event.event_name}\n"
                    
                    if event.forecast:
                        msg += f"   Forecast: {event.forecast}"
                        if event.previous:
                            msg += f" | Prev: {event.previous}"
                        msg += "\n"
                    msg += "\n"
                
                if len(events) > 10:
                    msg += f"_... and {len(events) - 10} more events_\n"
            else:
                msg += "ℹ️ No high/medium impact events scheduled\n"
            
            # Show last update time
            if status['last_update']:
                from datetime import datetime
                last_update = datetime.fromisoformat(status['last_update'])
                mins_ago = int((datetime.now(timezone.utc) - last_update).total_seconds() / 60)
                msg += f"\n_Last updated: {mins_ago} min ago_"
            
            return CommandResult(True, msg)
            
        except Exception as e:
            self._log_error(f"Error in news command: {e}")
            return CommandResult(False, "❌ Error fetching news data")
    
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
    
    # Configuration Commands
    @require_authorized()
    def _cmd_risk(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /risk command - Toggle risk mode with double confirmation"""
        from .risk_controller import get_risk_controller, RiskMode as RiskControlMode, TierLevel
        
        # Get user's tier (would come from profile in real implementation)
        # For now, assume from rank
        user_rank = self.rank_access.get_user_rank(user_id)
        tier_map = {
            'USER': TierLevel.NIBBLER,
            'AUTHORIZED': TierLevel.NIBBLER,
            'ELITE': TierLevel.FANG,
            'ADMIN': TierLevel.APEX
        }
        tier = tier_map.get(user_rank.name, TierLevel.NIBBLER)
        
        risk_controller = get_risk_controller()
        
        # Get current status
        status = risk_controller.get_user_status(user_id, tier, 10000)  # Dummy balance
        
        if not args:
            # Show current risk mode
            msg = f"⚙️ **Risk Configuration**\n\n"
            msg += f"**Current Mode**: {status['risk_mode']}\n"
            msg += f"**Risk Per Trade**: {status['current_risk_percent']}%\n"
            msg += f"**Daily Trades**: {status['daily_trades']}/{status['max_daily_trades']}\n"
            msg += f"**Daily Drawdown**: {status['daily_drawdown_percent']:.1f}%/{status['drawdown_limit']}%\n"
            
            if status['cooldown']:
                msg += f"\n🚫 **COOLDOWN ACTIVE**\n"
                msg += f"Expires: {status['cooldown']['expires_at']}\n"
                msg += f"Reason: {status['cooldown']['reason']}\n"
            
            msg += f"\n**Available Modes**:\n"
            if tier == TierLevel.NIBBLER:
                msg += "• `default` - 1.0% risk\n"
                msg += "• `boost` - 1.5% risk\n"
            else:
                msg += "• `default` - 1.25% risk\n"
                msg += "• `high` - 2.0% risk\n"
            
            msg += f"\nUsage: `/risk [mode]`"
            return CommandResult(True, msg)
        
        # Parse desired mode
        mode_str = args[0].lower()
        mode_map = {
            'default': RiskControlMode.DEFAULT,
            'boost': RiskControlMode.BOOST,
            'high': RiskControlMode.HIGH_RISK,
            'high-risk': RiskControlMode.HIGH_RISK,
            'high_risk': RiskControlMode.HIGH_RISK
        }
        
        if mode_str not in mode_map:
            return CommandResult(False, "❌ Invalid mode. Use: default, boost, or high")
        
        new_mode = mode_map[mode_str]
        
        # First confirmation - show warning
        if len(args) == 1:
            if new_mode in [RiskControlMode.BOOST, RiskControlMode.HIGH_RISK]:
                msg = "⚠️ **RISK MODE WARNING**\n\n"
                msg += "**Higher risk = Higher potential gains AND losses**\n\n"
                
                if new_mode == RiskControlMode.BOOST:
                    msg += "🔸 **BOOST MODE (1.5%)**\n"
                    msg += "• 50% more risk per trade\n"
                    msg += "• Recommended: $5,000+ accounts\n"
                else:
                    msg += "🔴 **HIGH-RISK MODE (2.0%)**\n"
                    msg += "• DOUBLE the standard risk\n"
                    msg += "• Recommended: $10,000+ accounts\n"
                
                msg += "\n**Cooldown Warning**:\n"
                msg += "• 2 consecutive losses = FORCED COOLDOWN\n"
                msg += f"• Cooldown duration: {4 if tier != TierLevel.NIBBLER else 6} hours\n"
                msg += "• During cooldown: 1.0% risk only\n"
                
                msg += f"\n**Confirm with**: `/risk {mode_str} confirm`"
                
                return CommandResult(True, msg)
        
        # Second confirmation - execute change
        if len(args) >= 2 and args[1] == 'confirm':
            success, message = risk_controller.toggle_risk_mode(user_id, tier, new_mode)
            
            if success:
                # Add visual confirmation
                emoji = "✅" if new_mode == RiskControlMode.DEFAULT else "⚡"
                msg = f"{emoji} **Risk Mode Updated**\n\n"
                msg += message
                msg += "\n\n_Remember: Discipline beats luck every time._"
            else:
                msg = f"❌ {message}"
            
            return CommandResult(success, msg)
        
        return CommandResult(False, "❌ Invalid command format")
    
    @require_elite()
    def _cmd_maxpos(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /maxpos command"""
        # Placeholder - would set max positions
        return CommandResult(False, "⚠️ Command not yet implemented")
    
    @require_authorized()
    def _cmd_notify(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /notify command"""
        # Placeholder - would set notification preferences
        return CommandResult(False, "⚠️ Command not yet implemented")
    
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
    
    # Intel Command Center
    @require_user()
    def _cmd_intel(self, user_id: int) -> CommandResult:
        """Handle /intel command - Comprehensive help system"""
        from .intel_command_center import handle_intel_command
        user_rank = self.rank_access.get_user_rank(user_id)
        return handle_intel_command(user_id, user_rank)
    
    def _get_command_description(self, command: str) -> str:
        """Get command description"""
        descriptions = {
            'start': 'Initialize bot session',
            'help': 'Show available commands',
            'intel': 'Intel Command Center - Everything you need',
            'status': 'System health check',
            'me': 'Your profile & stats',
            'positions': 'View open positions',
            'balance': 'Account balance',
            'history': 'Trading history',
            'performance': 'Performance metrics',
            'fire': 'Execute trade',
            'close': 'Close position',
            'mode': 'Switch trading mode',
            'uncertainty': 'View control mode status',
            'bitmode': 'Binary YES/NO confirmation system',
            'yes': 'Confirm YES for bit mode decision',
            'no': 'Confirm NO for bit mode decision',
            'control': 'Full control mode',
            'stealth': 'Hidden algorithm variations',
            'gemini': 'AI competitor tension mode',
            'chaos': 'Maximum uncertainty injection',
            'risk': 'Set risk parameters',
            'maxpos': 'Max positions limit',
            'notify': 'Notification settings',
            'tactical': 'Tactical mode',
            'tcs': 'Trade confidence score',
            'signals': 'Market signals',
            'closeall': 'Close all positions',
            'backtest': 'Strategy backtest',
            'emergency_stop': 'Emergency halt trading',
            'panic': 'Immediate emergency stop',
            'halt_all': 'Halt all system operations',
            'recover': 'Resume from emergency stop',
            'emergency_status': 'Check emergency status',
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
        
        # Handle Intel Command Center callbacks
        if data.startswith('menu_'):
            from .intel_command_center import handle_intel_callback
            user_rank = self.rank_access.get_user_rank(user_id)
            result = handle_intel_callback(data, user_id, user_rank)
            
            # Convert result to CommandResult
            if result.get('action') == 'edit_message':
                return CommandResult(
                    True,
                    result.get('text', ''),
                    data={'reply_markup': result.get('reply_markup')}
                )
            elif result.get('action') == 'answer_callback':
                return CommandResult(
                    True,
                    result.get('text', ''),
                    data={'callback_answer': True, 'show_alert': result.get('show_alert', False)}
                )
            elif result.get('action') == 'delete_message':
                return CommandResult(
                    True,
                    'Menu closed',
                    data={'delete_message': True}
                )
            elif result.get('action') == 'send_message':
                return CommandResult(
                    True,
                    result.get('text', ''),
                    data=result.get('data', {})
                )
        
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
    
    # Emergency Stop Commands
    @require_authorized()
    def _cmd_emergency_stop(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /emergency_stop command - Soft emergency stop"""
        try:
            # Validate and sanitize input
            reason = self._sanitize_emergency_reason(args) if args else "Manual emergency stop"
            
            # Check emergency permissions
            if not self._check_emergency_permissions(user_id, 'emergency_stop'):
                return CommandResult(False, "❌ Insufficient permissions for emergency stop")
            
            # Check if already active
            if self.emergency_controller.is_active():
                status = self.emergency_controller.get_emergency_status()
                current_event = status.get('current_event', {})
                return CommandResult(
                    False,
                    f"🚨 **Emergency stop already active**\n"
                    f"Trigger: {current_event.get('trigger', 'unknown')}\n"
                    f"Started: {current_event.get('timestamp', 'unknown')}\n"
                    f"Use /recover to restore trading"
                )
            
            # Inject components if bitten_core is available
            if self.bitten_core:
                components = {}
                if hasattr(self.bitten_core, 'fire_validator'):
                    components['fire_validator'] = self.bitten_core.fire_validator
                if hasattr(self.bitten_core, 'selector_switch'):
                    components['selector_switch'] = self.bitten_core.selector_switch
                if hasattr(self.bitten_core, 'position_manager'):
                    components['position_manager'] = self.bitten_core.position_manager
                if hasattr(self.bitten_core, 'trade_manager'):
                    components['trade_manager'] = self.bitten_core.trade_manager
                if hasattr(self.bitten_core, 'risk_controller'):
                    components['risk_controller'] = self.bitten_core.risk_controller
                if hasattr(self.bitten_core, 'mt5_bridge'):
                    components['mt5_bridge'] = self.bitten_core.mt5_bridge
                
                self.emergency_controller.inject_components(**components)
            
            # Trigger emergency stop
            result = self.emergency_controller.trigger_emergency_stop(
                trigger=EmergencyStopTrigger.MANUAL,
                level=EmergencyStopLevel.SOFT,
                user_id=user_id,
                reason=reason
            )
            
            if result['success']:
                # Create response with inline keyboard
                keyboard = [
                    [InlineKeyboardButton("🔄 RECOVER", callback_data=f"recover_{user_id}")],
                    [InlineKeyboardButton("📊 STATUS", callback_data="emergency_status")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                return CommandResult(
                    True,
                    f"🛑 **EMERGENCY STOP ACTIVATED**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔸 **Level**: SOFT (No new trades)\n"
                    f"🔸 **Reason**: {reason}\n"
                    f"🔸 **Time**: {datetime.now().strftime('%H:%M:%S UTC')}\n"
                    f"🔸 **User**: {user_id}\n\n"
                    f"⚠️ All new trading stopped\n"
                    f"📱 Use /recover to restore trading\n"
                    f"📊 Use /emergency_status for details",
                    data={'reply_markup': reply_markup}
                )
            else:
                return CommandResult(False, f"❌ Emergency stop failed: {result['message']}")
                
        except Exception as e:
            return CommandResult(False, f"❌ Emergency stop error: {str(e)}")
    
    @require_authorized()
    def _cmd_panic(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /panic command - Hard emergency stop with position closure"""
        try:
            # Validate and sanitize input
            reason = self._sanitize_emergency_reason(args) if args else "PANIC - Hard emergency stop"
            
            # Check emergency permissions and rate limits
            if not self._check_emergency_permissions(user_id, 'panic'):
                return CommandResult(False, "❌ Insufficient permissions for panic mode")
            
            if not self._check_emergency_rate_limit(user_id, 'panic'):
                return CommandResult(False, "❌ Panic command rate limit exceeded")
            
            # Check if already active
            if self.emergency_controller.is_active():
                # Escalate to PANIC level if not already
                current_event = self.emergency_controller.get_current_event()
                if current_event and current_event.get('level') != 'panic':
                    result = self.emergency_controller.trigger_emergency_stop(
                        trigger=EmergencyStopTrigger.PANIC,
                        level=EmergencyStopLevel.PANIC,
                        user_id=user_id,
                        reason=f"ESCALATED TO PANIC: {reason}"
                    )
                    return CommandResult(
                        True,
                        f"🚨 **ESCALATED TO PANIC MODE**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🔴 **All positions being closed**\n"
                        f"🔴 **All trading halted**\n"
                        f"🔴 **Manual recovery required**\n"
                        f"⚠️ Use /recover when ready to resume"
                    )
                else:
                    return CommandResult(
                        False,
                        f"🚨 **PANIC already active**\n"
                        f"Use /recover to restore trading"
                    )
            
            # Inject components
            if self.bitten_core:
                components = {}
                if hasattr(self.bitten_core, 'fire_validator'):
                    components['fire_validator'] = self.bitten_core.fire_validator
                if hasattr(self.bitten_core, 'selector_switch'):
                    components['selector_switch'] = self.bitten_core.selector_switch
                if hasattr(self.bitten_core, 'position_manager'):
                    components['position_manager'] = self.bitten_core.position_manager
                if hasattr(self.bitten_core, 'trade_manager'):
                    components['trade_manager'] = self.bitten_core.trade_manager
                if hasattr(self.bitten_core, 'risk_controller'):
                    components['risk_controller'] = self.bitten_core.risk_controller
                if hasattr(self.bitten_core, 'mt5_bridge'):
                    components['mt5_bridge'] = self.bitten_core.mt5_bridge
                
                self.emergency_controller.inject_components(**components)
            
            # Trigger PANIC emergency stop
            result = self.emergency_controller.trigger_emergency_stop(
                trigger=EmergencyStopTrigger.PANIC,
                level=EmergencyStopLevel.PANIC,
                user_id=user_id,
                reason=reason
            )
            
            if result['success']:
                return CommandResult(
                    True,
                    f"🚨 **PANIC MODE ACTIVATED**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔴 **Level**: PANIC (Hard stop)\n"
                    f"🔴 **Reason**: {reason}\n"
                    f"🔴 **Time**: {datetime.now().strftime('%H:%M:%S UTC')}\n"
                    f"🔴 **User**: {user_id}\n\n"
                    f"⚠️ All trading stopped\n"
                    f"⚠️ Positions being closed\n"
                    f"⚠️ Manual recovery required\n"
                    f"📱 Use /recover when ready"
                )
            else:
                return CommandResult(False, f"❌ PANIC failed: {result['message']}")
                
        except Exception as e:
            return CommandResult(False, f"❌ PANIC error: {str(e)}")
    
    @require_elite()
    def _cmd_halt_all(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /halt_all command - System-wide emergency halt (Elite+ only)"""
        try:
            reason = " ".join(args) if args else "System-wide emergency halt"
            
            # Inject components
            if self.bitten_core:
                components = {}
                if hasattr(self.bitten_core, 'fire_validator'):
                    components['fire_validator'] = self.bitten_core.fire_validator
                if hasattr(self.bitten_core, 'selector_switch'):
                    components['selector_switch'] = self.bitten_core.selector_switch
                if hasattr(self.bitten_core, 'position_manager'):
                    components['position_manager'] = self.bitten_core.position_manager
                if hasattr(self.bitten_core, 'trade_manager'):
                    components['trade_manager'] = self.bitten_core.trade_manager
                if hasattr(self.bitten_core, 'risk_controller'):
                    components['risk_controller'] = self.bitten_core.risk_controller
                if hasattr(self.bitten_core, 'mt5_bridge'):
                    components['mt5_bridge'] = self.bitten_core.mt5_bridge
                
                self.emergency_controller.inject_components(**components)
            
            # Trigger system-wide halt
            result = self.emergency_controller.trigger_emergency_stop(
                trigger=EmergencyStopTrigger.ADMIN_OVERRIDE,
                level=EmergencyStopLevel.HARD,
                user_id=user_id,
                reason=reason
            )
            
            if result['success']:
                return CommandResult(
                    True,
                    f"🚨 **SYSTEM-WIDE HALT ACTIVATED**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔴 **Level**: SYSTEM HALT\n"
                    f"🔴 **Authorized by**: Elite User {user_id}\n"
                    f"🔴 **Reason**: {reason}\n"
                    f"🔴 **Time**: {datetime.now().strftime('%H:%M:%S UTC')}\n\n"
                    f"⚠️ All trading suspended\n"
                    f"⚠️ All users affected\n"
                    f"⚠️ Manual recovery required\n"
                    f"📱 Use /recover to restore system"
                )
            else:
                return CommandResult(False, f"❌ System halt failed: {result['message']}")
                
        except Exception as e:
            return CommandResult(False, f"❌ System halt error: {str(e)}")
    
    @require_authorized()
    def _cmd_recover(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /recover command - Recover from emergency stop"""
        try:
            force_recovery = 'force' in args
            
            # Check if emergency stop is active
            if not self.emergency_controller.is_active():
                return CommandResult(
                    False,
                    f"✅ **No emergency stop active**\n"
                    f"Trading system is operational"
                )
            
            # Check recovery permissions
            current_event = self.emergency_controller.get_current_event()
            if current_event:
                # Admin override and manual triggers require elevated permissions
                if current_event.get('trigger') in ['admin_override', 'panic']:
                    user_rank = self.rank_access.get_user_rank(user_id)
                    if user_rank.value < UserRank.ELITE.value:
                        return CommandResult(
                            False,
                            f"❌ **Recovery requires ELITE+ rank**\n"
                            f"Current emergency: {current_event.get('trigger')}\n"
                            f"Your rank: {user_rank.name}"
                        )
            
            # Attempt recovery
            result = self.emergency_controller.recover_from_emergency(
                user_id=user_id,
                force=force_recovery
            )
            
            if result['success']:
                recovery_time = result.get('recovery_time', datetime.now())
                return CommandResult(
                    True,
                    f"✅ **EMERGENCY RECOVERY COMPLETED**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🟢 **Status**: Trading restored\n"
                    f"🟢 **Recovery time**: {recovery_time.strftime('%H:%M:%S UTC') if hasattr(recovery_time, 'strftime') else recovery_time}\n"
                    f"🟢 **Recovered by**: User {user_id}\n\n"
                    f"✅ All systems operational\n"
                    f"✅ Trading resumed\n"
                    f"📊 Use /status for system health"
                )
            else:
                # Handle auto-recovery timing
                if 'recovery_time' in result:
                    recovery_time = result['recovery_time']
                    return CommandResult(
                        False,
                        f"⏰ **Auto-recovery not ready**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🔸 **Recovery available at**: {recovery_time.strftime('%H:%M:%S UTC')}\n"
                        f"🔸 **Current time**: {datetime.now().strftime('%H:%M:%S UTC')}\n\n"
                        f"⚠️ Use `/recover force` to override\n"
                        f"⚠️ Or wait for auto-recovery"
                    )
                else:
                    return CommandResult(False, f"❌ Recovery failed: {result['message']}")
                    
        except Exception as e:
            return CommandResult(False, f"❌ Recovery error: {str(e)}")
    
    @require_authorized()
    def _cmd_emergency_status(self, user_id: int) -> CommandResult:
        """Handle /emergency_status command - Show emergency stop status"""
        try:
            status = self.emergency_controller.get_emergency_status()
            
            if not status['is_active']:
                return CommandResult(
                    True,
                    f"✅ **Emergency Status: OPERATIONAL**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🟢 **Status**: No emergency active\n"
                    f"🟢 **Trading**: Enabled\n"
                    f"🟢 **Last check**: {datetime.now().strftime('%H:%M:%S UTC')}\n\n"
                    f"📊 **Today's events**: {status.get('events_today', 0)}\n"
                    f"📊 **Last recovery**: {status.get('last_recovery', 'Never')}\n"
                    f"📊 **System health**: {status.get('system_health', {}).get('overall_status', 'Unknown')}"
                )
            
            # Emergency is active - show details
            current_event = status.get('current_event', {})
            active_triggers = status.get('active_triggers', [])
            affected_users = status.get('affected_users', [])
            
            msg = f"🚨 **Emergency Status: ACTIVE**\n"
            msg += f"━━━━━━━━━━━━━━━━━━━━\n"
            msg += f"🔴 **Level**: {current_event.get('level', 'unknown').upper()}\n"
            msg += f"🔴 **Trigger**: {current_event.get('trigger', 'unknown')}\n"
            msg += f"🔴 **Started**: {current_event.get('timestamp', 'unknown')}\n"
            msg += f"🔴 **Reason**: {current_event.get('reason', 'No reason provided')}\n"
            
            if current_event.get('user_id'):
                msg += f"🔴 **Initiated by**: User {current_event['user_id']}\n"
            
            msg += f"\n📊 **Active triggers**: {', '.join(active_triggers)}\n"
            msg += f"📊 **Affected users**: {len(affected_users)}\n"
            msg += f"📊 **Events today**: {status.get('events_today', 0)}\n"
            
            # Recovery information
            recovery_time = current_event.get('recovery_time')
            if recovery_time:
                msg += f"⏰ **Auto-recovery**: {recovery_time}\n"
            else:
                msg += f"⏰ **Auto-recovery**: Manual only\n"
            
            # System health
            health = status.get('system_health', {})
            msg += f"🔧 **System health**: {health.get('overall_status', 'Unknown')}\n"
            
            # Create inline keyboard
            keyboard = [
                [InlineKeyboardButton("🔄 RECOVER", callback_data=f"recover_{user_id}")],
                [InlineKeyboardButton("📊 REFRESH", callback_data="emergency_status")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            return CommandResult(
                True,
                msg,
                data={'reply_markup': reply_markup}
            )
            
        except Exception as e:
            return CommandResult(False, f"❌ Status error: {str(e)}")
    
    # Security helper methods
    def _sanitize_emergency_reason(self, args: List[str]) -> str:
        """Sanitize emergency reason input"""
        if not args or not isinstance(args, list):
            return "Manual emergency stop"
        
        # Join args and sanitize
        reason = " ".join(str(arg) for arg in args)
        
        # Remove potentially dangerous characters
        import re
        reason = re.sub(r'[<>"\'{}\[\]\\]', '', reason)
        
        # Limit length
        reason = reason[:500]
        
        # Ensure non-empty
        return reason if reason.strip() else "Manual emergency stop"
    
    def _check_emergency_permissions(self, user_id: int, command: str) -> bool:
        """Check if user has permission for emergency command"""
        user_rank = self.rank_access.get_user_rank(user_id)
        
        # Define required ranks for emergency commands
        emergency_permissions = {
            'emergency_stop': ['AUTHORIZED', 'ELITE', 'ADMIN'],
            'panic': ['AUTHORIZED', 'ELITE', 'ADMIN'],
            'halt_all': ['ELITE', 'ADMIN'],
            'recover': ['AUTHORIZED', 'ELITE', 'ADMIN'],
            'emergency_status': ['USER', 'AUTHORIZED', 'ELITE', 'ADMIN']
        }
        
        allowed_ranks = emergency_permissions.get(command, ['ADMIN'])
        return user_rank.name in allowed_ranks
    
    def _check_emergency_rate_limit(self, user_id: int, command: str) -> bool:
        """Check rate limit for emergency commands"""
        # Basic implementation - should be enhanced with proper rate limiting
        current_time = time.time()
        
        # Check if user has made emergency command recently
        if hasattr(self, '_emergency_calls'):
            user_calls = self._emergency_calls.get(user_id, [])
            # Remove calls older than 5 minutes
            user_calls = [t for t in user_calls if current_time - t < 300]
            
            # Check limits based on command
            limits = {
                'emergency_stop': 5,
                'panic': 2,
                'halt_all': 1,
                'recover': 10
            }
            
            if len(user_calls) >= limits.get(command, 3):
                return False
            
            # Add current call
            user_calls.append(current_time)
            self._emergency_calls[user_id] = user_calls
        else:
            self._emergency_calls = {user_id: [current_time]}
        
        return True
    
    # ========================================
    # UNCERTAINTY & CONTROL INTERPLAY COMMANDS
    # ========================================
    
    def _cmd_bitmode(self, user_id: int, args: List[str]) -> CommandResult:
        """Toggle Bit Mode - binary YES/NO confirmation system"""
        try:
            if not hasattr(self.bitten_core, 'fire_router'):
                return CommandResult(False, "❌ Fire router not available")
            
            if not args:
                # Toggle bit mode
                result = self.bitten_core.fire_router.set_uncertainty_mode(user_id, 'bit_mode')
                return CommandResult(result['success'], result['message'])
            elif args[0].lower() == 'off':
                # Turn off bit mode
                result = self.bitten_core.fire_router.set_uncertainty_mode(user_id, 'full_control')
                return CommandResult(result['success'], result['message'])
            else:
                return CommandResult(False, "❌ Usage: /bitmode [off]")
                
        except Exception as e:
            return CommandResult(False, f"❌ Bit mode error: {str(e)}")
    
    def _cmd_yes(self, user_id: int, args: List[str]) -> CommandResult:
        """Confirm YES for bit mode decision"""
        try:
            if not args:
                return CommandResult(False, "❌ Usage: /yes <decision_id>")
            
            decision_id = args[0]
            
            if not hasattr(self.bitten_core, 'fire_router'):
                return CommandResult(False, "❌ Fire router not available")
            
            result = self.bitten_core.fire_router.process_bit_mode_confirmation(decision_id, True, user_id)
            return CommandResult(result.success, result.message)
            
        except Exception as e:
            return CommandResult(False, f"❌ Confirmation error: {str(e)}")
    
    def _cmd_no(self, user_id: int, args: List[str]) -> CommandResult:
        """Confirm NO for bit mode decision"""
        try:
            if not args:
                return CommandResult(False, "❌ Usage: /no <decision_id>")
            
            decision_id = args[0]
            
            if not hasattr(self.bitten_core, 'fire_router'):
                return CommandResult(False, "❌ Fire router not available")
            
            result = self.bitten_core.fire_router.process_bit_mode_confirmation(decision_id, False, user_id)
            return CommandResult(result.success, result.message)
            
        except Exception as e:
            return CommandResult(False, f"❌ Confirmation error: {str(e)}")
    
    def _cmd_control(self, user_id: int, args: List[str]) -> CommandResult:
        """Set full control mode"""
        try:
            if not hasattr(self.bitten_core, 'fire_router'):
                return CommandResult(False, "❌ Fire router not available")
            
            result = self.bitten_core.fire_router.set_uncertainty_mode(user_id, 'full_control')
            return CommandResult(result['success'], result['message'])
            
        except Exception as e:
            return CommandResult(False, f"❌ Control mode error: {str(e)}")
    
    def _cmd_stealth(self, user_id: int, args: List[str]) -> CommandResult:
        """Activate stealth mode - hidden algorithm variations"""
        try:
            if not hasattr(self.bitten_core, 'fire_router'):
                return CommandResult(False, "❌ Fire router not available")
            
            result = self.bitten_core.fire_router.set_uncertainty_mode(user_id, 'stealth_mode')
            return CommandResult(result['success'], result['message'])
            
        except Exception as e:
            return CommandResult(False, f"❌ Stealth mode error: {str(e)}")
    
    def _cmd_gemini(self, user_id: int, args: List[str]) -> CommandResult:
        """Activate Gemini mode - AI competitor tension"""
        try:
            if not hasattr(self.bitten_core, 'fire_router'):
                return CommandResult(False, "❌ Fire router not available")
            
            result = self.bitten_core.fire_router.set_uncertainty_mode(user_id, 'gemini_mode')
            return CommandResult(result['success'], result['message'])
            
        except Exception as e:
            return CommandResult(False, f"❌ Gemini mode error: {str(e)}")
    
    def _cmd_chaos(self, user_id: int, args: List[str]) -> CommandResult:
        """Activate chaos mode - maximum uncertainty injection"""
        try:
            if not hasattr(self.bitten_core, 'fire_router'):
                return CommandResult(False, "❌ Fire router not available")
            
            result = self.bitten_core.fire_router.set_uncertainty_mode(user_id, 'chaos_mode')
            return CommandResult(result['success'], result['message'])
            
        except Exception as e:
            return CommandResult(False, f"❌ Chaos mode error: {str(e)}")
    
    def _cmd_uncertainty_status(self, user_id: int) -> CommandResult:
        """Get current uncertainty system status"""
        try:
            if not hasattr(self.bitten_core, 'fire_router'):
                return CommandResult(False, "❌ Fire router not available")
            
            result = self.bitten_core.fire_router.get_uncertainty_status(user_id)
            
            # Create inline keyboard with mode options
            keyboard = [
                [
                    InlineKeyboardButton("🎯 FULL CONTROL", callback_data="uncertainty_full_control"),
                    InlineKeyboardButton("🤖 BIT MODE", callback_data="uncertainty_bit_mode")
                ],
                [
                    InlineKeyboardButton("👻 STEALTH", callback_data="uncertainty_stealth_mode"),
                    InlineKeyboardButton("⚡ GEMINI", callback_data="uncertainty_gemini_mode")
                ],
                [
                    InlineKeyboardButton("🌪️ CHAOS", callback_data="uncertainty_chaos_mode"),
                    InlineKeyboardButton("📊 REFRESH", callback_data="uncertainty_status")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            return CommandResult(
                result['success'], 
                result['message'],
                data={'reply_markup': reply_markup}
            )
            
        except Exception as e:
            return CommandResult(False, f"❌ Status error: {str(e)}")
    
    def _get_help_text(self, user_id: int) -> str:
        """Generate help text with uncertainty commands"""
        user_rank = self.rank_access.get_user_rank(user_id)
        
        base_help = f"""🤖 **BITTEN Command Center**

**🎮 UNCERTAINTY & CONTROL**
`/uncertainty` - View control mode status
`/bitmode` - Binary YES/NO confirmation
`/control` - Full control mode
`/stealth` - Hidden algorithm variations
`/gemini` - AI competitor mode  
`/chaos` - Maximum uncertainty

**⚡ TRADING**
`/fire [symbol] [buy/sell] [size]` - Execute trade
`/positions` - View open positions
`/close [trade_id]` - Close position
`/closeall` - Close all positions

**📊 INFORMATION**
`/me` - Your profile
`/status` - System status
`/balance` - Account balance
`/performance` - Trading stats

**🚨 EMERGENCY**
`/emergency_stop` - Emergency halt
`/panic` - Immediate stop
`/recover` - Resume trading

**Your Rank:** {user_rank.name}
"""
        
        return base_help
