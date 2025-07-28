#!/usr/bin/env python3
"""
🔧 MT5 REAL CONNECTION SYSTEM - ZERO FAKE DATA
CRITICAL: This system ONLY connects to REAL MT5 - NO SIMULATION ALLOWED
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class MT5Fallback:
    """
    🔧 MT5 REAL CONNECTION - ZERO SIMULATION POLICY
    
    This system MUST connect to real MetaTrader5 or FAIL
    NO FAKE DATA, NO SIMULATION, NO FALLBACK DATA
    """
    
    def __init__(self):
        self.logger = logging.getLogger("MT5_REAL")
        self.connected = False
        self.mt5_real = None
        
    def initialize(self) -> bool:
        """Initialize REAL MT5 connection"""
        try:
            import MetaTrader5 as mt5
            self.mt5_real = mt5
            
            if not self.mt5_real.initialize():
                raise Exception("CRITICAL: Real MT5 initialization failed")
                
            self.logger.info("✅ MT5 REAL connection initialized")
            return True
            
        except ImportError:
            raise Exception("CRITICAL: MetaTrader5 package required - NO FAKE DATA ALLOWED")
        except Exception as e:
            self.logger.error(f"❌ MT5 Real initialization failed: {e}")
            raise Exception(f"CRITICAL: Cannot initialize real MT5 - {e}")
    
    def login(self, account: int, password: str, server: str) -> bool:
        """Login to REAL MT5 account - NO FAKE CREDENTIALS"""
        try:
            if not self.mt5_real:
                raise Exception("MT5 not initialized")
                
            if not all([account, password, server]):
                raise Exception("Missing real login credentials")
                
            # ATTEMPT REAL LOGIN
            if not self.mt5_real.login(account, password, server):
                error = self.mt5_real.last_error()
                raise Exception(f"REAL MT5 login failed: {error}")
                
            # VERIFY REAL ACCOUNT DATA
            real_account = self.mt5_real.account_info()
            if not real_account:
                raise Exception("Failed to get real account info after login")
                
            self.connected = True
            self.logger.info(f"✅ REAL MT5 login successful: {account} on {server}")
            self.logger.info(f"✅ REAL balance: ${real_account.balance}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ REAL MT5 login failed: {e}")
            raise Exception(f"CRITICAL: Real MT5 login failed - {e}")
    
    def account_info(self) -> Optional[object]:
        """Get REAL account info - NO FAKE DATA"""
        if not self.connected or not self.mt5_real:
            raise Exception("Not connected to real MT5")
            
        real_account = self.mt5_real.account_info()
        if not real_account:
            raise Exception("Failed to get real account info")
            
        return real_account
    
    def symbol_info_tick(self, symbol: str) -> Optional[object]:
        """Get REAL symbol tick data - NO SIMULATION"""
        if not self.connected or not self.mt5_real:
            raise Exception("Not connected to real MT5")
            
        real_tick = self.mt5_real.symbol_info_tick(symbol)
        if not real_tick:
            raise Exception(f"Failed to get real tick data for {symbol}")
            
        return real_tick
    
    def symbol_info(self, symbol: str) -> Optional[object]:
        """Get REAL symbol info - NO FAKE DATA"""
        if not self.connected or not self.mt5_real:
            raise Exception("Not connected to real MT5")
            
        real_symbol = self.mt5_real.symbol_info(symbol)
        if not real_symbol:
            raise Exception(f"Failed to get real symbol info for {symbol}")
            
        return real_symbol
    
    def symbol_select(self, symbol: str, enable: bool) -> bool:
        """Select symbol on REAL MT5"""
        if not self.connected or not self.mt5_real:
            raise Exception("Not connected to real MT5")
            
        return self.mt5_real.symbol_select(symbol, enable)
    
    def order_check(self, request: Dict) -> Optional[object]:
        """Check order on REAL MT5 - NO FAKE VALIDATION"""
        if not self.connected or not self.mt5_real:
            raise Exception("Not connected to real MT5")
            
        return self.mt5_real.order_check(request)
    
    def order_send(self, request: Dict) -> Optional[object]:
        """Send REAL order to MT5 - NO SIMULATION"""
        if not self.connected or not self.mt5_real:
            raise Exception("Not connected to real MT5")
            
        return self.mt5_real.order_send(request)
    
    def positions_get(self) -> tuple:
        """Get REAL positions - NO FAKE POSITIONS"""
        if not self.connected or not self.mt5_real:
            raise Exception("Not connected to real MT5")
            
        return self.mt5_real.positions_get()
    
    def shutdown(self) -> None:
        """Shutdown REAL MT5 connection"""
        if self.mt5_real:
            self.mt5_real.shutdown()
            self.connected = False
            self.logger.info("✅ Real MT5 connection shutdown")
    
    # MT5 constant imports for order types
    @property
    def TRADE_ACTION_DEAL(self):
        return self.mt5_real.TRADE_ACTION_DEAL if self.mt5_real else None
        
    @property
    def ORDER_TYPE_BUY(self):
        return self.mt5_real.ORDER_TYPE_BUY if self.mt5_real else None
        
    @property
    def ORDER_TYPE_SELL(self):
        return self.mt5_real.ORDER_TYPE_SELL if self.mt5_real else None
        
    @property
    def ORDER_TIME_GTC(self):
        return self.mt5_real.ORDER_TIME_GTC if self.mt5_real else None
        
    @property
    def ORDER_FILLING_IOC(self):
        return self.mt5_real.ORDER_FILLING_IOC if self.mt5_real else None
        
    @property
    def TRADE_RETCODE_DONE(self):
        return self.mt5_real.TRADE_RETCODE_DONE if self.mt5_real else None

# Global instance - REAL MT5 ONLY
mt5_fallback = MT5Fallback()

# Export MetaTrader5 constants for compatibility
try:
    import MetaTrader5
    # Re-export all MT5 constants
    for attr in dir(MetaTrader5):
        if not attr.startswith('_'):
            globals()[attr] = getattr(MetaTrader5, attr)
except ImportError:
    logger.error("CRITICAL: MetaTrader5 package not available - CANNOT PROCEED WITHOUT REAL MT5")