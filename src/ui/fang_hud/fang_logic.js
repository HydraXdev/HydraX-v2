// FANG HUD Logic - Enhanced Tactical Interface

// Initialize Telegram WebApp
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// FANG Configuration
const FANG_CONFIG = {
    dataVisibility: 0.6, // 60% data visibility
    refreshInterval: 5000, // 5 seconds
    glitchIntensity: 'medium',
    tcsThreshold: 80,
    colors: {
        primary: '#00ccff',
        secondary: '#0099cc',
        accent: '#00ffff',
        success: '#00ff88',
        danger: '#ff0066',
        warning: '#ffaa00'
    }
};

// Global state
let currentSignal = null;
let userData = null;
let isLoading = false;
let glitchTimer = null;

// Initialize HUD
document.addEventListener('DOMContentLoaded', () => {
    initializeHUD();
    setupEventListeners();
    startGlitchEffects();
    loadUserData();
    loadSignalData();
    startAutoRefresh();
});

// Initialize HUD components
function initializeHUD() {
    updateSystemTime();
    setInterval(updateSystemTime, 1000);
    
    // Initialize Bit assistant
    updateBitMessage('System initializing... Scanning market conditions...');
    
    // Set initial states
    document.getElementById('fireButton').disabled = true;
    document.getElementById('fireButton').querySelector('.fire-text').textContent = 'AWAITING SIGNAL';
    
    // Initialize TCS scores
    animateTCSScores();
}

// Setup event listeners
function setupEventListeners() {
    // Fire button
    document.getElementById('fireButton').addEventListener('click', handleFireButton);
    
    // Footer buttons
    document.getElementById('refreshBtn').addEventListener('click', refreshData);
    document.getElementById('analyticsBtn').addEventListener('click', showAnalytics);
    document.getElementById('profileBtn').addEventListener('click', showProfile);
    document.getElementById('closeBtn').addEventListener('click', closeHUD);
    
    // Alert modal
    document.getElementById('alertClose').addEventListener('click', closeAlert);
    
    // Position calculator
    document.getElementById('accountBalance').addEventListener('input', calculatePosition);
    document.getElementById('riskPercent').addEventListener('input', calculatePosition);
}

// Glitch effects
function startGlitchEffects() {
    // Random glitch intervals
    setInterval(() => {
        if (Math.random() < 0.1) {
            triggerGlitch();
        }
    }, 3000);
    
    // Continuous subtle glitch on certain elements
    document.querySelectorAll('.glitch').forEach(element => {
        element.addEventListener('mouseenter', () => triggerElementGlitch(element));
    });
}

function triggerGlitch() {
    const overlay = document.getElementById('glitchOverlay');
    const lines = document.getElementById('glitchLines');
    
    overlay.style.opacity = '1';
    lines.style.opacity = '1';
    
    setTimeout(() => {
        overlay.style.opacity = '0';
        lines.style.opacity = '0';
    }, 200);
}

function triggerElementGlitch(element) {
    element.style.animation = 'none';
    setTimeout(() => {
        element.style.animation = 'glitch 0.5s';
    }, 10);
}

// Update system time
function updateSystemTime() {
    const now = new Date();
    const timeString = now.toTimeString().split(' ')[0];
    document.getElementById('systemTime').textContent = timeString;
}

// Load user data
async function loadUserData() {
    try {
        // Simulate API call
        userData = {
            tier: 'FANG',
            username: tg.initDataUnsafe?.user?.username || 'OPERATOR',
            userId: tg.initDataUnsafe?.user?.id || '000000',
            stats: {
                currentStreak: 7,
                bestStreak: 15,
                winRate: 68.5,
                todayPnL: 3.2,
                dayPerformance: 2.8,
                weekPerformance: 12.4,
                monthPerformance: 45.7,
                totalXP: 8500,
                rank: 'ELITE HUNTER',
                missions: 145,
                successRate: 68.5
            }
        };
        
        updateUserStats();
        updatePerformanceMetrics();
        
    } catch (error) {
        console.error('Error loading user data:', error);
        showAlert('ERROR', 'Failed to load user profile. Please refresh.');
    }
}

// Update user statistics
function updateUserStats() {
    if (!userData) return;
    
    const stats = userData.stats;
    
    // Header stats
    document.getElementById('currentStreak').textContent = stats.currentStreak;
    document.getElementById('winRate').textContent = `${stats.winRate}%`;
    document.getElementById('todayPnL').textContent = stats.todayPnL > 0 ? `+${stats.todayPnL}%` : `${stats.todayPnL}%`;
    
    // Color code P&L
    const pnlElement = document.getElementById('todayPnL');
    pnlElement.style.color = stats.todayPnL > 0 ? FANG_CONFIG.colors.success : FANG_CONFIG.colors.danger;
    
    // Show fire emoji for streaks > 5
    document.getElementById('streakFire').style.display = stats.currentStreak > 5 ? 'inline' : 'none';
}

// Update performance metrics
function updatePerformanceMetrics() {
    if (!userData) return;
    
    const stats = userData.stats;
    
    // Performance cards
    updatePerformanceCard('dayPerformance', stats.dayPerformance);
    updatePerformanceCard('weekPerformance', stats.weekPerformance);
    updatePerformanceCard('monthPerformance', stats.monthPerformance);
    document.getElementById('bestStreak').textContent = stats.bestStreak;
}

function updatePerformanceCard(elementId, value) {
    const element = document.getElementById(elementId);
    element.textContent = value > 0 ? `+${value}%` : `${value}%`;
    element.className = value > 0 ? 'perf-value positive' : 'perf-value negative';
}

// Load signal data
async function loadSignalData() {
    try {
        isLoading = true;
        updateBitMessage('Analyzing incoming signals...');
        
        // Simulate API call with FANG-tier data
        currentSignal = {
            id: `SIG-FANG-${Math.random().toString(36).substr(2, 5).toUpperCase()}`,
            symbol: 'BTC/USDT',
            direction: 'LONG',
            currentPrice: 43250.50,
            priceChange: 2.3,
            tcs: {
                trend: 85,
                confidence: 92,
                sentiment: 78,
                composite: 85.0
            },
            entry: {
                price: 43200,
                range: [43150, 43250]
            },
            stopLoss: 42800,
            takeProfits: [
                { level: 1, price: 43600, percent: 0.93 },
                { level: 2, price: 44000, percent: 1.85 },
                { level: 3, price: 44500, percent: 3.01 }
            ],
            riskRatio: '1:3.2',
            winProbability: 72,
            strategy: 'MOMENTUM BREAKOUT',
            timeframe: '4H',
            expiry: Date.now() + 3600000, // 1 hour
            confidence: 85,
            strength: 78,
            marketConditions: {
                volatility: { level: 'MODERATE', value: 55 },
                trend: { level: 'STRONG', value: 75 },
                momentum: { level: 'BULLISH', value: 65 },
                volume: { level: 'ABOVE AVG', value: 80 }
            },
            indicators: [
                { name: 'RSI', value: 65, signal: 'BUY' },
                { name: 'MACD', value: 'BULLISH', signal: 'BUY' },
                { name: 'EMA Cross', value: 'GOLDEN', signal: 'BUY' },
                { name: 'Volume', value: 'INCREASING', signal: 'BUY' }
            ],
            context: [
                'Breaking key resistance at 43,000',
                'Volume surge confirms breakout',
                'Momentum indicators aligned',
                'Market structure favors longs'
            ]
        };
        
        updateSignalDisplay();
        updateMarketConditions();
        updateTechnicalIndicators();
        validateSignal();
        
    } catch (error) {
        console.error('Error loading signal:', error);
        showAlert('ERROR', 'Failed to load signal data. Please refresh.');
    } finally {
        isLoading = false;
    }
}

// Update signal display
function updateSignalDisplay() {
    if (!currentSignal) return;
    
    // Signal header
    document.getElementById('signalId').textContent = currentSignal.id;
    
    // Asset info
    document.getElementById('symbol').textContent = currentSignal.symbol;
    document.getElementById('direction').textContent = currentSignal.direction;
    document.getElementById('direction').className = `direction ${currentSignal.direction.toLowerCase()}`;
    document.getElementById('currentPrice').textContent = currentSignal.currentPrice.toFixed(2);
    document.getElementById('priceChange').textContent = currentSignal.priceChange > 0 ? 
        `+${currentSignal.priceChange}%` : `${currentSignal.priceChange}%`;
    document.getElementById('priceChange').className = currentSignal.priceChange > 0 ? 
        'price-change positive' : 'price-change negative';
    
    // TCS Scores
    animateTCSScore('trendScore', currentSignal.tcs.trend);
    animateTCSScore('confidenceScore', currentSignal.tcs.confidence);
    animateTCSScore('sentimentScore', currentSignal.tcs.sentiment);
    animateTCSScore('compositeScore', currentSignal.tcs.composite);
    
    // Signal strength
    updateSignalStrength(currentSignal.strength);
    
    // Trade parameters
    document.getElementById('entryPrice').textContent = currentSignal.entry.price.toFixed(2);
    document.getElementById('entryRange').textContent = 
        `${currentSignal.entry.range[0].toFixed(2)} - ${currentSignal.entry.range[1].toFixed(2)}`;
    document.getElementById('stopLoss').textContent = currentSignal.stopLoss.toFixed(2);
    
    // Risk calculation
    const riskPercent = ((currentSignal.entry.price - currentSignal.stopLoss) / currentSignal.entry.price * 100).toFixed(2);
    document.getElementById('riskPercent').textContent = `-${riskPercent}%`;
    
    // Take profit levels
    currentSignal.takeProfits.forEach((tp, index) => {
        document.getElementById(`tp${index + 1}`).textContent = tp.price.toFixed(2);
        document.querySelector(`#tp${index + 1}`).parentElement.querySelector('.tp-percent').textContent = `+${tp.percent}%`;
    });
    
    // Risk metrics
    document.getElementById('riskRatio').textContent = currentSignal.riskRatio;
    document.getElementById('winProbability').textContent = `${currentSignal.winProbability}%`;
    
    // Strategy
    document.getElementById('strategyType').textContent = currentSignal.strategy;
    document.getElementById('strategyConfidence').textContent = `${currentSignal.confidence}%`;
    
    // Start countdown
    startCountdown();
    
    // Update Bit message
    updateBitMessage(`Signal detected: ${currentSignal.symbol} ${currentSignal.direction}. TCS Score: ${currentSignal.tcs.composite}`);
}

// Animate TCS scores
function animateTCSScore(elementId, targetValue) {
    const element = document.getElementById(elementId);
    let currentValue = 0;
    const increment = targetValue / 20;
    
    const animation = setInterval(() => {
        currentValue += increment;
        if (currentValue >= targetValue) {
            currentValue = targetValue;
            clearInterval(animation);
        }
        element.textContent = Math.round(currentValue);
        
        // Color coding
        if (currentValue >= 80) {
            element.style.color = FANG_CONFIG.colors.success;
        } else if (currentValue >= 60) {
            element.style.color = FANG_CONFIG.colors.accent;
        } else {
            element.style.color = FANG_CONFIG.colors.warning;
        }
    }, 50);
}

// Update signal strength meter
function updateSignalStrength(strength) {
    const bar = document.getElementById('strengthBar');
    const value = document.getElementById('strengthValue');
    
    bar.style.width = '0%';
    value.textContent = '0%';
    
    setTimeout(() => {
        bar.style.width = `${strength}%`;
        value.textContent = `${strength}%`;
        
        // Color based on strength
        if (strength >= 80) {
            bar.style.background = `linear-gradient(90deg, ${FANG_CONFIG.colors.success}, ${FANG_CONFIG.colors.accent})`;
        } else if (strength >= 60) {
            bar.style.background = `linear-gradient(90deg, ${FANG_CONFIG.colors.primary}, ${FANG_CONFIG.colors.accent})`;
        } else {
            bar.style.background = `linear-gradient(90deg, ${FANG_CONFIG.colors.warning}, ${FANG_CONFIG.colors.primary})`;
        }
    }, 100);
}

// Update market conditions
function updateMarketConditions() {
    if (!currentSignal || !currentSignal.marketConditions) return;
    
    const conditions = currentSignal.marketConditions;
    
    Object.keys(conditions).forEach(key => {
        const condition = conditions[key];
        document.getElementById(`${key}Level`).textContent = condition.level;
        
        const bar = document.getElementById(`${key}Bar`);
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = `${condition.value}%`;
        }, 100);
    });
}

// Update technical indicators
function updateTechnicalIndicators() {
    if (!currentSignal || !currentSignal.indicators) return;
    
    const grid = document.getElementById('indicatorsGrid');
    grid.innerHTML = '';
    
    // Show 60% of indicators for FANG tier
    const visibleCount = Math.ceil(currentSignal.indicators.length * FANG_CONFIG.dataVisibility);
    const visibleIndicators = currentSignal.indicators.slice(0, visibleCount);
    
    visibleIndicators.forEach(indicator => {
        const item = document.createElement('div');
        item.className = 'indicator-item';
        item.innerHTML = `
            <div class="indicator-name">${indicator.name}</div>
            <div class="indicator-value">${indicator.value}</div>
            <div class="indicator-signal ${indicator.signal.toLowerCase()}">${indicator.signal}</div>
        `;
        grid.appendChild(item);
    });
    
    // Add hidden indicators placeholder
    const hiddenCount = currentSignal.indicators.length - visibleCount;
    if (hiddenCount > 0) {
        const placeholder = document.createElement('div');
        placeholder.className = 'indicator-item locked';
        placeholder.innerHTML = `
            <div class="indicator-locked">+${hiddenCount} MORE</div>
            <div class="indicator-upgrade">UPGRADE FOR FULL ACCESS</div>
        `;
        grid.appendChild(placeholder);
    }
}

// Countdown timer
function startCountdown() {
    if (!currentSignal) return;
    
    const updateCountdown = () => {
        const now = Date.now();
        const remaining = currentSignal.expiry - now;
        
        if (remaining <= 0) {
            document.getElementById('countdown').textContent = 'EXPIRED';
            document.getElementById('urgencyLevel').textContent = 'EXPIRED';
            document.getElementById('urgencyLevel').style.color = FANG_CONFIG.colors.danger;
            document.getElementById('fireButton').disabled = true;
            return;
        }
        
        const minutes = Math.floor(remaining / 60000);
        const seconds = Math.floor((remaining % 60000) / 1000);
        document.getElementById('countdown').textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Update urgency
        if (minutes < 5) {
            document.getElementById('urgencyLevel').textContent = 'CRITICAL';
            document.getElementById('urgencyLevel').style.color = FANG_CONFIG.colors.danger;
        } else if (minutes < 15) {
            document.getElementById('urgencyLevel').textContent = 'HIGH';
            document.getElementById('urgencyLevel').style.color = FANG_CONFIG.colors.warning;
        } else {
            document.getElementById('urgencyLevel').textContent = 'MEDIUM';
            document.getElementById('urgencyLevel').style.color = FANG_CONFIG.colors.accent;
        }
        
        setTimeout(updateCountdown, 1000);
    };
    
    updateCountdown();
}

// Validate signal and update fire control
function validateSignal() {
    if (!currentSignal) return;
    
    const checks = {
        check1: currentSignal.tcs.composite >= FANG_CONFIG.tcsThreshold,
        check2: currentSignal.entry.price && currentSignal.stopLoss,
        check3: currentSignal.marketConditions.trend.value >= 60
    };
    
    // Update checklist
    Object.keys(checks).forEach(checkId => {
        const element = document.getElementById(checkId);
        if (checks[checkId]) {
            element.classList.add('checked');
        } else {
            element.classList.remove('checked');
        }
    });
    
    // Enable fire button if all checks pass
    const allChecksPass = Object.values(checks).every(check => check);
    const fireButton = document.getElementById('fireButton');
    
    if (allChecksPass) {
        fireButton.disabled = false;
        fireButton.querySelector('.fire-text').textContent = 'ENGAGE TARGET';
        document.getElementById('fireStatus').innerHTML = `
            <span class="status-icon">⚡</span>
            <span class="status-message">READY TO FIRE</span>
        `;
        updateBitMessage('All systems green. Ready to engage target.');
    } else {
        fireButton.disabled = true;
        fireButton.querySelector('.fire-text').textContent = 'CHECKS FAILED';
        updateBitMessage('Pre-fire checks incomplete. Review parameters.');
    }
}

// Calculate position size
function calculatePosition() {
    if (!currentSignal) return;
    
    const balance = parseFloat(document.getElementById('accountBalance').value) || 10000;
    const riskPercent = parseFloat(document.getElementById('riskPercent').value) || 2;
    
    const riskAmount = balance * (riskPercent / 100);
    const stopDistance = Math.abs(currentSignal.entry.price - currentSignal.stopLoss);
    const positionSize = riskAmount / stopDistance;
    
    document.getElementById('positionSize').textContent = `${positionSize.toFixed(3)} LOT`;
    document.getElementById('dollarRisk').textContent = `$${riskAmount.toFixed(2)}`;
}

// Handle fire button
async function handleFireButton() {
    if (!currentSignal || isLoading) return;
    
    const fireButton = document.getElementById('fireButton');
    fireButton.disabled = true;
    fireButton.querySelector('.fire-text').textContent = 'ENGAGING...';
    fireButton.querySelector('.fire-loader').style.display = 'block';
    
    try {
        // Simulate trade execution
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Send to Telegram
        const tradeData = {
            signal: currentSignal,
            position: document.getElementById('positionSize').textContent,
            risk: document.getElementById('dollarRisk').textContent,
            timestamp: Date.now()
        };
        
        tg.sendData(JSON.stringify(tradeData));
        
        showAlert('TRADE EXECUTED', `${currentSignal.symbol} ${currentSignal.direction} position opened successfully.`);
        
        // Update UI
        fireButton.querySelector('.fire-text').textContent = 'POSITION ACTIVE';
        updateBitMessage('Trade executed successfully. Monitoring position...');
        
    } catch (error) {
        console.error('Trade execution error:', error);
        showAlert('EXECUTION FAILED', 'Failed to execute trade. Please try again.');
        fireButton.disabled = false;
        fireButton.querySelector('.fire-text').textContent = 'ENGAGE TARGET';
    } finally {
        fireButton.querySelector('.fire-loader').style.display = 'none';
    }
}

// Update Bit assistant message
function updateBitMessage(message) {
    const bitMessage = document.getElementById('bitMessage');
    bitMessage.style.opacity = '0';
    
    setTimeout(() => {
        bitMessage.textContent = message;
        bitMessage.style.opacity = '1';
    }, 200);
}

// Show alert modal
function showAlert(title, message) {
    document.getElementById('alertTitle').textContent = title;
    document.getElementById('alertMessage').textContent = message;
    document.getElementById('alertModal').classList.add('show');
    
    // Auto close after 5 seconds
    setTimeout(closeAlert, 5000);
}

// Close alert modal
function closeAlert() {
    document.getElementById('alertModal').classList.remove('show');
}

// Refresh data
async function refreshData() {
    if (isLoading) return;
    
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.disabled = true;
    refreshBtn.querySelector('.btn-icon').style.animation = 'spin 1s linear infinite';
    
    updateBitMessage('Refreshing data...');
    
    await Promise.all([
        loadUserData(),
        loadSignalData()
    ]);
    
    refreshBtn.disabled = false;
    refreshBtn.querySelector('.btn-icon').style.animation = 'none';
    
    updateBitMessage('Data refreshed successfully.');
}

// Show analytics
function showAnalytics() {
    showAlert('ANALYTICS', 'Full analytics available in FANG tier. Access your performance dashboard in the main app.');
}

// Show profile
function showProfile() {
    showAlert('PROFILE', `Tier: ${userData?.tier || 'FANG'}\nRank: ${userData?.stats.rank || 'ELITE HUNTER'}\nTotal XP: ${userData?.stats.totalXP || 0}`);
}

// Close HUD
function closeHUD() {
    if (confirm('Close FANG HUD and return to main app?')) {
        tg.close();
    }
}

// Auto refresh
function startAutoRefresh() {
    setInterval(() => {
        if (!isLoading) {
            loadSignalData();
        }
    }, FANG_CONFIG.refreshInterval);
}

// CSS animation helper
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .indicator-signal.buy { color: var(--success); }
    .indicator-signal.sell { color: var(--danger); }
    .indicator-signal.neutral { color: var(--fang-muted); }
    
    .direction.long { 
        background: rgba(0, 255, 136, 0.2); 
        color: var(--success);
    }
    .direction.short { 
        background: rgba(255, 0, 102, 0.2); 
        color: var(--danger);
    }
    
    .indicator-item.locked {
        opacity: 0.5;
        text-align: center;
        padding: 20px;
        grid-column: span 2;
    }
    
    .indicator-locked {
        font-size: 18px;
        color: var(--fang-primary);
        margin-bottom: 5px;
    }
    
    .indicator-upgrade {
        font-size: 12px;
        color: var(--fang-muted);
    }
    
    .fire-loader {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 30px;
        height: 30px;
        border: 3px solid var(--fang-darker);
        border-top-color: var(--fang-accent);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        display: none;
    }
`;
document.head.appendChild(style);