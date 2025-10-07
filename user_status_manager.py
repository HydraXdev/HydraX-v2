#!/usr/bin/env python3
"""
User Status Manager - Comprehensive User Resource Tracking
Provides complete user status for mission briefs and admin queries
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from src.bitten_core.fire_mode_database import fire_mode_db

class UserStatusManager:
    """Manages comprehensive user status queries"""

    def __init__(self):
        self.fire_modes_db = "/root/HydraX-v2/data/fire_modes.db"
        self.bitten_db = "/root/HydraX-v2/bitten.db"

    def get_complete_user_status(self, user_id: str) -> Dict:
        """Get complete user status for mission brief display"""
        try:
            # Get basic user profile
            profile = self.get_user_profile(user_id)

            # Get tier-based limits and current usage
            tier_info = fire_mode_db.get_user_tier_summary(user_id)

            # Get trading capabilities
            trading_check = fire_mode_db.can_user_fire_trade(user_id, 'MANUAL')
            auto_check = fire_mode_db.can_user_fire_trade(user_id, 'AUTO')

            # Get active positions
            active_positions = self.get_active_positions(user_id)

            # Get today's trading activity
            daily_activity = self.get_daily_activity(user_id, tier_info['tier'])

            return {
                'user_id': user_id,
                'profile': profile,
                'tier': tier_info['tier'],
                'current_mode': tier_info.get('current_mode', 'SELECT'),

                # Resource availability
                'slots': {
                    'manual': {
                        'available': tier_info['available_slots']['manual'],
                        'used': tier_info['current_usage']['manual_slots_used'],
                        'max': tier_info['limits']['manual']
                    },
                    'auto': {
                        'available': tier_info['available_slots']['auto'],
                        'used': tier_info['current_usage']['auto_slots_used'],
                        'max': tier_info['limits']['auto']
                    },
                    'total': {
                        'available': tier_info['available_slots']['total'],
                        'used': tier_info['current_usage']['total_slots_used'],
                        'max': tier_info['limits']['total']
                    }
                },

                # Daily ammo/bullets
                'daily_trades': {
                    'available': daily_activity['remaining'],
                    'used': daily_activity['used'],
                    'max': daily_activity['max'],
                    'unlimited': daily_activity['unlimited'],
                    'resets_at': daily_activity['next_reset']
                },

                # Capabilities
                'capabilities': {
                    'can_manual_fire': trading_check['can_fire'],
                    'can_auto_fire': auto_check['can_fire'],
                    'auto_fire_enabled': tier_info.get('auto_fire_enabled', False),
                    'manual_fire_available': tier_info['tier'] in ['NIBBLER', 'FANG', 'COMMANDER'],
                    'auto_fire_available': tier_info['tier'] == 'COMMANDER'
                },

                # Current positions
                'active_positions': active_positions,
                'position_count': len(active_positions),

                # Status indicators for UI
                'status_indicators': {
                    'slots_color': self._get_slots_color(tier_info['available_slots']['total'], tier_info['limits']['total']),
                    'ammo_color': self._get_ammo_color(daily_activity['remaining'], daily_activity['max']),
                    'tier_badge': self._get_tier_badge(tier_info['tier']),
                    'mode_status': self._get_mode_status(tier_info.get('current_mode', 'SELECT'))
                }
            }

        except Exception as e:
            print(f"Error getting user status: {e}")
            return self._get_default_status(user_id)

    def get_user_profile(self, user_id: str) -> Dict:
        """Get user profile information"""
        try:
            conn = sqlite3.connect(self.fire_modes_db)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT gamer_tag, first_name, last_name, email, telegram_id,
                       subscription_tier, subscription_status, broker_name,
                       account_balance, account_currency, account_creation_date
                FROM user_fire_modes
                WHERE user_id = ?
            ''', (user_id,))

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'gamer_tag': result[0] or f"User_{user_id[:8]}",
                    'full_name': f"{result[1] or ''} {result[2] or ''}".strip() or "Unknown",
                    'email': result[3],
                    'telegram_id': result[4],
                    'tier': result[5] or 'NIBBLER',
                    'subscription_status': result[6] or 'ACTIVE',
                    'broker': result[7],
                    'balance': float(result[8]) if result[8] else 0.0,
                    'currency': result[9] or 'USD',
                    'member_since': result[10]
                }
            else:
                return {
                    'gamer_tag': f"User_{user_id[:8]}",
                    'full_name': "Unknown",
                    'tier': 'NIBBLER',
                    'subscription_status': 'ACTIVE',
                    'balance': 0.0,
                    'currency': 'USD'
                }

        except Exception as e:
            print(f"Error getting user profile: {e}")
            return {'gamer_tag': f"User_{user_id[:8]}", 'tier': 'NIBBLER'}

    def get_active_positions(self, user_id: str) -> List[Dict]:
        """Get user's active trading positions"""
        try:
            conn = sqlite3.connect(self.bitten_db)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT signal_id, symbol, side, entry_price, sl_init, tp_init, open_ts
                FROM positions_live
                WHERE user_id = ?
                ORDER BY open_ts DESC
            ''', (user_id,))

            positions = []
            for row in cursor.fetchall():
                positions.append({
                    'signal_id': row[0],
                    'symbol': row[1],
                    'direction': row[2],
                    'entry_price': float(row[3]),
                    'sl': float(row[4]),
                    'tp': float(row[5]),
                    'opened_at': datetime.fromtimestamp(row[6]).strftime('%H:%M:%S'),
                    'duration': self._format_duration(row[6])
                })

            conn.close()
            return positions

        except Exception as e:
            print(f"Error getting active positions: {e}")
            return []

    def get_daily_activity(self, user_id: str, tier: str) -> Dict:
        """Get today's trading activity and limits"""
        try:
            daily_check = fire_mode_db.check_daily_trade_limit(user_id, tier)

            remaining = daily_check['max_trades'] - daily_check['trades_used']
            if daily_check['unlimited']:
                remaining = 999999

            # Calculate next reset time (next Sunday 5PM EST)
            now = datetime.now(timezone.utc)
            days_until_sunday = (6 - now.weekday()) % 7
            if days_until_sunday == 0 and now.hour >= 22:  # It's Sunday after 22:00 UTC
                days_until_sunday = 7

            next_reset = now.replace(hour=22, minute=0, second=0, microsecond=0)
            if days_until_sunday > 0:
                from datetime import timedelta
                next_reset += timedelta(days=days_until_sunday)

            return {
                'used': daily_check['trades_used'],
                'max': daily_check['max_trades'],
                'remaining': max(0, remaining),
                'unlimited': daily_check['unlimited'],
                'next_reset': next_reset.strftime('%a %H:%M UTC')
            }

        except Exception as e:
            print(f"Error getting daily activity: {e}")
            return {'used': 0, 'max': 6, 'remaining': 6, 'unlimited': False, 'next_reset': 'Sun 22:00 UTC'}

    def search_users(self, search_term: str, search_type: str = 'all') -> List[Dict]:
        """Search users by various criteria for admin interface"""
        try:
            conn = sqlite3.connect(self.fire_modes_db)
            cursor = conn.cursor()

            search_term = f"%{search_term}%"

            if search_type == 'gamer_tag':
                query = "SELECT * FROM user_fire_modes WHERE gamer_tag LIKE ? ORDER BY gamer_tag"
                params = (search_term,)
            elif search_type == 'email':
                query = "SELECT * FROM user_fire_modes WHERE email LIKE ? ORDER BY email"
                params = (search_term,)
            elif search_type == 'telegram_id':
                query = "SELECT * FROM user_fire_modes WHERE telegram_id LIKE ? ORDER BY telegram_id"
                params = (search_term,)
            elif search_type == 'name':
                query = "SELECT * FROM user_fire_modes WHERE (first_name LIKE ? OR last_name LIKE ?) ORDER BY last_name, first_name"
                params = (search_term, search_term)
            else:  # 'all'
                query = '''
                    SELECT * FROM user_fire_modes
                    WHERE gamer_tag LIKE ? OR email LIKE ? OR telegram_id LIKE ?
                    OR first_name LIKE ? OR last_name LIKE ? OR user_id LIKE ?
                    ORDER BY gamer_tag
                '''
                params = (search_term, search_term, search_term, search_term, search_term, search_term)

            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()

            # Convert to list of dicts with complete status
            users = []
            for row in results:
                user_id = row[0]  # user_id is first column
                status = self.get_complete_user_status(user_id)
                users.append(status)

            return users

        except Exception as e:
            print(f"Error searching users: {e}")
            return []

    def get_tier_statistics(self) -> Dict:
        """Get overall tier statistics for admin dashboard"""
        try:
            conn = sqlite3.connect(self.fire_modes_db)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT
                    subscription_tier,
                    COUNT(*) as user_count,
                    SUM(CASE WHEN current_mode = 'AUTO' THEN 1 ELSE 0 END) as auto_users,
                    AVG(account_balance) as avg_balance
                FROM user_fire_modes
                WHERE subscription_tier IS NOT NULL
                GROUP BY subscription_tier
                ORDER BY
                    CASE subscription_tier
                        WHEN 'COMMANDER' THEN 3
                        WHEN 'FANG' THEN 2
                        WHEN 'NIBBLER' THEN 1
                        ELSE 0
                    END DESC
            ''')

            results = cursor.fetchall()
            conn.close()

            stats = {}
            total_users = 0
            for row in results:
                tier = row[0]
                count = row[1]
                auto_count = row[2]
                avg_balance = row[3] or 0

                stats[tier] = {
                    'user_count': count,
                    'auto_users': auto_count,
                    'manual_users': count - auto_count,
                    'avg_balance': round(avg_balance, 2)
                }
                total_users += count

            stats['total'] = total_users
            return stats

        except Exception as e:
            print(f"Error getting tier statistics: {e}")
            return {}

    def _get_slots_color(self, available: int, max_slots: int) -> str:
        """Get color indicator for slot availability"""
        if available == 0:
            return 'red'
        elif available <= max_slots * 0.3:
            return 'orange'
        else:
            return 'green'

    def _get_ammo_color(self, remaining: int, max_ammo: int) -> str:
        """Get color indicator for ammo/daily trades"""
        if max_ammo >= 999999:  # Unlimited
            return 'blue'
        elif remaining == 0:
            return 'red'
        elif remaining <= max_ammo * 0.3:
            return 'orange'
        else:
            return 'green'

    def _get_tier_badge(self, tier: str) -> Dict:
        """Get tier badge information"""
        badges = {
            'NIBBLER': {'color': 'gray', 'icon': '🦈', 'name': 'NIBBLER'},
            'FANG': {'color': 'silver', 'icon': '🐺', 'name': 'FANG'},
            'COMMANDER': {'color': 'gold', 'icon': '⭐', 'name': 'COMMANDER'}
        }
        return badges.get(tier, {'color': 'gray', 'icon': '❓', 'name': tier})

    def _get_mode_status(self, mode: str) -> Dict:
        """Get mode status indicator"""
        status = {
            'AUTO': {'color': 'blue', 'text': 'AUTO FIRE', 'icon': '🤖'},
            'MANUAL': {'color': 'green', 'text': 'MANUAL', 'icon': '🎯'},
            'SELECT': {'color': 'gray', 'text': 'SELECTION', 'icon': '🔍'}
        }
        return status.get(mode, {'color': 'gray', 'text': mode, 'icon': '❓'})

    def _format_duration(self, timestamp: int) -> str:
        """Format position duration"""
        try:
            now = datetime.now().timestamp()
            duration = int(now - timestamp)

            if duration < 60:
                return f"{duration}s"
            elif duration < 3600:
                return f"{duration // 60}m"
            else:
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                return f"{hours}h {minutes}m"
        except:
            return "0s"

    def _get_default_status(self, user_id: str) -> Dict:
        """Get default status when queries fail"""
        return {
            'user_id': user_id,
            'profile': {'gamer_tag': f"User_{user_id[:8]}", 'tier': 'NIBBLER'},
            'tier': 'NIBBLER',
            'current_mode': 'SELECT',
            'slots': {'manual': {'available': 1, 'used': 0, 'max': 1}},
            'daily_trades': {'available': 6, 'used': 0, 'max': 6},
            'capabilities': {'can_manual_fire': True, 'can_auto_fire': False},
            'active_positions': [],
            'position_count': 0,
            'error': 'Unable to load complete status'
        }

# Create singleton instance
user_status = UserStatusManager()