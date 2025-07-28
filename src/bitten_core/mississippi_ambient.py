"""
BITTEN Mississippi Ambient Audio System
Environmental sounds that evoke the Mississippi Delta and complement Bit's presence
"""

import asyncio
import random
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .ambient_audio_system import ambient_audio_engine, AudioClip, AudioType, AudioMood
from .norman_story_integration import norman_story_engine, StoryPhase
from .user_settings import get_user_settings

logger = logging.getLogger(__name__)

class WeatherPattern(Enum):
    """Mississippi weather patterns that reflect market conditions"""
    CLEAR_MORNING = "clear_morning"
    GENTLE_BREEZE = "gentle_breeze"
    APPROACHING_STORM = "approaching_storm"
    SUMMER_RAIN = "summer_rain"
    CALM_EVENING = "calm_evening"
    NIGHT_CRICKETS = "night_crickets"
    DAWN_CHORUS = "dawn_chorus"
    RIVER_FLOW = "river_flow"

class SeasonalMood(Enum):
    """Seasonal moods reflecting trading phases"""
    SPRING_GROWTH = "spring_growth"      # New beginnings, learning
    SUMMER_ABUNDANCE = "summer_abundance" # Peak performance
    AUTUMN_HARVEST = "autumn_harvest"    # Reaping rewards
    WINTER_REFLECTION = "winter_reflection" # Rest and planning

class CulturalElement(Enum):
    """Mississippi cultural elements for authentic atmosphere"""
    CHURCH_BELLS = "church_bells"        # Sunday trading breaks
    STEAMBOAT_HORN = "steamboat_horn"    # Major milestones
    COTTON_FIELD = "cotton_field"        # Patience and timing
    FRONT_PORCH = "front_porch"          # Comfort and wisdom
    DELTA_BLUES = "delta_blues"          # Emotional expression

@dataclass
class EnvironmentalCluster:
    """Group of related environmental sounds"""
    cluster_id: str
    name: str
    base_clips: List[str]  # Core environmental sounds
    accent_clips: List[str]  # Occasional accent sounds
    mood_association: AudioMood
    weather_pattern: WeatherPattern
    story_phase_affinity: List[StoryPhase]
    time_of_day: Optional[Tuple[int, int]] = None  # Hour range (start, end)
    cultural_context: Optional[CulturalElement] = None

class MississippiAmbientEngine:
    """Engine for Mississippi Delta environmental audio"""
    
    def __init__(self):
        self.environmental_clusters: Dict[str, EnvironmentalCluster] = {}
        self.user_ambient_states: Dict[str, Dict] = {}
        self.active_ambient_loops: Dict[str, asyncio.Task] = {}
        
        # Initialize the system
        self._initialize_environmental_audio()
        self._initialize_cultural_audio()
        self._setup_weather_patterns()
        self._setup_seasonal_transitions()
    
    def _initialize_environmental_audio(self):
        """Initialize core environmental audio clips"""
        
        environmental_clips = {
            # Mississippi River sounds
            "delta_river_flow": AudioClip(
                clip_id="delta_river_flow",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CALM,
                file_path="mississippi/river/delta_flow.wav",
                duration=120.0,
                description="Steady flow of the Mississippi Delta",
                tags=["river", "flow", "constant", "peace"],
                loop=True,
                volume=0.15,
                fade_in=3.0,
                fade_out=3.0
            ),
            
            "river_gentle_lapping": AudioClip(
                clip_id="river_gentle_lapping",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CONTENT,
                file_path="mississippi/river/gentle_lapping.wav",
                duration=60.0,
                description="Gentle water lapping against the shore",
                tags=["water", "gentle", "rhythmic", "soothing"],
                loop=True,
                volume=0.12
            ),
            
            # Wind and breeze sounds
            "delta_breeze_light": AudioClip(
                clip_id="delta_breeze_light",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CALM,
                file_path="mississippi/wind/light_breeze.wav",
                duration=90.0,
                description="Light breeze through Delta vegetation",
                tags=["wind", "gentle", "movement", "natural"],
                loop=True,
                volume=0.10
            ),
            
            "cotton_field_wind": AudioClip(
                clip_id="cotton_field_wind",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CONTENT,
                file_path="mississippi/wind/cotton_field.wav",
                duration=75.0,
                description="Wind moving through cotton fields",
                tags=["cotton", "agricultural", "rustling", "heritage"],
                loop=True,
                volume=0.14
            ),
            
            "storm_approach_wind": AudioClip(
                clip_id="storm_approach_wind",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.ALERT,
                file_path="mississippi/weather/storm_approach.wav",
                duration=45.0,
                description="Wind picking up before a storm",
                tags=["storm", "building", "tension", "change"],
                volume=0.20
            ),
            
            # Weather patterns
            "gentle_rain_start": AudioClip(
                clip_id="gentle_rain_start",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CALM,
                file_path="mississippi/weather/gentle_rain.wav",
                duration=180.0,
                description="Gentle summer rain on Delta soil",
                tags=["rain", "gentle", "nourishing", "growth"],
                loop=True,
                volume=0.18
            ),
            
            "distant_thunder_rumble": AudioClip(
                clip_id="distant_thunder_rumble",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CAUTIOUS,
                file_path="mississippi/weather/distant_thunder.wav",
                duration=8.0,
                description="Distant thunder rolling across the Delta",
                tags=["thunder", "warning", "power", "distance"],
                volume=0.25
            ),
            
            "clearing_storm": AudioClip(
                clip_id="clearing_storm",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CONTENT,
                file_path="mississippi/weather/clearing_storm.wav",
                duration=30.0,
                description="Storm clearing, revealing calm",
                tags=["clearing", "relief", "renewal", "hope"],
                volume=0.16
            ),
            
            # Wildlife and nature
            "morning_birds_delta": AudioClip(
                clip_id="morning_birds_delta",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.ALERT,
                file_path="mississippi/wildlife/morning_birds.wav",
                duration=45.0,
                description="Delta birds welcoming the morning",
                tags=["birds", "morning", "awakening", "nature"],
                volume=0.20
            ),
            
            "evening_crickets": AudioClip(
                clip_id="evening_crickets",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.SLEEPY,
                file_path="mississippi/wildlife/evening_crickets.wav",
                duration=200.0,
                description="Evening cricket symphony",
                tags=["crickets", "evening", "peaceful", "rest"],
                loop=True,
                volume=0.12
            ),
            
            "bullfrogs_night": AudioClip(
                clip_id="bullfrogs_night",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CONTENT,
                file_path="mississippi/wildlife/bullfrogs.wav",
                duration=90.0,
                description="Deep bullfrog calls at night",
                tags=["frogs", "night", "deep", "natural"],
                loop=True,
                volume=0.14
            ),
            
            "cicada_summer": AudioClip(
                clip_id="cicada_summer",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.EXCITED,
                file_path="mississippi/wildlife/cicadas.wav",
                duration=60.0,
                description="Summer cicada chorus",
                tags=["cicadas", "summer", "intensity", "heat"],
                volume=0.16
            ),
            
            # Trees and vegetation
            "oak_tree_rustling": AudioClip(
                clip_id="oak_tree_rustling",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CALM,
                file_path="mississippi/vegetation/oak_rustling.wav",
                duration=80.0,
                description="Ancient oak leaves rustling",
                tags=["oak", "wisdom", "rustling", "timeless"],
                loop=True,
                volume=0.11
            ),
            
            "spanish_moss_wind": AudioClip(
                clip_id="spanish_moss_wind",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CONTENT,
                file_path="mississippi/vegetation/spanish_moss.wav",
                duration=70.0,
                description="Wind through Spanish moss",
                tags=["moss", "ethereal", "southern", "mystical"],
                loop=True,
                volume=0.13
            )
        }
        
        # Add to main audio engine
        ambient_audio_engine.audio_clips.update(environmental_clips)
        
        # Create environmental clusters
        self._create_environmental_clusters()
    
    def _create_environmental_clusters(self):
        """Create clusters of related environmental sounds"""
        
        clusters = {
            "morning_awakening": EnvironmentalCluster(
                cluster_id="morning_awakening",
                name="Delta Morning Awakening",
                base_clips=["delta_river_flow", "delta_breeze_light"],
                accent_clips=["morning_birds_delta", "oak_tree_rustling"],
                mood_association=AudioMood.ALERT,
                weather_pattern=WeatherPattern.CLEAR_MORNING,
                story_phase_affinity=[StoryPhase.AWAKENING, StoryPhase.DISCIPLINE],
                time_of_day=(6, 10)
            ),
            
            "peaceful_trading": EnvironmentalCluster(
                cluster_id="peaceful_trading",
                name="Peaceful Trading Hours",
                base_clips=["river_gentle_lapping", "cotton_field_wind"],
                accent_clips=["spanish_moss_wind"],
                mood_association=AudioMood.CONTENT,
                weather_pattern=WeatherPattern.GENTLE_BREEZE,
                story_phase_affinity=[StoryPhase.DISCIPLINE, StoryPhase.MASTERY],
                time_of_day=(10, 16)
            ),
            
            "storm_warning": EnvironmentalCluster(
                cluster_id="storm_warning",
                name="Approaching Market Storm",
                base_clips=["storm_approach_wind"],
                accent_clips=["distant_thunder_rumble"],
                mood_association=AudioMood.CAUTIOUS,
                weather_pattern=WeatherPattern.APPROACHING_STORM,
                story_phase_affinity=[StoryPhase.EARLY_STRUGGLE, StoryPhase.AWAKENING]
            ),
            
            "evening_reflection": EnvironmentalCluster(
                cluster_id="evening_reflection",
                name="Evening Reflection Time",
                base_clips=["delta_river_flow", "evening_crickets"],
                accent_clips=["bullfrogs_night"],
                mood_association=AudioMood.SLEEPY,
                weather_pattern=WeatherPattern.CALM_EVENING,
                story_phase_affinity=[StoryPhase.MASTERY, StoryPhase.LEGACY],
                time_of_day=(18, 22)
            ),
            
            "renewal_after_storm": EnvironmentalCluster(
                cluster_id="renewal_after_storm",
                name="Renewal After the Storm",
                base_clips=["clearing_storm", "gentle_rain_start"],
                accent_clips=["morning_birds_delta"],
                mood_association=AudioMood.CONTENT,
                weather_pattern=WeatherPattern.SUMMER_RAIN,
                story_phase_affinity=[StoryPhase.AWAKENING, StoryPhase.DISCIPLINE]
            )
        }
        
        self.environmental_clusters.update(clusters)
    
    def _initialize_cultural_audio(self):
        """Initialize Mississippi cultural audio elements"""
        
        cultural_clips = {
            "church_bells_sunday": AudioClip(
                clip_id="church_bells_sunday",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CONTENT,
                file_path="mississippi/culture/church_bells.wav",
                duration=15.0,
                description="Sunday morning church bells",
                tags=["church", "sunday", "community", "peace"],
                volume=0.22
            ),
            
            "steamboat_distant": AudioClip(
                clip_id="steamboat_distant",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CONFIDENT,
                file_path="mississippi/culture/steamboat_horn.wav",
                duration=4.0,
                description="Distant steamboat horn on the river",
                tags=["steamboat", "river", "journey", "progress"],
                volume=0.18
            ),
            
            "front_porch_sounds": AudioClip(
                clip_id="front_porch_sounds",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CALM,
                file_path="mississippi/culture/front_porch.wav",
                duration=60.0,
                description="Gentle sounds of front porch evening",
                tags=["porch", "evening", "wisdom", "comfort"],
                loop=True,
                volume=0.15
            ),
            
            "distant_train_whistle": AudioClip(
                clip_id="distant_train_whistle",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.NOSTALGIC,
                file_path="mississippi/culture/train_whistle.wav",
                duration=6.0,
                description="Distant train whistle across the Delta",
                tags=["train", "distance", "journey", "nostalgia"],
                volume=0.16
            ),
            
            "delta_wind_chimes": AudioClip(
                clip_id="delta_wind_chimes",
                audio_type=AudioType.ENVIRONMENTAL,
                mood=AudioMood.CONTENT,
                file_path="mississippi/culture/wind_chimes.wav",
                duration=25.0,
                description="Gentle wind chimes on a Delta porch",
                tags=["chimes", "gentle", "home", "peace"],
                volume=0.14
            )
        }
        
        ambient_audio_engine.audio_clips.update(cultural_clips)
    
    def _setup_weather_patterns(self):
        """Setup weather pattern correlations with market conditions"""
        
        self.weather_market_correlations = {
            # Market conditions that trigger weather patterns
            'high_volatility': WeatherPattern.APPROACHING_STORM,
            'market_crash': WeatherPattern.APPROACHING_STORM,
            'steady_growth': WeatherPattern.GENTLE_BREEZE,
            'low_volume': WeatherPattern.CALM_EVENING,
            'market_open': WeatherPattern.CLEAR_MORNING,
            'market_close': WeatherPattern.CALM_EVENING,
            'profit_taking': WeatherPattern.SUMMER_RAIN,
            'news_release': WeatherPattern.APPROACHING_STORM,
            'weekend': WeatherPattern.NIGHT_CRICKETS
        }
    
    def _setup_seasonal_transitions(self):
        """Setup seasonal mood transitions based on user journey"""
        
        self.story_season_mapping = {
            StoryPhase.EARLY_STRUGGLE: SeasonalMood.WINTER_REFLECTION,
            StoryPhase.AWAKENING: SeasonalMood.SPRING_GROWTH,
            StoryPhase.DISCIPLINE: SeasonalMood.SUMMER_ABUNDANCE,
            StoryPhase.MASTERY: SeasonalMood.AUTUMN_HARVEST,
            StoryPhase.LEGACY: SeasonalMood.WINTER_REFLECTION  # Full circle
        }
    
    def determine_environmental_mood(self, user_id: str, market_context: Dict[str, Any]) -> str:
        """Determine appropriate environmental cluster for current context"""
        
        # Get user context
        story_context = norman_story_engine.get_user_story_context(user_id)
        current_hour = datetime.now().hour
        
        # Analyze market conditions
        volatility = market_context.get('volatility', 'medium')
        market_state = market_context.get('market_state', 'active')
        recent_events = market_context.get('recent_events', [])
        
        # Score each cluster
        best_cluster = None
        best_score = 0
        
        for cluster in self.environmental_clusters.values():
            score = 0
            
            # Story phase affinity
            if story_context.current_phase in cluster.story_phase_affinity:
                score += 10
            
            # Time of day match
            if cluster.time_of_day:
                start_hour, end_hour = cluster.time_of_day
                if start_hour <= current_hour <= end_hour:
                    score += 8
            
            # Market condition correlation
            if volatility == 'high' and cluster.weather_pattern == WeatherPattern.APPROACHING_STORM:
                score += 15
            elif volatility == 'low' and cluster.weather_pattern in [WeatherPattern.CALM_EVENING, WeatherPattern.GENTLE_BREEZE]:
                score += 12
            elif market_state == 'opening' and cluster.weather_pattern == WeatherPattern.CLEAR_MORNING:
                score += 10
            
            # Recent events influence
            if 'loss' in recent_events and cluster.cluster_id == 'storm_warning':
                score += 8
            elif 'profit' in recent_events and cluster.cluster_id == 'renewal_after_storm':
                score += 8
            
            if score > best_score:
                best_score = score
                best_cluster = cluster.cluster_id
        
        return best_cluster or 'peaceful_trading'
    
    async def start_ambient_environment(self, user_id: str, market_context: Dict[str, Any] = None) -> Optional[str]:
        """Start ambient environmental audio for user"""
        
        # Check user settings
        user_settings = get_user_settings(user_id)
        if not user_settings.sounds_enabled:
            return None
        
        # Stop any existing ambient loop
        await self.stop_ambient_environment(user_id)
        
        # Determine appropriate cluster
        cluster_id = self.determine_environmental_mood(user_id, market_context or {})
        cluster = self.environmental_clusters.get(cluster_id)
        
        if not cluster:
            return None
        
        # Start the ambient loop
        task = asyncio.create_task(self._ambient_environment_loop(user_id, cluster))
        self.active_ambient_loops[user_id] = task
        
        # Track user state
        self.user_ambient_states[user_id] = {
            'cluster_id': cluster_id,
            'start_time': datetime.now(),
            'clips_played': 0
        }
        
        logger.info(f"Started ambient environment '{cluster.name}' for user {user_id}")
        return cluster_id
    
    async def stop_ambient_environment(self, user_id: str):
        """Stop ambient environmental audio for user"""
        
        if user_id in self.active_ambient_loops:
            task = self.active_ambient_loops[user_id]
            task.cancel()
            del self.active_ambient_loops[user_id]
        
        if user_id in self.user_ambient_states:
            del self.user_ambient_states[user_id]
        
        logger.info(f"Stopped ambient environment for user {user_id}")
    
    async def _ambient_environment_loop(self, user_id: str, cluster: EnvironmentalCluster):
        """Main loop for playing ambient environmental audio"""
        
        try:
            while True:
                # Play base clips with random selection
                base_clip_id = random.choice(cluster.base_clips)
                base_clip = ambient_audio_engine.audio_clips.get(base_clip_id)
                
                if base_clip:
                    await ambient_audio_engine._simulate_audio_playback(base_clip)
                    
                    # Update state
                    if user_id in self.user_ambient_states:
                        self.user_ambient_states[user_id]['clips_played'] += 1
                
                # Occasionally add accent clips
                if random.random() < 0.3 and cluster.accent_clips:  # 30% chance
                    accent_clip_id = random.choice(cluster.accent_clips)
                    accent_clip = ambient_audio_engine.audio_clips.get(accent_clip_id)
                    
                    if accent_clip:
                        # Wait a bit then play accent
                        await asyncio.sleep(random.uniform(5, 15))
                        await ambient_audio_engine._simulate_audio_playback(accent_clip)
                
                # Wait before next base clip
                wait_time = random.uniform(30, 90)  # 30-90 seconds between clips
                await asyncio.sleep(wait_time)
                
        except asyncio.CancelledError:
            logger.info(f"Ambient environment loop cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"Error in ambient environment loop for user {user_id}: {e}")
    
    async def trigger_weather_event(self, user_id: str, weather_pattern: WeatherPattern) -> Optional[str]:
        """Trigger specific weather event"""
        
        user_settings = get_user_settings(user_id)
        if not user_settings.sounds_enabled:
            return None
        
        # Map weather patterns to appropriate clips
        weather_clip_map = {
            WeatherPattern.APPROACHING_STORM: "storm_approach_wind",
            WeatherPattern.SUMMER_RAIN: "gentle_rain_start",
            WeatherPattern.CLEAR_MORNING: "morning_birds_delta",
            WeatherPattern.CALM_EVENING: "evening_crickets",
            WeatherPattern.NIGHT_CRICKETS: "bullfrogs_night",
            WeatherPattern.RIVER_FLOW: "delta_river_flow"
        }
        
        clip_id = weather_clip_map.get(weather_pattern)
        if not clip_id:
            return None
        
        clip = ambient_audio_engine.audio_clips.get(clip_id)
        if not clip:
            return None
        
        # Play the weather event
        await ambient_audio_engine._simulate_audio_playback(clip)
        
        logger.info(f"Triggered weather event {weather_pattern.value} for user {user_id}")
        return f"weather_{weather_pattern.value}_{datetime.now().timestamp()}"
    
    async def play_cultural_moment(self, user_id: str, cultural_element: CulturalElement) -> Optional[str]:
        """Play cultural audio moment"""
        
        user_settings = get_user_settings(user_id)
        if not user_settings.sounds_enabled:
            return None
        
        # Map cultural elements to clips
        cultural_clip_map = {
            CulturalElement.CHURCH_BELLS: "church_bells_sunday",
            CulturalElement.STEAMBOAT_HORN: "steamboat_distant",
            CulturalElement.FRONT_PORCH: "front_porch_sounds"
        }
        
        clip_id = cultural_clip_map.get(cultural_element)
        if not clip_id:
            return None
        
        clip = ambient_audio_engine.audio_clips.get(clip_id)
        if not clip:
            return None
        
        # Play cultural moment
        await ambient_audio_engine._simulate_audio_playback(clip)
        
        logger.info(f"Played cultural moment {cultural_element.value} for user {user_id}")
        return f"cultural_{cultural_element.value}_{datetime.now().timestamp()}"
    
    def get_ambient_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get ambient audio statistics for user"""
        
        state = self.user_ambient_states.get(user_id, {})
        
        return {
            'active_cluster': state.get('cluster_id'),
            'session_duration': (datetime.now() - state.get('start_time')).total_seconds() if state.get('start_time') else 0,
            'clips_played': state.get('clips_played', 0),
            'is_active': user_id in self.active_ambient_loops,
            'available_clusters': list(self.environmental_clusters.keys())
        }

# Global instance
mississippi_ambient_engine = MississippiAmbientEngine()

# Convenience functions
async def start_delta_ambience(user_id: str, market_context: Dict[str, Any] = None) -> Optional[str]:
    """Start Mississippi Delta ambient audio"""
    return await mississippi_ambient_engine.start_ambient_environment(user_id, market_context)

async def stop_delta_ambience(user_id: str):
    """Stop Mississippi Delta ambient audio"""
    await mississippi_ambient_engine.stop_ambient_environment(user_id)

async def trigger_storm_warning(user_id: str) -> Optional[str]:
    """Trigger storm warning audio for market volatility"""
    return await mississippi_ambient_engine.trigger_weather_event(user_id, WeatherPattern.APPROACHING_STORM)

async def trigger_calm_after_storm(user_id: str) -> Optional[str]:
    """Trigger calming audio after market turbulence"""
    return await mississippi_ambient_engine.trigger_weather_event(user_id, WeatherPattern.SUMMER_RAIN)

async def play_sunday_bells(user_id: str) -> Optional[str]:
    """Play Sunday church bells during trading breaks"""
    return await mississippi_ambient_engine.play_cultural_moment(user_id, CulturalElement.CHURCH_BELLS)