"""
Recovery Strategies for BITTEN System
Implements specific recovery strategies for common failure scenarios
"""

import sqlite3
import requests
import time
import os
import subprocess
import psutil
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading
import signal

logger = logging.getLogger("bitten_recovery")


@dataclass
class RecoveryAction:
    """Represents a recovery action that can be taken"""
    name: str
    description: str
    action: Callable[[Dict[str, Any]], bool]
    priority: int = 1  # Lower number = higher priority
    max_attempts: int = 3
    cooldown_seconds: int = 60


class DatabaseRecoveryManager:
    """Handles database-related recovery operations"""
    
    @staticmethod
    def recover_sqlite_database(context: Dict[str, Any]) -> bool:
        """Attempt to recover a corrupted SQLite database"""
        db_path = context.get("db_path")
        if not db_path or not os.path.exists(db_path):
            return False
        
        try:
            # Test if database is accessible
            conn = sqlite3.connect(db_path, timeout=5)
            conn.execute("SELECT 1")
            conn.close()
            return True
        
        except sqlite3.DatabaseError:
            # Attempt to recover using SQLite's built-in recovery
            try:
                backup_path = f"{db_path}.backup_{int(time.time())}"
                
                # Create backup
                with open(db_path, 'rb') as source:
                    with open(backup_path, 'wb') as backup:
                        backup.write(source.read())
                
                # Try to dump and restore
                dump_path = f"{db_path}.dump"
                restore_path = f"{db_path}.recovered"
                
                # Use sqlite3 command line tool for recovery
                dump_cmd = f"sqlite3 {db_path} .dump > {dump_path}"
                restore_cmd = f"sqlite3 {restore_path} < {dump_path}"
                
                if subprocess.run(dump_cmd, shell=True).returncode == 0:
                    if subprocess.run(restore_cmd, shell=True).returncode == 0:
                        # Replace original with recovered
                        os.replace(restore_path, db_path)
                        os.remove(dump_path)
                        logger.info(f"Successfully recovered database {db_path}")
                        return True
                
                # If recovery fails, restore backup
                os.replace(backup_path, db_path)
                return False
            
            except Exception as e:
                logger.error(f"Database recovery failed: {e}")
                return False
    
    @staticmethod
    def recreate_database_schema(context: Dict[str, Any]) -> bool:
        """Recreate database schema if corrupted"""
        db_path = context.get("db_path")
        schema_file = context.get("schema_file", "database/schema.sql")
        
        if not db_path:
            return False
        
        try:
            # Backup existing database
            if os.path.exists(db_path):
                backup_path = f"{db_path}.backup_{int(time.time())}"
                with open(db_path, 'rb') as source:
                    with open(backup_path, 'wb') as backup:
                        backup.write(source.read())
            
            # Remove corrupted database
            if os.path.exists(db_path):
                os.remove(db_path)
            
            # Recreate from schema if available
            if os.path.exists(schema_file):
                with open(schema_file, 'r') as f:
                    schema = f.read()
                
                conn = sqlite3.connect(db_path)
                conn.executescript(schema)
                conn.close()
                
                logger.info(f"Recreated database schema for {db_path}")
                return True
            
            # Create basic schema for engagement db
            elif "engagement" in db_path:
                from ..database.engagement_db import init_engagement_database
                init_engagement_database(db_path)
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Schema recreation failed: {e}")
            return False


class NetworkRecoveryManager:
    """Handles network-related recovery operations"""
    
    @staticmethod
    def test_internet_connectivity(context: Dict[str, Any]) -> bool:
        """Test basic internet connectivity"""
        test_urls = [
            "https://8.8.8.8",  # Google DNS
            "https://1.1.1.1",  # Cloudflare DNS
            "https://httpbin.org/status/200"
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return True
            except:
                continue
        
        return False
    
    @staticmethod
    def flush_dns_cache(context: Dict[str, Any]) -> bool:
        """Flush system DNS cache"""
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(["ipconfig", "/flushdns"], check=True)
            else:  # Linux
                subprocess.run(["systemctl", "restart", "systemd-resolved"], check=True)
            
            logger.info("DNS cache flushed successfully")
            return True
        
        except Exception as e:
            logger.error(f"DNS flush failed: {e}")
            return False
    
    @staticmethod
    def restart_network_interface(context: Dict[str, Any]) -> bool:
        """Restart network interface (Linux only)"""
        interface = context.get("interface", "eth0")
        
        try:
            subprocess.run(["ip", "link", "set", interface, "down"], check=True)
            time.sleep(2)
            subprocess.run(["ip", "link", "set", interface, "up"], check=True)
            time.sleep(5)
            
            logger.info(f"Network interface {interface} restarted")
            return True
        
        except Exception as e:
            logger.error(f"Network interface restart failed: {e}")
            return False


class TelegramRecoveryManager:
    """Handles Telegram API recovery operations"""
    
    @staticmethod
    def test_telegram_api(context: Dict[str, Any]) -> bool:
        """Test Telegram API connectivity"""
        bot_token = context.get("bot_token")
        if not bot_token:
            return False
        
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{bot_token}/getMe",
                timeout=10
            )
            return response.status_code == 200
        
        except Exception as e:
            logger.error(f"Telegram API test failed: {e}")
            return False
    
    @staticmethod
    def clear_telegram_webhook(context: Dict[str, Any]) -> bool:
        """Clear Telegram webhook that might be causing issues"""
        bot_token = context.get("bot_token")
        if not bot_token:
            return False
        
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/deleteWebhook",
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Telegram webhook cleared")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Webhook clearing failed: {e}")
            return False
    
    @staticmethod
    def reset_telegram_connection(context: Dict[str, Any]) -> bool:
        """Reset Telegram bot connection"""
        bot_token = context.get("bot_token")
        if not bot_token:
            return False
        
        try:
            # Clear webhook first
            requests.post(
                f"https://api.telegram.org/bot{bot_token}/deleteWebhook",
                timeout=5
            )
            
            time.sleep(2)
            
            # Test connection
            response = requests.get(
                f"https://api.telegram.org/bot{bot_token}/getMe",
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Telegram connection reset successfully")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Telegram connection reset failed: {e}")
            return False


class ProcessRecoveryManager:
    """Handles process and service recovery operations"""
    
    @staticmethod
    def restart_process_by_name(context: Dict[str, Any]) -> bool:
        """Restart a process by name"""
        process_name = context.get("process_name")
        if not process_name:
            return False
        
        try:
            # Find and terminate process
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if process_name in proc.info['name'] or \
                   any(process_name in cmd for cmd in (proc.info['cmdline'] or [])):
                    proc.terminate()
                    proc.wait(timeout=10)
            
            # Give time for process to stop
            time.sleep(3)
            
            # Restart command
            restart_cmd = context.get("restart_command")
            if restart_cmd:
                subprocess.Popen(restart_cmd, shell=True)
                time.sleep(5)
                
                # Verify process is running
                for proc in psutil.process_iter(['name', 'cmdline']):
                    if process_name in proc.info['name'] or \
                       any(process_name in cmd for cmd in (proc.info['cmdline'] or [])):
                        logger.info(f"Process {process_name} restarted successfully")
                        return True
            
            return False
        
        except Exception as e:
            logger.error(f"Process restart failed: {e}")
            return False
    
    @staticmethod
    def restart_webapp_server(context: Dict[str, Any]) -> bool:
        """Restart the Flask webapp server"""
        try:
            # Find webapp process
            webapp_pid = None
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = proc.info['cmdline'] or []
                if any('webapp_server.py' in cmd for cmd in cmdline):
                    webapp_pid = proc.info['pid']
                    proc.terminate()
                    proc.wait(timeout=10)
                    break
            
            time.sleep(3)
            
            # Restart webapp
            webapp_cmd = context.get("webapp_command", "python3 webapp_server.py")
            subprocess.Popen(webapp_cmd, shell=True, cwd="/root/HydraX-v2")
            
            # Wait and verify
            time.sleep(10)
            
            # Test if webapp is responding
            try:
                response = requests.get("http://localhost:8888/health", timeout=5)
                if response.status_code in [200, 503]:  # 503 is acceptable for health check
                    logger.info("Webapp server restarted successfully")
                    return True
            except:
                pass
            
            return False
        
        except Exception as e:
            logger.error(f"Webapp restart failed: {e}")
            return False


class SystemRecoveryManager:
    """Handles system-level recovery operations"""
    
    @staticmethod
    def clear_temp_files(context: Dict[str, Any]) -> bool:
        """Clear temporary files that might be causing issues"""
        temp_dirs = [
            "/tmp",
            "/var/tmp",
            "/root/HydraX-v2/logs",
            "/root/HydraX-v2/temp"
        ]
        
        try:
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    # Clear files older than 1 hour
                    cutoff_time = time.time() - 3600
                    
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                if os.path.getmtime(file_path) < cutoff_time:
                                    os.remove(file_path)
                            except:
                                continue
            
            logger.info("Temporary files cleared")
            return True
        
        except Exception as e:
            logger.error(f"Temp file clearing failed: {e}")
            return False
    
    @staticmethod
    def check_disk_space(context: Dict[str, Any]) -> bool:
        """Check if sufficient disk space is available"""
        min_free_gb = context.get("min_free_gb", 1)
        
        try:
            statvfs = os.statvfs('/')
            free_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
            
            if free_gb >= min_free_gb:
                return True
            
            logger.warning(f"Low disk space: {free_gb:.2f}GB free")
            return False
        
        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return False
    
    @staticmethod
    def check_memory_usage(context: Dict[str, Any]) -> bool:
        """Check memory usage and free up if needed"""
        max_memory_percent = context.get("max_memory_percent", 90)
        
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent < max_memory_percent:
                return True
            
            logger.warning(f"High memory usage: {memory.percent}%")
            
            # Attempt to free memory by killing high-memory processes
            processes = sorted(
                psutil.process_iter(['pid', 'name', 'memory_percent']),
                key=lambda p: p.info['memory_percent'],
                reverse=True
            )
            
            # Kill processes using more than 20% memory (except system processes)
            for proc in processes[:3]:  # Only top 3 memory users
                if proc.info['memory_percent'] > 20 and \
                   proc.info['name'] not in ['systemd', 'kernel', 'init']:
                    try:
                        proc.terminate()
                        proc.wait(timeout=5)
                        logger.info(f"Terminated high-memory process: {proc.info['name']}")
                    except:
                        continue
            
            # Check memory again
            memory = psutil.virtual_memory()
            return memory.percent < max_memory_percent
        
        except Exception as e:
            logger.error(f"Memory check failed: {e}")
            return False


class AdvancedRecoveryManager:
    """Manages advanced recovery strategies and coordination"""
    
    def __init__(self):
        self.recovery_actions = self._initialize_recovery_actions()
        self.recovery_history = {}
        self.active_recoveries = set()
        self._lock = threading.Lock()
    
    def _initialize_recovery_actions(self) -> Dict[str, List[RecoveryAction]]:
        """Initialize all recovery actions organized by category"""
        return {
            "database": [
                RecoveryAction(
                    name="test_connection",
                    description="Test database connection",
                    action=DatabaseRecoveryManager.recover_sqlite_database,
                    priority=1
                ),
                RecoveryAction(
                    name="recreate_schema",
                    description="Recreate database schema",
                    action=DatabaseRecoveryManager.recreate_database_schema,
                    priority=3,
                    max_attempts=1
                )
            ],
            "network": [
                RecoveryAction(
                    name="test_connectivity",
                    description="Test internet connectivity",
                    action=NetworkRecoveryManager.test_internet_connectivity,
                    priority=1
                ),
                RecoveryAction(
                    name="flush_dns",
                    description="Flush DNS cache",
                    action=NetworkRecoveryManager.flush_dns_cache,
                    priority=2
                ),
                RecoveryAction(
                    name="restart_interface",
                    description="Restart network interface",
                    action=NetworkRecoveryManager.restart_network_interface,
                    priority=3,
                    max_attempts=1,
                    cooldown_seconds=300
                )
            ],
            "telegram": [
                RecoveryAction(
                    name="test_api",
                    description="Test Telegram API",
                    action=TelegramRecoveryManager.test_telegram_api,
                    priority=1
                ),
                RecoveryAction(
                    name="clear_webhook",
                    description="Clear Telegram webhook",
                    action=TelegramRecoveryManager.clear_telegram_webhook,
                    priority=2
                ),
                RecoveryAction(
                    name="reset_connection",
                    description="Reset Telegram connection",
                    action=TelegramRecoveryManager.reset_telegram_connection,
                    priority=3
                )
            ],
            "webapp": [
                RecoveryAction(
                    name="restart_server",
                    description="Restart webapp server",
                    action=ProcessRecoveryManager.restart_webapp_server,
                    priority=2,
                    max_attempts=2,
                    cooldown_seconds=120
                )
            ],
            "system": [
                RecoveryAction(
                    name="clear_temp",
                    description="Clear temporary files",
                    action=SystemRecoveryManager.clear_temp_files,
                    priority=1
                ),
                RecoveryAction(
                    name="check_disk",
                    description="Check disk space",
                    action=SystemRecoveryManager.check_disk_space,
                    priority=1
                ),
                RecoveryAction(
                    name="check_memory",
                    description="Check memory usage",
                    action=SystemRecoveryManager.check_memory_usage,
                    priority=2
                )
            ]
        }
    
    def execute_recovery_sequence(self, category: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute recovery sequence for a specific category"""
        if category not in self.recovery_actions:
            return {"success": False, "error": f"Unknown recovery category: {category}"}
        
        with self._lock:
            if category in self.active_recoveries:
                return {
                    "success": False, 
                    "error": f"Recovery already in progress for {category}"
                }
            
            self.active_recoveries.add(category)
        
        try:
            results = []
            actions = sorted(
                self.recovery_actions[category],
                key=lambda x: x.priority
            )
            
            for action in actions:
                # Check cooldown
                last_attempt = self.recovery_history.get(f"{category}_{action.name}")
                if last_attempt and \
                   (datetime.now() - last_attempt).seconds < action.cooldown_seconds:
                    continue
                
                # Execute action
                logger.info(f"Executing recovery action: {action.name}")
                
                try:
                    success = action.action(context)
                    results.append({
                        "action": action.name,
                        "description": action.description,
                        "success": success
                    })
                    
                    # Record attempt
                    self.recovery_history[f"{category}_{action.name}"] = datetime.now()
                    
                    if success:
                        logger.info(f"Recovery action {action.name} succeeded")
                        break  # Stop on first success
                    else:
                        logger.warning(f"Recovery action {action.name} failed")
                
                except Exception as e:
                    logger.error(f"Recovery action {action.name} raised exception: {e}")
                    results.append({
                        "action": action.name,
                        "description": action.description,
                        "success": False,
                        "error": str(e)
                    })
            
            overall_success = any(result["success"] for result in results)
            
            return {
                "success": overall_success,
                "category": category,
                "actions_executed": len(results),
                "results": results
            }
        
        finally:
            with self._lock:
                self.active_recoveries.discard(category)
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Get current recovery system status"""
        return {
            "active_recoveries": list(self.active_recoveries),
            "available_categories": list(self.recovery_actions.keys()),
            "recovery_history_count": len(self.recovery_history),
            "last_recovery_attempts": {
                key: timestamp.isoformat()
                for key, timestamp in list(self.recovery_history.items())[-10:]
            }
        }


# Global recovery manager instance
recovery_manager = AdvancedRecoveryManager()


# Convenience functions for common recovery scenarios
def recover_database_issues(db_path: str) -> Dict[str, Any]:
    """Quick function to recover database issues"""
    return recovery_manager.execute_recovery_sequence(
        "database", 
        {"db_path": db_path}
    )


def recover_network_issues() -> Dict[str, Any]:
    """Quick function to recover network issues"""
    return recovery_manager.execute_recovery_sequence("network", {})


def recover_telegram_issues(bot_token: str) -> Dict[str, Any]:
    """Quick function to recover Telegram issues"""
    return recovery_manager.execute_recovery_sequence(
        "telegram", 
        {"bot_token": bot_token}
    )


def recover_webapp_issues() -> Dict[str, Any]:
    """Quick function to recover webapp issues"""
    return recovery_manager.execute_recovery_sequence("webapp", {})


def recover_system_issues() -> Dict[str, Any]:
    """Quick function to recover system issues"""
    return recovery_manager.execute_recovery_sequence("system", {})


if __name__ == "__main__":
    # Test recovery system
    print("Testing recovery system...")
    
    # Test database recovery
    result = recover_database_issues("test.db")
    print(f"Database recovery: {result}")
    
    # Test network recovery
    result = recover_network_issues()
    print(f"Network recovery: {result}")
    
    # Get status
    status = recovery_manager.get_recovery_status()
    print(f"Recovery status: {status}")