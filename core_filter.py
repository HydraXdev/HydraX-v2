#!/usr/bin/env python3
"""
BITTEN C.O.R.E. Signal Engine - Stage 1
Coin Operations Reconnaissance Engine

Processes BTCUSD crypto ticks and generates signals using SMC logic
"""

import zmq
import json
import time
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CORE_Filter')

class CoreCryptoEngine:
    """
    C.O.R.E. Crypto Signal Processing Engine
    """
    
    def __init__(self):
        # ZMQ Context
        self.context = zmq.Context()
        
        # Subscriber to MT5 tick stream
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://127.0.0.1:5555")
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b"CRYPTO|BTCUSD")
        
        # Publisher for outbound signals to Telegram bot
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind("tcp://127.0.0.1:5556")
        
        # Signal tracking
        self.last_signal_time = 0
        self.signal_cooldown = 300  # 5 minutes between signals
        
        logger.info("🚀 C.O.R.E. Crypto Engine initialized")
        logger.info("📡 Listening for CRYPTO|BTCUSD on tcp://127.0.0.1:5555")
        logger.info("📤 Publishing CORE_SIGNALS on tcp://127.0.0.1:5556")
    
    def process_crypto_tick(self, symbol: str, tick: dict) -> None:
        """
        Process incoming crypto tick and generate signal if criteria met
        """
        try:
            # Check cooldown
            current_time = time.time()
            if current_time - self.last_signal_time < self.signal_cooldown:
                return
            
            # Extract tick data
            bid = float(tick.get("bid", 0))
            ask = float(tick.get("ask", 0))
            volume = int(tick.get("volume", 0))
            spread = ask - bid
            
            logger.info(f"📊 Processing {symbol}: Bid={bid}, Ask={ask}, Volume={volume}")
            
            # Placeholder SMC pattern check (crypto-specific logic)
            score = self.calculate_smc_score(symbol, tick)
            
            # Generate signal if score meets threshold
            if score >= 65:
                signal = self.build_signal_packet(symbol, tick, score)
                self.send_core_signal(signal)
                self.last_signal_time = current_time
                
                logger.info(f"🎯 CORE_SIGNAL generated: {symbol} Score={score}")
            else:
                logger.debug(f"⏳ Signal below threshold: {symbol} Score={score}")
                
        except Exception as e:
            logger.error(f"❌ Error processing tick: {e}")
    
    def calculate_smc_score(self, symbol: str, tick: dict) -> int:
        """
        Calculate Smart Money Concepts score for crypto
        Placeholder implementation - will be enhanced with real SMC logic
        """
        # Placeholder scoring logic
        # TODO: Implement real SMC patterns:
        # - Liquidity sweeps
        # - Order block bounces  
        # - Fair value gaps
        # - Break of structure
        
        bid = float(tick.get("bid", 0))
        volume = int(tick.get("volume", 0))
        
        # Basic scoring criteria (placeholder)
        score = 60  # Base score
        
        # Volume bonus
        if volume > 1000:
            score += 10
        
        # Price level analysis (simplified)
        if bid > 50000:  # Above psychological level
            score += 8
            
        # Hardcoded score for testing
        score = 78  # Fixed for Stage 1 testing
        
        return score
    
    def build_signal_packet(self, symbol: str, tick: dict, score: int) -> dict:
        """
        Build standardized signal packet for C.O.R.E.
        """
        bid = float(tick.get("bid", 0))
        
        # Calculate targets (crypto-specific)
        stop_loss = round(bid - 1000, 2)    # $1000 SL
        take_profit = round(bid + 2000, 2)  # $2000 TP (2:1 R:R)
        
        # Generate unique mission ID
        mission_id = f"btc-mission-{int(time.time())}"
        
        signal = {
            "uuid": mission_id,
            "symbol": symbol,
            "entry": bid,
            "sl": stop_loss,
            "tp": take_profit,
            "pattern": "Sweep Reversal",  # Placeholder pattern
            "score": score,
            "xp": 160,  # XP reward for crypto signals
            "timestamp": datetime.now().isoformat(),
            "engine": "CORE",
            "type": "CRYPTO_ASSAULT",
            "risk_reward": 2.0
        }
        
        return signal
    
    def send_core_signal(self, signal: dict) -> None:
        """
        Send signal packet via ZMQ to Telegram routing system
        """
        try:
            # Format message for ZMQ routing
            message = f"CORE_SIGNAL {json.dumps(signal)}"
            self.publisher.send_string(message)
            
            logger.info(f"📤 CORE_SIGNAL sent: {signal['uuid']} ({signal['symbol']})")
            
        except Exception as e:
            logger.error(f"❌ Failed to send signal: {e}")
    
    def run(self) -> None:
        """
        Main processing loop
        """
        logger.info("🎯 C.O.R.E. Engine starting main loop...")
        
        while True:
            try:
                # Receive tick data with timeout
                if self.subscriber.poll(timeout=1000):  # 1 second timeout
                    raw_message = self.subscriber.recv_string(zmq.NOBLOCK)
                    
                    # Parse message: "CRYPTO|BTCUSD|{json_data}"
                    parts = raw_message.split('|', 2)
                    if len(parts) >= 3:
                        topic, symbol, json_data = parts
                        
                        # Parse tick data
                        tick = json.loads(json_data)
                        
                        # Process the tick
                        self.process_crypto_tick(symbol, tick)
                    else:
                        logger.warning(f"⚠️ Invalid message format: {raw_message}")
                
                # Sleep for processing interval
                time.sleep(30)  # Process every 30 seconds
                
            except zmq.Again:
                # No message received, continue
                continue
            except KeyboardInterrupt:
                logger.info("🛑 Shutdown requested")
                break
            except Exception as e:
                logger.error(f"❌ Main loop error: {e}")
                time.sleep(5)  # Brief pause before retry
        
        # Cleanup
        self.cleanup()
    
    def cleanup(self) -> None:
        """
        Clean shutdown of ZMQ connections
        """
        logger.info("🧹 Cleaning up ZMQ connections...")
        self.subscriber.close()
        self.publisher.close()
        self.context.term()

def main():
    """
    Entry point for C.O.R.E. crypto signal engine
    """
    print("🚀 Starting BITTEN C.O.R.E. Crypto Signal Engine")
    print("=" * 60)
    
    try:
        # Initialize and start engine
        engine = CoreCryptoEngine()
        engine.run()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())