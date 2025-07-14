# API Endpoints Documentation

This document describes the new API endpoints added to the HydraX v2 webapp server.

## Base URL
```
http://localhost:8888
```

## Endpoints

### 1. POST /api/fire
Handle user fire actions with user_id and signal_id.

**Request:**
```json
{
  "user_id": "string",
  "signal_id": "string"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Fire action recorded successfully",
  "user_id": "string",
  "signal_id": "string",
  "fired_at": "ISO8601 timestamp"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Error message"
}
```

**HTTP Status Codes:**
- 200: Success
- 400: Bad Request (missing or invalid parameters)
- 500: Internal Server Error

### 2. GET /api/stats/<signal_id>
Return live engagement data for a specific signal.

**Parameters:**
- `signal_id`: The ID of the signal to get stats for

**Response:**
```json
{
  "success": true,
  "data": {
    "signal_id": "string",
    "total_fires": 0,
    "unique_users": 0,
    "recent_fires_24h": 0,
    "last_fire_time": "ISO8601 timestamp or null",
    "engagement_rate": 0.0,
    "created_at": "ISO8601 timestamp or null",
    "updated_at": "ISO8601 timestamp or null"
  }
}
```

**HTTP Status Codes:**
- 200: Success
- 400: Bad Request (missing signal_id)
- 500: Internal Server Error

### 3. GET /api/user/<user_id>/stats
Return real user statistics.

**Parameters:**
- `user_id`: The ID of the user to get stats for

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "string",
    "total_fires": 0,
    "total_signals_engaged": 0,
    "unique_signals_fired": 0,
    "recent_fires_7d": 0,
    "last_fire_time": "ISO8601 timestamp or null",
    "streak_days": 0,
    "tier": "string",
    "avg_fires_per_signal": 0.0,
    "created_at": "ISO8601 timestamp or null",
    "updated_at": "ISO8601 timestamp or null"
  }
}
```

**HTTP Status Codes:**
- 200: Success
- 400: Bad Request (missing user_id)
- 500: Internal Server Error

### 4. GET /api/signals/active
Return all active signals with engagement counts.

**Response:**
```json
{
  "success": true,
  "data": {
    "signals": [
      {
        "signal_id": "string",
        "signal_data": {
          "pair": "string",
          "pattern": "string",
          "entry": 0.0,
          "stop_loss": 0.0,
          "take_profit": 0.0,
          "confidence": 0,
          "tier": "string"
        },
        "engagement": {
          "total_fires": 0,
          "unique_users": 0,
          "last_fire_time": "ISO8601 timestamp or null"
        },
        "created_at": "ISO8601 timestamp",
        "expires_at": "ISO8601 timestamp"
      }
    ],
    "total_count": 0,
    "timestamp": "ISO8601 timestamp"
  }
}
```

**HTTP Status Codes:**
- 200: Success
- 500: Internal Server Error

## Real-time Updates

The fire endpoint also emits real-time updates via WebSocket to subscribers in the signal's room:

```javascript
// Client receives this event when someone fires on a signal
socket.on('fire_update', function(data) {
  // data contains:
  // {
  //   user_id: "string",
  //   signal_id: "string", 
  //   timestamp: "ISO8601 timestamp"
  // }
});
```

## Error Handling

All endpoints include proper error handling:

- **400 Bad Request**: Missing or invalid parameters
- **500 Internal Server Error**: Database or server errors
- Errors return JSON with `success: false` and `error: "message"`

## Example Usage

### Using curl:
```bash
# Fire on a signal
curl -X POST http://localhost:8888/api/fire \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "signal_id": "EURUSD_LONDON_RAID_001"}'

# Get signal stats
curl http://localhost:8888/api/stats/EURUSD_LONDON_RAID_001

# Get user stats
curl http://localhost:8888/api/user/user123/stats

# Get active signals
curl http://localhost:8888/api/signals/active
```

### Using JavaScript:
```javascript
// Fire on a signal
fetch('/api/fire', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 'user123',
    signal_id: 'EURUSD_LONDON_RAID_001'
  })
})
.then(response => response.json())
.then(data => console.log(data));

// Get signal stats
fetch('/api/stats/EURUSD_LONDON_RAID_001')
  .then(response => response.json())
  .then(data => console.log(data));
```

## Database Integration

The API endpoints integrate with the `engagement_db` module which provides:

- SQLite database for persistence
- Automatic database table creation
- Engagement tracking and analytics
- User statistics and tier calculation
- Signal activity monitoring

## Testing

Use the provided test scripts:

- `test_engagement_functions.py`: Test database functions directly
- `test_api_curl.sh`: Test API endpoints with curl
- `test_api_endpoints.py`: Test API endpoints with Python requests
- `populate_engagement_test_data.py`: Populate database with test data