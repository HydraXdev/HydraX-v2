# BITTEN Elite Referral System

## Overview

The BITTEN Referral System is a comprehensive military-style recruitment system that gamifies user acquisition through squad building mechanics. Users can generate unique referral codes, recruit new members, and earn XP rewards based on their recruits' activities.

## Features

### 1. **Unique Referral Codes**
- Each user can generate a personalized referral code
- Support for custom codes (e.g., "ELITE", "ALPHA")
- Automatic generation of random codes if not specified
- Codes are permanent unless expired

### 2. **Multi-Tier Referral Chains**
- Track up to 3 levels of referrals
- Direct referrals (Tier 1): 100% rewards
- Secondary referrals (Tier 2): 50% rewards
- Tertiary referrals (Tier 3): 25% rewards

### 3. **Reward System**
- **Join Bonus**: 100 XP when someone uses your code
- **First Trade**: 50 XP when recruit completes first trade
- **Rank Achievements**:
  - Fang Tier: 25 XP
  - Commander Tier: 100 XP
  - Apex Tier: 250 XP
- **Weekly Activity**: 10 XP for active recruits
- **Trade Milestones**: 20 XP every 10 trades

### 4. **Squad Multipliers**
- 5+ recruits: 1.1x multiplier (10% bonus)
- 10+ recruits: 1.25x multiplier (25% bonus)
- 25+ recruits: 1.5x multiplier (50% bonus)
- 50+ recruits: 2.0x multiplier (100% bonus)
- 100+ recruits: 3.0x multiplier (200% bonus)

### 5. **Anti-Abuse Mechanisms**
- IP tracking to prevent self-referrals
- Maximum 10 referrals per day per user
- Maximum 3 referrals per IP address per day
- 5-minute cooldown between referrals from same IP
- 24-hour IP blocking for violations

### 6. **Squad Ranks**
- **Lone Wolf**: 0 recruits
- **Team Leader**: 1-4 recruits
- **Squad Leader**: 5-9 recruits
- **Platoon Sergeant**: 10-24 recruits
- **Company Commander**: 25-49 recruits
- **Battalion Commander**: 50-99 recruits
- **Brigade General**: 100+ recruits

### 7. **Special Promo Codes**
- Admin/Elite users can create promo codes
- Configurable bonus multipliers (e.g., 2x XP)
- Usage limits and expiration dates
- Perfect for campaigns and events

## Telegram Commands

### `/refer` - View your referral status
Shows current squad status, referral code, and basic stats

### `/refer generate [code]` - Generate referral code
- Without argument: generates random code
- With argument: creates custom code (if available)

### `/refer stats` - Detailed statistics
- Complete breakdown of recruits
- Recent rewards earned
- Top performing squad members

### `/refer tree` - Squad genealogy
- Visual representation of your recruitment tree
- Shows all tiers of referrals
- Displays activity status

### `/refer leaderboard` - Top recruiters
- Shows top 10 squad commanders
- Ranked by total XP earned from referrals

## Integration Points

### 1. **XP Economy Integration**
```python
from xp_economy import XPEconomy
referral_system = ReferralSystem(xp_economy=xp_economy)
```

### 2. **Trade Completion Hook**
```python
referral_integration.on_trade_completed(user_id, trade_data)
```

### 3. **Rank Upgrade Hook**
```python
referral_integration.on_rank_upgraded(user_id, new_rank, old_rank)
```

### 4. **Weekly Activity Check**
```python
referral_integration.on_weekly_activity_check(user_id)
```

## Database Schema

### Tables:
- `referral_codes` - Stores all generated codes
- `recruits` - Tracks all recruited users
- `referral_rewards` - Logs all XP rewards
- `ip_tracking` - Anti-abuse IP monitoring
- `blocked_ips` - Temporarily blocked IPs
- `squad_stats` - Aggregate squad statistics

## Usage Examples

### Generating a Referral Code
```
/refer generate ALPHA
```

### Using a Referral Code (during /start)
```
/start ALPHA
```

### Viewing Squad Status
```
/refer
```

### Creating a Promo Code (Admin)
```python
referral_system.create_promo_code(
    "WEEKEND50",
    creator_id,
    max_uses=100,
    expires_in_days=3,
    xp_multiplier=1.5
)
```

## Security Features

1. **IP-based Protection**
   - Tracks IP addresses for all referral actions
   - Prevents multiple accounts from same IP
   - Auto-blocks suspicious activity

2. **Rate Limiting**
   - Daily limits on referral generation
   - Cooldown periods between actions
   - Progressive penalties for violations

3. **Data Validation**
   - Sanitized inputs for all user data
   - SQL injection protection
   - Code uniqueness enforcement

## Best Practices

1. **For Users**:
   - Share your code on social media
   - Help recruits complete their first trades
   - Build an active squad for maximum rewards

2. **For Admins**:
   - Monitor the leaderboard for suspicious activity
   - Create promo codes for special events
   - Use IP logs to identify abuse patterns

## Military Theme Elements

The system uses military terminology throughout:
- "Squad" instead of team
- "Recruits" instead of referrals
- Military ranks for progression
- "Elite force" messaging
- Combat-style achievements

This creates an engaging, thematic experience that aligns with BITTEN's tactical trading narrative.

## Performance Considerations

- Efficient SQL indexing on key columns
- Caching of frequently accessed data
- Batch processing for reward calculations
- Automatic cleanup of expired data

## Future Enhancements

1. **Squad Battles**: Competitions between squads
2. **Special Missions**: Time-limited recruitment campaigns
3. **Squad Chat**: Private channels for squad communication
4. **Advanced Analytics**: Detailed recruitment funnel metrics
5. **NFT Badges**: Blockchain-based achievement system