"""
🛡️ BITTEN Risk Control Module

Enforces tier-based risk limits, cooldowns, and capital preservation.
This is BITTEN's capital protection firewall.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Optional, Tuple, List
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class RiskMode(Enum):
    """User's selected risk mode"""
    DEFAULT = "default"      # Base risk for tier
    BOOST = "boost"         # 1.5x for NIBBLER
    HIGH_RISK = "high_risk" # 2.0% for FANG+

class TierLevel(Enum):
    """BITTEN tier levels"""
    NIBBLER = "NIBBLER"
    FANG = "FANG"
    COMMANDER = "COMMANDER"
    = @dataclass
class TierRiskConfig:
    """Risk configuration per tier"""
    tier: TierLevel
    default_risk: float          # Base risk percentage
    boost_risk: Optional[float]  # Optional higher risk mode
    max_trades_per_day: int
    drawdown_cap: float         # Daily loss limit
    cooldown_hours: int         # Cooldown duration
    cooldown_max_trades: int    # Max trades during cooldown
    cooldown_risk: float        # Risk during cooldown

# Tier configurations as per spec
TIER_CONFIGS = {
    TierLevel.NIBBLER: TierRiskConfig(
        tier=TierLevel.NIBBLER,
        default_risk=1.0,
        boost_risk=1.5,
        max_trades_per_day=6,
        drawdown_cap=6.0,
        cooldown_hours=6,
        cooldown_max_trades=6,  # Normal during cooldown
        cooldown_risk=1.0
    ),
    TierLevel.FANG: TierRiskConfig(
        tier=TierLevel.FANG,
        default_risk=1.25,
        boost_risk=2.0,
        max_trades_per_day=10,
        drawdown_cap=8.5,
        cooldown_hours=4,
        cooldown_max_trades=4,
        cooldown_risk=1.0
    ),
    TierLevel.COMMANDER: TierRiskConfig(
        tier=TierLevel.COMMANDER,
        default_risk=1.25,
        boost_risk=2.0,
        max_trades_per_day=10,
        drawdown_cap=8.5,
        cooldown_hours=4,
        cooldown_max_trades=4,
        cooldown_risk=1.0
    ),
    TierLevel.: TierRiskConfig(
        tier=TierLevel.default_risk=1.25,
        boost_risk=2.0,
        max_trades_per_day=10,
        drawdown_cap=8.5,
        cooldown_hours=4,
        cooldown_max_trades=4,
        cooldown_risk=1.0
    )
}

@dataclass
class CooldownState:
    """User's cooldown state"""
    user_id: int
    activated_at: datetime
    expires_at: datetime
    trigger_reason: str
    consecutive_losses: int
    loss_amounts: List[float]

@dataclass
class UserRiskProfile:
    """User's risk profile and settings"""
    user_id: int
    tier: TierLevel
    risk_mode: RiskMode = RiskMode.DEFAULT
    daily_trades: int = 0
    daily_loss: float = 0.0
    last_trade_date: Optional[str] = None
    consecutive_high_risk_losses: int = 0
    last_loss_amounts: List[float] = None
    
    def __post_init__(self):
        if self.last_loss_amounts is None:
            self.last_loss_amounts = []

class RiskController:
    """
    Central risk management controller enforcing tier-based limits.
    This is the final authority on risk decisions.
    """
    
    def __init__(self, data_dir: str = "/root/HydraX-v2/data/risk_control"):
        self.data_dir = data_dir
        self.cooldown_file = os.path.join(data_dir, "cooldown_state.json")
        self.profile_file = os.path.join(data_dir, "risk_profiles.json")
        self._lock = Lock()
        
        # Create data directory if needed
        os.makedirs(data_dir, exist_ok=True)
        
        # Load persisted state
        self.cooldowns: Dict[int, CooldownState] = self._load_cooldowns()
        self.profiles: Dict[int, UserRiskProfile] = self._load_profiles()
    
    def get_user_risk_percent(self, user_id: int, tier: TierLevel) -> Tuple[float, str]:
        """
        Get user's current allowed risk percentage.
        
        Returns:
            Tuple of (risk_percent, reason)
        """
        with self._lock:
            # Get or create profile
            profile = self._get_or_create_profile(user_id, tier)
            
            # Check if in cooldown
            if self._is_in_cooldown(user_id):
                cooldown = self.cooldowns[user_id]
                config = TIER_CONFIGS[tier]
                return config.cooldown_risk, f"Cooldown active until {cooldown.expires_at.strftime('%H:%M UTC')}"
            
            # Get tier config
            config = TIER_CONFIGS[tier]
            
            # Return appropriate risk based on mode
            if profile.risk_mode == RiskMode.BOOST and config.boost_risk:
                return config.boost_risk, f"{tier.value} boost mode"
            elif profile.risk_mode == RiskMode.HIGH_RISK and config.boost_risk:
                return config.boost_risk, f"{tier.value} high-risk mode"
            else:
                return config.default_risk, f"{tier.value} default mode"
    
    def check_trade_allowed(self, user_id: int, tier: TierLevel, 
                          potential_loss: float, account_balance: float) -> Tuple[bool, str]:
        """
        Check if a trade is allowed based on all risk rules.
        
        Args:
            user_id: User ID
            tier: User's tier
            potential_loss: Potential loss amount (positive number)
            account_balance: Current account balance
            
        Returns:
            Tuple of (allowed, reason)
        """
        with self._lock:
            profile = self._get_or_create_profile(user_id, tier)
            config = TIER_CONFIGS[tier]
            
            # Reset daily counters if new day
            self._check_daily_reset(profile)
            
            # Check daily trade limit
            max_trades = config.max_trades_per_day
            if self._is_in_cooldown(user_id):
                max_trades = config.cooldown_max_trades
            
            if profile.daily_trades >= max_trades:
                return False, f"Daily trade limit reached ({max_trades} trades)"
            
            # Check drawdown limit
            potential_daily_loss = profile.daily_loss + potential_loss
            potential_loss_percent = (potential_daily_loss / account_balance) * 100
            
            if potential_loss_percent > config.drawdown_cap:
                return False, f"Would exceed {config.drawdown_cap}% daily drawdown limit"
            
            # Check if cooldown prevents high-risk trades
            if self._is_in_cooldown(user_id) and profile.risk_mode != RiskMode.DEFAULT:
                return False, "High-risk trades blocked during cooldown"
            
            return True, "Trade allowed"
    
    def record_trade_result(self, user_id: int, tier: TierLevel, 
                          won: bool, pnl: float, risk_percent: float):
        """
        Record trade result and check for cooldown triggers.
        
        Args:
            user_id: User ID
            tier: User's tier
            won: Whether trade was profitable
            pnl: Profit/loss amount (negative for losses)
            risk_percent: Risk percentage used
        """
        with self._lock:
            profile = self._get_or_create_profile(user_id, tier)
            config = TIER_CONFIGS[tier]
            
            # Update daily stats
            profile.daily_trades += 1
            if pnl < 0:
                profile.daily_loss += abs(pnl)
            
            # Track high-risk losses for cooldown trigger
            if not won and risk_percent >= 1.5:  # High risk threshold
                profile.consecutive_high_risk_losses += 1
                profile.last_loss_amounts.append(abs(pnl))
                
                # Keep only last 2 losses
                if len(profile.last_loss_amounts) > 2:
                    profile.last_loss_amounts = profile.last_loss_amounts[-2:]
                
                # Check cooldown trigger
                if (profile.consecutive_high_risk_losses >= 2 and 
                    not self._is_in_cooldown(user_id)):
                    self._activate_cooldown(user_id, tier, 
                                          "2 consecutive high-risk losses",
                                          profile.consecutive_high_risk_losses,
                                          profile.last_loss_amounts)
                    # Force default mode
                    profile.risk_mode = RiskMode.DEFAULT
            elif won:
                # Reset loss tracking on win
                profile.consecutive_high_risk_losses = 0
                profile.last_loss_amounts = []
                
                # Check XP-based recovery if in cooldown
                if self._is_in_cooldown(user_id):
                    # Recovery logic would check XP here
                    # For now, just log
                    logger.info(f"User {user_id} won trade during cooldown")
            
            # Save state
            self._save_profiles()
    
    def toggle_risk_mode(self, user_id: int, tier: TierLevel, 
                        new_mode: RiskMode) -> Tuple[bool, str]:
        """
        Toggle user's risk mode with validation.
        
        Returns:
            Tuple of (success, message)
        """
        with self._lock:
            profile = self._get_or_create_profile(user_id, tier)
            config = TIER_CONFIGS[tier]
            
            # Check if in cooldown
            if self._is_in_cooldown(user_id):
                return False, "Cannot change risk mode during cooldown"
            
            # Validate mode for tier
            if new_mode in [RiskMode.BOOST, RiskMode.HIGH_RISK]:
                if not config.boost_risk:
                    return False, f"{tier.value} tier does not support {new_mode.value}"
                
                # NIBBLER can only use BOOST
                if tier == TierLevel.NIBBLER and new_mode == RiskMode.HIGH_RISK:
                    return False, "NIBBLER tier limited to boost mode (1.5%)"
            
            # Update mode
            old_mode = profile.risk_mode
            profile.risk_mode = new_mode
            self._save_profiles()
            
            # Get new risk percentage
            risk_percent, _ = self.get_user_risk_percent(user_id, tier)
            
            return True, f"Risk mode changed from {old_mode.value} to {new_mode.value} ({risk_percent}%)"
    
    def get_user_status(self, user_id: int, tier: TierLevel, 
                       account_balance: float) -> Dict:
        """Get comprehensive user risk status"""
        with self._lock:
            profile = self._get_or_create_profile(user_id, tier)
            config = TIER_CONFIGS[tier]
            
            # Calculate current drawdown
            current_drawdown = 0.0
            if account_balance > 0:
                current_drawdown = (profile.daily_loss / account_balance) * 100
            
            # Get current risk
            risk_percent, risk_reason = self.get_user_risk_percent(user_id, tier)
            
            # Check cooldown
            cooldown_info = None
            if self._is_in_cooldown(user_id):
                cooldown = self.cooldowns[user_id]
                cooldown_info = {
                    'active': True,
                    'expires_at': cooldown.expires_at.isoformat(),
                    'time_remaining': str(cooldown.expires_at - datetime.now(timezone.utc)),
                    'reason': cooldown.trigger_reason
                }
            
            return {
                'user_id': user_id,
                'tier': tier.value,
                'risk_mode': profile.risk_mode.value,
                'current_risk_percent': risk_percent,
                'risk_reason': risk_reason,
                'daily_trades': profile.daily_trades,
                'max_daily_trades': config.cooldown_max_trades if cooldown_info else config.max_trades_per_day,
                'daily_loss': profile.daily_loss,
                'daily_drawdown_percent': current_drawdown,
                'drawdown_limit': config.drawdown_cap,
                'consecutive_high_risk_losses': profile.consecutive_high_risk_losses,
                'cooldown': cooldown_info
            }
    
    def _is_in_cooldown(self, user_id: int) -> bool:
        """Check if user is in cooldown"""
        if user_id not in self.cooldowns:
            return False
        
        cooldown = self.cooldowns[user_id]
        if datetime.now(timezone.utc) >= cooldown.expires_at:
            # Cooldown expired, remove it
            del self.cooldowns[user_id]
            self._save_cooldowns()
            return False
        
        return True
    
    def _activate_cooldown(self, user_id: int, tier: TierLevel, 
                          reason: str, consecutive_losses: int, 
                          loss_amounts: List[float]):
        """Activate cooldown for user"""
        config = TIER_CONFIGS[tier]
        now = datetime.now(timezone.utc)
        
        cooldown = CooldownState(
            user_id=user_id,
            activated_at=now,
            expires_at=now + timedelta(hours=config.cooldown_hours),
            trigger_reason=reason,
            consecutive_losses=consecutive_losses,
            loss_amounts=loss_amounts
        )
        
        self.cooldowns[user_id] = cooldown
        self._save_cooldowns()
        
        logger.warning(f"Cooldown activated for user {user_id}: {reason}")
    
    def _get_or_create_profile(self, user_id: int, tier: TierLevel) -> UserRiskProfile:
        """Get or create user profile"""
        if user_id not in self.profiles:
            self.profiles[user_id] = UserRiskProfile(
                user_id=user_id,
                tier=tier
            )
            self._save_profiles()
        
        # Update tier if changed
        profile = self.profiles[user_id]
        if profile.tier != tier:
            profile.tier = tier
            self._save_profiles()
        
        return profile
    
    def _check_daily_reset(self, profile: UserRiskProfile):
        """Reset daily counters if new day"""
        today = datetime.now(timezone.utc).date().isoformat()
        
        if profile.last_trade_date != today:
            profile.daily_trades = 0
            profile.daily_loss = 0.0
            profile.last_trade_date = today
            # Don't reset consecutive losses or cooldown
    
    def reset_all_daily_counters(self):
        """Reset all users' daily counters (for cron job)"""
        with self._lock:
            for profile in self.profiles.values():
                profile.daily_trades = 0
                profile.daily_loss = 0.0
            self._save_profiles()
            logger.info("Reset all daily counters")
    
    def _load_cooldowns(self) -> Dict[int, CooldownState]:
        """Load cooldown states from file"""
        if not os.path.exists(self.cooldown_file):
            return {}
        
        try:
            with open(self.cooldown_file, 'r') as f:
                data = json.load(f)
            
            cooldowns = {}
            for user_id_str, cooldown_data in data.items():
                cooldown = CooldownState(
                    user_id=int(user_id_str),
                    activated_at=datetime.fromisoformat(cooldown_data['activated_at']),
                    expires_at=datetime.fromisoformat(cooldown_data['expires_at']),
                    trigger_reason=cooldown_data['trigger_reason'],
                    consecutive_losses=cooldown_data['consecutive_losses'],
                    loss_amounts=cooldown_data['loss_amounts']
                )
                cooldowns[int(user_id_str)] = cooldown
            
            return cooldowns
        except Exception as e:
            logger.error(f"Error loading cooldowns: {e}")
            return {}
    
    def _save_cooldowns(self):
        """Save cooldown states to file"""
        data = {}
        for user_id, cooldown in self.cooldowns.items():
            data[str(user_id)] = {
                'activated_at': cooldown.activated_at.isoformat(),
                'expires_at': cooldown.expires_at.isoformat(),
                'trigger_reason': cooldown.trigger_reason,
                'consecutive_losses': cooldown.consecutive_losses,
                'loss_amounts': cooldown.loss_amounts
            }
        
        try:
            with open(self.cooldown_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cooldowns: {e}")
    
    def _load_profiles(self) -> Dict[int, UserRiskProfile]:
        """Load user profiles from file"""
        if not os.path.exists(self.profile_file):
            return {}
        
        try:
            with open(self.profile_file, 'r') as f:
                data = json.load(f)
            
            profiles = {}
            for user_id_str, profile_data in data.items():
                profile = UserRiskProfile(
                    user_id=int(user_id_str),
                    tier=TierLevel(profile_data['tier']),
                    risk_mode=RiskMode(profile_data.get('risk_mode', 'default')),
                    daily_trades=profile_data.get('daily_trades', 0),
                    daily_loss=profile_data.get('daily_loss', 0.0),
                    last_trade_date=profile_data.get('last_trade_date'),
                    consecutive_high_risk_losses=profile_data.get('consecutive_high_risk_losses', 0),
                    last_loss_amounts=profile_data.get('last_loss_amounts', [])
                )
                profiles[int(user_id_str)] = profile
            
            return profiles
        except Exception as e:
            logger.error(f"Error loading profiles: {e}")
            return {}
    
    def _save_profiles(self):
        """Save user profiles to file"""
        data = {}
        for user_id, profile in self.profiles.items():
            data[str(user_id)] = {
                'tier': profile.tier.value,
                'risk_mode': profile.risk_mode.value,
                'daily_trades': profile.daily_trades,
                'daily_loss': profile.daily_loss,
                'last_trade_date': profile.last_trade_date,
                'consecutive_high_risk_losses': profile.consecutive_high_risk_losses,
                'last_loss_amounts': profile.last_loss_amounts
            }
        
        try:
            with open(self.profile_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving profiles: {e}")

# Global instance for easy access
_risk_controller: Optional[RiskController] = None

def get_risk_controller() -> RiskController:
    """Get or create the global risk controller instance"""
    global _risk_controller
    if _risk_controller is None:
        _risk_controller = RiskController()
    return _risk_controller