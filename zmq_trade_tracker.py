#!/usr/bin/env python3
"""
ZMQ Trade Tracker - Track and log all confirmed trades
Records trade results in trade_log.json for analysis
"""

# ┌──────────────────────────────────────────────────────────────┐
# │ BITTEN ZMQ SYSTEM - DO NOT FALL BACK TO FILE/HTTP ROUTES    │
# │ Persistent ZMQ architecture is required                      │
# │ EA v7 connects directly via libzmq.dll to 134.199.204.67    │
# │ All command, telemetry, and feedback must use ZMQ sockets   │
# └──────────────────────────────────────────────────────────────┘

import zmq
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TradeTracker')

class ZMQTradeTracker:
    """
    Monitors ZMQ feedback channel for trade results and logs them
    """
    
    def __init__(self, feedback_port=5556):
        self.feedback_port = feedback_port
        self.running = False
        
        # ZMQ setup
        self.context = zmq.Context()
        self.feedback_socket = None
        
        # Trade log file
        self.trade_log_file = Path("/root/HydraX-v2/logs/zmq_trade_log.json")
        self.trade_log_file.parent.mkdir(exist_ok=True)
        
        # In-memory trade history
        self.trades = []
        self.load_existing_trades()
        
        logger.info(f"🧠 ZMQ Trade Tracker initialized - File fallback disabled")
        
    def load_existing_trades(self):
        """Load existing trades from log file"""
        if self.trade_log_file.exists():
            try:
                with open(self.trade_log_file, 'r') as f:
                    self.trades = json.load(f)
                logger.info(f"📜 Loaded {len(self.trades)} existing trades")
            except Exception as e:
                logger.error(f"Failed to load trade log: {e}")
                self.trades = []
                
    def save_trades(self):
        """Save trades to log file"""
        try:
            with open(self.trade_log_file, 'w') as f:
                json.dump(self.trades, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save trade log: {e}")
            
    def start(self):
        """Start monitoring for trade results"""
        try:
            # Connect to feedback channel
            self.feedback_socket = self.context.socket(zmq.SUB)
            self.feedback_socket.connect(f"tcp://localhost:{self.feedback_port}")
            self.feedback_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            self.feedback_socket.setsockopt(zmq.RCVTIMEO, 1000)
            
            logger.info(f"📡 Connected to ZMQ feedback on port {self.feedback_port}")
            
            self.running = True
            monitor_thread = threading.Thread(target=self._monitor_loop)
            monitor_thread.start()
            
            logger.info("🚀 Trade tracking started")
            
        except Exception as e:
            logger.error(f"Failed to start tracker: {e}")
            self.stop()
            
    def stop(self):
        """Stop the tracker"""
        self.running = False
        
        if self.feedback_socket:
            self.feedback_socket.close()
            
        self.context.term()
        self.save_trades()
        logger.info("Trade tracker stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("📊 Monitoring for trade results...")
        
        while self.running:
            try:
                message = self.feedback_socket.recv_string()
                data = json.loads(message)
                
                # Process trade results
                if data.get('type') == 'trade_result':
                    self._process_trade_result(data)
                    
            except zmq.Again:
                # No message, continue
                pass
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                
    def _process_trade_result(self, result: Dict):
        """Process and log a trade result"""
        signal_id = result.get('signal_id', 'unknown')
        status = result.get('status', 'unknown')
        
        # Create trade record
        trade_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "signal_id": signal_id,
            "status": status,
            "ticket": result.get('ticket', 0),
            "price": result.get('price', 0),
            "message": result.get('message', ''),
            "uuid": result.get('uuid', ''),
            "symbol": result.get('symbol', ''),
            "action": result.get('action', ''),
            "lot": result.get('lot', 0),
            "sl": result.get('sl', 0),
            "tp": result.get('tp', 0)
        }
        
        # Add account info if available
        if 'account' in result:
            trade_record['account'] = result['account']
            
        # Log the trade
        self.trades.append(trade_record)
        
        # Keep only last 1000 trades in memory
        if len(self.trades) > 1000:
            self.trades = self.trades[-1000:]
            
        # Save to file
        self.save_trades()
        
        # Log status
        if status == 'success':
            logger.info(f"✅ Trade confirmed: {signal_id} - Ticket {trade_record['ticket']}")
        else:
            logger.error(f"❌ Trade failed: {signal_id} - {result.get('message', 'Unknown error')}")
            
        # Display summary
        self._display_summary()
        
    def _display_summary(self):
        """Display trading summary"""
        total_trades = len(self.trades)
        successful = sum(1 for t in self.trades if t['status'] == 'success')
        failed = total_trades - successful
        
        if total_trades > 0:
            success_rate = (successful / total_trades) * 100
            logger.info(f"📊 Summary: {total_trades} trades | "
                       f"✅ {successful} ({success_rate:.1f}%) | "
                       f"❌ {failed}")
            
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent trades"""
        return self.trades[-limit:]
        
    def get_stats(self) -> Dict:
        """Get trading statistics"""
        total = len(self.trades)
        successful = sum(1 for t in self.trades if t['status'] == 'success')
        
        return {
            "total_trades": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "last_trade": self.trades[-1] if self.trades else None
        }

def main():
    """Run the trade tracker"""
    tracker = ZMQTradeTracker()
    
    try:
        tracker.start()
        
        print("=" * 60)
        print("ZMQ Trade Tracker - Monitoring all confirmed trades")
        print("=" * 60)
        print("📡 Connected to ZMQ feedback channel")
        print("📜 Logging trades to: logs/zmq_trade_log.json")
        print("=" * 60)
        
        # Keep running
        while True:
            time.sleep(30)
            
            # Show periodic stats
            stats = tracker.get_stats()
            if stats['total_trades'] > 0:
                print(f"\n📊 Stats: {stats['total_trades']} trades | "
                      f"Success rate: {stats['success_rate']:.1f}%")
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        tracker.stop()
        print("✅ Trade tracker stopped")

if __name__ == "__main__":
    main()