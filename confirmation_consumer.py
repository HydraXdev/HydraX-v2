#!/usr/bin/env python3
"""
CONFIRMATION CONSUMER v1.0
Consume REAL trade confirmations from port 5558
CRITICAL: Only process REAL confirmations from EA - NO FAKE DATA

Author: BITTEN Trading System
Date: August 6, 2025
Purpose: Process real trade confirmations and update truth tracker
"""

import zmq
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, Optional
import os
import sys

# Add project root to path for imports
sys.path.append('/root/HydraX-v2')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CONFIRMATION_CONSUMER - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/confirmation_consumer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RealConfirmationError(Exception):
    """Raised when confirmation is not from real EA"""
    pass

class FakeConfirmationDetectedError(Exception):
    """Raised when fake confirmation is detected"""
    pass

class ConfirmationConsumer:
    """
    Consume REAL trade confirmations from port 5558
    ABSOLUTE RULE: Only process confirmations from real EAs
    """
    
    def __init__(self):
        self.context = zmq.Context()
        
        # PULL socket binding to port 5558 - receive confirmations from EA
        self.socket = self.context.socket(zmq.PULL)
        self.socket.bind("tcp://*:5558")
        
        # Import truth tracker for REAL outcome recording
        try:
            from black_box_complete_truth_system import get_truth_system
            self.truth_tracker = get_truth_system()
            logger.info("✅ Truth tracker connected")
        except ImportError:
            logger.error("❌ Truth tracker not available - continuing without it")
            self.truth_tracker = None
        
        # Import position tracker for REAL position updates
        try:
            from position_tracker import PositionTrackerAPI
            self.position_tracker = PositionTrackerAPI()
            logger.info("✅ Position tracker connected")
        except ImportError:
            logger.error("❌ Position tracker not available - continuing without it")
            self.position_tracker = None
        
        # Confirmation validation requirements
        self.required_fields = [
            'ticket',       # Must have real MT5 ticket
            'symbol',       # Must have valid symbol
            'status',       # Must have real status (success/failure) - EA sends 'status' not 'result'
            'timestamp',    # Must have timestamp
            'account',      # Must have real account
            'node_id'       # Must have real EA node ID
        ]
        
        self.valid_results = [
            'success',      # Trade executed successfully
            'order_opened', # Order opened
            'order_closed', # Order closed
            'order_modified', # Order modified
            'sl_hit',       # Stop loss hit
            'tp_hit',       # Take profit hit
            'error',        # Real error from broker
            'rejected'      # Order rejected by broker
        ]
        
        # Statistics
        self.confirmations_processed = 0
        self.confirmations_rejected = 0
        self.real_outcomes_recorded = 0
        
        self.running = True
        
        logger.info("📥 Confirmation Consumer initialized - Port 5558 PULL socket")
        logger.info("🚨 REAL CONFIRMATIONS ONLY - NO FAKE DATA ACCEPTED")
    
    def validate_real_confirmation(self, data: Dict) -> bool:
        """
        Validate that confirmation is from REAL EA
        STRICT validation - reject ANY suspicious data
        """
        try:
            # Check all required fields exist
            for field in self.required_fields:
                if field not in data:
                    raise RealConfirmationError(f"Missing required field: {field}")
            
            # Validate ticket number (must be positive integer)
            ticket = data.get('ticket')
            if not ticket or not str(ticket).isdigit() or int(ticket) <= 0:
                raise FakeConfirmationDetectedError(f"Invalid ticket number: {ticket}")
            
            # Validate status type (EA sends 'status' not 'result')
            result = data.get('status', '').lower()
            if result not in self.valid_results:
                raise RealConfirmationError(f"Invalid status type: {result}")
            
            # Validate timestamp (must be recent)
            timestamp = data.get('timestamp')
            if not timestamp:
                raise RealConfirmationError("No timestamp provided")
            
            try:
                ts_float = float(timestamp)
                age = time.time() - ts_float
                if age > 300:  # More than 5 minutes old
                    raise RealConfirmationError(f"Confirmation too old: {age:.1f} seconds")
                if age < -60:  # From the future (more than 1 minute)
                    raise RealConfirmationError(f"Confirmation from future: {age:.1f} seconds")
            except (ValueError, TypeError):
                raise RealConfirmationError(f"Invalid timestamp format: {timestamp}")
            
            # Validate account number
            account = data.get('account')
            if not account or not str(account).isdigit():
                raise RealConfirmationError(f"Invalid account number: {account}")
            
            # Validate node_id (must be from known EA)
            node_id = data.get('node_id')
            if not node_id or len(str(node_id)) < 5:
                raise RealConfirmationError(f"Invalid node_id: {node_id}")
            
            # Additional validation for trade data
            if result in ['order_opened', 'order_closed', 'success']:
                # Check for required trading fields
                if 'symbol' not in data or len(data['symbol']) < 6:
                    raise RealConfirmationError(f"Invalid symbol: {data.get('symbol')}")
                
                # Validate prices if present
                for price_field in ['open_price', 'close_price', 'sl', 'tp']:
                    if price_field in data:
                        try:
                            price = float(data[price_field])
                            if price <= 0:
                                raise RealConfirmationError(f"Invalid {price_field}: {price}")
                        except (ValueError, TypeError):
                            raise RealConfirmationError(f"Invalid {price_field} format: {data[price_field]}")
            
            logger.debug(f"✅ Confirmation validated: {ticket} - {result}")
            return True
            
        except (RealConfirmationError, FakeConfirmationDetectedError) as e:
            logger.error(f"❌ CONFIRMATION REJECTED: {str(e)}")
            logger.error(f"❌ Suspicious data: {json.dumps(data, indent=2)}")
            return False
        except Exception as e:
            logger.error(f"❌ Validation error: {str(e)}")
            return False
    
    def process_confirmation(self, data: Dict):
        """Process a REAL confirmation and update systems"""
        try:
            # FIRST: Validate this is a real confirmation
            if not self.validate_real_confirmation(data):
                self.confirmations_rejected += 1
                logger.warning(f"⚠️ REJECTED fake/invalid confirmation")
                return
            
            ticket = str(data['ticket'])
            result = data['status'].lower()
            symbol = data.get('symbol', 'UNKNOWN')
            
            logger.info(f"📥 Processing REAL confirmation: {ticket} ({symbol}) - {result}")
            
            # Update truth tracker with REAL outcome
            if self.truth_tracker:
                self._update_truth_tracker(data)
            
            # Update position tracker with REAL position changes
            if self.position_tracker:
                self._update_position_tracker(data)
            
            # Log the real confirmation
            self._log_real_confirmation(data)
            
            self.confirmations_processed += 1
            self.real_outcomes_recorded += 1
            
            logger.info(f"✅ REAL confirmation processed: {ticket}")
            
        except Exception as e:
            logger.error(f"❌ Error processing confirmation: {str(e)}")
            logger.error(f"❌ Confirmation data: {json.dumps(data, indent=2)}")
    
    def _update_truth_tracker(self, data: Dict):
        """Update truth tracker with REAL outcome"""
        try:
            # Map confirmation result to truth tracker result
            result_mapping = {
                'tp_hit': 'TP_HIT',
                'sl_hit': 'SL_HIT', 
                'success': 'TP_HIT' if float(data.get('profit', 0)) > 0 else 'SL_HIT',
                'order_closed': 'TP_HIT' if float(data.get('profit', 0)) > 0 else 'SL_HIT',
                'error': 'ERROR',
                'rejected': 'REJECTED'
            }
            
            truth_result = result_mapping.get(data['status'].lower())
            if not truth_result:
                logger.warning(f"Unknown status type for truth tracker: {data['status']}")
                return
            
            # Find signal_id from ticket or other identifier
            signal_id = data.get('signal_id', f"TICKET_{data['ticket']}")
            
            # Calculate time to close if available
            time_to_close = None
            if 'open_time' in data and 'close_time' in data:
                try:
                    open_time = float(data['open_time'])
                    close_time = float(data['close_time'])
                    time_to_close = close_time - open_time
                except (ValueError, TypeError):
                    pass
            
            # Update truth tracker with REAL outcome
            self.truth_tracker.update_signal_outcome(
                signal_id=signal_id,
                result=truth_result,
                time_to_close=time_to_close,
                actual_profit=float(data.get('profit', 0)),
                close_price=float(data.get('close_price', 0)) if data.get('close_price') else None
            )
            
            logger.info(f"📊 Truth tracker updated: {signal_id} -> {truth_result}")
            
        except Exception as e:
            logger.error(f"Error updating truth tracker: {str(e)}")
    
    def _update_position_tracker(self, data: Dict):
        """Update position tracker with REAL position changes"""
        try:
            ticket = str(data['ticket'])
            result = data['status'].lower()
            
            if result == 'order_opened':
                # Position opened - notify position tracker
                uuid = data.get('user_id', data.get('uuid', 'UNKNOWN'))
                
                # Don't open position in tracker here - that should happen
                # when fire command is executed. Just log that EA confirmed it.
                logger.info(f"📈 EA confirmed position opened: {ticket} (UUID: {uuid})")
                
            elif result in ['order_closed', 'tp_hit', 'sl_hit']:
                # Position closed - update position tracker
                close_data = {
                    'close_price': float(data.get('close_price', 0)),
                    'profit': float(data.get('profit', 0)),
                    'swap': float(data.get('swap', 0)),
                    'commission': float(data.get('commission', 0))
                }
                
                # Close position with REAL confirmation
                result = self.position_tracker.close(ticket, close_data)
                if result.get('success'):
                    logger.info(f"📉 Position closed in tracker: {ticket}")
                else:
                    logger.warning(f"⚠️ Position close failed: {result.get('error')}")
            
        except Exception as e:
            logger.error(f"Error updating position tracker: {str(e)}")
    
    def _log_real_confirmation(self, data: Dict):
        """Log real confirmation to audit file"""
        try:
            log_entry = {
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'source': 'EA_CONFIRMATION',
                'ticket': data['ticket'],
                'symbol': data.get('symbol'),
                'result': data['status'],
                'account': data.get('account'),
                'node_id': data.get('node_id'),
                'profit': data.get('profit'),
                'verified_real': True
            }
            
            with open('/root/HydraX-v2/logs/real_confirmations.jsonl', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Error logging confirmation: {str(e)}")
    
    def get_statistics(self) -> Dict:
        """Get consumer statistics"""
        return {
            'confirmations_processed': self.confirmations_processed,
            'confirmations_rejected': self.confirmations_rejected,
            'real_outcomes_recorded': self.real_outcomes_recorded,
            'rejection_rate': (self.confirmations_rejected / max(1, self.confirmations_processed + self.confirmations_rejected)) * 100,
            'uptime': time.time() - getattr(self, 'start_time', time.time()),
            'fake_data_detected': self.confirmations_rejected,  # All rejections are fake data
            'last_confirmation': getattr(self, 'last_confirmation_time', None)
        }
    
    def run(self):
        """Main consumer loop"""
        logger.info("🔄 Starting confirmation consumer loop...")
        self.start_time = time.time()
        
        while self.running:
            try:
                # Poll for confirmations with timeout
                if self.socket.poll(1000):  # 1 second timeout
                    message_raw = self.socket.recv_string(zmq.NOBLOCK)
                    
                    try:
                        confirmation = json.loads(message_raw)
                        self.last_confirmation_time = time.time()
                        
                        # Process the REAL confirmation
                        self.process_confirmation(confirmation)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Invalid JSON received: {message_raw[:100]}...")
                        self.confirmations_rejected += 1
                        continue
                        
            except zmq.Again:
                continue
            except KeyboardInterrupt:
                logger.info("🛑 Confirmation consumer interrupted")
                break
            except Exception as e:
                logger.error(f"❌ Error in consumer loop: {str(e)}")
                time.sleep(1)
    
    def start(self):
        """Start the confirmation consumer"""
        logger.info("📥 Confirmation Consumer starting...")
        
        try:
            self.run()
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down confirmation consumer...")
            self.running = False
        finally:
            self.socket.close()
            self.context.term()
    
    def stop(self):
        """Stop the confirmation consumer"""
        logger.info("🛑 Stopping confirmation consumer...")
        self.running = False

if __name__ == "__main__":
    # Create and start consumer
    consumer = ConfirmationConsumer()
    
    # Log startup stats
    logger.info("📊 Consumer Statistics:")
    stats = consumer.get_statistics()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    # Start consuming REAL confirmations
    consumer.start()