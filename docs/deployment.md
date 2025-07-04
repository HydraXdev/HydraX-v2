# HydraX v2 Deployment Guide

## 🚀 **Deployment Overview**

This guide covers deploying HydraX v2 from development to production environments, including server setup, security configuration, and monitoring.

## 🏗️ **Deployment Architecture**

### **Production Stack**
```
Internet → Nginx (HTTPS/SSL) → Flask App (Port 5000) → MT5 Bridge → MetaTrader 5
                ↓
        Telegram Webhook
```

### **Components**
- **Nginx**: Reverse proxy with SSL termination
- **Flask Application**: Core trading API and bot handler
- **MT5 Bridge**: MetaTrader 5 integration
- **Telegram Bot**: Real-time command interface
- **SSL Certificate**: Let's Encrypt or commercial certificate

## 📋 **Prerequisites**

### **System Requirements**
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **Python**: 3.8 or higher
- **RAM**: Minimum 2GB, recommended 4GB+
- **Storage**: 20GB+ available space
- **Network**: Stable internet connection with public IP

### **Required Software**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install Nginx
sudo apt install nginx -y

# Install Git
sudo apt install git -y

# Install SSL certificate tools (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx -y
```

## 🔧 **Server Setup**

### **1. Clone Repository**
```bash
# Clone the repository
git clone https://github.com/HydraXdev/HydraX-v2.git
cd HydraX-v2

# Switch to production branch (if exists)
git checkout production || git checkout main
```

### **2. Create Virtual Environment**
```bash
# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **3. Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Production .env Configuration**:
```env
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your_super_secure_secret_key_here

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_production_bot_token
TELEGRAM_CHAT_ID=your_production_chat_id

# API Security  
DEV_API_KEY=your_production_api_key_here

# Trading Configuration
BRIDGE_URL=http://127.0.0.1:9000
MAX_RISK_PERCENT=1.0
MAX_CONCURRENT_TRADES=2

# Database (if implemented)
DATABASE_URL=postgresql://user:pass@localhost:5432/hydrax

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/hydrax/app.log
```

### **4. SSL Certificate Setup**
```bash
# Request SSL certificate from Let's Encrypt
sudo certbot --nginx -d your-domain.com

# Verify certificate auto-renewal
sudo certbot renew --dry-run
```

### **5. Nginx Configuration**
Create `/etc/nginx/sites-available/hydrax`:
```nginx
server {
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000/status;
        access_log off;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    if ($host = your-domain.com) {
        return 301 https://$host$request_uri;
    }

    listen 80;
    server_name your-domain.com;
    return 404;
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/hydrax /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔄 **Process Management**

### **Systemd Service Setup**
Create `/etc/systemd/system/hydrax.service`:
```ini
[Unit]
Description=HydraX v2 Trading Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/HydraX-v2
Environment=PATH=/home/ubuntu/HydraX-v2/venv/bin
ExecStart=/home/ubuntu/HydraX-v2/venv/bin/python src/core/TEN_elite_commands_FULL.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hydrax
sudo systemctl start hydrax
sudo systemctl status hydrax
```

### **Alternative: Screen/Tmux Deployment**
For simpler deployments:
```bash
# Using screen
screen -S hydrax
source venv/bin/activate
python src/core/TEN_elite_commands_FULL.py
# Ctrl+A, D to detach

# Using tmux
tmux new-session -d -s hydrax
tmux send-keys -t hydrax "source venv/bin/activate" Enter
tmux send-keys -t hydrax "python src/core/TEN_elite_commands_FULL.py" Enter
```

## 🔐 **Security Hardening**

### **Firewall Configuration**
```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Deny all other traffic by default
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Check status
sudo ufw status
```

### **SSH Hardening**
Edit `/etc/ssh/sshd_config`:
```bash
# Disable password authentication (use keys only)
PasswordAuthentication no
PubkeyAuthentication yes

# Disable root login
PermitRootLogin no

# Change default port (optional)
Port 2222

# Restart SSH service
sudo systemctl restart ssh
```

### **Application Security**
```bash
# Create dedicated user
sudo useradd -m -s /bin/bash hydrax
sudo usermod -aG www-data hydrax

# Set proper file permissions
sudo chown -R hydrax:hydrax /home/hydrax/HydraX-v2
sudo chmod 600 /home/hydrax/HydraX-v2/.env

# Secure log directory
sudo mkdir -p /var/log/hydrax
sudo chown hydrax:hydrax /var/log/hydrax
sudo chmod 755 /var/log/hydrax
```

## 📊 **Monitoring & Logging**

### **Application Logs**
```bash
# View live logs
sudo journalctl -u hydrax -f

# View recent logs
sudo journalctl -u hydrax --since "1 hour ago"

# Application log file (if configured)
tail -f /var/log/hydrax/app.log
```

### **Nginx Logs**
```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log

# Specific domain logs (if configured)
sudo tail -f /var/log/nginx/hydrax.access.log
```

### **System Monitoring**
```bash
# System resource usage
htop

# Disk usage
df -h

# Memory usage
free -h

# Network connections
netstat -tulpn | grep :5000
```

## 🚀 **Deployment Script**

Create `scripts/deploy.sh`:
```bash
#!/bin/bash

# HydraX v2 Production Deployment Script

set -e

echo "🚀 Starting HydraX v2 deployment..."

# Update code
echo "📥 Pulling latest code..."
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Backup current .env if exists
if [ -f .env ]; then
    cp .env .env.backup
    echo "💾 Backed up current .env to .env.backup"
fi

# Update environment from template if needed
echo "⚙️ Checking environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️ Created .env from template - please configure!"
    exit 1
fi

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart hydrax
sudo systemctl reload nginx

# Verify deployment
echo "✅ Verifying deployment..."
sleep 5

if curl -f http://localhost:5000/status > /dev/null 2>&1; then
    echo "✅ Deployment successful! Service is running."
else
    echo "❌ Deployment failed! Service is not responding."
    exit 1
fi

echo "🎉 HydraX v2 deployment complete!"
```

Make it executable:
```bash
chmod +x scripts/deploy.sh
```

## 🔧 **Telegram Webhook Setup**

### **Set Webhook URL**
```bash
# Set production webhook
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/status"}'

# Verify webhook
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
```

### **Test Webhook**
```bash
# Test from command line
curl -X POST https://your-domain.com/status \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 123456789,
    "message": {
      "message_id": 1,
      "from": {"id": 12345, "username": "test"},
      "chat": {"id": -1001234567890, "type": "supergroup"},
      "text": "/status"
    }
  }'
```

## 🔍 **Health Checks**

### **Automated Health Monitoring**
Create `scripts/health_check.sh`:
```bash
#!/bin/bash

# Health check script for monitoring

HEALTH_URL="https://your-domain.com/status"
TELEGRAM_URL="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"

# Check application health
if curl -f "$HEALTH_URL" > /dev/null 2>&1; then
    echo "✅ Application: Healthy"
else
    echo "❌ Application: Unhealthy"
    exit 1
fi

# Check Telegram bot connectivity
if curl -f "$TELEGRAM_URL" > /dev/null 2>&1; then
    echo "✅ Telegram Bot: Connected"
else
    echo "❌ Telegram Bot: Disconnected"
    exit 1
fi

echo "✅ All systems operational"
```

### **Cron Job for Health Checks**
```bash
# Add to crontab
crontab -e

# Check health every 5 minutes
*/5 * * * * /home/ubuntu/HydraX-v2/scripts/health_check.sh >> /var/log/hydrax/health.log 2>&1
```

## 🔄 **Updates & Maintenance**

### **Zero-Downtime Updates**
```bash
# Create update script
#!/bin/bash

echo "🔄 Starting zero-downtime update..."

# Pull changes
git pull origin main

# Install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -q

# Graceful restart
sudo systemctl reload hydrax

echo "✅ Update complete!"
```

### **Database Migrations** (Future)
```bash
# When database is implemented
flask db upgrade
```

### **Backup Strategy**
```bash
# Create backup script
#!/bin/bash

BACKUP_DIR="/var/backups/hydrax"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup configuration
cp .env "$BACKUP_DIR/env_$DATE"

# Backup database (when implemented)
# pg_dump hydrax > "$BACKUP_DIR/db_$DATE.sql"

# Backup logs
cp -r /var/log/hydrax "$BACKUP_DIR/logs_$DATE"

echo "✅ Backup created: $BACKUP_DIR"
```

## 🚨 **Troubleshooting**

### **Common Issues**

**Application won't start**:
```bash
# Check service status
sudo systemctl status hydrax

# Check logs
sudo journalctl -u hydrax -n 50

# Check Python path and dependencies
source venv/bin/activate
python -c "import flask; print('Flask OK')"
```

**Nginx connection errors**:
```bash
# Test Nginx configuration
sudo nginx -t

# Check if Flask is running
curl http://localhost:5000/status

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

**SSL certificate issues**:
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test SSL configuration
curl -I https://your-domain.com
```

**Telegram webhook issues**:
```bash
# Check webhook status
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"

# Reset webhook
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook"
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=https://your-domain.com/status"
```

## 📊 **Performance Optimization**

### **Application Performance**
- Use Gunicorn for production WSGI server
- Implement Redis for caching
- Optimize database queries
- Enable gzip compression in Nginx

### **Server Performance**
- Tune Nginx worker processes
- Optimize system kernel parameters
- Monitor resource usage
- Implement log rotation

---

**📝 Note**: This deployment guide assumes a production environment. Adjust configurations based on your specific requirements and security policies.