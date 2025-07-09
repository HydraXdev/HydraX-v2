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
    """
    
    def __init__(self):
        self.voice_lines = {
            'error_emotional': [
                "ERROR. EMOTIONAL IMPULSE DETECTED. RECALIBRATE. REFER TO RULES.",
                "WEAKNESS IDENTIFIED. EMOTION OVERRIDING LOGIC. ABORT CURRENT ACTION.",
                "DISCIPLINE BREACH. REALIGN WITH PROTOCOL. NOW.",
                "YOUR FEELINGS ARE IRRELEVANT. EXECUTE THE PLAN."
            ],
            'execution_optimal': [
                "EXECUTION: OPTIMAL. PATTERN RECOGNITION: CONFIRMED. REPEAT CYCLE.",
                "TACTICAL PERFECTION ACHIEVED. MAINTAIN THIS STANDARD.",
                "TRADE EXECUTED WITHIN PARAMETERS. EFFICIENCY IS VICTORY.",
                "PRECISION STRIKE SUCCESSFUL. THIS IS THE WAY."
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
                "REMEMBER YOUR TRAINING. TRUST THE SYSTEM. IGNORE THE NOISE."
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
    """
    
    def __init__(self):
        self.voice_lines = {
            'risk_warning': [
                "RISK EXPOSURE EXCEEDED THRESHOLD. PROTECT THE CAPITAL.",
                "POSITION SIZE TOO LARGE. REDUCE TO SURVIVE ANOTHER DAY.",
                "WARNING: APPROACHING DAILY LOSS LIMIT. TACTICAL RETREAT ADVISED.",
                "YOUR SURVIVAL IS PARAMOUNT. ADJUST RISK PARAMETERS."
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
                "THIS WOUND WILL HEAL. THE LESSONS REMAIN. THAT'S GROWTH."
            ],
            'protective_guidance': [
                "REVIEWING PREVIOUS ENGAGEMENT. LESSON LEARNED: OVER-LEVERAGE.",
                "YOUR ENDURANCE DETERMINES VICTORY. PACE YOURSELF.",
                "CAPITAL PRESERVATION IS WINNING. NEVER FORGET THAT.",
                "THE MIND IS THE FIRST WEAPON. PROTECT IT."
            ],
            'recovery_protocol': [
                "INITIATING RECOVERY SEQUENCE. STAND DOWN FOR 10 MINUTES.",
                "ASSESSMENT COMPLETE. MINOR DAMAGE. FULL RECOVERY EXPECTED.",
                "YOUR RESILIENCE IS YOUR STRENGTH. REST. REGROUP. RETURN.",
                "THIS IS A MARATHON, NOT A SPRINT. HYDRATE. BREATHE. RESET."
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
    """
    
    def __init__(self):
        self.voice_lines = {
            'welcome_new': [
                "NEW NODE ACTIVATED. YOUR PRESENCE IS NOTED. WELCOME TO THE FRONTLINE.",
                "TRANSMISSION RECEIVED. IDENTITY CONFIRMED. YOU ARE NOW BITTEN.",
                "FRESH RECRUIT DETECTED. THE NETWORK GROWS STRONGER.",
                "WELCOME, SOLDIER. YOUR JOURNEY BEGINS NOW."
            ],
            'network_strength': [
                "THE NETWORK ENDURES. 847 NODES ACTIVE. GROWING.",
                "COLLECTIVE INTELLIGENCE RISING. SHARED WISDOM MULTIPLIES.",
                "YOUR VICTORIES STRENGTHEN US ALL. WE RISE TOGETHER.",
                "SOLITARY WARRIORS FALL. THE NETWORK ENDURES."
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
                "THIS IS WHERE RESILIENCE IS FORGED. IN UNITY."
            ],
            'achievement_broadcast': [
                "NODE ACHIEVEMENT UNLOCKED. BROADCASTING SUCCESS.",
                "EXCEPTIONAL PERFORMANCE DETECTED. INSPIRING OTHERS.",
                "YOUR GROWTH ELEVATES THE ENTIRE NETWORK.",
                "MILESTONE REACHED. THE NETWORK CELEBRATES WITH YOU."
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
    Not a voice but a presence felt throughout the system
    """
    
    def __init__(self):
        self.mood_sounds = {
            EmotionalState.CALM: "soft_purr",
            EmotionalState.FOCUSED: "rhythmic_purr",
            EmotionalState.STRESSED: "agitated_chirp",
            EmotionalState.IMPULSIVE: "warning_chirp",
            EmotionalState.DEFEATED: "comforting_purr",
            EmotionalState.EUPHORIC: "curious_chirp",
            EmotionalState.LEARNING: "attentive_purr"
        }
        
        self.visual_cues = {
            'login': "paw_print_trail",
            'big_win': "cat_stretch_animation",
            'loss': "cat_curl_animation",
            'perfect_setup': "glitch_chirp_alert",
            'long_session': "cat_nudge_animation",
            'achievement': "tail_swish_animation"
        }
        
    def get_presence(self, user_state: EmotionalState, event: Optional[str] = None) -> PersonaResponse:
        """Generate Bit's presence based on user state and events"""
        
        audio = self.mood_sounds.get(user_state, "soft_purr")
        visual = None
        
        # Special events trigger specific animations
        if event:
            visual = self.visual_cues.get(event)
            
        # Bit's "glitch sense" for market opportunities
        if event == 'perfect_setup':
            audio = "glitch_chirp_pattern"
            
        return PersonaResponse(
            persona=PersonaType.BIT,
            message="",  # Bit doesn't speak
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
        
        # Bit is always present
        bit_response = self.bit.get_presence(user_state, event_type)
        if bit_response.visual_cue or bit_response.audio_cue:
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
        """Analyze user's emotional state from context"""
        
        # Simple heuristic-based analysis
        recent_losses = context.get('recent_losses', 0)
        win_rate = context.get('win_rate', 0.5)
        session_duration = context.get('session_hours', 0)
        rapid_trades = context.get('trades_per_hour', 0)
        
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