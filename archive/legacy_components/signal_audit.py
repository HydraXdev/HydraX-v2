#!/usr/bin/env python3
"""
SIGNAL AUDIT TOOL - Security Monitoring CLI

This tool provides administrators with comprehensive monitoring capabilities
to detect rogue signal attempts and verify truth system integrity.

Usage:
    python3 signal_audit.py --rogue-check      # Check for unauthorized signal attempts
    python3 signal_audit.py --system-health    # Verify truth system health
    python3 signal_audit.py --purge-scan       # Scan for signals bypassing purge
    python3 signal_audit.py --full-audit       # Run complete security audit
"""

import argparse
import json
import os
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/signal_audit.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SignalAuditor:
    """Security monitoring tool for the BITTEN signal system"""
    
    def __init__(self):
        self.missions_dir = Path("/root/HydraX-v2/missions")
        self.archive_dir = Path("/root/HydraX-v2/archive/rogue_signals")
        self.truth_log = Path("/root/HydraX-v2/truth_log.jsonl")
        self.rogue_engines = [
            "/root/HydraX-v2/apex_production_v6.py",
            "/root/HydraX-v2/working_signal_generator.py.FAKE_DISABLED", 
            "/root/HydraX-v2/apex_venom_v7_unfiltered.py.FAKE_DISABLED"
        ]
        self.authorized_sources = ['venom_scalp_master']
        
        logger.info("🛡️ Signal Auditor initialized")
        logger.info(f"📁 Monitoring: {self.missions_dir}")
        logger.info(f"🗂️ Archive: {self.archive_dir}")
        
    def check_rogue_signals(self) -> Dict[str, int]:
        """
        Check for signals that bypass source validation
        Returns counts of various signal types
        """
        logger.info("🔍 ROGUE CHECK: Scanning for unauthorized signal attempts...")
        
        results = {
            'total_signals': 0,
            'authorized_signals': 0,
            'rogue_signals': 0,
            'missing_source': 0,
            'invalid_source': 0,
            'corrupted_files': 0
        }
        
        rogue_signals = []
        
        if not self.missions_dir.exists():
            logger.warning("⚠️ Missions directory does not exist")
            return results
            
        # Scan current mission files
        for signal_file in self.missions_dir.glob("*.json"):
            results['total_signals'] += 1
            
            try:
                with open(signal_file, 'r') as f:
                    data = json.load(f)
                
                source = data.get('source', '')
                signal_id = data.get('signal_id', signal_file.name)
                
                if not source:
                    results['missing_source'] += 1
                    results['rogue_signals'] += 1
                    rogue_signals.append({
                        'file': signal_file.name,
                        'signal_id': signal_id,
                        'issue': 'MISSING_SOURCE',
                        'source': 'NONE'
                    })
                    logger.warning(f"🚨 ROGUE: {signal_file.name} - Missing source field")
                    
                elif source not in self.authorized_sources:
                    results['invalid_source'] += 1
                    results['rogue_signals'] += 1
                    rogue_signals.append({
                        'file': signal_file.name,
                        'signal_id': signal_id,
                        'issue': 'INVALID_SOURCE',
                        'source': source
                    })
                    logger.warning(f"🚨 ROGUE: {signal_file.name} - Invalid source: {source}")
                    
                else:
                    results['authorized_signals'] += 1
                    logger.debug(f"✅ AUTHORIZED: {signal_file.name} - Source: {source}")
                    
            except json.JSONDecodeError:
                results['corrupted_files'] += 1
                results['rogue_signals'] += 1
                logger.error(f"💥 CORRUPTED: {signal_file.name} - Invalid JSON")
                rogue_signals.append({
                    'file': signal_file.name,
                    'signal_id': 'UNKNOWN',
                    'issue': 'CORRUPTED_JSON',
                    'source': 'UNKNOWN'
                })
            except Exception as e:
                logger.error(f"❌ ERROR scanning {signal_file.name}: {e}")
        
        # Generate report
        print("\n" + "="*80)
        print("🛡️ ROGUE SIGNAL DETECTION REPORT")
        print("="*80)
        print(f"📊 Total signals scanned: {results['total_signals']}")
        print(f"✅ Authorized signals: {results['authorized_signals']}")
        print(f"🚨 Rogue signals found: {results['rogue_signals']}")
        print(f"   • Missing source: {results['missing_source']}")
        print(f"   • Invalid source: {results['invalid_source']}")
        print(f"   • Corrupted files: {results['corrupted_files']}")
        
        if rogue_signals:
            print(f"\n🚨 SECURITY ALERT: {len(rogue_signals)} rogue signals detected!")
            print("\nROGUE SIGNAL DETAILS:")
            for rogue in rogue_signals:
                print(f"  • {rogue['file']} - {rogue['issue']} (source: {rogue['source']})")
                
            print(f"\n💡 RECOMMENDATION: Run quarantine with:")
            print(f"   python3 /tmp/quarantine_no_source.py")
        else:
            print(f"\n✅ SECURITY STATUS: All signals properly authorized")
            
        print("="*80)
        
        return results
    
    def check_system_health(self) -> Dict[str, any]:
        """
        Verify truth system health and configuration
        """
        logger.info("🏥 HEALTH CHECK: Verifying truth system integrity...")
        
        health = {
            'truth_tracker_exists': False,
            'truth_log_exists': False, 
            'truth_log_entries': 0,
            'archive_exists': False,
            'archived_signals': 0,
            'rogue_engines_disabled': 0,
            'total_rogue_engines': len(self.rogue_engines),
            'source_validation_active': False
        }
        
        # Check truth tracker existence
        truth_tracker_path = Path("/root/HydraX-v2/truth_tracker.py")
        health['truth_tracker_exists'] = truth_tracker_path.exists()
        
        # Check truth log
        health['truth_log_exists'] = self.truth_log.exists()
        if health['truth_log_exists']:
            try:
                with open(self.truth_log, 'r') as f:
                    health['truth_log_entries'] = len(f.readlines())
            except Exception as e:
                logger.error(f"Error reading truth log: {e}")
        
        # Check archive directory
        health['archive_exists'] = self.archive_dir.exists()
        if health['archive_exists']:
            try:
                health['archived_signals'] = len(list(self.archive_dir.glob("*.json")))
            except Exception as e:
                logger.error(f"Error scanning archive: {e}")
        
        # Check rogue engines disabled
        for engine in self.rogue_engines:
            engine_path = Path(engine)
            if engine_path.exists():
                # Check if file is disabled (no execute permissions)
                stat = engine_path.stat()
                if stat.st_mode & 0o111 == 0:  # No execute permissions
                    health['rogue_engines_disabled'] += 1
                    
        # Check if truth tracker has source validation
        if health['truth_tracker_exists']:
            try:
                with open(truth_tracker_path, 'r') as f:
                    content = f.read()
                    if "venom_scalp_master" in content and "source" in content:
                        health['source_validation_active'] = True
            except Exception as e:
                logger.error(f"Error checking truth tracker validation: {e}")
        
        # Generate health report
        print("\n" + "="*80)
        print("🏥 TRUTH SYSTEM HEALTH REPORT")
        print("="*80)
        
        status_icon = "✅" if health['truth_tracker_exists'] else "❌"
        print(f"{status_icon} Truth Tracker: {'Active' if health['truth_tracker_exists'] else 'Missing'}")
        
        status_icon = "✅" if health['source_validation_active'] else "❌"
        print(f"{status_icon} Source Validation: {'Active' if health['source_validation_active'] else 'Inactive'}")
        
        status_icon = "✅" if health['truth_log_exists'] else "❌"
        print(f"{status_icon} Truth Log: {'Active' if health['truth_log_exists'] else 'Missing'} ({health['truth_log_entries']} entries)")
        
        status_icon = "✅" if health['archive_exists'] else "❌"
        print(f"{status_icon} Rogue Archive: {'Active' if health['archive_exists'] else 'Missing'} ({health['archived_signals']} archived)")
        
        engines_status = f"{health['rogue_engines_disabled']}/{health['total_rogue_engines']}"
        status_icon = "✅" if health['rogue_engines_disabled'] == health['total_rogue_engines'] else "⚠️"
        print(f"{status_icon} Rogue Engines Disabled: {engines_status}")
        
        # Overall health assessment
        critical_systems = [
            health['truth_tracker_exists'],
            health['source_validation_active'],
            health['rogue_engines_disabled'] == health['total_rogue_engines']
        ]
        
        if all(critical_systems):
            print(f"\n✅ OVERALL HEALTH: SECURE - All security measures active")
        else:
            print(f"\n🚨 OVERALL HEALTH: COMPROMISED - Security measures need attention")
            if not health['truth_tracker_exists']:
                print("   • Truth tracker missing - system vulnerable")
            if not health['source_validation_active']:
                print("   • Source validation inactive - rogue signals possible")
            if health['rogue_engines_disabled'] != health['total_rogue_engines']:
                print("   • Rogue engines still active - unauthorized signal generation possible")
                
        print("="*80)
        
        return health
    
    def purge_scan(self) -> Dict[str, int]:
        """
        Scan for signals that might have bypassed the purge process
        """
        logger.info("🧹 PURGE SCAN: Looking for signals that bypassed quarantine...")
        
        results = {
            'bypassed_signals': 0,
            'suspicious_patterns': 0,
            'recent_violations': 0
        }
        
        bypassed = []
        current_time = datetime.now()
        
        # Look for recently created signals without proper source
        if self.missions_dir.exists():
            for signal_file in self.missions_dir.glob("*.json"):
                try:
                    # Check file modification time (signals created after purge)
                    file_stat = signal_file.stat()
                    file_time = datetime.fromtimestamp(file_stat.st_mtime)
                    hours_old = (current_time - file_time).total_seconds() / 3600
                    
                    with open(signal_file, 'r') as f:
                        data = json.load(f)
                    
                    source = data.get('source', '')
                    signal_id = data.get('signal_id', signal_file.name)
                    
                    # Flag signals without proper source
                    if source != 'venom_scalp_master':
                        results['bypassed_signals'] += 1
                        bypassed.append({
                            'file': signal_file.name,
                            'signal_id': signal_id,
                            'source': source if source else 'MISSING',
                            'hours_old': round(hours_old, 1)
                        })
                        
                        if hours_old < 24:  # Recently created
                            results['recent_violations'] += 1
                    
                    # Check for suspicious patterns in signal IDs
                    if any(pattern in signal_id for pattern in ['APEX5', 'UNFILTERED', 'NUMBERED']):
                        results['suspicious_patterns'] += 1
                        
                except Exception as e:
                    logger.error(f"Error scanning {signal_file.name}: {e}")
        
        # Generate purge scan report
        print("\n" + "="*80)
        print("🧹 PURGE BYPASS DETECTION REPORT")
        print("="*80)
        print(f"🔍 Signals bypassing purge: {results['bypassed_signals']}")
        print(f"⚠️ Suspicious patterns: {results['suspicious_patterns']}")
        print(f"🚨 Recent violations (24h): {results['recent_violations']}")
        
        if bypassed:
            print(f"\nBYPASSED SIGNALS:")
            for signal in bypassed:
                age_indicator = "🔥" if signal['hours_old'] < 1 else "⚠️" if signal['hours_old'] < 24 else "📅"
                print(f"  {age_indicator} {signal['file']} - Source: {signal['source']} (Age: {signal['hours_old']}h)")
                
            print(f"\n💡 RECOMMENDATION: Quarantine bypassed signals immediately")
        else:
            print(f"\n✅ PURGE STATUS: No signals bypassing quarantine detected")
            
        print("="*80)
        
        return results
    
    def full_audit(self) -> Dict[str, any]:
        """
        Run complete security audit combining all checks
        """
        logger.info("🔒 FULL AUDIT: Running comprehensive security analysis...")
        
        print("\n" + "="*80)
        print("🔒 BITTEN SIGNAL SYSTEM - FULL SECURITY AUDIT")
        print("="*80)
        print(f"🕐 Audit Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"👤 Auditor: Signal Security Monitor")
        print("="*80)
        
        # Run all checks
        rogue_results = self.check_rogue_signals()
        health_results = self.check_system_health()
        purge_results = self.purge_scan()
        
        # Compile overall security score
        security_score = 0
        max_score = 10
        
        # Scoring criteria
        if health_results['source_validation_active']: security_score += 3
        if health_results['rogue_engines_disabled'] == health_results['total_rogue_engines']: security_score += 2
        if rogue_results['rogue_signals'] == 0: security_score += 2
        if purge_results['recent_violations'] == 0: security_score += 2
        if health_results['truth_log_exists']: security_score += 1
        
        # Final assessment
        print("\n" + "="*80)
        print("🏆 FINAL SECURITY ASSESSMENT")
        print("="*80)
        print(f"🔢 Security Score: {security_score}/{max_score}")
        
        if security_score >= 9:
            status = "🟢 SECURE"
            recommendation = "System is properly hardened against rogue signals"
        elif security_score >= 7:
            status = "🟡 MODERATE"
            recommendation = "Some security measures need attention"
        elif security_score >= 5:
            status = "🟠 COMPROMISED"
            recommendation = "Critical security issues require immediate action"
        else:
            status = "🔴 VULNERABLE"
            recommendation = "System is highly vulnerable to rogue signal attacks"
            
        print(f"🛡️ Security Status: {status}")
        print(f"💡 Recommendation: {recommendation}")
        
        # Action items
        action_items = []
        if not health_results['source_validation_active']:
            action_items.append("Enable source validation in truth tracker")
        if health_results['rogue_engines_disabled'] != health_results['total_rogue_engines']:
            action_items.append("Disable remaining rogue engines")
        if rogue_results['rogue_signals'] > 0:
            action_items.append("Quarantine unauthorized signals")
        if purge_results['recent_violations'] > 0:
            action_items.append("Investigate recent security violations")
            
        if action_items:
            print(f"\n📋 REQUIRED ACTIONS:")
            for i, action in enumerate(action_items, 1):
                print(f"   {i}. {action}")
        else:
            print(f"\n✅ NO ACTIONS REQUIRED: All security measures are active")
            
        print("="*80)
        
        return {
            'security_score': security_score,
            'max_score': max_score,
            'status': status,
            'rogue_check': rogue_results,
            'health_check': health_results,
            'purge_scan': purge_results,
            'action_items': action_items
        }
    
    def dual_track_scan(self):
        """Detect untracked legacy-format signals (5_*_USER*.json)"""
        print("🔍 DUAL TRACK SCAN - LEGACY SIGNAL DETECTION")
        print("="*60)
        
        # Load truth log entries
        truth_log_path = Path("/root/HydraX-v2/truth_log.jsonl")
        truth_signals = set()
        
        if truth_log_path.exists():
            try:
                with open(truth_log_path, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            signal_id = entry.get('signal_id', '')
                            if signal_id:
                                truth_signals.add(signal_id)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"⚠️ Error reading truth log: {e}")
        
        print(f"📊 Truth log contains {len(truth_signals)} tracked signals")
        
        # Scan mission files
        main_missions = []
        user_missions = []
        untracked_main = []
        untracked_user = []
        no_source_count = 0
        
        # Scan main mission files
        for mission_file in self.missions_dir.glob("mission_*.json"):
            try:
                with open(mission_file, 'r') as f:
                    data = json.load(f)
                
                signal_id = data.get('signal_id', 'unknown')
                source = data.get('source', '')
                main_missions.append(signal_id)
                
                if not source:
                    no_source_count += 1
                
                if signal_id not in truth_signals:
                    untracked_main.append({
                        'file': mission_file.name,
                        'signal_id': signal_id,
                        'source': source,
                        'has_source': bool(source)
                    })
                    
            except Exception as e:
                print(f"❌ Error reading {mission_file}: {e}")
        
        # Scan user mission files  
        for mission_file in self.missions_dir.glob("5_*_USER*.json"):
            try:
                with open(mission_file, 'r') as f:
                    data = json.load(f)
                
                mission_id = data.get('mission_id', 'unknown')
                base_signal_id = data.get('base_signal_id', 'unknown')
                source = data.get('source', '')
                user_missions.append(mission_id)
                
                if not source:
                    no_source_count += 1
                
                if mission_id not in truth_signals and base_signal_id not in truth_signals:
                    untracked_user.append({
                        'file': mission_file.name,
                        'mission_id': mission_id,
                        'base_signal_id': base_signal_id,
                        'source': source,
                        'has_source': bool(source)
                    })
                    
            except Exception as e:
                print(f"❌ Error reading {mission_file}: {e}")
        
        # Report results
        print(f"\n📁 MISSION FILE INVENTORY:")
        print(f"  Main missions (mission_*.json): {len(main_missions)}")
        print(f"  User missions (5_*_USER*.json): {len(user_missions)}")
        print(f"  Total mission files: {len(main_missions) + len(user_missions)}")
        
        print(f"\n🔍 TRACKING STATUS:")
        print(f"  Truth log entries: {len(truth_signals)}")
        print(f"  Untracked main missions: {len(untracked_main)}")
        print(f"  Untracked user missions: {len(untracked_user)}")
        print(f"  Files missing source tag: {no_source_count}")
        
        # Show untracked signals
        if untracked_main:
            print(f"\n❌ UNTRACKED MAIN MISSIONS ({len(untracked_main)}):")
            for signal in untracked_main[:10]:  # Show first 10
                source_status = "✅" if signal['has_source'] else "❌"
                print(f"  {source_status} {signal['signal_id']} - Source: {signal['source'] or 'MISSING'}")
            if len(untracked_main) > 10:
                print(f"  ... and {len(untracked_main) - 10} more")
        
        if untracked_user:
            print(f"\n❌ UNTRACKED USER MISSIONS ({len(untracked_user)}):")
            for signal in untracked_user[:10]:  # Show first 10
                source_status = "✅" if signal['has_source'] else "❌"
                print(f"  {source_status} {signal['mission_id']} - Source: {signal['source'] or 'MISSING'}")
            if len(untracked_user) > 10:
                print(f"  ... and {len(untracked_user) - 10} more")
        
        # Assessment
        total_untracked = len(untracked_main) + len(untracked_user)
        total_missions = len(main_missions) + len(user_missions)
        tracking_rate = ((total_missions - total_untracked) / total_missions * 100) if total_missions > 0 else 100
        
        print(f"\n📈 TRACKING EFFECTIVENESS:")
        print(f"  Tracking rate: {tracking_rate:.1f}%")
        
        if tracking_rate >= 95:
            print("  Status: ✅ EXCELLENT - Most signals are tracked")
        elif tracking_rate >= 80:
            print("  Status: ⚠️ GOOD - Some signals need tracking improvement")
        elif tracking_rate >= 60:
            print("  Status: ❌ POOR - Significant tracking gaps")
        else:
            print("  Status: 🚨 CRITICAL - Major tracking system failure")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if no_source_count > 0:
            print(f"  - Run fix_mission_source_tags.py to add missing source tags")
        if total_untracked > 0:
            print(f"  - Restart truth_tracker.py to pick up untracked signals")
            print(f"  - Investigate why {total_untracked} signals aren't being tracked")
        if tracking_rate < 80:
            print(f"  - Review truth tracker configuration and market data connectivity")
        
        print("="*60)
        
        return {
            'main_missions': len(main_missions),
            'user_missions': len(user_missions),
            'truth_signals': len(truth_signals),
            'untracked_main': len(untracked_main),
            'untracked_user': len(untracked_user),
            'tracking_rate': tracking_rate,
            'missing_source_tags': no_source_count
        }

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='BITTEN Signal Security Auditor')
    parser.add_argument('--rogue-check', action='store_true', 
                       help='Check for unauthorized signal attempts')
    parser.add_argument('--system-health', action='store_true',
                       help='Verify truth system health')
    parser.add_argument('--purge-scan', action='store_true',
                       help='Scan for signals bypassing purge')
    parser.add_argument('--full-audit', action='store_true',
                       help='Run complete security audit')
    parser.add_argument('--dual-track-scan', action='store_true',
                       help='Detect untracked legacy-format signals')
    
    args = parser.parse_args()
    
    auditor = SignalAuditor()
    
    if args.rogue_check:
        auditor.check_rogue_signals()
    elif args.system_health:
        auditor.check_system_health()
    elif args.purge_scan:
        auditor.purge_scan()
    elif args.full_audit:
        auditor.full_audit()
    elif args.dual_track_scan:
        auditor.dual_track_scan()
    else:
        # Default: run full audit
        auditor.full_audit()

if __name__ == "__main__":
    main()