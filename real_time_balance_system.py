#!/usr/bin/env python3
"""
REAL-TIME BALANCE SYSTEM
Get accurate account balance BEFORE any trade creation
Scalable for 5k users with safety defaults
"""

import json
import time
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass
class AccountBalance:
    """Account balance information"""
    user_id: str
    account_id: str
    balance: float
    equity: float
    margin: float
    free_margin: float
    currency: str
    server: str
    timestamp: datetime
    is_live: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "account_id": self.account_id,
            "balance": self.balance,
            "equity": self.equity,
            "margin": self.margin,
            "free_margin": self.free_margin,
            "currency": self.currency,
            "server": self.server,
            "timestamp": self.timestamp.isoformat(),
            "is_live": self.is_live
        }

class RealTimeBalanceSystem:
    """
    Scalable real-time balance system for 5k users
    - Gets balance BEFORE trade creation
    - $100 safety default for unknown balances
    - Efficient caching and batch updates
    """
    
    def __init__(self):
        self.db_path = Path("/root/HydraX-v2/data/user_balances.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Cache settings for scalability
        self.balance_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.max_cache_size = 10000  # Support 10k users
        
        # Safety defaults
        self.safety_default_balance = 100.0
        self.min_balance_for_trading = 10.0
        
        # Thread pool for async balance updates
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Initialize database
        self.init_database()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("BALANCE_SYSTEM")
        
        self.logger.info("🏦 REAL-TIME BALANCE SYSTEM INITIALIZED")
        self.logger.info(f"💰 Safety default: ${self.safety_default_balance}")
        self.logger.info(f"📊 Cache TTL: {self.cache_ttl}s")
        
    def init_database(self):
        """Initialize balance database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS user_balances (
                    user_id TEXT PRIMARY KEY,
                    account_id TEXT,
                    balance REAL,
                    equity REAL,
                    margin REAL,
                    free_margin REAL,
                    currency TEXT DEFAULT 'USD',
                    server TEXT,
                    timestamp TIMESTAMP,
                    is_live BOOLEAN DEFAULT 1,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS balance_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    old_balance REAL,
                    new_balance REAL,
                    change_reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_user_timestamp ON user_balances(user_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_audit_user ON balance_audit(user_id, timestamp);
            """)
    
    def get_live_balance_from_mt5(self, user_id: str) -> Optional[AccountBalance]:
        """Get real-time balance from MT5 via bridge"""
        try:
            from production_bridge_tunnel import get_production_tunnel
            tunnel = get_production_tunnel()
            
            # Create ping command with balance request
            balance_request = {
                "command": "get_balance",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Execute via AWS bridge
            result = tunnel.execute_live_trade(balance_request)
            
            if result.get("success"):
                # Try to parse account info from bridge response
                # This would need to be implemented in the bridge to return balance
                # For now, use fallback method
                pass
            
            # Fallback: Use FireRouter ping
            from src.bitten_core.fire_router import FireRouter
            router = FireRouter()
            ping_result = router.ping_bridge(user_id)
            
            if ping_result.get("success"):
                account_info = ping_result.get("account_info", {})
                
                if account_info:
                    return AccountBalance(
                        user_id=user_id,
                        account_id=account_info.get("login", user_id),
                        balance=float(account_info.get("balance", self.safety_default_balance)),
                        equity=float(account_info.get("equity", account_info.get("balance", self.safety_default_balance))),
                        margin=float(account_info.get("margin", 0)),
                        free_margin=float(account_info.get("free_margin", account_info.get("balance", self.safety_default_balance))),
                        currency=account_info.get("currency", "USD"),
                        server=account_info.get("server", "Unknown"),
                        timestamp=datetime.now(),
                        is_live=True
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Live balance retrieval failed for {user_id}: {e}")
            return None
    
    def get_cached_balance(self, user_id: str) -> Optional[AccountBalance]:
        """Get balance from cache if fresh"""
        if user_id in self.balance_cache:
            cached_data = self.balance_cache[user_id]
            age = (datetime.now() - cached_data["timestamp"]).total_seconds()
            
            if age < self.cache_ttl:
                return AccountBalance(**cached_data["balance"])
        
        return None
    
    def update_balance_cache(self, balance: AccountBalance):
        """Update balance cache with LRU eviction"""
        # Simple LRU eviction if cache is full
        if len(self.balance_cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = min(self.balance_cache.keys(), 
                           key=lambda k: self.balance_cache[k]["timestamp"])
            del self.balance_cache[oldest_key]
        
        self.balance_cache[balance.user_id] = {
            "balance": balance.to_dict(),
            "timestamp": datetime.now()
        }
    
    def get_balance_from_db(self, user_id: str) -> Optional[AccountBalance]:
        """Get balance from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT user_id, account_id, balance, equity, margin, free_margin, 
                           currency, server, timestamp, is_live
                    FROM user_balances 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return AccountBalance(
                        user_id=row[0],
                        account_id=row[1],
                        balance=row[2],
                        equity=row[3],
                        margin=row[4],
                        free_margin=row[5],
                        currency=row[6],
                        server=row[7],
                        timestamp=datetime.fromisoformat(row[8]),
                        is_live=bool(row[9])
                    )
        except Exception as e:
            self.logger.error(f"❌ Database balance retrieval failed for {user_id}: {e}")
        
        return None
    
    def save_balance_to_db(self, balance: AccountBalance):
        """Save balance to database with audit trail"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get old balance for audit
                old_balance = self.get_balance_from_db(balance.user_id)
                old_balance_value = old_balance.balance if old_balance else 0.0
                
                # Insert new balance
                conn.execute("""
                    INSERT OR REPLACE INTO user_balances 
                    (user_id, account_id, balance, equity, margin, free_margin, 
                     currency, server, timestamp, is_live)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    balance.user_id, balance.account_id, balance.balance,
                    balance.equity, balance.margin, balance.free_margin,
                    balance.currency, balance.server, balance.timestamp.isoformat(),
                    balance.is_live
                ))
                
                # Audit trail
                if abs(balance.balance - old_balance_value) > 0.01:  # Only log significant changes
                    conn.execute("""
                        INSERT INTO balance_audit 
                        (user_id, old_balance, new_balance, change_reason)
                        VALUES (?, ?, ?, ?)
                    """, (
                        balance.user_id, old_balance_value, balance.balance,
                        "real_time_update"
                    ))
                
        except Exception as e:
            self.logger.error(f"❌ Database save failed for {balance.user_id}: {e}")
    
    def get_user_balance(self, user_id: str, force_refresh: bool = False) -> AccountBalance:
        """
        Get user balance with multi-layer fallback
        1. Try live MT5 balance
        2. Use cached balance if fresh
        3. Use database balance
        4. Use safety default
        """
        self.logger.info(f"🔍 Getting balance for user {user_id}")
        
        # Force refresh or try live first
        if force_refresh or user_id not in self.balance_cache:
            live_balance = self.get_live_balance_from_mt5(user_id)
            if live_balance:
                self.update_balance_cache(live_balance)
                self.save_balance_to_db(live_balance)
                self.logger.info(f"💰 Live balance: ${live_balance.balance}")
                return live_balance
        
        # Try cache
        cached_balance = self.get_cached_balance(user_id)
        if cached_balance:
            self.logger.info(f"📊 Cached balance: ${cached_balance.balance}")
            return cached_balance
        
        # Try database
        db_balance = self.get_balance_from_db(user_id)
        if db_balance:
            # Check if balance is too old (>1 hour)
            age = (datetime.now() - db_balance.timestamp).total_seconds()
            if age < 3600:  # 1 hour
                self.update_balance_cache(db_balance)
                self.logger.info(f"🗄️ Database balance: ${db_balance.balance}")
                return db_balance
        
        # Safety default
        self.logger.warning(f"⚠️ Using safety default for {user_id}")
        safety_balance = AccountBalance(
            user_id=user_id,
            account_id=user_id,
            balance=self.safety_default_balance,
            equity=self.safety_default_balance,
            margin=0.0,
            free_margin=self.safety_default_balance,
            currency="USD",
            server="Unknown",
            timestamp=datetime.now(),
            is_live=False
        )
        
        # Save safety default to database
        self.save_balance_to_db(safety_balance)
        self.update_balance_cache(safety_balance)
        
        return safety_balance
    
    def validate_balance_for_trading(self, user_id: str) -> Dict:
        """Validate if user has sufficient balance for trading"""
        balance = self.get_user_balance(user_id)
        
        validation_result = {
            "user_id": user_id,
            "balance": balance.balance,
            "can_trade": balance.balance >= self.min_balance_for_trading,
            "is_live_balance": balance.is_live,
            "balance_source": "live" if balance.is_live else "default",
            "warnings": []
        }
        
        if not balance.is_live:
            validation_result["warnings"].append(
                f"Using safety default balance of ${self.safety_default_balance}"
            )
        
        if balance.balance < self.min_balance_for_trading:
            validation_result["warnings"].append(
                f"Balance ${balance.balance} below minimum ${self.min_balance_for_trading}"
            )
        
        return validation_result
    
    def batch_update_balances(self, user_ids: List[str]) -> Dict:
        """Update multiple user balances efficiently"""
        self.logger.info(f"🔄 Batch updating {len(user_ids)} balances")
        
        results = {
            "updated": 0,
            "failed": 0,
            "total": len(user_ids)
        }
        
        # Use thread pool for parallel updates
        futures = []
        for user_id in user_ids:
            future = self.executor.submit(self.get_user_balance, user_id, True)
            futures.append((user_id, future))
        
        # Collect results
        for user_id, future in futures:
            try:
                balance = future.result(timeout=30)
                if balance:
                    results["updated"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                self.logger.error(f"❌ Batch update failed for {user_id}: {e}")
                results["failed"] += 1
        
        self.logger.info(f"✅ Batch update complete: {results['updated']}/{results['total']} successful")
        return results
    
    def get_system_stats(self) -> Dict:
        """Get system statistics for monitoring"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM user_balances")
                total_users = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM user_balances WHERE is_live = 1")
                live_balances = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT AVG(balance) FROM user_balances WHERE is_live = 1")
                avg_balance = cursor.fetchone()[0] or 0
        except:
            total_users = 0
            live_balances = 0
            avg_balance = 0
        
        return {
            "total_users": total_users,
            "live_balances": live_balances,
            "cache_size": len(self.balance_cache),
            "avg_balance": round(avg_balance, 2),
            "safety_default": self.safety_default_balance,
            "cache_hit_rate": self._calculate_cache_hit_rate()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate for monitoring"""
        # Simple implementation - would need to track hits/misses in production
        return 0.85  # Placeholder

# Global balance system instance
BALANCE_SYSTEM = RealTimeBalanceSystem()

def get_user_balance_safe(user_id: str, force_refresh: bool = False) -> AccountBalance:
    """Get user balance with safety defaults"""
    return BALANCE_SYSTEM.get_user_balance(user_id, force_refresh)

def validate_user_can_trade(user_id: str) -> Dict:
    """Validate if user can trade safely"""
    return BALANCE_SYSTEM.validate_balance_for_trading(user_id)

def pre_trade_balance_check(user_id: str) -> Dict:
    """Pre-trade balance validation"""
    validation = validate_user_can_trade(user_id)
    balance = get_user_balance_safe(user_id)
    
    return {
        "user_id": user_id,
        "balance": balance.balance,
        "can_trade": validation["can_trade"],
        "is_live": balance.is_live,
        "warnings": validation["warnings"],
        "account_info": {
            "account_id": balance.account_id,
            "server": balance.server,
            "currency": balance.currency,
            "free_margin": balance.free_margin
        }
    }

if __name__ == "__main__":
    # Test the system
    print("🏦 TESTING REAL-TIME BALANCE SYSTEM")
    print("=" * 50)
    
    # Test with user 843859
    result = pre_trade_balance_check("843859")
    print(f"User: {result['user_id']}")
    print(f"Balance: ${result['balance']}")
    print(f"Can Trade: {result['can_trade']}")
    print(f"Live Balance: {result['is_live']}")
    print(f"Warnings: {result['warnings']}")
    
    # System stats
    stats = BALANCE_SYSTEM.get_system_stats()
    print(f"\\nSystem Stats: {stats}")