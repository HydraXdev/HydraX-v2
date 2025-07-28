# session_multiplier.py
# BITTEN Session Multiplier System - Market Timing Intelligence

from typing import Dict, List, Tuple, Optional
from datetime import datetime, time
from dataclasses import dataclass
from enum import Enum
import pytz

class MarketSession(Enum):
    ASIAN = "asian"
    LONDON = "london"
    NY = "ny"
    OVERLAP = "overlap"
    DEAD = "dead"

@dataclass
class SessionConfig:
    """Session configuration and characteristics"""
    name: str
    hours: Tuple[int, int]  # Start, end hour in EST
    multiplier: float
    description: str
    best_pairs: List[str]
    volume_profile: str
    
class SessionMultiplierSystem:
    """
    Adjusts signal quality based on market session
    
    Different sessions have different characteristics:
    - Volume levels
    - Volatility patterns
    - Directional clarity
    - Institutional participation
    """
    
    def __init__(self):
        # Session definitions (EST timezone)
        self.sessions = {
            MarketSession.ASIAN: SessionConfig(
                name="ASIAN",
                hours=(19, 3),  # 7 PM - 3 AM EST
                multiplier=0.85,
                description="Lower volume, tighter ranges",
                best_pairs=["USDJPY", "AUDJPY", "EURJPY", "AUDUSD", "NZDUSD"],
                volume_profile="LOW"
            ),
            MarketSession.LONDON: SessionConfig(
                name="LONDON",
                hours=(3, 11),  # 3 AM - 11 AM EST
                multiplier=1.15,
                description="Highest volume, best breakouts",
                best_pairs=["GBPUSD", "EURUSD", "GBPJPY", "EURGBP", "GBPCHF"],
                volume_profile="VERY HIGH"
            ),
            MarketSession.NY: SessionConfig(
                name="NEW YORK",
                hours=(8, 17),  # 8 AM - 5 PM EST
                multiplier=1.10,
                description="High volume, good trends",
                best_pairs=["EURUSD", "GBPUSD", "USDCAD", "USDCHF", "USDJPY"],
                volume_profile="HIGH"
            ),
            MarketSession.OVERLAP: SessionConfig(
                name="LONDON/NY OVERLAP",
                hours=(8, 11),  # 8 AM - 11 AM EST
                multiplier=1.20,
                description="Maximum volume period",
                best_pairs=["ALL MAJORS"],
                volume_profile="MAXIMUM"
            ),
            MarketSession.DEAD: SessionConfig(
                name="DEAD ZONE",
                hours=(17, 19),  # 5 PM - 7 PM EST
                multiplier=0.75,
                description="Avoid - low volume",
                best_pairs=["NONE RECOMMENDED"],
                volume_profile="MINIMAL"
            )
        }
        
        # Pair-specific bonuses
        self.pair_session_bonus = {
            "GBPUSD": {MarketSession.LONDON: 0.05, MarketSession.OVERLAP: 0.08},
            "EURUSD": {MarketSession.OVERLAP: 0.05, MarketSession.LONDON: 0.03},
            "USDJPY": {MarketSession.ASIAN: 0.05, MarketSession.NY: 0.03},
            "GBPJPY": {MarketSession.LONDON: 0.05, MarketSession.ASIAN: 0.03},
            "USDCAD": {MarketSession.NY: 0.05, MarketSession.OVERLAP: 0.03},
            "AUDUSD": {MarketSession.ASIAN: 0.05},
            "NZDUSD": {MarketSession.ASIAN: 0.05}}
        
        # Strategy-specific session preferences
        self.strategy_session_bonus = {
            "london_breakout": {MarketSession.LONDON: 0.10},
            "momentum": {MarketSession.OVERLAP: 0.08, MarketSession.LONDON: 0.05},
            "mean_reversion": {MarketSession.ASIAN: 0.08},
            "support_resistance": {MarketSession.LONDON: 0.05, MarketSession.NY: 0.05}
        }
    
    def get_current_session(self, timezone: str = "US/Eastern") -> MarketSession:
        """Determine current market session"""
        
        # Get current time in EST
        est = pytz.timezone(timezone)
        current_time = datetime.now(est)
        current_hour = current_time.hour
        
        # Check overlap first (highest priority)
        overlap_config = self.sessions[MarketSession.OVERLAP]
        if overlap_config.hours[0] <= current_hour < overlap_config.hours[1]:
            return MarketSession.OVERLAP
        
        # Check other sessions
        for session, config in self.sessions.items():
            if session == MarketSession.OVERLAP:
                continue
                
            start, end = config.hours
            
            # Handle sessions that cross midnight
            if start > end:  # e.g., Asian session 19-3
                if current_hour >= start or current_hour < end:
                    return session
            else:
                if start <= current_hour < end:
                    return session
        
        return MarketSession.DEAD
    
    def apply_session_multiplier(self, base_tcs: int, pair: str, 
                               strategy: Optional[str] = None) -> Dict:
        """
        Modifies TCS based on current session
        
        Returns enhanced signal data with session adjustments
        """
        
        current_session = self.get_current_session()
        session_config = self.sessions[current_session]
        
        # Base multiplier from session
        session_multiplier = session_config.multiplier
        
        # Apply pair-specific bonus
        if pair in self.pair_session_bonus:
            pair_bonus = self.pair_session_bonus[pair].get(current_session, 0)
            session_multiplier += pair_bonus
        
        # Apply strategy-specific bonus
        if strategy and strategy in self.strategy_session_bonus:
            strategy_bonus = self.strategy_session_bonus[strategy].get(current_session, 0)
            session_multiplier += strategy_bonus
        
        # Calculate final TCS
        adjusted_tcs = int(base_tcs * session_multiplier)
        adjusted_tcs = min(100, adjusted_tcs)  # Cap at 100
        
        # Determine quality label
        quality_label = self._get_quality_label(session_multiplier)
        
        # Build warning if in poor session
        warnings = []
        if session_multiplier < 0.9:
            warnings.append(f"Poor session for trading: {session_config.description}")
        if pair not in session_config.best_pairs and "ALL MAJORS" not in session_config.best_pairs:
            warnings.append(f"{pair} not optimal for {session_config.name} session")
        
        return {
            "original_tcs": base_tcs,
            "session": current_session.value,
            "session_name": session_config.name,
            "multiplier": round(session_multiplier, 2),
            "adjusted_tcs": adjusted_tcs,
            "session_quality": quality_label,
            "volume_profile": session_config.volume_profile,
            "best_pairs": session_config.best_pairs,
            "warnings": warnings,
            "description": session_config.description
        }
    
    def _get_quality_label(self, multiplier: float) -> str:
        """Get quality label with emoji"""
        if multiplier >= 1.15:
            return "🔥 PRIME TIME"
        elif multiplier >= 1.05:
            return "✅ GOOD"
        elif multiplier >= 0.95:
            return "⚡ NORMAL"
        elif multiplier >= 0.85:
            return "⚠️ CAUTION"
        else:
            return "❌ AVOID"
    
    def get_session_schedule(self) -> str:
        """Get formatted session schedule for display"""
        
        schedule = "📅 **MARKET SESSIONS (EST)**\n\n"
        
        # Sort sessions by start time
        sorted_sessions = sorted(
            [(s, c) for s, c in self.sessions.items()],
            key=lambda x: x[1].hours[0]
        )
        
        for session, config in sorted_sessions:
            start_hour = config.hours[0]
            end_hour = config.hours[1]
            
            # Format hours
            start_str = f"{start_hour:02d}:00"
            end_str = f"{end_hour:02d}:00"
            
            if start_hour > end_hour:  # Crosses midnight
                time_str = f"{start_str} - {end_str} (+1)"
            else:
                time_str = f"{start_str} - {end_str}"
            
            quality = self._get_quality_label(config.multiplier)
            
            schedule += f"{quality}\n"
            schedule += f"**{config.name}** ({time_str})\n"
            schedule += f"Multiplier: {config.multiplier}x | Volume: {config.volume_profile}\n"
            schedule += f"Best: {', '.join(config.best_pairs[:3])}\n\n"
        
        return schedule
    
    def get_best_trading_times(self, pair: str) -> List[Dict]:
        """Get best times to trade a specific pair"""
        
        best_times = []
        
        for session, config in self.sessions.items():
            if session == MarketSession.DEAD:
                continue
                
            score = config.multiplier
            
            # Add pair bonus
            if pair in config.best_pairs or "ALL MAJORS" in config.best_pairs:
                score += 0.1
            
            # Add specific pair bonus
            if pair in self.pair_session_bonus:
                score += self.pair_session_bonus[pair].get(session, 0)
            
            best_times.append({
                'session': session.value,
                'name': config.name,
                'hours': config.hours,
                'score': round(score, 2),
                'description': config.description
            })
        
        # Sort by score
        best_times.sort(key=lambda x: x['score'], reverse=True)
        
        return best_times
    
    def should_trade_now(self, pair: str, min_multiplier: float = 0.9) -> Tuple[bool, str]:
        """Quick check if current session is good for trading"""
        
        current_session = self.get_current_session()
        session_config = self.sessions[current_session]
        
        # Get effective multiplier for this pair
        multiplier = session_config.multiplier
        if pair in self.pair_session_bonus:
            multiplier += self.pair_session_bonus[pair].get(current_session, 0)
        
        if multiplier >= min_multiplier:
            return True, f"Good session: {session_config.name} ({multiplier:.2f}x)"
        else:
            return False, f"Poor session: {session_config.name} ({multiplier:.2f}x) - Consider waiting"