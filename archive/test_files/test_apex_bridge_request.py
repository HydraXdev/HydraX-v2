#!/usr/bin/env python3
import requests
import json

# Test 1: Exact APEX format
print("Test 1: APEX exact format")
apex_cmd = r'dir /B "C:\\Users\\Administrator\\AppData\\Roaming\\MetaQuotes\\Terminal\\Common\\Files\\BITTEN\\XAUUSD.json" 2>nul'
apex_request = {
    "command": apex_cmd,
    "type": "cmd"
}
print(f"Request: {json.dumps(apex_request, indent=2)}")

try:
    response = requests.post(
        "http://3.145.84.187:5555/execute",
        json=apex_request,
        timeout=10
    )
    print(f"Response Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50 + "\n")

# Test 2: Working format (type command)
print("Test 2: Working type command")
type_cmd = r'type "C:\\Users\\Administrator\\AppData\\Roaming\\MetaQuotes\\Terminal\\Common\\Files\\BITTEN\\XAUUSD.json"'
type_request = {
    "command": type_cmd,
    "type": "cmd"
}
print(f"Request: {json.dumps(type_request, indent=2)}")

try:
    response = requests.post(
        "http://3.145.84.187:5555/execute",
        json=type_request,
        timeout=10
    )
    print(f"Response Status: {response.status_code}")
    result = response.json()
    print(f"Return Code: {result.get('returncode')}")
    print(f"Stdout Length: {len(result.get('stdout', ''))}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50 + "\n")

# Test 3: Different path format
print("Test 3: Check if path escaping is the issue")
# Try with single backslashes
single_slash_cmd = r'dir /B "C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\Common\Files\BITTEN\XAUUSD.json" 2>nul'
single_request = {
    "command": single_slash_cmd,
    "type": "cmd"
}
print(f"Request: {json.dumps(single_request, indent=2)}")

try:
    response = requests.post(
        "http://3.145.84.187:5555/execute",
        json=single_request,
        timeout=10
    )
    print(f"Response Status: {response.status_code}")
    print(f"Return Code: {response.json().get('returncode')}")
except Exception as e:
    print(f"Error: {e}")