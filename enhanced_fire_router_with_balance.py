#!/usr/bin/env python3
"""
ENHANCED FIRE ROUTER WITH BALANCE VALIDATION
Integrates pre-trade balance validation into FireRouter
Prevents dangerous trades at execution level
"""

import logging
from typing import Dict, Optional
from src.bitten_core.fire_router import FireRouter, TradeRequest, TradeExecutionResult, TradeDirection
from pre_trade_validation_system import pre_trade_safety_check, can_user_trade_safely
from real_time_balance_system import get_user_balance_safe

class EnhancedFireRouter(FireRouter):
    """
    Enhanced FireRouter with pre-trade balance validation
    - Validates balance before every trade
    - Blocks dangerous trades
    - Provides safety defaults
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("ENHANCED_FIRE_ROUTER")
        self.logger.info("🔥 ENHANCED FIRE ROUTER WITH BALANCE VALIDATION INITIALIZED")
    
    def execute_trade_request(self, request: TradeRequest, user_profile: Optional[Dict] = None) -> TradeExecutionResult:
        """Execute trade with pre-trade balance validation"""
        
        execution_start = self._get_execution_start_time()
        
        try:
            # STEP 1: PRE-TRADE BALANCE VALIDATION
            self.logger.info(f"🔍 Pre-trade validation for user {request.user_id}")
            
            # Get real-time balance validation
            validation_result = pre_trade_safety_check(request.user_id)
            
            if not validation_result["can_execute"]:
                # Block trade due to balance issues
                self.logger.warning(f"🚨 Trade BLOCKED for {request.user_id}: {validation_result['errors']}")
                
                return TradeExecutionResult(
                    success=False,
                    message=f"🚨 Trade blocked for account protection. Balance validation failed.",
                    error_code="BALANCE_VALIDATION_FAILED",
                    execution_time_ms=int((self._get_execution_start_time() - execution_start) * 1000)
                )
            
            # STEP 2: ENHANCE USER PROFILE WITH BALANCE INFO
            enhanced_profile = user_profile or {}
            enhanced_profile.update({
                "balance": validation_result["balance"],
                "is_live_balance": validation_result["is_live_balance"],
                "safety_info": validation_result["safety_info"],
                "balance_validated": True,
                "validation_timestamp": validation_result["timestamp"]
            })
            
            # Log validation success
            self.logger.info(f"✅ Balance validation passed: ${validation_result['balance']} ({'live' if validation_result['is_live_balance'] else 'default'})")
            
            # Add warnings to trade comment if any
            if validation_result["warnings"]:
                warning_text = "; ".join(validation_result["warnings"][:2])  # Max 2 warnings
                request.comment = f"{request.comment} [WARN: {warning_text}]"
            
            # STEP 3: EXECUTE TRADE WITH ORIGINAL LOGIC
            return super().execute_trade_request(request, enhanced_profile)
            
        except Exception as e:
            self.logger.error(f"❌ Enhanced trade execution failed: {e}")
            
            return TradeExecutionResult(
                success=False,
                message=f"❌ Enhanced execution error: {str(e)}",
                error_code="ENHANCED_EXECUTION_ERROR",
                execution_time_ms=int((self._get_execution_start_time() - execution_start) * 1000)
            )
    
    def _get_execution_start_time(self):
        """Get execution start time for timing calculations"""
        import time
        return time.time()
    
    def validate_trade_with_balance(self, request: TradeRequest) -> Dict:
        """Validate trade request with balance information"""
        
        validation_result = pre_trade_safety_check(request.user_id)
        
        return {
            "can_execute": validation_result["can_execute"],
            "balance": validation_result["balance"],
            "is_live_balance": validation_result["is_live_balance"],
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"],
            "safety_info": validation_result["safety_info"]
        }
    
    def get_user_trading_status(self, user_id: str) -> Dict:
        """Get comprehensive user trading status"""
        
        try:
            # Get balance info
            balance_info = get_user_balance_safe(user_id)
            
            # Get validation status
            validation_result = pre_trade_safety_check(user_id)
            
            # Get system status
            system_status = self.get_system_status()
            
            return {
                "user_id": user_id,
                "can_trade": validation_result["can_execute"],
                "balance": {
                    "amount": balance_info.balance,
                    "currency": balance_info.currency,
                    "is_live": balance_info.is_live,
                    "account_id": balance_info.account_id,
                    "server": balance_info.server,
                    "free_margin": balance_info.free_margin
                },
                "validation": {
                    "errors": validation_result["errors"],
                    "warnings": validation_result["warnings"],
                    "safety_tier": validation_result["safety_info"]["balance_tier"]["tier"]
                },
                "system": {
                    "bridge_health": system_status["bridge_health"]["success_rate"],
                    "execution_mode": system_status["execution_mode"],
                    "emergency_stop": system_status["emergency_stop"]
                },
                "timestamp": validation_result["timestamp"]
            }
            
        except Exception as e:
            self.logger.error(f"❌ Trading status error for {user_id}: {e}")
            return {
                "user_id": user_id,
                "can_trade": False,
                "error": str(e)
            }

# Create enhanced router instances
def create_enhanced_fire_router(**kwargs) -> EnhancedFireRouter:
    """Create enhanced fire router with balance validation"""
    return EnhancedFireRouter(**kwargs)

# Global enhanced router
_enhanced_router = None

def get_enhanced_fire_router() -> EnhancedFireRouter:
    """Get global enhanced fire router instance"""
    global _enhanced_router
    if _enhanced_router is None:
        _enhanced_router = create_enhanced_fire_router()
    return _enhanced_router

# Convenience functions
def execute_trade_with_balance_validation(request: TradeRequest, user_profile: Optional[Dict] = None) -> TradeExecutionResult:
    """Execute trade with balance validation"""
    router = get_enhanced_fire_router()
    return router.execute_trade_request(request, user_profile)

def get_user_trading_readiness(user_id: str) -> Dict:
    """Get user trading readiness status"""
    router = get_enhanced_fire_router()
    return router.get_user_trading_status(user_id)

if __name__ == "__main__":
    # Test the enhanced router
    print("🔥 TESTING ENHANCED FIRE ROUTER WITH BALANCE VALIDATION")
    print("=" * 60)
    
    # Test user trading status
    status = get_user_trading_readiness("843859")
    print(f"User: {status['user_id']}")
    print(f"Can Trade: {status['can_trade']}")
    print(f"Balance: ${status['balance']['amount']} ({status['balance']['currency']})")
    print(f"Live Balance: {status['balance']['is_live']}")
    print(f"Errors: {status['validation']['errors']}")
    print(f"Warnings: {status['validation']['warnings']}")
    print(f"Safety Tier: {status['validation']['safety_tier']}")
    
    # Test trade validation
    test_request = TradeRequest(
        symbol="EURUSD",
        direction=TradeDirection.BUY,
        volume=0.01,
        user_id="843859",
        mission_id="TEST_BALANCE_VALIDATION",
        tcs_score=85.0,
        comment="BALANCE_VALIDATION_TEST"
    )
    
    print("\\n🧪 Testing trade validation...")
    router = get_enhanced_fire_router()
    validation = router.validate_trade_with_balance(test_request)
    print(f"Validation Result: {validation}")