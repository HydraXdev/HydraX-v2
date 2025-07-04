# rank_access.py
# BITTEN User Authorization and Access Control System

import os
import time
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from functools import wraps

class UserRank(Enum):
    """User access levels in BITTEN system"""
    UNAUTHORIZED = 0
    USER = 1
    AUTHORIZED = 2  
    ELITE = 3
    ADMIN = 4

@dataclass
class UserInfo:
    """User information and permissions"""
    user_id: int
    username: str
    rank: UserRank
    join_date: str
    last_command: Optional[str] = None
    command_count: int = 0
    rate_limit_reset: float = 0

class RankAccess:
    """User authorization and access control manager"""
    
    def __init__(self):
        self.users: Dict[int, UserInfo] = {}
        self.rate_limits: Dict[UserRank, int] = {
            UserRank.USER: 10,      # 10 commands per hour
            UserRank.AUTHORIZED: 30, # 30 commands per hour  
            UserRank.ELITE: 100,    # 100 commands per hour
            UserRank.ADMIN: 0       # No limit
        }
        self._load_user_config()
    
    def _load_user_config(self):
        """Load user configuration from environment variables"""
        # Admin users
        admin_users = os.getenv('BITTEN_ADMIN_USERS', '').split(',')
        for user in admin_users:
            if user.strip():
                try:
                    user_id = int(user.strip())
                    self.users[user_id] = UserInfo(
                        user_id=user_id,
                        username=f"admin_{user_id}",
                        rank=UserRank.ADMIN,
                        join_date=time.strftime("%Y-%m-%d")
                    )
                except ValueError:
                    pass
        
        # Elite users
        elite_users = os.getenv('BITTEN_ELITE_USERS', '').split(',')
        for user in elite_users:
            if user.strip():
                try:
                    user_id = int(user.strip())
                    if user_id not in self.users:  # Don't override admins
                        self.users[user_id] = UserInfo(
                            user_id=user_id,
                            username=f"elite_{user_id}",
                            rank=UserRank.ELITE,
                            join_date=time.strftime("%Y-%m-%d")
                        )
                except ValueError:
                    pass
        
        # Authorized users  
        auth_users = os.getenv('BITTEN_AUTHORIZED_USERS', '').split(',')
        for user in auth_users:
            if user.strip():
                try:
                    user_id = int(user.strip())
                    if user_id not in self.users:  # Don't override higher ranks
                        self.users[user_id] = UserInfo(
                            user_id=user_id,
                            username=f"auth_{user_id}",
                            rank=UserRank.AUTHORIZED,
                            join_date=time.strftime("%Y-%m-%d")
                        )
                except ValueError:
                    pass
    
    def get_user_rank(self, user_id: int) -> UserRank:
        """Get user's access rank"""
        if user_id in self.users:
            return self.users[user_id].rank
        return UserRank.USER  # Default rank for unknown users
    
    def check_permission(self, user_id: int, required_rank: UserRank) -> bool:
        """Check if user has required permission level"""
        user_rank = self.get_user_rank(user_id)
        return user_rank.value >= required_rank.value
    
    def check_rate_limit(self, user_id: int) -> bool:
        """Check if user is within rate limits"""
        user_rank = self.get_user_rank(user_id)
        
        # Admin has no rate limit
        if user_rank == UserRank.ADMIN:
            return True
        
        current_time = time.time()
        
        # Initialize user if not exists
        if user_id not in self.users:
            self.users[user_id] = UserInfo(
                user_id=user_id,
                username=f"user_{user_id}",
                rank=UserRank.USER,
                join_date=time.strftime("%Y-%m-%d"),
                rate_limit_reset=current_time + 3600  # Reset in 1 hour
            )
        
        user = self.users[user_id]
        
        # Reset counter if hour has passed
        if current_time > user.rate_limit_reset:
            user.command_count = 0
            user.rate_limit_reset = current_time + 3600
        
        # Check limit
        limit = self.rate_limits.get(user_rank, 10)
        if user.command_count >= limit:
            return False
        
        # Increment counter
        user.command_count += 1
        return True
    
    def log_command(self, user_id: int, command: str):
        """Log user command for tracking"""
        if user_id in self.users:
            self.users[user_id].last_command = command
    
    def get_user_info(self, user_id: int) -> Optional[UserInfo]:
        """Get complete user information"""
        return self.users.get(user_id)
    
    def add_user(self, user_id: int, username: str, rank: UserRank = UserRank.USER):
        """Add new user to system"""
        self.users[user_id] = UserInfo(
            user_id=user_id,
            username=username,
            rank=rank,
            join_date=time.strftime("%Y-%m-%d")
        )
    
    def promote_user(self, user_id: int, new_rank: UserRank) -> bool:
        """Promote user to higher rank"""
        if user_id in self.users:
            self.users[user_id].rank = new_rank
            return True
        return False
    
    def get_users_by_rank(self, rank: UserRank) -> List[UserInfo]:
        """Get all users with specific rank"""
        return [user for user in self.users.values() if user.rank == rank]

# Command permission decorators
def require_rank(required_rank: UserRank):
    """Decorator to require minimum user rank for command"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, user_id: int, *args, **kwargs):
            if not hasattr(self, 'rank_access'):
                return "❌ Authorization system not available"
            
            if not self.rank_access.check_permission(user_id, required_rank):
                user_rank = self.rank_access.get_user_rank(user_id)
                return f"❌ Access denied. Required: {required_rank.name}, Your rank: {user_rank.name}"
            
            if not self.rank_access.check_rate_limit(user_id):
                return "❌ Rate limit exceeded. Please wait before sending more commands."
            
            return func(self, user_id, *args, **kwargs)
        return wrapper
    return decorator

def require_user():
    """Decorator for basic user commands"""
    return require_rank(UserRank.USER)

def require_authorized():
    """Decorator for authorized user commands"""
    return require_rank(UserRank.AUTHORIZED)

def require_elite():
    """Decorator for elite user commands"""
    return require_rank(UserRank.ELITE)

def require_admin():
    """Decorator for admin-only commands"""
    return require_rank(UserRank.ADMIN)

# Example usage and command definitions
COMMAND_PERMISSIONS = {
    # System Commands - All Users
    '/start': UserRank.USER,
    '/help': UserRank.USER,
    '/status': UserRank.USER,
    
    # Trading Information - Authorized Users
    '/positions': UserRank.AUTHORIZED,
    '/balance': UserRank.AUTHORIZED,
    '/history': UserRank.AUTHORIZED,
    '/performance': UserRank.AUTHORIZED,
    
    # Trading Commands - Authorized Users
    '/fire': UserRank.AUTHORIZED,
    '/close': UserRank.AUTHORIZED,
    '/mode': UserRank.AUTHORIZED,
    
    # Configuration Commands - Elite Users
    '/risk': UserRank.ELITE,
    '/maxpos': UserRank.ELITE,
    '/tactical': UserRank.ELITE,
    '/tcs': UserRank.ELITE,
    '/signals': UserRank.ELITE,
    
    # Advanced Commands - Elite Users
    '/closeall': UserRank.ELITE,
    '/backtest': UserRank.ELITE,
    
    # Admin Commands - Admin Only
    '/logs': UserRank.ADMIN,
    '/restart': UserRank.ADMIN,
    '/backup': UserRank.ADMIN,
    '/promote': UserRank.ADMIN,
    '/ban': UserRank.ADMIN
}

def get_command_permission(command: str) -> UserRank:
    """Get required permission for a command"""
    return COMMAND_PERMISSIONS.get(command, UserRank.ELITE)  # Default to Elite for unknown commands
