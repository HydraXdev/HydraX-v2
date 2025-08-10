# mission_briefing_generator_v5.py
# v5.0 Mission Briefing Generator - Optimized for ultra-aggressive trading
# 40+ signals/day @ 89% win rate with enhanced mission briefings

import json
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Import timer integrations
try:
    from ..bitten.core.smart_timer_integration import smart_timer_integration
    from ..bitten.core.timer_expiry_integration import timer_expiry_integration
    TIMER_INTEGRATION_AVAILABLE = True
except ImportError:
    smart_timer_integration = None
    timer_expiry_integration = None
    TIMER_INTEGRATION_AVAILABLE = False

class v5MissionType(Enum):
    """v5.0 Mission types optimized for ultra-aggressive trading"""
    # Original mission types
    RAPID_ASSAULT_SCALP = "arcade_scalp"
    SNIPER_SHOT = "sniper_shot"
    MIDNIGHT_HAMMER = "midnight_hammer"
    CHAINGUN_SEQUENCE = "chaingun_sequence"
    TACTICAL_RETREAT = "tactical_retreat"
    
    # v5.0 New mission types
    ULTRA_VOLUME_ASSAULT = "ultra_volume_assault"      # 40+ signals/day mode
    M3_LIGHTNING_RAID = "m3_lightning_raid"           # M3 timeframe focus
    CONFLUENCE_HUNTER = "confluence_hunter"           # 2+ pattern hunting
    SESSION_BOOST_STRIKE = "session_boost_strike"     # OVERLAP 3x boost
    VOLATILITY_MONSTER_HUNT = "volatility_monster"    # Monster pair targeting
    _BEAST_UNLEASHED = "apex_beast_unleashed"     # Maximum extraction

class v5UrgencyLevel(Enum):
    """v5.0 Enhanced urgency levels"""
    CRITICAL = "CRITICAL"      # < 1 minute (ultra-fast)
    ULTRA_HIGH = "ULTRA_HIGH"  # 1-2 minutes (v5.0 speed)
    HIGH = "HIGH"              # 2-5 minutes  
    MEDIUM = "MEDIUM"          # 5-10 minutes
    LOW = "LOW"                # > 10 minutes

class v5SignalClass(Enum):
    """v5.0 Signal classifications - Updated for RAPID/SNIPER"""
    RAPID_ASSAULT = "RAPID_ASSAULT"       # Quick scalp trades (5-45 min)
    SNIPER_OPS = "SNIPER_OPS"             # Precision trades (30-90 min)
    M1_INSTANT = "M1_INSTANT"             # M1 hair-trigger signals
    M3_PRIMARY = "M3_PRIMARY"             # M3 primary signals (60% focus)
    M5_ENHANCED = "M5_ENHANCED"           # M5 enhanced patterns
    M15_SNIPER = "M15_SNIPER"             # M15 precision shots
    MEGA_CONFLUENCE = "MEGA_CONFLUENCE"   # 2+ pattern confluence
    ULTRA_CONFLUENCE = "ULTRA_CONFLUENCE" # 4+ pattern confluence
    MONSTER_SIGNAL = "MONSTER_SIGNAL"     # Volatility monster signals

@dataclass
class v5MissionBriefing:
    """v5.0 Enhanced mission briefing data structure"""
    # Core mission data
    mission_id: str
    mission_type: v5MissionType
    urgency_level: v5UrgencyLevel
    signal_class: v5SignalClass
    
    # Signal data (enhanced for v5.0)
    symbol: str
    direction: str  # BUY/SELL
    entry_price: float
    stop_loss: float
    take_profit: float
    tcs_score: float  # Trade Confidence Score (v5.0 optimized: 35-95)
    pattern_name: str
    timeframe: str
    session: str
    confluence_count: int = 1
    
    # v5.0 Enhanced metrics
    session_boost_active: bool = False
    session_boost_multiplier: float = 1.0
    pair_type: str = "standard"  # standard, volatile, monster
    volatility_rating: str = "NORMAL"  # NORMAL, HIGH, EXTREME
    signal_velocity: str = "STANDARD"  # INSTANT, FAST, STANDARD, PRECISION
    
    # Risk management (v5.0 optimized)
    position_size: float = 0.0
    risk_amount: float = 0.0
    risk_percentage: float = 1.0  # v5.0 default 1%
    reward_risk_ratio: float = 2.0
    correlation_warning: bool = False
    
    # Timing data (enhanced)
    signal_timestamp: datetime = None
    expiry_timestamp: datetime = None
    countdown_seconds: int = 0
    execution_window: int = 300  # 5 minutes default
    
    # User data
    user_tier: str = "AUTHORIZED"
    account_balance: float = 0.0
    daily_signals_count: int = 0
    daily_pips: float = 0.0
    win_rate: float = 0.0
    
    # Display data
    mission_title: str = ""
    mission_description: str = ""
    tactical_notes: List[str] = None
    dollar_amount: float = 0.0  # Expected profit in dollars
    
    # v5.0 Performance data
    engine_version: str = "5.0"
    signals_per_day_target: int = 40
    current_session_signals: int = 0
    total_pairs_active: int = 15

class v5MissionBriefingGenerator:
    """v5.0 Mission Briefing Generator with ultra-aggressive optimizations"""
    
    def __init__(self):
        self.v5_session_names = {
            'ASIAN': {'icon': '🌅', 'boost': 1.5},
            'LONDON': {'icon': '🏴󐁧󐁢󐁥󐁮󐁧󐁿', 'boost': 2.0},
            'NY': {'icon': '🗽', 'boost': 1.8},
            'OVERLAP': {'icon': '⚡', 'boost': 3.0}  # Triple boost
        }
        
        self.v5_signal_descriptions = {
            'RAPID_ASSAULT': "Quick scalp trade - 10-45 min execution window",
            'SNIPER_OPS': "Precision trade - 30-90 min high-reward targeting",
            'M1_INSTANT': "Lightning-fast M1 hair-trigger signal",
            'M3_PRIMARY': "Primary M3 timeframe signal (60% focus)",
            'M5_ENHANCED': "Enhanced M5 pattern recognition",
            'M15_SNIPER': "High-precision M15 sniper shot",
            'MEGA_CONFLUENCE': "Multiple pattern confluence detected",
            'ULTRA_CONFLUENCE': "Ultra-rare 4+ pattern stack",
            'MONSTER_SIGNAL': "Volatility monster pair signal"
        }
        
        self.v5_pair_classifications = {
            # Major pairs
            'EURUSD': {'type': 'major', 'volatility': 'NORMAL', 'icon': '🇪🇺🇺🇸'},
            'GBPUSD': {'type': 'major', 'volatility': 'NORMAL', 'icon': '🇬🇧🇺🇸'},
            'USDJPY': {'type': 'major', 'volatility': 'NORMAL', 'icon': '🇺🇸🇯🇵'},
            'USDCAD': {'type': 'commodity', 'volatility': 'NORMAL', 'icon': '🇺🇸🇨🇦'},
            
            # Volatile pairs
            'GBPJPY': {'type': 'volatile', 'volatility': 'HIGH', 'icon': '🇬🇧🇯🇵'},
            'EURJPY': {'type': 'volatile', 'volatility': 'HIGH', 'icon': '🇪🇺🇯🇵'},
            'AUDJPY': {'type': 'volatile', 'volatility': 'HIGH', 'icon': '🇦🇺🇯🇵'},
            'GBPCHF': {'type': 'volatile', 'volatility': 'HIGH', 'icon': '🇬🇧🇨🇭'},
            
            # Standard pairs
            'AUDUSD': {'type': 'commodity', 'volatility': 'NORMAL', 'icon': '🇦🇺🇺🇸'},
            'NZDUSD': {'type': 'commodity', 'volatility': 'NORMAL', 'icon': '🇳🇿🇺🇸'},
            'USDCHF': {'type': 'safe', 'volatility': 'NORMAL', 'icon': '🇺🇸🇨🇭'},
            'EURGBP': {'type': 'cross', 'volatility': 'NORMAL', 'icon': '🇪🇺🇬🇧'},
            
            # Volatility monsters (v5.0 new)
            'GBPNZD': {'type': 'monster', 'volatility': 'EXTREME', 'icon': '🇬🇧🇳🇿⚡'},
            'GBPAUD': {'type': 'monster', 'volatility': 'EXTREME', 'icon': '🇬🇧🇦🇺⚡'},
            'EURAUD': {'type': 'monster', 'volatility': 'EXTREME', 'icon': '🇪🇺🇦🇺⚡'}
        }
        
        logger.info("v5.0 Mission Briefing Generator initialized")
    
    def generate_v5_mission_briefing(self, signal_data: Dict, user_data: Dict, 
                                   account_data: Dict) -> v5MissionBriefing:
        """Generate v5.0 enhanced mission briefing"""
        
        # Extract signal data
        symbol = signal_data.get('symbol', 'EURUSD')
        direction = signal_data.get('direction', 'BUY')
        entry_price = signal_data.get('entry_price', 1.0000)
        tcs_score = signal_data.get('tcs', 50)
        pattern_name = signal_data.get('pattern', 'Unknown')
        timeframe = signal_data.get('timeframe', 'M5')
        session = signal_data.get('session', 'NORMAL')
        confluence_count = signal_data.get('confluence_count', 1)
        
        # Generate mission ID
        timestamp = datetime.now()
        mission_id = f"5_{symbol}_{timestamp.strftime('%H%M%S')}"
        
        # Determine signal class based on pattern and timeframe
        signal_class = self._determine_v5_signal_class(pattern_name, timeframe, confluence_count, signal_data.get('signal_type'))
        
        # Determine mission type
        mission_type = self._determine_v5_mission_type(signal_class, session, tcs_score)
        
        # Determine urgency based on timeframe and TCS
        urgency_level = self._determine_v5_urgency(timeframe, tcs_score, session)
        
        # Get pair classification
        pair_info = self.v5_pair_classifications.get(symbol, {
            'type': 'standard', 'volatility': 'NORMAL', 'icon': '📊'
        })
        
        # Calculate position sizing (v5.0 enhanced) - ZERO SIMULATION ENFORCEMENT
        from ZERO_SIMULATION_ENFORCEMENT import validate_balance
        
        account_balance_raw = account_data.get('balance')
        if account_balance_raw is None:
            raise ValueError(f"🚨 CRITICAL: No real account balance available for user {user_id} - CANNOT GENERATE MISSIONS WITH FAKE DATA")
        
        account_balance = validate_balance(account_balance_raw, f"mission_generator_user_{user_id}")
        position_size, risk_amount, dollar_amount = self._calculate_v5_position_sizing(
            signal_data, account_balance, user_data.get('tier', '')
        )
        
        # Session boost detection
        session_boost_active = session in ['OVERLAP', 'LONDON']
        session_boost_multiplier = self.v5_session_names.get(session, {}).get('boost', 1.0)
        
        # Calculate countdown
        execution_window = self._get_v5_execution_window(timeframe, signal_class)
        expiry_timestamp = timestamp + timedelta(seconds=execution_window)
        countdown_seconds = execution_window
        
        # Generate mission title and description
        mission_title, mission_description = self._generate_v5_mission_content(
            signal_class, symbol, direction, tcs_score, session, confluence_count
        )
        
        # Generate tactical notes
        tactical_notes = self._generate_v5_tactical_notes(
            signal_data, pair_info, session_boost_active, confluence_count
        )
        
        # Create briefing
        briefing = v5MissionBriefing(
            mission_id=mission_id,
            mission_type=mission_type,
            urgency_level=urgency_level,
            signal_class=signal_class,
            
            # Signal data
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=signal_data.get('stop_loss', 10),
            take_profit=signal_data.get('take_profit', 20),
            tcs_score=tcs_score,
            pattern_name=pattern_name,
            timeframe=timeframe,
            session=session,
            confluence_count=confluence_count,
            
            # v5.0 Enhanced metrics
            session_boost_active=session_boost_active,
            session_boost_multiplier=session_boost_multiplier,
            pair_type=pair_info['type'],
            volatility_rating=pair_info['volatility'],
            signal_velocity=self._get_signal_velocity(timeframe),
            
            # Risk management
            position_size=position_size,
            risk_amount=risk_amount,
            risk_percentage=self._get_v5_risk_percentage(user_data.get('tier', '')),
            reward_risk_ratio=signal_data.get('take_profit', 20) / max(signal_data.get('stop_loss', 10), 1),
            
            # Timing
            signal_timestamp=timestamp,
            expiry_timestamp=expiry_timestamp,
            countdown_seconds=countdown_seconds,
            execution_window=execution_window,
            
            # User data
            user_tier=user_data.get('tier', ''),
            account_balance=account_balance,
            daily_signals_count=user_data.get('daily_signals', 0),
            daily_pips=user_data.get('daily_pips', 0.0),
            win_rate=user_data.get('win_rate', 89.0),  # v5.0 target
            
            # Display data
            mission_title=mission_title,
            mission_description=mission_description,
            tactical_notes=tactical_notes,
            dollar_amount=dollar_amount,
            
            # v5.0 Performance data
            current_session_signals=user_data.get(f'{session.lower()}_signals', 0)
        )
        
        logger.info(f"Generated v5.0 mission briefing: {mission_id} - "
                   f"{signal_class.value} - TCS {tcs_score}")
        
        return briefing
    
    def _determine_v5_signal_class(self, pattern_name: str, timeframe: str, 
                                 confluence_count: int, signal_type: str = None) -> v5SignalClass:
        """Determine v5.0 signal class - prioritizes signal_type"""
        
        # New: Use signal_type from if available
        if signal_type:
            if signal_type == "RAPID ASSAULT" or signal_type == "RAPID_ASSAULT":
                return v5SignalClass.RAPID_ASSAULT
            elif signal_type == "SNIPER OPS" or signal_type == "SNIPER_OPS":
                return v5SignalClass.SNIPER_OPS
        
        # Legacy: Confluence count determines class
        if confluence_count >= 4:
            return v5SignalClass.ULTRA_CONFLUENCE
        elif confluence_count >= 2:
            return v5SignalClass.MEGA_CONFLUENCE
        elif 'Monster' in pattern_name or 'GBPNZD' in pattern_name or 'GBPAUD' in pattern_name:
            return v5SignalClass.MONSTER_SIGNAL
        elif timeframe == 'M1':
            return v5SignalClass.M1_INSTANT
        elif timeframe == 'M3':
            return v5SignalClass.M3_PRIMARY
        elif timeframe == 'M5':
            return v5SignalClass.M5_ENHANCED
        elif timeframe == 'M15':
            return v5SignalClass.M15_SNIPER
        else:
            return v5SignalClass.M3_PRIMARY  # Default to M3
    
    def _determine_v5_mission_type(self, signal_class: v5SignalClass, 
                                 session: str, tcs_score: float) -> v5MissionType:
        """Determine v5.0 mission type"""
        
        if session == 'OVERLAP':
            return v5MissionType.SESSION_BOOST_STRIKE
        elif signal_class == v5SignalClass.ULTRA_CONFLUENCE:
            return v5MissionType.CONFLUENCE_HUNTER
        elif signal_class == v5SignalClass.MONSTER_SIGNAL:
            return v5MissionType.VOLATILITY_MONSTER_HUNT
        elif signal_class == v5SignalClass.M3_PRIMARY:
            return v5MissionType.M3_LIGHTNING_RAID
        else:
            # Use centralized threshold
            from tcs_controller import get_current_threshold
            threshold = get_current_threshold()
            if tcs_score >= (threshold + 15):
                return v5MissionType._BEAST_UNLEASHED
        elif signal_class == v5SignalClass.M1_INSTANT:
            return v5MissionType.ULTRA_VOLUME_ASSAULT
        else:
            return v5MissionType.RAPID_ASSAULT_SCALP
    
    def _determine_v5_urgency(self, timeframe: str, tcs_score: float, session: str) -> v5UrgencyLevel:
        """Determine v5.0 urgency level"""
        
        if timeframe == 'M1' or session == 'OVERLAP':
            return v5UrgencyLevel.CRITICAL
        else:
            # Use centralized threshold
            from tcs_controller import get_current_threshold
            threshold = get_current_threshold()
            if timeframe == 'M3' or tcs_score >= (threshold + 15):
                return v5UrgencyLevel.ULTRA_HIGH
            elif timeframe == 'M5' or tcs_score >= threshold:
                return v5UrgencyLevel.HIGH
        elif timeframe == 'M15':
            return v5UrgencyLevel.MEDIUM
        else:
            return v5UrgencyLevel.LOW
    
    def _calculate_v5_position_sizing(self, signal_data: Dict, account_balance: float, 
                                    tier: str) -> Tuple[float, float, float]:
        """Calculate v5.0 optimized position sizing"""
        
        # Base risk percentages by tier (v5.0 enhanced)
        tier_risk = {
            'PRESS_PASS': 0.5,
            'NIBBLER': 0.7,
            'FANG': 1.0,
            'COMMANDER': 1.2,
            'APEX': 1.5  # Higher for apex tier
        }
        
        base_risk_percent = tier_risk.get(tier, 1.0)
        
        # TCS-based multiplier (v5.0 optimized for lower TCS)
        tcs = signal_data.get('tcs', 50)
        # Use centralized threshold
        from tcs_controller import get_current_threshold
        threshold = get_current_threshold()
        if tcs >= (threshold + 15):
            tcs_mult = 1.5
        elif tcs >= (threshold + 5):
            tcs_mult = 1.3
        elif tcs >= (threshold - 5):
            tcs_mult = 1.2
        elif tcs >= (threshold - 15):
            tcs_mult = 1.1
        else:
            tcs_mult = 1.0  # v5.0 handles lower TCS
        
        # Session multiplier
        session = signal_data.get('session', 'NORMAL')
        session_mult = {
            'OVERLAP': 1.3,  # 30% bonus during triple boost
            'LONDON': 1.1,
            'NY': 1.0,
            'ASIAN': 0.9
        }.get(session, 1.0)
        
        # Confluence bonus
        confluence_count = signal_data.get('confluence_count', 1)
        if confluence_count >= 4:
            confluence_mult = 1.4
        elif confluence_count >= 2:
            confluence_mult = 1.2
        else:
            confluence_mult = 1.0
        
        # Calculate final risk
        final_risk_percent = base_risk_percent * tcs_mult * session_mult * confluence_mult
        final_risk_percent = min(final_risk_percent, 3.0)  # Cap at 3%
        
        risk_amount = account_balance * (final_risk_percent / 100)
        
        # Convert to position size (simplified)
        symbol = signal_data.get('symbol', 'EURUSD')
        sl_pips = signal_data.get('stop_loss', 10)
        tp_pips = signal_data.get('take_profit', 20)
        
        pip_value = 10 if 'JPY' in symbol else 1
        position_size = risk_amount / (sl_pips * pip_value)
        position_size = max(0.01, min(position_size, 10.0))  # Constrain to reasonable range
        
        # Calculate expected dollar profit
        dollar_amount = tp_pips * pip_value * position_size
        
        return position_size, risk_amount, dollar_amount
    
    def _get_v5_execution_window(self, timeframe: str, signal_class: v5SignalClass) -> int:
        """Get v5.0 execution window in seconds"""
        
        base_windows = {
            'M1': 60,     # 1 minute for M1
            'M3': 180,    # 3 minutes for M3
            'M5': 300,    # 5 minutes for M5
            'M15': 900    # 15 minutes for M15
        }
        
        base_window = base_windows.get(timeframe, 300)
        
        # Adjust for signal class
        if signal_class in [v5SignalClass.ULTRA_CONFLUENCEv5SignalClass.MONSTER_SIGNAL]:
            base_window *= 1.5  # Longer window for special signals
        elif signal_class == v5SignalClass.M1_INSTANT:
            base_window *= 0.5  # Shorter for instant signals
        
        return int(base_window)
    
    def _generate_v5_mission_content(self, signal_class: v5SignalClass, symbol: str,
                                   direction: str, tcs_score: float, session: str,
                                   confluence_count: int) -> Tuple[str, str]:
        """Generate v5.0 mission title and description"""
        
        pair_info = self.v5_pair_classifications.get(symbol, {'icon': '📊'})
        session_info = self.v5_session_names.get(session, {'icon': '🎯'})
        
        # Generate title based on signal class - prioritize new signal types
        if signal_class == v5SignalClass.RAPID_ASSAULT:
            title = f"🔫 RAPID ASSAULT - {symbol}"
        elif signal_class == v5SignalClass.SNIPER_OPS:
            title = f"⚡ SNIPER OPS - {symbol}"
        elif signal_class == v5SignalClass.ULTRA_CONFLUENCE:
            title = f"🔥 ULTRA CONFLUENCE x{confluence_count} - {symbol}"
        elif signal_class == v5SignalClass.MEGA_CONFLUENCE:
            title = f"⚡ MEGA CONFLUENCE x{confluence_count} - {symbol}"
        elif signal_class == v5SignalClass.MONSTER_SIGNAL:
            title = f"👹 MONSTER HUNT - {symbol}"
        elif signal_class == v5SignalClass.M1_INSTANT:
            title = f"⚡ M1 INSTANT STRIKE - {symbol}"
        elif signal_class == v5SignalClass.M3_PRIMARY:
            title = f"🎯 M3 PRIMARY ASSAULT - {symbol}"
        else:
            title = f"{session_info['icon']} {signal_class.value} - {symbol}"
        
        # Generate description
        base_desc = self.v5_signal_descriptions.get(signal_class.value, "Advanced signal detected")
        
        if session == 'OVERLAP':
            description = f"{base_desc} 🚀 TRIPLE BOOST SESSION ACTIVE! 🚀"
        elif confluence_count > 1:
            description = f"{base_desc} 🔥 {confluence_count} patterns aligned for maximum impact!"
        else:
            # Use centralized threshold
            from tcs_controller import get_current_threshold
            threshold = get_current_threshold()
            if tcs_score >= (threshold + 15):
                description = f"{base_desc} ⭐ Ultra-high confidence signal detected!"
        else:
            description = base_desc
        
        return title, description
    
    def _generate_v5_tactical_notes(self, signal_data: Dict, pair_info: Dict,
                                  session_boost_active: bool, confluence_count: int) -> List[str]:
        """Generate v5.0 tactical notes"""
        
        notes = []
        
        # v5.0 Base notes
        notes.append("🚀 v5.0 Engine: Ultra-aggressive signal generation active")
        notes.append(f"📊 Target: 40+ signals/day @ 89% win rate")
        
        # TCS notes (v5.0 optimized)
        tcs = signal_data.get('tcs', 50)
        # Use centralized threshold
        from tcs_controller import get_current_threshold
        threshold = get_current_threshold()
        if tcs >= (threshold + 15):
            notes.append("🏆 Premium TCS score - Execute with confidence")
        elif tcs >= threshold:
            notes.append("✅ Strong TCS score - Good execution candidate")
        elif tcs >= (threshold - 15):
            notes.append("⚖️ Standard TCS score - Manage risk appropriately")
        else:
            notes.append("⚡ Ultra-aggressive TCS - High volume mode active")
        
        # Session notes
        session = signal_data.get('session', 'NORMAL')
        if session == 'OVERLAP':
            notes.append("🔥 OVERLAP SESSION: 3x boost multiplier active!")
        elif session == 'LONDON':
            notes.append("🏴󐁧󐁢󐁥󐁮󐁧󐁿 London session: Enhanced volatility expected")
        elif session == 'ASIAN':
            notes.append("🌅 Asian session: JPY/AUD pairs favored")
        
        # Confluence notes
        if confluence_count >= 4:
            notes.append("💎 ULTRA CONFLUENCE: 4+ patterns aligned - Rare opportunity!")
        elif confluence_count >= 2:
            notes.append("🔥 MEGA CONFLUENCE: Multiple patterns confirmed")
        
        # Pair-specific notes
        symbol = signal_data.get('symbol', 'EURUSD')
        if pair_info.get('type') == 'monster':
            notes.append("👹 VOLATILITY MONSTER: Extreme movement potential")
        elif pair_info.get('type') == 'volatile':
            notes.append("⚡ High volatility pair: Increased profit potential")
        
        # Timeframe notes
        timeframe = signal_data.get('timeframe', 'M5')
        if timeframe == 'M1':
            notes.append("⚡ M1 timeframe: Lightning-fast execution required")
        elif timeframe == 'M3':
            notes.append("🎯 M3 timeframe: Primary signal focus (60% allocation)")
        elif timeframe == 'M15':
            notes.append("🔍 M15 timeframe: High-precision sniper signal")
        
        return notes
    
    def _get_signal_velocity(self, timeframe: str) -> str:
        """Get signal velocity classification"""
        velocity_map = {
            'M1': 'INSTANT',
            'M3': 'FAST',
            'M5': 'STANDARD',
            'M15': 'PRECISION'
        }
        return velocity_map.get(timeframe, 'STANDARD')
    
    def _get_v5_risk_percentage(self, tier: str) -> float:
        """Get v5.0 risk percentage by tier"""
        tier_risk = {
            'PRESS_PASS': 0.5,
            'NIBBLER': 0.7,
            'FANG': 1.0,
            'COMMANDER': 1.2,
            '': 1.5
        }
        return tier_risk.get(tier, 1.0)
    
    def format_for_webapp(self, briefing: v5MissionBriefing) -> Dict[str, Any]:
        """Format v5.0 briefing for webapp display"""
        
        pair_info = self.v5_pair_classifications.get(briefing.symbol, {'icon': '📊'})
        
        formatted = {
            # Core display data
            'mission_id': briefing.mission_id,
            'title': briefing.mission_title,
            'description': briefing.mission_description,
            'urgency': briefing.urgency_level.value,
            'signal_class': briefing.signal_class.value,
            
            # Signal data with v5.0 enhancements
            'pair': briefing.symbol,
            'pair_icon': pair_info.get('icon', '📊'),
            'direction': briefing.direction,
            'entry_price': f"{briefing.entry_price:.5f}",
            'stop_loss': f"{briefing.stop_loss:.1f} pips",
            'take_profit': f"{briefing.take_profit:.1f} pips",
            'tcs_score': briefing.tcs_score,
            'pattern': briefing.pattern_name,
            'timeframe': briefing.timeframe,
            'session': briefing.session,
            
            # v5.0 Enhanced display
            'session_boost': briefing.session_boost_active,
            'session_multiplier': f"{briefing.session_boost_multiplier:.1f}x",
            'confluence_count': briefing.confluence_count,
            'volatility_rating': briefing.volatility_rating,
            'signal_velocity': briefing.signal_velocity,
            'pair_type': briefing.pair_type,
            
            # Financial data
            'position_size': f"{briefing.position_size:.2f} lots",
            'risk_amount': f"${briefing.risk_amount:.2f}",
            'risk_percentage': f"{briefing.risk_percentage:.1f}%",
            'dollar_amount': f"${briefing.dollar_amount:.2f}",
            'reward_risk_ratio': f"1:{briefing.reward_risk_ratio:.1f}",
            
            # Timing data with enhanced countdown
            'countdown_seconds': briefing.countdown_seconds,
            'execution_window': briefing.execution_window,
            'expiry_time': briefing.expiry_timestamp.strftime('%H:%M:%S'),
            
            # User performance data
            'user_tier': briefing.user_tier,
            'account_balance': f"${briefing.account_balance:,.2f}",
            'daily_signals': briefing.daily_signals_count,
            'daily_pips': f"{briefing.daily_pips:.1f}",
            'win_rate': f"{briefing.win_rate:.1f}%",
            
            # v5.0 Performance metrics
            'engine_version': briefing.engine_version,
            'signals_target': briefing.signals_per_day_target,
            'session_signals': briefing.current_session_signals,
            'total_pairs': briefing.total_pairs_active,
            
            # Tactical notes
            'tactical_notes': briefing.tactical_notes,
            
            # v5.0 Status indicators
            'ultra_mode_active': True,
            'max_extraction_mode': briefing.mission_type == v5MissionType._BEAST_UNLEASHED,
            'confluence_hunter_mode': briefing.signal_class in [v5SignalClass.MEGA_CONFLUENCEv5SignalClass.ULTRA_CONFLUENCE]
        }
        
        return formatted
    
    def update_countdown(self, briefing: v5MissionBriefing) -> v5MissionBriefing:
        """Update countdown timer for v5.0 briefing"""
        current_time = datetime.now()
        remaining_seconds = max(0, int((briefing.expiry_timestamp - current_time).total_seconds()))
        
        briefing.countdown_seconds = remaining_seconds
        
        # Update urgency based on remaining time
        if remaining_seconds <= 60:
            briefing.urgency_level = v5UrgencyLevel.CRITICAL
        elif remaining_seconds <= 120:
            briefing.urgency_level = v5UrgencyLevel.ULTRA_HIGH
        elif remaining_seconds <= 300:
            briefing.urgency_level = v5UrgencyLevel.HIGH
        
        return briefing

# Factory function for backward compatibility
def generate_apex_v5_mission_briefing(signal_data: Dict, user_data: Dict, 
                                     account_data: Dict) -> v5MissionBriefing:
    """Factory function to generate v5.0 mission briefing"""
    generator = v5MissionBriefingGenerator()
    return generator.generate_v5_mission_briefing(signal_data, user_data, account_data)