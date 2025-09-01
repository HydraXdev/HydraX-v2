#!/usr/bin/env python3
"""
POSITION TRACKER v1.0
Track positions by player UUID, enforce slot limits, monitor P&L

Author: BITTEN Trading System
Date: August 6, 2025
Purpose: Real-time position tracking with slot management and risk control
"""

import redis
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - POSITION_TRACKER - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/position_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Position data structure"""
    uuid: str
    ticket: str
    account: str
    symbol: str
    direction: str  # 'buy' or 'sell'
    lot_size: float
    open_price: float
    open_time: float
    sl: float
    tp: float
    magic_number: int
    status: str  # 'open', 'closed', 'partial'
    node_id: str
    signal_id: str = None
    close_price: float = None
    close_time: float = None
    profit: float = None
    swap: float = None
    commission: float = None
    current_pnl: float = None
    max_profit: float = None
    max_loss: float = None
    duration: float = None

class PositionTracker:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.running = True
        
        # User tier configurations (slots allowed)
        self.tier_slots = {
            'RECRUIT': 1,
            'SOLDIER': 1, 
            'CORPORAL': 2,
            'SERGEANT': 2,
            'LIEUTENANT': 3,
            'CAPTAIN': 3,
            'MAJOR': 4,
            'COLONEL': 5,
            'GENERAL': 10,
            'COMMANDER': 15
        }
        
        # Risk limits per position (as percentage of balance)
        self.max_risk_per_position = {
            'RECRUIT': 0.02,    # 2%
            'SOLDIER': 0.025,   # 2.5%
            'CORPORAL': 0.03,   # 3%
            'SERGEANT': 0.035,  # 3.5%
            'LIEUTENANT': 0.04, # 4%
            'CAPTAIN': 0.045,   # 4.5%
            'MAJOR': 0.05,      # 5%
            'COLONEL': 0.055,   # 5.5%
            'GENERAL': 0.06,    # 6%
            'COMMANDER': 0.10   # 10%
        }
        
        # Test Redis connection
        try:
            self.redis_client.ping()
            logger.info("✅ Connected to Redis server")
        except redis.ConnectionError:
            logger.error("❌ Failed to connect to Redis server")
            raise
        
        logger.info("📊 Position Tracker v1.0 initialized")

    def get_user_slots(self, uuid: str) -> int:
        """Get maximum slots allowed for user"""
        try:
            # Get user tier from user registry
            user_data = self.redis_client.hgetall(f"user:{uuid}")
            if not user_data:
                # Default to RECRUIT if user not found
                return self.tier_slots.get('RECRUIT', 1)
            
            tier = user_data.get('tier', 'RECRUIT')
            return self.tier_slots.get(tier, 1)
        
        except Exception as e:
            logger.error(f"Error getting user slots for {uuid}: {str(e)}")
            return 1  # Safe default

    def get_max_risk_per_position(self, uuid: str) -> float:
        """Get maximum risk per position for user tier"""
        try:
            user_data = self.redis_client.hgetall(f"user:{uuid}")
            tier = user_data.get('tier', 'RECRUIT') if user_data else 'RECRUIT'
            return self.max_risk_per_position.get(tier, 0.02)
        
        except Exception as e:
            logger.error(f"Error getting max risk for {uuid}: {str(e)}")
            return 0.02  # Safe default

    def calculate_position_risk(self, entry_price: float, sl_price: float, lot_size: float, symbol: str, balance: float) -> Dict:
        """Calculate position risk metrics"""
        try:
            # Calculate pip value and risk
            pip_size = 0.0001 if 'JPY' not in symbol else 0.01
            pip_difference = abs(entry_price - sl_price) / pip_size
            
            # Estimate pip value (simplified - would need proper calculation per symbol)
            pip_value = lot_size * 10 if 'JPY' not in symbol else lot_size * 1000
            
            risk_amount = pip_difference * pip_value
            risk_percentage = (risk_amount / balance) * 100 if balance > 0 else 100
            
            return {
                'risk_amount': round(risk_amount, 2),
                'risk_percentage': round(risk_percentage, 3),
                'pip_risk': round(pip_difference, 1),
                'pip_value': round(pip_value, 2)
            }
        
        except Exception as e:
            logger.error(f"Error calculating position risk: {str(e)}")
            return {'risk_amount': 0, 'risk_percentage': 0, 'pip_risk': 0, 'pip_value': 0}

    def open_position(self, uuid: str, trade_data: Dict) -> Dict:
        """Open a new position with slot and risk validation"""
        try:
            # Validate required fields
            required_fields = ['ticket', 'symbol', 'direction', 'lot_size', 'open_price']
            for field in required_fields:
                if field not in trade_data:
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # Check slot availability
            current_positions = self.get_open_positions(uuid)
            max_slots = self.get_user_slots(uuid)
            
            if len(current_positions) >= max_slots:
                return {
                    'success': False, 
                    'error': f'No slots available. Used: {len(current_positions)}/{max_slots}',
                    'current_slots': len(current_positions),
                    'max_slots': max_slots
                }
            
            # Get account balance for risk calculation
            account = trade_data.get('account', 'UNKNOWN')
            account_balance = float(trade_data.get('balance', 10000))  # Default if not provided
            
            # Calculate position risk
            entry_price = float(trade_data['open_price'])
            sl_price = float(trade_data.get('sl', entry_price))
            lot_size = float(trade_data['lot_size'])
            symbol = trade_data['symbol']
            
            if sl_price != entry_price:  # Only check risk if SL is set
                risk_metrics = self.calculate_position_risk(entry_price, sl_price, lot_size, symbol, account_balance)
                max_risk = self.get_max_risk_per_position(uuid)
                
                if risk_metrics['risk_percentage'] > max_risk * 100:
                    return {
                        'success': False,
                        'error': f'Position risk {risk_metrics["risk_percentage"]:.2f}% exceeds limit {max_risk*100:.2f}%',
                        'risk_metrics': risk_metrics
                    }
            else:
                risk_metrics = {'risk_amount': 0, 'risk_percentage': 0, 'pip_risk': 0}
            
            # Create position object
            position = Position(
                uuid=uuid,
                ticket=str(trade_data['ticket']),
                account=account,
                symbol=symbol,
                direction=trade_data['direction'].lower(),
                lot_size=lot_size,
                open_price=entry_price,
                open_time=time.time(),
                sl=sl_price,
                tp=float(trade_data.get('tp', 0)),
                magic_number=int(trade_data.get('magic_number', 0)),
                status='open',
                node_id=trade_data.get('node_id', 'UNKNOWN'),
                signal_id=trade_data.get('signal_id', ''),
                current_pnl=0.0,
                max_profit=0.0,
                max_loss=0.0
            )
            
            # Store position in Redis
            self._store_position(position)
            
            # Add to user's position list
            self.redis_client.sadd(f"user_positions:{uuid}", position.ticket)
            
            # Add to global open positions
            self.redis_client.sadd("all_open_positions", position.ticket)
            
            # Update user statistics
            self._update_user_stats(uuid, 'position_opened', {
                'symbol': symbol,
                'lot_size': lot_size,
                'risk_amount': risk_metrics['risk_amount']
            })
            
            logger.info(f"📈 Position opened: {position.ticket} ({symbol}) - {uuid} - Risk: {risk_metrics['risk_percentage']:.2f}%")
            
            return {
                'success': True,
                'position': asdict(position),
                'risk_metrics': risk_metrics,
                'slots_used': len(current_positions) + 1,
                'max_slots': max_slots
            }
            
        except Exception as e:
            logger.error(f"❌ Error opening position: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _store_position(self, position: Position):
        """Store position in Redis"""
        position_data = asdict(position)
        
        # Convert floats to strings for Redis
        for key, value in position_data.items():
            if isinstance(value, (float, int)) and value is not None:
                position_data[key] = str(value)
            elif value is None:
                position_data[key] = ""
        
        # Store position
        self.redis_client.hset(f"position:{position.ticket}", mapping=position_data)
        self.redis_client.expire(f"position:{position.ticket}", 86400 * 30)  # 30 days

    def close_position(self, ticket: str, close_data: Dict) -> Dict:
        """Close a position and update statistics"""
        try:
            # Get existing position
            position_data = self.redis_client.hgetall(f"position:{ticket}")
            
            if not position_data:
                return {'success': False, 'error': f'Position {ticket} not found'}
            
            if position_data.get('status') != 'open':
                return {'success': False, 'error': f'Position {ticket} is not open'}
            
            # Update position with close data
            close_updates = {
                'close_price': str(close_data.get('close_price', 0)),
                'close_time': str(time.time()),
                'profit': str(close_data.get('profit', 0)),
                'swap': str(close_data.get('swap', 0)),
                'commission': str(close_data.get('commission', 0)),
                'status': 'closed'
            }
            
            # Calculate duration
            open_time = float(position_data.get('open_time', time.time()))
            duration = time.time() - open_time
            close_updates['duration'] = str(duration)
            
            # Update position in Redis
            self.redis_client.hset(f"position:{ticket}", mapping=close_updates)
            
            # Remove from open positions
            uuid = position_data.get('uuid')
            self.redis_client.srem(f"user_positions:{uuid}", ticket)
            self.redis_client.srem("all_open_positions", ticket)
            
            # Add to closed positions history
            self.redis_client.lpush(f"user_closed_positions:{uuid}", ticket)
            self.redis_client.ltrim(f"user_closed_positions:{uuid}", 0, 999)  # Keep last 1000
            
            # Update user statistics
            profit = float(close_data.get('profit', 0))
            self._update_user_stats(uuid, 'position_closed', {
                'symbol': position_data.get('symbol'),
                'profit': profit,
                'duration': duration,
                'result': 'win' if profit > 0 else 'loss'
            })
            
            # Calculate final P&L metrics
            final_position = self.redis_client.hgetall(f"position:{ticket}")
            
            logger.info(f"📉 Position closed: {ticket} - Profit: ${profit:+.2f} - Duration: {duration/60:.1f}min")
            
            return {
                'success': True,
                'position': final_position,
                'profit': profit,
                'duration': duration
            }
            
        except Exception as e:
            logger.error(f"❌ Error closing position {ticket}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def update_position_pnl(self, ticket: str, current_price: float, pnl: float):
        """Update position's current P&L"""
        try:
            position_data = self.redis_client.hgetall(f"position:{ticket}")
            
            if not position_data or position_data.get('status') != 'open':
                return False
            
            # Update current P&L and track max profit/loss
            max_profit = float(position_data.get('max_profit', 0))
            max_loss = float(position_data.get('max_loss', 0))
            
            updates = {
                'current_pnl': str(pnl),
                'last_updated': str(time.time())
            }
            
            # Track maximum profit and loss during position lifetime
            if pnl > max_profit:
                updates['max_profit'] = str(pnl)
            
            if pnl < max_loss:
                updates['max_loss'] = str(pnl)
            
            self.redis_client.hset(f"position:{ticket}", mapping=updates)
            return True
            
        except Exception as e:
            logger.error(f"Error updating position P&L for {ticket}: {str(e)}")
            return False

    def get_open_positions(self, uuid: str) -> List[Dict]:
        """Get all open positions for a user"""
        try:
            position_tickets = self.redis_client.smembers(f"user_positions:{uuid}")
            positions = []
            
            for ticket in position_tickets:
                position_data = self.redis_client.hgetall(f"position:{ticket}")
                if position_data and position_data.get('status') == 'open':
                    # Convert string values back to appropriate types
                    position_data = self._convert_position_types(position_data)
                    positions.append(position_data)
                else:
                    # Clean up stale reference
                    self.redis_client.srem(f"user_positions:{uuid}", ticket)
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting open positions for {uuid}: {str(e)}")
            return []

    def get_position_history(self, uuid: str, limit: int = 50) -> List[Dict]:
        """Get closed position history for a user"""
        try:
            closed_tickets = self.redis_client.lrange(f"user_closed_positions:{uuid}", 0, limit - 1)
            positions = []
            
            for ticket in closed_tickets:
                position_data = self.redis_client.hgetall(f"position:{ticket}")
                if position_data:
                    position_data = self._convert_position_types(position_data)
                    positions.append(position_data)
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting position history for {uuid}: {str(e)}")
            return []

    def _convert_position_types(self, position_data: Dict) -> Dict:
        """Convert Redis string values back to appropriate Python types"""
        converted = dict(position_data)
        
        # Float fields
        float_fields = ['lot_size', 'open_price', 'close_price', 'sl', 'tp', 'profit', 
                       'swap', 'commission', 'current_pnl', 'max_profit', 'max_loss', 
                       'open_time', 'close_time', 'duration']
        
        for field in float_fields:
            if field in converted and converted[field]:
                try:
                    converted[field] = float(converted[field])
                except (ValueError, TypeError):
                    converted[field] = None
        
        # Integer fields
        int_fields = ['magic_number']
        
        for field in int_fields:
            if field in converted and converted[field]:
                try:
                    converted[field] = int(converted[field])
                except (ValueError, TypeError):
                    converted[field] = None
        
        return converted

    def get_position_stats(self, uuid: str) -> Dict:
        """Get comprehensive position statistics for a user"""
        try:
            open_positions = self.get_open_positions(uuid)
            closed_positions = self.get_position_history(uuid, 1000)  # Get more for accurate stats
            
            # Basic counts
            stats = {
                'open_positions': len(open_positions),
                'max_slots': self.get_user_slots(uuid),
                'slots_available': self.get_user_slots(uuid) - len(open_positions),
                'total_closed_positions': len(closed_positions)
            }
            
            # Current exposure
            total_lot_size = sum(pos.get('lot_size', 0) for pos in open_positions)
            total_current_pnl = sum(pos.get('current_pnl', 0) for pos in open_positions)
            total_risk_amount = sum(self.calculate_position_risk(
                pos.get('open_price', 0),
                pos.get('sl', pos.get('open_price', 0)),
                pos.get('lot_size', 0),
                pos.get('symbol', ''),
                10000  # Default balance for calculation
            ).get('risk_amount', 0) for pos in open_positions)
            
            stats.update({
                'total_lot_size': round(total_lot_size, 2),
                'current_unrealized_pnl': round(total_current_pnl, 2),
                'total_risk_amount': round(total_risk_amount, 2)
            })
            
            # Historical performance
            if closed_positions:
                profits = [pos.get('profit', 0) for pos in closed_positions if pos.get('profit')]
                wins = [p for p in profits if p > 0]
                losses = [p for p in profits if p < 0]
                
                stats.update({
                    'total_trades': len(profits),
                    'winning_trades': len(wins),
                    'losing_trades': len(losses),
                    'win_rate': round((len(wins) / len(profits)) * 100, 2) if profits else 0,
                    'total_profit': round(sum(wins), 2),
                    'total_loss': round(abs(sum(losses)), 2),
                    'net_profit': round(sum(profits), 2),
                    'average_win': round(sum(wins) / len(wins), 2) if wins else 0,
                    'average_loss': round(abs(sum(losses)) / len(losses), 2) if losses else 0,
                    'largest_win': round(max(wins), 2) if wins else 0,
                    'largest_loss': round(abs(min(losses)), 2) if losses else 0,
                    'profit_factor': round(sum(wins) / abs(sum(losses)), 2) if losses else float('inf')
                })
                
                # Average trade duration
                durations = [pos.get('duration', 0) for pos in closed_positions if pos.get('duration')]
                stats['avg_trade_duration_minutes'] = round(sum(durations) / len(durations) / 60, 1) if durations else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting position stats for {uuid}: {str(e)}")
            return {'error': str(e)}

    def _update_user_stats(self, uuid: str, event_type: str, event_data: Dict):
        """Update user statistics in Redis"""
        try:
            stats_key = f"user_position_stats:{uuid}"
            timestamp = time.time()
            
            # Update based on event type
            if event_type == 'position_opened':
                self.redis_client.hincrby(stats_key, 'positions_opened', 1)
                self.redis_client.hincrbyfloat(stats_key, 'total_risk', event_data.get('risk_amount', 0))
                
            elif event_type == 'position_closed':
                self.redis_client.hincrby(stats_key, 'positions_closed', 1)
                self.redis_client.hincrbyfloat(stats_key, 'total_realized_pnl', event_data.get('profit', 0))
                
                if event_data.get('result') == 'win':
                    self.redis_client.hincrby(stats_key, 'winning_positions', 1)
                else:
                    self.redis_client.hincrby(stats_key, 'losing_positions', 1)
            
            # Update last activity timestamp
            self.redis_client.hset(stats_key, 'last_activity', str(timestamp))
            self.redis_client.expire(stats_key, 86400 * 90)  # Keep for 90 days
            
        except Exception as e:
            logger.error(f"Error updating user stats: {str(e)}")

    def get_global_position_stats(self) -> Dict:
        """Get system-wide position statistics"""
        try:
            all_open_tickets = self.redis_client.smembers("all_open_positions")
            
            stats = {
                'total_open_positions': len(all_open_tickets),
                'active_users_with_positions': 0,
                'total_exposure': 0,
                'symbols_traded': set(),
                'by_symbol': {},
                'risk_distribution': {'low': 0, 'medium': 0, 'high': 0}
            }
            
            user_positions = defaultdict(int)
            
            for ticket in all_open_tickets:
                position_data = self.redis_client.hgetall(f"position:{ticket}")
                if position_data:
                    uuid = position_data.get('uuid')
                    symbol = position_data.get('symbol', 'UNKNOWN')
                    lot_size = float(position_data.get('lot_size', 0))
                    
                    user_positions[uuid] += 1
                    stats['total_exposure'] += lot_size
                    stats['symbols_traded'].add(symbol)
                    
                    # Symbol breakdown
                    if symbol not in stats['by_symbol']:
                        stats['by_symbol'][symbol] = {'positions': 0, 'total_lots': 0}
                    stats['by_symbol'][symbol]['positions'] += 1
                    stats['by_symbol'][symbol]['total_lots'] += lot_size
            
            stats['active_users_with_positions'] = len(user_positions)
            stats['symbols_traded'] = len(stats['symbols_traded'])
            stats['total_exposure'] = round(stats['total_exposure'], 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting global position stats: {str(e)}")
            return {'error': str(e)}

    def force_close_position(self, ticket: str, reason: str = 'force_close') -> Dict:
        """Force close a position (admin function)"""
        try:
            position_data = self.redis_client.hgetall(f"position:{ticket}")
            
            if not position_data:
                return {'success': False, 'error': 'Position not found'}
            
            # Close with estimated data
            close_data = {
                'close_price': position_data.get('open_price', 0),  # Use open price as fallback
                'profit': 0,  # Assume break-even
                'swap': 0,
                'commission': 0,
                'reason': reason
            }
            
            result = self.close_position(ticket, close_data)
            
            if result['success']:
                logger.warning(f"⚠️ Position force-closed: {ticket} - Reason: {reason}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error force closing position {ticket}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def cleanup_stale_positions(self):
        """Clean up stale or orphaned positions"""
        try:
            all_open_tickets = list(self.redis_client.smembers("all_open_positions"))
            cleaned_count = 0
            
            for ticket in all_open_tickets:
                position_data = self.redis_client.hgetall(f"position:{ticket}")
                
                if not position_data:
                    # Position data missing, remove from open set
                    self.redis_client.srem("all_open_positions", ticket)
                    cleaned_count += 1
                    continue
                
                # Check if position is really old (>7 days)
                open_time = float(position_data.get('open_time', time.time()))
                if time.time() - open_time > (7 * 24 * 3600):
                    logger.warning(f"⚠️ Found very old position: {ticket} (opened {(time.time() - open_time)/86400:.1f} days ago)")
            
            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned up {cleaned_count} stale positions")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up stale positions: {str(e)}")
            return 0

    def monitor_positions(self):
        """Background position monitoring"""
        while self.running:
            try:
                # Clean up stale positions
                self.cleanup_stale_positions()
                
                # Report global stats
                global_stats = self.get_global_position_stats()
                logger.info(f"📊 Position Status: {global_stats.get('total_open_positions', 0)} open positions, "
                          f"{global_stats.get('active_users_with_positions', 0)} active users, "
                          f"{global_stats.get('total_exposure', 0):.2f} total lots")
                
                time.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in position monitoring: {str(e)}")
                time.sleep(300)

    def start_monitoring(self):
        """Start background position monitoring"""
        logger.info("🔄 Starting position tracker monitoring...")
        monitor_thread = threading.Thread(target=self.monitor_positions, daemon=True)
        monitor_thread.start()
        return monitor_thread

    def shutdown(self):
        """Gracefully shutdown the tracker"""
        logger.info("🛑 Shutting down position tracker...")
        self.running = False

# API wrapper for easy integration
class PositionTrackerAPI:
    def __init__(self):
        self.tracker = PositionTracker()
        self.tracker.start_monitoring()
    
    def open(self, uuid: str, trade_data: Dict) -> Dict:
        return self.tracker.open_position(uuid, trade_data)
    
    def close(self, ticket: str, close_data: Dict) -> Dict:
        return self.tracker.close_position(ticket, close_data)
    
    def get_open(self, uuid: str) -> List[Dict]:
        return self.tracker.get_open_positions(uuid)
    
    def get_stats(self, uuid: str) -> Dict:
        return self.tracker.get_position_stats(uuid)
    
    def update_pnl(self, ticket: str, current_price: float, pnl: float) -> bool:
        return self.tracker.update_position_pnl(ticket, current_price, pnl)

if __name__ == "__main__":
    # Example usage and testing
    tracker = PositionTracker()
    monitor_thread = tracker.start_monitoring()
    
    try:
        logger.info("📊 Position Tracker running... Press Ctrl+C to stop")
        while True:
            time.sleep(30)
            
            # Display system status every 30 seconds
            global_stats = tracker.get_global_position_stats()
            if global_stats.get('total_open_positions', 0) > 0:
                logger.info(f"Global: {global_stats['total_open_positions']} positions, "
                          f"{global_stats['total_exposure']:.2f} lots")
    
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        tracker.shutdown()