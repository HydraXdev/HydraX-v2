"""
Norman's Notebook - Enhanced Story-Integrated Trade Journal
A deeply personal journal system that parallels Norman's journey from Mississippi Delta dreamer to disciplined trader.
Integrates family wisdom, Bit's guidance, and Delta culture for profound emotional learning.

Enhanced with:
- Norman's personal journal entries that unlock progressively
- Family wisdom integration (Grandmama's sayings, Mama's lessons)
- Bit-inspired intuitive guidance
- Mississippi Delta cultural elements
- Story phase-aware mood detection
- Tactical mission debrief integration
- Emotional healing progression tracking
"""

import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import re
from collections import defaultdict, Counter
import statistics
from enum import Enum

# Import story integration components
try:
    from .norman_story_integration import norman_story_engine, StoryPhase
    from .tactical_mission_framework import MissionPhase
except ImportError:
    # Fallback for testing
    norman_story_engine = None
    StoryPhase = None
    MissionPhase = None

class JournalType(Enum):
    """Types of journal entries"""
    USER_REFLECTION = "user_reflection"        # User's personal notes
    NORMAN_ENTRY = "norman_entry"              # Norman's unlocked journal entries
    MISSION_DEBRIEF = "mission_debrief"        # Post-mission reflections
    FAMILY_WISDOM = "family_wisdom"            # Grandmama/Mama moments
    BIT_INSIGHT = "bit_insight"                # Bit's observations
    BREAKTHROUGH = "breakthrough"              # Major realizations
    SCAR_HEALING = "scar_healing"              # Working through losses
    DELTA_REFLECTION = "delta_reflection"      # Cultural wisdom moments

class StoryProgressionTracker:
    """Tracks user's progression through Norman's story for journal unlocks"""
    
    def __init__(self):
        self.user_story_phases = {}  # user_id -> StoryPhase
        self.unlocked_entries = {}   # user_id -> List[str] (entry IDs)
        self.family_wisdom_heard = {} # user_id -> List[str]
        self.bit_encounters = {}     # user_id -> int
        
    def update_user_phase(self, user_id: str, new_phase: 'StoryPhase'):
        """Update user's story phase and unlock new content"""
        old_phase = self.user_story_phases.get(user_id, StoryPhase.EARLY_STRUGGLE if StoryPhase else None)
        self.user_story_phases[user_id] = new_phase
        
        if old_phase != new_phase:
            self._unlock_phase_content(user_id, new_phase)
    
    def _unlock_phase_content(self, user_id: str, phase: 'StoryPhase'):
        """Unlock story content for new phase"""
        if user_id not in self.unlocked_entries:
            self.unlocked_entries[user_id] = []
        
        # Phase-specific unlocks will be defined in Norman's entries database
        pass
    
    def get_available_norman_entries(self, user_id: str) -> List[str]:
        """Get Norman's journal entries available to this user"""
        return self.unlocked_entries.get(user_id, [])

class NormansNotebook:
    """Enhanced story-integrated trade journal with Norman's parallel journey"""
    
    def __init__(self, journal_path: str = "data/normans_journal.json", user_id: str = None):
        self.journal_path = journal_path
        self.user_id = user_id
        self.entries = []
        self.scars = []  # Memorable losses that taught lessons
        self.breakthroughs = []  # Moments of clarity and success
        self.norman_entries = []  # Norman's personal journal entries
        self.family_moments = []  # Family wisdom moments
        self.bit_observations = []  # Bit's insights
        self.user_trading_notes = []  # User's personal editable notes
        self.story_progression = StoryProgressionTracker()
        self.load_journal()
        
        # Initialize Norman's journal database
        self.normans_journal_database = self._initialize_normans_entries()
        self.family_wisdom_database = self._initialize_family_wisdom()
        self.bit_guidance_database = self._initialize_bit_guidance()
        self.delta_culture_database = self._initialize_delta_culture()
        
        # Enhanced emotional keywords with story phase awareness
        self.emotion_keywords = {
            'excited': ['excited', 'pumped', 'thrilled', 'euphoric', 'moon', 'lambo', 'breakthrough', 'clarity'],
            'fearful': ['scared', 'afraid', 'worried', 'anxious', 'nervous', 'panic', 'overwhelmed', 'shaking'],
            'greedy': ['greedy', 'more', 'double down', 'all in', 'yolo', 'leverage', 'risk everything'],
            'confident': ['confident', 'sure', 'certain', 'know', 'obvious', 'easy', 'trust myself', 'ready'],
            'doubtful': ['doubt', 'unsure', 'maybe', 'uncertain', 'questioning', 'second guessing'],
            'frustrated': ['frustrated', 'angry', 'pissed', 'stupid', 'hate', 'annoyed', 'stuck', 'why me'],
            'calm': ['calm', 'patient', 'steady', 'disciplined', 'controlled', 'focused', 'peaceful', 'centered'],
            'regretful': ['regret', 'should have', 'wish', 'mistake', 'wrong', 'failed', 'if only'],
            'hopeful': ['hope', 'optimistic', 'believe', 'turn around', 'recover', 'better tomorrow'],
            'defeated': ['defeated', 'quit', 'done', 'over', 'lost everything', 'wiped out', 'giving up'],
            'grateful': ['grateful', 'thankful', 'blessed', 'appreciate', 'family', 'support'],
            'determined': ['determined', 'will do this', 'not giving up', 'push through', 'for the family'],
            'humble': ['humble', 'learning', 'student', 'respect the market', 'still growing'],
            'nostalgic': ['remember when', 'back home', 'delta', 'mama', 'grandmama', 'family']
        }
        
        # Enhanced pattern templates with story integration
        self.pattern_templates = {
            'revenge_trading': ['revenge', 'get back', 'recover losses', 'double down after loss', 'show the market'],
            'fomo': ['fomo', 'missing out', 'everyone else', 'late to the party', 'chase', 'jump in'],
            'overconfidence': ['easy money', 'cant lose', 'guaranteed', 'sure thing', 'too easy'],
            'panic_selling': ['panic sold', 'scared out', 'weak hands', 'shaken out', 'fear took over'],
            'diamond_hands': ['held strong', 'conviction', 'stuck to plan', 'trusted analysis', 'stayed disciplined'],
            'cut_losses': ['cut losses', 'stopped out', 'risk management', 'protected capital', 'lived to fight'],
            'took_profits': ['took profits', 'secured gains', 'didnt get greedy', 'sold into strength', 'banked it'],
            'family_motivation': ['for mama', 'for the family', 'provide for', 'make them proud', 'change our life'],
            'norman_wisdom': ['like norman', 'norman would', 'remember the story', 'delta wisdom', 'patience'],
            'bit_guidance': ['bit would', 'cat wisdom', 'calm like bit', 'bit knows', 'intuition'],
            'grandmama_voice': ['grandmama said', 'wisdom of ages', 'patient like grandmama', 'elder wisdom'],
            'mama_strength': ['mama taught', 'protect family', 'sacrifice for others', 'mama strength'],
            'delta_connection': ['delta way', 'mississippi wisdom', 'southern patience', 'river teaches'],
            'community_focus': ['help others', 'share knowledge', 'lift community', 'pay it forward']
        }
    
    def _initialize_normans_entries(self) -> Dict[str, Any]:
        """Initialize Norman's personal journal entries database"""
        return {
            'early_struggle': [
                {
                    'id': 'norman_day1',
                    'title': "Day 1 - First Steps",
                    'date': "March 15, 2019",
                    'entry': """
Today I opened my first trading account. Hands shaking as I typed in my information. 
$500 - it's not much, but it's everything we can afford to lose. Mama doesn't know yet. 
If I can make this work, maybe I can pay for her medicine. Maybe change everything.

Bit showed up on the windowsill today. Don't know where he came from, but he watched 
me the whole time I was setting up. Like he knows something I don't.

Grandmama always said 'Patience is worth more than gold, child.' 
Gonna need all the patience I can find.
                    """,
                    'unlock_condition': 'first_trade_executed',
                    'emotional_state': 'nervous_hope',
                    'lesson': "Every journey starts with a single step"
                },
                {
                    'id': 'norman_first_loss',
                    'title': "The $200 Lesson",
                    'date': "March 22, 2019", 
                    'entry': """
Lost $200 today. FOMO got me - saw everyone talking about EUR/USD and jumped in 
without thinking. No stop loss. No plan. Just greed.

Sat on the porch afterward, Bit curled up next to me. Could hear Grandmama's voice:
'Never bet the farm on a maybe.' Should have listened.

Mama asked why I looked upset at dinner. Told her work was stressful. 
Couldn't tell her I just lost grocery money chasing a dream.

Tomorrow I start over. Smaller. Smarter. 
This market humbles you real quick if you don't respect it.
                    """,
                    'unlock_condition': 'user_experiences_significant_loss',
                    'emotional_state': 'regret_determination',
                    'lesson': "Losses are tuition for trading education"
                }
            ],
            'awakening': [
                {
                    'id': 'norman_breakthrough',
                    'title': "The First Green Week",
                    'date': "May 3, 2019",
                    'entry': """
First profitable week. $85 in profits, but it feels like a million. 
Not because of the money - because I finally understand.

It's not about being right. It's about managing risk. 
Position sizing. Having a plan and sticking to it.
Patience over impulse. System over emotion.

Bit purrs when I make good trades now. I swear he knows before I do.
Animals got instincts we lost somewhere along the way.

Called Mama tonight. Told her I might have found something. 
She said 'Baby, I'm proud of you for trying.'
That meant more than any profit ever could.
                    """,
                    'unlock_condition': 'first_profitable_week',
                    'emotional_state': 'breakthrough_clarity',
                    'lesson': "Understanding beats intelligence every time"
                }
            ],
            'discipline': [
                {
                    'id': 'norman_system',
                    'title': "Building the System",
                    'date': "August 10, 2019",
                    'entry': """
Six months in, finally got my system down. Not just rules - a real system.
Entry criteria, exit criteria, position sizing, risk management.
Even wrote it down and taped it to my monitor.

Hardest part isn't learning the rules. It's following them when 
your emotions are screaming to do something else.

Market tried to shake me out three times this week. 
But I held my positions. Trusted the analysis. Trusted the plan.
Ended up +$340. Best week yet.

Bit's been sleeping on my trading desk. Like he's standing guard.
Maybe that's what I need - a guardian to keep me honest.

Starting to believe this might actually work.
                    """,
                    'unlock_condition': 'consistent_profits_month',
                    'emotional_state': 'confident_discipline',
                    'lesson': "Systems protect you from yourself"
                }
            ],
            'mastery': [
                {
                    'id': 'norman_teaching',
                    'title': "Paying It Forward",
                    'date': "February 14, 2020",
                    'entry': """
Helped my first student today. Jamal from work. Been watching him lose money
the same way I did. Revenge trading, no plan, all emotion.

Showed him my system. Explained about position sizing, risk management.
But mostly just listened. He's carrying the same weight I was.
Family to provide for. Dreams bigger than his account.

Realized something: Teaching helps me understand better too.
When you have to explain why you do something, you see it clearer.

Bit's got competition now - Jamal brings his dog to trading sessions.
Animals understand what humans forget: patience is power.

This isn't just about making money anymore. It's about helping people
break the cycle. Building something bigger than ourselves.
                    """,
                    'unlock_condition': 'help_another_trader',
                    'emotional_state': 'purpose_fulfillment',
                    'lesson': "True mastery is measured by what you give back"
                }
            ],
            'legacy': [
                {
                    'id': 'norman_vision',
                    'title': "The Community Vision",
                    'date': "June 30, 2020",
                    'entry': """
They want me to start the community officially. A place where people
can learn the right way. No get-rich-quick promises. No false dreams.
Just honest education and support.

Been thinking about Grandmama and Mama. All the sacrifice they made.
The wisdom they passed down. Now I get to pass something down too.

Bit's old now, moves slower. But he still comes to every session.
Still knows when the market's about to turn. Still reminds me
to stay calm when things get crazy.

This is bigger than trading now. It's about changing lives.
Building a community where people lift each other up instead
of tearing each other down.

Delta wisdom flowing through fiber optic cables.
Grandmama would be proud.
                    """,
                    'unlock_condition': 'legacy_phase_achieved',
                    'emotional_state': 'legacy_pride',
                    'lesson': "Your greatest trade is the impact you have on others"
                }
            ]
        }
    
    def _initialize_family_wisdom(self) -> Dict[str, Any]:
        """Initialize family wisdom moments database"""
        return {
            'grandmama_moments': [
                {
                    'situation': 'before_big_risk',
                    'wisdom': "Never bet the farm on a maybe, child. The land provides when you tend it right, but gambling destroys everything good.",
                    'memory': "Grandmama counting change from her mason jar, teaching Norman the value of every penny",
                    'application': "Use proper position sizing - never risk more than you can afford to lose"
                },
                {
                    'situation': 'impatience',
                    'wisdom': "Good things come to those who wait for the right season. Cotton don't grow overnight, and wealth don't either.",
                    'memory': "Sitting on the porch, watching Grandmama's patience as she waited for storms to pass",
                    'application': "Wait for high-probability setups instead of forcing trades"
                },
                {
                    'situation': 'after_loss',
                    'wisdom': "The storm passes, but the oak remembers how to bend. Strong roots keep you standing when the wind tries to break you.",
                    'memory': "Grandmama's weathered hands, steady despite all the hardships she'd weathered",
                    'application': "Learn from losses but don't let them break your confidence"
                },
                {
                    'situation': 'success',
                    'wisdom': "Pride comes before the fall, baby. Stay humble, stay hungry, stay close to what matters.",
                    'memory': "Grandmama's gentle correction when young Norman got too proud of small achievements",
                    'application': "Success in trading requires constant humility and respect for the market"
                }
            ],
            'mama_moments': [
                {
                    'situation': 'family_responsibility',
                    'wisdom': "Your family needs you more than any gamble ever will. Protect what you have before you reach for more.",
                    'memory': "Mama working two jobs, never complaining, always putting family first",
                    'application': "Trading is about providing for family, not risking their security"
                },
                {
                    'situation': 'sacrifice',
                    'wisdom': "Every dollar saved is a dollar earned through sacrifice. Honor the work that went into it.",
                    'memory': "Mama's tired eyes counting bills, making every dollar stretch for the family",
                    'application': "Respect your trading capital - it represents real sacrifice and work"
                },
                {
                    'situation': 'strength',
                    'wisdom': "Know when to hold on and when to let go. Strength isn't stubbornness - it's wisdom in action.",
                    'memory': "Mama's decision to let Norman's father go - painful but necessary for family peace",
                    'application': "Cut losses quickly, but let winners run according to your plan"
                },
                {
                    'situation': 'belief',
                    'wisdom': "Don't put all your eggs in one basket, baby. Spread the risk, protect the family.",
                    'memory': "Mama's practical wisdom about not depending on any single source of income",
                    'application': "Diversify your trading approach and never risk everything on one trade"
                }
            ]
        }
    
    def _initialize_bit_guidance(self) -> Dict[str, Any]:
        """Initialize Bit's intuitive guidance system"""
        return {
            'pre_trade_signals': [
                {
                    'behavior': 'confident_stretch',
                    'message': "*Bit stretches with full confidence - he senses opportunity in the air*",
                    'interpretation': "Strong setup detected - proceed with standard position size",
                    'visual_cue': 'cat_confident_stretch.gif',
                    'audio_cue': 'encouraging_purr.mp3'
                },
                {
                    'behavior': 'cautious_crouch',
                    'message': "*Bit crouches low, ears alert - proceed carefully, danger lurks*",
                    'interpretation': "Risk warning - reduce position size or wait for better setup",
                    'visual_cue': 'cat_cautious_crouch.gif', 
                    'audio_cue': 'warning_chirp.mp3'
                },
                {
                    'behavior': 'patient_sitting',
                    'message': "*Bit sits perfectly still, demonstrating the art of patience*",
                    'interpretation': "Wait for clearer signal - patience will be rewarded",
                    'visual_cue': 'cat_patient_meditation.gif',
                    'audio_cue': 'calm_breathing.mp3'
                }
            ],
            'during_trade_guidance': [
                {
                    'situation': 'drawdown',
                    'behavior': 'calming_presence',
                    'message': "*Bit settles beside you, his calm presence reminding you to breathe*",
                    'wisdom': "Trust your stop loss - Bit knows when to rest and when to hunt"
                },
                {
                    'situation': 'profit',
                    'behavior': 'alert_watching',
                    'message': "*Bit watches intently, ready for the right moment to pounce*",
                    'wisdom': "Stay alert for exit signals - even successful hunts must end"
                },
                {
                    'situation': 'uncertainty',
                    'behavior': 'whisker_twitch',
                    'message': "*Bit's whiskers twitch - he senses something you can't see yet*",
                    'wisdom': "Trust your instincts - something in the market is about to shift"
                }
            ],
            'post_trade_insights': [
                {
                    'outcome': 'loss',
                    'behavior': 'comforting_purr',
                    'message': "*Bit purrs softly and curls up nearby - every hunter has misses*",
                    'lesson': "Even the best hunters don't catch every prey - learn and move on"
                },
                {
                    'outcome': 'win',
                    'behavior': 'victory_stretch',
                    'message': "*Bit does his satisfied victory stretch - hunt successful*",
                    'lesson': "Celebrate briefly, then prepare for the next opportunity"
                },
                {
                    'outcome': 'breakeven',
                    'behavior': 'thoughtful_grooming',
                    'message': "*Bit grooms thoughtfully - sometimes the best hunt is no hunt*",
                    'lesson': "Living to hunt another day is always a victory"
                }
            ]
        }
    
    def _initialize_delta_culture(self) -> Dict[str, Any]:
        """Initialize Mississippi Delta cultural elements"""
        return {
            'seasonal_wisdom': [
                {
                    'season': 'spring',
                    'lesson': "Spring rains bring growth if you've prepared the ground",
                    'trading_application': "New opportunities emerge after periods of consolidation",
                    'cultural_context': "Delta farmers know that preparation during winter determines spring success"
                },
                {
                    'season': 'summer',
                    'lesson': "Summer teaches abundance, but remember winter is coming",
                    'trading_application': "Profitable periods require saving for lean times",
                    'cultural_context': "Cotton season prosperity must sustain families through the entire year"
                },
                {
                    'season': 'fall',
                    'lesson': "Harvest comes to those who tend their fields daily",
                    'trading_application': "Consistent daily habits lead to long-term success",
                    'cultural_context': "Delta harvest time rewards the farmers who showed up every day"
                },
                {
                    'season': 'winter',
                    'lesson': "Winter teaches conservation and preparation",
                    'trading_application': "Protect capital during uncertain market conditions",
                    'cultural_context': "Surviving Delta winters requires careful resource management"
                }
            ],
            'river_wisdom': [
                {
                    'principle': 'flow_around_obstacles',
                    'saying': "The river flows around obstacles, not through them",
                    'trading_lesson': "Adapt to market conditions instead of fighting them",
                    'story': "Norman learned to read market flow like old-timers read the Mississippi"
                },
                {
                    'principle': 'patience_of_water',
                    'saying': "Water always finds a way, but never in a hurry",
                    'trading_lesson': "Persistent patience overcomes all obstacles",
                    'story': "Like the Delta itself, formed by millions of years of patient water"
                },
                {
                    'principle': 'respect_the_flood',
                    'saying': "When the river rises, smart folks move to higher ground",
                    'trading_lesson': "Know when to step aside and preserve capital",
                    'story': "Delta families learned to read flood signs and act early"
                }
            ],
            'community_values': [
                {
                    'value': 'mutual_support',
                    'expression': "Your neighbor's success is your success",
                    'trading_application': "Share knowledge and lift the whole community",
                    'manifestation': "Norman's vision of traders helping each other succeed"
                },
                {
                    'value': 'word_as_bond',
                    'expression': "Your word is your bond in the Delta",
                    'trading_application': "Honor your stop losses and trading rules",
                    'manifestation': "Keeping promises to yourself builds unshakeable discipline"
                },
                {
                    'value': 'respect_for_elders',
                    'expression': "Listen to your elders - they've seen more seasons",
                    'trading_application': "Learn from experienced traders and market history",
                    'manifestation': "Norman's respect for Grandmama's wisdom translated to market wisdom"
                }
            ]
        }
    
    def load_journal(self):
        """Load existing journal entries and story progression"""
        if os.path.exists(self.journal_path):
            with open(self.journal_path, 'r') as f:
                data = json.load(f)
                self.entries = data.get('entries', [])
                self.scars = data.get('scars', [])
                self.breakthroughs = data.get('breakthroughs', [])
                self.norman_entries = data.get('norman_entries', [])
                self.family_moments = data.get('family_moments', [])
                self.bit_observations = data.get('bit_observations', [])
                self.user_trading_notes = data.get('user_trading_notes', [])
                
                # Load story progression data
                story_data = data.get('story_progression', {})
                if self.user_id:
                    self.story_progression.user_story_phases = story_data.get('user_phases', {})
                    self.story_progression.unlocked_entries = story_data.get('unlocked_entries', {})
                    self.story_progression.family_wisdom_heard = story_data.get('family_wisdom_heard', {})
                    self.story_progression.bit_encounters = story_data.get('bit_encounters', {})
    
    def save_journal(self):
        """Save enhanced journal with all story elements to disk"""
        os.makedirs(os.path.dirname(self.journal_path), exist_ok=True)
        with open(self.journal_path, 'w') as f:
            json.dump({
                'entries': self.entries,
                'scars': self.scars,
                'breakthroughs': self.breakthroughs,
                'norman_entries': self.norman_entries,
                'family_moments': self.family_moments,
                'bit_observations': self.bit_observations,
                'user_trading_notes': self.user_trading_notes,
                'story_progression': {
                    'user_phases': self.story_progression.user_story_phases,
                    'unlocked_entries': self.story_progression.unlocked_entries,
                    'family_wisdom_heard': self.story_progression.family_wisdom_heard,
                    'bit_encounters': self.story_progression.bit_encounters
                }
            }, f, indent=2)
    
    def add_entry(self, 
                  trade_id: Optional[str] = None,
                  phase: str = 'general',  # 'before', 'during', 'after', 'general'
                  note: str = "",
                  symbol: Optional[str] = None,
                  pnl: Optional[float] = None):
        """Add a journal entry with automatic mood detection"""
        
        mood = self.detect_mood(note)
        patterns = self.detect_patterns(note)
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'trade_id': trade_id,
            'phase': phase,
            'note': note,
            'symbol': symbol,
            'pnl': pnl,
            'mood': mood,
            'patterns': patterns
        }
        
        self.entries.append(entry)
        
        # Check if this is a scar (memorable loss)
        if pnl and pnl < -100 and phase == 'after':
            self._check_for_scar(entry)
        
        # Check if this is a breakthrough
        if pnl and pnl > 500 and phase == 'after':
            self._check_for_breakthrough(entry)
        
        self.save_journal()
        return entry
    
    def detect_mood(self, text: str) -> Dict[str, float]:
        """Detect emotional state from journal text"""
        text_lower = text.lower()
        mood_scores = defaultdict(float)
        
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    mood_scores[emotion] += 1
        
        # Normalize scores
        total = sum(mood_scores.values())
        if total > 0:
            mood_scores = {k: v/total for k, v in mood_scores.items()}
        
        return dict(mood_scores)
    
    def detect_patterns(self, text: str) -> List[str]:
        """Detect behavioral patterns from journal text"""
        text_lower = text.lower()
        detected_patterns = []
        
        for pattern, indicators in self.pattern_templates.items():
            for indicator in indicators:
                if indicator in text_lower:
                    detected_patterns.append(pattern)
                    break
        
        return detected_patterns
    
    def _check_for_scar(self, entry: Dict):
        """Check if a loss is significant enough to be a 'scar'"""
        if abs(entry['pnl']) > 100:  # Significant loss
            lesson_prompt = f"What lesson did you learn from this {entry['pnl']:.2f} loss?"
            
            scar = {
                'timestamp': entry['timestamp'],
                'symbol': entry['symbol'],
                'loss': entry['pnl'],
                'note': entry['note'],
                'lesson': lesson_prompt,  # To be filled by user
                'healed': False  # Becomes true when similar situation handled better
            }
            
            self.scars.append(scar)
    
    def _check_for_breakthrough(self, entry: Dict):
        """Check if a win represents a breakthrough moment"""
        if entry['pnl'] > 500:  # Significant win
            breakthrough = {
                'timestamp': entry['timestamp'],
                'symbol': entry['symbol'],
                'gain': entry['pnl'],
                'note': entry['note'],
                'key_insight': "What made this trade different?",  # To be filled
                'replicated': 0  # Track if lesson was successfully repeated
            }
            
            self.breakthroughs.append(breakthrough)
    
    def get_weekly_review(self) -> str:
        """Generate a weekly review in Norman's voice"""
        one_week_ago = datetime.now() - timedelta(days=7)
        recent_entries = [e for e in self.entries 
                         if datetime.fromisoformat(e['timestamp']) > one_week_ago]
        
        if not recent_entries:
            return "📓 Empty week in the notebook. Sometimes silence speaks volumes..."
        
        # Analyze the week
        total_pnl = sum(e.get('pnl', 0) for e in recent_entries if e.get('pnl'))
        mood_counter = Counter()
        pattern_counter = Counter()
        
        for entry in recent_entries:
            for mood, score in entry.get('mood', {}).items():
                mood_counter[mood] += score
            for pattern in entry.get('patterns', []):
                pattern_counter[pattern] += 1
        
        # Find dominant mood and patterns
        dominant_mood = mood_counter.most_common(1)[0][0] if mood_counter else 'neutral'
        common_patterns = pattern_counter.most_common(3)
        
        # Generate review in Norman's voice
        review = f"""
📓 **Norman's Weekly Reflection**
*{datetime.now().strftime('%B %d, %Y')}*

This week's journey: {'profitable' if total_pnl > 0 else 'challenging'}
P&L: ${total_pnl:,.2f}

**Emotional Landscape:**
The dominant feeling was {dominant_mood}. """
        
        if dominant_mood in ['excited', 'greedy']:
            review += "Remember: The market humbles those who forget humility."
        elif dominant_mood in ['fearful', 'defeated']:
            review += "Fear is natural, but don't let it paralyze you. Every master was once a disaster."
        elif dominant_mood == 'calm':
            review += "This is the way. Calm seas make skilled sailors."
        
        if common_patterns:
            review += "\n\n**Patterns I Noticed:**\n"
            for pattern, count in common_patterns:
                if pattern == 'revenge_trading':
                    review += f"- Revenge trading appeared {count} times. The market doesn't care about your ego.\n"
                elif pattern == 'fomo':
                    review += f"- FOMO struck {count} times. There's always another bus coming.\n"
                elif pattern == 'diamond_hands':
                    review += f"- Showed conviction {count} times. Trust your analysis, but verify with price action.\n"
                elif pattern == 'cut_losses':
                    review += f"- Cut losses {count} times. Live to trade another day.\n"
        
        # Add scar check
        recent_scars = [s for s in self.scars if not s['healed']]
        if recent_scars:
            review += f"\n\n**Scars Still Healing:**\n"
            review += f"You carry {len(recent_scars)} lessons from past battles. Have you truly learned?\n"
        
        # Add personalized advice based on patterns
        review += "\n\n**This Week's Medicine:**\n"
        if 'revenge_trading' in [p[0] for p in common_patterns]:
            review += "- When you feel the urge for revenge, step away. The market will be there tomorrow.\n"
        if 'fomo' in [p[0] for p in common_patterns]:
            review += "- Write down 3 reasons before entering any trade. FOMO isn't one of them.\n"
        if total_pnl < -1000:
            review += "- Consider reducing position sizes. Survival first, profits second.\n"
        if total_pnl > 2000:
            review += "- Success is dangerous. Stay humble, stay hungry, stay disciplined.\n"
        
        review += "\n*Remember: I'm not trying to get rich. I'm trying to get right.*"
        
        return review
    
    def get_recent_entries(self, limit: int = 10) -> List[Dict]:
        """Get recent journal entries for display"""
        # Sort entries by timestamp (most recent first)
        sorted_entries = sorted(self.entries, 
                               key=lambda x: x.get('timestamp', ''), 
                               reverse=True)
        return sorted_entries[:limit]
    
    def get_user_emotional_state(self) -> Dict[str, Any]:
        """Get current user emotional state metrics"""
        recent_entries = self.get_recent_entries(limit=30)
        
        if not recent_entries:
            return {
                'confidence': 'Building...',
                'discipline': 'Growing...',
                'patience': 'Learning...'
            }
        
        # Calculate emotional metrics from recent entries
        mood_scores = defaultdict(list)
        for entry in recent_entries:
            for mood, score in entry.get('mood', {}).items():
                mood_scores[mood].append(score)
        
        # Average the scores
        metrics = {}
        for mood, scores in mood_scores.items():
            avg_score = statistics.mean(scores) if scores else 0
            if mood == 'calm':
                metrics['confidence'] = f"{avg_score:.1f}/10"
            elif mood == 'disciplined':
                metrics['discipline'] = f"{avg_score:.1f}/10"
            elif mood == 'patient':
                metrics['patience'] = f"{avg_score:.1f}/10"
        
        # Provide defaults if no data
        return {
            'confidence': metrics.get('confidence', 'N/A'),
            'discipline': metrics.get('discipline', 'N/A'),
            'patience': metrics.get('patience', 'N/A')
        }

    def find_repeated_mistakes(self, min_occurrences: int = 3) -> Dict[str, List[Dict]]:
        """Find patterns that keep repeating"""
        pattern_entries = defaultdict(list)
        
        for entry in self.entries:
            for pattern in entry.get('patterns', []):
                if pattern in ['revenge_trading', 'fomo', 'overconfidence', 'panic_selling']:
                    pattern_entries[pattern].append(entry)
        
        # Filter to repeated patterns
        repeated = {k: v for k, v in pattern_entries.items() if len(v) >= min_occurrences}
        
        return repeated
    
    def get_growth_trajectory(self) -> Dict[str, any]:
        """Analyze growth over time"""
        if len(self.entries) < 10:
            return {"status": "Too early to tell. Keep journaling."}
        
        # Split entries into early and recent
        midpoint = len(self.entries) // 2
        early_entries = self.entries[:midpoint]
        recent_entries = self.entries[midpoint:]
        
        # Compare emotional states
        early_moods = Counter()
        recent_moods = Counter()
        
        for entry in early_entries:
            for mood, score in entry.get('mood', {}).items():
                early_moods[mood] += score
                
        for entry in recent_entries:
            for mood, score in entry.get('mood', {}).items():
                recent_moods[mood] += score
        
        # Normalize
        early_total = sum(early_moods.values())
        recent_total = sum(recent_moods.values())
        
        if early_total > 0:
            early_moods = {k: v/early_total for k, v in early_moods.items()}
        if recent_total > 0:
            recent_moods = {k: v/recent_total for k, v in recent_moods.items()}
        
        # Calculate improvement metrics
        calm_increase = recent_moods.get('calm', 0) - early_moods.get('calm', 0)
        fear_decrease = early_moods.get('fearful', 0) - recent_moods.get('fearful', 0)
        greed_decrease = early_moods.get('greedy', 0) - recent_moods.get('greedy', 0)
        
        return {
            'early_emotional_state': dict(early_moods),
            'recent_emotional_state': dict(recent_moods),
            'calm_increase': calm_increase,
            'fear_decrease': fear_decrease,
            'greed_decrease': greed_decrease,
            'trajectory': 'improving' if calm_increase > 0.1 else 'work in progress',
            'breakthrough_count': len(self.breakthroughs),
            'unhealed_scars': len([s for s in self.scars if not s['healed']])
        }
    
    def add_trade_reflection(self, trade_id: str, reflection: str):
        """Add a reflection after a trade is closed"""
        entry = self.add_entry(
            trade_id=trade_id,
            phase='after',
            note=reflection
        )
        
        # Check if this reflection shows growth from past scars
        for scar in self.scars:
            if not scar['healed'] and scar['symbol'] in reflection:
                # Look for signs of learning
                if any(phrase in reflection.lower() for phrase in 
                       ['learned from', 'remembered', 'different this time', 'applied lesson']):
                    scar['healed'] = True
                    scar['healing_date'] = datetime.now().isoformat()
        
        return entry
    
    def get_symbol_history(self, symbol: str) -> List[Dict]:
        """Get all journal entries for a specific symbol"""
        return [e for e in self.entries if e.get('symbol') == symbol]
    
    def get_emotional_chart_data(self) -> Dict[str, List]:
        """Get data for plotting emotional journey over time"""
        if not self.entries:
            return {}
        
        # Group by date
        daily_moods = defaultdict(lambda: defaultdict(float))
        
        for entry in self.entries:
            date = datetime.fromisoformat(entry['timestamp']).date()
            for mood, score in entry.get('mood', {}).items():
                daily_moods[date][mood] += score
        
        # Convert to chart format
        dates = sorted(daily_moods.keys())
        mood_series = defaultdict(list)
        
        for date in dates:
            day_total = sum(daily_moods[date].values())
            for mood in self.emotion_keywords.keys():
                if day_total > 0:
                    mood_series[mood].append(daily_moods[date][mood] / day_total)
                else:
                    mood_series[mood].append(0)
        
        return {
            'dates': [d.isoformat() for d in dates],
            'series': dict(mood_series)
        }
    
    def generate_mantra(self) -> str:
        """Generate a personalized mantra based on patterns"""
        repeated_mistakes = self.find_repeated_mistakes()
        
        if 'revenge_trading' in repeated_mistakes:
            return "The market owes me nothing. I owe myself discipline."
        elif 'fomo' in repeated_mistakes:
            return "There's always another trade. Patience is my edge."
        elif 'overconfidence' in repeated_mistakes:
            return "Humility before profits. The market is always the teacher."
        elif len(self.scars) > 5:
            return "My scars are my teachers. Each loss brings wisdom."
        elif len(self.breakthroughs) > 3:
            return "Trust the process. My breakthroughs show the way."
        else:
            return "One trade at a time. One lesson at a time. This is my journey."
    
    # ===== USER TRADING NOTES SYSTEM =====
    
    def add_user_note(self, 
                      title: str,
                      content: str,
                      category: str = "general",
                      tags: List[str] = None,
                      symbol: str = None,
                      trade_id: str = None) -> Dict:
        """Add a user-editable trading note"""
        note = {
            'id': f"note_{int(datetime.now().timestamp())}_{len(self.user_trading_notes)}",
            'title': title,
            'content': content,
            'category': category,  # general, strategy, analysis, reminder, goal, lesson
            'tags': tags or [],
            'symbol': symbol,
            'trade_id': trade_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'pinned': False,
            'archived': False
        }
        
        self.user_trading_notes.append(note)
        self.save_journal()
        return note
    
    def edit_user_note(self, note_id: str, updates: Dict) -> bool:
        """Edit an existing user note"""
        for note in self.user_trading_notes:
            if note['id'] == note_id:
                # Update allowed fields
                for field in ['title', 'content', 'category', 'tags', 'symbol', 'pinned']:
                    if field in updates:
                        note[field] = updates[field]
                
                note['updated_at'] = datetime.now().isoformat()
                self.save_journal()
                return True
        return False
    
    def delete_user_note(self, note_id: str) -> bool:
        """Delete a user note"""
        for i, note in enumerate(self.user_trading_notes):
            if note['id'] == note_id:
                del self.user_trading_notes[i]
                self.save_journal()
                return True
        return False
    
    def archive_user_note(self, note_id: str) -> bool:
        """Archive a user note (soft delete)"""
        for note in self.user_trading_notes:
            if note['id'] == note_id:
                note['archived'] = True
                note['updated_at'] = datetime.now().isoformat()
                self.save_journal()
                return True
        return False
    
    def pin_user_note(self, note_id: str, pinned: bool = True) -> bool:
        """Pin/unpin a user note"""
        for note in self.user_trading_notes:
            if note['id'] == note_id:
                note['pinned'] = pinned
                note['updated_at'] = datetime.now().isoformat()
                self.save_journal()
                return True
        return False
    
    def get_user_notes(self, 
                       category: str = None,
                       symbol: str = None,
                       tags: List[str] = None,
                       include_archived: bool = False,
                       pinned_only: bool = False) -> List[Dict]:
        """Get user notes with optional filtering"""
        notes = self.user_trading_notes.copy()
        
        # Filter archived
        if not include_archived:
            notes = [n for n in notes if not n.get('archived', False)]
        
        # Filter by category
        if category:
            notes = [n for n in notes if n.get('category') == category]
        
        # Filter by symbol
        if symbol:
            notes = [n for n in notes if n.get('symbol') == symbol]
        
        # Filter by tags
        if tags:
            notes = [n for n in notes if any(tag in n.get('tags', []) for tag in tags)]
        
        # Filter pinned only
        if pinned_only:
            notes = [n for n in notes if n.get('pinned', False)]
        
        # Sort: pinned first, then by updated_at descending
        notes.sort(key=lambda x: (not x.get('pinned', False), x.get('updated_at', '')), reverse=True)
        
        return notes
    
    def search_user_notes(self, query: str) -> List[Dict]:
        """Search user notes by title and content"""
        query_lower = query.lower()
        results = []
        
        for note in self.user_trading_notes:
            if note.get('archived', False):
                continue
                
            # Search in title and content
            if (query_lower in note.get('title', '').lower() or 
                query_lower in note.get('content', '').lower() or
                query_lower in ' '.join(note.get('tags', [])).lower()):
                results.append(note)
        
        return results
    
    def get_notes_by_symbol(self, symbol: str) -> List[Dict]:
        """Get all notes for a specific trading symbol"""
        return [n for n in self.user_trading_notes 
                if n.get('symbol') == symbol and not n.get('archived', False)]
    
    def get_notes_by_trade(self, trade_id: str) -> List[Dict]:
        """Get all notes related to a specific trade"""
        return [n for n in self.user_trading_notes 
                if n.get('trade_id') == trade_id and not n.get('archived', False)]
    
    def create_quick_note_templates(self) -> Dict[str, Dict]:
        """Predefined note templates for quick creation"""
        return {
            'trade_plan': {
                'title': 'Trade Plan - {symbol}',
                'content': '''📋 **Trade Plan**
                
**Symbol:** {symbol}
**Direction:** 
**Entry Criteria:**
- 
- 
- 

**Risk Management:**
- Position Size: 
- Stop Loss: 
- Take Profit: 

**Why This Trade:**


**Market Context:**


**Notes:**

''',
                'category': 'strategy',
                'tags': ['plan', 'strategy']
            },
            
            'daily_review': {
                'title': 'Daily Review - {date}',
                'content': '''📊 **Daily Trading Review**

**Date:** {date}

**Trades Taken:**
- 

**What Went Well:**
- 

**What Could Improve:**
- 

**Lessons Learned:**
- 

**Tomorrow's Focus:**
- 

**Mood/Mindset:**

**Market Observations:**

''',
                'category': 'analysis',
                'tags': ['review', 'daily']
            },
            
            'lesson_learned': {
                'title': 'Lesson: {lesson_title}',
                'content': '''💡 **Trading Lesson**

**What Happened:**


**What I Learned:**


**How to Apply This:**


**Reminder to Future Self:**


**Related Symbols/Situations:**

''',
                'category': 'lesson',
                'tags': ['lesson', 'wisdom']
            },
            
            'strategy_note': {
                'title': 'Strategy: {strategy_name}',
                'content': '''🎯 **Trading Strategy**

**Strategy Name:** {strategy_name}

**Entry Rules:**
1. 
2. 
3. 

**Exit Rules:**
1. 
2. 

**Risk Management:**
- Max Risk per Trade: 
- Win Rate Target: 
- Risk:Reward Ratio: 

**Best Market Conditions:**


**Avoid When:**


**Backtest Results:**


**Real Trading Notes:**

''',
                'category': 'strategy',
                'tags': ['strategy', 'rules']
            },
            
            'market_analysis': {
                'title': 'Market Analysis - {symbol} {date}',
                'content': '''📈 **Market Analysis**

**Symbol:** {symbol}
**Date:** {date}

**Technical Analysis:**
- Trend: 
- Support: 
- Resistance: 
- Key Levels: 

**Fundamental Factors:**


**Sentiment:**


**News/Events:**


**Trading Opportunities:**


**Risk Factors:**

''',
                'category': 'analysis',
                'tags': ['analysis', 'technical']
            },
            
            'goal_tracker': {
                'title': 'Trading Goal: {goal_name}',
                'content': '''🎯 **Trading Goal**

**Goal:** {goal_name}

**Target Date:** 

**Current Progress:**


**Action Steps:**
1. 
2. 
3. 

**Metrics to Track:**
- 
- 

**Challenges Expected:**


**Success Criteria:**


**Progress Updates:**

''',
                'category': 'goal',
                'tags': ['goal', 'planning']
            },
            
            'quick_note': {
                'title': 'Quick Note',
                'content': '''📝 **Quick Trading Note**

**What's on my mind:**


**Action Items:**
- 


**Follow up:**

''',
                'category': 'general',
                'tags': ['quick', 'reminder']
            }
        }
    
    def create_note_from_template(self, template_name: str, variables: Dict = None) -> Dict:
        """Create a note from a predefined template"""
        templates = self.create_quick_note_templates()
        
        if template_name not in templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = templates[template_name].copy()
        variables = variables or {}
        
        # Fill in variables
        for field in ['title', 'content']:
            if field in template:
                template[field] = template[field].format(**variables)
        
        return self.add_user_note(
            title=template['title'],
            content=template['content'],
            category=template['category'],
            tags=template['tags'],
            symbol=variables.get('symbol'),
            trade_id=variables.get('trade_id')
        )
    
    def export_user_notes(self, format_type: str = 'json') -> str:
        """Export user notes to different formats"""
        active_notes = [n for n in self.user_trading_notes if not n.get('archived', False)]
        
        if format_type == 'json':
            return json.dumps(active_notes, indent=2)
        
        elif format_type == 'markdown':
            md_content = "# Trading Notes Export\n\n"
            
            # Group by category
            categories = {}
            for note in active_notes:
                cat = note.get('category', 'general')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(note)
            
            for category, notes in categories.items():
                md_content += f"## {category.title()}\n\n"
                for note in notes:
                    md_content += f"### {note['title']}\n\n"
                    md_content += f"{note['content']}\n\n"
                    if note.get('tags'):
                        md_content += f"*Tags: {', '.join(note['tags'])}*\n\n"
                    md_content += "---\n\n"
            
            return md_content
        
        elif format_type == 'text':
            text_content = "TRADING NOTES EXPORT\n" + "="*50 + "\n\n"
            
            for note in active_notes:
                text_content += f"TITLE: {note['title']}\n"
                text_content += f"CATEGORY: {note.get('category', 'general')}\n"
                text_content += f"CREATED: {note['created_at']}\n"
                if note.get('tags'):
                    text_content += f"TAGS: {', '.join(note['tags'])}\n"
                text_content += "\nCONTENT:\n"
                text_content += note['content']
                text_content += "\n\n" + "-"*50 + "\n\n"
            
            return text_content
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def get_notes_stats(self) -> Dict:
        """Get statistics about user notes"""
        active_notes = [n for n in self.user_trading_notes if not n.get('archived', False)]
        
        # Category breakdown
        categories = {}
        for note in active_notes:
            cat = note.get('category', 'general')
            categories[cat] = categories.get(cat, 0) + 1
        
        # Tag frequency
        tag_freq = {}
        for note in active_notes:
            for tag in note.get('tags', []):
                tag_freq[tag] = tag_freq.get(tag, 0) + 1
        
        # Recent activity
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        recent_week = sum(1 for n in active_notes 
                         if datetime.fromisoformat(n['updated_at']) > week_ago)
        recent_month = sum(1 for n in active_notes 
                          if datetime.fromisoformat(n['updated_at']) > month_ago)
        
        return {
            'total_notes': len(active_notes),
            'archived_notes': len([n for n in self.user_trading_notes if n.get('archived', False)]),
            'pinned_notes': len([n for n in active_notes if n.get('pinned', False)]),
            'categories': categories,
            'top_tags': sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)[:10],
            'notes_this_week': recent_week,
            'notes_this_month': recent_month,
            'oldest_note': min(active_notes, key=lambda x: x['created_at'])['created_at'] if active_notes else None,
            'newest_note': max(active_notes, key=lambda x: x['updated_at'])['updated_at'] if active_notes else None
        }


class TradingLessonExtractor:
    """Extract and summarize lessons from journal entries"""
    
    def __init__(self, notebook: NormansNotebook):
        self.notebook = notebook
    
    def extract_winning_patterns(self) -> List[Dict]:
        """Find what works from profitable trades"""
        profitable_entries = [e for e in self.notebook.entries 
                            if e.get('pnl', 0) > 100]
        
        winning_patterns = defaultdict(list)
        
        for entry in profitable_entries:
            for pattern in entry.get('patterns', []):
                if pattern in ['diamond_hands', 'cut_losses', 'took_profits']:
                    winning_patterns[pattern].append({
                        'date': entry['timestamp'],
                        'pnl': entry['pnl'],
                        'note': entry['note']
                    })
        
        return dict(winning_patterns)
    
    def create_rules_from_scars(self) -> List[str]:
        """Generate trading rules from painful lessons"""
        rules = []
        
        for scar in self.notebook.scars:
            if scar['loss'] < -500:
                rules.append(f"Never risk more than {abs(scar['loss'])/10:.0f} on a single trade")
            
            if 'fomo' in scar['note'].lower():
                rules.append("If you feel FOMO, wait 24 hours before entering")
            
            if 'revenge' in scar['note'].lower():
                rules.append("After a loss, take a break. No trades for at least 2 hours")
            
            if 'averaged down' in scar['note'].lower():
                rules.append("Set a stop loss and honor it. No averaging down without a plan")
        
        return list(set(rules))  # Remove duplicates
    
    def summarize_journey(self) -> str:
        """Create a narrative summary of the trading journey"""
        total_entries = len(self.notebook.entries)
        total_scars = len(self.notebook.scars)
        healed_scars = len([s for s in self.notebook.scars if s['healed']])
        total_breakthroughs = len(self.notebook.breakthroughs)
        
        trajectory = self.notebook.get_growth_trajectory()
        
        summary = f"""
📖 **The Story So Far**

{total_entries} journal entries tell the tale of transformation.

**The Battles:**
- {total_scars} scars earned in the arena
- {healed_scars} wounds that became wisdom
- {total_breakthroughs} breakthrough moments of clarity

**The Evolution:**
"""
        
        if trajectory.get('trajectory') == 'improving':
            summary += "You're becoming the trader you were meant to be. "
            summary += f"Calmness increased by {trajectory['calm_increase']*100:.0f}%. "
            summary += f"Fear decreased by {trajectory['fear_decrease']*100:.0f}%.\n"
        else:
            summary += "The journey continues. Every master was once a disaster. "
            summary += "Keep showing up, keep learning, keep growing.\n"
        
        # Add current state
        recent_moods = trajectory.get('recent_emotional_state', {})
        if recent_moods:
            dominant = max(recent_moods.items(), key=lambda x: x[1])
            summary += f"\n**Current State:** {dominant[0].title()}\n"
        
        # Add personalized message
        if total_scars > 10:
            summary += "\nYou've been battle-tested. Each scar is a badge of honor, a lesson learned."
        elif total_breakthroughs > 5:
            summary += "\nYour breakthroughs light the path forward. Trust what you've learned."
        else:
            summary += "\nYou're still early in the journey. Be patient with yourself."
        
        summary += "\n\n*Remember: Trading is not about being right. It's about being profitable.*"
        
        return summary


# Integration functions for the broader system
def create_journal_entry_from_trade(trade_data: Dict, notebook: NormansNotebook):
    """Automatically create journal entries from trade data"""
    
    # Entry when position opened
    if trade_data.get('status') == 'open':
        notebook.add_entry(
            trade_id=trade_data['id'],
            phase='before',
            symbol=trade_data['symbol'],
            note=f"Opened position in {trade_data['symbol']}. "
                 f"Risk: ${trade_data.get('risk', 0):.2f}"
        )
    
    # Entry when position closed
    elif trade_data.get('status') == 'closed':
        pnl = trade_data.get('pnl', 0)
        notebook.add_entry(
            trade_id=trade_data['id'],
            phase='after',
            symbol=trade_data['symbol'],
            pnl=pnl,
            note=f"Closed {trade_data['symbol']}. "
                 f"P&L: ${pnl:.2f}. "
                 f"{'Profit' if pnl > 0 else 'Loss'} of {abs(pnl/trade_data.get('entry_price', 1)*100):.1f}%"
        )


def get_journal_insights_for_symbol(symbol: str, notebook: NormansNotebook) -> Dict:
    """Get historical insights for a symbol from journal"""
    history = notebook.get_symbol_history(symbol)
    
    if not history:
        return {
            'has_history': False,
            'message': f"First time trading {symbol}. Make it count."
        }
    
    # Analyze past experiences
    total_pnl = sum(e.get('pnl', 0) for e in history if e.get('pnl'))
    moods = Counter()
    patterns = Counter()
    
    for entry in history:
        for mood, score in entry.get('mood', {}).items():
            moods[mood] += score
        for pattern in entry.get('patterns', []):
            patterns[pattern] += 1
    
    insights = {
        'has_history': True,
        'trade_count': len(history),
        'total_pnl': total_pnl,
        'dominant_mood': moods.most_common(1)[0][0] if moods else 'neutral',
        'common_patterns': [p[0] for p in patterns.most_common(3)],
        'last_experience': history[-1]['note'] if history else None
    }
    
    # Generate wisdom
    if total_pnl < -500:
        insights['warning'] = f"{symbol} has been your nemesis. Different approach needed."
    elif total_pnl > 1000:
        insights['confidence'] = f"{symbol} has treated you well. Stay disciplined."
    
    if 'revenge_trading' in insights['common_patterns']:
        insights['caution'] = "You've revenge traded this before. Stay calm."
    
    return insights