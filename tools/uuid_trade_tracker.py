#!/usr/bin/env python3
"""
🔗 UUID TRADE TRACKER
Complete trade tracing with unique identifiers for BITTEN Fire Loop Validation System
"""

import uuid
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class UUIDTradeTracker:
    """Track trades with unique identifiers from signal to execution"""
    
    def __init__(self):
        # Database file for UUID tracking
        self.tracking_db_path = Path("/root/HydraX-v2/data/uuid_trade_tracking.json")
        self.tracking_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database if it doesn't exist
        if not self.tracking_db_path.exists():
            self.save_tracking_data({
                "trades": {},
                "signals": {},
                "executions": {},
                "stats": {
                    "total_trades": 0,
                    "completed_loops": 0,
                    "failed_loops": 0,
                    "avg_loop_time": 0
                }
            })
        
        print("🔗 UUID TRADE TRACKER INITIALIZED")
        print(f"📊 Database: {self.tracking_db_path}")
        print("=" * 60)
    
    def load_tracking_data(self) -> Dict:
        """Load UUID tracking data from database"""
        try:
            with open(self.tracking_db_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading tracking data: {e}")
            return {"trades": {}, "signals": {}, "executions": {}, "stats": {}}
    
    def save_tracking_data(self, data: Dict):
        """Save UUID tracking data to database"""
        try:
            with open(self.tracking_db_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving tracking data: {e}")
    
    def generate_trade_uuid(self, signal_type: str = "UNKNOWN", symbol: str = "UNKNOWN") -> str:
        """Generate unique trade UUID"""
        # Create UUID with timestamp and signal info
        base_uuid = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Format: SIGNAL_SYMBOL_TIMESTAMP_UUID
        trade_uuid = f"{signal_type}_{symbol}_{timestamp}_{base_uuid[:8]}"
        
        return trade_uuid
    
    def track_signal_generation(self, signal_data: Dict) -> str:
        """Track signal generation and return UUID"""
        trade_uuid = self.generate_trade_uuid(
            signal_data.get("signal_type", "UNKNOWN"),
            signal_data.get("symbol", "UNKNOWN")
        )
        
        # Load current tracking data
        tracking_data = self.load_tracking_data()
        
        # Record signal generation
        signal_record = {
            "trade_uuid": trade_uuid,
            "signal_data": signal_data,
            "timestamp": datetime.utcnow().isoformat(),
            "stage": "signal_generated",
            "tcs_score": signal_data.get("tcs_score", 0),
            "user_id": signal_data.get("user_id", "unknown")
        }
        
        tracking_data["signals"][trade_uuid] = signal_record
        tracking_data["trades"][trade_uuid] = {
            "trade_uuid": trade_uuid,
            "stages": ["signal_generated"],
            "start_time": datetime.utcnow().isoformat(),
            "current_stage": "signal_generated",
            "status": "active"
        }
        
        # Update stats
        tracking_data["stats"]["total_trades"] += 1
        
        self.save_tracking_data(tracking_data)
        
        print(f"🔗 Signal tracked: {trade_uuid}")
        print(f"📊 Symbol: {signal_data.get('symbol', 'UNKNOWN')}")
        print(f"🎯 TCS: {signal_data.get('tcs_score', 0)}%")
        
        return trade_uuid
    
    def track_file_relay(self, trade_uuid: str, file_path: str, relay_type: str = "troll_relay"):
        """Track file relay stage"""
        tracking_data = self.load_tracking_data()
        
        if trade_uuid not in tracking_data["trades"]:
            print(f"❌ UUID not found: {trade_uuid}")
            return
        
        # Update trade record
        tracking_data["trades"][trade_uuid]["stages"].append(relay_type)
        tracking_data["trades"][trade_uuid]["current_stage"] = relay_type
        tracking_data["trades"][trade_uuid]["file_path"] = file_path
        tracking_data["trades"][trade_uuid]["relay_timestamp"] = datetime.utcnow().isoformat()
        
        self.save_tracking_data(tracking_data)
        
        print(f"📁 File relay tracked: {trade_uuid}")
        print(f"📄 File: {file_path}")
    
    def track_ea_detection(self, trade_uuid: str, ea_log_entry: str):
        """Track EA signal detection"""
        tracking_data = self.load_tracking_data()
        
        if trade_uuid not in tracking_data["trades"]:
            print(f"❌ UUID not found: {trade_uuid}")
            return
        
        # Update trade record
        tracking_data["trades"][trade_uuid]["stages"].append("ea_detected")
        tracking_data["trades"][trade_uuid]["current_stage"] = "ea_detected"
        tracking_data["trades"][trade_uuid]["ea_log"] = ea_log_entry
        tracking_data["trades"][trade_uuid]["ea_timestamp"] = datetime.utcnow().isoformat()
        
        self.save_tracking_data(tracking_data)
        
        print(f"🤖 EA detection tracked: {trade_uuid}")
        print(f"📝 Log: {ea_log_entry[:50]}...")
    
    def track_trade_execution(self, trade_uuid: str, execution_result: Dict):
        """Track trade execution result"""
        tracking_data = self.load_tracking_data()
        
        if trade_uuid not in tracking_data["trades"]:
            print(f"❌ UUID not found: {trade_uuid}")
            return
        
        # Update trade record
        tracking_data["trades"][trade_uuid]["stages"].append("trade_executed")
        tracking_data["trades"][trade_uuid]["current_stage"] = "trade_executed"
        tracking_data["trades"][trade_uuid]["execution_result"] = execution_result
        tracking_data["trades"][trade_uuid]["execution_timestamp"] = datetime.utcnow().isoformat()
        
        # Calculate loop completion time
        start_time = datetime.fromisoformat(tracking_data["trades"][trade_uuid]["start_time"])
        end_time = datetime.utcnow()
        loop_time = (end_time - start_time).total_seconds()
        
        tracking_data["trades"][trade_uuid]["loop_time"] = loop_time
        tracking_data["trades"][trade_uuid]["status"] = "completed" if execution_result.get("success") else "failed"
        
        # Store execution record
        tracking_data["executions"][trade_uuid] = {
            "trade_uuid": trade_uuid,
            "execution_result": execution_result,
            "timestamp": datetime.utcnow().isoformat(),
            "loop_time": loop_time
        }
        
        # Update stats
        if execution_result.get("success"):
            tracking_data["stats"]["completed_loops"] += 1
        else:
            tracking_data["stats"]["failed_loops"] += 1
        
        # Update average loop time
        total_loops = tracking_data["stats"]["completed_loops"] + tracking_data["stats"]["failed_loops"]
        if total_loops > 0:
            current_avg = tracking_data["stats"]["avg_loop_time"]
            tracking_data["stats"]["avg_loop_time"] = ((current_avg * (total_loops - 1)) + loop_time) / total_loops
        
        self.save_tracking_data(tracking_data)
        
        print(f"🎯 Trade execution tracked: {trade_uuid}")
        print(f"✅ Success: {execution_result.get('success', False)}")
        print(f"⏱️ Loop time: {loop_time:.2f}s")
    
    def get_trade_trace(self, trade_uuid: str) -> Optional[Dict]:
        """Get complete trace for a trade UUID"""
        tracking_data = self.load_tracking_data()
        
        if trade_uuid not in tracking_data["trades"]:
            return None
        
        trade_record = tracking_data["trades"][trade_uuid]
        
        # Build complete trace
        trace = {
            "trade_uuid": trade_uuid,
            "stages": trade_record["stages"],
            "current_stage": trade_record["current_stage"],
            "status": trade_record["status"],
            "start_time": trade_record["start_time"],
            "signal_data": tracking_data["signals"].get(trade_uuid, {}),
            "execution_data": tracking_data["executions"].get(trade_uuid, {}),
            "loop_time": trade_record.get("loop_time", 0)
        }
        
        return trace
    
    def get_active_trades(self) -> List[Dict]:
        """Get all active trades"""
        tracking_data = self.load_tracking_data()
        active_trades = []
        
        for trade_uuid, trade_record in tracking_data["trades"].items():
            if trade_record["status"] == "active":
                active_trades.append({
                    "trade_uuid": trade_uuid,
                    "current_stage": trade_record["current_stage"],
                    "start_time": trade_record["start_time"],
                    "stages": trade_record["stages"]
                })
        
        return active_trades
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        tracking_data = self.load_tracking_data()
        stats = tracking_data["stats"]
        
        # Calculate additional stats
        total_trades = stats["total_trades"]
        completed_loops = stats["completed_loops"]
        failed_loops = stats["failed_loops"]
        
        completion_rate = (completed_loops / total_trades * 100) if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "completed_loops": completed_loops,
            "failed_loops": failed_loops,
            "completion_rate": completion_rate,
            "avg_loop_time": stats["avg_loop_time"],
            "active_trades": len(self.get_active_trades())
        }
    
    def display_system_overview(self):
        """Display complete system overview"""
        stats = self.get_system_stats()
        active_trades = self.get_active_trades()
        
        print(f"\\n🔗 [UUID TRADE TRACKER] {datetime.utcnow().strftime('%H:%M:%S')} UTC")
        print("=" * 60)
        
        print("📊 SYSTEM STATISTICS:")
        print(f"Total Trades: {stats['total_trades']}")
        print(f"Completed Loops: {stats['completed_loops']}")
        print(f"Failed Loops: {stats['failed_loops']}")
        print(f"Completion Rate: {stats['completion_rate']:.1f}%")
        print(f"Average Loop Time: {stats['avg_loop_time']:.2f}s")
        print(f"Active Trades: {stats['active_trades']}")
        
        if active_trades:
            print("\\n🔄 ACTIVE TRADES:")
            for trade in active_trades[:5]:  # Show first 5
                print(f"  {trade['trade_uuid'][:20]}... - {trade['current_stage']}")
        
        print("-" * 60)
    
    def cleanup_old_trades(self, days_old: int = 7):
        """Cleanup trades older than specified days"""
        tracking_data = self.load_tracking_data()
        cutoff_time = datetime.utcnow().timestamp() - (days_old * 24 * 60 * 60)
        
        trades_to_remove = []
        for trade_uuid, trade_record in tracking_data["trades"].items():
            trade_time = datetime.fromisoformat(trade_record["start_time"]).timestamp()
            if trade_time < cutoff_time and trade_record["status"] in ["completed", "failed"]:
                trades_to_remove.append(trade_uuid)
        
        # Remove old trades
        for trade_uuid in trades_to_remove:
            tracking_data["trades"].pop(trade_uuid, None)
            tracking_data["signals"].pop(trade_uuid, None)
            tracking_data["executions"].pop(trade_uuid, None)
        
        self.save_tracking_data(tracking_data)
        
        print(f"🗑️ Cleaned up {len(trades_to_remove)} old trades")

def main():
    """Main UUID trade tracker"""
    tracker = UUIDTradeTracker()
    
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "--stats":
            tracker.display_system_overview()
        elif sys.argv[1] == "--cleanup":
            tracker.cleanup_old_trades(7)
        elif sys.argv[1] == "--trace" and len(sys.argv) > 2:
            trade_uuid = sys.argv[2]
            trace = tracker.get_trade_trace(trade_uuid)
            if trace:
                print(f"🔗 Trade Trace: {trade_uuid}")
                print(json.dumps(trace, indent=2))
            else:
                print(f"❌ Trade UUID not found: {trade_uuid}")
        elif sys.argv[1] == "--test":
            # Test UUID generation
            test_signal = {
                "signal_type": "RAPID_ASSAULT",
                "symbol": "EURUSD",
                "tcs_score": 85,
                "user_id": "test_user"
            }
            trade_uuid = tracker.track_signal_generation(test_signal)
            print(f"✅ Generated test UUID: {trade_uuid}")
    else:
        tracker.display_system_overview()

if __name__ == "__main__":
    main()