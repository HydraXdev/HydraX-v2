# mission_briefing_generator.py
# BITTEN Mission Briefing Generator - Formats trade data for WebApp HUD display

import json
import time
import random
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

# Import Norman's story integration
try:
    from .norman_story_integration import norman_story_engine, integrate_norman_story
except ImportError:
    # Fallback if import fails
    norman_story_engine = None
    def integrate_norman_story(briefing_data, user_id, context): return briefing_data

# Import timer integrations
try:
    from ..bitten.core.smart_timer_integration import smart_timer_integration
    from ..bitten.core.timer_expiry_integration import timer_expiry_integration
    TIMER_INTEGRATION_AVAILABLE = True
except ImportError:
    smart_timer_integration = None
    timer_expiry_integration = None
    TIMER_INTEGRATION_AVAILABLE = False
    logger = logging.getLogger(__name__)

class MissionType(Enum):
    """Mission types based on trading strategy"""
    RAPID_ASSAULT_SCALP = "arcade_scalp"
    SNIPER_SHOT = "sniper_shot"
    MIDNIGHT_HAMMER = "midnight_hammer"
    CHAINGUN_SEQUENCE = "chaingun_sequence"
    TACTICAL_RETREAT = "tactical_retreat"

class UrgencyLevel(Enum):
    """Mission urgency levels"""
    CRITICAL = "CRITICAL"  # < 2 minutes
    HIGH = "HIGH"         # 2-5 minutes  
    MEDIUM = "MEDIUM"     # 5-10 minutes
    LOW = "LOW"           # > 10 minutes

@dataclass
class MissionBriefing:
    """Complete mission briefing data structure for WebApp"""
    # Core mission data
    mission_id: str
    mission_type: MissionType
    urgency: UrgencyLevel
    callsign: str
    
    # Trading data
    symbol: str
    direction: str  # BUY/SELL
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_pips: int
    reward_pips: int
    risk_reward_ratio: float
    
    # Confidence metrics
    tcs_score: int
    strategy_confidence: float
    market_conditions: Dict[str, Any]
    
    # Timing data
    created_at: int
    expires_at: int
    time_remaining: int
    expected_duration: int  # minutes
    
    # Signal Vitality & Decay (NEW)
    signal_age_minutes: int
    vitality_percentage: float  # 100% fresh to 0% expired
    vitality_status: str  # FRESH, VALID, AGING, EXPIRED
    vitality_icon: str  # 🟢🟡🟠🔴
    xp_bonus_multiplier: float  # 2x, 1.5x, 1x, 0x
    decay_rate: str  # RAPID (30min) or STANDARD (60min)
    execution_blocked: bool  # True if signal too old
    slippage_warning: Optional[str]  # Warning about potential price drift
    
    # Social proof
    active_operators: int
    total_engaged: int
    squad_avg_tcs: float
    success_rate: float
    
    # Access control
    required_tier: str
    tier_benefits: Dict[str, Any]
    
    # Visual elements
    visual_style: str
    emoji_set: str
    color_scheme: Dict[str, str]
    
    # Additional intel
    technical_levels: Dict[str, float]
    market_intel: List[str]
    risk_warnings: List[str]

class NormansStoryIntegrator:
    """Integrates Norman's Mississippi story and family wisdom into mission briefings"""
    
    def __init__(self):
        # Norman's family wisdom phrases
        self.family_wisdom = {
            'grandmother': [
                "Grandmama always said: 'Patience is worth more than gold, child.'",
                "Remember the old words: 'Good things come to those who wait for the right season.'",
                "As Grandmama used to say: 'The storm passes, but the oak remembers how to bend.'",
                "Grandmama's wisdom: 'Never bet the farm on a maybe.'"
            ],
            'mother': [
                "Mama taught us: 'Protect what you have before you reach for more.'",
                "Mother's sacrifice reminds us: 'Every dollar saved is a dollar earned.'",
                "As Mama would say: 'Don't put all your eggs in one basket, baby.'",
                "Mother always said: 'Know when to hold on and when to let go.'"
            ],
            'work_ethic': [
                "Back home we learned: 'Honest work pays honest wages.'",
                "Mississippi taught us: 'You earn your keep with discipline and grit.'",
                "From the Delta: 'Slow and steady wins the race, but smart and steady wins the war.'",
                "Home wisdom: 'Don't work harder, work smarter.'"
            ]
        }
        
        # Bit the cat references for different situations
        self.bit_presence = {
            'confidence': [
                "Bit's purring - something good is coming",
                "The cat's tail is twitching - opportunity detected",
                "Bit just stretched - time to make a move",
                "Your feline companion senses profit in the air"
            ],
            'caution': [
                "Bit's ears are back - proceed with caution",
                "The cat's hiding - might be time to wait",
                "Bit's watching from afar - stay alert",
                "Your companion's whiskers are twitching - danger ahead"
            ],
            'comfort': [
                "Bit settles beside you - you're not alone in this",
                "A gentle purr reminds you: every master was once a beginner",
                "Bit's warm presence: losses teach, wins confirm",
                "Your loyal companion knows: this too shall pass"
            ]
        }
        
        # Mississippi-themed callsigns that honor Norman's roots
        self.norman_callsigns = {
            'tactical': [
                "DELTA WISDOM", "MAGNOLIA STRIKE", "COTTON FIELD", 
                "MUDDY WATERS", "RIVER BEND", "PINE GROVE"
            ],
            'family': [
                "MAMA'S BLESSING", "GRANDMAMA'S WATCH", "FAMILY HONOR",
                "HOME GUARDIAN", "LEGACY KEEPER", "DELTA PRIDE"
            ],
            'journey': [
                "LONG ROAD HOME", "DREAM KEEPER", "BRIDGE BUILDER",
                "MOUNTAIN MOVER", "LIGHT BEARER", "PATH FINDER"
            ]
        }
        
        # Southern/Mississippi cultural elements
        self.cultural_elements = {
            'weather_metaphors': [
                "Like a Delta storm, this opportunity builds slow but hits hard",
                "Summer heat teaches patience - good trades ripen in their time",
                "Winter morning clarity - the market shows its true face",
                "Spring rains bring growth - let your portfolio flourish"
            ],
            'farming_wisdom': [
                "You don't plant corn and expect cotton - know what you're trading",
                "Good farmers diversify crops - smart traders diversify positions",
                "Harvest time comes to those who tend their fields",
                "Even the best soil needs rest - don't overtrade"
            ],
            'community_values': [
                "We rise together or we fall apart - help your fellow traders",
                "Strong communities share knowledge, not just profits",
                "Your success lifts the whole neighborhood",
                "Remember why we do this - to build something bigger than ourselves"
            ]
        }

class MissionBriefingGenerator:
    """Generates comprehensive mission briefings infused with Norman's story for WebApp HUD"""
    
    def __init__(self, user_id: str = None):
        self.mission_counter = 0
        self.user_id = user_id
        self.norman_story = NormansStoryIntegrator()
        
        # Signal decay configuration
        self.decay_rates = {
            'RAPID_ASSAULT': 30,  # Expires in 30 minutes
            'PRECISION_STRIKE': 60,  # Expires in 60 minutes
            'SNIPER_SHOT': 60,  # Snipers get more time
            'TACTICAL_SHOT': 45,  # Medium duration
            'DEFAULT': 45  # Default for unknown types
        }
        
        # Enhanced callsign pool with Norman's story elements
        self.callsign_pool = {
            MissionType.RAPID_ASSAULT_SCALP: [
                "DAWN RAID", "VORTEX AMBUSH", "LIGHTNING STRIKE", 
                "SHADOW PIERCE", "RAPID ASSAULT", "GHOST RECON",
                "DELTA WISDOM", "COTTON FIELD", "RIVER BEND"
            ],
            MissionType.SNIPER_SHOT: [
                "EAGLE EYE", "PHANTOM SHOT", "SILENT HUNTER",
                "PRECISION STRIKE", "LONG RANGE", "STEALTH OPS",
                "GRANDMAMA'S WATCH", "MAMA'S BLESSING", "PINE GROVE"
            ],
            MissionType.MIDNIGHT_HAMMER: [
                "MIDNIGHT HAMMER", "UNITED FORCE", "SQUAD ASSAULT",
                "MASS STRIKE", "COORDINATED HIT", "TEAM TAKEDOWN",
                "FAMILY HONOR", "DELTA PRIDE", "BRIDGE BUILDER"
            ]
        }
        
        self.color_schemes = {
            "arcade": {
                "primary": "#00ff41",     # Matrix green
                "secondary": "#39ff14",   # Neon green
                "danger": "#ff073a",      # Neon red
                "warning": "#ffb700",     # Amber
                "info": "#00d4ff",        # Cyan
                "background": "#0a0a0a"   # Dark
            },
            "sniper": {
                "primary": "#ff6b35",     # Orange-red
                "secondary": "#f7931e",   # Orange
                "danger": "#cc0000",      # Dark red
                "warning": "#ffd700",     # Gold
                "info": "#4a90e2",        # Blue
                "background": "#1a1a1a"   # Dark gray
            },
            "midnight": {
                "primary": "#7b68ee",     # Medium slate blue
                "secondary": "#9370db",   # Medium purple
                "danger": "#dc143c",      # Crimson
                "warning": "#ffa500",     # Orange
                "info": "#00ced1",        # Dark turquoise
                "background": "#191970"   # Midnight blue
            }
        }
    
    def calculate_signal_vitality(self, signal_data: Dict) -> Dict:
        """Calculate signal vitality based on age and type"""
        # Get signal generation time
        signal_time = signal_data.get('generated_at', datetime.now())
        if isinstance(signal_time, str):
            try:
                signal_time = datetime.fromisoformat(signal_time.replace('Z', '+00:00'))
            except:
                signal_time = datetime.now()
        elif isinstance(signal_time, (int, float)):
            signal_time = datetime.fromtimestamp(signal_time)
        
        # Calculate age
        current_time = datetime.now()
        age_seconds = (current_time - signal_time).total_seconds()
        age_minutes = int(age_seconds / 60)
        
        # Get decay rate based on signal type
        signal_type = signal_data.get('signal_type', signal_data.get('type', 'DEFAULT'))
        if isinstance(signal_type, str):
            signal_type = signal_type.upper().replace(' ', '_')
        
        max_age_minutes = self.decay_rates.get(signal_type, self.decay_rates['DEFAULT'])
        
        # Calculate vitality percentage (100% fresh to 0% expired)
        vitality = max(0, min(100, (1 - (age_minutes / max_age_minutes)) * 100))
        
        # Determine status and bonuses based on vitality
        if vitality >= 80:
            status = "FRESH SIGNAL"
            icon = "🟢"  # Green circle
            xp_multiplier = 2.0
            execution_blocked = False
            slippage_warning = None
        elif vitality >= 50:
            status = "VALID SIGNAL"
            icon = "🟡"  # Yellow circle
            xp_multiplier = 1.5
            execution_blocked = False
            slippage_warning = "Minor price drift possible"
        elif vitality >= 20:
            status = "AGING SIGNAL"
            icon = "🟠"  # Orange circle
            xp_multiplier = 1.0
            execution_blocked = False
            slippage_warning = "Significant price drift likely - trade with caution"
        else:
            status = "EXPIRED SIGNAL"
            icon = "🔴"  # Red circle
            xp_multiplier = 0.0
            execution_blocked = True
            slippage_warning = "Signal expired - DO NOT EXECUTE"
        
        return {
            'age_minutes': age_minutes,
            'vitality_percentage': vitality,
            'vitality_status': status,
            'vitality_icon': icon,
            'xp_bonus_multiplier': xp_multiplier,
            'decay_rate': f"{signal_type} ({max_age_minutes}min)",
            'execution_blocked': execution_blocked,
            'slippage_warning': slippage_warning,
            'expires_in_minutes': max(0, max_age_minutes - age_minutes)
        }
    
    def generate_mission_briefing(self, 
                                 signal_data: Dict,
                                 market_data: Dict,
                                 user_tier: str = "AUTHORIZED",
                                 user_id: str = None) -> MissionBriefing:
        """Generate complete mission briefing from signal and market data"""
        
        # Calculate signal vitality FIRST
        vitality_data = self.calculate_signal_vitality(signal_data)
        
        # Determine mission type
        mission_type = self._determine_mission_type(signal_data)
        
        # Calculate timing
        current_time = int(time.time())
        
        # Check for smart timer data from AI enhancement
        if signal_data.get('countdown_minutes'):
            # Use AI-calculated smart timer
            countdown_seconds = signal_data.get('countdown_seconds', signal_data['countdown_minutes'] * 60)
            expires_at = current_time + countdown_seconds
            time_remaining = countdown_seconds
            
            # Log smart timer usage
            logger.info(f"Using smart timer: {signal_data['countdown_minutes']} min for {signal_data.get('symbol', 'unknown')}")
        else:
            # Fallback to default timing
            expires_at = signal_data.get('expires_at', current_time + 600)
            time_remaining = max(0, expires_at - current_time)
        
        # Calculate urgency
        urgency = self._calculate_urgency(time_remaining)
        
        # Get callsign with Norman's story integration
        base_callsign = self._get_callsign(mission_type)
        if user_id and norman_story_engine:
            callsign = norman_story_engine.get_callsign_with_story(base_callsign, user_id)
        else:
            callsign = self._add_norman_context_to_callsign(base_callsign, mission_type)
        
        # Generate mission ID
        mission_id = f"{mission_type.value}_{self.mission_counter}_{current_time}"
        self.mission_counter += 1
        
        # Calculate risk/reward
        entry = signal_data['entry_price']
        sl = signal_data['stop_loss']
        tp = signal_data['take_profit']
        
        risk_pips = abs(entry - sl) * 10000 if signal_data['symbol'].endswith('JPY') else abs(entry - sl) * 10000
        reward_pips = abs(tp - entry) * 10000 if signal_data['symbol'].endswith('JPY') else abs(tp - entry) * 10000
        risk_reward_ratio = round(reward_pips / risk_pips, 2) if risk_pips > 0 else 0
        
        # Get market conditions
        market_conditions = self._analyze_market_conditions(market_data)
        
        # Get tier benefits
        tier_benefits = self._get_tier_benefits(user_tier, mission_type)
        
        # Generate technical levels
        technical_levels = self._calculate_technical_levels(signal_data, market_data)
        
        # Generate market intel
        market_intel = self._generate_market_intel(signal_data, market_data, market_conditions)
        
        # Generate risk warnings
        risk_warnings = self._generate_risk_warnings(signal_data, market_conditions)
        
        # Determine visual style
        visual_style = self._get_visual_style(mission_type)
        emoji_set = self._get_emoji_set(mission_type, urgency)
        color_scheme = self.color_schemes.get(visual_style, self.color_schemes["arcade"])
        
        # Add slippage warning to risk warnings if signal is aging
        if vitality_data['slippage_warning'] and vitality_data['slippage_warning'] not in risk_warnings:
            risk_warnings.insert(0, f"⚠️ {vitality_data['slippage_warning']}")
        
        # Create mission briefing with vitality data
        briefing = MissionBriefing(
            mission_id=mission_id,
            mission_type=mission_type,
            urgency=urgency,
            callsign=callsign,
            symbol=signal_data['symbol'],
            direction=signal_data['direction'].upper(),
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            risk_pips=int(risk_pips),
            reward_pips=int(reward_pips),
            risk_reward_ratio=risk_reward_ratio,
            tcs_score=signal_data.get('tcs_score', 75),
            strategy_confidence=signal_data.get('confidence', 0.75),
            market_conditions=market_conditions,
            created_at=current_time,
            expires_at=expires_at,
            time_remaining=time_remaining,
            expected_duration=signal_data.get('expected_duration', 45),
            # Signal vitality data (NEW)
            signal_age_minutes=vitality_data['age_minutes'],
            vitality_percentage=vitality_data['vitality_percentage'],
            vitality_status=vitality_data['vitality_status'],
            vitality_icon=vitality_data['vitality_icon'],
            xp_bonus_multiplier=vitality_data['xp_bonus_multiplier'],
            decay_rate=vitality_data['decay_rate'],
            execution_blocked=vitality_data['execution_blocked'],
            slippage_warning=vitality_data['slippage_warning'],
            # Social proof
            active_operators=signal_data.get('active_traders', 0),
            total_engaged=signal_data.get('total_engaged', 0),
            squad_avg_tcs=signal_data.get('squad_avg_tcs', 70.0),
            success_rate=signal_data.get('success_rate', 0.65),
            required_tier=self._get_required_tier(mission_type, urgency),
            tier_benefits=tier_benefits,
            visual_style=visual_style,
            emoji_set=emoji_set,
            color_scheme=color_scheme,
            technical_levels=technical_levels,
            market_intel=market_intel,
            risk_warnings=risk_warnings
        )
        
        # Add smart timer data if available
        if signal_data.get('countdown_minutes'):
            # Store smart timer metadata
            smart_timer_data = {
                'enabled': True,
                'countdown_minutes': signal_data.get('countdown_minutes'),
                'countdown_seconds': signal_data.get('countdown_seconds', signal_data['countdown_minutes'] * 60),
                'timer_status': signal_data.get('timer_status', '⏱️ Normal timing'),
                'timer_factors': signal_data.get('timer_factors', {}),
                'original_timer': signal_data.get('original_timer', 45)
            }
            
            # Add to market intel
            timer_status = signal_data.get('timer_status', '')
            if '⚡' in timer_status:
                briefing.market_intel.append(f"⏱️ {timer_status} - market conditions require quick action")
            elif '🐢' in timer_status:
                briefing.market_intel.append(f"⏱️ {timer_status} - extra time to analyze this setup")
        
        # Integrate Norman's story if user_id provided
        if user_id and norman_story_engine:
            # Create enhanced briefing data
            briefing_dict = asdict(briefing)
            trading_context = {
                'days_active': signal_data.get('user_days_active', 0),
                'total_trades': signal_data.get('user_total_trades', 0),
                'win_rate': signal_data.get('user_win_rate', 0.0)
            }
            
            # Get story enhancements
            enhanced_data = integrate_norman_story(briefing_dict, user_id, trading_context)
            
            # Apply enhancements to briefing
            if enhanced_data.get('wisdom_note'):
                briefing.market_intel.append(f"🏠 {enhanced_data['wisdom_note']}")
            
            if enhanced_data.get('cultural_element'):
                briefing.market_intel.append(f"🌾 {enhanced_data['cultural_element']}")
            
            if enhanced_data.get('bit_presence'):
                bit_msg = enhanced_data['bit_presence'].get('message', '')
                if bit_msg:
                    briefing.market_intel.append(f"🐱 {bit_msg}")
        
        # Start timer expiry monitoring if available
        if TIMER_INTEGRATION_AVAILABLE and timer_expiry_integration:
            briefing_dict = asdict(briefing) if not isinstance(briefing, dict) else briefing
            briefing_dict['mission_id'] = mission_id
            briefing_dict['symbol'] = signal_data['symbol']
            briefing_dict['direction'] = signal_data['direction']
            briefing_dict['entry_price'] = entry
            briefing_dict['stop_loss'] = sl
            briefing_dict['take_profit'] = tp
            briefing_dict['tcs_score'] = signal_data.get('tcs_score', 75)
            
            # Start monitoring for expiry
            timer_expiry_integration.start_monitoring(briefing_dict)
            logger.info(f"Started timer expiry monitoring for mission {mission_id}")
        
        return briefing
    
    def format_for_webapp(self, briefing: MissionBriefing) -> Dict:
        """Format mission briefing for WebApp consumption"""
        # Convert dataclass to dict
        data = asdict(briefing)
        
        # Convert enums to values
        data['mission_type'] = briefing.mission_type.value
        data['urgency'] = briefing.urgency.value
        
        # Add formatted strings
        data['formatted'] = {
            'entry_price': f"{briefing.entry_price:.5f}",
            'stop_loss': f"{briefing.stop_loss:.5f}",
            'take_profit': f"{briefing.take_profit:.5f}",
            'risk_reward': f"1:{briefing.risk_reward_ratio}",
            'time_remaining': self._format_time_remaining(briefing.time_remaining),
            'confidence_bar': self._create_confidence_bar(briefing.tcs_score),
            'urgency_color': self._get_urgency_color(briefing.urgency)
        }
        
        # Add smart timer data if available
        if hasattr(briefing, 'smart_timer') or data.get('smart_timer'):
            data['has_smart_timer'] = True
            data['timer_display'] = {
                'type': 'smart',
                'countdown_seconds': data.get('time_remaining', briefing.time_remaining),
                'status': data.get('smart_timer', {}).get('timer_status', '⏱️ Normal timing')
            }
        else:
            data['has_smart_timer'] = False
            data['timer_display'] = {
                'type': 'standard',
                'countdown_seconds': briefing.time_remaining
            }
        
        # Add vitality display data (NEW)
        data['vitality_display'] = {
            'icon': briefing.vitality_icon,
            'status': briefing.vitality_status,
            'percentage': f"{briefing.vitality_percentage:.0f}%",
            'age': f"{briefing.signal_age_minutes} min",
            'xp_bonus': f"{briefing.xp_bonus_multiplier}x XP" if briefing.xp_bonus_multiplier > 0 else "No XP",
            'can_execute': not briefing.execution_blocked,
            'warning': briefing.slippage_warning,
            'decay_info': briefing.decay_rate
        }
        
        # Add visual elements
        data['visuals'] = {
            'progress_bars': {
                'tcs': self._create_progress_bar(briefing.tcs_score, 100),
                'time': self._create_progress_bar(briefing.time_remaining, 600),
                'squad': self._create_progress_bar(briefing.active_operators, 50)
            },
            'indicators': {
                'trend': self._get_trend_indicator(briefing.direction),
                'strength': self._get_strength_indicator(briefing.tcs_score),
                'risk': self._get_risk_indicator(briefing.risk_pips)
            }
        }
        
        # Add quick actions
        data['quick_actions'] = self._get_quick_actions(briefing)
        
        # Add user notes for this symbol if available
        try:
            from .normans_notebook import NormansNotebook
            if hasattr(self, 'user_id') and self.user_id:
                notebook = NormansNotebook(user_id=self.user_id)
                symbol_notes = notebook.get_notes_by_symbol(briefing.symbol)
                data['user_notes'] = {
                    'symbol_notes': symbol_notes[:3],  # Show top 3 recent notes
                    'has_more': len(symbol_notes) > 3,
                    'total_count': len(symbol_notes)
                }
            else:
                data['user_notes'] = {'symbol_notes': [], 'has_more': False, 'total_count': 0}
        except ImportError:
            data['user_notes'] = {'symbol_notes': [], 'has_more': False, 'total_count': 0}
        
        return data
    
    def generate_telegram_preview(self, briefing: MissionBriefing) -> str:
        """Generate short preview for Telegram alert with Norman's touch"""
        emoji = briefing.emoji_set.split()[0]  # Get first emoji
        
        # Add occasional Norman's wisdom to previews
        norman_touch = ""
        if random.random() < 0.3:
            quick_wisdom = [
                "🏠 For family and future",
                "🐱 Bit approves", 
                "💪 Delta strong",
                "⭐ Mississippi magic",
                "🌟 Dreams in motion"
            ]
            norman_touch = f"\n{random.choice(quick_wisdom)}"
        
        preview = f"{emoji} **{briefing.callsign}**\n"
        preview += f"{briefing.symbol} | {briefing.direction} | {briefing.tcs_score}% confidence\n"
        preview += f"⏰ {self._format_time_remaining(briefing.time_remaining)}{norman_touch}"
        
        return preview
    
    def _determine_mission_type(self, signal_data: Dict) -> MissionType:
        """Determine mission type from signal characteristics"""
        signal_type = signal_data.get('type', 'arcade')
        
        if signal_type == 'sniper':
            return MissionType.SNIPER_SHOT
        elif signal_type == 'midnight_hammer':
            return MissionType.MIDNIGHT_HAMMER
        elif signal_type == 'chaingun':
            return MissionType.CHAINGUN_SEQUENCE
        else:
            return MissionType.RAPID_ASSAULT_SCALP
    
    def _calculate_urgency(self, time_remaining: int) -> UrgencyLevel:
        """Calculate urgency based on time remaining"""
        if time_remaining < 120:  # < 2 minutes
            return UrgencyLevel.CRITICAL
        elif time_remaining < 300:  # < 5 minutes
            return UrgencyLevel.HIGH
        elif time_remaining < 600:  # < 10 minutes
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW
    
    def _get_callsign(self, mission_type: MissionType) -> str:
        """Get random callsign for mission type"""
        import random
        callsigns = self.callsign_pool.get(mission_type, ["TACTICAL OPERATION"])
        return random.choice(callsigns)
    
    def _analyze_market_conditions(self, market_data: Dict) -> Dict[str, Any]:
        """Analyze current market conditions"""
        return {
            'volatility': market_data.get('volatility', 'NORMAL'),
            'trend': market_data.get('trend', 'NEUTRAL'),
            'momentum': market_data.get('momentum', 'STABLE'),
            'volume': market_data.get('volume', 'AVERAGE'),
            'session': market_data.get('session', 'LONDON'),
            'key_levels': market_data.get('key_levels', [])
        }
    
    def _get_tier_benefits(self, user_tier: str, mission_type: MissionType) -> Dict[str, Any]:
        """Get tier-specific benefits for mission"""
        benefits = {
            "USER": {
                "access_delay": 60,  # 1 minute delay
                "partial_intel": True,
                "execution_limit": 1,
                "risk_multiplier": 0.5
            },
            "AUTHORIZED": {
                "access_delay": 0,
                "partial_intel": False,
                "execution_limit": 3,
                "risk_multiplier": 1.0
            },
            "ELITE": {
                "access_delay": 0,
                "partial_intel": False,
                "execution_limit": 6,
                "risk_multiplier": 1.5,
                "priority_execution": True,
                "advanced_intel": True
            },
            "ADMIN": {
                "access_delay": 0,
                "partial_intel": False,
                "execution_limit": -1,  # Unlimited
                "risk_multiplier": 2.0,
                "priority_execution": True,
                "advanced_intel": True,
                "system_override": True
            }
        }
        
        tier_benefits = benefits.get(user_tier, benefits["USER"])
        
        # Add mission-specific benefits
        if mission_type == MissionType.SNIPER_SHOT:
            if user_tier in ["ELITE", "ADMIN"]:
                tier_benefits["sniper_access"] = True
                tier_benefits["enhanced_tp"] = 1.2  # 20% larger TP
        
        return tier_benefits
    
    def _calculate_technical_levels(self, signal_data: Dict, market_data: Dict) -> Dict[str, float]:
        """Calculate key technical levels"""
        entry = signal_data['entry_price']
        
        levels = {
            'entry': entry,
            'stop_loss': signal_data['stop_loss'],
            'take_profit': signal_data['take_profit'],
            'breakeven': entry,
            'pivot': market_data.get('pivot', entry),
            'resistance_1': market_data.get('r1', entry + 0.0010),
            'resistance_2': market_data.get('r2', entry + 0.0020),
            'support_1': market_data.get('s1', entry - 0.0010),
            'support_2': market_data.get('s2', entry - 0.0020)
        }
        
        return levels
    
    def _generate_market_intel(self, signal_data: Dict, market_data: Dict, conditions: Dict) -> List[str]:
        """Generate market intelligence points with Norman's story elements"""
        intel = []
        
        # Add Bit's presence based on market conditions
        bit_mood = self._determine_bit_mood(conditions, signal_data)
        if bit_mood:
            intel.append(f"🐱 {bit_mood}")
        
        # Trend intel with cultural metaphors
        if conditions['trend'] == 'BULLISH':
            intel.append("📈 Strong uptrend - like spring floods in the Delta, rising waters lift all boats")
        elif conditions['trend'] == 'BEARISH':
            intel.append("📉 Downtrend active - winter has come, smart traders find shelter")
        
        # Volatility intel with weather wisdom
        if conditions['volatility'] == 'HIGH':
            intel.append("⚡ High volatility - storm's brewing, as Grandmama said: 'Bend with the wind'")  
        elif conditions['volatility'] == 'LOW':
            intel.append("💤 Low volatility - calm before opportunity, patience pays")
        
        # Session intel with personal touches
        session = conditions['session']
        if session == 'LONDON':
            intel.append("🇬🇧 London session - prime time, like morning on the farm")
        elif session == 'NEWYORK':
            intel.append("🇺🇸 New York session - where dreams are made, stay sharp")
        elif session == 'ASIAN':
            intel.append("🇯🇵 Asian session - quiet hours, time to plan your next move")
        
        # Technical intel with family wisdom
        if signal_data.get('near_resistance'):
            intel.append("⚠️ Approaching key resistance - Mama always said 'Know when to stop pushing'")
        if signal_data.get('near_support'):
            intel.append("🛡️ Near strong support - standing on solid ground, like home")
        
        # Add occasional family wisdom
        if random.random() < 0.3:
            wisdom_type = random.choice(['grandmother', 'mother', 'work_ethic'])
            wisdom = random.choice(self.norman_story.family_wisdom[wisdom_type])
            intel.append(f"💭 {wisdom}")
        
        return intel
    
    def _generate_risk_warnings(self, signal_data: Dict, conditions: Dict) -> List[str]:
        """Generate risk warnings with Norman's protective wisdom"""
        warnings = []
        
        # High volatility warning with Bit's caution
        if conditions['volatility'] == 'HIGH':
            bit_warning = random.choice(self.norman_story.bit_presence['caution'])
            warnings.append(f"⚠️ High volatility - {bit_warning}")
        
        # News warning with family wisdom
        if signal_data.get('news_pending'):
            warnings.append("📰 Major news event < 30 minutes - Mama taught us to prepare for storms")
        
        # Correlation warning
        if signal_data.get('correlated_risk'):
            warnings.append("🔗 Correlated pairs - remember: 'Don't put all eggs in one basket'")
        
        # Time warning with Delta wisdom
        if signal_data.get('end_of_session'):
            warnings.append("⏰ Session ending - like sunset on the Delta, time to head home")
        
        # Risk/reward warning with hard-earned lessons
        rr_ratio = signal_data.get('risk_reward_ratio', 0)
        if rr_ratio < 1.5:
            warnings.append("📊 Low R:R ratio - Grandmama said 'Don't chase pennies in front of dollars'")
        
        # Add protective wisdom occasionally
        if random.random() < 0.4:
            protection_wisdom = [
                "🛡️ Protect your capital like you'd protect your family",
                "💰 Every dollar risked is a dollar earned through sacrifice",
                "🏠 Think of home before making big decisions",
                "❤️ Your family needs you trading another day"
            ]
            warnings.append(random.choice(protection_wisdom))
        
        return warnings
    
    def _get_visual_style(self, mission_type: MissionType) -> str:
        """Get visual style for mission type"""
        styles = {
            MissionType.RAPID_ASSAULT_SCALP: "arcade",
            MissionType.SNIPER_SHOT: "sniper",
            MissionType.MIDNIGHT_HAMMER: "midnight",
            MissionType.CHAINGUN_SEQUENCE: "arcade",
            MissionType.TACTICAL_RETREAT: "sniper"
        }
        return styles.get(mission_type, "arcade")
    
    def _get_emoji_set(self, mission_type: MissionType, urgency: UrgencyLevel) -> str:
        """Get emoji set for mission and urgency"""
        emoji_sets = {
            MissionType.RAPID_ASSAULT_SCALP: {
                UrgencyLevel.CRITICAL: "🚨 🎮 ⚡",
                UrgencyLevel.HIGH: "⚡ 🎮 🎯",
                UrgencyLevel.MEDIUM: "🎯 🎮 📊",
                UrgencyLevel.LOW: "📊 🎮 💫"
            },
            MissionType.SNIPER_SHOT: {
                UrgencyLevel.CRITICAL: "🚨 🎯 🔥",
                UrgencyLevel.HIGH: "⚡ 🎯 💥",
                UrgencyLevel.MEDIUM: "🎯 🔭 📍",
                UrgencyLevel.LOW: "🔭 🎯 🌟"
            },
            MissionType.MIDNIGHT_HAMMER: {
                UrgencyLevel.CRITICAL: "🔨 🚨 💥",
                UrgencyLevel.HIGH: "🔨 ⚡ 🔥",
                UrgencyLevel.MEDIUM: "🔨 💪 ⭐",
                UrgencyLevel.LOW: "🔨 🌙 ✨"
            }
        }
        
        return emoji_sets.get(mission_type, {}).get(urgency, "📊 📈 💹")
    
    def _get_required_tier(self, mission_type: MissionType, urgency: UrgencyLevel) -> str:
        """Determine required tier for mission access"""
        if mission_type == MissionType.SNIPER_SHOT:
            return "ELITE"
        elif mission_type == MissionType.MIDNIGHT_HAMMER:
            return "AUTHORIZED"
        elif urgency == UrgencyLevel.CRITICAL:
            return "AUTHORIZED"
        else:
            return "USER"
    
    def _format_time_remaining(self, seconds: int) -> str:
        """Format time remaining in human readable format"""
        if seconds <= 0:
            return "EXPIRED"
        elif seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def _create_confidence_bar(self, score: int) -> str:
        """Create visual confidence bar"""
        filled = score // 10
        empty = 10 - filled
        
        if score >= 90:
            return "🟩" * filled + "⬜" * empty + " ELITE"
        elif score >= 80:
            return "🟨" * filled + "⬜" * empty + " HIGH"
        elif score >= 70:
            return "🟧" * filled + "⬜" * empty + " GOOD"
        else:
            return "🟥" * filled + "⬜" * empty + " STANDARD"
    
    def _create_progress_bar(self, current: float, maximum: float) -> Dict:
        """Create progress bar data"""
        percentage = min(100, (current / maximum) * 100) if maximum > 0 else 0
        
        return {
            'percentage': percentage,
            'current': current,
            'maximum': maximum,
            'filled': int(percentage / 10),
            'empty': 10 - int(percentage / 10)
        }
    
    def _get_urgency_color(self, urgency: UrgencyLevel) -> str:
        """Get color for urgency level"""
        colors = {
            UrgencyLevel.CRITICAL: "#ff073a",
            UrgencyLevel.HIGH: "#ff6b35",
            UrgencyLevel.MEDIUM: "#ffb700",
            UrgencyLevel.LOW: "#00d4ff"
        }
        return colors.get(urgency, "#ffffff")
    
    def _get_trend_indicator(self, direction: str) -> str:
        """Get trend indicator for direction"""
        return "↗️" if direction == "BUY" else "↘️"
    
    def _get_strength_indicator(self, tcs_score: int) -> str:
        """Get strength indicator based on TCS"""
        if tcs_score >= 90:
            return "💪💪💪"
        elif tcs_score >= 80:
            return "💪💪"
        elif tcs_score >= 70:
            return "💪"
        else:
            return "👊"
    
    def _get_risk_indicator(self, risk_pips: int) -> str:
        """Get risk level indicator"""
        if risk_pips <= 10:
            return "🟢 LOW"
        elif risk_pips <= 20:
            return "🟡 MEDIUM"
        elif risk_pips <= 30:
            return "🟠 HIGH"
        else:
            return "🔴 EXTREME"
    
    def _get_quick_actions(self, briefing: MissionBriefing) -> List[Dict]:
        """Get quick action buttons for mission"""
        actions = [
            {
                'id': 'execute',
                'label': '🔫 EXECUTE',
                'color': briefing.color_scheme['primary'],
                'action': 'execute_trade'
            },
            {
                'id': 'analyze',
                'label': '📊 ANALYZE',
                'color': briefing.color_scheme['info'],
                'action': 'view_analysis'
            }
        ]
        
        # Add tier-specific actions
        if briefing.tier_benefits.get('advanced_intel'):
            actions.append({
                'id': 'intel',
                'label': '🔍 ADV INTEL',
                'color': briefing.color_scheme['secondary'],
                'action': 'view_advanced_intel'
            })
        
        # Add risk management actions
        if briefing.risk_pips > 20:
            actions.append({
                'id': 'adjust_risk',
                'label': '⚠️ ADJUST RISK',
                'color': briefing.color_scheme['warning'],
                'action': 'adjust_risk_params'
            })
        
        return actions
    
    def _determine_bit_mood(self, conditions: Dict, signal_data: Dict) -> Optional[str]:
        """Determine Bit's presence and mood based on market conditions"""
        confidence = signal_data.get('tcs_score', 70)
        volatility = conditions.get('volatility', 'NORMAL')
        
        # High confidence trades - Bit is confident
        if confidence >= 85:
            return random.choice(self.norman_story.bit_presence['confidence'])
        
        # Risky conditions - Bit is cautious
        elif volatility == 'HIGH' or confidence < 70:
            return random.choice(self.norman_story.bit_presence['caution'])
        
        # Moderate conditions - occasional comfort
        elif random.random() < 0.2:
            return random.choice(self.norman_story.bit_presence['comfort'])
        
        return None
    
    def _add_norman_context_to_callsign(self, callsign: str, mission_type: MissionType) -> str:
        """Add Norman's story context to mission callsigns when appropriate"""
        # Occasionally add context that hints at Norman's journey
        context_additions = {
            'tactical': " - Delta Protocol",
            'family': " - For the Family", 
            'journey': " - Mississippi Rising",
            'wisdom': " - Grandmama's Blessing"
        }
        
        if random.random() < 0.15:  # 15% chance for context
            context_type = random.choice(list(context_additions.keys()))
            return f"{callsign}{context_additions[context_type]}"
        
        return callsign
    
    def _get_norman_enhanced_callsign(self, mission_type: MissionType) -> str:
        """Get callsign with potential Norman story enhancement"""
        callsign = self._get_callsign(mission_type)
        return self._add_norman_context_to_callsign(callsign, mission_type)

# Testing
if __name__ == "__main__":
    generator = MissionBriefingGenerator()
    
    # Test signal data
    test_signal = {
        'type': 'arcade',
        'symbol': 'GBPUSD',
        'direction': 'buy',
        'entry_price': 1.27650,
        'stop_loss': 1.27450,
        'take_profit': 1.27950,
        'tcs_score': 87,
        'confidence': 0.87,
        'expires_at': int(time.time()) + 300,  # 5 minutes
        'expected_duration': 45,
        'active_traders': 12,
        'total_engaged': 45,
        'squad_avg_tcs': 82.5,
        'success_rate': 0.73
    }
    
    # Test market data
    test_market = {
        'volatility': 'NORMAL',
        'trend': 'BULLISH',
        'momentum': 'STRONG',
        'volume': 'HIGH',
        'session': 'LONDON',
        'pivot': 1.27600,
        'r1': 1.27800,
        'r2': 1.28000,
        's1': 1.27400,
        's2': 1.27200
    }
    
    # Generate briefing
    briefing = generator.generate_mission_briefing(test_signal, test_market, "ELITE")
    
    # Test telegram preview
    print("=== TELEGRAM PREVIEW ===")
    print(generator.generate_telegram_preview(briefing))
    
    # Test webapp format
    print("\n=== WEBAPP DATA ===")
    webapp_data = generator.format_for_webapp(briefing)
    print(json.dumps(webapp_data, indent=2))