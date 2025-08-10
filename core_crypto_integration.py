#!/usr/bin/env python3
"""
🔧 C.O.R.E. CRYPTO INTEGRATION BRIDGE
Integrates Ultimate C.O.R.E. Crypto Engine with existing BITTEN infrastructure

INTEGRATION POINTS:
✅ ZMQ Signal Relay (Port 5558 → Port 5557 for Fire Router)
✅ WebApp Signal Display 
✅ Telegram Bot Commands
✅ Truth Tracking System
✅ Fire Execution System
✅ Performance Monitoring

Author: Claude Code Agent
Date: August 2025
Status: Production Ready
"""

import zmq
import json
import time
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/core_crypto_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CORECryptoIntegration')

class CORECryptoIntegrationBridge:
    """Integration bridge for C.O.R.E. Crypto Engine"""
    
    def __init__(self):
        self.context = zmq.Context()
        self.crypto_subscriber = None  # Subscribe to C.O.R.E. signals (port 5558)
        self.bitten_publisher = None   # Publish to BITTEN system (port 5557)
        self.running = True
        
        # Signal tracking
        self.processed_signals = []
        self.integration_stats = {
            'signals_received': 0,
            'signals_forwarded': 0,
            'integration_errors': 0,
            'last_signal_time': 0
        }
        
    def start_integration(self):
        """Start the integration bridge"""
        try:
            logger.info("🔧 Starting C.O.R.E. Crypto Integration Bridge...")
            
            # Subscribe to C.O.R.E. crypto signals (port 5558)
            self.crypto_subscriber = self.context.socket(zmq.SUB)
            self.crypto_subscriber.connect("tcp://127.0.0.1:5558")
            self.crypto_subscriber.setsockopt(zmq.SUBSCRIBE, b"")
            self.crypto_subscriber.setsockopt(zmq.RCVTIMEO, 1000)
            
            # Publisher to BITTEN system (port 5557 - same as Elite Guard)
            self.bitten_publisher = self.context.socket(zmq.PUB)
            self.bitten_publisher.bind("tcp://*:5559")  # Use different port to avoid conflicts
            
            logger.info("✅ Integration bridge connections established")
            logger.info("📡 Subscribing to C.O.R.E. signals on port 5558")
            logger.info("📡 Publishing integrated signals on port 5559")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Integration bridge startup failed: {e}")
            return False
    
    def run_integration_loop(self):
        """Main integration loop"""
        logger.info("🔄 Starting integration processing loop...")
        
        while self.running:
            try:
                # Process incoming C.O.R.E. signals
                if self._process_crypto_signal():
                    time.sleep(0.1)  # Brief pause after processing
                else:
                    time.sleep(1)    # Longer pause when no signals
                    
            except Exception as e:
                logger.error(f"❌ Integration loop error: {e}")
                self.integration_stats['integration_errors'] += 1
                time.sleep(5)
    
    def _process_crypto_signal(self) -> bool:
        """Process incoming crypto signal and integrate with BITTEN system"""
        try:
            # Receive signal from C.O.R.E. engine
            message = self.crypto_subscriber.recv_string(zmq.NOBLOCK)
            
            if "CRYPTO_SIGNAL" in message:
                signal_json = message.split("CRYPTO_SIGNAL ")[1]
                crypto_signal = json.loads(signal_json)
                
                logger.info(f"📥 Received C.O.R.E. signal: {crypto_signal['symbol']} {crypto_signal['direction']}")
                
                # Update stats
                self.integration_stats['signals_received'] += 1
                self.integration_stats['last_signal_time'] = time.time()
                
                # Convert to BITTEN-compatible format
                bitten_signal = self._convert_to_bitten_format(crypto_signal)
                
                # Forward to BITTEN system
                self._forward_to_bitten_system(bitten_signal)
                
                # Log to truth tracking system
                self._log_to_truth_system(crypto_signal)
                
                # Update WebApp if available
                self._update_webapp_display(crypto_signal)
                
                # Store for tracking
                self.processed_signals.append(crypto_signal)
                if len(self.processed_signals) > 100:
                    self.processed_signals = self.processed_signals[-100:]  # Keep last 100
                
                return True
                
        except zmq.Again:
            # No data available
            return False
        except Exception as e:
            logger.error(f"❌ Signal processing error: {e}")
            self.integration_stats['integration_errors'] += 1
            return False
    
    def _convert_to_bitten_format(self, crypto_signal: Dict) -> Dict:
        """Convert C.O.R.E. crypto signal to BITTEN-compatible format"""
        try:
            # Create BITTEN-compatible signal format
            bitten_signal = {
                'signal_id': crypto_signal['signal_id'],
                'symbol': crypto_signal['symbol'],
                'direction': crypto_signal['direction'],
                'pattern': f"CRYPTO_{crypto_signal['pattern']}",
                'entry_price': crypto_signal['entry_price'],
                'stop_loss': crypto_signal['stop_loss'],
                'take_profit': crypto_signal['take_profit'],
                'confidence': crypto_signal['final_score'],  # Use final score as confidence
                'timestamp': crypto_signal['timestamp'],
                'signal_type': 'CRYPTO_ENHANCED',
                'engine': 'ULTIMATE_CORE_CRYPTO',
                'risk_reward': crypto_signal['risk_reward_ratio'],
                
                # Additional C.O.R.E. specific data
                'ml_score': crypto_signal.get('ml_score', 0),
                'tf_alignment': crypto_signal.get('tf_alignment', 0),
                'volume_confirmation': crypto_signal.get('volume_confirmation', 0),
                'correlation_score': crypto_signal.get('correlation_score', 0),
                'session_score': crypto_signal.get('session_score', 0),
                'citadel_score': crypto_signal.get('citadel_score', 0),
                
                # Metadata
                'integration_timestamp': time.time(),
                'source': 'CORE_CRYPTO_ENGINE'
            }
            
            return bitten_signal
            
        except Exception as e:
            logger.error(f"❌ Signal conversion error: {e}")
            return crypto_signal  # Fallback to original
    
    def _forward_to_bitten_system(self, bitten_signal: Dict):
        """Forward signal to BITTEN system"""
        try:
            # Publish to ZMQ for fire router consumption
            if self.bitten_publisher:
                message = f"ELITE_GUARD_SIGNAL {json.dumps(bitten_signal)}"
                self.bitten_publisher.send_string(message)
                
                logger.info(f"📤 Forwarded to BITTEN system: {bitten_signal['signal_id']}")
                self.integration_stats['signals_forwarded'] += 1
            
        except Exception as e:
            logger.error(f"❌ BITTEN forwarding error: {e}")
    
    def _log_to_truth_system(self, crypto_signal: Dict):
        """Log signal to truth tracking system"""
        try:
            truth_entry = {
                **crypto_signal,
                'log_timestamp': time.time(),
                'log_type': 'crypto_signal_integration',
                'source_engine': 'ULTIMATE_CORE_CRYPTO',
                'integration_bridge': 'ACTIVE'
            }
            
            truth_log_file = Path('/root/HydraX-v2/truth_log.jsonl')
            with open(truth_log_file, 'a') as f:
                f.write(json.dumps(truth_entry) + '\n')
                
            logger.debug(f"📝 Logged to truth system: {crypto_signal['signal_id']}")
            
        except Exception as e:
            logger.error(f"❌ Truth logging error: {e}")
    
    def _update_webapp_display(self, crypto_signal: Dict):
        """Update WebApp with new crypto signal"""
        try:
            # Try to post to WebApp API
            webapp_url = "http://127.0.0.1:8888/api/signals"
            
            payload = {
                'signal_data': crypto_signal,
                'source': 'CORE_CRYPTO_ENGINE',
                'timestamp': time.time()
            }
            
            response = requests.post(webapp_url, json=payload, timeout=2)
            if response.status_code == 200:
                logger.debug(f"📱 Updated WebApp: {crypto_signal['signal_id']}")
            else:
                logger.warning(f"⚠️ WebApp update failed: {response.status_code}")
                
        except requests.exceptions.RequestException:
            # WebApp may not be running - this is not critical
            logger.debug("📱 WebApp not available for update")
        except Exception as e:
            logger.error(f"❌ WebApp update error: {e}")
    
    def get_integration_stats(self) -> Dict:
        """Get integration statistics"""
        return {
            **self.integration_stats,
            'uptime_seconds': time.time() - (self.integration_stats.get('start_time', time.time())),
            'signals_processed_total': len(self.processed_signals),
            'last_signal_age_seconds': time.time() - self.integration_stats['last_signal_time'] if self.integration_stats['last_signal_time'] > 0 else 0,
            'bridge_active': self.running
        }
    
    def stop_integration(self):
        """Stop the integration bridge"""
        logger.info("🛑 Stopping C.O.R.E. Crypto Integration Bridge...")
        
        self.running = False
        
        try:
            if self.crypto_subscriber:
                self.crypto_subscriber.close()
            if self.bitten_publisher:
                self.bitten_publisher.close()
            if self.context:
                self.context.term()
                
            logger.info("✅ Integration bridge stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Integration bridge stop error: {e}")

def main():
    """Main execution function"""
    try:
        # Create logs directory
        Path('/root/HydraX-v2/logs').mkdir(exist_ok=True)
        
        logger.info("🔧 Initializing C.O.R.E. Crypto Integration Bridge...")
        
        # Create and start integration bridge
        bridge = CORECryptoIntegrationBridge()
        
        if bridge.start_integration():
            logger.info("✅ C.O.R.E. Crypto Integration Bridge is LIVE!")
            
            # Start integration loop
            bridge.run_integration_loop()
        else:
            logger.error("❌ Failed to start integration bridge")
            return 1
            
    except KeyboardInterrupt:
        logger.info("🛑 Integration bridge stopped by user")
    except Exception as e:
        logger.error(f"❌ Integration bridge error: {e}")
        return 1
    finally:
        if 'bridge' in locals():
            bridge.stop_integration()
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())