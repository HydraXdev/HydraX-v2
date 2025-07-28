#!/usr/bin/env python3
"""
MT5 REAL TICK DATA EXTRACTOR
ZERO FAKE DATA - ONLY REAL MT5 PRICES
"""

import subprocess
import json
import time
import logging
from datetime import datetime
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MT5RealTickExtractor:
    """Extract REAL tick data from MT5 container - NO SYNTHETIC DATA"""
    
    def __init__(self, container_name="bitten_engine_mt5"):
        self.container_name = container_name
        self.pairs = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
            "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
            "XAUUSD"
        ]
        self.last_prices = {}
        logger.info(f"🎯 MT5 REAL Tick Extractor initialized")
        logger.info(f"📦 Container: {container_name}")
        logger.info(f"⚡ ZERO FAKE DATA - REAL PRICES ONLY")
        
    def check_mt5_running(self) -> bool:
        """Verify MT5 is actually running in container"""
        try:
            result = subprocess.run(
                ["docker", "exec", self.container_name, "ps", "aux"],
                capture_output=True, text=True, check=True
            )
            if "terminal64.exe" in result.stdout:
                logger.info("✅ MT5 is running")
                return True
            else:
                logger.error("❌ MT5 NOT RUNNING - NO TICK DATA AVAILABLE")
                return False
        except Exception as e:
            logger.error(f"❌ Container check failed: {e}")
            return False
    
    def extract_tick_from_log(self, symbol: str) -> Optional[Dict]:
        """Extract real tick data from MT5 logs"""
        try:
            # Check MT5 log files for tick data
            log_path = f"/wine/drive_c/Program Files/MetaTrader 5/Logs/{datetime.now().strftime('%Y%m%d')}.log"
            
            result = subprocess.run(
                ["docker", "exec", self.container_name, "tail", "-100", log_path],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                return None
                
            # Parse for tick data (this is where we'd extract real prices)
            # For now, we need to enhance the EA to write tick data
            
            return None
            
        except Exception as e:
            logger.error(f"Log extraction failed: {e}")
            return None
    
    def create_tick_writer_ea(self):
        """Create an EA to write real tick data to file"""
        ea_code = '''//+------------------------------------------------------------------+
//|                                          TickDataWriter.mq5      |
//|                                   Real Tick Data Writer for VENOM |
//+------------------------------------------------------------------+
#property copyright "HydraX Real Data"
#property version   "1.00"

input int UpdateIntervalMs = 500; // Update interval in milliseconds

datetime lastUpdate = 0;
int fileHandle = INVALID_HANDLE;

//+------------------------------------------------------------------+
int OnInit()
{
   EventSetMillisecondTimer(UpdateIntervalMs);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   if(fileHandle != INVALID_HANDLE)
      FileClose(fileHandle);
}

//+------------------------------------------------------------------+
void OnTimer()
{
   // Open file for writing
   fileHandle = FileOpen("tick_data.json", FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(fileHandle == INVALID_HANDLE)
      return;
   
   // Write current tick data
   string data = "{";
   data += "\\"timestamp\\": \\"" + TimeToString(TimeCurrent()) + "\\",";
   data += "\\"ticks\\": {";
   
   string symbols[] = {"EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", 
                      "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "XAUUSD"};
   
   for(int i = 0; i < ArraySize(symbols); i++)
   {
      MqlTick tick;
      if(SymbolInfoTick(symbols[i], tick))
      {
         if(i > 0) data += ",";
         data += "\\"" + symbols[i] + "\\": {";
         data += "\\"bid\\": " + DoubleToString(tick.bid, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
         data += "\\"ask\\": " + DoubleToString(tick.ask, (int)SymbolInfoInteger(symbols[i], SYMBOL_DIGITS)) + ",";
         data += "\\"time\\": " + IntegerToString(tick.time);
         data += "}";
      }
   }
   
   data += "}}";
   
   FileWriteString(fileHandle, data);
   FileClose(fileHandle);
}
'''
        
        # Write EA to container
        try:
            # Save EA code
            ea_path = "/wine/drive_c/Program Files/MetaTrader 5/MQL5/Experts/TickDataWriter.mq5"
            cmd = f'echo \'{ea_code}\' > "{ea_path}"'
            subprocess.run(
                ["docker", "exec", self.container_name, "bash", "-c", cmd],
                check=True
            )
            logger.info("✅ Tick writer EA created")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create EA: {e}")
            return False
    
    def get_real_tick_data(self) -> Dict[str, Dict]:
        """Get REAL tick data from MT5 - NO FAKE DATA"""
        if not self.check_mt5_running():
            logger.error("❌ MT5 NOT RUNNING - CANNOT GET REAL DATA")
            return {}
        
        try:
            # Read tick data file written by EA
            tick_file = "/wine/drive_c/Program Files/MetaTrader 5/MQL5/Files/tick_data.json"
            result = subprocess.run(
                ["docker", "exec", self.container_name, "cat", tick_file],
                capture_output=True, text=True
            )
            
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                logger.info(f"✅ Real tick data extracted at {data.get('timestamp')}")
                return data.get('ticks', {})
            else:
                logger.warning("⚠️ No tick data available yet")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Tick extraction failed: {e}")
            return {}
    
    def run_tick_monitor(self):
        """Monitor real ticks continuously"""
        logger.info("🚀 Starting REAL tick monitor")
        
        # First, ensure tick writer EA is installed
        if not self.create_tick_writer_ea():
            logger.error("❌ Cannot start without tick writer EA")
            return
            
        logger.info("⏳ Waiting for EA to start writing ticks...")
        time.sleep(5)
        
        while True:
            try:
                ticks = self.get_real_tick_data()
                
                if ticks:
                    # Log real price changes
                    for symbol, tick_data in ticks.items():
                        if symbol in self.last_prices:
                            last_bid = self.last_prices[symbol].get('bid', 0)
                            current_bid = tick_data.get('bid', 0)
                            if last_bid != current_bid:
                                logger.info(f"📊 {symbol}: {last_bid} → {current_bid} (REAL)")
                        
                        self.last_prices[symbol] = tick_data
                else:
                    logger.warning("⚠️ No tick data - EA may not be attached")
                
                time.sleep(1)  # Check every second
                
            except KeyboardInterrupt:
                logger.info("🛑 Stopping tick monitor")
                break
            except Exception as e:
                logger.error(f"❌ Monitor error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🎯 MT5 REAL TICK EXTRACTOR - ZERO FAKE DATA")
    logger.info("=" * 60)
    
    extractor = MT5RealTickExtractor()
    extractor.run_tick_monitor()