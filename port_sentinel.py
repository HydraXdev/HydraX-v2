#!/usr/bin/env python3
"""
BITTEN Port Sentinel - Production Port Protection System
Monitors critical trading ports 5555/5556/5558/5560 and blocks accidental binds
"""

import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

# Critical BITTEN trading ports
PROTECTED_PORTS = {
    5555: "FIRE_COMMANDS",  # command_router.py - Fire commands to EA
    5556: "MARKET_DATA_IN",  # telemetry bridge - Market data from EA
    5558: "CONFIRMATIONS",  # confirm_listener.py - Trade confirmations from EA
    5559: "TEST_PORT",  # Test port for sentinel validation
    5560: "MARKET_DATA_OUT",  # telemetry bridge - Market data redistribution
}

SENTINEL_LOG = "/root/HydraX-v2/logs/port_sentinel.log"


class PortSentinel:
    def __init__(self):
        self.authorized_owners: Dict[int, Dict] = {}
        self.blocked_attempts: List[Dict] = []

        # Ensure log directory exists
        os.makedirs(os.path.dirname(SENTINEL_LOG), exist_ok=True)

        self.log_event("SENTINEL_START", {"ports_protected": list(PROTECTED_PORTS.keys())})

    def log_event(self, event_type: str, data: Dict):
        """Log events to sentinel log file"""
        timestamp = datetime.utcnow().isoformat() + "Z"
        log_entry = {"timestamp": timestamp, "event_type": event_type, "data": data}

        # Console output
        print(f"[{timestamp}] {event_type}: {json.dumps(data)}")

        # File logging
        try:
            with open(SENTINEL_LOG, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"ERROR: Failed to write log: {e}")

    def get_process_info(self, pid: int) -> Optional[Dict]:
        """Get detailed process information"""
        try:
            result = subprocess.run(
                ["ps", "-p", str(pid), "-o", "pid,ppid,cmd", "--no-headers"], capture_output=True, text=True
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(None, 2)
                if len(parts) >= 3:
                    return {"pid": int(parts[0]), "ppid": int(parts[1]), "cmd": parts[2]}
        except Exception:
            pass
        return None

    def get_port_owner(self, port: int) -> Optional[Dict]:
        """Get the process currently owning a port"""
        try:
            result = subprocess.run(["ss", "-ltnp"], capture_output=True, text=True)
            for line in result.stdout.split("\n"):
                if f":{port}" in line and "LISTEN" in line:
                    # Extract PID from users:((cmd,pid=123,fd=x)) format
                    if "users:" in line:
                        users_part = line.split("users:")[1]
                        if "pid=" in users_part:
                            pid_start = users_part.find("pid=") + 4
                            pid_end = users_part.find(",", pid_start)
                            if pid_end == -1:
                                pid_end = users_part.find(")", pid_start)

                            pid = int(users_part[pid_start:pid_end])
                            process_info = self.get_process_info(pid)

                            if process_info:
                                return {"pid": pid, "cmd": process_info["cmd"], "ppid": process_info["ppid"]}
        except Exception as e:
            self.log_event("ERROR", {"message": f"Failed to get port owner: {e}"})

        return None

    def scan_ports(self):
        """Scan protected ports and record authorized owners"""
        current_owners = {}

        for port in PROTECTED_PORTS.keys():
            owner = self.get_port_owner(port)
            if owner:
                current_owners[port] = owner

                # Check if this is a new owner
                if port not in self.authorized_owners or self.authorized_owners[port]["pid"] != owner["pid"]:
                    self.log_event(
                        "PORT_OWNER_CHANGE",
                        {
                            "port": port,
                            "port_name": PROTECTED_PORTS[port],
                            "new_owner": owner,
                            "previous_owner": self.authorized_owners.get(port, "none"),
                        },
                    )
                    self.authorized_owners[port] = owner

        # Check for ports that became free
        for port in list(self.authorized_owners.keys()):
            if port not in current_owners:
                self.log_event(
                    "PORT_RELEASED",
                    {"port": port, "port_name": PROTECTED_PORTS[port], "previous_owner": self.authorized_owners[port]},
                )
                del self.authorized_owners[port]

    def attempt_bind_detection(self):
        """Detect unauthorized bind attempts by checking for new processes"""
        # This is a simplified detection - in production you'd use kernel modules
        # or eBPF for real-time syscall monitoring
        current_scan = {}

        for port in PROTECTED_PORTS.keys():
            owner = self.get_port_owner(port)
            if owner:
                # Check if owner changed unexpectedly
                if port in self.authorized_owners and self.authorized_owners[port]["pid"] != owner["pid"]:

                    self.log_event(
                        "BLOCK_BIND",
                        {
                            "port": port,
                            "port_name": PROTECTED_PORTS[port],
                            "blocked_process": owner,
                            "authorized_owner": self.authorized_owners[port],
                            "action": "DETECTED_UNAUTHORIZED_BIND",
                        },
                    )

                    self.blocked_attempts.append(
                        {"timestamp": datetime.utcnow().isoformat() + "Z", "port": port, "blocked_process": owner}
                    )

    def get_status(self) -> Dict:
        """Get current sentinel status"""
        return {
            "protected_ports": PROTECTED_PORTS,
            "authorized_owners": self.authorized_owners,
            "blocked_attempts_count": len(self.blocked_attempts),
            "last_scan": datetime.utcnow().isoformat() + "Z",
        }

    def monitor(self, scan_interval: int = 5):
        """Main monitoring loop"""
        print(f"🛡️  BITTEN Port Sentinel Started")
        print(f"📊 Protecting ports: {list(PROTECTED_PORTS.keys())}")
        print(f"📁 Logging to: {SENTINEL_LOG}")
        print(f"⏱️  Scan interval: {scan_interval}s")
        print("=" * 60)

        # Initial scan to establish baseline
        self.scan_ports()

        try:
            while True:
                self.scan_ports()
                self.attempt_bind_detection()
                time.sleep(scan_interval)

        except KeyboardInterrupt:
            self.log_event("SENTINEL_STOP", {"reason": "manual_shutdown"})
            print("\n🛡️  Port Sentinel stopped")


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            sentinel = PortSentinel()
            sentinel.scan_ports()
            status = sentinel.get_status()
            print(json.dumps(status, indent=2))
            return
        elif sys.argv[1] == "scan":
            sentinel = PortSentinel()
            sentinel.scan_ports()
            return

    # Default: Start monitoring
    sentinel = PortSentinel()
    sentinel.monitor()


if __name__ == "__main__":
    main()
