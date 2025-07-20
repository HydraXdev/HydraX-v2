# BITTEN User Registration and Authentication System

## Overview

The BITTEN user registration system provides a seamless flow from initial onboarding through full user account creation, with special support for Press Pass (7-day trial) users. The system integrates tightly with the onboarding orchestrator to create actual database users with proper authentication and session management.

## Architecture Components

### 1. Onboarding System (`/src/bitten_core/onboarding/`)
- **orchestrator.py**: Main onboarding flow controller
- **handlers.py**: Input validation and state-specific handlers
- **session_manager.py**: Temporary onboarding session storage
- **press_pass_manager.py**: Press Pass trial account management

### 2. User Management System (`/src/bitten_core/user_management/`)
- **user_manager.py**: Core user CRUD operations and authentication
- **auth_middleware.py**: Authentication decorators and session validation
- **__init__.py**: Module exports

### 3. Database Models (`/src/database/models.py`)
- **User**: Core user table with subscription info
- **UserProfile**: Extended profile with callsign, XP, preferences
- **UserSubscription**: Subscription tracking
- **Press Pass tables**: Shadow stats and conversion tracking

### 4. API Layer (`/src/bitten_core/api/`)
- **auth_api.py**: RESTful authentication endpoints
- Session management
- Profile updates
- Tier upgrades

## User Registration Flow

### 1. Onboarding Start
```python
# User starts with /start command
orchestrator.start_onboarding(user_id, telegram_id)
```

### 2. Data Collection During Onboarding
- Trading experience (yes/no)
- First name
- Email address (during secure_link phase)
- Theater selection (DEMO/LIVE/PRESS_PASS)
- Callsign creation
- Terms acceptance

### 3. User Account Creation
When onboarding completes, the system:

```python
# In orchestrator.complete_onboarding()
user_creation_result = await user_manager.create_user_from_onboarding(session.to_dict())
```

This creates:
- User record in `users` table
- UserProfile with callsign
- Initial subscription record
- Session token for immediate authentication

### 4. Press Pass Activation
For Press Pass users:
- Provisions $50K MetaQuotes demo account
- Sets 7-day expiration
- Registers for nightly XP reset
- Tracks in conversion funnel

## Authentication System

### Session Management
```python
# User login
result = await user_manager.authenticate_user(telegram_id, api_key=None)
# Returns: {
#   'authenticated': True,
#   'user_id': 123,
#   'session_token': 'secure_token',
#   'user_data': {...}
# }

# Validate session
session = await SessionManager.validate_session(token)

# Refresh session
new_token = await SessionManager.refresh_session(old_token)
```

### Authentication Middleware
```python
# Protect routes/functions
@require_auth(min_tier='FANG')
async def premium_feature(auth_session=None):
    user_id = auth_session['user_id']
    # Feature code

# Telegram bot authentication
@require_telegram_auth
async def bot_command(update, context):
    user_id = context.user_data['user_id']
    # Command code
```

## User Tier System

### Tier Levels
1. **PRESS_PASS** - 7-day trial with full features
2. **NIBBLER** - Basic paid tier ($39/mo)
3. **FANG** - Advanced tier ($89/mo)
4. **COMMANDER** - Elite tier ($189/mo)

### Tier Upgrades
```python
# Upgrade from Press Pass to paid tier
result = await user_manager.upgrade_user_tier(
    user_id=123,
    new_tier='FANG',
    payment_method='stripe'
)
```

Press Pass upgrades preserve:
- Current day's XP
- Add 50 XP enlistment bonus
- Transfer all progress

### Feature Access Control
```python
# Check feature access
if TierGuard.check_feature_access(user_tier, 'advanced_signals'):
    # Show advanced signals

# Get tier limits
limits = TierGuard.get_tier_limits('FANG')
# {
#   'daily_trades': 50,
#   'max_lot_size': 2.0,
#   'xp_multiplier': 1.5,
#   'demo_only': False
# }
```

## Database Schema

### Users Table
```sql
- user_id (PK)
- telegram_id (unique)
- username
- email
- tier
- subscription_status
- subscription_expires_at
- api_key
- created_at
```

### User Profiles Table
```sql
- profile_id (PK)
- user_id (FK)
- callsign (unique)
- total_xp
- current_rank
- notification_settings (JSON)
- trading_preferences (JSON)
- onboarding_completed
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Authenticate and get session
- `POST /api/auth/logout` - Invalidate session
- `GET /api/auth/session/validate` - Check session validity
- `POST /api/auth/session/refresh` - Refresh session token

### User Management
- `GET /api/auth/user/profile` - Get user profile
- `PUT /api/auth/user/profile` - Update profile
- `POST /api/auth/user/upgrade-tier` - Upgrade subscription tier

### Press Pass
- `GET /api/auth/press-pass/status` - Check Press Pass expiry

## Security Features

1. **Session Tokens**: Cryptographically secure tokens
2. **API Keys**: For external integrations
3. **Session TTL**: 24-hour default timeout
4. **IP Tracking**: Optional session IP binding
5. **Activity Logging**: All auth events logged

## Press Pass Special Handling

### Weekly Limits
- Maximum 200 Press Pass activations per week
- Tracked in `press_pass_weekly_limits` table
- Automatic limit checking

### Nightly XP Reset
- XP resets at midnight UTC
- Tracked in `press_pass_shadow_stats`
- Users notified of reset

### Conversion Tracking
- Time from Press Pass to paid tier
- XP preserved at conversion
- Conversion source tracking

## Integration Points

### 1. Telegram Bot
```python
# In telegram_router.py
from bitten_core.user_management.auth_middleware import require_telegram_auth

@require_telegram_auth
async def handle_command(update, context):
    # User is authenticated
    user_id = context.user_data['user_id']
```

### 2. Web Application
```javascript
// Frontend authentication
const response = await fetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ telegram_id: 12345678 })
});
const { session_token } = await response.json();

// Use token for subsequent requests
const profile = await fetch('/api/auth/user/profile', {
    headers: { 'Authorization': `Bearer ${session_token}` }
});
```

### 3. Trading System
```python
# Check user limits before trade
user_context = await SessionManager.get_user_context(session_token)
limits = TierGuard.get_tier_limits(user_context['tier'])

if trades_today >= limits['daily_trades']:
    raise TradeLimitExceeded()
```

## Testing

Run the comprehensive test suite:
```bash
python tests/test_user_registration_flow.py
```

Tests cover:
- Complete onboarding to registration flow
- Authentication and session management
- Press Pass to paid tier upgrades
- Tier access control
- Email capture during onboarding

## Migration

Apply database migrations:
```bash
psql -U bitten_user -d bitten_trading -f src/database/migrations/add_user_auth_fields.sql
```

## Best Practices

1. **Always validate sessions** before allowing access to features
2. **Check tier limits** before expensive operations
3. **Log authentication events** for security auditing
4. **Handle Press Pass expiry** gracefully with upgrade prompts
5. **Preserve user data** during tier transitions

## Error Handling

The system provides user-friendly error messages:
- "User not registered" → Redirect to onboarding
- "Session expired" → Prompt to login again
- "Tier insufficient" → Show upgrade options
- "Press Pass expired" → Display upgrade paths

## Future Enhancements

1. **OAuth Integration**: Support for Google/Apple login
2. **2FA Support**: Two-factor authentication
3. **Session Clustering**: Redis-based distributed sessions
4. **Biometric Auth**: For mobile app
5. **SSO Support**: Enterprise single sign-on