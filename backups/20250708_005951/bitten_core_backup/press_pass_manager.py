"""
Press Pass Management System for BITTEN
Handles the limited-time Press Pass offers with urgency and scarcity
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json
import os
from pathlib import Path

from .database.connection import get_db_connection
from .notification_handler import NotificationHandler
from .subscription_manager import SubscriptionManager
from config.telegram import TelegramConfig
from config.analytics import LIVE_COUNTERS, EMAIL_TRACKING


class PressPassManager:
    """Manages Press Pass offers and conversions"""
    
    def __init__(self):
        self.daily_limit = TelegramConfig.PRESS_PASS_DAILY_LIMIT
        self.duration_days = TelegramConfig.PRESS_PASS_DURATION_DAYS
        self.granted_tier = TelegramConfig.PRESS_PASS_TIER
        self.data_file = Path("data/press_pass_tracking.json")
        self._ensure_data_file()
        
    def _ensure_data_file(self):
        """Ensure the tracking file exists"""
        if not self.data_file.exists():
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_data({"daily_claims": {}, "active_passes": {}})
    
    def _load_data(self) -> Dict:
        """Load press pass tracking data"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            return {"daily_claims": {}, "active_passes": {}}
    
    def _save_data(self, data: Dict):
        """Save press pass tracking data"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def get_daily_remaining(self) -> int:
        """Get number of press passes remaining today"""
        data = self._load_data()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Reset counter if new day
        if today not in data["daily_claims"]:
            data["daily_claims"] = {today: 0}
            self._save_data(data)
        
        claimed_today = data["daily_claims"].get(today, 0)
        return max(0, self.daily_limit - claimed_today)
    
    async def claim_press_pass(self, user_id: int, username: str) -> Dict:
        """Claim a press pass for a user"""
        data = self._load_data()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check if user already has active pass
        if str(user_id) in data["active_passes"]:
            pass_info = data["active_passes"][str(user_id)]
            expiry = datetime.fromisoformat(pass_info["expiry_date"])
            if expiry > datetime.now():
                days_remaining = (expiry - datetime.now()).days
                return {
                    "success": False,
                    "error": "already_active",
                    "days_remaining": days_remaining,
                    "expiry_date": expiry
                }
        
        # Check daily limit
        remaining = self.get_daily_remaining()
        if remaining <= 0:
            return {
                "success": False,
                "error": "daily_limit_reached",
                "next_reset": "midnight UTC"
            }
        
        # Claim the pass
        now = datetime.now()
        expiry = now + timedelta(days=self.duration_days)
        
        # Update daily claims
        if today not in data["daily_claims"]:
            data["daily_claims"] = {today: 0}
        data["daily_claims"][today] += 1
        
        # Create press pass record
        data["active_passes"][str(user_id)] = {
            "username": username,
            "claimed_at": now.isoformat(),
            "expiry_date": expiry.isoformat(),
            "tier": self.granted_tier,
            "converted": False,
            "conversion_date": None,
            "total_value": 188 * self.duration_days // 30  # Pro-rated value
        }
        
        self._save_data(data)
        
        # Grant temporary APEX access
        await self._grant_temporary_access(user_id, username)
        
        # Start email campaign
        await self._start_email_campaign(user_id, username)
        
        # Track analytics
        await self._track_claim(user_id, username)
        
        return {
            "success": True,
            "expiry_date": expiry,
            "days": self.duration_days,
            "tier": self.granted_tier,
            "spots_remaining": remaining - 1
        }
    
    async def _grant_temporary_access(self, user_id: int, username: str):
        """Grant temporary APEX tier access"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Create or update user profile with press pass
            cursor.execute("""
                INSERT INTO users (user_id, username, tier, press_pass_active, press_pass_expiry)
                VALUES (?, ?, ?, 1, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    tier = ?,
                    press_pass_active = 1,
                    press_pass_expiry = ?
            """, (user_id, username, self.granted_tier, 
                  datetime.now() + timedelta(days=self.duration_days),
                  self.granted_tier,
                  datetime.now() + timedelta(days=self.duration_days)))
            
            conn.commit()
        finally:
            conn.close()
    
    async def _start_email_campaign(self, user_id: int, username: str):
        """Start the press pass email campaign"""
        # This would integrate with your email service
        # For now, we'll just log the campaign start
        campaign_data = {
            "user_id": user_id,
            "username": username,
            "campaign": "press_pass",
            "start_date": datetime.now().isoformat(),
            "emails_scheduled": len(EMAIL_TRACKING)
        }
        
        # Save campaign data
        campaign_file = Path(f"data/campaigns/press_pass_{user_id}.json")
        campaign_file.parent.mkdir(parents=True, exist_ok=True)
        with open(campaign_file, 'w') as f:
            json.dump(campaign_data, f, indent=2)
    
    async def _track_claim(self, user_id: int, username: str):
        """Track press pass claim in analytics"""
        # This would send to Google Analytics / Facebook Pixel
        analytics_data = {
            "event": "press_pass_claim",
            "user_id": user_id,
            "username": username,
            "value": 188,
            "currency": "USD",
            "timestamp": datetime.now().isoformat()
        }
        
        # Log analytics event
        analytics_file = Path("logs/analytics_events.jsonl")
        analytics_file.parent.mkdir(parents=True, exist_ok=True)
        with open(analytics_file, 'a') as f:
            f.write(json.dumps(analytics_data) + '\n')
    
    async def check_expiring_passes(self) -> List[Dict]:
        """Check for passes expiring soon"""
        data = self._load_data()
        expiring_soon = []
        now = datetime.now()
        
        for user_id, pass_info in data["active_passes"].items():
            if pass_info.get("converted", False):
                continue
                
            expiry = datetime.fromisoformat(pass_info["expiry_date"])
            days_remaining = (expiry - now).days
            
            # Flag passes expiring in 7 days or less
            if 0 < days_remaining <= 7:
                expiring_soon.append({
                    "user_id": int(user_id),
                    "username": pass_info["username"],
                    "days_remaining": days_remaining,
                    "expiry_date": expiry,
                    "urgency_level": "critical" if days_remaining <= 3 else "warning"
                })
        
        return expiring_soon
    
    async def convert_to_paid(self, user_id: int, tier: str, discount_applied: bool = False) -> Dict:
        """Convert a press pass user to paid subscription"""
        data = self._load_data()
        
        if str(user_id) not in data["active_passes"]:
            return {"success": False, "error": "no_active_pass"}
        
        pass_info = data["active_passes"][str(user_id)]
        pass_info["converted"] = True
        pass_info["conversion_date"] = datetime.now().isoformat()
        pass_info["converted_to_tier"] = tier
        pass_info["lifetime_discount"] = discount_applied
        
        self._save_data(data)
        
        # Track conversion
        await self._track_conversion(user_id, tier, discount_applied)
        
        return {
            "success": True,
            "tier": tier,
            "discount_applied": discount_applied,
            "message": "Successfully converted to paid subscription!"
        }
    
    async def _track_conversion(self, user_id: int, tier: str, discount_applied: bool):
        """Track press pass conversion"""
        tier_values = {"NIBBLER": 39, "FANG": 89, "COMMANDER": 139, "APEX": 188}
        value = tier_values.get(tier, 0)
        
        if discount_applied and tier == "APEX":
            value = 141  # Discounted price
        
        analytics_data = {
            "event": "press_pass_conversion",
            "user_id": user_id,
            "tier": tier,
            "value": value,
            "lifetime_discount": discount_applied,
            "currency": "USD",
            "timestamp": datetime.now().isoformat()
        }
        
        analytics_file = Path("logs/analytics_events.jsonl")
        with open(analytics_file, 'a') as f:
            f.write(json.dumps(analytics_data) + '\n')
    
    def get_user_press_pass_status(self, user_id: int) -> Optional[Dict]:
        """Get current press pass status for a user"""
        data = self._load_data()
        
        if str(user_id) not in data["active_passes"]:
            return None
        
        pass_info = data["active_passes"][str(user_id)]
        expiry = datetime.fromisoformat(pass_info["expiry_date"])
        now = datetime.now()
        
        if expiry < now:
            return {
                "active": False,
                "expired": True,
                "expired_date": expiry,
                "converted": pass_info.get("converted", False)
            }
        
        days_remaining = (expiry - now).days
        hours_remaining = int((expiry - now).total_seconds() / 3600)
        
        return {
            "active": True,
            "days_remaining": days_remaining,
            "hours_remaining": hours_remaining,
            "expiry_date": expiry,
            "tier": pass_info["tier"],
            "converted": pass_info.get("converted", False),
            "urgency_level": self._get_urgency_level(days_remaining)
        }
    
    def _get_urgency_level(self, days_remaining: int) -> str:
        """Determine urgency level based on days remaining"""
        if days_remaining <= 1:
            return "CRITICAL"
        elif days_remaining <= 3:
            return "HIGH"
        elif days_remaining <= 7:
            return "MEDIUM"
        elif days_remaining <= 14:
            return "LOW"
        else:
            return "NORMAL"
    
    async def send_urgency_reminder(self, user_id: int, notification_handler: NotificationHandler):
        """Send urgency reminder to user"""
        status = self.get_user_press_pass_status(user_id)
        if not status or not status["active"]:
            return
        
        urgency_messages = {
            "CRITICAL": "🚨 FINAL HOURS! Your Press Pass expires TOMORROW! Don't lose your $188/month APEX access!",
            "HIGH": "⚠️ Only {} days left on your Press Pass! Lock in your discount NOW!",
            "MEDIUM": "⏰ Your Press Pass expires in {} days. Secure your APEX access before it's too late!",
            "LOW": "📅 {} days remaining on your Press Pass. Ready to continue your trading success?"
        }
        
        level = status["urgency_level"]
        if level in urgency_messages:
            message = urgency_messages[level]
            if "{}" in message:
                message = message.format(status["days_remaining"])
            
            await notification_handler.send_notification(
                user_id=user_id,
                message=message,
                buttons=[
                    {"text": "🔒 Secure My Access", "callback_data": "secure_apex_access"},
                    {"text": "📊 View My Results", "callback_data": "view_press_pass_results"}
                ]
            )