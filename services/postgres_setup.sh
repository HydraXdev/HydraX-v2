#!/bin/bash
# BITTEN v2.1 - Postgres Setup Script
# Date: 2025-09-16
# Purpose: Complete Postgres setup for BITTEN user management system

set -e

echo "🚀 BITTEN v2.1 - Postgres Setup Starting..."

# Configuration
DB_NAME="bitten"
DB_USER="bitten"
DB_PASS="bitten_secure_2025"
DB_HOST="localhost"
DB_PORT="5432"

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
   echo "✅ Running with root privileges"
else
   echo "❌ This script requires root privileges. Run with sudo."
   exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install PostgreSQL if not present
if ! command_exists psql; then
    echo "📦 Installing PostgreSQL..."
    apt update
    apt install -y postgresql postgresql-contrib postgresql-client
    systemctl start postgresql
    systemctl enable postgresql
    echo "✅ PostgreSQL installed and started"
else
    echo "✅ PostgreSQL already installed"
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd /root/HydraX-v2
pip install psycopg[binary] psycopg_pool orjson
echo "✅ Python dependencies installed"

# Setup database and user
echo "🔐 Setting up database and user..."
sudo -u postgres psql << EOF
-- Create database
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME;

-- Create user
DROP USER IF EXISTS $DB_USER;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;

-- Connect to bitten database and grant schema privileges
\c $DB_NAME;
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;

\q
EOF

echo "✅ Database and user created"

# Create schema
echo "🏗️ Creating database schema..."
export PGPASSWORD="$DB_PASS"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f /root/HydraX-v2/db/postgres_schema.sql

if [ $? -eq 0 ]; then
    echo "✅ Database schema created successfully"
else
    echo "❌ Failed to create database schema"
    exit 1
fi

# Setup environment variables
echo "🔧 Setting up environment variables..."
ENV_FILE="/root/HydraX-v2/.env"

# Add Postgres DSN to .env file
if ! grep -q "POSTGRES_DSN" "$ENV_FILE" 2>/dev/null; then
    echo "POSTGRES_DSN=postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME" >> "$ENV_FILE"
    echo "✅ Added POSTGRES_DSN to .env file"
else
    echo "✅ POSTGRES_DSN already in .env file"
fi

# Set permissions
chmod 600 "$ENV_FILE" 2>/dev/null || true

# Test connection
echo "🧪 Testing database connection..."
python3 << EOF
import os
import sys
sys.path.append('/root/HydraX-v2')

try:
    import psycopg
    dsn = "postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"
    conn = psycopg.connect(dsn)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users")
        result = cur.fetchone()
        print(f"✅ Database connection successful. Users table has {result[0]} rows.")
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo "✅ Database connection test passed"
else
    echo "❌ Database connection test failed"
    exit 1
fi

# Create log directory
mkdir -p /root/HydraX-v2/logs
touch /root/HydraX-v2/logs/postgres_projector.log
chmod 664 /root/HydraX-v2/logs/postgres_projector.log

# Create data directory for projector position tracking
mkdir -p /root/HydraX-v2/data
touch /root/HydraX-v2/data/projector_position.txt
chmod 664 /root/HydraX-v2/data/projector_position.txt

# Make scripts executable
chmod +x /root/HydraX-v2/services/postgres_projector.py

echo ""
echo "🎉 BITTEN v2.1 Postgres Setup Complete!"
echo ""
echo "📋 Summary:"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   Host: $DB_HOST:$DB_PORT"
echo "   Schema: ✅ Created with all tables and views"
echo "   Test User: ✅ User 7176191872 (COMMANDER) ready"
echo ""
echo "🚀 Next Steps:"
echo "1. Start the Postgres projector:"
echo "   python3 /root/HydraX-v2/services/postgres_projector.py --backfill"
echo ""
echo "2. Add admin endpoints to webapp:"
echo "   # Add to webapp_server_optimized.py:"
echo "   from services.admin_endpoints import register_admin_routes"
echo "   register_admin_routes(app)"
echo ""
echo "3. Access admin dashboard:"
echo "   http://localhost:8888/admin/dashboard"
echo ""
echo "4. Test API endpoints:"
echo "   GET  http://localhost:8888/admin/users/telegram/7176191872"
echo "   POST http://localhost:8888/admin/users/1/settings"
echo ""
