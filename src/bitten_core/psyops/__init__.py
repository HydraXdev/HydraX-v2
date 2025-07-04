# __init__.py
# PSYOPS SYSTEM - PSYCHOLOGICAL WARFARE INTEGRATION

"""
BITTEN PsyOps System - Ultra-sophisticated psychological profiling and manipulation

This system uses advanced psychological techniques to:
1. Profile users from minimal data (2 questions reveal everything)
2. Adapt bot personalities to each user's psychology
3. Track and manipulate emotional states in real-time
4. Orchestrate multi-bot interventions at optimal moments
5. Transform users through carefully designed psychological stages

WARNING: This system is designed for maximum psychological impact.
It learns, adapts, and evolves with each interaction.
"""

from .psychological_profiler import (
    PsychologicalProfiler,
    PsyOpsOrchestrator,
    PsychProfile,
    CoreDriver,
    TraumaOrigin,
    PsychArchetype
)

from .adaptive_bot_system import (
    AdaptiveBotSystem,
    PsyOpsCoordinator,
    BotPersonality,
    BotMood,
    RelationshipStage
)

from .emotion_engine import (
    EmotionalManipulationEngine,
    EmotionalMonitor,
    EmotionalState,
    EmotionalTrigger,
    EmotionalProfile
)

from .psyops_orchestrator import (
    MasterPsyOpsOrchestrator,
    UserPsychState,
    initialize_psyops_system
)

# Advanced Psychological Warfare Systems
from .disclaimer_manager import DisclaimerManager
from .psyops_controller import PsyOpsController
from .dopamine_cycle import DopamineCycleEngine, DopamineState, XPReward
from .bot_conflict_system import BotConflictEngine, BotConflict, ConflictType
from .secret_bot_unlock import SecretBotUnlockSystem, SecretBot, SecretLevel
from .threat_conditioning import ThreatConditioningEngine, Threat, ThreatLevel
from .false_narrative_forks import FalseNarrativeEngine, FalseNarrative, NarrativeType

# Quick initialization helper
async def create_psyops_system():
    """Create and initialize complete PsyOps system"""
    return await initialize_psyops_system()

# Onboarding questions that reveal everything
PROFILING_QUESTIONS = {
    "purpose": {
        "question": "Why are you really here?",
        "options": {
            "money": "I need to make money. Life demands it.",
            "revenge": "The market took from me. I'm taking it back.",
            "family": "I have people depending on me.",
            "glory": "I want to prove I'm better than others."
        }
    },
    "first_loss": {
        "question": "Your first major loss in life was:",
        "options": {
            "parent": "A parent who gave up on me.",
            "betrayal": "Someone I trusted completely.",
            "failure": "My own weakness and mistakes.",
            "powerless": "Forces beyond my control."
        }
    }
}

__all__ = [
    'PsychologicalProfiler',
    'PsyOpsOrchestrator',
    'PsychProfile',
    'CoreDriver',
    'TraumaOrigin',
    'PsychArchetype',
    'AdaptiveBotSystem',
    'PsyOpsCoordinator',
    'BotPersonality',
    'BotMood',
    'RelationshipStage',
    'EmotionalManipulationEngine',
    'EmotionalMonitor',
    'EmotionalState',
    'EmotionalTrigger',
    'EmotionalProfile',
    'MasterPsyOpsOrchestrator',
    'UserPsychState',
    'initialize_psyops_system',
    'create_psyops_system',
    'PROFILING_QUESTIONS',
    # Advanced Warfare Systems
    'DisclaimerManager',
    'PsyOpsController',
    'DopamineCycleEngine',
    'DopamineState', 
    'XPReward',
    'BotConflictEngine',
    'BotConflict',
    'ConflictType',
    'SecretBotUnlockSystem',
    'SecretBot',
    'SecretLevel',
    'ThreatConditioningEngine',
    'Threat',
    'ThreatLevel',
    'FalseNarrativeEngine',
    'FalseNarrative',
    'NarrativeType'
]