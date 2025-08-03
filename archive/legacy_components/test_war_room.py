#!/usr/bin/env python3
"""Test the War Room /me route"""

import requests
import json

# Test the War Room route
def test_war_room():
    base_url = "http://localhost:7007"
    user_id = "12345678"
    
    print("Testing War Room route...")
    
    # Test /me endpoint
    response = requests.get(f"{base_url}/me?user_id={user_id}")
    
    if response.status_code == 200:
        print("✅ War Room route successful!")
        # Check if key elements are present
        html_content = response.text
        checks = [
            ("Callsign present", "callsign" in html_content),
            ("Stats grid present", "stats-grid" in html_content),
            ("Kill cards present", "kill-cards" in html_content),
            ("Achievements present", "achievements" in html_content),
            ("Squad section present", "squad-section" in html_content),
            ("Social sharing present", "share-buttons" in html_content)
        ]
        
        for check_name, passed in checks:
            print(f"  {'✅' if passed else '❌'} {check_name}")
            
    else:
        print(f"❌ War Room route failed with status {response.status_code}")
    
    # Test squad API endpoint
    print("\nTesting Squad API endpoint...")
    response = requests.get(f"{base_url}/api/user/{user_id}/squad")
    
    if response.status_code == 200:
        print("✅ Squad API successful!")
        data = response.json()
        print(f"  Squad data: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ Squad API failed with status {response.status_code}")

if __name__ == "__main__":
    test_war_room()