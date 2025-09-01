#!/usr/bin/env python3
"""
Direction Gate - Server-side position management
Prevents opposite positions on same symbol without EA changes
"""

import asyncio
import sqlite3
import json
import time
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DirectionGate')

class Direction(Enum):
    BUY = "BUY"
    SELL = "SELL"

class GateAction(Enum):
    OPEN = "OPEN"           # Allow normal open
    REDUCE = "REDUCE"       # Partial close only
    FLIP = "FLIP"          # Close all then open
    BLOCK = "BLOCK"        # Reject the trade

class DirectionGate:
    """
    Server-side gate to prevent opposite positions
    Tracks net exposure per symbol and enforces direction rules
    """
    
    def __init__(self, db_path='/root/HydraX-v2/bitten.db'):
        self.db_path = db_path
        
        # Configuration - Anti-hedging protection enabled
        self.ALLOW_OPPOSITE = False      # Block opposite direction trades (anti-hedging)
        self.AUTO_CLOSE_OPPOSITE = False # Block instead of auto-close (not implemented)
        self.REDUCE_ONLY = False         # Only allow reducing exposure
        
        # Per-symbol locks to prevent race conditions
        self.symbol_locks = {}
        
        # Position state cache
        self.position_cache = {}  # symbol -> {net_lots, tickets, direction}
        self.last_refresh = 0
        
        # Initialize position state from database
        self.refresh_positions()
    
    def refresh_positions(self):
        """Refresh position state from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get only CURRENTLY OPEN positions from live_positions table
            # This ensures we only track actual open positions, not historical trades
            # Ignore STALE and CLOSED positions
            cursor.execute("""
                SELECT 
                    fire_id,
                    symbol,
                    direction,
                    lot_size,
                    last_update
                FROM live_positions
                WHERE status = 'OPEN'
                AND user_id = '7176191872'
                ORDER BY last_update ASC
            """)
            
            # Build position cache
            positions = {}
            for row in cursor.fetchall():
                fire_id, symbol, direction, lot_size, last_update = row
                
                # Use actual lot size from the position
                volume = lot_size if lot_size else 0.01
                
                if symbol not in positions:
                    positions[symbol] = {
                        'net_lots': 0.0,
                        'tickets': [],
                        'direction': None
                    }
                
                # Track cumulative net position to prevent hedging
                # Add/subtract volume based on direction
                if direction == 'BUY':
                    positions[symbol]['net_lots'] += volume
                    positions[symbol]['direction'] = Direction.BUY if positions[symbol]['net_lots'] > 0 else Direction.SELL
                else:
                    positions[symbol]['net_lots'] -= volume
                    positions[symbol]['direction'] = Direction.SELL if positions[symbol]['net_lots'] < 0 else Direction.BUY
                positions[symbol]['last_trade_time'] = last_update
                
                # Track positions for FIFO closing
                positions[symbol]['tickets'].append({
                    'fire_id': fire_id,
                    'volume': volume,
                    'direction': direction,
                    'last_update': last_update
                })
            
            conn.close()
            
            self.position_cache = positions
            self.last_refresh = time.time()
            
            # Log position summary
            for symbol, data in positions.items():
                net = data['net_lots']
                if net != 0:
                    side = "LONG" if net > 0 else "SHORT"
                    logger.info(f"{symbol}: {side} {abs(net):.2f} lots ({len(data['tickets'])} tickets)")
            
            return positions
            
        except Exception as e:
            logger.error(f"Error refreshing positions: {e}")
            return {}
    
    def get_net_position(self, symbol: str) -> Tuple[float, Optional[Direction]]:
        """Get net position for a symbol"""
        # Refresh if stale (>5 seconds old)
        if time.time() - self.last_refresh > 5:
            self.refresh_positions()
        
        if symbol not in self.position_cache:
            return 0.0, None
        
        data = self.position_cache[symbol]
        net = data['net_lots']
        
        if net > 0:
            return net, Direction.BUY
        elif net < 0:
            return abs(net), Direction.SELL
        else:
            return 0.0, None
    
    def check_direction(self, symbol: str, direction: Direction, lots: float) -> Tuple[GateAction, Dict]:
        """
        Check if trade direction is allowed
        Returns: (action, details)
        """
        net_lots, current_direction = self.get_net_position(symbol)
        
        # If flat, always allow
        if net_lots == 0:
            return GateAction.OPEN, {'reason': 'flat position'}
        
        # Same direction, always allow
        if current_direction == direction:
            return GateAction.OPEN, {'reason': 'same direction'}
        
        # Opposite direction - ALWAYS block for anti-hedging
        if not self.ALLOW_OPPOSITE:
            # Log detailed blocking info for debugging
            logger.warning(f"🚫 BLOCKING HEDGE: {symbol} trying to {direction.value} with existing {current_direction.value} position of {net_lots:.2f} lots")
            
            if self.REDUCE_ONLY:
                # Only allow reducing exposure
                reduce_lots = min(net_lots, lots)
                return GateAction.REDUCE, {
                    'reason': 'reduce only mode',
                    'reduce_lots': reduce_lots,
                    'current_net': net_lots
                }
            
            elif self.AUTO_CLOSE_OPPOSITE:
                # Close all opposite positions first
                tickets_to_close = []
                if symbol in self.position_cache:
                    tickets_to_close = [
                        t['ticket'] for t in self.position_cache[symbol]['tickets']
                    ]
                
                return GateAction.FLIP, {
                    'reason': 'auto close opposite',
                    'tickets_to_close': tickets_to_close,
                    'current_net': net_lots,
                    'current_direction': current_direction.value
                }
            
            else:
                # Block the trade
                return GateAction.BLOCK, {
                    'reason': 'opposite direction blocked',
                    'current_net': net_lots,
                    'current_direction': current_direction.value
                }
        
        # If ALLOW_OPPOSITE is True
        return GateAction.OPEN, {'reason': 'opposite allowed'}
    
    async def acquire_symbol_lock(self, symbol: str):
        """Acquire lock for symbol to prevent race conditions"""
        if symbol not in self.symbol_locks:
            self.symbol_locks[symbol] = asyncio.Lock()
        
        await self.symbol_locks[symbol].acquire()
    
    def release_symbol_lock(self, symbol: str):
        """Release symbol lock"""
        if symbol in self.symbol_locks:
            self.symbol_locks[symbol].release()
    
    def get_close_commands(self, symbol: str) -> List[Dict]:
        """Get close commands for all positions on symbol (FIFO order)"""
        commands = []
        
        if symbol not in self.position_cache:
            return commands
        
        # FIFO - oldest first
        tickets = sorted(
            self.position_cache[symbol]['tickets'],
            key=lambda x: x['created_at']
        )
        
        for ticket_data in tickets:
            commands.append({
                'type': 'close',
                'ticket': ticket_data['ticket'],
                'fire_id': ticket_data['fire_id'],
                'symbol': symbol,
                'volume': ticket_data['volume']
            })
        
        return commands
    
    def update_position_closed(self, symbol: str, ticket: int):
        """Update cache when position is closed"""
        if symbol in self.position_cache:
            # Remove ticket from cache
            self.position_cache[symbol]['tickets'] = [
                t for t in self.position_cache[symbol]['tickets']
                if t['ticket'] != ticket
            ]
            
            # Recalculate net position
            net = 0.0
            for t in self.position_cache[symbol]['tickets']:
                if t['direction'] == 'BUY':
                    net += t['volume']
                else:
                    net -= t['volume']
            
            self.position_cache[symbol]['net_lots'] = net
            
            if net == 0:
                self.position_cache[symbol]['direction'] = None
    
    def get_summary(self) -> Dict:
        """Get summary of all positions"""
        summary = {}
        
        for symbol, data in self.position_cache.items():
            if data['net_lots'] != 0:
                summary[symbol] = {
                    'net_lots': data['net_lots'],
                    'direction': 'LONG' if data['net_lots'] > 0 else 'SHORT',
                    'ticket_count': len(data['tickets'])
                }
        
        return summary


# Singleton instance
_gate_instance = None

def get_direction_gate() -> DirectionGate:
    """Get singleton instance of direction gate"""
    global _gate_instance
    if _gate_instance is None:
        _gate_instance = DirectionGate()
    return _gate_instance


# Integration hook for fire pipeline
def check_fire_direction(symbol: str, direction: str, lots: float) -> Tuple[str, Dict]:
    """
    Check if a fire command should be allowed
    Returns: (action, details)
    
    Actions:
    - "OPEN": Proceed with normal open
    - "FLIP": Close opposite positions first, then open
    - "REDUCE": Only close partial position
    - "BLOCK": Reject the trade
    """
    gate = get_direction_gate()
    
    # Convert string direction to enum
    dir_enum = Direction.BUY if direction.upper() == 'BUY' else Direction.SELL
    
    # Check direction gate
    action, details = gate.check_direction(symbol, dir_enum, lots)
    
    # Log decision
    logger.info(f"Direction gate for {symbol} {direction} {lots}: {action.value} - {details}")
    
    return action.value, details


if __name__ == "__main__":
    # Test the direction gate
    gate = DirectionGate()
    
    print("\n=== Direction Gate Status ===")
    print(f"ALLOW_OPPOSITE: {gate.ALLOW_OPPOSITE}")
    print(f"AUTO_CLOSE_OPPOSITE: {gate.AUTO_CLOSE_OPPOSITE}")
    print(f"REDUCE_ONLY: {gate.REDUCE_ONLY}")
    
    print("\n=== Current Positions ===")
    summary = gate.get_summary()
    if summary:
        for symbol, data in summary.items():
            print(f"{symbol}: {data['direction']} {abs(data['net_lots']):.2f} lots ({data['ticket_count']} tickets)")
    else:
        print("No open positions")
    
    # Test check
    print("\n=== Test Checks ===")
    test_cases = [
        ("EURUSD", "BUY", 0.1),
        ("GBPUSD", "SELL", 0.1),
    ]
    
    for symbol, direction, lots in test_cases:
        action, details = check_fire_direction(symbol, direction, lots)
        print(f"{symbol} {direction} {lots}: {action} - {details.get('reason')}")