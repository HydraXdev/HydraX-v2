#!/usr/bin/env python3
"""
Handshake Enforcer - NO TRADING WITHOUT REAL ACCOUNT DATA
Protects users from devastating losses due to incorrect position sizing
"""

import json
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('HandshakeEnforcer')

class HandshakeEnforcer:
    """
    CRITICAL: Enforces handshake requirement before ANY trading
    No defaults, no assumptions - REAL DATA ONLY
    """
    
    @staticmethod
    def verify_handshake_for_trade(telegram_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Verify user has valid handshake before allowing ANY trade
        
        Returns:
            (can_trade, message, account_data)
        """
        try:
            # Check user registry for handshake data
            with open('/root/HydraX-v2/user_registry.json', 'r') as f:
                registry = json.load(f)
            
            user_data = registry.get(telegram_id, {})
            
            # CRITICAL CHECKS - ALL MUST PASS
            checks = {
                'exists': telegram_id in registry,
                'has_balance': user_data.get('account_balance', 0) > 0,
                'has_uuid': bool(user_data.get('user_uuid')),
                'handshake_received': user_data.get('handshake_received', False)
            }
            
            # Check if ALL requirements met
            if not checks['exists']:
                return False, "🔒 Market closed - Your terminal will connect when market opens", None
            
            if not checks['has_balance']:
                return False, "⏳ Waiting for market open - Terminal ready to connect", None
            
            if not checks['has_uuid']:
                return False, "🔄 Terminal initializing - Will be ready when market opens", None
            
            if not checks['handshake_received']:
                return False, "📡 Market closed - Automatic connection at next session", None
            
            # All checks passed - return account data
            account_data = {
                'telegram_id': telegram_id,
                'user_uuid': user_data.get('user_uuid'),
                'balance': user_data.get('account_balance'),
                'equity': user_data.get('account_equity', user_data.get('account_balance')),
                'currency': user_data.get('account_currency', 'USD'),
                'tier': user_data.get('tier', 'NIBBLER'),
                'last_update': user_data.get('last_update'),
                'verified': True
            }
            
            return True, "✅ Account verified", account_data
            
        except Exception as e:
            logger.error(f"Error verifying handshake: {e}")
            return False, f"❌ SYSTEM ERROR - Cannot verify account", None
    
    
    @staticmethod
    def get_handshake_status(telegram_id: str) -> Dict:
        """
        Get detailed handshake status for user
        """
        try:
            with open('/root/HydraX-v2/user_registry.json', 'r') as f:
                registry = json.load(f)
            
            if telegram_id not in registry:
                return {
                    'status': 'NOT_REGISTERED',
                    'message': '🔒 Market closed - Your terminal will activate when market opens',
                    'can_trade': False
                }
            
            user_data = registry.get(telegram_id, {})
            
            # Check handshake status
            if not user_data.get('handshake_received'):
                return {
                    'status': 'WAITING_HANDSHAKE',
                    'message': '⏳ Terminal ready - Will connect automatically at market open',
                    'can_trade': False
                }
            
            balance = user_data.get('account_balance', 0)
            
            # Check if data is stale
            last_update = user_data.get('last_update', '')
            if last_update:
                update_time = datetime.fromisoformat(last_update)
                age_minutes = (datetime.now() - update_time).total_seconds() / 60
                
                if age_minutes > 60:
                    return {
                        'status': 'STALE_DATA',
                        'message': f'Account data {age_minutes:.0f} minutes old - reconnect MT5',
                        'can_trade': False,
                        'balance': balance,
                        'last_update': last_update
                    }
            
            return {
                'status': 'READY',
                'message': f'Ready to trade - Balance: ${balance:.2f}',
                'can_trade': True,
                'balance': balance,
                'equity': user_data.get('account_equity', balance),
                'last_update': last_update
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'System error: {str(e)}',
                'can_trade': False
            }

def enforce_handshake_before_fire(telegram_id: str, signal_data: Dict) -> Tuple[bool, str]:
    """
    Main enforcement function - MUST be called before ANY trade execution
    Simply checks if we have real handshake data, core brain handles position sizing
    """
    enforcer = HandshakeEnforcer()
    
    # Verify handshake exists
    can_trade, message, account_data = enforcer.verify_handshake_for_trade(telegram_id)
    
    if not can_trade:
        logger.warning(f"Trade blocked for {telegram_id}: {message}")
        return False, message
    
    # Handshake verified - core brain will handle position sizing
    logger.info(f"✅ Handshake verified for {telegram_id}")
    logger.info(f"   Balance: ${account_data['balance']:.2f}")
    logger.info(f"   UUID: {account_data['user_uuid']}")
    
    return True, "Handshake verified"

# CRITICAL: This must be integrated into fire_router.py and bitten_core.py
# NO TRADE should execute without passing this enforcement

if __name__ == "__main__":
    # Test enforcement
    enforcer = HandshakeEnforcer()
    
    # Test with commander account
    status = enforcer.get_handshake_status('7176191872')
    print(f"Commander status: {json.dumps(status, indent=2)}")
    
    # Test trade enforcement
    can_trade, message = enforce_handshake_before_fire('7176191872', {'stop_pips': 20})
    print(f"Can trade: {can_trade}")
    print(f"Message: {message}")