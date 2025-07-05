// BITTEN Sniper HUD - Dynamic Functionality

// Initialize Telegram WebApp
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// HUD State Management
const HUDState = {
    signalData: null,
    userTier: 'FREE',
    userId: null,
    countdownInterval: null,
    isFireReady: false,
    personalStats: null,
    showingProfile: false
};

// Initialize HUD
document.addEventListener('DOMContentLoaded', () => {
    initializeHUD();
    setupEventListeners();
    startSystemClock();
    loadSignalData();
});

function initializeHUD() {
    // Get user data from Telegram
    const user = tg.initDataUnsafe.user;
    if (user) {
        HUDState.userId = user.id;
    }
    
    // Set theme
    tg.setHeaderColor('#111111');
    tg.setBackgroundColor('#0a0a0a');
    
    // Parse webapp data
    const urlParams = new URLSearchParams(window.location.search);
    const webappData = urlParams.get('data');
    
    if (webappData) {
        try {
            const data = JSON.parse(webappData);
            HUDState.signalData = data;
            HUDState.userTier = data.user_tier || 'FREE';
            updateUserTier(HUDState.userTier);
        } catch (e) {
            console.error('Failed to parse webapp data:', e);
        }
    }
}

function setupEventListeners() {
    // Fire button
    const fireButton = document.getElementById('fireButton');
    fireButton.addEventListener('click', handleFireButton);
    
    // Footer buttons
    document.getElementById('refreshBtn').addEventListener('click', refreshSignalData);
    document.getElementById('profileBtn').addEventListener('click', toggleProfile);
    document.getElementById('closeBtn').addEventListener('click', () => tg.close());
    
    // Upgrade button
    const upgradeButton = document.getElementById('upgradeButton');
    if (upgradeButton) {
        upgradeButton.addEventListener('click', handleUpgrade);
    }
    
    // Copy recruitment link
    document.getElementById('copyLink').addEventListener('click', copyRecruitmentLink);
    
    // Share button
    document.getElementById('shareButton').addEventListener('click', shareRecruitmentLink);
    
    // Alert modal
    document.getElementById('alertClose').addEventListener('click', closeAlert);
    
    // Risk amount input
    document.getElementById('riskAmount').addEventListener('input', calculatePositionSize);
}

// Load signal data from backend
async function loadSignalData() {
    if (!HUDState.signalData || !HUDState.signalData.signal_id) {
        showAlert('ERROR', 'No signal data available');
        return;
    }
    
    try {
        const response = await fetch(`/api/hud/signal/${HUDState.signalData.signal_id}`, {
            headers: {
                'Authorization': `Bearer ${tg.initData}`,
                'X-User-ID': HUDState.userId
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load signal data');
        }
        
        const data = await response.json();
        updateSignalDisplay(data.signal);
        updateFireControl(data.access);
        
        // Start countdown
        startCountdown(data.signal.expires_at);
        
    } catch (error) {
        console.error('Error loading signal:', error);
        showAlert('CONNECTION ERROR', 'Failed to load signal data');
    }
}

// Update signal display
function updateSignalDisplay(signal) {
    // Update signal ID
    document.getElementById('signalId').textContent = `SIG-${signal.id.substr(-5).toUpperCase()}`;
    
    // Update asset info
    document.getElementById('symbol').textContent = signal.symbol;
    const directionEl = document.getElementById('direction');
    directionEl.textContent = signal.direction;
    directionEl.className = `direction ${signal.direction.toLowerCase()}`;
    
    // Update confidence
    const confidencePercent = signal.confidence * 100;
    document.getElementById('confidenceBar').style.width = `${confidencePercent}%`;
    document.getElementById('confidenceValue').textContent = `${confidencePercent}%`;
    
    // Update urgency
    document.getElementById('urgencyLevel').textContent = signal.urgency;
    document.getElementById('urgencyLevel').className = `urgency-level ${signal.urgency.toLowerCase()}`;
    
    // Update trade parameters
    document.getElementById('entryPrice').textContent = formatPrice(signal.entry_price);
    document.getElementById('stopLoss').textContent = formatPrice(signal.stop_loss);
    document.getElementById('takeProfit').textContent = formatPrice(signal.take_profit);
    document.getElementById('riskRatio').textContent = calculateRiskRatio(signal);
    
    // Update strategy info
    updateStrategyDisplay(signal.strategy);
    
    // Calculate initial position size
    calculatePositionSize();
}

// Update strategy display
function updateStrategyDisplay(strategy) {
    document.getElementById('strategyType').textContent = strategy.type.toUpperCase();
    
    const detailsHtml = `
        <div class="strategy-item">
            <span class="label">Pattern:</span>
            <span class="value">${strategy.pattern || 'N/A'}</span>
        </div>
        <div class="strategy-item">
            <span class="label">Timeframe:</span>
            <span class="value">${strategy.timeframe || 'N/A'}</span>
        </div>
        <div class="strategy-item">
            <span class="label">Strength:</span>
            <span class="value">${strategy.strength || 'N/A'}</span>
        </div>
    `;
    document.getElementById('strategyDetails').innerHTML = detailsHtml;
    
    // Update market conditions
    if (strategy.conditions) {
        const conditionsHtml = strategy.conditions.map(condition => `
            <div class="condition-item ${condition.favorable ? 'favorable' : 'unfavorable'}">
                <span class="condition-icon">${condition.favorable ? '✓' : '⚠'}</span>
                <span class="condition-text">${condition.text}</span>
            </div>
        `).join('');
        document.getElementById('conditionGrid').innerHTML = conditionsHtml;
    }
}

// Update fire control based on access
function updateFireControl(access) {
    const fireButton = document.getElementById('fireButton');
    const fireStatus = document.getElementById('fireStatus');
    const tierLock = document.getElementById('tierLock');
    
    if (access.can_execute) {
        // User has access
        fireButton.disabled = false;
        fireButton.classList.add('ready');
        fireButton.querySelector('.fire-text').textContent = 'FIRE';
        
        fireStatus.innerHTML = `
            <span class="status-icon">🎯</span>
            <span class="status-message">READY TO EXECUTE</span>
        `;
        
        tierLock.style.display = 'none';
        HUDState.isFireReady = true;
        
    } else {
        // User needs upgrade
        fireButton.disabled = true;
        fireButton.classList.remove('ready');
        fireButton.querySelector('.fire-text').textContent = 'LOCKED';
        
        fireStatus.innerHTML = `
            <span class="status-icon">🔒</span>
            <span class="status-message">TIER ${access.required_tier} REQUIRED</span>
        `;
        
        if (tierLock) {
            tierLock.style.display = 'block';
            document.getElementById('requiredTier').textContent = access.required_tier;
        }
        
        HUDState.isFireReady = false;
    }
}

// Countdown timer
function startCountdown(expiresAt) {
    // Clear existing interval
    if (HUDState.countdownInterval) {
        clearInterval(HUDState.countdownInterval);
    }
    
    const updateCountdown = () => {
        const now = Math.floor(Date.now() / 1000);
        const remaining = expiresAt - now;
        
        if (remaining <= 0) {
            clearInterval(HUDState.countdownInterval);
            document.getElementById('countdown').textContent = 'EXPIRED';
            document.getElementById('countdown').classList.add('critical');
            disableFireButton();
            return;
        }
        
        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;
        const countdownEl = document.getElementById('countdown');
        
        countdownEl.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        
        // Add critical class if less than 1 minute
        if (remaining < 60) {
            countdownEl.classList.add('critical');
        }
    };
    
    updateCountdown();
    HUDState.countdownInterval = setInterval(updateCountdown, 1000);
}

// Handle fire button
async function handleFireButton() {
    if (!HUDState.isFireReady) return;
    
    const fireButton = document.getElementById('fireButton');
    const originalText = fireButton.querySelector('.fire-text').textContent;
    
    // Show loading state
    fireButton.classList.add('loading');
    fireButton.disabled = true;
    fireButton.querySelector('.fire-text').textContent = 'EXECUTING...';
    
    try {
        const response = await fetch('/api/hud/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${tg.initData}`,
                'X-User-ID': HUDState.userId
            },
            body: JSON.stringify({
                signal_id: HUDState.signalData.signal_id,
                position_size: calculatePositionSizeValue()
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Success animation
            fireButton.classList.remove('loading');
            fireButton.classList.add('success');
            fireButton.querySelector('.fire-text').textContent = 'EXECUTED!';
            
            // Show success message
            showAlert('MISSION SUCCESS', `Position opened: ${result.position_id}`);
            
            // Update stats if available
            if (result.updated_stats) {
                updatePersonalStats(result.updated_stats);
            }
            
            // Close HUD after delay
            setTimeout(() => {
                tg.close();
            }, 3000);
            
        } else {
            throw new Error(result.message || 'Execution failed');
        }
        
    } catch (error) {
        console.error('Execution error:', error);
        
        // Reset button
        fireButton.classList.remove('loading');
        fireButton.disabled = false;
        fireButton.querySelector('.fire-text').textContent = originalText;
        
        showAlert('EXECUTION FAILED', error.message);
    }
}

// Calculate position size
function calculatePositionSize() {
    const riskAmount = parseFloat(document.getElementById('riskAmount').value) || 100;
    const signal = HUDState.signalData;
    
    if (!signal) return;
    
    // Simple position size calculation (this would be more complex in production)
    const pipValue = 10; // Example pip value
    const stopLossPips = Math.abs(signal.entry_price - signal.stop_loss) * 10000;
    const positionSize = (riskAmount / (stopLossPips * pipValue)).toFixed(2);
    
    document.getElementById('positionSize').textContent = `${positionSize} LOT`;
}

function calculatePositionSizeValue() {
    const sizeText = document.getElementById('positionSize').textContent;
    return parseFloat(sizeText.replace(' LOT', '')) || 0.01;
}

// Calculate risk ratio
function calculateRiskRatio(signal) {
    const risk = Math.abs(signal.entry_price - signal.stop_loss);
    const reward = Math.abs(signal.take_profit - signal.entry_price);
    const ratio = (reward / risk).toFixed(1);
    return `1:${ratio}`;
}

// Format price
function formatPrice(price) {
    return price.toFixed(5);
}

// System clock
function startSystemClock() {
    const updateClock = () => {
        const now = new Date();
        const timeString = now.toTimeString().split(' ')[0];
        document.getElementById('systemTime').textContent = timeString;
    };
    
    updateClock();
    setInterval(updateClock, 1000);
}

// Update user tier display
function updateUserTier(tier) {
    const tierColors = {
        'FREE': '#666666',
        'AUTHORIZED': '#00ccff',
        'ELITE': '#ffcc00',
        'ADMIN': '#ff0044'
    };
    
    const tierEl = document.getElementById('userTier');
    tierEl.textContent = `TIER: ${tier}`;
    tierEl.style.color = tierColors[tier] || '#666666';
}

// Toggle profile view
async function toggleProfile() {
    const profileSection = document.getElementById('personalStats');
    const profileBtn = document.getElementById('profileBtn');
    
    HUDState.showingProfile = !HUDState.showingProfile;
    
    if (HUDState.showingProfile) {
        profileSection.style.display = 'block';
        profileBtn.innerHTML = '<span class="btn-icon">📊</span>SIGNALS';
        
        // Load profile data if not loaded
        if (!HUDState.personalStats) {
            await loadPersonalStats();
        }
    } else {
        profileSection.style.display = 'none';
        profileBtn.innerHTML = '<span class="btn-icon">👤</span>PROFILE';
    }
}

// Load personal stats
async function loadPersonalStats() {
    try {
        const response = await fetch('/api/hud/profile', {
            headers: {
                'Authorization': `Bearer ${tg.initData}`,
                'X-User-ID': HUDState.userId
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load profile');
        }
        
        const data = await response.json();
        HUDState.personalStats = data;
        updatePersonalStats(data);
        
    } catch (error) {
        console.error('Error loading profile:', error);
        showAlert('ERROR', 'Failed to load profile data');
    }
}

// Update personal stats display
function updatePersonalStats(stats) {
    // Update main stats
    document.getElementById('userRank').textContent = stats.rank || 'RECRUIT';
    document.getElementById('totalXP').textContent = stats.total_xp || '0';
    document.getElementById('totalMissions').textContent = stats.missions_completed || '0';
    document.getElementById('successRate').textContent = `${stats.success_rate || 0}%`;
    
    // Update medals
    if (stats.medals) {
        const medalsHtml = stats.medals.map(medal => `
            <div class="medal ${medal.earned ? 'earned' : ''}" title="${medal.name}">
                ${medal.icon}
                <div class="medal-tooltip">${medal.name}</div>
            </div>
        `).join('');
        document.getElementById('medalsGrid').innerHTML = medalsHtml;
    }
    
    // Update recruiting stats
    document.getElementById('recruitCount').textContent = stats.recruits_count || '0';
    document.getElementById('recruitXP').textContent = stats.recruit_xp || '0';
    
    // Set recruitment link
    const recruitLink = `https://t.me/BITTEN_bot?start=ref_${HUDState.userId}`;
    document.getElementById('recruitLink').value = recruitLink;
}

// Copy recruitment link
function copyRecruitmentLink() {
    const linkInput = document.getElementById('recruitLink');
    linkInput.select();
    document.execCommand('copy');
    
    // Show feedback
    const copyBtn = document.getElementById('copyLink');
    const originalText = copyBtn.textContent;
    copyBtn.textContent = 'COPIED!';
    copyBtn.style.background = 'var(--primary-green)';
    copyBtn.style.color = 'var(--bg-dark)';
    
    setTimeout(() => {
        copyBtn.textContent = originalText;
        copyBtn.style.background = '';
        copyBtn.style.color = '';
    }, 2000);
}

// Share recruitment link
function shareRecruitmentLink() {
    const recruitLink = document.getElementById('recruitLink').value;
    const shareText = `Join me in B.I.T.T.E.N. - The Bot-Integrated Tactical Trading Engine! 🎯\n\nProve you belong among the elite traders.\n\n${recruitLink}`;
    
    // Use Telegram's share
    if (tg.isVersionAtLeast('6.1')) {
        tg.shareMessage(shareText);
    } else {
        // Fallback to URL
        window.open(`https://t.me/share/url?url=${encodeURIComponent(recruitLink)}&text=${encodeURIComponent(shareText)}`);
    }
}

// Refresh signal data
async function refreshSignalData() {
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.disabled = true;
    refreshBtn.innerHTML = '<span class="btn-icon">⏳</span>LOADING...';
    
    await loadSignalData();
    
    refreshBtn.disabled = false;
    refreshBtn.innerHTML = '<span class="btn-icon">🔄</span>REFRESH';
}

// Handle upgrade
function handleUpgrade() {
    // Send upgrade request to Telegram bot
    tg.sendData(JSON.stringify({
        action: 'upgrade_tier',
        current_tier: HUDState.userTier,
        signal_id: HUDState.signalData.signal_id
    }));
}

// Disable fire button
function disableFireButton() {
    const fireButton = document.getElementById('fireButton');
    fireButton.disabled = true;
    fireButton.classList.remove('ready');
    fireButton.querySelector('.fire-text').textContent = 'EXPIRED';
    
    document.getElementById('fireStatus').innerHTML = `
        <span class="status-icon">⏰</span>
        <span class="status-message">SIGNAL EXPIRED</span>
    `;
}

// Show alert modal
function showAlert(title, message) {
    const modal = document.getElementById('alertModal');
    document.getElementById('alertTitle').textContent = title;
    document.getElementById('alertMessage').textContent = message;
    modal.classList.add('active');
    
    // Add glitch effect on error
    if (title.includes('ERROR') || title.includes('FAILED')) {
        document.body.classList.add('error-glitch');
        setTimeout(() => {
            document.body.classList.remove('error-glitch');
        }, 1000);
    }
}

// Close alert modal
function closeAlert() {
    const modal = document.getElementById('alertModal');
    modal.classList.remove('active');
}

// Add CSS class for error glitch
const style = document.createElement('style');
style.textContent = `
    .error-glitch {
        animation: error-glitch 0.5s;
    }
    
    @keyframes error-glitch {
        0%, 100% { filter: hue-rotate(0deg); }
        20% { filter: hue-rotate(90deg) brightness(1.5); }
        40% { filter: hue-rotate(-90deg) contrast(2); }
        60% { filter: hue-rotate(180deg) saturate(2); }
        80% { filter: hue-rotate(-180deg) brightness(0.8); }
    }
`;
document.head.appendChild(style);