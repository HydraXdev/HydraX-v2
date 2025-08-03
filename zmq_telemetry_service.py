#!/usr/bin/env python3
"""
ZMQ Telemetry Ingestion Service
Monitors port 5556 for real-time telemetry and trade results
Integrates with XP system and risk management
"""

import zmq
import json
import logging
import time
from datetime import datetime
from typing import Dict, Optional
import threading
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TelemetryService')

class TelemetryIngestionService:
    """
    Service that subscribes to telemetry stream and processes account data
    """
    
    def __init__(self, telemetry_port=5556):
        self.telemetry_port = telemetry_port
        self.running = False
        
        # ZMQ setup
        self.context = zmq.Context()
        self.telemetry_socket = None
        
        # Data storage
        self.user_telemetry = {}  # uuid -> latest telemetry
        self.trade_results = []   # List of all trade results
        self.telemetry_history = defaultdict(list)  # uuid -> telemetry history
        
        # Stats
        self.stats = {
            'telemetry_received': 0,
            'trade_results_received': 0,
            'last_update': None,
            'active_users': set()
        }
        
        # Integration points
        self.xp_callback = None
        self.risk_callback = None
        self.trade_callback = None
        
        logger.info(f"Telemetry Service initialized on port {telemetry_port}")
        
    def start(self):
        """Start the telemetry ingestion service"""
        try:
            # Create PULL socket to receive telemetry
            self.telemetry_socket = self.context.socket(zmq.PULL)
            self.telemetry_socket.connect(f"tcp://localhost:{self.telemetry_port}")
            self.telemetry_socket.setsockopt(zmq.RCVTIMEO, 1000)
            
            logger.info(f"✅ Connected to telemetry stream on port {self.telemetry_port}")
            
            # Start ingestion thread
            self.running = True
            ingestion_thread = threading.Thread(target=self._ingestion_loop)
            ingestion_thread.start()
            
            # Start processing thread
            processing_thread = threading.Thread(target=self._processing_loop)
            processing_thread.start()
            
            logger.info("🚀 Telemetry ingestion service started")
            
        except Exception as e:
            logger.error(f"Failed to start telemetry service: {e}")
            self.stop()
            raise
            
    def stop(self):
        """Stop the telemetry service"""
        self.running = False
        
        if self.telemetry_socket:
            self.telemetry_socket.close()
            
        self.context.term()
        logger.info("Telemetry service stopped")
        
    def _ingestion_loop(self):
        """Main loop for receiving telemetry data"""
        logger.info("📡 Telemetry ingestion loop started")
        
        while self.running:
            try:
                # Receive message
                message = self.telemetry_socket.recv_string(zmq.NOBLOCK)
                
                # Parse JSON
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                
                # Update stats
                self.stats['last_update'] = datetime.now()
                
                # Route by message type
                if msg_type in ['telemetry', 'heartbeat']:
                    self._process_telemetry(data)
                elif msg_type == 'trade_result':
                    self._process_trade_result(data)
                elif msg_type == 'error':
                    self._process_error(data)
                elif msg_type == 'status':
                    self._process_status(data)
                else:
                    logger.warning(f"Unknown message type: {msg_type}")
                    
            except zmq.Again:
                # No message available
                pass
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse telemetry JSON: {e}")
            except Exception as e:
                logger.error(f"Telemetry ingestion error: {e}")
                
        logger.info("Telemetry ingestion loop stopped")
        
    def _process_telemetry(self, data: Dict):
        """Process telemetry update"""
        uuid = data.get('uuid', 'unknown')
        
        # Create telemetry object
        telemetry = {
            'uuid': uuid,
            'balance': float(data.get('balance', 0)),
            'equity': float(data.get('equity', 0)),
            'margin': float(data.get('margin', 0)),
            'free_margin': float(data.get('free_margin', 0)),
            'profit': float(data.get('profit', 0)),
            'positions': int(data.get('positions', 0)),
            'margin_level': float(data.get('margin_level', 0)),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store latest telemetry
        self.user_telemetry[uuid] = telemetry
        
        # Store history (keep last 100)
        self.telemetry_history[uuid].append(telemetry)
        if len(self.telemetry_history[uuid]) > 100:
            self.telemetry_history[uuid] = self.telemetry_history[uuid][-100:]
        
        # Update stats
        self.stats['telemetry_received'] += 1
        self.stats['active_users'].add(uuid)
        
        # Log significant changes
        if telemetry['profit'] != 0:
            icon = "📈" if telemetry['profit'] > 0 else "📉"
            logger.info(f"{icon} {uuid}: Balance=${telemetry['balance']:.2f}, "
                       f"P&L=${telemetry['profit']:.2f}")
        
        # Trigger risk callback if margin level is concerning
        if telemetry['margin_level'] > 0 and telemetry['margin_level'] < 150:
            logger.warning(f"⚠️ Low margin level for {uuid}: {telemetry['margin_level']:.2f}%")
            if self.risk_callback:
                self.risk_callback(uuid, telemetry)
                
    def _process_trade_result(self, data: Dict):
        """Process trade execution result"""
        result = {
            'signal_id': data.get('signal_id'),
            'status': data.get('status'),
            'ticket': data.get('ticket'),
            'price': data.get('price'),
            'message': data.get('message'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store result
        self.trade_results.append(result)
        if len(self.trade_results) > 1000:
            self.trade_results = self.trade_results[-1000:]
        
        # Update stats
        self.stats['trade_results_received'] += 1
        
        # Log result
        if result['status'] == 'success':
            logger.info(f"✅ Trade executed: {result['signal_id']} - "
                       f"Ticket {result['ticket']} @ {result['price']}")
            
            # Award XP for successful trade
            if self.xp_callback:
                self.xp_callback(result['signal_id'], 'trade_success', 5)
        else:
            logger.error(f"❌ Trade failed: {result['signal_id']} - {result['message']}")
            
        # Trigger trade callback
        if self.trade_callback:
            self.trade_callback(result)
            
    def _process_error(self, data: Dict):
        """Process error message"""
        signal_id = data.get('signal_id', '')
        error = data.get('error', 'Unknown error')
        
        logger.error(f"❌ EA Error for {signal_id}: {error}")
        
        # Store as failed trade result
        result = {
            'signal_id': signal_id,
            'status': 'error',
            'message': error,
            'timestamp': datetime.now().isoformat()
        }
        self.trade_results.append(result)
        
    def _process_status(self, data: Dict):
        """Process status message"""
        status = data.get('status', '')
        message = data.get('message', '')
        
        if status == 'startup':
            logger.info(f"🚀 EA connected: {message}")
        elif status == 'shutdown':
            logger.info(f"👋 EA disconnecting: {message}")
        else:
            logger.info(f"📊 EA Status: {status} - {message}")
            
    def _processing_loop(self):
        """Background processing loop for derived metrics"""
        logger.info("⚙️ Processing loop started")
        
        while self.running:
            try:
                # Calculate user metrics every 30 seconds
                for uuid, telemetry in self.user_telemetry.items():
                    history = self.telemetry_history.get(uuid, [])
                    if len(history) >= 2:
                        # Calculate performance metrics
                        start_balance = history[0]['balance']
                        current_balance = telemetry['balance']
                        
                        if start_balance > 0:
                            return_pct = ((current_balance - start_balance) / start_balance) * 100
                            
                            # Award XP based on performance
                            if return_pct > 5 and self.xp_callback:
                                self.xp_callback(uuid, 'performance_milestone', 10)
                                logger.info(f"🏆 {uuid} achieved {return_pct:.1f}% return!")
                
                # Sleep for 30 seconds
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Processing loop error: {e}")
                time.sleep(5)
                
        logger.info("Processing loop stopped")
        
    # Integration methods
    
    def set_xp_callback(self, callback):
        """Set callback for XP awards"""
        self.xp_callback = callback
        
    def set_risk_callback(self, callback):
        """Set callback for risk alerts"""
        self.risk_callback = callback
        
    def set_trade_callback(self, callback):
        """Set callback for trade results"""
        self.trade_callback = callback
        
    def get_user_telemetry(self, uuid: str) -> Optional[Dict]:
        """Get latest telemetry for a user"""
        return self.user_telemetry.get(uuid)
        
    def get_all_telemetry(self) -> Dict:
        """Get telemetry for all users"""
        return self.user_telemetry.copy()
        
    def get_trade_results(self, limit: int = 10) -> list:
        """Get recent trade results"""
        return self.trade_results[-limit:]
        
    def get_stats(self) -> Dict:
        """Get service statistics"""
        return {
            **self.stats,
            'active_users_count': len(self.stats['active_users']),
            'total_users': len(self.user_telemetry)
        }
        
# Integration with existing systems

def integrate_with_xp_system():
    """Connect telemetry to XP system"""
    try:
        from src.bitten_core.xp_manager import award_xp
        
        def xp_callback(user_id: str, reason: str, amount: int):
            """Award XP based on telemetry events"""
            try:
                # Convert uuid to telegram_id if needed
                if user_id.startswith('mt5_'):
                    # Extract telegram_id from container name
                    telegram_id = user_id.split('_')[-1]
                else:
                    telegram_id = user_id
                    
                award_xp(telegram_id, amount, reason)
                logger.info(f"🎖️ Awarded {amount} XP to {telegram_id} for {reason}")
                
            except Exception as e:
                logger.error(f"Failed to award XP: {e}")
                
        return xp_callback
        
    except ImportError:
        logger.warning("XP system not available")
        return None
        
def integrate_with_risk_system():
    """Connect telemetry to risk management"""
    try:
        from src.bitten_core.risk_manager import check_margin_call
        
        def risk_callback(user_id: str, telemetry: Dict):
            """Check risk based on telemetry"""
            try:
                margin_level = telemetry.get('margin_level', 0)
                if margin_level > 0 and margin_level < 100:
                    check_margin_call(user_id, margin_level)
                    logger.warning(f"🚨 Margin call risk for {user_id}: {margin_level}%")
                    
            except Exception as e:
                logger.error(f"Failed to check risk: {e}")
                
        return risk_callback
        
    except ImportError:
        logger.warning("Risk system not available")
        return None

# Main service runner

def main():
    """Run telemetry ingestion service"""
    service = TelemetryIngestionService()
    
    # Set up integrations
    xp_callback = integrate_with_xp_system()
    if xp_callback:
        service.set_xp_callback(xp_callback)
        
    risk_callback = integrate_with_risk_system()
    if risk_callback:
        service.set_risk_callback(risk_callback)
    
    try:
        service.start()
        
        print("\n" + "="*60)
        print("ZMQ Telemetry Ingestion Service")
        print("="*60)
        print(f"Monitoring port: {service.telemetry_port}")
        print("Integrations:")
        print(f"  - XP System: {'✅' if xp_callback else '❌'}")
        print(f"  - Risk Management: {'✅' if risk_callback else '❌'}")
        print("="*60)
        print("\nPress Ctrl+C to stop")
        
        while True:
            time.sleep(5)
            stats = service.get_stats()
            print(f"\r📊 Stats: {stats['telemetry_received']} telemetry, "
                  f"{stats['trade_results_received']} trades, "
                  f"{stats['active_users_count']} active users", end='')
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        service.stop()
        print("✅ Service stopped")

if __name__ == "__main__":
    main()