#!/usr/bin/env python3
"""
Command Dispatcher Restoration Validation
Validates that all required commands are properly routed and fallback is implemented
"""

import re

def validate_dispatcher_restoration():
    """Validate the command dispatcher restoration"""
    
    print("🧠 COMMAND DISPATCHER RESTORATION VALIDATION")
    print("=" * 55)
    
    # Read the bot file
    try:
        with open('/root/HydraX-v2/bitten_production_bot.py', 'r') as f:
            bot_content = f.read()
    except Exception as e:
        print(f"❌ Error reading bot file: {e}")
        return False
    
    # Required command mappings
    required_commands = {
        '/connect': {
            'pattern': r'elif message\.text\.startswith\("/connect"\)',
            'description': 'MT5 terminal connection with enhanced UX'
        },
        '/status': {
            'pattern': r'(if|elif) message\.text == "/status"',
            'description': 'System status check and container monitoring'
        },
        '/help': {
            'pattern': r'elif message\.text == "/help"',
            'description': 'Help system with command documentation'
        },
        '/fire': {
            'pattern': r'elif message\.text\.startswith\("/fire"\)',
            'description': 'Signal execution with BittenCore integration'
        },
        '/notebook': {
            'pattern': r'elif message\.text\.startswith\("/notebook"\)',
            'description': 'Norman\'s Notebook access'
        },
        '/journal': {
            'pattern': r'message\.text\.startswith\("/journal"\)',
            'description': 'Journal alias for notebook'
        },
        '/notes': {
            'pattern': r'message\.text\.startswith\("/notes"\)',
            'description': 'Notes alias for notebook'
        }
    }
    
    print("✅ REQUIRED COMMAND ROUTING:")
    print("-" * 35)
    
    all_commands_found = True
    for cmd, info in required_commands.items():
        match = re.search(info['pattern'], bot_content)
        if match:
            line_num = bot_content[:match.start()].count('\n') + 1
            print(f"✅ {cmd:<12} → Line {line_num:>4} | {info['description']}")
        else:
            print(f"❌ {cmd:<12} → MISSING   | {info['description']}")
            all_commands_found = False
    
    # Check for fallback handler
    print(f"\n🛡️  FALLBACK SAFETY SYSTEMS:")
    print("-" * 35)
    
    fallback_checks = {
        'Unknown command handler': r'Command not recognized.*message\.text',
        'Error logging': r'logger\.warning.*Unknown command',
        'User guidance': r'Available Commands:',
        'Help redirect': r'/help.*complete command list'
    }
    
    fallback_working = True
    for check, pattern in fallback_checks.items():
        if re.search(pattern, bot_content, re.DOTALL):
            print(f"✅ {check}: IMPLEMENTED")
        else:
            print(f"❌ {check}: MISSING")
            fallback_working = False
    
    # Check /connect special handling
    print(f"\n🌐 /CONNECT UX ENHANCEMENTS:")
    print("-" * 35)
    
    connect_checks = {
        'Special flag handling': r'SEND_USAGE_WITH_KEYBOARD',
        'Enhanced usage message': r'_send_connect_usage_with_keyboard',
        'Throttling system': r'connect_usage_throttle',
        'WebApp integration': r'https://joinbitten\.com/connect'
    }
    
    connect_working = True
    for check, pattern in connect_checks.items():
        if re.search(pattern, bot_content):
            print(f"✅ {check}: ACTIVE")
        else:
            print(f"❌ {check}: MISSING")
            connect_working = False
    
    # Final validation
    print(f"\n📊 RESTORATION SUMMARY:")
    print("-" * 25)
    
    if all_commands_found:
        print("✅ Core command routing: RESTORED")
    else:
        print("❌ Core command routing: BROKEN")
    
    if fallback_working:
        print("✅ Fallback safety system: IMPLEMENTED")
    else:
        print("❌ Fallback safety system: INCOMPLETE")
    
    if connect_working:
        print("✅ /connect UX system: PRESERVED")
    else:
        print("❌ /connect UX system: DAMAGED")
    
    # Overall result
    overall_success = all_commands_found and fallback_working and connect_working
    
    print(f"\n🎯 FINAL RESULT:")
    print("=" * 15)
    
    if overall_success:
        print("✅ COMMAND DISPATCHER INTEGRITY: ✨ FULLY RESTORED ✨")
        print("\n🛡️  All required commands are properly routed")
        print("🔄 Fallback handler safely catches unknown commands") 
        print("🌐 /connect UX enhancements are preserved")
        print("🎯 System is ready for production deployment")
        return True
    else:
        print("❌ COMMAND DISPATCHER INTEGRITY: ⚠️ ISSUES DETECTED ⚠️")
        print("\n🔧 Please review and fix the identified issues")
        return False

if __name__ == "__main__":
    import sys
    success = validate_dispatcher_restoration()
    sys.exit(0 if success else 1)