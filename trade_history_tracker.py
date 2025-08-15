#!/usr/bin/env python3
"""
Trade History Tracker - Real-time tracking of all user trades
Shows open positions, closed trades, P&L, and outcome tracking
Similar to MetaTrader mobile app functionality
"""

import json
import sqlite3
import redis
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class TradeHistoryTracker:
    def __init__(self):
        self.db_path = "/root/HydraX-v2/bitten.db"
        self.redis_client = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
        
    def get_user_positions(self, user_id: str) -> Dict:
        """Get all positions for a user - open, closed, and pending"""
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get all fires (executed trades)
        fires = cur.execute("""
            SELECT f.*, m.payload_json, s.outcome, s.pips, s.resolved_at
            FROM fires f
            LEFT JOIN missions m ON f.mission_id = m.mission_id
            LEFT JOIN signal_outcomes s ON f.mission_id = s.signal_id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
            LIMIT 100
        """, (user_id,)).fetchall()
        
        # Parse into position data
        positions = {
            'open': [],
            'closed': [],
            'pending': []
        }
        
        for fire in fires:
            # Parse mission payload for trade details
            payload = {}
            if fire['payload_json']:
                try:
                    payload = json.loads(fire['payload_json'])
                except:
                    pass
            
            # Build position object
            position = {
                'fire_id': fire['fire_id'],
                'mission_id': fire['mission_id'],
                'symbol': payload.get('symbol', 'UNKNOWN'),
                'direction': payload.get('direction', 'UNKNOWN'),
                'entry_price': payload.get('entry_price', 0),
                'sl': payload.get('sl', 0),
                'tp': payload.get('tp', 0),
                'lot_size': payload.get('lot_size', 0.01),
                'ticket': fire['ticket'],
                'execution_price': fire['price'],
                'status': fire['status'],
                'created_at': fire['created_at'],
                'outcome': fire['outcome'] if 'outcome' in fire.keys() else None,
                'pips_result': fire['pips'] if 'pips' in fire.keys() else None,
                'closed_at': fire['resolved_at'] if 'resolved_at' in fire.keys() else None,
                'risk_used': fire['risk_pct_used'],
                'equity_used': fire['equity_used']
            }
            
            # Calculate current P&L if position is open
            if fire['status'] == 'FILLED' and not position['outcome']:
                # Get current price from Redis if available
                current_price = self._get_current_price(position['symbol'])
                if current_price:
                    position['current_price'] = current_price
                    position['current_pnl'] = self._calculate_pnl(position, current_price)
                    position['current_pips'] = self._calculate_pips(position, current_price)
                positions['open'].append(position)
            elif position['outcome'] in ['TP_HIT', 'SL_HIT', 'TIMEOUT']:
                # Closed position
                position['final_pnl'] = self._calculate_final_pnl(position)
                positions['closed'].append(position)
            else:
                # Pending or failed
                positions['pending'].append(position)
        
        conn.close()
        return positions
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from Redis tick stream"""
        try:
            # Try to get latest tick from Redis
            key = f"tick:{symbol}"
            tick_data = self.redis_client.get(key)
            if tick_data:
                tick = json.loads(tick_data)
                return (tick.get('bid', 0) + tick.get('ask', 0)) / 2
        except:
            pass
        return None
    
    def _calculate_pnl(self, position: Dict, current_price: float) -> float:
        """Calculate current P&L for open position"""
        if not position['entry_price'] or not current_price:
            return 0
            
        pip_size = self._get_pip_size(position['symbol'])
        
        if position['direction'] == 'BUY':
            pips = (current_price - position['entry_price']) / pip_size
        else:
            pips = (position['entry_price'] - current_price) / pip_size
            
        # Calculate dollar P&L based on lot size
        pip_value = self._get_pip_value(position['symbol'], position['lot_size'])
        return pips * pip_value
    
    def _calculate_pips(self, position: Dict, current_price: float) -> float:
        """Calculate current pips for open position"""
        if not position['entry_price'] or not current_price:
            return 0
            
        pip_size = self._get_pip_size(position['symbol'])
        
        if position['direction'] == 'BUY':
            return (current_price - position['entry_price']) / pip_size
        else:
            return (position['entry_price'] - current_price) / pip_size
    
    def _calculate_final_pnl(self, position: Dict) -> float:
        """Calculate final P&L for closed position"""
        if not position['pips_result']:
            return 0
            
        pip_value = self._get_pip_value(position['symbol'], position['lot_size'])
        return position['pips_result'] * pip_value
    
    def _get_pip_size(self, symbol: str) -> float:
        """Get pip size for symbol"""
        s = symbol.upper()
        if s.endswith("JPY"):
            return 0.01
        elif s.startswith("XAU"):
            return 0.1
        elif s.startswith("XAG"):
            return 0.01
        else:
            return 0.0001
    
    def _get_pip_value(self, symbol: str, lot_size: float) -> float:
        """Get pip value in USD for position"""
        # Standard pip values for 1 lot
        if symbol.endswith("JPY"):
            pip_value_per_lot = 1000 / 147  # Approximate USD/JPY rate
        elif symbol.startswith("XAU"):
            pip_value_per_lot = 10
        else:
            pip_value_per_lot = 10  # Standard forex
            
        return pip_value_per_lot * lot_size
    
    def get_user_statistics(self, user_id: str) -> Dict:
        """Get comprehensive trading statistics for user"""
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get all completed trades with outcomes
        completed = cur.execute("""
            SELECT f.*, s.outcome, s.pips
            FROM fires f
            LEFT JOIN signal_outcomes s ON f.mission_id = s.signal_id
            WHERE f.user_id = ? AND f.status = 'FILLED' AND s.outcome IS NOT NULL
            ORDER BY f.created_at DESC
        """, (user_id,)).fetchall()
        
        # Calculate statistics
        total_trades = len(completed)
        wins = sum(1 for t in completed if t['outcome'] == 'TP_HIT')
        losses = sum(1 for t in completed if t['outcome'] == 'SL_HIT')
        
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate total P&L
        total_pips = sum(t['pips'] or 0 for t in completed)
        
        # Get current streak
        streak = 0
        if completed:
            for trade in completed:
                if trade['outcome'] == 'TP_HIT':
                    streak += 1
                else:
                    break
        
        # Get best day
        best_day_pips = 0
        if completed:
            from collections import defaultdict
            daily_pips = defaultdict(float)
            for trade in completed:
                if trade['created_at']:
                    day = datetime.fromtimestamp(trade['created_at']).date()
                    daily_pips[day] += trade['pips'] or 0
            if daily_pips:
                best_day_pips = max(daily_pips.values())
        
        conn.close()
        
        return {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_pips': total_pips,
            'current_streak': streak,
            'best_day_pips': best_day_pips,
            'avg_win': (total_pips / wins) if wins > 0 else 0,
            'avg_loss': (total_pips / losses) if losses > 0 else 0
        }
    
    def format_positions_for_display(self, positions: Dict) -> str:
        """Format positions for telegram or web display"""
        output = []
        
        # Open positions
        if positions['open']:
            output.append("📊 **OPEN POSITIONS**")
            for pos in positions['open']:
                pnl_emoji = "🟢" if pos.get('current_pnl', 0) > 0 else "🔴"
                output.append(f"""
{pnl_emoji} **{pos['symbol']}** {pos['direction']}
• Entry: {pos['entry_price']:.5f}
• Current: {pos.get('current_price', 0):.5f}
• P&L: {pos.get('current_pips', 0):.1f} pips (${pos.get('current_pnl', 0):.2f})
• SL: {pos['sl']:.5f} | TP: {pos['tp']:.5f}
• Ticket: #{pos['ticket']}
""")
        
        # Recent closed
        if positions['closed'][:5]:  # Show last 5
            output.append("\n📈 **RECENT CLOSED**")
            for pos in positions['closed'][:5]:
                outcome_emoji = "✅" if pos['outcome'] == 'TP_HIT' else "❌"
                output.append(f"""
{outcome_emoji} **{pos['symbol']}** {pos['direction']} - {pos['outcome']}
• Result: {pos.get('pips_result', 0):.1f} pips (${pos.get('final_pnl', 0):.2f})
• Closed: {datetime.fromtimestamp(pos['closed_at']).strftime('%Y-%m-%d %H:%M') if pos['closed_at'] else 'Unknown'}
""")
        
        return "\n".join(output)

# API endpoint functions for webapp integration
def get_user_trade_data(user_id: str) -> Dict:
    """Get complete trade data for user - for API endpoint"""
    tracker = TradeHistoryTracker()
    
    positions = tracker.get_user_positions(user_id)
    stats = tracker.get_user_statistics(user_id)
    
    return {
        'positions': positions,
        'statistics': stats,
        'last_updated': datetime.now().isoformat()
    }

def format_for_telegram(user_id: str) -> str:
    """Format trade data for Telegram display"""
    tracker = TradeHistoryTracker()
    
    positions = tracker.get_user_positions(user_id)
    stats = tracker.get_user_statistics(user_id)
    
    output = [
        "📊 **YOUR TRADING DASHBOARD**\n",
        f"Win Rate: {stats['win_rate']:.1f}%",
        f"Total P&L: {stats['total_pips']:.1f} pips",
        f"Current Streak: {stats['current_streak']} wins",
        f"Total Trades: {stats['total_trades']}",
        "",
        tracker.format_positions_for_display(positions)
    ]
    
    return "\n".join(output)

if __name__ == "__main__":
    # Test with commander user
    user_id = "7176191872"
    print(format_for_telegram(user_id))