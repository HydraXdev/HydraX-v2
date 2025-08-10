#!/usr/bin/env python3
"""
CONFIRMATION LOGGER v1.0
Captures and processes trade confirmations from MT5 EA

Author: BITTEN Trading System
Date: August 6, 2025
Purpose: Log all trade confirmations, track win rates, and maintain position history
"""

import zmq
import json
import time
import logging
import redis
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CONFIRMATION - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/confirmation_logger.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConfirmationLogger:
    def __init__(self):
        self.context = zmq.Context()
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # PULL socket binding to port 5558 for trade confirmations
        self.socket = self.context.socket(zmq.PULL)
        self.socket.bind("tcp://*:5558")
        
        # Statistics tracking
        self.trade_stats = defaultdict(dict)
        self.running = True
        
        # Initialize Redis keys for statistics
        self._init_redis_stats()
        
        logger.info("📝 Confirmation Logger v1.0 initialized on port 5558")

    def _init_redis_stats(self):
        """Initialize Redis statistics if they don't exist"""
        try:
            # Global statistics
            if not self.redis_client.exists("global_trade_stats"):
                self.redis_client.hset("global_trade_stats", mapping={
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'total_profit': 0,
                    'total_loss': 0,
                    'largest_win': 0,
                    'largest_loss': 0,
                    'last_updated': time.time()
                })
        
        except Exception as e:
            logger.error(f"Error initializing Redis stats: {str(e)}")

    def process_confirmation(self, confirmation: Dict):
        """Process incoming trade confirmation"""
        try:
            # Validate required fields
            required_fields = ['ticket', 'symbol', 'result']
            for field in required_fields:
                if field not in confirmation:
                    logger.warning(f"⚠️ Missing required field '{field}' in confirmation: {confirmation}")
                    return

            ticket = str(confirmation['ticket'])
            symbol = confirmation['symbol']
            result = confirmation['result']
            timestamp = confirmation.get('timestamp', time.time())
            
            # Enhanced confirmation data
            enhanced_confirmation = {
                'ticket': ticket,
                'symbol': symbol,
                'result': result,
                'timestamp': timestamp,
                'processed_at': time.time(),
                'account': confirmation.get('account', 'UNKNOWN'),
                'magic_number': confirmation.get('magic_number', 0),
                'order_type': confirmation.get('type', 'UNKNOWN'),
                'volume': float(confirmation.get('volume', 0)),
                'open_price': float(confirmation.get('open_price', 0)),
                'close_price': float(confirmation.get('close_price', 0)),
                'profit': float(confirmation.get('profit', 0)),
                'swap': float(confirmation.get('swap', 0)),
                'commission': float(confirmation.get('commission', 0)),
                'sl': float(confirmation.get('sl', 0)),
                'tp': float(confirmation.get('tp', 0)),
                'open_time': confirmation.get('open_time', timestamp),
                'close_time': confirmation.get('close_time', timestamp),
                'comment': confirmation.get('comment', ''),
                'node_id': confirmation.get('node_id', 'UNKNOWN')
            }
            
            # Log to file (JSONL format for easy parsing)
            with open('/root/HydraX-v2/logs/trade_confirmations.jsonl', 'a') as f:
                f.write(json.dumps(enhanced_confirmation) + '\n')
            
            # Store in Redis with expiry
            self.store_in_redis(enhanced_confirmation)
            
            # Update statistics
            self.update_statistics(enhanced_confirmation)
            
            # Track position lifecycle
            self.track_position_lifecycle(enhanced_confirmation)
            
            logger.info(f"📋 Trade confirmation processed: {ticket} ({symbol}) - {result}")
            
            if result == 'success' and enhanced_confirmation['profit'] != 0:
                profit = enhanced_confirmation['profit']
                status = "WIN" if profit > 0 else "LOSS"
                logger.info(f"💰 Trade {ticket}: {status} ${profit:+.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error processing confirmation: {str(e)}")
            logger.error(f"Confirmation data: {json.dumps(confirmation, indent=2)}")

    def store_in_redis(self, confirmation: Dict):
        """Store trade confirmation in Redis"""
        try:
            ticket = confirmation['ticket']
            symbol = confirmation['symbol']
            
            # Store individual trade record
            trade_key = f"trade:{ticket}"
            self.redis_client.hset(trade_key, mapping=confirmation)
            self.redis_client.expire(trade_key, 86400 * 30)  # Keep for 30 days
            
            # Add to symbol-specific trade list
            symbol_key = f"trades:{symbol}"
            self.redis_client.lpush(symbol_key, ticket)
            self.redis_client.ltrim(symbol_key, 0, 999)  # Keep last 1000 trades per symbol
            self.redis_client.expire(symbol_key, 86400 * 7)  # Keep for 7 days
            
            # Add to account-specific trade list
            account = confirmation['account']
            account_key = f"account_trades:{account}"
            self.redis_client.lpush(account_key, ticket)
            self.redis_client.ltrim(account_key, 0, 999)  # Keep last 1000 trades per account
            self.redis_client.expire(account_key, 86400 * 30)  # Keep for 30 days
            
            # Add to daily trade list
            today = datetime.now().strftime('%Y-%m-%d')
            daily_key = f"daily_trades:{today}"
            self.redis_client.lpush(daily_key, ticket)
            self.redis_client.expire(daily_key, 86400 * 7)  # Keep for 7 days
            
        except Exception as e:
            logger.error(f"Error storing confirmation in Redis: {str(e)}")

    def update_statistics(self, confirmation: Dict):
        """Update win/loss statistics"""
        try:
            result = confirmation['result']
            symbol = confirmation['symbol']
            account = confirmation['account']
            profit = float(confirmation['profit'])
            
            # Global statistics
            self.redis_client.hincrby("global_trade_stats", "total_trades", 1)
            
            if result == 'success' and profit != 0:
                if profit > 0:
                    # Winning trade
                    self.redis_client.hincrby("global_trade_stats", "winning_trades", 1)
                    self.redis_client.hincrbyfloat("global_trade_stats", "total_profit", profit)
                    
                    current_largest_win = float(self.redis_client.hget("global_trade_stats", "largest_win") or 0)
                    if profit > current_largest_win:
                        self.redis_client.hset("global_trade_stats", "largest_win", profit)
                else:
                    # Losing trade
                    self.redis_client.hincrby("global_trade_stats", "losing_trades", 1)
                    self.redis_client.hincrbyfloat("global_trade_stats", "total_loss", abs(profit))
                    
                    current_largest_loss = float(self.redis_client.hget("global_trade_stats", "largest_loss") or 0)
                    if abs(profit) > current_largest_loss:
                        self.redis_client.hset("global_trade_stats", "largest_loss", abs(profit))
            
            # Symbol-specific statistics
            symbol_stats_key = f"symbol_stats:{symbol}"
            self.redis_client.hincrby(symbol_stats_key, "total_trades", 1)
            
            if result == 'success' and profit != 0:
                if profit > 0:
                    self.redis_client.hincrby(symbol_stats_key, "wins", 1)
                    self.redis_client.hincrbyfloat(symbol_stats_key, "total_profit", profit)
                else:
                    self.redis_client.hincrby(symbol_stats_key, "losses", 1)
                    self.redis_client.hincrbyfloat(symbol_stats_key, "total_loss", abs(profit))
            
            self.redis_client.expire(symbol_stats_key, 86400 * 30)
            
            # Account-specific statistics
            account_stats_key = f"account_stats_trades:{account}"
            self.redis_client.hincrby(account_stats_key, "total_trades", 1)
            
            if result == 'success' and profit != 0:
                if profit > 0:
                    self.redis_client.hincrby(account_stats_key, "wins", 1)
                    self.redis_client.hincrbyfloat(account_stats_key, "profit", profit)
                else:
                    self.redis_client.hincrby(account_stats_key, "losses", 1)
                    self.redis_client.hincrbyfloat(account_stats_key, "loss", abs(profit))
                
                # Update running balance
                self.redis_client.hincrbyfloat(account_stats_key, "running_pnl", profit)
            
            self.redis_client.expire(account_stats_key, 86400 * 30)
            
            # Update timestamp
            self.redis_client.hset("global_trade_stats", "last_updated", time.time())
            
        except Exception as e:
            logger.error(f"Error updating statistics: {str(e)}")

    def track_position_lifecycle(self, confirmation: Dict):
        """Track the full lifecycle of positions"""
        try:
            ticket = confirmation['ticket']
            result = confirmation['result']
            
            if result == 'order_opened':
                # Position opened
                position_data = {
                    'ticket': ticket,
                    'symbol': confirmation['symbol'],
                    'account': confirmation['account'],
                    'volume': confirmation['volume'],
                    'open_price': confirmation['open_price'],
                    'open_time': confirmation['timestamp'],
                    'sl': confirmation['sl'],
                    'tp': confirmation['tp'],
                    'type': confirmation['order_type'],
                    'status': 'open',
                    'magic_number': confirmation['magic_number']
                }
                
                self.redis_client.hset(f"position:{ticket}", mapping=position_data)
                self.redis_client.sadd("open_positions", ticket)
                self.redis_client.expire(f"position:{ticket}", 86400 * 7)
                
                logger.info(f"📈 Position opened: {ticket} ({confirmation['symbol']}) - {confirmation['volume']} lots")
            
            elif result == 'order_closed' or result == 'success':
                # Position closed
                if self.redis_client.sismember("open_positions", ticket):
                    # Update position with close data
                    close_updates = {
                        'close_price': confirmation['close_price'],
                        'close_time': confirmation['timestamp'],
                        'profit': confirmation['profit'],
                        'swap': confirmation['swap'],
                        'commission': confirmation['commission'],
                        'status': 'closed'
                    }
                    
                    self.redis_client.hset(f"position:{ticket}", mapping=close_updates)
                    self.redis_client.srem("open_positions", ticket)
                    
                    # Calculate trade duration
                    position = self.redis_client.hgetall(f"position:{ticket}")
                    if position and 'open_time' in position:
                        duration = float(confirmation['timestamp']) - float(position['open_time'])
                        self.redis_client.hset(f"position:{ticket}", "duration", duration)
                    
                    logger.info(f"📉 Position closed: {ticket} - Profit: ${float(confirmation['profit']):+.2f}")
            
        except Exception as e:
            logger.error(f"Error tracking position lifecycle: {str(e)}")

    def calculate_win_rate(self, symbol: Optional[str] = None, account: Optional[str] = None) -> Dict:
        """Calculate win rate statistics"""
        try:
            if symbol:
                stats_key = f"symbol_stats:{symbol}"
                scope = f"symbol {symbol}"
            elif account:
                stats_key = f"account_stats_trades:{account}"
                scope = f"account {account}"
            else:
                stats_key = "global_trade_stats"
                scope = "global"
            
            stats = self.redis_client.hgetall(stats_key)
            
            if not stats:
                return {'error': f'No statistics found for {scope}'}
            
            total_trades = int(stats.get('total_trades', 0))
            winning_trades = int(stats.get('winning_trades', 0)) + int(stats.get('wins', 0))
            losing_trades = int(stats.get('losing_trades', 0)) + int(stats.get('losses', 0))
            
            if total_trades == 0:
                return {'error': f'No trades recorded for {scope}'}
            
            win_rate = (winning_trades / total_trades) * 100
            loss_rate = (losing_trades / total_trades) * 100
            
            total_profit = float(stats.get('total_profit', 0)) + float(stats.get('profit', 0))
            total_loss = float(stats.get('total_loss', 0)) + float(stats.get('loss', 0))
            
            net_profit = total_profit - total_loss
            
            return {
                'scope': scope,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'loss_rate': round(loss_rate, 2),
                'total_profit': round(total_profit, 2),
                'total_loss': round(total_loss, 2),
                'net_profit': round(net_profit, 2),
                'average_win': round(total_profit / winning_trades, 2) if winning_trades > 0 else 0,
                'average_loss': round(total_loss / losing_trades, 2) if losing_trades > 0 else 0,
                'profit_factor': round(total_profit / total_loss, 2) if total_loss > 0 else float('inf'),
                'last_updated': stats.get('last_updated', time.time())
            }
            
        except Exception as e:
            logger.error(f"Error calculating win rate: {str(e)}")
            return {'error': str(e)}

    def get_recent_trades(self, limit: int = 10, symbol: Optional[str] = None) -> List[Dict]:
        """Get recent trade confirmations"""
        try:
            if symbol:
                trade_tickets = self.redis_client.lrange(f"trades:{symbol}", 0, limit - 1)
            else:
                # Get from all recent trades
                today = datetime.now().strftime('%Y-%m-%d')
                trade_tickets = self.redis_client.lrange(f"daily_trades:{today}", 0, limit - 1)
            
            trades = []
            for ticket in trade_tickets:
                trade_data = self.redis_client.hgetall(f"trade:{ticket}")
                if trade_data:
                    trades.append(trade_data)
            
            return trades
            
        except Exception as e:
            logger.error(f"Error getting recent trades: {str(e)}")
            return []

    def get_open_positions(self) -> List[Dict]:
        """Get currently open positions"""
        try:
            open_tickets = self.redis_client.smembers("open_positions")
            positions = []
            
            for ticket in open_tickets:
                position_data = self.redis_client.hgetall(f"position:{ticket}")
                if position_data:
                    # Calculate current P&L if we have market data
                    positions.append(position_data)
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting open positions: {str(e)}")
            return []

    def cleanup_old_data(self):
        """Clean up old trade data periodically"""
        while self.running:
            try:
                # Clean trades older than 30 days
                cutoff_time = time.time() - (30 * 24 * 3600)
                
                # This is a simplified cleanup - in production, implement proper cleanup
                logger.debug("🧹 Running trade data cleanup")
                
                time.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Error in cleanup: {str(e)}")
                time.sleep(3600)

    def status_reporter(self):
        """Report confirmation logger status periodically"""
        while self.running:
            try:
                global_stats = self.redis_client.hgetall("global_trade_stats")
                open_positions = len(self.redis_client.smembers("open_positions"))
                
                total_trades = int(global_stats.get('total_trades', 0))
                wins = int(global_stats.get('winning_trades', 0))
                losses = int(global_stats.get('losing_trades', 0))
                
                win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
                
                logger.info(f"📊 Confirmation Status: {total_trades} total trades, "
                          f"{win_rate:.1f}% win rate, {open_positions} open positions")
                
                time.sleep(300)  # Report every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in status reporter: {str(e)}")
                time.sleep(300)

    def run(self):
        """Main confirmation processing loop"""
        logger.info("🔄 Starting confirmation processing loop...")
        
        while self.running:
            try:
                # Poll for messages with timeout
                if self.socket.poll(1000):  # 1 second timeout
                    message_raw = self.socket.recv_string(zmq.NOBLOCK)
                    
                    try:
                        confirmation = json.loads(message_raw)
                        self.process_confirmation(confirmation)
                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ Invalid JSON received: {message_raw[:100]}...")
                        continue
                        
            except zmq.Again:
                continue
            except KeyboardInterrupt:
                logger.info("🛑 Confirmation logger interrupted")
                break
            except Exception as e:
                logger.error(f"❌ Error in processing loop: {str(e)}")
                time.sleep(1)

    def start(self):
        """Start the confirmation logger with background threads"""
        logger.info("📝 Confirmation Logger starting up...")
        
        # Start cleanup thread
        cleanup_thread = threading.Thread(target=self.cleanup_old_data, daemon=True)
        cleanup_thread.start()
        
        # Start status reporter thread
        status_thread = threading.Thread(target=self.status_reporter, daemon=True)
        status_thread.start()
        
        # Start main processing loop
        try:
            self.run()
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down confirmation logger...")
            self.running = False

if __name__ == "__main__":
    confirmation_logger = ConfirmationLogger()
    confirmation_logger.start()