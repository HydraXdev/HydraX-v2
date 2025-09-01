#!/usr/bin/env python3
"""
Production System Monitor - Live Test Conditions
Monitors signals, trades, XP milestones in real-time
"""

import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import requests
import zmq
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger('ProductionMonitor')

class ProductionMonitor:
    def __init__(self):
        # ZMQ setup for monitoring
        self.context = zmq.Context()
        self.telemetry_socket = self.context.socket(zmq.SUB)
        self.telemetry_socket.connect("tcp://localhost:5556")
        self.telemetry_socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self.telemetry_socket.setsockopt(zmq.RCVTIMEO, 100)
        
        # Tracking data
        self.signals_sent = 0
        self.trades_executed = 0
        self.trades_successful = 0
        self.user_xp = defaultdict(int)
        self.user_milestones = defaultdict(list)
        self.start_time = datetime.now()
        
        # Log files
        self.production_log = Path("/root/HydraX-v2/logs/production_test.log")
        self.xp_report = Path("/root/HydraX-v2/logs/xp_milestone_report.json")
        self.production_log.parent.mkdir(exist_ok=True)
        
    def generate_venom_signal(self):
        """Generate and send a VENOM signal via webapp"""
        signal_id = f"VENOM_PROD_{int(time.time() * 1000)}"
        
        # Realistic VENOM signal
        signal = {
            "type": "signal",
            "signal_id": signal_id,
            "symbol": "EURUSD",
            "direction": "BUY" if self.signals_sent % 2 == 0 else "SELL",
            "confidence": 85.0 + (self.signals_sent % 10),
            "tcs_score": 87.0 + (self.signals_sent % 8),
            "entry": 1.0850,
            "sl": 1.0800,
            "tp": 1.0950,
            "risk_reward": 2.0,
            "signal_type": "RAPID_ASSAULT" if self.signals_sent % 3 else "PRECISION_STRIKE",
            "target_pips": 100,
            "stop_pips": 50,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            response = requests.post(
                "http://localhost:8888/api/signals",
                json=signal,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "processed":
                    self.signals_sent += 1
                    self.log_event("SIGNAL_SENT", signal)
                    logger.info(f"📡 Signal sent: {signal_id} - {signal['symbol']} {signal['direction']}")
                    return signal_id
        except Exception as e:
            logger.error(f"Failed to send signal: {e}")
            
        return None
        
    def monitor_telemetry(self):
        """Monitor ZMQ telemetry for trades and XP events"""
        try:
            while True:
                try:
                    message = self.telemetry_socket.recv_string()
                    data = json.loads(message)
                    
                    msg_type = data.get('type', '')
                    
                    if msg_type == 'trade_result':
                        self.process_trade_result(data)
                    elif msg_type in ['telemetry', 'heartbeat']:
                        self.process_telemetry(data)
                        
                except zmq.Again:
                    break
                except Exception as e:
                    logger.error(f"Telemetry error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            
    def process_trade_result(self, result):
        """Process trade execution results"""
        signal_id = result.get('signal_id', '')
        status = result.get('status', '')
        uuid = result.get('uuid', '')
        
        self.trades_executed += 1
        
        if status == 'success':
            self.trades_successful += 1
            ticket = result.get('ticket', 0)
            
            # Award XP for successful trade
            self.user_xp[uuid] += 50  # 50 XP per successful trade
            
            # Check milestones
            total_trades = self.get_user_trades(uuid)
            if total_trades in [1, 10, 50, 100]:
                milestone = f"TRADES_{total_trades}"
                self.user_milestones[uuid].append(milestone)
                self.user_xp[uuid] += total_trades * 10  # Bonus XP
                logger.info(f"🏆 MILESTONE: {uuid} reached {total_trades} trades! +{total_trades * 10} XP")
                
            self.log_event("TRADE_SUCCESS", {
                "signal_id": signal_id,
                "uuid": uuid,
                "ticket": ticket,
                "xp_earned": 50
            })
            
            logger.info(f"✅ Trade executed: {signal_id} - Ticket {ticket} - User {uuid}")
        else:
            self.log_event("TRADE_FAILED", {
                "signal_id": signal_id,
                "uuid": uuid,
                "error": result.get('message', '')
            })
            logger.warning(f"❌ Trade failed: {signal_id} - {result.get('message', '')}")
            
    def process_telemetry(self, data):
        """Process telemetry for XP events"""
        uuid = data.get('uuid', '')
        account = data.get('account', {}) if data.get('type') == 'telemetry' else data
        
        balance = account.get('balance', 0) if isinstance(account, dict) else data.get('balance', 0)
        equity = account.get('equity', 0) if isinstance(account, dict) else data.get('equity', 0)
        
        # Track profit for XP
        if uuid and balance > 0:
            profit = equity - balance
            if profit > 10:  # Significant profit
                xp_from_profit = int(profit * 0.1)
                if xp_from_profit > self.user_xp.get(f"{uuid}_last_profit_xp", 0):
                    bonus_xp = xp_from_profit - self.user_xp.get(f"{uuid}_last_profit_xp", 0)
                    self.user_xp[uuid] += bonus_xp
                    self.user_xp[f"{uuid}_last_profit_xp"] = xp_from_profit
                    logger.info(f"💰 Profit XP: {uuid} earned +{bonus_xp} XP from ${profit:.2f} profit")
                    
    def get_user_trades(self, uuid):
        """Get total trades for a user"""
        # In production, this would query the database
        # For now, estimate based on successful trades
        return sum(1 for _ in range(self.trades_successful) if hash(uuid) % 3 == 0) + 1
        
    def log_event(self, event_type, data):
        """Log production events"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": data
        }
        
        with open(self.production_log, 'a') as f:
            f.write(json.dumps(event) + "\n")
            
    def generate_xp_report(self):
        """Generate XP milestone report"""
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "test_duration": str(datetime.now() - self.start_time),
            "signals_sent": self.signals_sent,
            "trades_executed": self.trades_executed,
            "trades_successful": self.trades_successful,
            "success_rate": (self.trades_successful / self.trades_executed * 100) if self.trades_executed > 0 else 0,
            "users": {}
        }
        
        for uuid, xp in self.user_xp.items():
            if not uuid.endswith("_last_profit_xp"):
                report["users"][uuid] = {
                    "total_xp": xp,
                    "milestones": self.user_milestones.get(uuid, []),
                    "estimated_trades": self.get_user_trades(uuid)
                }
                
        with open(self.xp_report, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report
        
    def display_status(self):
        """Display current system status"""
        runtime = datetime.now() - self.start_time
        success_rate = (self.trades_successful / self.trades_executed * 100) if self.trades_executed > 0 else 0
        
        print("\n" + "="*60)
        print("🚀 PRODUCTION TEST STATUS")
        print("="*60)
        print(f"Runtime: {runtime}")
        print(f"Signals Sent: {self.signals_sent}")
        print(f"Trades Executed: {self.trades_executed}")
        print(f"Successful: {self.trades_successful} ({success_rate:.1f}%)")
        print(f"Active Users: {len([u for u in self.user_xp if not u.endswith('_last_profit_xp')])}")
        print(f"Total XP Awarded: {sum(xp for u, xp in self.user_xp.items() if not u.endswith('_last_profit_xp'))}")
        print("="*60)
        
    def run(self, duration_minutes=60, signal_interval=300):
        """Run production test for specified duration"""
        logger.info("🚀 Starting Production Test")
        logger.info(f"Duration: {duration_minutes} minutes")
        logger.info(f"Signal Interval: {signal_interval} seconds")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        last_signal_time = datetime.now() - timedelta(seconds=signal_interval)
        last_report_time = datetime.now()
        
        while datetime.now() < end_time:
            # Send signals at interval
            if (datetime.now() - last_signal_time).seconds >= signal_interval:
                self.generate_venom_signal()
                last_signal_time = datetime.now()
                
            # Monitor telemetry
            self.monitor_telemetry()
            
            # Generate report every 5 minutes
            if (datetime.now() - last_report_time).seconds >= 300:
                self.display_status()
                self.generate_xp_report()
                last_report_time = datetime.now()
                
            time.sleep(1)
            
        # Final report
        logger.info("🏁 Production Test Complete")
        self.display_status()
        report = self.generate_xp_report()
        
        print(f"\n📊 XP Report saved to: {self.xp_report}")
        print(f"📜 Production log saved to: {self.production_log}")
        
        return report

if __name__ == "__main__":
    monitor = ProductionMonitor()
    
    # Run 30-minute production test with signals every 5 minutes
    monitor.run(duration_minutes=30, signal_interval=300)