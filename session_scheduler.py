#!/usr/bin/env python3
"""
🕒 BITTEN Session Scheduler
Automatically updates configuration based on trading sessions
"""

import time
import signal
import sys
import subprocess
import logging
from datetime import datetime, timezone
from session_based_pair_manager import SessionBasedPairManager

class SessionScheduler:
    """
    Automatic session-based configuration updates for engine
    
    Features:
    - Monitors UTC time for session changes
    - Updates config automatically 
    - Restarts engine with new configuration
    - Logs all session transitions
    """
    
    def __init__(self):
        self.manager = SessionBasedPairManager()
        self.current_session = None
        self.running = True
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - SESSION_SCHEDULER - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
        sys.exit(0)
    
    def _restart_apex_engine(self):
        """Restart engine with new configuration"""
        try:
            # Kill existing process
            try:
                with open('.apex_engine.pid', 'r') as f:
                    pid = int(f.read().strip())
                subprocess.run(['kill', str(pid)], check=False)
                time.sleep(3)  # Give time for cleanup
                self.logger.info(f"🔄 Stopped engine (PID: {pid})")
            except (FileNotFoundError, ValueError):
                self.logger.warning("⚠️ No existing PID found")
            
            # Start new process
            subprocess.Popen(['python3', 'apex_v5_lean.py'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            self.logger.info("🚀 Restarted engine with new session config")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to restart engine: {e}")
    
    def check_session_change(self):
        """Check if trading session has changed"""
        new_session = self.manager.get_current_session()
        
        if self.current_session is None or new_session.name != self.current_session.name:
            self.logger.info(f"🌍 Session change detected: {self.current_session.name if self.current_session else 'STARTUP'} → {new_session.name}")
            
            # Apply new session optimization
            self.manager.apply_session_optimization()
            
            # Restart engine
            self._restart_apex_engine()
            
            # Update current session
            self.current_session = new_session
            
            # Log session details
            session_info = self.manager.get_session_info()
            self.logger.info(f"✅ Applied {session_info['session_name']} session config:")
            self.logger.info(f"   📊 Pairs: {session_info['pair_count']} ({', '.join(session_info['pairs'][:3])}...)")
            self.logger.info(f"   🎯 TCS Threshold: {session_info['adjusted_threshold']}%")
            self.logger.info(f"   🚀 Boost: {session_info['boost_multiplier']}x")
            
            return True
        
        return False
    
    def run(self):
        """Main scheduler loop"""
        self.logger.info("🕒 Session Scheduler started")
        self.logger.info("📍 Monitoring for trading session changes...")
        
        # Initial session setup
        self.check_session_change()
        
        while self.running:
            try:
                # Check for session changes every 5 minutes
                if self.check_session_change():
                    self.logger.info("⏰ Next check in 5 minutes...")
                
                # Sleep for 5 minutes
                time.sleep(300)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Scheduler stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Scheduler error: {e}")
                time.sleep(60)  # Wait 1 minute before retry

def run_session_scheduler():
    """Run the session scheduler"""
    scheduler = SessionScheduler()
    scheduler.run()

if __name__ == "__main__":
    run_session_scheduler()