"""
Background tasks for trial and subscription management
"""

import asyncio
import logging
from datetime import datetime

from .trial_manager import get_trial_manager
from .subscription_manager import get_subscription_manager

logger = logging.getLogger(__name__)

async def run_trial_maintenance():
    """Run periodic trial maintenance tasks"""
    
    trial_manager = get_trial_manager()
    subscription_manager = get_subscription_manager()
    
    while True:
        try:
            # Check and send trial reminders (every hour)
            logger.info("Running trial maintenance tasks...")
            
            # Send day 14 reminders
            reminder_count = await trial_manager.send_trial_reminders()
            if reminder_count > 0:
                logger.info(f"Sent {reminder_count} trial reminders")
            
            # Handle expired trials
            expired_count = await trial_manager.handle_trial_expiry()
            if expired_count > 0:
                logger.info(f"Processed {expired_count} expired trials")
            
            # Check abandoned accounts (once per day)
            if datetime.now().hour == 3:  # Run at 3 AM
                abandoned_count = await trial_manager.check_abandoned_accounts()
                if abandoned_count > 0:
                    logger.info(f"Reset {abandoned_count} abandoned accounts")
            
            # Sleep for 1 hour
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"Error in trial maintenance: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error

async def run_subscription_maintenance():
    """Run periodic subscription maintenance tasks"""
    
    subscription_manager = get_subscription_manager()
    
    while True:
        try:
            logger.info("Running subscription maintenance tasks...")
            
            # Check expiring subscriptions
            expiring = await subscription_manager.check_expiring_subscriptions()
            if expiring:
                logger.info(f"Found {len(expiring)} expiring subscriptions")
            
            # Process expired subscriptions
            processed = await subscription_manager.process_expired_subscriptions()
            if processed > 0:
                logger.info(f"Processed {processed} expired subscriptions")
            
            # Retry failed payments
            retried = await subscription_manager.retry_failed_payments()
            if retried > 0:
                logger.info(f"Retried {retried} failed payments")
            
            # Sleep for 6 hours
            await asyncio.sleep(21600)
            
        except Exception as e:
            logger.error(f"Error in subscription maintenance: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error

def start_background_tasks():
    """Start all background tasks"""
    
    loop = asyncio.get_event_loop()
    
    # Create tasks
    trial_task = loop.create_task(run_trial_maintenance())
    subscription_task = loop.create_task(run_subscription_maintenance())
    
    logger.info("Started trial and subscription background tasks")
    
    return [trial_task, subscription_task]