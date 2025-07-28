#!/usr/bin/env python3
"""
Test script to exactly replicate engine signal detection
"""
import requests
import json
import time

def test_signal_detection():
    """Test signal detection exactly like engine"""
    
    symbol = 'EURUSD'
    
    # Step 1: Get list of files matching the symbol pattern
    cmd = f"dir /B /O:-D \"C:\\\\Users\\\\Administrator\\\\AppData\\\\Roaming\\\\MetaQuotes\\\\Terminal\\\\173477FF1060D99CE79296FC73108719\\\\MQL5\\\\Files\\\\BITTEN\\\\*{symbol}*.json\" 2>nul"
    print(f"Executing CMD: {cmd}")
    
    response = requests.post(
        "http://localhost:5555/execute",
        json={
            "command": cmd,
            "type": "cmd"
        },
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"File listing response: {result}")
        
        if result.get('success') and result.get('stdout'):
            # Get the first (most recent) file
            files = result['stdout'].strip().split('\n')
            print(f"Found files: {files}")
            
            if files and files[0]:
                latest_file = files[0].strip()
                print(f"Latest file: {latest_file}")
                
                # Step 2: Read the content of the latest file
                file_response = requests.post(
                    "http://localhost:5555/execute",
                    json={
                        "command": f"type \"C:\\\\Users\\\\Administrator\\\\AppData\\\\Roaming\\\\MetaQuotes\\\\Terminal\\\\173477FF1060D99CE79296FC73108719\\\\MQL5\\\\Files\\\\BITTEN\\\\{latest_file}\"",
                        "type": "cmd"
                    },
                    timeout=10
                )
                
                if file_response.status_code == 200:
                    file_result = file_response.json()
                    print(f"File content response: {file_result}")
                    
                    if file_result.get('success') and file_result.get('stdout'):
                        signal_content = file_result['stdout'].strip()
                        print(f"Signal content: {signal_content}")
                        
                        if signal_content:
                            try:
                                signal_data = json.loads(signal_content)
                                print(f"✅ SIGNAL DETECTED: {signal_data}")
                                return signal_data
                            except json.JSONDecodeError as e:
                                print(f"❌ JSON decode error: {e}")
                    else:
                        print("❌ File content read failed")
                else:
                    print(f"❌ File content request failed: {file_response.status_code}")
            else:
                print("❌ No files found in listing")
        else:
            print("❌ File listing failed or empty")
    else:
        print(f"❌ File listing request failed: {response.status_code}")
    
    return None

if __name__ == "__main__":
    print("Testing signal detection...")
    result = test_signal_detection()
    if result:
        print(f"\n🎉 SUCCESS! Signal detected: {result}")
    else:
        print("\n❌ FAILED! No signal detected")