// Education HUD Logic - Military Grade Learning System

class EducationHUD {
    constructor() {
        this.currentLevel = 42;
        this.currentXP = 8750;
        this.neededXP = 10000;
        this.missionsCompleted = 127;
        this.streakMultiplier = 5;
        this.timeDeployed = { hours: 48, minutes: 32, seconds: 15 };
        
        // Mission data
        this.missions = [
            {
                id: 1,
                name: "OPERATION: PYTHON MASTERY",
                progress: 75,
                xp: 250,
                active: true
            },
            {
                id: 2,
                name: "RECON: DATA STRUCTURES",
                progress: 30,
                xp: 500,
                active: false
            },
            {
                id: 3,
                name: "TACTICAL: ALGORITHM TRAINING",
                progress: 10,
                xp: 750,
                active: false
            }
        ];
        
        // Achievement queue
        this.achievementQueue = [];
        this.isShowingAchievement = false;
        
        // Initialize
        this.init();
    }
    
    init() {
        this.updateTime();
        this.startTimers();
        this.attachEventListeners();
        this.initializeRadar();
        this.startRandomEvents();
        
        // Initial animation
        this.playBootSequence();
    }
    
    playBootSequence() {
        // Add glitch effect on startup
        document.body.classList.add('glitch');
        setTimeout(() => {
            document.body.classList.remove('glitch');
        }, 500);
        
        // Stagger widget animations
        const widgets = document.querySelectorAll('.widget');
        widgets.forEach((widget, index) => {
            widget.style.animationDelay = `${index * 0.1}s`;
        });
    }
    
    updateTime() {
        const now = new Date();
        const timeString = now.toTimeString().split(' ')[0];
        document.getElementById('currentTime').textContent = timeString;
    }
    
    startTimers() {
        // Update clock
        setInterval(() => this.updateTime(), 1000);
        
        // Update deployment time
        setInterval(() => {
            this.timeDeployed.seconds++;
            if (this.timeDeployed.seconds >= 60) {
                this.timeDeployed.seconds = 0;
                this.timeDeployed.minutes++;
                if (this.timeDeployed.minutes >= 60) {
                    this.timeDeployed.minutes = 0;
                    this.timeDeployed.hours++;
                }
            }
            this.updateDeploymentTime();
        }, 1000);
        
        // Simulate ping variations
        setInterval(() => {
            const ping = 12 + Math.floor(Math.random() * 8);
            document.querySelector('.ping').textContent = `${ping}ms`;
        }, 2000);
    }
    
    updateDeploymentTime() {
        const timeStr = `${String(this.timeDeployed.hours).padStart(2, '0')}:${String(this.timeDeployed.minutes).padStart(2, '0')}:${String(this.timeDeployed.seconds).padStart(2, '0')}`;
        document.getElementById('timeDeployed').textContent = timeStr;
    }
    
    attachEventListeners() {
        // Mission interactions
        document.querySelectorAll('.mission-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const missionId = parseInt(item.dataset.missionId);
                this.selectMission(missionId);
            });
        });
        
        // Quick action buttons
        document.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = btn.dataset.action;
                this.handleQuickAction(action);
            });
        });
        
        // Norman's Notebook entries
        document.querySelectorAll('.notebook-entry').forEach(entry => {
            entry.addEventListener('click', () => {
                this.addTacticalFeedItem("Accessing Norman's Intel Database...");
                // Simulate loading
                setTimeout(() => {
                    this.showAchievement("Knowledge Seeker", "Accessed Norman's Notebook", 100);
                }, 1000);
            });
        });
        
        // Access button
        document.querySelector('.access-button').addEventListener('click', () => {
            this.addTacticalFeedItem("NORMAN'S NOTEBOOK: Full access granted");
            this.simulateXPGain(50);
        });
    }
    
    selectMission(missionId) {
        // Update active states
        document.querySelectorAll('.mission-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const selectedMission = document.querySelector(`[data-mission-id="${missionId}"]`);
        selectedMission.classList.add('active');
        
        // Update radar
        this.updateRadarTarget(missionId);
        
        // Add to tactical feed
        const mission = this.missions.find(m => m.id === missionId);
        this.addTacticalFeedItem(`Mission Selected: ${mission.name}`);
        
        // Sound effect simulation
        this.playSound('select');
    }
    
    handleQuickAction(action) {
        const actions = {
            deploy: "Deploying to mission area...",
            inventory: "Accessing loadout configuration...",
            intel: "Retrieving intelligence briefing...",
            comms: "Opening secure communications..."
        };
        
        this.addTacticalFeedItem(actions[action]);
        
        // Add visual feedback
        const btn = document.querySelector(`[data-action="${action}"]`);
        btn.style.background = 'rgba(0, 255, 65, 0.2)';
        setTimeout(() => {
            btn.style.background = 'transparent';
        }, 300);
    }
    
    initializeRadar() {
        // Add interactive radar blips
        document.querySelectorAll('.blip').forEach(blip => {
            blip.addEventListener('click', () => {
                this.addTacticalFeedItem("Target acquired on radar");
                blip.classList.add('pulse');
                setTimeout(() => blip.classList.remove('pulse'), 1000);
            });
        });
    }
    
    updateRadarTarget(missionId) {
        // Simulate radar update
        const radar = document.querySelector('.radar');
        radar.classList.add('glitch');
        setTimeout(() => radar.classList.remove('glitch'), 300);
    }
    
    startRandomEvents() {
        // Random XP gains
        setInterval(() => {
            if (Math.random() < 0.3) {
                const xpAmount = Math.floor(Math.random() * 50) + 10;
                this.simulateXPGain(xpAmount);
            }
        }, 10000);
        
        // Random mission progress
        setInterval(() => {
            if (Math.random() < 0.4) {
                const missionIndex = Math.floor(Math.random() * this.missions.length);
                this.updateMissionProgress(missionIndex);
            }
        }, 8000);
        
        // Random achievements
        setInterval(() => {
            if (Math.random() < 0.2) {
                const achievements = [
                    { title: "Speed Demon", desc: "Complete 5 missions in 1 hour", xp: 300 },
                    { title: "Perfect Execution", desc: "100% accuracy on Algorithm Training", xp: 500 },
                    { title: "Night Owl", desc: "Study past midnight", xp: 200 },
                    { title: "Quick Learner", desc: "Master a concept in record time", xp: 400 }
                ];
                const achievement = achievements[Math.floor(Math.random() * achievements.length)];
                this.showAchievement(achievement.title, achievement.desc, achievement.xp);
            }
        }, 15000);
    }
    
    simulateXPGain(amount) {
        // Show XP gain indicator
        const indicator = document.getElementById('xpGainIndicator');
        indicator.textContent = `+${amount} XP`;
        indicator.style.opacity = '1';
        indicator.style.animation = 'none';
        
        setTimeout(() => {
            indicator.style.animation = 'xpGain 2s ease-out';
        }, 10);
        
        // Update XP
        this.currentXP += amount;
        
        // Check for level up
        if (this.currentXP >= this.neededXP) {
            this.levelUp();
        } else {
            this.updateXPDisplay();
        }
        
        // Update streak
        if (Math.random() < 0.3) {
            this.updateStreak();
        }
    }
    
    updateXPDisplay() {
        document.getElementById('currentXP').textContent = this.currentXP.toLocaleString();
        const percentage = (this.currentXP / this.neededXP) * 100;
        document.getElementById('xpFill').style.width = `${percentage}%`;
    }
    
    levelUp() {
        this.currentLevel++;
        this.currentXP = this.currentXP - this.neededXP;
        this.neededXP = Math.floor(this.neededXP * 1.2);
        
        // Show level up animation
        const levelUpAnim = document.getElementById('levelUpAnimation');
        document.getElementById('newLevelNumber').textContent = this.currentLevel;
        levelUpAnim.classList.add('show');
        
        // Play level up sound
        this.playSound('levelup');
        
        setTimeout(() => {
            levelUpAnim.classList.remove('show');
            document.getElementById('currentLevel').textContent = this.currentLevel;
            document.getElementById('neededXP').textContent = this.neededXP.toLocaleString();
            this.updateXPDisplay();
        }, 3000);
        
        // Add to feed
        this.addTacticalFeedItem(`LEVEL UP! You are now Level ${this.currentLevel}`);
        
        // Update missions completed
        this.missionsCompleted++;
        document.getElementById('missionsCompleted').textContent = this.missionsCompleted;
    }
    
    updateMissionProgress(missionIndex) {
        const mission = this.missions[missionIndex];
        const progressIncrease = Math.floor(Math.random() * 10) + 5;
        mission.progress = Math.min(mission.progress + progressIncrease, 100);
        
        // Update UI
        const missionElement = document.querySelector(`[data-mission-id="${mission.id}"]`);
        const progressFill = missionElement.querySelector('.progress-fill');
        const progressText = missionElement.querySelector('.progress-text');
        
        progressFill.style.width = `${mission.progress}%`;
        progressText.textContent = `${mission.progress}% COMPLETE`;
        
        // Check for completion
        if (mission.progress === 100) {
            this.completeMission(mission);
        } else {
            this.addTacticalFeedItem(`Mission Progress: ${mission.name} +${progressIncrease}%`);
        }
    }
    
    completeMission(mission) {
        this.showAchievement("Mission Complete", mission.name, mission.xp);
        this.simulateXPGain(mission.xp);
        
        // Reset mission
        setTimeout(() => {
            mission.progress = 0;
            this.updateMissionProgress(this.missions.indexOf(mission));
        }, 5000);
    }
    
    updateStreak() {
        this.streakMultiplier = Math.min(this.streakMultiplier + 1, 10);
        document.getElementById('streakMultiplier').textContent = `x${this.streakMultiplier}`;
        
        // Add glow effect
        const streakElement = document.getElementById('streakMultiplier');
        streakElement.style.textShadow = `0 0 ${10 + this.streakMultiplier * 2}px var(--warning-orange)`;
    }
    
    showAchievement(title, description, xp) {
        // Queue achievement if one is showing
        if (this.isShowingAchievement) {
            this.achievementQueue.push({ title, description, xp });
            return;
        }
        
        this.isShowingAchievement = true;
        
        const notification = document.getElementById('achievementNotification');
        document.getElementById('achievementSubtitle').textContent = title;
        notification.querySelector('.achievement-xp').textContent = `+${xp} XP`;
        
        notification.classList.add('show');
        this.playSound('achievement');
        
        // Add to achievement list
        this.addAchievementToList(title, description);
        
        // Add to tactical feed
        this.addTacticalFeedItem(`ACHIEVEMENT UNLOCKED: ${title}`);
        
        setTimeout(() => {
            notification.classList.remove('show');
            this.isShowingAchievement = false;
            
            // Show next queued achievement
            if (this.achievementQueue.length > 0) {
                const next = this.achievementQueue.shift();
                setTimeout(() => {
                    this.showAchievement(next.title, next.description, next.xp);
                }, 500);
            }
        }, 3000);
    }
    
    addAchievementToList(title, description) {
        const achievementList = document.querySelector('.achievement-list');
        const newAchievement = document.createElement('div');
        newAchievement.className = 'achievement-item';
        newAchievement.style.animation = 'feedItemEntry 0.5s ease-out';
        
        const icons = ['🎖️', '⚡', '🔥', '💎', '🌟'];
        const randomIcon = icons[Math.floor(Math.random() * icons.length)];
        
        newAchievement.innerHTML = `
            <div class="achievement-icon">${randomIcon}</div>
            <div class="achievement-details">
                <div class="achievement-name">${title}</div>
                <div class="achievement-desc">${description}</div>
            </div>
        `;
        
        // Add to top of list
        if (achievementList.firstChild) {
            achievementList.insertBefore(newAchievement, achievementList.firstChild);
        } else {
            achievementList.appendChild(newAchievement);
        }
        
        // Keep only last 3 achievements
        while (achievementList.children.length > 3) {
            achievementList.removeChild(achievementList.lastChild);
        }
    }
    
    addTacticalFeedItem(message) {
        const feed = document.getElementById('tacticalFeed');
        const timestamp = new Date().toTimeString().split(' ')[0];
        
        const feedItem = document.createElement('div');
        feedItem.className = 'feed-item new';
        feedItem.innerHTML = `
            <span class="timestamp">${timestamp}</span>
            <span class="message">${message}</span>
        `;
        
        // Add to top of feed
        if (feed.firstChild) {
            feed.insertBefore(feedItem, feed.firstChild);
        } else {
            feed.appendChild(feedItem);
        }
        
        // Remove 'new' class after animation
        setTimeout(() => {
            feedItem.classList.remove('new');
        }, 500);
        
        // Keep only last 10 items
        while (feed.children.length > 10) {
            feed.removeChild(feed.lastChild);
        }
    }
    
    playSound(type) {
        // Simulate sound effects with visual feedback
        const body = document.body;
        
        switch(type) {
            case 'select':
                body.style.filter = 'brightness(1.1)';
                setTimeout(() => body.style.filter = 'brightness(1)', 50);
                break;
            case 'achievement':
                body.style.filter = 'hue-rotate(30deg)';
                setTimeout(() => body.style.filter = 'hue-rotate(0deg)', 200);
                break;
            case 'levelup':
                body.classList.add('glitch');
                setTimeout(() => body.classList.remove('glitch'), 500);
                break;
        }
    }
    
    // Keyboard shortcuts
    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case '1':
                case '2':
                case '3':
                    this.selectMission(parseInt(e.key));
                    break;
                case 'd':
                    this.handleQuickAction('deploy');
                    break;
                case 'i':
                    this.handleQuickAction('inventory');
                    break;
                case 'n':
                    document.querySelector('.access-button').click();
                    break;
                case ' ':
                    e.preventDefault();
                    this.simulateXPGain(Math.floor(Math.random() * 100) + 50);
                    break;
            }
        });
    }
}

// Initialize HUD when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const hud = new EducationHUD();
    hud.initKeyboardShortcuts();
    
    // Add mouse tracking for crosshair
    document.addEventListener('mousemove', (e) => {
        const crosshair = document.querySelector('.crosshair');
        crosshair.style.left = e.clientX + 'px';
        crosshair.style.top = e.clientY + 'px';
    });
    
    // Easter egg: Konami code
    let konamiCode = [];
    const konamiPattern = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
    
    document.addEventListener('keydown', (e) => {
        konamiCode.push(e.key);
        konamiCode = konamiCode.slice(-10);
        
        if (konamiCode.join(',') === konamiPattern.join(',')) {
            hud.showAchievement("Secret Agent", "Discovered the Konami Code", 1337);
            hud.streakMultiplier = 10;
            document.getElementById('streakMultiplier').textContent = 'x10';
            document.body.style.filter = 'hue-rotate(180deg)';
            setTimeout(() => document.body.style.filter = 'hue-rotate(0deg)', 1000);
        }
    });
    
    // Performance optimization: Reduce animations on low FPS
    let lastTime = performance.now();
    let fps = 60;
    
    function checkPerformance() {
        const currentTime = performance.now();
        const delta = currentTime - lastTime;
        fps = 1000 / delta;
        lastTime = currentTime;
        
        if (fps < 30) {
            document.body.classList.add('reduce-motion');
        } else {
            document.body.classList.remove('reduce-motion');
        }
        
        requestAnimationFrame(checkPerformance);
    }
    
    checkPerformance();
});

// Add CSS for reduced motion
const style = document.createElement('style');
style.textContent = `
    .reduce-motion * {
        animation-duration: 0.1s !important;
        transition-duration: 0.1s !important;
    }
`;
document.head.appendChild(style);