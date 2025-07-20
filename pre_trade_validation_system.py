#!/usr/bin/env python3
"""
PRE-TRADE VALIDATION SYSTEM
Validates account balance and safety BEFORE any trade creation
Prevents small account wipeouts with institutional-grade checks
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from real_time_balance_system import get_user_balance_safe, validate_user_can_trade

@dataclass
class PreTradeValidation:
    """Pre-trade validation result"""
    user_id: str
    can_execute: bool
    balance: float
    is_live_balance: bool
    validation_errors: List[str]
    validation_warnings: List[str]
    safety_info: Dict
    timestamp: datetime

class PreTradeValidationSystem:
    """
    Institutional-grade pre-trade validation
    - Gets real balance BEFORE mission creation
    - Blocks dangerous trades
    - Provides safety defaults
    """
    
    def __init__(self):
        self.logger = logging.getLogger("PRE_TRADE_VALIDATION")
        
        # Safety thresholds
        self.min_balance_for_trading = 10.0
        self.max_risk_per_trade_percent = 5.0  # 5% max risk per trade
        self.emergency_stop_balance = 5.0  # Stop trading below $5
        
        # Trade size limits based on balance
        self.balance_tier_limits = {
            (0, 50): {"max_risk_usd": 2.0, "warning": "Micro account - extra caution"},
            (50, 100): {"max_risk_usd": 5.0, "warning": "Small account - limited risk"},
            (100, 500): {"max_risk_usd": 15.0, "warning": "Standard account"},
            (500, 1000): {"max_risk_usd": 25.0, "warning": "Intermediate account"},
            (1000, float('inf')): {"max_risk_usd": 50.0, "warning": "Advanced account"}
        }
        
        self.logger.info("🛡️ PRE-TRADE VALIDATION SYSTEM INITIALIZED")
        self.logger.info(f"💰 Min balance: ${self.min_balance_for_trading}")
        self.logger.info(f"⚠️ Emergency stop: ${self.emergency_stop_balance}")
    
    def get_balance_tier_info(self, balance: float) -> Dict:
        """Get balance tier information and limits"""
        for (min_bal, max_bal), limits in self.balance_tier_limits.items():
            if min_bal <= balance < max_bal:
                return {
                    "tier": f"${min_bal}-${max_bal if max_bal != float('inf') else '∞'}",
                    "max_risk_usd": limits["max_risk_usd"],
                    "warning": limits["warning"]
                }
        
        return {
            "tier": "Unknown",
            "max_risk_usd": 2.0,
            "warning": "Micro account - extra caution"
        }
    
    def validate_account_safety(self, user_id: str) -> PreTradeValidation:
        """Comprehensive pre-trade account safety validation"""
        
        validation_errors = []
        validation_warnings = []
        
        # Get real-time balance
        balance_info = get_user_balance_safe(user_id, force_refresh=True)
        balance = balance_info.balance
        is_live = balance_info.is_live
        
        self.logger.info(f"🔍 Validating {user_id}: ${balance} ({'live' if is_live else 'default'})")
        
        # Critical validations (will block trade)
        if balance < self.emergency_stop_balance:
            validation_errors.append(f"Balance ${balance} below emergency stop threshold ${self.emergency_stop_balance}")
        
        if balance < self.min_balance_for_trading:
            validation_errors.append(f"Balance ${balance} below minimum trading threshold ${self.min_balance_for_trading}")
        
        # Warning validations (will warn but allow trade)
        if not is_live:
            validation_warnings.append(f"Using safety default balance of ${balance} - actual balance unknown")
        
        # Get balance tier info
        tier_info = self.get_balance_tier_info(balance)
        
        if balance < 100:
            validation_warnings.append(f"Small account detected - {tier_info['warning']}")
        
        # Safety information
        safety_info = {
            "balance": balance,
            "is_live_balance": is_live,
            "balance_tier": tier_info,
            "max_risk_usd": tier_info["max_risk_usd"],
            "account_info": {
                "account_id": balance_info.account_id,
                "server": balance_info.server,
                "currency": balance_info.currency,
                "free_margin": balance_info.free_margin
            }
        }
        
        # Determine if trade can execute
        can_execute = len(validation_errors) == 0
        
        return PreTradeValidation(
            user_id=user_id,
            can_execute=can_execute,
            balance=balance,
            is_live_balance=is_live,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            safety_info=safety_info,
            timestamp=datetime.now()
        )
    
    def generate_validation_message(self, validation: PreTradeValidation) -> str:
        """Generate user-friendly validation message"""
        
        if validation.can_execute:
            # Safe to trade message
            tier_info = validation.safety_info["balance_tier"]
            message = f"""
🛡️ **PRE-TRADE VALIDATION PASSED**

✅ **Account**: {validation.user_id}
✅ **Balance**: ${validation.balance:.2f} ({'Live' if validation.is_live_balance else 'Default'})
✅ **Tier**: {tier_info['tier']} - {tier_info['warning']}
✅ **Status**: Safe to trade

💡 **Risk Info**: Max recommended risk ${tier_info['max_risk_usd']} per trade
"""
            
            # Add warnings if any
            if validation.validation_warnings:
                message += "\n⚠️ **Warnings**:\n"
                for warning in validation.validation_warnings:
                    message += f"• {warning}\n"
        
        else:
            # Blocked trade message
            message = f"""
🚨 **TRADE BLOCKED - SAFETY PROTECTION**

❌ **Account**: {validation.user_id}
❌ **Balance**: ${validation.balance:.2f}
❌ **Status**: Trade blocked for account protection

**Errors**:
"""
            for error in validation.validation_errors:
                message += f"• {error}\n"
            
            message += """
💡 **What to do**:
• Deposit more funds to meet minimum balance
• Contact support if balance is incorrect
• Check account connection status
"""
        
        return message
    
    def pre_flight_check(self, user_id: str) -> Dict:
        """Main pre-flight check before any trade creation"""
        
        validation = self.validate_account_safety(user_id)
        message = self.generate_validation_message(validation)
        
        result = {
            "user_id": user_id,
            "can_execute": validation.can_execute,
            "balance": validation.balance,
            "is_live_balance": validation.is_live_balance,
            "validation_message": message,
            "errors": validation.validation_errors,
            "warnings": validation.validation_warnings,
            "safety_info": validation.safety_info,
            "timestamp": validation.timestamp.isoformat()
        }
        
        # Log result
        if validation.can_execute:
            self.logger.info(f"✅ Pre-flight PASSED for {user_id}: ${validation.balance}")
        else:
            self.logger.warning(f"❌ Pre-flight BLOCKED for {user_id}: {validation.validation_errors}")
        
        return result
    
    def validate_multiple_users(self, user_ids: List[str]) -> Dict:
        """Validate multiple users efficiently"""
        results = {}
        
        for user_id in user_ids:
            try:
                results[user_id] = self.pre_flight_check(user_id)
            except Exception as e:
                self.logger.error(f"❌ Validation failed for {user_id}: {e}")
                results[user_id] = {
                    "can_execute": False,
                    "error": str(e)
                }
        
        return results

# Global validation system
VALIDATION_SYSTEM = PreTradeValidationSystem()

def pre_trade_safety_check(user_id: str) -> Dict:
    """Main function: Pre-trade safety check"""
    return VALIDATION_SYSTEM.pre_flight_check(user_id)

def can_user_trade_safely(user_id: str) -> bool:
    """Quick check if user can trade safely"""
    result = pre_trade_safety_check(user_id)
    return result["can_execute"]

def get_user_safety_info(user_id: str) -> Dict:
    """Get detailed safety information for user"""
    result = pre_trade_safety_check(user_id)
    return result["safety_info"]

if __name__ == "__main__":
    # Test the system
    print("🛡️ TESTING PRE-TRADE VALIDATION SYSTEM")
    print("=" * 50)
    
    # Test with user 843859
    result = pre_trade_safety_check("843859")
    print(f"Can Execute: {result['can_execute']}")
    print(f"Balance: ${result['balance']}")
    print(f"Live Balance: {result['is_live_balance']}")
    print(f"Errors: {result['errors']}")
    print(f"Warnings: {result['warnings']}")
    print(f"\\nValidation Message:\\n{result['validation_message']}")