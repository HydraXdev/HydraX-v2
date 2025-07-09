"""
Analytics Configuration for BITTEN
Handles conversion tracking and analytics integration
"""

# Google Analytics
GA_MEASUREMENT_ID = "GA_MEASUREMENT_ID"  # Replace with actual ID

# Facebook Pixel
FB_PIXEL_ID = "YOUR_PIXEL_ID"  # Replace with actual ID

# Conversion Events
CONVERSION_EVENTS = {
    "press_pass_claim": {
        "ga_event": "sign_up",
        "ga_value": 188,  # Value of press pass
        "fb_event": "Lead",
        "fb_value": 188
    },
    "demo_start": {
        "ga_event": "begin_checkout",
        "ga_value": 0,
        "fb_event": "StartTrial",
        "fb_value": 0
    },
    "live_start": {
        "ga_event": "begin_checkout",
        "ga_value": 39,  # Minimum tier value
        "fb_event": "InitiateCheckout",
        "fb_value": 39
    },
    "tier_upgrade": {
        "ga_event": "purchase",
        "fb_event": "Purchase"
    },
    "midnight_hammer_activation": {
        "ga_event": "unlock_achievement",
        "fb_event": "CustomEvent"
    }
}

# UTM Parameters for tracking
UTM_CAMPAIGNS = {
    "press_pass": {
        "source": "landing",
        "medium": "cta",
        "campaign": "press_pass_offer"
    },
    "demo": {
        "source": "landing",
        "medium": "cta",
        "campaign": "demo_trial"
    },
    "live": {
        "source": "landing",
        "medium": "cta",
        "campaign": "live_trading"
    }
}

# A/B Testing Variables
AB_TESTS = {
    "press_pass_urgency": {
        "variants": ["7_spots", "5_spots", "3_spots"],
        "default": "7_spots"
    },
    "countdown_timer": {
        "variants": ["daily_reset", "48_hour", "weekly"],
        "default": "daily_reset"
    },
    "social_proof_numbers": {
        "variants": ["conservative", "moderate", "aggressive"],
        "default": "moderate"
    }
}

# Live Counter Configurations
LIVE_COUNTERS = {
    "active_traders": {
        "base": 2847,
        "variance": 50,
        "update_interval": 300  # 5 minutes
    },
    "trades_today": {
        "base": 18923,
        "increment_range": (5, 15),
        "update_interval": 10  # 10 seconds
    },
    "win_rate": {
        "base": 87.3,
        "variance": 2.0,
        "update_interval": 300  # 5 minutes
    },
    "online_now": {
        "base": 342,
        "variance": 40,
        "minimum": 280,
        "update_interval": 60  # 1 minute
    },
    "spots_remaining": {
        "daily_limit": 10,
        "reset_time": "00:00",  # Midnight UTC
        "decrement_probability": 0.1  # 10% chance per update
    }
}

# Email Campaign Tracking
EMAIL_TRACKING = {
    "press_pass_welcome": {
        "day": 0,
        "subject": "🎖️ Your BITTEN Press Pass is ACTIVE!",
        "track_opens": True,
        "track_clicks": True
    },
    "press_pass_day1": {
        "day": 1,
        "subject": "🎯 Ready for Your First BITTEN Trade?",
        "track_opens": True,
        "track_clicks": True
    },
    "press_pass_day3": {
        "day": 3,
        "subject": "🔨 $124 Made While You Slept (Midnight Hammer Report)",
        "track_opens": True,
        "track_clicks": True
    },
    "press_pass_day7": {
        "day": 7,
        "subject": "📊 Your First Week: +8.7% Growth!",
        "track_opens": True,
        "track_clicks": True
    },
    "press_pass_day14": {
        "day": 14,
        "subject": "⚠️ Your Press Pass is HALF OVER (Special Offer Inside)",
        "track_opens": True,
        "track_clicks": True
    },
    "press_pass_day25": {
        "day": 25,
        "subject": "🚨 FINAL WARNING: 5 Days Until Press Pass Expires",
        "track_opens": True,
        "track_clicks": True
    }
}

# Retargeting Pixels
RETARGETING_CONFIG = {
    "press_pass_abandoners": {
        "delay_hours": 24,
        "audience": "viewed_press_pass_not_claimed"
    },
    "demo_to_live": {
        "delay_days": 7,
        "audience": "demo_users_active_7days"
    },
    "tier_upgrades": {
        "delay_days": 14,
        "audience": "lower_tier_high_usage"
    }
}