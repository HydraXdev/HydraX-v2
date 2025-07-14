#!/usr/bin/env python3
"""
Press Pass XP Reset Job
Scheduled job for nightly XP resets with database integration
Can be run via cron or any job scheduler
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.xp_database import XPDatabase
from src.bitten_core.telegram_messenger import TelegramMessenger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/bitten/press_pass_reset.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PressPassResetJob:
    """Handles the nightly Press Pass XP reset job"""
    
    def __init__(self):
        self.xp_db = None
        self.telegram = None
        
    async def initialize(self):
        """Initialize database and telegram connections"""
        try:
            # Initialize database
            self.xp_db = XPDatabase()
            await self.xp_db.initialize()
            logger.info("Database connection initialized")
            
            # Initialize Telegram (if available)
            try:
                self.telegram = TelegramMessenger()
                await self.telegram.initialize()
                logger.info("Telegram messenger initialized")
            except Exception as e:
                logger.warning(f"Telegram not available: {e}")
                self.telegram = None
                
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise
    
    async def get_press_pass_users(self) -> List[Dict[str, Any]]:
        """Get all Press Pass users with positive XP balance"""
        async with self.xp_db.get_connection() as conn:
            rows = await conn.fetch('''
                SELECT 
                    xb.user_id,
                    xb.current_balance,
                    ps.total_resets,
                    ps.last_reset_at
                FROM xp_balances xb
                INNER JOIN press_pass_shadow_stats ps ON xb.user_id = ps.user_id
                WHERE xb.current_balance > 0
                ORDER BY xb.current_balance DESC
            ''')
            
            return [
                {
                    'user_id': row['user_id'],
                    'current_balance': row['current_balance'],
                    'total_resets': row['total_resets'],
                    'last_reset_at': row['last_reset_at']
                }
                for row in rows
            ]
    
    async def send_reset_notification(self, user_id: int, xp_wiped: int):
        """Send reset notification to user"""
        if not self.telegram:
            return
            
        try:
            message = (
                f"💀 **XP RESET EXECUTED** 💀\n\n"
                f"🔥 **{xp_wiped:,} XP DESTROYED** 🔥\n\n"
                f"Your Press Pass XP has been reset to ZERO.\n"
                f"**NO RECOVERY. NO RESTORATION.**\n\n"
                f"⏰ Next reset: Tomorrow at 00:00 UTC\n"
                f"💪 Start earning again - or enlist to keep your progress!"
            )
            
            await self.telegram.send_message(
                chat_id=str(user_id),
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"Sent reset notification to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send notification to {user_id}: {e}")
    
    async def execute_reset(self):
        """Execute the Press Pass XP reset"""
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting Press Pass XP reset at {start_time}")
        
        try:
            # Get users to reset
            users = await self.get_press_pass_users()
            logger.info(f"Found {len(users)} Press Pass users with XP to reset")
            
            if not users:
                logger.info("No users to reset")
                return
            
            # Extract user IDs
            user_ids = [user['user_id'] for user in users]
            
            # Execute bulk reset
            resets = await self.xp_db.bulk_reset_press_pass_xp(user_ids)
            
            # Send notifications
            total_wiped = 0
            notifications_sent = 0
            
            for reset in resets:
                total_wiped += reset.xp_wiped
                
                # Send notification
                await self.send_reset_notification(reset.user_id, reset.xp_wiped)
                notifications_sent += 1
                
                # Mark notification as sent in database
                await self.xp_db.mark_reset_notification_sent(reset.reset_id)
                
                # Small delay between notifications to avoid rate limiting
                await asyncio.sleep(0.1)
            
            # Log summary
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Press Pass reset completed:")
            logger.info(f"  - Users reset: {len(resets)}")
            logger.info(f"  - Total XP wiped: {total_wiped:,}")
            logger.info(f"  - Notifications sent: {notifications_sent}")
            logger.info(f"  - Duration: {duration:.2f} seconds")
            
            # Update job statistics
            async with self.xp_db.get_connection() as conn:
                await conn.execute('''
                    INSERT INTO job_execution_log 
                    (job_name, execution_time, success, records_processed, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                ''', 'press_pass_reset', start_time, True, len(resets),
                    {
                        'total_xp_wiped': total_wiped,
                        'notifications_sent': notifications_sent,
                        'duration_seconds': duration
                    })
            
        except Exception as e:
            logger.error(f"Reset job failed: {e}")
            
            # Log failure
            async with self.xp_db.get_connection() as conn:
                await conn.execute('''
                    INSERT INTO job_execution_log 
                    (job_name, execution_time, success, error_message)
                    VALUES ($1, $2, $3, $4)
                ''', 'press_pass_reset', start_time, False, str(e))
            
            raise
    
    async def send_warnings(self, minutes_before: int):
        """Send warning notifications before reset"""
        logger.info(f"Sending {minutes_before}-minute warnings")
        
        try:
            users = await self.get_press_pass_users()
            warnings_sent = 0
            
            for user in users:
                if user['current_balance'] > 0:
                    if minutes_before == 60:
                        message = (
                            f"⚠️ **PRESS PASS XP RESET WARNING** ⚠️\n\n"
                            f"🕐 **1 HOUR UNTIL RESET**\n\n"
                            f"💀 Your {user['current_balance']:,} XP will be **WIPED** at 00:00 UTC!\n\n"
                            f"⏰ Time is running out! Use your XP NOW or lose it FOREVER!\n"
                            f"🛒 Visit /xpshop before it's too late!"
                        )
                    else:  # 15 minutes
                        message = (
                            f"🚨 **FINAL WARNING - 15 MINUTES** 🚨\n\n"
                            f"💥 **{user['current_balance']:,} XP DELETION IMMINENT** 💥\n\n"
                            f"⏱️ You have 15 MINUTES to spend your XP!\n"
                            f"🔥 This is your LAST CHANCE!\n"
                            f"💸 /xpshop - HURRY!"
                        )
                    
                    if self.telegram:
                        try:
                            await self.telegram.send_message(
                                chat_id=str(user['user_id']),
                                text=message,
                                parse_mode='Markdown'
                            )
                            warnings_sent += 1
                        except Exception as e:
                            logger.error(f"Failed to send warning to {user['user_id']}: {e}")
                    
                    await asyncio.sleep(0.1)  # Rate limiting
            
            logger.info(f"Sent {warnings_sent} warning notifications")
            
        except Exception as e:
            logger.error(f"Failed to send warnings: {e}")
    
    async def cleanup(self):
        """Clean up connections"""
        if self.xp_db:
            await self.xp_db.close()
        if self.telegram:
            await self.telegram.close()


async def main(action: str = "reset"):
    """Main entry point for the job"""
    job = PressPassResetJob()
    
    try:
        await job.initialize()
        
        if action == "reset":
            await job.execute_reset()
        elif action == "warn_60":
            await job.send_warnings(60)
        elif action == "warn_15":
            await job.send_warnings(15)
        else:
            logger.error(f"Unknown action: {action}")
            
    finally:
        await job.cleanup()


if __name__ == "__main__":
    # Get action from command line argument
    import argparse
    
    parser = argparse.ArgumentParser(description="Press Pass XP Reset Job")
    parser.add_argument(
        "action",
        choices=["reset", "warn_60", "warn_15"],
        help="Action to perform"
    )
    
    args = parser.parse_args()
    
    # Run the job
    asyncio.run(main(args.action))