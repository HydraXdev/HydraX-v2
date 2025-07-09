"""
Netflix-Style Educational Content Delivery System for HydraX
Implements streaming platform mechanics for trading education
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import hashlib

from src.bitten_core.database import Database
from src.bitten_core.logger import Logger
from src.bitten_core.education_system import TradingTier, EducationTopic
from src.bitten_core.xp_economy import XPEconomy
from src.bitten_core.reward_system import RewardSystem


class ContentType(Enum):
    """Types of educational content"""
    VIDEO = "video"
    INTERACTIVE = "interactive"
    LIVE_SESSION = "live_session"
    DOCUMENTARY = "documentary"
    SERIES = "series"
    WORKSHOP = "workshop"
    MASTERCLASS = "masterclass"


class ViewingStatus(Enum):
    """Content viewing status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DOWNLOADED = "downloaded"


class ContentRating(Enum):
    """Content difficulty ratings (like movie ratings)"""
    BEGINNER = "beginner"  # G - General audiences
    INTERMEDIATE = "intermediate"  # PG - Parental guidance
    ADVANCED = "advanced"  # PG-13 - More complex
    EXPERT = "expert"  # R - Restricted to experienced
    MASTER = "master"  # NC-17 - Master tier only


@dataclass
class Episode:
    """Individual episode in a series"""
    episode_id: str
    season_number: int
    episode_number: int
    title: str
    description: str
    duration_minutes: int
    thumbnail_url: str
    video_url: str
    tier_required: TradingTier
    xp_reward: int
    checkpoint_timestamps: List[int] = field(default_factory=list)  # Minutes for interactive checkpoints
    quiz_questions: List[Dict[str, Any]] = field(default_factory=list)
    prerequisite_episodes: List[str] = field(default_factory=list)


@dataclass
class Season:
    """Season of educational content"""
    season_id: str
    season_number: int
    title: str
    description: str
    tier_required: TradingTier
    episodes: List[Episode] = field(default_factory=list)
    total_xp_available: int = 0
    completion_bonus_xp: int = 0
    trailer_url: Optional[str] = None


@dataclass
class Series:
    """Educational content series (like Netflix shows)"""
    series_id: str
    title: str
    description: str
    category: EducationTopic
    rating: ContentRating
    seasons: List[Season] = field(default_factory=list)
    total_episodes: int = 0
    average_episode_length: int = 0
    tags: List[str] = field(default_factory=list)
    featured: bool = False
    release_date: datetime = field(default_factory=datetime.utcnow)
    popularity_score: float = 0.0


@dataclass
class ViewingProgress:
    """User's viewing progress for content"""
    user_id: str
    content_id: str
    content_type: ContentType
    status: ViewingStatus
    progress_percentage: float
    last_watched_timestamp: datetime
    total_watch_time_minutes: int
    completed_checkpoints: List[str] = field(default_factory=list)
    quiz_scores: Dict[str, float] = field(default_factory=dict)
    downloaded_for_offline: bool = False
    download_expiry: Optional[datetime] = None


@dataclass
class ViewingParty:
    """Group viewing session"""
    party_id: str
    host_user_id: str
    content_id: str
    scheduled_time: datetime
    max_participants: int
    participants: List[str] = field(default_factory=list)
    chat_enabled: bool = True
    synchronized_playback: bool = True
    completion_bonus_xp: int = 50
    status: str = "scheduled"  # scheduled, active, completed, cancelled


@dataclass
class BingeReward:
    """Rewards for binge-watching sessions"""
    episodes_watched: int
    time_window_hours: int
    xp_bonus: int
    achievement_id: Optional[str] = None
    special_unlock: Optional[str] = None


class EducationContentDelivery:
    """Netflix-style content delivery system"""
    
    def __init__(self, database: Database, logger: Logger, xp_economy: XPEconomy, 
                 reward_system: RewardSystem):
        self.db = database
        self.logger = logger
        self.xp_economy = xp_economy
        self.reward_system = reward_system
        
        # Content library
        self.series_library: Dict[str, Series] = {}
        self.featured_content: List[str] = []
        
        # Viewing tracking
        self.active_viewing: Dict[str, ViewingProgress] = {}
        self.viewing_parties: Dict[str, ViewingParty] = {}
        
        # Binge rewards configuration
        self.binge_rewards = self._initialize_binge_rewards()
        
        # Recommendation engine data
        self.user_preferences: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.content_embeddings: Dict[str, List[float]] = {}
        
        # Download management
        self.offline_downloads: Dict[str, List[str]] = defaultdict(list)
        self.download_limits = {
            TradingTier.NIBBLER: 5,
            TradingTier.APPRENTICE: 10,
            TradingTier.JOURNEYMAN: 20,
            TradingTier.MASTER: 50,
            TradingTier.GRANDMASTER: 100
        }
        
        # Initialize content and database
        asyncio.create_task(self._initialize_system())
    
    async def _initialize_system(self):
        """Initialize the content delivery system"""
        await self._initialize_database()
        await self._initialize_content_library()
        await self._load_user_progress()
    
    async def _initialize_database(self):
        """Initialize database tables for content system"""
        try:
            # Viewing progress table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS viewing_progress (
                    progress_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress_percentage REAL DEFAULT 0,
                    last_watched TIMESTAMP,
                    total_watch_time INTEGER DEFAULT 0,
                    completed_checkpoints TEXT DEFAULT '[]',
                    quiz_scores TEXT DEFAULT '{}',
                    downloaded_offline BOOLEAN DEFAULT FALSE,
                    download_expiry TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Viewing parties table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS viewing_parties (
                    party_id TEXT PRIMARY KEY,
                    host_user_id TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    scheduled_time TIMESTAMP NOT NULL,
                    max_participants INTEGER DEFAULT 10,
                    participants TEXT DEFAULT '[]',
                    chat_enabled BOOLEAN DEFAULT TRUE,
                    synchronized_playback BOOLEAN DEFAULT TRUE,
                    completion_bonus_xp INTEGER DEFAULT 50,
                    status TEXT DEFAULT 'scheduled',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (host_user_id) REFERENCES users(user_id)
                )
            """)
            
            # Content interactions table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS content_interactions (
                    interaction_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    interaction_type TEXT NOT NULL,
                    interaction_data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Binge tracking table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS binge_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    episodes_watched INTEGER DEFAULT 0,
                    total_xp_earned INTEGER DEFAULT 0,
                    achievements_unlocked TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            self.logger.info("Education content delivery database initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize content database: {e}")
    
    def _initialize_binge_rewards(self) -> List[BingeReward]:
        """Initialize binge-watching rewards"""
        return [
            BingeReward(
                episodes_watched=3,
                time_window_hours=4,
                xp_bonus=50,
                achievement_id="weekend_warrior"
            ),
            BingeReward(
                episodes_watched=5,
                time_window_hours=8,
                xp_bonus=100,
                achievement_id="dedicated_learner",
                special_unlock="bonus_masterclass"
            ),
            BingeReward(
                episodes_watched=10,
                time_window_hours=24,
                xp_bonus=250,
                achievement_id="education_marathon",
                special_unlock="exclusive_strategy_series"
            ),
            BingeReward(
                episodes_watched=20,
                time_window_hours=48,
                xp_bonus=500,
                achievement_id="knowledge_seeker",
                special_unlock="private_mentorship_session"
            )
        ]
    
    async def _initialize_content_library(self):
        """Initialize the educational content library"""
        # Nibbler Season 1: Trading Basics
        nibbler_s1 = Season(
            season_id="nibbler_s1",
            season_number=1,
            title="Nibbler Bootcamp: Trading Fundamentals",
            description="Start your trading journey with essential concepts",
            tier_required=TradingTier.NIBBLER,
            episodes=[
                Episode(
                    episode_id="nib_s1e1",
                    season_number=1,
                    episode_number=1,
                    title="Welcome to Trading: Your First Steps",
                    description="Introduction to markets, terminology, and mindset",
                    duration_minutes=25,
                    thumbnail_url="/content/thumbnails/nib_s1e1.jpg",
                    video_url="/content/videos/nib_s1e1.mp4",
                    tier_required=TradingTier.NIBBLER,
                    xp_reward=50,
                    checkpoint_timestamps=[5, 15, 20],
                    quiz_questions=[
                        {
                            "timestamp": 5,
                            "question": "What is the primary purpose of stop loss?",
                            "options": ["Maximize profit", "Limit losses", "Enter trades", "Time the market"],
                            "correct": 1,
                            "xp_reward": 10
                        }
                    ]
                ),
                Episode(
                    episode_id="nib_s1e2",
                    season_number=1,
                    episode_number=2,
                    title="Risk Management 101: Protecting Your Capital",
                    description="Learn the 1% rule and position sizing basics",
                    duration_minutes=30,
                    thumbnail_url="/content/thumbnails/nib_s1e2.jpg",
                    video_url="/content/videos/nib_s1e2.mp4",
                    tier_required=TradingTier.NIBBLER,
                    xp_reward=75,
                    checkpoint_timestamps=[10, 20, 25],
                    prerequisite_episodes=["nib_s1e1"]
                ),
                Episode(
                    episode_id="nib_s1e3",
                    season_number=1,
                    episode_number=3,
                    title="Chart Reading Basics: Support & Resistance",
                    description="Identify key levels and understand price action",
                    duration_minutes=35,
                    thumbnail_url="/content/thumbnails/nib_s1e3.jpg",
                    video_url="/content/videos/nib_s1e3.mp4",
                    tier_required=TradingTier.NIBBLER,
                    xp_reward=100,
                    checkpoint_timestamps=[10, 20, 30],
                    prerequisite_episodes=["nib_s1e2"]
                )
            ],
            total_xp_available=225,
            completion_bonus_xp=100,
            trailer_url="/content/trailers/nibbler_s1_trailer.mp4"
        )
        
        # Nibbler Season 2: Psychology & Discipline
        nibbler_s2 = Season(
            season_id="nibbler_s2",
            season_number=2,
            title="Mind Over Markets: Trading Psychology",
            description="Master your emotions and develop discipline",
            tier_required=TradingTier.NIBBLER,
            episodes=[
                Episode(
                    episode_id="nib_s2e1",
                    season_number=2,
                    episode_number=1,
                    title="FOMO & Greed: Your Worst Enemies",
                    description="Recognize and overcome emotional trading",
                    duration_minutes=28,
                    thumbnail_url="/content/thumbnails/nib_s2e1.jpg",
                    video_url="/content/videos/nib_s2e1.mp4",
                    tier_required=TradingTier.NIBBLER,
                    xp_reward=80,
                    checkpoint_timestamps=[8, 16, 24]
                )
            ],
            total_xp_available=300,
            completion_bonus_xp=150
        )
        
        # Create Nibbler series
        nibbler_series = Series(
            series_id="nibbler_complete",
            title="The Complete Nibbler Training Program",
            description="Everything beginners need to start trading safely",
            category=EducationTopic.STRATEGY_BASICS,
            rating=ContentRating.BEGINNER,
            seasons=[nibbler_s1, nibbler_s2],
            total_episodes=6,
            average_episode_length=30,
            tags=["beginner", "fundamentals", "risk-management", "psychology"],
            featured=True,
            popularity_score=0.95
        )
        
        # Apprentice Series: Technical Analysis
        apprentice_ta_s1 = Season(
            season_id="apprentice_ta_s1",
            season_number=1,
            title="Technical Analysis Mastery",
            description="Deep dive into indicators and patterns",
            tier_required=TradingTier.APPRENTICE,
            episodes=[
                Episode(
                    episode_id="app_ta_s1e1",
                    season_number=1,
                    episode_number=1,
                    title="Moving Averages: The Foundation",
                    description="Master SMA, EMA, and crossover strategies",
                    duration_minutes=40,
                    thumbnail_url="/content/thumbnails/app_ta_s1e1.jpg",
                    video_url="/content/videos/app_ta_s1e1.mp4",
                    tier_required=TradingTier.APPRENTICE,
                    xp_reward=150,
                    checkpoint_timestamps=[10, 20, 30, 38]
                )
            ],
            total_xp_available=500,
            completion_bonus_xp=250
        )
        
        apprentice_series = Series(
            series_id="apprentice_technical",
            title="Technical Analysis: From Patterns to Profits",
            description="Advanced technical analysis for intermediate traders",
            category=EducationTopic.TECHNICAL_ANALYSIS,
            rating=ContentRating.INTERMEDIATE,
            seasons=[apprentice_ta_s1],
            total_episodes=8,
            average_episode_length=45,
            tags=["technical-analysis", "indicators", "patterns", "intermediate"],
            featured=True,
            popularity_score=0.88
        )
        
        # Master Series: Advanced Strategies
        master_strategies = Series(
            series_id="master_strategies",
            title="Elite Trading Strategies",
            description="Professional-grade strategies used by top traders",
            category=EducationTopic.ADVANCED_STRATEGIES,
            rating=ContentRating.EXPERT,
            seasons=[],  # Would be populated with actual content
            total_episodes=12,
            average_episode_length=60,
            tags=["advanced", "professional", "strategies", "master-only"],
            featured=False,
            popularity_score=0.92
        )
        
        # Add to library
        self.series_library = {
            "nibbler_complete": nibbler_series,
            "apprentice_technical": apprentice_series,
            "master_strategies": master_strategies
        }
        
        # Set featured content
        self.featured_content = ["nibbler_complete", "apprentice_technical"]
        
        # Generate content embeddings for recommendations
        await self._generate_content_embeddings()
    
    async def _generate_content_embeddings(self):
        """Generate embeddings for content recommendation"""
        for series_id, series in self.series_library.items():
            # Simple embedding based on tags and category
            embedding = []
            
            # Category embedding
            categories = list(EducationTopic)
            category_vector = [1.0 if series.category == cat else 0.0 for cat in categories]
            embedding.extend(category_vector)
            
            # Tag embedding (simplified)
            all_tags = ["beginner", "intermediate", "advanced", "fundamentals", 
                       "technical-analysis", "psychology", "risk-management", "strategies"]
            tag_vector = [1.0 if tag in series.tags else 0.0 for tag in all_tags]
            embedding.extend(tag_vector)
            
            # Popularity score
            embedding.append(series.popularity_score)
            
            self.content_embeddings[series_id] = embedding
    
    async def _load_user_progress(self):
        """Load active user viewing progress"""
        try:
            active_progress = await self.db.fetch_all("""
                SELECT * FROM viewing_progress 
                WHERE status IN ('in_progress', 'downloaded')
                AND last_watched > ?
            """, (datetime.utcnow() - timedelta(days=30),))
            
            for progress in active_progress:
                viewing = ViewingProgress(
                    user_id=progress['user_id'],
                    content_id=progress['content_id'],
                    content_type=ContentType(progress['content_type']),
                    status=ViewingStatus(progress['status']),
                    progress_percentage=progress['progress_percentage'],
                    last_watched_timestamp=progress['last_watched'],
                    total_watch_time_minutes=progress['total_watch_time'],
                    completed_checkpoints=json.loads(progress['completed_checkpoints']),
                    quiz_scores=json.loads(progress['quiz_scores']),
                    downloaded_for_offline=progress['downloaded_offline'],
                    download_expiry=progress['download_expiry']
                )
                self.active_viewing[f"{progress['user_id']}_{progress['content_id']}"] = viewing
            
        except Exception as e:
            self.logger.error(f"Failed to load user progress: {e}")
    
    async def get_home_screen(self, user_id: str, tier: TradingTier) -> Dict[str, Any]:
        """Get Netflix-style home screen with personalized content"""
        home_data = {
            "continue_watching": await self._get_continue_watching(user_id),
            "featured": await self._get_featured_content(tier),
            "recommended_for_you": await self._get_recommendations(user_id, tier),
            "trending_now": await self._get_trending_content(),
            "new_releases": await self._get_new_releases(tier),
            "my_list": await self._get_user_list(user_id),
            "categories": await self._get_categories(tier),
            "upcoming_parties": await self._get_upcoming_parties(user_id)
        }
        
        return home_data
    
    async def _get_continue_watching(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's continue watching list"""
        continue_list = []
        
        for key, progress in self.active_viewing.items():
            if progress.user_id == user_id and progress.status == ViewingStatus.IN_PROGRESS:
                # Find the content
                for series_id, series in self.series_library.items():
                    for season in series.seasons:
                        for episode in season.episodes:
                            if episode.episode_id == progress.content_id:
                                continue_list.append({
                                    "content_id": episode.episode_id,
                                    "series_id": series_id,
                                    "title": f"{series.title}: {episode.title}",
                                    "thumbnail": episode.thumbnail_url,
                                    "progress": progress.progress_percentage,
                                    "duration": episode.duration_minutes,
                                    "resume_position": int(episode.duration_minutes * progress.progress_percentage / 100),
                                    "last_watched": progress.last_watched_timestamp
                                })
        
        # Sort by last watched
        continue_list.sort(key=lambda x: x['last_watched'], reverse=True)
        return continue_list[:10]
    
    async def _get_featured_content(self, tier: TradingTier) -> List[Dict[str, Any]]:
        """Get featured content for user's tier"""
        featured = []
        
        for series_id in self.featured_content:
            series = self.series_library.get(series_id)
            if series and self._can_access_series(series, tier):
                featured.append({
                    "series_id": series_id,
                    "title": series.title,
                    "description": series.description,
                    "banner_image": f"/content/banners/{series_id}.jpg",
                    "rating": series.rating.value,
                    "total_episodes": series.total_episodes,
                    "tags": series.tags[:3]
                })
        
        return featured
    
    async def _get_recommendations(self, user_id: str, tier: TradingTier) -> List[Dict[str, Any]]:
        """Get personalized recommendations using collaborative filtering"""
        recommendations = []
        
        # Get user's viewing history
        user_history = await self.db.fetch_all("""
            SELECT content_id, interaction_type, interaction_data
            FROM content_interactions
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 50
        """, (user_id,))
        
        # Calculate user preferences
        if user_history:
            # Update user preference vector based on history
            for interaction in user_history:
                content_id = interaction['content_id']
                interaction_type = interaction['interaction_type']
                
                # Weight different interactions
                weight = {
                    'completed': 1.0,
                    'liked': 0.8,
                    'watched': 0.5,
                    'clicked': 0.3
                }.get(interaction_type, 0.1)
                
                # Find series containing this content
                for series_id, series in self.series_library.items():
                    if self._series_contains_content(series, content_id):
                        # Update preferences for this series' features
                        for tag in series.tags:
                            self.user_preferences[user_id][tag] += weight
                        self.user_preferences[user_id][series.category.value] += weight
        
        # Calculate content scores
        content_scores = []
        for series_id, series in self.series_library.items():
            if self._can_access_series(series, tier):
                # Calculate similarity score
                score = 0.0
                
                # Tag similarity
                for tag in series.tags:
                    score += self.user_preferences[user_id].get(tag, 0.0)
                
                # Category similarity
                score += self.user_preferences[user_id].get(series.category.value, 0.0) * 2
                
                # Popularity boost
                score += series.popularity_score * 0.5
                
                # Avoid already watched content
                if await self._has_completed_series(user_id, series_id):
                    score *= 0.1
                
                content_scores.append((series_id, score))
        
        # Sort by score and get top recommendations
        content_scores.sort(key=lambda x: x[1], reverse=True)
        
        for series_id, score in content_scores[:8]:
            series = self.series_library[series_id]
            recommendations.append({
                "series_id": series_id,
                "title": series.title,
                "description": series.description[:100] + "...",
                "thumbnail": f"/content/thumbnails/{series_id}.jpg",
                "match_percentage": min(int(score * 20 + 60), 98),  # Netflix-style match %
                "tags": series.tags[:2]
            })
        
        return recommendations
    
    async def _get_trending_content(self) -> List[Dict[str, Any]]:
        """Get trending content based on recent activity"""
        # In a real system, this would analyze recent viewing patterns
        trending = []
        
        # Sort by popularity score
        sorted_series = sorted(self.series_library.items(), 
                             key=lambda x: x[1].popularity_score, 
                             reverse=True)
        
        for series_id, series in sorted_series[:5]:
            trending.append({
                "series_id": series_id,
                "title": series.title,
                "thumbnail": f"/content/thumbnails/{series_id}.jpg",
                "trending_rank": len(trending) + 1,
                "category": series.category.value
            })
        
        return trending
    
    async def _get_new_releases(self, tier: TradingTier) -> List[Dict[str, Any]]:
        """Get new content releases"""
        new_releases = []
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        for series_id, series in self.series_library.items():
            if (series.release_date > cutoff_date and 
                self._can_access_series(series, tier)):
                new_releases.append({
                    "series_id": series_id,
                    "title": series.title,
                    "thumbnail": f"/content/thumbnails/{series_id}.jpg",
                    "release_date": series.release_date,
                    "is_new": True
                })
        
        return new_releases
    
    async def _get_user_list(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's saved content list"""
        # This would fetch from a user_lists table
        return []
    
    async def _get_categories(self, tier: TradingTier) -> List[Dict[str, Any]]:
        """Get content categories"""
        categories = []
        
        for topic in EducationTopic:
            category_series = []
            for series_id, series in self.series_library.items():
                if (series.category == topic and 
                    self._can_access_series(series, tier)):
                    category_series.append({
                        "series_id": series_id,
                        "title": series.title,
                        "thumbnail": f"/content/thumbnails/{series_id}_small.jpg"
                    })
            
            if category_series:
                categories.append({
                    "category": topic.value,
                    "display_name": topic.value.replace("_", " ").title(),
                    "series": category_series[:10]
                })
        
        return categories
    
    async def _get_upcoming_parties(self, user_id: str) -> List[Dict[str, Any]]:
        """Get upcoming viewing parties"""
        parties = []
        
        upcoming = await self.db.fetch_all("""
            SELECT * FROM viewing_parties
            WHERE (host_user_id = ? OR participants LIKE ?)
            AND scheduled_time > ?
            AND status = 'scheduled'
            ORDER BY scheduled_time
            LIMIT 5
        """, (user_id, f'%{user_id}%', datetime.utcnow()))
        
        for party in upcoming:
            parties.append({
                "party_id": party['party_id'],
                "content_id": party['content_id'],
                "scheduled_time": party['scheduled_time'],
                "participant_count": len(json.loads(party['participants'])) + 1,
                "is_host": party['host_user_id'] == user_id
            })
        
        return parties
    
    async def start_watching(self, user_id: str, content_id: str) -> Dict[str, Any]:
        """Start watching content"""
        # Check if user can access content
        episode = await self._get_episode_by_id(content_id)
        if not episode:
            return {"error": "Content not found"}
        
        user_tier = await self._get_user_tier(user_id)
        if not self._can_access_episode(episode, user_tier):
            return {"error": f"This content requires {episode.tier_required.value} tier"}
        
        # Check prerequisites
        if episode.prerequisite_episodes:
            for prereq_id in episode.prerequisite_episodes:
                if not await self._has_completed_episode(user_id, prereq_id):
                    return {"error": "Complete prerequisite episodes first"}
        
        # Create or update viewing progress
        progress_key = f"{user_id}_{content_id}"
        if progress_key in self.active_viewing:
            progress = self.active_viewing[progress_key]
        else:
            progress = ViewingProgress(
                user_id=user_id,
                content_id=content_id,
                content_type=ContentType.VIDEO,
                status=ViewingStatus.IN_PROGRESS,
                progress_percentage=0.0,
                last_watched_timestamp=datetime.utcnow(),
                total_watch_time_minutes=0
            )
            self.active_viewing[progress_key] = progress
        
        # Update last watched
        progress.last_watched_timestamp = datetime.utcnow()
        await self._save_viewing_progress(progress)
        
        # Track interaction
        await self._track_interaction(user_id, content_id, "started")
        
        # Check for active binge session
        binge_info = await self._check_binge_session(user_id)
        
        return {
            "success": True,
            "episode": {
                "episode_id": episode.episode_id,
                "title": episode.title,
                "video_url": episode.video_url,
                "duration": episode.duration_minutes,
                "checkpoints": episode.checkpoint_timestamps,
                "current_progress": progress.progress_percentage,
                "completed_checkpoints": progress.completed_checkpoints
            },
            "binge_session": binge_info
        }
    
    async def update_progress(self, user_id: str, content_id: str, 
                            progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update watching progress with checkpoint handling"""
        progress_key = f"{user_id}_{content_id}"
        if progress_key not in self.active_viewing:
            return {"error": "No active viewing session"}
        
        progress = self.active_viewing[progress_key]
        episode = await self._get_episode_by_id(content_id)
        
        # Update progress
        progress.progress_percentage = progress_data['percentage']
        progress.total_watch_time_minutes = progress_data['watch_time_minutes']
        
        # Check for checkpoint completion
        xp_earned = 0
        achievements = []
        
        if 'checkpoint_reached' in progress_data:
            checkpoint_index = progress_data['checkpoint_reached']
            checkpoint_id = f"{content_id}_checkpoint_{checkpoint_index}"
            
            if checkpoint_id not in progress.completed_checkpoints:
                progress.completed_checkpoints.append(checkpoint_id)
                
                # Award checkpoint XP
                xp_earned += 25
                await self.xp_economy.add_xp(
                    user_id, 25, 
                    f"Checkpoint {checkpoint_index + 1} completed in {episode.title}"
                )
        
        # Check for quiz completion
        if 'quiz_result' in progress_data:
            quiz_id = progress_data['quiz_result']['quiz_id']
            score = progress_data['quiz_result']['score']
            progress.quiz_scores[quiz_id] = score
            
            # Award quiz XP based on score
            quiz_xp = int(10 * score)
            xp_earned += quiz_xp
            await self.xp_economy.add_xp(
                user_id, quiz_xp,
                f"Quiz score: {int(score * 100)}% in {episode.title}"
            )
        
        # Check for episode completion
        if progress.progress_percentage >= 95 and progress.status != ViewingStatus.COMPLETED:
            progress.status = ViewingStatus.COMPLETED
            
            # Award completion XP
            xp_earned += episode.xp_reward
            await self.xp_economy.add_xp(
                user_id, episode.xp_reward,
                f"Completed episode: {episode.title}"
            )
            
            # Track completion
            await self._track_interaction(user_id, content_id, "completed")
            
            # Check for season completion
            season_complete = await self._check_season_completion(user_id, episode)
            if season_complete:
                achievements.append("season_complete")
                xp_earned += 200
            
            # Update binge session
            await self._update_binge_session(user_id, content_id)
        
        # Save progress
        await self._save_viewing_progress(progress)
        
        return {
            "success": True,
            "xp_earned": xp_earned,
            "achievements": achievements,
            "progress_saved": True
        }
    
    async def create_viewing_party(self, host_user_id: str, 
                                 content_id: str, 
                                 scheduled_time: datetime,
                                 settings: Dict[str, Any]) -> Dict[str, Any]:
        """Create a group viewing party"""
        # Verify host can access content
        episode = await self._get_episode_by_id(content_id)
        user_tier = await self._get_user_tier(host_user_id)
        
        if not episode or not self._can_access_episode(episode, user_tier):
            return {"error": "Cannot access this content"}
        
        party = ViewingParty(
            party_id=f"party_{datetime.utcnow().timestamp()}",
            host_user_id=host_user_id,
            content_id=content_id,
            scheduled_time=scheduled_time,
            max_participants=settings.get('max_participants', 10),
            chat_enabled=settings.get('chat_enabled', True),
            synchronized_playback=settings.get('synchronized_playback', True),
            completion_bonus_xp=settings.get('completion_bonus_xp', 50)
        )
        
        # Save to database
        await self.db.execute("""
            INSERT INTO viewing_parties 
            (party_id, host_user_id, content_id, scheduled_time, 
             max_participants, chat_enabled, synchronized_playback, 
             completion_bonus_xp, participants, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (party.party_id, party.host_user_id, party.content_id,
              party.scheduled_time, party.max_participants, party.chat_enabled,
              party.synchronized_playback, party.completion_bonus_xp,
              json.dumps(party.participants), party.status))
        
        self.viewing_parties[party.party_id] = party
        
        return {
            "success": True,
            "party_id": party.party_id,
            "share_link": f"/join-party/{party.party_id}",
            "scheduled_time": scheduled_time
        }
    
    async def join_viewing_party(self, user_id: str, party_id: str) -> Dict[str, Any]:
        """Join an existing viewing party"""
        party = self.viewing_parties.get(party_id)
        if not party:
            # Load from database
            party_data = await self.db.fetch_one(
                "SELECT * FROM viewing_parties WHERE party_id = ?",
                (party_id,)
            )
            if not party_data:
                return {"error": "Party not found"}
            
            party = ViewingParty(
                party_id=party_data['party_id'],
                host_user_id=party_data['host_user_id'],
                content_id=party_data['content_id'],
                scheduled_time=party_data['scheduled_time'],
                max_participants=party_data['max_participants'],
                participants=json.loads(party_data['participants']),
                chat_enabled=party_data['chat_enabled'],
                synchronized_playback=party_data['synchronized_playback'],
                completion_bonus_xp=party_data['completion_bonus_xp'],
                status=party_data['status']
            )
            self.viewing_parties[party_id] = party
        
        # Check if party is full
        if len(party.participants) >= party.max_participants:
            return {"error": "Party is full"}
        
        # Check if user can access content
        episode = await self._get_episode_by_id(party.content_id)
        user_tier = await self._get_user_tier(user_id)
        
        if not self._can_access_episode(episode, user_tier):
            return {"error": f"Requires {episode.tier_required.value} tier"}
        
        # Add user to party
        if user_id not in party.participants:
            party.participants.append(user_id)
            await self.db.execute(
                "UPDATE viewing_parties SET participants = ? WHERE party_id = ?",
                (json.dumps(party.participants), party_id)
            )
        
        return {
            "success": True,
            "party_details": {
                "content_id": party.content_id,
                "scheduled_time": party.scheduled_time,
                "participant_count": len(party.participants) + 1,
                "host_name": await self._get_user_name(party.host_user_id)
            }
        }
    
    async def download_for_offline(self, user_id: str, content_id: str) -> Dict[str, Any]:
        """Download content for offline viewing"""
        # Check download limits
        user_tier = await self._get_user_tier(user_id)
        current_downloads = len(self.offline_downloads.get(user_id, []))
        limit = self.download_limits.get(user_tier, 5)
        
        if current_downloads >= limit:
            return {
                "error": f"Download limit reached ({limit} for {user_tier.value})"
            }
        
        # Check if content can be downloaded
        episode = await self._get_episode_by_id(content_id)
        if not episode or not self._can_access_episode(episode, user_tier):
            return {"error": "Cannot download this content"}
        
        # Generate download token
        download_token = hashlib.sha256(
            f"{user_id}_{content_id}_{datetime.utcnow()}".encode()
        ).hexdigest()
        
        # Set expiry (7 days for most tiers, 14 for higher)
        if user_tier in [TradingTier.MASTER, TradingTier.GRANDMASTER]:
            expiry_days = 14
        else:
            expiry_days = 7
        
        expiry_date = datetime.utcnow() + timedelta(days=expiry_days)
        
        # Update viewing progress
        progress_key = f"{user_id}_{content_id}"
        if progress_key in self.active_viewing:
            progress = self.active_viewing[progress_key]
        else:
            progress = ViewingProgress(
                user_id=user_id,
                content_id=content_id,
                content_type=ContentType.VIDEO,
                status=ViewingStatus.DOWNLOADED,
                progress_percentage=0.0,
                last_watched_timestamp=datetime.utcnow(),
                total_watch_time_minutes=0
            )
            self.active_viewing[progress_key] = progress
        
        progress.downloaded_for_offline = True
        progress.download_expiry = expiry_date
        await self._save_viewing_progress(progress)
        
        # Track download
        self.offline_downloads[user_id].append(content_id)
        
        return {
            "success": True,
            "download_token": download_token,
            "expiry_date": expiry_date,
            "download_url": f"/download/{download_token}",
            "file_size_mb": episode.duration_minutes * 50  # Rough estimate
        }
    
    async def get_recommendation_engine_data(self, user_id: str) -> Dict[str, Any]:
        """Get data about the recommendation engine for transparency"""
        return {
            "user_preferences": dict(self.user_preferences.get(user_id, {})),
            "top_categories": sorted(
                self.user_preferences.get(user_id, {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "recommendation_explanation": "Based on your viewing history and preferences"
        }
    
    # Helper methods
    
    def _can_access_series(self, series: Series, tier: TradingTier) -> bool:
        """Check if user tier can access series"""
        tier_order = list(TradingTier)
        min_tier_required = TradingTier.GRANDMASTER
        
        for season in series.seasons:
            season_tier_index = tier_order.index(season.tier_required)
            min_tier_index = tier_order.index(min_tier_required)
            if season_tier_index < min_tier_index:
                min_tier_required = season.tier_required
        
        return tier_order.index(tier) >= tier_order.index(min_tier_required)
    
    def _can_access_episode(self, episode: Episode, tier: TradingTier) -> bool:
        """Check if user tier can access episode"""
        tier_order = list(TradingTier)
        return tier_order.index(tier) >= tier_order.index(episode.tier_required)
    
    def _series_contains_content(self, series: Series, content_id: str) -> bool:
        """Check if series contains specific content"""
        for season in series.seasons:
            for episode in season.episodes:
                if episode.episode_id == content_id:
                    return True
        return False
    
    async def _get_episode_by_id(self, episode_id: str) -> Optional[Episode]:
        """Get episode by ID"""
        for series in self.series_library.values():
            for season in series.seasons:
                for episode in season.episodes:
                    if episode.episode_id == episode_id:
                        return episode
        return None
    
    async def _get_user_tier(self, user_id: str) -> TradingTier:
        """Get user's current tier"""
        # This would integrate with the main education system
        result = await self.db.fetch_one(
            "SELECT tier FROM user_education_progress WHERE user_id = ?",
            (user_id,)
        )
        return TradingTier(result['tier']) if result else TradingTier.NIBBLER
    
    async def _has_completed_episode(self, user_id: str, episode_id: str) -> bool:
        """Check if user has completed an episode"""
        progress_key = f"{user_id}_{episode_id}"
        if progress_key in self.active_viewing:
            return self.active_viewing[progress_key].status == ViewingStatus.COMPLETED
        
        # Check database
        result = await self.db.fetch_one(
            """SELECT status FROM viewing_progress 
               WHERE user_id = ? AND content_id = ?""",
            (user_id, episode_id)
        )
        return result and result['status'] == ViewingStatus.COMPLETED.value
    
    async def _has_completed_series(self, user_id: str, series_id: str) -> bool:
        """Check if user has completed all episodes in a series"""
        series = self.series_library.get(series_id)
        if not series:
            return False
        
        for season in series.seasons:
            for episode in season.episodes:
                if not await self._has_completed_episode(user_id, episode.episode_id):
                    return False
        return True
    
    async def _save_viewing_progress(self, progress: ViewingProgress):
        """Save viewing progress to database"""
        try:
            await self.db.execute("""
                INSERT OR REPLACE INTO viewing_progress
                (progress_id, user_id, content_id, content_type, status,
                 progress_percentage, last_watched, total_watch_time,
                 completed_checkpoints, quiz_scores, downloaded_offline,
                 download_expiry, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{progress.user_id}_{progress.content_id}",
                progress.user_id, progress.content_id, progress.content_type.value,
                progress.status.value, progress.progress_percentage,
                progress.last_watched_timestamp, progress.total_watch_time_minutes,
                json.dumps(progress.completed_checkpoints),
                json.dumps(progress.quiz_scores), progress.downloaded_for_offline,
                progress.download_expiry, datetime.utcnow()
            ))
        except Exception as e:
            self.logger.error(f"Failed to save viewing progress: {e}")
    
    async def _track_interaction(self, user_id: str, content_id: str, 
                               interaction_type: str, data: Optional[Dict] = None):
        """Track user interactions with content"""
        try:
            await self.db.execute("""
                INSERT INTO content_interactions
                (interaction_id, user_id, content_id, interaction_type, 
                 interaction_data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f"{user_id}_{content_id}_{datetime.utcnow().timestamp()}",
                user_id, content_id, interaction_type,
                json.dumps(data) if data else None,
                datetime.utcnow()
            ))
        except Exception as e:
            self.logger.error(f"Failed to track interaction: {e}")
    
    async def _check_binge_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Check if user is in an active binge session"""
        # Get latest binge session
        session = await self.db.fetch_one("""
            SELECT * FROM binge_sessions
            WHERE user_id = ? AND end_time IS NULL
            ORDER BY start_time DESC
            LIMIT 1
        """, (user_id,))
        
        if not session:
            # Start new binge session
            session_id = f"binge_{user_id}_{datetime.utcnow().timestamp()}"
            await self.db.execute("""
                INSERT INTO binge_sessions
                (session_id, user_id, start_time, episodes_watched)
                VALUES (?, ?, ?, 1)
            """, (session_id, user_id, datetime.utcnow()))
            
            return {
                "session_active": True,
                "episodes_watched": 1,
                "next_reward_at": 3
            }
        
        # Check if session is still valid (within time window)
        start_time = session['start_time']
        time_elapsed = (datetime.utcnow() - start_time).total_seconds() / 3600
        
        # Find applicable rewards
        episodes_watched = session['episodes_watched'] + 1
        next_reward = None
        
        for reward in self.binge_rewards:
            if (episodes_watched < reward.episodes_watched and 
                time_elapsed <= reward.time_window_hours):
                next_reward = reward
                break
        
        return {
            "session_active": True,
            "episodes_watched": episodes_watched,
            "time_elapsed_hours": round(time_elapsed, 1),
            "next_reward_at": next_reward.episodes_watched if next_reward else None,
            "next_reward_xp": next_reward.xp_bonus if next_reward else None
        }
    
    async def _update_binge_session(self, user_id: str, content_id: str):
        """Update binge watching session"""
        session = await self.db.fetch_one("""
            SELECT * FROM binge_sessions
            WHERE user_id = ? AND end_time IS NULL
            ORDER BY start_time DESC
            LIMIT 1
        """, (user_id,))
        
        if not session:
            return
        
        episodes_watched = session['episodes_watched'] + 1
        total_xp = session['total_xp_earned']
        achievements = json.loads(session['achievements_unlocked'])
        
        # Check for binge rewards
        start_time = session['start_time']
        time_elapsed = (datetime.utcnow() - start_time).total_seconds() / 3600
        
        for reward in self.binge_rewards:
            if (episodes_watched == reward.episodes_watched and 
                time_elapsed <= reward.time_window_hours):
                # Award binge bonus
                await self.xp_economy.add_xp(
                    user_id, reward.xp_bonus,
                    f"Binge reward: {reward.episodes_watched} episodes!"
                )
                total_xp += reward.xp_bonus
                
                if reward.achievement_id:
                    achievements.append(reward.achievement_id)
                    await self.reward_system.unlock_achievement(
                        user_id, reward.achievement_id
                    )
                
                if reward.special_unlock:
                    # Unlock special content
                    await self._unlock_special_content(user_id, reward.special_unlock)
        
        # Update session
        await self.db.execute("""
            UPDATE binge_sessions
            SET episodes_watched = ?, total_xp_earned = ?, 
                achievements_unlocked = ?
            WHERE session_id = ?
        """, (episodes_watched, total_xp, json.dumps(achievements), 
              session['session_id']))
    
    async def _check_season_completion(self, user_id: str, 
                                     completed_episode: Episode) -> bool:
        """Check if user completed a full season"""
        # Find the season containing this episode
        for series in self.series_library.values():
            for season in series.seasons:
                if completed_episode in season.episodes:
                    # Check if all episodes in season are complete
                    for episode in season.episodes:
                        if not await self._has_completed_episode(user_id, 
                                                                episode.episode_id):
                            return False
                    
                    # Award season completion bonus
                    await self.xp_economy.add_xp(
                        user_id, season.completion_bonus_xp,
                        f"Season complete: {season.title}"
                    )
                    return True
        
        return False
    
    async def _unlock_special_content(self, user_id: str, unlock_id: str):
        """Unlock special content for user"""
        # This would unlock bonus content, early access, etc.
        self.logger.info(f"Special content unlocked for {user_id}: {unlock_id}")
    
    async def _get_user_name(self, user_id: str) -> str:
        """Get user's display name"""
        # This would fetch from user profile
        return f"Trader_{user_id[:8]}"