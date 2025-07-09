"""
Test Signal Configuration
Centralized configuration for the 60 TCS test signal system
"""

from typing import Dict, Any


TEST_SIGNAL_CONFIG = {
    # System settings
    "enabled": True,
    "debug_mode": False,  # Set to True to increase frequency for testing
    
    # Timing settings
    "min_days_between": 3,  # Minimum days between test signals
    "max_days_between": 5,  # Maximum days between test signals
    "max_active_per_week": 2,  # Maximum test signals per week
    "min_hours_between_per_user": 72,  # Minimum hours between test signals for same user
    
    # Signal characteristics
    "sl_distance_pips": 60,  # The telltale 60 pip stop loss
    "tp_distance_pips": 20,  # Poor TP for bad risk/reward
    "risk_reward_ratio": 0.33,  # 1:0.33 terrible ratio
    
    # Eligible pairs (most common pairs)
    "eligible_pairs": [
        "EURUSD", 
        "GBPUSD", 
        "USDJPY", 
        "AUDUSD",
        "USDCAD",
        "NZDUSD"
    ],
    
    # Eligible user tiers
    "eligible_tiers": [
        "nibbler",
        "fang", 
        "commander"
        # "apex" users are too experienced, they don't get test signals
    ],
    
    # Special hours when test signals are more likely (UTC)
    "special_hours": [3, 4, 21, 22],  # Early morning and late evening
    
    # User selection
    "user_selection_probability": 0.3,  # 30% chance per eligible user
    
    # Rewards
    "base_xp_pass_reward": 15,  # XP for correctly passing
    "bonus_xp_multiplier": 2,  # Multiplier every 5 correct passes
    "base_xp_win_reward": 50,  # XP for lucky win
    "extra_shots_on_sl": 1,  # Extra shots when hitting SL
    
    # Game mechanics
    "win_probability": 0.30,  # 30% chance to win if taken
    "attention_score_pass_bonus": 5,  # Points added for passing
    "attention_score_fail_penalty": 10,  # Points deducted for taking bait
    
    # Achievements thresholds
    "achievement_thresholds": {
        "sharp_eye": 5,  # Pass 5 test signals
        "master_detector": 20,  # Pass 20 test signals
        "lucky_gambit": 1,  # Win 1 test signal
        "risk_taker": 3,  # Win 3 test signals
    },
    
    # Notification settings
    "send_instant_feedback": True,  # Notify immediately when user acts on test signal
    "show_in_stats": True,  # Show test signal stats in user profile
    "anonymous_leaderboard": True,  # Anonymize user IDs in leaderboard
    
    # Advanced settings
    "adaptive_difficulty": False,  # Adjust frequency based on user performance
    "seasonal_events": True,  # Special test signals during events
    "streak_bonuses": True,  # Extra rewards for consecutive correct passes
}


def get_test_signal_config() -> Dict[str, Any]:
    """Get the current test signal configuration"""
    return TEST_SIGNAL_CONFIG.copy()


def update_test_signal_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update test signal configuration"""
    TEST_SIGNAL_CONFIG.update(updates)
    return TEST_SIGNAL_CONFIG.copy()


def reset_test_signal_config():
    """Reset configuration to defaults"""
    global TEST_SIGNAL_CONFIG
    TEST_SIGNAL_CONFIG = {
        "enabled": True,
        "debug_mode": False,
        "min_days_between": 3,
        "max_days_between": 5,
        "max_active_per_week": 2,
        "min_hours_between_per_user": 72,
        "sl_distance_pips": 60,
        "tp_distance_pips": 20,
        "risk_reward_ratio": 0.33,
        "eligible_pairs": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD"],
        "eligible_tiers": ["nibbler", "fang", "commander"],
        "special_hours": [3, 4, 21, 22],
        "user_selection_probability": 0.3,
        "base_xp_pass_reward": 15,
        "bonus_xp_multiplier": 2,
        "base_xp_win_reward": 50,
        "extra_shots_on_sl": 1,
        "win_probability": 0.30,
        "attention_score_pass_bonus": 5,
        "attention_score_fail_penalty": 10,
        "achievement_thresholds": {
            "sharp_eye": 5,
            "master_detector": 20,
            "lucky_gambit": 1,
            "risk_taker": 3,
        },
        "send_instant_feedback": True,
        "show_in_stats": True,
        "anonymous_leaderboard": True,
        "adaptive_difficulty": False,
        "seasonal_events": True,
        "streak_bonuses": True,
    }


# Debug mode helpers
def enable_debug_mode():
    """Enable debug mode for testing (more frequent test signals)"""
    TEST_SIGNAL_CONFIG.update({
        "debug_mode": True,
        "min_days_between": 0.1,  # Every 2.4 hours minimum
        "max_days_between": 0.2,  # Every 4.8 hours maximum
        "max_active_per_week": 10,  # More test signals
        "min_hours_between_per_user": 2,  # More frequent per user
        "user_selection_probability": 0.8,  # 80% chance in debug
    })


def disable_debug_mode():
    """Disable debug mode and return to normal frequency"""
    TEST_SIGNAL_CONFIG.update({
        "debug_mode": False,
        "min_days_between": 3,
        "max_days_between": 5,
        "max_active_per_week": 2,
        "min_hours_between_per_user": 72,
        "user_selection_probability": 0.3,
    })