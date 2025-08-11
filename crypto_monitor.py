#!/usr/bin/env python3
"""
Crypto Engine KPI Monitor - Track 7-day rolling metrics for tuning
Reads from ultimate_core_crypto.jsonl and prints key performance indicators
"""

import json
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List
import statistics

def load_signals(file_path: str, days: int = 7) -> List[dict]:
    """Load signals from JSON log within the last N days"""
    cutoff = time.time() - (days * 24 * 3600)
    signals = []
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    signal = json.loads(line.strip())
                    if signal.get('ts', 0) >= cutoff and signal.get('accepted'):
                        signals.append(signal)
                except:
                    continue
    except FileNotFoundError:
        print(f"Log file not found: {file_path}")
        return []
    
    return signals

def analyze_signals(signals: List[dict]) -> Dict:
    """Analyze signals and compute KPIs"""
    if not signals:
        return {}
    
    total_signals = len(signals)
    by_session = defaultdict(int)
    by_symbol = defaultdict(int)
    scores = []
    evs = []
    p_wins = []
    confirmations = defaultdict(int)
    spreads = []
    slippages = []
    
    for sig in signals:
        # Count by session
        session = sig.get('session', 'UNKNOWN')
        if session in ['ASIA', 'EU', 'US', 'GRAVEYARD']:
            by_session[session] += 1
        
        # Count by symbol
        symbol = sig.get('symbol', 'UNKNOWN')[:3]  # BTC, ETH, etc.
        by_symbol[symbol] += 1
        
        # Collect metrics
        if 'final_score' in sig:
            scores.append(sig['final_score'])
        if 'ev' in sig:
            evs.append(sig['ev'])
        if 'p_win' in sig:
            p_wins.append(sig['p_win'])
        
        # Count confirmations
        if sig.get('has_volume'):
            confirmations['volume'] += 1
        if sig.get('has_imb'):
            confirmations['imbalance'] += 1
        if sig.get('has_liq'):
            confirmations['liquidation'] += 1
        
        # Collect execution metrics
        if 'spread_bps' in sig:
            spreads.append(sig['spread_bps'])
        if 'slippage_bps' in sig:
            slippages.append(sig['slippage_bps'])
    
    return {
        'total_signals': total_signals,
        'signals_per_day': total_signals / 7.0,
        'by_session': dict(by_session),
        'by_symbol': dict(by_symbol),
        'scores': scores,
        'evs': evs,
        'p_wins': p_wins,
        'confirmations': dict(confirmations),
        'spreads': spreads,
        'slippages': slippages
    }

def print_kpis(analysis: Dict):
    """Print formatted KPI report"""
    if not analysis:
        print("❌ No signals found in the last 7 days")
        return
    
    print("🚀 CRYPTO ENGINE KPI REPORT (7-day rolling)")
    print("=" * 50)
    
    # Signal count and pacing
    print(f"📊 SIGNAL COUNT & PACING")
    print(f"   Total Signals: {analysis['total_signals']}")
    print(f"   Signals/Day: {analysis['signals_per_day']:.1f}")
    print(f"   Target: 10/day {'✅' if 8 <= analysis['signals_per_day'] <= 12 else '⚠️'}")
    print()
    
    # Session distribution
    print(f"🌍 SESSION DISTRIBUTION")
    sessions = analysis['by_session']
    for sess in ['ASIA', 'EU', 'US', 'GRAVEYARD']:
        count = sessions.get(sess, 0)
        pct = (count / analysis['total_signals'] * 100) if analysis['total_signals'] > 0 else 0
        print(f"   {sess}: {count} ({pct:.1f}%)")
    print()
    
    # Symbol breakdown
    print(f"💎 SYMBOL BREAKDOWN")
    symbols = analysis['by_symbol']
    for sym in ['BTC', 'ETH', 'XRP']:
        count = symbols.get(sym, 0)
        pct = (count / analysis['total_signals'] * 100) if analysis['total_signals'] > 0 else 0
        print(f"   {sym}: {count} ({pct:.1f}%)")
    print()
    
    # Quality metrics
    if analysis['scores']:
        scores = analysis['scores']
        print(f"📈 QUALITY METRICS")
        print(f"   Median Score: {statistics.median(scores):.1f}")
        print(f"   Score Range: {min(scores):.0f} - {max(scores):.0f}")
        target_score = statistics.median(scores) >= 82
        print(f"   Target: ≥82 {'✅' if target_score else '⚠️'}")
        print()
    
    # Expected value
    if analysis['evs']:
        evs = analysis['evs']
        print(f"💰 EXPECTED VALUE")
        print(f"   Median EV: {statistics.median(evs):.3f}")
        print(f"   EV Range: {min(evs):.3f} - {max(evs):.3f}")
        target_ev = statistics.median(evs) >= 0.22
        print(f"   Target: ≥0.22 {'✅' if target_ev else '⚠️'}")
        print()
    
    # Win probability
    if analysis['p_wins']:
        p_wins = analysis['p_wins']
        print(f"🎯 WIN PROBABILITY")
        print(f"   Median P(Win): {statistics.median(p_wins):.3f}")
        print(f"   P(Win) Range: {min(p_wins):.3f} - {max(p_wins):.3f}")
        print()
    
    # Confirmations
    confs = analysis['confirmations']
    total = analysis['total_signals']
    if total > 0:
        print(f"✅ CONFIRMATIONS")
        vol_pct = (confs.get('volume', 0) / total * 100)
        imb_pct = (confs.get('imbalance', 0) / total * 100) 
        liq_pct = (confs.get('liquidation', 0) / total * 100)
        print(f"   Volume Surge: {vol_pct:.1f}%")
        print(f"   Order Book Imbalance: {imb_pct:.1f}%")
        print(f"   Liquidation Cluster: {liq_pct:.1f}%")
        print()
    
    # Execution quality
    if analysis['spreads']:
        spreads = analysis['spreads']
        print(f"⚡ EXECUTION QUALITY")
        print(f"   Median Spread: {statistics.median(spreads):.1f} bps")
        print(f"   Spread Range: {min(spreads):.1f} - {max(spreads):.1f} bps")
        
        if analysis['slippages']:
            slippages = analysis['slippages']
            print(f"   Median Slippage: {statistics.median(slippages):.1f} bps")
            print(f"   Slippage Range: {min(slippages):.1f} - {max(slippages):.1f} bps")
        print()
    
    # Tuning recommendations
    signals_per_day = analysis['signals_per_day']
    print(f"🔧 TUNING RECOMMENDATIONS")
    if signals_per_day > 12:
        print("   📈 Over target: Raise L to 79 or reduce EU bucket 0.6→0.5")
    elif signals_per_day < 8:
        print("   📉 Under target: Lower H to 89 or increase US bucket 0.9→1.1")
    else:
        print("   ✅ Signal count in target range")
    
    if analysis['scores'] and statistics.median(analysis['scores']) < 82:
        print("   🎯 Low scores: Tighten confirmation gates or spread limits")
    
    if analysis['evs'] and statistics.median(analysis['evs']) < 0.22:
        print("   💰 Low EV: Consider raising EV override threshold")
    
    print()

def main():
    """Main monitoring function"""
    log_file = "/root/HydraX-v2/ultimate_core_crypto.jsonl"
    
    print("🔍 Loading signals from last 7 days...")
    signals = load_signals(log_file, days=7)
    
    analysis = analyze_signals(signals)
    print_kpis(analysis)
    
    # Real-time monitoring option
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        print("👁️  Monitoring mode: Press Ctrl+C to exit")
        try:
            while True:
                time.sleep(60)  # Update every minute
                print("\n" + "="*50)
                signals = load_signals(log_file, days=7)
                analysis = analyze_signals(signals)
                print_kpis(analysis)
        except KeyboardInterrupt:
            print("\n✋ Monitoring stopped")

if __name__ == "__main__":
    main()