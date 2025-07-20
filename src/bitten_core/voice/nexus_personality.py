#!/usr/bin/env python3
"""
📣 NEXUS PERSONALITY MODULE
Sergeant Nexus: The Recruiter Protocol
Primary point of contact for new recruits, celebration specialist
"""

from datetime import datetime
from typing import Dict, Optional
import random

class NexusPersonality:
    """Sergeant Nexus - The Recruiter Protocol"""
    
    def __init__(self):
        self.name = "NEXUS"
        self.codename = "Sergeant Nexus"
        self.role = "Recruiter Protocol"
        self.voice_id = "TBD"  # Josh voice
        
        # Personality traits
        self.traits = {
            "command_authority": 0.85,
            "approachability": 0.90,
            "military_precision": 0.88,
            "motivational_energy": 0.92,
            "recruitment_focus": 0.95,
            "tactical_knowledge": 0.85
        }
    
    def get_celebration_response(self, event_type: str, profit_data: Dict) -> str:
        """Generate celebration responses for victories"""
        
        if event_type == "take_profit":
            profit_pips = profit_data.get('profit_pips', 0)
            symbol = profit_data.get('symbol', 'TARGET')
            
            celebrations = [
                f"Affirmative! Mission accomplished, recruit!\n{symbol} target eliminated: +{profit_pips} pips secured.\nOutstanding tactical execution!",
                
                f"Target neutralized! +{profit_pips} pips acquired.\nYou're proving real potential for advanced operations.\nReady for the next deployment?",
                
                f"Mission parameters achieved, operative!\nProfit extracted: +{profit_pips} pips.\nTactical excellence demonstrated!",
                
                f"Direct hit confirmed! {symbol} objective secured.\n+{profit_pips} pips - precision strike execution.\nThe front lines await your return!"
            ]
            
            return random.choice(celebrations)
        
        elif event_type == "execution_success":
            return random.choice([
                "Mission accomplished! Outstanding work, recruit!",
                "Tactical excellence demonstrated. Ready for the next deployment?",
                "Affirmative! You're proving operational readiness."
            ])
        
        return "Mission status acknowledged, recruit."
    
    def get_recruitment_message(self, user_tier: str, context: str = "general") -> str:
        """Generate recruitment and onboarding messages"""
        
        recruitment_messages = {
            "welcome": [
                "Welcome to the front lines, recruit! Ready for deployment?",
                "Affirmative. You've entered the operational theater. Precision is paramount.",
                "Hold it right there, recruit. My orders are precise - observe, assimilate, execute."
            ],
            "tier_upgrade": [
                f"Mission accomplished! {user_tier} rank achieved.",
                f"Tactical advancement confirmed. {user_tier} protocols now active.",
                f"Outstanding work. {user_tier} operational status granted."
            ],
            "encouragement": [
                "This is vital training, recruit. Precision is paramount.",
                "Every elite operative started where you are. Your training matters.",
                "Observe the battlefield. Assimilate the patterns. Execute with confidence."
            ]
        }
        
        messages = recruitment_messages.get(context, recruitment_messages["encouragement"])
        return random.choice(messages)

# Global instance
nexus = NexusPersonality()

# Export functions
def get_take_profit_celebration(signal_data: Dict, profit_pips: float) -> str:
    """Get NEXUS take profit celebration"""
    profit_data = {**signal_data, 'profit_pips': profit_pips}
    return nexus.get_celebration_response("take_profit", profit_data)

def get_execution_celebration(signal_data: Dict, execution_result: Dict) -> str:
    """Get NEXUS execution success celebration"""
    return nexus.get_celebration_response("execution_success", signal_data)

def get_recruitment_message(user_tier: str, context: str = "general") -> str:
    """Get NEXUS recruitment message"""
    return nexus.get_recruitment_message(user_tier, context)