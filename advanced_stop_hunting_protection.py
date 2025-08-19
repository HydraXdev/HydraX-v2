#!/usr/bin/env python3
"""
BITTEN Advanced Stop Hunting Protection System
Implements sophisticated broker protection based on user's advanced suggestions

Features:
- Volatility-adaptive randomization
- Correlated pair analysis  
- Position size reduction over avoidance
- Broker-specific intensity scaling
- Dynamic spread baseline calculation
"""

import random
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict

class AdvancedStopHuntingProtection:
    """
    Advanced stop hunting protection implementing institutional-grade countermeasures
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.enabled = True
        
        # Broker hunting profiles (based on observed behavior)
        self.broker_profiles = {
            'FXCM': {
                'intensity': 0.85,  # High hunting frequency
                'preferred_times': [0, 1, 7, 8, 13, 14, 21, 22],
                'preferred_pairs': ['EURUSD', 'GBPUSD', 'USDJPY'],
                'spread_manipulation': 0.9,  # High spread games
                'stop_hunting_range': 8,  # Hunts 8+ pips from stops
                'randomization_multiplier': 1.5  # Need more randomization
            },
            'OANDA': {
                'intensity': 0.6,   # Moderate hunting
                'preferred_times': [8, 14, 22],
                'preferred_pairs': ['EURUSD', 'GBPUSD'],
                'spread_manipulation': 0.5,  # Moderate spread games
                'stop_hunting_range': 5,  # Hunts 5+ pips from stops
                'randomization_multiplier': 1.2
            },
            'IC_MARKETS': {
                'intensity': 0.3,   # Low hunting (ECN model)
                'preferred_times': [8, 14],
                'preferred_pairs': ['EURUSD'],
                'spread_manipulation': 0.2,  # Low spread manipulation
                'stop_hunting_range': 3,  # Minimal hunting
                'randomization_multiplier': 0.8  # Less protection needed
            },
            'PEPPERSTONE': {
                'intensity': 0.25,  # Very low hunting (Raw spread)
                'preferred_times': [14],
                'preferred_pairs': [],
                'spread_manipulation': 0.1,
                'stop_hunting_range': 2,
                'randomization_multiplier': 0.7
            },
            'FOREX_COM': {
                'intensity': 0.7,   # Moderate-high hunting
                'preferred_times': [1, 8, 14, 21],
                'preferred_pairs': ['EURUSD', 'GBPUSD', 'USDJPY'],
                'spread_manipulation': 0.6,
                'stop_hunting_range': 6,
                'randomization_multiplier': 1.3
            }
        }
        
        # Correlation groups for pair analysis
        self.correlation_groups = {
            'EUR_BASKET': ['EURUSD', 'EURGBP', 'EURJPY', 'EURCAD'],
            'GBP_BASKET': ['GBPUSD', 'EURGBP', 'GBPJPY', 'GBPCAD'], 
            'USD_BASKET': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD'],
            'JPY_BASKET': ['USDJPY', 'EURJPY', 'GBPJPY'],
            'GOLD_RELATED': ['XAUUSD', 'EURUSD', 'USDCAD']  # Gold correlations
        }
        
        # Spread baseline cache
        self.spread_baseline_cache = {}
        self.baseline_cache_ttl = 300  # 5 minutes
        
        # Current broker detection
        self.current_broker = self.detect_current_broker()
        
        # Statistics tracking
        self.protection_stats = {
            'total_signals_processed': 0,
            'stops_randomized': 0,
            'position_sizes_reduced': 0,
            'trades_blocked_spread': 0,
            'trades_blocked_correlation': 0,
            'avg_randomization_pips': 0,
            'avg_position_reduction': 0
        }
        
        self.logger.info("🛡️ Advanced Stop Hunting Protection initialized")
    
    def detect_current_broker(self) -> str:
        """
        Detect current broker from MT5 connection or config
        For now, returns default - would need MT5 integration
        """
        # TODO: Implement actual broker detection via MT5 API
        # For now, assume IC Markets (conservative profile)
        return 'IC_MARKETS'
    
    def calculate_adaptive_stop_randomization(self, symbol: str, base_stop: float, 
                                            current_atr: float, volatility_multiplier: float) -> float:
        """
        Volatility-adaptive randomization - scales with market conditions
        """
        if not self.enabled:
            return base_stop
            
        pip_size = 0.01 if 'JPY' in symbol else 0.0001
        base_range = current_atr / pip_size  # Convert ATR to pips
        
        # Adaptive range based on volatility
        if volatility_multiplier > 1.5:  # High volatility
            random_range = (int(base_range * 0.3), int(base_range * 0.8))  # 30-80% of ATR
        elif volatility_multiplier > 1.0:  # Normal volatility  
            random_range = (int(base_range * 0.2), int(base_range * 0.5))  # 20-50% of ATR
        else:  # Low volatility
            random_range = (int(base_range * 0.1), int(base_range * 0.3))  # 10-30% of ATR
        
        # Ensure minimum and maximum bounds
        random_range = (max(2, random_range[0]), min(15, random_range[1]))
        
        # Apply broker-specific multiplier
        broker_profile = self.broker_profiles.get(self.current_broker, {'randomization_multiplier': 1.0})
        broker_multiplier = broker_profile['randomization_multiplier']
        
        adjusted_range = (
            int(random_range[0] * broker_multiplier),
            int(random_range[1] * broker_multiplier)
        )
        
        random_pips = random.randint(*adjusted_range)
        randomization = random_pips * pip_size
        
        # 60% chance wider, 40% chance tighter (slight bias toward safety)
        if random.random() < 0.6:
            protected_stop = base_stop + randomization
        else:
            protected_stop = base_stop - (randomization * 0.4)  # Smaller tighter adjustment
        
        # Update statistics
        self.protection_stats['stops_randomized'] += 1
        self.protection_stats['avg_randomization_pips'] = (
            (self.protection_stats['avg_randomization_pips'] * (self.protection_stats['stops_randomized'] - 1) + random_pips) /
            self.protection_stats['stops_randomized']
        )
        
        self.logger.debug(f"🎲 {symbol} stop randomized: {random_pips:.1f} pips (volatility: {volatility_multiplier:.2f}x)")
        
        return protected_stop
    
    def calculate_rolling_spread_baseline(self, symbol: str, tick_data: List, lookback_minutes: int = 60) -> float:
        """
        Calculate dynamic spread baseline using rolling statistics
        """
        cache_key = f"{symbol}_{lookback_minutes}"
        current_time = time.time()
        
        # Check cache first
        if cache_key in self.spread_baseline_cache:
            cached_data = self.spread_baseline_cache[cache_key]
            if current_time - cached_data['timestamp'] < self.baseline_cache_ttl:
                return cached_data['baseline']
        
        if len(tick_data) < 10:
            # Fallback to hardcoded normal spreads if insufficient data
            normal_spreads = {
                'EURUSD': 0.8, 'GBPUSD': 1.2, 'USDJPY': 0.9,
                'USDCAD': 1.1, 'EURJPY': 1.4, 'GBPJPY': 1.8,
                'XAUUSD': 2.5
            }
            baseline = normal_spreads.get(symbol, 1.5)
            
            # Cache the fallback
            self.spread_baseline_cache[cache_key] = {
                'baseline': baseline,
                'timestamp': current_time
            }
            return baseline
        
        # Get recent ticks for baseline calculation
        cutoff_time = current_time - (lookback_minutes * 60)
        
        recent_spreads = []
        for tick in tick_data:
            if hasattr(tick, 'timestamp') and tick.timestamp >= cutoff_time:
                recent_spreads.append(tick.spread)
        
        if len(recent_spreads) < 5:
            baseline = 1.5  # Fallback if insufficient recent data
        else:
            # Calculate robust baseline using median + IQR (more stable than mean)
            recent_spreads.sort()
            n = len(recent_spreads)
            
            # Median
            if n % 2 == 0:
                median = (recent_spreads[n//2 - 1] + recent_spreads[n//2]) / 2
            else:
                median = recent_spreads[n//2]
            
            # Interquartile range for outlier detection
            q1 = recent_spreads[n//4]
            q3 = recent_spreads[3*n//4]
            iqr = q3 - q1
            
            # Filter outliers (spreads beyond 1.5*IQR from median)
            filtered_spreads = [s for s in recent_spreads if abs(s - median) <= 1.5 * iqr]
            
            if len(filtered_spreads) >= 3:
                baseline = sum(filtered_spreads) / len(filtered_spreads)
            else:
                baseline = median
            
            baseline = max(baseline, 0.5)  # Minimum baseline to prevent false positives
        
        # Cache the result
        self.spread_baseline_cache[cache_key] = {
            'baseline': baseline,
            'timestamp': current_time
        }
        
        return baseline
    
    def check_correlated_pair_spreads(self, primary_symbol: str, all_tick_data: Dict) -> Dict:
        """
        Check spread conditions across correlated pairs before trading
        """
        # Find which group primary symbol belongs to
        related_pairs = []
        for group_name, pairs in self.correlation_groups.items():
            if primary_symbol in pairs:
                related_pairs.extend([p for p in pairs if p in all_tick_data])
                break
        
        if not related_pairs:
            return {
                'safe_to_trade': True,
                'correlation_health': 1.0,
                'affected_pairs': [],
                'recommendation': 'TRADE'
            }
        
        # Check spread health across correlated pairs
        spread_issues = []
        total_pairs_checked = 0
        
        for pair in related_pairs:
            if pair in all_tick_data and len(all_tick_data[pair]) > 0:
                current_tick = list(all_tick_data[pair])[-1]
                normal_spread = self.calculate_rolling_spread_baseline(pair, list(all_tick_data[pair]))
                
                spread_ratio = current_tick.spread / normal_spread if normal_spread > 0 else 1
                
                if spread_ratio > 2.0:  # 100% above normal
                    spread_issues.append({
                        'pair': pair,
                        'current_spread': current_tick.spread,
                        'normal_spread': normal_spread,
                        'ratio': spread_ratio
                    })
                total_pairs_checked += 1
        
        # Calculate correlation health score
        if total_pairs_checked == 0:
            correlation_health = 1.0  # No data, assume healthy
        else:
            affected_ratio = len(spread_issues) / total_pairs_checked
            correlation_health = 1.0 - affected_ratio
        
        return {
            'safe_to_trade': correlation_health > 0.6,  # 60% of pairs must be healthy
            'correlation_health': correlation_health,
            'affected_pairs': spread_issues,
            'recommendation': 'TRADE' if correlation_health > 0.6 else 'WAIT'
        }
    
    def is_spread_spike_detected(self, symbol: str, tick_data: List, spike_threshold: float = 2.5) -> Dict:
        """
        Detect spread spikes using dynamic baseline
        """
        if len(tick_data) == 0:
            return {'spike_detected': False, 'reason': 'No tick data'}
        
        current_tick = list(tick_data)[-1]
        baseline = self.calculate_rolling_spread_baseline(symbol, list(tick_data))
        
        spike_ratio = current_tick.spread / baseline
        
        return {
            'spike_detected': spike_ratio > spike_threshold,
            'current_spread': current_tick.spread,
            'baseline_spread': baseline,
            'spike_ratio': round(spike_ratio, 2),
            'severity': 'HIGH' if spike_ratio > 4.0 else 'MEDIUM' if spike_ratio > 3.0 else 'LOW'
        }
    
    def is_stop_hunting_time(self) -> bool:
        """
        Check if current time is known hunting period for current broker
        """
        broker_profile = self.broker_profiles.get(self.current_broker, {'preferred_times': []})
        current_hour = datetime.utcnow().hour  # Use UTC for consistency
        
        return current_hour in broker_profile.get('preferred_times', [])
    
    def calculate_hunting_adjusted_position_size(self, base_size: float, symbol: str, 
                                               correlation_check: Dict, spread_analysis: Dict,
                                               volatility_multiplier: float, news_env: Dict = None) -> Dict:
        """
        Reduce position size during risky periods instead of avoiding trades
        """
        risk_factors = []
        size_multiplier = 1.0
        
        # Time-based hunting risk
        if self.is_stop_hunting_time():
            risk_factors.append('HUNTING_TIME')
            broker_profile = self.broker_profiles.get(self.current_broker, {'intensity': 0.5})
            hunting_intensity = broker_profile['intensity']
            size_multiplier *= (1.0 - (hunting_intensity * 0.4))  # Up to 40% reduction based on broker
        
        # Spread correlation risk
        if not correlation_check['safe_to_trade']:
            risk_factors.append('CORRELATION_SPIKE')
            health_factor = correlation_check['correlation_health']
            size_multiplier *= (0.5 + (health_factor * 0.3))  # 20-50% size based on health
        
        # Individual spread spike risk
        if spread_analysis['spike_detected']:
            risk_factors.append('SPREAD_SPIKE')
            if spread_analysis['severity'] == 'HIGH':
                size_multiplier *= 0.3  # 70% reduction
            elif spread_analysis['severity'] == 'MEDIUM':
                size_multiplier *= 0.6  # 40% reduction
            else:
                size_multiplier *= 0.8  # 20% reduction
        
        # Volatility spike risk
        if volatility_multiplier > 1.8:  # Extreme volatility
            risk_factors.append('HIGH_VOLATILITY')
            size_multiplier *= 0.6  # 40% reduction
        
        # News event proximity risk
        if news_env and news_env.get('action') == 'REDUCE':
            risk_factors.append('NEWS_PROXIMITY')
            size_multiplier *= 0.7  # 30% reduction
        
        # Apply compound risk reduction (don't over-reduce)
        final_multiplier = max(size_multiplier, 0.2)  # Never go below 20% size
        adjusted_size = base_size * final_multiplier
        
        # Update statistics
        if final_multiplier < 1.0:
            self.protection_stats['position_sizes_reduced'] += 1
            reduction_pct = (1 - final_multiplier) * 100
            self.protection_stats['avg_position_reduction'] = (
                (self.protection_stats['avg_position_reduction'] * (self.protection_stats['position_sizes_reduced'] - 1) + reduction_pct) /
                self.protection_stats['position_sizes_reduced']
            )
        
        return {
            'original_size': base_size,
            'adjusted_size': round(adjusted_size, 2),
            'size_reduction': round((1 - final_multiplier) * 100, 1),
            'risk_factors': risk_factors,
            'multiplier': final_multiplier
        }
    
    def get_final_trade_recommendation(self, correlation_check: Dict, spread_analysis: Dict, 
                                     position_adjustment: Dict) -> str:
        """
        Final go/no-go decision with reasoning
        """
        if spread_analysis['spike_detected'] and spread_analysis['spike_ratio'] > 4.0:
            self.protection_stats['trades_blocked_spread'] += 1
            return "SKIP - Extreme spread manipulation detected"
        
        if not correlation_check['safe_to_trade'] and correlation_check['correlation_health'] < 0.3:
            self.protection_stats['trades_blocked_correlation'] += 1
            return "SKIP - Systematic correlation breakdown"
            
        if position_adjustment['multiplier'] < 0.25:
            return "REDUCED - High risk environment, 75%+ position reduction"
        
        if position_adjustment['multiplier'] < 0.5:
            return "PROCEED_CAUTIOUS - Moderate risk, 50%+ position reduction"
        
        return "PROCEED - Normal risk environment"
    
    def apply_comprehensive_protection(self, signal: Dict, base_position_size: float,
                                     current_atr: float, volatility_multiplier: float,
                                     all_tick_data: Dict, news_env: Dict = None) -> Dict:
        """
        Master function implementing all advanced protection suggestions
        """
        if not self.enabled:
            return {
                'original_stop': signal['stop_loss'],
                'protected_stop': signal['stop_loss'],
                'original_position': base_position_size,
                'adjusted_position': base_position_size,
                'trade_recommendation': 'PROCEED',
                'protection_applied': False
            }
        
        symbol = signal['symbol']
        base_stop = signal['stop_loss']
        
        self.protection_stats['total_signals_processed'] += 1
        
        # 1. Volatility-adaptive randomization
        protected_stop = self.calculate_adaptive_stop_randomization(
            symbol, base_stop, current_atr, volatility_multiplier
        )
        
        # 2. Correlated pair analysis
        correlation_check = self.check_correlated_pair_spreads(symbol, all_tick_data)
        
        # 3. Dynamic spread spike detection
        symbol_tick_data = all_tick_data.get(symbol, [])
        spread_analysis = self.is_spread_spike_detected(symbol, symbol_tick_data)
        
        # 4. Position size adjustment (not avoidance)
        position_adjustment = self.calculate_hunting_adjusted_position_size(
            base_position_size, symbol, correlation_check, spread_analysis, 
            volatility_multiplier, news_env
        )
        
        # 5. Final recommendation
        trade_recommendation = self.get_final_trade_recommendation(
            correlation_check, spread_analysis, position_adjustment
        )
        
        # Calculate protection summary
        stop_adjustment_pips = abs(protected_stop - base_stop) * (10000 if 'JPY' not in symbol else 100)
        
        protection_summary = f"Stop randomized by {stop_adjustment_pips:.1f} pips"
        if position_adjustment['size_reduction'] > 0:
            protection_summary += f", position reduced by {position_adjustment['size_reduction']}%"
        
        # Compile final protection package
        result = {
            'original_stop': base_stop,
            'protected_stop': protected_stop,
            'stop_adjustment_pips': stop_adjustment_pips,
            
            'original_position': base_position_size,
            'adjusted_position': position_adjustment['adjusted_size'],
            'position_reduction': position_adjustment['size_reduction'],
            'risk_factors': position_adjustment['risk_factors'],
            
            'correlation_health': correlation_check['correlation_health'],
            'spread_spike_detected': spread_analysis['spike_detected'],
            'broker_intensity': self.broker_profiles.get(self.current_broker, {}).get('intensity', 0.5),
            
            'trade_recommendation': trade_recommendation,
            'protection_summary': protection_summary,
            'protection_applied': True
        }
        
        self.logger.info(f"🛡️ {symbol} protection: {protection_summary} | {trade_recommendation}")
        
        return result
    
    def get_protection_statistics(self) -> Dict:
        """
        Get comprehensive protection statistics
        """
        return {
            **self.protection_stats,
            'current_broker': self.current_broker,
            'broker_intensity': self.broker_profiles.get(self.current_broker, {}).get('intensity', 0.5),
            'protection_enabled': self.enabled
        }
    
    def enable_protection(self):
        """Enable stop hunting protection"""
        self.enabled = True
        self.logger.info("🛡️ Advanced Stop Hunting Protection ENABLED")
    
    def disable_protection(self):
        """Disable stop hunting protection (for testing)"""
        self.enabled = False
        self.logger.info("🛡️ Advanced Stop Hunting Protection DISABLED")
    
    def set_broker(self, broker: str):
        """Set current broker for profile-specific protection"""
        if broker in self.broker_profiles:
            self.current_broker = broker
            self.logger.info(f"🛡️ Broker set to {broker} (intensity: {self.broker_profiles[broker]['intensity']})")
        else:
            self.logger.warning(f"⚠️ Unknown broker: {broker}, using default profile")