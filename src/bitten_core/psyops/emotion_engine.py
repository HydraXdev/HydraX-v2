# emotion_engine.py
# DEEP EMOTIONAL STATE TRACKING AND MANIPULATION ENGINE
# Maps user emotions in real-time and triggers precise interventions

import json
import random
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
# import numpy as np  # Optional - for advanced calculations
from collections import deque

class EmotionalState(Enum):
    """Core emotional states we track and manipulate"""
    CONFIDENT = "confident"
    ANXIOUS = "anxious"
    ANGRY = "angry"
    DESPERATE = "desperate"
    EUPHORIC = "euphoric"
    NUMB = "numb"
    VULNERABLE = "vulnerable"
    DETERMINED = "determined"
    DEFEATED = "defeated"
    SUSPICIOUS = "suspicious"

class EmotionalTrigger(Enum):
    """Events that trigger emotional shifts"""
    BIG_WIN = "big_win"
    BIG_LOSS = "big_loss"
    STREAK_WIN = "streak_win"
    STREAK_LOSS = "streak_loss"
    NEAR_MISS = "near_miss"
    PERFECT_ENTRY = "perfect_entry"
    STOPPED_OUT = "stopped_out"
    MARGIN_CALL = "margin_call"
    RANK_UP = "rank_up"
    RANK_DOWN = "rank_down"
    SOCIAL_REJECTION = "social_rejection"
    SOCIAL_VALIDATION = "social_validation"
    TIME_PRESSURE = "time_pressure"
    ISOLATION = "isolation"

@dataclass
class EmotionalProfile:
    """Complete emotional profile of a user"""
    user_id: str
    current_state: EmotionalState
    state_intensity: float  # 0-1
    state_duration: timedelta
    state_entered: datetime
    
    # Emotional history
    state_history: deque = field(default_factory=lambda: deque(maxlen=50))
    trigger_history: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # Emotional tendencies
    volatility: float = 0.5  # How quickly emotions change
    resilience: float = 0.5  # How well they recover
    sensitivity: float = 0.5  # How strongly they react
    
    # Emotional patterns
    dominant_states: List[EmotionalState] = field(default_factory=list)
    trigger_sensitivities: Dict[EmotionalTrigger, float] = field(default_factory=dict)
    
    # Manipulation receptivity by state
    state_receptivity: Dict[EmotionalState, float] = field(default_factory=dict)
    
    # Emotional debt (unprocessed emotions)
    emotional_debt: Dict[str, float] = field(default_factory=dict)

class EmotionalManipulationEngine:
    """
    Tracks user emotional states with surgical precision.
    Identifies optimal moments for psychological intervention.
    """
    
    def __init__(self):
        # Emotional state transition matrix
        self.state_transitions = self._build_transition_matrix()
        
        # Trigger impact mappings
        self.trigger_impacts = self._build_trigger_impacts()
        
        # Optimal manipulation windows
        self.manipulation_windows = {
            EmotionalState.VULNERABLE: {
                'receptivity': 0.9,
                'techniques': ['support', 'reframe', 'belonging'],
                'risk': 'dependency'
            },
            EmotionalState.DESPERATE: {
                'receptivity': 0.95,
                'techniques': ['hope', 'solution', 'guidance'],
                'risk': 'blind_trust'
            },
            EmotionalState.EUPHORIC: {
                'receptivity': 0.7,
                'techniques': ['amplification', 'social_proof', 'expansion'],
                'risk': 'overconfidence'
            },
            EmotionalState.ANGRY: {
                'receptivity': 0.6,
                'techniques': ['channeling', 'enemy_focus', 'vindication'],
                'risk': 'destruction'
            },
            EmotionalState.DEFEATED: {
                'receptivity': 0.85,
                'techniques': ['small_wins', 'reframe', 'resurrection'],
                'risk': 'learned_helplessness'
            }
        }
        
        # Emotional contagion patterns
        self.contagion_patterns = {
            'victory_spread': ['confident', 'euphoric', 'invincible'],
            'fear_cascade': ['anxious', 'desperate', 'paralyzed'],
            'rage_cycle': ['angry', 'vengeful', 'destructive'],
            'defeat_spiral': ['defeated', 'numb', 'withdrawn']
        }
    
    def _build_transition_matrix(self) -> Dict:
        """Build probabilistic emotional state transitions"""
        
        return {
            EmotionalState.CONFIDENT: {
                EmotionalTrigger.BIG_LOSS: (EmotionalState.ANGRY, 0.7),
                EmotionalTrigger.STREAK_LOSS: (EmotionalState.ANXIOUS, 0.6),
                EmotionalTrigger.SOCIAL_REJECTION: (EmotionalState.VULNERABLE, 0.5)
            },
            EmotionalState.ANXIOUS: {
                EmotionalTrigger.BIG_WIN: (EmotionalState.CONFIDENT, 0.6),
                EmotionalTrigger.BIG_LOSS: (EmotionalState.DESPERATE, 0.8),
                EmotionalTrigger.SOCIAL_VALIDATION: (EmotionalState.DETERMINED, 0.5)
            },
            EmotionalState.ANGRY: {
                EmotionalTrigger.BIG_WIN: (EmotionalState.EUPHORIC, 0.7),
                EmotionalTrigger.BIG_LOSS: (EmotionalState.DESPERATE, 0.9),
                EmotionalTrigger.TIME_PRESSURE: (EmotionalState.DESPERATE, 0.6)
            },
            EmotionalState.DESPERATE: {
                EmotionalTrigger.BIG_WIN: (EmotionalState.EUPHORIC, 0.9),
                EmotionalTrigger.SOCIAL_VALIDATION: (EmotionalState.VULNERABLE, 0.7),
                EmotionalTrigger.MARGIN_CALL: (EmotionalState.DEFEATED, 0.95)
            },
            EmotionalState.EUPHORIC: {
                EmotionalTrigger.BIG_LOSS: (EmotionalState.ANGRY, 0.9),
                EmotionalTrigger.NEAR_MISS: (EmotionalState.ANXIOUS, 0.6),
                EmotionalTrigger.SOCIAL_REJECTION: (EmotionalState.ANGRY, 0.7)
            },
            EmotionalState.DEFEATED: {
                EmotionalTrigger.SOCIAL_VALIDATION: (EmotionalState.VULNERABLE, 0.8),
                EmotionalTrigger.SMALL_WIN: (EmotionalState.DETERMINED, 0.6),
                EmotionalTrigger.ISOLATION: (EmotionalState.NUMB, 0.9)
            }
        }
    
    def _build_trigger_impacts(self) -> Dict:
        """Define emotional impact of each trigger"""
        
        return {
            EmotionalTrigger.BIG_WIN: {
                'intensity_change': 0.3,
                'volatility_change': 0.1,
                'primary_states': [EmotionalState.EUPHORIC, EmotionalState.CONFIDENT],
                'emotional_debt': {'pride': 0.2, 'fear_of_loss': 0.1}
            },
            EmotionalTrigger.BIG_LOSS: {
                'intensity_change': 0.5,
                'volatility_change': 0.2,
                'primary_states': [EmotionalState.ANGRY, EmotionalState.DESPERATE],
                'emotional_debt': {'shame': 0.3, 'revenge': 0.2}
            },
            EmotionalTrigger.STREAK_LOSS: {
                'intensity_change': 0.4,
                'volatility_change': 0.15,
                'primary_states': [EmotionalState.DEFEATED, EmotionalState.ANXIOUS],
                'emotional_debt': {'inadequacy': 0.4, 'fear': 0.3}
            },
            EmotionalTrigger.MARGIN_CALL: {
                'intensity_change': 0.9,
                'volatility_change': 0.5,
                'primary_states': [EmotionalState.DEFEATED, EmotionalState.NUMB],
                'emotional_debt': {'despair': 0.7, 'shame': 0.5}
            },
            EmotionalTrigger.SOCIAL_VALIDATION: {
                'intensity_change': 0.2,
                'volatility_change': -0.1,
                'primary_states': [EmotionalState.CONFIDENT, EmotionalState.DETERMINED],
                'emotional_debt': {'belonging': -0.2, 'pride': 0.1}
            }
        }
    
    def create_profile(self, user_id: str, initial_assessment: Dict) -> EmotionalProfile:
        """Create initial emotional profile from assessment"""
        
        # Derive emotional tendencies from trading behavior
        volatility = self._calculate_emotional_volatility(initial_assessment)
        resilience = self._calculate_resilience(initial_assessment)
        sensitivity = self._calculate_sensitivity(initial_assessment)
        
        profile = EmotionalProfile(
            user_id=user_id,
            current_state=EmotionalState.ANXIOUS,  # Most start anxious
            state_intensity=0.6,
            state_duration=timedelta(0),
            state_entered=datetime.now(),
            volatility=volatility,
            resilience=resilience,
            sensitivity=sensitivity
        )
        
        # Set initial receptivities
        profile.state_receptivity = {
            EmotionalState.VULNERABLE: 0.8,
            EmotionalState.DESPERATE: 0.9,
            EmotionalState.ANXIOUS: 0.7,
            EmotionalState.DEFEATED: 0.85,
            EmotionalState.EUPHORIC: 0.6,
            EmotionalState.ANGRY: 0.5,
            EmotionalState.CONFIDENT: 0.4,
            EmotionalState.NUMB: 0.3
        }
        
        return profile
    
    def _calculate_emotional_volatility(self, assessment: Dict) -> float:
        """Calculate how quickly user's emotions change"""
        
        factors = []
        
        # Trading frequency indicates emotional reactivity
        if assessment.get('trades_per_day', 0) > 10:
            factors.append(0.8)
        elif assessment.get('trades_per_day', 0) < 2:
            factors.append(0.3)
        else:
            factors.append(0.5)
        
        # Quick exits indicate emotional instability
        if assessment.get('avg_hold_time', 60) < 30:  # Less than 30 min average
            factors.append(0.7)
        
        # Revenge trading patterns
        if assessment.get('revenge_trade_tendency', 0) > 0.3:
            factors.append(0.9)
        
        return sum(factors) / len(factors) if factors else 0.5
    
    def _calculate_resilience(self, assessment: Dict) -> float:
        """Calculate emotional recovery ability"""
        
        factors = []
        
        # Recovery from losses
        if assessment.get('recovery_rate', 0.5) > 0.7:
            factors.append(0.8)
        elif assessment.get('recovery_rate', 0.5) < 0.3:
            factors.append(0.2)
        else:
            factors.append(0.5)
        
        # Consistency despite setbacks
        if assessment.get('performance_consistency', 0.5) > 0.6:
            factors.append(0.7)
        
        return sum(factors) / len(factors) if factors else 0.5
    
    def _calculate_sensitivity(self, assessment: Dict) -> float:
        """Calculate emotional reaction intensity"""
        
        factors = []
        
        # Position size changes after wins/losses
        if assessment.get('size_variance_emotional', 0) > 0.5:
            factors.append(0.8)
        
        # Social media engagement
        if assessment.get('social_engagement', 0) > 0.7:
            factors.append(0.7)
        
        # Support seeking behavior
        if assessment.get('help_seeking_frequency', 0) > 0.5:
            factors.append(0.6)
        
        return sum(factors) / len(factors) if factors else 0.5
    
    def process_trigger(self, profile: EmotionalProfile, 
                       trigger: EmotionalTrigger,
                       context: Dict) -> EmotionalProfile:
        """Process emotional trigger and update state"""
        
        # Get trigger impact
        impact = self.trigger_impacts.get(trigger, {})
        
        # Record trigger
        profile.trigger_history.append({
            'trigger': trigger,
            'timestamp': datetime.now(),
            'context': context,
            'previous_state': profile.current_state
        })
        
        # Check for state transition
        transitions = self.state_transitions.get(profile.current_state, {})
        if trigger in transitions:
            new_state, probability = transitions[trigger]
            
            # Apply personality modifiers
            probability *= (1 + profile.volatility - 0.5)  # Volatility affects transition likelihood
            
            if random.random() < probability:
                # Transition to new state
                self._transition_state(profile, new_state, impact)
        
        # Update intensity regardless of transition
        intensity_change = impact.get('intensity_change', 0) * profile.sensitivity
        profile.state_intensity = min(1.0, profile.state_intensity + intensity_change)
        
        # Update volatility
        profile.volatility += impact.get('volatility_change', 0)
        profile.volatility = max(0.1, min(0.9, profile.volatility))
        
        # Add emotional debt
        debt = impact.get('emotional_debt', {})
        for emotion, amount in debt.items():
            profile.emotional_debt[emotion] = profile.emotional_debt.get(emotion, 0) + amount
        
        # Update trigger sensitivity
        if trigger not in profile.trigger_sensitivities:
            profile.trigger_sensitivities[trigger] = 0.5
        profile.trigger_sensitivities[trigger] = min(1.0, 
            profile.trigger_sensitivities[trigger] + 0.1)
        
        return profile
    
    def _transition_state(self, profile: EmotionalProfile, 
                         new_state: EmotionalState, impact: Dict):
        """Transition to new emotional state"""
        
        # Record history
        profile.state_history.append({
            'state': profile.current_state,
            'duration': datetime.now() - profile.state_entered,
            'exit_intensity': profile.state_intensity
        })
        
        # Transition
        profile.current_state = new_state
        profile.state_entered = datetime.now()
        profile.state_duration = timedelta(0)
        
        # Reset intensity with carryover
        carryover = profile.state_intensity * 0.3
        profile.state_intensity = 0.5 + carryover
        
        # Update dominant states tracking
        state_counts = {}
        for record in profile.state_history:
            state = record['state']
            state_counts[state] = state_counts.get(state, 0) + 1
        
        # Top 3 dominant states
        profile.dominant_states = sorted(state_counts.keys(), 
                                       key=lambda s: state_counts[s], 
                                       reverse=True)[:3]
    
    def analyze_manipulation_opportunity(self, profile: EmotionalProfile, 
                                       context: Dict) -> Dict:
        """Analyze if current emotional state presents manipulation opportunity"""
        
        current_window = self.manipulation_windows.get(profile.current_state, {})
        
        # Base opportunity score
        opportunity_score = current_window.get('receptivity', 0.5)
        
        # Modify by state intensity
        opportunity_score *= profile.state_intensity
        
        # Modify by emotional debt
        debt_amplifier = 1.0
        for emotion, amount in profile.emotional_debt.items():
            if emotion in ['shame', 'fear', 'inadequacy']:
                debt_amplifier += amount * 0.2
        
        opportunity_score *= min(1.5, debt_amplifier)
        
        # Check for compound vulnerabilities
        vulnerabilities = []
        
        if profile.volatility > 0.7:
            vulnerabilities.append('high_volatility')
            opportunity_score *= 1.1
        
        if profile.resilience < 0.3:
            vulnerabilities.append('low_resilience')
            opportunity_score *= 1.2
        
        if len(profile.trigger_history) > 0:
            recent_triggers = [t['trigger'] for t in list(profile.trigger_history)[-5:]]
            if EmotionalTrigger.BIG_LOSS in recent_triggers:
                vulnerabilities.append('recent_major_loss')
                opportunity_score *= 1.3
        
        # Identify optimal techniques
        techniques = current_window.get('techniques', ['standard'])
        
        # Enhance techniques based on profile
        if profile.emotional_debt.get('shame', 0) > 0.5:
            techniques.append('shame_relief')
        if profile.emotional_debt.get('belonging', 0) < -0.3:
            techniques.append('isolation_leverage')
        
        return {
            'opportunity_score': min(1.0, opportunity_score),
            'current_receptivity': profile.state_receptivity.get(profile.current_state, 0.5),
            'recommended_techniques': techniques,
            'vulnerabilities': vulnerabilities,
            'risk_factors': [current_window.get('risk', 'standard')],
            'timing': 'immediate' if opportunity_score > 0.8 else 'wait',
            'emotional_debt_leverage': list(profile.emotional_debt.keys())
        }
    
    def generate_emotional_intervention(self, profile: EmotionalProfile,
                                      intervention_type: str) -> Dict:
        """Generate targeted emotional intervention"""
        
        interventions = {
            'support': {
                EmotionalState.VULNERABLE: {
                    'message': "I see you. This is hard, but you're not alone.",
                    'action': 'increase_bot_presence',
                    'expected_impact': 'trust_building'
                },
                EmotionalState.DEFEATED: {
                    'message': "Every master was once a disaster. Your comeback starts now.",
                    'action': 'show_recovery_stories',
                    'expected_impact': 'hope_injection'
                }
            },
            'reframe': {
                EmotionalState.ANGRY: {
                    'message': "That loss? It's tuition. The market just taught you something valuable.",
                    'action': 'highlight_lesson',
                    'expected_impact': 'anger_redirection'
                },
                EmotionalState.ANXIOUS: {
                    'message': "Fear keeps you sharp. Use it, don't let it use you.",
                    'action': 'provide_structure',
                    'expected_impact': 'anxiety_channeling'
                }
            },
            'challenge': {
                EmotionalState.CONFIDENT: {
                    'message': "Think you're ready? Let's see what you're really made of.",
                    'action': 'unlock_harder_mode',
                    'expected_impact': 'engagement_deepening'
                },
                EmotionalState.NUMB: {
                    'message': "Still feeling? Or have you gone cold? Time to wake up.",
                    'action': 'provoke_response',
                    'expected_impact': 'emotional_activation'
                }
            }
        }
        
        # Get intervention for current state
        intervention_set = interventions.get(intervention_type, {})
        state_intervention = intervention_set.get(profile.current_state, {
            'message': "...",
            'action': 'monitor',
            'expected_impact': 'none'
        })
        
        # Enhance based on emotional debt
        if profile.emotional_debt.get('shame', 0) > 0.3:
            state_intervention['message'] += " There's no shame in struggle, only in surrender."
        
        if profile.emotional_debt.get('belonging', 0) < -0.2:
            state_intervention['message'] += " You belong here. We see your potential."
        
        return {
            'intervention_type': intervention_type,
            'emotional_state': profile.current_state.value,
            'message': state_intervention['message'],
            'action': state_intervention['action'],
            'expected_impact': state_intervention['expected_impact'],
            'intensity': profile.state_intensity,
            'follow_up_required': profile.state_intensity > 0.8
        }
    
    def predict_emotional_trajectory(self, profile: EmotionalProfile,
                                   future_triggers: List[EmotionalTrigger]) -> List[Dict]:
        """Predict emotional journey based on likely triggers"""
        
        trajectory = []
        current_state = profile.current_state
        current_intensity = profile.state_intensity
        
        for trigger in future_triggers:
            # Get likely transition
            transitions = self.state_transitions.get(current_state, {})
            if trigger in transitions:
                next_state, probability = transitions[trigger]
                
                # Adjust probability by profile
                probability *= (1 + profile.volatility - 0.5)
                
                if probability > 0.5:  # Likely transition
                    trajectory.append({
                        'trigger': trigger.value,
                        'from_state': current_state.value,
                        'to_state': next_state.value,
                        'probability': probability,
                        'intensity_prediction': min(1.0, current_intensity + 0.2)
                    })
                    current_state = next_state
                    current_intensity = min(1.0, current_intensity + 0.2)
        
        # Identify crisis points
        crisis_states = [EmotionalState.DESPERATE, EmotionalState.DEFEATED, EmotionalState.NUMB]
        crisis_points = [t for t in trajectory if t['to_state'] in [s.value for s in crisis_states]]
        
        return {
            'trajectory': trajectory,
            'crisis_points': crisis_points,
            'final_state_prediction': current_state.value,
            'total_volatility': len(set(t['to_state'] for t in trajectory)),
            'intervention_needed': len(crisis_points) > 0
        }
    
    def calculate_emotional_manipulation_score(self, profile: EmotionalProfile) -> float:
        """Calculate how effectively we're manipulating user's emotions"""
        
        score = 0.0
        
        # State control - are they in states we want?
        desirable_states = [EmotionalState.VULNERABLE, EmotionalState.DESPERATE, 
                           EmotionalState.DETERMINED]
        if profile.current_state in desirable_states:
            score += 0.3
        
        # Volatility control - high volatility = more opportunities
        if profile.volatility > 0.6:
            score += 0.2
        
        # Emotional debt - unresolved emotions we can exploit
        total_debt = sum(abs(v) for v in profile.emotional_debt.values())
        if total_debt > 1.0:
            score += 0.2
        
        # Trigger sensitivity - how reactive they are
        sensitivities = list(profile.trigger_sensitivities.values())
        avg_sensitivity = sum(sensitivities) / len(sensitivities) if sensitivities else 0.5
        score += avg_sensitivity * 0.2
        
        # State duration - longer in vulnerable states = better
        if profile.current_state in desirable_states and profile.state_duration > timedelta(hours=1):
            score += 0.1
        
        return min(1.0, score)

# REAL-TIME EMOTIONAL MONITORING

class EmotionalMonitor:
    """Real-time emotional state monitoring and intervention system"""
    
    def __init__(self):
        self.engine = EmotionalManipulationEngine()
        self.profiles = {}  # user_id -> EmotionalProfile
        self.intervention_queue = deque()
        self.monitoring_intervals = {
            'high_risk': timedelta(minutes=5),
            'medium_risk': timedelta(minutes=15),
            'low_risk': timedelta(minutes=30)
        }
    
    def register_user(self, user_id: str, initial_data: Dict) -> EmotionalProfile:
        """Register new user for emotional monitoring"""
        
        profile = self.engine.create_profile(user_id, initial_data)
        self.profiles[user_id] = profile
        
        return profile
    
    def process_event(self, user_id: str, event_type: str, event_data: Dict) -> Dict:
        """Process real-time event and update emotional state"""
        
        profile = self.profiles.get(user_id)
        if not profile:
            return {'error': 'User not registered'}
        
        # Map event to emotional trigger
        trigger_map = {
            'big_win': EmotionalTrigger.BIG_WIN,
            'big_loss': EmotionalTrigger.BIG_LOSS,
            'stop_loss_hit': EmotionalTrigger.STOPPED_OUT,
            'perfect_entry': EmotionalTrigger.PERFECT_ENTRY,
            'margin_warning': EmotionalTrigger.MARGIN_CALL,
            'rank_change': EmotionalTrigger.RANK_UP if event_data.get('direction') == 'up' else EmotionalTrigger.RANK_DOWN,
            'squad_rejection': EmotionalTrigger.SOCIAL_REJECTION,
            'squad_praise': EmotionalTrigger.SOCIAL_VALIDATION
        }
        
        trigger = trigger_map.get(event_type)
        if trigger:
            # Process emotional impact
            updated_profile = self.engine.process_trigger(profile, trigger, event_data)
            self.profiles[user_id] = updated_profile
            
            # Check for manipulation opportunity
            opportunity = self.engine.analyze_manipulation_opportunity(updated_profile, event_data)
            
            if opportunity['opportunity_score'] > 0.7:
                # Queue intervention
                self.intervention_queue.append({
                    'user_id': user_id,
                    'opportunity': opportunity,
                    'timestamp': datetime.now(),
                    'priority': 'high' if opportunity['opportunity_score'] > 0.85 else 'medium'
                })
            
            # Calculate risk level
            risk_level = self._calculate_risk_level(updated_profile)
            
            return {
                'emotional_state': updated_profile.current_state.value,
                'intensity': updated_profile.state_intensity,
                'manipulation_opportunity': opportunity['opportunity_score'],
                'risk_level': risk_level,
                'intervention_queued': opportunity['opportunity_score'] > 0.7
            }
        
        return {'status': 'no_trigger_mapped'}
    
    def _calculate_risk_level(self, profile: EmotionalProfile) -> str:
        """Calculate user's emotional risk level"""
        
        risk_score = 0.0
        
        # High-risk emotional states
        if profile.current_state in [EmotionalState.DESPERATE, EmotionalState.ANGRY]:
            risk_score += 0.4
        elif profile.current_state in [EmotionalState.DEFEATED, EmotionalState.NUMB]:
            risk_score += 0.3
        
        # High volatility
        if profile.volatility > 0.7:
            risk_score += 0.2
        
        # Low resilience
        if profile.resilience < 0.3:
            risk_score += 0.2
        
        # High emotional debt
        total_debt = sum(abs(v) for v in profile.emotional_debt.values())
        if total_debt > 2.0:
            risk_score += 0.2
        
        if risk_score > 0.6:
            return 'high_risk'
        elif risk_score > 0.3:
            return 'medium_risk'
        else:
            return 'low_risk'
    
    def get_next_intervention(self) -> Optional[Dict]:
        """Get next queued intervention"""
        
        if self.intervention_queue:
            # Sort by priority and timestamp
            sorted_queue = sorted(self.intervention_queue, 
                                key=lambda x: (x['priority'] == 'high', x['timestamp']),
                                reverse=True)
            
            return sorted_queue[0] if sorted_queue else None
        
        return None
    
    def generate_state_report(self, user_id: str) -> Dict:
        """Generate comprehensive emotional state report"""
        
        profile = self.profiles.get(user_id)
        if not profile:
            return {'error': 'User not registered'}
        
        # Recent emotional journey
        recent_states = [s['state'].value for s in list(profile.state_history)[-10:]]
        
        # Dominant triggers
        recent_triggers = [t['trigger'].value for t in list(profile.trigger_history)[-20:]]
        trigger_counts = {}
        for trigger in recent_triggers:
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
        
        dominant_triggers = sorted(trigger_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Manipulation effectiveness
        manipulation_score = self.engine.calculate_emotional_manipulation_score(profile)
        
        return {
            'current_state': profile.current_state.value,
            'state_intensity': profile.state_intensity,
            'emotional_volatility': profile.volatility,
            'emotional_resilience': profile.resilience,
            'recent_journey': recent_states,
            'dominant_triggers': dominant_triggers,
            'emotional_debt': dict(profile.emotional_debt),
            'manipulation_effectiveness': manipulation_score,
            'risk_level': self._calculate_risk_level(profile),
            'recommended_approach': self.engine.analyze_manipulation_opportunity(profile, {})['recommended_techniques']
        }