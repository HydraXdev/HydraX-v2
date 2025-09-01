#!/usr/bin/env python3
"""
State store for position management with idempotency and thread safety
Tracks position lifecycle and prevents duplicate operations
"""

import json
import time
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, Set, Any
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PositionState(Enum):
    """Position lifecycle states"""
    ENTERED = "entered"
    TP1_DONE = "tp1_done"
    BE_SET = "be_set"
    TRAILING = "trailing"
    CLOSED = "closed"

@dataclass
class Position:
    """Position tracking data"""
    ticket: int
    fire_id: str
    user_id: str
    user_tier: str
    symbol: str
    direction: str
    entry_px: float
    sl_init_px: float
    sl_current_px: float
    tp_px: float
    r_pips: float
    lot_size: float
    lot_remaining: float
    state: PositionState = PositionState.ENTERED
    tp1_done: bool = False
    be_set: bool = False
    trail_on: bool = False
    open_ts: float = field(default_factory=time.time)
    last_update_ts: float = field(default_factory=time.time)
    milestones_hit: Set[str] = field(default_factory=set)
    commands_sent: Dict[str, int] = field(default_factory=dict)  # cmd_type -> seq
    last_seq: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['state'] = self.state.value
        data['milestones_hit'] = list(self.milestones_hit)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Position':
        """Create from dictionary"""
        data['state'] = PositionState(data['state'])
        data['milestones_hit'] = set(data.get('milestones_hit', []))
        return cls(**data)

class StateStore:
    """
    Thread-safe state store for position management
    Provides idempotency and prevents race conditions
    """
    
    def __init__(self, persist_path: str = "/root/HydraX-v2/data/position_state.json"):
        self.positions: Dict[int, Position] = {}  # ticket -> Position
        self.locks: Dict[int, threading.RLock] = {}  # ticket -> lock
        self.global_lock = threading.RLock()
        self.persist_path = Path(persist_path)
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load persisted state
        self._load_state()
        
        # Track sequence numbers globally
        self.global_seq = 0
        
    def _load_state(self):
        """Load persisted state from disk"""
        if self.persist_path.exists():
            try:
                with open(self.persist_path, 'r') as f:
                    data = json.load(f)
                    for ticket_str, pos_data in data.get('positions', {}).items():
                        ticket = int(ticket_str)
                        self.positions[ticket] = Position.from_dict(pos_data)
                        self.locks[ticket] = threading.RLock()
                    self.global_seq = data.get('global_seq', 0)
                logger.info(f"Loaded {len(self.positions)} positions from state")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
    
    def _save_state(self):
        """Persist state to disk"""
        try:
            data = {
                'positions': {
                    str(ticket): pos.to_dict() 
                    for ticket, pos in self.positions.items()
                },
                'global_seq': self.global_seq,
                'timestamp': time.time()
            }
            
            # Write atomically
            temp_path = self.persist_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            temp_path.replace(self.persist_path)
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def with_ticket_lock(self, ticket: int):
        """Decorator for operations that need ticket-level locking"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                lock = self.get_or_create_lock(ticket)
                with lock:
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_or_create_lock(self, ticket: int) -> threading.RLock:
        """Get or create a lock for a ticket"""
        with self.global_lock:
            if ticket not in self.locks:
                self.locks[ticket] = threading.RLock()
            return self.locks[ticket]
    
    def create_position(self, ticket: int, fire_id: str, user_id: str, 
                       user_tier: str, symbol: str, direction: str,
                       entry_px: float, sl_px: float, tp_px: float,
                       r_pips: float, lot_size: float) -> Position:
        """Create a new position with thread safety"""
        with self.global_lock:
            if ticket in self.positions:
                logger.warning(f"Position {ticket} already exists")
                return self.positions[ticket]
            
            pos = Position(
                ticket=ticket,
                fire_id=fire_id,
                user_id=user_id,
                user_tier=user_tier,
                symbol=symbol,
                direction=direction,
                entry_px=entry_px,
                sl_init_px=sl_px,
                sl_current_px=sl_px,
                tp_px=tp_px,
                r_pips=r_pips,
                lot_size=lot_size,
                lot_remaining=lot_size
            )
            
            self.positions[ticket] = pos
            self.locks[ticket] = threading.RLock()
            self._save_state()
            
            logger.info(f"Created position {ticket}: {symbol} {direction} @ {entry_px}")
            return pos
    
    def get_position(self, ticket: int) -> Optional[Position]:
        """Get position by ticket"""
        return self.positions.get(ticket)
    
    def update_position(self, ticket: int, **updates) -> bool:
        """Update position with thread safety"""
        lock = self.get_or_create_lock(ticket)
        with lock:
            pos = self.positions.get(ticket)
            if not pos:
                logger.error(f"Position {ticket} not found")
                return False
            
            # Update fields
            for key, value in updates.items():
                if hasattr(pos, key):
                    setattr(pos, key, value)
            
            pos.last_update_ts = time.time()
            self._save_state()
            return True
    
    def check_milestone_idempotent(self, ticket: int, milestone: str) -> bool:
        """
        Check if a milestone can be executed (idempotent)
        Returns True if milestone hasn't been hit yet
        """
        lock = self.get_or_create_lock(ticket)
        with lock:
            pos = self.positions.get(ticket)
            if not pos:
                return False
            
            if milestone in pos.milestones_hit:
                logger.info(f"Milestone {milestone} already hit for {ticket}")
                return False
            
            # Mark milestone as hit
            pos.milestones_hit.add(milestone)
            self._save_state()
            return True
    
    def get_next_seq(self, ticket: int) -> int:
        """Get next sequence number for a ticket"""
        lock = self.get_or_create_lock(ticket)
        with lock:
            self.global_seq += 1
            
            pos = self.positions.get(ticket)
            if pos:
                pos.last_seq = self.global_seq
                self._save_state()
            
            return self.global_seq
    
    def record_command(self, ticket: int, cmd_type: str, seq: int):
        """Record that a command was sent"""
        lock = self.get_or_create_lock(ticket)
        with lock:
            pos = self.positions.get(ticket)
            if pos:
                pos.commands_sent[cmd_type] = seq
                pos.last_update_ts = time.time()
                self._save_state()
    
    def close_position(self, ticket: int):
        """Mark position as closed"""
        lock = self.get_or_create_lock(ticket)
        with lock:
            pos = self.positions.get(ticket)
            if pos:
                pos.state = PositionState.CLOSED
                pos.last_update_ts = time.time()
                self._save_state()
                logger.info(f"Closed position {ticket}")
    
    def get_active_positions(self, user_id: Optional[str] = None) -> Dict[int, Position]:
        """Get all active (non-closed) positions"""
        with self.global_lock:
            active = {}
            for ticket, pos in self.positions.items():
                if pos.state != PositionState.CLOSED:
                    if user_id is None or pos.user_id == user_id:
                        active[ticket] = pos
            return active
    
    def cleanup_old_positions(self, max_age_hours: int = 24):
        """Remove closed positions older than max_age"""
        with self.global_lock:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            to_remove = []
            for ticket, pos in self.positions.items():
                if pos.state == PositionState.CLOSED:
                    age = current_time - pos.last_update_ts
                    if age > max_age_seconds:
                        to_remove.append(ticket)
            
            for ticket in to_remove:
                del self.positions[ticket]
                if ticket in self.locks:
                    del self.locks[ticket]
            
            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old positions")
                self._save_state()

# Singleton instance
state_store = StateStore()