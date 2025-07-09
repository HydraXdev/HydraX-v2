# stealth_protocol.py
# BITTEN Stealth Protocol Implementation - Anti-Detection System

import os
import json
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

class StealthLevel(Enum):
    """Stealth intensity levels"""
    OFF = "off"
    LOW = "low"           # Minimal obfuscation
    MEDIUM = "medium"     # Standard stealth
    HIGH = "high"         # Maximum randomization
    GHOST = "ghost"       # Ultra-stealth mode

@dataclass
class StealthConfig:
    """Stealth protocol configuration"""
    enabled: bool = True
    level: StealthLevel = StealthLevel.MEDIUM
    
    # Entry delay configuration (seconds)
    entry_delay_min: float = 1.0
    entry_delay_max: float = 12.0
    
    # Lot size jitter configuration (percentage)
    lot_jitter_min: float = 0.03  # 3%
    lot_jitter_max: float = 0.07  # 7%
    
    # TP/SL offset configuration (pips)
    tp_offset_min: int = 1
    tp_offset_max: int = 3
    sl_offset_min: int = 1
    sl_offset_max: int = 3
    
    # Ghost skip configuration
    ghost_skip_rate: float = 0.167  # ~1 in 6 trades
    
    # Volume cap configuration
    max_concurrent_per_asset: int = 3
    max_total_concurrent: int = 10
    
    # Execution shuffle configuration
    shuffle_queue: bool = True
    shuffle_delay_min: float = 0.5
    shuffle_delay_max: float = 2.0

@dataclass
class StealthAction:
    """Record of a stealth action for logging"""
    timestamp: datetime
    action_type: str
    original_value: Any
    modified_value: Any
    level: StealthLevel
    details: Dict[str, Any]

class StealthProtocol:
    """Main stealth protocol implementation"""
    
    def __init__(self, config: Optional[StealthConfig] = None):
        self.config = config or StealthConfig()
        self.active_trades: Dict[str, List[str]] = {}  # asset -> [trade_ids]
        self.action_log: List[StealthAction] = []
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup stealth logging mechanism"""
        log_dir = "/root/HydraX-v2/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Create stealth logger
        self.logger = logging.getLogger('stealth_protocol')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        handler = logging.FileHandler(f"{log_dir}/stealth_log.txt")
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    def _log_action(self, action: StealthAction):
        """Log a stealth action"""
        self.action_log.append(action)
        
        # Write to log file
        log_entry = {
            'timestamp': action.timestamp.isoformat(),
            'action_type': action.action_type,
            'original': action.original_value,
            'modified': action.modified_value,
            'level': action.level.value,
            'details': action.details
        }
        
        self.logger.info(json.dumps(log_entry))
        
    def entry_delay(self, trade_params: Dict) -> float:
        """Add randomized entry delay to avoid pattern detection"""
        if not self.config.enabled:
            return 0.0
            
        # Calculate delay based on stealth level
        level_multipliers = {
            StealthLevel.LOW: 0.5,
            StealthLevel.MEDIUM: 1.0,
            StealthLevel.HIGH: 1.5,
            StealthLevel.GHOST: 2.0
        }
        
        multiplier = level_multipliers.get(self.config.level, 1.0)
        
        # Generate cryptographically secure random delay
        delay_range = self.config.entry_delay_max - self.config.entry_delay_min
        random_factor = secrets.randbelow(10000) / 10000.0
        delay = self.config.entry_delay_min + (random_factor * delay_range * multiplier)
        
        # Log the action
        self._log_action(StealthAction(
            timestamp=datetime.now(),
            action_type="entry_delay",
            original_value=0,
            modified_value=delay,
            level=self.config.level,
            details={
                'pair': trade_params.get('symbol', 'UNKNOWN'),
                'delay_seconds': delay
            }
        ))
        
        return delay
        
    def lot_size_jitter(self, original_lot_size: float, pair: str = None) -> float:
        """Apply random variation to lot size"""
        if not self.config.enabled:
            return original_lot_size
            
        # Calculate jitter range based on stealth level
        level_ranges = {
            StealthLevel.LOW: (0.01, 0.03),     # 1-3%
            StealthLevel.MEDIUM: (0.03, 0.07),  # 3-7%
            StealthLevel.HIGH: (0.05, 0.10),    # 5-10%
            StealthLevel.GHOST: (0.07, 0.15)    # 7-15%
        }
        
        jitter_min, jitter_max = level_ranges.get(
            self.config.level, 
            (self.config.lot_jitter_min, self.config.lot_jitter_max)
        )
        
        # Apply jitter
        jitter_range = jitter_max - jitter_min
        random_factor = secrets.randbelow(10000) / 10000.0
        jitter_percent = jitter_min + (random_factor * jitter_range)
        
        # Randomly increase or decrease
        if secrets.randbelow(2) == 0:
            jitter_percent = -jitter_percent
            
        modified_lot = original_lot_size * (1 + jitter_percent)
        
        # Round to appropriate decimal places
        modified_lot = round(modified_lot, 2)
        
        # Log the action
        self._log_action(StealthAction(
            timestamp=datetime.now(),
            action_type="lot_size_jitter",
            original_value=original_lot_size,
            modified_value=modified_lot,
            level=self.config.level,
            details={
                'pair': pair,
                'jitter_percent': jitter_percent * 100,
                'direction': 'increase' if jitter_percent > 0 else 'decrease'
            }
        ))
        
        return modified_lot
        
    def tp_sl_offset(self, tp_price: float, sl_price: float, 
                     pair: str = None) -> Tuple[float, float]:
        """Apply random offset to TP/SL levels"""
        if not self.config.enabled:
            return tp_price, sl_price
            
        # Get pip value for the pair (simplified)
        pip_value = 0.0001 if pair and 'JPY' not in pair else 0.01
        
        # Calculate offsets based on stealth level
        level_multipliers = {
            StealthLevel.LOW: 0.5,
            StealthLevel.MEDIUM: 1.0,
            StealthLevel.HIGH: 1.5,
            StealthLevel.GHOST: 2.0
        }
        
        multiplier = level_multipliers.get(self.config.level, 1.0)
        
        # Generate TP offset
        tp_offset_range = self.config.tp_offset_max - self.config.tp_offset_min
        tp_offset_pips = self.config.tp_offset_min + secrets.randbelow(tp_offset_range + 1)
        tp_offset_pips = int(tp_offset_pips * multiplier)
        
        # Generate SL offset
        sl_offset_range = self.config.sl_offset_max - self.config.sl_offset_min
        sl_offset_pips = self.config.sl_offset_min + secrets.randbelow(sl_offset_range + 1)
        sl_offset_pips = int(sl_offset_pips * multiplier)
        
        # Apply offsets (randomly positive or negative)
        tp_direction = 1 if secrets.randbelow(2) == 0 else -1
        sl_direction = 1 if secrets.randbelow(2) == 0 else -1
        
        modified_tp = tp_price + (tp_offset_pips * pip_value * tp_direction)
        modified_sl = sl_price + (sl_offset_pips * pip_value * sl_direction)
        
        # Log the action
        self._log_action(StealthAction(
            timestamp=datetime.now(),
            action_type="tp_sl_offset",
            original_value={'tp': tp_price, 'sl': sl_price},
            modified_value={'tp': modified_tp, 'sl': modified_sl},
            level=self.config.level,
            details={
                'pair': pair,
                'tp_offset_pips': tp_offset_pips * tp_direction,
                'sl_offset_pips': sl_offset_pips * sl_direction
            }
        ))
        
        return modified_tp, modified_sl
        
    def ghost_skip(self, trade_params: Dict) -> bool:
        """Randomly skip trades to avoid pattern detection"""
        if not self.config.enabled:
            return False
            
        # Adjust skip rate based on stealth level
        level_rates = {
            StealthLevel.LOW: 0.05,      # 5% skip
            StealthLevel.MEDIUM: 0.167,  # ~16.7% skip (1 in 6)
            StealthLevel.HIGH: 0.25,     # 25% skip
            StealthLevel.GHOST: 0.33     # 33% skip
        }
        
        skip_rate = level_rates.get(self.config.level, self.config.ghost_skip_rate)
        
        # Use cryptographically secure random
        should_skip = secrets.randbelow(10000) / 10000.0 < skip_rate
        
        if should_skip:
            self._log_action(StealthAction(
                timestamp=datetime.now(),
                action_type="ghost_skip",
                original_value="EXECUTE",
                modified_value="SKIP",
                level=self.config.level,
                details={
                    'pair': trade_params.get('symbol', 'UNKNOWN'),
                    'skip_rate': skip_rate * 100,
                    'reason': 'stealth_protocol'
                }
            ))
            
        return should_skip
        
    def vol_cap(self, asset: str, trade_id: str) -> bool:
        """Check if trade should be allowed based on volume caps"""
        if not self.config.enabled:
            return True
            
        # Initialize asset tracking if needed
        if asset not in self.active_trades:
            self.active_trades[asset] = []
            
        # Check per-asset limit
        current_asset_trades = len(self.active_trades[asset])
        if current_asset_trades >= self.config.max_concurrent_per_asset:
            self._log_action(StealthAction(
                timestamp=datetime.now(),
                action_type="vol_cap",
                original_value="ALLOW",
                modified_value="DENY",
                level=self.config.level,
                details={
                    'asset': asset,
                    'current_trades': current_asset_trades,
                    'limit': self.config.max_concurrent_per_asset,
                    'reason': 'per_asset_limit'
                }
            ))
            return False
            
        # Check total limit
        total_trades = sum(len(trades) for trades in self.active_trades.values())
        if total_trades >= self.config.max_total_concurrent:
            self._log_action(StealthAction(
                timestamp=datetime.now(),
                action_type="vol_cap",
                original_value="ALLOW",
                modified_value="DENY",
                level=self.config.level,
                details={
                    'asset': asset,
                    'total_trades': total_trades,
                    'limit': self.config.max_total_concurrent,
                    'reason': 'total_limit'
                }
            ))
            return False
            
        # Add trade to tracking
        self.active_trades[asset].append(trade_id)
        return True
        
    def execution_shuffle(self, trade_queue: List[Dict]) -> List[Dict]:
        """Randomize trade execution order"""
        if not self.config.enabled or not self.config.shuffle_queue:
            return trade_queue
            
        if len(trade_queue) <= 1:
            return trade_queue
            
        # Create a copy to avoid modifying original
        shuffled_queue = trade_queue.copy()
        
        # Use secure random shuffle
        for i in range(len(shuffled_queue) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            shuffled_queue[i], shuffled_queue[j] = shuffled_queue[j], shuffled_queue[i]
            
        # Add random delays between trades
        for i, trade in enumerate(shuffled_queue):
            if i > 0:  # Not first trade
                delay_range = self.config.shuffle_delay_max - self.config.shuffle_delay_min
                random_delay = self.config.shuffle_delay_min + (
                    secrets.randbelow(1000) / 1000.0 * delay_range
                )
                trade['shuffle_delay'] = random_delay
                
        # Log the action
        original_order = [t.get('symbol', 'UNKNOWN') for t in trade_queue]
        shuffled_order = [t.get('symbol', 'UNKNOWN') for t in shuffled_queue]
        
        self._log_action(StealthAction(
            timestamp=datetime.now(),
            action_type="execution_shuffle",
            original_value=original_order,
            modified_value=shuffled_order,
            level=self.config.level,
            details={
                'queue_size': len(trade_queue),
                'shuffle_applied': original_order != shuffled_order
            }
        ))
        
        return shuffled_queue
        
    def remove_completed_trade(self, asset: str, trade_id: str):
        """Remove completed trade from tracking"""
        if asset in self.active_trades and trade_id in self.active_trades[asset]:
            self.active_trades[asset].remove(trade_id)
            
    def apply_full_stealth(self, trade_params: Dict) -> Dict:
        """Apply all stealth protocols to a trade"""
        if not self.config.enabled:
            return trade_params
            
        # Create a copy to avoid modifying original
        stealth_params = trade_params.copy()
        
        # 1. Check ghost skip first
        if self.ghost_skip(stealth_params):
            stealth_params['skip_trade'] = True
            return stealth_params
            
        # 2. Check volume cap
        asset = stealth_params.get('symbol', 'UNKNOWN')
        trade_id = stealth_params.get('trade_id', secrets.token_hex(8))
        if not self.vol_cap(asset, trade_id):
            stealth_params['skip_trade'] = True
            stealth_params['skip_reason'] = 'volume_cap'
            return stealth_params
            
        # 3. Apply entry delay
        stealth_params['entry_delay'] = self.entry_delay(stealth_params)
        
        # 4. Apply lot size jitter
        if 'volume' in stealth_params:
            stealth_params['volume'] = self.lot_size_jitter(
                stealth_params['volume'], 
                asset
            )
            
        # 5. Apply TP/SL offset
        if 'tp' in stealth_params and 'sl' in stealth_params:
            stealth_params['tp'], stealth_params['sl'] = self.tp_sl_offset(
                stealth_params['tp'],
                stealth_params['sl'],
                asset
            )
            
        return stealth_params
        
    def get_stealth_stats(self) -> Dict:
        """Get current stealth protocol statistics"""
        stats = {
            'enabled': self.config.enabled,
            'level': self.config.level.value,
            'active_trades': {
                asset: len(trades) 
                for asset, trades in self.active_trades.items()
            },
            'total_active': sum(len(trades) for trades in self.active_trades.values()),
            'actions_logged': len(self.action_log),
            'recent_actions': []
        }
        
        # Get last 10 actions
        for action in self.action_log[-10:]:
            stats['recent_actions'].append({
                'timestamp': action.timestamp.isoformat(),
                'type': action.action_type,
                'level': action.level.value
            })
            
        return stats
        
    def set_level(self, level: StealthLevel):
        """Update stealth level"""
        old_level = self.config.level
        self.config.level = level
        
        self._log_action(StealthAction(
            timestamp=datetime.now(),
            action_type="level_change",
            original_value=old_level.value,
            modified_value=level.value,
            level=level,
            details={
                'changed_by': 'manual',
                'reason': 'user_request'
            }
        ))
        
    def export_logs(self, start_date: Optional[datetime] = None, 
                   end_date: Optional[datetime] = None) -> List[Dict]:
        """Export stealth logs for analysis"""
        logs = []
        
        for action in self.action_log:
            if start_date and action.timestamp < start_date:
                continue
            if end_date and action.timestamp > end_date:
                continue
                
            logs.append({
                'timestamp': action.timestamp.isoformat(),
                'action_type': action.action_type,
                'original': action.original_value,
                'modified': action.modified_value,
                'level': action.level.value,
                'details': action.details
            })
            
        return logs

# Singleton instance
_stealth_protocol = None

def get_stealth_protocol() -> StealthProtocol:
    """Get or create stealth protocol instance"""
    global _stealth_protocol
    if _stealth_protocol is None:
        _stealth_protocol = StealthProtocol()
    return _stealth_protocol