"""
Press Pass Email Automation System
Handles automated email campaigns for Press Pass users
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from .email_service import EmailService, create_email_service
from .database.connection import get_db_connection
from .press_pass_manager import PressPassManager

logger = logging.getLogger(__name__)


class PressPassEmailAutomation:
    """Manages automated email campaigns for Press Pass users"""
    
    def __init__(self, email_service: Optional[EmailService] = None):
        self.email_service = email_service or create_email_service()
        self.press_pass_manager = PressPassManager()
        
        # Load campaign configuration
        self.campaigns = self._load_campaign_config()
        
        # Email tracking
        self.sent_emails = {}  # Track sent emails to prevent duplicates
    
    def _load_campaign_config(self) -> Dict[str, Any]:
        """Load email campaign configuration"""
        return {
            "press_pass": {
                "duration_days": 30,
                "emails": [
                    {
                        "day": 0,
                        "template": "press_pass_welcome.html",
                        "subject": "🎖️ Your BITTEN Press Pass is ACTIVE!",
                        "send_time": "immediate",
                        "priority": 1
                    },
                    {
                        "day": 1,
                        "template": "press_pass_day1.html",
                        "subject": "🎯 Ready for Your First BITTEN Trade?",
                        "send_time": "10:00",
                        "priority": 2
                    },
                    {
                        "day": 3,
                        "template": "press_pass_day3.html",
                        "subject": "🔨 $124 Made While You Slept (Midnight Hammer Report)",
                        "send_time": "08:00",
                        "priority": 2
                    },
                    {
                        "day": 7,
                        "template": "press_pass_day7.html",
                        "subject": "📊 Your First Week: +8.7% Growth!",
                        "send_time": "14:00",
                        "priority": 2
                    },
                    {
                        "day": 14,
                        "template": "press_pass_day14.html",
                        "subject": "⚠️ Your Press Pass is HALF OVER (Special Offer Inside)",
                        "send_time": "10:00",
                        "priority": 1
                    },
                    {
                        "day": 21,
                        "template": "press_pass_day21.html",
                        "subject": "📈 3 Weeks In: Your Results Are INSANE",
                        "send_time": "15:00",
                        "priority": 2
                    },
                    {
                        "day": 25,
                        "template": "press_pass_day25.html",
                        "subject": "🚨 FINAL WARNING: 5 Days Until Press Pass Expires",
                        "send_time": "09:00",
                        "priority": 1
                    },
                    {
                        "day": 28,
                        "template": "press_pass_day28.html",
                        "subject": "⏰ 48 HOURS LEFT - Don't Lose Your Profits!",
                        "send_time": "10:00",
                        "priority": 1
                    },
                    {
                        "day": 29,
                        "template": "press_pass_day29.html",
                        "subject": "🔴 TOMORROW: Everything Changes (Last Chance)",
                        "send_time": "18:00",
                        "priority": 1
                    },
                    {
                        "day": 30,
                        "template": "press_pass_expired.html",
                        "subject": "Your Press Pass Has Expired - Here's What's Next",
                        "send_time": "09:00",
                        "priority": 1
                    }
                ]
            },
            "demo": {
                "emails": [
                    {
                        "day": 0,
                        "template": "demo_welcome.html",
                        "subject": "Welcome to BITTEN Demo Mode",
                        "send_time": "immediate",
                        "priority": 2
                    },
                    {
                        "day": 3,
                        "template": "demo_upgrade.html",
                        "subject": "Ready to Trade with Real Money?",
                        "send_time": "10:00",
                        "priority": 2
                    }
                ]
            },
            "tier_upgrade": {
                "emails": [
                    {
                        "trigger": "high_usage",
                        "template": "tier_upgrade_offer.html",
                        "subject": "🚀 You're Ready for More Power!",
                        "priority": 2
                    }
                ]
            }
        }
    
    def trigger_welcome_email(self, user_id: int, email: str, username: str) -> bool:
        """Send welcome email immediately after Press Pass activation"""
        try:
            # Get user data
            user_data = self._get_user_email_data(user_id)
            
            # Prepare template data
            template_data = {
                "username": username,
                "email": email,
                "activation_date": datetime.now().strftime("%B %d, %Y"),
                "expiry_date": (datetime.now() + timedelta(days=30)).strftime("%B %d, %Y"),
                "days_remaining": 30,
                "telegram_link": f"https://t.me/{os.getenv('TELEGRAM_BOT_USERNAME', 'BITTENbot')}",
                **user_data
            }
            
            # Send email
            success = self.email_service.send_template_email(
                to_email=email,
                template_name="press_pass_welcome.html",
                template_data=template_data,
                subject="🎖️ Your BITTEN Press Pass is ACTIVE!",
                tracking_data={
                    "user_id": user_id,
                    "campaign": "press_pass",
                    "email_type": "welcome"
                }
            )
            
            if success:
                self._record_sent_email(user_id, "press_pass_welcome", 0)
                logger.info(f"Welcome email sent to user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            return False
    
    def process_scheduled_emails(self) -> Dict[str, int]:
        """Process all scheduled emails for active Press Pass users"""
        sent_count = 0
        failed_count = 0
        
        try:
            # Get all active Press Pass users
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.id, u.email, u.username, pp.activated_at, pp.tier
                FROM users u
                JOIN press_passes pp ON u.id = pp.user_id
                WHERE pp.status = 'active'
                AND u.email IS NOT NULL
                AND pp.activated_at IS NOT NULL
            """)
            
            users = cursor.fetchall()
            
            for user in users:
                user_id, email, username, activated_at, tier = user
                
                # Calculate days since activation
                days_since_activation = (datetime.now() - activated_at).days
                
                # Get pending emails for this user
                pending_emails = self._get_pending_emails(
                    user_id, 
                    days_since_activation,
                    "press_pass"
                )
                
                for email_config in pending_emails:
                    success = self._send_campaign_email(
                        user_id=user_id,
                        email=email,
                        username=username,
                        email_config=email_config,
                        days_since_activation=days_since_activation
                    )
                    
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
            
            conn.close()
            
            logger.info(f"Processed scheduled emails: {sent_count} sent, {failed_count} failed")
            
        except Exception as e:
            logger.error(f"Error processing scheduled emails: {str(e)}")
        
        return {"sent": sent_count, "failed": failed_count}
    
    def _get_pending_emails(self, user_id: int, days_since_activation: int, 
                           campaign_type: str) -> List[Dict[str, Any]]:
        """Get emails that should be sent for a user"""
        pending = []
        
        campaign = self.campaigns.get(campaign_type, {})
        
        for email_config in campaign.get("emails", []):
            email_day = email_config.get("day")
            
            # Check if this email should be sent today
            if email_day == days_since_activation:
                # Check if already sent
                email_key = f"{user_id}_{email_config['template']}_{email_day}"
                if email_key not in self.sent_emails:
                    # Check send time
                    if self._should_send_now(email_config.get("send_time", "immediate")):
                        pending.append(email_config)
        
        return pending
    
    def _should_send_now(self, send_time: str) -> bool:
        """Check if email should be sent based on send time"""
        if send_time == "immediate":
            return True
        
        try:
            # Parse send time (HH:MM format)
            hour, minute = map(int, send_time.split(":"))
            now = datetime.now()
            send_datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Check if within 30 minutes of send time
            time_diff = abs((now - send_datetime).total_seconds())
            return time_diff <= 1800  # 30 minutes
            
        except Exception:
            return True  # Default to sending if parsing fails
    
    def _send_campaign_email(self, user_id: int, email: str, username: str,
                            email_config: Dict[str, Any], 
                            days_since_activation: int) -> bool:
        """Send a campaign email"""
        try:
            # Get user data
            user_data = self._get_user_email_data(user_id)
            
            # Calculate remaining days
            days_remaining = 30 - days_since_activation
            
            # Prepare template data
            template_data = {
                "username": username,
                "email": email,
                "days_elapsed": days_since_activation,
                "days_remaining": days_remaining,
                "progress_percentage": int((days_since_activation / 30) * 100),
                **user_data
            }
            
            # Send email
            success = self.email_service.send_template_email(
                to_email=email,
                template_name=email_config["template"],
                template_data=template_data,
                subject=email_config["subject"],
                tracking_data={
                    "user_id": user_id,
                    "campaign": "press_pass",
                    "email_type": email_config["template"].replace(".html", ""),
                    "day": email_config["day"]
                }
            )
            
            if success:
                self._record_sent_email(user_id, email_config["template"], email_config["day"])
                logger.info(f"Campaign email sent: {email_config['template']} to user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send campaign email: {str(e)}")
            return False
    
    def _get_user_email_data(self, user_id: int) -> Dict[str, Any]:
        """Get user-specific data for email templates"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get user stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(profit) as total_profit,
                    MAX(profit) as best_trade,
                    AVG(profit) as avg_profit
                FROM trades
                WHERE user_id = ?
            """, (user_id,))
            
            stats = cursor.fetchone()
            
            # Calculate win rate
            win_rate = 0
            if stats[0] > 0:  # total_trades
                win_rate = (stats[1] / stats[0]) * 100
            
            # Get current tier and pricing
            cursor.execute("""
                SELECT pp.tier, u.current_tier
                FROM press_passes pp
                JOIN users u ON pp.user_id = u.id
                WHERE u.id = ?
            """, (user_id,))
            
            tier_data = cursor.fetchone()
            
            conn.close()
            
            return {
                "total_trades": stats[0] or 0,
                "winning_trades": stats[1] or 0,
                "total_profit": f"${stats[2] or 0:.2f}",
                "best_trade": f"${stats[3] or 0:.2f}",
                "avg_profit": f"${stats[4] or 0:.2f}",
                "win_rate": f"{win_rate:.1f}%",
                "current_tier": tier_data[0] if tier_data else "nibbler",
                "next_tier": self._get_next_tier(tier_data[0] if tier_data else "nibbler"),
                "midnight_hammer_profits": "$124.00",  # Example data
                "account_growth": "+8.7%"  # Example data
            }
            
        except Exception as e:
            logger.error(f"Error getting user email data: {str(e)}")
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "total_profit": "$0.00",
                "best_trade": "$0.00",
                "avg_profit": "$0.00",
                "win_rate": "0.0%",
                "current_tier": "nibbler",
                "next_tier": "fang",
                "midnight_hammer_profits": "$0.00",
                "account_growth": "0.0%"
            }
    
    def _get_next_tier(self, current_tier: str) -> str:
        """Get the next tier upgrade"""
        tier_progression = {
            "nibbler": "fang",
            "fang": "commander",
            "commander": "apex",
            "apex": "apex"  # Already at highest
        }
        return tier_progression.get(current_tier, "fang")
    
    def _record_sent_email(self, user_id: int, template: str, day: int):
        """Record that an email was sent"""
        email_key = f"{user_id}_{template}_{day}"
        self.sent_emails[email_key] = datetime.now()
        
        # Also store in database for persistence
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO email_log (user_id, template, campaign_day, sent_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, template, day, datetime.now()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error recording sent email: {str(e)}")
    
    def send_expiry_reminder(self, user_id: int, days_remaining: int) -> bool:
        """Send expiry reminder emails"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT email, username FROM users WHERE id = ?
            """, (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if not user or not user[0]:  # No email
                return False
            
            email, username = user
            
            # Determine which reminder to send
            if days_remaining == 5:
                template = "press_pass_day25.html"
                subject = "🚨 FINAL WARNING: 5 Days Until Press Pass Expires"
            elif days_remaining == 2:
                template = "press_pass_day28.html"
                subject = "⏰ 48 HOURS LEFT - Don't Lose Your Profits!"
            elif days_remaining == 1:
                template = "press_pass_day29.html"
                subject = "🔴 TOMORROW: Everything Changes (Last Chance)"
            else:
                return False
            
            # Get user data
            user_data = self._get_user_email_data(user_id)
            
            # Send reminder
            return self.email_service.send_template_email(
                to_email=email,
                template_name=template,
                template_data={
                    "username": username,
                    "days_remaining": days_remaining,
                    **user_data
                },
                subject=subject,
                tracking_data={
                    "user_id": user_id,
                    "campaign": "press_pass",
                    "email_type": "expiry_reminder",
                    "days_remaining": days_remaining
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending expiry reminder: {str(e)}")
            return False


# Singleton instance
_email_automation = None

def get_email_automation() -> PressPassEmailAutomation:
    """Get singleton email automation instance"""
    global _email_automation
    if _email_automation is None:
        _email_automation = PressPassEmailAutomation()
    return _email_automation