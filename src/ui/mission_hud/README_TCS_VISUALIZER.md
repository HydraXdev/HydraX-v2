# TCS Visualizer Module

## Overview

The TCS (Trading Compliance Score) Visualizer is a comprehensive, modular JavaScript component designed for HydraX v2's mission HUD interface. It provides real-time visualization of trading compliance scores with predictive analytics, visual warnings, and smooth animations.

## Features

### Core Features
- **Real-time Score Display**: Animated circular progress ring with current score
- **Predictive Scoring**: Preview how trades will affect TCS before execution
- **Tier System**: Visual representation of score tiers (Excellent, Good, Warning, Critical, Danger)
- **Visual Warnings**: Automatic alerts when approaching or crossing tier thresholds
- **Score History**: Optional chart showing score trends over time
- **Smooth Animations**: Cubic easing animations for all score changes

### Visual Components
1. **Circular Progress Ring**: Main score display with color-coded tiers
2. **Tier Breakdown**: Visual representation of all score tiers with active highlighting
3. **Predictive Overlay**: Dashed ring showing predicted score after trade
4. **Warning System**: Contextual warnings for tier boundary crossings
5. **History Chart**: Canvas-based trend visualization

## Installation

```javascript
// Include the script
<script src="tcs_visualizer.js"></script>

// Or as a module
const TCSVisualizer = require('./tcs_visualizer.js');
```

## Basic Usage

```javascript
// Initialize the visualizer
const tcsViz = new TCSVisualizer('container-id', {
    currentScore: 100,
    maxScore: 100,
    animationDuration: 1000,
    showPredictive: true,
    showHistory: true
});

// Update score
tcsViz.updateScore(85); // Animated by default
tcsViz.updateScore(85, false); // Without animation

// Show predictive score
tcsViz.showPredictiveScore(75, {
    tradeType: 'sell',
    volume: 1000
});

// Hide predictive score
tcsViz.hidePredictiveScore();
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `currentScore` | Number | 100 | Initial TCS value |
| `maxScore` | Number | 100 | Maximum possible score |
| `animationDuration` | Number | 1000 | Animation duration in milliseconds |
| `updateInterval` | Number | 100 | Update frequency for animations |
| `showPredictive` | Boolean | true | Enable predictive score display |
| `showHistory` | Boolean | true | Show score history chart |
| `historySize` | Number | 20 | Number of historical points to maintain |

## API Methods

### Core Methods

#### `updateScore(newScore, animated = true)`
Updates the current TCS with optional animation.

```javascript
tcsViz.updateScore(85); // Animated update
tcsViz.updateScore(85, false); // Instant update
```

#### `showPredictiveScore(predictedScore, tradeDetails = {})`
Displays predicted score impact for a potential trade.

```javascript
tcsViz.showPredictiveScore(75, {
    tradeType: 'sell',
    volume: 1000,
    asset: 'BTC'
});
```

#### `hidePredictiveScore()`
Hides the predictive score display.

#### `showWarning(message, critical = false)`
Displays a warning message with optional critical styling.

```javascript
tcsViz.showWarning('Approaching critical tier', false);
tcsViz.showWarning('Score below minimum threshold!', true);
```

### Event Handling

#### `on(event, callback)`
Attaches an event listener.

```javascript
tcsViz.on('scoreChanged', (data) => {
    console.log(`Score: ${data.oldScore} → ${data.newScore}`);
});
```

#### `off(event, callback)`
Removes an event listener.

### Utility Methods

#### `getState()`
Returns current visualizer state.

```javascript
const state = tcsViz.getState();
// Returns: { currentScore, targetScore, predictedScore, tier, history }
```

#### `setConfig(config)`
Updates configuration at runtime.

```javascript
tcsViz.setConfig({ animationDuration: 2000 });
```

#### `destroy()`
Cleans up and removes the visualizer.

## Events

| Event | Data | Description |
|-------|------|-------------|
| `scoreChanged` | `{ oldScore, newScore, tier }` | Fired when score changes |
| `tierChanged` | `{ from, to, improving, message }` | Fired when crossing tier boundaries |
| `predictiveScore` | `{ current, predicted, change, tradeDetails }` | Fired when showing predictive score |
| `detailsRequested` | `{ score }` | Fired when details button clicked |
| `historyToggled` | `{ showing }` | Fired when history visibility changes |

## Tier System

The visualizer uses a 5-tier system:

1. **Excellent** (90-100): Green (#00ff88)
2. **Good** (75-89): Yellow-Green (#88ff00)
3. **Warning** (60-74): Orange (#ffaa00)
4. **Critical** (40-59): Dark Orange (#ff6600)
5. **Danger** (0-39): Red (#ff0044)

## Integration Example

```javascript
// Mission HUD Integration
class MissionHUD {
    constructor() {
        this.tcsVisualizer = new TCSVisualizer('tcs-panel', {
            currentScore: 100,
            showPredictive: true,
            showHistory: false // Save space in HUD
        });

        // Listen for score changes
        this.tcsVisualizer.on('scoreChanged', this.handleScoreChange.bind(this));
        this.tcsVisualizer.on('tierChanged', this.handleTierChange.bind(this));
    }

    // Preview trade impact
    previewTrade(tradeData) {
        const impact = this.calculateTCSImpact(tradeData);
        const currentScore = this.tcsVisualizer.getState().currentScore;
        this.tcsVisualizer.showPredictiveScore(currentScore + impact, tradeData);
    }

    // Execute trade
    executeTrade(tradeData) {
        const impact = this.calculateTCSImpact(tradeData);
        const currentScore = this.tcsVisualizer.getState().currentScore;
        this.tcsVisualizer.updateScore(currentScore + impact);
        this.tcsVisualizer.hidePredictiveScore();
    }

    handleScoreChange(data) {
        // Update other UI elements
        console.log('TCS Updated:', data);
    }

    handleTierChange(data) {
        if (!data.improving) {
            // Show additional warnings
            this.showMissionWarning(data.message);
        }
    }
}
```

## Styling Customization

The visualizer includes comprehensive CSS that can be customized:

```css
/* Override tier colors */
.tcs-tier-item[data-tier="excellent"] { color: #00ff88; }
.tcs-tier-item[data-tier="good"] { color: #88ff00; }

/* Customize animations */
.tcs-visualizer {
    --animation-duration: 1s;
    --ring-thickness: 12px;
}

/* Modify layout */
.tcs-main-display {
    flex-direction: column; /* Stack vertically */
}
```

## Performance Considerations

- Uses `requestAnimationFrame` for smooth animations
- Debounced canvas rendering for history chart
- Efficient DOM updates with minimal reflows
- Automatic cleanup of event listeners

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 11+
- Edge 79+

## Demo

A full demonstration is available in `tcs_demo.html` showing:
- Real-time score updates
- Predictive scoring simulation
- Trade impact preview
- Animation speed controls
- Event logging

## Future Enhancements

Potential additions for future versions:
1. WebSocket integration for real-time server updates
2. Multiple score tracking (different compliance metrics)
3. Export functionality for score history
4. Customizable tier configurations
5. Additional chart types for history visualization