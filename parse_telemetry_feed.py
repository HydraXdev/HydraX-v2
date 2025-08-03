#!/usr/bin/env python3
"""
Parse ZMQ Telemetry Feed - Extract XP/Risk Data
"""

import zmq
import json
import time
from datetime import datetime
from collections import defaultdict

class TelemetryParser:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect("tcp://localhost:5556")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self.socket.setsockopt(zmq.RCVTIMEO, 1000)
        
        # Track user data
        self.users = {}
        self.trade_results = []
        
    def parse_for_xp(self, telemetry):
        """Extract XP-relevant data from telemetry"""
        uuid = telemetry.get('uuid', 'unknown')
        account = telemetry.get('account', {})
        
        # Extract key metrics for XP calculation
        xp_data = {
            'uuid': uuid,
            'balance': account.get('balance', 0),
            'equity': account.get('equity', 0),
            'profit': account.get('profit', 0),
            'positions': account.get('positions', 0),
            'margin_level': account.get('margin_level', 0),
            'free_margin': account.get('free_margin', 0)
        }
        
        # Calculate XP events
        if uuid not in self.users:
            self.users[uuid] = {'last_balance': xp_data['balance']}
            print(f"🆕 New user detected: {uuid}")
            print(f"   Initial balance: ${xp_data['balance']:,.2f}")
            return
            
        last_balance = self.users[uuid].get('last_balance', 0)
        balance_change = xp_data['balance'] - last_balance
        
        # XP triggers
        if balance_change > 0:
            xp_earned = int(balance_change * 0.1)  # 10% of profit as XP
            print(f"💰 {uuid} profit: +${balance_change:.2f} → +{xp_earned} XP")
        elif xp_data['positions'] > 0:
            print(f"⚡ {uuid} has {xp_data['positions']} active positions")
            
        # Update tracking
        self.users[uuid]['last_balance'] = xp_data['balance']
        self.users[uuid]['last_equity'] = xp_data['equity']
        self.users[uuid]['last_update'] = datetime.now()
        
    def parse_for_risk(self, telemetry):
        """Extract risk management data from telemetry"""
        uuid = telemetry.get('uuid', 'unknown')
        account = telemetry.get('account', {})
        
        # Risk metrics
        balance = account.get('balance', 0)
        equity = account.get('equity', 0)
        margin = account.get('margin', 0)
        free_margin = account.get('free_margin', 0)
        
        if balance > 0:
            # Calculate risk ratios
            equity_ratio = (equity / balance) * 100
            margin_usage = (margin / balance) * 100 if balance > 0 else 0
            
            # Risk warnings
            if equity_ratio < 90:
                print(f"⚠️  {uuid} RISK: Equity down to {equity_ratio:.1f}% of balance")
            if margin_usage > 50:
                print(f"🚨 {uuid} HIGH MARGIN: Using {margin_usage:.1f}% of balance")
            if free_margin < balance * 0.2:
                print(f"❌ {uuid} LOW MARGIN: Only ${free_margin:.2f} free")
                
    def parse_trade_result(self, result):
        """Parse trade execution results"""
        signal_id = result.get('signal_id', 'unknown')
        status = result.get('status', 'unknown')
        ticket = result.get('ticket', 0)
        price = result.get('price', 0)
        message = result.get('message', '')
        uuid = result.get('uuid', 'unknown')
        
        self.trade_results.append(result)
        
        if status == 'success':
            print(f"✅ TRADE EXECUTED: {signal_id}")
            print(f"   User: {uuid}")
            print(f"   Ticket: {ticket}")
            print(f"   Price: {price}")
            
            # Track for XP
            if uuid in self.users:
                self.users[uuid]['trades_executed'] = self.users[uuid].get('trades_executed', 0) + 1
                trades = self.users[uuid]['trades_executed']
                if trades in [1, 10, 50, 100]:
                    print(f"🏆 {uuid} MILESTONE: {trades} trades executed! +{trades*10} XP")
        else:
            print(f"❌ TRADE FAILED: {signal_id} - {message}")
            
    def monitor(self, duration=60):
        """Monitor telemetry for specified duration"""
        print(f"📡 Monitoring ZMQ telemetry on port 5556 for {duration} seconds...")
        print("=" * 60)
        
        start_time = time.time()
        msg_count = 0
        
        while time.time() - start_time < duration:
            try:
                message = self.socket.recv_string()
                data = json.loads(message)
                msg_count += 1
                
                msg_type = data.get('type', 'unknown')
                
                if msg_type == 'telemetry' or msg_type == 'heartbeat':
                    self.parse_for_xp(data)
                    self.parse_for_risk(data)
                elif msg_type == 'trade_result':
                    self.parse_trade_result(data)
                else:
                    print(f"📥 Unknown message type: {msg_type}")
                    
            except zmq.Again:
                # No message, continue
                pass
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON decode error: {e}")
            except Exception as e:
                print(f"❌ Error: {e}")
                
        print("=" * 60)
        print(f"📊 Summary: {msg_count} messages received")
        print(f"👥 Active users: {len(self.users)}")
        print(f"📈 Trade results: {len(self.trade_results)}")
        
        # Show user summary
        for uuid, data in self.users.items():
            print(f"\n👤 {uuid}:")
            print(f"   Balance: ${data.get('last_balance', 0):,.2f}")
            print(f"   Equity: ${data.get('last_equity', 0):,.2f}")
            print(f"   Trades: {data.get('trades_executed', 0)}")
            
    def close(self):
        """Clean up resources"""
        self.socket.close()
        self.context.term()

if __name__ == "__main__":
    parser = TelemetryParser()
    try:
        parser.monitor(duration=30)  # Monitor for 30 seconds
    finally:
        parser.close()