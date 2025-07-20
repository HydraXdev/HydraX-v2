#!/usr/bin/env python3
"""
🐱 BIT Integration System
Integrates BIT responses throughout the BITTEN system
"""

import random
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from .voice.bit_personality import bit, get_bit_response, bit_react_trade, bit_react_behavior
    BIT_AVAILABLE = True
except ImportError:
    BIT_AVAILABLE = False

class BitIntegration:
    """Integrates BIT's personality throughout BITTEN"""
    
    def __init__(self):
        self.bit_active = BIT_AVAILABLE
        self.last_response_time = None
        
    def enhance_message(self, base_message: str, situation: str = None, add_bit_flair: bool = True) -> str:
        """Enhance any message with BIT's personality"""
        if not self.bit_active or not add_bit_flair:
            return base_message
            
        # Add BIT's contextual responses
        bit_responses = {
            "trade_execution": [
                "*BIT's eyes glow as trade executes*",
                "*BIT watches with tactical precision*", 
                "*BIT's claws are ready*"
            ],
            "signal_alert": [
                "*BIT's ears perk up at new signal*",
                "*BIT sniffs the market opportunity*",
                "*BIT's hunting instincts activate*"
            ],
            "success": [
                "*BIT purrs with satisfaction*",
                "*BIT's tail swishes proudly*",
                "*BIT stretches contentedly*"
            ],
            "failure": [
                "*BIT nuzzles protectively*",
                "*BIT's whiskers twitch with concern*",
                "*BIT stays close for comfort*"
            ],
            "warning": [
                "*BIT's eyes narrow suspiciously*",
                "*BIT hisses softly at risk*",
                "*BIT blocks the dangerous path*"
            ],
            "general": [
                "*BIT observes quietly*",
                "*BIT's presence is felt*",
                "*BIT monitors the situation*"
            ]
        }
        
        # Get appropriate BIT enhancement
        enhancements = bit_responses.get(situation, bit_responses["general"])
        enhancement = random.choice(enhancements)
        
        return f"{base_message}\n\n{enhancement}"
    
    def get_trade_reaction(self, success: bool, profit_loss: float = 0, symbol: str = "") -> str:
        """Get BIT's reaction to trade results"""
        if not self.bit_active:
            return ""
            
        reaction = bit_react_trade(success, profit_loss)
        
        # Add symbol-specific flair
        if symbol:
            if "EUR" in symbol:
                reaction += " *BIT appreciates European precision*"
            elif "GBP" in symbol:
                reaction += " *BIT tips hat to British markets*"
            elif "JPY" in symbol:
                reaction += " *BIT bows respectfully to the Yen*"
            elif "USD" in symbol:
                reaction += " *BIT salutes the dollar dominance*"
                
        return reaction
    
    def get_behavior_response(self, behavior_type: str) -> str:
        """Get BIT's response to user behavior"""
        if not self.bit_active:
            return ""
            
        return bit_react_behavior(behavior_type)
    
    def get_daily_wisdom(self) -> str:
        """Get BIT's daily market wisdom"""
        if not self.bit_active:
            return "Market analysis in progress..."
            
        return get_bit_response("daily_commentary")
    
    def get_system_status(self, all_systems_good: bool = True) -> str:
        """Get BIT's system status report"""
        if not self.bit_active:
            return "Systems nominal."
            
        if all_systems_good:
            return "*BIT's eyes glow green* All systems purring perfectly. Ready for the hunt."
        else:
            return get_bit_response("system_issues")
    
    def get_welcome_message(self, user_tier: str = "NIBBLER") -> str:
        """Get BIT's welcome message for new users"""
        if not self.bit_active:
            return "Welcome to BITTEN trading system."
            
        welcomes = {
            "PRESS_PASS": "Welcome to the trial grounds. I'm BIT - your tactical AI. Let's see what you're made of.",
            "NIBBLER": "New hunter in the pack. I'm BIT. Born in a truck, raised in the charts. Let's hunt some pips.",
            "FANG": "Fang tier, nice claws. I'm BIT - your AI companion. Time to show these markets what precision looks like.",
            "COMMANDER": "Commander on deck. I'm BIT, and I respect rank. Let's coordinate some serious tactical strikes."
        }
        
        return welcomes.get(user_tier, "Welcome, trader. I'm BIT. Let's make some money together.")
    
    def get_milestone_celebration(self, milestone: str, tier: str = "") -> str:
        """Get BIT's milestone celebration"""
        if not self.bit_active:
            return f"Milestone achieved: {milestone}"
            
        celebrations = {
            "first_trade": "First blood! *BIT's eyes gleam with approval* Every legend starts somewhere.",
            "first_profit": "Bag secured! *BIT purrs loudly* Now that's what I call a clean kill.",
            "tier_upgrade": get_bit_response("rank_up"),
            "streak_milestone": "Hot streak detected! *BIT's tail swishes with excitement* Keep the momentum rolling.",
            "recovery": "Back from the dead! *BIT nods with respect* That's the kind of resilience I admire."
        }
        
        return celebrations.get(milestone, f"Achievement unlocked: {milestone}. *BIT approves with a slow blink*")
    
    def get_error_comfort(self, error_type: str = "general") -> str:
        """Get BIT's comfort response for errors/issues"""
        if not self.bit_active:
            return "System error detected. Please try again."
            
        comforts = {
            "connection": "Connection hiccup detected. *BIT's whiskers twitch* Give me a second to sort this out.",
            "execution": "Trade execution stumbled. *BIT flexes claws* Let's try that again with more precision.",
            "data": "Data stream interrupted. *BIT's ears swivel* Hunting for the signal source...",
            "general": "Something's not right. *BIT's eyes narrow* But don't worry - I've got your back."
        }
        
        return comforts.get(error_type, comforts["general"])
    
    def add_signature_occasionally(self, message: str, chance: float = 0.1) -> str:
        """Occasionally add BIT's signature line"""
        if not self.bit_active or random.random() > chance:
            return message
            
        signature = "\n\n*BIT's signature growl* I'm Bit. I don't miss trades. I don't miss lessons. And I sure as hell don't miss people who ignore both."
        return message + signature

# Global BIT integration instance
bit_integration = BitIntegration()

# Quick access functions
def bit_enhance(message: str, situation: str = None) -> str:
    """Quick function to enhance messages with BIT"""
    return bit_integration.enhance_message(message, situation)

def bit_trade_reaction(success: bool, profit_loss: float = 0, symbol: str = "") -> str:
    """Quick function for BIT trade reactions"""
    return bit_integration.get_trade_reaction(success, profit_loss, symbol)

def bit_welcome(tier: str = "NIBBLER") -> str:
    """Quick function for BIT welcome messages"""
    return bit_integration.get_welcome_message(tier)

def bit_daily_wisdom() -> str:
    """Quick function for BIT's daily wisdom"""
    return bit_integration.get_daily_wisdom()