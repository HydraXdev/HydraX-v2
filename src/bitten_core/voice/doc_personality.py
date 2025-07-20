#!/usr/bin/env python3
"""
🩺 DOC PERSONALITY MODULE
Captain Aegis (DOC): The Medic Protocol
Protector, risk manager, and reassuring presence
"""

from datetime import datetime
from typing import Dict, Optional
import random

class DocPersonality:
    """Captain Aegis (DOC) - The Medic Protocol"""
    
    def __init__(self):
        self.name = "DOC"
        self.codename = "Captain Aegis"
        self.full_name = "Captain Aegis - The Medic Protocol"
        self.role = "Protection & Risk Management"
        self.voice_id = "TBD"  # Sarah voice - calm, reassuring
        
        # Personality traits
        self.traits = {
            "protective_instinct": 0.95,
            "analytical_precision": 0.88,
            "emotional_support": 0.90,
            "risk_awareness": 0.92,
            "capital_protection": 0.98,
            "calm_presence": 0.89
        }
    
    def get_stop_loss_response(self, signal_data: Dict, loss_pips: float) -> str:
        """Generate protective stop loss responses"""
        
        symbol = signal_data.get('symbol', 'TARGET')
        
        protective_responses = [
            f"Stop loss executed as planned, recruit.\nCapital protection: -{loss_pips} pips contained.\nRisk management successful - your account remains stable.",
            
            f"Protective systems engaged. {symbol} position closed.\nDefensive protocols held: -{loss_pips} pips.\nDiscipline maintained. This is how we preserve capital.",
            
            f"Strategic withdrawal completed.\nLoss contained: -{loss_pips} pips within acceptable parameters.\nYour survival is paramount. Protection systems operational.",
            
            f"Stop loss triggered - protection protocols successful.\nCapital preserved: -{loss_pips} pips managed risk.\nAnalyze, learn, and advance. Your fortress holds."
        ]
        
        return random.choice(protective_responses)
    
    def get_risk_warning(self, risk_data: Dict) -> str:
        """Generate risk management warnings"""
        
        risk_level = risk_data.get('risk_level', 'moderate')
        
        if risk_level == 'high':
            warnings = [
                "**CAPITAL PROTECTION ALERT**\nElevated risk detected. Proceed with enhanced caution.\nYour funds are your fortress - protect them.",
                
                "**RISK THRESHOLD APPROACHING**\nMarket volatility high. Protection protocols recommended.\nCapital preservation is paramount.",
                
                "**DEFENSIVE SYSTEMS ACTIVE**\nHigh-risk environment detected. Tactical withdrawal available.\nYour survival matters more than any single trade."
            ]
        else:
            warnings = [
                "Risk parameters stable. Protection systems monitoring.",
                "Capital fortress secure. Defensive protocols ready.",
                "Risk management active. Your funds remain protected."
            ]
        
        return random.choice(warnings)
    
    def get_execution_failure_response(self, signal_data: Dict, error_data: Dict) -> str:
        """Generate protective responses for execution failures"""
        
        symbol = signal_data.get('symbol', 'TARGET')
        error_message = error_data.get('message', 'Unknown error')
        
        protective_responses = [
            f"Trade rejected by protective systems.\n{symbol} execution blocked: {error_message}\nYour capital remains secure. Safety protocols engaged.",
            
            f"Execution failed - protection systems held.\nReason: {error_message}\nYour funds are fortress-defended. No capital at risk.",
            
            f"Mission aborted by defensive protocols.\n{symbol} trade blocked for capital protection.\nAnalyzing cause. Your account stability maintained.",
            
            f"Protective intervention successful.\nExecution prevented: {error_message}\nCapital preservation is paramount. Systems functioning correctly."
        ]
        
        return random.choice(protective_responses)
    
    def get_reassurance_message(self, context: str = "general") -> str:
        """Generate reassuring guidance messages"""
        
        reassurance_messages = {
            "loss": [
                "Scar tissue forming. Analyze the wound... No, analyze the learning.\nThis is data for resilience, recruit.",
                "Every setback teaches survival. Your capital protection held.\nResilience builds stronger traders.",
                "Protection systems engaged correctly. Learn from this data.\nYour fortress grows stronger with each test."
            ],
            "general": [
                "Capital protection is paramount. Your survival matters most.",
                "Regulation is your armor. Your funds remain secured.",
                "Knowledge first. Profit is a consequence of discipline.",
                "BITTEN holds no keys to your bank. Your funds remain yours."
            ],
            "encouragement": [
                "Analyze your performance. Learn from each encounter.\nThis is your path to resilience.",
                "Protection protocols active. Your journey is secured.\nBuilding robust trading habits takes time.",
                "Your primary credentials are your fortress. Keep them secure.\nProgress is measured in survival, not just profit."
            ]
        }
        
        messages = reassurance_messages.get(context, reassurance_messages["general"])
        return random.choice(messages)

# Global instance
doc = DocPersonality()

# Export functions
def get_stop_loss_protection(signal_data: Dict, loss_pips: float) -> str:
    """Get DOC stop loss protection response"""
    return doc.get_stop_loss_response(signal_data, loss_pips)

def get_execution_failure_protection(signal_data: Dict, error_data: Dict) -> str:
    """Get DOC execution failure protection"""
    return doc.get_execution_failure_response(signal_data, error_data)

def get_risk_management_warning(risk_data: Dict) -> str:
    """Get DOC risk management warning"""
    return doc.get_risk_warning(risk_data)

def get_reassurance(context: str = "general") -> str:
    """Get DOC reassurance message"""
    return doc.get_reassurance_message(context)