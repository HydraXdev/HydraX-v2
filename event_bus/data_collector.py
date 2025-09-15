#!/usr/bin/env python3
"""
BITTEN Data Collector - ZMQ Event Consumer & SQLite Storage
Subscribes to event bus and stores events in database
"""

import zmq
import json
import sqlite3
import time
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from pathlib import Path

try:
    from .event_schema import validate_event
except ImportError:
    from event_schema import validate_event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/data_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DataCollector')


class DataCollector:
    """Professional event collector and database storage"""
    
    def __init__(self, event_bus_port: int = 5570, db_path: str = "/root/HydraX-v2/event_bus/bitten_events.db"):
        self.event_bus_port = event_bus_port
        self.db_path = db_path
        self.context = None
        self.subscriber = None
        self.running = False
        self.stats = {
            'events_received': 0,
            'events_stored': 0,
            'events_failed': 0,
            'start_time': None,
            'last_event_time': None
        }
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with proper schema"""
        logger.info(f"📊 Initializing database at {self.db_path}")
        
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with self._get_db_connection() as conn:
            # Main events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    source TEXT NOT NULL,
                    correlation_id TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    data_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            
            # Create indexes separately
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_source ON events(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_correlation_id ON events(correlation_id)")
            
            # Signal events table for faster querying
            conn.execute("""
                CREATE TABLE IF NOT EXISTS signal_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    signal_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    pattern_type TEXT NOT NULL,
                    entry_price REAL,
                    stop_pips REAL,
                    target_pips REAL,
                    expires_at REAL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            """)
            
            # Create indexes for signal events
            conn.execute("CREATE INDEX IF NOT EXISTS idx_signal_events_signal_id ON signal_events(signal_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_signal_events_symbol ON signal_events(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_signal_events_pattern_type ON signal_events(pattern_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_signal_events_expires_at ON signal_events(expires_at)")
            
            # Trade events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    fire_id TEXT,
                    ticket INTEGER,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    volume REAL,
                    open_price REAL,
                    sl_price REAL,
                    tp_price REAL,
                    execution_time REAL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            """)
            
            # Create indexes for trade events
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trade_events_fire_id ON trade_events(fire_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trade_events_ticket ON trade_events(ticket)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trade_events_symbol ON trade_events(symbol)")
            
            # System health events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS health_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    component TEXT NOT NULL,
                    status TEXT NOT NULL,
                    uptime REAL,
                    memory_usage REAL,
                    cpu_usage REAL,
                    message TEXT,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            """)
            
            # Create indexes for health events
            conn.execute("CREATE INDEX IF NOT EXISTS idx_health_events_component ON health_events(component)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_health_events_status ON health_events(status)")
            
            # Event statistics view
            conn.execute("""
                CREATE VIEW IF NOT EXISTS event_stats AS
                SELECT 
                    event_type,
                    COUNT(*) as count,
                    MIN(timestamp) as first_seen,
                    MAX(timestamp) as last_seen,
                    AVG(timestamp) as avg_timestamp
                FROM events
                GROUP BY event_type
            """)
            
            conn.commit()
            logger.info("✅ Database schema initialized successfully")
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
            conn.execute("PRAGMA synchronous=NORMAL")  # Better performance
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def start(self):
        """Start the data collector"""
        try:
            logger.info(f"🚀 Starting Data Collector, connecting to port {self.event_bus_port}")
            
            # Initialize ZMQ subscriber
            self.context = zmq.Context()
            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.connect(f"tcp://localhost:{self.event_bus_port}")
            
            # Subscribe to all BITTEN events
            self.subscriber.setsockopt(zmq.SUBSCRIBE, b"bitten.")
            
            # Set socket options
            self.subscriber.setsockopt(zmq.RCVHWM, 10000)  # High water mark
            self.subscriber.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
            
            self.running = True
            self.stats['start_time'] = time.time()
            
            logger.info("✅ Data Collector started successfully")
            
            # Start collecting events
            self.run_collection_loop()
            
        except Exception as e:
            logger.error(f"❌ Failed to start Data Collector: {e}")
            self.stop()
            raise
    
    def run_collection_loop(self):
        """Main event collection loop"""
        logger.info("📡 Starting event collection loop")
        
        # Start stats reporting in background
        stats_thread = threading.Thread(target=self._stats_reporter, daemon=True)
        stats_thread.start()
        
        while self.running:
            try:
                # Receive event with timeout
                topic, message = self.subscriber.recv_multipart(zmq.NOBLOCK)
                
                # Decode message
                topic_str = topic.decode('utf-8')
                event_data = json.loads(message.decode('utf-8'))
                
                # Process event
                self._process_event(topic_str, event_data)
                
            except zmq.Again:
                # Timeout - check if we should continue
                continue
            except KeyboardInterrupt:
                logger.info("🛑 Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"❌ Event processing error: {e}")
                self.stats['events_failed'] += 1
                time.sleep(1)  # Brief pause on error
        
        self.stop()
    
    def _process_event(self, topic: str, event_data: Dict[str, Any]):
        """Process and store a single event"""
        try:
            # Update stats
            self.stats['events_received'] += 1
            self.stats['last_event_time'] = time.time()
            
            # Validate event structure
            if not validate_event(event_data):
                logger.warning(f"⚠️ Invalid event structure for topic {topic}")
                self.stats['events_failed'] += 1
                return
            
            # Store event in database
            event_id = self._store_event(event_data)
            
            if event_id:
                # Store in specialized tables based on event type
                self._store_specialized_event(event_id, event_data)
                self.stats['events_stored'] += 1
                logger.debug(f"📊 Stored event {event_id}: {event_data.get('event_type')}")
            else:
                self.stats['events_failed'] += 1
                
        except Exception as e:
            logger.error(f"❌ Failed to process event: {e}")
            self.stats['events_failed'] += 1
    
    def _store_event(self, event_data: Dict[str, Any]) -> Optional[int]:
        """Store event in main events table"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO events (
                        event_type, timestamp, source, correlation_id, 
                        user_id, session_id, data_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_data.get('event_type'),
                    event_data.get('timestamp'),
                    event_data.get('source'),
                    event_data.get('correlation_id'),
                    event_data.get('user_id'),
                    event_data.get('session_id'),
                    json.dumps(event_data.get('data', {})),
                    time.time()
                ))
                
                event_id = cursor.lastrowid
                conn.commit()
                return event_id
                
        except Exception as e:
            logger.error(f"❌ Failed to store event: {e}")
            return None
    
    def _store_specialized_event(self, event_id: int, event_data: Dict[str, Any]):
        """Store event in specialized tables based on type"""
        event_type = event_data.get('event_type')
        data = event_data.get('data', {})
        
        try:
            with self._get_db_connection() as conn:
                if event_type == 'signal_generated':
                    conn.execute("""
                        INSERT INTO signal_events (
                            event_id, signal_id, symbol, direction, confidence,
                            pattern_type, entry_price, stop_pips, target_pips,
                            expires_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event_id,
                        data.get('signal_id'),
                        data.get('symbol'),
                        data.get('direction'),
                        data.get('confidence'),
                        data.get('pattern_type'),
                        data.get('entry_price'),
                        data.get('stop_pips'),
                        data.get('target_pips'),
                        data.get('expires_at'),
                        time.time()
                    ))
                
                elif event_type in ['fire_command', 'trade_executed']:
                    conn.execute("""
                        INSERT INTO trade_events (
                            event_id, fire_id, ticket, symbol, direction,
                            volume, open_price, sl_price, tp_price,
                            execution_time, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event_id,
                        data.get('fire_id'),
                        data.get('ticket'),
                        data.get('symbol'),
                        data.get('direction'),
                        data.get('volume') or data.get('lot_size'),
                        data.get('open_price'),
                        data.get('sl_price'),
                        data.get('tp_price'),
                        data.get('execution_time'),
                        time.time()
                    ))
                
                elif event_type == 'system_health':
                    conn.execute("""
                        INSERT INTO health_events (
                            event_id, component, status, uptime,
                            memory_usage, cpu_usage, message, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event_id,
                        data.get('component', event_data.get('source')),
                        data.get('status'),
                        data.get('uptime'),
                        data.get('memory_usage'),
                        data.get('cpu_usage'),
                        data.get('message'),
                        time.time()
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to store specialized event: {e}")
    
    def _stats_reporter(self):
        """Background thread to report statistics"""
        while self.running:
            try:
                time.sleep(60)  # Report every minute
                
                if self.stats['start_time']:
                    uptime = time.time() - self.stats['start_time']
                    events_per_min = (self.stats['events_received'] / uptime) * 60 if uptime > 0 else 0
                    
                    logger.info(f"📊 Stats: {self.stats['events_received']} received, "
                              f"{self.stats['events_stored']} stored, "
                              f"{self.stats['events_failed']} failed, "
                              f"{events_per_min:.1f} events/min")
                
            except Exception as e:
                logger.error(f"❌ Stats reporting error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current collector statistics"""
        stats = self.stats.copy()
        if stats['start_time']:
            stats['uptime'] = time.time() - stats['start_time']
        return stats
    
    def query_events(self, event_type: Optional[str] = None, 
                    start_time: Optional[float] = None,
                    end_time: Optional[float] = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """Query events from database"""
        try:
            with self._get_db_connection() as conn:
                query = "SELECT * FROM events WHERE 1=1"
                params = []
                
                if event_type:
                    query += " AND event_type = ?"
                    params.append(event_type)
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time)
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                events = []
                for row in cursor.fetchall():
                    event = {
                        'id': row[0],
                        'event_type': row[1],
                        'timestamp': row[2],
                        'source': row[3],
                        'correlation_id': row[4],
                        'user_id': row[5],
                        'session_id': row[6],
                        'data': json.loads(row[7]),
                        'created_at': row[8]
                    }
                    events.append(event)
                
                return events
                
        except Exception as e:
            logger.error(f"❌ Failed to query events: {e}")
            return []
    
    def stop(self):
        """Gracefully stop the data collector"""
        logger.info("🛑 Stopping Data Collector")
        
        self.running = False
        
        # Clean up ZMQ resources
        if self.subscriber:
            self.subscriber.close()
        if self.context:
            self.context.term()
        
        # Log final stats
        if self.stats['start_time']:
            uptime = time.time() - self.stats['start_time']
            logger.info(f"📊 Final stats: {self.stats['events_received']} received, "
                       f"{self.stats['events_stored']} stored, "
                       f"{uptime:.1f}s uptime")
        
        logger.info("✅ Data Collector stopped successfully")


def main():
    """Main entry point for the data collector"""
    logger.info("🚀 BITTEN Data Collector starting...")
    
    try:
        collector = DataCollector()
        collector.start()
    except KeyboardInterrupt:
        logger.info("👋 Data Collector shutdown requested")
    except Exception as e:
        logger.error(f"💥 Data Collector crashed: {e}")
        raise


if __name__ == "__main__":
    main()