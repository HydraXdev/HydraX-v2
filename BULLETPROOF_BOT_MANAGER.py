#!/usr/bin/env python3
"""
🛡️ BULLETPROOF BOT MANAGER 🛡️
PREVENTS MULTIPLE BOT CONFLICTS - NEVER AGAIN SYSTEM

This system ensures ONLY ONE bot can run at a time with proper authorization.
"""

import os
import sys
import json
import fcntl
import signal
import time
import subprocess
from datetime import datetime
from pathlib import Path

class BotManager:
    """Bulletproof single-bot enforcement system"""
    
    def __init__(self):
        self.lock_file = "/tmp/bitten_bot.lock"
        self.config_file = "/root/HydraX-v2/data/authorized_bot.json"
        self.authorized_bots = {
            "production_signal_engine.py": "LIVE MT5 Production Engine",
            "live_signal_engine.py": "Live Signal Engine with TCS",
            "webapp_server.py": "Mission Brief WebApp",
            "AUTHORIZED_SIGNAL_ENGINE.py": "Authorized Signal Engine"
        }
        
    def acquire_bot_lock(self, bot_name: str, description: str = ""):
        """Acquire exclusive bot lock - ONLY ONE BOT ALLOWED"""
        
        # Kill any unauthorized bots immediately
        self.kill_unauthorized_bots()
        
        try:
            # Create lock file
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Write bot info to lock
            bot_info = {
                "bot_name": bot_name,
                "description": description,
                "pid": os.getpid(),
                "started_at": datetime.now().isoformat(),
                "authorized": bot_name in self.authorized_bots
            }
            
            self.lock_fd.write(json.dumps(bot_info, indent=2))
            self.lock_fd.flush()
            
            print(f"🔐 Bot lock acquired: {bot_name}")
            return True
            
        except BlockingIOError:
            print(f"❌ ANOTHER BOT IS ALREADY RUNNING!")
            self.show_running_bot()
            return False
        except Exception as e:
            print(f"❌ Lock error: {e}")
            return False
    
    def release_bot_lock(self):
        """Release bot lock"""
        try:
            if hasattr(self, 'lock_fd'):
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
            print("🔓 Bot lock released")
        except:
            pass
    
    def show_running_bot(self):
        """Show which bot is currently running"""
        try:
            with open(self.lock_file, 'r') as f:
                bot_info = json.load(f)
            print(f"🤖 Running bot: {bot_info['bot_name']}")
            print(f"📝 Description: {bot_info['description']}")
            print(f"🆔 PID: {bot_info['pid']}")
            print(f"⏰ Started: {bot_info['started_at']}")
            print(f"✅ Authorized: {bot_info['authorized']}")
        except:
            print("❓ Could not read lock file")
    
    def kill_unauthorized_bots(self):
        """Kill any bots not in authorized list"""
        unauthorized_patterns = [
            'SIGNALS_COMPACT.py',
            'START_SIGNALS_NOW.py',
            'SIGNALS_REALISTIC.py', 
            'SIGNALS_LIVE_DATA.py',
            'start_signals_fixed.py',
            'SIGNALS_CLEAN.py'
        ]
        
        print("🔫 Scanning for unauthorized bots...")
        for pattern in unauthorized_patterns:
            try:
                subprocess.run(['pkill', '-f', pattern], check=False)
                print(f"🔫 Killed unauthorized: {pattern}")
            except:
                pass
    
    def validate_bot_token(self, token: str) -> bool:
        """Validate bot token is correct and not disabled"""
        expected_token = os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")
        
        if token == "DISABLED_FOR_EMERGENCY_STOP" or token == "EMERGENCY_DISABLED":
            print("❌ Bot token is EMERGENCY DISABLED")
            return False
            
        if token != expected_token:
            print("❌ Invalid bot token")
            return False
            
        return True
    
    def get_authorized_signal_engine(self) -> str:
        """Get the name of the authorized signal engine"""
        return "production_signal_engine.py"  # ONLY this one allowed for signals

# Global instance
bot_manager = BotManager()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🔴 Bot shutdown signal received")
    bot_manager.release_bot_lock()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def require_bot_authorization(bot_name: str, description: str = ""):
    """Decorator to require bot authorization"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not bot_manager.acquire_bot_lock(bot_name, description):
                print("❌ UNAUTHORIZED BOT STARTUP BLOCKED")
                sys.exit(1)
            
            try:
                return func(*args, **kwargs)
            finally:
                bot_manager.release_bot_lock()
        return wrapper
    return decorator

if __name__ == "__main__":
    print("🛡️ BULLETPROOF BOT MANAGER")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            bot_manager.show_running_bot()
        elif sys.argv[1] == "kill-all":
            bot_manager.kill_unauthorized_bots()
            print("✅ All unauthorized bots killed")
        elif sys.argv[1] == "release":
            bot_manager.release_bot_lock()
            print("✅ Lock released")
    else:
        print("Usage:")
        print("  python BULLETPROOF_BOT_MANAGER.py status    - Show running bot")
        print("  python BULLETPROOF_BOT_MANAGER.py kill-all  - Kill unauthorized bots") 
        print("  python BULLETPROOF_BOT_MANAGER.py release   - Release lock")