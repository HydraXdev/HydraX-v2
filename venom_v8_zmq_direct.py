#!/usr/bin/env python3
"""
🐍 VENOM V8 ZMQ DIRECT - Pure ZMQ Market Data Connection
Bypasses HTTP layer entirely for direct EA → VENOM flow
"""

import zmq
import json
import time
import logging
import requests
from datetime import datetime
from collections import deque
from typing import Dict, Optional
from dataclasses import dataclass
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - VENOM8-ZMQ - %(message)s')
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
    """Rolling buffer for live tick evaluation"""
    def __init__(self, max_size: int = 20):
        self.ticks = deque(maxlen=max_size)
        self.last_update = 0
        
    def add_tick(self, tick: StreamTick):
        self.ticks.append(tick)
        self.last_update = time.time()
        
    def get_recent(self, count: int = 10):
        return list(self.ticks)[-count:]
        
    def is_fresh(self, max_age: float = 5.0):
        return (time.time() - self.last_update) < max_age

class VenomZMQEngine:
    """Direct ZMQ VENOM Engine"""
    
    def __init__(self):
        # ZMQ setup
        self.context = zmq.Context()
        self.socket = None
        
        # Live tick buffers
        self.tick_buffers: Dict[str, LiveTickBuffer] = {}
        
        # Stats
        self.stats = {
            'ticks_processed': 0,
            'signals_fired': 0,
            'start_time': time.time()
        }
        
        # Valid symbols
        self.valid_symbols = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
            "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
            "GBPNZD", "GBPAUD", "EURAUD", "GBPCHF", "AUDJPY",
            "XAUUSD"
        ]
        
        # Thresholds
        from tcs_controller import get_current_threshold
        self.fire_threshold = get_current_threshold()
        self.min_signal_gap = 60.0
        self.last_signals: Dict[str, float] = {}
        
        # Dispatch endpoint
        self.dispatch_url = "http://localhost:8888/api/signals"
        
        print(f"🐍 VENOM V8 ZMQ DIRECT INITIALIZED")
        print(f"🎯 Fire threshold: {self.fire_threshold}%")
        print(f"📡 Waiting for ZMQ market data on port 5557")
    
    def connect_zmq(self):
        """Connect to ZMQ telemetry stream (port 5556)"""
        try:
            # Connect to existing telemetry stream instead of creating new port
            self.socket = self.context.socket(zmq.SUB)
            self.socket.connect("tcp://localhost:5556")
            self.socket.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all messages
            self.socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
            print("✅ ZMQ socket connected to telemetry port 5556")
            print("💡 Listening to existing EA → Telemetry stream")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ZMQ: {e}")
            return False
    
    def process_tick(self, tick_data: Dict) -> Optional[StreamSignal]:
        """Process incoming tick and evaluate for signal"""
        try:
            symbol = tick_data.get('symbol', '').upper()
            if symbol not in self.valid_symbols:
                return None
                
            bid = float(tick_data.get('bid', 0))
            ask = float(tick_data.get('ask', 0))
            if bid <= 0 or ask <= 0:
                return None
                
            # Create tick
            tick = StreamTick(
                symbol=symbol,
                bid=bid,
                ask=ask,
                timestamp=time.time(),
                volume=int(tick_data.get('volume', 0)),
                spread=round((ask - bid) / 0.0001, 1)
            )
            
            # Add to buffer
            if symbol not in self.tick_buffers:
                self.tick_buffers[symbol] = LiveTickBuffer()
            
            self.tick_buffers[symbol].add_tick(tick)
            self.stats['ticks_processed'] += 1
            
            # Check signal gap
            last_signal = self.last_signals.get(symbol, 0)
            if (time.time() - last_signal) < self.min_signal_gap:
                return None
            
            # Evaluate for signal
            return self._evaluate_signal(symbol, tick)
            
        except Exception as e:
            logger.warning(f"Tick processing error: {e}")
            return None
    
    def _evaluate_signal(self, symbol: str, current_tick: StreamTick) -> Optional[StreamSignal]:
        """Evaluate if conditions warrant a signal"""
        buffer = self.tick_buffers[symbol]
        
        if not buffer.is_fresh() or len(buffer.ticks) < 5:
            return None
            
        recent_ticks = buffer.get_recent(10)
        prices = [t.bid for t in recent_ticks]
        
        if len(prices) < 5:
            return None
            
        # Calculate momentum
        price_change = prices[-1] - prices[0]
        volatility = statistics.stdev(prices) if len(prices) > 1 else 0
        
        pip_multiplier = 10000 if symbol not in ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "GBPCHF"] else 100
        price_change_pips = abs(price_change) * pip_multiplier
        
        if price_change_pips < 5:
            return None
            
        # Calculate confidence
        if price_change_pips < 10:
            base_confidence = 70 + (price_change_pips - 5) * 1.0
        elif price_change_pips < 15:
            base_confidence = 75 + (price_change_pips - 10) * 1.0
        elif price_change_pips < 20:
            base_confidence = 80 + (price_change_pips - 15) * 0.4
        else:
            base_confidence = min(82 + (price_change_pips - 20) * 0.15, 85)
            
        confidence = base_confidence
        
        # Fire check
        if confidence >= self.fire_threshold:
            direction = "BUY" if price_change > 0 else "SELL"
            entry_price = current_tick.ask if direction == "BUY" else current_tick.bid
            
            sl_distance = volatility * 15
            tp_distance = volatility * 25
            
            if direction == "BUY":
                stop_loss = entry_price - sl_distance
                take_profit = entry_price + tp_distance
            else:
                stop_loss = entry_price + sl_distance
                take_profit = entry_price - tp_distance
            
            signal_id = f"VENOM8_ZMQ_{symbol}_{int(time.time())}"
            
            signal = StreamSignal(
                signal_id=signal_id,
                symbol=symbol,
                direction=direction,
                confidence=round(confidence, 1),
                entry_price=round(entry_price, 5),
                stop_loss=round(stop_loss, 5),
                take_profit=round(take_profit, 5),
                timestamp=time.time(),
                fire_reason=f"momentum:{price_change_pips:.1f}pips"
            )
            
            self.last_signals[symbol] = time.time()
            self.stats['signals_fired'] += 1
            
            return signal
            
        return None
    
    def dispatch_signal(self, signal: StreamSignal) -> bool:
        """Send signal to webapp"""
        try:
            pip_multiplier = 10000 if signal.symbol not in ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "GBPCHF"] else 10000
            
            if signal.direction == "BUY":
                target_pips = round((signal.take_profit - signal.entry_price) * pip_multiplier, 1)
                stop_pips = round((signal.entry_price - signal.stop_loss) * pip_multiplier, 1)
            else:
                target_pips = round((signal.entry_price - signal.take_profit) * pip_multiplier, 1)
                stop_pips = round((signal.stop_loss - signal.entry_price) * pip_multiplier, 1)
            
            risk_reward = round(target_pips / stop_pips, 2) if stop_pips > 0 else 2.0
            signal_type = "RAPID_ASSAULT" if risk_reward < 2.5 else "PRECISION_STRIKE"
            
            payload = {
                "signal_id": signal.signal_id,
                "symbol": signal.symbol,
                "direction": signal.direction,
                "signal_type": signal_type,
                "confidence": signal.confidence,
                "target_pips": target_pips,
                "stop_pips": stop_pips,
                "risk_reward": risk_reward,
                "entry_price": signal.entry_price,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "source": "venom_zmq_direct",
                "timestamp": signal.timestamp,
                "fire_reason": signal.fire_reason
            }
            
            response = requests.post(self.dispatch_url, json=payload, timeout=1.0)
            
            if response.status_code == 200:
                print(f"🔥 FIRED: {signal.symbol} {signal.direction} @{signal.confidence:.1f}% [{signal.fire_reason}]")
                return True
            else:
                print(f"❌ DISPATCH FAILED: {signal.symbol} - {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ DISPATCH ERROR: {signal.symbol} - {e}")
            return False
    
    def run(self):
        """Main ZMQ receive loop"""
        if not self.connect_zmq():
            return
            
        print("🚀 VENOM V8 ZMQ DIRECT RUNNING")
        print("=" * 60)
        
        messages_received = 0
        last_stats = time.time()
        
        while True:
            try:
                # Try to receive ZMQ message
                message = self.socket.recv_string()
                messages_received += 1
                
                # Parse JSON
                data = json.loads(message)
                
                # Process ticks
                if 'ticks' in data:
                    for tick_data in data.get('ticks', []):
                        signal = self.process_tick(tick_data)
                        if signal:
                            self.dispatch_signal(signal)
                elif 'symbol' in data:
                    # Single tick format
                    signal = self.process_tick(data)
                    if signal:
                        self.dispatch_signal(signal)
                
                # Stats every 10 seconds
                if time.time() - last_stats > 10:
                    runtime = time.time() - self.stats['start_time']
                    tick_rate = self.stats['ticks_processed'] / runtime if runtime > 0 else 0
                    signal_rate = self.stats['signals_fired'] / runtime if runtime > 0 else 0
                    
                    print(f"\r📊 ZMQ Direct | Messages: {messages_received} | "
                          f"Ticks: {self.stats['ticks_processed']} ({tick_rate:.1f}/s) | "
                          f"Signals: {self.stats['signals_fired']} ({signal_rate:.3f}/s) | "
                          f"Active: {len([b for b in self.tick_buffers.values() if b.is_fresh()])} pairs", 
                          end='')
                    
                    last_stats = time.time()
                    messages_received = 0
                    
            except zmq.Again:
                # Timeout - no message, this is normal
                pass
                
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON: {e}")
                
            except KeyboardInterrupt:
                print("\n🛑 VENOM V8 ZMQ SHUTDOWN")
                break
                
            except Exception as e:
                logger.error(f"ZMQ error: {e}")
                time.sleep(1)

if __name__ == "__main__":
    engine = VenomZMQEngine()
    engine.run()