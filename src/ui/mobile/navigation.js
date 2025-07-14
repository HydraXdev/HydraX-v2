/**
 * HydraX Mobile Navigation System
 * Gesture-based navigation with Telegram WebApp integration
 * Features: swipe gestures, haptic feedback, pull-to-refresh, accessibility
 */

class HydraXMobileNavigation {
    constructor(options = {}) {
        this.options = {
            // Gesture settings
            swipeThreshold: options.swipeThreshold || 50,
            swipeVelocityThreshold: options.swipeVelocityThreshold || 0.3,
            pullToRefreshThreshold: options.pullToRefreshThreshold || 80,
            
            // Animation settings
            animationDuration: options.animationDuration || 300,
            hapticEnabled: options.hapticEnabled !== false,
            
            // Accessibility
            reducedMotion: options.reducedMotion || window.matchMedia('(prefers-reduced-motion: reduce)').matches,
            
            // Performance
            usePassiveListeners: options.usePassiveListeners !== false,
            debounceDelay: options.debounceDelay || 16,
            
            ...options
        };
        
        // State management
        this.state = {
            currentPage: 'dashboard',
            isNavigating: false,
            isPullToRefresh: false,
            touchStartY: 0,
            touchStartX: 0,
            touchStartTime: 0,
            scrollPosition: 0,
            isOneHandedMode: false,
            isDarkMode: this.detectDarkMode(),
            isLandscape: window.innerWidth > window.innerHeight
        };
        
        // Navigation history
        this.history = ['dashboard'];
        this.historyIndex = 0;
        
        // Performance optimization
        this.raf = null;
        this.lastUpdate = 0;
        
        // Telegram WebApp integration
        this.telegramApp = window.Telegram?.WebApp;
        this.isInTelegram = !!this.telegramApp;
        
        this.init();
    }
    
    /**
     * Initialize the navigation system
     */
    init() {
        this.initializeDOM();
        this.setupEventListeners();
        this.initializeTelegramIntegration();
        this.setupAccessibility();
        this.loadUserPreferences();
        this.updateOneHandedMode();
        
        // Initialize with smooth entrance animation
        this.animateEntrance();
        
        console.log('HydraX Mobile Navigation initialized', {
            telegram: this.isInTelegram,
            darkMode: this.state.isDarkMode,
            reducedMotion: this.options.reducedMotion
        });
    }
    
    /**
     * Initialize DOM elements and structure
     */
    initializeDOM() {
        // Get or create main navigation container
        this.navContainer = document.getElementById('mobile-nav') || this.createNavigationContainer();
        
        // Get content area
        this.contentArea = document.getElementById('content-area') || document.querySelector('main');
        
        // Create navigation elements
        this.createBottomTabNavigation();
        this.createPullToRefreshIndicator();
        this.createGestureOverlays();
        this.createOneHandedToggle();
        
        // Set initial theme
        this.updateTheme(this.state.isDarkMode);
    }
    
    /**
     * Create bottom tab navigation
     */
    createBottomTabNavigation() {
        const tabsConfig = [
            { id: 'dashboard', icon: '🏠', label: 'Dashboard', vibrant: true },
            { id: 'signals', icon: '📡', label: 'Signals', priority: 'high' },
            { id: 'trading', icon: '📈', label: 'Trading', secured: true },
            { id: 'education', icon: '🎓', label: 'Education' },
            { id: 'profile', icon: '👤', label: 'Profile' }
        ];
        
        const tabNav = document.createElement('nav');
        tabNav.className = 'mobile-tab-nav';
        tabNav.setAttribute('role', 'tablist');
        tabNav.setAttribute('aria-label', 'Main navigation');
        
        tabsConfig.forEach(tab => {
            const tabButton = this.createTabButton(tab);
            tabNav.appendChild(tabButton);
        });
        
        this.navContainer.appendChild(tabNav);
        this.tabNav = tabNav;
    }
    
    /**
     * Create individual tab button with enhanced features
     */
    createTabButton(config) {
        const button = document.createElement('button');
        button.className = `tab-button ${config.priority === 'high' ? 'priority-tab' : ''}`;
        button.setAttribute('data-tab', config.id);
        button.setAttribute('role', 'tab');
        button.setAttribute('aria-controls', `${config.id}-panel`);
        button.setAttribute('aria-selected', config.id === this.state.currentPage);
        button.setAttribute('tabindex', config.id === this.state.currentPage ? '0' : '-1');
        
        // Enhanced accessibility
        button.setAttribute('aria-label', `Navigate to ${config.label}`);
        
        const iconSpan = document.createElement('span');
        iconSpan.className = 'tab-icon';
        iconSpan.setAttribute('aria-hidden', 'true');
        iconSpan.textContent = config.icon;
        
        const labelSpan = document.createElement('span');
        labelSpan.className = 'tab-label';
        labelSpan.textContent = config.label;
        
        // Add special indicators
        if (config.secured) {
            const secureIndicator = document.createElement('span');
            secureIndicator.className = 'secure-indicator';
            secureIndicator.setAttribute('aria-label', 'Secure section');
            secureIndicator.textContent = '🔒';
            button.appendChild(secureIndicator);
        }
        
        if (config.vibrant) {
            button.classList.add('vibrant-tab');
        }
        
        button.appendChild(iconSpan);
        button.appendChild(labelSpan);
        
        // Touch-optimized click handler
        this.addTouchOptimizedHandler(button, () => this.navigateToPage(config.id));
        
        return button;
    }
    
    /**
     * Create pull-to-refresh indicator
     */
    createPullToRefreshIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'pull-to-refresh-indicator';
        indicator.setAttribute('aria-live', 'polite');
        indicator.setAttribute('aria-label', 'Pull to refresh status');
        
        const spinner = document.createElement('div');
        spinner.className = 'refresh-spinner';
        
        const text = document.createElement('span');
        text.className = 'refresh-text';
        text.textContent = 'Pull to refresh';
        
        indicator.appendChild(spinner);
        indicator.appendChild(text);
        
        if (this.contentArea) {
            this.contentArea.insertBefore(indicator, this.contentArea.firstChild);
        }
        
        this.pullToRefreshIndicator = indicator;
    }
    
    /**
     * Create gesture overlay areas for edge swipes
     */
    createGestureOverlays() {
        const overlays = ['left', 'right'].map(side => {
            const overlay = document.createElement('div');
            overlay.className = `gesture-overlay gesture-overlay-${side}`;
            overlay.setAttribute('aria-hidden', 'true');
            document.body.appendChild(overlay);
            return { side, element: overlay };
        });
        
        this.gestureOverlays = overlays;
    }
    
    /**
     * Create one-handed mode toggle
     */
    createOneHandedToggle() {
        const toggle = document.createElement('button');
        toggle.className = 'one-handed-toggle';
        toggle.setAttribute('aria-label', 'Toggle one-handed mode');
        toggle.setAttribute('title', 'One-handed mode');
        toggle.innerHTML = '👋';
        
        toggle.addEventListener('click', () => this.toggleOneHandedMode());
        
        document.body.appendChild(toggle);
        this.oneHandedToggle = toggle;
    }
    
    /**
     * Setup all event listeners with performance optimization
     */
    setupEventListeners() {
        const options = this.options.usePassiveListeners ? { passive: true } : {};
        
        // Touch events for gestures
        document.addEventListener('touchstart', this.handleTouchStart.bind(this), options);
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), options);
        document.addEventListener('touchend', this.handleTouchEnd.bind(this), options);
        
        // Keyboard navigation
        document.addEventListener('keydown', this.handleKeyNavigation.bind(this));
        
        // Orientation and resize
        window.addEventListener('orientationchange', this.debounce(this.handleOrientationChange.bind(this), 100));
        window.addEventListener('resize', this.debounce(this.handleResize.bind(this), 100));
        
        // Theme detection
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addListener(this.handleThemeChange.bind(this));
            window.matchMedia('(prefers-reduced-motion: reduce)').addListener(this.handleMotionPreferenceChange.bind(this));
        }
        
        // Page visibility for performance
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
        
        // Browser back/forward navigation
        window.addEventListener('popstate', this.handlePopState.bind(this));
    }
    
    /**
     * Initialize Telegram WebApp integration
     */
    initializeTelegramIntegration() {
        if (!this.isInTelegram) return;
        
        try {
            // Configure Telegram WebApp
            this.telegramApp.ready();
            
            // Set theme based on Telegram's theme
            const telegramTheme = this.telegramApp.colorScheme;
            if (telegramTheme) {
                this.state.isDarkMode = telegramTheme === 'dark';
                this.updateTheme(this.state.isDarkMode);
            }
            
            // Handle Telegram back button
            this.telegramApp.BackButton.onClick(() => this.handleBackNavigation());
            
            // Setup main button for key actions
            this.setupTelegramMainButton();
            
            // Handle haptic feedback through Telegram
            this.telegramApp.HapticFeedback.impactOccurred('light');
            
            console.log('Telegram WebApp integration active');
        } catch (error) {
            console.warn('Telegram WebApp integration failed:', error);
        }
    }
    
    /**
     * Setup Telegram main button for contextual actions
     */
    setupTelegramMainButton() {
        if (!this.telegramApp?.MainButton) return;
        
        const updateMainButton = () => {
            const page = this.state.currentPage;
            const buttonConfig = this.getMainButtonConfig(page);
            
            if (buttonConfig) {
                this.telegramApp.MainButton.text = buttonConfig.text;
                this.telegramApp.MainButton.color = buttonConfig.color || '#2481cc';
                this.telegramApp.MainButton.onClick(buttonConfig.action);
                this.telegramApp.MainButton.show();
            } else {
                this.telegramApp.MainButton.hide();
            }
        };
        
        // Update button when page changes
        this.addEventListener('pagechange', updateMainButton);
        updateMainButton(); // Initial setup
    }
    
    /**
     * Get main button configuration for current page
     */
    getMainButtonConfig(page) {
        const configs = {
            'signals': {
                text: 'View Live Signals',
                color: '#00ff88',
                action: () => this.triggerAction('view-live-signals')
            },
            'trading': {
                text: 'Open Position',
                color: '#ff6b35',
                action: () => this.triggerAction('open-position')
            },
            'education': {
                text: 'Start Learning',
                color: '#4285f4',
                action: () => this.triggerAction('start-learning')
            }
        };
        
        return configs[page];
    }
    
    /**
     * Handle touch start events
     */
    handleTouchStart(event) {
        if (this.state.isNavigating) return;
        
        const touch = event.touches[0];
        this.state.touchStartX = touch.clientX;
        this.state.touchStartY = touch.clientY;
        this.state.touchStartTime = Date.now();
        this.state.scrollPosition = window.pageYOffset;
        
        // Check for edge gesture start
        this.checkEdgeGestureStart(touch);
    }
    
    /**
     * Handle touch move events with performance optimization
     */
    handleTouchMove(event) {
        if (this.state.isNavigating || !event.touches[0]) return;
        
        // Use RAF for smooth animations
        if (this.raf) return;
        
        this.raf = requestAnimationFrame(() => {
            this.processTouchMove(event);
            this.raf = null;
        });
    }
    
    /**
     * Process touch move with gesture detection
     */
    processTouchMove(event) {
        const touch = event.touches[0];
        const deltaX = touch.clientX - this.state.touchStartX;
        const deltaY = touch.clientY - this.state.touchStartY;
        const currentScrollY = window.pageYOffset;
        
        // Pull to refresh detection
        if (this.shouldHandlePullToRefresh(deltaY, currentScrollY)) {
            this.handlePullToRefreshMove(deltaY);
            event.preventDefault();
        }
        
        // Horizontal swipe detection
        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 10) {
            this.handleHorizontalSwipeMove(deltaX);
        }
        
        // Update gesture overlays
        this.updateGestureVisuals(deltaX, deltaY);
    }
    
    /**
     * Handle touch end events
     */
    handleTouchEnd(event) {
        if (this.state.isNavigating) return;
        
        const endTime = Date.now();
        const duration = endTime - this.state.touchStartTime;
        const touch = event.changedTouches[0];
        const deltaX = touch.clientX - this.state.touchStartX;
        const deltaY = touch.clientY - this.state.touchStartY;
        const velocity = Math.abs(deltaX) / duration;
        
        // Process completed gestures
        this.processCompletedGesture(deltaX, deltaY, velocity, duration);
        
        // Reset visual feedback
        this.resetGestureVisuals();
        
        // Reset state
        this.resetTouchState();
    }
    
    /**
     * Process completed gesture and trigger actions
     */
    processCompletedGesture(deltaX, deltaY, velocity, duration) {
        // Pull to refresh
        if (this.state.isPullToRefresh && deltaY > this.options.pullToRefreshThreshold) {
            this.triggerRefresh();
            return;
        }
        
        // Horizontal swipe navigation
        if (Math.abs(deltaX) > this.options.swipeThreshold && 
            velocity > this.options.swipeVelocityThreshold &&
            Math.abs(deltaX) > Math.abs(deltaY)) {
            
            if (deltaX > 0) {
                this.handleSwipeRight();
            } else {
                this.handleSwipeLeft();
            }
            return;
        }
        
        // Quick tap gestures
        if (duration < 200 && Math.abs(deltaX) < 10 && Math.abs(deltaY) < 10) {
            this.handleQuickTap(touch);
        }
    }
    
    /**
     * Handle swipe right gesture
     */
    handleSwipeRight() {
        this.performHapticFeedback('light');
        
        // Go back in navigation history
        if (this.historyIndex > 0) {
            this.historyIndex--;
            const previousPage = this.history[this.historyIndex];
            this.navigateToPage(previousPage, { direction: 'back', skipHistory: true });
        } else {
            // Show back gesture feedback even if no history
            this.showGestureFeedback('No previous page');
        }
    }
    
    /**
     * Handle swipe left gesture
     */
    handleSwipeLeft() {
        this.performHapticFeedback('light');
        
        // Go forward in navigation history
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            const nextPage = this.history[this.historyIndex];
            this.navigateToPage(nextPage, { direction: 'forward', skipHistory: true });
        } else {
            // Navigate to next logical page or show feedback
            const nextPage = this.getNextLogicalPage();
            if (nextPage) {
                this.navigateToPage(nextPage, { direction: 'forward' });
            } else {
                this.showGestureFeedback('No next page');
            }
        }
    }
    
    /**
     * Navigate to a page with enhanced animations and state management
     */
    navigateToPage(pageId, options = {}) {
        if (this.state.isNavigating || this.state.currentPage === pageId) return;
        
        this.state.isNavigating = true;
        
        const direction = options.direction || 'none';
        const skipHistory = options.skipHistory || false;
        
        // Perform haptic feedback
        this.performHapticFeedback('medium');
        
        // Update navigation history
        if (!skipHistory) {
            this.updateNavigationHistory(pageId);
        }
        
        // Update tab states
        this.updateTabStates(pageId);
        
        // Animate page transition
        this.animatePageTransition(this.state.currentPage, pageId, direction)
            .then(() => {
                this.state.currentPage = pageId;
                this.state.isNavigating = false;
                
                // Update Telegram back button
                this.updateTelegramBackButton();
                
                // Emit page change event
                this.emitEvent('pagechange', { 
                    page: pageId, 
                    direction, 
                    history: this.history 
                });
                
                // Update URL without page reload
                this.updateURL(pageId);
                
                // Focus management for accessibility
                this.manageFocusOnPageChange(pageId);
            })
            .catch(error => {
                console.error('Page navigation failed:', error);
                this.state.isNavigating = false;
            });
    }
    
    /**
     * Animate page transition with optimized performance
     */
    animatePageTransition(fromPage, toPage, direction) {
        return new Promise((resolve) => {
            if (this.options.reducedMotion) {
                // Skip animation for reduced motion preference
                this.switchPageContent(fromPage, toPage);
                resolve();
                return;
            }
            
            const duration = this.options.animationDuration;
            const fromElement = document.querySelector(`[data-page="${fromPage}"]`);
            const toElement = document.querySelector(`[data-page="${toPage}"]`);
            
            if (!fromElement || !toElement) {
                this.switchPageContent(fromPage, toPage);
                resolve();
                return;
            }
            
            // Apply animation classes
            this.applyTransitionAnimation(fromElement, toElement, direction)
                .then(() => {
                    this.switchPageContent(fromPage, toPage);
                    resolve();
                });
        });
    }
    
    /**
     * Apply transition animation with hardware acceleration
     */
    applyTransitionAnimation(fromElement, toElement, direction) {
        return new Promise((resolve) => {
            const transforms = {
                'forward': { from: 'translateX(0)', to: 'translateX(-100%)', new: 'translateX(100%)' },
                'back': { from: 'translateX(0)', to: 'translateX(100%)', new: 'translateX(-100%)' },
                'none': { from: 'opacity: 1', to: 'opacity: 0', new: 'opacity: 0' }
            };
            
            const transform = transforms[direction] || transforms.none;
            
            // Prepare new page
            toElement.style.transform = transform.new;
            toElement.style.opacity = direction === 'none' ? '0' : '1';
            toElement.classList.add('page-entering');
            
            // Animate out current page
            fromElement.style.transform = transform.to;
            if (direction === 'none') fromElement.style.opacity = '0';
            fromElement.classList.add('page-exiting');
            
            // Animate in new page
            requestAnimationFrame(() => {
                toElement.style.transform = 'translateX(0)';
                toElement.style.opacity = '1';
                
                setTimeout(() => {
                    // Cleanup
                    fromElement.classList.remove('page-exiting');
                    toElement.classList.remove('page-entering');
                    fromElement.style.transform = '';
                    fromElement.style.opacity = '';
                    toElement.style.transform = '';
                    toElement.style.opacity = '';
                    
                    resolve();
                }, this.options.animationDuration);
            });
        });
    }
    
    /**
     * Handle pull-to-refresh functionality
     */
    triggerRefresh() {
        if (this.state.isRefreshing) return;
        
        this.state.isRefreshing = true;
        this.performHapticFeedback('medium');
        
        // Update indicator
        this.pullToRefreshIndicator.classList.add('refreshing');
        this.pullToRefreshIndicator.querySelector('.refresh-text').textContent = 'Refreshing...';
        
        // Emit refresh event
        this.emitEvent('refresh', { page: this.state.currentPage });
        
        // Simulate refresh (in real app, this would trigger data reload)
        setTimeout(() => {
            this.completeRefresh();
        }, 1500);
    }
    
    /**
     * Complete refresh process
     */
    completeRefresh() {
        this.state.isRefreshing = false;
        this.state.isPullToRefresh = false;
        
        // Reset indicator
        this.pullToRefreshIndicator.classList.remove('refreshing', 'active');
        this.pullToRefreshIndicator.querySelector('.refresh-text').textContent = 'Pull to refresh';
        
        // Show completion feedback
        this.showGestureFeedback('Content refreshed');
        this.performHapticFeedback('success');
    }
    
    /**
     * Toggle one-handed mode
     */
    toggleOneHandedMode() {
        this.state.isOneHandedMode = !this.state.isOneHandedMode;
        this.updateOneHandedMode();
        this.performHapticFeedback('light');
        
        // Save preference
        localStorage.setItem('hydraX_oneHandedMode', this.state.isOneHandedMode);
        
        // Announce to screen readers
        this.announceToScreenReader(
            `One-handed mode ${this.state.isOneHandedMode ? 'enabled' : 'disabled'}`
        );
    }
    
    /**
     * Update one-handed mode styling
     */
    updateOneHandedMode() {
        document.body.classList.toggle('one-handed-mode', this.state.isOneHandedMode);
        
        if (this.oneHandedToggle) {
            this.oneHandedToggle.setAttribute('aria-pressed', this.state.isOneHandedMode);
            this.oneHandedToggle.title = this.state.isOneHandedMode ? 
                'Disable one-handed mode' : 'Enable one-handed mode';
        }
    }
    
    /**
     * Perform haptic feedback (through Telegram or vibration API)
     */
    performHapticFeedback(type = 'light') {
        if (!this.options.hapticEnabled) return;
        
        try {
            if (this.isInTelegram && this.telegramApp.HapticFeedback) {
                // Use Telegram's haptic feedback
                const feedbackMap = {
                    'light': () => this.telegramApp.HapticFeedback.impactOccurred('light'),
                    'medium': () => this.telegramApp.HapticFeedback.impactOccurred('medium'),
                    'heavy': () => this.telegramApp.HapticFeedback.impactOccurred('heavy'),
                    'success': () => this.telegramApp.HapticFeedback.notificationOccurred('success'),
                    'error': () => this.telegramApp.HapticFeedback.notificationOccurred('error')
                };
                
                if (feedbackMap[type]) {
                    feedbackMap[type]();
                }
            } else if (navigator.vibrate) {
                // Use browser vibration API
                const patterns = {
                    'light': [50],
                    'medium': [100],
                    'heavy': [200],
                    'success': [50, 50, 50],
                    'error': [200, 100, 200]
                };
                
                navigator.vibrate(patterns[type] || patterns.light);
            }
        } catch (error) {
            console.warn('Haptic feedback failed:', error);
        }
    }
    
    /**
     * Handle keyboard navigation for accessibility
     */
    handleKeyNavigation(event) {
        const { key, ctrlKey, altKey, shiftKey } = event;
        
        // Tab navigation
        if (key === 'Tab') {
            this.handleTabNavigation(event);
            return;
        }
        
        // Arrow key navigation
        if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(key)) {
            this.handleArrowNavigation(event);
            return;
        }
        
        // Escape key
        if (key === 'Escape') {
            this.handleEscapeKey(event);
            return;
        }
        
        // Number keys for quick navigation
        if (!isNaN(key) && key !== ' ') {
            this.handleNumberKeyNavigation(parseInt(key));
            return;
        }
        
        // Shortcuts
        if (ctrlKey || altKey) {
            this.handleKeyboardShortcuts(event);
        }
    }
    
    /**
     * Handle tab navigation within the navigation component
     */
    handleTabNavigation(event) {
        const focusableElements = this.getFocusableElements();
        const currentIndex = focusableElements.indexOf(document.activeElement);
        
        if (currentIndex === -1) return;
        
        let nextIndex;
        if (event.shiftKey) {
            // Shift+Tab: go backwards
            nextIndex = currentIndex === 0 ? focusableElements.length - 1 : currentIndex - 1;
        } else {
            // Tab: go forwards
            nextIndex = currentIndex === focusableElements.length - 1 ? 0 : currentIndex + 1;
        }
        
        focusableElements[nextIndex].focus();
        event.preventDefault();
    }
    
    /**
     * Setup accessibility features
     */
    setupAccessibility() {
        // Add skip links
        this.createSkipLinks();
        
        // Setup ARIA live regions
        this.createLiveRegions();
        
        // Setup focus management
        this.setupFocusManagement();
        
        // Add role descriptions
        this.addRoleDescriptions();
        
        // Setup high contrast mode detection
        this.setupHighContrastMode();
    }
    
    /**
     * Create ARIA live regions for dynamic announcements
     */
    createLiveRegions() {
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        liveRegion.id = 'live-announcements';
        
        document.body.appendChild(liveRegion);
        this.liveRegion = liveRegion;
    }
    
    /**
     * Announce message to screen readers
     */
    announceToScreenReader(message) {
        if (!this.liveRegion) return;
        
        this.liveRegion.textContent = message;
        
        // Clear after announcement
        setTimeout(() => {
            this.liveRegion.textContent = '';
        }, 1000);
    }
    
    /**
     * Dark mode detection and handling
     */
    detectDarkMode() {
        // Check Telegram theme first
        if (this.isInTelegram && this.telegramApp?.colorScheme) {
            return this.telegramApp.colorScheme === 'dark';
        }
        
        // Check system preference
        if (window.matchMedia) {
            return window.matchMedia('(prefers-color-scheme: dark)').matches;
        }
        
        // Check stored preference
        const stored = localStorage.getItem('hydraX_darkMode');
        return stored ? JSON.parse(stored) : false;
    }
    
    /**
     * Update theme
     */
    updateTheme(isDark) {
        this.state.isDarkMode = isDark;
        document.body.classList.toggle('dark-mode', isDark);
        document.body.classList.toggle('light-mode', !isDark);
        
        // Update meta theme-color
        const metaTheme = document.querySelector('meta[name="theme-color"]');
        if (metaTheme) {
            metaTheme.setAttribute('content', isDark ? '#1a1a1a' : '#ffffff');
        }
        
        // Save preference
        localStorage.setItem('hydraX_darkMode', JSON.stringify(isDark));
        
        // Emit theme change event
        this.emitEvent('themechange', { isDark });
    }
    
    /**
     * Performance optimization: debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * Add touch-optimized event handler with proper feedback
     */
    addTouchOptimizedHandler(element, handler) {
        let isActive = false;
        
        const activate = () => {
            if (isActive) return;
            isActive = true;
            element.classList.add('active');
            this.performHapticFeedback('light');
        };
        
        const deactivate = () => {
            if (!isActive) return;
            isActive = false;
            element.classList.remove('active');
        };
        
        const execute = () => {
            if (isActive) {
                handler();
                deactivate();
            }
        };
        
        // Touch events
        element.addEventListener('touchstart', activate, { passive: true });
        element.addEventListener('touchend', execute, { passive: true });
        element.addEventListener('touchcancel', deactivate, { passive: true });
        
        // Mouse events for desktop testing
        element.addEventListener('mousedown', activate);
        element.addEventListener('mouseup', execute);
        element.addEventListener('mouseleave', deactivate);
        
        // Keyboard events
        element.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                activate();
                setTimeout(execute, 100);
            }
        });
    }
    
    /**
     * Event system for component communication
     */
    addEventListener(event, handler) {
        if (!this.eventHandlers) this.eventHandlers = {};
        if (!this.eventHandlers[event]) this.eventHandlers[event] = [];
        this.eventHandlers[event].push(handler);
    }
    
    emitEvent(event, data) {
        if (!this.eventHandlers || !this.eventHandlers[event]) return;
        this.eventHandlers[event].forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error(`Event handler error for ${event}:`, error);
            }
        });
    }
    
    /**
     * Load user preferences from storage
     */
    loadUserPreferences() {
        try {
            const oneHandedMode = localStorage.getItem('hydraX_oneHandedMode');
            if (oneHandedMode !== null) {
                this.state.isOneHandedMode = JSON.parse(oneHandedMode);
            }
            
            const darkMode = localStorage.getItem('hydraX_darkMode');
            if (darkMode !== null) {
                this.state.isDarkMode = JSON.parse(darkMode);
            }
        } catch (error) {
            console.warn('Failed to load user preferences:', error);
        }
    }
    
    /**
     * Animate entrance with staggered effect
     */
    animateEntrance() {
        if (this.options.reducedMotion) return;
        
        const elements = this.navContainer.querySelectorAll('.tab-button');
        elements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                element.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
                
                setTimeout(() => {
                    element.style.transition = '';
                }, 300);
            }, index * 50);
        });
    }
    
    /**
     * Check for edge gesture start
     */
    checkEdgeGestureStart(touch) {
        const edgeThreshold = 20;
        const isLeftEdge = touch.clientX <= edgeThreshold;
        const isRightEdge = touch.clientX >= window.innerWidth - edgeThreshold;
        
        if (isLeftEdge || isRightEdge) {
            this.state.isEdgeGesture = true;
            this.state.edgeGestureSide = isLeftEdge ? 'left' : 'right';
        }
    }
    
    /**
     * Should handle pull to refresh
     */
    shouldHandlePullToRefresh(deltaY, currentScrollY) {
        return deltaY > 0 && currentScrollY === 0 && !this.state.isRefreshing;
    }
    
    /**
     * Handle pull to refresh move
     */
    handlePullToRefreshMove(deltaY) {
        this.state.isPullToRefresh = true;
        const progress = Math.min(deltaY / this.options.pullToRefreshThreshold, 1);
        
        if (this.pullToRefreshIndicator) {
            this.pullToRefreshIndicator.classList.add('active');
            this.pullToRefreshIndicator.style.transform = `translateX(-50%) translateY(${Math.min(deltaY, 100)}px)`;
            this.pullToRefreshIndicator.style.opacity = progress;
        }
    }
    
    /**
     * Handle horizontal swipe move
     */
    handleHorizontalSwipeMove(deltaX) {
        const progress = Math.abs(deltaX) / this.options.swipeThreshold;
        const side = deltaX > 0 ? 'right' : 'left';
        
        // Update gesture overlays
        this.gestureOverlays.forEach(overlay => {
            if (overlay.side === side) {
                overlay.element.classList.add('active');
                overlay.element.style.opacity = Math.min(progress, 0.5);
            } else {
                overlay.element.classList.remove('active');
            }
        });
    }
    
    /**
     * Update gesture visuals
     */
    updateGestureVisuals(deltaX, deltaY) {
        // Implementation for visual feedback during gestures
        const absX = Math.abs(deltaX);
        const absY = Math.abs(deltaY);
        
        if (absX > absY) {
            // Horizontal gesture
            this.handleHorizontalSwipeMove(deltaX);
        } else if (deltaY > 0 && this.shouldHandlePullToRefresh(deltaY, window.pageYOffset)) {
            // Vertical pull gesture
            this.handlePullToRefreshMove(deltaY);
        }
    }
    
    /**
     * Reset gesture visuals
     */
    resetGestureVisuals() {
        // Reset gesture overlays
        this.gestureOverlays.forEach(overlay => {
            overlay.element.classList.remove('active');
            overlay.element.style.opacity = '';
        });
        
        // Reset pull to refresh indicator
        if (this.pullToRefreshIndicator && !this.state.isRefreshing) {
            this.pullToRefreshIndicator.classList.remove('active');
            this.pullToRefreshIndicator.style.transform = '';
            this.pullToRefreshIndicator.style.opacity = '';
        }
    }
    
    /**
     * Reset touch state
     */
    resetTouchState() {
        this.state.touchStartX = 0;
        this.state.touchStartY = 0;
        this.state.touchStartTime = 0;
        this.state.isPullToRefresh = false;
        this.state.isEdgeGesture = false;
        this.state.edgeGestureSide = null;
    }
    
    /**
     * Handle quick tap
     */
    handleQuickTap(touch) {
        // Handle quick tap gestures for accessibility
        const element = document.elementFromPoint(touch.clientX, touch.clientY);
        if (element && element.hasAttribute('data-quick-action')) {
            const action = element.getAttribute('data-quick-action');
            this.triggerAction(action);
        }
    }
    
    /**
     * Get next logical page
     */
    getNextLogicalPage() {
        const pages = ['dashboard', 'signals', 'trading', 'education', 'profile'];
        const currentIndex = pages.indexOf(this.state.currentPage);
        return currentIndex < pages.length - 1 ? pages[currentIndex + 1] : null;
    }
    
    /**
     * Update navigation history
     */
    updateNavigationHistory(pageId) {
        // Remove any pages after current index
        this.history = this.history.slice(0, this.historyIndex + 1);
        
        // Add new page if it's different from current
        if (this.history[this.history.length - 1] !== pageId) {
            this.history.push(pageId);
            this.historyIndex = this.history.length - 1;
        }
        
        // Limit history size
        if (this.history.length > 10) {
            this.history = this.history.slice(-10);
            this.historyIndex = this.history.length - 1;
        }
    }
    
    /**
     * Update tab states
     */
    updateTabStates(activePageId) {
        if (!this.tabNav) return;
        
        const tabs = this.tabNav.querySelectorAll('.tab-button');
        tabs.forEach(tab => {
            const isActive = tab.dataset.tab === activePageId;
            tab.classList.toggle('active', isActive);
            tab.setAttribute('aria-selected', isActive);
            tab.setAttribute('tabindex', isActive ? '0' : '-1');
        });
    }
    
    /**
     * Switch page content
     */
    switchPageContent(fromPage, toPage) {
        const fromPanel = document.querySelector(`[data-page="${fromPage}"]`);
        const toPanel = document.querySelector(`[data-page="${toPage}"]`);
        
        if (fromPanel) fromPanel.style.display = 'none';
        if (toPanel) toPanel.style.display = 'block';
    }
    
    /**
     * Update Telegram back button
     */
    updateTelegramBackButton() {
        if (!this.isInTelegram || !this.telegramApp?.BackButton) return;
        
        if (this.historyIndex > 0) {
            this.telegramApp.BackButton.show();
        } else {
            this.telegramApp.BackButton.hide();
        }
    }
    
    /**
     * Update URL
     */
    updateURL(pageId) {
        if (window.history && window.history.pushState) {
            const newUrl = `${window.location.pathname}#${pageId}`;
            window.history.pushState({ page: pageId }, '', newUrl);
        }
    }
    
    /**
     * Manage focus on page change
     */
    manageFocusOnPageChange(pageId) {
        const newPanel = document.querySelector(`[data-page="${pageId}"]`);
        if (newPanel) {
            const focusTarget = newPanel.querySelector('h1, [tabindex="0"], button, input, select, textarea, a[href]');
            if (focusTarget) {
                focusTarget.focus();
            }
        }
    }
    
    /**
     * Show gesture feedback
     */
    showGestureFeedback(message) {
        this.announceToScreenReader(message);
        
        // Create visual feedback
        const feedback = document.createElement('div');
        feedback.className = 'gesture-feedback';
        feedback.textContent = message;
        feedback.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: var(--bg-glass);
            color: var(--text-primary);
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 10000;
            backdrop-filter: blur(10px);
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        document.body.appendChild(feedback);
        
        requestAnimationFrame(() => {
            feedback.style.opacity = '1';
        });
        
        setTimeout(() => {
            feedback.style.opacity = '0';
            setTimeout(() => {
                if (feedback.parentNode) {
                    feedback.parentNode.removeChild(feedback);
                }
            }, 300);
        }, 1500);
    }
    
    /**
     * Trigger action
     */
    triggerAction(action) {
        this.emitEvent('action', { action, page: this.state.currentPage });
        
        // Handle built-in actions
        switch (action) {
            case 'view-live-signals':
                this.navigateToPage('signals');
                break;
            case 'open-position':
                this.navigateToPage('trading');
                break;
            case 'start-learning':
                this.navigateToPage('education');
                break;
            default:
                console.log('Custom action triggered:', action);
        }
    }
    
    /**
     * Handle back navigation
     */
    handleBackNavigation() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            const previousPage = this.history[this.historyIndex];
            this.navigateToPage(previousPage, { direction: 'back', skipHistory: true });
        } else if (this.isInTelegram) {
            this.telegramApp.close();
        }
    }
    
    /**
     * Handle arrow navigation
     */
    handleArrowNavigation(event) {
        const { key } = event;
        const tabs = Array.from(this.tabNav.querySelectorAll('.tab-button'));
        const currentTab = tabs.find(tab => tab.classList.contains('active'));
        const currentIndex = tabs.indexOf(currentTab);
        
        let newIndex = currentIndex;
        
        if (key === 'ArrowLeft' || key === 'ArrowUp') {
            newIndex = currentIndex > 0 ? currentIndex - 1 : tabs.length - 1;
        } else if (key === 'ArrowRight' || key === 'ArrowDown') {
            newIndex = currentIndex < tabs.length - 1 ? currentIndex + 1 : 0;
        }
        
        if (newIndex !== currentIndex) {
            const newTab = tabs[newIndex];
            this.navigateToPage(newTab.dataset.tab);
            newTab.focus();
            event.preventDefault();
        }
    }
    
    /**
     * Handle escape key
     */
    handleEscapeKey(event) {
        // Close any open modals or overlays
        this.emitEvent('escape', { page: this.state.currentPage });
    }
    
    /**
     * Handle number key navigation
     */
    handleNumberKeyNavigation(number) {
        const pages = ['dashboard', 'signals', 'trading', 'education', 'profile'];
        if (number >= 1 && number <= pages.length) {
            this.navigateToPage(pages[number - 1]);
        }
    }
    
    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(event) {
        const { key, ctrlKey, altKey } = event;
        
        if (altKey) {
            switch (key) {
                case 'r':
                    this.triggerRefresh();
                    event.preventDefault();
                    break;
                case 'd':
                    this.updateTheme(!this.state.isDarkMode);
                    event.preventDefault();
                    break;
                case 'h':
                    this.toggleOneHandedMode();
                    event.preventDefault();
                    break;
            }
        }
    }
    
    /**
     * Get focusable elements
     */
    getFocusableElements() {
        return Array.from(this.navContainer.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        ));
    }
    
    /**
     * Create skip links
     */
    createSkipLinks() {
        const skipLinks = document.querySelector('.skip-links');
        if (skipLinks) {
            // Skip links already exist in template
            return;
        }
        
        const container = document.createElement('div');
        container.className = 'skip-links';
        container.innerHTML = `
            <a href="#main-content" class="sr-only sr-only-focusable">Skip to main content</a>
            <a href="#mobile-nav" class="sr-only sr-only-focusable">Skip to navigation</a>
        `;
        
        document.body.insertBefore(container, document.body.firstChild);
    }
    
    /**
     * Add role descriptions
     */
    addRoleDescriptions() {
        if (this.navContainer) {
            this.navContainer.setAttribute('aria-roledescription', 'Mobile navigation with gesture support');
        }
    }
    
    /**
     * Setup high contrast mode
     */
    setupHighContrastMode() {
        if (window.matchMedia) {
            const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
            const updateHighContrast = (e) => {
                document.body.classList.toggle('high-contrast', e.matches);
            };
            
            highContrastQuery.addListener(updateHighContrast);
            updateHighContrast(highContrastQuery);
        }
    }
    
    /**
     * Setup focus management
     */
    setupFocusManagement() {
        // Enhanced focus management for mobile
        document.addEventListener('focusin', (e) => {
            if (e.target.closest('.mobile-nav-container')) {
                document.body.classList.add('nav-focused');
            }
        });
        
        document.addEventListener('focusout', (e) => {
            setTimeout(() => {
                if (!document.activeElement?.closest('.mobile-nav-container')) {
                    document.body.classList.remove('nav-focused');
                }
            }, 100);
        });
    }
    
    /**
     * Create navigation container if not exists
     */
    createNavigationContainer() {
        const container = document.createElement('nav');
        container.id = 'mobile-nav';
        container.className = 'mobile-nav-container';
        container.setAttribute('role', 'navigation');
        container.setAttribute('aria-label', 'Main navigation');
        
        document.body.appendChild(container);
        return container;
    }
    
    /**
     * Handle orientation change
     */
    handleOrientationChange() {
        setTimeout(() => {
            this.state.isLandscape = window.innerWidth > window.innerHeight;
            this.updateOneHandedMode();
        }, 100);
    }
    
    /**
     * Handle resize
     */
    handleResize() {
        this.state.isLandscape = window.innerWidth > window.innerHeight;
        this.updateOneHandedMode();
    }
    
    /**
     * Handle theme change
     */
    handleThemeChange(e) {
        if (!localStorage.getItem('hydraX_darkMode')) {
            this.updateTheme(e.matches);
        }
    }
    
    /**
     * Handle motion preference change
     */
    handleMotionPreferenceChange(e) {
        this.options.reducedMotion = e.matches;
        document.body.classList.toggle('reduce-motion', e.matches);
    }
    
    /**
     * Handle visibility change
     */
    handleVisibilityChange() {
        if (document.hidden) {
            // Page is hidden, pause animations
            document.body.classList.add('page-hidden');
        } else {
            // Page is visible, resume animations
            document.body.classList.remove('page-hidden');
        }
    }
    
    /**
     * Handle pop state
     */
    handlePopState(event) {
        const page = event.state?.page || window.location.hash.slice(1) || 'dashboard';
        this.navigateToPage(page, { skipHistory: true });
    }
    
    /**
     * Cleanup and destroy
     */
    destroy() {
        // Remove event listeners
        document.removeEventListener('touchstart', this.handleTouchStart);
        document.removeEventListener('touchmove', this.handleTouchMove);
        document.removeEventListener('touchend', this.handleTouchEnd);
        document.removeEventListener('keydown', this.handleKeyNavigation);
        window.removeEventListener('orientationchange', this.handleOrientationChange);
        window.removeEventListener('resize', this.handleResize);
        window.removeEventListener('popstate', this.handlePopState);
        
        // Cancel pending animations
        if (this.raf) {
            cancelAnimationFrame(this.raf);
        }
        
        // Remove DOM elements
        if (this.navContainer && this.navContainer.parentNode) {
            this.navContainer.parentNode.removeChild(this.navContainer);
        }
        
        // Clear event handlers
        this.eventHandlers = {};
        
        console.log('HydraX Mobile Navigation destroyed');
    }
}

// Helper functions and utilities
class HydraXNavigationUtils {
    static isMobile() {
        return /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }
    
    static getTouchCapabilities() {
        return {
            hasTouch: 'ontouchstart' in window,
            maxTouchPoints: navigator.maxTouchPoints || 0,
            hasHover: window.matchMedia('(hover: hover)').matches
        };
    }
    
    static getDeviceInfo() {
        const ua = navigator.userAgent;
        return {
            isIOS: /iPad|iPhone|iPod/.test(ua),
            isAndroid: /Android/.test(ua),
            isSafari: /Safari/.test(ua) && !/Chrome/.test(ua),
            isChrome: /Chrome/.test(ua),
            hasNotch: window.CSS && CSS.supports('padding-top: env(safe-area-inset-top)')
        };
    }
    
    static optimizeForDevice() {
        const device = this.getDeviceInfo();
        
        // iOS-specific optimizations
        if (device.isIOS) {
            document.documentElement.style.setProperty('--ios-safe-area-top', 'env(safe-area-inset-top)');
            document.documentElement.style.setProperty('--ios-safe-area-bottom', 'env(safe-area-inset-bottom)');
        }
        
        // Android-specific optimizations
        if (device.isAndroid) {
            // Prevent zoom on input focus
            document.addEventListener('touchstart', () => {
                const viewportMeta = document.querySelector('meta[name="viewport"]');
                if (viewportMeta) {
                    viewportMeta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
                }
            });
        }
        
        return device;
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { HydraXMobileNavigation, HydraXNavigationUtils };
}

// Auto-initialize if in browser environment
if (typeof window !== 'undefined') {
    window.HydraXMobileNavigation = HydraXMobileNavigation;
    window.HydraXNavigationUtils = HydraXNavigationUtils;
    
    // Auto-initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            HydraXNavigationUtils.optimizeForDevice();
        });
    } else {
        HydraXNavigationUtils.optimizeForDevice();
    }
}