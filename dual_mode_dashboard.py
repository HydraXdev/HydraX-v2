#!/usr/bin/env python3
"""
Dual Mode Dashboard - Live monitoring of RAPID vs SNIPER signal performance
Real-time statistics dashboard for BITTEN trading system
"""

import json
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import signal as sys_signal

class DualModeDashboard:
    def __init__(self):
        self.truth_file = "/root/HydraX-v2/truth_log.jsonl"
        self.outcome_file = "/root/HydraX-v2/signal_outcomes.jsonl"
        self.dual_mode_stats_file = "/root/HydraX-v2/dual_mode_stats.jsonl"
        self.running = True
        
        # Track dashboard state
        self.last_update = 0
        self.refresh_interval = 5  # seconds
        
        # Signal for graceful shutdown
        sys_signal.signal(sys_signal.SIGINT, self.signal_handler)
        sys_signal.signal(sys_signal.SIGTERM, self.signal_handler)
        
        print("📊 Dual Mode Dashboard initialized")
        print("   Monitoring RAPID vs SNIPER performance")
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print("\n👋 Shutting down dashboard...")
        self.running = False
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def load_recent_signals(self, hours: int = 24) -> List[Dict]:
        """Load recent signals from truth log"""
        recent_signals = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with open(self.truth_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and line != '[]':
                        try:
                            signal = json.loads(line)
                            
                            # Parse generation time
                            gen_time_str = signal.get('generated_at', '')
                            if gen_time_str:
                                try:
                                    gen_time = datetime.fromisoformat(gen_time_str.replace('Z', '+00:00'))
                                    if gen_time >= cutoff_time:
                                        recent_signals.append(signal)
                                except:
                                    continue
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass
            
        return recent_signals
        
    def load_recent_outcomes(self, hours: int = 24) -> List[Dict]:
        """Load recent signal outcomes"""
        recent_outcomes = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with open(self.outcome_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            outcome = json.loads(line)
                            
                            # Parse completion time
                            comp_time_str = outcome.get('completed_at', '')
                            if comp_time_str:
                                try:
                                    comp_time = datetime.fromisoformat(comp_time_str.replace('Z', '+00:00'))
                                    if comp_time >= cutoff_time:
                                        recent_outcomes.append(outcome)
                                except:
                                    continue
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass
            
        return recent_outcomes
        
    def load_latest_stats(self) -> Dict:
        """Load latest dual mode statistics"""
        try:
            with open(self.dual_mode_stats_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if last_line:
                        return json.loads(last_line)
        except FileNotFoundError:
            pass
            
        # Return empty stats if file doesn't exist
        return {
            'rapid_stats': {
                'signals_generated': 0, 'signals_completed': 0, 'wins': 0, 'losses': 0,
                'total_time_to_tp': 0, 'total_rr_achieved': 0.0, 'avg_confidence': 0.0
            },
            'sniper_stats': {
                'signals_generated': 0, 'signals_completed': 0, 'wins': 0, 'losses': 0,
                'total_time_to_tp': 0, 'total_rr_achieved': 0.0, 'avg_confidence': 0.0
            }
        }
        
    def calculate_signal_generation_frequency(self, signals: List[Dict]) -> Dict:
        """Calculate signal generation frequency per hour"""
        if not signals:
            return {'rapid_per_hour': 0.0, 'sniper_per_hour': 0.0}
            
        rapid_count = len([s for s in signals if s.get('signal_type') == 'RAPID_ASSAULT'])
        sniper_count = len([s for s in signals if s.get('signal_type') == 'PRECISION_STRIKE'])
        
        # Calculate per hour rate
        hours = 24  # Looking at 24h window
        return {
            'rapid_per_hour': rapid_count / hours,
            'sniper_per_hour': sniper_count / hours
        }
        
    def format_time_duration(self, seconds: int) -> str:
        """Format time duration in human readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
            
    def get_active_signal_count(self) -> int:
        """Count currently active signals"""
        recent_signals = self.load_recent_signals(hours=2)  # Last 2 hours
        recent_outcomes = self.load_recent_outcomes(hours=2)
        
        # Get signal IDs that have completed
        completed_ids = {outcome['signal_id'] for outcome in recent_outcomes}
        
        # Count signals not yet completed
        active_count = 0
        for signal in recent_signals:
            if signal.get('signal_id', '') not in completed_ids:
                active_count += 1
                
        return active_count
        
    def render_dashboard(self):
        """Render the live dashboard"""
        self.clear_screen()
        
        # Load data
        recent_signals = self.load_recent_signals()
        recent_outcomes = self.load_recent_outcomes()
        latest_stats = self.load_latest_stats()
        frequency_stats = self.calculate_signal_generation_frequency(recent_signals)
        active_signals = self.get_active_signal_count()
        
        # Header
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("=" * 80)
        print("🎯 BITTEN DUAL MODE PERFORMANCE DASHBOARD 🎯")
        print(f"Last Updated: {current_time}")
        print("=" * 80)
        
        # Active signals
        print(f"\n📡 LIVE STATUS:")
        print(f"   Active Signals: {active_signals}")
        print(f"   Signals Generated (24h): {len(recent_signals)}")
        print(f"   Signals Completed (24h): {len(recent_outcomes)}")
        
        # Signal generation frequency
        print(f"\n📊 SIGNAL GENERATION FREQUENCY:")
        print(f"   🏃 RAPID ASSAULT: {frequency_stats['rapid_per_hour']:.1f} signals/hour")
        print(f"   🎯 PRECISION STRIKE: {frequency_stats['sniper_per_hour']:.1f} signals/hour")
        
        # Rapid Assault Performance
        rapid_stats = latest_stats.get('rapid_stats', {})
        rapid_completed = rapid_stats.get('signals_completed', 0)
        rapid_wins = rapid_stats.get('wins', 0)
        rapid_losses = rapid_stats.get('losses', 0)
        rapid_win_rate = (rapid_wins / rapid_completed * 100) if rapid_completed > 0 else 0
        rapid_avg_time = (rapid_stats.get('total_time_to_tp', 0) / rapid_wins) if rapid_wins > 0 else 0
        rapid_avg_rr = (rapid_stats.get('total_rr_achieved', 0) / rapid_completed) if rapid_completed > 0 else 0
        
        print(f"\n🏃 RAPID ASSAULT PERFORMANCE:")
        print(f"   Win Rate: {rapid_win_rate:.1f}% ({rapid_wins}W/{rapid_losses}L)")
        print(f"   Average Time to TP: {self.format_time_duration(int(rapid_avg_time))}")
        print(f"   Average R:R Achieved: {rapid_avg_rr:.2f}")
        print(f"   Average Confidence: {rapid_stats.get('avg_confidence', 0):.1f}%")
        print(f"   Total Signals: {rapid_completed}")
        
        # Sniper Performance  
        sniper_stats = latest_stats.get('sniper_stats', {})
        sniper_completed = sniper_stats.get('signals_completed', 0)
        sniper_wins = sniper_stats.get('wins', 0)
        sniper_losses = sniper_stats.get('losses', 0)
        sniper_win_rate = (sniper_wins / sniper_completed * 100) if sniper_completed > 0 else 0
        sniper_avg_time = (sniper_stats.get('total_time_to_tp', 0) / sniper_wins) if sniper_wins > 0 else 0
        sniper_avg_rr = (sniper_stats.get('total_rr_achieved', 0) / sniper_completed) if sniper_completed > 0 else 0
        
        print(f"\n🎯 PRECISION STRIKE PERFORMANCE:")
        print(f"   Win Rate: {sniper_win_rate:.1f}% ({sniper_wins}W/{sniper_losses}L)")
        print(f"   Average Time to TP: {self.format_time_duration(int(sniper_avg_time))}")
        print(f"   Average R:R Achieved: {sniper_avg_rr:.2f}")
        print(f"   Average Confidence: {sniper_stats.get('avg_confidence', 0):.1f}%")
        print(f"   Total Signals: {sniper_completed}")
        
        # Mode comparison
        print(f"\n⚖️ MODE COMPARISON:")
        if rapid_completed > 0 and sniper_completed > 0:
            print(f"   Win Rate: RAPID {rapid_win_rate:.1f}% vs SNIPER {sniper_win_rate:.1f}%")
            time_comparison = "FASTER" if rapid_avg_time < sniper_avg_time else "SLOWER"
            print(f"   Speed: RAPID is {time_comparison} than SNIPER")
            rr_comparison = "HIGHER" if rapid_avg_rr > sniper_avg_rr else "LOWER" 
            print(f"   R:R Ratio: RAPID is {rr_comparison} than SNIPER")
        else:
            print("   Insufficient data for comparison")
            
        # Recent activity
        if recent_outcomes:
            print(f"\n🕒 RECENT ACTIVITY (Last 5 outcomes):")
            sorted_outcomes = sorted(recent_outcomes, key=lambda x: x.get('completed_at', ''), reverse=True)[:5]
            
            for outcome in sorted_outcomes:
                symbol = outcome.get('symbol', 'UNKNOWN')
                signal_type = outcome.get('signal_mode', 'UNKNOWN')
                result = outcome.get('outcome', 'UNKNOWN')
                pips = outcome.get('pips_result', 0)
                time_to_complete = outcome.get('actual_time_to_tp', 0)
                
                mode_icon = "🏃" if signal_type == 'RAPID_ASSAULT' else "🎯"
                result_icon = "✅" if result == 'WIN' else "❌"
                
                print(f"   {result_icon} {mode_icon} {symbol} {result} {pips:+.1f} pips in {self.format_time_duration(time_to_complete)}")
        
        # Footer
        print(f"\n" + "=" * 80)
        print(f"Press Ctrl+C to exit | Refreshing every {self.refresh_interval} seconds")
        print("=" * 80)
        
    def run(self):
        """Main dashboard loop"""
        print("🚀 Starting Dual Mode Dashboard...")
        
        while self.running:
            try:
                current_time = time.time()
                
                # Render dashboard at refresh interval
                if current_time - self.last_update >= self.refresh_interval:
                    self.render_dashboard()
                    self.last_update = current_time
                    
                # Small sleep to prevent high CPU usage
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"Dashboard error: {e}")
                time.sleep(1)
                
        print("\n👋 Dual Mode Dashboard stopped")

if __name__ == "__main__":
    dashboard = DualModeDashboard()
    dashboard.run()