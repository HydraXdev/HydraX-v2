#!/usr/bin/env python3
"""
Quick start script to run BITTEN live with TraderMade data
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import components
from bitten_core.market_analyzer import MarketAnalyzer
from bitten_core.tcs_engine import TCSEngine  
from bitten_core.signal_alerts import SignalAlerts
from bitten_core.complete_signal_flow_v2 import EnhancedSignalFlow
from bitten_core.tradermade_client import TraderMadeClient

async def test_tradermade():
    """Test TraderMade connection"""
    print("🔍 Testing TraderMade API...")
    
    client = TraderMadeClient(api_key=os.getenv('TRADERMADE_API_KEY'))
    
    # Test live rates
    rates = await client.get_live_rates(['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'])
    
    if rates:
        print("✅ TraderMade connected! Live rates:")
        for pair, data in rates.items():
            print(f"  {pair}: Bid={data['bid']:.5f}, Ask={data['ask']:.5f}")
    else:
        print("❌ TraderMade connection failed - will use simulated data")
    
    return client

async def main():
    """Start the live trading system"""
    print("🚀 Starting BITTEN Live Trading System")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 API Key: {os.getenv('TRADERMADE_API_KEY')[:10]}...")
    print(f"📱 Telegram Bot: {os.getenv('TELEGRAM_BOT_TOKEN')[:20]}...")
    print(f"💬 Chat ID: {os.getenv('TELEGRAM_CHAT_ID')}")
    print(f"🌐 WebApp: {os.getenv('WEBAPP_URL')}")
    print("=" * 50)
    
    # Test TraderMade connection
    tm_client = await test_tradermade()
    
    print("\n📊 Initializing components...")
    
    # Initialize components
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    webapp_url = os.getenv('WEBAPP_URL', 'https://joinbitten.com')
    
    # Create signal flow
    flow = EnhancedSignalFlow(
        bot_token=bot_token,
        chat_id=chat_id,
        webapp_url=webapp_url
    )
    
    print("✅ Components initialized")
    
    print("\n⚠️  IMPORTANT NOTES:")
    print("1. Signals will be sent to Telegram")
    print("2. WebApp buttons will point to joinbitten.com")
    print("3. MT5 execution is NOT connected (no farm yet)")
    print("4. This will analyze real market data")
    print("5. TCS scoring is active (70% minimum)")
    
    print("\n🎯 What will happen:")
    print("- Monitor EUR/USD, GBP/USD, USD/JPY, XAU/USD")
    print("- When conditions meet 70%+ TCS score")
    print("- Send 3-line alert to Telegram")
    print("- User clicks VIEW INTEL button")
    print("- Opens mission briefing (if deployed)")
    
    print("\n⏰ Starting in 5 seconds...")
    await asyncio.sleep(5)
    
    print("\n🔥 BITTEN IS LIVE! Monitoring markets...")
    print("Press Ctrl+C to stop\n")
    
    # Start monitoring
    try:
        await flow.start_monitoring()
        
        # Keep running
        while True:
            await asyncio.sleep(60)
            print(f"💓 Heartbeat - {datetime.now().strftime('%H:%M:%S')} - System running...")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping BITTEN...")
        print("✅ Shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check .env file has all required keys")
        print("2. Ensure internet connection is active")
        print("3. Verify Telegram bot token is valid")
        print("4. Check TraderMade API key is correct")