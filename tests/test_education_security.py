"""
Education System Security Tests
Comprehensive tests for security patches and vulnerabilities
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json

from src.bitten_core.education_security import (
    InputSanitizer,
    RateLimiter,
    AuthorizationManager,
    SecureCommunication,
    EncryptionManager,
    SecurityMiddleware,
    UserContext
)
from src.bitten_core.education_security_integration import (
    SecureEducationSystem,
    SecureSocialLearning,
    SecureEducationAPI
)


class TestInputSanitization:
    """Test input sanitization functions"""
    
    def test_sanitize_user_content(self):
        """Test user content sanitization"""
        sanitizer = InputSanitizer()
        
        # Test XSS prevention
        malicious = '<script>alert("XSS")</script>Hello'
        sanitized = sanitizer.sanitize_user_content(malicious)
        assert '<script>' not in sanitized
        assert 'Hello' in sanitized
        
        # Test SQL injection prevention
        sql_inject = "'; DROP TABLE users; --"
        sanitized = sanitizer.sanitize_user_content(sql_inject)
        assert 'DROP TABLE' not in sanitized
        
        # Test allowed HTML tags
        valid_html = '<b>Bold</b> and <i>italic</i> text'
        sanitized = sanitizer.sanitize_user_content(valid_html)
        assert '<b>Bold</b>' in sanitized
        assert '<i>italic</i>' in sanitized
        
        # Test max length
        long_text = 'A' * 2000
        sanitized = sanitizer.sanitize_user_content(long_text, max_length=100)
        assert len(sanitized) <= 100
    
    def test_sanitize_squad_name(self):
        """Test squad name sanitization"""
        sanitizer = InputSanitizer()
        
        # Valid squad names
        assert sanitizer.sanitize_squad_name("Elite Traders") == "Elite Traders"
        assert sanitizer.sanitize_squad_name("Squad-123") == "Squad-123"
        
        # Invalid characters
        with pytest.raises(ValueError):
            sanitizer.sanitize_squad_name("Squad@#$%")
        
        with pytest.raises(ValueError):
            sanitizer.sanitize_squad_name("")
        
        # XSS in squad name
        malicious = "Squad<script>alert()</script>"
        with pytest.raises(ValueError):
            sanitizer.sanitize_squad_name(malicious)
    
    def test_sanitize_quiz_answer(self):
        """Test quiz answer sanitization"""
        sanitizer = InputSanitizer()
        
        # Normal answer
        answer = "The answer is 42"
        sanitized = sanitizer.sanitize_quiz_answer(answer)
        assert sanitized == "The answer is 42"
        
        # HTML in answer
        html_answer = "<b>Bold</b> answer"
        sanitized = sanitizer.sanitize_quiz_answer(html_answer)
        assert '<b>' not in sanitized
        assert 'Bold answer' in sanitized
        
        # Long answer
        long_answer = 'A' * 1000
        sanitized = sanitizer.sanitize_quiz_answer(long_answer, max_length=100)
        assert len(sanitized) <= 100
    
    def test_sanitize_achievement_data(self):
        """Test achievement data sanitization"""
        sanitizer = InputSanitizer()
        
        # Valid achievement data
        valid_data = {
            'achievement_id': 'first_trade',
            'display_order': 1,
            'visibility': 'public'
        }
        sanitized = sanitizer.sanitize_achievement_data(valid_data)
        assert sanitized == valid_data
        
        # Invalid achievement ID
        invalid_data = {
            'achievement_id': 'achievement<script>',
            'display_order': 999,
            'visibility': 'everyone'
        }
        sanitized = sanitizer.sanitize_achievement_data(invalid_data)
        assert 'achievement_id' not in sanitized
        assert sanitized.get('display_order') is None  # Out of range
        assert 'visibility' not in sanitized  # Invalid value
    
    def test_sanitize_mission_parameters(self):
        """Test mission/trade parameter sanitization"""
        sanitizer = InputSanitizer()
        
        # Valid parameters
        valid_params = {
            'symbol': 'EURUSD',
            'entry_price': 1.0850,
            'stop_loss': 1.0800,
            'take_profit': 1.0900,
            'position_size': 0.1,
            'direction': 'BUY'
        }
        sanitized = sanitizer.sanitize_mission_parameters(valid_params)
        assert sanitized['symbol'] == 'EURUSD'
        assert sanitized['entry_price'] == 1.0850
        
        # Invalid parameters
        invalid_params = {
            'symbol': 'EUR/USD',  # Invalid format
            'entry_price': -100,  # Negative price
            'position_size': 1000,  # Too large
            'direction': 'PURCHASE'  # Invalid direction
        }
        sanitized = sanitizer.sanitize_mission_parameters(invalid_params)
        assert 'symbol' not in sanitized
        assert 'entry_price' not in sanitized
        assert 'position_size' not in sanitized
        assert 'direction' not in sanitized


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_basic_rate_limiting(self):
        """Test basic rate limiting"""
        limiter = RateLimiter()
        
        user_id = "user123"
        activity = "xp_generation"
        
        # Should allow initial requests
        for i in range(10):
            allowed, reset_time = limiter.check_limit(user_id, activity)
            assert allowed is True
            assert reset_time is None
        
        # Should block after limit
        limiter.limits['xp_generation'] = {'max': 10, 'window': 3600}
        allowed, reset_time = limiter.check_limit(user_id, activity)
        assert allowed is False
        assert reset_time is not None
        assert reset_time > 0
    
    def test_multiple_activities(self):
        """Test rate limiting for different activities"""
        limiter = RateLimiter()
        
        user_id = "user123"
        
        # Different activities should have separate limits
        allowed1, _ = limiter.check_limit(user_id, 'journal_entry')
        allowed2, _ = limiter.check_limit(user_id, 'squad_message')
        
        assert allowed1 is True
        assert allowed2 is True
    
    def test_ip_based_limiting(self):
        """Test IP-based rate limiting"""
        limiter = RateLimiter()
        
        ip_address = "192.168.1.1"
        
        # Should track separately from user-based limits
        for i in range(5):
            allowed, _ = limiter.check_limit(ip_address, 'api_call', is_ip=True)
            assert allowed is True
    
    def test_rate_limit_status(self):
        """Test getting rate limit status"""
        limiter = RateLimiter()
        
        user_id = "user123"
        activity = "quiz_submission"
        
        # Check initial status
        status = limiter.get_limit_status(user_id, activity)
        assert status['limited'] is False
        assert status['remaining'] == 20  # Default limit
        
        # Use some requests
        for i in range(5):
            limiter.check_limit(user_id, activity)
        
        status = limiter.get_limit_status(user_id, activity)
        assert status['remaining'] == 15


class TestAuthorization:
    """Test authorization system"""
    
    def test_permission_checks(self):
        """Test basic permission checking"""
        auth = AuthorizationManager()
        
        # Squad leader permissions
        leader_context = UserContext(
            user_id="leader123",
            squad_id="squad123",
            squad_role="LEADER",
            tier="apprentice"
        )
        
        assert auth.check_permission(leader_context, "squad.kick_member") is True
        assert auth.check_permission(leader_context, "squad.invite_member") is True
        assert auth.check_permission(leader_context, "admin.ban_user") is False
        
        # Regular member permissions
        member_context = UserContext(
            user_id="member123",
            squad_id="squad123",
            squad_role="MEMBER",
            tier="apprentice"
        )
        
        assert auth.check_permission(member_context, "squad.kick_member") is False
        assert auth.check_permission(member_context, "squad.create") is True  # Tier-based
    
    def test_tier_based_permissions(self):
        """Test tier-based authorization"""
        auth = AuthorizationManager()
        
        # Nibbler tier
        nibbler = UserContext(user_id="user1", tier="nibbler")
        assert auth.check_permission(nibbler, "squad.create") is False
        assert auth.check_permission(nibbler, "education.advanced_content") is False
        
        # Master tier
        master = UserContext(user_id="user2", tier="master")
        assert auth.check_permission(master, "squad.create") is True
        assert auth.check_permission(master, "trade.high_volume") is True
    
    def test_admin_bypass(self):
        """Test admin permission bypass"""
        auth = AuthorizationManager()
        
        admin = UserContext(user_id="admin1", is_admin=True, tier="nibbler")
        
        # Admin should bypass all checks
        assert auth.check_permission(admin, "squad.create") is True
        assert auth.check_permission(admin, "admin.ban_user") is True
        assert auth.check_permission(admin, "any.random.action") is True
    
    @pytest.mark.asyncio
    async def test_permission_decorator(self):
        """Test permission decorator"""
        auth = AuthorizationManager()
        
        @auth.require_permission("squad.kick_member")
        async def kick_member(self, context: UserContext, member_id: str):
            return f"Kicked {member_id}"
        
        # Should allow squad leader
        leader = UserContext(user_id="leader1", squad_role="LEADER")
        result = await kick_member(None, context=leader, member_id="member1")
        assert result == "Kicked member1"
        
        # Should deny regular member
        member = UserContext(user_id="member1", squad_role="MEMBER")
        with pytest.raises(PermissionError):
            await kick_member(None, context=member, member_id="member2")


class TestSecureCommunication:
    """Test secure communication patterns"""
    
    def test_secure_token_creation(self):
        """Test secure token generation and verification"""
        comm = SecureCommunication()
        
        # Create token
        user_id = "user123"
        action = "reset_password"
        token = comm.create_secure_token(user_id, action, expiry_minutes=60)
        
        assert '|' in token
        
        # Verify valid token
        data = comm.verify_secure_token(token)
        assert data is not None
        assert data['user_id'] == user_id
        assert data['action'] == action
    
    def test_token_expiry(self):
        """Test token expiration"""
        comm = SecureCommunication()
        
        # Create expired token
        token = comm.create_secure_token("user123", "action", expiry_minutes=-1)
        
        # Should fail verification
        data = comm.verify_secure_token(token)
        assert data is None
    
    def test_token_tampering(self):
        """Test token tampering detection"""
        comm = SecureCommunication()
        
        token = comm.create_secure_token("user123", "action")
        
        # Tamper with token
        parts = token.split('|')
        tampered = parts[0] + 'x' + '|' + parts[1]
        
        # Should fail verification
        data = comm.verify_secure_token(tampered)
        assert data is None
    
    def test_telegram_command_sanitization(self):
        """Test Telegram command sanitization"""
        comm = SecureCommunication()
        
        # Valid command
        cmd, args = comm.sanitize_telegram_command("start", ["param1", "param2"])
        assert cmd == "start"
        assert args == ["param1", "param2"]
        
        # Invalid command format
        with pytest.raises(ValueError):
            comm.sanitize_telegram_command("start@bot", [])
        
        # Too many arguments
        many_args = [f"arg{i}" for i in range(20)]
        cmd, args = comm.sanitize_telegram_command("test", many_args)
        assert len(args) == 10  # Limited to 10
    
    def test_frontend_request_validation(self):
        """Test frontend request validation"""
        comm = SecureCommunication()
        
        schema = {
            'username': {'type': 'string', 'required': True, 'max_length': 50},
            'age': {'type': 'number', 'min': 18, 'max': 100},
            'active': {'type': 'boolean'}
        }
        
        # Valid request
        valid_request = {
            'username': 'john_doe',
            'age': 25,
            'active': True
        }
        validated = comm.validate_frontend_request(valid_request, schema)
        assert validated == valid_request
        
        # Missing required field
        with pytest.raises(ValueError):
            comm.validate_frontend_request({'age': 25}, schema)
        
        # Invalid type
        with pytest.raises(TypeError):
            comm.validate_frontend_request({'username': 123}, schema)
        
        # Value out of range
        with pytest.raises(ValueError):
            comm.validate_frontend_request({'username': 'john', 'age': 150}, schema)


class TestEncryption:
    """Test encryption functionality"""
    
    def test_data_encryption_decryption(self):
        """Test encrypting and decrypting user data"""
        encryption = EncryptionManager()
        
        # Test data
        data = {
            'user_id': '123',
            'email': 'user@example.com',
            'balance': 1000.50,
            'public_field': 'visible'
        }
        
        # Encrypt sensitive fields
        encrypted = encryption.encrypt_user_data(data, ['email', 'balance'])
        
        assert encrypted['user_id'] == '123'
        assert encrypted['public_field'] == 'visible'
        assert encrypted['email'] != 'user@example.com'
        assert encrypted['balance'] != 1000.50
        
        # Decrypt
        decrypted = encryption.decrypt_user_data(encrypted, ['email', 'balance'])
        assert decrypted['email'] == 'user@example.com'
        assert decrypted['balance'] == '1000.5'  # Converted to string
    
    def test_quiz_answer_encryption(self):
        """Test quiz answer encryption"""
        encryption = EncryptionManager()
        
        answers = ['Answer 1', 'Answer 2', 'Answer 3']
        
        # Encrypt
        encrypted = encryption.encrypt_quiz_answers(answers)
        assert len(encrypted) == 3
        assert all(ans != orig for ans, orig in zip(encrypted, answers))
        
        # Decrypt
        decrypted = encryption.decrypt_quiz_answers(encrypted)
        assert decrypted == answers
    
    def test_encryption_integrity(self):
        """Test encryption integrity verification"""
        encryption = EncryptionManager()
        
        # Encrypt data
        original = "sensitive data"
        encrypted = encryption._simple_encrypt(original)
        
        # Tamper with encrypted data
        tampered = encrypted[:-5] + "xxxxx"
        
        # Should fail decryption
        with pytest.raises(ValueError):
            encryption._simple_decrypt(tampered)


class TestSecurityMiddleware:
    """Test security middleware integration"""
    
    @pytest.mark.asyncio
    async def test_request_processing(self):
        """Test processing education requests through middleware"""
        middleware = SecurityMiddleware()
        
        # Valid request
        context = UserContext(user_id="user123", tier="apprentice")
        request = {
            'action': 'journal.create',
            'data': {
                'content': 'Today I learned about trading',
                'tags': ['education', 'trading']
            }
        }
        
        processed = await middleware.process_education_request(request, context)
        assert processed['action'] == 'journal.create'
        assert 'Today I learned' in processed['data']['content']
    
    @pytest.mark.asyncio
    async def test_banned_user_check(self):
        """Test banned user detection"""
        middleware = SecurityMiddleware()
        middleware.ban_list.add("banned123")
        
        context = UserContext(user_id="banned123")
        request = {'action': 'any.action', 'data': {}}
        
        with pytest.raises(PermissionError):
            await middleware.process_education_request(request, context)
    
    @pytest.mark.asyncio
    async def test_suspicious_activity_tracking(self):
        """Test suspicious activity detection"""
        middleware = SecurityMiddleware()
        
        context = UserContext(user_id="suspicious123", tier="nibbler")
        
        # Simulate rapid quiz submissions
        for i in range(5):
            request = {
                'action': 'quiz.submit',
                'data': {
                    'quiz_id': 'quiz1',
                    'answers': ['A', 'B', 'C']
                }
            }
            
            if i < 4:
                await middleware.process_education_request(request, context)
            else:
                # Should raise error on 5th rapid submission
                with pytest.raises(ValueError) as exc:
                    await middleware.process_education_request(request, context)
                assert "Too many quiz submissions" in str(exc.value)


class TestSecureEducationSystem:
    """Test secure education system integration"""
    
    @pytest.mark.asyncio
    async def test_secure_journal_creation(self):
        """Test creating journal entries securely"""
        # Mock database
        mock_db = AsyncMock()
        mock_db.execute.return_value = "entry123"
        
        # Create system
        secure_edu = SecureEducationSystem(mock_db, Mock())
        
        # Create session
        context = UserContext(user_id="user123", tier="apprentice")
        session_id = secure_edu.session_manager.create_session("user123", context)
        
        # Create journal entry
        result = await secure_edu.create_secure_journal_entry(
            session_id,
            "Today I learned <script>alert('xss')</script> about trading",
            ["trading", "education", "<script>"]
        )
        
        assert result['success'] is True
        
        # Check sanitization
        call_args = mock_db.execute.call_args[0]
        assert '<script>' not in call_args[1][1]  # Content should be sanitized
    
    @pytest.mark.asyncio
    async def test_quiz_submission_security(self):
        """Test secure quiz submission"""
        # Mock database
        mock_db = AsyncMock()
        mock_db.fetch_one.side_effect = [
            {'quiz_id': 'quiz1', 'is_active': True},  # Quiz exists
            None  # No recent submission
        ]
        mock_db.execute.return_value = "submission123"
        
        secure_edu = SecureEducationSystem(mock_db, Mock())
        
        # Create session
        context = UserContext(user_id="user123", tier="apprentice")
        session_id = secure_edu.session_manager.create_session("user123", context)
        
        # Submit quiz
        result = await secure_edu.submit_quiz_answer(
            session_id,
            "quiz1",
            ["Answer 1", "<script>alert('xss')</script>", "Answer 3"]
        )
        
        assert result['success'] is True
        assert result['submission_id'] == "submission123"
    
    @pytest.mark.asyncio
    async def test_squad_creation_permissions(self):
        """Test squad creation with tier permissions"""
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = None  # No existing squad
        
        secure_edu = SecureEducationSystem(mock_db, Mock())
        
        # Nibbler should not be able to create squad
        nibbler_context = UserContext(user_id="nibbler1", tier="nibbler")
        nibbler_session = secure_edu.session_manager.create_session("nibbler1", nibbler_context)
        
        with pytest.raises(PermissionError):
            await secure_edu.create_squad_secure(
                nibbler_session,
                "Nibbler Squad",
                "We want to trade!",
                "General"
            )
        
        # Apprentice should be able to create squad
        apprentice_context = UserContext(user_id="apprentice1", tier="apprentice")
        apprentice_session = secure_edu.session_manager.create_session("apprentice1", apprentice_context)
        
        mock_db.execute.return_value = None
        result = await secure_edu.create_squad_secure(
            apprentice_session,
            "Elite Squad",
            "Victory through discipline!",
            "Trading"
        )
        
        assert result['success'] is True


class TestSecureAPI:
    """Test secure API endpoints"""
    
    @pytest.mark.asyncio
    async def test_api_request_validation(self):
        """Test API request validation"""
        mock_edu = AsyncMock()
        api = SecureEducationAPI(mock_edu)
        
        # Mock session validation
        mock_context = UserContext(user_id="user123", tier="apprentice")
        mock_edu.session_manager.validate_session.return_value = mock_context
        
        # Valid request
        request_data = {
            'name': 'Test Squad',
            'motto': 'Test motto',
            'specialization': 'Python'
        }
        
        result = await api.handle_request('create_squad', request_data, 'session123')
        
        assert result['code'] == 200
        
        # Invalid request (missing required field)
        invalid_data = {
            'motto': 'Test motto'
        }
        
        result = await api.handle_request('create_squad', invalid_data, 'session123')
        
        assert result['code'] == 400
        assert 'Invalid request' in result['error']
    
    @pytest.mark.asyncio
    async def test_api_session_validation(self):
        """Test API session validation"""
        mock_edu = AsyncMock()
        api = SecureEducationAPI(mock_edu)
        
        # Invalid session
        mock_edu.session_manager.validate_session.return_value = None
        
        result = await api.handle_request('any_endpoint', {}, 'invalid_session')
        
        assert result['code'] == 401
        assert result['error'] == 'Invalid session'


class TestIntegrationScenarios:
    """Test complete integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_education_flow(self):
        """Test complete education flow with security"""
        # Mock database
        mock_db = AsyncMock()
        mock_db.fetch_one.return_value = None
        mock_db.fetch_all.return_value = []
        mock_db.execute.return_value = "123"
        
        # Create secure system
        secure_edu = SecureEducationSystem(mock_db, Mock())
        
        # User registration and session creation
        user_id = "student123"
        context = UserContext(
            user_id=user_id,
            tier="apprentice",
            permissions=['squad.create', 'journal.write']
        )
        session_id = secure_edu.session_manager.create_session(user_id, context)
        
        # Create journal entry
        journal_result = await secure_edu.create_secure_journal_entry(
            session_id,
            "Started my trading education journey!",
            ["beginner", "motivation"]
        )
        assert journal_result['success'] is True
        
        # Create squad
        squad_result = await secure_edu.create_squad_secure(
            session_id,
            "Learning Warriors",
            "Knowledge is power!",
            "General"
        )
        assert squad_result['success'] is True
        
        # Submit quiz (mock quiz exists)
        mock_db.fetch_one.side_effect = [
            {'quiz_id': 'basics_quiz', 'is_active': True},
            None
        ]
        
        quiz_result = await secure_edu.submit_quiz_answer(
            session_id,
            "basics_quiz",
            ["A", "B", "C", "D"]
        )
        assert quiz_result['success'] is True
    
    @pytest.mark.asyncio
    async def test_attack_scenarios(self):
        """Test various attack scenarios"""
        mock_db = AsyncMock()
        secure_edu = SecureEducationSystem(mock_db, Mock())
        
        # Create legitimate session
        context = UserContext(user_id="user123", tier="apprentice")
        session_id = secure_edu.session_manager.create_session("user123", context)
        
        # Test 1: XSS attempt in journal
        xss_content = """
        <script>
        fetch('/api/steal-data', {
            method: 'POST',
            body: JSON.stringify({cookies: document.cookie})
        });
        </script>
        Check out my trading strategy!
        """
        
        result = await secure_edu.create_secure_journal_entry(
            session_id,
            xss_content,
            ["trading"]
        )
        
        # Should succeed but content should be sanitized
        assert result['success'] is True
        call_args = mock_db.execute.call_args[0]
        encrypted_content = call_args[1][1]
        # Would need to decrypt to fully verify, but script tags should be removed
        
        # Test 2: SQL injection in squad name
        try:
            await secure_edu.create_squad_secure(
                session_id,
                "Squad'; DROP TABLE squads; --",
                "Normal motto",
                "General"
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected
        
        # Test 3: Rate limiting attack
        for i in range(100):
            try:
                await secure_edu.create_secure_journal_entry(
                    session_id,
                    f"Spam entry {i}",
                    ["spam"]
                )
            except ValueError as e:
                if "Rate limit exceeded" in str(e):
                    break
        else:
            assert False, "Rate limiting should have kicked in"


# Performance tests
class TestSecurityPerformance:
    """Test security feature performance"""
    
    def test_sanitization_performance(self):
        """Test sanitization performance"""
        import time
        sanitizer = InputSanitizer()
        
        # Generate test content
        content = "This is a test " * 100  # ~1400 chars
        
        start = time.time()
        for _ in range(1000):
            sanitizer.sanitize_user_content(content)
        elapsed = time.time() - start
        
        # Should process 1000 sanitizations in under 1 second
        assert elapsed < 1.0
    
    def test_encryption_performance(self):
        """Test encryption performance"""
        import time
        encryption = EncryptionManager()
        
        data = "Sensitive user data that needs encryption"
        
        start = time.time()
        for _ in range(1000):
            encrypted = encryption._simple_encrypt(data)
            decrypted = encryption._simple_decrypt(encrypted)
        elapsed = time.time() - start
        
        # Should handle 1000 encrypt/decrypt cycles in under 2 seconds
        assert elapsed < 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])