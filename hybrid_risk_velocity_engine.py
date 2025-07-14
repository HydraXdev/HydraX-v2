#!/usr/bin/env python3
"""
HYBRID RISK-VELOCITY SIGNAL ENGINE - OPTION B IMPLEMENTATION
Mathematical classification: ARCADE vs SNIPER based on risk-efficiency
"""

import sqlite3
import time
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sys
import uuid
import os

# Add performance tracking
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
try:
    from bitten_core.live_performance_tracker import live_tracker, LiveSignal, SignalStatus
    from bitten_core.enhanced_ghost_tracker import enhanced_ghost_tracker, apply_ghost_mode_to_signal
    PERFORMANCE_TRACKING = True
    print("✅ Live performance tracking enabled")
except ImportError as e:
    print(f"⚠️ Performance tracking not available: {e}")
    PERFORMANCE_TRACKING = False

class HybridRiskVelocityEngine:
    def __init__(self):
        self.db_path = "/root/HydraX-v2/data/live_market.db"
        
        # Telegram config
        self.bot_token = "os.getenv("BOT_TOKEN", "DISABLED_FOR_SECURITY")"
        self.chat_id = "int(os.getenv("CHAT_ID", "-1002581996861"))"
        
        # Track sent signals
        self.sent_signals = set()
        
        # CALIBRATED MATHEMATICAL THRESHOLDS (based on backtesting results)
        self.arcade_risk_efficiency_min = 4.0  # >4 profit-pips per risk-pip per hour
        self.arcade_max_duration_minutes = 45  # Hard limit for ARCADE
        self.arcade_min_tcs = 87  # CALIBRATED from 82% to 87% - improved quality
        self.arcade_velocity_min = 15  # >15 pips/hour price movement
        
        self.sniper_min_profit_pips = 40  # Minimum absolute profit
        self.sniper_min_tcs = 90  # CALIBRATED from 85% to 90% - higher precision
        self.sniper_min_risk_reward = 3.0  # 1:3+ R:R minimum
        self.sniper_max_duration_hours = 4  # Premium patience
        
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/HydraX-v2/logs/hybrid_engine.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def calculate_market_velocity(self, symbol: str, timeframe_minutes: int = 60) -> float:
        """Calculate price velocity (pips/hour) for market movement assessment"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get price movement over timeframe
            cursor.execute('''
            SELECT entry_price FROM live_signals 
            WHERE symbol = ? AND source = 'production'
            AND timestamp > datetime('now', '-{} minutes')
            ORDER BY timestamp DESC
            LIMIT 10
            '''.format(timeframe_minutes), (symbol,))
            
            prices = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if len(prices) < 2:
                return 0.0
            
            # Calculate average pip movement per hour
            price_range = max(prices) - min(prices)
            
            # Convert to pips (assuming 4-decimal pairs like EURUSD)
            if symbol in ['USDJPY']:
                pips = price_range * 100  # 2-decimal pair
            else:
                pips = price_range * 10000  # 4-decimal pair
                
            # Velocity = pips per hour
            velocity = pips * (60 / timeframe_minutes)
            return velocity
            
        except Exception as e:
            self.logger.error(f"Velocity calculation error: {e}")
            return 0.0
    
    def calculate_risk_efficiency(self, signal: Dict) -> float:
        """Calculate risk efficiency: (TP_Pips / SL_Pips) / Expected_Duration_Hours"""
        try:
            entry = signal['entry_price']
            tp = signal['take_profit']
            sl = signal['stop_loss']
            
            # Calculate pips
            if signal['symbol'] in ['USDJPY']:
                tp_pips = abs(tp - entry) * 100
                sl_pips = abs(entry - sl) * 100
            else:
                tp_pips = abs(tp - entry) * 10000
                sl_pips = abs(entry - sl) * 10000
            
            if sl_pips == 0:
                return 0.0
                
            # Risk/Reward ratio
            risk_reward = tp_pips / sl_pips
            
            # Estimate duration based on TCS and market conditions
            tcs = signal['tcs_score']
            market_velocity = self.calculate_market_velocity(signal['symbol'])
            
            # Duration estimation formula
            if market_velocity > 20:  # Fast market
                estimated_hours = 0.5 + (100 - tcs) * 0.02  # 0.5-2 hours
            elif market_velocity > 10:  # Medium market
                estimated_hours = 1.0 + (100 - tcs) * 0.03  # 1-2.5 hours
            else:  # Slow market
                estimated_hours = 1.5 + (100 - tcs) * 0.04  # 1.5-3 hours
            
            # Risk efficiency = RR per hour
            risk_efficiency = risk_reward / estimated_hours
            
            return risk_efficiency
            
        except Exception as e:
            self.logger.error(f"Risk efficiency calculation error: {e}")
            return 0.0
    
    def classify_signal_type(self, signal: Dict) -> Optional[str]:
        """Classify signal as ARCADE or SNIPER based on Option B criteria"""
        
        tcs = signal['tcs_score']
        risk_efficiency = self.calculate_risk_efficiency(signal)
        market_velocity = self.calculate_market_velocity(signal['symbol'])
        
        # Calculate absolute profit in pips
        entry = signal['entry_price']
        tp = signal['take_profit']
        
        if signal['symbol'] in ['USDJPY']:
            profit_pips = abs(tp - entry) * 100
        else:
            profit_pips = abs(tp - entry) * 10000
        
        # Calculate actual risk/reward ratio
        sl = signal['stop_loss']
        if signal['symbol'] in ['USDJPY']:
            sl_pips = abs(entry - sl) * 100
        else:
            sl_pips = abs(entry - sl) * 10000
            
        actual_rr = profit_pips / sl_pips if sl_pips > 0 else 0
        
        # ARCADE CLASSIFICATION CRITERIA
        arcade_criteria = [
            risk_efficiency > self.arcade_risk_efficiency_min,  # >4.0 efficiency
            market_velocity > self.arcade_velocity_min,  # >15 pips/hour movement
            tcs >= self.arcade_min_tcs,  # >=70% TCS
            actual_rr >= 1.0 and actual_rr <= 2.0  # 1:1 to 1:2 R:R
        ]
        
        # SNIPER CLASSIFICATION CRITERIA
        sniper_criteria = [
            profit_pips >= self.sniper_min_profit_pips,  # >=40 pips absolute
            tcs >= self.sniper_min_tcs,  # >=90% TCS (calibrated)
            actual_rr >= self.sniper_min_risk_reward,  # >=1:3 R:R
            risk_efficiency >= 1.5 and risk_efficiency <= 4.0  # Strategic efficiency
        ]
        
        # Classification logic
        arcade_score = sum(arcade_criteria)
        sniper_score = sum(sniper_criteria)
        
        self.logger.debug(f"Signal {signal['id']}: ARCADE={arcade_score}/4, SNIPER={sniper_score}/4, RE={risk_efficiency:.1f}, MV={market_velocity:.1f}")
        
        if arcade_score >= 3:  # Need 3/4 criteria for ARCADE
            return "ARCADE"
        elif sniper_score >= 3:  # Need 3/4 criteria for SNIPER
            return "SNIPER"
        else:
            return None  # Doesn't meet either criteria
    
    def create_arcade_alert(self, tcs_score, signal_id, symbol):
        """ARCADE format for fast-action signals"""
        text = f"🔫 RAPID ASSAULT [{tcs_score}%]\n🔥 {symbol} STRIKE 💥"
        
        keyboard = {
            "inline_keyboard": [[{
                "text": "MISSION BRIEF",
                "url": f"https://joinbitten.com/hud?signal={signal_id}"
            }]]
        }
        
        return {"text": text, "keyboard": keyboard}

    def create_sniper_alert(self, tcs_score, signal_id, symbol):
        """SNIPER format for precision signals"""
        text = f"⚡ SNIPER OPS ⚡ [{tcs_score}%]\n🎖️ {symbol} ELITE ACCESS"
        
        keyboard = {
            "inline_keyboard": [[{
                "text": "VIEW INTEL", 
                "url": f"https://joinbitten.com/hud?signal={signal_id}"
            }]]
        }
        
        return {"text": text, "keyboard": keyboard}
    
    def send_telegram_message(self, text: str, keyboard=None) -> bool:
        """Send message to Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            
            if keyboard:
                data['reply_markup'] = json.dumps(keyboard)
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                self.logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Telegram send error: {e}")
            return False
    
    def get_candidate_signals(self) -> List[Dict]:
        """Get all recent signals for classification"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get signals from last 10 minutes
            cursor.execute('''
            SELECT id, symbol, timestamp, direction, tcs_score, entry_price,
                   stop_loss, take_profit, risk_reward, expires_at, status
            FROM live_signals 
            WHERE source = 'production' 
            AND status = 'active'
            AND timestamp > datetime('now', '-10 minutes')
            ORDER BY timestamp DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            signals = []
            
            for row in results:
                signal_id = row[0]
                
                # Skip if already sent
                if signal_id in self.sent_signals:
                    continue
                    
                signal = {
                    'id': signal_id,
                    'symbol': row[1],
                    'timestamp': row[2],
                    'direction': row[3],
                    'tcs_score': row[4],
                    'entry_price': row[5],
                    'stop_loss': row[6],
                    'take_profit': row[7],
                    'risk_reward': row[8],
                    'expires_at': row[9],
                    'status': row[10]
                }
                
                signals.append(signal)
                
            return signals
            
        except Exception as e:
            self.logger.error(f"Database error: {e}")
            return []
    
    def run_hybrid_engine(self):
        """Run the hybrid risk-velocity classification engine"""
        self.logger.info("🚀 HYBRID RISK-VELOCITY ENGINE STARTED")
        self.logger.info(f"🔫 ARCADE: RE>{self.arcade_risk_efficiency_min}, MV>{self.arcade_velocity_min} pips/h, TCS>={self.arcade_min_tcs}%")
        self.logger.info(f"⚡ SNIPER: >{self.sniper_min_profit_pips} pips, TCS>{self.sniper_min_tcs}%, RR>{self.sniper_min_risk_reward}")
        
        arcade_count = 0
        sniper_count = 0
        
        while True:
            try:
                # Get candidate signals
                candidates = self.get_candidate_signals()
                
                if candidates:
                    self.logger.info(f"🔍 Analyzing {len(candidates)} candidate signals")
                    
                    for signal in candidates:
                        # Classify signal type
                        signal_type = self.classify_signal_type(signal)
                        
                        if signal_type:
                            # LIVE PERFORMANCE TRACKING: Track signal generation
                            if PERFORMANCE_TRACKING:
                                try:
                                    live_signal = LiveSignal(
                                        signal_id=signal['id'],
                                        symbol=signal['symbol'],
                                        direction=signal['direction'],
                                        tcs_score=signal['tcs_score'],
                                        entry_price=signal['entry_price'],
                                        stop_loss=signal['stop_loss'],
                                        take_profit=signal['take_profit'],
                                        tier_generated=signal_type,
                                        status=SignalStatus.ACTIVE,
                                        ghost_mode_applied=False,
                                        users_received=0,
                                        users_executed=0,
                                        win_rate_prediction=85.0,
                                        actual_result=None,
                                        profit_pips=None
                                    )
                                    live_tracker.track_signal_generation(live_signal)
                                except Exception as e:
                                    self.logger.warning(f"Performance tracking error: {e}")
                            
                            # Apply ghost mode to signal
                            ghost_applied = False
                            if PERFORMANCE_TRACKING:
                                try:
                                    ghosted_signal, ghost_actions = enhanced_ghost_tracker.apply_enhanced_ghost_mode(
                                        signal, "commander"  # Default tier for classification
                                    )
                                    if ghost_actions:
                                        signal.update(ghosted_signal)
                                        ghost_applied = True
                                        self.logger.debug(f"👻 Ghost mode applied: {len(ghost_actions)} modifications")
                                except Exception as e:
                                    self.logger.warning(f"Ghost mode error: {e}")
                            
                            # Create appropriate alert
                            if signal_type == "ARCADE":
                                alert_data = self.create_arcade_alert(signal['tcs_score'], signal['id'], signal['symbol'])
                                arcade_count += 1
                            else:  # SNIPER
                                alert_data = self.create_sniper_alert(signal['tcs_score'], signal['id'], signal['symbol'])
                                sniper_count += 1
                            
                            # Send alert
                            if self.send_telegram_message(alert_data["text"], alert_data["keyboard"]):
                                self.sent_signals.add(signal['id'])
                                
                                # Update performance tracking with send confirmation
                                if PERFORMANCE_TRACKING:
                                    try:
                                        live_tracker.update_signal_transmission(signal['id'], True, ghost_applied)
                                    except Exception as e:
                                        self.logger.warning(f"Performance update error: {e}")
                                
                                # Log with classification details
                                risk_eff = self.calculate_risk_efficiency(signal)
                                velocity = self.calculate_market_velocity(signal['symbol'])
                                ghost_status = " [👻 GHOST]" if ghost_applied else ""
                                
                                self.logger.info(f"✅ Sent {signal_type} signal {signal['id']}: {signal['symbol']} {signal['direction']} (TCS: {signal['tcs_score']}%, RE: {risk_eff:.1f}, MV: {velocity:.1f}){ghost_status}")
                            else:
                                self.logger.error(f"❌ Failed to send {signal_type} signal {signal['id']}")
                        else:
                            self.logger.debug(f"🚫 Signal {signal['id']} doesn't meet ARCADE or SNIPER criteria")
                        
                        # Small delay between sends
                        time.sleep(1)
                    
                    # Clean up old sent signals
                    if len(self.sent_signals) > 200:
                        self.sent_signals = set(list(self.sent_signals)[-200:])
                        
                    # Log session stats every 10 cycles
                    if (arcade_count + sniper_count) % 10 == 0:
                        self.logger.info(f"📊 SESSION STATS: 🔫 ARCADE: {arcade_count}, ⚡ SNIPER: {sniper_count}")
                        
                else:
                    self.logger.debug("No candidate signals found")
                    
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                self.logger.info("🚀 Hybrid engine stopped")
                break
            except Exception as e:
                self.logger.error(f"Engine error: {e}")
                time.sleep(60)
    
    def test_classification(self):
        """Test the classification system"""
        print("🚀 TESTING HYBRID RISK-VELOCITY ENGINE")
        print("=" * 60)
        print(f"🔫 ARCADE Criteria:")
        print(f"  - Risk Efficiency > {self.arcade_risk_efficiency_min}")
        print(f"  - Market Velocity > {self.arcade_velocity_min} pips/hour")
        print(f"  - TCS ≥ {self.arcade_min_tcs}% (RAISED FROM 70%)")
        print(f"  - Risk/Reward: 1:1 to 1:2")
        print()
        print(f"⚡ SNIPER Criteria:")
        print(f"  - Absolute Profit ≥ {self.sniper_min_profit_pips} pips")
        print(f"  - TCS ≥ {self.sniper_min_tcs}%")
        print(f"  - Risk/Reward ≥ 1:{self.sniper_min_risk_reward}")
        print(f"  - Risk Efficiency: 1.5-4.0")
        print()
        
        # Test with current signals
        signals = self.get_candidate_signals()
        if signals:
            print(f"🔍 Testing {len(signals)} signals:")
            
            arcade_count = 0
            sniper_count = 0
            filtered_count = 0
            
            for signal in signals[:10]:  # Test first 10
                signal_type = self.classify_signal_type(signal)
                risk_eff = self.calculate_risk_efficiency(signal)
                velocity = self.calculate_market_velocity(signal['symbol'])
                
                if signal_type == "ARCADE":
                    print(f"  🔫 ARCADE: {signal['symbol']} {signal['direction']} (TCS: {signal['tcs_score']}%, RE: {risk_eff:.1f}, MV: {velocity:.1f})")
                    arcade_count += 1
                elif signal_type == "SNIPER":
                    print(f"  ⚡ SNIPER: {signal['symbol']} {signal['direction']} (TCS: {signal['tcs_score']}%, RE: {risk_eff:.1f}, MV: {velocity:.1f})")
                    sniper_count += 1
                else:
                    print(f"  🚫 FILTERED: {signal['symbol']} {signal['direction']} (TCS: {signal['tcs_score']}%, RE: {risk_eff:.1f}, MV: {velocity:.1f})")
                    filtered_count += 1
            
            print()
            print(f"📊 TEST RESULTS:")
            print(f"🔫 ARCADE signals: {arcade_count}")
            print(f"⚡ SNIPER signals: {sniper_count}")
            print(f"🚫 Filtered out: {filtered_count}")
            print(f"📤 Total qualified: {arcade_count + sniper_count}")
            
        else:
            print("📭 No signals available for testing")

if __name__ == "__main__":
    engine = HybridRiskVelocityEngine()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            engine.test_classification()
        elif sys.argv[1] == "run":
            engine.run_hybrid_engine()
    else:
        print("Usage:")
        print("  python3 hybrid_risk_velocity_engine.py test  - Test classification")
        print("  python3 hybrid_risk_velocity_engine.py run   - Run hybrid engine")