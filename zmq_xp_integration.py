#!/usr/bin/env python3
"""
ZMQ XP Integration Module
Connects telemetry data to XP awards and user progression
"""

import json
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger('ZMQXPIntegration')

class ZMQXPIntegration:
    """
    Integrates ZMQ telemetry with XP system for real-time awards
    """
    
    def __init__(self):
        self.xp_awards = {
            'trade_success': 5,
            'first_trade': 10,
            'profit_milestone_5': 10,
            'profit_milestone_10': 20,
            'profit_milestone_25': 50,
            'winning_streak_3': 15,
            'winning_streak_5': 25,
            'daily_active': 5,
            'margin_recovery': 10,
            'perfect_day': 30
        }
        
        self.user_stats = {}  # Track user performance for milestones
        
    def process_telemetry_for_xp(self, telemetry: Dict) -> Optional[Dict]:
        """
        Process telemetry data and determine XP awards
        
        Returns:
            Dict with xp_amount and reason if award earned, None otherwise
        """
        uuid = telemetry.get('uuid', '')
        
        # Initialize user stats if new
        if uuid not in self.user_stats:
            self.user_stats[uuid] = {
                'first_trade': False,
                'total_trades': 0,
                'winning_streak': 0,
                'daily_trades': 0,
                'last_trade_date': None,
                'starting_balance': telemetry.get('balance', 0),
                'highest_equity': telemetry.get('equity', 0),
                'profit_milestones': set()
            }
        
        stats = self.user_stats[uuid]
        
        # Update highest equity
        current_equity = telemetry.get('equity', 0)
        if current_equity > stats['highest_equity']:
            stats['highest_equity'] = current_equity
        
        # Check profit milestones
        if stats['starting_balance'] > 0:
            profit_pct = ((current_equity - stats['starting_balance']) / stats['starting_balance']) * 100
            
            # Check 5% milestone
            if profit_pct >= 5 and 5 not in stats['profit_milestones']:
                stats['profit_milestones'].add(5)
                return {
                    'xp_amount': self.xp_awards['profit_milestone_5'],
                    'reason': 'Reached 5% profit milestone',
                    'user_id': uuid
                }
            
            # Check 10% milestone
            if profit_pct >= 10 and 10 not in stats['profit_milestones']:
                stats['profit_milestones'].add(10)
                return {
                    'xp_amount': self.xp_awards['profit_milestone_10'],
                    'reason': 'Reached 10% profit milestone',
                    'user_id': uuid
                }
            
            # Check 25% milestone
            if profit_pct >= 25 and 25 not in stats['profit_milestones']:
                stats['profit_milestones'].add(25)
                return {
                    'xp_amount': self.xp_awards['profit_milestone_25'],
                    'reason': 'Reached 25% profit milestone',
                    'user_id': uuid
                }
        
        return None
        
    def process_trade_result_for_xp(self, result: Dict) -> Optional[Dict]:
        """
        Process trade result and determine XP awards
        """
        signal_id = result.get('signal_id', '')
        status = result.get('status', '')
        
        # Extract user_id from signal_id (format: VENOM_EURUSD_123_user_456 or VENOM_EURUSD_001_user_test_user_001)
        parts = signal_id.split('_')
        # Find the part after 'user'
        user_id = 'unknown'
        for i, part in enumerate(parts):
            if part == 'user' and i < len(parts) - 1:
                # Join remaining parts as user_id
                user_id = '_'.join(parts[i+1:])
                break
        
        if user_id == 'unknown':
            return None
        
        # Initialize user stats if needed
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'first_trade': False,
                'total_trades': 0,
                'winning_streak': 0,
                'daily_trades': 0,
                'last_trade_date': None,
                'starting_balance': 0,
                'highest_equity': 0,
                'profit_milestones': set()
            }
        
        stats = self.user_stats[user_id]
        
        # Track trade count
        stats['total_trades'] += 1
        
        # First trade bonus
        if not stats['first_trade']:
            stats['first_trade'] = True
            return {
                'xp_amount': self.xp_awards['first_trade'],
                'reason': 'First trade executed',
                'user_id': user_id
            }
        
        # Track winning streaks
        if status == 'success':
            stats['winning_streak'] += 1
            
            # 3-trade winning streak
            if stats['winning_streak'] == 3:
                return {
                    'xp_amount': self.xp_awards['winning_streak_3'],
                    'reason': '3-trade winning streak',
                    'user_id': user_id
                }
            
            # 5-trade winning streak
            if stats['winning_streak'] == 5:
                return {
                    'xp_amount': self.xp_awards['winning_streak_5'],
                    'reason': '5-trade winning streak',
                    'user_id': user_id
                }
        else:
            stats['winning_streak'] = 0
        
        # Standard trade success XP
        if status == 'success':
            return {
                'xp_amount': self.xp_awards['trade_success'],
                'reason': 'Trade executed successfully',
                'user_id': user_id
            }
        
        return None
        
    def check_daily_activity(self, user_id: str) -> Optional[Dict]:
        """
        Check if user qualifies for daily activity bonus
        """
        if user_id in self.user_stats:
            stats = self.user_stats[user_id]
            today = datetime.now().date()
            
            if stats['last_trade_date'] != today:
                stats['last_trade_date'] = today
                stats['daily_trades'] = 1
                
                return {
                    'xp_amount': self.xp_awards['daily_active'],
                    'reason': 'Daily trading activity',
                    'user_id': user_id
                }
        
        return None
        
    def check_margin_recovery(self, user_id: str, old_margin_level: float, new_margin_level: float) -> Optional[Dict]:
        """
        Check if user recovered from low margin
        """
        if old_margin_level < 150 and new_margin_level > 200:
            return {
                'xp_amount': self.xp_awards['margin_recovery'],
                'reason': 'Recovered from low margin level',
                'user_id': user_id
            }
        
        return None

# Integration helper functions

def award_xp_from_telemetry(telemetry_service, xp_integration: ZMQXPIntegration):
    """
    Process telemetry updates for XP awards
    """
    def telemetry_callback(telemetry: Dict):
        # Check for telemetry-based XP
        xp_award = xp_integration.process_telemetry_for_xp(telemetry)
        if xp_award:
            logger.info(f"🎖️ XP Award: {xp_award['user_id']} - {xp_award['reason']} ({xp_award['xp_amount']} XP)")
            # Here you would call the actual XP system
            # award_xp(xp_award['user_id'], xp_award['xp_amount'], xp_award['reason'])
    
    telemetry_service.register_telemetry_callback(telemetry_callback)
    
def award_xp_from_trades(telemetry_service, xp_integration: ZMQXPIntegration):
    """
    Process trade results for XP awards
    """
    def trade_callback(result: Dict):
        # Check for trade-based XP
        xp_award = xp_integration.process_trade_result_for_xp(result)
        if xp_award:
            logger.info(f"🎖️ XP Award: {xp_award['user_id']} - {xp_award['reason']} ({xp_award['xp_amount']} XP)")
            # Here you would call the actual XP system
            # award_xp(xp_award['user_id'], xp_award['xp_amount'], xp_award['reason'])
    
    telemetry_service.set_trade_callback(trade_callback)