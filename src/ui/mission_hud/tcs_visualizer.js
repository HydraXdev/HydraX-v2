/**
 * TCS (Trading Compliance Score) Visualizer Module
 * Handles all TCS scoring visualization with real-time updates,
 * predictive scoring, visual warnings, and animated transitions
 */

class TCSVisualizer {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container with id "${containerId}" not found`);
        }

        // Configuration
        this.config = {
            currentScore: options.currentScore || 100,
            maxScore: options.maxScore || 100,
            animationDuration: options.animationDuration || 1000,
            updateInterval: options.updateInterval || 100,
            showPredictive: options.showPredictive !== false,
            showHistory: options.showHistory !== false,
            historySize: options.historySize || 20,
            ...options
        };

        // Tier thresholds
        this.tiers = {
            excellent: { min: 90, color: '#00ff88', label: 'Excellent' },
            good: { min: 75, color: '#88ff00', label: 'Good' },
            warning: { min: 60, color: '#ffaa00', label: 'Warning' },
            critical: { min: 40, color: '#ff6600', label: 'Critical' },
            danger: { min: 0, color: '#ff0044', label: 'Danger' }
        };

        // State
        this.state = {
            currentScore: this.config.currentScore,
            targetScore: this.config.currentScore,
            predictedScore: null,
            scoreHistory: [],
            animationFrame: null,
            listeners: new Map()
        };

        this.init();
    }

    init() {
        this.createDOM();
        this.attachEventListeners();
        this.updateDisplay();
        this.startRealtimeUpdates();
    }

    createDOM() {
        this.container.innerHTML = `
            <div class="tcs-visualizer">
                <div class="tcs-header">
                    <h3 class="tcs-title">Trading Compliance Score</h3>
                    <div class="tcs-tier-indicator"></div>
                </div>
                
                <div class="tcs-main-display">
                    <div class="tcs-score-container">
                        <div class="tcs-score-ring">
                            <svg class="tcs-ring-svg" viewBox="0 0 200 200">
                                <circle class="tcs-ring-background" cx="100" cy="100" r="90"/>
                                <circle class="tcs-ring-progress" cx="100" cy="100" r="90"/>
                                <circle class="tcs-ring-predicted" cx="100" cy="100" r="90"/>
                            </svg>
                            <div class="tcs-score-text">
                                <div class="tcs-score-current">100</div>
                                <div class="tcs-score-label">TCS</div>
                            </div>
                        </div>
                        
                        <div class="tcs-predictive-display" style="display: none;">
                            <div class="tcs-predictive-arrow"></div>
                            <div class="tcs-predictive-text">
                                <span class="tcs-predictive-value"></span>
                                <span class="tcs-predictive-change"></span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="tcs-details">
                        <div class="tcs-tier-breakdown">
                            <div class="tcs-tier-item" data-tier="excellent">
                                <span class="tcs-tier-range">90-100</span>
                                <span class="tcs-tier-label">Excellent</span>
                            </div>
                            <div class="tcs-tier-item" data-tier="good">
                                <span class="tcs-tier-range">75-89</span>
                                <span class="tcs-tier-label">Good</span>
                            </div>
                            <div class="tcs-tier-item" data-tier="warning">
                                <span class="tcs-tier-range">60-74</span>
                                <span class="tcs-tier-label">Warning</span>
                            </div>
                            <div class="tcs-tier-item" data-tier="critical">
                                <span class="tcs-tier-range">40-59</span>
                                <span class="tcs-tier-label">Critical</span>
                            </div>
                            <div class="tcs-tier-item" data-tier="danger">
                                <span class="tcs-tier-range">0-39</span>
                                <span class="tcs-tier-label">Danger</span>
                            </div>
                        </div>
                        
                        <div class="tcs-warnings" style="display: none;">
                            <div class="tcs-warning-icon">⚠️</div>
                            <div class="tcs-warning-text"></div>
                        </div>
                    </div>
                </div>
                
                <div class="tcs-history-chart" style="display: ${this.config.showHistory ? 'block' : 'none'};">
                    <canvas class="tcs-history-canvas"></canvas>
                </div>
                
                <div class="tcs-actions">
                    <button class="tcs-action-btn tcs-details-btn">View Details</button>
                    <button class="tcs-action-btn tcs-history-btn">Score History</button>
                </div>
            </div>
        `;

        this.elements = {
            container: this.container.querySelector('.tcs-visualizer'),
            scoreText: this.container.querySelector('.tcs-score-current'),
            tierIndicator: this.container.querySelector('.tcs-tier-indicator'),
            ringProgress: this.container.querySelector('.tcs-ring-progress'),
            ringPredicted: this.container.querySelector('.tcs-ring-predicted'),
            predictiveDisplay: this.container.querySelector('.tcs-predictive-display'),
            predictiveValue: this.container.querySelector('.tcs-predictive-value'),
            predictiveChange: this.container.querySelector('.tcs-predictive-change'),
            warnings: this.container.querySelector('.tcs-warnings'),
            warningText: this.container.querySelector('.tcs-warning-text'),
            historyCanvas: this.container.querySelector('.tcs-history-canvas'),
            tierItems: this.container.querySelectorAll('.tcs-tier-item')
        };

        this.addStyles();
        this.initializeCanvas();
    }

    addStyles() {
        if (document.getElementById('tcs-visualizer-styles')) return;

        const style = document.createElement('style');
        style.id = 'tcs-visualizer-styles';
        style.textContent = `
            .tcs-visualizer {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1e 100%);
                border: 1px solid #333;
                border-radius: 12px;
                padding: 20px;
                color: #fff;
                position: relative;
                overflow: hidden;
            }

            .tcs-visualizer::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(0,255,136,0.1) 0%, transparent 70%);
                animation: tcs-pulse 4s ease-in-out infinite;
                pointer-events: none;
            }

            @keyframes tcs-pulse {
                0%, 100% { opacity: 0.5; transform: scale(1); }
                50% { opacity: 0.8; transform: scale(1.1); }
            }

            .tcs-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }

            .tcs-title {
                margin: 0;
                font-size: 18px;
                font-weight: 600;
                background: linear-gradient(90deg, #00ff88, #88ff00);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }

            .tcs-tier-indicator {
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                background: rgba(0,255,136,0.2);
                border: 1px solid rgba(0,255,136,0.5);
                transition: all 0.3s ease;
            }

            .tcs-main-display {
                display: flex;
                gap: 30px;
                margin-bottom: 20px;
            }

            .tcs-score-container {
                position: relative;
                width: 180px;
                height: 180px;
            }

            .tcs-score-ring {
                position: relative;
                width: 100%;
                height: 100%;
            }

            .tcs-ring-svg {
                width: 100%;
                height: 100%;
                transform: rotate(-90deg);
            }

            .tcs-ring-background {
                fill: none;
                stroke: rgba(255,255,255,0.1);
                stroke-width: 12;
            }

            .tcs-ring-progress {
                fill: none;
                stroke: #00ff88;
                stroke-width: 12;
                stroke-linecap: round;
                stroke-dasharray: 565.48;
                stroke-dashoffset: 0;
                transition: stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1),
                            stroke 0.3s ease;
            }

            .tcs-ring-predicted {
                fill: none;
                stroke: rgba(255,255,255,0.3);
                stroke-width: 8;
                stroke-linecap: round;
                stroke-dasharray: 565.48;
                stroke-dashoffset: 565.48;
                stroke-dasharray: 10 5;
                opacity: 0;
                transition: all 0.5s ease;
            }

            .tcs-score-text {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
            }

            .tcs-score-current {
                font-size: 48px;
                font-weight: 700;
                line-height: 1;
                transition: all 0.3s ease;
            }

            .tcs-score-label {
                font-size: 14px;
                opacity: 0.7;
                margin-top: 5px;
            }

            .tcs-predictive-display {
                position: absolute;
                top: 20px;
                right: -10px;
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 8px;
                padding: 8px 12px;
                backdrop-filter: blur(10px);
            }

            .tcs-predictive-arrow {
                display: inline-block;
                width: 0;
                height: 0;
                border-style: solid;
                margin-right: 8px;
            }

            .tcs-predictive-arrow.up {
                border-width: 0 6px 10px 6px;
                border-color: transparent transparent #00ff88 transparent;
            }

            .tcs-predictive-arrow.down {
                border-width: 10px 6px 0 6px;
                border-color: #ff0044 transparent transparent transparent;
            }

            .tcs-details {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 20px;
            }

            .tcs-tier-breakdown {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .tcs-tier-item {
                display: flex;
                justify-content: space-between;
                padding: 8px 12px;
                border-radius: 6px;
                background: rgba(255,255,255,0.05);
                border: 1px solid transparent;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }

            .tcs-tier-item::before {
                content: '';
                position: absolute;
                left: 0;
                top: 0;
                bottom: 0;
                width: 3px;
                background: currentColor;
                transform: scaleX(0);
                transform-origin: left;
                transition: transform 0.3s ease;
            }

            .tcs-tier-item.active {
                background: rgba(255,255,255,0.1);
                border-color: currentColor;
            }

            .tcs-tier-item.active::before {
                transform: scaleX(1);
            }

            .tcs-tier-item[data-tier="excellent"] { color: #00ff88; }
            .tcs-tier-item[data-tier="good"] { color: #88ff00; }
            .tcs-tier-item[data-tier="warning"] { color: #ffaa00; }
            .tcs-tier-item[data-tier="critical"] { color: #ff6600; }
            .tcs-tier-item[data-tier="danger"] { color: #ff0044; }

            .tcs-warnings {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px;
                background: rgba(255,102,0,0.1);
                border: 1px solid rgba(255,102,0,0.5);
                border-radius: 8px;
                animation: tcs-warning-pulse 2s ease-in-out infinite;
            }

            @keyframes tcs-warning-pulse {
                0%, 100% { opacity: 0.8; }
                50% { opacity: 1; }
            }

            .tcs-warning-icon {
                font-size: 24px;
            }

            .tcs-warning-text {
                flex: 1;
                font-size: 14px;
            }

            .tcs-history-chart {
                height: 100px;
                margin-top: 20px;
                background: rgba(255,255,255,0.05);
                border-radius: 8px;
                padding: 10px;
                position: relative;
            }

            .tcs-history-canvas {
                width: 100%;
                height: 100%;
            }

            .tcs-actions {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }

            .tcs-action-btn {
                flex: 1;
                padding: 10px 16px;
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 6px;
                color: #fff;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .tcs-action-btn:hover {
                background: rgba(255,255,255,0.2);
                transform: translateY(-1px);
            }

            .tcs-score-change {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 24px;
                font-weight: 700;
                opacity: 0;
                pointer-events: none;
                animation: tcs-score-change 1s ease-out;
            }

            @keyframes tcs-score-change {
                0% {
                    opacity: 0;
                    transform: translate(-50%, -50%) scale(0.5);
                }
                50% {
                    opacity: 1;
                    transform: translate(-50%, -50%) scale(1.2);
                }
                100% {
                    opacity: 0;
                    transform: translate(-50%, -50%) translateY(-30px) scale(1);
                }
            }

            .tcs-score-change.positive { color: #00ff88; }
            .tcs-score-change.negative { color: #ff0044; }
        `;
        document.head.appendChild(style);
    }

    attachEventListeners() {
        // Details button
        const detailsBtn = this.container.querySelector('.tcs-details-btn');
        detailsBtn?.addEventListener('click', () => {
            this.emit('detailsRequested', { score: this.state.currentScore });
        });

        // History button
        const historyBtn = this.container.querySelector('.tcs-history-btn');
        historyBtn?.addEventListener('click', () => {
            this.toggleHistory();
        });

        // Tier items hover
        this.elements.tierItems.forEach(item => {
            item.addEventListener('mouseenter', () => {
                const tier = item.dataset.tier;
                this.highlightTier(tier);
            });
            item.addEventListener('mouseleave', () => {
                this.updateTierDisplay();
            });
        });
    }

    updateScore(newScore, animated = true) {
        const oldScore = this.state.currentScore;
        this.state.targetScore = Math.max(0, Math.min(this.config.maxScore, newScore));
        
        // Add to history
        this.addToHistory(this.state.targetScore);
        
        if (animated) {
            this.animateScoreChange(oldScore, this.state.targetScore);
        } else {
            this.state.currentScore = this.state.targetScore;
            this.updateDisplay();
        }

        // Check for tier changes
        this.checkTierChange(oldScore, this.state.targetScore);
        
        // Emit change event
        this.emit('scoreChanged', {
            oldScore,
            newScore: this.state.targetScore,
            tier: this.getCurrentTier()
        });
    }

    animateScoreChange(from, to) {
        const startTime = Date.now();
        const duration = this.config.animationDuration;
        const change = to - from;

        // Show change indicator
        this.showScoreChange(change);

        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function
            const easeOutCubic = 1 - Math.pow(1 - progress, 3);
            
            this.state.currentScore = from + (change * easeOutCubic);
            this.updateDisplay();
            
            if (progress < 1) {
                this.state.animationFrame = requestAnimationFrame(animate);
            } else {
                this.state.currentScore = to;
                this.updateDisplay();
            }
        };

        if (this.state.animationFrame) {
            cancelAnimationFrame(this.state.animationFrame);
        }
        
        animate();
    }

    showScoreChange(change) {
        const indicator = document.createElement('div');
        indicator.className = `tcs-score-change ${change > 0 ? 'positive' : 'negative'}`;
        indicator.textContent = `${change > 0 ? '+' : ''}${change.toFixed(1)}`;
        
        this.elements.container.appendChild(indicator);
        
        setTimeout(() => {
            indicator.remove();
        }, 1000);
    }

    showPredictiveScore(predictedScore, tradeDetails = {}) {
        if (!this.config.showPredictive) return;

        this.state.predictedScore = Math.max(0, Math.min(this.config.maxScore, predictedScore));
        const change = this.state.predictedScore - this.state.currentScore;
        
        // Update predictive display
        this.elements.predictiveDisplay.style.display = 'flex';
        this.elements.predictiveValue.textContent = this.state.predictedScore.toFixed(1);
        this.elements.predictiveChange.textContent = `(${change > 0 ? '+' : ''}${change.toFixed(1)}%)`;
        
        // Update arrow direction
        this.elements.predictiveDisplay.querySelector('.tcs-predictive-arrow').className = 
            `tcs-predictive-arrow ${change > 0 ? 'up' : 'down'}`;
        
        // Update predicted ring
        this.updatePredictedRing();
        
        // Show warnings if crossing tier boundaries
        this.checkPredictiveWarnings(this.state.currentScore, this.state.predictedScore);
        
        // Emit predictive event
        this.emit('predictiveScore', {
            current: this.state.currentScore,
            predicted: this.state.predictedScore,
            change,
            tradeDetails
        });
    }

    hidePredictiveScore() {
        this.state.predictedScore = null;
        this.elements.predictiveDisplay.style.display = 'none';
        this.elements.ringPredicted.style.opacity = '0';
        this.elements.warnings.style.display = 'none';
    }

    updateDisplay() {
        // Update score text
        this.elements.scoreText.textContent = Math.round(this.state.currentScore);
        
        // Update ring progress
        const progress = this.state.currentScore / this.config.maxScore;
        const circumference = 2 * Math.PI * 90; // radius = 90
        const offset = circumference - (progress * circumference);
        this.elements.ringProgress.style.strokeDashoffset = offset;
        
        // Update colors based on tier
        const tier = this.getCurrentTier();
        this.elements.ringProgress.style.stroke = this.tiers[tier].color;
        this.elements.scoreText.style.color = this.tiers[tier].color;
        
        // Update tier indicator
        this.elements.tierIndicator.textContent = this.tiers[tier].label;
        this.elements.tierIndicator.style.background = `${this.tiers[tier].color}20`;
        this.elements.tierIndicator.style.borderColor = `${this.tiers[tier].color}80`;
        
        // Update tier display
        this.updateTierDisplay();
        
        // Update history chart
        if (this.config.showHistory) {
            this.updateHistoryChart();
        }
    }

    updatePredictedRing() {
        if (!this.state.predictedScore) return;
        
        const progress = this.state.predictedScore / this.config.maxScore;
        const circumference = 2 * Math.PI * 90;
        const offset = circumference - (progress * circumference);
        
        this.elements.ringPredicted.style.strokeDashoffset = offset;
        this.elements.ringPredicted.style.opacity = '0.5';
        
        const tier = this.getTierForScore(this.state.predictedScore);
        this.elements.ringPredicted.style.stroke = this.tiers[tier].color;
    }

    getCurrentTier() {
        return this.getTierForScore(this.state.currentScore);
    }

    getTierForScore(score) {
        for (const [key, tier] of Object.entries(this.tiers)) {
            if (score >= tier.min) {
                return key;
            }
        }
        return 'danger';
    }

    updateTierDisplay() {
        const currentTier = this.getCurrentTier();
        
        this.elements.tierItems.forEach(item => {
            const tier = item.dataset.tier;
            if (tier === currentTier) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    highlightTier(tierName) {
        this.elements.tierItems.forEach(item => {
            if (item.dataset.tier === tierName) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    checkTierChange(oldScore, newScore) {
        const oldTier = this.getTierForScore(oldScore);
        const newTier = this.getTierForScore(newScore);
        
        if (oldTier !== newTier) {
            this.showTierChangeNotification(oldTier, newTier);
        }
    }

    showTierChangeNotification(fromTier, toTier) {
        const improving = this.tiers[toTier].min > this.tiers[fromTier].min;
        const message = improving 
            ? `Score improved to ${this.tiers[toTier].label} tier!`
            : `Warning: Score dropped to ${this.tiers[toTier].label} tier!`;
        
        // Show warning if degrading
        if (!improving) {
            this.showWarning(message);
        }
        
        this.emit('tierChanged', {
            from: fromTier,
            to: toTier,
            improving,
            message
        });
    }

    checkPredictiveWarnings(currentScore, predictedScore) {
        const currentTier = this.getTierForScore(currentScore);
        const predictedTier = this.getTierForScore(predictedScore);
        
        if (currentTier !== predictedTier) {
            const improving = this.tiers[predictedTier].min > this.tiers[currentTier].min;
            const message = improving
                ? `This trade will improve your score to ${this.tiers[predictedTier].label} tier`
                : `Warning: This trade will drop your score to ${this.tiers[predictedTier].label} tier`;
            
            this.showWarning(message, !improving);
        }
    }

    showWarning(message, critical = false) {
        this.elements.warnings.style.display = 'flex';
        this.elements.warningText.textContent = message;
        
        if (critical) {
            this.elements.warnings.style.background = 'rgba(255,0,68,0.1)';
            this.elements.warnings.style.borderColor = 'rgba(255,0,68,0.5)';
        } else {
            this.elements.warnings.style.background = 'rgba(255,102,0,0.1)';
            this.elements.warnings.style.borderColor = 'rgba(255,102,0,0.5)';
        }
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.elements.warnings.style.display = 'none';
        }, 5000);
    }

    addToHistory(score) {
        const timestamp = Date.now();
        this.state.scoreHistory.push({ score, timestamp });
        
        // Keep only recent history
        if (this.state.scoreHistory.length > this.config.historySize) {
            this.state.scoreHistory.shift();
        }
    }

    initializeCanvas() {
        if (!this.config.showHistory) return;
        
        const canvas = this.elements.historyCanvas;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * window.devicePixelRatio;
        canvas.height = rect.height * window.devicePixelRatio;
        
        const ctx = canvas.getContext('2d');
        ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        
        this.chartContext = ctx;
    }

    updateHistoryChart() {
        if (!this.chartContext || this.state.scoreHistory.length < 2) return;
        
        const ctx = this.chartContext;
        const canvas = this.elements.historyCanvas;
        const width = canvas.width / window.devicePixelRatio;
        const height = canvas.height / window.devicePixelRatio;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Calculate points
        const points = this.state.scoreHistory.map((item, index) => ({
            x: (index / (this.state.scoreHistory.length - 1)) * width,
            y: height - (item.score / this.config.maxScore) * height
        }));
        
        // Draw gradient fill
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        const currentTier = this.getCurrentTier();
        gradient.addColorStop(0, `${this.tiers[currentTier].color}40`);
        gradient.addColorStop(1, `${this.tiers[currentTier].color}00`);
        
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        
        // Draw smooth curve
        for (let i = 1; i < points.length; i++) {
            const cp1x = points[i - 1].x + (points[i].x - points[i - 1].x) / 2;
            const cp1y = points[i - 1].y;
            const cp2x = points[i - 1].x + (points[i].x - points[i - 1].x) / 2;
            const cp2y = points[i].y;
            
            ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, points[i].x, points[i].y);
        }
        
        ctx.lineTo(width, height);
        ctx.lineTo(0, height);
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();
        
        // Draw line
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        
        for (let i = 1; i < points.length; i++) {
            const cp1x = points[i - 1].x + (points[i].x - points[i - 1].x) / 2;
            const cp1y = points[i - 1].y;
            const cp2x = points[i - 1].x + (points[i].x - points[i - 1].x) / 2;
            const cp2y = points[i].y;
            
            ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, points[i].x, points[i].y);
        }
        
        ctx.strokeStyle = this.tiers[currentTier].color;
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Draw points
        points.forEach((point, index) => {
            if (index === points.length - 1) {
                // Highlight current point
                ctx.beginPath();
                ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
                ctx.fillStyle = this.tiers[currentTier].color;
                ctx.fill();
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 2;
                ctx.stroke();
            }
        });
    }

    toggleHistory() {
        this.config.showHistory = !this.config.showHistory;
        this.elements.historyCanvas.parentElement.style.display = 
            this.config.showHistory ? 'block' : 'none';
        
        if (this.config.showHistory) {
            this.initializeCanvas();
            this.updateHistoryChart();
        }
        
        this.emit('historyToggled', { showing: this.config.showHistory });
    }

    startRealtimeUpdates() {
        // Override this method to connect to real-time data source
        // Example: WebSocket, polling, etc.
    }

    // Event handling
    on(event, callback) {
        if (!this.state.listeners.has(event)) {
            this.state.listeners.set(event, []);
        }
        this.state.listeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.state.listeners.has(event)) {
            const callbacks = this.state.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.state.listeners.has(event)) {
            this.state.listeners.get(event).forEach(callback => {
                callback(data);
            });
        }
    }

    // Public API
    destroy() {
        if (this.state.animationFrame) {
            cancelAnimationFrame(this.state.animationFrame);
        }
        this.state.listeners.clear();
        this.container.innerHTML = '';
    }

    setConfig(config) {
        this.config = { ...this.config, ...config };
        this.updateDisplay();
    }

    getState() {
        return {
            currentScore: this.state.currentScore,
            targetScore: this.state.targetScore,
            predictedScore: this.state.predictedScore,
            tier: this.getCurrentTier(),
            history: [...this.state.scoreHistory]
        };
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TCSVisualizer;
}