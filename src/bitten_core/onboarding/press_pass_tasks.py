"""
BITTEN Press Pass Background Tasks

Handles scheduled tasks for Press Pass users including
nightly XP resets and expiry checks.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from .press_pass_manager import PressPassManager

logger = logging.getLogger(__name__)

class PressPassTaskManager:
    """Manages background tasks for Press Pass functionality"""
    
    def __init__(self, press_pass_manager: PressPassManager):
        self.press_pass_manager = press_pass_manager
        self.running_tasks = []
        
    async def start_background_tasks(self):
        """Start all Press Pass background tasks"""
        try:
            # Start nightly reset task
            reset_task = asyncio.create_task(
                self.press_pass_manager.schedule_nightly_resets()
            )
            self.running_tasks.append(reset_task)
            
            # Start expiry check task
            expiry_task = asyncio.create_task(
                self.check_expiring_passes()
            )
            self.running_tasks.append(expiry_task)
            
            logger.info("Press Pass background tasks started")
            
        except Exception as e:
            logger.error(f"Error starting background tasks: {e}")
    
    async def stop_background_tasks(self):
        """Stop all background tasks gracefully"""
        for task in self.running_tasks:
            task.cancel()
        
        await asyncio.gather(*self.running_tasks, return_exceptions=True)
        self.running_tasks.clear()
        logger.info("Press Pass background tasks stopped")
    
    async def check_expiring_passes(self):
        """Check for expiring Press Passes and send reminders"""
        while True:
            try:
                # Run check every hour
                await self._check_all_press_passes()
                await asyncio.sleep(3600)  # 1 hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in expiry check task: {e}")
                await asyncio.sleep(3600)
    
    async def _check_all_press_passes(self):
        """Check all active Press Passes for expiry"""
        try:
            # TODO: In production, query database for all Press Pass users
            # For now, this is a placeholder
            logger.info("Checking Press Pass expiry status")
            
            # Example implementation:
            # users = await get_all_press_pass_users()
            # for user in users:
            #     expiry_check = await self.press_pass_manager.check_press_pass_expiry(
            #         user.id, user.press_pass_expiry
            #     )
            #     if not expiry_check['expired']:
            #         days_remaining = expiry_check['remaining_time']['days']
            #         if days_remaining in [3, 1, 0]:
            #             await self.press_pass_manager.send_expiry_reminder(
            #                 user.id, days_remaining
            #             )
            
        except Exception as e:
            logger.error(f"Error checking Press Passes: {e}")
    
    async def manually_reset_user_xp(self, user_id: str):
        """Manually reset XP for a specific Press Pass user"""
        try:
            result = await self.press_pass_manager.reset_daily_xp(user_id)
            if result['success']:
                logger.info(f"Manually reset XP for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error manually resetting XP for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}

# Singleton instance for the task manager
_task_manager = None

def get_press_pass_task_manager(press_pass_manager: PressPassManager) -> PressPassTaskManager:
    """Get or create the singleton task manager instance"""
    global _task_manager
    if _task_manager is None:
        _task_manager = PressPassTaskManager(press_pass_manager)
    return _task_manager