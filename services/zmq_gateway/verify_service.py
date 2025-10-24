#!/usr/bin/env python3
"""
Quick verification script for ZMQ Gateway Service
Tests that all components can be imported and initialized
"""
import asyncio
import sys

import zmq.asyncio


async def verify_imports():
    """Verify all modules import correctly"""
    print("🔍 Verifying imports...")

    try:
        from services.zmq_gateway.config import (
            DB_PATH,
            HEALTH_PORT,
            PORT_COMMAND_ROUTER,
            PORT_CONFIRMATIONS,
            PORT_MARKET_DATA_IN,
            PORT_MARKET_DATA_OUT,
        )

        print(f"   ✅ config.py - Ports configured correctly")
        print(f"      - Market data: {PORT_MARKET_DATA_IN} → {PORT_MARKET_DATA_OUT}")
        print(f"      - Command router: {PORT_COMMAND_ROUTER}")
        print(f"      - Confirmations: {PORT_CONFIRMATIONS}")
        print(f"      - Health: {HEALTH_PORT}")
        print(f"      - Database: {DB_PATH}")

        from services.zmq_gateway.market_data_handler import MarketDataHandler

        print(f"   ✅ market_data_handler.py - MarketDataHandler class available")

        from services.zmq_gateway.command_handler import CommandHandler

        print(f"   ✅ command_handler.py - CommandHandler class available")

        from services.zmq_gateway.confirmation_handler import ConfirmationHandler

        print(f"   ✅ confirmation_handler.py - ConfirmationHandler class available")

        from services.zmq_gateway.health_server import HealthServer

        print(f"   ✅ health_server.py - HealthServer class available")

        from services.zmq_gateway.main import ZMQGateway

        print(f"   ✅ main.py - ZMQGateway class available")

        return True

    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False


async def verify_initialization():
    """Verify components can be initialized"""
    print("\n🔨 Verifying component initialization...")

    try:
        context = zmq.asyncio.Context()

        # Test MarketDataHandler
        from services.zmq_gateway.market_data_handler import MarketDataHandler

        market_data = MarketDataHandler(context)
        print(f"   ✅ MarketDataHandler initialized")

        # Test CommandHandler
        from services.zmq_gateway.command_handler import CommandHandler

        command_handler = CommandHandler(context)
        print(f"   ✅ CommandHandler initialized")

        # Test ConfirmationHandler
        from services.zmq_gateway.confirmation_handler import ConfirmationHandler

        confirmation_handler = ConfirmationHandler(context)
        print(f"   ✅ ConfirmationHandler initialized")

        # Test HealthServer
        from services.zmq_gateway.health_server import HealthServer

        health_server = HealthServer()
        print(f"   ✅ HealthServer initialized")

        # Cleanup
        context.term()

        return True

    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        return False


async def verify_fire_command_format():
    """Verify fire command serialization format"""
    print("\n🔥 Verifying fire command format...")

    try:
        from services.zmq_gateway.command_handler import CommandHandler

        context = zmq.asyncio.Context()
        handler = CommandHandler(context)

        # Test fire command
        test_cmd = {
            "type": "fire",
            "target_uuid": "COMMANDER_DEV_001",
            "fire_id": "TEST_FIRE_123",
            "symbol": "EURUSD",
            "direction": "BUY",
            "entry": 0,
            "sl": 1.09800,
            "tp": 1.10300,
            "lot": 0.01,
        }

        # Serialize
        payload = handler._serialize_fire_command(test_cmd)
        payload_str = payload.decode("utf-8")

        print(f"   ✅ Fire command serialized successfully")
        print(f"      Format: {payload_str[:120]}")

        # Verify field order (type must be first)
        if payload_str.startswith('{"type":"fire"'):
            print(f"   ✅ Field order correct (type is first)")
        else:
            print(f"   ❌ Field order incorrect (type not first)")
            return False

        # Verify lot rounding
        if '"lot":0.01' in payload_str:
            print(f"   ✅ Lot rounding correct (2 decimals)")
        else:
            print(f"   ❌ Lot rounding incorrect")
            return False

        context.term()
        return True

    except Exception as e:
        print(f"   ❌ Format verification failed: {e}")
        return False


async def main():
    """Run all verification tests"""
    print("=" * 70)
    print("ZMQ Gateway v2.0 - Service Verification")
    print("=" * 70)
    print()

    results = []

    # Test imports
    results.append(await verify_imports())

    # Test initialization
    results.append(await verify_initialization())

    # Test fire command format
    results.append(await verify_fire_command_format())

    # Summary
    print()
    print("=" * 70)
    if all(results):
        print("✅ ALL VERIFICATION TESTS PASSED")
        print()
        print("Service is ready to deploy. Start with:")
        print("  python3 /root/HydraX-v2/services/zmq_gateway/main.py")
    else:
        print("❌ SOME VERIFICATION TESTS FAILED")
        print()
        print("Please fix the issues above before deploying.")
        sys.exit(1)
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
