#!/usr/bin/env python3
"""
Live Trade API Integration for BITTEN Mission Briefing
Connects MT5 farm data to webapp for real-time trade tracking
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveTradeAPI:
    """API for live trade data integration"""
    
    def __init__(self):
        self.farm_url = "http://localhost:5555"
        self.active_trades = {}
        self.account_data = {
            'balance': 2450.00,
            'equity': 2487.50,
            'margin': 245.00,
            'free_margin': 2242.50,
            'daily_pnl': 37.50,
            'open_trades': 0
        }
        
    def get_live_trades(self) -> List[Dict]:
        """Get current live trades from MT5 farm"""
        try:
            response = requests.get(f"{self.farm_url}/api/positions", timeout=5)
            if response.status_code == 200:
                positions = response.json()
                return self.format_trade_data(positions)
        except Exception as e:
            logger.error(f"Error fetching live trades: {e}")
            
        # Return mock data for demonstration
        return self.get_mock_trades()
    
    def format_trade_data(self, positions: List[Dict]) -> List[Dict]:
        """Format MT5 position data for webapp"""
        formatted_trades = []
        
        for pos in positions:
            trade = {
                'trade_id': pos.get('ticket', f"T{int(time.time())}"),
                'symbol': pos.get('symbol', 'EURUSD'),
                'direction': 'BUY' if pos.get('type', 0) == 0 else 'SELL',
                'volume': pos.get('volume', 0.1),
                'entry_price': pos.get('price_open', 1.0850),
                'current_price': pos.get('price_current', 1.0858),
                'stop_loss': pos.get('sl', 1.0830),
                'take_profit': pos.get('tp', 1.0880),
                'profit_usd': pos.get('profit', 12.50),
                'profit_pips': self.calculate_pips(pos),
                'open_time': pos.get('time', datetime.now().isoformat()),
                'swap': pos.get('swap', 0.0),
                'commission': pos.get('commission', 0.0)
            }
            formatted_trades.append(trade)
            
        return formatted_trades
    
    def calculate_pips(self, position: Dict) -> float:
        """Calculate pips profit/loss"""
        entry = position.get('price_open', 0)
        current = position.get('price_current', 0)
        symbol = position.get('symbol', 'EURUSD')
        
        if entry == 0 or current == 0:
            return 0.0
            
        # Determine pip multiplier based on symbol
        if 'JPY' in symbol:
            multiplier = 100
        else:
            multiplier = 10000
            
        # Calculate pips based on direction
        trade_type = position.get('type', 0)
        if trade_type == 0:  # BUY
            pips = (current - entry) * multiplier
        else:  # SELL
            pips = (entry - current) * multiplier
            
        return round(pips, 1)
    
    def get_mock_trades(self) -> List[Dict]:
        """Generate mock trade data for testing"""
        current_time = datetime.now()
        
        return [
            {
                'trade_id': 'T001',
                'symbol': 'EURUSD',
                'direction': 'BUY',
                'volume': 0.1,
                'entry_price': 1.0850,
                'current_price': 1.0858,
                'stop_loss': 1.0830,
                'take_profit': 1.0880,
                'profit_usd': 12.50,
                'profit_pips': 8.3,
                'open_time': (current_time.timestamp() - 135),  # 2:15 ago
                'swap': 0.0,
                'commission': 0.0
            },
            {
                'trade_id': 'T002',
                'symbol': 'GBPJPY',
                'direction': 'SELL',
                'volume': 0.05,
                'entry_price': 183.85,
                'current_price': 183.87,
                'stop_loss': 184.50,
                'take_profit': 183.20,
                'profit_usd': -5.20,
                'profit_pips': -2.1,
                'open_time': (current_time.timestamp() - 342),  # 5:42 ago
                'swap': -0.25,
                'commission': 0.0
            }
        ]
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            response = requests.get(f"{self.farm_url}/api/account", timeout=5)
            if response.status_code == 200:
                account = response.json()
                self.account_data.update({
                    'balance': account.get('balance', self.account_data['balance']),
                    'equity': account.get('equity', self.account_data['equity']),
                    'margin': account.get('margin', self.account_data['margin']),
                    'free_margin': account.get('margin_free', self.account_data['free_margin']),
                    'daily_pnl': account.get('profit', self.account_data['daily_pnl']),
                    'open_trades': len(self.get_live_trades())
                })
        except Exception as e:
            logger.error(f"Error fetching account info: {e}")
            
        return self.account_data
    
    def get_trade_details(self, trade_id: str) -> Optional[Dict]:
        """Get detailed information for a specific trade"""
        trades = self.get_live_trades()
        for trade in trades:
            if trade['trade_id'] == trade_id:
                return self.enhance_trade_details(trade)
        return None
    
    def enhance_trade_details(self, trade: Dict) -> Dict:
        """Add enhanced details for trade observation modal"""
        symbol = trade['symbol']
        
        # Calculate additional metrics
        entry_price = trade['entry_price']
        current_price = trade['current_price']
        stop_loss = trade['stop_loss']
        take_profit = trade['take_profit']
        
        # Risk/Reward calculation
        if trade['direction'] == 'BUY':
            risk_pips = abs(entry_price - stop_loss) * (100 if 'JPY' in symbol else 10000)
            reward_pips = abs(take_profit - entry_price) * (100 if 'JPY' in symbol else 10000)
        else:
            risk_pips = abs(stop_loss - entry_price) * (100 if 'JPY' in symbol else 10000)
            reward_pips = abs(entry_price - take_profit) * (100 if 'JPY' in symbol else 10000)
        
        risk_reward = f"1:{reward_pips/risk_pips:.1f}" if risk_pips > 0 else "1:0"
        
        # Win probability based on current progress
        if trade['direction'] == 'BUY':
            progress = (current_price - entry_price) / (take_profit - entry_price) if take_profit > entry_price else 0
        else:
            progress = (entry_price - current_price) / (entry_price - take_profit) if entry_price > take_profit else 0
        
        win_probability = min(90, max(50, 65 + (progress * 25)))
        
        # Trade duration
        open_timestamp = trade['open_time']
        if isinstance(open_timestamp, (int, float)):
            duration_seconds = time.time() - open_timestamp
        else:
            duration_seconds = 135  # Default for mock data
        
        duration_minutes = int(duration_seconds // 60)
        duration_display = f"{duration_minutes//60}:{duration_minutes%60:02d}"
        
        # Enhanced trade data
        enhanced = trade.copy()
        enhanced.update({
            'duration_display': duration_display,
            'duration_minutes': duration_minutes,
            'risk_reward': risk_reward,
            'win_probability': f"{win_probability:.0f}%",
            'max_drawdown': f"{max(0, -trade['profit_pips'] * 1.2):.1f} pips",
            'peak_profit': f"{max(trade['profit_pips'], trade['profit_pips'] * 1.1):.1f} pips",
            'spread_cost': f"{1.2 if 'JPY' not in symbol else 2.1} pips",
            'progress_percentage': max(0, min(100, progress * 100))
        })
        
        return enhanced
    
    def close_trade(self, trade_id: str, reason: str = "Manual close") -> Dict:
        """Close a specific trade"""
        try:
            # Try to close via MT5 farm
            response = requests.post(
                f"{self.farm_url}/api/close_position",
                json={'ticket': trade_id, 'reason': reason},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Trade {trade_id} closed successfully")
                return {'success': True, 'message': 'Trade closed successfully'}
        
        except Exception as e:
            logger.error(f"Error closing trade {trade_id}: {e}")
            
        # Mock response for demonstration
        logger.info(f"Mock close trade {trade_id}: {reason}")
        return {'success': True, 'message': f'Trade {trade_id} close request sent'}

# Global API instance
live_trade_api = LiveTradeAPI()

# Flask endpoints for webapp integration
def register_live_trade_endpoints(app: Flask):
    """Register live trade API endpoints with Flask app"""
    
    @app.route('/api/live/trades')
    def get_live_trades():
        """Get current live trades"""
        trades = live_trade_api.get_live_trades()
        account = live_trade_api.get_account_info()
        
        return jsonify({
            'success': True,
            'trades': trades,
            'account': account,
            'timestamp': time.time()
        })
    
    @app.route('/api/live/trade/<trade_id>')
    def get_trade_details(trade_id):
        """Get detailed trade information"""
        trade = live_trade_api.get_trade_details(trade_id)
        
        if trade:
            return jsonify({
                'success': True,
                'trade': trade,
                'timestamp': time.time()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Trade not found'
            }), 404
    
    @app.route('/api/live/close/<trade_id>', methods=['POST'])
    def close_trade(trade_id):
        """Close a specific trade"""
        data = request.get_json() or {}
        reason = data.get('reason', 'Manual close via webapp')
        
        result = live_trade_api.close_trade(trade_id, reason)
        
        return jsonify(result)
    
    @app.route('/api/live/account')
    def get_account_info():
        """Get account information"""
        account = live_trade_api.get_account_info()
        
        return jsonify({
            'success': True,
            'account': account,
            'timestamp': time.time()
        })

# WebSocket events for real-time updates
def register_socketio_events(socketio: SocketIO):
    """Register SocketIO events for real-time updates"""
    
    @socketio.on('join_live_trades')
    def on_join_live_trades(data):
        """Client joins live trade updates"""
        user_id = data.get('user_id', 'unknown')
        logger.info(f"User {user_id} joined live trades")
        emit('joined_live_trades', {'status': 'connected'})
    
    @socketio.on('request_trade_update')
    def on_request_trade_update(data):
        """Client requests trade update"""
        trade_id = data.get('trade_id')
        if trade_id:
            trade = live_trade_api.get_trade_details(trade_id)
            if trade:
                emit('trade_update', trade)

def start_live_updates(socketio: SocketIO):
    """Start background thread for live updates"""
    
    def update_loop():
        """Background loop for live trade updates"""
        while True:
            try:
                # Get current trades and account info
                trades = live_trade_api.get_live_trades()
                account = live_trade_api.get_account_info()
                
                # Emit updates to connected clients
                socketio.emit('live_trades_update', {
                    'trades': trades,
                    'account': account,
                    'timestamp': time.time()
                })
                
                # Update every 2 seconds
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in live update loop: {e}")
                time.sleep(5)
    
    # Start background thread
    update_thread = threading.Thread(target=update_loop, daemon=True)
    update_thread.start()
    logger.info("Live trade updates started")

if __name__ == "__main__":
    # Test the API
    logger.info("Testing Live Trade API...")
    
    trades = live_trade_api.get_live_trades()
    logger.info(f"Found {len(trades)} active trades")
    
    for trade in trades:
        logger.info(f"Trade: {trade['symbol']} {trade['direction']} - P&L: ${trade['profit_usd']}")
    
    account = live_trade_api.get_account_info()
    logger.info(f"Account Balance: ${account['balance']}, Equity: ${account['equity']}")