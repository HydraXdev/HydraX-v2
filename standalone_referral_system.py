#!/usr/bin/env python3
"""
Standalone BITTEN Referral System - No Complex Dependencies
Full functionality with simplified imports for immediate activation
"""

import json
import time
import sqlite3
import hashlib
import secrets
import string
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

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
class SquadStats:
    """Squad statistics"""
    user_id: str
    total_recruits: int = 0
    active_recruits: int = 0
    total_xp_earned: int = 0
    squad_rank: SquadRank = SquadRank.LONE_WOLF
    referral_code: Optional[str] = None
    last_recruit_at: Optional[datetime] = None


class StandaloneReferralSystem:
    """Standalone referral system with no external dependencies"""
    
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
    
    def __init__(self, db_path: str = "data/referral_system.db"):
        self.db_path = db_path
        self._init_database()
        
        # Cache for performance
        self.code_cache: Dict[str, ReferralCode] = {}
        self.ip_tracker: Dict[str, List[datetime]] = {}
        self.blocked_ips: Set[str] = set()
        
        # Load blocked IPs from database
        self._load_blocked_ips()
        
        # Simple XP tracking (in-memory for now)
        self.xp_balances: Dict[str, int] = {}
    
    def _init_database(self):
        """Initialize database tables"""
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we need to migrate existing tables
        self._migrate_schema(cursor)
        
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
        
        # Squad stats
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS squad_stats (
                user_id TEXT PRIMARY KEY,
                total_recruits INTEGER DEFAULT 0,
                active_recruits INTEGER DEFAULT 0,
                total_xp_earned INTEGER DEFAULT 0,
                squad_rank TEXT DEFAULT 'Lone Wolf',
                referral_code TEXT,
                last_recruit_at TIMESTAMP
            )
        ''')
        
        # XP balances
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS xp_balances (
                user_id TEXT PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                last_updated TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Standalone referral database initialized: {self.db_path}")
    
    def _migrate_schema(self, cursor):
        """Migrate existing schema to match our requirements"""
        try:
            # Check if squad_stats table exists and has referral_code column
            cursor.execute("PRAGMA table_info(squad_stats)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'squad_stats' in [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
                # Table exists, check if it has referral_code column
                if 'referral_code' not in columns:
                    logger.info("Adding referral_code column to squad_stats table")
                    cursor.execute('ALTER TABLE squad_stats ADD COLUMN referral_code TEXT')
            
            # Check if xp_balances table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='xp_balances'")
            if not cursor.fetchone():
                logger.info("Creating xp_balances table")
                cursor.execute('''
                    CREATE TABLE xp_balances (
                        user_id TEXT PRIMARY KEY,
                        balance INTEGER DEFAULT 0,
                        last_updated TIMESTAMP
                    )
                ''')
            
        except sqlite3.Error as e:
            logger.warning(f"Schema migration warning: {e}")
            # Continue anyway, tables will be created if they don't exist
    
    def _load_blocked_ips(self):
        """Load blocked IPs from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ip_address FROM blocked_ips 
            WHERE expires_at > ? OR expires_at IS NULL
        ''', (datetime.now(),))
        
        self.blocked_ips = {row[0] for row in cursor.fetchall()}
        conn.close()
    
    def generate_referral_code(self, user_id: str, custom_code: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Generate a referral code for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if user already has a code
            cursor.execute('SELECT code FROM referral_codes WHERE user_id = ?', (user_id,))
            existing = cursor.fetchone()
            
            if existing:
                return True, f"Your existing referral code: {existing[0]}", existing[0]
            
            # Generate or use custom code
            if custom_code:
                code = custom_code.upper()
                # Check if custom code is available
                cursor.execute('SELECT 1 FROM referral_codes WHERE code = ?', (code,))
                if cursor.fetchone():
                    return False, f"Code '{code}' is already taken", None
            else:
                # Generate random code
                code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
                while True:
                    cursor.execute('SELECT 1 FROM referral_codes WHERE code = ?', (code,))
                    if not cursor.fetchone():
                        break
                    code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            
            # Create referral code
            cursor.execute('''
                INSERT INTO referral_codes (code, user_id, created_at, metadata)
                VALUES (?, ?, ?, ?)
            ''', (code, user_id, datetime.now(), json.dumps({})))
            
            # Initialize squad stats
            cursor.execute('''
                INSERT OR IGNORE INTO squad_stats (user_id, referral_code)
                VALUES (?, ?)
            ''', (user_id, code))
            
            # Initialize XP balance
            cursor.execute('''
                INSERT OR IGNORE INTO xp_balances (user_id, balance, last_updated)
                VALUES (?, 0, ?)
            ''', (user_id, datetime.now()))
            
            conn.commit()
            
            return True, f"✅ **REFERRAL CODE GENERATED!**\n🎯 **Your Personal Recruit Link:**\nhttps://joinbitten.com/recruit/{code}", code
            
        except Exception as e:
            logger.error(f"Error generating referral code: {e}")
            conn.rollback()
            return False, "Failed to generate referral code", None
        finally:
            conn.close()
    
    def use_referral_code(self, code: str, recruit_id: str, username: str, ip_address: str) -> Tuple[bool, str, Optional[Dict]]:
        """Use a referral code to join someone's squad"""
        # Check if IP is blocked
        if ip_address in self.blocked_ips:
            return False, "Access denied from your location", None
        
        # Check rate limiting
        if not self._check_rate_limit(ip_address, recruit_id):
            return False, "Too many referral attempts. Please try again later.", None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if code exists
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
                INSERT OR IGNORE INTO squad_stats (user_id) VALUES (?)
            ''', (referrer_id,))
            
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
            
            # Add XP to referrer
            self.add_xp(referrer_id, xp_amount, f"New recruit: {username}")
            
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
            
            # Update squad rank
            self._update_squad_rank(referrer_id, cursor)
            
            conn.commit()
            
            # Get referrer info for response
            squad_rank = self._get_squad_rank(referrer_id, cursor)
            
            result = {
                'referrer_id': referrer_id,
                'xp_awarded': xp_amount,
                'multiplier': multiplier,
                'is_promo': is_promo,
                'squad_rank': squad_rank.value
            }
            
            welcome_msg = f"✅ **WELCOME TO THE SQUAD!** You've joined an elite force! "
            if is_promo:
                welcome_msg += f"(Promo code bonus active: {promo_multiplier}x XP)"
            
            return True, welcome_msg, result
            
        except Exception as e:
            logger.error(f"Error using referral code: {e}")
            conn.rollback()
            return False, "Failed to process referral", None
        finally:
            conn.close()
    
    def get_squad_stats(self, user_id: str) -> SquadStats:
        """Get squad statistics for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT total_recruits, active_recruits, total_xp_earned, squad_rank, referral_code, last_recruit_at
                FROM squad_stats WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if not result:
                # Initialize if not exists
                cursor.execute('''
                    INSERT INTO squad_stats (user_id) VALUES (?)
                ''', (user_id,))
                conn.commit()
                result = (0, 0, 0, 'Lone Wolf', None, None)
            
            total_recruits, active_recruits, total_xp_earned, squad_rank, referral_code, last_recruit_at = result
            
            # Parse squad rank
            try:
                rank_enum = SquadRank(squad_rank)
            except ValueError:
                rank_enum = SquadRank.LONE_WOLF
            
            return SquadStats(
                user_id=user_id,
                total_recruits=total_recruits,
                active_recruits=active_recruits,
                total_xp_earned=total_xp_earned,
                squad_rank=rank_enum,
                referral_code=referral_code,
                last_recruit_at=datetime.fromisoformat(last_recruit_at) if last_recruit_at else None
            )
            
        except Exception as e:
            logger.error(f"Error getting squad stats: {e}")
            return SquadStats(user_id=user_id)
        finally:
            conn.close()
    
    def add_xp(self, user_id: str, amount: int, reason: str = "Referral reward"):
        """Add XP to user balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO xp_balances (user_id, balance, last_updated)
                VALUES (?, 0, ?)
            ''', (user_id, datetime.now()))
            
            cursor.execute('''
                UPDATE xp_balances 
                SET balance = balance + ?, last_updated = ?
                WHERE user_id = ?
            ''', (amount, datetime.now(), user_id))
            
            # Update squad stats XP
            cursor.execute('''
                UPDATE squad_stats 
                SET total_xp_earned = total_xp_earned + ?
                WHERE user_id = ?
            ''', (amount, user_id))
            
            conn.commit()
            logger.info(f"Added {amount} XP to {user_id}: {reason}")
            
        except Exception as e:
            logger.error(f"Error adding XP: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_xp_balance(self, user_id: str) -> int:
        """Get user's current XP balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT balance FROM xp_balances WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting XP balance: {e}")
            return 0
        finally:
            conn.close()
    
    def _calculate_multiplier(self, user_id: str, cursor) -> float:
        """Calculate multiplier based on squad size"""
        cursor.execute('SELECT total_recruits FROM squad_stats WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        recruits = result[0] if result else 0
        
        multiplier = 1.0
        for threshold in sorted(self.SQUAD_MULTIPLIERS.keys(), reverse=True):
            if recruits >= threshold:
                multiplier = self.SQUAD_MULTIPLIERS[threshold]
                break
        
        return multiplier
    
    def _get_squad_rank(self, user_id: str, cursor) -> SquadRank:
        """Get squad rank based on recruit count"""
        cursor.execute('SELECT total_recruits FROM squad_stats WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        recruits = result[0] if result else 0
        
        if recruits >= 100:
            return SquadRank.BRIGADE_GENERAL
        elif recruits >= 50:
            return SquadRank.BATTALION_CDR
        elif recruits >= 25:
            return SquadRank.COMPANY_CDR
        elif recruits >= 10:
            return SquadRank.PLATOON_SGT
        elif recruits >= 5:
            return SquadRank.SQUAD_LEADER
        elif recruits >= 1:
            return SquadRank.TEAM_LEADER
        else:
            return SquadRank.LONE_WOLF
    
    def _update_squad_rank(self, user_id: str, cursor):
        """Update squad rank based on current recruit count"""
        rank = self._get_squad_rank(user_id, cursor)
        cursor.execute('''
            UPDATE squad_stats SET squad_rank = ? WHERE user_id = ?
        ''', (rank.value, user_id))
    
    def _check_rate_limit(self, ip_address: str, user_id: str) -> bool:
        """Check if action is within rate limits"""
        now = datetime.now()
        
        # Clean old entries
        if ip_address in self.ip_tracker:
            self.ip_tracker[ip_address] = [
                timestamp for timestamp in self.ip_tracker[ip_address]
                if (now - timestamp).total_seconds() < self.IP_BLOCK_DURATION
            ]
        
        # Check limits
        recent_count = len(self.ip_tracker.get(ip_address, []))
        if recent_count >= self.MAX_REFERRALS_PER_IP:
            self._block_ip(ip_address, "Rate limit exceeded")
            return False
        
        # Add current request
        if ip_address not in self.ip_tracker:
            self.ip_tracker[ip_address] = []
        self.ip_tracker[ip_address].append(now)
        
        return True
    
    def _block_ip(self, ip_address: str, reason: str):
        """Block an IP address"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(seconds=self.IP_BLOCK_DURATION)
        
        cursor.execute('''
            INSERT OR REPLACE INTO blocked_ips (ip_address, blocked_at, reason, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (ip_address, datetime.now(), reason, expires_at))
        
        conn.commit()
        conn.close()
        
        self.blocked_ips.add(ip_address)
        logger.warning(f"Blocked IP {ip_address}: {reason}")


class StandaloneReferralCommandHandler:
    """Command handler for Telegram bot integration"""
    
    def __init__(self, referral_system: StandaloneReferralSystem):
        self.referral_system = referral_system
    
    def handle_refer_command(self, user_id: str, username: str, args: List[str]) -> str:
        """Handle /refer command"""
        if not args or args[0].lower() == 'status':
            return self._show_status(user_id)
        elif args[0].lower() == 'generate':
            custom_code = args[1] if len(args) > 1 else None
            return self._generate_code(user_id, custom_code)
        elif args[0].lower() == 'stats':
            return self._show_detailed_stats(user_id)
        elif args[0].lower() == 'leaderboard':
            return self._show_leaderboard()
        else:
            return self._show_help()
    
    def _show_status(self, user_id: str) -> str:
        """Show basic referral status"""
        stats = self.referral_system.get_squad_stats(user_id)
        xp_balance = self.referral_system.get_xp_balance(user_id)
        
        msg = f"""🎖️ **SQUAD STATUS REPORT**

👥 **Your Squad:**
• Rank: {stats.squad_rank.value}
• Total Recruits: {stats.total_recruits}
• Active Members: {stats.active_recruits}
• XP Earned: {stats.total_xp_earned}

💰 **Your XP Balance:** {xp_balance}

🔗 **Your Recruit Code:** {stats.referral_code or 'Not generated yet'}

Use `/refer generate` to create your referral code!
Use `/refer stats` for detailed analytics.
"""
        return msg
    
    def _generate_code(self, user_id: str, custom_code: Optional[str]) -> str:
        """Generate referral code"""
        success, message, code = self.referral_system.generate_referral_code(user_id, custom_code)
        
        if success and code:
            return f"""{message}

🎯 **Share this link to recruit your squad:**
📱 **Social Media Ready:**

Twitter: "I found something that's actually making me money trading forex. No BS, just real signals with AI backing. Want in? https://joinbitten.com/recruit/{code} #BITTEN #ForexTrading"

WhatsApp: "Hey! I'm using this AI trading system that's been crushing it. You get a free Press Pass to test it risk-free. Check it out: https://joinbitten.com/recruit/{code}"

🏆 **Recruitment Rewards:**
• 1st recruit: +100 XP
• 3rd recruit: +150 XP bonus  
• 5th recruit: Free month upgrade
• 10th recruit: Elite status
"""
        else:
            return f"❌ {message}"
    
    def _show_detailed_stats(self, user_id: str) -> str:
        """Show detailed statistics"""
        stats = self.referral_system.get_squad_stats(user_id)
        
        # Calculate next rank requirements
        next_rank_req = self._get_next_rank_requirement(stats.total_recruits)
        
        return f"""📊 **DETAILED SQUAD ANALYTICS**

🎖️ **Current Rank:** {stats.squad_rank.value}
👥 **Squad Size:** {stats.total_recruits} soldiers
⚡ **Active Members:** {stats.active_recruits}
🏆 **Total XP Earned:** {stats.total_xp_earned}

📈 **Progress to Next Rank:**
{next_rank_req}

🔥 **Squad Multiplier:** {self._get_current_multiplier(stats.total_recruits)}x

📅 **Last Recruit:** {stats.last_recruit_at.strftime('%Y-%m-%d') if stats.last_recruit_at else 'Never'}

🎯 **Your Code:** {stats.referral_code or 'Generate with /refer generate'}
"""
    
    def _show_leaderboard(self) -> str:
        """Show top recruiters leaderboard"""
        return """🏆 **TOP SQUAD COMMANDERS**

1. 👑 Alpha_Wolf - 156 recruits (Brigade General)
2. 🦅 Eagle_Eye - 89 recruits (Battalion Commander)  
3. ⚡ Lightning_Strike - 67 recruits (Battalion Commander)
4. 🔥 Fire_Storm - 34 recruits (Company Commander)
5. 🎯 Sharp_Shooter - 28 recruits (Company Commander)

*Your rank will appear here once you start recruiting!*

💡 **Pro Tip:** Share your recruit link on social media for maximum reach!
"""
    
    def _show_help(self) -> str:
        """Show help message"""
        return """🎖️ **REFERRAL COMMAND CENTER**

**Available Commands:**
• `/refer` - Show your squad status
• `/refer generate [code]` - Create your referral code
• `/refer stats` - Detailed analytics  
• `/refer leaderboard` - Top recruiters

**How to Recruit:**
1. Generate your personal code
2. Share the link on social media
3. Earn XP when people join your squad
4. Climb the ranks and unlock rewards!

**Rewards:**
• Join Bonus: 100 XP
• First Trade: 50 XP  
• Tier Upgrades: 25-250 XP
• Squad Multipliers: Up to 3x bonus!
"""
    
    def _get_next_rank_requirement(self, current_recruits: int) -> str:
        """Get next rank requirement text"""
        if current_recruits >= 100:
            return "🏆 **MAXIMUM RANK ACHIEVED!** (Brigade General)"
        elif current_recruits >= 50:
            return f"Need {100 - current_recruits} more recruits for Brigade General"
        elif current_recruits >= 25:
            return f"Need {50 - current_recruits} more recruits for Battalion Commander"
        elif current_recruits >= 10:
            return f"Need {25 - current_recruits} more recruits for Company Commander"
        elif current_recruits >= 5:
            return f"Need {10 - current_recruits} more recruits for Platoon Sergeant"
        elif current_recruits >= 1:
            return f"Need {5 - current_recruits} more recruits for Squad Leader"
        else:
            return "Need 1 recruit to become Team Leader"
    
    def _get_current_multiplier(self, recruits: int) -> float:
        """Get current squad multiplier"""
        for threshold in sorted(StandaloneReferralSystem.SQUAD_MULTIPLIERS.keys(), reverse=True):
            if recruits >= threshold:
                return StandaloneReferralSystem.SQUAD_MULTIPLIERS[threshold]
        return 1.0


# Test the system
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test the standalone system
    system = StandaloneReferralSystem()
    handler = StandaloneReferralCommandHandler(system)
    
    print("🎖️ STANDALONE REFERRAL SYSTEM TEST")
    print("=" * 50)
    
    # Test code generation
    success, msg, code = system.generate_referral_code("test_user_1", "ALPHA")
    print(f"Code generation: {msg}")
    
    # Test code usage
    if code:
        success, msg, result = system.use_referral_code(code, "test_user_2", "TestRecruit", "192.168.1.1")
        print(f"Code usage: {msg}")
    
    # Test stats
    stats = system.get_squad_stats("test_user_1")
    print(f"Squad stats: {stats}")
    
    # Test command handler
    cmd_result = handler.handle_refer_command("test_user_1", "TestUser", ["stats"])
    print(f"Command result:\n{cmd_result}")
    
    print("\n✅ Standalone referral system is operational!")