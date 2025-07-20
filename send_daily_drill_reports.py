#!/usr/bin/env python3
"""
Automated Daily Drill Report Scheduler
Sends daily drill reports at 6 PM to all users with daily stats
Handles errors gracefully and logs all activity
"""

import sys
import os
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import traceback
import json

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Configure logging
log_file = project_root / "logs" / "drill_reports_scheduler.log"
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class DrillReportScheduler:
    """Automated drill report scheduler system"""
    
    def __init__(self):
        self.project_root = project_root
        self.drill_system = None
        self.telegram_bot = None
        self.reports_sent = 0
        self.errors_encountered = 0
        
    def initialize_systems(self):
        """Initialize drill report system and telegram bot"""
        try:
            logger.info("🚀 Initializing Daily Drill Report Scheduler...")
            
            # Import drill report system
            from src.bitten_core.daily_drill_report import DailyDrillReportSystem
            self.drill_system = DailyDrillReportSystem()
            logger.info("✅ Drill report system initialized")
            
            # Import and initialize telegram bot
            import telebot
            
            # Use BITTEN production bot token (from CLAUDE.md)
            BOT_TOKEN = '8103700393:AAEK3RjTGHHYyy_X1Uc9FUuUoRcLuzYZe4k'
            
            self.telegram_bot = telebot.TeleBot(BOT_TOKEN)
            logger.info("✅ Telegram bot initialized")
            
            return True
            
        except ImportError as e:
            logger.error(f"❌ Import error: {e}")
            logger.error("Make sure all required modules are installed and accessible")
            return False
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def get_users_for_reports(self):
        """Get list of users who should receive daily reports"""
        try:
            # Connect to drill reports database
            db_path = self.project_root / "data" / "drill_reports.db"
            
            if not db_path.exists():
                logger.warning("⚠️ Drill reports database not found")
                return []
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get users who have daily stats and haven't received reports yet
            cursor.execute('''
                SELECT DISTINCT user_id FROM daily_trading_stats 
                WHERE date = ? AND report_sent = 0
            ''', (today,))
            
            users_with_stats = [row[0] for row in cursor.fetchall()]
            
            # Also check for users who have preferences set but no stats today (for no-action reports)
            cursor.execute('''
                SELECT user_id FROM drill_preferences 
                WHERE report_enabled = 1
            ''')
            
            all_users = set([row[0] for row in cursor.fetchall()])
            conn.close()
            
            # Combine users with stats and users with preferences
            final_users = list(set(users_with_stats) | all_users)
            
            logger.info(f"📊 Found {len(final_users)} users for drill reports")
            logger.info(f"   - {len(users_with_stats)} with trading stats today")
            logger.info(f"   - {len(all_users)} with report preferences enabled")
            
            return final_users
            
        except Exception as e:
            logger.error(f"❌ Error getting users for reports: {e}")
            return []
    
    def send_drill_report_to_user(self, user_id: str):
        """Send drill report to a specific user"""
        try:
            # Generate drill report
            drill_message = self.drill_system.generate_drill_report(user_id)
            
            if not drill_message:
                logger.warning(f"⚠️ No drill message generated for user {user_id}")
                return False
            
            # Format for Telegram
            telegram_report = self.drill_system.format_telegram_report(drill_message, user_id)
            
            # Send via Telegram bot (telebot is synchronous)
            try:
                self.telegram_bot.send_message(
                    chat_id=user_id, 
                    text=telegram_report,
                    parse_mode='HTML'
                )
                success = True
            except Exception as e:
                logger.error(f"❌ Telegram send error for user {user_id}: {e}")
                success = False
            
            if success:
                # Mark as sent in database
                self._mark_report_sent(user_id)
                logger.info(f"✅ Drill report sent to user {user_id}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending drill report to {user_id}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _mark_report_sent(self, user_id: str):
        """Mark drill report as sent for user"""
        try:
            db_path = self.project_root / "data" / "drill_reports.db"
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute('''
                UPDATE daily_trading_stats 
                SET report_sent = 1 
                WHERE user_id = ? AND date = ?
            ''', (user_id, today))
            
            # Also record in drill report history
            cursor.execute('''
                INSERT INTO drill_report_history 
                (user_id, date, report_content, tone, sent_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, today, "Scheduled drill report", "auto", datetime.now()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error marking report sent for {user_id}: {e}")
    
    def run_daily_reports(self):
        """Main function to run daily drill reports"""
        start_time = datetime.now()
        logger.info(f"🪖 Starting Daily Drill Report Delivery - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Initialize systems
            if not self.initialize_systems():
                logger.error("❌ System initialization failed")
                return False
            
            # Get users who need reports
            users = self.get_users_for_reports()
            
            if not users:
                logger.info("ℹ️ No users found for drill reports today")
                return True
            
            # Send reports to each user
            for user_id in users:
                try:
                    success = self.send_drill_report_to_user(user_id)
                    if success:
                        self.reports_sent += 1
                    else:
                        self.errors_encountered += 1
                        
                except Exception as e:
                    logger.error(f"❌ Unexpected error for user {user_id}: {e}")
                    self.errors_encountered += 1
            
            # Log summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"📊 Daily Drill Report Summary:")
            logger.info(f"   ✅ Reports sent: {self.reports_sent}")
            logger.info(f"   ❌ Errors: {self.errors_encountered}")
            logger.info(f"   ⏱️ Duration: {duration:.2f} seconds")
            logger.info(f"   📅 Date: {start_time.strftime('%Y-%m-%d')}")
            
            # Write summary to file for monitoring
            self._write_summary_file(start_time, end_time, duration)
            
            return self.errors_encountered == 0
            
        except Exception as e:
            logger.error(f"❌ Critical error in drill report scheduler: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _write_summary_file(self, start_time, end_time, duration):
        """Write execution summary to file for monitoring"""
        try:
            summary_file = self.project_root / "logs" / "drill_reports_summary.json"
            
            summary = {
                "date": start_time.strftime('%Y-%m-%d'),
                "execution_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
                "duration_seconds": duration,
                "reports_sent": self.reports_sent,
                "errors_encountered": self.errors_encountered,
                "success": self.errors_encountered == 0,
                "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Load existing data if file exists
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    try:
                        data = json.load(f)
                        if not isinstance(data, list):
                            data = []
                    except:
                        data = []
            else:
                data = []
            
            # Add today's summary
            data.append(summary)
            
            # Keep only last 30 days
            data = data[-30:]
            
            with open(summary_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Error writing summary file: {e}")


def main():
    """Main entry point for scheduled execution"""
    
    print("🪖 BITTEN Daily Drill Report Scheduler")
    print(f"⏰ Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    scheduler = DrillReportScheduler()
    success = scheduler.run_daily_reports()
    
    if success:
        print(f"✅ Daily drill reports completed successfully!")
        print(f"📊 Reports sent: {scheduler.reports_sent}")
        sys.exit(0)
    else:
        print(f"❌ Daily drill reports failed!")
        print(f"📊 Reports sent: {scheduler.reports_sent}")
        print(f"❌ Errors: {scheduler.errors_encountered}")
        sys.exit(1)


# Health check function
def health_check():
    """Health check for monitoring systems"""
    try:
        scheduler = DrillReportScheduler()
        
        # Check if drill report system can be imported
        from src.bitten_core.daily_drill_report import DailyDrillReportSystem
        drill_system = DailyDrillReportSystem()
        
        # Check if database exists and is accessible
        db_path = scheduler.project_root / "data" / "drill_reports.db"
        if not db_path.exists():
            return False, "Drill reports database not found"
            
        # Test database connection
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM daily_trading_stats")
        count = cursor.fetchone()[0]
        conn.close()
        
        return True, f"System healthy - {count} trading records in database"
        
    except Exception as e:
        return False, f"Health check failed: {e}"


if __name__ == "__main__":
    # Check for health check argument
    if len(sys.argv) > 1 and sys.argv[1] == "health":
        healthy, message = health_check()
        print(f"Health Check: {'✅ PASS' if healthy else '❌ FAIL'}")
        print(f"Message: {message}")
        sys.exit(0 if healthy else 1)
    
    # Normal execution
    main()