"""
BITTEN Onboarding Input Handlers
Premium AAA-quality user experience with zero friction
Designed for everyone: tech newbies, grandmas, blue collar workers
"""

import logging
import re
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

class OnboardingHandlers:
    """
    Handles user input with extreme care for user experience.
    Every interaction is designed to be crystal clear and impossible to mess up.
    """
    
    def __init__(self):
        self.validators = None  # Will be injected by orchestrator
        
        # Friendly error messages that don't make users feel stupid
        self.friendly_errors = {
            'invalid_selection': "🤔 Hmm, I didn't catch that. Just tap one of the buttons below!",
            'invalid_callsign': "💭 That callsign won't work. Try something like 'Wolf' or 'Eagle21' - letters and numbers only!",
            'too_long': "📏 That's a bit long! Let's keep it under 15 characters.",
            'need_selection': "👆 Just tap one of the options above to continue!",
            'technical_error': "⚡ Something went wrong on our end. Just type /start to try again!"
        }
        
        # Smart input detection for common user mistakes
        self.yes_variations = ['yes', 'y', 'yeah', 'yep', 'yup', 'sure', 'ok', 'okay', '1', 'si', 'da']
        self.no_variations = ['no', 'n', 'nope', 'nah', 'not', '0', '2']
        
    async def handle_input(self, session, current_state, input_type: str, 
                          input_data: Any) -> Dict[str, Any]:
        """
        Process user input with maximum forgiveness and clarity
        """
        
        handler_method = f"_handle_{current_state.value}"
        
        try:
            if hasattr(self, handler_method):
                return await getattr(self, handler_method)(session, input_type, input_data)
            
            # Default handler for states without specific handling
            return {
                'error': False,
                'message': 'Processing...',
                'advance_state': True
            }
            
        except Exception as e:
            logger.error(f"Handler error in {current_state.value}: {str(e)}")
            return {
                'error': True,
                'message': self.friendly_errors['technical_error'],
                'advance_state': False
            }
    
    async def _handle_first_contact(self, session, input_type: str, input_data: Any) -> Dict[str, Any]:
        """Handle trading experience question with smart detection"""
        
        if input_type == "callback":
            if input_data in ["yes", "no"]:
                session.has_experience = (input_data == "yes")
                
                # Personalized response based on experience
                if session.has_experience:
                    confirm_msg = "🎯 Excellent! A seasoned trader. Let's get you set up properly."
                else:
                    confirm_msg = "🌟 Perfect! Everyone starts somewhere. I'll guide you step by step."
                
                return {
                    'error': False,
                    'message': confirm_msg,
                    'advance_state': True,
                    'state_data': {'has_experience': session.has_experience}
                }
        
        elif input_type == "text":
            # Smart text detection for users who type instead of clicking
            text_lower = input_data.lower().strip()
            
            if text_lower in self.yes_variations:
                return await self._handle_first_contact(session, "callback", "yes")
            elif text_lower in self.no_variations:
                return await self._handle_first_contact(session, "callback", "no")
            else:
                return {
                    'error': True,
                    'message': self.friendly_errors['need_selection'],
                    'advance_state': False
                }
        
        return {'error': True, 'message': self.friendly_errors['invalid_selection']}
    
    async def _handle_knowledge_source(self, session, input_type: str, input_data: Any) -> Dict[str, Any]:
        """Handle how they heard about trading - very forgiving"""
        
        valid_sources = ['friend', 'youtube', 'article', 'other']
        
        if input_type == "callback" and input_data in valid_sources:
            session.knowledge_source = input_data
            
            # Friendly acknowledgment for each source
            responses = {
                'friend': "👥 Word of mouth is powerful! Your friend gave you good advice.",
                'youtube': "📺 Great choice! Visual learning helps many traders succeed.",
                'article': "📖 Solid foundation! Reading shows you're serious about this.",
                'other': "🌐 However you found us, we're glad you're here!"
            }
            
            return {
                'error': False,
                'message': responses.get(input_data, responses['other']),
                'advance_state': True,
                'state_data': {'knowledge_source': input_data}
            }
        
        return {'error': True, 'message': self.friendly_errors['need_selection']}
    
    async def _handle_theater_selection(self, session, input_type: str, input_data: Any) -> Dict[str, Any]:
        """Handle demo vs live account vs press pass selection"""
        
        if input_type == "callback":
            if input_data in ['demo', 'live']:
                session.selected_theater = input_data
                
                if input_data == 'demo':
                    message = "🎮 **Training Mode Selected!**\n\nSmart choice! You'll practice with virtual funds until you're ready for the real thing. No risk, all learning!"
                else:
                    message = "💰 **Live Mode Selected!**\n\nYou're going straight to the action! Remember: start small, learn constantly, and never risk more than you can afford to lose."
                
                return {
                    'error': False,
                    'message': message,
                    'advance_state': True,
                    'state_data': {'theater': input_data}
                }
            elif input_data == 'press_pass':
                # Transition to Press Pass intro state
                session.selected_theater = 'press_pass'
                return {
                    'error': False,
                    'advance_state': True,
                    'next_state': 'press_pass_intro',
                    'state_data': {'theater': 'press_pass'}
                }
        
        return {'error': True, 'message': self.friendly_errors['need_selection']}
    
    async def _handle_secure_link(self, session, input_type: str, input_data: Any) -> Dict[str, Any]:
        """Handle secure link / broker connection and email capture"""
        
        # Check if we're waiting for email input
        if hasattr(session, '_waiting_for_email') and session._waiting_for_email:
            if input_type == "text":
                # Validate email
                if self.validators and self.validators.is_valid_email(input_data):
                    session.email = input_data.lower().strip()
                    session._waiting_for_email = False
                    return {
                        'error': False,
                        'message': (
                            f"✅ **Email Confirmed**: {session.email}\n\n"
                            "Great! I'll use this for important account notifications.\n"
                            "Let's continue setting up your account..."
                        ),
                        'advance_state': True,
                        'state_data': {'email': session.email}
                    }
                else:
                    return {
                        'error': True,
                        'message': (
                            "🤔 That doesn't look like a valid email address.\n\n"
                            "Please enter a valid email like: example@email.com"
                        ),
                        'advance_state': False
                    }
        
        if input_type == "callback":
            if input_data == "connect_broker":
                # Request email for broker connection
                session._waiting_for_email = True
                return {
                    'error': False,
                    'message': (
                        "📧 **Secure Connection Setup**\n\n"
                        "To connect your broker account and receive important updates, "
                        "I'll need your email address.\n\n"
                        "Please type your email address below:"
                    ),
                    'advance_state': False,
                    'keyboard': {}  # Remove buttons to encourage text input
                }
            elif input_data == "skip_broker":
                return {
                    'error': False,
                    'message': "⏭️ Skipping broker connection for now. You can connect later from settings.",
                    'advance_state': True
                }
        
        return {'error': True, 'message': self.friendly_errors['invalid_selection']}
    
    async def _handle_oath_of_enlistment(self, session, input_type: str, input_data: Any) -> Dict[str, Any]:
        """Handle oath acceptance"""
        
        if input_type == "callback":
            if input_data == "accept_oath":
                session.accepted_terms = True
                return {
                    'error': False,
                    'message': (
                        "🎖️ **OATH ACCEPTED!**\n\n"
                        "You are now bound by the code of the BITTEN Network.\n"
                        "Honor, discipline, and calculated aggression will guide your path.\n\n"
                        "*Welcome to the brotherhood, soldier.*"
                    ),
                    'advance_state': True,
                    'state_data': {'accepted_terms': True}
                }
            elif input_data == "read_oath":
                # Show the oath again
                oath_text = (
                    "📜 **THE BITTEN OATH OF ENLISTMENT**\n\n"
                    "I solemnly swear to:\n\n"
                    "⚔️ **HONOR** the markets with disciplined execution\n"
                    "🛡️ **PROTECT** my capital with strategic risk management\n"
                    "🎯 **EXECUTE** trades with precision and purpose\n"
                    "📚 **LEARN** from every victory and defeat\n"
                    "🤝 **SUPPORT** my fellow traders in the network\n\n"
                    "I understand that trading involves risk and commit to:\n"
                    "• Never risk more than I can afford to lose\n"
                    "• Follow the BITTEN risk management protocols\n"
                    "• Maintain emotional discipline at all times\n\n"
                    "Do you accept this oath?"
                )
                return {
                    'error': False,
                    'message': oath_text,
                    'advance_state': False
                }
        
        return {'error': True, 'message': self.friendly_errors['need_selection']}
    
    async def _handle_press_pass_intro(self, session, input_type: str, input_data: Any) -> Dict[str, Any]:
        """Handle Press Pass activation and information"""
        
        if input_type == "callback":
            if input_data == "activate_press_pass":
                # Set up Press Pass account
                from datetime import datetime, timedelta
                session.is_press_pass = True
                session.press_pass_expiry = datetime.utcnow() + timedelta(days=7)
                
                message = (
                    "🎟️ **PRESS PASS ACTIVATED!**\n\n"
                    "🚀 **Full Access Granted**: All BITTEN features unlocked for 7 days\n"
                    "💰 **MetaQuotes Demo**: $50,000 practice account provisioned\n"
                    "⏰ **Nightly XP Reset**: Your progress resets at midnight UTC\n"
                    "📅 **Expires**: 7 days from activation\n\n"
                    "⚡ **IMPORTANT**: After 7 days, upgrade to a paid tier to keep your progress!\n\n"
                    "*Welcome to the BITTEN Network, Press Corps operative!*"
                )
                
                return {
                    'error': False,
                    'message': message,
                    'advance_state': True,
                    'state_data': {
                        'is_press_pass': True,
                        'press_pass_expiry': session.press_pass_expiry.isoformat()
                    }
                }
            elif input_data == "press_pass_info":
                info_message = (
                    "🎟️ **BITTEN PRESS PASS**\n\n"
                    "The Press Pass is your VIP access to the BITTEN Network:\n\n"
                    "✅ **7-Day Full Access**: Experience everything BITTEN offers\n"
                    "✅ **No Payment Required**: Start immediately, no credit card\n"
                    "✅ **$50K Demo Account**: Practice with MetaQuotes virtual funds\n"
                    "✅ **All Features Unlocked**: Every tool, strategy, and signal\n\n"
                    "⚠️ **Limitations**:\n"
                    "• XP resets nightly at midnight UTC\n"
                    "• Access expires after 7 days\n"
                    "• Must upgrade to retain progress\n\n"
                    "Ready to activate your Press Pass?"
                )
                
                return {
                    'error': False,
                    'message': info_message,
                    'advance_state': False,
                    'keyboard': {
                        "inline_keyboard": [
                            [{"text": "🎟️ Activate Now", "callback_data": "onboarding_activate_press_pass"}],
                            [{"text": "↩️ Go Back", "callback_data": "onboarding_back"}]
                        ]
                    }
                }
        
        return {'error': True, 'message': self.friendly_errors['need_selection']}
    
    async def _handle_callsign_creation(self, session, input_type: str, input_data: Any) -> Dict[str, Any]:
        """Handle callsign creation with helpful validation"""
        
        if input_type == "text":
            callsign = input_data.strip()
            
            # Super helpful validation
            if len(callsign) < 3:
                return {
                    'error': True,
                    'message': "📏 Too short! Your callsign needs at least 3 characters. Try something like 'Ace' or 'Fox1'",
                    'advance_state': False
                }
            
            if len(callsign) > 15:
                return {
                    'error': True,
                    'message': self.friendly_errors['too_long'],
                    'advance_state': False
                }
            
            # Allow letters, numbers, and underscores only
            if not re.match(r'^[a-zA-Z0-9_]+$', callsign):
                return {
                    'error': True,
                    'message': "🔤 Callsigns can only use letters, numbers, and underscores. Try something like 'Shadow_1' or 'IronEagle'",
                    'advance_state': False
                }
            
            # Check for inappropriate content (basic filter)
            blocked_words = ['admin', 'bitten', 'system', 'support', 'help', 'mod', 'moderator']
            if any(word in callsign.lower() for word in blocked_words):
                return {
                    'error': True,
                    'message': "🚫 That callsign is reserved. Pick something unique to you!",
                    'advance_state': False
                }
            
            # Success! Make them feel awesome
            session.callsign = callsign
            return {
                'error': False,
                'message': f"🎖️ **Outstanding!** From now on, you're known as **{callsign}**!\n\nThis is your identity in the BITTEN network. Wear it with pride, soldier!",
                'advance_state': True,
                'state_data': {'callsign': callsign}
            }
        
        elif input_type == "callback" and input_data == "skip":
            # Allow skipping with auto-generated callsign
            import random
            auto_callsign = f"Trader{random.randint(1000, 9999)}"
            session.callsign = auto_callsign
            
            return {
                'error': False,
                'message': f"⚡ No problem! We'll call you **{auto_callsign}** for now. You can change this later in settings.",
                'advance_state': True,
                'state_data': {'callsign': auto_callsign, 'auto_generated': True}
            }
        
        return {
            'error': True,
            'message': "💭 Type your callsign using letters and numbers. For example: 'Eagle1' or 'RedFox'",
            'advance_state': False
        }
    
    async def _handle_notification_preferences(self, session, input_type: str, input_data: Any) -> Dict[str, Any]:
        """Handle notification preferences"""
        
        if input_type == "callback":
            if input_data == "all":
                session.notifications = {'trades': True, 'news': True, 'education': True}
                message = "🔔 **All Notifications ON!** You'll get the complete BITTEN experience."
            elif input_data == "essential":
                session.notifications = {'trades': True, 'news': False, 'education': False}
                message = "📌 **Essential Only!** You'll only hear about your trades."
            elif input_data == "custom":
                # This would lead to a sub-menu in a full implementation
                message = "⚙️ **Custom Settings!** Let's set up exactly what you want..."
                # For now, default to essential
                session.notifications = {'trades': True, 'news': False, 'education': False}
            else:
                return {'error': True, 'message': self.friendly_errors['need_selection']}
            
            return {
                'error': False,
                'message': message,
                'advance_state': True,
                'state_data': {'notifications': session.notifications}
            }
        
        return {'error': True, 'message': self.friendly_errors['need_selection']}
    
    async def _handle_ready_confirmation(self, session, input_type: str, input_data: Any) -> Dict[str, Any]:
        """Final confirmation before entering the platform"""
        
        if input_type == "callback":
            if input_data == "ready":
                return {
                    'error': False,
                    'message': "🚀 **SYSTEMS ONLINE!** Welcome to BITTEN, soldier. Your journey begins NOW!",
                    'advance_state': True,
                    'complete': True
                }
            elif input_data == "review":
                # Show summary of their choices
                summary = f"""📋 **Your BITTEN Profile:**

🎖️ Callsign: **{session.callsign}**
🎮 Mode: **{session.selected_theater.upper()}**
📚 Experience: **{'Veteran' if session.has_experience else 'Recruit'}**
🔔 Notifications: **{session.notifications.get('trades', False) and 'Active' or 'Limited'}**

Everything look good?"""
                
                return {
                    'error': False,
                    'message': summary,
                    'advance_state': False,
                    'show_ready_button': True
                }
        
        return {'error': True, 'message': self.friendly_errors['need_selection']}
    
    def get_skip_button(self, state: str) -> Optional[Dict]:
        """Provide skip option for certain states to reduce friction"""
        
        skippable_states = ['callsign_creation', 'notification_preferences']
        
        if state in skippable_states:
            return {"text": "⏭️ Skip for now", "callback_data": f"onboarding_skip"}
        
        return None
    
    def get_back_button(self, state: str) -> Optional[Dict]:
        """Allow going back to fix mistakes"""
        
        # Don't allow back on first state or final states
        no_back_states = ['first_contact', 'ready_confirmation', 'complete']
        
        if state not in no_back_states:
            return {"text": "↩️ Go Back", "callback_data": "onboarding_back"}
        
        return None
    
    def format_progress_bar(self, current_step: int, total_steps: int) -> str:
        """Show visual progress to reduce anxiety"""
        
        filled = "🟩" * current_step
        empty = "⬜" * (total_steps - current_step)
        percentage = (current_step / total_steps) * 100
        
        return f"{filled}{empty} {percentage:.0f}%"