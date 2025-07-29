#!/usr/bin/env python3
"""
🔍 BITTEN Engine Diagnostic Tool
Real-time CLI diagnostic to confirm VENOM is generating, filtering, and logging signals.

Usage:
    python3 engine_diagnostic_check.py
    python3 engine_diagnostic_check.py --verbose
    python3 engine_diagnostic_check.py --watch
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import glob

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    """Print diagnostic tool header"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}🔍 BITTEN ENGINE DIAGNOSTIC TOOL{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

def check_venom_process() -> Tuple[bool, str]:
    """Check if VENOM engine is running"""
    try:
        # Check for venom_scalp_master.py process
        result = subprocess.run(
            ['pgrep', '-f', 'venom_scalp_master.py'], 
            capture_output=True, text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pid = result.stdout.strip().split('\n')[0]
            return True, f"PID {pid}"
        
        # Also check for other VENOM engines
        venom_engines = [
            'apex_venom_v7_unfiltered.py',
            'apex_venom_v7_complete.py',
            'working_signal_generator.py',
            'bitten_tier_engine.py'
        ]
        
        for engine in venom_engines:
            result = subprocess.run(
                ['pgrep', '-f', engine], 
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                pid = result.stdout.strip().split('\n')[0]
                return True, f"{engine} - PID {pid}"
        
        return False, "No VENOM processes found"
        
    except Exception as e:
        return False, f"Error checking processes: {e}"

def get_recent_signals(minutes: int = 30) -> List[Dict]:
    """Get signals from the last N minutes"""
    signals = []
    signals_dir = Path("/root/HydraX-v2/signals")
    
    if not signals_dir.exists():
        return signals
    
    cutoff_time = datetime.now() - timedelta(minutes=minutes)
    
    # Check for signal files
    signal_files = glob.glob(str(signals_dir / "*.json"))
    
    for file_path in signal_files:
        try:
            # Check file modification time
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_time < cutoff_time:
                continue
                
            with open(file_path, 'r') as f:
                signal_data = json.load(f)
                signal_data['file_path'] = file_path
                signal_data['file_time'] = file_time
                signals.append(signal_data)
                
        except Exception as e:
            continue
    
    # Also check missions directory
    missions_dir = Path("/root/HydraX-v2/missions")
    if missions_dir.exists():
        mission_files = glob.glob(str(missions_dir / "*.json"))
        
        for file_path in mission_files:
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_time:
                    continue
                    
                with open(file_path, 'r') as f:
                    signal_data = json.load(f)
                    signal_data['file_path'] = file_path
                    signal_data['file_time'] = file_time
                    signal_data['source'] = 'mission'
                    signals.append(signal_data)
                    
            except Exception as e:
                continue
    
    # Sort by file time, newest first
    signals.sort(key=lambda x: x.get('file_time', datetime.min), reverse=True)
    
    return signals

def check_ml_filter_activity(minutes: int = 30) -> Tuple[bool, int, str]:
    """Check ML filter activity from suppressed signals log"""
    suppressed_log = Path("/root/HydraX-v2/logs/suppressed_signals.log")
    
    if not suppressed_log.exists():
        return False, 0, "suppressed_signals.log not found"
    
    try:
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_blocks = 0
        
        with open(suppressed_log, 'r') as f:
            for line in f:
                try:
                    # Parse log line for timestamp
                    if '[' in line and ']' in line:
                        timestamp_str = line.split('[')[1].split(']')[0]
                        log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        
                        if log_time >= cutoff_time:
                            recent_blocks += 1
                except:
                    continue
        
        return True, recent_blocks, f"{recent_blocks} signals blocked"
        
    except Exception as e:
        return False, 0, f"Error reading log: {e}"

def check_truth_tracker(minutes: int = 30) -> Tuple[bool, List[Dict], str]:
    """Check truth tracker activity from truth_log.jsonl"""
    truth_log = Path("/root/HydraX-v2/truth_log.jsonl")
    
    if not truth_log.exists():
        return False, [], "truth_log.jsonl not found"
    
    try:
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_entries = []
        
        with open(truth_log, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    
                    # Parse timestamp
                    if 'timestamp' in entry:
                        entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                        entry_time = entry_time.replace(tzinfo=None)  # Remove timezone for comparison
                        
                        if entry_time >= cutoff_time:
                            recent_entries.append(entry)
                            
                except Exception as e:
                    continue
        
        # Sort by timestamp, newest first
        recent_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return True, recent_entries, f"{len(recent_entries)} recent entries"
        
    except Exception as e:
        return False, [], f"Error reading truth log: {e}"

def print_signal_summary(signal: Dict, verbose: bool = False):
    """Print a summary of a signal"""
    signal_id = signal.get('signal_id', 'Unknown')
    timestamp = signal.get('file_time', datetime.now()).strftime('%H:%M:%S')
    signal_type = signal.get('signal_type', signal.get('type', 'Unknown'))
    risk_reward = signal.get('risk_reward', signal.get('risk_reward_ratio', 'Unknown'))
    source = signal.get('source', 'signal')
    
    # Try to get ML filter result
    ml_result = "Unknown"
    if 'ml_prediction' in signal:
        ml_result = f"Prediction: {signal['ml_prediction']}"
    elif 'filtered' in signal:
        ml_result = "Blocked" if signal['filtered'] else "Passed"
    elif 'shield_score' in signal:
        ml_result = f"Shield: {signal['shield_score']}/10"
    
    print(f"  📍 {Colors.BOLD}{signal_id}{Colors.END}")
    print(f"     ⏰ {timestamp} | 🎯 {signal_type} | 📊 R:R {risk_reward} | 🤖 {ml_result}")
    
    if verbose:
        print(f"     📁 Source: {source} | File: {Path(signal['file_path']).name}")
        if 'symbol' in signal:
            print(f"     💱 {signal['symbol']} | Direction: {signal.get('direction', 'N/A')}")

def print_truth_summary(entry: Dict, verbose: bool = False):
    """Print a summary of a truth log entry"""
    signal_id = entry.get('signal_id', 'Unknown')
    result = entry.get('result', entry.get('outcome', 'Unknown'))
    runtime = entry.get('runtime_minutes', entry.get('duration', 'Unknown'))
    signal_type = entry.get('signal_type', 'Unknown')
    
    result_color = Colors.GREEN if result == 'WIN' else Colors.RED if result == 'LOSS' else Colors.YELLOW
    
    print(f"  📍 {Colors.BOLD}{signal_id}{Colors.END}")
    print(f"     {result_color}🎯 {result}{Colors.END} | ⏱️ {runtime}min | 🔫 {signal_type}")
    
    if verbose and 'pips' in entry:
        print(f"     💰 Pips: {entry['pips']} | Confidence: {entry.get('confidence', 'N/A')}%")

def run_diagnostic(verbose: bool = False):
    """Run complete diagnostic check"""
    print_header()
    
    # 1. Check VENOM process
    print(f"{Colors.BOLD}1. 🐍 VENOM ENGINE STATUS{Colors.END}")
    venom_running, venom_info = check_venom_process()
    
    if venom_running:
        print(f"   {Colors.GREEN}✅ VENOM: Running ({venom_info}){Colors.END}")
    else:
        print(f"   {Colors.RED}❌ VENOM: Not running ({venom_info}){Colors.END}")
    
    # 2. Check recent signals
    print(f"\n{Colors.BOLD}2. 📡 SIGNAL ACTIVITY (Last 30 minutes){Colors.END}")
    signals = get_recent_signals(30)
    
    if signals:
        print(f"   {Colors.GREEN}✅ Signals Found: {len(signals)}{Colors.END}")
        for i, signal in enumerate(signals[:5]):  # Show max 5 recent signals
            print_signal_summary(signal, verbose)
        if len(signals) > 5:
            print(f"   ... and {len(signals) - 5} more signals")
    else:
        print(f"   {Colors.YELLOW}⚠️ No signal activity detected in past 30m{Colors.END}")
    
    # 3. Check ML Filter activity
    print(f"\n{Colors.BOLD}3. 🤖 ML FILTER STATUS{Colors.END}")
    filter_active, blocks_count, filter_info = check_ml_filter_activity(30)
    
    if filter_active and blocks_count > 0:
        print(f"   {Colors.GREEN}✅ ML Filter: Active ({filter_info}){Colors.END}")
    elif filter_active:
        print(f"   {Colors.YELLOW}⚠️ ML Filter: No blocked signals in last 30m{Colors.END}")
    else:
        print(f"   {Colors.RED}❌ ML Filter: {filter_info}{Colors.END}")
    
    # 4. Check Truth Tracker
    print(f"\n{Colors.BOLD}4. 📊 TRUTH TRACKER STATUS{Colors.END}")
    truth_active, truth_entries, truth_info = check_truth_tracker(30)
    
    if truth_active and truth_entries:
        print(f"   {Colors.GREEN}✅ Truth Tracker: Logging active ({truth_info}){Colors.END}")
        for entry in truth_entries[:3]:  # Show max 3 recent entries
            print_truth_summary(entry, verbose)
        if len(truth_entries) > 3:
            print(f"   ... and {len(truth_entries) - 3} more entries")
    elif truth_active:
        print(f"   {Colors.YELLOW}⚠️ Truth Tracker: No entries found in last 30m{Colors.END}")
    else:
        print(f"   {Colors.RED}❌ Truth Tracker: {truth_info}{Colors.END}")
    
    # 5. Summary Status
    print(f"\n{Colors.BOLD}📋 SYSTEM SUMMARY{Colors.END}")
    print(f"{Colors.CYAN}{'─' * 40}{Colors.END}")
    
    status_items = [
        ("VENOM Engine", venom_running),
        ("Signal Generation", len(signals) > 0),
        ("ML Filter", filter_active),
        ("Truth Logging", truth_active and len(truth_entries) > 0)
    ]
    
    all_good = True
    for item_name, status in status_items:
        if status:
            print(f"   {Colors.GREEN}✅ {item_name}: Operational{Colors.END}")
        else:
            print(f"   {Colors.RED}❌ {item_name}: Issues detected{Colors.END}")
            all_good = False
    
    if all_good:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎯 BITTEN ENGINE: FULLY OPERATIONAL{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ BITTEN ENGINE: PARTIAL OPERATION{Colors.END}")
    
    print(f"{Colors.CYAN}{'─' * 40}{Colors.END}\n")

def main():
    parser = argparse.ArgumentParser(description='BITTEN Engine Diagnostic Tool')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Print detailed signal information')
    parser.add_argument('--watch', '-w', action='store_true',
                       help='Watch mode - refresh every 60 seconds')
    
    args = parser.parse_args()
    
    if args.watch:
        try:
            while True:
                # Clear screen
                os.system('clear' if os.name == 'posix' else 'cls')
                run_diagnostic(args.verbose)
                print(f"{Colors.BLUE}Refreshing in 60 seconds... (Ctrl+C to exit){Colors.END}")
                time.sleep(60)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Diagnostic monitoring stopped.{Colors.END}")
            sys.exit(0)
    else:
        run_diagnostic(args.verbose)

if __name__ == "__main__":
    main()