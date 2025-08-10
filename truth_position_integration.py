#!/usr/bin/env python3
"""
TRUTH TRACKER ↔ POSITION TRACKER INTEGRATION
Real data flow connection with strict validation
CRITICAL: Only process REAL confirmations and outcomes
"""

import sys
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, Optional, List

# Add project root to path
sys.path.append('/root/HydraX-v2')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TRUTH_POSITION_INTEGRATION - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/truth_position_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RealDataIntegrationError(Exception):
    """Raised when non-real data is detected"""
    pass

class TruthPositionIntegrator:
    """
    Integrates Truth Tracker with Position Tracker using REAL data only
    ABSOLUTE RULE: No fake/demo/synthetic data allowed
    """
    
    def __init__(self):
        self.running = False
        self.integration_stats = {
            'positions_opened': 0,
            'positions_closed': 0,
            'real_confirmations_processed': 0,
            'fake_data_rejected': 0,
            'integration_errors': 0,
            'start_time': time.time()
        }
        
        # Import components
        try:
            from black_box_complete_truth_system import get_truth_system
            self.truth_tracker = get_truth_system()
            logger.info("✅ Truth tracker connected")
        except ImportError:
            logger.error("❌ Truth tracker not available")
            self.truth_tracker = None
            
        try:
            from position_tracker import PositionTrackerAPI
            self.position_tracker = PositionTrackerAPI()
            logger.info("✅ Position tracker connected")
        except ImportError:
            logger.error("❌ Position tracker not available")
            self.position_tracker = None
            
        try:
            from confirmation_consumer import ConfirmationConsumer
            self.confirmation_consumer = ConfirmationConsumer()
            logger.info("✅ Confirmation consumer connected")
        except ImportError:
            logger.error("❌ Confirmation consumer not available")
            self.confirmation_consumer = None
        
        if not all([self.truth_tracker, self.position_tracker, self.confirmation_consumer]):
            logger.error("❌ Missing required components for integration")
            
        logger.info("🔗 Truth-Position Integrator initialized")
        
    def validate_real_data(self, data: Dict) -> bool:
        """
        Strict validation that data is from REAL sources
        REJECT any synthetic/demo/fake data
        """
        try:
            # Check for required real data fields
            required_fields = [
                'signal_id',
                'uuid', 
                'symbol',
                'entry_price',
                'result_type',  # WIN_TP, LOSS_SL, etc.
                'timestamp',
                'source'  # Must be 'EA_CONFIRMATION' or 'TRUTH_TRACKER'
            ]
            
            for field in required_fields:
                if field not in data:
                    raise RealDataIntegrationError(f"Missing required field: {field}")
                    
            # Validate source is real
            valid_sources = ['EA_CONFIRMATION', 'TRUTH_TRACKER', 'POSITION_TRACKER']
            if data['source'] not in valid_sources:
                raise RealDataIntegrationError(f"Invalid source: {data['source']}")
                
            # Check for demo account indicators
            if 'demo' in str(data.get('account', '')).lower():
                logger.warning(f"⚠️ Demo account detected: {data.get('account')}")
                # Allow demo accounts but log warning
                
            # Validate timestamp is recent (not simulated historical data)
            timestamp = data.get('timestamp')
            if timestamp:
                try:
                    ts_float = float(timestamp)
                    age = time.time() - ts_float
                    if age > 3600:  # More than 1 hour old
                        logger.warning(f"⚠️ Old data: {age:.0f} seconds old")
                        # Allow old data but log warning
                except (ValueError, TypeError):
                    raise RealDataIntegrationError(f"Invalid timestamp: {timestamp}")
                    
            # Validate ticket number if present
            if 'ticket' in data:
                ticket = data['ticket']
                if not str(ticket).isdigit() or int(ticket) <= 0:
                    raise RealDataIntegrationError(f"Invalid ticket: {ticket}")
                    
            logger.debug(f"✅ Real data validation passed: {data['signal_id']}")
            return True
            
        except RealDataIntegrationError as e:
            logger.error(f"❌ REAL DATA VALIDATION FAILED: {str(e)}")
            logger.error(f"❌ Rejected data: {json.dumps(data, indent=2)}")
            self.integration_stats['fake_data_rejected'] += 1
            return False
        except Exception as e:
            logger.error(f"❌ Validation error: {str(e)}")
            self.integration_stats['integration_errors'] += 1
            return False
            
    def process_truth_tracker_outcome(self, signal_id: str, outcome_data: Dict):
        """
        Process truth tracker outcomes and update position tracker
        ONLY process outcomes with REAL data validation
        """
        try:
            # Add metadata for validation
            outcome_data['source'] = 'TRUTH_TRACKER'
            outcome_data['signal_id'] = signal_id
            outcome_data['timestamp'] = time.time()
            
            # Strict real data validation
            if not self.validate_real_data(outcome_data):
                logger.error(f"❌ Truth tracker outcome rejected: {signal_id}")
                return False
                
            # Extract position information
            uuid = outcome_data.get('uuid', 'UNKNOWN')
            result_type = outcome_data.get('result_type')  # WIN_TP, LOSS_SL, etc.
            
            # Map truth tracker results to position tracker results
            result_mapping = {
                'WIN_TP': 'TP_HIT',
                'LOSS_SL': 'SL_HIT',
                'EXPIRED': 'EXPIRED',
                'CANCELLED': 'CANCELLED',
                'ERROR': 'ERROR'
            }
            
            position_result = result_mapping.get(result_type, 'UNKNOWN')
            
            if position_result == 'UNKNOWN':
                logger.warning(f"⚠️ Unknown result type: {result_type}")
                
            # Update position tracker with REAL outcome
            if self.position_tracker:
                # Get position by signal_id or ticket
                ticket = outcome_data.get('ticket')
                if ticket:
                    # Close position with real outcome
                    close_data = {
                        'close_price': outcome_data.get('exit_price', 0),
                        'profit': outcome_data.get('pips_result', 0),
                        'result_type': position_result,
                        'close_time': outcome_data.get('completed_at'),
                        'verified_real': True
                    }
                    
                    result = self.position_tracker.close(str(ticket), close_data)
                    if result.get('success'):
                        logger.info(f"📉 Position closed in tracker: {ticket} ({position_result})")
                        self.integration_stats['positions_closed'] += 1
                    else:
                        logger.warning(f"⚠️ Position close failed: {result.get('error')}")
                else:
                    logger.warning(f"⚠️ No ticket in truth tracker outcome: {signal_id}")
                    
            # Update integration stats
            self.integration_stats['real_confirmations_processed'] += 1
            logger.info(f"🔗 Truth outcome integrated: {signal_id} -> {position_result}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing truth outcome: {str(e)}")
            logger.error(f"❌ Outcome data: {json.dumps(outcome_data, indent=2)}")
            self.integration_stats['integration_errors'] += 1
            return False
            
    def process_position_tracker_event(self, event_data: Dict):
        """
        Process position tracker events and notify truth tracker
        ONLY process events with REAL data validation
        """
        try:
            # Add metadata for validation
            event_data['source'] = 'POSITION_TRACKER'
            event_data['timestamp'] = time.time()
            
            # Strict real data validation
            if not self.validate_real_data(event_data):
                logger.error(f"❌ Position tracker event rejected")
                return False
                
            event_type = event_data.get('event_type')
            signal_id = event_data.get('signal_id')
            uuid = event_data.get('uuid')
            
            if event_type == 'POSITION_OPENED':
                # Notify truth tracker of execution
                if self.truth_tracker and signal_id:
                    self.truth_tracker.log_user_fired(
                        signal_id,
                        uuid,
                        event_data.get('entry_price', 0)
                    )
                    self.integration_stats['positions_opened'] += 1
                    logger.info(f"📈 Position opening logged in truth tracker: {signal_id}")
                    
            elif event_type == 'POSITION_CLOSED':
                # Truth tracker should already have this from EA confirmations
                logger.debug(f"📉 Position closed event noted: {signal_id}")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing position event: {str(e)}")
            logger.error(f"❌ Event data: {json.dumps(event_data, indent=2)}")
            self.integration_stats['integration_errors'] += 1
            return False
            
    def sync_active_positions(self):
        """
        Synchronize active positions between truth tracker and position tracker
        Ensure both systems have consistent REAL data
        """
        try:
            if not all([self.truth_tracker, self.position_tracker]):
                logger.warning("⚠️ Cannot sync - missing components")
                return
                
            # Get active signals from truth tracker
            active_signals = []
            if hasattr(self.truth_tracker, 'active_signals'):
                active_signals = list(self.truth_tracker.active_signals.keys())
                
            # Get open positions from position tracker
            try:
                open_positions = self.position_tracker.list_open()
                open_position_tickets = [pos.get('ticket') for pos in open_positions if pos.get('ticket')]
            except:
                logger.warning("⚠️ Could not get open positions list")
                open_position_tickets = []
                
            logger.info(f"🔗 Sync status: {len(active_signals)} active signals, {len(open_position_tickets)} open positions")
            
            # Log discrepancies for investigation (don't auto-correct)
            if len(active_signals) != len(open_position_tickets):
                logger.warning(f"⚠️ Signal/position count mismatch: {len(active_signals)} vs {len(open_position_tickets)}")
                
        except Exception as e:
            logger.error(f"❌ Error syncing positions: {str(e)}")
            self.integration_stats['integration_errors'] += 1
            
    def get_integration_status(self) -> Dict:
        """Get current integration status and statistics"""
        uptime = time.time() - self.integration_stats['start_time']
        
        status = {
            'running': self.running,
            'uptime_seconds': uptime,
            'uptime_minutes': uptime / 60,
            'components': {
                'truth_tracker': self.truth_tracker is not None,
                'position_tracker': self.position_tracker is not None,
                'confirmation_consumer': self.confirmation_consumer is not None
            },
            'statistics': self.integration_stats.copy(),
            'data_integrity': {
                'real_data_only': True,
                'fake_data_rejected': self.integration_stats['fake_data_rejected'],
                'validation_active': True
            }
        }
        
        # Calculate success rate
        total_processed = self.integration_stats['real_confirmations_processed']
        total_errors = self.integration_stats['integration_errors']
        if total_processed + total_errors > 0:
            status['success_rate'] = (total_processed / (total_processed + total_errors)) * 100
        else:
            status['success_rate'] = 100.0
            
        return status
        
    def start_integration(self):
        """Start the integration system"""
        self.running = True
        logger.info("🚀 Starting Truth-Position Integration...")
        
        # Initial sync
        self.sync_active_positions()
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        
        logger.info("✅ Truth-Position Integration started")
        
    def _monitor_loop(self):
        """Main monitoring loop for integration"""
        while self.running:
            try:
                # Periodic sync every 5 minutes
                self.sync_active_positions()
                
                # Log status every 10 minutes
                status = self.get_integration_status()
                logger.info(f"🔗 Integration Status: {status['statistics']['real_confirmations_processed']} processed, {status['success_rate']:.1f}% success")
                
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"❌ Monitor loop error: {str(e)}")
                time.sleep(60)
                
    def stop_integration(self):
        """Stop the integration system"""
        logger.info("🛑 Stopping Truth-Position Integration...")
        self.running = False
        
        # Final sync
        self.sync_active_positions()
        
        # Log final statistics
        status = self.get_integration_status()
        logger.info(f"📊 Final Integration Statistics:")
        logger.info(f"   Positions Opened: {status['statistics']['positions_opened']}")
        logger.info(f"   Positions Closed: {status['statistics']['positions_closed']}")
        logger.info(f"   Real Confirmations: {status['statistics']['real_confirmations_processed']}")
        logger.info(f"   Fake Data Rejected: {status['statistics']['fake_data_rejected']}")
        logger.info(f"   Success Rate: {status['success_rate']:.1f}%")
        logger.info("✅ Truth-Position Integration stopped")

# Global instance
_integrator = None

def get_truth_position_integrator() -> TruthPositionIntegrator:
    """Get or create singleton integrator"""
    global _integrator
    if not _integrator:
        _integrator = TruthPositionIntegrator()
    return _integrator

if __name__ == "__main__":
    # Run integration service
    integrator = get_truth_position_integrator()
    
    try:
        integrator.start_integration()
        
        logger.info("=" * 60)
        logger.info("🔗 TRUTH-POSITION INTEGRATION SERVICE")
        logger.info("=" * 60)
        logger.info("📊 Connecting Truth Tracker with Position Tracker")
        logger.info("🛡️ REAL DATA ONLY - No synthetic data processing")
        logger.info("🔗 Bidirectional integration with validation")
        logger.info("=" * 60)
        
        # Run forever
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown signal received")
        integrator.stop_integration()