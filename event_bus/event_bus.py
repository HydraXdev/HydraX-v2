#!/usr/bin/env python3
"""
Outcome Mirrorer - Phase A Implementation
Mirrors trade outcomes to event bus while preserving ZMQ hot path

Listens to:
1. ZMQ:5558 confirmations from EA 
2. JSONL outcome records (for backfill and current outcomes)

Publishes to:
Event Bus with execution.outcome.v1 schema
"""

import zmq
import json
import sqlite3
import time
import logging
from datetime import datetime
from typing import Dict, Optional
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [OUTCOME_MIRROR] %(message)s")
logger = logging.getLogger("OUTCOME_MIRROR")

class OutcomeMirrorer:
    """Mirrors outcomes from ZMQ + JSONL to Event Bus"""
    
    def __init__(self):
        # ZMQ setup for confirmations
        self.context = zmq.Context()
        self.confirmation_socket = self.context.socket(zmq.SUB)
        self.confirmation_socket.connect("tcp://localhost:5558")
        self.confirmation_socket.setsockopt_string(zmq.SUBSCRIBE, "")
        
        # Event bus database
        self.event_db_path = '/root/HydraX-v2/event_bus/bitten_events.db'
        self.main_db_path = '/root/HydraX-v2/bitten.db'
        
        # Track processed outcomes for idempotency
        self.processed_outcomes = set()
        
        logger.info("✅ Outcome Mirrorer initialized")
        
    def generate_trade_id(self, fire_id: str, ticket: Optional[int] = None) -> str:
        """Generate deterministic trade_id for idempotency"""
        if ticket:
            return f"mt5:{ticket}"
        return f"fire:{fire_id}"
    
    def publish_outcome_event(self, outcome_data: Dict):
        """Publish execution.outcome.v1 event to event bus"""
        try:
            # Generate deterministic trade_id
            trade_id = self.generate_trade_id(
                outcome_data.get('fire_id', outcome_data.get('signal_id', 'unknown')),
                outcome_data.get('ticket')
            )
            
            # Check for idempotency
            if trade_id in self.processed_outcomes:
                logger.debug(f"Skipping duplicate outcome: {trade_id}")
                return
            
            # Create execution.outcome.v1 event
            event_data = {
                "trade_id": trade_id,
                "signal_id": outcome_data.get('signal_id'),
                "fire_id": outcome_data.get('fire_id'),
                "symbol": outcome_data.get('symbol'),
                "direction": outcome_data.get('direction'),
                "result": outcome_data.get('outcome', outcome_data.get('status', 'unknown')),
                "pnl_pips": outcome_data.get('pips_result', 0),
                "entry_price": outcome_data.get('entry_price'),
                "exit_price": outcome_data.get('exit_price'),
                "duration_minutes": outcome_data.get('tracking_duration_minutes'),
                "pattern_type": outcome_data.get('pattern_type'),
                "confidence": outcome_data.get('confidence'),
                "source": outcome_data.get('source', 'unknown'),
                "schema_version": 1
            }
            
            # Insert into event bus
            conn = sqlite3.connect(self.event_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO events (
                    event_type, timestamp, source, correlation_id, 
                    user_id, data_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'execution.outcome.v1',
                time.time(),
                outcome_data.get('source', 'outcome_mirrorer'),
                trade_id,
                outcome_data.get('user_id'),
                json.dumps(event_data),
                time.time()
            ))
            
            conn.commit()
            conn.close()
            
            # Mark as processed
            self.processed_outcomes.add(trade_id)
            
            logger.info(f"📊 Published outcome: {trade_id} - {event_data['result']} - {event_data['pnl_pips']} pips")
            
        except Exception as e:
            logger.error(f"❌ Failed to publish outcome: {e}")
    
    def process_zmq_confirmation(self, message: bytes):
        """Process ZMQ confirmation from port 5558"""
        try:
            data = json.loads(message.decode('utf-8'))
            
            # Map ZMQ confirmation to outcome format
            outcome_data = {
                'fire_id': data.get('fire_id'),
                'signal_id': data.get('signal_id'),
                'symbol': data.get('symbol'),
                'direction': data.get('direction'),
                'status': data.get('status'),
                'ticket': data.get('ticket'),
                'entry_price': data.get('price'),
                'source': 'zmq_confirmation'
            }
            
            # Only process filled orders for now
            if data.get('status', '').upper() in ['FILLED', 'SUCCESS', 'OK']:
                self.publish_outcome_event(outcome_data)
                
        except Exception as e:
            logger.error(f"❌ Failed to process ZMQ confirmation: {e}")
    
    def process_jsonl_outcome(self, line: str):
        """Process outcome from JSONL file"""
        try:
            data = json.loads(line)
            
            if data.get('type') == 'outcome_recorded':
                outcome_data = {
                    'signal_id': data.get('signal_id'),
                    'symbol': data.get('symbol'),
                    'direction': data.get('direction'),
                    'outcome': data.get('outcome'),
                    'pips_result': data.get('pips_result'),
                    'exit_price': data.get('exit_price'),
                    'tracking_duration_minutes': data.get('tracking_duration_minutes'),
                    'pattern_type': data.get('pattern_type'),
                    'confidence': data.get('confidence'),
                    'source': 'jsonl_outcome'
                }
                
                self.publish_outcome_event(outcome_data)
                
        except Exception as e:
            logger.error(f"❌ Failed to process JSONL outcome: {e}")
    
    def backfill_historical_outcomes(self):
        """Backfill historical JSONL outcomes to event bus"""
        logger.info("🔄 Starting historical outcome backfill...")
        
        jsonl_files = [
            '/root/HydraX-v2/dynamic_tracking.jsonl',
            '/root/HydraX-v2/comprehensive_tracking.jsonl'
        ]
        
        backfill_count = 0
        for filepath in jsonl_files:
            if not os.path.exists(filepath):
                continue
                
            logger.info(f"📂 Processing {filepath}")
            try:
                with open(filepath, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and '"type": "outcome_recorded"' in line:
                            data = json.loads(line)
                            outcome_data = {
                                'signal_id': data.get('signal_id'),
                                'symbol': data.get('symbol'),
                                'direction': data.get('direction'),
                                'outcome': data.get('outcome'),
                                'pips_result': data.get('pips_result'),
                                'exit_price': data.get('exit_price'),
                                'tracking_duration_minutes': data.get('tracking_duration_minutes'),
                                'pattern_type': data.get('pattern_type'),
                                'confidence': data.get('confidence'),
                                'source': 'jsonl-backfill'
                            }
                            
                            self.publish_outcome_event(outcome_data)
                            backfill_count += 1
                            
            except Exception as e:
                logger.error(f"❌ Backfill failed for {filepath}: {e}")
        
        logger.info(f"✅ Backfill complete: {backfill_count} outcomes processed")
        
    def run(self):
        """Main loop - listen to ZMQ confirmations and mirror to event bus"""
        logger.info("🚀 Starting Outcome Mirrorer main loop")
        
        # First, backfill historical data
        self.backfill_historical_outcomes()
        
        # Then start real-time mirroring
        logger.info("👂 Listening for real-time confirmations on ZMQ:5558")
        
        while True:
            try:
                # Check for ZMQ messages (non-blocking)
                try:
                    message = self.confirmation_socket.recv(zmq.NOBLOCK)
                    self.process_zmq_confirmation(message)
                except zmq.Again:
                    pass
                
                # Also check for new JSONL entries (simple tail approach)
                # In production, you might want to use file watching
                
                time.sleep(1)  # Avoid busy loop
                
            except KeyboardInterrupt:
                logger.info("🛑 Shutdown requested")
                break
            except Exception as e:
                logger.error(f"❌ Main loop error: {e}")
                time.sleep(5)  # Backoff on error
        
        self.context.term()
        logger.info("✅ Outcome Mirrorer stopped")

def main():
    mirrorer = OutcomeMirrorer()
    mirrorer.run()

if __name__ == "__main__":
    main()