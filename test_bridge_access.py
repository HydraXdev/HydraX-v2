#!/usr/bin/env python3

import requests
import json

def test_bridge_directory_access():
    """Test access to Windows MT5 signal directory"""
    
    print("=== BRIDGE DIRECTORY ACCESS TEST ===")
    
    bridge_server = "3.145.84.187"
    bridge_port = 5555
    signal_directory = r"C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\173477FF1060D99CE79296FC73108719\MQL5\Files\BITTEN"
    
    try:
        # Test directory access
        response = requests.post(
            f"http://{bridge_server}:{bridge_port}/execute",
            json={
                "command": f'dir "{signal_directory}"',
                "type": "cmd"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - Directory accessible!")
            print(f"Return code: {result.get('returncode')}")
            
            if result.get('stdout'):
                print("\n📁 Files in signal directory:")
                lines = result['stdout'].strip().split('\n')
                file_count = 0
                for line in lines:
                    if line.strip() and not line.strip().startswith('Volume') and 'Directory of' not in line:
                        if '.json' in line or '<DIR>' in line:
                            print(f"  📄 {line.strip()}")
                            if '.json' in line:
                                file_count += 1
                
                print(f"\n📊 Total JSON signal files: {file_count}")
                
                # Test reading a specific signal file if any exist
                if file_count > 0:
                    print("\n🔍 Testing signal file content...")
                    test_file_content(bridge_server, bridge_port, signal_directory)
                
            else:
                print("⚠️  Directory empty or no output")
                
        else:
            print(f"❌ FAILED - Directory not accessible")
            print(f"HTTP Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"🚨 ERROR: {e}")

def test_file_content(server, port, directory):
    """Test reading signal file content"""
    
    try:
        # List JSON files
        response = requests.post(
            f"http://{server}:{port}/execute",
            json={
                "command": f'dir /B "{directory}\\*.json"',
                "type": "cmd"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('returncode') == 0 and result.get('stdout'):
                files = [f.strip() for f in result['stdout'].strip().split('\n') if f.strip()]
                if files:
                    test_file = files[0]
                    print(f"📋 Reading sample file: {test_file}")
                    
                    # Read file content
                    read_response = requests.post(
                        f"http://{server}:{port}/execute",
                        json={
                            "command": f'type "{directory}\\{test_file}"',
                            "type": "cmd"
                        },
                        timeout=10
                    )
                    
                    if read_response.status_code == 200:
                        read_result = read_response.json()
                        if read_result.get('returncode') == 0:
                            content = read_result.get('stdout', '').strip()
                            print(f"📄 File content preview:")
                            print(content[:500] + "..." if len(content) > 500 else content)
                            
                            # Try to parse as JSON
                            try:
                                parsed = json.loads(content)
                                print("✅ Valid JSON signal format confirmed")
                                if 'symbol' in parsed:
                                    print(f"🎯 Signal for: {parsed['symbol']}")
                                if 'action' in parsed:
                                    print(f"📈 Action: {parsed['action']}")
                            except json.JSONDecodeError:
                                print("⚠️  File content is not valid JSON")
                        else:
                            print(f"❌ Failed to read file: {read_result.get('stderr', '')}")
                    else:
                        print(f"❌ HTTP error reading file: {read_response.status_code}")
                        
    except Exception as e:
        print(f"🚨 Error testing file content: {e}")

if __name__ == "__main__":
    test_bridge_directory_access()