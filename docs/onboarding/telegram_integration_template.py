"""
BITTEN Onboarding - Telegram Bot Integration Template
This template shows how to integrate the onboarding flow with a Telegram bot
"""

from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

logger = logging.getLogger(__name__)

# Load dialogue from JSON
with open('docs/onboarding/onboarding_dialogue.json', 'r') as f:
    DIALOGUE = json.load(f)

class OnboardingState(Enum):
    """Onboarding flow states"""
    FIRST_CONTACT = "first_contact"
    MARKET_WARFARE_INTRO = "market_warfare_intro"
    KNOWLEDGE_SOURCE = "knowledge_source"
    TRAINING_SETUP = "training_setup"
    FIRST_MISSION = "first_mission"
    PATH_FORWARD = "path_forward"
    THEATER_SELECTION = "theater_selection"
    OATH_OF_ENLISTMENT = "oath_of_enlistment"
    SECURE_LINK = "secure_link"
    CALLSIGN_CREATION = "callsign_creation"
    OPERATIONAL_INTERFACE = "operational_interface"
    CORE_MANEUVERS = "core_maneuvers"
    FIELD_MANUAL = "field_manual"
    PERSONAL_RECORD = "personal_record"
    COMPLETE = "complete"

class OnboardingHandlers:
    """Handles all onboarding-related commands and callbacks"""
    
    def __init__(self, persona_orchestrator):
        self.persona_orchestrator = persona_orchestrator
        self.sessions = {}  # user_id -> session data
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - begin or resume onboarding"""
        user_id = str(update.effective_user.id)
        
        # Check for existing session
        if user_id in self.sessions:
            await self.resume_onboarding(update, context)
        else:
            await self.begin_onboarding(update, context)
    
    async def begin_onboarding(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start new onboarding session"""
        user_id = str(update.effective_user.id)
        
        # Initialize session
        self.sessions[user_id] = {
            'state': OnboardingState.FIRST_CONTACT.value,
            'started_at': datetime.now().isoformat(),
            'data': {},
            'responses': {}
        }
        
        # Get first contact dialogue
        phase = DIALOGUE['phases']['first_contact']
        
        # Create inline keyboard for YES/NO
        keyboard = [
            [
                InlineKeyboardButton("YES", callback_data="experience_yes"),
                InlineKeyboardButton("NO", callback_data="experience_no")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send Sergeant Nexus opening
        message = (
            f"**Sergeant Nexus:**\n"
            f"{phase['nexus_opening']}"
        )
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def handle_experience_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle YES/NO response about trading experience"""
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        # Acknowledge callback
        await query.answer()
        
        # Get response
        has_experience = query.data == "experience_yes"
        self.sessions[user_id]['data']['has_experience'] = has_experience
        
        # Get appropriate response
        phase = DIALOGUE['phases']['first_contact']
        response = phase['responses']['yes' if has_experience else 'no']
        
        # Send response and continue
        nexus_intro = phase['nexus_intro']
        hook_lines = '\n'.join(phase['universal_hook'])
        
        message = (
            f"**Sergeant Nexus:** {response}\n\n"
            f"{nexus_intro}\n\n"
            f"{hook_lines}"
        )
        
        # Add continue button
        keyboard = [[InlineKeyboardButton("Ready for deployment", callback_data="continue_market_intro")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Update state
        self.sessions[user_id]['state'] = OnboardingState.MARKET_WARFARE_INTRO.value
    
    async def show_market_demo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show market warfare demonstration"""
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        await query.answer()
        
        phase = DIALOGUE['phases']['market_warfare_intro']
        
        # Build explanation message
        explanation = '\n'.join(phase['nexus_explains'])
        
        message = (
            f"**Sergeant Nexus:**\n"
            f"{explanation}\n\n"
            f"{phase['training_moment']['setup']}\n"
            f"_{phase['training_moment']['explanation']}_\n\n"
            f"{phase['training_moment']['countdown']}"
        )
        
        # Add ENGAGE button
        keyboard = [[InlineKeyboardButton("🎯 ENGAGE NOW!", callback_data="execute_demo")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def handle_callsign_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callsign text input"""
        user_id = str(update.effective_user.id)
        
        # Check if we're in callsign creation state
        if (user_id not in self.sessions or 
            self.sessions[user_id]['state'] != OnboardingState.CALLSIGN_CREATION.value):
            return
        
        callsign = update.message.text.strip()
        
        # Validate callsign
        validation = DIALOGUE['callsign_validation']
        
        if len(callsign) < validation['min_length']:
            await update.message.reply_text(validation['error_messages']['too_short'])
            return
        
        if len(callsign) > validation['max_length']:
            await update.message.reply_text(validation['error_messages']['too_long'])
            return
        
        # Check pattern
        import re
        if not re.match(validation['allowed_pattern'], callsign):
            await update.message.reply_text(validation['error_messages']['invalid_chars'])
            return
        
        # Check reserved words
        if callsign.lower() in validation['reserved_words']:
            await update.message.reply_text(validation['error_messages']['reserved'])
            return
        
        # TODO: Check uniqueness against database
        
        # Accept callsign
        self.sessions[user_id]['data']['callsign'] = callsign
        
        # Send success message
        phase = DIALOGUE['phases']['operational_interface']
        welcome = phase['nexus_welcome'][0].replace('{CALLSIGN}', callsign)
        
        message = (
            f"**Sergeant Nexus:**\n"
            f"{welcome}\n\n"
            f"Your BITTEN identity is now active. Prepare for tactical deployment!"
        )
        
        # Add menu buttons for next phase
        keyboard = [
            [InlineKeyboardButton("📊 View Command Center", callback_data="show_interface")],
            [InlineKeyboardButton("🎯 Begin Training", callback_data="start_training")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Update state
        self.sessions[user_id]['state'] = OnboardingState.OPERATIONAL_INTERFACE.value
    
    async def handle_back_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /back command during onboarding"""
        user_id = str(update.effective_user.id)
        
        if user_id not in self.sessions:
            await update.message.reply_text("No active onboarding session found.")
            return
        
        current_state = self.sessions[user_id]['state']
        
        # Define back navigation
        back_map = {
            OnboardingState.MARKET_WARFARE_INTRO.value: OnboardingState.FIRST_CONTACT.value,
            OnboardingState.KNOWLEDGE_SOURCE.value: OnboardingState.MARKET_WARFARE_INTRO.value,
            OnboardingState.TRAINING_SETUP.value: OnboardingState.KNOWLEDGE_SOURCE.value,
            # Add more mappings as needed
        }
        
        if current_state in back_map:
            self.sessions[user_id]['state'] = back_map[current_state]
            await self.show_current_state(update, context)
        else:
            await update.message.reply_text("Cannot go back from this step.")
    
    async def show_current_state(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display the current onboarding state to user"""
        user_id = str(update.effective_user.id)
        session = self.sessions[user_id]
        state = session['state']
        
        # Route to appropriate handler based on state
        if state == OnboardingState.FIRST_CONTACT.value:
            await self.begin_onboarding(update, context)
        elif state == OnboardingState.MARKET_WARFARE_INTRO.value:
            await self.show_market_demo(update, context)
        # Add more state handlers...
    
    def register_handlers(self, application: Application):
        """Register all onboarding handlers with the bot"""
        # Commands
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("back", self.handle_back_command))
        
        # Callback queries
        application.add_handler(CallbackQueryHandler(
            self.handle_experience_response,
            pattern="^experience_(yes|no)$"
        ))
        application.add_handler(CallbackQueryHandler(
            self.show_market_demo,
            pattern="^continue_market_intro$"
        ))
        
        # Message handlers for text input
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_callsign_input
        ))

# Example integration with main bot
def setup_onboarding(application: Application, persona_orchestrator):
    """Setup onboarding handlers in the main bot"""
    onboarding = OnboardingHandlers(persona_orchestrator)
    onboarding.register_handlers(application)
    return onboarding

# Usage in main bot file:
"""
from telegram.ext import Application
from bitten_core.persona_system import PersonaOrchestrator

# Initialize bot
application = Application.builder().token(BOT_TOKEN).build()

# Initialize personas
persona_orchestrator = PersonaOrchestrator()

# Setup onboarding
onboarding = setup_onboarding(application, persona_orchestrator)

# Start bot
application.run_polling()
"""