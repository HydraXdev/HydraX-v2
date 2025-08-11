#!/usr/bin/env python3
"""
BITTEN Trading Guardrails - Central Risk Management and Game Rules
Enforces tier-based limits, position sizing, and risk management
"""

import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass, field
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# Tier configuration with signal class access
TIER_HIERARCHY = {
    "PRESS_PASS": {
        "price": 0,
        "daily_trades": 3,
        "max_positions": 1,
        "risk_per_trade": 0.02,  # 2% locked
        "max_daily_loss": 0.06,  # 6% daily drawdown limit
        "fire_slots": 1,
        "fire_mode": "manual",
        "signal_delay": 60,
        "signal_access": ["RAPID"],  # Only RAPID signals
        "risk_reward": 1.5
    },
    "NIBBLER": {
        "price": 39,
        "daily_trades": 6,
        "max_positions": 3,
        "risk_per_trade": 0.02,  # 2% locked
        "max_daily_loss": 0.06,  # 6% daily drawdown limit
        "fire_slots": 1,
        "fire_mode": "manual",
        "signal_delay": 0,
        "signal_access": ["RAPID"],  # Only RAPID signals
        "risk_reward": 1.5
    },
    "FANG": {
        "price": 79,
        "daily_trades": 10,
        "max_positions": 6,
        "risk_per_trade": 0.02,  # 2% locked (future: user selectable)
        "max_daily_loss": 0.085, # 8.5% daily drawdown limit
        "fire_slots": 2,
        "fire_mode": "select",
        "signal_delay": 0,
        "signal_access": ["RAPID", "SNIPER"],  # Both signal types
        "risk_reward": "DYNAMIC"  # Based on signal class
    },
    "COMMANDER": {
        "price": 139,
        "daily_trades": 20,
        "max_positions": 10,
        "risk_per_trade": 0.02,  # 2% locked (future: user selectable)
        "max_daily_loss": 0.10,  # 10% daily drawdown limit
        "fire_slots": 3,
        "fire_mode": "auto",
        "signal_delay": 0,
        "signal_access": ["RAPID", "SNIPER"],  # Both signal types
        "risk_reward": "DYNAMIC"  # Based on signal class
    }
}

# Signal class definitions
SIGNAL_CLASSES = {
    "RAPID": {
        "risk_reward": 1.5,  # 1:1.5 RR (risk 2% to make 3%)
        "typical_sl": 15,    # Smaller stops
        "typical_tp": 23,    # 15 * 1.5 = ~23 pips
        "description": "Quick scalps with tighter targets"
    },
    "SNIPER": {
        "risk_reward": 2.0,  # 1:2 RR (risk 2% to make 4%)
        "typical_sl": 20,    # Standard stops
        "typical_tp": 40,    # 20 * 2 = 40 pips
        "description": "Precision shots with better reward"
    }
}

# Pip values for position sizing (approximate)
PIP_VALUES = {
    "EURUSD": 10,
    "GBPUSD": 10,
    "USDJPY": 9,
    "USDCHF": 10,
    "AUDUSD": 10,
    "USDCAD": 10,
    "NZDUSD": 10,
    "EURJPY": 9,
    "GBPJPY": 9,
    "EURGBP": 10,
    "XAUUSD": 1,
    "XAGUSD": 0.5,
    "BTCUSD": 0.1,
    "ETHUSD": 0.01,
    "XRPUSD": 0.001
}

@dataclass
class TradingPermission:
    """Result of can_user_trade check"""
    allowed: bool
    reason: Optional[str] = None
    checks: Dict[str, bool] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TradeParameters:
    """Calculated trade parameters"""
    lot_size: float
    sl_pips: int
    tp_pips: int
    risk_amount: float
    potential_profit: float
    risk_reward: float
    signal_class: str

class TradingGuardrails:
    """Central trading rules enforcement and risk management"""
    
    def __init__(self, db_path: str = "/root/HydraX-v2/data/trading_guardrails.db"):
        self.db_path = db_path
        self.init_database()
        logger.info("Trading Guardrails initialized")
    
    def init_database(self):
        """Initialize database tables for tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Daily trading stats (resets at midnight UTC)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_trading_stats (
                user_id TEXT,
                date DATE,
                trades_count INTEGER DEFAULT 0,
                starting_balance REAL,
                current_balance REAL,
                daily_pnl REAL DEFAULT 0,
                daily_loss_percent REAL DEFAULT 0,
                consecutive_losses INTEGER DEFAULT 0,
                last_trade_time TIMESTAMP,
                cooldown_until TIMESTAMP,
                PRIMARY KEY (user_id, date)
            )
        ''')
        
        # Open positions tracker
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS open_positions (
                position_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                signal_id TEXT,
                symbol TEXT,
                direction TEXT,
                lot_size REAL,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                pnl REAL,
                status TEXT DEFAULT 'OPEN'
            )
        ''')
        
        # Risk violations audit
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_violations (
                violation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                violation_type TEXT,
                details TEXT,
                blocked_signal_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_position_size(
        self,
        balance: float,
        signal: Dict,
        tier: str
    ) -> TradeParameters:
        """
        Calculate position size based on 2% risk and signal class
        """
        # Get tier configuration
        tier_config = TIER_HIERARCHY.get(tier, TIER_HIERARCHY["NIBBLER"])
        
        # Fixed 2% risk for now
        risk_percent = tier_config["risk_per_trade"]
        risk_amount = balance * risk_percent
        
        # Get signal class and determine RR
        signal_class = signal.get("class", "RAPID")
        if signal_class not in SIGNAL_CLASSES:
            signal_class = "RAPID"
        
        signal_config = SIGNAL_CLASSES[signal_class]
        risk_reward = signal_config["risk_reward"]
        
        # Get stop loss from signal or use default
        stop_loss_pips = signal.get("sl_pips", signal_config["typical_sl"])
        
        # Get pip value for symbol
        symbol = signal.get("symbol", "EURUSD")
        pip_value = PIP_VALUES.get(symbol, 10)
        
        # Calculate lot size: Risk Amount / (Stop Loss in Pips × Pip Value)
        if stop_loss_pips > 0 and pip_value > 0:
            lot_size = risk_amount / (stop_loss_pips * pip_value)
        else:
            lot_size = 0.01  # Minimum lot size
        
        # Apply reasonable limits
        lot_size = max(0.01, min(lot_size, 5.0))
        
        # Calculate TP based on RR
        take_profit_pips = int(stop_loss_pips * risk_reward)
        
        return TradeParameters(
            lot_size=round(lot_size, 2),
            sl_pips=stop_loss_pips,
            tp_pips=take_profit_pips,
            risk_amount=risk_amount,
            potential_profit=risk_amount * risk_reward,
            risk_reward=risk_reward,
            signal_class=signal_class
        )
    
    def check_daily_trade_limit(self, user_id: str, tier: str) -> Tuple[bool, int, int]:
        """
        Check if user has reached daily trade limit
        Returns: (can_trade, trades_used, trades_allowed)
        """
        tier_config = TIER_HIERARCHY.get(tier, TIER_HIERARCHY["NIBBLER"])
        daily_limit = tier_config["daily_trades"]
        
        # Get today's date in UTC
        today = datetime.now(timezone.utc).date()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get or create today's stats
        cursor.execute('''
            SELECT trades_count FROM daily_trading_stats
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        result = cursor.fetchone()
        trades_today = result[0] if result else 0
        
        conn.close()
        
        can_trade = trades_today < daily_limit
        return can_trade, trades_today, daily_limit
    
    def check_daily_loss_limit(self, user_id: str, tier: str, current_balance: float) -> Tuple[bool, float]:
        """
        Check if user has exceeded daily loss limit
        Returns: (can_trade, daily_loss_percent)
        """
        tier_config = TIER_HIERARCHY.get(tier, TIER_HIERARCHY["NIBBLER"])
        max_daily_loss = tier_config["max_daily_loss"]
        
        today = datetime.now(timezone.utc).date()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get today's starting balance
        cursor.execute('''
            SELECT starting_balance, current_balance FROM daily_trading_stats
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        result = cursor.fetchone()
        
        if result:
            starting_balance = result[0]
            if starting_balance > 0:
                daily_loss_percent = (starting_balance - current_balance) / starting_balance
            else:
                daily_loss_percent = 0
        else:
            # First trade of the day - create record
            cursor.execute('''
                INSERT INTO daily_trading_stats 
                (user_id, date, starting_balance, current_balance)
                VALUES (?, ?, ?, ?)
            ''', (user_id, today, current_balance, current_balance))
            conn.commit()
            daily_loss_percent = 0
        
        conn.close()
        
        can_trade = daily_loss_percent < max_daily_loss
        return can_trade, daily_loss_percent
    
    def check_open_positions(self, user_id: str, tier: str) -> Tuple[bool, int, int]:
        """
        Check if user has reached max open positions
        Returns: (can_open_more, positions_open, max_positions)
        """
        tier_config = TIER_HIERARCHY.get(tier, TIER_HIERARCHY["NIBBLER"])
        max_positions = tier_config["max_positions"]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM open_positions
            WHERE user_id = ? AND status = 'OPEN'
        ''', (user_id,))
        
        positions_open = cursor.fetchone()[0]
        conn.close()
        
        can_open_more = positions_open < max_positions
        return can_open_more, positions_open, max_positions
    
    def can_user_access_signal(self, tier: str, signal: Dict) -> Tuple[bool, str]:
        """
        Check if user's tier can access this signal class
        """
        signal_class = signal.get("class", "RAPID")
        tier_config = TIER_HIERARCHY.get(tier, TIER_HIERARCHY["NIBBLER"])
        allowed_classes = tier_config["signal_access"]
        
        if signal_class not in allowed_classes:
            if signal_class == "SNIPER":
                return False, f"🎯 SNIPER signals require FANG tier or higher (currently {tier})"
            else:
                return False, f"Signal class {signal_class} not available for {tier} tier"
        
        return True, "Signal accessible"
    
    def is_signal_valid(self, signal: Dict, current_market: Dict) -> bool:
        """
        Dynamic signal validity based on real market conditions
        NOT a fixed timer
        """
        # Check if entry price is still achievable
        if signal.get('direction') == 'BUY':
            if current_market.get('ask', 0) > signal.get('entry', 0) + 0.0005:  # 5 pips for forex
                return False  # Price ran away
        else:  # SELL
            if current_market.get('bid', 999999) < signal.get('entry', 999999) - 0.0005:
                return False  # Price ran away
        
        # Check spread
        spread = current_market.get('spread', 0)
        if spread > 5:  # Max 5 pip spread
            return False
        
        # Check if market is open
        if not current_market.get('is_open', True):
            return False
        
        return True
    
    def can_user_trade(
        self,
        user_id: str,
        tier: str,
        signal: Dict,
        balance: float,
        current_market: Dict
    ) -> TradingPermission:
        """
        Master validation combining ALL trading rules
        """
        permission = TradingPermission(allowed=True)
        
        # 1. Check if user has active subscription (tier != FREE)
        if tier not in TIER_HIERARCHY:
            permission.allowed = False
            permission.reason = "Invalid or expired subscription"
            permission.checks["subscription"] = False
            return permission
        permission.checks["subscription"] = True
        
        # 2. Check daily trade limit
        can_trade, trades_used, trades_allowed = self.check_daily_trade_limit(user_id, tier)
        permission.checks["daily_trades"] = can_trade
        permission.details["trades_today"] = f"{trades_used}/{trades_allowed}"
        if not can_trade:
            permission.allowed = False
            permission.reason = f"Daily trade limit reached ({trades_used}/{trades_allowed})"
            self.log_violation(user_id, "DAILY_TRADE_LIMIT", permission.reason, signal.get("signal_id"))
            return permission
        
        # 3. Check daily loss limit
        can_trade, daily_loss = self.check_daily_loss_limit(user_id, tier, balance)
        permission.checks["daily_loss"] = can_trade
        permission.details["daily_loss"] = f"{daily_loss:.1%}"
        if not can_trade:
            permission.allowed = False
            permission.reason = f"Daily loss limit exceeded ({daily_loss:.1%})"
            self.log_violation(user_id, "DAILY_LOSS_LIMIT", permission.reason, signal.get("signal_id"))
            return permission
        
        # 4. Check open positions limit
        can_open, positions_open, max_positions = self.check_open_positions(user_id, tier)
        permission.checks["positions"] = can_open
        permission.details["positions"] = f"{positions_open}/{max_positions}"
        if not can_open:
            permission.allowed = False
            permission.reason = f"Max positions reached ({positions_open}/{max_positions})"
            self.log_violation(user_id, "MAX_POSITIONS", permission.reason, signal.get("signal_id"))
            return permission
        
        # 5. Check if signal class is allowed for tier
        can_access, access_reason = self.can_user_access_signal(tier, signal)
        permission.checks["signal_access"] = can_access
        if not can_access:
            permission.allowed = False
            permission.reason = access_reason
            self.log_violation(user_id, "SIGNAL_ACCESS", permission.reason, signal.get("signal_id"))
            return permission
        
        # 6. Check if signal is still valid (dynamic expiry)
        signal_valid = self.is_signal_valid(signal, current_market)
        permission.checks["signal_validity"] = signal_valid
        if not signal_valid:
            permission.allowed = False
            permission.reason = "Signal no longer valid (price moved or spread too wide)"
            return permission
        
        # 7. Check minimum balance ($100)
        min_balance = 100
        permission.checks["min_balance"] = balance >= min_balance
        if balance < min_balance:
            permission.allowed = False
            permission.reason = f"Minimum balance ${min_balance} required (current: ${balance:.2f})"
            self.log_violation(user_id, "MIN_BALANCE", permission.reason, signal.get("signal_id"))
            return permission
        
        # 8. Check margin (must have >50% free)
        # This would require broker API integration
        permission.checks["margin"] = True  # Placeholder
        
        # 9. Check cooldown period (if any)
        permission.checks["cooldown"] = True  # Placeholder for future implementation
        
        # All checks passed
        permission.details["tier"] = tier
        permission.details["signal_class"] = signal.get("class", "RAPID")
        permission.details["can_auto_fire"] = (tier == "COMMANDER" and signal.get("tcs", 0) >= 75)
        
        return permission
    
    def increment_trade_count(self, user_id: str):
        """Increment user's daily trade count"""
        today = datetime.now(timezone.utc).date()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE daily_trading_stats 
            SET trades_count = trades_count + 1,
                last_trade_time = CURRENT_TIMESTAMP
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        if cursor.rowcount == 0:
            # Create new record if doesn't exist
            cursor.execute('''
                INSERT INTO daily_trading_stats 
                (user_id, date, trades_count, last_trade_time)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ''', (user_id, today))
        
        conn.commit()
        conn.close()
    
    def record_position_opened(
        self,
        user_id: str,
        position_id: str,
        signal: Dict,
        lot_size: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ):
        """Record a new position being opened"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO open_positions 
            (position_id, user_id, signal_id, symbol, direction, 
             lot_size, entry_price, stop_loss, take_profit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            position_id,
            user_id,
            signal.get("signal_id"),
            signal.get("symbol"),
            signal.get("direction"),
            lot_size,
            entry_price,
            stop_loss,
            take_profit
        ))
        
        conn.commit()
        conn.close()
        
        # Also increment trade count
        self.increment_trade_count(user_id)
    
    def record_position_closed(
        self,
        position_id: str,
        pnl: float
    ):
        """Record a position being closed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE open_positions 
            SET status = 'CLOSED',
                closed_at = CURRENT_TIMESTAMP,
                pnl = ?
            WHERE position_id = ?
        ''', (pnl, position_id))
        
        conn.commit()
        conn.close()
    
    def update_balance_and_pnl(
        self,
        user_id: str,
        new_balance: float,
        trade_pnl: float
    ):
        """Update user's balance and P&L tracking"""
        today = datetime.now(timezone.utc).date()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current stats
        cursor.execute('''
            SELECT starting_balance, consecutive_losses 
            FROM daily_trading_stats
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        result = cursor.fetchone()
        if result:
            starting_balance = result[0]
            consecutive_losses = result[1] or 0
            
            # Update consecutive losses
            if trade_pnl < 0:
                consecutive_losses += 1
            else:
                consecutive_losses = 0
            
            # Calculate daily loss percent
            daily_loss_percent = 0
            if starting_balance > 0:
                daily_loss_percent = (starting_balance - new_balance) / starting_balance
            
            cursor.execute('''
                UPDATE daily_trading_stats 
                SET current_balance = ?,
                    daily_pnl = daily_pnl + ?,
                    daily_loss_percent = ?,
                    consecutive_losses = ?
                WHERE user_id = ? AND date = ?
            ''', (
                new_balance,
                trade_pnl,
                daily_loss_percent,
                consecutive_losses,
                user_id,
                today
            ))
        
        conn.commit()
        conn.close()
    
    def log_violation(
        self,
        user_id: str,
        violation_type: str,
        details: str,
        signal_id: Optional[str] = None
    ):
        """Log a risk violation for audit trail"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO risk_violations 
            (user_id, violation_type, details, blocked_signal_id)
            VALUES (?, ?, ?, ?)
        ''', (user_id, violation_type, details, signal_id))
        
        conn.commit()
        conn.close()
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get comprehensive user trading statistics"""
        today = datetime.now(timezone.utc).date()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get today's stats
        cursor.execute('''
            SELECT trades_count, starting_balance, current_balance, 
                   daily_pnl, daily_loss_percent, consecutive_losses
            FROM daily_trading_stats
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        today_stats = cursor.fetchone()
        
        # Get open positions
        cursor.execute('''
            SELECT COUNT(*), SUM(pnl)
            FROM open_positions
            WHERE user_id = ? AND status = 'OPEN'
        ''', (user_id,))
        
        open_positions = cursor.fetchone()
        
        conn.close()
        
        return {
            "today": {
                "trades": today_stats[0] if today_stats else 0,
                "pnl": today_stats[3] if today_stats else 0,
                "loss_percent": today_stats[4] if today_stats else 0,
                "consecutive_losses": today_stats[5] if today_stats else 0
            },
            "positions": {
                "open": open_positions[0] if open_positions else 0,
                "unrealized_pnl": open_positions[1] if open_positions and open_positions[1] else 0
            }
        }

# Singleton instance
_guardrails_instance = None

def get_trading_guardrails() -> TradingGuardrails:
    """Get singleton instance of trading guardrails"""
    global _guardrails_instance
    if _guardrails_instance is None:
        _guardrails_instance = TradingGuardrails()
    return _guardrails_instance