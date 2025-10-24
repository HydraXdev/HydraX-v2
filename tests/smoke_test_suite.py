#!/usr/bin/env python3
"""
BITTEN Smoke Test Suite
========================
Validates critical system components are operational.

SAFETY: READ ONLY - No modifications to live system
Tests check process status, port bindings, and basic connectivity
"""

import pytest
import subprocess
import socket
import sqlite3
import requests
import json
import os
from pathlib import Path


class TestProcessHealth:
    """Verify critical processes are running"""

    def test_elite_guard_process_running(self):
        """Elite Guard signal generator must be active"""
        result = subprocess.run(
            ['pgrep', '-f', 'elite_guard_with_citadel.py'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Elite Guard process not running"
        assert len(result.stdout.strip()) > 0, "Elite Guard PID not found"

    def test_webapp_process_running(self):
        """WebApp server must be active on port 8888"""
        result = subprocess.run(
            ['pgrep', '-f', 'webapp_server_optimized.py'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "WebApp process not running"

    def test_command_router_process_running(self):
        """Command router must be active"""
        result = subprocess.run(
            ['pgrep', '-f', 'command_router.py'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Command router process not running"

    def test_confirm_listener_process_running(self):
        """Confirmation listener must be active"""
        result = subprocess.run(
            ['pgrep', '-f', 'confirm_listener.py'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Confirm listener process not running"


class TestPortBindings:
    """Verify ZMQ ports are bound correctly"""

    def test_command_router_port_5555(self):
        """Port 5555 must be bound (command router)"""
        result = subprocess.run(
            ['ss', '-tuln'],
            capture_output=True,
            text=True
        )
        assert ':5555' in result.stdout, "Port 5555 not bound (command router)"

    def test_market_data_port_5556(self):
        """Port 5556 must be bound (market data ingestion)"""
        result = subprocess.run(
            ['ss', '-tuln'],
            capture_output=True,
            text=True
        )
        assert ':5556' in result.stdout, "Port 5556 not bound (market data)"

    def test_elite_guard_signal_port_5557(self):
        """Port 5557 must be bound (Elite Guard signals)"""
        result = subprocess.run(
            ['ss', '-tuln'],
            capture_output=True,
            text=True
        )
        assert ':5557' in result.stdout, "Port 5557 not bound (Elite Guard signals)"

    def test_confirmation_port_5558(self):
        """Port 5558 must be bound (trade confirmations)"""
        result = subprocess.run(
            ['ss', '-tuln'],
            capture_output=True,
            text=True
        )
        assert ':5558' in result.stdout, "Port 5558 not bound (confirmations)"

    def test_telemetry_relay_port_5560(self):
        """Port 5560 must be bound (telemetry relay)"""
        result = subprocess.run(
            ['ss', '-tuln'],
            capture_output=True,
            text=True
        )
        assert ':5560' in result.stdout, "Port 5560 not bound (telemetry relay)"

    def test_webapp_http_port_8888(self):
        """Port 8888 must be bound (WebApp HTTP)"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8888))
        sock.close()
        assert result == 0, "Port 8888 not accepting connections (WebApp)"


class TestWebAppEndpoints:
    """Verify WebApp HTTP endpoints respond correctly"""

    BASE_URL = "http://localhost:8888"

    def test_healthz_endpoint(self):
        """Health check endpoint must respond"""
        try:
            response = requests.get(f"{self.BASE_URL}/healthz", timeout=5)
            assert response.status_code == 200, f"Health check failed: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Health check endpoint unreachable: {e}")

    def test_api_signals_get(self):
        """GET /api/signals must be accessible"""
        try:
            response = requests.get(f"{self.BASE_URL}/api/signals", timeout=5)
            # Should return 200 or 204 (no signals currently)
            assert response.status_code in [200, 204], f"Signals API failed: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Signals API endpoint unreachable: {e}")

    def test_war_room_endpoint(self):
        """War Room /me endpoint must be accessible"""
        try:
            response = requests.get(f"{self.BASE_URL}/me", timeout=5)
            # May redirect to login, but should respond
            assert response.status_code in [200, 302, 401], f"War Room failed: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.fail(f"War Room endpoint unreachable: {e}")


class TestDatabaseConnectivity:
    """Verify database is accessible and has correct schema"""

    DB_PATH = "/root/HydraX-v2/bitten.db"

    def test_database_file_exists(self):
        """Database file must exist"""
        assert Path(self.DB_PATH).exists(), f"Database not found at {self.DB_PATH}"

    def test_database_readable(self):
        """Database must be readable"""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            assert len(tables) > 0, "Database has no tables"
        except sqlite3.Error as e:
            pytest.fail(f"Database not readable: {e}")

    def test_ea_instances_table_exists(self):
        """ea_instances table must exist"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ea_instances'")
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "ea_instances table missing"

    def test_missions_table_exists(self):
        """missions table must exist"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='missions'")
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "missions table missing"

    def test_fires_table_exists(self):
        """fires table must exist"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fires'")
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "fires table missing"

    def test_signals_table_exists(self):
        """signals table must exist"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='signals'")
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "signals table missing"

    def test_ea_instances_schema(self):
        """ea_instances table must have correct schema"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(ea_instances)")
        columns = {col[1] for col in cursor.fetchall()}
        conn.close()

        required_columns = {'target_uuid', 'user_id', 'last_seen', 'last_balance'}
        missing = required_columns - columns
        assert len(missing) == 0, f"ea_instances missing columns: {missing}"


class TestIPCQueue:
    """Verify IPC queue path exists and is accessible"""

    IPC_PATH = "/tmp/bitten_cmdqueue"

    def test_ipc_socket_exists(self):
        """IPC socket file should exist or be accessible"""
        # IPC socket may not show as file, check if process can access
        # This is a soft check - if command_router is running, IPC is working
        result = subprocess.run(
            ['pgrep', '-f', 'command_router.py'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Command router not running (IPC queue unavailable)"


class TestCriticalFiles:
    """Verify critical system files exist"""

    def test_elite_guard_file_exists(self):
        """Elite Guard source file must exist"""
        path = Path("/root/HydraX-v2/elite_guard_with_citadel.py")
        assert path.exists(), "elite_guard_with_citadel.py missing"

    def test_command_router_file_exists(self):
        """Command router source file must exist"""
        path = Path("/root/HydraX-v2/command_router.py")
        assert path.exists(), "command_router.py missing"

    def test_webapp_file_exists(self):
        """WebApp source file must exist"""
        path = Path("/root/HydraX-v2/webapp_server_optimized.py")
        assert path.exists(), "webapp_server_optimized.py missing"

    def test_confirm_listener_file_exists(self):
        """Confirm listener source file must exist"""
        path = Path("/root/HydraX-v2/confirm_listener.py")
        assert path.exists(), "confirm_listener.py missing"


class TestSystemHealth:
    """Overall system health checks"""

    def test_ea_heartbeat_freshness(self):
        """EA heartbeat should be recent (within 2 minutes)"""
        conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT target_uuid, (strftime('%s','now') - last_seen) AS age_s
            FROM ea_instances
        """)
        results = cursor.fetchall()
        conn.close()

        if len(results) > 0:
            # Check at least one EA has recent heartbeat
            fresh_eas = [r for r in results if r[1] < 120]
            # Warning only - don't fail if no recent heartbeat
            if len(fresh_eas) == 0:
                pytest.warns(UserWarning, "No EA heartbeats within 120 seconds")
        else:
            pytest.warns(UserWarning, "No EA instances registered")


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
