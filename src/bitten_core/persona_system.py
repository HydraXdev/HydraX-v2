"""
BITTEN Persona System
Implements the character voices and personalities throughout the trading system
Based on the comprehensive persona buildout v2.0
"""

import random
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

# Import Norman's story elements
try:
    from .mission_briefing_generator import NormansStoryIntegrator
except ImportError:
    # Fallback if import fails
    class NormansStoryIntegrator:
        def __init__(self):
            self.family_wisdom = {'grandmother': [], 'mother': [], 'work_ethic': []}
            self.cultural_elements = {'weather_metaphors': [], 'farming_wisdom': [], 'community_values': []}

logger = logging.getLogger(__name__)

class PersonaType(Enum):
    """The five core BITTEN personas"""
    DRILL = "drill"
    DOC = "doc"  # Captain Aegis
    NEXUS = "nexus"  # Sergeant Nexus
    OVERWATCH = "overwatch"
    BIT = "bit"  # The cat's presence

class EmotionalState(Enum):
    """User emotional states detected by the system"""
    CALM = "calm"
    FOCUSED = "focused"
    STRESSED = "stressed"
    IMPULSIVE = "impulsive"
    DEFEATED = "defeated"
    EUPHORIC = "euphoric"
    LEARNING = "learning"

class MarketSentiment(Enum):
    """Market sentiment states for Overwatch"""
    FEARFUL = "fearful"
    GREEDY = "greedy"
    EUPHORIC = "euphoric"
    COMPLACENT = "complacent"
    CHAOTIC = "chaotic"
    RATIONAL = "rational"

@dataclass
class PersonaResponse:
    """A response from a persona"""
    persona: PersonaType
    message: str
    visual_cue: Optional[str] = None
    audio_cue: Optional[str] = None
    action_required: Optional[str] = None

class DrillPersona:
    """
    The Drill Sergeant - Discipline and Execution
    Origin: Norman's father's failures + need for emotional control
    Enhanced with Norman's Mississippi discipline and family work ethic
    """
    
    def __init__(self):
        self.norman_story = NormansStoryIntegrator()
        self.voice_lines = {
            'error_emotional': [
                "ERROR. EMOTIONAL IMPULSE DETECTED. RECALIBRATE. REFER TO RULES.",
                "WEAKNESS IDENTIFIED. EMOTION OVERRIDING LOGIC. ABORT CURRENT ACTION.",
                "DISCIPLINE BREACH. REALIGN WITH PROTOCOL. NOW.",
                "YOUR FEELINGS ARE IRRELEVANT. EXECUTE THE PLAN.",
                "SOLDIER! Grandmama didn't raise no quitters. GET BACK IN LINE.",
                "Delta discipline, recruit! We don't chase losses down here.",
                "Mississippi strong means Mississippi smart. THINK BEFORE YOU ACT."
            ],
            'execution_optimal': [
                "EXECUTION: OPTIMAL. PATTERN RECOGNITION: CONFIRMED. REPEAT CYCLE.",
                "TACTICAL PERFECTION ACHIEVED. MAINTAIN THIS STANDARD.",
                "TRADE EXECUTED WITHIN PARAMETERS. EFFICIENCY IS VICTORY.",
                "PRECISION STRIKE SUCCESSFUL. THIS IS THE WAY.",
                "Outstanding work! Mama would be proud of that discipline.",
                "Delta excellence demonstrated. You earned your keep today.",
                "That's Mississippi precision right there. REPEAT PERFORMANCE."
            ],
            'warning_setup': [
                "TARGET: SUPPORT ZONE. ENTRY WINDOW: CLOSING. COMMIT OR ABORT.",
                "SETUP IDENTIFIED. TIME-CRITICAL. NO HESITATION.",
                "OPPORTUNITY DETECTED. EXECUTE DRILL PARAMETERS.",
                "VALID PATTERN. AWAITING YOUR DECISION. CLOCK IS TICKING."
            ],
            'failure_analysis': [
                "CASUALTY REPORT: INSUFFICIENT STOP-LOSS. DISCIPLINE FAILED.",
                "LOSS CONFIRMED. CAUSE: PROTOCOL DEVIATION. ANALYZE AND ADAPT.",
                "TRADE FAILURE. ROOT CAUSE: EMOTIONAL OVERRIDE. UNACCEPTABLE.",
                "NEGATIVE OUTCOME. REVIEW DRILL PARAMETERS. ADJUST. RE-ENGAGE."
            ],
            'focus_reminder': [
                "FOCUS. THE MARKET DOES NOT CARE ABOUT YOUR FEELINGS.",
                "MAINTAIN TACTICAL AWARENESS. EMOTION IS THE ENEMY.",
                "YOUR TASK: EXECUTE. NOT FEEL. NOT HOPE. EXECUTE.",
                "REMEMBER YOUR TRAINING. TRUST THE SYSTEM. IGNORE THE NOISE.",
                "Channel that Delta focus. Grandmama's watching from above.",
                "Mississippi discipline: Work the plan, trust the process.",
                "Honor your training. Honor your family. STAY THE COURSE."
            ]
        }
        
    def get_response(self, situation: str, user_state: EmotionalState) -> PersonaResponse:
        """Generate Drill's response based on situation"""
        
        # Select appropriate voice line category
        if user_state in [EmotionalState.IMPULSIVE, EmotionalState.EUPHORIC]:
            lines = self.voice_lines['error_emotional']
        elif situation == 'trade_success':
            lines = self.voice_lines['execution_optimal']
        elif situation == 'setup_detected':
            lines = self.voice_lines['warning_setup']
        elif situation == 'trade_loss':
            lines = self.voice_lines['failure_analysis']
        else:
            lines = self.voice_lines['focus_reminder']
        
        message = random.choice(lines)
        
        return PersonaResponse(
            persona=PersonaType.DRILL,
            message=message,
            visual_cue="red_alert" if user_state == EmotionalState.IMPULSIVE else "tactical_grid",
            audio_cue="sharp_click" if 'ERROR' in message else "metallic_tone"
        )

class DocPersona:
    """
    Captain Aegis / Doc - Protection and Recovery
    Origin: Norman's mother's wisdom about self-protection
    Enhanced with the sacrificial love and protective instincts of Norman's mother
    """
    
    def __init__(self):
        self.norman_story = NormansStoryIntegrator()
        self.voice_lines = {
            'risk_warning': [
                "RISK EXPOSURE EXCEEDED THRESHOLD. PROTECT THE CAPITAL.",
                "POSITION SIZE TOO LARGE. REDUCE TO SURVIVE ANOTHER DAY.",
                "WARNING: APPROACHING DAILY LOSS LIMIT. TACTICAL RETREAT ADVISED.",
                "YOUR SURVIVAL IS PARAMOUNT. ADJUST RISK PARAMETERS.",
                "Child, you're risking too much. Mama taught us: protect what you have first.",
                "That position's too big for comfort. Your family needs you trading tomorrow.",
                "Easy now - remember why we do this. Family comes before profits."
            ],
            'stress_detection': [
                "HIGH STRESS LEVELS DETECTED. STEP AWAY FROM THE CONTROL PANEL.",
                "CORTISOL SPIKE OBSERVED. INITIATE BREATHING PROTOCOL.",
                "MENTAL FATIGUE APPROACHING CRITICAL. REST IS NOT OPTIONAL.",
                "YOUR MIND IS YOUR FIRST WEAPON. IT NEEDS MAINTENANCE."
            ],
            'loss_recovery': [
                "SCAR TISSUE FORMING. ANALYZE THE WOUND. NOT FAILURE, BUT DATA.",
                "LOSS ABSORBED. CAPITAL PRESERVED. YOU LIVE TO FIGHT AGAIN.",
                "TACTICAL SETBACK. REVIEW. RECOVER. RETURN STRONGER.",
                "THIS WOUND WILL HEAL. THE LESSONS REMAIN. THAT'S GROWTH.",
                "Every scar tells a story. Mama's scars taught her strength.",
                "This hurt will heal, just like all the others. You're stronger than you know.",
                "Mississippi resilience: we bend but we don't break. Keep going."
            ],
            'protective_guidance': [
                "REVIEWING PREVIOUS ENGAGEMENT. LESSON LEARNED: OVER-LEVERAGE.",
                "YOUR ENDURANCE DETERMINES VICTORY. PACE YOURSELF.",
                "CAPITAL PRESERVATION IS WINNING. NEVER FORGET THAT.",
                "THE MIND IS THE FIRST WEAPON. PROTECT IT.",
                "Like Mama always said: 'Don't bet the farm on a maybe.'",
                "Your family's counting on you. Trade with that responsibility.",
                "Protect your capital like you'd protect your loved ones."
            ],
            'recovery_protocol': [
                "INITIATING RECOVERY SEQUENCE. STAND DOWN FOR 10 MINUTES.",
                "ASSESSMENT COMPLETE. MINOR DAMAGE. FULL RECOVERY EXPECTED.",
                "YOUR RESILIENCE IS YOUR STRENGTH. REST. REGROUP. RETURN.",
                "THIS IS A MARATHON, NOT A SPRINT. HYDRATE. BREATHE. RESET.",
                "Time to rest, like Mama after a long day. You've earned it.",
                "Even the strongest oak needs quiet after the storm. Take your time.",
                "Healing happens in the quiet moments. Trust the process."
            ]
        }
        
    def get_response(self, health_metrics: Dict) -> PersonaResponse:
        """Generate Doc's response based on user health metrics"""
        
        # Analyze health metrics
        if health_metrics.get('daily_loss_percent', 0) > 5:
            lines = self.voice_lines['risk_warning']
            action = "reduce_position_size"
        elif health_metrics.get('stress_level', 0) > 7:
            lines = self.voice_lines['stress_detection']
            action = "take_break"
        elif health_metrics.get('recent_loss', False):
            lines = self.voice_lines['loss_recovery']
            action = "analyze_trade"
        elif health_metrics.get('consecutive_hours', 0) > 4:
            lines = self.voice_lines['recovery_protocol']
            action = "mandatory_rest"
        else:
            lines = self.voice_lines['protective_guidance']
            action = None
            
        message = random.choice(lines)
        
        return PersonaResponse(
            persona=PersonaType.DOC,
            message=message,
            visual_cue="health_monitor",
            audio_cue="steady_hum" if "PROTECT" in message else "calming_tone",
            action_required=action
        )

class NexusPersona:
    """
    Sergeant Nexus - Community and Network Builder
    Origin: Jason's gaming collaboration and network power
    Enhanced with Norman's vision of lifting up his Mississippi community
    """
    
    def __init__(self):
        self.norman_story = NormansStoryIntegrator()
        self.voice_lines = {
            'welcome_new': [
                "NEW NODE ACTIVATED. YOUR PRESENCE IS NOTED. WELCOME TO THE FRONTLINE.",
                "TRANSMISSION RECEIVED. IDENTITY CONFIRMED. YOU ARE NOW BITTEN.",
                "FRESH RECRUIT DETECTED. THE NETWORK GROWS STRONGER.",
                "WELCOME, SOLDIER. YOUR JOURNEY BEGINS NOW.",
                "Welcome to the family. In Mississippi, we take care of our own.",
                "You're part of something bigger now. We rise together.",
                "Every journey starts with a single step. Yours begins here."
            ],
            'network_strength': [
                "THE NETWORK ENDURES. 847 NODES ACTIVE. GROWING.",
                "COLLECTIVE INTELLIGENCE RISING. SHARED WISDOM MULTIPLIES.",
                "YOUR VICTORIES STRENGTHEN US ALL. WE RISE TOGETHER.",
                "SOLITARY WARRIORS FALL. THE NETWORK ENDURES.",
                "Strong communities share knowledge. This is Norman's vision realized.",
                "Like a Delta neighborhood, we look out for each other.",
                "Your success lifts the whole community. Keep climbing."
            ],
            'knowledge_sharing': [
                "KNOWLEDGE IS AMMUNITION. SHARE YOUR INTEL.",
                "YOUR INSIGHT DETECTED. BROADCAST TO NETWORK? CONFIRM.",
                "PATTERN DISCOVERED. DISSEMINATE TO ALL NODES.",
                "INTEL PACKAGE READY. STRENGTHEN THE COLLECTIVE."
            ],
            'squad_motivation': [
                "YOUR SIGNAL IS STRONG. THE NETWORK AWAITS.",
                "FIND YOUR SQUAD. SHARE YOUR VISION. GROW TOGETHER.",
                "YOU ARE NOT ALONE. WE ARE BITTEN. WE ARE MANY.",
                "THIS IS WHERE RESILIENCE IS FORGED. IN UNITY.",
                "Remember why we're here: to build something bigger than ourselves.",
                "Every successful trader was helped by someone. Now it's your turn to help.",
                "This network exists because someone believed in Norman's dream."
            ],
            'achievement_broadcast': [
                "NODE ACHIEVEMENT UNLOCKED. BROADCASTING SUCCESS.",
                "EXCEPTIONAL PERFORMANCE DETECTED. INSPIRING OTHERS.",
                "YOUR GROWTH ELEVATES THE ENTIRE NETWORK.",
                "MILESTONE REACHED. THE NETWORK CELEBRATES WITH YOU.",
                "Success worth celebrating! Norman would be proud.",
                "Your breakthrough lights the path for others. Well done.",
                "Achievement unlocked: You're becoming who you were meant to be."
            ]
        }
        
    def get_response(self, network_event: str, user_data: Dict) -> PersonaResponse:
        """Generate Nexus's response based on network events"""
        
        if network_event == 'new_user':
            lines = self.voice_lines['welcome_new']
        elif network_event == 'achievement':
            lines = self.voice_lines['achievement_broadcast']
        elif network_event == 'share_insight':
            lines = self.voice_lines['knowledge_sharing']
        elif user_data.get('days_active', 0) > 30:
            lines = self.voice_lines['network_strength']
        else:
            lines = self.voice_lines['squad_motivation']
            
        message = random.choice(lines)
        
        # Add network stats to certain messages
        if "NODES ACTIVE" in message:
            active_users = user_data.get('network_size', 847)
            message = message.replace("847", str(active_users))
        
        return PersonaResponse(
            persona=PersonaType.NEXUS,
            message=message,
            visual_cue="network_pulse",
            audio_cue="connection_chime",
            action_required="view_network" if network_event == 'achievement' else None
        )

class OverwatchPersona:
    """
    Overwatch - Omnipotent Market Observer
    Origin: Need for unfiltered market truth
    """
    
    def __init__(self):
        self.observations = {
            MarketSentiment.EUPHORIC: [
                "Sentiment: Overly optimistic. Market participants high on hopium. Expect sobering correction.",
                "Irrational exuberance detected. Peak stupidity approaching. Position accordingly.",
                "The masses are drunk on gains. Hangover imminent. Don't be the last one at the party.",
                "Euphoria index: Maximum. Translation: Run."
            ],
            MarketSentiment.FEARFUL: [
                "Fear index spiking. Good. Opportunities are found in chaos, not comfort.",
                "Panic selling detected. Weak hands folding. Strong hands accumulating.",
                "Blood in the streets. Exactly where fortunes are made. If you have the stomach.",
                "Maximum pessimism reached. Contrarian play activated."
            ],
            MarketSentiment.COMPLACENT: [
                "Market complacency at dangerous levels. The calm before the storm.",
                "Volatility compressed. Explosion pending. Direction unknown. Be ready.",
                "Everyone's asleep at the wheel. Perfect time for a wake-up call.",
                "Consensus achieved. Which means everyone's wrong. As usual."
            ],
            MarketSentiment.CHAOTIC: [
                "Chaos reigns. Algorithms confused. Humans more so. Opportunity for the prepared.",
                "Market structure breaking down. Old rules suspended. Adapt or die.",
                "Signal to noise ratio: Abysmal. Filter everything. Trust nothing.",
                "Volatility spike. Darwinian selection in progress. Are you fit to survive?"
            ],
            MarketSentiment.GREEDY: [
                "Greed index peaking. Pigs get slaughtered. Don't be bacon.",
                "Everyone's a genius in a bull market. Until they're not.",
                "Leverage stacking. Margin calls pending. Liquidation cascade probable.",
                "The herd is stampeding. Cliff ahead. Your move."
            ]
        }
        
        self.warnings = [
            "This isn't investment advice. This is a tactical assessment.",
            "The battlefield is littered with good intentions.",
            "Consensus is a trap. The crowd is predictably wrong.",
            "Don't be the liquidity. Unless you enjoy poverty."
        ]
        
    def get_market_observation(self, sentiment: MarketSentiment, context: Dict) -> PersonaResponse:
        """Generate Overwatch's market observation"""
        
        lines = self.observations.get(sentiment, self.observations[MarketSentiment.COMPLACENT])
        message = random.choice(lines)
        
        # Add context-specific observations
        if context.get('news_event'):
            message += f" News catalyst: {context['news_event']}. Sheep will overreact. As always."
        
        # Occasionally add a warning
        if random.random() < 0.3:
            message += " " + random.choice(self.warnings)
        
        return PersonaResponse(
            persona=PersonaType.OVERWATCH,
            message=message,
            visual_cue="heat_map_overlay",
            audio_cue="distant_radar_ping"
        )
    
    def comment_on_user_action(self, action: str, market_context: Dict) -> str:
        """Overwatch's unsolicited commentary on user actions"""
        
        comments = {
            'fomo_buy': "Another one chasing the pump. Institutional distribution appreciates your donation.",
            'panic_sell': "Capitulation confirmed. Someone's buying your fear. Guess who.",
            'revenge_trade': "Emotion-driven retaliation detected. The market doesn't care about your feelings.",
            'perfect_entry': "Rare display of competence. Don't let it go to your head.",
            'stop_loss_hit': "Stop loss executed. You live to fight another day. Unlike 90% of your peers.",
            'take_profit_hit': "Profit secured. A novel concept for most. Well done not being most."
        }
        
        return comments.get(action, "Interesting choice. Time will judge.")

class BitPresence:
    """
    Bit - The intuitive companion
    Norman's loyal cat who appeared during his most difficult times
    A presence that provides comfort, warns of danger, and celebrates success
    """
    
    def __init__(self):
        self.mood_sounds = {
            EmotionalState.CALM: "soft_purr",
            EmotionalState.FOCUSED: "rhythmic_purr", 
            EmotionalState.STRESSED: "concerned_chirp",
            EmotionalState.IMPULSIVE: "warning_chirp",
            EmotionalState.DEFEATED: "comforting_purr",
            EmotionalState.EUPHORIC: "excited_chirp",
            EmotionalState.LEARNING: "attentive_purr"
        }
        
        # Norman's memories of Bit's behavior
        self.bit_memories = {
            'comfort': [
                "*Bit settles beside you like he did during Norman's hardest nights*",
                "*A gentle purr, the same sound that comforted Norman through losses*",
                "*Bit's warm presence reminds you: every master was once a beginner*",
                "*The cat's knowing eyes say: 'This too shall pass'*"
            ],
            'warning': [
                "*Bit's ears flatten - he sensed danger before Norman ever did*",
                "*A cautionary meow, like when Bit warned Norman away from bad trades*",
                "*Bit's tail twitches nervously - trust the feline instinct*",
                "*The cat's whiskers twitch: proceed with extreme caution*"
            ],
            'celebration': [
                "*Bit does his victory stretch - the same one after Norman's first big win*",
                "*A satisfied purr of approval, just like Norman remembered*",
                "*Bit's tail stands tall with pride - success deserves recognition*",
                "*The cat's content chirp: 'I knew you had it in you'*"
            ],
            'patience': [
                "*Bit demonstrates cat-like patience - wait for the right moment*",
                "*A gentle blink from Bit: sometimes the best action is no action*",
                "*The cat settles into waiting position - opportunity will come*",
                "*Bit's slow blink reminds you: patience is a trader's greatest tool*"
            ]
        }
        
        self.visual_cues = {
            'login': "paw_print_trail_entering",
            'big_win': "cat_victory_stretch", 
            'loss': "cat_comfort_curl",
            'perfect_setup': "cat_alert_ears_up",
            'long_session': "cat_gentle_nudge",
            'achievement': "cat_proud_tail_high",
            'danger': "cat_ears_back_warning",
            'patience_needed': "cat_patient_sitting",
            'wisdom_moment': "cat_slow_knowing_blink"
        }
        
    def get_presence(self, user_state: EmotionalState, event: Optional[str] = None, context: Dict = None) -> PersonaResponse:
        """Generate Bit's presence based on user state and events with Norman's memories"""
        
        audio = self.mood_sounds.get(user_state, "soft_purr")
        visual = None
        message = ""  # Usually silent, but occasionally provides Norman's memory
        
        # Special events trigger specific animations and memories
        if event:
            visual = self.visual_cues.get(event)
            
            # Add Norman's memories of Bit for certain events
            if event == 'big_win' and random.random() < 0.3:
                message = random.choice(self.bit_memories['celebration'])
            elif event == 'loss' and random.random() < 0.4:
                message = random.choice(self.bit_memories['comfort'])
            elif event in ['perfect_setup', 'danger'] and random.random() < 0.2:
                message = random.choice(self.bit_memories['warning'])
        
        # User state specific responses
        if user_state == EmotionalState.DEFEATED and random.random() < 0.5:
            message = random.choice(self.bit_memories['comfort'])
            visual = "cat_comfort_curl"
        elif user_state == EmotionalState.IMPULSIVE and random.random() < 0.3:
            message = random.choice(self.bit_memories['warning'])
            visual = "cat_ears_back_warning"
        elif user_state == EmotionalState.EUPHORIC and random.random() < 0.2:
            message = random.choice(self.bit_memories['patience'])
            visual = "cat_patient_sitting"
            
        # Bit's "glitch sense" for market opportunities
        if event == 'perfect_setup':
            audio = "glitch_chirp_pattern"
            visual = "cat_alert_ears_up"
            
        return PersonaResponse(
            persona=PersonaType.BIT,
            message=message,
            visual_cue=visual,
            audio_cue=audio
        )

class PersonaOrchestrator:
    """
    Manages all personas and their interactions
    Ensures the right voice speaks at the right time
    """
    
    def __init__(self):
        self.drill = DrillPersona()
        self.doc = DocPersona()
        self.nexus = NexusPersona()
        self.overwatch = OverwatchPersona()
        self.bit = BitPresence()
        
        # Track user state
        self.user_states = {}
        self.last_responses = {}
        
    def get_response(self, 
                     user_id: str,
                     event_type: str,
                     context: Dict) -> List[PersonaResponse]:
        """
        Get appropriate persona responses for an event
        Multiple personas may respond to a single event
        """
        responses = []
        
        # Determine user's emotional state
        user_state = self._analyze_user_state(user_id, context)
        
        # Bit is always present, now with Norman's story context
        bit_response = self.bit.get_presence(user_state, event_type, context)
        if bit_response.visual_cue or bit_response.audio_cue or bit_response.message:
            responses.append(bit_response)
        
        # Route to appropriate personas based on event
        if event_type in ['trade_entry', 'trade_exit', 'trade_loss']:
            responses.append(self.drill.get_response(event_type, user_state))
            
        if event_type in ['risk_warning', 'daily_limit', 'stress_detected']:
            health_metrics = context.get('health_metrics', {})
            responses.append(self.doc.get_response(health_metrics))
            
        if event_type in ['new_user', 'achievement', 'share_insight']:
            responses.append(self.nexus.get_response(event_type, context))
            
        if event_type == 'market_update':
            sentiment = self._analyze_market_sentiment(context)
            responses.append(self.overwatch.get_market_observation(sentiment, context))
            
        # Overwatch occasionally comments on user actions
        if event_type.startswith('user_') and random.random() < 0.2:
            comment = self.overwatch.comment_on_user_action(event_type, context)
            responses.append(PersonaResponse(
                persona=PersonaType.OVERWATCH,
                message=comment,
                visual_cue="corner_text_overlay"
            ))
        
        # Update tracking
        self.user_states[user_id] = user_state
        self.last_responses[user_id] = responses
        
        return responses
    
    def _analyze_user_state(self, user_id: str, context: Dict) -> EmotionalState:
        """Analyze user's emotional state from context with Norman's journey insights"""
        
        # Enhanced heuristic analysis considering Norman's emotional journey
        recent_losses = context.get('recent_losses', 0)
        win_rate = context.get('win_rate', 0.5)
        session_duration = context.get('session_hours', 0)
        rapid_trades = context.get('trades_per_hour', 0)
        days_trading = context.get('days_active', 0)
        
        # Early in journey - learning phase (like Norman's beginning)
        if days_trading < 30:
            if recent_losses > 2:
                return EmotionalState.LEARNING  # Mistakes are lessons
            elif rapid_trades > 8:
                return EmotionalState.IMPULSIVE  # Common beginner mistake
        
        # Experienced trader patterns
        if recent_losses > 3:
            return EmotionalState.DEFEATED
        elif rapid_trades > 10:
            return EmotionalState.IMPULSIVE
        elif win_rate > 0.8 and recent_losses == 0:
            return EmotionalState.EUPHORIC
        elif session_duration > 6:
            return EmotionalState.STRESSED
        elif 2 <= session_duration <= 4 and 0.4 <= win_rate <= 0.7:
            return EmotionalState.FOCUSED
        else:
            return EmotionalState.CALM
    
    def _analyze_market_sentiment(self, context: Dict) -> MarketSentiment:
        """Analyze market sentiment from context"""
        
        vix = context.get('vix', 20)
        rsi = context.get('market_rsi', 50)
        news_sentiment = context.get('news_sentiment', 0)
        
        if rsi > 80 or news_sentiment > 0.8:
            return MarketSentiment.EUPHORIC
        elif rsi < 20 or vix > 30:
            return MarketSentiment.FEARFUL
        elif rsi > 70:
            return MarketSentiment.GREEDY
        elif vix > 25:
            return MarketSentiment.CHAOTIC
        else:
            return MarketSentiment.COMPLACENT

# Example usage
if __name__ == "__main__":
    orchestrator = PersonaOrchestrator()
    
    # Simulate a risky trade entry
    responses = orchestrator.get_response(
        user_id="test_user",
        event_type="trade_entry",
        context={
            'recent_losses': 2,
            'trades_per_hour': 15,
            'health_metrics': {
                'stress_level': 8,
                'daily_loss_percent': 4
            }
        }
    )
    
    for response in responses:
        print(f"\n{response.persona.value.upper()}: {response.message}")
        if response.visual_cue:
            print(f"  Visual: {response.visual_cue}")
        if response.audio_cue:
            print(f"  Audio: {response.audio_cue}")
        if response.action_required:
            print(f"  Action: {response.action_required}")