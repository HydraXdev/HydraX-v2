#!/usr/bin/env python3
"""
MT5 Server Validation Script
Validates MT5 server connections before enabling trades
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add paths for imports
sys.path.append('/root/HydraX-v2')
sys.path.append('/root/HydraX-v2/src')

# MT5 Integration
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("❌ WARNING: MetaTrader5 not available - install with: pip install MetaTrader5")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/mt5_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MT5ServerValidator:
    """Validates MT5 server connections and configuration"""
    
    def __init__(self):
        self.validation_results = {}
        self.load_configuration()
    
    def load_configuration(self):
        """Load MT5 configuration from environment variables"""
        self.config = {
            'login': int(os.getenv('MT5_LOGIN', '843859')),
            'password': os.getenv('MT5_PASSWORD', 'Ao4@brz64erHaG'),
            'server': os.getenv('MT5_SERVER', 'MetaQuotes-Demo'),
            'path': os.getenv('MT5_PATH', r'C:\Program Files\MetaTrader 5\terminal64.exe')
        }
        
        # Load broker pools
        self.broker_pools = {
            'press_pass': os.getenv('PRESS_PASS_BROKER_POOL', 'MetaQuotes-Demo').split(','),
            'demo': os.getenv('DEMO_BROKER_POOL', 'ICMarkets-Demo').split(','),
            'live': os.getenv('LIVE_BROKER_POOL', 'ICMarkets-Live').split(',')
        }
        
        print(f"🔧 [VALIDATOR] Configuration loaded:")
        print(f"📊 Current Server: {self.config['server']}")
        print(f"👤 Account: {self.config['login']}")
        print(f"🔄 Rotation Enabled: {os.getenv('BROKER_ROTATION_ENABLED', 'false')}")
    
    def validate_server_connection(self, server_name: str) -> Dict[str, Any]:
        """Validate connection to specific MT5 server"""
        if not MT5_AVAILABLE:
            return {
                'success': False,
                'server': server_name,
                'error': 'MT5 library not available',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            print(f"🔍 [VALIDATOR] Testing connection to: {server_name}")
            
            # Create test configuration
            test_config = self.config.copy()
            test_config['server'] = server_name
            
            # Attempt to initialize
            if not mt5.initialize(
                login=test_config['login'],
                password=test_config['password'],
                server=test_config['server'],
                path=test_config['path']
            ):
                error_info = mt5.last_error()
                mt5.shutdown()
                return {
                    'success': False,
                    'server': server_name,
                    'error': f'Initialization failed: {error_info}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get account info
            account_info = mt5.account_info()
            if not account_info:
                mt5.shutdown()
                return {
                    'success': False,
                    'server': server_name,
                    'error': 'No account info available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Test symbol availability
            test_symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
            available_symbols = []
            for symbol in test_symbols:
                if mt5.symbol_info(symbol):
                    available_symbols.append(symbol)
            
            mt5.shutdown()
            
            result = {
                'success': True,
                'server': server_name,
                'account_info': {
                    'company': account_info.company,
                    'server': account_info.server,
                    'login': account_info.login,
                    'balance': account_info.balance,
                    'equity': account_info.equity,
                    'currency': account_info.currency,
                    'leverage': account_info.leverage,
                    'trade_mode': account_info.trade_mode
                },
                'available_symbols': available_symbols,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ [VALIDATOR] {server_name} - Connection successful!")
            print(f"🏢 Broker: {account_info.company}")
            print(f"💰 Balance: {account_info.balance} {account_info.currency}")
            print(f"🎚️ Leverage: 1:{account_info.leverage}")
            print(f"📊 Symbols: {len(available_symbols)}/3 available")
            
            return result
            
        except Exception as e:
            try:
                mt5.shutdown()
            except:
                pass
            
            result = {
                'success': False,
                'server': server_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"❌ [VALIDATOR] {server_name} - Connection failed: {e}")
            return result
    
    def validate_all_servers(self) -> Dict[str, Any]:
        """Validate all configured servers"""
        print(f"🚀 [VALIDATOR] Starting comprehensive server validation...")
        
        all_results = {}
        
        # Validate current server
        current_server = self.config['server']
        print(f"\n📊 [VALIDATOR] Testing current server: {current_server}")
        all_results[current_server] = self.validate_server_connection(current_server)
        
        # Validate broker pools
        for pool_name, servers in self.broker_pools.items():
            print(f"\n🔄 [VALIDATOR] Testing {pool_name} pool:")
            pool_results = {}
            for server in servers:
                server = server.strip()
                if server != current_server:  # Skip if already tested
                    pool_results[server] = self.validate_server_connection(server)
            if pool_results:
                all_results[f"{pool_name}_pool"] = pool_results
        
        return all_results
    
    def generate_validation_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive validation report"""
        report = []
        report.append("=" * 80)
        report.append("MT5 SERVER VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Configuration: {self.config['server']} (Account: {self.config['login']})")
        report.append("")
        
        successful_servers = []
        failed_servers = []
        
        for server_name, result in results.items():
            if isinstance(result, dict) and 'success' in result:
                if result['success']:
                    successful_servers.append(server_name)
                    report.append(f"✅ {server_name}")
                    if 'account_info' in result:
                        info = result['account_info']
                        report.append(f"   🏢 Broker: {info['company']}")
                        report.append(f"   💰 Balance: {info['balance']} {info['currency']}")
                        report.append(f"   🎚️ Leverage: 1:{info['leverage']}")
                        report.append(f"   📊 Symbols: {len(result.get('available_symbols', []))} available")
                else:
                    failed_servers.append(server_name)
                    report.append(f"❌ {server_name}")
                    report.append(f"   Error: {result.get('error', 'Unknown error')}")
                report.append("")
        
        # Summary
        report.append("SUMMARY")
        report.append("-" * 40)
        report.append(f"✅ Successful: {len(successful_servers)}")
        report.append(f"❌ Failed: {len(failed_servers)}")
        report.append(f"🌐 Total Tested: {len(successful_servers) + len(failed_servers)}")
        report.append("")
        
        if successful_servers:
            report.append("✅ AVAILABLE SERVERS:")
            for server in successful_servers:
                report.append(f"   - {server}")
        
        if failed_servers:
            report.append("")
            report.append("❌ UNAVAILABLE SERVERS:")
            for server in failed_servers:
                report.append(f"   - {server}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_validation(self):
        """Run complete validation process"""
        print(f"🎯 [VALIDATOR] MT5 Server Validation Starting...")
        
        # Validate all servers
        results = self.validate_all_servers()
        
        # Generate report
        report = self.generate_validation_report(results)
        
        # Save results
        with open('/root/HydraX-v2/mt5_validation_results.json', 'w') as f:
            import json
            json.dump(results, f, indent=2)
        
        with open('/root/HydraX-v2/mt5_validation_report.txt', 'w') as f:
            f.write(report)
        
        print(report)
        print(f"📄 [VALIDATOR] Report saved to: mt5_validation_report.txt")
        print(f"📊 [VALIDATOR] Results saved to: mt5_validation_results.json")
        
        return results

def main():
    """Main validation entry point"""
    validator = MT5ServerValidator()
    results = validator.run_validation()
    
    # Check if current server is valid
    current_server = os.getenv('MT5_SERVER', 'MetaQuotes-Demo')
    if current_server in results and results[current_server].get('success'):
        print(f"✅ [VALIDATOR] Current server {current_server} is READY for trading!")
        return 0
    else:
        print(f"❌ [VALIDATOR] Current server {current_server} is NOT READY for trading!")
        return 1

if __name__ == "__main__":
    sys.exit(main())