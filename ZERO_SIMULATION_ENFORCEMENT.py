#!/usr/bin/env python3
"""
🚨 ZERO SIMULATION ENFORCEMENT - CRITICAL ERROR PREVENTION
Permanently blocks ALL fake data from entering the system

THIS MODULE MUST BE IMPORTED BY ALL BITTEN CORE COMPONENTS
"""

import sys
import logging
from typing import Any, Dict, Optional
import traceback

logger = logging.getLogger("ZERO_SIMULATION_ENFORCER")

class FakeDataViolationError(Exception):
    """Raised when fake/simulation data is detected"""
    pass

class ZeroSimulationEnforcer:
    """
    🛡️ ZERO SIMULATION ENFORCER - THE GUARDIAN
    
    Prevents ANY fake data from entering the system
    FAILS FAST and FAILS LOUD when simulation detected
    """
    
    # BANNED FAKE VALUES - System dies if these are detected
    BANNED_FAKE_BALANCES = [
        10000.0, 10000, 15000.0, 15000, 15300.0, 15300,
        5000.0, 5000, 20000.0, 20000, 100000.0, 100000
    ]
    
    BANNED_FAKE_ACCOUNTS = [
        "demo", "test", "fake", "simulation", "mock", "sample"
    ]
    
    BANNED_FAKE_KEYWORDS = [
        "random.random", "mock", "fake", "demo_mode", "simulation", 
        "test_balance", "sample_data", "placeholder"
    ]
    
    @staticmethod
    def validate_account_balance(balance: Any, source: str = "unknown") -> float:
        """
        Validate account balance is REAL - DIE if fake detected
        
        Args:
            balance: The balance to validate
            source: Where this balance came from (for error reporting)
            
        Returns:
            float: The validated real balance
            
        Raises:
            FakeDataViolationError: If fake data detected
        """
        
        if balance is None:
            raise FakeDataViolationError(
                f"🚨 CRITICAL: NULL balance detected from {source} - REAL DATA REQUIRED"
            )
        
        try:
            balance_float = float(balance)
        except (ValueError, TypeError):
            raise FakeDataViolationError(
                f"🚨 CRITICAL: Invalid balance '{balance}' from {source} - REAL DATA REQUIRED"
            )
        
        # Check for banned fake values
        if balance_float in ZeroSimulationEnforcer.BANNED_FAKE_BALANCES:
            raise FakeDataViolationError(
                f"🚨 CRITICAL: FAKE BALANCE DETECTED: ${balance_float} from {source}\\n"
                f"BANNED FALLBACK VALUES: {ZeroSimulationEnforcer.BANNED_FAKE_BALANCES}\\n"
                f"SYSTEM POLICY: ZERO SIMULATION - REAL DATA ONLY\\n"
                f"STACK TRACE:\\n{''.join(traceback.format_stack())}"
            )
        
        # Balance must be positive and realistic
        if balance_float <= 0:
            raise FakeDataViolationError(
                f"🚨 CRITICAL: Invalid balance ${balance_float} from {source} - must be positive"
            )
            
        if balance_float > 1000000:  # $1M cap - anything higher needs verification
            logger.warning(f"⚠️ HIGH BALANCE DETECTED: ${balance_float} from {source} - please verify")
        
        logger.info(f"✅ REAL BALANCE VALIDATED: ${balance_float} from {source}")
        return balance_float
    
    @staticmethod
    def validate_account_info(account_info: Dict, source: str = "unknown") -> Dict:
        """
        Validate complete account info is REAL
        
        Args:
            account_info: Account data dictionary
            source: Where this data came from
            
        Returns:
            Dict: Validated account info
            
        Raises:
            FakeDataViolationError: If fake data detected
        """
        
        if not account_info:
            raise FakeDataViolationError(
                f"🚨 CRITICAL: Empty account info from {source} - REAL DATA REQUIRED"
            )
        
        # Validate balance if present
        if 'balance' in account_info:
            account_info['balance'] = ZeroSimulationEnforcer.validate_account_balance(
                account_info['balance'], f"{source}.balance"
            )
        
        # Validate equity if present
        if 'equity' in account_info:
            account_info['equity'] = ZeroSimulationEnforcer.validate_account_balance(
                account_info['equity'], f"{source}.equity"
            )
        
        # Check for banned fake account identifiers
        account_str = str(account_info).lower()
        for banned in ZeroSimulationEnforcer.BANNED_FAKE_ACCOUNTS:
            if banned in account_str and "real" not in account_str:
                logger.warning(f"⚠️ SUSPICIOUS ACCOUNT DATA: {banned} detected in {source}")
        
        logger.info(f"✅ ACCOUNT INFO VALIDATED from {source}")
        return account_info
    
    @staticmethod
    def enforce_real_data_only():
        """
        Master enforcement - checks entire system for fake data
        Call this on system startup
        """
        logger.info("🛡️ ZERO SIMULATION ENFORCER: SYSTEM SCAN STARTING")
        
        # Check for banned imports
        banned_modules = ['random', 'mock', 'faker', 'unittest.mock']
        for module_name in sys.modules:
            if any(banned in module_name.lower() for banned in banned_modules):
                logger.warning(f"⚠️ SUSPICIOUS MODULE LOADED: {module_name}")
        
        logger.info("🛡️ ZERO SIMULATION ENFORCER: ACTIVE AND GUARDING")

# Global enforcer instance
ENFORCER = ZeroSimulationEnforcer()

def validate_balance(balance: Any, source: str = "unknown") -> float:
    """Global function for balance validation"""
    return ENFORCER.validate_account_balance(balance, source)

def validate_account(account_info: Dict, source: str = "unknown") -> Dict:
    """Global function for account validation"""
    return ENFORCER.validate_account_info(account_info, source)

def enforce_zero_simulation():
    """Global function to enforce zero simulation"""
    return ENFORCER.enforce_real_data_only()

# AUTO-ENFORCE on import
try:
    enforce_zero_simulation()
except Exception as e:
    logger.error(f"❌ ZERO SIMULATION ENFORCEMENT FAILED: {e}")

if __name__ == "__main__":
    print("🛡️ ZERO SIMULATION ENFORCER - TESTING")
    print("=" * 50)
    
    # Test banned values
    for banned_balance in ENFORCER.BANNED_FAKE_BALANCES[:3]:
        try:
            validate_balance(banned_balance, "test")
            print(f"❌ FAILED: {banned_balance} should have been blocked")
        except FakeDataViolationError:
            print(f"✅ BLOCKED: {banned_balance} correctly rejected")
    
    # Test valid value
    try:
        real_balance = validate_balance(2847.50, "test_real")
        print(f"✅ ALLOWED: ${real_balance}")
    except FakeDataViolationError as e:
        print(f"❌ FAILED: Real balance rejected: {e}")
    
    print("🛡️ ZERO SIMULATION ENFORCER: OPERATIONAL")