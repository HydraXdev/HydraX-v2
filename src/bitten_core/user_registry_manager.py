#!/usr/bin/env python3
"""
User Registry Manager - HydraX Container Mapping System
Manages Telegram chat_id to container mapping and user status tracking
"""

import json
import os
import time
from typing import Dict, Optional, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class UserRegistryManager:
    """Manages user registry for Telegram to container mapping"""
    
    def __init__(self, registry_file: str = '/root/HydraX-v2/user_registry_complete.json'):
        self.registry_file = registry_file
        self.registry_data = {}
        self.load_registry()
    
    def load_registry(self):
        """Load user registry from JSON file"""
        try:
            if os.path.exists(self.registry_file):
                with open(self.registry_file, 'r') as f:
                    self.registry_data = json.load(f)
                logger.info(f"Loaded {len(self.registry_data)} users from registry")
            else:
                self.registry_data = {}
                self.save_registry()
                logger.info("Created new user registry")
        except Exception as e:
            logger.error(f"Error loading registry: {e}")
            self.registry_data = {}
    
    def save_registry(self):
        """Save user registry to JSON file"""
        try:
            # Create backup
            if os.path.exists(self.registry_file):
                backup_file = f"{self.registry_file}.backup"
                os.rename(self.registry_file, backup_file)
            
            with open(self.registry_file, 'w') as f:
                json.dump(self.registry_data, f, indent=2)
            logger.info("Registry saved successfully")
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
    
    def register_user(self, telegram_id: str, user_id: str, container: str, 
                     login: Optional[str] = None, broker: Optional[str] = None) -> bool:
        """Register a new user in the system"""
        try:
            current_time = datetime.now(timezone.utc).isoformat()
            
            user_data = {
                "user_id": user_id,
                "container": container,
                "login": login,
                "broker": broker,
                "status": "unassigned",
                "created_at": current_time,
                "updated_at": current_time,
                "wine_environment": f"/root/.wine_user_{telegram_id}",
                "fire_eligible": False,
                "last_activity": current_time,
                "connection_attempts": 0,
                "successful_connections": 0
            }
            
            self.registry_data[telegram_id] = user_data
            self.save_registry()
            logger.info(f"Registered user {telegram_id} with container {container}")
            return True
        except Exception as e:
            logger.error(f"Error registering user {telegram_id}: {e}")
            return False
    
    def update_user_status(self, telegram_id: str, status: str) -> bool:
        """Update user status in registry"""
        try:
            if telegram_id not in self.registry_data:
                logger.warning(f"User {telegram_id} not found in registry")
                return False
            
            valid_statuses = [
                "unassigned",
                "credentials_injected", 
                "mt5_logged_in",
                "ready_for_fire",
                "error_state"
            ]
            
            if status not in valid_statuses:
                logger.error(f"Invalid status: {status}")
                return False
            
            self.registry_data[telegram_id]["status"] = status
            self.registry_data[telegram_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Update fire eligibility based on status
            self.registry_data[telegram_id]["fire_eligible"] = (status == "ready_for_fire")
            
            self.save_registry()
            logger.info(f"Updated user {telegram_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating user {telegram_id} status: {e}")
            return False
    
    def update_user_credentials(self, telegram_id: str, login: str, broker: str) -> bool:
        """Update user MT5 credentials"""
        try:
            if telegram_id not in self.registry_data:
                logger.warning(f"User {telegram_id} not found in registry")
                return False
            
            self.registry_data[telegram_id]["login"] = login
            self.registry_data[telegram_id]["broker"] = broker
            self.registry_data[telegram_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            self.registry_data[telegram_id]["connection_attempts"] += 1
            
            self.save_registry()
            logger.info(f"Updated credentials for user {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating credentials for user {telegram_id}: {e}")
            return False
    
    def get_user_info(self, telegram_id: str) -> Optional[Dict[str, Any]]:
        """Get user information from registry"""
        return self.registry_data.get(telegram_id)
    
    def get_container_name(self, telegram_id: str) -> Optional[str]:
        """Get container name for user"""
        user_info = self.get_user_info(telegram_id)
        return user_info.get("container") if user_info else None
    
    def is_user_ready_for_fire(self, telegram_id: str) -> bool:
        """Check if user is ready to receive fire packets"""
        user_info = self.get_user_info(telegram_id)
        return user_info.get("fire_eligible", False) if user_info else False
    
    def get_all_ready_users(self) -> Dict[str, Dict]:
        """Get all users ready for fire packets"""
        ready_users = {}
        for telegram_id, user_info in self.registry_data.items():
            if user_info.get("fire_eligible", False):
                ready_users[telegram_id] = user_info
        return ready_users
    
    def record_successful_connection(self, telegram_id: str):
        """Record a successful connection for user"""
        try:
            if telegram_id in self.registry_data:
                self.registry_data[telegram_id]["successful_connections"] += 1
                self.registry_data[telegram_id]["last_activity"] = datetime.now(timezone.utc).isoformat()
                self.save_registry()
        except Exception as e:
            logger.error(f"Error recording connection for {telegram_id}: {e}")
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_users = len(self.registry_data)
        status_counts = {}
        ready_for_fire = 0
        
        for user_info in self.registry_data.values():
            status = user_info.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            if user_info.get("fire_eligible", False):
                ready_for_fire += 1
        
        return {
            "total_users": total_users,
            "ready_for_fire": ready_for_fire,
            "status_breakdown": status_counts,
            "registry_file": self.registry_file
        }

# Global instance
_registry_manager = None

def get_user_registry_manager() -> UserRegistryManager:
    """Get global user registry manager instance"""
    global _registry_manager
    if _registry_manager is None:
        _registry_manager = UserRegistryManager()
    return _registry_manager

# Convenience functions
def register_user(telegram_id: str, user_id: str, container: str, 
                 login: str = None, broker: str = None) -> bool:
    """Register user - convenience function"""
    return get_user_registry_manager().register_user(telegram_id, user_id, container, login, broker)

def update_user_status(telegram_id: str, status: str) -> bool:
    """Update user status - convenience function"""
    return get_user_registry_manager().update_user_status(telegram_id, status)

def get_user_container(telegram_id: str) -> Optional[str]:
    """Get user container name - convenience function"""
    return get_user_registry_manager().get_container_name(telegram_id)

def is_user_ready(telegram_id: str) -> bool:
    """Check if user ready for fire - convenience function"""
    return get_user_registry_manager().is_user_ready_for_fire(telegram_id)

if __name__ == "__main__":
    # Test the registry system
    registry = UserRegistryManager()
    
    # Test registering a user
    test_id = "7176191872"
    registry.register_user(test_id, "chris", f"mt5_user_{test_id}")
    
    # Test updating status
    registry.update_user_status(test_id, "credentials_injected")
    
    # Test getting info
    info = registry.get_user_info(test_id)
    print(f"User info: {json.dumps(info, indent=2)}")
    
    # Test stats
    stats = registry.get_registry_stats()
    print(f"Registry stats: {json.dumps(stats, indent=2)}")