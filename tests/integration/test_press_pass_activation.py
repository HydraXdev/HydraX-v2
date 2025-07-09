"""
Integration tests for Press Pass activation flow.
Tests the complete activation process from start to finish.
"""

import unittest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from bitten_core.onboarding.press_pass_manager import PressPassManager
from bitten_core.onboarding.orchestrator import OnboardingOrchestrator
from bitten_core.onboarding.session_manager import SessionManager
from bitten_core.email_service import EmailService
from bitten_core.database.connection import get_db_connection


class TestPressPassActivation(unittest.TestCase):
    """Test Press Pass activation flow from start to finish"""
    
    def setUp(self):
        """Set up test environment"""
        self.user_id = 123456789
        self.username = "test_user"
        self.email = "test@example.com"
        
        # Initialize managers
        self.press_pass_manager = PressPassManager()
        self.orchestrator = OnboardingOrchestrator()
        self.session_manager = SessionManager()
        
        # Mock database connection
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
        
    def tearDown(self):
        """Clean up after tests"""
        # Clean up any test data
        if hasattr(self, 'user_id'):
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Clean up test user data
                cursor.execute("DELETE FROM press_pass_users WHERE telegram_id = %s", (self.user_id,))
                cursor.execute("DELETE FROM onboarding_sessions WHERE telegram_id = %s", (self.user_id,))
                cursor.execute("DELETE FROM user_profiles WHERE telegram_id = %s", (self.user_id,))
                
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"Cleanup error: {e}")
    
    @patch('bitten_core.database.connection.get_db_connection')
    @patch('bitten_core.email_service.EmailService.send_email')
    async def test_complete_activation_flow(self, mock_send_email, mock_get_db):
        """Test complete Press Pass activation flow"""
        mock_get_db.return_value = self.mock_db
        mock_send_email.return_value = True
        
        # Mock database responses
        self.mock_cursor.fetchone.side_effect = [
            None,  # No existing press pass
            None,  # No existing user profile
            (self.user_id, self.email, 'press_pass', datetime.now()),  # Created press pass
        ]
        
        # 1. Start activation
        result = await self.press_pass_manager.activate_press_pass(
            telegram_id=self.user_id,
            email=self.email,
            username=self.username
        )
        
        # Verify activation success
        self.assertTrue(result['success'])
        self.assertEqual(result['tier'], 'press_pass')
        
        # 2. Verify database operations
        insert_calls = [call for call in self.mock_cursor.execute.call_args_list 
                       if 'INSERT' in str(call)]
        self.assertGreater(len(insert_calls), 0)
        
        # 3. Verify email was sent
        mock_send_email.assert_called_once()
        email_call = mock_send_email.call_args
        self.assertEqual(email_call[0][0], self.email)
        self.assertIn('Welcome', email_call[0][1])
        
        # 4. Verify session creation
        self.mock_cursor.fetchone.return_value = (
            self.user_id, 'active', 'welcome', datetime.now()
        )
        
        session = await self.session_manager.get_session(self.user_id)
        self.assertIsNotNone(session)
        self.assertEqual(session['status'], 'active')
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_duplicate_activation_prevention(self, mock_get_db):
        """Test that duplicate activations are prevented"""
        mock_get_db.return_value = self.mock_db
        
        # Mock existing press pass
        self.mock_cursor.fetchone.return_value = (
            self.user_id, self.email, 'press_pass', datetime.now()
        )
        
        # Try to activate again
        result = await self.press_pass_manager.activate_press_pass(
            telegram_id=self.user_id,
            email=self.email,
            username=self.username
        )
        
        # Should fail with appropriate message
        self.assertFalse(result['success'])
        self.assertIn('already active', result['message'].lower())
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_activation_with_referral(self, mock_get_db):
        """Test Press Pass activation with referral code"""
        mock_get_db.return_value = self.mock_db
        referrer_id = 987654321
        referral_code = "REF123"
        
        # Mock database responses
        self.mock_cursor.fetchone.side_effect = [
            None,  # No existing press pass
            (referrer_id, referral_code, 10),  # Valid referral code
            None,  # No existing user profile
        ]
        
        # Activate with referral
        result = await self.press_pass_manager.activate_press_pass(
            telegram_id=self.user_id,
            email=self.email,
            username=self.username,
            referral_code=referral_code
        )
        
        # Verify success
        self.assertTrue(result['success'])
        
        # Verify referral tracking
        referral_calls = [call for call in self.mock_cursor.execute.call_args_list 
                         if 'referral' in str(call).lower()]
        self.assertGreater(len(referral_calls), 0)
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_activation_failure_rollback(self, mock_get_db):
        """Test proper rollback on activation failure"""
        mock_get_db.return_value = self.mock_db
        
        # Mock database error during activation
        self.mock_cursor.execute.side_effect = Exception("Database error")
        
        # Try activation
        result = await self.press_pass_manager.activate_press_pass(
            telegram_id=self.user_id,
            email=self.email,
            username=self.username
        )
        
        # Verify failure
        self.assertFalse(result['success'])
        self.assertIn('error', result['message'].lower())
        
        # Verify rollback was called
        self.mock_db.rollback.assert_called()
    
    @patch('bitten_core.database.connection.get_db_connection')
    @patch('bitten_core.email_service.EmailService.send_email')
    async def test_activation_creates_all_required_records(self, mock_send_email, mock_get_db):
        """Test that activation creates all required database records"""
        mock_get_db.return_value = self.mock_db
        mock_send_email.return_value = True
        
        # Mock no existing records
        self.mock_cursor.fetchone.return_value = None
        
        # Activate
        result = await self.press_pass_manager.activate_press_pass(
            telegram_id=self.user_id,
            email=self.email,
            username=self.username
        )
        
        # Collect all INSERT statements
        insert_statements = []
        for call in self.mock_cursor.execute.call_args_list:
            if call[0][0] and 'INSERT' in call[0][0]:
                insert_statements.append(call[0][0])
        
        # Verify all required tables are populated
        required_tables = [
            'press_pass_users',
            'user_profiles',
            'onboarding_sessions',
            'user_tiers',
            'xp_users'
        ]
        
        for table in required_tables:
            table_inserts = [stmt for stmt in insert_statements if table in stmt]
            self.assertGreater(len(table_inserts), 0, 
                             f"No INSERT found for table: {table}")
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_activation_with_invalid_email(self, mock_get_db):
        """Test activation with invalid email format"""
        mock_get_db.return_value = self.mock_db
        
        # Try with invalid email
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@.com",
            ""
        ]
        
        for invalid_email in invalid_emails:
            result = await self.press_pass_manager.activate_press_pass(
                telegram_id=self.user_id,
                email=invalid_email,
                username=self.username
            )
            
            self.assertFalse(result['success'], 
                           f"Should fail for email: {invalid_email}")
            self.assertIn('invalid', result['message'].lower())
    
    @patch('bitten_core.database.connection.get_db_connection')
    async def test_activation_sets_correct_expiry(self, mock_get_db):
        """Test that Press Pass activation sets correct 30-day expiry"""
        mock_get_db.return_value = self.mock_db
        
        # Mock successful activation
        self.mock_cursor.fetchone.return_value = None
        
        # Activate
        result = await self.press_pass_manager.activate_press_pass(
            telegram_id=self.user_id,
            email=self.email,
            username=self.username
        )
        
        # Find the INSERT for press_pass_users
        for call in self.mock_cursor.execute.call_args_list:
            if call[0][0] and 'INSERT INTO press_pass_users' in call[0][0]:
                # Check that expiry date is set
                self.assertIn('expires_at', call[0][0])
                break
        else:
            self.fail("No INSERT INTO press_pass_users found")


class TestPressPassIntegrationFlow(unittest.TestCase):
    """Test the complete integration flow of Press Pass with other systems"""
    
    def setUp(self):
        """Set up test environment"""
        self.user_id = 123456789
        self.email = "integration@test.com"
        
    @patch('bitten_core.database.connection.get_db_connection')
    @patch('bitten_core.onboarding.orchestrator.OnboardingOrchestrator.start_onboarding')
    async def test_activation_triggers_onboarding(self, mock_start_onboarding, mock_get_db):
        """Test that activation properly triggers onboarding flow"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        
        # Mock no existing press pass
        mock_cursor.fetchone.return_value = None
        
        # Create manager and activate
        manager = PressPassManager()
        result = await manager.activate_press_pass(
            telegram_id=self.user_id,
            email=self.email,
            username="test_user"
        )
        
        # Verify onboarding was triggered
        mock_start_onboarding.assert_called_once()
        call_args = mock_start_onboarding.call_args[0]
        self.assertEqual(call_args[0], self.user_id)


if __name__ == '__main__':
    # Run async tests
    unittest.main()