#!/usr/bin/env python3
"""
BITTEN TOC System Startup Script

This script starts the complete TOC system:
1. Initializes databases
2. Starts the unified TOC server
3. Configures terminal pools
4. Connects to Telegram bot
"""

import os
import sys
import logging
import time
import signal
import threading
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import TOC components
from src.toc.terminal_assignment import TerminalAssignment, TerminalType
from src.bitten_core.database.manager import DatabaseManager
from src.bitten_core.database.repository import UserRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/toc_startup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = threading.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Shutdown signal received, stopping TOC system...")
    shutdown_flag.set()


def initialize_databases():
    """Initialize all required databases"""
    logger.info("Initializing databases...")
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Initialize terminal assignments database
    terminal_manager = TerminalAssignment("data/terminal_assignments.db")
    
    # Initialize main BITTEN database
    db_manager = DatabaseManager()
    db_manager.init_db()
    
    logger.info("Databases initialized successfully")
    return terminal_manager, db_manager


def setup_default_terminals(terminal_manager):
    """Setup default terminal configurations"""
    logger.info("Setting up default terminals...")
    
    # Check if terminals already exist
    existing = terminal_manager.get_available_terminals()
    if existing:
        logger.info(f"Found {len(existing)} existing terminals")
        return
    
    # Terminal configurations
    terminals = [
        {
            'name': 'PP-POOL-01',
            'type': TerminalType.PRESS_PASS,
            'ip': os.getenv('BRIDGE_PP_IP', '192.168.1.100'),
            'port': 5001,
            'folder': '/mt5/terminals/press_pass_01',
            'max_users': 10
        },
        {
            'name': 'PP-POOL-02',
            'type': TerminalType.PRESS_PASS,
            'ip': os.getenv('BRIDGE_PP_IP', '192.168.1.100'),
            'port': 5001,
            'folder': '/mt5/terminals/press_pass_02',
            'max_users': 10
        },
        {
            'name': 'DEMO-POOL-01',
            'type': TerminalType.DEMO,
            'ip': os.getenv('BRIDGE_DEMO_IP', '192.168.1.101'),
            'port': 5002,
            'folder': '/mt5/terminals/demo_01',
            'max_users': 5
        },
        {
            'name': 'LIVE-POOL-01',
            'type': TerminalType.LIVE,
            'ip': os.getenv('BRIDGE_LIVE_IP', '192.168.1.102'),
            'port': 5003,
            'folder': '/mt5/terminals/live_01',
            'max_users': 3
        }
    ]
    
    # Add terminals
    for config in terminals:
        try:
            terminal_id = terminal_manager.add_terminal(
                terminal_name=config['name'],
                terminal_type=config['type'],
                ip_address=config['ip'],
                port=config['port'],
                folder_path=config['folder'],
                max_users=config['max_users'],
                metadata={
                    'broker': 'MetaQuotes' if config['type'] == TerminalType.PRESS_PASS else 'ICMarkets',
                    'version': '5.0.36',
                    'region': 'US-East'
                }
            )
            logger.info(f"Added terminal: {config['name']} (ID: {terminal_id})")
        except Exception as e:
            logger.error(f"Failed to add terminal {config['name']}: {e}")
    
    logger.info("Default terminals configured")


def start_toc_server():
    """Start the unified TOC server"""
    logger.info("Starting TOC server...")
    
    try:
        # Start as subprocess
        cmd = [sys.executable, 'src/toc/unified_toc_server.py']
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )
        
        # Give it time to start
        time.sleep(3)
        
        if process.poll() is None:
            logger.info(f"TOC server started with PID {process.pid}")
            return process
        else:
            logger.error("TOC server failed to start")
            return None
            
    except Exception as e:
        logger.error(f"Failed to start TOC server: {e}")
        return None


def check_dependencies():
    """Check if all required services are available"""
    logger.info("Checking dependencies...")
    
    checks = {
        'Telegram Bot Token': os.getenv('TELEGRAM_BOT_TOKEN'),
        'Database Path': Path('data').exists(),
        'Logs Directory': Path('logs').exists()
    }
    
    # Create missing directories
    Path('data').mkdir(exist_ok=True)
    Path('logs').mkdir(exist_ok=True)
    
    failed = []
    for name, check in checks.items():
        if not check:
            failed.append(name)
            logger.warning(f"Missing dependency: {name}")
    
    if failed:
        logger.warning(f"Some dependencies are missing: {', '.join(failed)}")
    else:
        logger.info("All dependencies satisfied")
    
    return len(failed) == 0


def monitor_system(process):
    """Monitor system health"""
    logger.info("Starting system monitoring...")
    
    while not shutdown_flag.is_set():
        try:
            # Check if process is still running
            if process and process.poll() is not None:
                logger.error("TOC server process died, restarting...")
                process = start_toc_server()
            
            # Could add more health checks here
            # - Check database connections
            # - Check terminal availability
            # - Check Telegram bot status
            
            # Wait before next check
            shutdown_flag.wait(30)
            
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            time.sleep(30)


def create_systemd_service():
    """Create systemd service file for production deployment"""
    service_content = """[Unit]
Description=BITTEN TOC System
After=network.target

[Service]
Type=simple
User=bitten
WorkingDirectory=/root/HydraX-v2
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="PYTHONPATH=/root/HydraX-v2"
ExecStart=/usr/bin/python3 /root/HydraX-v2/start_toc_system.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_path = Path("/etc/systemd/system/bitten-toc.service")
    logger.info(f"Systemd service file content:\n{service_content}")
    logger.info(f"To install as service, save above to: {service_path}")


def main():
    """Main startup sequence"""
    print("""
    ╔══════════════════════════════════════════╗
    ║        BITTEN TOC SYSTEM v2.0            ║
    ║    Terminus Operational Core Server      ║
    ╚══════════════════════════════════════════╝
    """)
    
    logger.info("Starting BITTEN TOC System...")
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check dependencies
    if not check_dependencies():
        logger.warning("Some dependencies missing, continuing anyway...")
    
    # Initialize databases
    terminal_manager, db_manager = initialize_databases()
    
    # Setup default terminals
    setup_default_terminals(terminal_manager)
    
    # Start TOC server
    toc_process = start_toc_server()
    if not toc_process:
        logger.error("Failed to start TOC server, exiting...")
        return 1
    
    # Show startup summary
    stats = terminal_manager.get_statistics()
    logger.info("=" * 50)
    logger.info("TOC System Started Successfully!")
    logger.info(f"Terminals configured: {stats['utilization']['total_terminals']}")
    logger.info(f"Total capacity: {stats['utilization']['total_capacity']} users")
    logger.info(f"TOC Server URL: http://localhost:5000")
    logger.info("=" * 50)
    
    # Monitor system
    try:
        monitor_system(toc_process)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    
    # Cleanup
    logger.info("Shutting down TOC system...")
    if toc_process:
        toc_process.terminate()
        toc_process.wait(timeout=10)
    
    logger.info("TOC system stopped")
    return 0


if __name__ == '__main__':
    sys.exit(main())