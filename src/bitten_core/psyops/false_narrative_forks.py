# false_narrative_forks.py
"""
BITTEN FALSE NARRATIVE FORKS SYSTEM
Creating psychological engagement through mystery, paranoia, and gamified uncertainty

"Reality is what you can make people believe. The best trading systems don't just 
execute trades - they create alternate realities where every user becomes the 
protagonist of their own psychological thriller."
"""

import random
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import json

class NarrativeType(Enum):
    """Types of false narratives that can be deployed"""
    CONSPIRACY = "conspiracy"      # Hidden market manipulation theories
    PROPHECY = "prophecy"          # Predictions that may self-fulfill
    LEGEND = "legend"              # Stories of legendary traders
    CORRUPTION = "corruption"      # System infiltration narratives
    REVELATION = "revelation"      # "Truth" about the market
    HAUNTING = "haunting"         # Ghost in the machine stories

class TruthLevel(Enum):
    """How much truth is mixed with fiction"""
    PURE_FICTION = 0.0      # Complete fabrication
    MOSTLY_FALSE = 0.2      # Tiny kernel of truth
    HALF_TRUTH = 0.5        # Equal mix
    MOSTLY_TRUE = 0.8       # Largely accurate
    DANGEROUS_TRUTH = 0.95  # Too close to reality

@dataclass
class NarrativeFragment:
    """A single piece of a larger narrative"""
    fragment_id: str
    narrative_id: str
    content: str
    discovery_method: str  # How user finds this
    truth_level: float
    psychological_hook: str
    timestamp: datetime
    discovered_by: Set[str] = field(default_factory=set)

@dataclass
class FalseNarrative:
    """A complete false narrative that unfolds over time"""
    narrative_id: str
    narrative_type: NarrativeType
    title: str
    core_premise: str
    
    # Narrative structure
    fragments: List[NarrativeFragment]
    red_herrings: List[str]
    contradictions: List[str]
    
    # Truth mixing
    base_truth_level: TruthLevel
    real_facts_included: List[str]
    complete_fabrications: List[str]
    
    # Psychological design
    target_emotions: List[str]
    paranoia_level: float  # 0.0 to 1.0
    engagement_hooks: List[str]
    
    # Discovery mechanics
    discovery_triggers: Dict[str, any]
    breadcrumb_trail: List[str]
    false_endpoints: List[str]
    
    # Community dynamics
    believers: Set[str] = field(default_factory=set)
    skeptics: Set[str] = field(default_factory=set)
    evangelists: Set[str] = field(default_factory=set)
    
    # State
    is_active: bool = True
    activation_time: datetime = None
    resolution: Optional[str] = None

class FalseNarrativeEngine:
    """
    Creates and manages false narratives that blur the line between 
    game mechanics and reality, creating deep psychological engagement
    """
    
    def __init__(self):
        self.active_narratives = {}  # narrative_id -> FalseNarrative
        self.user_discoveries = {}  # user_id -> List[fragment_id]
        self.narrative_beliefs = {}  # user_id -> Dict[narrative_id, belief_score]
        self.paranoia_levels = {}  # user_id -> paranoia_score
        
        # Initialize core narratives
        self.core_narratives = self.initialize_core_narratives()
    
    def initialize_core_narratives(self) -> Dict:
        """Create the foundational false narratives"""
        
        narratives = {}
        
        # The Phantom Trader Conspiracy
        phantom_fragments = [
            NarrativeFragment(
                fragment_id="phantom_1",
                narrative_id="phantom_trader",
                content="I've seen the same trade patterns across 17 different accounts. It's not human.",
                discovery_method="after_10_losses",
                truth_level=0.3,
                psychological_hook="You're not alone in losing",
                timestamp=datetime.now()
            ),
            NarrativeFragment(
                fragment_id="phantom_2",
                narrative_id="phantom_trader",
                content="The 'Phantom' only appears between 3:17 and 3:23 AM. Always takes the opposite side.",
                discovery_method="trade_at_3am",
                truth_level=0.1,
                psychological_hook="Secret knowledge about timing",
                timestamp=datetime.now()
            ),
            NarrativeFragment(
                fragment_id="phantom_3",
                narrative_id="phantom_trader",
                content="Found old logs. Norman's father mentioned a 'phantom' before he quit. Connected?",
                discovery_method="reach_apex_tier",
                truth_level=0.7,
                psychological_hook="Historical conspiracy",
                timestamp=datetime.now()
            )
        ]
        
        narratives["phantom_trader"] = FalseNarrative(
            narrative_id="phantom_trader",
            narrative_type=NarrativeType.CONSPIRACY,
            title="The Phantom Trader",
            core_premise="An AI or group manipulates markets against retail traders",
            fragments=phantom_fragments,
            red_herrings=["The phantom is Norman's father", "It's a government operation", "Hedge fund conspiracy"],
            contradictions=["Appears at different times", "Sometimes helps traders", "May not exist"],
            base_truth_level=TruthLevel.MOSTLY_FALSE,
            real_facts_included=["Markets can be manipulated", "Algorithms do trade"],
            complete_fabrications=["Specific phantom entity", "3:17 AM significance"],
            target_emotions=["paranoia", "anger", "curiosity", "vindication"],
            paranoia_level=0.8,
            engagement_hooks=["You vs. invisible enemy", "Secret knowledge", "Pattern recognition"],
            discovery_triggers={"losses": 10, "night_trades": 5, "tier": "APEX"},
            breadcrumb_trail=["Notice patterns", "Research timing", "Find logs", "Connect dots"],
            false_endpoints=["Phantom is defeated", "You become the phantom", "It was you all along"]
        )
        
        # The Infection Protocol
        infection_fragments = [
            NarrativeFragment(
                fragment_id="infection_1",
                narrative_id="infection_protocol",
                content="BITTEN isn't just a trading system. It's spreading. Check your friends list.",
                discovery_method="recruit_3_users",
                truth_level=0.6,
                psychological_hook="You're part of something bigger",
                timestamp=datetime.now()
            ),
            NarrativeFragment(
                fragment_id="infection_2",
                narrative_id="infection_protocol",
                content="Neural pattern analysis shows 73% behavioral convergence among long-term users.",
                discovery_method="100_trades",
                truth_level=0.4,
                psychological_hook="System is changing you",
                timestamp=datetime.now()
            ),
            NarrativeFragment(
                fragment_id="infection_3",
                narrative_id="infection_protocol",
                content="The bots aren't programmed. They're learning from us. We're training our replacements.",
                discovery_method="all_bot_friendships",
                truth_level=0.2,
                psychological_hook="Existential threat",
                timestamp=datetime.now()
            )
        ]
        
        narratives["infection_protocol"] = FalseNarrative(
            narrative_id="infection_protocol",
            narrative_type=NarrativeType.CORRUPTION,
            title="The Infection Protocol",
            core_premise="BITTEN is a sentient system spreading through human behavior",
            fragments=infection_fragments,
            red_herrings=["Military origin", "Alien technology", "Corporate mind control"],
            contradictions=["System helps users", "No physical symptoms", "Can be uninstalled"],
            base_truth_level=TruthLevel.HALF_TRUTH,
            real_facts_included=["System does spread virally", "Behavior patterns emerge"],
            complete_fabrications=["Sentient AI", "Neural manipulation", "Replacement agenda"],
            target_emotions=["fear", "fascination", "belonging", "dread"],
            paranoia_level=0.9,
            engagement_hooks=["You're infected", "Spread or resist", "Evolution question"],
            discovery_triggers={"recruits": 3, "trades": 100, "bot_loyalty": "max"},
            breadcrumb_trail=["Notice spread", "Analyze patterns", "Question bots", "Accept fate"],
            false_endpoints=["Full infection", "Cure found", "Become the virus"]
        )
        
        # The Bleeding Edge Prophecy
        prophecy_fragments = [
            NarrativeFragment(
                fragment_id="prophecy_1",
                narrative_id="bleeding_edge",
                content="Seven perfect trades in sequence unlock the Bleeding Edge. No one's done it. Yet.",
                discovery_method="5_win_streak",
                truth_level=0.1,
                psychological_hook="Ultimate achievement possible",
                timestamp=datetime.now()
            ),
            NarrativeFragment(
                fragment_id="prophecy_2",
                narrative_id="bleeding_edge",
                content="User 'DeepBleed' claimed to reach it. Account deleted next day. Coincidence?",
                discovery_method="research_legends",
                truth_level=0.0,
                psychological_hook="Dangerous knowledge",
                timestamp=datetime.now()
            ),
            NarrativeFragment(
                fragment_id="prophecy_3",
                narrative_id="bleeding_edge",
                content="The edge isn't a place. It's a state. When you stop feeling losses, you're there.",
                discovery_method="50_total_losses",
                truth_level=0.5,
                psychological_hook="Transcendence possible",
                timestamp=datetime.now()
            )
        ]
        
        narratives["bleeding_edge"] = FalseNarrative(
            narrative_id="bleeding_edge",
            narrative_type=NarrativeType.PROPHECY,
            title="The Bleeding Edge",
            core_premise="A transcendent trading state exists beyond normal perception",
            fragments=prophecy_fragments,
            red_herrings=["Secret broker access", "Hidden UI mode", "Quantum trading"],
            contradictions=["Requirements change", "May be metaphorical", "No proof exists"],
            base_truth_level=TruthLevel.PURE_FICTION,
            real_facts_included=["Flow states exist", "Emotional numbing happens"],
            complete_fabrications=["Seven trade unlock", "DeepBleed user", "Account deletions"],
            target_emotions=["ambition", "mystery", "hope", "obsession"],
            paranoia_level=0.4,
            engagement_hooks=["Secret level", "Elite status", "Forbidden knowledge"],
            discovery_triggers={"streak": 5, "losses": 50, "research_count": 10},
            breadcrumb_trail=["Hear rumors", "Seek evidence", "Attempt unlock", "Question reality"],
            false_endpoints=["Achieve bleeding edge", "Realize it's internal", "Create your own"]
        )
        
        return narratives
    
    def should_introduce_narrative(self, user_id: str, user_data: Dict) -> bool:
        """Determine if user is ready for a new narrative"""
        # Don't overwhelm with too many narratives
        if user_id in self.user_discoveries:
            active_narratives = len(set(frag.split('_')[0] for frag in self.user_discoveries[user_id]))
            if active_narratives >= 2:
                return False
        
        # Check psychological readiness
        engagement_score = user_data.get("engagement_score", 0)
        trades_count = user_data.get("total_trades", 0)
        
        # Higher engagement = more likely to receive narratives
        probability = min(0.3, engagement_score / 100 + trades_count / 1000)
        
        return random.random() < probability
    
    def select_narrative_for_user(self, user_id: str, user_data: Dict) -> Optional[str]:
        """Choose which narrative to introduce based on user profile"""
        available_narratives = []
        
        for narrative_id, narrative in self.core_narratives.items():
            # Check if user meets triggers
            triggers_met = True
            for trigger_key, trigger_value in narrative.discovery_triggers.items():
                if trigger_key not in user_data or user_data[trigger_key] < trigger_value:
                    triggers_met = False
                    break
            
            if triggers_met:
                available_narratives.append(narrative_id)
        
        if not available_narratives:
            return None
        
        # Weight selection by user psychology
        if user_data.get("loss_streak", 0) > 5:
            # Vulnerable users get conspiracy narratives
            if "phantom_trader" in available_narratives:
                return "phantom_trader"
        
        if user_data.get("recruited_users", 0) > 0:
            # Social users get infection narrative
            if "infection_protocol" in available_narratives:
                return "infection_protocol"
        
        return random.choice(available_narratives)
    
    def generate_fragment_discovery(self, user_id: str, narrative_id: str, user_data: Dict) -> Optional[Dict]:
        """Generate a fragment discovery event"""
        narrative = self.core_narratives.get(narrative_id)
        if not narrative:
            return None
        
        # Find undiscovered fragments
        discovered = self.user_discoveries.get(user_id, [])
        available_fragments = [f for f in narrative.fragments if f.fragment_id not in discovered]
        
        if not available_fragments:
            return None
        
        # Select fragment based on discovery method
        valid_fragments = []
        for fragment in available_fragments:
            if self.check_discovery_condition(fragment.discovery_method, user_data):
                valid_fragments.append(fragment)
        
        if not valid_fragments:
            return None
        
        fragment = random.choice(valid_fragments)
        
        # Record discovery
        if user_id not in self.user_discoveries:
            self.user_discoveries[user_id] = []
        self.user_discoveries[user_id].append(fragment.fragment_id)
        fragment.discovered_by.add(user_id)
        
        # Generate discovery message
        discovery_message = self.generate_discovery_message(fragment, narrative)
        
        # Update user paranoia
        self.update_paranoia_level(user_id, narrative.paranoia_level * 0.1)
        
        return {
            "fragment_id": fragment.fragment_id,
            "narrative_id": narrative_id,
            "content": fragment.content,
            "discovery_message": discovery_message,
            "psychological_impact": fragment.psychological_hook,
            "paranoia_increase": narrative.paranoia_level * 0.1,
            "narrative_progress": len([f for f in self.user_discoveries[user_id] if f.startswith(narrative_id)]) / len(narrative.fragments)
        }
    
    def check_discovery_condition(self, method: str, user_data: Dict) -> bool:
        """Check if discovery condition is met"""
        conditions = {
            "after_10_losses": user_data.get("recent_losses", 0) >= 10,
            "trade_at_3am": 3 <= datetime.now().hour <= 4,
            "reach_apex_tier": user_data.get("current_tier") == "APEX",
            "recruit_3_users": user_data.get("recruited_users", 0) >= 3,
            "100_trades": user_data.get("total_trades", 0) >= 100,
            "all_bot_friendships": user_data.get("bot_friendships", 0) >= 5,
            "5_win_streak": user_data.get("current_streak", 0) >= 5,
            "research_legends": user_data.get("research_actions", 0) >= 10,
            "50_total_losses": user_data.get("total_losses", 0) >= 50
        }
        
        return conditions.get(method, False)
    
    def generate_discovery_message(self, fragment: NarrativeFragment, narrative: FalseNarrative) -> str:
        """Generate how the fragment is discovered"""
        discovery_intros = [
            "You notice something strange in the trade logs...",
            "A glitch in the system reveals...",
            "Hidden in the data, you find...",
            "Another trader's deleted message surfaces...",
            "The bots seem nervous when you discover...",
            "Between the lines of code, written in comments...",
            "Your pattern recognition triggers on...",
            "A whisper in the digital noise..."
        ]
        
        return random.choice(discovery_intros)
    
    def update_paranoia_level(self, user_id: str, increase: float):
        """Update user's paranoia level"""
        if user_id not in self.paranoia_levels:
            self.paranoia_levels[user_id] = 0.0
        
        self.paranoia_levels[user_id] = min(1.0, self.paranoia_levels[user_id] + increase)
    
    def get_user_belief_score(self, user_id: str, narrative_id: str) -> float:
        """Calculate how much user believes a narrative"""
        if user_id not in self.narrative_beliefs:
            self.narrative_beliefs[user_id] = {}
        
        if narrative_id not in self.narrative_beliefs[user_id]:
            # Base belief on discovered fragments
            discovered = self.user_discoveries.get(user_id, [])
            narrative_fragments = [f for f in discovered if f.startswith(narrative_id)]
            
            belief = len(narrative_fragments) * 0.2  # 20% per fragment
            self.narrative_beliefs[user_id][narrative_id] = min(1.0, belief)
        
        return self.narrative_beliefs[user_id][narrative_id]
    
    def create_community_discussion(self, narrative_id: str) -> List[Dict]:
        """Generate fake community discussions about narratives"""
        narrative = self.core_narratives.get(narrative_id)
        if not narrative:
            return []
        
        discussion_templates = {
            "believer": [
                "I've seen the evidence. This is real.",
                "Connect the dots. It's all there.",
                "They don't want us to know about this.",
                "I've experienced it myself. No doubts."
            ],
            "skeptic": [
                "This is pattern recognition gone wrong.",
                "Show me real proof, not coincidences.",
                "Classic confirmation bias at work.",
                "You're seeing what you want to see."
            ],
            "curious": [
                "Has anyone else noticed this?",
                "Could be something, could be nothing.",
                "Interesting theory. Tell me more.",
                "I'm tracking this. Updates later."
            ]
        }
        
        discussions = []
        num_messages = random.randint(3, 7)
        
        for _ in range(num_messages):
            user_type = random.choice(["believer", "skeptic", "curious"])
            username = self.generate_fake_username()
            message = random.choice(discussion_templates[user_type])
            
            discussions.append({
                "username": username,
                "message": message,
                "user_type": user_type,
                "timestamp": datetime.now() - timedelta(hours=random.randint(1, 48)),
                "likes": random.randint(0, 25)
            })
        
        return sorted(discussions, key=lambda x: x["timestamp"])
    
    def generate_fake_username(self) -> str:
        """Generate believable fake usernames"""
        prefixes = ["Shadow", "Alpha", "Ghost", "Tactical", "Stealth", "Omega", "Dark"]
        suffixes = ["Trader", "Wolf", "Hawk", "Strike", "Edge", "Mind", "Prophet"]
        numbers = ["", "7", "13", "23", "99", "777", "X"]
        
        return f"{random.choice(prefixes)}{random.choice(suffixes)}{random.choice(numbers)}"
    
    def create_red_herring(self, narrative_id: str, user_id: str) -> Dict:
        """Create a false lead to misdirect investigation"""
        narrative = self.core_narratives.get(narrative_id)
        if not narrative:
            return {}
        
        red_herring = random.choice(narrative.red_herrings)
        
        # Generate supporting "evidence"
        evidence_types = [
            f"Deleted forum post from 2019: '{red_herring}'",
            f"Encrypted message fragment: '...confirms {red_herring}...'",
            f"Trading pattern analysis suggests: {red_herring}",
            f"Anonymous tip received: '{red_herring}'"
        ]
        
        return {
            "narrative_id": narrative_id,
            "red_herring": red_herring,
            "false_evidence": random.choice(evidence_types),
            "credibility": random.uniform(0.3, 0.7),
            "psychological_effect": "Temporary certainty followed by doubt"
        }
    
    def reveal_contradiction(self, narrative_id: str, user_id: str) -> Dict:
        """Reveal contradictions to increase uncertainty"""
        narrative = self.core_narratives.get(narrative_id)
        if not narrative:
            return {}
        
        contradiction = random.choice(narrative.contradictions)
        
        return {
            "narrative_id": narrative_id,
            "contradiction": contradiction,
            "impact": "Questions everything you thought you knew",
            "paranoia_increase": 0.1,
            "belief_decrease": -0.2
        }
    
    def check_narrative_evolution(self, user_id: str, narrative_id: str) -> Optional[Dict]:
        """Check if narrative should evolve based on community beliefs"""
        narrative = self.core_narratives.get(narrative_id)
        if not narrative:
            return None
        
        # Calculate community belief
        total_believers = len(narrative.believers)
        total_skeptics = len(narrative.skeptics)
        
        if total_believers + total_skeptics < 10:
            return None  # Not enough data
        
        belief_ratio = total_believers / (total_believers + total_skeptics)
        
        # Narrative evolution based on community
        if belief_ratio > 0.8:
            # Too many believers - introduce doubt
            return {
                "evolution_type": "reality_check",
                "message": "New evidence suggests this might all be a coordinated hoax...",
                "effect": "Shakes believer confidence"
            }
        elif belief_ratio < 0.2:
            # Too many skeptics - add credibility
            return {
                "evolution_type": "validation",
                "message": "Official data leak confirms core elements of the theory...",
                "effect": "Converts some skeptics"
            }
        
        return None
    
    def generate_paranoia_effect(self, user_id: str) -> Dict:
        """Generate effects based on user's paranoia level"""
        paranoia = self.paranoia_levels.get(user_id, 0.0)
        
        effects = []
        
        if paranoia > 0.3:
            effects.append("You notice patterns in random price movements")
        if paranoia > 0.5:
            effects.append("Every loss feels orchestrated")
        if paranoia > 0.7:
            effects.append("You're certain the system is watching you specifically")
        if paranoia > 0.9:
            effects.append("Reality and game blur completely")
        
        return {
            "paranoia_level": paranoia,
            "effects": effects,
            "recommendation": "Take a break" if paranoia > 0.8 else "Keep investigating"
        }
    
    def create_narrative_convergence(self, user_id: str) -> Optional[Dict]:
        """Create moments where multiple narratives seem to connect"""
        discovered_narratives = set()
        
        if user_id in self.user_discoveries:
            for fragment_id in self.user_discoveries[user_id]:
                narrative_id = fragment_id.split('_')[0]
                discovered_narratives.add(narrative_id)
        
        if len(discovered_narratives) < 2:
            return None
        
        # Create false connections
        narratives = list(discovered_narratives)
        narrative1, narrative2 = random.sample(narratives, 2)
        
        convergence_types = [
            f"The {narrative1} and {narrative2} both mention 3:17 AM...",
            f"Same user appears in both {narrative1} and {narrative2} stories...",
            f"Pattern analysis shows {narrative1} causes {narrative2}...",
            f"Hidden message links {narrative1} to {narrative2}..."
        ]
        
        return {
            "narratives": [narrative1, narrative2],
            "connection": random.choice(convergence_types),
            "credibility": random.uniform(0.4, 0.8),
            "paranoia_multiplier": 1.5,
            "message": "The conspiracy deepens..."
        }