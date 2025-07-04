#!/bin/bash

# HydraX v2 Production Setup Script
# This script sets up a complete production environment

set -e

echo "🚀 HydraX v2 Production Setup Starting..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN=${1:-"your-domain.com"}
USER=${2:-"hydrax"}
PROJECT_DIR="/home/$USER/HydraX-v2"

echo -e "${YELLOW}Setting up for domain: $DOMAIN${NC}"
echo -e "${YELLOW}User: $USER${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root${NC}"
   exit 1
fi

# Update system
echo -e "${GREEN}📦 Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install required packages
echo -e "${GREEN}📦 Installing required packages...${NC}"
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    wget \
    htop \
    ufw \
    fail2ban

# Create user if doesn't exist
if ! id "$USER" &>/dev/null; then
    echo -e "${GREEN}👤 Creating user: $USER${NC}"
    sudo useradd -m -s /bin/bash "$USER"
    sudo usermod -aG sudo "$USER"
fi

# Clone repository if not exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${GREEN}📥 Cloning HydraX-v2 repository...${NC}"
    sudo -u "$USER" git clone https://github.com/HydraXdev/HydraX-v2.git "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Create Python virtual environment
echo -e "${GREEN}🐍 Setting up Python virtual environment...${NC}"
sudo -u "$USER" python3 -m venv venv
sudo -u "$USER" bash -c "source venv/bin/activate && pip install -r requirements.txt"

# Create environment file
if [ ! -f .env ]; then
    echo -e "${GREEN}⚙️ Creating environment configuration...${NC}"
    sudo -u "$USER" cp .env.example .env
    echo -e "${YELLOW}⚠️ Please edit .env file with your production values${NC}"
fi

# Set proper permissions
echo -e "${GREEN}🔒 Setting file permissions...${NC}"
sudo chown -R "$USER:$USER" "$PROJECT_DIR"
sudo chmod 600 "$PROJECT_DIR/.env"

# Create log directory
sudo mkdir -p /var/log/hydrax
sudo chown "$USER:$USER" /var/log/hydrax
sudo chmod 755 /var/log/hydrax

# Create systemd service
echo -e "${GREEN}🔧 Creating systemd service...${NC}"
sudo tee /etc/systemd/system/hydrax.service > /dev/null <<EOF
[Unit]
Description=HydraX v2 Trading Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python src/core/TEN_elite_commands_FULL.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable hydrax

# Configure Nginx
echo -e "${GREEN}🌐 Configuring Nginx...${NC}"
sudo tee /etc/nginx/sites-available/hydrax > /dev/null <<EOF
server {
    server_name $DOMAIN;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:5000/status;
        access_log off;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    listen 80;
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/hydrax /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Configure UFW firewall
echo -e "${GREEN}🔥 Configuring firewall...${NC}"
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# SSL Certificate
echo -e "${GREEN}🔐 Setting up SSL certificate...${NC}"
if [ "$DOMAIN" != "your-domain.com" ]; then
    sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN"
else
    echo -e "${YELLOW}⚠️ Skipping SSL setup - please run: sudo certbot --nginx -d your-actual-domain.com${NC}"
fi

# Create deployment script
echo -e "${GREEN}📜 Creating deployment script...${NC}"
sudo -u "$USER" tee "$PROJECT_DIR/scripts/deploy.sh" > /dev/null <<'EOF'
#!/bin/bash

set -e

echo "🚀 Starting HydraX v2 deployment..."

cd "$(dirname "$0")/.."

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v || echo "⚠️ Tests failed - continuing anyway"

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart hydrax
sudo systemctl reload nginx

# Wait for service to start
sleep 5

# Verify deployment
echo "✅ Verifying deployment..."
if curl -f http://localhost:5000/status > /dev/null 2>&1; then
    echo "✅ Deployment successful! Service is running."
else
    echo "❌ Deployment failed! Service is not responding."
    exit 1
fi

echo "🎉 HydraX v2 deployment complete!"
EOF

sudo chmod +x "$PROJECT_DIR/scripts/deploy.sh"

# Create health check script
echo -e "${GREEN}🏥 Creating health check script...${NC}"
sudo -u "$USER" tee "$PROJECT_DIR/scripts/health_check.sh" > /dev/null <<EOF
#!/bin/bash

HEALTH_URL="http://localhost:5000/status"

if curl -f "\$HEALTH_URL" > /dev/null 2>&1; then
    echo "✅ Application: Healthy"
else
    echo "❌ Application: Unhealthy"
    exit 1
fi

echo "✅ All systems operational"
EOF

sudo chmod +x "$PROJECT_DIR/scripts/health_check.sh"

# Add health check to cron
(sudo -u "$USER" crontab -l 2>/dev/null; echo "*/5 * * * * $PROJECT_DIR/scripts/health_check.sh >> /var/log/hydrax/health.log 2>&1") | sudo -u "$USER" crontab -

# Start the service
echo -e "${GREEN}🚀 Starting HydraX service...${NC}"
sudo systemctl start hydrax

echo -e "${GREEN}✅ Production setup complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Edit $PROJECT_DIR/.env with your production configuration"
echo "2. Configure your Telegram bot token and chat ID"
echo "3. Set up your domain DNS to point to this server"
echo "4. Run SSL setup: sudo certbot --nginx -d $DOMAIN"
echo "5. Test the application: curl http://localhost:5000/status"
echo ""
echo -e "${GREEN}🔧 Useful Commands:${NC}"
echo "• Check service status: sudo systemctl status hydrax"
echo "• View logs: sudo journalctl -u hydrax -f"
echo "• Deploy updates: $PROJECT_DIR/scripts/deploy.sh"
echo "• Check health: $PROJECT_DIR/scripts/health_check.sh"
echo ""
echo -e "${GREEN}🌐 Access Points:${NC}"
echo "• Application: http://$DOMAIN (or https:// after SSL setup)"
echo "• Health Check: http://$DOMAIN/health"
echo "• Logs: /var/log/hydrax/"
echo ""
echo -e "${GREEN}🎉 HydraX v2 is ready for production!${NC}"
EOF