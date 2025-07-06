"""
BITTEN Onboarding State Machine Orchestrator

Main controller for managing the 13-phase onboarding flow that transforms
new users into trained market operatives.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .session_manager import OnboardingSessionManager
from .dialogue_loader import DialogueLoader
from .validators import OnboardingValidators
from .handlers import OnboardingHandlers

logger = logging.getLogger(__name__)

# Move these to models.py to avoid circular import
class OnboardingState(Enum):
    """Enumeration of all onboarding states"""
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

@dataclass
class OnboardingSession:
    """Session data for tracking onboarding progress"""
    user_id: str
    telegram_id: int
    current_state: str
    state_data: Dict[str, Any]
    started_at: datetime
    last_activity: datetime
    completed_states: List[str]
    user_responses: Dict[str, Any]
    
    # User data collected during onboarding
    has_experience: Optional[bool] = None
    first_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    selected_theater: Optional[str] = None
    accepted_terms: bool = False
    broker_account_id: Optional[str] = None
    callsign: Optional[str] = None
    
    # Progress tracking
    completion_percentage: float = 0.0
    variant: str = "standard"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for persistence"""
        data = asdict(self)
        data['started_at'] = self.started_at.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OnboardingSession':
        """Create session from dictionary"""
        data['started_at'] = datetime.fromisoformat(data['started_at'])
        data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        return cls(**data)

class OnboardingOrchestrator:
    """Main orchestrator for the BITTEN onboarding system"""
    
    def __init__(self, persona_orchestrator=None, hud_webapp_url=None):
        self.session_manager = OnboardingSessionManager()
        self.dialogue_loader = DialogueLoader()
        self.validators = OnboardingValidators()
        self.handlers = OnboardingHandlers()
        self.handlers.validators = self.validators
        self.persona_orchestrator = persona_orchestrator
        self.hud_webapp_url = hud_webapp_url or "https://bitten.trading"
        
        # State transition mapping
        self.state_transitions = {
            OnboardingState.FIRST_CONTACT: OnboardingState.MARKET_WARFARE_INTRO,
            OnboardingState.MARKET_WARFARE_INTRO: OnboardingState.KNOWLEDGE_SOURCE,
            OnboardingState.KNOWLEDGE_SOURCE: OnboardingState.TRAINING_SETUP,
            OnboardingState.TRAINING_SETUP: OnboardingState.FIRST_MISSION,
            OnboardingState.FIRST_MISSION: OnboardingState.PATH_FORWARD,
            OnboardingState.PATH_FORWARD: OnboardingState.THEATER_SELECTION,
            OnboardingState.THEATER_SELECTION: OnboardingState.OATH_OF_ENLISTMENT,
            OnboardingState.OATH_OF_ENLISTMENT: OnboardingState.SECURE_LINK,
            OnboardingState.SECURE_LINK: OnboardingState.CALLSIGN_CREATION,
            OnboardingState.CALLSIGN_CREATION: OnboardingState.OPERATIONAL_INTERFACE,
            OnboardingState.OPERATIONAL_INTERFACE: OnboardingState.CORE_MANEUVERS,
            OnboardingState.CORE_MANEUVERS: OnboardingState.FIELD_MANUAL,
            OnboardingState.FIELD_MANUAL: OnboardingState.PERSONAL_RECORD,
            OnboardingState.PERSONAL_RECORD: OnboardingState.COMPLETE,
        }
        
        # Load dialogue content
        self.dialogue = self.dialogue_loader.load_dialogue()
        
        logger.info("BITTEN Onboarding Orchestrator initialized")
    
    async def start_onboarding(self, user_id: str, telegram_id: int, 
                              variant: str = "standard") -> Tuple[str, Dict[str, Any]]:
        """
        Start new onboarding session or resume existing one
        
        Returns:
            Tuple of (message_text, keyboard_markup)
        """
        try:
            # Check for existing session
            existing_session = await self.session_manager.load_session(user_id)
            
            if existing_session:
                logger.info(f"Resuming onboarding for user {user_id} at state {existing_session.current_state}")
                return await self.resume_session(existing_session)
            
            # Create new session
            session = OnboardingSession(
                user_id=user_id,
                telegram_id=telegram_id,
                current_state=OnboardingState.FIRST_CONTACT.value,
                state_data={},
                started_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                completed_states=[],
                user_responses={},
                variant=variant
            )
            
            # Save session
            await self.session_manager.save_session(session)
            
            # Track analytics
            await self._track_event("onboarding_started", {
                "user_id": user_id,
                "variant": variant,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Process first state
            return await self.process_state(session, OnboardingState.FIRST_CONTACT)
            
        except Exception as e:
            logger.error(f"Error starting onboarding for user {user_id}: {e}")
            return self._get_error_message("startup_error"), {}
    
    async def process_user_input(self, user_id: str, input_type: str, 
                               input_data: Any) -> Tuple[str, Dict[str, Any]]:
        """
        Process user input and advance through onboarding
        
        Args:
            user_id: User identifier
            input_type: Type of input (callback, text, etc.)
            input_data: The actual input data
            
        Returns:
            Tuple of (message_text, keyboard_markup)
        """
        try:
            # Load session
            session = await self.session_manager.load_session(user_id)
            if not session:
                return await self.start_onboarding(user_id, 0)
            
            # Update activity
            session.last_activity = datetime.utcnow()
            
            # Get current state
            current_state = OnboardingState(session.current_state)
            
            # Process input based on state
            result = await self.handlers.handle_input(
                session, current_state, input_type, input_data
            )
            
            if result.get('error'):
                return result['message'], result.get('keyboard', {})
            
            # Update session with response
            session.user_responses[f"{current_state.value}_{input_type}"] = input_data
            
            # Check if state is complete
            if result.get('advance_state'):
                return await self.advance_state(session, result.get('state_data', {}))
            
            # Save session
            await self.session_manager.save_session(session)
            
            return result['message'], result.get('keyboard', {})
            
        except Exception as e:
            logger.error(f"Error processing input for user {user_id}: {e}")
            return self._get_error_message("processing_error"), {}
    
    async def advance_state(self, session: OnboardingSession, 
                          state_data: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Advance to next state in onboarding flow
        
        Args:
            session: Current onboarding session
            state_data: Additional data from completed state
            
        Returns:
            Tuple of (message_text, keyboard_markup)
        """
        try:
            current_state = OnboardingState(session.current_state)
            
            # Mark current state as completed
            if current_state.value not in session.completed_states:
                session.completed_states.append(current_state.value)
            
            # Track completion
            await self._track_event("onboarding_state_completed", {
                "user_id": session.user_id,
                "state": current_state.value,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update state data
            if state_data:
                session.state_data.update(state_data)
            
            # Get next state
            next_state = self.state_transitions.get(current_state)
            if not next_state:
                # Onboarding complete
                return await self.complete_onboarding(session)
            
            # Update session
            session.current_state = next_state.value
            session.completion_percentage = (len(session.completed_states) / 14) * 100
            
            # Save session
            await self.session_manager.save_session(session)
            
            # Process next state
            return await self.process_state(session, next_state)
            
        except Exception as e:
            logger.error(f"Error advancing state for user {session.user_id}: {e}")
            return self._get_error_message("state_advance_error"), {}
    
    async def process_state(self, session: OnboardingSession, 
                          state: OnboardingState) -> Tuple[str, Dict[str, Any]]:
        """
        Process a specific onboarding state
        
        Args:
            session: Current onboarding session
            state: State to process
            
        Returns:
            Tuple of (message_text, keyboard_markup)
        """
        try:
            # Get state dialogue
            state_dialogue = self.dialogue.get('phases', {}).get(state.value, {})
            
            if not state_dialogue:
                logger.error(f"No dialogue found for state {state.value}")
                return self._get_error_message("dialogue_missing"), {}
            
            # Process state with persona system
            if self.persona_orchestrator:
                persona_response = await self.persona_orchestrator.get_response(
                    user_id=session.user_id,
                    event_type=f"onboarding_{state.value}",
                    context={
                        "state_data": session.state_data,
                        "user_responses": session.user_responses,
                        "completion_percentage": session.completion_percentage
                    }
                )
                
                if persona_response:
                    # Use persona response if available
                    message = persona_response.get('message', '')
                    keyboard = persona_response.get('keyboard', {})
                    return message, keyboard
            
            # Use dialogue content
            message = await self._format_dialogue_message(state_dialogue, session)
            keyboard = await self._create_state_keyboard(state, session)
            
            return message, keyboard
            
        except Exception as e:
            logger.error(f"Error processing state {state.value}: {e}")
            return self._get_error_message("state_processing_error"), {}
    
    async def resume_session(self, session: OnboardingSession) -> Tuple[str, Dict[str, Any]]:
        """
        Resume an existing onboarding session
        
        Args:
            session: Session to resume
            
        Returns:
            Tuple of (message_text, keyboard_markup)
        """
        try:
            # Check if session is expired
            if datetime.utcnow() - session.last_activity > timedelta(days=7):
                logger.info(f"Session expired for user {session.user_id}")
                await self.session_manager.archive_session(session.user_id)
                return await self.start_onboarding(session.user_id, session.telegram_id)
            
            # Create welcome back message
            current_state = OnboardingState(session.current_state)
            progress = f"{len(session.completed_states)}/14 phases completed"
            
            welcome_message = (
                f"🎖️ **Welcome back, recruit!**\n\n"
                f"📊 **Progress**: {progress} ({session.completion_percentage:.1f}%)\n"
                f"🎯 **Current Phase**: {current_state.value.replace('_', ' ').title()}\n\n"
                f"Ready to continue your training?"
            )
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🚀 Continue Training", "callback_data": "resume_continue"}],
                    [{"text": "📊 Show Progress", "callback_data": "show_progress"}],
                    [{"text": "🔄 Restart from Beginning", "callback_data": "restart_onboarding"}]
                ]
            }
            
            return welcome_message, keyboard
            
        except Exception as e:
            logger.error(f"Error resuming session: {e}")
            return self._get_error_message("resume_error"), {}
    
    async def complete_onboarding(self, session: OnboardingSession) -> Tuple[str, Dict[str, Any]]:
        """
        Complete onboarding and transition to main system
        
        Args:
            session: Completed onboarding session
            
        Returns:
            Tuple of (message_text, keyboard_markup)
        """
        try:
            # Mark as complete
            session.current_state = OnboardingState.COMPLETE.value
            session.completion_percentage = 100.0
            
            # Track completion
            await self._track_event("onboarding_completed", {
                "user_id": session.user_id,
                "total_duration": (datetime.utcnow() - session.started_at).total_seconds(),
                "theater_selected": session.selected_theater,
                "callsign": session.callsign,
                "variant": session.variant
            })
            
            # Create completion message
            completion_message = (
                f"🎖️ **MISSION ACCOMPLISHED, {session.callsign}!**\n\n"
                f"🎯 **Training Complete**: You've successfully completed Ground Zero\n"
                f"⚔️ **Theater**: {session.selected_theater}\n"
                f"🔥 **Status**: BITTEN operative ready for deployment\n\n"
                f"*\"Every mission begins with a plan. You've earned your place in the ranks.\"*\n"
                f"— **Sergeant Nexus**\n\n"
                f"Welcome to the BITTEN Network, operative. Your real training begins now."
            )
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🎯 Enter War Room", "callback_data": "enter_war_room"}],
                    [{"text": "📊 View Personal Record", "callback_data": "view_personal_record"}],
                    [{"text": "🎖️ Show Achievements", "callback_data": "show_achievements"}]
                ]
            }
            
            # Save callsign to database before archiving
            if session.callsign:
                try:
                    from ..database.connection import get_db_session
                    from ..database.models import UserProfile
                    
                    with get_db_session() as db_session:
                        # Check if profile exists
                        profile = db_session.query(UserProfile).filter(
                            UserProfile.user_id == session.telegram_id
                        ).first()
                        
                        if not profile:
                            # Create new profile with callsign
                            profile = UserProfile(
                                user_id=session.telegram_id,
                                callsign=session.callsign
                            )
                            db_session.add(profile)
                        else:
                            # Update existing profile
                            profile.callsign = session.callsign
                        
                        db_session.commit()
                        logger.info(f"Saved callsign '{session.callsign}' for user {session.telegram_id}")
                        
                except Exception as e:
                    logger.error(f"Error saving callsign to database: {e}")
            
            # Archive session
            await self.session_manager.archive_session(session.user_id)
            
            return completion_message, keyboard
            
        except Exception as e:
            logger.error(f"Error completing onboarding: {e}")
            return self._get_error_message("completion_error"), {}
    
    async def handle_command(self, user_id: str, command: str, 
                           args: List[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Handle onboarding-specific commands
        
        Args:
            user_id: User identifier
            command: Command to handle
            args: Optional command arguments
            
        Returns:
            Tuple of (message_text, keyboard_markup)
        """
        try:
            session = await self.session_manager.load_session(user_id)
            
            if command == "back":
                return await self._handle_back_command(session)
            elif command == "skip":
                return await self._handle_skip_command(session)
            elif command == "help":
                return await self._handle_help_command(session)
            elif command == "pause":
                return await self._handle_pause_command(session)
            elif command == "status":
                return await self._handle_status_command(session)
            else:
                return "Unknown command during onboarding.", {}
                
        except Exception as e:
            logger.error(f"Error handling command {command}: {e}")
            return self._get_error_message("command_error"), {}
    
    async def _format_dialogue_message(self, state_dialogue: Dict[str, Any], 
                                     session: OnboardingSession) -> str:
        """Format dialogue message with dynamic variables"""
        # Get the message text
        message = state_dialogue.get('message', '')
        
        # Variable replacements
        replacements = {
            '{NAME}': session.first_name or 'Recruit',
            '{CALLSIGN}': session.callsign or 'Soldier',
            '{THEATER}': session.selected_theater or 'Training',
            '{EXPERIENCE}': 'veteran' if session.has_experience else 'recruit',
            '{USER_ID}': str(session.telegram_id),
        }
        
        # Replace all variables
        for var, value in replacements.items():
            message = message.replace(var, value)
        
        return message
    
    async def _create_state_keyboard(self, state: OnboardingState, 
                                   session: OnboardingSession) -> Dict[str, Any]:
        """Create AAA-quality keyboards with amazing UX for each state"""
        
        # Show progress bar at top of every keyboard
        progress = self._calculate_progress(session)
        progress_bar = self.handlers.format_progress_bar(progress['current'], progress['total'])
        
        keyboard = {"inline_keyboard": []}
        
        if state == OnboardingState.FIRST_CONTACT:
            keyboard["inline_keyboard"] = [
                [{"text": "✅ Yes, I've traded before", "callback_data": "onboarding_yes"}],
                [{"text": "🌟 No, I'm new to this", "callback_data": "onboarding_no"}]
            ]
            
        elif state == OnboardingState.KNOWLEDGE_SOURCE:
            keyboard["inline_keyboard"] = [
                [{"text": "👥 Friend told me", "callback_data": "onboarding_friend"}],
                [{"text": "📺 YouTube/Social Media", "callback_data": "onboarding_youtube"}],
                [{"text": "📖 Article/Blog", "callback_data": "onboarding_article"}],
                [{"text": "🌐 Other", "callback_data": "onboarding_other"}]
            ]
            
        elif state == OnboardingState.THEATER_SELECTION:
            keyboard["inline_keyboard"] = [
                [{"text": "🎮 DEMO (Practice Mode)", "callback_data": "onboarding_demo"}],
                [{"text": "💰 LIVE (Real Money)", "callback_data": "onboarding_live"}]
            ]
            
        elif state == OnboardingState.OATH_OF_ENLISTMENT:
            keyboard["inline_keyboard"] = [
                [{"text": "🎖️ I ACCEPT THE OATH", "callback_data": "onboarding_accept_oath"}],
                [{"text": "📖 Read Again", "callback_data": "onboarding_read_oath"}]
            ]
            
        elif state == OnboardingState.SECURE_LINK:
            keyboard["inline_keyboard"] = [
                [{"text": "🔗 Connect Broker", "callback_data": "onboarding_connect_broker"}],
                [{"text": "⏭️ Do This Later", "callback_data": "onboarding_skip_broker"}]
            ]
            
        elif state == OnboardingState.CALLSIGN_CREATION:
            # For text input states, show helpful buttons
            keyboard["inline_keyboard"] = [
                [{"text": "🎲 Generate Random", "callback_data": "onboarding_random_callsign"}],
                [{"text": "💡 Show Examples", "callback_data": "onboarding_callsign_examples"}]
            ]
            
        elif state == OnboardingState.OPERATIONAL_INTERFACE:
            keyboard["inline_keyboard"] = [
                [{"text": "📱 Open Trading HUD", "url": self.hud_webapp_url if self.hud_webapp_url else "https://bitten.trading"}],
                [{"text": "➡️ Continue Tour", "callback_data": "onboarding_continue"}]
            ]
            
        elif state == OnboardingState.CORE_MANEUVERS:
            keyboard["inline_keyboard"] = [
                [{"text": "🎯 Understood!", "callback_data": "onboarding_understood"}],
                [{"text": "🔄 Explain Again", "callback_data": "onboarding_explain_again"}]
            ]
            
        elif state == OnboardingState.FIELD_MANUAL:
            keyboard["inline_keyboard"] = [
                [{"text": "📚 View Field Manual", "callback_data": "onboarding_view_manual"}],
                [{"text": "✅ Ready to Start", "callback_data": "onboarding_ready"}]
            ]
            
        elif state == OnboardingState.PERSONAL_RECORD:
            keyboard["inline_keyboard"] = [
                [{"text": "🔔 All Notifications", "callback_data": "onboarding_all"}],
                [{"text": "📌 Essential Only", "callback_data": "onboarding_essential"}],
                [{"text": "⚙️ Custom Setup", "callback_data": "onboarding_custom"}]
            ]
            
        else:
            # Default continue button
            keyboard["inline_keyboard"] = [
                [{"text": "➡️ Continue", "callback_data": "onboarding_continue"}]
            ]
        
        # Add navigation row at bottom (except for critical states)
        if state not in [OnboardingState.FIRST_CONTACT, OnboardingState.COMPLETE]:
            nav_row = []
            
            # Back button (if allowed)
            back_button = self.handlers.get_back_button(state.value)
            if back_button:
                nav_row.append(back_button)
            
            # Help button (always available)
            nav_row.append({"text": "❓ Help", "callback_data": "onboarding_help"})
            
            # Skip button (if allowed)
            skip_button = self.handlers.get_skip_button(state.value)
            if skip_button:
                nav_row.append(skip_button)
            
            if nav_row:
                keyboard["inline_keyboard"].append(nav_row)
        
        # Add progress indicator as last row
        keyboard["inline_keyboard"].append([
            {"text": progress_bar, "callback_data": "onboarding_progress"}
        ])
        
        return keyboard
    
    async def _handle_back_command(self, session: OnboardingSession) -> Tuple[str, Dict[str, Any]]:
        """Handle back command"""
        pass
    
    async def _handle_skip_command(self, session: OnboardingSession) -> Tuple[str, Dict[str, Any]]:
        """Handle skip command"""
        pass
    
    async def _handle_help_command(self, session: OnboardingSession) -> Tuple[str, Dict[str, Any]]:
        """Handle help command"""
        pass
    
    async def _handle_pause_command(self, session: OnboardingSession) -> Tuple[str, Dict[str, Any]]:
        """Handle pause command"""
        pass
    
    async def _handle_status_command(self, session: OnboardingSession) -> Tuple[str, Dict[str, Any]]:
        """Handle status command"""
        pass
    
    async def _track_event(self, event_type: str, data: Dict[str, Any]):
        """Track analytics event"""
        try:
            logger.info(f"Tracking event: {event_type} - {data}")
            # Implementation would send to analytics system
        except Exception as e:
            logger.error(f"Error tracking event {event_type}: {e}")
    
    def _get_error_message(self, error_type: str) -> str:
        """Get appropriate error message"""
        error_messages = {
            "startup_error": "🚨 **Tactical Error**: Unable to initialize training. Support notified.",
            "processing_error": "⚠️ **System Malfunction**: Unable to process command. Try again, recruit.",
            "state_advance_error": "🔧 **Navigation Error**: Unable to advance. Your progress is saved.",
            "dialogue_missing": "📡 **Communication Error**: Training manual corrupted. Standby for repair.",
            "state_processing_error": "🛠️ **Processing Error**: System hiccup detected. Retrying...",
            "resume_error": "🔄 **Resume Error**: Unable to restore session. Starting fresh.",
            "completion_error": "🎖️ **Completion Error**: Error during graduation. Contact command.",
            "command_error": "❌ **Command Error**: Invalid operation. Try again, operative."
        }
        
        return error_messages.get(error_type, "🚨 **Unknown Error**: Contact support immediately.")
    
    def _calculate_progress(self, session: OnboardingSession) -> Dict[str, int]:
        """Calculate onboarding progress"""
        # Get all states except COMPLETE
        all_states = [s for s in OnboardingState if s != OnboardingState.COMPLETE]
        
        # Find current state index
        try:
            current_index = all_states.index(OnboardingState(session.current_state))
            current_step = current_index + 1
        except (ValueError, KeyError):
            current_step = 1
        
        return {
            'current': current_step,
            'total': len(all_states)
        }