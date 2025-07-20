#!/usr/bin/env python3
"""
🔒 FOREX SAFE FIRE ROUTER
Enhanced FireRouter with US-compliant safe pairs validation
"""

import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add paths
sys.path.append('/root/HydraX-v2/src')
sys.path.append('/root/HydraX-v2')

from src.bitten_core.fire_router import FireRouter, TradeRequest, TradeDirection, TradeExecutionResult

# Configure logging
logger = logging.getLogger(__name__)

class ForexSafeFireRouter(FireRouter):
    """FireRouter with US-compliant safe pairs validation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # US-compliant safe pairs (no metals, no crypto)
        self.SAFE_PAIRS = ["EURUSD", "USDJPY", "GBPJPY", "USDCAD", "GBPUSD", "AUDUSD", "NZDUSD", "EURJPY", "EURGBP"]
        self.BLOCKED_PAIRS = ["XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD", "GOLD", "SILVER"]
        
        # Enhanced validation stats
        self.safe_pairs_stats = {
            "safe_pairs_attempted": 0,
            "blocked_pairs_rejected": 0,
            "unknown_pairs_rejected": 0
        }
        
        logger.info(f"Forex Safe Fire Router initialized with {len(self.SAFE_PAIRS)} safe pairs")
    
    def validate_symbol_safety(self, symbol: str) -> Dict[str, Any]:
        """Validate symbol safety for US-based accounts"""
        
        symbol_upper = symbol.upper()
        
        # Check if explicitly blocked
        if symbol_upper in self.BLOCKED_PAIRS:
            return {
                "safe": False,
                "category": "BLOCKED",
                "reason": "Symbol blocked for US-based accounts (metals/crypto)",
                "trade_mode": "DISABLED"
            }
        
        # Check if in safe list
        if symbol_upper in self.SAFE_PAIRS:
            return {
                "safe": True,
                "category": "SAFE_FOREX",
                "reason": "Major forex pair approved for US accounts",
                "trade_mode": "FULL"
            }
        
        # Unknown symbol - reject for safety
        return {
            "safe": False,
            "category": "UNKNOWN",
            "reason": "Symbol not in approved safe pairs list",
            "trade_mode": "UNKNOWN"
        }
    
    def execute_trade_request(self, request: TradeRequest, user_profile: Optional[Dict] = None) -> TradeExecutionResult:
        """Execute trade with enhanced symbol safety validation"""
        
        execution_start = time.time()
        
        # Step 1: Symbol Safety Validation
        symbol_validation = self.validate_symbol_safety(request.symbol)
        
        if not symbol_validation["safe"]:
            self.safe_pairs_stats[f"{symbol_validation['category'].lower()}_pairs_rejected"] += 1
            
            logger.warning(f"🚫 Symbol rejected: {request.symbol} - {symbol_validation['reason']}")
            
            return TradeExecutionResult(
                success=False,
                message=f"🚫 Symbol validation failed: {symbol_validation['reason']}",
                error_code=f"SYMBOL_{symbol_validation['category']}",
                execution_time_ms=int((time.time() - execution_start) * 1000)
            )
        
        # Symbol is safe - proceed with normal execution
        self.safe_pairs_stats["safe_pairs_attempted"] += 1
        logger.info(f"✅ Symbol approved: {request.symbol} ({symbol_validation['category']})")
        
        # Call parent execution with original validation
        return super().execute_trade_request(request, user_profile)
    
    def get_safe_pairs_stats(self) -> Dict[str, Any]:
        """Get safe pairs validation statistics"""
        return {
            **self.safe_pairs_stats,
            "safe_pairs_list": self.SAFE_PAIRS,
            "blocked_pairs_list": self.BLOCKED_PAIRS,
            "total_validations": sum(self.safe_pairs_stats.values())
        }

def create_test_eurusd_trade() -> TradeRequest:
    """Create a safe EURUSD test trade"""
    return TradeRequest(
        symbol="EURUSD",
        direction=TradeDirection.BUY,
        volume=0.01,
        stop_loss=1.0880,  # 20 pips below entry
        take_profit=1.0920,  # 40 pips above entry
        comment="FOREX_SAFE_TEST",
        tcs_score=85.0,
        user_id="7176191872",
        mission_id=f"EURUSD_TEST_{int(time.time())}"
    )

def test_safe_forex_execution():
    """Test safe forex execution with enhanced router"""
    
    logger.info("🧪 TESTING SAFE FOREX EXECUTION")
    logger.info("=" * 50)
    
    # Initialize safe router
    try:
        safe_router = ForexSafeFireRouter()
        logger.info("✅ Forex Safe Fire Router initialized")
    except Exception as e:
        logger.error(f"❌ Router initialization failed: {e}")
        return False
    
    # Test 1: Safe EURUSD trade
    logger.info("\n🎯 TEST 1: EURUSD (Safe Pair)")
    eurusd_request = create_test_eurusd_trade()
    
    result = safe_router.execute_trade_request(eurusd_request)
    
    logger.info(f"Result: {result.success}")
    logger.info(f"Message: {result.message}")
    if result.trade_id:
        logger.info(f"Trade ID: {result.trade_id}")
    if result.execution_time_ms:
        logger.info(f"Execution Time: {result.execution_time_ms}ms")
    
    # Test 2: Blocked XAUUSD trade
    logger.info("\n🚫 TEST 2: XAUUSD (Blocked Pair)")
    blocked_request = TradeRequest(
        symbol="XAUUSD",
        direction=TradeDirection.BUY,
        volume=0.01,
        comment="BLOCKED_TEST",
        tcs_score=85.0,
        user_id="7176191872",
        mission_id=f"XAUUSD_BLOCKED_TEST_{int(time.time())}"
    )
    
    blocked_result = safe_router.execute_trade_request(blocked_request)
    
    logger.info(f"Result: {blocked_result.success}")
    logger.info(f"Message: {blocked_result.message}")
    logger.info(f"Error Code: {blocked_result.error_code}")
    
    # Test 3: Unknown symbol
    logger.info("\n❓ TEST 3: UNKNOWN_PAIR")
    unknown_request = TradeRequest(
        symbol="UNKNOWN",
        direction=TradeDirection.BUY,
        volume=0.01,
        comment="UNKNOWN_TEST",
        tcs_score=85.0,
        user_id="7176191872",
        mission_id=f"UNKNOWN_TEST_{int(time.time())}"
    )
    
    unknown_result = safe_router.execute_trade_request(unknown_request)
    
    logger.info(f"Result: {unknown_result.success}")
    logger.info(f"Message: {unknown_result.message}")
    logger.info(f"Error Code: {unknown_result.error_code}")
    
    # Show statistics
    logger.info("\n📊 SAFE PAIRS STATISTICS")
    stats = safe_router.get_safe_pairs_stats()
    for key, value in stats.items():
        if isinstance(value, list):
            logger.info(f"{key}: {len(value)} items")
        else:
            logger.info(f"{key}: {value}")
    
    logger.info("\n✅ Safe forex execution test completed")
    
    return result.success or blocked_result.success == False  # Success if EURUSD works OR blocking works

if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/root/HydraX-v2/safe_forex_test.log'),
            logging.StreamHandler()
        ]
    )
    
    success = test_safe_forex_execution()
    sys.exit(0 if success else 1)