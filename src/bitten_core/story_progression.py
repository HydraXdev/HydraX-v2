#!/usr/bin/env python3
"""
📖 BITTEN Story Progression System
Manages the progressive revelation of Norman's story based on user milestones
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

class StoryProgressionSystem:
    """Manages story unlocks and progression based on user achievements"""
    
    def __init__(self):
        # Story entries mapped to XP milestones
        self.story_entries = {
            10: {
                "title": "The Discovery",
                "content": """📔 **Norman's Journal - Entry #1**

"Found Dad crying in his truck today. Market took everything. 
Again. Bit jumped on my desk, knocked over my mouse. Trading 
chart opened. Looked just like my game..."

"Maybe I can figure this out. Maybe I can help."

🐾 *Bit's paw print appears on the page*""",
                "reward": "Market patterns are just like game patterns"
            },
            
            25: {
                "title": "Grandmama's Wisdom",
                "content": """📔 **Bit's Memory Unlocked**

"Grandmama always said: 'Child, the river's gonna rise and fall. 
Can't stop it. But you can learn its rhythm. Build your house 
on high ground. Plant when it's low. Harvest before the flood.'"

"She was talking about the Delta. But she was also talking about life."

🌊 **New Market Insight**: Session timing matters. London is the morning flood.""",
                "reward": "Session timing knowledge unlocked"
            },
            
            50: {
                "title": "The First Scar",
                "content": """📹 **Video Message from Norman**

"Hey, you hit 50 XP. Means you've been bitten a few times now. 
Hurts, don't it? Let me tell you about my first real loss..."

"Thought I was smart. Bet half my lawn-mowing money on a 'sure thing.' 
EUR/USD. Looked just like a boss fight pattern from my game. 
Market took it all in 3 minutes."

"Bit stayed with me that whole night. Didn't leave my side."

"That's when I learned - the market don't care about your patterns. 
It cares about discipline."

🎁 **Unlocks**: Norman's Notebook Feature - Start documenting your journey""",
                "reward": "Norman's Notebook unlocked"
            },
            
            100: {
                "title": "Bit's Secret",
                "content": """🎬 **Special Animation: Bit's Origin Story**

"Storm was coming. Dad's truck broke down. Heard chirping from 
the engine. Tiny black kitten, covered in oil. Born in that truck. 
Survivor, like us."

"Vet said he had a glitch. Made these weird electronic chirps 
instead of normal meows. I knew he was special."

"First time I showed him a chart, his ears went straight up. 
Started pawing at the screen right before a big move. 
Bit sees what we miss."

🐱 **Bit Companion Upgrade**: Predictive chirps now warn of volatility""",
                "reward": "Bit volatility warnings activated"
            },
            
            120: {
                "title": "Tactical Evolution",
                "content": """🎖️ **FIRST_BLOOD Strategy Unlocked**

**DRILL**: "You've proven yourself, soldier. Time for advanced tactics. 
FIRST_BLOOD is about momentum. Like Mississippi floods - once they 
start, they build power..."

"Norman discovered this watching storm patterns. First drop of rain 
don't mean nothing. But when the drops connect? That's when you 
move to high ground."

"In trading: First signal might be noise. Second confirms direction. 
Third? That's when you strike."

**Strategy Details**: Take escalating positions as confidence builds.
1st: 75% confidence, 2nd: 78%, 3rd: 80%, 4th: 85%

"Strike fast, strike hard, then retreat. Like Bit hunting."

🎯 **Mississippi Magic**: Sometimes the best trades come in floods.""",
                "reward": "FIRST_BLOOD tactical strategy"
            },
            
            200: {
                "title": "Mother's Sacrifice",
                "content": """💔 **Emotional Story Sequence**

**NORMAN**: "Mom worked three jobs so I could have this computer. 
Said I had 'lightning inside.' That's why DOC protects so hard. 
Every dollar we risk, someone sacrificed for it."

"Found her fallen asleep at the kitchen table, still in her 
hospital scrubs. Bills spread everywhere. That's the night I 
swore I'd build something."

"Not just for me. For her. For everyone who's been bitten by 
this rigged system."

"DOC's voice? That's her. Protecting you like she protected me. 
'Don't risk what you can't afford to lose, baby.'"

🛡️ **DOC Personality Evolution**: Now includes Mom's actual phrases

"Every time you hear DOC, remember - someone loves you enough 
to want you trading tomorrow."

**Your capital isn't just money. It's someone's sacrifice.**""",
                "reward": "DOC personality enhanced with personal touch"
            },
            
            300: {
                "title": "ATHENA Awakens",
                "content": """🏛️ **Major Unlock Ceremony**

*Ancient Greek music plays*

**ATHENA**: "Greetings, warrior. You've proven worthy of deeper wisdom. 
I am ATHENA, guardian of strategic thought and institutional knowledge."

"The market is not your enemy. It's a teacher. Let me show you 
what the institutions see..."

"Norman reached this level after 1,000 trades. He realized the 
market has a hierarchy. Retail traders at the bottom. Institutions 
at the top. But with knowledge, you can follow their footprints."

"Like tracking big game through the Delta. You don't need to BE 
the elephant. You just need to know where it's going."

🏛️ **Wisdom Unlocked**: 
- Institutional order flow patterns
- Liquidity pool identification
- Smart money accumulation zones

"Remember: In Mississippi, the smartest farmers don't fight the 
river. They use it."

**Welcome to the 1%, warrior.**""",
                "reward": "ATHENA personality and institutional insights"
            },
            
            500: {
                "title": "The Vision",
                "content": """🌟 **Norman's Final Message**

"If you're seeing this, you've made it further than 99% of traders. 
You understand now - this isn't about the money. It's about proving 
the little guy can win. Building something for everyone who's been bitten."

"Started in my room in Mississippi. Now we're a network. Each NODE 
makes us stronger. Each trader who succeeds proves it's possible."

"Bit's getting older now. Sometimes I catch him staring at new 
traders' screens, like he's passing on what he knows. Maybe that's 
what we're all doing."

"You're not just trading anymore. You're teaching. Every win shows 
someone else it's possible. Every strategy you share lifts someone up."

"Welcome to the inner circle. Time to help others bite back."

🎖️ **Unlocks**: 
- Mentorship features
- Strategy sharing capabilities  
- Legacy builder status

"From one Mississippi kid to another - we did it. Now let's 
bring everyone else up with us."

**"Not trying to get rich. Trying to get right."**

- Norman""",
                "reward": "Mentorship features and legacy status"
            }
        }
        
        # Track which stories users have seen
        self.user_progress = {}  # user_id: [seen_story_ids]
        
        # Special event stories
        self.event_stories = {
            "first_win": {
                "title": "First Victory",
                "content": "Bit's celebration purr reminds Norman of his first win..."
            },
            "first_loss": {
                "title": "First Scar",  
                "content": "Every trader bears scars. Norman's first taught him..."
            },
            "win_streak_5": {
                "title": "Hot Hand",
                "content": "Grandmama said 'Even a blind squirrel finds a nut. Don't let it go to your head.'"
            },
            "recovery": {
                "title": "Phoenix Rising",
                "content": "Like the Delta after flooding - richest soil comes after disaster..."
            }
        }
        
    def check_story_unlocks(self, user_id: str, current_xp: int) -> List[Dict]:
        """Check if user has unlocked any new story entries"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = []
            
        unlocked_stories = []
        seen_stories = self.user_progress[user_id]
        
        for xp_threshold, story in self.story_entries.items():
            if current_xp >= xp_threshold and xp_threshold not in seen_stories:
                unlocked_stories.append({
                    "xp_threshold": xp_threshold,
                    "title": story["title"],
                    "content": story["content"],
                    "reward": story["reward"]
                })
                seen_stories.append(xp_threshold)
                
        return unlocked_stories
    
    def get_story_for_event(self, event_type: str) -> Optional[Dict]:
        """Get a special story for specific events"""
        return self.event_stories.get(event_type)
    
    def get_contextual_bit_behavior(self, user_id: str, current_xp: int, market_state: str) -> str:
        """Get Bit's behavior based on user progress and market conditions"""
        # Early stage (0-100 XP)
        if current_xp < 100:
            behaviors = {
                "volatile": "🐱 *Bit's fur stands on end - danger in the air*",
                "trending": "🐾 *Bit stretches lazily - smooth sailing ahead*",
                "ranging": "🐱 *Bit paces restlessly - waiting for direction*",
                "news": "🐾 *Bit hides under the desk - storm approaching*"
            }
        # Mid stage (100-300 XP)  
        elif current_xp < 300:
            behaviors = {
                "volatile": "🐱 *Bit's tactical assessment: High risk, stay alert*",
                "trending": "🐾 *Bit purrs - institutional flow detected*",
                "ranging": "🐱 *Bit grooms patiently - accumulation phase*",
                "news": "🐾 *Bit's warning chirp - volatility incoming*"
            }
        # Advanced stage (300+ XP)
        else:
            behaviors = {
                "volatile": "🐱 *Bit identifies the liquidity hunt pattern*",
                "trending": "🐾 *Bit confirms - smart money footprints clear*",
                "ranging": "🐱 *Bit signals - compression before expansion*",
                "news": "🐾 *Bit's wisdom - let others panic first*"
            }
            
        return behaviors.get(market_state, "🐱 *Bit observes quietly*")
    
    def get_family_wisdom_for_situation(self, situation: str) -> str:
        """Get contextual family wisdom based on trading situation"""
        wisdom_map = {
            "big_loss": "Mama's voice: 'Baby, even the river runs backwards sometimes. What matters is where it ends up.'",
            "big_win": "Grandmama's warning: 'Pride goeth before destruction, and a haughty spirit before a fall.'",
            "streak": "Dad's wisdom: 'When you're hot, that's when you're most dangerous to yourself.'",
            "drawdown": "Mississippi truth: 'Drought always ends. Keep your seed corn safe.'",
            "revenge_trade": "Mama stops you: 'Honey, you're swinging at ghosts. Come back when you can see straight.'",
            "overtrading": "Grandmama's penny jar: 'Every penny thinks it's a dollar till rent comes due.'",
            "patience": "Delta wisdom: 'Good things come to those who wait, but only what's left by those who hustle.'",
            "fear": "Norman's note: 'Bit never fears the market. He respects it. Big difference.'",
            "greed": "Dad's lesson: 'Pigs get fat, hogs get slaughtered. Know which you are.'",
            "discipline": "Mama's pride: 'That's my baby. Keeping your head when others lose theirs.'"
        }
        
        return wisdom_map.get(situation, "🌾 'Trust the process' - Mississippi wisdom")
    
    def get_personality_evolution(self, personality: str, user_xp: int) -> str:
        """Get evolved personality responses based on user progress"""
        evolution_stages = {
            "DRILL": {
                "early": "RECRUIT! EXECUTE THE TRADE! NO HESITATION!",
                "mid": "Good execution, soldier. You're learning discipline. Your Grandmama would be proud of that patience.",
                "late": "Outstanding, warrior. You've got Mississippi steel in your spine now. Remember when you couldn't even read a signal?"
            },
            "DOC": {
                "early": "Careful with that position size, rookie.",
                "mid": "Your family needs you trading tomorrow. Protect the farm.",
                "late": "You've learned well. But never forget - one bad trade without stops is all it takes."
            },
            "NEXUS": {
                "early": "Welcome to the network, new NODE.",
                "mid": "Your success lifts the whole community. We rise together.",
                "late": "You're becoming a beacon for others. Time to share what you've learned."
            },
            "OVERWATCH": {
                "early": "Another retail sheep to the slaughter.",
                "mid": "You might actually survive this. Surprised me.",
                "late": "You see it now. The game behind the game. Welcome to reality."
            },
            "BIT": {
                "early": "*curious chirps* 🐱",
                "mid": "*confident purrs* 🐾",
                "late": "*synchronized breathing* 🐱"
            }
        }
        
        if user_xp < 100:
            stage = "early"
        elif user_xp < 300:
            stage = "mid"
        else:
            stage = "late"
            
        return evolution_stages.get(personality, {}).get(stage, "...")
    
    def get_norman_quote_for_milestone(self, milestone: str) -> str:
        """Get a Norman quote for specific milestones"""
        quotes = {
            "first_trade": "Everyone remembers their first. Mine was a disaster. Yours will be better.",
            "first_win": "See? The market CAN give. Just gotta know when to take.",
            "first_loss": "Now you know why we called it BITTEN. Market bit you. Time to bite back.",
            "100_xp": "You're not a tourist anymore. You live here now.",
            "tier_upgrade": "Moving up in the world. Mama would be proud.",
            "profitable_week": "String together enough good days, you get a good life.",
            "mentor_unlock": "Time to give back. Someone helped us. Now we help others.",
            "athena_unlock": "Wisdom ain't given. It's earned. You earned this.",
            "comeback": "Mississippi folks know about comebacks. Floods, storms, poverty. We always come back.",
            "mastery": "From that kid in Clarksdale to here. We did it. All of us. Together."
        }
        
        return quotes.get(milestone, "Keep pushing. Every trade teaches something.")

# Global instance
story_progression = StoryProgressionSystem()