#!/usr/bin/env python3
"""
🧹 BITTEN Trade Data Purge Tool
Comprehensive purge of old trade logs and data to prevent number skewing

This tool identifies and optionally purges all historical trade data that could
contaminate new performance metrics with old R:R ratios (2.0/3.0).
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from pathlib import Path

class DataPurger:
    def __init__(self):
        self.base_path = Path("/root/HydraX-v2")
        self.findings = []
        
    def scan_file_data(self):
        """Scan file-based trade data"""
        print("🔍 Scanning file-based trade data...")
        
        # Check CSV/JSON trade files
        trade_files = [
            "fired_trades.csv",
            "fired_trades.json",
            "raw_trade_logs.txt"
        ]
        
        for file_name in trade_files:
            file_path = self.base_path / file_name
            if file_path.exists():
                size = file_path.stat().st_size
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                # Check content for old R:R ratios
                old_ratios_found = False
                try:
                    content = file_path.read_text()
                    if any(ratio in content for ratio in ["2.0", "3.0", "2.45", "2.36"]):
                        old_ratios_found = True
                except:
                    pass
                
                self.findings.append({
                    'type': 'file',
                    'path': str(file_path),
                    'size': size,
                    'modified': mtime.strftime('%Y-%m-%d %H:%M:%S'),
                    'old_ratios': old_ratios_found,
                    'action': 'PURGE' if old_ratios_found else 'KEEP'
                })
        
        # Check backtest result files
        result_files = list(self.base_path.glob("*results.json"))
        for file_path in result_files:
            if "backtest" in file_path.name or "performance" in file_path.name:
                size = file_path.stat().st_size
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                self.findings.append({
                    'type': 'backtest_file',
                    'path': str(file_path),
                    'size': size,
                    'modified': mtime.strftime('%Y-%m-%d %H:%M:%S'),
                    'old_ratios': True,  # Assume all backtest files have old data
                    'action': 'ARCHIVE'  # Don't delete, move to archive
                })
    
    def scan_database_data(self):
        """Scan database-based trade data"""
        print("🔍 Scanning database trade data...")
        
        db_files = [
            "data/signal_accuracy.db",
            "data/bitten_production.db", 
            "data/live_performance.db",
            "data/real_statistics.db",
            "signal_tracker.db"
        ]
        
        for db_file in db_files:
            db_path = self.base_path / db_file
            if db_path.exists():
                try:
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    
                    # Get all tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    
                    total_rows = 0
                    trade_related_tables = []
                    
                    for table in tables:
                        table_name = table[0]
                        if any(keyword in table_name.lower() for keyword in 
                               ['trade', 'signal', 'performance', 'execution', 'fire']):
                            try:
                                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                                count = cursor.fetchone()[0]
                                total_rows += count
                                if count > 0:
                                    trade_related_tables.append((table_name, count))
                            except:
                                pass
                    
                    conn.close()
                    
                    self.findings.append({
                        'type': 'database',
                        'path': str(db_path),
                        'tables': len(tables),
                        'trade_tables': trade_related_tables,
                        'total_rows': total_rows,
                        'action': 'BACKUP_AND_PURGE' if total_rows > 0 else 'KEEP'
                    })
                    
                except Exception as e:
                    self.findings.append({
                        'type': 'database_error',
                        'path': str(db_path),
                        'error': str(e),
                        'action': 'MANUAL_CHECK'
                    })
    
    def scan_mission_files(self):
        """Scan mission files for old R:R ratios"""
        print("🔍 Scanning mission files...")
        
        missions_dir = self.base_path / "missions"
        if missions_dir.exists():
            old_missions = 0
            new_missions = 0
            
            for mission_file in missions_dir.glob("*.json"):
                try:
                    content = mission_file.read_text()
                    mission_data = json.loads(content)
                    
                    # Check for old risk_reward values
                    risk_reward = mission_data.get('signal', {}).get('risk_reward', 0)
                    enhanced_rr = mission_data.get('enhanced_signal', {}).get('risk_reward_ratio', 0)
                    
                    if risk_reward >= 2.0 or enhanced_rr >= 2.0:
                        old_missions += 1
                    else:
                        new_missions += 1
                        
                except:
                    pass
            
            self.findings.append({
                'type': 'mission_files',
                'path': str(missions_dir),
                'old_ratio_missions': old_missions,
                'new_ratio_missions': new_missions,
                'action': 'PURGE_OLD' if old_missions > 0 else 'KEEP_ALL'
            })
    
    def generate_report(self):
        """Generate comprehensive data audit report"""
        print("\n" + "="*80)
        print("🧹 BITTEN TRADE DATA AUDIT REPORT")
        print("="*80)
        print(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base Path: {self.base_path}")
        print(f"Total Items Scanned: {len(self.findings)}")
        
        # Categorize findings
        files_to_purge = []
        databases_to_backup = []
        archives_needed = []
        clean_items = []
        
        for finding in self.findings:
            if finding['action'] == 'PURGE':
                files_to_purge.append(finding)
            elif finding['action'] == 'BACKUP_AND_PURGE':
                databases_to_backup.append(finding)
            elif finding['action'] == 'ARCHIVE':
                archives_needed.append(finding)
            elif finding['action'] in ['KEEP', 'KEEP_ALL']:
                clean_items.append(finding)
        
        print(f"\n📊 SUMMARY:")
        print(f"  🗑️  Files to Purge: {len(files_to_purge)}")
        print(f"  💾 Databases to Backup/Purge: {len(databases_to_backup)}")
        print(f"  📦 Files to Archive: {len(archives_needed)}")
        print(f"  ✅ Clean Items: {len(clean_items)}")
        
        print(f"\n🗑️ FILES TO PURGE (contain old R:R ratios):")
        for item in files_to_purge:
            print(f"  • {item['path']} ({item['size']} bytes, modified: {item['modified']})")
        
        print(f"\n💾 DATABASES TO BACKUP/PURGE:")
        for item in databases_to_backup:
            print(f"  • {item['path']} ({item['total_rows']} trade-related rows)")
            for table, count in item.get('trade_tables', []):
                print(f"    - {table}: {count} rows")
        
        print(f"\n📦 FILES TO ARCHIVE:")
        for item in archives_needed:
            print(f"  • {item['path']} ({item['size']} bytes)")
        
        # Check current truth log
        truth_log = self.base_path / "truth_log.jsonl"
        if truth_log.exists():
            size = truth_log.stat().st_size
            with open(truth_log, 'r') as f:
                lines = f.readlines()
            print(f"\n📝 CURRENT TRUTH LOG:")
            print(f"  • {truth_log} ({size} bytes, {len(lines)} entries)")
            print(f"  • Status: {'CLEAN - New format only' if size < 1000 else 'CONTAINS DATA'}")
    
    def execute_purge(self, confirm=False):
        """Execute the data purge with confirmation"""
        if not confirm:
            print(f"\n⚠️  DRY RUN MODE - No files will be modified")
            print(f"   Add --execute flag to perform actual purge")
            return
        
        print(f"\n🚨 EXECUTING DATA PURGE...")
        
        # Create archive directory
        archive_dir = self.base_path / "archive" / "pre_rr_update_data" 
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        purged_count = 0
        
        for finding in self.findings:
            if finding['action'] == 'PURGE':
                file_path = Path(finding['path'])
                if file_path.exists():
                    # Move to archive instead of delete
                    archive_path = archive_dir / file_path.name
                    file_path.rename(archive_path)
                    print(f"  ✅ Archived: {file_path.name}")
                    purged_count += 1
            
            elif finding['action'] == 'BACKUP_AND_PURGE':
                db_path = Path(finding['path'])
                if db_path.exists():
                    # Create backup
                    backup_path = archive_dir / f"{db_path.name}.backup"
                    
                    # Copy database
                    import shutil
                    shutil.copy2(db_path, backup_path)
                    
                    # Clear trade-related tables
                    try:
                        conn = sqlite3.connect(str(db_path))
                        cursor = conn.cursor()
                        
                        for table, count in finding.get('trade_tables', []):
                            cursor.execute(f"DELETE FROM {table}")
                            print(f"  ✅ Cleared {table}: {count} rows removed")
                        
                        conn.commit()
                        conn.close()
                        
                        print(f"  ✅ Database purged: {db_path.name} (backup created)")
                        purged_count += 1
                        
                    except Exception as e:
                        print(f"  ❌ Error purging {db_path.name}: {e}")
        
        print(f"\n✅ PURGE COMPLETE: {purged_count} items processed")
        print(f"📦 All old data archived to: {archive_dir}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='BITTEN Trade Data Purge Tool')
    parser.add_argument('--execute', action='store_true', 
                       help='Execute purge (default is dry-run)')
    parser.add_argument('--report-only', action='store_true',
                       help='Generate report without purge options')
    
    args = parser.parse_args()
    
    purger = DataPurger()
    
    # Perform scans
    purger.scan_file_data()
    purger.scan_database_data() 
    purger.scan_mission_files()
    
    # Generate report
    purger.generate_report()
    
    if not args.report_only:
        # Execute purge
        purger.execute_purge(confirm=args.execute)
    
    print(f"\n🔍 Use 'python3 purge_old_trade_data.py --execute' to perform actual purge")

if __name__ == "__main__":
    main()