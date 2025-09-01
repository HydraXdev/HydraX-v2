#!/usr/bin/env python3
"""
C.O.R.E. Truth Tracker Integration
Connects crypto signal generation to truth tracking system
"""

import logging
from typing import Dict, Optional
from truth_tracker import TruthTracker

logger = logging.getLogger(__name__)

class CoreTruthIntegration:
    """
    Integration layer between C.O.R.E. crypto signals and truth tracker
    """
    
    def __init__(self, truth_tracker: Optional[TruthTracker] = None):
        self.truth_tracker = truth_tracker or TruthTracker()
        
    def track_core_signal(self, signal_data: Dict) -> bool:
        """
        Add a C.O.R.E. crypto signal to truth tracking
        
        Args:
            signal_data: C.O.R.E. signal packet from core_filter.py
            
        Returns:
            bool: True if successfully added for tracking
        """
        try:
            # Log the signal addition
            signal_id = signal_data.get('uuid', 'unknown')
            symbol = signal_data.get('symbol', 'BTCUSD')
            entry = signal_data.get('entry', 0)
            
            logger.info(f"🔗 Integrating C.O.R.E. signal {signal_id} into truth tracker: {symbol} @ ${entry}")
            
            # Add to truth tracker
            success = self.truth_tracker.add_core_signal(signal_data)
            
            if success:
                logger.info(f"✅ C.O.R.E. signal {signal_id} added to crypto truth tracking")
            else:
                logger.error(f"❌ Failed to add C.O.R.E. signal {signal_id} to truth tracking")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error integrating C.O.R.E. signal: {e}")
            return False
    
    def get_crypto_stats(self) -> Dict:
        """
        Get crypto signal statistics from truth tracker
        
        Returns:
            Dict: Crypto signal performance statistics
        """
        try:
            # Get current tracker status
            status = self.truth_tracker.get_status()
            
            # Count crypto signals in active tracking
            crypto_active = 0
            with self.truth_tracker.lock:
                for tracker in self.truth_tracker.active_signals.values():
                    if tracker.signal_type == "crypto":
                        crypto_active += 1
            
            return {
                'crypto_active_signals': crypto_active,
                'total_active_signals': status['active_signals'],
                'total_processed_signals': status['processed_signals'],
                'crypto_log_path': str(self.truth_tracker.crypto_truth_log_path),
                'forex_log_path': str(self.truth_tracker.truth_log_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting crypto stats: {e}")
            return {}

# Global instance for easy access
_core_truth_integration = None

def get_core_truth_integration() -> CoreTruthIntegration:
    """Get global C.O.R.E. truth integration instance"""
    global _core_truth_integration
    if _core_truth_integration is None:
        _core_truth_integration = CoreTruthIntegration()
    return _core_truth_integration

def track_core_signal(signal_data: Dict) -> bool:
    """Convenience function to track a C.O.R.E. signal"""
    integration = get_core_truth_integration()
    return integration.track_core_signal(signal_data)

def get_crypto_stats() -> Dict:
    """Convenience function to get crypto stats"""
    integration = get_core_truth_integration()
    return integration.get_crypto_stats()

if __name__ == "__main__":
    # Test integration
    print("🧪 Testing C.O.R.E. Truth Integration")
    
    # Create test signal
    test_signal = {
        "uuid": "test-btc-mission-123456",
        "symbol": "BTCUSD",
        "entry": 67245.50,
        "sl": 66245.50,
        "tp": 69245.50,
        "pattern": "Test Sweep Reversal",
        "score": 78,
        "xp": 160,
        "timestamp": "2025-08-02T12:00:00",
        "engine": "CORE",
        "type": "CRYPTO_ASSAULT",
        "risk_reward": 2.0
    }
    
    # Test tracking
    integration = CoreTruthIntegration()
    success = integration.track_core_signal(test_signal)
    
    if success:
        print("✅ Test signal successfully integrated")
        stats = integration.get_crypto_stats()
        print(f"📊 Stats: {stats}")
    else:
        print("❌ Test signal integration failed")