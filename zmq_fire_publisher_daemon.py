#!/usr/bin/env python3
"""
ZMQ Fire Publisher Daemon
Non-interactive version for production deployment
"""

# ┌──────────────────────────────────────────────────────────────┐
# │ BITTEN ZMQ SYSTEM - DO NOT FALL BACK TO FILE/HTTP ROUTES    │
# │ Persistent ZMQ architecture is required                      │
# │ EA v7 connects directly via libzmq.dll to 134.199.204.67    │
# │ All command, telemetry, and feedback must use ZMQ sockets   │
# └──────────────────────────────────────────────────────────────┘

import zmq
import json
import logging
import time
import signal
import sys
from zmq_bitten_controller import BITTENZMQController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('FirePublisherDaemon')

class FirePublisherDaemon:
    def __init__(self):
        self.controller = BITTENZMQController()
        self.running = True
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Shutdown signal received")
        self.running = False
        
    def run(self):
        """Run the daemon"""
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # Start controller
            self.controller.start()
            logger.info("✅ ZMQ Fire Publisher started successfully")
            logger.info("📡 Command port: 5555 (Core → EA)")
            logger.info("📡 Feedback port: 5556 (EA → Core)")
            
            # Keep running
            while self.running:
                time.sleep(1)
                
                # Log stats periodically
                if int(time.time()) % 30 == 0:
                    stats = {
                        'active_users': len(self.controller.user_telemetry),
                        'pending_trades': len(self.controller.pending_trades),
                        'trade_results': len(self.controller.trade_results)
                    }
                    logger.info(f"📊 Stats: {stats}")
                    
        except Exception as e:
            logger.error(f"Daemon error: {e}")
        finally:
            self.controller.stop()
            logger.info("✅ Fire Publisher daemon stopped")

if __name__ == "__main__":
    daemon = FirePublisherDaemon()
    daemon.run()