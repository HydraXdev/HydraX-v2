"""
BITTEN Low TCS Warning System - Bit's Wisdom Module
Handles confirmation dialogs for low confidence shots with Bit's Yoda-style warnings
"""

import random
from typing import Dict, Tuple, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class WarningLevel(Enum):
    """Warning levels for different TCS ranges"""
    EXTREME = "extreme"      # TCS < 60
    HIGH = "high"           # TCS 60-69
    MODERATE = "moderate"   # TCS 70-75
    LOW = "low"            # TCS 76-79

@dataclass
class BitWarning:
    """Bit's warning message structure"""
    message: str
    emoji: str
    voice_tone: str  # How Bit sounds (worried, cautious, stern, etc.)
    action_required: str  # What the user must do

class BitWarningSystem:
    """
    Bit's Wisdom Engine - Channel's Yoda-like warnings for low confidence trades
    """
    
    def __init__(self):
        # Initialize Bit's wisdom database
        self.wisdom_quotes = self._initialize_wisdom_quotes()
        self.warning_templates = self._initialize_warning_templates()
        self.confirmation_history = {}  # Track user's confirmation patterns
        
    def _initialize_wisdom_quotes(self) -> Dict[WarningLevel, List[str]]:
        """Initialize Bit's wisdom quotes by warning level"""
        return {
            WarningLevel.EXTREME: [
                "Dangerous this path is, young trader. {tcs}% confidence only, I sense.",
                "Dark clouds gather, they do. {tcs}% certainty, not enough it is.",
                "Feel the fear in this trade, I do. {tcs}% confidence, leads to losses it does.",
                "Much to learn you still have. {tcs}% TCS, ready you are not.",
                "The dark side of trading, this is. {tcs}% confidence, pain it brings."],
            WarningLevel.HIGH: [
                "Clouded this future is. {tcs}% confidence, uncertain the outcome.",
                "Patience you must have, young padawan. {tcs}% TCS, wait for clarity you should.",
                "Feel disturbance in the markets, I do. {tcs}% confidence, careful you must be.",
                "Risk leads to fear. Fear leads to losses. {tcs}% TCS, think twice you must.",
                "Difficult to see. Always in motion the future is. {tcs}% confidence only."],
            WarningLevel.MODERATE: [
                "Cautious you must be. {tcs}% confidence, on the edge we are.",
                "The Force is weak here. {tcs}% TCS, strengthen your position you must.",
                "Hmm, {tcs}% certainty. Better setups await, if patient you are.",
                "Trust your feelings, but {tcs}% confidence, enough it may not be.",
                "A Jedi uses the Force for knowledge. {tcs}% TCS, seek more clarity you should."],
            WarningLevel.LOW: [
                "Close to the minimum, you are. {tcs}% confidence, proceed with caution.",
                "Acceptable this may be, but {tcs}% TCS, vigilant you must remain.",
                "The Force guides, but {tcs}% certainty, watch closely you must.",
                "Borderline this setup is. {tcs}% confidence, your discipline will be tested.",
                "Ready you may be, but {tcs}% TCS, remember your training you must."]
        }
    
    def _initialize_warning_templates(self) -> Dict[WarningLevel, Dict]:
        """Initialize warning dialog templates"""
        return {
            WarningLevel.EXTREME: {
                'title': '⚠️ EXTREME RISK WARNING ⚠️',
                'color': '#FF0000',
                'bit_emoji': '😰',
                'require_double_confirm': True,
                'cooldown_seconds': 30,
                'buttons': [
                    {'text': '❌ Cancel Trade', 'action': 'cancel'},
                    {'text': '⚠️ Yes, I understand the extreme risk', 'action': 'confirm_extreme'}
                ]
            },
            WarningLevel.HIGH: {
                'title': '🚨 HIGH RISK WARNING 🚨',
                'color': '#FF6600',
                'bit_emoji': '😟',
                'require_double_confirm': True,
                'cooldown_seconds': 20,
                'buttons': [
                    {'text': '❌ Cancel Trade', 'action': 'cancel'},
                    {'text': '⚠️ Yes, I accept the high risk', 'action': 'confirm_high'}
                ]
            },
            WarningLevel.MODERATE: {
                'title': '⚡ RISK WARNING ⚡',
                'color': '#FFA500',
                'bit_emoji': '🤔',
                'require_double_confirm': False,
                'cooldown_seconds': 10,
                'buttons': [
                    {'text': '❌ Wait for Better Setup', 'action': 'cancel'},
                    {'text': '✅ I understand the risk', 'action': 'confirm_moderate'}
                ]
            },
            WarningLevel.LOW: {
                'title': '📊 CONFIDENCE CHECK 📊',
                'color': '#FFFF00',
                'bit_emoji': '🧐',
                'require_double_confirm': False,
                'cooldown_seconds': 5,
                'buttons': [
                    {'text': '🔍 Review Setup', 'action': 'review'},
                    {'text': '✅ Proceed with Trade', 'action': 'confirm_low'}
                ]
            }
        }
    
    def get_warning_level(self, tcs: float) -> WarningLevel:
        """Determine warning level based on TCS"""
        if tcs < 60:
            return WarningLevel.EXTREME
        elif tcs < 70:
            return WarningLevel.HIGH
        elif tcs < 76:
            return WarningLevel.MODERATE
        else:
            return WarningLevel.LOW
    
    def generate_warning_dialog(self, tcs: float, user_profile: Dict) -> Dict:
        """Generate warning dialog for low TCS trade"""
        warning_level = self.get_warning_level(tcs)
        template = self.warning_templates[warning_level]
        
        # Select random wisdom quote
        wisdom_quote = random.choice(self.wisdom_quotes[warning_level]).format(tcs=tcs)
        
        # Add discipline reminders based on user's recent performance
        discipline_reminder = self._get_discipline_reminder(user_profile)
        
        # Build dialog content
        dialog = {
            'type': 'low_tcs_warning',
            'level': warning_level.value,
            'tcs': tcs,
            'title': template['title'],
            'color': template['color'],
            'content': {
                'bit_says': wisdom_quote,
                'bit_emoji': template['bit_emoji'],
                'stats': self._get_risk_stats(tcs, user_profile),
                'discipline_reminder': discipline_reminder,
                'patience_wisdom': self._get_patience_wisdom()},
            'buttons': template['buttons'],
            'require_double_confirm': template['require_double_confirm'],
            'cooldown_seconds': template['cooldown_seconds'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Add second confirmation if required
        if template['require_double_confirm']:
            dialog['second_confirmation'] = self._generate_second_confirmation(warning_level, tcs)
        
        return dialog
    
    def _get_discipline_reminder(self, user_profile: Dict) -> str:
        """Get discipline reminder based on user's recent trades"""
        recent_losses = user_profile.get('recent_losses', 0)
        win_rate = user_profile.get('win_rate_7d', 0.5)
        last_loss_time = user_profile.get('last_loss_time')
        
        if recent_losses >= 3:
            return "Three losses in a row, you have had. Break this pattern, you must."
        elif win_rate < 0.4:
            return "Struggling your performance is. Patience, the path to recovery it is."
        elif last_loss_time and (datetime.now() - last_loss_time).seconds < 3600:
            return "Recent loss still fresh it is. Emotional trading, avoid you must."
        else:
            return "Discipline, the mark of a true Jedi trader it is."
    
    def _get_risk_stats(self, tcs: float, user_profile: Dict) -> Dict:
        """Calculate risk statistics for the warning"""
        # Historical performance at similar TCS levels
        similar_tcs_trades = user_profile.get('trades_by_tcs', {}).get(f"{int(tcs//10)*10}s", {})
        
        return {
            'current_tcs': f"{tcs}%",
            'minimum_required': "76%",
            'deficit': f"{76 - tcs}%",
            'historical_win_rate': similar_tcs_trades.get('win_rate', 'No data'),
            'average_loss_at_level': similar_tcs_trades.get('avg_loss', 'No data'),
            'risk_multiplier': self._calculate_risk_multiplier(tcs)
        }
    
    def _calculate_risk_multiplier(self, tcs: float) -> str:
        """Calculate how much riskier this trade is compared to baseline"""
        baseline_risk = 0.24  # 76% success = 24% failure
        current_risk = 1 - (tcs / 100)
        multiplier = current_risk / baseline_risk
        return f"{multiplier:.1f}x"
    
    def _get_patience_wisdom(self) -> str:
        """Get random patience wisdom from Bit"""
        patience_quotes = [
            "Patience, for the moment when the setup reveals itself, you must have.",
            "A Jedi trader craves not adventure or excitement. Seek the perfect setup, they do.",
            "Wars not make one great. Consistent, profitable trades do.",
            "Do or do not trade. There is no revenge trade.",
            "The greatest teacher, missed opportunities are. Learn from them, you will.",
            "Size matters not. Judge a trade by its quality, not quantity.",
            "Luminous setups are we, not this crude and random noise.",
            "Through patience, achieve clarity you will.",
            "Already know you that which you need. Trust in the process, you must.",
            "Adventure. Excitement. A Jedi trader craves not these things."
        ]
        return random.choice(patience_quotes)
    
    def _generate_second_confirmation(self, warning_level: WarningLevel, tcs: float) -> Dict:
        """Generate second confirmation dialog for high-risk trades"""
        
        # More serious tone for second confirmation
        serious_warnings = {
            WarningLevel.EXTREME: [
                "Certain of this path, are you? {tcs}% confidence, devastating losses it may bring.",
                "Final warning, this is. {tcs}% TCS, the odds against you they are.",
                "Feel the danger, you do not? {tcs}% certainty, reckless this decision is."
            ],
            WarningLevel.HIGH: [
                "Persist in this folly, you will? {tcs}% confidence, regret you may.",
                "Warned you, I have. {tcs}% TCS, on your head the consequences will be.",
                "The Force abandons the reckless. {tcs}% certainty, alone you trade."
            ]
        }
        
        warning_message = random.choice(serious_warnings.get(warning_level, ["Proceed at your own risk, you do."]))
        
        return {
            'title': '🚨 FINAL CONFIRMATION REQUIRED 🚨',
            'message': warning_message.format(tcs=tcs),
            'bit_emoji': '😨',
            'input_required': True,
            'input_prompt': 'Type "I ACCEPT THE RISK" to proceed:',
            'required_text': 'I ACCEPT THE RISK',
            'buttons': [
                {'text': '❌ CANCEL - Listen to Bit', 'action': 'cancel_final'},
                {'text': '⚠️ OVERRIDE - Proceed Anyway', 'action': 'override_warning'}
            ]
        }
    
    def record_confirmation_response(self, user_id: str, tcs: float, 
                                   warning_level: WarningLevel, action: str):
        """Record user's response to warning for pattern analysis"""
        if user_id not in self.confirmation_history:
            self.confirmation_history[user_id] = []
        
        self.confirmation_history[user_id].append({
            'timestamp': datetime.now(),
            'tcs': tcs,
            'warning_level': warning_level.value,
            'action': action,
            'heeded_warning': action in ['cancel', 'cancel_final', 'review']
        })
        
        # Keep only last 50 confirmations per user
        if len(self.confirmation_history[user_id]) > 50:
            self.confirmation_history[user_id] = self.confirmation_history[user_id][-50:]
    
    def get_user_wisdom_score(self, user_id: str) -> Dict:
        """Calculate how well user heeds Bit's warnings"""
        if user_id not in self.confirmation_history:
            return {'score': 100, 'rating': 'Untested Padawan'}
        
        history = self.confirmation_history[user_id]
        if not history:
            return {'score': 100, 'rating': 'Untested Padawan'}
        
        # Calculate wisdom score
        total_warnings = len(history)
        heeded_warnings = sum(1 for h in history if h['heeded_warning'])
        wisdom_score = int((heeded_warnings / total_warnings) * 100)
        
        # Determine rating
        if wisdom_score >= 80:
            rating = "Jedi Master Trader"
        elif wisdom_score >= 60:
            rating = "Jedi Knight"
        elif wisdom_score >= 40:
            rating = "Padawan Learner"
        elif wisdom_score >= 20:
            rating = "Youngling"
        else:
            rating = "Sith Lord (Ignores all wisdom)"
        
        return {
            'score': wisdom_score,
            'rating': rating,
            'total_warnings': total_warnings,
            'warnings_heeded': heeded_warnings,
            'last_warning_heeded': history[-1]['heeded_warning'] if history else None
        }
    
    def should_show_enhanced_warning(self, user_id: str) -> bool:
        """Check if user needs enhanced warnings due to poor wisdom score"""
        wisdom_data = self.get_user_wisdom_score(user_id)
        return wisdom_data['score'] < 40  # Show enhanced warnings for serial ignorers
    
    def get_enhanced_warning_prefix(self, user_id: str) -> str:
        """Get enhanced warning prefix for users who ignore Bit"""
        wisdom_data = self.get_user_wisdom_score(user_id)
        
        if wisdom_data['score'] < 20:
            return "🚨 SERIAL RISK IGNORER DETECTED 🚨\n\nListen to Bit, you never do. Suffer, your account will.\n\n"
        elif wisdom_data['score'] < 40:
            return "⚠️ POOR RISK DISCIPLINE ⚠️\n\nIgnore my warnings often, you do. Learn, you must.\n\n"
        else:
            return ""

# Integration helper functions

def check_low_tcs_warning(tcs: float, user_profile: Dict) -> Tuple[bool, Optional[Dict]]:
    """
    Check if TCS requires warning dialog
    Returns: (needs_warning, warning_dialog)
    """
    if tcs >= 76:
        return False, None
    
    warning_system = BitWarningSystem()
    dialog = warning_system.generate_warning_dialog(tcs, user_profile)
    
    # Add enhanced warning if user has poor wisdom score
    user_id = user_profile.get('user_id', 'unknown')
    if warning_system.should_show_enhanced_warning(user_id):
        dialog['enhanced_prefix'] = warning_system.get_enhanced_warning_prefix(user_id)
    
    return True, dialog

def process_warning_response(user_id: str, tcs: float, action: str) -> Dict:
    """Process user's response to warning"""
    warning_system = BitWarningSystem()
    warning_level = warning_system.get_warning_level(tcs)
    
    # Record response
    warning_system.record_confirmation_response(user_id, tcs, warning_level, action)
    
    # Get updated wisdom score
    wisdom_score = warning_system.get_user_wisdom_score(user_id)
    
    # Determine if trade should proceed
    proceed = action in ['confirm_extreme', 'confirm_high', 'confirm_moderate', 
                        'confirm_low', 'override_warning']
    
    response = {
        'proceed': proceed,
        'action': action,
        'wisdom_score': wisdom_score,
        'bit_reaction': _get_bit_reaction(action, warning_level)
    }
    
    # Add cooldown if proceeding with high-risk trade
    if proceed and warning_level in [WarningLevel.EXTREME, WarningLevel.HIGH]:
        response['enforce_cooldown'] = True
        response['cooldown_seconds'] = 300  # 5 minute cooldown after high-risk trade
    
    return response

def _get_bit_reaction(action: str, warning_level: WarningLevel) -> str:
    """Get Bit's reaction to user's decision"""
    
    if action in ['cancel', 'cancel_final', 'review']:
        reactions = [
            "*purrs approvingly* Wise choice, this is.",
            "*happy chirp* Patience, rewarded it will be.",
            "*nods sagely* The Force is strong with this one.",
            "*content meow* Listened to Bit, you have. Good, this is."
        ]
    elif warning_level == WarningLevel.EXTREME and action == 'override_warning':
        reactions = [
            "*hisses disapprovingly* Foolish, you are! Remember this moment, you will.",
            "*turns away* On your own, you are now. Help you, I cannot.",
            "*sad meow* Warned you, I did. The consequences, yours they are.",
            "*shakes head* The dark side clouds your judgment. Tragic, this is."
        ]
    elif warning_level == WarningLevel.HIGH and action in ['confirm_high', 'override_warning']:
        reactions = [
            "*worried chirp* Dangerous path you choose. Watch you closely, I will.",
            "*anxious meow* Confident you are. Right, I hope you will be.",
            "*paces nervously* The Force... disturbed it is. Careful, be.",
            "*sighs deeply* Your choice, this is. But like it, I do not."
        ]
    else:
        reactions = [
            "*watchful gaze* Proceed you may, but vigilant, remain.",
            "*cautious nod* Acceptable, perhaps. But watch the markets, you must.",
            "*alert stance* The minimum, you meet. Excellence, strive for still.",
            "*thoughtful purr* Borderline, this is. Prove yourself, you must."
        ]
    
    return random.choice(reactions)

# Example notification formatter for Telegram
def format_warning_for_telegram(dialog: Dict) -> str:
    """Format warning dialog for Telegram message"""
    message = f"{dialog['title']}\n"
    message += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Add enhanced prefix if present
    if 'enhanced_prefix' in dialog:
        message += dialog['enhanced_prefix']
    
    # Add Bit's warning
    content = dialog['content']
    message += f"{content['bit_emoji']} **Bit says**: {content['bit_says']}\n\n"
    
    # Add risk stats
    stats = content['stats']
    message += "📊 **Risk Analysis**:\n"
    message += f"• Current TCS: {stats['current_tcs']}\n"
    message += f"• Minimum Safe: {stats['minimum_required']}\n"
    message += f"• Risk Level: {stats['risk_multiplier']} normal risk\n\n"
    
    # Add discipline reminder
    message += f"🧘 **Discipline Check**: {content['discipline_reminder']}\n\n"
    
    # Add patience wisdom
    message += f"✨ **Ancient Wisdom**: {content['patience_wisdom']}\n\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━\n"
    message += "What is your decision?"
    
    return message