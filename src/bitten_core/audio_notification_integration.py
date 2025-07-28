"""
BITTEN Audio Notification Integration
Integrates Bit's ambient audio system with existing notification handlers
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass

from .ambient_audio_system import ambient_audio_engine, TradingContext, AudioMood
from .audio_triggers import audio_trigger_manager, trigger_trading_event, trigger_market_event
from .bit_memory_audio import bit_memory_audio_engine, MemoryTrigger, trigger_memory_audio
from .mississippi_ambient import mississippi_ambient_engine, start_delta_ambience
from .trading_audio_feedback import trading_audio_feedback_engine, provide_entry_feedback, provide_outcome_feedback
from .notification_handler import notification_handler, NotificationType, Notification
from .user_settings import get_user_settings

logger = logging.getLogger(__name__)

@dataclass
class AudioNotificationMapping:
    """Maps notification types to audio responses"""
    notification_type: NotificationType
    audio_context: Optional[TradingContext] = None
    memory_trigger: Optional[MemoryTrigger] = None
    enable_feedback: bool = False
    enable_ambient: bool = False
    priority_modifier: int = 0

class AudioNotificationIntegrator:
    """Integrates audio system with existing notifications"""
    
    def __init__(self):
        self.notification_mappings: Dict[NotificationType, AudioNotificationMapping] = {}
        self.audio_handlers: Dict[str, Callable] = {}
        self.user_audio_sessions: Dict[str, Dict] = {}
        
        # Setup integration
        self._setup_notification_mappings()
        self._register_audio_handlers()
        self._integrate_with_notification_handler()
    
    def _setup_notification_mappings(self):
        """Setup mappings between notifications and audio responses"""
        
        mappings = {
            NotificationType.TP_HIT: AudioNotificationMapping(
                notification_type=NotificationType.TP_HIT,
                audio_context=TradingContext.PROFIT_TARGET,
                memory_trigger=MemoryTrigger.VICTORY_STRETCH,
                enable_feedback=True,
                priority_modifier=2
            ),
            
            NotificationType.SL_HIT: AudioNotificationMapping(
                notification_type=NotificationType.SL_HIT,
                audio_context=TradingContext.STOP_LOSS,
                memory_trigger=MemoryTrigger.COMFORT_PRESENCE,
                enable_feedback=True,
                priority_modifier=1
            ),
            
            NotificationType.SIGNAL: AudioNotificationMapping(
                notification_type=NotificationType.SIGNAL,
                audio_context=TradingContext.SIGNAL_RECEIVED,
                enable_feedback=True,
                priority_modifier=1
            ),
            
            NotificationType.TRADE_OPEN: AudioNotificationMapping(
                notification_type=NotificationType.TRADE_OPEN,
                audio_context=TradingContext.TRADE_OPENED,
                enable_feedback=True
            ),
            
            NotificationType.TRADE_CLOSE: AudioNotificationMapping(
                notification_type=NotificationType.TRADE_CLOSE,
                audio_context=TradingContext.TRADE_CLOSED,
                enable_feedback=True
            ),
            
            NotificationType.ACHIEVEMENT: AudioNotificationMapping(
                notification_type=NotificationType.ACHIEVEMENT,
                memory_trigger=MemoryTrigger.VICTORY_STRETCH,
                enable_feedback=True,
                priority_modifier=2
            ),
            
            NotificationType.WARNING: AudioNotificationMapping(
                notification_type=NotificationType.WARNING,
                audio_context=TradingContext.RISK_WARNING,
                memory_trigger=MemoryTrigger.DANGER_SENSING,
                enable_feedback=True,
                priority_modifier=3
            ),
            
            NotificationType.XP_GAIN: AudioNotificationMapping(
                notification_type=NotificationType.XP_GAIN,
                enable_feedback=True
            )
        }
        
        self.notification_mappings.update(mappings)
    
    def _register_audio_handlers(self):
        """Register audio handlers for different event types"""
        
        self.audio_handlers = {
            'tp_hit': self._handle_tp_hit_audio,
            'sl_hit': self._handle_sl_hit_audio,
            'signal_received': self._handle_signal_audio,
            'trade_opened': self._handle_trade_opened_audio,
            'trade_closed': self._handle_trade_closed_audio,
            'achievement': self._handle_achievement_audio,
            'warning': self._handle_warning_audio,
            'xp_gain': self._handle_xp_gain_audio,
            'user_login': self._handle_user_login_audio,
            'user_logout': self._handle_user_logout_audio,
            'market_open': self._handle_market_open_audio,
            'market_close': self._handle_market_close_audio,
            'session_milestone': self._handle_session_milestone_audio
        }
    
    def _integrate_with_notification_handler(self):
        """Integrate with the existing notification handler"""
        
        # Register our audio processor with the notification handler
        notification_handler.register_handler('audio_processor', self._process_notification_for_audio)
    
    async def _process_notification_for_audio(self, notification: Notification):
        """Process notification and trigger appropriate audio"""
        
        try:
            # Check if user has audio enabled
            user_settings = get_user_settings(notification.user_id)
            if not user_settings.sounds_enabled:
                return
            
            # Get mapping for this notification type
            mapping = self.notification_mappings.get(notification.notification_type)
            if not mapping:
                return
            
            # Create audio session context
            audio_context = {
                'notification': notification,
                'mapping': mapping,
                'user_settings': user_settings,
                'timestamp': datetime.now()
            }
            
            # Process audio response
            await self._execute_audio_response(notification.user_id, audio_context)
            
        except Exception as e:
            logger.error(f"Error processing notification audio for {notification.user_id}: {e}")
    
    async def _execute_audio_response(self, user_id: str, context: Dict[str, Any]):
        """Execute the audio response for a notification"""
        
        notification = context['notification']
        mapping = context['mapping']
        
        # Start ambient environment if needed
        if mapping.enable_ambient and user_id not in self.user_audio_sessions:
            await self._start_user_audio_session(user_id)
        
        # Trigger contextual audio
        if mapping.audio_context:
            await ambient_audio_engine.play_contextual_audio(
                user_id=user_id,
                context=mapping.audio_context,
                metadata={
                    'notification_id': f"{notification.user_id}_{notification.timestamp.timestamp()}",
                    'notification_type': notification.type.value,
                    'priority': notification.priority + mapping.priority_modifier
                }
            )
        
        # Trigger memory audio if appropriate
        if mapping.memory_trigger:
            await bit_memory_audio_engine.play_memory_sequence(
                user_id=user_id,
                trigger=mapping.memory_trigger
            )
        
        # Process feedback if enabled
        if mapping.enable_feedback:
            await self._process_trading_feedback(user_id, notification)
        
        # Trigger event-based systems
        await self._trigger_event_systems(user_id, notification)
    
    async def _start_user_audio_session(self, user_id: str):
        """Start ambient audio session for user"""
        
        # Start ambient environment
        ambient_id = await start_delta_ambience(user_id)
        
        # Initialize audio session tracking
        self.user_audio_sessions[user_id] = {
            'start_time': datetime.now(),
            'ambient_id': ambient_id,
            'events_triggered': 0,
            'last_activity': datetime.now()
        }
        
        # Trigger morning greeting if appropriate
        hour = datetime.now().hour
        if 6 <= hour <= 10:
            await bit_memory_audio_engine.play_memory_sequence(
                user_id, MemoryTrigger.MORNING_GREETING
            )
        
        logger.info(f"Started audio session for user {user_id}")
    
    async def _process_trading_feedback(self, user_id: str, notification: Notification):
        """Process trading feedback for notifications"""
        
        notification_data = notification.data
        
        if notification.type == NotificationType.TP_HIT:
            profit_pips = notification_data.get('profit_pips', 0)
            await provide_outcome_feedback(user_id, profit_pips)
        
        elif notification.type == NotificationType.SL_HIT:
            loss_pips = -abs(notification_data.get('loss_pips', 0))
            await provide_outcome_feedback(user_id, loss_pips)
        
        elif notification.type == NotificationType.TRADE_OPEN:
            tcs_score = notification_data.get('tcs_score', 80)
            risk_pct = notification_data.get('risk_percentage', 2.0)
            await provide_entry_feedback(user_id, tcs_score, risk_pct, {})
    
    async def _trigger_event_systems(self, user_id: str, notification: Notification):
        """Trigger audio event systems"""
        
        # Map notification to event type
        event_type_map = {
            NotificationType.TP_HIT: 'trade_closed',
            NotificationType.SL_HIT: 'trade_closed',
            NotificationType.SIGNAL: 'signal_received',
            NotificationType.TRADE_OPEN: 'trade_opened',
            NotificationType.ACHIEVEMENT: 'achievement_unlocked',
            NotificationType.WARNING: 'risk_warning'
        }
        
        event_type = event_type_map.get(notification.type)
        if event_type:
            await trigger_trading_event(user_id, event_type, notification.data)
    
    # Specific audio handlers
    async def _handle_tp_hit_audio(self, user_id: str, data: Dict[str, Any]) -> List[str]:
        """Handle take profit hit audio"""
        events = []
        
        profit_amount = data.get('profit_currency', 0)
        profit_pips = data.get('profit_pips', 0)
        
        # Victory celebration based on profit size
        if profit_amount > 200 or profit_pips > 50:
            # Big win - major celebration
            event_id = await bit_memory_audio_engine.play_memory_sequence(
                user_id, MemoryTrigger.VICTORY_STRETCH
            )
            if event_id:
                events.append(event_id)
        else:
            # Normal win - standard celebration
            event_id = await ambient_audio_engine.play_contextual_audio(
                user_id, TradingContext.PROFIT_TARGET, AudioMood.EXCITED
            )
            if event_id:
                events.append(event_id)
        
        return events
    
    async def _handle_sl_hit_audio(self, user_id: str, data: Dict[str, Any]) -> List[str]:
        """Handle stop loss hit audio"""
        events = []
        
        loss_amount = abs(data.get('loss_currency', 0))
        
        # Comfort response based on loss size
        if loss_amount > 100:
            # Significant loss - memory comfort
            event_id = await bit_memory_audio_engine.play_memory_sequence(
                user_id, MemoryTrigger.HARD_NIGHT
            )
        else:
            # Normal loss - gentle comfort
            event_id = await bit_memory_audio_engine.play_memory_sequence(
                user_id, MemoryTrigger.COMFORT_PRESENCE
            )
        
        if event_id:
            events.append(event_id)
        
        return events
    
    async def _handle_signal_audio(self, user_id: str, data: Dict[str, Any]) -> List[str]:
        """Handle signal received audio"""
        events = []
        
        signal_strength = data.get('strength', 'medium')
        
        # Alert level based on signal strength
        if signal_strength == 'strong':
            mood = AudioMood.EXCITED
        elif signal_strength == 'weak':
            mood = AudioMood.CAUTIOUS
        else:
            mood = AudioMood.ALERT
        
        event_id = await ambient_audio_engine.play_contextual_audio(
            user_id, TradingContext.SIGNAL_RECEIVED, mood
        )
        
        if event_id:
            events.append(event_id)
        
        return events
    
    async def _handle_trade_opened_audio(self, user_id: str, data: Dict[str, Any]) -> List[str]:
        """Handle trade opened audio"""
        events = []
        
        # Confirmation chirp for trade execution
        event_id = await ambient_audio_engine.play_contextual_audio(
            user_id, TradingContext.TRADE_OPENED, AudioMood.CONFIDENT
        )
        
        if event_id:
            events.append(event_id)
        
        return events
    
    async def _handle_trade_closed_audio(self, user_id: str, data: Dict[str, Any]) -> List[str]:
        """Handle trade closed audio"""
        events = []
        
        result = data.get('result', 'neutral')
        
        if result == 'profit':
            mood = AudioMood.CONTENT
        elif result == 'loss':
            mood = AudioMood.CALM
        else:
            mood = AudioMood.CONTENT
        
        event_id = await ambient_audio_engine.play_contextual_audio(
            user_id, TradingContext.TRADE_CLOSED, mood
        )
        
        if event_id:
            events.append(event_id)
        
        return events
    
    async def _handle_achievement_audio(self, user_id: str, data: Dict[str, Any]) -> List[str]:
        """Handle achievement unlocked audio"""
        events = []
        
        achievement_type = data.get('type', 'general')
        
        # Special memory for first achievements
        if 'first' in achievement_type.lower():
            event_id = await bit_memory_audio_engine.play_memory_sequence(
                user_id, MemoryTrigger.FIRST_WIN
            )
        else:
            event_id = await bit_memory_audio_engine.play_memory_sequence(
                user_id, MemoryTrigger.VICTORY_STRETCH
            )
        
        if event_id:
            events.append(event_id)
        
        return events
    
    async def _handle_warning_audio(self, user_id: str, data: Dict[str, Any]) -> List[str]:
        """Handle warning notification audio"""
        events = []
        
        severity = data.get('severity', 'medium')
        
        # Warning level based on severity
        if severity == 'critical':
            # Danger sensing memory
            event_id = await bit_memory_audio_engine.play_memory_sequence(
                user_id, MemoryTrigger.DANGER_SENSING
            )
        else:
            # Standard warning
            event_id = await ambient_audio_engine.play_contextual_audio(
                user_id, TradingContext.RISK_WARNING, AudioMood.CAUTIOUS
            )
        
        if event_id:
            events.append(event_id)
        
        return events
    
    async def _handle_xp_gain_audio(self, user_id: str, data: Dict[str, Any]) -> List[str]:
        """Handle XP gain audio"""
        events = []
        
        xp_amount = data.get('xp_amount', 0)
        
        # Celebration level based on XP amount
        if xp_amount >= 100:
            event_id = await ambient_audio_engine.play_contextual_audio(
                user_id, TradingContext.PROFIT_TARGET, AudioMood.EXCITED
            )
        else:
            event_id = await ambient_audio_engine.play_contextual_audio(
                user_id, TradingContext.PROFIT_TARGET, AudioMood.CONTENT
            )
        
        if event_id:
            events.append(event_id)
        
        return events
    
    async def _handle_user_login_audio(self, user_id: str, data: Dict[str, Any]) -> List[str]:
        """Handle user login audio"""
        events = []
        
        # Start audio session
        await self._start_user_audio_session(user_id)
        
        # Morning greeting
        event_id = await bit_memory_audio_engine.play_memory_sequence(
            user_id, MemoryTrigger.MORNING_GREETING
        )
        
        if event_id:
            events.append(event_id)
        
        return events
    
    async def _handle_user_logout_audio(self, user_id: str, data: Dict[str, Any]) -> List[str]:
        """Handle user logout audio"""
        events = []
        
        # Evening settling
        event_id = await bit_memory_audio_engine.play_memory_sequence(
            user_id, MemoryTrigger.EVENING_SETTLE
        )
        
        if event_id:
            events.append(event_id)
        
        # Stop ambient audio
        await mississippi_ambient_engine.stop_ambient_environment(user_id)
        
        # Clean up session
        if user_id in self.user_audio_sessions:
            del self.user_audio_sessions[user_id]
        
        return events
    
    async def _handle_market_open_audio(self, user_id: str, data: Dict[str, Any]) -> List[str]:
        """Handle market open audio"""
        events = []
        
        event_id = await trigger_market_event(user_id, 'market_open', data)
        if event_id:
            events.extend(event_id)
        
        return events
    
    async def _handle_market_close_audio(self, user_id: str, data: Dict[str, Any]) -> List[str]:
        """Handle market close audio"""
        events = []
        
        event_id = await trigger_market_event(user_id, 'market_close', data)
        if event_id:
            events.extend(event_id)
        
        return events
    
    async def _handle_session_milestone_audio(self, user_id: str, data: Dict[str, Any]) -> List[str]:
        """Handle session milestone audio"""
        events = []
        
        milestone_type = data.get('type', 'time')
        
        if milestone_type == 'time':
            # Time-based milestone
            event_id = await ambient_audio_engine.play_contextual_audio(
                user_id, TradingContext.LOW_VOLATILITY, AudioMood.CONTENT
            )
        
        if event_id:
            events.append(event_id)
        
        return events
    
    # Public API methods
    async def trigger_audio_event(self, user_id: str, event_type: str, data: Dict[str, Any] = None) -> List[str]:
        """Trigger audio event manually"""
        
        handler = self.audio_handlers.get(event_type)
        if handler:
            return await handler(user_id, data or {})
        
        logger.warning(f"No audio handler found for event type: {event_type}")
        return []
    
    def update_user_audio_activity(self, user_id: str):
        """Update user's audio activity timestamp"""
        
        if user_id in self.user_audio_sessions:
            self.user_audio_sessions[user_id]['last_activity'] = datetime.now()
            self.user_audio_sessions[user_id]['events_triggered'] += 1
    
    def get_audio_session_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get audio session information for user"""
        
        session = self.user_audio_sessions.get(user_id)
        if not session:
            return None
        
        duration = (datetime.now() - session['start_time']).total_seconds()
        
        return {
            'session_duration': duration,
            'events_triggered': session['events_triggered'],
            'last_activity': session['last_activity'].isoformat(),
            'ambient_active': session.get('ambient_id') is not None
        }
    
    def get_integration_statistics(self) -> Dict[str, Any]:
        """Get integration statistics"""
        
        active_sessions = len(self.user_audio_sessions)
        total_handlers = len(self.audio_handlers)
        total_mappings = len(self.notification_mappings)
        
        return {
            'active_audio_sessions': active_sessions,
            'registered_handlers': total_handlers,
            'notification_mappings': total_mappings,
            'integration_active': True
        }

# Global instance
audio_notification_integrator = AudioNotificationIntegrator()

# Convenience functions for external use
async def trigger_audio_notification(user_id: str, notification_type: NotificationType, 
                                   data: Dict[str, Any] = None) -> List[str]:
    """Trigger audio for a notification type"""
    
    # Create a mock notification
    from .notification_handler import Notification
    
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title="Manual Audio Trigger",
        message="",
        timestamp=datetime.now(),
        data=data or {}
    )
    
    # Process it through our audio system
    await audio_notification_integrator._process_notification_for_audio(notification)
    
    return []  # Event IDs would be tracked internally

async def start_user_audio_session(user_id: str) -> bool:
    """Start audio session for user"""
    
    try:
        await audio_notification_integrator._start_user_audio_session(user_id)
        return True
    except Exception as e:
        logger.error(f"Failed to start audio session for {user_id}: {e}")
        return False

async def stop_user_audio_session(user_id: str) -> bool:
    """Stop audio session for user"""
    
    try:
        await audio_notification_integrator._handle_user_logout_audio(user_id, {})
        return True
    except Exception as e:
        logger.error(f"Failed to stop audio session for {user_id}: {e}")
        return False

def get_user_audio_status(user_id: str) -> Dict[str, Any]:
    """Get user's audio status"""
    
    session_info = audio_notification_integrator.get_audio_session_info(user_id)
    user_settings = get_user_settings(user_id)
    
    return {
        'audio_enabled': user_settings.sounds_enabled,
        'session_active': session_info is not None,
        'session_info': session_info,
        'ambient_system_active': ambient_audio_engine.bit_states.get(user_id) is not None
    }