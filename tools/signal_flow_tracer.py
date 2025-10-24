#!/usr/bin/env python3
"""
Signal Flow Tracer - BITTEN System Phase 1
Tracks signal propagation from Elite Guard through to EA execution

⚠️ CRITICAL SAFETY: READ-ONLY OBSERVATIONAL TOOL
- Does NOT inject signals into live trading
- Does NOT modify signal flow
- Subscribes to EXISTING ZMQ ports in observation mode
- Measures latency and validates data integrity at each stage

Signal Flow Path:
1. Elite Guard (port 5557) → ZMQ PUB "ELITE_GUARD_SIGNAL {json}"
2. ZMQ Relay → POST /api/signals
3. WebApp → Mission DB insertion
4. WebApp → AUTO fire check
5. WebApp → IPC queue (/tmp/bitten_cmdqueue)
6. Command Router (port 5555) → EA
7. EA → Confirmation (port 5558)
"""

import argparse
import json
import sys
import time
import traceback
from collections import defaultdict
from datetime import datetime
from typing import Dict, Optional

import zmq


class SignalFlowTracer:
    """Traces signal flow through all stages of BITTEN system"""

    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or f"TRACE_{int(time.time())}"
        self.traces = {}  # signal_id -> stages dict
        self.stage_latencies = defaultdict(list)
        self.context = zmq.Context()

        # Stage timestamps
        self.STAGE_ELITE_GUARD = "elite_guard_pub"
        self.STAGE_ZMQ_RELAY = "zmq_relay"
        self.STAGE_WEBAPP = "webapp_api"
        self.STAGE_MISSION_DB = "mission_db"
        self.STAGE_AUTO_CHECK = "auto_fire_check"
        self.STAGE_IPC_QUEUE = "ipc_queue"
        self.STAGE_ROUTER = "command_router"
        self.STAGE_EA = "ea_execution"
        self.STAGE_CONFIRM = "confirmation"

        print("=" * 80)
        print("🔍 BITTEN SIGNAL FLOW TRACER - Phase 1 Development")
        print("=" * 80)
        print(f"Trace ID: {self.trace_id}")
        print(f"Started: {datetime.now().isoformat()}")
        print("=" * 80)
        print("\n⚠️  SAFETY MODE: Read-only observation, NO signal injection\n")

    def setup_listeners(self):
        """Setup ZMQ subscribers for observation"""
        print("📡 Setting up ZMQ listeners (observation mode)...")

        # 1. Elite Guard signal publisher (port 5557)
        try:
            self.elite_sub = self.context.socket(zmq.SUB)
            self.elite_sub.connect("tcp://127.0.0.1:5557")
            self.elite_sub.subscribe(b"")  # Subscribe to all
            self.elite_sub.setsockopt(zmq.RCVTIMEO, 1000)  # 1s timeout
            print("   ✅ Port 5557 - Elite Guard signal publisher")
        except Exception as e:
            print(f"   ❌ Port 5557 failed: {e}")
            self.elite_sub = None

        # 2. Confirmation listener (port 5558) - EA responses
        try:
            self.confirm_sub = self.context.socket(zmq.SUB)
            self.confirm_sub.connect("tcp://127.0.0.1:5558")
            self.confirm_sub.subscribe(b"")
            self.confirm_sub.setsockopt(zmq.RCVTIMEO, 1000)
            print("   ✅ Port 5558 - Trade confirmations from EA")
        except Exception as e:
            print(f"   ❌ Port 5558 failed: {e}")
            self.confirm_sub = None

        print("\n⚡ Listening for signals...\n")

    def trace_signal(self, signal_id: str, stage: str, data: Dict, timestamp: float = None):
        """Record signal at a specific stage"""
        if timestamp is None:
            timestamp = time.time()

        if signal_id not in self.traces:
            self.traces[signal_id] = {
                "signal_id": signal_id,
                "stages": {},
                "first_seen": timestamp,
                "last_seen": timestamp,
            }

        self.traces[signal_id]["stages"][stage] = {
            "timestamp": timestamp,
            "data": data,
            "iso_time": datetime.fromtimestamp(timestamp).isoformat(),
        }
        self.traces[signal_id]["last_seen"] = timestamp

        # Calculate latency from previous stage
        stages_order = [
            self.STAGE_ELITE_GUARD,
            self.STAGE_ZMQ_RELAY,
            self.STAGE_WEBAPP,
            self.STAGE_MISSION_DB,
            self.STAGE_AUTO_CHECK,
            self.STAGE_IPC_QUEUE,
            self.STAGE_ROUTER,
            self.STAGE_EA,
            self.STAGE_CONFIRM,
        ]

        if stage in stages_order:
            idx = stages_order.index(stage)
            if idx > 0:
                prev_stage = stages_order[idx - 1]
                if prev_stage in self.traces[signal_id]["stages"]:
                    prev_ts = self.traces[signal_id]["stages"][prev_stage]["timestamp"]
                    latency_ms = (timestamp - prev_ts) * 1000
                    self.stage_latencies[f"{prev_stage}→{stage}"].append(latency_ms)

    def listen_elite_guard(self):
        """Listen for signals from Elite Guard (port 5557)"""
        if not self.elite_sub:
            return

        try:
            message = self.elite_sub.recv_string()
            timestamp = time.time()

            # Parse Elite Guard message format: "ELITE_GUARD_SIGNAL {json}"
            if message.startswith("ELITE_GUARD_SIGNAL "):
                json_str = message[19:]
                signal_data = json.loads(json_str)

                signal_id = signal_data.get("signal_id")
                if signal_id:
                    self.trace_signal(signal_id, self.STAGE_ELITE_GUARD, signal_data, timestamp)

                    # Immediate validation
                    issues = self.validate_signal_data(signal_data, self.STAGE_ELITE_GUARD)

                    print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] ELITE GUARD SIGNAL")
                    print(f"   Signal ID: {signal_id}")
                    print(f"   Symbol: {signal_data.get('symbol')} {signal_data.get('direction')}")
                    print(f"   Confidence: {signal_data.get('confidence')}%")
                    print(f"   Pattern: {signal_data.get('pattern_type')}")
                    print(f"   Entry: {signal_data.get('entry_price')}")
                    print(f"   SL: {signal_data.get('stop_loss')} | TP: {signal_data.get('take_profit')}")

                    if issues:
                        print(f"   ⚠️  Validation Issues: {', '.join(issues)}")
                    else:
                        print(f"   ✅ Data integrity: OK")

                    print()

        except zmq.Again:
            pass  # Timeout - normal
        except Exception as e:
            print(f"❌ Elite Guard listener error: {e}")

    def listen_confirmations(self):
        """Listen for confirmations from EA (port 5558)"""
        if not self.confirm_sub:
            return

        try:
            message = self.confirm_sub.recv_string()
            timestamp = time.time()

            try:
                confirm_data = json.loads(message)
                fire_id = confirm_data.get("fire_id")

                if fire_id:
                    # Try to match to existing signal
                    signal_id = fire_id.replace("ELITE_GUARD_", "ELITE_GUARD_")

                    self.trace_signal(signal_id, self.STAGE_CONFIRM, confirm_data, timestamp)

                    print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] EA CONFIRMATION")
                    print(f"   Fire ID: {fire_id}")
                    print(f"   Ticket: {confirm_data.get('ticket')}")
                    print(f"   Fill Price: {confirm_data.get('price')}")
                    print(f"   Status: {confirm_data.get('status')}")

                    # Calculate total latency
                    if signal_id in self.traces:
                        first_ts = self.traces[signal_id]["first_seen"]
                        total_latency_ms = (timestamp - first_ts) * 1000
                        print(f"   ⏱️  Total Latency: {total_latency_ms:.2f}ms")

                    print()

            except json.JSONDecodeError:
                pass  # Not JSON, skip

        except zmq.Again:
            pass  # Timeout - normal
        except Exception as e:
            print(f"❌ Confirmation listener error: {e}")

    def validate_signal_data(self, signal_data: Dict, stage: str) -> list:
        """Validate signal data integrity at current stage"""
        issues = []

        # Required fields for Elite Guard stage
        if stage == self.STAGE_ELITE_GUARD:
            required = ["signal_id", "symbol", "direction", "confidence", "pattern_type"]

            for field in required:
                if field not in signal_data or signal_data[field] is None:
                    issues.append(f"Missing {field}")

            # Validate price levels
            if signal_data.get("stop_loss") is None or signal_data.get("stop_loss") == 0:
                issues.append("Missing/invalid stop_loss")

            if signal_data.get("take_profit") is None or signal_data.get("take_profit") == 0:
                issues.append("Missing/invalid take_profit")

            # Validate direction
            direction = signal_data.get("direction", "").upper()
            if direction not in ["BUY", "SELL"]:
                issues.append(f"Invalid direction: {direction}")

            # Validate confidence range
            confidence = signal_data.get("confidence", 0)
            if not (0 <= confidence <= 100):
                issues.append(f"Confidence out of range: {confidence}")

        return issues

    def generate_report(self):
        """Generate comprehensive flow analysis report"""
        print("\n" + "=" * 80)
        print("📊 SIGNAL FLOW ANALYSIS REPORT")
        print("=" * 80)

        if not self.traces:
            print("\n⚠️  No signals traced during observation period\n")
            return

        print(f"\nTotal Signals Traced: {len(self.traces)}")
        print(f"Observation Period: {datetime.fromtimestamp(min(t['first_seen'] for t in self.traces.values())).isoformat()}")
        print(f"                 to {datetime.fromtimestamp(max(t['last_seen'] for t in self.traces.values())).isoformat()}")

        # Stage completion rates
        print("\n📈 STAGE COMPLETION RATES:")
        print("-" * 80)

        stages_order = [
            ("Elite Guard", self.STAGE_ELITE_GUARD),
            ("ZMQ Relay", self.STAGE_ZMQ_RELAY),
            ("WebApp API", self.STAGE_WEBAPP),
            ("Mission DB", self.STAGE_MISSION_DB),
            ("Auto-Fire Check", self.STAGE_AUTO_CHECK),
            ("IPC Queue", self.STAGE_IPC_QUEUE),
            ("Command Router", self.STAGE_ROUTER),
            ("EA Execution", self.STAGE_EA),
            ("Confirmation", self.STAGE_CONFIRM),
        ]

        for stage_name, stage_key in stages_order:
            count = sum(1 for trace in self.traces.values() if stage_key in trace["stages"])
            pct = (count / len(self.traces)) * 100 if self.traces else 0
            print(f"   {stage_name:20} {count:3}/{len(self.traces):3} ({pct:5.1f}%)")

        # Latency analysis
        if self.stage_latencies:
            print("\n⏱️  STAGE LATENCIES (milliseconds):")
            print("-" * 80)

            for transition, latencies in sorted(self.stage_latencies.items()):
                if latencies:
                    avg = sum(latencies) / len(latencies)
                    min_lat = min(latencies)
                    max_lat = max(latencies)
                    print(f"   {transition:30} Avg: {avg:7.2f}ms | Min: {min_lat:7.2f}ms | Max: {max_lat:7.2f}ms")

        # Data integrity summary
        print("\n🔍 DATA INTEGRITY SUMMARY:")
        print("-" * 80)

        total_issues = 0
        for signal_id, trace in self.traces.items():
            if self.STAGE_ELITE_GUARD in trace["stages"]:
                signal_data = trace["stages"][self.STAGE_ELITE_GUARD]["data"]
                issues = self.validate_signal_data(signal_data, self.STAGE_ELITE_GUARD)
                if issues:
                    print(f"   ⚠️  {signal_id}: {', '.join(issues)}")
                    total_issues += len(issues)

        if total_issues == 0:
            print("   ✅ All signals passed validation")
        else:
            print(f"\n   Total Issues Found: {total_issues}")

        # Detailed trace for each signal
        print("\n📋 DETAILED SIGNAL TRACES:")
        print("-" * 80)

        for signal_id, trace in sorted(self.traces.items(), key=lambda x: x[1]["first_seen"]):
            print(f"\n🎯 {signal_id}")
            print(f"   First Seen: {datetime.fromtimestamp(trace['first_seen']).isoformat()}")

            for stage_name, stage_key in stages_order:
                if stage_key in trace["stages"]:
                    stage_data = trace["stages"][stage_key]
                    print(f"   ✅ {stage_name:20} {stage_data['iso_time']}")
                else:
                    print(f"   ❌ {stage_name:20} Not reached")

        print("\n" + "=" * 80)

    def run(self, duration_seconds: int = 300):
        """Run tracer for specified duration"""
        self.setup_listeners()

        print(f"⏳ Tracing for {duration_seconds} seconds (Ctrl+C to stop early)...\n")

        start_time = time.time()
        try:
            while time.time() - start_time < duration_seconds:
                # Listen to all channels
                self.listen_elite_guard()
                self.listen_confirmations()

                # Small sleep to prevent CPU spinning
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\n\n⚠️  Trace interrupted by user\n")

        finally:
            self.generate_report()

            # Save to JSON
            report_file = f"/root/HydraX-v2/signal_flow_trace_{self.trace_id}.json"
            with open(report_file, "w") as f:
                json.dump(
                    {
                        "trace_id": self.trace_id,
                        "traces": self.traces,
                        "stage_latencies": dict(self.stage_latencies),
                        "generated_at": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )
            print(f"\n💾 Full trace saved to: {report_file}\n")


def main():
    parser = argparse.ArgumentParser(description="BITTEN Signal Flow Tracer - Phase 1 Development")
    parser.add_argument(
        "--duration", type=int, default=300, help="Observation duration in seconds (default: 300)"
    )
    parser.add_argument("--trace-id", type=str, help="Custom trace ID (default: auto-generated)")

    args = parser.parse_args()

    try:
        tracer = SignalFlowTracer(trace_id=args.trace_id)
        tracer.run(duration_seconds=args.duration)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
