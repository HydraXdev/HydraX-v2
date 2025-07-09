"""
TCS Education System - Progressive Disclosure & Explanations
Helps users understand the Token Confidence Score algorithm
"""

import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class TCSEducation:
    """
    TCS Education System with progressive disclosure based on user level
    Maintains mystery while providing informative explanations
    """
    
    def __init__(self):
        self.tiers = {
            "novice": 1,      # Level 1-10: Basic understanding
            "apprentice": 2,  # Level 11-25: Intermediate concepts
            "trader": 3,      # Level 26-50: Advanced insights
            "master": 4,      # Level 51-75: Deep mechanics
            "legend": 5       # Level 76+: Full transparency
        }
        
        # Factor explanations with progressive detail levels
        self.factor_explanations = {
            "market_structure": {
                1: "Market patterns and trend quality",
                2: "Analyzes support/resistance levels and trend clarity",
                3: "Multi-timeframe structure alignment with Fibonacci levels",
                4: "Institutional order flow patterns and liquidity zones",
                5: "Smart money accumulation/distribution with volume profile analysis"
            },
            "timeframe_alignment": {
                1: "Multiple timeframe agreement",
                2: "Checks if M15, H1, H4, and Daily align",
                3: "Weighted confluence scoring across timeframes",
                4: "Fractal geometry patterns and cycle synchronization",
                5: "Harmonic timeframe resonance with volatility expansion"
            },
            "momentum": {
                1: "Market strength indicators",
                2: "RSI, MACD, and volume confirmation",
                3: "Momentum divergence detection and hidden signals",
                4: "Order flow momentum with delta analysis",
                5: "Proprietary momentum oscillator with AI enhancement"
            },
            "volatility": {
                1: "Market movement conditions",
                2: "ATR-based volatility and spread analysis",
                3: "Volatility regime detection and adaptation",
                4: "Options flow impact and implied volatility",
                5: "Volatility smile modeling with gamma exposure"
            },
            "session": {
                1: "Trading session timing",
                2: "London, NY, Tokyo session weighting",
                3: "Session overlap opportunities and liquidity",
                4: "Institutional activity patterns by session",
                5: "Algorithmic trading volume distribution analysis"
            },
            "liquidity": {
                1: "Market depth analysis",
                2: "Liquidity grab and stop hunt detection",
                3: "Order book imbalance and absorption",
                4: "Dark pool activity and block trade detection",
                5: "Microstructure analysis with HFT flow patterns"
            },
            "risk_reward": {
                1: "Trade quality assessment",
                2: "Risk/reward ratio optimization",
                3: "Dynamic R:R adjustment with market conditions",
                4: "Portfolio impact and correlation analysis",
                5: "Kelly criterion optimization with tail risk hedging"
            },
            "ai_sentiment": {
                1: "AI market analysis",
                2: "Machine learning sentiment scoring",
                3: "Neural network pattern recognition",
                4: "Multi-model ensemble with NLP analysis",
                5: "Quantum-inspired optimization algorithms"
            }
        }
        
        # Visual examples for each TCS tier
        self.visual_examples = {
            "hammer": {
                "range": "94-100",
                "description": "Elite setup with perfect confluence",
                "characteristics": [
                    "All timeframes aligned",
                    "Strong momentum confirmation", 
                    "Optimal session timing",
                    "High liquidity environment",
                    "4:1+ risk/reward ratio"
                ],
                "visual_cues": {
                    "color": "#00ff88",
                    "icon": "🔨",
                    "pattern": "Triple confluence at key level",
                    "example": "Major support bounce with volume spike during London open"
                }
            },
            "shadow_strike": {
                "range": "84-93",
                "description": "High probability institutional setup",
                "characteristics": [
                    "3+ timeframes aligned",
                    "Good momentum signals",
                    "Favorable session",
                    "Clear structure",
                    "3:1+ risk/reward"
                ],
                "visual_cues": {
                    "color": "#88ff00",
                    "icon": "⚡",
                    "pattern": "Breakout with retest confirmation",
                    "example": "Flag pattern completion with increasing volume"
                }
            },
            "scalp": {
                "range": "75-83",
                "description": "Quick intraday opportunity",
                "characteristics": [
                    "2+ timeframes aligned",
                    "Decent momentum",
                    "Active session",
                    "Clear levels",
                    "2:1+ risk/reward"
                ],
                "visual_cues": {
                    "color": "#ffaa00",
                    "icon": "🎯",
                    "pattern": "Range bounce or mini-breakout",
                    "example": "15-min range break during NY session"
                }
            },
            "watchlist": {
                "range": "65-74",
                "description": "Monitor for improvement",
                "characteristics": [
                    "Mixed signals",
                    "Weak momentum",
                    "Suboptimal timing",
                    "Unclear structure",
                    "1.5:1 risk/reward"
                ],
                "visual_cues": {
                    "color": "#ff6600",
                    "icon": "👁️",
                    "pattern": "Potential setup forming",
                    "example": "Consolidation near support, waiting for catalyst"
                }
            }
        }
        
        # Mystery elements that unlock with progression
        self.mystery_elements = {
            1: "The algorithm analyzes patterns beyond human perception...",
            2: "20+ factors work in harmony to predict market movements...",
            3: "Institutional order flow leaves traces only our AI can detect...",
            4: "Quantum probability models enhance traditional analysis...",
            5: "You've unlocked the full matrix. The market's secrets are yours..."
        }
        
    def get_tcs_explanation(self, user_level: int, factor: Optional[str] = None) -> Dict:
        """
        Get TCS explanation based on user level with progressive disclosure
        """
        tier = self._get_user_tier(user_level)
        
        if factor and factor in self.factor_explanations:
            detail_level = min(tier, 5)
            explanation = self.factor_explanations[factor][detail_level]
            
            return {
                "factor": factor,
                "explanation": explanation,
                "detail_level": detail_level,
                "unlock_next_at": self._get_next_unlock_level(user_level),
                "mystery_hint": self._get_mystery_hint(tier, factor)
            }
        
        # General TCS explanation
        return self._get_general_explanation(tier, user_level)
    
    def get_visual_example(self, tcs_score: float) -> Dict:
        """
        Get visual example for a given TCS score
        """
        if tcs_score >= 94:
            category = "hammer"
        elif tcs_score >= 84:
            category = "shadow_strike"
        elif tcs_score >= 75:
            category = "scalp"
        else:
            category = "watchlist"
            
        return self.visual_examples[category]
    
    def get_score_breakdown_explanation(self, breakdown: Dict, user_level: int) -> List[Dict]:
        """
        Explain each component of a TCS score breakdown
        """
        tier = self._get_user_tier(user_level)
        explanations = []
        
        for factor, score in breakdown.items():
            if factor in self.factor_explanations:
                explanation = self.factor_explanations[factor][min(tier, 5)]
                
                explanations.append({
                    "factor": factor,
                    "score": score,
                    "max_score": self._get_max_score_for_factor(factor),
                    "explanation": explanation,
                    "quality": self._assess_factor_quality(factor, score),
                    "improvement_tip": self._get_improvement_tip(factor, score, tier)
                })
                
        return explanations
    
    def get_interactive_tutorial(self, user_level: int) -> Dict:
        """
        Get interactive tutorial content based on user level
        """
        tier = self._get_user_tier(user_level)
        
        tutorials = {
            1: {
                "title": "Understanding TCS Basics",
                "lessons": [
                    "What is Token Confidence Score?",
                    "Reading score ranges (0-100)",
                    "Identifying trade quality tiers"
                ],
                "interactive_elements": [
                    "Score simulator",
                    "Basic pattern recognition",
                    "Risk/reward calculator"
                ]
            },
            2: {
                "title": "Intermediate TCS Analysis",
                "lessons": [
                    "Multi-factor scoring system",
                    "Timeframe confluence",
                    "Session-based optimization"
                ],
                "interactive_elements": [
                    "Factor weight explorer",
                    "Confluence detector",
                    "Session performance tracker"
                ]
            },
            3: {
                "title": "Advanced TCS Mastery",
                "lessons": [
                    "Institutional pattern detection",
                    "Liquidity analysis",
                    "AI sentiment integration"
                ],
                "interactive_elements": [
                    "Order flow visualizer",
                    "Liquidity heat map",
                    "AI prediction sandbox"
                ]
            },
            4: {
                "title": "Master Trader Insights",
                "lessons": [
                    "Market microstructure",
                    "Hidden divergences",
                    "Algorithmic edge detection"
                ],
                "interactive_elements": [
                    "Microstructure analyzer",
                    "Divergence scanner",
                    "Algorithm backtester"
                ]
            },
            5: {
                "title": "Legendary Status Achieved",
                "lessons": [
                    "Full algorithm transparency",
                    "Custom factor creation",
                    "AI model fine-tuning"
                ],
                "interactive_elements": [
                    "Algorithm customizer",
                    "Factor laboratory",
                    "AI training interface"
                ]
            }
        }
        
        return tutorials.get(tier, tutorials[1])
    
    def get_achievement_unlocks(self, user_level: int) -> List[Dict]:
        """
        Get list of unlocked features and upcoming unlocks
        """
        unlocks = []
        
        # Define unlock milestones
        milestones = [
            (5, "Basic TCS breakdown view", "See individual factor scores"),
            (10, "Score history tracking", "Track your TCS improvement over time"),
            (15, "Predictive scoring", "See how trades will affect your TCS"),
            (20, "Factor deep dive", "Detailed explanations for each factor"),
            (25, "Pattern library access", "View high-TCS pattern examples"),
            (30, "Custom alerts", "Set TCS threshold notifications"),
            (40, "AI insights", "Access AI-generated trade analysis"),
            (50, "Advanced metrics", "Unlock institutional-grade analytics"),
            (60, "Factor customization", "Adjust factor weights to your style"),
            (75, "Algorithm transparency", "See the full scoring algorithm"),
            (100, "Matrix mode", "Full market visualization suite")
        ]
        
        for level, feature, description in milestones:
            status = "unlocked" if user_level >= level else "locked"
            unlocks.append({
                "level": level,
                "feature": feature,
                "description": description,
                "status": status,
                "progress": min(100, (user_level / level) * 100) if status == "locked" else 100
            })
            
        return unlocks
    
    def generate_education_content(self, topic: str, user_level: int) -> Dict:
        """
        Generate educational content for specific topics
        """
        tier = self._get_user_tier(user_level)
        
        # Educational content templates
        content = {
            "tcs_overview": {
                "title": "Token Confidence Score Explained",
                "sections": self._get_overview_sections(tier),
                "quiz": self._generate_quiz(topic, tier),
                "next_lesson": self._get_next_lesson(topic, tier)
            },
            "factor_analysis": {
                "title": "Understanding TCS Factors",
                "sections": self._get_factor_sections(tier),
                "interactive": self._get_interactive_factor_explorer(tier),
                "case_studies": self._get_case_studies(tier)
            },
            "trading_examples": {
                "title": "Real Trading Scenarios",
                "examples": self._get_trading_examples(tier),
                "simulator": self._get_trade_simulator_config(tier),
                "best_practices": self._get_best_practices(tier)
            }
        }
        
        return content.get(topic, content["tcs_overview"])
    
    # Helper methods
    def _get_user_tier(self, level: int) -> int:
        """Determine user tier based on level"""
        if level >= 76:
            return 5
        elif level >= 51:
            return 4
        elif level >= 26:
            return 3
        elif level >= 11:
            return 2
        else:
            return 1
    
    def _get_next_unlock_level(self, current_level: int) -> int:
        """Get the next level where new content unlocks"""
        unlock_levels = [10, 25, 50, 75, 100]
        for level in unlock_levels:
            if current_level < level:
                return level
        return current_level
    
    def _get_mystery_hint(self, tier: int, factor: str) -> str:
        """Get a mysterious hint about the factor"""
        hints = {
            "market_structure": "Ancient patterns repeat in fractal dimensions...",
            "timeframe_alignment": "Time is an illusion, confluence is reality...",
            "momentum": "The force that moves markets leaves quantum traces...",
            "volatility": "Chaos theory meets predictable outcomes...",
            "session": "When titans trade, the algorithm listens...",
            "liquidity": "Dark pools hide secrets only we can illuminate...",
            "risk_reward": "Mathematics of the universe in every trade...",
            "ai_sentiment": "Neural pathways mirror market psychology..."
        }
        
        if tier >= 4:
            return f"{hints.get(factor, 'The truth is closer than you think...')} [Level {tier} insight unlocked]"
        else:
            return hints.get(factor, "Keep trading to unlock deeper mysteries...")
    
    def _get_general_explanation(self, tier: int, user_level: int) -> Dict:
        """Get general TCS explanation based on tier"""
        explanations = {
            1: {
                "title": "Token Confidence Score (TCS)",
                "description": "A proprietary scoring system (0-100) that analyzes multiple market factors to assess trade quality.",
                "factors_revealed": 3,
                "total_factors": "20+",
                "detail": "Higher scores indicate better trade setups with higher probability of success."
            },
            2: {
                "title": "Token Confidence Score (TCS) - Advanced",
                "description": "Our AI-powered algorithm evaluates 20+ market factors across multiple timeframes to generate a confidence score.",
                "factors_revealed": 5,
                "total_factors": "20+",
                "detail": "Scores above 84 indicate institutional-grade setups. The algorithm adapts to market conditions in real-time."
            },
            3: {
                "title": "Token Confidence Score (TCS) - Professional",
                "description": "A sophisticated multi-factor scoring system combining traditional TA, order flow analysis, and machine learning predictions.",
                "factors_revealed": 8,
                "total_factors": "23",
                "detail": "Each factor is weighted dynamically based on market regime. Institutional patterns are given priority weighting."
            },
            4: {
                "title": "Token Confidence Score (TCS) - Master Trader",
                "description": "Advanced quantitative model analyzing 23 factors including microstructure, dark pool flows, and AI sentiment analysis.",
                "factors_revealed": 15,
                "total_factors": "23",
                "detail": "The algorithm uses ensemble methods combining 7 different ML models with traditional quant strategies."
            },
            5: {
                "title": "Token Confidence Score (TCS) - Full Transparency",
                "description": "Complete algorithmic transparency: 23 factors across 8 categories, powered by ensemble ML with quantum-inspired optimization.",
                "factors_revealed": 23,
                "total_factors": "23",
                "detail": "You have achieved legendary status. The full algorithm is yours to understand and master."
            }
        }
        
        explanation = explanations[tier]
        explanation["mystery_element"] = self.mystery_elements[tier]
        explanation["next_unlock"] = self._get_next_unlock_level(user_level)
        
        return explanation
    
    def _get_max_score_for_factor(self, factor: str) -> int:
        """Get maximum possible score for a factor"""
        max_scores = {
            "market_structure": 20,
            "timeframe_alignment": 15,
            "momentum": 15,
            "volatility": 10,
            "session": 10,
            "liquidity": 10,
            "risk_reward": 10,
            "ai_sentiment": 10
        }
        return max_scores.get(factor, 10)
    
    def _assess_factor_quality(self, factor: str, score: float) -> str:
        """Assess quality level of a factor score"""
        max_score = self._get_max_score_for_factor(factor)
        percentage = (score / max_score) * 100
        
        if percentage >= 90:
            return "Excellent"
        elif percentage >= 75:
            return "Good"
        elif percentage >= 60:
            return "Fair"
        elif percentage >= 40:
            return "Weak"
        else:
            return "Poor"
    
    def _get_improvement_tip(self, factor: str, score: float, tier: int) -> str:
        """Get improvement tip for a factor based on score and user tier"""
        max_score = self._get_max_score_for_factor(factor)
        percentage = (score / max_score) * 100
        
        tips = {
            "market_structure": {
                "low": "Look for clearer trend structure and key levels",
                "medium": "Wait for pattern completion and confirmation",
                "high": "Excellent structure detected, maintain discipline"
            },
            "timeframe_alignment": {
                "low": "Check higher timeframes for confluence",
                "medium": "Good alignment, consider waiting for one more TF",
                "high": "Perfect multi-timeframe confluence achieved"
            },
            "momentum": {
                "low": "Momentum is weak, consider waiting for improvement",
                "medium": "Decent momentum, watch for divergences",
                "high": "Strong momentum confirmation in your favor"
            },
            "volatility": {
                "low": "Low volatility may limit profit potential",
                "medium": "Acceptable volatility for current conditions",
                "high": "Optimal volatility window detected"
            },
            "session": {
                "low": "Consider waiting for a more active session",
                "medium": "Session timing is acceptable",
                "high": "Prime session timing for this pair"
            },
            "liquidity": {
                "low": "Low liquidity detected, reduce position size",
                "medium": "Fair liquidity conditions",
                "high": "Excellent liquidity for smooth execution"
            },
            "risk_reward": {
                "low": "R:R ratio too low, adjust targets or entry",
                "medium": "Acceptable R:R, could be optimized",
                "high": "Excellent risk/reward ratio achieved"
            },
            "ai_sentiment": {
                "low": "AI models show conflicting signals",
                "medium": "AI sentiment moderately positive",
                "high": "Strong AI consensus on trade direction"
            }
        }
        
        quality = "low" if percentage < 50 else "medium" if percentage < 80 else "high"
        base_tip = tips.get(factor, {}).get(quality, "Continue monitoring this factor")
        
        # Add tier-specific insights
        if tier >= 3 and quality != "high":
            base_tip += f" [Pro tip: {self._get_pro_tip(factor, tier)}]"
            
        return base_tip
    
    def _get_pro_tip(self, factor: str, tier: int) -> str:
        """Get advanced tips for higher tier users"""
        pro_tips = {
            "market_structure": "Check for liquidity sweep patterns above/below structure",
            "timeframe_alignment": "Use Fibonacci time zones for cycle confluence",
            "momentum": "Monitor order flow delta for hidden momentum",
            "volatility": "Check options implied volatility for expansion signals",
            "session": "Track institutional VWAP levels by session",
            "liquidity": "Watch for iceberg orders in the order book",
            "risk_reward": "Use Monte Carlo simulation for position sizing",
            "ai_sentiment": "Cross-reference with social sentiment spikes"
        }
        
        return pro_tips.get(factor, "Advanced analysis available at higher levels")
    
    def _get_overview_sections(self, tier: int) -> List[Dict]:
        """Get overview sections based on tier"""
        base_sections = [
            {
                "title": "What is TCS?",
                "content": "Token Confidence Score measures trade quality from 0-100"
            },
            {
                "title": "Score Ranges",
                "content": "94+ Hammer | 84-93 Shadow Strike | 75-83 Scalp | 65-74 Watchlist"
            }
        ]
        
        if tier >= 2:
            base_sections.append({
                "title": "Multiple Factors",
                "content": "20+ market factors analyzed in real-time"
            })
            
        if tier >= 3:
            base_sections.append({
                "title": "AI Integration", 
                "content": "Machine learning models enhance traditional analysis"
            })
            
        if tier >= 4:
            base_sections.append({
                "title": "Institutional Edge",
                "content": "Order flow and dark pool analysis included"
            })
            
        if tier >= 5:
            base_sections.append({
                "title": "Full Algorithm",
                "content": "Complete transparency of all 23 factors and weights"
            })
            
        return base_sections
    
    def _get_factor_sections(self, tier: int) -> List[Dict]:
        """Get factor analysis sections based on tier"""
        sections = []
        
        # Reveal factors progressively
        factor_order = [
            "market_structure", "risk_reward", "timeframe_alignment",
            "momentum", "session", "volatility", "liquidity", "ai_sentiment"
        ]
        
        factors_to_show = min(3 + (tier - 1) * 2, len(factor_order))
        
        for i in range(factors_to_show):
            factor = factor_order[i]
            sections.append({
                "factor": factor,
                "title": factor.replace("_", " ").title(),
                "description": self.factor_explanations[factor][tier],
                "weight": f"{self._get_max_score_for_factor(factor)}%",
                "unlocked": True
            })
            
        # Add locked factors as teasers
        for i in range(factors_to_show, len(factor_order)):
            sections.append({
                "factor": factor_order[i],
                "title": "???",
                "description": "Unlock at higher levels",
                "weight": "?%",
                "unlocked": False
            })
            
        return sections
    
    def _get_trading_examples(self, tier: int) -> List[Dict]:
        """Get trading examples based on tier"""
        examples = []
        
        # Basic example - available to all
        examples.append({
            "title": "High TCS Breakout",
            "tcs_score": 92,
            "setup": "Bull flag on H1 with volume confirmation",
            "factors": {
                "structure": "Clear uptrend with flag consolidation",
                "momentum": "RSI holding above 50, MACD bullish",
                "risk_reward": "3.5:1 with clear stop below flag"
            },
            "outcome": "Target hit in 4 hours"
        })
        
        if tier >= 2:
            examples.append({
                "title": "Session-Optimized Scalp",
                "tcs_score": 81,
                "setup": "London open range break",
                "factors": {
                    "session": "London session peak liquidity",
                    "volatility": "ATR expansion signal",
                    "alignment": "M15 and H1 confluence"
                },
                "outcome": "Quick 30-pip scalp in 45 minutes"
            })
            
        if tier >= 3:
            examples.append({
                "title": "Liquidity Grab Reversal",
                "tcs_score": 96,
                "setup": "Stop hunt above resistance with rejection",
                "factors": {
                    "liquidity": "Clear liquidity grab pattern",
                    "structure": "Key resistance with multiple touches",
                    "ai_sentiment": "AI detected institutional selling"
                },
                "outcome": "200-pip reversal over 2 days"
            })
            
        return examples
    
    def _generate_quiz(self, topic: str, tier: int) -> List[Dict]:
        """Generate quiz questions based on topic and tier"""
        questions = []
        
        if topic == "tcs_overview":
            questions.append({
                "question": "What TCS score indicates a 'Hammer' trade?",
                "options": ["75+", "84+", "94+", "100"],
                "correct": 2,
                "explanation": "Hammer trades require 94+ TCS for elite setups"
            })
            
        if tier >= 2:
            questions.append({
                "question": "How many factors does TCS analyze?",
                "options": ["5-10", "10-15", "15-20", "20+"],
                "correct": 3,
                "explanation": "TCS analyzes 20+ factors for comprehensive analysis"
            })
            
        return questions
    
    def _get_next_lesson(self, current_topic: str, tier: int) -> Dict:
        """Get next recommended lesson"""
        lesson_progression = {
            "tcs_overview": "factor_analysis",
            "factor_analysis": "trading_examples",
            "trading_examples": "advanced_strategies"
        }
        
        next_topic = lesson_progression.get(current_topic, "tcs_overview")
        
        return {
            "topic": next_topic,
            "title": f"Next: {next_topic.replace('_', ' ').title()}",
            "available": True,
            "estimated_time": "10-15 minutes"
        }
    
    def _get_interactive_factor_explorer(self, tier: int) -> Dict:
        """Get interactive factor explorer configuration"""
        return {
            "enabled": tier >= 2,
            "factors_available": min(3 + (tier - 1) * 2, 8),
            "features": {
                "weight_adjustment": tier >= 4,
                "backtesting": tier >= 3,
                "custom_factors": tier >= 5
            }
        }
    
    def _get_case_studies(self, tier: int) -> List[Dict]:
        """Get case studies based on tier"""
        studies = []
        
        if tier >= 2:
            studies.append({
                "title": "The London Breakout",
                "date": "2024-01-15",
                "pair": "GBP/USD",
                "initial_tcs": 78,
                "final_tcs": 91,
                "key_learning": "Patience for TCS improvement paid off",
                "profit": "+127 pips"
            })
            
        if tier >= 3:
            studies.append({
                "title": "The Liquidity Sweep",
                "date": "2024-02-03", 
                "pair": "EUR/USD",
                "initial_tcs": 82,
                "final_tcs": 97,
                "key_learning": "Institutional patterns boost TCS dramatically",
                "profit": "+215 pips"
            })
            
        return studies
    
    def _get_trade_simulator_config(self, tier: int) -> Dict:
        """Get trade simulator configuration"""
        return {
            "enabled": True,
            "features": {
                "basic_scoring": True,
                "factor_breakdown": tier >= 2,
                "predictive_mode": tier >= 3,
                "custom_scenarios": tier >= 4,
                "ai_suggestions": tier >= 5
            },
            "available_pairs": ["EUR/USD", "GBP/USD", "USD/JPY"] if tier < 3 else "ALL"
        }
    
    def _get_best_practices(self, tier: int) -> List[str]:
        """Get best practices based on tier"""
        practices = [
            "Always wait for TCS 75+ before entering",
            "Check multiple timeframes for confluence",
            "Respect your risk management rules"
        ]
        
        if tier >= 2:
            practices.extend([
                "Trade during optimal sessions for your strategy",
                "Monitor TCS changes in real-time",
                "Use predictive TCS before placing trades"
            ])
            
        if tier >= 3:
            practices.extend([
                "Look for liquidity patterns before entry",
                "Combine TCS with your personal win rate",
                "Track factor performance over time"
            ])
            
        if tier >= 4:
            practices.extend([
                "Customize factor weights to your style",
                "Use AI insights for confirmation",
                "Monitor institutional flow patterns"
            ])
            
        return practices


def format_education_response(education_data: Dict) -> str:
    """
    Format education data for display in the UI
    """
    if "explanation" in education_data:
        # Single factor explanation
        response = f"**{education_data['factor'].replace('_', ' ').title()}**\n\n"
        response += f"{education_data['explanation']}\n\n"
        
        if "mystery_hint" in education_data:
            response += f"*{education_data['mystery_hint']}*\n\n"
            
        if "unlock_next_at" in education_data:
            response += f"🔓 More details unlock at Level {education_data['unlock_next_at']}"
            
    else:
        # General explanation
        response = f"# {education_data['title']}\n\n"
        response += f"{education_data['description']}\n\n"
        response += f"**Factors Analyzed:** {education_data['factors_revealed']}/{education_data['total_factors']}\n\n"
        response += f"{education_data['detail']}\n\n"
        
        if "mystery_element" in education_data:
            response += f"_{education_data['mystery_element']}_\n\n"
            
    return response


# Example usage
if __name__ == "__main__":
    educator = TCSEducation()
    
    # Example: Get explanation for different user levels
    for level in [5, 15, 30, 50, 80]:
        print(f"\n--- User Level {level} ---")
        explanation = educator.get_tcs_explanation(level, "momentum")
        print(format_education_response(explanation))
        
    # Example: Get visual example
    print("\n--- Visual Example for TCS 95 ---")
    example = educator.get_visual_example(95)
    print(json.dumps(example, indent=2))
    
    # Example: Get achievement unlocks
    print("\n--- Achievement Unlocks for Level 25 ---")
    unlocks = educator.get_achievement_unlocks(25)
    for unlock in unlocks[:5]:  # Show first 5
        status_icon = "✅" if unlock["status"] == "unlocked" else "🔒"
        print(f"{status_icon} Level {unlock['level']}: {unlock['feature']}")