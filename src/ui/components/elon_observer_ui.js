/**
 * Elon Observer UI Component
 * Displays Elon's observations and insights in the trading interface
 */

class ElonObserverUI {
    constructor(containerId = 'elon-observer-container') {
        this.container = document.getElementById(containerId);
        this.websocket = null;
        this.isMinimized = false;
        this.messageQueue = [];
        this.currentMessage = null;
        this.displayDuration = 8000; // 8 seconds per message
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error('Elon Observer container not found');
            return;
        }
        
        this.createUI();
        this.connectWebSocket();
        this.startMessageRotation();
    }
    
    createUI() {
        this.container.innerHTML = `
            <div class="elon-observer-widget ${this.isMinimized ? 'minimized' : ''}">
                <div class="elon-header">
                    <div class="elon-avatar">
                        <span class="elon-emoji">🚀</span>
                    </div>
                    <div class="elon-title">
                        <h4>Elon Observer</h4>
                        <span class="elon-status">Analyzing...</span>
                    </div>
                    <div class="elon-controls">
                        <button class="minimize-btn" onclick="elonObserver.toggleMinimize()">
                            <i class="fas fa-minus"></i>
                        </button>
                    </div>
                </div>
                <div class="elon-body">
                    <div class="elon-message">
                        <p id="elon-message-text">Initializing first-principles analysis...</p>
                    </div>
                    <div class="elon-quote">
                        <i class="fas fa-quote-left"></i>
                        <span id="elon-quote-text">Physics is the law, everything else is a recommendation</span>
                    </div>
                    <div class="elon-mood">
                        <span id="elon-mood-indicator">Mood: VISIONARY</span>
                    </div>
                </div>
            </div>
        `;
        
        this.addStyles();
    }
    
    addStyles() {
        if (document.getElementById('elon-observer-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'elon-observer-styles';
        styles.innerHTML = `
            .elon-observer-widget {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 380px;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border: 2px solid #0f4c75;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
                transition: all 0.3s ease;
                z-index: 1000;
                animation: slideIn 0.5s ease-out;
            }
            
            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            .elon-observer-widget.minimized {
                width: 200px;
                height: 60px;
                overflow: hidden;
            }
            
            .elon-observer-widget.minimized .elon-body {
                display: none;
            }
            
            .elon-header {
                display: flex;
                align-items: center;
                padding: 15px;
                border-bottom: 1px solid #0f4c75;
                background: rgba(15, 76, 117, 0.2);
                border-radius: 15px 15px 0 0;
            }
            
            .elon-avatar {
                width: 50px;
                height: 50px;
                background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 10px;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% {
                    box-shadow: 0 0 0 0 rgba(50, 130, 184, 0.7);
                }
                70% {
                    box-shadow: 0 0 0 10px rgba(50, 130, 184, 0);
                }
                100% {
                    box-shadow: 0 0 0 0 rgba(50, 130, 184, 0);
                }
            }
            
            .elon-emoji {
                font-size: 24px;
            }
            
            .elon-title h4 {
                margin: 0;
                color: #ffffff;
                font-size: 16px;
                font-weight: 600;
            }
            
            .elon-status {
                font-size: 12px;
                color: #3282b8;
                font-weight: 500;
            }
            
            .elon-controls {
                margin-left: auto;
            }
            
            .minimize-btn {
                background: none;
                border: none;
                color: #3282b8;
                cursor: pointer;
                font-size: 16px;
                padding: 5px 10px;
                transition: color 0.3s ease;
            }
            
            .minimize-btn:hover {
                color: #ffffff;
            }
            
            .elon-body {
                padding: 20px;
            }
            
            .elon-message {
                margin-bottom: 15px;
            }
            
            .elon-message p {
                margin: 0;
                color: #ffffff;
                font-size: 14px;
                line-height: 1.6;
                animation: fadeIn 0.5s ease;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            .elon-quote {
                background: rgba(50, 130, 184, 0.1);
                border-left: 3px solid #3282b8;
                padding: 10px 15px;
                margin-bottom: 15px;
                border-radius: 5px;
            }
            
            .elon-quote i {
                color: #3282b8;
                margin-right: 8px;
            }
            
            .elon-quote span {
                color: #bbbbbb;
                font-style: italic;
                font-size: 13px;
            }
            
            .elon-mood {
                text-align: center;
                padding: 8px;
                background: rgba(15, 76, 117, 0.3);
                border-radius: 20px;
            }
            
            .elon-mood span {
                color: #3282b8;
                font-size: 11px;
                text-transform: uppercase;
                font-weight: 600;
                letter-spacing: 1px;
            }
            
            /* Mood-specific styles */
            .mood-memey .elon-avatar {
                animation: bounce 1s infinite;
            }
            
            @keyframes bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-5px); }
            }
            
            .mood-caffeinated .elon-message {
                animation: shake 0.5s;
            }
            
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-5px); }
                75% { transform: translateX(5px); }
            }
            
            /* Priority indicators */
            .priority-high {
                border-color: #e74c3c;
                box-shadow: 0 10px 30px rgba(231, 76, 60, 0.3);
            }
            
            .priority-high .elon-header {
                background: rgba(231, 76, 60, 0.2);
            }
            
            /* Notification animation */
            .new-message {
                animation: glow 1s ease-in-out;
            }
            
            @keyframes glow {
                0% { box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); }
                50% { box-shadow: 0 10px 50px rgba(50, 130, 184, 0.8); }
                100% { box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); }
            }
        `;
        
        document.head.appendChild(styles);
    }
    
    connectWebSocket() {
        // Connect to observer WebSocket endpoint
        const wsUrl = `ws://${window.location.host}/ws/observer`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('Connected to Elon Observer');
                this.updateStatus('Online');
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleObserverEvent(data);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('Error');
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket connection closed');
                this.updateStatus('Offline');
                // Attempt to reconnect after 5 seconds
                setTimeout(() => this.connectWebSocket(), 5000);
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
        }
    }
    
    handleObserverEvent(event) {
        console.log('Observer event:', event);
        
        // Add to message queue
        this.messageQueue.push(event);
        
        // If high priority, show immediately
        if (event.priority >= 8) {
            this.showMessage(event);
        }
    }
    
    showMessage(event) {
        this.currentMessage = event;
        
        // Update UI elements
        const messageText = document.getElementById('elon-message-text');
        const quoteText = document.getElementById('elon-quote-text');
        const moodIndicator = document.getElementById('elon-mood-indicator');
        const widget = document.querySelector('.elon-observer-widget');
        
        if (messageText) {
            messageText.textContent = event.data.message || event.data.insight || 'Processing...';
            messageText.classList.add('new-message');
            setTimeout(() => messageText.classList.remove('new-message'), 1000);
        }
        
        if (quoteText && event.data.quote) {
            quoteText.textContent = event.data.quote;
        }
        
        if (moodIndicator && event.data.mood) {
            moodIndicator.textContent = `Mood: ${event.data.mood.toUpperCase()}`;
            // Apply mood-specific styling
            widget.className = `elon-observer-widget mood-${event.data.mood}`;
            if (this.isMinimized) widget.classList.add('minimized');
        }
        
        // Apply priority styling
        if (event.priority >= 8) {
            widget.classList.add('priority-high');
            setTimeout(() => widget.classList.remove('priority-high'), 3000);
        }
        
        // If minimized and high priority, expand temporarily
        if (this.isMinimized && event.priority >= 7) {
            this.toggleMinimize();
            setTimeout(() => {
                if (!this.isMinimized) this.toggleMinimize();
            }, this.displayDuration);
        }
        
        // Play notification sound for high priority
        if (event.priority >= 8) {
            this.playNotificationSound();
        }
    }
    
    startMessageRotation() {
        setInterval(() => {
            if (this.messageQueue.length > 0 && !this.currentMessage) {
                const nextMessage = this.messageQueue.shift();
                this.showMessage(nextMessage);
                
                // Clear current message after display duration
                setTimeout(() => {
                    this.currentMessage = null;
                }, this.displayDuration);
            }
        }, 1000); // Check every second
    }
    
    toggleMinimize() {
        this.isMinimized = !this.isMinimized;
        const widget = document.querySelector('.elon-observer-widget');
        if (widget) {
            widget.classList.toggle('minimized');
        }
    }
    
    updateStatus(status) {
        const statusElement = document.querySelector('.elon-status');
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.style.color = status === 'Online' ? '#27ae60' : '#e74c3c';
        }
    }
    
    playNotificationSound() {
        // Create and play a simple notification sound
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        gainNode.gain.value = 0.1;
        
        oscillator.start();
        oscillator.stop(audioContext.currentTime + 0.1);
    }
    
    // Public API methods
    
    sendTradeFeedback(tradeData) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'trade_completed',
                data: tradeData
            }));
        }
    }
    
    sendBehaviorNotification(behavior, context) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'trader_behavior',
                behavior: behavior,
                context: context
            }));
        }
    }
    
    requestDailyInsight() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'request_daily_insight'
            }));
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.elonObserver = new ElonObserverUI();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ElonObserverUI;
}