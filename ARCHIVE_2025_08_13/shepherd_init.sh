#!/bin/bash
# SHEPHERD Initialization Script
# Production-ready initialization with comprehensive error handling

set -euo pipefail  # Exit on error, undefined variables, pipe failures
IFS=$'\n\t'       # Set secure Internal Field Separator

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"
SHEPHERD_DIR="${PROJECT_ROOT}/bitten/core/shepherd"
DATA_DIR="${PROJECT_ROOT}/bitten/data/shepherd"
LOG_DIR="${PROJECT_ROOT}/logs/shepherd"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HEALTHCHECK_INTERVAL=60  # seconds

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $*"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" >&2
}

# Error handler
handle_error() {
    local line_no=$1
    local error_code=$2
    log_error "Script failed at line ${line_no} with error code ${error_code}"
    log_error "Stack trace:"
    local frame=0
    while caller $frame; do
        ((frame++))
    done
    exit "${error_code}"
}

trap 'handle_error ${LINENO} $?' ERR

# Check if running as root (optional warning)
check_root_privileges() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. Consider running as a dedicated user for security."
    fi
}

# Check Python version
check_python_version() {
    log_info "Checking Python version..."
    
    if ! command -v "${PYTHON_BIN}" &> /dev/null; then
        log_error "Python not found. Please install Python 3.8 or higher."
        return 1
    fi
    
    local python_version
    python_version=$("${PYTHON_BIN}" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    
    if [[ "$(echo "${python_version} < 3.8" | bc)" -eq 1 ]]; then
        log_error "Python ${python_version} detected. SHEPHERD requires Python 3.8 or higher."
        return 1
    fi
    
    log_success "Python ${python_version} detected"
    return 0
}

# Check and install Python dependencies
check_dependencies() {
    log_info "Checking Python dependencies..."
    
    local requirements_file="${PROJECT_ROOT}/requirements.txt"
    local missing_deps=()
    
    # Check core dependencies
    local core_deps=("ast" "json" "pathlib" "typing" "dataclasses")
    
    for dep in "${core_deps[@]}"; do
        if ! "${PYTHON_BIN}" -c "import ${dep}" &> /dev/null; then
            missing_deps+=("${dep}")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_warning "Missing dependencies: ${missing_deps[*]}"
        
        # Install requirements if file exists
        if [[ -f "${requirements_file}" ]]; then
            log_info "Installing dependencies from requirements.txt..."
            "${PYTHON_BIN}" -m pip install -r "${requirements_file}" --quiet
        else
            log_warning "requirements.txt not found. Installing core dependencies..."
            "${PYTHON_BIN}" -m pip install dataclasses typing --quiet
        fi
    fi
    
    log_success "All dependencies satisfied"
    return 0
}

# Initialize data directories
initialize_directories() {
    log_info "Initializing data directories..."
    
    local directories=(
        "${DATA_DIR}"
        "${LOG_DIR}"
        "${DATA_DIR}/indexes"
        "${DATA_DIR}/cache"
        "${DATA_DIR}/backups"
        "${LOG_DIR}/indexer"
        "${LOG_DIR}/query"
        "${LOG_DIR}/health"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "${dir}" ]]; then
            mkdir -p "${dir}"
            log_info "Created directory: ${dir}"
        else
            log_info "Directory exists: ${dir}"
        fi
        
        # Set appropriate permissions
        chmod 755 "${dir}"
    done
    
    log_success "All directories initialized"
    return 0
}

# Backup existing index if present
backup_existing_index() {
    local index_file="${DATA_DIR}/shepherd_index.json"
    
    if [[ -f "${index_file}" ]]; then
        local backup_dir="${DATA_DIR}/backups"
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local backup_file="${backup_dir}/shepherd_index_${timestamp}.json"
        
        log_info "Backing up existing index..."
        cp "${index_file}" "${backup_file}"
        
        # Compress old backups (keep last 10)
        local backup_count=$(ls -1 "${backup_dir}"/shepherd_index_*.json 2>/dev/null | wc -l)
        if [[ ${backup_count} -gt 10 ]]; then
            log_info "Compressing old backups..."
            ls -1t "${backup_dir}"/shepherd_index_*.json | tail -n +11 | xargs -I {} gzip {}
        fi
        
        log_success "Index backed up to: ${backup_file}"
    fi
}

# Build initial index
build_index() {
    log_info "Building SHEPHERD index..."
    
    backup_existing_index
    
    # Set Python path
    export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"
    
    # Run indexer with error handling
    local start_time=$(date +%s)
    local index_log="${LOG_DIR}/indexer/build_$(date +%Y%m%d_%H%M%S).log"
    
    if "${PYTHON_BIN}" "${SHEPHERD_DIR}/indexer.py" 2>&1 | tee "${index_log}"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_success "Index built successfully in ${duration} seconds"
        
        # Verify index file
        local index_file="${DATA_DIR}/shepherd_index.json"
        if [[ -f "${index_file}" ]]; then
            local component_count=$(jq '.metadata.total_components' "${index_file}" 2>/dev/null || echo "0")
            log_info "Index contains ${component_count} components"
        else
            log_error "Index file not created"
            return 1
        fi
    else
        log_error "Failed to build index. Check log: ${index_log}"
        return 1
    fi
    
    return 0
}

# Start SHEPHERD in watch mode
start_watch_mode() {
    log_info "Starting SHEPHERD in watch mode..."
    
    # Check if already running
    if pgrep -f "shepherd_watch.py" > /dev/null; then
        log_warning "SHEPHERD watch mode is already running"
        return 0
    fi
    
    # Create watch script if it doesn't exist
    local watch_script="${SHEPHERD_DIR}/shepherd_watch.py"
    if [[ ! -f "${watch_script}" ]]; then
        log_info "Creating watch mode script..."
        cat > "${watch_script}" << 'EOF'
#!/usr/bin/env python3
"""SHEPHERD Watch Mode - Monitors codebase changes and updates index"""

import os
import sys
import time
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add project root to path
sys.path.insert(0, '/root/HydraX-v2')

from bitten.core.shepherd.indexer import BITTENIndexer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/HydraX-v2/logs/shepherd/watch.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ShepherdWatcher(FileSystemEventHandler):
    def __init__(self, base_path, debounce_seconds=5):
        self.base_path = Path(base_path)
        self.indexer = BITTENIndexer(base_path)
        self.debounce_seconds = debounce_seconds
        self.pending_update = False
        self.last_update = 0
        self.file_hashes = {}
        self.load_file_hashes()
    
    def load_file_hashes(self):
        """Load existing file hashes"""
        hash_file = self.base_path / "bitten/data/shepherd/file_hashes.json"
        if hash_file.exists():
            with open(hash_file, 'r') as f:
                self.file_hashes = json.load(f)
    
    def save_file_hashes(self):
        """Save file hashes"""
        hash_file = self.base_path / "bitten/data/shepherd/file_hashes.json"
        with open(hash_file, 'w') as f:
            json.dump(self.file_hashes, f, indent=2)
    
    def get_file_hash(self, filepath):
        """Calculate file hash"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Only process Python files
        if not event.src_path.endswith('.py'):
            return
        
        # Skip files in certain directories
        skip_dirs = ['__pycache__', '.git', 'venv', 'env', 'logs', 'data']
        if any(skip_dir in event.src_path for skip_dir in skip_dirs):
            return
        
        # Check if file content actually changed
        file_hash = self.get_file_hash(event.src_path)
        if file_hash and self.file_hashes.get(event.src_path) == file_hash:
            return
        
        self.file_hashes[event.src_path] = file_hash
        logger.info(f"Detected change in: {event.src_path}")
        self.pending_update = True
    
    def update_index(self):
        """Update the SHEPHERD index"""
        if not self.pending_update:
            return
        
        current_time = time.time()
        if current_time - self.last_update < self.debounce_seconds:
            return
        
        logger.info("Updating SHEPHERD index...")
        try:
            self.indexer.scan_codebase()
            self.save_file_hashes()
            self.pending_update = False
            self.last_update = current_time
            logger.info("Index updated successfully")
        except Exception as e:
            logger.error(f"Failed to update index: {e}")

def main():
    base_path = "/root/HydraX-v2"
    watcher = ShepherdWatcher(base_path)
    
    # Set up file system observer
    observer = Observer()
    observer.schedule(watcher, base_path, recursive=True)
    observer.start()
    
    logger.info(f"SHEPHERD watch mode started. Monitoring: {base_path}")
    
    try:
        while True:
            time.sleep(1)
            watcher.update_index()
    except KeyboardInterrupt:
        observer.stop()
        logger.info("SHEPHERD watch mode stopped")
    
    observer.join()

if __name__ == "__main__":
    main()
EOF
        chmod +x "${watch_script}"
    fi
    
    # Install watchdog if not present
    if ! "${PYTHON_BIN}" -c "import watchdog" &> /dev/null; then
        log_info "Installing watchdog dependency..."
        "${PYTHON_BIN}" -m pip install watchdog --quiet
    fi
    
    # Start watch mode in background
    nohup "${PYTHON_BIN}" "${watch_script}" > "${LOG_DIR}/watch.log" 2>&1 &
    local watch_pid=$!
    
    # Save PID for later management
    echo ${watch_pid} > "${DATA_DIR}/shepherd_watch.pid"
    
    log_success "SHEPHERD watch mode started with PID: ${watch_pid}"
    return 0
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    local health_script="${PROJECT_ROOT}/shepherd_healthcheck.py"
    
    if [[ -f "${health_script}" ]]; then
        if "${PYTHON_BIN}" "${health_script}"; then
            log_success "All health checks passed"
        else
            log_warning "Some health checks failed"
        fi
    else
        log_warning "Health check script not found. Creating basic checks..."
        
        # Basic health checks
        local index_file="${DATA_DIR}/shepherd_index.json"
        if [[ -f "${index_file}" ]]; then
            local file_age=$(($(date +%s) - $(stat -c %Y "${index_file}")))
            if [[ ${file_age} -gt 86400 ]]; then
                log_warning "Index file is more than 24 hours old"
            fi
        else
            log_error "Index file not found"
        fi
        
        # Check if watch mode is running
        if [[ -f "${DATA_DIR}/shepherd_watch.pid" ]]; then
            local watch_pid=$(cat "${DATA_DIR}/shepherd_watch.pid")
            if ! kill -0 ${watch_pid} 2>/dev/null; then
                log_warning "Watch mode is not running"
            fi
        fi
    fi
    
    return 0
}

# Main initialization
main() {
    log_info "Starting SHEPHERD initialization..."
    log_info "Project root: ${PROJECT_ROOT}"
    
    # Run all initialization steps
    check_root_privileges
    check_python_version || exit 1
    check_dependencies || exit 1
    initialize_directories || exit 1
    build_index || exit 1
    start_watch_mode || exit 1
    run_health_checks || exit 1
    
    log_success "SHEPHERD initialization completed successfully!"
    log_info "SHEPHERD is now monitoring the codebase for changes"
    log_info "Health checks will run every ${HEALTHCHECK_INTERVAL} seconds"
    
    # Optional: Start continuous health monitoring
    if [[ "${1:-}" == "--monitor" ]]; then
        log_info "Starting continuous health monitoring..."
        while true; do
            sleep ${HEALTHCHECK_INTERVAL}
            run_health_checks
        done
    fi
}

# Run main function
main "$@"