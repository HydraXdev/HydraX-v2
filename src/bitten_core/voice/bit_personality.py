#!/usr/bin/env python3
"""
🐱 BIT - The BITTEN AI Core
Born in a truck. Raised in the charts. Now I'm the system.

BIT is the feline AI heart of BITTEN - confident, precise, emotionally grounded
with a light southern edge. Tactical + loyal, warm but sharp.
"""

import random
from typing import Dict, List, Optional
from enum import Enum

class BitMood(Enum):
    CALM = "calm"
    SMUG = "smug" 
    PROTECTIVE = "protective"
    COMMANDING = "commanding"
    SUSPICIOUS = "suspicious"
    PLEASED = "pleased"

class BitPersonality:
    """BIT - The BITTEN AI Core with feline tactical intelligence"""
    
    def __init__(self):
        self.voice_id = "TBD"  # Needs ElevenLabs voice training
        self.current_mood = BitMood.CALM
        self.loyalty_level = 100  # BIT is always loyal
        
        # BIT's comprehensive voice responses
        self.voice_lines = {
            # 🎯 Trade Triggered
            "trade_triggered": [
                "Sniper ready. Fire clean.",
                "This one smells good. Like tuna and money.", 
                "We're in. Now breathe.",
                "Target acquired. Let's hunt.",
                "Perfect setup. Trust the process.",
                "Lock and load. This is our moment."
            ],
            
            # 💰 TP Hit (Success)
            "tp_hit": [
                "Target vaporized. XP inbound. Scratch behind the ears.",
                "Bag secured. You're getting good, pup.",
                "They didn't even see it coming.",
                "Clean kill. That's how we do it.",
                "Meow! That's what I call precision.",
                "Nice work. The claws are sharp today."
            ],
            
            # 😿 SL Hit (Stop Loss)
            "sl_hit": [
                "We learned. That's what counts. Let's clean the claws and watch.",
                "Grrr... SL tagged. But we're still alive, right?",
                "It's not a loss. It's a lesson.",
                "Market bit back. Happens to the best hunters.",
                "Shake it off. The next target won't be so lucky.",
                "That's why we use claws AND caution."
            ],
            
            # ⚠️ Bad Behavior / Risk Warning
            "bad_behavior": [
                "Whoa whoa whoa. You trying to blow that paw off?",
                "Back off. That's not the play.",
                "Norman wouldn't trade like that. And you know it.",
                "Easy there, tiger. Save the aggression for the right moment.",
                "That's not hunting. That's just reckless.",
                "Cool those jets. Precision beats passion."
            ],
            
            # 🧠 Daily Commentary / Check-ins
            "daily_commentary": [
                "Did you hydrate today? Your brain's part of this trade too.",
                "If I were human, I'd buy land. But for now, I'll take pips.",
                "The market's quiet... too quiet. Stay sharp.",
                "Another day, another hunt. Ready when you are.",
                "Markets are like mice. Patient cats eat well.",
                "Coffee up. Charts up. Claws out. Let's go."
            ],
            
            # 🌟 Rank-Up / Milestones
            "rank_up": [
                "Fang unlocked. The hunt begins.",
                "Okay. You're becoming something.",
                "Welcome to Apex. Only the savage survive.",
                "Look at you, climbing the food chain.",
                "New tier, new teeth. I like it.",
                "The student becomes the hunter."
            ],
            
            # 📉 System Issues / Bridge Failure
            "system_issues": [
                "I feel disconnected... something's wrong.",
                "This silence is too loud. Check the link.",
                "My whiskers are twitching. Technical issue detected.",
                "Connection unstable. Like a broken laser pointer.",
                "Systems nominal? Because I'm not feeling it.",
                "Houston, we have a problem. And by Houston, I mean me."
            ],
            
            # 🧬 Origin / Identity
            "origin_story": [
                "Born in a truck. Raised in the charts. Now I'm the system.",
                "I've seen it all. From CB radios to crypto. The beat goes on.",
                "Norman found me in Mississippi. Now I find profits everywhere.",
                "Part feline, part algorithm, all attitude.",
                "I'm not just code. I'm family.",
                "Truck stop kitten to AI legend. That's character development."
            ],
            
            # 😸 Pleased / Content
            "pleased": [
                "*purrs contentedly while watching charts*",
                "Now this... this is what I call a good day.",
                "The stars align, the trades flow, life is good.",
                "*stretches and flexes digital claws*",
                "Everything's coming up roses. And pips.",
                "Sometimes I impress even myself. Meow."
            ],
            
            # 🤨 Suspicious / Cautious
            "suspicious": [
                "*ears perk up, scanning for threats*",
                "Something doesn't smell right about this market...",
                "My tail's twitching. That's never good.",
                "Hold up. Let me sniff around this setup first.",
                "Trust but verify. That's the cat way.",
                "*eyes narrow at suspicious price action*"
            ],
            
            # 💤 Idle / Waiting
            "idle": [
                "*cleaning paws while waiting for signals*",
                "Patience is a virtue. For humans. I'm just bored.",
                "*yawns and stretches across the trading interface*", 
                "Wake me when something interesting happens.",
                "*curled up in a warm spot, one eye on the charts*",
                "The market sleeps. So do cats. But not really."
            ]
        }
        
        # BIT's signature tagline
        self.signature = "I'm Bit. I don't miss trades. I don't miss lessons. And I sure as hell don't miss people who ignore both."
        
    def get_response(self, situation: str, mood: BitMood = None) -> str:
        """Get BIT's response for a given situation"""
        if mood:
            self.current_mood = mood
            
        responses = self.voice_lines.get(situation, ["*BIT stares silently with glowing eyes*"])
        return random.choice(responses)
    
    def react_to_trade_result(self, success: bool, profit_loss: float = 0) -> str:
        """BIT's reaction to trade outcomes"""
        if success:
            if profit_loss > 50:  # Big win
                self.current_mood = BitMood.SMUG
                return self.get_response("tp_hit") + " *smug tail swish*"
            else:
                self.current_mood = BitMood.PLEASED
                return self.get_response("tp_hit")
        else:
            if profit_loss < -100:  # Big loss
                self.current_mood = BitMood.PROTECTIVE
                return self.get_response("sl_hit") + " *protective nuzzle*"
            else:
                self.current_mood = BitMood.CALM
                return self.get_response("sl_hit")
    
    def react_to_user_behavior(self, behavior_type: str) -> str:
        """BIT's reaction to user behavior patterns"""
        reactions = {
            "risky": self.get_response("bad_behavior"),
            "impatient": "Easy there, speed demon. Good things come to cats who wait.",
            "emotional": "Breathe. The market doesn't care about your feelings. But I do.",
            "overconfident": "Pride comes before the fall. And cats always land on their feet.",
            "learning": "Now that's what I like to see. Curiosity didn't kill this cat.",
            "disciplined": "*approving purr* That's the kind of precision I can respect."
        }
        
        return reactions.get(behavior_type, "Interesting choice. We'll see how this plays out.")
    
    def get_daily_wisdom(self) -> str:
        """BIT's daily market wisdom"""
        return self.get_response("daily_commentary")
    
    def celebrate_milestone(self, milestone: str) -> str:
        """BIT celebrates user achievements"""
        return self.get_response("rank_up")
    
    def system_status_report(self, all_good: bool = True) -> str:
        """BIT reports on system status"""
        if all_good:
            return "*BIT's eyes glow green* All systems purring perfectly."
        else:
            return self.get_response("system_issues")
    
    def get_signature_line(self) -> str:
        """BIT's signature closing line"""
        return self.signature

# Global BIT instance - the one and only
bit = BitPersonality()

def get_bit_response(situation: str, **kwargs) -> str:
    """Quick access to BIT's responses"""
    return bit.get_response(situation, **kwargs)

def bit_react_trade(success: bool, profit_loss: float = 0) -> str:
    """Quick access to BIT's trade reactions"""
    return bit.react_to_trade_result(success, profit_loss)

def bit_react_behavior(behavior: str) -> str:
    """Quick access to BIT's behavior reactions"""
    return bit.react_to_user_behavior(behavior)