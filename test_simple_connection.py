#!/usr/bin/env python3
"""
Simple test to isolate the connection issue
"""

import requests
import time

def test_basic_connection():
    """Test basic connection to market data receiver"""
    try:
        print("Testing basic connection to market data receiver...")
        response = requests.get("http://127.0.0.1:8001/market-data/health", timeout=3)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.text}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Connection timed out")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Other error: {e}")

if __name__ == "__main__":
    test_basic_connection()