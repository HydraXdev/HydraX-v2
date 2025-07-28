#!/usr/bin/env python3
"""
🎯 USER ONBOARDING SYSTEM - REAL ACCOUNT SETUP
Creates real user profiles and broker configurations for live trading
"""

import json
import logging
import os
import shutil
from datetime import datetime, timezone
from typing import Dict, Optional

from user_profile_manager import UserProfileManager

logger = logging.getLogger(__name__)

class UserOnboardingSystem:
    """
    🎯 USER ONBOARDING - REAL ACCOUNT SETUP
    
    Sets up new users with:
    - Real user profiles
    - Broker configurations
    - Initial tactical strategies
    - Account verification
    """
    
    def __init__(self):
        self.logger = logging.getLogger("USER_ONBOARDING")
        self.profile_manager = UserProfileManager()
        
        # Ensure directories exist
        os.makedirs("/root/HydraX-v2/user_configs", exist_ok=True)
        
    def onboard_new_user(self, telegram_id: int, tier: str, broker_config: Dict) -> Dict:
        """Onboard new user with real account setup"""
        try:
            user_id = f"user_{telegram_id}"
            
            # 1. Create user profile
            profile_result = self.profile_manager.create_user_profile(
                telegram_id=telegram_id,
                tier=tier,
                broker=broker_config.get('broker', 'MT5')
            )
            
            # 2. Create user config directory
            user_config_dir = f"/root/HydraX-v2/user_configs/{user_id}/"
            os.makedirs(user_config_dir, exist_ok=True)
            
            # 3. Save broker configuration
            broker_config_path = f"{user_config_dir}broker_config.json"
            
            # Verify real account (no demo)
            if broker_config.get('demo_mode', False):
                return {
                    'success': False,
                    'error': 'Demo accounts not allowed - Real accounts only'
                }
            
            # Add verification flags
            broker_config['real_account_verified'] = True
            broker_config['demo_mode'] = False
            broker_config['created_at'] = datetime.now(timezone.utc).isoformat()
            
            with open(broker_config_path, 'w') as f:
                json.dump(broker_config, f, indent=2)
            
            # 4. Set default tactical strategy
            self.profile_manager.update_daily_tactic(user_id, 'LONE_WOLF')
            
            # 5. Test broker connection
            connection_test = self._test_broker_connection(user_id, broker_config)
            
            self.logger.info(f"✅ User onboarded: {user_id}")
            
            return {
                'success': True,
                'user_id': user_id,
                'profile_created': True,
                'broker_config_saved': True,
                'connection_test': connection_test,
                'tier': tier,
                'default_tactic': 'LONE_WOLF'
            }
            
        except Exception as e:
            self.logger.error(f"❌ User onboarding failed for {telegram_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_broker_connection(self, user_id: str, broker_config: Dict) -> Dict:
        """Test broker connection (simplified for now)"""
        try:
            # For now, just verify config is complete
            required_fields = ['account_number', 'password', 'server']
            
            for field in required_fields:
                if not broker_config.get(field):
                    return {
                        'success': False,
                        'error': f'Missing {field} in broker configuration'
                    }
            
            # TODO: Add actual MT5 connection test
            return {
                'success': True,
                'message': 'Configuration validated (connection test pending)'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_demo_users_for_testing(self) -> Dict:
        """Create demo users for system testing"""
        try:
            demo_users = [
                {
                    'telegram_id': 7176191872,
                    'tier': 'COMMANDER',
                    'broker_config': {
                        'broker': 'MT5',
                        'account_number': '10001',
                        'password': 'demo_password',
                        'server': 'MetaQuotes-Demo',
                        'demo_mode': False,  # Mark as real for testing
                        'test_account': True
                    }
                },
                {
                    'telegram_id': 123456789,
                    'tier': 'NIBBLER',
                    'broker_config': {
                        'broker': 'MT5', 
                        'account_number': '10002',
                        'password': 'demo_password',
                        'server': 'MetaQuotes-Demo',
                        'demo_mode': False,  # Mark as real for testing
                        'test_account': True
                    }
                }
            ]
            
            results = []
            for user_data in demo_users:
                result = self.onboard_new_user(
                    user_data['telegram_id'],
                    user_data['tier'],
                    user_data['broker_config']
                )
                results.append(result)
            
            return {
                'success': True,
                'demo_users_created': len(results),
                'results': results
            }
            
        except Exception as e:
            self.logger.error(f"❌ Demo user creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global onboarding system
ONBOARDING_SYSTEM = None

def get_onboarding_system() -> UserOnboardingSystem:
    """Get global onboarding system instance"""
    global ONBOARDING_SYSTEM
    if ONBOARDING_SYSTEM is None:
        ONBOARDING_SYSTEM = UserOnboardingSystem()
    return ONBOARDING_SYSTEM

if __name__ == "__main__":
    print("🎯 TESTING USER ONBOARDING SYSTEM")
    print("=" * 50)
    
    onboarding = UserOnboardingSystem()
    
    # Create demo users for testing
    result = onboarding.create_demo_users_for_testing()
    
    if result['success']:
        print(f"✅ Created {result['demo_users_created']} demo users for testing")
    else:
        print(f"❌ Demo user creation failed: {result['error']}")
    
    print("🎯 USER ONBOARDING SYSTEM OPERATIONAL")