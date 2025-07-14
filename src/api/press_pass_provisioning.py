#!/usr/bin/env python3
"""
BITTEN Press Pass Provisioning System
Handles email capture, clone creation, and user onboarding flow
"""

from flask import Flask, request, jsonify, session
import json
import uuid
import time
from datetime import datetime, timedelta
import logging
# Email imports commented out for now - implement with your email service
# import smtplib
# from email.mime.text import MimeText
# from email.mime.multipart import MimeMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('PressPassProvisioning')

class PressPassManager:
    def __init__(self, app):
        self.app = app
        self.setup_routes()
        
        # Press Pass storage (replace with real database)
        self.active_passes = {}
        self.user_emails = {}
        self.clone_assignments = {}
        
        logger.info("Press Pass Manager initialized")
        
    def setup_routes(self):
        """Setup Press Pass API routes"""
        
        @self.app.route('/api/provision-press-pass', methods=['POST'])
        def provision_press_pass():
            return self.handle_provision_press_pass()
            
        @self.app.route('/api/press-pass-status/<pass_id>', methods=['GET'])
        def get_pass_status(pass_id):
            return self.handle_get_pass_status(pass_id)
            
        @self.app.route('/api/activate-telegram/<pass_id>', methods=['POST'])
        def activate_telegram(pass_id):
            return self.handle_activate_telegram(pass_id)
            
        @self.app.route('/api/extend-press-pass/<pass_id>', methods=['POST'])
        def extend_press_pass(pass_id):
            return self.handle_extend_press_pass(pass_id)
    
    def handle_provision_press_pass(self):
        """Provision a new Press Pass from email capture"""
        try:
            data = request.get_json()
            email = data.get('email', '').strip().lower()
            source = data.get('source', 'unknown')
            
            # Validate email
            if not email or '@' not in email:
                return jsonify({'error': 'Valid email required'}), 400
            
            # Check if email already has active pass
            existing_pass = self.get_active_pass_by_email(email)
            if existing_pass:
                logger.info(f"Email {email} already has active pass: {existing_pass['pass_id']}")
                return jsonify({
                    'success': True,
                    'press_pass_id': existing_pass['pass_id'],
                    'status': 'existing',
                    'message': 'Welcome back! Your Press Pass is still active.',
                    'expires_at': existing_pass['expires_at']
                })
            
            # Generate new Press Pass
            pass_id = self.generate_pass_id()
            clone_id = self.assign_mt5_clone()
            
            # Create Press Pass record
            press_pass = {
                'pass_id': pass_id,
                'email': email,
                'clone_id': clone_id,
                'source': source,
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=12)).isoformat(),
                'telegram_activated': False,
                'trades_made': 0,
                'xp_earned': 15  # From Bit's first trade demo
            }
            
            # Store in system
            self.active_passes[pass_id] = press_pass
            self.user_emails[email] = pass_id
            self.clone_assignments[clone_id] = pass_id
            
            # Send welcome email
            self.send_welcome_email(email, press_pass)
            
            # Log metrics
            logger.info(f"Press Pass provisioned: {pass_id} for {email} (source: {source})")
            
            return jsonify({
                'success': True,
                'press_pass_id': pass_id,
                'clone_id': clone_id,
                'status': 'provisioned',
                'message': 'Press Pass activated! Terminal spinning up...',
                'expires_at': press_pass['expires_at'],
                'telegram_bot_link': f"https://t.me/Bitten_Commander_bot?start=presspass_{pass_id}"
            })
            
        except Exception as e:
            logger.error(f"Press Pass provisioning error: {e}")
            return jsonify({'error': 'Provisioning failed'}), 500
    
    def handle_get_pass_status(self, pass_id):
        """Get Press Pass status and details"""
        try:
            if pass_id not in self.active_passes:
                return jsonify({'error': 'Press Pass not found'}), 404
            
            press_pass = self.active_passes[pass_id]
            
            # Check if expired
            expires_at = datetime.fromisoformat(press_pass['expires_at'])
            is_expired = datetime.now() > expires_at
            
            if is_expired:
                press_pass['status'] = 'expired'
            
            # Calculate time remaining
            time_remaining = max(0, (expires_at - datetime.now()).total_seconds())
            hours_remaining = int(time_remaining // 3600)
            minutes_remaining = int((time_remaining % 3600) // 60)
            
            return jsonify({
                'success': True,
                'press_pass': {
                    'id': pass_pass['pass_id'],
                    'status': press_pass['status'],
                    'email': press_pass['email'],
                    'clone_id': press_pass['clone_id'],
                    'created_at': press_pass['created_at'],
                    'expires_at': press_pass['expires_at'],
                    'time_remaining': f"{hours_remaining}h {minutes_remaining}m",
                    'telegram_activated': press_pass['telegram_activated'],
                    'trades_made': press_pass['trades_made'],
                    'xp_earned': press_pass['xp_earned']
                }
            })
            
        except Exception as e:
            logger.error(f"Get pass status error: {e}")
            return jsonify({'error': 'Status check failed'}), 500
    
    def handle_activate_telegram(self, pass_id):
        """Activate Telegram integration for Press Pass"""
        try:
            if pass_id not in self.active_passes:
                return jsonify({'error': 'Press Pass not found'}), 404
            
            press_pass = self.active_passes[pass_id]
            telegram_user_id = request.get_json().get('telegram_user_id')
            
            # Update Press Pass with Telegram info
            press_pass['telegram_activated'] = True
            press_pass['telegram_user_id'] = telegram_user_id
            press_pass['telegram_activated_at'] = datetime.now().isoformat()
            
            # Add to Terminal group (would integrate with actual Telegram bot)
            terminal_invite_link = self.add_to_terminal_group(telegram_user_id, press_pass)
            
            logger.info(f"Telegram activated for Press Pass {pass_id}")
            
            return jsonify({
                'success': True,
                'message': 'Welcome to The Terminal!',
                'terminal_invite_link': terminal_invite_link,
                'squad_members': 1247,  # Mock data
                'active_trades': 23,    # Mock data
                'your_rank': 'NIBBLER 01'
            })
            
        except Exception as e:
            logger.error(f"Telegram activation error: {e}")
            return jsonify({'error': 'Telegram activation failed'}), 500
    
    def handle_extend_press_pass(self, pass_id):
        """Extend Press Pass (for testing or special cases)"""
        try:
            if pass_id not in self.active_passes:
                return jsonify({'error': 'Press Pass not found'}), 404
            
            press_pass = self.active_passes[pass_id]
            extension_hours = request.get_json().get('hours', 12)
            
            # Extend expiration
            current_expires = datetime.fromisoformat(press_pass['expires_at'])
            new_expires = current_expires + timedelta(hours=extension_hours)
            press_pass['expires_at'] = new_expires.isoformat()
            
            logger.info(f"Press Pass {pass_id} extended by {extension_hours} hours")
            
            return jsonify({
                'success': True,
                'message': f'Press Pass extended by {extension_hours} hours',
                'new_expires_at': press_pass['expires_at']
            })
            
        except Exception as e:
            logger.error(f"Extend pass error: {e}")
            return jsonify({'error': 'Extension failed'}), 500
    
    def generate_pass_id(self):
        """Generate unique Press Pass ID"""
        timestamp = int(time.time())
        random_suffix = uuid.uuid4().hex[:4].upper()
        return f"PRESS-{timestamp}-{random_suffix}"
    
    def assign_mt5_clone(self):
        """Assign available MT5 clone terminal"""
        # In real implementation, this would:
        # 1. Find available clone from pool
        # 2. Spin up new instance if needed
        # 3. Configure with demo broker
        # 4. Return clone identifier
        
        clone_number = len(self.clone_assignments) + 1
        return f"CLONE-DEMO-{clone_number:04d}"
    
    def get_active_pass_by_email(self, email):
        """Check if email has existing active Pass Pass"""
        if email in self.user_emails:
            pass_id = self.user_emails[email]
            if pass_id in self.active_passes:
                press_pass = self.active_passes[pass_id]
                expires_at = datetime.fromisoformat(press_pass['expires_at'])
                if datetime.now() < expires_at:
                    return press_pass
        return None
    
    def send_welcome_email(self, email, press_pass):
        """Send welcome email with Press Pass details"""
        try:
            subject = "🎟️ Your BITTEN Press Pass Is Active!"
            
            body = f"""
🎖️ Welcome to BITTEN, Operator!

Your Press Pass is now ACTIVE and your $50,000 demo terminal is spinning up.

PRESS PASS DETAILS:
━━━━━━━━━━━━━━━━━━━━
🆔 Pass ID: {press_pass['pass_id']}
🖥️ Terminal: {press_pass['clone_id']}
⏰ Expires: {press_pass['expires_at'][:16]} UTC
💰 Demo Balance: $50,000
🎯 XP Earned: {press_pass['xp_earned']} (from your first trade with Bit!)

NEXT STEPS:
━━━━━━━━━━━━━━━━━━━━
1. 🐾 Meet your AI squad in Telegram:
   {f"https://t.me/Bitten_Commander_bot?start=presspass_{press_pass['pass_id']}"}

2. 💬 Join The Terminal (live trading room):
   Where you'll see live trades and earn XP

3. 🎮 Complete your first missions:
   Guided by Drill Sergeant, Doc, Nexus & Overwatch

IMPORTANT NOTES:
━━━━━━━━━━━━━━━━━━━━
⚠️ Your Press Pass expires in 12 hours
🎯 Perfect for testing the system
🚀 Upgrade anytime to keep your progress
💪 XP transfers when you go live

Ready to join 1,247 active operators?
Click the Telegram link above to meet your squad!

See you in The Terminal,
🐾 Bit & The BITTEN Team

---
Questions? Reply to this email.
Unsubscribe: Not recommended (you'll miss the action!)
            """
            
            # In real implementation, send via SMTP or email service
            logger.info(f"Welcome email sent to {email}")
            
            # Mock email sending for now
            return True
            
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            return False
    
    def add_to_terminal_group(self, telegram_user_id, press_pass):
        """Add user to Terminal Telegram group"""
        try:
            # In real implementation, this would:
            # 1. Use Telegram Bot API to add user to group
            # 2. Set user permissions (read-only initially)
            # 3. Send welcome message from squad
            # 4. Return group invite link
            
            # Mock implementation
            terminal_invite = f"https://t.me/+BITTENTerminal_{press_pass['pass_id'][:8]}"
            
            logger.info(f"User {telegram_user_id} added to Terminal group")
            return terminal_invite
            
        except Exception as e:
            logger.error(f"Terminal group add error: {e}")
            return "https://t.me/Bitten_Commander_bot"
    
    def cleanup_expired_passes(self):
        """Clean up expired Press Passes (run as background task)"""
        try:
            current_time = datetime.now()
            expired_passes = []
            
            for pass_id, press_pass in self.active_passes.items():
                expires_at = datetime.fromisoformat(press_pass['expires_at'])
                if current_time > expires_at:
                    expired_passes.append(pass_id)
            
            for pass_id in expired_passes:
                press_pass = self.active_passes[pass_id]
                
                # Release MT5 clone
                if press_pass['clone_id'] in self.clone_assignments:
                    del self.clone_assignments[press_pass['clone_id']]
                
                # Remove from email mapping
                if press_pass['email'] in self.user_emails:
                    del self.user_emails[press_pass['email']]
                
                # Mark as expired but keep record for analytics
                press_pass['status'] = 'expired'
                press_pass['expired_at'] = current_time.isoformat()
                
                logger.info(f"Press Pass {pass_id} expired and cleaned up")
            
            return len(expired_passes)
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return 0
    
    def get_analytics_summary(self):
        """Get Press Pass analytics for admin dashboard"""
        try:
            total_passes = len(self.active_passes)
            active_count = len([p for p in self.active_passes.values() if p['status'] == 'active'])
            telegram_activated = len([p for p in self.active_passes.values() if p['telegram_activated']])
            
            # Calculate conversion rates
            email_to_telegram = (telegram_activated / total_passes * 100) if total_passes > 0 else 0
            
            return {
                'total_press_passes': total_passes,
                'active_passes': active_count,
                'telegram_activations': telegram_activated,
                'conversion_rate': round(email_to_telegram, 1),
                'active_clones': len(self.clone_assignments),
                'last_24h_signups': len([p for p in self.active_passes.values() 
                                       if (datetime.now() - datetime.fromisoformat(p['created_at'])).days < 1])
            }
            
        except Exception as e:
            logger.error(f"Analytics error: {e}")
            return {}

# Integration function for main webapp
def register_press_pass_api(app):
    """Register Press Pass API with Flask app"""
    manager = PressPassManager(app)
    
    @app.route('/api/press-pass-analytics')
    def get_analytics():
        """Admin endpoint for Press Pass analytics"""
        return jsonify(manager.get_analytics_summary())
    
    # Background cleanup task (would be run via cron in production)
    @app.route('/api/cleanup-expired-passes', methods=['POST'])
    def cleanup_expired():
        """Manual cleanup endpoint (for testing)"""
        cleaned = manager.cleanup_expired_passes()
        return jsonify({'cleaned_passes': cleaned})
    
    logger.info("Press Pass API registered")
    return manager

if __name__ == "__main__":
    # Test server
    app = Flask(__name__)
    app.secret_key = 'press_pass_secret_key'
    
    register_press_pass_api(app)
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'Press Pass API operational'})
    
    app.run(debug=True, port=5002)