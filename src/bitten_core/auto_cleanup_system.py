#!/usr/bin/env python3
"""
🧹 AUTO CLEANUP SYSTEM - Telegram Messages & Mission Files
Automatically deletes expired content to keep system clean and save storage
"""

import os
import json
import time
import logging
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import glob
import threading

logger = logging.getLogger('AutoCleanup')

class AutoCleanupSystem:
    """
    Manages automatic deletion of:
    1. Telegram messages after 8 hours
    2. Mission files after expiry
    3. Old signal files
    """
    
    def __init__(self):
        self.cleanup_interval = 300  # Check every 5 minutes
        self.message_ttl = 8 * 3600  # 8 hours for Telegram messages
        self.mission_ttl = 8 * 3600  # 8 hours for mission files
        self.signal_ttl = 24 * 3600  # 24 hours for shared signals
        
        # Track sent messages for deletion
        self.message_tracker_file = "/root/HydraX-v2/data/telegram_messages.jsonl"
        self.missions_dir = "/root/HydraX-v2/missions/"
        self.signals_dir = "/root/HydraX-v2/signals/shared/"
        
        # Telegram bot tokens
        self.bot_tokens = {
            'production': '7854827710:AAE6m_sNuMk2X6Z3yf2mYO6-6-Clqan-F2c',
            'athena': os.getenv("BOT_TOKEN")
        }
        
        # Start cleanup thread
        self.cleanup_thread = None
        self.running = False
    
    def track_telegram_message(self, bot_name: str, chat_id: str, message_id: int, signal_id: str):
        """
        Track a sent Telegram message for later deletion
        """
        message_data = {
            'bot': bot_name,
            'chat_id': chat_id,
            'message_id': message_id,
            'signal_id': signal_id,
            'sent_at': datetime.now().isoformat(),
            'delete_at': (datetime.now() + timedelta(seconds=self.message_ttl)).isoformat()
        }
        
        try:
            with open(self.message_tracker_file, 'a') as f:
                f.write(json.dumps(message_data) + '\n')
            logger.info(f"Tracked message {message_id} for deletion in 8 hours")
        except Exception as e:
            logger.error(f"Failed to track message: {e}")
    
    def delete_telegram_message(self, bot_name: str, chat_id: str, message_id: int) -> bool:
        """
        Delete a specific Telegram message
        """
        if bot_name not in self.bot_tokens:
            logger.error(f"Unknown bot: {bot_name}")
            return False
        
        token = self.bot_tokens[bot_name]
        url = f"https://api.telegram.org/bot{token}/deleteMessage"
        
        try:
            response = requests.post(url, json={
                'chat_id': chat_id,
                'message_id': message_id
            }, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"Deleted Telegram message {message_id} from chat {chat_id}")
                    return True
                else:
                    logger.warning(f"Failed to delete message: {result.get('description')}")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting Telegram message: {e}")
            return False
    
    def cleanup_expired_telegram_messages(self):
        """
        Delete all expired Telegram messages
        """
        if not os.path.exists(self.message_tracker_file):
            return
        
        current_time = datetime.now()
        active_messages = []
        deleted_count = 0
        
        try:
            with open(self.message_tracker_file, 'r') as f:
                for line in f:
                    try:
                        message_data = json.loads(line.strip())
                        delete_at = datetime.fromisoformat(message_data['delete_at'])
                        
                        if current_time >= delete_at:
                            # Delete the message
                            if self.delete_telegram_message(
                                message_data['bot'],
                                message_data['chat_id'],
                                message_data['message_id']
                            ):
                                deleted_count += 1
                                logger.info(f"Deleted expired message for signal {message_data['signal_id']}")
                            else:
                                # Keep if deletion failed (might retry later)
                                active_messages.append(line)
                        else:
                            # Keep active messages
                            active_messages.append(line)
                            
                    except Exception as e:
                        logger.error(f"Error processing message record: {e}")
                        continue
            
            # Rewrite file with only active messages
            with open(self.message_tracker_file, 'w') as f:
                f.writelines(active_messages)
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired Telegram messages")
                
        except Exception as e:
            logger.error(f"Error during Telegram cleanup: {e}")
    
    def cleanup_expired_mission_files(self):
        """
        Delete all expired mission files (8 hours old)
        """
        if not os.path.exists(self.missions_dir):
            return
        
        current_time = time.time()
        deleted_count = 0
        freed_space = 0
        
        try:
            # Find all mission files
            mission_files = glob.glob(os.path.join(self.missions_dir, "mission_*.json"))
            
            for mission_file in mission_files:
                try:
                    file_age = current_time - os.path.getctime(mission_file)
                    
                    if file_age > self.mission_ttl:
                        file_size = os.path.getsize(mission_file)
                        os.remove(mission_file)
                        deleted_count += 1
                        freed_space += file_size
                        logger.debug(f"Deleted expired mission: {os.path.basename(mission_file)}")
                        
                except Exception as e:
                    logger.error(f"Error deleting mission file {mission_file}: {e}")
                    continue
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired mission files, freed {freed_space/1024:.1f} KB")
                
        except Exception as e:
            logger.error(f"Error during mission file cleanup: {e}")
    
    def cleanup_old_signal_files(self):
        """
        Delete signal files older than 24 hours
        """
        if not os.path.exists(self.signals_dir):
            return
        
        current_time = time.time()
        deleted_count = 0
        
        try:
            signal_files = glob.glob(os.path.join(self.signals_dir, "*.json"))
            
            for signal_file in signal_files:
                try:
                    file_age = current_time - os.path.getctime(signal_file)
                    
                    if file_age > self.signal_ttl:
                        os.remove(signal_file)
                        deleted_count += 1
                        logger.debug(f"Deleted old signal: {os.path.basename(signal_file)}")
                        
                except Exception as e:
                    logger.error(f"Error deleting signal file {signal_file}: {e}")
                    continue
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old signal files")
                
        except Exception as e:
            logger.error(f"Error during signal file cleanup: {e}")
    
    def cleanup_loop(self):
        """
        Main cleanup loop that runs every 5 minutes
        """
        logger.info("Auto-cleanup system started")
        
        while self.running:
            try:
                # Run all cleanup tasks
                self.cleanup_expired_telegram_messages()
                self.cleanup_expired_mission_files()
                self.cleanup_old_signal_files()
                
                # Log system stats
                self.log_cleanup_stats()
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
            
            # Wait for next interval
            time.sleep(self.cleanup_interval)
    
    def log_cleanup_stats(self):
        """
        Log current storage usage stats
        """
        try:
            # Count files
            mission_count = len(glob.glob(os.path.join(self.missions_dir, "*.json")))
            signal_count = len(glob.glob(os.path.join(self.signals_dir, "*.json")))
            
            # Calculate size
            mission_size = sum(os.path.getsize(f) for f in glob.glob(os.path.join(self.missions_dir, "*.json")))
            signal_size = sum(os.path.getsize(f) for f in glob.glob(os.path.join(self.signals_dir, "*.json")))
            
            logger.info(f"Storage stats - Missions: {mission_count} files ({mission_size/1024:.1f}KB), "
                       f"Signals: {signal_count} files ({signal_size/1024:.1f}KB)")
            
        except Exception as e:
            logger.error(f"Error logging stats: {e}")
    
    def start(self):
        """
        Start the auto-cleanup system
        """
        if not self.running:
            self.running = True
            self.cleanup_thread = threading.Thread(target=self.cleanup_loop, daemon=True)
            self.cleanup_thread.start()
            logger.info("Auto-cleanup system started")
    
    def stop(self):
        """
        Stop the auto-cleanup system
        """
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=10)
        logger.info("Auto-cleanup system stopped")

# Global instance
cleanup_system = AutoCleanupSystem()

def start_cleanup_system():
    """Start the global cleanup system"""
    cleanup_system.start()

def track_message(bot_name: str, chat_id: str, message_id: int, signal_id: str):
    """Track a Telegram message for auto-deletion"""
    cleanup_system.track_telegram_message(bot_name, chat_id, message_id, signal_id)

if __name__ == "__main__":
    # Test the cleanup system
    logging.basicConfig(level=logging.INFO)
    
    print("Starting auto-cleanup system...")
    cleanup_system.start()
    
    try:
        # Keep running
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nStopping cleanup system...")
        cleanup_system.stop()