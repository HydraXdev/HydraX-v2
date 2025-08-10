"""
BITTEN Elite Referral System - Build Your Squad
Military-style recruitment system with multi-tier rewards and anti-abuse mechanisms
"""

import json
import time
import sqlite3
import hashlib
import secrets
import string
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from pathlib import Path
import ipaddress

logger = logging.getLogger(__name__)

class ReferralTier(Enum):
    """Referral tier levels"""
    DIRECT = 1      # Direct referral
    SECONDARY = 2   # Referral of referral
    TERTIARY = 3    # Third level referral

class SquadRank(Enum):
    """Squad leader ranks based on recruits"""
    LONE_WOLF = "Lone Wolf"           # 0 recruits
    TEAM_LEADER = "Team Leader"       # 1-4 recruits
    SQUAD_LEADER = "Squad Leader"     # 5-9 recruits
    PLATOON_SGT = "Platoon Sergeant"  # 10-24 recruits
    COMPANY_CDR = "Company Commander"  # 25-49 recruits
    BATTALION_CDR = "Battalion Commander"  # 50-99 recruits
    BRIGADE_GENERAL = "Brigade General"    # 100+ recruits

@dataclass
class ReferralCode:
    """Referral code structure"""
    code: str
    user_id: str
    created_at: datetime
    uses_count: int = 0
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_promo: bool = False
    promo_multiplier: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ReferralReward:
    """Reward structure for referrals"""
    xp_amount: int
    reason: str
    multiplier: float = 1.0
    bonus_type: Optional[str] = None

@dataclass
class Recruit:
    """Recruit information"""
    recruit_id: str
    referrer_id: str
    referral_code: str
    joined_at: datetime
    username: str
    ip_address: str
    tier: ReferralTier
    total_xp_earned: int = 0
    trades_completed: int = 0
    current_rank: str = "NIBBLER"
    is_active: bool = True
    last_activity: Optional[datetime] = None

@dataclass
class SquadMember:
    """Squad member for genealogy tracking"""
    user_id: str
    username: str
    rank: str
    tier: ReferralTier
    joined_at: datetime
    xp_contributed: int
    recruits_count: int
    activity_score: float  # 0-100 based on recent activity

class ReferralSystem:
    """Elite military-style referral system"""
    
    # Reward configuration
    REWARDS = {
        'join': ReferralReward(100, "New recruit joined your squad"),
        'first_trade': ReferralReward(50, "Recruit completed first mission"),
        'reach_fang': ReferralReward(25, "Recruit achieved Fang tier"),
        'reach_commander': ReferralReward(100, "Recruit achieved Commander tier"),
        'reach_apex': ReferralReward(250, "Recruit achieved Apex tier"),
        'weekly_active': ReferralReward(10, "Recruit active this week"),
        'trade_milestone': ReferralReward(20, "Recruit trade milestone")  # Every 10 trades
    }
    
    # Bonus multipliers for multiple referrals
    SQUAD_MULTIPLIERS = {
        5: 1.1,    # 5+ recruits = 10% bonus
        10: 1.25,  # 10+ recruits = 25% bonus
        25: 1.5,   # 25+ recruits = 50% bonus
        50: 2.0,   # 50+ recruits = 100% bonus
        100: 3.0   # 100+ recruits = 200% bonus
    }
    
    # Anti-abuse configuration
    MAX_REFERRALS_PER_DAY = 10
    MAX_REFERRALS_PER_IP = 3
    COOLDOWN_BETWEEN_REFERRALS = 300  # 5 minutes
    IP_BLOCK_DURATION = 86400  # 24 hours
    
    def __init__(self, db_path: str = "data/referral_system.db", xp_economy=None):
        self.db_path = db_path
        self.xp_economy = xp_economy
        self._init_database()
        
        # Cache for performance
        self.code_cache: Dict[str, ReferralCode] = {}
        self.ip_tracker: Dict[str, List[datetime]] = {}
        self.blocked_ips: Set[str] = set()
        
        # Load blocked IPs from database
        self._load_blocked_ips()
    
    def _init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Referral codes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_codes (
                code TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP,
                uses_count INTEGER DEFAULT 0,
                max_uses INTEGER,
                expires_at TIMESTAMP,
                is_promo BOOLEAN DEFAULT 0,
                promo_multiplier REAL DEFAULT 1.0,
                metadata TEXT
            )
        ''')
        
        # Recruits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recruits (
                recruit_id TEXT PRIMARY KEY,
                referrer_id TEXT NOT NULL,
                referral_code TEXT,
                joined_at TIMESTAMP,
                username TEXT,
                ip_address TEXT,
                tier INTEGER DEFAULT 1,
                total_xp_earned INTEGER DEFAULT 0,
                trades_completed INTEGER DEFAULT 0,
                current_rank TEXT DEFAULT 'NIBBLER',
                is_active BOOLEAN DEFAULT 1,
                last_activity TIMESTAMP,
                FOREIGN KEY (referral_code) REFERENCES referral_codes(code)
            )
        ''')
        
        # Referral rewards log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id TEXT,
                recruit_id TEXT,
                reward_type TEXT,
                xp_amount INTEGER,
                multiplier REAL DEFAULT 1.0,
                timestamp TIMESTAMP
            )
        ''')
        
        # IP tracking for anti-abuse
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_tracking (
                ip_address TEXT,
                user_id TEXT,
                action TEXT,
                timestamp TIMESTAMP,
                PRIMARY KEY (ip_address, user_id, timestamp)
            )
        ''')
        
        # Blocked IPs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocked_ips (
                ip_address TEXT PRIMARY KEY,
                blocked_at TIMESTAMP,
                reason TEXT,
                expires_at TIMESTAMP
            )
        ''')
        
        # Squad statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS squad_stats (
                user_id TEXT PRIMARY KEY,
                total_recruits INTEGER DEFAULT 0,
                active_recruits INTEGER DEFAULT 0,
                total_xp_from_recruits INTEGER DEFAULT 0,
                squad_rank TEXT DEFAULT 'Lone Wolf',
                last_recruit_at TIMESTAMP,
                streak_days INTEGER DEFAULT 0,
                best_recruit_id TEXT
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_recruits_referrer ON recruits(referrer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rewards_referrer ON referral_rewards(referrer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_tracking ON ip_tracking(ip_address, timestamp)')
        
        conn.commit()
        conn.close()
    
    def generate_referral_code(self, user_id: str, custom_code: Optional[str] = None) -> Tuple[bool, str, ReferralCode]:
        """Generate unique referral code for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if user already has an active code
            cursor.execute('''
                SELECT code, created_at, uses_count FROM referral_codes 
                WHERE user_id = ? AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY created_at DESC LIMIT 1
            ''', (user_id, datetime.now()))
            
            existing = cursor.fetchone()
            if existing:
                code = ReferralCode(
                    code=existing[0],
                    user_id=user_id,
                    created_at=datetime.fromisoformat(existing[1]),
                    uses_count=existing[2]
                )
                return True, "Your active referral code", code
            
            # Generate new code
            if custom_code:
                # Validate custom code
                if len(custom_code) < 4 or len(custom_code) > 20:
                    return False, "Custom code must be 4-20 characters", None
                
                if not custom_code.isalnum():
                    return False, "Custom code must be alphanumeric only", None
                
                # Check if custom code is available
                cursor.execute('SELECT 1 FROM referral_codes WHERE code = ?', (custom_code.upper(),))
                if cursor.fetchone():
                    return False, "This code is already taken", None
                
                code_str = custom_code.upper()
            else:
                # Generate random code
                code_str = self._generate_random_code()
                
                # Ensure uniqueness
                while True:
                    cursor.execute('SELECT 1 FROM referral_codes WHERE code = ?', (code_str,))
                    if not cursor.fetchone():
                        break
                    code_str = self._generate_random_code()
            
            # Create referral code
            code = ReferralCode(
                code=code_str,
                user_id=user_id,
                created_at=datetime.now()
            )
            
            # Save to database
            cursor.execute('''
                INSERT INTO referral_codes (code, user_id, created_at, uses_count)
                VALUES (?, ?, ?, ?)
            ''', (code.code, code.user_id, code.created_at, code.uses_count))
            
            # Initialize squad stats if needed
            cursor.execute('''
                INSERT OR IGNORE INTO squad_stats (user_id) VALUES (?)
            ''', (user_id,))
            
            conn.commit()
            
            # Cache the code
            self.code_cache[code.code] = code
            
            return True, f"Referral code generated: {code.code}", code
            
        except Exception as e:
            logger.error(f"Error generating referral code: {e}")
            return False, "Failed to generate referral code", None
        finally:
            conn.close()
    
    def create_promo_code(
        self, 
        code: str, 
        creator_id: str,
        max_uses: Optional[int] = None,
        expires_in_days: Optional[int] = None,
        xp_multiplier: float = 1.5
    ) -> Tuple[bool, str]:
        """Create a special promo code with bonus rewards"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Validate code
            if len(code) < 4 or len(code) > 20 or not code.isalnum():
                return False, "Invalid promo code format"
            
            code = code.upper()
            
            # Check if code exists
            cursor.execute('SELECT 1 FROM referral_codes WHERE code = ?', (code,))
            if cursor.fetchone():
                return False, "This code already exists"
            
            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now() + timedelta(days=expires_in_days)
            
            # Create promo code
            cursor.execute('''
                INSERT INTO referral_codes 
                (code, user_id, created_at, max_uses, expires_at, is_promo, promo_multiplier)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (code, creator_id, datetime.now(), max_uses, expires_at, True, xp_multiplier))
            
            conn.commit()
            
            # Create code object for cache
            promo = ReferralCode(
                code=code,
                user_id=creator_id,
                created_at=datetime.now(),
                max_uses=max_uses,
                expires_at=expires_at,
                is_promo=True,
                promo_multiplier=xp_multiplier
            )
            
            self.code_cache[code] = promo
            
            details = []
            if max_uses:
                details.append(f"{max_uses} uses")
            if expires_in_days:
                details.append(f"expires in {expires_in_days} days")
            details.append(f"{xp_multiplier}x XP bonus")
            
            return True, f"Promo code '{code}' created ({', '.join(details)})"
            
        except Exception as e:
            logger.error(f"Error creating promo code: {e}")
            return False, "Failed to create promo code"
        finally:
            conn.close()
    
    def use_referral_code(
        self, 
        recruit_id: str, 
        code: str, 
        username: str,
        ip_address: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Use a referral code to join someone's squad"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Anti-abuse checks
            abuse_check = self._check_anti_abuse(recruit_id, ip_address)
            if not abuse_check[0]:
                return False, abuse_check[1], None
            
            # Validate code
            code = code.upper()
            cursor.execute('''
                SELECT user_id, uses_count, max_uses, expires_at, is_promo, promo_multiplier
                FROM referral_codes WHERE code = ?
            ''', (code,))
            
            code_data = cursor.fetchone()
            if not code_data:
                return False, "Invalid referral code", None
            
            referrer_id, uses_count, max_uses, expires_at, is_promo, promo_multiplier = code_data
            
            # Check if recruit is trying to use their own code
            if referrer_id == recruit_id:
                return False, "You cannot use your own referral code", None
            
            # Check if already recruited
            cursor.execute('SELECT 1 FROM recruits WHERE recruit_id = ?', (recruit_id,))
            if cursor.fetchone():
                return False, "You have already been recruited", None
            
            # Check code limits
            if max_uses and uses_count >= max_uses:
                return False, "This code has reached its usage limit", None
            
            if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
                return False, "This code has expired", None
            
            # Create recruit record
            cursor.execute('''
                INSERT INTO recruits 
                (recruit_id, referrer_id, referral_code, joined_at, username, ip_address, tier)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (recruit_id, referrer_id, code, datetime.now(), username, ip_address, ReferralTier.DIRECT.value))
            
            # Update code usage
            cursor.execute('''
                UPDATE referral_codes SET uses_count = uses_count + 1 WHERE code = ?
            ''', (code,))
            
            # Update squad stats
            cursor.execute('''
                UPDATE squad_stats 
                SET total_recruits = total_recruits + 1,
                    active_recruits = active_recruits + 1,
                    last_recruit_at = ?
                WHERE user_id = ?
            ''', (datetime.now(), referrer_id))
            
            # Award XP to referrer
            base_reward = self.REWARDS['join']
            multiplier = self._calculate_multiplier(referrer_id, cursor) * promo_multiplier
            xp_amount = int(base_reward.xp_amount * multiplier)
            
            if self.xp_economy:
                self.xp_economy.add_xp(
                    referrer_id, 
                    xp_amount, 
                    f"New recruit: {username}"
                )
            
            # Log reward
            cursor.execute('''
                INSERT INTO referral_rewards 
                (referrer_id, recruit_id, reward_type, xp_amount, multiplier, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (referrer_id, recruit_id, 'join', xp_amount, multiplier, datetime.now()))
            
            # Track IP
            cursor.execute('''
                INSERT INTO ip_tracking (ip_address, user_id, action, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (ip_address, recruit_id, 'referral_join', datetime.now()))
            
            # Check for multi-tier rewards
            self._process_multi_tier_rewards(referrer_id, cursor)
            
            conn.commit()
            
            # Get referrer info for response
            cursor.execute('SELECT username FROM recruits WHERE recruit_id = ?', (referrer_id,))
            referrer_data = cursor.fetchone()
            referrer_name = referrer_data[0] if referrer_data else "Unknown"
            
            squad_rank = self._get_squad_rank(referrer_id, cursor)
            
            result = {
                'referrer_id': referrer_id,
                'referrer_name': referrer_name,
                'xp_awarded': xp_amount,
                'multiplier': multiplier,
                'is_promo': is_promo,
                'squad_rank': squad_rank.value
            }
            
            welcome_msg = f"Welcome to {referrer_name}'s squad! "
            if is_promo:
                welcome_msg += f"(Promo code - {promo_multiplier}x XP bonus active)"
            
            return True, welcome_msg, result
            
        except Exception as e:
            logger.error(f"Error using referral code: {e}")
            conn.rollback()
            return False, "Failed to process referral", None
        finally:
            conn.close()
    
    def track_recruit_progress(
        self, 
        recruit_id: str, 
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, int]]:
        """Track recruit progress and award rewards"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        rewards_given = []
        
        try:
            # Get recruit info
            cursor.execute('''
                SELECT referrer_id, trades_completed, current_rank 
                FROM recruits WHERE recruit_id = ? AND is_active = 1
            ''', (recruit_id,))
            
            recruit_data = cursor.fetchone()
            if not recruit_data:
                return rewards_given
            
            referrer_id, trades_completed, current_rank = recruit_data
            
            # Process different events
            if event_type == 'trade_completed':
                # Update trade count
                new_trade_count = trades_completed + 1
                cursor.execute('''
                    UPDATE recruits 
                    SET trades_completed = ?, last_activity = ?
                    WHERE recruit_id = ?
                ''', (new_trade_count, datetime.now(), recruit_id))
                
                # First trade bonus
                if trades_completed == 0:
                    reward = self.REWARDS['first_trade']
                    multiplier = self._calculate_multiplier(referrer_id, cursor)
                    xp_amount = int(reward.xp_amount * multiplier)
                    
                    if self.xp_economy:
                        self.xp_economy.add_xp(referrer_id, xp_amount, reward.reason)
                    
                    rewards_given.append((referrer_id, xp_amount))
                    
                    cursor.execute('''
                        INSERT INTO referral_rewards 
                        (referrer_id, recruit_id, reward_type, xp_amount, multiplier, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (referrer_id, recruit_id, 'first_trade', xp_amount, multiplier, datetime.now()))
                
                # Milestone rewards (every 10 trades)
                elif new_trade_count % 10 == 0:
                    reward = self.REWARDS['trade_milestone']
                    multiplier = self._calculate_multiplier(referrer_id, cursor)
                    xp_amount = int(reward.xp_amount * multiplier)
                    
                    if self.xp_economy:
                        self.xp_economy.add_xp(
                            referrer_id, 
                            xp_amount, 
                            f"{reward.reason} ({new_trade_count} trades)"
                        )
                    
                    rewards_given.append((referrer_id, xp_amount))
            
            elif event_type == 'rank_upgraded':
                new_rank = event_data.get('new_rank', '')
                
                # Update recruit rank
                cursor.execute('''
                    UPDATE recruits SET current_rank = ? WHERE recruit_id = ?
                ''', (new_rank, recruit_id))
                
                # Check for rank rewards
                if new_rank == 'FANG' and current_rank != 'FANG':
                    reward = self.REWARDS['reach_fang']
                elif new_rank == 'COMMANDER' and current_rank not in ['COMMANDER', '']:
                    reward = self.REWARDS['reach_commander']
                elif new_rank == '' and current_rank != '':
                    reward = self.REWARDS['reach_apex']
                else:
                    reward = None
                
                if reward:
                    multiplier = self._calculate_multiplier(referrer_id, cursor)
                    xp_amount = int(reward.xp_amount * multiplier)
                    
                    if self.xp_economy:
                        self.xp_economy.add_xp(referrer_id, xp_amount, reward.reason)
                    
                    rewards_given.append((referrer_id, xp_amount))
                    
                    cursor.execute('''
                        INSERT INTO referral_rewards 
                        (referrer_id, recruit_id, reward_type, xp_amount, multiplier, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (referrer_id, recruit_id, f'reach_{new_rank.lower()}', xp_amount, multiplier, datetime.now()))
            
            elif event_type == 'weekly_activity':
                # Award weekly activity bonus
                reward = self.REWARDS['weekly_active']
                multiplier = self._calculate_multiplier(referrer_id, cursor)
                xp_amount = int(reward.xp_amount * multiplier)
                
                if self.xp_economy:
                    self.xp_economy.add_xp(referrer_id, xp_amount, reward.reason)
                
                rewards_given.append((referrer_id, xp_amount))
            
            # Update total XP from recruits
            if rewards_given:
                total_xp = sum(xp for _, xp in rewards_given)
                cursor.execute('''
                    UPDATE squad_stats 
                    SET total_xp_from_recruits = total_xp_from_recruits + ?
                    WHERE user_id = ?
                ''', (total_xp, referrer_id))
            
            conn.commit()
            
            # Process multi-tier rewards
            self._process_multi_tier_rewards(referrer_id, cursor)
            
        except Exception as e:
            logger.error(f"Error tracking recruit progress: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        return rewards_given
    
    def get_squad_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get squad statistics for a user.
        
        Args:
            user_id: User ID to get squad stats for
            
        Returns:
            Dict containing squad statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get squad stats
                cursor.execute('''
                    SELECT * FROM squad_stats WHERE user_id = ?
                ''', (user_id,))
                
                squad_row = cursor.fetchone()
                if not squad_row:
                    return {
                        'total_recruits': 0,
                        'active_recruits': 0,
                        'total_xp': 0,
                        'squad_rank': 'LONE_WOLF'
                    }
                
                return {
                    'total_recruits': squad_row['total_recruits'] or 0,
                    'active_recruits': squad_row['active_recruits'] or 0, 
                    'total_xp': squad_row['total_xp_earned'] or 0,
                    'squad_rank': squad_row['squad_rank'] or 'LONE_WOLF'
                }
                
        except Exception as e:
            logger.error(f"Error getting squad stats for {user_id}: {e}")
            return {
                'total_recruits': 0,
                'active_recruits': 0,
                'total_xp': 0,
                'squad_rank': 'LONE_WOLF'
            }

    def get_squad_genealogy(self, user_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """Get multi-tier squad genealogy tree"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            def build_tree(parent_id: str, depth: int) -> List[Dict[str, Any]]:
                if depth > max_depth:
                    return []
                
                cursor.execute('''
                    SELECT recruit_id, username, current_rank, trades_completed, 
                           total_xp_earned, joined_at, last_activity
                    FROM recruits 
                    WHERE referrer_id = ? AND is_active = 1
                    ORDER BY joined_at DESC
                ''', (parent_id,))
                
                recruits = []
                for row in cursor.fetchall():
                    recruit = {
                        'user_id': row[0],
                        'username': row[1],
                        'rank': row[2],
                        'trades': row[3],
                        'xp_contributed': row[4],
                        'joined_at': row[5],
                        'last_activity': row[6],
                        'tier': depth,
                        'sub_recruits': build_tree(row[0], depth + 1)
                    }
                    recruits.append(recruit)
                
                return recruits
            
            # Get user's squad stats
            cursor.execute('''
                SELECT total_recruits, active_recruits, total_xp_from_recruits, squad_rank
                FROM squad_stats WHERE user_id = ?
            ''', (user_id,))
            
            stats = cursor.fetchone()
            if not stats:
                stats = (0, 0, 0, SquadRank.LONE_WOLF.value)
            
            genealogy = {
                'user_id': user_id,
                'squad_stats': {
                    'total_recruits': stats[0],
                    'active_recruits': stats[1],
                    'total_xp_earned': stats[2],
                    'squad_rank': stats[3]
                },
                'recruits': build_tree(user_id, 1)
            }
            
            return genealogy
            
        except Exception as e:
            logger.error(f"Error getting squad genealogy: {e}")
            return {'error': str(e)}
        finally:
            conn.close()
    
    def get_referral_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top recruiters leaderboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    s.user_id,
                    s.total_recruits,
                    s.active_recruits,
                    s.total_xp_from_recruits,
                    s.squad_rank,
                    r.username
                FROM squad_stats s
                LEFT JOIN recruits r ON s.user_id = r.recruit_id
                WHERE s.total_recruits > 0
                ORDER BY s.total_xp_from_recruits DESC, s.total_recruits DESC
                LIMIT ?
            ''', (limit,))
            
            leaderboard = []
            rank = 1
            
            for row in cursor.fetchall():
                entry = {
                    'rank': rank,
                    'user_id': row[0],
                    'username': row[5] or f"User{row[0][:6]}",
                    'total_recruits': row[1],
                    'active_recruits': row[2],
                    'total_xp': row[3],
                    'squad_rank': row[4],
                    'efficiency': round(row[3] / row[1], 1) if row[1] > 0 else 0
                }
                leaderboard.append(entry)
                rank += 1
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
        finally:
            conn.close()
    
    def get_referral_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive referral statistics for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get squad stats
            cursor.execute('''
                SELECT total_recruits, active_recruits, total_xp_from_recruits, 
                       squad_rank, last_recruit_at, streak_days
                FROM squad_stats WHERE user_id = ?
            ''', (user_id,))
            
            stats_row = cursor.fetchone()
            if not stats_row:
                return self._empty_stats(user_id)
            
            # Get referral code
            cursor.execute('''
                SELECT code, uses_count FROM referral_codes 
                WHERE user_id = ? AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY created_at DESC LIMIT 1
            ''', (user_id, datetime.now()))
            
            code_data = cursor.fetchone()
            
            # Get recent rewards
            cursor.execute('''
                SELECT reward_type, xp_amount, timestamp 
                FROM referral_rewards 
                WHERE referrer_id = ?
                ORDER BY timestamp DESC LIMIT 10
            ''', (user_id,))
            
            recent_rewards = [
                {
                    'type': row[0],
                    'xp': row[1],
                    'timestamp': row[2]
                }
                for row in cursor.fetchall()
            ]
            
            # Get top recruits
            cursor.execute('''
                SELECT recruit_id, username, trades_completed, total_xp_earned, current_rank
                FROM recruits 
                WHERE referrer_id = ? AND is_active = 1
                ORDER BY total_xp_earned DESC LIMIT 5
            ''', (user_id,))
            
            top_recruits = [
                {
                    'user_id': row[0],
                    'username': row[1],
                    'trades': row[2],
                    'xp_contributed': row[3],
                    'rank': row[4]
                }
                for row in cursor.fetchall()
            ]
            
            # Calculate multiplier
            multiplier = self._calculate_multiplier(user_id, cursor)
            
            stats = {
                'user_id': user_id,
                'referral_code': code_data[0] if code_data else None,
                'code_uses': code_data[1] if code_data else 0,
                'squad_stats': {
                    'total_recruits': stats_row[0],
                    'active_recruits': stats_row[1],
                    'total_xp_earned': stats_row[2],
                    'squad_rank': stats_row[3],
                    'last_recruit_at': stats_row[4],
                    'streak_days': stats_row[5]
                },
                'current_multiplier': multiplier,
                'next_multiplier_at': self._get_next_multiplier_threshold(stats_row[0]),
                'recent_rewards': recent_rewards,
                'top_recruits': top_recruits
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting referral stats: {e}")
            return self._empty_stats(user_id)
        finally:
            conn.close()
    
    def format_telegram_response(self, user_id: str) -> str:
        """Format referral stats for Telegram display"""
        stats = self.get_referral_stats(user_id)
        
        lines = [
            "🎖️ **SQUAD RECRUITMENT STATUS** 🎖️",
            "",
            f"**Rank:** {stats['squad_stats']['squad_rank']}",
            f"**Total Recruits:** {stats['squad_stats']['total_recruits']}",
            f"**Active Recruits:** {stats['squad_stats']['active_recruits']}",
            f"**Total XP Earned:** {stats['squad_stats']['total_xp_earned']:}",
            f"**Current Multiplier:** {stats['current_multiplier']}x",
            ""
        ]
        
        if stats['referral_code']:
            lines.extend([
                f"📋 **Your Referral Code:** `{stats['referral_code']}`",
                f"Times Used: {stats['code_uses']}",
                ""
            ])
        else:
            lines.extend([
                "⚠️ No active referral code",
                "Use /refer generate to create one",
                ""
            ])
        
        if stats['top_recruits']:
            lines.append("🏆 **Top Squad Members:**")
            for i, recruit in enumerate(stats['top_recruits'], 1):
                lines.append(
                    f"{i}. {recruit['username']} - "
                    f"{recruit['rank']} - "
                    f"{recruit['xp_contributed']} XP"
                )
            lines.append("")
        
        if stats['next_multiplier_at']:
            lines.append(
                f"📈 Next multiplier boost at "
                f"{stats['next_multiplier_at']} recruits"
            )
        
        lines.extend([
            "",
            "**Commands:**",
            "`/refer generate` - Create referral code",
            "`/refer stats` - View detailed stats",
            "`/refer tree` - View squad genealogy",
            "`/refer leaderboard` - Top recruiters"
        ])
        
        return "\n".join(lines)
    
    # Helper methods
    
    def _generate_random_code(self, length: int = 8) -> str:
        """Generate random alphanumeric code"""
        chars = string.ascii_uppercase + string.digits
        # Avoid confusing characters
        chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def _check_anti_abuse(self, user_id: str, ip_address: str) -> Tuple[bool, str]:
        """Check for abuse patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if IP is blocked
            cursor.execute('''
                SELECT reason, expires_at FROM blocked_ips 
                WHERE ip_address = ? AND expires_at > ?
            ''', (ip_address, datetime.now()))
            
            blocked = cursor.fetchone()
            if blocked:
                return False, f"IP blocked: {blocked[0]}"
            
            # Check recent referrals from this IP
            cutoff_time = datetime.now() - timedelta(hours=24)
            cursor.execute('''
                SELECT COUNT(*) FROM ip_tracking 
                WHERE ip_address = ? AND action = 'referral_join' AND timestamp > ?
            ''', (ip_address, cutoff_time))
            
            ip_count = cursor.fetchone()[0]
            if ip_count >= self.MAX_REFERRALS_PER_IP:
                # Block IP
                cursor.execute('''
                    INSERT OR REPLACE INTO blocked_ips 
                    (ip_address, blocked_at, reason, expires_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    ip_address, 
                    datetime.now(), 
                    "Too many referrals", 
                    datetime.now() + timedelta(seconds=self.IP_BLOCK_DURATION)
                ))
                conn.commit()
                return False, "Too many referrals from this IP"
            
            # Check cooldown
            cursor.execute('''
                SELECT MAX(timestamp) FROM ip_tracking 
                WHERE ip_address = ? AND action = 'referral_join'
            ''', (ip_address,))
            
            last_referral = cursor.fetchone()[0]
            if last_referral:
                last_time = datetime.fromisoformat(last_referral)
                if (datetime.now() - last_time).total_seconds() < self.COOLDOWN_BETWEEN_REFERRALS:
                    return False, "Please wait before using another referral"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Error checking anti-abuse: {e}")
            return True, "OK"  # Allow on error
        finally:
            conn.close()
    
    def _calculate_multiplier(self, user_id: str, cursor) -> float:
        """Calculate reward multiplier based on squad size"""
        cursor.execute(
            'SELECT total_recruits FROM squad_stats WHERE user_id = ?',
            (user_id,)
        )
        
        result = cursor.fetchone()
        if not result:
            return 1.0
        
        recruit_count = result[0]
        multiplier = 1.0
        
        for threshold, mult in sorted(self.SQUAD_MULTIPLIERS.items(), reverse=True):
            if recruit_count >= threshold:
                multiplier = mult
                break
        
        return multiplier
    
    def _get_squad_rank(self, user_id: str, cursor) -> SquadRank:
        """Determine squad rank based on recruit count"""
        cursor.execute(
            'SELECT total_recruits FROM squad_stats WHERE user_id = ?',
            (user_id,)
        )
        
        result = cursor.fetchone()
        if not result:
            return SquadRank.LONE_WOLF
        
        count = result[0]
        
        if count >= 100:
            return SquadRank.BRIGADE_GENERAL
        elif count >= 50:
            return SquadRank.BATTALION_CDR
        elif count >= 25:
            return SquadRank.COMPANY_CDR
        elif count >= 10:
            return SquadRank.PLATOON_SGT
        elif count >= 5:
            return SquadRank.SQUAD_LEADER
        elif count >= 1:
            return SquadRank.TEAM_LEADER
        else:
            return SquadRank.LONE_WOLF
    
    def _get_next_multiplier_threshold(self, current_recruits: int) -> Optional[int]:
        """Get next multiplier threshold"""
        for threshold in sorted(self.SQUAD_MULTIPLIERS.keys()):
            if current_recruits < threshold:
                return threshold
        return None
    
    def _process_multi_tier_rewards(self, direct_referrer_id: str, cursor):
        """Process rewards for multi-tier referrals"""
        # Get parent referrer (tier 2)
        cursor.execute('''
            SELECT referrer_id FROM recruits WHERE recruit_id = ?
        ''', (direct_referrer_id,))
        
        tier2_result = cursor.fetchone()
        if tier2_result and tier2_result[0]:
            tier2_referrer = tier2_result[0]
            # Award 50% of base reward for tier 2
            if self.xp_economy:
                self.xp_economy.add_xp(
                    tier2_referrer, 
                    int(self.REWARDS['join'].xp_amount * 0.5),
                    "Tier 2 recruit joined"
                )
            
            # Get grandparent referrer (tier 3)
            cursor.execute('''
                SELECT referrer_id FROM recruits WHERE recruit_id = ?
            ''', (tier2_referrer,))
            
            tier3_result = cursor.fetchone()
            if tier3_result and tier3_result[0]:
                tier3_referrer = tier3_result[0]
                # Award 25% of base reward for tier 3
                if self.xp_economy:
                    self.xp_economy.add_xp(
                        tier3_referrer,
                        int(self.REWARDS['join'].xp_amount * 0.25),
                        "Tier 3 recruit joined"
                    )
    
    def _load_blocked_ips(self):
        """Load blocked IPs into memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT ip_address FROM blocked_ips WHERE expires_at > ?
            ''', (datetime.now(),))
            
            self.blocked_ips = {row[0] for row in cursor.fetchall()}
            
        except Exception as e:
            logger.error(f"Error loading blocked IPs: {e}")
        finally:
            conn.close()
    
    def _empty_stats(self, user_id: str) -> Dict[str, Any]:
        """Return empty stats structure"""
        return {
            'user_id': user_id,
            'referral_code': None,
            'code_uses': 0,
            'squad_stats': {
                'total_recruits': 0,
                'active_recruits': 0,
                'total_xp_earned': 0,
                'squad_rank': SquadRank.LONE_WOLF.value,
                'last_recruit_at': None,
                'streak_days': 0
            },
            'current_multiplier': 1.0,
            'next_multiplier_at': 5,
            'recent_rewards': [],
            'top_recruits': []
        }

# Telegram command handler
class ReferralCommandHandler:
    """Handle /refer commands in Telegram"""
    
    def __init__(self, referral_system: ReferralSystem):
        self.referral_system = referral_system
    
    def handle_command(self, user_id: str, username: str, args: List[str]) -> str:
        """Process /refer command"""
        if not args:
            return self.referral_system.format_telegram_response(user_id)
        
        subcommand = args[0].lower()
        
        if subcommand == 'generate':
            custom_code = args[1] if len(args) > 1 else None
            success, message, code = self.referral_system.generate_referral_code(
                user_id, custom_code
            )
            
            if success and code:
                return (
                    f"✅ {message}\n\n"
                    f"📋 **Your Code:** `{code.code}`\n"
                    f"Share this code to build your squad!\n\n"
                    f"Rewards per recruit:\n"
                    f"• 100 XP when they join\n"
                    f"• 50 XP on first trade\n"
                    f"• 25 XP when they reach Fang\n"
                    f"• Bonus multipliers for larger squads"
                )
            else:
                return f"❌ {message}"
        
        elif subcommand == 'stats':
            return self._format_detailed_stats(user_id)
        
        elif subcommand == 'tree':
            genealogy = self.referral_system.get_squad_genealogy(user_id)
            return self._format_genealogy_tree(genealogy)
        
        elif subcommand == 'leaderboard':
            leaderboard = self.referral_system.get_referral_leaderboard()
            return self._format_leaderboard(leaderboard)
        
        elif subcommand == 'use' and len(args) > 1:
            # This would typically be handled during onboarding
            return "Please use referral codes during the initial setup process"
        
        else:
            return (
                "**Referral Commands:**\n"
                "`/refer` - View your referral status\n"
                "`/refer generate [code]` - Create referral code\n"
                "`/refer stats` - Detailed statistics\n"
                "`/refer tree` - View squad genealogy\n"
                "`/refer leaderboard` - Top recruiters"
            )
    
    def _format_detailed_stats(self, user_id: str) -> str:
        """Format detailed statistics"""
        stats = self.referral_system.get_referral_stats(user_id)
        
        lines = [
            "📊 **DETAILED REFERRAL STATISTICS** 📊",
            "",
            f"**Squad Rank:** {stats['squad_stats']['squad_rank']}",
            f"**Total Recruits:** {stats['squad_stats']['total_recruits']}",
            f"**Active Recruits:** {stats['squad_stats']['active_recruits']}",
            f"**Total XP Earned:** {stats['squad_stats']['total_xp_earned']:}",
            f"**Current Multiplier:** {stats['current_multiplier']}x",
            ""
        ]
        
        if stats['recent_rewards']:
            lines.append("💰 **Recent Rewards:**")
            for reward in stats['recent_rewards'][:5]:
                lines.append(
                    f"• {reward['type'].replace('_', ' ').title()} - "
                    f"{reward['xp']} XP"
                )
            lines.append("")
        
        if stats['top_recruits']:
            lines.append("🏆 **MVP Squad Members:**")
            for recruit in stats['top_recruits']:
                lines.append(
                    f"• {recruit['username']} ({recruit['rank']}) - "
                    f"{recruit['trades']} trades, "
                    f"{recruit['xp_contributed']} XP contributed"
                )
        
        return "\n".join(lines)
    
    def _format_genealogy_tree(self, genealogy: Dict[str, Any]) -> str:
        """Format squad genealogy tree"""
        lines = [
            "🌳 **SQUAD GENEALOGY TREE** 🌳",
            "",
            f"Total Squad Size: {genealogy['squad_stats']['total_recruits']}",
            ""
        ]
        
        def format_recruit(recruit: Dict[str, Any], indent: int = 0):
            prefix = "  " * indent + ("└─" if indent > 0 else "")
            lines.append(
                f"{prefix}{recruit['username']} "
                f"({recruit['rank']}) - "
                f"{recruit['trades']} trades"
            )
            
            for sub_recruit in recruit.get('sub_recruits', []):
                format_recruit(sub_recruit, indent + 1)
        
        for recruit in genealogy['recruits']:
            format_recruit(recruit)
        
        if not genealogy['recruits']:
            lines.append("No recruits yet. Start building your squad!")
        
        return "\n".join(lines)
    
    def _format_leaderboard(self, leaderboard: List[Dict[str, Any]]) -> str:
        """Format leaderboard display"""
        lines = [
            "🏆 **TOP SQUAD COMMANDERS** 🏆",
            ""
        ]
        
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        
        for entry in leaderboard:
            medal = medals.get(entry['rank'], f"{entry['rank']}.")
            lines.append(
                f"{medal} {entry['username']} - "
                f"{entry['squad_rank']} - "
                f"{entry['total_recruits']} recruits - "
                f"{entry['total_xp']:} XP"
            )
        
        return "\n".join(lines)

# Integration hooks for other systems
class ReferralIntegration:
    """Integration hooks for referral system"""
    
    def __init__(self, referral_system: ReferralSystem):
        self.referral_system = referral_system
    
    def on_trade_completed(self, user_id: str, trade_data: Dict[str, Any]) -> None:
        """Called when a user completes a trade"""
        try:
            rewards = self.referral_system.track_recruit_progress(
                user_id, 
                'trade_completed',
                trade_data
            )
            
            if rewards:
                logger.info(f"Referral rewards given for trade: {rewards}")
        except Exception as e:
            logger.error(f"Error processing trade referral rewards: {e}")
    
    def on_rank_upgraded(self, user_id: str, new_rank: str, old_rank: str) -> None:
        """Called when a user's rank is upgraded"""
        try:
            rewards = self.referral_system.track_recruit_progress(
                user_id,
                'rank_upgraded',
                {'new_rank': new_rank, 'old_rank': old_rank}
            )
            
            if rewards:
                logger.info(f"Referral rewards given for rank upgrade: {rewards}")
        except Exception as e:
            logger.error(f"Error processing rank referral rewards: {e}")
    
    def on_weekly_activity_check(self, user_id: str) -> None:
        """Called during weekly activity checks"""
        try:
            rewards = self.referral_system.track_recruit_progress(
                user_id,
                'weekly_activity'
            )
            
            if rewards:
                logger.info(f"Weekly activity rewards given: {rewards}")
        except Exception as e:
            logger.error(f"Error processing weekly activity rewards: {e}")

# Example usage
if __name__ == "__main__":
    # Initialize with XP economy integration
    from xp_economy import XPEconomy
    
    xp_economy = XPEconomy()
    referral_system = ReferralSystem(xp_economy=xp_economy)
    
    # Generate referral code
    success, message, code = referral_system.generate_referral_code("user123", "ELITE")
    print(f"Generate code: {message}")
    
    # Use referral code
    success, message, result = referral_system.use_referral_code(
        "new_user456",
        "ELITE",
        "NewRecruit",
        "192.168.1.1"
    )
    print(f"Use code: {message}")
    
    # Track progress
    rewards = referral_system.track_recruit_progress(
        "new_user456",
        "trade_completed"
    )
    print(f"Rewards given: {rewards}")
    
    # Get stats
    stats = referral_system.get_referral_stats("user123")
    print(f"Referral stats: {stats}")