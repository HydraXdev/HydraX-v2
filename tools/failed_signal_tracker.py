#!/usr/bin/env python3
"""
🚨 FAILED SIGNAL TRACKER
Enhanced tracking system for stalled, failed, and timeout trades
Integrated with Fire Loop Validation System and Enhanced Notifications
"""

import json
import os
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# UUID tracking integration
try:
    from uuid_trade_tracker import UUIDTradeTracker
    UUID_TRACKING_AVAILABLE = True
except ImportError:
    UUID_TRACKING_AVAILABLE = False

# Enhanced notifications integration
try:
    from enhanced_trade_notifications import notification_system
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

# Telegram integration
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

class FailedSignalTracker:
    """Track failed, stalled, and timeout trades with notifications"""
    
    def __init__(self):
        # Directories and files
        self.fired_signals_dir = Path("/root/HydraX-v2/logs/fired_signals")
        self.fired_signals_dir.mkdir(parents=True, exist_ok=True)
        
        self.results_file = Path("/root/HydraX-v2/bitten_results.txt")
        self.missions_dir = Path("/root/HydraX-v2/missions")
        
        # Timeout settings
        self.timeout_seconds = 180  # 3 minutes
        self.warning_seconds = 60   # 1 minute warning
        
        # UUID tracking
        self.uuid_tracker = None
        if UUID_TRACKING_AVAILABLE:
            self.uuid_tracker = UUIDTradeTracker()
        
        # Telegram bot for alerts
        self.bot = None
        if TELEGRAM_AVAILABLE:
            self.bot = Bot(token="8103700393:AAEK3RjTGHHYyy_X1Uc9FUuUoRcLuzYZe4k")
        
        # Admin chat ID for alerts
        self.admin_chat_id = "7176191872"
        
        # Tracking state
        self.tracked_trades = {}
        self.warned_trades = set()
        
        print("🚨 Failed Signal Tracker initialized")
        print(f"⏰ Timeout: {self.timeout_seconds}s")
        print(f"⚠️ Warning: {self.warning_seconds}s")
    
    def save_fired_signal(self, trade_uuid: str, mission_data: Dict, user_id: str):
        """Save fired signal for tracking"""
        try:
            signal = mission_data.get('signal', {})
            enhanced_signal = mission_data.get('enhanced_signal', signal)
            
            fired_signal = {
                "uuid": trade_uuid,
                "symbol": enhanced_signal.get('symbol', 'UNKNOWN'),
                "direction": enhanced_signal.get('direction', 'UNKNOWN'),
                "entry_price": enhanced_signal.get('entry_price', 0),
                "volume": enhanced_signal.get('volume', 0.01),
                "take_profit": enhanced_signal.get('take_profit', 0),
                "stop_loss": enhanced_signal.get('stop_loss', 0),
                "user_id": user_id,
                "fired_at": datetime.utcnow().isoformat(),
                "mission_id": mission_data.get('mission_id', 'UNKNOWN'),
                "tcs_score": enhanced_signal.get('tcs_score', 0)
            }
            
            # Save to file
            signal_file = self.fired_signals_dir / f"{trade_uuid}.json"
            with open(signal_file, 'w') as f:
                json.dump(fired_signal, f, indent=2)
            
            # Add to tracking
            self.tracked_trades[trade_uuid] = {
                "data": fired_signal,
                "fired_at": datetime.utcnow(),
                "status": "fired"
            }
            
            print(f"📁 Fired signal saved: {trade_uuid}")
            
        except Exception as e:
            print(f"❌ Error saving fired signal: {e}")
    
    def load_all_fired_signals(self) -> Dict:
        """Load all fired signals from disk"""
        fired_signals = {}
        
        try:
            for signal_file in self.fired_signals_dir.glob("*.json"):
                try:
                    with open(signal_file, 'r') as f:
                        data = json.load(f)
                    
                    uuid = data.get("uuid")
                    fired_at = data.get("fired_at")
                    
                    if uuid and fired_at:
                        fired_signals[uuid] = {
                            "data": data,
                            "fired_at": datetime.fromisoformat(fired_at),
                            "status": "fired"
                        }
                
                except Exception as e:
                    print(f"❌ Error loading {signal_file}: {e}")
                    continue
        
        except Exception as e:
            print(f"❌ Error loading fired signals: {e}")
        
        return fired_signals
    
    def load_completed_results(self) -> set:
        """Load completed trade UUIDs from results file"""
        completed_uuids = set()
        
        try:
            if self.results_file.exists():
                with open(self.results_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            # Parse result line: uuid,status,ticket,message,price
                            parts = line.split(',')
                            if len(parts) >= 1:
                                uuid = parts[0].strip()
                                if uuid:
                                    completed_uuids.add(uuid)
        
        except Exception as e:
            print(f"❌ Error loading completed results: {e}")
        
        return completed_uuids
    
    def check_uuid_tracking(self) -> Dict:
        """Check UUID tracking system for trade status"""
        if not self.uuid_tracker:
            return {}
        
        try:
            # Get active trades from UUID tracker
            active_trades = self.uuid_tracker.get_active_trades()
            
            uuid_status = {}
            for trade in active_trades:
                uuid_status[trade['trade_uuid']] = {
                    "current_stage": trade['current_stage'],
                    "stages": trade['stages'],
                    "start_time": trade['start_time']
                }
            
            return uuid_status
            
        except Exception as e:
            print(f"❌ Error checking UUID tracking: {e}")
            return {}
    
    async def send_warning_alert(self, trade_uuid: str, trade_data: Dict, age_seconds: int):
        """Send warning alert for delayed trade"""
        try:
            if not self.bot:
                return
            
            data = trade_data["data"]
            
            warning_message = f"""⚠️ **TRADE EXECUTION DELAYED**

🕐 **{int(age_seconds)}s** since fire
Symbol: {data['symbol']} {data['direction']}
Strike: {data['entry_price']}
Volume: {data['volume']} lots
UUID: `{trade_uuid}`

🔍 **MONITORING FOR TIMEOUT...**"""
            
            await self.bot.send_message(
                chat_id=self.admin_chat_id,
                text=warning_message,
                parse_mode='Markdown'
            )
            
            # Also send to user if available
            if NOTIFICATIONS_AVAILABLE:
                await notification_system.send_execution_timeout(
                    data['user_id'], 
                    {"trade_uuid": trade_uuid, "enhanced_signal": data}, 
                    int(age_seconds)
                )
            
            print(f"⚠️ Warning sent for {trade_uuid}")
            
        except Exception as e:
            print(f"❌ Error sending warning: {e}")
    
    async def send_timeout_alert(self, trade_uuid: str, trade_data: Dict, age_seconds: int):
        """Send timeout alert for failed trade"""
        try:
            if not self.bot:
                return
            
            data = trade_data["data"]
            
            # CHARACTER DISPATCHER - Route timeout to DRILL for discipline
            character_response = ""
            character_name = ""
            try:
                from src.bitten_core.voice.character_event_dispatcher import route_trade_event
                signal_data = {
                    'symbol': data.get('symbol', 'UNKNOWN'),
                    'direction': data.get('direction', 'UNKNOWN'),
                    'entry_price': data.get('entry_price', 0),
                    'timeout_seconds': int(age_seconds)
                }
                
                # Route timeout event to DRILL for discipline enforcement
                char_result = route_trade_event(
                    'timeout_warning',
                    signal_data,
                    {'tier': 'ADMIN', 'user_id': 'system'}
                )
                
                character_response = char_result.get('response', '')
                character_name = char_result.get('character', 'DRILL')
                
            except Exception as e:
                print(f"Character timeout warning failed: {e}")
                character_response = "TIMEOUT DETECTED. SYSTEM REQUIRES ATTENTION."
                character_name = "DRILL"
            
            timeout_message = f"""❌ **TRADE EXECUTION TIMEOUT**

🕐 **{int(age_seconds)}s** - TIMEOUT REACHED
Symbol: {data['symbol']} {data['direction']}
Strike: {data['entry_price']}
Volume: {data['volume']} lots
UUID: `{trade_uuid}`

🚨 **MANUAL INVESTIGATION REQUIRED**"""
            
            # Add character response if available
            if character_response:
                character_emoji = {
                    'ATHENA': '🏛️', 'NEXUS': '📣', 'DRILL': '🔧', 
                    'DOC': '🩺', 'BIT': '🐱', 'OVERWATCH': '👁️', 'STEALTH': '🕶️'
                }.get(character_name, '🎯')
                timeout_message += f"\n\n{character_emoji} **{character_name}**: {character_response}"
            
            await self.bot.send_message(
                chat_id=self.admin_chat_id,
                text=timeout_message,
                parse_mode='Markdown'
            )
            
            # Mark as timeout in UUID tracker
            if self.uuid_tracker:
                timeout_result = {
                    "success": False,
                    "message": f"Timeout after {age_seconds}s",
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.uuid_tracker.track_trade_execution(trade_uuid, timeout_result)
            
            print(f"❌ Timeout alert sent for {trade_uuid}")
            
        except Exception as e:
            print(f"❌ Error sending timeout alert: {e}")
    
    async def find_stalled_trades(self):
        """Find and alert on stalled trades"""
        try:
            # Load all fired signals
            fired_signals = self.load_all_fired_signals()
            
            # Load completed results
            completed_uuids = self.load_completed_results()
            
            # Check UUID tracking
            uuid_status = self.check_uuid_tracking()
            
            now = datetime.utcnow()
            
            print(f"\n🚨 [FAILED SIGNAL TRACKER] {now.strftime('%H:%M:%S')} UTC")
            print(f"📊 Fired: {len(fired_signals)} | Completed: {len(completed_uuids)}")
            
            alerts_sent = 0
            
            for trade_uuid, trade_data in fired_signals.items():
                fired_at = trade_data["fired_at"]
                age_seconds = (now - fired_at).total_seconds()
                
                # Skip if already completed
                if trade_uuid in completed_uuids:
                    continue
                
                # Check UUID tracking status
                uuid_info = uuid_status.get(trade_uuid, {})
                current_stage = uuid_info.get('current_stage', 'unknown')
                
                # Warning alert (1 minute)
                if (age_seconds > self.warning_seconds and 
                    trade_uuid not in self.warned_trades and
                    age_seconds < self.timeout_seconds):
                    
                    await self.send_warning_alert(trade_uuid, trade_data, age_seconds)
                    self.warned_trades.add(trade_uuid)
                    alerts_sent += 1
                
                # Timeout alert (3 minutes)
                elif age_seconds > self.timeout_seconds:
                    await self.send_timeout_alert(trade_uuid, trade_data, age_seconds)
                    alerts_sent += 1
                
                # Display status
                if age_seconds > 30:  # Only show trades > 30 seconds
                    status_emoji = "⚠️" if age_seconds > self.warning_seconds else "🕐"
                    print(f"{status_emoji} {trade_uuid[:20]}... → {int(age_seconds)}s | Stage: {current_stage}")
            
            if alerts_sent > 0:
                print(f"📨 Sent {alerts_sent} alerts")
            
            return {
                "fired_count": len(fired_signals),
                "completed_count": len(completed_uuids),
                "stalled_count": len(fired_signals) - len(completed_uuids),
                "alerts_sent": alerts_sent
            }
            
        except Exception as e:
            print(f"❌ Error finding stalled trades: {e}")
            return {}
    
    async def run_monitoring_loop(self):
        """Run continuous monitoring loop"""
        print("🔄 Starting failed signal tracker monitoring...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                await self.find_stalled_trades()
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            print("\n⏹️ Failed signal tracker stopped")
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
    
    async def run_single_check(self):
        """Run single check"""
        result = await self.find_stalled_trades()
        return result

# Global instance
failed_tracker = FailedSignalTracker()

# Helper functions for integration
def save_fired_signal(trade_uuid: str, mission_data: Dict, user_id: str):
    """Helper: Save fired signal for tracking"""
    failed_tracker.save_fired_signal(trade_uuid, mission_data, user_id)

async def check_stalled_trades():
    """Helper: Check for stalled trades"""
    return await failed_tracker.run_single_check()

def main():
    """Main failed signal tracker"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        asyncio.run(failed_tracker.run_single_check())
    else:
        asyncio.run(failed_tracker.run_monitoring_loop())

if __name__ == "__main__":
    main()