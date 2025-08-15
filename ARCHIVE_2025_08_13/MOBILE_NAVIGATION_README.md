# HydraX Mobile Navigation System

## Overview

A comprehensive mobile-first navigation overhaul for the HydraX-v2 platform featuring gesture support, Telegram WebApp integration, and advanced accessibility features.

## Features

### 🎯 Core Navigation Features
- **Bottom Tab Navigation**: Touch-optimized tab system for core app sections
- **Swipe Gestures**: Left/right swipes for navigation history
- **Pull-to-Refresh**: Vertical pull gesture for content updates
- **One-Handed Mode**: Scaled interface for easier thumb navigation
- **Edge Gestures**: Swipe from screen edges for quick actions

### 📱 Mobile Optimization
- **Mobile-First Design**: Built specifically for mobile devices
- **Performance Optimized**: Smooth 60fps animations with hardware acceleration
- **Touch-Friendly**: 44px minimum touch targets following platform guidelines
- **Responsive Layout**: Adapts to different screen sizes and orientations
- **PWA Support**: Installable progressive web app with offline capabilities

### 🔗 Telegram WebApp Integration
- **Native Telegram Theming**: Automatic theme detection from Telegram
- **Haptic Feedback**: Uses Telegram's haptic feedback API
- **Back Button Integration**: Seamless back navigation with Telegram's back button
- **Main Button Context**: Dynamic main button for page-specific actions
- **Close Integration**: Proper app closure handling

### ♿ Accessibility Features
- **WCAG 2.1 Compliance**: Meets AA accessibility standards
- **Screen Reader Support**: Full ARIA implementation with live regions
- **Keyboard Navigation**: Complete keyboard navigation support
- **Focus Management**: Intelligent focus handling during navigation
- **High Contrast Support**: Automatic high contrast mode detection
- **Reduced Motion**: Respects user's motion preferences

### 🌙 Theme & Customization
- **Dark Mode Support**: Auto-detection with manual override
- **Theme Persistence**: User preferences saved locally
- **Telegram Theme Sync**: Matches Telegram's color scheme
- **Dynamic Theming**: CSS custom properties for easy customization

## File Structure

```
/root/HydraX-v2/
├── src/ui/mobile/
│   ├── navigation.js              # Main navigation controller
│   └── mobile_optimized.css       # Mobile-first CSS framework
├── templates/
│   └── mobile_navigation.html     # Mobile navigation template
├── webapp/static/
│   ├── manifest.json              # PWA manifest
│   └── sw.js                      # Service worker for offline support
└── src/bitten_core/
    └── webapp_router.py           # Backend integration (updated)
```

## Installation & Setup

### 1. Backend Integration

The mobile navigation is integrated into the existing HydraX webapp router:

```python
# Already added to webapp_router.py
def _handle_mobile_navigation_view(self, request: WebAppRequest) -> Dict[str, Any]:
    # Returns mobile-optimized data structure
```

### 2. Frontend Setup

Include the mobile navigation in your webapp:

```html
<!-- In your main template -->
<link rel="stylesheet" href="/src/ui/mobile/mobile_optimized.css">
<script src="/src/ui/mobile/navigation.js"></script>

<!-- Initialize navigation -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    const navigation = new HydraXMobileNavigation({
        swipeThreshold: 60,
        hapticEnabled: true,
        telegramIntegration: true
    });
});
</script>
```

### 3. Telegram WebApp Setup

Configure your Telegram bot to use the mobile interface:

```python
# In your Telegram bot code
webapp_url = "https://yourdomain.com/templates/mobile_navigation.html"
webapp_button = InlineKeyboardButton(
    text="Open HydraX",
    web_app=WebAppInfo(url=webapp_url)
)
```

## Usage

### Navigation Pages

The system includes five main navigation sections:

1. **Dashboard** (🏠)
   - Portfolio overview
   - Quick stats
   - Recent activity
   - Quick action buttons

2. **Signals** (📡)
   - Live trading signals
   - Signal filtering
   - Real-time updates
   - Copy trading options

3. **Trading** (📈)
   - Open positions
   - Risk management
   - Account balance
   - Trading tools

4. **Education** (🎓)
   - Learning paths
   - Progress tracking
   - Achievements
   - Interactive lessons

5. **Profile** (👤)
   - User information
   - Settings
   - Preferences
   - Account management

### Gesture Controls

- **Swipe Right**: Navigate back in history
- **Swipe Left**: Navigate forward or to next logical page
- **Pull Down**: Refresh current page content
- **Long Press**: Context actions (where applicable)
- **Edge Swipes**: Quick navigation between sections

### Keyboard Shortcuts

- **Alt + 1-5**: Navigate to pages (Dashboard, Signals, Trading, Education, Profile)
- **Alt + R**: Refresh current page
- **Alt + D**: Toggle dark mode
- **Alt + H**: Toggle one-handed mode
- **Arrow Keys**: Navigate between tabs
- **Tab**: Navigate focusable elements
- **Escape**: Close modals/overlays

## Configuration Options

### JavaScript Configuration

```javascript
const navigation = new HydraXMobileNavigation({
    // Gesture settings
    swipeThreshold: 60,              // Minimum swipe distance (pixels)
    swipeVelocityThreshold: 0.3,     // Minimum swipe velocity
    pullToRefreshThreshold: 80,      // Pull distance for refresh
    
    // Animation settings
    animationDuration: 300,          // Page transition duration (ms)
    hapticEnabled: true,             // Enable haptic feedback
    
    // Accessibility
    reducedMotion: false,            // Respect motion preferences
    
    // Performance
    usePassiveListeners: true,       // Use passive event listeners
    debounceDelay: 16,              // Event debounce delay (ms)
    
    // Telegram integration
    telegramIntegration: true        // Enable Telegram WebApp features
});
```

### CSS Custom Properties

```css
:root {
    /* Colors */
    --color-primary: #2481cc;
    --color-secondary: #34c759;
    --color-accent: #ff6b35;
    
    /* Navigation */
    --nav-height: 60px;
    --tab-height: 64px;
    --touch-target-size: 44px;
    
    /* Animation */
    --transition-fast: 150ms ease;
    --transition-base: 200ms ease;
    --transition-slow: 300ms ease;
    
    /* Safe areas (for notched devices) */
    --safe-area-inset-top: env(safe-area-inset-top, 0px);
    --safe-area-inset-bottom: env(safe-area-inset-bottom, 0px);
}
```

## API Integration

### WebApp Router Endpoint

```python
# Request mobile navigation data
request = WebAppRequest(
    user_id=user_id,
    username=username,
    view='mobile_nav',
    data={},
    timestamp=int(time.time()),
    auth_hash=auth_hash
)

response = webapp_router.route_request(request)
# Returns comprehensive mobile navigation data
```

### Event System

```javascript
// Listen for navigation events
navigation.addEventListener('pagechange', function(data) {
    console.log('Navigated to:', data.page);
    // Update content, analytics, etc.
});

navigation.addEventListener('refresh', function(data) {
    console.log('Page refreshed:', data.page);
    // Reload data for current page
});

navigation.addEventListener('action', function(data) {
    console.log('Action triggered:', data.action);
    // Handle custom actions
});
```

## Performance Optimization

### Hardware Acceleration
- CSS transforms use `transform3d()` for GPU acceleration
- `will-change` property hints for browser optimization
- Passive event listeners for better scroll performance

### Caching Strategy
- Service worker caches static assets
- Network-first strategy for API data
- Stale-while-revalidate for optimal UX

### Bundle Optimization
- Modular CSS architecture
- Tree-shakable JavaScript
- Critical CSS inlined for fast first paint

## Browser Support

### Mobile Browsers
- ✅ Safari iOS 12+
- ✅ Chrome Mobile 70+
- ✅ Firefox Mobile 68+
- ✅ Samsung Internet 10+
- ✅ Opera Mobile 50+

### Features
- ✅ Touch events
- ✅ CSS Grid/Flexbox
- ✅ CSS Custom Properties
- ✅ Service Workers
- ✅ Web App Manifest
- ✅ Intersection Observer

## Testing

### Manual Testing Checklist
- [ ] All navigation gestures work correctly
- [ ] Haptic feedback triggers appropriately
- [ ] Dark/light mode switching
- [ ] One-handed mode functionality
- [ ] Pull-to-refresh in all sections
- [ ] Keyboard navigation
- [ ] Screen reader compatibility
- [ ] Performance on slower devices

### Automated Testing
```bash
# Run mobile navigation tests
npm test src/ui/mobile/
```

## Troubleshooting

### Common Issues

**Gestures not working**
- Check touch event support: `'ontouchstart' in window`
- Verify viewport meta tag is present
- Ensure CSS `touch-action` is not preventing gestures

**Haptic feedback not working**
- Confirm device supports vibration API
- Check if running in Telegram WebApp context
- Verify user hasn't disabled haptic feedback

**Performance issues**
- Enable hardware acceleration in CSS
- Check for memory leaks in event listeners
- Reduce animation complexity on slower devices

### Debug Mode

Enable debug logging:
```javascript
window.hydraXNav.options.debug = true;
// See console for detailed navigation logs
```

## Security Considerations

### WebApp Authentication
- All requests include HMAC authentication
- User data is validated server-side
- Sensitive operations require additional verification

### Content Security Policy
```
Content-Security-Policy: 
  default-src 'self';
  script-src 'self' https://telegram.org;
  style-src 'self' 'unsafe-inline';
  connect-src 'self' wss:;
  img-src 'self' data: https:;
```

## Contributing

### Development Setup
1. Clone the repository
2. Install dependencies: `npm install`
3. Start development server: `npm run dev`
4. Open mobile navigation in browser/Telegram

### Code Style
- Follow existing naming conventions
- Use semantic HTML elements
- Include ARIA attributes for accessibility
- Add JSDoc comments for functions
- Test on multiple devices/browsers

## License

This mobile navigation system is part of the HydraX-v2 platform and follows the same licensing terms.

## Support

For technical support or questions about the mobile navigation system:
- Check the troubleshooting section above
- Review browser console for error messages
- Test on multiple devices to isolate issues
- Ensure all dependencies are properly loaded