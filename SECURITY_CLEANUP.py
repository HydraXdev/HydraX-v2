#!/usr/bin/env python3
"""
🔐 SECURITY CLEANUP - Remove exposed secrets and prepare for safe git push
"""

import os
import re
import shutil
from datetime import datetime

def secure_env_file():
    """Move .env file and create template"""
    print("🔐 Securing .env file...")
    
    if os.path.exists('/root/HydraX-v2/.env'):
        # Backup the real .env as .env.local
        shutil.move('/root/HydraX-v2/.env', '/root/HydraX-v2/.env.local')
        print("  ✅ Moved .env to .env.local")
        
        # Create .env.example template
        env_template = """# BITTEN Environment Variables Template
# Copy to .env.local and fill in your real values

# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
CHAT_ID=your_chat_id_here
ADMIN_USER_ID=your_admin_user_id_here

# Stripe Payment Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_test_key_here
STRIPE_SECRET_KEY=sk_test_your_test_key_here
STRIPE_RESTRICTED_KEY=rk_test_your_restricted_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Flask Configuration
FLASK_SECRET_KEY=generate_random_secret_key_here
FLASK_ENV=development

# Trading APIs
TRADERMADE_API_KEY=your_tradermade_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///data/bitten.db

# MT5 Configuration
MT5_SERVER=your_mt5_server_here
MT5_LOGIN=your_mt5_login_here
"""
        
        with open('/root/HydraX-v2/.env.example', 'w') as f:
            f.write(env_template)
        print("  ✅ Created .env.example template")

def create_gitignore():
    """Create comprehensive .gitignore"""
    print("📝 Creating .gitignore...")
    
    gitignore_content = """# Environment and secrets
.env
.env.*
!.env.example

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
*.egg-info/
.pytest_cache/

# Logs
*.log
logs/
*.out

# Database
*.db
*.sqlite
*.sqlite3

# Temporary files
*.tmp
*.temp
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# MT5 Files
*.ex5
*.ex4

# Backup files
*.backup
*.bak

# Sensitive data
*secret*
*password*
*token*
*key*
!*example*
!*template*

# Build artifacts
build/
dist/
*.tar.gz
*.zip

# Local development
.local/
local/
"""
    
    with open('/root/HydraX-v2/.gitignore', 'w') as f:
        f.write(gitignore_content)
    print("  ✅ Created comprehensive .gitignore")

def clean_hardcoded_secrets():
    """Remove hardcoded secrets from Python files"""
    print("🧹 Cleaning hardcoded secrets...")
    
    # Patterns to find and replace
    replacements = [
        # Telegram bot token
        (r'os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")', 'os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")'),
        
        # TraderMade API key
        (r'os.getenv("TRADERMADE_API_KEY", "YOUR_API_KEY_HERE")', 'os.getenv("TRADERMADE_API_KEY", "YOUR_API_KEY_HERE")'),
        
        # Chat/User IDs (less sensitive but still good practice)
        (r'int(os.getenv("CHAT_ID", "-1002581996861"))', 'int(os.getenv("CHAT_ID", "int(os.getenv("CHAT_ID", "-1002581996861"))"))'),
        (r'int(os.getenv("ADMIN_USER_ID", "7176191872"))', 'int(os.getenv("ADMIN_USER_ID", "int(os.getenv("ADMIN_USER_ID", "7176191872"))"))'),
        
        # Flask secret key
        (r'os.getenv("FLASK_SECRET_KEY", "dev-key-change-in-production")', 'os.getenv("FLASK_SECRET_KEY", "dev-key-change-in-production")'),
    ]
    
    cleaned_files = []
    
    for root, dirs, files in os.walk('/root/HydraX-v2'):
        # Skip hidden dirs and quarantine
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['QUARANTINE', '__pycache__']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Apply replacements
                    for pattern, replacement in replacements:
                        if pattern in content:
                            content = content.replace(pattern, replacement)
                    
                    # Add os import if needed and secrets were replaced
                    if content != original_content and 'os.getenv' in content:
                        if 'import os' not in content and 'from os' not in content:
                            # Add import at the top after other imports
                            lines = content.split('\n')
                            insert_pos = 0
                            for i, line in enumerate(lines):
                                if line.startswith('import ') or line.startswith('from '):
                                    insert_pos = i + 1
                                elif line.strip() and not line.startswith('#'):
                                    break
                            lines.insert(insert_pos, 'import os')
                            content = '\n'.join(lines)
                    
                    # Write back if changed
                    if content != original_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        cleaned_files.append(filepath)
                        
                except Exception as e:
                    print(f"    ⚠️ Error cleaning {filepath}: {e}")
    
    print(f"  ✅ Cleaned {len(cleaned_files)} files")
    return cleaned_files

def setup_redundancies():
    """Set up critical system redundancies"""
    print("🛡️ Setting up critical redundancies...")
    
    # Create redundant config loader
    redundant_config = '''#!/usr/bin/env python3
"""
🛡️ REDUNDANT CONFIG LOADER - Failsafe environment loading
"""

import os
from typing import Dict, Any

class RedundantConfig:
    """Load config with multiple fallback methods"""
    
    def __init__(self):
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load config with fallbacks"""
        # Try .env.local first (real secrets)
        self._try_load_env_file('.env.local')
        
        # Fallback to .env if exists
        self._try_load_env_file('.env')
        
        # Apply defaults for critical values
        self._apply_defaults()
    
    def _try_load_env_file(self, filename: str):
        """Try to load environment file"""
        try:
            from dotenv import load_dotenv
            load_dotenv(filename)
        except ImportError:
            # Manual parsing if python-dotenv not available
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
        except Exception:
            pass
    
    def _apply_defaults(self):
        """Apply safe defaults for critical components"""
        defaults = {
            'BOT_TOKEN': 'DISABLED_FOR_SECURITY',
            'CHAT_ID': 'int(os.getenv("CHAT_ID", "-1002581996861"))',
            'ADMIN_USER_ID': 'int(os.getenv("ADMIN_USER_ID", "7176191872"))',
            'FLASK_SECRET_KEY': 'dev-key-change-in-production',
            'DATABASE_URL': 'sqlite:///data/bitten.db',
            'WEBAPP_PORT': '8888',
            'WEBAPP_HOST': '0.0.0.0',
        }
        
        for key, default_value in defaults.items():
            if not os.getenv(key):
                os.environ[key] = default_value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with fallback"""
        return os.getenv(key, default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer config value"""
        try:
            return int(os.getenv(key, default))
        except (ValueError, TypeError):
            return default
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return os.getenv('FLASK_ENV', 'development').lower() == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return not self.is_production()

# Global config instance
config = RedundantConfig()
'''
    
    with open('/root/HydraX-v2/config/redundant_config.py', 'w') as f:
        f.write(redundant_config)
    print("  ✅ Created redundant config loader")

def create_connection_redundancy():
    """Create redundant connection handlers"""
    print("🔗 Setting up connection redundancies...")
    
    connection_manager = '''#!/usr/bin/env python3
"""
🔗 CONNECTION MANAGER - Redundant connections for critical services
"""

import time
import logging
from typing import Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage redundant connections with failover"""
    
    def __init__(self):
        self.connections = {}
        self.fallback_handlers = {}
    
    def register_fallback(self, service: str, handler: Callable):
        """Register fallback handler for service"""
        self.fallback_handlers[service] = handler
    
    def with_fallback(self, service: str, max_retries: int = 3, delay: float = 1.0):
        """Decorator for automatic failover"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        logger.warning(f"{service} attempt {attempt + 1} failed: {e}")
                        
                        if attempt < max_retries - 1:
                            time.sleep(delay * (2 ** attempt))  # Exponential backoff
                
                # All retries failed, try fallback
                if service in self.fallback_handlers:
                    logger.info(f"Using fallback handler for {service}")
                    try:
                        return self.fallback_handlers[service](*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(f"Fallback also failed for {service}: {fallback_error}")
                
                # Re-raise the last exception
                raise last_exception
            
            return wrapper
        return decorator

# Global connection manager
connection_manager = ConnectionManager()

# Telegram fallback
def telegram_fallback(*args, **kwargs):
    """Fallback for Telegram failures"""
    logger.info("Telegram service unavailable - logging message locally")
    with open('/root/HydraX-v2/logs/telegram_fallback.log', 'a') as f:
        f.write(f"{time.time()}: Telegram message failed - {args} {kwargs}\\n")

# WebApp fallback  
def webapp_fallback(*args, **kwargs):
    """Fallback for WebApp failures"""
    logger.info("WebApp service unavailable - using minimal response")
    return {"status": "service_unavailable", "message": "Please try again later"}

# Register fallbacks
connection_manager.register_fallback('telegram', telegram_fallback)
connection_manager.register_fallback('webapp', webapp_fallback)
'''
    
    with open('/root/HydraX-v2/config/connection_manager.py', 'w') as f:
        f.write(connection_manager)
    print("  ✅ Created connection redundancy manager")

def main():
    """Main security cleanup"""
    print("🔐 SECURITY CLEANUP - Preparing for safe git push")
    print("="*60)
    
    # Create backup timestamp
    backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Backup timestamp: {backup_time}")
    
    # Execute cleanup steps
    secure_env_file()
    create_gitignore()
    cleaned_files = clean_hardcoded_secrets()
    setup_redundancies() 
    create_connection_redundancy()
    
    print("="*60)
    print("✅ SECURITY CLEANUP COMPLETED")
    print(f"  - Environment secured: .env → .env.local")
    print(f"  - .gitignore created with comprehensive rules")
    print(f"  - {len(cleaned_files)} files cleaned of hardcoded secrets")
    print(f"  - Redundant config system created")
    print(f"  - Connection failover system created")
    print()
    print("🚨 IMPORTANT NEXT STEPS:")
    print("1. Update .env.local with your real API keys")
    print("2. Test the system with environment variables")
    print("3. Revoke and regenerate all exposed API keys")
    print("4. Verify no secrets remain in code before git push")

if __name__ == "__main__":
    main()