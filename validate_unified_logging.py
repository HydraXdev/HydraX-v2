#!/usr/bin/env python3
"""
Validation Script for Unified Logging System
Checks signal volume and metric completeness during London session
"""

import json
import os
from datetime import datetime, timedelta
import pytz
from collections import defaultdict, Counter

def validate_unified_logging():
    """Validate signal volume and metric completeness"""
    
    log_file = '/root/HydraX-v2/logs/comprehensive_tracking.jsonl'
    zmq_debug_file = '/root/HydraX-v2/logs/zmq_debug.log'
    predictions_file = '/root/HydraX-v2/logs/grokkeeper_predictions.jsonl'
    
    print("=" * 70)
    print("🔍 UNIFIED LOGGING VALIDATION REPORT")
    print("=" * 70)
    print(f"Time: {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    # 1. Check if files exist
    print("📁 FILE STATUS:")
    print(f"  Unified log: {'✅ EXISTS' if os.path.exists(log_file) else '❌ MISSING'}")
    print(f"  ZMQ debug: {'✅ EXISTS' if os.path.exists(zmq_debug_file) else '❌ MISSING'}")
    print(f"  ML predictions: {'✅ EXISTS' if os.path.exists(predictions_file) else '❌ MISSING'}")
    print()
    
    if not os.path.exists(log_file):
        print("❌ Unified log file not found!")
        return
    
    # 2. Load and analyze signals
    signals = []
    with open(log_file, 'r') as f:
        for line in f:
            try:
                signals.append(json.loads(line.strip()))
            except:
                continue
    
    print(f"📊 SIGNAL STATISTICS:")
    print(f"  Total signals: {len(signals)}")
    
    if not signals:
        print("  ⚠️ No signals found in log!")
        return
    
    # 3. Time-based analysis
    now = datetime.now(pytz.UTC)
    last_hour_signals = []
    last_24h_signals = []
    
    for signal in signals:
        try:
            # Parse timestamp
            ts_str = signal.get('timestamp', '')
            if ts_str:
                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                
                # Check time windows
                if now - ts < timedelta(hours=1):
                    last_hour_signals.append(signal)
                if now - ts < timedelta(hours=24):
                    last_24h_signals.append(signal)
        except:
            continue
    
    print(f"  Last hour: {len(last_hour_signals)} signals")
    print(f"  Last 24h: {len(last_24h_signals)} signals")
    
    # Calculate hourly rate
    if last_hour_signals:
        print(f"  📈 Current rate: {len(last_hour_signals)} signals/hour")
    elif last_24h_signals:
        avg_rate = len(last_24h_signals) / 24
        print(f"  📈 24h average: {avg_rate:.1f} signals/hour")
    
    # 4. Session breakdown
    print("\n🌍 SESSION DISTRIBUTION:")
    sessions = Counter(s.get('session', 'UNKNOWN') for s in signals)
    for session, count in sessions.most_common():
        pct = (count / len(signals)) * 100
        print(f"  {session}: {count} ({pct:.1f}%)")
    
    # 5. Pattern analysis
    print("\n🎯 PATTERN DISTRIBUTION:")
    patterns = Counter(s.get('pattern', 'UNKNOWN') for s in signals)
    for pattern, count in patterns.most_common():
        pct = (count / len(signals)) * 100
        print(f"  {pattern}: {count} ({pct:.1f}%)")
    
    # 6. Field completeness check
    print("\n✅ FIELD COMPLETENESS:")
    required_fields = [
        'signal_id', 'pair', 'pattern', 'confidence', 
        'entry_price', 'sl_price', 'tp_price', 
        'sl_pips', 'tp_pips', 'direction', 'session'
    ]
    
    optional_fields = [
        'rsi', 'volume_ratio', 'shield_score', 
        'executed', 'win', 'pips', 'lot_size'
    ]
    
    # Check last 5 signals for field completeness
    recent_signals = signals[-5:] if len(signals) >= 5 else signals
    
    for i, signal in enumerate(recent_signals, 1):
        print(f"\n  Signal {i}: {signal.get('signal_id', 'NO_ID')}")
        
        # Required fields
        missing_required = [f for f in required_fields if not signal.get(f)]
        if missing_required:
            print(f"    ❌ Missing required: {', '.join(missing_required)}")
        else:
            print(f"    ✅ All required fields present")
        
        # Optional fields with values
        present_optional = {f: signal.get(f) for f in optional_fields if signal.get(f) is not None}
        if present_optional:
            print(f"    📊 Metrics: {json.dumps(present_optional, indent=0).replace(chr(10), ', ')}")
    
    # 7. Win/Loss tracking
    print("\n🏆 OUTCOME TRACKING:")
    with_outcome = [s for s in signals if s.get('win') is not None]
    if with_outcome:
        wins = sum(1 for s in with_outcome if s.get('win'))
        losses = len(with_outcome) - wins
        win_rate = (wins / len(with_outcome)) * 100 if with_outcome else 0
        print(f"  Signals with outcomes: {len(with_outcome)}/{len(signals)}")
        print(f"  Wins: {wins}, Losses: {losses}")
        print(f"  Win rate: {win_rate:.1f}%")
    else:
        print(f"  ⚠️ No signals have outcome data yet")
    
    # 8. Confidence distribution
    print("\n📊 CONFIDENCE DISTRIBUTION:")
    confidence_buckets = defaultdict(int)
    for signal in signals:
        conf = signal.get('confidence', 0)
        if conf > 0:
            bucket = int(conf // 10) * 10
            confidence_buckets[bucket] += 1
    
    for bucket in sorted(confidence_buckets.keys()):
        count = confidence_buckets[bucket]
        print(f"  {bucket}-{bucket+9}%: {count} signals")
    
    # 9. Check for test vs real signals
    print("\n🔬 SIGNAL TYPES:")
    test_signals = [s for s in signals if 'TEST' in s.get('signal_id', '')]
    real_signals = [s for s in signals if 'ELITE_GUARD' in s.get('signal_id', '') and 'TEST' not in s.get('signal_id', '')]
    
    print(f"  Test signals: {len(test_signals)}")
    print(f"  Real signals: {len(real_signals)}")
    
    # 10. London session check
    print("\n🏴 LONDON SESSION CHECK:")
    london_signals = [s for s in signals if s.get('session') == 'LONDON']
    if london_signals:
        print(f"  Total London signals: {len(london_signals)}")
        
        # Check if currently London session
        current_hour = datetime.now(pytz.UTC).hour
        if 7 <= current_hour < 16:  # London: 7 AM - 4 PM UTC
            print(f"  ✅ Currently in London session")
            
            # Recent London signals
            recent_london = [s for s in last_hour_signals if s.get('session') == 'LONDON']
            print(f"  Last hour London signals: {len(recent_london)}")
            
            if len(recent_london) < 5:
                print(f"  ⚠️ Below target (5-10 signals/hour)")
            elif len(recent_london) > 10:
                print(f"  ⚠️ Above target (5-10 signals/hour)")
            else:
                print(f"  ✅ On target (5-10 signals/hour)")
    
    # 11. ZMQ Debug check
    if os.path.exists(zmq_debug_file):
        print("\n📡 ZMQ DEBUG LOG:")
        try:
            with open(zmq_debug_file, 'r') as f:
                zmq_entries = [json.loads(line) for line in f.readlines()[-10:]]
                print(f"  Recent entries: {len(zmq_entries)}")
                
                actions = Counter(e.get('action') for e in zmq_entries)
                for action, count in actions.items():
                    print(f"    {action}: {count}")
        except:
            print("  ⚠️ Could not parse ZMQ debug log")
    
    # 12. ML Predictions check
    if os.path.exists(predictions_file):
        print("\n🤖 ML PREDICTIONS:")
        try:
            with open(predictions_file, 'r') as f:
                predictions = [json.loads(line) for line in f]
                print(f"  Total predictions: {len(predictions)}")
                
                if predictions:
                    recent_pred = predictions[-5:]
                    avg_win_prob = sum(p.get('win_probability', 0) for p in recent_pred) / len(recent_pred)
                    print(f"  Recent avg win probability: {avg_win_prob:.1%}")
        except:
            print("  ⚠️ Could not parse predictions file")
    
    print("\n" + "=" * 70)
    print("📋 RECOMMENDATIONS:")
    
    # Generate recommendations
    if len(signals) < 10:
        print("  • Need more signals for meaningful analysis")
    
    if not real_signals:
        print("  • No real Elite Guard signals detected - check if Elite Guard is running")
    
    if not os.path.exists(zmq_debug_file):
        print("  • ZMQ debug logging not active - signals may not be publishing")
    
    if last_hour_signals and len(last_hour_signals) < 5:
        print("  • Signal rate below target - check CITADEL threshold settings")
    
    if not with_outcome:
        print("  • No outcome data available - outcome tracking may not be working")
    
    missing_metrics = []
    for signal in recent_signals:
        if not signal.get('rsi'):
            missing_metrics.append('RSI')
            break
    for signal in recent_signals:
        if not signal.get('volume_ratio'):
            missing_metrics.append('volume_ratio')
            break
    for signal in recent_signals:
        if not signal.get('shield_score'):
            missing_metrics.append('shield_score')
            break
    
    if missing_metrics:
        print(f"  • Missing metrics in recent signals: {', '.join(set(missing_metrics))}")
    
    if len(signals) > 0 and len(real_signals) > 0:
        print("  ✅ System appears to be functioning correctly")
    
    print("=" * 70)

if __name__ == "__main__":
    validate_unified_logging()