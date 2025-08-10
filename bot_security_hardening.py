#!/usr/bin/env python3
"""
🚨 BOT SECURITY HARDENING SYSTEM
Implemented due to bot compromise - August 7, 2025
"""

import time
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
from collections import defaultdict, deque

logger = logging.getLogger('BotSecurity')

class BotSecurityHardening:
    """Enhanced security system to prevent bot compromise"""
    
    def __init__(self):
        # Rate limiting
        self.user_request_counts = defaultdict(lambda: deque(maxlen=100))
        self.user_last_request = {}
        
        # Command monitoring
        self.suspicious_patterns = [
            "spam", "hack", "bot", "token", "admin", "root", "password",
            "inject", "execute", "eval", "import", "os.", "subprocess",
            "system", "shell", "cmd", "__", "getattr", "setattr"
        ]
        
        # User behavior tracking
        self.user_command_history = defaultdict(lambda: deque(maxlen=50))
        self.blocked_users = set()
        self.suspicious_users = set()
        
        # Security metrics
        self.total_requests = 0
        self.blocked_requests = 0
        self.suspicious_requests = 0
        
        logger.info("🛡️ Bot Security Hardening initialized")
        
    def validate_user_request(self, user_id: str, message_text: str, chat_type: str = "private") -> bool:
        """Validate incoming user request for security threats"""
        try:
            self.total_requests += 1
            
            # 1. Check if user is blocked
            if user_id in self.blocked_users:
                logger.warning(f"🚫 Blocked user {user_id} attempted request")
                self.blocked_requests += 1
                return False
                
            # 2. Rate limiting check
            if not self._check_rate_limit(user_id):
                logger.warning(f"⏰ Rate limit exceeded for user {user_id}")
                self._add_suspicious_user(user_id, "rate_limit_exceeded")
                return False
                
            # 3. Content validation
            if not self._validate_message_content(message_text, user_id):
                logger.warning(f"🚨 Suspicious content from user {user_id}: {message_text[:50]}...")
                return False
                
            # 4. Behavioral analysis
            if not self._analyze_user_behavior(user_id, message_text):
                logger.warning(f"🔍 Suspicious behavior pattern from user {user_id}")
                return False
                
            # 5. Update tracking
            self._update_user_tracking(user_id, message_text)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in security validation: {e}")
            return False  # Fail secure
            
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        current_time = time.time()
        
        # Add current request
        self.user_request_counts[user_id].append(current_time)
        
        # Check requests in last minute
        minute_ago = current_time - 60
        recent_requests = [t for t in self.user_request_counts[user_id] if t > minute_ago]
        
        # Rate limit: 30 requests per minute max
        if len(recent_requests) > 30:
            return False
            
        # Check for burst requests (5 in 5 seconds)
        five_seconds_ago = current_time - 5
        burst_requests = [t for t in self.user_request_counts[user_id] if t > five_seconds_ago]
        
        if len(burst_requests) > 5:
            return False
            
        return True
        
    def _validate_message_content(self, message: str, user_id: str) -> bool:
        """Validate message content for suspicious patterns"""
        message_lower = message.lower()
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if pattern in message_lower:
                self._add_suspicious_user(user_id, f"suspicious_pattern_{pattern}")
                self.suspicious_requests += 1
                return False
                
        # Check for excessive length (potential spam)
        if len(message) > 1000:
            self._add_suspicious_user(user_id, "excessive_length")
            return False
            
        # Check for repeated characters (spam indicator)
        if self._detect_spam_patterns(message):
            self._add_suspicious_user(user_id, "spam_pattern")
            return False
            
        return True
        
    def _detect_spam_patterns(self, message: str) -> bool:
        """Detect spam patterns in message"""
        # Repeated characters
        for i in range(len(message) - 4):
            if message[i] == message[i+1] == message[i+2] == message[i+3] == message[i+4]:
                return True
                
        # Too many caps
        if len(message) > 20:
            caps_count = sum(1 for c in message if c.isupper())
            if caps_count / len(message) > 0.7:
                return True
                
        return False
        
    def _analyze_user_behavior(self, user_id: str, message: str) -> bool:
        """Analyze user behavior patterns"""
        # Check command frequency
        user_history = self.user_command_history[user_id]
        
        # Too many identical commands
        if len(user_history) >= 5:
            recent_commands = list(user_history)[-5:]
            if len(set(recent_commands)) == 1:  # All same command
                self._add_suspicious_user(user_id, "repeated_commands")
                return False
                
        return True
        
    def _update_user_tracking(self, user_id: str, message: str):
        """Update user behavior tracking"""
        # Extract command from message
        command = message.split()[0] if message.split() else message
        self.user_command_history[user_id].append(command)
        self.user_last_request[user_id] = time.time()
        
    def _add_suspicious_user(self, user_id: str, reason: str):
        """Add user to suspicious list"""
        self.suspicious_users.add(user_id)
        logger.warning(f"🚨 User {user_id} marked suspicious: {reason}")
        
        # Auto-block after multiple suspicious activities
        user_history = self.user_command_history[user_id]
        if len([cmd for cmd in user_history if 'suspicious' in str(cmd)]) >= 3:
            self.blocked_users.add(user_id)
            logger.error(f"🚫 User {user_id} auto-blocked for repeated suspicious activity")
            
    def block_user(self, user_id: str, reason: str = "manual_block"):
        """Manually block a user"""
        self.blocked_users.add(user_id)
        logger.error(f"🚫 User {user_id} blocked manually: {reason}")
        
    def unblock_user(self, user_id: str):
        """Unblock a user"""
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)
            logger.info(f"✅ User {user_id} unblocked")
            
    def get_security_stats(self) -> Dict:
        """Get security statistics"""
        return {
            'total_requests': self.total_requests,
            'blocked_requests': self.blocked_requests,
            'suspicious_requests': self.suspicious_requests,
            'blocked_users_count': len(self.blocked_users),
            'suspicious_users_count': len(self.suspicious_users),
            'block_rate': f"{(self.blocked_requests/max(1,self.total_requests)*100):.1f}%"
        }
        
    def log_security_event(self, event_type: str, user_id: str, details: str):
        """Log security events"""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} | {event_type} | User: {user_id} | {details}"
        
        # Write to security log
        try:
            with open('/root/HydraX-v2/logs/security.log', 'a') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            logger.error(f"❌ Failed to write security log: {e}")

# Global security instance
bot_security = BotSecurityHardening()

def validate_request(user_id: str, message: str, chat_type: str = "private") -> bool:
    """Easy access function for request validation"""
    return bot_security.validate_user_request(str(user_id), message, chat_type)

def block_user(user_id: str, reason: str = "security_threat"):
    """Easy access function to block user"""
    bot_security.block_user(str(user_id), reason)

def get_stats():
    """Get security statistics"""
    return bot_security.get_security_stats()

if __name__ == "__main__":
    # Test security system
    print("🧪 Testing bot security hardening...")
    
    # Test normal request
    result1 = validate_request("123456", "/status")
    print(f"Normal request: {result1}")
    
    # Test suspicious request
    result2 = validate_request("123456", "hack the bot please")
    print(f"Suspicious request: {result2}")
    
    # Test rate limiting
    for i in range(35):
        result = validate_request("123456", f"/spam{i}")
    print(f"Rate limit test (should be False): {validate_request('123456', '/test')}")
    
    # Print stats
    print("Security stats:", get_stats())