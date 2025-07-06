# HydraX Education XP System

## Overview

The Education XP System rewards users for engaging in learning activities while maintaining balance to prevent exploitation. The system encourages consistent learning through multipliers and bonuses while implementing anti-abuse measures.

## Education Activities & Base XP

### Core Learning Activities (5-25 XP base)
- **Complete Lesson**: 15 XP (No cooldown, 150 XP daily cap)
- **Watch Video**: 10 XP (No cooldown, 100 XP daily cap)
- **Read Article**: 5 XP (No cooldown, 50 XP daily cap)
- **Complete Quiz**: 20 XP (1 hour cooldown, 100 XP daily cap)
- **Complete Module**: 50 XP (4 hour cooldown, 150 XP daily cap)

### Interactive Activities (10-30 XP base)
- **Join Webinar**: 25 XP (24 hour cooldown, 50 XP daily cap)
- **Attend Workshop**: 30 XP (24 hour cooldown, 60 XP daily cap)
- **Participate Discussion**: 10 XP (30 min cooldown, 80 XP daily cap)
- **Ask Question**: 15 XP (1 hour cooldown, 60 XP daily cap)
- **Answer Question**: 20 XP (30 min cooldown, 100 XP daily cap)

### Practice Activities (15-35 XP base)
- **Paper Trade**: 20 XP (No cooldown, 200 XP daily cap)
- **Backtest Strategy**: 25 XP (2 hour cooldown, 100 XP daily cap)
- **Analyze Chart**: 15 XP (30 min cooldown, 120 XP daily cap)
- **Journal Entry**: 20 XP (12 hour cooldown, 40 XP daily cap)

### Advanced Activities (30-75 XP base)
- **Create Strategy**: 50 XP (24 hour cooldown, 100 XP daily cap)
- **Mentor Session**: 40 XP (24 hour cooldown, 80 XP daily cap)
- **Teach Others**: 35 XP (4 hour cooldown, 140 XP daily cap)
- **Content Creation**: 75 XP (48 hour cooldown, 150 XP daily cap)

## Multiplier System

### Daily Streak Multiplier (Compound Bonus)
- Base: 1.0x
- Increment: +0.05x per day (+5%)
- Maximum: 2.0x (reached at 20 days)
- Reset: After 48 hours of inactivity

### Squad Bonus (Group Activities)
- Small Group (2-4 people): 1.1x
- Medium Group (5-9 people): 1.2x
- Large Group (10+ people): 1.3x

### Mentor Bonus
- Helping Others: 1.25x
- Receiving Help: 1.15x
- Verified Helpful Answer: 1.5x

### Perfect Score Bonus
- Quiz: 1.5x
- Module: 1.75x
- Assessment: 2.0x

### Difficulty Tier Bonus
- Beginner: 1.0x
- Intermediate: 1.25x
- Advanced: 1.5x
- Expert: 1.75x

### Special Event Multipliers
- Double XP Weekend: 2.0x
- Learning Marathon: 1.5x
- Community Challenge: 1.75x

## Achievement Bonuses (One-Time)

- **First Lesson**: 50 XP
- **First Perfect Quiz**: 100 XP
- **Week Streak**: 200 XP
- **Month Streak**: 500 XP
- **Help 10 Traders**: 300 XP
- **Complete Course**: 1,000 XP
- **Create Popular Content**: 500 XP (50+ likes/views)
- **Mentor Badge**: 750 XP
- **Scholar Badge**: 1,000 XP (Complete all courses in tier)

## Anti-Abuse Measures

### Cooldown System
- Each activity has a specific cooldown period
- Prevents rapid farming of the same activity
- Cooldowns range from 0 (unlimited) to 48 hours

### Daily Caps
- Each activity has a maximum daily XP limit
- Prevents excessive grinding of high-value activities
- Caps are balanced based on activity value and time investment

### Multiplier Caps
- Maximum total multiplier for education: 5.0x
- Lower than trading multiplier cap (10.0x) to prevent exploitation
- Multiplicative stacking with diminishing returns

## XP Calculation Formula

```
Base XP × Streak Multiplier × Squad Bonus × Mentor Bonus × Perfect Score × Difficulty × Event = Final XP
```

Example:
- Complete Advanced Quiz with perfect score
- 10-day streak, during double XP weekend
- Base: 20 XP
- Multipliers: 1.5 (streak) × 1.5 (perfect) × 1.5 (advanced) × 2.0 (event) = 6.75x
- Capped at 5.0x
- Final XP: 20 × 5.0 = 100 XP

## Best Practices for Users

1. **Maintain Daily Streaks**: Log in daily for compound bonuses
2. **Join Group Activities**: Participate in workshops and webinars
3. **Help Others**: Answer questions and mentor for bonus XP
4. **Aim for Excellence**: Perfect scores provide significant multipliers
5. **Progress Through Tiers**: Higher difficulty = higher rewards
6. **Take Advantage of Events**: Plan learning during special events

## Integration with Trading XP

- Education XP contributes to the same milestone progression
- Balanced to complement trading XP without overshadowing it
- Target: 30-60 days to reach Elite status with combined activities
- Education alone: ~90-120 days to Elite (encourages trading participation)

## Implementation Notes

- All XP calculations are server-side to prevent manipulation
- Activity tracking persists across sessions
- Daily resets occur at midnight UTC
- Special events are configured server-side for flexibility