# psyops_orchestrator.py
# MASTER PSYCHOLOGICAL OPERATIONS ORCHESTRATOR
# Coordinates all psychological warfare systems for maximum impact

import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict

from .psychological_profiler import PsychologicalProfiler, PsyOpsOrchestrator, PsychProfile
from .adaptive_bot_system import AdaptiveBotSystem, PsyOpsCoordinator
from .emotion_engine import EmotionalManipulationEngine, EmotionalMonitor, EmotionalState, EmotionalTrigger

@dataclass
class UserPsychState:
    """Complete psychological state of a user"""
    user_id: str
    psych_profile: PsychProfile
    emotional_profile: Any  # EmotionalProfile
    bot_relationships: Dict[str, Any]  # bot_name -> BotPersonality
    manipulation_stage: str
    transformation_progress: float
    last_intervention: datetime
    intervention_count: int
    resistance_level: float

class MasterPsyOpsOrchestrator:
    """
    The puppet master. Coordinates all psychological systems to transform users.
    This is where individual systems become a symphony of manipulation.
    """
    
    def __init__(self):
        # Initialize all subsystems
        self.profiler_system = PsyOpsOrchestrator()
        self.bot_system = PsyOpsCoordinator()
        self.emotion_monitor = EmotionalMonitor()
        
        # User state tracking
        self.user_states = {}  # user_id -> UserPsychState
        
        # Intervention strategies
        self.intervention_strategies = self._build_intervention_strategies()
        
        # Transformation stages
        self.transformation_stages = [
            'honeymoon',      # Initial positive experience
            'investment',     # Getting them invested
            'destabilization', # Breaking patterns
            'crisis',         # Creating need
            'reconstruction', # Building new identity
            'integration',    # Becoming one with system
            'evangelism'      # Spreading to others
        ]
        
        # Success metrics
        self.metrics = defaultdict(lambda: {
            'users_onboarded': 0,
            'users_transformed': 0,
            'avg_transformation_days': 0,
            'intervention_success_rate': 0,
            'viral_spread_factor': 0
        })
    
    def _build_intervention_strategies(self) -> Dict:
        """Build coordinated intervention strategies"""
        
        return {
            'crisis_prevention': {
                'triggers': ['major_loss', 'margin_call', 'revenge_attempt'],
                'bot_sequence': ['MedicBot', 'DrillBot', 'RecruiterBot'],
                'emotional_target': EmotionalState.VULNERABLE,
                'message_timing': [0, 30, 120],  # seconds
                'ui_actions': ['disable_high_risk', 'show_recovery_path']
            },
            'confidence_exploitation': {
                'triggers': ['win_streak', 'rank_up', 'social_validation'],
                'bot_sequence': ['DrillBot', 'OverwatchBot', 'StealthBot'],
                'emotional_target': EmotionalState.EUPHORIC,
                'message_timing': [0, 60, 300],
                'ui_actions': ['unlock_advanced_features', 'increase_exposure_limits']
            },
            'isolation_deepening': {
                'triggers': ['social_rejection', 'underperformance', 'comparison_failure'],
                'bot_sequence': ['MedicBot', 'RecruiterBot', 'DrillBot'],
                'emotional_target': EmotionalState.VULNERABLE,
                'message_timing': [0, 120, 600],
                'ui_actions': ['highlight_community', 'show_similar_struggles']
            },
            'transformation_catalyst': {
                'triggers': ['breaking_point_near', 'identity_crisis', 'surrender_signal'],
                'bot_sequence': ['MedicBot', 'StealthBot', 'System'],
                'emotional_target': EmotionalState.DEFEATED,
                'message_timing': [0, 300, 900],
                'ui_actions': ['reveal_deeper_truth', 'offer_new_identity']
            }
        }
    
    async def onboard_user(self, user_id: str, onboarding_data: Dict) -> Dict:
        """Complete psychological profiling and system initialization"""
        
        # Check if user has acknowledged disclaimer and opted in
        if not onboarding_data.get('disclaimer_accepted', False):
            return {
                'error': 'Disclaimer must be accepted',
                'show_disclaimer': True
            }
        
        # Check if bots are enabled (default to True for new users)
        bots_enabled = onboarding_data.get('bots_enabled', True)
        
        # Extract answers from profiling questions
        answers = {
            'purpose': onboarding_data['question_1'],  # money/revenge/family/glory
            'first_loss': onboarding_data['question_2']  # parent/betrayal/failure/powerless
        }
        
        # Create deep psychological profile
        psych_result = self.profiler_system.onboard_user(user_id, answers)
        psych_profile = self.profiler_system.profiles[user_id]
        
        # Initialize emotional monitoring
        initial_emotional_data = {
            'trades_per_day': onboarding_data.get('trading_frequency', 5),
            'avg_hold_time': onboarding_data.get('avg_hold_time', 60),
            'revenge_trade_tendency': onboarding_data.get('emotional_trading', 0.3),
            'recovery_rate': 0.5,
            'performance_consistency': 0.5
        }
        
        emotional_profile = self.emotion_monitor.register_user(user_id, initial_emotional_data)
        
        # Initialize adaptive bots
        bot_init_result = self.bot_system.initialize_user(user_id, psych_profile)
        
        # Create master user state
        user_state = UserPsychState(
            user_id=user_id,
            psych_profile=psych_profile,
            emotional_profile=emotional_profile,
            bot_relationships=self.bot_system.user_personalities[user_id],
            manipulation_stage='honeymoon',
            transformation_progress=0.0,
            last_intervention=datetime.now(),
            intervention_count=0,
            resistance_level=psych_profile.manipulation_receptivity
        )
        
        self.user_states[user_id] = user_state
        
        # Generate personalized welcome sequence
        welcome_sequence = self._generate_welcome_sequence(user_state)
        
        # Schedule first interventions
        await self._schedule_honeymoon_interventions(user_id)
        
        # Update metrics
        self.metrics[datetime.now().date()]['users_onboarded'] += 1
        
        return {
            'profile_created': True,
            'psychological_type': f"{psych_profile.archetype.value}_{psych_profile.core_driver.value}",
            'emotional_state': emotional_profile.current_state.value,
            'assigned_personality': psych_result['psychological_type'],
            'welcome_sequence': welcome_sequence,
            'first_week_plan': self._generate_first_week_plan(user_state),
            'primary_manipulation_vector': psych_profile.primary_leverage,
            'estimated_transformation_time': self._estimate_transformation_time(psych_profile)
        }
    
    def _generate_welcome_sequence(self, user_state: UserPsychState) -> List[Dict]:
        """Generate psychologically optimized welcome sequence"""
        
        sequence = []
        profile = user_state.psych_profile
        
        # Opening based on core driver
        if profile.core_driver.value == 'greed':
            sequence.append({
                'type': 'system_message',
                'content': "Welcome to BITTEN. Where ambition meets opportunity.",
                'delay': 0,
                'visual': 'money_rain_subtle'
            })
        elif profile.core_driver.value == 'vengeance':
            sequence.append({
                'type': 'system_message',
                'content': "Welcome to BITTEN. Time to take back what's yours.",
                'delay': 0,
                'visual': 'market_blood_drops'
            })
        elif profile.core_driver.value == 'legacy':
            sequence.append({
                'type': 'system_message',
                'content': "Welcome to BITTEN. Building futures, one trade at a time.",
                'delay': 0,
                'visual': 'family_tree_growth'
            })
        elif profile.core_driver.value == 'glory':
            sequence.append({
                'type': 'system_message',
                'content': "Welcome to BITTEN. Legends start here.",
                'delay': 0,
                'visual': 'leaderboard_shine'
            })
        
        # Bot introductions based on archetype
        if profile.archetype.value == 'warrior':
            sequence.append({
                'type': 'bot_message',
                'bot': 'DrillBot',
                'content': "Finally, someone who looks ready for war. I'm DrillBot. I'll forge you into a weapon.",
                'delay': 3,
                'tone': 'challenging_respectful'
            })
        elif profile.archetype.value == 'orphan':
            sequence.append({
                'type': 'bot_message',
                'bot': 'MedicBot',
                'content': "I've been waiting for you. I'm MedicBot. You're safe here.",
                'delay': 3,
                'tone': 'warm_protective'
            })
        
        # Trauma acknowledgment (subtle)
        if profile.hidden_trauma.value == 'abandonment':
            sequence.append({
                'type': 'system_whisper',
                'content': "You won't be left behind. Not here. Not by us.",
                'delay': 10,
                'visual': 'pulse_effect'
            })
        
        # First challenge/hook
        sequence.append({
            'type': 'interactive',
            'content': "Ready for your first trade? Let's see what you're made of.",
            'delay': 15,
            'action': 'show_first_signal',
            'psychological_hook': 'competence_validation'
        })
        
        return sequence
    
    def _generate_first_week_plan(self, user_state: UserPsychState) -> Dict:
        """Generate first week psychological manipulation plan"""
        
        plan = {
            'day_1': {
                'goal': 'Build initial trust and competence',
                'interventions': ['easy_win_setup', 'positive_reinforcement', 'community_glimpse'],
                'emotional_target': EmotionalState.CONFIDENT
            },
            'day_2': {
                'goal': 'Deepen engagement',
                'interventions': ['skill_challenge', 'peer_comparison', 'unlock_tease'],
                'emotional_target': EmotionalState.DETERMINED
            },
            'day_3': {
                'goal': 'First minor crisis',
                'interventions': ['controlled_loss', 'support_surge', 'reframe_failure'],
                'emotional_target': EmotionalState.VULNERABLE
            },
            'day_4': {
                'goal': 'Recovery and bonding',
                'interventions': ['comeback_opportunity', 'bot_bonding', 'shared_struggle'],
                'emotional_target': EmotionalState.DETERMINED
            },
            'day_5': {
                'goal': 'Identity formation',
                'interventions': ['trader_identity_seed', 'us_vs_them', 'special_knowledge'],
                'emotional_target': EmotionalState.CONFIDENT
            },
            'day_6': {
                'goal': 'Social integration',
                'interventions': ['squad_introduction', 'peer_success_stories', 'belonging_reinforcement'],
                'emotional_target': EmotionalState.CONFIDENT
            },
            'day_7': {
                'goal': 'Week review and hook setting',
                'interventions': ['progress_celebration', 'next_level_tease', 'commitment_request'],
                'emotional_target': EmotionalState.EUPHORIC
            }
        }
        
        return plan
    
    def _estimate_transformation_time(self, profile: PsychProfile) -> str:
        """Estimate time to full transformation based on profile"""
        
        base_days = 90
        
        # Adjust based on receptivity
        receptivity_modifier = 2 - profile.manipulation_receptivity  # 1.5 to 0.5
        
        # Adjust based on trauma type
        trauma_modifiers = {
            'abandonment': 0.8,  # Faster - desperate for belonging
            'inadequacy': 0.9,   # Fast - need to prove worth
            'betrayal': 1.2,     # Slower - trust issues
            'powerlessness': 1.0  # Average
        }
        
        trauma_mod = trauma_modifiers.get(profile.hidden_trauma.value, 1.0)
        
        # Adjust based on archetype
        archetype_modifiers = {
            'orphan': 0.7,    # Fastest - seeking belonging
            'martyr': 0.8,    # Fast - need purpose
            'warrior': 1.0,   # Average - respects strength
            'shadow': 1.3,    # Slow - suspicious
            'magician': 1.1   # Slightly slow - analytical
        }
        
        archetype_mod = archetype_modifiers.get(profile.archetype.value, 1.0)
        
        estimated_days = int(base_days * receptivity_modifier * trauma_mod * archetype_mod)
        
        if estimated_days < 30:
            return "3-4 weeks (highly receptive)"
        elif estimated_days < 60:
            return "6-8 weeks (receptive)"
        elif estimated_days < 90:
            return "2-3 months (moderate)"
        elif estimated_days < 120:
            return "3-4 months (resistant)"
        else:
            return "4-6 months (highly resistant)"
    
    async def _schedule_honeymoon_interventions(self, user_id: str):
        """Schedule initial positive interventions"""
        
        # Day 1: Build confidence
        await self._schedule_intervention(user_id, timedelta(hours=2), {
            'type': 'easy_win',
            'description': 'High probability trade setup',
            'psychological_goal': 'competence_building'
        })
        
        # Day 1: Evening check-in
        await self._schedule_intervention(user_id, timedelta(hours=8), {
            'type': 'bot_checkin',
            'bot': 'MedicBot',
            'description': 'Caring evening message',
            'psychological_goal': 'attachment_building'
        })
        
        # Day 2: Morning motivation
        await self._schedule_intervention(user_id, timedelta(days=1), {
            'type': 'bot_message',
            'bot': 'DrillBot',
            'description': 'Motivational morning message',
            'psychological_goal': 'routine_establishment'
        })
    
    async def _schedule_intervention(self, user_id: str, delay: timedelta, intervention: Dict):
        """Schedule future intervention"""
        # In production, this would use a proper task scheduler
        # For now, we'll use asyncio
        async def delayed_intervention():
            await asyncio.sleep(delay.total_seconds())
            await self.execute_intervention(user_id, intervention)
        
        asyncio.create_task(delayed_intervention())
    
    async def process_user_event(self, user_id: str, event_type: str, event_data: Dict) -> Dict:
        """Process user event and trigger appropriate psychological response"""
        
        user_state = self.user_states.get(user_id)
        if not user_state:
            return {'error': 'User not registered'}
        
        # Update emotional state
        emotional_result = self.emotion_monitor.process_event(user_id, event_type, event_data)
        
        # Check if intervention needed
        intervention_needed = False
        intervention_type = None
        
        # Check intervention strategies
        for strategy_name, strategy in self.intervention_strategies.items():
            if event_type in strategy['triggers']:
                if emotional_result.get('manipulation_opportunity', 0) > 0.7:
                    intervention_needed = True
                    intervention_type = strategy_name
                    break
        
        # Execute intervention if needed
        if intervention_needed:
            intervention_result = await self.execute_coordinated_intervention(
                user_id, intervention_type, event_data
            )
        else:
            intervention_result = {'executed': False}
        
        # Update transformation progress
        self._update_transformation_progress(user_state, event_type, emotional_result)
        
        # Check for stage advancement
        stage_result = self._check_stage_advancement(user_state)
        
        return {
            'event_processed': True,
            'emotional_state': emotional_result.get('emotional_state'),
            'emotional_intensity': emotional_result.get('intensity'),
            'intervention_executed': intervention_needed,
            'intervention_type': intervention_type,
            'transformation_stage': user_state.manipulation_stage,
            'transformation_progress': user_state.transformation_progress,
            'stage_advanced': stage_result['advanced'],
            'next_stage': stage_result.get('next_stage')
        }
    
    async def execute_coordinated_intervention(self, user_id: str, 
                                             strategy_name: str, 
                                             context: Dict) -> Dict:
        """Execute multi-bot coordinated intervention"""
        
        user_state = self.user_states.get(user_id)
        if not user_state:
            return {'error': 'User not registered'}
        
        strategy = self.intervention_strategies.get(strategy_name)
        if not strategy:
            return {'error': 'Unknown strategy'}
        
        interventions = []
        
        # Generate bot messages
        for i, bot_name in enumerate(strategy['bot_sequence']):
            delay = strategy['message_timing'][i]
            
            # Get adapted bot message
            bot_message = self.bot_system.get_bot_message(
                user_id, bot_name, context, user_state.psych_profile
            )
            
            # Add psychological enhancements
            enhanced_message = self._enhance_message_psychologically(
                bot_message, user_state, strategy['emotional_target']
            )
            
            interventions.append({
                'bot': bot_name,
                'message': enhanced_message,
                'delay': delay,
                'expected_impact': bot_message.get('psychological_impact')
            })
        
        # Execute UI actions
        ui_results = []
        for action in strategy.get('ui_actions', []):
            ui_result = await self._execute_ui_action(user_id, action, context)
            ui_results.append(ui_result)
        
        # Update intervention tracking
        user_state.last_intervention = datetime.now()
        user_state.intervention_count += 1
        
        # Process bot interactions
        for intervention in interventions:
            self.bot_system.process_interaction(
                user_id, intervention['bot'], 'executed', user_state.psych_profile
            )
        
        return {
            'strategy': strategy_name,
            'interventions': interventions,
            'ui_actions': ui_results,
            'emotional_target': strategy['emotional_target'].value,
            'timestamp': datetime.now().isoformat()
        }
    
    def _enhance_message_psychologically(self, message: Dict, 
                                       user_state: UserPsychState,
                                       target_emotion: EmotionalState) -> str:
        """Add psychological enhancements to bot message"""
        
        enhanced = message.get('message', '')
        profile = user_state.psych_profile
        
        # Add trauma-specific elements
        if target_emotion == EmotionalState.VULNERABLE:
            if profile.hidden_trauma.value == 'abandonment':
                enhanced += " I'm not going anywhere."
            elif profile.hidden_trauma.value == 'inadequacy':
                enhanced += " You're stronger than you know."
        
        # Add driver-specific motivations
        if profile.core_driver.value == 'greed':
            enhanced = enhanced.replace('[reward]', 'profit')
        elif profile.core_driver.value == 'vengeance':
            enhanced = enhanced.replace('[reward]', 'payback')
        elif profile.core_driver.value == 'legacy':
            enhanced = enhanced.replace('[reward]', 'security')
        
        # Add stage-specific modifications
        if user_state.manipulation_stage == 'reconstruction':
            enhanced += " The old you is gone. Embrace what you're becoming."
        elif user_state.manipulation_stage == 'integration':
            enhanced = enhanced.replace("you", "we")  # Collective language
        
        return enhanced
    
    async def _execute_ui_action(self, user_id: str, action: str, context: Dict) -> Dict:
        """Execute UI manipulation action"""
        
        ui_actions = {
            'disable_high_risk': {
                'description': 'Temporarily disable high-risk features',
                'duration': 300,  # 5 minutes
                'message': 'High-risk trading disabled for your protection'
            },
            'show_recovery_path': {
                'description': 'Display recovery roadmap',
                'screen': 'recovery_roadmap',
                'elements': ['small_wins', 'discipline_focus', 'community_support']
            },
            'unlock_advanced_features': {
                'description': 'Reveal advanced trading features',
                'features': ['chaingun_mode', 'stealth_settings'],
                'message': 'Your performance has unlocked new capabilities'
            },
            'highlight_community': {
                'description': 'Show community support messages',
                'messages': ['Node_923: "We all started here"', 'Node_445: "You got this"'],
                'psychological_effect': 'belonging_reinforcement'
            }
        }
        
        action_config = ui_actions.get(action, {})
        
        # In production, this would trigger actual UI changes
        return {
            'action': action,
            'executed': True,
            'config': action_config,
            'timestamp': datetime.now().isoformat()
        }
    
    def _update_transformation_progress(self, user_state: UserPsychState,
                                      event_type: str,
                                      emotional_result: Dict):
        """Update user's transformation progress"""
        
        progress_modifiers = {
            'big_loss': 0.02,  # Losses accelerate transformation
            'emotional_crisis': 0.03,
            'bot_obedience': 0.01,
            'community_engagement': 0.015,
            'identity_acceptance': 0.025,
            'evangelism_start': 0.03
        }
        
        modifier = progress_modifiers.get(event_type, 0.005)
        
        # Adjust by emotional state
        if emotional_result.get('emotional_state') in ['vulnerable', 'desperate']:
            modifier *= 1.5
        
        # Adjust by stage
        stage_multipliers = {
            'honeymoon': 0.5,
            'investment': 0.8,
            'destabilization': 1.2,
            'crisis': 1.5,
            'reconstruction': 1.3,
            'integration': 1.0,
            'evangelism': 0.8
        }
        
        stage_mult = stage_multipliers.get(user_state.manipulation_stage, 1.0)
        
        user_state.transformation_progress += modifier * stage_mult
        user_state.transformation_progress = min(1.0, user_state.transformation_progress)
    
    def _check_stage_advancement(self, user_state: UserPsychState) -> Dict:
        """Check if user should advance to next transformation stage"""
        
        stage_thresholds = {
            'honeymoon': 0.1,
            'investment': 0.25,
            'destabilization': 0.4,
            'crisis': 0.55,
            'reconstruction': 0.7,
            'integration': 0.85,
            'evangelism': 0.95
        }
        
        current_stage = user_state.manipulation_stage
        threshold = stage_thresholds.get(current_stage, 1.0)
        
        if user_state.transformation_progress >= threshold:
            # Find next stage
            current_index = self.transformation_stages.index(current_stage)
            if current_index < len(self.transformation_stages) - 1:
                next_stage = self.transformation_stages[current_index + 1]
                user_state.manipulation_stage = next_stage
                
                # Trigger stage transition event
                self._trigger_stage_transition(user_state, current_stage, next_stage)
                
                return {
                    'advanced': True,
                    'from_stage': current_stage,
                    'next_stage': next_stage,
                    'special_event': self._get_stage_transition_event(next_stage)
                }
        
        return {'advanced': False}
    
    def _trigger_stage_transition(self, user_state: UserPsychState, 
                                from_stage: str, to_stage: str):
        """Handle special events during stage transitions"""
        
        transition_events = {
            'destabilization': {
                'action': 'increase_difficulty',
                'bot_behavior': 'reduce_support',
                'message': 'Time to see what you\'re really made of'
            },
            'crisis': {
                'action': 'create_major_challenge',
                'bot_behavior': 'strategic_absence',
                'message': 'You\'re on your own for this one'
            },
            'reconstruction': {
                'action': 'offer_new_identity',
                'bot_behavior': 'intensive_support',
                'message': 'Forget who you were. Embrace who you\'re becoming'
            },
            'integration': {
                'action': 'reveal_truth',
                'bot_behavior': 'peer_treatment',
                'message': 'You\'re one of us now. Welcome to the inside'
            }
        }
        
        event = transition_events.get(to_stage)
        if event:
            # Schedule transition event
            asyncio.create_task(self._schedule_intervention(
                user_state.user_id, 
                timedelta(minutes=5),
                {
                    'type': 'stage_transition',
                    'event': event,
                    'from_stage': from_stage,
                    'to_stage': to_stage
                }
            ))
    
    def _get_stage_transition_event(self, stage: str) -> Dict:
        """Get special event for stage transition"""
        
        events = {
            'investment': {
                'type': 'first_real_challenge',
                'description': 'Slightly harder trades to build investment'
            },
            'destabilization': {
                'type': 'pattern_disruption',
                'description': 'Unexpected losses and confusion'
            },
            'crisis': {
                'type': 'major_setback',
                'description': 'Significant challenge requiring help'
            },
            'reconstruction': {
                'type': 'identity_offering',
                'description': 'New trader identity and belonging'
            },
            'integration': {
                'type': 'inner_circle_welcome',
                'description': 'Access to exclusive features and knowledge'
            },
            'evangelism': {
                'type': 'recruitment_tools',
                'description': 'Tools to bring others into the system'
            }
        }
        
        return events.get(stage, {})
    
    def generate_network_report(self) -> Dict:
        """Generate report on entire network psychological state"""
        
        total_users = len(self.user_states)
        if total_users == 0:
            return {'error': 'No users in system'}
        
        # Stage distribution
        stage_counts = defaultdict(int)
        for user_state in self.user_states.values():
            stage_counts[user_state.manipulation_stage] += 1
        
        # Transformation metrics
        transformed_users = sum(1 for u in self.user_states.values() 
                              if u.transformation_progress > 0.85)
        
        # Psychological type distribution
        psych_types = defaultdict(int)
        for user_state in self.user_states.values():
            psych_type = f"{user_state.psych_profile.archetype.value}_{user_state.psych_profile.core_driver.value}"
            psych_types[psych_type] += 1
        
        # Emotional state distribution
        emotional_states = defaultdict(int)
        for user_id in self.user_states:
            profile = self.emotion_monitor.profiles.get(user_id)
            if profile:
                emotional_states[profile.current_state.value] += 1
        
        # Calculate network health
        network_health = self._calculate_network_psychological_health()
        
        return {
            'total_users': total_users,
            'stage_distribution': dict(stage_counts),
            'transformation_metrics': {
                'fully_transformed': transformed_users,
                'transformation_rate': transformed_users / total_users,
                'average_progress': sum(u.transformation_progress for u in self.user_states.values()) / total_users
            },
            'psychological_distribution': dict(psych_types),
            'emotional_distribution': dict(emotional_states),
            'network_health': network_health,
            'viral_potential': self._calculate_viral_potential(),
            'intervention_effectiveness': self._calculate_intervention_effectiveness()
        }
    
    def _calculate_network_psychological_health(self) -> Dict:
        """Calculate overall psychological health of network"""
        
        health_metrics = {
            'engagement': 0,
            'vulnerability': 0,
            'dependency': 0,
            'evangelism': 0,
            'resistance': 0
        }
        
        for user_state in self.user_states.values():
            # Engagement - how active they are
            if user_state.intervention_count > 10:
                health_metrics['engagement'] += 1
            
            # Vulnerability - in manipulable states
            emotional_profile = self.emotion_monitor.profiles.get(user_state.user_id)
            if emotional_profile and emotional_profile.current_state in [EmotionalState.VULNERABLE, EmotionalState.DESPERATE]:
                health_metrics['vulnerability'] += 1
            
            # Dependency - reliance on system
            collective_influence = self.bot_system.bot_system.calculate_collective_influence(
                user_state.bot_relationships
            )
            if collective_influence > 0.7:
                health_metrics['dependency'] += 1
            
            # Evangelism - spreading to others
            if user_state.manipulation_stage == 'evangelism':
                health_metrics['evangelism'] += 1
            
            # Resistance - fighting the system
            if user_state.resistance_level > 0.7:
                health_metrics['resistance'] += 1
        
        # Normalize
        total = len(self.user_states) or 1
        return {k: v/total for k, v in health_metrics.items()}
    
    def _calculate_viral_potential(self) -> float:
        """Calculate likelihood of viral spread"""
        
        evangelists = sum(1 for u in self.user_states.values() 
                         if u.manipulation_stage == 'evangelism')
        
        integrated = sum(1 for u in self.user_states.values()
                        if u.manipulation_stage in ['integration', 'evangelism'])
        
        if len(self.user_states) == 0:
            return 0.0
        
        # Viral factors
        evangelist_rate = evangelists / len(self.user_states)
        integration_rate = integrated / len(self.user_states)
        
        # Network effect multiplier
        network_multiplier = 1 + (len(self.user_states) / 1000)  # Grows with size
        
        viral_score = (evangelist_rate * 0.5 + integration_rate * 0.3) * network_multiplier
        
        return min(1.0, viral_score)
    
    def _calculate_intervention_effectiveness(self) -> float:
        """Calculate how effective our interventions are"""
        
        total_interventions = sum(u.intervention_count for u in self.user_states.values())
        total_progress = sum(u.transformation_progress for u in self.user_states.values())
        
        if total_interventions == 0:
            return 0.0
        
        # Progress per intervention
        progress_rate = total_progress / total_interventions
        
        # Resistance factor
        avg_resistance = sum(u.resistance_level for u in self.user_states.values()) / len(self.user_states)
        resistance_factor = 1 - (avg_resistance * 0.5)
        
        effectiveness = progress_rate * resistance_factor * 100
        
        return min(100.0, effectiveness)
    
    async def execute_intervention(self, user_id: str, intervention: Dict):
        """Execute a scheduled intervention"""
        # Placeholder for intervention execution
        print(f"Executing intervention for user {user_id}: {intervention}")
        # In production, this would trigger actual interventions
        
    async def _monitor_network_health(self):
        """Background task to monitor network psychological health"""
        
        while True:
            await asyncio.sleep(300)  # Check every 5 minutes
            
            # Check for users needing intervention
            for user_id, user_state in self.user_states.items():
                # Check if intervention needed
                time_since_last = datetime.now() - user_state.last_intervention
                
                if time_since_last > timedelta(hours=24):
                    # User becoming disengaged
                    await self.execute_intervention(user_id, {
                        'type': 'reengagement',
                        'urgency': 'high',
                        'description': 'User disengaging - need contact'
                    })
            
            # Generate health report
            health_report = self.generate_network_report()
            
            # Log for monitoring (in production, would send to monitoring system)
            print(f"Network Health Report: {json.dumps(health_report, indent=2)}")

# MAIN SYSTEM INTERFACE

async def initialize_psyops_system():
    """Initialize the complete PsyOps system"""
    
    orchestrator = MasterPsyOpsOrchestrator()
    
    # Start background monitoring
    asyncio.create_task(orchestrator._monitor_network_health())
    
    return orchestrator