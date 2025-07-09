"""
Ammunition Manager for BITTEN
Handles XP-purchased ammunition upgrades like Extended Mag, Rapid Reload, and Special Ammo
"""

from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AmmoType(Enum):
    """Types of ammunition upgrades"""
    EXTENDED_MAG = "extended_mag"      # +2 shots for 24h
    RAPID_RELOAD = "rapid_reload"      # Skip one cooldown
    SPECIAL_AMMO = "special_ammo"      # One 3% risk shot


@dataclass
class AmmoUpgrade:
    """Active ammunition upgrade"""
    upgrade_type: AmmoType
    user_id: str
    activated_at: datetime
    expires_at: Optional[datetime] = None
    uses_remaining: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_active(self) -> bool:
        """Check if upgrade is still active"""
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        if self.uses_remaining is not None and self.uses_remaining <= 0:
            return False
        return True
    
    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining for timed upgrades"""
        if self.expires_at:
            remaining = self.expires_at - datetime.now()
            return remaining if remaining.total_seconds() > 0 else None
        return None


@dataclass
class UserAmmoStatus:
    """User's ammunition status"""
    user_id: str
    extra_shots_today: int = 0          # From extended mag
    cooldowns_skipped_today: int = 0    # From rapid reload
    special_shots_available: int = 0     # From special ammo
    active_upgrades: List[AmmoUpgrade] = field(default_factory=list)
    last_reset: datetime = field(default_factory=datetime.now)


class AmmunitionManager:
    """Manages ammunition upgrades and shot allowances"""
    
    # Base shot limits by tier
    BASE_SHOTS = {
        "NIBBLER": 3,
        "FANG": 5,
        "COMMANDER": 7,
        "APEX": 10
    }
    
    # Upgrade configurations
    UPGRADE_CONFIG = {
        AmmoType.EXTENDED_MAG: {
            "extra_shots": 2,
            "duration_hours": 24,
            "min_tcs": 85,
            "tier_required": "FANG"
        },
        AmmoType.RAPID_RELOAD: {
            "cooldown_skips": 1,
            "daily_limit": 1,
            "tier_required": "NIBBLER"
        },
        AmmoType.SPECIAL_AMMO: {
            "risk_percent": 3,
            "min_tcs": 91,
            "uses": 1,
            "tier_required": "COMMANDER"
        }
    }
    
    def __init__(self, data_dir: str = "data/ammunition"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # User ammo status cache
        self.user_status: Dict[str, UserAmmoStatus] = {}
        
        # Load existing data
        self._load_ammo_data()
    
    def activate_upgrade(
        self, 
        user_id: str, 
        upgrade_type: AmmoType,
        user_tier: str
    ) -> Tuple[bool, str]:
        """Activate an ammunition upgrade after purchase"""
        config = self.UPGRADE_CONFIG[upgrade_type]
        
        # Check tier requirement
        if not self._check_tier_requirement(user_tier, config.get("tier_required", "NIBBLER")):
            return False, f"Requires {config['tier_required']} tier or higher"
        
        # Get or create user status
        if user_id not in self.user_status:
            self.user_status[user_id] = UserAmmoStatus(user_id=user_id)
        
        status = self.user_status[user_id]
        
        # Check if already active
        for upgrade in status.active_upgrades:
            if upgrade.upgrade_type == upgrade_type and upgrade.is_active():
                return False, "Upgrade already active"
        
        # Create upgrade
        if upgrade_type == AmmoType.EXTENDED_MAG:
            upgrade = AmmoUpgrade(
                upgrade_type=upgrade_type,
                user_id=user_id,
                activated_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=config["duration_hours"]),
                metadata={"extra_shots": config["extra_shots"]}
            )
            status.extra_shots_today += config["extra_shots"]
            
        elif upgrade_type == AmmoType.RAPID_RELOAD:
            upgrade = AmmoUpgrade(
                upgrade_type=upgrade_type,
                user_id=user_id,
                activated_at=datetime.now(),
                uses_remaining=config["cooldown_skips"],
                metadata={"daily_limit": config["daily_limit"]}
            )
            
        elif upgrade_type == AmmoType.SPECIAL_AMMO:
            upgrade = AmmoUpgrade(
                upgrade_type=upgrade_type,
                user_id=user_id,
                activated_at=datetime.now(),
                uses_remaining=config["uses"],
                metadata={
                    "risk_percent": config["risk_percent"],
                    "min_tcs": config["min_tcs"]
                }
            )
            status.special_shots_available += config["uses"]
        
        status.active_upgrades.append(upgrade)
        self._save_user_status(user_id)
        
        logger.info(f"Activated {upgrade_type.value} for user {user_id}")
        return True, f"{upgrade_type.value} activated successfully"
    
    def get_shot_allowance(self, user_id: str, user_tier: str) -> Dict[str, Any]:
        """Get user's current shot allowance including upgrades"""
        base_shots = self.BASE_SHOTS.get(user_tier, 3)
        
        # Get user status
        status = self._get_user_status(user_id)
        
        # Clean expired upgrades
        self._clean_expired_upgrades(status)
        
        # Calculate extra shots from active extended mags
        extra_shots = 0
        extended_mag_active = False
        time_remaining = None
        
        for upgrade in status.active_upgrades:
            if upgrade.upgrade_type == AmmoType.EXTENDED_MAG and upgrade.is_active():
                extended_mag_active = True
                time_remaining = upgrade.time_remaining()
                # Extra shots are already added to status.extra_shots_today
                break
        
        total_shots = base_shots + (status.extra_shots_today if extended_mag_active else 0)
        
        return {
            "base_shots": base_shots,
            "extra_shots": status.extra_shots_today if extended_mag_active else 0,
            "total_shots": total_shots,
            "extended_mag_active": extended_mag_active,
            "extended_mag_remaining": str(time_remaining) if time_remaining else None,
            "special_shots_available": status.special_shots_available
        }
    
    def can_skip_cooldown(self, user_id: str) -> Tuple[bool, str]:
        """Check if user can skip a cooldown"""
        status = self._get_user_status(user_id)
        
        # Check daily limit
        if status.cooldowns_skipped_today >= 1:
            return False, "Daily cooldown skip limit reached"
        
        # Check for active rapid reload
        for upgrade in status.active_upgrades:
            if upgrade.upgrade_type == AmmoType.RAPID_RELOAD and upgrade.is_active():
                if upgrade.uses_remaining and upgrade.uses_remaining > 0:
                    return True, "Rapid reload available"
        
        return False, "No rapid reload available"
    
    def use_rapid_reload(self, user_id: str) -> Tuple[bool, str]:
        """Use a rapid reload to skip cooldown"""
        can_skip, reason = self.can_skip_cooldown(user_id)
        if not can_skip:
            return False, reason
        
        status = self.user_status[user_id]
        
        # Find and use rapid reload
        for upgrade in status.active_upgrades:
            if upgrade.upgrade_type == AmmoType.RAPID_RELOAD and upgrade.is_active():
                if upgrade.uses_remaining and upgrade.uses_remaining > 0:
                    upgrade.uses_remaining -= 1
                    status.cooldowns_skipped_today += 1
                    self._save_user_status(user_id)
                    
                    logger.info(f"User {user_id} used rapid reload")
                    return True, "Cooldown skipped!"
        
        return False, "Failed to use rapid reload"
    
    def can_use_special_ammo(
        self, 
        user_id: str, 
        signal_tcs: float
    ) -> Tuple[bool, str, Optional[float]]:
        """Check if user can use special ammo (3% risk)"""
        status = self._get_user_status(user_id)
        
        if status.special_shots_available <= 0:
            return False, "No special ammo available", None
        
        # Check for active special ammo upgrade
        for upgrade in status.active_upgrades:
            if upgrade.upgrade_type == AmmoType.SPECIAL_AMMO and upgrade.is_active():
                min_tcs = upgrade.metadata.get("min_tcs", 91)
                if signal_tcs < min_tcs:
                    return False, f"Requires {min_tcs}% TCS or higher", None
                
                risk_percent = upgrade.metadata.get("risk_percent", 3)
                return True, "Special ammo available", risk_percent
        
        return False, "No special ammo upgrade active", None
    
    def use_special_ammo(self, user_id: str, trade_id: str) -> Tuple[bool, str]:
        """Use special ammo for a trade"""
        status = self._get_user_status(user_id)
        
        if status.special_shots_available <= 0:
            return False, "No special ammo available"
        
        # Find and use special ammo
        for upgrade in status.active_upgrades:
            if upgrade.upgrade_type == AmmoType.SPECIAL_AMMO and upgrade.is_active():
                if upgrade.uses_remaining and upgrade.uses_remaining > 0:
                    upgrade.uses_remaining -= 1
                    status.special_shots_available -= 1
                    
                    # Log usage
                    upgrade.metadata["last_used"] = {
                        "trade_id": trade_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    self._save_user_status(user_id)
                    
                    logger.info(f"User {user_id} used special ammo for trade {trade_id}")
                    return True, "Special ammo activated - 3% risk!"
        
        return False, "Failed to use special ammo"
    
    def get_active_ammo_upgrades(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active ammo upgrades for display"""
        status = self._get_user_status(user_id)
        self._clean_expired_upgrades(status)
        
        active = []
        for upgrade in status.active_upgrades:
            if upgrade.is_active():
                info = {
                    "type": upgrade.upgrade_type.value,
                    "activated_at": upgrade.activated_at.isoformat(),
                    "active": True
                }
                
                if upgrade.expires_at:
                    info["expires_at"] = upgrade.expires_at.isoformat()
                    info["time_remaining"] = str(upgrade.time_remaining())
                
                if upgrade.uses_remaining is not None:
                    info["uses_remaining"] = upgrade.uses_remaining
                
                # Add type-specific info
                if upgrade.upgrade_type == AmmoType.EXTENDED_MAG:
                    info["bonus"] = "+2 shots"
                elif upgrade.upgrade_type == AmmoType.RAPID_RELOAD:
                    info["bonus"] = "Skip cooldown"
                elif upgrade.upgrade_type == AmmoType.SPECIAL_AMMO:
                    info["bonus"] = "3% risk shot"
                
                active.append(info)
        
        return active
    
    def reset_daily_limits(self, user_id: str) -> None:
        """Reset daily usage limits"""
        status = self._get_user_status(user_id)
        
        # Reset daily counters
        status.cooldowns_skipped_today = 0
        
        # Check if extended mag expired
        extended_mag_active = False
        for upgrade in status.active_upgrades:
            if upgrade.upgrade_type == AmmoType.EXTENDED_MAG and upgrade.is_active():
                extended_mag_active = True
                break
        
        if not extended_mag_active:
            status.extra_shots_today = 0
        
        status.last_reset = datetime.now()
        self._save_user_status(user_id)
        
        logger.info(f"Reset daily limits for user {user_id}")
    
    def _get_user_status(self, user_id: str) -> UserAmmoStatus:
        """Get or create user ammo status"""
        if user_id not in self.user_status:
            self.user_status[user_id] = UserAmmoStatus(user_id=user_id)
        
        # Check if needs daily reset
        status = self.user_status[user_id]
        if datetime.now().date() > status.last_reset.date():
            self.reset_daily_limits(user_id)
        
        return status
    
    def _clean_expired_upgrades(self, status: UserAmmoStatus) -> None:
        """Remove expired upgrades"""
        active_upgrades = []
        for upgrade in status.active_upgrades:
            if upgrade.is_active():
                active_upgrades.append(upgrade)
            else:
                logger.info(f"Removed expired {upgrade.upgrade_type.value} for {status.user_id}")
        
        status.active_upgrades = active_upgrades
    
    def _check_tier_requirement(self, user_tier: str, required_tier: str) -> bool:
        """Check if user meets tier requirement"""
        tier_hierarchy = ["NIBBLER", "FANG", "COMMANDER", "APEX"]
        try:
            user_index = tier_hierarchy.index(user_tier)
            required_index = tier_hierarchy.index(required_tier)
            return user_index >= required_index
        except ValueError:
            return False
    
    def _save_user_status(self, user_id: str) -> None:
        """Save user ammo status to file"""
        status = self.user_status[user_id]
        status_file = self.data_dir / f"user_{user_id}_ammo.json"
        
        # Convert to serializable format
        data = {
            "user_id": status.user_id,
            "extra_shots_today": status.extra_shots_today,
            "cooldowns_skipped_today": status.cooldowns_skipped_today,
            "special_shots_available": status.special_shots_available,
            "last_reset": status.last_reset.isoformat(),
            "active_upgrades": []
        }
        
        for upgrade in status.active_upgrades:
            upgrade_data = {
                "upgrade_type": upgrade.upgrade_type.value,
                "activated_at": upgrade.activated_at.isoformat(),
                "expires_at": upgrade.expires_at.isoformat() if upgrade.expires_at else None,
                "uses_remaining": upgrade.uses_remaining,
                "metadata": upgrade.metadata
            }
            data["active_upgrades"].append(upgrade_data)
        
        with open(status_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_ammo_data(self) -> None:
        """Load all user ammo data"""
        for status_file in self.data_dir.glob("user_*_ammo.json"):
            try:
                with open(status_file, 'r') as f:
                    data = json.load(f)
                
                status = UserAmmoStatus(
                    user_id=data["user_id"],
                    extra_shots_today=data["extra_shots_today"],
                    cooldowns_skipped_today=data["cooldowns_skipped_today"],
                    special_shots_available=data["special_shots_available"],
                    last_reset=datetime.fromisoformat(data["last_reset"])
                )
                
                # Load upgrades
                for upgrade_data in data["active_upgrades"]:
                    upgrade = AmmoUpgrade(
                        upgrade_type=AmmoType(upgrade_data["upgrade_type"]),
                        user_id=data["user_id"],
                        activated_at=datetime.fromisoformat(upgrade_data["activated_at"]),
                        expires_at=datetime.fromisoformat(upgrade_data["expires_at"]) if upgrade_data["expires_at"] else None,
                        uses_remaining=upgrade_data["uses_remaining"],
                        metadata=upgrade_data["metadata"]
                    )
                    status.active_upgrades.append(upgrade)
                
                self.user_status[data["user_id"]] = status
                
            except Exception as e:
                logger.error(f"Error loading ammo file {status_file}: {e}")


# Example usage
if __name__ == "__main__":
    manager = AmmunitionManager()
    
    # Activate extended mag
    user_id = "test_user"
    success, message = manager.activate_upgrade(user_id, AmmoType.EXTENDED_MAG, "FANG")
    print(f"Extended mag: {message}")
    
    # Check shot allowance
    allowance = manager.get_shot_allowance(user_id, "FANG")
    print(f"Shot allowance: {allowance}")
    
    # Activate rapid reload
    success, message = manager.activate_upgrade(user_id, AmmoType.RAPID_RELOAD, "FANG")
    print(f"Rapid reload: {message}")
    
    # Try to skip cooldown
    can_skip, reason = manager.can_skip_cooldown(user_id)
    print(f"Can skip cooldown: {can_skip} - {reason}")
    
    if can_skip:
        success, message = manager.use_rapid_reload(user_id)
        print(f"Used rapid reload: {message}")
    
    # Check active upgrades
    active = manager.get_active_ammo_upgrades(user_id)
    print(f"Active upgrades: {active}")