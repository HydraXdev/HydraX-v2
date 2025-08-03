#!/usr/bin/env python3
"""
VENOM v7.0 WITH ANTI-FRICTION FILTER - LIVE MARKET TEST
Testing if the defensive filter helps protect against live market brutality

HYPOTHESIS: Filter removes dangerous signals that would be even worse in live conditions
QUESTION: Does filter improve live performance vs unfiltered VENOM?
"""

import json
import random
import statistics
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    VOLATILE_RANGE = "volatile_range"
    CALM_RANGE = "calm_range"
    BREAKOUT = "breakout"
    NEWS_EVENT = "news_event"

class SignalQuality(Enum):
    PLATINUM = "platinum"
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"

class AntiFrictionOverlay:
    """Anti-Friction Overlay - Defensive protection for live markets"""
    
    def __init__(self):
        self.config = {
            'news_protection': {
                'enabled': True,
                'avoid_before_minutes': 5,
                'avoid_after_minutes': 15
            },
            'spread_protection': {
                'enabled': True,
                'max_spread_multiplier': 2.0,
                'normal_spreads': {
                    'EURUSD': 0.8, 'GBPUSD': 1.0, 'USDJPY': 0.9,
                    'USDCAD': 1.2, 'AUDUSD': 1.0, 'NZDUSD': 1.5
                }
            },
            'session_protection': {
                'enabled': True,
                'dead_zones': [
                    {'start': 21, 'end': 23},  # NY close to Asian open
                    {'start': 23, 'end': 1},   # Weekend gap risk
                ]
            },
            'volatility_protection': {
                'enabled': True,
                'max_volatility_multiple': 3.0,
                'min_volatility_multiple': 0.4
            },
            'volume_protection': {
                'enabled': True,
                'min_volume_ratio': 1.1
            },
            'live_market_protection': {
                'enabled': True,
                'max_slippage_tolerance': 2.0,  # Reject if expected slippage > 2 pips
                'min_execution_probability': 0.8,  # Need 80%+ execution chance
                'dangerous_pairs_blacklist': [],  # Pairs to avoid in certain conditions
                'flash_crash_detection': True
            }
        }
        
        self.stats = {
            'total_received': 0,
            'filtered_out': 0,
            'approved': 0,
            'filter_reasons': {}
        }
    
    def filter_signal_for_live_conditions(self, signal: Dict, market_data: Dict, live_conditions: Dict) -> Tuple[bool, str, float]:
        """Enhanced filtering specifically designed for live market protection"""
        self.stats['total_received'] += 1
        
        confidence_adjustment = 0.0
        
        # 1. LIVE MARKET EXECUTION PROTECTION
        if live_conditions.get('expected_slippage', 0) > self.config['live_market_protection']['max_slippage_tolerance']:
            return self._reject_signal("SLIPPAGE_PROTECTION", f"Expected slippage {live_conditions['expected_slippage']:.1f} pips too high")
        
        if live_conditions.get('execution_probability', 1.0) < self.config['live_market_protection']['min_execution_probability']:
            return self._reject_signal("EXECUTION_PROTECTION", f"Execution probability {live_conditions['execution_probability']:.1f} too low")
        
        # 2. NEWS PROTECTION (Enhanced for live)
        if self._is_news_time() or live_conditions.get('is_news_time', False):
            return self._reject_signal("NEWS_PROTECTION", "Major news event - high slippage risk")
        
        # 3. SPREAD PROTECTION (Critical for live)
        pair = signal['pair']
        normal_spread = self.config['spread_protection']['normal_spreads'].get(pair, 2.0)
        max_spread = normal_spread * self.config['spread_protection']['max_spread_multiplier']
        current_spread = market_data.get('spread', normal_spread)
        
        if current_spread > max_spread:
            return self._reject_signal("SPREAD_PROTECTION", f"Spread too wide: {current_spread:.1f} pips")
        
        # 4. VOLATILITY PROTECTION (Enhanced)
        volatility = market_data.get('volatility', 1.0)
        if volatility > self.config['volatility_protection']['max_volatility_multiple']:
            return self._reject_signal("VOLATILITY_PROTECTION", f"Volatility too high: {volatility:.1f}x")
        
        if volatility < self.config['volatility_protection']['min_volatility_multiple']:
            return self._reject_signal("VOLATILITY_PROTECTION", f"Volatility too low: {volatility:.1f}x")
        
        # 5. SESSION PROTECTION (Live market specific)
        current_hour = datetime.now().hour
        for dead_zone in self.config['session_protection']['dead_zones']:
            start, end = dead_zone['start'], dead_zone['end']
            if self._is_in_dead_zone(current_hour, start, end):
                return self._reject_signal("SESSION_PROTECTION", f"Dead zone: {start}:00-{end}:00")
        
        # 6. LIVE CONDITIONS PROTECTION
        if live_conditions.get('is_friday_close', False):
            return self._reject_signal("FRIDAY_PROTECTION", "Friday close - weekend gap risk")
        
        if live_conditions.get('flash_crash_risk', False):
            return self._reject_signal("FLASH_PROTECTION", "Flash crash conditions detected")
        
        if live_conditions.get('broker_issues', False):
            return self._reject_signal("BROKER_PROTECTION", "Broker execution issues detected")
        
        # 7. CONFIDENCE ADJUSTMENTS (For approved signals)
        # Spread penalty
        spread_ratio = current_spread / normal_spread
        if spread_ratio > 1.3:
            confidence_adjustment -= (spread_ratio - 1.0) * 3
        
        # Volatility adjustments
        if volatility > 1.5:
            confidence_adjustment -= (volatility - 1.0) * 2
        elif volatility < 0.7:
            confidence_adjustment -= (1.0 - volatility) * 3
        
        # Live conditions adjustments
        if live_conditions.get('low_liquidity', False):
            confidence_adjustment -= 5
        
        if live_conditions.get('high_slippage_expected', False):
            confidence_adjustment -= 8
        
        # Calculate final confidence
        original_confidence = signal.get('confidence', 70)
        adjusted_confidence = max(30, original_confidence + confidence_adjustment)
        
        # Final confidence check
        if adjusted_confidence < 55:  # Higher threshold for live trading
            return self._reject_signal("CONFIDENCE_PROTECTION", f"Adjusted confidence too low: {adjusted_confidence:.1f}%")
        
        self.stats['approved'] += 1
        
        reason = "APPROVED"
        if confidence_adjustment != 0:
            reason += f" (confidence {original_confidence:.1f}% → {adjusted_confidence:.1f}%)"
        
        return True, reason, adjusted_confidence
    
    def _reject_signal(self, filter_type: str, reason: str) -> Tuple[bool, str, float]:
        """Reject signal with tracking"""
        self.stats['filtered_out'] += 1
        self.stats['filter_reasons'][filter_type] = self.stats['filter_reasons'].get(filter_type, 0) + 1
        return False, f"REJECTED: {reason}", 0.0
    
    def _is_news_time(self) -> bool:
        """Simple news time detection"""
        return random.random() < 0.08  # 8% chance of news
    
    def _is_in_dead_zone(self, hour: int, start: int, end: int) -> bool:
        """Check if hour is in dead zone"""
        if start <= end:
            return start <= hour <= end
        else:  # Overnight range
            return hour >= start or hour <= end

class VenomFilteredLiveTest:
    """
    VENOM v7.0 with Anti-Friction Filter - Live Market Testing
    
    Tests if defensive filtering improves live performance vs unfiltered VENOM
    """
    
    def __init__(self):
        # Trading pairs
        self.trading_pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF',
            'AUDUSD', 'USDCAD', 'NZDUSD',
            'EURJPY', 'GBPJPY', 'EURGBP',
            'XAUUSD', 'XAGUSD',
            'USDMXN', 'USDZAR', 'USDTRY'
        ]
        
        # VENOM configuration with filter
        self.config = {
            'start_date': datetime(2024, 7, 1),
            'end_date': datetime(2024, 12, 31),
            'target_signals_per_day': 25,
            'initial_balance': 10000,
            'dollar_per_pip': 10
        }
        
        # Initialize anti-friction overlay
        self.anti_friction = AntiFrictionOverlay()
        
        # Enhanced live market conditions
        self.live_market_factors = {
            'typical_slippage': {'min': 0.5, 'max': 3.5, 'spike': 10.0},
            'spread_widening': {'normal': 1.0, 'news': 3.0, 'illiquid': 5.0},
            'execution_delays': {'normal': 50, 'busy': 200, 'peak': 500},
            'requotes': 0.15,
            'rejected_trades': 0.05,
            'partial_fills': 0.08,
            'server_issues': 0.02,
            'news_events': 0.08,
            'liquidity_gaps': 0.12,
            'flash_crashes': 0.001
        }
        
        # Performance tracking
        self.total_signals_generated = 0
        self.total_signals_approved = 0
        self.all_trades = []
        self.filtered_signals = []
        
        logger.info("🐍 VENOM v7.0 WITH FILTER - Live Market Test Initialized")
        logger.info("🛡️ Anti-friction overlay ENABLED for live protection")
    
    def generate_venom_signal_with_filter(self, pair: str, timestamp: datetime) -> Optional[Dict]:
        """Generate VENOM signal with anti-friction filtering for live conditions"""
        
        # Generate base VENOM signal (same genius optimization)
        market_data = self.generate_live_market_data(pair, timestamp)
        regime = self.detect_market_regime(pair, timestamp)
        confidence = self.calculate_venom_confidence(pair, market_data, regime)
        quality = self.determine_signal_quality(confidence, market_data['session'], regime)
        
        if not self.should_generate_signal(pair, confidence, quality, market_data['session']):
            return None
        
        signal_type = self.determine_signal_type(confidence, quality)
        win_probability = self.calculate_win_probability(signal_type, quality, confidence, regime)
        
        self.total_signals_generated += 1
        direction = random.choice(['BUY', 'SELL'])
        
        # Perfect R:R ratios
        if signal_type == 'RAPID_ASSAULT':
            stop_pips = random.randint(10, 15)
            target_pips = stop_pips * 2
        else:
            stop_pips = random.randint(15, 20)
            target_pips = stop_pips * 3
        
        base_signal = {
            'signal_id': f'VENOM_FILTERED_{pair}_{self.total_signals_generated:06d}',
            'timestamp': timestamp,
            'pair': pair,
            'direction': direction,
            'signal_type': signal_type,
            'confidence': round(confidence, 1),
            'quality': quality.value,
            'market_regime': regime.value,
            'win_probability': round(win_probability, 3),
            'target_pips': target_pips,
            'stop_pips': stop_pips,
            'risk_reward': target_pips / stop_pips,
            'session': market_data['session'],
            'spread': market_data['spread'],
            'volume': market_data['volume']
        }
        
        # Generate live market conditions for this signal
        live_conditions = self.assess_live_conditions(pair, timestamp, market_data)
        
        # APPLY ANTI-FRICTION FILTER WITH LIVE CONDITIONS
        approved, reason, adjusted_confidence = self.anti_friction.filter_signal_for_live_conditions(
            base_signal, market_data, live_conditions
        )
        
        if not approved:
            # Signal was filtered for live protection
            filtered_signal = base_signal.copy()
            filtered_signal['filter_reason'] = reason
            filtered_signal['live_conditions'] = live_conditions
            self.filtered_signals.append(filtered_signal)
            return None
        
        # Signal approved - update confidence and return
        base_signal['original_confidence'] = confidence
        base_signal['adjusted_confidence'] = adjusted_confidence
        base_signal['filter_reason'] = reason
        base_signal['confidence'] = adjusted_confidence
        base_signal['live_conditions'] = live_conditions
        
        # Recalculate win probability with adjusted confidence
        base_signal['win_probability'] = self.calculate_win_probability(
            signal_type, quality, adjusted_confidence, regime
        )
        
        self.total_signals_approved += 1
        return base_signal
    
    def assess_live_conditions(self, pair: str, timestamp: datetime, market_data: Dict) -> Dict:
        """Assess current live market conditions for signal filtering"""
        
        # Simulate realistic live conditions
        expected_slippage = random.uniform(
            self.live_market_factors['typical_slippage']['min'],
            self.live_market_factors['typical_slippage']['max']
        )
        
        # Execution probability based on market conditions
        base_execution_prob = 0.85
        
        # Check for problematic conditions
        is_news_time = random.random() < self.live_market_factors['news_events']
        is_low_liquidity = random.random() < self.live_market_factors['liquidity_gaps']
        is_friday_close = random.random() < 0.05
        broker_issues = random.random() < self.live_market_factors['server_issues']
        flash_crash_risk = random.random() < self.live_market_factors['flash_crashes']
        
        # Adjust conditions based on factors
        if is_news_time:
            expected_slippage *= random.uniform(2.0, 4.0)
            base_execution_prob *= 0.7
        
        if is_low_liquidity:
            expected_slippage *= random.uniform(1.5, 2.5)
            base_execution_prob *= 0.8
        
        if is_friday_close:
            expected_slippage *= random.uniform(1.2, 1.8)
            base_execution_prob *= 0.9
        
        if broker_issues:
            base_execution_prob *= 0.5
        
        if flash_crash_risk:
            expected_slippage = self.live_market_factors['typical_slippage']['spike']
            base_execution_prob *= 0.3
        
        return {
            'expected_slippage': expected_slippage,
            'execution_probability': base_execution_prob,
            'is_news_time': is_news_time,
            'low_liquidity': is_low_liquidity,
            'is_friday_close': is_friday_close,
            'broker_issues': broker_issues,
            'flash_crash_risk': flash_crash_risk,
            'high_slippage_expected': expected_slippage > 2.0,
            'timestamp': timestamp
        }
    
    def execute_filtered_live_trade(self, signal: Dict) -> Dict:
        """Execute trade with live market conditions and filtering protection"""
        
        live_conditions = signal['live_conditions']
        
        # Use the live execution probability from conditions
        execution_success = random.random() < live_conditions['execution_probability']
        
        if not execution_success:
            return {
                'signal_id': signal['signal_id'],
                'executed': False,
                'reason': 'execution_failed',
                'live_conditions': live_conditions
            }
        
        # Execute with realistic live conditions
        is_win = random.random() < signal['win_probability']
        
        # Apply the expected slippage from live conditions
        actual_slippage = live_conditions['expected_slippage']
        
        # Additional spread costs
        spread_cost = signal['spread'] * 0.5  # Half spread cost
        
        if is_win:
            pips_result = signal['target_pips'] - actual_slippage - spread_cost
        else:
            pips_result = -(signal['stop_pips'] + actual_slippage + spread_cost)
        
        dollar_result = pips_result * self.config['dollar_per_pip']
        
        return {
            'signal_id': signal['signal_id'],
            'timestamp': signal['timestamp'],
            'pair': signal['pair'],
            'direction': signal['direction'],
            'signal_type': signal['signal_type'],
            'confidence': signal['confidence'],
            'original_confidence': signal.get('original_confidence', signal['confidence']),
            'adjusted_confidence': signal.get('adjusted_confidence', signal['confidence']),
            'quality': signal['quality'],
            'market_regime': signal['market_regime'],
            'win_probability': signal['win_probability'],
            'executed': True,
            'result': 'WIN' if is_win else 'LOSS',
            'pips_result': round(pips_result, 1),
            'dollar_result': round(dollar_result, 2),
            'target_pips': signal['target_pips'],
            'stop_pips': signal['stop_pips'],
            'risk_reward': signal['risk_reward'],
            'session': signal['session'],
            'spread': signal['spread'],
            'actual_slippage': round(actual_slippage, 2),
            'spread_cost': round(spread_cost, 2),
            'filter_reason': signal.get('filter_reason', 'APPROVED'),
            'live_conditions': live_conditions
        }
    
    # Include simplified versions of VENOM's core methods for space
    def detect_market_regime(self, pair: str, timestamp: datetime) -> MarketRegime:
        regimes = [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR, 
                  MarketRegime.VOLATILE_RANGE, MarketRegime.CALM_RANGE, 
                  MarketRegime.BREAKOUT, MarketRegime.NEWS_EVENT]
        return random.choice(regimes)
    
    def calculate_venom_confidence(self, pair: str, market_data: Dict, regime: MarketRegime) -> float:
        return random.uniform(65, 90)
    
    def determine_signal_quality(self, confidence: float, session: str, regime: MarketRegime) -> SignalQuality:
        if confidence >= 85:
            return SignalQuality.PLATINUM
        elif confidence >= 75:
            return SignalQuality.GOLD
        elif confidence >= 65:
            return SignalQuality.SILVER
        else:
            return SignalQuality.BRONZE
    
    def should_generate_signal(self, pair: str, confidence: float, quality: SignalQuality, session: str) -> bool:
        return random.random() < 0.25  # 25% base generation rate
    
    def determine_signal_type(self, confidence: float, quality: SignalQuality) -> str:
        return random.choice(['RAPID_ASSAULT', 'PRECISION_STRIKE'])
    
    def calculate_win_probability(self, signal_type: str, quality: SignalQuality, confidence: float, regime: MarketRegime) -> float:
        base_rates = {SignalQuality.PLATINUM: 0.82, SignalQuality.GOLD: 0.76, SignalQuality.SILVER: 0.71, SignalQuality.BRONZE: 0.66}
        return base_rates.get(quality, 0.70)
    
    def generate_live_market_data(self, pair: str, timestamp: datetime) -> Dict:
        return {
            'symbol': pair,
            'timestamp': timestamp,
            'spread': random.uniform(0.8, 3.0),
            'volume': random.randint(1000, 2000),
            'session': self.get_session_type(timestamp.hour),
            'volatility': random.uniform(0.5, 2.0)
        }
    
    def get_session_type(self, hour: int) -> str:
        if 7 <= hour <= 11:
            return 'LONDON'
        elif 13 <= hour <= 17:
            return 'NY'
        elif 8 <= hour <= 9 or 14 <= hour <= 15:
            return 'OVERLAP'
        elif 0 <= hour <= 6:
            return 'ASIAN'
        else:
            return 'OFF_HOURS'
    
    def run_filtered_live_backtest(self) -> Dict:
        """Run VENOM backtest with anti-friction filter for live conditions"""
        
        logger.info("🐍 Starting VENOM Filtered Live Market Test")
        logger.info("🛡️ Anti-friction overlay protecting against live conditions")
        
        current_date = self.config['start_date']
        
        while current_date <= self.config['end_date']:
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            daily_signals = []
            daily_trades = []
            
            for hour in range(24):
                timestamp = current_date.replace(hour=hour, minute=0, second=0)
                
                # Scan pairs for signals
                pairs_to_scan = random.sample(self.trading_pairs, k=random.randint(6, 10))
                
                for pair in pairs_to_scan:
                    if len(daily_signals) >= self.config['target_signals_per_day']:
                        break
                    
                    signal = self.generate_venom_signal_with_filter(pair, timestamp)
                    if signal:
                        daily_signals.append(signal)
                        trade_result = self.execute_filtered_live_trade(signal)
                        if trade_result['executed']:
                            daily_trades.append(trade_result)
                            self.all_trades.append(trade_result)
            
            current_date += timedelta(days=1)
        
        return self.calculate_filtered_results()
    
    def calculate_filtered_results(self) -> Dict:
        """Calculate results with filter analysis"""
        
        executed_trades = [t for t in self.all_trades if t['executed']]
        
        if not executed_trades:
            return {'error': 'No trades executed'}
        
        # Basic performance metrics
        total_executed = len(executed_trades)
        total_wins = sum(1 for t in executed_trades if t['result'] == 'WIN')
        win_rate = (total_wins / total_executed) * 100
        total_pips = sum(t['pips_result'] for t in executed_trades)
        total_dollars = sum(t['dollar_result'] for t in executed_trades)
        
        # Filter effectiveness
        filter_stats = self.anti_friction.stats
        filter_rate = (filter_stats['filtered_out'] / filter_stats['total_received']) * 100
        
        # Signal type breakdown
        signal_types = {}
        for trade in executed_trades:
            signal_type = trade['signal_type']
            if signal_type not in signal_types:
                signal_types[signal_type] = {'count': 0, 'wins': 0, 'pips': 0}
            signal_types[signal_type]['count'] += 1
            if trade['result'] == 'WIN':
                signal_types[signal_type]['wins'] += 1
            signal_types[signal_type]['pips'] += trade['pips_result']
        
        for signal_type, data in signal_types.items():
            if data['count'] > 0:
                data['win_rate'] = round((data['wins'] / data['count']) * 100, 1)
            else:
                data['win_rate'] = 0
        
        # Execution analysis
        execution_rate = (total_executed / self.total_signals_approved) * 100 if self.total_signals_approved > 0 else 0
        
        # Average costs
        avg_slippage = statistics.mean([t['actual_slippage'] for t in executed_trades])
        avg_spread_cost = statistics.mean([t['spread_cost'] for t in executed_trades])
        
        logger.info(f"🐍 FILTERED VENOM Complete: {total_executed} trades executed, {win_rate:.1f}% win rate")
        logger.info(f"🛡️ Filter protected: {filter_stats['filtered_out']} signals filtered ({filter_rate:.1f}%)")
        
        return {
            'summary': {
                'total_signals_generated': self.total_signals_generated,
                'total_signals_approved': self.total_signals_approved,
                'total_trades_executed': total_executed,
                'win_rate': round(win_rate, 1),
                'total_pips': round(total_pips, 1),
                'total_dollars': round(total_dollars, 2),
                'execution_rate': round(execution_rate, 1),
                'avg_slippage': round(avg_slippage, 2),
                'avg_spread_cost': round(avg_spread_cost, 2)
            },
            'filter_analysis': {
                'filter_rate': round(filter_rate, 1),
                'total_filtered': filter_stats['filtered_out'],
                'filter_reasons': filter_stats['filter_reasons']
            },
            'signal_type_performance': signal_types,
            'all_trades': executed_trades,
            'filtered_signals': self.filtered_signals
        }

def main():
    """Run VENOM filtered live market test"""
    print("🐍 VENOM v7.0 WITH ANTI-FRICTION FILTER - LIVE MARKET TEST")
    print("=" * 80)
    print("🛡️ TESTING: Does the filter help protect against live market brutality?")
    print("🎯 COMPARISON: Filtered vs Unfiltered VENOM in harsh live conditions")
    print("📊 FOCUS: Filter effectiveness in protecting live performance")
    print("=" * 80)
    
    tester = VenomFilteredLiveTest()
    results = tester.run_filtered_live_backtest()
    
    if 'error' in results:
        print(f"❌ Test failed: {results['error']}")
        return
    
    # Display results
    summary = results['summary']
    filter_analysis = results['filter_analysis']
    signal_performance = results['signal_type_performance']
    
    print(f"\n🐍 VENOM FILTERED LIVE RESULTS")
    print("=" * 80)
    print(f"📊 Signals Generated: {summary['total_signals_generated']:}")
    print(f"🛡️ Signals Approved: {summary['total_signals_approved']:}")
    print(f"⚡ Trades Executed: {summary['total_trades_executed']:}")
    print(f"🎯 Live Win Rate: {summary['win_rate']}%")
    print(f"💰 Total Return: ${summary['total_dollars']:+,.2f}")
    print(f"📈 Total Pips: {summary['total_pips']:+.1f}")
    print(f"⚡ Execution Rate: {summary['execution_rate']}%")
    print(f"📉 Avg Slippage: {summary['avg_slippage']} pips")
    print(f"💸 Avg Spread Cost: {summary['avg_spread_cost']} pips")
    
    print(f"\n🛡️ FILTER PROTECTION ANALYSIS:")
    print("=" * 80)
    print(f"📊 Filter Rate: {filter_analysis['filter_rate']}%")
    print(f"🚫 Total Filtered: {filter_analysis['total_filtered']:} signals")
    print(f"\n📋 Filter Reasons:")
    for reason, count in filter_analysis['filter_reasons'].items():
        percentage = (count / filter_analysis['total_filtered']) * 100
        print(f"  {reason}: {count} signals ({percentage:.1f}%)")
    
    print(f"\n📊 SIGNAL TYPE PERFORMANCE:")
    print("=" * 80)
    for signal_type, data in signal_performance.items():
        print(f"\n{signal_type}:")
        print(f"  Count: {data['count']} trades")
        print(f"  Win Rate: {data['win_rate']}%")
        print(f"  Total Pips: {data['pips']:+.1f}")
    
    # Compare with unfiltered expectations
    print(f"\n🔍 FILTERED vs UNFILTERED COMPARISON:")
    print("=" * 80)
    unfiltered_expectation = 67.6  # From previous unfiltered live test
    filtered_actual = summary['win_rate']
    improvement = filtered_actual - unfiltered_expectation
    
    print(f"📊 Unfiltered Expected: {unfiltered_expectation}% win rate")
    print(f"🛡️ Filtered Actual: {filtered_actual}% win rate")
    
    if improvement > 0:
        print(f"✅ Filter Improvement: +{improvement:.1f}%")
        print(f"🛡️ VERDICT: Filter helps protect against live market risks")
    else:
        print(f"❌ Filter Impact: {improvement:.1f}%")
        print(f"⚠️ VERDICT: Filter may be over-protective for live conditions")
    
    print(f"\n🎯 FILTER EFFECTIVENESS:")
    print("=" * 80)
    if filter_analysis['filter_rate'] > 20:
        print("🛡️ HIGH PROTECTION: Filter blocking >20% of signals")
        print("💡 May be reducing both bad AND good signals")
    elif filter_analysis['filter_rate'] > 10:
        print("⚖️ BALANCED PROTECTION: Moderate filtering")
        print("💡 Good balance of protection vs opportunity")
    else:
        print("🔓 LOW PROTECTION: <10% signals filtered")
        print("💡 Minimal protection, most signals pass through")
    
    # Final recommendation
    print(f"\n🏆 FINAL RECOMMENDATION:")
    print("=" * 80)
    
    if improvement >= 2 and filter_analysis['filter_rate'] <= 25:
        print("✅ USE FILTER: Improves live performance with reasonable signal retention")
    elif improvement >= 0 and filter_analysis['filter_rate'] <= 15:
        print("⚖️ FILTER OPTIONAL: Marginal benefit but not harmful")
    else:
        print("❌ SKIP FILTER: Over-protective or reduces performance")
    
    # Save results
    with open('venom_filtered_live_test_results.json', 'w') as f:
        serializable_results = results.copy()
        for trade in serializable_results['all_trades']:
            trade['timestamp'] = trade['timestamp'].isoformat()
            trade['live_conditions']['timestamp'] = trade['live_conditions']['timestamp'].isoformat()
        for signal in serializable_results['filtered_signals']:
            signal['timestamp'] = signal['timestamp'].isoformat()
        json.dump(serializable_results, f, indent=2)
    
    print(f"\n💾 Results saved to: venom_filtered_live_test_results.json")
    print(f"\n🛡️ FILTERED LIVE TEST COMPLETE!")

if __name__ == "__main__":
    main()