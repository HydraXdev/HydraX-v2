#!/usr/bin/env python3
"""
AI Integration Patch for BITTEN Production Bot
Adds AI coaching and institutional intelligence to existing fire commands
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AIIntegrationPatch:
    """
    Patch to integrate AI systems with existing BITTEN bot
    Minimal integration that enhances without breaking existing functionality
    """
    
    def __init__(self):
        self.ai_coach_available = False
        self.institutional_intel_available = False
        
        # Try to import AI systems
        try:
            from .ai_trading_coach import get_ai_coach
            from .institutional_intelligence import get_institutional_intelligence
            from .enhanced_fire_router import get_enhanced_fire_router
            
            self.get_ai_coach = get_ai_coach
            self.get_institutional_intelligence = get_institutional_intelligence
            self.get_enhanced_fire_router = get_enhanced_fire_router
            
            self.ai_coach_available = True
            self.institutional_intel_available = True
            
            logger.info("✅ AI systems successfully imported and ready")
            
        except ImportError as e:
            logger.warning(f"⚠️ AI systems not available: {e}")
    
    def enhance_fire_command(self, user_id: str, signal_data: Dict[str, Any], 
                           user_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Enhance fire command with AI analysis
        Returns enhanced response with AI insights
        """
        
        if not self.ai_coach_available:
            return {"ai_enhanced": False, "message": "AI systems not available"}
        
        try:
            # Get AI coach for user
            ai_coach = self.get_ai_coach(user_id)
            
            # Get institutional intelligence
            institutional_intel = self.get_institutional_intelligence()
            
            # Prepare context
            user_context = self._prepare_user_context(user_id, user_profile)
            
            # Run AI analysis
            coaching_analysis = ai_coach.analyze_trade_request(signal_data, user_context)
            institutional_analysis = institutional_intel.analyze_market_structure(
                signal_data.get("symbol", "EURUSD")
            )
            
            # Generate AI-enhanced response
            ai_response = self._generate_ai_response(
                signal_data, coaching_analysis, institutional_analysis
            )
            
            return {
                "ai_enhanced": True,
                "coaching_analysis": coaching_analysis,
                "institutional_analysis": institutional_analysis,
                "ai_response": ai_response,
                "intervention_needed": coaching_analysis.get("psychological_state", {}).get("intervention_needed", False),
                "position_adjustment": coaching_analysis.get("position_size_adjustment", 1.0)
            }
            
        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
            return {"ai_enhanced": False, "error": str(e)}
    
    def generate_pre_fire_analysis(self, user_id: str, signal_data: Dict[str, Any]) -> str:
        """
        Generate pre-fire analysis message for Telegram
        """
        
        if not self.ai_coach_available:
            return ""
        
        try:
            enhancement = self.enhance_fire_command(user_id, signal_data)
            
            if not enhancement.get("ai_enhanced"):
                return ""
            
            # Build analysis message
            message_parts = []
            
            # Psychological state
            psych_state = enhancement["coaching_analysis"].get("psychological_state", {})
            if psych_state.get("intervention_needed"):
                message_parts.append(f"🧠 **PSYCHOLOGICAL ALERT**: {psych_state.get('intervention_message', 'Intervention recommended')}")
            else:
                state = psych_state.get("current_state", "neutral").replace("_", " ").title()
                stress = psych_state.get("stress_level", 5.0)
                confidence = psych_state.get("confidence_level", 5.0)
                message_parts.append(f"🧠 **Mental State**: {state} | Stress: {stress:.1f}/10 | Confidence: {confidence:.1f}/10")
            
            # Risk assessment
            risk_assessment = enhancement["coaching_analysis"].get("risk_assessment", {})
            risk_level = risk_assessment.get("overall_level", "moderate").upper()
            if risk_level in ["HIGH", "EXTREME"]:
                message_parts.append(f"⚠️ **RISK ALERT**: {risk_level} risk detected")
            else:
                message_parts.append(f"⚖️ **Risk Level**: {risk_level}")
            
            # Institutional intelligence
            institutional = enhancement["institutional_analysis"]
            intel_score = institutional.get("overall_intelligence_score", 0.5)
            smart_money = institutional.get("smart_money", {})
            if smart_money.get("confidence", 0) > 0.7:
                action = smart_money.get("current_activity", "activity").replace("_", " ").title()
                message_parts.append(f"🏛️ **Smart Money**: {action} detected ({smart_money.get('confidence', 0):.0%} confidence)")
            
            # Position adjustment
            position_adj = enhancement.get("position_adjustment", 1.0)
            if position_adj != 1.0:
                if position_adj < 1.0:
                    message_parts.append(f"📉 **AI Recommendation**: Reduce position to {position_adj:.0%} of normal size")
                else:
                    message_parts.append(f"📈 **AI Recommendation**: Increase position to {position_adj:.0%} of normal size")
            
            # Coaching advice
            advice = enhancement["coaching_analysis"].get("personalized_advice", {})
            pre_trade_advice = advice.get("pre_trade_coaching")
            if pre_trade_advice:
                message_parts.append(f"🎯 **Coach**: {pre_trade_advice}")
            
            if message_parts:
                return "\n\n🤖 **AI ANALYSIS**\n" + "\n".join(message_parts)
            
            return ""
            
        except Exception as e:
            logger.error(f"Failed to generate pre-fire analysis: {e}")
            return ""
    
    def check_intervention_needed(self, user_id: str, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if AI intervention is needed before trade execution
        """
        
        if not self.ai_coach_available:
            return {"intervention_needed": False}
        
        try:
            enhancement = self.enhance_fire_command(user_id, signal_data)
            
            if not enhancement.get("ai_enhanced"):
                return {"intervention_needed": False}
            
            # Check for psychological interventions
            psych_state = enhancement["coaching_analysis"].get("psychological_state", {})
            if psych_state.get("intervention_needed", False):
                return {
                    "intervention_needed": True,
                    "intervention_type": "psychological",
                    "message": psych_state.get("intervention_message", "Psychological intervention required"),
                    "block_trade": True
                }
            
            # Check for risk interventions
            risk_assessment = enhancement["coaching_analysis"].get("risk_assessment", {})
            if risk_assessment.get("overall_level") == "extreme":
                return {
                    "intervention_needed": True,
                    "intervention_type": "risk",
                    "message": "Extreme risk level detected - trade blocked for safety",
                    "block_trade": True
                }
            
            return {"intervention_needed": False}
            
        except Exception as e:
            logger.error(f"Intervention check failed: {e}")
            return {"intervention_needed": False}
    
    def generate_post_fire_insights(self, user_id: str, trade_result: Dict[str, Any]) -> str:
        """
        Generate post-fire insights for learning
        """
        
        if not self.ai_coach_available:
            return ""
        
        try:
            # Record trade for AI learning
            ai_coach = self.get_ai_coach(user_id)
            ai_coach.record_trade_execution(trade_result)
            
            # Generate insights
            insights = []
            
            # Basic execution feedback
            if trade_result.get("success", False):
                insights.append("✅ Trade executed successfully - AI learning from this execution")
            else:
                insights.append("❌ Trade execution failed - reviewing for pattern analysis")
            
            # Symbol-specific feedback
            symbol = trade_result.get("symbol", "")
            if symbol:
                coach_summary = ai_coach.get_coaching_summary()
                recent_perf = coach_summary.get("recent_performance", {})
                if recent_perf.get("trades_last_30_days", 0) > 5:
                    win_rate = recent_perf.get("win_rate", 50)
                    insights.append(f"📊 Your recent win rate: {win_rate:.0f}% over {recent_perf.get('trades_last_30_days')} trades")
            
            if insights:
                return "\n\n🤖 **AI INSIGHTS**\n" + "\n".join(insights)
            
            return ""
            
        except Exception as e:
            logger.error(f"Failed to generate post-fire insights: {e}")
            return ""
    
    def get_user_coaching_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get current coaching status for user
        """
        
        if not self.ai_coach_available:
            return {"available": False}
        
        try:
            ai_coach = self.get_ai_coach(user_id)
            summary = ai_coach.get_coaching_summary()
            
            return {
                "available": True,
                "total_trades": summary.get("total_trades_analyzed", 0),
                "recent_performance": summary.get("recent_performance", {}),
                "psychological_state": summary.get("psychological_state", {}),
                "top_insights": summary.get("top_insights", []),
                "areas_for_improvement": summary.get("areas_for_improvement", []),
                "strengths": summary.get("strengths", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get coaching status: {e}")
            return {"available": False, "error": str(e)}
    
    def get_market_intelligence_summary(self) -> str:
        """
        Get market intelligence summary for display
        """
        
        if not self.institutional_intel_available:
            return "📊 Market intelligence not available"
        
        try:
            institutional_intel = self.get_institutional_intelligence()
            
            # Get overview for major pairs
            major_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
            summaries = []
            
            for pair in major_pairs[:2]:  # Limit to 2 pairs for message length
                summary = institutional_intel.get_institutional_summary(pair)
                grade = summary.get("intelligence_grade", "C")
                bias = summary.get("institutional_bias", "neutral")
                
                summaries.append(f"{pair}: Grade {grade} | {bias.title()} bias")
            
            if summaries:
                return "📊 **MARKET INTEL**\n" + "\n".join(summaries)
            
            return "📊 Market intelligence: Normal activity levels"
            
        except Exception as e:
            logger.error(f"Failed to get market intelligence: {e}")
            return "📊 Market intelligence temporarily unavailable"
    
    def _prepare_user_context(self, user_id: str, user_profile: Optional[Dict]) -> Dict[str, Any]:
        """Prepare user context for AI analysis"""
        return {
            "user_id": user_id,
            "account_balance": user_profile.get("account_balance", 10000) if user_profile else 10000,
            "tier": user_profile.get("tier", "nibbler") if user_profile else "nibbler",
            "recent_pnl": user_profile.get("recent_pnl", 0) if user_profile else 0,
            "open_positions": user_profile.get("open_positions", 0) if user_profile else 0
        }
    
    def _generate_ai_response(self, signal_data: Dict, coaching_analysis: Dict, 
                            institutional_analysis: Dict) -> Dict[str, Any]:
        """Generate comprehensive AI response"""
        return {
            "summary": "AI analysis completed",
            "confidence": coaching_analysis.get("risk_assessment", {}).get("confidence", 0.5),
            "recommendation": coaching_analysis.get("trade_recommendation", "proceed"),
            "key_factors": [
                "Psychological state analyzed",
                "Risk assessment completed", 
                "Institutional intelligence gathered"
            ]
        }

# Global instance for easy access
ai_integration = AIIntegrationPatch()

# Helper functions for bot integration
def enhance_fire_command(user_id: str, signal_data: Dict[str, Any], 
                        user_profile: Optional[Dict] = None) -> Dict[str, Any]:
    """Helper function for fire command enhancement"""
    return ai_integration.enhance_fire_command(user_id, signal_data, user_profile)

def generate_pre_fire_analysis(user_id: str, signal_data: Dict[str, Any]) -> str:
    """Helper function for pre-fire analysis"""
    return ai_integration.generate_pre_fire_analysis(user_id, signal_data)

def check_intervention_needed(user_id: str, signal_data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function for intervention check"""
    return ai_integration.check_intervention_needed(user_id, signal_data)

def generate_post_fire_insights(user_id: str, trade_result: Dict[str, Any]) -> str:
    """Helper function for post-fire insights"""
    return ai_integration.generate_post_fire_insights(user_id, trade_result)

def get_user_coaching_status(user_id: str) -> Dict[str, Any]:
    """Helper function for coaching status"""
    return ai_integration.get_user_coaching_status(user_id)

def get_market_intelligence_summary() -> str:
    """Helper function for market intelligence"""
    return ai_integration.get_market_intelligence_summary()