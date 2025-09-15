#!/usr/bin/env python3
"""
BITTEN Dynamic Outcome Tracker - ATR-Based Resolution Tracking
Replaces fixed 60min checks with dynamic horizons based on ATR.
Tracks until TP/SL hit OR 3x expected time (max 4 hours).
Prevents misclassifying slow-burn winners as failures.
"""

import json
import time
import sqlite3
import zmq
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import threading
import math

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DynamicOutcomeTracker:
    """
    ATR-based dynamic outcome tracking system.
    Adapts tracking duration based on market volatility and expected time to target.
    """
    
    def __init__(self, 
                 db_path: str = "/root/HydraX-v2/bitten.db",
                 tracking_log: str = "/root/HydraX-v2/dynamic_tracking.jsonl"):
        self.db_path = db_path
        self.tracking_log = tracking_log
        
        # Dynamic tracking parameters
        self.base_timeout_minutes = 60  # Base timeout for normal volatility
        self.atr_multiplier = 3.0  # Track for 3x expected time
        self.max_tracking_hours = 24  # Track up to 24 hours for full completion
        self.min_tracking_minutes = 15  # Minimum tracking duration
        self.enable_timeout = False  # Disable timeout - track to actual TP/SL
        
        # ATR calculation settings
        self.atr_period = 14  # ATR calculation period
        self.atr_cache = {}  # Cache ATR values
        self.atr_cache_ttl = 300  # 5 minutes cache TTL
        
        # Price monitoring
        self.active_signals = {}  # Currently tracked signals
        self.price_subscriber = None
        self.context = zmq.Context()
        self.running = False
        self.monitor_thread = None
        
        logger.info("DynamicOutcomeTracker initialized with ATR-based timing")
    
    def start_tracking(self, market_data_port: int = 5560):
        """Start dynamic outcome tracking"""
        try:
            # Subscribe to market data for price updates
            self.price_subscriber = self.context.socket(zmq.SUB)
            self.price_subscriber.connect(f"tcp://localhost:{market_data_port}")
            self.price_subscriber.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all
            self.price_subscriber.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
            
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_outcomes, daemon=True)
            self.monitor_thread.start()
            
            # Load pending signals from database
            self._load_pending_signals()
            
            logger.info(f"Started dynamic outcome tracking on port {market_data_port}")
            
        except Exception as e:
            logger.error(f"Error starting outcome tracking: {e}")
    
    def stop_tracking(self):
        """Stop outcome tracking"""
        self.running = False
        if self.price_subscriber:
            self.price_subscriber.close()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped dynamic outcome tracking")
    
    def _load_pending_signals(self):
        """Load pending signals from database for tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get signals without outcomes from last 24 hours
                # (older signals likely already resolved but not tracked)
                cutoff_time = int(time.time()) - (24 * 3600)
                cursor = conn.execute("""
                    SELECT signal_id, symbol, direction, entry_price, stop_pips, 
                           target_pips, created_at, confidence, pattern_type
                    FROM signals 
                    WHERE created_at > ? 
                        AND (outcome IS NULL OR outcome = 'PENDING')
                        AND entry_price IS NOT NULL
                    ORDER BY created_at DESC
                    LIMIT 500
                """, (cutoff_time,))
                
                pending_signals = [dict(row) for row in cursor.fetchall()]
            
            for signal in pending_signals:
                self._add_signal_for_tracking(signal)
            
            logger.info(f"Loaded {len(pending_signals)} pending signals for tracking")
            
        except Exception as e:
            logger.error(f"Error loading pending signals: {e}")
    
    def _add_signal_for_tracking(self, signal: Dict):
        """Add signal for dynamic outcome tracking"""
        try:
            signal_id = signal['signal_id']
            symbol = signal['symbol']
            
            # Calculate dynamic timeout based on ATR
            atr_value = self._get_symbol_atr(symbol)
            dynamic_timeout = self._calculate_dynamic_timeout(signal, atr_value)
            
            # Calculate TP and SL levels
            entry_price = signal['entry_price']
            direction = signal['direction']
            stop_pips = signal['stop_pips']
            target_pips = signal['target_pips']
            
            pip_size = self._get_pip_size(symbol)
            
            if direction == 'BUY':
                tp_level = entry_price + (target_pips * pip_size)
                sl_level = entry_price - (stop_pips * pip_size)
            else:  # SELL
                tp_level = entry_price - (target_pips * pip_size)
                sl_level = entry_price + (stop_pips * pip_size)
            
            tracking_info = {
                'signal_id': signal_id,
                'symbol': symbol,
                'direction': direction,
                'entry_price': entry_price,
                'tp_level': tp_level,
                'sl_level': sl_level,
                'stop_pips': stop_pips,
                'target_pips': target_pips,
                'created_at': signal['created_at'],
                'tracking_start': int(time.time()),
                'timeout_at': int(time.time()) + dynamic_timeout,
                'atr_value': atr_value,
                'dynamic_timeout_minutes': dynamic_timeout / 60,
                'max_favorable_excursion': 0.0,
                'max_adverse_excursion': 0.0,
                'last_price': entry_price,
                'pattern_type': signal.get('pattern_type'),
                'confidence': signal.get('confidence')
            }
            
            self.active_signals[signal_id] = tracking_info
            
            # Log tracking start
            self._log_tracking_event("tracking_started", tracking_info)
            
        except Exception as e:
            logger.error(f"Error adding signal for tracking: {e}")
    
    def _calculate_dynamic_timeout(self, signal: Dict, atr_value: float) -> int:
        """Calculate dynamic timeout based on ATR and signal characteristics"""
        try:
            target_pips = signal['target_pips']
            
            if atr_value <= 0:
                # Fallback to base timeout if no ATR data
                return self.base_timeout_minutes * 60
            
            # Expected time based on target size vs daily volatility
            # If target is 20 pips and daily ATR is 80 pips, expect 25% of daily movement
            volatility_ratio = target_pips / atr_value
            
            # Base calculation: smaller targets relative to volatility take longer
            if volatility_ratio < 0.1:  # Very small target vs volatility
                time_factor = 2.0
            elif volatility_ratio < 0.25:  # Small target
                time_factor = 1.5
            elif volatility_ratio < 0.5:  # Medium target
                time_factor = 1.0
            else:  # Large target relative to volatility
                time_factor = 0.5
            
            # Apply ATR multiplier
            base_minutes = self.base_timeout_minutes * time_factor
            dynamic_minutes = base_minutes * self.atr_multiplier
            
            # Apply limits
            dynamic_minutes = max(self.min_tracking_minutes, dynamic_minutes)
            dynamic_minutes = min(self.max_tracking_hours * 60, dynamic_minutes)
            
            return int(dynamic_minutes * 60)  # Convert to seconds
            
        except Exception as e:
            logger.error(f"Error calculating dynamic timeout: {e}")
            return self.base_timeout_minutes * 60
    
    def _get_symbol_atr(self, symbol: str) -> float:
        """Get ATR value for symbol with caching"""
        current_time = int(time.time())
        cache_key = f"{symbol}_atr"
        
        # Check cache
        if cache_key in self.atr_cache:
            cached_data = self.atr_cache[cache_key]
            if current_time - cached_data['timestamp'] < self.atr_cache_ttl:
                return cached_data['value']
        
        # Calculate ATR from recent price data
        atr_value = self._calculate_atr(symbol)
        
        # Cache result
        self.atr_cache[cache_key] = {
            'value': atr_value,
            'timestamp': current_time
        }
        
        return atr_value
    
    def _calculate_atr(self, symbol: str) -> float:
        """Calculate ATR from recent market data"""
        try:
            # This would typically get recent OHLC data from market data
            # For now, use a simplified approach with recent price ranges
            
            # Get recent tick data for this symbol (last hour)
            cutoff_time = int(time.time()) - 3600
            
            # Simulated ATR calculation - in production this would use real OHLC data
            # Different symbols have different typical ATR values
            atr_estimates = {
                'EURUSD': 0.0015,  # ~15 pips daily ATR
                'GBPUSD': 0.0020,  # ~20 pips daily ATR
                'USDJPY': 0.15,    # ~15 pips daily ATR (JPY pairs)
                'EURJPY': 0.25,    # ~25 pips daily ATR
                'GBPJPY': 0.30,    # ~30 pips daily ATR
                'AUDUSD': 0.0018,  # ~18 pips daily ATR
                'USDCAD': 0.0016,  # ~16 pips daily ATR
                'NZDUSD': 0.0020,  # ~20 pips daily ATR
                'XAUUSD': 8.0,     # ~800 point daily ATR for Gold
                'BTCUSD': 1500.0,  # ~1500 point daily ATR for Bitcoin
            }
            
            # Get base ATR or default
            base_atr = atr_estimates.get(symbol, 0.0020)  # Default to 20 pips equivalent
            
            # Convert to pips for easier calculation
            pip_size = self._get_pip_size(symbol)
            atr_pips = base_atr / pip_size
            
            return atr_pips
            
        except Exception as e:
            logger.error(f"Error calculating ATR for {symbol}: {e}")
            return 20.0  # Default 20 pips ATR
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        if 'JPY' in symbol:
            if symbol in ['BTCJPY', 'ETHJPY']:
                return 1.0  # Crypto vs JPY
            return 0.01  # XXX/JPY pairs
        elif symbol in ['XAUUSD', 'XAGUSD']:
            return 0.1  # Precious metals
        elif symbol in ['BTCUSD', 'ETHUSD']:
            return 1.0  # Major crypto
        else:
            return 0.0001  # Major forex pairs
    
    def _monitor_outcomes(self):
        """Monitor signals for TP/SL hits and timeouts"""
        while self.running:
            try:
                current_time = int(time.time())
                
                # Process market data for price updates
                try:
                    message = self.price_subscriber.recv_string(zmq.DONTWAIT)
                    self._process_price_update(message)
                except zmq.Again:
                    pass  # No message available
                
                # Check for timeouts (only if enabled)
                if self.enable_timeout:
                    self._check_timeouts(current_time)
                
                # Clean up old completed signals (older than 1 hour)
                self._cleanup_old_signals(current_time)
                
                time.sleep(0.1)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                logger.error(f"Error in outcome monitoring: {e}")
                time.sleep(1)
    
    def _process_price_update(self, message: str):
        """Process incoming price update"""
        try:
            # Parse JSON market data message
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                return
            
            # Check if this is a TICK message
            if data.get('type') != 'TICK':
                return
            
            symbol = data.get('symbol')
            bid = data.get('bid')
            ask = data.get('ask')
            
            if not symbol or bid is None or ask is None:
                return
            
            bid = float(bid)
            ask = float(ask)
            
            # Check active signals for this symbol
            signals_to_remove = []
            
            for signal_id, tracking_info in self.active_signals.items():
                if tracking_info['symbol'] == symbol:
                    result = self._check_signal_outcome(tracking_info, bid, ask)
                    if result:
                        signals_to_remove.append(signal_id)
            
            # Remove completed signals
            for signal_id in signals_to_remove:
                del self.active_signals[signal_id]
                
        except Exception as e:
            logger.error(f"Error processing price update: {e}")
    
    def _check_signal_outcome(self, tracking_info: Dict, bid: float, ask: float) -> bool:
        """Check if signal has hit TP or SL - ALWAYS CHECK SL FIRST"""
        try:
            signal_id = tracking_info['signal_id']
            direction = tracking_info['direction']
            tp_level = tracking_info['tp_level']
            sl_level = tracking_info['sl_level']
            entry_price = tracking_info['entry_price']
            
            # Use appropriate price for direction
            current_price = bid if direction == 'SELL' else ask
            
            # Get previous price to check if we crossed levels
            previous_price = tracking_info.get('last_price', entry_price)
            tracking_info['last_price'] = current_price
            
            # Calculate excursions
            if direction == 'BUY':
                favorable_excursion = (current_price - entry_price) / self._get_pip_size(tracking_info['symbol'])
                adverse_excursion = (entry_price - current_price) / self._get_pip_size(tracking_info['symbol'])
            else:  # SELL
                favorable_excursion = (entry_price - current_price) / self._get_pip_size(tracking_info['symbol'])
                adverse_excursion = (current_price - entry_price) / self._get_pip_size(tracking_info['symbol'])
            
            # Update max excursions
            tracking_info['max_favorable_excursion'] = max(
                tracking_info['max_favorable_excursion'], 
                max(0, favorable_excursion)
            )
            tracking_info['max_adverse_excursion'] = max(
                tracking_info['max_adverse_excursion'], 
                max(0, adverse_excursion)
            )
            
            # Add slippage tolerance (3 pips for entry, affects TP/SL levels)
            pip_size = self._get_pip_size(tracking_info['symbol'])
            slippage_tolerance = 3 * pip_size  # 3 pip tolerance
            
            # Adjust levels for realistic slippage
            if direction == 'BUY':
                # Assume worst case: bought higher, so TP is harder to hit, SL easier
                realistic_tp = tp_level + slippage_tolerance
                realistic_sl = sl_level + slippage_tolerance
            else:  # SELL
                # Assume worst case: sold lower, so TP is harder to hit, SL easier
                realistic_tp = tp_level - slippage_tolerance
                realistic_sl = sl_level - slippage_tolerance
            
            # CRITICAL: Check if price moved THROUGH SL (gap scenario)
            # This catches cases where price jumped past SL directly
            if direction == 'BUY':
                # Check if we crossed SL going down
                if previous_price > realistic_sl and current_price <= realistic_sl:
                    self._record_outcome(tracking_info, 'LOSS', -tracking_info['stop_pips'], realistic_sl)
                    return True
                # Or if current price is below SL
                elif current_price <= realistic_sl:
                    self._record_outcome(tracking_info, 'LOSS', -tracking_info['stop_pips'], current_price)
                    return True
            else:  # SELL
                # Check if we crossed SL going up
                if previous_price < realistic_sl and current_price >= realistic_sl:
                    self._record_outcome(tracking_info, 'LOSS', -tracking_info['stop_pips'], realistic_sl)
                    return True
                # Or if current price is above SL
                elif current_price >= realistic_sl:
                    self._record_outcome(tracking_info, 'LOSS', -tracking_info['stop_pips'], current_price)
                    return True
            
            # ONLY check TP if SL hasn't been hit
            # Check if price moved THROUGH TP
            if direction == 'BUY':
                if previous_price < realistic_tp and current_price >= realistic_tp:
                    self._record_outcome(tracking_info, 'WIN', tracking_info['target_pips'], realistic_tp)
                    return True
                elif current_price >= realistic_tp:
                    self._record_outcome(tracking_info, 'WIN', tracking_info['target_pips'], current_price)
                    return True
            else:  # SELL
                if previous_price > realistic_tp and current_price <= realistic_tp:
                    self._record_outcome(tracking_info, 'WIN', tracking_info['target_pips'], realistic_tp)
                    return True
                elif current_price <= realistic_tp:
                    self._record_outcome(tracking_info, 'WIN', tracking_info['target_pips'], current_price)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking signal outcome: {e}")
            return False
    
    def _check_timeouts(self, current_time: int):
        """Check for timed out signals"""
        signals_to_remove = []
        
        for signal_id, tracking_info in self.active_signals.items():
            if current_time >= tracking_info['timeout_at']:
                # Signal timed out - record as timeout
                current_price = tracking_info['last_price']
                entry_price = tracking_info['entry_price']
                
                # Calculate final pips result
                pip_size = self._get_pip_size(tracking_info['symbol'])
                if tracking_info['direction'] == 'BUY':
                    pips_result = (current_price - entry_price) / pip_size
                else:
                    pips_result = (entry_price - current_price) / pip_size
                
                self._record_outcome(tracking_info, 'TIMEOUT', pips_result, current_price)
                signals_to_remove.append(signal_id)
        
        # Remove timed out signals
        for signal_id in signals_to_remove:
            del self.active_signals[signal_id]
    
    def _cleanup_old_signals(self, current_time: int):
        """Clean up old completed signals"""
        # This method would clean up any stale tracking data
        # For now, just log active signal count periodically
        if current_time % 300 == 0:  # Every 5 minutes
            logger.info(f"Currently tracking {len(self.active_signals)} active signals")
    
    def _record_outcome(self, tracking_info: Dict, outcome: str, pips_result: float, exit_price: float):
        """Record signal outcome in database"""
        try:
            signal_id = tracking_info['signal_id']
            tracking_duration = int(time.time()) - tracking_info['tracking_start']
            
            # EVENT BUS INTEGRATION - Track signal outcomes
            try:
                from event_bus.event_bridge import signal_outcome_recorded
                signal_outcome_recorded({
                    'signal_id': signal_id,
                    'outcome': outcome,  # WIN or LOSS
                    'pips_result': pips_result,
                    'exit_price': exit_price,
                    'tracking_duration': tracking_duration,
                    'pattern': tracking_info.get('pattern_type'),
                    'confidence': tracking_info.get('confidence'),
                    'symbol': tracking_info.get('symbol'),
                    'direction': tracking_info.get('direction'),
                    'max_favorable': tracking_info.get('max_favorable_excursion'),
                    'max_adverse': tracking_info.get('max_adverse_excursion'),
                    'timestamp': int(time.time())
                })
                logger.info(f"✅ Event Bus: Outcome {outcome} published for {signal_id}")
            except Exception as e:
                logger.warning(f"⚠️ Event Bus: Failed to publish outcome (non-critical): {e}")
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE signals 
                    SET outcome = ?, 
                        pips_result = ?,
                        exit_price = ?,
                        resolution_time = ?,
                        tracking_duration = ?,
                        max_favorable_excursion = ?,
                        max_adverse_excursion = ?,
                        dynamic_timeout_used = ?
                    WHERE signal_id = ?
                """, (
                    outcome, pips_result, exit_price, int(time.time()),
                    tracking_duration, tracking_info['max_favorable_excursion'],
                    tracking_info['max_adverse_excursion'], 
                    tracking_info['dynamic_timeout_minutes'], signal_id
                ))
                conn.commit()
            
            # Log outcome
            self._log_tracking_event("outcome_recorded", tracking_info, {
                'outcome': outcome,
                'pips_result': pips_result,
                'exit_price': exit_price,
                'tracking_duration_minutes': tracking_duration / 60
            })
            
            logger.info(f"Signal {signal_id} resolved: {outcome} ({pips_result:.1f} pips) "
                       f"after {tracking_duration/60:.1f} minutes")
            
        except Exception as e:
            logger.error(f"Error recording outcome for {signal_id}: {e}")
    
    def _log_tracking_event(self, event_type: str, tracking_info: Dict, extra_data: Dict = None):
        """Log tracking event to JSONL file"""
        try:
            log_entry = {
                "type": event_type,
                "signal_id": tracking_info['signal_id'],
                "symbol": tracking_info['symbol'],
                "direction": tracking_info['direction'],
                "pattern_type": tracking_info.get('pattern_type'),
                "confidence": tracking_info.get('confidence'),
                "atr_value": tracking_info.get('atr_value'),
                "dynamic_timeout_minutes": tracking_info.get('dynamic_timeout_minutes'),
                "max_favorable_excursion": tracking_info.get('max_favorable_excursion', 0),
                "max_adverse_excursion": tracking_info.get('max_adverse_excursion', 0),
                "timestamp": int(time.time()),
                "datetime": datetime.now().isoformat()
            }
            
            if extra_data:
                log_entry.update(extra_data)
            
            # Write to BOTH files so bitten_report can read it
            with open(self.tracking_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            # Also write outcomes to comprehensive_tracking for bitten_report
            if event_type == "outcome_recorded" and 'outcome' in extra_data:
                comprehensive_entry = {
                    "signal_id": tracking_info['signal_id'],
                    "symbol": tracking_info['symbol'],
                    "direction": tracking_info['direction'],
                    "pattern_type": tracking_info.get('pattern_type'),
                    "confidence": tracking_info.get('confidence'),
                    "outcome": extra_data['outcome'],
                    "pips_result": extra_data.get('pips_result', 0),
                    "timestamp": int(time.time()),
                    "datetime": datetime.now().isoformat()
                }
                with open('/root/HydraX-v2/comprehensive_tracking.jsonl', 'a') as f:
                    f.write(json.dumps(comprehensive_entry) + '\n')
                logger.info(f"Wrote outcome to comprehensive_tracking: {tracking_info['signal_id']} = {extra_data['outcome']}")
                
        except Exception as e:
            logger.error(f"Error logging tracking event: {e}")
    
    def get_tracking_statistics(self, days_back: int = 7) -> Dict:
        """Get statistics on dynamic tracking performance"""
        try:
            cutoff_time = int(time.time()) - (days_back * 24 * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get signals with tracking data
                cursor = conn.execute("""
                    SELECT signal_id, symbol, pattern_type, outcome, pips_result,
                           tracking_duration, dynamic_timeout_used, 
                           max_favorable_excursion, max_adverse_excursion,
                           confidence, created_at
                    FROM signals 
                    WHERE created_at > ? 
                        AND tracking_duration IS NOT NULL
                        AND outcome IN ('WIN', 'LOSS', 'TIMEOUT')
                    ORDER BY created_at DESC
                """, (cutoff_time,))
                
                tracked_signals = [dict(row) for row in cursor.fetchall()]
            
            if not tracked_signals:
                return {"error": "No tracked signals found"}
            
            # Calculate statistics
            total_signals = len(tracked_signals)
            wins = sum(1 for s in tracked_signals if s['outcome'] == 'WIN')
            losses = sum(1 for s in tracked_signals if s['outcome'] == 'LOSS')
            timeouts = sum(1 for s in tracked_signals if s['outcome'] == 'TIMEOUT')
            
            # Timing statistics
            if total_signals > 0:
                avg_tracking_duration = sum(s.get('tracking_duration', 0) or 0 for s in tracked_signals) / total_signals / 60
                avg_timeout_used = sum(s.get('dynamic_timeout_used', 0) or 0 for s in tracked_signals) / total_signals
            else:
                avg_tracking_duration = 0
                avg_timeout_used = 0
            
            # Performance by timeout bucket
            timeout_buckets = {'<30min': [], '30-60min': [], '60-120min': [], '>120min': []}
            for signal in tracked_signals:
                timeout_min = signal.get('dynamic_timeout_used', 60)
                if timeout_min < 30:
                    timeout_buckets['<30min'].append(signal)
                elif timeout_min < 60:
                    timeout_buckets['30-60min'].append(signal)
                elif timeout_min < 120:
                    timeout_buckets['60-120min'].append(signal)
                else:
                    timeout_buckets['>120min'].append(signal)
            
            bucket_stats = {}
            for bucket, signals in timeout_buckets.items():
                if signals:
                    bucket_wins = sum(1 for s in signals if s['outcome'] == 'WIN')
                    bucket_stats[bucket] = {
                        'count': len(signals),
                        'win_rate': bucket_wins / len(signals),
                        'avg_pips': sum(s.get('pips_result', 0) for s in signals) / len(signals)
                    }
            
            return {
                "analysis_period_days": days_back,
                "total_signals": total_signals,
                "outcomes": {
                    "wins": wins,
                    "losses": losses,
                    "timeouts": timeouts
                },
                "win_rate": wins / total_signals if total_signals > 0 else 0,
                "avg_tracking_duration_minutes": round(avg_tracking_duration, 1),
                "avg_dynamic_timeout_minutes": round(avg_timeout_used, 1),
                "timeout_bucket_performance": bucket_stats,
                "currently_tracking": len(self.active_signals),
                "calculated_at": int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Error calculating tracking statistics: {e}")
            return {"error": str(e)}
    
    def add_signal_for_tracking(self, signal_data: Dict):
        """Add new signal for tracking (external interface)"""
        self._add_signal_for_tracking(signal_data)
    
    def export_tracking_report(self) -> str:
        """Export comprehensive tracking report"""
        try:
            stats = self.get_tracking_statistics()
            
            report = {
                "generated_at": datetime.now().isoformat(),
                "generator": "DynamicOutcomeTracker",
                "tracking_settings": {
                    "base_timeout_minutes": self.base_timeout_minutes,
                    "atr_multiplier": self.atr_multiplier,
                    "max_tracking_hours": self.max_tracking_hours,
                    "min_tracking_minutes": self.min_tracking_minutes
                },
                "statistics": stats,
                "active_signals": {
                    "count": len(self.active_signals),
                    "signals": {
                        signal_id: {
                            "symbol": info['symbol'],
                            "direction": info['direction'],
                            "minutes_tracked": (int(time.time()) - info['tracking_start']) / 60,
                            "timeout_in_minutes": (info['timeout_at'] - int(time.time())) / 60,
                            "max_favorable_excursion": info['max_favorable_excursion'],
                            "max_adverse_excursion": info['max_adverse_excursion']
                        }
                        for signal_id, info in self.active_signals.items()
                    }
                }
            }
            
            output_file = f"/root/HydraX-v2/dynamic_tracking_report_{int(time.time())}.json"
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Dynamic tracking report exported to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting tracking report: {e}")
            return ""

def main():
    """Run dynamic outcome tracking"""
    tracker = DynamicOutcomeTracker()
    
    # Start tracking
    tracker.start_tracking()
    
    try:
        # Generate report
        report_file = tracker.export_tracking_report()
        print(f"Dynamic tracking report saved to: {report_file}")
        
        # Show current status
        stats = tracker.get_tracking_statistics()
        print(f"\nTracking Statistics (last 7 days):")
        print(f"  Total signals: {stats.get('total_signals', 0)}")
        print(f"  Win rate: {stats.get('win_rate', 0):.1%}")
        print(f"  Avg tracking duration: {stats.get('avg_tracking_duration_minutes', 0):.1f} minutes")
        print(f"  Currently tracking: {stats.get('currently_tracking', 0)} signals")
        
        # Monitor continuously
        print(f"\nMonitoring active signals... (Press Ctrl+C to stop)")
        while True:
            time.sleep(60)  # Check every minute
            # Reload pending signals periodically
            tracker._load_pending_signals()
            print(f"Currently tracking {len(tracker.active_signals)} signals...")
        
    except KeyboardInterrupt:
        print("\nStopping dynamic tracking...")
    finally:
        tracker.stop_tracking()

if __name__ == "__main__":
    main()