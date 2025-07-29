#!/usr/bin/env python3
"""
BITTEN AI Trading Coach - Personalized Intelligence System
Combines coaching, risk prediction, and psychological state detection
"""

import json
import time
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class PsychologicalState(Enum):
    """Psychological trading states"""
    CONFIDENT = "confident"
    FEARFUL = "fearful"
    GREEDY = "greedy"
    REVENGE_TRADING = "revenge_trading"
    OVERCONFIDENT = "overconfident"
    NEUTRAL = "neutral"
    TILT = "tilt"
    ANALYSIS_PARALYSIS = "analysis_paralysis"

class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"

@dataclass
class TradePattern:
    """Individual trade pattern analysis"""
    symbol: str
    direction: str
    tcs_score: float
    outcome: str  # win/loss/pending
    pnl_percent: float
    hold_time_minutes: int
    exit_reason: str
    psychological_state: PsychologicalState
    timestamp: datetime

@dataclass
class PsychologicalProfile:
    """User's psychological trading profile"""
    current_state: PsychologicalState
    dominant_emotions: List[str]
    stress_level: float  # 0-10
    confidence_level: float  # 0-10
    revenge_trading_risk: float  # 0-10
    overtrading_risk: float  # 0-10
    last_updated: datetime
    intervention_needed: bool

@dataclass
class RiskPrediction:
    """AI-generated risk prediction"""
    drawdown_risk_percent: float
    correlation_storm_risk: float
    overexposure_risk: float
    psychological_risk: float
    overall_risk_level: RiskLevel
    predicted_max_drawdown: float
    recommendation: str
    confidence: float

@dataclass
class CoachingInsight:
    """Personalized coaching insight"""
    category: str  # pattern/psychology/risk/strategy
    insight: str
    actionable_advice: str
    priority: str  # high/medium/low
    based_on_trades: List[str]  # trade IDs
    confidence: float

class AITradingCoach:
    """
    Comprehensive AI Trading Coach with psychological awareness
    Provides real-time coaching, risk prediction, and emotional intervention
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.trade_history: List[TradePattern] = []
        self.psychological_history: List[PsychologicalProfile] = []
        self.coaching_history: List[CoachingInsight] = []
        
        # Analysis parameters
        self.min_trades_for_patterns = 5
        self.pattern_lookback_days = 30
        self.psychology_analysis_window = 10  # Last 10 trades
        
        # Risk thresholds
        self.risk_thresholds = {
            "drawdown_warning": 10.0,  # 10% predicted drawdown
            "correlation_warning": 0.7,  # 70% correlation
            "overexposure_warning": 15.0,  # 15% of account
            "revenge_trading_threshold": 3,  # 3 losses in a row
            "overtrading_threshold": 10  # 10 trades in 24h
        }
        
        # Load existing data
        self._load_user_data()
        
        logger.info(f"AI Trading Coach initialized for user {user_id}")
    
    def analyze_trade_request(self, signal: Dict, user_context: Dict) -> Dict[str, Any]:
        """
        Comprehensive analysis before trade execution
        Returns coaching advice, risk assessment, and psychological state
        """
        analysis_start = time.time()
        
        # 1. Psychological State Detection
        psych_state = self._detect_psychological_state(user_context)
        
        # 2. Risk Prediction
        risk_prediction = self._predict_trade_risk(signal, user_context)
        
        # 3. Pattern Analysis
        pattern_insights = []  # Would implement pattern analysis here
        
        # 4. Generate Coaching Advice
        coaching_advice = self._generate_coaching_advice(signal, psych_state, risk_prediction)
        
        # 5. Intervention Check
        intervention = self._check_intervention_needed(psych_state, risk_prediction)
        
        analysis_time = time.time() - analysis_start
        
        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_time_ms": int(analysis_time * 1000),
            "psychological_state": {
                "current_state": psych_state.current_state.value,
                "stress_level": psych_state.stress_level,
                "confidence_level": psych_state.confidence_level,
                "intervention_needed": intervention["needed"],
                "intervention_message": intervention.get("message", "")
            },
            "risk_assessment": {
                "overall_level": risk_prediction.overall_risk_level.value,
                "drawdown_risk": risk_prediction.drawdown_risk_percent,
                "correlation_risk": risk_prediction.correlation_storm_risk,
                "psychological_risk": risk_prediction.psychological_risk,
                "recommendation": risk_prediction.recommendation,
                "confidence": risk_prediction.confidence
            },
            "coaching_insights": [asdict(insight) for insight in pattern_insights],
            "personalized_advice": coaching_advice,
            "trade_recommendation": self._get_trade_recommendation(signal, psych_state, risk_prediction),
            "position_size_adjustment": self._calculate_position_adjustment(risk_prediction, psych_state)
        }
    
    def record_trade_execution(self, trade_data: Dict):
        """Record trade execution for pattern learning"""
        
        # Detect psychological state at trade time
        psych_state = self._detect_psychological_state(trade_data.get("user_context", {}))
        
        trade_pattern = TradePattern(
            symbol=trade_data["symbol"],
            direction=trade_data["direction"],
            tcs_score=trade_data.get("tcs_score", 0),
            outcome="pending",  # Will be updated when trade closes
            pnl_percent=0,  # Will be updated when trade closes
            hold_time_minutes=0,  # Will be updated when trade closes
            exit_reason="pending",
            psychological_state=psych_state.current_state,
            timestamp=datetime.now()
        )
        
        self.trade_history.append(trade_pattern)
        self._save_user_data()
        
        logger.info(f"Trade recorded for AI analysis: {trade_data['symbol']} {trade_data['direction']}")
    
    def update_trade_outcome(self, trade_id: str, outcome_data: Dict):
        """Update trade outcome for learning"""
        
        # Find and update the trade
        for trade in reversed(self.trade_history):  # Search from most recent
            if (trade.symbol == outcome_data.get("symbol") and 
                trade.direction == outcome_data.get("direction")):
                
                trade.outcome = "win" if outcome_data.get("pnl", 0) > 0 else "loss"
                trade.pnl_percent = outcome_data.get("pnl_percent", 0)
                trade.hold_time_minutes = outcome_data.get("hold_time_minutes", 0)
                trade.exit_reason = outcome_data.get("exit_reason", "manual")
                
                # Generate post-trade insights
                self._generate_post_trade_insights(trade)
                break
        
        self._save_user_data()
    
    def _detect_psychological_state(self, user_context: Dict) -> PsychologicalProfile:
        """Detect current psychological state based on recent trading behavior"""
        
        if len(self.trade_history) < 3:
            return PsychologicalProfile(
                current_state=PsychologicalState.NEUTRAL,
                dominant_emotions=["learning"],
                stress_level=3.0,
                confidence_level=5.0,
                revenge_trading_risk=2.0,
                overtrading_risk=2.0,
                last_updated=datetime.now(),
                intervention_needed=False
            )
        
        recent_trades = self.trade_history[-self.psychology_analysis_window:]
        
        # Calculate metrics
        recent_losses = [t for t in recent_trades if t.outcome == "loss"]
        consecutive_losses = self._count_consecutive_losses(recent_trades)
        trades_today = self._count_trades_today()
        avg_hold_time = statistics.mean([t.hold_time_minutes for t in recent_trades if t.hold_time_minutes > 0])
        
        # Detect psychological patterns
        stress_level = self._calculate_stress_level(recent_trades, user_context)
        confidence_level = self._calculate_confidence_level(recent_trades)
        
        # Determine primary psychological state
        current_state = PsychologicalState.NEUTRAL
        dominant_emotions = ["focused"]
        
        if consecutive_losses >= 3:
            current_state = PsychologicalState.REVENGE_TRADING
            dominant_emotions = ["frustration", "desperation"]
            stress_level = min(10.0, stress_level + 3.0)
        elif len(recent_losses) / len(recent_trades) > 0.7:
            current_state = PsychologicalState.FEARFUL
            dominant_emotions = ["anxiety", "doubt"]
            confidence_level = max(1.0, confidence_level - 2.0)
        elif trades_today > self.risk_thresholds["overtrading_threshold"]:
            current_state = PsychologicalState.OVERCONFIDENT
            dominant_emotions = ["excitement", "impulsiveness"]
        elif avg_hold_time < 5:  # Very short hold times
            current_state = PsychologicalState.TILT
            dominant_emotions = ["impatience", "anxiety"]
        
        revenge_risk = min(10.0, consecutive_losses * 2.5)
        overtrading_risk = min(10.0, (trades_today / 5) * 2.0)
        
        intervention_needed = (stress_level > 7.0 or 
                             revenge_risk > 6.0 or 
                             overtrading_risk > 6.0 or
                             current_state in [PsychologicalState.REVENGE_TRADING, PsychologicalState.TILT])
        
        profile = PsychologicalProfile(
            current_state=current_state,
            dominant_emotions=dominant_emotions,
            stress_level=stress_level,
            confidence_level=confidence_level,
            revenge_trading_risk=revenge_risk,
            overtrading_risk=overtrading_risk,
            last_updated=datetime.now(),
            intervention_needed=intervention_needed
        )
        
        self.psychological_history.append(profile)
        return profile
    
    def _predict_trade_risk(self, signal: Dict, user_context: Dict) -> RiskPrediction:
        """Predict comprehensive risk for the proposed trade"""
        
        # 1. Historical Drawdown Analysis
        drawdown_risk = self._predict_drawdown_risk(signal, user_context)
        
        # 2. Correlation Storm Detection
        correlation_risk = self._detect_correlation_storm_risk(signal)
        
        # 3. Overexposure Analysis
        overexposure_risk = self._calculate_overexposure_risk(signal, user_context)
        
        # 4. Psychological Risk Factor
        psychological_risk = self._calculate_psychological_risk_factor(user_context)
        
        # 5. Overall Risk Level
        risk_scores = [drawdown_risk, correlation_risk, overexposure_risk, psychological_risk]
        overall_risk_score = statistics.mean(risk_scores)
        
        if overall_risk_score < 3.0:
            risk_level = RiskLevel.LOW
        elif overall_risk_score < 6.0:
            risk_level = RiskLevel.MODERATE
        elif overall_risk_score < 8.5:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.EXTREME
        
        # Generate recommendation
        recommendation = self._generate_risk_recommendation(risk_level, risk_scores)
        
        # Predict maximum drawdown
        predicted_max_dd = self._predict_max_drawdown(signal, user_context)
        
        return RiskPrediction(
            drawdown_risk_percent=drawdown_risk,
            correlation_storm_risk=correlation_risk,
            overexposure_risk=overexposure_risk,
            psychological_risk=psychological_risk,
            overall_risk_level=risk_level,
            predicted_max_drawdown=predicted_max_dd,
            recommendation=recommendation,
            confidence=0.75  # AI confidence in prediction
        )
    
    def _generate_coaching_advice(self, signal: Dict, psych_state: PsychologicalProfile, 
                                risk_prediction: RiskPrediction) -> Dict[str, str]:
        """Generate personalized coaching advice"""
        
        advice = {
            "pre_trade_coaching": "",
            "psychological_guidance": "",
            "risk_management_tip": "",
            "strategy_suggestion": "",
            "confidence_building": ""
        }
        
        # Pre-trade coaching based on patterns
        symbol = signal.get("symbol", "")
        if self._has_symbol_weakness(symbol):
            advice["pre_trade_coaching"] = (
                f"⚠️ COACH: You've struggled with {symbol} recently. "
                f"Consider reducing position size by 25% until you regain confidence."
            )
        elif self._has_symbol_strength(symbol):
            advice["pre_trade_coaching"] = (
                f"💪 COACH: Strong track record on {symbol}. "
                f"Your last 3 trades averaged +{self._get_symbol_avg_return(symbol):.1f}%."
            )
        
        # Psychological guidance
        if psych_state.current_state == PsychologicalState.REVENGE_TRADING:
            advice["psychological_guidance"] = (
                "🛑 INTERVENTION: Revenge trading detected. Take a 30-minute break. "
                "Your next trade needs 90%+ TCS to proceed."
            )
        elif psych_state.current_state == PsychologicalState.FEARFUL:
            advice["psychological_guidance"] = (
                "🧘 MINDSET: Fear is affecting your judgment. Start with 50% position size. "
                "Focus on process, not profit."
            )
        elif psych_state.current_state == PsychologicalState.OVERCONFIDENT:
            advice["psychological_guidance"] = (
                "⚖️ BALANCE: Confidence is good, overconfidence is dangerous. "
                "Stick to your risk management rules."
            )
        
        # Risk management tips
        if risk_prediction.overall_risk_level == RiskLevel.HIGH:
            advice["risk_management_tip"] = (
                "🚨 HIGH RISK: Consider reducing position to 50% normal size. "
                f"Predicted max drawdown: {risk_prediction.predicted_max_drawdown:.1f}%"
            )
        elif risk_prediction.correlation_storm_risk > 7.0:
            advice["risk_management_tip"] = (
                "⛈️ CORRELATION STORM: Multiple pairs moving together. "
                "Avoid additional trades in correlated pairs."
            )
        
        # Strategy suggestions
        tcs_score = signal.get("tcs_score", 0)
        if tcs_score < 75:
            advice["strategy_suggestion"] = (
                "📊 STRATEGY: TCS below 75%. Consider waiting for higher probability setup "
                "or using this as a small test position."
            )
        
        return advice
    
    def _check_intervention_needed(self, psych_state: PsychologicalProfile, 
                                 risk_prediction: RiskPrediction) -> Dict[str, Any]:
        """Check if immediate intervention is needed"""
        
        interventions = []
        
        # Psychological interventions
        if psych_state.current_state == PsychologicalState.REVENGE_TRADING:
            interventions.append({
                "type": "psychological",
                "severity": "high",
                "message": "🛑 MANDATORY BREAK: Revenge trading detected. 30-minute cooldown required.",
                "action": "force_break",
                "duration_minutes": 30
            })
        
        if psych_state.stress_level > 8.0:
            interventions.append({
                "type": "psychological", 
                "severity": "medium",
                "message": "🧘 STRESS WARNING: High stress detected. Consider meditation or break.",
                "action": "suggest_break",
                "duration_minutes": 15
            })
        
        # Risk interventions
        if risk_prediction.overall_risk_level == RiskLevel.EXTREME:
            interventions.append({
                "type": "risk",
                "severity": "high", 
                "message": "⚠️ EXTREME RISK: Trade blocked. Risk level too high for execution.",
                "action": "block_trade",
                "reason": "extreme_risk"
            })
        
        # Overtrading intervention
        if self._count_trades_today() > self.risk_thresholds["overtrading_threshold"]:
            interventions.append({
                "type": "overtrading",
                "severity": "medium",
                "message": "📊 OVERTRADING: Daily limit reached. Consider quality over quantity.",
                "action": "warn_overtrading",
                "trades_today": self._count_trades_today()
            })
        
        return {
            "needed": len(interventions) > 0,
            "interventions": interventions,
            "message": interventions[0]["message"] if interventions else ""
        }
    
    def _calculate_position_adjustment(self, risk_prediction: RiskPrediction, 
                                     psych_state: PsychologicalProfile) -> float:
        """Calculate position size adjustment multiplier"""
        
        base_multiplier = 1.0
        
        # Risk-based adjustments
        if risk_prediction.overall_risk_level == RiskLevel.HIGH:
            base_multiplier *= 0.5
        elif risk_prediction.overall_risk_level == RiskLevel.EXTREME:
            base_multiplier *= 0.1
        elif risk_prediction.overall_risk_level == RiskLevel.LOW:
            base_multiplier *= 1.2
        
        # Psychology-based adjustments
        if psych_state.current_state == PsychologicalState.FEARFUL:
            base_multiplier *= 0.7
        elif psych_state.current_state == PsychologicalState.REVENGE_TRADING:
            base_multiplier *= 0.3
        elif psych_state.current_state == PsychologicalState.CONFIDENT:
            base_multiplier *= 1.1
        
        # Stress level adjustments
        if psych_state.stress_level > 7.0:
            base_multiplier *= 0.6
        
        # Ensure reasonable bounds
        return max(0.1, min(2.0, base_multiplier))
    
    # Helper methods for analysis
    def _count_consecutive_losses(self, trades: List[TradePattern]) -> int:
        """Count consecutive losses from most recent trades"""
        consecutive = 0
        for trade in reversed(trades):
            if trade.outcome == "loss":
                consecutive += 1
            else:
                break
        return consecutive
    
    def _count_trades_today(self) -> int:
        """Count trades executed today"""
        today = datetime.now().date()
        return len([t for t in self.trade_history if t.timestamp.date() == today])
    
    def _calculate_stress_level(self, recent_trades: List[TradePattern], user_context: Dict) -> float:
        """Calculate current stress level based on trading behavior"""
        base_stress = 3.0
        
        # Recent losses increase stress
        loss_count = len([t for t in recent_trades if t.outcome == "loss"])
        base_stress += (loss_count / len(recent_trades)) * 4.0
        
        # Consecutive losses increase stress exponentially
        consecutive_losses = self._count_consecutive_losses(recent_trades)
        base_stress += min(4.0, consecutive_losses * 1.5)
        
        # Overtrading increases stress
        trades_today = self._count_trades_today()
        if trades_today > 5:
            base_stress += (trades_today - 5) * 0.5
        
        return min(10.0, base_stress)
    
    def _calculate_confidence_level(self, recent_trades: List[TradePattern]) -> float:
        """Calculate confidence level based on recent performance"""
        if not recent_trades:
            return 5.0
        
        win_rate = len([t for t in recent_trades if t.outcome == "win"]) / len(recent_trades)
        avg_pnl = statistics.mean([t.pnl_percent for t in recent_trades if t.pnl_percent != 0])
        
        confidence = 5.0 + (win_rate - 0.5) * 8.0 + (avg_pnl / 2.0)
        return max(1.0, min(10.0, confidence))
    
    def _predict_drawdown_risk(self, signal: Dict, user_context: Dict) -> float:
        """Predict drawdown risk for this trade"""
        # Simplified implementation - would use ML model in production
        symbol = signal.get("symbol", "")
        tcs_score = signal.get("tcs_score", 75)
        
        # Base risk from symbol volatility
        symbol_risk = {
            "XAUUSD": 8.0, "GBPJPY": 7.0, "EURJPY": 6.0,
            "GBPUSD": 5.0, "EURUSD": 4.0, "USDJPY": 4.5
        }.get(symbol, 5.0)
        
        # Adjust for TCS score
        tcs_adjustment = max(0, (75 - tcs_score) / 10)
        
        return min(10.0, symbol_risk + tcs_adjustment)
    
    def _detect_correlation_storm_risk(self, signal: Dict) -> float:
        """Detect risk of correlation storm (multiple pairs moving together)"""
        # Simplified - would analyze real correlation data
        symbol = signal.get("symbol", "")
        
        # Check for high-correlation periods
        high_correlation_symbols = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"]
        if symbol in high_correlation_symbols:
            return 6.0  # Moderate correlation risk
        
        return 3.0  # Low correlation risk
    
    def _calculate_overexposure_risk(self, signal: Dict, user_context: Dict) -> float:
        """Calculate overexposure risk"""
        current_exposure = user_context.get("total_exposure_percent", 0)
        proposed_trade_size = signal.get("lot_size", 0.01) * 1000  # Convert to risk units
        
        if current_exposure + proposed_trade_size > 15:
            return 8.0  # High overexposure risk
        elif current_exposure + proposed_trade_size > 10:
            return 5.0  # Moderate risk
        
        return 2.0  # Low risk
    
    def _calculate_psychological_risk_factor(self, user_context: Dict) -> float:
        """Calculate risk from psychological factors"""
        if len(self.psychological_history) == 0:
            return 3.0
        
        latest_psych = self.psychological_history[-1]
        
        risk_factor = 3.0  # Base
        risk_factor += (latest_psych.stress_level - 5.0) * 0.5
        risk_factor += latest_psych.revenge_trading_risk * 0.3
        risk_factor += latest_psych.overtrading_risk * 0.2
        
        return min(10.0, max(0.0, risk_factor))
    
    def _has_symbol_weakness(self, symbol: str) -> bool:
        """Check if user has weakness with specific symbol"""
        symbol_trades = [t for t in self.trade_history[-20:] if t.symbol == symbol]
        if len(symbol_trades) < 3:
            return False
        
        win_rate = len([t for t in symbol_trades if t.outcome == "win"]) / len(symbol_trades)
        return win_rate < 0.4
    
    def _has_symbol_strength(self, symbol: str) -> bool:
        """Check if user has strength with specific symbol"""
        symbol_trades = [t for t in self.trade_history[-20:] if t.symbol == symbol]
        if len(symbol_trades) < 3:
            return False
        
        win_rate = len([t for t in symbol_trades if t.outcome == "win"]) / len(symbol_trades)
        return win_rate > 0.7
    
    def _get_symbol_avg_return(self, symbol: str) -> float:
        """Get average return for symbol"""
        symbol_trades = [t for t in self.trade_history[-10:] if t.symbol == symbol and t.outcome == "win"]
        if not symbol_trades:
            return 0.0
        
        return statistics.mean([t.pnl_percent for t in symbol_trades])
    
    def _predict_max_drawdown(self, signal: Dict, user_context: Dict) -> float:
        """Predict maximum drawdown for this trade"""
        # Simplified prediction - would use sophisticated ML model
        base_dd = signal.get("risk_percent", 2.0) * 2.5  # Assume 2.5x risk as max DD
        
        # Adjust for user's psychological state
        if len(self.psychological_history) > 0:
            latest_psych = self.psychological_history[-1]
            if latest_psych.current_state == PsychologicalState.REVENGE_TRADING:
                base_dd *= 2.0
            elif latest_psych.stress_level > 7.0:
                base_dd *= 1.5
        
        return min(20.0, base_dd)
    
    def _generate_risk_recommendation(self, risk_level: RiskLevel, risk_scores: List[float]) -> str:
        """Generate risk management recommendation"""
        if risk_level == RiskLevel.EXTREME:
            return "❌ BLOCK TRADE: Risk too high. Wait for better setup."
        elif risk_level == RiskLevel.HIGH:
            return "⚠️ REDUCE SIZE: Cut position to 50%. High risk detected."
        elif risk_level == RiskLevel.MODERATE:
            return "⚖️ PROCEED CAUTIOUSLY: Normal size OK with tight stops."
        else:
            return "✅ GREEN LIGHT: Low risk. Consider slightly larger position."
    
    def _generate_post_trade_insights(self, trade: TradePattern):
        """Generate insights after trade completion"""
        insights = []
        
        # Performance insights
        if trade.outcome == "win" and trade.pnl_percent > 3.0:
            insights.append(CoachingInsight(
                category="performance",
                insight=f"Excellent execution on {trade.symbol}! +{trade.pnl_percent:.1f}%",
                actionable_advice="Analyze what made this trade successful. Look for similar setups.",
                priority="medium",
                based_on_trades=[str(trade.timestamp)],
                confidence=0.8
            ))
        elif trade.outcome == "loss" and trade.hold_time_minutes < 10:
            insights.append(CoachingInsight(
                category="psychology",
                insight="Quick exit on loss suggests good discipline or possible fear",
                actionable_advice="Review if exit was based on analysis or emotion",
                priority="high",
                based_on_trades=[str(trade.timestamp)],
                confidence=0.7
            ))
        
        self.coaching_history.extend(insights)
    
    def _get_trade_recommendation(self, signal: Dict, psych_state: PsychologicalProfile, 
                                risk_prediction: RiskPrediction) -> str:
        """Get overall trade recommendation"""
        
        # Block trades for extreme conditions
        if psych_state.current_state == PsychologicalState.REVENGE_TRADING:
            return "BLOCK - Revenge trading intervention required"
        
        if risk_prediction.overall_risk_level == RiskLevel.EXTREME:
            return "BLOCK - Risk level too high"
        
        # Conditional approvals
        if risk_prediction.overall_risk_level == RiskLevel.HIGH:
            return "CONDITIONAL - Reduce position size by 50%"
        
        if psych_state.stress_level > 7.0:
            return "CONDITIONAL - High stress detected, consider break"
        
        # Full approval
        tcs_score = signal.get("tcs_score", 0)
        if tcs_score > 85 and risk_prediction.overall_risk_level == RiskLevel.LOW:
            return "STRONG BUY - High probability, low risk"
        elif tcs_score > 75:
            return "BUY - Good setup with manageable risk"
        else:
            return "WEAK - Consider waiting for better setup"
    
    def _load_user_data(self):
        """Load user's trading history and psychological profile"""
        try:
            # In production, load from database
            # For now, initialize empty
            logger.info(f"Loaded trading data for user {self.user_id}")
        except Exception as e:
            logger.warning(f"Could not load user data: {e}")
    
    def _save_user_data(self):
        """Save user's trading data and insights"""
        try:
            # In production, save to database
            logger.debug(f"Saved trading data for user {self.user_id}")
        except Exception as e:
            logger.error(f"Could not save user data: {e}")
    
    def get_coaching_summary(self) -> Dict[str, Any]:
        """Get summary of coaching insights and user progress"""
        recent_trades = self.trade_history[-20:] if self.trade_history else []
        latest_psych = self.psychological_history[-1] if self.psychological_history else None
        
        return {
            "user_id": self.user_id,
            "total_trades_analyzed": len(self.trade_history),
            "recent_performance": {
                "win_rate": len([t for t in recent_trades if t.outcome == "win"]) / max(len(recent_trades), 1) * 100,
                "avg_pnl": statistics.mean([t.pnl_percent for t in recent_trades if t.pnl_percent != 0]) if recent_trades else 0,
                "trades_last_30_days": len([t for t in recent_trades if (datetime.now() - t.timestamp).days <= 30])
            },
            "psychological_state": {
                "current_state": latest_psych.current_state.value if latest_psych else "neutral",
                "stress_level": latest_psych.stress_level if latest_psych else 5.0,
                "confidence_level": latest_psych.confidence_level if latest_psych else 5.0,
                "intervention_active": latest_psych.intervention_needed if latest_psych else False
            },
            "top_insights": [asdict(insight) for insight in self.coaching_history[-5:]],
            "areas_for_improvement": self._identify_improvement_areas(),
            "strengths": self._identify_strengths()
        }
    
    def _identify_improvement_areas(self) -> List[str]:
        """Identify areas where user can improve"""
        areas = []
        
        if len(self.trade_history) < 10:
            return ["Build more trading experience", "Establish consistent patterns"]
        
        recent_trades = self.trade_history[-20:]
        
        # Check win rate
        win_rate = len([t for t in recent_trades if t.outcome == "win"]) / len(recent_trades)
        if win_rate < 0.5:
            areas.append("Improve trade selection criteria")
        
        # Check hold times
        avg_hold_time = statistics.mean([t.hold_time_minutes for t in recent_trades if t.hold_time_minutes > 0])
        if avg_hold_time < 15:
            areas.append("Consider longer hold times for trend development")
        
        # Check psychological patterns
        if len(self.psychological_history) > 5:
            stress_levels = [p.stress_level for p in self.psychological_history[-5:]]
            if statistics.mean(stress_levels) > 6.0:
                areas.append("Stress management and emotional control")
        
        return areas[:3]  # Top 3 areas
    
    def _identify_strengths(self) -> List[str]:
        """Identify user's trading strengths"""
        strengths = []
        
        if len(self.trade_history) < 5:
            return ["Building foundation", "Learning discipline"]
        
        recent_trades = self.trade_history[-20:]
        
        # Check consistency
        if len(set(t.symbol for t in recent_trades)) <= 5:
            strengths.append("Focused on familiar currency pairs")
        
        # Check risk management
        if all(abs(t.pnl_percent) <= 5.0 for t in recent_trades if t.pnl_percent != 0):
            strengths.append("Good risk management discipline")
        
        # Check psychological stability
        if len(self.psychological_history) > 3:
            recent_psych = self.psychological_history[-3:]
            if all(p.stress_level <= 6.0 for p in recent_psych):
                strengths.append("Emotional stability under pressure")
        
        return strengths[:3]  # Top 3 strengths

# Helper function for integration
def get_ai_coach(user_id: str) -> AITradingCoach:
    """Get or create AI trading coach for user"""
    # In production, would use caching/singleton pattern
    return AITradingCoach(user_id)