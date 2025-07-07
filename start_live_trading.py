#!/usr/bin/env python3
"""
Start BITTEN Live Trading System
Connects all components for real-time signal detection and alerts
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all components
from src.bitten_core.tradermade_client import TraderMadeClient
from src.bitten_core.complete_signal_flow import CompleteBITTENFlow
from src.bitten_core.tcs_scoring import TCSCalculator
from src.bitten_core.strategies.market_analyzer import MarketAnalyzer
from telegram import Bot

load_dotenv()

class BITTENLiveSystem:
    """Complete live trading system"""
    
    def __init__(self):
        # Configuration
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '7854827710:AAHnUNfP5GyxoYePoAV5BeOtDbmEJo6i_EQ')
        self.chat_id = int(os.getenv('MAIN_CHAT_ID', '-1002581996861'))
        self.webapp_url = 'https://joinbitten.com'
        
        # Initialize components
        self.market_data = TraderMadeClient()
        self.signal_flow = CompleteBITTENFlow(
            bot_token=self.bot_token,
            webapp_base_url=self.webapp_url
        )
        self.tcs_calculator = TCSCalculator()
        self.analyzer = MarketAnalyzer()
        
        # Track last signal time to avoid spam
        self.last_signal_time = {}
        self.signal_cooldown = 300  # 5 minutes between signals per pair
        
    async def start(self):
        """Start the live system"""
        print("🚀 Starting BITTEN Live Trading System")
        print("=" * 50)
        print(f"📱 Telegram Bot: Connected")
        print(f"🌐 WebApp URL: {self.webapp_url}")
        print(f"📊 Market Data: Connecting...")
        
        # Connect to market data
        await self.market_data.connect()
        
        # Send startup notification
        await self.send_notification("🟢 BITTEN System Online\n\nLive signal detection active.")
        
        print("\n✅ System ready! Monitoring markets...")
        print("Press Ctrl+C to stop\n")
        
        # Start monitoring
        await self.monitor_markets()
    
    async def monitor_markets(self):
        """Main monitoring loop"""
        while True:
            try:
                # Get current market data
                rates = await self.market_data.get_live_rates()
                
                # Check each pair for signals
                for symbol, price_data in rates.items():
                    if price_data:
                        await self.check_for_signal(symbol, price_data)
                
                # Check every 5 seconds
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                print("\n⏹️ Stopping system...")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(10)
    
    async def check_for_signal(self, symbol: str, price_data: Dict):
        """Check if current market conditions trigger a signal"""
        
        # Check cooldown
        if symbol in self.last_signal_time:
            if (datetime.now().timestamp() - self.last_signal_time[symbol]) < self.signal_cooldown:
                return
        
        # Get OHLC data for analysis
        candles = await self.market_data.get_ohlc(symbol, '5m', 50)
        
        if not candles:
            return
        
        # Prepare market data for analysis
        market_data = {
            'symbol': symbol,
            'current_price': price_data['mid'],
            'bid': price_data['bid'],
            'ask': price_data['ask'],
            'candles': candles,
            'timeframe': '5m'
        }
        
        # Run through analyzer
        analysis = self.analyzer.analyze_opportunity(market_data)
        
        if not analysis or not analysis.get('signal'):
            return
        
        # Calculate TCS score
        tcs_score = self.calculate_signal_score(analysis, market_data)
        
        # Check if meets minimum threshold
        if tcs_score < 70:
            return
        
        # Signal detected!
        print(f"\n🎯 Signal Detected: {symbol} {analysis['direction']} @ {price_data['mid']} (TCS: {tcs_score}%)")
        
        # Create signal data
        signal_data = {
            'symbol': symbol,
            'direction': analysis['direction'],
            'entry_price': price_data['ask'] if analysis['direction'] == 'BUY' else price_data['bid'],
            'stop_loss': analysis['stop_loss'],
            'take_profit': analysis['take_profit'],
            'tcs_score': tcs_score,
            'strategy_type': analysis.get('strategy', 'momentum'),
            'expires_in': 600  # 10 minutes
        }
        
        # Process through signal flow
        await self.signal_flow._process_new_signal(signal_data)
        
        # Update cooldown
        self.last_signal_time[symbol] = datetime.now().timestamp()
    
    def calculate_signal_score(self, analysis: Dict, market_data: Dict) -> int:
        """Calculate TCS score for signal"""
        score = 50  # Base score
        
        # Strategy confidence
        if analysis.get('confidence', 0) > 0.8:
            score += 20
        elif analysis.get('confidence', 0) > 0.6:
            score += 10
        
        # Risk/Reward ratio
        rr_ratio = analysis.get('risk_reward_ratio', 1)
        if rr_ratio >= 2:
            score += 15
        elif rr_ratio >= 1.5:
            score += 10
        
        # Trend alignment
        if analysis.get('trend_aligned', False):
            score += 10
        
        # Support/Resistance
        if analysis.get('near_support', False) or analysis.get('near_resistance', False):
            score += 5
        
        return min(score, 95)  # Cap at 95%
    
    async def send_notification(self, message: str):
        """Send system notification to Telegram"""
        try:
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Error sending notification: {e}")
    
    async def shutdown(self):
        """Clean shutdown"""
        await self.send_notification("🔴 BITTEN System Offline\n\nSignal detection stopped.")
        await self.market_data.close()
        print("✅ System shutdown complete")

async def main():
    """Main entry point"""
    system = BITTENLiveSystem()
    
    try:
        await system.start()
    except KeyboardInterrupt:
        print("\n⏹️ Shutdown requested...")
    finally:
        await system.shutdown()

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════╗
    ║         BITTEN LIVE TRADING          ║
    ║    Bot-Integrated Tactical Trading   ║
    ║            Engine/Network            ║
    ╚══════════════════════════════════════╝
    """)
    
    asyncio.run(main())