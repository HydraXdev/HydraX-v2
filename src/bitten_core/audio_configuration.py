"""
BITTEN Audio Configuration and Settings Management
Enhanced audio settings management for Bit's ambient audio system
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .user_settings import UserSettings, settings_manager
from .ambient_audio_system import AudioType, AudioMood
from .bit_memory_audio import MemoryTrigger
from .mississippi_ambient import WeatherPattern

logger = logging.getLogger(__name__)


class AudioQuality(Enum):
    """Audio quality settings"""
    LOW = "low"           # Minimal audio, basic chirps only
    MEDIUM = "medium"     # Standard audio experience
    HIGH = "high"         # Full audio experience
    ULTRA = "ultra"       # Maximum immersion


class FocusMode(Enum):
    """Focus modes that adjust audio behavior"""
    DISTRACTION_FREE = "distraction_free"  # Minimal audio only
    FOCUSED = "focused"                     # Reduced ambient, key events only
    BALANCED = "balanced"                   # Standard experience
    IMMERSIVE = "immersive"                # Full ambient experience


@dataclass
class BitAudioSettings:
    """Extended audio settings for Bit's system"""
    user_id: str
    
    # Basic audio controls
    master_volume: float = 0.8
    audio_quality: AudioQuality = AudioQuality.MEDIUM
    focus_mode: FocusMode = FocusMode.BALANCED
    
    # Bit's personality audio
    bit_chirps_enabled: bool = True
    bit_purrs_enabled: bool = True
    bit_meows_enabled: bool = True
    bit_memory_audio_enabled: bool = True
    
    # Environmental audio
    mississippi_ambient_enabled: bool = True
    weather_audio_enabled: bool = True
    cultural_audio_enabled: bool = True
    
    # Trading feedback audio
    trading_feedback_enabled: bool = True
    approval_sounds_enabled: bool = True
    warning_sounds_enabled: bool = True
    celebration_sounds_enabled: bool = True
    
    # Advanced settings
    adaptive_volume: bool = True          # Adjust volume based on time of day
    emotional_responsiveness: float = 0.8 # How responsive Bit is to user emotions
    ambient_frequency: float = 0.6        # How often ambient sounds play
    memory_trigger_sensitivity: float = 0.7 # How easily memories are triggered
    
    # Time-based settings
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    quiet_hours_volume_reduction: float = 0.3
    
    # Context awareness
    reduce_audio_during_news: bool = True
    enhance_audio_during_wins: bool = True
    comfort_audio_after_losses: bool = True
    
    # Accessibility
    visual_audio_indicators: bool = False  # Show visual indicators for audio events
    audio_descriptions: bool = False       # Text descriptions of audio events
    
    # Custom preferences
    favorite_audio_types: List[str] = None
    disabled_audio_types: List[str] = None
    custom_volume_levels: Dict[str, float] = None


class BitAudioConfigurationManager:
    """Manages Bit's audio configuration and settings"""
    
    def __init__(self, config_dir: str = "data/audio_config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Audio settings cache
        self.audio_settings_cache: Dict[str, BitAudioSettings] = {}
        
        # Default configurations for different scenarios
        self.preset_configurations = self._create_preset_configurations()
        
        # Audio validation rules
        self.validation_rules = self._setup_validation_rules()
    
    def _create_preset_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Create preset audio configurations"""
        
        return {
            "beginner_friendly": {
                "description": "Gentle audio experience for new traders",
                "settings": {
                    "audio_quality": AudioQuality.MEDIUM,
                    "focus_mode": FocusMode.FOCUSED,
                    "emotional_responsiveness": 0.9,
                    "comfort_audio_after_losses": True,
                    "trading_feedback_enabled": True,
                    "mississippi_ambient_enabled": False,
                    "celebration_sounds_enabled": True
                }
            },
            
            "experienced_trader": {
                "description": "Balanced audio for experienced traders",
                "settings": {
                    "audio_quality": AudioQuality.HIGH,
                    "focus_mode": FocusMode.BALANCED,
                    "emotional_responsiveness": 0.7,
                    "mississippi_ambient_enabled": True,
                    "bit_memory_audio_enabled": True,
                    "adaptive_volume": True
                }
            },
            
            "full_immersion": {
                "description": "Complete Norman's story experience",
                "settings": {
                    "audio_quality": AudioQuality.ULTRA,
                    "focus_mode": FocusMode.IMMERSIVE,
                    "emotional_responsiveness": 1.0,
                    "mississippi_ambient_enabled": True,
                    "cultural_audio_enabled": True,
                    "bit_memory_audio_enabled": True,
                    "weather_audio_enabled": True,
                    "ambient_frequency": 1.0
                }
            },
            
            "minimal_distraction": {
                "description": "Minimal audio for focused trading",
                "settings": {
                    "audio_quality": AudioQuality.LOW,
                    "focus_mode": FocusMode.DISTRACTION_FREE,
                    "bit_chirps_enabled": True,
                    "bit_purrs_enabled": False,
                    "mississippi_ambient_enabled": False,
                    "trading_feedback_enabled": True,
                    "approval_sounds_enabled": False,
                    "warning_sounds_enabled": True,
                    "emotional_responsiveness": 0.3
                }
            },
            
            "story_focused": {
                "description": "Emphasizes Norman's story and memories",
                "settings": {
                    "audio_quality": AudioQuality.HIGH,
                    "focus_mode": FocusMode.IMMERSIVE,
                    "bit_memory_audio_enabled": True,
                    "mississippi_ambient_enabled": True,
                    "cultural_audio_enabled": True,
                    "memory_trigger_sensitivity": 1.0,
                    "emotional_responsiveness": 0.9
                }
            }
        }
    
    def _setup_validation_rules(self) -> Dict[str, Any]:
        """Setup validation rules for audio settings"""
        
        return {
            "master_volume": {"min": 0.0, "max": 1.0},
            "emotional_responsiveness": {"min": 0.0, "max": 1.0},
            "ambient_frequency": {"min": 0.0, "max": 2.0},
            "memory_trigger_sensitivity": {"min": 0.0, "max": 1.0},
            "quiet_hours_volume_reduction": {"min": 0.0, "max": 1.0}
        }
    
    def get_user_audio_settings(self, user_id: str) -> BitAudioSettings:
        """Get comprehensive audio settings for user"""
        
        # Check cache first
        if user_id in self.audio_settings_cache:
            return self.audio_settings_cache[user_id]
        
        # Try to load from file
        settings_file = self.config_dir / f"audio_settings_{user_id}.json"
        
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                    
                    # Handle list fields
                    if data.get('favorite_audio_types') is None:
                        data['favorite_audio_types'] = []
                    if data.get('disabled_audio_types') is None:
                        data['disabled_audio_types'] = []
                    if data.get('custom_volume_levels') is None:
                        data['custom_volume_levels'] = {}
                    
                    # Convert enum strings back to enums
                    if 'audio_quality' in data:
                        data['audio_quality'] = AudioQuality(data['audio_quality'])
                    if 'focus_mode' in data:
                        data['focus_mode'] = FocusMode(data['focus_mode'])
                    
                    settings = BitAudioSettings(**data)
                    self.audio_settings_cache[user_id] = settings
                    return settings
                    
            except Exception as e:
                logger.error(f"Error loading audio settings for {user_id}: {e}")
        
        # Create default settings
        settings = BitAudioSettings(user_id=user_id)
        
        # Apply basic user settings if they exist
        basic_settings = settings_manager.get_user_settings(user_id)
        if basic_settings:
            settings.bit_chirps_enabled = basic_settings.sounds_enabled
            settings.trading_feedback_enabled = basic_settings.sounds_enabled
            settings.warning_sounds_enabled = basic_settings.warning_sounds
            settings.celebration_sounds_enabled = basic_settings.achievement_sounds
        
        self.audio_settings_cache[user_id] = settings
        self._save_audio_settings(settings)
        
        return settings
    
    def update_user_audio_settings(self, user_id: str, updates: Dict[str, Any]) -> BitAudioSettings:
        """Update user's audio settings"""
        
        settings = self.get_user_audio_settings(user_id)
        
        # Validate and apply updates
        for key, value in updates.items():
            if hasattr(settings, key):
                # Apply validation if rules exist
                if key in self.validation_rules:
                    rule = self.validation_rules[key]
                    if 'min' in rule and value < rule['min']:
                        value = rule['min']
                    if 'max' in rule and value > rule['max']:
                        value = rule['max']
                
                setattr(settings, key, value)
        
        # Save updated settings
        self._save_audio_settings(settings)
        
        # Update basic settings if needed
        self._sync_with_basic_settings(user_id, settings)
        
        logger.info(f"Updated audio settings for user {user_id}: {list(updates.keys())}")
        
        return settings
    
    def apply_preset_configuration(self, user_id: str, preset_name: str) -> BitAudioSettings:
        """Apply a preset configuration to user"""
        
        if preset_name not in self.preset_configurations:
            raise ValueError(f"Unknown preset configuration: {preset_name}")
        
        preset = self.preset_configurations[preset_name]
        preset_settings = preset['settings']
        
        # Convert enum strings to enums
        if 'audio_quality' in preset_settings:
            preset_settings['audio_quality'] = AudioQuality(preset_settings['audio_quality'])
        if 'focus_mode' in preset_settings:
            preset_settings['focus_mode'] = FocusMode(preset_settings['focus_mode'])
        
        # Apply the preset
        updated_settings = self.update_user_audio_settings(user_id, preset_settings)
        
        logger.info(f"Applied preset '{preset_name}' to user {user_id}")
        
        return updated_settings
    
    def _save_audio_settings(self, settings: BitAudioSettings):
        """Save audio settings to file"""
        
        settings_file = self.config_dir / f"audio_settings_{settings.user_id}.json"
        
        # Convert to dict and handle enums
        data = asdict(settings)
        data['audio_quality'] = settings.audio_quality.value
        data['focus_mode'] = settings.focus_mode.value
        
        with open(settings_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _sync_with_basic_settings(self, user_id: str, audio_settings: BitAudioSettings):
        """Sync with basic user settings"""
        
        # Update basic settings to match audio settings
        basic_updates = {
            'sounds_enabled': audio_settings.bit_chirps_enabled or audio_settings.trading_feedback_enabled,
            'warning_sounds': audio_settings.warning_sounds_enabled,
            'achievement_sounds': audio_settings.celebration_sounds_enabled
        }
        
        settings_manager.update_user_settings(user_id, basic_updates)
    
    def get_volume_for_audio_type(self, user_id: str, audio_type: AudioType) -> float:
        """Get effective volume for specific audio type"""
        
        settings = self.get_user_audio_settings(user_id)
        
        # Start with master volume
        volume = settings.master_volume
        
        # Apply audio type specific settings
        if not settings.bit_chirps_enabled and audio_type == AudioType.CHIRP:
            return 0.0
        if not settings.bit_purrs_enabled and audio_type == AudioType.PURR:
            return 0.0
        if not settings.mississippi_ambient_enabled and audio_type == AudioType.ENVIRONMENTAL:
            return 0.0
        if not settings.trading_feedback_enabled and audio_type == AudioType.TRADING_FEEDBACK:
            return 0.0
        
        # Apply custom volume levels
        type_key = audio_type.value
        if type_key in settings.custom_volume_levels:
            volume *= settings.custom_volume_levels[type_key]
        
        # Apply focus mode adjustments
        if settings.focus_mode == FocusMode.DISTRACTION_FREE:
            if audio_type in [AudioType.ENVIRONMENTAL, AudioType.AMBIENT]:
                volume *= 0.2
        elif settings.focus_mode == FocusMode.FOCUSED:
            if audio_type in [AudioType.ENVIRONMENTAL, AudioType.AMBIENT]:
                volume *= 0.5
        
        # Apply quiet hours if active
        if self._is_quiet_hours_active(settings):
            volume *= settings.quiet_hours_volume_reduction
        
        # Apply adaptive volume if enabled
        if settings.adaptive_volume:
            volume *= self._get_adaptive_volume_multiplier()
        
        return min(1.0, max(0.0, volume))
    
    def _is_quiet_hours_active(self, settings: BitAudioSettings) -> bool:
        """Check if quiet hours are currently active"""
        
        if not settings.quiet_hours_enabled:
            return False
        
        from datetime import datetime, time
        
        current_time = datetime.now().time()
        start_time = time.fromisoformat(settings.quiet_hours_start)
        end_time = time.fromisoformat(settings.quiet_hours_end)
        
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:
            # Quiet hours span midnight
            return current_time >= start_time or current_time <= end_time
    
    def _get_adaptive_volume_multiplier(self) -> float:
        """Get adaptive volume multiplier based on time of day"""
        
        from datetime import datetime
        
        hour = datetime.now().hour
        
        # Volume curve: quieter at night, normal during day
        if 22 <= hour or hour <= 6:
            return 0.4  # Night time
        elif 7 <= hour <= 9:
            return 0.7  # Early morning
        elif 10 <= hour <= 18:
            return 1.0  # Day time
        elif 19 <= hour <= 21:
            return 0.8  # Evening
        else:
            return 0.6  # Late evening
    
    def should_trigger_audio(self, user_id: str, audio_type: AudioType, 
                           context: Optional[str] = None) -> bool:
        """Check if audio should be triggered for user"""
        
        settings = self.get_user_audio_settings(user_id)
        
        # Check if audio type is disabled
        if audio_type.value in settings.disabled_audio_types:
            return False
        
        # Get effective volume
        volume = self.get_volume_for_audio_type(user_id, audio_type)
        if volume <= 0.0:
            return False
        
        # Apply frequency settings
        import random
        trigger_chance = settings.ambient_frequency
        
        if audio_type == AudioType.ENVIRONMENTAL:
            trigger_chance *= 0.8  # Environmental sounds are less frequent
        elif audio_type == AudioType.CHIRP:
            trigger_chance *= 1.2  # Chirps are more common
        
        return random.random() < trigger_chance
    
    def get_audio_context_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user's audio context preferences"""
        
        settings = self.get_user_audio_settings(user_id)
        
        return {
            'emotional_responsiveness': settings.emotional_responsiveness,
            'memory_trigger_sensitivity': settings.memory_trigger_sensitivity,
            'reduce_during_news': settings.reduce_audio_during_news,
            'enhance_during_wins': settings.enhance_audio_during_wins,
            'comfort_after_losses': settings.comfort_audio_after_losses,
            'focus_mode': settings.focus_mode.value,
            'audio_quality': settings.audio_quality.value
        }
    
    def export_user_settings(self, user_id: str) -> str:
        """Export user's audio settings as JSON"""
        
        settings = self.get_user_audio_settings(user_id)
        data = asdict(settings)
        data['audio_quality'] = settings.audio_quality.value
        data['focus_mode'] = settings.focus_mode.value
        
        return json.dumps(data, indent=2)
    
    def import_user_settings(self, user_id: str, json_data: str) -> BitAudioSettings:
        """Import user's audio settings from JSON"""
        
        try:
            data = json.loads(json_data)
            data['user_id'] = user_id  # Ensure correct user ID
            
            # Convert enum strings to enums
            if 'audio_quality' in data:
                data['audio_quality'] = AudioQuality(data['audio_quality'])
            if 'focus_mode' in data:
                data['focus_mode'] = FocusMode(data['focus_mode'])
            
            # Handle list/dict fields
            if data.get('favorite_audio_types') is None:
                data['favorite_audio_types'] = []
            if data.get('disabled_audio_types') is None:
                data['disabled_audio_types'] = []
            if data.get('custom_volume_levels') is None:
                data['custom_volume_levels'] = {}
            
            settings = BitAudioSettings(**data)
            self.audio_settings_cache[user_id] = settings
            self._save_audio_settings(settings)
            
            logger.info(f"Imported audio settings for user {user_id}")
            
            return settings
            
        except Exception as e:
            logger.error(f"Error importing audio settings: {e}")
            raise ValueError(f"Invalid audio settings format: {e}")
    
    def get_available_presets(self) -> Dict[str, str]:
        """Get available preset configurations"""
        
        return {
            name: config['description'] 
            for name, config in self.preset_configurations.items()
        }
    
    def get_audio_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get audio system statistics for user"""
        
        settings = self.get_user_audio_settings(user_id)
        
        # Count enabled features
        enabled_features = 0
        total_features = 0
        
        features = [
            'bit_chirps_enabled', 'bit_purrs_enabled', 'bit_meows_enabled',
            'bit_memory_audio_enabled', 'mississippi_ambient_enabled',
            'weather_audio_enabled', 'cultural_audio_enabled',
            'trading_feedback_enabled', 'approval_sounds_enabled',
            'warning_sounds_enabled', 'celebration_sounds_enabled'
        ]
        
        for feature in features:
            total_features += 1
            if getattr(settings, feature, False):
                enabled_features += 1
        
        return {
            'audio_quality': settings.audio_quality.value,
            'focus_mode': settings.focus_mode.value,
            'master_volume': settings.master_volume,
            'features_enabled': enabled_features,
            'total_features': total_features,
            'feature_usage_percentage': (enabled_features / total_features) * 100,
            'quiet_hours_active': self._is_quiet_hours_active(settings),
            'adaptive_volume_multiplier': self._get_adaptive_volume_multiplier() if settings.adaptive_volume else 1.0
        }


# Global instance
bit_audio_config_manager = BitAudioConfigurationManager()


# Convenience functions
def get_user_audio_config(user_id: str) -> BitAudioSettings:
    """Get user's audio configuration"""
    return bit_audio_config_manager.get_user_audio_settings(user_id)


def update_audio_config(user_id: str, updates: Dict[str, Any]) -> BitAudioSettings:
    """Update user's audio configuration"""
    return bit_audio_config_manager.update_user_audio_settings(user_id, updates)


def apply_audio_preset(user_id: str, preset_name: str) -> BitAudioSettings:
    """Apply audio preset to user"""
    return bit_audio_config_manager.apply_preset_configuration(user_id, preset_name)


def get_audio_volume(user_id: str, audio_type: AudioType) -> float:
    """Get effective volume for audio type"""
    return bit_audio_config_manager.get_volume_for_audio_type(user_id, audio_type)


def should_play_audio(user_id: str, audio_type: AudioType) -> bool:
    """Check if audio should be played"""
    return bit_audio_config_manager.should_trigger_audio(user_id, audio_type)