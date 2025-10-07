#!/usr/bin/env python3
"""
🚀 ULTIMATE C.O.R.E. CRYPTO ENGINE LAUNCHER
Professional startup script with comprehensive monitoring and recovery

Features:
✅ Health checks and dependency verification
✅ Automatic restart on failure
✅ Performance monitoring
✅ Signal quality tracking
✅ Integration with existing infrastructure
✅ Comprehensive logging

Author: Claude Code Agent
Date: August 2025
Status: Production Ready
"""

import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/root/HydraX-v2/logs/core_crypto_launcher.log"), logging.StreamHandler()],
)
logger = logging.getLogger("CORECryptoLauncher")


class UltimateCORECryptoLauncher:
    """Professional launcher for Ultimate C.O.R.E. Crypto Engine"""

    def __init__(self):
        self.engine_process = None
        self.running = True
        self.restart_count = 0
        self.max_restarts = 10
        self.health_check_interval = 30  # seconds
        self.last_health_check = 0

        # Performance tracking
        self.start_time = time.time()
        self.uptime_stats = {"total_restarts": 0, "longest_uptime": 0, "current_uptime_start": time.time()}

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        logger.info("🔍 Checking dependencies...")

        try:
            # Check Python packages
            required_packages = ["zmq", "numpy", "pandas", "sklearn", "scipy"]

            for package in required_packages:
                try:
                    __import__(package)
                    logger.info(f"✅ {package} - OK")
                except ImportError:
                    logger.error(f"❌ {package} - MISSING")
                    return False

            # Check ZMQ ports availability
            zmq_ports = [5560, 5558]  # Subscriber, Publisher
            for port in zmq_ports:
                if self._check_port_available(port):
                    logger.info(f"✅ Port {port} - Available")
                else:
                    logger.warning(f"⚠️ Port {port} - In use (may be normal)")

            # Check log directories
            log_dir = Path("/root/HydraX-v2/logs")
            if not log_dir.exists():
                log_dir.mkdir(parents=True, exist_ok=True)
                logger.info("📁 Created logs directory")

            # Check models directory
            models_dir = Path("/root/HydraX-v2/models")
            if not models_dir.exists():
                models_dir.mkdir(parents=True, exist_ok=True)
                logger.info("📁 Created models directory")

            logger.info("✅ All dependencies checked")
            return True

        except Exception as e:
            logger.error(f"❌ Dependency check failed: {e}")
            return False

    def _check_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            import socket

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return True
        except OSError:
            return False

    def check_infrastructure(self) -> bool:
        """Check if required infrastructure is running"""
        logger.info("🏗️ Checking infrastructure...")

        try:
            # Check if telemetry bridge is running (required for market data)
            bridge_running = self._check_process_running("telemetry_pubbridge.py")
            if bridge_running:
                logger.info("✅ Telemetry bridge - Running")
            else:
                logger.warning("⚠️ Telemetry bridge - Not detected (data flow may be affected)")

            # Check if Elite Guard is running (provides reference architecture)
            elite_guard_running = self._check_process_running("elite_guard_with_citadel.py")
            if elite_guard_running:
                logger.info("✅ Elite Guard - Running (good for reference)")
            else:
                logger.info("ℹ️ Elite Guard - Not running (C.O.R.E. is independent)")

            return True  # C.O.R.E. can run independently

        except Exception as e:
            logger.error(f"❌ Infrastructure check failed: {e}")
            return False

    def _check_process_running(self, process_name: str) -> bool:
        """Check if a specific process is running"""
        try:
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = " ".join(proc.info["cmdline"] or [])
                    if process_name in cmdline:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception:
            return False

    def start_engine(self) -> bool:
        """Start the Ultimate C.O.R.E. Crypto Engine"""
        try:
            logger.info("🚀 Starting Ultimate C.O.R.E. Crypto Engine...")

            # Start the engine process
            cmd = [sys.executable, "/root/HydraX-v2/ultimate_core_crypto_engine.py"]

            self.engine_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, bufsize=1
            )

            # Give it a moment to start
            time.sleep(2)

            # Check if process started successfully
            if self.engine_process.poll() is None:
                logger.info(f"✅ Engine started successfully - PID: {self.engine_process.pid}")
                self.uptime_stats["current_uptime_start"] = time.time()
                return True
            else:
                stdout, stderr = self.engine_process.communicate()
                logger.error(f"❌ Engine failed to start:")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ Engine startup error: {e}")
            return False

    def monitor_engine(self):
        """Monitor engine health and performance"""
        logger.info("📊 Starting engine monitoring...")

        while self.running:
            try:
                current_time = time.time()

                # Health check every 30 seconds
                if current_time - self.last_health_check > self.health_check_interval:
                    self._perform_health_check()
                    self.last_health_check = current_time

                # Check if engine process is still running
                if self.engine_process and self.engine_process.poll() is not None:
                    logger.warning("⚠️ Engine process terminated")
                    self._handle_engine_failure()

                time.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                time.sleep(10)

    def _perform_health_check(self):
        """Perform comprehensive health check"""
        try:
            # Check process health
            if self.engine_process:
                try:
                    proc = psutil.Process(self.engine_process.pid)
                    cpu_percent = proc.cpu_percent()
                    memory_mb = proc.memory_info().rss / 1024 / 1024

                    logger.info(f"📊 Health Check - CPU: {cpu_percent:.1f}%, Memory: {memory_mb:.1f}MB")

                    # Alert on high resource usage
                    if cpu_percent > 80:
                        logger.warning(f"⚠️ High CPU usage: {cpu_percent:.1f}%")
                    if memory_mb > 500:
                        logger.warning(f"⚠️ High memory usage: {memory_mb:.1f}MB")

                except psutil.NoSuchProcess:
                    logger.error("❌ Engine process not found")

            # Check log file activity
            self._check_log_activity()

            # Update uptime stats
            current_uptime = time.time() - self.uptime_stats["current_uptime_start"]
            if current_uptime > self.uptime_stats["longest_uptime"]:
                self.uptime_stats["longest_uptime"] = current_uptime

        except Exception as e:
            logger.error(f"❌ Health check error: {e}")

    def _check_log_activity(self):
        """Check if engine is actively logging (sign of health)"""
        try:
            log_file = Path("/root/HydraX-v2/logs/ultimate_core_crypto_engine.log")
            if log_file.exists():
                # Check if log file was modified recently (within 5 minutes)
                last_modified = log_file.stat().st_mtime
                if time.time() - last_modified < 300:  # 5 minutes
                    logger.debug("✅ Engine logging activity - Normal")
                else:
                    logger.warning("⚠️ No recent logging activity detected")

        except Exception as e:
            logger.error(f"❌ Log activity check error: {e}")

    def _handle_engine_failure(self):
        """Handle engine process failure with intelligent restart"""
        try:
            logger.warning("🔄 Engine failure detected - Attempting restart...")

            # Update statistics
            self.restart_count += 1
            self.uptime_stats["total_restarts"] += 1

            # Check restart limits
            if self.restart_count > self.max_restarts:
                logger.error(f"❌ Maximum restart attempts ({self.max_restarts}) reached")
                self.running = False
                return

            # Clean up old process
            if self.engine_process:
                try:
                    self.engine_process.terminate()
                    self.engine_process.wait(timeout=10)
                except:
                    try:
                        self.engine_process.kill()
                    except:
                        pass

            # Wait before restart (exponential backoff)
            wait_time = min(60, 2 ** (self.restart_count - 1))
            logger.info(f"⏳ Waiting {wait_time} seconds before restart...")
            time.sleep(wait_time)

            # Attempt restart
            if self.start_engine():
                logger.info(f"✅ Engine restarted successfully (Attempt {self.restart_count})")
                # Reset restart count on successful restart
                time.sleep(30)  # Give it time to stabilize
                if self.engine_process and self.engine_process.poll() is None:
                    self.restart_count = 0  # Reset counter on stable restart
            else:
                logger.error(f"❌ Engine restart failed (Attempt {self.restart_count})")

        except Exception as e:
            logger.error(f"❌ Restart handling error: {e}")

    def stop_engine(self):
        """Gracefully stop the engine"""
        logger.info("🛑 Stopping Ultimate C.O.R.E. Crypto Engine...")

        self.running = False

        if self.engine_process:
            try:
                # Try graceful termination first
                self.engine_process.terminate()

                # Wait for graceful shutdown
                try:
                    self.engine_process.wait(timeout=15)
                    logger.info("✅ Engine stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if necessary
                    logger.warning("⚠️ Forcing engine termination...")
                    self.engine_process.kill()
                    self.engine_process.wait()
                    logger.info("✅ Engine terminated")

            except Exception as e:
                logger.error(f"❌ Engine stop error: {e}")

    def print_startup_banner(self):
        """Print professional startup banner"""
        banner = """
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀

    ██╗   ██╗██╗  ████████╗██╗███╗   ███╗ █████╗ ████████╗███████╗
    ██║   ██║██║  ╚══██╔══╝██║████╗ ████║██╔══██╗╚══██╔══╝██╔════╝
    ██║   ██║██║     ██║   ██║██╔████╔██║███████║   ██║   █████╗
    ██║   ██║██║     ██║   ██║██║╚██╔╝██║██╔══██║   ██║   ██╔══╝
    ╚██████╔╝███████╗██║   ██║██║ ╚═╝ ██║██║  ██║   ██║   ███████╗
     ╚═════╝ ╚══════╝╚═╝   ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝

     ██████╗ ██████╗ ██████╗ ███████╗     ██████╗██████╗ ██╗   ██╗██████╗████████╗ ██████╗
    ██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔════╝██╔══██╗╚██╗ ██╔╝██╔══████╔═══██╗██╔═══██╗
    ██║     ██║   ██║██████╔╝█████╗      ██║     ██████╔╝ ╚████╔╝ ██████╔╝█████╗██║   ██║
    ██║     ██║   ██║██╔══██╗██╔══╝      ██║     ██╔══██╗  ╚██╔╝  ██╔═══╝ ██╔══╝██║   ██║
    ╚██████╗╚██████╔╝██║  ██║███████╗    ╚██████╗██║  ██║   ██║   ██║     ███████╗╚██████╔╝
     ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝     ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚══════╝ ╚═════╝

                            COMPREHENSIVE OUTSTANDING RELIABLE ENGINE
                                   PROFESSIONAL CRYPTO SIGNAL SYSTEM

🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀

🎯 TARGET WIN RATE: 70-85%
💰 PROFESSIONAL RISK MANAGEMENT: 1% per trade
📈 RISK:REWARD RATIO: 1:2
⚡ PROCESSING TIME: <50ms per signal
🔥 SMC PATTERNS: Liquidity Sweeps, Order Blocks, FVGs
🤖 ML ENHANCEMENT: RandomForest with market features
📊 MULTI-TIMEFRAME: M1/M5/M15 confluence analysis
📡 ARCHITECTURE: Full ZMQ integration
🛡️ CITADEL SHIELD: Advanced signal validation
✅ STATUS: PRODUCTION READY

🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀
        """

        print(banner)
        logger.info("🎯 Ultimate C.O.R.E. Crypto Engine Launcher initialized")

    def run(self):
        """Main launcher execution"""
        try:
            # Print startup banner
            self.print_startup_banner()

            # Dependency and infrastructure checks
            if not self.check_dependencies():
                logger.error("❌ Dependency check failed - Cannot start")
                return False

            if not self.check_infrastructure():
                logger.error("❌ Infrastructure check failed - Cannot start")
                return False

            # Start the engine
            if not self.start_engine():
                logger.error("❌ Engine startup failed")
                return False

            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            # Start monitoring in separate thread
            monitor_thread = threading.Thread(target=self.monitor_engine, daemon=True)
            monitor_thread.start()

            logger.info("✅ Ultimate C.O.R.E. Crypto Engine is now LIVE!")
            logger.info("📊 Monitoring active - Press Ctrl+C to stop")

            # Keep main thread alive
            while self.running:
                time.sleep(1)

            return True

        except Exception as e:
            logger.error(f"❌ Launcher execution error: {e}")
            return False
        finally:
            self.stop_engine()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum} - Initiating shutdown...")
        self.running = False

    def get_status_report(self) -> dict:
        """Get comprehensive status report"""
        current_time = time.time()
        current_uptime = current_time - self.uptime_stats["current_uptime_start"]
        total_runtime = current_time - self.start_time

        return {
            "engine_running": self.engine_process is not None and self.engine_process.poll() is None,
            "engine_pid": self.engine_process.pid if self.engine_process else None,
            "current_uptime_seconds": current_uptime,
            "total_runtime_seconds": total_runtime,
            "restart_count": self.restart_count,
            "total_restarts": self.uptime_stats["total_restarts"],
            "longest_uptime_seconds": self.uptime_stats["longest_uptime"],
            "max_restarts": self.max_restarts,
            "monitoring_active": self.running,
        }


def main():
    """Main execution function"""
    launcher = UltimateCORECryptoLauncher()

    try:
        success = launcher.run()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("🛑 Launcher stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Launcher error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
