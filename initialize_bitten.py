#!/usr/bin/env python3
"""
BITTEN System Initializer
Properly configures all components with joinbitten.com
"""

import os
import sys
import asyncio
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import configurations
from config.telegram import TelegramConfig
from config.webapp import webapp_config

# Import core components
from src.bitten_core.telegram_router import TelegramRouter
from src.bitten_core.signal_alerts import SignalAlertSystem
from src.bitten_core.fire_router import FireRouter
from src.bitten_core.user_manager import UserManager
from src.bitten_core.bitten_core import BITTENCore

class BITTENInitializer:
    """Initialize BITTEN with proper configuration"""
    
    def __init__(self):
        self.telegram_config = TelegramConfig()
        self.webapp_config = webapp_config
        self.components = {}
        
    async def initialize_all_components(self) -> Dict[str, Any]:
        """Initialize all BITTEN components with proper configuration"""
        
        print("🚀 Initializing BITTEN System...")
        print(f"📱 Telegram Bot: {self.telegram_config.bot_token[:20]}...")
        print(f"🌐 WebApp URL: {self.webapp_config.HUD_URL}")
        print("=" * 50)
        
        # 1. Initialize User Manager
        print("📊 Initializing User Manager...")
        user_manager = UserManager()
        self.components['user_manager'] = user_manager
        
        # 2. Initialize Signal Alert System with joinbitten.com
        print("🚨 Initializing Signal Alert System...")
        signal_alerts = SignalAlertSystem(
            bot_token=self.telegram_config.bot_token,
            hud_webapp_url=self.webapp_config.HUD_URL  # Uses https://joinbitten.com/hud
        )
        self.components['signal_alerts'] = signal_alerts
        
        # 3. Initialize Fire Router
        print("🔥 Initializing Fire Router...")
        fire_router = FireRouter(
            signal_alert_system=signal_alerts,
            user_manager=user_manager
        )
        self.components['fire_router'] = fire_router
        
        # 4. Initialize Telegram Router with joinbitten.com
        print("💬 Initializing Telegram Router...")
        telegram_router = TelegramRouter(
            bot_token=self.telegram_config.bot_token,
            hud_webapp_url=self.webapp_config.HUD_URL,  # Uses https://joinbitten.com/hud
            user_manager=user_manager,
            fire_router=fire_router
        )
        self.components['telegram_router'] = telegram_router
        
        # 5. Initialize BITTEN Core
        print("🤖 Initializing BITTEN Core...")
        bitten_core = BITTENCore(
            telegram_bot_token=self.telegram_config.bot_token,
            webapp_base_url=self.webapp_config.PRODUCTION_BASE_URL  # https://joinbitten.com
        )
        self.components['bitten_core'] = bitten_core
        
        print("\n✅ All components initialized successfully!")
        print("\n📋 Component Summary:")
        print(f"- User Manager: Active")
        print(f"- Signal Alerts: Connected to {self.webapp_config.HUD_URL}")
        print(f"- Fire Router: Ready")
        print(f"- Telegram Router: Connected")
        print(f"- BITTEN Core: Online")
        
        return self.components
    
    def get_startup_config(self) -> Dict[str, str]:
        """Get configuration for starting BITTEN"""
        return {
            'bot_token': self.telegram_config.bot_token,
            'chat_id': str(self.telegram_config.chat_id),
            'webapp_hud_url': self.webapp_config.HUD_URL,
            'webapp_mission_url': self.webapp_config.MISSION_BRIEF_URL,
            'webapp_stats_url': self.webapp_config.STATS_DASHBOARD_URL,
            'environment': 'production'
        }
    
    async def test_configuration(self):
        """Test that all configurations are valid"""
        print("\n🔍 Testing Configuration...")
        
        # Test Telegram config
        if self.telegram_config.bot_token:
            print("✅ Telegram bot token configured")
        else:
            print("❌ Telegram bot token missing!")
            
        # Test WebApp config
        if self.webapp_config.validate_config():
            print("✅ WebApp URLs properly configured")
            print(f"   - HUD: {self.webapp_config.HUD_URL}")
            print(f"   - Mission: {self.webapp_config.MISSION_BRIEF_URL}")
            print(f"   - Stats: {self.webapp_config.STATS_DASHBOARD_URL}")
        else:
            print("❌ WebApp configuration invalid!")
            
        # Test data URL generation
        test_data = {'signal_id': 'test123', 'tier': 'FANG'}
        test_url = self.webapp_config.get_webapp_data_url('hud', test_data)
        print(f"\n📝 Test URL Generation:")
        print(f"   {test_url[:80]}...")
        
        print("\n✅ Configuration test complete!")

async def main():
    """Main initialization function"""
    initializer = BITTENInitializer()
    
    # Test configuration
    await initializer.test_configuration()
    
    # Initialize all components
    components = await initializer.initialize_all_components()
    
    # Get startup configuration
    config = initializer.get_startup_config()
    
    print("\n🎯 BITTEN System Ready!")
    print("\nTo start the bot, use:")
    print("python start_bitten.py")
    
    print("\nTo send a test signal:")
    print("python send_test_signal.py")
    
    return components, config

if __name__ == "__main__":
    asyncio.run(main())