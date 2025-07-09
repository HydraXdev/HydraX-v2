"""
Education System Security Integration
Patches and enhancements for existing education modules
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from functools import wraps
import logging
import asyncio
from dataclasses import dataclass

from .education_system import EducationSystem, PersonaType, TradingTier
from .education_social import SquadSystem, MentorshipProgram, StudyGroups
from .education_security import (
    InputSanitizer,
    RateLimiter,
    AuthorizationManager,
    SecureCommunication,
    EncryptionManager,
    SecurityMiddleware,
    UserContext,
    SecureSessionManager
)

logger = logging.getLogger(__name__)

# ==========================================
# SECURE EDUCATION SYSTEM
# ==========================================

class SecureEducationSystem(EducationSystem):
    """Enhanced education system with comprehensive security"""
    
    def __init__(self, database, logger):
        super().__init__(database, logger)
        
        # Initialize security components
        self.security = SecurityMiddleware()
        self.session_manager = SecureSessionManager()
        self.sanitizer = InputSanitizer()
        self.rate_limiter = RateLimiter()
        self.encryption = EncryptionManager()
        
        # Track active sessions per user
        self.user_sessions = {}
    
    # ==========================================
    # SECURE JOURNAL ENTRIES
    # ==========================================
    
    async def create_secure_journal_entry(self, session_id: str, 
                                        content: str, tags: List[str]) -> Dict[str, Any]:
        """Create journal entry with security checks"""
        # Validate session
        context = self.session_manager.validate_session(session_id)
        if not context:
            raise ValueError("Invalid or expired session")
        
        # Rate limiting
        allowed, reset_time = self.rate_limiter.check_limit(
            context.user_id, 'journal_entry'
        )
        if not allowed:
            raise ValueError(f"Rate limit exceeded. Try again in {reset_time} seconds")
        
        # Sanitize content
        sanitized_content = self.sanitizer.sanitize_user_content(content, max_length=2000)
        sanitized_tags = [
            self.sanitizer.sanitize_user_content(tag, 50) 
            for tag in tags[:10]  # Limit number of tags
        ]
        
        # Store encrypted journal entry
        encrypted_content = self.encryption._simple_encrypt(sanitized_content)
        
        # Store in database
        entry_id = await self.db.execute(
            """INSERT INTO user_journal_entries 
               (user_id, content_encrypted, tags, created_at)
               VALUES (?, ?, ?, ?)
               RETURNING entry_id""",
            (context.user_id, encrypted_content, 
             ','.join(sanitized_tags), datetime.utcnow())
        )
        
        # Log activity for analytics
        await self._log_secure_activity(context.user_id, 'journal_entry_created', {
            'entry_id': entry_id,
            'tag_count': len(sanitized_tags)
        })
        
        return {
            'success': True,
            'entry_id': entry_id,
            'message': 'Journal entry created securely'
        }
    
    async def get_journal_entries(self, session_id: str, 
                                limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user's journal entries with decryption"""
        context = self.session_manager.validate_session(session_id)
        if not context:
            raise ValueError("Invalid session")
        
        # Validate pagination parameters
        limit = min(max(1, limit), 50)  # Max 50 entries at once
        offset = max(0, offset)
        
        entries = await self.db.fetch_all(
            """SELECT entry_id, content_encrypted, tags, created_at
               FROM user_journal_entries
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT ? OFFSET ?""",
            (context.user_id, limit, offset)
        )
        
        # Decrypt entries
        decrypted_entries = []
        for entry in entries:
            try:
                decrypted_content = self.encryption._simple_decrypt(
                    entry['content_encrypted']
                )
                decrypted_entries.append({
                    'entry_id': entry['entry_id'],
                    'content': decrypted_content,
                    'tags': entry['tags'].split(',') if entry['tags'] else [],
                    'created_at': entry['created_at']
                })
            except Exception as e:
                logger.error(f"Failed to decrypt journal entry: {e}")
                continue
        
        return decrypted_entries
    
    # ==========================================
    # SECURE QUIZ HANDLING
    # ==========================================
    
    async def submit_quiz_answer(self, session_id: str, quiz_id: str, 
                               answers: List[str]) -> Dict[str, Any]:
        """Submit quiz answers with security validation"""
        context = self.session_manager.validate_session(session_id)
        if not context:
            raise ValueError("Invalid session")
        
        # Rate limiting for quiz submissions
        allowed, reset_time = self.rate_limiter.check_limit(
            context.user_id, 'quiz_submission'
        )
        if not allowed:
            raise ValueError(f"Too many quiz attempts. Try again in {reset_time} seconds")
        
        # Validate quiz exists and is active
        quiz = await self.db.fetch_one(
            "SELECT * FROM education_quizzes WHERE quiz_id = ? AND is_active = TRUE",
            (quiz_id,)
        )
        if not quiz:
            raise ValueError("Invalid or inactive quiz")
        
        # Check if user already completed this quiz recently
        recent_submission = await self.db.fetch_one(
            """SELECT submission_id FROM quiz_submissions 
               WHERE user_id = ? AND quiz_id = ? 
               AND created_at > ?""",
            (context.user_id, quiz_id, datetime.utcnow() - timedelta(hours=24))
        )
        if recent_submission:
            raise ValueError("Quiz already completed recently")
        
        # Sanitize and encrypt answers
        sanitized_answers = [
            self.sanitizer.sanitize_quiz_answer(answer) 
            for answer in answers[:50]  # Max 50 answers
        ]
        encrypted_answers = self.encryption.encrypt_quiz_answers(sanitized_answers)
        
        # Store submission
        submission_id = await self.db.execute(
            """INSERT INTO quiz_submissions 
               (user_id, quiz_id, answers_encrypted, submitted_at)
               VALUES (?, ?, ?, ?)
               RETURNING submission_id""",
            (context.user_id, quiz_id, ','.join(encrypted_answers), datetime.utcnow())
        )
        
        # Grade quiz asynchronously
        asyncio.create_task(self._grade_quiz_secure(submission_id, quiz_id, encrypted_answers))
        
        return {
            'success': True,
            'submission_id': submission_id,
            'message': 'Quiz submitted successfully'
        }
    
    async def _grade_quiz_secure(self, submission_id: str, quiz_id: str, 
                               encrypted_answers: List[str]):
        """Grade quiz with secure answer comparison"""
        # Fetch correct answers
        quiz = await self.db.fetch_one(
            "SELECT correct_answers_encrypted FROM education_quizzes WHERE quiz_id = ?",
            (quiz_id,)
        )
        
        if not quiz:
            return
        
        # Decrypt answers
        try:
            user_answers = self.encryption.decrypt_quiz_answers(encrypted_answers)
            correct_answers = self.encryption.decrypt_quiz_answers(
                quiz['correct_answers_encrypted'].split(',')
            )
        except Exception as e:
            logger.error(f"Failed to decrypt quiz answers: {e}")
            return
        
        # Calculate score
        score = sum(1 for ua, ca in zip(user_answers, correct_answers) if ua == ca)
        total = len(correct_answers)
        percentage = (score / total * 100) if total > 0 else 0
        
        # Update submission with score
        await self.db.execute(
            """UPDATE quiz_submissions 
               SET score = ?, percentage = ?, graded_at = ?
               WHERE submission_id = ?""",
            (score, percentage, datetime.utcnow(), submission_id)
        )
        
        # Award XP if passed (70% or higher)
        if percentage >= 70:
            await self._award_quiz_xp(submission_id, score, total)
    
    # ==========================================
    # SECURE SQUAD OPERATIONS
    # ==========================================
    
    async def create_squad_secure(self, session_id: str, squad_name: str, 
                                motto: str, specialization: str = "General") -> Dict[str, Any]:
        """Create squad with security validation"""
        context = self.session_manager.validate_session(session_id)
        if not context:
            raise ValueError("Invalid session")
        
        # Check tier permission
        if context.tier == "nibbler":
            raise PermissionError("Nibblers cannot create squads. Reach Apprentice tier first!")
        
        # Check if user already leads a squad
        existing_squad = await self.db.fetch_one(
            "SELECT squad_id FROM squads WHERE leader_id = ?",
            (context.user_id,)
        )
        if existing_squad:
            raise ValueError("You already lead a squad")
        
        # Sanitize inputs
        try:
            sanitized_name = self.sanitizer.sanitize_squad_name(squad_name)
            sanitized_motto = self.sanitizer.sanitize_user_content(motto, max_length=200)
        except ValueError as e:
            raise ValueError(f"Invalid squad details: {e}")
        
        # Validate specialization
        allowed_specializations = ["General", "Python", "Security", "AI", "Web", "Data"]
        if specialization not in allowed_specializations:
            specialization = "General"
        
        # Create squad with additional security fields
        squad_id = f"squad_{context.user_id}_{datetime.now().timestamp()}"
        
        await self.db.execute(
            """INSERT INTO squads 
               (squad_id, name, motto, leader_id, specialization, 
                created_at, is_verified, max_members)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (squad_id, sanitized_name, sanitized_motto, context.user_id,
             specialization, datetime.utcnow(), False, 6)
        )
        
        # Add leader as first member
        await self.db.execute(
            """INSERT INTO squad_members 
               (squad_id, user_id, role, joined_at)
               VALUES (?, ?, ?, ?)""",
            (squad_id, context.user_id, 'LEADER', datetime.utcnow())
        )
        
        # Log squad creation
        await self._log_secure_activity(context.user_id, 'squad_created', {
            'squad_id': squad_id,
            'name': sanitized_name
        })
        
        return {
            'success': True,
            'squad_id': squad_id,
            'message': f'Squad "{sanitized_name}" created successfully!'
        }
    
    async def send_squad_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Send message to squad chat with security checks"""
        context = self.session_manager.validate_session(session_id)
        if not context or not context.squad_id:
            raise ValueError("Not in a squad")
        
        # Rate limiting
        allowed, reset_time = self.rate_limiter.check_limit(
            context.user_id, 'squad_message'
        )
        if not allowed:
            raise ValueError(f"Message rate limit exceeded. Wait {reset_time} seconds")
        
        # Sanitize message
        sanitized_message = self.sanitizer.sanitize_user_content(message, max_length=500)
        
        # Check for spam patterns
        if self._is_spam_message(sanitized_message):
            await self._log_secure_activity(context.user_id, 'spam_detected', {
                'squad_id': context.squad_id
            })
            raise ValueError("Message appears to be spam")
        
        # Store message
        message_id = await self.db.execute(
            """INSERT INTO squad_messages 
               (squad_id, user_id, message, created_at)
               VALUES (?, ?, ?, ?)
               RETURNING message_id""",
            (context.squad_id, context.user_id, sanitized_message, datetime.utcnow())
        )
        
        # Broadcast to squad members (implement WebSocket or polling)
        await self._broadcast_squad_message(context.squad_id, {
            'message_id': message_id,
            'user_id': context.user_id,
            'message': sanitized_message,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return {
            'success': True,
            'message_id': message_id
        }
    
    def _is_spam_message(self, message: str) -> bool:
        """Check if message contains spam patterns"""
        spam_patterns = [
            r'(buy|sell)\s+now',
            r'guaranteed\s+profit',
            r'click\s+here',
            r'(telegram|whatsapp|discord)\.me',
            r'@[a-zA-Z0-9_]{5,}',  # Multiple mentions
            r'http[s]?://[^\s]+',  # URLs (can be configured)
        ]
        
        message_lower = message.lower()
        
        # Check for repeated characters
        if any(char * 10 in message for char in 'abcdefghijklmnopqrstuvwxyz0123456789'):
            return True
        
        # Check spam patterns
        for pattern in spam_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    # ==========================================
    # SECURE ACHIEVEMENT SYSTEM
    # ==========================================
    
    async def update_achievement_showcase(self, session_id: str, 
                                        achievements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update achievement showcase with validation"""
        context = self.session_manager.validate_session(session_id)
        if not context:
            raise ValueError("Invalid session")
        
        # Limit number of showcased achievements
        if len(achievements) > 10:
            raise ValueError("Maximum 10 achievements can be showcased")
        
        # Validate each achievement
        validated_achievements = []
        for ach in achievements:
            sanitized = self.sanitizer.sanitize_achievement_data(ach)
            
            # Verify user owns the achievement
            owned = await self.db.fetch_one(
                """SELECT ua.user_achievement_id 
                   FROM user_achievements ua
                   JOIN achievements a ON ua.achievement_id = a.achievement_id
                   WHERE ua.user_id = ? AND a.code = ?""",
                (context.user_id, sanitized.get('achievement_id'))
            )
            
            if owned:
                validated_achievements.append(sanitized)
        
        # Update showcase
        await self.db.execute(
            """UPDATE user_profiles 
               SET achievement_showcase = ?
               WHERE user_id = ?""",
            (json.dumps(validated_achievements), context.user_id)
        )
        
        return {
            'success': True,
            'showcased': len(validated_achievements)
        }
    
    # ==========================================
    # SECURE XP SYSTEM
    # ==========================================
    
    async def award_xp_secure(self, user_id: str, amount: int, 
                            source: str, source_id: Optional[str] = None) -> Dict[str, Any]:
        """Award XP with security checks"""
        # Rate limiting for XP generation
        allowed, reset_time = self.rate_limiter.check_limit(user_id, 'xp_generation')
        if not allowed:
            logger.warning(f"XP rate limit hit for user {user_id}")
            return {'success': False, 'reason': 'rate_limited'}
        
        # Validate XP amount
        if amount < 0 or amount > 1000:
            logger.warning(f"Invalid XP amount {amount} for user {user_id}")
            return {'success': False, 'reason': 'invalid_amount'}
        
        # Check for duplicate XP awards
        if source_id:
            duplicate = await self.db.fetch_one(
                """SELECT transaction_id FROM xp_transactions 
                   WHERE user_id = ? AND source_type = ? AND source_id = ?""",
                (user_id, source, source_id)
            )
            if duplicate:
                return {'success': False, 'reason': 'duplicate_award'}
        
        # Get current XP
        current_xp = await self.db.fetch_value(
            "SELECT total_xp FROM user_profiles WHERE user_id = ?",
            (user_id,)
        ) or 0
        
        new_total = current_xp + amount
        
        # Create XP transaction
        await self.db.execute(
            """INSERT INTO xp_transactions 
               (user_id, amount, balance_after, source_type, source_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, amount, new_total, source, source_id, datetime.utcnow())
        )
        
        # Update user profile
        await self.db.execute(
            "UPDATE user_profiles SET total_xp = ? WHERE user_id = ?",
            (new_total, user_id)
        )
        
        # Check for level up
        old_level = self._calculate_level(current_xp)
        new_level = self._calculate_level(new_total)
        
        if new_level > old_level:
            await self._handle_level_up(user_id, new_level)
        
        return {
            'success': True,
            'amount': amount,
            'new_total': new_total,
            'level_up': new_level > old_level
        }
    
    def _calculate_level(self, xp: int) -> int:
        """Calculate level from XP using secure formula"""
        # Exponential curve: level = floor(sqrt(xp / 100))
        import math
        return int(math.sqrt(xp / 100))
    
    # ==========================================
    # SECURE MENTOR SYSTEM
    # ==========================================
    
    async def request_mentor_session(self, session_id: str, mentor_id: str,
                                   topic: str, preferred_time: datetime) -> Dict[str, Any]:
        """Request mentorship session with validation"""
        context = self.session_manager.validate_session(session_id)
        if not context:
            raise ValueError("Invalid session")
        
        # Validate mentor exists and is active
        mentor = await self.db.fetch_one(
            """SELECT user_id, is_mentor, mentor_active 
               FROM users WHERE user_id = ? AND is_mentor = TRUE AND mentor_active = TRUE""",
            (mentor_id,)
        )
        if not mentor:
            raise ValueError("Invalid or inactive mentor")
        
        # Check if mentee already has pending request
        pending = await self.db.fetch_one(
            """SELECT request_id FROM mentor_requests 
               WHERE mentee_id = ? AND status = 'pending'""",
            (context.user_id,)
        )
        if pending:
            raise ValueError("You already have a pending mentor request")
        
        # Sanitize topic
        sanitized_topic = self.sanitizer.sanitize_user_content(topic, max_length=200)
        
        # Validate time is in future
        if preferred_time <= datetime.utcnow():
            raise ValueError("Session time must be in the future")
        
        # Create request
        request_id = await self.db.execute(
            """INSERT INTO mentor_requests 
               (mentor_id, mentee_id, topic, preferred_time, status, created_at)
               VALUES (?, ?, ?, ?, 'pending', ?)
               RETURNING request_id""",
            (mentor_id, context.user_id, sanitized_topic, preferred_time, datetime.utcnow())
        )
        
        # Notify mentor (implement notification system)
        await self._notify_mentor(mentor_id, {
            'type': 'session_request',
            'mentee_id': context.user_id,
            'topic': sanitized_topic,
            'time': preferred_time.isoformat()
        })
        
        return {
            'success': True,
            'request_id': request_id,
            'message': 'Mentor session requested successfully'
        }
    
    # ==========================================
    # ACTIVITY LOGGING
    # ==========================================
    
    async def _log_secure_activity(self, user_id: str, action: str, 
                                 details: Dict[str, Any]):
        """Log user activity for security monitoring"""
        await self.db.execute(
            """INSERT INTO security_activity_log 
               (user_id, action, details, ip_address, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, action, json.dumps(details), 
             details.get('ip_address'), datetime.utcnow())
        )
    
    async def _broadcast_squad_message(self, squad_id: str, message_data: Dict[str, Any]):
        """Broadcast message to squad members (placeholder)"""
        # In production, implement WebSocket or push notifications
        pass
    
    async def _notify_mentor(self, mentor_id: str, notification: Dict[str, Any]):
        """Send notification to mentor (placeholder)"""
        # In production, implement notification system
        pass
    
    async def _handle_level_up(self, user_id: str, new_level: int):
        """Handle level up rewards and notifications"""
        # Award level up rewards
        await self.award_xp_secure(user_id, 100 * new_level, 'level_up', f'level_{new_level}')
        
        # Send notification
        # In production, implement notification system
        pass


# ==========================================
# SECURE SOCIAL LEARNING INTEGRATION
# ==========================================

class SecureSocialLearning:
    """Security wrapper for social learning components"""
    
    def __init__(self, squad_system: SquadSystem, 
                 mentorship_program: MentorshipProgram,
                 study_groups: StudyGroups):
        self.squad_system = squad_system
        self.mentorship_program = mentorship_program
        self.study_groups = study_groups
        self.sanitizer = InputSanitizer()
        self.rate_limiter = RateLimiter()
        self.auth_manager = AuthorizationManager()
    
    async def secure_squad_operation(self, operation: str, 
                                   context: UserContext, **kwargs) -> Any:
        """Execute squad operation with security checks"""
        # Check permission
        if not self.auth_manager.check_permission(context, f"squad.{operation}"):
            raise PermissionError(f"Unauthorized squad operation: {operation}")
        
        # Rate limiting
        allowed, reset_time = self.rate_limiter.check_limit(
            context.user_id, 'squad_operation'
        )
        if not allowed:
            raise ValueError(f"Rate limit exceeded. Try again in {reset_time} seconds")
        
        # Execute operation based on type
        if operation == 'create':
            squad_name = self.sanitizer.sanitize_squad_name(kwargs.get('name', ''))
            motto = self.sanitizer.sanitize_user_content(kwargs.get('motto', ''), 200)
            return self.squad_system.create_squad(
                context.user_id, 
                kwargs.get('username', 'Unknown'),
                squad_name, 
                motto,
                kwargs.get('specialization', 'General')
            )
        
        elif operation == 'send_message':
            message = self.sanitizer.sanitize_user_content(
                kwargs.get('message', ''), 
                max_length=500
            )
            return self.squad_system.send_squad_message(
                context.squad_id,
                context.user_id,
                message
            )
        
        else:
            raise ValueError(f"Unknown squad operation: {operation}")
    
    async def secure_mentorship_operation(self, operation: str,
                                        context: UserContext, **kwargs) -> Any:
        """Execute mentorship operation with security checks"""
        # Check if user is mentor for mentor operations
        if operation.startswith('mentor_') and not context.is_mentor:
            raise PermissionError("Not authorized as mentor")
        
        # Rate limiting
        allowed, reset_time = self.rate_limiter.check_limit(
            context.user_id, 'mentorship_operation'
        )
        if not allowed:
            raise ValueError(f"Rate limit exceeded. Try again in {reset_time} seconds")
        
        # Execute operation
        if operation == 'schedule_session':
            # Validate inputs
            topic = self.sanitizer.sanitize_user_content(kwargs.get('topic', ''), 200)
            
            return self.mentorship_program.schedule_session(
                kwargs.get('mentor_id'),
                context.user_id,
                kwargs.get('scheduled_time'),
                kwargs.get('duration'),
                topic,
                kwargs.get('goals', [])
            )
        
        else:
            raise ValueError(f"Unknown mentorship operation: {operation}")


# ==========================================
# SECURE API ENDPOINTS
# ==========================================

class SecureEducationAPI:
    """Secure API wrapper for education system"""
    
    def __init__(self, education_system: SecureEducationSystem):
        self.education = education_system
        self.request_schemas = self._init_request_schemas()
    
    def _init_request_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Initialize request validation schemas"""
        return {
            'create_journal': {
                'content': {'type': 'string', 'required': True, 'max_length': 2000},
                'tags': {'type': 'array', 'max_items': 10}
            },
            'submit_quiz': {
                'quiz_id': {'type': 'string', 'required': True, 'pattern': r'^[a-zA-Z0-9_-]+$'},
                'answers': {'type': 'array', 'required': True, 'max_items': 50}
            },
            'create_squad': {
                'name': {'type': 'string', 'required': True, 'pattern': r'^[a-zA-Z0-9\s\-\.]{3,50}$'},
                'motto': {'type': 'string', 'required': True, 'max_length': 200},
                'specialization': {'type': 'string', 'pattern': r'^[a-zA-Z]+$'}
            }
        }
    
    async def handle_request(self, endpoint: str, request_data: Dict[str, Any],
                           session_id: str) -> Dict[str, Any]:
        """Handle API request with validation"""
        # Validate session first
        context = self.education.session_manager.validate_session(session_id)
        if not context:
            return {'error': 'Invalid session', 'code': 401}
        
        # Validate request against schema
        if endpoint in self.request_schemas:
            try:
                validated_data = self.education.security.secure_comm.validate_frontend_request(
                    request_data,
                    self.request_schemas[endpoint]
                )
            except (ValueError, TypeError) as e:
                return {'error': f'Invalid request: {e}', 'code': 400}
        else:
            validated_data = request_data
        
        # Route to appropriate handler
        try:
            if endpoint == 'create_journal':
                result = await self.education.create_secure_journal_entry(
                    session_id,
                    validated_data.get('content', ''),
                    validated_data.get('tags', [])
                )
            
            elif endpoint == 'submit_quiz':
                result = await self.education.submit_quiz_answer(
                    session_id,
                    validated_data['quiz_id'],
                    validated_data['answers']
                )
            
            elif endpoint == 'create_squad':
                result = await self.education.create_squad_secure(
                    session_id,
                    validated_data['name'],
                    validated_data['motto'],
                    validated_data.get('specialization', 'General')
                )
            
            else:
                return {'error': 'Unknown endpoint', 'code': 404}
            
            return {'success': True, 'data': result, 'code': 200}
            
        except PermissionError as e:
            return {'error': str(e), 'code': 403}
        except ValueError as e:
            return {'error': str(e), 'code': 400}
        except Exception as e:
            logger.error(f"API error: {e}")
            return {'error': 'Internal server error', 'code': 500}


# ==========================================
# DATABASE MIGRATIONS FOR SECURITY
# ==========================================

async def apply_security_migrations(db):
    """Apply database migrations for security features"""
    
    # User journal entries with encryption
    await db.execute("""
        CREATE TABLE IF NOT EXISTS user_journal_entries (
            entry_id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            content_encrypted TEXT NOT NULL,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_journal_user_date (user_id, created_at)
        )
    """)
    
    # Quiz submissions with encryption
    await db.execute("""
        CREATE TABLE IF NOT EXISTS quiz_submissions (
            submission_id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            quiz_id VARCHAR(255) NOT NULL,
            answers_encrypted TEXT NOT NULL,
            score INTEGER,
            percentage DECIMAL(5,2),
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            graded_at TIMESTAMP,
            INDEX idx_quiz_user (user_id, quiz_id),
            INDEX idx_quiz_time (submitted_at)
        )
    """)
    
    # Security activity log
    await db.execute("""
        CREATE TABLE IF NOT EXISTS security_activity_log (
            log_id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            action VARCHAR(255) NOT NULL,
            details JSON,
            ip_address INET,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_security_user_time (user_id, timestamp),
            INDEX idx_security_action (action)
        )
    """)
    
    # Squad security
    await db.execute("""
        ALTER TABLE squads 
        ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS verification_date TIMESTAMP,
        ADD COLUMN IF NOT EXISTS banned BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS ban_reason TEXT
    """)
    
    # Rate limit tracking
    await db.execute("""
        CREATE TABLE IF NOT EXISTS rate_limit_violations (
            violation_id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            activity_type VARCHAR(100) NOT NULL,
            violation_count INTEGER DEFAULT 1,
            first_violation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_violation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_rate_limit_user (user_id, activity_type)
        )
    """)
    
    logger.info("Security migrations applied successfully")


# ==========================================
# EXAMPLE USAGE
# ==========================================

"""
# Initialize secure education system
secure_edu = SecureEducationSystem(database, logger)

# Create secure API
api = SecureEducationAPI(secure_edu)

# Handle incoming request
async def handle_api_request(request):
    # Extract session from headers/cookies
    session_id = request.headers.get('X-Session-Id')
    
    # Get endpoint and data
    endpoint = request.path.split('/')[-1]
    data = await request.json()
    
    # Process through secure API
    response = await api.handle_request(endpoint, data, session_id)
    
    return web.json_response(response, status=response['code'])

# Squad operation with security
async def create_squad_example(user_id: str):
    # Create session
    context = UserContext(
        user_id=user_id,
        tier='apprentice',
        permissions=['squad.create']
    )
    session_id = secure_edu.session_manager.create_session(user_id, context)
    
    # Create squad
    result = await secure_edu.create_squad_secure(
        session_id,
        "Elite Traders",
        "Victory through discipline!",
        "Trading"
    )
    
    return result
"""