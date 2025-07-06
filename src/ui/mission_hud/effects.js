/**
 * Mission HUD Effects System
 * Provides immersive audio/visual effects for the trading interface
 */

export class MissionHUDEffects {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.explosions = [];
        this.glitchElements = new Set();
        this.audioContext = null;
        this.hapticSupported = 'vibrate' in navigator;
        this.animationFrame = null;
        this.isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        // Performance settings
        this.maxParticles = this.isMobile() ? 50 : 100;
        this.maxExplosions = this.isMobile() ? 3 : 5;
        
        // Tier-specific configurations
        this.tierEffects = {
            1: { color: '#00ffff', intensity: 0.6, particleCount: 20 },
            2: { color: '#00ff88', intensity: 0.7, particleCount: 30 },
            3: { color: '#ffaa00', intensity: 0.8, particleCount: 40 },
            4: { color: '#ff00ff', intensity: 0.9, particleCount: 50 },
            5: { color: '#ff0066', intensity: 1.0, particleCount: 60 }
        };
        
        this.init();
    }
    
    init() {
        // Create off-screen canvas for effects
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'effects-canvas';
        this.canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1000;
        `;
        
        this.ctx = this.canvas.getContext('2d');
        this.resizeCanvas();
        
        // Initialize audio context on first user interaction
        document.addEventListener('click', () => {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
        }, { once: true });
        
        // Handle resize
        window.addEventListener('resize', () => this.resizeCanvas());
        
        // Start animation loop
        if (!this.isReducedMotion) {
            this.animate();
        }
    }
    
    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }
    
    // Glitch effect for new entries
    glitchEntry(element, tier = 1) {
        if (this.isReducedMotion) {
            element.classList.add('entry-appear');
            return;
        }
        
        const config = this.tierEffects[tier];
        const duration = 300 + (tier * 50);
        
        element.classList.add('glitch-effect');
        this.glitchElements.add(element);
        
        // Apply glitch CSS animation
        element.style.cssText = `
            animation: glitch ${duration}ms steps(2, end);
            --glitch-color: ${config.color};
        `;
        
        // Create glitch frames
        let glitchFrames = 0;
        const glitchInterval = setInterval(() => {
            if (glitchFrames++ > 10) {
                clearInterval(glitchInterval);
                element.classList.remove('glitch-effect');
                this.glitchElements.delete(element);
                return;
            }
            
            // Random transform and opacity
            const x = (Math.random() - 0.5) * 10;
            const y = (Math.random() - 0.5) * 10;
            const skew = (Math.random() - 0.5) * 5;
            
            element.style.transform = `translate(${x}px, ${y}px) skewX(${skew}deg)`;
            element.style.opacity = Math.random() > 0.1 ? '1' : '0.5';
        }, 30);
        
        // Play glitch sound
        this.playGlitchSound(tier);
        
        // Trigger haptic feedback
        this.triggerHaptic(10 * tier);
    }
    
    // Explosion animation for trade execution
    explodeTradeExecution(x, y, tier = 1, amount = 0) {
        if (this.isReducedMotion) return;
        
        const config = this.tierEffects[tier];
        const explosion = {
            x,
            y,
            radius: 0,
            maxRadius: 50 + (tier * 20),
            opacity: 1,
            color: config.color,
            particles: [],
            shockwave: true,
            tier
        };
        
        // Create explosion particles
        const particleCount = Math.min(config.particleCount, this.maxParticles - this.particles.length);
        for (let i = 0; i < particleCount; i++) {
            const angle = (Math.PI * 2 * i) / particleCount;
            const speed = 2 + Math.random() * 4 * config.intensity;
            
            explosion.particles.push({
                x,
                y,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                life: 1,
                size: 2 + Math.random() * 3,
                color: config.color
            });
        }
        
        // Manage explosion count
        if (this.explosions.length >= this.maxExplosions) {
            this.explosions.shift();
        }
        
        this.explosions.push(explosion);
        
        // Screen shake for large trades
        if (tier >= 3) {
            this.screenShake(tier * 2, 200);
        }
        
        // Play explosion sound
        this.playExplosionSound(tier, amount);
        
        // Strong haptic feedback
        this.triggerHaptic(50 + (tier * 20));
    }
    
    // Particle system for XP gains
    spawnXPParticles(x, y, xpAmount, tier = 1) {
        if (this.isReducedMotion) return;
        
        const config = this.tierEffects[tier];
        const particleCount = Math.min(
            Math.floor(xpAmount / 10) + 5,
            this.maxParticles - this.particles.length
        );
        
        for (let i = 0; i < particleCount; i++) {
            const particle = {
                x: x + (Math.random() - 0.5) * 20,
                y: y + (Math.random() - 0.5) * 20,
                vx: (Math.random() - 0.5) * 2,
                vy: -2 - Math.random() * 2,
                life: 1,
                maxLife: 1,
                size: 3 + Math.random() * 2,
                color: config.color,
                type: 'xp',
                value: Math.floor(xpAmount / particleCount),
                glow: true
            };
            
            this.particles.push(particle);
        }
        
        // Play XP sound
        this.playXPSound(tier);
        
        // Light haptic feedback
        this.triggerHaptic(20);
    }
    
    // Warning animation for low TCS
    warningLowTCS(tcsPercentage) {
        const warningLevel = tcsPercentage < 10 ? 'critical' : 'low';
        const pulseSpeed = warningLevel === 'critical' ? 100 : 200;
        
        // Create warning overlay
        const warning = document.createElement('div');
        warning.className = `tcs-warning tcs-warning-${warningLevel}`;
        warning.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            z-index: 999;
            background: radial-gradient(ellipse at center, 
                transparent 0%, 
                transparent 40%, 
                rgba(255, 0, 0, ${warningLevel === 'critical' ? 0.3 : 0.1}) 100%
            );
            animation: pulse ${pulseSpeed}ms ease-in-out infinite;
        `;
        
        document.body.appendChild(warning);
        
        // Flash border
        const flashCount = warningLevel === 'critical' ? 5 : 3;
        let flashes = 0;
        const flashInterval = setInterval(() => {
            if (flashes++ >= flashCount) {
                clearInterval(flashInterval);
                warning.remove();
                return;
            }
            
            warning.style.opacity = flashes % 2 ? '1' : '0.5';
        }, pulseSpeed);
        
        // Play warning sound
        this.playWarningSound(warningLevel);
        
        // Haptic pattern for warning
        if (warningLevel === 'critical') {
            this.triggerHapticPattern([100, 50, 100, 50, 100]);
        } else {
            this.triggerHapticPattern([50, 100, 50]);
        }
    }
    
    // Screen shake effect
    screenShake(intensity, duration) {
        if (this.isReducedMotion) return;
        
        const startTime = Date.now();
        const shakeElement = document.querySelector('.mission-hud-container') || document.body;
        
        const shake = () => {
            const elapsed = Date.now() - startTime;
            if (elapsed > duration) {
                shakeElement.style.transform = '';
                return;
            }
            
            const decay = 1 - (elapsed / duration);
            const x = (Math.random() - 0.5) * intensity * decay;
            const y = (Math.random() - 0.5) * intensity * decay;
            
            shakeElement.style.transform = `translate(${x}px, ${y}px)`;
            requestAnimationFrame(shake);
        };
        
        shake();
    }
    
    // Haptic feedback
    triggerHaptic(duration) {
        if (this.hapticSupported && !this.isReducedMotion) {
            navigator.vibrate(duration);
        }
    }
    
    triggerHapticPattern(pattern) {
        if (this.hapticSupported && !this.isReducedMotion) {
            navigator.vibrate(pattern);
        }
    }
    
    // Audio effects
    playCashRegisterSound(intensity = 1.0) {
        if (!this.audioContext || this.isReducedMotion) return;
        
        const now = this.audioContext.currentTime;
        
        // Bell sound (ka-ching!)
        const bellOsc = this.audioContext.createOscillator();
        const bellGain = this.audioContext.createGain();
        bellOsc.frequency.setValueAtTime(2800, now);
        bellOsc.frequency.exponentialRampToValueAtTime(2400, now + 0.1);
        bellGain.gain.setValueAtTime(0.8 * intensity, now);
        bellGain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
        
        bellOsc.connect(bellGain);
        bellGain.connect(this.audioContext.destination);
        bellOsc.start(now);
        bellOsc.stop(now + 0.3);
        
        // Coin sounds
        for (let i = 0; i < 5; i++) {
            const coinOsc = this.audioContext.createOscillator();
            const coinGain = this.audioContext.createGain();
            const coinFreq = 4000 + Math.random() * 500;
            const startTime = now + (i * 0.05);
            
            coinOsc.frequency.setValueAtTime(coinFreq, startTime);
            coinGain.gain.setValueAtTime(0.6 * intensity, startTime);
            coinGain.gain.exponentialRampToValueAtTime(0.01, startTime + 0.03);
            
            coinOsc.connect(coinGain);
            coinGain.connect(this.audioContext.destination);
            coinOsc.start(startTime);
            coinOsc.stop(startTime + 0.03);
        }
        
        // Cash drawer sound
        const drawerOsc = this.audioContext.createOscillator();
        const drawerGain = this.audioContext.createGain();
        const drawerFilter = this.audioContext.createBiquadFilter();
        
        drawerOsc.type = 'sawtooth';
        drawerOsc.frequency.setValueAtTime(150, now);
        drawerFilter.type = 'lowpass';
        drawerFilter.frequency.setValueAtTime(400, now);
        drawerGain.gain.setValueAtTime(0.4 * intensity, now);
        drawerGain.gain.linearRampToValueAtTime(0, now + 0.2);
        
        drawerOsc.connect(drawerFilter);
        drawerFilter.connect(drawerGain);
        drawerGain.connect(this.audioContext.destination);
        drawerOsc.start(now);
        drawerOsc.stop(now + 0.2);
    }
    
    playTPHitSound() {
        if (!this.audioContext || this.isReducedMotion) return;
        
        const now = this.audioContext.currentTime;
        
        // Rising sweep
        const sweepOsc = this.audioContext.createOscillator();
        const sweepGain = this.audioContext.createGain();
        sweepOsc.frequency.setValueAtTime(400, now);
        sweepOsc.frequency.exponentialRampToValueAtTime(800, now + 0.2);
        sweepGain.gain.setValueAtTime(0.5, now);
        sweepGain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
        
        sweepOsc.connect(sweepGain);
        sweepGain.connect(this.audioContext.destination);
        sweepOsc.start(now);
        sweepOsc.stop(now + 0.3);
        
        // Success chord (C major)
        const chordFreqs = [523, 659, 784, 1047]; // C5, E5, G5, C6
        chordFreqs.forEach((freq, i) => {
            const osc = this.audioContext.createOscillator();
            const gain = this.audioContext.createGain();
            const startTime = now + 0.2 + (i * 0.05);
            
            osc.frequency.setValueAtTime(freq, startTime);
            gain.gain.setValueAtTime(0.3, startTime);
            gain.gain.exponentialRampToValueAtTime(0.01, startTime + 0.5);
            
            osc.connect(gain);
            gain.connect(this.audioContext.destination);
            osc.start(startTime);
            osc.stop(startTime + 0.5);
        });
    }
    
    playGlitchSound(tier) {
        if (!this.audioContext || this.isReducedMotion) return;
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        // Glitch frequency based on tier
        oscillator.frequency.setValueAtTime(200 + (tier * 100), this.audioContext.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(50, this.audioContext.currentTime + 0.1);
        
        gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.1);
        
        oscillator.type = 'square';
        oscillator.start();
        oscillator.stop(this.audioContext.currentTime + 0.1);
    }
    
    playExplosionSound(tier, amount) {
        if (!this.audioContext || this.isReducedMotion) return;
        
        // White noise for explosion
        const bufferSize = this.audioContext.sampleRate * 0.2;
        const buffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
        const data = buffer.getChannelData(0);
        
        for (let i = 0; i < bufferSize; i++) {
            data[i] = (Math.random() - 0.5) * 0.5;
        }
        
        const noise = this.audioContext.createBufferSource();
        const filter = this.audioContext.createBiquadFilter();
        const gainNode = this.audioContext.createGain();
        
        noise.buffer = buffer;
        noise.connect(filter);
        filter.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(1000 + (tier * 500), this.audioContext.currentTime);
        
        gainNode.gain.setValueAtTime(0.2 * (tier / 5), this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.3);
        
        noise.start();
        noise.stop(this.audioContext.currentTime + 0.3);
    }
    
    playXPSound(tier) {
        if (!this.audioContext || this.isReducedMotion) return;
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        // Rising tone for XP
        oscillator.frequency.setValueAtTime(400 + (tier * 50), this.audioContext.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(800 + (tier * 100), this.audioContext.currentTime + 0.2);
        
        gainNode.gain.setValueAtTime(0.05, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.2);
        
        oscillator.type = 'sine';
        oscillator.start();
        oscillator.stop(this.audioContext.currentTime + 0.2);
    }
    
    playWarningSound(level) {
        if (!this.audioContext || this.isReducedMotion) return;
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        if (level === 'critical') {
            // Alarm sound
            oscillator.frequency.setValueAtTime(800, this.audioContext.currentTime);
            oscillator.frequency.setValueAtTime(400, this.audioContext.currentTime + 0.1);
            oscillator.frequency.setValueAtTime(800, this.audioContext.currentTime + 0.2);
            gainNode.gain.setValueAtTime(0.2, this.audioContext.currentTime);
        } else {
            // Warning beep
            oscillator.frequency.setValueAtTime(600, this.audioContext.currentTime);
            gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
        }
        
        oscillator.type = 'square';
        oscillator.start();
        oscillator.stop(this.audioContext.currentTime + 0.3);
    }
    
    // Animation loop
    animate() {
        this.animationFrame = requestAnimationFrame(() => this.animate());
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Update and draw particles
        this.updateParticles();
        
        // Update and draw explosions
        this.updateExplosions();
    }
    
    updateParticles() {
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const particle = this.particles[i];
            
            // Update position
            particle.x += particle.vx;
            particle.y += particle.vy;
            particle.vy += 0.1; // Gravity
            
            // Update life
            particle.life -= 0.02;
            
            // Remove dead particles
            if (particle.life <= 0 || particle.y > this.canvas.height) {
                this.particles.splice(i, 1);
                continue;
            }
            
            // Draw particle
            this.ctx.save();
            this.ctx.globalAlpha = particle.life;
            
            if (particle.glow) {
                // Glow effect
                this.ctx.shadowBlur = 10;
                this.ctx.shadowColor = particle.color;
            }
            
            this.ctx.fillStyle = particle.color;
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size * particle.life, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Draw value for XP particles
            if (particle.type === 'xp' && particle.value) {
                this.ctx.font = '12px monospace';
                this.ctx.fillText(`+${particle.value}`, particle.x + 10, particle.y);
            }
            
            this.ctx.restore();
        }
    }
    
    updateExplosions() {
        for (let i = this.explosions.length - 1; i >= 0; i--) {
            const explosion = this.explosions[i];
            
            // Update explosion
            explosion.radius += 5;
            explosion.opacity -= 0.03;
            
            // Remove finished explosions
            if (explosion.opacity <= 0) {
                this.explosions.splice(i, 1);
                continue;
            }
            
            // Draw shockwave
            if (explosion.shockwave) {
                this.ctx.save();
                this.ctx.globalAlpha = explosion.opacity * 0.5;
                this.ctx.strokeStyle = explosion.color;
                this.ctx.lineWidth = 2;
                this.ctx.beginPath();
                this.ctx.arc(explosion.x, explosion.y, explosion.radius, 0, Math.PI * 2);
                this.ctx.stroke();
                this.ctx.restore();
            }
            
            // Update and draw explosion particles
            for (let j = explosion.particles.length - 1; j >= 0; j--) {
                const particle = explosion.particles[j];
                
                particle.x += particle.vx;
                particle.y += particle.vy;
                particle.vx *= 0.98;
                particle.vy *= 0.98;
                particle.life -= 0.02;
                
                if (particle.life <= 0) {
                    explosion.particles.splice(j, 1);
                    continue;
                }
                
                this.ctx.save();
                this.ctx.globalAlpha = particle.life * explosion.opacity;
                this.ctx.fillStyle = particle.color;
                this.ctx.shadowBlur = 20;
                this.ctx.shadowColor = particle.color;
                this.ctx.beginPath();
                this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                this.ctx.fill();
                this.ctx.restore();
            }
        }
    }
    
    // Cleanup
    destroy() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.remove();
        }
        
        this.particles = [];
        this.explosions = [];
        this.glitchElements.clear();
    }
}

// CSS animations to be injected
export const effectStyles = `
    .effects-canvas {
        mix-blend-mode: screen;
    }
    
    @keyframes glitch {
        0%, 100% {
            text-shadow: 
                0.05em 0 0 var(--glitch-color),
                -0.05em -0.025em 0 rgba(0, 255, 0, 0.75),
                0.025em 0.05em 0 rgba(0, 0, 255, 0.75);
        }
        15% {
            text-shadow: 
                0.05em 0 0 var(--glitch-color),
                -0.05em -0.025em 0 rgba(0, 255, 0, 0.75),
                0.025em 0.05em 0 rgba(0, 0, 255, 0.75);
            transform: translate(2px, 2px);
        }
        30% {
            text-shadow: 
                -0.05em -0.025em 0 var(--glitch-color),
                0.025em 0.025em 0 rgba(0, 255, 0, 0.75),
                -0.05em -0.05em 0 rgba(0, 0, 255, 0.75);
            transform: translate(-2px, -2px);
        }
        45%, 60% {
            text-shadow: 
                -0.05em -0.025em 0 var(--glitch-color),
                -0.025em 0.025em 0 rgba(0, 255, 0, 0.75),
                -0.05em -0.05em 0 rgba(0, 0, 255, 0.75);
            transform: translate(0, 0);
        }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .glitch-effect {
        position: relative;
        animation: glitch 300ms infinite;
    }
    
    .glitch-effect::before,
    .glitch-effect::after {
        content: attr(data-text);
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }
    
    .glitch-effect::before {
        animation: glitch-1 600ms infinite;
        color: var(--glitch-color);
        z-index: -1;
    }
    
    .glitch-effect::after {
        animation: glitch-2 600ms infinite;
        color: rgba(255, 255, 255, 0.5);
        z-index: -2;
    }
    
    @keyframes glitch-1 {
        0%, 100% { clip-path: inset(0 0 0 0); }
        20% { clip-path: inset(1em 0 0.5em 0); }
        40% { clip-path: inset(0.5em 0 1em 0); }
        60% { clip-path: inset(1em 0 0.25em 0); }
        80% { clip-path: inset(0.25em 0 0.75em 0); }
    }
    
    @keyframes glitch-2 {
        0%, 100% { clip-path: inset(0 0 0 0); }
        20% { clip-path: inset(0.5em 0 1em 0); }
        40% { clip-path: inset(1em 0 0.25em 0); }
        60% { clip-path: inset(0.25em 0 0.75em 0); }
        80% { clip-path: inset(0.75em 0 0.5em 0); }
    }
    
    .entry-appear {
        animation: fadeIn 300ms ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .tcs-warning {
        animation: pulse 200ms ease-in-out infinite;
    }
    
    .tcs-warning-critical {
        border: 3px solid rgba(255, 0, 0, 0.8);
        box-shadow: 
            inset 0 0 50px rgba(255, 0, 0, 0.5),
            0 0 20px rgba(255, 0, 0, 0.5);
    }
    
    .tcs-warning-low {
        border: 2px solid rgba(255, 200, 0, 0.6);
        box-shadow: 
            inset 0 0 30px rgba(255, 200, 0, 0.3),
            0 0 10px rgba(255, 200, 0, 0.3);
    }
    
    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
        .glitch-effect,
        .effects-canvas,
        .tcs-warning {
            animation: none !important;
        }
        
        .glitch-effect::before,
        .glitch-effect::after {
            display: none;
        }
    }
`;

// Export singleton instance
export const missionEffects = new MissionHUDEffects();