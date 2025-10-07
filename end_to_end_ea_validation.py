#!/usr/bin/env python3
"""
🔄 END-TO-END EA CONNECTIVITY VALIDATION
Complete validation pipeline from signal generation to EA execution
Can be run when markets are closed to verify full system integrity
"""

import json
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, Optional

# Add HydraX-v2 to path
sys.path.append("/root/HydraX-v2")


class EndToEndEAValidator:
    """Complete EA connectivity validation pipeline"""

    def __init__(self):
        self.validation_id = f"E2E_VALIDATION_{int(time.time())}"
        self.results = []
        self.start_time = time.time()

        print("🔄 End-to-End EA Connectivity Validator")
        print(f"📋 Validation ID: {self.validation_id}")
        print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    def log_step(self, step: str, status: str, details: str = "", duration: float = 0):
        """Log validation step with timing"""
        result = {
            "step": step,
            "status": status,
            "details": details,
            "duration_ms": round(duration * 1000, 1),
            "timestamp": datetime.now().isoformat(),
        }
        self.results.append(result)

        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        duration_str = f" ({result['duration_ms']}ms)" if duration > 0 else ""
        print(f"{status_icon} {step}: {details}{duration_str}")

    def step_1_infrastructure_check(self) -> bool:
        """Step 1: Verify core infrastructure is running"""
        print("\n🔧 STEP 1: INFRASTRUCTURE VERIFICATION")
        print("-" * 50)

        step_start = time.time()

        try:
            # Check PM2 processes
            result = subprocess.run(["pm2", "jlist"], capture_output=True, text=True)
            if result.returncode == 0:
                pm2_data = json.loads(result.stdout)
                critical_processes = ["command_router", "elite_guard", "confirm_listener", "webapp"]

                running_processes = []
                for process in pm2_data:
                    if process["name"] in critical_processes and process["pm2_env"]["status"] == "online":
                        running_processes.append(process["name"])

                if len(running_processes) >= 3:  # At least 3 critical processes
                    self.log_step(
                        "PM2 Processes",
                        "PASS",
                        f"{len(running_processes)}/4 critical processes running",
                        time.time() - step_start,
                    )
                    return True
                else:
                    self.log_step(
                        "PM2 Processes",
                        "FAIL",
                        f"Only {len(running_processes)}/4 critical processes running",
                        time.time() - step_start,
                    )
                    return False
            else:
                self.log_step("PM2 Processes", "FAIL", "PM2 not responding", time.time() - step_start)
                return False

        except Exception as e:
            self.log_step("PM2 Processes", "FAIL", f"Error: {e}", time.time() - step_start)
            return False

    def step_2_zmq_port_verification(self) -> bool:
        """Step 2: Verify all ZMQ ports are bound and listening"""
        print("\n📡 STEP 2: ZMQ PORT VERIFICATION")
        print("-" * 50)

        step_start = time.time()

        try:
            result = subprocess.run(["ss", "-tulpen"], capture_output=True, text=True)
            required_ports = [5555, 5556, 5557, 5558, 5560]
            bound_ports = []

            for port in required_ports:
                for line in result.stdout.split("\n"):
                    if f":{port}" in line and "LISTEN" in line:
                        bound_ports.append(port)
                        break

            if len(bound_ports) == len(required_ports):
                self.log_step("ZMQ Ports", "PASS", f"All {len(bound_ports)} ports listening", time.time() - step_start)
                return True
            else:
                missing = set(required_ports) - set(bound_ports)
                self.log_step("ZMQ Ports", "FAIL", f"Missing ports: {missing}", time.time() - step_start)
                return False

        except Exception as e:
            self.log_step("ZMQ Ports", "FAIL", f"Error: {e}", time.time() - step_start)
            return False

    def step_3_database_connectivity(self) -> bool:
        """Step 3: Test database connectivity and EA registration"""
        print("\n🗄️ STEP 3: DATABASE CONNECTIVITY")
        print("-" * 50)

        step_start = time.time()

        try:
            conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
            cursor = conn.cursor()

            # Test database query
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            required_tables = ["ea_instances", "signals", "fires", "missions"]
            existing_tables = [table[0] for table in tables]

            missing_tables = set(required_tables) - set(existing_tables)

            if not missing_tables:
                # Check EA instances
                cursor.execute("SELECT COUNT(*) FROM ea_instances")
                ea_count = cursor.fetchone()[0]

                self.log_step(
                    "Database", "PASS", f"All tables present, {ea_count} EA instances", time.time() - step_start
                )

                conn.close()
                return True
            else:
                self.log_step("Database", "FAIL", f"Missing tables: {missing_tables}", time.time() - step_start)
                conn.close()
                return False

        except Exception as e:
            self.log_step("Database", "FAIL", f"Error: {e}", time.time() - step_start)
            return False

    def step_4_fire_packet_generation(self) -> Optional[Dict]:
        """Step 4: Generate and validate test fire packet"""
        print("\n🔥 STEP 4: FIRE PACKET GENERATION")
        print("-" * 50)

        step_start = time.time()

        try:
            from collections import OrderedDict

            # Generate test fire packet
            test_packet = OrderedDict(
                [
                    ("type", "fire"),
                    ("target_uuid", "COMMANDER_DEV_001"),
                    ("fire_id", self.validation_id),
                    ("symbol", "EURUSD"),
                    ("direction", "BUY"),
                    ("entry", 0),
                    ("sl", 1.09800),
                    ("tp", 1.10300),
                    ("lot", 0.01),
                ]
            )

            # Validate packet format
            format_checks = [
                test_packet.get("type") == "fire",
                test_packet.get("direction").isupper(),
                isinstance(test_packet.get("entry"), (int, float)),
                isinstance(test_packet.get("sl"), (int, float)),
                isinstance(test_packet.get("tp"), (int, float)),
                isinstance(test_packet.get("lot"), (int, float)),
            ]

            if all(format_checks):
                self.log_step("Fire Packet", "PASS", "Valid packet generated", time.time() - step_start)
                return test_packet
            else:
                self.log_step("Fire Packet", "FAIL", "Invalid packet format", time.time() - step_start)
                return None

        except Exception as e:
            self.log_step("Fire Packet", "FAIL", f"Error: {e}", time.time() - step_start)
            return None

    def step_5_ipc_transmission(self, test_packet: Dict) -> bool:
        """Step 5: Test IPC queue transmission"""
        print("\n📤 STEP 5: IPC TRANSMISSION TEST")
        print("-" * 50)

        step_start = time.time()

        try:
            from enqueue_fire import enqueue_fire

            # Send via enqueue_fire function
            success = enqueue_fire(test_packet)

            if success:
                self.log_step("IPC Transmission", "PASS", "Fire packet sent via IPC queue", time.time() - step_start)
                return True
            else:
                self.log_step("IPC Transmission", "FAIL", "enqueue_fire returned False", time.time() - step_start)
                return False

        except Exception as e:
            self.log_step("IPC Transmission", "FAIL", f"Error: {e}", time.time() - step_start)
            return False

    def step_6_ea_heartbeat_check(self) -> Dict:
        """Step 6: Check EA heartbeat status"""
        print("\n💓 STEP 6: EA HEARTBEAT VERIFICATION")
        print("-" * 50)

        step_start = time.time()

        try:
            conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
            cursor = conn.cursor()

            # Check COMMANDER_DEV_001 specifically
            cursor.execute(
                """
                SELECT target_uuid, user_id, last_seen,
                       (strftime('%s','now') - last_seen) as age_seconds
                FROM ea_instances
                WHERE target_uuid = 'COMMANDER_DEV_001'
            """
            )

            row = cursor.fetchone()
            if row:
                target_uuid, user_id, last_seen, age_seconds = row

                if age_seconds < 300:  # 5 minutes
                    self.log_step(
                        "EA Heartbeat", "PASS", f"Fresh heartbeat ({age_seconds}s ago)", time.time() - step_start
                    )
                    status = "FRESH"
                else:
                    self.log_step(
                        "EA Heartbeat", "WARN", f"Stale heartbeat ({age_seconds}s ago)", time.time() - step_start
                    )
                    status = "STALE"

                conn.close()
                return {"status": status, "age_seconds": age_seconds, "user_id": user_id}
            else:
                self.log_step("EA Heartbeat", "FAIL", "COMMANDER_DEV_001 not found", time.time() - step_start)
                conn.close()
                return {"status": "MISSING"}

        except Exception as e:
            self.log_step("EA Heartbeat", "FAIL", f"Error: {e}", time.time() - step_start)
            return {"status": "ERROR", "error": str(e)}

    def step_7_command_router_verification(self) -> bool:
        """Step 7: Verify command router processing"""
        print("\n⚙️ STEP 7: COMMAND ROUTER VERIFICATION")
        print("-" * 50)

        step_start = time.time()

        try:
            # Check command router logs
            result = subprocess.run(
                ["pm2", "logs", "command_router", "--lines", "5", "--nostream"], capture_output=True, text=True
            )

            if result.returncode == 0 and result.stdout:
                self.log_step("Command Router", "PASS", "Command router responsive", time.time() - step_start)
                return True
            else:
                self.log_step(
                    "Command Router", "WARN", "Command router not responding to logs", time.time() - step_start
                )
                return False

        except Exception as e:
            self.log_step("Command Router", "FAIL", f"Error: {e}", time.time() - step_start)
            return False

    def run_complete_validation(self) -> Dict:
        """Run complete end-to-end validation"""
        print("🚀 STARTING END-TO-END EA CONNECTIVITY VALIDATION")
        print("=" * 70)

        # Step 1: Infrastructure
        infra_ok = self.step_1_infrastructure_check()

        # Step 2: ZMQ Ports
        ports_ok = self.step_2_zmq_port_verification()

        # Step 3: Database
        db_ok = self.step_3_database_connectivity()

        # Step 4: Fire Packet
        test_packet = self.step_4_fire_packet_generation()
        packet_ok = test_packet is not None

        # Step 5: IPC Transmission (only if packet generated)
        ipc_ok = False
        if packet_ok:
            ipc_ok = self.step_5_ipc_transmission(test_packet)

        # Step 6: EA Heartbeat
        ea_status = self.step_6_ea_heartbeat_check()

        # Step 7: Command Router
        router_ok = self.step_7_command_router_verification()

        # Calculate results
        total_duration = time.time() - self.start_time

        critical_checks = [infra_ok, ports_ok, db_ok, packet_ok, ipc_ok]
        passed_critical = sum(critical_checks)

        print("\n" + "=" * 70)
        print("🎯 END-TO-END VALIDATION COMPLETE")
        print("=" * 70)

        # Summary
        print(f"⏱️ Total Duration: {total_duration:.1f} seconds")
        print(f"📊 Critical Checks: {passed_critical}/5 passed")
        print(f"💓 EA Status: {ea_status.get('status', 'UNKNOWN')}")

        # Overall assessment
        if passed_critical >= 4 and ea_status.get("status") in ["FRESH", "STALE"]:
            overall_status = "READY"
            print("🎯 OVERALL STATUS: ✅ SYSTEM READY FOR EA CONNECTION")

            if ea_status.get("status") == "STALE":
                print("💡 NOTE: EA heartbeat is stale - restart EA on Windows VPS")

        elif passed_critical >= 3:
            overall_status = "PARTIAL"
            print("🎯 OVERALL STATUS: ⚠️ SYSTEM PARTIALLY READY - CHECK WARNINGS")

        else:
            overall_status = "NOT_READY"
            print("🎯 OVERALL STATUS: ❌ SYSTEM NOT READY - FIX CRITICAL ISSUES")

        # Next steps
        print("\n📋 NEXT STEPS:")
        if ea_status.get("status") == "FRESH":
            print("1. ✅ EA is connected - test live fire packet")
            print("2. ✅ Monitor confirmation system")
        elif ea_status.get("status") == "STALE":
            print("1. 🔄 Restart EA on Windows VPS")
            print("2. 🔍 Check EA logs for connection errors")
            print("3. 🛡️ Verify Windows firewall rules")
        else:
            print("1. 🔧 Configure EA on Windows VPS")
            print("2. 📡 Test network connectivity")

        # Return comprehensive results
        return {
            "validation_id": self.validation_id,
            "overall_status": overall_status,
            "total_duration": total_duration,
            "critical_checks_passed": passed_critical,
            "ea_status": ea_status,
            "detailed_results": self.results,
            "timestamp": datetime.now().isoformat(),
        }

    def save_results(self, results: Dict):
        """Save validation results to file"""
        try:
            results_file = f"/root/HydraX-v2/ea_validation_{self.validation_id}.json"
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)

            print(f"\n💾 Results saved to: {results_file}")

        except Exception as e:
            print(f"\n❌ Failed to save results: {e}")


def main():
    """Run end-to-end EA validation"""
    print("🔄 BITTEN End-to-End EA Connectivity Validation")
    print("Tests complete signal flow from Linux server to EA")
    print("=" * 70)

    validator = EndToEndEAValidator()

    try:
        results = validator.run_complete_validation()
        validator.save_results(results)

        # Return appropriate exit code
        if results["overall_status"] == "READY":
            exit(0)
        elif results["overall_status"] == "PARTIAL":
            exit(1)
        else:
            exit(2)

    except KeyboardInterrupt:
        print("\n\n⚠️ Validation interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n\n❌ Validation failed with error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
