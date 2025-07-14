"""
BITTEN Mission Progression System
Manages progression from basic to advanced tactical operations based on demonstrated competency
Unlocks new mission types, capabilities, and story elements as users prove their skills
"""

import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

# Import existing systems
try:
    from .tactical_mission_framework import OperationType, MissionPhase, TacticalMissionFramework
    from .norman_story_integration import StoryPhase, norman_story_engine
    from .mission_briefing_generator import MissionType, UrgencyLevel
except ImportError:
    # Fallback for testing
    class OperationType(Enum):
        RECONNAISSANCE = "reconnaissance"
        INFILTRATION = "infiltration"
        PRECISION_STRIKE = "precision_strike"
        EXTRACTION = "extraction"
        SUPPORT_MISSION = "support_mission"
        JOINT_OPERATION = "joint_operation"

class OperatorRank(Enum):
    """Military ranks that users progress through"""
    RECRUIT = "recruit"                    # New users, basic training
    PRIVATE = "private"                    # Completed first trade successfully
    CORPORAL = "corporal"                  # Consistent profits, good risk management
    SERGEANT = "sergeant"                  # Multiple successful operations
    LIEUTENANT = "lieutenant"              # Advanced techniques, leadership qualities
    CAPTAIN = "captain"                    # Expert level, helping others
    MAJOR = "major"                        # Master trader, community contributor
    COLONEL = "colonel"                    # Elite status, strategic thinking
    GENERAL = "general"                    # Legendary trader, Norman's successor

class MissionDifficulty(Enum):
    """Mission difficulty levels"""
    BASIC_TRAINING = "basic_training"      # Tutorial missions
    STANDARD = "standard"                  # Regular operations
    ADVANCED = "advanced"                  # Challenging setups
    EXPERT = "expert"                      # High-risk/high-reward
    ELITE = "elite"                        # Ultra-challenging scenarios
    LEGENDARY = "legendary"                # Ultimate missions

class UnlockableCapability(Enum):
    """Capabilities that can be unlocked through progression"""
    MULTIPLE_POSITIONS = "multiple_positions"        # Trade multiple pairs
    ADVANCED_RISK_MGMT = "advanced_risk_management" # Complex risk strategies
    PATTERN_RECOGNITION = "pattern_recognition"      # Advanced TA
    NEWS_TRADING = "news_trading"                   # Economic event trading
    CORRELATION_TRADING = "correlation_trading"      # Multi-asset strategies
    SWING_POSITIONS = "swing_positions"             # Longer-term trades
    HEDGING_STRATEGIES = "hedging_strategies"       # Risk hedging
    MENTOR_ABILITIES = "mentor_abilities"           # Help other traders
    SIGNAL_CREATION = "signal_creation"             # Create own signals
    COMMUNITY_LEADERSHIP = "community_leadership"   # Lead squads/teams

@dataclass
class OperatorProfile:
    """Complete operator profile with progression tracking"""
    user_id: str
    callsign: str
    current_rank: OperatorRank
    
    # Experience and progression
    total_experience: int
    missions_completed: int
    mission_success_rate: float
    current_win_rate: float
    
    # Skill assessments
    risk_management_score: int      # 0-100
    execution_quality_score: int    # 0-100
    emotional_control_score: int    # 0-100
    technical_analysis_score: int   # 0-100
    
    # Unlocked capabilities
    unlocked_mission_types: List[OperationType]
    unlocked_capabilities: List[UnlockableCapability]
    maximum_difficulty: MissionDifficulty
    
    # Story progression
    story_phase: StoryPhase
    story_elements_revealed: List[str]
    norman_wisdom_learned: List[str]
    
    # Achievement tracking
    commendations_earned: List[str]
    milestones_achieved: List[str]
    special_recognitions: List[str]
    
    # Mentorship
    is_mentor: bool
    mentees: List[str]
    community_contributions: int
    
    # Activity tracking
    last_active: int
    days_active: int
    consecutive_trading_days: int
    
    # Personal records
    best_trade_return: float
    longest_win_streak: int
    total_profits: float
    largest_loss: float

@dataclass 
class MissionTemplate:
    """Template for generating missions of different types and difficulties"""
    template_id: str
    operation_type: OperationType
    difficulty: MissionDifficulty
    required_rank: OperatorRank
    required_capabilities: List[UnlockableCapability]
    
    # Mission characteristics
    estimated_duration: int          # minutes
    complexity_level: int           # 1-10
    risk_level: int                # 1-10
    educational_focus: List[str]    # Learning objectives
    
    # Story integration
    story_arc: str
    norman_connection: str
    bit_presence_type: str
    
    # Unlock requirements
    prerequisite_missions: List[str]
    minimum_success_rate: float
    minimum_experience: int
    
    # Rewards
    experience_reward: int
    possible_unlocks: List[UnlockableCapability]
    story_revelations: List[str]

class MissionProgressionSystem:
    """Main system for managing mission progression and unlocks"""
    
    def __init__(self):
        self.operator_profiles: Dict[str, OperatorProfile] = {}
        self.mission_templates = self._initialize_mission_templates()
        self.rank_requirements = self._initialize_rank_requirements()
        self.unlock_criteria = self._initialize_unlock_criteria()
        
    def _initialize_mission_templates(self) -> Dict[str, MissionTemplate]:
        """Initialize all mission templates organized by progression level"""
        templates = {}
        
        # BASIC TRAINING MISSIONS
        templates['normandy_echo'] = MissionTemplate(
            template_id='normandy_echo',
            operation_type=OperationType.RECONNAISSANCE,
            difficulty=MissionDifficulty.BASIC_TRAINING,
            required_rank=OperatorRank.RECRUIT,
            required_capabilities=[],
            estimated_duration=30,
            complexity_level=2,
            risk_level=2,
            educational_focus=['position_sizing', 'stop_loss_discipline', 'trade_execution'],
            story_arc='first_trade_courage',
            norman_connection="Norman's very first live trade - the moment that changed everything",
            bit_presence_type='encouraging_guide',
            prerequisite_missions=[],
            minimum_success_rate=0.0,
            minimum_experience=0,
            experience_reward=100,
            possible_unlocks=[],
            story_revelations=['bit_arrival_story', 'first_trade_memory']
        )
        
        templates['alpha_foundation'] = MissionTemplate(
            template_id='alpha_foundation',
            operation_type=OperationType.RECONNAISSANCE,
            difficulty=MissionDifficulty.STANDARD,
            required_rank=OperatorRank.PRIVATE,
            required_capabilities=[],
            estimated_duration=45,
            complexity_level=3,
            risk_level=3,
            educational_focus=['trend_identification', 'entry_timing', 'patience'],
            story_arc='building_discipline',
            norman_connection="Learning to read the market like Norman learned to read the Delta",
            bit_presence_type='patient_observer',
            prerequisite_missions=['normandy_echo'],
            minimum_success_rate=0.6,
            minimum_experience=100,
            experience_reward=150,
            possible_unlocks=[],
            story_revelations=['grandmother_patience_wisdom']
        )
        
        # INTERMEDIATE MISSIONS
        templates['delta_precision'] = MissionTemplate(
            template_id='delta_precision',
            operation_type=OperationType.PRECISION_STRIKE,
            difficulty=MissionDifficulty.STANDARD,
            required_rank=OperatorRank.CORPORAL,
            required_capabilities=[],
            estimated_duration=60,
            complexity_level=5,
            risk_level=4,
            educational_focus=['precise_entries', 'market_timing', 'confluence_trading'],
            story_arc='developing_expertise',
            norman_connection="Norman's breakthrough in precision - when good became great",
            bit_presence_type='tactical_advisor',
            prerequisite_missions=['alpha_foundation'],
            minimum_success_rate=0.65,
            minimum_experience=300,
            experience_reward=200,
            possible_unlocks=[UnlockableCapability.ADVANCED_RISK_MGMT],
            story_revelations=['norman_precision_breakthrough', 'mother_sacrifice_story']
        )
        
        templates['bravo_extraction'] = MissionTemplate(
            template_id='bravo_extraction',
            operation_type=OperationType.EXTRACTION,
            difficulty=MissionDifficulty.STANDARD,
            required_rank=OperatorRank.CORPORAL,
            required_capabilities=[],
            estimated_duration=45,
            complexity_level=4,
            risk_level=5,
            educational_focus=['exit_strategies', 'profit_taking', 'loss_cutting'],
            story_arc='mastering_exits',
            norman_connection="The hardest lesson Norman learned - when to let go",
            bit_presence_type='protective_companion',
            prerequisite_missions=['delta_precision'],
            minimum_success_rate=0.7,
            minimum_experience=500,
            experience_reward=180,
            possible_unlocks=[UnlockableCapability.PATTERN_RECOGNITION],
            story_revelations=['grandmother_letting_go_wisdom']
        )
        
        # ADVANCED MISSIONS
        templates['charlie_infiltration'] = MissionTemplate(
            template_id='charlie_infiltration',
            operation_type=OperationType.INFILTRATION,
            difficulty=MissionDifficulty.ADVANCED,
            required_rank=OperatorRank.SERGEANT,
            required_capabilities=[UnlockableCapability.ADVANCED_RISK_MGMT],
            estimated_duration=90,
            complexity_level=6,
            risk_level=6,
            educational_focus=['market_structure', 'liquidity_hunting', 'advanced_entries'],
            story_arc='advanced_techniques',
            norman_connection="Norman's discovery of hidden market patterns",
            bit_presence_type='silent_hunter',
            prerequisite_missions=['bravo_extraction'],
            minimum_success_rate=0.7,
            minimum_experience=800,
            experience_reward=300,
            possible_unlocks=[UnlockableCapability.MULTIPLE_POSITIONS],
            story_revelations=['norman_pattern_discovery', 'delta_wisdom_deep']
        )
        
        templates['echo_support'] = MissionTemplate(
            template_id='echo_support',
            operation_type=OperationType.SUPPORT_MISSION,
            difficulty=MissionDifficulty.ADVANCED,
            required_rank=OperatorRank.LIEUTENANT,
            required_capabilities=[UnlockableCapability.PATTERN_RECOGNITION],
            estimated_duration=120,
            complexity_level=7,
            risk_level=5,
            educational_focus=['psychology', 'discipline', 'emotional_control'],
            story_arc='mental_mastery',
            norman_connection="Norman's greatest battle was with himself",
            bit_presence_type='emotional_anchor',
            prerequisite_missions=['charlie_infiltration'],
            minimum_success_rate=0.75,
            minimum_experience=1200,
            experience_reward=350,
            possible_unlocks=[UnlockableCapability.NEWS_TRADING],
            story_revelations=['norman_emotional_journey', 'bit_calming_presence']
        )
        
        # EXPERT MISSIONS
        templates['foxtrot_joint_ops'] = MissionTemplate(
            template_id='foxtrot_joint_ops',
            operation_type=OperationType.JOINT_OPERATION,
            difficulty=MissionDifficulty.EXPERT,
            required_rank=OperatorRank.CAPTAIN,
            required_capabilities=[UnlockableCapability.MULTIPLE_POSITIONS, UnlockableCapability.NEWS_TRADING],
            estimated_duration=180,
            complexity_level=8,
            risk_level=7,
            educational_focus=['correlation_trading', 'portfolio_management', 'advanced_risk'],
            story_arc='mastery_achievement',
            norman_connection="The complex strategies that made Norman a legend",
            bit_presence_type='master_companion',
            prerequisite_missions=['echo_support'],
            minimum_success_rate=0.75,
            minimum_experience=2000,
            experience_reward=500,
            possible_unlocks=[UnlockableCapability.CORRELATION_TRADING, UnlockableCapability.SWING_POSITIONS],
            story_revelations=['norman_mastery_moment', 'family_legacy_complete']
        )
        
        # ELITE MISSIONS
        templates['golf_legendary'] = MissionTemplate(
            template_id='golf_legendary',
            operation_type=OperationType.JOINT_OPERATION,
            difficulty=MissionDifficulty.LEGENDARY,
            required_rank=OperatorRank.MAJOR,
            required_capabilities=[
                UnlockableCapability.CORRELATION_TRADING,
                UnlockableCapability.SWING_POSITIONS,
                UnlockableCapability.HEDGING_STRATEGIES
            ],
            estimated_duration=240,
            complexity_level=10,
            risk_level=9,
            educational_focus=['mastery_synthesis', 'market_innovation', 'legacy_building'],
            story_arc='legend_creation',
            norman_connection="Surpassing Norman's achievements - becoming the legend",
            bit_presence_type='legend_witness',
            prerequisite_missions=['foxtrot_joint_ops'],
            minimum_success_rate=0.8,
            minimum_experience=5000,
            experience_reward=1000,
            possible_unlocks=[UnlockableCapability.MENTOR_ABILITIES, UnlockableCapability.SIGNAL_CREATION],
            story_revelations=['norman_full_story', 'legend_status_achieved']
        )
        
        return templates
    
    def _initialize_rank_requirements(self) -> Dict[OperatorRank, Dict]:
        """Define requirements for each rank advancement"""
        return {
            OperatorRank.PRIVATE: {
                'missions_required': 1,
                'success_rate_required': 0.6,
                'experience_required': 100,
                'special_requirements': ['complete_normandy_echo']
            },
            OperatorRank.CORPORAL: {
                'missions_required': 3,
                'success_rate_required': 0.65,
                'experience_required': 300,
                'special_requirements': ['demonstrate_risk_management']
            },
            OperatorRank.SERGEANT: {
                'missions_required': 6,
                'success_rate_required': 0.7,
                'experience_required': 600,
                'special_requirements': ['advanced_mission_success']
            },
            OperatorRank.LIEUTENANT: {
                'missions_required': 10,
                'success_rate_required': 0.72,
                'experience_required': 1000,
                'special_requirements': ['leadership_demonstration']
            },
            OperatorRank.CAPTAIN: {
                'missions_required': 15,
                'success_rate_required': 0.75,
                'experience_required': 1500,
                'special_requirements': ['expert_mission_success', 'mentor_others']
            },
            OperatorRank.MAJOR: {
                'missions_required': 25,
                'success_rate_required': 0.78,
                'experience_required': 2500,
                'special_requirements': ['elite_mission_success', 'community_contribution']
            },
            OperatorRank.COLONEL: {
                'missions_required': 40,
                'success_rate_required': 0.8,
                'experience_required': 4000,
                'special_requirements': ['legendary_mission_attempt', 'significant_mentorship']
            },
            OperatorRank.GENERAL: {
                'missions_required': 60,
                'success_rate_required': 0.82,
                'experience_required': 7000,
                'special_requirements': ['legendary_mission_success', 'community_leadership', 'norman_legacy_fulfilled']
            }
        }
    
    def _initialize_unlock_criteria(self) -> Dict[UnlockableCapability, Dict]:
        """Define criteria for unlocking capabilities"""
        return {
            UnlockableCapability.ADVANCED_RISK_MGMT: {
                'required_rank': OperatorRank.CORPORAL,
                'required_missions': ['delta_precision'],
                'risk_management_score': 80,
                'special_criteria': 'demonstrate_stop_loss_discipline'
            },
            UnlockableCapability.PATTERN_RECOGNITION: {
                'required_rank': OperatorRank.CORPORAL,
                'required_missions': ['bravo_extraction'],
                'technical_analysis_score': 75,
                'special_criteria': 'identify_market_patterns'
            },
            UnlockableCapability.MULTIPLE_POSITIONS: {
                'required_rank': OperatorRank.SERGEANT,
                'required_missions': ['charlie_infiltration'],
                'execution_quality_score': 80,
                'special_criteria': 'manage_single_position_expertly'
            },
            UnlockableCapability.NEWS_TRADING: {
                'required_rank': OperatorRank.LIEUTENANT,
                'required_missions': ['echo_support'],
                'emotional_control_score': 85,
                'special_criteria': 'demonstrate_news_reaction_control'
            },
            UnlockableCapability.CORRELATION_TRADING: {
                'required_rank': OperatorRank.CAPTAIN,
                'required_missions': ['foxtrot_joint_ops'],
                'technical_analysis_score': 85,
                'special_criteria': 'understand_market_relationships'
            },
            UnlockableCapability.MENTOR_ABILITIES: {
                'required_rank': OperatorRank.MAJOR,
                'required_missions': ['golf_legendary'],
                'community_contributions': 10,
                'special_criteria': 'demonstrate_teaching_ability'
            }
        }
    
    def get_operator_profile(self, user_id: str) -> OperatorProfile:
        """Get or create operator profile"""
        if user_id not in self.operator_profiles:
            self.operator_profiles[user_id] = OperatorProfile(
                user_id=user_id,
                callsign=self._generate_initial_callsign(user_id),
                current_rank=OperatorRank.RECRUIT,
                total_experience=0,
                missions_completed=0,
                mission_success_rate=0.0,
                current_win_rate=0.0,
                risk_management_score=50,
                execution_quality_score=50,
                emotional_control_score=50,
                technical_analysis_score=50,
                unlocked_mission_types=[OperationType.RECONNAISSANCE],
                unlocked_capabilities=[],
                maximum_difficulty=MissionDifficulty.BASIC_TRAINING,
                story_phase=StoryPhase.EARLY_STRUGGLE,
                story_elements_revealed=[],
                norman_wisdom_learned=[],
                commendations_earned=[],
                milestones_achieved=[],
                special_recognitions=[],
                is_mentor=False,
                mentees=[],
                community_contributions=0,
                last_active=int(time.time()),
                days_active=1,
                consecutive_trading_days=0,
                best_trade_return=0.0,
                longest_win_streak=0,
                total_profits=0.0,
                largest_loss=0.0
            )
        return self.operator_profiles[user_id]
    
    def get_available_missions(self, user_id: str) -> List[MissionTemplate]:
        """Get missions available to the operator based on their progression"""
        profile = self.get_operator_profile(user_id)
        available_missions = []
        
        for template in self.mission_templates.values():
            if self._is_mission_available(profile, template):
                available_missions.append(template)
        
        return available_missions
    
    def _is_mission_available(self, profile: OperatorProfile, template: MissionTemplate) -> bool:
        """Check if a mission is available to the operator"""
        
        # Check rank requirement
        if profile.current_rank.value < template.required_rank.value:
            return False
        
        # Check capability requirements
        for required_cap in template.required_capabilities:
            if required_cap not in profile.unlocked_capabilities:
                return False
        
        # Check prerequisite missions
        for prereq in template.prerequisite_missions:
            if prereq not in [m for m in profile.commendations_earned if prereq in m]:
                return False
        
        # Check minimum success rate
        if profile.mission_success_rate < template.minimum_success_rate:
            return False
        
        # Check minimum experience
        if profile.total_experience < template.minimum_experience:
            return False
        
        return True
    
    def complete_mission(self, user_id: str, mission_template_id: str, results: Dict) -> Dict:
        """Process mission completion and update progression"""
        profile = self.get_operator_profile(user_id)
        template = self.mission_templates.get(mission_template_id)
        
        if not template:
            return {'error': 'Mission template not found'}
        
        # Update mission statistics
        profile.missions_completed += 1
        profile.total_experience += template.experience_reward
        
        # Calculate success rate
        mission_success = results.get('success', False)
        if mission_success:
            new_successes = profile.mission_success_rate * (profile.missions_completed - 1) + 1
            profile.mission_success_rate = new_successes / profile.missions_completed
        else:
            new_successes = profile.mission_success_rate * (profile.missions_completed - 1)
            profile.mission_success_rate = new_successes / profile.missions_completed
        
        # Update skill scores based on performance
        self._update_skill_scores(profile, results)
        
        # Check for unlocks
        unlocks = self._check_unlocks(profile, template, results)
        
        # Check for rank advancement
        rank_advancement = self._check_rank_advancement(profile)
        
        # Update story progression
        story_updates = self._update_story_progression(profile, template, results)
        
        # Generate progression report
        progression_report = {
            'mission_completed': mission_template_id,
            'experience_gained': template.experience_reward,
            'new_total_experience': profile.total_experience,
            'updated_success_rate': profile.mission_success_rate,
            'unlocks': unlocks,
            'rank_advancement': rank_advancement,
            'story_updates': story_updates,
            'next_available_missions': [t.template_id for t in self.get_available_missions(user_id)],
            'achievements': self._check_achievements(profile, results)
        }
        
        return progression_report
    
    def _update_skill_scores(self, profile: OperatorProfile, results: Dict) -> None:
        """Update skill scores based on mission performance"""
        
        # Risk Management Score
        if results.get('risk_management_followed', False):
            profile.risk_management_score = min(100, profile.risk_management_score + 2)
        elif results.get('risk_violations', 0) > 0:
            profile.risk_management_score = max(0, profile.risk_management_score - 5)
        
        # Execution Quality Score
        execution_quality = results.get('execution_quality', 0.5)
        adjustment = int((execution_quality - 0.5) * 10)
        profile.execution_quality_score = max(0, min(100, profile.execution_quality_score + adjustment))
        
        # Emotional Control Score
        if results.get('emotional_deviations', 0) == 0:
            profile.emotional_control_score = min(100, profile.emotional_control_score + 3)
        else:
            profile.emotional_control_score = max(0, profile.emotional_control_score - 4)
        
        # Technical Analysis Score
        if results.get('analysis_accuracy', 0) > 0.7:
            profile.technical_analysis_score = min(100, profile.technical_analysis_score + 2)
    
    def _check_unlocks(self, profile: OperatorProfile, template: MissionTemplate, results: Dict) -> List[str]:
        """Check for capability unlocks"""
        unlocks = []
        
        for capability in template.possible_unlocks:
            if capability not in profile.unlocked_capabilities:
                criteria = self.unlock_criteria.get(capability, {})
                
                # Check all criteria
                if self._meets_unlock_criteria(profile, criteria):
                    profile.unlocked_capabilities.append(capability)
                    unlocks.append(capability.value)
        
        return unlocks
    
    def _meets_unlock_criteria(self, profile: OperatorProfile, criteria: Dict) -> bool:
        """Check if operator meets criteria for unlock"""
        
        # Check rank requirement
        required_rank = criteria.get('required_rank')
        if required_rank and profile.current_rank.value < required_rank.value:
            return False
        
        # Check skill score requirements
        for skill, required_score in criteria.items():
            if skill.endswith('_score'):
                current_score = getattr(profile, skill, 0)
                if current_score < required_score:
                    return False
        
        # Check special criteria (would need mission-specific implementation)
        special_criteria = criteria.get('special_criteria')
        if special_criteria:
            # This would be implemented based on specific criteria
            pass
        
        return True
    
    def _check_rank_advancement(self, profile: OperatorProfile) -> Optional[Dict]:
        """Check if operator qualifies for rank advancement"""
        current_rank_index = list(OperatorRank).index(profile.current_rank)
        
        # Can't advance beyond General
        if current_rank_index >= len(OperatorRank) - 1:
            return None
        
        next_rank = list(OperatorRank)[current_rank_index + 1]
        requirements = self.rank_requirements.get(next_rank, {})
        
        # Check requirements
        if (profile.missions_completed >= requirements.get('missions_required', 0) and
            profile.mission_success_rate >= requirements.get('success_rate_required', 0) and
            profile.total_experience >= requirements.get('experience_required', 0)):
            
            # Check special requirements (simplified)
            special_reqs = requirements.get('special_requirements', [])
            if self._meets_special_requirements(profile, special_reqs):
                # Advance rank
                old_rank = profile.current_rank
                profile.current_rank = next_rank
                
                # Unlock new mission types and difficulties
                self._unlock_rank_benefits(profile, next_rank)
                
                return {
                    'old_rank': old_rank.value,
                    'new_rank': next_rank.value,
                    'benefits_unlocked': self._get_rank_benefits(next_rank)
                }
        
        return None
    
    def _meets_special_requirements(self, profile: OperatorProfile, requirements: List[str]) -> bool:
        """Check special requirements for rank advancement"""
        # Simplified implementation - would need detailed mission tracking
        for requirement in requirements:
            if requirement == 'complete_normandy_echo':
                if 'normandy_echo' not in profile.commendations_earned:
                    return False
            elif requirement == 'demonstrate_risk_management':
                if profile.risk_management_score < 75:
                    return False
            # Add more specific requirements as needed
        
        return True
    
    def _unlock_rank_benefits(self, profile: OperatorProfile, new_rank: OperatorRank) -> None:
        """Unlock benefits associated with new rank"""
        
        rank_benefits = {
            OperatorRank.PRIVATE: {
                'mission_types': [OperationType.RECONNAISSANCE],
                'max_difficulty': MissionDifficulty.STANDARD
            },
            OperatorRank.CORPORAL: {
                'mission_types': [OperationType.PRECISION_STRIKE],
                'max_difficulty': MissionDifficulty.STANDARD
            },
            OperatorRank.SERGEANT: {
                'mission_types': [OperationType.INFILTRATION, OperationType.EXTRACTION],
                'max_difficulty': MissionDifficulty.ADVANCED
            },
            OperatorRank.LIEUTENANT: {
                'mission_types': [OperationType.SUPPORT_MISSION],
                'max_difficulty': MissionDifficulty.ADVANCED
            },
            OperatorRank.CAPTAIN: {
                'mission_types': [OperationType.JOINT_OPERATION],
                'max_difficulty': MissionDifficulty.EXPERT
            },
            OperatorRank.MAJOR: {
                'mission_types': [],  # All types already unlocked
                'max_difficulty': MissionDifficulty.ELITE
            },
            OperatorRank.COLONEL: {
                'mission_types': [],
                'max_difficulty': MissionDifficulty.LEGENDARY
            }
        }
        
        benefits = rank_benefits.get(new_rank, {})
        
        # Unlock new mission types
        for mission_type in benefits.get('mission_types', []):
            if mission_type not in profile.unlocked_mission_types:
                profile.unlocked_mission_types.append(mission_type)
        
        # Update maximum difficulty
        max_difficulty = benefits.get('max_difficulty')
        if max_difficulty:
            profile.maximum_difficulty = max_difficulty
    
    def _get_rank_benefits(self, rank: OperatorRank) -> List[str]:
        """Get list of benefits for achieving rank"""
        benefits_map = {
            OperatorRank.PRIVATE: ["Access to standard missions", "Basic tactical callsign"],
            OperatorRank.CORPORAL: ["Precision Strike operations", "Advanced risk management tools"],
            OperatorRank.SERGEANT: ["Infiltration missions", "Extraction operations", "Squad leadership potential"],
            OperatorRank.LIEUTENANT: ["Support mission command", "Mentor capabilities", "Advanced strategies"],
            OperatorRank.CAPTAIN: ["Joint operations", "Expert-level missions", "Community leadership"],
            OperatorRank.MAJOR: ["Elite mission access", "Signal creation rights", "Master trader status"],
            OperatorRank.COLONEL: ["Legendary missions", "Community governance", "Norman's inner circle"],
            OperatorRank.GENERAL: ["Ultimate mastery", "Legend status", "Norman's successor"]
        }
        return benefits_map.get(rank, [])
    
    def _update_story_progression(self, profile: OperatorProfile, template: MissionTemplate, results: Dict) -> Dict:
        """Update story progression based on mission completion"""
        story_updates = {}
        
        # Add story revelations from template
        for revelation in template.story_revelations:
            if revelation not in profile.story_elements_revealed:
                profile.story_elements_revealed.append(revelation)
                story_updates[revelation] = self._get_story_content(revelation)
        
        # Update story phase if appropriate
        if norman_story_engine:
            old_phase = profile.story_phase
            norman_story_engine.update_user_progress(profile.user_id, {
                'days_active': profile.days_active,
                'total_trades': profile.missions_completed,
                'win_rate': profile.mission_success_rate
            })
            new_context = norman_story_engine.get_user_story_context(profile.user_id)
            if new_context.current_phase != old_phase:
                profile.story_phase = new_context.current_phase
                story_updates['phase_advancement'] = {
                    'old_phase': old_phase.value,
                    'new_phase': new_context.current_phase.value
                }
        
        return story_updates
    
    def _get_story_content(self, revelation_id: str) -> str:
        """Get story content for revelation"""
        story_content = {
            'bit_arrival_story': "The night Bit appeared on Norman's windowsill, as if sent by destiny itself...",
            'first_trade_memory': "Norman's hands trembled as he clicked 'execute' for the first time, just like yours did...",
            'grandmother_patience_wisdom': "Grandmama's voice echoes: 'Patience, child. Good things come to those who wait for the right season.'",
            'norman_precision_breakthrough': "The moment Norman discovered that precision beats power every time...",
            'mother_sacrifice_story': "How Norman's mother worked two jobs to keep the family together, teaching him the value of sacrifice...",
            'norman_pattern_discovery': "Norman's eureka moment when he first saw the patterns hiding in market chaos...",
            'delta_wisdom_deep': "The ancient wisdom of the Mississippi Delta, flowing through generations of traders...",
            'norman_emotional_journey': "Norman's greatest battle wasn't with the market - it was with himself...",
            'bit_calming_presence': "How Bit learned to sense Norman's emotions and provide exactly the comfort needed...",
            'norman_mastery_moment': "The day Norman realized he had become the trader he always dreamed of being...",
            'family_legacy_complete': "How Norman's success fulfilled his promise to honor his family's sacrifices...",
            'norman_full_story': "The complete tale of Norman's journey from struggle to legend...",
            'legend_status_achieved': "You have walked Norman's path and made it your own. The legend continues..."
        }
        return story_content.get(revelation_id, "A new chapter in the legend unfolds...")
    
    def _check_achievements(self, profile: OperatorProfile, results: Dict) -> List[str]:
        """Check for special achievements"""
        achievements = []
        
        # Mission-specific achievements
        if results.get('perfect_execution', False):
            achievements.append("Perfect Execution")
        
        if results.get('risk_management_score', 0) == 100:
            achievements.append("Risk Management Master")
        
        # Milestone achievements
        if profile.missions_completed == 1:
            achievements.append("First Blood")
        elif profile.missions_completed == 10:
            achievements.append("Veteran Operator")
        elif profile.missions_completed == 50:
            achievements.append("Mission Master")
        
        # Win streak achievements
        win_streak = results.get('current_win_streak', 0)
        if win_streak >= 5:
            achievements.append("Hot Streak")
        elif win_streak >= 10:
            achievements.append("Unstoppable")
        
        # Add achievements to profile
        for achievement in achievements:
            if achievement not in profile.commendations_earned:
                profile.commendations_earned.append(achievement)
        
        return achievements
    
    def _generate_initial_callsign(self, user_id: str) -> str:
        """Generate initial callsign for new operator"""
        # Simple callsign generation - could be more sophisticated
        return f"RECRUIT-{user_id[:8].upper()}"
    
    def get_progression_summary(self, user_id: str) -> Dict:
        """Get comprehensive progression summary for operator"""
        profile = self.get_operator_profile(user_id)
        available_missions = self.get_available_missions(user_id)
        
        # Calculate progress to next rank
        current_rank_index = list(OperatorRank).index(profile.current_rank)
        next_rank = None
        next_rank_progress = None
        
        if current_rank_index < len(OperatorRank) - 1:
            next_rank = list(OperatorRank)[current_rank_index + 1]
            requirements = self.rank_requirements.get(next_rank, {})
            
            next_rank_progress = {
                'missions_progress': f"{profile.missions_completed}/{requirements.get('missions_required', 0)}",
                'success_rate_progress': f"{profile.mission_success_rate:.2f}/{requirements.get('success_rate_required', 0):.2f}",
                'experience_progress': f"{profile.total_experience}/{requirements.get('experience_required', 0)}"
            }
        
        return {
            'operator_profile': {
                'callsign': profile.callsign,
                'rank': profile.current_rank.value,
                'experience': profile.total_experience,
                'missions_completed': profile.missions_completed,
                'success_rate': profile.mission_success_rate,
                'story_phase': profile.story_phase.value
            },
            'capabilities': {
                'unlocked_mission_types': [t.value for t in profile.unlocked_mission_types],
                'unlocked_capabilities': [c.value for c in profile.unlocked_capabilities],
                'maximum_difficulty': profile.maximum_difficulty.value
            },
            'progression': {
                'next_rank': next_rank.value if next_rank else None,
                'next_rank_progress': next_rank_progress,
                'available_missions': [
                    {
                        'id': m.template_id,
                        'type': m.operation_type.value,
                        'difficulty': m.difficulty.value,
                        'duration': m.estimated_duration,
                        'rewards': m.experience_reward
                    }
                    for m in available_missions
                ],
                'recent_achievements': profile.commendations_earned[-5:] if profile.commendations_earned else []
            },
            'story_progress': {
                'current_phase': profile.story_phase.value,
                'elements_revealed': len(profile.story_elements_revealed),
                'wisdom_learned': len(profile.norman_wisdom_learned),
                'recent_revelations': profile.story_elements_revealed[-3:] if profile.story_elements_revealed else []
            }
        }

# Global instance
mission_progression_system = MissionProgressionSystem()

# Helper functions for easy integration
def get_available_missions_for_user(user_id: str) -> List[Dict]:
    """Get available missions formatted for UI"""
    templates = mission_progression_system.get_available_missions(user_id)
    return [
        {
            'mission_id': t.template_id,
            'operation_type': t.operation_type.value,
            'difficulty': t.difficulty.value,
            'estimated_duration': t.estimated_duration,
            'complexity_level': t.complexity_level,
            'risk_level': t.risk_level,
            'experience_reward': t.experience_reward,
            'story_arc': t.story_arc,
            'norman_connection': t.norman_connection
        }
        for t in templates
    ]

def process_mission_completion(user_id: str, mission_id: str, results: Dict) -> Dict:
    """Process mission completion and return progression updates"""
    return mission_progression_system.complete_mission(user_id, mission_id, results)

def get_user_progression_summary(user_id: str) -> Dict:
    """Get user's complete progression summary"""
    return mission_progression_system.get_progression_summary(user_id)

def check_mission_unlock(user_id: str, mission_id: str) -> bool:
    """Check if specific mission is unlocked for user"""
    available_missions = mission_progression_system.get_available_missions(user_id)
    return any(m.template_id == mission_id for m in available_missions)

# Testing
if __name__ == "__main__":
    # Test progression system
    test_user = "test_user_123"
    
    # Get initial state
    print("=== INITIAL PROGRESSION STATE ===")
    summary = get_user_progression_summary(test_user)
    print(f"Rank: {summary['operator_profile']['rank']}")
    print(f"Experience: {summary['operator_profile']['experience']}")
    print(f"Available Missions: {len(summary['progression']['available_missions'])}")
    
    # Test mission completion
    print("\n=== COMPLETING NORMANDY ECHO ===")
    completion_results = {
        'success': True,
        'risk_management_followed': True,
        'execution_quality': 0.8,
        'emotional_deviations': 0,
        'analysis_accuracy': 0.7
    }
    
    progression = process_mission_completion(test_user, 'normandy_echo', completion_results)
    print(f"Experience gained: {progression['experience_gained']}")
    print(f"Unlocks: {progression['unlocks']}")
    print(f"Rank advancement: {progression.get('rank_advancement', 'None')}")
    
    # Check updated state
    print("\n=== UPDATED PROGRESSION STATE ===")
    updated_summary = get_user_progression_summary(test_user)
    print(f"New Rank: {updated_summary['operator_profile']['rank']}")
    print(f"New Experience: {updated_summary['operator_profile']['experience']}")
    print(f"Available Missions: {len(updated_summary['progression']['available_missions'])}")
    
    print("\n=== MISSION PROGRESSION SYSTEM READY ===")