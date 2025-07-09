"""
Terminal Assignment Manager for MT5 Bridge Connections

This module manages user-to-bridge assignments for MT5 terminals, tracking which users
are assigned to which terminals and storing bridge connection details.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
from pathlib import Path
import threading
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)


class TerminalType(Enum):
    """Enumeration of MT5 terminal types"""
    PRESS_PASS = "press_pass"
    DEMO = "demo"
    LIVE = "live"


class TerminalStatus(Enum):
    """Enumeration of terminal assignment statuses"""
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class TerminalAssignment:
    """Manages user-to-bridge assignments for MT5 terminals"""
    
    def __init__(self, db_path: str = "terminal_assignments.db"):
        """
        Initialize the Terminal Assignment Manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
        
    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create terminals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terminals (
                    terminal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    terminal_name TEXT UNIQUE NOT NULL,
                    terminal_type TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    folder_path TEXT NOT NULL,
                    status TEXT DEFAULT 'available',
                    max_users INTEGER DEFAULT 1,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create assignments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    terminal_id INTEGER NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    released_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    metadata TEXT,
                    FOREIGN KEY (terminal_id) REFERENCES terminals (terminal_id),
                    UNIQUE(user_id, terminal_id, is_active)
                )
            """)
            
            # Create assignment history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assignment_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    terminal_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Create indices for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignments_user ON assignments(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignments_terminal ON assignments(terminal_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignments_active ON assignments(is_active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_user ON assignment_history(user_id)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def add_terminal(self, terminal_name: str, terminal_type: TerminalType,
                    ip_address: str, port: int, folder_path: str,
                    max_users: int = 1, metadata: Optional[Dict] = None) -> int:
        """
        Add a new terminal to the system
        
        Args:
            terminal_name: Unique name for the terminal
            terminal_type: Type of terminal (press_pass, demo, live)
            ip_address: IP address of the bridge
            port: Port number for the bridge connection
            folder_path: Path to the MT5 terminal folder
            max_users: Maximum number of users that can be assigned to this terminal
            metadata: Additional metadata as dictionary
            
        Returns:
            Terminal ID of the newly added terminal
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                metadata_json = json.dumps(metadata) if metadata else None
                
                cursor.execute("""
                    INSERT INTO terminals (terminal_name, terminal_type, ip_address, 
                                         port, folder_path, max_users, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (terminal_name, terminal_type.value, ip_address, port, 
                     folder_path, max_users, metadata_json))
                
                conn.commit()
                return cursor.lastrowid
    
    def assign_terminal(self, user_id: str, terminal_type: TerminalType,
                       preferred_terminal_id: Optional[int] = None,
                       metadata: Optional[Dict] = None) -> Optional[Dict]:
        """
        Assign a terminal to a user
        
        Args:
            user_id: User identifier
            terminal_type: Type of terminal requested
            preferred_terminal_id: Optional specific terminal to assign
            metadata: Additional metadata for the assignment
            
        Returns:
            Dictionary with assignment details or None if no terminal available
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user already has an active assignment of this type
                cursor.execute("""
                    SELECT a.*, t.* FROM assignments a
                    JOIN terminals t ON a.terminal_id = t.terminal_id
                    WHERE a.user_id = ? AND a.is_active = 1 AND t.terminal_type = ?
                """, (user_id, terminal_type.value))
                
                existing = cursor.fetchone()
                if existing:
                    return self._row_to_assignment_dict(existing)
                
                # Find available terminal
                if preferred_terminal_id:
                    cursor.execute("""
                        SELECT * FROM terminals 
                        WHERE terminal_id = ? AND terminal_type = ? AND status = ?
                    """, (preferred_terminal_id, terminal_type.value, TerminalStatus.AVAILABLE.value))
                else:
                    cursor.execute("""
                        SELECT t.* FROM terminals t
                        LEFT JOIN (
                            SELECT terminal_id, COUNT(*) as active_users
                            FROM assignments
                            WHERE is_active = 1
                            GROUP BY terminal_id
                        ) a ON t.terminal_id = a.terminal_id
                        WHERE t.terminal_type = ? AND t.status = ?
                        AND (a.active_users IS NULL OR a.active_users < t.max_users)
                        ORDER BY COALESCE(a.active_users, 0) ASC
                        LIMIT 1
                    """, (terminal_type.value, TerminalStatus.AVAILABLE.value))
                
                terminal = cursor.fetchone()
                if not terminal:
                    return None
                
                # Create assignment
                metadata_json = json.dumps(metadata) if metadata else None
                cursor.execute("""
                    INSERT INTO assignments (user_id, terminal_id, metadata)
                    VALUES (?, ?, ?)
                """, (user_id, terminal['terminal_id'], metadata_json))
                
                assignment_id = cursor.lastrowid
                
                # Log to history
                cursor.execute("""
                    INSERT INTO assignment_history (user_id, terminal_id, action, metadata)
                    VALUES (?, ?, 'assigned', ?)
                """, (user_id, terminal['terminal_id'], metadata_json))
                
                conn.commit()
                
                # Return assignment details
                return {
                    'assignment_id': assignment_id,
                    'user_id': user_id,
                    'terminal_id': terminal['terminal_id'],
                    'terminal_name': terminal['terminal_name'],
                    'terminal_type': terminal['terminal_type'],
                    'ip_address': terminal['ip_address'],
                    'port': terminal['port'],
                    'folder_path': terminal['folder_path'],
                    'assigned_at': datetime.now().isoformat()
                }
    
    def get_user_assignments(self, user_id: str, active_only: bool = True) -> List[Dict]:
        """
        Get all terminal assignments for a user
        
        Args:
            user_id: User identifier
            active_only: Whether to return only active assignments
            
        Returns:
            List of assignment dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT a.*, t.* FROM assignments a
                JOIN terminals t ON a.terminal_id = t.terminal_id
                WHERE a.user_id = ?
            """
            
            if active_only:
                query += " AND a.is_active = 1"
                
            cursor.execute(query, (user_id,))
            
            return [self._row_to_assignment_dict(row) for row in cursor.fetchall()]
    
    def get_terminal_assignments(self, terminal_id: int, active_only: bool = True) -> List[Dict]:
        """
        Get all user assignments for a terminal
        
        Args:
            terminal_id: Terminal identifier
            active_only: Whether to return only active assignments
            
        Returns:
            List of assignment dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT a.*, t.* FROM assignments a
                JOIN terminals t ON a.terminal_id = t.terminal_id
                WHERE a.terminal_id = ?
            """
            
            if active_only:
                query += " AND a.is_active = 1"
                
            cursor.execute(query, (terminal_id,))
            
            return [self._row_to_assignment_dict(row) for row in cursor.fetchall()]
    
    def release_terminal(self, user_id: str, terminal_id: Optional[int] = None,
                        terminal_type: Optional[TerminalType] = None) -> bool:
        """
        Release a terminal assignment for a user
        
        Args:
            user_id: User identifier
            terminal_id: Specific terminal to release
            terminal_type: Type of terminal to release (if terminal_id not specified)
            
        Returns:
            True if successfully released, False otherwise
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if terminal_id:
                    cursor.execute("""
                        UPDATE assignments 
                        SET is_active = 0, released_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND terminal_id = ? AND is_active = 1
                    """, (user_id, terminal_id))
                elif terminal_type:
                    cursor.execute("""
                        UPDATE assignments
                        SET is_active = 0, released_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND is_active = 1
                        AND terminal_id IN (
                            SELECT terminal_id FROM terminals 
                            WHERE terminal_type = ?
                        )
                    """, (user_id, terminal_type.value))
                else:
                    # Release all active assignments for the user
                    cursor.execute("""
                        UPDATE assignments 
                        SET is_active = 0, released_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND is_active = 1
                    """, (user_id,))
                
                released_count = cursor.rowcount
                
                if released_count > 0:
                    # Log releases to history
                    if terminal_id:
                        cursor.execute("""
                            INSERT INTO assignment_history (user_id, terminal_id, action)
                            VALUES (?, ?, 'released')
                        """, (user_id, terminal_id))
                    else:
                        cursor.execute("""
                            INSERT INTO assignment_history (user_id, terminal_id, action)
                            SELECT ?, terminal_id, 'released' FROM assignments
                            WHERE user_id = ? AND released_at = (
                                SELECT MAX(released_at) FROM assignments WHERE user_id = ?
                            )
                        """, (user_id, user_id, user_id))
                
                conn.commit()
                return released_count > 0
    
    def update_terminal_status(self, terminal_id: int, status: TerminalStatus) -> bool:
        """
        Update the status of a terminal
        
        Args:
            terminal_id: Terminal identifier
            status: New status for the terminal
            
        Returns:
            True if successfully updated, False otherwise
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE terminals 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE terminal_id = ?
                """, (status.value, terminal_id))
                
                conn.commit()
                return cursor.rowcount > 0
    
    def get_terminal_info(self, terminal_id: int) -> Optional[Dict]:
        """
        Get detailed information about a terminal
        
        Args:
            terminal_id: Terminal identifier
            
        Returns:
            Dictionary with terminal details or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT t.*, 
                       COUNT(CASE WHEN a.is_active = 1 THEN 1 END) as active_users
                FROM terminals t
                LEFT JOIN assignments a ON t.terminal_id = a.terminal_id
                WHERE t.terminal_id = ?
                GROUP BY t.terminal_id
            """, (terminal_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_available_terminals(self, terminal_type: Optional[TerminalType] = None) -> List[Dict]:
        """
        Get list of available terminals
        
        Args:
            terminal_type: Optional filter by terminal type
            
        Returns:
            List of available terminal dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT t.*, 
                       COALESCE(a.active_users, 0) as active_users,
                       (t.max_users - COALESCE(a.active_users, 0)) as available_slots
                FROM terminals t
                LEFT JOIN (
                    SELECT terminal_id, COUNT(*) as active_users
                    FROM assignments
                    WHERE is_active = 1
                    GROUP BY terminal_id
                ) a ON t.terminal_id = a.terminal_id
                WHERE t.status = ? AND (t.max_users - COALESCE(a.active_users, 0)) > 0
            """
            
            params = [TerminalStatus.AVAILABLE.value]
            
            if terminal_type:
                query += " AND t.terminal_type = ?"
                params.append(terminal_type.value)
                
            cursor.execute(query, params)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_assignment_history(self, user_id: Optional[str] = None,
                              terminal_id: Optional[int] = None,
                              limit: int = 100) -> List[Dict]:
        """
        Get assignment history
        
        Args:
            user_id: Optional filter by user
            terminal_id: Optional filter by terminal
            limit: Maximum number of records to return
            
        Returns:
            List of history records
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT h.*, t.terminal_name, t.terminal_type
                FROM assignment_history h
                JOIN terminals t ON h.terminal_id = t.terminal_id
                WHERE 1=1
            """
            
            params = []
            
            if user_id:
                query += " AND h.user_id = ?"
                params.append(user_id)
                
            if terminal_id:
                query += " AND h.terminal_id = ?"
                params.append(terminal_id)
                
            query += " ORDER BY h.timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_stale_assignments(self, hours: int = 24) -> int:
        """
        Clean up assignments that have been active for too long
        
        Args:
            hours: Number of hours after which an assignment is considered stale
            
        Returns:
            Number of assignments cleaned up
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE assignments
                    SET is_active = 0, released_at = CURRENT_TIMESTAMP
                    WHERE is_active = 1 
                    AND datetime(assigned_at, '+' || ? || ' hours') < datetime('now')
                """, (hours,))
                
                cleaned = cursor.rowcount
                
                if cleaned > 0:
                    cursor.execute("""
                        INSERT INTO assignment_history (user_id, terminal_id, action, metadata)
                        SELECT user_id, terminal_id, 'auto_released', 
                               json_object('reason', 'stale_assignment', 'hours', ?)
                        FROM assignments
                        WHERE released_at = (SELECT MAX(released_at) FROM assignments)
                    """, (hours,))
                
                conn.commit()
                return cleaned
    
    def _row_to_assignment_dict(self, row: sqlite3.Row) -> Dict:
        """Convert a database row to assignment dictionary"""
        result = dict(row)
        
        # Parse JSON metadata if present
        if 'metadata' in result and result['metadata']:
            try:
                result['metadata'] = json.loads(result['metadata'])
            except json.JSONDecodeError:
                pass
                
        return result
    
    def get_statistics(self) -> Dict:
        """
        Get overall statistics about terminal assignments
        
        Returns:
            Dictionary with statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total terminals by type
            cursor.execute("""
                SELECT terminal_type, COUNT(*) as count
                FROM terminals
                GROUP BY terminal_type
            """)
            stats['terminals_by_type'] = dict(cursor.fetchall())
            
            # Active assignments by type
            cursor.execute("""
                SELECT t.terminal_type, COUNT(*) as count
                FROM assignments a
                JOIN terminals t ON a.terminal_id = t.terminal_id
                WHERE a.is_active = 1
                GROUP BY t.terminal_type
            """)
            stats['active_assignments_by_type'] = dict(cursor.fetchall())
            
            # Terminal utilization
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT t.terminal_id) as total_terminals,
                    COUNT(DISTINCT CASE WHEN a.is_active = 1 THEN t.terminal_id END) as used_terminals,
                    SUM(t.max_users) as total_capacity,
                    COUNT(CASE WHEN a.is_active = 1 THEN 1 END) as used_capacity
                FROM terminals t
                LEFT JOIN assignments a ON t.terminal_id = a.terminal_id
                WHERE t.status = ?
            """, (TerminalStatus.AVAILABLE.value,))
            
            utilization = cursor.fetchone()
            stats['utilization'] = dict(utilization)
            
            return stats


# Example usage
if __name__ == "__main__":
    # Initialize the terminal assignment manager
    manager = TerminalAssignment()
    
    # Add some example terminals
    press_pass_id = manager.add_terminal(
        terminal_name="PP-Terminal-01",
        terminal_type=TerminalType.PRESS_PASS,
        ip_address="192.168.1.100",
        port=5000,
        folder_path="/mt5/terminals/press_pass_01",
        max_users=10,
        metadata={"region": "US-East", "version": "5.0.36"}
    )
    
    demo_id = manager.add_terminal(
        terminal_name="Demo-Terminal-01",
        terminal_type=TerminalType.DEMO,
        ip_address="192.168.1.101",
        port=5001,
        folder_path="/mt5/terminals/demo_01",
        max_users=5,
        metadata={"region": "US-East", "version": "5.0.36"}
    )
    
    # Assign a terminal to a user
    assignment = manager.assign_terminal(
        user_id="user123",
        terminal_type=TerminalType.PRESS_PASS,
        metadata={"session_type": "training"}
    )
    
    if assignment:
        print(f"Assigned terminal: {assignment}")
    
    # Get user assignments
    user_assignments = manager.get_user_assignments("user123")
    print(f"User assignments: {user_assignments}")
    
    # Get available terminals
    available = manager.get_available_terminals(TerminalType.PRESS_PASS)
    print(f"Available terminals: {available}")
    
    # Get statistics
    stats = manager.get_statistics()
    print(f"Statistics: {stats}")