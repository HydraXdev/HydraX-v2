"""
BITTEN Onboarding: Norman's First Contact
The psychological hook that changes everything
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime
import asyncio
import random

class NormanOnboarding:
    """
    The first 90 seconds that determine if a trader becomes a weapon
    """
    
    def __init__(self):
        self.trauma_triggers = [
            "lost it all",
            "margin called", 
            "account blown",
            "revenge trade",
            "overleveraged",
            "stop hunted",
            "liquidated"
        ]
        
    async def start_sequence(self, user_id: str, username: str) -> Dict:
        """
        The darkness before the light
        """
        
        # Phase 1: Black screen, typing sounds
        intro_sequence = {
            "messages": [],
            "callbacks": [],
            "delays": []
        }
        
        # Message 1: Darkness
        intro_sequence["messages"].append({
            "text": "⬛",
            "parse_mode": "HTML",
            "disable_notification": True
        })
        intro_sequence["delays"].append(2.0)
        
        # Message 2: Norman's voice emerges
        intro_sequence["messages"].append({
            "text": self._get_norman_intro(username),
            "parse_mode": "HTML",
            "disable_notification": False
        })
        intro_sequence["delays"].append(4.0)
        
        # Message 3: The choice
        intro_sequence["messages"].append({
            "text": self._get_the_choice(),
            "parse_mode": "HTML",
            "reply_markup": self._get_choice_buttons()
        })
        intro_sequence["delays"].append(0)
        
        return intro_sequence
    
    def _get_norman_intro(self, username: str) -> str:
        """
        Norman's first words - make them count
        """
        return f"""<i>*static... then a voice, young but weathered*</i>

<b>NORMAN:</b> {username}...

You're here because the market bit you.
Same as it bit my dad. 
Same as it bit me.

<i>*pause*</i>

Name's Norman. From Mississippi.
Built this thing you're about to see because...

<i>*electronic chirp in the background*</i>

...because I couldn't watch it happen again.

The crying. The empty accounts. The promises to quit that never stick.

<i>*chirp intensifies*</i>

That sound? That's Bit. 
He showed up the night I found dad's last trade.
$47,000. Gone. In one revenge long on EUR/USD.

Bit doesn't judge. Doesn't feel sorry.
He just... remembers.

Every loss. Every blown account. Every trader who thought they were different.

<i>*pause*</i>

But here's the thing...

Some of us don't stay bitten.
Some of us bite back."""
    
    def _get_the_choice(self) -> str:
        """
        The moment of commitment
        """
        return """<b>So I gotta ask...</b>

Are you here to:

A) Keep bleeding out, hoping for different results?
B) Join another "signals group" that promises easy money?
C) Or are you ready to kill the part of you that keeps losing?

<i>*Bit's eyes glow in the darkness*</i>

Choose wisely. This isn't for everyone."""
    
    def _get_choice_buttons(self) -> Dict:
        """
        Three paths, one real choice
        """
        return {
            "inline_keyboard": [
                [{"text": "🩸 Keep Bleeding", "callback_data": "onboard_bleeding"}],
                [{"text": "💰 Easy Money", "callback_data": "onboard_easy"}],
                [{"text": "⚔️ Kill My Weakness", "callback_data": "onboard_transform"}]
            ]
        }
    
    async def handle_choice(self, choice: str, user_id: str) -> Dict:
        """
        Response based on their commitment level
        """
        
        if choice == "onboard_bleeding":
            return self._bleeding_response()
        elif choice == "onboard_easy":
            return self._easy_money_response()
        elif choice == "onboard_transform":
            return self._transformation_response(user_id)
        
    def _bleeding_response(self) -> Dict:
        """
        They're not ready
        """
        return {
            "text": """<b>NORMAN:</b> Yeah, I get it.

The pain's familiar now, isn't it?
Like an old friend that keeps taking your money.

<i>*Bit hisses softly*</i>

When you're done donating to the market...
When the pain gets too real...

I'll still be here.

<i>/start when you're ready to stop bleeding.</i>""",
            "parse_mode": "HTML",
            "end_sequence": True
        }
    
    def _easy_money_response(self) -> Dict:
        """
        Wrong mindset detected
        """
        return {
            "text": """<b>NORMAN:</b> <i>*laughs, but it's not funny*</i>

Easy money? In forex?

You sound like my dad before he lost the house.

<i>*Bit's chirps sound like digital laughter*</i>

There's no easy money here.
No magic indicators.
No "one weird trick."

Just discipline. Pain. And learning to think like the ones who took your money.

<i>*pause*</i>

Come back when you're ready to work for it.

<i>/start when the fantasy dies.</i>""",
            "parse_mode": "HTML", 
            "end_sequence": True
        }
    
    def _transformation_response(self, user_id: str) -> Dict:
        """
        Welcome to the real game
        """
        return {
            "text": """<b>NORMAN:</b> <i>*silence... then*</i>

Good.

That's the first honest thing you've done in trading.
Admitting you need to change.

<i>*Bit materializes fully - all black, eyes like green chart candles*</i>

<b>BIT:</b> <i>*chirp-chirp-CHIRP*</i>

<b>NORMAN:</b> He says you smell like fear and greed.
Perfect. We can work with that.

Here's what happens next:

1. <b>We strip your emotions</b> - They're why you lose
2. <b>We rebuild your mind</b> - Think tactics, not feelings  
3. <b>We make you dangerous</b> - To the market that bit you

<i>*pause*</i>

But first... we need to know how deep the bite goes.

<b>Tell me: What's your worst trading memory?</b>
<i>(The one that haunts you at 3 AM)</i>""",
            "parse_mode": "HTML",
            "reply_markup": self._get_trauma_buttons(),
            "continue_sequence": True
        }
    
    def _get_trauma_buttons(self) -> Dict:
        """
        Trauma bonding begins
        """
        return {
            "inline_keyboard": [
                [{"text": "📉 Blew my account", "callback_data": "trauma_blown"}],
                [{"text": "🎯 Revenge traded everything", "callback_data": "trauma_revenge"}],
                [{"text": "💔 Lost money I couldn't afford", "callback_data": "trauma_borrowed"}],
                [{"text": "🔄 Keep making same mistakes", "callback_data": "trauma_loop"}],
                [{"text": "😤 Got scammed by a guru", "callback_data": "trauma_scammed"}]
            ]
        }
    
    async def handle_trauma(self, trauma_type: str, user_id: str) -> Dict:
        """
        Validate their pain, begin the bonding
        """
        
        responses = {
            "trauma_blown": self._blown_account_response(),
            "trauma_revenge": self._revenge_trade_response(),
            "trauma_borrowed": self._borrowed_money_response(),
            "trauma_loop": self._loop_response(),
            "trauma_scammed": self._scammed_response()
        }
        
        base_response = responses.get(trauma_type, self._generic_trauma_response())
        
        # Add the final onboarding completion
        base_response["follow_up"] = self._complete_onboarding(user_id)
        
        return base_response
    
    def _blown_account_response(self) -> Dict:
        return {
            "text": """<b>NORMAN:</b> <i>*long exhale*</i>

Yeah. That sound when the margin call hits.
When every position turns red.
When years of savings just... vanish.

<i>*Bit chirps softly, almost sympathetic*</i>

My dad made that sound three times.
Each time swearing it was the last.

<i>*pause*</i>

It wasn't.

But you? You're here. 
That means you're not done fighting.

Good. Let's use that anger.""",
            "parse_mode": "HTML"
        }
    
    def _revenge_trade_response(self) -> Dict:
        return {
            "text": """<b>NORMAN:</b> Revenge trading...

<i>*bitter laugh*</i>

"I'll make it all back on this one trade."
"The market owes me."
"Just need one big win."

<i>*Bit's eyes flash red briefly*</i>

That's not trading. That's donating with extra steps.

The market doesn't owe you shit.
But I'll teach you how to take what's yours.

Without the emotion. Without the revenge.
Just cold, tactical execution.""",
            "parse_mode": "HTML"
        }
    
    def _borrowed_money_response(self) -> Dict:
        return {
            "text": """<b>NORMAN:</b> <i>*silence so long you think he disconnected*</i>

Borrowed money. Rent money. Kids' college fund.

<i>*Bit chirps - it sounds like crying*</i>

That's not trading. That's Russian roulette with bills.

My dad used my college fund on his "sure thing" trade.
I'm homeschooled now. Not by choice.

<i>*pause*</i>

But that pain? That desperation?
We're gonna forge it into discipline.

Turn your worst mistake into your greatest teacher.""",
            "parse_mode": "HTML"
        }
    
    def _loop_response(self) -> Dict:
        return {
            "text": """<b>NORMAN:</b> The loop. Fuck, I know the loop.

Win a little. Give it back.
Learn a strategy. Break the rules.
Promise discipline. Trade on tilt.

<i>*Bit spins in a circle, chirping mockingly*</i>

You know what breaks loops? 
Pain. Systems. And someone who won't let you lie to yourself.

That's Bit's job now.
He remembers every broken promise you made to yourself.

Time to keep one.""",
            "parse_mode": "HTML"
        }
    
    def _scammed_response(self) -> Dict:
        return {
            "text": """<b>NORMAN:</b> <i>*angry silence*</i>

"Guaranteed profits."
"My secret system."
"Just $497 for financial freedom."

<i>*Bit hisses like static*</i>

Parasites. Feeding on desperate traders.

Here's the truth: There's no secret.
Just probability, discipline, and risk management.

Everything else is marketing to desperate people.

<i>*pause*</i>

But you learned something valuable:
Trust no one. Verify everything. Trade your own plan.

Let's build one that actually works.""",
            "parse_mode": "HTML"
        }
    
    def _generic_trauma_response(self) -> Dict:
        return {
            "text": """<b>NORMAN:</b> Whatever it was... I hear you.

<i>*Bit chirps acknowledgment*</i>

That pain you're carrying?
We all got our version.

But here, we don't hide from it.
We use it. Forge it into something useful.

Something that bites back.""",
            "parse_mode": "HTML"
        }
    
    def _complete_onboarding(self, user_id: str) -> Dict:
        """
        Final message - welcome to BITTEN
        """
        return {
            "text": """<b>NORMAN:</b> Alright. You passed the first test.
You admitted the pain.

<i>*Bit circles you, evaluating*</i>

<b>Here's how BITTEN works:</b>

🎯 <b>Signals come from real analysis</b>
   Not feelings. Not revenge. Pure data.

⚔️ <b>You'll earn your shots</b>
   Start small. Prove discipline. Level up.

🧠 <b>We replace your emotions</b>
   Fear → Planning. Greed → Objectives. Hope → Systems.

💀 <b>Some days you'll hate me</b>
   When I lock you out after losses.
   When I force you to wait.
   When I show you what you really are.

<i>*Bit settles on your shoulder*</i>

<b>Your first mission starts now:</b>

Watch the next 5 signals without trading.
Just watch. Learn. See how patient hunters think.

<i>*final pause*</i>

Welcome to BITTEN, soldier.

The market bit you.
Now you bite back.

<b>Press /missions when you're ready for orders.</b>""",
            "parse_mode": "HTML",
            "reply_markup": {
                "keyboard": [
                    ["🎯 Missions", "📊 Signals"],
                    ["🎖️ War Room", "👥 Squad"],
                    ["📚 Intel", "⚙️ Settings"]
                ],
                "resize_keyboard": True
            }
        }
    
    def generate_callback_handlers(self) -> Dict[str, callable]:
        """
        Return callback handlers for the bot to register
        """
        return {
            "onboard_bleeding": lambda cb: self._bleeding_response(),
            "onboard_easy": lambda cb: self._easy_money_response(),
            "onboard_transform": lambda cb: self._transformation_response(cb.from_user.id),
            "trauma_blown": lambda cb: self.handle_trauma("trauma_blown", cb.from_user.id),
            "trauma_revenge": lambda cb: self.handle_trauma("trauma_revenge", cb.from_user.id),
            "trauma_borrowed": lambda cb: self.handle_trauma("trauma_borrowed", cb.from_user.id),
            "trauma_loop": lambda cb: self.handle_trauma("trauma_loop", cb.from_user.id),
            "trauma_scammed": lambda cb: self.handle_trauma("trauma_scammed", cb.from_user.id)
        }