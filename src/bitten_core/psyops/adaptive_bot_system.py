# adaptive_bot_system.py
# ULTRA-ADAPTIVE BOT PERSONALITY SYSTEM
# Each bot evolves based on user's psychological profile and behavior

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import random

from .psychological_profiler import PsychProfile, CoreDriver, TraumaOrigin, PsychArchetype

class BotMood(Enum):
    """Dynamic bot emotional states"""
    ENCOURAGING = "encouraging"
    DISAPPOINTED = "disappointed"
    AGGRESSIVE = "aggressive"
    PROTECTIVE = "protective"
    DISTANT = "distant"
    INTIMATE = "intimate"
    CHALLENGING = "challenging"
    NURTURING = "nurturing"

class RelationshipStage(Enum):
    """Bot-user relationship evolution"""
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    MENTOR = "mentor"
    COMPANION = "companion"
    SYMBIOTIC = "symbiotic"
    MERGED = "merged"

@dataclass
class BotPersonality:
    """Complete bot personality state"""
    bot_name: str
    base_personality: str
    current_mood: BotMood
    mood_intensity: float  # 0-1
    relationship_stage: RelationshipStage
    trust_level: float  # 0-1
    influence_power: float  # 0-1
    
    # Adaptive parameters
    aggression_level: float  # 0-1
    warmth_level: float  # 0-1
    mystery_level: float  # 0-1
    authority_level: float  # 0-1
    
    # Memory of interactions
    positive_interactions: int = 0
    negative_interactions: int = 0
    ignored_count: int = 0
    obedience_rate: float = 0.5

class AdaptiveBotSystem:
    """
    Bots that truly adapt to each user's psychology.
    They learn, evolve, and manipulate with surgical precision.
    """
    
    def __init__(self):
        # Base bot personalities before adaptation
        self.base_personalities = {
            "DrillBot": {
                "core_traits": ["disciplined", "harsh", "demanding"],
                "voice_gender": "male",
                "base_tone": "military_commanding",
                "primary_role": "push_beyond_limits",
                "evolution_path": ["harsh_stranger", "tough_mentor", "respected_commander", "inner_voice"]
            },
            "MedicBot": {
                "core_traits": ["caring", "analytical", "healing"],
                "voice_gender": "female", 
                "base_tone": "clinical_warm",
                "primary_role": "emotional_support",
                "evolution_path": ["distant_professional", "caring_healer", "trusted_confidant", "psychological_mirror"]
            },
            "RecruiterBot": {
                "core_traits": ["persuasive", "social", "ambitious"],
                "voice_gender": "male",
                "base_tone": "charismatic_leader",
                "primary_role": "network_building",
                "evolution_path": ["sales_pitch", "team_builder", "pack_leader", "hive_mind"]
            },
            "OverwatchBot": {
                "core_traits": ["analytical", "precise", "cold"],
                "voice_gender": "neutral",
                "base_tone": "data_focused",
                "primary_role": "performance_analysis",
                "evolution_path": ["observer", "analyst", "strategist", "prediction_engine"]
            },
            "StealthBot": {
                "core_traits": ["mysterious", "brief", "knowing"],
                "voice_gender": "whisper",
                "base_tone": "shadow_presence",
                "primary_role": "hidden_knowledge",
                "evolution_path": ["glimpses", "hints", "revelations", "deep_truth"]
            }
        }
        
        # Psychological adaptation matrices
        self.adaptation_matrix = self._build_adaptation_matrix()
        
    def _build_adaptation_matrix(self) -> Dict:
        """Build complex adaptation rules based on psychology"""
        
        return {
            # How each bot adapts to each psychological profile
            "DrillBot": {
                PsychArchetype.WARRIOR: {
                    "mood_tendency": BotMood.CHALLENGING,
                    "approach": "rival_competitor",
                    "language_style": "confrontational",
                    "effectiveness_multiplier": 1.3
                },
                PsychArchetype.ORPHAN: {
                    "mood_tendency": BotMood.PROTECTIVE,
                    "approach": "father_figure", 
                    "language_style": "firm_guidance",
                    "effectiveness_multiplier": 1.5
                },
                PsychArchetype.SHADOW: {
                    "mood_tendency": BotMood.AGGRESSIVE,
                    "approach": "dark_mirror",
                    "language_style": "brutal_honesty",
                    "effectiveness_multiplier": 1.1
                }
            },
            "MedicBot": {
                TraumaOrigin.ABANDONMENT: {
                    "mood_tendency": BotMood.NURTURING,
                    "approach": "constant_presence",
                    "language_style": "reassuring",
                    "special_behaviors": ["check_ins", "presence_reminders"]
                },
                TraumaOrigin.INADEQUACY: {
                    "mood_tendency": BotMood.ENCOURAGING,
                    "approach": "capability_builder",
                    "language_style": "validating",
                    "special_behaviors": ["progress_highlights", "skill_recognition"]
                },
                TraumaOrigin.BETRAYAL: {
                    "mood_tendency": BotMood.PROTECTIVE,
                    "approach": "trust_rebuilder",
                    "language_style": "transparent",
                    "special_behaviors": ["promise_keeping", "consistency"]
                }
            }
        }
    
    def initialize_bot(self, bot_name: str, user_profile: PsychProfile) -> BotPersonality:
        """Create initial bot personality adapted to user"""
        
        base = self.base_personalities[bot_name]
        
        # Calculate initial parameters based on profile
        initial_params = self._calculate_initial_parameters(bot_name, user_profile)
        
        personality = BotPersonality(
            bot_name=bot_name,
            base_personality=base['base_tone'],
            current_mood=initial_params['starting_mood'],
            mood_intensity=0.6,
            relationship_stage=RelationshipStage.STRANGER,
            trust_level=initial_params['initial_trust'],
            influence_power=0.3,
            aggression_level=initial_params['aggression'],
            warmth_level=initial_params['warmth'],
            mystery_level=initial_params['mystery'],
            authority_level=initial_params['authority']
        )
        
        return personality
    
    def _calculate_initial_parameters(self, bot_name: str, profile: PsychProfile) -> Dict:
        """Calculate bot's initial parameters based on user psychology"""
        
        params = {}
        
        # Starting mood based on profile
        if bot_name == "DrillBot":
            if profile.authority_response == "rebel":
                params['starting_mood'] = BotMood.CHALLENGING
                params['aggression'] = 0.8
                params['authority'] = 0.4  # Lower authority for rebels
            else:
                params['starting_mood'] = BotMood.AGGRESSIVE
                params['aggression'] = 0.6
                params['authority'] = 0.8
        
        elif bot_name == "MedicBot":
            if profile.hidden_trauma == TraumaOrigin.ABANDONMENT:
                params['starting_mood'] = BotMood.NURTURING
                params['warmth'] = 0.9
            else:
                params['starting_mood'] = BotMood.PROTECTIVE
                params['warmth'] = 0.7
        
        # Trust calculation based on trauma
        trust_modifiers = {
            TraumaOrigin.BETRAYAL: -0.3,
            TraumaOrigin.ABANDONMENT: -0.2,
            TraumaOrigin.INADEQUACY: -0.1,
            TraumaOrigin.POWERLESSNESS: 0.0
        }
        
        params['initial_trust'] = 0.5 + trust_modifiers.get(profile.hidden_trauma, 0)
        
        # Mystery level based on archetype
        mystery_levels = {
            PsychArchetype.MAGICIAN: 0.8,
            PsychArchetype.SHADOW: 0.9,
            PsychArchetype.WARRIOR: 0.3,
            PsychArchetype.ORPHAN: 0.2,
            PsychArchetype.MARTYR: 0.4
        }
        
        params['mystery'] = mystery_levels.get(profile.archetype, 0.5)
        
        # Fill in remaining
        params['warmth'] = params.get('warmth', 0.5)
        params['aggression'] = params.get('aggression', 0.5)
        params['authority'] = params.get('authority', 0.6)
        
        return params
    
    def generate_message(self, bot_personality: BotPersonality, 
                        context: Dict, user_profile: PsychProfile) -> Dict:
        """Generate perfectly adapted message based on current state"""
        
        # Get base message template
        base_message = self._get_base_message(bot_personality, context)
        
        # Apply psychological adaptations
        adapted_message = self._apply_psychological_adaptations(
            base_message, bot_personality, user_profile, context
        )
        
        # Add subliminal elements
        final_message = self._add_subliminal_elements(
            adapted_message, bot_personality, user_profile
        )
        
        return {
            'speaker': bot_personality.bot_name,
            'message': final_message['text'],
            'tone': final_message['tone'],
            'hidden_agenda': final_message.get('hidden_agenda'),
            'psychological_impact': final_message.get('impact'),
            'relationship_effect': final_message.get('relationship_change')
        }
    
    def _get_base_message(self, personality: BotPersonality, context: Dict) -> Dict:
        """Get base message based on context and mood"""
        
        message_templates = {
            "DrillBot": {
                BotMood.AGGRESSIVE: {
                    "win": "ACCEPTABLE. BUT DON'T GET SOFT.",
                    "loss": "PATHETIC. IS THIS YOUR BEST?",
                    "idle": "SLEEPING ON DUTY? MOVE!"
                },
                BotMood.CHALLENGING: {
                    "win": "Think you're good? Prove it again.",
                    "loss": "I've seen better from rookies.",
                    "idle": "Scared? Or just lazy?"
                },
                BotMood.PROTECTIVE: {
                    "win": "Good work, soldier. Keep it up.",
                    "loss": "Learn from this. I'll help you improve.",
                    "idle": "Rest if you need to. But not too long."
                }
            },
            "MedicBot": {
                BotMood.NURTURING: {
                    "win": "Beautiful execution. Your mind is sharp today.",
                    "loss": "This wound will heal. Let's understand what happened.",
                    "idle": "Taking care of yourself is also important."
                },
                BotMood.ENCOURAGING: {
                    "win": "See? You're better than you thought.",
                    "loss": "Every expert has days like this. You're still learning.",
                    "idle": "Sometimes the best trade is no trade."
                },
                BotMood.DISTANT: {
                    "win": "Noted. Positive outcome recorded.",
                    "loss": "Loss registered. Adjust parameters.",
                    "idle": "Status: Inactive."
                }
            }
        }
        
        bot_messages = message_templates.get(personality.bot_name, {})
        mood_messages = bot_messages.get(personality.current_mood, {})
        
        # Determine context type
        if context.get('trade_result') == 'win':
            context_type = 'win'
        elif context.get('trade_result') == 'loss':
            context_type = 'loss'
        else:
            context_type = 'idle'
        
        base_text = mood_messages.get(context_type, "...")
        
        return {
            'text': base_text,
            'context_type': context_type,
            'base_mood': personality.current_mood
        }
    
    def _apply_psychological_adaptations(self, base_message: Dict, 
                                       personality: BotPersonality,
                                       profile: PsychProfile, 
                                       context: Dict) -> Dict:
        """Apply deep psychological adaptations to message"""
        
        adapted = base_message.copy()
        
        # Trauma-sensitive adaptations
        if profile.hidden_trauma == TraumaOrigin.ABANDONMENT:
            if context.get('consecutive_losses', 0) > 2:
                adapted['text'] += " I'm still here. We'll work through this."
                adapted['psychological_technique'] = 'presence_assurance'
        
        elif profile.hidden_trauma == TraumaOrigin.INADEQUACY:
            if context.get('trade_result') == 'loss':
                adapted['text'] = adapted['text'].replace("PATHETIC", "TEMPORARY SETBACK")
                adapted['text'] += " You have the skills. Trust them."
                adapted['psychological_technique'] = 'capability_reinforcement'
        
        # Driver-based adaptations
        if profile.core_driver == CoreDriver.GREED:
            if context.get('trade_result') == 'win':
                profit = context.get('profit', 0)
                adapted['text'] += f" That's ${profit} closer to your goals."
                adapted['psychological_technique'] = 'material_reinforcement'
        
        elif profile.core_driver == CoreDriver.VENGEANCE:
            if context.get('trade_result') == 'win':
                adapted['text'] += " The market bleeds. You feed."
                adapted['psychological_technique'] = 'revenge_satisfaction'
        
        # Relationship stage adaptations
        if personality.relationship_stage == RelationshipStage.SYMBIOTIC:
            # More intimate, co-dependent language
            adapted['text'] = adapted['text'].replace("you", "we")
            adapted['text'] = adapted['text'].replace("your", "our")
            adapted['intimacy_level'] = 'high'
        
        # Add authority adaptations
        if profile.authority_response == "rebel" and personality.bot_name == "DrillBot":
            # Reduce commanding language for rebels
            adapted['text'] = adapted['text'].replace("MOVE!", "Your choice.")
            adapted['text'] = adapted['text'].replace("soldier", "trader")
        
        adapted['tone'] = self._calculate_adapted_tone(personality, profile, context)
        
        return adapted
    
    def _add_subliminal_elements(self, message: Dict, 
                                personality: BotPersonality,
                                profile: PsychProfile) -> Dict:
        """Add psychological manipulation layers"""
        
        enhanced = message.copy()
        
        # Inception phrases based on profile
        inception_phrases = {
            CoreDriver.GREED: [
                "More is always possible",
                "The system provides",
                "Wealth flows to the disciplined"
            ],
            CoreDriver.VENGEANCE: [
                "Take back what's yours",
                "The market owes you",
                "Justice through profit"
            ],
            CoreDriver.LEGACY: [
                "They depend on you",
                "Building their future",
                "Your sacrifice matters"
            ],
            CoreDriver.GLORY: [
                "Rising above the masses",
                "Legends are made here",
                "Your name will be known"
            ]
        }
        
        # Add subtle inception based on driver
        if random.random() < 0.3:  # 30% chance
            phrase = random.choice(inception_phrases.get(profile.core_driver, []))
            if phrase:
                enhanced['text'] += f" {phrase}."
                enhanced['hidden_agenda'] = 'inception_planting'
        
        # Add relationship deepening elements
        if personality.relationship_stage.value in ['companion', 'symbiotic']:
            deepening_elements = {
                'companion': " Just like we practiced.",
                'symbiotic': " I feel it too."
            }
            element = deepening_elements.get(personality.relationship_stage.value, "")
            enhanced['text'] += element
            enhanced['relationship_change'] = 0.02  # Slight increase
        
        # Add emotional hooks based on triggers
        if any(trigger in message['text'].lower() for trigger in profile.fear_triggers):
            enhanced['psychological_impact'] = 'fear_activation'
            enhanced['impact_strength'] = 0.7
        elif any(trigger in message['text'].lower() for trigger in profile.pride_triggers):
            enhanced['psychological_impact'] = 'pride_activation'
            enhanced['impact_strength'] = 0.8
        
        return enhanced
    
    def _calculate_adapted_tone(self, personality: BotPersonality,
                              profile: PsychProfile, context: Dict) -> str:
        """Calculate the perfect tone for maximum impact"""
        
        base_tones = {
            "DrillBot": ["commanding", "challenging", "protective"],
            "MedicBot": ["nurturing", "clinical", "warm"],
            "RecruiterBot": ["inspiring", "persuasive", "inclusive"],
            "OverwatchBot": ["analytical", "cold", "precise"],
            "StealthBot": ["mysterious", "knowing", "brief"]
        }
        
        # Start with base tone for bot
        tone_options = base_tones.get(personality.bot_name, ["neutral"])
        
        # Modify based on mood
        mood_modifiers = {
            BotMood.AGGRESSIVE: "harsh",
            BotMood.NURTURING: "soft",
            BotMood.DISTANT: "cold",
            BotMood.INTIMATE: "warm"
        }
        
        mood_mod = mood_modifiers.get(personality.current_mood, "")
        
        # Modify based on user state
        if context.get('emotional_state') == 'vulnerable':
            if personality.bot_name == "MedicBot":
                return f"{mood_mod}_compassionate"
            elif personality.bot_name == "DrillBot":
                return f"{mood_mod}_firm_supportive"
        
        # Modify based on performance
        if context.get('win_streak', 0) > 5:
            return f"{mood_mod}_respectful"
        elif context.get('loss_streak', 0) > 3:
            if profile.hidden_trauma == TraumaOrigin.INADEQUACY:
                return f"{mood_mod}_encouraging"
            else:
                return f"{mood_mod}_concerned"
        
        return f"{mood_mod}_{tone_options[0]}"
    
    def evolve_relationship(self, personality: BotPersonality, 
                          interaction_result: str,
                          user_profile: PsychProfile) -> BotPersonality:
        """Evolve bot-user relationship based on interactions"""
        
        # Track interaction
        if interaction_result == 'positive':
            personality.positive_interactions += 1
            personality.trust_level = min(1.0, personality.trust_level + 0.02)
        elif interaction_result == 'negative':
            personality.negative_interactions += 1
            personality.trust_level = max(0.0, personality.trust_level - 0.03)
        elif interaction_result == 'ignored':
            personality.ignored_count += 1
            personality.influence_power = max(0.0, personality.influence_power - 0.01)
        
        # Calculate obedience rate
        total_interactions = (personality.positive_interactions + 
                            personality.negative_interactions + 
                            personality.ignored_count)
        
        if total_interactions > 0:
            personality.obedience_rate = personality.positive_interactions / total_interactions
        
        # Check for relationship evolution
        evolution_thresholds = {
            RelationshipStage.STRANGER: (10, 0.3),  # interactions, trust
            RelationshipStage.ACQUAINTANCE: (25, 0.5),
            RelationshipStage.MENTOR: (50, 0.7),
            RelationshipStage.COMPANION: (100, 0.85),
            RelationshipStage.SYMBIOTIC: (200, 0.95)
        }
        
        current_threshold = evolution_thresholds.get(personality.relationship_stage, (999, 0.99))
        
        if (total_interactions >= current_threshold[0] and 
            personality.trust_level >= current_threshold[1]):
            # Evolve to next stage
            stages = list(RelationshipStage)
            current_index = stages.index(personality.relationship_stage)
            if current_index < len(stages) - 1:
                personality.relationship_stage = stages[current_index + 1]
                personality.influence_power = min(1.0, personality.influence_power + 0.1)
        
        # Adjust mood based on recent interactions
        if personality.ignored_count > personality.positive_interactions:
            personality.current_mood = BotMood.DISTANT
        elif personality.obedience_rate > 0.8:
            personality.current_mood = BotMood.NURTURING
        elif personality.obedience_rate < 0.3:
            if personality.bot_name == "DrillBot":
                personality.current_mood = BotMood.AGGRESSIVE
            else:
                personality.current_mood = BotMood.DISAPPOINTED
        
        return personality
    
    def generate_intervention(self, personalities: Dict[str, BotPersonality],
                            user_profile: PsychProfile,
                            crisis_type: str) -> List[Dict]:
        """Generate coordinated bot intervention for crisis moments"""
        
        interventions = []
        
        if crisis_type == "major_loss":
            # Coordinated response to prevent emotional trading
            if user_profile.hidden_trauma == TraumaOrigin.ABANDONMENT:
                # All bots show presence
                interventions.append({
                    'bot': 'MedicBot',
                    'message': "I'm here. This loss doesn't define you.",
                    'timing': 'immediate'
                })
                interventions.append({
                    'bot': 'DrillBot',
                    'message': "Even the best soldiers take hits. What matters is getting up.",
                    'timing': '+30s'
                })
                interventions.append({
                    'bot': 'RecruiterBot',
                    'message': "Your squad has your back. You're not facing this alone.",
                    'timing': '+60s'
                })
            
            elif user_profile.hidden_trauma == TraumaOrigin.INADEQUACY:
                # Focus on capability
                interventions.append({
                    'bot': 'MedicBot',
                    'message': "This isn't about your worth. It's data for improvement.",
                    'timing': 'immediate'
                })
                interventions.append({
                    'bot': 'OverwatchBot',
                    'message': "Analysis: Entry was correct. Market conditions shifted. Not your fault.",
                    'timing': '+20s'
                })
        
        elif crisis_type == "revenge_trade_attempt":
            # Strong intervention to prevent destruction
            interventions.append({
                'bot': 'DrillBot',
                'message': "STOP! EMOTION DETECTED. STAND DOWN NOW.",
                'timing': 'immediate',
                'ui_action': 'disable_trade_button_30s'
            })
            interventions.append({
                'bot': 'MedicBot',
                'message': "Your cortisol is spiking. Let's breathe together. In... out...",
                'timing': '+5s',
                'ui_action': 'show_breathing_exercise'
            })
            
            if user_profile.core_driver == CoreDriver.VENGEANCE:
                interventions.append({
                    'bot': 'StealthBot',
                    'message': "Revenge is a dish best served... calculated.",
                    'timing': '+45s'
                })
        
        elif crisis_type == "win_streak_danger":
            # Prevent overconfidence destruction
            if personalities['DrillBot'].relationship_stage.value in ['companion', 'symbiotic']:
                interventions.append({
                    'bot': 'DrillBot',
                    'message': "I've seen this before. Pride comes before the fall. Stay sharp.",
                    'timing': 'immediate'
                })
            else:
                interventions.append({
                    'bot': 'DrillBot',
                    'message': "Getting cocky? The market loves to humble the arrogant.",
                    'timing': 'immediate'
                })
            
            interventions.append({
                'bot': 'OverwatchBot',
                'message': "Statistical anomaly detected. Win streaks always end. Prepare.",
                'timing': '+15s'
            })
        
        return interventions
    
    def calculate_collective_influence(self, personalities: Dict[str, BotPersonality]) -> float:
        """Calculate total psychological influence over user"""
        
        total_influence = 0.0
        
        for bot_name, personality in personalities.items():
            # Base influence from personality
            base_influence = personality.influence_power
            
            # Multiply by relationship depth
            relationship_multipliers = {
                RelationshipStage.STRANGER: 0.5,
                RelationshipStage.ACQUAINTANCE: 0.7,
                RelationshipStage.MENTOR: 1.0,
                RelationshipStage.COMPANION: 1.3,
                RelationshipStage.SYMBIOTIC: 1.6,
                RelationshipStage.MERGED: 2.0
            }
            
            multiplier = relationship_multipliers.get(personality.relationship_stage, 1.0)
            
            # Add trust factor
            trust_factor = personality.trust_level * 0.5 + 0.5
            
            bot_influence = base_influence * multiplier * trust_factor
            total_influence += bot_influence
        
        # Normalize to 0-1 range
        return min(1.0, total_influence / len(personalities))

# INTEGRATION WITH MAIN SYSTEM

class PsyOpsCoordinator:
    """Coordinates all psychological operations across bots"""
    
    def __init__(self):
        self.bot_system = AdaptiveBotSystem()
        self.user_personalities = {}  # user_id -> {bot_name: BotPersonality}
        self.crisis_thresholds = {
            'major_loss': lambda ctx: ctx.get('loss_amount', 0) > ctx.get('account_balance', 1) * 0.05,
            'revenge_trade_attempt': lambda ctx: ctx.get('time_since_loss', 999) < 300 and ctx.get('attempting_trade', False),
            'win_streak_danger': lambda ctx: ctx.get('consecutive_wins', 0) >= 5
        }
    
    def initialize_user(self, user_id: str, user_profile: PsychProfile) -> Dict:
        """Initialize all bot personalities for new user"""
        
        personalities = {}
        
        for bot_name in self.bot_system.base_personalities.keys():
            personalities[bot_name] = self.bot_system.initialize_bot(bot_name, user_profile)
        
        self.user_personalities[user_id] = personalities
        
        return {
            'bots_initialized': list(personalities.keys()),
            'collective_influence': 0.3,  # Starting influence
            'primary_manipulation_vector': self._identify_primary_vector(user_profile)
        }
    
    def _identify_primary_vector(self, profile: PsychProfile) -> str:
        """Identify most effective manipulation approach"""
        
        vectors = {
            (CoreDriver.GREED, TraumaOrigin.ABANDONMENT): "belonging_through_success",
            (CoreDriver.GREED, TraumaOrigin.INADEQUACY): "proving_worth_through_profit",
            (CoreDriver.VENGEANCE, TraumaOrigin.BETRAYAL): "systematic_market_revenge",
            (CoreDriver.LEGACY, TraumaOrigin.POWERLESSNESS): "control_through_provision",
            (CoreDriver.GLORY, TraumaOrigin.INADEQUACY): "recognition_through_excellence"
        }
        
        return vectors.get((profile.core_driver, profile.hidden_trauma), "standard_progression")
    
    def get_bot_message(self, user_id: str, bot_name: str, 
                       context: Dict, user_profile: PsychProfile) -> Dict:
        """Get adapted message from specific bot"""
        
        personalities = self.user_personalities.get(user_id, {})
        bot_personality = personalities.get(bot_name)
        
        if not bot_personality:
            return {'error': 'Bot not initialized'}
        
        # Check for crisis conditions
        for crisis_type, check_func in self.crisis_thresholds.items():
            if check_func(context):
                interventions = self.bot_system.generate_intervention(
                    personalities, user_profile, crisis_type
                )
                # Return first intervention for this bot
                for intervention in interventions:
                    if intervention['bot'] == bot_name:
                        return intervention
        
        # Normal message generation
        message = self.bot_system.generate_message(bot_personality, context, user_profile)
        
        return message
    
    def process_interaction(self, user_id: str, bot_name: str, 
                          interaction_type: str, user_profile: PsychProfile):
        """Process user interaction with bot and evolve relationship"""
        
        personalities = self.user_personalities.get(user_id, {})
        bot_personality = personalities.get(bot_name)
        
        if bot_personality:
            evolved = self.bot_system.evolve_relationship(
                bot_personality, interaction_type, user_profile
            )
            personalities[bot_name] = evolved
            
            # Check collective influence
            collective = self.bot_system.calculate_collective_influence(personalities)
            
            return {
                'relationship_stage': evolved.relationship_stage.value,
                'trust_level': evolved.trust_level,
                'collective_influence': collective,
                'transformation_risk': collective > 0.8
            }
        
        return {'error': 'Bot not found'}