#!/usr/bin/env python3
"""
Data Flow Alert System - Sends alerts when critical data flows break
Integrates with Telegram for immediate notifications
"""

import json
import time
import sqlite3
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class DataFlowAlerts:
    """Alert system for critical data flow failures"""
    
    def __init__(self):
        self.health_file = "/root/HydraX-v2/data_flow_health.json"
        self.db_path = "/root/HydraX-v2/bitten.db"
        self.alert_history = {}  # Track when alerts were last sent
        self.alert_cooldown = 3600  # Don't repeat same alert for 1 hour
        
        # Alert thresholds
        self.thresholds = {
            "no_signals": 3600,      # Alert if no signals for 1 hour
            "ea_stale": 300,         # Alert if EA heartbeat > 5 minutes
            "no_trades": 7200,       # Alert if no trades for 2 hours
            "process_down": 60,      # Alert after 1 minute of process being down
            "port_unbound": 60,      # Alert after 1 minute of port being unbound
            "tracking_stale": 7200,  # Alert if tracking files > 2 hours old
        }
        
        # Critical processes that must always be running
        self.critical_processes = [
            "elite_guard",
            "command_router", 
            "webapp",
            "telemetry_bridge"
        ]
        
        # Critical ports that must always be bound
        self.critical_ports = [5555, 5556, 5557, 5558, 5560]
        
        # Alert levels
        self.alert_levels = {
            "CRITICAL": "🚨",  # System broken, immediate action needed
            "WARNING": "⚠️",   # Degraded performance
            "INFO": "ℹ️"       # Informational
        }
        
    def should_send_alert(self, alert_key: str) -> bool:
        """Check if we should send this alert based on cooldown"""
        now = time.time()
        last_sent = self.alert_history.get(alert_key, 0)
        
        if now - last_sent > self.alert_cooldown:
            self.alert_history[alert_key] = now
            return True
        return False
        
    def send_telegram_alert(self, level: str, title: str, message: str):
        """Send alert to Telegram monitoring channel"""
        try:
            # Check if we should send this alert
            alert_key = f"{level}:{title}"
            if not self.should_send_alert(alert_key):
                return
                
            # Format alert message
            icon = self.alert_levels.get(level, "📢")
            alert_text = f"{icon} *{level}: {title}*\n\n{message}\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            
            # Log to console
            print(f"\n{icon} {level}: {title}")
            print(f"  {message}")
            
            # Would send to Telegram here if bot token configured
            # For now just log to alert file
            with open("/root/HydraX-v2/data_flow_alerts.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} | {level} | {title} | {message}\n")
                
        except Exception as e:
            print(f"Error sending alert: {e}")
            
    def check_health_status(self) -> Dict:
        """Load current health status"""
        try:
            if os.path.exists(self.health_file):
                with open(self.health_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading health file: {e}")
        return {}
        
    def check_process_alerts(self, health_data: Dict):
        """Check for process-related alerts"""
        process_health = health_data.get("health_status", {}).get("process_health", {})
        
        down_processes = []
        for proc in self.critical_processes:
            if not process_health.get(proc, False):
                down_processes.append(proc)
                
        if down_processes:
            self.send_telegram_alert(
                "CRITICAL",
                "Critical Processes Down",
                f"The following critical processes are DOWN:\n" + 
                "\n".join([f"• {p}" for p in down_processes]) +
                "\n\nSystem may not be generating or executing trades!"
            )
            
    def check_port_alerts(self, health_data: Dict):
        """Check for port binding alerts"""
        port_health = health_data.get("health_status", {}).get("port_health", {})
        
        unbound_ports = []
        for port in self.critical_ports:
            if not port_health.get(port, False):
                port_name = {
                    5555: "Command Router",
                    5556: "Market Data Input",
                    5557: "Elite Guard Signals",
                    5558: "Trade Confirmations",
                    5560: "Market Data Relay"
                }.get(port, str(port))
                unbound_ports.append(f"{port} ({port_name})")
                
        if unbound_ports:
            self.send_telegram_alert(
                "CRITICAL",
                "ZMQ Ports Unbound",
                f"The following critical ports are UNBOUND:\n" +
                "\n".join([f"• Port {p}" for p in unbound_ports]) +
                "\n\nData flow is broken!"
            )
            
    def check_signal_alerts(self, health_data: Dict):
        """Check for signal generation alerts"""
        flow_health = health_data.get("health_status", {}).get("data_flow_health", {})
        signal_flow = flow_health.get("signal_generation", {})
        
        if signal_flow:
            age = signal_flow.get("age_seconds")
            if age and age > self.thresholds["no_signals"]:
                hours = age / 3600
                self.send_telegram_alert(
                    "WARNING",
                    "No Signals Generated",
                    f"No signals have been generated for {hours:.1f} hours.\n" +
                    "Possible causes:\n" +
                    "• Market closed (weekend/holiday)\n" +
                    "• Elite Guard not receiving market data\n" +
                    "• Pattern detection too restrictive"
                )
                
    def check_ea_alerts(self, health_data: Dict):
        """Check for EA connection alerts"""
        ea_freshness = health_data.get("health_status", {}).get("ea_freshness")
        
        if ea_freshness and ea_freshness > self.thresholds["ea_stale"]:
            minutes = ea_freshness / 60
            self.send_telegram_alert(
                "CRITICAL",
                "EA Connection Lost",
                f"EA has not sent heartbeat for {minutes:.1f} minutes.\n" +
                "Trading is HALTED!\n" +
                "Check:\n" +
                "• MT5 terminal is running\n" +
                "• EA is attached to chart\n" +
                "• Network connection to server"
            )
            
    def check_trade_alerts(self, health_data: Dict):
        """Check for trade execution alerts"""
        fires_24h = health_data.get("health_status", {}).get("fires_24h", 0)
        
        # Check database for last trade time
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT MAX(created_at) as last_trade
                FROM fires
                WHERE status = 'FILLED'
            """)
            result = cursor.fetchone()
            
            if result and result[0]:
                last_trade_age = int(time.time()) - result[0]
                
                if last_trade_age > self.thresholds["no_trades"] and fires_24h == 0:
                    hours = last_trade_age / 3600
                    self.send_telegram_alert(
                        "INFO",
                        "No Recent Trades",
                        f"No trades executed in the last {hours:.1f} hours.\n" +
                        "This may be normal if:\n" +
                        "• No high-confidence signals generated\n" +
                        "• Market conditions unfavorable\n" +
                        "• Trading hours restrictions"
                    )
                    
            conn.close()
        except Exception as e:
            print(f"Error checking trade alerts: {e}")
            
    def check_tracking_alerts(self, health_data: Dict):
        """Check for tracking file staleness"""
        flow_health = health_data.get("health_status", {}).get("data_flow_health", {})
        
        stale_files = []
        for file_name in ["comprehensive_tracking.jsonl", "dynamic_tracking.jsonl", "ml_training_data.jsonl"]:
            file_data = flow_health.get(file_name, {})
            age = file_data.get("age_seconds")
            
            if age and age > self.thresholds["tracking_stale"]:
                hours = age / 3600
                stale_files.append(f"{file_name} ({hours:.1f}h old)")
                
        if stale_files:
            self.send_telegram_alert(
                "WARNING",
                "Tracking Files Stale",
                f"The following tracking files are not being updated:\n" +
                "\n".join([f"• {f}" for f in stale_files]) +
                "\n\nML training and performance tracking may be affected."
            )
            
    def generate_summary_alert(self, health_data: Dict):
        """Generate daily summary alert"""
        # Only send at specific times (e.g., 00:00, 12:00 UTC)
        current_hour = datetime.now().hour
        if current_hour not in [0, 12]:
            return
            
        # Check if we already sent summary today
        alert_key = f"SUMMARY:{datetime.now().date()}-{current_hour}"
        if not self.should_send_alert(alert_key):
            return
            
        stats = health_data.get("health_status", {})
        
        summary = []
        summary.append(f"📊 24-Hour Statistics:")
        summary.append(f"• Signals: {stats.get('signals_24h', 0)}")
        summary.append(f"• Trades: {stats.get('fires_24h', 0)}")
        
        # Check overall health
        all_healthy = health_data.get("all_healthy", False)
        if all_healthy:
            summary.append(f"• System Status: ✅ All systems operational")
        else:
            summary.append(f"• System Status: ⚠️ Some issues detected")
            
        self.send_telegram_alert(
            "INFO",
            "Daily System Summary",
            "\n".join(summary)
        )
        
    def monitor_loop(self):
        """Main monitoring loop"""
        print("📢 Data Flow Alert System starting...")
        print("Monitoring for critical failures and sending alerts")
        print("")
        
        while True:
            try:
                # Load health data
                health_data = self.check_health_status()
                
                if health_data:
                    # Check various alert conditions
                    self.check_process_alerts(health_data)
                    self.check_port_alerts(health_data)
                    self.check_signal_alerts(health_data)
                    self.check_ea_alerts(health_data)
                    self.check_trade_alerts(health_data)
                    self.check_tracking_alerts(health_data)
                    self.generate_summary_alert(health_data)
                    
                # Sleep before next check
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                print("\n✅ Alert system stopped")
                break
            except Exception as e:
                print(f"Alert loop error: {e}")
                time.sleep(60)
                
if __name__ == "__main__":
    alert_system = DataFlowAlerts()
    alert_system.monitor_loop()