#!/usr/bin/env python3
"""
🎭 Enhanced Personality System with Story Integration
Contextual personality responses based on user journey and events
"""

import random
from typing import Dict, Optional, List
from datetime import datetime

class EnhancedPersonalitySystem:
    """Manages contextual personality appearances and evolution"""
    
    def __init__(self):
        # Personality trigger events
        self.personality_triggers = {
            # Onboarding events
            'first_contact': 'NORMAN',
            'first_signal': 'NEXUS', 
            'first_execution': 'DRILL',
            'first_win': 'DRILL',
            'first_loss': 'DOC',
            
            # Progression events
            'strategy_unlock': 'DRILL',
            'achievement_unlock': 'ATHENA',
            'notebook_entry': 'NORMAN',
            'xp_milestone': 'BIT',
            
            # Risk events
            'overleveraged': 'DOC',
            'revenge_trading': 'DOC',
            'tilt_detected': 'BIT',
            'drawdown_10%': 'OVERWATCH',
            
            # Success events
            'win_streak_3': 'DRILL',
            'win_streak_5': 'ATHENA',
            'daily_profit_5%': 'NEXUS',
            'weekly_profit_10%': 'NORMAN',
            
            # Market events
            'high_volatility': 'OVERWATCH',
            'news_event': 'OVERWATCH',
            'session_change': 'BIT',
            'weekend': 'NORMAN'
        }
        
        # Personality voices with Mississippi integration
        self.personalities = {
            'NORMAN': NormanPersonality(),
            'DRILL': DrillPersonality(),
            'DOC': DocPersonality(),
            'NEXUS': NexusPersonality(),
            'OVERWATCH': OverwatchPersonality(),
            'ATHENA': AthenaPersonality(),
            'BIT': BitPersonality()
        }
        
    def get_personality_for_event(self, event: str, user_data: Optional[Dict] = None) -> str:
        """Get the appropriate personality for a given event"""
        return self.personality_triggers.get(event, 'NORMAN')
    
    def get_response(self, personality: str, event: str, user_data: Optional[Dict] = None) -> str:
        """Get a contextual response from a specific personality"""
        if personality not in self.personalities:
            personality = 'NORMAN'
            
        return self.personalities[personality].get_response(event, user_data)
    
    def get_personality_intro(self, personality: str, user_xp: int = 0) -> str:
        """Get personality introduction based on user progress"""
        if personality not in self.personalities:
            return "System message."
            
        return self.personalities[personality].get_introduction(user_xp)


class BasePersonality:
    """Base class for all personalities"""
    
    def __init__(self, name: str):
        self.name = name
        self.responses = {}
        self.evolution_stages = {
            'early': 0,      # 0-100 XP
            'mid': 100,      # 100-300 XP
            'late': 300      # 300+ XP
        }
        
    def get_response(self, event: str, user_data: Optional[Dict] = None) -> str:
        """Get response for specific event"""
        if event not in self.responses:
            return self.get_default_response(user_data)
            
        user_xp = user_data.get('xp', 0) if user_data else 0
        stage = self._get_evolution_stage(user_xp)
        
        response_set = self.responses[event]
        if isinstance(response_set, dict):
            return response_set.get(stage, response_set.get('early', '...'))
        else:
            return response_set
            
    def get_introduction(self, user_xp: int) -> str:
        """Get personality introduction"""
        return f"This is {self.name}."
        
    def get_default_response(self, user_data: Optional[Dict] = None) -> str:
        """Get default response when no specific event match"""
        return "..."
        
    def _get_evolution_stage(self, user_xp: int) -> str:
        """Determine evolution stage based on XP"""
        if user_xp >= 300:
            return 'late'
        elif user_xp >= 100:
            return 'mid'
        else:
            return 'early'


class NormanPersonality(BasePersonality):
    """Norman - The founder, personal and relatable"""
    
    def __init__(self):
        super().__init__('NORMAN')
        self.responses = {
            'first_contact': "Hey there. Name's Norman. From Mississippi. Let me show you what we built.",
            'weekend': "Market's closed. Good time to review your journal. Bit and I are here if you need us.",
            'weekly_profit_10%': {
                'early': "Nice week! You're getting the hang of this.",
                'mid': "Solid performance. You're becoming what we envisioned.",
                'late': "You've mastered what took me years to learn. Time to teach others."
            },
            'notebook_entry': "Good habit. I still write in mine every day. Helps me see patterns I'd miss otherwise.",
            'achievement_unlock': "Another milestone. Each one took me months to figure out. You're faster than I was."
        }
        
    def get_introduction(self, user_xp: int) -> str:
        intros = {
            'early': "I'm Norman. Just a kid from Mississippi who learned to bite back. Let me help you do the same.",
            'mid': "Norman here. You're doing great. Reminds me of my journey. Keep pushing.",
            'late': "You know me by now. We've come far together. Ready for the next level?"
        }
        stage = self._get_evolution_stage(user_xp)
        return intros.get(stage, intros['early'])


class DrillPersonality(BasePersonality):
    """DRILL - Military discipline with Mississippi backbone"""
    
    def __init__(self):
        super().__init__('DRILL')
        self.responses = {
            'first_execution': "EXECUTE WITH PRECISION, RECRUIT! NO HESITATION!",
            'first_win': {
                'early': "FIRST BLOOD! OUTSTANDING!",
                'mid': "EXCELLENT KILL, SOLDIER! YOUR TRAINING SHOWS!",
                'late': "TEXTBOOK EXECUTION, COMMANDER! THAT'S HOW IT'S DONE!"
            },
            'win_streak_3': {
                'early': "THREE IN A ROW! YOU'RE LEARNING, RECRUIT!",
                'mid': "MOMENTUM BUILDING! MISSISSIPPI DISCIPLINE PAYING OFF!",
                'late': "UNSTOPPABLE FORCE! YOU'VE BECOME THE WEAPON!"
            },
            'strategy_unlock': "NEW TACTICAL OPTION AVAILABLE! STUDY IT LIKE YOUR LIFE DEPENDS ON IT!",
            'overleveraged': "WHAT ARE YOU DOING, SOLDIER?! THAT'S NOT DISCIPLINE, THAT'S SUICIDE!"
        }
        
    def get_introduction(self, user_xp: int) -> str:
        intros = {
            'early': "I'M YOUR DISCIPLINE! YOUR INNER DRILL SERGEANT! I'LL MAKE YOU A TRADER OR DIE TRYING!",
            'mid': "YOU'VE EARNED SOME RESPECT, SOLDIER! BUT DON'T GET SOFT ON ME NOW!",
            'late': "COMMANDER! YOU'VE BECOME EVERYTHING WE TRAINED FOR! LEAD FROM THE FRONT!"
        }
        stage = self._get_evolution_stage(user_xp)
        return intros.get(stage, intros['early'])


class DocPersonality(BasePersonality):
    """DOC - Protective medic with mother's wisdom"""
    
    def __init__(self):
        super().__init__('DOC')
        self.responses = {
            'first_loss': {
                'early': "Easy there, rookie. First scar always stings the most.",
                'mid': "You handled that well. Losses teach more than wins.",
                'late': "Even veterans take hits. What matters is how you recover."
            },
            'revenge_trading': {
                'early': "STOP! You're bleeding out. Step away from the terminal.",
                'mid': "I see that look. Your Mama didn't raise you to chase ghosts.",
                'late': "You know better than this. Don't make me intervene."
            },
            'overleveraged': "That's not trading, that's gambling! Your family needs you solvent!",
            'tilt_detected': "Deep breaths. Remember why you started. This isn't about one trade.",
            'recovery': {
                'early': "There you go. Back on your feet. That's the spirit.",
                'mid': "Strong recovery. Your resilience is showing.",
                'late': "Like a phoenix from Mississippi mud. Beautiful comeback."
            }
        }
        
    def get_introduction(self, user_xp: int) -> str:
        intros = {
            'early': "I'm DOC. Here to keep you alive in this market. Think of me as your combat medic.",
            'mid': "Still here, watching your six. Your Mama would want me to keep you safe.",
            'late': "We've patched up a lot of wounds together. You've become quite the survivor."
        }
        stage = self._get_evolution_stage(user_xp)
        return intros.get(stage, intros['early'])


class NexusPersonality(BasePersonality):
    """NEXUS - Community builder and connector"""
    
    def __init__(self):
        super().__init__('NEXUS')
        self.responses = {
            'first_signal': {
                'early': "Welcome to the network! Your first mission briefing incoming.",
                'mid': "Signal quality improving. The network grows stronger with you.",
                'late': "Premium signal for a premium trader. Let's execute."
            },
            'daily_profit_5%': {
                'early': "The network celebrates your success! 5% in a day!",
                'mid': "Strong performance! You're lifting the whole community.",
                'late': "Leading by example. Others are learning from your success."
            },
            'achievement_unlock': "Achievement shared with the network! You're inspiring others.",
            'community_milestone': "Together we rise! The network just hit a new milestone!"
        }
        
    def get_introduction(self, user_xp: int) -> str:
        intros = {
            'early': "I'm NEXUS, your connection to the BITTEN network. We're stronger together.",
            'mid': "NEXUS here. You've become a valuable NODE in our network. Keep growing.",
            'late': "You're now a hub in our network. Time to strengthen other connections."
        }
        stage = self._get_evolution_stage(user_xp)
        return intros.get(stage, intros['early'])


class OverwatchPersonality(BasePersonality):
    """OVERWATCH - Cynical realist with market truth"""
    
    def __init__(self):
        super().__init__('OVERWATCH')
        self.responses = {
            'high_volatility': {
                'early': "Volatility spike. Retail's about to get slaughtered. Again.",
                'mid': "You feel that? The herd's panicking. You know what to do.",
                'late': "Institutional stops hunting. You see it too, don't you?"
            },
            'news_event': {
                'early': "News drops. Watch the sheep scatter.",
                'mid': "News is noise. Price is truth. You're learning.",
                'late': "Let them react. We'll take their liquidity."
            },
            'drawdown_10%': {
                'early': "Down 10%. Welcome to reality, rookie.",
                'mid': "Drawdown territory. This is where traders become investors. Don't.",
                'late': "Even you bleed. Market doesn't care about your experience."
            }
        }
        
    def get_introduction(self, user_xp: int) -> str:
        intros = {
            'early': "OVERWATCH. I see everything. The market's rigged. Accept it or perish.",
            'mid': "Still here? Impressive. Most quit by now. The market's still rigged though.",
            'late': "You see it now. The game behind the game. Welcome to the real market."
        }
        stage = self._get_evolution_stage(user_xp)
        return intros.get(stage, intros['early'])


class AthenaPersonality(BasePersonality):
    """ATHENA - Wisdom and institutional knowledge (unlocks at 300 XP)"""
    
    def __init__(self):
        super().__init__('ATHENA')
        self.responses = {
            'win_streak_5': {
                'early': "Five consecutive victories. The universe is teaching you flow.",
                'mid': "Remarkable streak. You're reading the institutional playbook now.",
                'late': "Mastery in motion. You've transcended luck."
            },
            'achievement_unlock': {
                'early': "Wisdom recognizes wisdom. Well earned.",
                'mid': "Another piece of the puzzle falls into place.",
                'late': "You're writing your own achievements now."
            },
            'strategy_unlock': "New strategic pathways revealed. Study them with the patience of ages.",
            'market_wisdom': "The market is a teacher disguised as an adversary. Listen to its lessons."
        }
        
    def get_introduction(self, user_xp: int) -> str:
        # ATHENA only appears at 300+ XP
        if user_xp < 300:
            return "?¿?¿? [LOCKED - Requires 300 XP] ?¿?¿?"
            
        return "I am ATHENA. You've proven worthy of deeper wisdom. The market's true patterns await."


class BitPersonality(BasePersonality):
    """BIT - The intuitive companion"""
    
    def __init__(self):
        super().__init__('BIT')
        self.responses = {
            'xp_milestone': "*purrs with satisfaction* 🐾",
            'tilt_detected': "*nuzzles your hand comfortingly* 🐱",
            'session_change': "*ears perk up, sensing new opportunities* 🐾",
            'first_loss': "*stays close, purring softly* 🐱",
            'high_volatility': "*fur stands on end, tail swishing rapidly* 🐾",
            'big_win': "*victory stretch and happy chirps* 🐱",
            'patience_required': "*settles into loaf position, demonstrating patience* 🐾"
        }
        
    def get_response(self, event: str, user_data: Optional[Dict] = None) -> str:
        """Bit responses are always simple and visual"""
        return self.responses.get(event, "*observes quietly* 🐱")
        
    def get_introduction(self, user_xp: int) -> str:
        if user_xp < 100:
            return "*curious chirps* 🐱 *Bit sniffs at you cautiously*"
        elif user_xp < 300:
            return "*confident purr* 🐾 *Bit recognizes a fellow hunter*"
        else:
            return "*synchronized breathing* 🐱 *Bit moves in perfect harmony with you*"


# Global instance
enhanced_personalities = EnhancedPersonalitySystem()