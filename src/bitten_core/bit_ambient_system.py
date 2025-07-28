"""
BITTEN Bit Ambient System - Master Integration
Complete ambient audio system that brings Bit the cat to life throughout the BITTEN experience
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# Import all audio system components
from .ambient_audio_system import (
    ambient_audio_engine, 
    TradingContext, 
    AudioMood,
    start_ambient_audio,
    stop_ambient_audio
)
from .audio_triggers import (
    audio_trigger_manager,
    trigger_trading_event,
    trigger_market_event,
    start_audio_triggers,
    stop_audio_triggers
)
from .bit_memory_audio import (
    bit_memory_audio_engine,
    MemoryTrigger,
    trigger_memory_audio,
    comfort_user_with_memory,
    celebrate_with_memory
)
from .mississippi_ambient import (
    mississippi_ambient_engine,
    start_delta_ambience,
    stop_delta_ambience,
    trigger_storm_warning,
    trigger_calm_after_storm,
    play_sunday_bells
)
from .trading_audio_feedback import (
    trading_audio_feedback_engine,
    provide_entry_feedback,
    provide_outcome_feedback
)
from .audio_notification_integration import (
    audio_notification_integrator,
    start_user_audio_session,
    stop_user_audio_session,
    get_user_audio_status
)
from .audio_configuration import (
    bit_audio_config_manager,
    get_user_audio_config,
    update_audio_config,
    apply_audio_preset,
    should_play_audio
)
from .norman_story_integration import norman_story_engine, StoryPhase

logger = logging.getLogger(__name__)

class BitAmbientSystem:
    """
    Master class for Bit's Ambient Audio System
    
    This is the main interface for integrating Bit's presence throughout
    the BITTEN trading experience. It orchestrates all audio subsystems
    to create a cohesive, immersive companion experience.
    """
    
    def __init__(self):
        self.is_initialized = False
        self.active_users: Dict[str, Dict] = {}
        self.system_stats = {
            'users_with_audio': 0,
            'total_audio_events': 0,
            'memory_sequences_played': 0,
            'ambient_sessions_active': 0
        }
    
    async def initialize(self) -> bool:
        """Initialize the complete Bit ambient system"""
        
        try:
            logger.info("Initializing Bit's Ambient Audio System...")
            
            # Start core systems
            start_ambient_audio()
            start_audio_triggers()
            
            self.is_initialized = True
            
            logger.info("✅ Bit's Ambient Audio System initialized successfully")
            logger.info("🐱 Bit is now ready to accompany traders on their journey")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Bit's Ambient Audio System: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the ambient system gracefully"""
        
        try:
            logger.info("Shutting down Bit's Ambient Audio System...")
            
            # Stop all user sessions
            for user_id in list(self.active_users.keys()):
                await self.stop_user_session(user_id)
            
            # Stop core systems
            stop_ambient_audio()
            stop_audio_triggers()
            
            self.is_initialized = False
            
            logger.info("👋 Bit's Ambient Audio System shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    # User Session Management
    async def start_user_session(self, user_id: str, context: Optional[Dict] = None) -> bool:
        """
        Start a complete audio session for a user
        
        This begins Bit's companionship for the trading session, including:
        - Ambient environmental sounds
        - Mood-responsive audio
        - Trading feedback
        - Memory-based interactions
        """
        
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Check if user already has an active session
            if user_id in self.active_users:
                return True
            
            # Get user's audio configuration
            audio_config = get_user_audio_config(user_id)
            
            # Check if user has audio enabled
            if not should_play_audio(user_id, ambient_audio_engine.audio_clips['greeting_chirp'].audio_type):
                logger.info(f"Audio disabled for user {user_id}")
                return False
            
            # Start the session
            session_data = {
                'start_time': datetime.now(),
                'audio_events_count': 0,
                'last_interaction': datetime.now(),
                'story_phase': norman_story_engine.get_user_story_context(user_id).current_phase,
                'mood': AudioMood.CONTENT,
                'ambient_active': False
            }
            
            # Initialize Bit's state for this user
            bit_state = ambient_audio_engine.get_bit_state(user_id)
            
            # Start ambient environment if enabled
            if audio_config.mississippi_ambient_enabled:
                ambient_id = await start_delta_ambience(user_id, context or {})
                session_data['ambient_active'] = bool(ambient_id)
            
            # Play greeting based on time of day and story phase
            await self._play_session_greeting(user_id, session_data['story_phase'])
            
            # Store session
            self.active_users[user_id] = session_data
            self.system_stats['users_with_audio'] += 1
            
            logger.info(f"🐱 Started Bit's audio session for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start audio session for {user_id}: {e}")
            return False
    
    async def stop_user_session(self, user_id: str) -> bool:
        """Stop a user's audio session gracefully"""
        
        try:
            if user_id not in self.active_users:
                return True
            
            # Play farewell based on story phase
            story_phase = self.active_users[user_id].get('story_phase', StoryPhase.EARLY_STRUGGLE)
            await self._play_session_farewell(user_id, story_phase)
            
            # Stop ambient audio
            await stop_delta_ambience(user_id)
            
            # Clean up session
            del self.active_users[user_id]
            self.system_stats['users_with_audio'] = max(0, self.system_stats['users_with_audio'] - 1)
            
            logger.info(f"👋 Stopped Bit's audio session for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop audio session for {user_id}: {e}")
            return False
    
    # Trading Event Integration
    async def on_trade_signal(self, user_id: str, signal_data: Dict[str, Any]) -> Optional[str]:
        """Handle incoming trading signal"""
        
        if not self._is_user_active(user_id):
            return None
        
        # Trigger signal audio
        await trigger_trading_event(user_id, 'signal_received', signal_data)
        
        # Update user interaction
        self._update_user_interaction(user_id)
        
        return "signal_audio_triggered"
    
    async def on_trade_opened(self, user_id: str, trade_data: Dict[str, Any]) -> Optional[str]:
        """Handle trade opening"""
        
        if not self._is_user_active(user_id):
            return None
        
        # Provide entry feedback
        tcs_score = trade_data.get('tcs_score', 80)
        risk_percentage = trade_data.get('risk_percentage', 2.0)
        
        feedback_events = await provide_entry_feedback(
            user_id, tcs_score, risk_percentage, trade_data
        )
        
        # Trigger trade opened event
        await trigger_trading_event(user_id, 'trade_opened', trade_data)
        
        self._update_user_interaction(user_id)
        
        return f"trade_opened_feedback_{len(feedback_events)}_events"
    
    async def on_trade_closed(self, user_id: str, result_data: Dict[str, Any]) -> Optional[str]:
        """Handle trade closing"""
        
        if not self._is_user_active(user_id):
            return None
        
        profit_pips = result_data.get('profit_pips', 0)
        profit_currency = result_data.get('profit_currency', 0)
        
        # Provide outcome feedback
        outcome_event = await provide_outcome_feedback(user_id, profit_pips, profit_currency)
        
        # Trigger appropriate memory if significant result
        if profit_pips > 30:
            # Big win - celebrate
            await celebrate_with_memory(user_id, 'big_win')
        elif profit_pips < -20:
            # Significant loss - comfort
            await comfort_user_with_memory(user_id, abs(profit_currency))
        
        # Update Bit's mood based on result
        if profit_pips > 0:
            ambient_audio_engine.update_bit_mood(user_id, AudioMood.EXCITED, "profitable_trade")
        else:
            ambient_audio_engine.update_bit_mood(user_id, AudioMood.CAUTIOUS, "loss_trade")
        
        self._update_user_interaction(user_id)
        
        return f"trade_closed_outcome_{outcome_event}"
    
    async def on_achievement_unlocked(self, user_id: str, achievement_data: Dict[str, Any]) -> Optional[str]:
        """Handle achievement unlocks"""
        
        if not self._is_user_active(user_id):
            return None
        
        achievement_type = achievement_data.get('type', 'general')
        
        # Celebrate with appropriate memory
        memory_event = await celebrate_with_memory(user_id, achievement_type)
        
        # Update mood to excited
        ambient_audio_engine.update_bit_mood(user_id, AudioMood.EXCITED, "achievement_unlocked")
        
        self._update_user_interaction(user_id)
        
        return f"achievement_celebration_{memory_event}"
    
    async def on_risk_warning(self, user_id: str, risk_data: Dict[str, Any]) -> Optional[str]:
        """Handle risk warnings"""
        
        if not self._is_user_active(user_id):
            return None
        
        risk_level = risk_data.get('risk_level', 'medium')
        
        # Trigger danger sensing memory for high risk
        if risk_level in ['high', 'critical']:
            memory_event = await bit_memory_audio_engine.play_memory_sequence(
                user_id, MemoryTrigger.DANGER_SENSING
            )
        
        # Update mood to worried
        ambient_audio_engine.update_bit_mood(user_id, AudioMood.WORRIED, "risk_warning")
        
        # Trigger warning audio
        await trigger_trading_event(user_id, 'risk_warning', risk_data)
        
        self._update_user_interaction(user_id)
        
        return f"risk_warning_triggered_{risk_level}"
    
    # Market Event Integration
    async def on_market_open(self, user_ids: List[str], market_data: Optional[Dict] = None) -> Dict[str, str]:
        """Handle market opening for multiple users"""
        
        results = {}
        
        for user_id in user_ids:
            if self._is_user_active(user_id):
                # Morning greeting and market open audio
                await trigger_memory_audio(user_id, MemoryTrigger.MORNING_GREETING, {})
                event_id = await trigger_market_event(user_id, 'market_open', market_data or {})
                results[user_id] = f"market_open_{event_id}"
        
        return results
    
    async def on_market_close(self, user_ids: List[str], market_data: Optional[Dict] = None) -> Dict[str, str]:
        """Handle market closing for multiple users"""
        
        results = {}
        
        for user_id in user_ids:
            if self._is_user_active(user_id):
                # Evening settling audio
                await trigger_memory_audio(user_id, MemoryTrigger.EVENING_SETTLE, {})
                event_id = await trigger_market_event(user_id, 'market_close', market_data or {})
                results[user_id] = f"market_close_{event_id}"
        
        return results
    
    async def on_high_volatility(self, user_ids: List[str], volatility_data: Dict[str, Any]) -> Dict[str, str]:
        """Handle high volatility periods"""
        
        results = {}
        
        for user_id in user_ids:
            if self._is_user_active(user_id):
                # Storm warning audio
                storm_event = await trigger_storm_warning(user_id)
                
                # Update Bit's mood to alert
                ambient_audio_engine.update_bit_mood(user_id, AudioMood.ALERT, "high_volatility")
                
                results[user_id] = f"volatility_warning_{storm_event}"
        
        return results
    
    async def on_market_calm(self, user_ids: List[str]) -> Dict[str, str]:
        """Handle return to market calm"""
        
        results = {}
        
        for user_id in user_ids:
            if self._is_user_active(user_id):
                # Calm after storm audio
                calm_event = await trigger_calm_after_storm(user_id)
                
                # Update Bit's mood to content
                ambient_audio_engine.update_bit_mood(user_id, AudioMood.CONTENT, "market_calm")
                
                results[user_id] = f"market_calm_{calm_event}"
        
        return results
    
    # User Configuration
    def get_user_audio_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user's complete audio preferences"""
        
        config = get_user_audio_config(user_id)
        status = get_user_audio_status(user_id)
        
        return {
            'config': {
                'audio_quality': config.audio_quality.value,
                'focus_mode': config.focus_mode.value,
                'master_volume': config.master_volume,
                'bit_personality_enabled': config.bit_chirps_enabled,
                'ambient_environment_enabled': config.mississippi_ambient_enabled,
                'trading_feedback_enabled': config.trading_feedback_enabled,
                'memory_audio_enabled': config.bit_memory_audio_enabled
            },
            'status': status,
            'session_active': user_id in self.active_users,
            'available_presets': bit_audio_config_manager.get_available_presets()
        }
    
    def update_user_audio_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user's audio preferences"""
        
        updated_config = update_audio_config(user_id, preferences)
        
        # If user has active session, apply changes immediately
        if user_id in self.active_users:
            # Update session based on new preferences
            if not updated_config.mississippi_ambient_enabled:
                asyncio.create_task(stop_delta_ambience(user_id))
            elif updated_config.mississippi_ambient_enabled and not self.active_users[user_id].get('ambient_active'):
                asyncio.create_task(start_delta_ambience(user_id))
        
        return {
            'success': True,
            'updated_preferences': self.get_user_audio_preferences(user_id)
        }
    
    def apply_audio_preset_to_user(self, user_id: str, preset_name: str) -> Dict[str, Any]:
        """Apply an audio preset to user"""
        
        try:
            updated_config = apply_audio_preset(user_id, preset_name)
            
            return {
                'success': True,
                'preset_applied': preset_name,
                'new_preferences': self.get_user_audio_preferences(user_id)
            }
            
        except ValueError as e:
            return {
                'success': False,
                'error': str(e),
                'available_presets': bit_audio_config_manager.get_available_presets()
            }
    
    # System Monitoring
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        
        return {
            'initialized': self.is_initialized,
            'active_users': len(self.active_users),
            'system_stats': self.system_stats.copy(),
            'engine_stats': {
                'ambient_engine': ambient_audio_engine.get_audio_statistics('system'),
                'mississippi_engine': mississippi_ambient_engine.get_ambient_statistics('system'),
                'trigger_manager': audio_trigger_manager.get_trigger_statistics('system')
            }
        }
    
    def get_user_session_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed session information for user"""
        
        if user_id not in self.active_users:
            return None
        
        session = self.active_users[user_id]
        
        # Get stats from various engines
        ambient_stats = ambient_audio_engine.get_audio_statistics(user_id)
        memory_stats = bit_memory_audio_engine.get_memory_statistics(user_id)
        mississippi_stats = mississippi_ambient_engine.get_ambient_statistics(user_id)
        feedback_stats = trading_audio_feedback_engine.get_feedback_statistics(user_id)
        
        return {
            'session': {
                'duration_minutes': (datetime.now() - session['start_time']).total_seconds() / 60,
                'audio_events_count': session['audio_events_count'],
                'current_mood': session['mood'].value,
                'story_phase': session['story_phase'].value,
                'ambient_active': session['ambient_active']
            },
            'audio_stats': ambient_stats,
            'memory_stats': memory_stats,
            'ambient_stats': mississippi_stats,
            'feedback_stats': feedback_stats
        }
    
    # Helper methods
    def _is_user_active(self, user_id: str) -> bool:
        """Check if user has an active audio session"""
        return user_id in self.active_users
    
    def _update_user_interaction(self, user_id: str):
        """Update user's last interaction time"""
        if user_id in self.active_users:
            self.active_users[user_id]['last_interaction'] = datetime.now()
            self.active_users[user_id]['audio_events_count'] += 1
            self.system_stats['total_audio_events'] += 1
    
    async def _play_session_greeting(self, user_id: str, story_phase: StoryPhase):
        """Play appropriate session greeting"""
        
        hour = datetime.now().hour
        
        if 6 <= hour <= 10:
            # Morning greeting
            await trigger_memory_audio(user_id, MemoryTrigger.MORNING_GREETING, {})
        elif story_phase in [StoryPhase.EARLY_STRUGGLE, StoryPhase.AWAKENING]:
            # Encouraging greeting for beginners
            await ambient_audio_engine.play_contextual_audio(
                user_id, TradingContext.MARKET_OPEN, AudioMood.CONTENT
            )
        else:
            # Standard greeting
            await ambient_audio_engine.play_contextual_audio(
                user_id, TradingContext.MARKET_OPEN, AudioMood.ALERT
            )
    
    async def _play_session_farewell(self, user_id: str, story_phase: StoryPhase):
        """Play appropriate session farewell"""
        
        hour = datetime.now().hour
        
        if 18 <= hour <= 22:
            # Evening farewell
            await trigger_memory_audio(user_id, MemoryTrigger.EVENING_SETTLE, {})
        else:
            # Standard farewell
            await ambient_audio_engine.play_contextual_audio(
                user_id, TradingContext.MARKET_CLOSE, AudioMood.CONTENT
            )

# Global instance - the main interface to Bit's ambient system
bit_ambient_system = BitAmbientSystem()

# Convenience functions for easy integration
async def start_bit_for_user(user_id: str, context: Optional[Dict] = None) -> bool:
    """Start Bit's companionship for a user"""
    return await bit_ambient_system.start_user_session(user_id, context)

async def stop_bit_for_user(user_id: str) -> bool:
    """Stop Bit's companionship for a user"""
    return await bit_ambient_system.stop_user_session(user_id)

async def bit_reacts_to_trade(user_id: str, trade_event: str, data: Dict[str, Any]) -> Optional[str]:
    """Make Bit react to trading events"""
    
    event_handlers = {
        'signal': bit_ambient_system.on_trade_signal,
        'opened': bit_ambient_system.on_trade_opened,
        'closed': bit_ambient_system.on_trade_closed,
        'achievement': bit_ambient_system.on_achievement_unlocked,
        'risk_warning': bit_ambient_system.on_risk_warning
    }
    
    handler = event_handlers.get(trade_event)
    if handler:
        return await handler(user_id, data)
    
    return None

def get_bit_status_for_user(user_id: str) -> Dict[str, Any]:
    """Get Bit's status and preferences for user"""
    return bit_ambient_system.get_user_audio_preferences(user_id)

def configure_bit_for_user(user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
    """Configure Bit's behavior for user"""
    return bit_ambient_system.update_user_audio_preferences(user_id, preferences)

async def initialize_bit_system() -> bool:
    """Initialize the complete Bit ambient system"""
    return await bit_ambient_system.initialize()

async def shutdown_bit_system():
    """Shutdown the Bit ambient system"""
    await bit_ambient_system.shutdown()