"""
BITTEN Soul Filter
Ensures every feature, message, and interaction aligns with the psychological warfare mission
"""

from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import re

class SoulAlignment(Enum):
    """How well something aligns with BITTEN's soul"""
    PERFECT = "perfect"      # 100% aligned - builds tactical thinking
    GOOD = "good"           # 80%+ aligned - supports mission
    NEUTRAL = "neutral"     # 50-79% aligned - doesn't help/hurt
    CORRUPTED = "corrupted" # <50% aligned - undermines mission
    POISON = "poison"       # Anti-BITTEN - creates gambling mindset

class BittenSoulFilter:
    """
    The guardian of BITTEN's psychological warfare mission
    """
    
    def __init__(self):
        # Core BITTEN values - everything must align with these
        self.core_values = {
            "emotion_replacement": "Strip trading emotions, replace with tactical protocols",
            "trauma_alchemy": "Transform pain into strength through shared experience", 
            "stealth_education": "Teach forex mastery through military missions",
            "tactical_identity": "Convert traders into disciplined operators",
            "norman_authenticity": "Honor Norman's story and struggle",
            "bit_mystique": "Maintain Bit's dangerous, mysterious nature",
            "squad_bonding": "Build brotherhood through shared discipline",
            "transparent_fomo": "Show all signals, earn execution rights",
            "punishment_as_love": "Lockouts and restrictions prevent self-destruction"
        }
        
        # Poison patterns - immediate rejection
        self.poison_patterns = [
            r"easy.{0,10}money",
            r"guaranteed.{0,10}profit",
            r"get.{0,10}rich.{0,10}quick",
            r"no.{0,10}risk",
            r"100%.{0,10}win.{0,10}rate",
            r"secret.{0,10}system",
            r"holy.{0,10}grail",
            r"never.{0,10}lose",
            r"instant.{0,10}success",
            r"magic.{0,10}indicator"
        ]
        
        # Corruption indicators - undermines mission
        self.corruption_indicators = [
            "cute", "adorable", "fun", "entertaining",
            "comfortable", "safe", "easy", "simple",
            "casual", "lighthearted", "playful", "silly",
            "mascot", "friendly", "welcoming", "soft"
        ]
        
        # Perfect alignment indicators
        self.perfect_indicators = [
            "tactical", "protocol", "discipline", "mission",
            "objective", "execution", "precision", "calculated",
            "strategic", "systematic", "methodical", "deadly",
            "weapon", "operator", "soldier", "commander",
            "warfare", "battlefield", "enemy", "target"
        ]
        
        # Emotional gambling words (to be replaced)
        self.gambling_emotions = {
            "exciting": "calculated",
            "thrilling": "precise", 
            "fun": "tactical",
            "lucky": "prepared",
            "hoping": "planning",
            "feeling": "analyzing",
            "guess": "calculate",
            "gamble": "execute",
            "bet": "invest",
            "try": "execute"
        }
    
    def evaluate_feature(self, feature_description: str, feature_config: Dict) -> Dict:
        """
        Evaluate if a feature aligns with BITTEN's soul
        """
        analysis = {
            "alignment": SoulAlignment.NEUTRAL,
            "score": 50,
            "issues": [],
            "recommendations": [],
            "poison_detected": False,
            "corruption_level": 0,
            "perfect_elements": []
        }
        
        # Check for poison patterns
        poison_score = self._check_poison_patterns(feature_description)
        if poison_score > 0:
            analysis["alignment"] = SoulAlignment.POISON
            analysis["score"] = 0
            analysis["poison_detected"] = True
            analysis["issues"].append("POISON DETECTED: Contains gambling/scam language")
            return analysis
        
        # Check for corruption
        corruption_score = self._check_corruption(feature_description, feature_config)
        analysis["corruption_level"] = corruption_score
        
        # Check for perfect alignment
        perfect_score = self._check_perfect_alignment(feature_description, feature_config)
        
        # Calculate overall score
        base_score = 50
        base_score += perfect_score
        base_score -= corruption_score
        
        # Apply mission alignment bonuses
        mission_bonus = self._evaluate_mission_alignment(feature_description, feature_config)
        base_score += mission_bonus
        
        analysis["score"] = max(0, min(100, base_score))
        
        # Determine alignment category
        if analysis["score"] >= 90:
            analysis["alignment"] = SoulAlignment.PERFECT
        elif analysis["score"] >= 80:
            analysis["alignment"] = SoulAlignment.GOOD
        elif analysis["score"] >= 50:
            analysis["alignment"] = SoulAlignment.NEUTRAL
        else:
            analysis["alignment"] = SoulAlignment.CORRUPTED
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(
            analysis["score"], 
            corruption_score, 
            perfect_score,
            feature_description,
            feature_config
        )
        
        return analysis
    
    def evaluate_message(self, message: str, context: Dict = None) -> Dict:
        """
        Evaluate if a message aligns with BITTEN's psychological warfare tone
        """
        analysis = {
            "alignment": SoulAlignment.NEUTRAL,
            "score": 50,
            "tone_issues": [],
            "suggested_replacements": {},
            "personality_match": None
        }
        
        # Check for poison
        if self._check_poison_patterns(message) > 0:
            analysis["alignment"] = SoulAlignment.POISON
            analysis["score"] = 0
            analysis["tone_issues"].append("Contains gambling/scam language")
            return analysis
        
        # Check message tone
        tone_score = self._evaluate_message_tone(message)
        
        # Check personality consistency
        personality_score = self._check_personality_consistency(message, context)
        
        # Check for emotional gambling language
        gambling_replacements = self._identify_gambling_language(message)
        analysis["suggested_replacements"] = gambling_replacements
        
        # Calculate score
        analysis["score"] = (tone_score + personality_score) / 2
        analysis["score"] -= len(gambling_replacements) * 5  # Penalty for gambling words
        
        # Determine alignment
        if analysis["score"] >= 90:
            analysis["alignment"] = SoulAlignment.PERFECT
        elif analysis["score"] >= 80:
            analysis["alignment"] = SoulAlignment.GOOD
        elif analysis["score"] >= 50:
            analysis["alignment"] = SoulAlignment.NEUTRAL
        else:
            analysis["alignment"] = SoulAlignment.CORRUPTED
        
        return analysis
    
    def filter_signal_presentation(self, signal_data: Dict) -> Dict:
        """
        Ensure signal presentation maintains BITTEN's tactical nature
        """
        filtered = signal_data.copy()
        
        # Replace gambling language in descriptions
        if "description" in filtered:
            filtered["description"] = self._militarize_language(filtered["description"])
        
        # Ensure tactical framing
        if "setup" in filtered:
            filtered["setup"] = self._convert_to_tactical_language(filtered["setup"])
        
        # Add mission context
        filtered["mission_context"] = self._generate_mission_context(signal_data)
        
        # Remove any "fun" or "entertainment" framing
        filtered = self._remove_gambling_framing(filtered)
        
        return filtered
    
    def validate_ui_element(self, element: Dict) -> Dict:
        """
        Validate UI elements maintain the psychological warfare aesthetic
        """
        issues = []
        recommendations = []
        
        # Check colors
        if "colors" in element:
            color_issues = self._validate_colors(element["colors"])
            issues.extend(color_issues)
        
        # Check copy/text
        if "text" in element:
            text_analysis = self.evaluate_message(element["text"])
            if text_analysis["alignment"] in [SoulAlignment.CORRUPTED, SoulAlignment.POISON]:
                issues.append(f"Text alignment: {text_analysis['alignment'].value}")
        
        # Check iconography
        if "icons" in element:
            icon_issues = self._validate_icons(element["icons"])
            issues.extend(icon_issues)
        
        # Generate recommendations
        if issues:
            recommendations = self._generate_ui_recommendations(element, issues)
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "soul_alignment": SoulAlignment.GOOD if len(issues) == 0 else SoulAlignment.CORRUPTED
        }
    
    def _check_poison_patterns(self, text: str) -> int:
        """Check for poison patterns that destroy BITTEN's credibility"""
        poison_count = 0
        text_lower = text.lower()
        
        for pattern in self.poison_patterns:
            if re.search(pattern, text_lower):
                poison_count += 1
                
        return poison_count * 50  # Heavy penalty
    
    def _check_corruption(self, description: str, config: Dict) -> int:
        """Check for corruption that undermines the mission"""
        corruption_score = 0
        text_lower = description.lower()
        
        # Check for corruption indicators
        for indicator in self.corruption_indicators:
            if indicator in text_lower:
                corruption_score += 10
        
        # Check config for corrupting elements
        if isinstance(config, dict):
            if config.get("gamification_level") == "high" and "achievement" not in description:
                corruption_score += 15
            
            if config.get("difficulty") == "easy":
                corruption_score += 10
                
            if "entertainment_value" in config:
                corruption_score += 20
        
        return min(corruption_score, 40)  # Cap at 40 points
    
    def _check_perfect_alignment(self, description: str, config: Dict) -> int:
        """Check for perfect alignment elements"""
        perfect_score = 0
        text_lower = description.lower()
        
        # Check for perfect indicators
        for indicator in self.perfect_indicators:
            if indicator in text_lower:
                perfect_score += 5
        
        # Check for mission alignment
        if "emotion" in text_lower and ("replace" in text_lower or "strip" in text_lower):
            perfect_score += 15
            
        if "norman" in text_lower or "bit" in text_lower:
            perfect_score += 10
            
        if "tactical" in text_lower and "thinking" in text_lower:
            perfect_score += 10
            
        if "discipline" in text_lower or "protocol" in text_lower:
            perfect_score += 8
        
        return min(perfect_score, 40)  # Cap at 40 points
    
    def _evaluate_mission_alignment(self, description: str, config: Dict) -> int:
        """Evaluate alignment with core mission values"""
        bonus = 0
        
        for value_key, value_desc in self.core_values.items():
            key_words = value_desc.lower().split()[:3]  # First 3 words
            if all(word in description.lower() for word in key_words[:2]):
                bonus += 5
        
        return min(bonus, 30)
    
    def _evaluate_message_tone(self, message: str) -> int:
        """Evaluate if message tone matches BITTEN personalities"""
        score = 50  # Neutral baseline
        
        # Military/tactical language bonus
        military_words = ["mission", "objective", "protocol", "execute", "tactical", "soldier"]
        for word in military_words:
            if word in message.lower():
                score += 8
        
        # Emotional gambling language penalty
        gambling_words = ["exciting", "fun", "easy", "guarantee", "sure thing"]
        for word in gambling_words:
            if word in message.lower():
                score -= 12
        
        # Discipline/structure bonus
        discipline_words = ["discipline", "structure", "system", "rules", "method"]
        for word in discipline_words:
            if word in message.lower():
                score += 6
        
        return max(0, min(100, score))
    
    def _check_personality_consistency(self, message: str, context: Dict) -> int:
        """Check if message matches personality speaking"""
        if not context or "personality" not in context:
            return 50
        
        personality = context["personality"]
        message_lower = message.lower()
        
        personality_patterns = {
            "DRILL": ["discipline", "protocol", "execute", "soldier", "weakness"],
            "DOC": ["careful", "protect", "risk", "safety", "family"],
            "OVERWATCH": ["market", "probability", "analysis", "cynical", "reality"],
            "ATHENA": ["wisdom", "patience", "river", "time", "experience"],
            "NEXUS": ["squad", "team", "together", "brothers", "support"],
            "BIT": ["chirp", "hiss", "watch", "remember", "silent"]
        }
        
        if personality in personality_patterns:
            pattern_matches = sum(1 for word in personality_patterns[personality] 
                                if word in message_lower)
            return min(100, 50 + (pattern_matches * 10))
            
        return 50
    
    def _identify_gambling_language(self, message: str) -> Dict[str, str]:
        """Identify gambling language and suggest tactical replacements"""
        replacements = {}
        message_lower = message.lower()
        
        for gambling_word, tactical_word in self.gambling_emotions.items():
            if gambling_word in message_lower:
                replacements[gambling_word] = tactical_word
                
        return replacements
    
    def _militarize_language(self, text: str) -> str:
        """Convert civilian language to military/tactical language"""
        replacements = {
            "trade": "mission",
            "position": "deployment", 
            "profit": "objective secured",
            "loss": "tactical retreat",
            "entry": "engagement",
            "exit": "extraction",
            "stop loss": "evacuation protocol",
            "take profit": "mission complete",
            "analysis": "intelligence",
            "signal": "target acquisition",
            "setup": "operational briefing"
        }
        
        result = text
        for civilian, military in replacements.items():
            result = re.sub(r'\b' + civilian + r'\b', military, result, flags=re.IGNORECASE)
            
        return result
    
    def _convert_to_tactical_language(self, setup_text: str) -> str:
        """Convert trading setup to tactical mission briefing"""
        # Add tactical framing
        tactical_setup = f"**MISSION BRIEFING:**\n{setup_text}"
        
        # Replace key terms
        tactical_setup = self._militarize_language(tactical_setup)
        
        # Add operational context
        if "support" in setup_text.lower():
            tactical_setup += "\n**TACTICAL NOTE:** Defensive position identified."
        if "resistance" in setup_text.lower():
            tactical_setup += "\n**TACTICAL NOTE:** Enemy stronghold detected."
            
        return tactical_setup
    
    def _generate_mission_context(self, signal_data: Dict) -> str:
        """Generate mission context for signals"""
        tcs_score = signal_data.get("tcs_score", 75)
        
        if tcs_score >= 94:
            return "🔨 **HAMMER PROTOCOL** - Elite tactical opportunity"
        elif tcs_score >= 84:
            return "⚡ **SHADOW STRIKE** - High-probability engagement"
        elif tcs_score >= 75:
            return "🎯 **PRECISION SCALP** - Quick tactical strike"
        else:
            return "👁️ **RECONNAISSANCE** - Monitor for improvement"
    
    def _remove_gambling_framing(self, data: Dict) -> Dict:
        """Remove gambling/entertainment framing"""
        filtered = data.copy()
        
        # Remove entertainment keys
        entertainment_keys = ["fun_factor", "excitement_level", "entertainment_value"]
        for key in entertainment_keys:
            filtered.pop(key, None)
        
        # Replace gambling terminology in all string values
        def clean_value(value):
            if isinstance(value, str):
                for gambling, tactical in self.gambling_emotions.items():
                    value = re.sub(r'\b' + gambling + r'\b', tactical, value, flags=re.IGNORECASE)
            return value
        
        for key, value in filtered.items():
            if isinstance(value, str):
                filtered[key] = clean_value(value)
            elif isinstance(value, dict):
                filtered[key] = {k: clean_value(v) for k, v in value.items()}
                
        return filtered
    
    def _validate_colors(self, colors: Dict) -> List[str]:
        """Validate color scheme maintains military aesthetic"""
        issues = []
        
        # Forbidden colors (too soft/cute)
        forbidden = ["pink", "purple", "light_blue", "yellow", "orange"]
        
        # Preferred colors (military/tactical)
        preferred = ["dark_green", "black", "red", "white", "gray", "gold"]
        
        for color_name, color_value in colors.items():
            if any(forbidden_color in color_name.lower() for forbidden_color in forbidden):
                issues.append(f"Color {color_name} too soft for military aesthetic")
                
        return issues
    
    def _validate_icons(self, icons: List[str]) -> List[str]:
        """Validate icons maintain tactical aesthetic"""
        issues = []
        
        # Forbidden icons (too cute/soft)
        forbidden_icons = ["😊", "😄", "🎉", "💖", "🌈", "🦄", "🌸"]
        
        for icon in icons:
            if icon in forbidden_icons:
                issues.append(f"Icon {icon} undermines tactical identity")
                
        return issues
    
    def _generate_recommendations(self, score: int, corruption: int, perfect: int,
                                description: str, config: Dict) -> List[str]:
        """Generate specific recommendations for improvement"""
        recommendations = []
        
        if score < 50:
            recommendations.append("CRITICAL: This feature undermines BITTEN's mission")
            recommendations.append("Remove all gambling/entertainment language")
            recommendations.append("Reframe as tactical/military operation")
        
        if corruption > 20:
            recommendations.append("Replace 'cute/fun' elements with tactical equivalents")
            recommendations.append("Add discipline/protocol framework")
        
        if perfect < 10:
            recommendations.append("Add military/tactical language")
            recommendations.append("Connect to Norman's story or mission values")
            recommendations.append("Include emotion replacement elements")
        
        if score >= 80:
            recommendations.append("Excellent alignment with BITTEN's soul")
            recommendations.append("Consider adding this to core feature examples")
        
        return recommendations
    
    def _generate_ui_recommendations(self, element: Dict, issues: List[str]) -> List[str]:
        """Generate UI-specific recommendations"""
        recommendations = []
        
        if any("color" in issue.lower() for issue in issues):
            recommendations.append("Use military color palette: blacks, greens, reds, golds")
            
        if any("icon" in issue.lower() for issue in issues):
            recommendations.append("Replace with tactical icons: ⚔️🎯🔨⚡👁️")
            
        if any("text" in issue.lower() for issue in issues):
            recommendations.append("Rewrite copy using military/tactical language")
            
        return recommendations

# Global soul filter instance
soul_filter = BittenSoulFilter()

def evaluate_feature_alignment(description: str, config: Dict = None) -> Dict:
    """
    Quick function to evaluate any feature's alignment with BITTEN's soul
    """
    return soul_filter.evaluate_feature(description, config or {})

def ensure_tactical_message(message: str, personality: str = None) -> str:
    """
    Quick function to ensure a message maintains tactical tone
    """
    context = {"personality": personality} if personality else {}
    analysis = soul_filter.evaluate_message(message, context)
    
    if analysis["alignment"] in [SoulAlignment.CORRUPTED, SoulAlignment.POISON]:
        # Apply suggested replacements
        improved_message = message
        for gambling_word, tactical_word in analysis["suggested_replacements"].items():
            improved_message = re.sub(r'\b' + gambling_word + r'\b', tactical_word, 
                                    improved_message, flags=re.IGNORECASE)
        return improved_message
    
    return message