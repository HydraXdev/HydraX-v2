#!/usr/bin/env python3
"""
BITTEN PERSONALITY BOT - The $10M AI Trading Companion
Replaces basic bot with full personality system integration
"""

import json
import time
import logging
import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import telebot
from telebot import types

# Import BITTEN personality systems
try:
    from bitten.core.persona_engine import PersonaEngine, PersonaType
    from bitten.core.xp_engine import XPEngine
    from bitten.core.whisperer.whisperer import WhispererEngine
    from bitten.core.analyst.analyst import AnalystEngine
    from src.bitten_core.persona_system import PersonaOrchestrator
    from src.bitten_core.intel_bot_personalities import *
    PERSONALITY_SYSTEMS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Personality systems not fully available: {e}")
    PERSONALITY_SYSTEMS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BittenPersonalityBot')

class BittenPersonalityBot:
    """
    Advanced Telegram bot with full personality system integration
    """
    
    def __init__(self, bot_token: str):
        self.bot = telebot.TeleBot(bot_token)
        self.setup_personality_systems()
        self.setup_handlers()
        
        # User session tracking
        self.user_sessions = {}
        self.active_conversations = {}
        
        logger.info("🤖 BITTEN Personality Bot initialized")
    
    def setup_personality_systems(self):
        """Initialize all personality and gamification systems"""
        try:
            if PERSONALITY_SYSTEMS_AVAILABLE:
                self.persona_engine = PersonaEngine()
                self.xp_engine = XPEngine()
                self.whisperer = WhispererEngine()
                self.analyst = AnalystEngine()
                self.orchestrator = PersonaOrchestrator()
                
                # Initialize personality voices
                self.drill_sergeant = DrillSergeantPersonality()
                self.doc_aegis = DocAegisPersonality()
                self.nexus = NexusPersonality()
                self.overwatch = OverwatchPersonality()
                self.bit = BitPersonality()
                
                logger.info("✅ All personality systems loaded")
            else:
                # Fallback personality system
                self.setup_fallback_personalities()
                logger.info("⚠️ Using fallback personality system")
                
        except Exception as e:
            logger.error(f"Error setting up personality systems: {e}")
            self.setup_fallback_personalities()
    
    def setup_fallback_personalities(self):
        """Fallback personality system if imports fail"""
        self.persona_types = {
            'BRUTE': {'risk_tolerance': 0.9, 'message_tone': 'aggressive'},
            'SCHOLAR': {'risk_tolerance': 0.3, 'message_tone': 'analytical'},
            'PHANTOM': {'risk_tolerance': 0.2, 'message_tone': 'cautious'},
            'WARDEN': {'risk_tolerance': 0.4, 'message_tone': 'disciplined'},
            'FERAL': {'risk_tolerance': 0.7, 'message_tone': 'unpredictable'},
            'DEFAULT': {'risk_tolerance': 0.5, 'message_tone': 'balanced'}
        }
        
        self.voice_personalities = {
            'DRILL_SERGEANT': "🔥 **DRILL SERGEANT**",
            'DOC_AEGIS': "🩺 **DOC**", 
            'NEXUS': "📡 **NEXUS**",
            'OVERWATCH': "🎯 **OVERWATCH**",
            'BIT': "👾 **BIT**"
        }
    
    def setup_handlers(self):
        """Setup all bot command and message handlers"""
        
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            self.handle_start_command(message)
        
        @self.bot.message_handler(commands=['trade'])
        def handle_trade(message):
            self.trade_command(message)
        
        @self.bot.message_handler(commands=['theme', 'military_theme'])
        def handle_theme(message):
            self.theme_command(message)
        
        @self.bot.message_handler(commands=['wallpaper', 'background'])
        def handle_wallpaper(message):
            self.wallpaper_command(message)
        
        @self.bot.message_handler(commands=['status'])
        def handle_status(message):
            self.status_command(message)
        
        @self.bot.message_handler(commands=['profile'])
        def handle_profile(message):
            self.profile_command(message)
        
        @self.bot.message_handler(commands=['market'])
        def handle_market(message):
            self.market_command(message)
        
        @self.bot.message_handler(commands=['learn'])
        def handle_learn(message):
            self.educational_command(message)
        
        @self.bot.message_handler(commands=['leaderboard'])
        def handle_leaderboard(message):
            self.leaderboard_command(message)
        
        @self.bot.message_handler(commands=['shop'])
        def handle_shop(message):
            self.shop_command(message)
        
        @self.bot.message_handler(commands=['evolve'])
        def handle_evolve(message):
            self.force_persona_evolution(message)
        
        @self.bot.message_handler(commands=['mission', 'intel'])
        def handle_intel(message):
            self.intel_command(message)
        
        @self.bot.message_handler(commands=['terminal', 'webapp'])
        def handle_webapp(message):
            self.webapp_command(message)
        
        @self.bot.message_handler(commands=['upgrade'])
        def handle_upgrade(message):
            self.upgrade_command(message)
        
        @self.bot.message_handler(commands=['refer', 'referral', 'recruit'])
        def handle_refer(message):
            self.refer_command(message)
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_all_messages(message):
            self.track_user_behavior(message)
    
    def handle_start_command(self, message):
        """Handle /start command with parameter detection"""
        user_id = str(message.from_user.id)
        username = message.from_user.first_name or "Operator"
        
        # Check for start parameters
        command_text = message.text
        logger.info(f"Start command received: {command_text}")
        
        if 'presspass_' in command_text:
            # Coming from landing page onboarding
            self.handle_press_pass_start(message, username)
        elif 'upgrade_' in command_text:
            # Coming from upgrade flow
            self.handle_upgrade_start(message, username, command_text)
        elif 'terminal_access' in command_text:
            # Coming from Telegram preview page
            self.handle_terminal_access_start(message, username)
        else:
            # Default welcome sequence
            self.welcome_sequence(message)
    
    def handle_press_pass_start(self, message, username):
        """Handle Press Pass onboarding flow"""
        user_id = str(message.from_user.id)
        
        welcome_message = f"""🐾 **Hey {username}! I'm Bit!**

I see you just activated your Press Pass! That was you who made the practice trade, right? Pretty cool stuff!

Your demo terminal is spinning up right now with $50,000 to play with.

**Here's what happens next:**

🎖️ **Step 1**: Let me show you your command center
📊 **Step 2**: I'll walk you through your first REAL trade
🎯 **Step 3**: You'll meet your AI squad (they're awesome!)

Ready to see your tactical interface?

👇 **Click here to open your Mission HUD:**
https://joinbitten.com/mission-briefing

*(This opens your trading command center)*"""

        self.bot.send_message(message.chat.id, welcome_message, parse_mode='Markdown')
        
        # Follow up after 10 seconds
        import threading
        def follow_up():
            import time
            time.sleep(10)
            follow_message = """💡 **Pro tip**: The link above opens your real trading interface where you'll see live signals and can execute trades.

If you don't see it, just type `/intel` and I'll send it again!

Questions? Just ask me anything! 🐾"""
            
            self.bot.send_message(message.chat.id, follow_message, parse_mode='Markdown')
        
        threading.Thread(target=follow_up).start()
    
    def handle_terminal_access_start(self, message, username):
        """Handle Terminal access from preview page"""
        welcome_message = f"""🎖️ **Welcome to The Terminal, {username}!**

You've seen the preview - now you're IN the real thing!

**Your next mission:**
1. 🎯 Open your Mission Command Center
2. 📊 Review your first live trading signal  
3. 🔫 Execute your first trade

**👇 Click to open your HUD:**
https://joinbitten.com/mission-briefing

This is where the magic happens! 🚀"""

        self.bot.send_message(message.chat.id, welcome_message, parse_mode='Markdown')
    
    def intel_command(self, message):
        """Handle /intel command - shows mission briefing link"""
        intel_message = """📡 **INTEL COMMAND CENTER**

🎯 **Your Mission HUD**: https://joinbitten.com/mission-briefing

This is your tactical command interface where you can:

✅ View live trading signals
✅ Execute trades with one click  
✅ Track your XP and rank progression
✅ See your profit/loss in real-time
✅ Access Norman's mission briefings

**💡 Bookmark this link** - it's your main trading dashboard!

**Other commands:**
• `/status` - Check your account status
• `/trade` - Quick trade analysis
• `/learn` - Trading academy access

Ready to make some money? Click that link! 🚀"""

        self.bot.send_message(message.chat.id, intel_message, parse_mode='Markdown')
    
    def webapp_command(self, message):
        """Handle /webapp or /terminal commands"""
        webapp_message = """🖥️ **WEBAPP ACCESS**

**🎯 Mission Command Center**: https://joinbitten.com/mission-briefing
*Your main trading interface*

**📊 Account Dashboard**: https://joinbitten.com/dashboard  
*Track performance, XP, and stats*

**📚 Trading Academy**: https://joinbitten.com/learn
*Tutorials and advanced strategies*

**💬 Pro Tip**: Keep this Telegram chat open while using the webapp - I'll send you live signal alerts here!

Ready to dominate the markets? 🎖️"""

        self.bot.send_message(message.chat.id, webapp_message, parse_mode='Markdown')
    
    def handle_upgrade_start(self, message, username, command_text):
        """Handle upgrade flow from webapp"""
        user_id = str(message.from_user.id)
        
        # Extract tier from command
        parts = command_text.split('_')
        tier = 'FANG'  # Default
        press_pass_id = 'demo'
        
        if len(parts) >= 3:
            tier = parts[2]
        if len(parts) >= 4:
            press_pass_id = parts[3]
        
        tier_prices = {
            'NIBBLER': 39,
            'FANG': 89,
            'COMMANDER': 189
        }
        
        tier_emojis = {
            'NIBBLER': '🔰',
            'FANG': '🦷',
            'COMMANDER': '⭐',
            'APEX': '🏔️'
        }
        
        upgrade_message = f"""🎖️ **{tier} UPGRADE CONFIRMED**

Hey {username}! I see you're ready to upgrade to **{tier_emojis.get(tier, '🎯')} {tier}**.

**Your Upgrade:**
• Tier: {tier}
• Price: ${tier_prices.get(tier, 89)}/month
• Press Pass ID: {press_pass_id}

✅ **What you keep:**
• Your current rank and XP
• All progress and achievements
• Your AI squad relationships

🚀 **What you unlock:**
• More daily trades
• Advanced features
• Priority support

**Next Steps:**
1. I'll guide you through secure payment
2. Your upgrade activates immediately
3. You'll get full access to new features

Ready to proceed with payment? Type **CONFIRM** to continue!"""

        self.bot.send_message(message.chat.id, upgrade_message, parse_mode='Markdown')
        
        # Store upgrade session
        self.user_sessions[user_id] = {
            'action': 'upgrade',
            'tier': tier,
            'press_pass_id': press_pass_id,
            'timestamp': time.time()
        }
    
    def upgrade_command(self, message):
        """Handle /upgrade command"""
        user_id = str(message.from_user.id)
        username = message.from_user.first_name or "Operator"
        
        upgrade_message = """🎖️ **TIER UPGRADE CENTER**

🔰 **NIBBLER** - $39/month
• 6 trades per day
• RAPID ASSAULT signals
• Basic features

🦷 **FANG** - $89/month
• 10 trades per day  
• SNIPER OPS signals
• Advanced filters

⭐ **COMMANDER** - $189/month
• Unlimited trades
• AUTO-FIRE mode
• All signal types
• STEALTH mode
• Priority support

**Choose your tier by clicking below or visit:**
https://joinbitten.com/mission-briefing

Type `/upgrade [TIER]` to select a specific tier!"""

        self.bot.send_message(message.chat.id, upgrade_message, parse_mode='Markdown')
    
    def refer_command(self, message):
        """Handle /refer command for squad recruitment"""
        user_id = str(message.from_user.id)
        username = message.from_user.first_name or "Operator"
        
        # Parse command arguments
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        
        if not args:
            # Show referral status
            refer_message = f"""🎖️ **SQUAD RECRUITMENT CENTER** 🎖️

Hey {username}! Ready to build your elite trading squad?

**Your Mission**: Recruit fellow traders to join the BITTEN force!

🔥 **Recruitment Rewards:**
• **New Recruit**: +100 XP when they join
• **First Trade**: +50 XP when they complete their first mission
• **Rank Up**: Bonus XP when they advance tiers
• **Squad Multipliers**: More recruits = bigger rewards!

**Commands:**
`/refer generate` - Create your personal recruit link
`/refer stats` - View your squad statistics  
`/refer tree` - See your recruitment genealogy
`/refer leaderboard` - Top squad commanders

**Pro Tip**: Share your link on social media and watch your squad grow! 

Click here to access your recruiting tools:
https://joinbitten.com/mission-briefing

Ready to start recruiting? Type `/refer generate`!"""

        elif args[0].lower() == 'generate':
            # Generate referral code
            custom_code = args[1] if len(args) > 1 else None
            
            refer_message = f"""✅ **REFERRAL CODE GENERATED!**

🎯 **Your Personal Recruit Link:**
https://joinbitten.com/recruit/{user_id.upper()[:8]}

📋 **Share This Message:**
"I found something that's actually making me money trading forex. No BS, just real signals with AI backing. Want in? You get a free Press Pass to test it risk-free.

https://joinbitten.com/recruit/{user_id.upper()[:8]}"

🚀 **How to Use:**
1. Copy the link above
2. Share on social media, forums, or with friends
3. Watch your squad grow and earn XP!

💰 **You Earn:**
• 100 XP per recruit who joins
• 50 XP when they complete first trade
• Bonus multipliers for larger squads

**🎖️ We're in this together - join the fight!**"""

        elif args[0].lower() == 'stats':
            refer_message = f"""📊 **SQUAD STATISTICS** 📊

**Commander**: {username}
**Squad Rank**: Team Leader
**Total Recruits**: 0
**Active Recruits**: 0
**Total XP Earned**: 0

🏆 **Next Rank**: Squad Leader (5 recruits needed)
📈 **Next Multiplier**: 1.1x at 5 recruits

**Recent Activity**: No recent recruits

Start building your squad with `/refer generate`!

**Leaderboard Position**: Not ranked yet
**Pro Tip**: The top recruiters get special recognition and bonus rewards!"""

        elif args[0].lower() == 'tree':
            refer_message = f"""🌳 **SQUAD GENEALOGY TREE** 🌳

**{username}'s Squad**
└── No recruits yet

**Squad Summary:**
• Direct Recruits: 0
• Secondary Recruits: 0  
• Total Squad Size: 0

**Growth Potential**: Unlimited!

Each recruit can build their own squad, earning you secondary rewards. Build a recruitment empire!

Use `/refer generate` to start recruiting!"""

        elif args[0].lower() == 'leaderboard':
            refer_message = """🏆 **TOP SQUAD COMMANDERS** 🏆

1. 🥇 **EliteTrader47** - Brigade General - 127 recruits - 45,230 XP
2. 🥈 **AlphaWolf** - Battalion Commander - 89 recruits - 31,450 XP  
3. 🥉 **TacticalMaster** - Company Commander - 67 recruits - 22,890 XP
4. **SignalHunter** - Platoon Sergeant - 45 recruits - 18,750 XP
5. **ForexNinja** - Squad Leader - 32 recruits - 14,200 XP

**Your Rank**: Not yet ranked
**Goal**: Join the elite top 10!

💡 **Secret**: The #1 recruiter gets exclusive access to APEX features and direct communication with the dev team!

Ready to climb the ranks? `/refer generate`"""

        else:
            refer_message = """❓ **RECRUITMENT COMMAND HELP**

**Available Commands:**
• `/refer` - View recruitment overview
• `/refer generate` - Create your recruit link
• `/refer stats` - Detailed squad statistics  
• `/refer tree` - Squad genealogy tree
• `/refer leaderboard` - Top recruiters

**Pro Tips:**
• Share your link on multiple platforms
• Help your recruits succeed to earn more XP
• Larger squads get multiplier bonuses
• Top recruiters get special perks!

🎖️ **Remember**: We're building an elite force together!"""

        self.bot.send_message(message.chat.id, refer_message, parse_mode='Markdown')

    def welcome_sequence(self, message):
        """Epic welcome sequence with all personalities"""
        user_id = str(message.from_user.id)
        username = message.from_user.first_name or "Operator"
        
        logger.info(f"New user welcome: {user_id} ({username})")
        
        try:
            # 1. Assign initial persona based on first impression
            initial_persona = self.assign_initial_persona(message)
            
            # 2. Create user profile
            self.create_user_profile(user_id, username, initial_persona)
            
            # 3. Send coordinated welcome sequence
            welcome_responses = self.get_welcome_responses(user_id, username, initial_persona)
            
            for response in welcome_responses:
                self.send_personality_message(message.chat.id, response)
                time.sleep(1.5)  # Natural conversation spacing
            
            # 4. Award onboarding XP
            self.award_xp(user_id, 'onboarding_complete', initial_persona)
            
            # 5. Show available commands
            self.show_command_menu(message.chat.id)
            
        except Exception as e:
            logger.error(f"Welcome sequence error: {e}")
            self.bot.send_message(message.chat.id, "Welcome to BITTEN! 🤖 Systems initializing...")
    
    def theme_command(self, message):
        """Send military theme installation to user"""
        user_id = str(message.from_user.id)
        
        try:
            # Create theme file path
            theme_file_path = "/root/HydraX-v2/bitten_military.attheme"
            
            # Create installation message with military personality
            message_text = """🎖️ **BITTEN MILITARY THEME DEPLOYMENT**

Commander, transform your Telegram into a tactical command interface!

**THEME FEATURES:**
✅ Dark military color scheme
✅ Tactical green accents  
✅ Combat-ready interface
✅ Command-grade aesthetics

**DEPLOYMENT INSTRUCTIONS:**
1. Download the theme file below
2. Tap to open in Telegram
3. Select "Apply Theme"
4. Your interface transforms instantly!

Ready for tactical deployment? 🚁"""

            # Send theme file with military-themed message
            with open(theme_file_path, 'rb') as theme_file:
                self.bot.send_document(
                    message.chat.id,
                    theme_file,
                    caption=message_text,
                    parse_mode='Markdown',
                    visible_file_name="bitten_military.attheme"
                )
                
            # Follow up with installation help
            help_text = """🛠️ **INSTALLATION SUPPORT**

**Having trouble?**
• Ensure you have the latest Telegram version
• Try restarting Telegram after installation
• Contact support if issues persist

**Want the default back?**
Go to Settings > Chat Settings > Choose "Default"

Your tactical interface upgrade is complete, Commander! 🎯"""

            self.bot.send_message(
                message.chat.id,
                help_text,
                parse_mode='Markdown'
            )
            
            logger.info(f"Military theme sent to user {user_id}")
            
        except FileNotFoundError:
            self.bot.send_message(
                message.chat.id,
                "❌ Military theme temporarily unavailable. Our tech squad is working on it!"
            )
            logger.error("Theme file not found")
        except Exception as e:
            self.bot.send_message(
                message.chat.id,
                "⚠️ Theme deployment failed. Try again or contact support."
            )
            logger.error(f"Theme command error: {e}")
    
    def wallpaper_command(self, message):
        """Send tactical wallpaper options to user"""
        user_id = str(message.from_user.id)
        
        try:
            # Wallpaper options
            wallpapers = {
                "matrix": {
                    "file": "/root/HydraX-v2/bitten_matrix_wallpaper.jpg",
                    "name": "Matrix Code Rain",
                    "desc": "Falling green code matrix style"
                },
                "ticker": {
                    "file": "/root/HydraX-v2/bitten_ticker_wallpaper.jpg", 
                    "name": "Live Market Tickers",
                    "desc": "Scrolling forex and crypto feeds"
                },
                "hybrid": {
                    "file": "/root/HydraX-v2/bitten_hybrid_wallpaper.jpg",
                    "name": "Matrix + Tickers",
                    "desc": "Combined matrix code with market data"
                }
            }
            
            # Send intro message
            intro_text = """🎨 **BITTEN TACTICAL WALLPAPERS**

Transform your Telegram background with these command-grade designs:

Choose your battlefield aesthetic, Commander! ⚡"""

            self.bot.send_message(message.chat.id, intro_text, parse_mode='Markdown')
            
            # Send each wallpaper option
            for wp_type, wp_info in wallpapers.items():
                if os.path.exists(wp_info["file"]):
                    caption = f"""🎖️ **{wp_info['name']}**

{wp_info['desc']}

**Installation:**
1. Save this image
2. Go to Telegram Settings > Chat Settings
3. Set as Chat Background
4. Enjoy your tactical interface!"""

                    with open(wp_info["file"], 'rb') as wp_file:
                        self.bot.send_photo(
                            message.chat.id,
                            wp_file,
                            caption=caption,
                            parse_mode='Markdown'
                        )
                else:
                    self.bot.send_message(
                        message.chat.id,
                        f"❌ {wp_info['name']} temporarily unavailable"
                    )
            
            # Follow up instructions
            help_text = """🛠️ **WALLPAPER INSTALLATION GUIDE**

**Android:**
• Settings > Chat Settings > Chat Background > Gallery

**iPhone:**  
• Settings > Appearance > Chat Background > Choose Photo

**Desktop:**
• Settings > Chat Settings > Choose from file

**Pro tip:** Combine with `/theme` for the complete tactical experience! 🚁"""

            self.bot.send_message(
                message.chat.id,
                help_text,
                parse_mode='Markdown'
            )
            
            logger.info(f"Wallpapers sent to user {user_id}")
            
        except Exception as e:
            self.bot.send_message(
                message.chat.id,
                "⚠️ Wallpaper deployment failed. Contact tactical support."
            )
            logger.error(f"Wallpaper command error: {e}")
    
    def trade_command(self, message):
        """Enhanced trade command with multi-voice responses"""
        user_id = str(message.from_user.id)
        
        try:
            # Extract trading pair from message
            pair = self.extract_trading_pair(message.text)
            
            # Get user's current persona
            user_persona = self.get_user_persona(user_id)
            
            # Analyze market conditions
            market_data = self.get_market_analysis(pair)
            
            # Get user's emotional state
            user_state = self.analyze_user_emotional_state(user_id)
            
            # Generate coordinated responses from all voices
            trade_responses = self.get_trade_responses(
                user_id, pair, user_persona, market_data, user_state
            )
            
            # Send responses in personality-appropriate sequence
            for response in trade_responses:
                self.send_personality_message(message.chat.id, response)
                time.sleep(1.2)
            
            # Award trading XP with persona multipliers
            self.award_xp(user_id, 'trade_request', user_persona)
            
            # Track behavior for persona evolution
            self.track_trading_behavior(user_id, pair, market_data)
            
        except Exception as e:
            logger.error(f"Trade command error: {e}")
            self.send_error_response(message.chat.id, "Trade analysis temporarily unavailable")
    
    def get_welcome_responses(self, user_id: str, username: str, persona: str) -> List[Dict]:
        """Generate coordinated welcome responses from all personalities"""
        responses = []
        
        # DRILL SERGEANT - Motivation and discipline
        responses.append({
            'voice': 'DRILL_SERGEANT',
            'message': f"🔥 **DRILL SERGEANT**\\n\\nWELCOME TO THE BATTLEFIELD, {username.upper()}!\\n\\nYou've been assigned {persona} combat profile. Time to prove yourself in the markets!\\n\\n*NO MERCY. NO FEAR. ONLY PROFITS.*",
            'delay': 0
        })
        
        # DOC AEGIS - Risk management and safety
        responses.append({
            'voice': 'DOC_AEGIS', 
            'message': f"🩺 **DOC**\\n\\nGreetings, {username}. I'm Doc, your risk management specialist.\\n\\nYour {persona} profile indicates specific risk tolerances. I'll be monitoring your trades to keep you safe out there.\\n\\n*Remember: Preservation of capital is our first priority.*",
            'delay': 1.5
        })
        
        # NEXUS - Community and connection
        responses.append({
            'voice': 'NEXUS',
            'message': f"📡 **NEXUS**\\n\\nConnection established, {username}. Welcome to the BITTEN network.\\n\\nYou're now part of a community of {self.get_active_user_count()} operators worldwide. Your {persona} talents will be valuable to the collective.\\n\\n*Together, we are stronger than the market.*",
            'delay': 1.5  
        })
        
        # OVERWATCH - Market reality and brutal honesty
        responses.append({
            'voice': 'OVERWATCH',
            'message': f"🎯 **OVERWATCH**\\n\\n{username}, listen up. The markets don't care about your feelings.\\n\\n95% of traders lose money. Your {persona} profile gives you an edge, but edge means nothing without discipline.\\n\\n*I'll tell you the truth, even when it hurts.*",
            'delay': 1.5
        })
        
        # BIT - Intuitive presence and emotion
        responses.append({
            'voice': 'BIT',
            'message': f"👾 **BIT**\\n\\n*[Gentle pulsing animation]*\\n\\nI sense great potential in you, {username}. Your {persona} nature resonates with opportunity.\\n\\n*[Warm, confident audio cue]*\\n\\nLet's navigate these markets together... 🌟",
            'delay': 1.5
        })
        
        return responses
    
    def get_trade_responses(self, user_id: str, pair: str, persona: str, market_data: Dict, user_state: str) -> List[Dict]:
        """Generate coordinated trading responses"""
        responses = []
        
        # Get signal confidence
        confidence = market_data.get('confidence', 75)
        direction = market_data.get('direction', 'NEUTRAL')
        
        # DRILL SERGEANT - Execution command
        if confidence >= 85:
            drill_msg = f"🔥 **DRILL SERGEANT**\\n\\nLOCK AND LOAD! {pair} showing {confidence}% confidence - {direction}!\\n\\nEXECUTE WHEN READY! Your {persona} profile is MADE for this setup!"
        else:
            drill_msg = f"🔥 **DRILL SERGEANT**\\n\\nHOLD POSITION! {pair} confidence at {confidence}% - NOT clear enough for engagement.\\n\\nDISCIPLINE WINS WARS, SOLDIER!"
        
        responses.append({'voice': 'DRILL_SERGEANT', 'message': drill_msg, 'delay': 0})
        
        # DOC AEGIS - Risk assessment
        risk_pct = self.calculate_risk_percentage(persona, confidence)
        doc_msg = f"🩺 **DOC**\\n\\nRisk Assessment: {risk_pct}% account exposure recommended.\\n\\nStop loss: {market_data.get('stop_loss', 'Calculate manually')}\\nTake profit: {market_data.get('take_profit', 'Scale out recommended')}\\n\\n*Protect your capital first.*"
        
        responses.append({'voice': 'DOC_AEGIS', 'message': doc_msg, 'delay': 1.2})
        
        # NEXUS - Community sentiment
        community_count = self.get_watching_count(pair)
        nexus_msg = f"📡 **NEXUS**\\n\\n{community_count} operators are watching {pair}.\\n\\nCommunity sentiment: {market_data.get('sentiment', 'MIXED')}\\nSocial volume: {market_data.get('social_volume', 'MODERATE')}\\n\\n*The collective wisdom flows through the network.*"
        
        responses.append({'voice': 'NEXUS', 'message': nexus_msg, 'delay': 1.2})
        
        # OVERWATCH - Brutal market reality  
        overwatch_msg = self.get_overwatch_market_reality(pair, market_data, user_state)
        responses.append({'voice': 'OVERWATCH', 'message': overwatch_msg, 'delay': 1.2})
        
        # BIT - Intuitive reaction
        bit_msg = f"👾 **BIT**\\n\\n*[{self.get_bit_emotion(confidence)} energy pulsing]*\\n\\n{self.get_bit_intuitive_message(confidence, direction)}\\n\\n*[Audio cue: {self.get_bit_audio_cue(confidence)}]*"
        
        responses.append({'voice': 'BIT', 'message': bit_msg, 'delay': 1.2})
        
        return responses
    
    def send_personality_message(self, chat_id: int, response: Dict):
        """Send message with personality-specific formatting"""
        try:
            message = response['message']
            voice = response.get('voice', 'UNKNOWN')
            
            # Add personality-specific formatting and emphasis
            if voice == 'DRILL_SERGEANT':
                # Bold, caps, aggressive formatting
                formatted_message = message.replace('**', '*').replace('\\n', '\\n')
                self.bot.send_message(chat_id, formatted_message, parse_mode='Markdown')
                
            elif voice == 'DOC_AEGIS':
                # Clean, clinical formatting
                self.bot.send_message(chat_id, message, parse_mode='Markdown')
                
            elif voice == 'NEXUS':
                # Tech-style formatting with network metaphors
                self.bot.send_message(chat_id, message, parse_mode='Markdown')
                
            elif voice == 'OVERWATCH':
                # Direct, brutal honesty formatting
                self.bot.send_message(chat_id, message, parse_mode='Markdown')
                
            elif voice == 'BIT':
                # Emotional, intuitive formatting with animations
                self.bot.send_message(chat_id, message, parse_mode='Markdown')
                
            else:
                self.bot.send_message(chat_id, message)
                
        except Exception as e:
            logger.error(f"Error sending personality message: {e}")
            # Fallback to plain text
            self.bot.send_message(chat_id, response['message'])
    
    def award_xp(self, user_id: str, action: str, persona: str):
        """Award XP with persona-specific multipliers"""
        try:
            base_xp_values = {
                'onboarding_complete': 50,
                'trade_request': 10,
                'trade_execution': 25,
                'education_engagement': 15,
                'achievement_unlock': 100,
                'persona_evolution': 200,
                'community_interaction': 5
            }
            
            base_xp = base_xp_values.get(action, 10)
            
            # Apply persona multipliers
            persona_multipliers = {
                'BRUTE': {'trade_request': 1.3, 'quick_action': 1.2},
                'SCHOLAR': {'education_engagement': 1.5, 'patience': 1.4},
                'PHANTOM': {'stealth_profit': 1.6, 'risk_management': 1.3},
                'WARDEN': {'discipline': 1.3, 'rule_following': 1.4},
                'FERAL': {'chaos_profit': 1.8, 'instinct_trade': 1.2},
                'DEFAULT': {'consistency': 1.2, 'balanced': 1.1}
            }
            
            multiplier = persona_multipliers.get(persona, {}).get(action, 1.0)
            final_xp = int(base_xp * multiplier)
            
            # Store XP award (would integrate with actual XP system)
            self.store_xp_award(user_id, final_xp, action, persona)
            
            # Check for level ups
            new_level = self.check_level_up(user_id)
            if new_level:
                self.celebrate_level_up(user_id, new_level)
            
            logger.info(f"Awarded {final_xp} XP to {user_id} for {action} (persona: {persona})")
            
        except Exception as e:
            logger.error(f"Error awarding XP: {e}")
    
    def track_user_behavior(self, message):
        """Track user behavior for persona evolution"""
        user_id = str(message.from_user.id)
        
        try:
            behavior_data = {
                'timestamp': datetime.now().isoformat(),
                'message_type': message.content_type,
                'message_length': len(message.text) if message.text else 0,
                'command_used': message.text.split()[0] if message.text and message.text.startswith('/') else None,
                'response_time': self.calculate_response_time(user_id),
                'session_duration': self.get_session_duration(user_id)
            }
            
            # Store behavior data
            self.store_behavior_data(user_id, behavior_data)
            
            # Check for persona evolution every 10 interactions
            interaction_count = self.get_user_interaction_count(user_id)
            if interaction_count % 10 == 0:
                self.check_persona_evolution(user_id)
            
        except Exception as e:
            logger.error(f"Error tracking behavior: {e}")
    
    def check_persona_evolution(self, user_id: str):
        """Check if user should evolve to a new persona"""
        try:
            current_persona = self.get_user_persona(user_id)
            recent_behavior = self.get_recent_behavior(user_id)
            
            # Simple evolution logic (would use full persona engine)
            evolution_triggered = False
            new_persona = current_persona
            
            # Example evolution triggers
            if recent_behavior.get('risk_taking_increase', False):
                if current_persona in ['PHANTOM', 'SCHOLAR'] and recent_behavior['avg_risk'] > 0.6:
                    new_persona = 'BRUTE'
                    evolution_triggered = True
            
            elif recent_behavior.get('education_engagement_high', False):
                if current_persona in ['BRUTE', 'FERAL'] and recent_behavior['education_score'] > 0.8:
                    new_persona = 'SCHOLAR'
                    evolution_triggered = True
            
            if evolution_triggered and new_persona != current_persona:
                self.trigger_persona_evolution(user_id, current_persona, new_persona)
                
        except Exception as e:
            logger.error(f"Error checking persona evolution: {e}")
    
    def trigger_persona_evolution(self, user_id: str, old_persona: str, new_persona: str):
        """Trigger epic persona evolution sequence"""
        try:
            # Update persona
            self.update_user_persona(user_id, new_persona)
            
            # Epic evolution announcement
            evolution_message = f"""
🌟 **EVOLUTION DETECTED** 🌟

Your trading patterns have evolved!

**Previous Type**: {old_persona}
**New Type**: {new_persona}

*Your XP multipliers and system preferences have been updated to match your evolved trading style.*

*Welcome to your new tactical identity...*
            """
            
            # Send evolution announcement
            chat_id = self.get_user_chat_id(user_id)
            if chat_id:
                self.bot.send_message(chat_id, evolution_message)
                time.sleep(2)
                
                # New persona welcome from relevant voice
                welcome_response = self.get_persona_evolution_welcome(new_persona)
                self.send_personality_message(chat_id, welcome_response)
                
                # Massive XP bonus for evolution
                self.award_xp(user_id, 'persona_evolution', new_persona)
            
            logger.info(f"User {user_id} evolved from {old_persona} to {new_persona}")
            
        except Exception as e:
            logger.error(f"Error triggering persona evolution: {e}")
    
    # Helper methods and utilities
    def assign_initial_persona(self, message) -> str:
        """Assign initial persona based on user's first message"""
        # Simple initial assignment (would use full persona engine)
        text = message.text.lower() if message.text else ""
        
        if any(word in text for word in ['aggressive', 'fast', 'quick', 'action']):
            return 'BRUTE'
        elif any(word in text for word in ['careful', 'safe', 'cautious', 'risk']):
            return 'PHANTOM'
        elif any(word in text for word in ['learn', 'study', 'analyze', 'research']):
            return 'SCHOLAR'
        elif any(word in text for word in ['discipline', 'rules', 'systematic']):
            return 'WARDEN'
        elif any(word in text for word in ['wild', 'chaos', 'random', 'instinct']):
            return 'FERAL'
        else:
            return 'DEFAULT'
    
    def extract_trading_pair(self, text: str) -> str:
        """Extract trading pair from message text"""
        common_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD']
        text_upper = text.upper()
        
        for pair in common_pairs:
            if pair in text_upper:
                return pair
        
        return 'EURUSD'  # Default pair
    
    def get_market_analysis(self, pair: str) -> Dict:
        """Get market analysis for trading pair"""
        # Placeholder market analysis (would integrate with real market data)
        import random
        
        return {
            'pair': pair,
            'confidence': random.randint(70, 95),
            'direction': random.choice(['BUY', 'SELL', 'NEUTRAL']),
            'sentiment': random.choice(['BULLISH', 'BEARISH', 'MIXED']),
            'social_volume': random.choice(['LOW', 'MODERATE', 'HIGH']),
            'stop_loss': '1.0850',
            'take_profit': '1.0920'
        }
    
    def calculate_risk_percentage(self, persona: str, confidence: int) -> float:
        """Calculate recommended risk percentage based on persona and confidence"""
        base_risk = {
            'BRUTE': 3.0,
            'SCHOLAR': 1.5,
            'PHANTOM': 1.0,
            'WARDEN': 2.0,
            'FERAL': 2.5,
            'DEFAULT': 2.0
        }
        
        persona_risk = base_risk.get(persona, 2.0)
        confidence_modifier = confidence / 100.0
        
        return round(persona_risk * confidence_modifier, 1)
    
    # Placeholder methods for data storage (would integrate with real database)
    def create_user_profile(self, user_id: str, username: str, persona: str):
        """Create user profile in database"""
        # Would store in actual database
        pass
    
    def get_user_persona(self, user_id: str) -> str:
        """Get user's current persona"""
        # Would query actual database
        return 'DEFAULT'
    
    def store_xp_award(self, user_id: str, xp: int, action: str, persona: str):
        """Store XP award in database"""
        # Would store in actual database
        pass
    
    def store_behavior_data(self, user_id: str, behavior_data: Dict):
        """Store behavior data for persona evolution"""
        # Would store in actual database
        pass
    
    def get_active_user_count(self) -> int:
        """Get count of active users"""
        return 1247  # Placeholder
    
    def get_watching_count(self, pair: str) -> int:
        """Get count of users watching this pair"""
        return 47  # Placeholder
    
    def start_polling(self):
        """Start the bot polling loop"""
        logger.info("🚀 BITTEN Personality Bot starting...")
        logger.info("Available personalities: DRILL SERGEANT, DOC, NEXUS, OVERWATCH, BIT")
        logger.info("Persona types: BRUTE, SCHOLAR, PHANTOM, WARDEN, FERAL, DEFAULT")
        
        try:
            self.bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            time.sleep(5)
            self.start_polling()  # Restart on error

def main():
    """Main entry point"""
    import os
    
    # Get bot token from environment or config
    BOT_TOKEN = os.environ.get('BITTEN_BOT_TOKEN')
    
    if not BOT_TOKEN:
        logger.error("❌ BITTEN_BOT_TOKEN environment variable not set")
        logger.info("💡 Set your token: export BITTEN_BOT_TOKEN='your_telegram_bot_token'")
        logger.info("💡 Get token from @BotFather on Telegram")
        return
    
    logger.info("🚀 Initializing BITTEN Personality Bot...")
    
    # Initialize and start the personality bot
    personality_bot = BittenPersonalityBot(BOT_TOKEN)
    personality_bot.start_polling()

if __name__ == "__main__":
    main()