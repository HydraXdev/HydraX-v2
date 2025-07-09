# strategy_validator.py
# BITTEN Strategy Validation Engine - The Final Filter

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from .strategy_base import TradingSignal, SignalDirection, MarketSession

@dataclass
class ValidationResult:
    """Strategy validation result"""
    is_valid: bool
    confidence_boost: float  # -20 to +20 adjustment
    enhanced_factors: List[str]
    risk_warnings: List[str]
    kill_switches: List[str]  # Critical stop conditions

class StrategyValidator:
    """
    MASTER VALIDATION ENGINE
    
    The final filter that separates profitable trades from account destroyers.
    Based on 20+ years of painful lessons and institutional knowledge.
    """
    
    def __init__(self):
        # Kill switch conditions (NEVER trade these)
        self.news_blackout_events = {
            'NFP': 30,      # Non-Farm Payrolls ±30 mins
            'FOMC': 45,     # Fed announcements ±45 mins
            'CPI': 30,      # Consumer Price Index ±30 mins
            'GDP': 30,      # GDP releases ±30 mins
            'ECB': 45,      # ECB announcements ±45 mins
            'BOE': 30,      # Bank of England ±30 mins
        }
        
        # Market condition thresholds
        self.spread_kill_multiplier = 3.0   # Kill if spread > 3x normal
        self.volatility_kill_atr = 150      # Kill if ATR > 150 pips
        self.liquidity_kill_volume = 0.3    # Kill if volume < 30% average
        
        # Session quality scores
        self.session_quality = {
            MarketSession.LONDON: 1.0,
            MarketSession.NEW_YORK: 0.95,
            MarketSession.OVERLAP: 1.1,      # Best liquidity
            MarketSession.TOKYO: 0.8,
            MarketSession.SYDNEY: 0.7,
            MarketSession.DEAD_ZONE: 0.4,    # Avoid
        }
        
        # Multi-signal correlation (avoid same direction cluster)
        self.correlation_window_minutes = 30
        self.max_correlated_signals = 2
        
    def validate_signal(self, signal: TradingSignal, 
                       recent_signals: List[TradingSignal],
                       market_conditions: Dict) -> ValidationResult:
        """
        COMPREHENSIVE SIGNAL VALIDATION
        
        The final checkpoint before risking capital.
        """
        
        enhanced_factors = []
        risk_warnings = []
        kill_switches = []
        confidence_adjustment = 0
        
        # 1. News Event Check (CRITICAL)
        news_check = self._check_news_proximity(signal.timestamp)
        if news_check:
            kill_switches.append(f"NEWS EVENT: {news_check}")
            return ValidationResult(False, -100, [], [], kill_switches)
        
        # 2. Spread Validation
        current_spread = market_conditions.get('spread', 2.0)
        normal_spread = market_conditions.get('normal_spread', 2.0)
        if current_spread > normal_spread * self.spread_kill_multiplier:
            kill_switches.append(f"EXTREME SPREAD: {current_spread:.1f} pips")
            return ValidationResult(False, -100, [], [], kill_switches)
        elif current_spread > normal_spread * 2:
            risk_warnings.append(f"High spread: {current_spread:.1f} pips")
            confidence_adjustment -= 10
        
        # 3. Volatility Check
        current_atr = market_conditions.get('atr', 50)
        if current_atr > self.volatility_kill_atr:
            kill_switches.append(f"EXTREME VOLATILITY: {current_atr:.0f} pips ATR")
            return ValidationResult(False, -100, [], [], kill_switches)
        elif current_atr > 100:
            risk_warnings.append(f"High volatility: {current_atr:.0f} pips")
            confidence_adjustment -= 5
        elif 20 <= current_atr <= 60:
            enhanced_factors.append(f"Optimal volatility: {current_atr:.0f} pips")
            confidence_adjustment += 5
        
        # 4. Session Quality
        session_score = self.session_quality.get(signal.session, 0.5)
        if session_score >= 1.0:
            enhanced_factors.append(f"Prime session: {signal.session.value}")
            confidence_adjustment += 10
        elif session_score <= 0.5:
            risk_warnings.append(f"Poor session: {signal.session.value}")
            confidence_adjustment -= 10
        
        # 5. Signal Correlation Check
        correlation_issue = self._check_signal_correlation(signal, recent_signals)
        if correlation_issue:
            risk_warnings.append(correlation_issue)
            confidence_adjustment -= 15
        
        # 6. Risk-Reward Validation
        if signal.risk_reward_ratio >= 3.0:
            enhanced_factors.append(f"Excellent R:R: 1:{signal.risk_reward_ratio:.1f}")
            confidence_adjustment += 10
        elif signal.risk_reward_ratio >= 2.0:
            enhanced_factors.append(f"Good R:R: 1:{signal.risk_reward_ratio:.1f}")
            confidence_adjustment += 5
        elif signal.risk_reward_ratio < 1.5:
            risk_warnings.append(f"Poor R:R: 1:{signal.risk_reward_ratio:.1f}")
            confidence_adjustment -= 10
        
        # 7. Pattern Confluence (multi-strategy agreement)
        confluence_bonus = self._check_pattern_confluence(signal, market_conditions)
        if confluence_bonus > 0:
            enhanced_factors.append("Multi-pattern confluence detected")
            confidence_adjustment += confluence_bonus
        
        # 8. Time of Day Optimization
        hour = signal.timestamp.hour
        if signal.strategy_type.value == 'london_breakout' and 8 <= hour <= 9:
            enhanced_factors.append("Optimal London timing")
            confidence_adjustment += 5
        elif 22 <= hour or hour <= 6:  # Late night/early morning
            risk_warnings.append("Off-peak trading hours")
            confidence_adjustment -= 5
        
        # 9. Liquidity Validation
        volume_ratio = market_conditions.get('volume_ratio', 1.0)
        if volume_ratio < self.liquidity_kill_volume:
            kill_switches.append(f"NO LIQUIDITY: {volume_ratio:.1%} of normal")
            return ValidationResult(False, -100, [], [], kill_switches)
        elif volume_ratio > 1.5:
            enhanced_factors.append(f"High liquidity: {volume_ratio:.1f}x normal")
            confidence_adjustment += 5
        
        # Final decision
        is_valid = len(kill_switches) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            confidence_boost=confidence_adjustment,
            enhanced_factors=enhanced_factors,
            risk_warnings=risk_warnings,
            kill_switches=kill_switches
        )
    
    def _check_news_proximity(self, timestamp: datetime) -> Optional[str]:
        """Check if we're near a high-impact news event"""
        
        # In production, this would check actual economic calendar
        # For now, check standard news times
        hour = timestamp.hour
        minute = timestamp.minute
        
        # NFP (First Friday, 13:30 UTC)
        if timestamp.weekday() == 4 and hour == 13 and 0 <= minute <= 59:
            return "NFP WINDOW"
        
        # FOMC (Usually Wednesday, 18:00 UTC)
        if timestamp.weekday() == 2 and hour == 18 and 0 <= minute <= 59:
            return "FOMC WINDOW"
        
        return None
    
    def _check_signal_correlation(self, signal: TradingSignal, 
                                 recent_signals: List[TradingSignal]) -> Optional[str]:
        """Check for correlated signals (avoid overexposure)"""
        
        if not recent_signals:
            return None
        
        cutoff_time = signal.timestamp - timedelta(minutes=self.correlation_window_minutes)
        recent_same_direction = [
            s for s in recent_signals 
            if s.timestamp > cutoff_time 
            and s.direction == signal.direction
            and s.symbol == signal.symbol
        ]
        
        if len(recent_same_direction) >= self.max_correlated_signals:
            return f"Too many {signal.direction.value} signals on {signal.symbol}"
        
        return None
    
    def _check_pattern_confluence(self, signal: TradingSignal, 
                                 market_conditions: Dict) -> float:
        """Check for multiple pattern agreement"""
        
        confluence_score = 0
        
        # Check if multiple strategies would trigger
        # This is simplified - in production would run all strategies
        if signal.tcs_score >= 85:
            confluence_score += 10
        
        # Check for key level proximity
        if 'near_key_level' in market_conditions and market_conditions['near_key_level']:
            confluence_score += 5
        
        # Check for trend agreement
        if 'trend_direction' in market_conditions:
            if (market_conditions['trend_direction'] == 'up' and 
                signal.direction == SignalDirection.BUY):
                confluence_score += 5
            elif (market_conditions['trend_direction'] == 'down' and 
                  signal.direction == SignalDirection.SELL):
                confluence_score += 5
        
        return confluence_score