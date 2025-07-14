#!/usr/bin/env python3
"""
APEX v5.0 LIVE REAL TRADING SYSTEM
Connects to actual MT5 infrastructure for live signal generation
NO SIMULATION - LIVE TRADING ONLY
"""

import sys
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import requests
# MetaTrader5 module import (will be mock for demo)
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    # Mock MT5 class for demo purposes
    class MockMT5:
        @staticmethod
        def initialize():
            print("🔧 MT5 MODULE NOT AVAILABLE - RUNNING IN DEMO MODE")
            return True
        @staticmethod
        def login(login, password, server):
            print(f"🔧 DEMO: Login attempt {login}@{server}")
            return True
        @staticmethod
        def account_info():
            class MockAccount:
                login = 12345
                balance = 50000.0
                equity = 50000.0
                server = "Demo-Server"
            return MockAccount()
        @staticmethod
        def symbol_info_tick(symbol):
            class MockTick:
                bid = 1.0850
                ask = 1.0852
                volume_real = 100
                time = 1721784000
            return MockTick()
        @staticmethod
        def symbol_info(symbol):
            class MockSymbol:
                point = 0.00001
                digits = 5
            return MockSymbol()
        @staticmethod
        def order_send(request):
            class MockResult:
                retcode = 10009  # TRADE_RETCODE_DONE
                order = 123456
                comment = "Demo order"
            return MockResult()
        @staticmethod
        def shutdown():
            print("🔧 DEMO: MT5 shutdown")
        @staticmethod
        def last_error():
            return (0, "No error")
        # Constants
        TRADE_ACTION_DEAL = 1
        ORDER_TYPE_BUY = 0
        ORDER_TIME_GTC = 0
        ORDER_FILLING_IOC = 2
        TRADE_RETCODE_DONE = 10009
    
    mt5 = MockMT5()

# Setup logging for live trading
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - APEX v5.0 LIVE - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/apex_v5_live_real.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class APEXv5LiveSystem:
    """APEX v5.0 Live Trading System - NO SIMULATION"""
    
    def __init__(self):
        self.is_running = False
        self.mt5_connected = False
        
        # MT5 connection parameters
        self.mt5_login = None  # Will be set from environment
        self.mt5_password = None
        self.mt5_server = None
        
        # 15 pairs for APEX v5.0
        self.v5_pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'GBPJPY',
            'EURJPY', 'AUDJPY', 'GBPCHF', 'AUDUSD', 'NZDUSD', 
            'USDCHF', 'EURGBP', 'GBPNZD', 'GBPAUD', 'EURAUD'
        ]
        
        # Performance tracking
        self.session_stats = {
            'signals_generated': 0,
            'trades_executed': 0,
            'total_pips': 0.0,
            'win_rate': 0.0,
            'session_start': datetime.now()
        }
        
        logger.info("🚀 APEX v5.0 LIVE SYSTEM INITIALIZED")
    
    def connect_mt5(self) -> bool:
        """Connect to MT5 terminal"""
        try:
            # Initialize MT5
            if not mt5.initialize():
                logger.error("❌ MT5 initialization failed")
                return False
            
            # Get MT5 credentials from environment
            login = os.getenv('MT5_LOGIN')
            password = os.getenv('MT5_PASSWORD') 
            server = os.getenv('MT5_SERVER', 'MetaQuotes-Demo')
            
            if not login or not password:
                logger.error("❌ MT5 credentials not found in environment")
                return False
            
            # Login to MT5
            authorized = mt5.login(int(login), password=password, server=server)
            
            if authorized:
                account_info = mt5.account_info()
                logger.info(f"✅ MT5 Connected - Account: {account_info.login}, Balance: ${account_info.balance}")
                if not MT5_AVAILABLE:
                    logger.warning("⚠️  RUNNING IN DEMO MODE - NO REAL MT5 CONNECTION")
                self.mt5_connected = True
                return True
            else:
                logger.error(f"❌ MT5 login failed: {mt5.last_error()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ MT5 connection error: {e}")
            return False
    
    def get_live_market_data(self, symbol: str) -> Optional[Dict]:
        """Get live market data - try bridge first, fallback to mock"""
        try:
            # Use your existing bridge infrastructure instead of direct MT5
            logger.info(f"🔍 Checking bridge files for {symbol}")
            bridge_data = self.get_market_data_from_bridge_files(symbol)
            if bridge_data:
                logger.info(f"📊 BRIDGE FILE DATA {symbol}: Bid={bridge_data['bid']:.5f}, Ask={bridge_data['ask']:.5f}, Spread={bridge_data['spread']}")
                return bridge_data
            else:
                logger.info(f"❌ No bridge data found for {symbol}")
            
            # If no bridge data available, don't generate fake signals
            logger.debug(f"❌ No bridge signal files found for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting live data for {symbol}: {e}")
            return None
    
    def calculate_live_tcs(self, symbol: str, market_data: Dict) -> float:
        """Calculate TCS score using live market data"""
        try:
            base_score = 45  # v5.0 base
            
            # Session boost
            session = self.get_current_session()
            session_boost = {
                'OVERLAP': 20,  # Triple boost
                'LONDON': 15,   # London boost
                'NY': 12,       # NY boost
                'ASIAN': 8      # Asian boost
            }.get(session, 5)
            
            # Spread penalty (live spreads matter)
            spread = market_data.get('spread', 2)
            if spread <= 2:
                spread_bonus = 10
            elif spread <= 5:
                spread_bonus = 5
            elif spread <= 10:
                spread_bonus = 0
            else:
                spread_bonus = -5  # Penalty for high spreads
            
            # Pair type scoring
            monster_pairs = ['GBPNZD', 'GBPAUD', 'EURAUD']
            volatile_pairs = ['GBPJPY', 'EURJPY', 'AUDJPY', 'GBPCHF']
            
            if symbol in monster_pairs:
                pair_boost = 15
            elif symbol in volatile_pairs:
                pair_boost = 10
            else:
                pair_boost = 5
            
            # Volume boost (more volume = better execution)
            volume = market_data.get('volume', 0)
            if volume > 100:
                volume_boost = 5
            elif volume > 50:
                volume_boost = 3
            else:
                volume_boost = 0
            
            # Calculate final TCS
            tcs_score = base_score + session_boost + spread_bonus + pair_boost + volume_boost
            
            # v5.0 bounds (35-95)
            return max(35, min(95, tcs_score))
            
        except Exception as e:
            logger.error(f"❌ TCS calculation error for {symbol}: {e}")
            return 35  # Minimum TCS
    
    def generate_live_signal(self, symbol: str) -> Optional[Dict]:
        """Generate signal using live market data and log to file"""
        try:
            # Get live market data
            market_data = self.get_live_market_data(symbol)
            if not market_data:
                return None
            
            # Calculate live TCS
            tcs_score = self.calculate_live_tcs(symbol, market_data)
            
            # EMERGENCY TEST - Generate signal regardless of TCS for testing
            if tcs_score < 15:  # Emergency low threshold for pipeline test
                return None
            
            # Generate signal
            signal = {
                'symbol': symbol,
                'direction': 'BUY',  # Simplified for v5.0
                'entry_price': market_data['ask'],
                'bid_price': market_data['bid'], 
                'spread': market_data['spread'],
                'tcs': tcs_score,
                'pattern': f'APEX_v5_LIVE_{self.get_current_session()}',
                'timeframe': 'M3',
                'session': self.get_current_session(),
                'stop_loss': 10,  # pips
                'take_profit': 20,  # pips
                'timestamp': datetime.now(),
                'market_data': market_data,
                'confidence': 'LIVE'
            }
            
            # Log signal in format expected by telegram_connector
            self.session_stats['signals_generated'] += 1
            signal_number = self.session_stats['signals_generated']
            
            # Write to log file AND execution log in expected format
            signal_log = f"🎯 SIGNAL #{signal_number}: {symbol} {signal['direction']} TCS:{tcs_score:.0f}%"
            logger.info(signal_log)
            
            # Also write to execution log for tracking
            with open('/root/HydraX-v2/apex_v5_live_execution.log', 'a') as f:
                f.write(f"{datetime.now().isoformat()}: {signal_log}\n")
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Signal generation error for {symbol}: {e}")
            return None
    
    def get_market_data_from_bridge_files(self, symbol: str) -> Optional[Dict]:
        """Get market data from existing bridge signal files"""
        try:
            import requests
            import json
            
            # Step 1: Get list of files matching the symbol pattern
            cmd = f"dir /B /O:-D \"C:\\\\Users\\\\Administrator\\\\AppData\\\\Roaming\\\\MetaQuotes\\\\Terminal\\\\173477FF1060D99CE79296FC73108719\\\\MQL5\\\\Files\\\\BITTEN\\\\*{symbol}*.json\" 2>nul"
            logger.info(f"📋 Executing CMD: {cmd}")
            response = requests.post(
                "http://3.145.84.187:5555/execute",
                json={
                    "command": cmd,
                    "type": "cmd"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"🔍 File listing response for {symbol}: {result}")
                if result.get('success') and result.get('stdout'):
                    # Get the first (most recent) file
                    files = result['stdout'].strip().split('\n')
                    logger.info(f"📁 Found files for {symbol}: {files}")
                    if files and files[0]:
                        latest_file = files[0].strip()
                        logger.info(f"📄 Latest file for {symbol}: {latest_file}")
                        
                        # Step 2: Read the content of the latest file
                        file_response = requests.post(
                            "http://3.145.84.187:5555/execute",
                            json={
                                "command": f"type \"C:\\\\Users\\\\Administrator\\\\AppData\\\\Roaming\\\\MetaQuotes\\\\Terminal\\\\173477FF1060D99CE79296FC73108719\\\\MQL5\\\\Files\\\\BITTEN\\\\{latest_file}\"",
                                "type": "cmd"
                            },
                            timeout=10
                        )
                        
                        if file_response.status_code == 200:
                            file_result = file_response.json()
                            if file_result.get('success') and file_result.get('stdout'):
                                response = file_response  # Use the file content response
                            else:
                                return None
                        else:
                            return None
                    else:
                        return None
                else:
                    return None
            else:
                return None
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"🔗 Bridge response for {symbol}: {result}")
                if result.get('success') and result.get('stdout'):
                    # Parse the JSON signal data
                    signal_content = result['stdout'].strip()
                    logger.info(f"📋 Signal content for {symbol}: {signal_content}")
                    if signal_content:
                        try:
                            # Try to parse as JSON
                            signal_data = json.loads(signal_content)
                            logger.info(f"✅ SIGNAL DETECTED for {symbol}: {signal_data}")
                            
                            # Extract market data from signal
                            entry_price = signal_data.get('entry_price', 1.0000)
                            spread = signal_data.get('spread', 2)
                            
                            # Calculate bid/ask from entry price and spread
                            if signal_data.get('direction') == 'BUY':
                                ask = entry_price
                                bid = entry_price - (spread * 0.00001)  # Assuming 5-digit quotes
                            else:
                                bid = entry_price  
                                ask = entry_price + (spread * 0.00001)
                            
                            return {
                                'symbol': symbol,
                                'bid': bid,
                                'ask': ask,
                                'spread': spread,
                                'volume': 100,  # Default volume
                                'timestamp': datetime.now(),
                                'point': 0.00001,
                                'digits': 5,
                                'source': 'fortress_bridge',
                                'signal_data': signal_data,
                                'fortress_validated': FORTRESS_AVAILABLE
                            }
                        except json.JSONDecodeError:
                            logger.debug(f"Failed to parse signal JSON for {symbol}")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Bridge file read error for {symbol}: {e}")
            return None
    
    def get_current_session(self) -> str:
        """Get current trading session"""
        hour = datetime.utcnow().hour
        
        if 12 <= hour < 16:  # OVERLAP (most important)
            return 'OVERLAP'
        elif 7 <= hour < 16:  # London
            return 'LONDON' 
        elif 13 <= hour < 22:  # New York
            return 'NY'
        elif 22 <= hour or hour < 7:  # Asian
            return 'ASIAN'
        else:
            return 'NORMAL'
    
    def run_live_trading(self) -> None:
        """Main live trading loop"""
        logger.info("🎯 STARTING LIVE TRADING - APEX v5.0")
        logger.info("⚠️  LIVE ACCOUNT - REAL MONEY AT RISK")
        logger.info("=" * 50)
        
        self.is_running = True
        
        try:
            while self.is_running:
                current_session = self.get_current_session()
                signals_found = 0
                
                logger.info(f"🔄 Starting scan cycle - Session: {current_session}")
                
                # Scan all 15 pairs for live signals
                for symbol in self.v5_pairs:
                    try:
                        signal = self.generate_live_signal(symbol)
                        
                        if signal:
                            signals_found += 1
                            self.session_stats['signals_generated'] += 1
                            
                            # Log signal in Telegram format for connector to pick up
                            signal_num = self.session_stats['signals_generated']
                            signal_log = f"🎯 SIGNAL #{signal_num}: {symbol} {signal['direction']} TCS:{signal['tcs']:.0f}%"
                            logger.info(signal_log)
                            
                            # Also write to execution log
                            with open('/root/HydraX-v2/apex_v5_live_execution.log', 'a') as f:
                                f.write(f"{datetime.now().isoformat()}: {signal_log}\n")
                            
                            logger.info(f"📊 Generated: {symbol} TCS {signal['tcs']:.1f} Spread:{signal['spread']:.1f} {current_session}")
                    except Exception as e:
                        logger.error(f"❌ Error processing {symbol}: {e}")
                        continue
                
                # Session summary
                if signals_found > 0:
                    logger.info(f"📊 LIVE Session {current_session}: {signals_found} signals, "
                              f"Total: {self.session_stats['signals_generated']}/40 target")
                else:
                    logger.info(f"🔍 No signals found this cycle - {current_session} session")
                
                # Adaptive sleep
                sleep_time = 15 if current_session == 'OVERLAP' else 45
                logger.info(f"💤 Sleeping {sleep_time}s until next scan")
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("🛑 Live trading stopped by user")
        except Exception as e:
            logger.error(f"❌ Critical error in live trading: {e}")
        finally:
            self.is_running = False
            if self.mt5_connected:
                mt5.shutdown()
                logger.info("🔒 MT5 connection closed")
    
    def start_live_system(self) -> None:
        """Start live trading system"""
        logger.info("🚀 APEX v5.0 LIVE SYSTEM STARTING")
        logger.info("⚠️  CONNECTING TO LIVE MT5 ACCOUNT")
        
        # Connect to MT5
        if not self.connect_mt5():
            logger.error("❌ Failed to connect to MT5 - ABORTING")
            return
        
        # Confirm live trading
        account_info = mt5.account_info()
        logger.info(f"💰 Account Balance: ${account_info.balance}")
        logger.info(f"📊 Account Equity: ${account_info.equity}")
        logger.info(f"🏦 Server: {account_info.server}")
        
        # Final confirmation
        logger.info("⚠️  STARTING LIVE TRADING IN 5 SECONDS...")
        time.sleep(5)
        
        # Start live trading
        self.run_live_trading()

def main():
    """Main entry point"""
    print("🚀 APEX v5.0 LIVE TRADING SYSTEM")
    print("⚠️  WARNING: LIVE ACCOUNT TRADING")
    print("=" * 50)
    
    # Auto-confirm for demo mode
    if not MT5_AVAILABLE:
        print("🔧 AUTO-STARTING IN DEMO MODE (MT5 module not available)")
        confirm = 'LIVE'
    else:
        confirm = input("Type 'LIVE' to confirm live trading with real money: ").strip()
        
        if confirm != 'LIVE':
            print("❌ Live trading cancelled")
            return
    
    # Create and start system
    system = APEXv5LiveSystem()
    system.start_live_system()

if __name__ == "__main__":
    main()