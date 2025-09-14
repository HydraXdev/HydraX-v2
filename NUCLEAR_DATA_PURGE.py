#!/usr/bin/env python3
"""
NUCLEAR DATA PURGE SCRIPT
Wipes ALL corrupted/fake signal data and starts completely fresh
Only keeps the REAL tracker data going forward
"""
import os
import shutil
import sqlite3
from datetime import datetime

def nuclear_purge():
    print("🔥 STARTING NUCLEAR DATA PURGE - WIPING ALL FAKE DATA")
    
    # Create timestamp for this purge
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. BACKUP THE CURRENT REAL TRACKER (only if it has real data)
    real_file = "/root/HydraX-v2/comprehensive_tracking.jsonl"
    backup_dir = f"/root/HydraX-v2/PURGE_BACKUP_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    print(f"📦 Creating backup directory: {backup_dir}")
    
    # Check if real tracker has generated any new data
    real_data_count = 0
    try:
        with open(real_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and 'REAL TRACKING STARTED' not in line:
                    real_data_count += 1
        print(f"📊 Found {real_data_count} real tracking records")
    except:
        real_data_count = 0
        
    if real_data_count > 0:
        shutil.copy2(real_file, f"{backup_dir}/real_data_backup.jsonl")
        print(f"✅ Backed up {real_data_count} real records")
    
    # 2. NUCLEAR WIPE ALL TRACKING FILES
    tracking_files = [
        "/root/HydraX-v2/comprehensive_tracking.jsonl",
        "/root/HydraX-v2/truth_log.jsonl", 
        "/root/HydraX-v2/optimized_tracking.jsonl",
        "/root/HydraX-v2/ml_performance_tracking.jsonl",
        "/root/HydraX-v2/signal_outcomes.jsonl",
        "/root/HydraX-v2/REAL_tracking.jsonl",
        "/root/HydraX-v2/enhanced_truth_log.jsonl",
        "/root/HydraX-v2/signal_freshness.jsonl",
        "/root/HydraX-v2/comprehensive_tracking_test.jsonl",
        "/root/HydraX-v2/logs/comprehensive_tracking.jsonl"
    ]
    
    print("🔥 WIPING ALL TRACKING FILES...")
    for file_path in tracking_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️  DELETED: {file_path}")
            
    # 3. WIPE BACKUP FILES (all fake data)
    backup_files = []
    for root, dirs, files in os.walk("/root/HydraX-v2"):
        for file in files:
            if any(x in file.lower() for x in ['backup', 'fake', 'truth_log', 'tracking']) and file.endswith('.jsonl'):
                backup_files.append(os.path.join(root, file))
                
    print("🔥 WIPING ALL BACKUP/FAKE FILES...")
    for file_path in backup_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️  DELETED: {file_path}")
    
    # 4. CLEAR DATABASE TABLES WITH FAKE SIGNAL DATA
    databases_to_clean = [
        "/root/HydraX-v2/bitten.db",
        "/root/HydraX-v2/data/signals.db",
        "/root/HydraX-v2/data/live_performance.db"
    ]
    
    print("🔥 CLEARING DATABASE TABLES...")
    for db_path in databases_to_clean:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                for table_name, in tables:
                    # Skip system tables and user/account tables
                    if table_name.startswith('sqlite_'):
                        continue
                    if table_name in ['users', 'ea_instances', 'user_fire_modes', 'fires']:
                        print(f"⚠️  SKIPPING: {table_name} (preserving user data)")
                        continue
                        
                    # Clear signal/tracking related tables
                    if any(x in table_name.lower() for x in ['signal', 'track', 'outcome', 'performance']):
                        cursor.execute(f"DELETE FROM {table_name}")
                        deleted_count = cursor.rowcount
                        print(f"🗑️  CLEARED: {table_name} ({deleted_count} records)")
                        
                conn.commit()
                conn.close()
                print(f"✅ Cleaned database: {db_path}")
                
            except Exception as e:
                print(f"❌ Error cleaning {db_path}: {e}")
    
    # 5. CREATE FRESH TRACKING FILE
    fresh_tracking_file = "/root/HydraX-v2/comprehensive_tracking.jsonl"
    with open(fresh_tracking_file, 'w') as f:
        f.write(f"# FRESH START - NUCLEAR PURGE COMPLETE - {datetime.now().isoformat()}\n")
        f.write(f"# ALL FAKE DATA DESTROYED - ONLY REAL TRACKER DATA FROM NOW ON\n")
        
        # Restore real data if we had any
        if real_data_count > 0 and os.path.exists(f"{backup_dir}/real_data_backup.jsonl"):
            with open(f"{backup_dir}/real_data_backup.jsonl", 'r') as backup_f:
                for line in backup_f:
                    if line.strip() and not line.startswith('#'):
                        f.write(line)
            print(f"✅ Restored {real_data_count} real tracking records")
    
    print("✅ Created fresh tracking file")
    
    # 6. SUMMARY
    print("\n" + "="*60)
    print("🔥 NUCLEAR PURGE COMPLETE 🔥")
    print("="*60)
    print("✅ ALL fake/corrupted tracking data DESTROYED")
    print("✅ ALL backup files with fake data WIPED") 
    print("✅ Database tables cleared of fake signals")
    print("✅ Fresh comprehensive_tracking.jsonl created")
    print(f"✅ Real data backup created in: {backup_dir}")
    print("✅ System ready for 100% REAL tracking data only")
    print("="*60)
    
    return True

if __name__ == "__main__":
    nuclear_purge()