# Press Pass XP Reset System

## Overview

The Press Pass system is a high-stakes XP mode that creates urgency and engagement by resetting users' XP to zero every night at 00:00 UTC. This dramatic feature encourages daily engagement and strategic XP spending.

## Features

### 1. Nightly XP Reset
- **Schedule**: Automatic reset at 00:00 UTC daily
- **Scope**: Only affects users who have activated Press Pass
- **Effect**: Current XP balance is set to 0, but shadow stats track real progress

### 2. Warning Notifications
- **23:00 UTC**: 1-hour warning notification
- **23:45 UTC**: 15-minute final warning
- **Content**: Shows current XP that will be lost and urges spending

### 3. Shadow Stat Tracking
Real stats are secretly maintained:
- `real_total_xp`: Actual total XP earned (never reset)
- `real_lifetime_earned`: True lifetime earnings
- `total_xp_wiped`: Cumulative XP lost to resets
- `reset_count`: Number of times reset
- `largest_wipe`: Biggest single XP loss

### 4. Dramatic Notifications
- Warning messages create urgency with countdown timers
- Reset notifications show exact amount of XP destroyed
- Uses dramatic language and emojis for impact

## Implementation

### Core Components

1. **PressPassResetManager** (`press_pass_reset.py`)
   - Manages Press Pass users
   - Handles scheduled resets
   - Tracks shadow statistics
   - Sends notifications

2. **XP Integration Updates** (`xp_integration.py`)
   - Integrates Press Pass manager
   - Updates XP awarding to maintain shadow stats
   - Provides Press Pass status in user profiles

3. **Command Handler** (`press_pass_commands.py`)
   - `/presspass` - Show info or manage Press Pass
   - `/presspass activate` - Enable Press Pass mode
   - `/presspass deactivate` - Disable Press Pass mode
   - `/presspass status` - Show detailed status
   - `/xpstatus` - Enhanced to show Press Pass warnings

4. **Scheduler Service** (`press_pass_scheduler.py`)
   - Runs as system service
   - Manages scheduled resets and warnings
   - Provides heartbeat logging

### System Service

The Press Pass scheduler runs as a systemd service:

```bash
# Install service
sudo ./scripts/setup_press_pass.sh

# Start service
sudo systemctl start press_pass_reset

# Check status
sudo systemctl status press_pass_reset

# View logs
sudo journalctl -u press_pass_reset -f
```

## Usage

### For Users

1. **Activate Press Pass**:
   ```
   /presspass activate
   ```

2. **Check Status**:
   ```
   /xpstatus
   ```
   Shows current XP and time until reset

3. **Spend XP Before Reset**:
   ```
   /xpshop
   ```
   Browse and purchase items before XP is wiped

4. **Deactivate When Needed**:
   ```
   /presspass deactivate
   ```

### For Administrators

1. **Monitor Service**:
   ```bash
   sudo systemctl status press_pass_reset
   ```

2. **Check Logs**:
   ```bash
   tail -f /root/HydraX-v2/logs/press_pass_scheduler.log
   ```

3. **Manual Reset (Testing)**:
   ```python
   # In Python console
   from bitten_core.xp_integration import XPIntegrationManager
   xp_manager = XPIntegrationManager(telegram_messenger=telegram)
   await xp_manager.press_pass_manager.manual_reset("user_id")
   ```

## Integration Points

### Telegram Bot
- Press Pass commands integrated into main command router
- Notifications sent via TelegramMessenger
- XP status commands show Press Pass warnings

### XP Economy
- XP balance reset handled through XP economy system
- Shadow stats maintained separately
- Purchases still work normally until reset

### User Profile
- Press Pass status included in user profiles
- Shadow stats available for internal tracking
- Real progress maintained for achievements

## Testing

Run the test suite:
```bash
python test_press_pass.py
```

This tests:
- Press Pass activation/deactivation
- XP awarding with shadow tracking
- Warning notifications
- XP reset execution
- Shadow stat persistence

## Security Considerations

1. **Data Persistence**: Shadow stats saved to disk immediately after updates
2. **Service Reliability**: Systemd ensures automatic restart on failure
3. **User Protection**: Deactivation immediately removes from reset list
4. **Audit Trail**: All resets logged with timestamps and amounts

## Future Enhancements

1. **Prestige Integration**: Special prestige bonuses for Press Pass users
2. **Leaderboards**: Shadow stat leaderboards for Press Pass veterans
3. **Achievements**: Special medals for surviving Press Pass streaks
4. **Variable Reset Times**: Different reset schedules for different user tiers
5. **Grace Period**: Optional 5-minute grace period after warnings