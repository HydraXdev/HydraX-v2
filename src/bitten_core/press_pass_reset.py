#!/usr/bin/env python3
"""
Press Pass XP Reset System
Nightly XP wipe for Press Pass users with dramatic notifications
"""

import json
import os
import asyncio
import logging
from datetime import datetime, timezone, time as datetime_time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import threading
import schedule
import time

from .telegram_messenger import TelegramMessenger
from .xp_integration import XPIntegrationManager
from .user_profile import UserProfileManager

logger = logging.getLogger(__name__)


@dataclass
class ShadowStats:
    """Shadow stats that persist through resets"""
    user_id: str
    real_total_xp: int = 0
    real_lifetime_earned: int = 0
    real_lifetime_spent: int = 0
    total_xp_wiped: int = 0
    reset_count: int = 0
    largest_wipe: int = 0
    last_reset: Optional[str] = None


class PressPassResetManager:
    """Manages nightly XP resets for Press Pass users"""
    
    def __init__(
        self,
        xp_manager: XPIntegrationManager,
        telegram: TelegramMessenger,
        shadow_data_path: str = "data/press_pass_shadow.json"
    ):
        self.xp_manager = xp_manager
        self.telegram = telegram
        self.shadow_data_path = shadow_data_path
        self.shadow_stats: Dict[str, ShadowStats] = {}
        self.press_pass_users: List[str] = []
        
        # Load shadow stats
        self._load_shadow_stats()
        
        # Schedule thread
        self.scheduler_thread = None
        self.running = False
        
    def _load_shadow_stats(self):
        """Load shadow stats from file"""
        if os.path.exists(self.shadow_data_path):
            try:
                with open(self.shadow_data_path, 'r') as f:
                    data = json.load(f)
                    for user_id, stats in data.items():
                        self.shadow_stats[user_id] = ShadowStats(**stats)
            except Exception as e:
                logger.error(f"Failed to load shadow stats: {e}")
                
    def _save_shadow_stats(self):
        """Save shadow stats to file"""
        try:
            os.makedirs(os.path.dirname(self.shadow_data_path), exist_ok=True)
            with open(self.shadow_data_path, 'w') as f:
                data = {
                    user_id: asdict(stats) 
                    for user_id, stats in self.shadow_stats.items()
                }
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save shadow stats: {e}")
    
    def add_press_pass_user(self, user_id: str):
        """Add a user to Press Pass program"""
        if user_id not in self.press_pass_users:
            self.press_pass_users.append(user_id)
            
            # Initialize shadow stats
            if user_id not in self.shadow_stats:
                # Get current stats to initialize shadow
                xp_status = self.xp_manager.get_user_xp_status(user_id)
                self.shadow_stats[user_id] = ShadowStats(
                    user_id=user_id,
                    real_total_xp=xp_status["profile"]["total_xp"],
                    real_lifetime_earned=xp_status["xp_economy"]["lifetime_earned"],
                    real_lifetime_spent=xp_status["xp_economy"]["lifetime_spent"]
                )
                self._save_shadow_stats()
                
            logger.info(f"Added {user_id} to Press Pass program")
            
    def remove_press_pass_user(self, user_id: str):
        """Remove a user from Press Pass program"""
        if user_id in self.press_pass_users:
            self.press_pass_users.remove(user_id)
            logger.info(f"Removed {user_id} from Press Pass program")
    
    def is_press_pass_user(self, user_id: str) -> bool:
        """Check if user is in Press Pass program"""
        return user_id in self.press_pass_users
    
    async def send_warning_notification(self, hours_until_reset: float):
        """Send warning notification to Press Pass users"""
        for user_id in self.press_pass_users:
            try:
                # Get current XP that will be wiped
                xp_status = self.xp_manager.get_user_xp_status(user_id)
                current_xp = xp_status["xp_economy"]["current_balance"]
                
                if current_xp > 0:
                    if hours_until_reset == 1:
                        message = (
                            f"⚠️ **PRESS PASS XP RESET WARNING** ⚠️\n\n"
                            f"🕐 **1 HOUR UNTIL RESET**\n\n"
                            f"💀 Your {current_xp:,} XP will be **WIPED** at 00:00 UTC!\n\n"
                            f"⏰ Time is running out! Use your XP NOW or lose it FOREVER!\n"
                            f"🛒 Visit /xpshop before it's too late!"
                        )
                    else:  # 15 minutes
                        message = (
                            f"🚨 **FINAL WARNING - 15 MINUTES** 🚨\n\n"
                            f"💥 **{current_xp:,} XP DELETION IMMINENT** 💥\n\n"
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
        """Execute the XP reset for all Press Pass users"""
        reset_time = datetime.now(timezone.utc).isoformat()
        total_wiped = 0
        
        for user_id in self.press_pass_users:
            try:
                # Get current XP before wipe
                xp_status = self.xp_manager.get_user_xp_status(user_id)
                current_xp = xp_status["xp_economy"]["current_balance"]
                
                if current_xp > 0:
                    # Update shadow stats before wipe
                    shadow = self.shadow_stats.get(user_id)
                    if shadow:
                        shadow.real_total_xp += current_xp
                        shadow.real_lifetime_earned += current_xp
                        shadow.total_xp_wiped += current_xp
                        shadow.reset_count += 1
                        shadow.largest_wipe = max(shadow.largest_wipe, current_xp)
                        shadow.last_reset = reset_time
                    
                    # Wipe the XP (set to 0)
                    self.xp_manager.xp_economy.users[user_id].current_balance = 0
                    self.xp_manager.xp_economy._save_user_data(user_id)
                    
                    # Send dramatic notification
                    message = (
                        f"💀 **XP RESET EXECUTED** 💀\n\n"
                        f"🔥 **{current_xp:,} XP DESTROYED** 🔥\n\n"
                        f"Your Press Pass XP has been reset to ZERO.\n"
                        f"The nightly purge is complete.\n\n"
                        f"⏰ Next reset: Tomorrow at 00:00 UTC\n"
                        f"💪 Start earning again - but remember, it's temporary!"
                    )
                    
                    await self.telegram.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    
                    total_wiped += current_xp
                    logger.info(f"Wiped {current_xp} XP from user {user_id}")
                    
            except Exception as e:
                logger.error(f"Failed to reset XP for {user_id}: {e}")
        
        # Save shadow stats
        self._save_shadow_stats()
        
        logger.info(f"Press Pass reset complete. Total XP wiped: {total_wiped}")
        
        return total_wiped
    
    def get_shadow_stats(self, user_id: str) -> Optional[ShadowStats]:
        """Get shadow stats for a user"""
        return self.shadow_stats.get(user_id)
    
    def get_real_xp(self, user_id: str) -> int:
        """Get real total XP including wiped amount"""
        shadow = self.shadow_stats.get(user_id)
        if shadow:
            return shadow.real_total_xp
        
        # If no shadow stats, return current XP
        xp_status = self.xp_manager.get_user_xp_status(user_id)
        return xp_status["profile"]["total_xp"]
    
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
                self.press_pass_users = [user_id]
                await self.execute_xp_reset()
                self.press_pass_users = self._load_press_pass_users()  # Reload full list
        else:
            # Reset all Press Pass users
            await self.execute_xp_reset()
    
    def _load_press_pass_users(self) -> List[str]:
        """Load Press Pass users from storage"""
        # This would typically load from a database or file
        # For now, return the current list
        return self.press_pass_users