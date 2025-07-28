#!/usr/bin/env python3
"""
Press Pass XP Reset System with Database Integration
Nightly XP wipe for Press Pass users with dramatic notifications
"""

import asyncio
import logging
from datetime import datetime, timezone, time as datetime_time
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if TYPE_CHECKING:
    from .xp_integration import XPIntegrationManager
from dataclasses import dataclass, asdict
import threading
import schedule
import time

from .telegram_messenger import TelegramMessenger
from .user_profile import UserProfileManager
from database.xp_database import XPDatabase, PressPassReset

logger = logging.getLogger(__name__)

@dataclass
class PressPassStats:
    """Simple Press Pass stats - no restoration, just current day tracking"""
    user_id: str
    xp_earned_today: int = 0
    trades_executed_today: int = 0
    total_resets: int = 0
    last_reset: Optional[str] = None

class PressPassResetManager:
    """Manages nightly XP resets for Press Pass users with database integration"""
    
    def __init__(
        self,
        xp_manager: "XPIntegrationManager",
        telegram: TelegramMessenger,
        xp_database: Optional[XPDatabase] = None
    ):
        self.xp_manager = xp_manager
        self.telegram = telegram
        self.xp_db = xp_database
        self.press_pass_users: List[str] = []
        
        # Schedule thread
        self.scheduler_thread = None
        self.running = False
        
        # Initialize database connection if not provided
        if not self.xp_db:
            self._init_db_task = asyncio.create_task(self._initialize_database())
        
    async def _initialize_database(self):
        """Initialize database connection"""
        try:
            self.xp_db = XPDatabase()
            await self.xp_db.initialize()
            await self.xp_db.initialize_tables()
            logger.info("Press Pass database connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            self.xp_db = None
    
    async def _ensure_db_ready(self):
        """Ensure database is initialized before use"""
        if hasattr(self, '_init_db_task'):
            await self._init_db_task
    
    def add_press_pass_user(self, user_id: str):
        """Add a user to Press Pass program"""
        if user_id not in self.press_pass_users:
            self.press_pass_users.append(user_id)
            logger.info(f"Added {user_id} to Press Pass program")
            
    def remove_press_pass_user(self, user_id: str):
        """Remove a user from Press Pass program"""
        if user_id in self.press_pass_users:
            self.press_pass_users.remove(user_id)
            logger.info(f"Removed {user_id} from Press Pass program")
    
    def is_press_pass_user(self, user_id: str) -> bool:
        """Check if user is in Press Pass program"""
        return user_id in self.press_pass_users
    
    async def get_user_xp_balance(self, user_id: str) -> int:
        """Get current XP balance from database"""
        await self._ensure_db_ready()
        
        if self.xp_db:
            try:
                # Convert string user_id to int for database
                user_id_int = int(user_id)
                balance = await self.xp_db.get_user_balance(user_id_int)
                if balance:
                    return balance.current_balance
            except Exception as e:
                logger.error(f"Failed to get XP balance from database: {e}")
        
        # Fallback to file-based system
        try:
            xp_status = self.xp_manager.get_user_xp_status(user_id)
            return xp_status["xp_economy"]["current_balance"]
        except:
            return 0
    
    async def send_warning_notification(self, hours_until_reset: float):
        """Send warning notification to Press Pass users"""
        for user_id in self.press_pass_users:
            try:
                # Get current XP that will be wiped
                current_xp = await self.get_user_xp_balance(user_id)
                
                if current_xp > 0:
                    if hours_until_reset == 1:
                        message = (
                            f"⚠️ **PRESS PASS XP RESET WARNING** ⚠️\n\n"
                            f"🕐 **1 HOUR UNTIL RESET**\n\n"
                            f"💀 Your {current_xp:} XP will be **WIPED** at 00:00 UTC!\n\n"
                            f"⏰ Time is running out! Use your XP NOW or lose it FOREVER!\n"
                            f"🛒 Visit /xpshop before it's too late!"
                        )
                    else:  # 15 minutes
                        message = (
                            f"🚨 **FINAL WARNING - 15 MINUTES** 🚨\n\n"
                            f"💥 **{current_xp:} XP DELETION IMMINENT** 💥\n\n"
                            f"⏱️ You have 15 MINUTES to spend your XP!\n"
                            f"🔥 This is your LAST CHANCE!\n"
                            f"💸 /xpshop - HURRY!"
                        )
                    
                    await self.telegram.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    
            except Exception as e:
                logger.error(f"Failed to send warning to {user_id}: {e}")
    
    async def execute_xp_reset(self):
        """Execute the XP reset for all Press Pass users using database"""
        await self._ensure_db_ready()
        
        reset_time = datetime.now(timezone.utc)
        total_wiped = 0
        resets_executed = []
        
        # Use database for atomic batch reset
        if self.xp_db:
            try:
                # Convert string user IDs to integers
                user_ids_int = []
                for user_id in self.press_pass_users:
                    try:
                        user_ids_int.append(int(user_id))
                    except ValueError:
                        logger.warning(f"Invalid user ID format: {user_id}")
                
                # Execute bulk reset in database
                resets = await self.xp_db.bulk_reset_press_pass_xp(user_ids_int)
                
                # Send notifications for each reset
                for reset in resets:
                    total_wiped += reset.xp_wiped
                    resets_executed.append(reset)
                    
                    # Send dramatic notification
                    message = (
                        f"💀 **XP RESET EXECUTED** 💀\n\n"
                        f"🔥 **{reset.xp_wiped:} XP DESTROYED** 🔥\n\n"
                        f"Your Press Pass XP has been reset to ZERO.\n"
                        f"**NO RECOVERY. NO RESTORATION.**\n\n"
                        f"⏰ Next reset: Tomorrow at 00:00 UTC\n"
                        f"💪 Start earning again - or enlist to keep your progress!"
                    )
                    
                    await self.telegram.send_message(
                        chat_id=str(reset.user_id),
                        text=message,
                        parse_mode='Markdown'
                    )
                    
                    # Mark notification as sent
                    await self.xp_db.mark_reset_notification_sent(reset.reset_id)
                    
                    logger.info(f"Wiped {reset.xp_wiped} XP from user {reset.user_id} - NO RESTORATION")
                
            except Exception as e:
                logger.error(f"Database reset failed, falling back to file-based: {e}")
                # Fallback to file-based reset
                await self._execute_file_based_reset()
        else:
            # Use file-based system if database not available
            await self._execute_file_based_reset()
        
        logger.info(f"Press Pass reset complete. Total XP wiped: {total_wiped}")
        return total_wiped
    
    async def _execute_file_based_reset(self):
        """Fallback file-based reset (legacy support)"""
        total_wiped = 0
        
        for user_id in self.press_pass_users:
            try:
                # Get current XP before wipe
                xp_status = self.xp_manager.get_user_xp_status(user_id)
                current_xp = xp_status["xp_economy"]["current_balance"]
                
                if current_xp > 0:
                    # Wipe the XP (set to 0) - GONE FOREVER
                    self.xp_manager.xp_economy.users[user_id].current_balance = 0
                    self.xp_manager.xp_economy._save_user_data(user_id)
                    
                    # Send dramatic notification
                    message = (
                        f"💀 **XP RESET EXECUTED** 💀\n\n"
                        f"🔥 **{current_xp:} XP DESTROYED** 🔥\n\n"
                        f"Your Press Pass XP has been reset to ZERO.\n"
                        f"**NO RECOVERY. NO RESTORATION.**\n\n"
                        f"⏰ Next reset: Tomorrow at 00:00 UTC\n"
                        f"💪 Start earning again - or enlist to keep your progress!"
                    )
                    
                    await self.telegram.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    
                    total_wiped += current_xp
                    logger.info(f"Wiped {current_xp} XP from user {user_id} - NO RESTORATION")
                    
            except Exception as e:
                logger.error(f"Failed to reset XP for {user_id}: {e}")
        
        return total_wiped
    
    async def get_press_pass_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get Press Pass stats for a user from database"""
        await self._ensure_db_ready()
        
        if self.xp_db:
            try:
                user_id_int = int(user_id)
                
                # Get from press_pass_shadow_stats table
                async with self.xp_db.get_connection() as conn:
                    row = await conn.fetchrow('''
                        SELECT xp_earned_today, trades_executed_today, total_resets, last_reset_at
                        FROM press_pass_shadow_stats
                        WHERE user_id = $1
                    ''', user_id_int)
                    
                    if row:
                        return {
                            'user_id': user_id,
                            'xp_earned_today': row['xp_earned_today'],
                            'trades_executed_today': row['trades_executed_today'],
                            'total_resets': row['total_resets'],
                            'last_reset': row['last_reset_at'].isoformat() if row['last_reset_at'] else None
                        }
            except Exception as e:
                logger.error(f"Failed to get stats from database: {e}")
        
        return None
    
    def get_current_xp_for_enlistment(self, user_id: str) -> int:
        """Get current day's XP that would be preserved on enlistment"""
        # Only current day's XP, no historical data
        try:
            return asyncio.run(self.get_user_xp_balance(user_id))
        except:
            xp_status = self.xp_manager.get_user_xp_status(user_id)
            return xp_status["xp_economy"]["current_balance"]
    
    def start_scheduler(self):
        """Start the scheduler thread"""
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Press Pass reset scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler thread"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Press Pass reset scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in a separate thread"""
        # Schedule warning at 23:00 UTC (1 hour before)
        schedule.every().day.at("23:00").do(
            lambda: asyncio.create_task(self.send_warning_notification(1))
        )
        
        # Schedule warning at 23:45 UTC (15 minutes before)
        schedule.every().day.at("23:45").do(
            lambda: asyncio.create_task(self.send_warning_notification(0.25))
        )
        
        # Schedule reset at 00:00 UTC
        schedule.every().day.at("00:00").do(
            lambda: asyncio.create_task(self.execute_xp_reset())
        )
        
        logger.info("Press Pass reset scheduled for 00:00 UTC daily")
        logger.info("Warnings scheduled for 23:00 and 23:45 UTC")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    async def manual_reset(self, user_id: Optional[str] = None):
        """Manually trigger reset for testing"""
        if user_id:
            # Reset specific user
            if user_id in self.press_pass_users:
                original_users = self.press_pass_users.copy()
                self.press_pass_users = [user_id]
                await self.execute_xp_reset()
                self.press_pass_users = original_users
        else:
            # Reset all Press Pass users
            await self.execute_xp_reset()
    
    async def load_press_pass_users_from_db(self) -> List[str]:
        """Load Press Pass users from database"""
        await self._ensure_db_ready()
        
        if self.xp_db:
            try:
                async with self.xp_db.get_connection() as conn:
                    rows = await conn.fetch('''
                        SELECT DISTINCT user_id 
                        FROM press_pass_shadow_stats
                    ''')
                    
                    return [str(row['user_id']) for row in rows]
            except Exception as e:
                logger.error(f"Failed to load Press Pass users from database: {e}")
        
        return []
    
    async def sync_with_database(self):
        """Sync local Press Pass user list with database"""
        db_users = await self.load_press_pass_users_from_db()
        
        # Merge with existing users
        for user_id in db_users:
            if user_id not in self.press_pass_users:
                self.press_pass_users.append(user_id)
        
        logger.info(f"Synced {len(self.press_pass_users)} Press Pass users with database")
    
    async def cleanup(self):
        """Clean up database connections"""
        if self.xp_db:
            await self.xp_db.close()
            logger.info("Press Pass database connection closed")