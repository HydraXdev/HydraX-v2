#!/usr/bin/env python3
"""
🎛️ VENOM Throttle Controller Integration
Connects VENOM v8 Stream Pipeline with Dynamic Signal Governor

This module implements the integration between venom_stream_pipeline.py 
and throttle_controller.py to enable dynamic TCS/ML threshold adjustment
based on real-time signal performance.
"""

import time
import logging
from typing import Optional, Dict, Any
from threading import Thread
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - THROTTLE_INTEGRATION - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VenomThrottleIntegration:
    """Integration layer between VENOM Stream Pipeline and Throttle Controller"""
    
    def __init__(self, venom_engine, throttle_controller):
        """
        Initialize integration
        
        Args:
            venom_engine: VenomStreamEngine instance from venom_stream_pipeline.py
            throttle_controller: VenomThrottleController instance from throttle_controller.py
        """
        self.venom_engine = venom_engine
        self.throttle_controller = throttle_controller
        self.integration_active = False
        self.monitoring_thread = None
        
        # Override VENOM's fire threshold with throttle controller
        self._apply_initial_thresholds()
        
        logger.info("🎛️ VENOM Throttle Integration initialized")
    
    def _apply_initial_thresholds(self):
        """Apply throttle controller thresholds to VENOM engine"""
        tcs_threshold, ml_threshold = self.throttle_controller.get_current_thresholds()
        
        # Update VENOM's fire threshold with TCS threshold
        self.venom_engine.fire_threshold = tcs_threshold
        
        logger.info(f"🎯 Applied initial thresholds: TCS={tcs_threshold}%, ML={ml_threshold}")
    
    def start_integration(self):
        """Start the throttle integration monitoring"""
        if self.integration_active:
            return
        
        self.integration_active = True
        
        # Start throttle controller monitoring
        self.throttle_controller.start_monitoring()
        
        # Start integration monitoring thread
        self.monitoring_thread = Thread(target=self._integration_monitor_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("🎛️ VENOM Throttle Integration started")
    
    def stop_integration(self):
        """Stop the throttle integration monitoring"""
        self.integration_active = False
        
        if self.throttle_controller:
            self.throttle_controller.stop_monitoring()
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("🎛️ VENOM Throttle Integration stopped")
    
    def _integration_monitor_loop(self):
        """Background monitoring loop for throttle integration"""
        while self.integration_active:
            try:
                # Update VENOM thresholds from throttle controller
                self._sync_thresholds()
                
                # Monitor VENOM performance and update throttle controller
                self._sync_performance_data()
                
                # Sleep for 10 seconds between updates
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"❌ Integration monitor error: {e}")
                time.sleep(30)
    
    def _sync_thresholds(self):
        """Sync thresholds from throttle controller to VENOM engine"""
        try:
            tcs_threshold, ml_threshold = self.throttle_controller.get_current_thresholds()
            
            # Update VENOM's fire threshold if it changed
            if abs(self.venom_engine.fire_threshold - tcs_threshold) > 0.1:
                old_threshold = self.venom_engine.fire_threshold
                self.venom_engine.fire_threshold = tcs_threshold
                
                logger.info(f"🎯 Updated VENOM fire threshold: {old_threshold}% → {tcs_threshold}%")
            
        except Exception as e:
            logger.error(f"❌ Threshold sync error: {e}")
    
    def _sync_performance_data(self):
        """Sync VENOM performance data to throttle controller"""
        try:
            # Get recent signals from VENOM stats
            stats = self.venom_engine.stats
            
            # Check if we have truth tracking for signal results
            if hasattr(self, '_last_signal_count'):
                new_signals = stats['signals_fired'] - self._last_signal_count
                
                if new_signals > 0:
                    logger.debug(f"📊 {new_signals} new signals since last sync")
            
            self._last_signal_count = stats['signals_fired']
            
        except Exception as e:
            logger.error(f"❌ Performance sync error: {e}")
    
    def on_signal_generated(self, signal_data: Dict[str, Any]):
        """
        Hook called when VENOM generates a signal
        
        Args:
            signal_data: Signal data from StreamSignal
        """
        try:
            # Check if signal should fire based on throttle controller
            should_fire = self.throttle_controller.should_fire_signal(
                tcs_score=signal_data.get('confidence', 0),
                ml_score=0.70  # Default ML score for stream mode
            )
            
            if not should_fire:
                logger.debug(f"🚫 Signal blocked by throttle controller: {signal_data.get('symbol')} {signal_data.get('confidence')}%")
                return False
            
            # Record signal in throttle controller
            self.throttle_controller.add_signal(
                signal_id=signal_data.get('signal_id', ''),
                symbol=signal_data.get('symbol', ''),
                direction=signal_data.get('direction', ''),
                tcs_score=signal_data.get('confidence', 0),
                ml_score=0.70  # Default ML score for stream mode
            )
            
            logger.debug(f"✅ Signal approved by throttle controller: {signal_data.get('symbol')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Signal generation hook error: {e}")
            return True  # Default to allowing signal on error
    
    def on_signal_result(self, signal_id: str, result: str, pips: Optional[float] = None):
        """
        Hook called when signal result is available
        
        Args:
            signal_id: Signal identifier
            result: "win" or "loss"
            pips: Pip profit/loss (optional)
        """
        try:
            # Update throttle controller with signal result
            self.throttle_controller.update_signal_result(signal_id, result, pips)
            
            logger.debug(f"📊 Signal result updated: {signal_id} → {result}")
            
        except Exception as e:
            logger.error(f"❌ Signal result hook error: {e}")
    
    def get_throttle_status(self) -> Dict[str, Any]:
        """Get current throttle controller status"""
        try:
            return self.throttle_controller.get_status_report()
        except Exception as e:
            logger.error(f"❌ Status report error: {e}")
            return {
                "error": str(e),
                "integration_active": self.integration_active
            }


def integrate_venom_with_throttle(venom_engine, throttle_controller):
    """
    Factory function to create and start VENOM throttle integration
    
    Args:
        venom_engine: VenomStreamEngine instance
        throttle_controller: VenomThrottleController instance
    
    Returns:
        VenomThrottleIntegration instance
    """
    integration = VenomThrottleIntegration(venom_engine, throttle_controller)
    integration.start_integration()
    return integration


# Modified VENOM Stream Engine with Throttle Integration
class EnhancedVenomStreamEngine:
    """
    Enhanced VENOM Stream Engine with integrated throttle controller
    
    This class wraps the original VenomStreamEngine and adds throttle controller integration
    """
    
    def __init__(self):
        # Import the required modules
        from venom_stream_pipeline import VenomStreamEngine
        from throttle_controller import get_throttle_controller
        
        # Initialize base engine
        self.base_engine = VenomStreamEngine()
        
        # Initialize throttle controller
        self.throttle_controller = get_throttle_controller()
        
        # Create integration
        self.integration = VenomThrottleIntegration(
            venom_engine=self.base_engine,
            throttle_controller=self.throttle_controller
        )
        
        # Start integration
        self.integration.start_integration()
        
        logger.info("🎛️ Enhanced VENOM Stream Engine with throttle control initialized")
    
    def __getattr__(self, name):
        """Delegate all other attributes to the base engine"""
        return getattr(self.base_engine, name)
    
    def process_tick_stream(self, tick_data: Dict) -> Optional[Any]:
        """Enhanced tick processing with throttle control"""
        # Process tick through base engine
        signal = self.base_engine.process_tick_stream(tick_data)
        
        if signal:
            # Check with throttle controller
            signal_data = {
                'signal_id': signal.signal_id,
                'symbol': signal.symbol,
                'direction': signal.direction,
                'confidence': signal.confidence
            }
            
            # Apply throttle control
            if self.integration.on_signal_generated(signal_data):
                return signal
            else:
                return None  # Signal blocked by throttle controller
        
        return signal
    
    def dispatch_signal(self, signal) -> bool:
        """Enhanced signal dispatch with throttle integration"""
        # Use base engine dispatch
        result = self.base_engine.dispatch_signal(signal)
        
        # Log to throttle controller for performance tracking
        if result:
            logger.debug(f"🔥 Signal dispatched via throttle integration: {signal.symbol}")
        
        return result
    
    def get_throttle_status(self) -> Dict[str, Any]:
        """Get current throttle status"""
        return self.integration.get_throttle_status()
    
    def stop(self):
        """Stop the enhanced engine and throttle integration"""
        self.integration.stop_integration()
        logger.info("🎛️ Enhanced VENOM Stream Engine stopped")


if __name__ == "__main__":
    """Test the integration"""
    print("🧪 Testing VENOM Throttle Integration")
    
    try:
        # Initialize enhanced engine
        enhanced_engine = EnhancedVenomStreamEngine()
        
        # Run for 30 seconds
        import time
        print("⏱️ Running for 30 seconds...")
        time.sleep(30)
        
        # Get status
        status = enhanced_engine.get_throttle_status()
        print(f"📊 Final status: {json.dumps(status, indent=2)}")
        
        # Stop
        enhanced_engine.stop()
        
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
    
    print("✅ Integration test complete")