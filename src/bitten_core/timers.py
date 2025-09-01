#!/usr/bin/env python3
"""
Timer system for position management
Handles time-boxed exits and position lifecycle timing
"""

import time
import threading
from typing import Dict, Optional, Callable
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Timer:
    """Position timer"""
    ticket: int
    fire_id: str
    expiry_time: float
    callback: Callable
    reason: str
    cancelled: bool = False

class TimerManager:
    """
    Manages position timers for time-boxed exits
    """
    
    def __init__(self):
        self.timers: Dict[int, Timer] = {}  # ticket -> Timer
        self.timer_lock = threading.RLock()
        self.check_thread = None
        self.running = False
        self._start_checker()
    
    def _start_checker(self):
        """Start timer checker thread"""
        self.running = True
        self.check_thread = threading.Thread(target=self._check_timers)
        self.check_thread.daemon = True
        self.check_thread.start()
        logger.info("Timer manager started")
    
    def _check_timers(self):
        """Check for expired timers"""
        while self.running:
            try:
                current_time = time.time()
                expired = []
                
                with self.timer_lock:
                    for ticket, timer in self.timers.items():
                        if not timer.cancelled and current_time >= timer.expiry_time:
                            expired.append(timer)
                
                # Execute callbacks outside lock
                for timer in expired:
                    try:
                        logger.info(f"Timer expired for ticket {timer.ticket}: {timer.reason}")
                        timer.callback(timer.ticket, timer.fire_id, timer.reason)
                        
                        # Remove expired timer
                        with self.timer_lock:
                            if timer.ticket in self.timers:
                                del self.timers[timer.ticket]
                                
                    except Exception as e:
                        logger.error(f"Timer callback failed for {timer.ticket}: {e}")
                
                # Sleep briefly
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Timer check error: {e}")
                time.sleep(1)
    
    def set_timer(self, ticket: int, fire_id: str, duration_seconds: float,
                 callback: Callable, reason: str = "MAX_HOLD") -> bool:
        """
        Set a timer for a position
        
        Args:
            ticket: Position ticket
            fire_id: Fire ID
            duration_seconds: Timer duration in seconds
            callback: Function to call when timer expires (ticket, fire_id, reason)
            reason: Reason for timer expiry
        
        Returns:
            Success status
        """
        with self.timer_lock:
            if ticket in self.timers:
                logger.warning(f"Timer already exists for ticket {ticket}")
                return False
            
            expiry_time = time.time() + duration_seconds
            
            timer = Timer(
                ticket=ticket,
                fire_id=fire_id,
                expiry_time=expiry_time,
                callback=callback,
                reason=reason
            )
            
            self.timers[ticket] = timer
            
            logger.info(f"Set timer for ticket {ticket}: {duration_seconds}s ({reason})")
            return True
    
    def cancel_timer(self, ticket: int) -> bool:
        """Cancel a timer for a position"""
        with self.timer_lock:
            if ticket in self.timers:
                self.timers[ticket].cancelled = True
                del self.timers[ticket]
                logger.info(f"Cancelled timer for ticket {ticket}")
                return True
            return False
    
    def get_remaining_time(self, ticket: int) -> Optional[float]:
        """Get remaining time for a timer in seconds"""
        with self.timer_lock:
            timer = self.timers.get(ticket)
            if timer and not timer.cancelled:
                remaining = timer.expiry_time - time.time()
                return max(0, remaining)
            return None
    
    def extend_timer(self, ticket: int, additional_seconds: float) -> bool:
        """Extend an existing timer"""
        with self.timer_lock:
            timer = self.timers.get(ticket)
            if timer and not timer.cancelled:
                timer.expiry_time += additional_seconds
                logger.info(f"Extended timer for ticket {ticket} by {additional_seconds}s")
                return True
            return False
    
    def reset_timer(self, ticket: int, new_duration_seconds: float) -> bool:
        """Reset timer to new duration from now"""
        with self.timer_lock:
            timer = self.timers.get(ticket)
            if timer and not timer.cancelled:
                timer.expiry_time = time.time() + new_duration_seconds
                logger.info(f"Reset timer for ticket {ticket} to {new_duration_seconds}s")
                return True
            return False
    
    def get_active_timers(self) -> Dict[int, Dict]:
        """Get all active timers with their status"""
        with self.timer_lock:
            active = {}
            current_time = time.time()
            
            for ticket, timer in self.timers.items():
                if not timer.cancelled:
                    active[ticket] = {
                        "fire_id": timer.fire_id,
                        "remaining_seconds": max(0, timer.expiry_time - current_time),
                        "reason": timer.reason
                    }
            
            return active
    
    def shutdown(self):
        """Shutdown timer manager"""
        self.running = False
        if self.check_thread:
            self.check_thread.join(timeout=2)
        logger.info("Timer manager shutdown")

# Singleton instance
timer_manager = TimerManager()

class PositionTimer:
    """
    Helper class for managing position-specific timers
    """
    
    @staticmethod
    def set_max_hold_timer(ticket: int, fire_id: str, tier: str, 
                          callback: Callable) -> bool:
        """Set max hold timer based on tier configuration"""
        import toml
        from pathlib import Path
        
        # Load tier config
        config_path = Path("/root/HydraX-v2/config/tiers.toml")
        if config_path.exists():
            config = toml.load(config_path)
            tier_config = config.get(tier, {})
            max_hold_min = tier_config.get("MAX_HOLD_MIN", 90)
        else:
            max_hold_min = 90  # Default 90 minutes
        
        duration_seconds = max_hold_min * 60
        
        return timer_manager.set_timer(
            ticket=ticket,
            fire_id=fire_id,
            duration_seconds=duration_seconds,
            callback=callback,
            reason=f"MAX_HOLD_{max_hold_min}MIN"
        )
    
    @staticmethod
    def cancel_position_timer(ticket: int) -> bool:
        """Cancel timer for a position"""
        return timer_manager.cancel_timer(ticket)
    
    @staticmethod
    def get_time_remaining(ticket: int) -> Optional[float]:
        """Get remaining time for position in seconds"""
        return timer_manager.get_remaining_time(ticket)

# New timeout metadata helpers for persistent storage
import sqlite3
import os

DB = os.getenv("BITTEN_DB_PATH", "/root/HydraX-v2/bitten.db")

def set_timeout_meta(ticket: int, open_ts_utc: str, max_hold_min: int):
    """Store timeout metadata in persistent database"""
    with sqlite3.connect(DB) as cx:
        cx.execute("INSERT OR REPLACE INTO position_meta(ticket,open_ts_utc,pre_tp1_max_hold_min) VALUES(?,?,?)",
                   (ticket, open_ts_utc, int(max_hold_min)))

def get_timeout_meta(ticket: int):
    """Retrieve timeout metadata from database"""
    with sqlite3.connect(DB) as cx:
        row = cx.execute("SELECT open_ts_utc, pre_tp1_max_hold_min FROM position_meta WHERE ticket=?",
                         (ticket,)).fetchone()
        return {"open_ts_utc": row[0], "pre_tp1_max_hold_min": row[1]} if row else None

def clear_timeout_meta(ticket: int):
    """Remove timeout metadata after TP1 or position close"""
    with sqlite3.connect(DB) as cx:
        cx.execute("DELETE FROM position_meta WHERE ticket=?", (ticket,))