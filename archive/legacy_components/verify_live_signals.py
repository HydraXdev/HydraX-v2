#!/usr/bin/env python3

import requests
import json

def verify_live_signals():
    """Verify live signal files on Windows MT5"""
    
    bridge_server = "localhost"
    bridge_port = 5555
    signal_directory = r"C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\173477FF1060D99CE79296FC73108719\MQL5\Files\BITTEN"
    
    print("🎯 VERIFYING LIVE SIGNALS ON WINDOWS MT5")
    print("=" * 50)
    
    try:
        # List LIVE signal files
        response = requests.post(
            f"http://{bridge_server}:{bridge_port}/execute",
            json={
                "command": f'dir /B /O:D "{signal_directory}\\LIVE_*.json"',
                "type": "cmd"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('returncode') == 0 and result.get('stdout'):
                files = [f.strip() for f in result['stdout'].strip().split('\n') if f.strip()]
                
                print(f"📊 Found {len(files)} LIVE signal files:")
                for i, file in enumerate(files, 1):
                    print(f"  {i}. {file}")
                
                # Read the latest file
                if files:
                    latest_file = files[-1]
                    print(f"\n📋 Reading latest signal: {latest_file}")
                    
                    read_response = requests.post(
                        f"http://{bridge_server}:{bridge_port}/execute",
                        json={
                            "command": f'type "{signal_directory}\\{latest_file}"',
                            "type": "cmd"
                        },
                        timeout=10
                    )
                    
                    if read_response.status_code == 200:
                        read_result = read_response.json()
                        if read_result.get('returncode') == 0:
                            content = read_result.get('stdout', '').strip()
                            try:
                                parsed = json.loads(content)
                                print("✅ LIVE SIGNAL CONFIRMED ON WINDOWS MT5:")
                                print(json.dumps(parsed, indent=2))
                                print(f"\n🎯 Signal Details:")
                                print(f"   Symbol: {parsed.get('symbol')}")
                                print(f"   Direction: {parsed.get('direction')}")
                                print(f"   TCS: {parsed.get('tcs')}")
                                print(f"   Entry Price: {parsed.get('entry_price')}")
                                print(f"   Risk: {parsed.get('risk_percent', 'N/A')}%")
                                
                            except json.JSONDecodeError as e:
                                print(f"⚠️ JSON parsing error: {e}")
                                print("Raw content:", content[:200])
                        else:
                            print(f"❌ Error reading file: {read_result.get('stderr', '')}")
                    else:
                        print(f"❌ HTTP error reading file: {read_response.status_code}")
                        
            else:
                print("📭 No LIVE signal files found")
                
        else:
            print(f"❌ Failed to list files: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"🚨 Error: {e}")

if __name__ == "__main__":
    verify_live_signals()