#!/usr/bin/env python3
"""
ZMQ Migration Helpers
Feature flags and migration utilities for transitioning from fire.txt to ZMQ
"""

import os
import json
import logging
from typing import Dict, Optional, Callable
from pathlib import Path

logger = logging.getLogger('ZMQMigration')

# Feature flags
USE_ZMQ = os.getenv('USE_ZMQ', 'false').lower() == 'true'
ZMQ_DUAL_WRITE = os.getenv('ZMQ_DUAL_WRITE', 'true').lower() == 'true'
ZMQ_LOG_MIGRATIONS = os.getenv('ZMQ_LOG_MIGRATIONS', 'true').lower() == 'true'

class MigrationHelper:
    """
    Helper class to manage migration from fire.txt to ZMQ
    """
    
    def __init__(self):
        self.zmq_controller = None
        self.migration_stats = {
            'fire_txt_writes': 0,
            'zmq_writes': 0,
            'dual_writes': 0,
            'failures': 0
        }
        
        # Try to import ZMQ controller if enabled
        if USE_ZMQ:
            try:
                from zmq_bitten_controller import get_bitten_controller
                self.zmq_controller = get_bitten_controller()
                logger.info("✅ ZMQ migration enabled - controller loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load ZMQ controller: {e}")
                
    def execute_trade(self, user_id: str, signal_data: Dict, 
                     fire_path: Optional[str] = None,
                     callback: Optional[Callable] = None) -> Dict:
        """
        Execute trade with migration support
        
        Args:
            user_id: User identifier
            signal_data: Trade signal data
            fire_path: Path to fire.txt (for legacy support)
            callback: Optional callback for trade result
            
        Returns:
            Dict with execution status
        """
        result = {
            'success': False,
            'method': 'none',
            'message': 'No execution method available'
        }
        
        # Log migration attempt
        if ZMQ_LOG_MIGRATIONS:
            logger.info(f"🔄 Migration: Executing trade for {user_id} - "
                       f"USE_ZMQ={USE_ZMQ}, DUAL_WRITE={ZMQ_DUAL_WRITE}")
        
        # ZMQ execution
        if USE_ZMQ and self.zmq_controller:
            try:
                # Add signal_id if not present
                if 'signal_id' not in signal_data:
                    signal_data['signal_id'] = f"MIG_{user_id}_{int(time.time() * 1000)}"
                
                # Execute via ZMQ
                zmq_success = self.zmq_controller.send_signal(signal_data, callback)
                
                if zmq_success:
                    self.migration_stats['zmq_writes'] += 1
                    result = {
                        'success': True,
                        'method': 'zmq',
                        'message': 'Trade sent via ZMQ',
                        'signal_id': signal_data['signal_id']
                    }
                    
                    if ZMQ_LOG_MIGRATIONS:
                        logger.info(f"✅ ZMQ execution successful: {signal_data['signal_id']}")
                else:
                    raise Exception("ZMQ send_signal returned False")
                    
            except Exception as e:
                logger.error(f"❌ ZMQ execution failed: {e}")
                self.migration_stats['failures'] += 1
                
                # Fall back to fire.txt if not dual-write mode
                if not ZMQ_DUAL_WRITE:
                    result['message'] = f"ZMQ failed: {e}"
        
        # Fire.txt execution (legacy or dual-write)
        if (not USE_ZMQ or ZMQ_DUAL_WRITE or not result['success']) and fire_path:
            try:
                # Ensure directory exists
                Path(fire_path).parent.mkdir(parents=True, exist_ok=True)
                
                # Write to fire.txt
                with open(fire_path, 'w') as f:
                    json.dump(signal_data, f)
                
                self.migration_stats['fire_txt_writes'] += 1
                
                # Update result if this is primary method
                if not result['success']:
                    result = {
                        'success': True,
                        'method': 'fire_txt',
                        'message': 'Trade written to fire.txt',
                        'path': fire_path
                    }
                else:
                    # This was dual-write
                    self.migration_stats['dual_writes'] += 1
                    result['method'] = 'dual'
                    result['message'] = 'Trade sent via ZMQ and fire.txt'
                
                if ZMQ_LOG_MIGRATIONS:
                    logger.info(f"✅ Fire.txt write successful: {fire_path}")
                    
            except Exception as e:
                logger.error(f"❌ Fire.txt write failed: {e}")
                self.migration_stats['failures'] += 1
                
                if not result['success']:
                    result['message'] = f"All methods failed: {e}"
        
        return result
        
    def get_migration_stats(self) -> Dict:
        """
        Get migration statistics
        """
        total = sum([
            self.migration_stats['fire_txt_writes'],
            self.migration_stats['zmq_writes']
        ]) - self.migration_stats['dual_writes']
        
        zmq_pct = (self.migration_stats['zmq_writes'] / total * 100) if total > 0 else 0
        
        return {
            **self.migration_stats,
            'total_executions': total,
            'zmq_percentage': zmq_pct,
            'migration_mode': self._get_migration_mode()
        }
        
    def _get_migration_mode(self) -> str:
        """
        Get current migration mode
        """
        if USE_ZMQ and ZMQ_DUAL_WRITE:
            return "dual_write"
        elif USE_ZMQ:
            return "zmq_only"
        else:
            return "legacy_fire_txt"
            
    def health_check(self) -> Dict:
        """
        Check health of migration system
        """
        health = {
            'mode': self._get_migration_mode(),
            'zmq_available': self.zmq_controller is not None,
            'stats': self.get_migration_stats()
        }
        
        # Test ZMQ if available
        if self.zmq_controller:
            try:
                test_result = self.zmq_controller.send_command('ping')
                health['zmq_status'] = 'healthy' if test_result else 'unhealthy'
            except Exception as e:
                health['zmq_status'] = f'error: {e}'
        else:
            health['zmq_status'] = 'not_configured'
            
        return health

# Global migration helper instance
_migration_helper = None

def get_migration_helper() -> MigrationHelper:
    """
    Get or create migration helper instance
    """
    global _migration_helper
    if _migration_helper is None:
        _migration_helper = MigrationHelper()
    return _migration_helper

# Convenience functions for easy migration

def migrate_execute_trade(user_id: str, signal_data: Dict, 
                         fire_path: Optional[str] = None) -> Dict:
    """
    Execute trade with automatic migration handling
    
    This is a drop-in replacement for fire.txt writes
    """
    helper = get_migration_helper()
    return helper.execute_trade(user_id, signal_data, fire_path)

def check_migration_status() -> Dict:
    """
    Get current migration status and statistics
    """
    helper = get_migration_helper()
    return helper.health_check()

# Example usage for migration
"""
# Before (fire.txt only):
with open(fire_path, 'w') as f:
    json.dump(signal_data, f)

# After (with migration):
from zmq_migration_helpers import migrate_execute_trade
result = migrate_execute_trade(user_id, signal_data, fire_path)
if not result['success']:
    logger.error(f"Trade execution failed: {result['message']}")
"""

import time  # Add missing import

if __name__ == "__main__":
    # Test migration helper
    print("🔧 ZMQ Migration Helper Test")
    print("="*50)
    
    # Check current configuration
    print(f"USE_ZMQ: {USE_ZMQ}")
    print(f"ZMQ_DUAL_WRITE: {ZMQ_DUAL_WRITE}")
    print(f"ZMQ_LOG_MIGRATIONS: {ZMQ_LOG_MIGRATIONS}")
    
    # Get health status
    status = check_migration_status()
    print(f"\nMigration Mode: {status['mode']}")
    print(f"ZMQ Available: {status['zmq_available']}")
    print(f"ZMQ Status: {status['zmq_status']}")
    
    # Test execution
    print("\n🧪 Testing trade execution...")
    test_signal = {
        'symbol': 'EURUSD',
        'action': 'buy',
        'lot': 0.01,
        'sl': 50,
        'tp': 100
    }
    
    result = migrate_execute_trade('test_user', test_signal, '/tmp/test_fire.txt')
    print(f"Result: {result}")
    
    # Show stats
    helper = get_migration_helper()
    stats = helper.get_migration_stats()
    print(f"\n📊 Migration Statistics:")
    print(f"Fire.txt writes: {stats['fire_txt_writes']}")
    print(f"ZMQ writes: {stats['zmq_writes']}")
    print(f"Dual writes: {stats['dual_writes']}")
    print(f"Failures: {stats['failures']}")
    print(f"ZMQ percentage: {stats['zmq_percentage']:.1f}%")