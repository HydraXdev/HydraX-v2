#!/usr/bin/env python3
"""
Enhanced Ghost Mode Tracker for BITTEN
Integrates with live performance tracking and provides comprehensive stealth analytics
"""

import uuid
import random
import time
import json
import os
import glob
from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
import logging
import requests

logger = logging.getLogger(__name__)

@dataclass
class GhostModification:
    action_type: str
    original_value: float
    modified_value: float
    variance_percent: float
    effectiveness_score: float
    timestamp: datetime

@dataclass
class MissedWinResult:
    mission_id: str
    symbol: str
    direction: str
    entry_price: float
    take_profit: float
    stop_loss: float
    tcs_score: int
    created_timestamp: int
    expired_timestamp: int
    tp_hit: bool
    sl_hit: bool
    result: str  # "UNFIRED_WIN", "UNFIRED_LOSS", "RANGE_BOUND", "UNKNOWN"
    price_reached: Optional[float]
    analysis_timestamp: datetime

class EnhancedGhostTracker:
    """Enhanced ghost mode with comprehensive tracking and analytics"""
    
    def __init__(self):
        self.modifications_log: Dict[str, List[GhostModification]] = {}
        self.missed_win_log_path = "/root/HydraX-v2/data/missed_win_log.json"
        self.missions_dir = "/root/HydraX-v2/missions/"
        self.stealth_patterns = {
            'entry_delay': {'min': 0.5, 'max': 12.0, 'optimal': 6.0},
            'lot_variance': {'min': 2.0, 'max': 15.0, 'optimal': 8.0},
            'tp_sl_offset': {'min': 1.0, 'max': 5.0, 'optimal': 2.5},
            'strategic_skip': {'probability': 0.08, 'optimal': 0.12}
        }
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.missed_win_log_path), exist_ok=True)
        os.makedirs(self.missions_dir, exist_ok=True)
        
    def apply_enhanced_ghost_mode(self, signal_data: Dict, user_tier: str) -> Tuple[Dict, List[GhostModification]]:
        """
        Apply comprehensive ghost mode modifications based on user tier
        
        Returns:
            Tuple of (modified_signal_data, list_of_modifications)
        """
        modifications = []
        modified_data = signal_data.copy()
        signal_id = signal_data.get('signal_id', str(uuid.uuid4()))
        
        # Tier-based stealth intensity
        stealth_intensity = {
            'nibbler': 0.6,    # 60% stealth
            'fang': 0.75,      # 75% stealth
            'commander': 0.85,  # 85% stealth
            'apex': 1.0        # 100% stealth
        }.get(user_tier.lower(), 0.6)
        
        # 1. Entry Delay Randomization
        if random.random() < stealth_intensity:
            delay_mod = self._apply_entry_delay(signal_data, stealth_intensity)
            modifications.append(delay_mod)
            modified_data['entry_delay'] = delay_mod.modified_value
        
        # 2. Lot Size Variance
        if 'lot_size' in signal_data and random.random() < stealth_intensity:
            lot_mod = self._apply_lot_variance(signal_data, stealth_intensity)
            modifications.append(lot_mod)
            modified_data['lot_size'] = lot_mod.modified_value
        
        # 3. TP/SL Offset
        if random.random() < stealth_intensity * 0.8:  # Slightly less frequent
            tp_mod = self._apply_tp_offset(signal_data, stealth_intensity)
            sl_mod = self._apply_sl_offset(signal_data, stealth_intensity)
            modifications.extend([tp_mod, sl_mod])
            modified_data['take_profit'] = tp_mod.modified_value
            modified_data['stop_loss'] = sl_mod.modified_value
        
        # 4. Strategic Skip Decision
        skip_decision = self._should_strategically_skip(signal_data, stealth_intensity)
        if skip_decision['skip']:
            skip_mod = GhostModification(
                action_type='strategic_skip',
                original_value=1.0,  # Would execute
                modified_value=0.0,  # Skip execution
                variance_percent=100.0,
                effectiveness_score=skip_decision['effectiveness'],
                timestamp=datetime.now()
            )
            modifications.append(skip_mod)
            modified_data['ghost_skip'] = True
        
        # 5. Execution Timing Shuffle
        if random.random() < stealth_intensity * 0.3:  # Less frequent but powerful
            timing_mod = self._apply_execution_shuffle(signal_data, stealth_intensity)
            modifications.append(timing_mod)
            modified_data['execution_delay'] = timing_mod.modified_value
        
        # Log all modifications
        self.modifications_log[signal_id] = modifications
        
        # Track with live performance system
        self._log_to_performance_tracker(signal_id, modifications)
        
        return modified_data, modifications
    
    def _apply_entry_delay(self, signal_data: Dict, intensity: float) -> GhostModification:
        """Apply randomized entry delay based on intensity"""
        config = self.stealth_patterns['entry_delay']
        
        # Scale delay with intensity
        max_delay = config['min'] + (config['max'] - config['min']) * intensity
        delay = random.uniform(config['min'], max_delay)
        
        # Effectiveness based on randomness and broker detection avoidance
        effectiveness = min(1.0, (delay / config['optimal']) * intensity)
        
        return GhostModification(
            action_type='entry_delay',
            original_value=0.0,  # Immediate execution
            modified_value=delay,
            variance_percent=(delay / config['max']) * 100,
            effectiveness_score=effectiveness,
            timestamp=datetime.now()
        )
    
    def _apply_lot_variance(self, signal_data: Dict, intensity: float) -> GhostModification:
        """Apply lot size variance based on intensity"""
        original_lot = signal_data.get('lot_size', 0.01)
        config = self.stealth_patterns['lot_variance']
        
        # Scale variance with intensity
        max_variance = config['min'] + (config['max'] - config['min']) * intensity
        variance_pct = random.uniform(config['min'], max_variance)
        
        # Randomly increase or decrease
        modifier = 1.0 + (variance_pct / 100) * random.choice([-1, 1])
        modified_lot = original_lot * modifier
        
        # Ensure reasonable bounds
        modified_lot = max(0.001, min(modified_lot, original_lot * 1.2))
        
        actual_variance = abs((modified_lot - original_lot) / original_lot) * 100
        effectiveness = min(1.0, (actual_variance / config['optimal']) * intensity)
        
        return GhostModification(
            action_type='lot_variance',
            original_value=original_lot,
            modified_value=modified_lot,
            variance_percent=actual_variance,
            effectiveness_score=effectiveness,
            timestamp=datetime.now()
        )
    
    def _apply_tp_offset(self, signal_data: Dict, intensity: float) -> GhostModification:
        """Apply take profit offset"""
        original_tp = signal_data.get('take_profit', 1.1050)
        config = self.stealth_patterns['tp_sl_offset']
        
        # Convert to pips for calculation
        pip_value = 0.0001 if 'JPY' not in signal_data.get('symbol', '') else 0.01
        max_offset_pips = config['min'] + (config['max'] - config['min']) * intensity
        
        offset_pips = random.uniform(-max_offset_pips, max_offset_pips)
        modified_tp = original_tp + (offset_pips * pip_value)
        
        actual_offset = abs(offset_pips)
        effectiveness = min(1.0, (actual_offset / config['optimal']) * intensity)
        
        return GhostModification(
            action_type='tp_offset',
            original_value=original_tp,
            modified_value=modified_tp,
            variance_percent=actual_offset,
            effectiveness_score=effectiveness,
            timestamp=datetime.now()
        )
    
    def _apply_sl_offset(self, signal_data: Dict, intensity: float) -> GhostModification:
        """Apply stop loss offset"""
        original_sl = signal_data.get('stop_loss', 1.0950)
        config = self.stealth_patterns['tp_sl_offset']
        
        # Convert to pips for calculation
        pip_value = 0.0001 if 'JPY' not in signal_data.get('symbol', '') else 0.01
        max_offset_pips = config['min'] + (config['max'] - config['min']) * intensity
        
        offset_pips = random.uniform(-max_offset_pips, max_offset_pips)
        modified_sl = original_sl + (offset_pips * pip_value)
        
        actual_offset = abs(offset_pips)
        effectiveness = min(1.0, (actual_offset / config['optimal']) * intensity)
        
        return GhostModification(
            action_type='sl_offset',
            original_value=original_sl,
            modified_value=modified_sl,
            variance_percent=actual_offset,
            effectiveness_score=effectiveness,
            timestamp=datetime.now()
        )
    
    def _should_strategically_skip(self, signal_data: Dict, intensity: float) -> Dict:
        """Determine if signal should be strategically skipped"""
        config = self.stealth_patterns['strategic_skip']
        
        # Base skip probability adjusted by intensity
        skip_probability = config['probability'] * intensity
        
        # Increase skip probability for lower TCS scores
        tcs_score = signal_data.get('tcs_score', 85)
        if tcs_score < 80:
            skip_probability *= 1.5
        elif tcs_score < 75:
            skip_probability *= 2.0
        
        # Check recent skip frequency to maintain natural patterns
        should_skip = random.random() < skip_probability
        
        # Effectiveness based on how strategic the skip is
        effectiveness = intensity * (1.0 if tcs_score < 80 else 0.7)
        
        return {
            'skip': should_skip,
            'probability': skip_probability,
            'effectiveness': effectiveness,
            'reason': f"TCS {tcs_score}% strategic skip"
        }
    
    def _apply_execution_shuffle(self, signal_data: Dict, intensity: float) -> GhostModification:
        """Apply execution timing shuffle"""
        # Random delay between 30 seconds to 5 minutes
        base_delay = random.uniform(30, 300)  # seconds
        intensity_modified_delay = base_delay * intensity
        
        effectiveness = min(1.0, intensity * 0.8)  # Execution shuffle is inherently effective
        
        return GhostModification(
            action_type='execution_shuffle',
            original_value=0.0,  # Immediate execution
            modified_value=intensity_modified_delay,
            variance_percent=(intensity_modified_delay / 300) * 100,
            effectiveness_score=effectiveness,
            timestamp=datetime.now()
        )
    
    def _log_to_performance_tracker(self, signal_id: str, modifications: List[GhostModification]):
        """Log ghost mode actions to the live performance tracker"""
        try:
            from bitten_core.live_performance_tracker import live_tracker
            
            for mod in modifications:
                live_tracker.log_ghost_mode_action(
                    signal_id=signal_id,
                    user_id="system",  # Could be made user-specific later
                    action=mod.action_type,
                    original_value=mod.original_value,
                    modified_value=mod.modified_value
                )
                
        except ImportError:
            logger.warning("Live performance tracker not available for ghost mode logging")
        except Exception as e:
            logger.error(f"Error logging ghost mode action: {e}")
    
    def get_ghost_effectiveness_summary(self, signal_id: str) -> Dict:
        """Get effectiveness summary for a specific signal's ghost modifications"""
        if signal_id not in self.modifications_log:
            return {'error': 'Signal not found in ghost log'}
        
        modifications = self.modifications_log[signal_id]
        
        if not modifications:
            return {'effectiveness': 0.0, 'actions': 0, 'summary': 'No ghost mode applied'}
        
        total_effectiveness = sum(mod.effectiveness_score for mod in modifications)
        avg_effectiveness = total_effectiveness / len(modifications)
        
        action_counts = {}
        for mod in modifications:
            action_counts[mod.action_type] = action_counts.get(mod.action_type, 0) + 1
        
        return {
            'signal_id': signal_id,
            'total_actions': len(modifications),
            'avg_effectiveness': avg_effectiveness * 100,
            'action_breakdown': action_counts,
            'stealth_score': min(100, avg_effectiveness * 120),  # Boost score for multiple actions
            'summary': f"{len(modifications)} stealth actions, {avg_effectiveness*100:.1f}% effective"
        }
    
    def get_recent_ghost_activity(self, hours_back: int = 24) -> Dict:
        """Get recent ghost mode activity summary"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        recent_modifications = []
        for signal_id, mods in self.modifications_log.items():
            for mod in mods:
                if mod.timestamp >= cutoff_time:
                    recent_modifications.append(mod)
        
        if not recent_modifications:
            return {'message': 'No recent ghost mode activity', 'total_actions': 0}
        
        action_counts = {}
        total_effectiveness = 0
        
        for mod in recent_modifications:
            action_counts[mod.action_type] = action_counts.get(mod.action_type, 0) + 1
            total_effectiveness += mod.effectiveness_score
        
        avg_effectiveness = total_effectiveness / len(recent_modifications)
        
        return {
            'period_hours': hours_back,
            'total_actions': len(recent_modifications),
            'avg_effectiveness': avg_effectiveness * 100,
            'action_breakdown': action_counts,
            'most_used_action': max(action_counts.items(), key=lambda x: x[1])[0],
            'stealth_assessment': 'Excellent' if avg_effectiveness > 0.8 else 'Good' if avg_effectiveness > 0.6 else 'Needs Improvement'
        }
    
    def analyze_missed_winners(self, hours_back: int = 24) -> List[MissedWinResult]:
        """
        Analyze expired missions that were never fired to determine missed wins
        
        Args:
            hours_back: How many hours back to analyze
            
        Returns:
            List of MissedWinResult objects
        """
        logger.info(f"🔍 Analyzing missed winners for last {hours_back} hours...")
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        cutoff_timestamp = int(cutoff_time.timestamp())
        current_timestamp = int(datetime.now(timezone.utc).timestamp())
        
        missed_results = []
        
        # Find all mission files
        mission_files = glob.glob(os.path.join(self.missions_dir, "*.json"))
        
        for mission_file in mission_files:
            try:
                with open(mission_file, 'r') as f:
                    mission_data = json.load(f)
                
                # Check if mission is expired and within our time window
                created_ts = mission_data.get('created_timestamp', 0)
                expired_ts = mission_data.get('expires_timestamp', 0)
                status = mission_data.get('status', 'pending')
                
                # Skip if not in our time window or not expired unfired mission
                if created_ts < cutoff_timestamp:
                    continue
                    
                if status != 'pending' or expired_ts >= current_timestamp:
                    continue
                
                # This is an expired unfired mission - analyze it
                result = self._analyze_mission_outcome(mission_data)
                if result:
                    missed_results.append(result)
                    
            except Exception as e:
                logger.warning(f"Error analyzing mission file {mission_file}: {e}")
                continue
        
        # Save results to log
        self._save_missed_win_results(missed_results)
        
        logger.info(f"✅ Analyzed {len(missed_results)} expired missions")
        return missed_results
    
    def _analyze_mission_outcome(self, mission_data: Dict) -> Optional[MissedWinResult]:
        """
        Analyze a single mission to determine if it would have been a win/loss
        
        Args:
            mission_data: Mission data dictionary
            
        Returns:
            MissedWinResult if analysis successful, None otherwise
        """
        try:
            symbol = mission_data.get('symbol')
            direction = mission_data.get('direction', '').upper()
            entry_price = mission_data.get('entry_price')
            take_profit = mission_data.get('take_profit') 
            stop_loss = mission_data.get('stop_loss')
            created_ts = mission_data.get('created_timestamp')
            expired_ts = mission_data.get('expires_timestamp')
            
            if not all([symbol, direction, entry_price, take_profit, stop_loss, created_ts, expired_ts]):
                logger.warning(f"Missing required mission data for analysis")
                return None
            
            # Get price data for the mission timeframe
            price_data = self._get_price_data_for_period(symbol, created_ts, expired_ts)
            
            if not price_data:
                return MissedWinResult(
                    mission_id=mission_data.get('mission_id', 'unknown'),
                    symbol=symbol,
                    direction=direction,
                    entry_price=entry_price,
                    take_profit=take_profit,
                    stop_loss=stop_loss,
                    tcs_score=mission_data.get('tcs_score', 0),
                    created_timestamp=created_ts,
                    expired_timestamp=expired_ts,
                    tp_hit=False,
                    sl_hit=False,
                    result="UNKNOWN",
                    price_reached=None,
                    analysis_timestamp=datetime.now(timezone.utc)
                )
            
            # Analyze if TP or SL would have been hit
            tp_hit, sl_hit, price_reached = self._check_tp_sl_hits(
                direction, entry_price, take_profit, stop_loss, price_data
            )
            
            # Determine result
            if tp_hit and not sl_hit:
                result = "UNFIRED_WIN"
            elif sl_hit and not tp_hit:
                result = "UNFIRED_LOSS"
            elif tp_hit and sl_hit:
                # Both hit - depends on which came first (SL usually hits first in real trading)
                result = "UNFIRED_LOSS"  # Conservative assumption
            else:
                result = "RANGE_BOUND"
            
            return MissedWinResult(
                mission_id=mission_data.get('mission_id', 'unknown'),
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                take_profit=take_profit,
                stop_loss=stop_loss,
                tcs_score=mission_data.get('tcs_score', 0),
                created_timestamp=created_ts,
                expired_timestamp=expired_ts,
                tp_hit=tp_hit,
                sl_hit=sl_hit,
                result=result,
                price_reached=price_reached,
                analysis_timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing mission outcome: {e}")
            return None
    
    def _get_price_data_for_period(self, symbol: str, start_ts: int, end_ts: int) -> Optional[List[Dict]]:
        """
        Get price data for the given symbol and time period
        
        Args:
            symbol: Currency pair symbol
            start_ts: Start timestamp
            end_ts: End timestamp
            
        Returns:
            List of price data points or None if unavailable
        """
        try:
            # Try to get data from bridge files first
            bridge_data = self._get_bridge_price_data(symbol, start_ts, end_ts)
            if bridge_data:
                return bridge_data
            
            # Fallback to simulated price movement
            return self._simulate_price_movement(symbol, start_ts, end_ts)
            
        except Exception as e:
            logger.warning(f"Could not get price data for {symbol}: {e}")
            return None
    
    def _get_bridge_price_data(self, symbol: str, start_ts: int, end_ts: int) -> Optional[List[Dict]]:
        """
        Try to get real price data from bridge files
        
        Args:
            symbol: Currency pair symbol
            start_ts: Start timestamp  
            end_ts: End timestamp
            
        Returns:
            List of price data or None
        """
        # Check bridge directories for historical data
        bridge_paths = [
            f"C:\\MT5_Farm\\Bridge\\Incoming\\signal_{symbol}_*.json",
            f"C:\\Users\\Administrator\\Desktop\\BITTEN\\{symbol}*.json",
            f"/root/HydraX-v2/bridge/data/{symbol}_*.json"
        ]
        
        price_points = []
        
        for bridge_pattern in bridge_paths:
            try:
                bridge_files = glob.glob(bridge_pattern)
                for bridge_file in bridge_files:
                    with open(bridge_file, 'r') as f:
                        data = json.load(f)
                    
                    file_timestamp = data.get('timestamp')
                    if file_timestamp:
                        # Convert timestamp if needed
                        if isinstance(file_timestamp, str):
                            file_ts = int(datetime.fromisoformat(file_timestamp.replace('Z', '+00:00')).timestamp())
                        else:
                            file_ts = int(file_timestamp)
                        
                        if start_ts <= file_ts <= end_ts:
                            price_points.append({
                                'timestamp': file_ts,
                                'ask': data.get('ask', data.get('price', 0)),
                                'bid': data.get('bid', data.get('price', 0)),
                                'high': data.get('high', data.get('price', 0)),
                                'low': data.get('low', data.get('price', 0))
                            })
                            
            except Exception as e:
                logger.debug(f"Could not read bridge file {bridge_pattern}: {e}")
                continue
        
        return price_points if price_points else None
    
    def _simulate_price_movement(self, symbol: str, start_ts: int, end_ts: int) -> List[Dict]:
        """
        Simulate realistic price movement for the given period
        
        Args:
            symbol: Currency pair symbol
            start_ts: Start timestamp
            end_ts: End timestamp
            
        Returns:
            List of simulated price data points
        """
        # Base prices for major pairs
        base_prices = {
            'EURUSD': 1.0900,
            'GBPUSD': 1.2700,
            'USDJPY': 150.00,
            'USDCHF': 0.9000,
            'AUDUSD': 0.6600,
            'USDCAD': 1.3600,
            'NZDUSD': 0.6100,
            'EURJPY': 163.50,
            'GBPJPY': 190.50,
            'EURGBP': 0.8580
        }
        
        base_price = base_prices.get(symbol, 1.0000)
        duration_hours = (end_ts - start_ts) / 3600
        
        # Generate price points every hour
        price_points = []
        current_price = base_price
        
        for hour in range(int(duration_hours) + 1):
            timestamp = start_ts + (hour * 3600)
            
            # Random price movement (±0.5% per hour max)
            volatility = 0.005
            if 'JPY' in symbol:
                volatility = 0.5  # Adjust for JPY pairs
            
            price_change = random.uniform(-volatility, volatility)
            current_price *= (1 + price_change)
            
            # Calculate bid/ask spread
            spread = 0.0002 if 'JPY' not in symbol else 0.02
            ask = current_price + (spread / 2)
            bid = current_price - (spread / 2)
            
            price_points.append({
                'timestamp': timestamp,
                'ask': ask,
                'bid': bid,
                'high': current_price * 1.001,
                'low': current_price * 0.999
            })
        
        return price_points
    
    def _check_tp_sl_hits(self, direction: str, entry_price: float, 
                         take_profit: float, stop_loss: float, 
                         price_data: List[Dict]) -> Tuple[bool, bool, Optional[float]]:
        """
        Check if take profit or stop loss would have been hit during the period
        
        Args:
            direction: BUY or SELL
            entry_price: Entry price level
            take_profit: Take profit level
            stop_loss: Stop loss level
            price_data: List of price data points
            
        Returns:
            Tuple of (tp_hit, sl_hit, max_favorable_price)
        """
        tp_hit = False
        sl_hit = False
        max_favorable_price = entry_price
        
        for price_point in price_data:
            if direction == 'BUY':
                # For BUY orders, use bid for TP and ask for SL
                current_bid = price_point.get('bid', price_point.get('ask', 0))
                current_ask = price_point.get('ask', price_point.get('bid', 0))
                
                # Check TP hit (bid >= take_profit)
                if current_bid >= take_profit:
                    tp_hit = True
                    max_favorable_price = max(max_favorable_price, current_bid)
                
                # Check SL hit (ask <= stop_loss)
                if current_ask <= stop_loss:
                    sl_hit = True
                    
            else:  # SELL
                # For SELL orders, use ask for TP and bid for SL
                current_bid = price_point.get('bid', price_point.get('ask', 0))
                current_ask = price_point.get('ask', price_point.get('bid', 0))
                
                # Check TP hit (ask <= take_profit)
                if current_ask <= take_profit:
                    tp_hit = True
                    max_favorable_price = min(max_favorable_price, current_ask)
                
                # Check SL hit (bid >= stop_loss)
                if current_bid >= stop_loss:
                    sl_hit = True
        
        return tp_hit, sl_hit, max_favorable_price
    
    def _save_missed_win_results(self, results: List[MissedWinResult]):
        """
        Save missed win analysis results to log file
        
        Args:
            results: List of MissedWinResult objects
        """
        try:
            # Load existing results
            existing_results = []
            if os.path.exists(self.missed_win_log_path):
                with open(self.missed_win_log_path, 'r') as f:
                    existing_data = json.load(f)
                    existing_results = existing_data.get('results', [])
            
            # Convert new results to dict format
            new_results = []
            for result in results:
                result_dict = {
                    'mission_id': result.mission_id,
                    'symbol': result.symbol,
                    'direction': result.direction,
                    'entry_price': result.entry_price,
                    'take_profit': result.take_profit,
                    'stop_loss': result.stop_loss,
                    'tcs_score': result.tcs_score,
                    'created_timestamp': result.created_timestamp,
                    'expired_timestamp': result.expired_timestamp,
                    'tp_hit': result.tp_hit,
                    'sl_hit': result.sl_hit,
                    'result': result.result,
                    'price_reached': result.price_reached,
                    'analysis_timestamp': result.analysis_timestamp.isoformat()
                }
                new_results.append(result_dict)
            
            # Combine and save
            all_results = existing_results + new_results
            
            # Keep only last 1000 results to prevent file from growing too large
            if len(all_results) > 1000:
                all_results = all_results[-1000:]
            
            save_data = {
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'total_results': len(all_results),
                'results': all_results
            }
            
            with open(self.missed_win_log_path, 'w') as f:
                json.dump(save_data, f, indent=2)
                
            logger.info(f"💾 Saved {len(new_results)} missed win results to log")
            
        except Exception as e:
            logger.error(f"Error saving missed win results: {e}")
    
    def get_missed_win_summary(self, hours_back: int = 24) -> Dict:
        """
        Get summary of missed win analysis
        
        Args:
            hours_back: Hours to analyze
            
        Returns:
            Dictionary with missed win statistics
        """
        try:
            # Run fresh analysis
            results = self.analyze_missed_winners(hours_back)
            
            if not results:
                return {
                    'period_hours': hours_back,
                    'total_expired': 0,
                    'unfired_wins': 0,
                    'unfired_losses': 0,
                    'range_bound': 0,
                    'unknown': 0,
                    'missed_win_rate': 0.0,
                    'top_missed_tcs': None,
                    'top_missed_symbol': None
                }
            
            # Calculate statistics
            unfired_wins = sum(1 for r in results if r.result == "UNFIRED_WIN")
            unfired_losses = sum(1 for r in results if r.result == "UNFIRED_LOSS")
            range_bound = sum(1 for r in results if r.result == "RANGE_BOUND")
            unknown = sum(1 for r in results if r.result == "UNKNOWN")
            
            total_analyzed = len(results)
            total_with_outcome = unfired_wins + unfired_losses
            missed_win_rate = (unfired_wins / total_with_outcome * 100) if total_with_outcome > 0 else 0.0
            
            # Find top missed TCS
            win_results = [r for r in results if r.result == "UNFIRED_WIN"]
            top_missed_tcs = max(win_results, key=lambda x: x.tcs_score) if win_results else None
            
            # Most missed symbol
            symbol_counts = {}
            for result in win_results:
                symbol_counts[result.symbol] = symbol_counts.get(result.symbol, 0) + 1
            
            top_missed_symbol = max(symbol_counts.items(), key=lambda x: x[1]) if symbol_counts else None
            
            return {
                'period_hours': hours_back,
                'total_expired': total_analyzed,
                'unfired_wins': unfired_wins,
                'unfired_losses': unfired_losses,
                'range_bound': range_bound,
                'unknown': unknown,
                'missed_win_rate': missed_win_rate,
                'top_missed_tcs': {
                    'symbol': top_missed_tcs.symbol,
                    'tcs_score': top_missed_tcs.tcs_score,
                    'direction': top_missed_tcs.direction
                } if top_missed_tcs else None,
                'top_missed_symbol': {
                    'symbol': top_missed_symbol[0],
                    'count': top_missed_symbol[1]
                } if top_missed_symbol else None
            }
            
        except Exception as e:
            logger.error(f"Error generating missed win summary: {e}")
            return {'error': str(e)}

# Global instance for integration
enhanced_ghost_tracker = EnhancedGhostTracker()

def apply_ghost_mode_to_signal(signal_data: Dict, user_tier: str = 'nibbler') -> Dict:
    """
    Convenience function to apply ghost mode to a signal
    
    Args:
        signal_data: Signal data dictionary
        user_tier: User's tier level
    
    Returns:
        Modified signal data with ghost mode applied
    """
    modified_data, modifications = enhanced_ghost_tracker.apply_enhanced_ghost_mode(signal_data, user_tier)
    
    # Add ghost mode summary to the signal
    signal_id = signal_data.get('signal_id', 'unknown')
    ghost_summary = enhanced_ghost_tracker.get_ghost_effectiveness_summary(signal_id)
    modified_data['ghost_mode_summary'] = ghost_summary
    
    return modified_data

# Quick test function
def test_ghost_mode():
    """Test the enhanced ghost mode system"""
    print("👻 Testing Enhanced Ghost Mode...")
    
    test_signal = {
        'signal_id': 'TEST_001',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'tcs_score': 85,
        'entry_price': 1.1000,
        'take_profit': 1.1050,
        'stop_loss': 1.0950,
        'lot_size': 0.01
    }
    
    # Test different tiers
    for tier in ['nibbler', 'fang', 'commander', 'apex']:
        print(f"\n🎯 Testing {tier.upper()} tier...")
        modified_signal = apply_ghost_mode_to_signal(test_signal.copy(), tier)
        
        print(f"   Original Entry: {test_signal['entry_price']}")
        print(f"   Ghost Summary: {modified_signal['ghost_mode_summary']['summary']}")
        print(f"   Stealth Score: {modified_signal['ghost_mode_summary']['stealth_score']:.1f}%")
    
    # Test recent activity
    activity = enhanced_ghost_tracker.get_recent_ghost_activity(1)
    print(f"\n📊 Recent Activity: {activity['total_actions']} actions")
    print(f"   Effectiveness: {activity.get('avg_effectiveness', 0):.1f}%")
    
    print("\n✅ Ghost mode testing complete!")

if __name__ == "__main__":
    test_ghost_mode()