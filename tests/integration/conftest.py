#!/usr/bin/env python3
"""
BITTEN v2.0 Phase 1 - Pytest Fixtures for Integration Tests

Provides shared fixtures and utilities for testing v2 services.

Author: Claude Code (Sonnet 4.5)
Created: 2025-10-08
"""

import pytest
import asyncio
import zmq
import zmq.asyncio
import asyncpg
from typing import AsyncGenerator, Dict, Any
from dataclasses import dataclass


@dataclass
class TestConfig:
    """Test environment configuration"""
    # Database
    postgres_dsn: str = "postgresql://bitten_admin@localhost:5432/bitten_v2_test"

    # ZMQ Ports
    zmq_gateway_pub: int = 15560  # Test port (5560 + 10000)
    zmq_signal_pub: int = 15557   # Test port (5557 + 10000)
    zmq_command_router: int = 15555  # Test port (5555 + 10000)
    zmq_confirm_pull: int = 15558  # Test port (5558 + 10000)

    # API Servers
    api_server_port: int = 18888  # Test port (8888 + 10000)

    # Test data
    test_user_id: str = "test_user_123"
    test_ea_uuid: str = "TEST_EA_001"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def config() -> TestConfig:
    """Provide test configuration"""
    return TestConfig()


@pytest.fixture(scope="session")
async def db_pool(config: TestConfig) -> AsyncGenerator[asyncpg.Pool, None]:
    """
    Create PostgreSQL connection pool for tests

    Note: This expects a test database to exist. If not available,
    tests will be skipped gracefully.
    """
    try:
        pool = await asyncpg.create_pool(
            config.postgres_dsn,
            min_size=2,
            max_size=5,
            command_timeout=10.0
        )

        # Verify connection
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")

        yield pool
        await pool.close()

    except (asyncpg.PostgresError, OSError) as e:
        pytest.skip(f"PostgreSQL not available: {e}")


@pytest.fixture
async def clean_db(db_pool: asyncpg.Pool):
    """
    Clean test database before each test

    Truncates all tables to ensure clean state
    """
    async with db_pool.acquire() as conn:
        await conn.execute("""
            TRUNCATE TABLE
                signals,
                fires,
                positions,
                ea_instances,
                user_sessions,
                analytics_cache
            CASCADE
        """)
    yield


@pytest.fixture
def zmq_context() -> zmq.asyncio.Context:
    """Provide ZMQ context for tests"""
    ctx = zmq.asyncio.Context()
    yield ctx
    ctx.term()


@pytest.fixture
async def mock_market_data_pub(zmq_context: zmq.asyncio.Context, config: TestConfig):
    """
    Mock market data publisher (ZMQ PUB socket)

    Simulates zmq_gateway publishing market data
    """
    pub = zmq_context.socket(zmq.PUB)
    pub.bind(f"tcp://127.0.0.1:{config.zmq_gateway_pub}")

    # Give subscribers time to connect
    await asyncio.sleep(0.1)

    yield pub
    pub.close()


@pytest.fixture
async def mock_command_router(zmq_context: zmq.asyncio.Context, config: TestConfig):
    """
    Mock command router (ZMQ ROUTER socket)

    Simulates fire_service ROUTER for commands
    """
    router = zmq_context.socket(zmq.ROUTER)
    router.bind(f"tcp://127.0.0.1:{config.zmq_command_router}")

    yield router
    router.close()


@pytest.fixture
async def mock_signal_subscriber(zmq_context: zmq.asyncio.Context, config: TestConfig):
    """
    Mock signal subscriber (ZMQ SUB socket)

    Simulates api_server subscribing to signals
    """
    sub = zmq_context.socket(zmq.SUB)
    sub.connect(f"tcp://127.0.0.1:{config.zmq_signal_pub}")
    sub.setsockopt(zmq.SUBSCRIBE, b"")

    # Give PUB socket time to connect
    await asyncio.sleep(0.1)

    yield sub
    sub.close()


@pytest.fixture
def sample_signal_data() -> Dict[str, Any]:
    """Provide sample signal data for tests"""
    return {
        "signal_id": "TEST_SIGNAL_001",
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.09500,
        "sl_pips": 20,
        "tp_pips": 40,
        "confidence": 85.5,
        "pattern_type": "LIQUIDITY_SWEEP_REVERSAL",
        "created_at": 1728400000
    }


@pytest.fixture
def sample_fire_command() -> Dict[str, Any]:
    """Provide sample fire command for tests"""
    return {
        "type": "fire",
        "fire_id": "TEST_FIRE_001",
        "target_uuid": "TEST_EA_001",
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry": 1.09500,
        "sl": 1.09300,
        "tp": 1.09900,
        "lot": 0.10
    }


@pytest.fixture
def sample_position_data() -> Dict[str, Any]:
    """Provide sample position data for tests"""
    return {
        "position_id": "POS_TEST_001",
        "fire_id": "TEST_FIRE_001",
        "ticket": 12345,
        "symbol": "EURUSD",
        "direction": "BUY",
        "open_price": 1.09500,
        "volume": 0.10,
        "sl": 1.09300,
        "tp": 1.09900,
        "status": "OPEN"
    }


@pytest.fixture
async def wait_for_message(timeout: float = 5.0):
    """
    Helper fixture to wait for ZMQ messages with timeout

    Usage:
        msg = await wait_for_message(socket)
    """
    async def _wait(socket, timeout_override: float = None):
        t = timeout_override or timeout
        try:
            msg = await asyncio.wait_for(socket.recv_json(), timeout=t)
            return msg
        except asyncio.TimeoutError:
            pytest.fail(f"Timeout waiting for message after {t}s")

    return _wait


# Test utilities

def assert_signal_valid(signal: Dict[str, Any]):
    """Assert signal has all required fields"""
    required_fields = [
        "signal_id", "symbol", "direction", "entry_price",
        "sl_pips", "tp_pips", "confidence", "pattern_type"
    ]

    for field in required_fields:
        assert field in signal, f"Signal missing required field: {field}"

    # Validate field types
    assert isinstance(signal["confidence"], (int, float))
    assert 0 <= signal["confidence"] <= 100
    assert signal["direction"] in ["BUY", "SELL"]


def assert_fire_valid(fire: Dict[str, Any]):
    """Assert fire command has all required fields"""
    required_fields = [
        "type", "fire_id", "target_uuid", "symbol",
        "direction", "entry", "sl", "tp", "lot"
    ]

    for field in required_fields:
        assert field in fire, f"Fire command missing required field: {field}"

    assert fire["type"] == "fire"
    assert fire["direction"] in ["BUY", "SELL"]
    assert isinstance(fire["lot"], (int, float))
    assert fire["lot"] > 0


def assert_position_valid(position: Dict[str, Any]):
    """Assert position has all required fields"""
    required_fields = [
        "position_id", "fire_id", "ticket", "symbol",
        "direction", "open_price", "volume", "status"
    ]

    for field in required_fields:
        assert field in position, f"Position missing required field: {field}"

    assert position["status"] in ["OPEN", "CLOSED", "PENDING"]
    assert position["direction"] in ["BUY", "SELL"]
