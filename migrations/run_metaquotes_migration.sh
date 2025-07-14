#!/bin/bash

# MetaQuotes Demo Account Tables Migration Script
# This script creates all necessary tables for the MetaQuotes integration

echo "=========================================="
echo "MetaQuotes Demo Account Migration"
echo "=========================================="
echo "Starting at: $(date)"

# Database connection parameters
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-bitten_test}"
DB_USER="${POSTGRES_USER:-postgres}"

# Export password to avoid prompt
export PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"

echo ""
echo "Database Configuration:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Function to run SQL file
run_sql_file() {
    local file=$1
    local description=$2
    
    echo "Running $description..."
    
    if psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -f "$file" > /tmp/migration_output.log 2>&1; then
        echo "  ✅ $description completed successfully"
        return 0
    else
        echo "  ❌ $description failed!"
        echo "  Error output:"
        cat /tmp/migration_output.log
        return 1
    fi
}

# Check if PostgreSQL is accessible
echo "Checking database connection..."
if psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "  ✅ Database connection successful"
else
    echo "  ❌ Cannot connect to database!"
    echo "  Please check your database settings and try again."
    exit 1
fi

# Run MetaQuotes migration
echo ""
echo "Creating MetaQuotes demo account tables..."

if run_sql_file "metaquotes_demo_accounts.sql" "MetaQuotes demo account tables"; then
    echo ""
    echo "Verifying tables..."
    
    # Check if tables were created
    TABLES_CHECK=$(psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -t -c "
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN (
            'demo_account_pool',
            'user_demo_accounts',
            'demo_provisioning_queue',
            'metaquotes_api_config',
            'demo_account_health_logs',
            'credential_encryption_keys'
        );
    ")
    
    TABLES_COUNT=$(echo $TABLES_CHECK | tr -d ' ')
    
    if [ "$TABLES_COUNT" -eq "6" ]; then
        echo "  ✅ All 6 MetaQuotes tables created successfully"
    else
        echo "  ⚠️  Only $TABLES_COUNT of 6 expected tables found"
    fi
    
    # Check if functions were created
    FUNCTIONS_CHECK=$(psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -t -c "
        SELECT COUNT(*) 
        FROM information_schema.routines 
        WHERE routine_schema = 'public' 
        AND routine_name IN (
            'get_next_available_demo_account',
            'check_demo_account_health',
            'cleanup_expired_demo_accounts'
        );
    ")
    
    FUNCTIONS_COUNT=$(echo $FUNCTIONS_CHECK | tr -d ' ')
    
    if [ "$FUNCTIONS_COUNT" -eq "3" ]; then
        echo "  ✅ All 3 MetaQuotes functions created successfully"
    else
        echo "  ⚠️  Only $FUNCTIONS_COUNT of 3 expected functions found"
    fi
    
    # Check initial data
    API_CONFIG_CHECK=$(psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -t -c "
        SELECT COUNT(*) FROM metaquotes_api_config WHERE api_name = 'MetaQuotes-Demo-API';
    ")
    
    if [ "$(echo $API_CONFIG_CHECK | tr -d ' ')" -eq "1" ]; then
        echo "  ✅ Initial API configuration inserted"
    else
        echo "  ⚠️  Initial API configuration not found"
    fi
    
    echo ""
    echo "=========================================="
    echo "✅ MetaQuotes migration completed successfully!"
    echo "=========================================="
    
    # Show summary
    echo ""
    echo "Summary of created objects:"
    echo "  - 6 database tables for demo account management"
    echo "  - 3 stored functions for account operations"
    echo "  - Multiple indexes for performance optimization"
    echo "  - Initial configuration data"
    echo ""
    echo "Next steps:"
    echo "  1. Start the MetaQuotes services: python start_metaquotes_services.py"
    echo "  2. Run integration tests: python test_metaquotes_integration.py"
    echo "  3. Configure API endpoints in your application"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ Migration failed!"
    echo "=========================================="
    echo "Please check the error messages above and try again."
    exit 1
fi

# Cleanup
unset PGPASSWORD
rm -f /tmp/migration_output.log

echo "Completed at: $(date)"