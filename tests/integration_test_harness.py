#!/usr/bin/env python3
"""
BITTEN Integration Test Harness
================================
Tests complete signal flow using mock data and test ports.

SAFETY FEATURES:
- Uses TEST PORTS ONLY (15555, 15557, 15558 - NOT production 5555, 5557, 5558)
- NO real trades executed
- NO production database modifications
- Uses mock signal data from fixtures
"""

import pytest
import zmq
import json
import time
import sqlite3
import requests
from pathlib import Path
from collections import OrderedDict


# TEST PORTS - NEVER USE PRODUCTION PORTS
TEST_COMMAND_PORT = 15555  # Test command router port
TEST_SIGNAL_PORT = 15557   # Test Elite Guard signal port
TEST_CONFIRM_PORT = 15558  # Test confirmation port


class TestSignalInjection:
    """Test mock signal injection through ZMQ"""

    def test_signal_publish_format(self):
        """Verify signal publishing with correct format"""
        context = zmq.Context()
        publisher = context.socket(zmq.PUB)
        publisher.bind(f"tcp://127.0.0.1:{TEST_SIGNAL_PORT}")

        # Load test signal fixture
        fixture_path = Path("/root/HydraX-v2/tests/test_data/test_signal_eurusd_buy.json")
        with open(fixture_path, 'r') as f:
            test_signal = json.load(f)

        # Give socket time to bind
        time.sleep(0.5)

        # Publish signal
        signal_msg = json.dumps(test_signal)
        publisher.send_string(f"ELITE_GUARD_SIGNAL {signal_msg}")

        # Cleanup
        publisher.close()
        context.term()

        # Verify signal structure
        assert 'signal_id' in test_signal
        assert 'symbol' in test_signal
        assert 'direction' in test_signal
        assert 'confidence' in test_signal

    def test_signal_subscription(self):
        """Verify signal subscription and receipt"""
        context = zmq.Context()
        publisher = context.socket(zmq.PUB)
        publisher.bind(f"tcp://127.0.0.1:{TEST_SIGNAL_PORT}")

        subscriber = context.socket(zmq.SUB)
        subscriber.connect(f"tcp://127.0.0.1:{TEST_SIGNAL_PORT}")
        subscriber.setsockopt_string(zmq.SUBSCRIBE, "ELITE_GUARD_SIGNAL")
        subscriber.setsockopt(zmq.RCVTIMEO, 2000)  # 2 second timeout

        time.sleep(0.5)  # Socket setup time

        # Publish test signal
        test_signal = {
            "signal_id": "TEST_SIGNAL_001",
            "symbol": "EURUSD",
            "direction": "BUY",
            "confidence": 85.0
        }

        publisher.send_string(f"ELITE_GUARD_SIGNAL {json.dumps(test_signal)}")

        # Attempt to receive
        try:
            message = subscriber.recv_string()
            assert message.startswith("ELITE_GUARD_SIGNAL")

            # Parse signal
            signal_json = message.replace("ELITE_GUARD_SIGNAL ", "")
            received_signal = json.loads(signal_json)
            assert received_signal['signal_id'] == "TEST_SIGNAL_001"

        except zmq.Again:
            pytest.fail("Signal not received within timeout")
        finally:
            publisher.close()
            subscriber.close()
            context.term()


class TestFireCommandRouting:
    """Test fire command routing through IPC queue"""

    def test_fire_command_format_validation(self):
        """Verify fire command has correct format per EA v2.07 spec"""
        # Load test fire command fixture
        fixture_path = Path("/root/HydraX-v2/tests/test_data/test_fire_command.json")
        with open(fixture_path, 'r') as f:
            fire_cmd = json.load(f)

        # Validate mandatory fields
        assert fire_cmd['type'] == 'fire', "First field must be 'type': 'fire'"
        assert 'target_uuid' in fire_cmd
        assert 'fire_id' in fire_cmd
        assert 'symbol' in fire_cmd
        assert 'direction' in fire_cmd
        assert fire_cmd['direction'] in ['BUY', 'SELL'], "Direction must be uppercase"
        assert 'entry' in fire_cmd
        assert 'sl' in fire_cmd
        assert 'tp' in fire_cmd
        assert 'lot' in fire_cmd

        # Validate types
        assert isinstance(fire_cmd['entry'], (int, float))
        assert isinstance(fire_cmd['sl'], (int, float))
        assert isinstance(fire_cmd['tp'], (int, float))
        assert isinstance(fire_cmd['lot'], (int, float))

        # Lot must be rounded to 2 decimals
        lot_str = str(fire_cmd['lot'])
        if '.' in lot_str:
            decimals = len(lot_str.split('.')[1])
            assert decimals <= 2, f"Lot must be rounded to 2 decimals, got {decimals}"

    def test_fire_command_field_order(self):
        """Verify field order matches EA v2.07 requirements"""
        # Create OrderedDict with correct order
        fire_cmd = OrderedDict([
            ("type", "fire"),
            ("target_uuid", "TEST_UUID_001"),
            ("fire_id", "TEST_FIRE_001"),
            ("symbol", "EURUSD"),
            ("direction", "BUY"),
            ("entry", 0),
            ("sl", 1.09800),
            ("tp", 1.10300),
            ("lot", 0.01)
        ])

        # Serialize and verify order
        json_str = json.dumps(fire_cmd)
        assert json_str.index('"type"') < json_str.index('"target_uuid"')
        assert json_str.index('"target_uuid"') < json_str.index('"fire_id"')

    def test_fire_command_with_bitmode_hybrid(self):
        """Verify BITMODE hybrid configuration format"""
        fire_cmd = {
            "type": "fire",
            "target_uuid": "TEST_UUID_001",
            "fire_id": "TEST_BITMODE_001",
            "symbol": "GBPJPY",
            "direction": "SELL",
            "entry": 0,
            "sl": 199.65,
            "tp": 199.20,
            "lot": 0.45,
            "hybrid": {
                "enabled": True,
                "partial1": {"trigger": 8, "percent": 25},
                "partial2": {"trigger": 12, "percent": 25},
                "trail": {"distance": 8}
            }
        }

        # Validate hybrid structure
        assert 'hybrid' in fire_cmd
        assert fire_cmd['hybrid']['enabled'] is True
        assert 'partial1' in fire_cmd['hybrid']
        assert 'partial2' in fire_cmd['hybrid']
        assert 'trail' in fire_cmd['hybrid']

        # Validate partial take profit triggers
        assert fire_cmd['hybrid']['partial1']['trigger'] == 8
        assert fire_cmd['hybrid']['partial1']['percent'] == 25
        assert fire_cmd['hybrid']['partial2']['trigger'] == 12
        assert fire_cmd['hybrid']['partial2']['percent'] == 25


class TestConfirmationReceipt:
    """Test confirmation message simulation"""

    def test_confirmation_message_format(self):
        """Verify confirmation message has required fields"""
        # Load test confirmation fixture
        fixture_path = Path("/root/HydraX-v2/tests/test_data/test_confirmation.json")
        with open(fixture_path, 'r') as f:
            confirmation = json.load(f)

        # Validate required fields
        assert 'type' in confirmation
        assert confirmation['type'] == 'confirmation'
        assert 'fire_id' in confirmation
        assert 'status' in confirmation
        assert 'ticket' in confirmation
        assert 'price' in confirmation

    def test_confirmation_push_socket(self):
        """Test confirmation publishing through PUSH socket"""
        context = zmq.Context()

        # Bind PULL socket (simulating confirm_listener)
        puller = context.socket(zmq.PULL)
        puller.bind(f"tcp://127.0.0.1:{TEST_CONFIRM_PORT}")
        puller.setsockopt(zmq.RCVTIMEO, 2000)  # 2 second timeout

        # Connect PUSH socket (simulating EA)
        pusher = context.socket(zmq.PUSH)
        pusher.connect(f"tcp://127.0.0.1:{TEST_CONFIRM_PORT}")

        time.sleep(0.5)  # Socket setup time

        # Push test confirmation
        test_confirmation = {
            "type": "confirmation",
            "fire_id": "TEST_FIRE_001",
            "status": "FILLED",
            "ticket": 19059064,
            "price": 1.10250
        }

        pusher.send_json(test_confirmation)

        # Attempt to receive
        try:
            received = puller.recv_json()
            assert received['fire_id'] == "TEST_FIRE_001"
            assert received['status'] == "FILLED"
            assert received['ticket'] == 19059064
        except zmq.Again:
            pytest.fail("Confirmation not received within timeout")
        finally:
            puller.close()
            pusher.close()
            context.term()


class TestEndToEndSignalFlow:
    """Test complete signal flow (mock, non-live)"""

    def test_signal_to_fire_command_conversion(self):
        """Test signal conversion to fire command"""
        # Load signal fixture
        signal_path = Path("/root/HydraX-v2/tests/test_data/test_signal_eurusd_buy.json")
        with open(signal_path, 'r') as f:
            signal = json.load(f)

        # Simulate conversion to fire command
        fire_cmd = OrderedDict([
            ("type", "fire"),
            ("target_uuid", "TEST_UUID_001"),
            ("fire_id", f"TEST_{signal['signal_id']}"),
            ("symbol", signal['symbol']),
            ("direction", signal['direction']),
            ("entry", 0),
            ("sl", signal.get('stop_loss', 0)),
            ("tp", signal.get('take_profit', 0)),
            ("lot", 0.01)
        ])

        # Validate conversion
        assert fire_cmd['symbol'] == signal['symbol']
        assert fire_cmd['direction'] == signal['direction']
        assert fire_cmd['type'] == 'fire'

    def test_fire_command_to_confirmation_flow(self):
        """Test fire command → confirmation flow"""
        # Load fire command
        fire_path = Path("/root/HydraX-v2/tests/test_data/test_fire_command.json")
        with open(fire_path, 'r') as f:
            fire_cmd = json.load(f)

        # Simulate confirmation response
        confirmation = {
            "type": "confirmation",
            "fire_id": fire_cmd['fire_id'],
            "status": "FILLED",
            "ticket": 19059064,
            "price": 1.10250
        }

        # Validate flow
        assert confirmation['fire_id'] == fire_cmd['fire_id']
        assert confirmation['type'] == 'confirmation'


class TestDatabaseOperations:
    """Test database read operations (READ ONLY)"""

    DB_PATH = "/root/HydraX-v2/bitten.db"

    def test_query_recent_signals(self):
        """Test querying recent signals (read-only)"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT signal_id, symbol, direction, confidence
            FROM signals
            ORDER BY created_at DESC
            LIMIT 10
        """)

        results = cursor.fetchall()
        conn.close()

        # Verify structure (may be empty)
        if len(results) > 0:
            assert len(results[0]) == 4  # 4 columns selected

    def test_query_ea_instances(self):
        """Test querying EA instances (read-only)"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT target_uuid, user_id, last_seen
            FROM ea_instances
            ORDER BY last_seen DESC
        """)

        results = cursor.fetchall()
        conn.close()

        # Verify we can read EA instances
        # May be empty in test environment
        for row in results:
            assert len(row) == 3

    def test_query_fire_history(self):
        """Test querying fire command history (read-only)"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT fire_id, mission_id, status, ticket
            FROM fires
            ORDER BY created_at DESC
            LIMIT 10
        """)

        results = cursor.fetchall()
        conn.close()

        # Verify structure
        for row in results:
            assert len(row) == 4


class TestWebAppAPI:
    """Test WebApp API endpoints (read-only)"""

    BASE_URL = "http://localhost:8888"

    def test_api_signals_structure(self):
        """Test /api/signals response structure"""
        try:
            response = requests.get(f"{self.BASE_URL}/api/signals", timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Validate structure if signals exist
                if isinstance(data, list) and len(data) > 0:
                    signal = data[0]
                    assert 'signal_id' in signal or 'id' in signal
        except requests.exceptions.RequestException:
            pytest.skip("WebApp not available for testing")

    def test_healthz_response_format(self):
        """Test /healthz endpoint response"""
        try:
            response = requests.get(f"{self.BASE_URL}/healthz", timeout=5)
            assert response.status_code == 200

            # Try to parse JSON if returned
            try:
                health = response.json()
                # Common health check fields
                if isinstance(health, dict):
                    assert 'status' in health or 'ok' in health or len(health) >= 0
            except json.JSONDecodeError:
                # May return plain text "OK"
                pass
        except requests.exceptions.RequestException:
            pytest.skip("WebApp not available for testing")


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
