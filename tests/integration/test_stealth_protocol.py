"""
Integration tests for Stealth Protocol functionality.
Tests stealth mode operations, visibility controls, and integration.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import asyncio
from datetime import datetime, timedelta
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from bitten_core.stealth_protocol import StealthProtocol
from bitten_core.stealth_integration import StealthIntegration
from bitten_core.database.connection import get_db_connection


class TestStealthProtocolIntegration(unittest.TestCase):
    """Test Stealth Protocol integration and functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.user_id = 123456789
        self.stealth_protocol = StealthProtocol()
        self.stealth_integration = StealthIntegration()
        
        # Mock database
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_stealth_mode_activation(self, mock_get_db):
        """Test stealth mode activation and deactivation"""
        mock_get_db.return_value = self.mock_db
        
        # Mock user has access
        self.mock_cursor.fetchone.return_value = (self.user_id, 'elite', True)
        
        # Activate stealth mode
        result = await self.stealth_protocol.activate_stealth(self.user_id)
        
        # Verify activation
        self.assertTrue(result['success'])
        self.assertTrue(result['stealth_active'])
        
        # Verify database update
        update_calls = [call for call in self.mock_cursor.execute.call_args_list
                       if 'UPDATE' in str(call)]
        self.assertGreater(len(update_calls), 0)
        
        # Deactivate stealth mode
        result = await self.stealth_protocol.deactivate_stealth(self.user_id)
        
        # Verify deactivation
        self.assertTrue(result['success'])
        self.assertFalse(result['stealth_active'])
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_stealth_visibility_controls(self, mock_get_db):
        """Test stealth mode visibility controls"""
        mock_get_db.return_value = self.mock_db
        
        # Set up stealth active user
        self.mock_cursor.fetchone.return_value = (
            self.user_id, 'elite', True, True  # stealth_active = True
        )
        
        # Test visibility check
        is_visible = await self.stealth_protocol.is_user_visible(self.user_id)
        self.assertFalse(is_visible)
        
        # Test getting visible users (should exclude stealth users)
        self.mock_cursor.fetchall.return_value = [
            (111, 'user1', False),  # Not in stealth
            (222, 'user2', True),   # In stealth
            (333, 'user3', False),  # Not in stealth
        ]
        
        visible_users = await self.stealth_protocol.get_visible_users()
        
        # Should only include non-stealth users
        visible_ids = [user[0] for user in visible_users]
        self.assertIn(111, visible_ids)
        self.assertNotIn(222, visible_ids)
        self.assertIn(333, visible_ids)
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_stealth_signal_filtering(self, mock_get_db):
        """Test that signals are filtered based on stealth status"""
        mock_get_db.return_value = self.mock_db
        
        # Mock stealth user
        self.mock_cursor.fetchone.return_value = (self.user_id, True)
        
        # Create test signal
        signal = {
            'user_id': self.user_id,
            'pair': 'EURUSD',
            'action': 'BUY',
            'timestamp': datetime.now()
        }
        
        # Filter signal through stealth
        filtered = await self.stealth_integration.filter_signal(signal)
        
        # Stealth user's signal should be marked
        self.assertTrue(filtered.get('stealth_mode', False))
        self.assertIn('hidden', filtered.get('visibility', '').lower())
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_stealth_leaderboard_exclusion(self, mock_get_db):
        """Test that stealth users are excluded from leaderboards"""
        mock_get_db.return_value = self.mock_db
        
        # Mock leaderboard data with stealth users
        self.mock_cursor.fetchall.return_value = [
            (111, 'user1', 1000, False),  # Not stealth
            (222, 'user2', 2000, True),   # Stealth
            (333, 'user3', 1500, False),  # Not stealth
            (self.user_id, 'test_user', 3000, True),  # Stealth
        ]
        
        # Get leaderboard
        leaderboard = await self.stealth_integration.get_public_leaderboard()
        
        # Verify stealth users are excluded
        user_ids = [entry['user_id'] for entry in leaderboard]
        self.assertIn(111, user_ids)
        self.assertNotIn(222, user_ids)
        self.assertIn(333, user_ids)
        self.assertNotIn(self.user_id, user_ids)
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_stealth_tier_requirements(self, mock_get_db):
        """Test that stealth mode requires proper tier"""
        mock_get_db.return_value = self.mock_db
        
        # Test with different tiers
        test_cases = [
            ('press_pass', False),  # No access
            ('starter', False),     # No access
            ('sniper', True),       # Has access
            ('elite', True),        # Has access
            ('legend', True),       # Has access
        ]
        
        for tier, should_have_access in test_cases:
            # Mock user tier
            self.mock_cursor.fetchone.return_value = (self.user_id, tier, False)
            
            # Try to activate stealth
            result = await self.stealth_protocol.activate_stealth(self.user_id)
            
            if should_have_access:
                self.assertTrue(result['success'], 
                              f"Tier {tier} should have stealth access")
            else:
                self.assertFalse(result['success'], 
                               f"Tier {tier} should not have stealth access")
                self.assertIn('not available', result['message'].lower())
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_stealth_activity_logging(self, mock_get_db):
        """Test that stealth mode activities are properly logged"""
        mock_get_db.return_value = self.mock_db
        
        # Mock user with stealth access
        self.mock_cursor.fetchone.return_value = (self.user_id, 'elite', False)
        
        # Activate stealth
        await self.stealth_protocol.activate_stealth(self.user_id)
        
        # Check for activity log
        log_calls = [call for call in self.mock_cursor.execute.call_args_list
                    if 'stealth_activity_log' in str(call)]
        
        self.assertGreater(len(log_calls), 0, "Stealth activation should be logged")
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_stealth_stats_tracking(self, mock_get_db):
        """Test that stealth mode tracks separate statistics"""
        mock_get_db.return_value = self.mock_db
        
        # Mock stealth active user
        self.mock_cursor.fetchone.return_value = (self.user_id, True, 10, 8)  # stealth_trades, stealth_wins
        
        # Get stealth stats
        stats = await self.stealth_protocol.get_stealth_stats(self.user_id)
        
        # Verify stats
        self.assertEqual(stats['stealth_trades'], 10)
        self.assertEqual(stats['stealth_wins'], 8)
        self.assertEqual(stats['stealth_win_rate'], 80.0)
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_stealth_notification_suppression(self, mock_get_db):
        """Test that notifications are suppressed in stealth mode"""
        mock_get_db.return_value = self.mock_db
        
        # Mock stealth user
        self.mock_cursor.fetchone.return_value = (self.user_id, True)
        
        # Create notification
        notification = {
            'user_id': self.user_id,
            'type': 'trade_alert',
            'message': 'Trade executed'
        }
        
        # Check if notification should be sent
        should_send = await self.stealth_integration.should_send_notification(notification)
        
        # Stealth users should have suppressed public notifications
        self.assertFalse(should_send)
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_stealth_profile_privacy(self, mock_get_db):
        """Test that stealth mode protects profile information"""
        mock_get_db.return_value = self.mock_db
        
        # Mock stealth user profile
        self.mock_cursor.fetchone.return_value = (
            self.user_id, 'StealthUser', 'elite', True, 'Hidden'
        )
        
        # Get public profile
        profile = await self.stealth_integration.get_public_profile(self.user_id)
        
        # Verify sensitive info is hidden
        self.assertEqual(profile.get('username'), 'Anonymous')
        self.assertEqual(profile.get('status'), 'Hidden')
        self.assertNotIn('trades', profile)
        self.assertNotIn('profit', profile)
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_stealth_cooldown_period(self, mock_get_db):
        """Test stealth mode cooldown between activations"""
        mock_get_db.return_value = self.mock_db
        
        # Mock recent stealth deactivation
        last_deactivation = datetime.now() - timedelta(hours=23)  # Less than 24h ago
        self.mock_cursor.fetchone.return_value = (
            self.user_id, 'elite', False, last_deactivation
        )
        
        # Try to activate stealth
        result = await self.stealth_protocol.activate_stealth(self.user_id)
        
        # Should fail due to cooldown
        self.assertFalse(result['success'])
        self.assertIn('cooldown', result['message'].lower())
        
        # Mock deactivation more than 24h ago
        last_deactivation = datetime.now() - timedelta(hours=25)
        self.mock_cursor.fetchone.return_value = (
            self.user_id, 'elite', False, last_deactivation
        )
        
        # Try again
        result = await self.stealth_protocol.activate_stealth(self.user_id)
        
        # Should succeed
        self.assertTrue(result['success'])


class TestStealthProtocolEdgeCases(unittest.TestCase):
    """Test edge cases and error handling in Stealth Protocol"""
    
    def setUp(self):
        """Set up test environment"""
        self.stealth_protocol = StealthProtocol()
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_stealth_database_failure_handling(self, mock_get_db):
        """Test handling of database failures"""
        mock_get_db.return_value = self.mock_db
        
        # Mock database error
        self.mock_cursor.execute.side_effect = Exception("Database connection lost")
        
        # Try to activate stealth
        result = await self.stealth_protocol.activate_stealth(123)
        
        # Should handle gracefully
        self.assertFalse(result['success'])
        self.assertIn('error', result['message'].lower())
        
        # Verify rollback was called
        self.mock_db.rollback.assert_called()
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_stealth_concurrent_activation(self, mock_get_db):
        """Test handling of concurrent stealth activation attempts"""
        mock_get_db.return_value = self.mock_db
        user_id = 123
        
        # Mock user with access
        self.mock_cursor.fetchone.return_value = (user_id, 'elite', False)
        
        # Simulate concurrent activation attempts
        tasks = [
            self.stealth_protocol.activate_stealth(user_id)
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # At least one should succeed
        successes = [r for r in results if isinstance(r, dict) and r.get('success')]
        self.assertGreaterEqual(len(successes), 1)
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_stealth_with_invalid_user(self, mock_get_db):
        """Test stealth operations with invalid user"""
        mock_get_db.return_value = self.mock_db
        
        # Mock no user found
        self.mock_cursor.fetchone.return_value = None
        
        # Try to activate stealth
        result = await self.stealth_protocol.activate_stealth(999999)
        
        # Should fail gracefully
        self.assertFalse(result['success'])
        self.assertIn('not found', result['message'].lower())


if __name__ == '__main__':
    # Run async tests
    unittest.main()