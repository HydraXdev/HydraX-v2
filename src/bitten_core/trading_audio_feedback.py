"""
BITTEN Trading Audio Feedback System
Audio feedback for trading decisions, approval chirps, and warning sounds
"""

import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .ambient_audio_system import ambient_audio_engine, AudioClip, AudioType, AudioMood, TradingContext
from .norman_story_integration import norman_story_engine, StoryPhase
from .user_settings import get_user_settings

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of trading feedback"""
    APPROVAL = "approval"           # Good decisions
    CAUTION = "caution"            # Risky but acceptable
    WARNING = "warning"            # High risk decisions
    CELEBRATION = "celebration"    # Major wins
    COMFORT = "comfort"           # After losses
    PATIENCE = "patience"         # Wait for better setups
    DISCIPLINE = "discipline"     # Following rules
    CONFIDENCE = "confidence"     # Building momentum


class DecisionQuality(Enum):
    """Quality of trading decisions for feedback"""
    EXCELLENT = "excellent"       # High TCS, good timing
    GOOD = "good"                # Solid decision
    ACCEPTABLE = "acceptable"    # Marginal but ok
    RISKY = "risky"              # Low TCS, high risk
    POOR = "poor"                # Very risky decision


class TradeOutcome(Enum):
    """Possible trade outcomes"""
    BIG_WIN = "big_win"          # >50 pips profit
    SMALL_WIN = "small_win"      # 10-50 pips profit
    SCRATCH = "scratch"          # -5 to +10 pips
    SMALL_LOSS = "small_loss"    # 5-25 pips loss
    BIG_LOSS = "big_loss"        # >25 pips loss


@dataclass
class TradingDecision:
    """Represents a trading decision for feedback"""
    decision_id: str
    user_id: str
    decision_type: str  # 'entry', 'exit', 'size', 'timing'
    tcs_score: Optional[float]
    risk_percentage: float
    market_conditions: Dict[str, Any]
    user_emotional_state: str
    story_phase: StoryPhase
    timestamp: datetime


@dataclass
class FeedbackRule:
    """Rule for determining appropriate feedback"""
    rule_id: str
    name: str
    conditions: Dict[str, Any]
    feedback_type: FeedbackType
    audio_clips: List[str]
    story_phase_modifiers: Dict[StoryPhase, Dict[str, Any]]
    cooldown_minutes: int = 5
    priority: int = 5


class TradingAudioFeedbackEngine:
    """Engine for trading decision audio feedback"""
    
    def __init__(self):
        self.feedback_rules: Dict[str, FeedbackRule] = {}
        self.user_feedback_history: Dict[str, List[Dict]] = {}
        self.feedback_audio_clips: Dict[str, AudioClip] = {}
        
        # Initialize the system
        self._initialize_feedback_audio_clips()
        self._setup_feedback_rules()
        self._setup_bit_personality_responses()
    
    def _initialize_feedback_audio_clips(self):
        """Initialize audio clips for trading feedback"""
        
        feedback_clips = {
            # Approval sounds - Bit likes the decision
            "approval_chirp_confident": AudioClip(
                clip_id="approval_chirp_confident",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.CONFIDENT,
                file_path="bit/feedback/approval_confident.wav",
                duration=0.8,
                description="Confident approval chirp for good decisions",
                tags=["approval", "confident", "good_choice"]
            ),
            
            "approval_purr_satisfied": AudioClip(
                clip_id="approval_purr_satisfied",
                audio_type=AudioType.PURR,
                mood=AudioMood.CONTENT,
                file_path="bit/feedback/approval_purr.wav",
                duration=2.5,
                description="Satisfied purr for excellent decisions",
                tags=["approval", "satisfaction", "excellent"]
            ),
            
            "approval_chirp_gentle": AudioClip(
                clip_id="approval_chirp_gentle",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.CONTENT,
                file_path="bit/feedback/approval_gentle.wav",
                duration=0.6,
                description="Gentle approval for acceptable decisions",
                tags=["approval", "gentle", "acceptable"]
            ),
            
            # Caution sounds - Bit is concerned but not alarmed
            "caution_chirp_questioning": AudioClip(
                clip_id="caution_chirp_questioning",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.CAUTIOUS,
                file_path="bit/feedback/caution_questioning.wav",
                duration=0.9,
                description="Questioning chirp for risky decisions",
                tags=["caution", "questioning", "risk"]
            ),
            
            "caution_trill_concerned": AudioClip(
                clip_id="caution_trill_concerned",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.CAUTIOUS,
                file_path="bit/feedback/caution_trill.wav",
                duration=1.2,
                description="Concerned trill for marginal decisions",
                tags=["caution", "concern", "marginal"]
            ),
            
            "caution_purr_nervous": AudioClip(
                clip_id="caution_purr_nervous",
                audio_type=AudioType.PURR,
                mood=AudioMood.WORRIED,
                file_path="bit/feedback/caution_nervous.wav",
                duration=1.5,
                description="Nervous purr for questionable timing",
                tags=["caution", "nervous", "timing"]
            ),
            
            # Warning sounds - Bit is alarmed
            "warning_chirp_sharp": AudioClip(
                clip_id="warning_chirp_sharp",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.WORRIED,
                file_path="bit/feedback/warning_sharp.wav",
                duration=0.7,
                description="Sharp warning chirp for poor decisions",
                tags=["warning", "sharp", "poor_choice"]
            ),
            
            "warning_meow_protest": AudioClip(
                clip_id="warning_meow_protest",
                audio_type=AudioType.MEOW,
                mood=AudioMood.WORRIED,
                file_path="bit/feedback/warning_protest.wav",
                duration=1.4,
                description="Protesting meow for very risky trades",
                tags=["warning", "protest", "very_risky"]
            ),
            
            "warning_hiss_danger": AudioClip(
                clip_id="warning_hiss_danger",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.WORRIED,
                file_path="bit/feedback/warning_hiss.wav",
                duration=1.0,
                description="Warning hiss for dangerous decisions",
                tags=["warning", "danger", "hiss"]
            ),
            
            # Celebration sounds - Big wins and achievements
            "celebration_trill_excited": AudioClip(
                clip_id="celebration_trill_excited",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.EXCITED,
                file_path="bit/feedback/celebration_trill.wav",
                duration=1.5,
                description="Excited trill for big wins",
                tags=["celebration", "excited", "big_win"]
            ),
            
            "celebration_purr_victory": AudioClip(
                clip_id="celebration_purr_victory",
                audio_type=AudioType.PURR,
                mood=AudioMood.EXCITED,
                file_path="bit/feedback/celebration_victory.wav",
                duration=3.0,
                description="Victory purr for major achievements",
                tags=["celebration", "victory", "achievement"]
            ),
            
            "celebration_chirp_series": AudioClip(
                clip_id="celebration_chirp_series",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.EXCITED,
                file_path="bit/feedback/celebration_series.wav",
                duration=2.0,
                description="Series of celebration chirps",
                tags=["celebration", "series", "multiple"]
            ),
            
            # Comfort sounds - After losses
            "comfort_purr_healing": AudioClip(
                clip_id="comfort_purr_healing",
                audio_type=AudioType.PURR,
                mood=AudioMood.CALM,
                file_path="bit/feedback/comfort_healing.wav",
                duration=4.0,
                description="Healing comfort purr after losses",
                tags=["comfort", "healing", "loss"],
                volume=0.6
            ),
            
            "comfort_chirp_supportive": AudioClip(
                clip_id="comfort_chirp_supportive",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.CALM,
                file_path="bit/feedback/comfort_supportive.wav",
                duration=1.0,
                description="Supportive chirp during difficult times",
                tags=["comfort", "support", "difficult"]
            ),
            
            "comfort_presence_quiet": AudioClip(
                clip_id="comfort_presence_quiet",
                audio_type=AudioType.AMBIENT,
                mood=AudioMood.CALM,
                file_path="bit/feedback/comfort_presence.wav",
                duration=6.0,
                description="Quiet presence sound for comfort",
                tags=["comfort", "presence", "quiet"],
                volume=0.4
            ),
            
            # Patience sounds - Wait for better setups
            "patience_purr_wisdom": AudioClip(
                clip_id="patience_purr_wisdom",
                audio_type=AudioType.PURR,
                mood=AudioMood.CONTENT,
                file_path="bit/feedback/patience_wisdom.wav",
                duration=3.5,
                description="Wise purr teaching patience",
                tags=["patience", "wisdom", "teaching"]
            ),
            
            "patience_chirp_gentle": AudioClip(
                clip_id="patience_chirp_gentle",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.CALM,
                file_path="bit/feedback/patience_gentle.wav",
                duration=0.8,
                description="Gentle chirp encouraging patience",
                tags=["patience", "gentle", "encouragement"]
            ),
            
            # Discipline sounds - Following the rules
            "discipline_chirp_approval": AudioClip(
                clip_id="discipline_chirp_approval",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.CONFIDENT,
                file_path="bit/feedback/discipline_approval.wav",
                duration=0.9,
                description="Approval chirp for disciplined behavior",
                tags=["discipline", "approval", "rules"]
            ),
            
            "discipline_purr_proud": AudioClip(
                clip_id="discipline_purr_proud",
                audio_type=AudioType.PURR,
                mood=AudioMood.CONFIDENT,
                file_path="bit/feedback/discipline_proud.wav",
                duration=2.8,
                description="Proud purr for following discipline",
                tags=["discipline", "proud", "following"]
            ),
            
            # Confidence building sounds
            "confidence_chirp_building": AudioClip(
                clip_id="confidence_chirp_building",
                audio_type=AudioType.CHIRP,
                mood=AudioMood.CONFIDENT,
                file_path="bit/feedback/confidence_building.wav",
                duration=1.1,
                description="Chirp that builds confidence",
                tags=["confidence", "building", "momentum"]
            ),
            
            "confidence_purr_steady": AudioClip(
                clip_id="confidence_purr_steady",
                audio_type=AudioType.PURR,
                mood=AudioMood.CONFIDENT,
                file_path="bit/feedback/confidence_steady.wav",
                duration=2.2,
                description="Steady purr building confidence",
                tags=["confidence", "steady", "building"]
            ),
            
            # Subtle trading sounds
            "trade_entry_chime": AudioClip(
                clip_id="trade_entry_chime",
                audio_type=AudioType.TRADING_FEEDBACK,
                mood=AudioMood.ALERT,
                file_path="bit/feedback/entry_chime.wav",
                duration=1.0,
                description="Subtle chime for trade entries",
                tags=["entry", "chime", "subtle"]
            ),
            
            "trade_exit_bell": AudioClip(
                clip_id="trade_exit_bell",
                audio_type=AudioType.TRADING_FEEDBACK,
                mood=AudioMood.CONTENT,
                file_path="bit/feedback/exit_bell.wav",
                duration=1.5,
                description="Gentle bell for trade exits",
                tags=["exit", "bell", "gentle"]
            ),
            
            "profit_chime_soft": AudioClip(
                clip_id="profit_chime_soft",
                audio_type=AudioType.TRADING_FEEDBACK,
                mood=AudioMood.CONTENT,
                file_path="bit/feedback/profit_soft.wav",
                duration=2.0,
                description="Soft chime for profitable trades",
                tags=["profit", "chime", "soft"]
            )
        }
        
        self.feedback_audio_clips.update(feedback_clips)
        ambient_audio_engine.audio_clips.update(feedback_clips)
    
    def _setup_feedback_rules(self):
        """Setup rules for trading feedback"""
        
        rules = {
            "excellent_decision": FeedbackRule(
                rule_id="excellent_decision",
                name="Excellent Trading Decision",
                conditions={
                    'tcs_score_min': 85,
                    'risk_percentage_max': 2.0,
                    'market_conditions': ['stable', 'trending']
                },
                feedback_type=FeedbackType.APPROVAL,
                audio_clips=["approval_purr_satisfied", "approval_chirp_confident"],
                story_phase_modifiers={
                    StoryPhase.EARLY_STRUGGLE: {'encouragement_boost': True},
                    StoryPhase.LEGACY: {'wisdom_acknowledgment': True}
                },
                cooldown_minutes=2,
                priority=8
            ),
            
            "good_decision": FeedbackRule(
                rule_id="good_decision",
                name="Good Trading Decision", 
                conditions={
                    'tcs_score_min': 75,
                    'risk_percentage_max': 2.5
                },
                feedback_type=FeedbackType.APPROVAL,
                audio_clips=["approval_chirp_confident", "approval_chirp_gentle"],
                story_phase_modifiers={},
                cooldown_minutes=3,
                priority=6
            ),
            
            "risky_decision": FeedbackRule(
                rule_id="risky_decision",
                name="Risky Trading Decision",
                conditions={
                    'tcs_score_max': 70,
                    'risk_percentage_min': 3.0
                },
                feedback_type=FeedbackType.CAUTION,
                audio_clips=["caution_chirp_questioning", "caution_trill_concerned"],
                story_phase_modifiers={
                    StoryPhase.EARLY_STRUGGLE: {'extra_concern': True}
                },
                cooldown_minutes=1,
                priority=7
            ),
            
            "dangerous_decision": FeedbackRule(
                rule_id="dangerous_decision",
                name="Dangerous Trading Decision",
                conditions={
                    'tcs_score_max': 60,
                    'risk_percentage_min': 4.0
                },
                feedback_type=FeedbackType.WARNING,
                audio_clips=["warning_chirp_sharp", "warning_meow_protest"],
                story_phase_modifiers={},
                cooldown_minutes=1,
                priority=9
            ),
            
            "very_dangerous": FeedbackRule(
                rule_id="very_dangerous",
                name="Very Dangerous Decision",
                conditions={
                    'tcs_score_max': 50,
                    'risk_percentage_min': 5.0
                },
                feedback_type=FeedbackType.WARNING,
                audio_clips=["warning_hiss_danger", "warning_meow_protest"],
                story_phase_modifiers={},
                cooldown_minutes=0,  # Always warn about very dangerous decisions
                priority=10
            ),
            
            "big_win_celebration": FeedbackRule(
                rule_id="big_win_celebration",
                name="Big Win Celebration",
                conditions={
                    'trade_outcome': TradeOutcome.BIG_WIN
                },
                feedback_type=FeedbackType.CELEBRATION,
                audio_clips=["celebration_trill_excited", "celebration_purr_victory"],
                story_phase_modifiers={
                    StoryPhase.EARLY_STRUGGLE: {'extra_excitement': True}
                },
                cooldown_minutes=5,
                priority=9
            ),
            
            "loss_comfort": FeedbackRule(
                rule_id="loss_comfort",
                name="Loss Comfort",
                conditions={
                    'trade_outcome': [TradeOutcome.SMALL_LOSS, TradeOutcome.BIG_LOSS]
                },
                feedback_type=FeedbackType.COMFORT,
                audio_clips=["comfort_purr_healing", "comfort_chirp_supportive"],
                story_phase_modifiers={
                    StoryPhase.EARLY_STRUGGLE: {'extended_comfort': True}
                },
                cooldown_minutes=10,
                priority=8
            ),
            
            "patience_teaching": FeedbackRule(
                rule_id="patience_teaching",
                name="Patience Teaching",
                conditions={
                    'impatient_behavior': True,
                    'market_conditions': ['choppy', 'uncertain']
                },
                feedback_type=FeedbackType.PATIENCE,
                audio_clips=["patience_purr_wisdom", "patience_chirp_gentle"],
                story_phase_modifiers={},
                cooldown_minutes=15,
                priority=6
            ),
            
            "discipline_reward": FeedbackRule(
                rule_id="discipline_reward",
                name="Discipline Reward",
                conditions={
                    'followed_rules': True,
                    'risk_adherence': True
                },
                feedback_type=FeedbackType.DISCIPLINE,
                audio_clips=["discipline_chirp_approval", "discipline_purr_proud"],
                story_phase_modifiers={
                    StoryPhase.DISCIPLINE: {'reinforcement': True}
                },
                cooldown_minutes=20,
                priority=5
            ),
            
            "confidence_building": FeedbackRule(
                rule_id="confidence_building",
                name="Confidence Building",
                conditions={
                    'consecutive_wins': 2,
                    'improving_performance': True
                },
                feedback_type=FeedbackType.CONFIDENCE,
                audio_clips=["confidence_chirp_building", "confidence_purr_steady"],
                story_phase_modifiers={},
                cooldown_minutes=30,
                priority=4
            )
        }
        
        self.feedback_rules.update(rules)
    
    def _setup_bit_personality_responses(self):
        """Setup Bit's personality-driven responses"""
        
        # Bit's responses evolve based on user's story phase
        self.personality_responses = {
            StoryPhase.EARLY_STRUGGLE: {
                'supportive': True,
                'patient': True,
                'extra_comfort': True,
                'gentle_warnings': True
            },
            StoryPhase.AWAKENING: {
                'encouraging': True,
                'celebrates_small_wins': True,
                'guidance_focused': True
            },
            StoryPhase.DISCIPLINE: {
                'reinforces_good_habits': True,
                'stricter_on_rules': True,
                'proud_of_progress': True
            },
            StoryPhase.MASTERY: {
                'confident_companion': True,
                'celebrates_expertise': True,
                'subtle_guidance': True
            },
            StoryPhase.LEGACY: {
                'wise_companion': True,
                'respectful_acknowledgment': True,
                'shared_accomplishment': True
            }
        }
    
    def evaluate_trading_decision(self, decision: TradingDecision) -> List[FeedbackType]:
        """Evaluate a trading decision and return appropriate feedback types"""
        
        applicable_feedback = []
        
        # Check each rule
        for rule in self.feedback_rules.values():
            if self._rule_applies(rule, decision):
                # Check cooldown
                if not self._is_rule_on_cooldown(decision.user_id, rule.rule_id):
                    applicable_feedback.append((rule.feedback_type, rule))
        
        # Sort by priority and return
        applicable_feedback.sort(key=lambda x: x[1].priority, reverse=True)
        return applicable_feedback
    
    def _rule_applies(self, rule: FeedbackRule, decision: TradingDecision) -> bool:
        """Check if a rule applies to the decision"""
        
        conditions = rule.conditions
        
        # Check TCS score conditions
        if 'tcs_score_min' in conditions and decision.tcs_score:
            if decision.tcs_score < conditions['tcs_score_min']:
                return False
        
        if 'tcs_score_max' in conditions and decision.tcs_score:
            if decision.tcs_score > conditions['tcs_score_max']:
                return False
        
        # Check risk percentage conditions
        if 'risk_percentage_min' in conditions:
            if decision.risk_percentage < conditions['risk_percentage_min']:
                return False
        
        if 'risk_percentage_max' in conditions:
            if decision.risk_percentage > conditions['risk_percentage_max']:
                return False
        
        # Check market conditions
        if 'market_conditions' in conditions:
            required_conditions = conditions['market_conditions']
            current_condition = decision.market_conditions.get('state', 'unknown')
            if current_condition not in required_conditions:
                return False
        
        # Check other conditions based on rule type
        # This would be expanded based on specific rule needs
        
        return True
    
    def _is_rule_on_cooldown(self, user_id: str, rule_id: str) -> bool:
        """Check if rule is on cooldown for user"""
        
        history = self.user_feedback_history.get(user_id, [])
        rule = self.feedback_rules.get(rule_id)
        
        if not rule or rule.cooldown_minutes == 0:
            return False
        
        # Find last time this rule was triggered
        for record in reversed(history):
            if record.get('rule_id') == rule_id:
                last_trigger = record['timestamp']
                time_since = datetime.now() - last_trigger
                if time_since < timedelta(minutes=rule.cooldown_minutes):
                    return True
                break
        
        return False
    
    async def provide_trading_feedback(self, decision: TradingDecision) -> List[str]:
        """Provide audio feedback for a trading decision"""
        
        # Check user settings
        user_settings = get_user_settings(decision.user_id)
        if not user_settings.sounds_enabled:
            return []
        
        # Evaluate the decision
        feedback_list = self.evaluate_trading_decision(decision)
        
        if not feedback_list:
            return []
        
        # Play feedback audio
        played_events = []
        
        for feedback_type, rule in feedback_list[:2]:  # Limit to 2 pieces of feedback
            # Select appropriate audio clip
            audio_clip_id = self._select_audio_clip(rule, decision)
            
            if audio_clip_id:
                # Play the audio
                event_id = await ambient_audio_engine.play_contextual_audio(
                    user_id=decision.user_id,
                    context=TradingContext.TRADE_OPENED,  # Or appropriate context
                    mood=self._get_mood_for_feedback(feedback_type),
                    metadata={
                        'feedback_type': feedback_type.value,
                        'rule_id': rule.rule_id,
                        'decision_id': decision.decision_id
                    }
                )
                
                if event_id:
                    played_events.append(event_id)
                    self._record_feedback(decision.user_id, rule.rule_id, feedback_type)
        
        return played_events
    
    def _select_audio_clip(self, rule: FeedbackRule, decision: TradingDecision) -> Optional[str]:
        """Select appropriate audio clip for the rule and decision"""
        
        available_clips = rule.audio_clips.copy()
        
        # Apply story phase modifiers
        story_modifiers = rule.story_phase_modifiers.get(decision.story_phase, {})
        
        if story_modifiers.get('encouragement_boost') and decision.story_phase == StoryPhase.EARLY_STRUGGLE:
            # Prefer more encouraging clips for early phase
            encouraging_clips = [clip for clip in available_clips if 'gentle' in clip or 'supportive' in clip]
            if encouraging_clips:
                available_clips = encouraging_clips
        
        if story_modifiers.get('wisdom_acknowledgment') and decision.story_phase == StoryPhase.LEGACY:
            # Prefer wisdom-oriented clips for legacy phase
            wisdom_clips = [clip for clip in available_clips if 'wisdom' in clip or 'proud' in clip]
            if wisdom_clips:
                available_clips = wisdom_clips
        
        return random.choice(available_clips) if available_clips else None
    
    def _get_mood_for_feedback(self, feedback_type: FeedbackType) -> AudioMood:
        """Get appropriate mood for feedback type"""
        
        mood_map = {
            FeedbackType.APPROVAL: AudioMood.CONFIDENT,
            FeedbackType.CAUTION: AudioMood.CAUTIOUS,
            FeedbackType.WARNING: AudioMood.WORRIED,
            FeedbackType.CELEBRATION: AudioMood.EXCITED,
            FeedbackType.COMFORT: AudioMood.CALM,
            FeedbackType.PATIENCE: AudioMood.CONTENT,
            FeedbackType.DISCIPLINE: AudioMood.CONFIDENT,
            FeedbackType.CONFIDENCE: AudioMood.CONFIDENT
        }
        
        return mood_map.get(feedback_type, AudioMood.CONTENT)
    
    def _record_feedback(self, user_id: str, rule_id: str, feedback_type: FeedbackType):
        """Record feedback for cooldown tracking"""
        
        if user_id not in self.user_feedback_history:
            self.user_feedback_history[user_id] = []
        
        self.user_feedback_history[user_id].append({
            'rule_id': rule_id,
            'feedback_type': feedback_type.value,
            'timestamp': datetime.now()
        })
        
        # Keep only last 100 feedback records per user
        if len(self.user_feedback_history[user_id]) > 100:
            self.user_feedback_history[user_id] = self.user_feedback_history[user_id][-100:]
    
    async def provide_trade_outcome_feedback(self, user_id: str, outcome: TradeOutcome, 
                                           profit_loss: float, details: Dict[str, Any]) -> Optional[str]:
        """Provide feedback based on trade outcome"""
        
        # Create a mock decision for outcome evaluation
        decision = TradingDecision(
            decision_id=f"outcome_{datetime.now().timestamp()}",
            user_id=user_id,
            decision_type='outcome',
            tcs_score=None,
            risk_percentage=details.get('risk_percentage', 2.0),
            market_conditions=details.get('market_conditions', {}),
            user_emotional_state=details.get('emotional_state', 'neutral'),
            story_phase=norman_story_engine.get_user_story_context(user_id).current_phase,
            timestamp=datetime.now()
        )
        
        # Add outcome to decision
        decision.market_conditions['trade_outcome'] = outcome
        
        # Get feedback
        feedback_events = await self.provide_trading_feedback(decision)
        
        # Additional outcome-specific audio
        if outcome == TradeOutcome.BIG_WIN and profit_loss > 100:
            # Extra celebration for really big wins
            await ambient_audio_engine.play_contextual_audio(
                user_id=user_id,
                context=TradingContext.PROFIT_TARGET,
                mood=AudioMood.EXCITED
            )
        
        elif outcome in [TradeOutcome.BIG_LOSS, TradeOutcome.SMALL_LOSS]:
            # Comfort after losses
            await ambient_audio_engine.play_contextual_audio(
                user_id=user_id,
                context=TradingContext.STOP_LOSS,
                mood=AudioMood.CALM
            )
        
        return feedback_events[0] if feedback_events else None
    
    def get_feedback_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get feedback statistics for user"""
        
        history = self.user_feedback_history.get(user_id, [])
        
        # Analyze feedback patterns
        feedback_counts = {}
        for record in history:
            feedback_type = record['feedback_type']
            feedback_counts[feedback_type] = feedback_counts.get(feedback_type, 0) + 1
        
        # Calculate recent feedback
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_feedback = [r for r in history if r['timestamp'] > recent_cutoff]
        
        return {
            'total_feedback_events': len(history),
            'feedback_distribution': feedback_counts,
            'recent_feedback_24h': len(recent_feedback),
            'most_common_feedback': max(feedback_counts.items(), key=lambda x: x[1])[0] if feedback_counts else None,
            'available_feedback_types': [ft.value for ft in FeedbackType]
        }


# Global instance
trading_audio_feedback_engine = TradingAudioFeedbackEngine()


# Convenience functions
async def provide_entry_feedback(user_id: str, tcs_score: float, risk_percentage: float, 
                               market_conditions: Dict[str, Any]) -> List[str]:
    """Provide feedback for trade entry decisions"""
    
    decision = TradingDecision(
        decision_id=f"entry_{datetime.now().timestamp()}",
        user_id=user_id,
        decision_type='entry',
        tcs_score=tcs_score,
        risk_percentage=risk_percentage,
        market_conditions=market_conditions,
        user_emotional_state='neutral',
        story_phase=norman_story_engine.get_user_story_context(user_id).current_phase,
        timestamp=datetime.now()
    )
    
    return await trading_audio_feedback_engine.provide_trading_feedback(decision)


async def provide_outcome_feedback(user_id: str, profit_pips: float, profit_currency: float = 0) -> Optional[str]:
    """Provide feedback for trade outcomes"""
    
    # Determine outcome based on profit
    if profit_pips > 50:
        outcome = TradeOutcome.BIG_WIN
    elif profit_pips > 10:
        outcome = TradeOutcome.SMALL_WIN
    elif profit_pips > -5:
        outcome = TradeOutcome.SCRATCH
    elif profit_pips > -25:
        outcome = TradeOutcome.SMALL_LOSS
    else:
        outcome = TradeOutcome.BIG_LOSS
    
    return await trading_audio_feedback_engine.provide_trade_outcome_feedback(
        user_id, outcome, profit_currency, {'profit_pips': profit_pips}
    )