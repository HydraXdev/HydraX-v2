#!/usr/bin/env python3
"""
Elite Guard ZMQ-to-HTTP Relay
Bridges Elite Guard ZMQ signals (port 5557) to BITTEN WebApp (/api/signals)

🎯 PURPOSE:
Elite Guard publishes signals via ZMQ but nothing was listening.
This relay receives those ZMQ messages and POSTs them to the WebApp
to trigger the full mission lifecycle: BittenCore → ATHENA → Telegram → HUD

🔄 SIGNAL FLOW:
Elite Guard (ZMQ 5557) → This Relay → POST /api/signals → BittenCore → Missions → Alerts

🚨 CRITICAL: This relay is the missing link that enables full signal processing.
Without it, Elite Guard signals are silently lost.
"""

import zmq
import json
import time
import logging
import requests
import threading
from datetime import datetime
from typing import Dict, Optional
import signal as signal_handler
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/elite_guard_zmq_relay.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EliteGuardZMQRelay')

class EliteGuardZMQRelay:
    """ZMQ-to-HTTP relay for Elite Guard signals"""
    
    def __init__(self):
        self.running = False
        self.context = zmq.Context()
        self.subscriber = None
        
        # Configuration
        self.zmq_endpoint = "tcp://127.0.0.1:5557"
        self.webapp_url = "http://localhost:8888/api/signals"
        self.http_timeout = 3
        self.reconnect_delay = 5
        
        # Statistics
        self.stats = {
            'signals_received': 0,
            'signals_relayed': 0,
            'http_errors': 0,
            'zmq_errors': 0,
            'started_at': None
        }
        
    def start(self):
        """Start the ZMQ-to-HTTP relay"""
        self.running = True
        self.stats['started_at'] = datetime.utcnow().isoformat()
        
        logger.info("🚀 Starting Elite Guard ZMQ-to-HTTP Relay")
        logger.info(f"📡 ZMQ Source: {self.zmq_endpoint}")
        logger.info(f"🌐 HTTP Target: {self.webapp_url}")
        logger.info("=" * 60)
        
        # Start relay loop in separate thread
        relay_thread = threading.Thread(target=self._relay_loop, daemon=True)
        relay_thread.start()
        
        logger.info("✅ Elite Guard ZMQ Relay started successfully")
        logger.info("🔍 Listening for ELITE_GUARD_SIGNAL messages...")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown signal received")
            self.stop()
    
    def stop(self):
        """Stop the relay"""
        self.running = False
        if self.subscriber:
            self.subscriber.close()
        self.context.term()
        
        logger.info("📊 Final Statistics:")
        logger.info(f"   Signals Received: {self.stats['signals_received']}")
        logger.info(f"   Signals Relayed: {self.stats['signals_relayed']}")
        logger.info(f"   HTTP Errors: {self.stats['http_errors']}")
        logger.info(f"   ZMQ Errors: {self.stats['zmq_errors']}")
        logger.info("🔒 Elite Guard ZMQ Relay stopped")
    
    def _relay_loop(self):
        """Main relay loop - receives ZMQ and sends HTTP"""
        while self.running:
            try:
                self._setup_zmq_connection()
                self._listen_and_relay()
            except Exception as e:
                logger.error(f"Relay loop error: {e}")
                self.stats['zmq_errors'] += 1
                if self.running:
                    logger.info(f"⏳ Reconnecting in {self.reconnect_delay} seconds...")
                    time.sleep(self.reconnect_delay)
    
    def _setup_zmq_connection(self):
        """Setup ZMQ subscriber connection"""
        if self.subscriber:
            self.subscriber.close()
            
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(self.zmq_endpoint)
        self.subscriber.subscribe(b'')  # Subscribe to all messages
        self.subscriber.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
        
        logger.debug(f"📡 Connected to ZMQ endpoint: {self.zmq_endpoint}")
    
    def _listen_and_relay(self):
        """Listen for ZMQ messages and relay to HTTP"""
        while self.running:
            try:
                # Receive ZMQ message
                message = self.subscriber.recv_string()
                self.stats['signals_received'] += 1
                
                logger.debug(f"📨 Raw ZMQ message: {message[:100]}...")
                
                # Parse Elite Guard signal
                signal_data = self._parse_elite_guard_message(message)
                if not signal_data:
                    continue
                
                # Convert to WebApp format
                webapp_signal = self._convert_to_webapp_format(signal_data)
                
                # Skip if safety check failed
                if webapp_signal is None:
                    logger.error(f"Skipping signal relay due to missing SL/TP")
                    continue
                
                # Relay to WebApp
                success = self._send_to_webapp(webapp_signal)
                if success:
                    self.stats['signals_relayed'] += 1
                    logger.info(f"✅ Signal relayed: {signal_data.get('signal_id')} "
                              f"({signal_data.get('symbol')} {signal_data.get('direction')})")
                else:
                    self.stats['http_errors'] += 1
                    
            except zmq.Again:
                # Timeout - normal, just continue
                continue
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                self.stats['zmq_errors'] += 1
    
    def _parse_elite_guard_message(self, message: str) -> Optional[Dict]:
        """Parse Elite Guard ZMQ message"""
        try:
            # Elite Guard sends "ELITE_GUARD_SIGNAL {json}"
            if message.startswith("ELITE_GUARD_SIGNAL "):
                json_str = message[19:]  # Remove prefix
                signal_data = json.loads(json_str)
                return signal_data
            else:
                # Try to parse as direct JSON (fallback)
                signal_data = json.loads(message)
                return signal_data
                
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Invalid JSON in message: {e}")
            logger.debug(f"   Message: {message}")
            return None
        except Exception as e:
            logger.error(f"Message parsing error: {e}")
            return None
    
    def _convert_to_webapp_format(self, elite_signal: Dict) -> Dict:
        """Convert Elite Guard format to WebApp /api/signals format"""
        
        # DEBUG: Log what fields we received
        logger.info(f"🔍 Signal received with fields: {list(elite_signal.keys())}")
        if 'stop_loss' in elite_signal:
            logger.info(f"   stop_loss: {elite_signal['stop_loss']}")
        if 'take_profit' in elite_signal:
            logger.info(f"   take_profit: {elite_signal['take_profit']}")
        if 'sl' in elite_signal:
            logger.info(f"   sl: {elite_signal['sl']}")
        if 'tp' in elite_signal:
            logger.info(f"   tp: {elite_signal['tp']}")
        
        # Get current timestamp
        current_time = time.time()
        
        # Convert Elite Guard signal to WebApp format
        # Based on send_signal_to_webapp.py format
        webapp_signal = {
            # Core signal data
            'signal_id': elite_signal.get('signal_id'),
            'pair': elite_signal.get('pair', elite_signal.get('symbol')),
            'symbol': elite_signal.get('symbol', elite_signal.get('pair')),
            'direction': elite_signal.get('direction'),
            'signal_type': elite_signal.get('signal_type', 'ELITE_GUARD'),
            'pattern': elite_signal.get('pattern', 'UNKNOWN'),
            
            # Confidence and scoring
            'confidence': elite_signal.get('confidence', 0),
            'tcs_score': elite_signal.get('confidence', 0),  # WebApp expects this
            'base_confidence': elite_signal.get('base_confidence', elite_signal.get('confidence', 0)),
            
            # Price levels - CRITICAL: Never default SL/TP to 0!
            'entry_price': elite_signal.get('entry_price') or 1.0000,  # Default entry for validation
            'stop_loss': elite_signal.get('stop_loss') or elite_signal.get('sl') or 0,  # Check both field names
            'take_profit': elite_signal.get('take_profit') or elite_signal.get('tp') or 0,  # Check both field names
            'stop_pips': elite_signal.get('stop_pips') or 10,  # Default 10 pips SL
            'target_pips': elite_signal.get('target_pips') or 20,  # Default 20 pips TP
            'risk_reward': elite_signal.get('risk_reward') or 2.0,  # Default 1:2 R:R
            
            # Trading parameters
            'duration': elite_signal.get('duration', 1800),  # Default 30 min
            'xp_reward': int(elite_signal.get('confidence', 50)),  # XP based on confidence
            
            # Market context
            'session': elite_signal.get('session', 'UNKNOWN'),
            'timeframe': elite_signal.get('timeframe', 'M5'),
            'timestamp': current_time,
            'source': 'ELITE_GUARD_v6',
            
            # CITADEL Shield data (if present)
            'citadel_shielded': elite_signal.get('citadel_shielded', False),
            'consensus_confidence': elite_signal.get('citadel_shield', {}).get('score', 0),
            'shield_score': elite_signal.get('citadel_shield', {}).get('score', 0),
            'quality': self._determine_quality(elite_signal.get('confidence', 0)),
            
            # Mission briefing data
            'countdown_seconds': elite_signal.get('duration', 300),
            'market_conditions': elite_signal.get('market_regime', 'UNKNOWN'),
            'volatility': elite_signal.get('volatility', 'NORMAL'),
            'signal_strength': self._determine_strength(elite_signal.get('confidence', 0))
        }
        
        # CRITICAL SAFETY CHECK: Never send signals without SL/TP
        if (webapp_signal.get('stop_loss') is None or webapp_signal.get('stop_loss') == 0) or \
           (webapp_signal.get('take_profit') is None or webapp_signal.get('take_profit') == 0):
            logger.error(f"🚨 CRITICAL: Refusing to relay signal {webapp_signal['signal_id']} - Missing SL/TP!")
            logger.error(f"   Entry: {webapp_signal.get('entry_price')}, SL: {webapp_signal.get('stop_loss')}, TP: {webapp_signal.get('take_profit')}")
            logger.error(f"   Original signal had: stop_loss={elite_signal.get('stop_loss')}, take_profit={elite_signal.get('take_profit')}")
            return None  # Return None to prevent relaying
        
        return webapp_signal
    
    def _determine_quality(self, confidence: float) -> str:
        """Determine signal quality based on confidence"""
        if confidence >= 85:
            return 'platinum'
        elif confidence >= 75:
            return 'gold'
        elif confidence >= 65:
            return 'silver'
        else:
            return 'bronze'
    
    def _determine_strength(self, confidence: float) -> str:
        """Determine signal strength based on confidence"""
        if confidence >= 85:
            return 'VERY_STRONG'
        elif confidence >= 75:
            return 'STRONG'
        elif confidence >= 65:
            return 'MODERATE'
        else:
            return 'WEAK'
    
    def _send_to_webapp(self, signal_data: Dict) -> bool:
        """Send signal to WebApp /api/signals endpoint"""
        try:
            logger.debug(f"📤 Sending to WebApp: {signal_data['signal_id']}")
            
            response = requests.post(
                self.webapp_url,
                json=signal_data,
                timeout=self.http_timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.debug(f"✅ WebApp response: {response.status_code}")
                return True
            else:
                logger.warning(f"⚠️ WebApp error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ HTTP timeout to WebApp ({self.http_timeout}s)")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("🔌 Connection error to WebApp - is it running on port 8888?")
            return False
        except Exception as e:
            logger.error(f"HTTP relay error: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get relay statistics"""
        stats = self.stats.copy()
        if stats['started_at']:
            start_time = datetime.fromisoformat(stats['started_at'])
            uptime = datetime.utcnow() - start_time
            stats['uptime_seconds'] = int(uptime.total_seconds())
        return stats

def main():
    """Run the Elite Guard ZMQ Relay"""
    
    # Setup signal handlers for graceful shutdown
    relay = EliteGuardZMQRelay()
    
    def signal_handler_func(sig, frame):
        logger.info(f"\n🛑 Received signal {sig}")
        relay.stop()
        sys.exit(0)
    
    signal_handler.signal(signal_handler.SIGINT, signal_handler_func)
    signal_handler.signal(signal_handler.SIGTERM, signal_handler_func)
    
    # Print startup banner
    print("=" * 60)
    print("🚀 ELITE GUARD ZMQ-TO-HTTP RELAY")
    print("=" * 60)
    print("📡 Bridging: Elite Guard ZMQ → BITTEN WebApp")
    print("🎯 Purpose: Enable full mission lifecycle for Elite Guard signals")
    print("🔄 Flow: ZMQ 5557 → HTTP /api/signals → BittenCore → ATHENA → Telegram")
    print("=" * 60)
    
    # Start relay
    try:
        relay.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()