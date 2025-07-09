#!/bin/bash

# Press Pass Database Migration Runner
# This script executes all Press Pass migrations in the correct order
# and checks for duplicates to avoid re-running migrations

set -e  # Exit on error

# Database connection parameters (update these with your actual values)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-bitten_db}"
DB_USER="${DB_USER:-bitten_app}"
DB_PASSWORD="${DB_PASSWORD}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Function to execute SQL and capture output
execute_sql() {
    local sql_file=$1
    local description=$2
    
    print_status "Executing: $description"
    
    if [ -n "$DB_PASSWORD" ]; then
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -f "$sql_file" -v ON_ERROR_STOP=1
    else
        psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -f "$sql_file" -v ON_ERROR_STOP=1
    fi
    
    if [ $? -eq 0 ]; then
        print_status "✓ Successfully executed: $description"
    else
        print_error "✗ Failed to execute: $description"
        exit 1
    fi
}

# Function to check if migration was already applied
check_migration() {
    local filename=$1
    local result
    
    if [ -n "$DB_PASSWORD" ]; then
        result=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -t -c "SELECT COUNT(*) FROM migration_history WHERE filename = '$filename';" 2>/dev/null || echo "0")
    else
        result=$(psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -t -c "SELECT COUNT(*) FROM migration_history WHERE filename = '$filename';" 2>/dev/null || echo "0")
    fi
    
    # Trim whitespace
    result=$(echo $result | xargs)
    
    if [ "$result" = "0" ] || [ -z "$result" ]; then
        return 1  # Migration not applied
    else
        return 0  # Migration already applied
    fi
}

# Function to create migration_history table if it doesn't exist
ensure_migration_table() {
    print_status "Ensuring migration_history table exists..."
    
    local create_table_sql="
CREATE TABLE IF NOT EXISTS migration_history (
    migration_id BIGSERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);"
    
    if [ -n "$DB_PASSWORD" ]; then
        echo "$create_table_sql" | PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER
    else
        echo "$create_table_sql" | psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER
    fi
    
    print_status "✓ Migration history table ready"
}

# Main execution
print_status "Starting Press Pass Database Migration"
print_status "Database: $DB_NAME@$DB_HOST:$DB_PORT"

# Ensure migration table exists
ensure_migration_table

# Define migrations in order
declare -a migrations=(
    "add_press_pass_tier_enum.sql|Adding PRESS_PASS to database enums"
    "press_pass_tables.sql|Creating Press Pass core tables"
    "press_pass_views.sql|Creating Press Pass analytics views"
    "press_pass_jobs.sql|Setting up Press Pass scheduled jobs"
)

# Execute each migration
for migration in "${migrations[@]}"; do
    IFS='|' read -r filename description <<< "$migration"
    
    if [ ! -f "$filename" ]; then
        print_error "Migration file not found: $filename"
        exit 1
    fi
    
    if check_migration "$filename"; then
        print_warning "Skipping $filename - already applied"
    else
        execute_sql "$filename" "$description"
    fi
done

print_status "================================================================"
print_status "Press Pass migration completed successfully!"
print_status "================================================================"

# Show summary of applied migrations
print_status "Migration Summary:"
if [ -n "$DB_PASSWORD" ]; then
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -c "
    SELECT filename, applied_at 
    FROM migration_history 
    WHERE filename LIKE '%press_pass%' 
    ORDER BY applied_at;"
else
    psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -c "
    SELECT filename, applied_at 
    FROM migration_history 
    WHERE filename LIKE '%press_pass%' 
    ORDER BY applied_at;"
fi

# Optional: Show current Press Pass stats
print_status ""
print_status "Current Press Pass Configuration:"
if [ -n "$DB_PASSWORD" ]; then
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -c "
    SELECT tier, name, price_usd, features->>'daily_shots' as daily_shots, 
           features->>'min_tcs' as min_tcs, is_active
    FROM subscription_plans 
    WHERE tier = 'PRESS_PASS';"
else
    psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER -c "
    SELECT tier, name, price_usd, features->>'daily_shots' as daily_shots, 
           features->>'min_tcs' as min_tcs, is_active
    FROM subscription_plans 
    WHERE tier = 'PRESS_PASS';"
fi