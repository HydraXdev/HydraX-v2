"""
Elite Trading Protocols for BITTEN
Advanced trading features unlocked with XP
"""

from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ProtocolType(Enum):
    """Types of elite protocols"""
    TRAILING_GUARD = "trailing_guard"
    SPLIT_COMMAND = "split_command"  
    STEALTH_ENTRY = "stealth_entry"
    FORTRESS_MODE = "fortress_mode"

class ProtocolStatus(Enum):
    """Protocol activation status"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    TRIGGERED = "triggered"
    COMPLETED = "completed"

@dataclass
class TrailingGuardConfig:
    """Configuration for Trailing Guard protocol"""
    activation_profit_pips: int = 20  # Activate after +20 pips
    trail_distance_pips: int = 10    # Trail by 10 pips
    enabled: bool = True

@dataclass
class SplitCommandConfig:
    """Configuration for Split Command protocol"""
    first_target_percent: float = 0.5  # Close 50% at TP1
    breakeven_on_first: bool = True    # Move SL to BE after TP1
    second_target_extra_pips: int = 10  # TP2 is TP1 + 10 pips
    enabled: bool = True

@dataclass
class StealthEntryConfig:
    """Configuration for Stealth Entry protocol"""
    entry_range_pips: int = 5         # ±5 pips from signal
    order_type: str = "limit"         # limit or stop
    expiration_minutes: int = 30      # Pending order expiration
    enabled: bool = True

@dataclass
class FortressModeConfig:
    """Configuration for Fortress Mode protocol"""
    trigger_wins: int = 3             # Activate after 3 wins
    reduced_risk_percent: float = 1.0  # Reduce to 1% risk
    reset_on_loss: bool = True        # Reset counter on loss
    enabled: bool = True

@dataclass
class ActiveProtocol:
    """Tracks an active protocol on a trade"""
    protocol_type: ProtocolType
    trade_id: str
    user_id: str
    status: ProtocolStatus
    activated_at: datetime
    config: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

class EliteProtocolManager:
    """Manages elite trading protocols for users"""
    
    def __init__(self, data_dir: str = "data/elite_protocols"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # User protocol configurations
        self.user_configs: Dict[str, Dict[ProtocolType, Any]] = {}
        
        # Active protocols on trades
        self.active_protocols: Dict[str, List[ActiveProtocol]] = {}
        
        # User win streaks for Fortress Mode
        self.user_streaks: Dict[str, int] = {}
        
        # Load saved data
        self._load_configurations()
    
    def enable_protocol(self, user_id: str, protocol_type: ProtocolType) -> bool:
        """Enable a protocol for a user after they purchase it"""
        if user_id not in self.user_configs:
            self.user_configs[user_id] = {}
        
        # Create default configuration
        if protocol_type == ProtocolType.TRAILING_GUARD:
            config = TrailingGuardConfig()
        elif protocol_type == ProtocolType.SPLIT_COMMAND:
            config = SplitCommandConfig()
        elif protocol_type == ProtocolType.STEALTH_ENTRY:
            config = StealthEntryConfig()
        elif protocol_type == ProtocolType.FORTRESS_MODE:
            config = FortressModeConfig()
        else:
            return False
        
        self.user_configs[user_id][protocol_type] = config
        self._save_user_config(user_id)
        
        logger.info(f"Enabled {protocol_type.value} for user {user_id}")
        return True
    
    def is_protocol_enabled(self, user_id: str, protocol_type: ProtocolType) -> bool:
        """Check if a user has a protocol enabled"""
        if user_id not in self.user_configs:
            return False
        
        config = self.user_configs[user_id].get(protocol_type)
        if not config:
            return False
        
        return getattr(config, 'enabled', False)
    
    def get_protocol_config(
        self, 
        user_id: str, 
        protocol_type: ProtocolType
    ) -> Optional[Any]:
        """Get protocol configuration for a user"""
        if user_id not in self.user_configs:
            return None
        
        return self.user_configs[user_id].get(protocol_type)
    
    def update_protocol_config(
        self, 
        user_id: str, 
        protocol_type: ProtocolType,
        updates: Dict[str, Any]
    ) -> bool:
        """Update protocol configuration"""
        config = self.get_protocol_config(user_id, protocol_type)
        if not config:
            return False
        
        # Update allowed fields
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self._save_user_config(user_id)
        return True
    
    def check_trailing_guard(
        self, 
        user_id: str, 
        trade_id: str,
        current_profit_pips: float,
        current_sl_pips: float
    ) -> Optional[float]:
        """Check if Trailing Guard should adjust stop loss"""
        if not self.is_protocol_enabled(user_id, ProtocolType.TRAILING_GUARD):
            return None
        
        config = self.get_protocol_config(user_id, ProtocolType.TRAILING_GUARD)
        
        # Check if we should activate trailing
        if current_profit_pips >= config.activation_profit_pips:
            # Calculate new SL position
            new_sl_distance = current_profit_pips - config.trail_distance_pips
            
            # Only trail if it improves the SL
            if new_sl_distance > current_sl_pips:
                self._record_protocol_activation(
                    user_id, 
                    trade_id, 
                    ProtocolType.TRAILING_GUARD,
                    {"profit_pips": current_profit_pips, "new_sl": new_sl_distance}
                )
                return new_sl_distance
        
        return None
    
    def check_split_command(
        self, 
        user_id: str, 
        trade_id: str,
        current_profit_pips: float,
        tp1_pips: float
    ) -> Optional[Dict[str, Any]]:
        """Check if Split Command should execute partial close"""
        if not self.is_protocol_enabled(user_id, ProtocolType.SPLIT_COMMAND):
            return None
        
        config = self.get_protocol_config(user_id, ProtocolType.SPLIT_COMMAND)
        
        # Check if we hit TP1
        if current_profit_pips >= tp1_pips:
            # Check if already triggered
            if self._is_protocol_triggered(trade_id, ProtocolType.SPLIT_COMMAND):
                return None
            
            tp2_pips = tp1_pips + config.second_target_extra_pips
            
            action = {
                "close_percent": config.first_target_percent,
                "move_sl_to_breakeven": config.breakeven_on_first,
                "new_tp": tp2_pips,
                "remaining_percent": 1 - config.first_target_percent
            }
            
            self._record_protocol_activation(
                user_id, 
                trade_id, 
                ProtocolType.SPLIT_COMMAND,
                action
            )
            
            return action
        
        return None
    
    def prepare_stealth_entry(
        self, 
        user_id: str, 
        signal_price: float,
        pair: str,
        direction: str  # "buy" or "sell"
    ) -> Optional[List[Dict[str, Any]]]:
        """Prepare stealth entry orders"""
        if not self.is_protocol_enabled(user_id, ProtocolType.STEALTH_ENTRY):
            return None
        
        config = self.get_protocol_config(user_id, ProtocolType.STEALTH_ENTRY)
        
        # Calculate pip value (simplified - needs real implementation)
        pip_value = 0.0001 if "JPY" not in pair else 0.01
        range_price = config.entry_range_pips * pip_value
        
        orders = []
        
        if config.order_type == "limit":
            # Place limit orders at better prices
            if direction == "buy":
                orders.append({
                    "type": "buy_limit",
                    "price": signal_price - range_price,
                    "expiration": datetime.now() + timedelta(minutes=config.expiration_minutes)
                })
            else:
                orders.append({
                    "type": "sell_limit", 
                    "price": signal_price + range_price,
                    "expiration": datetime.now() + timedelta(minutes=config.expiration_minutes)
                })
        else:
            # Place stop orders for momentum entries
            if direction == "buy":
                orders.append({
                    "type": "buy_stop",
                    "price": signal_price + range_price,
                    "expiration": datetime.now() + timedelta(minutes=config.expiration_minutes)
                })
            else:
                orders.append({
                    "type": "sell_stop",
                    "price": signal_price - range_price,
                    "expiration": datetime.now() + timedelta(minutes=config.expiration_minutes)
                })
        
        return orders
    
    def check_fortress_mode(
        self, 
        user_id: str,
        base_risk_percent: float
    ) -> float:
        """Check if Fortress Mode should reduce risk"""
        if not self.is_protocol_enabled(user_id, ProtocolType.FORTRESS_MODE):
            return base_risk_percent
        
        config = self.get_protocol_config(user_id, ProtocolType.FORTRESS_MODE)
        current_streak = self.user_streaks.get(user_id, 0)
        
        # Apply reduced risk if streak threshold met
        if current_streak >= config.trigger_wins:
            logger.info(f"Fortress Mode active for {user_id}: reducing risk to {config.reduced_risk_percent}%")
            return config.reduced_risk_percent
        
        return base_risk_percent
    
    def update_win_streak(self, user_id: str, is_win: bool) -> int:
        """Update user's win streak for Fortress Mode"""
        if is_win:
            self.user_streaks[user_id] = self.user_streaks.get(user_id, 0) + 1
        else:
            # Check if Fortress Mode resets on loss
            if user_id in self.user_configs:
                fortress_config = self.user_configs[user_id].get(ProtocolType.FORTRESS_MODE)
                if fortress_config and fortress_config.reset_on_loss:
                    self.user_streaks[user_id] = 0
        
        self._save_streaks()
        return self.user_streaks.get(user_id, 0)
    
    def get_active_protocols(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active protocols for a user"""
        active = []
        
        if user_id in self.user_configs:
            for protocol_type, config in self.user_configs[user_id].items():
                if getattr(config, 'enabled', False):
                    active.append({
                        "type": protocol_type.value,
                        "config": self._config_to_dict(config),
                        "active_trades": len([
                            p for p in self.active_protocols.get(user_id, [])
                            if p.protocol_type == protocol_type
                        ])
                    })
        
        return active
    
    def _record_protocol_activation(
        self, 
        user_id: str, 
        trade_id: str,
        protocol_type: ProtocolType,
        metadata: Dict[str, Any]
    ) -> None:
        """Record protocol activation"""
        if user_id not in self.active_protocols:
            self.active_protocols[user_id] = []
        
        protocol = ActiveProtocol(
            protocol_type=protocol_type,
            trade_id=trade_id,
            user_id=user_id,
            status=ProtocolStatus.TRIGGERED,
            activated_at=datetime.now(),
            config={},
            metadata=metadata
        )
        
        self.active_protocols[user_id].append(protocol)
        logger.info(f"{protocol_type.value} triggered for trade {trade_id}")
    
    def _is_protocol_triggered(self, trade_id: str, protocol_type: ProtocolType) -> bool:
        """Check if a protocol was already triggered for a trade"""
        for protocols in self.active_protocols.values():
            for protocol in protocols:
                if protocol.trade_id == trade_id and protocol.protocol_type == protocol_type:
                    return True
        return False
    
    def _config_to_dict(self, config: Any) -> Dict[str, Any]:
        """Convert config object to dictionary"""
        result = {}
        for key, value in config.__dict__.items():
            if not key.startswith('_'):
                result[key] = value
        return result
    
    def _save_user_config(self, user_id: str) -> None:
        """Save user configuration to file"""
        config_file = self.data_dir / f"user_{user_id}_protocols.json"
        
        data = {}
        if user_id in self.user_configs:
            for protocol_type, config in self.user_configs[user_id].items():
                data[protocol_type.value] = self._config_to_dict(config)
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_streaks(self) -> None:
        """Save win streaks to file"""
        streaks_file = self.data_dir / "win_streaks.json"
        with open(streaks_file, 'w') as f:
            json.dump(self.user_streaks, f, indent=2)
    
    def _load_configurations(self) -> None:
        """Load saved configurations"""
        # Load user protocols
        for config_file in self.data_dir.glob("user_*_protocols.json"):
            try:
                user_id = config_file.stem.replace("user_", "").replace("_protocols", "")
                with open(config_file, 'r') as f:
                    data = json.load(f)
                
                self.user_configs[user_id] = {}
                for protocol_str, config_data in data.items():
                    protocol_type = ProtocolType(protocol_str)
                    
                    # Recreate config object
                    if protocol_type == ProtocolType.TRAILING_GUARD:
                        config = TrailingGuardConfig(**config_data)
                    elif protocol_type == ProtocolType.SPLIT_COMMAND:
                        config = SplitCommandConfig(**config_data)
                    elif protocol_type == ProtocolType.STEALTH_ENTRY:
                        config = StealthEntryConfig(**config_data)
                    elif protocol_type == ProtocolType.FORTRESS_MODE:
                        config = FortressModeConfig(**config_data)
                    
                    self.user_configs[user_id][protocol_type] = config
                    
            except Exception as e:
                logger.error(f"Error loading config {config_file}: {e}")
        
        # Load win streaks
        streaks_file = self.data_dir / "win_streaks.json"
        if streaks_file.exists():
            try:
                with open(streaks_file, 'r') as f:
                    self.user_streaks = json.load(f)
            except Exception as e:
                logger.error(f"Error loading streaks: {e}")

# Example usage
if __name__ == "__main__":
    manager = EliteProtocolManager()
    
    # Enable protocols for a user
    user_id = "test_user"
    manager.enable_protocol(user_id, ProtocolType.TRAILING_GUARD)
    manager.enable_protocol(user_id, ProtocolType.SPLIT_COMMAND)
    
    # Check trailing guard
    new_sl = manager.check_trailing_guard(user_id, "trade_123", 25.0, 10.0)
    if new_sl:
        print(f"Trail SL to: {new_sl} pips")
    
    # Check split command
    split_action = manager.check_split_command(user_id, "trade_456", 15.0, 15.0)
    if split_action:
        print(f"Split command: {split_action}")
    
    # Update win streak
    manager.update_win_streak(user_id, True)
    manager.update_win_streak(user_id, True)
    manager.update_win_streak(user_id, True)
    
    # Check fortress mode
    risk = manager.check_fortress_mode(user_id, 2.0)
    print(f"Adjusted risk: {risk}%")