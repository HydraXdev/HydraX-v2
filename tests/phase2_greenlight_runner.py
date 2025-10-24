#!/usr/bin/env python3
"""
BITTEN v2.0 PHASE 2 - Automated Green-Light Test Runner

Executes all Commander-requested validation checks automatically.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple


class Phase2GreenlightRunner:
    """Automated Phase 2 green-light validation"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "overall_status": "PENDING"
        }
        self.failures = []

    def run_all_checks(self) -> Dict:
        """Execute all validation checks"""
        print("🚀 BITTEN v2.0 PHASE 2 GREEN-LIGHT VALIDATION")
        print("=" * 70)
        print(f"Started: {self.results['timestamp']}")
        print()

        # Run checks in sequence
        self.check_parity_suite()
        self.check_load_tests()
        self.check_service_health()
        self.check_rbac_security()
        self.check_reconciliation()
        self.check_archive_isolation()

        # Determine overall status
        self.results["overall_status"] = "PASS" if len(self.failures) == 0 else "FAIL"
        self.results["failures"] = self.failures

        self.print_summary()
        return self.results

    def check_parity_suite(self):
        """Check 1: Run parity tests"""
        print("\n📊 CHECK 1: Parity Suite (100% match required)")
        print("-" * 70)

        try:
            # Run parity runner
            result = subprocess.run(
                ["python3", "/root/HydraX-v2/tests/parity/parity_runner.py",
                 "--output", "/tmp/parity_results.json"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                # Parse results
                with open("/tmp/parity_results.json", 'r') as f:
                    parity_data = json.load(f)

                signals_match = parity_data.get("signals_pass", False)
                fires_match = parity_data.get("fires_pass", False)
                positions_match = parity_data.get("positions_pass", False)

                self.results["checks"]["parity"] = {
                    "status": "PASS" if all([signals_match, fires_match, positions_match]) else "FAIL",
                    "signals_match": signals_match,
                    "fires_match": fires_match,
                    "positions_match": positions_match
                }

                if self.results["checks"]["parity"]["status"] == "FAIL":
                    self.failures.append("Parity suite: Not all comparisons matched")

                print(f"  Signals: {'✅ PASS' if signals_match else '❌ FAIL'}")
                print(f"  Fires: {'✅ PASS' if fires_match else '❌ FAIL'}")
                print(f"  Positions: {'✅ PASS' if positions_match else '❌ FAIL'}")
            else:
                self.results["checks"]["parity"] = {"status": "ERROR", "error": result.stderr}
                self.failures.append(f"Parity suite failed to run: {result.stderr}")
                print(f"  ❌ ERROR: {result.stderr}")

        except Exception as e:
            self.results["checks"]["parity"] = {"status": "ERROR", "error": str(e)}
            self.failures.append(f"Parity suite exception: {e}")
            print(f"  ❌ EXCEPTION: {e}")

    def check_load_tests(self):
        """Check 2: Run load tests with SLO validation"""
        print("\n⚡ CHECK 2: Load Tests (P95 SLOs required)")
        print("-" * 70)

        try:
            result = subprocess.run(
                ["python3", "/root/HydraX-v2/tests/load/load_runner.py",
                 "--output", "/tmp/load_results.json"],
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                with open("/tmp/load_results.json", 'r') as f:
                    load_data = json.load(f)

                perf = load_data.get("summary", {}).get("performance_summary", {})

                fire_p95 = perf.get("fire_p95_ms", 9999)
                signal_p95 = perf.get("signal_p95_ms", 9999)
                ws_p95 = perf.get("websocket_p95_ms", 9999)

                fire_pass = fire_p95 < 100
                signal_pass = signal_p95 < 50
                ws_pass = ws_p95 < 250

                self.results["checks"]["load_tests"] = {
                    "status": "PASS" if all([fire_pass, signal_pass, ws_pass]) else "FAIL",
                    "fire_p95_ms": fire_p95,
                    "signal_p95_ms": signal_p95,
                    "websocket_p95_ms": ws_p95,
                    "fire_pass": fire_pass,
                    "signal_pass": signal_pass,
                    "websocket_pass": ws_pass
                }

                if not all([fire_pass, signal_pass, ws_pass]):
                    self.failures.append("Load tests: SLO thresholds not met")

                print(f"  Fire P95: {fire_p95:.1f}ms {'✅ <100ms' if fire_pass else '❌ ≥100ms'}")
                print(f"  Signal P95: {signal_p95:.1f}ms {'✅ <50ms' if signal_pass else '❌ ≥50ms'}")
                print(f"  WebSocket P95: {ws_p95:.1f}ms {'✅ <250ms' if ws_pass else '❌ ≥250ms'}")
            else:
                self.results["checks"]["load_tests"] = {"status": "ERROR"}
                self.failures.append("Load tests failed to run")
                print(f"  ❌ ERROR: {result.stderr}")

        except Exception as e:
            self.results["checks"]["load_tests"] = {"status": "ERROR", "error": str(e)}
            self.failures.append(f"Load tests exception: {e}")
            print(f"  ❌ EXCEPTION: {e}")

    def check_service_health(self):
        """Check 3: Service health endpoints"""
        print("\n🏥 CHECK 3: Service Health & Alerting")
        print("-" * 70)

        services = [
            ("zmq_gateway", "http://localhost:9091/health/readiness"),
            ("signal_engine", "http://localhost:9092/health/readiness"),
            ("fire_service", "http://localhost:8890/health"),
            ("api_server", "http://localhost:8888/health"),
            ("analytics_worker", "http://localhost:9093/health/readiness")
        ]

        health_results = {}
        all_healthy = True

        for service_name, url in services:
            try:
                result = subprocess.run(
                    ["curl", "-s", "-f", url],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                healthy = result.returncode == 0
                health_results[service_name] = healthy
                all_healthy = all_healthy and healthy

                print(f"  {service_name}: {'✅ healthy' if healthy else '❌ unhealthy'}")

            except Exception as e:
                health_results[service_name] = False
                all_healthy = False
                print(f"  {service_name}: ❌ ERROR ({e})")

        self.results["checks"]["service_health"] = {
            "status": "PASS" if all_healthy else "FAIL",
            "services": health_results
        }

        if not all_healthy:
            self.failures.append("Service health: Not all services healthy")

    def check_rbac_security(self):
        """Check 4: RBAC and rate limiting"""
        print("\n🔒 CHECK 4: RBAC + Rate Limits")
        print("-" * 70)

        # Test unauthenticated request
        try:
            result = subprocess.run(
                ["curl", "-s", "-w", "%{http_code}", "-o", "/dev/null",
                 "-X", "POST", "http://localhost:8888/api/fire"],
                capture_output=True,
                text=True,
                timeout=5
            )

            status_code = result.stdout.strip()
            rbac_active = status_code == "401"

            print(f"  RBAC enforcement: {'✅ 401 Unauthorized' if rbac_active else '❌ ' + status_code}")

            self.results["checks"]["rbac"] = {
                "status": "PASS" if rbac_active else "FAIL",
                "unauthenticated_blocked": rbac_active
            }

            if not rbac_active:
                self.failures.append("RBAC: Unauthenticated requests not blocked")

        except Exception as e:
            self.results["checks"]["rbac"] = {"status": "ERROR", "error": str(e)}
            self.failures.append(f"RBAC check exception: {e}")
            print(f"  ❌ EXCEPTION: {e}")

    def check_reconciliation(self):
        """Check 5: Postgres ↔ Firestore reconciliation"""
        print("\n🌙 CHECK 5: Nightly Reconciliation")
        print("-" * 70)

        try:
            result = subprocess.run(
                ["python3", "/root/HydraX-v2/tests/validation/reconciliation.py"],
                capture_output=True,
                text=True,
                timeout=60
            )

            recon_pass = result.returncode == 0

            print(f"  Reconciliation: {'✅ PASS' if recon_pass else '❌ FAIL'}")

            self.results["checks"]["reconciliation"] = {
                "status": "PASS" if recon_pass else "FAIL"
            }

            if not recon_pass:
                self.failures.append("Reconciliation: Data mismatch detected")

        except Exception as e:
            self.results["checks"]["reconciliation"] = {"status": "ERROR", "error": str(e)}
            self.failures.append(f"Reconciliation exception: {e}")
            print(f"  ❌ EXCEPTION: {e}")

    def check_archive_isolation(self):
        """Check 6: Archive imports verification"""
        print("\n📦 CHECK 6: Archive Isolation")
        print("-" * 70)

        try:
            # Check for archive imports
            result = subprocess.run(
                ["grep", "-r", "import.*archive", "/root/HydraX-v2/services/"],
                capture_output=True,
                text=True
            )

            no_imports = result.returncode != 0

            print(f"  No archive imports: {'✅ verified' if no_imports else '❌ found imports'}")

            self.results["checks"]["archive_isolation"] = {
                "status": "PASS" if no_imports else "FAIL",
                "no_imports": no_imports
            }

            if not no_imports:
                self.failures.append("Archive isolation: Found archive imports in services")

        except Exception as e:
            self.results["checks"]["archive_isolation"] = {"status": "ERROR", "error": str(e)}
            print(f"  ❌ EXCEPTION: {e}")

    def print_summary(self):
        """Print final summary"""
        print("\n" + "=" * 70)
        print("📋 PHASE 2 GREEN-LIGHT VALIDATION SUMMARY")
        print("=" * 70)

        print(f"\nOverall Status: {self.results['overall_status']}")
        print(f"Checks Run: {len(self.results['checks'])}")
        print(f"Failures: {len(self.failures)}")

        if self.failures:
            print("\n❌ FAILURES:")
            for failure in self.failures:
                print(f"  - {failure}")
        else:
            print("\n✅ ALL CHECKS PASSED - READY FOR PHASE 2")

        print("\n" + "=" * 70)

        # Save results
        output_file = f"/tmp/phase2_greenlight_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nResults saved to: {output_file}")


def main():
    """Main execution"""
    import sys

    runner = Phase2GreenlightRunner()
    results = runner.run_all_checks()

    sys.exit(0 if results["overall_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
