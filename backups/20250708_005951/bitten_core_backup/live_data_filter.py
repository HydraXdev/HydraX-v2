"""Live data filtering from MT5 farm"""

import requests
from typing import Dict, List

class LiveDataFilter:
    """Filter signals based on live MT5 data"""
    
    def __init__(self, farm_url: str = "http://129.212.185.102:8001"):
        self.farm_url = farm_url
    
    def get_live_positions(self) -> List[Dict]:
        """Get all active positions from farm"""
        try:
            response = requests.get(f"{self.farm_url}/positions")
            data = response.json()
            return data.get('positions', [])
        except:
            return []
    
    def get_live_account_data(self) -> Dict:
        """Get live account data from all brokers"""
        try:
            response = requests.get(f"{self.farm_url}/live_data")
            return response.json()
        except:
            return {}
    
    def should_take_signal(self, signal: Dict) -> bool:
        """Decide if signal should be taken based on live data"""
        positions = self.get_live_positions()
        
        # Check position limits
        if len(positions) >= 10:  # Max 10 concurrent
            return False
        
        # Check if already in this symbol
        symbol_positions = [p for p in positions if p.get('symbol') == signal['symbol']]
        if len(symbol_positions) >= 2:  # Max 2 per symbol
            return False
        
        # Check drawdown
        total_pnl = sum(p.get('profit', 0) for p in positions)
        if total_pnl < -500:  # $500 drawdown limit
            return False
        
        return True
    
    def get_optimal_broker(self) -> str:
        """Select best broker based on load"""
        live_data = self.get_live_account_data()
        
        # Find broker with least positions
        min_positions = float('inf')
        best_broker = 'broker1'
        
        for broker, data in live_data.get('brokers', {}).items():
            if data.get('connected'):
                positions = data.get('positions_count', 0)
                if positions < min_positions:
                    min_positions = positions
                    best_broker = broker
        
        return best_broker
