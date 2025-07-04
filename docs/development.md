# Development Guide

## Setup Development Environment

### Prerequisites
- Python 3.8+
- Git
- Make (optional, for convenience)

### Initial Setup
```bash
# Clone the repository
git clone https://github.com/HydraXdev/HydraX-v2.git
cd HydraX-v2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make dev
# Or manually: pip install -r requirements.txt -r requirements-dev.txt

# Copy environment template
cp .env.example .env
# Edit .env with your configuration
```

## Project Structure

```
HydraX-v2/
├── src/
│   ├── core/
│   │   ├── hydrastrike_v3.5.py     # Core engine
│   │   ├── TEN_elite_commands_FULL.py  # Flask API
│   │   └── modules/
│   │       ├── bitmode.py          # Safe scalping mode
│   │       ├── commandermode.py    # High-risk mode
│   │       └── tcs_scoring.py      # Trade scoring
│   ├── telegram_bot/
│   │   ├── bot.py                  # Telegram interface
│   │   ├── requirements.txt        # Bot dependencies
│   │   └── .env.example           # Bot config template
│   └── bridge/
│       └── FileBridgeEA.mq5       # MT5 bridge
├── tests/
│   ├── test_core.py               # Core module tests
│   └── __init__.py
├── docs/
│   ├── bitten/                    # BITTEN bot documentation
│   ├── development.md             # This file
│   └── api.md                     # API documentation
├── scripts/
│   ├── deploy_flask.sh            # Deployment script
│   └── set_telegram_webhook.sh    # Webhook setup
├── config/                        # Configuration files
├── archive/                       # Archived/legacy code
├── requirements.txt               # Main dependencies
├── requirements-dev.txt           # Development dependencies
├── .env.example                   # Environment template
└── Makefile                       # Development commands
```

## Development Commands

```bash
# Install dependencies
make install

# Setup development environment
make dev

# Run tests
make test

# Code quality
make lint
make format

# Run application
make run

# Clean build artifacts
make clean
```

## Code Style

This project uses:
- **Black** for code formatting
- **flake8** for linting
- **isort** for import sorting
- **mypy** for type checking

Run before committing:
```bash
make format
make lint
```

## Testing

### Running Tests
```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_core.py -v

# Run with coverage
pytest --cov=src tests/
```

### Writing Tests
- Place test files in `tests/` directory
- Name test files `test_*.py`
- Use pytest fixtures for common setup
- Test both success and failure cases

Example:
```python
def test_bitmode_initialization():
    from src.core.modules.bitmode import run_bitmode
    # Test logic here
```

## Adding New Features

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Implement Feature
- Add code to appropriate module in `src/`
- Add tests in `tests/`
- Update documentation

### 3. Test and Lint
```bash
make test
make lint
make format
```

### 4. Commit and Push
```bash
git add .
git commit -m "Add: your feature description"
git push origin feature/your-feature-name
```

## Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Flask
FLASK_APP=src/core/TEN_elite_commands_FULL.py
FLASK_ENV=development
FLASK_DEBUG=True

# Trading
BROKER_API_KEY=your_broker_api_key
MAX_RISK_PERCENT=2.0
```

### Adding New Configuration
1. Add to `.env.example` with description
2. Add to `config/` directory if complex
3. Document in this guide

## Database

Currently using file-based storage. Future versions will include:
- SQLite for development
- PostgreSQL for production
- Redis for caching

## API Development

### Flask API Structure
Main API in `src/core/TEN_elite_commands_FULL.py`:
- Trading endpoints
- Status monitoring
- Configuration management

### Adding New Endpoints
```python
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint():
    # Implementation here
    return jsonify({'status': 'success'})
```

## Deployment

### Development
```bash
make run
# Or: FLASK_APP=src/core/TEN_elite_commands_FULL.py flask run --debug
```

### Production
```bash
make deploy
# Or: bash deploy_flask.sh
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Check Python path and virtual environment
2. **Missing Dependencies**: Run `make install`
3. **Test Failures**: Check test configuration and dependencies
4. **Flask Not Starting**: Verify FLASK_APP environment variable

### Getting Help
- Check existing issues on GitHub
- Review documentation in `docs/`
- Ask in project discussions

## Contributing Guidelines

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Use meaningful commit messages
5. Keep pull requests focused

## Future Improvements

- [ ] Add Docker support
- [ ] Implement CI/CD pipeline
- [ ] Add database migrations
- [ ] Create admin dashboard
- [ ] Add real-time monitoring
- [ ] Implement backtesting framework