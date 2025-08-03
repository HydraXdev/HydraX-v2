#!/usr/bin/env python3
"""
🎯 TRUTH TRACKING DEMO - Complete lifecycle demonstration
Shows how signals are tracked from generation to completion
"""

import time
import json
from signal_truth_tracker import tracker as truth_tracker

def demo_complete_signal_lifecycle():
    """Demonstrate complete signal lifecycle tracking"""
    print("🚀 TRUTH TRACKING SYSTEM DEMO")
    print("=" * 60)
    
    # Start truth tracking
    truth_tracker.start_monitoring()
    print(f"🎯 Truth tracking started - logging to {truth_tracker.truth_log_path}")
    
    # Demo 1: Generate a signal
    print("\n1️⃣ GENERATING SIGNAL...")
    signal_id = truth_tracker.log_signal_generated(
        symbol="EURUSD",
        direction="BUY",
        confidence=87.5,
        entry_price=1.0845,
        stop_loss=1.0825,
        take_profit=1.0885,
        source="demo_venom_v8",
        tcs_score=87.5,
        citadel_score=8.2,
        ml_filter_passed=True,
        fire_reason="momentum:85.2 vol:1.2"
    )
    print(f"✅ Signal generated: {signal_id}")
    
    # Demo 2: Fire the signal
    print("\n2️⃣ FIRING SIGNAL...")
    truth_tracker.log_signal_fired(signal_id, user_count=3)
    print(f"🔥 Signal fired to 3 users")
    
    # Demo 3: Generate another signal that gets filtered
    print("\n3️⃣ GENERATING FILTERED SIGNAL...")
    filtered_signal_id = truth_tracker.log_signal_generated(
        symbol="GBPUSD",
        direction="SELL", 
        confidence=65.0,
        entry_price=1.2735,
        stop_loss=1.2755,
        take_profit=1.2695,
        source="demo_venom_v8",
        tcs_score=65.0,
        citadel_score=4.1,
        ml_filter_passed=False,
        fire_reason="weak_momentum:55.0"
    )
    print(f"✅ Signal generated: {filtered_signal_id}")
    
    # Filter it
    truth_tracker.log_signal_filtered(filtered_signal_id, "citadel_shield_block")
    print(f"🚫 Signal filtered: CITADEL shield block")
    
    # Demo 4: Complete the first signal
    print("\n4️⃣ COMPLETING FIRST SIGNAL...")
    time.sleep(1)  # Simulate some runtime
    truth_tracker.log_signal_completed(signal_id, "WIN", 20.0, 45)
    print(f"✅ Signal completed: WIN +20.0 pips (45s runtime)")
    
    # Demo 5: Generate an expiring signal
    print("\n5️⃣ GENERATING EXPIRING SIGNAL...")
    expiring_signal_id = truth_tracker.log_signal_generated(
        symbol="USDJPY",
        direction="BUY",
        confidence=78.0,
        entry_price=153.25,
        stop_loss=153.05,
        take_profit=153.65,
        source="demo_venom_v8",
        tcs_score=78.0,
        citadel_score=6.8,
        ml_filter_passed=True,
        fire_reason="session_strength:72.0"
    )
    print(f"✅ Signal generated: {expiring_signal_id}")
    
    # Expire it
    truth_tracker.log_signal_expired(expiring_signal_id)
    print(f"⏰ Signal expired: No user action within timeout")
    
    # Demo 6: Show current status
    print("\n6️⃣ CURRENT STATUS...")
    status = truth_tracker.get_status()
    print(f"📊 Active signals: {status['active_signals']}")
    print(f"📁 Truth log: {status['truth_log_path']}")
    print(f"🔢 Signal counters: {status['signal_counters']}")
    
    # Stop tracking
    truth_tracker.stop_monitoring()
    print("\n🎯 Truth tracking stopped")

def demo_cli_tools():
    """Demonstrate CLI tools for truth inspection"""
    print("\n" + "=" * 60)
    print("🔍 CLI TOOLS DEMONSTRATION")
    print("=" * 60)
    
    import subprocess
    
    # Show recent signals
    print("\n📊 RECENT SIGNALS:")
    print("-" * 40)
    result = subprocess.run(['python3', 'truth_cli.py', '--recent', '10'], 
                          capture_output=True, text=True)
    print(result.stdout)
    
    # Show statistics
    print("\n📈 SIGNAL STATISTICS:")
    print("-" * 40)
    result = subprocess.run(['python3', 'truth_cli.py', '--stats'], 
                          capture_output=True, text=True)
    print(result.stdout)
    
    # Show active signals
    print("\n⚡ ACTIVE SIGNALS:")
    print("-" * 40)
    result = subprocess.run(['python3', 'truth_cli.py', '--active'], 
                          capture_output=True, text=True)
    print(result.stdout)

def main():
    """Main demo function"""
    print("🎯 COMPLETE TRUTH TRACKING SYSTEM DEMONSTRATION")
    print("This demo shows the complete signal lifecycle tracking system")
    print("that monitors ALL signals from generation through completion.")
    print()
    
    # Run demos
    demo_complete_signal_lifecycle()
    demo_cli_tools()
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE")
    print("=" * 60)
    print("🎯 The truth tracking system is now fully operational!")
    print("📊 All signals are being logged to truth_log.jsonl")
    print("🔍 Use truth_cli.py for inspection and analysis")
    print("⚡ Integrate with any signal generator using truth_tracker")
    
    print("\n🚀 Ready for production signal tracking!")

if __name__ == "__main__":
    main()