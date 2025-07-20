#!/usr/bin/env python3
"""
🎭 Unified Personality Orchestrator for BITTEN
Combines all 3 personality layers into one cohesive system
- Adaptive Personality System (voice + evolution)
- Core Persona System (Norman's story + deep characters)
- Intel Bot Personalities (specialized trading roles)
"""

import os
import sys
import json
import random
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

# Add project paths
sys.path.insert(0, '/root/HydraX-v2/src')
sys.path.insert(0, '/root/HydraX-v2')

# Import all personality systems
from bitten_core.voice.personality_engine import PersonalityEngine
from bitten_core.voice.elevenlabs_voice_driver import ElevenLabsVoiceDriver
from bitten_core.voice.voice_personality_map import VOICE_PERSONALITY_MAP
from bitten_core.persona_system import (
    PersonaOrchestrator, PersonaType, EmotionalState, MarketSentiment
)

# Import Intel Bot personalities
try:
    from bitten_core.intel_bot_personalities import IntelBotPersonalities
except ImportError:
    IntelBotPersonalities = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('UnifiedPersonalityOrchestrator')

@dataclass
class UnifiedResponse:
    """Enhanced response that combines all personality layers"""
    primary_personality: str  # From adaptive system
    deep_persona: Optional[str] = None  # From core persona system
    intel_role: Optional[str] = None  # From intel bot system
    message: str = ""
    voice_message: Optional[str] = None
    voice_file: Optional[str] = None
    emotional_state: Optional[str] = None
    market_context: Optional[Dict] = None
    norman_story_element: Optional[str] = None
    visual_cue: Optional[str] = None
    audio_cue: Optional[str] = None
    action_required: Optional[str] = None
    evolution_triggered: bool = False

class UnifiedPersonalityOrchestrator:
    """
    Master orchestrator that combines all personality layers
    Creates a unified, evolving character experience
    """
    
    def __init__(self):
        # Initialize all personality systems
        self.adaptive_engine = PersonalityEngine()
        self.voice_driver = ElevenLabsVoiceDriver()
        self.core_personas = PersonaOrchestrator()
        
        # Initialize Intel Bot personalities if available
        self.intel_personalities = IntelBotPersonalities() if IntelBotPersonalities else None
        
        # Personality mapping between systems
        self.personality_mapping = {
            # Adaptive -> Core Persona -> Intel Role
            'DRILL_SERGEANT': {
                'core_persona': PersonaType.DRILL,
                'intel_role': 'DRILL',
                'voice_traits': ['aggressive', 'commanding', 'disciplined'],
                'story_elements': ['military_precision', 'family_discipline', 'mississippi_strength']
            },
            'DOC_AEGIS': {
                'core_persona': PersonaType.DOC,
                'intel_role': 'MEDIC',
                'voice_traits': ['caring', 'analytical', 'protective'],
                'story_elements': ['mother_wisdom', 'protection_instinct', 'healing_presence']
            },
            'RECRUITER': {
                'core_persona': PersonaType.NEXUS,
                'intel_role': 'MENTOR',
                'voice_traits': ['enthusiastic', 'social', 'inspiring'],
                'story_elements': ['community_building', 'network_growth', 'shared_success']
            },
            'OVERWATCH': {
                'core_persona': PersonaType.OVERWATCH,
                'intel_role': 'ANALYST',
                'voice_traits': ['strategic', 'analytical', 'tactical'],
                'story_elements': ['market_observation', 'tactical_awareness', 'truth_telling']
            },
            'STEALTH': {
                'core_persona': PersonaType.BIT,
                'intel_role': 'TECH',
                'voice_traits': ['minimal', 'precise', 'intuitive'],
                'story_elements': ['cat_intuition', 'silent_wisdom', 'glitch_sensing']
            },
            'ATHENA': {
                'core_persona': PersonaType.OVERWATCH,  # Strategic command overlap
                'intel_role': 'COMMANDER',
                'voice_traits': ['authoritative', 'strategic', 'protective', 'tactical'],
                'story_elements': ['strategic_command', 'mission_leadership', 'tactical_wisdom']
            }
        }
        
        # Enhanced emotional state mapping
        self.emotion_mapping = {
            'calm': EmotionalState.CALM,
            'focused': EmotionalState.FOCUSED,
            'stressed': EmotionalState.STRESSED,
            'impulsive': EmotionalState.IMPULSIVE,
            'defeated': EmotionalState.DEFEATED,
            'euphoric': EmotionalState.EUPHORIC,
            'learning': EmotionalState.LEARNING
        }
        
        # Norman's story elements for integration
        self.norman_story_elements = {
            'military_precision': [
                "Like Norman's father taught him about discipline and order",
                "This reminds Norman of his military training days",
                "Norman's father would be proud of this precision"
            ],
            'family_discipline': [
                "Norman's grandmother always said 'Work the plan, trust the process'",
                "This is Mississippi discipline at its finest",
                "Norman's family values showing through"
            ],
            'mother_wisdom': [
                "Norman's mother always protected what mattered most",
                "This is the caring wisdom Norman learned from his mother",
                "Norman's mother taught him to look after others"
            ],
            'community_building': [
                "Norman's vision of lifting up the Mississippi community",
                "This is what Norman dreamed of - people helping people",
                "Norman's network growing stronger, just like he planned"
            ],
            'cat_intuition': [
                "Bit the cat always knew before Norman did",
                "This is Bit's intuition working through the system",
                "Norman's cat Bit had this same sensing ability"
            ],
            'strategic_command': [
                "ATHENA embodies Norman's vision of intelligent leadership",
                "This is the strategic mind Norman always wanted to build",
                "Norman's dream of a tactical commander protecting traders"
            ],
            'mission_leadership': [
                "ATHENA carries Norman's protective instinct for his community",
                "This is Norman's legacy - an AI that truly cares about traders",
                "Norman's vision of guidance without abandonment"
            ],
            'tactical_wisdom': [
                "ATHENA combines Norman's analytical mind with Delta wisdom",
                "This represents Norman's balance of technology and humanity",
                "Norman's gift to traders - tactical intelligence with emotional grounding"
            ]
        }
        
        logger.info("✅ Unified Personality Orchestrator initialized")
    
    async def process_user_interaction(self, 
                                     user_id: str, 
                                     message_text: str,
                                     user_tier: str = "NIBBLER",
                                     user_action: str = None,
                                     market_context: Dict = None) -> UnifiedResponse:
        """
        Process user interaction through all personality layers
        Returns unified response with rich character depth
        """
        
        # 1. Get primary personality from adaptive system
        user_profile = self.adaptive_engine.get_user_profile(user_id)
        if not user_profile:
            self.adaptive_engine.assign_personality(user_id, user_tier)
            user_profile = self.adaptive_engine.get_user_profile(user_id)
        
        primary_personality = user_profile.get('personality', 'DRILL_SERGEANT')
        
        # 2. Analyze user behavior and update adaptive system
        if user_action:
            self.adaptive_engine.analyze_user_behavior(user_id, message_text, user_action)
        
        # 3. Get personality mapping for unified response
        personality_config = self.personality_mapping.get(primary_personality, {})
        core_persona = personality_config.get('core_persona')
        intel_role = personality_config.get('intel_role')
        
        # 4. Determine emotional state from context
        emotional_state = self._analyze_emotional_state(user_id, user_action, market_context)
        
        # 5. Create unified context
        unified_context = {
            'user_id': user_id,
            'user_tier': user_tier,
            'primary_personality': primary_personality,
            'emotional_state': emotional_state,
            'market_context': market_context or {},
            'recent_losses': user_profile.get('recent_losses', 0),
            'win_rate': user_profile.get('win_rate', 0.5),
            'days_active': user_profile.get('days_active', 0),
            'session_duration': user_profile.get('session_duration', 0),
            'personality_traits': personality_config.get('voice_traits', [])
        }
        
        # 6. Generate responses from all systems
        responses = await self._generate_unified_responses(
            message_text, unified_context, user_action
        )
        
        # 7. Combine and enhance the response
        unified_response = await self._combine_responses(responses, unified_context)
        
        # 8. Check for evolution triggers
        evolution_result = self._check_evolution_triggers(user_id, unified_context)
        if evolution_result:
            unified_response.evolution_triggered = True
            unified_response.message += f"\n\n🎭 *{evolution_result}*"
        
        return unified_response
    
    async def _generate_unified_responses(self, 
                                        message_text: str,
                                        context: Dict,
                                        user_action: str) -> Dict:
        """Generate responses from all personality systems"""
        
        responses = {}
        
        # 1. Adaptive personality response
        adaptive_response = self.adaptive_engine.format_personality_message(
            context['user_id'], message_text
        )
        responses['adaptive'] = adaptive_response
        
        # 2. Core persona response
        if context.get('primary_personality'):
            persona_responses = self.core_personas.get_response(
                context['user_id'],
                user_action or 'general_interaction',
                context
            )
            responses['core_personas'] = persona_responses
        
        # 3. Intel bot response (if available)
        if self.intel_personalities and context.get('intel_role'):
            intel_response = self.intel_personalities.get_response(
                context['intel_role'],
                user_action or 'general_interaction',
                context
            )
            responses['intel'] = intel_response
        
        return responses
    
    async def _combine_responses(self, responses: Dict, context: Dict) -> UnifiedResponse:
        """Combine all responses into one unified character response"""
        
        # Start with adaptive response as base
        adaptive_msg, voice_config = responses.get('adaptive', ("", {}))
        
        # Enhance with core persona depth
        persona_elements = []
        if 'core_personas' in responses:
            for persona_response in responses['core_personas']:
                if persona_response.message:
                    persona_elements.append(persona_response.message)
        
        # Add intel role specialization
        intel_enhancement = ""
        if 'intel' in responses and responses['intel']:
            intel_enhancement = responses['intel'].get('message', '')
        
        # Weave together the personality layers
        combined_message = self._weave_personality_layers(
            adaptive_msg, persona_elements, intel_enhancement, context
        )
        
        # Add Norman's story elements
        story_element = self._add_norman_story_context(context)
        
        # Generate voice if enabled
        voice_file = None
        if voice_config and context.get('voice_enabled'):
            try:
                voice_file = await self.voice_driver.generate_personality_voice(
                    combined_message, voice_config
                )
            except Exception as e:
                logger.error(f"Voice generation failed: {e}")
        
        # Create unified response
        unified_response = UnifiedResponse(
            primary_personality=context['primary_personality'],
            deep_persona=context.get('core_persona'),
            intel_role=context.get('intel_role'),
            message=combined_message,
            voice_file=voice_file,
            emotional_state=context.get('emotional_state'),
            market_context=context.get('market_context'),
            norman_story_element=story_element,
            visual_cue=self._get_visual_cue(context),
            audio_cue=self._get_audio_cue(context)
        )
        
        return unified_response
    
    def _weave_personality_layers(self, 
                                adaptive_msg: str,
                                persona_elements: List[str],
                                intel_enhancement: str,
                                context: Dict) -> str:
        """Weave all personality layers into one cohesive message"""
        
        # Start with adaptive message
        base_message = adaptive_msg
        
        # Add persona depth (20% chance for deeper character insight)
        if persona_elements and random.random() < 0.2:
            persona_insight = random.choice(persona_elements)
            # Clean up the persona message and integrate naturally
            if not persona_insight.startswith(base_message[:20]):
                base_message += f"\n\n*{persona_insight}*"
        
        # Add intel specialization for specific actions
        if intel_enhancement and context.get('user_action') in [
            'trade_analysis', 'risk_assessment', 'strategy_review'
        ]:
            base_message += f"\n\n📊 **{context.get('intel_role', 'ANALYST')}**: {intel_enhancement}"
        
        # Add personality-specific flavor
        personality_traits = context.get('personality_traits', [])
        if 'aggressive' in personality_traits:
            base_message = base_message.replace('.', '!').replace('?', '!')
        elif 'minimal' in personality_traits:
            # Keep message concise
            sentences = base_message.split('.')
            if len(sentences) > 2:
                base_message = '. '.join(sentences[:2]) + '.'
        
        return base_message
    
    def _add_norman_story_context(self, context: Dict) -> Optional[str]:
        """Add Norman's story elements to provide narrative depth"""
        
        # 10% chance to add story context
        if random.random() < 0.1:
            personality_config = self.personality_mapping.get(
                context['primary_personality'], {}
            )
            story_elements = personality_config.get('story_elements', [])
            
            if story_elements:
                story_type = random.choice(story_elements)
                story_options = self.norman_story_elements.get(story_type, [])
                if story_options:
                    return random.choice(story_options)
        
        return None
    
    def _analyze_emotional_state(self, 
                               user_id: str, 
                               user_action: str,
                               market_context: Dict) -> str:
        """Analyze user's emotional state across all systems"""
        
        # Get user profile for analysis
        user_profile = self.adaptive_engine.get_user_profile(user_id)
        if not user_profile:
            return 'calm'
        
        # Analyze based on actions and context
        if user_action == 'trade_execution':
            return 'focused'
        elif user_action == 'trade_failed':
            return 'stressed'
        elif user_action in ['help_request', 'question']:
            return 'learning'
        elif user_action == 'celebration':
            return 'euphoric'
        elif user_profile.get('recent_losses', 0) > 2:
            return 'defeated'
        elif user_profile.get('win_rate', 0.5) > 0.8:
            return 'euphoric'
        else:
            return 'calm'
    
    def _check_evolution_triggers(self, user_id: str, context: Dict) -> Optional[str]:
        """Check if personality evolution should be triggered"""
        
        user_profile = self.adaptive_engine.get_user_profile(user_id)
        if not user_profile:
            return None
        
        # Check for tier advancement
        current_tier = context.get('user_tier', 'NIBBLER')
        profile_tier = user_profile.get('tier', 'NIBBLER')
        
        if current_tier != profile_tier:
            result = self.adaptive_engine.evolve_personality(
                user_id, 'tier_advancement', {'new_tier': current_tier}
            )
            if result:
                return f"Your {context['primary_personality']} has evolved with your {current_tier} advancement!"
        
        # Check for behavioral milestones
        interaction_count = user_profile.get('interaction_count', 0)
        if interaction_count > 0 and interaction_count % 50 == 0:
            result = self.adaptive_engine.evolve_personality(
                user_id, 'milestone_reached', {'interactions': interaction_count}
            )
            if result:
                return f"Your {context['primary_personality']} has grown stronger through {interaction_count} interactions!"
        
        return None
    
    def _get_visual_cue(self, context: Dict) -> Optional[str]:
        """Get appropriate visual cue based on context"""
        
        personality = context.get('primary_personality', '')
        emotional_state = context.get('emotional_state', 'calm')
        
        visual_cues = {
            'DRILL_SERGEANT': {
                'focused': 'tactical_grid_overlay',
                'stressed': 'red_alert_flash',
                'euphoric': 'victory_display'
            },
            'DOC_AEGIS': {
                'focused': 'health_monitor_stable',
                'stressed': 'medical_alert',
                'defeated': 'recovery_mode'
            },
            'RECRUITER': {
                'focused': 'network_pulse',
                'euphoric': 'celebration_burst',
                'learning': 'knowledge_flow'
            },
            'OVERWATCH': {
                'focused': 'tactical_overview',
                'stressed': 'threat_assessment',
                'euphoric': 'market_dominance'
            },
            'STEALTH': {
                'focused': 'minimal_indicator',
                'stressed': 'shadow_mode',
                'euphoric': 'subtle_glow'
            }
        }
        
        return visual_cues.get(personality, {}).get(emotional_state)
    
    def _get_audio_cue(self, context: Dict) -> Optional[str]:
        """Get appropriate audio cue based on context"""
        
        personality = context.get('primary_personality', '')
        emotional_state = context.get('emotional_state', 'calm')
        
        audio_cues = {
            'DRILL_SERGEANT': {
                'focused': 'sharp_beep',
                'stressed': 'alarm_chirp',
                'euphoric': 'victory_fanfare'
            },
            'DOC_AEGIS': {
                'focused': 'steady_hum',
                'stressed': 'medical_beep',
                'defeated': 'comforting_tone'
            },
            'RECRUITER': {
                'focused': 'connection_chime',
                'euphoric': 'celebration_sound',
                'learning': 'knowledge_ping'
            },
            'OVERWATCH': {
                'focused': 'radar_ping',
                'stressed': 'alert_tone',
                'euphoric': 'success_notification'
            },
            'STEALTH': {
                'focused': 'soft_purr',
                'stressed': 'warning_chirp',
                'euphoric': 'content_purr'
            }
        }
        
        return audio_cues.get(personality, {}).get(emotional_state)
    
    async def get_personality_stats(self, user_id: str) -> Dict:
        """Get comprehensive personality stats across all systems"""
        
        # Get adaptive system stats
        adaptive_stats = self.adaptive_engine.get_personality_stats(user_id)
        
        # Get user profile
        user_profile = self.adaptive_engine.get_user_profile(user_id)
        
        # Get personality mapping
        primary_personality = user_profile.get('personality', 'DRILL_SERGEANT')
        personality_config = self.personality_mapping.get(primary_personality, {})
        
        # Combine stats
        unified_stats = {
            'primary_personality': primary_personality,
            'deep_persona': personality_config.get('core_persona', '').value if personality_config.get('core_persona') else None,
            'intel_role': personality_config.get('intel_role'),
            'voice_traits': personality_config.get('voice_traits', []),
            'adaptive_stats': adaptive_stats,
            'story_integration': len(personality_config.get('story_elements', [])),
            'system_layers': 3,  # Adaptive + Core + Intel
            'evolution_level': user_profile.get('evolution_stage', 0),
            'character_depth': 'Multi-layered with Norman\'s story integration'
        }
        
        return unified_stats
    
    async def force_personality_evolution(self, user_id: str, evolution_type: str, context: Dict) -> bool:
        """Force personality evolution across all systems"""
        
        result = self.adaptive_engine.evolve_personality(user_id, evolution_type, context)
        
        if result:
            # Update user profile with evolution
            user_profile = self.adaptive_engine.get_user_profile(user_id)
            logger.info(f"✅ Personality evolution triggered for {user_id}: {evolution_type}")
            return True
        
        return False


# Global unified orchestrator instance
unified_orchestrator = UnifiedPersonalityOrchestrator()