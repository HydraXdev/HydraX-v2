#!/usr/bin/env python3
"""
Test and diagnose the inline menu issue
"""

def test_menu_components():
    """Test individual components of the menu system"""
    
    print("🔍 Diagnosing Inline Menu Issue")
    print("=" * 40)
    
    # Test 1: Check if InlineKeyboard imports work
    try:
        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
        print("✅ InlineKeyboard imports working")
    except ImportError as e:
        print(f"❌ InlineKeyboard import failed: {e}")
        return False
    
    # Test 2: Check if Intel Command Center imports work
    try:
        import sys
        sys.path.insert(0, 'src')
        from bitten_core.intel_command_center import IntelCommandCenter
        print("✅ Intel Command Center import working")
        
        # Test instantiation
        intel_center = IntelCommandCenter()
        print("✅ Intel Command Center instantiation working")
    except ImportError as e:
        print(f"❌ Intel Command Center import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Intel Command Center instantiation failed: {e}")
        return False
    
    # Test 3: Check if the menu creation works
    try:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔫 COMBAT OPS", callback_data="menu_combat_ops"),
                InlineKeyboardButton("📚 FIELD MANUAL", callback_data="menu_field_manual")
            ],
            [
                InlineKeyboardButton("💰 TIER INTEL", callback_data="menu_tier_intel"),
                InlineKeyboardButton("🎖️ XP ECONOMY", callback_data="menu_xp_economy")
            ],
            [
                InlineKeyboardButton("🌐 MISSION HUD", url="https://joinbitten.com/hud"),
                InlineKeyboardButton("❌ Close Menu", callback_data="menu_close")
            ]
        ])
        print("✅ Menu keyboard creation working")
        print(f"   Keyboard has {len(keyboard.keyboard)} rows")
    except Exception as e:
        print(f"❌ Menu keyboard creation failed: {e}")
        return False
    
    # Test 4: Check asyncio compatibility
    try:
        import asyncio
        print("✅ Asyncio import working")
        
        # Test if we can create an event loop
        loop = asyncio.new_event_loop()
        loop.close()
        print("✅ Asyncio event loop creation working")
    except Exception as e:
        print(f"❌ Asyncio test failed: {e}")
        return False
    
    return True

def test_bot_integration():
    """Test if the bot integration is working"""
    
    print("\n🤖 Testing Bot Integration")
    print("=" * 30)
    
    try:
        # Check if there are conflicts with multiple bot instances
        import psutil
        
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python3' and proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'bitten' in cmdline.lower():
                        python_processes.append({
                            'pid': proc.info['pid'],
                            'cmdline': cmdline
                        })
            except:
                pass
        
        print(f"📊 Found {len(python_processes)} BITTEN bot processes:")
        for proc in python_processes:
            print(f"   PID {proc['pid']}: {proc['cmdline']}")
        
        if len(python_processes) > 1:
            print("⚠️  Multiple bot instances detected - this could cause conflicts!")
            return False
        else:
            print("✅ Single bot instance running")
            return True
            
    except Exception as e:
        print(f"❌ Bot integration test failed: {e}")
        return False

def test_callback_handler():
    """Test the callback handler logic"""
    
    print("\n📞 Testing Callback Handler")
    print("=" * 28)
    
    try:
        # Test callback data patterns
        test_callbacks = [
            "menu_combat_ops",
            "menu_field_manual", 
            "menu_tier_intel",
            "menu_xp_economy",
            "menu_close"
        ]
        
        for callback_data in test_callbacks:
            # Test if the callback pattern matching works
            if callback_data.startswith(("menu_", "combat_", "field_", "tier_", "xp_", "help_", "tool_", "bot_")):
                print(f"✅ Callback pattern match: {callback_data}")
            else:
                print(f"❌ Callback pattern failed: {callback_data}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Callback handler test failed: {e}")
        return False

def check_recent_changes():
    """Check for recent changes that might have broken the menu"""
    
    print("\n🔍 Checking Recent Changes")
    print("=" * 30)
    
    try:
        import os
        import time
        
        # Check modification times of key files
        key_files = [
            "/root/HydraX-v2/bitten_production_bot.py",
            "/root/HydraX-v2/deploy_intel_command_center.py"
        ]
        
        for file_path in key_files:
            if os.path.exists(file_path):
                mod_time = os.path.getmtime(file_path)
                age_hours = (time.time() - mod_time) / 3600
                print(f"📁 {os.path.basename(file_path)}: {age_hours:.1f} hours ago")
                
                if age_hours < 2:
                    print(f"   ⚠️  Recently modified - potential cause")
            else:
                print(f"❌ {file_path} not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Recent changes check failed: {e}")
        return False

def main():
    """Run all diagnostic tests"""
    
    print("🔧 INLINE MENU DIAGNOSTIC TOOL")
    print("=" * 50)
    
    results = []
    
    # Test 1: Menu components
    results.append(test_menu_components())
    
    # Test 2: Bot integration
    results.append(test_bot_integration())
    
    # Test 3: Callback handler
    results.append(test_callback_handler())
    
    # Test 4: Recent changes
    results.append(check_recent_changes())
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "Menu Components",
        "Bot Integration",
        "Callback Handler",
        "Recent Changes"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\nOVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🤔 All components appear to be working...")
        print("💡 The issue might be:")
        print("   • Multiple bot instances causing conflicts")
        print("   • Telegram API rate limiting")
        print("   • Network connectivity issues")
        print("   • User not typing /menu command")
    else:
        print("\n🔧 Issues found - check the failed tests above")
        
    print("\n📋 TROUBLESHOOTING STEPS:")
    print("1. Kill all bot instances: pkill -f bitten_production_bot")
    print("2. Start single bot instance: python3 bitten_production_bot.py")
    print("3. Test /menu command in Telegram")
    print("4. Check bot logs for errors")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)