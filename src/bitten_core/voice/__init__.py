#!/usr/bin/env python3
"""
🎭 BITTEN Voice Personality System
Multi-personality voice-augmented AI system for Telegram bots
"""

from .voice_personality_map import (
    VOICE_PERSONALITY_MAP,
    PERSONALITY_ASSIGNMENT_RULES,
    EVOLUTION_TRIGGERS,
    get_personality_config,
    calculate_personality_score
)

from .personality_engine import PersonalityEngine, personality_engine
from .elevenlabs_voice_driver import ElevenLabsVoiceDriver, voice_driver

__all__ = [
    'VOICE_PERSONALITY_MAP',
    'PERSONALITY_ASSIGNMENT_RULES', 
    'EVOLUTION_TRIGGERS',
    'get_personality_config',
    'calculate_personality_score',
    'PersonalityEngine',
    'personality_engine',
    'ElevenLabsVoiceDriver',
    'voice_driver'
]

# Version info
__version__ = "1.0.0"
__description__ = "BITTEN Voice Personality System - Adaptive AI personalities with voice"