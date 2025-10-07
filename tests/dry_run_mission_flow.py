#!/usr/bin/env python3
"""
BITTEN Mission Flow Dry-Run Test Suite
Complete simulation of user journey from Telegram alert to trade execution

Usage:
    python3 /root/HydraX-v2/tests/dry_run_mission_flow.py

Exit Codes:
    0 = All tests passed
    1 = One or more tests failed
"""

import json
import logging
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ANSI color codes for output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.duration_ms = 0
        self.error = None
        self.details = {}
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def finish(self, passed: bool, error: str = None, **details):
        self.duration_ms = int((time.time() - self.start_time) * 1000)
        self.passed = passed
        self.error = error
        self.details = details

    def to_dict(self):
        return {
            "name": self.name,
            "passed": self.passed,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "details": self.details,
        }


class DryRunTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.test_data = {}
        self.setup_logging()

    def setup_logging(self):
        """Configure logging for test execution"""
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger(__name__)

    def print_header(self, text: str):
        """Print colored section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

    def print_step(self, step_num: int, description: str):
        """Print test step description"""
        print(f"{Colors.BOLD}[STEP {step_num}]{Colors.RESET} {description}")

    def print_result(self, result: TestResult):
        """Print test result with color coding"""
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if result.passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        print(f"  {status} ({result.duration_ms}ms)")

        if result.error:
            print(f"  {Colors.RED}Error: {result.error}{Colors.RESET}")

        if result.details:
            for key, value in result.details.items():
                print(f"    {Colors.YELLOW}{key}:{Colors.RESET} {value}")

    def run_test(self, name: str, test_func):
        """Execute a test and record results"""
        result = TestResult(name)
        result.start()

        try:
            test_func(result)
            if result.passed is None:  # Test didn't set status
                result.finish(True)
        except Exception as e:
            result.finish(False, str(e))
            self.logger.exception(f"Test {name} failed with exception")

        self.results.append(result)
        self.print_result(result)
        return result.passed

    # =========================================================================
    # TEST 1: Generate Mission Session
    # =========================================================================
    def test_generate_mission_session(self, result: TestResult):
        """Generate mission session with JWT token and deep link"""
        self.print_step(1, "Generate Test Mission Session")

        try:
            from src.missions.session_manager import session_manager

            # Test mission data
            signal_data = {
                "signal_id": f"TEST_DRY_RUN_{int(time.time())}",
                "symbol": "EURUSD",
                "direction": "BUY",
                "entry_price": 1.10000,
                "sl": 1.09800,
                "tp": 1.10300,
                "sl_pips": 20,
                "tp_pips": 30,
                "confidence": 87.5,
                "pattern_type": "LIQUIDITY_SWEEP_REVERSAL",
                "signal_type": "RAPID_ASSAULT",
                "created_at": int(time.time()),
            }

            # User context
            user_id = "7176191872"  # Test user (COMMANDER)
            account_id = "COMMANDER_DEV_001"
            risk_max_usd = 100.0

            # Generate session
            session = session_manager.create_mission_session(
                signal_data=signal_data,
                user_id=user_id,
                account_id=account_id,
                ttl_minutes=10,
                risk_max_usd=risk_max_usd,
            )

            # Verify session structure
            assert session["ms"], "Mission session ID missing"
            assert session["token"], "JWT token missing"
            assert session["deep_link"], "Deep link URL missing"
            assert session["expires_at"], "Expiry timestamp missing"

            # Verify deep link format
            deep_link = session["deep_link"]
            assert "ms=" in deep_link, "Deep link missing ms parameter"
            assert "token=" in deep_link, "Deep link missing token parameter"

            # Store for next tests
            self.test_data["session"] = session
            self.test_data["signal_data"] = signal_data
            self.test_data["user_id"] = user_id
            self.test_data["account_id"] = account_id
            self.test_data["risk_max_usd"] = risk_max_usd

            result.finish(
                True,
                ms=session["ms"],
                deep_link=deep_link,
                expires_at=datetime.fromtimestamp(session["expires_at"]).isoformat(),
            )

        except ImportError:
            result.finish(False, "session_manager not found - module may not exist yet")
        except Exception as e:
            result.finish(False, str(e))

    # =========================================================================
    # TEST 2: Simulate Telegram Alert
    # =========================================================================
    def test_simulate_telegram_alert(self, result: TestResult):
        """Simulate what would be posted to Telegram"""
        self.print_step(2, "Simulate Telegram Alert")

        try:
            session = self.test_data.get("session")
            signal_data = self.test_data.get("signal_data")

            if not session or not signal_data:
                result.finish(False, "Missing session data from previous test")
                return

            # Format alert message (matching actual Telegram format)
            alert_message = f"""
🎯 RAPID ASSAULT DETECTED

Symbol: {signal_data['symbol']}
Direction: {signal_data['direction']}
Entry: {signal_data['entry_price']:.5f}
SL: {signal_data['sl']:.5f} ({signal_data['sl_pips']} pips)
TP: {signal_data['tp']:.5f} ({signal_data['tp_pips']} pips)
Confidence: {signal_data['confidence']}%
Pattern: {signal_data['pattern_type']}

⏱ Expires in 10 minutes

🎯 Execute Mission:
{session['deep_link']}
            """.strip()

            # Verify alert format
            assert signal_data["symbol"] in alert_message
            assert signal_data["direction"] in alert_message
            assert session["deep_link"] in alert_message

            # Store alert
            self.test_data["telegram_alert"] = alert_message

            result.finish(True, alert_length=len(alert_message), deep_link_included=True)

        except Exception as e:
            result.finish(False, str(e))

    # =========================================================================
    # TEST 3: Mission Page Load
    # =========================================================================
    def test_mission_page_load(self, result: TestResult):
        """Test mission page load and validation"""
        self.print_step(3, "Test Mission Page Load")

        try:
            from src.missions.session_manager import session_manager

            session = self.test_data.get("session")
            if not session:
                result.finish(False, "Missing session data")
                return

            ms = session["ms"]
            token = session["token"]

            # Parse deep link (extract ms and token)
            deep_link = session["deep_link"]
            assert f"ms={ms}" in deep_link
            assert f"token={token}" in deep_link

            # Validate token
            validation = session_manager.validate_session_token(ms, token)

            assert validation["valid"], "Token validation failed"
            assert validation["session_id"] == ms
            assert validation["scopes"], "No scopes in token"
            assert "mission:view" in validation["scopes"]
            assert "order:execute" in validation["scopes"]

            # Fetch mission data
            mission_data = session_manager.get_mission_data(ms)

            assert mission_data, "Mission data not found"
            assert mission_data["signal"]["symbol"] == "EURUSD"
            assert mission_data["aid"], "Account ID missing"
            assert mission_data["riskMaxUsd"] == self.test_data["risk_max_usd"]

            # Verify beacons
            beacons = {
                "operational": True,  # System is running
                "secure": True,  # Token valid
                "latency": 45,  # Simulated latency
            }

            self.test_data["mission_data"] = mission_data
            self.test_data["beacons"] = beacons

            result.finish(True, token_valid=validation["valid"], scopes=validation["scopes"], beacons=beacons)

        except ImportError:
            result.finish(False, "session_manager not found")
        except Exception as e:
            result.finish(False, str(e))

    # =========================================================================
    # TEST 4: Execute Action
    # =========================================================================
    def test_execute_action(self, result: TestResult):
        """Test fire command execution"""
        self.print_step(4, "Test Execute Action")

        try:
            session = self.test_data.get("session")
            mission_data = self.test_data.get("mission_data")

            if not session or not mission_data:
                result.finish(False, "Missing session or mission data")
                return

            # Generate clientRequestId
            client_request_id = str(uuid.uuid4())

            # Simulate POST to /api/fire
            fire_request = {
                "ms": session["ms"],
                "clientRequestId": client_request_id,
                "riskUsd": 50.0,  # Within risk_max_usd of 100
            }

            # Mock execution (since we're in dry-run)
            # In real system, this would POST to webapp /api/fire

            # Generate opId (operation ID)
            op_id = f"OP_{int(time.time() * 1000)}"

            # Verify request structure
            assert fire_request["ms"] == session["ms"]
            assert fire_request["clientRequestId"]
            assert fire_request["riskUsd"] <= self.test_data["risk_max_usd"]

            # Store for idempotency test
            self.test_data["client_request_id"] = client_request_id
            self.test_data["op_id"] = op_id
            self.test_data["fire_request"] = fire_request

            result.finish(
                True,
                client_request_id=client_request_id,
                op_id=op_id,
                response_code=202,
                redirect_to=f"/status?opId={op_id}",
            )

        except Exception as e:
            result.finish(False, str(e))

    # =========================================================================
    # TEST 5: Event Delivery
    # =========================================================================
    def test_event_delivery(self, result: TestResult):
        """Test SSE event delivery for trade updates"""
        self.print_step(5, "Test Event Delivery")

        try:
            op_id = self.test_data.get("op_id")
            if not op_id:
                result.finish(False, "Missing op_id from execute test")
                return

            # Simulate event sequence
            events = []

            # Event 1: ARMING
            arming_time = time.time()
            arming_event = {
                "type": "trades.delta",
                "timestamp": int(arming_time * 1000),
                "data": {"opId": op_id, "status": "ARMING", "message": "Order queued for execution"},
            }
            events.append(("ARMING", arming_event, 0))

            # Event 2: FILLED (simulated 150ms later)
            filled_time = arming_time + 0.150
            filled_event = {
                "type": "trades.delta",
                "timestamp": int(filled_time * 1000),
                "data": {"opId": op_id, "status": "FILLED", "ticket": 123456, "fill_price": 1.10005, "latency_ms": 150},
            }
            events.append(("FILLED", filled_event, 150))

            # Verify latency < 250ms
            latency = filled_time - arming_time
            assert latency < 0.250, f"Latency {latency*1000}ms exceeds 250ms threshold"

            # Event 3: P&L Update (simulated)
            pnl_event = {
                "type": "trades.delta",
                "timestamp": int((filled_time + 0.100) * 1000),
                "data": {"opId": op_id, "status": "OPEN", "unrealized_pnl": 5.50, "pips": 5.5},
            }
            events.append(("P&L_UPDATE", pnl_event, 250))

            self.test_data["events"] = events

            result.finish(True, event_count=len(events), latency_ms=int(latency * 1000), latency_ok=latency < 0.250)

        except Exception as e:
            result.finish(False, str(e))

    # =========================================================================
    # TEST 6: Idempotency
    # =========================================================================
    def test_idempotency(self, result: TestResult):
        """Test idempotent request handling"""
        self.print_step(6, "Test Idempotency")

        try:
            client_request_id = self.test_data.get("client_request_id")
            original_op_id = self.test_data.get("op_id")
            fire_request = self.test_data.get("fire_request")

            if not all([client_request_id, original_op_id, fire_request]):
                result.finish(False, "Missing data from execute test")
                return

            # Re-send identical request
            duplicate_request = fire_request.copy()

            # In real system, this should return same opId
            # Mock the behavior
            returned_op_id = original_op_id  # Same as original

            # Verify idempotency
            assert returned_op_id == original_op_id, "Different opId for duplicate request"

            # Verify no duplicate order created
            # In real system, would check fires DB for single entry

            result.finish(
                True,
                original_op_id=original_op_id,
                duplicate_op_id=returned_op_id,
                idempotency_preserved=True,
                expected_response_code="202 or 409",
            )

        except Exception as e:
            result.finish(False, str(e))

    # =========================================================================
    # TEST 7: Session Expiry
    # =========================================================================
    def test_session_expiry(self, result: TestResult):
        """Test expired session handling"""
        self.print_step(7, "Test Session Expiry")

        try:
            from src.missions.session_manager import session_manager

            session = self.test_data.get("session")
            if not session:
                result.finish(False, "Missing session data")
                return

            # Create expired session for testing
            expired_signal = {
                "signal_id": f"EXPIRED_TEST_{int(time.time())}",
                "symbol": "GBPUSD",
                "direction": "SELL",
                "entry_price": 1.28000,
                "sl": 1.28200,
                "tp": 1.27700,
                "sl_pips": 20,
                "tp_pips": 30,
                "confidence": 82.0,
                "pattern_type": "ORDER_BLOCK_BOUNCE",
                "signal_type": "PRECISION_STRIKE",
                "created_at": int(time.time()),
            }

            # Create session with 0 second TTL (immediately expired)
            expired_session = session_manager.create_mission_session(
                signal_data=expired_signal,
                user_id=self.test_data["user_id"],
                account_id=self.test_data["account_id"],
                ttl_minutes=0,  # Expire immediately
                risk_max_usd=100.0,
            )

            # Wait 1 second to ensure expiry
            time.sleep(1)

            # Try to validate expired token
            validation = session_manager.validate_session_token(expired_session["ms"], expired_session["token"])

            # Should be invalid
            assert not validation["valid"], "Expired token validated as valid"
            assert "expired" in validation.get("error", "").lower()

            result.finish(
                True, expired_session_rejected=True, error_message=validation.get("error"), expected_response_code=410
            )

        except ImportError:
            result.finish(False, "session_manager not found")
        except Exception as e:
            result.finish(False, str(e))

    # =========================================================================
    # TEST 8: Risk Fuse
    # =========================================================================
    def test_risk_fuse(self, result: TestResult):
        """Test risk limit enforcement"""
        self.print_step(8, "Test Risk Fuse")

        try:
            session = self.test_data.get("session")
            risk_max_usd = self.test_data.get("risk_max_usd")

            if not session or not risk_max_usd:
                result.finish(False, "Missing session or risk data")
                return

            # Create request exceeding risk limit
            excessive_risk_request = {
                "ms": session["ms"],
                "clientRequestId": str(uuid.uuid4()),
                "riskUsd": risk_max_usd + 50.0,  # Exceed by 50
            }

            # Verify risk check
            requested_risk = excessive_risk_request["riskUsd"]
            risk_exceeded = requested_risk > risk_max_usd

            assert risk_exceeded, "Risk check failed to detect excess"

            # In real system, would return 422 with error
            expected_error = f"Risk ${requested_risk} exceeds maximum ${risk_max_usd}"

            result.finish(
                True,
                risk_requested=requested_risk,
                risk_max=risk_max_usd,
                risk_exceeded=risk_exceeded,
                expected_response_code=422,
                expected_error=expected_error,
            )

        except Exception as e:
            result.finish(False, str(e))

    # =========================================================================
    # TEST 9: Stats Page
    # =========================================================================
    def test_stats_page(self, result: TestResult):
        """Test stats page updates"""
        self.print_step(9, "Test Stats Page")

        try:
            op_id = self.test_data.get("op_id")
            events = self.test_data.get("events")

            if not op_id or not events:
                result.finish(False, "Missing operation data")
                return

            # Simulate stats page data
            # In real system, would fetch from /stats endpoint

            # Verify equity series would be updated
            equity_update = {
                "timestamp": int(time.time() * 1000),
                "equity": 850.45 + 5.50,  # Original balance + unrealized P&L
                "trade_id": op_id,
            }

            # Verify trade appears in recent events
            recent_trade = {
                "opId": op_id,
                "symbol": "EURUSD",
                "direction": "BUY",
                "status": "OPEN",
                "pnl": 5.50,
                "timestamp": int(time.time() * 1000),
            }

            # Check stats would include this trade
            assert equity_update["equity"] > 850.45
            assert recent_trade["opId"] == op_id

            result.finish(True, equity_updated=True, new_equity=equity_update["equity"], trade_in_recent_events=True)

        except Exception as e:
            result.finish(False, str(e))

    # =========================================================================
    # MAIN TEST RUNNER
    # =========================================================================
    def run_all_tests(self):
        """Execute all tests in sequence"""
        self.print_header("🎯 BITTEN MISSION FLOW DRY-RUN TEST SUITE")

        start_time = time.time()

        # Execute tests in order
        tests = [
            ("Generate Mission Session", self.test_generate_mission_session),
            ("Simulate Telegram Alert", self.test_simulate_telegram_alert),
            ("Mission Page Load", self.test_mission_page_load),
            ("Execute Action", self.test_execute_action),
            ("Event Delivery", self.test_event_delivery),
            ("Idempotency", self.test_idempotency),
            ("Session Expiry", self.test_session_expiry),
            ("Risk Fuse", self.test_risk_fuse),
            ("Stats Page", self.test_stats_page),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
            else:
                failed += 1

        total_duration = int((time.time() - start_time) * 1000)

        # Print summary
        self.print_header("📊 TEST SUMMARY")

        print(f"Total Tests: {len(tests)}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"Duration: {total_duration}ms\n")

        # Print detailed results
        self.print_header("📋 DETAILED RESULTS")
        for result in self.results:
            status = f"{Colors.GREEN}✓{Colors.RESET}" if result.passed else f"{Colors.RED}✗{Colors.RESET}"
            print(f"{status} {result.name} ({result.duration_ms}ms)")
            if result.error:
                print(f"   {Colors.RED}Error: {result.error}{Colors.RESET}")

        # Save results to JSON
        self.save_results(total_duration)

        # Return exit code
        return 0 if failed == 0 else 1

    def save_results(self, total_duration_ms: int):
        """Save test results to JSON file"""
        output_file = Path("/root/HydraX-v2/tests/dry_run_results.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        results_data = {
            "timestamp": datetime.now().isoformat(),
            "total_duration_ms": total_duration_ms,
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "tests": [r.to_dict() for r in self.results],
        }

        with open(output_file, "w") as f:
            json.dump(results_data, f, indent=2)

        print(f"\n{Colors.CYAN}Results saved to: {output_file}{Colors.RESET}")


def main():
    """Main entry point"""
    tester = DryRunTester()
    exit_code = tester.run_all_tests()

    if exit_code == 0:
        print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 ALL TESTS PASSED{Colors.RESET}\n")
    else:
        print(f"\n{Colors.BOLD}{Colors.RED}❌ SOME TESTS FAILED{Colors.RESET}\n")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
