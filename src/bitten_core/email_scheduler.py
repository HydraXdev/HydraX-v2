#!/usr/bin/env python3
"""
Email Scheduler for BITTEN Press Pass Campaigns
Runs as a background task to process scheduled emails
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime, timedelta
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.bitten_core.press_pass_email_automation import get_email_automation
from src.bitten_core.database.connection import get_db_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailScheduler:
    """Manages scheduled email tasks"""
    
    def __init__(self):
        self.automation = get_email_automation()
        self.running = False
    
    def process_email_queue(self):
        """Process emails in the queue"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get pending emails scheduled for now or earlier
            cursor.execute("""
                SELECT id, user_id, email_address, template, subject, template_data
                FROM email_queue
                WHERE status = 'pending'
                AND scheduled_for <= datetime('now')
                AND attempts < 3
                ORDER BY priority ASC, scheduled_for ASC
                LIMIT 50
            """)
            
            emails = cursor.fetchall()
            
            for email in emails:
                email_id, user_id, email_address, template, subject, template_data = email
                
                # Update attempt count
                cursor.execute("""
                    UPDATE email_queue 
                    SET attempts = attempts + 1, last_attempt_at = datetime('now')
                    WHERE id = ?
                """, (email_id,))
                
                # Send email
                try:
                    import json
                    data = json.loads(template_data) if template_data else {}
                    
                    success = self.automation.email_service.send_template_email(
                        to_email=email_address,
                        template_name=template,
                        template_data=data,
                        subject=subject
                    )
                    
                    if success:
                        cursor.execute("""
                            UPDATE email_queue 
                            SET status = 'sent', sent_at = datetime('now')
                            WHERE id = ?
                        """, (email_id,))
                        logger.info(f"Email sent: {template} to {email_address}")
                    else:
                        cursor.execute("""
                            UPDATE email_queue 
                            SET status = 'failed', error_message = 'Send failed'
                            WHERE id = ?
                        """, (email_id,))
                        
                except Exception as e:
                    cursor.execute("""
                        UPDATE email_queue 
                        SET error_message = ?
                        WHERE id = ?
                    """, (str(e), email_id))
                    logger.error(f"Error sending email {email_id}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            if emails:
                logger.info(f"Processed {len(emails)} emails from queue")
                
        except Exception as e:
            logger.error(f"Error processing email queue: {str(e)}")
    
    def check_press_pass_campaigns(self):
        """Check and send Press Pass campaign emails"""
        try:
            logger.info("Checking Press Pass campaigns...")
            
            # Process scheduled emails
            results = self.automation.process_scheduled_emails()
            
            if results['sent'] > 0 or results['failed'] > 0:
                logger.info(f"Campaign emails: {results['sent']} sent, {results['failed']} failed")
            
            # Check for expiring Press Passes
            self._check_expiring_passes()
            
        except Exception as e:
            logger.error(f"Error checking campaigns: {str(e)}")
    
    def _check_expiring_passes(self):
        """Check for Press Passes expiring soon"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get Press Passes expiring in 5, 2, or 1 days
            for days in [5, 2, 1]:
                expiry_date = datetime.now() + timedelta(days=days)
                
                cursor.execute("""
                    SELECT pp.user_id, u.email, u.username
                    FROM press_passes pp
                    JOIN users u ON pp.user_id = u.id
                    WHERE pp.status = 'active'
                    AND u.email IS NOT NULL
                    AND DATE(pp.activated_at, '+30 days') = DATE(?)
                    AND NOT EXISTS (
                        SELECT 1 FROM email_log 
                        WHERE user_id = pp.user_id 
                        AND template LIKE '%day' || ? || '%'
                        AND sent_at > datetime('now', '-24 hours')
                    )
                """, (expiry_date.date(), 30 - days))
                
                users = cursor.fetchall()
                
                for user_id, email, username in users:
                    success = self.automation.send_expiry_reminder(user_id, days)
                    if success:
                        logger.info(f"Sent {days}-day expiry reminder to user {user_id}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error checking expiring passes: {str(e)}")
    
    def update_campaign_stats(self):
        """Update email campaign statistics"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Update daily stats
            cursor.execute("""
                INSERT OR REPLACE INTO email_campaign_stats 
                (campaign, date, total_sent, total_opened, total_clicked, 
                 total_bounced, total_unsubscribed, unique_opens, unique_clicks)
                SELECT 
                    campaign,
                    DATE(sent_at) as date,
                    COUNT(*) as total_sent,
                    SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) as total_opened,
                    SUM(CASE WHEN clicked_at IS NOT NULL THEN 1 ELSE 0 END) as total_clicked,
                    SUM(CASE WHEN bounced = 1 THEN 1 ELSE 0 END) as total_bounced,
                    SUM(CASE WHEN unsubscribed = 1 THEN 1 ELSE 0 END) as total_unsubscribed,
                    COUNT(DISTINCT CASE WHEN opened_at IS NOT NULL THEN user_id END) as unique_opens,
                    COUNT(DISTINCT CASE WHEN clicked_at IS NOT NULL THEN user_id END) as unique_clicks
                FROM email_log
                WHERE DATE(sent_at) >= DATE('now', '-7 days')
                GROUP BY campaign, DATE(sent_at)
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("Updated email campaign statistics")
            
        except Exception as e:
            logger.error(f"Error updating campaign stats: {str(e)}")
    
    def cleanup_old_data(self):
        """Clean up old email data"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Delete old queue items
            cursor.execute("""
                DELETE FROM email_queue 
                WHERE status IN ('sent', 'failed') 
                AND created_at < datetime('now', '-30 days')
            """)
            
            # Archive old email logs
            cursor.execute("""
                DELETE FROM email_log 
                WHERE sent_at < datetime('now', '-90 days')
            """)
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old email records")
                
        except Exception as e:
            logger.error(f"Error cleaning up data: {str(e)}")
    
    def start(self):
        """Start the email scheduler"""
        logger.info("Starting email scheduler...")
        
        # Schedule tasks
        schedule.every(1).minutes.do(self.process_email_queue)
        schedule.every(30).minutes.do(self.check_press_pass_campaigns)
        schedule.every(1).hours.do(self.update_campaign_stats)
        schedule.every(1).days.at("03:00").do(self.cleanup_old_data)
        
        # Run initial checks
        self.process_email_queue()
        self.check_press_pass_campaigns()
        
        self.running = True
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except KeyboardInterrupt:
                logger.info("Stopping email scheduler...")
                self.running = False
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying


def main():
    """Main entry point"""
    scheduler = EmailScheduler()
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Email scheduler stopped")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()