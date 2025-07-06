# News Event Detection and Auto-Pause Feature

## Overview

The BITTEN trading system now includes automatic news event detection and trading pause functionality. This feature monitors economic calendars for high-impact news events and automatically pauses trading to protect against volatility.

## Features

### 1. Automatic News Event Fetching
- Fetches economic calendar data from ForexFactory (or other providers)
- Updates every 30 minutes by default
- Monitors high and medium impact events
- Tracks events for all major currency pairs (USD, EUR, GBP, JPY, CHF, CAD, AUD, NZD)

### 2. Trading Auto-Pause
- Automatically pauses trading 30 minutes before high-impact news
- Resumes trading 30 minutes after the event
- Integrated with the existing risk management system
- Trading state shows as `NEWS_LOCKOUT` during blackout periods

### 3. Telegram Integration
- `/news` command shows upcoming economic events
- `/news [hours]` - Show events for next N hours (default: 24, max: 72)
- Displays current blackout status if active
- Shows event times, currencies, and impact levels

## Configuration

### Environment Variables (.env)
```bash
# News API Configuration
NEWS_API_PROVIDER=forexfactory  # Options: forexfactory, investing, fxstreet
NEWS_API_KEY=your_api_key_here   # Required for some providers
NEWS_UPDATE_INTERVAL=1800        # Update interval in seconds (30 min default)
NEWS_CACHE_DURATION=3600         # Cache duration in seconds (1 hour default)
```

### News Filter Configuration (config/trading.yml)
```yaml
news_filter:
  enabled: true
  impact_levels: ["high", "medium"]
  time_before: 30  # minutes before news
  time_after: 30   # minutes after news
  currencies: ["USD", "EUR", "GBP", "JPY"]
```

## Architecture

### Components

1. **NewsAPIClient** (`news_api_client.py`)
   - Fetches events from economic calendar APIs
   - Caches results to reduce API calls
   - Handles multiple API providers
   - Falls back to mock data if API unavailable

2. **NewsScheduler** (`news_scheduler.py`)
   - Runs periodic updates in background thread
   - Populates RiskManager with upcoming events
   - Provides status and upcoming events queries

3. **RiskManager Integration**
   - Existing `NewsEvent` class stores event data
   - `_is_news_lockout()` checks for active blackouts
   - Trading restrictions enforced in `check_trading_restrictions()`

4. **Telegram Commands**
   - `/news` command added to telegram_router.py
   - Authorized users can view upcoming events
   - Shows blackout status and event details

## Usage Examples

### Telegram Command
```
/news
📰 Economic Calendar
━━━━━━━━━━━━━━━━━━━━

🚫 TRADING PAUSED
High impact news: Non-Farm Payrolls
Currency: USD
Resume after: 13:30 UTC

📅 Upcoming Events (24h):

🔴 08 Jan 13:00 UTC
   USD - Non-Farm Payrolls
   Forecast: 160K | Prev: 199K

🟡 08 Jan 15:30 UTC
   EUR - ECB Meeting Minutes

🔴 09 Jan 09:00 UTC
   GBP - UK GDP
   Forecast: 0.2% | Prev: 0.1%

Last updated: 5 min ago
```

### API Endpoints
- `GET /news` - Get news scheduler status and upcoming events
- `GET /health` - Check webhook server health (includes news scheduler status)

## Testing

Run the test script to verify the integration:
```bash
python test_news_integration.py
```

For local testing without real API:
```bash
# Start mock API server
python mock_news_api.py

# Update .env to use local mock
NEWS_API_PROVIDER=forexfactory
# Then update config/news_api.py base_url to http://localhost:5001
```

## High Impact Events Monitored

The system specifically monitors these event types:
- Non-Farm Payrolls (NFP)
- Interest Rate Decisions
- Central Bank meetings (FOMC, ECB, BoE, BoJ)
- CPI (Consumer Price Index)
- GDP releases
- Unemployment Rate
- Retail Sales
- PMI/ISM data

## Future Enhancements

1. **Pre-event Notifications**
   - Alert users 15 minutes before high-impact news
   - Telegram push notifications

2. **Historical Volatility Analysis**
   - Track actual vs expected impact
   - Adjust buffer times based on historical data

3. **Multi-Provider Support**
   - Implement Investing.com integration
   - Add FXStreet calendar support
   - Consensus from multiple sources

4. **Advanced Filtering**
   - Filter by event type
   - User-configurable impact thresholds
   - Currency pair specific settings