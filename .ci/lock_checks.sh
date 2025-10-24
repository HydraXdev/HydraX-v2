#!/bin/bash

# BITTEN v2 Codebase Lock Checks
# Purpose: Prevent reintroduction of legacy patterns, deprecated code, and versioned bloat
# Exit 0 = PASS, Exit 1 = VIOLATIONS FOUND

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPORT_DIR="$PROJECT_ROOT/reports/lock"

# Initialize report files
mkdir -p "$REPORT_DIR"
VIOLATIONS_FILE="$REPORT_DIR/lock_scan_results.json"
SERVICES_FILE="$REPORT_DIR/allowed_services.json"
IMPORTS_FILE="$REPORT_DIR/banned_imports.json"

# Initialize violation tracking
VIOLATIONS=0
VIOLATION_DETAILS=()

echo "========================================================================"
echo "BITTEN v2 CODEBASE LOCK CHECK"
echo "========================================================================"
echo ""

# ==============================================================================
# CHECK 1: Archive v1 Import Detection
# ==============================================================================
echo -e "${YELLOW}[CHECK 1]${NC} Scanning for imports from archive_v1/..."

ARCHIVE_IMPORTS=$(grep -r "from archive_v1" "$PROJECT_ROOT" --include="*.py" 2>/dev/null || true)
if [ -z "$ARCHIVE_IMPORTS" ]; then
    ARCHIVE_IMPORT_COUNT=0
else
    ARCHIVE_IMPORT_COUNT=$(echo "$ARCHIVE_IMPORTS" | grep -c "from archive_v1" 2>/dev/null || echo "0")
fi

if [ "$ARCHIVE_IMPORT_COUNT" -gt 0 ]; then
    echo -e "${RED}✗ FAIL${NC}: Found $ARCHIVE_IMPORT_COUNT imports from archive_v1/"
    echo "$ARCHIVE_IMPORTS"
    VIOLATIONS=$((VIOLATIONS + 1))
    VIOLATION_DETAILS+=("archive_imports: $ARCHIVE_IMPORT_COUNT violations")
else
    echo -e "${GREEN}✓ PASS${NC}: No archive_v1/ imports found"
fi

# Generate imports report
if [ -z "$ARCHIVE_IMPORTS" ]; then
    VIOLATIONS_JSON="[]"
else
    VIOLATIONS_JSON=$(echo "$ARCHIVE_IMPORTS" | jq -R -s -c 'split("\n") | map(select(length > 0))')
fi

cat > "$IMPORTS_FILE" <<EOF
{
  "check": "banned_imports",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "archive_v1_imports": {
    "count": $ARCHIVE_IMPORT_COUNT,
    "status": "$([ "$ARCHIVE_IMPORT_COUNT" -eq 0 ] && echo 'PASS' || echo 'FAIL')",
    "violations": $VIOLATIONS_JSON
  }
}
EOF

echo ""

# ==============================================================================
# CHECK 2: Banned Filename Patterns
# ==============================================================================
echo -e "${YELLOW}[CHECK 2]${NC} Scanning for banned filename patterns..."

BANNED_FILES=()

# Exclude /tests/, /archive_v1/, /node_modules/, and /migration/ directories from filename checks
# Patterns: *_v1*.py, *_v2*.py, *_old*.py, *_backup*.py, *legacy*, *ARCHIVE*, *experimental*, *debug_*, *smoke_*

while IFS= read -r pattern; do
    # Skip comment lines and archive_v1/ pattern (handled separately)
    [[ "$pattern" =~ ^#.*$ ]] && continue
    [[ "$pattern" == "archive_v1/" ]] && continue
    [[ "$pattern" == "*_tracking.jsonl" ]] && continue
    [[ "$pattern" == "truth_log.jsonl" ]] && continue
    [[ "$pattern" == "*experimental*" ]] && continue  # Skip experimental - often in node_modules

    # Find files matching pattern, excluding safe directories
    MATCHES=$(find "$PROJECT_ROOT" -type f -name "$pattern" \
        ! -path "*/tests/*" \
        ! -path "*/archive_v1/*" \
        ! -path "*/reports/*" \
        ! -path "*/.ci/*" \
        ! -path "*/node_modules/*" \
        ! -path "*/migration/*" \
        ! -path "*/bitten-ui/*" \
        2>/dev/null || true)

    if [ -n "$MATCHES" ]; then
        while IFS= read -r match; do
            BANNED_FILES+=("$match")
        done <<< "$MATCHES"
    fi
done < "$SCRIPT_DIR/banned_patterns.txt"

BANNED_FILE_COUNT=${#BANNED_FILES[@]}

if [ "$BANNED_FILE_COUNT" -gt 0 ]; then
    echo -e "${RED}✗ FAIL${NC}: Found $BANNED_FILE_COUNT banned filename patterns"
    for file in "${BANNED_FILES[@]}"; do
        echo "  - $file"
    done
    VIOLATIONS=$((VIOLATIONS + 1))
    VIOLATION_DETAILS+=("banned_filenames: $BANNED_FILE_COUNT violations")
else
    echo -e "${GREEN}✓ PASS${NC}: No banned filename patterns found"
fi

echo ""

# ==============================================================================
# CHECK 3: JSONL Business Trackers Outside /tests
# ==============================================================================
echo -e "${YELLOW}[CHECK 3]${NC} Scanning for JSONL trackers outside /tests/..."

JSONL_TRACKERS=$(find "$PROJECT_ROOT" -type f \( -name "*_tracking.jsonl" -o -name "truth_log.jsonl" \) \
    ! -path "*/tests/*" \
    ! -path "*/archive_v1/*" \
    ! -path "*/reports/*" \
    ! -path "*/CONTAMINATED_DATA_BACKUP_*/*" \
    2>/dev/null || true)

if [ -z "$JSONL_TRACKERS" ]; then
    JSONL_COUNT=0
else
    JSONL_COUNT=$(echo "$JSONL_TRACKERS" | grep -c ".jsonl" 2>/dev/null || echo "0")
fi

if [ "$JSONL_COUNT" -gt 0 ]; then
    echo -e "${RED}✗ FAIL${NC}: Found $JSONL_COUNT JSONL trackers outside /tests/"
    echo "$JSONL_TRACKERS"
    VIOLATIONS=$((VIOLATIONS + 1))
    VIOLATION_DETAILS+=("jsonl_trackers: $JSONL_COUNT violations")
else
    echo -e "${GREEN}✓ PASS${NC}: No JSONL trackers outside /tests/"
fi

echo ""

# ==============================================================================
# CHECK 4: Service Directory Count
# ==============================================================================
echo -e "${YELLOW}[CHECK 4]${NC} Verifying exactly 5 service directories..."

if [ ! -d "$PROJECT_ROOT/services" ]; then
    echo -e "${RED}✗ FAIL${NC}: /services directory does not exist"
    VIOLATIONS=$((VIOLATIONS + 1))
    VIOLATION_DETAILS+=("services_directory: missing")
    SERVICE_DIRS=()
else
    # Count directories in /services, excluding __pycache__
    SERVICE_DIRS=($(find "$PROJECT_ROOT/services" -mindepth 1 -maxdepth 1 -type d ! -name "__pycache__" -exec basename {} \; 2>/dev/null | sort))
    SERVICE_COUNT=${#SERVICE_DIRS[@]}

    if [ "$SERVICE_COUNT" -ne 5 ]; then
        echo -e "${RED}✗ FAIL${NC}: Expected 5 services, found $SERVICE_COUNT"
        echo "Services found:"
        for svc in "${SERVICE_DIRS[@]}"; do
            echo "  - $svc"
        done
        VIOLATIONS=$((VIOLATIONS + 1))
        VIOLATION_DETAILS+=("service_count: expected 5, found $SERVICE_COUNT")
    else
        # Verify each service matches allowlist
        ALLOWLIST=($(cat "$SCRIPT_DIR/service_allowlist.txt"))
        MISMATCH=0

        for svc in "${SERVICE_DIRS[@]}"; do
            if [[ ! " ${ALLOWLIST[@]} " =~ " ${svc} " ]]; then
                echo -e "${RED}✗ FAIL${NC}: Unauthorized service directory: $svc"
                MISMATCH=1
            fi
        done

        if [ "$MISMATCH" -eq 0 ]; then
            echo -e "${GREEN}✓ PASS${NC}: Exactly 5 authorized services found"
            for svc in "${SERVICE_DIRS[@]}"; do
                echo "  ✓ $svc"
            done
        else
            VIOLATIONS=$((VIOLATIONS + 1))
            VIOLATION_DETAILS+=("service_mismatch: unauthorized services")
        fi
    fi
fi

# Generate services report
SERVICE_JSON=$(printf '%s\n' "${SERVICE_DIRS[@]}" | jq -R . | jq -s .)
cat > "$SERVICES_FILE" <<EOF
{
  "check": "service_directories",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "expected_count": 5,
  "actual_count": ${#SERVICE_DIRS[@]},
  "status": "$([ "${#SERVICE_DIRS[@]}" -eq 5 ] && [ "$MISMATCH" -eq 0 ] && echo 'PASS' || echo 'FAIL')",
  "services": $SERVICE_JSON,
  "allowlist": $(cat "$SCRIPT_DIR/service_allowlist.txt" | jq -R . | jq -s .)
}
EOF

echo ""

# ==============================================================================
# CHECK 5: Banned Keywords in Code
# ==============================================================================
echo -e "${YELLOW}[CHECK 5]${NC} Scanning for banned keywords..."

BANNED_KEYWORDS=("XSTREAM" "buffer_replay")
KEYWORD_VIOLATIONS=()

for keyword in "${BANNED_KEYWORDS[@]}"; do
    MATCHES=$(grep -r "$keyword" "$PROJECT_ROOT" \
        --include="*.py" \
        ! -path "*/tests/*" \
        ! -path "*/archive_v1/*" \
        ! -path "*/.ci/*" \
        ! -path "*/reports/*" \
        2>/dev/null || true)

    if [ -n "$MATCHES" ]; then
        MATCH_COUNT=$(echo "$MATCHES" | wc -l)
        echo -e "${RED}✗ FAIL${NC}: Found '$keyword' in $MATCH_COUNT locations"
        echo "$MATCHES" | head -5
        [ "$MATCH_COUNT" -gt 5 ] && echo "  ... and $((MATCH_COUNT - 5)) more"
        KEYWORD_VIOLATIONS+=("$keyword: $MATCH_COUNT")
    fi
done

# Check for file-backed signal/fire queues
FILE_QUEUE_PATTERNS=("fire.txt" "trade_result.txt" "signal_queue.txt")
FILE_QUEUE_VIOLATIONS=()

for pattern in "${FILE_QUEUE_PATTERNS[@]}"; do
    MATCHES=$(grep -r "$pattern" "$PROJECT_ROOT" \
        --include="*.py" \
        ! -path "*/tests/*" \
        ! -path "*/archive_v1/*" \
        ! -path "*/.ci/*" \
        ! -path "*/reports/*" \
        ! -path "*/CLAUDE.md" \
        2>/dev/null || true)

    if [ -n "$MATCHES" ]; then
        MATCH_COUNT=$(echo "$MATCHES" | wc -l)
        echo -e "${RED}✗ FAIL${NC}: Found file-backed queue '$pattern' in $MATCH_COUNT locations"
        echo "$MATCHES" | head -3
        FILE_QUEUE_VIOLATIONS+=("$pattern: $MATCH_COUNT")
    fi
done

KEYWORD_VIOLATION_COUNT=$((${#KEYWORD_VIOLATIONS[@]} + ${#FILE_QUEUE_VIOLATIONS[@]}))

if [ "$KEYWORD_VIOLATION_COUNT" -gt 0 ]; then
    VIOLATIONS=$((VIOLATIONS + 1))
    VIOLATION_DETAILS+=("banned_keywords: $KEYWORD_VIOLATION_COUNT types")
else
    echo -e "${GREEN}✓ PASS${NC}: No banned keywords found"
fi

echo ""

# ==============================================================================
# FINAL REPORT
# ==============================================================================
echo "========================================================================"
echo "LOCK CHECK SUMMARY"
echo "========================================================================"

# Generate final violations report
if [ ${#VIOLATION_DETAILS[@]} -eq 0 ]; then
    VIOLATIONS_JSON="[]"
else
    VIOLATIONS_JSON=$(printf '%s\n' "${VIOLATION_DETAILS[@]}" | jq -R . | jq -s .)
fi

cat > "$VIOLATIONS_FILE" <<EOF
{
  "check": "codebase_lock",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "$([ "$VIOLATIONS" -eq 0 ] && echo 'PASS' || echo 'FAIL')",
  "total_violations": $VIOLATIONS,
  "violations": $VIOLATIONS_JSON,
  "checks": {
    "archive_imports": "$([ "$ARCHIVE_IMPORT_COUNT" -eq 0 ] && echo 'PASS' || echo 'FAIL')",
    "banned_filenames": "$([ "$BANNED_FILE_COUNT" -eq 0 ] && echo 'PASS' || echo 'FAIL')",
    "jsonl_trackers": "$([ "$JSONL_COUNT" -eq 0 ] && echo 'PASS' || echo 'FAIL')",
    "service_directories": "$([ "${#SERVICE_DIRS[@]}" -eq 5 ] && [ "$MISMATCH" -eq 0 ] && echo 'PASS' || echo 'FAIL')",
    "banned_keywords": "$([ "$KEYWORD_VIOLATION_COUNT" -eq 0 ] && echo 'PASS' || echo 'FAIL')"
  }
}
EOF

if [ "$VIOLATIONS" -eq 0 ]; then
    echo -e "${GREEN}✓✓✓ ALL CHECKS PASSED ✓✓✓${NC}"
    echo ""
    echo "Codebase is clean:"
    echo "  ✓ No archive_v1/ imports"
    echo "  ✓ No banned filename patterns"
    echo "  ✓ No JSONL trackers outside /tests"
    echo "  ✓ Exactly 5 authorized services"
    echo "  ✓ No banned keywords"
    echo ""
    echo "Reports generated:"
    echo "  - $VIOLATIONS_FILE"
    echo "  - $SERVICES_FILE"
    echo "  - $IMPORTS_FILE"
    echo ""
    exit 0
else
    echo -e "${RED}✗✗✗ $VIOLATIONS CHECK(S) FAILED ✗✗✗${NC}"
    echo ""
    echo "Violations detected:"
    for detail in "${VIOLATION_DETAILS[@]}"; do
        echo "  ✗ $detail"
    done
    echo ""
    echo "Reports generated:"
    echo "  - $VIOLATIONS_FILE"
    echo "  - $SERVICES_FILE"
    echo "  - $IMPORTS_FILE"
    echo ""
    echo "Fix violations before committing."
    exit 1
fi
