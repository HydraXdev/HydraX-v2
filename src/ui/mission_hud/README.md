# HydraX Mission Command Center

## Overview

The Mission HUD is the primary trading interface for HydraX v2, designed as a comprehensive mission briefing and execution platform. It replaces the previous sniper_hud as the main WebApp interface for trading operations.

## Features

### 1. Tactical Overview
- Real-time market data display
- Asset price monitoring
- Market condition meters (Volatility, Volume, Momentum)
- Time-critical mission countdown
- Entry window status tracking

### 2. Intelligence Panel
- **Analysis Tab**: Technical indicators (RSI, MACD, MA), pattern recognition, market sentiment
- **Signals Tab**: Signal strength meter, component breakdown
- **Risks Tab**: Risk matrix, critical factors assessment

### 3. Execution Controls
- Entry parameters configuration
- Risk management settings
- Multi-target profit levels
- Position sizing calculator with leverage display
- Pre-flight checklist system
- Launch control with progress tracking

### 4. TCS Integration
- Trading Channel Sync connectivity
- Auto-execute toggle
- Risk limit configuration
- Live feed display
- Settings synchronization

### 5. Mission Statistics
- Success rate tracking
- Total missions counter
- P&L performance
- Win streak monitoring

## File Structure

```
mission_hud/
├── index.html          # Main HTML structure
├── styles.css          # Comprehensive styling with dark theme
├── mission_logic.js    # Core JavaScript functionality
└── README.md          # This file
```

## Integration

### Telegram WebApp
The interface is designed to work within Telegram's WebApp framework:
- Auto-expands to full screen
- Uses Telegram theme colors
- Supports data exchange with bot

### Backend API Endpoints
Expected endpoints for full functionality:
- `/api/mission/data` - Fetch current mission/signal data
- `/api/mission/execute` - Execute trading mission
- `/api/tcs/connect` - Connect to Trading Channel Sync
- `/api/stats/user` - Fetch user statistics

## Usage

### Standalone Testing
```html
<!-- Open index.html directly in browser for development -->
<!-- Mock data will be loaded automatically -->
```

### Production Deployment
1. Integrate with Flask backend
2. Configure API endpoints
3. Set up Telegram WebApp parameters
4. Connect to real trading systems

## Customization

### Color Scheme
All colors are defined as CSS variables in `:root`:
```css
--hydra-green: #00ff88;
--hydra-red: #ff0044;
--hydra-blue: #00ccff;
--hydra-yellow: #ffcc00;
```

### Animation Speed
Adjust transition durations:
```css
--transition-fast: 0.2s ease;
--transition-normal: 0.3s ease;
--transition-slow: 0.5s ease;
```

## Security Notes

- All trading operations require pre-flight checks
- Authorization verification before execution
- Secure channel requirement for sensitive operations
- Risk limits enforced through TCS integration

## Development

### Adding New Features
1. Update HTML structure in `index.html`
2. Add styling in `styles.css`
3. Implement logic in `mission_logic.js`
4. Update state management in `MissionState` object

### Testing
- Use browser developer tools
- Check responsive design at different screen sizes
- Test with Telegram WebApp simulator
- Verify all interactive elements

## Future Enhancements

- [ ] Real-time chart integration
- [ ] Advanced order types
- [ ] Multi-asset support
- [ ] Historical performance charts
- [ ] Social trading features
- [ ] Voice command support
- [ ] AR/VR trading interface

---

Built for HydraX v2 - Advanced Trading Operations Platform