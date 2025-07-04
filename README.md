# HydraX v2: Bit by Bit Edition

HydraX is an AI-powered trading bot system built for beginners, optimized for speed and scale.

## 🚀 Features

### Trading Modes
- **Bit Mode** - Safe auto-scalping with low risk
- **Commander Mode** - High-risk compounding with tactical logic
- **Tactical Logic** - Multiple modes: Auto, Semi, Sniper, Leroy

### Integrations
- **Telegram Bot** - Real-time notifications and command interface
- **Flask API** - Web interface for monitoring and control
- **MT5 Bridge** - MetaTrader 5 integration via MQL5

### Future Features
- Myfxbook API integration
- Advanced risk management
- Backtesting framework
- Real-time analytics dashboard

## 📁 Project Structure

```
HydraX-v2/
├── src/
│   ├── core/           # Core trading logic
│   ├── telegram_bot/   # Telegram integration
│   └── bridge/         # MT5 bridge
├── tests/              # Test suites
├── docs/               # Documentation
├── scripts/            # Utility scripts
├── config/             # Configuration files
└── archive/            # Archived/legacy code
```

## 🛠️ Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/HydraXdev/HydraX-v2.git
   cd HydraX-v2
   ```

2. **Set up environment**
   ```bash
   make dev
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the application**
   ```bash
   make run
   ```

## 📖 Documentation

- [BITTEN Bot Setup](docs/bitten/) - Telegram bot configuration
- [Development Guide](docs/development.md) - Development setup and guidelines
- [API Reference](docs/api.md) - Flask API documentation
- [Deployment Guide](docs/deployment.md) - Production deployment

## 🧪 Testing

```bash
make test        # Run all tests
make lint        # Code linting
make format      # Code formatting
```

## 🔧 Configuration

Copy `.env.example` to `.env` and configure:
- Telegram bot token
- Broker API credentials
- Risk management parameters
- Database settings

## 📊 Current Status

✅ **Working Components:**
- Core trading modules
- Telegram bot integration
- Flask API endpoints
- MT5 bridge connection

🚧 **In Development:**
- Advanced risk management
- Backtesting framework
- Real-time analytics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
- Open an issue on GitHub
- Check the [documentation](docs/)
- Review the [development guide](docs/development.md)
