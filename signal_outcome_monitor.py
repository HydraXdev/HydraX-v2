#!/usr/bin/env python3
"""
Signal Outcome Monitor - Tracks whether signals hit SL or TP first
Monitors live tick data to determine actual signal outcomes
"""

import json
import zmq
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SignalOutcomeMonitor:
    def __init__(self):
        self.context = zmq.Context()
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://localhost:5560")  # Market data port
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        self.active_signals = {}  # signal_id -> signal data
        self.completed_signals = []
        self.truth_file = "/root/HydraX-v2/truth_log.jsonl"
        self.outcome_file = "/root/HydraX-v2/signal_outcomes.jsonl"
        self.freshness_file = "/root/HydraX-v2/signal_freshness.jsonl"
        
        # FRESHNESS TRACKING SYSTEM
        self.freshness_snapshots = {}  # signal_id -> {30s, 1m, 2m, 5m snapshots}
        self.freshness_intervals = [30, 60, 120, 300]  # seconds
        self.pattern_invalidation_rules = {
            'LIQUIDITY_SWEEP_REVERSAL': self.check_sweep_invalidation,
            'ORDER_BLOCK_BOUNCE': self.check_orderblock_invalidation, 
            'FAIR_VALUE_GAP_FILL': self.check_fvg_invalidation,
            'VCB_BREAKOUT': self.check_vcb_invalidation,
            'SWEEP_RETURN': self.check_srl_invalidation
        }
        
        print("📊 Signal Outcome Monitor started with FRESHNESS TRACKING")
        print("   Monitoring tick data to track SL/TP hits + signal decay")
        self.load_active_signals()
        
    def load_active_signals(self):
        """Load active signals from truth log"""
        try:
            with open(self.truth_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and line != '[]':
                        try:
                            signal = json.loads(line)
                            # Only track Elite Guard signals that aren't completed
                            if ('ELITE_GUARD' in signal.get('signal_id', '') and 
                                not signal.get('completed', False) and
                                signal.get('entry_price', 0) > 0):
                                
                                # Add to active signals
                                self.active_signals[signal['signal_id']] = {
                                    'signal': signal,
                                    'monitoring_started': datetime.now().isoformat(),
                                    'ticks_processed': 0,
                                    'max_favorable': 0,
                                    'max_adverse': 0,
                                    'current_price': signal['entry_price']
                                }
                        except:
                            continue
            
            print(f"   Loaded {len(self.active_signals)} active signals to monitor")
            for sid in self.active_signals:
                sig = self.active_signals[sid]['signal']
                print(f"   • {sig['symbol']} {sig['direction']} @ {sig['entry_price']}")
                
        except FileNotFoundError:
            print("   No truth log found, starting fresh")
    
    def track_signal_freshness(self, signal_id: str, current_price: float, timestamp: float):
        """Track signal freshness at key intervals"""
        if signal_id not in self.active_signals:
            return
            
        signal = self.active_signals[signal_id]['signal']
        entry_price = signal.get('entry_price', 0)
        if entry_price == 0:
            return
            
        # Get signal generation timestamp
        signal_timestamp = signal.get('timestamp', timestamp)
        if isinstance(signal_timestamp, str):
            # Parse ISO format if needed
            try:
                from datetime import datetime
                signal_timestamp = datetime.fromisoformat(signal_timestamp.replace('Z', '+00:00')).timestamp()
            except:
                signal_timestamp = timestamp
                
        age_seconds = timestamp - signal_timestamp
        
        # Initialize freshness tracking for new signals
        if signal_id not in self.freshness_snapshots:
            self.freshness_snapshots[signal_id] = {
                'signal_id': signal_id,
                'symbol': signal.get('symbol', ''),
                'pattern_type': signal.get('pattern_type', ''),
                'entry_price': entry_price,
                'direction': signal.get('direction', ''),
                'generated_at': signal_timestamp,
                'snapshots': {},
                'pattern_invalidated': False,
                'invalidation_time': None,
                'invalidation_reason': None,
                'max_decay_pips': 0,
                'last_updated': timestamp
            }
        
        freshness = self.freshness_snapshots[signal_id]
        
        # Take snapshots at key intervals
        for interval in self.freshness_intervals:
            if (age_seconds >= interval and 
                interval not in freshness['snapshots']):
                
                pip_movement = abs(current_price - entry_price) * self.get_pip_multiplier(signal['symbol'])
                direction_correct = self.is_price_moving_favorably(signal, current_price, entry_price)
                
                freshness['snapshots'][interval] = {
                    'price': current_price,
                    'age_seconds': age_seconds,
                    'pip_movement': pip_movement,
                    'favorable_direction': direction_correct,
                    'pattern_valid': not freshness['pattern_invalidated'],
                    'timestamp': timestamp
                }
                
                print(f"   📸 {signal['symbol']} snapshot at {interval}s: {pip_movement:.1f} pips, {'✅' if direction_correct else '❌'}")
        
        # Check pattern-specific invalidation
        pattern_type = signal.get('pattern_type', '')
        if (not freshness['pattern_invalidated'] and 
            pattern_type in self.pattern_invalidation_rules):
            
            invalidated, reason = self.pattern_invalidation_rules[pattern_type](signal, current_price, age_seconds)
            if invalidated:
                freshness['pattern_invalidated'] = True
                freshness['invalidation_time'] = age_seconds
                freshness['invalidation_reason'] = reason
                print(f"   ⚠️ {signal['symbol']} pattern INVALIDATED: {reason}")
                
        # Track maximum decay
        current_decay = abs(current_price - entry_price) * self.get_pip_multiplier(signal['symbol'])
        freshness['max_decay_pips'] = max(freshness['max_decay_pips'], current_decay)
        freshness['last_updated'] = timestamp
        
        # Save freshness data every 30 seconds
        if int(age_seconds) % 30 == 0:
            self.save_freshness_data(signal_id)
            
        # Broadcast freshness updates every 15 seconds for real-time UI
        if int(age_seconds) % 15 == 0:
            self.broadcast_freshness_update(signal_id)

    def is_price_moving_favorably(self, signal: dict, current_price: float, entry_price: float) -> bool:
        """Check if price is moving in signal's favor"""
        direction = signal.get('direction', '').upper()
        if direction == 'BUY':
            return current_price > entry_price
        else:
            return current_price < entry_price

    def get_pip_multiplier(self, symbol: str) -> float:
        """Get pip multiplier for a symbol"""
        s = symbol.upper().replace('/', '')
        if s.endswith("JPY"): return 100  # 0.01 pip size
        if s.startswith("XAU"): return 10  # 0.1 pip size
        if s.startswith("XAG"): return 100  # 0.01 pip size  
        return 10000  # 0.0001 pip size

    # Pattern-specific invalidation rules
    def check_sweep_invalidation(self, signal: dict, current_price: float, age_seconds: float) -> tuple:
        """Liquidity sweep patterns invalidate if price moves back past entry"""
        entry = signal.get('entry_price', 0)
        direction = signal.get('direction', '').upper()
        pip_threshold = 5  # 5 pip reversal invalidates
        pip_size = 0.0001 if not signal.get('symbol', '').endswith('JPY') else 0.01
        
        if direction == 'BUY' and current_price < (entry - pip_threshold * pip_size):
            return True, f"Price reversed {pip_threshold}+ pips below entry"
        elif direction == 'SELL' and current_price > (entry + pip_threshold * pip_size):
            return True, f"Price reversed {pip_threshold}+ pips above entry"
        elif age_seconds > 300:  # 5 minute max for sweeps
            return True, "Liquidity sweep timeout (5 minutes)"
        return False, None

    def check_vcb_invalidation(self, signal: dict, current_price: float, age_seconds: float) -> tuple:
        """VCB breakouts invalidate if no follow-through in 2 minutes"""
        entry = signal.get('entry_price', 0)
        direction = signal.get('direction', '').upper()
        min_movement = 3  # Need 3 pip movement to stay valid
        
        pip_movement = abs(current_price - entry) * self.get_pip_multiplier(signal.get('symbol', ''))
        
        if age_seconds > 120 and pip_movement < min_movement:
            return True, f"No follow-through after 2 minutes ({pip_movement:.1f} pips < {min_movement})"
        elif age_seconds > 600:  # 10 minute max for VCB
            return True, "VCB breakout timeout (10 minutes)"
        return False, None

    def check_orderblock_invalidation(self, signal: dict, current_price: float, age_seconds: float) -> tuple:
        """Order block bounces invalidate if price breaks through the block"""
        entry = signal.get('entry_price', 0)
        direction = signal.get('direction', '').upper()
        break_threshold = 8  # 8 pip break invalidates
        pip_size = 0.0001 if not signal.get('symbol', '').endswith('JPY') else 0.01
        
        if direction == 'BUY' and current_price < (entry - break_threshold * pip_size):
            return True, f"Price broke below order block by {break_threshold}+ pips"
        elif direction == 'SELL' and current_price > (entry + break_threshold * pip_size):
            return True, f"Price broke above order block by {break_threshold}+ pips"
        elif age_seconds > 900:  # 15 minute max for order blocks
            return True, "Order block timeout (15 minutes)"
        return False, None

    def check_fvg_invalidation(self, signal: dict, current_price: float, age_seconds: float) -> tuple:
        """Fair value gaps invalidate if filled in wrong direction"""
        entry = signal.get('entry_price', 0)
        direction = signal.get('direction', '').upper()
        
        # FVG patterns are more forgiving on timing but strict on price action
        if age_seconds > 720:  # 12 minute max for FVG
            return True, "Fair value gap timeout (12 minutes)"
        return False, None

    def check_srl_invalidation(self, signal: dict, current_price: float, age_seconds: float) -> tuple:
        """Sweep and return patterns invalidate if no quick reversal"""
        entry = signal.get('entry_price', 0)
        direction = signal.get('direction', '').upper()
        min_return = 4  # Need 4 pip return to stay valid
        
        pip_movement = abs(current_price - entry) * self.get_pip_multiplier(signal.get('symbol', ''))
        favorable = self.is_price_moving_favorably(signal, current_price, entry)
        
        if age_seconds > 180 and (not favorable or pip_movement < min_return):
            return True, f"No sufficient return after 3 minutes ({pip_movement:.1f} pips)"
        elif age_seconds > 600:  # 10 minute max for SRL
            return True, "Sweep-return timeout (10 minutes)"
        return False, None

    def save_freshness_data(self, signal_id: str):
        """Save freshness data to file"""
        if signal_id not in self.freshness_snapshots:
            return
            
        try:
            freshness_data = self.freshness_snapshots[signal_id]
            with open(self.freshness_file, 'a') as f:
                f.write(json.dumps(freshness_data) + '\n')
        except Exception as e:
            print(f"Error saving freshness data: {e}")

    def calculate_freshness_status(self, pattern_type: str, age_seconds: float, freshness_data: dict) -> dict:
        """Calculate pattern-specific freshness status"""
        
        # Pattern-specific decay rules
        decay_rules = {
            'LIQUIDITY_SWEEP_REVERSAL': {'fresh': 60, 'stale': 180, 'expired': 300},
            'ORDER_BLOCK_BOUNCE': {'fresh': 120, 'stale': 300, 'expired': 600},
            'FAIR_VALUE_GAP_FILL': {'fresh': 90, 'stale': 240, 'expired': 480},
            'VCB_BREAKOUT': {'fresh': 45, 'stale': 120, 'expired': 300},
            'SWEEP_RETURN': {'fresh': 75, 'stale': 200, 'expired': 400}
        }
        
        thresholds = decay_rules.get(pattern_type, {'fresh': 60, 'stale': 180, 'expired': 300})
        
        # Check if pattern was invalidated
        if freshness_data.get('pattern_invalidated', False):
            return {
                'score': 0,
                'status': 'expired',
                'warning': 'danger',
                'action': 'abort'
            }
        
        # Calculate score based on age
        if age_seconds <= thresholds['fresh']:
            score = 100 - (age_seconds / thresholds['fresh']) * 30  # 100-70
            return {'score': score, 'status': 'fresh', 'warning': 'none', 'action': 'fire'}
        elif age_seconds <= thresholds['stale']:
            score = 70 - ((age_seconds - thresholds['fresh']) / (thresholds['stale'] - thresholds['fresh'])) * 50  # 70-20
            return {'score': score, 'status': 'stale', 'warning': 'caution', 'action': 'caution'}
        else:
            return {'score': 0, 'status': 'expired', 'warning': 'danger', 'action': 'abort'}

    def broadcast_freshness_update(self, signal_id: str):
        """Broadcast freshness update to webapp via HTTP"""
        if signal_id not in self.freshness_snapshots:
            return
            
        try:
            freshness_data = self.freshness_snapshots[signal_id]
            age_seconds = time.time() - freshness_data.get('generated_at', time.time())
            pattern_type = freshness_data.get('pattern_type', '')
            
            # Calculate current freshness status
            freshness_status = self.calculate_freshness_status(pattern_type, age_seconds, freshness_data)
            
            # Prepare broadcast data
            broadcast_data = {
                'signal_id': signal_id,
                'age_seconds': age_seconds,
                'pattern_valid': not freshness_data.get('pattern_invalidated', False),
                'freshness_score': freshness_status['score'],
                'status': freshness_status['status'],
                'warning_level': freshness_status['warning'],
                'invalidation_reason': freshness_data.get('invalidation_reason'),
                'max_decay_pips': freshness_data.get('max_decay_pips', 0),
                'recommended_action': freshness_status['action']
            }
            
            # Send to webapp for SocketIO broadcast
            import requests
            requests.post('http://localhost:8888/api/internal/broadcast-freshness', 
                json=broadcast_data, timeout=2)
                
        except Exception as e:
            # Non-critical - don't break signal monitoring if webapp unavailable
            pass
    
    def pip_size(self, symbol: str) -> float:
        """Calculate pip size for a symbol"""
        s = symbol.upper()
        if s.endswith("JPY"): return 0.01
        if s.startswith("XAU"): return 0.1
        if s.startswith("XAG"): return 0.01
        return 0.0001
        
    def ensure_levels(self, signal: dict) -> tuple:
        """Ensure signal has absolute SL/TP levels"""
        sym = signal.get('symbol', '').upper()
        side = signal.get('direction', '').upper()
        entry = float(signal.get('entry_price', 0))
        sl_abs = float(signal.get('sl', 0))
        tp_abs = float(signal.get('tp', 0))
        stop_pips = float(signal.get('stop_pips', 0) or signal.get('sl_pips', 0))
        target_pips = float(signal.get('target_pips', 0) or signal.get('tp_pips', 0))
        
        # If we already have absolute levels, use them
        if sl_abs > 0 and tp_abs > 0:
            return sl_abs, tp_abs, entry
            
        # Calculate from pips if we have entry and pips
        if entry > 0 and (stop_pips > 0 or target_pips > 0) and side in ("BUY", "SELL"):
            pip = self.pip_size(sym)
            if side == "BUY":
                sl_abs = entry - (stop_pips * pip) if stop_pips > 0 else 0
                tp_abs = entry + (target_pips * pip) if target_pips > 0 else 0
            else:
                sl_abs = entry + (stop_pips * pip) if stop_pips > 0 else 0
                tp_abs = entry - (target_pips * pip) if target_pips > 0 else 0
                
        return sl_abs, tp_abs, entry
    
    def process_tick(self, symbol: str, bid: float, ask: float):
        """Process tick data and check if any signals hit SL/TP + track freshness"""
        
        # Check each active signal for this symbol
        completed_now = []
        current_timestamp = time.time()
        
        for signal_id, data in self.active_signals.items():
            signal = data['signal']
            
            # Skip if different symbol
            if signal['symbol'] != symbol:
                continue
                
            data['ticks_processed'] += 1
            
            # FRESHNESS TRACKING: Track signal decay in real-time
            current_price = bid if signal.get('direction', '').upper() == 'SELL' else ask
            self.track_signal_freshness(signal_id, current_price, current_timestamp)
            
            # Ensure we have SL/TP levels
            sl, tp, entry_price = self.ensure_levels(signal)
            
            # Skip if we couldn't determine levels
            if sl <= 0 or tp <= 0:
                continue
                
            # Store computed levels back in signal for future use
            if 'sl' not in signal or signal['sl'] <= 0:
                signal['sl'] = sl
                signal['tp'] = tp
            
            # Determine relevant price based on direction
            if signal['direction'] == 'BUY':
                # For BUY: Use bid for SL, ask for entry
                current_price = bid  # Exit price
                entry_price = signal['entry_price']
                sl = signal['sl']
                tp = signal['tp']
                
                # Track max favorable/adverse
                favorable = current_price - entry_price
                data['max_favorable'] = max(data['max_favorable'], favorable)
                data['max_adverse'] = min(data['max_adverse'], favorable)
                
                # Check SL hit (bid <= sl)
                if current_price <= sl:
                    completed_now.append({
                        'signal_id': signal_id,
                        'outcome': 'LOSS',
                        'hit_level': 'SL',
                        'exit_price': current_price,
                        'pips': (current_price - entry_price) * self.get_pip_multiplier(symbol)
                    })
                    print(f"   ❌ {symbol} hit SL @ {current_price:.5f}")
                    
                # Check TP hit (bid >= tp)
                elif current_price >= tp:
                    completed_now.append({
                        'signal_id': signal_id,
                        'outcome': 'WIN',
                        'hit_level': 'TP',
                        'exit_price': current_price,
                        'pips': (current_price - entry_price) * self.get_pip_multiplier(symbol)
                    })
                    print(f"   ✅ {symbol} hit TP @ {current_price:.5f}")
                    
            else:  # SELL
                # For SELL: Use ask for SL, bid for exit
                current_price = ask  # Exit price
                entry_price = signal['entry_price']
                sl = signal['sl']
                tp = signal['tp']
                
                # Track max favorable/adverse
                favorable = entry_price - current_price
                data['max_favorable'] = max(data['max_favorable'], favorable)
                data['max_adverse'] = min(data['max_adverse'], favorable)
                
                # Check SL hit (ask >= sl)
                if current_price >= sl:
                    completed_now.append({
                        'signal_id': signal_id,
                        'outcome': 'LOSS',
                        'hit_level': 'SL',
                        'exit_price': current_price,
                        'pips': (entry_price - current_price) * self.get_pip_multiplier(symbol)
                    })
                    print(f"   ❌ {symbol} hit SL @ {current_price:.5f}")
                    
                # Check TP hit (ask <= tp)
                elif current_price <= tp:
                    completed_now.append({
                        'signal_id': signal_id,
                        'outcome': 'WIN',
                        'hit_level': 'TP',
                        'exit_price': current_price,
                        'pips': (entry_price - current_price) * self.get_pip_multiplier(symbol)
                    })
                    print(f"   ✅ {symbol} hit TP @ {current_price:.5f}")
            
            data['current_price'] = current_price
        
        # Process completed signals
        for completion in completed_now:
            signal_id = completion['signal_id']
            data = self.active_signals[signal_id]
            
            # Create outcome record
            outcome_record = {
                'signal_id': signal_id,
                'symbol': data['signal']['symbol'],
                'direction': data['signal']['direction'],
                'pattern': data['signal'].get('pattern_type'),
                'signal_type': data['signal'].get('signal_type'),
                'confidence': data['signal'].get('confidence', 0),  # Track confidence
                'session': data['signal'].get('session', ''),  # Track session
                'risk_reward': data['signal'].get('risk_reward', 1.0),  # Track R:R
                'entry_price': data['signal']['entry_price'],
                'sl': data['signal']['sl'],
                'tp': data['signal']['tp'],
                'outcome': completion['outcome'],
                'hit_level': completion['hit_level'],
                'exit_price': completion['exit_price'],
                'pips_result': completion['pips'],
                'max_favorable': data['max_favorable'] * self.get_pip_multiplier(data['signal']['symbol']),
                'max_adverse': data['max_adverse'] * self.get_pip_multiplier(data['signal']['symbol']),
                'ticks_processed': data['ticks_processed'],
                'completed_at': datetime.now().isoformat(),
                'monitoring_started': data['monitoring_started']
            }
            
            # Save outcome
            self.save_outcome(outcome_record)
            self.completed_signals.append(outcome_record)
            
            # Send outcome to Elite Guard ML system for learning
            self.send_outcome_to_ml(outcome_record)
            
            # Remove from active
            del self.active_signals[signal_id]
    
    def get_pip_multiplier(self, symbol: str) -> float:
        """Get pip multiplier for symbol"""
        if symbol in ['USDJPY', 'EURJPY', 'GBPJPY']:
            return 100  # JPY pairs
        elif symbol == 'XAUUSD':
            return 10   # Gold
        else:
            return 10000  # Major pairs
    
    def save_outcome(self, outcome: Dict):
        """Save signal outcome to file"""
        try:
            with open(self.outcome_file, 'a') as f:
                f.write(json.dumps(outcome) + '\n')
        except Exception as e:
            print(f"Error saving outcome: {e}")
    
    def send_outcome_to_ml(self, outcome: Dict):
        """Send outcome to ML system for performance tracking"""
        try:
            # Calculate runtime duration
            start_time = datetime.fromisoformat(outcome['monitoring_started'])
            end_time = datetime.fromisoformat(outcome['completed_at'])
            runtime_minutes = (end_time - start_time).total_seconds() / 60
            
            # Log comprehensive tracking data
            tracking_data = {
                'signal_id': outcome['signal_id'],
                'outcome': outcome['outcome'],  # WIN or LOSS
                'pattern': outcome['pattern'],
                'confidence': outcome.get('confidence', 0),
                'symbol': outcome['symbol'],
                'session': outcome.get('session', ''),
                'runtime_minutes': round(runtime_minutes, 2),
                'pips_result': outcome['pips_result'],
                'max_favorable_pips': outcome['max_favorable'],
                'max_adverse_pips': outcome['max_adverse'],
                'risk_reward': outcome.get('risk_reward', 1.0),
                'completed_at': outcome['completed_at']
            }
            
            # Write to ML tracking file for analysis
            ml_tracking_file = '/root/HydraX-v2/ml_performance_tracking.jsonl'
            with open(ml_tracking_file, 'a') as f:
                f.write(json.dumps(tracking_data) + '\n')
            
            # Also update ML signal filter directly
            from ml_signal_filter import report_trade_outcome
            report_trade_outcome(
                signal_id=outcome['signal_id'],
                outcome='WIN' if outcome['outcome'] == 'WIN' else 'LOSS',
                pips=outcome['pips_result']
            )
            
            print(f"   📈 ML TRACKING: {outcome['symbol']} {outcome['pattern']} - "
                  f"{outcome['outcome']} after {runtime_minutes:.1f} mins")
            
        except Exception as e:
            print(f"   ⚠️ ML tracking error: {e}")
    
    def print_statistics(self):
        """Print current monitoring statistics"""
        print(f"\n📊 OUTCOME MONITOR STATISTICS:")
        print(f"   Active Signals: {len(self.active_signals)}")
        print(f"   Completed: {len(self.completed_signals)}")
        
        if self.completed_signals:
            wins = [s for s in self.completed_signals if s['outcome'] == 'WIN']
            losses = [s for s in self.completed_signals if s['outcome'] == 'LOSS']
            
            print(f"   Wins: {len(wins)}")
            print(f"   Losses: {len(losses)}")
            if wins or losses:
                win_rate = len(wins) / (len(wins) + len(losses)) * 100
                print(f"   Win Rate: {win_rate:.1f}%")
                
                total_pips = sum(s['pips_result'] for s in self.completed_signals)
                print(f"   Total Pips: {total_pips:+.1f}")
        
        print(f"\n   Currently Monitoring:")
        for sid, data in self.active_signals.items():
            sig = data['signal']
            print(f"   • {sig['symbol']} {sig['direction']} - {data['ticks_processed']} ticks")
    
    def run(self):
        """Main monitoring loop"""
        print("\n🔍 Monitoring tick data for signal outcomes...")
        last_stats = time.time()
        
        while True:
            try:
                # Check for new tick data (non-blocking with timeout)
                if self.subscriber.poll(100):  # 100ms timeout
                    message = self.subscriber.recv_string()
                    
                    # Parse tick data - handle "tick " prefix
                    try:
                        # Remove "tick " prefix if present
                        if message.startswith("tick "):
                            json_str = message[5:]  # Remove "tick " prefix
                        else:
                            json_str = message
                            
                        data = json.loads(json_str)
                        if data.get('type') == 'TICK':
                            symbol = data.get('symbol')
                            bid = data.get('bid')
                            ask = data.get('ask')
                            if symbol and bid and ask:
                                self.process_tick(symbol, float(bid), float(ask))
                    except (json.JSONDecodeError, ValueError, TypeError):
                        # Try old format as fallback
                        if message.startswith("TICK") or message.startswith("tick"):
                            parts = message.split()
                            if len(parts) >= 4:
                                try:
                                    symbol = parts[1]
                                    bid = float(parts[2])
                                    ask = float(parts[3])
                                    self.process_tick(symbol, bid, ask)
                                except ValueError:
                                    pass
                
                # Print statistics every 30 seconds
                if time.time() - last_stats > 30:
                    self.print_statistics()
                    last_stats = time.time()
                    
            except KeyboardInterrupt:
                print("\n👋 Signal Outcome Monitor stopped")
                break
            except Exception as e:
                print(f"Error in monitor: {e}")
                time.sleep(1)

if __name__ == "__main__":
    monitor = SignalOutcomeMonitor()
    monitor.run()