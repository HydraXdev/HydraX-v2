# BITTEN Bot Control System Documentation

## Overview
The BITTEN Bot Control System provides comprehensive control over AI bot personalities, allowing users to customize their trading experience. The system includes a mandatory disclaimer, individual bot toggles, and immersion level settings.

## Features

### 1. Disclaimer Management
- **Prominent onboarding disclaimer** about fictional AI personalities
- Must be accepted before using BITTEN
- Clearly states all characters are fictional motivational overlays

### 2. Bot Control Commands

#### `/disclaimer`
- View the full system disclaimer at any time
- Available to all users (UserRank.USER+)

#### `/bots [on/off]`
- Master toggle for all AI bot personalities
- No arguments: Shows current bot status
- `on`: Enables all bots
- `off`: Disables all bots

#### `/toggle [BotName]`
- Toggle individual bot on/off
- Available bots: DrillBot, MedicBot, RecruiterBot, OverwatchBot, StealthBot
- Only works when master bot switch is ON

#### `/immersion [level]`
- Set experience intensity level
- Levels:
  - `full`: Maximum intensity, all features enabled
  - `moderate`: Balanced experience (recommended)
  - `minimal`: Just trading, minimal extras

#### `/settings`
- View comprehensive bot settings menu
- Shows all bot statuses and current preferences
- Organized in clear sections

### 3. Bot Personalities

1. **DrillBot** (Discipline Coach)
   - Military-style motivation and discipline enforcement
   - Intensity: High

2. **MedicBot** (Emotional Support)
   - Provides comfort and psychological support during losses
   - Intensity: Medium

3. **RecruiterBot** (Community Builder)
   - Encourages network participation and growth
   - Intensity: Low

4. **OverwatchBot** (Performance Analyst)
   - Provides detailed performance analysis
   - Intensity: Low

5. **StealthBot** (Hidden Insights)
   - Occasional mysterious insights and warnings
   - Intensity: Low

### 4. Integration Features

#### Message Filtering
- Bot messages are automatically filtered based on user preferences
- Messages from disabled bots are not shown
- System respects individual bot toggles

#### Immersion-Based Formatting
- **Full**: Enhanced formatting with emojis and effects
- **Moderate**: Standard formatting
- **Minimal**: Toned-down messages with minimal formatting

#### Status Display
- Bot status automatically appears in `/status` command
- Shows enabled/disabled state and active bot count

## Implementation Details

### File Structure
```
src/bitten_core/
├── telegram_bot_controls.py      # Main bot control handlers
├── bot_control_integration.py    # Integration with BITTEN Core
└── psyops/
    └── disclaimer_manager.py     # Disclaimer and consent management
```

### Key Classes
- `TelegramBotControls`: Handles all bot control commands
- `DisclaimerManager`: Manages user consent and preferences
- `BotControlIntegration`: Integrates with main telegram router
- `BotMessageMiddleware`: Filters messages based on preferences

### User Consent Storage
- Stored per user_id
- Tracks:
  - Disclaimer acceptance
  - Bot enabled/disabled state
  - Individual bot preferences
  - Immersion level
  - Timestamp of acceptance

## Legal Compliance
The system ensures legal compliance by:
1. Requiring explicit disclaimer acceptance
2. Clearly stating all personalities are fictional
3. Providing easy ON/OFF toggles
4. Respecting user preferences immediately
5. No bot messages sent when disabled

## Usage Example
```
1. User joins BITTEN
2. /start - Shows they need to accept disclaimer
3. /disclaimer - Shows full disclaimer
4. User accepts with bot preferences
5. /settings - Shows their current settings
6. /toggle DrillBot - Disables DrillBot
7. /immersion minimal - Sets minimal experience
8. /bots off - Disables all bots
```

## Technical Notes
- Commands are available to all users (UserRank.USER)
- Preferences persist across sessions
- Bot messages include formatting based on immersion level
- System gracefully handles missing preferences