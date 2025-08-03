#!/usr/bin/env python3
"""
🎬 BITTEN Cinematic Onboarding System
Implements the immersive onboarding experience with Norman's story and Bit integration
"""

import random
from typing import Dict, Optional, Tuple, List
from datetime import datetime

class CinematicOnboarding:
    """Manages the cinematic onboarding experience for new users"""
    
    def __init__(self):
        self.onboarding_stages = {
            "welcome": self._get_welcome_sequence,
            "bit_intro": self._get_bit_introduction,
            "mission_briefing": self._get_mission_briefing,
            "first_trade_tutorial": self._get_first_trade_tutorial,
            "risk_visualization": self._get_risk_visualization,
            "execution_ceremony": self._get_execution_ceremony
        }
        
        # User progress tracking
        self.user_progress = {}  # user_id: current_stage
        
    def get_onboarding_message(self, user_id: str, stage: str = "welcome", user_data: Optional[Dict] = None) -> Tuple[str, Optional[Dict]]:
        """Get the appropriate onboarding message for the user's current stage"""
        if stage not in self.onboarding_stages:
            stage = "welcome"
            
        message_func = self.onboarding_stages[stage]
        return message_func(user_id, user_data)
    
    def _get_welcome_sequence(self, user_id: str, user_data: Optional[Dict] = None) -> Tuple[str, Optional[Dict]]:
        """First contact - Norman's personal welcome"""
        message = """🌙 *The screen fades in...*

*A gentle chirp echoes in the darkness*

**NORMAN** (voice): "Hey there. Name's Norman. From Clarksdale, Mississippi. 
That chirp you heard? That's Bit. He's... well, he's why you're here."

🐾

**NORMAN**: "See, Bit and I discovered something. The market? It bites. 
Hard. Took everything from my dad. Almost took me too."

*Bit purrs softly*

**NORMAN**: "But we learned to bite back. And now... we're gonna teach you."

Ready to begin your journey?"""
        
        # Track user progress
        self.user_progress[user_id] = "welcome"
        
        # Return message and inline keyboard options
        keyboard = {
            "inline_keyboard": [[
                {"text": "🐾 Meet Bit", "callback_data": "onboard_bit_intro"},
                {"text": "📖 Tell me more", "callback_data": "onboard_norman_story"}
            ]]
        }
        
        return message, keyboard
    
    def _get_bit_introduction(self, user_id: str, user_data: Optional[Dict] = None) -> Tuple[str, Optional[Dict]]:
        """Bit's personal introduction"""
        message = """🐱 *Bit's amber eyes glow in the darkness*

**BIT PERSONALITY**: *chirps excitedly* 

"This here's Bit - Born In Truck, if you're wondering. Found him 
in Dad's work truck during the worst storm Mississippi ever saw."

*Bit's presence becomes more tangible*

"He's got this way of knowing things. When to wait. When to strike. 
When to run. Trust him. He's saved me more times than I can count."

🐾 *Bit nuzzles your hand virtually*

**NORMAN**: "Bit sees patterns I miss. Feels the market's mood before the charts show it. 
When his ears go back, I listen. When he purrs at a setup, I pay attention."

"You ready to meet your squad?"

*Bit's tail swishes expectantly*"""
        
        self.user_progress[user_id] = "bit_intro"
        
        keyboard = {
            "inline_keyboard": [[
                {"text": "🎖️ Meet the Squad", "callback_data": "onboard_mission_briefing"},
                {"text": "🐾 Pet Bit", "callback_data": "onboard_pet_bit"}
            ]]
        }
        
        return message, keyboard
    
    def _get_mission_briefing(self, user_id: str, user_data: Optional[Dict] = None) -> Tuple[str, Optional[Dict]]:
        """Introduction to the military squad (personalities)"""
        message = """🎯 **DRILL PERSONALITY**: "ALRIGHT RECRUIT! LISTEN UP!"

"You've been BITTEN. That means you're one of us now. 
A NODE in our network. A soldier in our war against the rigged system."

"Your first mission is simple: Learn. Survive. Grow."

"Norman built this system after the market nearly destroyed his family. 
Every feature, every voice, every protection - it's all here because 
someone bled for that lesson."

🐾 *Bit sits at attention, watching intently*

**DRILL**: "You'll meet the whole squad:
• **ME** - Your discipline. Your father's voice when emotion tries to control you.
• **DOC** - Your mother's protection. She'll patch you up when you fall.
• **NEXUS** - Your community. We rise together or not at all.
• **OVERWATCH** - The cynic. He'll show you what the market really is.

And later, if you prove worthy...
• **ATHENA** - The wisdom. She appears only to those who've earned it."

"ARE YOU READY TO BITE BACK?"

*Bit's claws extend slightly, ready for action*"""
        
        self.user_progress[user_id] = "mission_briefing"
        
        keyboard = {
            "inline_keyboard": [[
                {"text": "✅ YES, SIR!", "callback_data": "onboard_first_trade"},
                {"text": "❓ Tell me more", "callback_data": "onboard_more_info"}
            ]]
        }
        
        return message, keyboard
    
    def _get_first_trade_tutorial(self, user_id: str, user_data: Optional[Dict] = None) -> Tuple[str, Optional[Dict]]:
        """Interactive first trade tutorial"""
        # Get a sample signal for demonstration
        sample_signal = {
            "symbol": "EURUSD",
            "direction": "BUY",
            "confidence": 82,
            "risk_reward": 2.0
        }
        
        message = f"""📊 **Your First Mission Briefing**

**NEXUS**: "Welcome to your first mission briefing, soldier! 
I'm NEXUS - think of me as your squad leader."

"See that signal coming in? That's not just numbers. 
That's opportunity. Let me break it down..."

🎯 **Mission: COTTON FIELD**
📊 {sample_signal['symbol']} | {sample_signal['direction']} | {sample_signal['confidence']}% confidence

**Signal Analysis:**
• 🐱 **Bit's Reaction**: *ears perk up* - High confidence signal
• 📈 **Direction**: {sample_signal['direction']} - Bit stretches, ready to pounce
• 💯 **Confidence**: {sample_signal['confidence']}% - Bit purrs approvingly
• 📏 **Risk:Reward**: 1:{sample_signal['risk_reward']} - Balanced opportunity

**NEXUS**: "In trading, we risk a little to gain more. That 1:2 ratio? 
It means we're risking $1 to potentially make $2. Smart warfare."

🐾 *Bit demonstrates hunting patience*

"Your Grandmama would say: 'Child, never bet the farm on one crop.'"

Ready to learn about risk?"""
        
        self.user_progress[user_id] = "first_trade_tutorial"
        
        keyboard = {
            "inline_keyboard": [[
                {"text": "📊 Show me risk", "callback_data": "onboard_risk_visual"},
                {"text": "🎯 Let's trade!", "callback_data": "onboard_execute"}
            ]]
        }
        
        return message, keyboard
    
    def _get_risk_visualization(self, user_id: str, user_data: Optional[Dict] = None) -> Tuple[str, Optional[Dict]]:
        """Risk management visualization"""
        message = """🛡️ **Risk Management - The Foundation**

**DOC**: "Hold up there, soldier. Before you fire, let me show you 
what we're really risking here."

🏚️ *Visual: Your account as a Mississippi farmhouse*

"This is your capital. Your family's future. Every trade risks 
a piece of this farm."

**The 2% Rule:**
```
Your Farm: $1,000 (example)
One Field (2%): $20
Maximum Risk: Never more than one field
```

"We only risk 2% - one small field. Even if the storm comes, 
the farm survives. That's how we outlast the market."

🐾 *Bit guards the farmhouse protectively*

**DOC**: "Your Mama didn't sacrifice for you to gamble. We trade with 
discipline. Always."

"Norman learned this the hard way. Lost everything once. 
Bit stayed by his side through it all. Now we protect what matters."

**Mississippi Wisdom**: "Plant in the spring, harvest in the fall. 
But always keep seed corn for next year."

Ready to execute your first trade with proper protection?"""
        
        self.user_progress[user_id] = "risk_visualization"
        
        keyboard = {
            "inline_keyboard": [[
                {"text": "🔥 Execute with discipline", "callback_data": "onboard_ceremony"},
                {"text": "📖 Learn more", "callback_data": "onboard_risk_details"}
            ]]
        }
        
        return message, keyboard
    
    def _get_execution_ceremony(self, user_id: str, user_data: Optional[Dict] = None) -> Tuple[str, Optional[Dict]]:
        """First trade execution ceremony"""
        message = """⚡ **THE MOMENT OF TRUTH**

*Time slows down*

🐱 *Bit's intense stare at the screen*

**NORMAN**: "This is it. Your first shot. Remember - the market's 
gonna try to bite. But you've got Bit. You've got us."

*The air crackles with anticipation*

**Your First Trade:**
• 📊 EURUSD - Following institutional flow
• 🎯 BUY - Bit's instincts align
• 🛡️ 2% Risk - Protecting the farm
• 📈 Target: 2x your risk

**DRILL**: "STEADY YOUR BREATHING, SOLDIER!"

**DOC**: "Remember, win or lose, we're here."

**NEXUS**: "The network's watching. We believe in you."

🐾 *Bit places a paw on your hand*

**NORMAN**: "Every legend starts with one trade. Make it count."

When you're ready, type `/fire` to execute your destiny..."""
        
        self.user_progress[user_id] = "execution_ceremony"
        
        keyboard = {
            "inline_keyboard": [[
                {"text": "🔥 I'm ready - BITE BACK!", "callback_data": "onboard_complete"}
            ]]
        }
        
        return message, keyboard
    
    def handle_first_trade_result(self, user_id: str, trade_result: Dict) -> str:
        """Generate response based on first trade outcome"""
        if trade_result.get("success", False):
            return self._first_win_response(user_id, trade_result)
        else:
            return self._first_loss_response(user_id, trade_result)
    
    def _first_win_response(self, user_id: str, trade_result: Dict) -> str:
        """Response for first winning trade"""
        profit = trade_result.get("profit", 0)
        
        message = f"""🎯 **FIRST BLOOD DRAWN!**

**DRILL**: "OUTSTANDING! FIRST KILL CONFIRMED!"

*Bit does his victory stretch - the legendary full-body arch*

**NORMAN**: "See that? You just took your first bite outta the market. 
+${profit:.2f}. Feels good, don't it? But don't get cocky..."

🏆 **Achievement Unlocked: FIRST BITE**
⚡ **+50 XP** - You're officially a trader

*Bit purrs loudly, rubbing against your leg*

**DOC**: "Well done, but remember - one victory doesn't win the war."

**NEXUS**: "The network celebrates your first blood! 🎉"

**ATHENA** (preview whisper): "A wise warrior celebrates briefly, 
then prepares for the next battle..."

🐾 *Bit settles into a satisfied loaf position*

**NORMAN**: "You've tasted victory. The market will try harder next time. 
Stay disciplined. Trust Bit. Trust the system."

"Welcome to the family, soldier. You're one of us now."

Type `/status` to see your progress or wait for the next signal..."""
        
        return message
    
    def _first_loss_response(self, user_id: str, trade_result: Dict) -> str:
        """Response for first losing trade"""
        loss = abs(trade_result.get("loss", 0))
        
        message = f"""💔 **First Scar Earned**

*Bit nuzzles your hand comfortingly*

**DOC**: "Easy there, soldier. That sting you're feeling? That's the 
market's bite. We've all felt it. -${loss:.2f} this time."

**NORMAN**: "Lost my first trade too. And my second. Hell, lost my 
whole account once. But Bit stayed with me. And I learned."

🐾 *Bit demonstrates his 'shake it off' move*

"Every scar teaches. This one just taught you the market's real. 
Now let's learn to bite back smarter."

**DRILL**: "PAIN IS THE BEST TEACHER, RECRUIT!"

**Mississippi Wisdom**: "The river takes before it gives. But those who 
understand its rhythm always eat."

📚 **Lesson Learned** 
⚡ **+25 XP** - Even losses make you stronger

*Bit settles beside you, purring softly*

**DOC**: "You lost 2% - one small field. The farm still stands. 
That's why we have rules. That's why we protect."

**NORMAN**: "Ready to get back up? The market's still out there. 
And now you know it bites. Time to bite back harder."

Type `/tactical` to adjust your strategy or wait for better opportunities..."""
        
        return message
    
    def get_random_bit_interaction(self) -> str:
        """Get a random Bit interaction for ambient presence"""
        interactions = [
            "🐾 *Bit watches the charts intently*",
            "🐱 *Bit's tail swishes, sensing opportunity*",
            "🐾 *Bit stretches, maintaining alertness*",
            "🐱 *Bit's ears rotate, tracking market sounds*",
            "🐾 *Bit purrs softly at the setup*",
            "🐱 *Bit's whiskers twitch with anticipation*",
            "🐾 *Bit settles into hunting position*",
            "🐱 *Bit chirps his signature glitch sound*",
            "🐾 *Bit's eyes narrow, focused on price action*",
            "🐱 *Bit kneads the trading desk thoughtfully*"
        ]
        return random.choice(interactions)
    
    def get_mississippi_wisdom(self) -> str:
        """Get random Mississippi/family wisdom"""
        wisdom = [
            "🌾 Grandmama says: 'Patience is worth more than gold, child.'",
            "🏚️ 'Never chase what's running away' - Dad's truck wisdom",
            "🌊 'The river rises and falls. Build on high ground.' - Delta wisdom",
            "👵🏾 'Count your pennies like they're dollars' - Grandmama",
            "🌾 'Plant in season, harvest in season' - Mississippi timing",
            "🏚️ 'Storm's coming means opportunity after' - Delta truth",
            "💭 'Your Mama worked three jobs for this' - Never forget",
            "🌊 'Still water runs deep, child' - Market wisdom",
            "🌾 'One bad season don't ruin a farmer' - Resilience",
            "👵🏾 'The Lord helps those who help themselves' - Action wisdom"
        ]
        return random.choice(wisdom)

# Global instance
cinematic_onboarding = CinematicOnboarding()