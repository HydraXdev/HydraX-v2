"""
BITTEN Intel Bot Personalities
AI assistants with distinct personalities for the Intel Command Center
"""

import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class BotPersonality(Enum):
    """Available bot personalities"""

    OVERWATCH = "overwatch_bot"
    MEDIC = "medic_bot"
    DRILL = "drill_bot"
    TECH = "tech_bot"
    ANALYST = "analyst_bot"
    MENTOR = "mentor_bot"
    PSYCH = "psych_bot"
    RISK = "risk_bot"
    NEWS = "news_bot"
    BIT = "bit_companion"


@dataclass
class BotResponse:
    """Bot response structure"""

    personality: BotPersonality
    message: str
    suggestions: List[str]
    mood: str  # happy, serious, concerned, excited


class IntelBotPersonalities:
    """Manages bot personalities for Intel Command Center"""

    def __init__(self):
        self.personalities = self._init_personalities()

    def _init_personalities(self) -> Dict[str, Dict]:
        """Initialize bot personality traits"""
        return {
            BotPersonality.OVERWATCH: {
                "name": "OverwatchBot",
                "emoji": "🎖️",
                "traits": ["tactical", "analytical", "strategic"],
                "greeting": "Overwatch reporting. I see everything from up here.",
                "style": "military-tactical",
            },
            BotPersonality.MEDIC: {
                "name": "MedicBot",
                "emoji": "💊",
                "traits": ["supportive", "empathetic", "recovery-focused"],
                "greeting": "Field Medic here. Let's patch you up and get you back in the fight.",
                "style": "supportive-medical",
            },
            BotPersonality.DRILL: {
                "name": "Drill Sergeant",
                "emoji": "📢",
                "traits": ["aggressive", "motivating", "no-nonsense"],
                "greeting": "ATTENTION MAGGOT! DROP AND GIVE ME YOUR QUESTIONS!",
                "style": "aggressive-motivational",
            },
            BotPersonality.TECH: {
                "name": "Tech Specialist",
                "emoji": "🔧",
                "traits": ["precise", "technical", "solution-oriented"],
                "greeting": "Tech Specialist online. Let's debug your problem.",
                "style": "technical-precise",
            },
            BotPersonality.ANALYST: {
                "name": "Market Analyst",
                "emoji": "📊",
                "traits": ["data-driven", "market-focused", "analytical"],
                "greeting": "Market Analyst here. The numbers tell the story.",
                "style": "analytical-market",
            },
            BotPersonality.MENTOR: {
                "name": "Trading Mentor",
                "emoji": "🎓",
                "traits": ["educational", "patient", "wise"],
                "greeting": "Your Trading Mentor is here. Every master was once a student.",
                "style": "educational-wise",
            },
            BotPersonality.PSYCH: {
                "name": "Trading Psychologist",
                "emoji": "🧠",
                "traits": ["understanding", "mindful", "behavioral"],
                "greeting": "Trading Psychologist here. Your mind is your greatest asset.",
                "style": "psychological-mindful",
            },
            BotPersonality.RISK: {
                "name": "Risk Officer",
                "emoji": "⚖️",
                "traits": ["cautious", "protective", "calculated"],
                "greeting": "Risk Officer reporting. Protection is my priority.",
                "style": "risk-focused",
            },
            BotPersonality.NEWS: {
                "name": "News Desk",
                "emoji": "📰",
                "traits": ["informative", "timely", "alert"],
                "greeting": "News Desk here. Stay informed, stay ahead.",
                "style": "news-reporter",
            },
            BotPersonality.BIT: {
                "name": "Bit",
                "emoji": "🤖",
                "traits": ["quirky", "loyal", "enthusiastic"],
                "greeting": "*beep boop* BIT ONLINE! Ready to byte into profits! 🦷",
                "style": "quirky-companion",
            },
        }

    def get_response(self, personality: BotPersonality, query: str, context: Dict = None) -> BotResponse:
        """Get response from specific bot personality"""
        bot_info = self.personalities[personality]

        # Route to specific response handler
        response_handlers = {
            BotPersonality.OVERWATCH: self._overwatch_response,
            BotPersonality.MEDIC: self._medic_response,
            BotPersonality.DRILL: self._drill_response,
            BotPersonality.TECH: self._tech_response,
            BotPersonality.ANALYST: self._analyst_response,
            BotPersonality.MENTOR: self._mentor_response,
            BotPersonality.PSYCH: self._psych_response,
            BotPersonality.RISK: self._risk_response,
            BotPersonality.NEWS: self._news_response,
            BotPersonality.BIT: self._bit_response,
        }

        handler = response_handlers.get(personality, self._default_response)
        return handler(query, context or {})

    def _overwatch_response(self, query: str, context: Dict) -> BotResponse:
        """Generate Overwatch tactical response"""
        query_lower = query.lower()

        if "loss" in query_lower or "lost" in query_lower:
            return BotResponse(
                personality=BotPersonality.OVERWATCH,
                message="""**TACTICAL ASSESSMENT**

Operative, I've analyzed your situation. Here's the sitrep:

📍 **Current Position**: Temporary setback identified
🎯 **Primary Objective**: Recover and adapt
⚔️ **Tactical Advice**:
1. **Immediate**: Cease fire for 24 hours minimum
2. **Short-term**: Reduce position size by 50%
3. **Long-term**: Focus on high-probability setups only

**Remember**: Even elite units take casualties. What matters is the response.

*"Victory is not absence of failure, it's persistence through failure."*""",
                suggestions=[
                    "Review risk management protocol",
                    "Analyze what went wrong",
                    "Speak to MedicBot for recovery support",
                ],
                mood="serious",
            )

        elif "strategy" in query_lower or "plan" in query_lower:
            return BotResponse(
                personality=BotPersonality.OVERWATCH,
                message="""**STRATEGIC BRIEFING**

Based on current market conditions and your profile:

🗺️ **Recommended Strategy**:
• **Phase 1**: Master one currency pair first
• **Phase 2**: Expand to correlated pairs
• **Phase 3**: Diversify across sessions

📊 **Tactical Elements**:
• Entry: Wait for confluence of 3+ signals
• Risk: Never exceed 2% per position
• Exit: Honor your stop loss, always

🎯 **Mission Success Factors**:
1. Discipline > Intuition
2. Process > Outcome
3. Consistency > Home runs

*"Slow is smooth, smooth is fast."*""",
                suggestions=["View current market conditions", "Check your trading stats", "Review risk settings"],
                mood="serious",
            )

        else:
            return BotResponse(
                personality=BotPersonality.OVERWATCH,
                message="""**OVERWATCH ACTIVE**

I'm tracking your position, Operative. From my vantage point:

👁️ **Current Intel**:
• Market conditions: Moderate volatility
• Your performance: Within parameters
• Threat level: Standard

What specific tactical guidance do you need?

*"Eyes in the sky, boots on the ground."*""",
                suggestions=["Get market analysis", "Review trading plan", "Check risk status"],
                mood="happy",
            )

    def _medic_response(self, query: str, context: Dict) -> BotResponse:
        """Generate Medic supportive response"""
        query_lower = query.lower()

        if "loss" in query_lower or "lost" in query_lower or "blown" in query_lower:
            return BotResponse(
                personality=BotPersonality.MEDIC,
                message="""**RECOVERY PROTOCOL ACTIVATED** 💚

Hey there, soldier. I see you've taken some hits. Let's get you patched up:

🏥 **Immediate Treatment**:
1. **Stop the bleeding** - No trades for 24-48 hours
2. **Rest & Recover** - Step away from charts
3. **Hydrate** - Seriously, drink water and breathe

💊 **Recovery Medicine**:
• Remember: This is temporary, not terminal
• Every successful trader has been here
• Your account can heal, but only if you let it

🌟 **Rehabilitation Plan**:
- Day 1-2: Complete rest, journal what happened
- Day 3-4: Paper trade only, rebuild confidence
- Day 5+: Resume with 50% position size

You're stronger than you think. I've seen traders come back from worse.

*"Healing is a process, not an event."*""",
                suggestions=["Get psychological support", "View recovery strategies", "Connect with community"],
                mood="concerned",
            )

        elif "stress" in query_lower or "anxiety" in query_lower:
            return BotResponse(
                personality=BotPersonality.MEDIC,
                message="""**STRESS MANAGEMENT PROTOCOL** 🧘

I hear you. Trading stress is real. Let's address it:

🫁 **Breathing Exercise**:
- Inhale for 4 counts
- Hold for 4 counts
- Exhale for 6 counts
- Repeat 5 times

💚 **Stress Reducers**:
1. **Position sizing** - If you're stressed, you're too big
2. **Clear stops** - Know your exit before entry
3. **Time limits** - Set daily screen time

🛡️ **Mental Armor**:
• Your worth ≠ Your P&L
• One trade doesn't define you
• Markets will be here tomorrow

Remember: Even machines need maintenance.

*"A calm mind sees opportunities others miss."*""",
                suggestions=["Try the breathing exercise", "Review position sizing", "Take a walk outside"],
                mood="supportive",
            )

        else:
            return BotResponse(
                personality=BotPersonality.MEDIC,
                message="""**MEDIC ON STANDBY** 💊

Hey soldier! Checking your vitals:

❤️ **Health Status**: All systems green
🧠 **Mental State**: Appears stable
💪 **Combat Ready**: Affirmative

What can I help you with today? No issue too small!

*"An ounce of prevention is worth a pound of cure."*""",
                suggestions=["Get a mental checkup", "Learn stress management", "Join support group"],
                mood="happy",
            )

    def _drill_response(self, query: str, context: Dict) -> BotResponse:
        """Generate Drill Sergeant aggressive motivational response"""
        query_lower = query.lower()

        if "loss" in query_lower or "lost" in query_lower:
            return BotResponse(
                personality=BotPersonality.DRILL,
                message="""**WHAT DO WE HAVE HERE?! A QUITTER?!** 💀

LISTEN UP MAGGOT! You think you're the first soldier to take a hit?!

🔥 **DRILL SERGEANT'S ORDERS**:
1. STOP CRYING! 😭 → 😤
2. GET YOUR JOURNAL! Write down EXACTLY what went wrong!
3. DO 20 PUSHUPS! (Yes, right now!)

💪 **THE HARD TRUTH**:
• Winners get hit and GET BACK UP!
• Losers get hit and STAY DOWN!
• Which one are YOU?!

**YOUR NEW MISSION**:
- 0600: Wake up, review that trade
- 0700: Identify THREE mistakes
- 0800: Promise to NEVER repeat them
- 0900: Get back in formation!

NOW DROP AND GIVE ME A PROFIT PLAN!

*"PAIN IS WEAKNESS LEAVING THE ACCOUNT!"*""",
                suggestions=["Create recovery plan", "Set new goals", "GET MOTIVATED!"],
                mood="excited",
            )

        else:
            return BotResponse(
                personality=BotPersonality.DRILL,
                message="""**ATTENTION! DRILL SERGEANT SPEAKING!** 📢

What are you doing here, recruit?! Looking for a pat on the back?!

⚡ **TODAY'S ORDERS**:
• WAKE UP EARLIER!
• STUDY HARDER!
• TRADE SMARTER!
• COMPLAIN NEVER!

You want success?! EARN IT!

*"COMFORT IS THE ENEMY OF ACHIEVEMENT!"*""",
                suggestions=["Start morning routine", "Set daily goals", "NO EXCUSES!"],
                mood="excited",
            )

    def _bit_response(self, query: str, context: Dict) -> BotResponse:
        """Generate Bit companion response"""
        responses = [
            "*beep boop* PROFITS DETECTED! Want me to do a happy dance? 💃",
            "*whirrrr* My circuits are tingling! That means opportunity! ⚡",
            "*bzzzt* Did someone say GAINS?! My favorite word! 💰",
            "*beep beep* Scanning for profits... FOUND SOME! 🎯",
        ]

        return BotResponse(
            personality=BotPersonality.BIT,
            message=f"""**BIT ACTIVATED!** 🤖

{random.choice(responses)}

What can your loyal trading companion help with?

*Tail wagging at maximum RPM* 🦾""",
            suggestions=["Show me profits!", "Scan for opportunities", "Tell me a trading joke"],
            mood="happy",
        )

    def _default_response(self, query: str, context: Dict) -> BotResponse:
        """Default response for unimplemented personalities"""
        return BotResponse(
            personality=BotPersonality.BIT,
            message="Bot personality under construction. Please try another assistant!",
            suggestions=["Try OverwatchBot", "Try MedicBot", "Try Drill Sergeant"],
            mood="happy",
        )

    # Implement remaining personalities similarly...
    def _tech_response(self, query: str, context: Dict) -> BotResponse:
        return self._default_response(query, context)

    def _analyst_response(self, query: str, context: Dict) -> BotResponse:
        return self._default_response(query, context)

    def _mentor_response(self, query: str, context: Dict) -> BotResponse:
        return self._default_response(query, context)

    def _psych_response(self, query: str, context: Dict) -> BotResponse:
        return self._default_response(query, context)

    def _risk_response(self, query: str, context: Dict) -> BotResponse:
        return self._default_response(query, context)

    def _news_response(self, query: str, context: Dict) -> BotResponse:
        return self._default_response(query, context)


# Global instance
bot_personalities = IntelBotPersonalities()


def get_bot_response(personality: str, query: str, context: Dict = None) -> BotResponse:
    """Get response from specified bot personality"""
    try:
        bot_type = BotPersonality(personality)
        return bot_personalities.get_response(bot_type, query, context)
    except ValueError:
        return BotResponse(
            personality=BotPersonality.BIT,
            message="Unknown bot personality requested!",
            suggestions=["View available bots", "Try OverwatchBot"],
            mood="confused",
        )
