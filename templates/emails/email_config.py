"""
Email Template Configuration for BITTEN Press Pass Campaign
"""

from datetime import datetime, timedelta

class EmailCampaignManager:
    """Manages the Press Pass email campaign sequence"""
    
    def __init__(self):
        self.campaigns = {
            "press_pass": {
                "duration_days": 30,
                "emails": [
                    {
                        "day": 0,
                        "template": "press_pass_welcome.html",
                        "subject": "🎖️ Your BITTEN Press Pass is ACTIVE!",
                        "send_time": "immediate"
                    },
                    {
                        "day": 1,
                        "template": "press_pass_day1.html",
                        "subject": "🎯 Ready for Your First BITTEN Trade?",
                        "send_time": "10:00"
                    },
                    {
                        "day": 3,
                        "template": "press_pass_day3.html",
                        "subject": "🔨 $124 Made While You Slept (Midnight Hammer Report)",
                        "send_time": "08:00"
                    },
                    {
                        "day": 7,
                        "template": "press_pass_day7.html",
                        "subject": "📊 Your First Week: +8.7% Growth!",
                        "send_time": "14:00"
                    },
                    {
                        "day": 14,
                        "template": "press_pass_day14.html",
                        "subject": "⚠️ Your Press Pass is HALF OVER (Special Offer Inside)",
                        "send_time": "10:00"
                    },
                    {
                        "day": 21,
                        "template": "press_pass_day21.html",
                        "subject": "📈 3 Weeks In: Your Results Are INSANE",
                        "send_time": "15:00"
                    },
                    {
                        "day": 25,
                        "template": "press_pass_day25.html",
                        "subject": "🚨 FINAL WARNING: 5 Days Until Press Pass Expires",
                        "send_time": "09:00"
                    },
                    {
                        "day": 28,
                        "template": "press_pass_day28.html",
                        "subject": "⏰ 48 HOURS LEFT - Don't Lose Your Profits!",
                        "send_time": "10:00"
                    },
                    {
                        "day": 29,
                        "template": "press_pass_day29.html",
                        "subject": "🔴 TOMORROW: Everything Changes (Last Chance)",
                        "send_time": "18:00"
                    },
                    {
                        "day": 30,
                        "template": "press_pass_expired.html",
                        "subject": "Your Press Pass Has Expired - Here's What's Next",
                        "send_time": "09:00"
                    }
                ]
            },
            "demo": {
                "emails": [
                    {
                        "day": 0,
                        "template": "demo_welcome.html",
                        "subject": "Welcome to BITTEN Demo Mode",
                        "send_time": "immediate"
                    },
                    {
                        "day": 3,
                        "template": "demo_upgrade.html",
                        "subject": "Ready to Trade with Real Money?",
                        "send_time": "10:00"
                    }
                ]
            }
        }
    
    def get_email_for_day(self, campaign_type, day_number):
        """Get the email template for a specific day in the campaign"""
        if campaign_type not in self.campaigns:
            return None
            
        campaign = self.campaigns[campaign_type]
        for email in campaign.get("emails", []):
            if email["day"] == day_number:
                return email
        return None
    
    def get_pending_emails(self, user_start_date, campaign_type="press_pass"):
        """Get all pending emails for a user based on their start date"""
        if campaign_type not in self.campaigns:
            return []
            
        pending = []
        now = datetime.now()
        campaign = self.campaigns[campaign_type]
        
        for email in campaign.get("emails", []):
            send_date = user_start_date + timedelta(days=email["day"])
            
            # Parse send time
            if email["send_time"] == "immediate":
                send_datetime = send_date
            else:
                hour, minute = map(int, email["send_time"].split(":"))
                send_datetime = send_date.replace(hour=hour, minute=minute)
            
            # Check if email should be sent
            if send_datetime <= now:
                pending.append({
                    "email": email,
                    "send_datetime": send_datetime,
                    "days_since_start": email["day"]
                })
        
        return pending
    
    def get_campaign_status(self, user_start_date, campaign_type="press_pass"):
        """Get the current status of a user's campaign"""
        now = datetime.now()
        days_elapsed = (now - user_start_date).days
        
        campaign = self.campaigns.get(campaign_type, {})
        duration = campaign.get("duration_days", 30)
        
        if days_elapsed > duration:
            return {
                "status": "expired",
                "days_elapsed": days_elapsed,
                "days_remaining": 0,
                "progress_percentage": 100
            }
        else:
            return {
                "status": "active",
                "days_elapsed": days_elapsed,
                "days_remaining": duration - days_elapsed,
                "progress_percentage": int((days_elapsed / duration) * 100)
            }

# Email merge variables
EMAIL_VARIABLES = {
    "username": "User's Telegram username",
    "days_remaining": "Days left in Press Pass",
    "total_profits": "Total profits made so far",
    "win_rate": "User's current win rate",
    "trades_count": "Total number of trades",
    "best_trade": "Best single trade profit",
    "account_growth": "Percentage account growth",
    "midnight_hammer_profits": "Profits from Midnight Hammer",
    "current_tier": "User's current tier",
    "next_tier": "Next available tier",
    "discount_amount": "Discount amount for upgrade",
    "expiry_date": "Press Pass expiry date"
}