# Alert Feed API Documentation

## Endpoint: `/api/alerts/feed`

### Purpose
Returns a user's signal feed with fire status, showing which signals have been fired and which are still available to trade.

### Authentication
- **Required**: Firebase ID token in Authorization header
- **Format**: `Authorization: Bearer <firebase_id_token>`
- **Development Mode**: When Firebase is not initialized, defaults to user `wlJ5lafBqRSLwHIUBxJQMr4SBtk1`

### Request

#### Method
`GET /api/alerts/feed`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Maximum number of alerts to return |
| `hours` | integer | 24 | Number of hours to look back |

#### Example Requests

```bash
# Basic request (last 24 hours, max 50 alerts)
curl -X GET http://localhost:8888/api/alerts/feed \
  -H "Authorization: Bearer <firebase_token>"

# Custom time range (last 12 hours, max 10 alerts)
curl -X GET "http://localhost:8888/api/alerts/feed?hours=12&limit=10" \
  -H "Authorization: Bearer <firebase_token>"

# Recent signals only (last 1 hour)
curl -X GET "http://localhost:8888/api/alerts/feed?hours=1&limit=20" \
  -H "Authorization: Bearer <firebase_token>"
```

### Response

#### Success Response (200 OK)

```json
{
  "alerts": [
    {
      "signal_id": "ELITE_RAPID_GBPUSD_1760968694",
      "symbol": "GBPUSD",
      "direction": "BUY",
      "entry_price": 1.27345,
      "sl": 1.27295,
      "tp": 1.27445,
      "confidence": 87.0,
      "pattern_type": "BB_SCALP",
      "created_at": 1760968694,

      "fire_id": "ELITE_RAPID_GBPUSD_1760968694",
      "fire_mode": "AUTO",
      "fire_status": "FILLED",
      "fired_at": 1760968700,

      "is_fired": true,
      "can_fire": false,
      "is_settled": false,

      "outcome": null,
      "duration_seconds": null
    },
    {
      "signal_id": "ELITE_RAPID_EURUSD_1760968500",
      "symbol": "EURUSD",
      "direction": "SELL",
      "entry_price": 1.08456,
      "sl": 1.08506,
      "tp": 1.08356,
      "confidence": 82.5,
      "pattern_type": "KALMAN_QUICKFIRE",
      "created_at": 1760968500,

      "fire_id": null,
      "fire_mode": null,
      "fire_status": null,
      "fired_at": null,

      "is_fired": false,
      "can_fire": true,
      "is_settled": false,

      "outcome": null,
      "duration_seconds": null
    },
    {
      "signal_id": "ELITE_RAPID_USDJPY_1760965000",
      "symbol": "USDJPY",
      "direction": "BUY",
      "entry_price": 149.850,
      "sl": 149.800,
      "tp": 149.950,
      "confidence": 85.0,
      "pattern_type": "BB_SCALP",
      "created_at": 1760965000,

      "fire_id": null,
      "fire_mode": null,
      "fire_status": null,
      "fired_at": null,

      "is_fired": false,
      "can_fire": false,
      "is_settled": true,

      "outcome": "WIN",
      "duration_seconds": 3420
    }
  ],
  "user_id": "wlJ5lafBqRSLwHIUBxJQMr4SBtk1",
  "hours_lookback": 24,
  "limit": 50,
  "count": 3
}
```

#### Response Fields

##### Root Level
| Field | Type | Description |
|-------|------|-------------|
| `alerts` | array | Array of alert objects |
| `user_id` | string | Firebase UID of the authenticated user |
| `hours_lookback` | integer | Number of hours searched |
| `limit` | integer | Maximum alerts requested |
| `count` | integer | Actual number of alerts returned |

##### Alert Object
| Field | Type | Description |
|-------|------|-------------|
| `signal_id` | string | Unique signal identifier |
| `symbol` | string | Trading pair (e.g., "GBPUSD") |
| `direction` | string | "BUY" or "SELL" |
| `entry_price` | float | Signal entry price |
| `sl` | float | Stop loss price |
| `tp` | float | Take profit price |
| `confidence` | float | Signal confidence percentage |
| `pattern_type` | string | Pattern that generated signal |
| `created_at` | integer | Unix timestamp of signal creation |
| **Fire Status** | | |
| `fire_id` | string \| null | Fire ID if user fired this signal |
| `fire_mode` | string \| null | "AUTO" or "MANUAL" if fired |
| `fire_status` | string \| null | "SENT", "FILLED", etc. if fired |
| `fired_at` | integer \| null | Unix timestamp when fired |
| **UI State Flags** | | |
| `is_fired` | boolean | `true` if user has fired this signal |
| `can_fire` | boolean | `true` if signal can still be fired |
| `is_settled` | boolean | `true` if signal has reached TP/SL |
| **Outcome** | | |
| `outcome` | string \| null | "WIN" or "LOSS" when settled |
| `duration_seconds` | integer \| null | Time from signal to TP/SL |

### UI State Logic

The endpoint provides three boolean flags for easy UI state management:

#### `is_fired`
- **true**: User has executed this signal
- **false**: User has not fired this signal
- **UI Action**: Show "Fired" badge, disable fire button

#### `can_fire`
- **true**: Signal can still be executed (not fired, not settled)
- **false**: Signal cannot be fired (already fired or expired/settled)
- **UI Action**: Enable/disable "Fire" button

#### `is_settled`
- **true**: Signal has reached TP or SL (outcome determined)
- **false**: Signal still active or expired without hitting TP/SL
- **UI Action**: Show outcome badge (WIN/LOSS), move to history

### Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Missing Authorization header. Provide: Authorization: Bearer <token>"
}
```

#### 403 Forbidden
```json
{
  "detail": "Forbidden: You can only access your own data"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Database error: <error_message>"
}
```

## Implementation Details

### Files Created
1. `/root/HydraX-v2/services/api_server/rest/alerts.py` - Alert feed endpoint
2. `/root/HydraX-v2/test_alert_feed_endpoint.py` - Test script

### Files Modified
1. `/root/HydraX-v2/services/api_server/main.py`:
   - Added `alerts` to imports (line 29)
   - Registered `alerts.router` (line 147)

### Database Query
The endpoint uses a LEFT JOIN to combine signals with fires:

```sql
SELECT
    s.signal_id,
    s.symbol,
    s.direction,
    s.entry_price,
    s.sl,
    s.tp,
    s.confidence,
    s.pattern_type,
    s.created_at,
    s.outcome,
    s.duration_seconds,
    f.fire_id,
    f.fire_mode,
    f.status as fire_status,
    f.created_at as fired_at
FROM signals s
LEFT JOIN fires f ON (
    f.mission_id = s.signal_id
    AND f.user_id = ?
    AND f.status IN ('SENT', 'FILLED')
)
WHERE s.created_at > ?
ORDER BY s.created_at DESC
LIMIT ?
```

### Authentication Flow
1. Extract Firebase ID token from `Authorization: Bearer <token>` header
2. Verify token with Firebase Admin SDK
3. Extract user UID from verified token
4. Use UID to filter signals/fires in database

### Performance Considerations
- Database query is indexed on `signals.created_at` and `fires.user_id`
- Default limit of 50 prevents excessive data transfer
- Time-based filtering reduces query scope
- LEFT JOIN ensures all signals are returned (fired or not)

## Testing

### Manual Test (Development Mode)
```bash
# Test endpoint (no auth needed in dev mode)
curl -X GET http://localhost:8888/api/alerts/feed

# Test with parameters
curl -X GET "http://localhost:8888/api/alerts/feed?hours=12&limit=10"
```

### Automated Test Script
```bash
# Run test suite
python3 /root/HydraX-v2/test_alert_feed_endpoint.py
```

### Expected Results
1. Returns 200 OK with JSON response
2. `count` field matches number of alerts in array
3. Alerts ordered by `created_at` descending (newest first)
4. Fired signals have `is_fired=true` and fire status fields populated
5. Unfired signals have `is_fired=false` and null fire status fields

## Integration Notes

### For Frontend Developers
1. **Authentication**: Include Firebase ID token in all requests
2. **Polling**: Consider polling every 30-60 seconds for live updates
3. **State Management**: Use `is_fired`, `can_fire`, `is_settled` for UI logic
4. **Error Handling**: Handle 401 (token expired) by refreshing token

### For Backend Developers
1. **Server Restart Required**: API server must be restarted to load new endpoint
2. **Database**: Uses existing SQLite database at `/root/HydraX-v2/bitten.db`
3. **Authentication**: Uses existing Firebase auth middleware
4. **No Breaking Changes**: New endpoint, no modifications to existing code

## Deployment Checklist

- [x] Create `alerts.py` endpoint file
- [x] Register router in `main.py`
- [x] Verify Python syntax
- [x] Create test script
- [ ] Restart API server (pm2 restart api_server)
- [ ] Run test script to verify endpoint works
- [ ] Monitor logs for errors
- [ ] Test with real Firebase token in production

## Future Enhancements

1. **WebSocket Support**: Real-time push of new alerts
2. **Filtering**: Add query params for symbol, pattern_type, direction
3. **Pagination**: Cursor-based pagination for large datasets
4. **Caching**: Redis cache for frequently accessed data
5. **Aggregation**: Add summary statistics (fired count, win rate, etc.)
