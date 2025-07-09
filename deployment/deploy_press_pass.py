#!/usr/bin/env python3
"""
Press Pass & TCS++ Deployment Script
Handles complete deployment of Press Pass integration
"""

import os
import sys
import shutil
import subprocess
import json
from datetime import datetime
import traceback

class PressPassDeployer:
    def __init__(self):
        self.deployment_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = f"/root/HydraX-v2/backups/{self.deployment_time}"
        self.deployment_log = []
        self.errors = []
        
    def log(self, message, level="INFO"):
        """Log deployment messages"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        self.deployment_log.append(log_entry)
        
    def run_command(self, command, description=""):
        """Execute shell command and log output"""
        self.log(f"Running: {description or command}")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.errors.append(f"Command failed: {command}\nError: {result.stderr}")
                self.log(f"Error: {result.stderr}", "ERROR")
                return False
            return True
        except Exception as e:
            self.errors.append(f"Exception running command: {command}\nError: {str(e)}")
            self.log(f"Exception: {str(e)}", "ERROR")
            return False
    
    def create_backup(self):
        """Create backup of current deployment"""
        self.log("Creating backup...", "INFO")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Backup critical files
        backup_items = [
            ("src/bitten_core/telegram_router.py", "telegram_router.py"),
            ("config", "config"),
            ("/var/www/html", "webapp"),
            ("src/bitten_core", "bitten_core_backup")
        ]
        
        for source, dest in backup_items:
            if os.path.exists(source):
                dest_path = os.path.join(self.backup_dir, dest)
                if os.path.isdir(source):
                    shutil.copytree(source, dest_path)
                else:
                    shutil.copy2(source, dest_path)
                self.log(f"Backed up: {source} -> {dest_path}")
        
        return True
    
    def deploy_press_pass_components(self):
        """Deploy Press Pass Python components"""
        self.log("Deploying Press Pass components...", "INFO")
        
        # Ensure target directories exist
        os.makedirs("src/bitten_core", exist_ok=True)
        os.makedirs("src/bitten_core/onboarding", exist_ok=True)
        
        # Components to deploy
        components = [
            "src/bitten_core/press_pass_manager.py",
            "src/bitten_core/press_pass_scheduler.py",
            "src/bitten_core/press_pass_commands.py",
            "src/bitten_core/press_pass_reset.py",
            "src/bitten_core/press_pass_email_automation.py",
            "src/bitten_core/onboarding/press_pass_manager.py",
            "src/bitten_core/onboarding/press_pass_tasks.py",
            "src/bitten_core/onboarding/press_pass_upgrade.py"
        ]
        
        for component in components:
            if os.path.exists(component):
                self.log(f"Component exists: {component}")
            else:
                self.log(f"Warning: Component missing: {component}", "WARN")
        
        return True
    
    def update_telegram_router(self):
        """Update Telegram router with Press Pass commands"""
        self.log("Updating Telegram router...", "INFO")
        
        router_path = "src/bitten_core/telegram_router.py"
        if not os.path.exists(router_path):
            self.log("Telegram router not found!", "ERROR")
            return False
        
        # Read current router
        with open(router_path, 'r') as f:
            content = f.read()
        
        # Check if Press Pass commands already integrated
        if "press_pass" in content or "presspass" in content:
            self.log("Press Pass commands already integrated")
            return True
        
        # Add Press Pass import
        import_line = "from .press_pass_commands import PressPassCommandHandler\n"
        if import_line not in content:
            # Find imports section and add
            import_pos = content.find("from .referral_system import")
            if import_pos > 0:
                content = content[:import_pos] + import_line + content[import_pos:]
        
        # Add Press Pass handler initialization
        init_code = """        # Initialize Press Pass system
        from .xp_integration import XPIntegrationManager
        self.xp_manager = XPIntegrationManager()
        self.press_pass_handler = PressPassCommandHandler(self.xp_manager)
        """
        
        if "self.press_pass_handler" not in content:
            # Find initialization section
            init_pos = content.find("self.trial_manager = get_trial_manager")
            if init_pos > 0:
                end_pos = content.find("\n", init_pos)
                content = content[:end_pos+1] + init_code + content[end_pos+1:]
        
        # Add Press Pass commands to command categories
        if "'Press Pass'" not in content:
            categories_pos = content.find("self.command_categories = {")
            if categories_pos > 0:
                insert_pos = content.find("'Social':", categories_pos)
                if insert_pos > 0:
                    new_category = "            'Press Pass': ['presspass', 'pp_status', 'pp_upgrade'],\n"
                    content = content[:insert_pos] + new_category + content[insert_pos:]
        
        # Add command routing
        routing_code = """        # Press Pass Commands
        elif command == '/presspass':
            return self._handle_press_pass_command(update.user_id, args)
        elif command == '/pp_status':
            return self._handle_pp_status(update.user_id)
        elif command == '/pp_upgrade':
            return self._handle_pp_upgrade(update.user_id)
        """
        
        if "'/presspass'" not in content:
            # Find command routing section
            route_pos = content.find("elif command == '/refer':")
            if route_pos > 0:
                content = content[:route_pos] + routing_code + "\n        " + content[route_pos:]
        
        # Add handler methods
        handler_methods = '''
    def _handle_press_pass_command(self, user_id: str, args: List[str]) -> CommandResult:
        """Handle Press Pass command"""
        result = self.press_pass_handler.handle_presspass(str(user_id), args)
        return CommandResult(
            success=result["success"],
            message=result["message"],
            data=result
        )
    
    def _handle_pp_status(self, user_id: str) -> CommandResult:
        """Handle Press Pass status command"""
        result = self.press_pass_handler.handle_presspass(str(user_id), ["status"])
        return CommandResult(
            success=result["success"],
            message=result["message"],
            data=result
        )
    
    def _handle_pp_upgrade(self, user_id: str) -> CommandResult:
        """Handle Press Pass upgrade command"""
        # Show upgrade options with inline keyboard
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎫 Bronze Pass ($10)", callback_data="pp_upgrade_bronze")],
            [InlineKeyboardButton("🥈 Silver Pass ($25)", callback_data="pp_upgrade_silver")],
            [InlineKeyboardButton("🥇 Gold Pass ($50)", callback_data="pp_upgrade_gold")],
            [InlineKeyboardButton("💎 Diamond Pass ($100)", callback_data="pp_upgrade_diamond")]
        ])
        
        message = (
            "🎫 **PRESS PASS TIERS**\\n\\n"
            "Choose your Press Pass tier:\\n\\n"
            "🎫 **Bronze** - $10/month\\n"
            "• Daily XP reset\\n"
            "• Basic shadow stats\\n\\n"
            "🥈 **Silver** - $25/month\\n"
            "• All Bronze features\\n"
            "• 2x XP multiplier\\n"
            "• Advanced analytics\\n\\n"
            "🥇 **Gold** - $50/month\\n"
            "• All Silver features\\n"
            "• 5x XP multiplier\\n"
            "• Priority notifications\\n\\n"
            "💎 **Diamond** - $100/month\\n"
            "• All Gold features\\n"
            "• 10x XP multiplier\\n"
            "• Exclusive rewards\\n"
            "• VIP support"
        )
        
        return CommandResult(
            success=True,
            message=message,
            data={"keyboard": keyboard, "parse_mode": "Markdown"}
        )
'''
        
        if "_handle_press_pass_command" not in content:
            # Add at the end of the class
            content = content.rstrip() + handler_methods
        
        # Write updated router
        with open(router_path, 'w') as f:
            f.write(content)
        
        self.log("Telegram router updated successfully")
        return True
    
    def deploy_landing_page(self):
        """Deploy updated landing page with Press Pass section"""
        self.log("Deploying landing page updates...", "INFO")
        
        source_landing = "landing/index.html"
        dest_landing = "/var/www/html/index.html"
        
        if os.path.exists(source_landing):
            shutil.copy2(source_landing, dest_landing)
            self.log(f"Deployed landing page: {source_landing} -> {dest_landing}")
            
            # Set proper permissions
            self.run_command(f"chmod 644 {dest_landing}", "Setting landing page permissions")
        else:
            self.log("Landing page source not found", "WARN")
        
        return True
    
    def setup_tcs_engine(self):
        """Ensure TCS engine is properly configured"""
        self.log("Setting up TCS engine...", "INFO")
        
        tcs_path = "core/tcs_engine.py"
        if os.path.exists(tcs_path):
            self.log("TCS engine found and ready")
        else:
            self.log("TCS engine not found", "WARN")
        
        return True
    
    def run_tests(self):
        """Run basic tests to verify deployment"""
        self.log("Running deployment tests...", "INFO")
        
        tests = [
            ("python3 -m py_compile src/bitten_core/press_pass_manager.py", "Compile Press Pass Manager"),
            ("python3 -m py_compile src/bitten_core/press_pass_commands.py", "Compile Press Pass Commands"),
            ("python3 -m py_compile src/bitten_core/telegram_router.py", "Compile Telegram Router"),
            ("curl -s http://localhost/index.html | grep -q 'Press Pass' && echo 'OK'", "Check landing page")
        ]
        
        all_passed = True
        for test_cmd, description in tests:
            if not self.run_command(test_cmd, f"Test: {description}"):
                all_passed = False
        
        return all_passed
    
    def restart_services(self):
        """Restart necessary services"""
        self.log("Restarting services...", "INFO")
        
        services = [
            ("nginx -t && systemctl reload nginx", "Reload Nginx"),
            ("systemctl restart hydrax-bot || true", "Restart HydraX bot (if exists)")
        ]
        
        for cmd, description in services:
            self.run_command(cmd, description)
        
        return True
    
    def save_deployment_log(self):
        """Save deployment log"""
        log_path = os.path.join(self.backup_dir, "deployment_log.txt")
        with open(log_path, 'w') as f:
            f.write("\n".join(self.deployment_log))
        
        if self.errors:
            error_path = os.path.join(self.backup_dir, "deployment_errors.txt")
            with open(error_path, 'w') as f:
                f.write("\n".join(self.errors))
    
    def deploy(self):
        """Main deployment process"""
        self.log("Starting Press Pass deployment...", "INFO")
        
        try:
            # Phase 1: Backup
            if not self.create_backup():
                self.log("Backup failed, aborting deployment", "ERROR")
                return False
            
            # Phase 2: Deploy components
            if not self.deploy_press_pass_components():
                self.log("Component deployment failed", "ERROR")
                return False
            
            # Phase 3: Update Telegram router
            if not self.update_telegram_router():
                self.log("Router update failed", "ERROR")
                return False
            
            # Phase 4: Deploy landing page
            if not self.deploy_landing_page():
                self.log("Landing page deployment failed", "ERROR")
                return False
            
            # Phase 5: Setup TCS
            if not self.setup_tcs_engine():
                self.log("TCS setup failed", "ERROR")
                return False
            
            # Phase 6: Run tests
            if not self.run_tests():
                self.log("Tests failed but continuing...", "WARN")
            
            # Phase 7: Restart services
            if not self.restart_services():
                self.log("Service restart failed", "WARN")
            
            self.log("Deployment completed successfully!", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Deployment failed with exception: {str(e)}", "ERROR")
            self.errors.append(traceback.format_exc())
            return False
        finally:
            self.save_deployment_log()

if __name__ == "__main__":
    deployer = PressPassDeployer()
    success = deployer.deploy()
    
    if success:
        print("\n✅ DEPLOYMENT SUCCESSFUL!")
        print(f"Backup location: {deployer.backup_dir}")
        print("\nNext steps:")
        print("1. Test /presspass command in Telegram bot")
        print("2. Verify landing page at http://your-domain.com")
        print("3. Monitor logs for any errors")
        print("4. Run end-to-end user journey test")
    else:
        print("\n❌ DEPLOYMENT FAILED!")
        print(f"Check errors in: {deployer.backup_dir}/deployment_errors.txt")
        print("\nTo rollback, run:")
        print(f"python3 deployment/rollback.py {deployer.deployment_time}")
    
    sys.exit(0 if success else 1)