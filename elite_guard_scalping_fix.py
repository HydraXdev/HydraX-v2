#!/usr/bin/env python3
"""
Elite Guard Scalping Fix - High Win Rate Signal Generator
Requirements:
- RAPID signals: TP within 1 hour (5-10 pips)
- SNIPER signals: TP within 2 hours (10-20 pips)
- High probability patterns only
"""

import json
import time
import numpy as np
from collections import deque
from typing import Optional, Dict, Any
import logging
import zmq

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScalpingSignalGenerator:
    """High win rate scalping signal generator"""
    
    def __init__(self):
        self.context = zmq.Context()
        
        # Subscribe to market data
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://127.0.0.1:5560")
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        
        # Publish signals
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind("tcp://127.0.0.1:5559")  # New port for scalping signals
        
        # Track recent price action
        self.price_buffer = {}  # symbol -> deque of prices
        self.momentum = {}      # symbol -> momentum score
        self.last_signal = {}   # symbol -> timestamp of last signal
        
        # Scalping parameters
        self.RAPID_TP_PIPS = 8     # 8 pips for 1-hour targets
        self.RAPID_SL_PIPS = 5     # 5 pips stop loss
        self.SNIPER_TP_PIPS = 15   # 15 pips for 2-hour targets
        self.SNIPER_SL_PIPS = 8    # 8 pips stop loss
        self.MIN_MOMENTUM = 2.5    # Minimum momentum score
        self.SIGNAL_COOLDOWN = 300 # 5 minutes between signals per symbol
        
    def calculate_momentum(self, prices: list) -> float:
        """Calculate momentum score (velocity + acceleration)"""
        if len(prices) < 5:
            return 0
            
        # Recent price changes
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Velocity (average change)
        velocity = np.mean(changes[-3:]) if changes else 0
        
        # Acceleration (change in velocity)
        if len(changes) >= 2:
            acceleration = changes[-1] - changes[-2]
        else:
            acceleration = 0
            
        # Momentum score (higher = stronger move)
        momentum = abs(velocity * 10000) + abs(acceleration * 5000)
        
        return momentum
    
    def detect_breakout_pattern(self, symbol: str, prices: list) -> Optional[Dict]:
        """Detect micro breakout patterns for scalping"""
        if len(prices) < 20:
            return None
            
        current_price = prices[-1]
        
        # Find recent range (last 20 ticks)
        recent_high = max(prices[-20:-2])  # Exclude last 2 for breakout
        recent_low = min(prices[-20:-2])
        range_size = (recent_high - recent_low) * 10000  # Convert to pips
        
        # Check for tight range (consolidation)
        if range_size > 10:  # Range too wide for scalping
            return None
            
        # Detect breakout
        breakout_up = current_price > recent_high and prices[-2] > recent_high
        breakout_down = current_price < recent_low and prices[-2] < recent_low
        
        if not (breakout_up or breakout_down):
            return None
            
        # Check momentum
        momentum = self.calculate_momentum(prices)
        if momentum < self.MIN_MOMENTUM:
            return None
            
        # Generate signal
        direction = "BUY" if breakout_up else "SELL"
        entry_price = current_price
        
        # Determine signal type based on momentum
        if momentum > 4.0:  # Strong momentum = SNIPER
            pattern_class = "SNIPER"
            tp_pips = self.SNIPER_TP_PIPS
            sl_pips = self.SNIPER_SL_PIPS
            confidence = min(85, 70 + momentum * 2)
            pattern_type = "MOMENTUM_BREAKOUT"
        else:  # Moderate momentum = RAPID
            pattern_class = "RAPID"
            tp_pips = self.RAPID_TP_PIPS
            sl_pips = self.RAPID_SL_PIPS
            confidence = min(75, 65 + momentum * 2)
            pattern_type = "RANGE_BREAKOUT"
            
        # Calculate actual TP/SL prices
        pip_value = 0.0001 if 'JPY' not in symbol else 0.01
        
        if direction == "BUY":
            sl = entry_price - (sl_pips * pip_value)
            tp = entry_price + (tp_pips * pip_value)
        else:
            sl = entry_price + (sl_pips * pip_value)
            tp = entry_price - (tp_pips * pip_value)
            
        return {
            'signal_id': f"SCALP_{symbol}_{int(time.time())}",
            'symbol': symbol,
            'direction': direction,
            'entry_price': round(entry_price, 5),
            'sl': round(sl, 5),
            'tp': round(tp, 5),
            'stop_pips': sl_pips,
            'target_pips': tp_pips,
            'confidence': round(confidence),
            'pattern_type': pattern_type,
            'pattern_class': pattern_class,
            'momentum_score': round(momentum, 2),
            'expected_minutes': 60 if pattern_class == "RAPID" else 120,
            'created_at': int(time.time())
        }
    
    def detect_momentum_surge(self, symbol: str, prices: list) -> Optional[Dict]:
        """Detect sudden momentum surges for quick scalps"""
        if len(prices) < 10:
            return None
            
        # Calculate recent momentum
        momentum = self.calculate_momentum(prices[-10:])
        
        # Need STRONG momentum for this pattern
        if momentum < 5.0:
            return None
            
        # Check if momentum is accelerating
        old_momentum = self.calculate_momentum(prices[-20:-10]) if len(prices) >= 20 else 0
        if momentum <= old_momentum * 1.5:  # Need 50% momentum increase
            return None
            
        current_price = prices[-1]
        
        # Determine direction from recent price action
        price_change = current_price - prices[-10]
        direction = "BUY" if price_change > 0 else "SELL"
        
        # Ultra-fast scalp parameters
        pattern_class = "RAPID"
        tp_pips = 5  # Quick 5 pip scalp
        sl_pips = 3  # Tight 3 pip stop
        confidence = min(80, 70 + momentum)
        
        # Calculate TP/SL
        pip_value = 0.0001 if 'JPY' not in symbol else 0.01
        
        if direction == "BUY":
            sl = current_price - (sl_pips * pip_value)
            tp = current_price + (tp_pips * pip_value)
        else:
            sl = current_price + (sl_pips * pip_value)
            tp = current_price - (tp_pips * pip_value)
            
        return {
            'signal_id': f"SURGE_{symbol}_{int(time.time())}",
            'symbol': symbol,
            'direction': direction,
            'entry_price': round(current_price, 5),
            'sl': round(sl, 5),
            'tp': round(tp, 5),
            'stop_pips': sl_pips,
            'target_pips': tp_pips,
            'confidence': round(confidence),
            'pattern_type': "MOMENTUM_SURGE",
            'pattern_class': pattern_class,
            'momentum_score': round(momentum, 2),
            'expected_minutes': 30,  # Should hit within 30 minutes
            'created_at': int(time.time())
        }
    
    def process_tick(self, symbol: str, bid: float, ask: float):
        """Process incoming tick data"""
        # Initialize buffer if needed
        if symbol not in self.price_buffer:
            self.price_buffer[symbol] = deque(maxlen=100)
            self.last_signal[symbol] = 0
            
        # Use mid price
        mid_price = (bid + ask) / 2
        self.price_buffer[symbol].append(mid_price)
        
        # Need enough data
        if len(self.price_buffer[symbol]) < 20:
            return
            
        # Check cooldown
        if time.time() - self.last_signal[symbol] < self.SIGNAL_COOLDOWN:
            return
            
        prices = list(self.price_buffer[symbol])
        
        # Try different pattern detectors
        signal = None
        
        # 1. Check for momentum surge (highest priority)
        signal = self.detect_momentum_surge(symbol, prices)
        
        # 2. Check for breakout pattern
        if not signal:
            signal = self.detect_breakout_pattern(symbol, prices)
            
        # Publish signal if found
        if signal:
            logger.info(f"🎯 SCALPING SIGNAL: {signal['symbol']} {signal['direction']} "
                       f"TP:{signal['target_pips']}p SL:{signal['stop_pips']}p "
                       f"Class:{signal['pattern_class']} Conf:{signal['confidence']}%")
            
            # Publish to ZMQ
            self.publisher.send_string(f"SCALP_SIGNAL {json.dumps(signal)}")
            
            # Mark signal time
            self.last_signal[symbol] = time.time()
    
    def run(self):
        """Main loop"""
        logger.info("🚀 Scalping Signal Generator Started")
        logger.info(f"📊 Settings: RAPID={self.RAPID_TP_PIPS}/{self.RAPID_SL_PIPS}p, "
                   f"SNIPER={self.SNIPER_TP_PIPS}/{self.SNIPER_SL_PIPS}p")
        
        while True:
            try:
                # Receive market data
                message = self.subscriber.recv_string(flags=zmq.NOBLOCK)
                
                # Parse tick data
                if "TICK" in message:
                    parts = message.split()
                    if len(parts) >= 4:
                        symbol = parts[1]
                        try:
                            bid = float(parts[2])
                            ask = float(parts[3])
                            self.process_tick(symbol, bid, ask)
                        except ValueError:
                            pass
                            
            except zmq.Again:
                time.sleep(0.01)  # No data, wait briefly
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(1)

if __name__ == "__main__":
    generator = ScalpingSignalGenerator()
    generator.run()