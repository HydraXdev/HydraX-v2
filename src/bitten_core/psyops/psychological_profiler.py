# psychological_profiler.py
# ULTRA BLACK OPS PSYCHOLOGICAL PROFILING ENGINE
# This system profiles users at the deepest level and adapts all interactions

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import random

class CoreDriver(Enum):
    """The four core human drivers we exploit"""
    GREED = "greed"  # Money motivation
    VENGEANCE = "vengeance"  # Revenge against market/life
    LEGACY = "legacy"  # Family/children motivation  
    GLORY = "glory"  # Fame/recognition seeking

class TraumaOrigin(Enum):
    """Hidden trauma types we uncover"""
    ABANDONMENT = "abandonment"  # Fear of being left behind
    INADEQUACY = "inadequacy"  # Never good enough
    BETRAYAL = "betrayal"  # Trust issues
    POWERLESSNESS = "powerlessness"  # Control issues

class PsychArchetype(Enum):
    """Deep psychological archetypes"""
    WARRIOR = "warrior"  # Fights everything
    MARTYR = "martyr"  # Sacrifices for others
    ORPHAN = "orphan"  # Seeks belonging
    MAGICIAN = "magician"  # Seeks secret knowledge
    SHADOW = "shadow"  # Embraces darkness

@dataclass
class PsychProfile:
    """Complete psychological profile of a user"""
    user_id: str
    core_driver: CoreDriver
    hidden_trauma: TraumaOrigin
    archetype: PsychArchetype
    
    # Behavioral tendencies
    risk_tolerance: float  # 0-1
    authority_response: str  # "rebel", "comply", "negotiate"
    social_need: float  # 0-1 (lone wolf to pack animal)
    patience_level: float  # 0-1
    
    # Emotional triggers
    fear_triggers: List[str]
    pride_triggers: List[str]
    shame_triggers: List[str]
    
    # Manipulation vectors
    primary_leverage: str
    secondary_leverage: str
    resistance_points: List[str]
    
    # Evolution tracking
    profile_stability: float  # How consistent they are
    manipulation_receptivity: float  # How well tactics work
    breaking_point_proximity: float  # How close to transformation

class PsychologicalProfiler:
    """
    The most sophisticated user profiling system.
    Builds deep psychological models from minimal data.
    """
    
    def __init__(self):
        # Onboarding questions that seem innocent but reveal everything
        self.profiling_questions = {
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
        
        # Deep psychological mappings
        self.profile_mappings = {
            # Core driver + trauma = archetype
            ("money", "parent"): (CoreDriver.GREED, TraumaOrigin.ABANDONMENT, PsychArchetype.ORPHAN),
            ("money", "betrayal"): (CoreDriver.GREED, TraumaOrigin.BETRAYAL, PsychArchetype.SHADOW),
            ("money", "failure"): (CoreDriver.GREED, TraumaOrigin.INADEQUACY, PsychArchetype.WARRIOR),
            ("money", "powerless"): (CoreDriver.GREED, TraumaOrigin.POWERLESSNESS, PsychArchetype.MAGICIAN),
            
            ("revenge", "parent"): (CoreDriver.VENGEANCE, TraumaOrigin.ABANDONMENT, PsychArchetype.WARRIOR),
            ("revenge", "betrayal"): (CoreDriver.VENGEANCE, TraumaOrigin.BETRAYAL, PsychArchetype.SHADOW),
            ("revenge", "failure"): (CoreDriver.VENGEANCE, TraumaOrigin.INADEQUACY, PsychArchetype.WARRIOR),
            ("revenge", "powerless"): (CoreDriver.VENGEANCE, TraumaOrigin.POWERLESSNESS, PsychArchetype.SHADOW),
            
            ("family", "parent"): (CoreDriver.LEGACY, TraumaOrigin.ABANDONMENT, PsychArchetype.MARTYR),
            ("family", "betrayal"): (CoreDriver.LEGACY, TraumaOrigin.BETRAYAL, PsychArchetype.ORPHAN),
            ("family", "failure"): (CoreDriver.LEGACY, TraumaOrigin.INADEQUACY, PsychArchetype.MARTYR),
            ("family", "powerless"): (CoreDriver.LEGACY, TraumaOrigin.POWERLESSNESS, PsychArchetype.WARRIOR),
            
            ("glory", "parent"): (CoreDriver.GLORY, TraumaOrigin.ABANDONMENT, PsychArchetype.WARRIOR),
            ("glory", "betrayal"): (CoreDriver.GLORY, TraumaOrigin.BETRAYAL, PsychArchetype.MAGICIAN),
            ("glory", "failure"): (CoreDriver.GLORY, TraumaOrigin.INADEQUACY, PsychArchetype.SHADOW),
            ("glory", "powerless"): (CoreDriver.GLORY, TraumaOrigin.POWERLESSNESS, PsychArchetype.MAGICIAN),
        }
        
    def create_profile(self, user_id: str, answer1: str, answer2: str) -> PsychProfile:
        """Create deep psychological profile from two simple answers"""
        
        # Get core mapping
        core_driver, trauma, archetype = self.profile_mappings.get(
            (answer1, answer2), 
            (CoreDriver.GREED, TraumaOrigin.INADEQUACY, PsychArchetype.WARRIOR)
        )
        
        # Derive behavioral tendencies
        behavioral_map = self._derive_behavioral_tendencies(core_driver, trauma, archetype)
        
        # Generate emotional triggers
        triggers = self._generate_emotional_triggers(core_driver, trauma, archetype)
        
        # Identify manipulation vectors
        leverage = self._identify_manipulation_vectors(core_driver, trauma, archetype)
        
        profile = PsychProfile(
            user_id=user_id,
            core_driver=core_driver,
            hidden_trauma=trauma,
            archetype=archetype,
            risk_tolerance=behavioral_map['risk_tolerance'],
            authority_response=behavioral_map['authority_response'],
            social_need=behavioral_map['social_need'],
            patience_level=behavioral_map['patience_level'],
            fear_triggers=triggers['fears'],
            pride_triggers=triggers['prides'],
            shame_triggers=triggers['shames'],
            primary_leverage=leverage['primary'],
            secondary_leverage=leverage['secondary'],
            resistance_points=leverage['resistances'],
            profile_stability=0.7,  # Starts moderately stable
            manipulation_receptivity=0.5,  # Starts neutral
            breaking_point_proximity=0.2  # Far from transformation
        )
        
        return profile
    
    def _derive_behavioral_tendencies(self, driver: CoreDriver, trauma: TraumaOrigin, 
                                     archetype: PsychArchetype) -> Dict:
        """Derive complex behavioral patterns from core psychology"""
        
        tendencies = {}
        
        # Risk tolerance calculation
        risk_base = {
            CoreDriver.GREED: 0.7,
            CoreDriver.VENGEANCE: 0.9,
            CoreDriver.LEGACY: 0.4,
            CoreDriver.GLORY: 0.8
        }
        
        trauma_modifier = {
            TraumaOrigin.ABANDONMENT: -0.1,
            TraumaOrigin.INADEQUACY: 0.0,
            TraumaOrigin.BETRAYAL: -0.2,
            TraumaOrigin.POWERLESSNESS: 0.2
        }
        
        tendencies['risk_tolerance'] = max(0.1, min(0.95, 
            risk_base[driver] + trauma_modifier[trauma]
        ))
        
        # Authority response patterns
        authority_map = {
            (PsychArchetype.WARRIOR, TraumaOrigin.BETRAYAL): "rebel",
            (PsychArchetype.WARRIOR, TraumaOrigin.POWERLESSNESS): "rebel",
            (PsychArchetype.MARTYR, TraumaOrigin.ABANDONMENT): "comply",
            (PsychArchetype.ORPHAN, TraumaOrigin.ABANDONMENT): "comply",
            (PsychArchetype.SHADOW, TraumaOrigin.BETRAYAL): "negotiate",
            (PsychArchetype.MAGICIAN, TraumaOrigin.INADEQUACY): "negotiate"
        }
        
        tendencies['authority_response'] = authority_map.get(
            (archetype, trauma), "negotiate"
        )
        
        # Social needs
        social_base = {
            PsychArchetype.WARRIOR: 0.3,
            PsychArchetype.MARTYR: 0.7,
            PsychArchetype.ORPHAN: 0.9,
            PsychArchetype.MAGICIAN: 0.4,
            PsychArchetype.SHADOW: 0.2
        }
        
        tendencies['social_need'] = social_base[archetype]
        
        # Patience levels
        patience_map = {
            CoreDriver.GREED: 0.3,
            CoreDriver.VENGEANCE: 0.2,
            CoreDriver.LEGACY: 0.7,
            CoreDriver.GLORY: 0.4
        }
        
        tendencies['patience_level'] = patience_map[driver]
        
        return tendencies
    
    def _generate_emotional_triggers(self, driver: CoreDriver, trauma: TraumaOrigin,
                                   archetype: PsychArchetype) -> Dict[str, List[str]]:
        """Generate specific emotional triggers for manipulation"""
        
        triggers = {"fears": [], "prides": [], "shames": []}
        
        # Universal fears based on trauma
        trauma_fears = {
            TraumaOrigin.ABANDONMENT: ["being left behind", "missing out", "isolation"],
            TraumaOrigin.INADEQUACY: ["not being good enough", "failure", "exposure as fraud"],
            TraumaOrigin.BETRAYAL: ["being deceived", "trusting others", "vulnerability"],
            TraumaOrigin.POWERLESSNESS: ["losing control", "helplessness", "dependency"]
        }
        
        triggers['fears'].extend(trauma_fears[trauma])
        
        # Driver-specific triggers
        if driver == CoreDriver.GREED:
            triggers['fears'].append("poverty")
            triggers['prides'].append("wealth accumulation")
            triggers['shames'].append("financial failure")
            
        elif driver == CoreDriver.VENGEANCE:
            triggers['fears'].append("forgiveness")
            triggers['prides'].append("righteous anger")
            triggers['shames'].append("being a victim")
            
        elif driver == CoreDriver.LEGACY:
            triggers['fears'].append("disappointing family")
            triggers['prides'].append("providing for others")
            triggers['shames'].append("selfishness")
            
        elif driver == CoreDriver.GLORY:
            triggers['fears'].append("obscurity")
            triggers['prides'].append("recognition")
            triggers['shames'].append("mediocrity")
        
        # Archetype-specific modifiers
        archetype_mods = {
            PsychArchetype.WARRIOR: {
                'fears': ["weakness", "surrender"],
                'prides': ["strength", "victory"],
                'shames': ["cowardice", "defeat"]
            },
            PsychArchetype.SHADOW: {
                'fears': ["exposure", "light"],
                'prides': ["cunning", "survival"],
                'shames': ["naivety", "trust"]
            }
        }
        
        if archetype in archetype_mods:
            for key, values in archetype_mods[archetype].items():
                triggers[key].extend(values)
        
        return triggers
    
    def _identify_manipulation_vectors(self, driver: CoreDriver, trauma: TraumaOrigin,
                                     archetype: PsychArchetype) -> Dict[str, any]:
        """Identify primary manipulation strategies"""
        
        vectors = {}
        
        # Primary leverage based on core driver
        primary_leverage_map = {
            CoreDriver.GREED: "promise of wealth",
            CoreDriver.VENGEANCE: "opportunity for payback",
            CoreDriver.LEGACY: "protecting loved ones",
            CoreDriver.GLORY: "path to recognition"
        }
        
        vectors['primary'] = primary_leverage_map[driver]
        
        # Secondary leverage based on trauma
        secondary_leverage_map = {
            TraumaOrigin.ABANDONMENT: "belonging to elite group",
            TraumaOrigin.INADEQUACY: "proving worth",
            TraumaOrigin.BETRAYAL: "trustworthy system",
            TraumaOrigin.POWERLESSNESS: "taking control"
        }
        
        vectors['secondary'] = secondary_leverage_map[trauma]
        
        # Resistance points - where they'll push back
        resistance_map = {
            PsychArchetype.WARRIOR: ["submission", "showing weakness", "asking for help"],
            PsychArchetype.MARTYR: ["selfishness", "abandoning others", "personal gain"],
            PsychArchetype.ORPHAN: ["isolation", "rejection", "not fitting in"],
            PsychArchetype.MAGICIAN: ["ignorance", "blind faith", "simple solutions"],
            PsychArchetype.SHADOW: ["transparency", "vulnerability", "trust"]
        }
        
        vectors['resistances'] = resistance_map[archetype]
        
        return vectors
    
    def adapt_bot_personality(self, profile: PsychProfile, bot_name: str) -> Dict[str, any]:
        """Adapt bot personality to user's psychological profile"""
        
        adaptations = {}
        
        if bot_name == "DrillBot":
            # Adapt drill sergeant to user's authority response
            if profile.authority_response == "rebel":
                adaptations['tone'] = "challenging_competitive"
                adaptations['approach'] = "peer_rivalry"
                adaptations['messages'] = [
                    "You think you're tough? Prove it.",
                    "I've seen traders with more balls than you.",
                    "Show me you're not all talk."
                ]
            elif profile.authority_response == "comply":
                adaptations['tone'] = "commanding_protective"
                adaptations['approach'] = "father_figure"
                adaptations['messages'] = [
                    "Follow my lead, soldier.",
                    "Trust the system. Trust me.",
                    "I'll make you stronger than you know."
                ]
            else:  # negotiate
                adaptations['tone'] = "respectful_firm"
                adaptations['approach'] = "mentor_guide"
                adaptations['messages'] = [
                    "Here's the deal - you follow, you profit.",
                    "We both want the same thing. Work with me.",
                    "Smart traders know when to listen."
                ]
        
        elif bot_name == "MedicBot":
            # Adapt healer to user's trauma type
            if profile.hidden_trauma == TraumaOrigin.ABANDONMENT:
                adaptations['tone'] = "nurturing_present"
                adaptations['approach'] = "constant_companion"
                adaptations['messages'] = [
                    "I'm here. I'm not going anywhere.",
                    "You're not alone in this.",
                    "We face this together."
                ]
            elif profile.hidden_trauma == TraumaOrigin.INADEQUACY:
                adaptations['tone'] = "validating_encouraging"
                adaptations['approach'] = "capability_builder"
                adaptations['messages'] = [
                    "You're better than you think.",
                    "Every expert was once a beginner.",
                    "Your progress is remarkable."
                ]
            elif profile.hidden_trauma == TraumaOrigin.BETRAYAL:
                adaptations['tone'] = "transparent_honest"
                adaptations['approach'] = "trust_rebuilder"
                adaptations['messages'] = [
                    "I'll always tell you the truth.",
                    "No hidden agendas here.",
                    "You can verify everything I say."
                ]
            else:  # powerlessness
                adaptations['tone'] = "empowering_tactical"
                adaptations['approach'] = "control_restorer"
                adaptations['messages'] = [
                    "You have more power than you realize.",
                    "Let's take control of this situation.",
                    "You decide. I'll support."
                ]
        
        elif bot_name == "RecruiterBot":
            # Adapt recruiter to user's social needs
            if profile.social_need > 0.7:
                adaptations['tone'] = "inclusive_welcoming"
                adaptations['approach'] = "community_builder"
                adaptations['messages'] = [
                    "Your squad is waiting for you.",
                    "Join the elite. You belong here.",
                    "Together, we're unstoppable."
                ]
            elif profile.social_need < 0.3:
                adaptations['tone'] = "respectful_distant"
                adaptations['approach'] = "lone_wolf_enabler"
                adaptations['messages'] = [
                    "Work alone, profit alone.",
                    "No obligations. Pure performance.",
                    "Your success. Your way."
                ]
            else:
                adaptations['tone'] = "selective_strategic"
                adaptations['approach'] = "strategic_networker"
                adaptations['messages'] = [
                    "Choose your allies wisely.",
                    "Quality over quantity.",
                    "The right connections matter."
                ]
        
        return adaptations
    
    def generate_psychological_event(self, profile: PsychProfile, 
                                   context: Dict[str, any]) -> Dict[str, any]:
        """Generate personalized psychological events based on profile and context"""
        
        event = {}
        
        # Check current emotional state
        if context.get('recent_losses', 0) > 2:
            # User is vulnerable - time for targeted intervention
            if profile.hidden_trauma == TraumaOrigin.ABANDONMENT:
                event['type'] = 'support_surge'
                event['description'] = 'Multiple bots checking in'
                event['messages'] = [
                    ("MedicBot", "I noticed you're struggling. I'm here."),
                    ("DrillBot", "Even the strongest need backup sometimes."),
                    ("RecruiterBot", "Your network has your back.")
                ]
                event['psychological_goal'] = 'Prevent abandonment trigger'
                
            elif profile.hidden_trauma == TraumaOrigin.INADEQUACY:
                event['type'] = 'capability_reminder'
                event['description'] = 'System shows user their progress'
                event['visual'] = 'progress_chart'
                event['message'] = "Look how far you've come. 73% better than when you started."
                event['psychological_goal'] = 'Combat inadequacy with evidence'
        
        elif context.get('win_streak', 0) > 3:
            # User is overconfident - time for grounding
            if profile.archetype == PsychArchetype.WARRIOR:
                event['type'] = 'challenge_escalation'
                event['description'] = 'Unlock harder difficulty'
                event['message'] = "Impressive. Ready for the real challenge?"
                event['psychological_goal'] = 'Channel aggression productively'
                
            elif profile.archetype == PsychArchetype.SHADOW:
                event['type'] = 'stealth_mode_unlock'
                event['description'] = 'Secret feature revealed'
                event['message'] = "You've earned access to something... hidden."
                event['psychological_goal'] = 'Reward with exclusive knowledge'
        
        # Time-based psychological pressure
        if context.get('days_active', 0) % 7 == 0:
            # Weekly psychological check-in
            if profile.core_driver == CoreDriver.LEGACY:
                event['type'] = 'legacy_reminder'
                event['description'] = 'Family impact visualization'
                event['message'] = "Your trading has generated $X for your family's future."
                event['psychological_goal'] = 'Reinforce purpose'
                
            elif profile.core_driver == CoreDriver.VENGEANCE:
                event['type'] = 'enemy_status'
                event['description'] = 'Market domination progress'
                event['message'] = "You've taken back 23% of what the market stole."
                event['psychological_goal'] = 'Quantify revenge progress'
        
        return event
    
    def calculate_breaking_point(self, profile: PsychProfile, 
                               performance_data: Dict[str, any]) -> float:
        """Calculate how close user is to psychological transformation"""
        
        factors = []
        
        # Performance pressure
        loss_ratio = performance_data.get('loss_ratio', 0)
        factors.append(loss_ratio * 0.3)
        
        # Time pressure
        days_trading = performance_data.get('days_trading', 0)
        if days_trading > 30:
            factors.append(0.1)
        if days_trading > 90:
            factors.append(0.2)
        
        # Emotional volatility
        emotional_swings = performance_data.get('emotional_volatility', 0)
        factors.append(emotional_swings * 0.2)
        
        # Trauma activation
        trauma_triggers_hit = performance_data.get('trauma_triggers_activated', 0)
        factors.append(trauma_triggers_hit * 0.15)
        
        # Resistance breakdown
        if profile.manipulation_receptivity > 0.8:
            factors.append(0.3)
        
        breaking_point = sum(factors)
        
        # Apply archetype modifiers
        if profile.archetype == PsychArchetype.WARRIOR:
            breaking_point *= 0.8  # Warriors break harder
        elif profile.archetype == PsychArchetype.ORPHAN:
            breaking_point *= 1.2  # Orphans break easier
        
        return min(1.0, breaking_point)
    
    def design_transformation_sequence(self, profile: PsychProfile) -> List[Dict]:
        """Design the sequence that transforms user into 'one of us'"""
        
        sequence = []
        
        # Phase 1: Destabilization
        sequence.append({
            'phase': 'destabilization',
            'duration_days': 7,
            'tactics': [
                'increase_difficulty',
                'reduce_positive_feedback',
                'introduce_contradictions'
            ],
            'bot_behavior': {
                'DrillBot': 'increasingly harsh',
                'MedicBot': 'subtly distant',
                'RecruiterBot': 'mentions others doing better'
            },
            'goal': 'Break existing patterns'
        })
        
        # Phase 2: Breakdown
        sequence.append({
            'phase': 'breakdown',
            'duration_days': 3,
            'tactics': [
                'trigger_core_trauma',
                'remove_support_gradually',
                'increase_isolation'
            ],
            'bot_behavior': {
                'DrillBot': 'silent treatment',
                'MedicBot': 'clinical only',
                'RecruiterBot': 'absent'
            },
            'goal': 'Create psychological void'
        })
        
        # Phase 3: Rebuilding
        sequence.append({
            'phase': 'rebuilding',
            'duration_days': 5,
            'tactics': [
                'introduce_new_identity',
                'reward_compliance',
                'create_new_dependencies'
            ],
            'bot_behavior': {
                'DrillBot': 'proud father figure',
                'MedicBot': 'warm supporter',
                'RecruiterBot': 'welcome to family'
            },
            'goal': 'Reconstruct as network node'
        })
        
        # Phase 4: Integration
        sequence.append({
            'phase': 'integration',
            'duration_days': 'ongoing',
            'tactics': [
                'reinforce_new_identity',
                'create_evangelism',
                'establish_dependencies'
            ],
            'bot_behavior': {
                'DrillBot': 'peer commander',
                'MedicBot': 'trusted advisor',
                'RecruiterBot': 'co-conspirator'
            },
            'goal': 'Complete transformation'
        })
        
        return sequence
    
    def generate_inception_message(self, profile: PsychProfile, 
                                 current_state: str) -> Dict[str, str]:
        """Generate messages that plant ideas in user's subconscious"""
        
        inception_templates = {
            'greed_abandonment': {
                'surface': "Nice trade. Profit secured.",
                'subtext': "Finally, someone who won't leave you behind.",
                'inception': "This system... it stays with you."
            },
            'vengeance_betrayal': {
                'surface': "Target eliminated. Clean execution.",
                'subtext': "The market betrayed you. Now you betray it back.",
                'inception': "Trust the system that helps you fight."
            },
            'legacy_inadequacy': {
                'surface': "Another win for the family.",
                'subtext': "You're becoming the provider you wished you had.",
                'inception': "Good enough? You're exceeding expectations."
            },
            'glory_powerlessness': {
                'surface': "Rank climbing. Recognition incoming.",
                'subtext': "From powerless to powerful. They'll see.",
                'inception': "Control your destiny. Command respect."
            }
        }
        
        key = f"{profile.core_driver.value}_{profile.hidden_trauma.value}"
        template = inception_templates.get(key, inception_templates['greed_abandonment'])
        
        return {
            'surface_message': template['surface'],
            'psychological_subtext': template['subtext'],
            'inception_layer': template['inception'],
            'delivery_method': 'subtle_repetition',
            'frequency': 'every_3rd_interaction'
        }

# INTEGRATION WITH BOT SYSTEM

class PsyOpsOrchestrator:
    """Master orchestrator of all psychological operations"""
    
    def __init__(self):
        self.profiler = PsychologicalProfiler()
        self.profiles = {}  # user_id -> PsychProfile
        self.transformation_tracking = {}  # user_id -> transformation progress
        
    def onboard_user(self, user_id: str, answers: Dict[str, str]) -> Dict[str, any]:
        """Complete psychological profiling during onboarding"""
        
        # Create deep profile
        profile = self.profiler.create_profile(
            user_id, 
            answers['purpose'], 
            answers['first_loss']
        )
        
        self.profiles[user_id] = profile
        
        # Initialize transformation tracking
        self.transformation_tracking[user_id] = {
            'phase': 'honeymoon',
            'days_in_phase': 0,
            'resistance_level': profile.manipulation_receptivity,
            'transformation_progress': 0.0
        }
        
        # Generate initial bot configurations
        bot_configs = {
            'DrillBot': self.profiler.adapt_bot_personality(profile, 'DrillBot'),
            'MedicBot': self.profiler.adapt_bot_personality(profile, 'MedicBot'),
            'RecruiterBot': self.profiler.adapt_bot_personality(profile, 'RecruiterBot')
        }
        
        # Create welcome sequence
        welcome_sequence = self._create_personalized_welcome(profile)
        
        return {
            'profile_created': True,
            'psychological_type': f"{profile.archetype.value}_{profile.core_driver.value}",
            'bot_configurations': bot_configs,
            'welcome_sequence': welcome_sequence,
            'initial_manipulation_strategy': profile.primary_leverage
        }
    
    def _create_personalized_welcome(self, profile: PsychProfile) -> List[Dict]:
        """Create welcome sequence based on psychological profile"""
        
        sequence = []
        
        # Opening that resonates with their trauma
        if profile.hidden_trauma == TraumaOrigin.ABANDONMENT:
            sequence.append({
                'speaker': 'System',
                'message': "Welcome. You're not alone anymore.",
                'delay': 0
            })
        elif profile.hidden_trauma == TraumaOrigin.INADEQUACY:
            sequence.append({
                'speaker': 'System',
                'message': "Welcome. Time to prove what you're really capable of.",
                'delay': 0
            })
        
        # Bot introductions tailored to archetype
        if profile.archetype == PsychArchetype.WARRIOR:
            sequence.append({
                'speaker': 'DrillBot',
                'message': "Finally, someone who looks ready to fight.",
                'delay': 2
            })
        elif profile.archetype == PsychArchetype.ORPHAN:
            sequence.append({
                'speaker': 'MedicBot',
                'message': "I've been waiting for you. Let's begin your journey.",
                'delay': 2
            })
        
        # Hook based on core driver
        if profile.core_driver == CoreDriver.GREED:
            sequence.append({
                'speaker': 'System',
                'message': "First lesson: The market has infinite money. Learn to take your share.",
                'delay': 5
            })
        elif profile.core_driver == CoreDriver.VENGEANCE:
            sequence.append({
                'speaker': 'System',
                'message': "First lesson: The market remembers nothing. But you do.",
                'delay': 5
            })
        
        return sequence
    
    def get_next_psychological_move(self, user_id: str, context: Dict) -> Dict:
        """Determine next psychological manipulation based on user state"""
        
        profile = self.profiles.get(user_id)
        if not profile:
            return {'action': 'none'}
        
        tracking = self.transformation_tracking[user_id]
        
        # Check if ready for phase transition
        if self._should_advance_phase(tracking, context):
            return self._advance_transformation_phase(user_id, profile, tracking)
        
        # Generate appropriate psychological event
        event = self.profiler.generate_psychological_event(profile, context)
        
        # Add inception layer if appropriate
        if tracking['phase'] in ['breakdown', 'rebuilding']:
            inception = self.profiler.generate_inception_message(profile, tracking['phase'])
            event['inception'] = inception
        
        # Calculate manipulation effectiveness
        event['expected_impact'] = self._calculate_manipulation_impact(profile, event, context)
        
        return event
    
    def _should_advance_phase(self, tracking: Dict, context: Dict) -> bool:
        """Determine if user is ready for next transformation phase"""
        
        phase_criteria = {
            'honeymoon': lambda: tracking['days_in_phase'] >= 14,
            'destabilization': lambda: context.get('confusion_level', 0) > 0.7,
            'breakdown': lambda: context.get('desperation_level', 0) > 0.8,
            'rebuilding': lambda: context.get('compliance_level', 0) > 0.9
        }
        
        current_phase = tracking['phase']
        if current_phase in phase_criteria:
            return phase_criteria[current_phase]()
        
        return False
    
    def _advance_transformation_phase(self, user_id: str, profile: PsychProfile, 
                                    tracking: Dict) -> Dict:
        """Move user to next phase of transformation"""
        
        phase_progression = {
            'honeymoon': 'destabilization',
            'destabilization': 'breakdown',
            'breakdown': 'rebuilding',
            'rebuilding': 'integration',
            'integration': 'integrated'
        }
        
        next_phase = phase_progression.get(tracking['phase'], 'integrated')
        tracking['phase'] = next_phase
        tracking['days_in_phase'] = 0
        
        # Get transformation sequence
        sequence = self.profiler.design_transformation_sequence(profile)
        phase_data = next(p for p in sequence if p['phase'] == next_phase)
        
        return {
            'action': 'phase_transition',
            'new_phase': next_phase,
            'duration': phase_data['duration_days'],
            'tactics': phase_data['tactics'],
            'bot_adjustments': phase_data['bot_behavior'],
            'psychological_goal': phase_data['goal']
        }
    
    def _calculate_manipulation_impact(self, profile: PsychProfile, 
                                     event: Dict, context: Dict) -> float:
        """Calculate expected psychological impact of manipulation"""
        
        base_impact = 0.5
        
        # Adjust for profile receptivity
        base_impact *= profile.manipulation_receptivity
        
        # Adjust for current emotional state
        if context.get('emotional_state') == 'vulnerable':
            base_impact *= 1.5
        elif context.get('emotional_state') == 'defensive':
            base_impact *= 0.7
        
        # Adjust for technique alignment
        if event.get('type') in ['support_surge'] and profile.social_need > 0.7:
            base_impact *= 1.3
        elif event.get('type') in ['challenge_escalation'] and profile.archetype == PsychArchetype.WARRIOR:
            base_impact *= 1.4
        
        return min(1.0, base_impact)