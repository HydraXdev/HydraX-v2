#!/usr/bin/env python3
"""
Message Expiry Checker - Monitors and marks expired Telegram alerts
Runs as background service to edit expired trading signals in chat
"""

import asyncio
import json
import os
import time
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageExpiryChecker:
    """Checks for expired messages and edits them in Telegram"""
    
    def __init__(self):
        self.expiry_dir = Path("data/message_expiry")
        self.expiry_dir.mkdir(parents=True, exist_ok=True)
        
    async def check_expired_messages(self):
        """Check all stored messages for entry expiry and deletion"""
        current_time = datetime.now()
        entry_expired_count = 0
        deleted_count = 0
        
        try:
            # Import the flow to access Telegram bot
            from apex_mission_integrated_flow import create_apex_mission_flow
            flow = create_apex_mission_flow()
            
            # Check all expiry files
            for expiry_file in self.expiry_dir.glob("*.json"):
                try:
                    with open(expiry_file, 'r') as f:
                        expiry_data = json.load(f)
                    
                    entry_expires_at = datetime.fromisoformat(expiry_data['entry_expires_at'])
                    delete_at = datetime.fromisoformat(expiry_data['delete_at'])
                    mission_id = expiry_data['mission_id']
                    
                    # Check if message should be completely deleted (4 hours)
                    if current_time > delete_at:
                        success = await flow.delete_expired_message(mission_id)
                        if success:
                            deleted_count += 1
                            logger.info(f"🗑️ Deleted {mission_id} from chat")
                    
                    # Check if entry window expired (30 minutes) but not yet deleted
                    elif current_time > entry_expires_at and not expiry_data.get('entry_marked', False):
                        success = await flow.mark_message_entry_expired(mission_id)
                        if success:
                            entry_expired_count += 1
                            # Mark as processed
                            expiry_data['entry_marked'] = True
                            with open(expiry_file, 'w') as f:
                                json.dump(expiry_data, f, indent=2)
                            logger.info(f"⏰ Marked {mission_id} entry closed")
                        
                except Exception as e:
                    logger.error(f"Error processing expiry file {expiry_file}: {e}")
            
            if entry_expired_count > 0 or deleted_count > 0:
                logger.info(f"✅ Entry expired: {entry_expired_count}, Deleted: {deleted_count}")
                
        except Exception as e:
            logger.error(f"Error in expiry check: {e}")
    
    async def run_continuous(self, check_interval=300):  # Check every 5 minutes
        """Run continuous expiry checking"""
        logger.info("🕐 Starting message expiry checker...")
        
        while True:
            try:
                await self.check_expired_messages()
                await asyncio.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Expiry checker stopped")
                break
            except Exception as e:
                logger.error(f"Expiry checker error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

async def main():
    """Main entry point"""
    checker = MessageExpiryChecker()
    await checker.run_continuous()

if __name__ == "__main__":
    asyncio.run(main())