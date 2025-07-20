#!/usr/bin/env python3
"""
Press Pass Daily Maintenance Script
Handles expiry checking, account recycling, and system cleanup
"""

import os
import sys
import time
import schedule
import logging
from datetime import datetime

# Add paths for imports
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

from src.bitten_core.presspass_rotation_system import PressPassRotationSystem
from src.bitten_core.mt5_terminal_manager import MT5TerminalManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/presspass_maintenance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PressPassMaintenance')

def run_daily_maintenance():
    """
    Run the daily Press Pass maintenance tasks
    """
    logger.info("Starting Press Pass daily maintenance...")
    
    try:
        # Initialize systems
        rotation_system = PressPassRotationSystem()
        terminal_manager = MT5TerminalManager()
        
        # 1. Check and expire accounts
        logger.info("Checking for expired Press Pass accounts...")
        expiry_result = rotation_system.check_and_expire_accounts()
        
        if expiry_result["success"]:
            logger.info(f"Expiry check completed:")
            logger.info(f"  - Expired accounts: {expiry_result['expired_count']}")
            logger.info(f"  - Available accounts: {expiry_result['available_count']}")
            logger.info(f"  - Assigned accounts: {expiry_result['assigned_count']}")
            logger.info(f"  - Total accounts: {expiry_result['total_accounts']}")
            
            # Log recycled accounts
            for recycled in expiry_result.get("recycled_accounts", []):
                logger.info(f"  - Recycled account {recycled['login']} from user {recycled['user_id']}")
        else:
            logger.error(f"Expiry check failed: {expiry_result.get('error', 'Unknown error')}")
        
        # 2. Clean up orphaned processes
        logger.info("Cleaning up orphaned processes...")
        cleanup_result = terminal_manager.cleanup_orphaned_processes()
        
        if cleanup_result["success"]:
            logger.info(f"Process cleanup completed: {cleanup_result['cleaned_count']} orphaned processes removed")
        else:
            logger.error(f"Process cleanup failed: {cleanup_result.get('error', 'Unknown error')}")
        
        # 3. Generate maintenance report
        vault = rotation_system.load_vault()
        
        # Calculate statistics
        total_accounts = len(vault)
        available_accounts = sum(1 for acc in vault if acc.get("status") == "available")
        assigned_accounts = sum(1 for acc in vault if acc.get("status") == "assigned")
        
        # Calculate utilization rate
        utilization_rate = (assigned_accounts / total_accounts * 100) if total_accounts > 0 else 0
        
        # Check for low availability
        availability_warning = ""
        if available_accounts < 5:
            availability_warning = "⚠️ WARNING: Low account availability! Consider adding more demo accounts."
        elif available_accounts < 10:
            availability_warning = "⚠️ NOTICE: Account availability getting low."
        
        maintenance_report = f"""
=== PRESS PASS MAINTENANCE REPORT ===
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Account Statistics:
  Total Accounts: {total_accounts}
  Available: {available_accounts}
  Assigned: {assigned_accounts}
  Utilization Rate: {utilization_rate:.1f}%

Maintenance Actions:
  Expired Accounts Recycled: {expiry_result.get('expired_count', 0)}
  Orphaned Processes Cleaned: {cleanup_result.get('cleaned_count', 0)}

{availability_warning}

System Status: ✅ OPERATIONAL
==========================================
"""
        
        logger.info(maintenance_report)
        
        # Save maintenance report
        report_file = f"/root/HydraX-v2/logs/maintenance_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_file, 'w') as f:
            f.write(maintenance_report)
        
        logger.info("Daily maintenance completed successfully")
        
    except Exception as e:
        logger.error(f"Daily maintenance failed: {e}")
        raise

def run_hourly_health_check():
    """
    Run hourly health checks
    """
    logger.info("Running hourly Press Pass health check...")
    
    try:
        rotation_system = PressPassRotationSystem()
        
        # Quick expiry check (for accounts that might have expired since last daily run)
        expiry_result = rotation_system.check_and_expire_accounts()
        
        if expiry_result["success"] and expiry_result["expired_count"] > 0:
            logger.info(f"Hourly health check: Recycled {expiry_result['expired_count']} expired accounts")
        
        logger.info("Hourly health check completed")
        
    except Exception as e:
        logger.error(f"Hourly health check failed: {e}")

def main():
    """
    Main maintenance scheduler
    """
    logger.info("Press Pass Daily Maintenance Scheduler starting...")
    
    # Schedule daily maintenance at 3:00 AM
    schedule.every().day.at("03:00").do(run_daily_maintenance)
    
    # Schedule hourly health checks
    schedule.every().hour.do(run_hourly_health_check)
    
    # Run initial health check
    run_hourly_health_check()
    
    logger.info("Scheduler configured:")
    logger.info("  - Daily maintenance: 3:00 AM")
    logger.info("  - Hourly health checks: Every hour")
    logger.info("  - Running continuously...")
    
    # Keep running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Maintenance scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(300)  # Sleep 5 minutes on error

if __name__ == "__main__":
    # Ensure log directory exists
    os.makedirs("/root/HydraX-v2/logs", exist_ok=True)
    
    # Run maintenance
    if len(sys.argv) > 1:
        if sys.argv[1] == "daily":
            run_daily_maintenance()
        elif sys.argv[1] == "hourly":
            run_hourly_health_check()
        else:
            print("Usage: python3 presspass_daily_maintenance.py [daily|hourly]")
    else:
        main()