#!/usr/bin/env python3
"""
Example Fire Execution
Demonstrates how to execute a fire command via API
"""

import requests
import json
from datetime import datetime

# Fire Service API endpoint
API_URL = "http://localhost:8890"


def execute_manual_fire():
    """Execute manual fire command"""
    fire_request = {
        "user_id": "7176191872",
        "signal_id": f"ELITE_GUARD_EURUSD_{int(datetime.now().timestamp())}",
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.10500,
        "sl_price": 1.10300,
        "tp_price": 1.10800,
        "fire_mode": "MANUAL",
        "enable_bitmode": False
    }

    print("=" * 70)
    print("EXECUTING MANUAL FIRE")
    print("=" * 70)
    print(json.dumps(fire_request, indent=2))
    print()

    response = requests.post(f"{API_URL}/api/fire", json=fire_request)

    print("RESPONSE:")
    print(json.dumps(response.json(), indent=2))
    print("=" * 70)

    return response.json()


def execute_auto_fire_with_bitmode():
    """Execute AUTO fire with BITMODE enabled"""
    fire_request = {
        "user_id": "7176191872",
        "signal_id": f"ELITE_GUARD_GBPUSD_{int(datetime.now().timestamp())}",
        "symbol": "GBPUSD",
        "direction": "SELL",
        "entry_price": 1.28500,
        "sl_price": 1.28700,
        "tp_price": 1.28200,
        "fire_mode": "AUTO",
        "enable_bitmode": True
    }

    print("\n" + "=" * 70)
    print("EXECUTING AUTO FIRE WITH BITMODE")
    print("=" * 70)
    print(json.dumps(fire_request, indent=2))
    print()

    response = requests.post(f"{API_URL}/api/fire", json=fire_request)

    print("RESPONSE:")
    print(json.dumps(response.json(), indent=2))
    print("=" * 70)

    return response.json()


def get_fire_details(fire_id: str):
    """Get fire execution details"""
    print("\n" + "=" * 70)
    print(f"GETTING FIRE DETAILS: {fire_id}")
    print("=" * 70)

    response = requests.get(f"{API_URL}/api/fires/{fire_id}")

    print("DETAILS:")
    print(json.dumps(response.json(), indent=2))
    print("=" * 70)

    return response.json()


def get_user_positions(user_id: str):
    """Get user's current positions"""
    print("\n" + "=" * 70)
    print(f"GETTING POSITIONS FOR USER: {user_id}")
    print("=" * 70)

    response = requests.get(f"{API_URL}/api/positions", params={"user_id": user_id})

    print("POSITIONS:")
    print(json.dumps(response.json(), indent=2))
    print("=" * 70)

    return response.json()


def toggle_bitmode(user_id: str, enabled: bool):
    """Toggle BITMODE for user"""
    print("\n" + "=" * 70)
    print(f"TOGGLING BITMODE: {enabled}")
    print("=" * 70)

    request = {
        "user_id": user_id,
        "enabled": enabled
    }

    response = requests.post(f"{API_URL}/api/bitmode/toggle", json=request)

    print("RESPONSE:")
    print(json.dumps(response.json(), indent=2))
    print("=" * 70)

    return response.json()


def main():
    """Main execution"""
    print("\n🔥 BITTEN FIRE SERVICE - EXAMPLE EXECUTION 🔥\n")

    # Example 1: Manual fire (2% risk)
    result1 = execute_manual_fire()
    if result1["success"]:
        fire_id = result1["fire_id"]
        # Get fire details
        get_fire_details(fire_id)

    # Example 2: Enable BITMODE
    toggle_bitmode("7176191872", True)

    # Example 3: AUTO fire with BITMODE (5% risk + hybrid position management)
    result2 = execute_auto_fire_with_bitmode()

    # Example 4: Get current positions
    get_user_positions("7176191872")

    print("\n✅ EXAMPLE EXECUTION COMPLETE\n")


if __name__ == "__main__":
    main()
