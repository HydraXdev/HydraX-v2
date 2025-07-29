#!/usr/bin/env python3
"""Test script for the Commander Throne health endpoint"""

import requests
import json
import sys

def test_health_endpoint():
    """Test the health endpoint"""
    url = "http://localhost:8899/health"
    
    try:
        response = requests.get(url, timeout=5)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("\nResponse Body:")
        print(json.dumps(response.json(), indent=2))
        
        # Verify expected fields
        data = response.json()
        expected_fields = ["status", "timestamp", "service", "checks", "metrics"]
        for field in expected_fields:
            if field not in data:
                print(f"\n❌ Missing expected field: {field}")
                return False
        
        # Verify expected checks
        expected_checks = ["service", "database", "active_sessions", "uptime", "last_command"]
        for check in expected_checks:
            if check not in data["checks"]:
                print(f"\n❌ Missing expected check: {check}")
                return False
        
        print("\n✅ All expected fields and checks are present!")
        return True
        
    except requests.ConnectionError:
        print("❌ Could not connect to Commander Throne service on port 8899")
        print("Make sure the service is running with: python3 commander_throne.py")
        return False
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return False

if __name__ == "__main__":
    success = test_health_endpoint()
    sys.exit(0 if success else 1)