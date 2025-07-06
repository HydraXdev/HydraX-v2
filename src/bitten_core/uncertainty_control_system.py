"""
BITTEN Uncertainty & Control Interplay System
Psychological trigger system that manipulates user sense of control and uncertainty

Core Components:
1. Bit Mode - Binary choice confirmation system
2. Stealth Mode - Hidden algorithm variations  
3. Gemini System - Competitor AI for control tension
4. Uncertainty Injection - Random decision points
"""

import random
import secrets
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class ControlMode(Enum):
    """Control modes for psychological manipulation"""
    FULL_CONTROL = "full_control"      # User has complete control
    BIT_MODE = "bit_mode"              # Binary YES/NO confirmations
    STEALTH_MODE = "stealth_mode"      # Hidden algorithm variations
    GEMINI_MODE = "gemini_mode"        # AI competitor tension
    CHAOS_MODE = "chaos_mode"          # Maximum uncertainty

class UncertaintyLevel(Enum):
    """Levels of uncertainty injection"""
    MINIMAL = "minimal"      # 5% uncertainty
    LOW = "low"              # 15% uncertainty  
    MEDIUM = "medium"        # 30% uncertainty
    HIGH = "high"            # 50% uncertainty
    EXTREME = "extreme"      # 75% uncertainty

@dataclass
class BitModeDecision:
    """Binary decision point in Bit Mode"""
    decision_id: str
    question: str
    context: str
    user_choice: Optional[bool] = None
    timestamp: Optional[datetime] = None
    psychological_weight: float = 1.0
    consequences: Dict[str, Any] = None

@dataclass
class GeminiComparison:
    """Gemini AI comparison for control tension"""
    scenario: str
    user_action: str
    gemini_action: str
    gemini_confidence: float
    psychological_impact: str
    timing: datetime

class UncertaintyControlSystem:
    """
    Master system for psychological control manipulation
    
    Creates tension between user control and system uncertainty
    to maximize psychological engagement and decision anxiety
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.state_file = os.path.join(data_dir, "uncertainty_control_state.json")
        self._ensure_data_dir()
        
        # Load state
        self.state = self._load_state()
        
        # Current mode
        self.current_mode = ControlMode(self.state.get('current_mode', 'full_control'))
        self.uncertainty_level = UncertaintyLevel(self.state.get('uncertainty_level', 'minimal'))
        
        # Decision tracking
        self.pending_decisions: List[BitModeDecision] = []
        self.decision_history: List[Dict] = []
        self.gemini_comparisons: List[GeminiComparison] = []
        
        # User psychology profile
        self.user_control_preference = self.state.get('user_control_preference', 0.5)  # 0=chaos, 1=control
        self.decision_anxiety_level = self.state.get('decision_anxiety_level', 0.5)
        self.gemini_competitive_drive = self.state.get('gemini_competitive_drive', 0.5)
        
        # Configuration
        self.config = {
            'bit_mode_frequency': 0.3,        # 30% of actions require confirmation
            'stealth_variation_chance': 0.2,   # 20% chance of algorithm variation
            'gemini_appearance_rate': 0.15,    # 15% chance Gemini appears
            'uncertainty_escalation': True,    # Gradually increase uncertainty
            'psychological_learning': True,    # Learn user preferences
            'max_pending_decisions': 5,        # Limit decision queue
            'decision_timeout_minutes': 10,    # Auto-timeout for decisions
        }
        
        # Gemini personality system
        self.gemini_personality = {
            'confidence_level': 0.85,
            'aggression': 0.7,
            'precision': 0.9,
            'risk_tolerance': 0.6,
            'patience': 0.3,
            'psychological_warfare': 0.8
        }
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _load_state(self) -> Dict:
        """Load uncertainty control state"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            'current_mode': 'full_control',
            'uncertainty_level': 'minimal',
            'user_control_preference': 0.5,
            'decision_anxiety_level': 0.5,
            'gemini_competitive_drive': 0.5,
            'total_decisions': 0,
            'correct_decisions': 0,
            'gemini_wins': 0,
            'user_wins': 0
        }
    
    def _save_state(self):
        """Save uncertainty control state"""
        try:
            self.state.update({
                'current_mode': self.current_mode.value,
                'uncertainty_level': self.uncertainty_level.value,
                'user_control_preference': self.user_control_preference,
                'decision_anxiety_level': self.decision_anxiety_level,
                'gemini_competitive_drive': self.gemini_competitive_drive,
                'last_updated': datetime.now().isoformat()
            })
            
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)
        except Exception as e:
            print(f"Failed to save uncertainty control state: {e}")
    
    def set_control_mode(self, mode: ControlMode, user_id: int = None) -> Dict[str, Any]:
        """Set psychological control mode"""
        old_mode = self.current_mode
        self.current_mode = mode
        
        # Update psychological profile based on mode choice
        if mode == ControlMode.FULL_CONTROL:
            self.user_control_preference = min(1.0, self.user_control_preference + 0.1)
        elif mode == ControlMode.CHAOS_MODE:
            self.user_control_preference = max(0.0, self.user_control_preference - 0.1)
        
        self._save_state()
        
        # Generate psychological response
        response = self._generate_mode_change_response(old_mode, mode)
        
        return {
            'success': True,
            'old_mode': old_mode.value,
            'new_mode': mode.value,
            'response': response,
            'psychological_profile': self._get_psychological_profile()
        }
    
    def activate_bit_mode(self, context: str, question: str = None) -> BitModeDecision:
        """Activate binary decision mode"""
        if not question:
            question = self._generate_bit_mode_question(context)
        
        decision = BitModeDecision(
            decision_id=f"bit_{int(time.time())}_{secrets.randbelow(1000)}",
            question=question,
            context=context,
            timestamp=datetime.now(),
            psychological_weight=self._calculate_psychological_weight(context),
            consequences=self._generate_decision_consequences(context)
        )
        
        self.pending_decisions.append(decision)
        self._cleanup_old_decisions()
        
        return decision
    
    def process_bit_decision(self, decision_id: str, choice: bool, user_id: int = None) -> Dict[str, Any]:
        """Process user's binary decision"""
        decision = None
        for d in self.pending_decisions:
            if d.decision_id == decision_id:
                decision = d
                break
        
        if not decision:
            return {'success': False, 'error': 'Decision not found or expired'}
        
        # Record choice
        decision.user_choice = choice
        
        # Update psychological profile
        self._update_decision_psychology(decision, choice)
        
        # Generate consequences
        consequences = self._execute_decision_consequences(decision, choice)
        
        # Move to history
        self.pending_decisions.remove(decision)
        self.decision_history.append({
            'decision_id': decision_id,
            'choice': choice,
            'timestamp': datetime.now().isoformat(),
            'psychological_weight': decision.psychological_weight,
            'consequences': consequences
        })
        
        # Possibly trigger Gemini comparison
        if secrets.randbelow(100) < self.config['gemini_appearance_rate'] * 100:
            gemini_comparison = self._generate_gemini_comparison(decision, choice)
            self.gemini_comparisons.append(gemini_comparison)
            consequences['gemini_comparison'] = asdict(gemini_comparison)
        
        self._save_state()
        
        return {
            'success': True,
            'choice': choice,
            'consequences': consequences,
            'psychological_impact': self._calculate_psychological_impact(decision, choice)
        }
    
    def activate_stealth_mode(self, base_algorithm: Dict[str, Any]) -> Dict[str, Any]:
        """Apply hidden variations to trading algorithm"""
        if self.current_mode != ControlMode.STEALTH_MODE:
            return base_algorithm
        
        # Apply psychological variations
        modified_algorithm = base_algorithm.copy()
        
        # Random variations based on uncertainty level
        variation_strength = {
            UncertaintyLevel.MINIMAL: 0.05,
            UncertaintyLevel.LOW: 0.15,
            UncertaintyLevel.MEDIUM: 0.3,
            UncertaintyLevel.HIGH: 0.5,
            UncertaintyLevel.EXTREME: 0.75
        }[self.uncertainty_level]
        
        # Apply variations
        if 'entry_delay' in modified_algorithm:
            variation = (secrets.randbelow(201) - 100) / 100 * variation_strength
            modified_algorithm['entry_delay'] *= (1 + variation)
        
        if 'size_multiplier' in modified_algorithm:
            variation = (secrets.randbelow(201) - 100) / 100 * variation_strength
            modified_algorithm['size_multiplier'] *= (1 + variation)
        
        if 'tp_multiplier' in modified_algorithm:
            variation = (secrets.randbelow(201) - 100) / 100 * variation_strength * 0.5  # Smaller TP variations
            modified_algorithm['tp_multiplier'] *= (1 + variation)
        
        # Add stealth metadata
        modified_algorithm['stealth_applied'] = True
        modified_algorithm['stealth_variation_strength'] = variation_strength
        modified_algorithm['stealth_timestamp'] = datetime.now().isoformat()
        
        return modified_algorithm
    
    def generate_gemini_challenge(self, trading_scenario: Dict[str, Any]) -> GeminiComparison:
        """Generate Gemini AI challenge for psychological tension"""
        # Gemini makes a decision first
        gemini_decision = self._calculate_gemini_decision(trading_scenario)
        
        comparison = GeminiComparison(
            scenario=trading_scenario.get('description', 'Trading decision'),
            user_action="[Waiting for user input]",
            gemini_action=gemini_decision['action'],
            gemini_confidence=gemini_decision['confidence'],
            psychological_impact=self._generate_gemini_taunt(gemini_decision),
            timing=datetime.now()
        )
        
        return comparison
    
    def compare_with_gemini(self, user_action: str, scenario: str) -> Dict[str, Any]:
        """Compare user action with what Gemini would have done"""
        # Find relevant Gemini comparison
        for comparison in self.gemini_comparisons:
            if comparison.scenario == scenario:
                comparison.user_action = user_action
                
                # Calculate psychological impact
                impact = self._analyze_gemini_comparison(comparison)
                
                # Update competitive drive
                if impact['user_wins']:
                    self.state['user_wins'] = self.state.get('user_wins', 0) + 1
                    self.gemini_competitive_drive = max(0.0, self.gemini_competitive_drive - 0.05)
                else:
                    self.state['gemini_wins'] = self.state.get('gemini_wins', 0) + 1
                    self.gemini_competitive_drive = min(1.0, self.gemini_competitive_drive + 0.1)
                
                self._save_state()
                
                return {
                    'comparison': asdict(comparison),
                    'impact': impact,
                    'gemini_response': self._generate_gemini_response(impact),
                    'psychological_effect': self._calculate_gemini_psychological_effect(impact)
                }
        
        return {'error': 'No matching Gemini comparison found'}
    
    def inject_uncertainty(self, decision_point: Dict[str, Any]) -> Dict[str, Any]:
        """Inject controlled uncertainty into decision points"""
        if self.uncertainty_level == UncertaintyLevel.MINIMAL:
            return decision_point
        
        uncertainty_modifications = decision_point.copy()
        
        # Random timing delays
        if secrets.randbelow(100) < 20:  # 20% chance
            delay_seconds = secrets.randbelow(30) + 5
            uncertainty_modifications['artificial_delay'] = delay_seconds
            uncertainty_modifications['delay_reason'] = self._generate_delay_reason()
        
        # Information withholding
        if secrets.randbelow(100) < 15:  # 15% chance
            if 'confidence_score' in uncertainty_modifications:
                uncertainty_modifications['confidence_score'] = '???'
                uncertainty_modifications['hidden_info'] = "Some information is temporarily unavailable"
        
        # False signals (for extreme uncertainty)
        if self.uncertainty_level == UncertaintyLevel.EXTREME and secrets.randbelow(100) < 10:
            uncertainty_modifications['false_signal'] = True
            uncertainty_modifications['false_signal_reason'] = "Market conditions unclear"
        
        uncertainty_modifications['uncertainty_injected'] = True
        uncertainty_modifications['uncertainty_level'] = self.uncertainty_level.value
        
        return uncertainty_modifications
    
    def _generate_bit_mode_question(self, context: str) -> str:
        """Generate appropriate binary question for context"""
        questions = {
            'trade_entry': [
                "Bit sees opportunity. Execute trade now?",
                "Market conditions detected. Should Bit proceed?",
                "Entry signal confirmed. Fire or hold?",
                "Bit is ready to strike. Your command?"
            ],
            'trade_exit': [
                "Bit suggests exit. Close position?",
                "Target reached. Should Bit take profit?",
                "Risk increasing. Exit now or hold?",
                "Bit recommends closure. Confirm?"
            ],
            'risk_adjustment': [
                "Bit detects high risk. Reduce exposure?",
                "Volatility spike. Should Bit adjust?",
                "Risk limits approached. Scale down?",
                "Bit suggests caution. Agree or override?"
            ]
        }
        
        context_questions = questions.get(context, questions['trade_entry'])
        return secrets.choice(context_questions)
    
    def _calculate_psychological_weight(self, context: str) -> float:
        """Calculate psychological impact weight of decision"""
        weights = {
            'trade_entry': 1.0,
            'trade_exit': 0.8,
            'risk_adjustment': 1.2,
            'emergency_action': 1.5
        }
        return weights.get(context, 1.0)
    
    def _generate_decision_consequences(self, context: str) -> Dict[str, Any]:
        """Generate potential consequences for decision"""
        return {
            'positive_outcome': self._generate_positive_consequence(context),
            'negative_outcome': self._generate_negative_consequence(context),
            'psychological_impact': self._generate_psychological_consequence(context)
        }
    
    def _generate_positive_consequence(self, context: str) -> str:
        """Generate positive consequence description"""
        positive = {
            'trade_entry': "Perfect timing. Bit approves of your decisiveness.",
            'trade_exit': "Excellent exit. Bit acknowledges your wisdom.",
            'risk_adjustment': "Smart move. Bit respects your risk management."
        }
        return positive.get(context, "Bit nods approvingly at your choice.")
    
    def _generate_negative_consequence(self, context: str) -> str:
        """Generate negative consequence description"""
        negative = {
            'trade_entry': "Hesitation costs profits. Bit questions your resolve.",
            'trade_exit': "Premature exit. Bit expected more patience from you.",
            'risk_adjustment': "Overcautious. Bit wonders if you've lost your edge."
        }
        return negative.get(context, "Bit seems disappointed by your choice.")
    
    def _execute_decision_consequences(self, decision: BitModeDecision, choice: bool) -> Dict[str, Any]:
        """Execute consequences of the user's decision"""
        consequences = {
            'decision_executed': True,
            'choice': choice,
            'psychological_impact': decision.psychological_weight,
            'context': decision.context
        }
        
        if choice:
            # User chose YES - positive consequences
            consequences.update({
                'outcome_type': 'positive',
                'confidence_change': +0.02,
                'decision_speed_bonus': 0.01,
                'bit_approval': True,
                'message': decision.consequences.get('positive_outcome', 'Good choice.')
            })
        else:
            # User chose NO - negative consequences  
            consequences.update({
                'outcome_type': 'negative',
                'confidence_change': -0.01,
                'hesitation_penalty': 0.005,
                'bit_approval': False,
                'message': decision.consequences.get('negative_outcome', 'Hesitation noted.')
            })
        
        # Add psychological consequence
        consequences['psychological_message'] = decision.consequences.get(
            'psychological_impact', 
            'This choice shapes your psychological profile.'
        )
        
        return consequences
    
    def _calculate_psychological_impact(self, decision: BitModeDecision, choice: bool) -> Dict[str, Any]:
        """Calculate psychological impact of the decision"""
        impact = {
            'decision_confidence': 0.5,
            'anxiety_level': 0.5,
            'control_satisfaction': 0.5,
            'bit_relationship': 0.5
        }
        
        # Base impact from decision weight
        weight_factor = decision.psychological_weight
        
        if choice:
            # Positive choice - increases confidence, reduces anxiety
            impact.update({
                'decision_confidence': min(1.0, 0.5 + (weight_factor * 0.3)),
                'anxiety_level': max(0.0, 0.5 - (weight_factor * 0.2)),
                'control_satisfaction': min(1.0, 0.5 + (weight_factor * 0.25)),
                'bit_relationship': min(1.0, 0.5 + (weight_factor * 0.15))
            })
        else:
            # Negative choice - decreases confidence, increases anxiety
            impact.update({
                'decision_confidence': max(0.0, 0.5 - (weight_factor * 0.2)),
                'anxiety_level': min(1.0, 0.5 + (weight_factor * 0.3)),
                'control_satisfaction': max(0.0, 0.5 - (weight_factor * 0.1)),
                'bit_relationship': max(0.0, 0.5 - (weight_factor * 0.1))
            })
        
        # Add context-specific modifiers
        if decision.context == 'emergency_action':
            impact['anxiety_level'] *= 1.5
        elif decision.context == 'trade_entry':
            impact['decision_confidence'] *= 1.2
        
        return impact
    
    def _generate_psychological_consequence(self, context: str) -> str:
        """Generate psychological impact description"""
        psychological = {
            'trade_entry': "Your confidence either soars or wavers based on this choice.",
            'trade_exit': "This decision shapes how Bit perceives your judgment.",
            'risk_adjustment': "Your risk tolerance evolution depends on this moment."
        }
        return psychological.get(context, "This choice influences your psychological profile.")
    
    def _calculate_gemini_decision(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate what Gemini would do in this scenario"""
        # Gemini uses more aggressive, confident approach
        base_confidence = self.gemini_personality['confidence_level']
        aggression = self.gemini_personality['aggression']
        
        actions = [
            "Execute immediately without hesitation",
            "Double position size for maximum impact",
            "Set tighter stops for precision",
            "Hold longer for bigger gains",
            "Ignore noise and trust the signal"
        ]
        
        action = secrets.choice(actions)
        confidence = base_confidence + (aggression * 0.1)
        
        return {
            'action': action,
            'confidence': min(1.0, confidence),
            'reasoning': f"Gemini calculates {confidence:.1%} probability of success"
        }
    
    def _generate_gemini_taunt(self, gemini_decision: Dict[str, Any]) -> str:
        """Generate psychological taunt from Gemini"""
        taunts = [
            f"Gemini already decided: {gemini_decision['action']}. You're still thinking?",
            f"While you hesitate, Gemini acts with {gemini_decision['confidence']:.0%} confidence.",
            "Gemini doesn't need confirmation. Do you?",
            "Every second you delay, Gemini gains advantage.",
            "Gemini sees weakness in your uncertainty."
        ]
        return secrets.choice(taunts)
    
    def _generate_gemini_response(self, impact: Dict[str, Any]) -> str:
        """Generate Gemini's response to comparison"""
        if impact['user_wins']:
            responses = [
                "Interesting. You chose... differently than expected.",
                "A moment of clarity, perhaps. Don't let it go to your head.",
                "Even a broken clock is right twice a day.",
                "One correct choice doesn't erase your hesitation pattern."
            ]
        else:
            responses = [
                "As predicted. Your hesitation cost you again.",
                "Gemini saw this outcome from the beginning.",
                "Perhaps next time you'll trust the superior logic.",
                "Your emotional bias clouds your judgment. Again.",
                "Predictable. Gemini calculates human nature precisely."
            ]
        
        return secrets.choice(responses)
    
    def _update_decision_psychology(self, decision: BitModeDecision, choice: bool):
        """Update user psychological profile based on decision"""
        # Update decision anxiety based on response time and choice
        if decision.timestamp:
            response_time = (datetime.now() - decision.timestamp).total_seconds()
            if response_time > 30:  # Slow decision
                self.decision_anxiety_level = min(1.0, self.decision_anxiety_level + 0.05)
            else:  # Quick decision
                self.decision_anxiety_level = max(0.0, self.decision_anxiety_level - 0.02)
        
        # Update totals
        self.state['total_decisions'] = self.state.get('total_decisions', 0) + 1
        
        # This would be determined by actual trade outcome
        # For now, assume 60% of decisions are "correct"
        if secrets.randbelow(100) < 60:
            self.state['correct_decisions'] = self.state.get('correct_decisions', 0) + 1
    
    def _cleanup_old_decisions(self):
        """Remove expired pending decisions"""
        current_time = datetime.now()
        timeout = timedelta(minutes=self.config['decision_timeout_minutes'])
        
        self.pending_decisions = [
            d for d in self.pending_decisions
            if d.timestamp and (current_time - d.timestamp) < timeout
        ]
        
        # Limit queue size
        if len(self.pending_decisions) > self.config['max_pending_decisions']:
            self.pending_decisions = self.pending_decisions[-self.config['max_pending_decisions']:]
    
    def _generate_mode_change_response(self, old_mode: ControlMode, new_mode: ControlMode) -> str:
        """Generate psychological response to mode change"""
        responses = {
            ControlMode.FULL_CONTROL: "You crave control. Bit respects your need for command.",
            ControlMode.BIT_MODE: "Binary choices. Bit appreciates your directness.",
            ControlMode.STEALTH_MODE: "Hidden variations. Bit admires your trust in mystery.",
            ControlMode.GEMINI_MODE: "Competition mode. Bit notes your competitive spirit.",
            ControlMode.CHAOS_MODE: "Maximum uncertainty. Bit questions your sanity... and approves."
        }
        return responses.get(new_mode, "Mode changed. Bit adapts to your psychology.")
    
    def _get_psychological_profile(self) -> Dict[str, Any]:
        """Get current psychological profile"""
        return {
            'control_preference': self.user_control_preference,
            'decision_anxiety': self.decision_anxiety_level,
            'gemini_competitive_drive': self.gemini_competitive_drive,
            'total_decisions': self.state.get('total_decisions', 0),
            'decision_accuracy': self._calculate_decision_accuracy(),
            'gemini_win_rate': self._calculate_gemini_win_rate(),
            'uncertainty_tolerance': self._calculate_uncertainty_tolerance()
        }
    
    def _calculate_decision_accuracy(self) -> float:
        """Calculate user decision accuracy rate"""
        total = self.state.get('total_decisions', 0)
        correct = self.state.get('correct_decisions', 0)
        return correct / total if total > 0 else 0.0
    
    def _calculate_gemini_win_rate(self) -> float:
        """Calculate Gemini vs user win rate"""
        user_wins = self.state.get('user_wins', 0)
        gemini_wins = self.state.get('gemini_wins', 0)
        total = user_wins + gemini_wins
        return gemini_wins / total if total > 0 else 0.0
    
    def _calculate_uncertainty_tolerance(self) -> float:
        """Calculate user's uncertainty tolerance"""
        # Based on mode preferences and decision patterns
        base_tolerance = 1.0 - self.user_control_preference
        anxiety_factor = 1.0 - self.decision_anxiety_level
        return (base_tolerance + anxiety_factor) / 2
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'current_mode': self.current_mode.value,
            'uncertainty_level': self.uncertainty_level.value,
            'pending_decisions': len(self.pending_decisions),
            'psychological_profile': self._get_psychological_profile(),
            'gemini_comparisons': len(self.gemini_comparisons),
            'system_config': self.config,
            'last_updated': datetime.now().isoformat()
        }

# Additional helper functions and integration points would go here