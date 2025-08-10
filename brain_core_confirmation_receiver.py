#!/usr/bin/env python3
"""
Brain Core Confirmation Receiver
Part of the Python Brain Core (Command Center) that receives trade confirmations from EAs
According to the ZMQ pattern: PULL (central) ← PUSH (MT5)
This binds a PULL socket on port 5558 to receive confirmations from MT5 EAs
"""

import zmq
import json
import logging
from datetime import datetime
import os
import sys

# Add the src directory to path for imports
sys.path.insert(0, '/root/HydraX-v2/src')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BrainCoreConfirmation')

class BrainCoreConfirmationReceiver:
    """
    The Brain Core component that receives trade confirmations from user EAs.
    This is NOT part of signal engines - it's part of the central command center.
    """
    
    def __init__(self):
        self.context = zmq.Context()
        self.running = True
        
    def update_user_account(self, confirmation):
        """Update user account data based on trade confirmation"""
        # This would integrate with UserRegistryManager and other core systems
        user_id = confirmation.get('user_id')
        balance = confirmation.get('balance')
        result = confirmation.get('result')
        
        logger.info(f"📊 Updating account for user {user_id}")
        logger.info(f"   New balance: ${balance}")
        logger.info(f"   Trade result: {result}")
        
        # TODO: Integrate with actual user management systems
        # from bitten_core.user_registry_manager import UserRegistryManager
        # user_registry = UserRegistryManager()
        # user_registry.update_balance(user_id, balance)
        
    def process_confirmation(self, message):
        """Process incoming trade confirmation"""
        logger.info(f"🧠 BRAIN CORE received confirmation!")
        logger.info(f"   Signal ID: {message.get('signal_id')}")
        logger.info(f"   User ID: {message.get('user_id')}")
        logger.info(f"   Result: {message.get('result', 'UNKNOWN')}")
        logger.info(f"   Ticket: {message.get('ticket')}")
        logger.info(f"   Symbol: {message.get('symbol')}")
        logger.info(f"   Volume: {message.get('volume')}")
        logger.info(f"   Price: {message.get('price')}")
        logger.info(f"   Balance: {message.get('balance')}")
        logger.info(f"   Message: {message.get('message')}")
        
        # Update user account data
        self.update_user_account(message)
        
        # Log to persistent storage
        with open('/tmp/brain_core_confirmations.jsonl', 'a') as f:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'confirmation': message,
                'processed_by': 'brain_core'
            }
            f.write(json.dumps(log_entry) + '\n')
            
        # TODO: Integrate with other brain core systems
        # - Update XP system
        # - Update gamification badges
        # - Send notification to user via Telegram
        # - Update truth tracking system
        
    def run(self):
        """Run the brain core confirmation receiver"""
        # PULL socket to receive confirmations from MT5 EAs
        # Pattern: PULL (central brain) ← PUSH (MT5 EAs)
        receiver = self.context.socket(zmq.PULL)
        receiver.bind("tcp://*:5558")
        
        logger.info("="*60)
        logger.info("🧠 BRAIN CORE CONFIRMATION RECEIVER STARTED")
        logger.info("="*60)
        logger.info("📡 Listening on port 5558 for trade confirmations from EAs")
        logger.info("🔄 Pattern: PULL (brain core) ← PUSH (user EAs)")
        logger.info("💡 This is the COMMAND CENTER, not a signal engine!")
        logger.info("⏳ Waiting for trade confirmations...")
        logger.info("="*60)
        
        while self.running:
            try:
                # Set timeout to prevent blocking forever
                receiver.setsockopt(zmq.RCVTIMEO, 1000)
                
                # Receive the confirmation
                message = receiver.recv_json()
                
                # Process the confirmation through brain core systems
                self.process_confirmation(message)
                    
            except zmq.Again:
                # Timeout - no message received, continue
                pass
            except KeyboardInterrupt:
                logger.info("\n✅ Brain Core confirmation receiver stopped")
                break
            except Exception as e:
                logger.error(f"Error receiving confirmation: {e}")
                
        receiver.close()
        self.context.term()

if __name__ == "__main__":
    logger.info("Starting Brain Core Confirmation Receiver...")
    logger.info("This is the CENTRAL COMMAND CENTER component")
    logger.info("NOT a signal engine - this manages user accounts and confirmations")
    
    receiver = BrainCoreConfirmationReceiver()
    receiver.run()