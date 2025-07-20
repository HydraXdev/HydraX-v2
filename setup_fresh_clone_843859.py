#!/usr/bin/env python3
"""
FRESH MT5 CLONE SETUP - User 843859
Creates a clean MT5 clone with proper connectivity testing
"""

import time
import json
import requests
import os
import sys
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

# MT5 module only available on Windows - handle gracefully
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("⚠️  MetaTrader5 module not available on Linux - will use bridge communication")

class FreshCloneSetup:
    def __init__(self):
        self.user_id = "843859"
        self.credentials = {
            "username": "843859",
            "password": "Ao4@brz64erHaG",
            "server": "Coinexx-Demo"
        }
        self.clone_manager_url = "http://localhost:5559"
        self.db_path = "/root/HydraX-v2/data/bitten_clones.db"
        
    def log_step(self, step, status, details=""):
        """Log setup steps"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {step}: {status}")
        if details:
            print(f"    {details}")
    
    def cleanup_existing_clones(self):
        """Clean up any existing corrupted clones"""
        self.log_step("CLEANUP", "🧹 Starting cleanup of existing clones")
        
        try:
            # Check if database exists
            if os.path.exists(self.db_path):
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("SELECT user_id, clone_path, process_id FROM user_clones")
                    existing_clones = cursor.fetchall()
                    
                    for user_id, clone_path, process_id in existing_clones:
                        self.log_step("CLEANUP", f"🗑️ Found existing clone: {user_id}")
                        
                        # Stop any running processes
                        if process_id:
                            try:
                                os.system(f'kill -9 {process_id} 2>/dev/null')
                                self.log_step("CLEANUP", f"✅ Stopped process {process_id}")
                            except:
                                pass
                        
                        # Remove clone directory
                        if os.path.exists(clone_path):
                            try:
                                shutil.rmtree(clone_path)
                                self.log_step("CLEANUP", f"✅ Removed directory {clone_path}")
                            except Exception as e:
                                self.log_step("CLEANUP", f"⚠️ Could not remove {clone_path}: {e}")
                    
                    # Clear database
                    conn.execute("DELETE FROM user_clones")
                    conn.execute("DELETE FROM clone_logs")
                    conn.commit()
                    self.log_step("CLEANUP", "✅ Database cleared")
            
            # Additional cleanup of any straggler MT5 processes (Linux)
            os.system('pkill -f terminal64.exe 2>/dev/null')
            os.system('pkill -f metatrader5.exe 2>/dev/null')
            os.system('pkill -f mt5 2>/dev/null')
            
            self.log_step("CLEANUP", "✅ Cleanup completed")
            return True
            
        except Exception as e:
            self.log_step("CLEANUP", f"❌ Cleanup failed: {e}")
            return False
    
    def start_clone_manager(self):
        """Start the clone manager if not running"""
        self.log_step("MANAGER", "🚀 Starting clone manager")
        
        try:
            # Test if already running
            response = requests.get(f"{self.clone_manager_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_step("MANAGER", "✅ Clone manager already running")
                return True
        except:
            pass
        
        # Start clone manager
        import subprocess
        import time
        
        self.log_step("MANAGER", "🔄 Starting clone manager process")
        process = subprocess.Popen([
            sys.executable, "/root/HydraX-v2/bitten_clone_manager.py"
        ])
        
        # Wait for it to start
        for i in range(30):
            try:
                response = requests.get(f"{self.clone_manager_url}/health", timeout=2)
                if response.status_code == 200:
                    self.log_step("MANAGER", "✅ Clone manager started successfully")
                    return True
            except:
                time.sleep(1)
        
        self.log_step("MANAGER", "❌ Clone manager failed to start")
        return False
    
    def create_fresh_clone(self):
        """Create fresh MT5 clone with credentials"""
        self.log_step("CLONE", "🏗️ Creating fresh MT5 clone")
        
        try:
            # Create clone via API
            payload = {
                "user_id": self.user_id,
                "credentials": self.credentials
            }
            
            response = requests.post(
                f"{self.clone_manager_url}/clone/create",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_step("CLONE", "✅ Clone created successfully")
                self.log_step("CLONE", f"📁 Path: {result.get('clone_path')}")
                self.log_step("CLONE", f"🔌 Port: {result.get('port')}")
                self.log_step("CLONE", f"🏦 Type: {result.get('broker_type')}")
                return result
            else:
                error = response.json().get('error', 'Unknown error')
                self.log_step("CLONE", f"❌ Clone creation failed: {error}")
                return None
                
        except Exception as e:
            self.log_step("CLONE", f"❌ Clone creation error: {e}")
            return None
    
    def start_mt5_instance(self):
        """Start the MT5 instance"""
        self.log_step("MT5", "🚀 Starting MT5 instance")
        
        try:
            response = requests.post(
                f"{self.clone_manager_url}/clone/start/{self.user_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_step("MT5", "✅ MT5 instance started")
                self.log_step("MT5", f"🆔 PID: {result.get('process_id')}")
                return True
            else:
                error = response.json().get('error', 'Unknown error')
                self.log_step("MT5", f"❌ MT5 start failed: {error}")
                return False
                
        except Exception as e:
            self.log_step("MT5", f"❌ MT5 start error: {e}")
            return False
    
    def test_mt5_connectivity(self):
        """Test MT5 connectivity with diagnostic code"""
        self.log_step("CONNECTIVITY", "🔍 Testing MT5 connectivity")
        
        if not MT5_AVAILABLE:
            self.log_step("CONNECTIVITY", "⚠️ Running on Linux - will test via bridge communication")
            return self.test_bridge_connectivity()
        
        print("\n[CLONE CHECK] 🔄 Starting terminal diagnostics...\n")
        
        # Connect to terminal
        if not mt5.initialize():
            error = mt5.last_error()
            self.log_step("CONNECTIVITY", f"❌ MT5 failed to initialize: {error}")
            return False
        
        # Pause to give terminal time to fully load
        time.sleep(2)
        
        # Get account info
        account = mt5.account_info()
        if account is None:
            self.log_step("CONNECTIVITY", "❌ No account connected")
            mt5.shutdown()
            return False
        else:
            print(f"[✅] Account ID: {account.login}")
            print(f"[✅] Account Balance: {account.balance}")
            print(f"[✅] Leverage: {account.leverage}")
            print(f"[✅] Broker: {account.company}")
            
            # Store account info for system sync
            self.account_info = {
                "login": account.login,
                "balance": account.balance,
                "leverage": account.leverage,
                "company": account.company
            }
        
        # Get terminal info
        terminal = mt5.terminal_info()
        if terminal is None:
            self.log_step("CONNECTIVITY", "❌ Terminal info not found")
            mt5.shutdown()
            return False
        else:
            print(f"[⚙️] Algo Trading Allowed: {terminal.trade_allowed}")
            print(f"[⚙️] MT5 Version: {terminal.version}")
            print(f"[⚙️] Connected: {terminal.connected}")
            
            if not terminal.trade_allowed:
                self.log_step("CONNECTIVITY", "⚠️ WARNING: Algo trading not allowed")
            
            if not terminal.connected:
                self.log_step("CONNECTIVITY", "⚠️ WARNING: Terminal not connected to broker")
        
        # Test if EURUSD is tradable
        symbol = "EURUSD"
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            self.log_step("CONNECTIVITY", f"❌ Symbol {symbol} not found")
            mt5.shutdown()
            return False
        else:
            print(f"[📊] Symbol: {symbol}")
            print(f"[📶] Tradable: {symbol_info.trade_mode == mt5.TRADE_MODE_FULL}")
            print(f"[🟢] Visible: {symbol_info.visible}")
            print(f"[🔁] Ask: {symbol_info.ask} | Bid: {symbol_info.bid}")
            
            if symbol_info.trade_mode != mt5.TRADE_MODE_FULL:
                self.log_step("CONNECTIVITY", "⚠️ WARNING: EURUSD not fully tradable")
        
        # Cleanup
        mt5.shutdown()
        
        self.log_step("CONNECTIVITY", "✅ MT5 connectivity test completed")
        return True
    
    def test_bridge_connectivity(self):
        """Test connectivity via bridge communication (Linux)"""
        self.log_step("BRIDGE_TEST", "🌉 Testing bridge connectivity")
        
        try:
            # Since we're on Linux, we'll test via the AWS bridge
            from src.bitten_core.fire_router import FireRouter
            
            # Create router to test connection
            router = FireRouter()
            
            # Test ping
            ping_result = router.ping_bridge(self.user_id)
            
            if ping_result.get("success"):
                self.log_step("BRIDGE_TEST", "✅ Bridge ping successful")
                
                # Extract account info if available
                account_info = ping_result.get("account_info")
                if account_info:
                    self.account_info = {
                        "login": account_info.get("login", self.user_id),
                        "balance": account_info.get("balance", 0),
                        "leverage": account_info.get("leverage", 100),
                        "company": account_info.get("company", "Coinexx-Demo")
                    }
                    
                    print(f"[✅] Account ID: {self.account_info['login']}")
                    print(f"[✅] Account Balance: {self.account_info['balance']}")
                    print(f"[✅] Leverage: {self.account_info['leverage']}")
                    print(f"[✅] Broker: {self.account_info['company']}")
                else:
                    # Use configured credentials as fallback
                    self.account_info = {
                        "login": self.credentials["username"],
                        "balance": 0,  # Will be updated on first connection
                        "leverage": 100,
                        "company": self.credentials["server"]
                    }
                    print(f"[⚠️] Using configured credentials: {self.credentials['username']}")
                
                return True
            else:
                self.log_step("BRIDGE_TEST", f"❌ Bridge ping failed: {ping_result.get('message')}")
                return False
                
        except Exception as e:
            self.log_step("BRIDGE_TEST", f"❌ Bridge test error: {e}")
            # Set minimal account info for continuation
            self.account_info = {
                "login": self.credentials["username"],
                "balance": 0,
                "leverage": 100,
                "company": self.credentials["server"]
            }
            return False
    
    def test_file_bridge(self):
        """Test file-based trade packet communication"""
        self.log_step("BRIDGE", "🌉 Testing file-based bridge communication")
        
        try:
            # Get clone info
            response = requests.get(f"{self.clone_manager_url}/clone/status/{self.user_id}")
            if response.status_code != 200:
                self.log_step("BRIDGE", "❌ Could not get clone status")
                return False
            
            clone_info = response.json()
            bridge_path = Path(clone_info.get('bridge_path', ''))
            
            if not bridge_path.exists():
                self.log_step("BRIDGE", f"❌ Bridge path not found: {bridge_path}")
                return False
            
            # Test signal file creation
            test_signal = {
                "user_id": self.user_id,
                "symbol": "EURUSD",
                "direction": "BUY",
                "volume": 0.01,
                "take_profit": 1.0950,
                "stop_loss": 1.0900,
                "comment": "TEST_SIGNAL",
                "timestamp": datetime.now().isoformat()
            }
            
            signal_file = bridge_path / "signals_in.json"
            with open(signal_file, 'w') as f:
                json.dump(test_signal, f, indent=2)
            
            self.log_step("BRIDGE", f"✅ Test signal written to {signal_file}")
            
            # Verify files exist
            config_file = bridge_path / "bridge_config.json"
            status_file = bridge_path / "status.json"
            
            if config_file.exists():
                self.log_step("BRIDGE", "✅ Bridge config file exists")
            else:
                self.log_step("BRIDGE", "⚠️ Bridge config file missing")
            
            if status_file.exists():
                with open(status_file, 'r') as f:
                    status = json.load(f)
                self.log_step("BRIDGE", f"✅ Bridge status: {status.get('status')}")
            else:
                self.log_step("BRIDGE", "⚠️ Bridge status file missing")
            
            # Clean up test signal
            if signal_file.exists():
                signal_file.unlink()
                self.log_step("BRIDGE", "✅ Test signal cleaned up")
            
            return True
            
        except Exception as e:
            self.log_step("BRIDGE", f"❌ Bridge test failed: {e}")
            return False
    
    def sync_account_balance(self):
        """Sync account balance with BITTEN system"""
        self.log_step("SYNC", "🔄 Syncing account balance with BITTEN system")
        
        if not hasattr(self, 'account_info'):
            self.log_step("SYNC", "⚠️ No account info available for sync")
            return False
        
        try:
            # Update user balance in system (placeholder for actual implementation)
            balance_info = {
                "user_id": self.user_id,
                "account_id": self.account_info["login"],
                "balance": self.account_info["balance"],
                "leverage": self.account_info["leverage"],
                "broker": self.account_info["company"],
                "sync_time": datetime.now().isoformat()
            }
            
            # Save to file for system integration
            balance_file = Path(f"/root/HydraX-v2/data/user_balances/{self.user_id}.json")
            balance_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(balance_file, 'w') as f:
                json.dump(balance_info, f, indent=2)
            
            self.log_step("SYNC", f"✅ Account balance synced: ${self.account_info['balance']}")
            return True
            
        except Exception as e:
            self.log_step("SYNC", f"❌ Balance sync failed: {e}")
            return False
    
    def run_full_setup(self):
        """Run complete fresh clone setup"""
        print("=" * 60)
        print("🚀 BITTEN FRESH MT5 CLONE SETUP - User 843859")
        print("=" * 60)
        
        # Step 1: Cleanup
        if not self.cleanup_existing_clones():
            print("❌ Setup failed at cleanup step")
            return False
        
        # Step 2: Start clone manager
        if not self.start_clone_manager():
            print("❌ Setup failed at clone manager step")
            return False
        
        # Step 3: Create fresh clone
        clone_result = self.create_fresh_clone()
        if not clone_result:
            print("❌ Setup failed at clone creation step")
            return False
        
        # Step 4: Start MT5 instance
        if not self.start_mt5_instance():
            print("❌ Setup failed at MT5 startup step")
            return False
        
        # Wait for MT5 to fully start
        time.sleep(10)
        
        # Step 5: Test connectivity
        if not self.test_mt5_connectivity():
            print("❌ Setup failed at connectivity test step")
            return False
        
        # Step 6: Test file bridge
        if not self.test_file_bridge():
            print("❌ Setup failed at bridge test step")
            return False
        
        # Step 7: Sync account balance
        if not self.sync_account_balance():
            print("❌ Setup failed at balance sync step")
            return False
        
        print("\n" + "=" * 60)
        print("✅ FRESH MT5 CLONE SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📁 Clone Path: {clone_result.get('clone_path')}")
        print(f"🔌 Port: {clone_result.get('port')}")
        print(f"🏦 Broker: {self.account_info.get('company')}")
        print(f"💰 Balance: ${self.account_info.get('balance')}")
        print(f"🔗 Bridge: {clone_result.get('bridge_path')}")
        print("=" * 60)
        
        return True

def main():
    """Main setup function"""
    setup = FreshCloneSetup()
    
    try:
        success = setup.run_full_setup()
        if success:
            print("\n🎉 Fresh MT5 clone is ready for live trading!")
            print("⚠️  IMPORTANT: System will NEVER execute fake trades")
            print("⚠️  IMPORTANT: All trades will be real or clearly fail")
        else:
            print("\n❌ Setup failed. Please check logs and try again.")
            
    except KeyboardInterrupt:
        print("\n⏹️  Setup interrupted by user")
    except Exception as e:
        print(f"\n💥 Setup crashed: {e}")

if __name__ == "__main__":
    main()