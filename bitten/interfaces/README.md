# Shepherd Interfaces for HydraX-v2

This directory contains two interface implementations for the Shepherd system:

## 1. Shepherd CLI (`shepherd_cli.py`)

A command-line interface for managing and debugging the HydraX-v2 system.

### Usage

```bash
# Show connections for a module
python shepherd_cli.py trace risk_controller

# Explain what triggered an event
python shepherd_cli.py why "high_volatility_signal"

# Get function documentation
python shepherd_cli.py doc process_signal

# Test impact of changes
python shepherd_cli.py simulate "increase risk limit to 15%"

# Save system state checkpoint
python shepherd_cli.py checkpoint "before production deploy"
```

### Features

- **trace**: Display inbound/outbound connections and dependencies for any module
- **why**: Show the complete trigger chain that led to a specific event
- **doc**: Get detailed documentation for functions including signatures and examples
- **simulate**: Test the impact of proposed changes before implementation
- **checkpoint**: Save current system state with a descriptive label

## 2. Shepherd Webhook API (`shepherd_webhook.py`)

A RESTful API server providing HTTP endpoints for system management.

### Running the Server

```bash
# Development mode
python shepherd_webhook.py

# Production mode (with gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 shepherd_webhook:app
```

### API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/validate` | Validate logic configuration | Yes |
| GET | `/api/v1/trace/:module` | Get module connections | Yes |
| POST | `/api/v1/simulate` | Test proposed changes | Yes |
| GET | `/api/v1/status` | System health check | No |
| POST | `/api/v1/webhook` | Receive external webhooks | No* |

*Webhook endpoint uses signature verification instead of bearer token

### Authentication

Most endpoints require a Bearer token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:5000/api/v1/trace/risk_controller
```

### Example API Calls

```bash
# Validate logic configuration
curl -X POST http://localhost:5000/api/v1/validate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module": "risk_controller",
    "logic_type": "risk_management",
    "configuration": {
      "max_risk": 0.05,
      "stop_loss": 0.02
    }
  }'

# Get module trace
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:5000/api/v1/trace/signal_processor

# Simulate changes
curl -X POST http://localhost:5000/api/v1/simulate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "change_type": "configuration",
    "changes": {
      "risk_limits": {"max_exposure": 0.1},
      "signal_threshold": 0.8
    },
    "duration": "24h"
  }'

# Check system health (no auth required)
curl http://localhost:5000/api/v1/status
```

## Directory Structure

The interfaces expect the following directory structure:

```
/root/HydraX-v2/bitten/
├── interfaces/
│   ├── shepherd_cli.py      # CLI interface
│   ├── shepherd_webhook.py  # Web API interface
│   └── README.md           # This file
└── data/
    └── shepherd/
        ├── state.json      # System state
        ├── metrics.json    # Performance metrics
        └── checkpoints/    # Saved checkpoints
```

## Environment Variables

### For Webhook API:

- `SHEPHERD_SECRET_KEY`: Secret key for webhook signature verification (default: 'development-secret-key')

## Security Notes

1. In production, replace the mock authentication with proper token validation
2. Use HTTPS for all API communications
3. Set strong secret keys for webhook signature verification
4. Implement rate limiting to prevent abuse
5. Regular security audits of exposed endpoints

## Integration

Both interfaces are designed to integrate with the existing HydraX-v2 system. The mock implementations should be replaced with actual system calls to:

- Risk management modules
- Signal processing systems
- Database connections
- Monitoring systems
- Configuration managers

## Development

To extend these interfaces:

1. Add new commands to the CLI by creating new methods in `ShepherdCLI` class
2. Add new API endpoints by creating new routes in the webhook server
3. Update the mock implementations with real system integration
4. Add proper error handling and logging
5. Implement comprehensive test suites

## Requirements

```
flask>=2.0.0
flask-cors>=3.0.0
```

Install with: `pip install flask flask-cors`