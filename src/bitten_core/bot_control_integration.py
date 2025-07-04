# bot_control_integration.py
# INTEGRATION MODULE FOR BOT CONTROLS WITH MAIN SYSTEM
# Connects disclaimer management and bot controls to the trading system

from typing import Dict, Optional, Any
from .telegram_router import TelegramRouter, TelegramUpdate, CommandResult
from .telegram_bot_controls import TelegramBotControls, should_show_bot_message, format_bot_message
from .psyops.disclaimer_manager import DisclaimerManager
from .psyops.psyops_orchestrator import MasterPsyOpsOrchestrator

class BotControlIntegration:
    """Integrates bot controls with main BITTEN system"""
    
    def __init__(self, telegram_router: TelegramRouter = None, bitten_core = None):
        self.telegram_router = telegram_router
        self.bitten_core = bitten_core
        self.bot_controls = TelegramBotControls()
        self.disclaimer_manager = self.bot_controls.disclaimer_manager
        self.psyops_orchestrator = None  # Initialize when ready
        
        # Register commands with router if provided
        if self.telegram_router:
            self._register_commands()
    
    def _register_commands(self):
        """Register bot control commands with telegram router"""
        
        # Add new command handlers to the router's command routing
        router = self.telegram_router
        
        # Store original route command method
        original_route = router._route_command
        
        def enhanced_route_command(command: str, args: list, update: TelegramUpdate) -> CommandResult:
            """Enhanced routing that includes bot control commands"""
            
            # Check bot control commands first
            if command == '/disclaimer':
                result = self.bot_controls.handle_disclaimer_command(str(update.user_id))
                return CommandResult(
                    success=result.get('success', True),
                    message=result.get('message', ''),
                    data=result
                )
            elif command == '/bots':
                result = self.bot_controls.handle_bots_command(str(update.user_id), args)
                return CommandResult(
                    success=result.get('success', True),
                    message=result.get('message', ''),
                    data=result
                )
            elif command == '/toggle':
                result = self.bot_controls.handle_toggle_command(str(update.user_id), args)
                return CommandResult(
                    success=result.get('success', True),
                    message=result.get('message', ''),
                    data=result
                )
            elif command == '/immersion':
                result = self.bot_controls.handle_immersion_command(str(update.user_id), args)
                return CommandResult(
                    success=result.get('success', True),
                    message=result.get('message', ''),
                    data=result
                )
            elif command == '/settings':
                result = self.bot_controls.handle_settings_command(str(update.user_id))
                return CommandResult(
                    success=result.get('success', True),
                    message=result.get('message', ''),
                    data=result
                )
            
            # Fall back to original routing
            return original_route(command, args, update)
        
        # Replace the route method
        router._route_command = enhanced_route_command
        
        # Update command categories
        router.command_categories['Bot Controls'] = [
            'disclaimer', 'bots', 'toggle', 'immersion', 'settings'
        ]
    
    def check_user_consent(self, user_id: str) -> Dict:
        """Check if user has accepted disclaimer and configured preferences"""
        
        consent = self.bot_controls.get_user_consent(str(user_id))
        
        if not consent:
            return {
                'has_consent': False,
                'needs_onboarding': True,
                'message': 'Please complete onboarding with /start'
            }
        
        return {
            'has_consent': True,
            'disclaimer_accepted': consent['disclaimer_accepted'],
            'bots_enabled': consent['bots_enabled'],
            'immersion_level': consent['immersion_level'],
            'bot_preferences': consent['bot_preferences']
        }
    
    def format_bot_message_for_user(self, user_id: str, bot_name: str, message: str) -> Optional[str]:
        """Format bot message based on user preferences"""
        
        # Check if bot is allowed
        if not self.bot_controls.check_bot_permission(str(user_id), bot_name):
            return None
        
        # Get user consent for formatting
        consent = self.bot_controls.get_user_consent(str(user_id))
        if not consent:
            return None
        
        # Format message based on preferences
        return format_bot_message(message, bot_name, consent)
    
    def handle_onboarding_disclaimer(self, user_id: str, accepted: bool, preferences: Dict) -> Dict:
        """Handle disclaimer during onboarding process"""
        
        result = self.bot_controls.handle_onboarding_disclaimer(
            str(user_id), accepted, preferences
        )
        
        # If accepted, initialize PsyOps if enabled
        if result.get('success') and preferences.get('bots_enabled', True):
            # This would be called after PsyOps questions
            pass
        
        return result
    
    def get_bot_status_for_display(self, user_id: str) -> str:
        """Get formatted bot status for display in other commands"""
        
        consent = self.bot_controls.get_user_consent(str(user_id))
        
        if not consent:
            return "🤖 Bot Status: Not configured (/settings)"
        
        if not consent['bots_enabled']:
            return "🤖 Bot Status: ❌ OFF (/bots on to enable)"
        
        enabled_count = sum(1 for enabled in consent['bot_preferences'].values() if enabled)
        total_count = len(consent['bot_preferences'])
        
        return f"🤖 Bot Status: ✅ ON ({enabled_count}/{total_count} active)"
    
    def should_show_system_message(self, user_id: str, message_type: str) -> bool:
        """Check if system message should be shown based on immersion level"""
        
        consent = self.bot_controls.get_user_consent(str(user_id))
        if not consent:
            return True  # Show all messages if not configured
        
        immersion = consent.get('immersion_level', 'moderate')
        
        # Message type filters based on immersion
        if immersion == 'minimal':
            # Only show essential messages
            essential_types = ['trade_result', 'error', 'critical_alert']
            return message_type in essential_types
        elif immersion == 'moderate':
            # Show most messages except purely atmospheric
            excluded_types = ['atmosphere', 'lore', 'deep_narrative']
            return message_type not in excluded_types
        else:  # full
            # Show everything
            return True
    
    def get_command_descriptions(self) -> Dict[str, str]:
        """Get bot control command descriptions for help system"""
        
        return {
            'disclaimer': 'View system disclaimer and terms',
            'bots': 'Toggle all AI bot personalities on/off',
            'toggle': 'Toggle individual bot on/off',
            'immersion': 'Set experience intensity level',
            'settings': 'View and manage all bot settings'
        }
    
    def inject_bot_status_into_message(self, user_id: str, original_message: str) -> str:
        """Inject bot status into existing messages where appropriate"""
        
        # Only inject into certain message types
        if any(keyword in original_message.lower() for keyword in ['status', 'settings', 'welcome']):
            bot_status = self.get_bot_status_for_display(user_id)
            
            # Find appropriate place to inject
            if "**System Health:**" in original_message:
                # Inject into status message
                original_message = original_message.replace(
                    "**System Health:**",
                    f"**System Health:**\n{bot_status}\n"
                )
            elif original_message.endswith("\n"):
                # Append to end
                original_message += f"\n{bot_status}"
            else:
                # Append with newlines
                original_message += f"\n\n{bot_status}"
        
        return original_message

# Integration helper for BiTTEN Core
def create_bot_control_integration(telegram_router: TelegramRouter = None, 
                                 bitten_core = None) -> BotControlIntegration:
    """Create and configure bot control integration"""
    
    integration = BotControlIntegration(telegram_router, bitten_core)
    
    # Add command descriptions to router if available
    if telegram_router and hasattr(telegram_router, '_get_command_description'):
        original_get_desc = telegram_router._get_command_description
        
        def enhanced_get_description(command: str) -> str:
            # Check bot control commands first
            bot_descriptions = integration.get_command_descriptions()
            if command in bot_descriptions:
                return bot_descriptions[command]
            # Fall back to original
            return original_get_desc(command)
        
        telegram_router._get_command_description = enhanced_get_description
    
    return integration

# Middleware for bot message filtering
class BotMessageMiddleware:
    """Middleware to filter bot messages based on user preferences"""
    
    def __init__(self, integration: BotControlIntegration):
        self.integration = integration
    
    def process_outgoing_message(self, user_id: str, message: Dict) -> Optional[Dict]:
        """Process outgoing message, filtering based on preferences"""
        
        # Check message type
        if message.get('type') == 'bot_message':
            bot_name = message.get('bot_name')
            content = message.get('content')
            
            if not bot_name or not content:
                return message
            
            # Format message based on preferences
            formatted = self.integration.format_bot_message_for_user(
                user_id, bot_name, content
            )
            
            if formatted is None:
                # Bot is disabled for this user
                return None
            
            # Update message content
            message['content'] = formatted
        
        # Check system messages
        elif message.get('type') == 'system_message':
            message_subtype = message.get('subtype', 'general')
            
            if not self.integration.should_show_system_message(user_id, message_subtype):
                return None
        
        # Inject bot status where appropriate
        if 'content' in message and isinstance(message['content'], str):
            message['content'] = self.integration.inject_bot_status_into_message(
                user_id, message['content']
            )
        
        return message