"""
BITTEN Audio Triggers System
Handles automated audio triggers based on market conditions, user actions, and trading events
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .ambient_audio_system import ambient_audio_engine, TradingContext, AudioMood
from .norman_story_integration import norman_story_engine, StoryPhase
from .user_settings import get_user_settings

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Types of audio triggers"""
    TIME_BASED = "time_based"
    EVENT_BASED = "event_based"
    CONDITION_BASED = "condition_based"
    USER_ACTION = "user_action"
    MARKET_STATE = "market_state"


class MarketCondition(Enum):
    """Market conditions that trigger audio"""
    MARKET_OPENING = "market_opening"
    MARKET_CLOSING = "market_closing"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    CONSOLIDATION = "consolidation"
    NEWS_RELEASE = "news_release"
    WEEKEND_APPROACH = "weekend_approach"


@dataclass
class AudioTrigger:
    """Represents an audio trigger configuration"""
    trigger_id: str
    trigger_type: TriggerType
    name: str
    description: str
    condition_check: Callable[[str, Dict], bool]
    audio_context: TradingContext
    audio_mood: Optional[AudioMood]
    cooldown_minutes: int = 5
    priority: int = 5
    enabled: bool = True


class AudioTriggerManager:
    """Manages automated audio triggers for trading events"""
    
    def __init__(self):
        self.triggers: Dict[str, AudioTrigger] = {}
        self.user_trigger_history: Dict[str, List[Dict]] = {}
        self.is_monitoring = False
        self.monitor_task = None
        
        # Initialize all triggers
        self._setup_market_triggers()
        self._setup_trading_triggers()
        self._setup_emotional_triggers()
        self._setup_story_progression_triggers()
        self._setup_time_based_triggers()
    
    def _setup_market_triggers(self):
        """Setup market condition-based triggers"""
        
        market_triggers = [
            AudioTrigger(
                trigger_id="market_open_morning",
                trigger_type=TriggerType.TIME_BASED,
                name="Market Opening Bell",
                description="Bit greets the start of trading day",
                condition_check=self._check_market_opening,
                audio_context=TradingContext.MARKET_OPEN,
                audio_mood=AudioMood.ALERT,
                cooldown_minutes=480,  # Once per session
                priority=6
            ),
            AudioTrigger(
                trigger_id="market_close_evening",
                trigger_type=TriggerType.TIME_BASED,
                name="Market Closing",
                description="Bit settles down as markets close",
                condition_check=self._check_market_closing,
                audio_context=TradingContext.MARKET_CLOSE,
                audio_mood=AudioMood.CONTENT,
                cooldown_minutes=480,
                priority=5
            ),
            AudioTrigger(
                trigger_id="high_volatility_alert",
                trigger_type=TriggerType.MARKET_STATE,
                name="High Volatility Alert",
                description="Bit becomes alert during volatile periods",
                condition_check=self._check_high_volatility,
                audio_context=TradingContext.HIGH_VOLATILITY,
                audio_mood=AudioMood.ALERT,
                cooldown_minutes=15,
                priority=7
            ),
            AudioTrigger(
                trigger_id="low_volatility_calm",
                trigger_type=TriggerType.MARKET_STATE,
                name="Low Volatility Calm",
                description="Bit relaxes during quiet market periods",
                condition_check=self._check_low_volatility,
                audio_context=TradingContext.LOW_VOLATILITY,
                audio_mood=AudioMood.SLEEPY,
                cooldown_minutes=30,
                priority=3
            ),
            AudioTrigger(
                trigger_id="news_event_attention",
                trigger_type=TriggerType.EVENT_BASED,
                name="News Event Alert",
                description="Bit alerts to important news releases",
                condition_check=self._check_news_event,
                audio_context=TradingContext.NEWS_EVENT,
                audio_mood=AudioMood.CURIOUS,
                cooldown_minutes=5,
                priority=8
            )
        ]
        
        for trigger in market_triggers:
            self.triggers[trigger.trigger_id] = trigger
    
    def _setup_trading_triggers(self):
        """Setup trading action-based triggers"""
        
        trading_triggers = [
            AudioTrigger(
                trigger_id="signal_received",
                trigger_type=TriggerType.EVENT_BASED,
                name="Signal Received",
                description="Bit reacts to incoming trading signals",
                condition_check=self._check_signal_received,
                audio_context=TradingContext.SIGNAL_RECEIVED,
                audio_mood=AudioMood.ALERT,
                cooldown_minutes=1,
                priority=7
            ),
            AudioTrigger(
                trigger_id="trade_opened",
                trigger_type=TriggerType.EVENT_BASED,
                name="Trade Opened",
                description="Bit acknowledges trade execution",
                condition_check=self._check_trade_opened,
                audio_context=TradingContext.TRADE_OPENED,
                audio_mood=AudioMood.CONFIDENT,
                cooldown_minutes=2,
                priority=6
            ),
            AudioTrigger(
                trigger_id="profit_target_hit",
                trigger_type=TriggerType.EVENT_BASED,
                name="Profit Target Hit",
                description="Bit celebrates successful trades",
                condition_check=self._check_profit_target,
                audio_context=TradingContext.PROFIT_TARGET,
                audio_mood=AudioMood.EXCITED,
                cooldown_minutes=1,
                priority=9
            ),
            AudioTrigger(
                trigger_id="stop_loss_hit",
                trigger_type=TriggerType.EVENT_BASED,
                name="Stop Loss Hit",
                description="Bit provides comfort after losses",
                condition_check=self._check_stop_loss,
                audio_context=TradingContext.STOP_LOSS,
                audio_mood=AudioMood.CAUTIOUS,
                cooldown_minutes=5,
                priority=8
            ),
            AudioTrigger(
                trigger_id="breakeven_reached",
                trigger_type=TriggerType.EVENT_BASED,
                name="Breakeven Reached",
                description="Bit acknowledges risk-free status",
                condition_check=self._check_breakeven,
                audio_context=TradingContext.BREAKEVEN,
                audio_mood=AudioMood.CONTENT,
                cooldown_minutes=3,
                priority=5
            ),
            AudioTrigger(
                trigger_id="risk_warning_triggered",
                trigger_type=TriggerType.CONDITION_BASED,
                name="Risk Warning",
                description="Bit warns about risky trading decisions",
                condition_check=self._check_risk_warning,
                audio_context=TradingContext.RISK_WARNING,
                audio_mood=AudioMood.WORRIED,
                cooldown_minutes=10,
                priority=8
            )
        ]
        
        for trigger in trading_triggers:
            self.triggers[trigger.trigger_id] = trigger
    
    def _setup_emotional_triggers(self):
        """Setup emotion-based triggers tied to user state"""
        
        emotional_triggers = [
            AudioTrigger(
                trigger_id="winning_streak",
                trigger_type=TriggerType.CONDITION_BASED,
                name="Winning Streak",
                description="Bit celebrates consecutive wins",
                condition_check=self._check_winning_streak,
                audio_context=TradingContext.PROFIT_TARGET,
                audio_mood=AudioMood.EXCITED,
                cooldown_minutes=30,
                priority=7
            ),
            AudioTrigger(
                trigger_id="losing_streak_comfort",
                trigger_type=TriggerType.CONDITION_BASED,
                name="Losing Streak Comfort",
                description="Bit provides comfort during difficult periods",
                condition_check=self._check_losing_streak,
                audio_context=TradingContext.STOP_LOSS,
                audio_mood=AudioMood.WORRIED,
                cooldown_minutes=20,
                priority=8
            ),
            AudioTrigger(
                trigger_id="achievement_unlocked",
                trigger_type=TriggerType.EVENT_BASED,
                name="Achievement Unlocked",
                description="Bit celebrates user achievements",
                condition_check=self._check_achievement,
                audio_context=TradingContext.PROFIT_TARGET,
                audio_mood=AudioMood.EXCITED,
                cooldown_minutes=5,
                priority=9
            ),
            AudioTrigger(
                trigger_id="user_inactivity",
                trigger_type=TriggerType.TIME_BASED,
                name="User Inactivity",
                description="Bit checks on inactive users",
                condition_check=self._check_user_inactivity,
                audio_context=TradingContext.LOW_VOLATILITY,
                audio_mood=AudioMood.CURIOUS,
                cooldown_minutes=30,
                priority=2
            )
        ]
        
        for trigger in emotional_triggers:
            self.triggers[trigger.trigger_id] = trigger
    
    def _setup_story_progression_triggers(self):
        """Setup triggers based on Norman's story progression"""
        
        story_triggers = [
            AudioTrigger(
                trigger_id="first_profitable_week",
                trigger_type=TriggerType.CONDITION_BASED,
                name="First Profitable Week",
                description="Bit's first purr milestone - like Norman's breakthrough",
                condition_check=self._check_first_profitable_week,
                audio_context=TradingContext.PROFIT_TARGET,
                audio_mood=AudioMood.CONTENT,
                cooldown_minutes=10080,  # Once per week
                priority=10
            ),
            AudioTrigger(
                trigger_id="discipline_milestone",
                trigger_type=TriggerType.CONDITION_BASED,
                name="Discipline Milestone",
                description="Bit recognizes developing discipline",
                condition_check=self._check_discipline_milestone,
                audio_context=TradingContext.TRADE_OPENED,
                audio_mood=AudioMood.CONFIDENT,
                cooldown_minutes=1440,  # Once per day
                priority=8
            ),
            AudioTrigger(
                trigger_id="story_phase_transition",
                trigger_type=TriggerType.EVENT_BASED,
                name="Story Phase Transition",
                description="Bit reacts to user's journey progression",
                condition_check=self._check_story_transition,
                audio_context=TradingContext.PROFIT_TARGET,
                audio_mood=AudioMood.EXCITED,
                cooldown_minutes=60,
                priority=9
            )
        ]
        
        for trigger in story_triggers:
            self.triggers[trigger.trigger_id] = trigger
    
    def _setup_time_based_triggers(self):
        """Setup time-based ambient triggers"""
        
        time_triggers = [
            AudioTrigger(
                trigger_id="weekend_approach",
                trigger_type=TriggerType.TIME_BASED,
                name="Weekend Approach",
                description="Bit prepares for weekend rest",
                condition_check=self._check_weekend_approach,
                audio_context=TradingContext.WEEKEND_BREAK,
                audio_mood=AudioMood.SLEEPY,
                cooldown_minutes=480,
                priority=4
            ),
            AudioTrigger(
                trigger_id="session_milestone",
                trigger_type=TriggerType.TIME_BASED,
                name="Session Milestone",
                description="Bit acknowledges extended trading sessions",
                condition_check=self._check_session_milestone,
                audio_context=TradingContext.LOW_VOLATILITY,
                audio_mood=AudioMood.CONTENT,
                cooldown_minutes=60,
                priority=3
            )
        ]
        
        for trigger in time_triggers:
            self.triggers[trigger.trigger_id] = trigger
    
    # Condition check methods
    def _check_market_opening(self, user_id: str, context: Dict) -> bool:
        """Check if market is opening"""
        return context.get('event_type') == 'market_open'
    
    def _check_market_closing(self, user_id: str, context: Dict) -> bool:
        """Check if market is closing"""
        return context.get('event_type') == 'market_close'
    
    def _check_high_volatility(self, user_id: str, context: Dict) -> bool:
        """Check for high volatility conditions"""
        volatility = context.get('market_data', {}).get('volatility')
        return volatility == 'high' or context.get('volatility_spike', False)
    
    def _check_low_volatility(self, user_id: str, context: Dict) -> bool:
        """Check for low volatility conditions"""
        volatility = context.get('market_data', {}).get('volatility')
        return volatility == 'low' and context.get('open_positions', 0) == 0
    
    def _check_news_event(self, user_id: str, context: Dict) -> bool:
        """Check for news events"""
        return context.get('event_type') == 'news_release' and context.get('impact') in ['high', 'medium']
    
    def _check_signal_received(self, user_id: str, context: Dict) -> bool:
        """Check for received trading signals"""
        return context.get('event_type') == 'signal_received'
    
    def _check_trade_opened(self, user_id: str, context: Dict) -> bool:
        """Check for trade opening"""
        return context.get('event_type') == 'trade_opened'
    
    def _check_profit_target(self, user_id: str, context: Dict) -> bool:
        """Check for profit target hits"""
        return context.get('event_type') == 'trade_closed' and context.get('result') == 'profit'
    
    def _check_stop_loss(self, user_id: str, context: Dict) -> bool:
        """Check for stop loss hits"""
        return context.get('event_type') == 'trade_closed' and context.get('result') == 'loss'
    
    def _check_breakeven(self, user_id: str, context: Dict) -> bool:
        """Check for breakeven reached"""
        return context.get('event_type') == 'breakeven_reached'
    
    def _check_risk_warning(self, user_id: str, context: Dict) -> bool:
        """Check for risk warning conditions"""
        return (context.get('risk_level') == 'high' or 
                context.get('event_type') == 'risk_warning' or
                context.get('tcs_score', 100) < 70)
    
    def _check_winning_streak(self, user_id: str, context: Dict) -> bool:
        """Check for winning streaks"""
        streak = context.get('trading_stats', {}).get('current_streak', 0)
        return streak >= 3 and context.get('event_type') == 'trade_closed' and context.get('result') == 'profit'
    
    def _check_losing_streak(self, user_id: str, context: Dict) -> bool:
        """Check for losing streaks"""
        streak = context.get('trading_stats', {}).get('current_loss_streak', 0)
        return streak >= 2
    
    def _check_achievement(self, user_id: str, context: Dict) -> bool:
        """Check for achievement unlocks"""
        return context.get('event_type') == 'achievement_unlocked'
    
    def _check_user_inactivity(self, user_id: str, context: Dict) -> bool:
        """Check for user inactivity"""
        last_activity = context.get('last_activity')
        if last_activity:
            inactive_time = datetime.now() - last_activity
            return inactive_time > timedelta(minutes=30)
        return False
    
    def _check_first_profitable_week(self, user_id: str, context: Dict) -> bool:
        """Check for first profitable week milestone"""
        story_context = norman_story_engine.get_user_story_context(user_id)
        weekly_pnl = context.get('trading_stats', {}).get('weekly_pnl', 0)
        return (weekly_pnl > 0 and 
                story_context.current_phase in [StoryPhase.EARLY_STRUGGLE, StoryPhase.AWAKENING] and
                context.get('milestone') == 'first_profitable_week')
    
    def _check_discipline_milestone(self, user_id: str, context: Dict) -> bool:
        """Check for discipline development milestones"""
        risk_adherence = context.get('trading_stats', {}).get('risk_adherence', 0)
        return risk_adherence > 0.8 and context.get('trades_today', 0) > 0
    
    def _check_story_transition(self, user_id: str, context: Dict) -> bool:
        """Check for story phase transitions"""
        return context.get('event_type') == 'story_phase_transition'
    
    def _check_weekend_approach(self, user_id: str, context: Dict) -> bool:
        """Check for weekend approach"""
        now = datetime.now()
        return now.weekday() == 4 and now.hour >= 16  # Friday after 4 PM
    
    def _check_session_milestone(self, user_id: str, context: Dict) -> bool:
        """Check for session time milestones"""
        session_duration = context.get('session_duration_minutes', 0)
        return session_duration > 0 and session_duration % 60 == 0  # Every hour
    
    async def process_trigger_event(self, user_id: str, context: Dict[str, Any]) -> List[str]:
        """Process an event and check for triggered audio"""
        
        triggered_events = []
        
        # Check user audio settings
        user_settings = get_user_settings(user_id)
        if not user_settings.sounds_enabled:
            return triggered_events
        
        # Check each trigger
        for trigger_id, trigger in self.triggers.items():
            if not trigger.enabled:
                continue
            
            # Check cooldown
            if self._is_trigger_on_cooldown(user_id, trigger_id):
                continue
            
            try:
                # Check trigger condition
                if trigger.condition_check(user_id, context):
                    # Trigger the audio
                    event_id = await ambient_audio_engine.play_contextual_audio(
                        user_id=user_id,
                        context=trigger.audio_context,
                        mood=trigger.audio_mood,
                        metadata={
                            'trigger_id': trigger_id,
                            'trigger_name': trigger.name,
                            'context': context
                        }
                    )
                    
                    if event_id:
                        triggered_events.append(event_id)
                        self._record_trigger_activation(user_id, trigger_id)
                        
                        logger.info(f"Audio trigger activated: {trigger.name} for user {user_id}")
            
            except Exception as e:
                logger.error(f"Error checking trigger {trigger_id}: {e}")
        
        return triggered_events
    
    def _is_trigger_on_cooldown(self, user_id: str, trigger_id: str) -> bool:
        """Check if trigger is on cooldown for user"""
        history = self.user_trigger_history.get(user_id, [])
        
        for record in history:
            if record['trigger_id'] == trigger_id:
                trigger = self.triggers[trigger_id]
                time_since = datetime.now() - record['timestamp']
                if time_since < timedelta(minutes=trigger.cooldown_minutes):
                    return True
        
        return False
    
    def _record_trigger_activation(self, user_id: str, trigger_id: str):
        """Record trigger activation for cooldown tracking"""
        if user_id not in self.user_trigger_history:
            self.user_trigger_history[user_id] = []
        
        self.user_trigger_history[user_id].append({
            'trigger_id': trigger_id,
            'timestamp': datetime.now()
        })
        
        # Keep only last 24 hours of history
        cutoff = datetime.now() - timedelta(hours=24)
        self.user_trigger_history[user_id] = [
            record for record in self.user_trigger_history[user_id]
            if record['timestamp'] > cutoff
        ]
    
    def start_monitoring(self):
        """Start the trigger monitoring system"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Audio trigger monitoring started")
    
    def stop_monitoring(self):
        """Stop the trigger monitoring system"""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
        logger.info("Audio trigger monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop for time-based triggers"""
        while self.is_monitoring:
            try:
                # Check time-based triggers for all active users
                current_time = datetime.now()
                
                # Create time-based context
                time_context = {
                    'event_type': 'time_check',
                    'current_time': current_time,
                    'hour': current_time.hour,
                    'weekday': current_time.weekday()
                }
                
                # Process for each user with recent activity
                for user_id in ambient_audio_engine.bit_states.keys():
                    await self.process_trigger_event(user_id, time_context)
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in trigger monitoring loop: {e}")
                await asyncio.sleep(5)
    
    def enable_trigger(self, trigger_id: str, enabled: bool = True):
        """Enable or disable a specific trigger"""
        if trigger_id in self.triggers:
            self.triggers[trigger_id].enabled = enabled
            logger.info(f"Trigger {trigger_id} {'enabled' if enabled else 'disabled'}")
    
    def get_trigger_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get trigger statistics for user"""
        history = self.user_trigger_history.get(user_id, [])
        
        trigger_counts = {}
        for record in history:
            trigger_id = record['trigger_id']
            trigger_counts[trigger_id] = trigger_counts.get(trigger_id, 0) + 1
        
        return {
            'total_triggers_24h': len(history),
            'trigger_breakdown': trigger_counts,
            'active_triggers': len([t for t in self.triggers.values() if t.enabled]),
            'total_triggers': len(self.triggers)
        }


# Global instance
audio_trigger_manager = AudioTriggerManager()


# Convenience functions for integration
async def trigger_market_event(user_id: str, event_type: str, market_data: Dict = None):
    """Trigger market-related audio events"""
    context = {
        'event_type': event_type,
        'market_data': market_data or {},
        'timestamp': datetime.now()
    }
    return await audio_trigger_manager.process_trigger_event(user_id, context)


async def trigger_trading_event(user_id: str, event_type: str, trade_data: Dict = None):
    """Trigger trading-related audio events"""
    context = {
        'event_type': event_type,
        'trade_data': trade_data or {},
        'timestamp': datetime.now()
    }
    return await audio_trigger_manager.process_trigger_event(user_id, context)


async def trigger_achievement_event(user_id: str, achievement_data: Dict):
    """Trigger achievement-related audio events"""
    context = {
        'event_type': 'achievement_unlocked',
        'achievement_data': achievement_data,
        'timestamp': datetime.now()
    }
    return await audio_trigger_manager.process_trigger_event(user_id, context)


def start_audio_triggers():
    """Start the audio trigger monitoring system"""
    audio_trigger_manager.start_monitoring()


def stop_audio_triggers():
    """Stop the audio trigger monitoring system"""
    audio_trigger_manager.stop_monitoring()