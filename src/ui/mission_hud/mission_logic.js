// HydraX Mission Command Center - Core Logic

// Initialize Telegram WebApp
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
}

// Mission State Management
const MissionState = {
    missionData: null,
    operatorInfo: null,
    currentSignal: null,
    countdown: null,
    tcsConnected: false,
    preFlightStatus: {
        market: false,
        risk: false,
        capital: false,
        authorization: false
    },
    activeTab: 'analysis',
    alerts: [],
    stats: {
        successRate: 0,
        totalMissions: 0,
        totalPnL: 0,
        currentStreak: 0
    }
};

// Initialize Mission Control
document.addEventListener('DOMContentLoaded', () => {
    initializeMissionControl();
    setupEventListeners();
    startSystemClocks();
    loadMissionData();
    performPreFlightChecks();
});

function initializeMissionControl() {
    // Get operator data from Telegram
    if (tg && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user;
        MissionState.operatorInfo = {
            id: user.id,
            username: user.username || 'OPERATOR',
            clearance: 'LEVEL 1' // Default clearance
        };
        updateOperatorDisplay();
    }
    
    // Set theme colors
    if (tg) {
        tg.setHeaderColor('#111111');
        tg.setBackgroundColor('#0a0a0a');
    }
    
    // Generate mission ID
    MissionState.missionData = {
        id: generateMissionId(),
        timestamp: Date.now()
    };
    document.getElementById('missionId').textContent = MissionState.missionData.id;
    
    // Initialize visual effects
    initializeGlitchEffects();
}

function generateMissionId() {
    const prefix = 'MX';
    const timestamp = Date.now().toString(36).toUpperCase();
    const random = Math.random().toString(36).substr(2, 4).toUpperCase();
    return `${prefix}-${timestamp}-${random}`;
}

function updateOperatorDisplay() {
    if (MissionState.operatorInfo) {
        document.getElementById('operatorId').textContent = 
            MissionState.operatorInfo.username.toUpperCase();
        document.getElementById('clearanceLevel').textContent = 
            MissionState.operatorInfo.clearance;
    }
}

// Event Listeners Setup
function setupEventListeners() {
    // Tab Navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => switchTab(e.target.dataset.tab));
    });
    
    // Tactical Controls
    document.getElementById('refreshTactical').addEventListener('click', refreshTacticalData);
    
    // Launch Button
    document.getElementById('launchButton').addEventListener('click', initiateMission);
    
    // TCS Controls
    document.getElementById('connectTCS').addEventListener('click', connectTCS);
    document.getElementById('syncSettings').addEventListener('click', syncTCSSettings);
    document.getElementById('autoExecute').addEventListener('change', toggleAutoExecute);
    
    // Footer Actions
    document.getElementById('dashboardBtn').addEventListener('click', openDashboard);
    document.getElementById('historyBtn').addEventListener('click', openHistory);
    document.getElementById('settingsBtn').addEventListener('click', openSettings);
    document.getElementById('abortBtn').addEventListener('click', abortMission);
    
    // Position Sizing
    document.getElementById('riskAmount').addEventListener('input', calculatePositionSize);
    
    // Modal Close
    document.getElementById('modalOverlay').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) closeModal();
    });
}

// System Clocks
function startSystemClocks() {
    // Mission Timer
    setInterval(() => {
        const now = new Date();
        const timeString = now.toTimeString().split(' ')[0];
        document.getElementById('missionTimer').textContent = timeString;
        document.getElementById('serverTime').textContent = `${timeString} UTC`;
    }, 1000);
    
    // Mission Countdown
    startMissionCountdown();
}

function startMissionCountdown() {
    // Simulate mission time window (5 minutes)
    let timeRemaining = 300; // 5 minutes in seconds
    
    MissionState.countdown = setInterval(() => {
        if (timeRemaining <= 0) {
            clearInterval(MissionState.countdown);
            updateEntryWindow('EXPIRED');
            showAlert('warning', 'Mission window has expired');
            return;
        }
        
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = timeRemaining % 60;
        const display = document.getElementById('missionCountdown');
        
        display.innerHTML = `
            <span class="countdown-number">${String(minutes).padStart(2, '0')}</span>
            <span class="countdown-separator">:</span>
            <span class="countdown-number">${String(seconds).padStart(2, '0')}</span>
            <span class="countdown-separator">:</span>
            <span class="countdown-number">00</span>
        `;
        
        // Update urgency based on time remaining
        if (timeRemaining <= 60) {
            display.style.color = 'var(--hydra-red)';
            document.getElementById('urgencyLevel').textContent = 'CRITICAL';
        } else if (timeRemaining <= 180) {
            display.style.color = 'var(--hydra-yellow)';
            document.getElementById('urgencyLevel').textContent = 'HIGH';
        }
        
        timeRemaining--;
    }, 1000);
}

// Load Mission Data
async function loadMissionData() {
    try {
        // Simulate API call for mission data
        showLoadingState();
        
        // In production, this would be an actual API call
        setTimeout(() => {
            const mockData = generateMockMissionData();
            MissionState.currentSignal = mockData;
            updateMissionDisplay(mockData);
            hideLoadingState();
        }, 1500);
        
    } catch (error) {
        console.error('Failed to load mission data:', error);
        showAlert('error', 'Failed to load mission data');
        hideLoadingState();
    }
}

function generateMockMissionData() {
    return {
        asset: 'BTC/USDT',
        direction: 'LONG',
        currentPrice: 45678.90,
        priceChange24h: 2.34,
        entryPrice: 45650.00,
        entryRangeMin: 45600.00,
        entryRangeMax: 45700.00,
        stopLoss: 45000.00,
        targets: [46200.00, 46500.00, 47000.00],
        riskRatio: '1:3.5',
        confidence: 87,
        volatility: 65,
        volume: 82,
        momentum: 73,
        pattern: {
            name: 'BULL FLAG',
            confidence: 87,
            description: 'Strong bullish continuation pattern detected on 4H timeframe'
        },
        indicators: {
            rsi: 65.4,
            macd: 0.054,
            ma200: 45230
        },
        sentiment: 72
    };
}

function updateMissionDisplay(data) {
    // Update Primary Target
    document.getElementById('targetAsset').textContent = data.asset;
    document.getElementById('marketDirection').innerHTML = `
        <span class="direction-arrow">${data.direction === 'LONG' ? '↗' : '↘'}</span>
        <span class="direction-text">${data.direction}</span>
    `;
    document.getElementById('currentPrice').textContent = data.currentPrice.toFixed(2);
    document.getElementById('priceChange').textContent = 
        `${data.priceChange24h > 0 ? '+' : ''}${data.priceChange24h.toFixed(2)}%`;
    
    // Update Market Conditions
    updateConditionMeter('volatility', data.volatility);
    updateConditionMeter('volume', data.volume);
    updateConditionMeter('momentum', data.momentum);
    
    // Update Entry Parameters
    document.getElementById('entryPrice').textContent = data.entryPrice.toFixed(5);
    document.getElementById('entryRangeMin').textContent = data.entryRangeMin.toFixed(5);
    document.getElementById('entryRangeMax').textContent = data.entryRangeMax.toFixed(5);
    
    // Update Risk Management
    document.getElementById('stopLoss').textContent = data.stopLoss.toFixed(5);
    document.getElementById('riskPercent').textContent = '2.5%';
    
    // Update Profit Targets
    document.getElementById('target1').textContent = data.targets[0].toFixed(5);
    document.getElementById('target2').textContent = data.targets[1].toFixed(5);
    document.getElementById('target3').textContent = data.targets[2].toFixed(5);
    
    // Update Intelligence Data
    updateIntelligencePanel(data);
    
    // Calculate initial position size
    calculatePositionSize();
}

function updateConditionMeter(type, value) {
    const meter = document.getElementById(`${type}Meter`);
    const valueElement = document.getElementById(`${type}Value`);
    
    meter.style.width = `${value}%`;
    
    // Update color based on value
    if (value >= 70) {
        meter.style.background = 'var(--gradient-green)';
        valueElement.textContent = type === 'momentum' ? 'BULLISH' : 'HIGH';
        valueElement.style.color = 'var(--hydra-green)';
    } else if (value >= 40) {
        meter.style.background = 'var(--gradient-blue)';
        valueElement.textContent = 'MODERATE';
        valueElement.style.color = 'var(--hydra-blue)';
    } else {
        meter.style.background = 'var(--gradient-red)';
        valueElement.textContent = type === 'momentum' ? 'BEARISH' : 'LOW';
        valueElement.style.color = 'var(--hydra-red)';
    }
}

function updateIntelligencePanel(data) {
    // Update Technical Analysis
    document.getElementById('rsiValue').textContent = data.indicators.rsi.toFixed(1);
    document.getElementById('macdValue').textContent = 
        `${data.indicators.macd > 0 ? '+' : ''}${data.indicators.macd.toFixed(3)}`;
    document.getElementById('maValue').textContent = data.indicators.ma200.toLocaleString();
    
    // Update Pattern Recognition
    document.getElementById('patternDetected').innerHTML = `
        <span class="pattern-name">${data.pattern.name}</span>
        <span class="pattern-confidence">${data.pattern.confidence}% CONFIDENCE</span>
    `;
    document.getElementById('patternDescription').textContent = data.pattern.description;
    
    // Update Sentiment
    document.getElementById('sentimentFill').style.width = `${data.sentiment}%`;
    document.querySelector('.sentiment-value').textContent = data.sentiment;
    
    // Update Signal Strength
    updateSignalStrength(data.confidence);
}

function updateSignalStrength(confidence) {
    const strengthBar = document.getElementById('signalStrength');
    const strengthValue = document.getElementById('strengthValue');
    
    strengthBar.style.width = `${confidence}%`;
    
    if (confidence >= 80) {
        strengthBar.style.background = 'var(--gradient-green)';
        strengthValue.textContent = 'STRONG';
        strengthValue.style.color = 'var(--hydra-green)';
    } else if (confidence >= 60) {
        strengthBar.style.background = 'var(--gradient-blue)';
        strengthValue.textContent = 'MODERATE';
        strengthValue.style.color = 'var(--hydra-blue)';
    } else {
        strengthBar.style.background = 'var(--gradient-red)';
        strengthValue.textContent = 'WEAK';
        strengthValue.style.color = 'var(--hydra-red)';
    }
}

// Pre-Flight Checks
function performPreFlightChecks() {
    const checks = ['market', 'risk', 'capital', 'authorization'];
    let completedChecks = 0;
    
    checks.forEach((check, index) => {
        setTimeout(() => {
            const checkItem = document.querySelector(`[data-check="${check}"]`);
            
            // Simulate check process
            checkItem.querySelector('.check-status').textContent = 'VERIFYING...';
            
            setTimeout(() => {
                MissionState.preFlightStatus[check] = true;
                checkItem.setAttribute('data-status', 'ready');
                checkItem.querySelector('.check-icon').textContent = '✓';
                checkItem.querySelector('.check-status').textContent = 'READY';
                
                completedChecks++;
                
                // Update launch button progress
                const progress = (completedChecks / checks.length) * 100;
                document.getElementById('launchProgress').style.width = `${progress}%`;
                
                // Enable launch button when all checks complete
                if (completedChecks === checks.length) {
                    enableLaunchButton();
                }
            }, 1000 + Math.random() * 1000);
        }, index * 500);
    });
}

function enableLaunchButton() {
    const launchButton = document.getElementById('launchButton');
    launchButton.disabled = false;
    launchButton.classList.add('ready');
    document.getElementById('launchStatus').textContent = 'READY FOR LAUNCH';
    document.querySelector('.launch-text').textContent = 'EXECUTE MISSION';
    showAlert('success', 'All systems ready - Mission can be initiated');
}

// Position Sizing Calculator
function calculatePositionSize() {
    if (!MissionState.currentSignal) return;
    
    const riskAmount = parseFloat(document.getElementById('riskAmount').value) || 100;
    const entryPrice = MissionState.currentSignal.entryPrice;
    const stopLoss = MissionState.currentSignal.stopLoss;
    const riskPercentage = Math.abs((entryPrice - stopLoss) / entryPrice) * 100;
    
    // Calculate position size (simplified calculation)
    const positionSize = (riskAmount / riskPercentage).toFixed(2);
    const leverage = Math.min(Math.ceil(positionSize / riskAmount), 20);
    
    document.getElementById('positionSize').textContent = `${positionSize} LOT`;
    document.getElementById('leverageValue').textContent = `${leverage}x`;
}

// Tab Switching
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.intel-tab').forEach(tab => {
        tab.classList.toggle('active', tab.id === `${tabName}Tab`);
    });
    
    MissionState.activeTab = tabName;
    
    // Load tab-specific content
    if (tabName === 'signals') {
        loadSignalComponents();
    } else if (tabName === 'risks') {
        loadRiskMatrix();
    }
}

function loadSignalComponents() {
    const componentList = document.getElementById('componentList');
    const components = [
        { name: 'Technical Indicators', status: 'CONFIRMED', weight: 35 },
        { name: 'Pattern Recognition', status: 'STRONG', weight: 30 },
        { name: 'Market Structure', status: 'ALIGNED', weight: 20 },
        { name: 'Volume Analysis', status: 'POSITIVE', weight: 15 }
    ];
    
    componentList.innerHTML = components.map(comp => `
        <div class="signal-component">
            <span class="component-name">${comp.name}</span>
            <span class="component-status ${comp.status.toLowerCase()}">${comp.status}</span>
            <span class="component-weight">${comp.weight}%</span>
        </div>
    `).join('');
}

function loadRiskMatrix() {
    const riskMatrix = document.getElementById('riskMatrix');
    const risks = [
        { factor: 'Market Volatility', level: 'high', impact: 'HIGH' },
        { factor: 'Economic Events', level: 'medium', impact: 'MEDIUM' },
        { factor: 'Technical Resistance', level: 'low', impact: 'LOW' },
        { factor: 'Liquidity Risk', level: 'low', impact: 'LOW' }
    ];
    
    riskMatrix.innerHTML = risks.map(risk => `
        <div class="risk-item ${risk.level}">
            <span class="risk-factor">${risk.factor}</span>
            <span class="risk-impact">${risk.impact}</span>
        </div>
    `).join('');
}

// Mission Execution
async function initiateMission() {
    const launchButton = document.getElementById('launchButton');
    
    if (!launchButton.classList.contains('ready')) {
        showAlert('warning', 'Pre-flight checks not complete');
        return;
    }
    
    // Disable button and show progress
    launchButton.disabled = true;
    document.getElementById('launchStatus').textContent = 'INITIATING MISSION...';
    
    try {
        // Simulate mission execution
        await executeMissionSequence();
        
        // Update stats
        MissionState.stats.totalMissions++;
        updateMissionStats();
        
        showAlert('success', 'Mission initiated successfully');
        
        // Send data back to Telegram if available
        if (tg) {
            tg.sendData(JSON.stringify({
                action: 'mission_executed',
                missionId: MissionState.missionData.id,
                signal: MissionState.currentSignal
            }));
        }
        
    } catch (error) {
        console.error('Mission execution failed:', error);
        showAlert('error', 'Mission execution failed');
        launchButton.disabled = false;
    }
}

async function executeMissionSequence() {
    // Simulate execution steps
    const steps = [
        'Validating parameters...',
        'Connecting to exchange...',
        'Placing orders...',
        'Confirming execution...'
    ];
    
    for (const step of steps) {
        document.getElementById('launchStatus').textContent = step;
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}

// TCS Integration
function connectTCS() {
    const indicator = document.getElementById('tcsStatusIndicator');
    const statusText = document.getElementById('tcsStatusText');
    
    if (MissionState.tcsConnected) {
        // Disconnect
        MissionState.tcsConnected = false;
        indicator.classList.remove('active');
        statusText.textContent = 'DISCONNECTED';
        document.getElementById('connectTCS').innerHTML = `
            <span class="btn-icon">🔗</span>
            CONNECT TCS
        `;
        showAlert('info', 'TCS disconnected');
    } else {
        // Connect
        MissionState.tcsConnected = true;
        indicator.classList.add('active');
        statusText.textContent = 'CONNECTED';
        document.getElementById('connectTCS').innerHTML = `
            <span class="btn-icon">🔓</span>
            DISCONNECT
        `;
        showAlert('success', 'TCS connected successfully');
        
        // Start live feed
        startTCSFeed();
    }
}

function startTCSFeed() {
    const feedMessages = document.getElementById('feedMessages');
    const messages = [
        'TCS: Connection established',
        'TCS: Synchronizing settings...',
        'TCS: Live feed active',
        'TCS: Monitoring signals...'
    ];
    
    messages.forEach((msg, index) => {
        setTimeout(() => {
            const messageElement = document.createElement('div');
            messageElement.className = 'feed-message';
            messageElement.textContent = `[${new Date().toTimeString().split(' ')[0]}] ${msg}`;
            feedMessages.appendChild(messageElement);
            feedMessages.scrollTop = feedMessages.scrollHeight;
        }, index * 1000);
    });
}

function syncTCSSettings() {
    if (!MissionState.tcsConnected) {
        showAlert('warning', 'Please connect TCS first');
        return;
    }
    
    showAlert('info', 'Synchronizing TCS settings...');
    
    setTimeout(() => {
        showAlert('success', 'TCS settings synchronized');
    }, 1500);
}

function toggleAutoExecute(e) {
    const enabled = e.target.checked;
    
    if (enabled && !MissionState.tcsConnected) {
        e.target.checked = false;
        showAlert('warning', 'Please connect TCS first');
        return;
    }
    
    showAlert('info', `Auto-execute ${enabled ? 'enabled' : 'disabled'}`);
}

// Alert System
function showAlert(type, message) {
    const alertContainer = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = `alert ${type}`;
    
    const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
    };
    
    alert.innerHTML = `
        <span class="alert-icon">${icons[type]}</span>
        <span class="alert-message">${message}</span>
        <span class="alert-close">✕</span>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        alert.remove();
    }, 5000);
    
    // Manual close
    alert.querySelector('.alert-close').addEventListener('click', () => {
        alert.remove();
    });
}

// Modal Functions
function openModal(content) {
    const modalOverlay = document.getElementById('modalOverlay');
    const modalContent = document.getElementById('modalContent');
    
    modalContent.innerHTML = content;
    modalOverlay.classList.add('active');
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('active');
}

// Footer Actions
function openDashboard() {
    // In production, this would navigate to dashboard
    showAlert('info', 'Opening dashboard...');
}

function openHistory() {
    const historyContent = `
        <h2>Mission History</h2>
        <div class="history-list">
            <p>No previous missions found</p>
        </div>
        <button class="modal-close-btn" onclick="closeModal()">Close</button>
    `;
    openModal(historyContent);
}

function openSettings() {
    const settingsContent = `
        <h2>Mission Settings</h2>
        <div class="settings-list">
            <div class="setting-item">
                <label>Default Risk Amount</label>
                <input type="number" value="100" min="10">
            </div>
            <div class="setting-item">
                <label>Max Leverage</label>
                <input type="number" value="20" min="1" max="100">
            </div>
            <div class="setting-item">
                <label>Sound Alerts</label>
                <div class="toggle-switch">
                    <input type="checkbox" id="soundAlerts" checked>
                    <label for="soundAlerts"></label>
                </div>
            </div>
        </div>
        <button class="save-btn" onclick="saveSettings()">Save Settings</button>
        <button class="modal-close-btn" onclick="closeModal()">Close</button>
    `;
    openModal(settingsContent);
}

function saveSettings() {
    showAlert('success', 'Settings saved');
    closeModal();
}

function abortMission() {
    if (confirm('Are you sure you want to abort the current mission?')) {
        clearInterval(MissionState.countdown);
        showAlert('warning', 'Mission aborted');
        
        // Reset UI
        document.getElementById('launchButton').disabled = true;
        document.getElementById('launchStatus').textContent = 'MISSION ABORTED';
        
        // Close app if in Telegram
        if (tg) {
            setTimeout(() => {
                tg.close();
            }, 1500);
        }
    }
}

// Utility Functions
function refreshTacticalData() {
    showAlert('info', 'Refreshing tactical data...');
    loadMissionData();
}

function updateEntryWindow(status) {
    const windowElement = document.getElementById('entryWindow');
    windowElement.textContent = status;
    windowElement.style.color = status === 'ACTIVE' ? 'var(--hydra-green)' : 'var(--hydra-red)';
}

function updateMissionStats() {
    document.getElementById('totalMissions').textContent = MissionState.stats.totalMissions;
    document.getElementById('successRate').textContent = 
        `${MissionState.stats.successRate.toFixed(1)}%`;
    document.getElementById('totalPnL').textContent = 
        `${MissionState.stats.totalPnL >= 0 ? '+' : ''}${MissionState.stats.totalPnL.toFixed(2)}%`;
    document.getElementById('currentStreak').textContent = MissionState.stats.currentStreak;
}

function showLoadingState() {
    // Add loading indicators to various sections
    document.querySelectorAll('.metric-value, .param-value').forEach(el => {
        el.innerHTML = '<span class="loading"></span>';
    });
}

function hideLoadingState() {
    // Remove loading indicators
    document.querySelectorAll('.loading').forEach(el => {
        el.remove();
    });
}

// Visual Effects
function initializeGlitchEffects() {
    const glitchOverlay = document.getElementById('glitchOverlay');
    
    // Random glitch effects
    setInterval(() => {
        if (Math.random() > 0.95) {
            glitchOverlay.style.opacity = '1';
            setTimeout(() => {
                glitchOverlay.style.opacity = '0';
            }, 100);
        }
    }, 3000);
}

// Export for external use
window.MissionControl = {
    showAlert,
    openModal,
    closeModal,
    updateMissionData,
    initiateMission
};