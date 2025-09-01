#!/usr/bin/env python3
"""
Simplified Tier-based Exit Manager for NIBBLER, FANG, COMMANDER
Integrates with existing BITTEN system without complex slot management
"""

import toml
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Load tier configuration
TIER_CONFIG_PATH = Path("/root/HydraX-v2/config/tiers.toml")
TIER_CONFIG = toml.load(TIER_CONFIG_PATH) if TIER_CONFIG_PATH.exists() else {}

class TierExitManager:
    """
    Manages exit strategies based on user tier (NIBBLER/FANG/COMMANDER)
    Simplified implementation that works with current system
    """
    
    @staticmethod
    def get_user_tier_from_db(user_id: str) -> str:
        """Get user tier from database based on EA instance"""
        import sqlite3
        try:
            conn = sqlite3.connect('/root/HydraX-v2/bitten.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT target_uuid FROM ea_instances WHERE user_id = ? ORDER BY last_seen DESC LIMIT 1", 
                (user_id,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                target_uuid = result[0]
                # Determine tier based on target_uuid
                if 'COMMANDER' in target_uuid.upper():
                    return 'COMMANDER'
                elif 'FANG' in target_uuid.upper():
                    return 'FANG'
                else:
                    return 'NIBBLER'
            else:
                return 'NIBBLER'  # Default
                
        except Exception as e:
            logger.error(f"Error getting user tier: {e}")
            return 'NIBBLER'
    
    @staticmethod
    def get_exit_config(user_id: str) -> Dict:
        """
        Get exit configuration for user based on their tier
        Returns configuration that can be used in fire commands
        """
        tier = TierExitManager.get_user_tier_from_db(user_id)
        tier_config = TIER_CONFIG.get(tier, TIER_CONFIG.get('NIBBLER', {}))
        
        logger.info(f"User {user_id} tier: {tier}")
        
        # Build exit configuration based on tier
        exit_config = {
            "tier": tier,
            "mode": tier_config.get("MODE", "FIXED")
        }
        
        if tier == "NIBBLER":
            # Simple fixed exit at 1.5R
            exit_config.update({
                "use_partials": False,
                "use_trailing": False,
                "use_be": False,
                "fixed_rr": tier_config.get("RR", 1.5),
                "max_hold_minutes": tier_config.get("MAX_HOLD_MIN", 90)
            })
            
        elif tier in ["FANG", "COMMANDER"]:
            # Scalp core + runner strategy
            exit_config.update({
                "use_partials": True,
                "use_trailing": tier_config.get("TRAIL_ENABLED", True),
                "use_be": True,
                "tp1_r": tier_config.get("TP1_R", 1.5),
                "tp1_close_pct": tier_config.get("TP1_CLOSE_PCT", 0.75),
                "move_be_at": tier_config.get("MOVE_BE_AT", "TP1"),
                "trail_method": tier_config.get("TRAIL_METHOD", "ATR"),
                "trail_step_pips": tier_config.get("TRAIL_STEP_PIPS", 20),
                "max_hold_minutes": tier_config.get("MAX_HOLD_MIN", 90)
            })
            
            # COMMANDER gets autofire
            if tier == "COMMANDER":
                exit_config["autofire_enabled"] = tier_config.get("AUTOFIRE_ENABLED", True)
        
        return exit_config
    
    @staticmethod
    def apply_tier_exit_to_fire_command(fire_command: Dict, user_id: str) -> Dict:
        """
        Apply tier-based exit strategy to a fire command
        Modifies the command to include tier-specific exit parameters
        """
        exit_config = TierExitManager.get_exit_config(user_id)
        tier = exit_config["tier"]
        
        # Add tier information
        fire_command["user_tier"] = tier
        fire_command["exit_mode"] = exit_config["mode"]
        
        if tier == "NIBBLER":
            # Simple fixed target
            # Adjust TP based on fixed R:R
            if "sl" in fire_command and "entry" in fire_command:
                entry = fire_command["entry"]
                sl = fire_command["sl"]
                direction = fire_command.get("direction", "BUY")
                
                # Calculate risk distance
                risk_distance = abs(entry - sl)
                target_distance = risk_distance * exit_config["fixed_rr"]
                
                # Set TP based on direction
                if direction.upper() == "BUY":
                    fire_command["tp"] = round(entry + target_distance, 5)
                else:
                    fire_command["tp"] = round(entry - target_distance, 5)
                
                logger.info(f"NIBBLER: Fixed TP at {exit_config['fixed_rr']}R = {fire_command['tp']}")
            
            # Disable any hybrid features
            fire_command["hybrid"] = None
            
        elif tier in ["FANG", "COMMANDER"]:
            # For FANG/COMMANDER, we want the exit profile system to manage
            # Set a far TP to allow partials and trailing to work
            if "sl" in fire_command and "entry" in fire_command:
                entry = fire_command["entry"]
                sl = fire_command["sl"]
                direction = fire_command.get("direction", "BUY")
                
                # Set TP far away (10R) to let the exit system manage
                risk_distance = abs(entry - sl)
                target_distance = risk_distance * 10  # Far target
                
                if direction.upper() == "BUY":
                    fire_command["tp"] = round(entry + target_distance, 5)
                else:
                    fire_command["tp"] = round(entry - target_distance, 5)
                
                logger.info(f"{tier}: TP set far at 10R for exit management = {fire_command['tp']}")
            
            # Mark that this should use tier-based exit management
            fire_command["use_tier_exits"] = True
            fire_command["exit_config"] = exit_config
        
        return fire_command
    
    @staticmethod
    def should_autofire(user_id: str) -> bool:
        """Check if user can use autofire based on tier"""
        tier = TierExitManager.get_user_tier_from_db(user_id)
        
        # Only COMMANDER can autofire (but unlimited for testing)
        if tier == "COMMANDER":
            logger.info(f"User {user_id} (COMMANDER) can autofire - UNLIMITED for testing")
            return True
        
        return False
    
    @staticmethod
    def get_tier_limits(user_id: str) -> Dict:
        """
        Get tier limits for user
        Returns simplified limits that work with current system
        """
        tier = TierExitManager.get_user_tier_from_db(user_id)
        tier_config = TIER_CONFIG.get(tier, {})
        
        limits = {
            "tier": tier,
            "max_manual_slots": tier_config.get("MAX_MANUAL_SLOTS", 1),
            "max_auto_slots": tier_config.get("MAX_AUTO_SLOTS", 0),
            "max_concurrent": tier_config.get("MAX_CONCURRENT", 1),
            "signal_modes": tier_config.get("SIGNAL_MODES", ["RAPID"]),
# [DISABLED BITMODE]             "can_use_bitmode": tier_config.get("BITMODE_ENABLED", False)
        }
        
        # COMMANDER gets unlimited for testing
        if tier == "COMMANDER":
            limits.update({
                "max_manual_slots": 999,
                "max_auto_slots": 999,
                "max_concurrent": 999,
                "testing_mode": True
            })
        
        return limits

# Helper function to integrate with existing enqueue_fire.py
def enhance_fire_command_with_tier_exits(fire_command: Dict, user_id: str) -> Dict:
    """
    Enhance fire command with tier-based exits
    This can be called from enqueue_fire.py
    """
    return TierExitManager.apply_tier_exit_to_fire_command(fire_command, user_id)