# User Engagement Database System

## Overview

The SQLite database infrastructure for user engagement tracking provides comprehensive functionality for tracking user interactions with trading signals, including signal fires, user statistics, and performance metrics.

## Database Location

- **Database File**: `/root/HydraX-v2/data/engagement.db`
- **Module**: `/root/HydraX-v2/database/engagement_db.py`

## Database Schema

### Tables

#### 1. `signal_fires`
Primary table for tracking signal fire events.

```sql
CREATE TABLE signal_fires (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    signal_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    executed BOOLEAN NOT NULL DEFAULT 0,
    UNIQUE(user_id, signal_id)
);
```

#### 2. `user_stats`
User performance and engagement statistics.

```sql
CREATE TABLE user_stats (
    user_id INTEGER PRIMARY KEY,
    total_fires INTEGER NOT NULL DEFAULT 0,
    win_rate REAL NOT NULL DEFAULT 0.0,
    pnl REAL NOT NULL DEFAULT 0.0,
    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. `signal_metrics`
Signal-level engagement metrics.

```sql
CREATE TABLE signal_metrics (
    signal_id TEXT PRIMARY KEY,
    total_fires INTEGER NOT NULL DEFAULT 0,
    active_users INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes

- `idx_signal_fires_user_id` - Fast user lookup
- `idx_signal_fires_signal_id` - Fast signal lookup
- `idx_signal_fires_timestamp` - Time-based queries
- `idx_user_stats_last_updated` - Recent activity tracking

## Core Functionality

### 1. Database Connection Management

```python
from database.engagement_db import EngagementDatabase

db = EngagementDatabase()
# Context manager automatically handles connections
with db.get_connection() as conn:
    # Database operations
    pass
```

### 2. Signal Fire Tracking

```python
# Record a signal fire
success = db.record_signal_fire(
    user_id=12345,
    signal_id="EURUSD_LONG_001",
    executed=True
)

# Get user's signal fires
fires = db.get_user_signal_fires(user_id=12345, limit=50)

# Get fires for a specific signal
signal_fires = db.get_signal_fires_by_signal("EURUSD_LONG_001")
```

### 3. User Statistics

```python
# Get user statistics
stats = db.get_user_stats(user_id=12345)

# Update user performance
db.update_user_pnl(
    user_id=12345,
    pnl_change=150.75,
    is_win=True
)

# Get comprehensive user summary
summary = db.get_user_engagement_summary(user_id=12345)
```

### 4. Signal Metrics

```python
# Get signal metrics
metrics = db.get_signal_metrics("EURUSD_LONG_001")
print(f"Total fires: {metrics.total_fires}")
print(f"Active users: {metrics.active_users}")
```

### 5. Real-time Engagement Statistics

```python
# Get current engagement stats
stats = db.get_real_time_engagement_stats()
print(f"Today's fires: {stats['total_fires_today']}")
print(f"Active users: {stats['active_users_today']}")
print(f"Execution rate: {stats['execution_rate']:.2%}")
```

## Helper Functions

### Quick Access Functions

```python
from database.engagement_db import (
    record_user_signal_fire,
    get_engagement_stats,
    get_user_engagement_data,
    update_user_performance
)

# Record signal fire
record_user_signal_fire(user_id=12345, signal_id="EURUSD_LONG_001", executed=True)

# Get real-time stats
stats = get_engagement_stats()

# Get user data
user_data = get_user_engagement_data(user_id=12345)

# Update performance
update_user_performance(user_id=12345, pnl_change=100.0, is_win=True)
```

## Advanced Features

### 1. Leaderboards

```python
# Get top performers
top_by_fires = db.get_leaderboard(metric='total_fires', limit=10)
top_by_winrate = db.get_leaderboard(metric='win_rate', limit=10)
top_by_pnl = db.get_leaderboard(metric='pnl', limit=10)
```

### 2. Data Export

```python
# Export all user data
export_data = db.export_user_data(user_id=12345)
# Contains: user_stats, signal_fires, engagement_summary
```

### 3. Data Cleanup

```python
# Clean up old data (keep last 90 days)
deleted_count = db.cleanup_old_data(days_to_keep=90)
```

### 4. Streak Calculation

The system automatically calculates consecutive day streaks for users based on their signal fire activity.

## Database Migration

### Initial Setup

```python
from database.engagement_db import run_migration

# Run migration to create tables
if run_migration():
    print("Database ready!")
```

### Manual Migration

```python
db = EngagementDatabase()
db.initialize_database()
```

## Data Models

### SignalFire

```python
@dataclass
class SignalFire:
    id: Optional[int] = None
    user_id: int = None
    signal_id: str = None
    timestamp: datetime = None
    executed: bool = False
```

### UserStats

```python
@dataclass
class UserStats:
    user_id: int = None
    total_fires: int = 0
    win_rate: float = 0.0
    pnl: float = 0.0
    last_updated: datetime = None
```

### SignalMetrics

```python
@dataclass
class SignalMetrics:
    signal_id: str = None
    total_fires: int = 0
    active_users: int = 0
    created_at: datetime = None
```

## Testing

### Run Tests

```bash
python3 database/test_engagement_db.py
```

### Verify Database Structure

```bash
python3 database/verify_db_structure.py
```

## Performance Considerations

- **Indexes**: Strategic indexes on frequently queried columns
- **Connection Management**: Context managers for proper connection handling
- **Batch Operations**: Efficient bulk operations for large datasets
- **Data Cleanup**: Automatic cleanup of old data to maintain performance

## Security Features

- **SQL Injection Protection**: All queries use parameterized statements
- **Input Validation**: Data validation through dataclasses
- **Error Handling**: Comprehensive error handling with logging
- **Transaction Management**: Automatic rollback on errors

## Logging

The system includes comprehensive logging for:
- Database operations
- Error conditions
- Performance metrics
- Data cleanup operations

## Integration Examples

### With Telegram Bot

```python
from database.engagement_db import record_user_signal_fire

def handle_signal_fire(user_id, signal_id):
    # Record the signal fire
    success = record_user_signal_fire(
        user_id=user_id,
        signal_id=signal_id,
        executed=True
    )
    
    if success:
        # Send confirmation to user
        send_telegram_message(user_id, "Signal fired successfully!")
```

### With Trading System

```python
from database.engagement_db import update_user_performance

def on_trade_close(user_id, pnl, is_win):
    # Update user performance
    update_user_performance(
        user_id=user_id,
        pnl_change=pnl,
        is_win=is_win
    )
```

## Monitoring and Analytics

The system provides real-time analytics for:
- Daily engagement metrics
- User performance tracking
- Signal popularity analysis
- Execution rate monitoring
- Streak tracking
- Leaderboard generation

## Future Enhancements

Potential future features:
- Time-based engagement analysis
- Advanced streak rewards
- Social features integration
- Performance prediction models
- Custom metric definitions
- API endpoints for external access

## Troubleshooting

### Common Issues

1. **Database locked**: Ensure proper connection handling with context managers
2. **Migration failures**: Check file permissions and disk space
3. **Performance issues**: Review indexes and consider data cleanup
4. **Data inconsistencies**: Use transaction management for multi-step operations

### Log Analysis

Check logs for:
- Database connection errors
- Query performance issues
- Data validation failures
- Migration problems

## Support

For issues or questions regarding the engagement database system, check:
- Error logs in the application
- Database file permissions
- Available disk space
- Python SQLite3 module availability