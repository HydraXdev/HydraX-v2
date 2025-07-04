# telegram_bot_controls.py
# TELEGRAM BOT CONTROL COMMANDS
# Handles disclaimer, bot toggles, and user preferences

from typing import Dict, Optional
from .psyops.disclaimer_manager import DisclaimerManager, create_bot_toggle_menu

class TelegramBotControls:
    """Handles bot control commands for Telegram integration"""
    
    def __init__(self):
        self.disclaimer_manager = DisclaimerManager()
        
    def handle_disclaimer_command(self, user_id: str) -> Dict:
        """Handle /disclaimer command"""
        
        disclaimer = self.disclaimer_manager.get_onboarding_disclaimer()
        
        return {
            'success': True,
            'message': disclaimer['content'],
            'parse_mode': 'Markdown',
            'reply_markup': {
                'inline_keyboard': [[
                    {'text': '⚙️ Bot Settings', 'callback_data': 'open_settings'}
                ]]
            }
        }
    
    def handle_bots_command(self, user_id: str, args: list) -> Dict:
        """Handle /bots [on/off] command"""
        
        if not args:
            # Show current status
            menu_text = create_bot_toggle_menu(user_id, self.disclaimer_manager)
            return {
                'success': True,
                'message': menu_text,
                'parse_mode': 'Markdown'
            }
        
        action = args[0].lower()
        if action == 'on':
            result = self.disclaimer_manager.toggle_all_bots(user_id, True)
            return {
                'success': True,
                'message': "✅ **BOT SQUAD ACTIVATED**\n\n_All tactical personalities online. The team has your six._",
                'parse_mode': 'Markdown'
            }
        elif action == 'off':
            result = self.disclaimer_manager.toggle_all_bots(user_id, False)
            return {
                'success': True,
                'message': "❌ **BOT SQUAD OFFLINE**\n\n_Going dark. You're on your own, operator._",
                'parse_mode': 'Markdown'
            }
        else:
            return {
                'success': False,
                'message': "Invalid option. Use `/bots on` or `/bots off`"
            }
    
    def handle_toggle_command(self, user_id: str, args: list) -> Dict:
        """Handle /toggle [botname] command"""
        
        if not args:
            return {
                'success': False,
                'message': "Please specify a bot name. Example: `/toggle DrillBot`"
            }
        
        bot_name = args[0]
        
        # Check if bot exists
        if bot_name not in self.disclaimer_manager.bot_descriptions:
            available_bots = ", ".join(self.disclaimer_manager.bot_descriptions.keys())
            return {
                'success': False,
                'message': f"Unknown bot. Available bots: {available_bots}"
            }
        
        # Get current state
        consent = self.disclaimer_manager.get_user_preferences(user_id)
        if not consent:
            return {
                'success': False,
                'message': "Please complete onboarding first with /start"
            }
        
        # Toggle the bot
        current_state = consent.bot_preferences.get(bot_name, True)
        new_state = not current_state
        
        result = self.disclaimer_manager.toggle_individual_bot(user_id, bot_name, new_state)
        
        if result.get('success'):
            bot_info = self.disclaimer_manager.bot_descriptions[bot_name]
            status_emoji = "✅" if new_state else "❌"
            status_text = "enabled" if new_state else "disabled"
            
            message = f"{status_emoji} **{bot_name}** has been {status_text}\n\n"
            message += f"_{bot_info['description']}_"
            
            return {
                'success': True,
                'message': message,
                'parse_mode': 'Markdown'
            }
        else:
            return {
                'success': False,
                'message': result.get('message', 'Failed to toggle bot')
            }
    
    def handle_immersion_command(self, user_id: str, args: list) -> Dict:
        """Handle /immersion [level] command"""
        
        if not args:
            consent = self.disclaimer_manager.get_user_preferences(user_id)
            if not consent:
                return {
                    'success': False,
                    'message': "Please complete onboarding first with /start"
                }
            
            current_level = consent.immersion_level
            return {
                'success': True,
                'message': f"""🎮 **Current Immersion Level: {current_level.title()}**

Available levels:
• **Full** - Maximum intensity, all features enabled
• **Moderate** - Balanced experience (recommended)
• **Minimal** - Just trading, minimal extras

Use `/immersion [full/moderate/minimal]` to change""",
                'parse_mode': 'Markdown'
            }
        
        level = args[0].lower()
        result = self.disclaimer_manager.set_immersion_level(user_id, level)
        
        if result.get('success'):
            level_descriptions = {
                'full': "🔥 **MAXIMUM TACTICAL IMMERSION**\n\n_All psychological systems engaged. Welcome to the deep end, soldier._",
                'moderate': "⚖️ **TACTICAL BALANCE PROTOCOL**\n\n_Optimized engagement parameters. Recommended for sustained operations._",
                'minimal': "🎯 **STEALTH TRADER MODE**\n\n_Minimal chatter. Maximum focus. Ghost protocol activated._"
            }
            
            return {
                'success': True,
                'message': level_descriptions.get(level, "Immersion level updated"),
                'parse_mode': 'Markdown'
            }
        else:
            return {
                'success': False,
                'message': result.get('message', 'Invalid immersion level')
            }
    
    def handle_settings_command(self, user_id: str) -> Dict:
        """Handle /settings command"""
        
        settings_menu = self.disclaimer_manager.get_settings_menu(user_id)
        
        if 'error' in settings_menu:
            return {
                'success': False,
                'message': "Please complete onboarding first with /start"
            }
        
        # Format settings for Telegram
        message = "⚙️ **BITTEN Settings**\n\n"
        
        for section in settings_menu['sections']:
            message += f"**{section['name']}**\n"
            message += f"_{section['description']}_\n\n"
            
            for control in section['controls']:
                if control['type'] == 'master_toggle':
                    status = "✅ ON" if control['current'] else "❌ OFF"
                    message += f"{control['label']}: {status}\n"
                elif control['type'] == 'bot_toggle':
                    if control['enabled']:
                        status = "✅" if control['current'] else "❌"
                    else:
                        status = "⏸️"
                    message += f"{status} {control['label']}\n"
                elif control['type'] == 'select':
                    message += f"{control['label']}: {control['current'].title()}\n"
                elif control['type'] == 'toggle':
                    status = "✅" if control['current'] else "❌"
                    message += f"{status} {control['label']}\n"
                elif control['type'] == 'info':
                    message += f"\n_{control['content']}_\n"
            
            message += "\n"
        
        # Add quick commands
        message += "**Quick Commands:**\n"
        message += "• `/bots on/off` - Toggle all bots\n"
        message += "• `/toggle [BotName]` - Toggle specific bot\n"
        message += "• `/immersion [level]` - Set immersion level\n"
        message += "• `/disclaimer` - View full disclaimer"
        
        return {
            'success': True,
            'message': message,
            'parse_mode': 'Markdown',
            'reply_markup': self.disclaimer_manager.format_bot_control_buttons()
        }
    
    def check_bot_permission(self, user_id: str, bot_name: str) -> bool:
        """Check if bot is allowed to message user"""
        return self.disclaimer_manager.check_bot_permission(user_id, bot_name)
    
    def get_user_consent(self, user_id: str) -> Optional[Dict]:
        """Get user's consent status"""
        consent = self.disclaimer_manager.get_user_preferences(user_id)
        if consent:
            return {
                'disclaimer_accepted': consent.disclaimer_accepted,
                'bots_enabled': consent.bots_enabled,
                'immersion_level': consent.immersion_level,
                'bot_preferences': consent.bot_preferences
            }
        return None
    
    def handle_onboarding_disclaimer(self, user_id: str, accepted: bool, preferences: Dict) -> Dict:
        """Handle disclaimer acceptance during onboarding"""
        
        if not accepted:
            return {
                'success': False,
                'message': "You must accept the disclaimer to use BITTEN.",
                'exit_onboarding': True
            }
        
        # Record consent
        consent = self.disclaimer_manager.accept_disclaimer(user_id, preferences)
        
        welcome_message = "✅ **TACTICAL ENGAGEMENT CONFIRMED**\n\n"
        welcome_message += "🎯 **BITTEN ACTUAL Online**\n\n"
        
        if consent.bots_enabled:
            welcome_message += "🤖 **Bot Squad:** ACTIVE\n"
            welcome_message += "_Toggle with /bots • Individual control with /toggle_\n\n"
        else:
            welcome_message += "🤖 **Bot Squad:** STANDBY\n"
            welcome_message += "_Activate with /bots on_\n\n"
        
        welcome_message += f"🎮 **Immersion Protocol:** {consent.immersion_level.upper()}\n"
        welcome_message += "_Adjust tactical intensity with /immersion_\n\n"
        
        welcome_message += "**You're not just trading. You're training.**\n\n"
        welcome_message += "_Stay tactical, soldier._"
        
        return {
            'success': True,
            'message': welcome_message,
            'parse_mode': 'Markdown',
            'consent_recorded': True,
            'preferences': {
                'bots_enabled': consent.bots_enabled,
                'immersion_level': consent.immersion_level
            }
        }

# Integration functions for main bot

def should_show_bot_message(user_id: str, bot_name: str, bot_controls: TelegramBotControls) -> bool:
    """Check if bot should show message to user"""
    return bot_controls.check_bot_permission(user_id, bot_name)

def format_bot_message(message: str, bot_name: str, user_consent: Dict) -> str:
    """Format bot message based on user preferences"""
    
    if not user_consent or not user_consent.get('bots_enabled'):
        return None  # Don't show bot messages
    
    if not user_consent.get('bot_preferences', {}).get(bot_name, True):
        return None  # This specific bot is disabled
    
    # Adjust intensity based on immersion level
    immersion = user_consent.get('immersion_level', 'moderate')
    
    if immersion == 'minimal':
        # Tone down the message
        return f"_{bot_name}: {message}_"
    elif immersion == 'moderate':
        # Standard formatting
        return f"**{bot_name}:** {message}"
    else:  # full
        # Enhanced formatting
        return f"🔥 **{bot_name}:** {message} 🔥"

# Command registration helper
def register_bot_control_commands(router):
    """Register bot control commands with the router"""
    
    bot_controls = TelegramBotControls()
    
    # Add command handlers
    router.add_command('disclaimer', lambda u, a: bot_controls.handle_disclaimer_command(u))
    router.add_command('bots', lambda u, a: bot_controls.handle_bots_command(u, a))
    router.add_command('toggle', lambda u, a: bot_controls.handle_toggle_command(u, a))
    router.add_command('immersion', lambda u, a: bot_controls.handle_immersion_command(u, a))
    router.add_command('settings', lambda u, a: bot_controls.handle_settings_command(u))
    
    return bot_controls