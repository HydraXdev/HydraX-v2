#!/usr/bin/env python3
"""
🔍 CLONE LOG WATCHER
AWS MT5 clone log monitoring via bridge agents
"""

import json
import time
from datetime import datetime
from typing import Dict, List

import requests


class CloneLogWatcher:
    """Monitor AWS MT5 clone logs via bridge agents"""

    def __init__(self, user_id: str = "843859"):
        self.user_id = user_id
        self.bridge_server = "localhost"
        self.bridge_port = 5555
        self.clone_path = f"C:\\MT5_Farm\\Users\\user_{user_id}"

        print(f"🔍 CLONE LOG WATCHER INITIALIZED")
        print(f"👤 User: {user_id}")
        print(f"🖥️ Clone: {self.clone_path}")
        print(f"☁️ Bridge: {self.bridge_server}:{self.bridge_port}")
        print("=" * 60)

    def execute_bridge_command(self, command: str) -> Dict:
        """Execute command on AWS bridge"""
        try:
            response = requests.post(
                f"http://{self.bridge_server}:{self.bridge_port}/execute",
                json={"command": command, "type": "powershell"},
                timeout=30,
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_ea_logs(self) -> List[str]:
        """Get EA logs from AWS MT5 clone"""
        command = f"""
# Get EA logs for user {self.user_id}
$logPath = "{self.clone_path}\\MQL5\\Logs"
$bridgePath = "{self.clone_path}\\bridge"

Write-Host "=== EA LOG ANALYSIS ==="

# Find latest EA log file
if (Test-Path $logPath) {{
    $latestLog = Get-ChildItem -Path $logPath -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

    if ($latestLog) {{
        Write-Host "📁 Latest EA Log: $($latestLog.Name)"
        Write-Host "⏰ Last Modified: $($latestLog.LastWriteTime)"

        # Get last 20 lines and filter for trade-related content
        $content = Get-Content $latestLog.FullName -Tail 20

        Write-Host "\\n📊 TRADE-RELATED ENTRIES:"
        foreach ($line in $content) {{
            if ($line -match "Trade|OrderSend|BITTEN|Bridge|Signal|Execution") {{
                Write-Host "  $line"
            }}
        }}
    }} else {{
        Write-Host "❌ No EA log files found"
    }}
}} else {{
    Write-Host "❌ EA log directory not found: $logPath"
}}

# Check bridge files
Write-Host "\\n=== BRIDGE FILES ==="
if (Test-Path $bridgePath) {{
    $bridgeFiles = Get-ChildItem -Path $bridgePath -Filter "*.json"
    foreach ($file in $bridgeFiles) {{
        Write-Host "📄 $($file.Name): $($file.LastWriteTime)"
        if ($file.Name -match "status|result|heartbeat") {{
            $content = Get-Content $file.FullName -Raw
            if ($content) {{
                Write-Host "  Preview: $($content.Substring(0, [Math]::Min(100, $content.Length)))"
            }}
        }}
    }}
}} else {{
    Write-Host "❌ Bridge directory not found: $bridgePath"
}}
"""

        result = self.execute_bridge_command(command)

        if result.get("returncode") == 0:
            return result.get("stdout", "").split("\\n")
        else:
            return [f"Error getting EA logs: {result.get('stderr', 'Unknown error')}"]

    def get_mt5_journal(self) -> List[str]:
        """Get MT5 terminal journal logs"""
        command = f"""
# Get MT5 journal logs for user {self.user_id}
$journalPath = "{self.clone_path}\\Logs"

Write-Host "=== MT5 JOURNAL ANALYSIS ==="

if (Test-Path $journalPath) {{
    $latestJournal = Get-ChildItem -Path $journalPath -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

    if ($latestJournal) {{
        Write-Host "📁 Latest Journal: $($latestJournal.Name)"
        Write-Host "⏰ Last Modified: $($latestJournal.LastWriteTime)"

        # Get last 15 lines and filter for trade execution
        $content = Get-Content $latestJournal.FullName -Tail 15

        Write-Host "\\n📊 TRADE EXECUTION ENTRIES:"
        foreach ($line in $content) {{
            if ($line -match "Trade|Order|Deal|Position|Buy|Sell|executed") {{
                Write-Host "  $line"
            }}
        }}
    }} else {{
        Write-Host "❌ No journal files found"
    }}
}} else {{
    Write-Host "❌ Journal directory not found: $journalPath"
}}

# Check MT5 process status
Write-Host "\\n=== MT5 PROCESS STATUS ==="
$mt5Process = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue | Where-Object {{$_.Path -like "*user_{self.user_id}*"}}
if ($mt5Process) {{
    Write-Host "✅ MT5 Process Running: PID $($mt5Process.Id)"
    Write-Host "💾 Memory Usage: $([math]::Round($mt5Process.WorkingSet64/1MB, 1)) MB"
}} else {{
    Write-Host "❌ MT5 Process Not Found"
}}
"""

        result = self.execute_bridge_command(command)

        if result.get("returncode") == 0:
            return result.get("stdout", "").split("\\n")
        else:
            return [f"Error getting MT5 journal: {result.get('stderr', 'Unknown error')}"]

    def get_signal_activity(self) -> List[str]:
        """Get signal file activity"""
        command = f"""
# Check signal activity for user {self.user_id}
$signalDir = "C:\\Users\\Administrator\\AppData\\Roaming\\MetaQuotes\\Terminal\\173477FF1060D99CE79296FC73108719\\MQL5\\Files\\BITTEN"

Write-Host "=== SIGNAL ACTIVITY ==="

if (Test-Path $signalDir) {{
    $signalFiles = Get-ChildItem -Path $signalDir -Filter "*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 5

    if ($signalFiles) {{
        Write-Host "📊 Recent Signal Files:"
        foreach ($file in $signalFiles) {{
            Write-Host "  📄 $($file.Name) - $($file.LastWriteTime)"

            # Preview signal content
            try {{
                $content = Get-Content $file.FullName -Raw | ConvertFrom-Json
                Write-Host "    Symbol: $($content.symbol) | Direction: $($content.direction) | TCS: $($content.tcs)"
            }} catch {{
                Write-Host "    (Unable to parse signal content)"
            }}
        }}
    }} else {{
        Write-Host "❌ No signal files found"
    }}
}} else {{
    Write-Host "❌ Signal directory not found: $signalDir"
}}
"""

        result = self.execute_bridge_command(command)

        if result.get("returncode") == 0:
            return result.get("stdout", "").split("\\n")
        else:
            return [f"Error getting signal activity: {result.get('stderr', 'Unknown error')}"]

    def display_comprehensive_status(self):
        """Display comprehensive clone status"""
        print(f"\\n🔍 [CLONE LOG TRACE] {datetime.utcnow().strftime('%H:%M:%S')} UTC")
        print("=" * 60)

        # Get EA logs
        print("🤖 EA LOG ANALYSIS:")
        ea_logs = self.get_ea_logs()
        for line in ea_logs:
            if line.strip():
                print(f"  {line}")

        # Get MT5 journal
        print("\\n📊 MT5 JOURNAL ANALYSIS:")
        journal_logs = self.get_mt5_journal()
        for line in journal_logs:
            if line.strip():
                print(f"  {line}")

        # Get signal activity
        print("\\n📡 SIGNAL ACTIVITY:")
        signal_activity = self.get_signal_activity()
        for line in signal_activity:
            if line.strip():
                print(f"  {line}")

        print("-" * 60)

    def run_continuous_monitoring(self):
        """Run continuous clone log monitoring"""
        print("🔄 Starting continuous clone log monitoring...")
        print("Press Ctrl+C to stop")

        try:
            while True:
                self.display_comprehensive_status()
                time.sleep(15)  # Check every 15 seconds
        except KeyboardInterrupt:
            print("\\n⏹️ Clone log monitoring stopped")

    def run_single_check(self):
        """Run single clone log check"""
        self.display_comprehensive_status()


def main():
    """Main clone log watcher"""
    import sys

    user_id = "843859"
    if len(sys.argv) > 1 and sys.argv[1] != "--continuous":
        user_id = sys.argv[1]

    watcher = CloneLogWatcher(user_id)

    if len(sys.argv) > 1 and sys.argv[-1] == "--continuous":
        watcher.run_continuous_monitoring()
    else:
        watcher.run_single_check()


if __name__ == "__main__":
    main()
