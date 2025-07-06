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
from .trade_confirmation_system import TradeConfirmationSystem, create_confirmation_system
from .referral_system import ReferralSystem, ReferralCommandHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from .onboarding import OnboardingOrchestrator
from .trial_manager import get_trial_manager, AccountType, TrialStatus
import asyncio

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
    
    def __init__(self, bitten_core=None, hud_webapp_url="https://your-domain.com/sniper_hud", telegram_bot=None):
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
        
        # Initialize referral system
        self.referral_system = ReferralSystem()
        self.referral_handler = ReferralCommandHandler(self.referral_system)
        
        # Initialize trade confirmation system
        self.telegram_bot = telegram_bot
        self.confirmation_system = create_confirmation_system(self._send_telegram_message)
        
        # Initialize onboarding system
        self.onboarding_orchestrator = OnboardingOrchestrator(
            persona_orchestrator=None,
            hud_webapp_url=self.hud_webapp_url
        )
        
        # Initialize trial system
        self.trial_manager = get_trial_manager(telegram_bot)
        
        # Start confirmation processing
        if telegram_bot:
            asyncio.create_task(self.confirmation_system.start_processing())
        
        # Command categories for help system
        self.command_categories = {
            'System': ['start', 'help', 'intel', 'status', 'me', 'callsign', 'upgrade', 'subscribe', 'golive'],
            'Trading Info': ['positions', 'balance', 'history', 'performance', 'news'],
            'Trading Commands': ['fire', 'close', 'mode'],
            'Uncertainty Control': ['uncertainty', 'bitmode', 'yes', 'no', 'control', 'stealth', 'gemini', 'chaos'],
            'Configuration': ['risk', 'maxpos', 'notify', 'confirmations'],
            'Elite Features': ['tactical', 'tcs', 'signals', 'closeall', 'backtest'],
            'Emergency Stop': ['emergency_stop', 'panic', 'halt_all', 'recover', 'emergency_status'],
            'Education': ['learn', 'missions', 'journal', 'squad', 'achievements', 'study', 'mentor'],
            'Social': ['refer'],
            'Admin Only': ['logs', 'restart', 'backup', 'promote', 'ban']
        }
        
        # Initialize education system components
        self.education_data = {
            'active_missions': {},
            'user_progress': {},
            'squads': {},
            'study_groups': {},
            'mentor_sessions': {},
            'pending_notifications': []
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
            # Check if user is in onboarding flow first
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                session = loop.run_until_complete(
                    self.onboarding_orchestrator.session_manager.load_session(str(update.user_id))
                )
                
                if session and session.current_state.value not in ["complete", "error", None]:
                    # User is in onboarding - process as onboarding input
                    message, keyboard = loop.run_until_complete(
                        self.onboarding_orchestrator.process_user_input(
                            user_id=str(update.user_id),
                            input_type='text',
                            input_data=update.text
                        )
                    )
                    loop.close()
                    
                    if keyboard and 'inline_keyboard' in keyboard:
                        telegram_keyboard = InlineKeyboardMarkup([
                            [InlineKeyboardButton(btn['text'], callback_data=btn['callback_data']) 
                             for btn in row]
                            for row in keyboard['inline_keyboard']
                        ])
                        return CommandResult(True, message, data={'reply_markup': telegram_keyboard})
                    
                    return CommandResult(True, message)
                    
            except Exception as e:
                pass  # Continue to normal command processing
            finally:
                loop.close()
            
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
        elif command == '/callsign':
            return self._cmd_callsign(update.user_id, args)
        elif command == '/upgrade':
            return self._cmd_upgrade(update.user_id)
        elif command == '/subscribe':
            return self._cmd_subscribe(update.user_id)
        elif command == '/golive':
            return self._cmd_golive(update.user_id, args)
        
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
        elif command == '/confirmations':
            return self._cmd_confirmations(update.user_id, args)
        
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
        
        # Education Commands
        elif command == '/learn':
            return self._cmd_learn(update.user_id, update.chat_id)
        elif command == '/missions':
            return self._cmd_missions(update.user_id, args)
        elif command == '/journal':
            return self._cmd_journal(update.user_id, args)
        elif command == '/squad':
            return self._cmd_squad(update.user_id, args)
        elif command == '/achievements':
            return self._cmd_achievements(update.user_id, args)
        elif command == '/study':
            return self._cmd_study(update.user_id, args)
        elif command == '/mentor':
            return self._cmd_mentor(update.user_id, args)
        
        # Social Commands
        elif command == '/refer':
            return self._cmd_refer(update.user_id, update.username, args)
        
        else:
            return CommandResult(False, f"❌ Unknown command: {command}")
    
    # System Commands
    def _cmd_start(self, user_id: int, username: str, args: List[str]) -> CommandResult:
        """Handle /start command with AAA-quality onboarding experience"""
        
        # Check if user exists
        is_new_user = not self.rank_access.get_user_info(user_id)
        
        if is_new_user:
            # Add user to system
            self.rank_access.add_user(user_id, username)
            
            # Handle referral code if provided
            referral_code = None
            if args and args[0]:
                referral_code = args[0]
                # Convert old ref_123 format if needed
                if referral_code.startswith('ref_'):
                    try:
                        referrer_id = referral_code.replace('ref_', '')
                        self.referral_system.generate_referral_code(referrer_id)
                        stats = self.referral_system.get_referral_stats(referrer_id)
                        if stats['referral_code']:
                            referral_code = stats['referral_code']
                    except:
                        pass
            
            # Start 15-day trial FIRST (no payment mention!)
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Start trial
                trial_result = loop.run_until_complete(
                    self.trial_manager.start_trial(user_id, AccountType.DEMO)
                )
                
                if not trial_result.success:
                    loop.close()
                    return trial_result
                
                # Now start onboarding
                message, keyboard = loop.run_until_complete(
                    self.onboarding_orchestrator.start_onboarding(
                        user_id=str(user_id),
                        telegram_id=user_id,
                        variant="standard"
                    )
                )
                
                # Store referral code for later processing
                if referral_code:
                    session = loop.run_until_complete(
                        self.onboarding_orchestrator.session_manager.load_session(str(user_id))
                    )
                    if session:
                        session.state_data['pending_referral'] = referral_code
                        loop.run_until_complete(
                            self.onboarding_orchestrator.session_manager.save_session(session)
                        )
                
                loop.close()
                
                # Convert keyboard to telegram format
                if keyboard and 'inline_keyboard' in keyboard:
                    telegram_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton(btn['text'], callback_data=btn['callback_data']) 
                         for btn in row]
                        for row in keyboard['inline_keyboard']
                    ])
                    return CommandResult(True, message, data={'reply_markup': telegram_keyboard})
                
                return CommandResult(True, message)
                
            except Exception as e:
                # Fallback to simple welcome if onboarding fails
                return self._show_simple_welcome(user_id, username)
        
        else:
            # Existing user - check for active onboarding
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                session = loop.run_until_complete(
                    self.onboarding_orchestrator.session_manager.load_session(str(user_id))
                )
                
                if session and session.current_state.value not in ["complete", "error"]:
                    # Resume onboarding
                    message, keyboard = loop.run_until_complete(
                        self.onboarding_orchestrator.resume_session(session)
                    )
                    loop.close()
                    
                    if keyboard and 'inline_keyboard' in keyboard:
                        telegram_keyboard = InlineKeyboardMarkup([
                            [InlineKeyboardButton(btn['text'], callback_data=btn['callback_data']) 
                             for btn in row]
                            for row in keyboard['inline_keyboard']
                        ])
                        return CommandResult(True, message, data={'reply_markup': telegram_keyboard})
                    
                    return CommandResult(True, message)
                
                loop.close()
                
            except Exception as e:
                pass  # Continue to regular welcome
            
            # Check trial/subscription status for existing users
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                trial_status = loop.run_until_complete(
                    self.trial_manager.check_trial_status(user_id)
                )
                
                # Check if features are locked
                from .database.connection import get_db_session
                from .database.models import User
                
                with get_db_session() as session:
                    user = session.query(User).filter(User.user_id == user_id).first()
                    if user and user.features_locked:
                        # User's trial/subscription expired - show subscription required
                        return self._show_subscription_required(user_id, trial_status)
                
                # Check if we should show payment prompt (day 14-15)
                if trial_status.get('show_payment_prompt', False):
                    return self._show_payment_reminder(user_id, trial_status)
                
            except Exception as e:
                logger.error(f"Error checking trial status: {e}")
            finally:
                loop.close()
            
            # Show regular welcome for active users
            return self._show_regular_welcome(user_id, username)
    
    def _show_simple_welcome(self, user_id: int, username: str) -> CommandResult:
        """Simple fallback welcome message"""
        user_rank = self.rank_access.get_user_rank(user_id)
        welcome_msg = f"""🤖 **Welcome to BITTEN!**

**Bot-Integrated Tactical Trading Engine / Network**

Hello {username}! Your access level: **{user_rank.name}**

*"You've been B.I.T.T.E.N. — now prove you belong."*

🎯 **Quick Commands:**
• `/intel` - Intel Command Center
• `/help` - Command list
• `/me` - Your profile & stats
• `/positions` - View positions (Auth+)
• `/fire` - Execute trade (Auth+)

🔐 **Access Levels:**
👤 USER → 🔑 AUTHORIZED → ⭐ ELITE → 🛡️ ADMIN

Type `/help` for complete command list."""
        
        return CommandResult(True, welcome_msg)
    
    def _show_regular_welcome(self, user_id: int, username: str) -> CommandResult:
        """Welcome message for returning users"""
        user_rank = self.rank_access.get_user_rank(user_id)
        profile = self.profile_manager.get_user_profile(user_id)
        
        # Check if they have a callsign from onboarding
        callsign = profile.get('callsign', username) if profile else username
        
        welcome_msg = f"""🎖️ **Welcome back, {callsign}!**

**B.I.T.T.E.N. Trading Operations Center**

Status: **OPERATIONAL** ✅
Your Rank: **{user_rank.name}**

📊 **Your Stats:**
• Total XP: {profile.get('total_xp', 0) if profile else 0}
• Missions Complete: {profile.get('missions_complete', 0) if profile else 0}
• Win Rate: {profile.get('win_rate', 0) if profile else 0}%

🎯 **Mission Control:**
• `/intel` - Access Intel Command Center
• `/missions` - View active missions
• `/fire` - Execute trades
• `/squad` - Squad management

*"Once bitten, forever committed."*

Type `/help` for all commands."""
        
        return CommandResult(True, welcome_msg)
    
    def _show_subscription_required(self, user_id: int, trial_status: Dict) -> CommandResult:
        """Show subscription required message for expired users"""
        
        days_since_expiry = trial_status.get('days_since_expiry', 0)
        
        if days_since_expiry > 45:
            msg = """🔒 **ACCOUNT RESET REQUIRED**

Your trial expired over 45 days ago. All progress has been reset.

Ready to start fresh?"""
        else:
            msg = f"""🔒 **SUBSCRIPTION REQUIRED**

Your trial has expired. All trading features are locked.

⏰ **Good news!** You have {45 - days_since_expiry} days to subscribe and keep your:
• XP and achievements
• Trading history  
• Squad connections
• All your progress

Ready to continue your journey?"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Subscribe Now", callback_data="expired_subscribe")],
            [InlineKeyboardButton("💰 View Pricing", callback_data="expired_pricing")]
        ])
        
        return CommandResult(True, msg, data={'reply_markup': keyboard})
    
    def _show_payment_reminder(self, user_id: int, trial_status: Dict) -> CommandResult:
        """Show payment reminder for day 14-15 users"""
        
        days_remaining = trial_status.get('days_remaining', 0)
        
        msg = f"""🎖️ **Welcome back, soldier!**

⏰ **Trial Status**: {days_remaining} day{'s' if days_remaining != 1 else ''} remaining

You've been crushing it! Don't lose your momentum.

Ready to lock in your gains with a subscription?"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Subscribe Now", callback_data="trial_subscribe")],
            [InlineKeyboardButton("📊 Compare Plans", callback_data="trial_compare_plans")],
            [InlineKeyboardButton("⏰ Remind Me Later", callback_data="trial_remind_later")]
        ])
        
        return CommandResult(True, msg, data={'reply_markup': keyboard})
    
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
    
    def _cmd_callsign(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /callsign command - Change user's callsign"""
        
        # If no args, show current callsign and instructions
        if not args:
            # Get current callsign
            profile = self.profile_manager.get_user_profile(user_id)
            current_callsign = profile.get('callsign', 'Not Set') if profile else 'Not Set'
            
            help_msg = f"""🎖️ **Callsign Management**

**Current Callsign**: {current_callsign}

To change your callsign:
`/callsign NewCallsign`

**Rules:**
• 3-15 characters
• Letters, numbers, underscores only
• Must be unique
• No special characters

**Examples:**
• `/callsign Eagle007`
• `/callsign RedFox`
• `/callsign Shadow_1`

*Your callsign is your identity in the BITTEN network. Choose wisely, soldier!*"""
            
            return CommandResult(True, help_msg)
        
        # User wants to change callsign
        new_callsign = args[0].strip()
        
        # Validate callsign using the onboarding validators
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Import validator
            from .onboarding.validators import OnboardingValidators
            validators = OnboardingValidators()
            
            # Validate the new callsign
            is_valid, error_msg = loop.run_until_complete(
                validators.validate_callsign(new_callsign)
            )
            
            if not is_valid:
                return CommandResult(False, error_msg)
            
            # Check if callsign is already taken in the database
            from .database.connection import get_db_session
            from .database.models import UserProfile
            
            with get_db_session() as session:
                # Check if callsign exists
                existing = session.query(UserProfile).filter(
                    UserProfile.callsign == new_callsign,
                    UserProfile.user_id != user_id
                ).first()
                
                if existing:
                    return CommandResult(
                        False, 
                        "🚨 **Already Taken**: Another operative has that callsign. Be original!"
                    )
                
                # Update user's callsign
                user_profile = session.query(UserProfile).filter(
                    UserProfile.user_id == user_id
                ).first()
                
                if not user_profile:
                    # Create profile if it doesn't exist
                    user_profile = UserProfile(
                        user_id=user_id,
                        callsign=new_callsign
                    )
                    session.add(user_profile)
                else:
                    old_callsign = user_profile.callsign or "Recruit"
                    user_profile.callsign = new_callsign
                
                session.commit()
                
                # Update in-memory profile cache if exists
                if hasattr(self.profile_manager, '_update_callsign'):
                    self.profile_manager._update_callsign(user_id, new_callsign)
                
                success_msg = f"""✅ **Callsign Updated!**

**New Callsign**: {new_callsign}

Your identity has been updated across the BITTEN network.

*"A new name, a new legend begins."*

Use `/me` to see your updated profile."""
                
                return CommandResult(True, success_msg)
                
        except Exception as e:
            logger.error(f"Error updating callsign: {e}")
            return CommandResult(
                False, 
                "❌ Error updating callsign. Please try again later."
            )
        finally:
            loop.close()
    
    def _cmd_upgrade(self, user_id: int) -> CommandResult:
        """Handle /upgrade command - Tier upgrade/downgrade management"""
        from .upgrade_router import get_upgrade_router
        
        upgrade_router = get_upgrade_router()
        return upgrade_router.get_upgrade_options(user_id)
    
    def _cmd_subscribe(self, user_id: int) -> CommandResult:
        """Handle /subscribe command - Direct subscription access"""
        
        # Check trial status
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            trial_status = loop.run_until_complete(
                self.trial_manager.check_trial_status(user_id)
            )
            
            # Show subscription options
            result = loop.run_until_complete(
                self.trial_manager._show_subscription_options(user_id)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error showing subscription options: {e}")
            return CommandResult(False, "❌ Error loading subscription options")
        finally:
            loop.close()
    
    def _cmd_golive(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /golive command - Switch from demo to live account"""
        
        if not args:
            # Show instructions
            msg = """🔄 **SWITCH TO LIVE TRADING**

Ready to trade with real money? Your progress will be preserved!

**To switch to live:**
`/golive MT5_ACCOUNT MT5_SERVER`

**Example:**
`/golive 12345678 ICMarkets-Live03`

**What transfers:**
• All your XP and levels
• Your trading history
• Squad connections
• All achievements

⚠️ **IMPORTANT**: Live trading involves real money risk!"""
            
            return CommandResult(True, msg)
        
        if len(args) < 2:
            return CommandResult(False, "❌ Please provide both MT5 account and server")
        
        mt5_account = args[0]
        mt5_server = args[1]
        
        # Validate inputs
        if not mt5_account.isdigit():
            return CommandResult(False, "❌ MT5 account must be numeric")
        
        # Process migration
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.trial_manager.migrate_demo_to_live(
                    user_id,
                    {
                        'account': mt5_account,
                        'server': mt5_server
                    }
                )
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error migrating to live: {e}")
            return CommandResult(False, "❌ Migration failed. Please try again.")
        finally:
            loop.close()
    
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
            'confirmations': 'Configure trade confirmations',
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
            'ban': 'Ban user',
            'learn': 'Trading education HQ',
            'missions': 'Daily/weekly objectives',
            'journal': 'Combat journal entry',
            'squad': 'Squad management',
            'achievements': 'Medals & progress',
            'study': 'Join study groups',
            'mentor': 'Find or become mentor',
            'refer': 'Elite recruitment system'
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
        
        # Handle onboarding callbacks FIRST (highest priority)
        if data.startswith('onboarding_'):
            # Process onboarding callback
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Extract the actual callback data
                onboarding_data = data.replace('onboarding_', '')
                
                message, keyboard = loop.run_until_complete(
                    self.onboarding_orchestrator.process_user_input(
                        user_id=str(user_id),
                        input_type='callback',
                        input_data=onboarding_data
                    )
                )
                
                # Check if onboarding is complete
                if 'Welcome to BITTEN, soldier' in message or 'SYSTEMS ONLINE' in message:
                    # Process any pending referral
                    session = loop.run_until_complete(
                        self.onboarding_orchestrator.session_manager.load_session(str(user_id))
                    )
                    
                    if session and session.state_data.get('pending_referral'):
                        referral_code = session.state_data['pending_referral']
                        ip_address = "unknown"  # In production, get from request
                        
                        success, ref_message, result = self.referral_system.use_referral_code(
                            str(user_id), referral_code, 
                            callback_query.get('from', {}).get('username', 'Unknown'),
                            ip_address
                        )
                        
                        if success:
                            message += f"\n\n🎯 **Squad Bonus**: You've joined {result.get('referrer_name', 'Unknown')}'s squad!"
                
                loop.close()
                
                if keyboard and 'inline_keyboard' in keyboard:
                    telegram_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton(btn['text'], callback_data=btn['callback_data']) 
                         for btn in row]
                        for row in keyboard['inline_keyboard']
                    ])
                    return CommandResult(True, message, data={
                        'reply_markup': telegram_keyboard,
                        'edit_message': True
                    })
                
                return CommandResult(True, message, data={'edit_message': True})
                
            except Exception as e:
                loop.close()
                return CommandResult(False, "❌ Onboarding error. Please type /start to continue.")
        
        # Handle Intel Command Center callbacks
        elif data.startswith('menu_'):
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
        
        # Handle Trial/Subscription callbacks
        elif data.startswith('trial_') or data.startswith('expired_') or \
             data.startswith('subscribe_'):
            # Handle trial-related callbacks
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.trial_manager.handle_subscription_callback(user_id, data)
                )
                
                if result.data and result.data.get('reply_markup'):
                    return CommandResult(True, result.message, data={
                        'reply_markup': result.data['reply_markup'],
                        'edit_message': True
                    })
                
                return CommandResult(True, result.message, data={'edit_message': True})
                
            except Exception as e:
                logger.error(f"Error handling trial callback: {e}")
                return CommandResult(False, "❌ Error processing request")
            finally:
                loop.close()
        
        # Handle Upgrade/Subscription callbacks
        elif data.startswith('upgrade_') or data.startswith('downgrade_') or \
             data in ['cancel_subscription', 'reactivate_subscription', 'view_tier_benefits', 
                      'renew_current', 'manage_payment']:
            from .upgrade_router import get_upgrade_router
            upgrade_router = get_upgrade_router()
            return upgrade_router.handle_subscription_callback(user_id, data)
        
        # Handle Education System callbacks
        elif data.startswith('learn_') or data.startswith('missions_') or data.startswith('journal_') or \
             data.startswith('squad_') or data.startswith('achievements_') or data.startswith('study_') or \
             data.startswith('mentor_') or data.startswith('notification_'):
            return self._handle_education_callback(user_id, data)
        
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
    
    async def _send_telegram_message(self, user_id: int, message: str) -> bool:
        """Send message to Telegram user"""
        try:
            if self.telegram_bot:
                await self.telegram_bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                return True
            else:
                # Log message if no bot configured (for testing)
                logger.info(f"[TELEGRAM CONFIRMATION] To user {user_id}: {message}")
                return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message to user {user_id}: {e}")
            return False
    
    @require_authorized()
    def _cmd_confirmations(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /confirmations command - Configure trade confirmations"""
        
        if not args:
            # Show current settings
            prefs = self.confirmation_system.get_user_preferences(user_id)
            
            msg = "⚙️ **Trade Confirmation Settings**\n\n"
            
            # General settings
            status = "✅ Enabled" if prefs['confirmations_enabled'] else "❌ Disabled"
            msg += f"🔔 **Confirmations**: {status}\n"
            
            if prefs['min_pnl_threshold'] > 0:
                msg += f"💰 **Min P&L Threshold**: ${prefs['min_pnl_threshold']:.2f}\n"
            
            msg += "\n📊 **Notification Types**:\n"
            
            # List each notification type
            notification_types = [
                ('trade_opened', 'Trade Opened', '🔫'),
                ('trade_closed', 'Trade Closed', '🎯'),
                ('stop_loss_hit', 'Stop Loss Hit', '❌'),
                ('take_profit_hit', 'Take Profit Hit', '💰'),
                ('partial_close', 'Partial Close', '⚡'),
                ('trailing_stop_moved', 'Trailing Stop', '📈'),
                ('breakeven_moved', 'Breakeven', '🛡️'),
                ('emergency_close', 'Emergency Close', '🚨'),
                ('connection_lost', 'Connection Issues', '🔌')
            ]
            
            for type_key, display_name, emoji in notification_types:
                enabled = prefs.get(f"{type_key}_enabled", True)
                status_emoji = "✅" if enabled else "❌"
                msg += f"{emoji} {display_name}: {status_emoji}\n"
            
            msg += f"\n**Usage Examples**:\n"
            msg += f"`/confirmations enable` - Enable all confirmations\n"
            msg += f"`/confirmations disable` - Disable all confirmations\n"
            msg += f"`/confirmations trailing off` - Disable trailing stop notifications\n"
            msg += f"`/confirmations threshold 10` - Only notify for P&L > $10\n"
            
            return CommandResult(True, msg)
        
        # Handle configuration changes
        action = args[0].lower()
        
        if action == 'enable':
            self.confirmation_system.set_user_preferences(user_id, {
                **self.confirmation_system.get_user_preferences(user_id),
                'confirmations_enabled': True
            })
            return CommandResult(True, "✅ Trade confirmations **enabled**")
        
        elif action == 'disable':
            self.confirmation_system.set_user_preferences(user_id, {
                **self.confirmation_system.get_user_preferences(user_id),
                'confirmations_enabled': False
            })
            return CommandResult(True, "❌ Trade confirmations **disabled**")
        
        elif action == 'threshold':
            if len(args) < 2 or not args[1].replace('.', '').isdigit():
                return CommandResult(False, "❌ Usage: `/confirmations threshold <amount>`")
            
            threshold = float(args[1])
            self.confirmation_system.set_user_preferences(user_id, {
                **self.confirmation_system.get_user_preferences(user_id),
                'min_pnl_threshold': threshold
            })
            return CommandResult(True, f"💰 P&L threshold set to **${threshold:.2f}**")
        
        elif action in ['trailing', 'breakeven', 'partial', 'emergency']:
            if len(args) < 2 or args[1].lower() not in ['on', 'off']:
                return CommandResult(False, f"❌ Usage: `/confirmations {action} on/off`")
            
            enabled = args[1].lower() == 'on'
            key_map = {
                'trailing': 'trailing_stop_moved_enabled',
                'breakeven': 'breakeven_moved_enabled', 
                'partial': 'partial_close_enabled',
                'emergency': 'emergency_close_enabled'
            }
            
            prefs = self.confirmation_system.get_user_preferences(user_id)
            prefs[key_map[action]] = enabled
            self.confirmation_system.set_user_preferences(user_id, prefs)
            
            status = "enabled" if enabled else "disabled"
            return CommandResult(True, f"✅ {action.title()} notifications **{status}**")
        
        else:
            return CommandResult(False, "❌ Invalid option. Use `/confirmations` to see available options.")
    
    def get_confirmation_system(self) -> TradeConfirmationSystem:
        """Get the trade confirmation system instance"""
        return self.confirmation_system
    
    # ========================================
    # EDUCATION SYSTEM COMMANDS
    # ========================================
    
    @require_user()
    def _cmd_learn(self, user_id: int, chat_id: int) -> CommandResult:
        """Handle /learn command - Main education menu"""
        try:
            # Get user progress data
            user_rank = self.rank_access.get_user_rank(user_id)
            progress = self._get_user_education_progress(user_id)
            
            # Military-style header
            msg = "🎯 **OPERATIVE TRAINING CENTER**\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += f"**Rank**: {user_rank.name} | **Level**: {progress.get('level', 1)}\n"
            msg += f"**XP**: {progress.get('xp', 0):,}/{progress.get('next_level_xp', 1000):,}\n"
            msg += f"**Mission Streak**: {progress.get('mission_streak', 0)} days\n\n"
            
            msg += "🎖️ **COMMAND OPTIONS**\n"
            msg += "*Select your next move, soldier*\n"
            
            # Create inline keyboard menu
            keyboard = [
                [InlineKeyboardButton("📋 TODAY'S MISSIONS", callback_data="learn_missions")],
                [InlineKeyboardButton("📹 VIDEO LIBRARY", callback_data="learn_videos")],
                [InlineKeyboardButton("📊 MY PROGRESS", callback_data="learn_progress")],
                [InlineKeyboardButton("👥 SQUAD HQ", callback_data="learn_squad")],
                [InlineKeyboardButton("🎖️ ACHIEVEMENTS", callback_data="learn_achievements")],
                [InlineKeyboardButton("📝 NORMAN'S JOURNAL", callback_data="learn_journal")],
                [InlineKeyboardButton("📈 PAPER TRADING", callback_data="learn_paper_trading")],
                [InlineKeyboardButton("🎯 FIND MENTOR", callback_data="learn_mentor")]
            ]
            
            # Add notification badge if there are pending items
            pending = self._get_pending_notifications(user_id)
            if pending > 0:
                keyboard.insert(0, [InlineKeyboardButton(f"🔔 NOTIFICATIONS ({pending})", callback_data="learn_notifications")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Add motivational footer
            msg += "\n💬 *\"Every expert was once a disaster who refused to give up\"*"
            msg += "\n    - Norman, BITTEN Commander"
            
            return CommandResult(
                True,
                msg,
                data={'reply_markup': reply_markup}
            )
            
        except Exception as e:
            return CommandResult(False, f"❌ Training center error: {str(e)}")
    
    @require_user()
    def _cmd_missions(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /missions command - Show daily/weekly objectives"""
        try:
            missions = self._get_user_missions(user_id)
            
            msg = "📋 **MISSION BRIEFING**\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += f"*Operative {user_id} - Status Report*\n\n"
            
            # Daily Missions
            msg += "🎯 **DAILY OBJECTIVES** (Reset in 14h 32m)\n"
            for mission in missions.get('daily', []):
                status = "✅" if mission['completed'] else "⬜"
                reward = f"+{mission['xp']} XP" if mission['xp'] > 0 else ""
                msg += f"{status} {mission['name']} {reward}\n"
                if mission.get('progress'):
                    msg += f"   Progress: {mission['progress']}/{mission['target']}\n"
            
            msg += "\n📊 **WEEKLY CHALLENGES** (Reset in 3d 14h)\n"
            for mission in missions.get('weekly', []):
                status = "✅" if mission['completed'] else "⬜"
                reward = f"+{mission['xp']} XP"
                if mission.get('medal'):
                    reward += f" + 🎖️ {mission['medal']}"
                msg += f"{status} {mission['name']} {reward}\n"
                if mission.get('progress'):
                    msg += f"   Progress: {mission['progress']}/{mission['target']}\n"
            
            # Add special event missions if any
            if missions.get('special'):
                msg += "\n⚡ **SPECIAL OPS**\n"
                for mission in missions['special']:
                    msg += f"🔥 {mission['name']} - Expires in {mission['expires_in']}\n"
                    msg += f"   Reward: {mission['reward']}\n"
            
            # Progress summary
            daily_complete = sum(1 for m in missions.get('daily', []) if m['completed'])
            weekly_complete = sum(1 for m in missions.get('weekly', []) if m['completed'])
            msg += f"\n📈 **Progress**: {daily_complete}/{len(missions.get('daily', []))} daily | "
            msg += f"{weekly_complete}/{len(missions.get('weekly', []))} weekly\n"
            
            # Create inline keyboard
            keyboard = [
                [InlineKeyboardButton("🔄 REFRESH", callback_data="missions_refresh")],
                [InlineKeyboardButton("🏆 LEADERBOARD", callback_data="missions_leaderboard")]
            ]
            
            if daily_complete == len(missions.get('daily', [])):
                keyboard.insert(0, [InlineKeyboardButton("🎁 CLAIM DAILY BONUS", callback_data="missions_claim_daily")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            return CommandResult(
                True,
                msg,
                data={'reply_markup': reply_markup}
            )
            
        except Exception as e:
            return CommandResult(False, f"❌ Mission briefing error: {str(e)}")
    
    @require_user()
    def _cmd_journal(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /journal command - Quick journal entry"""
        try:
            if not args:
                # Show journal prompt
                msg = "📝 **COMBAT JOURNAL**\n"
                msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                msg += "*Record your trading thoughts, soldier*\n\n"
                
                # Show recent entries
                recent_entries = self._get_recent_journal_entries(user_id, limit=3)
                if recent_entries:
                    msg += "📖 **Recent Entries**:\n"
                    for entry in recent_entries:
                        msg += f"• {entry['timestamp']} - {entry['preview']}...\n"
                    msg += "\n"
                
                msg += "**Quick Entry Options**:\n"
                msg += "`/journal win [details]` - Log a victory\n"
                msg += "`/journal loss [details]` - Analyze a defeat\n"
                msg += "`/journal idea [details]` - Strategy thoughts\n"
                msg += "`/journal review` - Daily review\n"
                
                # Create inline keyboard
                keyboard = [
                    [InlineKeyboardButton("✍️ NEW ENTRY", callback_data="journal_new")],
                    [InlineKeyboardButton("📚 VIEW ALL", callback_data="journal_view_all")],
                    [InlineKeyboardButton("📊 STATS", callback_data="journal_stats")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                return CommandResult(True, msg, data={'reply_markup': reply_markup})
            
            # Process journal entry
            entry_type = args[0].lower()
            content = " ".join(args[1:]) if len(args) > 1 else ""
            
            # Save journal entry
            entry_id = self._save_journal_entry(user_id, entry_type, content)
            
            # Response based on entry type
            responses = {
                'win': "🎯 **Victory logged!** Keep that momentum going, soldier!",
                'loss': "📊 **Defeat analyzed.** Every loss is a lesson in disguise.",
                'idea': "💡 **Strategy noted!** Innovation wins wars.",
                'review': "✅ **Daily review complete.** Discipline creates champions."
            }
            
            response = responses.get(entry_type, "📝 **Entry saved!** Stay sharp out there.")
            response += f"\n\n+10 XP earned | Entry #{entry_id}"
            
            return CommandResult(True, response)
            
        except Exception as e:
            return CommandResult(False, f"❌ Journal error: {str(e)}")
    
    @require_user()
    def _cmd_squad(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /squad command - Squad management"""
        try:
            if not args:
                # Show squad overview
                squad_data = self._get_user_squad(user_id)
                
                msg = "👥 **SQUAD COMMAND**\n"
                msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                
                if squad_data:
                    msg += f"**Squad**: {squad_data['name']}\n"
                    msg += f"**Rank**: #{squad_data['rank']} | **Members**: {squad_data['member_count']}/10\n"
                    msg += f"**Total XP**: {squad_data['total_xp']:,}\n"
                    msg += f"**Win Rate**: {squad_data['win_rate']:.1f}%\n\n"
                    
                    msg += "👥 **Active Members**:\n"
                    for member in squad_data['members'][:5]:
                        status = "🟢" if member['online'] else "⚫"
                        msg += f"{status} {member['name']} - {member['rank']} ({member['xp']:,} XP)\n"
                    
                    if len(squad_data['members']) > 5:
                        msg += f"... and {len(squad_data['members']) - 5} more\n"
                else:
                    msg += "⚠️ **No squad assigned**\n"
                    msg += "Join a squad to unlock team missions!\n"
                
                # Create inline keyboard
                keyboard = []
                if squad_data:
                    keyboard.extend([
                        [InlineKeyboardButton("📊 SQUAD STATS", callback_data="squad_stats")],
                        [InlineKeyboardButton("💬 SQUAD CHAT", callback_data="squad_chat")],
                        [InlineKeyboardButton("🎯 TEAM MISSIONS", callback_data="squad_missions")]
                    ])
                    if squad_data.get('is_leader'):
                        keyboard.append([InlineKeyboardButton("⚙️ MANAGE", callback_data="squad_manage")])
                else:
                    keyboard.extend([
                        [InlineKeyboardButton("🔍 FIND SQUAD", callback_data="squad_find")],
                        [InlineKeyboardButton("➕ CREATE SQUAD", callback_data="squad_create")]
                    ])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                return CommandResult(True, msg, data={'reply_markup': reply_markup})
            
            # Handle squad sub-commands
            action = args[0].lower()
            if action == 'invite':
                if len(args) < 2:
                    return CommandResult(False, "❌ Usage: `/squad invite @username`")
                return self._squad_invite_member(user_id, args[1])
            elif action == 'leave':
                return self._squad_leave(user_id)
            else:
                return CommandResult(False, "❌ Unknown squad command")
                
        except Exception as e:
            return CommandResult(False, f"❌ Squad error: {str(e)}")
    
    @require_user()
    def _cmd_achievements(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /achievements command - Show medals and progress"""
        try:
            achievements = self._get_user_achievements(user_id)
            
            msg = "🎖️ **ACHIEVEMENT SHOWCASE**\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += f"**Total Medals**: {achievements['earned']}/{achievements['total']}\n"
            msg += f"**Completion**: {achievements['completion_percent']:.1f}%\n\n"
            
            # Show categories
            categories = ['Combat', 'Strategy', 'Discipline', 'Leadership', 'Special']
            for category in categories:
                cat_data = achievements.get(category.lower(), {})
                if cat_data:
                    msg += f"**{category}** ({cat_data['earned']}/{cat_data['total']})\n"
                    
                    # Show recent or notable achievements
                    for medal in cat_data.get('medals', [])[:3]:
                        icon = "🏅" if medal['rarity'] == 'legendary' else "🎖️"
                        status = "✅" if medal['earned'] else "🔒"
                        msg += f"{status} {icon} {medal['name']}\n"
                        if medal['earned']:
                            msg += f"   Earned: {medal['date']}\n"
                        else:
                            msg += f"   Progress: {medal['progress']}%\n"
                    msg += "\n"
            
            # Show next achievable medals
            if achievements.get('next_achievable'):
                msg += "🎯 **WITHIN REACH**:\n"
                for medal in achievements['next_achievable'][:3]:
                    msg += f"• {medal['name']} - {medal['requirement']}\n"
                    msg += f"  Progress: {medal['progress_bar']}\n"
            
            # Create inline keyboard
            keyboard = [
                [InlineKeyboardButton("🏆 ALL MEDALS", callback_data="achievements_all")],
                [InlineKeyboardButton("📊 STATISTICS", callback_data="achievements_stats")],
                [InlineKeyboardButton("🌟 SHOWCASE", callback_data="achievements_showcase")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            return CommandResult(True, msg, data={'reply_markup': reply_markup})
            
        except Exception as e:
            return CommandResult(False, f"❌ Achievements error: {str(e)}")
    
    @require_user()
    def _cmd_study(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /study command - Join study groups"""
        try:
            if not args:
                # Show available study groups
                groups = self._get_study_groups()
                
                msg = "📚 **STUDY GROUPS**\n"
                msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                msg += "*Join forces with fellow operatives*\n\n"
                
                # Active sessions
                active_sessions = [g for g in groups if g['status'] == 'active']
                if active_sessions:
                    msg += "🟢 **LIVE NOW**:\n"
                    for session in active_sessions[:3]:
                        msg += f"• **{session['topic']}**\n"
                        msg += f"  Host: {session['host']} | {session['participants']} operatives\n"
                        msg += f"  Level: {session['level']} | Started: {session['started_ago']}\n\n"
                
                # Scheduled sessions
                scheduled = [g for g in groups if g['status'] == 'scheduled']
                if scheduled:
                    msg += "📅 **UPCOMING**:\n"
                    for session in scheduled[:3]:
                        msg += f"• **{session['topic']}**\n"
                        msg += f"  Starts in: {session['starts_in']} | Level: {session['level']}\n"
                        msg += f"  Registered: {session['registered']}/{session['max_participants']}\n\n"
                
                # Study stats
                user_study_stats = self._get_user_study_stats(user_id)
                msg += f"📊 **Your Stats**: {user_study_stats['sessions_attended']} sessions | "
                msg += f"{user_study_stats['hours_studied']}h studied\n"
                
                # Create inline keyboard
                keyboard = [
                    [InlineKeyboardButton("🔍 BROWSE ALL", callback_data="study_browse")],
                    [InlineKeyboardButton("➕ CREATE SESSION", callback_data="study_create")],
                    [InlineKeyboardButton("📅 MY SCHEDULE", callback_data="study_schedule")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                return CommandResult(True, msg, data={'reply_markup': reply_markup})
            
            # Handle study sub-commands
            action = args[0].lower()
            if action == 'join':
                if len(args) < 2:
                    return CommandResult(False, "❌ Usage: `/study join <session_id>`")
                return self._study_join_session(user_id, args[1])
            elif action == 'host':
                return self._study_create_session(user_id, " ".join(args[1:]))
            else:
                return CommandResult(False, "❌ Unknown study command")
                
        except Exception as e:
            return CommandResult(False, f"❌ Study group error: {str(e)}")
    
    @require_user()
    def _cmd_mentor(self, user_id: int, args: List[str]) -> CommandResult:
        """Handle /mentor command - Find or become a mentor"""
        try:
            user_rank = self.rank_access.get_user_rank(user_id)
            
            if not args:
                # Show mentor overview
                msg = "🎯 **MENTOR PROGRAM**\n"
                msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                msg += "*Elite operatives training the next generation*\n\n"
                
                # Check if user is a mentor
                mentor_status = self._get_mentor_status(user_id)
                if mentor_status['is_mentor']:
                    msg += "👨‍🏫 **YOUR MENTOR STATUS**\n"
                    msg += f"Rating: {'⭐' * mentor_status['rating']} ({mentor_status['rating']}/5)\n"
                    msg += f"Students: {mentor_status['student_count']} active\n"
                    msg += f"Sessions: {mentor_status['total_sessions']} completed\n\n"
                
                # Show available mentors
                mentors = self._get_available_mentors(user_id)
                if mentors:
                    msg += "🌟 **AVAILABLE MENTORS**:\n"
                    for mentor in mentors[:5]:
                        msg += f"• **{mentor['name']}** - {mentor['rank']}\n"
                        msg += f"  Speciality: {mentor['specialty']}\n"
                        msg += f"  Rating: {'⭐' * mentor['rating']} | Students: {mentor['students']}\n"
                        msg += f"  Win Rate: {mentor['win_rate']:.1f}%\n\n"
                
                # Requirements to become a mentor
                if not mentor_status['is_mentor'] and user_rank.value >= UserRank.ELITE.value:
                    msg += "📋 **BECOME A MENTOR**:\n"
                    msg += "✅ Rank: ELITE or higher\n"
                    msg += "✅ 100+ successful trades\n"
                    msg += "✅ 65%+ win rate\n"
                    msg += "✅ Complete mentor training\n"
                
                # Create inline keyboard
                keyboard = []
                if mentor_status['is_mentor']:
                    keyboard.extend([
                        [InlineKeyboardButton("👥 MY STUDENTS", callback_data="mentor_students")],
                        [InlineKeyboardButton("📅 SCHEDULE", callback_data="mentor_schedule")]
                    ])
                else:
                    keyboard.append([InlineKeyboardButton("🔍 FIND MENTOR", callback_data="mentor_find")])
                    if user_rank.value >= UserRank.ELITE.value:
                        keyboard.append([InlineKeyboardButton("🎓 APPLY TO MENTOR", callback_data="mentor_apply")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                return CommandResult(True, msg, data={'reply_markup': reply_markup})
            
            # Handle mentor sub-commands
            action = args[0].lower()
            if action == 'request':
                if len(args) < 2:
                    return CommandResult(False, "❌ Usage: `/mentor request <mentor_id>`")
                return self._mentor_request_session(user_id, args[1])
            elif action == 'rate':
                if len(args) < 3:
                    return CommandResult(False, "❌ Usage: `/mentor rate <mentor_id> <1-5>`")
                return self._mentor_rate(user_id, args[1], args[2])
            else:
                return CommandResult(False, "❌ Unknown mentor command")
                
        except Exception as e:
            return CommandResult(False, f"❌ Mentor program error: {str(e)}")
    
    # Social Commands
    @require_user()
    def _cmd_refer(self, user_id: int, username: str, args: List[str]) -> CommandResult:
        """Handle /refer command - Elite military-style recruitment system"""
        try:
            # Integrate with XP economy if available
            if hasattr(self, 'bitten_core') and hasattr(self.bitten_core, 'xp_economy'):
                self.referral_system.xp_economy = self.bitten_core.xp_economy
            
            # Process referral command
            response = self.referral_handler.handle_command(str(user_id), username, args)
            
            # Check if we need to add inline keyboard for certain responses
            data = None
            if not args or (args and args[0].lower() == 'generate'):
                # Add share button for generated codes
                keyboard = [
                    [InlineKeyboardButton("📤 Share Code", callback_data="share_referral_code")],
                    [InlineKeyboardButton("📊 View Squad Tree", callback_data="referral_tree")],
                    [InlineKeyboardButton("🏆 Leaderboard", callback_data="referral_leaderboard")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                data = {'reply_markup': reply_markup}
            
            return CommandResult(True, response, data)
            
        except Exception as e:
            logger.error(f"Referral command error: {e}")
            return CommandResult(False, f"❌ Referral system error: {str(e)}")
    
    # Education System Helper Methods
    def _get_user_education_progress(self, user_id: int) -> Dict:
        """Get user's education progress"""
        # This would fetch from database in production
        return self.education_data['user_progress'].get(user_id, {
            'level': 1,
            'xp': 0,
            'next_level_xp': 1000,
            'mission_streak': 0,
            'total_missions': 0,
            'medals_earned': 0,
            'study_hours': 0
        })
    
    def _get_pending_notifications(self, user_id: int) -> int:
        """Get count of pending notifications for user"""
        return len([n for n in self.education_data['pending_notifications'] if n['user_id'] == user_id])
    
    def _get_user_missions(self, user_id: int) -> Dict:
        """Get user's active missions"""
        # This would fetch from database in production
        return {
            'daily': [
                {'name': 'Complete 3 paper trades', 'completed': False, 'xp': 50, 'progress': 1, 'target': 3},
                {'name': 'Watch 1 strategy video', 'completed': True, 'xp': 30, 'progress': 1, 'target': 1},
                {'name': 'Journal your trades', 'completed': False, 'xp': 20, 'progress': 0, 'target': 1},
                {'name': 'Review market analysis', 'completed': False, 'xp': 40, 'progress': 0, 'target': 1}
            ],
            'weekly': [
                {'name': 'Achieve 60% win rate', 'completed': False, 'xp': 200, 'medal': 'Sharpshooter', 'progress': 45, 'target': 60},
                {'name': 'Complete 20 trades', 'completed': False, 'xp': 150, 'progress': 12, 'target': 20},
                {'name': 'Attend 3 study sessions', 'completed': False, 'xp': 100, 'progress': 1, 'target': 3}
            ],
            'special': []
        }
    
    def _get_recent_journal_entries(self, user_id: int, limit: int) -> List[Dict]:
        """Get recent journal entries"""
        # This would fetch from database in production
        return [
            {'timestamp': '14:32', 'preview': 'EURUSD win - followed the trend perfectly'},
            {'timestamp': 'Yesterday', 'preview': 'Need to work on stop loss discipline'},
            {'timestamp': '2 days ago', 'preview': 'Market structure analysis paying off'}
        ]
    
    def _save_journal_entry(self, user_id: int, entry_type: str, content: str) -> int:
        """Save journal entry and return entry ID"""
        # This would save to database in production
        import random
        return random.randint(1000, 9999)
    
    def _get_user_squad(self, user_id: int) -> Optional[Dict]:
        """Get user's squad information"""
        # This would fetch from database in production
        return {
            'name': 'Alpha Traders',
            'rank': 42,
            'member_count': 7,
            'total_xp': 45320,
            'win_rate': 68.5,
            'is_leader': False,
            'members': [
                {'name': 'TradeMaster', 'rank': 'ELITE', 'xp': 12500, 'online': True},
                {'name': 'PipHunter', 'rank': 'AUTHORIZED', 'xp': 8900, 'online': True},
                {'name': 'ChartNinja', 'rank': 'ELITE', 'xp': 10200, 'online': False}
            ]
        }
    
    def _get_user_achievements(self, user_id: int) -> Dict:
        """Get user's achievements"""
        # This would fetch from database in production
        return {
            'earned': 24,
            'total': 75,
            'completion_percent': 32.0,
            'combat': {
                'earned': 8,
                'total': 20,
                'medals': [
                    {'name': 'First Blood', 'earned': True, 'date': '2 weeks ago', 'rarity': 'common'},
                    {'name': 'Sharpshooter', 'earned': False, 'progress': 75, 'rarity': 'rare'},
                    {'name': 'Perfect Week', 'earned': False, 'progress': 40, 'rarity': 'legendary'}
                ]
            },
            'next_achievable': [
                {'name': 'Consistent Trader', 'requirement': '5 winning days in a row', 'progress_bar': '███░░ 3/5'},
                {'name': 'Risk Manager', 'requirement': 'Never exceed 2% risk for 50 trades', 'progress_bar': '████░ 42/50'}
            ]
        }
    
    def _get_study_groups(self) -> List[Dict]:
        """Get available study groups"""
        # This would fetch from database in production
        return [
            {
                'topic': 'Market Structure Masterclass',
                'host': 'EliteTrader99',
                'participants': 12,
                'level': 'Intermediate',
                'status': 'active',
                'started_ago': '15 min ago'
            },
            {
                'topic': 'Risk Management Basics',
                'host': 'SafeTrader',
                'participants': 0,
                'max_participants': 20,
                'level': 'Beginner',
                'status': 'scheduled',
                'starts_in': '2 hours',
                'registered': 8
            }
        ]
    
    def _get_user_study_stats(self, user_id: int) -> Dict:
        """Get user's study statistics"""
        return {'sessions_attended': 12, 'hours_studied': 24}
    
    def _get_mentor_status(self, user_id: int) -> Dict:
        """Get user's mentor status"""
        user_rank = self.rank_access.get_user_rank(user_id)
        return {
            'is_mentor': user_rank.value >= UserRank.ELITE.value,
            'rating': 4,
            'student_count': 3,
            'total_sessions': 45
        }
    
    def _get_available_mentors(self, user_id: int) -> List[Dict]:
        """Get list of available mentors"""
        return [
            {
                'name': 'MasterTrader',
                'rank': 'ADMIN',
                'specialty': 'Scalping & Risk Management',
                'rating': 5,
                'students': 8,
                'win_rate': 78.5
            }
        ]
    
    def send_education_notification(self, user_id: int, notification_type: str, data: Dict) -> CommandResult:
        """Send education-related notifications"""
        try:
            # Mission reminders
            if notification_type == 'mission_reminder':
                msg = "📋 **MISSION REMINDER**\n"
                msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                msg += f"⏰ Daily reset in {data['time_remaining']}\n"
                msg += f"📊 Incomplete: {data['incomplete_count']} missions\n"
                msg += f"💰 Potential XP: {data['potential_xp']}\n\n"
                msg += "*Don't break your streak, soldier!*"
                
                keyboard = [[InlineKeyboardButton("📋 VIEW MISSIONS", callback_data="notification_missions")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
            # Achievement unlocked
            elif notification_type == 'achievement_unlocked':
                msg = "🎖️ **ACHIEVEMENT UNLOCKED!**\n"
                msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                msg += f"🏆 **{data['achievement_name']}**\n"
                msg += f"{data['description']}\n\n"
                msg += f"✨ +{data['xp_reward']} XP earned!\n"
                
                keyboard = [
                    [InlineKeyboardButton("🎖️ VIEW MEDAL", callback_data=f"achievement_view_{data['achievement_id']}")],
                    [InlineKeyboardButton("📤 SHARE", callback_data=f"achievement_share_{data['achievement_id']}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
            # Squad activity
            elif notification_type == 'squad_activity':
                msg = "👥 **SQUAD ALERT**\n"
                msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                msg += f"📢 {data['member_name']} {data['action']}\n"
                msg += f"Squad: {data['squad_name']}\n"
                
                keyboard = [[InlineKeyboardButton("👥 VIEW SQUAD", callback_data="notification_squad")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
            # Mentor session
            elif notification_type == 'mentor_session':
                msg = "🎯 **MENTOR SESSION**\n"
                msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                msg += f"📅 {data['session_type']} with {data['mentor_name']}\n"
                msg += f"⏰ Starting in: {data['time_until']}\n"
                msg += f"📍 Topic: {data['topic']}\n"
                
                keyboard = [
                    [InlineKeyboardButton("✅ JOIN SESSION", callback_data=f"mentor_join_{data['session_id']}")],
                    [InlineKeyboardButton("❌ CANCEL", callback_data=f"mentor_cancel_{data['session_id']}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
            else:
                return CommandResult(False, "Unknown notification type")
            
            # Store notification
            self.education_data['pending_notifications'].append({
                'user_id': user_id,
                'type': notification_type,
                'data': data,
                'timestamp': time.time()
            })
            
            return CommandResult(True, msg, data={'reply_markup': reply_markup})
            
        except Exception as e:
            return CommandResult(False, f"❌ Notification error: {str(e)}")
    
    def _handle_education_callback(self, user_id: int, callback_data: str) -> CommandResult:
        """Handle education system callbacks"""
        try:
            # Parse callback data
            parts = callback_data.split('_')
            category = parts[0]
            action = '_'.join(parts[1:]) if len(parts) > 1 else ''
            
            # Route to appropriate handler based on category
            if category == 'learn':
                if action == 'missions':
                    return self._cmd_missions(user_id, [])
                elif action == 'videos':
                    return self._show_video_library(user_id)
                elif action == 'progress':
                    return self._show_user_progress(user_id)
                elif action == 'squad':
                    return self._cmd_squad(user_id, [])
                elif action == 'achievements':
                    return self._cmd_achievements(user_id, [])
                elif action == 'journal':
                    return self._cmd_journal(user_id, [])
                elif action == 'paper_trading':
                    return self._show_paper_trading(user_id)
                elif action == 'mentor':
                    return self._cmd_mentor(user_id, [])
                elif action == 'notifications':
                    return self._show_notifications(user_id)
            
            elif category == 'missions':
                if action == 'refresh':
                    return self._cmd_missions(user_id, [])
                elif action == 'leaderboard':
                    return self._show_missions_leaderboard(user_id)
                elif action == 'claim_daily':
                    return self._claim_daily_bonus(user_id)
            
            elif category == 'journal':
                if action == 'new':
                    return self._show_journal_entry_form(user_id)
                elif action == 'view_all':
                    return self._show_all_journal_entries(user_id)
                elif action == 'stats':
                    return self._show_journal_stats(user_id)
            
            elif category == 'squad':
                if action == 'stats':
                    return self._show_squad_stats(user_id)
                elif action == 'chat':
                    return self._show_squad_chat(user_id)
                elif action == 'missions':
                    return self._show_squad_missions(user_id)
                elif action == 'manage':
                    return self._show_squad_management(user_id)
                elif action == 'find':
                    return self._show_squad_finder(user_id)
                elif action == 'create':
                    return self._show_squad_creation(user_id)
            
            elif category == 'achievements':
                if action == 'all':
                    return self._show_all_achievements(user_id)
                elif action == 'stats':
                    return self._show_achievement_stats(user_id)
                elif action == 'showcase':
                    return self._show_achievement_showcase(user_id)
            
            elif category == 'study':
                if action == 'browse':
                    return self._show_all_study_groups(user_id)
                elif action == 'create':
                    return self._show_study_creation_form(user_id)
                elif action == 'schedule':
                    return self._show_study_schedule(user_id)
            
            elif category == 'mentor':
                if action == 'students':
                    return self._show_mentor_students(user_id)
                elif action == 'schedule':
                    return self._show_mentor_schedule(user_id)
                elif action == 'find':
                    return self._show_mentor_finder(user_id)
                elif action == 'apply':
                    return self._show_mentor_application(user_id)
            
            elif category == 'notification':
                if action == 'missions':
                    return self._cmd_missions(user_id, [])
                elif action == 'squad':
                    return self._cmd_squad(user_id, [])
            
            # Default response
            return CommandResult(True, "✅ Processing your request...")
            
        except Exception as e:
            return CommandResult(False, f"❌ Callback error: {str(e)}")
    
    # Additional helper methods for education callbacks
    def _show_video_library(self, user_id: int) -> CommandResult:
        """Show video library"""
        msg = "📹 **VIDEO LIBRARY**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "📚 **Categories**:\n"
        msg += "• Beginner Basics (12 videos)\n"
        msg += "• Market Structure (8 videos)\n"
        msg += "• Risk Management (6 videos)\n"
        msg += "• Advanced Strategies (15 videos)\n\n"
        msg += "🔥 **Featured**: *'The 3-Bar Setup That Changed Everything'*\n"
        msg += "👁️ 2.3k views | ⭐ 4.8/5 rating\n"
        
        keyboard = [
            [InlineKeyboardButton("🎬 BROWSE VIDEOS", url="https://your-video-platform.com/library")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="learn_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_user_progress(self, user_id: int) -> CommandResult:
        """Show detailed user progress"""
        progress = self._get_user_education_progress(user_id)
        
        msg = "📊 **OPERATIVE PROGRESS REPORT**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += f"**Level {progress['level']}** - {progress['xp']:,}/{progress['next_level_xp']:,} XP\n"
        msg += f"Progress: {'█' * int(progress['xp']/progress['next_level_xp']*10)}{'░' * (10-int(progress['xp']/progress['next_level_xp']*10))}\n\n"
        msg += "📈 **Statistics**:\n"
        msg += f"• Mission Streak: {progress['mission_streak']} days 🔥\n"
        msg += f"• Total Missions: {progress['total_missions']}\n"
        msg += f"• Medals Earned: {progress['medals_earned']}\n"
        msg += f"• Study Hours: {progress['study_hours']}h\n\n"
        msg += "🎯 **Next Milestone**: Level 10 - Unlock Advanced Strategies\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="learn_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_paper_trading(self, user_id: int) -> CommandResult:
        """Show paper trading interface"""
        msg = "📈 **PAPER TRADING SIMULATOR**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "💰 **Virtual Balance**: $10,000\n"
        msg += "📊 **Open Positions**: 2\n"
        msg += "📈 **Today's P&L**: +$127.50 (+1.28%)\n\n"
        msg += "🎯 **Active Trades**:\n"
        msg += "• EURUSD Long @ 1.0855 (+12 pips)\n"
        msg += "• GBPJPY Short @ 185.20 (-5 pips)\n\n"
        msg += "*Practice without risk, master with confidence*\n"
        
        keyboard = [
            [InlineKeyboardButton("🔫 NEW TRADE", callback_data="paper_new_trade")],
            [InlineKeyboardButton("📊 PERFORMANCE", callback_data="paper_performance")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="learn_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_notifications(self, user_id: int) -> CommandResult:
        """Show pending notifications for user"""
        notifications = [n for n in self.education_data['pending_notifications'] if n['user_id'] == user_id]
        
        if not notifications:
            msg = "🔔 **NOTIFICATIONS**\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            msg += "📭 No new notifications\n\n"
            msg += "*Stay tuned for mission updates and achievements!*"
        else:
            msg = "🔔 **NOTIFICATIONS**\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for notif in notifications[-10:]:  # Show last 10
                icon = {
                    'mission_reminder': '📋',
                    'achievement_unlocked': '🎖️',
                    'squad_activity': '👥',
                    'mentor_session': '🎯'
                }.get(notif['type'], '📬')
                
                msg += f"{icon} {notif['type'].replace('_', ' ').title()}\n"
                if 'time_remaining' in notif['data']:
                    msg += f"   ⏰ {notif['data']['time_remaining']}\n"
                msg += "\n"
        
        keyboard = [
            [InlineKeyboardButton("🗑️ CLEAR ALL", callback_data="notifications_clear")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="learn_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    # Placeholder methods for squad operations
    def _squad_invite_member(self, user_id: int, username: str) -> CommandResult:
        """Invite member to squad"""
        return CommandResult(True, f"✅ Invitation sent to {username}")
    
    def _squad_leave(self, user_id: int) -> CommandResult:
        """Leave current squad"""
        return CommandResult(True, "✅ You have left the squad")
    
    # Placeholder methods for study operations  
    def _study_join_session(self, user_id: int, session_id: str) -> CommandResult:
        """Join study session"""
        return CommandResult(True, f"✅ Joined study session #{session_id}")
    
    def _study_create_session(self, user_id: int, topic: str) -> CommandResult:
        """Create new study session"""
        return CommandResult(True, f"✅ Study session created: {topic}")
    
    # Placeholder methods for mentor operations
    def _mentor_request_session(self, user_id: int, mentor_id: str) -> CommandResult:
        """Request mentor session"""
        return CommandResult(True, f"✅ Mentor session requested")
    
    def _mentor_rate(self, user_id: int, mentor_id: str, rating: str) -> CommandResult:
        """Rate mentor"""
        return CommandResult(True, f"✅ Thank you for rating your mentor!")
    
    # Additional placeholder methods for callbacks
    def _show_missions_leaderboard(self, user_id: int) -> CommandResult:
        """Show missions leaderboard"""
        msg = "🏆 **MISSIONS LEADERBOARD**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "🥇 **TradeMaster** - 342 missions\n"
        msg += "🥈 **PipHunter** - 298 missions\n"
        msg += "🥉 **ChartNinja** - 276 missions\n\n"
        msg += "Your rank: #42 (127 missions)\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="missions_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _claim_daily_bonus(self, user_id: int) -> CommandResult:
        """Claim daily bonus"""
        return CommandResult(True, "🎁 **Daily bonus claimed!** +100 XP")
    
    def _show_journal_entry_form(self, user_id: int) -> CommandResult:
        """Show journal entry form"""
        msg = "✍️ **NEW JOURNAL ENTRY**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "Select entry type:\n"
        
        keyboard = [
            [InlineKeyboardButton("🎯 Victory", callback_data="journal_type_win")],
            [InlineKeyboardButton("📊 Defeat", callback_data="journal_type_loss")],
            [InlineKeyboardButton("💡 Strategy", callback_data="journal_type_idea")],
            [InlineKeyboardButton("✅ Review", callback_data="journal_type_review")],
            [InlineKeyboardButton("⬅️ CANCEL", callback_data="journal_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_all_journal_entries(self, user_id: int) -> CommandResult:
        """Show all journal entries"""
        entries = self._get_recent_journal_entries(user_id, limit=10)
        
        msg = "📚 **COMBAT JOURNAL**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for entry in entries:
            msg += f"📝 {entry['timestamp']} - {entry['preview']}\n\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="journal_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_journal_stats(self, user_id: int) -> CommandResult:
        """Show journal statistics"""
        msg = "📊 **JOURNAL STATISTICS**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "📝 Total Entries: 47\n"
        msg += "🎯 Victories: 28 (59.6%)\n"
        msg += "📊 Defeats: 19 (40.4%)\n"
        msg += "💡 Strategy Ideas: 12\n"
        msg += "✅ Reviews: 15\n\n"
        msg += "📈 Most Active Day: Tuesday\n"
        msg += "⏰ Avg Entry Time: 15:30\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="journal_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    # Squad callback handlers
    def _show_squad_stats(self, user_id: int) -> CommandResult:
        """Show squad statistics"""
        msg = "📊 **SQUAD STATISTICS**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "👥 **Alpha Traders** - Rank #42\n\n"
        msg += "📈 **Performance**:\n"
        msg += "• Weekly Missions: 147/200 (73.5%)\n"
        msg += "• Total Wins: 892\n"
        msg += "• Win Rate: 68.5%\n"
        msg += "• Avg Risk/Reward: 1:2.3\n\n"
        msg += "🏆 **Top Performers**:\n"
        msg += "1. TradeMaster - 142 wins\n"
        msg += "2. PipHunter - 98 wins\n"
        msg += "3. ChartNinja - 87 wins\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="squad_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_squad_chat(self, user_id: int) -> CommandResult:
        """Show squad chat interface"""
        msg = "💬 **SQUAD CHAT**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "📍 Connect with your squad in the dedicated Telegram group\n\n"
        msg += "Share strategies, celebrate wins, analyze losses together!\n"
        
        keyboard = [
            [InlineKeyboardButton("💬 JOIN SQUAD CHAT", url="https://t.me/+squad_chat_link")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="squad_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_squad_missions(self, user_id: int) -> CommandResult:
        """Show squad missions"""
        msg = "🎯 **SQUAD MISSIONS**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "👥 **Team Objectives**:\n\n"
        msg += "⬜ Combined 500 trades this week (342/500)\n"
        msg += "⬜ Maintain 65%+ win rate (68.5% ✅)\n"
        msg += "⬜ Zero blown accounts (✅)\n"
        msg += "⬜ 10 members online daily (7/10)\n\n"
        msg += "🎁 **Rewards**: Squad Badge + 500 XP each\n"
        msg += "⏰ **Resets in**: 4d 12h 23m\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="squad_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_squad_management(self, user_id: int) -> CommandResult:
        """Show squad management options"""
        msg = "⚙️ **SQUAD MANAGEMENT**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "Leader tools coming soon!\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="squad_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_squad_finder(self, user_id: int) -> CommandResult:
        """Show squad finder"""
        msg = "🔍 **FIND A SQUAD**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "🌟 **Recommended Squads**:\n\n"
        msg += "1. **Risk Managers** (8/10 members)\n"
        msg += "   Focus: Conservative trading\n"
        msg += "   Avg Win Rate: 72%\n\n"
        msg += "2. **Scalp Masters** (9/10 members)\n"
        msg += "   Focus: Quick trades\n"
        msg += "   Avg Win Rate: 65%\n\n"
        msg += "3. **Trend Riders** (6/10 members)\n"
        msg += "   Focus: Swing trading\n"
        msg += "   Avg Win Rate: 68%\n"
        
        keyboard = [
            [InlineKeyboardButton("🔍 VIEW ALL", callback_data="squad_browse_all")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="squad_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_squad_creation(self, user_id: int) -> CommandResult:
        """Show squad creation form"""
        msg = "➕ **CREATE SQUAD**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "📋 **Requirements**:\n"
        msg += "• Level 5+ required\n"
        msg += "• 50+ completed trades\n"
        msg += "• 60%+ win rate\n\n"
        msg += "Send squad details:\n"
        msg += "`/squad create [name] [focus]`\n\n"
        msg += "Example:\n"
        msg += "`/squad create \"Pip Warriors\" scalping`\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="squad_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    # Achievement callback handlers
    def _show_all_achievements(self, user_id: int) -> CommandResult:
        """Show all achievements"""
        msg = "🏆 **ALL ACHIEVEMENTS**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "Browse all 75 achievements across 5 categories\n\n"
        msg += "Select category to view:\n"
        
        keyboard = [
            [InlineKeyboardButton("⚔️ COMBAT", callback_data="achievements_cat_combat")],
            [InlineKeyboardButton("🧠 STRATEGY", callback_data="achievements_cat_strategy")],
            [InlineKeyboardButton("📊 DISCIPLINE", callback_data="achievements_cat_discipline")],
            [InlineKeyboardButton("👥 LEADERSHIP", callback_data="achievements_cat_leadership")],
            [InlineKeyboardButton("⭐ SPECIAL", callback_data="achievements_cat_special")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="achievements_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_achievement_stats(self, user_id: int) -> CommandResult:
        """Show achievement statistics"""
        msg = "📊 **ACHIEVEMENT STATISTICS**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "🎖️ **Progress**: 24/75 (32%)\n\n"
        msg += "📈 **By Rarity**:\n"
        msg += "• Common: 15/30 (50%)\n"
        msg += "• Rare: 7/25 (28%)\n"
        msg += "• Epic: 2/15 (13%)\n"
        msg += "• Legendary: 0/5 (0%)\n\n"
        msg += "🏅 **Recent**: First Blood (2 weeks ago)\n"
        msg += "⏰ **Next**: Risk Manager (85% complete)\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="achievements_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_achievement_showcase(self, user_id: int) -> CommandResult:
        """Show achievement showcase configuration"""
        msg = "🌟 **ACHIEVEMENT SHOWCASE**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "Select up to 3 achievements to display on your profile:\n\n"
        msg += "Currently showcasing:\n"
        msg += "1. 🎖️ First Blood\n"
        msg += "2. 🎖️ Week Warrior\n"
        msg += "3. 🎖️ Risk Manager\n\n"
        msg += "Tap an achievement to change it\n"
        
        keyboard = [
            [InlineKeyboardButton("📝 EDIT SHOWCASE", callback_data="achievements_edit_showcase")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="achievements_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    # Study group callback handlers
    def _show_all_study_groups(self, user_id: int) -> CommandResult:
        """Show all study groups"""
        msg = "🔍 **ALL STUDY GROUPS**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "Filter by level:\n"
        
        keyboard = [
            [InlineKeyboardButton("🟢 BEGINNER", callback_data="study_filter_beginner")],
            [InlineKeyboardButton("🟡 INTERMEDIATE", callback_data="study_filter_intermediate")],
            [InlineKeyboardButton("🔴 ADVANCED", callback_data="study_filter_advanced")],
            [InlineKeyboardButton("📅 SCHEDULED", callback_data="study_filter_scheduled")],
            [InlineKeyboardButton("🔴 LIVE NOW", callback_data="study_filter_live")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="study_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_study_creation_form(self, user_id: int) -> CommandResult:
        """Show study session creation form"""
        msg = "➕ **CREATE STUDY SESSION**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "Host a session and share your knowledge!\n\n"
        msg += "**Format**:\n"
        msg += "`/study host [topic] [level] [time]`\n\n"
        msg += "**Example**:\n"
        msg += "`/study host \"Support & Resistance\" intermediate 2pm`\n\n"
        msg += "**Guidelines**:\n"
        msg += "• Keep sessions focused (30-60 min)\n"
        msg += "• Prepare materials in advance\n"
        msg += "• Encourage participation\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="study_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_study_schedule(self, user_id: int) -> CommandResult:
        """Show user's study schedule"""
        msg = "📅 **MY STUDY SCHEDULE**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "📍 **Upcoming Sessions**:\n\n"
        msg += "**Today 3:00 PM**\n"
        msg += "Risk Management Basics\n"
        msg += "Host: SafeTrader\n\n"
        msg += "**Tomorrow 2:00 PM**\n"
        msg += "Chart Patterns 101\n"
        msg += "Host: ChartMaster\n\n"
        msg += "**Friday 4:00 PM**\n"
        msg += "Weekly Market Review\n"
        msg += "Host: MarketGuru\n"
        
        keyboard = [
            [InlineKeyboardButton("📅 SYNC CALENDAR", callback_data="study_sync_calendar")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="study_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    # Mentor callback handlers
    def _show_mentor_students(self, user_id: int) -> CommandResult:
        """Show mentor's students"""
        msg = "👥 **MY STUDENTS**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "Currently mentoring 3 operatives:\n\n"
        msg += "1. **NewTrader123**\n"
        msg += "   Level: 3 | Sessions: 5\n"
        msg += "   Focus: Risk Management\n\n"
        msg += "2. **LearningPips**\n"
        msg += "   Level: 5 | Sessions: 8\n"
        msg += "   Focus: Technical Analysis\n\n"
        msg += "3. **FutureElite**\n"
        msg += "   Level: 7 | Sessions: 12\n"
        msg += "   Focus: Psychology\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="mentor_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_mentor_schedule(self, user_id: int) -> CommandResult:
        """Show mentor's schedule"""
        msg = "📅 **MENTOR SCHEDULE**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "📍 **This Week**:\n\n"
        msg += "**Mon 3PM**: NewTrader123 - Risk Review\n"
        msg += "**Wed 4PM**: LearningPips - Chart Analysis\n"
        msg += "**Fri 2PM**: FutureElite - Psychology\n\n"
        msg += "⏰ **Available Slots**:\n"
        msg += "• Tue 2-5 PM\n"
        msg += "• Thu 3-6 PM\n"
        msg += "• Sat 10 AM-12 PM\n"
        
        keyboard = [
            [InlineKeyboardButton("📝 MANAGE SLOTS", callback_data="mentor_manage_slots")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="mentor_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_mentor_finder(self, user_id: int) -> CommandResult:
        """Show mentor finder interface"""
        msg = "🔍 **FIND A MENTOR**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "Match with experienced traders:\n\n"
        msg += "Filter by specialty:\n"
        
        keyboard = [
            [InlineKeyboardButton("📊 Technical Analysis", callback_data="mentor_spec_technical")],
            [InlineKeyboardButton("💰 Risk Management", callback_data="mentor_spec_risk")],
            [InlineKeyboardButton("🧠 Psychology", callback_data="mentor_spec_psychology")],
            [InlineKeyboardButton("⚡ Scalping", callback_data="mentor_spec_scalping")],
            [InlineKeyboardButton("📈 Swing Trading", callback_data="mentor_spec_swing")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="mentor_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
    
    def _show_mentor_application(self, user_id: int) -> CommandResult:
        """Show mentor application form"""
        msg = "🎓 **MENTOR APPLICATION**\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "📋 **Requirements Check**:\n"
        msg += "✅ Rank: ELITE or higher\n"
        msg += "❌ 100+ successful trades (87/100)\n"
        msg += "✅ 65%+ win rate (68.5%)\n"
        msg += "❌ Complete mentor training\n\n"
        msg += "You need 13 more successful trades to apply.\n\n"
        msg += "Keep pushing, soldier! You're almost there.\n"
        
        keyboard = [
            [InlineKeyboardButton("📚 MENTOR TRAINING", callback_data="mentor_training_info")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="mentor_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return CommandResult(True, msg, data={'reply_markup': reply_markup})
