#!/usr/bin/env python3
"""
Complete Infrastructure Test Suite
Tests all components of the HydraX onboarding and container management system
"""

import sys
import os
import json
import time
sys.path.append('/root/HydraX-v2/src')

def test_srv_files():
    """Test that broker server files are available"""
    print("=== TESTING .SRV BROKER FILES ===")
    
    required_servers = [
        "Coinexx-Demo.srv",
        "Coinexx-Live.srv", 
        "Forex.com-Demo.srv",
        "Forex.com-Live3.srv",
        "OANDA-Demo-1.srv",
        "Eightcap-Real.srv",
        "HugosWay-Demo.srv",
        "LMFX-Demo.srv"
    ]
    
    srv_dir = "/root/HydraX-v2/mt5_server_templates/servers"
    
    if not os.path.exists(srv_dir):
        print(f"❌ Server templates directory not found: {srv_dir}")
        return False
    
    missing_servers = []
    found_servers = []
    
    for server in required_servers:
        srv_path = os.path.join(srv_dir, server)
        if os.path.exists(srv_path):
            found_servers.append(server)
            print(f"✅ Found: {server}")
        else:
            missing_servers.append(server)
            print(f"❌ Missing: {server}")
    
    print(f"\nSummary: {len(found_servers)}/{len(required_servers)} server files found")
    
    if missing_servers:
        print(f"Missing servers: {', '.join(missing_servers)}")
        return False
    
    return True

def test_user_registry():
    """Test user registry system"""
    print("\n=== TESTING USER REGISTRY SYSTEM ===")
    
    try:
        from bitten_core.user_registry_manager import UserRegistryManager
        
        # Create test registry
        test_registry = UserRegistryManager("/tmp/test_registry.json")
        
        # Test user registration
        test_user = "test_user_123"
        container = f"mt5_user_{test_user}"
        
        print(f"Registering test user: {test_user}")
        success = test_registry.register_user(test_user, "test", container, "12345", "Coinexx-Demo")
        
        if not success:
            print("❌ User registration failed")
            return False
        print("✅ User registration successful")
        
        # Test status updates
        print("Testing status updates...")
        test_registry.update_user_status(test_user, "credentials_injected")
        test_registry.update_user_status(test_user, "mt5_logged_in")
        test_registry.update_user_status(test_user, "ready_for_fire")
        
        # Test user info retrieval
        user_info = test_registry.get_user_info(test_user)
        if not user_info:
            print("❌ Could not retrieve user info")
            return False
        
        print(f"✅ User info retrieved: {user_info['status']}")
        
        # Test fire eligibility
        is_ready = test_registry.is_user_ready_for_fire(test_user)
        if not is_ready:
            print("❌ User not marked as ready for fire")
            return False
        
        print("✅ User correctly marked as ready for fire")
        
        # Test stats
        stats = test_registry.get_registry_stats()
        print(f"✅ Registry stats: {json.dumps(stats, indent=2)}")
        
        # Cleanup
        if os.path.exists("/tmp/test_registry.json"):
            os.remove("/tmp/test_registry.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Registry test failed: {e}")
        return False

def test_container_status():
    """Test container status tracking"""
    print("\n=== TESTING CONTAINER STATUS TRACKER ===")
    
    try:
        from bitten_core.container_status_tracker import ContainerStatusTracker
        
        tracker = ContainerStatusTracker()
        
        # Test with existing container
        test_container = "hydrax_engine_node_v7"
        print(f"Checking status for container: {test_container}")
        
        status = tracker.check_container_status(test_container)
        print(f"✅ Container status check completed")
        print(f"   Status: {status.status}")
        print(f"   MT5 Running: {status.mt5_running}")
        print(f"   Balance: ${status.account_balance}")
        print(f"   Last Check: {status.last_check}")
        
        # Test status message formatting
        message = tracker.format_container_status_message(test_container)
        print(f"✅ Status message formatted")
        print(f"Message preview: {message[:100]}...")
        
        # Test system overview
        overview = tracker.get_system_overview()
        print(f"✅ System overview generated")
        print(f"Overview preview: {overview[:150]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Container status test failed: {e}")
        return False

def test_integration():
    """Test integration between components"""
    print("\n=== TESTING SYSTEM INTEGRATION ===")
    
    try:
        from bitten_core.user_registry_manager import get_user_registry_manager
        from bitten_core.container_status_tracker import get_container_status_tracker
        
        registry = get_user_registry_manager()
        tracker = get_container_status_tracker()
        
        print("✅ Successfully imported all components")
        
        # Test that registry and tracker can work together
        test_user = "integration_test_456"
        container = f"mt5_user_{test_user}"
        
        # Register user
        registry.register_user(test_user, "integration_test", container)
        
        # Get container name from registry
        retrieved_container = registry.get_container_name(test_user)
        if retrieved_container != container:
            print(f"❌ Container name mismatch: {retrieved_container} != {container}")
            return False
        
        print("✅ Registry-container integration successful")
        
        # Test credential parsing (from connect command)
        test_message = """/connect
Login: 843859
Password: TestPass123
Server: Coinexx-Demo"""
        
        lines = test_message.split('\n')
        login_id = None
        password = None
        server_name = None
        
        for line in lines:
            line = line.strip()
            if line.lower().startswith('login:'):
                login_id = line.split(':', 1)[1].strip()
            elif line.lower().startswith('password:'):
                password = line.split(':', 1)[1].strip()
            elif line.lower().startswith('server:'):
                server_name = line.split(':', 1)[1].strip()
        
        if login_id and password and server_name:
            print("✅ Credential parsing works correctly")
        else:
            print("❌ Credential parsing failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_docker_containers():
    """Test Docker container access"""
    print("\n=== TESTING DOCKER CONTAINER ACCESS ===")
    
    try:
        import docker
        
        client = docker.from_env()
        containers = client.containers.list(all=True)
        
        print(f"Found {len(containers)} containers")
        
        # Look for MT5 containers
        mt5_containers = [c for c in containers if 'mt5' in c.name.lower() or 'hydrax' in c.name.lower()]
        
        if not mt5_containers:
            print("❌ No MT5/HydraX containers found")
            return False
        
        print(f"✅ Found {len(mt5_containers)} MT5/HydraX containers:")
        
        for container in mt5_containers:
            print(f"   - {container.name} (status: {container.status})")
            
            # Test basic container access
            try:
                result = container.exec_run(['echo', 'test'])
                if result.exit_code == 0:
                    print(f"   ✅ {container.name} accessible")
                else:
                    print(f"   ❌ {container.name} not accessible")
            except Exception as e:
                print(f"   ❌ {container.name} error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Docker test failed: {e}")
        return False

def main():
    """Run all infrastructure tests"""
    print("🧠 HYDRAX INFRASTRUCTURE COMPLETE TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Broker Server Files", test_srv_files),
        ("User Registry System", test_user_registry), 
        ("Container Status Tracker", test_container_status),
        ("System Integration", test_integration),
        ("Docker Container Access", test_docker_containers)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Infrastructure is ready!")
        return True
    else:
        print("⚠️  Some tests failed - check logs above")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)