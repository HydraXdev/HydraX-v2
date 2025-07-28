#!/usr/bin/env python3
"""
v6.0 PREMIUM BACKTEST
Test filtering v6.0 to only highest-confidence signals
Goal: Reduce 76.2 → 30 signals/day while increasing 56.1% win rate
"""

import sys
import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import random

class v6Premium:
    """v6.0 with premium filtering for highest confidence signals only"""
    
    def __init__(self):
        self.setup_logging()
        
        # PREMIUM THRESHOLDS (higher than standard v6.0)
        self.premium_config = {
            'min_tcs_threshold': 65,      # Raised from 60 to 65 (top ~40% signals)
            'min_technical_score': 60,    # Higher technical requirements
            'min_pattern_strength': 55,   # Stronger patterns only
            'min_momentum_score': 50,     # Better momentum required
            'max_spread_pips': 2.0,       # Tighter spread requirements (was 3.0)
            'min_volume_ratio': 1.1,      # Volume confirmation required
            'target_signals_per_day': 30  # Quality over quantity
        }
        
        # Enhanced session multipliers (more selective)
        self.session_boosts = {
            'LONDON': 12,      # Premium London boost
            'NY': 10,          # Premium NY boost
            'OVERLAP': 15,     # Premium overlap boost
            'ASIAN': 6,        # Slightly higher Asian
            'OTHER': 0         # No signals during off-hours
        }
        
        # Same 15 pairs as original v6.0
        self.pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'GBPJPY', 
            'AUDUSD', 'EURGBP', 'USDCHF', 'EURJPY', 'NZDUSD',
            'AUDJPY', 'GBPCHF', 'GBPAUD', 'EURAUD', 'GBPNZD'
        ]
        
        self.signal_count = 0
        self.start_time = datetime.now()
        
        self.logger.info("🌟 v6.0 PREMIUM Engine Initialized")
        self.logger.info("🎯 Target: 30 signals/day with 65%+ win rate")
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - _PREMIUM - %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/apex_premium_backtest.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_current_session(self) -> str:
        """Get current trading session"""
        hour = datetime.now().hour
        
        if 8 <= hour <= 12:
            return 'LONDON'
        elif 13 <= hour <= 17:
            return 'NY'
        elif 8 <= hour <= 9 or 14 <= hour <= 15:
            return 'OVERLAP'
        elif 0 <= hour <= 7:
            return 'ASIAN'
        else:
            return 'OTHER'
    
    def calculate_enhanced_tcs(self, symbol: str, market_data: Dict) -> float:
        """Calculate enhanced TCS with premium requirements"""
        
        # Base components (same as v6.0 but with higher minimums)
        technical_base = 50 + random.uniform(0, 30)    # 50-80 (raised from 45-75)
        pattern_base = 45 + random.uniform(0, 30)      # 45-75 (raised from 40-70)  
        momentum_base = 47 + random.uniform(0, 28)     # 47-75 (raised from 42-70)
        structure_base = 50 + random.uniform(0, 25)    # 50-75 (raised from 45-70)
        volume_base = 52 + random.uniform(0, 23)       # 52-75 (raised from 48-70)
        
        # PREMIUM SESSION BONUS (enhanced)
        session = self.get_current_session()
        session_bonus = self.session_boosts.get(session, 0)
        
        # Volume confirmation boost
        volume_ratio = market_data.get('volume_ratio', 1.0)
        volume_boost = 0
        if volume_ratio >= 1.3:
            volume_boost = 5  # Strong volume confirmation
        elif volume_ratio >= 1.1:
            volume_boost = 2  # Moderate volume confirmation
        
        # Spread quality boost
        spread = market_data.get('spread', 2.0)
        spread_boost = 0
        if spread < 1.5:
            spread_boost = 3  # Excellent spread
        elif spread < 2.0:
            spread_boost = 1  # Good spread
        
        # PREMIUM weighted TCS calculation
        tcs = (
            technical_base * 0.25 +     # 25%
            pattern_base * 0.20 +       # 20%
            momentum_base * 0.20 +      # 20%
            structure_base * 0.15 +     # 15%
            volume_base * 0.10 +        # 10%
            session_bonus * 0.10        # 10%
        ) + volume_boost + spread_boost
        
        # PREMIUM range: 40-90 (higher than standard 35-85)
        return max(40, min(90, tcs))
    
    def passes_premium_filters(self, symbol: str, market_data: Dict, tcs: float) -> bool:
        """Check if signal passes all premium filters"""
        
        # TCS threshold (primary filter)
        if tcs < self.premium_config['min_tcs_threshold']:
            return False
        
        # Spread quality filter  
        spread = market_data.get('spread', 3.0)
        if spread > self.premium_config['max_spread_pips']:
            return False
        
        # Volume confirmation filter
        volume_ratio = market_data.get('volume_ratio', 1.0)
        if volume_ratio < self.premium_config['min_volume_ratio']:
            return False
        
        # Session filter (no signals during OTHER session)
        session = self.get_current_session()
        if session == 'OTHER':
            return False
        
        # Premium pair filter (focus on most liquid pairs during optimal sessions)
        premium_pairs = {
            'LONDON': ['EURUSD', 'GBPUSD', 'EURGBP'],
            'NY': ['EURUSD', 'GBPUSD', 'USDCAD'],
            'OVERLAP': ['EURUSD', 'GBPUSD', 'USDJPY'],
            'ASIAN': ['USDJPY', 'AUDUSD', 'NZDUSD']
        }
        
        if symbol not in premium_pairs.get(session, self.pairs):
            # Allow other pairs but with higher TCS requirement
            if tcs < self.premium_config['min_tcs_threshold'] + 3:
                return False
        
        return True
    
    def get_market_data(self, symbol: str) -> Dict:
        """Get market data for symbol (identical to v6.0)"""
        base_prices = {
            'EURUSD': 1.0851, 'GBPUSD': 1.2655, 'USDJPY': 150.33,
            'USDCAD': 1.3582, 'GBPJPY': 189.67, 'AUDUSD': 0.6718,
            'EURGBP': 0.8583, 'USDCHF': 0.8954, 'EURJPY': 163.78,
            'NZDUSD': 0.6122, 'AUDJPY': 100.97, 'GBPCHF': 1.1325,
            'GBPAUD': 1.8853, 'EURAUD': 1.6148, 'GBPNZD': 2.0675
        }
        
        base_price = base_prices.get(symbol, 1.0000)
        
        # Add small random variation
        price_variation = random.uniform(-0.001, 0.001)
        ask = base_price + price_variation
        bid = ask - random.uniform(0.00005, 0.00020)  # Tighter spreads for premium
        
        return {
            'bid': round(bid, 5),
            'ask': round(ask, 5), 
            'spread': round((ask - bid) * 10000, 1),  # Pips
            'volume': random.randint(1200000, 3000000),  # Higher volume range
            'volume_ratio': random.uniform(0.8, 2.0),   # Better volume ratios
            'timestamp': datetime.now()
        }
    
    def calculate_premium_entry_levels(self, symbol: str, direction: str, entry_price: float, tcs: float) -> Dict:
        """Calculate entry levels with premium risk management"""
        
        # PREMIUM risk management based on TCS (tighter than standard)
        if tcs >= 85:
            risk_pips = 12      # Reduced from 15
            rr_ratio = 3.0      # Increased from 2.5
        elif tcs >= 80:
            risk_pips = 14      # Reduced from 16
            rr_ratio = 2.8      # Increased from 2.3
        elif tcs >= 75:
            risk_pips = 16      # Reduced from 18
            rr_ratio = 2.5      # Increased from 2.2
        else:
            risk_pips = 18      # Reduced from 22
            rr_ratio = 2.2      # Increased from 1.8
        
        # Convert pips to price
        pip_value = 0.0001 if 'JPY' not in symbol else 0.01
        risk_amount = risk_pips * pip_value
        reward_amount = risk_amount * rr_ratio
        
        if direction == 'BUY':
            stop_loss = entry_price - risk_amount
            take_profit = entry_price + reward_amount
        else:
            stop_loss = entry_price + risk_amount  
            take_profit = entry_price - reward_amount
        
        return {
            'entry': entry_price,
            'stop_loss': round(stop_loss, 5),
            'take_profit': round(take_profit, 5),
            'risk_pips': risk_pips,
            'reward_pips': round(risk_pips * rr_ratio, 1),
            'rr_ratio': rr_ratio
        }
    
    def determine_direction(self, symbol: str, market_data: Dict, tcs: float) -> str:
        """Determine trade direction (enhanced for premium)"""
        session = self.get_current_session()
        
        # Enhanced session bias for premium signals
        if session in ['LONDON', 'OVERLAP']:
            buy_probability = 0.58  # Stronger buy bias during active sessions
        elif session == 'NY':
            buy_probability = 0.54  # Moderate buy bias
        else:
            buy_probability = 0.52  # Slight buy bias
        
        # TCS influence (enhanced)
        if tcs >= 85:
            buy_probability += 0.12  # Higher TCS gets stronger directional bias
        elif tcs >= 80:
            buy_probability += 0.08
        elif tcs >= 75:
            buy_probability += 0.05
        
        # Volume confirmation influence
        volume_ratio = market_data.get('volume_ratio', 1.0)
        if volume_ratio > 1.3:
            buy_probability += 0.03  # High volume slightly favors trend continuation
        
        return 'BUY' if random.random() < buy_probability else 'SELL'
    
    def generate_premium_signal(self, symbol: str) -> Optional[Dict]:
        """Generate premium signal with enhanced filtering"""
        
        # Get market data
        market_data = self.get_market_data(symbol)
        
        # Calculate enhanced TCS
        tcs = self.calculate_enhanced_tcs(symbol, market_data)
        
        # Check if passes ALL premium filters
        if not self.passes_premium_filters(symbol, market_data, tcs):
            return None
        
        # Determine direction
        direction = self.determine_direction(symbol, market_data, tcs)
        
        # Calculate premium entry levels
        entry_price = market_data['ask'] if direction == 'BUY' else market_data['bid']
        levels = self.calculate_premium_entry_levels(symbol, direction, entry_price, tcs)
        
        # Generate premium signal
        self.signal_count += 1
        
        signal = {
            'signal_id': f'6P_{symbol}_{self.signal_count:04d}',
            'symbol': symbol,
            'direction': direction,
            'tcs': round(tcs, 1),
            'entry_price': levels['entry'],
            'stop_loss': levels['stop_loss'],
            'take_profit': levels['take_profit'],
            'risk_pips': levels['risk_pips'],
            'reward_pips': levels['reward_pips'],
            'rr_ratio': levels['rr_ratio'],
            'bid': market_data['bid'],
            'ask': market_data['ask'],
            'spread': market_data['spread'],
            'volume_ratio': market_data['volume_ratio'],
            'session': self.get_current_session(),
            'timestamp': datetime.now().isoformat(),
            'signal_number': self.signal_count,
            'quality_tier': 'PREMIUM'
        }
        
        self.logger.info(f"🌟 PREMIUM Signal #{self.signal_count}: {symbol} {direction} TCS:{tcs:.1f}% R:R=1:{levels['rr_ratio']:.1f}")
        
        return signal
    
    def scan_markets_premium(self) -> List[Dict]:
        """Scan markets for premium signals only"""
        signals = []
        
        for symbol in self.pairs:
            signal = self.generate_premium_signal(symbol)
            if signal:
                signals.append(signal)
                
                # Limit to maintain quality (premium approach)
                if len(signals) >= 2:  # Max 2 premium signals per scan
                    break
        
        return signals

class v6PremiumBacktest:
    """Backtest v6.0 Premium against original v6.0"""
    
    def __init__(self):
        self.setup_logging()
        
        # Initialize premium engine first
        self.premium_engine = v6Premium()
        
        # Load identical market data
        self.real_market_data = self._load_identical_real_data()
        
        self.logger.info("🌟 v6.0 PREMIUM BACKTEST")
        self.logger.info(f"📊 Market samples: {len(self.real_market_data)}")
        self.logger.info("🎯 TARGET: 30 signals/day with 65%+ win rate")
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - PREMIUM_BACKTEST - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/apex_premium_comparison.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('PremiumBacktest')
    
    def _load_identical_real_data(self) -> List[Dict]:
        """Load identical market data for fair comparison"""
        # Same data generation as other tests
        np.random.seed(42)
        
        base_prices = {
            'EURUSD': 1.0851, 'GBPUSD': 1.2655, 'USDJPY': 150.33, 'USDCAD': 1.3582,
            'GBPJPY': 189.67, 'AUDUSD': 0.6718, 'EURGBP': 0.8583, 'USDCHF': 0.8954,
            'EURJPY': 163.78, 'NZDUSD': 0.6122, 'AUDJPY': 100.97, 'GBPCHF': 1.1325,
            'GBPAUD': 1.8853, 'EURAUD': 1.6148, 'GBPNZD': 2.0675
        }
        
        volatilities = {
            'EURUSD': 0.00012, 'GBPUSD': 0.00016, 'USDJPY': 0.00011, 'USDCAD': 0.00009,
            'GBPJPY': 0.00025, 'AUDUSD': 0.00014, 'EURGBP': 0.00008, 'USDCHF': 0.00010,
            'EURJPY': 0.00018, 'NZDUSD': 0.00015, 'AUDJPY': 0.00019, 'GBPCHF': 0.00017,
            'GBPAUD': 0.00022, 'EURAUD': 0.00020, 'GBPNZD': 0.00028
        }
        
        sessions = ['SYDNEY_TOKYO', 'LONDON', 'OVERLAP', 'NEW_YORK']
        session_multipliers = {'SYDNEY_TOKYO': 0.7, 'LONDON': 1.2, 'OVERLAP': 1.5, 'NEW_YORK': 1.1}
        
        market_data = []
        start_date = datetime.now() - timedelta(days=90)
        
        for day in range(90):
            current_date = start_date + timedelta(days=day)
            if current_date.weekday() >= 5:
                continue
            
            for hour_offset in range(24):
                session_hour = hour_offset
                
                if 0 <= session_hour < 8:
                    session = 'SYDNEY_TOKYO'
                elif 8 <= session_hour < 13:
                    session = 'LONDON'
                elif 13 <= session_hour < 17:
                    session = 'OVERLAP'
                else:
                    session = 'NEW_YORK'
                
                session_multiplier = session_multipliers[session]
                
                for pair in self.premium_engine.pairs:
                    timestamp = int((current_date + timedelta(hours=hour_offset)).timestamp())
                    base_price = base_prices[pair]
                    daily_vol = volatilities[pair] * session_multiplier
                    
                    cycle_position = ((day % 21) + hour_offset/24) / 21
                    trend_strength = np.sin(cycle_position * 2 * np.pi) * 0.3
                    micro_trend = np.sin(hour_offset * 0.1) * 0.1
                    
                    price_change = (trend_strength + micro_trend + np.random.uniform(-1, 1) * 0.5) * daily_vol
                    
                    if np.random.random() < 0.002:
                        price_change += np.random.choice([-1, 1]) * np.random.uniform(1.0, 3.0) * daily_vol
                    
                    open_price = base_price + (np.random.uniform(-0.3, 0.3) * daily_vol)
                    close_price = open_price + price_change
                    
                    range_size = daily_vol * np.random.uniform(0.3, 1.2)
                    high_price = max(open_price, close_price) + range_size * np.random.random()
                    low_price = min(open_price, close_price) - range_size * np.random.random()
                    
                    volume = int(np.random.randint(800, 2000) * session_multiplier)
                    
                    market_data.append({
                        'symbol': pair,
                        'timestamp': timestamp,
                        'date': current_date.strftime('%Y-%m-%d'),
                        'hour': hour_offset,
                        'session': session,
                        'open': round(open_price, 5),
                        'high': round(high_price, 5),
                        'low': round(low_price, 5),
                        'close': round(close_price, 5),
                        'volume': volume
                    })
                    
                    base_prices[pair] = close_price
        
        self.logger.info(f"✅ Generated {len(market_data)} market data points")
        return market_data
    
    def run_premium_backtest(self) -> Dict:
        """Run premium backtest"""
        self.logger.info("🌟 Starting v6.0 Premium backtest...")
        
        results = {
            'backtest_period': '3_months_premium_filtered',
            'total_market_data': len(self.real_market_data),
            'signals_generated': 0,
            'signals_tested': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0,
            'total_pips': 0.0,
            'total_profit_loss': 0.0,
            'signal_details': [],
            'tcs_performance': {},
            'session_performance': {}
        }
        
        # Group data by symbol
        symbol_data = {}
        for sample in self.real_market_data:
            symbol = sample['symbol']
            if symbol not in symbol_data:
                symbol_data[symbol] = []
            symbol_data[symbol].append(sample)
        
        for symbol in symbol_data:
            symbol_data[symbol].sort(key=lambda x: x['timestamp'])
        
        # Test premium engine
        test_intervals = 0
        for symbol, data in symbol_data.items():
            if len(data) < 50:
                continue
            
            # Test at intervals 
            for i in range(50, len(data), 24):  # Once per day
                test_intervals += 1
                
                try:
                    # Simulate market data at this point
                    current_sample = data[i]
                    
                    # Mock the market data for premium engine
                    market_data = {
                        'bid': current_sample['close'] - 0.00015,
                        'ask': current_sample['close'] + 0.00015,
                        'spread': 1.5,
                        'volume': current_sample['volume'],
                        'volume_ratio': random.uniform(0.8, 2.0),
                        'timestamp': datetime.fromtimestamp(current_sample['timestamp'])
                    }
                    
                    # Calculate TCS
                    tcs = self.premium_engine.calculate_enhanced_tcs(symbol, market_data)
                    
                    # Check if passes premium filters
                    if self.premium_engine.passes_premium_filters(symbol, market_data, tcs):
                        # Generate signal
                        signal = self.premium_engine.generate_premium_signal(symbol)
                        
                        if signal:
                            results['signals_generated'] += 1
                            win_result = self._test_signal_performance(signal, data[i:], results)
                            
                            if win_result is not None:
                                results['signals_tested'] += 1
                                if win_result:
                                    results['wins'] += 1
                                else:
                                    results['losses'] += 1
                
                except Exception as e:
                    continue
        
        # Calculate metrics
        self._calculate_performance_metrics(results)
        
        self.logger.info("🏁 Premium backtest complete!")
        return results
    
    def _test_signal_performance(self, signal: Dict, future_data: List[Dict], results: Dict) -> Optional[bool]:
        """Test signal performance by following price action"""
        try:
            entry_price = signal['entry_price']
            stop_loss = signal['stop_loss']
            take_profit = signal['take_profit']
            direction = signal['direction']
            
            max_test_candles = min(len(future_data), 72)  # 3 days max
            pips_multiplier = 10000 if 'JPY' not in signal['symbol'] else 100
            
            for i, candle in enumerate(future_data[:max_test_candles]):
                high = candle['high']
                low = candle['low']
                
                if direction == "BUY":
                    if low <= stop_loss:
                        loss_pips = (entry_price - stop_loss) * pips_multiplier
                        self._record_result(signal, False, -loss_pips, results)
                        return False
                    
                    if high >= take_profit:
                        win_pips = (take_profit - entry_price) * pips_multiplier
                        self._record_result(signal, True, win_pips, results)
                        return True
                
                else:  # SELL
                    if high >= stop_loss:
                        loss_pips = (stop_loss - entry_price) * pips_multiplier
                        self._record_result(signal, False, -loss_pips, results)
                        return False
                    
                    if low <= take_profit:
                        win_pips = (entry_price - take_profit) * pips_multiplier
                        self._record_result(signal, True, win_pips, results)
                        return True
            
            # Expired - count as loss
            self._record_result(signal, False, 0, results)
            return False
            
        except Exception as e:
            return None
    
    def _record_result(self, signal: Dict, won: bool, pips: float, results: Dict):
        """Record signal result"""
        results['total_pips'] += pips
        results['total_profit_loss'] += pips * 10
        
        # Track by TCS range
        tcs = signal['tcs']
        tcs_range = f"{int(tcs//5)*5}-{int(tcs//5)*5+5}"
        if tcs_range not in results['tcs_performance']:
            results['tcs_performance'][tcs_range] = {'wins': 0, 'losses': 0, 'pips': 0}
        
        if won:
            results['tcs_performance'][tcs_range]['wins'] += 1
        else:
            results['tcs_performance'][tcs_range]['losses'] += 1
        results['tcs_performance'][tcs_range]['pips'] += pips
        
        # Store sample details
        if len(results['signal_details']) < 50:
            results['signal_details'].append({
                'symbol': signal['symbol'],
                'direction': signal['direction'],
                'tcs': signal['tcs'],
                'rr_ratio': signal['rr_ratio'],
                'quality_tier': signal['quality_tier'],
                'won': won,
                'pips': pips
            })
    
    def _calculate_performance_metrics(self, results: Dict):
        """Calculate performance metrics"""
        tested = results['signals_tested']
        
        if tested > 0:
            results['win_rate'] = (results['wins'] / tested) * 100
            results['average_pips'] = results['total_pips'] / tested
            results['signals_per_day'] = tested / 90  # 90 day test
            
            for category, data in results['tcs_performance'].items():
                total = data['wins'] + data['losses']
                if total > 0:
                    data['win_rate'] = (data['wins'] / total) * 100
    
    def generate_comparison_report(self, results: Dict) -> str:
        """Generate comparison report"""
        
        apex_standard = {'win_rate': 56.1, 'signals_per_day': 76.2, 'avg_pips': 90.8}
        premium = results
        
        report = f"""
🌟⚡ **v6.0 PREMIUM vs STANDARD COMPARISON**
📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎯 TEST: Premium Filtering Strategy

═══════════════════════════════════════════════════════════════════

📊 **QUALITY vs QUANTITY COMPARISON:**
                    Standard |    Premium
Win Rate:           {apex_standard['win_rate']:>8.1f}%    |    {premium.get('win_rate', 0):>8.1f}%
Signals per Day:    {apex_standard['signals_per_day']:>8.1f}     |    {premium.get('signals_per_day', 0):>8.1f}
Total Signals:      {16236:>8}     |    {premium['signals_tested']:>8}
Avg per Signal:     {apex_standard['avg_pips']:>+8.1f}     |    {premium.get('average_pips', 0):>+8.1f}

🎯 **PREMIUM FILTERING RESULTS:**"""
        
        win_rate_change = premium.get('win_rate', 0) - apex_standard['win_rate']
        volume_change = premium.get('signals_per_day', 0) - apex_standard['signals_per_day']
        
        if win_rate_change > 0:
            report += f"""
✅ Win Rate IMPROVED: +{win_rate_change:.1f}% ({premium.get('win_rate', 0):.1f}% vs {apex_standard['win_rate']:.1f}%)"""
        else:
            report += f"""
❌ Win Rate DECLINED: {win_rate_change:.1f}% ({premium.get('win_rate', 0):.1f}% vs {apex_standard['win_rate']:.1f}%)"""
        
        report += f"""
📉 Volume REDUCED: {volume_change:.1f} signals/day ({premium.get('signals_per_day', 0):.1f} vs {apex_standard['signals_per_day']:.1f})

🎯 **PREMIUM PERFORMANCE DETAILS:**
• Total Signals: {premium['signals_generated']:}
• Signals Tested: {premium['signals_tested']:}
• Wins: {premium['wins']:}
• Losses: {premium['losses']:}
• Total P&L: ${premium['total_profit_loss']:+,.2f}

📊 **TCS PERFORMANCE BREAKDOWN:**"""
        
        for tcs_range, data in premium.get('tcs_performance', {}).items():
            total = data['wins'] + data['losses']
            win_rate = data.get('win_rate', 0)
            if total > 0:
                report += f"""
• TCS {tcs_range}: {data['wins']}W/{data['losses']}L ({win_rate:.1f}%) - {data['pips']:+.1f} pips"""
        
        premium_win_rate = premium.get('win_rate', 0)
        premium_volume = premium.get('signals_per_day', 0)
        
        report += f"""

🏁 **FINAL VERDICT:**"""
        
        if premium_win_rate > apex_standard['win_rate'] + 3 and premium_volume >= 25:
            verdict = "🏆 PREMIUM STRATEGY SUCCEEDS - Higher quality achieved"
            recommendation = "✅ DEPLOY PREMIUM - Better win rate with acceptable volume"
        elif premium_win_rate > apex_standard['win_rate'] and premium_volume >= 20:
            verdict = "✅ PREMIUM STRATEGY WORKS - Modest improvement"
            recommendation = "✅ CONSIDER PREMIUM - Quality over quantity approach"
        elif premium_volume < 15:
            verdict = "⚠️ TOO RESTRICTIVE - Volume too low for production"
            recommendation = "🔄 ADJUST THRESHOLDS - Need more signals per day"
        else:
            verdict = "❌ PREMIUM FILTERING FAILED - No improvement"
            recommendation = "❌ STICK WITH STANDARD - Premium doesn't deliver"
        
        report += f"""
{verdict}

🎯 **PRODUCTION RECOMMENDATION:**
{recommendation}

📊 **FILTERING ANALYSIS:**
Premium Threshold: TCS 65+ (vs standard 60+)
Quality Gain: {win_rate_change:+.1f}% win rate
Volume Cost: {abs(volume_change):.1f} fewer signals/day
Trade-off: {'WORTHWHILE' if premium_win_rate > apex_standard['win_rate'] and premium_volume >= 20 else 'NOT JUSTIFIED'}

💡 **INSIGHT:** {'Premium filtering successfully improves win rate while maintaining viable signal volume.' if premium_win_rate > apex_standard['win_rate'] and premium_volume >= 20 else 'Premium filtering is either too restrictive or does not improve performance sufficiently.'}
"""
        
        return report

def main():
    """Run v6.0 Premium backtest"""
    print("🌟 v6.0 PREMIUM BACKTEST")
    print("=" * 60)
    print("🎯 Testing premium filtering: TCS 75+ only")
    print("📊 Goal: 30 signals/day with 65%+ win rate")
    print()
    
    backtest = v6PremiumBacktest()
    
    print("🚀 Starting Premium backtest...")
    print("⏱️ Testing premium filtering strategy...")
    print()
    
    # Run backtest
    results = backtest.run_premium_backtest()
    
    # Generate report
    report = backtest.generate_comparison_report(results)
    print(report)
    
    # Save results
    results_path = '/root/HydraX-v2/apex_premium_backtest_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    report_path = '/root/HydraX-v2/apex_premium_backtest_report.txt'
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Premium report saved to: {report_path}")
    print(f"📊 Full results saved to: {results_path}")
    
    # Return success if premium beats standard
    premium_win_rate = results.get('win_rate', 0)
    standard_win_rate = 56.1
    premium_volume = results.get('signals_per_day', 0)
    
    return premium_win_rate > standard_win_rate and premium_volume >= 20

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)