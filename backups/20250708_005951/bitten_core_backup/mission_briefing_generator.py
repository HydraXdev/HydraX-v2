# mission_briefing_generator.py
# BITTEN Mission Briefing Generator - Formats trade data for WebApp HUD display

import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

class MissionType(Enum):
    """Mission types based on trading strategy"""
    ARCADE_SCALP = "arcade_scalp"
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

class MissionBriefingGenerator:
    """Generates comprehensive mission briefings for WebApp HUD"""
    
    def __init__(self):
        self.mission_counter = 0
        self.callsign_pool = {
            MissionType.ARCADE_SCALP: [
                "DAWN RAID", "VORTEX AMBUSH", "LIGHTNING STRIKE", 
                "SHADOW PIERCE", "RAPID ASSAULT", "GHOST RECON"
            ],
            MissionType.SNIPER_SHOT: [
                "EAGLE EYE", "PHANTOM SHOT", "SILENT HUNTER",
                "PRECISION STRIKE", "LONG RANGE", "STEALTH OPS"
            ],
            MissionType.MIDNIGHT_HAMMER: [
                "MIDNIGHT HAMMER", "UNITED FORCE", "SQUAD ASSAULT",
                "MASS STRIKE", "COORDINATED HIT", "TEAM TAKEDOWN"
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
    
    def generate_mission_briefing(self, 
                                 signal_data: Dict,
                                 market_data: Dict,
                                 user_tier: str = "AUTHORIZED") -> MissionBriefing:
        """Generate complete mission briefing from signal and market data"""
        
        # Determine mission type
        mission_type = self._determine_mission_type(signal_data)
        
        # Calculate timing
        current_time = int(time.time())
        expires_at = signal_data.get('expires_at', current_time + 600)
        time_remaining = max(0, expires_at - current_time)
        
        # Calculate urgency
        urgency = self._calculate_urgency(time_remaining)
        
        # Get callsign
        callsign = self._get_callsign(mission_type)
        
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
        
        # Create mission briefing
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
        
        return data
    
    def generate_telegram_preview(self, briefing: MissionBriefing) -> str:
        """Generate short preview for Telegram alert"""
        emoji = briefing.emoji_set.split()[0]  # Get first emoji
        
        preview = f"{emoji} **{briefing.callsign}**\n"
        preview += f"{briefing.symbol} | {briefing.direction} | {briefing.tcs_score}% confidence\n"
        preview += f"⏰ {self._format_time_remaining(briefing.time_remaining)}"
        
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
            return MissionType.ARCADE_SCALP
    
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
        """Generate market intelligence points"""
        intel = []
        
        # Trend intel
        if conditions['trend'] == 'BULLISH':
            intel.append("📈 Strong uptrend detected - momentum favors longs")
        elif conditions['trend'] == 'BEARISH':
            intel.append("📉 Downtrend active - shorts have advantage")
        
        # Volatility intel
        if conditions['volatility'] == 'HIGH':
            intel.append("⚡ High volatility - expect rapid movements")
        elif conditions['volatility'] == 'LOW':
            intel.append("💤 Low volatility - slower price action expected")
        
        # Session intel
        session = conditions['session']
        if session == 'LONDON':
            intel.append("🇬🇧 London session - peak liquidity hours")
        elif session == 'NEWYORK':
            intel.append("🇺🇸 New York session - major news impact possible")
        elif session == 'ASIAN':
            intel.append("🇯🇵 Asian session - range-bound conditions likely")
        
        # Technical intel
        if signal_data.get('near_resistance'):
            intel.append("⚠️ Approaching key resistance level")
        if signal_data.get('near_support'):
            intel.append("🛡️ Near strong support zone")
        
        return intel
    
    def _generate_risk_warnings(self, signal_data: Dict, conditions: Dict) -> List[str]:
        """Generate risk warnings based on conditions"""
        warnings = []
        
        # High volatility warning
        if conditions['volatility'] == 'HIGH':
            warnings.append("⚠️ High volatility - use tight risk management")
        
        # News warning
        if signal_data.get('news_pending'):
            warnings.append("📰 Major news event in < 30 minutes")
        
        # Correlation warning
        if signal_data.get('correlated_risk'):
            warnings.append("🔗 Correlated pairs - avoid overexposure")
        
        # Time warning
        if signal_data.get('end_of_session'):
            warnings.append("⏰ Session ending soon - limited time window")
        
        # Risk/reward warning
        rr_ratio = signal_data.get('risk_reward_ratio', 0)
        if rr_ratio < 1.5:
            warnings.append("📊 Low R:R ratio - consider skipping")
        
        return warnings
    
    def _get_visual_style(self, mission_type: MissionType) -> str:
        """Get visual style for mission type"""
        styles = {
            MissionType.ARCADE_SCALP: "arcade",
            MissionType.SNIPER_SHOT: "sniper",
            MissionType.MIDNIGHT_HAMMER: "midnight",
            MissionType.CHAINGUN_SEQUENCE: "arcade",
            MissionType.TACTICAL_RETREAT: "sniper"
        }
        return styles.get(mission_type, "arcade")
    
    def _get_emoji_set(self, mission_type: MissionType, urgency: UrgencyLevel) -> str:
        """Get emoji set for mission and urgency"""
        emoji_sets = {
            MissionType.ARCADE_SCALP: {
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