#!/usr/bin/env python3
"""
NODE REGISTRY v1.0
Redis-backed node registry for EA connections with state management

Author: BITTEN Trading System
Date: August 6, 2025
Purpose: Manage EA node connections, track heartbeats, and provide node APIs
"""

import redis
import json
import time
import logging
import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - NODE_REGISTRY - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/node_registry.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class NodeInfo:
    """Node information data structure"""
    node_id: str
    account: str
    broker: str
    balance: float
    equity: float
    symbol: str
    server: str
    ea_version: str
    magic_number: int
    connected_at: float
    last_heartbeat: float
    status: str
    connection_ip: str
    session_id: str = None
    disconnected_at: float = None
    total_uptime: float = 0
    connection_count: int = 1

class NodeRegistry:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.heartbeat_timeout = 60  # seconds
        self.cleanup_interval = 300  # 5 minutes
        self.running = True
        
        # Test Redis connection
        try:
            self.redis_client.ping()
            logger.info("✅ Connected to Redis server")
        except redis.ConnectionError:
            logger.error("❌ Failed to connect to Redis server")
            raise
        
        logger.info("🗂️ Node Registry v1.0 initialized")

    def generate_node_id(self, handshake_data: Dict) -> str:
        """Generate unique node ID"""
        account = handshake_data.get('account', 'UNKNOWN')
        broker = handshake_data.get('broker', 'UNKNOWN')
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        
        return f"NODE_{account}_{broker}_{timestamp}_{unique_id}"

    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        return str(uuid.uuid4())

    def register_node(self, handshake_data: Dict) -> str:
        """Register a new node or update existing one"""
        try:
            account = handshake_data.get('account', 'UNKNOWN')
            broker = handshake_data.get('broker', 'UNKNOWN')
            
            # Check if account is already connected
            existing_node_id = self.get_node_by_account(account)
            
            if existing_node_id:
                # Account reconnection - mark old node as replaced
                self._handle_account_reconnection(existing_node_id, handshake_data)
            
            # Generate new node ID and session
            node_id = self.generate_node_id(handshake_data)
            session_id = self.generate_session_id()
            
            # Create node info
            node_info = NodeInfo(
                node_id=node_id,
                account=account,
                broker=broker,
                balance=float(handshake_data.get('balance', 0)),
                equity=float(handshake_data.get('equity', 0)),
                symbol=handshake_data.get('symbol', 'UNKNOWN'),
                server=handshake_data.get('server', 'UNKNOWN'),
                ea_version=handshake_data.get('ea_version', 'UNKNOWN'),
                magic_number=int(handshake_data.get('magic_number', 0)),
                connected_at=time.time(),
                last_heartbeat=time.time(),
                status='active',
                connection_ip=handshake_data.get('ip', 'UNKNOWN'),
                session_id=session_id
            )
            
            # Store node info in Redis
            self._store_node(node_info)
            
            # Update account mapping
            self.redis_client.hset("account_to_node", account, node_id)
            
            # Update session mapping
            self.redis_client.hset("session_to_node", session_id, node_id)
            self.redis_client.expire("session_to_node", 86400)  # 24 hour sessions
            
            # Add to active nodes set
            self.redis_client.sadd("active_nodes", node_id)
            
            # Update broker statistics
            self._update_broker_stats(broker, 'connection')
            
            # Log connection event
            self._log_connection_event(node_id, 'connected', handshake_data)
            
            logger.info(f"🟢 Node registered: {node_id} (Account: {account}, Broker: {broker})")
            
            return node_id
            
        except Exception as e:
            logger.error(f"❌ Error registering node: {str(e)}")
            raise

    def _store_node(self, node_info: NodeInfo):
        """Store node information in Redis"""
        node_data = asdict(node_info)
        
        # Convert floats to strings for Redis storage
        for key, value in node_data.items():
            if isinstance(value, float):
                node_data[key] = str(value)
        
        # Store node data
        self.redis_client.hset(f"node:{node_info.node_id}", mapping=node_data)
        
        # Set expiry (extended by heartbeats)
        self.redis_client.expire(f"node:{node_info.node_id}", 86400)  # 24 hours

    def _handle_account_reconnection(self, old_node_id: str, new_handshake_data: Dict):
        """Handle account reconnecting with new node"""
        try:
            # Get old node data
            old_node_data = self.redis_client.hgetall(f"node:{old_node_id}")
            
            if old_node_data:
                # Calculate uptime of old connection
                connected_at = float(old_node_data.get('connected_at', time.time()))
                uptime = time.time() - connected_at
                
                # Update old node status
                self.redis_client.hset(f"node:{old_node_id}", mapping={
                    'status': 'replaced',
                    'disconnected_at': str(time.time()),
                    'total_uptime': str(uptime)
                })
                
                # Remove from active nodes
                self.redis_client.srem("active_nodes", old_node_id)
                
                # Log disconnection
                self._log_connection_event(old_node_id, 'replaced', {'reason': 'reconnection'})
                
                logger.info(f"🔄 Node {old_node_id} replaced by reconnection")
        
        except Exception as e:
            logger.error(f"Error handling account reconnection: {str(e)}")

    def update_heartbeat(self, node_id: str, heartbeat_data: Optional[Dict] = None):
        """Update node heartbeat"""
        try:
            if not self.redis_client.sismember("active_nodes", node_id):
                logger.warning(f"⚠️ Heartbeat from inactive node: {node_id}")
                return False
            
            updates = {'last_heartbeat': str(time.time())}
            
            # Update additional data if provided
            if heartbeat_data:
                if 'balance' in heartbeat_data:
                    updates['balance'] = str(float(heartbeat_data['balance']))
                if 'equity' in heartbeat_data:
                    updates['equity'] = str(float(heartbeat_data['equity']))
                if 'symbol' in heartbeat_data:
                    updates['symbol'] = heartbeat_data['symbol']
            
            # Update node data
            self.redis_client.hset(f"node:{node_id}", mapping=updates)
            
            # Extend expiry
            self.redis_client.expire(f"node:{node_id}", 86400)
            
            logger.debug(f"💓 Heartbeat updated for {node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating heartbeat for {node_id}: {str(e)}")
            return False

    def get_node_by_account(self, account: str) -> Optional[str]:
        """Get active node ID by account number"""
        return self.redis_client.hget("account_to_node", account)

    def get_node_by_session(self, session_id: str) -> Optional[str]:
        """Get node ID by session ID"""
        return self.redis_client.hget("session_to_node", session_id)

    def get_node_info(self, node_id: str) -> Optional[Dict]:
        """Get complete node information"""
        try:
            node_data = self.redis_client.hgetall(f"node:{node_id}")
            
            if not node_data:
                return None
            
            # Convert string values back to appropriate types
            for key in ['balance', 'equity', 'connected_at', 'last_heartbeat', 'disconnected_at', 'total_uptime']:
                if key in node_data and node_data[key]:
                    try:
                        node_data[key] = float(node_data[key])
                    except ValueError:
                        pass
            
            for key in ['magic_number', 'connection_count']:
                if key in node_data and node_data[key]:
                    try:
                        node_data[key] = int(node_data[key])
                    except ValueError:
                        pass
            
            return node_data
            
        except Exception as e:
            logger.error(f"Error getting node info for {node_id}: {str(e)}")
            return None

    def get_active_nodes(self) -> List[Dict]:
        """Get all currently active nodes"""
        try:
            active_node_ids = self.redis_client.smembers("active_nodes")
            active_nodes = []
            
            for node_id in active_node_ids:
                node_info = self.get_node_info(node_id)
                if node_info:
                    # Check if node is truly active (heartbeat within timeout)
                    last_heartbeat = node_info.get('last_heartbeat', 0)
                    if time.time() - last_heartbeat <= self.heartbeat_timeout:
                        active_nodes.append(node_info)
                    else:
                        # Node is stale, mark as timeout
                        self._handle_node_timeout(node_id)
            
            return active_nodes
            
        except Exception as e:
            logger.error(f"Error getting active nodes: {str(e)}")
            return []

    def get_nodes_by_broker(self, broker: str) -> List[Dict]:
        """Get all active nodes for a specific broker"""
        active_nodes = self.get_active_nodes()
        return [node for node in active_nodes if node.get('broker') == broker]

    def get_nodes_by_status(self, status: str) -> List[Dict]:
        """Get nodes by status (active, inactive, replaced, timeout)"""
        try:
            # This is a simplified implementation - in production, maintain status indexes
            all_node_keys = self.redis_client.keys("node:*")
            matching_nodes = []
            
            for node_key in all_node_keys:
                node_data = self.redis_client.hgetall(node_key)
                if node_data.get('status') == status:
                    matching_nodes.append(self.get_node_info(node_key.split(':')[1]))
            
            return [node for node in matching_nodes if node is not None]
            
        except Exception as e:
            logger.error(f"Error getting nodes by status {status}: {str(e)}")
            return []

    def disconnect_node(self, node_id: str, reason: str = 'manual'):
        """Manually disconnect a node"""
        try:
            node_info = self.get_node_info(node_id)
            if not node_info:
                logger.warning(f"⚠️ Cannot disconnect unknown node: {node_id}")
                return False
            
            # Calculate uptime
            connected_at = node_info.get('connected_at', time.time())
            uptime = time.time() - connected_at
            
            # Update node status
            self.redis_client.hset(f"node:{node_id}", mapping={
                'status': 'disconnected',
                'disconnected_at': str(time.time()),
                'total_uptime': str(uptime),
                'disconnect_reason': reason
            })
            
            # Remove from active nodes
            self.redis_client.srem("active_nodes", node_id)
            
            # Remove account mapping if this is the current node
            account = node_info.get('account')
            current_node = self.get_node_by_account(account)
            if current_node == node_id:
                self.redis_client.hdel("account_to_node", account)
            
            # Log disconnection
            self._log_connection_event(node_id, 'disconnected', {'reason': reason})
            
            logger.info(f"🔴 Node disconnected: {node_id} (Reason: {reason})")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting node {node_id}: {str(e)}")
            return False

    def _handle_node_timeout(self, node_id: str):
        """Handle node timeout (no heartbeat)"""
        self.disconnect_node(node_id, 'timeout')
        logger.warning(f"⏰ Node timed out: {node_id}")

    def get_registry_stats(self) -> Dict:
        """Get registry statistics"""
        try:
            active_nodes = self.get_active_nodes()
            
            # Basic stats
            stats = {
                'active_nodes': len(active_nodes),
                'total_nodes_ever': len(self.redis_client.keys("node:*")),
                'unique_accounts': len(set(node.get('account') for node in active_nodes)),
                'unique_brokers': len(set(node.get('broker') for node in active_nodes)),
                'total_balance': sum(float(node.get('balance', 0)) for node in active_nodes),
                'total_equity': sum(float(node.get('equity', 0)) for node in active_nodes),
                'last_updated': time.time()
            }
            
            # Broker breakdown
            broker_stats = {}
            for node in active_nodes:
                broker = node.get('broker', 'UNKNOWN')
                if broker not in broker_stats:
                    broker_stats[broker] = {
                        'nodes': 0,
                        'accounts': set(),
                        'total_balance': 0,
                        'total_equity': 0
                    }
                
                broker_stats[broker]['nodes'] += 1
                broker_stats[broker]['accounts'].add(node.get('account'))
                broker_stats[broker]['total_balance'] += float(node.get('balance', 0))
                broker_stats[broker]['total_equity'] += float(node.get('equity', 0))
            
            # Convert sets to counts
            for broker in broker_stats:
                broker_stats[broker]['unique_accounts'] = len(broker_stats[broker]['accounts'])
                del broker_stats[broker]['accounts']
            
            stats['brokers'] = broker_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting registry stats: {str(e)}")
            return {'error': str(e)}

    def _update_broker_stats(self, broker: str, event_type: str):
        """Update broker-specific statistics"""
        try:
            stats_key = f"broker_stats:{broker}"
            self.redis_client.hincrby(stats_key, f"total_{event_type}s", 1)
            self.redis_client.hset(stats_key, f"last_{event_type}", str(time.time()))
            self.redis_client.expire(stats_key, 86400 * 30)  # Keep for 30 days
        
        except Exception as e:
            logger.error(f"Error updating broker stats: {str(e)}")

    def _log_connection_event(self, node_id: str, event_type: str, event_data: Dict):
        """Log connection events for audit trail"""
        try:
            event_record = {
                'timestamp': time.time(),
                'node_id': node_id,
                'event_type': event_type,
                'event_data': event_data
            }
            
            # Store in Redis list
            self.redis_client.lpush("connection_events", json.dumps(event_record))
            self.redis_client.ltrim("connection_events", 0, 9999)  # Keep last 10k events
            
            # Store in file
            with open('/root/HydraX-v2/logs/connection_events.jsonl', 'a') as f:
                f.write(json.dumps(event_record) + '\n')
        
        except Exception as e:
            logger.error(f"Error logging connection event: {str(e)}")

    def cleanup_stale_nodes(self):
        """Clean up stale/expired nodes"""
        try:
            active_node_ids = list(self.redis_client.smembers("active_nodes"))
            cleaned_count = 0
            
            for node_id in active_node_ids:
                node_info = self.get_node_info(node_id)
                
                if not node_info:
                    # Node data doesn't exist
                    self.redis_client.srem("active_nodes", node_id)
                    cleaned_count += 1
                    continue
                
                # Check heartbeat timeout
                last_heartbeat = node_info.get('last_heartbeat', 0)
                if time.time() - last_heartbeat > self.heartbeat_timeout:
                    self._handle_node_timeout(node_id)
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned up {cleaned_count} stale nodes")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up stale nodes: {str(e)}")
            return 0

    def monitor_nodes(self):
        """Background monitoring of node health"""
        while self.running:
            try:
                # Clean up stale nodes
                self.cleanup_stale_nodes()
                
                # Report status
                stats = self.get_registry_stats()
                logger.info(f"📊 Registry Status: {stats.get('active_nodes', 0)} active nodes, "
                          f"{stats.get('unique_accounts', 0)} accounts, "
                          f"{stats.get('unique_brokers', 0)} brokers")
                
                time.sleep(self.cleanup_interval)
                
            except Exception as e:
                logger.error(f"Error in node monitoring: {str(e)}")
                time.sleep(60)

    def start_monitoring(self):
        """Start background node monitoring"""
        logger.info("🔄 Starting node registry monitoring...")
        monitor_thread = threading.Thread(target=self.monitor_nodes, daemon=True)
        monitor_thread.start()
        return monitor_thread

    def switch_account(self, old_node_id: str, new_account: str, handshake_data: Dict) -> str:
        """Handle account switching on same EA instance"""
        try:
            # Disconnect old node
            self.disconnect_node(old_node_id, 'account_switch')
            
            # Register new node with new account
            handshake_data['account'] = new_account
            new_node_id = self.register_node(handshake_data)
            
            logger.info(f"🔄 Account switch: {old_node_id} -> {new_node_id}")
            return new_node_id
            
        except Exception as e:
            logger.error(f"Error switching account: {str(e)}")
            raise

    def get_connection_history(self, limit: int = 100) -> List[Dict]:
        """Get recent connection history"""
        try:
            events = self.redis_client.lrange("connection_events", 0, limit - 1)
            return [json.loads(event) for event in events]
        
        except Exception as e:
            logger.error(f"Error getting connection history: {str(e)}")
            return []

    def shutdown(self):
        """Gracefully shutdown the registry"""
        logger.info("🛑 Shutting down node registry...")
        self.running = False

# API wrapper for easy integration
class NodeRegistryAPI:
    def __init__(self):
        self.registry = NodeRegistry()
        self.registry.start_monitoring()
    
    def register(self, handshake_data: Dict) -> str:
        return self.registry.register_node(handshake_data)
    
    def heartbeat(self, node_id: str, data: Dict = None) -> bool:
        return self.registry.update_heartbeat(node_id, data)
    
    def get_active(self) -> List[Dict]:
        return self.registry.get_active_nodes()
    
    def get_stats(self) -> Dict:
        return self.registry.get_registry_stats()
    
    def disconnect(self, node_id: str, reason: str = 'manual') -> bool:
        return self.registry.disconnect_node(node_id, reason)

if __name__ == "__main__":
    # Example usage and testing
    registry = NodeRegistry()
    
    # Start monitoring
    monitor_thread = registry.start_monitoring()
    
    try:
        logger.info("🗂️ Node Registry running... Press Ctrl+C to stop")
        while True:
            time.sleep(10)
            
            # Display current status every 10 seconds
            stats = registry.get_registry_stats()
            if stats.get('active_nodes', 0) > 0:
                logger.info(f"Status: {stats['active_nodes']} active nodes")
    
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        registry.shutdown()