# AI Gamification Engine

## Overview

The AI Gamification Engine is a sophisticated system that automatically generates personalized challenges, achievements, and content for the HydraX trading platform. It leverages OpenAI and Claude APIs to create dynamic, engaging content tailored to individual user profiles and behaviors.

## Features

### 🎯 Core Capabilities

1. **Dynamic Content Generation**
   - Personalized daily challenges
   - Custom achievements
   - Adaptive mission briefings
   - Motivational messages
   - Tutorial content
   - Social engagement prompts

2. **AI Provider Support**
   - OpenAI GPT-4 integration
   - Claude 3 Opus integration
   - Ensemble approach for optimal results
   - Automatic fallback mechanisms

3. **Personalization Engine**
   - User behavior profiling
   - Persona-based content matching
   - Skill level adaptation
   - Risk tolerance consideration
   - Engagement pattern analysis

4. **Performance Tracking**
   - Content effectiveness metrics
   - Completion rate tracking
   - User satisfaction monitoring
   - A/B testing capabilities

## Installation

### Prerequisites

```bash
# Required Python packages
pip install httpx asyncio sqlite3 pathlib

# Environment variables
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-claude-key"
```

### Quick Start

```python
from ai_gamification_engine import AIGamificationEngine

# Initialize the engine
engine = AIGamificationEngine()

# Generate content for a user
challenges = await engine.generate_daily_challenges(user_id="user123")
```

## Architecture

### System Components

```
┌─────────────────────────────────────────────┐
│            AI Gamification Engine           │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────┐       ┌─────────────┐    │
│  │   OpenAI    │       │   Claude    │    │
│  │ Generator   │       │ Generator   │    │
│  └──────┬──────┘       └──────┬──────┘    │
│         │                      │            │
│         └──────────┬───────────┘           │
│                    │                        │
│         ┌──────────▼──────────┐            │
│         │ Content Orchestrator│            │
│         └──────────┬──────────┘            │
│                    │                        │
│    ┌───────────────┴────────────────┐      │
│    │                                 │      │
│    ▼                                 ▼      │
│ ┌──────────┐                ┌──────────┐   │
│ │ Profile  │                │ Content  │   │
│ │ Manager  │                │ Storage  │   │
│ └──────────┘                └──────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

### Database Schema

```sql
-- Generated content storage
CREATE TABLE generated_content (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    content_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT NOT NULL,
    rewards TEXT NOT NULL,
    difficulty_level INTEGER,
    personalization_score REAL,
    ai_provider TEXT,
    generated_at TIMESTAMP,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    user_feedback INTEGER,
    metadata TEXT
);

-- User behavior profiles
CREATE TABLE user_behavior_profiles (
    user_id TEXT PRIMARY KEY,
    persona_type TEXT NOT NULL,
    profile_data TEXT NOT NULL,
    last_updated TIMESTAMP,
    generation_count INTEGER DEFAULT 0
);

-- Content performance metrics
CREATE TABLE content_performance (
    content_id INTEGER,
    engagement_score REAL,
    completion_rate REAL,
    avg_time_to_complete INTEGER,
    user_satisfaction REAL,
    FOREIGN KEY (content_id) REFERENCES generated_content(id)
);
```

## Usage Examples

### 1. Generate Daily Challenges

```python
async def create_daily_challenges(user_id: str):
    engine = AIGamificationEngine()
    
    # Generate 3 personalized daily challenges
    challenges = await engine.generate_daily_challenges(
        user_id=user_id,
        count=3
    )
    
    for challenge in challenges:
        print(f"Challenge: {challenge.title}")
        print(f"Description: {challenge.description}")
        print(f"Difficulty: {challenge.difficulty_level}/10")
        print(f"Rewards: {challenge.rewards}")
```

### 2. Create Custom Achievement

```python
async def create_achievement(user_id: str):
    engine = AIGamificationEngine()
    
    # Generate a gold-tier combat achievement
    achievement = await engine.generate_achievement(
        user_id=user_id,
        category=AchievementCategory.COMBAT,
        tier=AchievementTier.GOLD
    )
    
    print(f"Achievement Unlocked: {achievement.title}")
    print(f"Requirements: {achievement.requirements}")
```

### 3. Generate Adaptive Mission

```python
async def create_adaptive_mission(user_id: str):
    engine = AIGamificationEngine()
    
    # Generate mission based on recent performance
    mission = await engine.generate_adaptive_mission(
        user_id=user_id,
        mission_type="weekly"
    )
    
    print(f"Mission Brief: {mission.title}")
    print(f"Objectives: {mission.requirements}")
```

### 4. Use Specific AI Provider

```python
# Force OpenAI generation
content = await engine.generate_personalized_content(
    user_id="user123",
    content_type=ContentGenerationType.CHALLENGE,
    preferred_provider=AIProvider.OPENAI
)

# Force Claude generation
content = await engine.generate_personalized_content(
    user_id="user123",
    content_type=ContentGenerationType.ACHIEVEMENT,
    preferred_provider=AIProvider.CLAUDE
)

# Use ensemble approach (both providers)
content = await engine.generate_personalized_content(
    user_id="user123",
    content_type=ContentGenerationType.MISSION_BRIEF,
    preferred_provider=AIProvider.BOTH
)
```

## Content Types

### 1. Challenges
Dynamic tasks that adapt to user skill level and trading style.

```python
ContentGenerationType.CHALLENGE
```

**Example Output:**
```json
{
    "title": "Sniper's Precision",
    "description": "Execute 5 trades with 90% accuracy using technical analysis",
    "requirements": {
        "trades": 5,
        "accuracy": 0.9,
        "analysis_type": "technical"
    },
    "rewards": {
        "xp": 300,
        "badge": "precision_sniper"
    },
    "difficulty_level": 7,
    "estimated_completion_time": 45
}
```

### 2. Achievements
Milestone-based accomplishments with tiered rewards.

```python
ContentGenerationType.ACHIEVEMENT
```

**Example Output:**
```json
{
    "title": "Market Dominator",
    "description": "Achieve 20% portfolio growth in a single month",
    "requirements": {
        "growth_percentage": 20,
        "timeframe_days": 30
    },
    "rewards": {
        "xp": 1000,
        "title": "Market Dominator",
        "unlock": "elite_strategies"
    },
    "difficulty_level": 9
}
```

### 3. Mission Briefs
Story-driven objectives that integrate with the BITTEN universe.

```python
ContentGenerationType.MISSION_BRIEF
```

**Example Output:**
```json
{
    "title": "Operation Market Storm",
    "description": "Intel suggests major volatility incoming. Prepare defensive positions.",
    "requirements": {
        "set_stop_losses": true,
        "reduce_position_size": 0.5,
        "monitor_news": true
    },
    "rewards": {
        "xp": 500,
        "intel_points": 50
    },
    "narrative_element": "Whispers from the underground suggest institutional moves..."
}
```

## User Behavior Profiling

The engine creates comprehensive user profiles based on:

### Trading Personas
- **BRUTE**: Aggressive, high-risk, action-oriented
- **SCHOLAR**: Analytical, patient, data-driven
- **PHANTOM**: Cautious, stealthy, risk-averse
- **WARDEN**: Disciplined, protective, rule-following
- **FERAL**: Unpredictable, wild, instinct-driven

### Profile Components
```python
@dataclass
class UserBehaviorProfile:
    user_id: str
    persona_type: PersonaType
    trading_style: Dict[str, Any]
    activity_patterns: Dict[str, Any]
    achievement_history: List[str]
    challenge_completion_rate: float
    preferred_content_types: List[ContentGenerationType]
    skill_level: str  # beginner, intermediate, advanced
    engagement_metrics: Dict[str, float]
    social_interactions: Dict[str, Any]
    risk_tolerance: float  # 0.0 to 1.0
    learning_preferences: Dict[str, Any]
```

## AI Prompt Engineering

### OpenAI Prompts
The engine uses structured prompts optimized for GPT-4:

```python
# System prompt for consistency
"You are an AI game designer for BITTEN, a military-themed trading gamification platform..."

# User-specific context
"User Profile:
- Persona: BRUTE (Risk tolerance: 0.85)
- Skill Level: advanced
- Challenge Completion Rate: 78%
- Preferred Activities: high-risk trades, speed challenges"
```

### Claude Prompts
Optimized for Claude's analytical capabilities:

```python
# Behavioral psychology focus
"You are a master game designer and behavioral psychologist creating content for BITTEN..."

# Detailed requirements
"Generate content that:
1. Perfectly matches their persona's psychology
2. Challenges them at their skill level
3. Creates emotional investment"
```

## Performance Metrics

### Track Content Effectiveness

```python
metrics = await engine.get_content_performance_metrics()

# Overall metrics
print(f"Total Generated: {metrics['overall']['total_generated']}")
print(f"Completion Rate: {metrics['overall']['total_completed'] / metrics['overall']['total_generated']:.2%}")
print(f"Avg Personalization: {metrics['overall']['avg_personalization']:.2%}")
print(f"User Satisfaction: {metrics['overall']['avg_satisfaction']:.1f}/5")

# By content type
for content_type, data in metrics['by_content_type'].items():
    print(f"\n{content_type}:")
    print(f"  Generated: {data['count']}")
    print(f"  Completion Rate: {data['completion_rate']:.2%}")
    print(f"  Avg Feedback: {data['avg_feedback']:.1f}/5")

# By AI provider
for provider, data in metrics['by_ai_provider'].items():
    print(f"\n{provider}:")
    print(f"  Generated: {data['count']}")
    print(f"  Personalization: {data['avg_personalization']:.2%}")
    print(f"  Completion Rate: {data['completion_rate']:.2%}")
```

## Integration with HydraX

### 1. Connect to Existing Systems

```python
# Integration with achievement system
from src.bitten_core.achievement_system import AchievementSystem

async def award_ai_achievement(user_id: str, achievement_data: GeneratedContent):
    achievement_system = AchievementSystem()
    
    # Convert AI-generated achievement to system achievement
    achievement_id = await achievement_system.create_custom_achievement(
        name=achievement_data.title,
        description=achievement_data.description,
        requirements=achievement_data.requirements,
        rewards=achievement_data.rewards,
        tier=AchievementTier.GOLD
    )
    
    # Track progress
    await achievement_system.update_progress(user_id, achievement_id)
```

### 2. Webhook Integration

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
engine = AIGamificationEngine()

@app.route('/api/gamification/generate', methods=['POST'])
async def generate_content():
    data = request.json
    user_id = data.get('user_id')
    content_type = ContentGenerationType[data.get('content_type', 'CHALLENGE')]
    
    content = await engine.generate_personalized_content(
        user_id=user_id,
        content_type=content_type,
        context=data.get('context', {})
    )
    
    return jsonify({
        'success': True,
        'content': {
            'title': content.title,
            'description': content.description,
            'requirements': content.requirements,
            'rewards': content.rewards,
            'difficulty': content.difficulty_level
        }
    })
```

### 3. Scheduled Generation

```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def generate_daily_content_for_all_users():
    """Generate daily challenges for all active users"""
    engine = AIGamificationEngine()
    
    # Get active users from database
    active_users = get_active_users()  # Your implementation
    
    for user_id in active_users:
        try:
            challenges = await engine.generate_daily_challenges(user_id)
            # Send to user via notification system
            await notify_user_new_challenges(user_id, challenges)
        except Exception as e:
            logger.error(f"Failed to generate for {user_id}: {e}")

# Schedule daily at 6 AM
scheduler.add_job(
    generate_daily_content_for_all_users,
    'cron',
    hour=6,
    minute=0
)

scheduler.start()
```

## Best Practices

### 1. API Key Management
```python
# Use environment variables
os.environ['OPENAI_API_KEY'] = 'your-key'
os.environ['ANTHROPIC_API_KEY'] = 'your-key'

# Or use a secure key management service
from your_key_manager import get_secret
engine = AIGamificationEngine(
    openai_key=get_secret('openai_api_key'),
    claude_key=get_secret('anthropic_api_key')
)
```

### 2. Rate Limiting
```python
# Implement rate limiting for API calls
from asyncio import Semaphore

class RateLimitedEngine(AIGamificationEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.semaphore = Semaphore(10)  # Max 10 concurrent requests
    
    async def generate_personalized_content(self, *args, **kwargs):
        async with self.semaphore:
            return await super().generate_personalized_content(*args, **kwargs)
```

### 3. Caching Strategy
```python
from functools import lru_cache
from aiocache import cached

class CachedEngine(AIGamificationEngine):
    @cached(ttl=3600)  # Cache for 1 hour
    async def _get_user_profile(self, user_id: str):
        return await super()._get_user_profile(user_id)
```

### 4. Error Handling
```python
async def safe_generate_content(engine, user_id, content_type):
    try:
        return await engine.generate_personalized_content(
            user_id=user_id,
            content_type=content_type
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        # Return fallback content
        return GeneratedContent(
            content_type=content_type,
            title="Daily Challenge",
            description="Complete today's trading challenge",
            requirements={"trades": 3},
            rewards={"xp": 100},
            difficulty_level=5,
            estimated_completion_time=30,
            personalization_score=0.5,
            ai_provider=AIProvider.OPENAI,
            metadata={"fallback": True, "error": str(e)}
        )
```

## Monitoring and Analytics

### 1. Track Generation Performance
```python
import time

async def monitored_generation(engine, *args, **kwargs):
    start_time = time.time()
    
    try:
        content = await engine.generate_personalized_content(*args, **kwargs)
        generation_time = time.time() - start_time
        
        # Log metrics
        logger.info(f"Generation completed in {generation_time:.2f}s")
        logger.info(f"Personalization score: {content.personalization_score:.2%}")
        
        # Send to monitoring service
        send_metric('gamification.generation_time', generation_time)
        send_metric('gamification.personalization_score', content.personalization_score)
        
        return content
    except Exception as e:
        send_metric('gamification.generation_error', 1)
        raise
```

### 2. A/B Testing
```python
async def ab_test_providers(engine, user_id, content_type):
    """Test different AI providers"""
    
    # Generate with both providers
    openai_content = await engine.generate_personalized_content(
        user_id=user_id,
        content_type=content_type,
        preferred_provider=AIProvider.OPENAI
    )
    
    claude_content = await engine.generate_personalized_content(
        user_id=user_id,
        content_type=content_type,
        preferred_provider=AIProvider.CLAUDE
    )
    
    # Track which performs better
    return {
        'openai': {
            'content': openai_content,
            'score': openai_content.personalization_score
        },
        'claude': {
            'content': claude_content,
            'score': claude_content.personalization_score
        }
    }
```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   ```
   Error: Invalid API key
   Solution: Verify environment variables are set correctly
   ```

2. **Rate Limiting**
   ```
   Error: Rate limit exceeded
   Solution: Implement exponential backoff and request queuing
   ```

3. **Generation Timeouts**
   ```
   Error: Request timeout
   Solution: Increase timeout settings or use simpler prompts
   ```

4. **Low Personalization Scores**
   ```
   Issue: Content not matching user profiles well
   Solution: Enrich user profiles with more behavioral data
   ```

### Debug Mode

```python
# Enable debug logging
logging.getLogger('AIGamificationEngine').setLevel(logging.DEBUG)

# Test with verbose output
engine = AIGamificationEngine()
engine.debug_mode = True

content = await engine.generate_personalized_content(
    user_id="test_user",
    content_type=ContentGenerationType.CHALLENGE
)

# Debug output includes:
# - Full prompts sent to AI
# - Raw AI responses
# - Personalization score calculation
# - Profile matching details
```

## Future Enhancements

### Planned Features

1. **Multi-language Support**
   - Generate content in user's preferred language
   - Cultural adaptation of challenges

2. **Voice Integration**
   - AI-generated voice briefings
   - Personalized coaching messages

3. **Visual Content Generation**
   - AI-generated achievement badges
   - Dynamic mission briefing visuals

4. **Advanced Personalization**
   - Emotion-based content adaptation
   - Time-of-day optimization
   - Seasonal/event-based content

5. **Community Features**
   - AI-generated squad challenges
   - Competitive events
   - Social engagement prompts

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the example implementations
3. Consult the API documentation for OpenAI/Claude
4. Submit issues to the HydraX repository

---

**Version:** 1.0.0  
**Last Updated:** 2025-07-12  
**License:** MIT