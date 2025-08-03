#!/usr/bin/env python3
"""
Legacy Cleanup Executor - Safely removes legacy components
Preserves critical ZMQ and production infrastructure
"""

import os
import shutil
import glob
import re
from pathlib import Path
from datetime import datetime
import json

class LegacyCleanupExecutor:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.archive_dir = "archive/legacy_purge_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        self.preserved_files = [
            # Critical ZMQ infrastructure
            "zmq_bitten_controller.py",
            "zmq_telemetry_service.py", 
            "zmq_fire_publisher_daemon.py",
            "zmq_telemetry_daemon.py",
            "zmq_xp_integration.py",
            "zmq_risk_integration.py",
            "zmq_migration_helpers.py",
            
            # Core production files
            "apex_venom_v7_unfiltered.py",
            "working_signal_generator.py",
            "bitten_production_bot.py",
            "webapp_server_optimized.py",
            "src/bitten_core/fire_router.py",
            
            # ForexVPS integration
            "forexvps/client.py",
            "config/settings.py"
        ]
        self.cleanup_log = []
        
    def run(self):
        """Execute cleanup process"""
        print(f"🧹 Legacy Cleanup Executor - {'DRY RUN' if self.dry_run else 'EXECUTE'} Mode")
        print("="*60)
        
        if not self.dry_run:
            os.makedirs(self.archive_dir, exist_ok=True)
            
        # 1. Clean up file-based execution references
        self._cleanup_fire_txt_references()
        
        # 2. Remove Wine/Docker infrastructure
        self._cleanup_wine_docker()
        
        # 3. Remove obsolete EAs
        self._cleanup_obsolete_eas()
        
        # 4. Update configuration
        self._update_configuration()
        
        # 5. Clean temp files
        self._cleanup_temp_files()
        
        # 6. Generate report
        self._generate_report()
        
    def _cleanup_fire_txt_references(self):
        """Remove or update files with fire.txt references"""
        print("\n🔥 Cleaning file-based execution references...")
        
        # Files to update (preserve but modify)
        files_to_update = {
            "src/bitten_core/fire_router.py": self._update_fire_router,
            ".env": self._update_env_file
        }
        
        # Files to archive (not critical)
        files_to_archive = []
        
        # Search for fire.txt references
        for root, dirs, files in os.walk('.'):
            # Skip archive and critical dirs
            if any(skip in root for skip in ['archive', '.git', '__pycache__', 'venv', 'lockbox']):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    
                    # Skip preserved files
                    if any(preserved in filepath for preserved in self.preserved_files):
                        continue
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Check for fire.txt references
                        if re.search(r'fire\.txt|trade_result\.txt|fire_path', content, re.IGNORECASE):
                            # If it's an update target, update it
                            if filepath in files_to_update:
                                files_to_update[filepath](filepath)
                            # Otherwise archive it
                            else:
                                files_to_archive.append(filepath)
                                
                    except Exception as e:
                        print(f"  ⚠️ Error reading {filepath}: {e}")
                        
        # Archive files
        for filepath in files_to_archive:
            self._archive_file(filepath, "file_based_execution")
            
    def _cleanup_wine_docker(self):
        """Remove Wine/Docker related files and directories"""
        print("\n🍷 Cleaning Wine/Docker infrastructure...")
        
        # Patterns to remove
        patterns = [
            "wine_*",
            "*.wine",
            "winetricks*",
            "mt5_wine*",
            "Dockerfile.mt5",
            "docker-compose*.yml",
            "start_mt5.sh",
            "spinup_terminal.sh",
            "inject_login.sh"
        ]
        
        for pattern in patterns:
            matches = glob.glob(pattern, recursive=False)
            for match in matches:
                if os.path.exists(match):
                    self._archive_file(match, "wine_docker")
                    
    def _cleanup_obsolete_eas(self):
        """Remove obsolete EA files"""
        print("\n🤖 Cleaning obsolete EAs...")
        
        # EA files to remove (keeping only ZMQ v7)
        obsolete_eas = [
            "mq5/BITTENBridge_TradeExecutor_PRODUCTION.mq5",
            "mq5/BITTENBridge_TradeExecutor_DEBUG.mq5",
            "mq5/BITTENBridge_TradeExecutor_FIXED.mq5",
            "mq5/BITTENBridge_TradeExecutor_FIXED_v2.mq5",
            "mq5/BITTENBridge_TradeExecutor_LEAN.mq5"
        ]
        
        for ea_file in obsolete_eas:
            if os.path.exists(ea_file):
                self._archive_file(ea_file, "obsolete_eas")
                
    def _update_configuration(self):
        """Update configuration files"""
        print("\n⚙️ Updating configuration...")
        
        # Update .env to disable dual-write
        self._update_env_file(".env")
        
    def _cleanup_temp_files(self):
        """Clean temporary files"""
        print("\n📄 Cleaning temp files...")
        
        # Clean /tmp files
        tmp_patterns = [
            "/tmp/*bitten*",
            "/tmp/*fire*", 
            "/tmp/*mt5*"
        ]
        
        for pattern in tmp_patterns:
            matches = glob.glob(pattern)
            for match in matches:
                self._remove_file(match, "temp_files")
                
    def _update_fire_router(self, filepath):
        """Update fire_router.py to remove dual-write"""
        if self.dry_run:
            self.cleanup_log.append({
                "action": "UPDATE",
                "file": filepath,
                "reason": "Remove dual-write mode"
            })
            return
            
        try:
            # Backup original
            shutil.copy2(filepath, filepath + ".bak")
            
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Update content to force ZMQ only
            content = re.sub(
                r'if\s+os\.getenv\(["\']ZMQ_DUAL_WRITE["\'],\s*["\']false["\']\)\.lower\(\)\s*==\s*["\']true["\']:',
                'if False:  # Dual-write disabled permanently',
                content
            )
            
            with open(filepath, 'w') as f:
                f.write(content)
                
            self.cleanup_log.append({
                "action": "UPDATED",
                "file": filepath,
                "changes": "Disabled dual-write mode"
            })
            
        except Exception as e:
            print(f"  ❌ Error updating {filepath}: {e}")
            
    def _update_env_file(self, filepath):
        """Update .env file"""
        if not os.path.exists(filepath):
            return
            
        if self.dry_run:
            self.cleanup_log.append({
                "action": "UPDATE",
                "file": filepath,
                "reason": "Set USE_ZMQ=true, ZMQ_DUAL_WRITE=false"
            })
            return
            
        try:
            # Backup original
            shutil.copy2(filepath, filepath + ".bak")
            
            with open(filepath, 'r') as f:
                lines = f.readlines()
                
            # Update lines
            new_lines = []
            for line in lines:
                if line.startswith("USE_ZMQ="):
                    new_lines.append("USE_ZMQ=true\n")
                elif line.startswith("ZMQ_DUAL_WRITE="):
                    new_lines.append("ZMQ_DUAL_WRITE=false\n")
                else:
                    new_lines.append(line)
                    
            with open(filepath, 'w') as f:
                f.writelines(new_lines)
                
            self.cleanup_log.append({
                "action": "UPDATED",
                "file": filepath,
                "changes": "Set USE_ZMQ=true, ZMQ_DUAL_WRITE=false"
            })
            
        except Exception as e:
            print(f"  ❌ Error updating {filepath}: {e}")
            
    def _archive_file(self, filepath, category):
        """Archive a file to the archive directory"""
        if self.dry_run:
            self.cleanup_log.append({
                "action": "ARCHIVE",
                "file": filepath,
                "category": category
            })
            print(f"  📦 Would archive: {filepath}")
            return
            
        try:
            # Create category directory
            category_dir = os.path.join(self.archive_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            
            # Move file
            dest = os.path.join(category_dir, os.path.basename(filepath))
            shutil.move(filepath, dest)
            
            self.cleanup_log.append({
                "action": "ARCHIVED",
                "file": filepath,
                "destination": dest
            })
            print(f"  ✅ Archived: {filepath}")
            
        except Exception as e:
            print(f"  ❌ Error archiving {filepath}: {e}")
            
    def _remove_file(self, filepath, category):
        """Remove a temporary file"""
        if self.dry_run:
            self.cleanup_log.append({
                "action": "REMOVE",
                "file": filepath,
                "category": category
            })
            print(f"  🗑️ Would remove: {filepath}")
            return
            
        try:
            if os.path.isfile(filepath):
                os.remove(filepath)
            elif os.path.isdir(filepath):
                shutil.rmtree(filepath)
                
            self.cleanup_log.append({
                "action": "REMOVED",
                "file": filepath
            })
            print(f"  ✅ Removed: {filepath}")
            
        except Exception as e:
            print(f"  ❌ Error removing {filepath}: {e}")
            
    def _generate_report(self):
        """Generate cleanup report"""
        print("\n" + "="*60)
        print("📊 CLEANUP SUMMARY")
        print("="*60)
        
        # Count actions
        actions = {}
        for entry in self.cleanup_log:
            action = entry['action']
            actions[action] = actions.get(action, 0) + 1
            
        # Print summary
        for action, count in actions.items():
            print(f"{action}: {count} files")
            
        print(f"\nTotal items processed: {len(self.cleanup_log)}")
        
        if self.dry_run:
            print("\n⚠️ DRY RUN - No actual changes made")
            print("Run with --execute to perform cleanup")
        else:
            # Save log
            log_file = f"cleanup_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(log_file, 'w') as f:
                json.dump(self.cleanup_log, f, indent=2)
            print(f"\n✅ Cleanup complete! Log saved to: {log_file}")

if __name__ == "__main__":
    import sys
    
    dry_run = '--execute' not in sys.argv
    
    if not dry_run:
        print("⚠️ WARNING: This will permanently modify files!")
        print("Press Ctrl+C to cancel, or Enter to continue...")
        try:
            input()
        except KeyboardInterrupt:
            print("\n❌ Cleanup cancelled")
            sys.exit(0)
    
    executor = LegacyCleanupExecutor(dry_run=dry_run)
    executor.run()