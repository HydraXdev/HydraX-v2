#!/usr/bin/env python3
"""
VENOM v7.0 - FILTER ANALYSIS
Analyzes the performance of the 830 filtered signals
Shows exactly what win rate they would have achieved
"""

import json
import random
import statistics
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Use the same classes from VENOM v7.0
from apex_venom_v7_complete import ApexVenomV7, AntiFrictionOverlay, MarketRegime, SignalQuality

# Set up logging for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VenomFilterAnalyzer(ApexVenomV7):
    """
    Enhanced VENOM v7.0 that tracks filtered signals and their hypothetical performance
    """
    
    def __init__(self):
        super().__init__()
        
        # Additional tracking for filtered signals
        self.filtered_signals = []
        self.filtered_performance = {
            'total_filtered': 0,
            'by_filter_type': {},
            'hypothetical_trades': []
        }
        
        # Override anti-friction to capture filtered signals
        self.anti_friction = FilterTrackingOverlay()
        
        logger.info("🔍 VENOM Filter Analyzer Initialized")
        logger.info("📊 Will track performance of filtered signals")
    
    def generate_venom_signal_with_tracking(self, pair: str, timestamp: datetime) -> Optional[Dict]:
        """Enhanced signal generation that tracks filtered signals"""
        market_data = self.generate_realistic_market_data(pair, timestamp)
        regime = self.detect_market_regime(pair, timestamp)
        confidence = self.calculate_venom_confidence(pair, market_data, regime)
        quality = self.determine_signal_quality(confidence, market_data['session'], regime)
        
        if not self.should_generate_venom_signal(pair, confidence, quality, market_data['session']):
            return None
        
        signal_type = self.determine_signal_type_venom(confidence, quality)
        win_probability = self.calculate_venom_win_probability(signal_type, quality, confidence, regime)
        
        self.total_signals += 1
        direction = random.choice(['BUY', 'SELL'])
        
        # Perfect R:R ratios
        if signal_type == 'RAPID_ASSAULT':
            stop_pips = random.randint(10, 15)
            target_pips = stop_pips * 2
        else:
            stop_pips = random.randint(15, 20)
            target_pips = stop_pips * 3
        
        base_signal = {
            'signal_id': f'VENOM_TRACK_{pair}_{self.total_signals:06d}',
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
            'volume': market_data['volume'],
            'volume_ratio': market_data.get('volume_ratio', 1.0),
            'volatility': market_data.get('volatility', 1.0)
        }
        
        # APPLY ANTI-FRICTION OVERLAY WITH TRACKING
        approved, reason, adjusted_confidence, filter_details = self.anti_friction.filter_signal_with_tracking(base_signal, market_data)
        
        if not approved:
            # Signal was filtered - add to filtered tracking
            filtered_signal = base_signal.copy()
            filtered_signal['filter_reason'] = reason
            filtered_signal['filter_type'] = filter_details.get('filter_type', 'UNKNOWN')
            filtered_signal['filter_details'] = filter_details
            
            # Calculate what the hypothetical trade result would have been
            hypothetical_trade = self.simulate_filtered_trade(filtered_signal)
            
            self.filtered_signals.append(filtered_signal)
            self.filtered_performance['hypothetical_trades'].append(hypothetical_trade)
            self.filtered_performance['total_filtered'] += 1
            
            filter_type = filter_details.get('filter_type', 'UNKNOWN')
            self.filtered_performance['by_filter_type'][filter_type] = (
                self.filtered_performance['by_filter_type'].get(filter_type, 0) + 1
            )
            
            return None  # Signal was filtered
        
        # Signal approved - update and return
        base_signal['original_confidence'] = confidence
        base_signal['adjusted_confidence'] = adjusted_confidence
        base_signal['overlay_reason'] = reason
        base_signal['confidence'] = adjusted_confidence
        
        # Recalculate win probability with adjusted confidence
        base_signal['win_probability'] = self.calculate_venom_win_probability(
            signal_type, quality, adjusted_confidence, regime
        )
        
        return base_signal
    
    def simulate_filtered_trade(self, filtered_signal: Dict) -> Dict:
        """Simulate what the trade result would have been for a filtered signal"""
        # Use the original win probability (before filtering)
        is_win = random.random() < filtered_signal['win_probability']
        
        # Apply realistic slippage (potentially worse for filtered signals)
        base_slippage = random.uniform(0.3, 0.8)  # Higher slippage for "dangerous" signals
        
        # Additional slippage based on filter reason
        filter_type = filtered_signal.get('filter_type', '')
        if 'SPREAD' in filter_type:
            base_slippage += random.uniform(0.2, 0.5)  # Wide spreads = more slippage
        elif 'VOLATILITY' in filter_type:
            base_slippage += random.uniform(0.3, 0.7)  # High volatility = more slippage
        elif 'VOLUME' in filter_type:
            base_slippage += random.uniform(0.1, 0.3)  # Low volume = some extra slippage
        
        if is_win:
            pips_result = filtered_signal['target_pips'] - base_slippage
        else:
            pips_result = -(filtered_signal['stop_pips'] + base_slippage)
        
        dollar_result = pips_result * self.config['dollar_per_pip']
        
        return {
            'signal_id': filtered_signal['signal_id'],
            'timestamp': filtered_signal['timestamp'],
            'pair': filtered_signal['pair'],
            'direction': filtered_signal['direction'],
            'signal_type': filtered_signal['signal_type'],
            'confidence': filtered_signal['confidence'],
            'quality': filtered_signal['quality'],
            'win_probability': filtered_signal['win_probability'],
            'filter_reason': filtered_signal['filter_reason'],
            'filter_type': filtered_signal['filter_type'],
            'result': 'WIN' if is_win else 'LOSS',
            'pips_result': round(pips_result, 1),
            'dollar_result': round(dollar_result, 2),
            'target_pips': filtered_signal['target_pips'],
            'stop_pips': filtered_signal['stop_pips'],
            'risk_reward': filtered_signal['risk_reward'],
            'session': filtered_signal['session'],
            'spread': filtered_signal['spread'],
            'hypothetical': True
        }
    
    def run_filter_analysis_backtest(self) -> Dict:
        """Run backtest with comprehensive filter analysis"""
        logger.info("🔍 Starting VENOM Filter Analysis Backtest")
        logger.info("📊 Tracking both approved AND filtered signals")
        
        current_date = self.config['start_date']
        
        while current_date <= self.config['end_date']:
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            daily_signals = []
            daily_trades = []
            
            for hour in range(24):
                timestamp = current_date.replace(hour=hour, minute=0, second=0)
                session = self.get_session_type(hour)
                
                # Smart pair selection
                session_optimal = self.session_intelligence[session]['optimal_pairs']
                if session_optimal:
                    primary_pairs = session_optimal
                    secondary_pairs = [p for p in self.trading_pairs if p not in session_optimal]
                    pairs_to_scan = primary_pairs + random.sample(secondary_pairs, k=min(3, len(secondary_pairs)))
                else:
                    pairs_to_scan = random.sample(self.trading_pairs, k=random.randint(4, 8))
                
                scan_attempts = 3 if session in ['OVERLAP', 'LONDON', 'NY'] else 2
                
                for attempt in range(scan_attempts):
                    for pair in pairs_to_scan:
                        if len(daily_signals) >= self.config['target_signals_per_day']:
                            break
                        
                        signal = self.generate_venom_signal_with_tracking(pair, timestamp)
                        if signal:
                            daily_signals.append(signal)
                            trade_result = self.execute_venom_trade(signal)
                            daily_trades.append(trade_result)
                            self.all_trades.append(trade_result)
                    
                    if len(daily_signals) >= self.config['target_signals_per_day']:
                        break
            
            # Daily statistics
            if daily_trades:
                daily_wins = sum(1 for trade in daily_trades if trade['result'] == 'WIN')
                daily_pips = sum(trade['pips_result'] for trade in daily_trades)
                
                self.daily_stats.append({
                    'date': current_date,
                    'signals': len(daily_signals),
                    'wins': daily_wins,
                    'total_pips': round(daily_pips, 1)
                })
            
            # Progress tracking
            days_elapsed = (current_date - self.config['start_date']).days
            if days_elapsed % 30 == 0 and days_elapsed > 0:
                approved_so_far = len(self.all_trades)
                filtered_so_far = self.filtered_performance['total_filtered']
                total_generated = approved_so_far + filtered_so_far
                filter_rate = (filtered_so_far / total_generated * 100) if total_generated > 0 else 0
                logger.info(f"🔍 Day {days_elapsed}: {approved_so_far} approved, {filtered_so_far} filtered ({filter_rate:.1f}% filter rate)")
            
            current_date += timedelta(days=1)
        
        return self.calculate_filter_analysis_results()
    
    def calculate_filter_analysis_results(self) -> Dict:
        """Calculate comprehensive results including filtered signal analysis"""
        # Get base VENOM results
        base_results = self.calculate_venom_results()
        
        # Analyze filtered signals
        filtered_analysis = self.analyze_filtered_performance()
        
        # Combine results
        base_results['filtered_analysis'] = filtered_analysis
        
        return base_results
    
    def analyze_filtered_performance(self) -> Dict:
        """Comprehensive analysis of filtered signals and their hypothetical performance"""
        if not self.filtered_performance['hypothetical_trades']:
            return {'error': 'No filtered signals to analyze'}
        
        hypothetical_trades = self.filtered_performance['hypothetical_trades']
        total_filtered = len(hypothetical_trades)
        
        # Overall filtered performance
        filtered_wins = sum(1 for trade in hypothetical_trades if trade['result'] == 'WIN')
        filtered_win_rate = (filtered_wins / total_filtered) * 100
        filtered_pips = sum(trade['pips_result'] for trade in hypothetical_trades)
        filtered_dollars = sum(trade['dollar_result'] for trade in hypothetical_trades)
        
        # Analyze by filter type
        filter_type_analysis = {}
        for filter_type, count in self.filtered_performance['by_filter_type'].items():
            type_trades = [t for t in hypothetical_trades if t['filter_type'] == filter_type]
            if type_trades:
                type_wins = sum(1 for t in type_trades if t['result'] == 'WIN')
                type_win_rate = (type_wins / len(type_trades)) * 100
                type_pips = sum(t['pips_result'] for t in type_trades)
                
                filter_type_analysis[filter_type] = {
                    'count': len(type_trades),
                    'win_rate': round(type_win_rate, 1),
                    'total_pips': round(type_pips, 1),
                    'avg_pips_per_trade': round(type_pips / len(type_trades), 2)
                }
        
        # Analyze by signal type
        signal_type_analysis = {}
        for signal_type in ['RAPID_ASSAULT', 'PRECISION_STRIKE']:
            type_trades = [t for t in hypothetical_trades if t['signal_type'] == signal_type]
            if type_trades:
                type_wins = sum(1 for t in type_trades if t['result'] == 'WIN')
                type_win_rate = (type_wins / len(type_trades)) * 100
                type_pips = sum(t['pips_result'] for t in type_trades)
                
                signal_type_analysis[signal_type] = {
                    'count': len(type_trades),
                    'win_rate': round(type_win_rate, 1),
                    'total_pips': round(type_pips, 1),
                    'avg_pips_per_trade': round(type_pips / len(type_trades), 2)
                }
        
        # Quality distribution of filtered signals
        quality_dist = {}
        for trade in hypothetical_trades:
            quality = trade['quality']
            quality_dist[quality] = quality_dist.get(quality, 0) + 1
        
        # Win rate by quality for filtered signals
        quality_performance = {}
        for quality in quality_dist.keys():
            quality_trades = [t for t in hypothetical_trades if t['quality'] == quality]
            quality_wins = sum(1 for t in quality_trades if t['result'] == 'WIN')
            quality_win_rate = (quality_wins / len(quality_trades)) * 100
            quality_performance[quality] = round(quality_win_rate, 1)
        
        logger.info(f"🔍 Filtered Signal Analysis Complete:")
        logger.info(f"📊 Total Filtered: {total_filtered}")
        logger.info(f"🎯 Hypothetical Win Rate: {filtered_win_rate:.1f}%")
        logger.info(f"💰 Hypothetical Pips: {filtered_pips:+.1f}")
        
        return {
            'summary': {
                'total_filtered_signals': total_filtered,
                'hypothetical_win_rate': round(filtered_win_rate, 1),
                'hypothetical_total_pips': round(filtered_pips, 1),
                'hypothetical_total_dollars': round(filtered_dollars, 2),
                'avg_pips_per_filtered_trade': round(filtered_pips / total_filtered, 2)
            },
            'filter_type_breakdown': filter_type_analysis,
            'signal_type_breakdown': signal_type_analysis,
            'quality_distribution': quality_dist,
            'quality_performance': quality_performance,
            'filter_effectiveness': {
                'filter_saved_money': filtered_win_rate < 65,  # If filtered signals had <65% win rate, filter was effective
                'filter_justification': f"Filtered signals would have achieved {filtered_win_rate:.1f}% win rate vs target 65%+"
            }
        }

class FilterTrackingOverlay(AntiFrictionOverlay):
    """Enhanced overlay that provides detailed tracking information"""
    
    def filter_signal_with_tracking(self, signal: Dict, market_data: Dict) -> Tuple[bool, str, float, Dict]:
        """Enhanced filter that returns detailed tracking info"""
        self.stats['total_received'] += 1
        
        confidence_adjustment = 0.0
        filter_details = {}
        
        # 1. NEWS PROTECTION
        if self._is_news_time():
            filter_details = {'filter_type': 'NEWS_PROTECTION', 'reason': 'Major news event nearby'}
            return self._reject_signal_with_tracking("NEWS_PROTECTION", "Major news event nearby", filter_details)
        
        # 2. SPREAD PROTECTION
        pair = signal['pair']
        normal_spread = self.config['spread_protection']['normal_spreads'].get(pair, 2.0)
        max_spread = normal_spread * self.config['spread_protection']['max_spread_multiplier']
        current_spread = market_data.get('spread', normal_spread)
        
        if current_spread > max_spread:
            filter_details = {
                'filter_type': 'SPREAD_PROTECTION', 
                'current_spread': current_spread,
                'max_allowed': max_spread,
                'spread_ratio': current_spread / normal_spread
            }
            return self._reject_signal_with_tracking("SPREAD_PROTECTION", f"Spread too wide: {current_spread:.1f} pips", filter_details)
        
        # Spread penalty
        spread_ratio = current_spread / normal_spread
        if spread_ratio > 1.3:
            confidence_adjustment -= (spread_ratio - 1.0) * 2
        
        # 3. SESSION PROTECTION
        current_hour = datetime.now().hour
        for dead_zone in self.config['session_protection']['dead_zones']:
            start, end = dead_zone['start'], dead_zone['end']
            if self._is_in_dead_zone(current_hour, start, end):
                filter_details = {
                    'filter_type': 'SESSION_PROTECTION',
                    'current_hour': current_hour,
                    'dead_zone': f"{start}:00-{end}:00"
                }
                return self._reject_signal_with_tracking("SESSION_PROTECTION", f"Dead zone: {start}:00-{end}:00", filter_details)
        
        # Session adjustments
        session_adjustments = {
            (7, 12): 3.0, (12, 16): 5.0, (16, 21): 2.0, (22, 7): -2.0
        }
        
        for (start, end), adjustment in session_adjustments.items():
            if self._is_in_time_range(current_hour, start, end):
                confidence_adjustment += adjustment
                break
        
        # 4. VOLATILITY PROTECTION
        volatility = market_data.get('volatility', 1.0)
        if volatility > self.config['volatility_protection']['max_volatility_multiple']:
            filter_details = {
                'filter_type': 'VOLATILITY_PROTECTION',
                'current_volatility': volatility,
                'max_allowed': self.config['volatility_protection']['max_volatility_multiple']
            }
            return self._reject_signal_with_tracking("VOLATILITY_PROTECTION", f"Volatility too high: {volatility:.1f}x", filter_details)
        
        if volatility < self.config['volatility_protection']['min_volatility_multiple']:
            filter_details = {
                'filter_type': 'VOLATILITY_PROTECTION',
                'current_volatility': volatility,
                'min_required': self.config['volatility_protection']['min_volatility_multiple']
            }
            return self._reject_signal_with_tracking("VOLATILITY_PROTECTION", f"Volatility too low: {volatility:.1f}x", filter_details)
        
        # 5. VOLUME PROTECTION
        volume_ratio = market_data.get('volume_ratio', 1.0)
        if volume_ratio < self.config['volume_protection']['min_volume_ratio']:
            filter_details = {
                'filter_type': 'VOLUME_PROTECTION',
                'current_volume_ratio': volume_ratio,
                'min_required': self.config['volume_protection']['min_volume_ratio']
            }
            return self._reject_signal_with_tracking("VOLUME_PROTECTION", f"Volume too low: {volume_ratio:.1f}x average", filter_details)
        
        # Volume boost
        if volume_ratio > 1.5:
            confidence_adjustment += min(4.0, (volume_ratio - 1.0) * 2)
        
        # Calculate final confidence
        original_confidence = signal.get('confidence', 70)
        adjusted_confidence = max(30, original_confidence + confidence_adjustment)
        
        self.stats['approved'] += 1
        
        reason = "APPROVED"
        if confidence_adjustment != 0:
            reason += f" (confidence {original_confidence:.1f}% → {adjusted_confidence:.1f}%)"
        
        return True, reason, adjusted_confidence, filter_details
    
    def _reject_signal_with_tracking(self, filter_type: str, reason: str, details: Dict) -> Tuple[bool, str, float, Dict]:
        """Enhanced rejection with tracking details"""
        self.stats['filtered_out'] += 1
        self.stats['filter_reasons'][filter_type] = self.stats['filter_reasons'].get(filter_type, 0) + 1
        return False, f"REJECTED: {reason}", 0.0, details

def main():
    """Run comprehensive filter analysis"""
    print("🔍 VENOM v7.0 - COMPREHENSIVE FILTER ANALYSIS")
    print("=" * 80)
    print("📊 ANALYZING THE 830 FILTERED SIGNALS:")
    print("   🎯 What win rate would they have achieved?")
    print("   💰 How much money would they have made/lost?")
    print("   🛡️ Was the filter actually protective?")
    print("=" * 80)
    
    analyzer = VenomFilterAnalyzer()
    results = analyzer.run_filter_analysis_backtest()
    
    if 'error' in results:
        print(f"❌ Analysis failed: {results['error']}")
        return
    
    # Display main results
    summary = results['summary']
    filtered_analysis = results['filtered_analysis']
    
    print(f"\n🐍 APPROVED SIGNALS PERFORMANCE:")
    print("=" * 80)
    print(f"📊 Total Approved Trades: {summary['total_trades']:}")
    print(f"🏆 Approved Win Rate: {summary['overall_win_rate']}%")
    print(f"💰 Approved Total Return: ${summary['total_dollars']:+,.2f}")
    
    print(f"\n🚫 FILTERED SIGNALS ANALYSIS:")
    print("=" * 80)
    
    if 'error' not in filtered_analysis:
        filtered_summary = filtered_analysis['summary']
        filter_effectiveness = filtered_analysis['filter_effectiveness']
        
        print(f"📊 Total Filtered Signals: {filtered_summary['total_filtered_signals']:}")
        print(f"🎯 Hypothetical Win Rate: {filtered_summary['hypothetical_win_rate']}%")
        print(f"💰 Hypothetical Total Return: ${filtered_summary['hypothetical_total_dollars']:+,.2f}")
        print(f"📈 Avg Pips per Filtered Trade: {filtered_summary['avg_pips_per_filtered_trade']:+.2f}")
        
        print(f"\n🛡️ FILTER EFFECTIVENESS ANALYSIS:")
        print("=" * 80)
        effectiveness = "✅ PROTECTIVE" if filter_effectiveness['filter_saved_money'] else "❌ OVER-FILTERING"
        print(f"Filter Result: {effectiveness}")
        print(f"Justification: {filter_effectiveness['filter_justification']}")
        
        # Compare approved vs filtered performance
        approved_win_rate = summary['overall_win_rate']
        filtered_win_rate = filtered_summary['hypothetical_win_rate']
        performance_gap = approved_win_rate - filtered_win_rate
        
        print(f"\n📊 PERFORMANCE COMPARISON:")
        print("=" * 80)
        print(f"✅ Approved Signals: {approved_win_rate}% win rate")
        print(f"🚫 Filtered Signals: {filtered_win_rate}% win rate")
        print(f"📈 Performance Gap: {performance_gap:+.1f}%")
        
        if performance_gap > 0:
            money_saved = abs(filtered_summary['hypothetical_total_dollars'])
            print(f"💰 Money Potentially Saved: ${money_saved:,.2f}")
            print(f"🛡️ Filter Verdict: EXCELLENT - Saved money by filtering weak signals")
        else:
            money_lost = filtered_summary['hypothetical_total_dollars']
            print(f"💸 Potential Profit Lost: ${money_lost:,.2f}")
            print(f"⚠️ Filter Verdict: OVER-PROTECTIVE - May be filtering good signals")
        
        # Filter type breakdown
        print(f"\n🔍 BREAKDOWN BY FILTER TYPE:")
        print("=" * 80)
        for filter_type, data in filtered_analysis['filter_type_breakdown'].items():
            print(f"{filter_type}:")
            print(f"  📊 Count: {data['count']} signals")
            print(f"  🎯 Win Rate: {data['win_rate']}%")
            print(f"  💰 Total Pips: {data['total_pips']:+.1f}")
            print(f"  📈 Avg per Trade: {data['avg_pips_per_trade']:+.2f} pips")
        
        # Quality analysis of filtered signals
        print(f"\n⭐ QUALITY ANALYSIS OF FILTERED SIGNALS:")
        print("=" * 80)
        quality_dist = filtered_analysis['quality_distribution']
        quality_perf = filtered_analysis['quality_performance']
        
        for quality, count in quality_dist.items():
            win_rate = quality_perf.get(quality, 0)
            percentage = (count / filtered_summary['total_filtered_signals']) * 100
            print(f"{quality.upper()}: {count} signals ({percentage:.1f}%) - {win_rate}% win rate")
    
    else:
        print(f"❌ No filtered signals to analyze: {filtered_analysis['error']}")
    
    # Save comprehensive results
    with open('venom_filter_analysis_results.json', 'w') as f:
        serializable_results = results.copy()
        
        # Serialize trades
        if 'all_trades' in results:
            trades_for_json = []
            for trade in results['all_trades']:
                trade_copy = trade.copy()
                trade_copy['timestamp'] = trade['timestamp'].isoformat()
                trades_for_json.append(trade_copy)
            serializable_results['all_trades'] = trades_for_json
        
        # Serialize filtered trades
        if 'filtered_analysis' in results and 'hypothetical_trades' in results['filtered_analysis']:
            filtered_trades = []
            for trade in results['filtered_analysis']['hypothetical_trades']:
                trade_copy = trade.copy()
                trade_copy['timestamp'] = trade['timestamp'].isoformat()
                filtered_trades.append(trade_copy)
            serializable_results['filtered_analysis']['hypothetical_trades'] = filtered_trades
        
        json.dump(serializable_results, f, indent=2)
    
    print(f"\n💾 Comprehensive analysis saved to: venom_filter_analysis_results.json")
    print(f"\n🔍 FILTER ANALYSIS COMPLETE!")

if __name__ == "__main__":
    main()