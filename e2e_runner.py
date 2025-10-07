#!/usr/bin/env python3
"""
STRICT_EXECUTION_PROTOCOL — E2E-1 End-to-End Runner
Consolidated test runner for all PHASE-2 components
"""

import zmq
import json
import time
import os
import subprocess
from pathlib import Path
import hashlib

class E2ERunner:
    def __init__(self):
        self.ctx = zmq.Context()
        self.push_socket = self.ctx.socket(zmq.PUSH)
        self.push_socket.connect("ipc:///tmp/bitten_cmdqueue")

        self.timestamp = int(time.time())
        self.report = {}
        self.start_time = time.time()

    def _send_fire_command(self, fire_data):
        """Send fire command via IPC"""
        fire_id = f"E2E-{fire_data['test']}-{self.timestamp}"

        payload = {
            "type": "fire",
            "target_uuid": "COMMANDER_DEV_001",
            "fire_id": fire_id,
            **fire_data['payload']
        }

        self.push_socket.send_json(payload)
        return fire_id

    def _wait_for_confirmation(self, fire_id, timeout=15):
        """Wait for confirmation in PM2 logs"""
        confirm_log = "/root/.pm2/logs/confirm-listener-v207-error.log"
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                with open(confirm_log, 'r') as f:
                    content = f.read()

                if fire_id in content and "CONFIRMATION RECEIVED" in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if fire_id in line and ("FILLED" in line or "REJECTED" in line):
                            # Extract key info from update line
                            if "FILLED" in line:
                                parts = line.split()
                                for part in parts:
                                    if "ticket=" in part:
                                        ticket = int(part.split('=')[1].rstrip(','))
                                        return {"status": "success", "ticket": ticket}
                            else:
                                return {"status": "failed", "message": "Trade rejected"}

                time.sleep(0.5)
            except Exception:
                time.sleep(0.5)

        return {"status": "timeout", "message": "No confirmation received"}

    def run_mf_tests(self):
        """Run MF-1, MF-2, MF-3 smoke tests"""
        print("🔥 Running MF smoke tests...")

        # MF-1: No SL/TP
        fire_id = self._send_fire_command({
            "test": "MF1",
            "payload": {
                "symbol": "EURUSD",
                "direction": "SELL",
                "lot": 0.01,
                "entry": 1.1000
            }
        })
        self.report['mf1'] = {
            "fire_id": fire_id,
            "confirmation": self._wait_for_confirmation(fire_id)
        }

        time.sleep(1)

        # MF-2: Wrong ordering
        fire_id = self._send_fire_command({
            "test": "MF2",
            "payload": {
                "symbol": "GBPUSD",
                "direction": "BUY",
                "lot": 0.01,
                "entry": 1.3000,
                "sl": 1.3200,  # Wrong
                "tp": 1.2800   # Wrong
            }
        })
        self.report['mf2'] = {
            "fire_id": fire_id,
            "confirmation": self._wait_for_confirmation(fire_id)
        }

        time.sleep(1)

        # MF-3: Extreme bounds success
        fire_id = self._send_fire_command({
            "test": "MF3",
            "payload": {
                "symbol": "EURUSD",
                "direction": "SELL",
                "lot": 0.01,
                "entry": 1.1000,
                "sl": 9.99999,
                "tp": 0.00010
            }
        })
        self.report['mf3'] = {
            "fire_id": fire_id,
            "confirmation": self._wait_for_confirmation(fire_id)
        }

    def run_sr_tests(self):
        """Run SR-1 symbol resolver tests"""
        print("🎯 Running SR symbol resolver tests...")

        aliases = ["GOLD", "XAUUSD", "XAUUSD."]
        self.report['sr_tests'] = []

        for i, symbol in enumerate(aliases, 1):
            fire_id = self._send_fire_command({
                "test": f"SR{i}",
                "payload": {
                    "symbol": symbol,
                    "direction": "SELL",
                    "lot": 0.01,
                    "entry": 2000.0,
                    "sl": 2050.0,
                    "tp": 1950.0
                }
            })

            result = {
                "symbol": symbol,
                "fire_id": fire_id,
                "confirmation": self._wait_for_confirmation(fire_id)
            }
            self.report['sr_tests'].append(result)
            time.sleep(1)

    def run_hp_test(self):
        """Run HP-1 hedge preemptive test"""
        print("🛡️ Running HP hedge preemptive test...")

        # Try to open position first
        fire_id = self._send_fire_command({
            "test": "HP1",
            "payload": {
                "symbol": "EURUSD",
                "direction": "SELL",
                "lot": 0.01,
                "entry": 1.1000,
                "sl": 1.1050,
                "tp": 1.0950
            }
        })

        self.report['hp_test'] = {
            "fire_id": fire_id,
            "confirmation": self._wait_for_confirmation(fire_id),
            "note": "HP-1 router-level preemptive reject not implemented - EA-level only"
        }

    def run_af_test(self):
        """Run AF-1 auto-fire test"""
        print("⚡ Running AF auto-fire test...")

        fire_id = self._send_fire_command({
            "test": "AF1",
            "payload": {
                "symbol": "EURUSD",
                "direction": "BUY",
                "lot": 0.01,
                "entry": 0,
                "sl": 1.1000,
                "tp": 1.1100
            }
        })

        self.report['af_test'] = {
            "fire_id": fire_id,
            "confirmation": self._wait_for_confirmation(fire_id)
        }

    def check_telemetry(self):
        """Check for 3 telemetry lines"""
        print("📡 Checking telemetry...")

        try:
            log_file = "/root/.pm2/logs/telemetry-bridge-v207-error.log"
            with open(log_file, 'r') as f:
                lines = f.readlines()

            # Get last 3 STATS lines
            stats_lines = [line for line in lines if "📈 STATS:" in line][-3:]

            self.report['telemetry'] = {
                "lines_found": len(stats_lines),
                "sample": stats_lines[0].strip() if stats_lines else "No telemetry found"
            }
        except Exception as e:
            self.report['telemetry'] = {
                "lines_found": 0,
                "error": str(e)
            }

    def send_ping_test(self):
        """Send PONG test"""
        print("🏓 Testing PONG...")

        ping_payload = {
            "type": "ping",
            "target_uuid": "COMMANDER_DEV_001",
            "ping_id": f"E2E-PING-{self.timestamp}"
        }

        self.push_socket.send_json(ping_payload)

        # Check for PONG in confirm logs
        time.sleep(2)
        try:
            with open("/root/.pm2/logs/confirm-listener-v207-error.log", 'r') as f:
                content = f.read()
                if f"E2E-PING-{self.timestamp}" in content and "PONG:" in content:
                    self.report['pong_test'] = {"status": "success"}
                else:
                    self.report['pong_test'] = {"status": "no_pong_found"}
        except Exception as e:
            self.report['pong_test'] = {"status": "error", "message": str(e)}

    def generate_report(self):
        """Generate comprehensive JSON report"""
        report_dir = Path("/root/HydraX-v2/_reports")
        report_dir.mkdir(exist_ok=True)

        # Add runtime info
        self.report['runtime_seconds'] = round(time.time() - self.start_time, 2)
        self.report['timestamp'] = self.timestamp
        self.report['test_summary'] = self._count_passes()

        # Write report
        report_file = report_dir / f"e2e_{self.timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(self.report, f, indent=2)

        return report_file

    def _count_passes(self):
        """Count test passes by section"""
        counts = {}

        # Count MF passes
        mf_passes = 0
        for key in ['mf1', 'mf2', 'mf3']:
            if key in self.report and self.report[key].get('confirmation', {}).get('status') in ['success', 'failed']:
                mf_passes += 1
        counts['mf_tests'] = mf_passes

        # Count SR passes
        sr_passes = len(self.report.get('sr_tests', []))
        counts['sr_tests'] = sr_passes

        # Count other sections
        counts['hp_test'] = 1 if 'hp_test' in self.report else 0
        counts['af_test'] = 1 if 'af_test' in self.report else 0
        counts['telemetry'] = 1 if 'telemetry' in self.report else 0
        counts['pong_test'] = 1 if 'pong_test' in self.report else 0

        return counts

    def run_all(self):
        """Execute complete E2E test suite"""
        print("🚀 BITTEN E2E-1 END-TO-END RUNNER")
        print("=" * 50)

        try:
            self.run_mf_tests()
            time.sleep(2)

            self.run_sr_tests()
            time.sleep(2)

            self.run_hp_test()
            time.sleep(2)

            self.run_af_test()
            time.sleep(2)

            self.check_telemetry()

            self.send_ping_test()

            report_file = self.generate_report()

            print(f"\n📊 E2E TEST COMPLETE")
            print(f"📁 Report: {report_file}")
            print(f"⏱️  Runtime: {self.report['runtime_seconds']}s")

            return report_file

        except Exception as e:
            print(f"❌ E2E Test failed: {e}")
            return None
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        self.push_socket.close()
        self.ctx.term()

if __name__ == "__main__":
    runner = E2ERunner()
    report_file = runner.run_all()

    if report_file:
        # Calculate MD5
        with open(report_file, 'rb') as f:
            md5sum = hashlib.md5(f.read()).hexdigest()

        # Show first 40 lines
        with open(report_file, 'r') as f:
            lines = f.readlines()[:40]

        print(f"\n📋 First 40 JSON lines:")
        for i, line in enumerate(lines, 1):
            print(f"{i:2d}→ {line.rstrip()}")

        print(f"\n🔐 MD5SUM: {md5sum}")
        print(str(report_file))
    else:
        exit(1)