#!/usr/bin/env python3
"""
BITTEN Credit Referral System
Simple $10 credit system for successful subscription referrals
"""

import logging
import sqlite3
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path

# Import gamification hooks if available
try:
    from .referral_gamification_hooks import get_referral_gamification_hooks
    GAMIFICATION_AVAILABLE = True
except ImportError:
    GAMIFICATION_AVAILABLE = False
    logger.warning("Gamification hooks not available - referral rewards will be basic")

logger = logging.getLogger(__name__)

@dataclass
class ReferralCredit:
    """Credit referral tracking"""
    id: Optional[int] = None
    referrer_id: str = ""
    referred_user_id: str = ""
    referral_code: str = ""
    credit_amount: float = 10.0
    credited: bool = False
    payment_confirmed: bool = False
    created_at: Optional[datetime] = None
    credited_at: Optional[datetime] = None
    applied_on_invoice_id: Optional[str] = None

@dataclass
class UserCreditBalance:
    """User credit balance tracking"""
    user_id: str
    total_credits: float = 0.0
    pending_credits: float = 0.0
    applied_credits: float = 0.0
    referral_count: int = 0
    last_updated: Optional[datetime] = None

class CreditReferralSystem:
    """Simplified credit-based referral system"""
    
    def __init__(self, db_path: str = "/root/HydraX-v2/data/credit_referrals.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with credit referral tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS referral_codes (
                    code TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    uses_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS referral_credits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id TEXT NOT NULL,
                    referred_user_id TEXT NOT NULL,
                    referral_code TEXT NOT NULL,
                    credit_amount REAL DEFAULT 10.0,
                    credited BOOLEAN DEFAULT 0,
                    payment_confirmed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    credited_at TIMESTAMP NULL,
                    applied_on_invoice_id TEXT NULL,
                    FOREIGN KEY (referral_code) REFERENCES referral_codes(code)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_credit_balances (
                    user_id TEXT PRIMARY KEY,
                    total_credits REAL DEFAULT 0.0,
                    pending_credits REAL DEFAULT 0.0,
                    applied_credits REAL DEFAULT 0.0,
                    referral_count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Gamification rewards table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gamification_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    referral_count INTEGER NOT NULL,
                    xp_gained INTEGER DEFAULT 0,
                    badges_earned TEXT NULL,
                    milestones_reached TEXT NULL,
                    notifications TEXT NULL,
                    processed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_referral_credits_referrer ON referral_credits(referrer_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_referral_credits_referred ON referral_credits(referred_user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_referral_codes_user ON referral_codes(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_gamification_rewards_user ON gamification_rewards(user_id)")
            
            conn.commit()
    
    def generate_referral_code(self, user_id: str, custom_code: Optional[str] = None) -> str:
        """Generate unique referral code for user"""
        with sqlite3.connect(self.db_path) as conn:
            # Check if user already has an active code
            cursor = conn.execute(
                "SELECT code FROM referral_codes WHERE user_id = ? AND is_active = 1",
                (user_id,)
            )
            existing = cursor.fetchone()
            if existing:
                return existing[0]
            
            # Generate new code
            if custom_code:
                code = custom_code.upper()
                # Check if custom code is available
                cursor = conn.execute("SELECT code FROM referral_codes WHERE code = ?", (code,))
                if cursor.fetchone():
                    raise ValueError(f"Code '{code}' already exists")
            else:
                # Generate random code
                while True:
                    code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
                    cursor = conn.execute("SELECT code FROM referral_codes WHERE code = ?", (code,))
                    if not cursor.fetchone():
                        break
            
            # Insert new code
            conn.execute(
                "INSERT INTO referral_codes (code, user_id) VALUES (?, ?)",
                (code, user_id)
            )
            conn.commit()
            
            logger.info(f"Generated referral code {code} for user {user_id}")
            return code
    
    def use_referral_code(self, code: str, new_user_id: str) -> bool:
        """Register new user with referral code"""
        with sqlite3.connect(self.db_path) as conn:
            # Validate referral code
            cursor = conn.execute(
                "SELECT user_id FROM referral_codes WHERE code = ? AND is_active = 1",
                (code,)
            )
            referrer_data = cursor.fetchone()
            if not referrer_data:
                logger.warning(f"Invalid referral code: {code}")
                return False
            
            referrer_id = referrer_data[0]
            
            # Prevent self-referral
            if referrer_id == new_user_id:
                logger.warning(f"Self-referral attempt: {new_user_id}")
                return False
            
            # Check if user was already referred
            cursor = conn.execute(
                "SELECT id FROM referral_credits WHERE referred_user_id = ?",
                (new_user_id,)
            )
            if cursor.fetchone():
                logger.warning(f"User {new_user_id} already referred")
                return False
            
            # Create pending credit entry
            conn.execute("""
                INSERT INTO referral_credits 
                (referrer_id, referred_user_id, referral_code, credit_amount) 
                VALUES (?, ?, ?, ?)
            """, (referrer_id, new_user_id, code, 10.0))
            
            # Update referral code usage
            conn.execute(
                "UPDATE referral_codes SET uses_count = uses_count + 1 WHERE code = ?",
                (code,)
            )
            
            # Update pending credits for referrer
            self._update_user_balance(conn, referrer_id, pending_credit=10.0)
            
            conn.commit()
            logger.info(f"User {new_user_id} referred by {referrer_id} with code {code}")
            return True
    
    def confirm_payment_and_apply_credit(self, referred_user_id: str, invoice_id: Optional[str] = None) -> Optional[str]:
        """Confirm payment and apply credit to referrer's account"""
        with sqlite3.connect(self.db_path) as conn:
            # Find pending credit for this user
            cursor = conn.execute("""
                SELECT id, referrer_id, credit_amount, referral_code 
                FROM referral_credits 
                WHERE referred_user_id = ? AND payment_confirmed = 0 AND credited = 0
            """, (referred_user_id,))
            
            credit_data = cursor.fetchone()
            if not credit_data:
                logger.warning(f"No pending credit found for user {referred_user_id}")
                return None
            
            credit_id, referrer_id, credit_amount, referral_code = credit_data
            
            # Mark payment as confirmed and credit as applied
            conn.execute("""
                UPDATE referral_credits 
                SET payment_confirmed = 1, credited = 1, credited_at = CURRENT_TIMESTAMP,
                    applied_on_invoice_id = ?
                WHERE id = ?
            """, (invoice_id, credit_id))
            
            # Update user balance - move from pending to total
            self._update_user_balance(conn, referrer_id, pending_credit=-credit_amount, total_credit=credit_amount)
            
            conn.commit()
            
            # Trigger gamification rewards
            if GAMIFICATION_AVAILABLE:
                try:
                    # Get updated referral count
                    updated_balance = self.get_user_credit_balance(referrer_id)
                    gamification = get_referral_gamification_hooks()
                    rewards = gamification.trigger_referral_success_rewards(referrer_id, updated_balance.referral_count)
                    
                    logger.info(f"Gamification rewards triggered for {referrer_id}: {rewards}")
                    
                    # Store rewards info for later notification
                    # This could be picked up by the bot or notification system
                    self._store_gamification_rewards(conn, referrer_id, rewards)
                    
                except Exception as e:
                    logger.error(f"Error triggering gamification rewards: {e}")
            
            logger.info(f"Applied ${credit_amount} credit to {referrer_id} for referring {referred_user_id}")
            return referrer_id
    
    def _update_user_balance(self, conn, user_id: str, pending_credit: float = 0, total_credit: float = 0, applied_credit: float = 0):
        """Update user credit balance"""
        # Get current balance or create new
        cursor = conn.execute(
            "SELECT total_credits, pending_credits, applied_credits, referral_count FROM user_credit_balances WHERE user_id = ?",
            (user_id,)
        )
        current = cursor.fetchone()
        
        if current:
            new_total = current[0] + total_credit
            new_pending = current[1] + pending_credit
            new_applied = current[2] + applied_credit
            new_count = current[3] + (1 if total_credit > 0 else 0)
            
            conn.execute("""
                UPDATE user_credit_balances 
                SET total_credits = ?, pending_credits = ?, applied_credits = ?, 
                    referral_count = ?, last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (new_total, new_pending, new_applied, new_count, user_id))
        else:
            conn.execute("""
                INSERT INTO user_credit_balances 
                (user_id, total_credits, pending_credits, applied_credits, referral_count)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, total_credit, pending_credit, applied_credit, 1 if total_credit > 0 else 0))
    
    def _store_gamification_rewards(self, conn, user_id: str, rewards: Dict):
        """Store gamification rewards for later processing by bot/notification system"""
        import json
        
        conn.execute("""
            INSERT INTO gamification_rewards 
            (user_id, referral_count, xp_gained, badges_earned, milestones_reached, notifications)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            rewards.get('referral_count', 0),
            rewards.get('xp_gained', 0),
            json.dumps(rewards.get('badges_earned', [])),
            json.dumps(rewards.get('milestones_reached', [])),
            json.dumps(rewards.get('notifications', []))
        ))
    
    def get_user_credit_balance(self, user_id: str) -> UserCreditBalance:
        """Get user's current credit balance"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT total_credits, pending_credits, applied_credits, referral_count, last_updated FROM user_credit_balances WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            
            if result:
                return UserCreditBalance(
                    user_id=user_id,
                    total_credits=result[0],
                    pending_credits=result[1],
                    applied_credits=result[2],
                    referral_count=result[3],
                    last_updated=datetime.fromisoformat(result[4]) if result[4] else None
                )
            else:
                return UserCreditBalance(user_id=user_id)
    
    def apply_credit_to_invoice(self, user_id: str, invoice_amount: float, invoice_id: str) -> Tuple[float, float]:
        """Apply available credit to an invoice and return (credit_applied, remaining_amount)"""
        with sqlite3.connect(self.db_path) as conn:
            balance = self.get_user_credit_balance(user_id)
            
            if balance.total_credits <= 0:
                return 0.0, invoice_amount
            
            # Apply up to the invoice amount or available credit
            credit_to_apply = min(balance.total_credits, invoice_amount)
            remaining_amount = invoice_amount - credit_to_apply
            
            # Update balances
            self._update_user_balance(
                conn, user_id, 
                total_credit=-credit_to_apply, 
                applied_credit=credit_to_apply
            )
            
            # Log the application
            conn.execute("""
                INSERT INTO referral_credits 
                (referrer_id, referred_user_id, referral_code, credit_amount, credited, payment_confirmed, applied_on_invoice_id)
                VALUES (?, ?, 'CREDIT_APPLICATION', ?, 1, 1, ?)
            """, (user_id, user_id, -credit_to_apply, invoice_id))
            
            conn.commit()
            
            logger.info(f"Applied ${credit_to_apply} credit to invoice {invoice_id} for user {user_id}")
            return credit_to_apply, remaining_amount
    
    def get_referral_stats(self, user_id: str) -> Dict:
        """Get detailed referral statistics for user"""
        with sqlite3.connect(self.db_path) as conn:
            balance = self.get_user_credit_balance(user_id)
            
            # Get referral code
            cursor = conn.execute(
                "SELECT code FROM referral_codes WHERE user_id = ? AND is_active = 1",
                (user_id,)
            )
            code_result = cursor.fetchone()
            referral_code = code_result[0] if code_result else None
            
            # Get recent referrals
            cursor = conn.execute("""
                SELECT referred_user_id, credit_amount, credited, payment_confirmed, created_at
                FROM referral_credits 
                WHERE referrer_id = ? AND credit_amount > 0
                ORDER BY created_at DESC LIMIT 10
            """, (user_id,))
            
            recent_referrals = []
            for row in cursor.fetchall():
                recent_referrals.append({
                    'referred_user': row[0],
                    'credit_amount': row[1],
                    'credited': bool(row[2]),
                    'payment_confirmed': bool(row[3]),
                    'created_at': row[4]
                })
            
            return {
                'referral_code': referral_code,
                'balance': balance,
                'recent_referrals': recent_referrals,
                'free_months_earned': int(balance.total_credits // 39),  # $39/month
                'progress_to_free_month': f"${39 - (balance.total_credits % 39):.0f}"
            }
    
    def get_admin_stats(self) -> Dict:
        """Get admin statistics"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # Total credits issued
            cursor = conn.execute("SELECT SUM(credit_amount) FROM referral_credits WHERE credited = 1 AND credit_amount > 0")
            stats['total_credits_issued'] = cursor.fetchone()[0] or 0
            
            # Total referrals
            cursor = conn.execute("SELECT COUNT(*) FROM referral_credits WHERE credit_amount > 0")
            stats['total_referrals'] = cursor.fetchone()[0] or 0
            
            # Pending credits
            cursor = conn.execute("SELECT SUM(credit_amount) FROM referral_credits WHERE credited = 0 AND credit_amount > 0")
            stats['pending_credits'] = cursor.fetchone()[0] or 0
            
            # Top referrers
            cursor = conn.execute("""
                SELECT referrer_id, COUNT(*) as referral_count, SUM(credit_amount) as total_earned
                FROM referral_credits 
                WHERE credited = 1 AND credit_amount > 0
                GROUP BY referrer_id 
                ORDER BY referral_count DESC 
                LIMIT 10
            """)
            stats['top_referrers'] = [
                {'user_id': row[0], 'referrals': row[1], 'total_earned': row[2]}
                for row in cursor.fetchall()
            ]
            
            return stats
    
    def get_pending_gamification_rewards(self, user_id: str) -> List[Dict]:
        """Get unprocessed gamification rewards for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, referral_count, xp_gained, badges_earned, milestones_reached, notifications, created_at
                FROM gamification_rewards 
                WHERE user_id = ? AND processed = 0
                ORDER BY created_at ASC
            """, (user_id,))
            
            import json
            rewards = []
            for row in cursor.fetchall():
                rewards.append({
                    'id': row[0],
                    'referral_count': row[1],
                    'xp_gained': row[2],
                    'badges_earned': json.loads(row[3]) if row[3] else [],
                    'milestones_reached': json.loads(row[4]) if row[4] else [],
                    'notifications': json.loads(row[5]) if row[5] else [],
                    'created_at': row[6]
                })
            
            return rewards
    
    def apply_manual_credit(self, user_id: str, amount: float, reason: str = "Manual admin credit") -> Dict:
        """Apply manual credit to a user (admin function)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Add credit record (reason stored in referred_user_id for admin credits)
                conn.execute("""
                    INSERT INTO referral_credits (
                        referrer_id, referred_user_id, referral_code, credit_amount, 
                        credited_at, payment_confirmed, credited
                    ) VALUES (?, ?, ?, ?, ?, 1, 1)
                """, (user_id, f"MANUAL_ADMIN:{reason}", "ADMIN_CREDIT", amount, datetime.now().isoformat()))
                
                # Update balance
                conn.execute("""
                    INSERT OR REPLACE INTO user_credit_balances (
                        user_id, total_credits, applied_credits, pending_credits, referral_count, last_updated
                    ) VALUES (
                        ?, 
                        COALESCE((SELECT total_credits FROM user_credit_balances WHERE user_id = ?), 0) + ?,
                        COALESCE((SELECT applied_credits FROM user_credit_balances WHERE user_id = ?), 0),
                        COALESCE((SELECT pending_credits FROM user_credit_balances WHERE user_id = ?), 0),
                        COALESCE((SELECT referral_count FROM user_credit_balances WHERE user_id = ?), 0),
                        ?
                    )
                """, (user_id, user_id, amount, user_id, user_id, user_id, datetime.now().isoformat()))
                
                conn.commit()
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "amount": amount,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_top_referrers(self, limit: int = 10) -> List[Dict]:
        """Get top referrers by number of successful referrals"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        referrer_id as user_id,
                        COUNT(*) as referral_count,
                        SUM(credit_amount) as total_credits
                    FROM referral_credits 
                    WHERE credited = 1
                    GROUP BY referrer_id
                    ORDER BY referral_count DESC, total_credits DESC
                    LIMIT ?
                """, (limit,))
                
                results = cursor.fetchall()
                
                top_referrers = []
                for row in results:
                    user_id, referral_count, total_credits = row
                    top_referrers.append({
                        "user_id": user_id,
                        "referral_count": referral_count,
                        "total_credits": total_credits or 0.0
                    })
                
                return top_referrers
                
        except Exception as e:
            return []
    
    def mark_gamification_rewards_processed(self, reward_ids: List[int]):
        """Mark gamification rewards as processed"""
        with sqlite3.connect(self.db_path) as conn:
            for reward_id in reward_ids:
                conn.execute(
                    "UPDATE gamification_rewards SET processed = 1 WHERE id = ?",
                    (reward_id,)
                )
            conn.commit()

# Global instance
_credit_referral_system = None

def get_credit_referral_system() -> CreditReferralSystem:
    """Get global credit referral system instance"""
    global _credit_referral_system
    if _credit_referral_system is None:
        _credit_referral_system = CreditReferralSystem()
    return _credit_referral_system