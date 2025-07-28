# BITTEN Social Brag Notification System

## Overview

The Social Brag Notification System automatically sends military-themed squad notifications when users unlock tactical strategies, achieve rank promotions, or reach prestige levels. It integrates with the existing XP economy, referral system, and notification systems to create an engaging social experience.

## Features

- **Tactical Strategy Unlock Notifications**: Automatic squad notifications when users unlock new strategies
- **Military-Themed Messages**: Drill sergeant style messages with appropriate military terminology
- **Squad Integration**: Leverages existing referral/squad system to identify team members
- **Multi-Channel Delivery**: Uses both in-game notifications and chat notification systems
- **Cooldown System**: Prevents spam by limiting duplicate notifications
- **Flexible Integration**: Easy to integrate with existing BITTEN systems

## Components

### 1. Social Brag System (`social_brag_system.py`)
- Main notification engine
- Message templates and formatting
- Squad member discovery
- Notification delivery coordination

### 2. Integration Helper (`social_brag_integration.py`)
- Initialization and setup utilities
- Helper functions for other systems
- Global integration management

### 3. XP Economy Integration
- Automatic detection of tactical strategy unlocks
- Username lookup functionality
- Seamless integration with existing XP system

## Message Types

### Tactical Strategy Unlocks
- **FIRST_BLOOD**: "🎯 {username} just unlocked FIRST BLOOD! This soldier is ready for combat!"
- **DOUBLE_TAP**: "🎯 {username} just unlocked DOUBLE TAP! Precision firepower at its finest!"
- **TACTICAL_COMMAND**: "🎯 {username} just unlocked TACTICAL COMMAND! Another leader emerges from the ranks!"

### Rank Promotions
- **FANG**: "🏆 {username} just achieved FANG rank! Sharp teeth, sharper trades!"
- **COMMANDER**: "🏆 {username} just achieved COMMANDER rank! Leadership through firepower!"
- ****: "🏆 {username} just achieved rank! The pinnacle of trading warfare!"

### Prestige Achievements
- **Level 1**: "⭐ {username} just achieved PRESTIGE LEVEL 1! Legendary status unlocked!"
- **Level 2**: "⭐ {username} just achieved PRESTIGE LEVEL 2! Double legendary!"
- **Level 3**: "⭐ {username} just achieved PRESTIGE LEVEL 3! Triple threat activated!"

## Setup and Integration

### Basic Setup

```python
from bitten_core.social_brag_integration import setup_bitten_social_brags

# Initialize with your existing systems
success = setup_bitten_social_brags(
    xp_economy=your_xp_economy,
    referral_system=your_referral_system,
    notification_handler=your_notification_handler,
    chat_notification_service=your_chat_service,
    user_manager=your_user_manager  # For better usernames
)
```

### Manual Integration

```python
from bitten_core.social_brag_system import initialize_social_brag_system

# Initialize the social brag system
social_brag_system = initialize_social_brag_system(
    referral_system=referral_system,
    notification_handler=notification_handler,
    chat_notification_service=chat_notification_service
)

# Set up username lookup in XP economy
xp_economy.set_username_lookup_function(user_manager.get_username)
```

### Using Helper Functions

```python
from bitten_core.social_brag_integration import handle_user_rank_promotion, handle_user_prestige

# Handle rank promotion from anywhere in your system
handle_user_rank_promotion("user123", "FANG", "NIBBLER", "ALPHA-1")

# Handle prestige achievement
handle_user_prestige("user456", 1, "BRAVO-2")
```

## How It Works

### Tactical Strategy Unlocks (Automatic)

1. User earns XP through trading activities
2. XP Economy `add_xp()` method is called
3. `_check_tactical_unlocks()` detects new strategy unlocks
4. Social Brag System automatically sends notifications to squad members
5. Squad members receive notifications via multiple channels

### Manual Notifications

```python
from bitten_core.social_brag_system import get_social_brag_system

brag_system = get_social_brag_system()

# Manual tactical strategy notification
brag_system.notify_tactical_strategy_unlock(
    user_id="user123",
    username="ALPHA-1",
    strategy_name="FIRST_BLOOD",
    strategy_display_name="First Blood",
    strategy_description="Strike fast and hard with precision timing",
    xp_amount=120
)

# Manual rank promotion notification
brag_system.notify_rank_promotion(
    user_id="user123",
    username="ALPHA-1", 
    new_rank="FANG",
    old_rank="NIBBLER"
)
```

## Squad Member Discovery

The system automatically identifies squad members through:

1. **Direct Recruits**: Users recruited by the achiever
2. **Sub-Recruits**: Recruits of recruits (2 levels deep)
3. **Squad Leader**: The user who recruited the achiever

This creates a network effect where achievements are shared with the extended squad family.

## Notification Channels

### In-Game Notifications (via NotificationHandler)
- High-priority achievement notifications
- Sound effects and visual feedback
- WebApp integration ready

### Chat Notifications (via ChatNotificationService)
- Email notifications
- Telegram bot messages
- Push notifications
- Real-time chat alerts

## Customization

### Adding New Message Types

```python
# In social_brag_system.py, add to TACTICAL_STRATEGY_MESSAGES
"NEW_STRATEGY": {
    "brag_message": "🎯 {username} just unlocked NEW STRATEGY! Custom message here!",
    "drill_sergeant": "ATTENTION SQUAD! {username} has mastered NEW STRATEGY! Custom drill sergeant message!",
    "celebration_emoji": "🎯"
}
```

### Custom Username Lookup

```python
def custom_username_lookup(user_id: str) -> str:
    # Your custom logic here
    return f"CUSTOM-{user_id}"

xp_economy.set_username_lookup_function(custom_username_lookup)
```

## Configuration

### Cooldown Settings

```python
# In social_brag_system.py
self.notification_cooldown = 300  # 5 minutes between same achievement notifications
```

### Message Formatting

Messages support format strings with these variables:
- `{username}`: Display name of the achieving user
- `{strategy_name}`: Name of the unlocked strategy
- Custom variables can be added in the metadata

## Debugging and Logging

The system provides comprehensive logging:

```python
import logging
logging.getLogger('bitten_core.social_brag_system').setLevel(logging.DEBUG)
```

Key log messages:
- Tactical strategy unlock brags sent
- Squad member discovery results
- Notification delivery status
- Integration initialization status

## Performance Considerations

- **Squad member lookup**: Cached and optimized for performance
- **Cooldown system**: Prevents spam and reduces database load
- **Error isolation**: Failures in brag system don't affect core XP functionality
- **Async ready**: Designed to work with background task systems

## Testing

```python
# Test the system with mock data
if __name__ == "__main__":
    from bitten_core.social_brag_system import SocialBragSystem
    
    brag_system = SocialBragSystem()
    
    # Test tactical strategy unlock
    result = brag_system.notify_tactical_strategy_unlock(
        user_id="test_user",
        username="TEST-ALPHA",
        strategy_name="FIRST_BLOOD",
        strategy_display_name="First Blood",
        strategy_description="Test strategy",
        xp_amount=120
    )
    
    print(f"Brag result: {result}")
```

## Troubleshooting

### Common Issues

1. **No squad members found**: Check referral system integration
2. **Usernames showing as user IDs**: Set up username lookup function
3. **Notifications not sending**: Verify notification system initialization
4. **Duplicate notifications**: Check cooldown system settings

### Debug Steps

1. Check system initialization logs
2. Verify squad member discovery is working
3. Test notification delivery systems independently
4. Check username lookup function

## Integration with Other Systems

### Battle Pass Integration
```python
# When user completes battle pass tier
handle_user_rank_promotion(user_id, new_tier, old_tier, username)
```

### Achievement System Integration
```python
# When user unlocks major achievement
brag_system.notify_milestone_achievement(user_id, achievement_name, description)
```

### Trade System Integration
```python
# Already integrated via XP economy automatic tactical unlocks
# No additional code needed for basic strategy unlocks
```

## Future Enhancements

- Custom message templates per squad
- Achievement leaderboards with brag history
- Video/GIF support in notifications
- Cross-squad competition notifications
- Seasonal/event-specific brag messages

## API Reference

See the docstrings in the source files for detailed API documentation:
- `SocialBragSystem` class methods
- Helper functions in `social_brag_integration.py`
- XP Economy integration points