#!/usr/bin/env python3
"""
Process Coordination Script for EA v2.07 Signal Engine
Manages stopping/starting conflicting processes to enable clean EA v2.07 implementation

This script coordinates:
- command_router.py (PID 2530882) on port 5555
- zmq_telemetry_bridge_v207.py (PID 2346356) on ports 5556, 5560
- confirm_listener_v207.py (PID 2420923) on port 5558
"""

import subprocess
import time
import signal
import os
import sys
import json
from pathlib import Path

class ProcessCoordinator:
    def __init__(self):
        self.config_file = Path("/root/HydraX-v2/v207_process_state.json")
        self.stopped_processes = {}
        self.load_state()

    def load_state(self):
        """Load previously stopped process state"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.stopped_processes = json.load(f)
                print(f"📂 Loaded state: {len(self.stopped_processes)} processes tracked")
            except Exception as e:
                print(f"⚠️ Error loading state: {e}")
                self.stopped_processes = {}

    def save_state(self):
        """Save stopped process state for restoration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.stopped_processes, f, indent=2)
            print(f"💾 Saved state: {len(self.stopped_processes)} processes tracked")
        except Exception as e:
            print(f"❌ Error saving state: {e}")

    def get_process_info(self, pid):
        """Get detailed process information"""
        try:
            result = subprocess.run(['ps', '-p', str(pid), '-o', 'pid,ppid,cmd', '--no-headers'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    def get_processes_on_port(self, port):
        """Find all processes using a specific port"""
        try:
            result = subprocess.run(['ss', '-tulpen'], capture_output=True, text=True, timeout=5)
            lines = result.stdout.split('\n')

            pids = []
            for line in lines:
                if f':{port}' in line and 'pid=' in line:
                    import re
                    pid_match = re.search(r'pid=(\d+)', line)
                    if pid_match:
                        pids.append(int(pid_match.group(1)))
            return pids
        except Exception as e:
            print(f"❌ Error checking port {port}: {e}")
            return []

    def stop_process_gracefully(self, pid, process_name):
        """Stop process gracefully with SIGTERM then SIGKILL if needed"""
        try:
            # Check if process exists
            if not self.get_process_info(pid):
                print(f"⚠️ Process {pid} ({process_name}) not found - already stopped")
                return True

            print(f"🛑 Stopping {process_name} (PID {pid}) gracefully...")

            # Send SIGTERM
            os.kill(pid, signal.SIGTERM)

            # Wait up to 10 seconds for graceful shutdown
            for i in range(10):
                time.sleep(1)
                if not self.get_process_info(pid):
                    print(f"✅ {process_name} (PID {pid}) stopped gracefully")
                    return True
                print(f"   ⏳ Waiting for graceful shutdown... ({i+1}/10)")

            # Force kill if still running
            print(f"💀 Force killing {process_name} (PID {pid})...")
            os.kill(pid, signal.SIGKILL)
            time.sleep(2)

            if not self.get_process_info(pid):
                print(f"✅ {process_name} (PID {pid}) force killed")
                return True
            else:
                print(f"❌ Failed to kill {process_name} (PID {pid})")
                return False

        except ProcessLookupError:
            print(f"✅ {process_name} (PID {pid}) already stopped")
            return True
        except PermissionError:
            print(f"❌ Permission denied killing {process_name} (PID {pid})")
            return False
        except Exception as e:
            print(f"❌ Error stopping {process_name} (PID {pid}): {e}")
            return False

    def stop_conflicting_processes(self):
        """Stop all processes that conflict with EA v2.07 ports"""
        print("🚫 Stopping processes that conflict with EA v2.07 ports...")
        print("=" * 60)

        # Map of ports to expected processes
        port_processes = {
            5555: ("command_router", "command_router.py"),
            5556: ("zmq_bridge", "zmq_telemetry_bridge_v207.py"),
            5558: ("confirm_listener", "confirm_listener_v207.py"),
            5560: ("zmq_bridge_pub", "zmq_telemetry_bridge_v207.py")
        }

        stopped_count = 0
        for port, (proc_name, script_name) in port_processes.items():
            print(f"\n📡 Checking port {port} for {proc_name}...")

            pids = self.get_processes_on_port(port)
            if not pids:
                print(f"   ✅ Port {port} is free")
                continue

            for pid in pids:
                proc_info = self.get_process_info(pid)
                if proc_info and script_name in proc_info:
                    print(f"   🎯 Found {script_name} on PID {pid}")

                    # Save process info for restoration
                    self.stopped_processes[str(pid)] = {
                        'name': proc_name,
                        'script': script_name,
                        'port': port,
                        'cmd': proc_info,
                        'stopped_at': time.time()
                    }

                    if self.stop_process_gracefully(pid, proc_name):
                        stopped_count += 1
                    else:
                        # Remove from stopped list if we couldn't stop it
                        del self.stopped_processes[str(pid)]

        self.save_state()
        print(f"\n✅ Stopped {stopped_count} conflicting processes")
        return stopped_count > 0

    def restore_processes(self):
        """Restore previously stopped processes"""
        if not self.stopped_processes:
            print("📝 No stopped processes to restore")
            return

        print("🔄 Restoring previously stopped processes...")
        print("=" * 60)

        restored_count = 0
        failed_count = 0

        for pid_str, proc_info in list(self.stopped_processes.items()):
            script_name = proc_info['script']
            proc_name = proc_info['name']

            print(f"\n🔄 Restoring {proc_name} ({script_name})...")

            try:
                # Find the script file
                script_path = Path(f"/root/HydraX-v2/{script_name}")
                if not script_path.exists():
                    print(f"❌ Script not found: {script_path}")
                    failed_count += 1
                    continue

                # Start the process
                process = subprocess.Popen(
                    ['python3', str(script_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )

                # Give it a moment to start
                time.sleep(2)

                if process.poll() is None:
                    print(f"✅ Restored {proc_name} (new PID {process.pid})")
                    restored_count += 1
                else:
                    stdout, stderr = process.communicate()
                    print(f"❌ Failed to start {proc_name}")
                    if stderr:
                        print(f"   Error: {stderr.decode()[:200]}")
                    failed_count += 1

                # Remove from stopped list
                del self.stopped_processes[pid_str]

            except Exception as e:
                print(f"❌ Error restoring {proc_name}: {e}")
                failed_count += 1

        self.save_state()
        print(f"\n✅ Restored {restored_count} processes, {failed_count} failed")

    def check_ea_v207_readiness(self):
        """Check if EA v2.07 ports are ready"""
        print("🔍 Checking EA v2.07 port readiness...")

        required_ports = [5555, 5556, 5558, 5560]
        free_ports = []
        busy_ports = []

        for port in required_ports:
            pids = self.get_processes_on_port(port)
            if pids:
                busy_ports.append((port, pids))
            else:
                free_ports.append(port)

        print(f"✅ Free ports: {free_ports}")
        if busy_ports:
            print(f"❌ Busy ports: {[(port, pids) for port, pids in busy_ports]}")
            return False
        else:
            print("🎯 All EA v2.07 ports are ready!")
            return True

    def status(self):
        """Show current system status"""
        print("📊 Current System Status")
        print("=" * 60)

        # Check port status
        required_ports = [5555, 5556, 5558, 5560]
        for port in required_ports:
            pids = self.get_processes_on_port(port)
            if pids:
                print(f"Port {port}: ❌ BUSY (PIDs: {pids})")
                for pid in pids:
                    proc_info = self.get_process_info(pid)
                    if proc_info:
                        print(f"   └─ PID {pid}: {proc_info}")
            else:
                print(f"Port {port}: ✅ FREE")

        # Show stopped processes
        if self.stopped_processes:
            print(f"\n📝 Tracked stopped processes: {len(self.stopped_processes)}")
            for pid_str, proc_info in self.stopped_processes.items():
                print(f"   {proc_info['name']} (was PID {pid_str}) - stopped {time.time() - proc_info['stopped_at']:.0f}s ago")

def main():
    if len(sys.argv) < 2:
        print("""
🎛️ EA v2.07 Process Coordinator

Usage:
  python3 coordinate_v207_processes.py <command>

Commands:
  stop     - Stop conflicting processes to free EA v2.07 ports
  restore  - Restore previously stopped processes
  status   - Show current port and process status
  check    - Check if EA v2.07 ports are ready

Examples:
  python3 coordinate_v207_processes.py stop
  python3 coordinate_v207_processes.py restore
  python3 coordinate_v207_processes.py status
""")
        sys.exit(1)

    coordinator = ProcessCoordinator()
    command = sys.argv[1].lower()

    if command == "stop":
        coordinator.stop_conflicting_processes()
        coordinator.check_ea_v207_readiness()

    elif command == "restore":
        coordinator.restore_processes()

    elif command == "status":
        coordinator.status()

    elif command == "check":
        coordinator.check_ea_v207_readiness()

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()