"""
BITTEN Onboarding Session Manager

Handles persistence, timeout management, and session lifecycle for onboarding sessions.
Implements 7-day session retention with automatic cleanup.
"""

import json
import logging
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path

from .orchestrator import OnboardingSession

logger = logging.getLogger(__name__)

class OnboardingSessionManager:
    """Manages onboarding session persistence and lifecycle"""
    
    def __init__(self, data_dir: str = "data/onboarding"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Session storage paths
        self.active_sessions_dir = self.data_dir / "active"
        self.archived_sessions_dir = self.data_dir / "archived"
        
        # Create directories
        self.active_sessions_dir.mkdir(exist_ok=True)
        self.archived_sessions_dir.mkdir(exist_ok=True)
        
        # Session retention settings
        self.session_ttl = timedelta(days=7)  # 7-day retention
        self.cleanup_interval = timedelta(hours=1)  # Cleanup every hour
        
        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
        
        logger.info(f"Session manager initialized with data dir: {self.data_dir}")
    
    async def save_session(self, session: OnboardingSession) -> bool:
        """
        Save onboarding session to disk
        
        Args:
            session: Session to save
            
        Returns:
            True if saved successfully
        """
        try:
            session_path = self.active_sessions_dir / f"{session.user_id}.json"
            
            # Convert session to dict
            session_data = session.to_dict()
            
            # Add metadata
            session_data['_metadata'] = {
                'saved_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'schema': 'onboarding_session'
            }
            
            # Write to file atomically
            temp_path = session_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Atomic rename
            temp_path.rename(session_path)
            
            logger.debug(f"Session saved for user {session.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session for user {session.user_id}: {e}")
            return False
    
    async def load_session(self, user_id: str) -> Optional[OnboardingSession]:
        """
        Load onboarding session from disk
        
        Args:
            user_id: User identifier
            
        Returns:
            Session if found, None otherwise
        """
        try:
            session_path = self.active_sessions_dir / f"{user_id}.json"
            
            if not session_path.exists():
                return None
            
            # Load session data
            with open(session_path, 'r') as f:
                session_data = json.load(f)
            
            # Remove metadata
            session_data.pop('_metadata', None)
            
            # Create session object
            session = OnboardingSession.from_dict(session_data)
            
            # Check if session is expired
            if datetime.utcnow() - session.last_activity > self.session_ttl:
                logger.info(f"Session expired for user {user_id}")
                await self.archive_session(user_id)
                return None
            
            logger.debug(f"Session loaded for user {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error loading session for user {user_id}: {e}")
            return None
    
    async def archive_session(self, user_id: str) -> bool:
        """
        Archive completed or expired session
        
        Args:
            user_id: User identifier
            
        Returns:
            True if archived successfully
        """
        try:
            active_path = self.active_sessions_dir / f"{user_id}.json"
            
            if not active_path.exists():
                return False
            
            # Create archive filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            archive_path = self.archived_sessions_dir / f"{user_id}_{timestamp}.json"
            
            # Add archive metadata
            with open(active_path, 'r') as f:
                session_data = json.load(f)
            
            session_data['_archive_metadata'] = {
                'archived_at': datetime.utcnow().isoformat(),
                'reason': 'completed_or_expired'
            }
            
            # Write to archive
            with open(archive_path, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Remove from active
            active_path.unlink()
            
            logger.info(f"Session archived for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error archiving session for user {user_id}: {e}")
            return False
    
    async def delete_session(self, user_id: str) -> bool:
        """
        Delete active session (for restarts)
        
        Args:
            user_id: User identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            session_path = self.active_sessions_dir / f"{user_id}.json"
            
            if session_path.exists():
                session_path.unlink()
                logger.info(f"Session deleted for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting session for user {user_id}: {e}")
            return False
    
    async def get_session_stats(self, user_id: str) -> Dict[str, any]:
        """
        Get session statistics
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with session stats
        """
        try:
            session = await self.load_session(user_id)
            
            if not session:
                return {
                    'exists': False,
                    'message': 'No active session found'
                }
            
            total_states = 14  # Total onboarding states
            completed_count = len(session.completed_states)
            
            # Calculate time spent
            time_spent = datetime.utcnow() - session.started_at
            
            return {
                'exists': True,
                'current_state': session.current_state,
                'progress': {
                    'completed': completed_count,
                    'total': total_states,
                    'percentage': (completed_count / total_states) * 100
                },
                'timing': {
                    'started_at': session.started_at.isoformat(),
                    'last_activity': session.last_activity.isoformat(),
                    'time_spent_minutes': int(time_spent.total_seconds() / 60)
                },
                'user_data': {
                    'has_experience': session.has_experience,
                    'first_name': session.first_name,
                    'selected_theater': session.selected_theater,
                    'callsign': session.callsign,
                    'accepted_terms': session.accepted_terms
                },
                'variant': session.variant
            }
            
        except Exception as e:
            logger.error(f"Error getting session stats for user {user_id}: {e}")
            return {
                'exists': False,
                'error': str(e)
            }
    
    async def get_all_active_sessions(self) -> List[Dict[str, any]]:
        """
        Get all active sessions for monitoring
        
        Returns:
            List of session summaries
        """
        try:
            sessions = []
            
            for session_file in self.active_sessions_dir.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    # Extract key info
                    user_id = session_data.get('user_id')
                    started_at = datetime.fromisoformat(session_data.get('started_at'))
                    last_activity = datetime.fromisoformat(session_data.get('last_activity'))
                    current_state = session_data.get('current_state')
                    completed_states = session_data.get('completed_states', [])
                    
                    sessions.append({
                        'user_id': user_id,
                        'current_state': current_state,
                        'progress': len(completed_states),
                        'started_at': started_at.isoformat(),
                        'last_activity': last_activity.isoformat(),
                        'duration_minutes': int((datetime.utcnow() - started_at).total_seconds() / 60),
                        'idle_minutes': int((datetime.utcnow() - last_activity).total_seconds() / 60)
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing session file {session_file}: {e}")
                    continue
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting all active sessions: {e}")
            return []
    
    async def send_reminders(self) -> int:
        """
        Send reminders to inactive sessions
        
        Returns:
            Number of reminders sent
        """
        try:
            sessions = await self.get_all_active_sessions()
            reminders_sent = 0
            
            for session_info in sessions:
                idle_minutes = session_info['idle_minutes']
                user_id = session_info['user_id']
                
                # Send reminder based on idle time
                if idle_minutes >= 60 and idle_minutes < 120:  # 1 hour
                    await self._send_reminder(user_id, 'one_hour')
                    reminders_sent += 1
                elif idle_minutes >= 1440 and idle_minutes < 1500:  # 24 hours
                    await self._send_reminder(user_id, 'one_day')
                    reminders_sent += 1
                elif idle_minutes >= 10080:  # 7 days
                    await self._send_reminder(user_id, 'final_reminder')
                    reminders_sent += 1
            
            return reminders_sent
            
        except Exception as e:
            logger.error(f"Error sending reminders: {e}")
            return 0
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            cleaned_count = 0
            cutoff_time = datetime.utcnow() - self.session_ttl
            
            for session_file in self.active_sessions_dir.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    last_activity = datetime.fromisoformat(session_data.get('last_activity'))
                    
                    if last_activity < cutoff_time:
                        user_id = session_data.get('user_id')
                        await self.archive_session(user_id)
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing session file {session_file}: {e}")
                    continue
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired sessions")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    async def _send_reminder(self, user_id: str, reminder_type: str):
        """Send reminder message to user"""
        try:
            # This would integrate with the telegram system
            # For now, just log the reminder
            logger.info(f"Sending {reminder_type} reminder to user {user_id}")
            
            # TODO: Integrate with telegram_router to send actual reminders
            
        except Exception as e:
            logger.error(f"Error sending reminder to user {user_id}: {e}")
    
    def _start_cleanup_task(self):
        """Start the background cleanup task"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Cleanup task started")
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                
                # Clean up expired sessions
                await self.cleanup_expired_sessions()
                
                # Send reminders
                await self.send_reminders()
                
            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    def stop_cleanup_task(self):
        """Stop the background cleanup task"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            logger.info("Cleanup task stopped")
    
    def __del__(self):
        """Cleanup on destruction"""
        self.stop_cleanup_task()