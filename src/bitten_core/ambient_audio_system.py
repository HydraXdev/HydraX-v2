"""
BITTEN Ambient Audio System - Bit's Presence Engine
Creates immersive ambient audio experience with Bit the cat as Norman's companion
"""

import json
import random
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from .user_settings import should_play_sound, get_user_settings
from .norman_story_integration import norman_story_engine, StoryPhase

logger = logging.getLogger(__name__)

class AudioType(Enum):
    """Types of ambient audio"""
    CHIRP = "chirp"
    PURR = "purr"
    MEOW = "meow"
    ENVIRONMENTAL = "environmental"
    TRADING_FEEDBACK = "trading_feedback"
    AMBIENT = "ambient"

class AudioMood(Enum):
    """Audio moods reflecting market/user states"""
    CALM = "calm"
    ALERT = "alert"
    CAUTIOUS = "cautious"
    CONFIDENT = "confident"
    WORRIED = "worried"
    EXCITED = "excited"
    CONTENT = "content"
    SLEEPY = "sleepy"

class TradingContext(Enum):
    """Trading contexts for audio triggers"""
    MARKET_OPEN = "market_open"
    MARKET_CLOSE = "market_close"
    SIGNAL_RECEIVED = "signal_received"
    TRADE_OPENED = "trade_opened"
    TRADE_CLOSED = "trade_closed"
    PROFIT_TARGET = "profit_target"
    STOP_LOSS = "stop_loss"
    BREAKEVEN = "breakeven"
    RISK_WARNING = "risk_warning"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    NEWS_EVENT = "news_event"
    WEEKEND_BREAK = "weekend_break"

@dataclass
class AudioClip:
    """Represents an audio clip with metadata"""
    clip_id: str
    audio_type: AudioType
    mood: AudioMood
    file_path: str
    duration: float
    description: str
    tags: List[str]
    volume: float = 0.8
    loop: bool = False
    fade_in: float = 0.0
    fade_out: float = 0.0

@dataclass
class AudioEvent:
    """Represents an audio event to be played"""
    event_id: str
    user_id: str
    clip_id: str
    trigger_context: TradingContext
    timestamp: datetime
    priority: int = 5  # 1-10, higher = more important
    mood_context: Optional[AudioMood] = None
    metadata: Dict[str, Any] = None

@dataclass
class BitCompanionState:
    """Tracks Bit's emotional and behavioral state"""
    user_id: str
    current_mood: AudioMood
    energy_level: int  # 1-10
    alertness_level: int  # 1-10
    last_interaction: Optional[datetime]
    mood_history: List[Tuple[AudioMood, datetime]]
    active_sessions: int
    comfort_level: int  # How comfortable Bit is with user's trading

class AmbientAudioEngine:
    """Main engine for Bit's ambient audio system"""
    
    def __init__(self, audio_assets_path: str = "assets/audio"):
        self.audio_assets_path = Path(audio_assets_path)
        self.audio_assets_path.mkdir(parents=True, exist_ok=True)
        
        # State tracking
        self.bit_states: Dict[str, BitCompanionState] = {}
        self.active_events: List[AudioEvent] = []
        self.audio_clips: Dict[str, AudioClip] = {}
        self.user_preferences: Dict[str, Dict] = {}
        
        # Timing and frequency control
        self.last_ambient_play: Dict[str, datetime] = {}
        self.ambient_cooldowns: Dict[str, int] = {}
        
        # Audio library initialization
        self._initialize_audio_library()
        self._initialize_mississippi_sounds()
        self._initialize_trading_feedback_sounds()
        
        # Background tasks
        self.is_running = False
        self.ambient_task = None
    
    def _initialize_audio_library(self):
        """Initialize Bit's audio library with contextual sounds"""
        
        # Chirp patterns for different moods and contexts
        chirp_library = {
            "greeting_chirp": AudioClip(
                clip_id="greeting_chirp",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.CONTENT,
                file_path="bit/chirps/greeting.wav",
                duration=0.8,
                description="Bit's welcoming chirp when user logs in",
                tags=["welcome", "friendly", "start"]
            ),
            "alert_chirp": AudioClip(
                clip_id="alert_chirp",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.ALERT,
                file_path="bit/chirps/alert.wav",
                duration=0.6,
                description="Quick alert chirp for important events",
                tags=["alert", "attention", "important"]
            ),
            "approval_chirp": AudioClip(
                clip_id="approval_chirp",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.CONFIDENT,
                file_path="bit/chirps/approval.wav",
                duration=0.7,
                description="Approving chirp for good trading decisions",
                tags=["approval", "good_choice", "confidence"]
            ),
            "warning_chirp": AudioClip(
                clip_id="warning_chirp",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.CAUTIOUS,
                file_path="bit/chirps/warning.wav",
                duration=1.0,
                description="Cautious chirp for risky situations",
                tags=["warning", "caution", "risk"]
            ),
            "curious_chirp": AudioClip(
                clip_id="curious_chirp",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.ALERT,
                file_path="bit/chirps/curious.wav",
                duration=0.5,
                description="Curious chirp when markets are interesting",
                tags=["curiosity", "interest", "exploration"]
            ),
            "comfort_chirp": AudioClip(
                clip_id="comfort_chirp",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.CALM,
                file_path="bit/chirps/comfort.wav",
                duration=0.9,
                description="Comforting chirp during difficult times",
                tags=["comfort", "support", "calm"]
            )
        }
        
        # Purr patterns for different emotional states
        purr_library = {
            "content_purr": AudioClip(
                clip_id="content_purr",
                audio_type=AudioType.PURR,
                mood=AudioMood.CONTENT,
                file_path="bit/purrs/content.wav",
                duration=3.0,
                description="Content purring during stable periods",
                tags=["content", "stable", "peaceful"],
                loop=True,
                volume=0.4
            ),
            "victory_purr": AudioClip(
                clip_id="victory_purr",
                audio_type=AudioType.PURR,
                mood=AudioMood.EXCITED,
                file_path="bit/purrs/victory.wav",
                duration=2.5,
                description="Excited purring after successful trades",
                tags=["victory", "success", "celebration"]
            ),
            "drowsy_purr": AudioClip(
                clip_id="drowsy_purr",
                audio_type=AudioType.PURR,
                mood=AudioMood.SLEEPY,
                file_path="bit/purrs/drowsy.wav",
                duration=4.0,
                description="Sleepy purring during quiet market periods",
                tags=["sleepy", "quiet", "rest"],
                loop=True,
                volume=0.3
            ),
            "nervous_purr": AudioClip(
                clip_id="nervous_purr",
                audio_type=AudioType.PURR,
                mood=AudioMood.WORRIED,
                file_path="bit/purrs/nervous.wav",
                duration=1.8,
                description="Nervous purring during volatile markets",
                tags=["nervous", "worry", "volatility"]
            )
        }
        
        # Meow variations for specific situations
        meow_library = {
            "attention_meow": AudioClip(
                clip_id="attention_meow",
                audio_type=AudioType.MEOW,
                mood=AudioMood.ALERT,
                file_path="bit/meows/attention.wav",
                duration=1.2,
                description="Attention-seeking meow for important signals",
                tags=["attention", "signal", "important"]
            ),
            "protest_meow": AudioClip(
                clip_id="protest_meow",
                audio_type=AudioType.MEOW,
                mood=AudioMood.WORRIED,
                file_path="bit/meows/protest.wav",
                duration=1.5,
                description="Protesting meow for very risky trades",
                tags=["protest", "concern", "high_risk"]
            ),
            "happy_meow": AudioClip(
                clip_id="happy_meow",
                audio_type=AudioType.MEOW,
                mood=AudioMood.EXCITED,
                file_path="bit/meows/happy.wav",
                duration=1.0,
                description="Happy meow celebrating achievements",
                tags=["happy", "celebration", "achievement"]
            )
        }
        
        # Combine all libraries
        self.audio_clips.update(chirp_library)
        self.audio_clips.update(purr_library)
        self.audio_clips.update(meow_library)
    
    def _initialize_mississippi_sounds(self):
        """Initialize environmental Mississippi Delta sounds"""
        
        mississippi_sounds = {
            "delta_breeze": AudioClip(
                clip_id="delta_breeze",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CALM,
                file_path="environment/delta_breeze.wav",
                duration=30.0,
                description="Gentle Mississippi Delta breeze",
                tags=["nature", "wind", "peaceful", "background"],
                loop=True,
                volume=0.2,
                fade_in=2.0,
                fade_out=2.0
            ),
            "distant_thunder": AudioClip(
                clip_id="distant_thunder",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CAUTIOUS,
                file_path="environment/distant_thunder.wav",
                duration=8.0,
                description="Distant thunder warning of market storms",
                tags=["weather", "warning", "storm", "atmosphere"],
                volume=0.3
            ),
            "crickets_evening": AudioClip(
                clip_id="crickets_evening",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.SLEEPY,
                file_path="environment/crickets.wav",
                duration=45.0,
                description="Evening crickets during market close",
                tags=["night", "peaceful", "close", "rest"],
                loop=True,
                volume=0.15
            ),
            "river_flow": AudioClip(
                clip_id="river_flow",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CONTENT,
                file_path="environment/river_flow.wav",
                duration=60.0,
                description="Steady river flow representing market consistency",
                tags=["water", "steady", "flow", "consistency"],
                loop=True,
                volume=0.2
            ),
            "morning_birds": AudioClip(
                clip_id="morning_birds",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.ALERT,
                file_path="environment/morning_birds.wav",
                duration=20.0,
                description="Morning bird songs for market opening",
                tags=["morning", "awakening", "fresh_start", "optimism"],
                volume=0.25
            )
        }
        
        self.audio_clips.update(mississippi_sounds)
    
    def _initialize_trading_feedback_sounds(self):
        """Initialize trading-specific feedback sounds"""
        
        trading_sounds = {
            "gentle_chime": AudioClip(
                clip_id="gentle_chime",
                audio_type=AudioType.TRADING_FEEDBACK,
                mood=AudioMood.CONFIDENT,
                file_path="trading/gentle_chime.wav",
                duration=1.5,
                description="Subtle chime for trade confirmations",
                tags=["confirmation", "gentle", "positive"]
            ),
            "soft_bell": AudioClip(
                clip_id="soft_bell",
                audio_type=AudioType.TRADING_FEEDBACK,
                mood=AudioMood.CONTENT,
                file_path="trading/soft_bell.wav",
                duration=2.0,
                description="Soft bell for profit targets",
                tags=["success", "target", "achievement"]
            ),
            "low_tone": AudioClip(
                clip_id="low_tone",
                audio_type=AudioType.TRADING_FEEDBACK,
                mood=AudioMood.CAUTIOUS,
                file_path="trading/low_tone.wav",
                duration=1.0,
                description="Low tone for stop losses (non-harsh)",
                tags=["stop", "caution", "awareness"]
            ),
            "wind_chime": AudioClip(
                clip_id="wind_chime",
                audio_type=AudioType.TRADING_FEEDBACK,
                mood=AudioMood.CALM,
                file_path="trading/wind_chime.wav",
                duration=3.0,
                description="Wind chime for breakeven notifications",
                tags=["neutral", "safe", "balance"]
            )
        }
        
        self.audio_clips.update(trading_sounds)
    
    def get_bit_state(self, user_id: str) -> BitCompanionState:
        """Get or create Bit's companion state for user"""
        if user_id not in self.bit_states:
            self.bit_states[user_id] = BitCompanionState(
                user_id=user_id,
                current_mood=AudioMood.CONTENT,
                energy_level=7,
                alertness_level=6,
                last_interaction=None,
                mood_history=[],
                active_sessions=0,
                comfort_level=5
            )
        return self.bit_states[user_id]
    
    def update_bit_mood(self, user_id: str, new_mood: AudioMood, 
                       context: Optional[str] = None) -> None:
        """Update Bit's emotional state"""
        bit_state = self.get_bit_state(user_id)
        
        # Record mood history
        bit_state.mood_history.append((bit_state.current_mood, datetime.now()))
        
        # Keep only last 24 hours of mood history
        cutoff = datetime.now() - timedelta(hours=24)
        bit_state.mood_history = [
            (mood, time) for mood, time in bit_state.mood_history
            if time > cutoff
        ]
        
        # Update current mood
        bit_state.current_mood = new_mood
        bit_state.last_interaction = datetime.now()
        
        logger.info(f"Bit's mood updated for {user_id}: {new_mood.value} ({context})")
    
    def analyze_trading_context(self, user_id: str, market_data: Dict[str, Any]) -> AudioMood:
        """Analyze trading context to determine appropriate mood"""
        
        # Get user's story phase for mood adjustment
        story_phase = norman_story_engine.get_user_story_context(user_id).current_phase
        
        # Extract market context
        volatility = market_data.get('volatility', 'medium')
        win_rate = market_data.get('recent_win_rate', 0.5)
        open_positions = market_data.get('open_positions', 0)
        recent_pnl = market_data.get('recent_pnl', 0)
        
        # Determine mood based on multiple factors
        if recent_pnl > 100:  # Good profit
            if story_phase in [StoryPhase.EARLY_STRUGGLE, StoryPhase.AWAKENING]:
                return AudioMood.EXCITED
            else:
                return AudioMood.CONFIDENT
        
        elif recent_pnl < -50:  # Losses
            if win_rate < 0.4:
                return AudioMood.WORRIED
            else:
                return AudioMood.CAUTIOUS
        
        elif volatility == 'high':
            return AudioMood.ALERT
        
        elif volatility == 'low' and open_positions == 0:
            return AudioMood.SLEEPY
        
        else:
            return AudioMood.CONTENT
    
    def should_play_ambient_audio(self, user_id: str, audio_type: AudioType) -> bool:
        """Check if ambient audio should be played for user"""
        
        # Check user settings
        user_settings = get_user_settings(user_id)
        if not user_settings.sounds_enabled:
            return False
        
        # Check specific audio type settings
        audio_setting_map = {
            AudioType.CHIRP: "achievement_sounds",  # Reuse existing setting
            AudioType.PURR: "sounds_enabled",
            AudioType.MEOW: "achievement_sounds",
            AudioType.ENVIRONMENTAL: "sounds_enabled",
            AudioType.TRADING_FEEDBACK: "warning_sounds",
            AudioType.AMBIENT: "sounds_enabled"
        }
        
        setting_key = audio_setting_map.get(audio_type, "sounds_enabled")
        setting_value = getattr(user_settings, setting_key, True)
        
        if not setting_value:
            return False
        
        # Check cooldowns to prevent audio spam
        last_play = self.last_ambient_play.get(f"{user_id}_{audio_type.value}")
        if last_play:
            cooldown = self.ambient_cooldowns.get(audio_type.value, 30)  # Default 30 seconds
            if (datetime.now() - last_play).seconds < cooldown:
                return False
        
        return True
    
    def select_contextual_audio(self, user_id: str, context: TradingContext, 
                              mood: Optional[AudioMood] = None) -> Optional[AudioClip]:
        """Select appropriate audio clip based on context and mood"""
        
        bit_state = self.get_bit_state(user_id)
        target_mood = mood or bit_state.current_mood
        
        # Define audio selection rules based on context
        context_audio_map = {
            TradingContext.SIGNAL_RECEIVED: [
                AudioType.CHIRP, AudioType.MEOW
            ],
            TradingContext.TRADE_OPENED: [
                AudioType.CHIRP, AudioType.TRADING_FEEDBACK
            ],
            TradingContext.PROFIT_TARGET: [
                AudioType.PURR, AudioType.TRADING_FEEDBACK
            ],
            TradingContext.STOP_LOSS: [
                AudioType.CHIRP, AudioType.TRADING_FEEDBACK
            ],
            TradingContext.RISK_WARNING: [
                AudioType.CHIRP, AudioType.MEOW
            ],
            TradingContext.MARKET_OPEN: [
                AudioType.CHIRP, AudioType.ENVIRONMENTAL
            ],
            TradingContext.MARKET_CLOSE: [
                AudioType.PURR, AudioType.ENVIRONMENTAL
            ],
            TradingContext.HIGH_VOLATILITY: [
                AudioType.CHIRP, AudioType.ENVIRONMENTAL
            ],
            TradingContext.LOW_VOLATILITY: [
                AudioType.PURR, AudioType.ENVIRONMENTAL
            ]
        }
        
        # Get possible audio types for this context
        possible_types = context_audio_map.get(context, [AudioType.CHIRP])
        
        # Filter clips by type and mood
        matching_clips = [
            clip for clip in self.audio_clips.values()
            if clip.audio_type in possible_types and clip.mood == target_mood
        ]
        
        # If no exact mood match, find closest mood
        if not matching_clips:
            matching_clips = [
                clip for clip in self.audio_clips.values()
                if clip.audio_type in possible_types
            ]
        
        # Select based on story phase and user preferences
        if matching_clips:
            story_phase = norman_story_engine.get_user_story_context(user_id).current_phase
            
            # Weight selection based on story phase
            if story_phase == StoryPhase.EARLY_STRUGGLE:
                # Prefer comforting sounds
                comfort_clips = [c for c in matching_clips if 'comfort' in c.tags]
                if comfort_clips:
                    matching_clips = comfort_clips
            
            elif story_phase == StoryPhase.LEGACY:
                # Prefer confident, achievement sounds
                achievement_clips = [c for c in matching_clips if 'achievement' in c.tags]
                if achievement_clips:
                    matching_clips = achievement_clips
            
            return random.choice(matching_clips)
        
        return None
    
    async def play_contextual_audio(self, user_id: str, context: TradingContext, 
                                  mood: Optional[AudioMood] = None,
                                  metadata: Optional[Dict] = None) -> Optional[str]:
        """Play contextual audio and return event ID"""
        
        # Check if audio should be played
        audio_clip = self.select_contextual_audio(user_id, context, mood)
        if not audio_clip:
            return None
        
        if not self.should_play_ambient_audio(user_id, audio_clip.audio_type):
            return None
        
        # Create audio event
        event = AudioEvent(
            event_id=f"audio_{datetime.now().timestamp()}_{user_id}",
            user_id=user_id,
            clip_id=audio_clip.clip_id,
            trigger_context=context,
            timestamp=datetime.now(),
            priority=self._get_context_priority(context),
            mood_context=mood,
            metadata=metadata or {}
        )
        
        # Queue the event
        self.active_events.append(event)
        
        # Update cooldown
        self.last_ambient_play[f"{user_id}_{audio_clip.audio_type.value}"] = datetime.now()
        
        # Update Bit's state
        if mood:
            self.update_bit_mood(user_id, mood, context.value)
        
        logger.info(f"Queued ambient audio: {audio_clip.clip_id} for {context.value}")
        
        # In a real implementation, this would trigger actual audio playback
        await self._simulate_audio_playback(audio_clip)
        
        return event.event_id
    
    def _get_context_priority(self, context: TradingContext) -> int:
        """Get priority level for trading context"""
        priority_map = {
            TradingContext.PROFIT_TARGET: 9,
            TradingContext.STOP_LOSS: 8,
            TradingContext.RISK_WARNING: 8,
            TradingContext.SIGNAL_RECEIVED: 7,
            TradingContext.TRADE_OPENED: 6,
            TradingContext.TRADE_CLOSED: 6,
            TradingContext.HIGH_VOLATILITY: 5,
            TradingContext.MARKET_OPEN: 4,
            TradingContext.MARKET_CLOSE: 4,
            TradingContext.LOW_VOLATILITY: 3,
            TradingContext.WEEKEND_BREAK: 2
        }
        return priority_map.get(context, 5)
    
    async def _simulate_audio_playback(self, audio_clip: AudioClip):
        """Simulate audio playback (placeholder for real implementation)"""
        # In real implementation, this would:
        # 1. Load audio file
        # 2. Apply volume, fade settings
        # 3. Play through appropriate audio channel
        # 4. Handle looping if specified
        
        await asyncio.sleep(0.1)  # Simulate async operation
        logger.debug(f"Playing audio: {audio_clip.description}")
    
    def start_ambient_system(self):
        """Start the ambient audio background system"""
        if not self.is_running:
            self.is_running = True
            self.ambient_task = asyncio.create_task(self._ambient_loop())
            logger.info("Ambient audio system started")
    
    def stop_ambient_system(self):
        """Stop the ambient audio system"""
        self.is_running = False
        if self.ambient_task:
            self.ambient_task.cancel()
        logger.info("Ambient audio system stopped")
    
    async def _ambient_loop(self):
        """Background loop for ambient audio management"""
        while self.is_running:
            try:
                # Clean up old events
                cutoff = datetime.now() - timedelta(hours=1)
                self.active_events = [
                    event for event in self.active_events
                    if event.timestamp > cutoff
                ]
                
                # Update Bit states for all users
                for user_id, bit_state in self.bit_states.items():
                    await self._update_ambient_state(user_id, bit_state)
                
                # Wait before next cycle
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in ambient audio loop: {e}")
                await asyncio.sleep(5)
    
    async def _update_ambient_state(self, user_id: str, bit_state: BitCompanionState):
        """Update ambient state for a user"""
        
        # Check if user has been inactive
        if bit_state.last_interaction:
            inactive_time = datetime.now() - bit_state.last_interaction
            
            # After 30 minutes of inactivity, Bit becomes sleepy
            if inactive_time > timedelta(minutes=30):
                if bit_state.current_mood not in [AudioMood.SLEEPY, AudioMood.CALM]:
                    self.update_bit_mood(user_id, AudioMood.SLEEPY, "inactivity")
                    
                    # Occasionally play sleepy ambient sounds
                    if random.random() < 0.1:  # 10% chance every cycle
                        await self.play_contextual_audio(
                            user_id, 
                            TradingContext.LOW_VOLATILITY,
                            AudioMood.SLEEPY
                        )
        
        # Gradually adjust energy and alertness
        if bit_state.energy_level > 3:
            bit_state.energy_level = max(1, bit_state.energy_level - 1)
        
        if bit_state.alertness_level > 3:
            bit_state.alertness_level = max(1, bit_state.alertness_level - 1)
    
    def get_audio_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get audio statistics for user"""
        bit_state = self.get_bit_state(user_id)
        user_events = [e for e in self.active_events if e.user_id == user_id]
        
        return {
            "current_mood": bit_state.current_mood.value,
            "energy_level": bit_state.energy_level,
            "alertness_level": bit_state.alertness_level,
            "comfort_level": bit_state.comfort_level,
            "recent_events": len(user_events),
            "mood_history_24h": len(bit_state.mood_history),
            "last_interaction": bit_state.last_interaction.isoformat() if bit_state.last_interaction else None
        }

# Global instance
ambient_audio_engine = AmbientAudioEngine()

# Convenience functions for integration
async def play_trading_audio(user_id: str, context: TradingContext, 
                           market_data: Optional[Dict] = None) -> Optional[str]:
    """Convenience function to play trading-related audio"""
    
    # Analyze context for appropriate mood
    mood = None
    if market_data:
        mood = ambient_audio_engine.analyze_trading_context(user_id, market_data)
    
    return await ambient_audio_engine.play_contextual_audio(user_id, context, mood)

async def bit_react_to_trade(user_id: str, trade_result: Dict[str, Any]) -> Optional[str]:
    """Make Bit react to trade results"""
    
    pnl = trade_result.get('pnl', 0)
    
    if pnl > 0:
        # Positive trade
        context = TradingContext.PROFIT_TARGET
        mood = AudioMood.EXCITED if pnl > 50 else AudioMood.CONFIDENT
    else:
        # Negative trade
        context = TradingContext.STOP_LOSS
        mood = AudioMood.WORRIED if pnl < -100 else AudioMood.CAUTIOUS
    
    return await ambient_audio_engine.play_contextual_audio(
        user_id, context, mood, metadata=trade_result
    )

def start_ambient_audio():
    """Start the ambient audio system"""
    ambient_audio_engine.start_ambient_system()

def stop_ambient_audio():
    """Stop the ambient audio system"""
    ambient_audio_engine.stop_ambient_system()