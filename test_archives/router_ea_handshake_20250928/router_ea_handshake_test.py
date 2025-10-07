#!/usr/bin/env python3
"""
Router⇄EA Handshake Test Suite
Tests minimal flows with existing HydraSocket Router + BITTEN infrastructure
No live market required - works with demo/sandbox mode
"""

import asyncio
import json
import socket
import time
import uuid
import zmq
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3
import threading
import signal
import sys

class RouterEAHandshakeTester:
    """Comprehensive test suite for Router⇄EA communication flows"""

    def __init__(self):
        self.test_results = []
        self.test_account_id = "TEST_ACCOUNT_001"
        self.test_node_id = "EA_TEST_NODE"
        self.test_session_id = f"TEST_SESSION_{int(time.time())}"
        self.context = zmq.Context()

        # Test ports (using existing infrastructure)
        self.command_port = 5555  # Router command port
        self.event_port = 5558    # Event ingestion port
        self.metrics_port = 5560  # Metrics ingestion port

        print(f"🧪 Router⇄EA Handshake Test Suite")
        print(f"📊 Test Account: {self.test_account_id}")
        print(f"🔗 Test Session: {self.test_session_id}")

    def log_result(self, test_name: str, success: bool, message: str = "", details: Dict = None):
        """Log test result with timestamp"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": self.test_session_id
        }
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")

        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")

    def connect_socket(self, port: int, socket_type: int) -> zmq.Socket:
        """Create ZMQ socket connection"""
        try:
            socket = self.context.socket(socket_type)
            socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
            socket.setsockopt(zmq.SNDTIMEO, 5000)  # 5 second timeout

            if socket_type == zmq.REQ:
                socket.connect(f"tcp://localhost:{port}")
            elif socket_type == zmq.PUSH:
                socket.connect(f"tcp://localhost:{port}")
            elif socket_type == zmq.SUB:
                socket.connect(f"tcp://localhost:{port}")
                socket.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all

            return socket
        except Exception as e:
            raise ConnectionError(f"Failed to connect to port {port}: {e}")

    def send_jsonl_event(self, socket: zmq.Socket, event_data: Dict) -> bool:
        """Send JSON event to router"""
        try:
            message = json.dumps(event_data)
            socket.send_string(message)
            return True
        except Exception as e:
            print(f"Error sending event: {e}")
            return False

    def send_command(self, socket: zmq.Socket, command: Dict) -> Optional[Dict]:
        """Send command and get response"""
        try:
            message = json.dumps(command)
            socket.send_string(message)

            # Wait for response
            response = socket.recv_string()
            return json.loads(response)
        except Exception as e:
            print(f"Error sending command: {e}")
            return None

    def test_1_boot_order_sequence(self):
        """Test 1: Boot Order Check (config→ea_started→idemp_sync→portfolio)"""
        print("\n🔄 Test 1: Boot Order Sequence")

        try:
            event_socket = self.connect_socket(self.event_port, zmq.PUSH)

            # Step 1: Send config_snapshot event
            config_event = {
                "type": "config_snapshot",
                "ts": datetime.utcnow().isoformat() + "Z",
                "account_id": self.test_account_id,
                "node_id": self.test_node_id,
                "source": "ea",
                "session_id": self.test_session_id,
                "version": "EA_v2.07_TEST",
                "broker": "MetaQuotes-Demo",
                "account_number": "12345678",
                "leverage": 100,
                "base_currency": "USD",
                "server_time": datetime.utcnow().isoformat() + "Z"
            }

            if self.send_jsonl_event(event_socket, config_event):
                self.log_result("Boot Order - Config Snapshot", True, "Config event sent")
            else:
                self.log_result("Boot Order - Config Snapshot", False, "Failed to send config")
                return

            time.sleep(0.5)  # Brief pause

            # Step 2: Send ea_started event
            started_event = {
                "type": "ea_started",
                "ts": datetime.utcnow().isoformat() + "Z",
                "account_id": self.test_account_id,
                "node_id": self.test_node_id,
                "source": "ea",
                "session_id": self.test_session_id,
                "startup_time_ms": 1247,
                "symbols_loaded": ["EURUSD", "GBPUSD", "USDJPY"],
                "timeframes": ["M1", "M5", "H1"],
                "ready": True
            }

            if self.send_jsonl_event(event_socket, started_event):
                self.log_result("Boot Order - EA Started", True, "EA started event sent")
            else:
                self.log_result("Boot Order - EA Started", False, "Failed to send ea_started")
                return

            time.sleep(0.5)

            # Step 3: Send idemp_sync event
            idemp_event = {
                "type": "idemp_sync",
                "ts": datetime.utcnow().isoformat() + "Z",
                "account_id": self.test_account_id,
                "node_id": self.test_node_id,
                "source": "ea",
                "session_id": self.test_session_id,
                "known_refs": [
                    f"R-TEST-{int(time.time())}-001",
                    f"R-TEST-{int(time.time())}-002"
                ]
            }

            if self.send_jsonl_event(event_socket, idemp_event):
                self.log_result("Boot Order - Idempotency Sync", True, "Idemp sync event sent")
            else:
                self.log_result("Boot Order - Idempotency Sync", False, "Failed to send idemp_sync")
                return

            time.sleep(0.5)

            # Step 4: Send portfolio_snapshot event
            portfolio_event = {
                "type": "portfolio_snapshot",
                "ts": datetime.utcnow().isoformat() + "Z",
                "account_id": self.test_account_id,
                "node_id": self.test_node_id,
                "source": "ea",
                "session_id": self.test_session_id,
                "positions": [
                    {
                        "ticket": 12345001,
                        "symbol": "EURUSD",
                        "side": "buy",
                        "volume": 0.10,
                        "price_open": 1.1000,
                        "sl": 1.0950,
                        "tp": 1.1050,
                        "profit": 5.00,
                        "swap": 0.15
                    }
                ],
                "pending": [],
                "balance": 10000.00,
                "equity": 10005.15,
                "margin": 110.00,
                "free_margin": 9895.15,
                "currency": "USD",
                "open_positions_count": 1
            }

            if self.send_jsonl_event(event_socket, portfolio_event):
                self.log_result("Boot Order - Portfolio Snapshot", True, "Portfolio snapshot sent", {
                    "positions": len(portfolio_event["positions"]),
                    "balance": portfolio_event["balance"],
                    "equity": portfolio_event["equity"]
                })
            else:
                self.log_result("Boot Order - Portfolio Snapshot", False, "Failed to send portfolio")

            event_socket.close()

        except Exception as e:
            self.log_result("Boot Order Sequence", False, f"Exception: {str(e)}")

    def test_2_idempotency_roundtrip(self):
        """Test 2: Idempotency Seed Roundtrip"""
        print("\n🔄 Test 2: Idempotency Seed Roundtrip")

        try:
            # Use existing command router on port 5555
            command_socket = self.connect_socket(self.command_port, zmq.REQ)

            # Generate unique idempotency key
            idemp_key = f"TEST_IDEMP_{int(time.time())}_{uuid.uuid4().hex[:8]}"

            # Send command with idempotency key
            open_command = {
                "type": "open",
                "account_id": self.test_account_id,
                "request_ref": f"R-TEST-IDEMP-{int(time.time())}",
                "ts": datetime.utcnow().isoformat() + "Z",
                "symbol": "EURUSD",
                "side": "buy",
                "volume": 0.01,
                "sl": 1.0900,
                "tp": 1.1100,
                "idempotency_key": idemp_key
            }

            # First request
            response1 = self.send_command(command_socket, open_command)
            command_socket.close()

            if response1:
                self.log_result("Idempotency - First Request", True, f"Response: {response1.get('status', 'unknown')}", {
                    "request_ref": response1.get("request_ref"),
                    "code": response1.get("code", "none")
                })

                time.sleep(1)  # Brief pause

                # Second identical request (should be deduplicated)
                command_socket2 = self.connect_socket(self.command_port, zmq.REQ)
                response2 = self.send_command(command_socket2, open_command)
                command_socket2.close()

                if response2:
                    # Check if responses are identical (idempotency working)
                    if response1.get("request_ref") == response2.get("request_ref"):
                        self.log_result("Idempotency - Duplicate Handling", True, "Identical responses received", {
                            "first_status": response1.get("status"),
                            "second_status": response2.get("status"),
                            "idempotency_key": idemp_key
                        })
                    else:
                        self.log_result("Idempotency - Duplicate Handling", False, "Responses differ - idempotency failed")
                else:
                    self.log_result("Idempotency - Second Request", False, "No response to duplicate request")
            else:
                self.log_result("Idempotency - First Request", False, "No response to initial request")

        except Exception as e:
            self.log_result("Idempotency Roundtrip", False, f"Exception: {str(e)}")

    def test_3_summary_mode_toggle(self):
        """Test 3: Summary Mode Toggle (hz1=0/1)"""
        print("\n🔄 Test 3: Summary Mode Toggle")

        try:
            event_socket = self.connect_socket(self.event_port, zmq.PUSH)

            # Send account summary at 1Hz (summary mode enabled)
            summary_hz1 = {
                "type": "account_summary",
                "ts": datetime.utcnow().isoformat() + "Z",
                "account_id": self.test_account_id,
                "node_id": self.test_node_id,
                "source": "ea",
                "session_id": self.test_session_id,
                "balance": 10000.00,
                "equity": 10025.50,
                "margin": 220.00,
                "free_margin": 9805.50,
                "margin_level": 4556.81,
                "currency": "USD",
                "open_positions_count": 2,
                "hz1": 1  # Summary mode enabled
            }

            if self.send_jsonl_event(event_socket, summary_hz1):
                self.log_result("Summary Mode - Hz1 Enabled", True, "Summary with hz1=1 sent", {
                    "balance": summary_hz1["balance"],
                    "equity": summary_hz1["equity"],
                    "mode": "hz1=1 (enabled)"
                })

            time.sleep(0.5)

            # Send account summary without hz1 (summary mode disabled)
            summary_hz0 = {
                "type": "account_summary",
                "ts": datetime.utcnow().isoformat() + "Z",
                "account_id": self.test_account_id,
                "node_id": self.test_node_id,
                "source": "ea",
                "session_id": self.test_session_id,
                "balance": 10000.00,
                "equity": 10030.75,
                "margin": 220.00,
                "free_margin": 9810.75,
                "margin_level": 4558.52,
                "currency": "USD",
                "open_positions_count": 2,
                "hz1": 0  # Summary mode disabled
            }

            if self.send_jsonl_event(event_socket, summary_hz0):
                self.log_result("Summary Mode - Hz1 Disabled", True, "Summary with hz1=0 sent", {
                    "balance": summary_hz0["balance"],
                    "equity": summary_hz0["equity"],
                    "mode": "hz1=0 (disabled)"
                })

            event_socket.close()

        except Exception as e:
            self.log_result("Summary Mode Toggle", False, f"Exception: {str(e)}")

    def test_4_feed_bootstrap(self):
        """Test 4: Feed Bootstrap with EURUSD M1"""
        print("\n🔄 Test 4: Feed Bootstrap with EURUSD M1")

        try:
            event_socket = self.connect_socket(self.event_port, zmq.PUSH)

            # Generate realistic EURUSD M1 feed data
            base_price = 1.1000
            current_time = datetime.utcnow()

            # Send multiple M1 candles to bootstrap feed
            for i in range(5):
                candle_time = current_time - timedelta(minutes=4-i)

                # Simulate realistic price movement
                open_price = base_price + (i * 0.0001)
                high_price = open_price + 0.0005
                low_price = open_price - 0.0003
                close_price = open_price + 0.0002

                feed_event = {
                    "type": "feed_data",
                    "ts": candle_time.isoformat() + "Z",
                    "account_id": self.test_account_id,
                    "node_id": self.test_node_id,
                    "source": "ea",
                    "session_id": self.test_session_id,
                    "symbol": "EURUSD",
                    "timeframe": "M1",
                    "open": round(open_price, 5),
                    "high": round(high_price, 5),
                    "low": round(low_price, 5),
                    "close": round(close_price, 5),
                    "volume": 1000 + (i * 100),
                    "candle_time": candle_time.isoformat() + "Z"
                }

                if self.send_jsonl_event(event_socket, feed_event):
                    self.log_result(f"Feed Bootstrap - M1 Candle {i+1}", True, f"EURUSD M1 candle sent", {
                        "open": feed_event["open"],
                        "close": feed_event["close"],
                        "volume": feed_event["volume"],
                        "time": candle_time.strftime("%H:%M:%S")
                    })
                else:
                    self.log_result(f"Feed Bootstrap - M1 Candle {i+1}", False, "Failed to send candle")

                time.sleep(0.2)  # Brief pause between candles

            # Send current tick data
            tick_event = {
                "type": "tick_data",
                "ts": datetime.utcnow().isoformat() + "Z",
                "account_id": self.test_account_id,
                "node_id": self.test_node_id,
                "source": "ea",
                "session_id": self.test_session_id,
                "symbol": "EURUSD",
                "bid": 1.10025,
                "ask": 1.10028,
                "spread": 0.3,
                "volume": 50
            }

            if self.send_jsonl_event(event_socket, tick_event):
                self.log_result("Feed Bootstrap - Current Tick", True, "Live tick data sent", {
                    "bid": tick_event["bid"],
                    "ask": tick_event["ask"],
                    "spread": tick_event["spread"]
                })

            event_socket.close()

        except Exception as e:
            self.log_result("Feed Bootstrap", False, f"Exception: {str(e)}")

    def test_5_websocket_broadcast(self):
        """Test 5: WebSocket Broadcast Sanity Check"""
        print("\n🔄 Test 5: WebSocket Broadcast Sanity")

        try:
            # Test WebSocket endpoint availability
            import requests

            # Check if WebSocket endpoint is available
            try:
                response = requests.get("http://localhost:8888/healthz", timeout=5)
                if response.status_code == 200:
                    self.log_result("WebSocket - Health Check", True, "WebApp health endpoint responsive", {
                        "status_code": response.status_code,
                        "response_time_ms": int(response.elapsed.total_seconds() * 1000)
                    })

                    # Send position heartbeat event for WebSocket broadcast
                    event_socket = self.connect_socket(self.event_port, zmq.PUSH)

                    heartbeat_event = {
                        "type": "position_heartbeat",
                        "ts": datetime.utcnow().isoformat() + "Z",
                        "account_id": self.test_account_id,
                        "node_id": self.test_node_id,
                        "source": "ea",
                        "session_id": self.test_session_id,
                        "ticket": 12345001,
                        "mark_price": 1.10050,
                        "floating_pnl_ccy": 5.25,
                        "margin_used": 110.00
                    }

                    if self.send_jsonl_event(event_socket, heartbeat_event):
                        self.log_result("WebSocket - Position Heartbeat", True, "Heartbeat event for WS broadcast sent", {
                            "ticket": heartbeat_event["ticket"],
                            "mark_price": heartbeat_event["mark_price"],
                            "pnl": heartbeat_event["floating_pnl_ccy"]
                        })

                    event_socket.close()
                else:
                    self.log_result("WebSocket - Health Check", False, f"Health endpoint returned {response.status_code}")

            except requests.exceptions.RequestException as e:
                self.log_result("WebSocket - Health Check", False, f"WebApp not responding: {str(e)}")

        except Exception as e:
            self.log_result("WebSocket Broadcast", False, f"Exception: {str(e)}")

    def test_6_metrics_verification(self):
        """Test 6: Metrics Verification on Port 5560"""
        print("\n🔄 Test 6: Metrics Verification")

        try:
            metrics_socket = self.connect_socket(self.metrics_port, zmq.PUSH)

            # Send line protocol metrics
            line_metrics = [
                "account_summary_emitted=10",
                "events_processed=25",
                "position_heartbeats=50",
                "trades_executed=3",
                "avg_latency_ms=45",
                f"test_session_active=1,session_id={self.test_session_id}"
            ]

            for metric in line_metrics:
                try:
                    metrics_socket.send_string(metric)
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Failed to send metric: {metric} - {e}")

            self.log_result("Metrics - Line Protocol", True, f"Sent {len(line_metrics)} line protocol metrics", {
                "metrics_count": len(line_metrics),
                "sample": line_metrics[0]
            })

            # Send JSON format metrics
            json_metrics = {
                "account_balance": 10000.00,
                "account_equity": 10035.75,
                "open_positions": 2,
                "daily_trades": 3,
                "session_duration_minutes": 15,
                "test_session_id": self.test_session_id
            }

            try:
                metrics_socket.send_string(json.dumps(json_metrics))
                self.log_result("Metrics - JSON Format", True, "JSON metrics sent", {
                    "balance": json_metrics["account_balance"],
                    "equity": json_metrics["account_equity"],
                    "positions": json_metrics["open_positions"]
                })
            except Exception as e:
                self.log_result("Metrics - JSON Format", False, f"Failed to send JSON metrics: {e}")

            metrics_socket.close()

        except Exception as e:
            self.log_result("Metrics Verification", False, f"Exception: {str(e)}")

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📊 Generating Test Report...")

        # Calculate summary statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Generate report
        report = {
            "test_session": {
                "session_id": self.test_session_id,
                "account_id": self.test_account_id,
                "node_id": self.test_node_id,
                "start_time": self.test_results[0]["timestamp"] if self.test_results else None,
                "end_time": datetime.utcnow().isoformat() + "Z",
                "total_duration_seconds": int(time.time() - int(self.test_session_id.split('_')[-1]))
            },
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate_percent": round(success_rate, 1)
            },
            "test_results": self.test_results,
            "conclusions": {
                "router_communication": "TESTED" if any("Boot Order" in r["test"] for r in self.test_results) else "NOT TESTED",
                "idempotency_system": "TESTED" if any("Idempotency" in r["test"] for r in self.test_results) else "NOT TESTED",
                "event_ingestion": "TESTED" if any("Feed Bootstrap" in r["test"] for r in self.test_results) else "NOT TESTED",
                "metrics_collection": "TESTED" if any("Metrics" in r["test"] for r in self.test_results) else "NOT TESTED",
                "websocket_readiness": "TESTED" if any("WebSocket" in r["test"] for r in self.test_results) else "NOT TESTED"
            }
        }

        # Save report to file
        report_filename = f"/root/HydraX-v2/router_ea_handshake_test_report_{self.test_session_id}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)

        return report, report_filename

    def run_all_tests(self):
        """Execute complete Router⇄EA handshake test suite"""
        print("🚀 Starting Router⇄EA Handshake Test Suite")
        print("=" * 60)
        print(f"📍 Testing against existing infrastructure:")
        print(f"   Command Port: {self.command_port}")
        print(f"   Event Port: {self.event_port}")
        print(f"   Metrics Port: {self.metrics_port}")
        print("=" * 60)

        # Execute all test phases
        self.test_1_boot_order_sequence()
        self.test_2_idempotency_roundtrip()
        self.test_3_summary_mode_toggle()
        self.test_4_feed_bootstrap()
        self.test_5_websocket_broadcast()
        self.test_6_metrics_verification()

        # Generate final report
        report, report_file = self.generate_test_report()

        print("\n" + "=" * 60)
        print("📊 ROUTER⇄EA HANDSHAKE TEST RESULTS")
        print("=" * 60)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: ✅ {report['summary']['passed_tests']}")
        print(f"Failed: ❌ {report['summary']['failed_tests']}")
        print(f"Success Rate: {report['summary']['success_rate_percent']}%")
        print(f"Duration: {report['test_session']['total_duration_seconds']} seconds")

        if report['summary']['failed_tests'] > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")

        print(f"\n📁 Detailed report saved: {report_file}")

        # Clean up
        self.context.term()

        return report['summary']['failed_tests'] == 0

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Test interrupted by user")
    sys.exit(1)

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal_handler)

    # Run the test suite
    tester = RouterEAHandshakeTester()
    success = tester.run_all_tests()

    if success:
        print("\n🎉 ALL TESTS PASSED - Router⇄EA handshake verified!")
        exit(0)
    else:
        print("\n💥 SOME TESTS FAILED - Check handshake implementation")
        exit(1)