#!/usr/bin/env python3
import socket
import subprocess
import time


def check_port(port):
    """Check if a port is bound/listening"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex(("127.0.0.1", port))
        return result == 0
    finally:
        sock.close()


def main():
    print("🚀 MetaSocket Sidecar Launcher")
    print("=" * 50)

    # Start command proxy (port 5561)
    print("Starting command proxy on port 5561...")
    cmd_proc = subprocess.Popen(["python3", "/root/HydraX-v2/sidecars/cmd_proxy_5561.py"])
    time.sleep(1)

    # Start health monitor (port 8890)
    print("Starting health monitor on port 8890...")
    health_proc = subprocess.Popen(["python3", "/root/HydraX-v2/sidecars/healthz_8890.py"])
    time.sleep(2)

    # Check all three expected ports
    print("\nVerifying port bindings:")
    ports = {5561: "Command Proxy (inbound)", 5562: "MetaSocket Publisher (outbound)", 8890: "Health Monitor"}

    all_bound = True
    for port, description in ports.items():
        if check_port(port):
            print(f"✅ :{port} - {description}")
        else:
            print(f"❌ :{port} - {description} (not bound)")
            all_bound = False

    if all_bound:
        print("\n🎯 All ports bound successfully!")
    else:
        print("\n⚠️  Some ports not bound - check processes")

    # Show detailed port binding info
    print("\nDetailed port status:")
    subprocess.run(["ss", "-lntp"], text=True)

    print("\nSidecars launched. Press Ctrl+C to stop both processes.")

    try:
        # Wait for processes
        cmd_proc.wait()
        health_proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping sidecars...")
        cmd_proc.terminate()
        health_proc.terminate()
        print("✅ Sidecars stopped")


if __name__ == "__main__":
    main()
