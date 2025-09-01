#!/usr/bin/env python3
"""
Command bus for sending commands to EA with sequencing, rate limiting, and retries
Ensures commands are sent reliably and in order
"""

import json
import time
import zmq
import toml
import threading
from dataclasses import dataclass
from typing import Dict, Optional, Any, List
from pathlib import Path
import logging
from queue import Queue, PriorityQueue
import random

logger = logging.getLogger(__name__)

# Load rollout configuration
CONFIG_PATH = Path("/root/HydraX-v2/config/rollout.toml")
ROLLOUT_CONFIG = toml.load(CONFIG_PATH) if CONFIG_PATH.exists() else {}

@dataclass
class Command:
    """Command to be sent to EA"""
    fire_id: str
    ticket: int
    seq: int
    cmd_type: str  # PARTIAL_CLOSE, MODIFY_SL, CLOSE
    args: Dict[str, Any]
    timestamp_ms: int
    retries: int = 0
    priority: int = 1  # Lower = higher priority
    target_uuid: Optional[str] = None  # EA identifier
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for ZMQ transmission"""
        data = {
            "fire_id": self.fire_id,
            "seq": self.seq,
            "cmd": self.cmd_type,
            "ticket": self.ticket,
            "args": self.args,
            "ts_ms": self.timestamp_ms
        }
        if self.target_uuid:
            data["target_uuid"] = self.target_uuid
        return data
    
    def __lt__(self, other):
        """For priority queue ordering"""
        return (self.priority, self.seq) < (other.priority, other.seq)

class CommandBus:
    """
    Manages command sending to EA with reliability features
    """
    
    def __init__(self, zmq_addr: str = "ipc:///tmp/bitten_cmdqueue"):
        self.zmq_addr = zmq_addr
        self.context = zmq.Context()
        self.socket = None
        self._connect()
        
        # Rate limiting
        self.last_command_time: Dict[int, float] = {}  # ticket -> last send time
        self.min_gap_ms = ROLLOUT_CONFIG.get("MIN_CMD_GAP_MS", 700)
        
        # Retry configuration
        self.max_retries = ROLLOUT_CONFIG.get("MAX_RETRIES", 3)
        self.retry_backoff_ms = ROLLOUT_CONFIG.get("RETRY_BACKOFF_MS", [150, 300, 600])
        
        # Command queue for throttling
        self.command_queue = PriorityQueue()
        self.processing = False
        self.process_thread = None
        
        # Tracking
        self.sent_commands: Dict[str, Command] = {}  # fire_id:seq -> Command
        self.command_lock = threading.RLock()
        
        # Start processor
        self._start_processor()
    
    def _connect(self):
        """Connect to ZMQ socket"""
        try:
            self.socket = self.context.socket(zmq.PUSH)
            self.socket.connect(self.zmq_addr)
            self.socket.setsockopt(zmq.LINGER, 0)
            logger.info(f"Connected to command queue at {self.zmq_addr}")
        except Exception as e:
            logger.error(f"Failed to connect to ZMQ: {e}")
    
    def _start_processor(self):
        """Start command processor thread"""
        self.processing = True
        self.process_thread = threading.Thread(target=self._process_commands)
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def _process_commands(self):
        """Process commands from queue with rate limiting"""
        while self.processing:
            try:
                # Get next command (blocks with timeout)
                try:
                    cmd = self.command_queue.get(timeout=0.1)
                except:
                    continue
                
                # Check rate limit
                if not self._can_send(cmd.ticket):
                    # Re-queue with slight delay
                    time.sleep(0.05)
                    self.command_queue.put(cmd)
                    continue
                
                # Send command
                success = self._send_command(cmd)
                
                if not success and cmd.retries < self.max_retries:
                    # Retry with backoff
                    cmd.retries += 1
                    backoff_ms = self.retry_backoff_ms[min(cmd.retries - 1, len(self.retry_backoff_ms) - 1)]
                    
                    # Add jitter
                    jitter = random.uniform(0.8, 1.2)
                    backoff_ms = int(backoff_ms * jitter)
                    
                    time.sleep(backoff_ms / 1000.0)
                    
                    logger.info(f"Retrying command {cmd.cmd_type} for ticket {cmd.ticket} (attempt {cmd.retries})")
                    self.command_queue.put(cmd)
                elif not success:
                    logger.error(f"Command {cmd.cmd_type} for ticket {cmd.ticket} failed after {cmd.retries} retries")
                
            except Exception as e:
                logger.error(f"Error in command processor: {e}")
                time.sleep(0.1)
    
    def _can_send(self, ticket: int) -> bool:
        """Check if we can send a command for this ticket (rate limiting)"""
        now = time.time() * 1000  # milliseconds
        last = self.last_command_time.get(ticket, 0)
        
        if now - last < self.min_gap_ms:
            return False
        
        return True
    
    def _send_command(self, cmd: Command) -> bool:
        """Actually send command via ZMQ"""
        try:
            # Update rate limit tracker
            self.last_command_time[cmd.ticket] = time.time() * 1000
            
            # Send via ZMQ
            self.socket.send_json(cmd.to_dict())
            
            # Track sent command
            with self.command_lock:
                key = f"{cmd.fire_id}:{cmd.seq}"
                self.sent_commands[key] = cmd
            
            logger.info(f"Sent {cmd.cmd_type} for ticket {cmd.ticket} (seq={cmd.seq})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False
    
    def partial_close(self, ticket: int, fire_id: str, seq: int, 
                     close_pct: float, milestone: str = "") -> bool:
        """Queue a partial close command"""
        # Add comment for MT5 tracking
        comment = ""
        if close_pct == 0.75:
            comment = "BITMODE_PARTIAL75"
        elif close_pct == 0.50:
            comment = "BITMODE_PARTIAL50"
        else:
            comment = f"PARTIAL_{int(close_pct*100)}"
        
        cmd = Command(
            fire_id=fire_id,
            ticket=ticket,
            seq=seq,
            cmd_type="PARTIAL_CLOSE",
            args={
                "close_pct": close_pct,
                "milestone": milestone,
                "comment": comment
            },
            timestamp_ms=int(time.time() * 1000)
        )
        
        self.command_queue.put(cmd)
        logger.info(f"Queued PARTIAL_CLOSE {close_pct:.0%} for ticket {ticket}")
        return True
    
    def modify_sl(self, ticket: int, fire_id: str, seq: int, 
                 new_sl: float, milestone: str = "") -> bool:
        """Queue a stop loss modification"""
        # Add comment based on milestone
        comment = ""
        if "tp1" in milestone.lower() or "be" in milestone.lower():
            comment = "BE_MOVE"
        elif "trail" in milestone.lower():
            comment = "TRAIL_ACTIVE"
        else:
            comment = milestone[:20] if milestone else "SL_MODIFY"
        
        cmd = Command(
            fire_id=fire_id,
            ticket=ticket,
            seq=seq,
            cmd_type="MODIFY_SL",
            args={
                "sl_price": new_sl,
                "milestone": milestone,
                "comment": comment
            },
            timestamp_ms=int(time.time() * 1000)
        )
        
        self.command_queue.put(cmd)
        logger.info(f"Queued MODIFY_SL to {new_sl} for ticket {ticket}")
        return True
    
    def close_all(self, ticket: int, fire_id: str, seq: int, 
                 reason: str = "", target_uuid: Optional[str] = None) -> bool:
        """Queue a full position close"""
        # If no target_uuid provided, try to get it from fires table first
        if not target_uuid:
            import sqlite3
            try:
                conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
                cursor = conn.cursor()
                
                # First try to get from fires table using ticket
                cursor.execute("SELECT target_uuid FROM fires WHERE ticket=? AND target_uuid IS NOT NULL LIMIT 1", 
                             (ticket,))
                result = cursor.fetchone()
                if result:
                    target_uuid = result[0]
                else:
                    # Fallback to getting from position's user
                    from .state_store import state_store
                    pos = state_store.get_position(ticket)
                    if pos and pos.user_id:
                        cursor.execute("SELECT target_uuid FROM ea_instances WHERE user_id=? LIMIT 1", 
                                     (pos.user_id,))
                        result = cursor.fetchone()
                        if result:
                            target_uuid = result[0]
                conn.close()
            except Exception as e:
                logger.warning(f"Failed to get target_uuid for ticket {ticket}: {e}")
        
        # Add comment based on close reason
        comment = ""
        if "timeout" in reason.lower():
            comment = "TIMEOUT_CLOSE"
        elif "manual" in reason.lower():
            comment = "MANUAL_CLOSE"
        elif "trail" in reason.lower():
            comment = "TRAIL_CLOSE"
        elif "runner" in reason.lower():
            comment = "RUNNER"
        else:
            comment = reason[:20] if reason else "CLOSE"  # Limit to 20 chars
        
        cmd = Command(
            fire_id=fire_id,
            ticket=ticket,
            seq=seq,
            cmd_type="CLOSE",
            args={
                "reason": reason,
                "comment": comment
            },
            timestamp_ms=int(time.time() * 1000),
            priority=0,  # High priority for closes
            target_uuid=target_uuid
        )
        
        self.command_queue.put(cmd)
        logger.info(f"Queued CLOSE for ticket {ticket} (reason: {reason}, target: {target_uuid})")
        return True
    
    def start_trail(self, ticket: int, fire_id: str, seq: int,
                   method: str, distance_pips: float) -> bool:
        """Queue a trailing stop activation"""
        # Add comment for trail activation
        comment = f"TRAIL_{int(distance_pips)}PIPS"
        
        cmd = Command(
            fire_id=fire_id,
            ticket=ticket,
            seq=seq,
            cmd_type="START_TRAIL",
            args={
                "method": method,
                "distance_pips": distance_pips,
                "comment": comment
            },
            timestamp_ms=int(time.time() * 1000)
        )
        
        self.command_queue.put(cmd)
        logger.info(f"Queued START_TRAIL ({method}, {distance_pips} pips) for ticket {ticket}")
        return True
    
    def get_command_status(self, fire_id: str, seq: int) -> Optional[Command]:
        """Get status of a sent command"""
        with self.command_lock:
            key = f"{fire_id}:{seq}"
            return self.sent_commands.get(key)
    
    def shutdown(self):
        """Shutdown command bus"""
        self.processing = False
        if self.process_thread:
            self.process_thread.join(timeout=2)
        
        if self.socket:
            self.socket.close()
        self.context.term()

# Singleton instance
command_bus = CommandBus()