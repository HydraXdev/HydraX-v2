"""
BITTEN Enhanced Social System - Advanced Social Features for Community Engagement
Comprehensive social platform with activity feeds, mentorship, guild competitions, and viral mechanics
"""

import json
import time
import sqlite3
import hashlib
import secrets
import asyncio
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SocialEventType(Enum):
    """Types of social events that can occur"""
    TRADE_WIN = "trade_win"
    TRADE_LOSS = "trade_loss"
    ACHIEVEMENT_EARNED = "achievement_earned"
    RANK_PROMOTION = "rank_promotion"
    STREAK_MILESTONE = "streak_milestone"
    PROFIT_MILESTONE = "profit_milestone"
    FRIEND_ADDED = "friend_added"
    CHALLENGE_COMPLETED = "challenge_completed"
    GUILD_JOINED = "guild_joined"
    MENTORSHIP_STARTED = "mentorship_started"
    CUSTOM_POST = "custom_post"

class RelationshipType(Enum):
    """Types of social relationships"""
    FOLLOWER = "follower"
    FOLLOWING = "following"
    FRIEND = "friend"
    BLOCKED = "blocked"
    MENTOR = "mentor"
    MENTEE = "mentee"
    GUILD_MEMBER = "guild_member"

class PostVisibility(Enum):
    """Post visibility levels"""
    PUBLIC = "public"
    FRIENDS = "friends"
    GUILD = "guild"
    PRIVATE = "private"

@dataclass
class SocialProfile:
    """Enhanced user social profile"""
    user_id: str
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    rank: str = "NIBBLER"
    total_trades: int = 0
    win_rate: float = 0.0
    total_profit: float = 0.0
    follower_count: int = 0
    following_count: int = 0
    friend_count: int = 0
    guild_id: Optional[str] = None
    guild_role: Optional[str] = None
    reputation_score: int = 100
    is_verified: bool = False
    is_mentor: bool = False
    privacy_settings: Dict[str, Any] = field(default_factory=dict)
    achievements: List[str] = field(default_factory=list)
    badges: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)

@dataclass
class SocialPost:
    """Social media style post"""
    post_id: str
    user_id: str
    content: str
    post_type: str = "text"  # text, trade, achievement, milestone
    visibility: PostVisibility = PostVisibility.PUBLIC
    media_urls: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    trade_data: Optional[Dict[str, Any]] = None
    achievement_data: Optional[Dict[str, Any]] = None
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

@dataclass
class SocialInteraction:
    """User interaction with posts"""
    interaction_id: str
    user_id: str
    post_id: str
    interaction_type: str  # like, comment, share, view
    content: Optional[str] = None  # For comments
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class MentorshipMatch:
    """Mentorship pairing"""
    match_id: str
    mentor_id: str
    mentee_id: str
    status: str = "pending"  # pending, active, completed, cancelled
    match_score: float = 0.0
    trading_style_compatibility: float = 0.0
    experience_gap: int = 0
    goals: List[str] = field(default_factory=list)
    progress_milestones: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class Guild:
    """Trading guild/team"""
    guild_id: str
    name: str
    description: str
    founder_id: str
    member_count: int = 0
    max_members: int = 50
    total_profit: float = 0.0
    average_win_rate: float = 0.0
    guild_rank: int = 0
    is_public: bool = True
    requirements: Dict[str, Any] = field(default_factory=dict)
    perks: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

class SocialSystemEnhanced:
    """Enhanced social system for BITTEN platform"""
    
    def __init__(self, db_path: str = "data/social_enhanced.db"):
        self.db_path = db_path
        self._init_database()
        
        # Cache for performance
        self.profile_cache: Dict[str, SocialProfile] = {}
        self.feed_cache: Dict[str, List[Dict]] = {}
        self.cache_expiry = 300  # 5 minutes
        self.cache_timestamps: Dict[str, datetime] = {}
    
    def _init_database(self):
        """Initialize enhanced social database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced user profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_profiles (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT,
                bio TEXT,
                avatar_url TEXT,
                rank TEXT DEFAULT 'NIBBLER',
                total_trades INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.0,
                total_profit REAL DEFAULT 0.0,
                follower_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                friend_count INTEGER DEFAULT 0,
                guild_id TEXT,
                guild_role TEXT,
                reputation_score INTEGER DEFAULT 100,
                is_verified BOOLEAN DEFAULT 0,
                is_mentor BOOLEAN DEFAULT 0,
                privacy_settings TEXT DEFAULT '{}',
                achievements TEXT DEFAULT '[]',
                badges TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Social relationships
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                target_user_id TEXT,
                relationship_type TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, target_user_id, relationship_type)
            )
        ''')
        
        # Social posts/feed
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_posts (
                post_id TEXT PRIMARY KEY,
                user_id TEXT,
                content TEXT,
                post_type TEXT DEFAULT 'text',
                visibility TEXT DEFAULT 'public',
                media_urls TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                mentions TEXT DEFAULT '[]',
                trade_data TEXT,
                achievement_data TEXT,
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                share_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES social_profiles(user_id)
            )
        ''')
        
        # Post interactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_interactions (
                interaction_id TEXT PRIMARY KEY,
                user_id TEXT,
                post_id TEXT,
                interaction_type TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES social_profiles(user_id),
                FOREIGN KEY (post_id) REFERENCES social_posts(post_id)
            )
        ''')
        
        # Mentorship system
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mentorship_matches (
                match_id TEXT PRIMARY KEY,
                mentor_id TEXT,
                mentee_id TEXT,
                status TEXT DEFAULT 'pending',
                match_score REAL DEFAULT 0.0,
                trading_style_compatibility REAL DEFAULT 0.0,
                experience_gap INTEGER DEFAULT 0,
                goals TEXT DEFAULT '[]',
                progress_milestones TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (mentor_id) REFERENCES social_profiles(user_id),
                FOREIGN KEY (mentee_id) REFERENCES social_profiles(user_id)
            )
        ''')
        
        # Guilds/Teams
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                founder_id TEXT,
                member_count INTEGER DEFAULT 0,
                max_members INTEGER DEFAULT 50,
                total_profit REAL DEFAULT 0.0,
                average_win_rate REAL DEFAULT 0.0,
                guild_rank INTEGER DEFAULT 0,
                is_public BOOLEAN DEFAULT 1,
                requirements TEXT DEFAULT '{}',
                perks TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (founder_id) REFERENCES social_profiles(user_id)
            )
        ''')
        
        # Copy trading relationships
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS copy_trading (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower_id TEXT,
                trader_id TEXT,
                copy_percentage REAL DEFAULT 10.0,
                max_copy_amount REAL DEFAULT 100.0,
                is_active BOOLEAN DEFAULT 1,
                total_copied_trades INTEGER DEFAULT 0,
                total_profit REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (follower_id) REFERENCES social_profiles(user_id),
                FOREIGN KEY (trader_id) REFERENCES social_profiles(user_id),
                UNIQUE(follower_id, trader_id)
            )
        ''')
        
        # Social activity feed
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_feed (
                activity_id TEXT PRIMARY KEY,
                user_id TEXT,
                activity_type TEXT,
                title TEXT,
                description TEXT,
                icon TEXT,
                data TEXT DEFAULT '{}',
                visibility TEXT DEFAULT 'public',
                engagement_score REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES social_profiles(user_id)
            )
        ''')
        
        # Viral mechanics tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS viral_actions (
                action_id TEXT PRIMARY KEY,
                user_id TEXT,
                action_type TEXT,
                target_id TEXT,
                viral_score REAL DEFAULT 1.0,
                referral_chain TEXT DEFAULT '[]',
                reward_given REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_social_posts_user ON social_posts(user_id, created_at DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_social_interactions_post ON social_interactions(post_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_relationships_user ON social_relationships(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_feed_user ON activity_feed(user_id, created_at DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mentorship_status ON mentorship_matches(status)')
        
        conn.commit()
        conn.close()
    
    # Profile Management
    def create_profile(self, user_id: str, username: str, **kwargs) -> Tuple[bool, str]:
        """Create enhanced social profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if profile exists
            cursor.execute('SELECT user_id FROM social_profiles WHERE user_id = ?', (user_id,))
            if cursor.fetchone():
                return False, "Profile already exists"
            
            # Create profile
            profile = SocialProfile(
                user_id=user_id,
                username=username,
                display_name=kwargs.get('display_name'),
                bio=kwargs.get('bio'),
                avatar_url=kwargs.get('avatar_url'),
                rank=kwargs.get('rank', 'NIBBLER'),
                privacy_settings=kwargs.get('privacy_settings', {})
            )
            
            cursor.execute('''
                INSERT INTO social_profiles 
                (user_id, username, display_name, bio, avatar_url, rank, privacy_settings)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                profile.user_id, profile.username, profile.display_name,
                profile.bio, profile.avatar_url, profile.rank,
                json.dumps(profile.privacy_settings)
            ))
            
            # Create initial activity
            self._add_activity(user_id, SocialEventType.FRIEND_ADDED, {
                'title': f'{username} joined BITTEN!',
                'description': 'Welcome to the elite trading community',
                'icon': '🎯'
            })
            
            conn.commit()
            return True, "Profile created successfully"
            
        except Exception as e:
            logger.error(f"Error creating profile: {e}")
            return False, f"Failed to create profile: {str(e)}"
        finally:
            conn.close()
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """Update user profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Validate updates
            allowed_fields = {
                'display_name', 'bio', 'avatar_url', 'privacy_settings'
            }
            
            valid_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not valid_updates:
                return False, "No valid fields to update"
            
            # Build update query
            set_clauses = []
            values = []
            
            for field, value in valid_updates.items():
                if field == 'privacy_settings':
                    value = json.dumps(value)
                set_clauses.append(f"{field} = ?")
                values.append(value)
            
            values.append(user_id)
            
            cursor.execute(f'''
                UPDATE social_profiles 
                SET {', '.join(set_clauses)}, last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', values)
            
            if cursor.rowcount == 0:
                return False, "Profile not found"
            
            # Clear cache
            if user_id in self.profile_cache:
                del self.profile_cache[user_id]
            
            conn.commit()
            return True, "Profile updated successfully"
            
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            return False, f"Failed to update profile: {str(e)}"
        finally:
            conn.close()
    
    def get_profile(self, user_id: str) -> Optional[SocialProfile]:
        """Get user social profile with caching"""
        # Check cache
        if user_id in self.profile_cache:
            cache_time = self.cache_timestamps.get(f"profile_{user_id}")
            if cache_time and (datetime.now() - cache_time).total_seconds() < self.cache_expiry:
                return self.profile_cache[user_id]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT user_id, username, display_name, bio, avatar_url, rank,
                       total_trades, win_rate, total_profit, follower_count,
                       following_count, friend_count, guild_id, guild_role,
                       reputation_score, is_verified, is_mentor, privacy_settings,
                       achievements, badges, created_at, last_active
                FROM social_profiles WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            profile = SocialProfile(
                user_id=row[0],
                username=row[1],
                display_name=row[2],
                bio=row[3],
                avatar_url=row[4],
                rank=row[5],
                total_trades=row[6],
                win_rate=row[7],
                total_profit=row[8],
                follower_count=row[9],
                following_count=row[10],
                friend_count=row[11],
                guild_id=row[12],
                guild_role=row[13],
                reputation_score=row[14],
                is_verified=bool(row[15]),
                is_mentor=bool(row[16]),
                privacy_settings=json.loads(row[17] or '{}'),
                achievements=json.loads(row[18] or '[]'),
                badges=json.loads(row[19] or '[]'),
                created_at=datetime.fromisoformat(row[20]),
                last_active=datetime.fromisoformat(row[21])
            )
            
            # Cache the profile
            self.profile_cache[user_id] = profile
            self.cache_timestamps[f"profile_{user_id}"] = datetime.now()
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return None
        finally:
            conn.close()
    
    # Social Relationships
    def follow_user(self, follower_id: str, target_id: str) -> Tuple[bool, str]:
        """Follow another user"""
        if follower_id == target_id:
            return False, "Cannot follow yourself"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if already following
            cursor.execute('''
                SELECT 1 FROM social_relationships 
                WHERE user_id = ? AND target_user_id = ? AND relationship_type = 'following'
            ''', (follower_id, target_id))
            
            if cursor.fetchone():
                return False, "Already following this user"
            
            # Check if target exists
            cursor.execute('SELECT username FROM social_profiles WHERE user_id = ?', (target_id,))
            target_data = cursor.fetchone()
            if not target_data:
                return False, "User not found"
            
            # Create following relationship
            cursor.execute('''
                INSERT INTO social_relationships (user_id, target_user_id, relationship_type)
                VALUES (?, ?, 'following')
            ''', (follower_id, target_id))
            
            # Create follower relationship
            cursor.execute('''
                INSERT INTO social_relationships (user_id, target_user_id, relationship_type)
                VALUES (?, ?, 'follower')
            ''', (target_id, follower_id))
            
            # Update counts
            cursor.execute('''
                UPDATE social_profiles SET following_count = following_count + 1 
                WHERE user_id = ?
            ''', (follower_id,))
            
            cursor.execute('''
                UPDATE social_profiles SET follower_count = follower_count + 1 
                WHERE user_id = ?
            ''', (target_id,))
            
            # Add activity
            follower_profile = self.get_profile(follower_id)
            if follower_profile:
                self._add_activity(target_id, SocialEventType.FRIEND_ADDED, {
                    'title': f'{follower_profile.username} started following you!',
                    'description': f'You gained a new follower',
                    'icon': '👥'
                })
            
            conn.commit()
            return True, f"Now following {target_data[0]}"
            
        except Exception as e:
            logger.error(f"Error following user: {e}")
            return False, "Failed to follow user"
        finally:
            conn.close()
    
    def unfollow_user(self, follower_id: str, target_id: str) -> Tuple[bool, str]:
        """Unfollow a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Remove relationships
            cursor.execute('''
                DELETE FROM social_relationships 
                WHERE user_id = ? AND target_user_id = ? AND relationship_type = 'following'
            ''', (follower_id, target_id))
            
            cursor.execute('''
                DELETE FROM social_relationships 
                WHERE user_id = ? AND target_user_id = ? AND relationship_type = 'follower'
            ''', (target_id, follower_id))
            
            if cursor.rowcount == 0:
                return False, "Not following this user"
            
            # Update counts
            cursor.execute('''
                UPDATE social_profiles SET following_count = following_count - 1 
                WHERE user_id = ? AND following_count > 0
            ''', (follower_id,))
            
            cursor.execute('''
                UPDATE social_profiles SET follower_count = follower_count - 1 
                WHERE user_id = ? AND follower_count > 0
            ''', (target_id,))
            
            conn.commit()
            return True, "Unfollowed successfully"
            
        except Exception as e:
            logger.error(f"Error unfollowing user: {e}")
            return False, "Failed to unfollow user"
        finally:
            conn.close()
    
    # Activity Feed
    def create_post(self, user_id: str, content: str, post_type: str = "text", **kwargs) -> Tuple[bool, str]:
        """Create a social post"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            post_id = f"post_{int(time.time())}_{user_id}"
            
            post = SocialPost(
                post_id=post_id,
                user_id=user_id,
                content=content,
                post_type=post_type,
                visibility=kwargs.get('visibility', PostVisibility.PUBLIC),
                media_urls=kwargs.get('media_urls', []),
                tags=kwargs.get('tags', []),
                mentions=kwargs.get('mentions', []),
                trade_data=kwargs.get('trade_data'),
                achievement_data=kwargs.get('achievement_data')
            )
            
            cursor.execute('''
                INSERT INTO social_posts 
                (post_id, user_id, content, post_type, visibility, media_urls, 
                 tags, mentions, trade_data, achievement_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post.post_id, post.user_id, post.content, post.post_type,
                post.visibility.value, json.dumps(post.media_urls),
                json.dumps(post.tags), json.dumps(post.mentions),
                json.dumps(post.trade_data) if post.trade_data else None,
                json.dumps(post.achievement_data) if post.achievement_data else None
            ))
            
            # Add to activity feed
            self._add_activity(user_id, SocialEventType.CUSTOM_POST, {
                'title': 'New post shared',
                'description': content[:100] + ('...' if len(content) > 100 else ''),
                'icon': '📝',
                'post_id': post_id
            })
            
            # Process mentions for notifications
            for mentioned_user in post.mentions:
                self._notify_mention(mentioned_user, user_id, post_id, content)
            
            conn.commit()
            return True, f"Post created: {post_id}"
            
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return False, "Failed to create post"
        finally:
            conn.close()
    
    def like_post(self, user_id: str, post_id: str) -> Tuple[bool, str]:
        """Like/unlike a post"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if already liked
            cursor.execute('''
                SELECT interaction_id FROM social_interactions 
                WHERE user_id = ? AND post_id = ? AND interaction_type = 'like'
            ''', (user_id, post_id))
            
            if cursor.fetchone():
                # Unlike
                cursor.execute('''
                    DELETE FROM social_interactions 
                    WHERE user_id = ? AND post_id = ? AND interaction_type = 'like'
                ''', (user_id, post_id))
                
                cursor.execute('''
                    UPDATE social_posts SET like_count = like_count - 1 
                    WHERE post_id = ? AND like_count > 0
                ''', (post_id,))
                
                conn.commit()
                return True, "Post unliked"
            else:
                # Like
                interaction_id = f"like_{int(time.time())}_{user_id}"
                cursor.execute('''
                    INSERT INTO social_interactions 
                    (interaction_id, user_id, post_id, interaction_type)
                    VALUES (?, ?, ?, 'like')
                ''', (interaction_id, user_id, post_id))
                
                cursor.execute('''
                    UPDATE social_posts SET like_count = like_count + 1 
                    WHERE post_id = ?
                ''', (post_id,))
                
                # Track viral action
                self._track_viral_action(user_id, 'like', post_id, 0.5)
                
                conn.commit()
                return True, "Post liked"
                
        except Exception as e:
            logger.error(f"Error liking post: {e}")
            return False, "Failed to like post"
        finally:
            conn.close()
    
    def comment_on_post(self, user_id: str, post_id: str, content: str) -> Tuple[bool, str]:
        """Comment on a post"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            interaction_id = f"comment_{int(time.time())}_{user_id}"
            
            cursor.execute('''
                INSERT INTO social_interactions 
                (interaction_id, user_id, post_id, interaction_type, content)
                VALUES (?, ?, ?, 'comment', ?)
            ''', (interaction_id, user_id, post_id, content))
            
            cursor.execute('''
                UPDATE social_posts SET comment_count = comment_count + 1 
                WHERE post_id = ?
            ''', (post_id,))
            
            # Track viral action
            self._track_viral_action(user_id, 'comment', post_id, 1.0)
            
            conn.commit()
            return True, f"Comment added: {interaction_id}"
            
        except Exception as e:
            logger.error(f"Error commenting on post: {e}")
            return False, "Failed to add comment"
        finally:
            conn.close()
    
    def get_activity_feed(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get personalized activity feed"""
        # Check cache
        cache_key = f"feed_{user_id}_{limit}_{offset}"
        if cache_key in self.feed_cache:
            cache_time = self.cache_timestamps.get(cache_key)
            if cache_time and (datetime.now() - cache_time).total_seconds() < self.cache_expiry:
                return self.feed_cache[cache_key]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get posts from followed users and own posts
            cursor.execute('''
                SELECT DISTINCT p.post_id, p.user_id, p.content, p.post_type,
                       p.media_urls, p.tags, p.mentions, p.trade_data,
                       p.achievement_data, p.like_count, p.comment_count,
                       p.share_count, p.created_at, sp.username, sp.avatar_url,
                       sp.rank, sp.is_verified
                FROM social_posts p
                JOIN social_profiles sp ON p.user_id = sp.user_id
                WHERE p.visibility = 'public' 
                   OR p.user_id = ?
                   OR p.user_id IN (
                       SELECT target_user_id FROM social_relationships 
                       WHERE user_id = ? AND relationship_type = 'following'
                   )
                ORDER BY p.created_at DESC
                LIMIT ? OFFSET ?
            ''', (user_id, user_id, limit, offset))
            
            posts = []
            for row in cursor.fetchall():
                post_data = {
                    'post_id': row[0],
                    'user_id': row[1],
                    'content': row[2],
                    'post_type': row[3],
                    'media_urls': json.loads(row[4] or '[]'),
                    'tags': json.loads(row[5] or '[]'),
                    'mentions': json.loads(row[6] or '[]'),
                    'trade_data': json.loads(row[7]) if row[7] else None,
                    'achievement_data': json.loads(row[8]) if row[8] else None,
                    'like_count': row[9],
                    'comment_count': row[10],
                    'share_count': row[11],
                    'created_at': row[12],
                    'username': row[13],
                    'avatar_url': row[14],
                    'rank': row[15],
                    'is_verified': bool(row[16])
                }
                
                # Get recent comments
                cursor.execute('''
                    SELECT si.content, si.created_at, sp.username 
                    FROM social_interactions si
                    JOIN social_profiles sp ON si.user_id = sp.user_id
                    WHERE si.post_id = ? AND si.interaction_type = 'comment'
                    ORDER BY si.created_at DESC LIMIT 3
                ''', (row[0],))
                
                post_data['recent_comments'] = [
                    {
                        'content': comment[0],
                        'created_at': comment[1],
                        'username': comment[2]
                    }
                    for comment in cursor.fetchall()
                ]
                
                # Check if current user liked this post
                cursor.execute('''
                    SELECT 1 FROM social_interactions 
                    WHERE user_id = ? AND post_id = ? AND interaction_type = 'like'
                ''', (user_id, row[0]))
                
                post_data['user_liked'] = bool(cursor.fetchone())
                
                posts.append(post_data)
            
            # Cache the results
            self.feed_cache[cache_key] = posts
            self.cache_timestamps[cache_key] = datetime.now()
            
            return posts
            
        except Exception as e:
            logger.error(f"Error getting activity feed: {e}")
            return []
        finally:
            conn.close()
    
    # Trading Performance Integration
    def update_trading_stats(self, user_id: str, trade_data: Dict[str, Any]) -> None:
        """Update user trading statistics from completed trades"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            profit = trade_data.get('profit', 0)
            is_win = trade_data.get('is_win', False)
            
            # Update profile stats
            cursor.execute('''
                UPDATE social_profiles 
                SET total_trades = total_trades + 1,
                    total_profit = total_profit + ?,
                    win_rate = CASE 
                        WHEN total_trades = 0 THEN ?
                        ELSE (win_rate * total_trades + ?) / (total_trades + 1)
                    END,
                    last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (profit, 1.0 if is_win else 0.0, 1.0 if is_win else 0.0, user_id))
            
            # Create automatic post for significant trades
            if abs(profit) > 100:  # Configurable threshold
                post_content = self._generate_trade_post(trade_data)
                if post_content:
                    self.create_post(
                        user_id, 
                        post_content,
                        post_type="trade",
                        trade_data=trade_data
                    )
            
            # Add to activity feed
            activity_type = SocialEventType.TRADE_WIN if is_win else SocialEventType.TRADE_LOSS
            self._add_activity(user_id, activity_type, {
                'title': f"{'Winning' if is_win else 'Losing'} trade completed",
                'description': f"{'Profit' if profit > 0 else 'Loss'}: ${abs(profit):.2f}",
                'icon': '📈' if is_win else '📉',
                'trade_data': trade_data
            })
            
            # Clear cache
            if user_id in self.profile_cache:
                del self.profile_cache[user_id]
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error updating trading stats: {e}")
        finally:
            conn.close()
    
    # Mentorship System
    def register_as_mentor(self, user_id: str, expertise_areas: List[str], bio: str) -> Tuple[bool, str]:
        """Register user as available mentor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check requirements (example: min trades, win rate, rank)
            profile = self.get_profile(user_id)
            if not profile:
                return False, "Profile not found"
            
            if profile.total_trades < 100:
                return False, "Need at least 100 completed trades to become a mentor"
            
            if profile.win_rate < 0.6:
                return False, "Need at least 60% win rate to become a mentor"
            
            # Update profile
            cursor.execute('''
                UPDATE social_profiles 
                SET is_mentor = 1, bio = COALESCE(?, bio)
                WHERE user_id = ?
            ''', (bio, user_id))
            
            # Add activity
            self._add_activity(user_id, SocialEventType.MENTORSHIP_STARTED, {
                'title': 'Became a mentor!',
                'description': f'Now available to guide new traders in {", ".join(expertise_areas)}',
                'icon': '🎓'
            })
            
            conn.commit()
            return True, "Successfully registered as mentor"
            
        except Exception as e:
            logger.error(f"Error registering mentor: {e}")
            return False, "Failed to register as mentor"
        finally:
            conn.close()
    
    def find_mentor_matches(self, mentee_id: str, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find compatible mentor matches"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            mentee_profile = self.get_profile(mentee_id)
            if not mentee_profile:
                return []
            
            # Get available mentors
            cursor.execute('''
                SELECT sp.user_id, sp.username, sp.bio, sp.total_trades, 
                       sp.win_rate, sp.total_profit, sp.rank
                FROM social_profiles sp
                WHERE sp.is_mentor = 1 
                  AND sp.user_id != ?
                  AND sp.user_id NOT IN (
                      SELECT mentor_id FROM mentorship_matches 
                      WHERE mentee_id = ? AND status IN ('pending', 'active')
                  )
                ORDER BY sp.win_rate DESC, sp.total_trades DESC
                LIMIT 10
            ''', (mentee_id, mentee_id))
            
            matches = []
            for row in cursor.fetchall():
                mentor_data = {
                    'user_id': row[0],
                    'username': row[1],
                    'bio': row[2],
                    'total_trades': row[3],
                    'win_rate': row[4],
                    'total_profit': row[5],
                    'rank': row[6]
                }
                
                # Calculate compatibility score
                score = self._calculate_mentor_compatibility(mentee_profile, mentor_data, preferences)
                mentor_data['compatibility_score'] = score
                
                matches.append(mentor_data)
            
            # Sort by compatibility score
            matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error finding mentor matches: {e}")
            return []
        finally:
            conn.close()
    
    def request_mentorship(self, mentee_id: str, mentor_id: str, message: str) -> Tuple[bool, str]:
        """Request mentorship from a mentor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            match_id = f"mentor_{int(time.time())}_{mentee_id}_{mentor_id}"
            
            # Check if mentor is available
            cursor.execute('''
                SELECT COUNT(*) FROM mentorship_matches 
                WHERE mentor_id = ? AND status = 'active'
            ''', (mentor_id,))
            
            active_mentees = cursor.fetchone()[0]
            if active_mentees >= 5:  # Max 5 active mentees per mentor
                return False, "Mentor is at capacity"
            
            # Create mentorship match
            cursor.execute('''
                INSERT INTO mentorship_matches 
                (match_id, mentor_id, mentee_id, status, goals)
                VALUES (?, ?, ?, 'pending', ?)
            ''', (match_id, mentor_id, mentee_id, json.dumps([message])))
            
            # Notify mentor
            mentor_profile = self.get_profile(mentor_id)
            mentee_profile = self.get_profile(mentee_id)
            
            if mentor_profile and mentee_profile:
                self._add_activity(mentor_id, SocialEventType.MENTORSHIP_STARTED, {
                    'title': 'New mentorship request!',
                    'description': f'{mentee_profile.username} wants you as their mentor',
                    'icon': '🎓',
                    'match_id': match_id
                })
            
            conn.commit()
            return True, f"Mentorship request sent: {match_id}"
            
        except Exception as e:
            logger.error(f"Error requesting mentorship: {e}")
            return False, "Failed to send mentorship request"
        finally:
            conn.close()
    
    # Guild System
    def create_guild(self, founder_id: str, name: str, description: str, **kwargs) -> Tuple[bool, str]:
        """Create a new guild"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            guild_id = f"guild_{int(time.time())}_{founder_id}"
            
            guild = Guild(
                guild_id=guild_id,
                name=name,
                description=description,
                founder_id=founder_id,
                max_members=kwargs.get('max_members', 50),
                is_public=kwargs.get('is_public', True),
                requirements=kwargs.get('requirements', {}),
                perks=kwargs.get('perks', [])
            )
            
            cursor.execute('''
                INSERT INTO guilds 
                (guild_id, name, description, founder_id, max_members, 
                 is_public, requirements, perks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                guild.guild_id, guild.name, guild.description, guild.founder_id,
                guild.max_members, guild.is_public, json.dumps(guild.requirements),
                json.dumps(guild.perks)
            ))
            
            # Add founder to guild
            cursor.execute('''
                UPDATE social_profiles 
                SET guild_id = ?, guild_role = 'founder'
                WHERE user_id = ?
            ''', (guild_id, founder_id))
            
            cursor.execute('''
                UPDATE guilds SET member_count = 1 WHERE guild_id = ?
            ''', (guild_id,))
            
            # Add activity
            self._add_activity(founder_id, SocialEventType.GUILD_JOINED, {
                'title': f'Founded guild "{name}"!',
                'description': description,
                'icon': '⚔️',
                'guild_id': guild_id
            })
            
            conn.commit()
            return True, f"Guild created: {guild_id}"
            
        except Exception as e:
            logger.error(f"Error creating guild: {e}")
            return False, "Failed to create guild"
        finally:
            conn.close()
    
    def join_guild(self, user_id: str, guild_id: str) -> Tuple[bool, str]:
        """Join a guild"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if guild exists and has space
            cursor.execute('''
                SELECT name, member_count, max_members, requirements, is_public
                FROM guilds WHERE guild_id = ?
            ''', (guild_id,))
            
            guild_data = cursor.fetchone()
            if not guild_data:
                return False, "Guild not found"
            
            name, member_count, max_members, requirements, is_public = guild_data
            
            if member_count >= max_members:
                return False, "Guild is at capacity"
            
            # Check if user already in a guild
            cursor.execute('''
                SELECT guild_id FROM social_profiles WHERE user_id = ?
            ''', (user_id,))
            
            current_guild = cursor.fetchone()
            if current_guild and current_guild[0]:
                return False, "Already in a guild"
            
            # Check requirements
            profile = self.get_profile(user_id)
            if not self._check_guild_requirements(profile, json.loads(requirements or '{}')):
                return False, "Does not meet guild requirements"
            
            # Join guild
            cursor.execute('''
                UPDATE social_profiles 
                SET guild_id = ?, guild_role = 'member'
                WHERE user_id = ?
            ''', (guild_id, user_id))
            
            cursor.execute('''
                UPDATE guilds SET member_count = member_count + 1 
                WHERE guild_id = ?
            ''', (guild_id,))
            
            # Add activity
            self._add_activity(user_id, SocialEventType.GUILD_JOINED, {
                'title': f'Joined guild "{name}"!',
                'description': 'Welcome to the guild',
                'icon': '⚔️',
                'guild_id': guild_id
            })
            
            conn.commit()
            return True, f"Joined guild: {name}"
            
        except Exception as e:
            logger.error(f"Error joining guild: {e}")
            return False, "Failed to join guild"
        finally:
            conn.close()
    
    # Copy Trading
    def start_copy_trading(self, follower_id: str, trader_id: str, copy_percentage: float = 10.0, max_amount: float = 100.0) -> Tuple[bool, str]:
        """Start copy trading relationship"""
        if follower_id == trader_id:
            return False, "Cannot copy trade yourself"
        
        if copy_percentage <= 0 or copy_percentage > 100:
            return False, "Copy percentage must be between 0 and 100"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if already copy trading this trader
            cursor.execute('''
                SELECT 1 FROM copy_trading 
                WHERE follower_id = ? AND trader_id = ? AND is_active = 1
            ''', (follower_id, trader_id))
            
            if cursor.fetchone():
                return False, "Already copy trading this trader"
            
            # Check trader's performance and rank
            trader_profile = self.get_profile(trader_id)
            if not trader_profile:
                return False, "Trader not found"
            
            if trader_profile.total_trades < 50:
                return False, "Trader must have at least 50 trades"
            
            if trader_profile.win_rate < 0.55:
                return False, "Trader must have at least 55% win rate"
            
            # Create copy trading relationship
            cursor.execute('''
                INSERT OR REPLACE INTO copy_trading 
                (follower_id, trader_id, copy_percentage, max_copy_amount, is_active)
                VALUES (?, ?, ?, ?, 1)
            ''', (follower_id, trader_id, copy_percentage, max_amount))
            
            # Add activity
            self._add_activity(follower_id, SocialEventType.FRIEND_ADDED, {
                'title': f'Started copy trading {trader_profile.username}!',
                'description': f'Copying {copy_percentage}% of trades (max ${max_amount})',
                'icon': '📊'
            })
            
            conn.commit()
            return True, f"Started copy trading {trader_profile.username}"
            
        except Exception as e:
            logger.error(f"Error starting copy trading: {e}")
            return False, "Failed to start copy trading"
        finally:
            conn.close()
    
    # Viral Mechanics
    def _track_viral_action(self, user_id: str, action_type: str, target_id: str, viral_score: float) -> None:
        """Track viral actions for growth mechanics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            action_id = f"viral_{int(time.time())}_{user_id}"
            
            # Get referral chain
            referral_chain = self._get_referral_chain(user_id)
            
            cursor.execute('''
                INSERT INTO viral_actions 
                (action_id, user_id, action_type, target_id, viral_score, referral_chain)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (action_id, user_id, action_type, target_id, viral_score, json.dumps(referral_chain)))
            
            # Award viral rewards to referral chain
            for i, referrer_id in enumerate(referral_chain[:3]):  # Max 3 levels
                reward = viral_score * (0.5 ** i)  # Decreasing rewards
                
                if reward >= 0.1:  # Minimum reward threshold
                    # In production, integrate with XP system
                    pass
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error tracking viral action: {e}")
        finally:
            conn.close()
    
    def get_viral_stats(self, user_id: str) -> Dict[str, Any]:
        """Get viral growth statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get direct viral actions
            cursor.execute('''
                SELECT action_type, COUNT(*), SUM(viral_score)
                FROM viral_actions 
                WHERE user_id = ?
                GROUP BY action_type
            ''', (user_id,))
            
            viral_actions = {row[0]: {'count': row[1], 'score': row[2]} for row in cursor.fetchall()}
            
            # Get referral chain impact
            cursor.execute('''
                SELECT COUNT(*), SUM(viral_score), SUM(reward_given)
                FROM viral_actions 
                WHERE JSON_EXTRACT(referral_chain, '$[0]') = ?
            ''', (user_id,))
            
            chain_impact = cursor.fetchone()
            
            return {
                'direct_actions': viral_actions,
                'chain_impact': {
                    'total_actions': chain_impact[0] or 0,
                    'total_score': chain_impact[1] or 0.0,
                    'total_rewards': chain_impact[2] or 0.0
                },
                'viral_coefficient': self._calculate_viral_coefficient(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting viral stats: {e}")
            return {}
        finally:
            conn.close()
    
    # Helper Methods
    def _add_activity(self, user_id: str, event_type: SocialEventType, data: Dict[str, Any]) -> None:
        """Add activity to user's feed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            activity_id = f"activity_{int(time.time())}_{user_id}"
            
            cursor.execute('''
                INSERT INTO activity_feed 
                (activity_id, user_id, activity_type, title, description, icon, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity_id, user_id, event_type.value,
                data.get('title', ''), data.get('description', ''),
                data.get('icon', '📊'), json.dumps(data)
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error adding activity: {e}")
        finally:
            conn.close()
    
    def _generate_trade_post(self, trade_data: Dict[str, Any]) -> Optional[str]:
        """Generate automatic trade post content"""
        try:
            profit = trade_data.get('profit', 0)
            pair = trade_data.get('pair', 'Unknown')
            direction = trade_data.get('direction', 'Unknown')
            
            if profit > 0:
                return f"🚀 Just closed a profitable {direction} trade on {pair}! +${profit:.2f} profit! #TradingWin #BITTEN"
            else:
                return f"📚 Learning experience on {pair}. Every trade teaches us something valuable. #TradingJourney #BITTEN"
                
        except Exception:
            return None
    
    def _notify_mention(self, mentioned_user: str, mentioning_user: str, post_id: str, content: str) -> None:
        """Notify user when mentioned in a post"""
        # In production, integrate with notification system
        self._add_activity(mentioned_user, SocialEventType.FRIEND_ADDED, {
            'title': 'You were mentioned in a post!',
            'description': content[:100] + ('...' if len(content) > 100 else ''),
            'icon': '📢',
            'post_id': post_id,
            'mentioning_user': mentioning_user
        })
    
    def _calculate_mentor_compatibility(self, mentee: SocialProfile, mentor: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        """Calculate mentor-mentee compatibility score"""
        score = 0.0
        
        # Experience gap (ideal: mentor has 3-10x more experience)
        experience_ratio = mentor['total_trades'] / max(mentee.total_trades, 1)
        if 3 <= experience_ratio <= 10:
            score += 30
        elif experience_ratio > 10:
            score += 20
        else:
            score += 10
        
        # Performance differential
        performance_gap = mentor['win_rate'] - mentee.win_rate
        if 0.1 <= performance_gap <= 0.3:
            score += 25
        elif performance_gap > 0.3:
            score += 20
        else:
            score += 10
        
        # Rank compatibility
        rank_weights = {'': 5, 'COMMANDER': 4, 'FANG': 3, 'SNIPER': 2, 'NIBBLER': 1}
        mentor_rank_weight = rank_weights.get(mentor['rank'], 1)
        mentee_rank_weight = rank_weights.get(mentee.rank, 1)
        
        if mentor_rank_weight > mentee_rank_weight:
            score += 20
        
        # Profit track record
        if mentor['total_profit'] > 1000:
            score += 15
        elif mentor['total_profit'] > 500:
            score += 10
        
        # Normalize to 0-100
        return min(score, 100.0)
    
    def _check_guild_requirements(self, profile: SocialProfile, requirements: Dict[str, Any]) -> bool:
        """Check if user meets guild requirements"""
        if requirements.get('min_trades', 0) > profile.total_trades:
            return False
        
        if requirements.get('min_win_rate', 0) > profile.win_rate:
            return False
        
        if requirements.get('min_profit', 0) > profile.total_profit:
            return False
        
        required_rank_weights = {'': 5, 'COMMANDER': 4, 'FANG': 3, 'SNIPER': 2, 'NIBBLER': 1}
        user_rank_weight = required_rank_weights.get(profile.rank, 1)
        min_rank_weight = required_rank_weights.get(requirements.get('min_rank', 'NIBBLER'), 1)
        
        if user_rank_weight < min_rank_weight:
            return False
        
        return True
    
    def _get_referral_chain(self, user_id: str) -> List[str]:
        """Get referral chain for viral mechanics"""
        # In production, integrate with referral system
        # This is a placeholder implementation
        return []
    
    def _calculate_viral_coefficient(self, user_id: str) -> float:
        """Calculate user's viral coefficient"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Calculate based on actions that lead to new user acquisitions
            cursor.execute('''
                SELECT COUNT(*) FROM viral_actions 
                WHERE user_id = ? AND action_type IN ('share', 'referral', 'invite')
            ''', (user_id,))
            
            viral_actions = cursor.fetchone()[0] or 0
            
            # Get follower count for normalization
            profile = self.get_profile(user_id)
            follower_count = profile.follower_count if profile else 1
            
            # Calculate coefficient (viral actions per follower)
            coefficient = viral_actions / max(follower_count, 1)
            
            return min(coefficient, 10.0)  # Cap at 10.0
            
        except Exception as e:
            logger.error(f"Error calculating viral coefficient: {e}")
            return 0.0
        finally:
            conn.close()

# Integration with existing systems
class SocialIntegration:
    """Integration hooks for social system"""
    
    def __init__(self, social_system: SocialSystemEnhanced):
        self.social_system = social_system
    
    def on_trade_completed(self, user_id: str, trade_data: Dict[str, Any]) -> None:
        """Called when a trade is completed"""
        self.social_system.update_trading_stats(user_id, trade_data)
    
    def on_achievement_earned(self, user_id: str, achievement_data: Dict[str, Any]) -> None:
        """Called when an achievement is earned"""
        self.social_system.create_post(
            user_id,
            f"🏆 Achievement unlocked: {achievement_data.get('name', 'Unknown')}!",
            post_type="achievement",
            achievement_data=achievement_data
        )
    
    def on_rank_promotion(self, user_id: str, new_rank: str, old_rank: str) -> None:
        """Called when rank is promoted"""
        self.social_system.create_post(
            user_id,
            f"🎖️ Promoted to {new_rank} rank! Moving up in the BITTEN elite!",
            post_type="milestone"
        )

# Example usage and testing
if __name__ == "__main__":
    # Initialize system
    social_system = SocialSystemEnhanced()
    
    # Create test profiles
    social_system.create_profile("user1", "EliteTrader", display_name="Elite Trader", bio="Professional forex trader")
    social_system.create_profile("user2", "NewbieJoe", display_name="Newbie Joe", bio="Learning to trade")
    
    # Test following
    success, msg = social_system.follow_user("user2", "user1")
    print(f"Follow result: {msg}")
    
    # Test posting
    success, msg = social_system.create_post("user1", "Just had an amazing trading session! 🚀 #forex #profits")
    print(f"Post result: {msg}")
    
    # Test activity feed
    feed = social_system.get_activity_feed("user2")
    print(f"Feed items: {len(feed)}")
    
    # Test mentorship
    success, msg = social_system.register_as_mentor("user1", ["Forex", "Risk Management"], "Experienced trader")
    print(f"Mentor registration: {msg}")
    
    matches = social_system.find_mentor_matches("user2", {"trading_style": "conservative"})
    print(f"Mentor matches: {len(matches)}")