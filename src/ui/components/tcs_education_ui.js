/**
 * TCS Education UI Component
 * Provides interactive educational elements for understanding TCS scoring
 * Includes hover tooltips, progressive disclosure, and visual examples
 */

class TCSEducationUI {
    constructor(options = {}) {
        this.config = {
            userLevel: options.userLevel || 1,
            apiEndpoint: options.apiEndpoint || '/api/tcs/education',
            tooltipDelay: options.tooltipDelay || 500,
            animationDuration: options.animationDuration || 300,
            theme: options.theme || 'dark',
            ...options
        };

        this.state = {
            activeTooltips: new Map(),
            loadedContent: new Map(),
            userProgress: null,
            currentTutorial: null
        };

        this.init();
    }

    init() {
        this.injectStyles();
        this.loadUserProgress();
        this.attachGlobalListeners();
    }

    injectStyles() {
        if (document.getElementById('tcs-education-styles')) return;

        const styles = `
            /* TCS Education Info Icons */
            .tcs-info-icon {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 16px;
                height: 16px;
                margin-left: 4px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                cursor: help;
                font-size: 10px;
                color: rgba(255, 255, 255, 0.6);
                transition: all 0.2s ease;
                vertical-align: middle;
                position: relative;
            }

            .tcs-info-icon:hover {
                background: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.4);
                color: rgba(255, 255, 255, 0.9);
                transform: scale(1.1);
            }

            .tcs-info-icon.pulsing {
                animation: tcs-pulse 2s infinite;
            }

            @keyframes tcs-pulse {
                0%, 100% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.4); }
                50% { box-shadow: 0 0 0 6px rgba(0, 255, 136, 0); }
            }

            /* Tooltip Container */
            .tcs-tooltip {
                position: absolute;
                z-index: 10000;
                pointer-events: none;
                opacity: 0;
                transform: translateY(10px);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }

            .tcs-tooltip.visible {
                opacity: 1;
                transform: translateY(0);
                pointer-events: auto;
            }

            .tcs-tooltip-content {
                background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1e 100%);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 16px;
                max-width: 320px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(20px);
            }

            .tcs-tooltip-arrow {
                position: absolute;
                width: 12px;
                height: 12px;
                background: #1a1a2e;
                border: 1px solid rgba(255, 255, 255, 0.1);
                transform: rotate(45deg);
            }

            .tcs-tooltip-arrow.top {
                top: -7px;
                left: 50%;
                margin-left: -6px;
                border-bottom: none;
                border-right: none;
            }

            .tcs-tooltip-arrow.bottom {
                bottom: -7px;
                left: 50%;
                margin-left: -6px;
                border-top: none;
                border-left: none;
            }

            /* Tooltip Content Styling */
            .tcs-tooltip-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 12px;
                padding-bottom: 8px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }

            .tcs-tooltip-title {
                font-size: 14px;
                font-weight: 600;
                color: #fff;
                margin: 0;
                background: linear-gradient(90deg, #00ff88, #88ff00);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }

            .tcs-tooltip-level {
                font-size: 11px;
                color: rgba(255, 255, 255, 0.5);
                background: rgba(255, 255, 255, 0.1);
                padding: 2px 8px;
                border-radius: 12px;
            }

            .tcs-tooltip-body {
                font-size: 13px;
                line-height: 1.6;
                color: rgba(255, 255, 255, 0.8);
            }

            .tcs-tooltip-mystery {
                margin-top: 12px;
                padding: 8px;
                background: rgba(138, 43, 226, 0.1);
                border: 1px solid rgba(138, 43, 226, 0.3);
                border-radius: 8px;
                font-size: 12px;
                font-style: italic;
                color: rgba(138, 43, 226, 0.9);
            }

            .tcs-tooltip-progress {
                margin-top: 12px;
                padding-top: 12px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }

            .tcs-tooltip-progress-bar {
                height: 4px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 2px;
                overflow: hidden;
                margin-top: 4px;
            }

            .tcs-tooltip-progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #00ff88, #88ff00);
                border-radius: 2px;
                transition: width 0.3s ease;
            }

            .tcs-tooltip-unlock {
                font-size: 11px;
                color: rgba(255, 255, 255, 0.5);
                margin-top: 4px;
            }

            /* Visual Examples */
            .tcs-visual-example {
                margin-top: 16px;
                padding: 12px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }

            .tcs-visual-header {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
            }

            .tcs-visual-icon {
                font-size: 20px;
            }

            .tcs-visual-label {
                font-size: 14px;
                font-weight: 600;
            }

            .tcs-visual-characteristics {
                list-style: none;
                padding: 0;
                margin: 8px 0 0 0;
            }

            .tcs-visual-characteristics li {
                font-size: 12px;
                color: rgba(255, 255, 255, 0.7);
                padding: 4px 0;
                padding-left: 16px;
                position: relative;
            }

            .tcs-visual-characteristics li:before {
                content: "▸";
                position: absolute;
                left: 0;
                color: rgba(0, 255, 136, 0.6);
            }

            /* Interactive Tutorial */
            .tcs-tutorial-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.8);
                z-index: 9999;
                display: flex;
                align-items: center;
                justify-content: center;
                opacity: 0;
                pointer-events: none;
                transition: opacity 0.3s ease;
            }

            .tcs-tutorial-overlay.active {
                opacity: 1;
                pointer-events: auto;
            }

            .tcs-tutorial-content {
                background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1e 100%);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                padding: 24px;
                max-width: 500px;
                max-height: 80vh;
                overflow-y: auto;
                position: relative;
            }

            .tcs-tutorial-close {
                position: absolute;
                top: 16px;
                right: 16px;
                width: 32px;
                height: 32px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .tcs-tutorial-close:hover {
                background: rgba(255, 255, 255, 0.2);
                transform: scale(1.1);
            }

            /* Score Breakdown Education */
            .tcs-breakdown-item {
                position: relative;
            }

            .tcs-breakdown-education {
                position: absolute;
                top: 0;
                right: 0;
                opacity: 0;
                transition: opacity 0.2s ease;
            }

            .tcs-breakdown-item:hover .tcs-breakdown-education {
                opacity: 1;
            }

            /* Achievement Unlocks */
            .tcs-achievement-popup {
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1e 100%);
                border: 1px solid rgba(0, 255, 136, 0.5);
                border-radius: 12px;
                padding: 16px;
                max-width: 300px;
                z-index: 10001;
                transform: translateX(400px);
                transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            }

            .tcs-achievement-popup.show {
                transform: translateX(0);
            }

            .tcs-achievement-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 8px;
            }

            .tcs-achievement-icon {
                font-size: 32px;
            }

            .tcs-achievement-title {
                font-size: 16px;
                font-weight: 600;
                color: #00ff88;
                margin: 0;
            }

            .tcs-achievement-description {
                font-size: 13px;
                color: rgba(255, 255, 255, 0.8);
                margin: 0;
            }

            /* Mobile Optimizations */
            @media (max-width: 768px) {
                .tcs-tooltip-content {
                    max-width: 280px;
                }

                .tcs-tutorial-content {
                    margin: 20px;
                    max-width: calc(100vw - 40px);
                }

                .tcs-achievement-popup {
                    right: 10px;
                    max-width: calc(100vw - 20px);
                }
            }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.id = 'tcs-education-styles';
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }

    /**
     * Create an info icon for a TCS element
     */
    createInfoIcon(factor, options = {}) {
        const icon = document.createElement('span');
        icon.className = 'tcs-info-icon';
        icon.innerHTML = 'i';
        icon.dataset.factor = factor;
        
        if (options.pulsing && this.config.userLevel < 10) {
            icon.classList.add('pulsing');
        }

        // Touch/click events for mobile
        icon.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showTooltip(icon, factor);
        });

        // Hover events for desktop
        let hoverTimeout;
        icon.addEventListener('mouseenter', () => {
            hoverTimeout = setTimeout(() => {
                this.showTooltip(icon, factor);
            }, this.config.tooltipDelay);
        });

        icon.addEventListener('mouseleave', () => {
            clearTimeout(hoverTimeout);
            this.hideTooltip(factor);
        });

        return icon;
    }

    /**
     * Show tooltip for a factor
     */
    async showTooltip(element, factor) {
        // Check if tooltip already exists
        if (this.state.activeTooltips.has(factor)) {
            return;
        }

        // Get or load content
        const content = await this.getEducationContent(factor);
        
        // Create tooltip
        const tooltip = this.createTooltipElement(content, factor);
        document.body.appendChild(tooltip);

        // Position tooltip
        this.positionTooltip(tooltip, element);

        // Show with animation
        requestAnimationFrame(() => {
            tooltip.classList.add('visible');
        });

        // Store reference
        this.state.activeTooltips.set(factor, tooltip);

        // Track analytics
        this.trackInteraction('tooltip_shown', { factor, userLevel: this.config.userLevel });
    }

    /**
     * Hide tooltip
     */
    hideTooltip(factor) {
        const tooltip = this.state.activeTooltips.get(factor);
        if (!tooltip) return;

        tooltip.classList.remove('visible');
        
        setTimeout(() => {
            tooltip.remove();
            this.state.activeTooltips.delete(factor);
        }, this.config.animationDuration);
    }

    /**
     * Create tooltip element
     */
    createTooltipElement(content, factor) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tcs-tooltip';
        
        const factorTitle = factor.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const levelLabel = this.getLevelLabel(this.config.userLevel);
        const progress = this.calculateProgress(this.config.userLevel, content.unlock_next_at);

        tooltip.innerHTML = `
            <div class="tcs-tooltip-content">
                <div class="tcs-tooltip-arrow top"></div>
                <div class="tcs-tooltip-header">
                    <h4 class="tcs-tooltip-title">${factorTitle}</h4>
                    <span class="tcs-tooltip-level">${levelLabel}</span>
                </div>
                <div class="tcs-tooltip-body">
                    ${content.explanation}
                </div>
                ${content.mystery_hint ? `
                    <div class="tcs-tooltip-mystery">
                        ${content.mystery_hint}
                    </div>
                ` : ''}
                ${content.unlock_next_at > this.config.userLevel ? `
                    <div class="tcs-tooltip-progress">
                        <div class="tcs-tooltip-unlock">
                            Next unlock at Level ${content.unlock_next_at}
                        </div>
                        <div class="tcs-tooltip-progress-bar">
                            <div class="tcs-tooltip-progress-fill" style="width: ${progress}%"></div>
                        </div>
                    </div>
                ` : ''}
                ${this.getVisualExample(factor, content)}
            </div>
        `;

        // Add close on click outside
        tooltip.addEventListener('click', (e) => {
            if (e.target === tooltip) {
                this.hideTooltip(factor);
            }
        });

        return tooltip;
    }

    /**
     * Get visual example HTML
     */
    getVisualExample(factor, content) {
        if (!content.visual_example || this.config.userLevel < 5) return '';

        const example = content.visual_example;
        return `
            <div class="tcs-visual-example">
                <div class="tcs-visual-header">
                    <span class="tcs-visual-icon">${example.icon}</span>
                    <span class="tcs-visual-label" style="color: ${example.color}">
                        ${example.label} Example
                    </span>
                </div>
                <div class="tcs-visual-description">
                    ${example.example}
                </div>
                ${example.characteristics ? `
                    <ul class="tcs-visual-characteristics">
                        ${example.characteristics.map(char => `<li>${char}</li>`).join('')}
                    </ul>
                ` : ''}
            </div>
        `;
    }

    /**
     * Position tooltip relative to element
     */
    positionTooltip(tooltip, element) {
        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        // Calculate optimal position
        let top = rect.bottom + 10;
        let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);

        // Adjust if going off screen
        if (left < 10) left = 10;
        if (left + tooltipRect.width > window.innerWidth - 10) {
            left = window.innerWidth - tooltipRect.width - 10;
        }

        // Flip to top if not enough space below
        if (top + tooltipRect.height > window.innerHeight - 10) {
            top = rect.top - tooltipRect.height - 10;
            tooltip.querySelector('.tcs-tooltip-arrow').classList.remove('top');
            tooltip.querySelector('.tcs-tooltip-arrow').classList.add('bottom');
        }

        tooltip.style.top = `${top}px`;
        tooltip.style.left = `${left}px`;
    }

    /**
     * Get education content from API or cache
     */
    async getEducationContent(factor) {
        const cacheKey = `${factor}_${this.config.userLevel}`;
        
        if (this.state.loadedContent.has(cacheKey)) {
            return this.state.loadedContent.get(cacheKey);
        }

        try {
            const response = await fetch(`${this.config.apiEndpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    factor: factor,
                    user_level: this.config.userLevel
                })
            });

            const data = await response.json();
            this.state.loadedContent.set(cacheKey, data);
            return data;
        } catch (error) {
            console.error('Failed to load education content:', error);
            return this.getFallbackContent(factor);
        }
    }

    /**
     * Fallback content if API fails
     */
    getFallbackContent(factor) {
        const fallbacks = {
            market_structure: {
                explanation: "Analyzes market patterns and trend quality to identify optimal trade setups.",
                mystery_hint: "The market speaks in patterns only the trained eye can see...",
                unlock_next_at: 10
            },
            momentum: {
                explanation: "Measures the strength and direction of price movement using multiple indicators.",
                mystery_hint: "Momentum reveals the invisible force driving prices...",
                unlock_next_at: 15
            },
            default: {
                explanation: "This factor contributes to the overall TCS calculation.",
                mystery_hint: "More secrets unlock as you progress...",
                unlock_next_at: 20
            }
        };

        return fallbacks[factor] || fallbacks.default;
    }

    /**
     * Add education icons to TCS display
     */
    enhanceTCSDisplay(container) {
        // Find all TCS-related elements
        const elements = container.querySelectorAll('[data-tcs-factor]');
        
        elements.forEach(element => {
            const factor = element.dataset.tcsFactor;
            if (!element.querySelector('.tcs-info-icon')) {
                const icon = this.createInfoIcon(factor, {
                    pulsing: this.shouldPulse(factor)
                });
                element.appendChild(icon);
            }
        });

        // Add to main TCS score
        const mainScore = container.querySelector('.tcs-score-container');
        if (mainScore && !mainScore.querySelector('.tcs-info-icon')) {
            const icon = this.createInfoIcon('tcs_overview', { pulsing: true });
            mainScore.appendChild(icon);
        }
    }

    /**
     * Show interactive tutorial
     */
    showTutorial(topic = 'tcs_basics') {
        const overlay = document.createElement('div');
        overlay.className = 'tcs-tutorial-overlay';
        
        const content = this.getTutorialContent(topic);
        
        overlay.innerHTML = `
            <div class="tcs-tutorial-content">
                <button class="tcs-tutorial-close">✕</button>
                <h2>${content.title}</h2>
                <div class="tcs-tutorial-body">
                    ${content.sections.map(section => `
                        <div class="tcs-tutorial-section">
                            <h3>${section.title}</h3>
                            <p>${section.content}</p>
                            ${section.interactive ? `
                                <button class="tcs-tutorial-action" data-action="${section.interactive}">
                                    Try It
                                </button>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
                <div class="tcs-tutorial-footer">
                    <button class="tcs-tutorial-prev" ${content.prev ? '' : 'disabled'}>
                        Previous
                    </button>
                    <span class="tcs-tutorial-progress">
                        ${content.current} of ${content.total}
                    </span>
                    <button class="tcs-tutorial-next" ${content.next ? '' : 'disabled'}>
                        Next
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);
        
        // Show with animation
        requestAnimationFrame(() => {
            overlay.classList.add('active');
        });

        // Event handlers
        overlay.querySelector('.tcs-tutorial-close').addEventListener('click', () => {
            this.closeTutorial(overlay);
        });

        this.state.currentTutorial = { overlay, topic };
    }

    /**
     * Close tutorial
     */
    closeTutorial(overlay) {
        overlay.classList.remove('active');
        setTimeout(() => {
            overlay.remove();
            this.state.currentTutorial = null;
        }, 300);
    }

    /**
     * Show achievement popup
     */
    showAchievement(achievement) {
        const popup = document.createElement('div');
        popup.className = 'tcs-achievement-popup';
        
        popup.innerHTML = `
            <div class="tcs-achievement-header">
                <span class="tcs-achievement-icon">🏆</span>
                <div>
                    <h4 class="tcs-achievement-title">${achievement.title}</h4>
                    <p class="tcs-achievement-description">${achievement.description}</p>
                </div>
            </div>
        `;

        document.body.appendChild(popup);

        // Show animation
        requestAnimationFrame(() => {
            popup.classList.add('show');
        });

        // Auto hide after 5 seconds
        setTimeout(() => {
            popup.classList.remove('show');
            setTimeout(() => popup.remove(), 500);
        }, 5000);
    }

    /**
     * Calculate progress percentage
     */
    calculateProgress(current, target) {
        return Math.min(100, (current / target) * 100);
    }

    /**
     * Get level label
     */
    getLevelLabel(level) {
        if (level >= 76) return 'Legend';
        if (level >= 51) return 'Master';
        if (level >= 26) return 'Trader';
        if (level >= 11) return 'Apprentice';
        return 'Novice';
    }

    /**
     * Check if icon should pulse
     */
    shouldPulse(factor) {
        // Pulse for new users on important factors
        const importantFactors = ['tcs_overview', 'market_structure', 'risk_reward'];
        return this.config.userLevel < 5 && importantFactors.includes(factor);
    }

    /**
     * Track user interactions
     */
    trackInteraction(action, data) {
        // Send to analytics
        if (window.gtag) {
            window.gtag('event', action, {
                event_category: 'TCS_Education',
                ...data
            });
        }
    }

    /**
     * Load user progress
     */
    async loadUserProgress() {
        try {
            const response = await fetch(`${this.config.apiEndpoint}/progress`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const progress = await response.json();
            this.state.userProgress = progress;
            
            // Check for new unlocks
            this.checkForUnlocks(progress);
        } catch (error) {
            console.error('Failed to load user progress:', error);
        }
    }

    /**
     * Check for new unlocks
     */
    checkForUnlocks(progress) {
        const unlocks = progress.recent_unlocks || [];
        
        unlocks.forEach(unlock => {
            this.showAchievement({
                title: 'New Unlock!',
                description: unlock.feature
            });
        });
    }

    /**
     * Get tutorial content
     */
    getTutorialContent(topic) {
        const tutorials = {
            tcs_basics: {
                title: 'Understanding TCS Basics',
                current: 1,
                total: 3,
                next: 'tcs_factors',
                prev: null,
                sections: [
                    {
                        title: 'What is TCS?',
                        content: 'Token Confidence Score (TCS) is a proprietary algorithm that analyzes 20+ market factors to score trade quality from 0-100.',
                        interactive: 'score_simulator'
                    },
                    {
                        title: 'Score Ranges',
                        content: '94+: Hammer (Elite) | 84-93: Shadow Strike | 75-83: Scalp | 65-74: Watchlist',
                        interactive: 'visual_examples'
                    }
                ]
            }
        };

        return tutorials[topic] || tutorials.tcs_basics;
    }

    /**
     * Attach global event listeners
     */
    attachGlobalListeners() {
        // Listen for TCS updates
        document.addEventListener('tcs-updated', (e) => {
            const container = e.detail.container;
            if (container) {
                this.enhanceTCSDisplay(container);
            }
        });

        // Mobile touch handling
        if ('ontouchstart' in window) {
            document.addEventListener('touchstart', (e) => {
                if (!e.target.closest('.tcs-info-icon') && !e.target.closest('.tcs-tooltip')) {
                    this.hideAllTooltips();
                }
            });
        }
    }

    /**
     * Hide all tooltips
     */
    hideAllTooltips() {
        this.state.activeTooltips.forEach((tooltip, factor) => {
            this.hideTooltip(factor);
        });
    }

    /**
     * Public API
     */
    
    setUserLevel(level) {
        this.config.userLevel = level;
        this.state.loadedContent.clear(); // Clear cache to reload with new level
    }

    destroy() {
        this.hideAllTooltips();
        this.state.loadedContent.clear();
        if (this.state.currentTutorial) {
            this.closeTutorial(this.state.currentTutorial.overlay);
        }
    }
}

// Auto-initialize if included in page
if (typeof window !== 'undefined') {
    window.TCSEducationUI = TCSEducationUI;
    
    // Auto-enhance on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.tcsEducation = new TCSEducationUI({
                userLevel: window.userLevel || 1
            });
        });
    } else {
        window.tcsEducation = new TCSEducationUI({
            userLevel: window.userLevel || 1
        });
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TCSEducationUI;
}