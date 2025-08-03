#!/usr/bin/env python3
"""
ZMQ Deployment Verification Script
Checks that all ZMQ components are properly deployed and working
"""

import sys
import time
import json
from typing import Dict, List, Tuple

def check_imports() -> Tuple[bool, List[str]]:
    """
    Check all required imports are available
    """
    errors = []
    success = True
    
    required_imports = [
        ('zmq', 'ZeroMQ library'),
        ('zmq_bitten_controller', 'BITTEN ZMQ Controller'),
        ('zmq_telemetry_service', 'Telemetry Ingestion Service'),
        ('zmq_xp_integration', 'XP Integration Module'),
        ('zmq_risk_integration', 'Risk Integration Module'),
        ('zmq_migration_helpers', 'Migration Helpers')
    ]
    
    for module_name, description in required_imports:
        try:
            __import__(module_name)
            print(f"✅ {description} ({module_name})")
        except ImportError as e:
            errors.append(f"❌ {description} ({module_name}): {e}")
            success = False
    
    return success, errors

def check_fire_router_integration() -> Tuple[bool, str]:
    """
    Check if fire_router.py has ZMQ integration
    """
    try:
        with open('/root/HydraX-v2/src/bitten_core/fire_router.py', 'r') as f:
            content = f.read()
            
        if 'zmq_bitten_controller' in content and 'execute_bitten_trade' in content:
            return True, "Fire router has ZMQ integration"
        else:
            return False, "Fire router missing ZMQ integration"
    except Exception as e:
        return False, f"Error checking fire router: {e}"

def check_zmq_controller() -> Tuple[bool, str]:
    """
    Test ZMQ controller functionality
    """
    try:
        from zmq_bitten_controller import BITTENZMQController
        
        # Create test controller
        controller = BITTENZMQController(command_port=5557, feedback_port=5558)
        
        # Test basic functionality (don't actually start to avoid port conflicts)
        if hasattr(controller, 'send_signal') and hasattr(controller, 'get_user_telemetry'):
            return True, "ZMQ controller API verified"
        else:
            return False, "ZMQ controller missing required methods"
            
    except Exception as e:
        return False, f"ZMQ controller test failed: {e}"

def check_telemetry_service() -> Tuple[bool, str]:
    """
    Check telemetry service setup
    """
    try:
        from zmq_telemetry_service import TelemetryIngestionService
        
        # Create test service
        service = TelemetryIngestionService(telemetry_port=5559)
        
        # Check methods
        required_methods = ['start', 'stop', 'get_user_telemetry', 'get_trade_results']
        missing = [m for m in required_methods if not hasattr(service, m)]
        
        if not missing:
            return True, "Telemetry service API verified"
        else:
            return False, f"Telemetry service missing methods: {missing}"
            
    except Exception as e:
        return False, f"Telemetry service test failed: {e}"

def check_migration_helpers() -> Tuple[bool, str]:
    """
    Check migration helper configuration
    """
    try:
        from zmq_migration_helpers import (
            USE_ZMQ, ZMQ_DUAL_WRITE, check_migration_status
        )
        
        status = check_migration_status()
        
        info = (f"Migration mode: {status['mode']}, "
                f"ZMQ available: {status['zmq_available']}")
        
        return True, info
        
    except Exception as e:
        return False, f"Migration helpers test failed: {e}"

def check_ea_configuration() -> Dict:
    """
    Check EA configuration (informational)
    """
    info = {
        'ea_version': 'BITTENBridge_TradeExecutor_ZMQ_v7_CLIENT.mq5',
        'connection_type': 'CLIENT (connects to controller)',
        'command_endpoint': 'tcp://134.199.204.67:5555',
        'feedback_endpoint': 'tcp://134.199.204.67:5556',
        'note': 'EA connects outward to controller, controller must bind ports'
    }
    return info

def generate_deployment_checklist() -> List[str]:
    """
    Generate deployment checklist
    """
    checklist = [
        "1. Set environment variables:",
        "   export USE_ZMQ=true",
        "   export ZMQ_DUAL_WRITE=true  # For safety during transition",
        "",
        "2. Start ZMQ controller on remote server (134.199.204.67):",
        "   python3 zmq_bitten_controller.py",
        "",
        "3. Start telemetry ingestion service:",
        "   python3 zmq_telemetry_service.py",
        "",
        "4. Verify EA is running with ZMQ v7 CLIENT:",
        "   - Check MT5 Expert tab for connection messages",
        "   - Verify libzmq.dll is in Libraries folder",
        "",
        "5. Test signal flow:",
        "   - Send test signal via fire command",
        "   - Monitor telemetry service output",
        "   - Check trade execution in MT5",
        "",
        "6. Monitor migration:",
        "   - Check both fire.txt and ZMQ channels",
        "   - Verify dual-write is working",
        "   - Monitor migration statistics",
        "",
        "7. After verification:",
        "   - Set ZMQ_DUAL_WRITE=false to disable fire.txt",
        "   - Monitor for any issues",
        "   - Remove fire.txt code after stable period"
    ]
    return checklist

def main():
    """
    Run deployment verification
    """
    print("🔍 ZMQ Deployment Verification")
    print("="*50)
    
    # Check imports
    print("\n📦 Checking required modules...")
    imports_ok, import_errors = check_imports()
    if not imports_ok:
        print("\n❌ Import errors found:")
        for error in import_errors:
            print(f"  {error}")
        print("\nPlease install missing dependencies")
        sys.exit(1)
    
    # Check integrations
    print("\n🔧 Checking integrations...")
    
    # Fire router
    fr_ok, fr_msg = check_fire_router_integration()
    print(f"{'✅' if fr_ok else '❌'} Fire Router: {fr_msg}")
    
    # ZMQ controller
    zc_ok, zc_msg = check_zmq_controller()
    print(f"{'✅' if zc_ok else '❌'} ZMQ Controller: {zc_msg}")
    
    # Telemetry service
    ts_ok, ts_msg = check_telemetry_service()
    print(f"{'✅' if ts_ok else '❌'} Telemetry Service: {ts_msg}")
    
    # Migration helpers
    mh_ok, mh_msg = check_migration_helpers()
    print(f"{'✅' if mh_ok else '❌'} Migration Helpers: {mh_msg}")
    
    # EA info
    print("\n📡 EA Configuration:")
    ea_info = check_ea_configuration()
    for key, value in ea_info.items():
        print(f"  {key}: {value}")
    
    # Overall status
    all_ok = all([imports_ok, fr_ok, zc_ok, ts_ok, mh_ok])
    
    if all_ok:
        print("\n✅ All components verified successfully!")
        print("\n📋 Deployment Checklist:")
        for item in generate_deployment_checklist():
            print(item)
    else:
        print("\n❌ Some components failed verification")
        print("Please fix the issues before deployment")
        sys.exit(1)

if __name__ == "__main__":
    main()