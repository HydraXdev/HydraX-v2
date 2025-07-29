#!/usr/bin/env python3
"""
Enhanced Fire Router with AI Coach and Institutional Intelligence Integration
Combines existing fire router with new AI capabilities
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import existing fire router
from .fire_router import FireRouter, TradeRequest, TradeExecutionResult, ExecutionMode

# Import new AI systems
from .ai_trading_coach import get_ai_coach, AITradingCoach
from .institutional_intelligence import get_institutional_intelligence, InstitutionalIntelligence

logger = logging.getLogger(__name__)

class EnhancedFireRouter(FireRouter):
    """
    Enhanced Fire Router with AI Trading Coach and Institutional Intelligence
    Provides comprehensive trade analysis before execution
    """
    
    def __init__(self, api_endpoint: str = "api.broker.local",
                 execution_mode: ExecutionMode = ExecutionMode.LIVE):
        
        # Initialize base fire router
        super().__init__(api_endpoint, execution_mode)
        
        # Initialize AI systems
        self.institutional_intelligence = get_institutional_intelligence()
        self.user_coaches: Dict[str, AITradingCoach] = {}
        
        # Enhanced statistics
        self.ai_stats = {
            "trades_analyzed": 0,
            "interventions_triggered": 0,
            "psychological_blocks": 0,
            "risk_reductions": 0,
            "ai_coaching_active": True
        }
        
        logger.info("Enhanced Fire Router initialized with AI capabilities")
    
    def execute_trade_request_with_ai(self, request: TradeRequest, user_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute trade request with comprehensive AI analysis
        Returns both execution result and AI insights
        """
        execution_start = datetime.now()
        
        # Get or create AI coach for user
        ai_coach = self._get_user_coach(request.user_id)
        
        # 1. PRE-TRADE AI ANALYSIS
        logger.info(f"🧠 Starting AI analysis for {request.symbol} {request.direction.value}")
        
        # Prepare context for AI analysis
        user_context = self._prepare_user_context(request, user_profile)
        signal_data = self._prepare_signal_data(request)
        
        # AI Coach Analysis
        coaching_analysis = ai_coach.analyze_trade_request(signal_data, user_context)
        
        # Institutional Intelligence Analysis
        institutional_analysis = self.institutional_intelligence.analyze_market_structure(request.symbol)
        
        # 2. DECISION LOGIC WITH AI INPUTS
        ai_decision = self._make_ai_enhanced_decision(request, coaching_analysis, institutional_analysis)
        
        # Update AI statistics
        self.ai_stats["trades_analyzed"] += 1
        
        # 3. HANDLE AI INTERVENTIONS
        if ai_decision["intervention_needed"]:
            self.ai_stats["interventions_triggered"] += 1
            
            if ai_decision["intervention_type"] == "psychological_block":
                self.ai_stats["psychological_blocks"] += 1
                return self._create_intervention_response(request, ai_decision, coaching_analysis)
            
            elif ai_decision["intervention_type"] == "risk_reduction":
                self.ai_stats["risk_reductions"] += 1
                # Modify request based on AI recommendation
                request = self._apply_risk_reduction(request, ai_decision)
        
        # 4. EXECUTE TRADE WITH AI ENHANCEMENTS
        execution_result = self.execute_trade_request(request, user_profile)
        
        # 5. POST-EXECUTION AI PROCESSING
        if execution_result.success:
            # Record trade for AI learning
            trade_data = {
                "symbol": request.symbol,
                "direction": request.direction.value,
                "volume": request.volume,
                "tcs_score": request.tcs_score,
                "user_context": user_context,
                "execution_result": execution_result.__dict__
            }
            ai_coach.record_trade_execution(trade_data)
        
        # 6. COMPILE COMPREHENSIVE RESPONSE
        return {
            "execution_result": execution_result.__dict__,
            "ai_analysis": {
                "coaching_insights": coaching_analysis,
                "institutional_intelligence": institutional_analysis,
                "ai_decision": ai_decision,
                "position_adjustment": ai_decision.get("position_adjustment", 1.0),
                "confidence_score": ai_decision.get("confidence", 0.5)
            },
            "enhanced_recommendations": self._generate_enhanced_recommendations(
                coaching_analysis, institutional_analysis
            ),
            "learning_insights": self._generate_learning_insights(
                request, coaching_analysis, institutional_analysis
            ),
            "execution_metadata": {
                "ai_enhanced": True,
                "analysis_time": (datetime.now() - execution_start).total_seconds(),
                "intervention_applied": ai_decision["intervention_needed"],
                "institutional_grade": institutional_analysis.get("overall_intelligence_score", 0.5)
            }
        }
    
    def _get_user_coach(self, user_id: str) -> AITradingCoach:
        """Get or create AI coach for user"""
        if user_id not in self.user_coaches:
            self.user_coaches[user_id] = get_ai_coach(user_id)
            logger.info(f"Created AI coach for user {user_id}")
        
        return self.user_coaches[user_id]
    
    def _prepare_user_context(self, request: TradeRequest, user_profile: Optional[Dict]) -> Dict[str, Any]:
        """Prepare user context for AI analysis"""
        return {
            "user_id": request.user_id,
            "account_balance": user_profile.get("account_balance", 10000) if user_profile else 10000,
            "tier": user_profile.get("tier", "nibbler") if user_profile else "nibbler",
            "recent_pnl": user_profile.get("recent_pnl", 0) if user_profile else 0,
            "open_positions": user_profile.get("open_positions", 0) if user_profile else 0,
            "shots_today": user_profile.get("shots_today", 0) if user_profile else 0,
            "total_exposure_percent": user_profile.get("total_exposure_percent", 0) if user_profile else 0,
            "last_trade_time": user_profile.get("last_trade_time") if user_profile else None,
            "current_streak": user_profile.get("current_streak", 0) if user_profile else 0
        }
    
    def _prepare_signal_data(self, request: TradeRequest) -> Dict[str, Any]:
        """Prepare signal data for AI analysis"""
        return {
            "symbol": request.symbol,
            "direction": request.direction.value,
            "volume": request.volume,
            "tcs_score": request.tcs_score,
            "stop_loss": request.stop_loss,
            "take_profit": request.take_profit,
            "risk_percent": 2.0,  # Default risk
            "lot_size": request.volume,
            "mission_id": request.mission_id,
            "comment": request.comment
        }
    
    def _make_ai_enhanced_decision(self, request: TradeRequest, coaching_analysis: Dict, 
                                 institutional_analysis: Dict) -> Dict[str, Any]:
        """Make trading decision with AI inputs"""
        
        decision = {
            "intervention_needed": False,
            "intervention_type": None,
            "intervention_message": "",
            "position_adjustment": 1.0,
            "confidence": 0.5,
            "recommendation": "proceed"
        }
        
        # Check psychological interventions
        psych_state = coaching_analysis.get("psychological_state", {})
        if psych_state.get("intervention_needed", False):
            decision.update({
                "intervention_needed": True,
                "intervention_type": "psychological_block",
                "intervention_message": psych_state.get("intervention_message", "Psychological intervention required"),
                "recommendation": "block"
            })
            return decision
        
        # Check risk interventions
        risk_assessment = coaching_analysis.get("risk_assessment", {})
        if risk_assessment.get("overall_level") == "extreme":
            decision.update({
                "intervention_needed": True,
                "intervention_type": "risk_reduction",
                "intervention_message": "Extreme risk detected - reducing position size",
                "position_adjustment": 0.25,
                "recommendation": "reduce"
            })
            return decision
        elif risk_assessment.get("overall_level") == "high":
            decision.update({
                "intervention_needed": True,
                "intervention_type": "risk_reduction",
                "intervention_message": "High risk detected - reducing position size",
                "position_adjustment": 0.5,
                "recommendation": "reduce"
            })
            return decision
        
        # Apply position size adjustments from AI
        position_adjustment = coaching_analysis.get("position_size_adjustment", 1.0)
        
        # Factor in institutional intelligence
        institutional_score = institutional_analysis.get("overall_intelligence_score", 0.5)
        if institutional_score > 0.8:
            position_adjustment *= 1.2  # Increase size for high institutional confidence
        elif institutional_score < 0.3:
            position_adjustment *= 0.8  # Decrease size for low institutional confidence
        
        # Apply correlation storm adjustments
        correlation_data = institutional_analysis.get("correlation", {})
        if correlation_data.get("state") == "correlation_storm":
            position_adjustment *= 0.6  # Reduce size during correlation storms
        
        decision.update({
            "position_adjustment": max(0.1, min(2.0, position_adjustment)),
            "confidence": (institutional_score + risk_assessment.get("confidence", 0.5)) / 2,
            "recommendation": coaching_analysis.get("trade_recommendation", "proceed")
        })
        
        return decision
    
    def _create_intervention_response(self, request: TradeRequest, ai_decision: Dict, 
                                    coaching_analysis: Dict) -> Dict[str, Any]:
        """Create response for AI intervention"""
        
        # Create blocked execution result
        blocked_result = TradeExecutionResult(
            success=False,
            message=f"🛑 AI INTERVENTION: {ai_decision['intervention_message']}",
            error_code="AI_INTERVENTION",
            execution_time_ms=50
        )
        
        return {
            "execution_result": blocked_result.__dict__,
            "ai_analysis": {
                "coaching_insights": coaching_analysis,
                "intervention_active": True,
                "intervention_type": ai_decision["intervention_type"],
                "intervention_message": ai_decision["intervention_message"]
            },
            "enhanced_recommendations": [
                "Take a break and assess your psychological state",
                "Review your trading plan and risk management rules",
                "Consider the AI coaching feedback before next trade"
            ],
            "execution_metadata": {
                "ai_enhanced": True,
                "intervention_applied": True,
                "blocked_by_ai": True
            }
        }
    
    def _apply_risk_reduction(self, request: TradeRequest, ai_decision: Dict) -> TradeRequest:
        """Apply AI-recommended risk reduction to trade request"""
        
        adjustment = ai_decision.get("position_adjustment", 1.0)
        
        # Adjust position size
        request.volume = round(request.volume * adjustment, 2)
        
        # Ensure minimum position size
        request.volume = max(0.01, request.volume)
        
        # Update comment to reflect AI adjustment
        request.comment = f"{request.comment} [AI:{adjustment:.1f}x]"
        
        logger.info(f"Applied AI risk reduction: {adjustment:.1f}x adjustment to {request.symbol}")
        
        return request
    
    def _generate_enhanced_recommendations(self, coaching_analysis: Dict, 
                                         institutional_analysis: Dict) -> List[str]:
        """Generate enhanced recommendations combining AI insights"""
        
        recommendations = []
        
        # Coaching recommendations
        coaching_advice = coaching_analysis.get("personalized_advice", {})
        for advice_type, advice in coaching_advice.items():
            if advice and advice_type in ["pre_trade_coaching", "psychological_guidance"]:
                recommendations.append(advice)
        
        # Institutional recommendations
        institutional_summary = self.institutional_intelligence.get_institutional_summary(
            institutional_analysis.get("symbol", "EURUSD")
        )
        
        for insight in institutional_summary.get("key_insights", []):
            recommendations.append(f"📊 INSTITUTIONAL: {insight}")
        
        for alert in institutional_summary.get("risk_alerts", []):
            recommendations.append(alert)
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _generate_learning_insights(self, request: TradeRequest, coaching_analysis: Dict, 
                                  institutional_analysis: Dict) -> List[str]:
        """Generate learning insights for user education"""
        
        insights = []
        
        # TCS-based insights
        tcs_score = request.tcs_score
        if tcs_score > 90:
            insights.append("🎯 Excellent signal quality - this is what to look for in future trades")
        elif tcs_score < 70:
            insights.append("⚠️ Lower TCS score - consider this for learning but with reduced size")
        
        # Psychological insights
        psych_state = coaching_analysis.get("psychological_state", {})
        current_state = psych_state.get("current_state", "neutral")
        if current_state != "neutral":
            insights.append(f"🧠 Current psychological state: {current_state.replace('_', ' ').title()}")
        
        # Institutional insights
        smart_money = institutional_analysis.get("smart_money", {})
        if smart_money.get("confidence", 0) > 0.7:
            action = smart_money.get("current_activity", "activity")
            insights.append(f"🏛️ Institutional {action} detected - learn to spot these patterns")
        
        # Risk management insights
        risk_level = coaching_analysis.get("risk_assessment", {}).get("overall_level", "moderate")
        if risk_level in ["high", "extreme"]:
            insights.append(f"⚖️ Risk level: {risk_level} - study why this setup is riskier")
        
        return insights[:4]  # Top 4 learning insights
    
    def get_enhanced_system_status(self) -> Dict[str, Any]:
        """Get enhanced system status including AI metrics"""
        
        base_status = self.get_system_status()
        
        # Add AI-specific metrics
        ai_metrics = {
            "ai_systems": {
                "coaching_active": self.ai_stats["ai_coaching_active"],
                "institutional_intelligence_active": True,
                "active_coaches": len(self.user_coaches)
            },
            "ai_statistics": self.ai_stats.copy(),
            "ai_performance": {
                "intervention_rate": (self.ai_stats["interventions_triggered"] / 
                                    max(self.ai_stats["trades_analyzed"], 1)) * 100,
                "psychological_intervention_rate": (self.ai_stats["psychological_blocks"] / 
                                                  max(self.ai_stats["trades_analyzed"], 1)) * 100,
                "risk_reduction_rate": (self.ai_stats["risk_reductions"] / 
                                      max(self.ai_stats["trades_analyzed"], 1)) * 100
            }
        }
        
        # Merge with base status
        enhanced_status = {**base_status, **ai_metrics}
        
        return enhanced_status
    
    def update_trade_outcome_with_ai(self, trade_id: str, outcome_data: Dict):
        """Update trade outcome and trigger AI learning"""
        
        # Find user from trade history
        user_id = None
        for trade in self.trade_history:
            if trade.get("mission_id") == trade_id:
                user_id = trade.get("user_id")
                break
        
        if user_id and user_id in self.user_coaches:
            # Update AI coach with outcome
            self.user_coaches[user_id].update_trade_outcome(trade_id, outcome_data)
            logger.info(f"Updated AI coach for user {user_id} with trade outcome")
    
    def get_user_coaching_summary(self, user_id: str) -> Dict[str, Any]:
        """Get AI coaching summary for specific user"""
        
        if user_id not in self.user_coaches:
            return {"error": "No AI coach data available for user"}
        
        coach = self.user_coaches[user_id]
        return coach.get_coaching_summary()
    
    def get_institutional_market_overview(self) -> Dict[str, Any]:
        """Get institutional intelligence overview for multiple pairs"""
        
        major_pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD"]
        overview = {}
        
        for pair in major_pairs:
            summary = self.institutional_intelligence.get_institutional_summary(pair)
            overview[pair] = {
                "intelligence_grade": summary["intelligence_grade"],
                "institutional_bias": summary["institutional_bias"],
                "key_insight": summary["key_insights"][0] if summary["key_insights"] else "No significant activity",
                "confidence": summary["confidence_level"]
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "market_overview": overview,
            "overall_market_state": self._assess_overall_market_state(overview)
        }
    
    def _assess_overall_market_state(self, overview: Dict[str, Any]) -> str:
        """Assess overall market state from institutional data"""
        
        grades = [data["intelligence_grade"] for data in overview.values()]
        confidence_levels = [data["confidence"] for data in overview.values()]
        
        a_grades = grades.count("A")
        avg_confidence = sum(confidence_levels) / len(confidence_levels)
        
        if a_grades >= 3 and avg_confidence > 0.8:
            return "High institutional activity across markets"
        elif a_grades >= 2 or avg_confidence > 0.7:
            return "Moderate institutional activity"
        else:
            return "Low institutional activity"

# Helper function for integration
def get_enhanced_fire_router(execution_mode: ExecutionMode = ExecutionMode.LIVE) -> EnhancedFireRouter:
    """Get enhanced fire router with AI capabilities"""
    return EnhancedFireRouter(execution_mode=execution_mode)