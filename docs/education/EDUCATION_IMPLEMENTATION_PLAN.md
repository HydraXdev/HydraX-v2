# 🎯 BITTEN EDUCATION SYSTEM - COMPLETE IMPLEMENTATION PLAN

## 🚨 CRITICAL: THIS IS THE HEART OF BITTEN
The education system transforms BITTEN from a trading bot into a **Trading Academy**. Every feature must reinforce learning and discipline while maintaining the engaging military theme.

---

## 📊 SYSTEM ARCHITECTURE

### Core Components
```
education_system.py (EXISTS - ENHANCE)
    ├── education_missions.py (NEW)
    ├── education_content.py (NEW)
    ├── education_achievements.py (NEW)
    ├── education_social.py (NEW)
    └── education_analytics.py (NEW)
```

### Integration Points
```
fire_router.py ←→ education_system.py (pre-trade checks)
xp_calculator.py ←→ education_achievements.py (XP rewards)
telegram_router.py ←→ education_missions.py (commands)
webapp_router.py ←→ education HUD (dashboard)
```

---

## 📝 DETAILED IMPLEMENTATION TASKS

### Task 1: Enhance education_system.py
**Priority**: HIGH
**Dependencies**: None
**Time Estimate**: 4 hours

```python
# Add to existing education_system.py

class EducationBotPersonalities:
    """Bot personalities for educational interactions"""
    
    def __init__(self):
        self.personalities = {
            'drill': DrillSergeantEducator(),
            'medic': FieldMedicEducator(),
            'intel': IntelOfficerEducator(),
            'bit': BitCompanionEducator()
        }
    
    async def get_response(self, bot_type: str, scenario: str, context: dict) -> str:
        """Get personality-appropriate response"""
        return await self.personalities[bot_type].respond(scenario, context)

class DrillSergeantEducator:
    """Harsh but fair discipline enforcer"""
    
    responses = {
        'cooldown_start': [
            "STAND DOWN, MAGGOT! 30 minutes to think about that disaster!",
            "NEGATIVE! Cool your jets and study why that trade failed!",
            "DENIED! Hit the education center before you hit the market again!"
        ],
        'big_loss': [
            "WHAT WAS THAT?! Your stop loss was wider than the Grand Canyon!",
            "PATHETIC! But we'll make a trader out of you yet. STUDY UP!",
            "That's what happens when you ignore the rules! LEARN FROM IT!"
        ],
        'good_trade': [
            "Finally following orders! That's how it's done, recruit!",
            "Not bad! But don't let it go to your head. Stay disciplined!",
            "THAT'S the discipline I want to see! Keep it up!"
        ]
    }

class TierBasedEducation:
    """Education requirements by tier"""
    
    TIER_CURRICULUM = {
        'NIBBLER': {
            'required_videos': ['risk_basics', 'stop_loss_101', 'psychology_intro'],
            'required_quizzes': ['risk_management_quiz', 'basic_analysis_quiz'],
            'paper_trades_required': 20,
            'min_quiz_score': 70,
            'cooldown_minutes': 30
        },
        'FANG': {
            'required_videos': ['advanced_patterns', 'multi_timeframe', 'volume_analysis'],
            'required_quizzes': ['pattern_recognition_quiz', 'advanced_risk_quiz'],
            'paper_trades_required': 10,
            'min_quiz_score': 80,
            'cooldown_minutes': 15
        }
    }
```

### Task 2: Create education_missions.py
**Priority**: HIGH
**Dependencies**: Task 1
**Time Estimate**: 3 hours

```python
# src/bitten_core/education_missions.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

class MissionType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    SPECIAL = "special"

@dataclass
class Mission:
    id: str
    type: MissionType
    title: str
    description: str
    objectives: List[Dict[str, any]]
    xp_reward: int
    tier_requirement: Optional[str] = None
    time_limit: Optional[timedelta] = None
    prerequisite_missions: List[str] = None

class MissionSystem:
    """Daily and weekly educational missions"""
    
    DAILY_MISSIONS = {
        'chart_recon': Mission(
            id='EDU_D001',
            type=MissionType.DAILY,
            title='Chart Reconnaissance',
            description='Analyze 3 charts and identify support/resistance',
            objectives=[
                {'action': 'analyze_chart', 'count': 3},
                {'action': 'identify_levels', 'count': 6}
            ],
            xp_reward=50,
            time_limit=timedelta(hours=24)
        ),
        'risk_drill': Mission(
            id='EDU_D002',
            type=MissionType.DAILY,
            title='Risk Management Drill',
            description='Calculate position sizes for 5 trade scenarios',
            objectives=[
                {'action': 'calculate_position', 'count': 5},
                {'action': 'verify_risk_percent', 'max': 1.0}
            ],
            xp_reward=75,
            tier_requirement='NIBBLER'
        )
    }
    
    WEEKLY_CAMPAIGNS = {
        'risk_bootcamp': Mission(
            id='EDU_W001',
            type=MissionType.WEEKLY,
            title='Risk Management Bootcamp',
            description='Complete all risk management training',
            objectives=[
                {'action': 'complete_daily_mission', 'mission_id': 'EDU_D002', 'count': 5},
                {'action': 'watch_video', 'video_id': 'risk_advanced', 'count': 1},
                {'action': 'pass_quiz', 'quiz_id': 'risk_certification', 'min_score': 85}
            ],
            xp_reward=500,
            time_limit=timedelta(days=7)
        )
    }
```

### Task 3: Create education_content.py
**Priority**: HIGH
**Dependencies**: None
**Time Estimate**: 3 hours

```python
# src/bitten_core/education_content.py

@dataclass
class VideoContent:
    id: str
    title: str
    description: str
    url: str
    duration_minutes: int
    tier_requirement: str
    xp_reward: int
    quiz_id: Optional[str] = None
    tags: List[str] = None

@dataclass
class Quiz:
    id: str
    title: str
    questions: List[QuizQuestion]
    passing_score: int
    xp_reward: int
    certificate_id: Optional[str] = None

class ContentLibrary:
    """Manages all educational content"""
    
    VIDEO_LIBRARY = {
        'NIBBLER': [
            VideoContent(
                id='NIB_V001',
                title='Stop Loss Bootcamp',
                description='Master the art of capital preservation',
                url='https://embed.video/stop_loss_basics',
                duration_minutes=15,
                tier_requirement='NIBBLER',
                xp_reward=100,
                quiz_id='NIB_Q001',
                tags=['risk', 'basics', 'essential']
            ),
            VideoContent(
                id='NIB_V002',
                title='Psychology 101: FOMO and Revenge Trading',
                description='Understand and overcome emotional trading',
                url='https://embed.video/trading_psychology',
                duration_minutes=20,
                tier_requirement='NIBBLER',
                xp_reward=125,
                tags=['psychology', 'emotions', 'discipline']
            )
        ],
        'FANG': [
            VideoContent(
                id='FNG_V001',
                title='Multi-Timeframe Warfare',
                description='Coordinate attacks across multiple timeframes',
                url='https://embed.video/mtf_analysis',
                duration_minutes=30,
                tier_requirement='FANG',
                xp_reward=200,
                quiz_id='FNG_Q001',
                tags=['advanced', 'analysis', 'strategy']
            )
        ]
    }
    
    QUIZ_BANK = {
        'NIB_Q001': Quiz(
            id='NIB_Q001',
            title='Stop Loss Certification',
            questions=[
                QuizQuestion(
                    question='What percentage of your account should you risk per trade?',
                    options=['5%', '2%', '1%', '10%'],
                    correct_index=2,
                    explanation='The 1% rule ensures you can survive 100 losing trades'
                ),
                QuizQuestion(
                    question='Where should you place your stop loss?',
                    options=[
                        'At a random distance',
                        'Below support for longs, above resistance for shorts',
                        'Always 50 pips away',
                        'You don\'t need stops'
                    ],
                    correct_index=1,
                    explanation='Stops should be placed at logical levels where your trade idea is invalidated'
                )
            ],
            passing_score=80,
            xp_reward=150
        )
    }
```

### Task 4: Create education_achievements.py
**Priority**: MEDIUM
**Dependencies**: Tasks 1-3
**Time Estimate**: 2 hours

```python
# src/bitten_core/education_achievements.py

@dataclass
class Achievement:
    id: str
    name: str
    description: str
    icon: str
    xp_reward: int
    tier_requirement: Optional[str] = None
    hidden: bool = False
    
@dataclass
class Certification:
    id: str
    name: str
    requirements: List[str]
    benefits: List[str]
    badge_icon: str
    
class AchievementSystem:
    """Track educational achievements and certifications"""
    
    ACHIEVEMENTS = {
        # Learning Achievements
        'first_lesson': Achievement(
            id='EDU_ACH_001',
            name='Boot Camp Graduate',
            description='Complete your first educational video',
            icon='🎓',
            xp_reward=50
        ),
        'risk_master': Achievement(
            id='EDU_ACH_002',
            name='Risk Management Specialist',
            description='Pass all risk management quizzes with 90%+',
            icon='🛡️',
            xp_reward=500,
            tier_requirement='FANG'
        ),
        'paper_champion': Achievement(
            id='EDU_ACH_003',
            name='Simulation Champion',
            description='Achieve 60% win rate in 50 paper trades',
            icon='📊',
            xp_reward=750
        ),
        'study_streak': Achievement(
            id='EDU_ACH_004',
            name='Dedicated Student',
            description='Complete daily missions for 30 days straight',
            icon='🔥',
            xp_reward=1000
        ),
        'mentor': Achievement(
            id='EDU_ACH_005',
            name='Squad Leader',
            description='Help 10 traders in study groups',
            icon='⭐',
            xp_reward=750,
            tier_requirement='COMMANDER'
        )
    }
    
    CERTIFICATIONS = {
        'nibbler_graduate': Certification(
            id='CERT_001',
            name='Nibbler Academy Graduate',
            requirements=[
                'Complete all Nibbler required videos',
                'Pass all Nibbler quizzes with 80%+',
                'Complete 30 paper trades',
                'Maintain 40%+ win rate'
            ],
            benefits=[
                'Unlock Fang tier',
                'Reduced cooldowns (30min → 15min)',
                'Access to advanced content',
                'Nibbler Graduate badge'
            ],
            badge_icon='🎖️'
        )
    }
```

### Task 5: Create education_social.py
**Priority**: MEDIUM
**Dependencies**: Tasks 1-4
**Time Estimate**: 3 hours

```python
# src/bitten_core/education_social.py

@dataclass
class StudyGroup:
    id: str
    name: str
    topic: str
    leader_id: str
    members: List[str]
    max_members: int = 10
    created_at: datetime = field(default_factory=datetime.utcnow)
    
@dataclass
class MentorMatch:
    mentor_id: str
    student_id: str
    started_at: datetime
    topics: List[str]
    sessions_completed: int = 0
    
class SocialLearning:
    """Group learning and mentorship features"""
    
    async def create_study_group(self, leader_id: str, name: str, topic: str) -> StudyGroup:
        """Create a new study group"""
        group = StudyGroup(
            id=f"SG_{datetime.utcnow().timestamp()}",
            name=name,
            topic=topic,
            leader_id=leader_id,
            members=[leader_id]
        )
        await self.save_group(group)
        return group
        
    async def match_mentor(self, student_id: str, preferred_topics: List[str]) -> Optional[MentorMatch]:
        """Match student with appropriate mentor"""
        # Find mentors (COMMANDER+ with good track record)
        available_mentors = await self.find_available_mentors(preferred_topics)
        
        if not available_mentors:
            return None
            
        # Score and match based on compatibility
        best_mentor = self.score_mentor_match(student_id, available_mentors)
        
        match = MentorMatch(
            mentor_id=best_mentor['user_id'],
            student_id=student_id,
            started_at=datetime.utcnow(),
            topics=preferred_topics
        )
        
        await self.save_match(match)
        await self.notify_mentor_match(match)
        return match
```

### Task 6: Create Education HUD Components
**Priority**: HIGH
**Dependencies**: Tasks 1-5
**Time Estimate**: 4 hours

```html
<!-- src/ui/education_hud/index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>BITTEN Tactical Academy</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="education-hud">
        <!-- Header -->
        <header class="academy-header">
            <div class="logo">
                <img src="/assets/bitten_academy.png" alt="BITTEN Academy">
            </div>
            <div class="user-tier">
                <span class="tier-badge" data-tier="{{user_tier}}">{{user_tier}}</span>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{tier_progress}}%"></div>
                </div>
            </div>
        </header>
        
        <!-- Main Dashboard -->
        <div class="dashboard-grid">
            <!-- Daily Missions -->
            <section class="mission-panel">
                <h2>📋 DAILY BRIEFING</h2>
                <div class="mission-list">
                    <!-- Dynamically populated -->
                </div>
            </section>
            
            <!-- Video Library -->
            <section class="video-panel">
                <h2>🎥 TACTICAL LIBRARY</h2>
                <div class="video-grid">
                    <!-- Tier-appropriate videos -->
                </div>
            </section>
            
            <!-- Progress Tracker -->
            <section class="progress-panel">
                <h2>📊 COMBAT READINESS</h2>
                <div class="stats-container">
                    <div class="stat-card">
                        <h3>Videos Watched</h3>
                        <div class="stat-value">{{videos_completed}}/{{total_videos}}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Quiz Average</h3>
                        <div class="stat-value">{{quiz_average}}%</div>
                    </div>
                    <div class="stat-card">
                        <h3>Paper Trade W/R</h3>
                        <div class="stat-value">{{paper_win_rate}}%</div>
                    </div>
                </div>
            </section>
            
            <!-- Achievements -->
            <section class="achievement-panel">
                <h2>🏆 MEDALS & HONORS</h2>
                <div class="achievement-grid">
                    <!-- Earned achievements -->
                </div>
            </section>
        </div>
        
        <!-- Study Groups -->
        <section class="social-panel">
            <h2>👥 SQUAD TRAINING</h2>
            <div class="group-list">
                <!-- Active study groups -->
            </div>
            <button class="cta-button" onclick="createStudyGroup()">
                Create Study Group
            </button>
        </section>
    </div>
    
    <script src="education_logic.js"></script>
</body>
</html>
```

```css
/* src/ui/education_hud/styles.css */

.education-hud {
    background: var(--military-black);
    color: var(--military-green);
    font-family: 'Military', monospace;
    min-height: 100vh;
}

.academy-header {
    display: flex;
    justify-content: space-between;
    padding: 20px;
    border-bottom: 2px solid var(--military-green);
}

.tier-badge {
    display: inline-block;
    padding: 10px 20px;
    background: var(--tier-color);
    color: black;
    font-weight: bold;
    text-transform: uppercase;
}

.tier-badge[data-tier="NIBBLER"] { background: #4CAF50; }
.tier-badge[data-tier="FANG"] { background: #FF9800; }
.tier-badge[data-tier="COMMANDER"] { background: #F44336; }
.tier-badge[data-tier=] { background: #9C27B0; }

.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    padding: 20px;
}

.mission-panel, .video-panel, .progress-panel, .achievement-panel {
    background: rgba(0, 255, 0, 0.05);
    border: 1px solid var(--military-green);
    padding: 20px;
    position: relative;
}

.mission-panel::before {
    content: "⚠️ CLASSIFIED";
    position: absolute;
    top: 5px;
    right: 10px;
    font-size: 10px;
    opacity: 0.5;
}

.mission-list .mission-card {
    background: rgba(0, 0, 0, 0.3);
    border-left: 4px solid var(--military-green);
    padding: 15px;
    margin: 10px 0;
    cursor: pointer;
    transition: all 0.3s;
}

.mission-card:hover {
    transform: translateX(5px);
    box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
}

.mission-card.completed {
    opacity: 0.5;
    border-color: #4CAF50;
}

.video-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 15px;
}

.video-card {
    background: #111;
    border: 1px solid #333;
    padding: 10px;
    text-align: center;
    cursor: pointer;
}

.video-card.locked {
    opacity: 0.3;
    cursor: not-allowed;
}

.video-card.locked::after {
    content: "🔒 CLASSIFIED";
    display: block;
    color: red;
    margin-top: 10px;
}

.achievement-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.achievement-badge {
    width: 60px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    background: rgba(255, 255, 255, 0.1);
    border: 2px solid transparent;
    border-radius: 50%;
    position: relative;
}

.achievement-badge.earned {
    border-color: gold;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(255, 215, 0, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(255, 215, 0, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 215, 0, 0); }
}

/* Combat Terminal Effect */
.education-hud::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0, 255, 0, 0.03) 2px,
        rgba(0, 255, 0, 0.03) 4px
    );
    pointer-events: none;
    z-index: 1;
}
```

### Task 7: Integration Updates
**Priority**: HIGH
**Dependencies**: Tasks 1-6
**Time Estimate**: 3 hours

```python
# Updates to fire_router.py

async def execute_fire(self, request: TradeRequest) -> TradeResult:
    """Execute trade with education checks"""
    
    # Education pre-trade check
    education_check = await self.education.pre_trade_check(
        request.user_id,
        {
            'symbol': request.symbol,
            'entry_price': request.entry_price,
            'position_size': request.position_size,
            'stop_loss': request.stop_loss,
            'account_balance': await self.get_account_balance(request.user_id)
        }
    )
    
    if not education_check['approved']:
        # Return educational response instead of executing
        return TradeResult(
            success=False,
            message=education_check['warnings'][0],
            educational_content=education_check['educational_tips'],
            suggest_paper_trade=education_check['paper_trade_suggestion']
        )
    
    # Continue with normal execution...
```

```python
# Updates to xp_calculator.py

EDUCATION_XP_TABLE = {
    'video_watched': 50,
    'quiz_passed': 100,
    'quiz_perfect': 150,
    'mission_daily': 75,
    'mission_weekly': 500,
    'paper_trade_win': 25,
    'paper_trade_analyzed': 50,
    'study_group_created': 200,
    'study_group_joined': 100,
    'mentor_session': 150,
    'achievement_earned': 'variable'  # Based on achievement
}

async def calculate_education_xp(self, activity: str, details: Dict[str, Any]) -> int:
    """Calculate XP for educational activities"""
    base_xp = EDUCATION_XP_TABLE.get(activity, 0)
    
    # Apply multipliers
    multipliers = 1.0
    
    # Quiz perfect score bonus
    if activity == 'quiz_passed' and details.get('score', 0) == 100:
        multipliers *= 1.5
        
    # Streak bonuses
    if details.get('daily_streak', 0) > 7:
        multipliers *= 1.2
        
    # Tier bonuses (higher tiers get more XP to compensate for difficulty)
    tier_multipliers = {
        'NIBBLER': 1.0,
        'FANG': 1.2,
        'COMMANDER': 1.5,
        '': 2.0
    }
    multipliers *= tier_multipliers.get(details.get('user_tier', 'NIBBLER'), 1.0)
    
    return int(base_xp * multipliers)
```

```python
# Updates to telegram_router.py

@bot.command('learn')
async def education_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Access education features"""
    keyboard = [
        ['📚 Today\'s Missions', '🎥 Video Library'],
        ['📊 My Progress', '👥 Study Groups'],
        ['🏆 Achievements', '📝 Trade Journal'],
        ['📈 Paper Trading', '🔙 Back']
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    progress = await education_system.get_education_dashboard(update.effective_user.id)
    
    message = f"""🎓 **BITTEN TACTICAL ACADEMY**
    
**Rank**: {progress['current_tier']}
**Progress**: {progress['tier_progress']}% to next tier
**Win Rate**: {progress['win_rate']}%
**Active Cooldown**: {'YES ⏰' if progress['cooldown_active'] else 'NO ✅'}

Select your training module below."""
    
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
```

### Task 8: Database Migrations
**Priority**: HIGH
**Dependencies**: None
**Time Estimate**: 1 hour

```sql
-- migrations/add_education_tables.sql

-- Enhanced education progress
ALTER TABLE user_education_progress ADD COLUMN 
    daily_streak INTEGER DEFAULT 0,
    total_xp_earned INTEGER DEFAULT 0,
    certifications TEXT DEFAULT '[]',
    mentor_id TEXT,
    study_groups TEXT DEFAULT '[]';

-- Mission progress tracking
CREATE TABLE IF NOT EXISTS mission_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    mission_id TEXT NOT NULL,
    progress TEXT NOT NULL, -- JSON
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    xp_awarded INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Video watch history
CREATE TABLE IF NOT EXISTS video_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    watch_percentage REAL DEFAULT 0,
    last_position INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    quiz_score REAL,
    watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Study groups
CREATE TABLE IF NOT EXISTS study_groups (
    group_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    topic TEXT NOT NULL,
    leader_id TEXT NOT NULL,
    members TEXT NOT NULL, -- JSON array
    max_members INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (leader_id) REFERENCES users(user_id)
);

-- Mentorship matches
CREATE TABLE IF NOT EXISTS mentor_matches (
    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    topics TEXT NOT NULL, -- JSON array
    sessions_completed INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    FOREIGN KEY (mentor_id) REFERENCES users(user_id),
    FOREIGN KEY (student_id) REFERENCES users(user_id)
);

-- Achievement tracking
CREATE TABLE IF NOT EXISTS user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    achievement_id TEXT NOT NULL,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    xp_awarded INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, achievement_id)
);

-- Create indexes for performance
CREATE INDEX idx_mission_user ON mission_progress(user_id);
CREATE INDEX idx_video_user ON video_progress(user_id);
CREATE INDEX idx_achievement_user ON user_achievements(user_id);
CREATE INDEX idx_study_group_leader ON study_groups(leader_id);
```

---

## 🔧 CONFIGURATION REQUIREMENTS

### Environment Variables
```bash
# Education System Config
EDUCATION_VIDEO_CDN="https://cdn.bitten.academy"
EDUCATION_QUIZ_API_KEY="your-quiz-api-key"
EDUCATION_CONTENT_ENCRYPTION_KEY="your-encryption-key"

# Feature Flags
EDUCATION_PAPER_TRADING_ENABLED=true
EDUCATION_SOCIAL_FEATURES_ENABLED=true
EDUCATION_VIDEO_STREAMING_ENABLED=true
```

### Settings Configuration
```python
# config/education.py
EDUCATION_SETTINGS = {
    'cooldowns': {
        'nibbler_minutes': 30,
        'fang_minutes': 15,
        'commander_minutes': 5,
        'apex_minutes': 0
    },
    'xp_rewards': {
        'video_base': 50,
        'quiz_base': 100,
        'mission_base': 75,
        'achievement_base': 'variable'
    },
    'paper_trading': {
        'starting_balance': 10000,
        'max_position_size': 0.1,  # 10% of balance
        'allowed_instruments': ['EUR/USD', 'GBP/USD', 'USD/JPY']
    },
    'content_delivery': {
        'video_format': 'HLS',
        'max_concurrent_streams': 3,
        'quality_options': ['480p', '720p', '1080p']
    }
}
```

---

## 🧪 TESTING REQUIREMENTS

### Unit Tests
```python
# tests/test_education_system.py
- Test cooldown enforcement
- Test bot personality responses
- Test tier progression logic
- Test XP calculations
- Test mission completion

# tests/test_education_content.py
- Test video access control
- Test quiz scoring
- Test content recommendations

# tests/test_education_social.py
- Test study group creation
- Test mentor matching algorithm
- Test group size limits
```

### Integration Tests
```python
# tests/test_education_integration.py
- Test fire_router education checks
- Test XP system integration
- Test Telegram command flow
- Test database migrations
- Test WebApp data flow
```

### E2E Tests
```python
# tests/test_education_e2e.py
- Complete new user education flow
- Paper trading to real trading transition
- Mission completion and rewards
- Video watch and quiz flow
- Study group interaction
```

---

## 📈 SUCCESS METRICS

### User Engagement
- Daily active learners
- Video completion rates
- Quiz pass rates
- Mission completion rates
- Study group participation

### Learning Effectiveness
- Win rate improvement over time
- Reduction in basic mistakes
- Risk management compliance
- Average trade quality scores

### System Performance
- Video streaming reliability
- Quiz system uptime
- Database query performance
- XP calculation accuracy

---

## 🚨 CRITICAL REMINDERS

1. **Safety First**: Cooldowns are MANDATORY for Nibblers
2. **Consistency**: Bot personalities must maintain voice across all systems
3. **Balance**: XP rewards must not break existing economy
4. **Performance**: Video streaming must not impact trading performance
5. **Security**: Quiz answers must be encrypted, not client-side
6. **Accessibility**: Content must work on mobile devices
7. **Scalability**: System must handle 10,000+ concurrent users

---

## 🎯 FINAL CHECKLIST

Before marking education system as complete:

- [ ] All bot personalities respond appropriately
- [ ] Cooldown system enforces learning periods
- [ ] Mission system generates daily/weekly content
- [ ] Video library serves tier-appropriate content
- [ ] Quiz system accurately scores and rewards
- [ ] Achievement system tracks all activities
- [ ] Study groups allow collaboration
- [ ] Paper trading simulates real conditions
- [ ] All systems integrate with existing code
- [ ] Database migrations run cleanly
- [ ] Tests achieve 90%+ coverage
- [ ] Documentation is complete
- [ ] Performance benchmarks met
- [ ] Security audit passed
- [ ] Mobile experience verified

---

This education system transforms BITTEN into a comprehensive trading academy that makes learning addictive, not painful. Every feature reinforces the core mission: helping the 90% who fail become disciplined, profitable traders.

"The market bites. We bite back. But first, we learn HOW to bite."