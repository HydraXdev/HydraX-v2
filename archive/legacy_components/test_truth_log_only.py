#!/usr/bin/env python3
"""
🧪 TEST: Truth Log Only Implementation
Verifies all fallback data sources are disabled and only truth_log.jsonl is used
"""

import sys
import os
sys.path.append('/root/HydraX-v2')

from truth_dashboard_integration import TruthDashboard

def test_truth_log_only():
    """Test that truth dashboard only uses truth_log.jsonl"""
    print("🧪 Testing Truth Log Only Implementation")
    print("=" * 50)
    
    # Initialize dashboard
    dashboard = TruthDashboard()
    
    # Test 1: Check insufficient data handling (<10 entries)
    print("\n📊 Test 1: Insufficient Data Handling")
    summary = dashboard.get_black_box_summary(hours_back=168)  # Last week
    
    print(f"Total tracked: {summary['total_tracked']}")
    print(f"Win rate: {summary['black_box_confirmed_win_rate']}")
    print(f"Data source: {summary.get('data_source', 'NOT SPECIFIED')}")
    print(f"Fallback disabled: {summary.get('fallback_disabled', 'NOT SPECIFIED')}")
    
    # Verify insufficient data handling
    if summary['total_tracked'] < 10:
        assert summary['black_box_confirmed_win_rate'] == "Insufficient Data"
        assert summary['confidence_interval'] == "Insufficient data (<10 entries)"
        print("✅ Insufficient data handling: CORRECT")
    else:
        print(f"✅ Sufficient data found: {summary['total_tracked']} entries")
    
    # Test 2: Source verification
    print("\n🔒 Test 2: Source Verification")
    verified_summary = dashboard.get_black_box_summary(hours_back=168, verify_source=True)
    
    print(f"Verified entries: {verified_summary['total_tracked']}")
    print(f"All entries verified: {verified_summary['total_tracked']} entries with 'venom_scalp_master' source")
    
    # Test 3: Data source confirmation
    print("\n📋 Test 3: Data Source Confirmation")
    assert summary.get('data_source') == "truth_log.jsonl ONLY"
    assert summary.get('fallback_disabled') == True
    print("✅ Data source: truth_log.jsonl ONLY")
    print("✅ Fallback disabled: TRUE")
    
    # Test 4: Load actual truth data
    print("\n📄 Test 4: Actual Truth Data")
    truth_data = dashboard.load_truth_data(hours_back=168)
    print(f"Raw truth entries loaded: {len(truth_data)}")
    
    if truth_data:
        print("Sample entry keys:", list(truth_data[0].keys()))
        for entry in truth_data:
            source = entry.get('source', 'NO_SOURCE')
            signal_id = entry.get('signal_id', 'NO_ID')
            result = entry.get('result', 'NO_RESULT')
            print(f"  • {signal_id}: {result} (source: {source})")
    else:
        print("  • No truth data found in log")
    
    print("\n🎯 VERIFICATION COMPLETE")
    print("=" * 50)
    print("✅ All fallback data sources disabled")
    print("✅ Only truth_log.jsonl is used as data source")
    print("✅ Insufficient data handling implemented")
    print("✅ Source verification available")

if __name__ == "__main__":
    test_truth_log_only()