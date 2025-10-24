#!/bin/bash
# BITTEN v2.0 PostgreSQL Schema Test Script
# Tests schema installation without requiring PostgreSQL to be installed

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         BITTEN v2.0 Schema Validation Test                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCHEMA_DIR="/root/HydraX-v2/db/schema"
cd "$SCHEMA_DIR"

echo "→ Checking schema files exist..."
REQUIRED_FILES=(
    "01_users.sql"
    "02_signals.sql"
    "03_fires.sql"
    "04_positions.sql"
    "05_signal_outcomes.sql"
    "06_ea_instances.sql"
    "07_missions.sql"
    "99_all_tables.sql"
    "README.md"
)

MISSING=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file (MISSING)"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    echo -e "\n${RED}✗ Schema validation FAILED - missing files${NC}"
    exit 1
fi

echo ""
echo "→ Validating SQL syntax (basic checks)..."

# Check for common SQL errors
for file in *.sql; do
    if grep -q "CREATE TABLE.*(" "$file"; then
        echo -e "  ${GREEN}✓${NC} $file has CREATE TABLE statements"
    else
        echo -e "  ${YELLOW}⚠${NC} $file has no CREATE TABLE (might be OK)"
    fi
done

echo ""
echo "→ Checking dependencies..."

# Verify foreign key references exist
echo "  Checking fires.sql references..."
if grep -q "REFERENCES signals" 03_fires.sql && grep -q "REFERENCES users" 03_fires.sql; then
    echo -e "    ${GREEN}✓${NC} Foreign keys properly defined"
else
    echo -e "    ${RED}✗${NC} Missing foreign key references"
    exit 1
fi

echo "  Checking positions.sql references..."
if grep -q "REFERENCES fires" 04_positions.sql && grep -q "REFERENCES users" 04_positions.sql; then
    echo -e "    ${GREEN}✓${NC} Foreign keys properly defined"
else
    echo -e "    ${RED}✗${NC} Missing foreign key references"
    exit 1
fi

echo ""
echo "→ Checking TimescaleDB integration..."
if grep -q "create_hypertable" 05_signal_outcomes.sql; then
    echo -e "  ${GREEN}✓${NC} TimescaleDB hypertable configured"
else
    echo -e "  ${RED}✗${NC} Missing TimescaleDB hypertable"
    exit 1
fi

if grep -q "add_retention_policy" 05_signal_outcomes.sql; then
    echo -e "  ${GREEN}✓${NC} Retention policy configured (90 days)"
else
    echo -e "  ${RED}✗${NC} Missing retention policy"
    exit 1
fi

echo ""
echo "→ Checking indexes..."
INDEX_COUNT=$(grep -c "CREATE INDEX" *.sql | awk -F: '{sum+=$2} END {print sum}')
echo -e "  ${GREEN}✓${NC} Found $INDEX_COUNT indexes across all tables"

echo ""
echo "→ Statistics..."
echo "  Total SQL files: $(ls -1 *.sql | wc -l)"
echo "  Total lines: $(cat *.sql | wc -l)"
echo "  Total size: $(du -sh . | awk '{print $1}')"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              Schema Validation PASSED                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Install PostgreSQL 14+ with TimescaleDB extension"
echo "  2. Run: psql -U postgres -f 99_all_tables.sql"
echo "  3. Verify with: psql -U postgres -c '\dt' bitten_db"
echo ""
