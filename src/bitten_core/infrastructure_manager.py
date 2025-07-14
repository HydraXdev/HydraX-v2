#!/usr/bin/env python3
"""
Infrastructure Manager - Ensures singleton instances of critical components
Prevents multiple instantiations and provides thread-safe access
"""

import threading
from typing import Optional
import logging

class InfrastructureManager:
    """Manages singleton instances of infrastructure components"""
    
    _instance = None
    _lock = threading.Lock()
    
    # Component instances
    _bulletproof_mt5_instance = None
    _aws_mt5_bridge_instance = None
    
    # Instance locks for thread safety
    _bulletproof_lock = threading.Lock()
    _aws_bridge_lock = threading.Lock()
    
    def __new__(cls):
        """Ensure only one instance of InfrastructureManager exists"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the infrastructure manager"""
        if self._initialized:
            return
            
        self._initialized = True
        self.logger = self._setup_logging()
        self.logger.info("🏗️ Infrastructure Manager initialized")
    
    def _setup_logging(self):
        """Setup logging for the infrastructure manager"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - INFRA MANAGER - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_bulletproof_mt5_infrastructure(self):
        """Get singleton instance of BulletproofMT5Infrastructure"""
        if self._bulletproof_mt5_instance is None:
            with self._bulletproof_lock:
                if self._bulletproof_mt5_instance is None:
                    try:
                        # Import here to avoid circular imports
                        import sys
                        import os
                        # Add parent directory to path
                        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                        if parent_dir not in sys.path:
                            sys.path.insert(0, parent_dir)
                            
                        from BULLETPROOF_INFRASTRUCTURE import BulletproofMT5Infrastructure
                        
                        self.logger.info("🛡️ Creating BulletproofMT5Infrastructure singleton...")
                        self._bulletproof_mt5_instance = BulletproofMT5Infrastructure()
                        self.logger.info("✅ BulletproofMT5Infrastructure singleton created")
                    except Exception as e:
                        self.logger.error(f"❌ Failed to create BulletproofMT5Infrastructure: {e}")
                        raise
        
        return self._bulletproof_mt5_instance
    
    def get_aws_mt5_bridge(self):
        """Get singleton instance of AWSMT5Bridge"""
        if self._aws_mt5_bridge_instance is None:
            with self._aws_bridge_lock:
                if self._aws_mt5_bridge_instance is None:
                    try:
                        # Import here to avoid circular imports
                        import sys
                        import os
                        # Add parent directory to path
                        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                        if parent_dir not in sys.path:
                            sys.path.insert(0, parent_dir)
                            
                        from aws_mt5_bridge import AWSMT5Bridge
                        
                        self.logger.info("🌉 Creating AWSMT5Bridge singleton...")
                        self._aws_mt5_bridge_instance = AWSMT5Bridge()
                        self.logger.info("✅ AWSMT5Bridge singleton created")
                    except Exception as e:
                        self.logger.error(f"❌ Failed to create AWSMT5Bridge: {e}")
                        raise
        
        return self._aws_mt5_bridge_instance
    
    def reset_infrastructure(self):
        """Reset all infrastructure instances (use with caution)"""
        with self._bulletproof_lock:
            self._bulletproof_mt5_instance = None
            self.logger.warning("⚠️ BulletproofMT5Infrastructure instance reset")
            
        with self._aws_bridge_lock:
            self._aws_mt5_bridge_instance = None
            self.logger.warning("⚠️ AWSMT5Bridge instance reset")
    
    def get_status(self):
        """Get status of all infrastructure components"""
        status = {
            'bulletproof_mt5': 'initialized' if self._bulletproof_mt5_instance else 'not_initialized',
            'aws_mt5_bridge': 'initialized' if self._aws_mt5_bridge_instance else 'not_initialized'
        }
        
        # Try to get detailed status if instances exist
        if self._bulletproof_mt5_instance:
            try:
                bulletproof_status = self._bulletproof_mt5_instance.status_report()
                status['bulletproof_details'] = bulletproof_status
            except Exception as e:
                status['bulletproof_error'] = str(e)
        
        if self._aws_mt5_bridge_instance:
            try:
                status['aws_bridge_connected'] = self._aws_mt5_bridge_instance.test_connection()
            except Exception as e:
                status['aws_bridge_error'] = str(e)
        
        return status

# Global singleton instance
infrastructure_manager = InfrastructureManager()

# Convenience functions for easy access
def get_bulletproof_mt5_infrastructure():
    """Get singleton BulletproofMT5Infrastructure instance"""
    return infrastructure_manager.get_bulletproof_mt5_infrastructure()

def get_aws_mt5_bridge():
    """Get singleton AWSMT5Bridge instance"""
    return infrastructure_manager.get_aws_mt5_bridge()

def get_infrastructure_status():
    """Get status of all infrastructure components"""
    return infrastructure_manager.get_status()

# Test the infrastructure manager
if __name__ == "__main__":
    print("🧪 Testing Infrastructure Manager...")
    
    # Test singleton behavior
    manager1 = InfrastructureManager()
    manager2 = InfrastructureManager()
    
    print(f"✅ Singleton test: {manager1 is manager2}")
    
    # Test getting components
    try:
        print("\n🌉 Getting AWS MT5 Bridge...")
        bridge1 = get_aws_mt5_bridge()
        bridge2 = get_aws_mt5_bridge()
        print(f"✅ AWS Bridge singleton test: {bridge1 is bridge2}")
        
        print("\n🛡️ Getting Bulletproof Infrastructure...")
        infra1 = get_bulletproof_mt5_infrastructure()
        infra2 = get_bulletproof_mt5_infrastructure()
        print(f"✅ Bulletproof singleton test: {infra1 is infra2}")
        
        print("\n📊 Infrastructure Status:")
        status = get_infrastructure_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")