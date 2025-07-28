#!/usr/bin/env python3
"""
Comprehensive BITTEN System Cleanup Plan
Based on code audit results - implements systematic cleanup
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

class BittenSystemCleaner:
    def __init__(self, root_dir="/root/HydraX-v2"):
        self.root_dir = Path(root_dir)
        self.archive_dir = self.root_dir / "archive"
        self.broken_dir = self.archive_dir / "broken_syntax"
        self.duplicates_dir = self.archive_dir / "duplicates"
        self.orphaned_dir = self.archive_dir / "orphaned"
        self.backup_dir = self.archive_dir / "old_versions"
        
        # Ensure archive directories exist
        for dir_path in [self.archive_dir, self.broken_dir, self.duplicates_dir, self.orphaned_dir, self.backup_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_cleanup_manifest(self):
        """Define what needs to be cleaned based on audit"""
        
        # Files with syntax errors that are broken
        broken_syntax_files = [
            'BITTEN_InitSync_Module.py',
            'setup_stripe_products.py', 
            'venom_vs_apex_validator.py',
            'bitten_alerts_actual.py',
            'setup_persistent_menu.py',
            'apex_v5_lean.py',
            'user_mission_system.py',
            'AUTONOMOUS_OPERATION_VALIDATOR.py',
            'webapp_server.py',  # Has issues but keep for reference
        ]
        
        # Clear duplicates - keep the newer/better version
        duplicate_groups = {
            'apex_venom_v7_smart_timer': {
                'keep': 'apex_venom_v7_with_smart_timer.py',
                'archive': ['apex_venom_v7_with_smart_timer_original.py']
            },
            'tcs_engine': {
                'keep': 'core/tcs_engine_active.py',
                'archive': ['core/tcs_engine_v5.py']
            },
            'risk_management': {
                'keep': 'src/bitten_core/risk_management_active.py',
                'archive': ['src/bitten_core/risk_management_v5.py']
            },
            'market_data_receiver': {
                'keep': 'market_data_receiver_enhanced.py',
                'archive': ['market_data_receiver.py']
            },
            'engine_engineer': {
                'keep': 'engine_engineer_enhanced.py',
                'archive': ['core/engine_engineer_v2.py']
            },
            'mt5_enhanced_adapter': {
                'keep': 'src/bitten_core/mt5_enhanced_adapter.py',
                'archive': ['BITTEN_Windows_Package/API/mt5_enhanced_adapter.py']
            }
        }
        
        # Orphaned files that are not connected to anything
        orphaned_files = [
            'TELEGRAM_MENU_AAA.py',
            'summarize_docs.py',
            'SYSTEM_ENGINE_CONFIG.py',
            'MAIN_SIGNAL_ENGINE.py',
            'serve_ea.py',
            'add_live_mt5_endpoint.py',
            'show_one_style.py',
            'EDUCATION_TOUCHPOINTS.py',
            'dynamic_alert_elements.py',
            'build_full_index.py',
            'launch_live_farm.py',
            'verify_help_message.py',
            'show_all_mockups.py'
        ]
        
        # Old backup/version files that should be archived
        backup_version_files = [
            'troll_duty_upgrade_v3.py',
            'apex_production_v6_backup_20250718_232725.py',
            'hyper_engine_v1.py',
            'apex_v5_real_performance_backtest.py',
            'webapp_server_backup.py',
            'src/bitten_core/mission_briefing_generator_v5.py',
            'src/core/hydrastrike_v3.5.py'
        ]
        
        # Test files that are outdated or duplicated
        outdated_test_files = [
            'test_fake_data_disabled.py',
            'test_enhanced_connect_command.py', 
            'test_connect_enhancements.py',
            'test_citadel_enhanced.py',  # Keep test_citadel.py instead
            'test_public_signal_broadcast.py',
            'test_signal_broadcast_simple.py'
        ]
        
        return {
            'broken_syntax': broken_syntax_files,
            'duplicates': duplicate_groups,
            'orphaned': orphaned_files,
            'backup_versions': backup_version_files,
            'outdated_tests': outdated_test_files
        }
    
    def document_production_architecture(self):
        """Document the actual production architecture"""
        
        production_docs = {
            'timestamp': datetime.now().isoformat(),
            'core_production_files': {
                'bitten_production_bot.py': {
                    'purpose': 'Main Telegram bot - handles signals, tactics, execution, drill reports',
                    'status': 'ACTIVE - Currently running',
                    'dependencies': ['src/bitten_core/*', 'config/*'],
                    'tokens': 'BOT_TOKEN (7854827710...)'
                },
                'webapp_server_optimized.py': {
                    'purpose': 'WebApp server - mission HUD, onboarding, War Room',
                    'status': 'ACTIVE - Currently running',
                    'port': '8888',
                    'dependencies': ['src/bitten_core/*', 'templates/*']
                },
                'commander_throne.py': {
                    'purpose': 'Command center dashboard',
                    'status': 'ACTIVE - Currently running', 
                    'port': '8899',
                    'dependencies': ['minimal']
                },
                'bridge_fortress_daemon.py': {
                    'purpose': 'Bridge health monitoring and heartbeat system',
                    'status': 'ACTIVE - Currently running',
                    'location': '/root/core/bridge_fortress_daemon.py (symlinked)'
                },
                'bitten_voice_personality_bot.py': {
                    'purpose': 'Voice/personality bot - ATHENA, DRILL, NEXUS, DOC, OBSERVER',
                    'status': 'AVAILABLE - Not currently running',
                    'tokens': 'VOICE_BOT_TOKEN (8103700393...)'
                }
            },
            'signal_generation': {
                'apex_venom_v7_unfiltered.py': {
                    'purpose': 'VENOM v7.0 - Main signal generation engine',
                    'status': 'PRODUCTION ENGINE - 84.3% win rate',
                    'performance': '25+ signals/day, 3,250 trades validated'
                },
                'apex_venom_v7_with_smart_timer.py': {
                    'purpose': 'VENOM v7.0 with smart timer integration',
                    'status': 'ENHANCED VERSION'
                }
            },
            'supporting_systems': {
                'src/bitten_core/': 'Core business logic modules',
                'src/mt5_bridge/': 'MT5 integration adapters',
                'config/': 'Configuration files',
                'citadel_core/': 'CITADEL Shield System modules',
                'database/': 'Database management',
                'tests/': 'Test suite'
            },
            'infrastructure': {
                'start_both_bots.py': 'Dual bot launcher (recommended)',
                'start_production_bot.py': 'Single bot launcher',
                'webapp_server_optimized.py': 'WebApp server (standalone)',
                'commander_throne.py': 'Command center (standalone)'
            }
        }
        
        # Save documentation
        with open(self.root_dir / 'PRODUCTION_ARCHITECTURE.json', 'w') as f:
            json.dump(production_docs, f, indent=2)
            
        print("📋 Production architecture documented in PRODUCTION_ARCHITECTURE.json")
        return production_docs
    
    def clean_broken_syntax_files(self, manifest):
        """Move broken syntax files to archive"""
        print("\n🔧 CLEANING BROKEN SYNTAX FILES")
        print("-" * 40)
        
        for filename in manifest['broken_syntax']:
            file_path = self.root_dir / filename
            if file_path.exists():
                target_path = self.broken_dir / filename
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.move(str(file_path), str(target_path))
                print(f"🗂️ Moved {filename} → archive/broken_syntax/")
            else:
                print(f"⚠️ {filename} not found")
    
    def clean_duplicate_files(self, manifest):
        """Archive duplicate files, keep the better version"""
        print("\n🔧 CLEANING DUPLICATE FILES")
        print("-" * 40)
        
        for group_name, group_info in manifest['duplicates'].items():
            print(f"\n📁 {group_name}:")
            print(f"   ✅ Keeping: {group_info['keep']}")
            
            for duplicate in group_info['archive']:
                file_path = self.root_dir / duplicate
                if file_path.exists():
                    target_path = self.duplicates_dir / duplicate
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.move(str(file_path), str(target_path))
                    print(f"   🗂️ Archived: {duplicate}")
                else:
                    print(f"   ⚠️ Not found: {duplicate}")
    
    def clean_orphaned_files(self, manifest):
        """Archive orphaned files"""
        print("\n🔧 CLEANING ORPHANED FILES")
        print("-" * 40)
        
        for filename in manifest['orphaned']:
            file_path = self.root_dir / filename
            if file_path.exists():
                target_path = self.orphaned_dir / filename
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.move(str(file_path), str(target_path))
                print(f"🗂️ Moved {filename} → archive/orphaned/")
            else:
                print(f"⚠️ {filename} not found")
    
    def clean_backup_versions(self, manifest):
        """Archive old backup and version files"""
        print("\n🔧 CLEANING BACKUP/VERSION FILES")
        print("-" * 40)
        
        for filename in manifest['backup_versions']:
            file_path = self.root_dir / filename
            if file_path.exists():
                target_path = self.backup_dir / filename
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.move(str(file_path), str(target_path))
                print(f"🗂️ Moved {filename} → archive/old_versions/")
            else:
                print(f"⚠️ {filename} not found")
    
    def clean_outdated_tests(self, manifest):
        """Archive outdated test files"""
        print("\n🔧 CLEANING OUTDATED TEST FILES")
        print("-" * 40)
        
        for filename in manifest['outdated_tests']:
            file_path = self.root_dir / filename
            if file_path.exists():
                target_path = self.archive_dir / "outdated_tests" / filename
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.move(str(file_path), str(target_path))
                print(f"🗂️ Moved {filename} → archive/outdated_tests/")
            else:
                print(f"⚠️ {filename} not found")
    
    def create_cleanup_summary(self, manifest):
        """Create a summary of what was cleaned"""
        summary = {
            'cleanup_date': datetime.now().isoformat(),
            'total_files_archived': (
                len(manifest['broken_syntax']) +
                sum(len(group['archive']) for group in manifest['duplicates'].values()) +
                len(manifest['orphaned']) +
                len(manifest['backup_versions']) +
                len(manifest['outdated_tests'])
            ),
            'categories': {
                'broken_syntax': len(manifest['broken_syntax']),
                'duplicates': sum(len(group['archive']) for group in manifest['duplicates'].values()),
                'orphaned': len(manifest['orphaned']),
                'backup_versions': len(manifest['backup_versions']),
                'outdated_tests': len(manifest['outdated_tests'])
            },
            'archive_structure': {
                'archive/broken_syntax/': 'Files with syntax errors',
                'archive/duplicates/': 'Duplicate implementations',
                'archive/orphaned/': 'Unconnected files',
                'archive/old_versions/': 'Backup and version files',
                'archive/outdated_tests/': 'Outdated test files'
            }
        }
        
        with open(self.root_dir / 'CLEANUP_SUMMARY.json', 'w') as f:
            json.dump(summary, f, indent=2)
            
        return summary
    
    def run_comprehensive_cleanup(self, dry_run=True):
        """Run the complete cleanup process"""
        print("🧹 BITTEN SYSTEM COMPREHENSIVE CLEANUP")
        print("=" * 60)
        
        if dry_run:
            print("🚨 DRY RUN MODE - No files will be moved")
        else:
            print("🔥 LIVE MODE - Files will be moved to archive")
            
        # Get cleanup manifest
        manifest = self.get_cleanup_manifest()
        
        # Document current production architecture
        self.document_production_architecture()
        
        if not dry_run:
            # Perform cleanup
            self.clean_broken_syntax_files(manifest)
            self.clean_duplicate_files(manifest)
            self.clean_orphaned_files(manifest)
            self.clean_backup_versions(manifest)
            self.clean_outdated_tests(manifest)
            
            # Create summary
            summary = self.create_cleanup_summary(manifest)
            
            print(f"\n🎉 CLEANUP COMPLETE!")
            print(f"📊 Total files archived: {summary['total_files_archived']}")
            print(f"📋 Summary saved to: CLEANUP_SUMMARY.json")
        else:
            print(f"\n📋 DRY RUN SUMMARY:")
            total = (len(manifest['broken_syntax']) +
                    sum(len(group['archive']) for group in manifest['duplicates'].values()) +
                    len(manifest['orphaned']) +
                    len(manifest['backup_versions']) +
                    len(manifest['outdated_tests']))
            print(f"   Would archive {total} files")
            print(f"   Broken syntax: {len(manifest['broken_syntax'])}")
            print(f"   Duplicates: {sum(len(group['archive']) for group in manifest['duplicates'].values())}")
            print(f"   Orphaned: {len(manifest['orphaned'])}")
            print(f"   Backup versions: {len(manifest['backup_versions'])}")
            print(f"   Outdated tests: {len(manifest['outdated_tests'])}")
        
        return manifest

def main():
    cleaner = BittenSystemCleaner()
    
    # First run as dry run
    print("Running dry run to show what would be cleaned...")
    manifest = cleaner.run_comprehensive_cleanup(dry_run=True)
    
    print("\n" + "="*60)
    response = input("Proceed with actual cleanup? (y/N): ")
    
    if response.lower() == 'y':
        print("\nRunning live cleanup...")
        cleaner.run_comprehensive_cleanup(dry_run=False)
    else:
        print("Cleanup cancelled. Files remain unchanged.")

if __name__ == "__main__":
    main()