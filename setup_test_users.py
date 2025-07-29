#!/usr/bin/env python3
"""
Setup Test Users for Individual Messaging
Creates fire-eligible users in the registry for testing
"""

import json
from datetime import datetime

def setup_test_users():
    """Create test users with fire eligibility"""
    
    # Load existing registry
    registry_file = '/root/HydraX-v2/user_registry_complete.json'
    
    try:
        with open(registry_file, 'r') as f:
            registry = json.load(f)
    except:
        registry = {}
    
    # Test users for individual messaging
    test_users = {
        "7176191872": {  # Commander user (already exists, update it)
            "user_id": "7176191872",
            "container": "mt5_user_7176191872",
            "container_name": "mt5_user_7176191872",
            "login": "843859",
            "broker": "Coinexx-Demo",
            "status": "connected",
            "tier": "COMMANDER",
            "ready_for_fire": True,
            "fire_eligible": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "wine_environment": "/root/.wine_user_7176191872",
            "last_activity": datetime.now().isoformat(),
            "connection_attempts": 1,
            "successful_connections": 1,
            "account_balance": 15000.0,
            "win_rate": 78.5,
            "total_pips": 1247.3,
            "streak_days": 12,
            "rank": "VETERAN",
            "uuid": "USER-7176191872"
        },
        "987654321": {  # Test FANG user
            "user_id": "987654321",
            "container": "mt5_user_987654321",
            "container_name": "mt5_user_987654321",
            "login": "654321",
            "broker": "MetaQuotes-Demo",
            "status": "connected",
            "tier": "FANG",
            "ready_for_fire": True,
            "fire_eligible": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "wine_environment": "/root/.wine_user_987654321",
            "last_activity": datetime.now().isoformat(),
            "connection_attempts": 1,
            "successful_connections": 1,
            "account_balance": 7500.0,
            "win_rate": 72.1,
            "total_pips": 423.7,
            "streak_days": 3,
            "rank": "SOLDIER",
            "uuid": "USER-987654321"
        },
        "123456789": {  # Test NIBBLER user
            "user_id": "123456789",
            "container": "mt5_user_123456789",
            "container_name": "mt5_user_123456789",
            "login": "123456",
            "broker": "FOREX.com-Demo",
            "status": "connected",
            "tier": "NIBBLER",
            "ready_for_fire": True,
            "fire_eligible": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "wine_environment": "/root/.wine_user_123456789",
            "last_activity": datetime.now().isoformat(),
            "connection_attempts": 1,
            "successful_connections": 1,
            "account_balance": 2500.0,
            "win_rate": 65.4,
            "total_pips": 87.2,
            "streak_days": 1,
            "rank": "RECRUIT",
            "uuid": "USER-123456789"
        },
        "555666777": {  # Additional test user for higher count
            "user_id": "555666777",
            "container": "mt5_user_555666777",
            "container_name": "mt5_user_555666777",
            "login": "555666",
            "broker": "HugosWay-Demo",
            "status": "connected",
            "tier": "FANG",
            "ready_for_fire": True,
            "fire_eligible": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "wine_environment": "/root/.wine_user_555666777",
            "last_activity": datetime.now().isoformat(),
            "connection_attempts": 1,
            "successful_connections": 1,
            "account_balance": 5000.0,
            "win_rate": 70.0,
            "total_pips": 250.0,
            "streak_days": 2,
            "rank": "SOLDIER",
            "uuid": "USER-555666777"
        }
    }
    
    # Update registry with test users
    for user_id, user_data in test_users.items():
        registry[user_id] = user_data
        print(f"✅ Setup test user {user_id} ({user_data['tier']})")
    
    # Save updated registry
    with open(registry_file, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"\n🎯 Registry updated with {len(test_users)} fire-eligible test users")
    print(f"📄 Registry file: {registry_file}")
    
    return len(test_users)

if __name__ == "__main__":
    count = setup_test_users()
    print(f"\n✅ Individual messaging test setup complete: {count} users ready")