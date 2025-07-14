"""
BITTEN Tactical Mission Framework
The core system that disguises forex education as authentic military operations
Focus: Operation Normandy Echo - First Live Trade Mission
"""

import json
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

# Import existing systems
try:
    from .mission_briefing_generator import MissionBriefingGenerator, MissionType, UrgencyLevel
    from .norman_story_integration import norman_story_engine, StoryPhase
    from .education_system import EducationModule, LearningObjective
except ImportError:
    # Fallback imports for testing
    MissionBriefingGenerator = None
    norman_story_engine = None

class OperationType(Enum):
    """Types of tactical operations (disguised forex education levels)"""
    RECONNAISSANCE = "reconnaissance"     # Market analysis education
    INFILTRATION = "infiltration"        # Entry strategy training
    PRECISION_STRIKE = "precision_strike" # Risk management education
    EXTRACTION = "extraction"            # Exit strategy training
    SUPPORT_MISSION = "support_mission"   # Psychology and discipline
    JOINT_OPERATION = "joint_operation"   # Advanced multi-pair strategies

class MissionPhase(Enum):
    """Mission progression phases"""
    BRIEFING = "briefing"           # Pre-mission education
    PREPARATION = "preparation"     # Setup and planning
    EXECUTION = "execution"         # Active trading
    MONITORING = "monitoring"       # Position management
    EXTRACTION = "extraction"       # Exit management
    DEBRIEF = "debrief"            # Post-mission learning

class OperationalStatus(Enum):
    """Current operational status"""
    STANDBY = "standby"
    BRIEFING_ACTIVE = "briefing_active"
    MISSION_READY = "mission_ready"
    MISSION_ACTIVE = "mission_active"
    MISSION_COMPLETE = "mission_complete"
    MISSION_ABORTED = "mission_aborted"

@dataclass
class LearningObjectiveDisguised:
    """Learning objectives disguised as military objectives"""
    objective_id: str
    military_description: str       # What the user sees
    educational_content: str        # What they're actually learning
    completion_criteria: Dict       # How we measure understanding
    story_integration: Optional[str] # Norman's story connection
    bit_wisdom: Optional[str]       # Bit's guidance

@dataclass
class OperationNormandyEcho:
    """The foundational first live trade operation"""
    mission_id: str
    operator_callsign: str
    current_phase: MissionPhase
    status: OperationalStatus
    
    # Mission parameters (disguised trading education)
    target_symbol: str              # Currency pair
    operation_type: OperationType   # Learning focus
    intel_confidence: int           # TCS score equivalent
    risk_assessment: str            # Risk management lesson
    
    # Timing and urgency
    mission_start: int
    estimated_duration: int
    time_sensitive: bool
    extraction_deadline: Optional[int]
    
    # Educational objectives (hidden)
    learning_objectives: List[LearningObjectiveDisguised]
    knowledge_checkpoints: List[Dict]
    story_progression: Dict
    
    # Mission assets and support
    support_available: List[str]    # Available tools/indicators
    intel_sources: List[str]        # Information sources
    backup_protocols: List[str]     # Risk management options
    
    # Success metrics (disguised learning assessment)
    primary_objective: str          # Main learning goal
    secondary_objectives: List[str] # Additional learning points
    mission_success_criteria: Dict  # How we measure success
    
    # Narrative elements
    background_story: str
    norman_context: Optional[str]
    bit_presence: Optional[Dict]
    family_wisdom: Optional[str]

class TacticalMissionFramework:
    """Main framework for creating and managing tactical missions"""
    
    def __init__(self):
        self.mission_generator = MissionBriefingGenerator() if MissionBriefingGenerator else None
        self.active_operations: Dict[str, OperationNormandyEcho] = {}
        self.operation_templates = self._initialize_operation_templates()
        self.educational_disguises = self._initialize_educational_disguises()
        
    def _initialize_operation_templates(self) -> Dict[str, Dict]:
        """Initialize templates for different operation types"""
        return {
            'normandy_echo': {
                'operation_name': "Operation Normandy Echo",
                'mission_type': 'first_live_trade',
                'difficulty': 'beginner',
                'estimated_duration': 30,  # minutes
                'learning_focus': 'basic_execution',
                'story_arc': 'norman_first_success',
                'objectives': [
                    {
                        'military': "Establish forward position in hostile territory",
                        'educational': "Learn proper position sizing for first live trade",
                        'story': "Remember Norman's first careful step into live markets"
                    },
                    {
                        'military': "Maintain communication with base command",
                        'educational': "Understand the importance of following the trading plan",
                        'story': "Just like Norman learned to trust the system over emotion"
                    },
                    {
                        'military': "Execute tactical withdrawal if conditions deteriorate",
                        'educational': "Master the discipline of taking stop losses",
                        'story': "Grandmama's wisdom: 'Know when to fold, child'"
                    }
                ]
            },
            'sniper_precision': {
                'operation_name': "Operation Delta Sniper",
                'mission_type': 'precision_entry',
                'difficulty': 'intermediate',
                'estimated_duration': 45,
                'learning_focus': 'entry_timing',
                'story_arc': 'norman_patience_lesson',
                'objectives': [
                    {
                        'military': "Wait for optimal firing solution",
                        'educational': "Learn patience and precise entry timing",
                        'story': "Norman's breakthrough came from waiting for the perfect setup"
                    }
                ]
            }
        }
    
    def _initialize_educational_disguises(self) -> Dict[str, Dict]:
        """Map educational concepts to military terminology"""
        return {
            'risk_management': {
                'military_terms': [
                    "Force protection protocols",
                    "Asset preservation strategies", 
                    "Tactical withdrawal procedures",
                    "Damage limitation protocols"
                ],
                'story_context': "Norman learned the hard way - protect your capital like family"
            },
            'position_sizing': {
                'military_terms': [
                    "Deployment strength assessment",
                    "Resource allocation strategy",
                    "Force multiplication tactics",
                    "Strategic asset distribution"
                ],
                'story_context': "Mama's wisdom: 'Don't bet more than you can afford to lose'"
            },
            'entry_timing': {
                'military_terms': [
                    "Optimal strike window identification",
                    "Target acquisition protocols",
                    "Precision engagement timing",
                    "Tactical opportunity assessment"
                ],
                'story_context': "Patience, child - Grandmama's voice echoing through time"
            },
            'exit_strategy': {
                'military_terms': [
                    "Mission completion protocols",
                    "Strategic extraction procedures",
                    "Objective achievement confirmation",
                    "Tactical disengagement"
                ],
                'story_context': "Know when to come home - that's what kept Norman safe"
            },
            'psychology': {
                'military_terms': [
                    "Mental fortitude protocols",
                    "Stress response management",
                    "Decision clarity under pressure",
                    "Emotional regulation systems"
                ],
                'story_context': "Bit's calm presence during chaos - learn from your companion"
            }
        }
    
    def create_operation_normandy_echo(self, user_id: str, signal_data: Dict, user_tier: str = "RECRUIT") -> OperationNormandyEcho:
        """Create the foundational Operation Normandy Echo for first live trade"""
        
        # Generate unique mission ID
        mission_id = f"NORMANDY_ECHO_{int(time.time())}_{user_id[:8]}"
        
        # Get user's story context
        user_context = norman_story_engine.get_user_story_context(user_id) if norman_story_engine else None
        
        # Generate operator callsign with story integration
        base_callsign = self._generate_callsign(user_tier, signal_data.get('symbol', 'EURUSD'))
        operator_callsign = self._enhance_callsign_with_story(base_callsign, user_context)
        
        # Create learning objectives disguised as military objectives
        learning_objectives = self._create_normandy_echo_objectives(user_context, signal_data)
        
        # Generate mission background story
        background_story = self._create_normandy_echo_story(user_context, signal_data)
        
        # Create the operation
        operation = OperationNormandyEcho(
            mission_id=mission_id,
            operator_callsign=operator_callsign,
            current_phase=MissionPhase.BRIEFING,
            status=OperationalStatus.BRIEFING_ACTIVE,
            
            # Mission parameters
            target_symbol=signal_data.get('symbol', 'EURUSD'),
            operation_type=OperationType.RECONNAISSANCE,
            intel_confidence=signal_data.get('tcs_score', 75),
            risk_assessment=self._assess_mission_risk(signal_data),
            
            # Timing
            mission_start=int(time.time()),
            estimated_duration=30,  # 30 minutes for first mission
            time_sensitive=True,
            extraction_deadline=signal_data.get('expires_at'),
            
            # Educational content (hidden from user)
            learning_objectives=learning_objectives,
            knowledge_checkpoints=self._create_knowledge_checkpoints(),
            story_progression=self._create_story_progression(user_context),
            
            # Mission support
            support_available=self._get_available_support(user_tier),
            intel_sources=self._get_intel_sources(user_tier),
            backup_protocols=self._get_backup_protocols(user_tier),
            
            # Success criteria
            primary_objective="Successfully execute first live trade with proper risk management",
            secondary_objectives=[
                "Demonstrate position sizing discipline",
                "Show emotional control during trade execution", 
                "Follow stop loss protocols",
                "Complete post-mission analysis"
            ],
            mission_success_criteria=self._create_success_criteria(),
            
            # Narrative elements
            background_story=background_story,
            norman_context=self._get_norman_context_for_first_trade(user_context),
            bit_presence=self._get_bit_presence_for_mission(signal_data),
            family_wisdom=self._get_family_wisdom_for_first_trade(user_context)
        )
        
        # Store active operation
        self.active_operations[mission_id] = operation
        
        return operation
    
    def _generate_callsign(self, user_tier: str, symbol: str) -> str:
        """Generate appropriate callsign for the operator"""
        
        # Base callsigns by tier
        tier_callsigns = {
            'RECRUIT': ['ECHO-1', 'BRAVO-1', 'CHARLIE-1', 'DELTA-1'],
            'AUTHORIZED': ['ALPHA-6', 'BRAVO-6', 'CHARLIE-6', 'DELTA-6'],
            'ELITE': ['PHANTOM-1', 'GHOST-1', 'VIPER-1', 'EAGLE-1'],
            'ADMIN': ['OVERWATCH', 'COMMAND-1', 'ACTUAL', 'CONTROL']
        }
        
        # Symbol-specific prefixes
        symbol_prefixes = {
            'EURUSD': 'EURO',
            'GBPUSD': 'STERLING', 
            'USDJPY': 'PACIFIC',
            'USDCHF': 'ALPINE',
            'AUDUSD': 'SOUTHERN',
            'USDCAD': 'NORTHERN'
        }
        
        base = random.choice(tier_callsigns.get(user_tier, tier_callsigns['RECRUIT']))
        prefix = symbol_prefixes.get(symbol, 'TACTICAL')
        
        return f"{prefix}-{base}"
    
    def _enhance_callsign_with_story(self, base_callsign: str, user_context) -> str:
        """Enhance callsign with Norman's story elements"""
        if not user_context:
            return base_callsign
            
        story_enhancements = {
            StoryPhase.EARLY_STRUGGLE: [" [LEARNING]", " [FIRST STEPS]", " [DELTA ROOKIE]"],
            StoryPhase.AWAKENING: [" [RISING]", " [BREAKTHROUGH]", " [DELTA DAWN]"],
            StoryPhase.DISCIPLINE: [" [STEADY]", " [DISCIPLINED]", " [DELTA STRONG]"],
            StoryPhase.MASTERY: [" [EXPERT]", " [MASTER]", " [DELTA PRIDE]"],
            StoryPhase.LEGACY: [" [LEGEND]", " [MENTOR]", " [DELTA LEGACY]"]
        }
        
        if random.random() < 0.3:  # 30% chance for story enhancement
            enhancements = story_enhancements.get(user_context.current_phase, [])
            if enhancements:
                return base_callsign + random.choice(enhancements)
        
        return base_callsign
    
    def _create_normandy_echo_objectives(self, user_context, signal_data: Dict) -> List[LearningObjectiveDisguised]:
        """Create the learning objectives for Operation Normandy Echo"""
        
        objectives = [
            LearningObjectiveDisguised(
                objective_id="normandy_alpha",
                military_description="🎯 PRIMARY: Establish operational foothold in target zone",
                educational_content="Learn to execute your first live trade with confidence",
                completion_criteria={
                    'trade_executed': True,
                    'position_size_appropriate': True,
                    'stop_loss_set': True
                },
                story_integration="Norman's first careful step into live markets - courage with caution",
                bit_wisdom="*Bit stretches confidently - he senses opportunity*"
            ),
            LearningObjectiveDisguised(
                objective_id="normandy_bravo", 
                military_description="🛡️ SECONDARY: Maintain defensive protocols throughout operation",
                educational_content="Master risk management fundamentals for live trading",
                completion_criteria={
                    'risk_percentage_correct': True,
                    'stop_loss_respected': True,
                    'no_position_sizing_errors': True
                },
                story_integration="Mama's voice: 'Protect what you have before reaching for more'",
                bit_wisdom="*Bit sits alert but calm - vigilance with patience*"
            ),
            LearningObjectiveDisguised(
                objective_id="normandy_charlie",
                military_description="📡 SUPPORT: Maintain communication discipline with command",
                educational_content="Learn to follow your trading plan without emotional deviation",
                completion_criteria={
                    'followed_entry_signal': True,
                    'no_premature_exits': True,
                    'no_position_additions': True
                },
                story_integration="Norman learned to trust the system over his emotions",
                bit_wisdom="*Bit's steady breathing reminds you to stay calm*"
            ),
            LearningObjectiveDisguised(
                objective_id="normandy_delta",
                military_description="🎖️ BONUS: Execute flawless extraction upon objective completion",
                educational_content="Master the art of taking profits and cutting losses with discipline",
                completion_criteria={
                    'target_hit_or_stop_triggered': True,
                    'no_hesitation_on_exit': True,
                    'proper_post_trade_analysis': True
                },
                story_integration="Grandmama's wisdom: 'Know when to come home, child'",
                bit_wisdom="*Bit knows when to stop hunting - timing is everything*"
            )
        ]
        
        return objectives
    
    def _create_normandy_echo_story(self, user_context, signal_data: Dict) -> str:
        """Create the compelling background story for Operation Normandy Echo"""
        
        symbol = signal_data.get('symbol', 'EURUSD')
        direction = signal_data.get('direction', 'BUY').upper()
        
        # Create market-specific story elements
        symbol_stories = {
            'EURUSD': {
                'location': "the European markets",
                'context': "Continental intelligence suggests movement",
                'terrain': "familiar ground for first operations"
            },
            'GBPUSD': {
                'location': "British territories",
                'context': "Sterling intel indicates opportunity",
                'terrain': "volatile but predictable landscape"
            },
            'USDJPY': {
                'location': "Pacific theater operations",
                'context': "Asian session intel shows movement",
                'terrain': "precise timing required in these waters"
            }
        }
        
        story_data = symbol_stories.get(symbol, symbol_stories['EURUSD'])
        
        base_story = f"""
🎯 **OPERATION NORMANDY ECHO - CLASSIFIED BRIEFING**

**MISSION BACKGROUND:**
Intelligence assets have identified a high-probability tactical opportunity in {story_data['location']}. 
{story_data['context']}, requiring immediate deployment of our newest operational asset - YOU.

**STRATEGIC CONTEXT:**
This is your first live deployment, operator. Every legend started with their first mission. 
Norman himself stood where you stand now, heart pounding, ready to prove himself worthy of the family legacy.

**OPERATIONAL THEATER:**
Target: {symbol} - {story_data['terrain']}
Action: {direction} positioning
Intel Confidence: {signal_data.get('tcs_score', 75)}%

**THE NORMANDY ECHO PROTOCOL:**
Named after the historic landings that changed everything. This isn't just about the mission - 
it's about proving you belong here. Every successful trader remembers their first live trade.
Make Norman proud.

**MISSION PHILOSOPHY:**
"*Courage isn't the absence of fear - it's acting despite it.*" - Norman's journal, Day 1

Remember: Bit is with you. The ancestors watch. The family believes.
Your training prepared you for this moment.

**COMMAND GUIDANCE:**
- Trust your training
- Follow protocols precisely  
- Remember why you're here
- Come home safe
        """
        
        # Add user-specific story elements based on their phase
        if user_context:
            phase_additions = {
                StoryPhase.EARLY_STRUGGLE: "\n\n*Every master was once a beginner. Today, your journey truly begins.*",
                StoryPhase.AWAKENING: "\n\n*You've learned the basics. Now prove you can apply them under pressure.*",
                StoryPhase.DISCIPLINE: "\n\n*Your discipline has been tested. Show the market your steel.*",
                StoryPhase.MASTERY: "\n\n*From student to operator. Lead by example.*",
                StoryPhase.LEGACY: "\n\n*The next generation watches. Show them how legends are made.*"
            }
            base_story += phase_additions.get(user_context.current_phase, "")
        
        return base_story.strip()
    
    def _create_knowledge_checkpoints(self) -> List[Dict]:
        """Create disguised education checkpoints throughout the mission"""
        return [
            {
                'checkpoint_id': 'pre_deployment',
                'phase': MissionPhase.PREPARATION,
                'military_description': "Pre-deployment equipment check",
                'educational_check': "Confirm understanding of position sizing",
                'questions': [
                    {
                        'prompt': "Confirm your deployment strength (position size)",
                        'validation': "position_size_within_risk_limits",
                        'failure_response': "Command recommends lighter deployment for first mission"
                    }
                ]
            },
            {
                'checkpoint_id': 'insertion_point',
                'phase': MissionPhase.EXECUTION,
                'military_description': "Confirm insertion coordinates",
                'educational_check': "Verify entry price and stop loss understanding",
                'questions': [
                    {
                        'prompt': "Verify your entry coordinates and extraction point",
                        'validation': "entry_and_stop_loss_confirmed",
                        'failure_response': "Hold position - verify target coordinates with command"
                    }
                ]
            },
            {
                'checkpoint_id': 'mission_status',
                'phase': MissionPhase.MONITORING,
                'military_description': "Mission status report",
                'educational_check': "Assess emotional state and plan adherence",
                'questions': [
                    {
                        'prompt': "Report operational status and any protocol deviations",
                        'validation': "emotional_control_maintained",
                        'failure_response': "Remember your training - stick to the plan"
                    }
                ]
            }
        ]
    
    def _create_story_progression(self, user_context) -> Dict:
        """Create story progression elements that unlock during mission"""
        return {
            'phase_unlocks': {
                MissionPhase.BRIEFING: {
                    'story_element': "Norman's first mission briefing",
                    'wisdom': "Mama's blessing before his first trade",
                    'bit_moment': "Bit settling beside the computer for the first time"
                },
                MissionPhase.EXECUTION: {
                    'story_element': "The moment Norman clicked 'Buy' for the first time",
                    'wisdom': "Grandmama's voice: 'Courage, child'",
                    'bit_moment': "Bit's encouraging purr as the trade executes"
                },
                MissionPhase.DEBRIEF: {
                    'story_element': "Norman's reflection on his first live trade",
                    'wisdom': "What he learned that changed everything",
                    'bit_moment': "Bit's satisfied stretch after a job well done"
                }
            },
            'success_revelations': [
                "The pride in Norman's eyes when he realized he could do this",
                "How that first successful trade funded his mother's medicine",
                "Why Bit started appearing during every important decision",
                "The moment Norman knew he'd found his calling"
            ],
            'struggle_support': [
                "Norman's first loss and how he recovered",
                "Grandmama's wisdom that saved his account",
                "Why every trader needs their 'Bit' - a source of calm",
                "The family strength that carried him through doubt"
            ]
        }
    
    def _assess_mission_risk(self, signal_data: Dict) -> str:
        """Assess and describe mission risk in military terms"""
        tcs_score = signal_data.get('tcs_score', 75)
        volatility = signal_data.get('volatility', 'NORMAL')
        
        if tcs_score >= 85 and volatility == 'LOW':
            return "🟢 LOW RISK - Optimal conditions for first deployment"
        elif tcs_score >= 75 and volatility in ['LOW', 'NORMAL']:
            return "🟡 MODERATE RISK - Standard operational parameters"
        elif tcs_score >= 65:
            return "🟠 ELEVATED RISK - Extra caution required, perfect for learning"
        else:
            return "🔴 HIGH RISK - Command recommends delay for inexperienced operators"
    
    def _get_available_support(self, user_tier: str) -> List[str]:
        """Get available support based on user tier"""
        base_support = [
            "📡 Real-time intel updates",
            "🎯 Target confirmation system", 
            "⚠️ Risk monitoring protocols",
            "🛡️ Automatic defensive measures"
        ]
        
        tier_support = {
            'AUTHORIZED': ["📊 Enhanced technical intelligence"],
            'ELITE': ["🔍 Advanced pattern recognition", "⚡ Priority signal access"],
            'ADMIN': ["🎮 Full system override capabilities", "👑 Command authority"]
        }
        
        return base_support + tier_support.get(user_tier, [])
    
    def _get_intel_sources(self, user_tier: str) -> List[str]:
        """Get available intelligence sources"""
        return [
            "🌐 Market sentiment analysis",
            "📈 Technical pattern recognition",
            "⏰ Time-based probability models",
            "🔄 Correlation intelligence",
            "📰 Economic event monitoring"
        ]
    
    def _get_backup_protocols(self, user_tier: str) -> List[str]:
        """Get available backup protocols"""
        return [
            "🚨 Emergency stop protocols",
            "📞 Direct command communication",
            "🔄 Position modification procedures",
            "⚡ Rapid extraction capabilities",
            "🛡️ Account protection measures"
        ]
    
    def _create_success_criteria(self) -> Dict:
        """Create mission success criteria"""
        return {
            'mission_complete': {
                'trade_executed': True,
                'risk_management_followed': True,
                'emotional_control_maintained': True,
                'exit_strategy_executed': True
            },
            'learning_objectives_met': {
                'position_sizing_correct': True,
                'stop_loss_understanding': True,
                'plan_adherence': True,
                'post_analysis_completed': True
            },
            'story_progression': {
                'confidence_gained': True,
                'milestone_recognized': True,
                'wisdom_internalized': True,
                'ready_for_next_phase': True
            }
        }
    
    def _get_norman_context_for_first_trade(self, user_context) -> Optional[str]:
        """Get Norman's story context for first trade"""
        contexts = [
            "Norman's hands shook on his first live trade too - courage isn't fearlessness",
            "The moment Norman proved to himself he could do this - just like you will",
            "Every dollar Norman risked was a dollar earned through sacrifice - honor that",
            "Norman's mother watched from heaven as he clicked 'execute' - family legacy continues"
        ]
        return random.choice(contexts)
    
    def _get_bit_presence_for_mission(self, signal_data: Dict) -> Optional[Dict]:
        """Get Bit's presence and wisdom for the mission"""
        confidence = signal_data.get('tcs_score', 75)
        
        if confidence >= 80:
            return {
                'mood': 'confident',
                'message': "*Bit stretches and settles in - he senses a good hunt ahead*",
                'visual': 'cat_confident_stretch',
                'audio': 'encouraging_purr'
            }
        elif confidence >= 70:
            return {
                'mood': 'alert',
                'message': "*Bit sits tall and alert - ready for whatever comes*", 
                'visual': 'cat_alert_sitting',
                'audio': 'steady_breathing'
            }
        else:
            return {
                'mood': 'cautious',
                'message': "*Bit's ears twitch - proceed with extra caution*",
                'visual': 'cat_ears_alert',
                'audio': 'concerned_chirp'
            }
    
    def _get_family_wisdom_for_first_trade(self, user_context) -> Optional[str]:
        """Get appropriate family wisdom for first trade"""
        wisdom_options = [
            "Grandmama's blessing: 'Be brave but not foolish, child'",
            "Mama's strength: 'You've got this - we believe in you'", 
            "Delta wisdom: 'The river flows around obstacles, not through them'",
            "Family motto: 'Steady hands, clear mind, warm heart'"
        ]
        return random.choice(wisdom_options)
    
    def generate_pre_mission_briefing(self, operation: OperationNormandyEcho) -> Dict:
        """Generate comprehensive pre-mission briefing (disguised education)"""
        
        briefing = {
            'operation_header': {
                'title': f"🎯 {operation.operation_id} - PRE-MISSION BRIEFING",
                'classification': "FOR OPERATIONAL EYES ONLY",
                'operator': operation.operator_callsign,
                'mission_type': operation.operation_type.value.upper(),
                'urgency': "IMMEDIATE DEPLOYMENT REQUIRED"
            },
            
            'situation_assessment': {
                'target_zone': f"Market Sector: {operation.target_symbol}",
                'intel_confidence': f"{operation.intel_confidence}% verified",
                'environmental_conditions': operation.risk_assessment,
                'time_window': f"Optimal window: {operation.estimated_duration} minutes",
                'extraction_deadline': operation.extraction_deadline
            },
            
            'mission_objectives': [
                {
                    'designation': obj.objective_id.upper(),
                    'description': obj.military_description,
                    'success_criteria': obj.completion_criteria,
                    'special_notes': obj.story_integration
                }
                for obj in operation.learning_objectives
            ],
            
            'tactical_preparation': {
                'equipment_check': [
                    "✅ Trading platform operational",
                    "✅ Risk management protocols loaded",
                    "✅ Communication channels established",
                    "✅ Emergency procedures confirmed"
                ],
                'mental_preparation': [
                    "🧠 Review operational parameters",
                    "💪 Confirm psychological readiness",
                    "🎯 Visualize successful execution",
                    "🛡️ Prepare for contingencies"
                ],
                'support_assets': operation.support_available
            },
            
            'intelligence_brief': {
                'market_analysis': operation.intel_sources,
                'risk_factors': [
                    "Market volatility assessment",
                    "Economic event proximity",
                    "Correlation risk evaluation",
                    "Liquidity condition analysis"
                ],
                'opportunity_window': "High probability setup identified"
            },
            
            'story_context': {
                'historical_reference': operation.background_story,
                'personal_significance': operation.norman_context,
                'companion_status': operation.bit_presence,
                'ancestral_wisdom': operation.family_wisdom
            },
            
            'final_verification': {
                'pre_flight_checklist': [
                    "🔍 Confirm position size calculation",
                    "🎯 Verify entry and exit points", 
                    "⚠️ Double-check stop loss placement",
                    "💰 Confirm risk percentage compliance",
                    "📱 Test communication systems"
                ],
                'go_no_go_criteria': [
                    "Mental state: Calm and focused",
                    "Risk parameters: Within acceptable limits",
                    "Market conditions: Suitable for deployment",
                    "Support systems: All operational"
                ]
            },
            
            'authorization': {
                'command_approval': "APPROVED FOR IMMEDIATE DEPLOYMENT",
                'operator_acknowledgment': "AWAITING OPERATOR CONFIRMATION",
                'mission_code': operation.mission_id,
                'timestamp': int(time.time())
            }
        }
        
        return briefing
    
    def generate_during_mission_guidance(self, operation: OperationNormandyEcho, current_phase: MissionPhase) -> Dict:
        """Generate real-time mission guidance (disguised trading support)"""
        
        guidance = {
            'mission_status': {
                'current_phase': current_phase.value.upper(),
                'operator': operation.operator_callsign,
                'mission_timer': self._calculate_mission_time(operation),
                'next_checkpoint': self._get_next_checkpoint(operation, current_phase)
            },
            
            'tactical_updates': self._get_phase_specific_guidance(current_phase),
            
            'real_time_support': {
                'bit_status': self._get_bit_current_mood(operation),
                'family_encouragement': self._get_contextual_encouragement(current_phase),
                'norman_wisdom': self._get_phase_appropriate_wisdom(current_phase)
            },
            
            'critical_reminders': self._get_phase_reminders(current_phase),
            
            'communication_channel': {
                'status': "CHANNEL OPEN",
                'emergency_support': "Type 'HELP' for immediate assistance",
                'command_frequency': "Monitoring all operational channels"
            }
        }
        
        return guidance
    
    def generate_post_mission_debrief(self, operation: OperationNormandyEcho, mission_results: Dict) -> Dict:
        """Generate comprehensive post-mission debrief (learning extraction)"""
        
        # Analyze mission performance
        performance_analysis = self._analyze_mission_performance(operation, mission_results)
        
        # Extract learning points
        learning_extraction = self._extract_learning_points(operation, mission_results)
        
        # Generate story progression
        story_progression = self._generate_story_progression_update(operation, mission_results)
        
        debrief = {
            'mission_summary': {
                'operation_id': operation.mission_id,
                'operator': operation.operator_callsign,
                'mission_status': mission_results.get('final_status', 'COMPLETED'),
                'duration': mission_results.get('total_duration', 0),
                'timestamp': int(time.time())
            },
            
            'performance_assessment': performance_analysis,
            
            'objectives_review': [
                {
                    'objective': obj.military_description,
                    'status': 'COMPLETED' if self._objective_completed(obj, mission_results) else 'PARTIAL',
                    'learning_extracted': obj.educational_content,
                    'story_connection': obj.story_integration
                }
                for obj in operation.learning_objectives
            ],
            
            'tactical_analysis': {
                'what_went_well': learning_extraction['successes'],
                'areas_for_improvement': learning_extraction['improvements'],
                'unexpected_outcomes': learning_extraction['surprises'],
                'next_mission_preparation': learning_extraction['next_steps']
            },
            
            'story_revelation': {
                'norman_parallel': story_progression['norman_connection'],
                'wisdom_unlocked': story_progression['wisdom_gained'],
                'bit_observation': story_progression['bit_insight'],
                'family_pride': story_progression['family_connection']
            },
            
            'progression_update': {
                'experience_gained': self._calculate_experience_gained(mission_results),
                'new_capabilities_unlocked': self._check_capability_unlocks(operation, mission_results),
                'next_operation_availability': self._determine_next_operations(performance_analysis),
                'story_phase_progress': self._check_story_phase_progression(operation, mission_results)
            },
            
            'personal_reflection': {
                'operator_notes': "Space for personal mission reflection",
                'emotional_state': "Post-mission psychological assessment",
                'confidence_level': "Operator confidence evaluation",
                'readiness_for_next': "Assessment of readiness for next operation"
            },
            
            'command_recognition': {
                'commendations': self._generate_commendations(performance_analysis),
                'milestone_achievements': self._check_milestone_achievements(operation, mission_results),
                'special_recognition': self._check_special_recognition(operation, mission_results)
            }
        }
        
        return debrief
    
    def _calculate_mission_time(self, operation: OperationNormandyEcho) -> str:
        """Calculate elapsed mission time"""
        elapsed = int(time.time()) - operation.mission_start
        minutes = elapsed // 60
        seconds = elapsed % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def _get_next_checkpoint(self, operation: OperationNormandyEcho, current_phase: MissionPhase) -> str:
        """Get next checkpoint based on current phase"""
        checkpoints = {
            MissionPhase.BRIEFING: "Pre-deployment verification",
            MissionPhase.PREPARATION: "Mission execution authorization",
            MissionPhase.EXECUTION: "Position status confirmation", 
            MissionPhase.MONITORING: "Extraction readiness assessment",
            MissionPhase.EXTRACTION: "Mission completion verification",
            MissionPhase.DEBRIEF: "Final assessment complete"
        }
        return checkpoints.get(current_phase, "Status update pending")
    
    def _get_phase_specific_guidance(self, phase: MissionPhase) -> Dict:
        """Get specific guidance for current mission phase"""
        guidance_map = {
            MissionPhase.PREPARATION: {
                'focus': "Confirm all parameters before execution",
                'actions': ["Verify position size", "Check entry price", "Confirm stop loss"],
                'mindset': "Calm preparation prevents poor performance"
            },
            MissionPhase.EXECUTION: {
                'focus': "Execute according to plan with precision",
                'actions': ["Click execute when ready", "Monitor for confirmation", "Stay calm"],
                'mindset': "Trust your training, trust the plan"
            },
            MissionPhase.MONITORING: {
                'focus': "Maintain discipline while position develops",
                'actions': ["Watch for exit signals", "Resist premature exits", "Stay patient"],
                'mindset': "Patience and discipline win the day"
            }
        }
        return guidance_map.get(phase, {})
    
    def _get_bit_current_mood(self, operation: OperationNormandyEcho) -> str:
        """Get Bit's current mood and message"""
        if operation.bit_presence:
            return operation.bit_presence.get('message', "*Bit watches calmly*")
        return "*Bit settles nearby, offering silent support*"
    
    def _get_contextual_encouragement(self, phase: MissionPhase) -> str:
        """Get contextual encouragement for current phase"""
        encouragements = {
            MissionPhase.PREPARATION: "The family believes in you - trust your preparation",
            MissionPhase.EXECUTION: "Norman's courage flows through you - you've got this",
            MissionPhase.MONITORING: "Grandmama's patience guides you - let it develop",
            MissionPhase.EXTRACTION: "Mama's wisdom protects you - secure your gains"
        }
        return encouragements.get(phase, "You carry the strength of generations")
    
    def _get_phase_appropriate_wisdom(self, phase: MissionPhase) -> str:
        """Get Norman's wisdom appropriate for current phase"""
        wisdom_map = {
            MissionPhase.PREPARATION: "Norman always said: 'Measure twice, cut once'",
            MissionPhase.EXECUTION: "Norman's journal: 'Courage is action despite fear'",
            MissionPhase.MONITORING: "Norman learned: 'Good things come to those who wait'",
            MissionPhase.EXTRACTION: "Norman knew: 'Greed kills more traders than fear'"
        }
        return wisdom_map.get(phase, "Norman's spirit guides every decision")
    
    def _get_phase_reminders(self, phase: MissionPhase) -> List[str]:
        """Get critical reminders for current phase"""
        reminders_map = {
            MissionPhase.PREPARATION: [
                "🎯 Confirm entry price alignment",
                "🛡️ Verify stop loss placement",
                "💰 Double-check position size"
            ],
            MissionPhase.EXECUTION: [
                "⚡ Execute with confidence",
                "📱 Monitor for confirmation",
                "🧠 Stay emotionally controlled"
            ],
            MissionPhase.MONITORING: [
                "👁️ Watch price action calmly",
                "⏰ Be patient with development",
                "🚫 Resist impulsive modifications"
            ]
        }
        return reminders_map.get(phase, ["Stay focused", "Trust the process"])
    
    def _analyze_mission_performance(self, operation: OperationNormandyEcho, results: Dict) -> Dict:
        """Analyze overall mission performance"""
        return {
            'overall_grade': self._calculate_overall_grade(results),
            'objective_completion': self._calculate_objective_completion(operation, results),
            'risk_management_score': self._score_risk_management(results),
            'execution_quality': self._score_execution_quality(results),
            'emotional_control': self._score_emotional_control(results),
            'learning_demonstration': self._score_learning_demonstration(results)
        }
    
    def _extract_learning_points(self, operation: OperationNormandyEcho, results: Dict) -> Dict:
        """Extract key learning points from mission"""
        return {
            'successes': [
                "Successful trade execution under pressure",
                "Proper risk management maintained",
                "Plan adherence demonstrated"
            ],
            'improvements': [
                "Consider entry timing optimization",
                "Monitor emotional responses during drawdown",
                "Practice position sizing calculations"
            ],
            'surprises': [
                "Market moved faster than expected",
                "Emotional response was stronger than anticipated",
                "Stop loss placement proved optimal"
            ],
            'next_steps': [
                "Practice with similar setups",
                "Study market timing patterns",
                "Develop emotional regulation techniques"
            ]
        }
    
    def _generate_story_progression_update(self, operation: OperationNormandyEcho, results: Dict) -> Dict:
        """Generate story progression based on mission results"""
        return {
            'norman_connection': "This trade mirrors Norman's breakthrough moment - the first time he proved to himself he could do this",
            'wisdom_gained': "Every successful trader remembers their first live trade. You've crossed that threshold.",
            'bit_insight': "*Bit purrs with satisfaction - he witnessed another trader find their courage*",
            'family_connection': "Mama's sacrifice, Grandmama's wisdom, Norman's example - they all led to this moment"
        }
    
    def _calculate_overall_grade(self, results: Dict) -> str:
        """Calculate overall mission grade"""
        score = results.get('performance_score', 75)
        if score >= 90:
            return "EXCEPTIONAL (A+)"
        elif score >= 80:
            return "OUTSTANDING (A)"
        elif score >= 70:
            return "PROFICIENT (B)"
        elif score >= 60:
            return "ADEQUATE (C)"
        else:
            return "NEEDS IMPROVEMENT (D)"
    
    def _objective_completed(self, objective: LearningObjectiveDisguised, results: Dict) -> bool:
        """Check if specific objective was completed"""
        criteria = objective.completion_criteria
        return all(results.get(key, False) for key in criteria.keys())
    
    def get_active_operation(self, mission_id: str) -> Optional[OperationNormandyEcho]:
        """Get active operation by mission ID"""
        return self.active_operations.get(mission_id)
    
    def update_operation_phase(self, mission_id: str, new_phase: MissionPhase) -> bool:
        """Update operation phase"""
        if mission_id in self.active_operations:
            self.active_operations[mission_id].current_phase = new_phase
            return True
        return False
    
    def complete_operation(self, mission_id: str, results: Dict) -> Dict:
        """Complete operation and generate final debrief"""
        operation = self.active_operations.get(mission_id)
        if not operation:
            return {'error': 'Operation not found'}
        
        operation.status = OperationalStatus.MISSION_COMPLETE
        debrief = self.generate_post_mission_debrief(operation, results)
        
        # Archive the operation
        self.active_operations.pop(mission_id, None)
        
        return debrief

# Global instance
tactical_mission_framework = TacticalMissionFramework()

# Main functions for easy integration
def create_first_live_trade_mission(user_id: str, signal_data: Dict, user_tier: str = "RECRUIT") -> OperationNormandyEcho:
    """Create Operation Normandy Echo for user's first live trade"""
    return tactical_mission_framework.create_operation_normandy_echo(user_id, signal_data, user_tier)

def get_mission_briefing(mission_id: str) -> Optional[Dict]:
    """Get pre-mission briefing for operation"""
    operation = tactical_mission_framework.get_active_operation(mission_id)
    if operation:
        return tactical_mission_framework.generate_pre_mission_briefing(operation)
    return None

def get_mission_guidance(mission_id: str, current_phase: MissionPhase) -> Optional[Dict]:
    """Get real-time mission guidance"""
    operation = tactical_mission_framework.get_active_operation(mission_id)
    if operation:
        return tactical_mission_framework.generate_during_mission_guidance(operation, current_phase)
    return None

def complete_mission(mission_id: str, results: Dict) -> Dict:
    """Complete mission and get debrief"""
    return tactical_mission_framework.complete_operation(mission_id, results)

# Testing
if __name__ == "__main__":
    # Test Operation Normandy Echo creation
    test_signal = {
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.0850,
        'stop_loss': 1.0820,
        'take_profit': 1.0890,
        'tcs_score': 82,
        'expires_at': int(time.time()) + 1800  # 30 minutes
    }
    
    # Create first live trade mission
    operation = create_first_live_trade_mission("test_user_123", test_signal, "RECRUIT")
    
    print("=== OPERATION NORMANDY ECHO CREATED ===")
    print(f"Mission ID: {operation.mission_id}")
    print(f"Operator: {operation.operator_callsign}")
    print(f"Target: {operation.target_symbol}")
    print(f"Phase: {operation.current_phase.value}")
    
    # Get pre-mission briefing
    briefing = get_mission_briefing(operation.mission_id)
    if briefing:
        print("\n=== PRE-MISSION BRIEFING GENERATED ===")
        print(f"Title: {briefing['operation_header']['title']}")
        print(f"Objectives: {len(briefing['mission_objectives'])}")
    
    # Test mission guidance
    guidance = get_mission_guidance(operation.mission_id, MissionPhase.EXECUTION)
    if guidance:
        print("\n=== MISSION GUIDANCE GENERATED ===")
        print(f"Phase: {guidance['mission_status']['current_phase']}")
        print(f"Bit Status: {guidance['real_time_support']['bit_status']}")
    
    print("\n=== TACTICAL MISSION FRAMEWORK READY ===")