#!/usr/bin/env python3
"""
Rollback script for Press Pass deployment
"""

import os
import sys
import shutil
from datetime import datetime

def rollback(backup_timestamp):
    """Rollback to a specific backup"""
    backup_dir = f"/root/HydraX-v2/backups/{backup_timestamp}"
    
    if not os.path.exists(backup_dir):
        print(f"❌ Backup not found: {backup_dir}")
        return False
    
    print(f"🔄 Rolling back to backup: {backup_timestamp}")
    
    # Restore items
    restore_items = [
        ("telegram_router.py", "src/bitten_core/telegram_router.py"),
        ("config", "config"),
        ("webapp", "/var/www/html"),
        ("bitten_core_backup", "src/bitten_core")
    ]
    
    for source, dest in restore_items:
        source_path = os.path.join(backup_dir, source)
        if os.path.exists(source_path):
            if os.path.isdir(source_path):
                if os.path.exists(dest):
                    shutil.rmtree(dest)
                shutil.copytree(source_path, dest)
            else:
                shutil.copy2(source_path, dest)
            print(f"✓ Restored: {source} -> {dest}")
    
    # Restart services
    os.system("nginx -t && systemctl reload nginx")
    os.system("systemctl restart hydrax-bot || true")
    
    print("✅ Rollback completed!")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 rollback.py <backup_timestamp>")
        print("\nAvailable backups:")
        backup_root = "/root/HydraX-v2/backups"
        if os.path.exists(backup_root):
            for backup in sorted(os.listdir(backup_root)):
                print(f"  - {backup}")
        sys.exit(1)
    
    success = rollback(sys.argv[1])
    sys.exit(0 if success else 1)