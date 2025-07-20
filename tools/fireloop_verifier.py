#!/usr/bin/env python3
"""
🔥 BITTEN FIRE LOOP VALIDATION SYSTEM
Linux-side monitor for complete trade verification
"""

import os
import time
import json
from datetime import datetime
from pathlib import Path

# UUID tracking integration
try:
    from uuid_trade_tracker import UUIDTradeTracker
    UUID_TRACKING_AVAILABLE = True
except ImportError:
    UUID_TRACKING_AVAILABLE = False
    class UUIDTradeTracker:
        def get_system_stats(self): return {"total_trades": 0, "active_trades": 0}
        def get_active_trades(self): return []

class FireLoopVerifier:
    """Real-time fire loop monitoring and validation"""
    
    def __init__(self):
        # File paths for monitoring
        self.instructions_file = Path("/root/HydraX-v2/bitten_instructions.txt")
        self.secure_file = Path("/root/HydraX-v2/bitten_instructions_secure.txt")
        self.result_file = Path("/root/HydraX-v2/bitten_results.txt")
        self.heartbeat_file = Path("/var/run/bridge_troll_heartbeat.txt")
        
        # AWS bridge signal directory (for monitoring)
        self.aws_signal_dir = Path("/root/HydraX-v2/data/aws_signals")
        self.aws_signal_dir.mkdir(parents=True, exist_ok=True)
        
        # Stats tracking
        self.stats = {
            "total_signals": 0,
            "signals_relayed": 0,
            "trades_executed": 0,
            "trades_failed": 0,
            "loop_completions": 0
        }
        
        print("🔥 BITTEN FIRE LOOP VALIDATOR INITIALIZED")
        print("📊 Monitoring complete signal-to-execution pipeline")
        print("=" * 60)
    
    def check_file_status(self, file_path: Path) -> dict:
        """Check file status with detailed information"""
        if not file_path.exists():
            return {
                "status": "❌ NOT FOUND",
                "age": "N/A",
                "size": "N/A",
                "content_preview": "File does not exist"
            }
        
        try:
            stat = file_path.stat()
            age = time.time() - stat.st_mtime
            size = stat.st_size
            
            # Get content preview
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    preview = content[-100:] if len(content) > 100 else content
                    preview = preview.replace('\n', ' ').strip()
            except:
                preview = "Unable to read content"
            
            # Determine status based on age
            if age < 10:
                status = "🟢 FRESH"
            elif age < 60:
                status = "🟡 RECENT"
            elif age < 300:
                status = "🟠 AGING"
            else:
                status = "🔴 STALE"
            
            return {
                "status": status,
                "age": f"{age:.1f}s",
                "size": f"{size}B",
                "content_preview": preview
            }
        except Exception as e:
            return {
                "status": "❌ ERROR",
                "age": "N/A",
                "size": "N/A",
                "content_preview": f"Error: {e}"
            }
    
    def check_bridge_heartbeat(self) -> dict:
        """Check bridge heartbeat status"""
        heartbeat_info = self.check_file_status(self.heartbeat_file)
        
        if heartbeat_info["status"] == "❌ NOT FOUND":
            return {
                "status": "❌ BRIDGE OFFLINE",
                "message": "No heartbeat file found"
            }
        
        try:
            with open(self.heartbeat_file, 'r') as f:
                heartbeat_content = f.read().strip()
            
            if "[HEARTBEAT]" in heartbeat_content:
                timestamp_str = heartbeat_content.split("[HEARTBEAT]")[1].strip()
                heartbeat_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                
                now = datetime.utcnow().replace(tzinfo=heartbeat_time.tzinfo)
                age = (now - heartbeat_time).total_seconds()
                
                if age < 60:
                    status = "🟢 BRIDGE ALIVE"
                elif age < 300:
                    status = "🟡 BRIDGE DELAYED"
                else:
                    status = "🔴 BRIDGE STALE"
                
                return {
                    "status": status,
                    "message": f"Last heartbeat: {age:.1f}s ago"
                }
        except Exception as e:
            return {
                "status": "❌ BRIDGE ERROR",
                "message": f"Heartbeat read error: {e}"
            }
    
    def analyze_trade_flow(self) -> dict:
        """Analyze the complete trade flow"""
        flow_analysis = {
            "stage_1_signal": self.check_file_status(self.instructions_file),
            "stage_2_relay": self.check_file_status(self.secure_file),
            "stage_3_result": self.check_file_status(self.result_file),
            "bridge_health": self.check_bridge_heartbeat()
        }
        
        # Determine overall flow health
        stages_healthy = 0
        total_stages = 3
        
        for stage_key in ["stage_1_signal", "stage_2_relay", "stage_3_result"]:
            if "🟢" in flow_analysis[stage_key]["status"]:
                stages_healthy += 1
        
        flow_health = (stages_healthy / total_stages) * 100
        
        if flow_health == 100:
            overall_status = "🟢 OPTIMAL"
        elif flow_health >= 66:
            overall_status = "🟡 PARTIAL"
        elif flow_health >= 33:
            overall_status = "🟠 DEGRADED"
        else:
            overall_status = "🔴 FAILED"
        
        flow_analysis["overall_status"] = overall_status
        flow_analysis["flow_health"] = f"{flow_health:.0f}%"
        
        return flow_analysis
    
    def check_aws_bridge_signals(self) -> dict:
        """Check AWS bridge signal activity"""
        try:
            # Check if AWS signal tracking exists
            aws_signals = []
            if self.aws_signal_dir.exists():
                for signal_file in self.aws_signal_dir.glob("*.json"):
                    try:
                        with open(signal_file, 'r') as f:
                            signal_data = json.load(f)
                            aws_signals.append({
                                "file": signal_file.name,
                                "timestamp": signal_data.get("timestamp", "unknown"),
                                "symbol": signal_data.get("symbol", "unknown"),
                                "status": signal_data.get("status", "unknown")
                            })
                    except:
                        continue
            
            # Sort by timestamp
            aws_signals.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return {
                "total_signals": len(aws_signals),
                "recent_signals": aws_signals[:5],  # Last 5 signals
                "last_signal_time": aws_signals[0]["timestamp"] if aws_signals else "None"
            }
        except Exception as e:
            return {
                "total_signals": 0,
                "recent_signals": [],
                "last_signal_time": "Error",
                "error": str(e)
            }
    
    def display_fire_loop_status(self):
        """Display comprehensive fire loop status"""
        flow_analysis = self.analyze_trade_flow()
        aws_signals = self.check_aws_bridge_signals()
        
        print(f"\n🔥 [FIRE LOOP STATUS] {datetime.utcnow().strftime('%H:%M:%S')} UTC")
        print("=" * 60)
        
        # Stage-by-stage analysis
        print("📊 PIPELINE STAGES:")
        print(f"[1] Signal Generation: {flow_analysis['stage_1_signal']['status']} ({flow_analysis['stage_1_signal']['age']})")
        print(f"[2] Troll Relay: {flow_analysis['stage_2_relay']['status']} ({flow_analysis['stage_2_relay']['age']})")
        print(f"[3] Trade Result: {flow_analysis['stage_3_result']['status']} ({flow_analysis['stage_3_result']['age']})")
        
        # Bridge health
        print(f"\n🌉 BRIDGE STATUS: {flow_analysis['bridge_health']['status']}")
        print(f"    {flow_analysis['bridge_health']['message']}")
        
        # AWS activity
        print(f"\n☁️ AWS SIGNALS: {aws_signals['total_signals']} total")
        print(f"    Last signal: {aws_signals['last_signal_time']}")
        
        # UUID tracking system
        if UUID_TRACKING_AVAILABLE:
            try:
                uuid_tracker = UUIDTradeTracker()
                uuid_stats = uuid_tracker.get_system_stats()
                active_trades = uuid_tracker.get_active_trades()
                
                print(f"\n🔗 UUID TRACKING: {uuid_stats['total_trades']} total trades")
                print(f"    Active: {uuid_stats['active_trades']}")
                print(f"    Completed: {uuid_stats['completed_loops']}")
                print(f"    Failed: {uuid_stats['failed_loops']}")
                print(f"    Success Rate: {uuid_stats['completion_rate']:.1f}%")
                
                if active_trades:
                    print(f"    Current: {active_trades[0]['trade_uuid'][:30]}... ({active_trades[0]['current_stage']})")
                
            except Exception as e:
                print(f"\n🔗 UUID TRACKING: Error - {e}")
        else:
            print("\n🔗 UUID TRACKING: Not available")
        
        # Overall health
        print(f"\n🎯 OVERALL HEALTH: {flow_analysis['overall_status']} ({flow_analysis['flow_health']})")
        
        # Recent activity preview
        if flow_analysis['stage_1_signal']['content_preview'] != "File does not exist":
            print(f"\n📝 LAST SIGNAL: {flow_analysis['stage_1_signal']['content_preview']}")
        
        if flow_analysis['stage_3_result']['content_preview'] != "File does not exist":
            print(f"📊 LAST RESULT: {flow_analysis['stage_3_result']['content_preview']}")
        
        print("-" * 60)
    
    def run_continuous_monitoring(self):
        """Run continuous fire loop monitoring"""
        print("🔄 Starting continuous fire loop monitoring...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.display_fire_loop_status()
                time.sleep(10)  # Check every 10 seconds
        except KeyboardInterrupt:
            print("\n⏹️ Fire loop monitoring stopped")
    
    def run_single_check(self):
        """Run single fire loop check"""
        self.display_fire_loop_status()
        
        # Return analysis for programmatic use
        return self.analyze_trade_flow()

def main():
    """Main fire loop verifier"""
    verifier = FireLoopVerifier()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        verifier.run_continuous_monitoring()
    else:
        verifier.run_single_check()

if __name__ == "__main__":
    main()