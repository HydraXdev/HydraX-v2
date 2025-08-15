# HydraX-v2 Deployment and Operations Specifications

## Table of Contents
1. [Infrastructure Requirements](#infrastructure-requirements)
2. [Deployment Procedures](#deployment-procedures)
3. [Environment Configuration](#environment-configuration)
4. [Monitoring and Alerting](#monitoring-and-alerting)
5. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
6. [Performance Tuning and Scaling](#performance-tuning-and-scaling)
7. [Security Hardening](#security-hardening)
8. [Troubleshooting and Maintenance](#troubleshooting-and-maintenance)

---

## Infrastructure Requirements

### Multi-Server Architecture

#### Linux Main Server (134.199.204.67)
- **OS**: Ubuntu 20.04 LTS or higher
- **CPU**: 8 cores minimum, 16 cores recommended
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 100GB SSD minimum, 500GB recommended
- **Network**: 1Gbps connection, low latency to Windows farm

#### Windows MT5 Farm (3.145.84.187)
- **OS**: Windows Server 2019 or higher
- **CPU**: 16 cores minimum, 32 cores recommended
- **RAM**: 32GB minimum, 64GB recommended
- **Storage**: 200GB SSD minimum, 1TB recommended
- **Network**: 1Gbps connection, low latency to Linux server

### Port Requirements

#### Linux Server
- **80**: HTTP (redirects to HTTPS)
- **443**: HTTPS (main application)
- **5000**: Flask application
- **5432**: PostgreSQL database
- **6379**: Redis cache
- **8000**: Analytics dashboard
- **22**: SSH (secured)

#### Windows Server
- **3389**: RDP (secured)
- **5555**: Primary agent
- **5556**: Backup agent
- **5557**: WebSocket agent
- **22**: SSH (if enabled)

### Software Dependencies

#### Linux Server
```bash
# System packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3.9 \
    python3.9-pip \
    python3.9-venv \
    nginx \
    postgresql-13 \
    redis-server \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    wget \
    htop \
    ufw \
    fail2ban \
    supervisor \
    logrotate

# Python packages (from requirements.txt)
pip install -r requirements.txt
```

#### Windows Server
```powershell
# Required software
- Python 3.9+
- MetaTrader 5 (multiple instances)
- PowerShell 5.1+
- Windows Task Scheduler
- Remote Desktop Services

# Python packages
pip install requests flask asyncio websockets
```

---

## Deployment Procedures

### Initial Setup Process

#### 1. Linux Server Setup
```bash
# Clone repository
git clone https://github.com/HydraXdev/HydraX-v2.git /root/HydraX-v2
cd /root/HydraX-v2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up database
sudo -u postgres createuser -s hydrax_user
sudo -u postgres createdb -O hydrax_user hydrax_db
python src/database/setup_db.py

# Create configuration files
cp config/trading.yml.example config/trading.yml
cp config/telegram.py.example config/telegram.py
cp config/stealth_settings.yml.example config/stealth_settings.yml

# Set permissions
chmod 600 config/*.yml config/*.py
chown -R $(whoami):$(whoami) /root/HydraX-v2
```

#### 2. Windows Server Setup
```powershell
# Create directory structure
New-Item -ItemType Directory -Path 'C:\MT5_Farm' -Force
New-Item -ItemType Directory -Path 'C:\MT5_Farm\Masters' -Force
New-Item -ItemType Directory -Path 'C:\MT5_Farm\EA' -Force
New-Item -ItemType Directory -Path 'C:\BITTEN_Agent' -Force
New-Item -ItemType Directory -Path 'C:\BITTEN_Bridge' -Force

# Deploy bulletproof agents
# Copy files from Linux server to Windows
scp -r /root/HydraX-v2/bulletproof_agents/* administrator@3.145.84.187:C:\BITTEN_Agent\

# Start services
cd C:\BITTEN_Agent
.\START_AGENTS.bat
```

### Deployment Script Usage

#### Automated Linux Deployment
```bash
# Run production setup
./scripts/setup_production.sh yourdomain.com hydrax

# Deploy updates
./scripts/deploy.sh

# Health check
./scripts/health_check.sh
```

#### Windows Agent Deployment
```powershell
# Manual deployment (required due to current agent status)
# 1. RDP to 3.145.84.187
# 2. Navigate to C:\BITTEN_Agent
# 3. Run START_AGENTS.bat
# 4. Verify all three agents are running (ports 5555, 5556, 5557)
```

### Service Management

#### Linux Services
```bash
# Main application service
sudo systemctl start hydrax
sudo systemctl enable hydrax
sudo systemctl status hydrax

# Monitoring service
sudo systemctl start press_pass_monitoring
sudo systemctl enable press_pass_monitoring

# Email scheduler
sudo systemctl start bitten_email_scheduler
sudo systemctl enable bitten_email_scheduler

# Press pass reset
sudo systemctl start press_pass_reset
sudo systemctl enable press_pass_reset
```

#### Windows Services
```powershell
# Task Scheduler for automatic restart
schtasks /create /tn "BITTEN_Agents" /tr "C:\BITTEN_Agent\START_AGENTS.bat" /sc minute /mo 5 /ru SYSTEM

# Service status check
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
```

---

## Environment Configuration

### Development Environment

#### Linux Configuration
```bash
# .env.development
export FLASK_ENV=development
export DEBUG=True
export DATABASE_URL=postgresql://hydrax_user:password@localhost/hydrax_dev
export REDIS_URL=redis://localhost:6379/0
export TELEGRAM_BOT_TOKEN=your_dev_token
export WEBHOOK_URL=https://dev.yourdomain.com/webhook
export LOG_LEVEL=DEBUG
export RATE_LIMIT_ENABLED=false
export STEALTH_ENABLED=false
```

#### Windows Configuration
```powershell
# Set environment variables
$env:BITTEN_ENV = "development"
$env:AGENT_PORT = "5555"
$env:DEBUG_MODE = "true"
$env:LOG_LEVEL = "DEBUG"
```

### Staging Environment

#### Linux Configuration
```bash
# .env.staging
export FLASK_ENV=staging
export DEBUG=false
export DATABASE_URL=postgresql://hydrax_user:password@localhost/hydrax_staging
export REDIS_URL=redis://localhost:6379/1
export TELEGRAM_BOT_TOKEN=your_staging_token
export WEBHOOK_URL=https://staging.yourdomain.com/webhook
export LOG_LEVEL=INFO
export RATE_LIMIT_ENABLED=true
export STEALTH_ENABLED=true
export STEALTH_LEVEL=medium
```

#### Windows Configuration
```powershell
# Set environment variables
$env:BITTEN_ENV = "staging"
$env:AGENT_PORT = "5555"
$env:DEBUG_MODE = "false"
$env:LOG_LEVEL = "INFO"
```

### Production Environment

#### Linux Configuration
```bash
# .env.production
export FLASK_ENV=production
export DEBUG=false
export DATABASE_URL=postgresql://hydrax_user:secure_password@localhost/hydrax_prod
export REDIS_URL=redis://localhost:6379/2
export TELEGRAM_BOT_TOKEN=your_prod_token
export WEBHOOK_URL=https://yourdomain.com/webhook
export LOG_LEVEL=WARNING
export RATE_LIMIT_ENABLED=true
export STEALTH_ENABLED=true
export STEALTH_LEVEL=high
export SSL_CERT_PATH=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
export SSL_KEY_PATH=/etc/letsencrypt/live/yourdomain.com/privkey.pem
```

#### Windows Configuration
```powershell
# Set environment variables
$env:BITTEN_ENV = "production"
$env:AGENT_PORT = "5555"
$env:DEBUG_MODE = "false"
$env:LOG_LEVEL = "WARNING"
$env:STEALTH_ENABLED = "true"
```

### Configuration Management

#### Centralized Configuration
```yaml
# config/tier_settings.yml
tiers:
  nibbler:
    max_trades_per_day: 5
    max_lot_size: 0.1
    risk_percent: 1.0
    
  fang:
    max_trades_per_day: 20
    max_lot_size: 0.5
    risk_percent: 2.0
    
  commander:
    max_trades_per_day: 50
    max_lot_size: 1.0
    risk_percent: 3.0
    
  apex:
    max_trades_per_day: 100
    max_lot_size: 2.0
    risk_percent: 5.0
```

#### Trading Configuration
```yaml
# config/trading.yml
risk_management:
  global_max_risk: 10.0
  max_daily_loss: 5.0
  max_drawdown: 15.0
  position_sizing:
    method: "fixed_percent"
    default_percent: 2.0

instruments:
  forex:
    - symbol: "EURUSD"
      spread_limit: 2.0
      session_hours: ["08:00-17:00", "13:00-22:00"]
```

---

## Monitoring and Alerting

### System Monitoring

#### Linux Server Monitoring
```bash
# CPU, Memory, Disk monitoring
htop
iostat -x 1
df -h
free -h

# Application monitoring
sudo journalctl -u hydrax -f
tail -f /var/log/hydrax/application.log

# Database monitoring
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

#### Windows Server Monitoring
```powershell
# System resources
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
Get-Counter "\Processor(_Total)\% Processor Time"
Get-Counter "\Memory\Available MBytes"

# Agent monitoring
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
netstat -an | findstr ":5555"
```

### Application Monitoring

#### Health Checks
```python
# Health check endpoints
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0.0',
        'services': {
            'database': check_database_health(),
            'redis': check_redis_health(),
            'windows_agent': check_windows_agent_health()
        }
    }
```

#### Monitoring Dashboard
```bash
# Access monitoring dashboard
http://yourdomain.com:8000/dashboard

# Key metrics displayed:
- Active users by tier
- Trading volume
- System performance
- Error rates
- Agent connectivity
```

### Alerting Configuration

#### Alert Thresholds
```yaml
# alerts.yml
thresholds:
  cpu_usage: 80
  memory_usage: 85
  disk_usage: 90
  error_rate: 5
  response_time: 5000
  
notifications:
  email:
    enabled: true
    recipients: ["admin@yourdomain.com"]
  
  webhook:
    enabled: true
    url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

#### Alert Types
1. **System Alerts**: High CPU, memory, disk usage
2. **Application Alerts**: High error rates, slow response times
3. **Trading Alerts**: Failed trades, risk limit breaches
4. **Security Alerts**: Failed authentication attempts, suspicious activity

---

## Backup and Disaster Recovery

### Backup Strategy

#### Database Backups
```bash
# Daily automated backups
#!/bin/bash
# /root/HydraX-v2/scripts/backup_database.sh

BACKUP_DIR="/root/HydraX-v2/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DATE}/database_backup.sql"

mkdir -p "$BACKUP_DIR/$DATE"

# Create database backup
sudo -u postgres pg_dump hydrax_prod > "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"

# Upload to cloud storage (optional)
aws s3 cp "$BACKUP_FILE.gz" s3://hydrax-backups/database/

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} \;
```

#### Application Backups
```bash
# Full application backup
#!/bin/bash
# /root/HydraX-v2/scripts/backup_application.sh

BACKUP_DIR="/root/HydraX-v2/backups"
DATE=$(date +%Y%m%d_%H%M%S)
APP_BACKUP="$BACKUP_DIR/${DATE}/app_backup.tar.gz"

mkdir -p "$BACKUP_DIR/$DATE"

# Create application backup
tar -czf "$APP_BACKUP" \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='logs' \
    /root/HydraX-v2/

# Upload to cloud storage
aws s3 cp "$APP_BACKUP" s3://hydrax-backups/application/
```

#### Windows Server Backups
```powershell
# Backup Windows configuration
$BackupPath = "C:\BITTEN_Backup\$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $BackupPath -Force

# Copy critical files
Copy-Item -Path "C:\BITTEN_Agent\*" -Destination "$BackupPath\Agent\" -Recurse -Force
Copy-Item -Path "C:\BITTEN_Bridge\*" -Destination "$BackupPath\Bridge\" -Recurse -Force
Copy-Item -Path "C:\MT5_Farm\EA\*" -Destination "$BackupPath\EA\" -Recurse -Force

# Compress backup
Compress-Archive -Path $BackupPath -DestinationPath "$BackupPath.zip"
```

### Disaster Recovery

#### Recovery Procedures

##### Linux Server Recovery
```bash
# 1. Restore from backup
cd /root/HydraX-v2
tar -xzf /backups/latest/app_backup.tar.gz

# 2. Restore database
sudo -u postgres psql -c "DROP DATABASE IF EXISTS hydrax_prod;"
sudo -u postgres psql -c "CREATE DATABASE hydrax_prod;"
sudo -u postgres psql hydrax_prod < /backups/latest/database_backup.sql

# 3. Restore configuration
cp /backups/latest/config/* config/

# 4. Restart services
sudo systemctl restart hydrax
sudo systemctl restart nginx
sudo systemctl restart postgresql
```

##### Windows Server Recovery
```powershell
# 1. Restore agent files
if (Test-Path "C:\BITTEN_Backup\latest\Agent\") {
    Copy-Item -Path "C:\BITTEN_Backup\latest\Agent\*" -Destination "C:\BITTEN_Agent\" -Recurse -Force
}

# 2. Restore bridge files
if (Test-Path "C:\BITTEN_Backup\latest\Bridge\") {
    Copy-Item -Path "C:\BITTEN_Backup\latest\Bridge\*" -Destination "C:\BITTEN_Bridge\" -Recurse -Force
}

# 3. Restart services
cd C:\BITTEN_Agent
.\START_AGENTS.bat
```

#### Recovery Time Objectives (RTO)
- **Linux Server**: 30 minutes
- **Windows Server**: 15 minutes
- **Database**: 45 minutes
- **Full System**: 1 hour

#### Recovery Point Objectives (RPO)
- **Database**: 1 hour (hourly backups)
- **Application**: 24 hours (daily backups)
- **Configuration**: 1 hour (versioned in Git)

---

## Performance Tuning and Scaling

### Database Optimization

#### PostgreSQL Configuration
```sql
-- /etc/postgresql/13/main/postgresql.conf
shared_buffers = 8GB
effective_cache_size = 24GB
maintenance_work_mem = 2GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

#### Database Indexing
```sql
-- Critical indexes for performance
CREATE INDEX CONCURRENTLY idx_trades_user_timestamp ON trades(user_id, created_at);
CREATE INDEX CONCURRENTLY idx_trades_symbol_status ON trades(symbol, status);
CREATE INDEX CONCURRENTLY idx_user_sessions_active ON user_sessions(user_id, is_active);
CREATE INDEX CONCURRENTLY idx_signals_timestamp ON signals(created_at);
```

### Application Performance

#### Redis Configuration
```conf
# /etc/redis/redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### Flask Application Tuning
```python
# config/webapp.py
class ProductionConfig:
    DEBUG = False
    TESTING = False
    
    # Database connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 30
    }
    
    # Redis configuration
    REDIS_URL = 'redis://localhost:6379/0'
    
    # Session configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
```

### Scaling Strategies

#### Horizontal Scaling

##### Load Balancer Configuration
```nginx
# /etc/nginx/sites-available/hydrax_lb
upstream hydrax_backend {
    server 127.0.0.1:5000 weight=3;
    server 127.0.0.1:5001 weight=2;
    server 127.0.0.1:5002 weight=1;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://hydrax_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

##### Multi-Instance Deployment
```bash
# Start multiple application instances
for i in {0..2}; do
    PORT=$((5000 + i))
    gunicorn --bind 0.0.0.0:$PORT --workers 4 --worker-class gevent src.core.app:app &
done
```

#### Vertical Scaling

##### Resource Allocation
```bash
# Optimize system resources
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'fs.file-max=65536' >> /etc/sysctl.conf
echo 'net.core.somaxconn=65536' >> /etc/sysctl.conf

# Apply changes
sysctl -p
```

##### Process Optimization
```bash
# Optimize Python processes
export PYTHONUNBUFFERED=1
export PYTHONHASHSEED=random
export PYTHONDONTWRITEBYTECODE=1
```

### Performance Monitoring

#### Key Metrics
```python
# Performance metrics to monitor
metrics = {
    'response_time': 'Average response time < 200ms',
    'throughput': 'Requests per second > 100',
    'error_rate': 'Error rate < 1%',
    'cpu_usage': 'CPU usage < 70%',
    'memory_usage': 'Memory usage < 80%',
    'disk_io': 'Disk I/O wait < 10%',
    'database_connections': 'Active connections < 80% of max'
}
```

#### Performance Testing
```bash
# Load testing with Apache Bench
ab -n 1000 -c 10 http://yourdomain.com/status

# Stress testing with wrk
wrk -t12 -c400 -d30s http://yourdomain.com/

# Database performance testing
pgbench -c 10 -j 2 -t 1000 hydrax_prod
```

---

## Security Hardening

### System Security

#### Linux Server Hardening
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Configure firewall
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Install fail2ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Configure SSH security
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl reload ssh

# Set up automatic security updates
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

#### Windows Server Hardening
```powershell
# Enable Windows Defender
Set-MpPreference -DisableRealtimeMonitoring $false
Set-MpPreference -DisableIOAVProtection $false
Set-MpPreference -DisableBehaviorMonitoring $false

# Configure Windows Firewall
netsh advfirewall set allprofiles state on
netsh advfirewall firewall add rule name="Allow RDP" dir=in action=allow protocol=TCP localport=3389
netsh advfirewall firewall add rule name="Allow Agent Port" dir=in action=allow protocol=TCP localport=5555

# Disable unnecessary services
Stop-Service -Name "Fax" -Force
Set-Service -Name "Fax" -StartupType Disabled
```

### Application Security

#### Authentication and Authorization
```python
# src/bitten_core/security_config.py
SECURITY_CONFIG = {
    'password_policy': {
        'min_length': 12,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_numbers': True,
        'require_special': True
    },
    'session_timeout': 3600,  # 1 hour
    'max_login_attempts': 5,
    'lockout_duration': 900,  # 15 minutes
    'two_factor_enabled': True
}
```

#### Data Encryption
```python
# Database encryption
from cryptography.fernet import Fernet

class EncryptionManager:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def encrypt_sensitive_data(self, data):
        return self.cipher.encrypt(data.encode())
    
    def decrypt_sensitive_data(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data).decode()
```

#### API Security
```python
# Rate limiting and API security
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/trade', methods=['POST'])
@limiter.limit("10 per minute")
@require_api_key
def execute_trade():
    # Trade execution logic
    pass
```

### Security Monitoring

#### Log Analysis
```bash
# Security log monitoring
grep "Failed password" /var/log/auth.log
grep "Invalid user" /var/log/auth.log
grep "Accepted publickey" /var/log/auth.log

# Application security logs
grep "SECURITY" /var/log/hydrax/application.log
grep "UNAUTHORIZED" /var/log/hydrax/application.log
```

#### Intrusion Detection
```bash
# Install and configure OSSEC
wget https://github.com/ossec/ossec-hids/archive/3.6.0.tar.gz
tar -xzf 3.6.0.tar.gz
cd ossec-hids-3.6.0
sudo ./install.sh

# Configure OSSEC rules
sudo nano /var/ossec/rules/local_rules.xml
```

---

## Troubleshooting and Maintenance

### Common Issues and Solutions

#### Linux Server Issues

##### High Memory Usage
```bash
# Identify memory-consuming processes
ps aux --sort=-%mem | head -10

# Check for memory leaks
valgrind --tool=memcheck --leak-check=full python app.py

# Optimize memory usage
echo 'vm.overcommit_memory=1' >> /etc/sysctl.conf
sysctl -p
```

##### Database Connection Issues
```bash
# Check database status
sudo systemctl status postgresql

# Check active connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Restart database if needed
sudo systemctl restart postgresql
```

##### Application Not Starting
```bash
# Check service status
sudo systemctl status hydrax

# Check logs
sudo journalctl -u hydrax -f

# Check configuration
python -c "from src.core.config import Config; print(Config.validate())"
```

#### Windows Server Issues

##### Agent Not Responding
```powershell
# Check agent processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# Kill stuck processes
Stop-Process -Name "python" -Force

# Restart agents
cd C:\BITTEN_Agent
.\START_AGENTS.bat
```

##### MT5 Connection Issues
```powershell
# Check MT5 processes
Get-Process | Where-Object {$_.ProcessName -like "*terminal*"}

# Check EA status
# In MT5: Tools > Options > Expert Advisors > Allow live trading

# Restart MT5 if needed
Stop-Process -Name "terminal64" -Force
# Manually restart MT5 instances
```

##### File System Issues
```powershell
# Check disk space
Get-Volume

# Clean temporary files
Remove-Item -Path "C:\Windows\Temp\*" -Recurse -Force
Remove-Item -Path "C:\Temp\*" -Recurse -Force

# Check file permissions
Get-Acl "C:\BITTEN_Agent"
```

### Maintenance Procedures

#### Daily Maintenance
```bash
# Daily maintenance checklist
#!/bin/bash
# /root/HydraX-v2/scripts/daily_maintenance.sh

# Check system health
./scripts/health_check.sh

# Backup database
./scripts/backup_database.sh

# Clean logs
find /var/log/hydrax -name "*.log" -type f -mtime +7 -delete

# Check disk space
df -h | grep -E "(80%|90%|100%)" && echo "WARNING: Disk space critical"

# Update system security
sudo apt update && sudo apt upgrade -y
```

#### Weekly Maintenance
```bash
# Weekly maintenance checklist
#!/bin/bash
# /root/HydraX-v2/scripts/weekly_maintenance.sh

# Full system backup
./scripts/backup_application.sh

# Database optimization
sudo -u postgres vacuumdb --all --verbose

# Log rotation
sudo logrotate -f /etc/logrotate.conf

# Security scan
sudo rkhunter --check --skip-keypress

# Performance analysis
iostat -x 1 10 > /tmp/io_stats.txt
```

#### Monthly Maintenance
```bash
# Monthly maintenance checklist
#!/bin/bash
# /root/HydraX-v2/scripts/monthly_maintenance.sh

# Security audit
./scripts/security_audit.sh

# Performance optimization
./scripts/optimize_database.sh

# Update dependencies
pip install --upgrade -r requirements.txt

# Clean old backups
find /root/HydraX-v2/backups -type d -mtime +30 -exec rm -rf {} \;

# Generate monthly report
python scripts/generate_monthly_report.py
```

### Emergency Procedures

#### System Recovery
```bash
# Emergency system recovery
#!/bin/bash
# /root/HydraX-v2/scripts/emergency_recovery.sh

echo "EMERGENCY RECOVERY INITIATED"

# Stop all services
sudo systemctl stop hydrax
sudo systemctl stop nginx
sudo systemctl stop postgresql

# Restore from latest backup
./scripts/restore_from_backup.sh

# Start services
sudo systemctl start postgresql
sudo systemctl start hydrax
sudo systemctl start nginx

# Verify system health
sleep 30
./scripts/health_check.sh

echo "EMERGENCY RECOVERY COMPLETED"
```

#### Incident Response
```bash
# Incident response procedure
#!/bin/bash
# /root/HydraX-v2/scripts/incident_response.sh

# 1. Isolate affected systems
sudo ufw deny all

# 2. Collect forensic data
mkdir -p /tmp/incident_$(date +%Y%m%d_%H%M%S)
cp -r /var/log/hydrax /tmp/incident_$(date +%Y%m%d_%H%M%S)/
ps aux > /tmp/incident_$(date +%Y%m%d_%H%M%S)/processes.txt
netstat -an > /tmp/incident_$(date +%Y%m%d_%H%M%S)/connections.txt

# 3. Notify stakeholders
echo "SECURITY INCIDENT DETECTED" | mail -s "HydraX Security Alert" admin@yourdomain.com

# 4. Document incident
echo "$(date): Security incident detected and response initiated" >> /var/log/hydrax/security_incidents.log
```

### Monitoring Scripts

#### Continuous Monitoring
```bash
# Continuous monitoring script
#!/bin/bash
# /root/HydraX-v2/scripts/continuous_monitor.sh

while true; do
    # Check system health
    CPU=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    MEM=$(free | grep Mem | awk '{printf("%.2f", $3/$2 * 100.0)}')
    
    # Check application health
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
    
    # Log metrics
    echo "$(date): CPU: ${CPU}%, MEM: ${MEM}%, HTTP: ${HTTP_STATUS}" >> /var/log/hydrax/metrics.log
    
    # Alert if thresholds exceeded
    if (( $(echo "$CPU > 80" | bc -l) )); then
        echo "HIGH CPU USAGE: $CPU%" | mail -s "HydraX Alert" admin@yourdomain.com
    fi
    
    sleep 60
done
```

### Documentation Updates

#### Change Log Maintenance
```bash
# Update change log
#!/bin/bash
# /root/HydraX-v2/scripts/update_changelog.sh

DATE=$(date +%Y-%m-%d)
VERSION=$(git describe --tags --abbrev=0)

echo "## [$VERSION] - $DATE" >> CHANGELOG.md
echo "" >> CHANGELOG.md
echo "### Added" >> CHANGELOG.md
echo "### Changed" >> CHANGELOG.md
echo "### Fixed" >> CHANGELOG.md
echo "### Removed" >> CHANGELOG.md
echo "" >> CHANGELOG.md
```

This comprehensive deployment and operations specification provides everything needed to deploy, monitor, and maintain the HydraX-v2 multi-server trading system. The procedures are designed for the current Linux main server (134.199.204.67) and Windows MT5 farm (3.145.84.187) architecture, with bulletproof redundancy and enterprise-grade reliability.