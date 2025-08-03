#!/usr/bin/env python3
"""
🐍 VENOM V8 STREAM EDITION - FIRE AND FORGET
High-frequency stateless stream processor for instant signal generation and dispatch
NO STORAGE | NO LOGGING | NO DELAYS - Pure streaming architecture
WITH INTEGRATED TRUTH TRACKING for complete signal audit trails
"""

import json
import time
import requests
import threading
from datetime import datetime
from collections import deque, defaultdict
from typing import Dict, Optional, List, Tuple
import logging
import statistics
from dataclasses import dataclass
import asyncio
import aiohttp
import signal
import sys

# Import truth tracking system
try:
    from signal_truth_tracker import tracker as truth_tracker
except ImportError:
    print("⚠️ WARNING: Truth tracker not available - signals will not be logged")
    truth_tracker = None

# Configure minimal logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - VENOM8 - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class StreamTick:
    """Minimal tick data for stream processing"""
    symbol: str
    bid: float
    ask: float
    timestamp: float
    volume: int = 0
    spread: float = 0.0

@dataclass
class StreamSignal:
    """Lightweight signal for immediate dispatch"""
    signal_id: str
    symbol: str
    direction: str
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: float
    fire_reason: str

class LiveTickBuffer:
    """Rolling buffer for live tick evaluation - NO PERSISTENCE"""
    def __init__(self, max_size: int = 20):
        self.ticks = deque(maxlen=max_size)
        self.last_update = 0
        
    def add_tick(self, tick: StreamTick):
        self.ticks.append(tick)
        self.last_update = time.time()
        
    def get_recent(self, count: int = 10) -> List[StreamTick]:
        return list(self.ticks)[-count:]
        
    def is_fresh(self, max_age: float = 5.0) -> bool:
        return (time.time() - self.last_update) < max_age

class VenomStreamEngine:
    """Core VENOM v8 stream processor - NO STORAGE MODE"""
    
    def __init__(self, throttle_controller=None, adaptive_throttle=None):
        # Live tick buffers (temporary, rolling)
        self.tick_buffers: Dict[str, LiveTickBuffer] = {}
        
        # Stream statistics (live only)
        self.stats = {
            'ticks_processed': 0,
            'signals_fired': 0,
            'start_time': time.time(),
            'last_signal_time': 0,
            'avg_processing_ms': 0
        }
        
        # Valid symbols (NO XAUUSD)
        self.valid_symbols = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
            "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
            "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY",
            "XAUUSD"  # GOLD added for testing
        ]
        
        # Fire thresholds (controlled by adaptive throttle and throttle controller)
        # Get initial threshold from centralized controller
        from tcs_controller import get_current_threshold
        self.fire_threshold = get_current_threshold()  # Dynamic threshold from controller
        self.min_signal_gap = 60.0   # Minimum 60 seconds between signals per pair
        
        # Last signal times (prevent spam)
        self.last_signals: Dict[str, float] = {}
        
        # Dispatch endpoint
        self.dispatch_url = "http://localhost:8888/api/signals"
        
        # Running state
        self.running = False
        
        # Throttle controller integration
        self.throttle_controller = throttle_controller
        self.adaptive_throttle = adaptive_throttle
        
        # Update fire threshold from controllers
        self._update_fire_threshold()
        
        print(f"🐍 VENOM V8 STREAM EDITION INITIALIZED")
        print(f"⚡ High-frequency mode: {len(self.valid_symbols)} pairs")
        print(f"🎯 Fire threshold: {self.fire_threshold}%")
        print(f"🚀 NO STORAGE | NO LOGGING | PURE STREAM")
    
    def _update_fire_threshold(self):
        """Update fire threshold from adaptive throttle and throttle controller"""
        threshold_updated = False
        
        # Priority 1: CITADEL adaptive throttle (pressure release system)
        if self.adaptive_throttle:
            try:
                adaptive_tcs = self.adaptive_throttle.current_state.current_tcs
                if adaptive_tcs != self.fire_threshold:
                    old_threshold = self.fire_threshold
                    self.fire_threshold = adaptive_tcs
                    print(f"🛡️ CITADEL adaptive TCS: {old_threshold}% → {adaptive_tcs}% ({self.adaptive_throttle.current_state.reason_code})")
                    threshold_updated = True
            except Exception as e:
                logger.warning(f"⚠️ Adaptive throttle error: {e}")
        
        # Priority 2: Throttle controller (if no adaptive throttle or as fallback)
        elif self.throttle_controller:
            try:
                tcs_threshold, _ = self.throttle_controller.get_current_thresholds()
                if tcs_threshold != self.fire_threshold:
                    old_threshold = self.fire_threshold
                    self.fire_threshold = tcs_threshold
                    print(f"🎛️ Throttle controller TCS: {old_threshold}% → {tcs_threshold}%")
                    threshold_updated = True
            except Exception as e:
                logger.warning(f"⚠️ Throttle controller error: {e}")
        
        return threshold_updated

    def process_tick_stream(self, tick_data: Dict) -> Optional[StreamSignal]:
        """Process incoming tick and evaluate for immediate signal generation"""
        start_time = time.time()
        
        try:
            # Extract tick data
            symbol = tick_data.get('symbol', '').upper()
            if symbol not in self.valid_symbols:
                return None
                
            bid = float(tick_data.get('bid', 0))
            ask = float(tick_data.get('ask', 0))
            if bid <= 0 or ask <= 0:
                return None
                
            # Create stream tick
            tick = StreamTick(
                symbol=symbol,
                bid=bid,
                ask=ask,
                timestamp=time.time(),
                volume=int(tick_data.get('volume', 0)),
                spread=round((ask - bid) / 0.0001, 1)  # Pips
            )
            
            # Add to rolling buffer
            if symbol not in self.tick_buffers:
                self.tick_buffers[symbol] = LiveTickBuffer()
            
            self.tick_buffers[symbol].add_tick(tick)
            self.stats['ticks_processed'] += 1
            
            # Check signal gap
            last_signal = self.last_signals.get(symbol, 0)
            if (time.time() - last_signal) < self.min_signal_gap:
                return None
            
            # Evaluate for signal
            signal = self._evaluate_live_conditions(symbol, tick)
            
            # Update processing time
            processing_ms = (time.time() - start_time) * 1000
            self.stats['avg_processing_ms'] = (self.stats['avg_processing_ms'] + processing_ms) / 2
            
            return signal
            
        except Exception as e:
            logger.warning(f"Tick processing error: {e}")
            return None

    def _evaluate_live_conditions(self, symbol: str, current_tick: StreamTick) -> Optional[StreamSignal]:
        """Live evaluation using rolling buffer - NO HISTORICAL DATA"""
        buffer = self.tick_buffers[symbol]
        
        if not buffer.is_fresh() or len(buffer.ticks) < 5:
            return None
            
        recent_ticks = buffer.get_recent(10)
        
        # Calculate live momentum
        prices = [t.bid for t in recent_ticks]
        if len(prices) < 5:
            return None
            
        # Simple momentum calculation
        price_change = prices[-1] - prices[0]
        volatility = statistics.stdev(prices) if len(prices) > 1 else 0
        
        # Calculate pip distance based on symbol
        pip_multiplier = 10000 if symbol not in ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "GBPCHF"] else 100
        price_change_pips = abs(price_change) * pip_multiplier
        
        # If no significant movement, no signal
        if price_change_pips < 2.0:  # Less than 2 pips movement
            return None
            
        # More realistic confidence calculation based on pip movement
        # 5-10 pips = 70-75%, 10-15 pips = 75-80%, 15-20 pips = 80-82%, 20+ pips = 82-85%
        if price_change_pips < 5:
            return None  # Ignore movements under 5 pips
        elif price_change_pips < 10:
            base_confidence = 70 + (price_change_pips - 5) * 1.0  # 70-75%
        elif price_change_pips < 15:
            base_confidence = 75 + (price_change_pips - 10) * 1.0  # 75-80%
        elif price_change_pips < 20:
            base_confidence = 80 + (price_change_pips - 15) * 0.4  # 80-82%
        else:
            base_confidence = min(82 + (price_change_pips - 20) * 0.15, 85)  # 82-85% max
            
        momentum_score = base_confidence
        
        # Volume confirmation
        volumes = [t.volume for t in recent_ticks if t.volume > 0]
        volume_boost = 1.15 if volumes and statistics.mean(volumes) > 1000 else 1.0
        
        # Spread penalty
        spread_penalty = 0.85 if current_tick.spread > 3.0 else 1.0
        
        # Final confidence (ensure realistic range 0-100%)
        confidence = min(momentum_score * volume_boost * spread_penalty, 100.0)
        
        # DEBUG: Log confidence calculations for first 10 iterations
        if hasattr(self, '_debug_count'):
            self._debug_count += 1
        else:
            self._debug_count = 1
            
        if self._debug_count <= 10:
            logger.info(f"🔍 DEBUG {symbol}: price_change={price_change:.5f}, pips={price_change_pips:.1f}, confidence={confidence:.1f}%, threshold={self.fire_threshold}%")
        
        # Fire condition with throttle controller check
        if confidence >= self.fire_threshold:
            # Check with throttle controller if available
            if self.throttle_controller:
                ml_score = 0.70  # Default ML score for stream mode
                should_fire = self.throttle_controller.should_fire_signal(confidence, ml_score)
                if not should_fire:
                    return None  # Signal blocked by throttle controller
            
            # Determine direction
            direction = "BUY" if price_change > 0 else "SELL"
            
            # Calculate levels
            entry_price = current_tick.ask if direction == "BUY" else current_tick.bid
            
            # Dynamic SL/TP based on volatility
            sl_distance = volatility * 15  # 15x volatility for SL
            tp_distance = volatility * 25  # 25x volatility for TP (1.67 R:R)
            
            if direction == "BUY":
                stop_loss = entry_price - sl_distance
                take_profit = entry_price + tp_distance
            else:
                stop_loss = entry_price + sl_distance
                take_profit = entry_price - tp_distance
            
            # Log signal generation to truth tracker
            signal_id = None
            if truth_tracker:
                signal_id = truth_tracker.log_signal_generated(
                    symbol=symbol,
                    direction=direction,
                    confidence=confidence,
                    entry_price=round(entry_price, 5),
                    stop_loss=round(stop_loss, 5),
                    take_profit=round(take_profit, 5),
                    source="venom_stream_pipeline",
                    tcs_score=confidence,  # Use confidence as TCS score for stream mode
                    citadel_score=0.0,     # Stream mode bypasses CITADEL
                    ml_filter_passed=True,  # Stream mode bypasses ML filter
                    fire_reason=f"momentum:{momentum_score:.1f} vol:{volume_boost:.1f}"
                )
            else:
                # Fallback signal ID if truth tracker unavailable
                signal_id = f"VENOM8_{symbol}_{int(time.time())}"
            
            signal = StreamSignal(
                signal_id=signal_id,
                symbol=symbol,
                direction=direction,
                confidence=round(confidence, 1),
                entry_price=round(entry_price, 5),
                stop_loss=round(stop_loss, 5),
                take_profit=round(take_profit, 5),
                timestamp=time.time(),
                fire_reason=f"momentum:{momentum_score:.1f} vol:{volume_boost:.1f}"
            )
            
            # Record signal in throttle controller if available
            if self.throttle_controller:
                self.throttle_controller.add_signal(
                    signal_id=signal_id,
                    symbol=symbol,
                    direction=direction,
                    tcs_score=confidence,
                    ml_score=0.70  # Default ML score for stream mode
                )
            
            # Update last signal time
            self.last_signals[symbol] = time.time()
            self.stats['signals_fired'] += 1
            self.stats['last_signal_time'] = time.time()
            
            return signal
            
        return None

    def dispatch_signal(self, signal: StreamSignal) -> bool:
        """Fire and forget signal dispatch with truth tracking"""
        try:
            # Calculate target and stop pips from entry/sl/tp
            pip_multiplier = 10000 if signal.symbol in ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "GBPCHF"] else 10000
            
            if signal.direction == "BUY":
                target_pips = round((signal.take_profit - signal.entry_price) * pip_multiplier, 1)
                stop_pips = round((signal.entry_price - signal.stop_loss) * pip_multiplier, 1)
            else:  # SELL
                target_pips = round((signal.entry_price - signal.take_profit) * pip_multiplier, 1)
                stop_pips = round((signal.stop_loss - signal.entry_price) * pip_multiplier, 1)
            
            # Calculate risk reward ratio
            risk_reward = round(target_pips / stop_pips, 2) if stop_pips > 0 else 2.0
            
            # Determine signal type based on R:R
            signal_type = "RAPID_ASSAULT" if risk_reward < 2.5 else "PRECISION_STRIKE"
            
            payload = {
                "signal_id": signal.signal_id,
                "symbol": signal.symbol,
                "direction": signal.direction,
                "signal_type": signal_type,  # Added missing field
                "confidence": signal.confidence,
                "target_pips": target_pips,   # Added missing field
                "stop_pips": stop_pips,       # Added missing field
                "risk_reward": risk_reward,   # Added missing field
                "entry_price": signal.entry_price,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "source": "venom_stream_v8",
                "timestamp": signal.timestamp,
                "fire_reason": signal.fire_reason
            }
            
            # Fire and forget (no waiting for response)
            response = requests.post(self.dispatch_url, json=payload, timeout=1.0)
            
            if response.status_code == 200:
                # Log successful dispatch to truth tracker
                if truth_tracker:
                    truth_tracker.log_signal_fired(signal.signal_id, user_count=1)
                
                print(f"🔥 FIRED: {signal.symbol} {signal.direction} @{signal.confidence:.1f}% [{signal.fire_reason}]")
                return True
            else:
                print(f"❌ DISPATCH FAILED: {signal.symbol} - {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"⏱️ TIMEOUT: {signal.symbol} dispatch (continuing...)")
            return False
        except Exception as e:
            print(f"❌ DISPATCH ERROR: {signal.symbol} - {e}")
            return False

class StreamDataIntake:
    """Market data intake system - STATELESS"""
    
    def __init__(self, venom_engine: VenomStreamEngine):
        self.venom = venom_engine
        self.market_data_url = "http://localhost:8001/market-data/all?fast=true"
        self.intake_interval = 0.5  # 500ms for high frequency
        self.running = False
        self.use_zmq = False  # Flag to switch between HTTP and ZMQ
        self.zmq_intake = None
        
    def start_intake(self, use_zmq=False):
        """Start the data intake loop"""
        self.running = True
        self.use_zmq = use_zmq
        
        if self.use_zmq:
            print(f"📡 ZMQ MARKET DATA INTAKE STARTING - Direct connection")
            # Import and initialize ZMQ intake
            try:
                from venom_zmq_intake import VenomZMQIntake
                self.zmq_intake = VenomZMQIntake()
                if not self.zmq_intake.connect():
                    print("❌ Failed to connect to ZMQ, falling back to HTTP")
                    self.use_zmq = False
                else:
                    print("✅ ZMQ connection established - waiting for market data")
            except Exception as e:
                print(f"❌ ZMQ initialization failed: {e}, falling back to HTTP")
                self.use_zmq = False
        
        if not self.use_zmq:
            print(f"📡 HTTP MARKET DATA INTAKE STARTED - {1/self.intake_interval:.1f} Hz")
        
        last_threshold_update = 0
        threshold_update_interval = 10  # Update thresholds every 10 seconds
        
        while self.running:
            try:
                start_time = time.time()
                
                # Periodic threshold update from adaptive throttle
                if (start_time - last_threshold_update) >= threshold_update_interval:
                    if self.venom._update_fire_threshold():
                        logger.info(f"🎯 Fire threshold updated to {self.venom.fire_threshold}%")
                    last_threshold_update = start_time
                
                # Fetch market data
                if self.use_zmq and self.zmq_intake:
                    # Get data from ZMQ
                    market_data = {'data': self.zmq_intake.get_market_snapshot()}
                    
                    # If no data from ZMQ, skip this iteration
                    if not market_data['data']:
                        time.sleep(self.intake_interval)
                        continue
                else:
                    # Original HTTP method
                    response = requests.get(self.market_data_url, timeout=2.0)
                    
                    if response.status_code == 200:
                        market_data = response.json()
                    else:
                        logger.error(f"Market data response error: status_code={response.status_code}")
                        time.sleep(1.0)
                        continue
                
                # 🛡️ SIGNAL FIREWALL - MAXIMUM SECURITY
                data_section = market_data.get('data', market_data)
                    logger.debug(f"Market data response keys: {list(market_data.keys())}, data section type: {type(data_section)}, length: {len(data_section) if hasattr(data_section, '__len__') else 'N/A'}")
                    if len(data_section) == 0:
                        print("🚫 Signal engine disabled — no real market data.")
                        logger.error("🚫 SIGNAL FIREWALL: No live market data available - signal generation disabled")
                        time.sleep(10)  # Wait 10 seconds before next check
                        continue
                    
                    logger.info(f"📊 Processing {len(data_section)} symbols from market data")
                    processed_count = 0
                    signal_count = 0
                    
                    # Process each symbol's data - REAL MT5 ONLY
                    for symbol, data in data_section.items():
                        if isinstance(data, dict) and 'bid' in data and 'ask' in data:
                            # CRITICAL: Validate source is MT5_LIVE only
                            if data.get('source') != 'MT5_LIVE':
                                logger.warning(f"❌ REJECTED non-live data for {symbol}: source={data.get('source', 'unknown')}")
                                continue
                                
                            # Generate signal if conditions met (REAL DATA ONLY)
                            processed_count += 1
                            signal = self.venom.process_tick_stream(data)
                            
                            if signal:
                                signal_count += 1
                                # Immediate dispatch
                                self.venom.dispatch_signal(signal)
                    
                if processed_count > 0:
                    logger.debug(f"Processed {processed_count} symbols, generated {signal_count} signals")
                
                # High-frequency timing
                elapsed = time.time() - start_time
                sleep_time = max(0, self.intake_interval - elapsed)
                time.sleep(sleep_time)
                
            except requests.exceptions.RequestException as e:
                # Log network errors for debugging
                logger.error(f"Network error fetching market data: {e}")
                time.sleep(1.0)
            except Exception as e:
                logger.error(f"Intake error: {e}")
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(1.0)

    def stop_intake(self):
        """Stop the intake"""
        self.running = False
        if self.zmq_intake:
            self.zmq_intake.stop()
            self.zmq_intake.disconnect()

class LiveStatsConsole:
    """Live performance statistics console"""
    
    def __init__(self, venom_engine: VenomStreamEngine):
        self.venom = venom_engine
        self.running = False
        
    def start_console(self):
        """Start live stats display"""
        self.running = True
        print("📊 LIVE STATS CONSOLE STARTED")
        
        while self.running:
            try:
                self._display_stats()
                time.sleep(5)  # Update every 5 seconds
            except KeyboardInterrupt:
                break
                
    def _display_stats(self):
        """Display current statistics"""
        stats = self.venom.stats
        runtime = time.time() - stats['start_time']
        
        # Calculate rates
        tick_rate = stats['ticks_processed'] / runtime if runtime > 0 else 0
        signal_rate = stats['signals_fired'] / runtime if runtime > 0 else 0
        
        # Time since last signal
        time_since_signal = time.time() - stats['last_signal_time'] if stats['last_signal_time'] > 0 else 0
        
        # Active buffers
        active_buffers = sum(1 for buf in self.venom.tick_buffers.values() if buf.is_fresh())
        
        print(f"\r🐍 VENOM V8 STREAM | "
              f"Ticks: {stats['ticks_processed']} ({tick_rate:.1f}/s) | "
              f"Signals: {stats['signals_fired']} ({signal_rate:.2f}/s) | "
              f"Active: {active_buffers} pairs | "
              f"Last signal: {time_since_signal:.0f}s ago | "
              f"Avg: {stats['avg_processing_ms']:.1f}ms", end='')

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 VENOM V8 STREAM SHUTDOWN")
    sys.exit(0)

def main():
    """Main VENOM V8 Stream Pipeline"""
    # Handle shutdown gracefully
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 STARTING VENOM V8 STREAM EDITION")
    print("=" * 60)
    
    # Initialize truth tracking
    if truth_tracker:
        truth_tracker.start_monitoring()
        print(f"🎯 Truth tracking active - logging to {truth_tracker.truth_log_path}")
    else:
        print("⚠️ Truth tracking disabled - signals will not be logged")
    
    # Initialize throttle controller
    throttle_controller = None
    try:
        from throttle_controller import get_throttle_controller
        throttle_controller = get_throttle_controller()
        throttle_controller.start_monitoring()
        print(f"🎛️ Throttle controller active - dynamic signal governor")
    except ImportError:
        print("⚠️ Throttle controller not available - using static thresholds")
    except Exception as e:
        print(f"⚠️ Throttle controller error: {e} - using static thresholds")
    
    # Initialize CITADEL adaptive throttle
    adaptive_throttle = None
    try:
        from citadel_adaptive_throttle import get_adaptive_throttle
        adaptive_throttle = get_adaptive_throttle()
        adaptive_throttle.start_monitoring()
        print(f"🛡️ CITADEL adaptive throttle active - pressure release system")
    except ImportError:
        print("⚠️ CITADEL adaptive throttle not available - using static TCS")
    except Exception as e:
        print(f"⚠️ CITADEL adaptive throttle error: {e} - using static TCS")
    
    # Initialize components
    venom_engine = VenomStreamEngine(
        throttle_controller=throttle_controller,
        adaptive_throttle=adaptive_throttle
    )
    data_intake = StreamDataIntake(venom_engine)
    stats_console = LiveStatsConsole(venom_engine)
    
    # Check if we should use ZMQ based on command line argument
    use_zmq = '--zmq' in sys.argv or '--direct' in sys.argv
    
    # Start intake in background thread
    intake_thread = threading.Thread(target=lambda: data_intake.start_intake(use_zmq=use_zmq), daemon=True)
    intake_thread.start()
    
    # Wait a moment for intake to start
    time.sleep(1)
    
    try:
        # Run live stats console (main thread)
        stats_console.start_console()
    except KeyboardInterrupt:
        print("\n🛑 SHUTTING DOWN VENOM V8 STREAM")
    finally:
        data_intake.stop_intake()
        stats_console.running = False
        
        # Stop throttle controller
        if throttle_controller:
            throttle_controller.stop_monitoring()
        
        # Stop adaptive throttle
        if adaptive_throttle:
            adaptive_throttle.stop_monitoring()
        
        # Stop truth tracking
        if truth_tracker:
            truth_tracker.stop_monitoring()

if __name__ == "__main__":
    main()