"""
BITTEN Norman's Story Integration Module
Comprehensive integration of Norman's Mississippi journey into mission briefings and system personas
"""

import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class StoryPhase(Enum):
    """Norman's journey phases that users discover progressively"""
    EARLY_STRUGGLE = "early_struggle"      # Learning basics, making mistakes
    AWAKENING = "awakening"                # First successes, understanding markets
    DISCIPLINE = "discipline"              # Building systems, controlling emotions
    MASTERY = "mastery"                    # Consistent profits, helping others
    LEGACY = "legacy"                      # Full story revealed, community building

@dataclass
class NormanStoryContext:
    """Context about user's progression through Norman's story"""
    user_id: str
    current_phase: StoryPhase
    days_active: int
    total_trades: int
    win_rate: float
    story_elements_revealed: List[str]
    bit_encounters: int
    family_wisdom_heard: List[str]

class NormanStoryEngine:
    """Main engine for integrating Norman's story throughout the system"""
    
    def __init__(self):
        self.story_database = self._initialize_story_database()
        self.user_contexts: Dict[str, NormanStoryContext] = {}
        
    def _initialize_story_database(self) -> Dict[str, Any]:
        """Initialize the complete Norman story database"""
        return {
            'family_backstory': {
                'grandmother': {
                    'wisdom_phrases': [
                        "Patience is worth more than gold, child",
                        "Good things come to those who wait for the right season",
                        "The storm passes, but the oak remembers how to bend",
                        "Never bet the farm on a maybe",
                        "Slow and steady wins the race, but smart and steady wins the war"
                    ],
                    'memories': [
                        "Grandmama on the front porch, teaching patience through her stories",
                        "Her weathered hands counting change, showing the value of every penny",
                        "Sunday mornings listening to wisdom older than the Delta itself",
                        "The way she could predict weather - and trouble - before it arrived"
                    ]
                },
                'mother': {
                    'wisdom_phrases': [
                        "Protect what you have before you reach for more",
                        "Every dollar saved is a dollar earned through sacrifice",
                        "Don't put all your eggs in one basket, baby",
                        "Know when to hold on and when to let go",
                        "Your family needs you more than any gamble ever will"
                    ],
                    'memories': [
                        "Mama working two jobs, never complaining, always providing",
                        "Her sacrifice to keep the family together when daddy left",
                        "The strength in her eyes when she said 'We'll make it through'",
                        "Teaching Norman that love means protection, not just provision"
                    ]
                },
                'father_absence': {
                    'lessons': [
                        "Some paths are better walked alone than with the wrong guide",
                        "A man's worth isn't in his promises, but in what he protects",
                        "Sometimes the best lesson is learning what not to become",
                        "Independence earned through necessity becomes unshakeable strength"
                    ],
                    'impacts': [
                        "Learning to trust himself when no one else was there",
                        "Understanding that discipline comes from within, not from others",
                        "The drive to become the man his family needed",
                        "Why helping others became more important than helping himself"
                    ]
                }
            },
            'bit_companion': {
                'arrival_story': "Bit showed up during Norman's hardest night - portfolio blown, dreams shattered. Just appeared on the windowsill like he'd been sent.",
                'personality_traits': [
                    "Uncanny ability to sense market opportunities before they manifest",
                    "Appears during moments of doubt to provide silent comfort",
                    "Tail twitches when danger approaches - taught Norman to trust instincts",
                    "Purrs during winning streaks, goes quiet before major losses",
                    "Independent but loyal - mirrors Norman's own journey"
                ],
                'special_moments': [
                    "The night Bit first purred - Norman's first profitable week",
                    "Warning signs: ears back before the 2018 flash crash Norman avoided",
                    "Victory stretches after each milestone Norman achieved",
                    "The way Bit settles during tough lessons - patience incarnate"
                ]
            },
            'mississippi_culture': {
                'delta_wisdom': [
                    "Like the Delta floods, markets rise and fall with natural rhythm",
                    "Cotton season teaches timing - you can't rush what needs to ripen",
                    "Southern storms build slow but hit hard - watch for the signs",
                    "Community matters more than individual success",
                    "Hard work beats talent when talent doesn't work hard"
                ],
                'regional_values': [
                    "Your word is your bond - honor your stops and targets",
                    "Help your neighbor's harvest before celebrating your own",
                    "Respect the land (market) and it will provide",
                    "Weather the storms together, celebrate the sunshine as one",
                    "Every ending is a new beginning if you're brave enough to plant again"
                ],
                'cultural_metaphors': {
                    'farming': [
                        "You don't plant corn and expect cotton overnight",
                        "Good farmers diversify crops, smart traders diversify positions",
                        "Harvest comes to those who tend their fields daily",
                        "Even the best soil needs rest between seasons"
                    ],
                    'weather': [
                        "Calm before the storm often precedes the biggest moves",
                        "Spring rains bring growth if you've prepared the ground",
                        "Winter teaches conservation, summer teaches abundance",
                        "Smart folks take shelter when the wind changes direction"
                    ],
                    'community': [
                        "Rising water lifts all boats in the harbor",
                        "Strong fences make good neighbors, strong traders make good communities",
                        "Share the knowledge, multiply the success",
                        "No one succeeds alone in the Delta, no one should trade alone either"
                    ]
                }
            },
            'trading_journey': {
                'early_mistakes': [
                    "The FOMO trade that cost two months of savings - learned patience the hard way",
                    "Revenge trading after a bad loss - emotion became the enemy",
                    "Over-leveraging because 'this one was different' - hubris meets reality",
                    "Following hot tips instead of doing homework - dependency vs independence",
                    "Ignoring risk management because 'I was on a roll' - pride before the fall"
                ],
                'breakthrough_moments': [
                    "First month of consistent profits - discipline finally clicked",
                    "Avoiding a major market crash by trusting the system over emotions",
                    "The trade that paid off Mama's medical bills - purpose crystallized",
                    "Teaching his first student and seeing them succeed - legacy began",
                    "Realizing he'd become the trader his family needed him to be"
                ],
                'philosophy_evolution': [
                    "From 'get rich quick' to 'get right first'",
                    "From individual success to community elevation",
                    "From following others to trusting his own analysis",
                    "From chasing profits to managing risks",
                    "From trading for himself to trading for something bigger"
                ]
            }
        }
    
    def get_user_story_context(self, user_id: str) -> NormanStoryContext:
        """Get or create user's story context"""
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = NormanStoryContext(
                user_id=user_id,
                current_phase=StoryPhase.EARLY_STRUGGLE,
                days_active=0,
                total_trades=0,
                win_rate=0.0,
                story_elements_revealed=[],
                bit_encounters=0,
                family_wisdom_heard=[]
            )
        return self.user_contexts[user_id]
    
    def update_user_progress(self, user_id: str, trading_data: Dict) -> None:
        """Update user's progress through Norman's story based on trading activity"""
        context = self.get_user_story_context(user_id)
        
        # Update basic stats
        context.days_active = trading_data.get('days_active', 0)
        context.total_trades = trading_data.get('total_trades', 0)
        context.win_rate = trading_data.get('win_rate', 0.0)
        
        # Determine story phase progression
        old_phase = context.current_phase
        new_phase = self._determine_story_phase(context, trading_data)
        
        if new_phase != old_phase:
            context.current_phase = new_phase
            self._trigger_phase_transition(user_id, old_phase, new_phase)
    
    def _determine_story_phase(self, context: NormanStoryContext, trading_data: Dict) -> StoryPhase:
        """Determine user's current phase in Norman's journey"""
        days = context.days_active
        trades = context.total_trades
        win_rate = context.win_rate
        
        if days < 30 or trades < 50:
            return StoryPhase.EARLY_STRUGGLE
        elif days < 90 or win_rate < 0.6:
            return StoryPhase.AWAKENING
        elif days < 180 or win_rate < 0.7:
            return StoryPhase.DISCIPLINE
        elif days < 365 or win_rate < 0.75:
            return StoryPhase.MASTERY
        else:
            return StoryPhase.LEGACY
    
    def _trigger_phase_transition(self, user_id: str, old_phase: StoryPhase, new_phase: StoryPhase) -> None:
        """Handle user's transition to new story phase"""
        transition_messages = {
            StoryPhase.AWAKENING: "Something's changing. The patterns are starting to make sense, like Norman's first breakthrough.",
            StoryPhase.DISCIPLINE: "You're building something here. Norman would recognize this growth.",
            StoryPhase.MASTERY: "The student becomes the teacher. Norman's vision lives through traders like you.",
            StoryPhase.LEGACY: "You've walked Norman's path and made it your own. Time to help others find theirs."
        }
        
        message = transition_messages.get(new_phase)
        if message:
            # This would trigger a special notification or mission briefing
            self._queue_story_revelation(user_id, new_phase, message)
    
    def _queue_story_revelation(self, user_id: str, phase: StoryPhase, message: str) -> None:
        """Queue a special story revelation for the user"""
        # Implementation would depend on notification system
        pass
    
    def get_contextual_wisdom(self, situation: str, user_id: str) -> Optional[str]:
        """Get appropriate Norman/family wisdom for current situation"""
        context = self.get_user_story_context(user_id)
        phase = context.current_phase
        
        wisdom_map = {
            'loss': {
                StoryPhase.EARLY_STRUGGLE: self.story_database['family_backstory']['grandmother']['wisdom_phrases'],
                StoryPhase.AWAKENING: self.story_database['family_backstory']['mother']['wisdom_phrases'],
                StoryPhase.DISCIPLINE: self.story_database['trading_journey']['philosophy_evolution'],
                StoryPhase.MASTERY: self.story_database['mississippi_culture']['delta_wisdom'],
                StoryPhase.LEGACY: self.story_database['trading_journey']['breakthrough_moments']
            },
            'risk_warning': {
                StoryPhase.EARLY_STRUGGLE: self.story_database['family_backstory']['mother']['wisdom_phrases'],
                StoryPhase.AWAKENING: self.story_database['trading_journey']['early_mistakes'],
                StoryPhase.DISCIPLINE: self.story_database['mississippi_culture']['cultural_metaphors']['weather'],
                StoryPhase.MASTERY: self.story_database['family_backstory']['father_absence']['lessons'],
                StoryPhase.LEGACY: self.story_database['mississippi_culture']['regional_values']
            },
            'success': {
                StoryPhase.EARLY_STRUGGLE: ["Every small win builds toward something bigger"],
                StoryPhase.AWAKENING: self.story_database['trading_journey']['breakthrough_moments'],
                StoryPhase.DISCIPLINE: self.story_database['mississippi_culture']['delta_wisdom'],
                StoryPhase.MASTERY: self.story_database['mississippi_culture']['regional_values'],
                StoryPhase.LEGACY: self.story_database['mississippi_culture']['cultural_metaphors']['community']
            }
        }
        
        appropriate_wisdom = wisdom_map.get(situation, {}).get(phase, [])
        if appropriate_wisdom:
            wisdom = random.choice(appropriate_wisdom)
            # Track what wisdom this user has heard
            if wisdom not in context.family_wisdom_heard:
                context.family_wisdom_heard.append(wisdom)
            return wisdom
        
        return None
    
    def get_bit_interaction(self, event_type: str, user_id: str) -> Optional[Dict[str, str]]:
        """Get appropriate Bit interaction for the event"""
        context = self.get_user_story_context(user_id)
        context.bit_encounters += 1
        
        bit_interactions = {
            'loss': {
                'message': "*Bit settles beside you, purring softly like he did during Norman's hardest nights*",
                'visual': 'cat_comfort_curl',
                'audio': 'comforting_purr'
            },
            'big_win': {
                'message': "*Bit does his victory stretch - the same one after Norman's first profitable month*",
                'visual': 'cat_victory_stretch',
                'audio': 'satisfied_purr'
            },
            'risk_warning': {
                'message': "*Bit's ears flatten - he always sensed danger before Norman did*",
                'visual': 'cat_ears_back_warning',
                'audio': 'warning_chirp'
            },
            'patience_needed': {
                'message': "*Bit demonstrates perfect cat patience - wait for the right moment*",
                'visual': 'cat_patient_sitting',
                'audio': 'rhythmic_purr'
            }
        }
        
        return bit_interactions.get(event_type)
    
    def enhance_mission_briefing(self, briefing_data: Dict, user_id: str) -> Dict:
        """Enhance mission briefing with Norman's story elements"""
        context = self.get_user_story_context(user_id)
        enhanced_briefing = briefing_data.copy()
        
        # Add phase-appropriate story elements
        if context.current_phase in [StoryPhase.EARLY_STRUGGLE, StoryPhase.AWAKENING]:
            # Add learning-focused elements
            enhanced_briefing['wisdom_note'] = self.get_contextual_wisdom('learning', user_id)
            enhanced_briefing['encouragement'] = "Every master was once a beginner. Norman's journey started just like this."
        
        elif context.current_phase in [StoryPhase.DISCIPLINE, StoryPhase.MASTERY]:
            # Add discipline and mastery elements
            enhanced_briefing['wisdom_note'] = self.get_contextual_wisdom('discipline', user_id)
            enhanced_briefing['regional_touch'] = random.choice(self.story_database['mississippi_culture']['delta_wisdom'])
        
        elif context.current_phase == StoryPhase.LEGACY:
            # Add community building elements
            enhanced_briefing['wisdom_note'] = self.get_contextual_wisdom('legacy', user_id)
            enhanced_briefing['community_message'] = "Your success lifts others. Norman's vision lives through traders like you."
        
        # Add Bit's presence
        bit_interaction = self.get_bit_interaction('mission_start', user_id)
        if bit_interaction:
            enhanced_briefing['bit_presence'] = bit_interaction
        
        # Add cultural flavor
        enhanced_briefing['cultural_element'] = random.choice(
            self.story_database['mississippi_culture']['cultural_metaphors']['farming'] +
            self.story_database['mississippi_culture']['cultural_metaphors']['weather']
        )
        
        return enhanced_briefing
    
    def get_callsign_with_story(self, base_callsign: str, user_id: str) -> str:
        """Enhance callsign with Norman's story context"""
        context = self.get_user_story_context(user_id)
        
        story_suffixes = {
            StoryPhase.EARLY_STRUGGLE: [" - Learning", " - First Steps", " - Building"],
            StoryPhase.AWAKENING: [" - Rising", " - Delta Dawn", " - Breakthrough"],
            StoryPhase.DISCIPLINE: [" - Steady", " - Mississippi Strong", " - Disciplined"],
            StoryPhase.MASTERY: [" - Expert", " - Delta Pride", " - Master Class"],
            StoryPhase.LEGACY: [" - Legend", " - Norman's Legacy", " - Community Builder"]
        }
        
        if random.random() < 0.15:  # 15% chance for story enhancement
            suffixes = story_suffixes.get(context.current_phase, [])
            if suffixes:
                return base_callsign + random.choice(suffixes)
        
        return base_callsign

# Global instance for easy access
norman_story_engine = NormanStoryEngine()

def integrate_norman_story(briefing_data: Dict, user_id: str, trading_context: Dict) -> Dict:
    """Main function to integrate Norman's story into any system component"""
    
    # Update user progress through story
    norman_story_engine.update_user_progress(user_id, trading_context)
    
    # Enhance the briefing with story elements
    enhanced_briefing = norman_story_engine.enhance_mission_briefing(briefing_data, user_id)
    
    return enhanced_briefing

def get_story_appropriate_response(event_type: str, user_id: str, context: Dict) -> Optional[str]:
    """Get story-appropriate response for any event"""
    return norman_story_engine.get_contextual_wisdom(event_type, user_id)

def get_user_story_phase(user_id: str) -> StoryPhase:
    """Get user's current phase in Norman's journey"""
    context = norman_story_engine.get_user_story_context(user_id)
    return context.current_phase