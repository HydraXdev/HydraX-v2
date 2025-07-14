/**
 * BITTEN Animated Achievement Unlock System
 * Advanced particle effects and celebration animations for achievement unlocks
 * Military-themed with 60fps performance optimization
 */

class BittenAchievementAnimator {
    constructor() {
        this.particleSystems = new Map();
        this.audioContext = null;
        this.isInitialized = false;
        this.canvas = null;
        this.ctx = null;
        
        // Achievement tier configurations
        this.tierConfigs = {
            bronze: {
                particles: 50,
                colors: ['#CD7F32', '#B8860B', '#DAA520'],
                duration: 3000,
                effects: ['sparkle', 'glow'],
                sound: 'achievement_bronze'
            },
            silver: {
                particles: 75,
                colors: ['#C0C0C0', '#A8A8A8', '#E5E5E5'],
                duration: 4000,
                effects: ['sparkle', 'glow', 'shimmer'],
                sound: 'achievement_silver'
            },
            gold: {
                particles: 100,
                colors: ['#FFD700', '#FFA500', '#FFFF00'],
                duration: 5000,
                effects: ['sparkle', 'glow', 'shimmer', 'burst'],
                sound: 'achievement_gold'
            },
            platinum: {
                particles: 150,
                colors: ['#E5E4E2', '#FFFFFF', '#B0C4DE'],
                duration: 6000,
                effects: ['sparkle', 'glow', 'shimmer', 'burst', 'wave'],
                sound: 'achievement_platinum'
            },
            diamond: {
                particles: 200,
                colors: ['#00FFFF', '#87CEEB', '#B0E0E6'],
                duration: 7000,
                effects: ['sparkle', 'glow', 'shimmer', 'burst', 'wave', 'diamond'],
                sound: 'achievement_diamond'
            },
            master: {
                particles: 300,
                colors: ['#FF00FF', '#9400D3', '#8A2BE2', '#4B0082'],
                duration: 8000,
                effects: ['sparkle', 'glow', 'shimmer', 'burst', 'wave', 'diamond', 'legendary'],
                sound: 'achievement_master'
            }
        };

        this.init();
    }

    async init() {
        // Initialize audio context
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.warn('Audio context not available');
        }

        // Create canvas for particle effects
        this.createCanvas();
        
        // Load sound effects
        await this.loadSoundEffects();
        
        this.isInitialized = true;
    }

    createCanvas() {
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'achievement-particles';
        this.canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            pointer-events: none;
            z-index: 9999;
        `;
        this.ctx = this.canvas.getContext('2d');
        this.resizeCanvas();
        
        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    async loadSoundEffects() {
        const sounds = [
            'achievement_bronze', 'achievement_silver', 'achievement_gold',
            'achievement_platinum', 'achievement_diamond', 'achievement_master'
        ];

        for (const sound of sounds) {
            try {
                // In production, load actual audio files
                // For now, create synthetic sounds
                this.createSyntheticSound(sound);
            } catch (e) {
                console.warn(`Failed to load sound: ${sound}`);
            }
        }
    }

    createSyntheticSound(name) {
        if (!this.audioContext) return;

        const frequencies = {
            achievement_bronze: [220, 330],
            achievement_silver: [330, 440],
            achievement_gold: [440, 550],
            achievement_platinum: [550, 660],
            achievement_diamond: [660, 770],
            achievement_master: [770, 880]
        };

        // Store frequency for later use
        this[name] = frequencies[name] || [440, 550];
    }

    /**
     * Trigger achievement unlock animation
     * @param {Object} achievement - Achievement data
     * @param {string} achievement.tier - Achievement tier (bronze, silver, gold, etc.)
     * @param {string} achievement.title - Achievement title
     * @param {string} achievement.description - Achievement description
     * @param {string} achievement.icon - Achievement icon URL
     * @param {number} achievement.xp - XP reward
     */
    async unlockAchievement(achievement) {
        if (!this.isInitialized) {
            await this.init();
        }

        const config = this.tierConfigs[achievement.tier] || this.tierConfigs.bronze;
        
        // Play sound effect
        this.playSound(config.sound);
        
        // Show achievement modal
        this.showAchievementModal(achievement, config);
        
        // Create particle system
        this.createParticleSystem(achievement, config);
        
        // Trigger haptic feedback if available
        this.triggerHapticFeedback(achievement.tier);
        
        // Share to squad if enabled
        if (achievement.shareToSquad) {
            this.shareToSquad(achievement);
        }
    }

    showAchievementModal(achievement, config) {
        const modal = document.createElement('div');
        modal.className = `achievement-modal tier-${achievement.tier}`;
        modal.innerHTML = `
            <div class="achievement-content">
                <div class="achievement-glow"></div>
                <div class="achievement-icon">
                    <img src="${achievement.icon}" alt="${achievement.title}">
                    <div class="icon-burst"></div>
                </div>
                <div class="achievement-details">
                    <h2 class="achievement-title">${achievement.title}</h2>
                    <p class="achievement-description">${achievement.description}</p>
                    <div class="achievement-reward">
                        <span class="xp-icon">🏆</span>
                        <span class="xp-amount">+${achievement.xp} XP</span>
                    </div>
                </div>
                <div class="achievement-actions">
                    <button class="share-btn" onclick="this.closest('.achievement-modal').dispatchEvent(new CustomEvent('share'))">
                        Share to Squad
                    </button>
                    <button class="close-btn" onclick="this.closest('.achievement-modal').remove()">
                        Continue
                    </button>
                </div>
            </div>
        `;

        // Add event listeners
        modal.addEventListener('share', () => this.shareToSquad(achievement));
        
        // Auto-remove after duration
        setTimeout(() => {
            if (modal.parentNode) {
                modal.style.opacity = '0';
                setTimeout(() => modal.remove(), 500);
            }
        }, config.duration);

        document.body.appendChild(modal);
        
        // Trigger entrance animation
        requestAnimationFrame(() => {
            modal.classList.add('show');
        });
    }

    createParticleSystem(achievement, config) {
        if (!this.canvas.parentNode) {
            document.body.appendChild(this.canvas);
        }

        const particles = [];
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;

        // Create particles
        for (let i = 0; i < config.particles; i++) {
            particles.push({
                x: centerX + (Math.random() - 0.5) * 100,
                y: centerY + (Math.random() - 0.5) * 100,
                vx: (Math.random() - 0.5) * 10,
                vy: (Math.random() - 0.5) * 10,
                size: Math.random() * 8 + 2,
                color: config.colors[Math.floor(Math.random() * config.colors.length)],
                life: 1.0,
                decay: Math.random() * 0.02 + 0.005,
                type: config.effects[Math.floor(Math.random() * config.effects.length)]
            });
        }

        this.animateParticles(particles, config.duration);
    }

    animateParticles(particles, duration) {
        const startTime = Date.now();
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            
            if (elapsed > duration && particles.length === 0) {
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                return;
            }

            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

            // Update and draw particles
            for (let i = particles.length - 1; i >= 0; i--) {
                const particle = particles[i];
                
                // Update position
                particle.x += particle.vx;
                particle.y += particle.vy;
                particle.vy += 0.1; // gravity
                particle.life -= particle.decay;

                // Remove dead particles
                if (particle.life <= 0) {
                    particles.splice(i, 1);
                    continue;
                }

                // Draw particle based on type
                this.drawParticle(particle);
            }

            requestAnimationFrame(animate);
        };

        animate();
    }

    drawParticle(particle) {
        const alpha = particle.life;
        this.ctx.save();
        this.ctx.globalAlpha = alpha;

        switch (particle.type) {
            case 'sparkle':
                this.drawSparkle(particle);
                break;
            case 'glow':
                this.drawGlow(particle);
                break;
            case 'shimmer':
                this.drawShimmer(particle);
                break;
            case 'burst':
                this.drawBurst(particle);
                break;
            case 'wave':
                this.drawWave(particle);
                break;
            case 'diamond':
                this.drawDiamond(particle);
                break;
            case 'legendary':
                this.drawLegendary(particle);
                break;
            default:
                this.drawDefault(particle);
        }

        this.ctx.restore();
    }

    drawSparkle(particle) {
        this.ctx.fillStyle = particle.color;
        this.ctx.beginPath();
        this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Add sparkle effect
        this.ctx.strokeStyle = '#FFFFFF';
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        this.ctx.moveTo(particle.x - particle.size, particle.y);
        this.ctx.lineTo(particle.x + particle.size, particle.y);
        this.ctx.moveTo(particle.x, particle.y - particle.size);
        this.ctx.lineTo(particle.x, particle.y + particle.size);
        this.ctx.stroke();
    }

    drawGlow(particle) {
        const gradient = this.ctx.createRadialGradient(
            particle.x, particle.y, 0,
            particle.x, particle.y, particle.size * 2
        );
        gradient.addColorStop(0, particle.color);
        gradient.addColorStop(1, 'transparent');
        
        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.arc(particle.x, particle.y, particle.size * 2, 0, Math.PI * 2);
        this.ctx.fill();
    }

    drawShimmer(particle) {
        this.ctx.fillStyle = particle.color;
        this.ctx.save();
        this.ctx.translate(particle.x, particle.y);
        this.ctx.rotate(Date.now() * 0.01);
        this.ctx.fillRect(-particle.size, -1, particle.size * 2, 2);
        this.ctx.fillRect(-1, -particle.size, 2, particle.size * 2);
        this.ctx.restore();
    }

    drawBurst(particle) {
        this.ctx.strokeStyle = particle.color;
        this.ctx.lineWidth = 2;
        for (let i = 0; i < 8; i++) {
            const angle = (Math.PI * 2 * i) / 8;
            this.ctx.beginPath();
            this.ctx.moveTo(particle.x, particle.y);
            this.ctx.lineTo(
                particle.x + Math.cos(angle) * particle.size,
                particle.y + Math.sin(angle) * particle.size
            );
            this.ctx.stroke();
        }
    }

    drawWave(particle) {
        this.ctx.strokeStyle = particle.color;
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        this.ctx.stroke();
        
        this.ctx.beginPath();
        this.ctx.arc(particle.x, particle.y, particle.size * 1.5, 0, Math.PI * 2);
        this.ctx.stroke();
    }

    drawDiamond(particle) {
        this.ctx.fillStyle = particle.color;
        this.ctx.beginPath();
        this.ctx.moveTo(particle.x, particle.y - particle.size);
        this.ctx.lineTo(particle.x + particle.size, particle.y);
        this.ctx.lineTo(particle.x, particle.y + particle.size);
        this.ctx.lineTo(particle.x - particle.size, particle.y);
        this.ctx.closePath();
        this.ctx.fill();
        
        // Add diamond shine
        this.ctx.strokeStyle = '#FFFFFF';
        this.ctx.lineWidth = 1;
        this.ctx.stroke();
    }

    drawLegendary(particle) {
        // Rainbow effect for legendary
        const hue = (Date.now() * 0.5 + particle.x + particle.y) % 360;
        this.ctx.fillStyle = `hsl(${hue}, 100%, 50%)`;
        
        this.ctx.beginPath();
        this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Add legendary aura
        const gradient = this.ctx.createRadialGradient(
            particle.x, particle.y, 0,
            particle.x, particle.y, particle.size * 3
        );
        gradient.addColorStop(0, `hsla(${hue}, 100%, 70%, 0.8)`);
        gradient.addColorStop(1, 'transparent');
        
        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.arc(particle.x, particle.y, particle.size * 3, 0, Math.PI * 2);
        this.ctx.fill();
    }

    drawDefault(particle) {
        this.ctx.fillStyle = particle.color;
        this.ctx.beginPath();
        this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        this.ctx.fill();
    }

    playSound(soundName) {
        if (!this.audioContext) return;

        try {
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            const frequencies = this[soundName] || [440, 550];
            
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            oscillator.frequency.setValueAtTime(frequencies[0], this.audioContext.currentTime);
            oscillator.frequency.exponentialRampToValueAtTime(
                frequencies[1], 
                this.audioContext.currentTime + 0.5
            );
            
            gainNode.gain.setValueAtTime(0.3, this.audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.5);
            
            oscillator.start();
            oscillator.stop(this.audioContext.currentTime + 0.5);
        } catch (e) {
            console.warn('Failed to play sound:', e);
        }
    }

    triggerHapticFeedback(tier) {
        if (navigator.vibrate) {
            const patterns = {
                bronze: [100],
                silver: [100, 50, 100],
                gold: [100, 50, 100, 50, 100],
                platinum: [100, 50, 100, 50, 100, 50, 100],
                diamond: [200, 100, 200, 100, 200],
                master: [300, 100, 300, 100, 300, 100, 300]
            };
            
            navigator.vibrate(patterns[tier] || patterns.bronze);
        }

        // Telegram WebApp haptic feedback
        if (window.Telegram?.WebApp?.HapticFeedback) {
            const impacts = {
                bronze: 'light',
                silver: 'medium',
                gold: 'heavy',
                platinum: 'heavy',
                diamond: 'heavy',
                master: 'heavy'
            };
            
            window.Telegram.WebApp.HapticFeedback.impactOccurred(
                impacts[tier] || 'light'
            );
        }
    }

    shareToSquad(achievement) {
        // Share achievement to squad chat
        if (window.squadChat) {
            window.squadChat.shareAchievement(achievement);
        }

        // Post to social feed
        if (window.socialFeed) {
            window.socialFeed.postAchievement(achievement);
        }

        // Share via Telegram if available
        if (window.Telegram?.WebApp?.showPopup) {
            window.Telegram.WebApp.showPopup({
                title: 'Achievement Unlocked!',
                message: `Just unlocked: ${achievement.title}!`,
                buttons: [
                    {type: 'default', text: 'Share'},
                    {type: 'cancel', text: 'Close'}
                ]
            });
        }
    }

    // Preset achievement unlocks for common scenarios
    unlockFirstTrade() {
        this.unlockAchievement({
            tier: 'bronze',
            title: 'First Blood',
            description: 'Executed your first trade',
            icon: '/static/icons/first_trade.png',
            xp: 100,
            shareToSquad: true
        });
    }

    unlockWinStreak(streakLength) {
        const tiers = ['bronze', 'silver', 'gold', 'platinum', 'diamond', 'master'];
        const tierIndex = Math.min(Math.floor(streakLength / 5), tiers.length - 1);
        
        this.unlockAchievement({
            tier: tiers[tierIndex],
            title: `${streakLength}-Win Streak`,
            description: `Won ${streakLength} trades in a row`,
            icon: '/static/icons/win_streak.png',
            xp: streakLength * 50,
            shareToSquad: true
        });
    }

    unlockProfitMilestone(profitAmount) {
        let tier = 'bronze';
        if (profitAmount >= 10000) tier = 'master';
        else if (profitAmount >= 5000) tier = 'diamond';
        else if (profitAmount >= 1000) tier = 'platinum';
        else if (profitAmount >= 500) tier = 'gold';
        else if (profitAmount >= 100) tier = 'silver';
        
        this.unlockAchievement({
            tier: tier,
            title: 'Profit Milestone',
            description: `Earned $${profitAmount} in total profit`,
            icon: '/static/icons/profit_milestone.png',
            xp: Math.floor(profitAmount / 10),
            shareToSquad: true
        });
    }
}

// Global instance
window.achievementAnimator = new BittenAchievementAnimator();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BittenAchievementAnimator;
}