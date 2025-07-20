#!/usr/bin/env python3
"""
Test script for the enhanced mission_endpoints.py
Tests all endpoints with real mission data
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5001"
TEST_USER_ID = "test_user_123"
TEST_TOKEN = "test_token_12345"

# Headers for authentication
HEADERS = {
    "Authorization": f"Bearer {TEST_TOKEN}",
    "X-User-ID": TEST_USER_ID,
    "Content-Type": "application/json"
}

def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_mission_status():
    """Test mission status endpoint"""
    print("Testing mission status...")
    
    # Use an existing mission from the missions directory
    mission_id = "test_user_123_1752507290"
    
    response = requests.get(
        f"{BASE_URL}/api/mission-status/{mission_id}",
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_list_missions():
    """Test mission listing endpoint"""
    print("Testing mission listing...")
    
    # Test with different filters
    for status_filter in [None, "pending", "active", "expired"]:
        params = {"limit": 10, "offset": 0}
        if status_filter:
            params["status"] = status_filter
        
        response = requests.get(
            f"{BASE_URL}/api/missions",
            headers=HEADERS,
            params=params
        )
        
        print(f"Filter: {status_filter} - Status: {response.status_code}")
        data = response.json()
        if response.status_code == 200:
            print(f"Found {data['total']} missions")
        else:
            print(f"Error: {data}")
        print()

def test_fire_mission():
    """Test firing a mission"""
    print("Testing mission firing...")
    
    mission_id = "test_user_123_1752507290"
    
    payload = {
        "mission_id": mission_id
    }
    
    response = requests.post(
        f"{BASE_URL}/api/fire",
        headers=HEADERS,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_cancel_mission():
    """Test cancelling a mission"""
    print("Testing mission cancellation...")
    
    mission_id = "test_user_456_1752507290"  # Use a different mission
    
    response = requests.post(
        f"{BASE_URL}/api/missions/{mission_id}/cancel",
        headers=HEADERS
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_auth_required():
    """Test authentication requirements"""
    print("Testing authentication requirements...")
    
    # Test without headers
    response = requests.get(f"{BASE_URL}/api/missions")
    print(f"No auth - Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("BITTEN Mission Endpoints API Tests")
    print("=" * 60)
    
    try:
        test_health_check()
        test_auth_required()
        test_mission_status()
        test_list_missions()
        test_fire_mission()
        test_cancel_mission()
        
        print("All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the API server.")
        print("Make sure the mission endpoints server is running on port 5001")
        print()
        print("To start the server:")
        print("cd /root/HydraX-v2/src/api")
        print("python mission_endpoints.py")
    
    except Exception as e:
        print(f"Error running tests: {e}")

if __name__ == "__main__":
    run_all_tests()