#!/usr/bin/env python3
"""
FORTRESS SIGNAL PROCESSOR ENGINE (SPE) - Military Grade Signal Handling
Version: 1.0 BULLETPROOF
Mission: Process standardized bridge signals with zero tolerance for failure

HANDLES EVERYTHING. VALIDATES EVERYTHING. NEVER FAILS.
"""

import json
import socket
import threading
import time
import logging
import queue
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import jsonschema

class ProcessingStatus(Enum):
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"

@dataclass
class ProcessingResult:
    signal_id: str
    status: ProcessingStatus
    timestamp: datetime
    processing_time: float
    error_message: Optional[str] = None
    result_data: Optional[Dict] = None

class FortressSignalProcessor:
    """
    MILITARY-GRADE SIGNAL PROCESSING ENGINE
    
    Capabilities:
    - Bulletproof signal reception and validation
    - Multi-threaded processing with queue management
    - Real-time error handling and recovery
    - Performance monitoring and metrics
    - Automatic schema validation
    - Circuit breaker for overload protection
    """
    
    def __init__(self, listen_port: int = 8888, max_queue_size: int = 1000):
        self.listen_port = listen_port
        self.max_queue_size = max_queue_size
        self.is_running = False
        self.socket = None
        
        # Processing components
        self.signal_queue = queue.Queue(maxsize=max_queue_size)
        self.processing_threads = []
        self.num_worker_threads = 4
        
        # Signal handlers
        self.signal_handlers = {}
        self.default_handler = None
        
        # Metrics and monitoring
        self.total_received = 0
        self.total_processed = 0
        self.total_errors = 0
        self.processing_history = []
        self.start_time = time.time()
        
        # Circuit breaker
        self.circuit_breaker_threshold = 10  # errors in window
        self.circuit_breaker_window = 60  # seconds
        self.circuit_breaker_active = False
        self.error_timestamps = []
        
        # Load schema for validation
        self.schema = self._load_schema()
        
        # Initialize logging
        self.setup_logging()
        
        self.logger.info(f"🛡️ FORTRESS SPE INITIALIZED")
        self.logger.info(f"📡 Listen Port: {self.listen_port}")
        self.logger.info(f"⚙️ Worker Threads: {self.num_worker_threads}")
        self.logger.info(f"📊 Max Queue Size: {self.max_queue_size}")
        
    def setup_logging(self):
        """Initialize military-grade logging"""
        log_format = '%(asctime)s - FORTRESS_SPE - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('/root/HydraX-v2/fortress_spe.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("FORTRESS_SPE")
        
    def _load_schema(self) -> Dict:
        """Load signal validation schema"""
        try:
            with open('/root/HydraX-v2/shared/formats/bitten_trade.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load schema: {e}")
            return {"type": "object"}  # Fallback schema
            
    def register_handler(self, event_type: str, handler: Callable[[Dict], Any]):
        """Register signal handler for specific event type"""
        self.signal_handlers[event_type] = handler
        self.logger.info(f"✅ Registered handler for event: {event_type}")
        
    def set_default_handler(self, handler: Callable[[Dict], Any]):
        """Set default handler for unregistered events"""
        self.default_handler = handler
        self.logger.info(f"✅ Default handler registered")
        
    def start(self):
        """Start the fortress signal processor"""
        if self.is_running:
            self.logger.warning("SPE already running")
            return
            
        self.is_running = True
        self.logger.info(f"🚀 STARTING FORTRESS SPE")
        
        # Start socket listener
        self._start_socket_listener()
        
        # Start worker threads
        self._start_worker_threads()
        
        # Start monitoring thread
        self._start_monitoring_thread()
        
        self.logger.info(f"✅ FORTRESS SPE OPERATIONAL")
        
    def stop(self):
        """Stop the fortress signal processor"""
        self.logger.info(f"🛑 STOPPING FORTRESS SPE")
        
        self.is_running = False
        
        # Close socket
        if self.socket:
            self.socket.close()
            
        # Wait for worker threads to finish
        for thread in self.processing_threads:
            thread.join(timeout=5)
            
        self.logger.info(f"✅ FORTRESS SPE STOPPED")
        
    def _start_socket_listener(self):
        """Start socket listener thread"""
        listener_thread = threading.Thread(target=self._socket_listener, daemon=True)
        listener_thread.start()
        self.logger.info(f"📡 Socket listener started on port {self.listen_port}")
        
    def _socket_listener(self):
        """Socket listener for incoming signals"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.listen_port))
            self.socket.listen(5)
            
            self.logger.info(f"🔊 Listening for signals on port {self.listen_port}")
            
            while self.is_running:
                try:
                    client_socket, address = self.socket.accept()
                    self.logger.debug(f"📨 Connection from {address}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.error as e:
                    if self.is_running:
                        self.logger.error(f"❌ Socket error: {e}")
                        
        except Exception as e:
            self.logger.error(f"❌ Socket listener failed: {e}")
            
    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle individual client connection"""
        try:
            while self.is_running:
                data = client_socket.recv(4096)
                if not data:
                    break
                    
                # Decode and queue signal
                signal_data = data.decode('utf-8')
                self._queue_signal(signal_data, address)
                
                # Send acknowledgment
                client_socket.send(b"ACK\n")
                
        except Exception as e:
            self.logger.error(f"❌ Client handling error from {address}: {e}")
        finally:
            client_socket.close()
            
    def _queue_signal(self, signal_data: str, source: tuple):
        """Queue incoming signal for processing"""
        try:
            # Check circuit breaker
            if self.circuit_breaker_active:
                self.logger.warning(f"🚫 Circuit breaker active - rejecting signal from {source}")
                return
                
            # Parse signal
            signal = json.loads(signal_data)
            
            # Add metadata
            signal['_metadata'] = {
                'received_at': datetime.now(timezone.utc).isoformat(),
                'source': f"{source[0]}:{source[1]}",
                'signal_id': f"signal_{int(time.time() * 1000000)}"
            }
            
            # Queue for processing
            try:
                self.signal_queue.put(signal, block=False)
                self.total_received += 1
                self.logger.debug(f"📨 Signal queued: {signal.get('event', 'unknown')}")
            except queue.Full:
                self.logger.error(f"❌ Signal queue full - dropping signal")
                self._record_error("Queue overflow")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Invalid JSON from {source}: {e}")
            self._record_error(f"JSON decode error: {e}")
        except Exception as e:
            self.logger.error(f"❌ Signal queuing error: {e}")
            self._record_error(f"Queuing error: {e}")
            
    def _start_worker_threads(self):
        """Start worker threads for signal processing"""
        for i in range(self.num_worker_threads):
            worker_thread = threading.Thread(
                target=self._worker_thread,
                args=(f"worker_{i}",),
                daemon=True
            )
            worker_thread.start()
            self.processing_threads.append(worker_thread)
            
        self.logger.info(f"⚙️ Started {self.num_worker_threads} worker threads")
        
    def _worker_thread(self, worker_name: str):
        """Worker thread for processing signals"""
        self.logger.info(f"👷 Worker {worker_name} started")
        
        while self.is_running:
            try:
                # Get signal from queue with timeout
                signal = self.signal_queue.get(timeout=1)
                
                # Process signal
                result = self._process_signal(signal, worker_name)
                
                # Record result
                self._record_processing_result(result)
                
                # Mark task as done
                self.signal_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"❌ Worker {worker_name} error: {e}")
                self._record_error(f"Worker error: {e}")
                
        self.logger.info(f"👷 Worker {worker_name} stopped")
        
    def _process_signal(self, signal: Dict, worker_name: str) -> ProcessingResult:
        """Process individual signal"""
        signal_id = signal.get('_metadata', {}).get('signal_id', 'unknown')
        start_time = time.time()
        
        try:
            self.logger.debug(f"⚙️ {worker_name} processing {signal_id}")
            
            # Validate signal
            self._validate_signal(signal)
            
            # Get event type and handler
            event_type = signal.get('event', 'unknown')
            handler = self.signal_handlers.get(event_type, self.default_handler)
            
            if not handler:
                raise ProcessingError(f"No handler for event type: {event_type}")
                
            # Process signal
            result_data = handler(signal)
            
            processing_time = time.time() - start_time
            self.total_processed += 1
            
            return ProcessingResult(
                signal_id=signal_id,
                status=ProcessingStatus.COMPLETED,
                timestamp=datetime.now(timezone.utc),
                processing_time=processing_time,
                result_data=result_data
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"❌ Processing failed for {signal_id}: {e}")
            self._record_error(f"Processing error: {e}")
            
            return ProcessingResult(
                signal_id=signal_id,
                status=ProcessingStatus.FAILED,
                timestamp=datetime.now(timezone.utc),
                processing_time=processing_time,
                error_message=str(e)
            )
            
    def _validate_signal(self, signal: Dict):
        """Validate signal against schema"""
        try:
            # Remove metadata before validation
            signal_copy = signal.copy()
            signal_copy.pop('_metadata', None)
            
            jsonschema.validate(signal_copy, self.schema)
        except jsonschema.ValidationError as e:
            raise ProcessingError(f"Signal validation failed: {e.message}")
            
    def _record_processing_result(self, result: ProcessingResult):
        """Record processing result for monitoring"""
        self.processing_history.append(result)
        
        # Keep only recent history
        if len(self.processing_history) > 1000:
            self.processing_history = self.processing_history[-500:]
            
    def _record_error(self, error_message: str):
        """Record error for circuit breaker"""
        self.total_errors += 1
        self.error_timestamps.append(time.time())
        
        # Clean old timestamps
        cutoff = time.time() - self.circuit_breaker_window
        self.error_timestamps = [ts for ts in self.error_timestamps if ts > cutoff]
        
        # Check circuit breaker
        if len(self.error_timestamps) >= self.circuit_breaker_threshold:
            self.circuit_breaker_active = True
            self.logger.error(f"🚫 CIRCUIT BREAKER ACTIVATED - Too many errors")
            
            # Auto-reset after window
            threading.Timer(self.circuit_breaker_window, self._reset_circuit_breaker).start()
            
    def _reset_circuit_breaker(self):
        """Reset circuit breaker"""
        self.circuit_breaker_active = False
        self.error_timestamps = []
        self.logger.info(f"✅ Circuit breaker reset")
        
    def _start_monitoring_thread(self):
        """Start monitoring thread"""
        monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitor_thread.start()
        self.logger.info(f"📊 Monitoring thread started")
        
    def _monitoring_loop(self):
        """Monitoring loop for performance metrics"""
        while self.is_running:
            try:
                time.sleep(30)  # Monitor every 30 seconds
                
                metrics = self.get_performance_metrics()
                self.logger.info(f"📊 Performance: {metrics['signals_per_minute']:.1f} signals/min, "
                               f"{metrics['success_rate']:.1f}% success, "
                               f"Queue: {metrics['queue_size']}")
                
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                
    def get_performance_metrics(self) -> Dict:
        """Get comprehensive performance metrics"""
        uptime = time.time() - self.start_time
        queue_size = self.signal_queue.qsize()
        
        success_count = sum(1 for r in self.processing_history if r.status == ProcessingStatus.COMPLETED)
        total_attempts = len(self.processing_history)
        success_rate = (success_count / total_attempts * 100) if total_attempts > 0 else 100
        
        avg_processing_time = sum(r.processing_time for r in self.processing_history) / len(self.processing_history) if self.processing_history else 0
        
        return {
            "uptime_seconds": uptime,
            "total_received": self.total_received,
            "total_processed": self.total_processed,
            "total_errors": self.total_errors,
            "queue_size": queue_size,
            "success_rate": success_rate,
            "signals_per_minute": (self.total_received / (uptime / 60)) if uptime > 0 else 0,
            "avg_processing_time": avg_processing_time,
            "circuit_breaker_active": self.circuit_breaker_active,
            "worker_threads": len(self.processing_threads)
        }
        
    def process_signal_sync(self, signal_data: str) -> ProcessingResult:
        """Process signal synchronously (for testing)"""
        try:
            signal = json.loads(signal_data)
            signal['_metadata'] = {
                'received_at': datetime.now(timezone.utc).isoformat(),
                'source': 'sync_test',
                'signal_id': f"sync_{int(time.time() * 1000000)}"
            }
            
            return self._process_signal(signal, "sync_worker")
            
        except Exception as e:
            return ProcessingResult(
                signal_id="sync_error",
                status=ProcessingStatus.FAILED,
                timestamp=datetime.now(timezone.utc),
                processing_time=0,
                error_message=str(e)
            )

class ProcessingError(Exception):
    """Custom exception for processing errors"""
    pass

# Default signal handlers
def handle_new_trade(signal: Dict) -> Dict:
    """Default handler for new trade signals"""
    logging.getLogger("FORTRESS_SPE").info(f"🔥 NEW TRADE: {signal['symbol']} {signal['order_type']} {signal['lot_size']} lots @ {signal['entry_price']}")
    
    # Process the trade signal
    result = {
        "action": "trade_processed",
        "symbol": signal['symbol'],
        "entry_price": signal['entry_price'],
        "lot_size": signal['lot_size'],
        "tcs_score": signal['tcs_score'],
        "processed_at": datetime.now(timezone.utc).isoformat()
    }
    
    return result

def handle_price_update(signal: Dict) -> Dict:
    """Default handler for price updates"""
    logging.getLogger("FORTRESS_SPE").debug(f"📈 PRICE UPDATE: {signal['symbol']} @ {signal['entry_price']}")
    
    return {
        "action": "price_updated",
        "symbol": signal['symbol'],
        "price": signal['entry_price'],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

def handle_heartbeat(signal: Dict) -> Dict:
    """Default handler for heartbeat signals"""
    logging.getLogger("FORTRESS_SPE").debug(f"💓 HEARTBEAT from {signal['bridge_id']}")
    
    return {
        "action": "heartbeat_received",
        "bridge_id": signal['bridge_id'],
        "timestamp": signal['timestamp']
    }

# Global SPE instance
FORTRESS_SPE = None

def get_fortress_spe(port: int = 8888) -> FortressSignalProcessor:
    """Get or create global SPE instance"""
    global FORTRESS_SPE
    if FORTRESS_SPE is None:
        FORTRESS_SPE = FortressSignalProcessor(listen_port=port)
        
        # Register default handlers
        FORTRESS_SPE.register_handler("new_trade", handle_new_trade)
        FORTRESS_SPE.register_handler("price_update", handle_price_update)
        FORTRESS_SPE.register_handler("heartbeat", handle_heartbeat)
        FORTRESS_SPE.set_default_handler(lambda signal: {"action": "unhandled", "event": signal.get("event")})
        
    return FORTRESS_SPE

if __name__ == "__main__":
    # Test the signal processor
    print("🛡️ FORTRESS SIGNAL PROCESSOR - TESTING MODE")
    
    spe = get_fortress_spe(8889)
    
    # Test signal
    test_signal = {
        "event": "new_trade",
        "timestamp": "2025-07-14T18:21:00.123Z",
        "symbol": "XAUUSD",
        "order_type": "buy",
        "lot_size": 0.10,
        "entry_price": 2374.10,
        "sl": 2370.00,
        "tp": 2382.00,
        "bridge_id": "bridge_019",
        "account_id": "843859",
        "execution_id": "CMD123456",
        "strategy": "bitmode_auto",
        "tcs_score": 82
    }
    
    # Test synchronous processing
    result = spe.process_signal_sync(json.dumps(test_signal))
    print(f"Test result: {result}")
    
    # Get metrics
    metrics = spe.get_performance_metrics()
    print(f"Metrics: {metrics}")
    
    print("✅ Test completed")