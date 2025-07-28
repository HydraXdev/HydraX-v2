#!/usr/bin/env python3
"""
🌍 BITTEN Session-Based Pair Manager
Dynamically rotates currency pairs based on historical trading session activity
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class TradingSession:
    name: str
    start_hour: int  # UTC hour
    end_hour: int    # UTC hour
    pairs: List[str]
    boost_multiplier: float
    
class SessionBasedPairManager:
    """
    Intelligent pair selection based on trading session activity
    
    Key Features:
    - Rotates pairs based on UTC time and market sessions
    - Applies session-specific TCS threshold adjustments
    - Maximizes signal quality during peak activity periods
    - Reduces noise during low-activity periods
    """
    
    def __init__(self):
        self.sessions = self._initialize_sessions()
        self.base_config = self._load_base_config()
    
    def _initialize_sessions(self) -> List[TradingSession]:
        """Define trading sessions with optimal pairs"""
        return [
            # Asian Session: JPY pairs most active
            TradingSession(
                name="ASIAN",
                start_hour=22,  # 22:00 UTC (7:00 JST)
                end_hour=8,     # 08:00 UTC (17:00 JST)
                pairs=[
                    "USDJPY", "EURJPY", "GBPJPY", "AUDJPY", 
                    "CHFJPY", "CADJPY", "NZDJPY",
                    "AUDUSD", "NZDUSD"  # Also active during Asian session
                ],
                boost_multiplier=1.0
            ),
            
            # London Session: EUR and GBP pairs peak activity
            TradingSession(
                name="LONDON",
                start_hour=7,   # 07:00 UTC (8:00 GMT)
                end_hour=16,    # 16:00 UTC (17:00 GMT)
                pairs=[
                    "EURUSD", "GBPUSD", "EURGBP", "EURAUD",
                    "USDCHF", "EURJPY", "GBPJPY"
                ],
                boost_multiplier=2.0
            ),
            
            # NY Session: USD pairs and majors
            TradingSession(
                name="NY",
                start_hour=13,  # 13:00 UTC (8:00 EST)
                end_hour=22,    # 22:00 UTC (17:00 EST)
                pairs=[
                    "EURUSD", "GBPUSD", "USDJPY", "USDCAD",
                    "AUDUSD", "NZDUSD", "USDCHF"
                ],
                boost_multiplier=2.0
            ),
            
            # London-NY Overlap: Maximum volatility
            TradingSession(
                name="OVERLAP",
                start_hour=13,  # 13:00 UTC
                end_hour=16,    # 16:00 UTC
                pairs=[
                    "EURUSD", "GBPUSD", "USDJPY", "USDCHF"
                ],
                boost_multiplier=3.0
            )
        ]
    
    def _load_base_config(self) -> Dict:
        """Load base configuration from apex_config.json"""
        try:
            with open('apex_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "signal_generation": {
                    "min_tcs_threshold": 40,
                    "signals_per_hour_target": 1,
                    "scan_interval_seconds": 60
                }
            }
    
    def get_current_session(self) -> TradingSession:
        """Determine current trading session based on UTC time"""
        current_hour = datetime.now(timezone.utc).hour
        
        # Check for overlap first (highest priority)
        for session in self.sessions:
            if session.name == "OVERLAP":
                if self._is_hour_in_session(current_hour, session):
                    return session
        
        # Check other sessions
        for session in self.sessions:
            if session.name != "OVERLAP" and self._is_hour_in_session(current_hour, session):
                return session
        
        # Default to Asian if no session matches
        return next(s for s in self.sessions if s.name == "ASIAN")
    
    def _is_hour_in_session(self, hour: int, session: TradingSession) -> bool:
        """Check if hour falls within session time range"""
        if session.start_hour <= session.end_hour:
            # Normal range (e.g., 7-16)
            return session.start_hour <= hour < session.end_hour
        else:
            # Crosses midnight (e.g., 22-8)
            return hour >= session.start_hour or hour < session.end_hour
    
    def get_optimized_pairs(self) -> List[str]:
        """Get optimal pairs for current session"""
        current_session = self.get_current_session()
        return current_session.pairs
    
    def get_session_adjusted_threshold(self) -> float:
        """Get TCS threshold adjusted for current session activity"""
        current_session = self.get_current_session()
        base_threshold = self.base_config["signal_generation"]["min_tcs_threshold"]
        
        # Lower threshold during high-activity sessions (more signals)
        # Higher threshold during low-activity sessions (better quality)
        if current_session.boost_multiplier >= 2.0:
            # High activity: lower threshold by 10%
            return max(25, base_threshold - 10)
        else:
            # Normal/low activity: keep base threshold
            return base_threshold
    
    def get_session_info(self) -> Dict:
        """Get comprehensive session information"""
        current_session = self.get_current_session()
        return {
            "session_name": current_session.name,
            "pairs": current_session.pairs,
            "pair_count": len(current_session.pairs),
            "boost_multiplier": current_session.boost_multiplier,
            "adjusted_threshold": self.get_session_adjusted_threshold(),
            "utc_hour": datetime.now(timezone.utc).hour,
            "local_time": datetime.now().strftime("%H:%M:%S")
        }
    
    def create_session_config(self) -> Dict:
        """Create a complete config file optimized for current session"""
        session_info = self.get_session_info()
        
        # Create optimized config
        config = {
            "description": f"Session-Optimized Configuration - {session_info['session_name']} Session",
            "session_info": session_info,
            "signal_generation": {
                "signals_per_hour_target": max(1, int(session_info["boost_multiplier"])),
                "min_tcs_threshold": session_info["adjusted_threshold"],
                "max_spread_allowed": 15,
                "scan_interval_seconds": 60 if session_info["boost_multiplier"] >= 2.0 else 90
            },
            "trading_pairs": {
                "enabled": True,
                "pairs": session_info["pairs"],
                "notes": f"Optimized for {session_info['session_name']} session activity"
            },
            "session_boosts": {
                "LONDON": 2,
                "NY": 2, 
                "OVERLAP": 3,
                "ASIAN": 1,
                "OTHER": 0
            }
        }
        
        return config
    
    def apply_session_optimization(self):
        """Apply session-based optimization to config"""
        optimized_config = self.create_session_config()
        
        # Save to apex_config.json
        with open('apex_config.json', 'w') as f:
            json.dump(optimized_config, f, indent=4)
        
        return optimized_config

def apply_session_optimization():
    """Apply session-based optimization to config"""
    manager = SessionBasedPairManager()
    
    # Get optimized config
    optimized_config = manager.create_session_config()
    
    # Save to apex_config.json
    with open('apex_config.json', 'w') as f:
        json.dump(optimized_config, f, indent=4)
    
    # Print session info
    session_info = manager.get_session_info()
    print(f"🌍 SESSION OPTIMIZATION APPLIED")
    print(f"📍 Current Session: {session_info['session_name']}")
    print(f"📊 Monitoring {session_info['pair_count']} pairs: {', '.join(session_info['pairs'][:5])}...")
    print(f"🎯 Adjusted TCS Threshold: {session_info['adjusted_threshold']}%")
    print(f"🚀 Boost Multiplier: {session_info['boost_multiplier']}x")
    print(f"⏰ UTC Hour: {session_info['utc_hour']} | Local: {session_info['local_time']}")
    
    return optimized_config

if __name__ == "__main__":
    apply_session_optimization()