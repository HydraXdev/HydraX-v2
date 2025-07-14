"""
BITTEN ALLY CODE System
Secure tactical access codes for special operations
"""

import sqlite3
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import os

class AllyCodeManager:
    def __init__(self, db_path: str = "data/ally_codes.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize the ally code database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main ally codes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ally_codes (
                code TEXT PRIMARY KEY,
                code_type TEXT NOT NULL,
                discount_type TEXT NOT NULL,
                discount_value REAL NOT NULL,
                uses_remaining INTEGER,
                max_uses INTEGER,
                created_date TEXT NOT NULL,
                expires_date TEXT,
                active BOOLEAN DEFAULT 1,
                metadata TEXT,
                creator TEXT
            )
        ''')
        
        # Usage tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                user_id TEXT,
                email TEXT,
                telegram_id TEXT,
                stripe_session_id TEXT,
                used_date TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (code) REFERENCES ally_codes (code)
            )
        ''')
        
        # Founder status tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS founder_status (
                telegram_id TEXT PRIMARY KEY,
                founder_code TEXT NOT NULL,
                activated_date TEXT NOT NULL,
                current_tier TEXT,
                lifetime_discount REAL DEFAULT 89.0,
                special_medals BOOLEAN DEFAULT 1,
                total_savings REAL DEFAULT 0.0,
                FOREIGN KEY (founder_code) REFERENCES ally_codes (code)
            )
        ''')
        
        # Commission tracking for influencers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                influencer_name TEXT NOT NULL,
                commission_rate REAL NOT NULL,
                payment_amount REAL NOT NULL,
                commission_amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                paid BOOLEAN DEFAULT 0,
                stripe_session_id TEXT,
                FOREIGN KEY (code) REFERENCES ally_codes (code)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_founder_codes(self):
        """Create the 10 founder legacy codes"""
        founder_codes = [
            f"FOUNDER{str(i).zfill(2)}" for i in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90]
        ]
        
        created_codes = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for code in founder_codes:
            try:
                cursor.execute('''
                    INSERT INTO ally_codes 
                    (code, code_type, discount_type, discount_value, uses_remaining, max_uses, created_date, metadata, creator)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    code,
                    'FOUNDER_LEGACY',
                    'LIFETIME_TIER',
                    89.0,  # Lifetime $89 tier value
                    1,     # Single use
                    1,     # Max 1 use
                    datetime.now().isoformat(),
                    json.dumps({
                        'lifetime_tier': 'FANG',
                        'original_price': 89,
                        'description': 'Founder Legacy - Lifetime FANG Access',
                        'special_medals': True,
                        'founder_privileges': True
                    }),
                    'SYSTEM'
                ))
                created_codes.append(code)
            except sqlite3.IntegrityError:
                pass  # Code already exists
        
        conn.commit()
        conn.close()
        return created_codes
    
    def create_influencer_code(self, influencer_name: str, commission_rate: float = 0.5, 
                              discount_percent: float = 50.0, max_uses: int = 100) -> str:
        """Create an influencer referral code"""
        code = influencer_name.upper().replace(' ', '')[:8]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO ally_codes 
            (code, code_type, discount_type, discount_value, uses_remaining, max_uses, created_date, metadata, creator)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            code,
            'INFLUENCER',
            'FIRST_MONTH_PERCENT',
            discount_percent,
            max_uses,
            max_uses,
            datetime.now().isoformat(),
            json.dumps({
                'influencer_name': influencer_name,
                'commission_rate': commission_rate,
                'discount_percent': discount_percent,
                'description': f'{influencer_name} - {discount_percent}% off first month'
            }),
            influencer_name
        ))
        
        conn.commit()
        conn.close()
        return code
    
    def validate_ally_code(self, code: str) -> Dict:
        """Validate an ally code and return its details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM ally_codes WHERE code = ? AND active = 1
        ''', (code.upper(),))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {'valid': False, 'error': 'ALLY CODE not recognized'}
        
        code_data = {
            'code': result[0],
            'code_type': result[1],
            'discount_type': result[2],
            'discount_value': result[3],
            'uses_remaining': result[4],
            'max_uses': result[5],
            'created_date': result[6],
            'expires_date': result[7],
            'metadata': json.loads(result[9]) if result[9] else {}
        }
        
        # Check if expired
        if code_data['expires_date']:
            if datetime.fromisoformat(code_data['expires_date']) < datetime.now():
                return {'valid': False, 'error': 'ALLY CODE expired'}
        
        # Check if uses remaining
        if code_data['uses_remaining'] <= 0:
            return {'valid': False, 'error': 'ALLY CODE already used'}
        
        code_data['valid'] = True
        return code_data
    
    def bind_founder_to_telegram(self, founder_code: str, telegram_id: str, tier: str) -> Dict:
        """Bind a founder code to a specific Telegram ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if code is already bound to someone else
        cursor.execute('''
            SELECT telegram_id FROM founder_status WHERE founder_code = ?
        ''', (founder_code,))
        existing = cursor.fetchone()
        
        if existing and existing[0] != telegram_id:
            conn.close()
            return {'success': False, 'error': f'FOUNDER code already bound to another user'}
        
        # Check if this telegram ID already has a founder code
        cursor.execute('''
            SELECT founder_code FROM founder_status WHERE telegram_id = ?
        ''', (telegram_id,))
        existing_user = cursor.fetchone()
        
        if existing_user and existing_user[0] != founder_code:
            conn.close()
            return {'success': False, 'error': f'User already has founder status with different code'}
        
        # Bind the founder code
        cursor.execute('''
            INSERT OR REPLACE INTO founder_status 
            (telegram_id, founder_code, activated_date, current_tier, lifetime_discount, special_medals, total_savings)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            telegram_id,
            founder_code,
            datetime.now().isoformat(),
            tier,
            89.0,
            True,
            0.0
        ))
        
        conn.commit()
        conn.close()
        return {'success': True, 'message': f'FOUNDER {founder_code} bound to Telegram user'}
    
    def check_founder_status(self, telegram_id: str) -> Dict:
        """Check if a Telegram user has founder status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT founder_code, activated_date, current_tier, lifetime_discount, special_medals, total_savings
            FROM founder_status WHERE telegram_id = ?
        ''', (telegram_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'is_founder': True,
                'founder_code': result[0],
                'activated_date': result[1],
                'current_tier': result[2],
                'lifetime_discount': result[3],
                'special_medals': result[4],
                'total_savings': result[5]
            }
        else:
            return {'is_founder': False}
    
    def apply_founder_upgrade(self, telegram_id: str, new_tier: str, new_tier_price: int) -> Dict:
        """Apply founder discount to an upgrade"""
        founder_status = self.check_founder_status(telegram_id)
        
        if not founder_status['is_founder']:
            return {'founder_discount': False, 'final_price': new_tier_price}
        
        discount_amount = int(founder_status['lifetime_discount'] * 100)  # $89 to cents
        final_price = max(0, new_tier_price - discount_amount)
        savings = new_tier_price - final_price
        
        # Update founder status
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE founder_status 
            SET current_tier = ?, total_savings = total_savings + ?
            WHERE telegram_id = ?
        ''', (new_tier, savings / 100, telegram_id))
        
        conn.commit()
        conn.close()
        
        return {
            'founder_discount': True,
            'original_price': new_tier_price,
            'discount_amount': discount_amount,
            'final_price': final_price,
            'savings': savings,
            'founder_code': founder_status['founder_code'],
            'total_lifetime_savings': founder_status['total_savings'] + (savings / 100)
        }

    def use_ally_code(self, code: str, user_id: str = None, email: str = None, 
                      telegram_id: str = None, stripe_session_id: str = None, ip_address: str = None) -> Dict:
        """Use an ally code and track the usage"""
        validation = self.validate_ally_code(code)
        if not validation['valid']:
            return validation
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Decrease uses remaining
        cursor.execute('''
            UPDATE ally_codes SET uses_remaining = uses_remaining - 1
            WHERE code = ?
        ''', (code.upper(),))
        
        # Record usage
        cursor.execute('''
            INSERT INTO code_usage 
            (code, user_id, email, telegram_id, stripe_session_id, used_date, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            code.upper(),
            user_id,
            email,
            telegram_id,
            stripe_session_id,
            datetime.now().isoformat(),
            ip_address
        ))
        
        # If this is a founder code, bind it to the telegram ID
        if validation['code_type'] == 'FOUNDER_LEGACY' and telegram_id:
            tier = 'FANG'  # Default tier, will be updated when they complete payment
            self.bind_founder_to_telegram(code.upper(), telegram_id, tier)
        
        # If influencer code, record commission
        if validation['code_type'] == 'INFLUENCER':
            metadata = validation['metadata']
            commission_rate = metadata.get('commission_rate', 0.5)
            
            # Calculate commission based on tier price
            tier_prices = {'FANG': 89, 'NIBBLER': 39, 'COMMANDER': 139, 'APEX': 188}
            payment_amount = tier_prices.get('FANG', 89)  # Default to FANG
            commission_amount = payment_amount * commission_rate
            
            cursor.execute('''
                INSERT INTO commissions 
                (code, influencer_name, commission_rate, payment_amount, commission_amount, payment_date, stripe_session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                code.upper(),
                metadata.get('influencer_name', 'Unknown'),
                commission_rate,
                payment_amount,
                commission_amount,
                datetime.now().isoformat(),
                stripe_session_id
            ))
        
        conn.commit()
        conn.close()
        
        return {
            'valid': True,
            'used': True,
            'code_type': validation['code_type'],
            'discount_info': validation
        }
    
    def get_code_stats(self) -> Dict:
        """Get statistics about ally codes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total codes by type
        cursor.execute('''
            SELECT code_type, COUNT(*), SUM(CASE WHEN uses_remaining > 0 THEN 1 ELSE 0 END)
            FROM ally_codes 
            GROUP BY code_type
        ''')
        code_stats = cursor.fetchall()
        
        # Usage statistics
        cursor.execute('''
            SELECT COUNT(*), COUNT(DISTINCT code)
            FROM code_usage
        ''')
        usage_stats = cursor.fetchone()
        
        # Commission stats
        cursor.execute('''
            SELECT SUM(commission_amount), COUNT(*)
            FROM commissions
            WHERE paid = 0
        ''')
        commission_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'code_types': [{'type': row[0], 'total': row[1], 'available': row[2]} for row in code_stats],
            'total_uses': usage_stats[0],
            'unique_codes_used': usage_stats[1],
            'pending_commissions': commission_stats[0] or 0,
            'pending_commission_count': commission_stats[1] or 0
        }

# Helper functions for integration
def apply_ally_code_discount(tier: str, price_cents: int, ally_code_data: Dict) -> Dict:
    """Apply ally code discount to pricing"""
    discount_type = ally_code_data['discount_type']
    discount_value = ally_code_data['discount_value']
    
    if discount_type == 'LIFETIME_TIER':
        # Founder codes - $89 lifetime discount on any tier
        discount_amount = int(discount_value * 100)  # $89.00 = 8900 cents
        final_price = max(0, price_cents - discount_amount)  # Can't go below $0
        
        return {
            'type': 'lifetime_discount',
            'tier': tier,  # Keep selected tier
            'original_price': price_cents,
            'discount_amount': discount_amount,
            'final_price': final_price,
            'description': f'FOUNDER LEGACY - ${discount_value:.0f} lifetime discount'
        }
    
    elif discount_type == 'FIRST_MONTH_PERCENT':
        # Influencer codes - percentage off first month
        discount_amount = int(price_cents * (discount_value / 100))
        return {
            'type': 'first_month_discount',
            'tier': tier,
            'original_price': price_cents,
            'discount_amount': discount_amount,
            'final_price': price_cents - discount_amount,
            'description': f'{discount_value}% off first month'
        }
    
    return {
        'type': 'none',
        'tier': tier,
        'original_price': price_cents,
        'final_price': price_cents,
        'description': 'No discount applied'
    }

if __name__ == "__main__":
    # Initialize and create founder codes
    manager = AllyCodeManager()
    codes = manager.create_founder_codes()
    print(f"Created {len(codes)} founder codes: {codes}")
    
    # Create example influencer codes
    joey_code = manager.create_influencer_code("Joey", commission_rate=0.3, discount_percent=50)
    print(f"Created influencer code: {joey_code}")
    
    # Show stats
    stats = manager.get_code_stats()
    print(f"Code statistics: {stats}")