#!/usr/bin/env python3
"""
HydraX WebApp Onboarding System
Professional-grade MT5 credential injection with cinematic UX
"""

import os
import sys
import json
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from flask import Flask, render_template_string, request, jsonify, redirect, session
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HydraXOnboardingSystem:
    """Complete onboarding system for HydraX WebApp"""
    
    def __init__(self):
        self.project_root = Path("/root/HydraX-v2")
        self.srv_directory = self.project_root / "mt5_server_templates" / "servers"
        self.user_registry_path = self.project_root / "data" / "user_registry_complete.json"
        self.onboarding_log = self.project_root / "logs" / "onboarding_failures.log"
        
        # Ensure directories exist
        self.onboarding_log.parent.mkdir(exist_ok=True)
        
        # Initialize user registry manager
        self._init_user_registry()
    
    def _init_user_registry(self):
        """Initialize user registry manager"""
        try:
            sys.path.append(str(self.project_root / "src" / "bitten_core"))
            from user_registry_manager import UserRegistryManager
            self.user_registry = UserRegistryManager()
            logger.info("✅ User registry manager initialized")
        except ImportError as e:
            logger.error(f"❌ Failed to import UserRegistryManager: {e}")
            self.user_registry = None
    
    def get_available_servers(self) -> List[Dict[str, str]]:
        """Get list of available MT5 server configurations with enhanced parsing"""
        servers = []
        
        try:
            if self.srv_directory.exists():
                logger.info(f"Scanning server directory: {self.srv_directory}")
                
                for srv_file in self.srv_directory.glob("*.srv"):
                    server_config = self._parse_srv_file(srv_file)
                    if server_config:
                        servers.append(server_config)
            
            # Add fallback servers if none found
            if not servers:
                logger.warning("No .srv files found, using fallback servers")
                servers = self._get_fallback_servers()
            
            # Sort servers: Demo first, then Live, alphabetically within each type
            sorted_servers = sorted(servers, key=lambda x: (x['type'] != 'demo', x['display']))
            
            logger.info(f"✅ Loaded {len(sorted_servers)} server configurations")
            for server in sorted_servers:
                logger.info(f"   📡 {server['display']} ({server['type'].upper()})")
            
            return sorted_servers
            
        except Exception as e:
            logger.error(f"❌ Error loading servers: {e}")
            return self._get_fallback_servers()
    
    def _parse_srv_file(self, srv_file: Path) -> Optional[Dict[str, str]]:
        """Parse individual .srv file with enhanced validation"""
        try:
            server_name = srv_file.stem
            
            # Security check: sanitize server name
            if not self._is_safe_server_name(server_name):
                logger.warning(f"⚠️ Skipping potentially unsafe server name: {server_name}")
                return None
            
            with open(srv_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse server configuration
            config = {}
            for line in content.split('\n'):
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
            
            # Extract display information
            display_name = config.get('Name', server_name)
            company = config.get('Company', '')
            environment = config.get('Environment', '').lower()
            
            # Determine server type
            server_type = 'demo' if (
                'demo' in server_name.lower() or 
                'demo' in environment or
                'demo' in display_name.lower()
            ) else 'live'
            
            # Create display name with company if available
            if company and company not in display_name:
                display_name = f"{company} - {display_name}"
            
            # Validate required fields
            if not config.get('Address'):
                logger.warning(f"⚠️ Server {server_name} missing Address field")
                return None
            
            return {
                'value': server_name,
                'display': display_name,
                'type': server_type,
                'company': company,
                'address': config.get('Address', ''),
                'environment': environment
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing {srv_file}: {e}")
            return None
    
    def _is_safe_server_name(self, name: str) -> bool:
        """Validate server name for security"""
        import re
        # Allow alphanumeric, hyphens, single dots, underscores
        # Prevent path traversal (no consecutive dots or leading dots)
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$'
        
        # Additional security checks
        if not bool(re.match(pattern, name)):
            return False
        if len(name) > 50:
            return False
        if '..' in name:  # Prevent path traversal
            return False
        if name.startswith('.') or name.startswith('-'):
            return False
        
        return True
    
    def _get_fallback_servers(self) -> List[Dict[str, str]]:
        """Fallback server list if no .srv files found"""
        return [
            {
                'value': 'Coinexx-Demo', 
                'display': 'Coinexx - Demo Server', 
                'type': 'demo',
                'company': 'Coinexx',
                'address': 'demo.coinexx.com:443',
                'environment': 'demo'
            },
            {
                'value': 'Coinexx-Live', 
                'display': 'Coinexx - Live Server', 
                'type': 'live',
                'company': 'Coinexx',
                'address': 'live.coinexx.com:443',
                'environment': 'live'
            },
            {
                'value': 'Forex.com-Live3', 
                'display': 'FOREX.com - Live Server', 
                'type': 'live',
                'company': 'FOREX.com',
                'address': 'mt5-live3.forex.com:443',
                'environment': 'live'
            },
            {
                'value': 'MetaQuotes-Demo', 
                'display': 'MetaQuotes - Demo Server', 
                'type': 'demo',
                'company': 'MetaQuotes',
                'address': 'demo.metaquotes.net:443',
                'environment': 'demo'
            },
        ]
    
    def validate_credentials(self, login_id: str, password: str, server: str) -> Dict[str, Any]:
        """Validate MT5 credentials"""
        try:
            # Basic validation
            if not login_id or not login_id.isdigit():
                return {'valid': False, 'error': 'Login ID must be numeric'}
            
            if not password or len(password) < 4:
                return {'valid': False, 'error': 'Password must be at least 4 characters'}
            
            if not server:
                return {'valid': False, 'error': 'Server selection required'}
            
            # Check server exists
            available_servers = [s['value'] for s in self.get_available_servers()]
            if server not in available_servers:
                return {'valid': False, 'error': 'Invalid server selection'}
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Credential validation error: {e}")
            return {'valid': False, 'error': 'Validation failed'}
    
    def create_user_container(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update user container with MT5 credentials"""
        try:
            login_id = user_data['login_id']
            telegram_id = user_data.get('telegram_id')
            
            # Determine container name
            if telegram_id:
                container_name = f"mt5_user_{telegram_id}"
            else:
                container_name = f"mt5_user_{login_id}"
            
            # Check if container exists
            import docker
            client = docker.from_env()
            
            try:
                container = client.containers.get(container_name)
                logger.info(f"Container {container_name} already exists")
                container_exists = True
            except docker.errors.NotFound:
                logger.info(f"Container {container_name} not found, will create new")
                container_exists = False
            
            # Inject credentials using existing system
            result = self._inject_mt5_credentials(container_name, user_data, container_exists)
            
            if result['success']:
                logger.info(f"✅ Container {container_name} configured successfully")
                return {
                    'success': True,
                    'container_name': container_name,
                    'message': 'Terminal configured successfully'
                }
            else:
                logger.error(f"❌ Container configuration failed: {result['error']}")
                return {
                    'success': False,
                    'error': result['error']
                }
            
        except Exception as e:
            logger.error(f"Container creation error: {e}")
            return {
                'success': False,
                'error': f'Container setup failed: {str(e)}'
            }
    
    def _inject_mt5_credentials(self, container_name: str, user_data: Dict[str, Any], exists: bool) -> Dict[str, Any]:
        """Inject MT5 credentials into container"""
        try:
            # Import credential injection system
            sys.path.append(str(self.project_root))
            from telegram_command_connect_handler import inject_mt5_credentials_to_container
            
            credentials = {
                'login': user_data['login_id'],
                'password': user_data['password'],
                'server': user_data['server']
            }
            
            # Inject credentials
            result = inject_mt5_credentials_to_container(container_name, credentials)
            
            if result.get('success'):
                return {'success': True}
            else:
                return {'success': False, 'error': result.get('error', 'Injection failed')}
                
        except ImportError as e:
            logger.error(f"Failed to import credential injection: {e}")
            return {'success': False, 'error': 'Credential injection system not available'}
        except Exception as e:
            logger.error(f"Credential injection error: {e}")
            return {'success': False, 'error': f'Credential injection failed: {str(e)}'}
    
    def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register user in the system"""
        try:
            if not self.user_registry:
                logger.error("User registry not available")
                return {'success': False, 'error': 'User registry not available'}
            
            # Create user profile
            user_profile = {
                'user_id': user_data.get('telegram_id') or f"user_{user_data['login_id']}",
                'login_id': user_data['login_id'],
                'server': user_data['server'],
                'telegram_handle': user_data.get('telegram_handle'),
                'referral_code': user_data.get('referral_code'),
                'risk_mode': user_data.get('risk_mode', 'Bit Mode'),
                'status': 'credentials_injected',
                'onboarded_at': datetime.now().isoformat(),
                'onboarding_source': 'webapp'
            }
            
            # Register user
            registration_result = self.user_registry.register_user(
                user_profile['user_id'],
                user_profile
            )
            
            if registration_result:
                logger.info(f"✅ User {user_profile['user_id']} registered successfully")
                return {'success': True, 'user_profile': user_profile}
            else:
                logger.error(f"❌ User registration failed")
                return {'success': False, 'error': 'User registration failed'}
                
        except Exception as e:
            logger.error(f"User registration error: {e}")
            return {'success': False, 'error': f'Registration failed: {str(e)}'}
    
    def award_onboarding_xp(self, user_id: str) -> None:
        """Award XP for completing onboarding"""
        try:
            sys.path.append(str(self.project_root / "src" / "bitten_core"))
            from xp_calculator import XPCalculator
            
            xp_calc = XPCalculator()
            xp_calc.award_milestone_xp(user_id, "terminal_activated", 10)
            
            logger.info(f"✅ Awarded 10 XP to {user_id} for terminal activation")
            
        except Exception as e:
            logger.error(f"XP award error: {e}")
    
    def send_telegram_confirmation(self, user_data: Dict[str, Any], container_info: Dict[str, Any]) -> None:
        """Send Telegram confirmation from BittenProductionBot"""
        try:
            telegram_id = user_data.get('telegram_id')
            
            # If no telegram_id, try to resolve from telegram_handle
            if not telegram_id:
                telegram_handle = user_data.get('telegram_handle')
                if telegram_handle:
                    telegram_id = self._resolve_telegram_handle_to_id(telegram_handle)
                
            if not telegram_id:
                logger.info("No telegram_id or resolvable telegram_handle provided, skipping confirmation message")
                return
            
            # Import bot system  
            sys.path.append(str(self.project_root))
            from config_loader import get_bot_token
            import telebot
            
            bot_token = get_bot_token()
            bot = telebot.TeleBot(bot_token)
            
            # Get server display name for user-friendly message
            server_display = user_data.get('server', 'your broker')
            
            # Create the exact message format requested
            message = f"""✅ Your terminal is now active and connected to {server_display}.
🐾 'One login. One shot. One trade that changed your life.' — Norman
Type /status to confirm your fire readiness or wait for your first signal."""
            
            # Send message using telebot (synchronous)
            try:
                bot.send_message(
                    chat_id=telegram_id, 
                    text=message, 
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                logger.info(f"✅ Telegram confirmation sent to {telegram_id} via BittenProductionBot")
                
                # Optional: Send additional technical details in a follow-up message
                self._send_technical_details(bot, telegram_id, user_data, container_info)
                
            except Exception as send_error:
                logger.error(f"Failed to send message via telebot: {send_error}")
                # Fallback to the previous telegram method
                self._send_telegram_fallback(telegram_id, user_data, container_info)
            
        except Exception as e:
            logger.error(f"Telegram confirmation error: {e}")
    
    def _send_technical_details(self, bot, telegram_id: str, user_data: Dict[str, Any], container_info: Dict[str, Any]) -> None:
        """Send technical connection details as follow-up message"""
        try:
            details_message = f"""📊 <b>Terminal Details</b>
            
🏢 <b>Broker:</b> {user_data.get('server', 'Unknown')}
🆔 <b>Account ID:</b> {user_data.get('login_id', 'Hidden')}
🐳 <b>Container:</b> {container_info.get('container_name', 'Deployed')}
⚙️ <b>Risk Mode:</b> {user_data.get('risk_mode', 'Sniper Mode')}

<i>Your trading terminal is fully operational. Signals will appear automatically when market conditions align.</i>"""
            
            bot.send_message(
                chat_id=telegram_id,
                text=details_message,
                parse_mode='HTML'
            )
            logger.info(f"✅ Technical details sent to {telegram_id}")
            
        except Exception as e:
            logger.error(f"Failed to send technical details: {e}")
    
    def _send_telegram_fallback(self, telegram_id: str, user_data: Dict[str, Any], container_info: Dict[str, Any]) -> None:
        """Fallback method using telegram library"""
        try:
            import asyncio
            import telegram
            from config_loader import get_bot_token
            
            bot_token = get_bot_token()
            bot = telegram.Bot(token=bot_token)
            
            server_display = user_data.get('server', 'your broker')
            message = f"""✅ Your terminal is now active and connected to {server_display}.
🐾 'One login. One shot. One trade that changed your life.' — Norman
Type /status to confirm your fire readiness or wait for your first signal."""
            
            # Send async message
            async def send_message():
                await bot.send_message(chat_id=telegram_id, text=message)
            
            # Run in event loop or create new one
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(send_message())
            except RuntimeError:
                asyncio.run(send_message())
                
            logger.info(f"✅ Fallback telegram confirmation sent to {telegram_id}")
            
        except Exception as e:
            logger.error(f"Fallback telegram confirmation error: {e}")
    
    def _resolve_telegram_handle_to_id(self, telegram_handle: str) -> Optional[str]:
        """Resolve telegram handle to chat_id using user registry"""
        try:
            if not self.user_registry:
                logger.warning("User registry not available for telegram handle resolution")
                return None
            
            # Clean the handle (remove @ if present)
            clean_handle = telegram_handle.lstrip('@').lower()
            
            # Search through user registry for matching telegram handle
            registry_data = self.user_registry.registry_data
            for user_id, user_data in registry_data.items():
                if isinstance(user_data, dict):
                    user_handle = user_data.get('telegram_handle', '').lstrip('@').lower()
                    if user_handle == clean_handle:
                        # Found matching handle, return the user_id if it's a telegram chat_id
                        if user_id.isdigit():
                            logger.info(f"✅ Resolved @{clean_handle} to telegram_id: {user_id}")
                            return user_id
                        else:
                            # Check if there's a telegram_id field in user data
                            telegram_id = user_data.get('telegram_id')
                            if telegram_id:
                                logger.info(f"✅ Resolved @{clean_handle} to telegram_id: {telegram_id}")
                                return str(telegram_id)
            
            logger.warning(f"⚠️ Could not resolve telegram handle @{clean_handle} to chat_id")
            return None
            
        except Exception as e:
            logger.error(f"Error resolving telegram handle: {e}")
            return None
    
    def log_onboarding_failure(self, user_data: Dict[str, Any], error: str) -> None:
        """Log onboarding failures for debugging"""
        try:
            failure_entry = {
                'timestamp': datetime.now().isoformat(),
                'user_data': {k: v for k, v in user_data.items() if k != 'password'},
                'error': error,
                'stage': 'onboarding'
            }
            
            with open(self.onboarding_log, 'a') as f:
                f.write(json.dumps(failure_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to log onboarding failure: {e}")

class OnboardingWebAppRoutes:
    """Flask routes for the onboarding webapp"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.onboarding_system = HydraXOnboardingSystem()
        self.register_routes()
    
    def register_routes(self):
        """Register all onboarding routes"""
        
        @self.app.route('/connect')
        def connect_landing():
            """Main onboarding landing page"""
            try:
                servers = self.onboarding_system.get_available_servers()
                
                return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧠 B.I.T.T.E.N. | Launch Your Terminal</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-gold: #FFD700;
            --tactical-red: #FF4444;
            --elite-blue: #00D9FF;
            --dark-bg: #0A0A0A;
            --panel-bg: #1A1A1A;
            --border-glow: #333;
            --text-light: #FFFFFF;
            --text-muted: #CCCCCC;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--dark-bg);
            color: var(--text-light);
            min-height: 100vh;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 20% 50%, rgba(255, 215, 0, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(0, 217, 255, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 40% 80%, rgba(255, 68, 68, 0.02) 0%, transparent 50%);
        }

        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
        }

        .particle {
            position: absolute;
            width: 2px;
            height: 2px;
            background: var(--primary-gold);
            border-radius: 50%;
            opacity: 0.3;
            animation: float 6s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px) translateX(0px); opacity: 0.3; }
            50% { transform: translateY(-20px) translateX(10px); opacity: 0.6; }
        }

        .header {
            position: relative;
            z-index: 10;
            padding: 2rem 1rem;
            text-align: center;
            background: linear-gradient(135deg, var(--panel-bg) 0%, rgba(26, 26, 26, 0.8) 100%);
            border-bottom: 1px solid var(--border-glow);
        }

        .title {
            font-family: 'Orbitron', monospace;
            font-size: 3rem;
            font-weight: 900;
            background: linear-gradient(45deg, var(--primary-gold), var(--elite-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            text-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
        }

        .subtitle {
            font-size: 1.2rem;
            color: var(--text-muted);
            font-weight: 300;
            letter-spacing: 2px;
        }

        .main-container {
            position: relative;
            z-index: 10;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }

        .onboarding-card {
            background: var(--panel-bg);
            border: 1px solid var(--border-glow);
            border-radius: 20px;
            padding: 3rem;
            backdrop-filter: blur(20px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            position: relative;
            overflow: hidden;
        }

        .onboarding-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--primary-gold), transparent);
            animation: shimmer 3s ease-in-out infinite;
        }

        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        .form-section {
            margin-bottom: 2rem;
        }

        .section-title {
            font-family: 'Orbitron', monospace;
            font-size: 1.3rem;
            color: var(--primary-gold);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-label {
            display: block;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--text-light);
            font-size: 0.95rem;
        }

        .form-input, .form-select {
            width: 100%;
            padding: 1rem;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-glow);
            border-radius: 10px;
            color: var(--text-light);
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .form-input:focus, .form-select:focus {
            outline: none;
            border-color: var(--elite-blue);
            box-shadow: 0 0 0 2px rgba(0, 217, 255, 0.2);
        }

        .password-wrapper {
            position: relative;
        }

        .password-toggle {
            position: absolute;
            right: 1rem;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 1.1rem;
        }

        .risk-mode-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 0.5rem;
        }

        .risk-mode-option {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-glow);
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }

        .risk-mode-option:hover {
            border-color: var(--elite-blue);
            background: rgba(0, 217, 255, 0.1);
        }

        .risk-mode-option.selected {
            border-color: var(--primary-gold);
            background: rgba(255, 215, 0, 0.1);
        }

        .risk-mode-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .risk-mode-desc {
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .terms-section {
            background: rgba(255, 68, 68, 0.05);
            border: 1px solid rgba(255, 68, 68, 0.2);
            border-radius: 10px;
            padding: 1.5rem;
            margin: 2rem 0;
        }

        .checkbox-wrapper {
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
        }

        .custom-checkbox {
            width: 20px;
            height: 20px;
            border: 2px solid var(--border-glow);
            border-radius: 4px;
            cursor: pointer;
            position: relative;
            flex-shrink: 0;
            margin-top: 2px;
        }

        .custom-checkbox.checked {
            background: var(--primary-gold);
            border-color: var(--primary-gold);
        }

        .custom-checkbox.checked::after {
            content: '✓';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: var(--dark-bg);
            font-weight: bold;
            font-size: 12px;
        }

        .terms-text {
            font-size: 0.9rem;
            line-height: 1.5;
            color: var(--text-muted);
        }

        .submit-button {
            width: 100%;
            padding: 1.2rem;
            background: linear-gradient(45deg, var(--primary-gold), #FFB800);
            border: none;
            border-radius: 15px;
            color: var(--dark-bg);
            font-family: 'Orbitron', monospace;
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
        }

        .submit-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(255, 215, 0, 0.4);
        }

        .submit-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .submit-button.loading::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            animation: loading 1.5s infinite;
        }

        @keyframes loading {
            0% { left: -100%; }
            100% { left: 100%; }
        }

        .status-message {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            font-weight: 600;
            display: none;
        }

        .status-message.success {
            background: rgba(40, 167, 69, 0.2);
            border: 1px solid rgba(40, 167, 69, 0.3);
            color: #28a745;
        }

        .status-message.error {
            background: rgba(220, 53, 69, 0.2);
            border: 1px solid rgba(220, 53, 69, 0.3);
            color: #dc3545;
        }

        .success-animation {
            text-align: center;
            padding: 2rem 1rem;
        }

        .bit-paw {
            font-size: 4rem;
            animation: pawPrint 2s ease-in-out infinite;
            display: inline-block;
            margin-bottom: 1rem;
        }

        @keyframes pawPrint {
            0%, 100% { transform: scale(1) rotate(0deg); opacity: 0.8; }
            25% { transform: scale(1.1) rotate(-5deg); opacity: 1; }
            50% { transform: scale(1.2) rotate(0deg); opacity: 1; }
            75% { transform: scale(1.1) rotate(5deg); opacity: 1; }
        }

        .norman-quote {
            font-style: italic;
            color: var(--elite-gold);
            font-size: 1.1rem;
            line-height: 1.6;
            margin: 1rem 0;
            padding: 1.5rem;
            background: rgba(139, 90, 43, 0.1);
            border-left: 4px solid var(--elite-gold);
            border-radius: 8px;
            position: relative;
        }

        .norman-quote::before {
            content: '"';
            font-size: 3rem;
            color: var(--elite-gold);
            position: absolute;
            top: -10px;
            left: 10px;
            opacity: 0.3;
        }

        .norman-quote::after {
            content: '" — Norman';
            font-size: 0.9rem;
            color: var(--text-muted);
            font-style: normal;
            display: block;
            text-align: right;
            margin-top: 0.5rem;
            font-weight: 600;
        }

        .success-details {
            background: rgba(40, 167, 69, 0.1);
            border: 1px solid rgba(40, 167, 69, 0.2);
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            text-align: left;
        }

        .detail-line {
            display: flex;
            justify-content: space-between;
            margin: 0.5rem 0;
            font-size: 0.95rem;
        }

        .detail-label {
            color: var(--text-muted);
        }

        .detail-value {
            color: var(--text-light);
            font-weight: 600;
        }

        @media (max-width: 768px) {
            .title {
                font-size: 2rem;
            }
            
            .onboarding-card {
                padding: 2rem 1.5rem;
                margin: 1rem;
            }
            
            .risk-mode-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="particles" id="particles"></div>
    
    <header class="header">
        <h1 class="title">🧠 B.I.T.T.E.N.</h1>
        <p class="subtitle">Launch Your Terminal</p>
    </header>

    <div class="main-container">
        <div class="onboarding-card">
            <form id="onboardingForm">
                <div class="form-section">
                    <h2 class="section-title">
                        🔐 MT5 Credentials
                    </h2>
                    
                    <div class="form-group">
                        <label class="form-label">Login ID</label>
                        <input type="text" id="loginId" name="loginId" class="form-input" 
                               placeholder="843859" pattern="[0-9]+" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Password</label>
                        <div class="password-wrapper">
                            <input type="password" id="password" name="password" class="form-input" 
                                   placeholder="Your MT5 password" required>
                            <button type="button" class="password-toggle" onclick="togglePassword()">👁️</button>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Broker Server</label>
                        <select id="server" name="server" class="form-select" required>
                            <option value="">Select your broker server...</option>
                            {% for server in servers %}
                            <option value="{{ server.value }}">
                                {{ server.display }} {% if server.type == 'demo' %}(Demo){% else %}(Live){% endif %}
                            </option>
                            {% endfor %}
                        </select>
                    </div>
                </div>

                <div class="form-section">
                    <h2 class="section-title">
                        📱 Connection (Optional)
                    </h2>
                    
                    <div class="form-group">
                        <label class="form-label">Telegram Handle</label>
                        <input type="text" id="telegramHandle" name="telegramHandle" class="form-input" 
                               placeholder="@username">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Referral Code</label>
                        <input type="text" id="referralCode" name="referralCode" class="form-input" 
                               placeholder="Optional referral code">
                    </div>
                </div>

                <div class="form-section">
                    <h2 class="section-title">
                        ⚔️ Risk Mode
                    </h2>
                    
                    <div class="risk-mode-grid">
                        <div class="risk-mode-option" data-mode="Bit Mode">
                            <div class="risk-mode-title">🐱 Bit Mode</div>
                            <div class="risk-mode-desc">Conservative, cat-like precision</div>
                        </div>
                        <div class="risk-mode-option selected" data-mode="Sniper Mode">
                            <div class="risk-mode-title">🎯 Sniper Mode</div>
                            <div class="risk-mode-desc">Tactical, calculated strikes</div>
                        </div>
                        <div class="risk-mode-option" data-mode="Commander">
                            <div class="risk-mode-title">⚡ Commander</div>
                            <div class="risk-mode-desc">Elite, full-spectrum warfare</div>
                        </div>
                    </div>
                    <input type="hidden" id="riskMode" name="riskMode" value="Sniper Mode">
                </div>

                <div class="terms-section">
                    <div class="checkbox-wrapper">
                        <div class="custom-checkbox" id="termsCheckbox"></div>
                        <div class="terms-text">
                            I authorize this system to trade on my connected MT5 demo or live account, 
                            and I accept the user agreement and risk disclosures. I understand that 
                            trading involves substantial risk and I may lose money.
                        </div>
                    </div>
                    <input type="hidden" id="termsAccepted" name="termsAccepted" value="false">
                </div>

                <button type="submit" class="submit-button" id="submitButton" disabled>
                    🚀 Initialize Terminal
                </button>

                <div class="status-message" id="statusMessage"></div>
            </form>
        </div>
    </div>

    <script>
        // Generate floating particles
        function createParticles() {
            const particlesContainer = document.getElementById('particles');
            for (let i = 0; i < 50; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.top = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 6 + 's';
                particle.style.animationDuration = (4 + Math.random() * 4) + 's';
                particlesContainer.appendChild(particle);
            }
        }

        // Risk mode selection
        document.querySelectorAll('.risk-mode-option').forEach(option => {
            option.addEventListener('click', function() {
                document.querySelectorAll('.risk-mode-option').forEach(opt => opt.classList.remove('selected'));
                this.classList.add('selected');
                document.getElementById('riskMode').value = this.dataset.mode;
            });
        });

        // Terms checkbox
        document.getElementById('termsCheckbox').addEventListener('click', function() {
            this.classList.toggle('checked');
            const accepted = this.classList.contains('checked');
            document.getElementById('termsAccepted').value = accepted;
            updateSubmitButton();
        });

        // Password toggle
        function togglePassword() {
            const passwordInput = document.getElementById('password');
            const toggle = document.querySelector('.password-toggle');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                toggle.textContent = '🙈';
            } else {
                passwordInput.type = 'password';
                toggle.textContent = '👁️';
            }
        }

        // Update submit button state
        function updateSubmitButton() {
            const loginId = document.getElementById('loginId').value;
            const password = document.getElementById('password').value;
            const server = document.getElementById('server').value;
            const termsAccepted = document.getElementById('termsAccepted').value === 'true';
            
            const submitButton = document.getElementById('submitButton');
            submitButton.disabled = !(loginId && password && server && termsAccepted);
        }

        // Form validation
        document.querySelectorAll('#loginId, #password, #server').forEach(input => {
            input.addEventListener('input', updateSubmitButton);
        });

        // Form submission
        document.getElementById('onboardingForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitButton = document.getElementById('submitButton');
            const statusMessage = document.getElementById('statusMessage');
            
            // Show loading state
            submitButton.disabled = true;
            submitButton.classList.add('loading');
            submitButton.textContent = '🚀 Initializing...';
            
            statusMessage.style.display = 'none';
            
            try {
                const formData = new FormData(this);
                const data = Object.fromEntries(formData.entries());
                
                const response = await fetch('/api/onboard', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    statusMessage.className = 'status-message success';
                    statusMessage.innerHTML = `
                        <div class="success-animation">
                            <div class="bit-paw">🐾</div>
                            <div class="norman-quote">
                                One login. One shot. One trade that changed your life.
                            </div>
                            <div class="success-details">
                                <div class="detail-line">
                                    <span class="detail-label">Terminal Status:</span>
                                    <span class="detail-value">✅ Online</span>
                                </div>
                                <div class="detail-line">
                                    <span class="detail-label">User ID:</span>
                                    <span class="detail-value">${result.user_id || 'Assigned'}</span>
                                </div>
                                <div class="detail-line">
                                    <span class="detail-label">Container:</span>
                                    <span class="detail-value">${result.container || 'Deployed'}</span>
                                </div>
                                <div class="detail-line">
                                    <span class="detail-label">Next Step:</span>
                                    <span class="detail-value">Mission HUD</span>
                                </div>
                            </div>
                            <div style="margin-top: 1rem; color: var(--text-muted); font-size: 0.9rem;">
                                🚀 Redirecting to HUD in 3 seconds...
                            </div>
                        </div>
                    `;
                    statusMessage.style.display = 'block';
                    
                    // Redirect after delay
                    setTimeout(() => {
                        window.location.href = '/firestatus';
                    }, 3000);
                } else {
                    throw new Error(result.error || 'Onboarding failed');
                }
                
            } catch (error) {
                statusMessage.className = 'status-message error';
                statusMessage.textContent = '❌ ' + error.message;
                statusMessage.style.display = 'block';
                
                // Reset button
                submitButton.disabled = false;
                submitButton.classList.remove('loading');
                submitButton.textContent = '🚀 Initialize Terminal';
                updateSubmitButton();
            }
        });

        // Initialize particles
        createParticles();
    </script>
</body>
</html>
                """, servers=servers)
                
            except Exception as e:
                logger.error(f"Connect landing error: {e}")
                return f"Error loading onboarding page: {str(e)}", 500
        
        @self.app.route('/api/onboard', methods=['POST'])
        def api_onboard():
            """Process onboarding form submission"""
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({'success': False, 'error': 'No data provided'}), 400
                
                # Validate required fields
                required_fields = ['loginId', 'password', 'server', 'riskMode', 'termsAccepted']
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'success': False, 'error': f'Missing {field}'}), 400
                
                if data['termsAccepted'] != 'true':
                    return jsonify({'success': False, 'error': 'Terms must be accepted'}), 400
                
                # Validate credentials
                validation = self.onboarding_system.validate_credentials(
                    data['loginId'], 
                    data['password'], 
                    data['server']
                )
                
                if not validation['valid']:
                    return jsonify({'success': False, 'error': validation['error']}), 400
                
                # Process onboarding
                user_data = {
                    'login_id': data['loginId'],
                    'password': data['password'],  # This will not be logged
                    'server': data['server'],
                    'telegram_handle': data.get('telegramHandle'),
                    'referral_code': data.get('referralCode'),
                    'risk_mode': data['riskMode'],
                    'telegram_id': session.get('telegram_id')  # If available from Telegram WebApp
                }
                
                # Create container
                container_result = self.onboarding_system.create_user_container(user_data)
                
                if not container_result['success']:
                    self.onboarding_system.log_onboarding_failure(user_data, container_result['error'])
                    return jsonify({'success': False, 'error': container_result['error']}), 500
                
                # Register user
                registration_result = self.onboarding_system.register_user(user_data)
                
                if not registration_result['success']:
                    self.onboarding_system.log_onboarding_failure(user_data, registration_result['error'])
                    return jsonify({'success': False, 'error': registration_result['error']}), 500
                
                user_profile = registration_result['user_profile']
                
                # Award XP
                self.onboarding_system.award_onboarding_xp(user_profile['user_id'])
                
                # Send Telegram confirmation
                self.onboarding_system.send_telegram_confirmation(user_data, container_result)
                
                logger.info(f"✅ Onboarding completed for user {user_profile['user_id']}")
                
                return jsonify({
                    'success': True,
                    'message': 'Terminal initialized successfully',
                    'user_id': user_profile['user_id'],
                    'container': container_result['container_name'],
                    'next_step': '/firestatus'
                })
                
            except Exception as e:
                logger.error(f"Onboarding API error: {e}")
                return jsonify({'success': False, 'error': 'Internal server error'}), 500
        
        @self.app.route('/firestatus')
        def fire_status():
            """Post-onboarding status page"""
            return redirect('/hud?welcome=true')

def register_onboarding_system(app: Flask):
    """Register the onboarding system with Flask app"""
    try:
        onboarding_routes = OnboardingWebAppRoutes(app)
        logger.info("✅ HydraX Onboarding WebApp registered successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to register onboarding system: {e}")
        return False

if __name__ == "__main__":
    # Test the onboarding system
    from flask import Flask
    
    app = Flask(__name__)
    app.secret_key = 'test-secret-key'
    
    register_onboarding_system(app)
    
    print("🧪 Testing HydraX Onboarding System...")
    print("Visit: http://localhost:5000/connect")
    
    app.run(debug=True, port=5000)