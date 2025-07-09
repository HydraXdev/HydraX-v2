#!/usr/bin/env python3
"""
MT5 Farm Adapter - Connects to remote MT5 farm server
Replaces local file-based MT5 bridge with API calls
"""

import requests
import json
import time
from typing import Dict, Optional, List
from datetime import datetime

class MT5FarmAdapter:
    """Adapter for connecting to MT5 farm server"""
    
    def __init__(self, farm_url: str = "http://129.212.185.102:8001"):
        self.farm_url = farm_url
        self.timeout = 30
        
    def check_health(self) -> Dict:
        """Check health of MT5 farm"""
        try:
            response = requests.get(f"{self.farm_url}/health", timeout=5)
            return response.json()
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def execute_trade(self, trade_params: Dict) -> Dict:
        """Execute trade on MT5 farm"""
        try:
            # Prepare trade instruction
            instruction = {
                'action': 'OPEN_TRADE',
                'symbol': trade_params['symbol'],
                'direction': trade_params['direction'],
                'lot_size': trade_params.get('lot_size', 0.01),
                'stop_loss': trade_params.get('stop_loss', 0),
                'take_profit': trade_params.get('take_profit', 0),
                'comment': trade_params.get('comment', 'BITTEN'),
                'magic_number': trade_params.get('magic_number', 12345),
                'timestamp': int(time.time())
            }
            
            # Send to farm
            response = requests.post(
                f"{self.farm_url}/execute",
                json=instruction,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': result.get('success', False),
                    'broker': result.get('broker'),
                    'ticket': result.get('ticket'),
                    'message': result.get('message', 'Trade sent to farm')
                }
            else:
                return {
                    'success': False,
                    'error': f'Farm returned status {response.status_code}',
                    'details': response.text
                }
                
        except requests.Timeout:
            return {
                'success': False,
                'error': 'Farm request timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_status(self) -> Dict:
        """Get status of all MT5 brokers"""
        try:
            response = requests.get(f"{self.farm_url}/status", timeout=5)
            return response.json()
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def close_trade(self, ticket: int) -> Dict:
        """Close specific trade"""
        instruction = {
            'action': 'CLOSE_TRADE',
            'ticket': ticket,
            'timestamp': int(time.time())
        }
        
        try:
            response = requests.post(
                f"{self.farm_url}/execute",
                json=instruction,
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def modify_trade(self, ticket: int, stop_loss: float = None, take_profit: float = None) -> Dict:
        """Modify existing trade"""
        instruction = {
            'action': 'MODIFY_TRADE',
            'ticket': ticket,
            'timestamp': int(time.time())
        }
        
        if stop_loss is not None:
            instruction['stop_loss'] = stop_loss
        if take_profit is not None:
            instruction['take_profit'] = take_profit
            
        try:
            response = requests.post(
                f"{self.farm_url}/execute",
                json=instruction,
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Backward compatibility - replace MT5BridgeAdapter
MT5BridgeAdapter = MT5FarmAdapter

# Test the connection
if __name__ == "__main__":
    print("🧪 Testing MT5 Farm Connection...")
    
    adapter = MT5FarmAdapter()
    
    # Test health
    print("\n📊 Health Check:")
    health = adapter.check_health()
    print(json.dumps(health, indent=2))
    
    # Test status
    print("\n📊 Farm Status:")
    status = adapter.get_status()
    print(json.dumps(status, indent=2))
    
    # Test trade execution (dry run)
    print("\n🔫 Test Trade Execution:")
    test_trade = {
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'lot_size': 0.01,
        'stop_loss': 1.0800,
        'take_profit': 1.0900,
        'comment': 'BITTEN Test'
    }
    result = adapter.execute_trade(test_trade)
    print(json.dumps(result, indent=2))
    
    print("\n✅ MT5 Farm adapter ready!")