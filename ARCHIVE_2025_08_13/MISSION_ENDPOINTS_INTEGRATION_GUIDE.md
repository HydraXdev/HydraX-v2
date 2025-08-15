# BITTEN Mission Endpoints Integration Guide

## Overview

The enhanced `mission_endpoints.py` provides a complete REST API for managing mission data in the BITTEN trading system. This guide explains how to integrate these endpoints with the WebApp.

## Key Features

1. **Real Mission Data**: Reads actual mission files from `./missions/` directory
2. **Authentication**: Requires Bearer token and user ID for all protected endpoints
3. **Mission Management**: Create, read, update, and cancel missions
4. **Time Calculations**: Proper countdown timers and expiry handling
5. **Error Handling**: Comprehensive error responses with specific error codes
6. **Logging**: Full request/response logging for debugging

## API Endpoints

### Health Check
```
GET /api/health
```
No authentication required. Returns service status.

### Mission Status
```
GET /api/mission-status/<mission_id>
Authorization: Bearer <token>
X-User-ID: <user_id>
```
Returns detailed mission status including countdown timer.

### List Missions
```
GET /api/missions?status=pending&limit=50&offset=0
Authorization: Bearer <token>
X-User-ID: <user_id>
```
Returns paginated list of user missions with filtering options.

### Fire Mission (Execute Trade)
```
POST /api/fire
Authorization: Bearer <token>
X-User-ID: <user_id>
Content-Type: application/json

{
  "mission_id": "test_user_123_1752507290"
}
```
Executes a trade for the specified mission.

### Cancel Mission
```
POST /api/missions/<mission_id>/cancel
Authorization: Bearer <token>
X-User-ID: <user_id>
```
Cancels a pending mission.

## Authentication

All protected endpoints require:
- `Authorization: Bearer <token>` header
- `X-User-ID: <user_id>` header

The system validates:
1. Presence of both headers
2. Correct Bearer token format
3. User access to specific missions

## Mission Data Structure

```json
{
  "mission_id": "test_user_123_1752507290",
  "user_id": "test_user_123",
  "symbol": "GBPUSD",
  "type": "arcade",
  "direction": "BUY",
  "entry_price": 1.2765,
  "tp": 20,
  "sl": 10,
  "lot_size": 0.12,
  "tcs": 87,
  "confidence": 0.87,
  "expires_at": "2025-07-14T15:39:50.733860",
  "status": "pending",
  "time_remaining": 285,
  "countdown_seconds": 285,
  "is_expired": false,
  "mission_stats": {
    "fire_count": 0,
    "user_fired": false,
    "time_remaining": 285
  }
}
```

## Error Responses

All errors follow this format:
```json
{
  "status": "error",
  "reason": "error_code",
  "message": "Human readable error message"
}
```

Common error codes:
- `authentication_required`: Missing auth headers
- `invalid_token_format`: Invalid Bearer token
- `access_denied`: User doesn't have mission access
- `mission_not_found`: Mission file doesn't exist
- `mission_expired`: Mission has expired
- `already_fired`: Mission already executed
- `execution_failed`: Trade execution failed

## Integration with WebApp

### 1. Update WebApp Configuration

Add mission endpoints URL to your WebApp config:
```python
MISSION_ENDPOINTS_URL = "http://localhost:5001"
```

### 2. Authentication Integration

Use the existing authentication system to get user tokens:
```python
from src.bitten_core.user_management.auth_middleware import SessionManager

async def get_user_token(user_id):
    session = await SessionManager.validate_session(user_id)
    return session['token']
```

### 3. Mission Data Fetching

```python
import requests

async def fetch_mission_status(mission_id, user_id, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    
    response = requests.get(
        f"{MISSION_ENDPOINTS_URL}/api/mission-status/{mission_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch mission: {response.json()}")
```

### 4. Fire Button Integration

```python
async def fire_mission(mission_id, user_id, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id,
        "Content-Type": "application/json"
    }
    
    payload = {"mission_id": mission_id}
    
    response = requests.post(
        f"{MISSION_ENDPOINTS_URL}/api/fire",
        headers=headers,
        json=payload
    )
    
    return response.json()
```

### 5. Real-time Updates

For countdown timers, use JavaScript to update the UI:
```javascript
function updateCountdown(timeRemaining) {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    
    document.getElementById('countdown').textContent = 
        `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    if (timeRemaining > 0) {
        setTimeout(() => updateCountdown(timeRemaining - 1), 1000);
    } else {
        document.getElementById('mission-expired').style.display = 'block';
    }
}
```

## File Structure

```
/root/HydraX-v2/
├── src/api/mission_endpoints.py          # Enhanced API endpoints
├── src/bitten_core/fire_router.py        # Trade execution
├── missions/                             # Mission data files
│   ├── test_user_123_1752507290.json
│   ├── test_user_456_1752507290.json
│   └── ...
├── test_mission_endpoints.py            # Test script
└── MISSION_ENDPOINTS_INTEGRATION_GUIDE.md
```

## Running the Service

1. Start the mission endpoints server:
```bash
cd /root/HydraX-v2/src/api
python mission_endpoints.py
```

2. Test the endpoints:
```bash
cd /root/HydraX-v2
python test_mission_endpoints.py
```

## Security Considerations

1. **Token Validation**: Implement proper JWT token validation
2. **Rate Limiting**: Add rate limiting to prevent abuse
3. **Input Validation**: Validate all user inputs
4. **Mission Access**: Ensure users can only access their own missions
5. **Trade Execution**: Validate trading permissions before execution

## Future Enhancements

1. **WebSocket Support**: Real-time mission updates
2. **Mission Templates**: Pre-configured mission types
3. **Batch Operations**: Execute multiple missions at once
4. **Analytics**: Mission performance tracking
5. **Caching**: Redis caching for frequently accessed data

## Troubleshooting

### Common Issues

1. **Connection Refused**: Make sure the service is running on port 5001
2. **Authentication Errors**: Check Bearer token format and user ID
3. **Mission Not Found**: Verify mission file exists in missions/ directory
4. **Import Errors**: Check fire_router.py import path

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Log Files

Check logs for detailed error information:
- Application logs contain request/response details
- Error logs show stack traces for failures
- Trade execution logs track fire_router calls

## Support

For issues or questions about the mission endpoints integration, check:
1. This integration guide
2. API endpoint documentation
3. Test script examples
4. Error response codes and messages