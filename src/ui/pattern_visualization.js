/**
 * 📊 REAL-TIME PATTERN VISUALIZATION SYSTEM
 * Enhanced visual indicators for trading patterns and confluence analysis
 */

class PatternVisualization {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.patterns = [];
        this.confluenceLevel = 0;
        this.tcsScore = 0;
        this.marketSentiment = 'neutral';
        
        this.init();
    }
    
    init() {
        this.createVisualizationContainer();
        this.setupEventListeners();
    }
    
    createVisualizationContainer() {
        const html = `
            <div class="pattern-visualization">
                <div class="pattern-header">
                    <h3>📊 Pattern Analysis</h3>
                    <div class="live-indicator">
                        <span class="pulse-dot"></span>
                        <span>LIVE</span>
                    </div>
                </div>
                
                <!-- TCS Confidence Meter -->
                <div class="tcs-meter-container">
                    <div class="meter-label">TCS Confidence</div>
                    <div class="tcs-meter">
                        <div class="meter-background">
                            <div class="meter-fill" id="tcs-fill"></div>
                            <div class="meter-markers">
                                <span class="marker low">40</span>
                                <span class="marker med">65</span>
                                <span class="marker high">85</span>
                            </div>
                        </div>
                        <div class="tcs-value" id="tcs-value">0%</div>
                    </div>
                </div>
                
                <!-- Pattern Confluence Display -->
                <div class="confluence-display">
                    <div class="confluence-header">
                        <span>Pattern Confluence</span>
                        <span class="confluence-count" id="confluence-count">0 Patterns</span>
                    </div>
                    <div class="pattern-grid" id="pattern-grid">
                        <!-- Patterns will be dynamically added here -->
                    </div>
                </div>
                
                <!-- Market Sentiment Gauge -->
                <div class="sentiment-gauge">
                    <div class="gauge-label">Market Sentiment</div>
                    <div class="gauge-container">
                        <div class="gauge-arc" id="sentiment-arc">
                            <div class="gauge-needle" id="sentiment-needle"></div>
                            <div class="gauge-center"></div>
                        </div>
                        <div class="sentiment-labels">
                            <span class="bearish">BEARISH</span>
                            <span class="neutral">NEUTRAL</span>
                            <span class="bullish">BULLISH</span>
                        </div>
                    </div>
                </div>
                
                <!-- Real-time Pattern Detection -->
                <div class="pattern-detection">
                    <div class="detection-header">Active Patterns</div>
                    <div class="detected-patterns" id="detected-patterns">
                        <!-- Real-time patterns appear here -->
                    </div>
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
        this.injectStyles();
    }
    
    injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .pattern-visualization {
                background: rgba(10, 10, 10, 0.95);
                border: 2px solid #00ff41;
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 0 30px rgba(0, 255, 65, 0.3);
                color: white;
                font-family: 'Courier New', monospace;
            }
            
            .pattern-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 1px solid #333;
            }
            
            .pattern-header h3 {
                margin: 0;
                color: #00ff41;
                font-size: 1.2em;
            }
            
            .live-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
                color: #ff4444;
                font-weight: bold;
                font-size: 0.9em;
            }
            
            .pulse-dot {
                width: 8px;
                height: 8px;
                background: #ff4444;
                border-radius: 50%;
                animation: pulse 1.5s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.6; transform: scale(1.2); }
            }
            
            /* TCS Confidence Meter */
            .tcs-meter-container {
                margin-bottom: 25px;
            }
            
            .meter-label {
                color: #00ff41;
                font-weight: bold;
                margin-bottom: 10px;
                font-size: 1em;
            }
            
            .tcs-meter {
                position: relative;
            }
            
            .meter-background {
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 10px;
                height: 30px;
                position: relative;
                overflow: hidden;
            }
            
            .meter-fill {
                height: 100%;
                background: linear-gradient(90deg, #ff4444 0%, #ffaa00 50%, #00ff41 100%);
                border-radius: 9px;
                width: 0%;
                transition: width 0.8s ease-out;
                position: relative;
                overflow: hidden;
            }
            
            .meter-fill::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(90deg, 
                    transparent 0%, 
                    rgba(255,255,255,0.3) 50%, 
                    transparent 100%);
                animation: shimmer 2s infinite;
            }
            
            @keyframes shimmer {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
            
            .meter-markers {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0 10px;
                pointer-events: none;
            }
            
            .marker {
                font-size: 0.8em;
                color: #666;
                font-weight: bold;
            }
            
            .tcs-value {
                text-align: center;
                font-size: 1.5em;
                font-weight: bold;
                color: #00ff41;
                margin-top: 8px;
            }
            
            /* Pattern Confluence */
            .confluence-display {
                margin-bottom: 25px;
            }
            
            .confluence-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 15px;
                color: #00ff41;
                font-weight: bold;
            }
            
            .confluence-count {
                color: #ffaa00;
            }
            
            .pattern-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 10px;
            }
            
            .pattern-card {
                background: rgba(0, 255, 65, 0.1);
                border: 1px solid #00ff41;
                border-radius: 8px;
                padding: 12px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }
            
            .pattern-card.active {
                background: rgba(0, 255, 65, 0.2);
                box-shadow: 0 0 15px rgba(0, 255, 65, 0.5);
                animation: patternPulse 2s infinite;
            }
            
            @keyframes patternPulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            
            .pattern-name {
                font-size: 0.9em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .pattern-strength {
                font-size: 0.8em;
                color: #ffaa00;
            }
            
            /* Market Sentiment Gauge */
            .sentiment-gauge {
                margin-bottom: 25px;
            }
            
            .gauge-label {
                color: #00ff41;
                font-weight: bold;
                margin-bottom: 15px;
                text-align: center;
            }
            
            .gauge-container {
                position: relative;
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            
            .gauge-arc {
                width: 150px;
                height: 75px;
                border: 3px solid #333;
                border-bottom: none;
                border-radius: 150px 150px 0 0;
                position: relative;
                background: linear-gradient(90deg, #ff4444 0%, #666 50%, #00ff41 100%);
            }
            
            .gauge-needle {
                width: 2px;
                height: 60px;
                background: #fff;
                position: absolute;
                bottom: 0;
                left: 50%;
                transform-origin: bottom center;
                transform: translateX(-50%) rotate(0deg);
                transition: transform 1s ease-out;
                box-shadow: 0 0 5px rgba(255, 255, 255, 0.8);
            }
            
            .gauge-center {
                width: 12px;
                height: 12px;
                background: #fff;
                border-radius: 50%;
                position: absolute;
                bottom: -6px;
                left: 50%;
                transform: translateX(-50%);
                box-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
            }
            
            .sentiment-labels {
                display: flex;
                justify-content: space-between;
                width: 150px;
                margin-top: 10px;
                font-size: 0.8em;
            }
            
            .sentiment-labels .bearish { color: #ff4444; }
            .sentiment-labels .neutral { color: #666; }
            .sentiment-labels .bullish { color: #00ff41; }
            
            /* Real-time Pattern Detection */
            .pattern-detection {
                background: rgba(0, 0, 0, 0.5);
                border: 1px solid #333;
                border-radius: 8px;
                padding: 15px;
            }
            
            .detection-header {
                color: #00ff41;
                font-weight: bold;
                margin-bottom: 10px;
                border-bottom: 1px solid #333;
                padding-bottom: 8px;
            }
            
            .detected-patterns {
                max-height: 120px;
                overflow-y: auto;
            }
            
            .detected-pattern {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
                border-bottom: 1px solid #222;
            }
            
            .detected-pattern:last-child {
                border-bottom: none;
            }
            
            .pattern-info {
                display: flex;
                flex-direction: column;
            }
            
            .pattern-title {
                font-weight: bold;
                color: #00ff41;
                font-size: 0.9em;
            }
            
            .pattern-details {
                font-size: 0.8em;
                color: #888;
            }
            
            .pattern-status {
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.8em;
                font-weight: bold;
            }
            
            .pattern-status.forming {
                background: #ffaa00;
                color: #000;
            }
            
            .pattern-status.confirmed {
                background: #00ff41;
                color: #000;
            }
            
            .pattern-status.weak {
                background: #ff4444;
                color: #fff;
            }
            
            /* Responsive design */
            @media (max-width: 768px) {
                .pattern-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .pattern-header {
                    flex-direction: column;
                    gap: 10px;
                    text-align: center;
                }
                
                .confluence-header {
                    flex-direction: column;
                    gap: 5px;
                    text-align: center;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    updateTCSScore(score) {
        this.tcsScore = score;
        const fillElement = document.getElementById('tcs-fill');
        const valueElement = document.getElementById('tcs-value');
        
        if (fillElement && valueElement) {
            fillElement.style.width = `${score}%`;
            valueElement.textContent = `${score}%`;
            
            // Add visual effects based on score
            if (score >= 85) {
                fillElement.style.boxShadow = '0 0 20px rgba(0, 255, 65, 0.8)';
            } else if (score >= 65) {
                fillElement.style.boxShadow = '0 0 15px rgba(255, 170, 0, 0.6)';
            } else {
                fillElement.style.boxShadow = '0 0 10px rgba(255, 68, 68, 0.4)';
            }
        }
    }
    
    updatePatterns(patterns) {
        this.patterns = patterns;
        this.confluenceLevel = patterns.length;
        
        const gridElement = document.getElementById('pattern-grid');
        const countElement = document.getElementById('confluence-count');
        
        if (gridElement && countElement) {
            countElement.textContent = `${patterns.length} Pattern${patterns.length !== 1 ? 's' : ''}`;
            
            gridElement.innerHTML = patterns.map(pattern => `
                <div class="pattern-card ${pattern.active ? 'active' : ''}">
                    <div class="pattern-name">${pattern.name}</div>
                    <div class="pattern-strength">${pattern.strength}%</div>
                </div>
            `).join('');
        }
    }
    
    updateMarketSentiment(sentiment, strength = 0.5) {
        this.marketSentiment = sentiment;
        const needleElement = document.getElementById('sentiment-needle');
        
        if (needleElement) {
            // Convert sentiment to needle rotation (-90deg to +90deg)
            let rotation = 0;
            switch (sentiment) {
                case 'bullish':
                    rotation = 45 + (strength * 45); // 45 to 90 degrees
                    break;
                case 'bearish':
                    rotation = -45 - (strength * 45); // -45 to -90 degrees
                    break;
                case 'neutral':
                default:
                    rotation = -22.5 + (strength * 45); // -22.5 to +22.5 degrees
                    break;
            }
            
            needleElement.style.transform = `translateX(-50%) rotate(${rotation}deg)`;
        }
    }
    
    updateRealTimePatterns(detectedPatterns) {
        const container = document.getElementById('detected-patterns');
        
        if (container) {
            container.innerHTML = detectedPatterns.map(pattern => `
                <div class="detected-pattern">
                    <div class="pattern-info">
                        <div class="pattern-title">${pattern.name}</div>
                        <div class="pattern-details">${pattern.timeframe} • ${pattern.confidence}% confidence</div>
                    </div>
                    <div class="pattern-status ${pattern.status}">${pattern.status.toUpperCase()}</div>
                </div>
            `).join('');
        }
    }
    
    simulateRealTimeData() {
        // Simulate TCS score changes
        setInterval(() => {
            const randomTCS = 40 + Math.random() * 50; // 40-90%
            this.updateTCSScore(Math.round(randomTCS));
        }, 3000);
        
        // Simulate pattern updates
        setInterval(() => {
            const samplePatterns = [
                { name: 'Bullish Engulfing', strength: 78, active: true },
                { name: 'Support/Resistance', strength: 85, active: true },
                { name: 'Moving Average Cross', strength: 62, active: false },
                { name: 'Volume Surge', strength: 91, active: true }
            ];
            
            // Randomly select 1-4 patterns
            const selectedPatterns = samplePatterns
                .sort(() => 0.5 - Math.random())
                .slice(0, Math.floor(Math.random() * 4) + 1);
                
            this.updatePatterns(selectedPatterns);
        }, 5000);
        
        // Simulate sentiment changes
        setInterval(() => {
            const sentiments = ['bullish', 'bearish', 'neutral'];
            const randomSentiment = sentiments[Math.floor(Math.random() * sentiments.length)];
            const randomStrength = Math.random();
            this.updateMarketSentiment(randomSentiment, randomStrength);
        }, 4000);
        
        // Simulate real-time pattern detection
        setInterval(() => {
            const patterns = [
                { name: 'Double Bottom', timeframe: 'M5', confidence: 87, status: 'confirmed' },
                { name: 'Ascending Triangle', timeframe: 'M15', confidence: 73, status: 'forming' },
                { name: 'Head & Shoulders', timeframe: 'M1', confidence: 45, status: 'weak' }
            ];
            
            // Randomly select patterns
            const selected = patterns.sort(() => 0.5 - Math.random()).slice(0, 2);
            this.updateRealTimePatterns(selected);
        }, 6000);
    }
    
    setupEventListeners() {
        // Setup any click handlers or interaction events
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Pause animations when tab is hidden
                this.pauseAnimations();
            } else {
                // Resume animations when tab is visible
                this.resumeAnimations();
            }
        });
    }
    
    pauseAnimations() {
        const animatedElements = document.querySelectorAll('.pulse-dot, .meter-fill, .pattern-card.active');
        animatedElements.forEach(el => {
            el.style.animationPlayState = 'paused';
        });
    }
    
    resumeAnimations() {
        const animatedElements = document.querySelectorAll('.pulse-dot, .meter-fill, .pattern-card.active');
        animatedElements.forEach(el => {
            el.style.animationPlayState = 'running';
        });
    }
}

// Initialize pattern visualization when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if the container exists
    if (document.getElementById('pattern-visualization-container')) {
        const patternViz = new PatternVisualization('pattern-visualization-container');
        
        // Start simulation if in development mode
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            patternViz.simulateRealTimeData();
        }
        
        // Make it globally available for mission HUD integration
        window.patternVisualization = patternViz;
    }
});