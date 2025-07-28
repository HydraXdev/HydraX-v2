"""
Telegram Shield Formatter - Format CITADEL analysis for Telegram messages

Purpose: Transform shield analysis into beautifully formatted Telegram messages
that enhance signal display without overwhelming users.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramShieldFormatter:
    """
    Formats CITADEL shield analysis into enhanced Telegram messages
    that maintain clarity while adding valuable protection insights.
    """
    
    def __init__(self):
        # Message templates for different shield levels
        self.templates = {
            'SHIELD_APPROVED': {
                'header': '🛡️ SHIELD APPROVED',
                'color': 'green',
                'emphasis': 'strong'
            },
            'SHIELD_ACTIVE': {
                'header': '✅ SHIELD ACTIVE',
                'color': 'blue',
                'emphasis': 'moderate'
            },
            'VOLATILITY_ZONE': {
                'header': '⚠️ VOLATILITY ZONE',
                'color': 'yellow',
                'emphasis': 'caution'
            },
            'UNVERIFIED': {
                'header': '🔍 UNVERIFIED',
                'color': 'gray',
                'emphasis': 'minimal'
            }
        }
        
        # Compact reason mappings
        self.reason_shortcuts = {
            'post_sweep_entry': 'Post-sweep confirmed',
            'strong_tf_alignment': 'Multi-TF aligned',
            'trend_continuation': 'Trend continuation',
            'key_level_confluence': 'Key level confluence',
            'liquidity_trap': 'Trap zone detected',
            'news_high_impact': 'High-impact news',
            'volatility_extreme': 'Extreme volatility'
        }
    
    def format_enhanced_signal(self, signal: Dict[str, Any], 
                             shield_analysis: Dict[str, Any],
                             compact: bool = False) -> str:
        """
        Format signal with CITADEL shield enhancement.
        
        Args:
            signal: Original signal data
            shield_analysis: Complete shield analysis results
            compact: Whether to use compact formatting
            
        Returns:
            Formatted Telegram message string
        """
        try:
            # Extract core signal data
            pair = signal.get('pair', 'UNKNOWN')
            direction = signal.get('direction', 'BUY')
            entry = signal.get('entry_price', 0)
            tp = signal.get('tp', 0)
            sl = signal.get('sl', 0)
            
            # Extract shield data
            classification = shield_analysis.get('classification', 'UNVERIFIED')
            score = shield_analysis.get('shield_score', 0)
            emoji = shield_analysis.get('emoji', '🔍')
            
            if compact:
                return self._format_compact(
                    pair, direction, entry, tp, sl,
                    classification, score, emoji, shield_analysis
                )
            else:
                return self._format_detailed(
                    pair, direction, entry, tp, sl,
                    classification, score, emoji, shield_analysis
                )
                
        except Exception as e:
            logger.error(f"Telegram formatting error: {str(e)}")
            return self._format_basic_signal(signal)
    
    def _format_compact(self, pair: str, direction: str, entry: float,
                       tp: float, sl: float, classification: str,
                       score: float, emoji: str, analysis: Dict) -> str:
        """Format compact signal message."""
        # Basic signal info
        direction_emoji = "📈" if direction == "BUY" else "📉"
        message_parts = [
            f"📍 {pair} {direction_emoji} {direction} @ {entry}",
            f"🎯 TP: {tp} | 🛑 SL: {sl}"
        ]
        
        # Shield status line
        template = self.templates.get(classification, self.templates['UNVERIFIED'])
        shield_line = f"{emoji} {template['header']} [{score}/10]"
        
        # Add key insight
        if classification == 'SHIELD_APPROVED':
            # Show top quality factor
            quality_factors = analysis.get('quality_factors', [])
            if quality_factors:
                reason = self._get_compact_reason(quality_factors[0]['description'])
                shield_line += f" - {reason}"
        elif classification in ['VOLATILITY_ZONE', 'UNVERIFIED']:
            # Show top risk factor
            risk_factors = analysis.get('risk_factors', [])
            if risk_factors:
                reason = self._get_compact_reason(risk_factors[0]['description'])
                shield_line += f" - {reason}"
        
        message_parts.append(shield_line)
        
        return "\n".join(message_parts)
    
    def _format_detailed(self, pair: str, direction: str, entry: float,
                        tp: float, sl: float, classification: str,
                        score: float, emoji: str, analysis: Dict) -> str:
        """Format detailed signal message with full shield analysis."""
        # Header with signal info
        direction_emoji = "📈" if direction == "BUY" else "📉"
        lines = [
            f"📍 **{pair}** {direction_emoji} {direction} @ {entry}",
            f"🎯 TP: {tp} | 🛑 SL: {sl}",
            ""  # Blank line
        ]
        
        # Shield status section
        template = self.templates.get(classification, self.templates['UNVERIFIED'])
        lines.append(f"{emoji} **{template['header']}** - Score: {score}/10")
        
        # Add concise explanation
        explanation = analysis.get('explanation', '')
        if explanation:
            lines.append(f"_{explanation}_")
        
        # Key factors section
        lines.append("")  # Blank line
        
        # Positive factors
        quality_factors = analysis.get('quality_factors', [])[:2]
        if quality_factors:
            lines.append("✅ **Strengths:**")
            for factor in quality_factors:
                lines.append(f"  • {self._format_factor(factor['description'])}")
        
        # Risk factors
        risk_factors = analysis.get('risk_factors', [])[:2]
        if risk_factors:
            lines.append("⚠️ **Cautions:**")
            for factor in risk_factors:
                lines.append(f"  • {self._format_factor(factor['description'])}")
        
        # Recommendation
        recommendation = analysis.get('recommendation', '')
        if recommendation and classification != 'SHIELD_APPROVED':
            lines.append("")
            lines.append(f"💡 _{recommendation}_")
        
        return "\n".join(lines)
    
    def format_shield_insight(self, shield_analysis: Dict[str, Any]) -> str:
        """
        Format detailed shield insight for users who tap to learn more.
        
        Args:
            shield_analysis: Complete shield analysis
            
        Returns:
            Detailed explanation message
        """
        lines = [
            "🛡️ **CITADEL Shield Analysis**",
            f"Score: {shield_analysis.get('shield_score', 0)}/10",
            ""
        ]
        
        # Score breakdown
        lines.append("📊 **Score Components:**")
        components = shield_analysis.get('components', [])
        
        # Group by positive/negative
        positive_components = [c for c in components if c['impact'] == 'positive']
        negative_components = [c for c in components if c['impact'] == 'negative']
        
        if positive_components:
            lines.append("\n✅ Positive Factors:")
            for comp in sorted(positive_components, key=lambda x: x['score'], reverse=True)[:5]:
                lines.append(f"  • {comp['name']}: +{comp['score']:.1f} ({comp['reason']})")
        
        if negative_components:
            lines.append("\n❌ Negative Factors:")
            for comp in sorted(negative_components, key=lambda x: x['score'])[:5]:
                lines.append(f"  • {comp['name']}: {comp['score']:.1f} ({comp['reason']})")
        
        # Quality and risk summary
        quality_factors = shield_analysis.get('quality_factors', [])
        risk_factors = shield_analysis.get('risk_factors', [])
        
        if quality_factors:
            lines.append("\n🏆 **Quality Bonuses:**")
            for factor in quality_factors:
                lines.append(f"  • {factor['description']} (+{factor['bonus']})")
        
        if risk_factors:
            lines.append("\n⚠️ **Risk Penalties:**")
            for factor in risk_factors:
                lines.append(f"  • {factor['description']} ({factor['penalty']})")
        
        # Learning tip
        lines.extend([
            "",
            "💡 **What This Means:**",
            self._get_educational_tip(shield_analysis)
        ])
        
        # Confidence level
        confidence = shield_analysis.get('confidence', 0)
        lines.extend([
            "",
            f"🎯 Shield Confidence: {int(confidence * 100)}%"
        ])
        
        return "\n".join(lines)
    
    def format_shield_summary(self, signals_analyzed: int, 
                            classifications: Dict[str, int]) -> str:
        """
        Format daily shield summary statistics.
        
        Args:
            signals_analyzed: Total signals analyzed
            classifications: Count by classification type
            
        Returns:
            Summary message
        """
        lines = [
            "🛡️ **CITADEL Daily Shield Report**",
            f"Signals Analyzed: {signals_analyzed}",
            "",
            "📊 Shield Distribution:"
        ]
        
        # Add classification breakdown
        total = sum(classifications.values())
        for classification, count in sorted(classifications.items(), 
                                          key=lambda x: x[1], reverse=True):
            if count > 0:
                percentage = (count / total * 100) if total > 0 else 0
                emoji = self._get_classification_emoji(classification)
                label = self._get_classification_label(classification)
                lines.append(f"{emoji} {label}: {count} ({percentage:.1f}%)")
        
        # Add insight
        approved_rate = classifications.get('SHIELD_APPROVED', 0) / total * 100 if total > 0 else 0
        if approved_rate > 40:
            lines.append("\n✅ Excellent market conditions today!")
        elif approved_rate > 20:
            lines.append("\n⚠️ Mixed market conditions - trade selectively")
        else:
            lines.append("\n🔍 Challenging conditions - extra caution advised")
        
        return "\n".join(lines)
    
    def _get_compact_reason(self, description: str) -> str:
        """Get compact reason for shield decision."""
        # Check for known patterns
        for pattern, shortcut in self.reason_shortcuts.items():
            if pattern.lower() in description.lower():
                return shortcut
        
        # Default to first few words
        words = description.split()[:4]
        return " ".join(words)
    
    def _format_factor(self, description: str) -> str:
        """Format factor description for readability."""
        # Capitalize first letter and ensure proper ending
        formatted = description[0].upper() + description[1:] if description else ""
        if formatted and not formatted[-1] in '.!?':
            formatted += "."
        return formatted
    
    def _get_educational_tip(self, analysis: Dict[str, Any]) -> str:
        """Generate educational tip based on shield analysis."""
        classification = analysis.get('classification', 'UNVERIFIED')
        score = analysis.get('shield_score', 0)
        
        tips = {
            'SHIELD_APPROVED': {
                'high': "This signal shows strong institutional characteristics. "
                       "The post-sweep entry and multi-timeframe alignment suggest "
                       "smart money positioning.",
                'moderate': "Solid setup with good protection factors. The shield "
                          "identifies this as a quality opportunity with manageable risks."
            },
            'SHIELD_ACTIVE': {
                'default': "Decent setup but not perfect. Consider reducing position "
                          "size or waiting for better confirmation. The shield helps "
                          "you avoid overcommitting to moderate setups."
            },
            'VOLATILITY_ZONE': {
                'default': "High-risk environment detected. The shield protects you "
                          "from volatile conditions where stops are easily hunted. "
                          "Wait for calmer conditions or use wider stops."
            },
            'UNVERIFIED': {
                'default': "Insufficient confirmation for this setup. The shield "
                          "cannot verify institutional behavior patterns. This "
                          "often indicates a potential trap or poor timing."
            }
        }
        
        if classification == 'SHIELD_APPROVED':
            return tips[classification]['high' if score >= 9 else 'moderate']
        else:
            return tips.get(classification, {}).get('default', 
                   "Continue learning to recognize these patterns yourself.")
    
    def _get_classification_emoji(self, classification: str) -> str:
        """Get emoji for classification type."""
        emojis = {
            'SHIELD_APPROVED': '🛡️',
            'SHIELD_ACTIVE': '✅',
            'VOLATILITY_ZONE': '⚠️',
            'UNVERIFIED': '🔍'
        }
        return emojis.get(classification, '❓')
    
    def _get_classification_label(self, classification: str) -> str:
        """Get readable label for classification."""
        labels = {
            'SHIELD_APPROVED': 'Shield Approved',
            'SHIELD_ACTIVE': 'Shield Active',
            'VOLATILITY_ZONE': 'Volatility Zone',
            'UNVERIFIED': 'Unverified'
        }
        return labels.get(classification, 'Unknown')
    
    def _format_basic_signal(self, signal: Dict[str, Any]) -> str:
        """Format basic signal without shield data."""
        pair = signal.get('pair', 'UNKNOWN')
        direction = signal.get('direction', 'BUY')
        entry = signal.get('entry_price', 0)
        tp = signal.get('tp', 0)
        sl = signal.get('sl', 0)
        
        direction_emoji = "📈" if direction == "BUY" else "📉"
        return (
            f"📍 {pair} {direction_emoji} {direction} @ {entry}\n"
            f"🎯 TP: {tp} | 🛑 SL: {sl}"
        )


# Example usage
if __name__ == "__main__":
    formatter = TelegramShieldFormatter()
    
    # Test signal
    test_signal = {
        'pair': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.0850,
        'tp': 1.0900,
        'sl': 1.0820
    }
    
    # Test shield analysis
    test_shield = {
        'shield_score': 8.5,
        'classification': 'SHIELD_APPROVED',
        'emoji': '🛡️',
        'explanation': 'Post-sweep entry with multi-TF alignment | Low volatility environment',
        'quality_factors': [
            {'description': 'Entry after liquidity sweep', 'bonus': 2.0},
            {'description': 'Strong multi-TF alignment', 'bonus': 1.5}
        ],
        'risk_factors': [],
        'recommendation': 'High-quality setup - Standard position size',
        'confidence': 0.85
    }
    
    # Test formatting
    print("=== COMPACT FORMAT ===")
    print(formatter.format_enhanced_signal(test_signal, test_shield, compact=True))
    
    print("\n=== DETAILED FORMAT ===")
    print(formatter.format_enhanced_signal(test_signal, test_shield, compact=False))
    
    print("\n=== SHIELD INSIGHT ===")
    print(formatter.format_shield_insight(test_shield))