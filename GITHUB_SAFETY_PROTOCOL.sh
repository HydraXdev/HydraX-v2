#!/bin/bash
# 🛡️ GITHUB SAFETY PROTOCOL - Prevent contaminated code from returning

set -e

REPO_URL="https://github.com/your-repo/HydraX-v2.git"
CLEAN_BASELINE_TAG="CLEAN_BASELINE_$(date +%Y%m%d_%H%M%S)"
QUARANTINE_DIR="/tmp/github_quarantine"

echo "🛡️ GITHUB SAFETY PROTOCOL - Preventing contaminated code re-entry"

# Function to scan incoming code
scan_incoming_code() {
    local code_dir="$1"
    echo "🔍 Scanning incoming code for threats..."

    cd "$code_dir"
    python3 /root/HydraX-v2/SECURITY_SCANNER.py > scan_results.txt

    threat_count=$(grep "Total threats found:" scan_results.txt | grep -o '[0-9]\+')

    if [ "$threat_count" -gt 50 ]; then  # Allow some false positives
        echo "🚨 THREAT DETECTED: $threat_count threats found in incoming code"
        echo "❌ BLOCKING git pull - code appears contaminated"
        cat scan_results.txt
        return 1
    else
        echo "✅ Code appears clean ($threat_count minor issues)"
        return 0
    fi
}

# Function to safely pull from GitHub
safe_git_pull() {
    echo "🔄 Performing SAFE git pull..."

    # Create quarantine directory
    rm -rf "$QUARANTINE_DIR"
    mkdir -p "$QUARANTINE_DIR"

    # Clone to quarantine first
    echo "📥 Cloning to quarantine for inspection..."
    git clone "$REPO_URL" "$QUARANTINE_DIR/code_inspection"

    # Scan the quarantined code
    if scan_incoming_code "$QUARANTINE_DIR/code_inspection"; then
        echo "✅ Code passed security scan - proceeding with merge"

        # Create backup of current state
        git tag "BACKUP_BEFORE_PULL_$(date +%Y%m%d_%H%M%S)"

        # Perform the actual pull
        cd /root/HydraX-v2
        git pull origin main

        # Scan again after pull
        echo "🔍 Post-pull security verification..."
        python3 /root/HydraX-v2/SECURITY_SCANNER.py > post_pull_scan.txt
        post_threat_count=$(grep "Total threats found:" post_pull_scan.txt | grep -o '[0-9]\+')

        if [ "$post_threat_count" -gt 100 ]; then
            echo "🚨 POST-PULL THREATS DETECTED: $post_threat_count"
            echo "🔄 Rolling back to previous state..."
            git reset --hard HEAD~1
            echo "✅ Rollback complete"
            return 1
        fi

    else
        echo "❌ Code failed security scan - pull blocked"
        return 1
    fi

    # Cleanup quarantine
    rm -rf "$QUARANTINE_DIR"
    echo "✅ Safe git pull completed"
}

# Function to push safely (without contamination)
safe_git_push() {
    echo "📤 Performing SAFE git push..."

    # Scan current state before push
    echo "🔍 Pre-push security scan..."
    python3 /root/HydraX-v2/SECURITY_SCANNER.py > pre_push_scan.txt
    threat_count=$(grep "Total threats found:" pre_push_scan.txt | grep -o '[0-9]\+')

    if [ "$threat_count" -gt 50 ]; then
        echo "🚨 CANNOT PUSH: System contains $threat_count threats"
        echo "🧹 Please clean system before pushing"
        cat pre_push_scan.txt
        return 1
    fi

    # Create clean commit
    git add .
    git commit -m "Clean update - security scanned ✅ ($threat_count minor issues)"
    git push origin main

    echo "✅ Clean code pushed to GitHub"
}

# Main execution
case "$1" in
    "pull")
        safe_git_pull
        ;;
    "push")
        safe_git_push
        ;;
    "scan")
        python3 /root/HydraX-v2/SECURITY_SCANNER.py
        ;;
    *)
        echo "Usage: $0 {pull|push|scan}"
        echo "  pull  - Safely pull from GitHub with threat scanning"
        echo "  push  - Safely push to GitHub after cleaning"
        echo "  scan  - Scan current system for threats"
        exit 1
        ;;
esac
