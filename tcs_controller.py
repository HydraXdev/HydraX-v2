#!/usr/bin/env python3
"""
🎯 TCS Controller - Centralized Threshold Management
Provides single source of truth for TCS thresholds across the entire system
"""

from throttle_controller import VenomThrottleController
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Global throttle controller instance
_throttle_controller = None

def get_throttle_controller():
    """Get or create the singleton throttle controller instance"""
    global _throttle_controller
    if _throttle_controller is None:
        _throttle_controller = VenomThrottleController()
        logger.info(f"🎯 TCS Controller initialized with throttle controller")
    return _throttle_controller

def get_current_threshold():
    """
    Get the current TCS threshold value
    Returns: float - The current TCS threshold (e.g., 70.0)
    """
    controller = get_throttle_controller()
    tcs_threshold, _ = controller.get_current_thresholds()
    return tcs_threshold

def get_current_thresholds():
    """
    Get both TCS and ML thresholds
    Returns: tuple(float, float) - (tcs_threshold, ml_threshold)
    """
    controller = get_throttle_controller()
    return controller.get_current_thresholds()

def should_fire_signal(tcs_score, ml_score=0.0):
    """
    Check if a signal should fire based on current thresholds
    Args:
        tcs_score: float - The TCS score to check
        ml_score: float - The ML score to check (optional)
    Returns: bool - Whether the signal should fire
    """
    controller = get_throttle_controller()
    return controller.should_fire_signal(tcs_score, ml_score)

def get_threshold_state():
    """
    Get current governor state and thresholds
    Returns: dict with state info
    """
    controller = get_throttle_controller()
    tcs, ml = controller.get_current_thresholds()
    return {
        'tcs_threshold': tcs,
        'ml_threshold': ml,
        'governor_state': controller.current_settings.governor_state,
        'signals_fired': controller.current_settings.signals_fired_count
    }

# Convenience function for backward compatibility
def get_tcs_threshold():
    """Alias for get_current_threshold()"""
    return get_current_threshold()

if __name__ == "__main__":
    # Test the controller
    threshold = get_current_threshold()
    print(f"Current TCS threshold: {threshold}")
    
    state = get_threshold_state()
    print(f"Current state: {state}")
    
    # Test signal firing
    test_scores = [65, 70, 75, 80, 85, 90]
    for score in test_scores:
        should_fire = should_fire_signal(score)
        print(f"TCS {score}: {'FIRE' if should_fire else 'HOLD'}")