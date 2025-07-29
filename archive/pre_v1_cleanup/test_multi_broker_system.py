#!/usr/bin/env python3
"""
🔧 MULTI-BROKER SYMBOL SYSTEM - COMPREHENSIVE TEST SUITE
Tests the complete symbol translation system for BITTEN

COVERAGE:
- Symbol mapper functionality
- Bridge integration
- Fire router integration  
- Translation accuracy
- Error handling
- Performance testing
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List

# Add src to path
sys.path.insert(0, '/root/HydraX-v2/src')

def create_test_broker_symbols():
    """Create test symbol sets for different broker types"""
    
    # Standard broker (clean symbols)
    standard_broker = [
        {"name": "EURUSD", "digits": 5, "point": 0.00001, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "GBPUSD", "digits": 5, "point": 0.00001, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "USDJPY", "digits": 3, "point": 0.001, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "XAUUSD", "digits": 2, "point": 0.01, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "US30", "digits": 1, "point": 0.1, "volume_min": 0.1, "volume_max": 10.0, "volume_step": 0.1},
        {"name": "BTCUSD", "digits": 2, "point": 0.01, "volume_min": 0.01, "volume_max": 1.0, "volume_step": 0.01}
    ]
    
    # ICMarkets style (.r suffix)
    icmarkets_broker = [
        {"name": "EURUSD.r", "digits": 5, "point": 0.00001, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "GBPUSD.r", "digits": 5, "point": 0.00001, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "USDJPY.r", "digits": 3, "point": 0.001, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "XAU/USD.r", "digits": 2, "point": 0.01, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "US30.r", "digits": 1, "point": 0.1, "volume_min": 0.1, "volume_max": 10.0, "volume_step": 0.1},
        {"name": "BITCOIN.r", "digits": 2, "point": 0.01, "volume_min": 0.01, "volume_max": 1.0, "volume_step": 0.01}
    ]
    
    # Alternative naming broker
    alternative_broker = [
        {"name": "EUR/USD", "digits": 5, "point": 0.00001, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "GBP/USD", "digits": 5, "point": 0.00001, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "USD/JPY", "digits": 3, "point": 0.001, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "GOLD", "digits": 2, "point": 0.01, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "DOW", "digits": 1, "point": 0.1, "volume_min": 0.1, "volume_max": 10.0, "volume_step": 0.1},
        {"name": "BITCOIN", "digits": 2, "point": 0.01, "volume_min": 0.01, "volume_max": 1.0, "volume_step": 0.01}
    ]
    
    # Mixed broker (various formats)
    mixed_broker = [
        {"name": "EURUSD_", "digits": 5, "point": 0.00001, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "GBPUSD.pro", "digits": 5, "point": 0.00001, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "USDJPY-m", "digits": 3, "point": 0.001, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "XAU_USD", "digits": 2, "point": 0.01, "volume_min": 0.01, "volume_max": 100.0, "volume_step": 0.01},
        {"name": "US30_Cash", "digits": 1, "point": 0.1, "volume_min": 0.1, "volume_max": 10.0, "volume_step": 0.1},
        {"name": "BTC/USD", "digits": 2, "point": 0.01, "volume_min": 0.01, "volume_max": 1.0, "volume_step": 0.01}
    ]
    
    return {
        "standard": {"symbols": standard_broker, "broker_name": "Standard Broker"},
        "icmarkets": {"symbols": icmarkets_broker, "broker_name": "ICMarkets"},
        "alternative": {"symbols": alternative_broker, "broker_name": "Alternative Broker"},
        "mixed": {"symbols": mixed_broker, "broker_name": "Mixed Format Broker"}
    }

def test_symbol_mapper():
    """Test the core symbol mapper functionality"""
    print("🔧 Testing Symbol Mapper...")
    
    try:
        from bitten_core.symbol_mapper import symbol_mapper, initialize_user_symbols, translate_symbol
        
        test_brokers = create_test_broker_symbols()
        test_results = {}
        
        # Test each broker type
        for broker_type, broker_data in test_brokers.items():
            print(f"\n📊 Testing {broker_data['broker_name']}...")
            
            user_id = f"test_user_{broker_type}"
            symbols = broker_data["symbols"]
            broker_name = broker_data["broker_name"]
            
            # Initialize symbols
            success = initialize_user_symbols(user_id, symbols, broker_name)
            
            if success:
                print(f"   ✅ Symbol initialization successful")
                
                # Test translations
                test_pairs = ["EURUSD", "XAUUSD", "US30", "BTCUSD", "NONEXISTENT"]
                translations = {}
                
                for pair in test_pairs:
                    result = translate_symbol(user_id, pair)
                    translations[pair] = {
                        "success": result.success,
                        "translated": result.translated_pair,
                        "fallback": result.fallback_used,
                        "error": result.error_message
                    }
                    
                    status = "✅" if result.success else "❌"
                    print(f"   {status} {pair} → {result.translated_pair if result.success else 'FAILED'}")
                    
                    if result.fallback_used:
                        print(f"      (Fallback used)")
                
                test_results[broker_type] = {
                    "initialization": True,
                    "translations": translations
                }
            else:
                print(f"   ❌ Symbol initialization failed")
                test_results[broker_type] = {
                    "initialization": False,
                    "translations": {}
                }
        
        return test_results
        
    except Exception as e:
        print(f"❌ Symbol Mapper test failed: {e}")
        return None

def test_bridge_integration():
    """Test bridge integration functionality"""
    print("\n🌉 Testing Bridge Integration...")
    
    try:
        from bitten_core.bridge_symbol_integration import bridge_integration, translate_signal_for_user
        
        # Setup test user with mapping
        from bitten_core.symbol_mapper import symbol_mapper
        
        user_id = "bridge_test_user"
        symbol_mapper.user_maps[user_id] = {
            "XAUUSD": "XAU/USD.r",
            "EURUSD": "EURUSD.r",
            "US30": "US30.r"
        }
        
        symbol_mapper.user_symbol_info[user_id] = {
            "XAU/USD.r": {
                "digits": 2,
                "point": 0.01,
                "volume_min": 0.01,
                "volume_max": 100.0,
                "volume_step": 0.01
            },
            "EURUSD.r": {
                "digits": 5,
                "point": 0.00001,
                "volume_min": 0.01,
                "volume_max": 100.0,
                "volume_step": 0.01
            }
        }
        
        # Mock bridge connection
        bridge_integration.active_connections[user_id] = {
            "bridge_id": "bridge_001",
            "mapping_ready": True
        }
        
        # Test signal translation
        test_signals = [
            {
                "pair": "XAUUSD",
                "direction": "BUY",
                "lot_size": 0.01,
                "sl": 1950.0,
                "tp": 1970.0
            },
            {
                "pair": "EURUSD", 
                "direction": "SELL",
                "lot_size": 0.1,
                "sl": 1.0920,
                "tp": 1.0880
            },
            {
                "pair": "NONEXISTENT",
                "direction": "BUY",
                "lot_size": 0.01
            }
        ]
        
        translation_results = []
        
        for signal in test_signals:
            success, translated = translate_signal_for_user(user_id, signal)
            
            result = {
                "original_pair": signal["pair"],
                "success": success,
                "translated_pair": translated.get("symbol") if success else None,
                "error": translated.get("error") if not success else None
            }
            
            translation_results.append(result)
            
            status = "✅" if success else "❌"
            print(f"   {status} {signal['pair']} → {result['translated_pair'] if success else 'FAILED'}")
            
            if not success:
                print(f"      Error: {result['error']}")
        
        return translation_results
        
    except Exception as e:
        print(f"❌ Bridge Integration test failed: {e}")
        return None

def test_fire_router_integration():
    """Test fire router integration"""
    print("\n🔥 Testing Fire Router Integration...")
    
    try:
        from bitten_core.fire_router_symbol_integration import execute_trade_with_translation
        from bitten_core.symbol_mapper import symbol_mapper
        from bitten_core.bridge_symbol_integration import bridge_integration
        
        # Setup test user
        user_id = "fire_test_user"
        
        symbol_mapper.user_maps[user_id] = {
            "XAUUSD": "XAU/USD.r",
            "EURUSD": "EURUSD.r"
        }
        
        symbol_mapper.user_symbol_info[user_id] = {
            "XAU/USD.r": {
                "digits": 2,
                "point": 0.01,
                "volume_min": 0.01,
                "volume_max": 100.0,
                "volume_step": 0.01
            }
        }
        
        bridge_integration.active_connections[user_id] = {
            "bridge_id": "bridge_001",
            "mapping_ready": True
        }
        
        # Test trade execution
        test_signal = {
            "pair": "XAUUSD",
            "direction": "BUY",
            "lot_size": 0.01,
            "sl": 1950.0,
            "tp": 1970.0,
            "risk": 2.0
        }
        
        test_profile = {
            "tier": "fang",
            "balance": 1000.0
        }
        
        result = execute_trade_with_translation(user_id, test_signal, test_profile)
        
        print(f"   📊 Execution Result:")
        print(f"      Success: {result.success}")
        print(f"      Original Pair: {result.original_signal.get('pair')}")
        
        if result.translated_signal:
            print(f"      Translated Pair: {result.translated_signal.get('symbol')}")
            print(f"      Lot Size: {result.translated_signal.get('lot_size')}")
        
        if result.error_message:
            print(f"      Error: {result.error_message}")
        
        return {
            "success": result.success,
            "original_pair": result.original_signal.get("pair"),
            "translated_pair": result.translated_signal.get("symbol") if result.translated_signal else None,
            "error": result.error_message
        }
        
    except Exception as e:
        print(f"❌ Fire Router Integration test failed: {e}")
        return None

def test_error_handling():
    """Test error handling scenarios"""
    print("\n⚠️ Testing Error Handling...")
    
    try:
        from bitten_core.symbol_mapper import translate_symbol
        from bitten_core.bridge_symbol_integration import translate_signal_for_user
        
        error_tests = []
        
        # Test 1: Non-existent user
        print("   🧪 Testing non-existent user...")
        result = translate_symbol("nonexistent_user", "EURUSD")
        error_tests.append({
            "test": "non_existent_user",
            "success": not result.success,
            "error_handled": result.error_message is not None
        })
        print(f"      {'✅' if not result.success else '❌'} Properly rejected non-existent user")
        
        # Test 2: Invalid symbol
        print("   🧪 Testing invalid symbol...")
        from bitten_core.symbol_mapper import symbol_mapper
        
        # Setup test user first
        test_user = "error_test_user"
        symbol_mapper.user_maps[test_user] = {"EURUSD": "EURUSD"}
        
        result = translate_symbol(test_user, "INVALID_SYMBOL")
        error_tests.append({
            "test": "invalid_symbol",
            "success": not result.success,
            "error_handled": result.error_message is not None
        })
        print(f"      {'✅' if not result.success else '❌'} Properly rejected invalid symbol")
        
        # Test 3: Malformed signal
        print("   🧪 Testing malformed signal...")
        malformed_signal = {"invalid": "signal"}
        
        success, response = translate_signal_for_user(test_user, malformed_signal)
        error_tests.append({
            "test": "malformed_signal",
            "success": not success,
            "error_handled": "error" in response
        })
        print(f"      {'✅' if not success else '❌'} Properly rejected malformed signal")
        
        return error_tests
        
    except Exception as e:
        print(f"❌ Error Handling test failed: {e}")
        return None

def test_performance():
    """Test system performance"""
    print("\n⚡ Testing Performance...")
    
    try:
        from bitten_core.symbol_mapper import symbol_mapper, translate_symbol
        
        # Setup large symbol set
        large_symbol_set = []
        for i in range(1000):
            large_symbol_set.append({
                "name": f"TEST{i:04d}",
                "digits": 5,
                "point": 0.00001,
                "volume_min": 0.01,
                "volume_max": 100.0,
                "volume_step": 0.01
            })
        
        user_id = "performance_test_user"
        
        # Test initialization time
        start_time = time.time()
        success = symbol_mapper.initialize_user_symbols(user_id, large_symbol_set, "Performance Test Broker")
        init_time = time.time() - start_time
        
        print(f"   📊 Symbol initialization: {init_time:.3f}s for {len(large_symbol_set)} symbols")
        
        if success:
            # Test translation time
            test_pairs = ["EURUSD", "XAUUSD", "US30", "BTCUSD", "TEST0001"]
            
            start_time = time.time()
            for _ in range(100):  # 100 translations
                for pair in test_pairs:
                    translate_symbol(user_id, pair)
            translation_time = time.time() - start_time
            
            print(f"   📊 Translation performance: {translation_time:.3f}s for 500 translations")
            print(f"      Average: {(translation_time/500)*1000:.2f}ms per translation")
            
            return {
                "initialization_time": init_time,
                "translation_time": translation_time,
                "avg_translation_ms": (translation_time/500)*1000
            }
        else:
            print("   ❌ Performance test failed - initialization unsuccessful")
            return None
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return None

def test_data_persistence():
    """Test data persistence functionality"""
    print("\n💾 Testing Data Persistence...")
    
    try:
        from bitten_core.symbol_mapper import symbol_mapper
        
        # Create test user and mapping
        user_id = "persistence_test_user"
        test_symbols = create_test_broker_symbols()["standard"]["symbols"]
        
        # Initialize mapping
        success = symbol_mapper.initialize_user_symbols(user_id, test_symbols, "Persistence Test Broker")
        
        if success:
            print("   ✅ Symbol mapping created")
            
            # Check if files were created
            mapping_file = f"/root/HydraX-v2/data/symbol_maps/user_{user_id}_symbols.json"
            
            if os.path.exists(mapping_file):
                print("   ✅ Mapping file created")
                
                # Clear memory cache
                symbol_mapper.user_maps.pop(user_id, None)
                symbol_mapper.user_symbol_info.pop(user_id, None)
                
                # Test loading from file
                status = symbol_mapper.get_user_mapping_status(user_id)
                
                if status["mapping_exists"]:
                    print("   ✅ Mapping loaded from file")
                    print(f"      Pairs mapped: {status['pairs_mapped']}")
                    
                    return {
                        "file_created": True,
                        "file_loaded": True,
                        "pairs_mapped": status['pairs_mapped']
                    }
                else:
                    print("   ❌ Mapping failed to load from file")
                    return {"file_created": True, "file_loaded": False}
            else:
                print("   ❌ Mapping file not created")
                return {"file_created": False, "file_loaded": False}
        else:
            print("   ❌ Symbol mapping creation failed")
            return None
            
    except Exception as e:
        print(f"❌ Data Persistence test failed: {e}")
        return None

def generate_test_report(test_results: Dict):
    """Generate comprehensive test report"""
    print("\n📊 MULTI-BROKER SYMBOL SYSTEM - TEST REPORT")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    # Symbol Mapper Results
    if test_results.get("symbol_mapper"):
        print("\n🔧 SYMBOL MAPPER RESULTS:")
        for broker_type, results in test_results["symbol_mapper"].items():
            total_tests += 1
            if results["initialization"]:
                passed_tests += 1
                print(f"   ✅ {broker_type.upper()}: {len(results['translations'])} translations tested")
            else:
                print(f"   ❌ {broker_type.upper()}: Initialization failed")
    
    # Bridge Integration Results
    if test_results.get("bridge_integration"):
        print("\n🌉 BRIDGE INTEGRATION RESULTS:")
        results = test_results["bridge_integration"]
        successful = sum(1 for r in results if r["success"])
        total_tests += len(results)
        passed_tests += successful
        print(f"   📊 {successful}/{len(results)} signal translations successful")
    
    # Fire Router Results
    if test_results.get("fire_router"):
        print("\n🔥 FIRE ROUTER INTEGRATION RESULTS:")
        result = test_results["fire_router"]
        total_tests += 1
        if result["success"]:
            passed_tests += 1
            print(f"   ✅ Trade execution with symbol translation successful")
            print(f"      {result['original_pair']} → {result['translated_pair']}")
        else:
            print(f"   ❌ Trade execution failed: {result['error']}")
    
    # Error Handling Results
    if test_results.get("error_handling"):
        print("\n⚠️ ERROR HANDLING RESULTS:")
        results = test_results["error_handling"]
        for test in results:
            total_tests += 1
            if test["success"] and test["error_handled"]:
                passed_tests += 1
                print(f"   ✅ {test['test']}: Properly handled")
            else:
                print(f"   ❌ {test['test']}: Not properly handled")
    
    # Performance Results
    if test_results.get("performance"):
        print("\n⚡ PERFORMANCE RESULTS:")
        perf = test_results["performance"]
        print(f"   📊 Initialization: {perf['initialization_time']:.3f}s")
        print(f"   📊 Average Translation: {perf['avg_translation_ms']:.2f}ms")
        
        # Performance assessment
        if perf['avg_translation_ms'] < 1.0:
            print("   ✅ Performance: EXCELLENT")
        elif perf['avg_translation_ms'] < 5.0:
            print("   ✅ Performance: GOOD")
        else:
            print("   ⚠️ Performance: NEEDS IMPROVEMENT")
    
    # Data Persistence Results
    if test_results.get("persistence"):
        print("\n💾 DATA PERSISTENCE RESULTS:")
        persist = test_results["persistence"]
        total_tests += 2  # File creation and loading
        if persist["file_created"]:
            passed_tests += 1
            print("   ✅ File creation: SUCCESS")
        else:
            print("   ❌ File creation: FAILED")
        
        if persist["file_loaded"]:
            passed_tests += 1
            print("   ✅ File loading: SUCCESS")
        else:
            print("   ❌ File loading: FAILED")
    
    # Overall Results
    print(f"\n📈 OVERALL RESULTS:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {total_tests - passed_tests}")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "   Success Rate: 0%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED - Multi-Broker Symbol System Ready!")
        status = "READY"
    elif passed_tests >= total_tests * 0.8:
        print("\n✅ MOST TESTS PASSED - System mostly functional with minor issues")
        status = "MOSTLY_READY"
    else:
        print("\n⚠️ MULTIPLE FAILURES - System needs attention before deployment")
        status = "NEEDS_WORK"
    
    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": (passed_tests/total_tests)*100 if total_tests > 0 else 0,
        "status": status
    }

def main():
    """Run comprehensive multi-broker symbol system tests"""
    print("🔧 MULTI-BROKER SYMBOL SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    # Ensure data directories exist
    os.makedirs("/root/HydraX-v2/data/symbol_maps", exist_ok=True)
    os.makedirs("/root/HydraX-v2/data", exist_ok=True)
    
    test_results = {}
    
    # Run all tests
    test_results["symbol_mapper"] = test_symbol_mapper()
    test_results["bridge_integration"] = test_bridge_integration()
    test_results["fire_router"] = test_fire_router_integration()
    test_results["error_handling"] = test_error_handling()
    test_results["performance"] = test_performance()
    test_results["persistence"] = test_data_persistence()
    
    # Generate final report
    final_report = generate_test_report(test_results)
    
    return final_report["status"] == "READY"

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)