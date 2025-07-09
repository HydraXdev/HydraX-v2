"""
🎖️ Weekend Safety Briefing Scheduler

Runs every Friday at 1200 UTC (noon) to brief all operators before weekend liberty
"""

import asyncio
import schedule
import time
from datetime import datetime, timezone
import logging
from typing import List, Dict

from .weekend_warning_system import WeekendSafetyBriefing, send_weekend_warnings
from .telegram_router import TelegramRouter
from .user_profile import UserProfileManager

logger = logging.getLogger(__name__)

class WeekendBriefingScheduler:
    """
    Handles scheduling and execution of mandatory weekend safety briefings
    """
    
    def __init__(self, telegram_router: TelegramRouter, profile_manager: UserProfileManager):
        self.telegram_router = telegram_router
        self.profile_manager = profile_manager
        self.briefing_system = WeekendSafetyBriefing()
        self.is_running = False
        
    async def execute_weekend_briefing(self):
        """
        Execute the weekend safety briefing for all active users
        """
        logger.info("🎖️ WEEKEND SAFETY BRIEFING INITIATED")
        
        try:
            # Get all active users
            active_users = await self.profile_manager.get_active_users()
            logger.info(f"Found {len(active_users)} operators for briefing")
            
            briefed_count = 0
            with_positions = 0
            
            for user in active_users:
                try:
                    # Get user's current positions
                    positions = await self.telegram_router.mt5_bridge.get_open_positions(
                        user['user_id']
                    )
                    
                    if positions:
                        with_positions += 1
                    
                    # Generate appropriate briefing
                    briefing_message = self.briefing_system.get_weekend_warning_message(
                        user['tier'],
                        len(positions)
                    )
                    
                    # Add user's weekend performance stats
                    if user.get('weekend_stats'):
                        briefing_message += self.briefing_system.get_weekend_stats_summary(
                            user['weekend_stats']
                        )
                    
                    # Add signature
                    briefing_message += (
                        "\n\n"
                        "────────────────────\n"
                        "**BRIEFING COMPLETE**\n"
                        f"Time: {datetime.now(timezone.utc).strftime('%H:%M UTC')}\n"
                        "Authority: OVERWATCH\n"
                        "\n"
                        "_This briefing is mandatory. "
                        "Your acknowledgment is assumed._"
                    )
                    
                    # Send the briefing
                    await self.telegram_router.send_message(
                        chat_id=user['chat_id'],
                        text=briefing_message,
                        parse_mode='Markdown'
                    )
                    
                    briefed_count += 1
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Failed to brief user {user['user_id']}: {e}")
            
            # Log completion
            logger.info(
                f"🎖️ WEEKEND BRIEFING COMPLETE: "
                f"{briefed_count}/{len(active_users)} operators briefed. "
                f"{with_positions} had open positions."
            )
            
            # Send admin summary
            await self._send_admin_summary(briefed_count, with_positions, len(active_users))
            
        except Exception as e:
            logger.error(f"Weekend briefing failed: {e}")
    
    async def _send_admin_summary(self, briefed: int, with_positions: int, total: int):
        """Send summary to admin after briefing"""
        admin_message = (
            "🎖️ **WEEKEND BRIEFING REPORT**\n"
            "────────────────────\n"
            f"**Operators Briefed:** {briefed}/{total}\n"
            f"**With Open Positions:** {with_positions}\n"
            f"**Clean (No Positions):** {briefed - with_positions}\n"
            f"\n"
            f"**Briefing Time:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"\n"
            "_All operators have been advised of weekend risks._"
        )
        
        # Send to admin
        await self.telegram_router.send_admin_message(admin_message)
    
    def schedule_briefings(self):
        """
        Schedule weekly briefings for Friday noon UTC
        """
        # Schedule for every Friday at 12:00 UTC
        schedule.every().friday.at("12:00").do(
            lambda: asyncio.create_task(self.execute_weekend_briefing())
        )
        
        logger.info("📅 Weekend safety briefings scheduled for Fridays at 1200 UTC")
    
    async def run_scheduler(self):
        """
        Run the scheduler in the background
        """
        self.is_running = True
        self.schedule_briefings()
        
        while self.is_running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        logger.info("🛑 Weekend briefing scheduler stopped")


# Integration with main bot
async def setup_weekend_briefings(telegram_router: TelegramRouter, profile_manager: UserProfileManager):
    """
    Set up weekend briefing system
    Called from main bot initialization
    """
    scheduler = WeekendBriefingScheduler(telegram_router, profile_manager)
    
    # Start scheduler in background
    asyncio.create_task(scheduler.run_scheduler())
    
    logger.info("✅ Weekend safety briefing system initialized")
    
    return scheduler


# Manual trigger for testing
async def trigger_test_briefing(telegram_router: TelegramRouter, profile_manager: UserProfileManager):
    """
    Manually trigger a briefing for testing
    Can be called from admin command
    """
    scheduler = WeekendBriefingScheduler(telegram_router, profile_manager)
    await scheduler.execute_weekend_briefing()