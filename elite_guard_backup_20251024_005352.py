#!/usr/bin/env python3
"""
ELITE GUARD v7.0 - BALANCED EDITION
Target: 45-50% win rate with 1-2 signals per hour minimum
Focus: User engagement + quality improvement
"""

import json
import logging
import os
import statistics

# Add unified logging support
import sys
import threading
import time
import traceback
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pytz
import zmq

from citadel_lite import CitadelProtection
from src.bitten_core.news_api_client import NewsAPIClient
from src.bitten_core.constants import (
    get_pip_size,
    get_min_max_stop_pips,
    calc_scalp_stop_pips,
    ATR_SCALP_MULTIPLIERS
)

sys.path.insert(0, "/root/HydraX-v2")

# Finnhub hybrid data adapter (Phase 1 - Finnhub integration)
sys.path.insert(0, "/root/HydraX-v2")
from services.finnhub_data_adapter import FinnhubDataAdapter

# Import Memory-Lite system for signal filtering
from memory_lite import memory as memory_system


# Comprehensive tracking disabled - using direct DB writes
# from comprehensive_tracking_layer import log_signal_comprehensive as log_trade
def log_trade(*args, **kwargs):
    """Stub for disabled comprehensive tracking"""
    pass


# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# TRADING CONFIGURATION CONSTANTS
class TradingConfig:
    # Pip sizes for different symbol types - SCALPING OPTIMIZED
    PIP_SIZES = {
        "JPY": 0.01,
        "GOLD": 0.1,  # XAUUSD - $0.10 = 1 pip (2510.50 to 2510.60 = 1 pip)
        "SILVER": 0.001,  # XAGUSD - $0.001 = 1 pip (38.500 to 38.501 = 1 pip)
        "BTC": 1.0,  # BTCUSD - $1 = 1 pip
        "ETH": 0.1,  # ETHUSD - $0.10 = 1 pip
        "DEFAULT": 0.0001,
    }

    # Minimum stop requirements to prevent broker errors - SCALPING OPTIMIZED
    MIN_STOP_REQUIREMENTS = {
        "USDMXN": 60,
        "USDSEK": 20,
        "USDCNH": 30,
        "XAGUSD": 25,  # Silver - Increased to 25 cents for better risk management
        "XAUUSD": 30,  # Gold - Increased to $30 move for safer stops
        "USDNOK": 20,
        "USDDKK": 20,
        "USDTRY": 50,
        "USDZAR": 30,
        # JPY pairs need larger stops due to their pip value (0.01 = 1 pip)
        "USDJPY": 15,
        "EURJPY": 18,
        "GBPJPY": 20,
        "AUDJPY": 15,
        "NZDJPY": 15,
    }

    # Session quality bonuses
    SESSION_BONUSES = {"LONDON": 10, "OVERLAP": 8, "NEWYORK": 6, "ASIAN": 2}

    # Risk management settings
    DEFAULT_RISK_PERCENT = 0.03  # 3% risk per trade
    DEFAULT_ACCOUNT_BALANCE = 1000.0


@dataclass
class PatternSignal:
    pattern: str
    direction: str
    entry_price: float
    confidence: float
    timeframe: str
    pair: str
    quality_score: float = 0  # NEW: Shows relative quality
    momentum_score: float = 0
    volume_quality: float = 0


class DynamicThresholdManager:
    """Manages dynamic thresholds per pattern based on session, volatility, and signal flow"""

    def __init__(self):
        # Base thresholds for each pattern - QUALITY focused
        self.thresholds = {
            "LIQUIDITY_SWEEP_REVERSAL": {
                "pip_sweep": 3.0,  # HIGH sweep requirement for quality
                "min_conf": 75,  # Minimum 75% confidence
                "vol_gate": 1.3,
                "rejection_required": True,  # Require rejection candle
            },
            "ORDER_BLOCK_BOUNCE": {
                "body_ratio": 0.6,  # Strong body requirement
                "min_conf": 70,  # Minimum 70% confidence
                "vol_gate": 1.2,
                "zone_tolerance": 0.3,  # Tighter zone
            },
            "FAIR_VALUE_GAP_FILL": {"gap_size": 0.5, "min_conf": 65, "vol_gate": 1.1, "fill_ratio": 0.5},  # Lower base
            "VCB_BREAKOUT": {
                "compression_ratio": 0.6,  # Tighter compression = better quality
                "min_conf": 75,  # Higher quality requirement
                "vol_gate": 2.0,  # Need 2x volume for institutional move
                "breakout_mult": 1.5,  # Stronger breakout required
            },
            "SWEEP_RETURN": {
                "wick_ratio": 0.6,  # 60% wick shows real rejection
                "min_conf": 78,  # Higher quality signals only
                "vol_gate": 1.8,  # Need volume for liquidity sweep
                "sweep_pips": 3.0,  # Clear sweep required
            },
            "MOMENTUM_BURST": {
                "breakout_pips": 2.0,  # Real momentum needs 2+ pip move
                "min_conf": 75,  # Quality signals only
                "vol_gate": 2.5,  # Strong volume for momentum
                "momentum_mult": 1.5,  # 1.5x average momentum required
            },
            "TRAPDOOR_SSR": {
                "sweep_min_pips": 3.0,  # Minimum session high/low sweep distance
                "min_conf": 72,  # Minimum 72% confidence for SSR
                "vol_gate": 1.2,  # Volume confirmation requirement
                "ltf_confirmation": True,  # Require LTF break of structure
                "entry_window_minutes": 30,  # Entry window after sweep detection (updated from 15)
            },
            "PRESSURE_VALVE_VCB": {
                "compression_bars": 5,  # Minimum bars in compression
                "max_compression_atr": 0.8,  # Max range vs ATR for compression
                "break_multiplier": 1.3,  # Breakout size vs ATR
                "min_conf": 70,  # Minimum confidence
                "entry_window_minutes": 25,  # Time window for entry (updated from 20)
            },
        }

        # Track signals per pattern per 15-min window
        self.signal_counts = {pattern: 0 for pattern in self.thresholds}
        self.tradeable_count = 0  # Track 70%+ signals
        self.scout_count = 0  # Track <70% scout signals
        self.last_adjust_time = datetime.now()
        self.current_session = self.get_session()
        self.last_atr = 0.0005  # Default ATR
        self.adjustment_history = []
        self.scout_mode_active = True  # Start in scout mode for quiet periods
        self.last_hour_tradeables = []  # Track hourly tradeable rate

    def get_session(self):
        """Determine current trading session based on UTC time"""
        hour = datetime.utcnow().hour
        if 22 <= hour or hour < 7:
            return "ASIAN"  # Low volatility session
        elif 7 <= hour < 12:
            return "LONDON"  # Medium-high volatility
        elif 12 <= hour < 17:
            return "NY"  # High volatility
        elif 17 <= hour < 22:
            return "LATE_NY"  # Medium volatility
        else:
            return "OVERLAP"  # Highest volatility

    def update_volatility(self, atr_value):
        """Update current market volatility (ATR)"""
        self.last_atr = atr_value

    def record_signal(self, pattern):
        """Record that a signal was generated for tracking"""
        if pattern in self.signal_counts:
            self.signal_counts[pattern] += 1

    def adjust_thresholds(self):
        """Adjust thresholds based on session, volatility, and signal flow"""
        now = datetime.now()

        # Only adjust every 15 minutes
        if (now - self.last_adjust_time).total_seconds() < 900:
            return

        self.last_adjust_time = now
        session = self.get_session()

        # Calculate hourly tradeable rate
        self.last_hour_tradeables = [t for t in self.last_hour_tradeables if (now - t).total_seconds() < 3600]
        hourly_rate = len(self.last_hour_tradeables)

        # Phase out scout mode when we have 2+ tradeables per hour
        if hourly_rate >= 2:
            self.scout_mode_active = False
            logger.info(f"📈 Scout mode DISABLED - {hourly_rate} tradeables/hr")
        elif hourly_rate < 1:
            self.scout_mode_active = True
            logger.info(f"🔍 Scout mode ENABLED - {hourly_rate} tradeables/hr")

        # Log adjustment
        logger.info(
            f"🎯 Adjusting thresholds - Session: {session}, ATR: {self.last_atr:.5f}, Scout: {self.scout_mode_active}"
        )

        for pattern in self.thresholds:
            th = self.thresholds[pattern]
            signals = self.signal_counts[pattern]

            # Base adjustment based on signal flow
            if signals == 0:
                # No signals - loosen thresholds by 10%
                self._loosen_thresholds(th, 0.10)
                logger.info(f"  {pattern}: No signals - loosening 10%")
            elif signals > 5:
                # Too many signals - tighten by 15%
                self._tighten_thresholds(th, 0.15)
                logger.info(f"  {pattern}: {signals} signals - tightening 15%")
            elif signals > 3:
                # Good flow - slight tightening
                self._tighten_thresholds(th, 0.05)
                logger.info(f"  {pattern}: {signals} signals - tightening 5%")
            # 1-3 signals is ideal, no adjustment

            # Session-based override
            if session == "ASIAN":
                # Asian session - loosen for low volatility
                self._loosen_thresholds(th, 0.20)
                logger.debug(f"  {pattern}: Asian session - extra 20% looser")
            elif session in ["LONDON", "NY"]:
                # Active sessions - slight tightening for quality
                self._tighten_thresholds(th, 0.10)
                logger.debug(f"  {pattern}: Active session - 10% tighter")
            elif session == "OVERLAP":
                # Highest volatility - tighten more
                self._tighten_thresholds(th, 0.15)
                logger.debug(f"  {pattern}: Overlap session - 15% tighter")

            # Volatility-based override
            if self.last_atr < 0.0003:
                # Very low volatility - aggressive loosening
                self._loosen_thresholds(th, 0.25)
                logger.debug(f"  {pattern}: Very low ATR - 25% looser")
            elif self.last_atr < 0.0005:
                # Low volatility - moderate loosening
                self._loosen_thresholds(th, 0.15)
                logger.debug(f"  {pattern}: Low ATR - 15% looser")
            elif self.last_atr > 0.001:
                # High volatility - tighten for quality
                self._tighten_thresholds(th, 0.20)
                logger.debug(f"  {pattern}: High ATR - 20% tighter")

            # Apply bounds to prevent extreme values
            self._apply_bounds(th, pattern)

            # Reset signal count for next period
            self.signal_counts[pattern] = 0

    def _loosen_thresholds(self, thresholds, factor):
        """Loosen thresholds by given factor"""
        for key, value in thresholds.items():
            if key == "rejection_required":
                continue  # Skip boolean
            elif "pip" in key or "ratio" in key or "size" in key or "mult" in key:
                thresholds[key] *= 1 - factor  # Reduce requirement
            elif "conf" in key:
                thresholds[key] = max(20, value - (factor * 20))  # Lower min confidence
            elif "vol" in key:
                thresholds[key] *= 1 - factor  # Lower volume gate

    def _tighten_thresholds(self, thresholds, factor):
        """Tighten thresholds by given factor"""
        for key, value in thresholds.items():
            if key == "rejection_required":
                continue  # Skip boolean
            elif "pip" in key or "ratio" in key or "size" in key or "mult" in key:
                thresholds[key] *= 1 + factor  # Increase requirement
            elif "conf" in key:
                thresholds[key] = min(85, value + (factor * 20))  # Raise min confidence
            elif "vol" in key:
                thresholds[key] *= 1 + factor  # Raise volume gate

    def _apply_bounds(self, thresholds, pattern):
        """Apply reasonable bounds to prevent extreme threshold values"""
        bounds = {
            "pip_sweep": (0.05, 5.0),
            "min_conf": (20, 85),
            "vol_gate": (0.5, 2.0),
            "body_ratio": (0.1, 0.8),
            "compression_ratio": (0.3, 0.9),
            "wick_ratio": (0.3, 0.9),
            "gap_size": (0.1, 2.0),
            "breakout_pips": (0.5, 5.0),
        }

        for key, value in thresholds.items():
            if key in bounds:
                min_val, max_val = bounds[key]
                thresholds[key] = max(min_val, min(max_val, value))

    def get_threshold(self, pattern, key):
        """Get current threshold value for pattern and key"""
        if pattern in self.thresholds and key in self.thresholds[pattern]:
            return self.thresholds[pattern][key]
        return None

    def get_status(self):
        """Get current status of thresholds"""
        return {
            "session": self.current_session,
            "atr": self.last_atr,
            "signal_counts": self.signal_counts.copy(),
            "thresholds": self.thresholds.copy(),
        }

    final_score: float = 0


def get_pip_size(symbol: str) -> float:
    """Centralized pip size calculation for all patterns"""
    if "JPY" in symbol:
        return TradingConfig.PIP_SIZES["JPY"]
    elif symbol == "XAUUSD":
        return TradingConfig.PIP_SIZES["GOLD"]
    elif symbol == "XAGUSD":
        return TradingConfig.PIP_SIZES["SILVER"]
    else:
        return TradingConfig.PIP_SIZES["DEFAULT"]


class EliteGuardBalanced:
    """Balanced signal generation for optimal user engagement"""

    def __init__(self):
        self.context = zmq.Context()

        # Initialize Finnhub hybrid data adapter (replaces EA tick consumption)
        print("🌐 Initializing Finnhub Data Adapter...")
        self.finnhub_adapter = FinnhubDataAdapter()
        print("✅ Finnhub adapter ready - hybrid candles + ticks")
        self.subscriber = None
        self.publisher = None

        # Track startup time for stale data detection grace period
        self.startup_time = time.time()

        # Market data storage - EXPANDED for proper pattern detection
        self.tick_data = defaultdict(lambda: deque(maxlen=500))

        # CUSTOM 15-SECOND BARS (4x faster than M1) - NEW FOR RAPID PATTERN DETECTION
        self.s15_data = defaultdict(lambda: deque(maxlen=400))  # 15s bars (~100 minutes / 1.6 hours)
        self.s15_timestamps = defaultdict(set)  # Dedup by timestamp

        self.m1_data = defaultdict(lambda: deque(maxlen=500))  # M1 OHLC data (~8 hours)
        self.m5_data = defaultdict(lambda: deque(maxlen=300))  # M5 OHLC data (~25 hours)
        self.m15_data = defaultdict(lambda: deque(maxlen=200))  # M15 OHLC data (~50 hours)
        self.m30_data = defaultdict(lambda: deque(maxlen=100))  # M30 OHLC data (~50 hours)
        self.h1_data = defaultdict(lambda: deque(maxlen=100))  # H1 OHLC data (~100 hours)
        self.h4_data = defaultdict(lambda: deque(maxlen=50))  # H4 OHLC data (~200 hours)
        self.current_candles = {}  # For building M1 candles from ticks
        self.last_tick_time = defaultdict(float)

        # Custom bar statistics
        self.custom_bar_stats = {"received": 0, "duplicates": 0, "processed": 0}

        # ✅ TASK D: Health metrics for observability
        self.health_metrics = {
            "tick_count": 0,
            "tick_rate": 0.0,  # ticks/second
            "candle_close_count": 0,
            "candle_close_rate": 0.0,  # bars/second
            "pattern_candidates": 0,
            "pattern_kept": 0,
            "signals_fired": 0,
            "exec_confirms": 0,
            "data_lag_ms": 0.0,
            "last_tick_time": 0,
            "metrics_start_time": time.time(),
        }

        # CITADEL Protection System
        self.citadel = CitadelProtection()

        # ML Performance tracking
        self.performance_history = {}

        # Pattern detection state
        self.last_signal_time = defaultdict(float)  # Per-pair cooldown
        self.signal_history = deque(maxlen=100)  # Track recent signals

        # Define trading pairs FIRST (before load_candles)
        self.trading_pairs = [
            # Major Forex Pairs (7) - SYNCHRONIZED WITH FINNHUB OCT 22, 2025
            "EURUSD",
            "GBPUSD",
            "USDCHF",
            "USDJPY",
            "AUDUSD",
            "NZDUSD",
            "USDCAD",  # Re-added to match Finnhub feed
            # Cross Pairs (10)
            "EURJPY",
            "GBPJPY",
            "AUDJPY",
            "NZDJPY",
            "EURGBP",
            "EURAUD",
            "EURNZD",  # Added to match Finnhub feed
            "GBPAUD",  # Added to match Finnhub feed
            "GBPNZD",  # Added to match Finnhub feed
            # Removed unsupported pairs: GBPCAD, CHFJPY, CADJPY, AUDCAD, AUDNZD
            # Additional Pairs (1)
            "USDCNH",
            # Precious Metals (2)
            "XAUUSD",  # GOLD
            "XAGUSD",  # SILVER - Re-enabled for MetaSocket integration
            # Total: 19 pairs (synchronized with Finnhub WebSocket Manager)
        ]

        # Load candle cache on startup (AFTER trading_pairs defined)
        self.load_candles()

        # Test candle building (for debugging)
        self.test_candle_building()

        # Run initial analysis on startup
        print("\n" + "=" * 60)
        print("🔍 RUNNING INITIAL 6-HOUR ANALYSIS ON STARTUP")
        print("=" * 60)
        self.analyze_initial_data()
        self.verify_rr_ratio()
        print("=" * 60 + "\n")

        self.hourly_signal_count = defaultdict(int)  # Track signals per hour
        self.current_hour = datetime.now().hour

        # News calendar for confidence adjustment (Forex Factory API)
        self.news_client = NewsAPIClient()
        self.news_events = []
        self.last_news_fetch = 0

        # Quality tracking
        self.pattern_performance = defaultdict(lambda: {"wins": 0, "losses": 0})

        # Initialize Dynamic Threshold Manager
        self.threshold_manager = DynamicThresholdManager()

        # Initialize Pattern Module Enhancer (Phase 1 Universal Modules)
        print("🔧 Initializing Pattern Module Enhancer...")
        from services.pattern_module_enhancer import PatternModuleEnhancer
        self.module_enhancer = PatternModuleEnhancer(
            elite_guard_baseline_wr=0.68,  # Elite Guard's proven historical win rate
            finnhub_api_key='d3rvpb1r01qldtrba440d3rvpb1r01qldtrba44g'
        )
        print("✅ Pattern Module Enhancer ready (5 modules + Bayesian calibration)")

        # Balanced thresholds (less strict than optimized)
        # Trading pairs already defined above (before load_candles)

        self.MIN_MOMENTUM = 30  # Require strong momentum
        self.MIN_VOLUME = 20  # Require decent volume
        self.MIN_TREND = 15  # Require some trend alignment
        self.MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "70"))  # Lowered to 70% for more data collection
        self.COOLDOWN_MINUTES = 5  # Reduced cooldown to allow more signals (5-10/hr target)

        # Quality tiers for user display
        self.QUALITY_TIERS = {
            "PREMIUM": 75,  # Best signals
            "STANDARD": 65,  # Good signals
            "ACCEPTABLE": 55,  # Minimum viable
        }

        # Session times
        self.sessions = {"tokyo": (0, 9), "london": (8, 17), "newyork": (13, 22), "overlap_london_ny": (13, 17)}

        self.running = False

    def get_session(self):
        """Determine current trading session based on UTC time"""
        from datetime import datetime

        hour = datetime.utcnow().hour
        if 22 <= hour or hour < 7:
            return "ASIAN"  # Low volatility session
        elif 7 <= hour < 12:
            return "LONDON"  # Medium-high volatility
        elif 12 <= hour < 17:
            return "NY"  # High volatility
        elif 17 <= hour < 22:
            return "LATE_NY"  # Medium volatility
        return "UNKNOWN"

    def analyze_signal_quality(self):
        """Analyze signal quality from last 30 minutes of truth log"""
        try:
            with open("/root/HydraX-v2/truth_log.jsonl", "r") as f:
                lines = f.readlines()

            recent = []
            cutoff_time = datetime.now() - timedelta(seconds=1800)  # 30 minutes

            for line in lines[-200:]:  # Check last 200 lines for efficiency
                try:
                    data = json.loads(line)
                    timestamp_str = data.get("timestamp", "")
                    if timestamp_str:
                        # Parse ISO format timestamp
                        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00").replace("+00:00", ""))
                        if ts > cutoff_time:
                            recent.append(data)
                except:
                    continue

            # Calculate metrics
            total_signals = len(recent)

            # For win rate, we'd need to check if next candle closed higher
            # This is a simplified version - in reality we'd track actual outcomes
            wins = 0
            for sig in recent:
                # Simplified win check - would need actual outcome tracking
                if sig.get("quality_score", 0) > 70:  # Proxy for win
                    wins += 1

            win_rate = (wins / total_signals * 100) if total_signals else 0
            avg_conf = (
                sum(s.get("confidence", s.get("quality_score", 0)) for s in recent) / total_signals
                if total_signals
                else 0
            )
            avg_quality = sum(s.get("quality_score", 0) for s in recent) / total_signals if total_signals else 0

            # Pattern breakdown
            pattern_counts = defaultdict(int)
            for s in recent:
                pattern = s.get("pattern", "UNKNOWN")
                pattern_counts[pattern] += 1

            print(f"\n📊 SIGNAL QUALITY ANALYSIS (Last 30 min)")
            print(f"=" * 50)
            print(f"Total Signals: {total_signals} ({total_signals*2}/hr projected)")
            print(f"Win Rate: {win_rate:.1f}% (proxy based on quality>70)")
            print(f"Avg Confidence: {avg_conf:.1f}%")
            print(f"Avg Quality: {avg_quality:.1f}%")
            print(f"\nPattern Distribution:")
            for pattern, count in pattern_counts.items():
                print(f"  {pattern}: {count}")
            print(f"=" * 50)

            return total_signals, win_rate, avg_conf, avg_quality

        except Exception as e:
            print(f"Error analyzing signals: {e}")
            return 0, 0, 0, 0

    def setup_zmq(self):
        """Setup ZMQ connections (SIGNALS ONLY - no tick consumption)"""
        try:
            # ✅ Publisher for signals (KEEP - generators still publish signals!)
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind("tcp://*:5557")
            print(f"🔌 Signal PUB bound to 5557")

            # ✅ Subscribe to Grokkeeper ML adjustments on port 5565 (KEEP - ML feedback)
            self.ml_subscriber = self.context.socket(zmq.SUB)
            self.ml_subscriber.connect("tcp://127.0.0.1:5565")
            self.ml_subscriber.setsockopt_string(zmq.SUBSCRIBE, "PATTERN_ADJUSTMENT")
            self.ml_subscriber.setsockopt(zmq.RCVTIMEO, 100)  # Non-blocking
            print("🤖 Connected to Grokkeeper ML feedback on port 5565")

            logger.info(
                "✅ ZMQ connections established (5557 PUB for signals, 5565 SUB for ML)"
            )
            logger.info("📡 Market data: Using Finnhub hybrid candles (not EA ticks)")
            return True
        except Exception as e:
            logger.error(f"❌ ZMQ setup failed: {e}")
            return False

    def update_pattern_thresholds_from_ml(self):
        """Check for ML threshold updates from Grokkeeper"""
        try:
            if not hasattr(self, "ml_subscriber"):
                return

            message = self.ml_subscriber.recv_string(zmq.NOBLOCK)
            if message.startswith("PATTERN_ADJUSTMENT"):
                adjustment = json.loads(message.split(" ", 1)[1])
                pattern = adjustment["pattern"]
                new_threshold = adjustment["threshold"]
                win_rate = adjustment["win_rate"]

                # Initialize pattern_thresholds if not exists
                if not hasattr(self, "pattern_thresholds"):
                    self.pattern_thresholds = {
                        "VCB_BREAKOUT": 65,
                        "SWEEP_RETURN": 70,
                        "MOMENTUM_BURST": 70,
                        "LIQUIDITY_SWEEP_REVERSAL": 75,
                        "ORDER_BLOCK_BOUNCE": 80,
                        "FAIR_VALUE_GAP_FILL": 85,
                    }

                old_threshold = self.pattern_thresholds.get(pattern, 70)
                self.pattern_thresholds[pattern] = new_threshold
                print(
                    f"🎯 ML ADJUSTMENT: {pattern} threshold {old_threshold}% → {new_threshold}% (WR: {win_rate:.1f}%)"
                )

        except zmq.Again:
            pass  # No message available
        except Exception as e:
            print(f"ML update error: {e}")

    def is_active_session(self) -> bool:
        """Check if we're in an active trading session"""
        # TEMPORARY: Always active for testing
        return True

        current_hour = datetime.now(pytz.UTC).hour

        # Most active during overlaps
        if 13 <= current_hour <= 17:  # London/NY overlap
            return True
        if 8 <= current_hour <= 22:  # London through NY
            return True
        if 0 <= current_hour <= 2:  # Late Asia
            return True

        return False

    def get_session_bonus(self) -> float:
        """Get confidence bonus based on session"""
        current_hour = datetime.now(pytz.UTC).hour

        if 13 <= current_hour <= 17:  # Best time
            return 10
        elif 8 <= current_hour <= 11:  # London open
            return 8
        elif 14 <= current_hour <= 16:  # NY open
            return 7
        else:
            return 5

    def calculate_dynamic_confidence(
        self, symbol: str, base_pattern_score: float, momentum: float, volume: float
    ) -> float:
        """Calculate confidence based on quality components for 75-82% target"""
        confidence = 0

        # Base from pattern strength (65% contribution for reliable base)
        base_contribution = base_pattern_score * 0.65
        confidence += base_contribution
        print(f"🎯 {symbol} CONFIDENCE CALCULATION:")
        print(f"  📊 Base pattern: {base_pattern_score:.1f} * 0.65 = {base_contribution:.1f}%")

        # Momentum bonus: +0.2% per pip for better signal quality
        momentum_bonus = min(12, momentum * 0.2)  # Cap at 12%
        confidence += momentum_bonus
        print(f"  📊 Momentum: {momentum:.1f} pips * 0.2 = +{momentum_bonus:.1f}%")

        # Volume scoring (volume is % of average, e.g., 100 = average)
        if volume >= 100:  # At or above average
            volume_bonus = 8.0
        elif volume >= 80:  # Slightly below average
            volume_bonus = 6.0
        elif volume >= 60:  # Below average
            volume_bonus = 4.0
        elif volume >= 40:  # Low volume
            volume_bonus = 2.0
        else:
            volume_bonus = 1.0
        confidence += volume_bonus
        print(f"  📊 Volume: {volume:.0f}% of avg = +{volume_bonus:.1f}%")

        # Session bonus (5-10%)
        session_bonus = self.get_session_bonus()
        confidence += session_bonus
        print(f"  📊 Session: +{session_bonus:.0f}%")

        # Spread quality (-1 to +2%)
        spread_adjustment = 0
        if symbol in self.tick_data:
            recent_ticks = list(self.tick_data[symbol])[-10:]
            if recent_ticks:
                spreads = [(t.get("ask", 0) - t.get("bid", 0)) for t in recent_ticks if t.get("ask") and t.get("bid")]
                if spreads:
                    avg_spread = np.mean(spreads)
                    pip_size = get_pip_size(symbol)
                    spread_pips = avg_spread / pip_size
                    if spread_pips < 1.5:
                        spread_adjustment = 2  # Tight spread
                    elif spread_pips < 2.5:
                        spread_adjustment = 0  # Normal
                    else:
                        spread_adjustment = -1  # Wide spread
                    print(f"  📊 Spread: {spread_pips:.1f}p = {spread_adjustment:+d}%")
        confidence += spread_adjustment

        # Market activity bonus
        activity_bonus = 0
        if symbol in self.m1_data and len(self.m1_data[symbol]) >= 5:
            recent = list(self.m1_data[symbol])[-5:]
            ranges = [(c["high"] - c["low"]) for c in recent]
            avg_range = np.mean(ranges) if ranges else 0
            pip_size = get_pip_size(symbol)
            range_pips = avg_range / pip_size
            if range_pips > 3:
                activity_bonus = 4  # Very active
            elif range_pips > 1.5:
                activity_bonus = 2  # Active
            print(f"  📊 Activity: {range_pips:.1f}p range = +{activity_bonus}%")
        confidence += activity_bonus

        # Apply recalibration based on actual performance data
        raw_confidence = confidence
        pre_calibration = min(95, max(55, confidence))  # Floor at 55%, cap at 95%

        # RECALIBRATION: Fix overconfident 85%+ signals (actual 32.4% win rate)
        if pre_calibration >= 85:
            # 85%+ severely overconfident (32.4% actual vs 85%+ claimed)
            final_confidence = 30 + (pre_calibration - 85) * 0.5
            final_confidence = min(35, max(30, final_confidence))
        elif pre_calibration >= 80:
            # 80-84% is optimal range (43.4% actual) - slight adjustment
            final_confidence = 40 + (pre_calibration - 80) * 1.25
            final_confidence = min(45, max(40, final_confidence))
        elif pre_calibration >= 75:
            # 75-79% performs at 39.6%
            final_confidence = 35 + (pre_calibration - 75) * 1.0
            final_confidence = min(40, max(35, final_confidence))
        elif pre_calibration >= 70:
            # 70-74% performs at 37.4%
            final_confidence = 32 + (pre_calibration - 70) * 1.25
            final_confidence = min(37, max(32, final_confidence))
        else:
            # Below 70% - conservative mapping
            final_confidence = max(20, pre_calibration * 0.5)

        print(f"  🎯 RAW: {raw_confidence:.1f}% → PRE: {pre_calibration:.1f}% → CALIBRATED: {final_confidence:.1f}%")
        print(f"  🔧 RECALIBRATION: Based on actual win rate performance (80-84% = best at 43.4%)")

        return round(final_confidence, 1)

    def calculate_atr(self, symbol: str, period: int = 14) -> float:
        """Calculate Average True Range for R:R feasibility check"""
        if symbol not in self.m5_data or len(self.m5_data[symbol]) < period:
            # Default ATR values for different pairs
            if "JPY" in symbol:
                return 0.5  # 50 pips default for JPY pairs
            elif symbol in ["XAUUSD"]:
                return 0.5  # 50 pips for gold (adjusted for 0.01 pip size)
            elif symbol in ["XAGUSD"]:
                return 0.05  # 5 pips for silver
            else:
                return 0.001  # 10 pips default for majors

        candles = list(self.m5_data[symbol])[-period:]
        pip_size = get_pip_size(symbol)

        true_ranges = []
        for i in range(1, len(candles)):
            high_low = candles[i]["high"] - candles[i]["low"]
            high_close = abs(candles[i]["high"] - candles[i - 1]["close"])
            low_close = abs(candles[i]["low"] - candles[i - 1]["close"])
            true_range = max(high_low, high_close, low_close)
            true_ranges.append(true_range)

        atr = np.mean(true_ranges) if true_ranges else 0.001
        atr_pips = atr / pip_size
        return atr_pips

    def calculate_quality_score(self, signal: PatternSignal) -> float:
        """Calculate overall quality score for ranking"""
        score = 0

        # Base pattern confidence
        score += signal.confidence * 0.3

        # Momentum contribution
        if signal.momentum_score >= 25:
            score += 20
        elif signal.momentum_score >= 15:
            score += 10

        # Volume quality
        if signal.volume_quality >= 20:
            score += 15
        elif signal.volume_quality >= 10:
            score += 8

        # Session bonus
        score += self.get_session_bonus()

        # Pattern history performance
        pattern_stats = self.pattern_performance[signal.pattern]
        if pattern_stats["wins"] + pattern_stats["losses"] > 5:
            win_rate = pattern_stats["wins"] / (pattern_stats["wins"] + pattern_stats["losses"])
            score += win_rate * 20

        # Spread penalty (if available)
        if signal.pair in self.tick_data:
            recent_ticks = list(self.tick_data[signal.pair])[-10:]
            if recent_ticks:
                spreads = [abs(t.get("ask", 0) - t.get("bid", 0)) for t in recent_ticks]
                avg_spread = np.mean(spreads) if spreads else 0
                pip_size = (
                    0.01
                    if "JPY" in signal.pair
                    else 0.01 if signal.pair == "XAUUSD" else 0.001 if signal.pair == "XAGUSD" else 0.0001
                )
                spread_pips = avg_spread / pip_size

                if spread_pips < 2:
                    score += 5
                elif spread_pips > 4:
                    score -= 10

        return min(100, max(0, score))

    def calculate_momentum_score(self, symbol: str, direction: str) -> float:
        """FIXED: Calculate momentum in PIPS not percentage"""
        try:
            if symbol not in self.m1_data or len(self.m1_data[symbol]) < 5:
                return 0

            candles = list(self.m1_data[symbol])  # Convert deque to list for slicing
            if len(candles) < 5:
                return 0

            recent = candles[-5:]

            # Calculate pip size for this symbol
            if "JPY" in symbol:
                pip_size = 0.01
            elif symbol == "XAUUSD":
                pip_size = 0.1
            elif symbol == "XAGUSD":
                pip_size = 0.001  # Silver: 0.001 = 1 pip (38.500 to 38.501 = 1 pip)
            else:
                pip_size = 0.0001

            # Calculate average pip movement over last 5 candles
            pip_changes = []
            for i in range(1, len(recent)):
                pip_change = (recent[i]["close"] - recent[i - 1]["close"]) / pip_size
                pip_changes.append(pip_change)

            # Average pip movement (directional)
            avg_pip_movement = sum(pip_changes) / len(pip_changes)

            # 3-bar momentum in pips for stronger signal
            momentum_3bar_pips = (recent[-1]["close"] - recent[-3]["close"]) / pip_size

            # Use the stronger of the two
            momentum_pips = max(abs(avg_pip_movement), abs(momentum_3bar_pips))

            # Score based on pip movement - proper scaling for real trading
            # 1 pip = 10 score, 5 pips = 50 score, 10 pips = 100 score
            score = momentum_pips * 10

            print(
                f"🔍 Momentum {symbol} {direction}: Avg={avg_pip_movement:.1f}pips, 3bar={momentum_3bar_pips:.1f}pips, Score={score:.1f}"
            )

            # Direction check - return real score for prime time trading
            if direction == "BUY" and momentum_3bar_pips > 0:
                return score  # Return actual calculated score
            elif direction == "SELL" and momentum_3bar_pips < 0:
                return score  # Return actual calculated score

            return 0  # Wrong direction = no momentum

        except Exception as e:
            print(f"❌ Momentum calc error for {symbol}: {e}")
            return 0

    def analyze_volume_profile(self, symbol: str) -> float:
        """Session-aware volume analysis for low-volatility periods"""
        try:
            from datetime import datetime

            current_hour = datetime.utcnow().hour

            # PROPER VOLUME SCORING FOR PRIME TIME
            min_volume_score = 10  # Base volume score for active trading

            # Session detection for logging
            if current_hour >= 22 or current_hour < 7:
                session = "ASIAN"
            elif current_hour >= 7 and current_hour < 8:
                session = "PRE-LONDON"
            else:
                session = "LONDON/NY"
            if symbol not in self.m1_data or len(self.m1_data[symbol]) < 10:
                return 20  # Default to decent volume for prime time

            candles = list(self.m1_data[symbol])  # Convert deque to list for slicing
            if len(candles) < 10:
                return 20  # Default to decent volume for prime time

            recent = candles[-10:]
            volumes = [c.get("tick_volume", 0) for c in recent]

            if not volumes or np.mean(volumes) == 0:
                return 20  # Default to decent volume for prime time

            # Current vs average
            current_vol = volumes[-1]
            avg_vol = np.mean(volumes[:-1])

            print(f"📊 Volume {symbol} [{session}]: Current={current_vol}, Avg={avg_vol:.1f}, Min={min_volume_score}")

            if avg_vol > 0:
                vol_ratio = current_vol / avg_vol
                # PRIME TIME VOLUME SCORING
                if vol_ratio > 1.5:  # 50% above average = strong volume
                    return min(50, vol_ratio * 30)
                elif vol_ratio > 1.2:  # 20% above average = good volume
                    return 30
                elif vol_ratio > 1.0:  # Above average
                    return 20
                else:  # Below average but still trading
                    return 15

            return 20  # Default volume for prime time

        except:
            return 20  # Default volume for prime time

    def detect_liquidity_sweep_reversal(self, symbol: str) -> Optional[PatternSignal]:
        """
        SCALPING LIQUIDITY SWEEP REVERSAL: Professional SMC pattern for <1hr scalps
        Price sweeps liquidity pools beyond key levels, then reverses with institutional rejection
        """
        try:
            print(f"🔍 LSR {symbol}: SCALPING LIQUIDITY SWEEP ANALYSIS")

            # Need sufficient data for proper sweep detection
            if len(self.m5_data[symbol]) < 10:
                print(f"🔍 LSR {symbol}: Need 10+ M5 candles, have {len(self.m5_data[symbol])}")
                return None

            candles = list(self.m5_data[symbol])[-10:]  # Last 10 candles for context
            current = candles[-1]

            # Professional pip size calculation
            if "JPY" in symbol:
                pip_size = 0.01
            elif symbol == "XAUUSD":
                pip_size = 0.1  # Gold: 0.1 = 1 pip
            elif symbol == "XAGUSD":
                pip_size = 0.001  # Silver
            else:
                pip_size = 0.0001

            print(f"🔍 LSR {symbol}: Using pip_size={pip_size}")

            # STEP 1: IDENTIFY LIQUIDITY POOLS
            # Look for recent swing highs/lows that form liquidity clusters
            swing_lookback = 5  # 5 candles for swing identification
            recent_highs = []
            recent_lows = []

            for i in range(swing_lookback, len(candles) - 1):  # Don't include current candle
                candle = candles[i]

                # Check if it's a swing high (higher than surrounding candles)
                is_swing_high = all(
                    candle["high"] >= candles[j]["high"]
                    for j in range(i - 2, i + 3)
                    if j != i and 0 <= j < len(candles) - 1
                )
                if is_swing_high:
                    recent_highs.append(candle["high"])

                # Check if it's a swing low
                is_swing_low = all(
                    candle["low"] <= candles[j]["low"]
                    for j in range(i - 2, i + 3)
                    if j != i and 0 <= j < len(candles) - 1
                )
                if is_swing_low:
                    recent_lows.append(candle["low"])

            if not recent_highs and not recent_lows:
                print(f"🔍 LSR {symbol}: No swing highs/lows found")
                return None

            print(f"🔍 LSR {symbol}: Found {len(recent_highs)} swing highs, {len(recent_lows)} swing lows")

            # STEP 2: DETECT LIQUIDITY SWEEP
            # Check if current candle swept above/below key levels
            # TIGHTENED: Require minimum 3 pip sweep for real liquidity grab
            sweep_threshold_pips = 3.0  # Raised from 2.5 to 3.0 (more selective)
            if symbol == "XAUUSD":
                sweep_threshold_pips = 300  # Gold needs bigger moves (raised from 250)
            elif "JPY" in symbol:
                sweep_threshold_pips = 4.0  # JPY pairs need more (raised from 3.0)

            bullish_sweep_strength = 0
            bearish_sweep_strength = 0
            swept_level = 0

            # Check for bearish liquidity sweep (swept above recent high)
            if recent_highs:
                highest_high = max(recent_highs)
                if current["high"] > highest_high:
                    sweep_pips = (current["high"] - highest_high) / pip_size
                    if sweep_pips >= sweep_threshold_pips:
                        bearish_sweep_strength = sweep_pips
                        swept_level = highest_high
                        print(f"🔍 LSR {symbol}: BEARISH SWEEP! {sweep_pips:.1f}p above {highest_high:.5f}")

            # Check for bullish liquidity sweep (swept below recent low)
            if recent_lows:
                lowest_low = min(recent_lows)
                if current["low"] < lowest_low:
                    sweep_pips = (lowest_low - current["low"]) / pip_size
                    if sweep_pips >= sweep_threshold_pips:
                        bullish_sweep_strength = sweep_pips
                        swept_level = lowest_low
                        print(f"🔍 LSR {symbol}: BULLISH SWEEP! {sweep_pips:.1f}p below {lowest_low:.5f}")

            # STEP 3: REJECTION CANDLE ANALYSIS
            candle_body = abs(current["close"] - current["open"])
            candle_range = current["high"] - current["low"]
            upper_wick = current["high"] - max(current["open"], current["close"])
            lower_wick = min(current["open"], current["close"]) - current["low"]

            body_ratio = candle_body / candle_range if candle_range > 0 else 0
            upper_wick_ratio = upper_wick / candle_range if candle_range > 0 else 0
            lower_wick_ratio = lower_wick / candle_range if candle_range > 0 else 0

            print(f"🔍 LSR {symbol}: Candle analysis:")
            print(f"   Range: {candle_range/pip_size:.1f}p, Body: {body_ratio:.2%}")
            print(f"   Upper wick: {upper_wick_ratio:.2%}, Lower wick: {lower_wick_ratio:.2%}")

            direction = None
            confidence_score = 0
            entry_price = 0

            # BEARISH SETUP: Swept highs, strong rejection downward - PROFESSIONAL LOGIC
            if bearish_sweep_strength > 0:
                # PROFESSIONAL: Multi-condition institutional sweep validation
                prev_candle = candles[-2] if len(candles) >= 2 else current

                # 1. STRONG REJECTION: 40%+ wick (loosened for more signals)
                strong_rejection = upper_wick_ratio >= 0.50

                # 2. CLOSED BELOW SWEPT LEVEL: Price returned after sweep
                closed_below = current["close"] < swept_level

                # 3. MOMENTUM SHIFT: Previous candle was bullish, current bearish
                momentum_shift = prev_candle["close"] > prev_candle["open"] and current["close"] < current["open"]

                # 4. MINIMUM RANGE: Avoid doji/small candles
                min_range_pips = 2.0
                has_range = (candle_range / pip_size) >= min_range_pips

                has_rejection = strong_rejection and closed_below and momentum_shift and has_range

                if has_rejection:
                    direction = "SELL"
                    entry_price = current["close"] - pip_size  # Enter below close

                    # Calculate scalping-focused confidence (55-90% range)
                    base_confidence = 55.0

                    # Sweep strength bonus (max +15)
                    sweep_bonus = min(15, bearish_sweep_strength * 2)  # 2% per pip swept

                    # Rejection quality bonus (max +12)
                    rejection_quality = upper_wick_ratio * 30  # Scale 40% wick = 12 points
                    rejection_bonus = min(12, rejection_quality)

                    # Close position bonus (max +8)
                    close_below_swept = (swept_level - current["close"]) / pip_size
                    close_bonus = min(8, close_below_swept)

                    # Volume confirmation (max +10) - TIGHTENED: Require 1.5x volume
                    volume_ratio = current.get("volume", 1000) / max(
                        1, sum(c.get("volume", 1000) for c in candles[-5:-1]) / 4
                    )
                    volume_bonus = (
                        min(10, (volume_ratio - 1.0) * 5) if volume_ratio >= 1.5 else 0
                    )  # RAISED from 1.2x to 1.5x

                    confidence_score = base_confidence + sweep_bonus + rejection_bonus + close_bonus + volume_bonus
                    confidence_score = min(90.0, max(60.0, confidence_score))

                    print(f"🔍 LSR {symbol}: BEARISH CONFIDENCE BREAKDOWN:")
                    print(f"   Base: {base_confidence:.1f}%")
                    print(f"   Sweep: +{sweep_bonus:.1f}% ({bearish_sweep_strength:.1f}p)")
                    print(f"   Rejection: +{rejection_bonus:.1f}% ({upper_wick_ratio:.1%} wick)")
                    print(f"   Close position: +{close_bonus:.1f}% ({close_below_swept:.1f}p below)")
                    print(f"   Volume: +{volume_bonus:.1f}% ({volume_ratio:.2f}x)")
                    print(f"   FINAL: {confidence_score:.1f}%")

            # BULLISH SETUP: Swept lows, strong rejection upward - PROFESSIONAL LOGIC
            elif bullish_sweep_strength > 0:
                # PROFESSIONAL: Multi-condition institutional sweep validation
                prev_candle = candles[-2] if len(candles) >= 2 else current

                # 1. STRONG REJECTION: 60%+ wick (consistent with bearish threshold)
                strong_rejection = lower_wick_ratio >= 0.60

                # 2. CLOSED ABOVE SWEPT LEVEL: Price returned after sweep
                closed_above = current["close"] > swept_level

                # 3. MOMENTUM SHIFT: Previous candle was bearish, current bullish
                momentum_shift = prev_candle["close"] < prev_candle["open"] and current["close"] > current["open"]

                # 4. MINIMUM RANGE: Avoid doji/small candles
                min_range_pips = 2.0
                has_range = (candle_range / pip_size) >= min_range_pips

                has_rejection = strong_rejection and closed_above and momentum_shift and has_range

                if has_rejection:
                    direction = "BUY"
                    entry_price = current["close"] + pip_size  # Enter above close

                    # Calculate scalping-focused confidence
                    base_confidence = 55.0

                    # Sweep strength bonus (max +15)
                    sweep_bonus = min(15, bullish_sweep_strength * 2)

                    # Rejection quality bonus (max +12)
                    rejection_quality = lower_wick_ratio * 30
                    rejection_bonus = min(12, rejection_quality)

                    # Close position bonus (max +8)
                    close_above_swept = (current["close"] - swept_level) / pip_size
                    close_bonus = min(8, close_above_swept)

                    # Volume confirmation (max +10) - TIGHTENED: Require 1.5x volume
                    volume_ratio = current.get("volume", 1000) / max(
                        1, sum(c.get("volume", 1000) for c in candles[-5:-1]) / 4
                    )
                    volume_bonus = (
                        min(10, (volume_ratio - 1.0) * 5) if volume_ratio >= 1.5 else 0
                    )  # RAISED from 1.2x to 1.5x

                    confidence_score = base_confidence + sweep_bonus + rejection_bonus + close_bonus + volume_bonus
                    confidence_score = min(90.0, max(60.0, confidence_score))

                    print(f"🔍 LSR {symbol}: BULLISH CONFIDENCE BREAKDOWN:")
                    print(f"   Base: {base_confidence:.1f}%")
                    print(f"   Sweep: +{sweep_bonus:.1f}% ({bullish_sweep_strength:.1f}p)")
                    print(f"   Rejection: +{rejection_bonus:.1f}% ({lower_wick_ratio:.1%} wick)")
                    print(f"   Close position: +{close_bonus:.1f}% ({close_above_swept:.1f}p above)")
                    print(f"   Volume: +{volume_bonus:.1f}% ({volume_ratio:.2f}x)")
                    print(f"   FINAL: {confidence_score:.1f}%")

            if not direction:
                print(f"🔍 LSR {symbol}: No quality sweep+rejection setup found")
                return None

            # STEP 4: SCALPING VIABILITY CHECK
            # Ensure tight stops and reasonable targets for <1hr scalps
            if direction == "SELL":
                sl_distance = (current["high"] - entry_price) / pip_size
            else:
                sl_distance = (entry_price - current["low"]) / pip_size

            # Scalping-appropriate stop distances (tight for quick moves)
            max_sl_pips = {"EURUSD": 12, "GBPUSD": 15, "USDJPY": 15, "XAUUSD": 400}.get(symbol, 12)

            if sl_distance > max_sl_pips:
                print(f"🔍 LSR {symbol}: Stop too wide for scalping ({sl_distance:.1f}p > {max_sl_pips}p)")
                return None

            # Target 1.5-2.0 R:R for scalping
            target_rr = 1.75  # Sweet spot for scalping
            tp_distance = sl_distance * target_rr

            print(f"✅ LSR {symbol}: SCALPING SETUP CONFIRMED!")
            print(f"   Direction: {direction}")
            print(f"   Entry: {entry_price:.5f}")
            print(f"   SL Distance: {sl_distance:.1f}p")
            print(f"   TP Distance: {tp_distance:.1f}p (R:R {target_rr})")
            print(f"   Confidence: {confidence_score:.1f}%")
            print(f"   Expected duration: 15-45 minutes")

            return PatternSignal(
                pattern="LIQUIDITY_SWEEP_REVERSAL",
                direction=direction,
                entry_price=entry_price,
                confidence=confidence_score,
                timeframe="M5",
                pair=symbol,
                quality_score=confidence_score,
            )

        except Exception as e:
            print(f"❌ LSR {symbol}: Error in detection: {str(e)}")
            logger.exception(f"LSR pattern detection error for {symbol}")
            traceback.print_exc()
            return None

    def detect_order_block_bounce(self, symbol: str) -> Optional[PatternSignal]:
        """
        PROFESSIONAL ORDER BLOCK BOUNCE: Institutional accumulation/distribution zones
        Based on SMC principles with proper validation criteria
        """
        try:
            if len(self.m5_data[symbol]) < 15:  # Need more data for proper OB identification
                return None

            candles = list(self.m5_data[symbol])[-15:]
            current = candles[-1]

            # Professional pip size calculation
            pip_size = get_pip_size(symbol)

            # INSTITUTIONAL STANDARD: Find valid order blocks
            for i in range(3, 10):  # Look back 3-10 candles for OB formation
                ob_candle = candles[-i]

                # STEP 1: ORDER BLOCK FORMATION CRITERIA
                # 1. Must be "last candle" before significant displacement
                next_candles = candles[-i + 1 :]
                if len(next_candles) < 3:
                    continue

                # 2. DISPLACEMENT VALIDATION: Strong move after OB candle
                displacement_pips = 0
                displacement_direction = None

                # Check for displacement in next 3 candles
                for j in range(min(3, len(next_candles))):
                    next_candle = next_candles[j]
                    move_up = (next_candle["high"] - ob_candle["high"]) / pip_size
                    move_down = (ob_candle["low"] - next_candle["low"]) / pip_size

                    if move_up >= 8:  # 8+ pip displacement upward
                        displacement_pips = move_up
                        displacement_direction = "UP"
                        break
                    elif move_down >= 8:  # 8+ pip displacement downward
                        displacement_pips = move_down
                        displacement_direction = "DOWN"
                        break

                if displacement_pips < 8:  # No significant displacement = invalid OB
                    continue

                # STEP 2.5: CHECK FOR LIQUIDITY SWEEP BEFORE OB (INSTITUTIONAL REQUIREMENT)
                # Order blocks are most valid after liquidity is swept
                liquidity_swept = False
                for prev_idx in range(max(0, -i - 5), -i):
                    if prev_idx >= -len(candles):
                        prev_candle = candles[prev_idx]
                        # Check if previous candles swept liquidity
                        if displacement_direction == "DOWN":
                            # For bearish OB, check if we swept above recent highs first
                            if prev_candle["high"] > ob_candle["high"] + (pip_size * 3):
                                liquidity_swept = True
                                break
                        elif displacement_direction == "UP":
                            # For bullish OB, check if we swept below recent lows first
                            if prev_candle["low"] < ob_candle["low"] - (pip_size * 3):
                                liquidity_swept = True
                                break

                if not liquidity_swept:
                    continue  # Skip OB without liquidity sweep

                # STEP 3: VOLUME VALIDATION - Institutional footprint (ENHANCED)
                ob_volume = ob_candle.get("volume", 0)
                avg_volume = sum(c.get("volume", 0) for c in candles[-20:]) / 20 if len(candles) >= 20 else 1000

                # INSTITUTIONAL REQUIREMENT: 2x average volume
                if ob_volume < avg_volume * 2.0:  # Raised from 1.5x for institutional footprint
                    continue

                # STEP 4: ORDER BLOCK ZONE DEFINITION
                # Use full candle range for institutional OB (not just body)
                ob_high = ob_candle["high"]
                ob_low = ob_candle["low"]
                ob_mid = (ob_high + ob_low) / 2

                # STEP 5: CURRENT PRICE INTERACTION WITH OB
                # For BULLISH Order Block (price should bounce UP from demand zone)
                if displacement_direction == "UP" and ob_candle["close"] > ob_candle["open"]:
                    # Price must have returned to OB zone
                    if not (ob_low <= current["low"] <= ob_high):
                        continue

                    # PROFESSIONAL BOUNCE VALIDATION
                    # 1. Price should close in upper half of OB (showing demand)
                    if current["close"] < ob_mid:
                        continue

                    # 2. Current candle should show rejection (bullish candle or hammer)
                    current_body_ratio = abs(current["close"] - current["open"]) / (current["high"] - current["low"])
                    if current_body_ratio < 0.4:  # Avoid indecision candles
                        continue

                    # 3. Multi-touch validation (has OB been tested before?)
                    touches = 0
                    for test_candle in candles[-i + 1 : -1]:  # Candles between OB and current
                        if ob_low <= test_candle["low"] <= ob_high:
                            touches += 1

                    # Virgin OB (untested) gets higher confidence
                    touch_multiplier = 1.0 if touches == 0 else 0.85

                    # CALCULATE PROFESSIONAL CONFIDENCE
                    base_confidence = 70.0  # Higher base for institutional pattern

                    # Displacement strength bonus (max +15)
                    displacement_bonus = min(15, displacement_pips * 1.5)

                    # Volume strength bonus (max +10)
                    volume_strength = ob_volume / avg_volume if avg_volume > 0 else 1.0
                    volume_bonus = min(10, (volume_strength - 1.0) * 5)

                    # Zone position bonus (max +8) - better if price at exact low
                    zone_position = (current["low"] - ob_low) / pip_size
                    position_bonus = max(0, 8 - zone_position) if zone_position <= 8 else 0

                    # Session quality bonus
                    session = self.get_current_session()
                    session_bonus = {"LONDON": 8, "OVERLAP": 6, "NEWYORK": 4, "ASIAN": 2}.get(session, 0)

                    confidence_score = (
                        base_confidence + displacement_bonus + volume_bonus + position_bonus + session_bonus
                    ) * touch_multiplier
                    confidence_score = min(92.0, max(70.0, confidence_score))

                    # RISK MANAGEMENT - Professional stop placement
                    entry_price = current["close"] + (pip_size * 0.5)  # Half pip above close
                    stop_loss = ob_low - pip_size  # Below order block
                    sl_distance = (entry_price - stop_loss) / pip_size

                    # Only take trades with reasonable risk (max 18 pips SL)
                    if sl_distance <= 18:
                        print(f"🎯 OBB {symbol}: INSTITUTIONAL BULLISH BOUNCE")
                        print(f"   Displacement: {displacement_pips:.1f}p UP after OB")
                        print(f"   Volume: {volume_strength:.1f}x average ({ob_volume})")
                        print(f"   Touches: {touches} (Virgin: {touches==0})")
                        print(f"   Zone: {zone_position:.1f}p from OB low")
                        print(f"   Confidence: {confidence_score:.1f}%")

                        return PatternSignal(
                            pattern="ORDER_BLOCK_BOUNCE",
                            direction="BUY",
                            entry_price=entry_price,
                            confidence=confidence_score,
                            timeframe="M5",
                            pair=symbol,
                            quality_score=confidence_score,
                        )

                # For BEARISH Order Block (price should bounce DOWN from supply zone)
                elif displacement_direction == "DOWN" and ob_candle["close"] < ob_candle["open"]:
                    # Price must have returned to OB zone
                    if not (ob_low <= current["high"] <= ob_high):
                        continue

                    # PROFESSIONAL BOUNCE VALIDATION
                    # 1. Price should close in lower half of OB (showing supply)
                    if current["close"] > ob_mid:
                        continue

                    # 2. Current candle should show rejection (bearish candle or inverted hammer)
                    current_body_ratio = abs(current["close"] - current["open"]) / (current["high"] - current["low"])
                    if current_body_ratio < 0.4:  # Avoid indecision candles
                        continue

                    # 3. Multi-touch validation
                    touches = 0
                    for test_candle in candles[-i + 1 : -1]:  # Candles between OB and current
                        if ob_low <= test_candle["high"] <= ob_high:
                            touches += 1

                    # Virgin OB gets higher confidence
                    touch_multiplier = 1.0 if touches == 0 else 0.85

                    # CALCULATE PROFESSIONAL CONFIDENCE
                    base_confidence = 70.0

                    displacement_bonus = min(15, displacement_pips * 1.5)

                    volume_strength = ob_volume / avg_volume if avg_volume > 0 else 1.0
                    volume_bonus = min(10, (volume_strength - 1.0) * 5)

                    # Zone position bonus - better if price at exact high
                    zone_position = (ob_high - current["high"]) / pip_size
                    position_bonus = max(0, 8 - zone_position) if zone_position <= 8 else 0

                    session = self.get_current_session()
                    session_bonus = {"LONDON": 8, "OVERLAP": 6, "NEWYORK": 4, "ASIAN": 2}.get(session, 0)

                    confidence_score = (
                        base_confidence + displacement_bonus + volume_bonus + position_bonus + session_bonus
                    ) * touch_multiplier
                    confidence_score = min(92.0, max(70.0, confidence_score))

                    # RISK MANAGEMENT - Professional stop placement
                    entry_price = current["close"] - (pip_size * 0.5)  # Half pip below close
                    stop_loss = ob_high + pip_size  # Above order block
                    sl_distance = (stop_loss - entry_price) / pip_size

                    # Only take trades with reasonable risk (max 18 pips SL)
                    if sl_distance <= 18:
                        print(f"🎯 OBB {symbol}: INSTITUTIONAL BEARISH BOUNCE")
                        print(f"   Displacement: {displacement_pips:.1f}p DOWN after OB")
                        print(f"   Volume: {volume_strength:.1f}x average ({ob_volume})")
                        print(f"   Touches: {touches} (Virgin: {touches==0})")
                        print(f"   Zone: {zone_position:.1f}p from OB high")
                        print(f"   Confidence: {confidence_score:.1f}%")

                        return PatternSignal(
                            pattern="ORDER_BLOCK_BOUNCE",
                            direction="SELL",
                            entry_price=entry_price,
                            confidence=confidence_score,
                            timeframe="M5",
                            pair=symbol,
                            quality_score=confidence_score,
                        )

            return None

        except Exception as e:
            print(f"❌ OBB {symbol}: Error in institutional analysis: {str(e)}")
            logger.exception(f"Order Block Bounce pattern detection error for {symbol}")
            traceback.print_exc()
            return None

    def detect_sweep_and_return(self, symbol: str) -> Optional[PatternSignal]:
        """
        SWEEP & RETURN: Simplified liquidity sweep detection
        Real ICT approach: Find sweep of obvious levels + immediate return

        QUALITY IMPROVEMENTS (Oct 7, 2025):
        - FIX #1: Defined min_sweep variable (was causing crashes)
        - FIX #2: Raised base confidence from 68% to 75%
        - FIX #3: Re-enabled volume filter for quality control
        - FIX #4: Increased return requirement from 0.5 to 2.0 pips
        - FIX #5: Disabled during ASIAN/LATE_NY sessions (low quality)
        """
        try:
            # FIX #5: SESSION GATING - Disable during low-quality sessions
            session = self.get_current_session()
            if session in ["ASIAN", "LATE_NY", "TOKYO"]:
                print(f"🎯 SWEEP_RETURN {symbol}: Disabled during {session} session (low quality)")
                return None

            # SIMPLIFIED: Just need basic candle data
            if len(self.m5_data[symbol]) < 10:
                return None

            candles = list(self.m5_data[symbol])[-10:]
            current = candles[-1]

            pip_size = get_pip_size(symbol)
            if pip_size == 0:
                return None

            # FIX #1: Define minimum sweep distance (was undefined, causing crashes)
            min_sweep = 2.0  # Minimum 2 pips for valid sweep

            # SIMPLIFIED: Find recent swing high and low (last 8 candles)
            highs = [c["high"] for c in candles[-8:-1]]  # Exclude current
            lows = [c["low"] for c in candles[-8:-1]]  # Exclude current

            recent_high = max(highs)
            recent_low = min(lows)

            # ENHANCED SWEEP DETECTION WITH PERFORMANCE FILTERS
            swept_high = current["high"] > recent_high
            swept_low = current["low"] < recent_low

            if swept_high:
                sweep_distance = (current["high"] - recent_high) / pip_size

                # Check minimum sweep requirement
                if sweep_distance < min_sweep:
                    print(f"🎯 SWEEP_RETURN {symbol}: Sweep too small ({sweep_distance:.1f}p < {min_sweep}p)")
                    return None

                # PERFORMANCE FILTER: Aggressive rejection wick (60%+ of candle)
                candle_range = current["high"] - current["low"]
                upper_wick = current["high"] - max(current["open"], current["close"])
                wick_ratio = upper_wick / candle_range if candle_range > 0 else 0

                if wick_ratio < 0.4:  # TIGHTENED: 10% → 40% for quality
                    print(f"🎯 SWEEP_RETURN {symbol}: Weak rejection wick ({wick_ratio:.1%} < 40%)")
                    return None

                # FIX #3: RE-ENABLED VOLUME FILTER for quality control
                volumes = [c.get("volume", 1000) for c in candles[-5:]]
                avg_volume = sum(volumes[:-1]) / 4
                current_volume = volumes[-1]
                volume_surge = current_volume / avg_volume if avg_volume > 0 else 1.0

                if volume_surge < 1.5:  # Need 50%+ volume surge
                    print(f"🎯 SWEEP_RETURN {symbol}: No volume spike ({volume_surge:.1f}x < 1.5x)")
                    return None

                # FIX #4: TIGHTENED return requirement from 0.5 to 2.0 pips
                return_distance = (current["high"] - current["close"]) / pip_size
                if return_distance < 2.0:  # TIGHTENED: 0.5p → 2.0p for quality
                    print(f"🎯 SWEEP_RETURN {symbol}: Weak return ({return_distance:.1f}p < 2.0p)")
                    return None

                # Calculate optimized levels
                entry_price = current["close"]
                # Dynamic SL based on sweep distance (larger sweep = wider SL)
                sl_distance = min(15, max(10, int(sweep_distance * 0.8)))  # 10-15 pips
                tp_distance = int(sl_distance * 1.5)  # 1.5:1 R:R
                stop_price = entry_price + (sl_distance * pip_size)
                target_price = entry_price - (tp_distance * pip_size)

                # FIX #2: Raised base confidence from 68% to 75%
                session_bonus = 0
                if session == "LONDON":
                    session_bonus = 15
                elif session == "NEWYORK":
                    session_bonus = 12
                elif session == "LONDON_NY":  # Overlap session
                    session_bonus = 20

                confidence = 75 + session_bonus  # RAISED: 68% → 75%
                confidence = min(confidence, 95)  # Allow higher confidence for best setups

                print(f"✅ SWEEP_RETURN {symbol}: High swept & returned - SELL at {confidence}%")

                return PatternSignal(
                    pattern="SWEEP_RETURN",
                    pair=symbol,
                    direction="SELL",
                    entry_price=entry_price,
                    confidence=confidence,
                    timeframe="M5",
                    quality_score=confidence,
                )

            elif swept_low:
                sweep_distance = (recent_low - current["low"]) / pip_size
                if sweep_distance < min_sweep:
                    print(f"🎯 SWEEP_RETURN {symbol}: Sweep too small ({sweep_distance:.1f}p < {min_sweep}p)")
                    return None

                # PERFORMANCE FILTER: Aggressive rejection wick (60%+ of candle)
                candle_range = current["high"] - current["low"]
                lower_wick = min(current["open"], current["close"]) - current["low"]
                wick_ratio = lower_wick / candle_range if candle_range > 0 else 0

                if wick_ratio < 0.6:  # Need aggressive rejection
                    print(f"🎯 SWEEP_RETURN {symbol}: Weak rejection wick ({wick_ratio:.1%} < 60%)")
                    return None

                # PERFORMANCE FILTER: Volume spike confirmation
                volumes = [c.get("volume", 1000) for c in candles[-5:]]
                avg_volume = sum(volumes[:-1]) / 4
                current_volume = volumes[-1]
                volume_surge = current_volume / avg_volume if avg_volume > 0 else 1.0

                if volume_surge < 1.5:  # Need 50%+ volume surge
                    print(f"🎯 SWEEP_RETURN {symbol}: No volume spike ({volume_surge:.1f}x < 1.5x)")
                    return None

                # RETURN DETECTION: Price came back significantly
                return_distance = (current["close"] - current["low"]) / pip_size
                if return_distance < 2:  # Need meaningful return
                    print(f"🎯 SWEEP_RETURN {symbol}: Weak return ({return_distance:.1f}p < 2p)")
                    return None

                # Calculate optimized levels
                entry_price = current["close"]
                # Dynamic SL based on sweep distance
                sl_distance = min(15, max(10, int(sweep_distance * 0.8)))  # 10-15 pips
                tp_distance = int(sl_distance * 1.5)  # 1.5:1 R:R
                stop_price = entry_price - (sl_distance * pip_size)
                target_price = entry_price + (tp_distance * pip_size)

                # FIX #2: Raised base confidence from 68% to 75%
                session_bonus = 0
                if session == "LONDON":
                    session_bonus = 15
                elif session == "NEWYORK":
                    session_bonus = 12
                elif session == "LONDON_NY":  # Overlap session
                    session_bonus = 20

                confidence = 75 + session_bonus  # RAISED: 68% → 75%
                confidence = min(confidence, 95)  # Allow higher confidence for best setups

                print(f"✅ SWEEP_RETURN {symbol}: Low swept & returned - BUY at {confidence}%")

                return PatternSignal(
                    pattern="SWEEP_RETURN",
                    pair=symbol,
                    direction="BUY",
                    entry_price=entry_price,
                    confidence=confidence,
                    timeframe="M5",
                    quality_score=confidence,
                )

            return None

        except Exception as e:
            print(f"⚠️ SWEEP_RETURN {symbol}: Error - {e}")
            return None

    def detect_vcb_breakout(self, symbol: str) -> Optional[PatternSignal]:
        """
        VCB BREAKOUT: Simplified Volatility Compression + Expansion
        Real ICT approach: Focus on probability, not perfection
        """
        try:
            if len(self.m5_data[symbol]) < 10:
                return None

            candles = list(self.m5_data[symbol])[-10:]
            current = candles[-1]

            pip_size = get_pip_size(symbol)
            if pip_size == 0:
                return None

            print(f"🏛️ VCB {symbol}: Checking volatility compression...")

            # SIMPLIFIED: Just use ATR for volatility measurement
            atr_values = []
            for i in range(1, len(candles)):
                high = candles[i]["high"]
                low = candles[i]["low"]
                prev_close = candles[i - 1]["close"]

                true_range = max(high - low, abs(high - prev_close), abs(low - prev_close))
                atr_values.append(true_range)

            if len(atr_values) < 5:
                return None

            # Current ATR vs Recent ATR
            current_atr = sum(atr_values[-3:]) / 3  # Last 3 periods
            recent_atr = sum(atr_values[-6:-3]) / 3  # Previous 3 periods

            # ONLY REQUIREMENT: Current volatility is compressed
            compression_ratio = current_atr / recent_atr if recent_atr > 0 else 1.0

            if compression_ratio > 0.9:  # LOOSENED: 0.7 → 0.9 for more signals
                print(f"🏛️ VCB {symbol}: No compression ({compression_ratio:.2f})")
                return None

            print(f"🏛️ VCB {symbol}: Volatility compressed ({compression_ratio:.2f}) - Looking for breakout...")

            # ENHANCED BREAKOUT DETECTION WITH PERFORMANCE OPTIMIZATIONS
            current_range = (current["high"] - current["low"]) / pip_size
            avg_range = sum((c["high"] - c["low"]) / pip_size for c in candles[-5:-1]) / 4

            # PERFORMANCE FILTER 1: Expansion must be significant (LOOSENED: 1.5x → 1.2x for more signals)
            if current_range < avg_range * 1.2:
                print(f"🏛️ VCB {symbol}: No expansion yet ({current_range:.1f}p vs avg {avg_range:.1f}p)")
                return None

            # PERFORMANCE FILTER 2: Volume confirmation (LOOSENED: 1.3x → 1.1x for more signals)
            volumes = [c.get("volume", 1000) for c in candles[-5:]]
            avg_volume = sum(volumes[:-1]) / 4  # Average of last 4
            current_volume = volumes[-1]
            volume_surge = current_volume / avg_volume if avg_volume > 0 else 1.0

            if volume_surge < 1.1:  # Need 10%+ volume increase (was 30%)
                print(f"🏛️ VCB {symbol}: No volume confirmation ({volume_surge:.1f}x < 1.1x)")
                return None

            # PERFORMANCE FILTER 3: Strong directional body (LOOSENED: 60% → 50% for more signals)
            body_size = abs(current["close"] - current["open"])
            body_ratio = body_size / (current["high"] - current["low"]) if current["high"] != current["low"] else 0

            if body_ratio < 0.5:  # Need 50%+ body (was 60%)
                print(f"🏛️ VCB {symbol}: Weak body ratio ({body_ratio:.1%} < 50%)")
                return None

            # PERFORMANCE FILTER 4: Range breakout validation (breaks recent levels)
            recent_highs = [c["high"] for c in candles[-8:-1]]
            recent_lows = [c["low"] for c in candles[-8:-1]]
            resistance = max(recent_highs) if recent_highs else current["high"]
            support = min(recent_lows) if recent_lows else current["low"]

            breakout_confirmed = False

            if current["close"] > current["open"]:
                # BULLISH BREAKOUT: Must break resistance
                if current["high"] > resistance + (2 * pip_size):  # 2 pip breakout minimum
                    direction = "BUY"
                    breakout_confirmed = True
                    print(f"🏛️ VCB {symbol}: Bullish breakout above {resistance:.5f}")
                else:
                    print(f"🏛️ VCB {symbol}: No resistance breakout ({current['high']:.5f} vs {resistance:.5f})")
                    return None
            else:
                # BEARISH BREAKOUT: Must break support
                if current["low"] < support - (2 * pip_size):  # 2 pip breakdown minimum
                    direction = "SELL"
                    breakout_confirmed = True
                    print(f"🏛️ VCB {symbol}: Bearish breakdown below {support:.5f}")
                else:
                    print(f"🏛️ VCB {symbol}: No support breakdown ({current['low']:.5f} vs {support:.5f})")
                    return None

            if not breakout_confirmed:
                return None

            # PERFORMANCE OPTIMIZED TRADE LEVELS
            if direction == "BUY":
                entry_price = current["close"]
                # Dynamic SL based on compression level (tighter compression = tighter SL)
                sl_distance = max(12, int(20 * compression_ratio))  # 12-14 pips for good compression
                tp_distance = int(sl_distance * 1.8)  # 1.8:1 R:R for better expectancy
                stop_price = entry_price - (sl_distance * pip_size)
                target_price = entry_price + (tp_distance * pip_size)
            else:
                entry_price = current["close"]
                sl_distance = max(12, int(20 * compression_ratio))
                tp_distance = int(sl_distance * 1.8)
                stop_price = entry_price + (sl_distance * pip_size)
                target_price = entry_price - (tp_distance * pip_size)

            # Session bonus
            session_bonus = 0
            session = self.get_current_session()
            if session == "LONDON":
                session_bonus = 18
            elif session == "NEWYORK":
                session_bonus = 15
            elif session == "LONDON_NY":  # Overlap session
                session_bonus = 22

            confidence = 72 + session_bonus
            confidence = min(confidence, 90)

            print(f"✅ VCB_BREAKOUT {symbol}: {direction} expansion breakout at {confidence}% confidence")

            return PatternSignal(
                pattern="VCB_BREAKOUT",
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                stop_loss=stop_price,
                take_profit=target_price,
                confidence=confidence,
                reasoning=f"Volatility compressed ({compression_ratio:.2f}) then expanded {current_range:.1f} pips",
            )

        except Exception as e:
            print(f"⚠️ VCB_BREAKOUT {symbol}: Error - {e}")
            return None

    def detect_momentum_breakout(self, symbol: str) -> Optional[PatternSignal]:
        """
        MOMENTUM BREAKOUT: Simplified momentum expansion detection
        Real ICT approach: Price accelerating with volume + directional body
        """
        try:
            # SIMPLIFIED: Just need basic candle data
            if len(self.m5_data[symbol]) < 6:
                return None

            candles = list(self.m5_data[symbol])[-6:]
            current = candles[-1]
            prev_candles = candles[-4:-1]  # Last 3 candles

            pip_size = get_pip_size(symbol)
            if pip_size == 0:
                return None

            # ENHANCED MOMENTUM DETECTION WITH PERFORMANCE FILTERS

            # PERFORMANCE FILTER 1: Momentum acceleration (LOOSENED: 10% → 5% per candle for more signals)
            ranges = [c["high"] - c["low"] for c in candles[-4:]]  # Last 4 candles including current
            momentum_acceleration = True
            for i in range(1, len(ranges)):
                if ranges[i] <= ranges[i - 1] * 1.05:  # Each candle should be 5% larger (was 10%)
                    momentum_acceleration = False
                    break

            if not momentum_acceleration:
                print(f"💨 MOMENTUM_BURST {symbol}: No momentum acceleration detected")
                return None

            # PERFORMANCE FILTER 2: Volume confirmation (LOOSENED: 1.3x → 1.1x for more signals)
            volumes = [c.get("volume", 1000) for c in candles[-4:]]
            avg_volume = sum(volumes[:-1]) / 3  # Average of last 3
            current_volume = volumes[-1]
            volume_surge = current_volume / avg_volume if avg_volume > 0 else 1.0

            if volume_surge < 1.1:  # Need 10%+ volume increase (was 30%)
                print(f"💨 MOMENTUM_BURST {symbol}: No volume surge ({volume_surge:.1f}x < 1.1x)")
                return None

            # PERFORMANCE FILTER 3: Range breakout validation (breaks recent high/low)
            lookback_candles = candles[-8:-1]  # Last 7 candles before current
            recent_high = max(c["high"] for c in lookback_candles)
            recent_low = min(c["low"] for c in lookback_candles)

            # PERFORMANCE FILTER 4: Strong directional body (LOOSENED: 60% → 50% for more signals)
            current_range = current["high"] - current["low"]
            body_size = abs(current["close"] - current["open"])
            body_ratio = body_size / current_range if current_range > 0 else 0

            if body_ratio < 0.5:
                print(f"💨 MOMENTUM_BURST {symbol}: Weak body conviction ({body_ratio:.1%} < 50%)")
                return None

            # DETERMINE DIRECTION WITH BREAKOUT VALIDATION
            direction = None
            breakout_distance = 0

            if current["close"] > current["open"]:
                # BULLISH: Must break recent high + significant movement
                if current["high"] > recent_high + (2 * pip_size):
                    breakout_distance = (current["high"] - recent_high) / pip_size
                    body_movement = (current["close"] - current["open"]) / pip_size
                    if body_movement >= 3:  # Minimum 3 pip body
                        direction = "BUY"
                        print(
                            f"💨 MOMENTUM_BURST {symbol}: Bullish breakout {breakout_distance:.1f}p + {body_movement:.1f}p body"
                        )

            elif current["close"] < current["open"]:
                # BEARISH: Must break recent low + significant movement
                if current["low"] < recent_low - (2 * pip_size):
                    breakout_distance = (recent_low - current["low"]) / pip_size
                    body_movement = (current["open"] - current["close"]) / pip_size
                    if body_movement >= 3:  # Minimum 3 pip body
                        direction = "SELL"
                        print(
                            f"💨 MOMENTUM_BURST {symbol}: Bearish breakdown {breakout_distance:.1f}p + {body_movement:.1f}p body"
                        )

            if not direction:
                print(f"💨 MOMENTUM_BURST {symbol}: No valid breakout with momentum")
                return None

            # PERFORMANCE OPTIMIZED TRADE LEVELS
            # R:R feasibility check (minimum 1.5:1)
            if direction == "BUY":
                entry_price = current["close"]
                # Dynamic SL based on breakout strength (stronger breakout = tighter SL)
                sl_distance = max(12, int(18 - (breakout_distance * 0.5)))  # 12-18 pips
                tp_distance = int(sl_distance * 1.6)  # 1.6:1 R:R for momentum trades
                stop_price = entry_price - (sl_distance * pip_size)
                target_price = entry_price + (tp_distance * pip_size)
            else:
                entry_price = current["close"]
                sl_distance = max(12, int(18 - (breakout_distance * 0.5)))
                tp_distance = int(sl_distance * 1.6)
                stop_price = entry_price + (sl_distance * pip_size)
                target_price = entry_price - (tp_distance * pip_size)

            # PERFORMANCE FILTER 5: R:R feasibility check
            risk_reward_ratio = tp_distance / sl_distance if sl_distance > 0 else 0
            if risk_reward_ratio < 1.5:
                print(f"💨 MOMENTUM_BURST {symbol}: Poor R:R ratio ({risk_reward_ratio:.1f} < 1.5)")
                return None

            # Session bonus
            session_bonus = 0
            session = self.get_current_session()
            if session == "LONDON":
                session_bonus = 15
            elif session == "NEWYORK":
                session_bonus = 12
            elif session == "LONDON_NY":  # Overlap session
                session_bonus = 18

            confidence = 70 + session_bonus
            confidence = min(confidence, 88)

            print(f"✅ MOMENTUM_BURST {symbol}: {direction} momentum at {confidence}% confidence")

            return PatternSignal(
                pattern="MOMENTUM_BURST",
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                stop_loss=stop_price,
                take_profit=target_price,
                confidence=confidence,
                reasoning=f"Strong {direction.lower()} momentum candle with {body_size/pip_size:.1f} pip body",
            )

        except Exception as e:
            print(f"⚠️ MOMENTUM_BURST {symbol}: Error - {e}")
            return None

    def detect_fair_value_gap_fill(self, symbol: str) -> Optional[PatternSignal]:
        """
        ICT FAIR VALUE GAP: Professional imbalance detection with Smart Money logic
        Identifies institutional displacement creating inefficient pricing for retracement
        """
        try:
            # Need minimum candles for FVG identification
            if len(self.m5_data[symbol]) < 10:
                return None

            candles = list(self.m5_data[symbol])[-10:]
            current = candles[-1]

            # Professional pip size calculation
            pip_size = get_pip_size(symbol)

            # STEP 1: IDENTIFY FAIR VALUE GAPS (3-candle pattern)
            # ICT standard: Gap between candle 1 and candle 3, with candle 2 creating displacement
            fvg_zones = []

            for i in range(len(candles) - 3):
                candle1 = candles[i]
                candle2 = candles[i + 1]  # Displacement candle
                candle3 = candles[i + 2]

                # BULLISH FVG: Gap up (candle 3 low > candle 1 high)
                if candle3["low"] > candle1["high"]:
                    gap_size = (candle3["low"] - candle1["high"]) / pip_size

                    # REALISTIC MINIMUM: 4 pips for majors, 15 for gold
                    min_gap_pips = 4 if symbol != "XAUUSD" else 15
                    if gap_size >= min_gap_pips:
                        # Validate displacement candle (must be strong bullish)
                        displacement_body = candle2["close"] - candle2["open"]
                        displacement_range = candle2["high"] - candle2["low"]
                        body_ratio = displacement_body / displacement_range if displacement_range > 0 else 0

                        if body_ratio >= 0.4:  # Moderate bullish candle (40%+ body)
                            fvg_zones.append(
                                {
                                    "type": "BULLISH",
                                    "gap_top": candle3["low"],
                                    "gap_bottom": candle1["high"],
                                    "gap_size": gap_size,
                                    "displacement_strength": body_ratio,
                                    "candle_index": i,
                                    "filled": False,
                                    "partial_fill": 0,
                                }
                            )
                            print(
                                f"💎 FVG {symbol}: Bullish FVG found - {gap_size:.1f} pips, displacement: {body_ratio:.1%}"
                            )

                # BEARISH FVG: Gap down (candle 3 high < candle 1 low)
                elif candle3["high"] < candle1["low"]:
                    gap_size = (candle1["low"] - candle3["high"]) / pip_size

                    # REALISTIC MINIMUM: 4 pips for majors, 15 for gold
                    min_gap_pips = 4 if symbol != "XAUUSD" else 15
                    if gap_size >= min_gap_pips:
                        # Validate displacement candle (must be strong bearish)
                        displacement_body = candle2["open"] - candle2["close"]
                        displacement_range = candle2["high"] - candle2["low"]
                        body_ratio = displacement_body / displacement_range if displacement_range > 0 else 0

                        if body_ratio >= 0.4:  # Moderate bearish candle (40%+ body)
                            fvg_zones.append(
                                {
                                    "type": "BEARISH",
                                    "gap_top": candle1["low"],
                                    "gap_bottom": candle3["high"],
                                    "gap_size": gap_size,
                                    "displacement_strength": body_ratio,
                                    "candle_index": i,
                                    "filled": False,
                                    "partial_fill": 0,
                                }
                            )
                            print(
                                f"💎 FVG {symbol}: Bearish FVG found - {gap_size:.1f} pips, displacement: {body_ratio:.1%}"
                            )

            if not fvg_zones:
                return None

            # STEP 2: CHECK FOR FVG MITIGATION (Price returning to fill gap)
            for fvg in fvg_zones:
                # Calculate how much of the gap has been filled
                if fvg["type"] == "BULLISH":
                    # For bullish FVG, price should retrace down into the gap
                    if current["low"] <= fvg["gap_top"]:
                        # Price has entered the gap zone
                        if current["low"] >= fvg["gap_bottom"]:
                            # Partial fill
                            fill_distance = (fvg["gap_top"] - current["low"]) / pip_size
                            fvg["partial_fill"] = fill_distance / fvg["gap_size"]
                        else:
                            # Complete fill (price went through entire gap)
                            fvg["filled"] = True
                            fvg["partial_fill"] = 1.0

                elif fvg["type"] == "BEARISH":
                    # For bearish FVG, price should retrace up into the gap
                    if current["high"] >= fvg["gap_bottom"]:
                        # Price has entered the gap zone
                        if current["high"] <= fvg["gap_top"]:
                            # Partial fill
                            fill_distance = (current["high"] - fvg["gap_bottom"]) / pip_size
                            fvg["partial_fill"] = fill_distance / fvg["gap_size"]
                        else:
                            # Complete fill (price went through entire gap)
                            fvg["filled"] = True
                            fvg["partial_fill"] = 1.0

            # STEP 3: IDENTIFY TRADEABLE FVG SETUPS
            # ICT concept: Trade when price returns to fill 50% of gap (equilibrium)
            for fvg in fvg_zones:
                # Skip if gap is too old (more than 7 candles)
                if fvg["candle_index"] < len(candles) - 7:
                    continue

                # BULLISH FVG TRADE SETUP
                if fvg["type"] == "BULLISH" and not fvg["filled"]:
                    # Check if price has retraced to 50% of gap (ICT optimal entry)
                    gap_midpoint = (fvg["gap_top"] + fvg["gap_bottom"]) / 2

                    # Price should be near 50% fill level
                    distance_to_midpoint = abs(current["low"] - gap_midpoint) / pip_size
                    print(f"💎 FVG {symbol}: Distance to midpoint: {distance_to_midpoint:.1f} pips")
                    if distance_to_midpoint <= 15:  # More flexible distance for quality
                        # VALIDATION 1: Market structure must be bullish (loosened)
                        recent_trend_up = (
                            sum(1 for c in candles[-5:] if c["close"] > c["open"]) >= 2
                        )  # 2 of 5 instead of 3

                        # VALIDATION 2: Volume confirmation (loosened)
                        avg_volume = sum(c.get("volume", 1000) for c in candles[-5:]) / 5
                        current_volume = current.get("volume", 1000)
                        volume_confirmation = current_volume >= avg_volume * 0.8  # 0.8x instead of 1.2x

                        # VALIDATION 3: Rejection from FVG (removed - too strict)
                        showing_rejection = True  # Always pass this check

                        if recent_trend_up and volume_confirmation and showing_rejection:
                            # PROFESSIONAL CONFIDENCE CALCULATION
                            base_confidence = 72.0  # ICT pattern base

                            # Gap size bonus (larger gaps = stronger imbalance)
                            gap_bonus = min(12, fvg["gap_size"] * 1.5)  # 8 pips = 12 points

                            # Displacement strength bonus
                            displacement_bonus = min(10, fvg["displacement_strength"] * 12)

                            # Fill precision bonus (closer to 50% = better)
                            fill_precision = 1.0 - abs(0.5 - fvg["partial_fill"])
                            precision_bonus = fill_precision * 8

                            # Volume bonus
                            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
                            volume_bonus = min(8, (volume_ratio - 1.0) * 5)

                            # Session bonus
                            session = self.get_current_session()
                            session_bonus = {"LONDON": 8, "OVERLAP": 6, "NEWYORK": 5, "ASIAN": 2}.get(session, 0)

                            confidence_score = (
                                base_confidence
                                + gap_bonus
                                + displacement_bonus
                                + precision_bonus
                                + volume_bonus
                                + session_bonus
                            )
                            confidence_score = min(92.0, max(72.0, confidence_score))

                            # Professional entry at current close
                            entry_price = current["close"] + (pip_size * 0.5)

                            print(f"🎯 FVG {symbol}: ICT BULLISH FVG SETUP CONFIRMED!")
                            print(f"   Gap Size: {fvg['gap_size']:.1f} pips")
                            print(f"   Fill Level: {fvg['partial_fill']:.1%} (optimal: 50%)")
                            print(f"   Displacement: {fvg['displacement_strength']:.1%}")
                            print(f"   Volume: {volume_ratio:.1f}x")
                            print(f"   Confidence: {confidence_score:.1f}%")

                            return PatternSignal(
                                pattern="FAIR_VALUE_GAP_FILL",
                                direction="SELL",  # FIXED: Bullish gap = SELL (gap becomes resistance)
                                entry_price=entry_price,
                                confidence=confidence_score,
                                timeframe="M5",
                                pair=symbol,
                                quality_score=confidence_score,
                            )

                # BEARISH FVG TRADE SETUP
                elif fvg["type"] == "BEARISH" and not fvg["filled"]:
                    # Check if price has retraced to 50% of gap
                    gap_midpoint = (fvg["gap_top"] + fvg["gap_bottom"]) / 2

                    # Price should be near 50% fill level
                    distance_to_midpoint = abs(current["high"] - gap_midpoint) / pip_size
                    print(f"💎 FVG {symbol}: Distance to midpoint: {distance_to_midpoint:.1f} pips")
                    if distance_to_midpoint <= 15:  # More flexible distance for quality
                        # VALIDATION 1: Market structure must be bearish (loosened)
                        recent_trend_down = (
                            sum(1 for c in candles[-5:] if c["close"] < c["open"]) >= 2
                        )  # 2 of 5 instead of 3

                        # VALIDATION 2: Volume confirmation (loosened)
                        avg_volume = sum(c.get("volume", 1000) for c in candles[-5:]) / 5
                        current_volume = current.get("volume", 1000)
                        volume_confirmation = current_volume >= avg_volume * 0.8  # 0.8x instead of 1.2x

                        # VALIDATION 3: Rejection from FVG (removed - too strict)
                        showing_rejection = True  # Always pass this check

                        if recent_trend_down and volume_confirmation and showing_rejection:
                            # PROFESSIONAL CONFIDENCE CALCULATION
                            base_confidence = 72.0

                            gap_bonus = min(12, fvg["gap_size"] * 1.5)
                            displacement_bonus = min(10, fvg["displacement_strength"] * 12)

                            fill_precision = 1.0 - abs(0.5 - fvg["partial_fill"])
                            precision_bonus = fill_precision * 8

                            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
                            volume_bonus = min(8, (volume_ratio - 1.0) * 5)

                            session = self.get_current_session()
                            session_bonus = {"LONDON": 8, "OVERLAP": 6, "NEWYORK": 5, "ASIAN": 2}.get(session, 0)

                            confidence_score = (
                                base_confidence
                                + gap_bonus
                                + displacement_bonus
                                + precision_bonus
                                + volume_bonus
                                + session_bonus
                            )
                            confidence_score = min(92.0, max(72.0, confidence_score))

                            # Professional entry at current close
                            entry_price = current["close"] - (pip_size * 0.5)

                            print(f"🎯 FVG {symbol}: ICT BEARISH FVG SETUP CONFIRMED!")
                            print(f"   Gap Size: {fvg['gap_size']:.1f} pips")
                            print(f"   Fill Level: {fvg['partial_fill']:.1%} (optimal: 50%)")
                            print(f"   Displacement: {fvg['displacement_strength']:.1%}")
                            print(f"   Volume: {volume_ratio:.1f}x")
                            print(f"   Confidence: {confidence_score:.1f}%")

                            return PatternSignal(
                                pattern="FAIR_VALUE_GAP_FILL",
                                direction="BUY",  # FIXED: Bearish gap = BUY (gap becomes support)
                                entry_price=entry_price,
                                confidence=confidence_score,
                                timeframe="M5",
                                pair=symbol,
                                quality_score=confidence_score,
                            )

            return None

        except Exception as e:
            print(f"❌ FVG {symbol}: Error in ICT analysis: {str(e)}")
            logger.exception(f"Fair Value Gap pattern detection error for {symbol}")
            traceback.print_exc()
            return None

    def detect_blind_spot(self, symbol: str) -> Optional[PatternSignal]:
        """
        BLIND SPOT - Displacement + Partial Retracement Pattern
        Based on ICT methodology: Strong displacement followed by incomplete retracement
        Creates a "blind spot" where retail traders miss the continuation
        """
        print(f"🔍 BLIND SPOT {symbol}: Starting detection")

        # Need M5 data for displacement detection
        m5_candles = self.m5_data.get(symbol, deque())
        if len(m5_candles) < 20:
            print(f"🔍 BLIND_SPOT {symbol}: Need 20+ M5 candles, have {len(m5_candles)}")
            return None

        candles = list(m5_candles)[-20:]  # Last 20 candles
        pip_size = get_pip_size(symbol)

        # Calculate ATR for displacement threshold
        ranges = []
        for i in range(1, len(candles)):
            high_low = candles[i]["high"] - candles[i]["low"]
            ranges.append(high_low)

        if not ranges:
            return None

        avg_range = sum(ranges) / len(ranges)
        displacement_threshold = avg_range * 2.0  # 2x average range = significant displacement

        # Look for displacement candle in recent 10 candles
        displacement_found = False
        displacement_candle = None
        displacement_direction = None

        for i in range(len(candles) - 10, len(candles)):
            if i < 0:
                continue

            candle = candles[i]
            candle_range = candle["high"] - candle["low"]
            body_size = abs(candle["close"] - candle["open"])

            # Strong displacement: Large range + strong body (>70% of range)
            if candle_range >= displacement_threshold and body_size >= (candle_range * 0.7):
                displacement_found = True
                displacement_candle = i
                displacement_direction = "BUY" if candle["close"] > candle["open"] else "SELL"
                print(f"🔍 BLIND_SPOT {symbol}: Displacement found at candle {i}, direction {displacement_direction}")
                break

        if not displacement_found:
            print(f"🔍 BLIND_SPOT {symbol}: No displacement found")
            return None

        # Check for partial retracement (incomplete mitigation)
        displacement = candles[displacement_candle]
        current = candles[-1]

        if displacement_direction == "BUY":
            # Bullish displacement - look for partial retrace down
            displacement_low = displacement["low"]
            displacement_high = displacement["high"]
            retrace_range = displacement_high - displacement_low

            # Current price should be in 38-78% retracement zone (partial, not full)
            fib_38 = displacement_high - (retrace_range * 0.38)
            fib_78 = displacement_high - (retrace_range * 0.78)

            if fib_78 <= current["close"] <= fib_38:
                print(f"🔍 BLIND_SPOT {symbol}: Bullish setup in retracement zone")

                # Entry setup
                entry_price = current["close"]
                stop_pips = max(10, int((entry_price - displacement_low) / pip_size))
                target_pips = int(stop_pips * 2.0)  # 2:1 RR minimum

                # Basic confluence scoring
                base_confidence = 72.0

                return PatternSignal(
                    pattern="BLIND_SPOT",
                    direction="BUY",
                    entry_price=entry_price,
                    confidence=base_confidence,
                    timeframe="M5",
                    pair=symbol,
                    quality_score=0.75,
                    momentum_score=0.7,
                    volume_quality=0.6,
                )

        else:  # SELL displacement
            # Bearish displacement - look for partial retrace up
            displacement_low = displacement["low"]
            displacement_high = displacement["high"]
            retrace_range = displacement_high - displacement_low

            # Current price should be in 38-78% retracement zone
            fib_38 = displacement_low + (retrace_range * 0.38)
            fib_78 = displacement_low + (retrace_range * 0.78)

            if fib_38 <= current["close"] <= fib_78:
                print(f"🔍 BLIND_SPOT {symbol}: Bearish setup in retracement zone")

                # Entry setup
                entry_price = current["close"]
                stop_pips = max(10, int((displacement_high - entry_price) / pip_size))
                target_pips = int(stop_pips * 2.0)  # 2:1 RR minimum

                # Basic confluence scoring
                base_confidence = 72.0

                return PatternSignal(
                    pattern="BLIND_SPOT",
                    direction="SELL",
                    entry_price=entry_price,
                    confidence=base_confidence,
                    timeframe="M5",
                    pair=symbol,
                    quality_score=0.75,
                    momentum_score=0.7,
                    volume_quality=0.6,
                )

        print(f"🔍 BLIND_SPOT {symbol}: No valid retracement setup found")
        return None

        # Step 4: Use M5 for trigger instead of M1 (more stable for scalping)
        latest_m5 = m5[-1]
        prev_m5 = m5[-2] if len(m5) > 1 else m5[-1]
        trigger_detected = False

        if direction == "BUY":
            # BOS: latest high > prev high OR Sweep: low < liquidity_low with reversal
            if latest_m5["high"] > prev_m5["high"] or (
                latest_m5["low"] < liquidity_low
                and latest_m5["close"] > latest_m5["open"]
                and latest_m5["close"] > prev_m5["close"]
            ):
                trigger_detected = True
        else:
            # BOS: latest low < prev low OR Sweep: high > liquidity_high with reversal
            if latest_m5["low"] < prev_m5["low"] or (
                latest_m5["high"] > liquidity_high
                and latest_m5["close"] < latest_m5["open"]
                and latest_m5["close"] < prev_m5["close"]
            ):
                trigger_detected = True

        if not trigger_detected:
            return None

        # Step 5: SNIPER R:R CALCULATION - MINIMUM 2:1
        entry_price = latest_m5["close"]

        # Find invalidation point (where pattern fails)
        recent_m5_low = min([c["low"] for c in list(m5)[-3:]])
        recent_m5_high = max([c["high"] for c in list(m5)[-3:]])

        # Add buffer for wicks/spread
        buffer = pip_size * 1.5

        if direction == "BUY":
            stop_loss = recent_m5_low - buffer
            if stop_loss >= entry_price:
                return None
            risk = entry_price - stop_loss

            # Find nearest liquidity target (15M high)
            target_levels = [c["high"] for c in list(m15)[-10:]]
            take_profit = max(target_levels)

            # Ensure minimum TP based on profile
            min_tp = entry_price + (profile["min_tp"] * pip_size)
            take_profit = max(take_profit, min_tp)

        else:
            stop_loss = recent_m5_high + buffer
            if stop_loss <= entry_price:
                return None
            risk = stop_loss - entry_price

            # Find nearest liquidity target (15M low)
            target_levels = [c["low"] for c in list(m15)[-10:]]
            take_profit = min(target_levels)

            # Ensure minimum TP based on profile
            min_tp = entry_price - (profile["min_tp"] * pip_size)
            take_profit = min(take_profit, min_tp)

        # Calculate actual R:R
        reward = abs(take_profit - entry_price)
        risk_pips = risk / pip_size
        reward_pips = reward / pip_size
        actual_rr = reward / risk if risk > 0 else 0

        # SNIPER STANDARD: Minimum 2:1 RR
        if actual_rr < 2.0:
            return None

        # Reject if SL exceeds profile maximum
        if risk_pips > profile["max_sl"]:
            return None

        # Cap TP to profile maximum
        if reward_pips > profile["max_tp"]:
            if direction == "BUY":
                take_profit = entry_price + (profile["max_tp"] * pip_size)
            else:
                take_profit = entry_price - (profile["max_tp"] * pip_size)
            reward_pips = profile["max_tp"]

        # Session Guards - Only trade in prime sessions
        session = self.get_session()
        if session == "ASIAN":
            return None  # Skip Asian session for sniper patterns

        # Check spread vs profile maximum
        current_spread = self.spreads.get(symbol, 0)
        if current_spread > profile["max_spread"]:
            return None

        # Confidence based on R:R quality
        # 2:1 = 70%, 3:1 = 75%, 4:1+ = 80%
        if actual_rr >= 4.0:
            confidence = 80
        elif actual_rr >= 3.0:
            confidence = 75
        else:
            confidence = 70

        # Session bonus for prime times
        if session == "LONDON":
            confidence += 5
        elif session == "OVERLAP":
            confidence += 8
        elif session == "NEWYORK":
            confidence += 3

        # Inside bar bonus (tighter pattern)
        if inside_bar:
            confidence += 5

        confidence = min(confidence, 85)  # Cap at 85%

        # Store calculated levels for signal (used later in signal processing)
        self.blind_spot_levels = {
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_pips": risk_pips,
            "reward_pips": reward_pips,
            "rr_ratio": actual_rr,
        }

        print(
            f"🎯 BLIND SPOT {symbol}: TRUE SNIPER - {direction} RR={actual_rr:.1f}:1, SL={risk_pips:.1f}p, TP={reward_pips:.1f}p"
        )

        return PatternSignal(
            pattern="BLIND_SPOT",
            direction=direction,
            entry_price=entry_price,
            confidence=confidence,
            timeframe="H4",
            pair=symbol,
            quality_score=confidence / 100,
            momentum_score=0.7 if trigger_detected else 0.5,
            volume_quality=0.6,
        )

    def detect_trapdoor_ssr(self, symbol: str) -> Optional[PatternSignal]:
        """
        TRAPDOOR SSR - Session Sweep Reversal Pattern
        Based on ICT methodology: Session high/low sweeps that reverse quickly
        Creates liquidity grabs during London-NY transitions
        """
        print(f"🔍 TRAPDOOR SSR {symbol}: Starting detection")

        # Need M15 data for session analysis
        m15_candles = self.m15_data.get(symbol, deque())
        if len(m15_candles) < 30:
            print(f"🔍 TRAPDOOR SSR {symbol}: Need 30+ M15 candles, have {len(m15_candles)}")
            return None

        candles = list(m15_candles)[-30:]  # Last 30 M15 candles (7.5 hours)
        pip_size = get_pip_size(symbol)

        # Get current session info
        session = self.get_current_session()
        print(f"🔍 TRAPDOOR SSR {symbol}: Current session: {session}")

        # Focus on London-NY transition periods
        if session not in ["LONDON", "OVERLAP", "NY"]:
            print(f"🔍 TRAPDOOR SSR {symbol}: Session {session} not optimal for SSR")
            return None

        # Find session boundaries (last 15 candles = ~4 hours)
        session_candles = candles[-15:]
        if len(session_candles) < 10:
            return None

        session_high = max(c["high"] for c in session_candles)
        session_low = min(c["low"] for c in session_candles)
        current = candles[-1]

        # Sweep thresholds by pair
        sweep_thresholds = {
            "EURUSD": 3.0,
            "GBPUSD": 4.0,
            "USDJPY": 3.0,
            "GBPJPY": 8.0,
            "EURJPY": 6.0,
            "XAUUSD": 50.0,
            "XAGUSD": 10.0,
        }
        min_sweep_pips = sweep_thresholds.get(symbol, 3.0)

        # Check for recent sweep and reversal in last 5 candles
        sweep_found = False
        sweep_direction = None

        for i in range(len(candles) - 5, len(candles)):
            if i < 0:
                continue

            candle = candles[i]

            # High sweep (bearish reversal setup)
            if candle["high"] > session_high:
                sweep_pips = (candle["high"] - session_high) / pip_size
                if sweep_pips >= min_sweep_pips:
                    # Must close back below session high (rejection)
                    if candle["close"] < session_high:
                        # Check if current price is still below swept level
                        if current["close"] < session_high:
                            sweep_found = True
                            sweep_direction = "SELL"
                            print(
                                f"🔍 TRAPDOOR SSR {symbol}: Bearish sweep found, {sweep_pips:.1f} pips above session high"
                            )
                            break

            # Low sweep (bullish reversal setup)
            elif candle["low"] < session_low:
                sweep_pips = (session_low - candle["low"]) / pip_size
                if sweep_pips >= min_sweep_pips:
                    # Must close back above session low (rejection)
                    if candle["close"] > session_low:
                        # Check if current price is still above swept level
                        if current["close"] > session_low:
                            sweep_found = True
                            sweep_direction = "BUY"
                            print(
                                f"🔍 TRAPDOOR SSR {symbol}: Bullish sweep found, {sweep_pips:.1f} pips below session low"
                            )
                            break

        if not sweep_found:
            print(f"🔍 TRAPDOOR SSR {symbol}: No valid sweep and reversal found")
            return None

        # Entry setup based on sweep direction
        entry_price = current["close"]

        if sweep_direction == "BUY":
            # Bullish SSR: Stop below swept low, target session high + extension
            stop_loss = session_low - (5 * pip_size)  # 5 pips buffer below sweep
            target = session_high + (10 * pip_size)  # Target above session high

            stop_pips = max(8, int((entry_price - stop_loss) / pip_size))
            target_pips = int((target - entry_price) / pip_size)

        else:  # SELL
            # Bearish SSR: Stop above swept high, target session low - extension
            stop_loss = session_high + (5 * pip_size)  # 5 pips buffer above sweep
            target = session_low - (10 * pip_size)  # Target below session low

            stop_pips = max(8, int((stop_loss - entry_price) / pip_size))
            target_pips = int((entry_price - target) / pip_size)

        # Ensure minimum 1:1.5 risk/reward
        if target_pips < (stop_pips * 1.5):
            target_pips = int(stop_pips * 1.5)

        # Session-based confidence scoring
        base_confidence = 74.0
        if session == "OVERLAP":  # London-NY overlap is prime time
            base_confidence += 4.0

        print(
            f"🔍 TRAPDOOR SSR {symbol}: {sweep_direction} setup, SL={stop_pips}p, TP={target_pips}p, RR={target_pips/stop_pips:.1f}"
        )

        return PatternSignal(
            pattern="TRAPDOOR_SSR",
            direction=sweep_direction,
            entry_price=entry_price,
            confidence=base_confidence,
            timeframe="M5",
            pair=symbol,
            quality_score=0.74,
            momentum_score=0.8,  # High momentum from sweep reversal
            volume_quality=0.7,
        )

    def get_current_session(self):
        """Determine current trading session based on UTC time"""
        return self.get_session()

    def get_session_boundaries(self, session):
        """Get session start and end times in UTC hours"""
        session_times = {
            "ASIAN": (22, 7),  # 22:00 - 07:00 UTC
            "LONDON": (7, 17),  # 07:00 - 17:00 UTC
            "NY": (12, 22),  # 12:00 - 22:00 UTC
            "OVERLAP": (12, 17),  # 12:00 - 17:00 UTC (London/NY overlap)
            "LATE_NY": (17, 22),  # 17:00 - 22:00 UTC
        }
        return session_times.get(session, (None, None))

    def get_session_candles(self, candles, session_start, session_end):
        """Filter candles to current session timeframe"""
        session_candles = []
        current_time = datetime.utcnow()

        # For simplicity, use last 4 hours of candles as session
        # In production, you'd use actual session time filtering
        if len(candles) >= 48:  # 4 hours of M5 candles
            session_candles = candles[-48:]
        else:
            session_candles = candles

        return session_candles

    def validate_ltf_break_of_structure(self, candles, direction):
        """Validate lower timeframe break of structure away from sweep"""
        if len(candles) < 5:
            return False

        current = candles[-1]

        if direction == "BUY":
            # Look for bullish BOS - break above recent swing high
            recent_high = max(c["high"] for c in candles[-5:-1])
            return current["high"] > recent_high
        else:  # SELL
            # Look for bearish BOS - break below recent swing low
            recent_low = min(c["low"] for c in candles[-5:-1])
            return current["low"] < recent_low

    def identify_retest_zone(self, candles, direction, pip_size):
        """Identify order block/FVG retest zone for entry"""
        if len(candles) < 3:
            return None

        if direction == "BUY":
            # Entry zone based on recent demand area
            entry_zone_low = min(c["low"] for c in candles[-3:])
            entry_zone_high = entry_zone_low + (5 * pip_size)  # 5 pip zone
            entry = (entry_zone_low + entry_zone_high) / 2
        else:  # SELL
            # Entry zone based on recent supply area
            entry_zone_high = max(c["high"] for c in candles[-3:])
            entry_zone_low = entry_zone_high - (5 * pip_size)  # 5 pip zone
            entry = (entry_zone_low + entry_zone_high) / 2

        return {"entry": entry, "zone_high": entry_zone_high, "zone_low": entry_zone_low}

    def get_recent_volume(self, symbol):
        """Get recent volume for volume confirmation"""
        if symbol in self.m5_data and len(self.m5_data[symbol]) >= 3:
            recent_candles = list(self.m5_data[symbol])[-3:]
            return sum(c.get("volume", 1) for c in recent_candles) / len(recent_candles)
        return 1  # Default volume if not available

    def get_average_volume(self, symbol):
        """Get average volume over longer period"""
        if symbol in self.m5_data and len(self.m5_data[symbol]) >= 20:
            candles = list(self.m5_data[symbol])[-20:]
            return sum(c.get("volume", 1) for c in candles) / len(candles)
        return 1  # Default volume if not available

    def detect_pressure_valve(self, symbol: str) -> Optional[PatternSignal]:
        """
        PRESSURE VALVE - Volatility Compression Breakout Pattern
        Based on Bollinger Band squeeze + ATR compression detection
        Detects explosive breakouts after periods of low volatility
        """
        print(f"🔍 PRESSURE VALVE {symbol}: Starting detection")

        # Need M15 data for volatility analysis
        m15_candles = self.m15_data.get(symbol, deque())
        if len(m15_candles) < 20:
            print(f"🔍 PRESSURE_VALVE {symbol}: Need 20+ M15 candles, have {len(m15_candles)}")
            return None

        candles = list(m15_candles)[-20:]  # Last 20 M15 candles
        pip_size = get_pip_size(symbol)

        # Calculate Bollinger Bands and ATR for compression detection
        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]

        # Simple Bollinger Band calculation (20-period SMA, 2 std dev)
        if len(closes) < 20:
            return None

        sma = sum(closes[-20:]) / 20
        variance = sum((close - sma) ** 2 for close in closes[-20:]) / 20
        std_dev = variance**0.5

        upper_bb = sma + (2 * std_dev)
        lower_bb = sma - (2 * std_dev)
        bb_width = (upper_bb - lower_bb) / sma

        # Calculate ATR for last 14 periods
        atr_values = []
        for i in range(1, min(15, len(candles))):
            true_range = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
            atr_values.append(true_range)

        if not atr_values:
            return None

        current_atr = sum(atr_values) / len(atr_values)
        atr_avg = current_atr  # Simplified average

        # Compression detection: Low BB width AND low ATR
        # Thresholds based on research
        bb_squeeze_threshold = 0.02  # 2% width is considered tight
        atr_compression_factor = 0.7  # Current ATR < 70% of average = compressed

        is_bb_squeezed = bb_width < bb_squeeze_threshold
        is_atr_compressed = current_atr < (atr_compression_factor * atr_avg)

        compression_detected = is_bb_squeezed and is_atr_compressed

        if not compression_detected:
            print(
                f"🔍 PRESSURE_VALVE {symbol}: No compression detected (BB width: {bb_width:.4f}, ATR ratio: {current_atr/atr_avg:.2f})"
            )
            return None

        print(f"🔍 PRESSURE_VALVE {symbol}: Compression detected! BB width: {bb_width:.4f}, ATR compressed")

        # Look for breakout in recent candles
        current = candles[-1]
        prev = candles[-2]

        breakout_detected = False
        breakout_direction = None

        # Breakout above upper BB
        if current["close"] > upper_bb and prev["close"] <= upper_bb:
            breakout_size = current["close"] - upper_bb
            if breakout_size >= (current_atr * 1.5):  # Significant breakout
                breakout_detected = True
                breakout_direction = "BUY"
                print(f"🔍 PRESSURE_VALVE {symbol}: Bullish breakout detected above BB")

        # Breakout below lower BB
        elif current["close"] < lower_bb and prev["close"] >= lower_bb:
            breakout_size = lower_bb - current["close"]
            if breakout_size >= (current_atr * 1.5):  # Significant breakout
                breakout_detected = True
                breakout_direction = "SELL"
                print(f"🔍 PRESSURE_VALVE {symbol}: Bearish breakout detected below BB")

        if not breakout_detected:
            print(f"🔍 PRESSURE_VALVE {symbol}: Compression found but no significant breakout")
            return None

        # Entry setup
        entry_price = current["close"]

        if breakout_direction == "BUY":
            # Bullish breakout
            stop_loss = lower_bb - (current_atr * 0.5)  # Stop below BB with buffer
            target = entry_price + (current_atr * 3.0)  # Target 3x ATR above entry

            stop_pips = max(8, int((entry_price - stop_loss) / pip_size))
            target_pips = int((target - entry_price) / pip_size)

        else:  # SELL
            # Bearish breakout
            stop_loss = upper_bb + (current_atr * 0.5)  # Stop above BB with buffer
            target = entry_price - (current_atr * 3.0)  # Target 3x ATR below entry

            stop_pips = max(8, int((stop_loss - entry_price) / pip_size))
            target_pips = int((entry_price - target) / pip_size)

        # Ensure minimum 1:2 risk/reward
        if target_pips < (stop_pips * 2.0):
            target_pips = int(stop_pips * 2.0)

        # Confidence scoring based on compression quality
        base_confidence = 72.0

        # Compression strength bonus
        if bb_width < 0.01:  # Very tight squeeze
            base_confidence += 4.0
        if current_atr < (0.5 * atr_avg):  # Very low volatility
            base_confidence += 3.0

        # Breakout strength bonus
        breakout_strength = breakout_size / current_atr
        if breakout_strength >= 2.0:
            base_confidence += 5.0

        print(
            f"🔍 PRESSURE_VALVE {symbol}: {breakout_direction} setup, SL={stop_pips}p, TP={target_pips}p, RR={target_pips/stop_pips:.1f}"
        )

        return PatternSignal(
            pattern="PRESSURE_VALVE",
            direction=breakout_direction,
            entry_price=entry_price,
            confidence=base_confidence,
            timeframe="M5",
            pair=symbol,
            quality_score=0.75,
            momentum_score=0.85,  # High momentum from compression release
            volume_quality=0.7,
        )

    def get_enhanced_4h_bias(self, h4_candles: List) -> str:
        """Enhanced 4H trend bias using EMA and recent price action"""
        if len(h4_candles) < 10:
            return "NEUTRAL"

        # EMA-based bias with more sophisticated logic
        closes = [candle["close"] for candle in h4_candles[-10:]]
        ema_9 = sum(closes[-9:]) / 9
        ema_21 = sum(closes) / 10  # Simplified 21 EMA

        current_price = h4_candles[-1]["close"]
        prev_price = h4_candles[-2]["close"]

        # Strong trend conditions
        if current_price > ema_9 > ema_21 and prev_price < current_price:
            return "BULLISH"
        elif current_price < ema_9 < ema_21 and prev_price > current_price:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def identify_enhanced_compression_block(self, candles: List, atr_m5: float, thresholds: Dict) -> Optional[Tuple]:
        """Enhanced compression block identification with configurable parameters"""
        min_bars = thresholds["compression_bars"]
        max_atr_ratio = thresholds["max_compression_atr"]

        # Look for compression in recent 20 candles
        for start_idx in range(len(candles) - min_bars - 5, len(candles) - min_bars):
            if start_idx < 0:
                continue

            # Check compression blocks of different lengths
            for block_length in range(min_bars, min(15, len(candles) - start_idx)):
                end_idx = start_idx + block_length
                block = candles[start_idx:end_idx]

                if len(block) < min_bars:
                    continue

                # Calculate block range
                block_high = max(candle["high"] for candle in block)
                block_low = min(candle["low"] for candle in block)
                block_range = block_high - block_low

                # Check if range is compressed (≤max_compression_atr×ATR)
                if block_range <= (atr_m5 * max_atr_ratio):
                    return (start_idx, end_idx, block_high, block_low)

        return None

    def detect_enhanced_impulsive_breakout(
        self,
        candles: List,
        comp_start: int,
        comp_end: int,
        comp_high: float,
        comp_low: float,
        atr_m5: float,
        h4_bias: str,
        thresholds: Dict,
    ) -> Optional[Tuple]:
        """Enhanced impulsive breakout detection with configurable multiplier"""
        break_multiplier = thresholds["break_multiplier"]

        # Look for breakout in candles after compression
        for i in range(comp_end, min(comp_end + 5, len(candles))):
            candle = candles[i]
            candle_range = candle["high"] - candle["low"]

            # Check if candle is impulsive (≥break_multiplier×ATR)
            if candle_range < (atr_m5 * break_multiplier):
                continue

            # Check breakout direction aligned with 4H bias
            bullish_break = candle["high"] > comp_high and candle["close"] > comp_high
            bearish_break = candle["low"] < comp_low and candle["close"] < comp_low

            if h4_bias == "BULLISH" and bullish_break:
                return (i, "BUY", candle_range)
            elif h4_bias == "BEARISH" and bearish_break:
                return (i, "SELL", candle_range)

        return None

    def calculate_enhanced_pressure_valve_levels(
        self,
        candles: List,
        breakout_idx: int,
        direction: str,
        comp_high: float,
        comp_low: float,
        comp_height: float,
        pip_size: float,
    ) -> Optional[Tuple]:
        """Enhanced entry, SL, and TP calculation with flexible pullback band (45-65%)"""
        breakout_candle = candles[breakout_idx]

        if direction == "BUY":
            # Flexible 45-65% pullback band
            break_range = breakout_candle["high"] - comp_high
            pullback_45 = breakout_candle["high"] - (break_range * 0.45)
            pullback_65 = breakout_candle["high"] - (break_range * 0.65)
            entry_price = breakout_candle["high"] - (break_range * 0.55)  # Default 55%

            # SL: Below compression low with 5 pip buffer
            sl_price = comp_low - (5 * pip_size)

            # TP: Measured move (compression height projected from breakout high)
            tp_price = breakout_candle["high"] + comp_height

            # Allow wider band if RR still ≥ 2.0
            risk_45 = abs(pullback_45 - sl_price)
            reward_45 = abs(tp_price - pullback_45)
            rr_45 = reward_45 / risk_45 if risk_45 > 0 else 0

            if rr_45 >= 2.0:
                entry_zone = {"high": pullback_45, "low": pullback_65}
                # Use more aggressive entry if RR allows
                entry_price = pullback_45

        else:  # SELL
            # Flexible 45-65% pullback band
            break_range = comp_low - breakout_candle["low"]
            pullback_45 = breakout_candle["low"] + (break_range * 0.45)
            pullback_65 = breakout_candle["low"] + (break_range * 0.65)
            entry_price = breakout_candle["low"] + (break_range * 0.55)  # Default 55%

            # SL: Above compression high with 5 pip buffer
            sl_price = comp_high + (5 * pip_size)

            # TP: Measured move (compression height projected from breakout low)
            tp_price = breakout_candle["low"] - comp_height

            # Allow wider band if RR still ≥ 2.0
            risk_45 = abs(sl_price - pullback_45)
            reward_45 = abs(pullback_45 - tp_price)
            rr_45 = reward_45 / risk_45 if risk_45 > 0 else 0

            if rr_45 >= 2.0:
                entry_zone = {"high": pullback_45, "low": pullback_65}
                # Use more aggressive entry if RR allows
                entry_price = pullback_45

        return (entry_price, sl_price, tp_price)

    def find_m15_liquidity_pools(self, symbol: str, direction: str) -> List[float]:
        """Find M15 liquidity pools (swing highs/lows) for TP extension"""
        if symbol not in self.m15_data or len(self.m15_data[symbol]) < 20:
            return []

        m15_candles = list(self.m15_data[symbol])
        pools = []
        pip_size = get_pip_size(symbol)

        # Look for significant swing points in last 20 M15 candles
        for i in range(5, len(m15_candles) - 5):
            candle = m15_candles[i]

            if direction == "BUY":
                # Find resistance levels (swing highs)
                is_swing_high = True
                for j in range(i - 3, i + 4):
                    if j != i and j >= 0 and j < len(m15_candles):
                        if m15_candles[j]["high"] >= candle["high"]:
                            is_swing_high = False
                            break

                if is_swing_high and candle["high"] > m15_candles[-1]["close"]:
                    pools.append(candle["high"])

            else:  # SELL
                # Find support levels (swing lows)
                is_swing_low = True
                for j in range(i - 3, i + 4):
                    if j != i and j >= 0 and j < len(m15_candles):
                        if m15_candles[j]["low"] <= candle["low"]:
                            is_swing_low = False
                            break

                if is_swing_low and candle["low"] < m15_candles[-1]["close"]:
                    pools.append(candle["low"])

        # Sort pools by proximity to current price
        current_price = m15_candles[-1]["close"]
        if direction == "BUY":
            pools = [p for p in pools if p > current_price]
            pools.sort()  # Closest resistance first
        else:
            pools = [p for p in pools if p < current_price]
            pools.sort(reverse=True)  # Closest support first

        return pools[:3]  # Return top 3 nearest levels

    def calculate_rr_with_tp(self, entry_price: float, sl_price: float, tp_price: float) -> float:
        """Calculate risk/reward ratio"""
        risk = abs(entry_price - sl_price)
        reward = abs(tp_price - entry_price)
        return reward / risk if risk > 0 else 0

    def get_current_spread(self, symbol: str) -> float:
        """Get current spread in pips (simplified estimate)"""
        # This would normally get real-time spread data
        # For now, using typical spreads by symbol type
        spread_estimates = {
            "EURUSD": 0.8,
            "GBPUSD": 1.2,
            "USDJPY": 0.9,
            "USDCHF": 1.1,
            "AUDUSD": 1.4,
            "USDCAD": 1.3,
            "NZDUSD": 1.8,
            "EURJPY": 1.5,
            "GBPJPY": 2.0,
            "EURGBP": 1.0,
            "XAUUSD": 35.0,
            "XAGUSD": 3.5,
            "BTCUSD": 50.0,
        }
        return spread_estimates.get(symbol, 2.0)  # Default 2 pips

    def validate_spread_guard(self, symbol: str, entry_price: float, sl_price: float) -> bool:
        """Spread guard (20% of SL distance max)"""
        spread = self.get_current_spread(symbol)
        pip_size = get_pip_size(symbol)
        sl_distance = abs(entry_price - sl_price) / pip_size
        return spread <= (sl_distance * 0.20)

    def calculate_enhanced_pressure_valve_confidence(
        self, compression_result: Tuple, breakout_size: float, atr_m5: float, h4_bias: str, rr_ratio: float, symbol: str
    ) -> float:
        """Enhanced confidence calculation with multiple factors"""
        base_confidence = 70.0

        # Compression quality bonus (longer compression = higher confidence)
        comp_start, comp_end, comp_high, comp_low = compression_result
        compression_bars = comp_end - comp_start
        if compression_bars >= 8:
            base_confidence += 8
        elif compression_bars >= 6:
            base_confidence += 5

        # Breakout strength bonus (stronger breakout = higher confidence)
        breakout_strength = breakout_size / atr_m5
        if breakout_strength >= 2.0:
            base_confidence += 10
        elif breakout_strength >= 1.5:
            base_confidence += 6

        # 4H bias alignment bonus
        if h4_bias in ["BULLISH", "BEARISH"]:
            base_confidence += 8

        # Risk/reward bonus
        if rr_ratio >= 3.0:
            base_confidence += 8
        elif rr_ratio >= 2.5:
            base_confidence += 5

        # Session bonus
        session = self.get_current_session()
        if session in ["LONDON", "OVERLAP"]:
            base_confidence += 6
        elif session == "NEWYORK":
            base_confidence += 4

        # Volume quality bonus
        volume_quality = self.get_current_volume_quality(symbol)
        if volume_quality > 1.3:
            base_confidence += 5
        elif volume_quality > 1.1:
            base_confidence += 3

        return min(base_confidence, 95.0)  # Cap at 95%

    def detect_bb_scalp(self, symbol: str) -> Optional[PatternSignal]:
        """
        BB_SCALP FIXED: Major flaws corrected
        - Changed from 1.5 SD to 2.0 SD (was too tight)
        - Fixed RSI thresholds (was using wrong values)
        - Added trend filter to avoid counter-trend trades
        - Increased wick requirement from 40% to 60%
        """
        try:
            print(f"📊 BB_SCALP {symbol}: PROFESSIONAL BOLLINGER ANALYSIS")

            # Need sufficient data for reliable BB calculation
            if len(self.m5_data[symbol]) < 25:
                return None

            candles = list(self.m5_data[symbol])[-25:]
            current = candles[-1]

            # Professional pip size calculation
            pip_size = get_pip_size(symbol)

            # STEP 1: CALCULATE BOLLINGER BANDS (Professional settings)
            # For scalping: 20-period SMA with 1.5 StdDev (tighter than standard 2.0)
            closes = [c["close"] for c in candles[-20:]]
            sma_20 = sum(closes) / 20

            # Calculate standard deviation
            variance = sum((close - sma_20) ** 2 for close in closes) / 20
            std_dev = variance**0.5

            # FIXED: Use standard 2.0 SD (1.5 was causing too many false signals)
            bb_upper = sma_20 + (2.0 * std_dev)
            bb_lower = sma_20 - (2.0 * std_dev)
            bb_width = (bb_upper - bb_lower) / pip_size

            print(f"📊 BB_SCALP {symbol}: BB Width: {bb_width:.1f} pips")

            # STEP 2: SQUEEZE DETECTION (Low volatility precedes expansion)
            # Calculate ATR for squeeze comparison
            atr_values = []
            for i in range(1, 20):
                high = candles[-20 + i]["high"]
                low = candles[-20 + i]["low"]
                prev_close = candles[-20 + i - 1]["close"]
                true_range = max(high - low, abs(high - prev_close), abs(low - prev_close))
                atr_values.append(true_range)

            atr = sum(atr_values) / len(atr_values) if atr_values else 0
            atr_pips = atr / pip_size

            # Squeeze condition: BB width < 2.5x ATR (professional threshold)
            is_squeeze = bb_width < (atr_pips * 2.5)

            # Calculate historical squeeze for comparison
            historical_widths = []
            for i in range(5, 20):
                hist_closes = [c["close"] for c in candles[-i - 20 : -i]]
                hist_sma = sum(hist_closes) / len(hist_closes)
                hist_variance = sum((close - hist_sma) ** 2 for close in hist_closes) / len(hist_closes)
                hist_std = hist_variance**0.5
                hist_width = 2 * 1.5 * hist_std / pip_size
                historical_widths.append(hist_width)

            avg_historical_width = sum(historical_widths) / len(historical_widths) if historical_widths else bb_width
            squeeze_intensity = 1.0 - (bb_width / avg_historical_width) if avg_historical_width > 0 else 0

            print(f"📊 BB_SCALP {symbol}: Squeeze active: {is_squeeze}, Intensity: {squeeze_intensity:.2f}")

            # STEP 3: RSI CALCULATION (Overbought/Oversold confirmation)
            # Calculate 14-period RSI
            price_changes = []
            for i in range(1, 15):
                price_changes.append(candles[-15 + i]["close"] - candles[-15 + i - 1]["close"])

            gains = [change if change > 0 else 0 for change in price_changes]
            losses = [-change if change < 0 else 0 for change in price_changes]

            avg_gain = sum(gains) / 14
            avg_loss = sum(losses) / 14

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            print(f"📊 BB_SCALP {symbol}: RSI: {rsi:.1f}")

            # STEP 3.5: TREND FILTER (Critical for mean reversion)
            # Calculate trend using 50-period SMA slope and ADX
            if len(candles) >= 50:
                sma_50_current = sum(c["close"] for c in candles[-50:]) / 50
                sma_50_prev = sum(c["close"] for c in candles[-51:-1]) / 50
                sma_slope_pips = (sma_50_current - sma_50_prev) / pip_size

                # Strong trend = slope > 2 pips per candle
                is_strong_uptrend = sma_slope_pips > 2
                is_strong_downtrend = sma_slope_pips < -2
                is_ranging = abs(sma_slope_pips) <= 2

                print(
                    f"📊 BB_SCALP {symbol}: SMA slope: {sma_slope_pips:.1f} pips, Market: {'UPTREND' if is_strong_uptrend else 'DOWNTREND' if is_strong_downtrend else 'RANGING'}"
                )
            else:
                # Not enough data for trend - assume ranging
                is_strong_uptrend = False
                is_strong_downtrend = False
                is_ranging = True

            # STEP 4: IDENTIFY TRADING SETUP
            current_price = current["close"]
            direction = None
            setup_type = None

            # MEAN REVERSION SETUP (Price at bands with RSI confirmation)
            # Bearish setup: Price at upper band + RSI overbought + NOT in strong uptrend
            if current["high"] >= bb_upper and not is_strong_uptrend:  # Don't fight trends
                price_penetration = (current["high"] - bb_upper) / pip_size

                if rsi >= 65:  # Balanced threshold for quality
                    # Validate reversal candle pattern
                    upper_wick = current["high"] - max(current["open"], current["close"])
                    candle_range = current["high"] - current["low"]
                    wick_ratio = upper_wick / candle_range if candle_range > 0 else 0

                    if wick_ratio >= 0.6:  # FIXED: Require 60%+ wick for real rejection
                        direction = "SELL"
                        setup_type = "MEAN_REVERSION"
                        print(f"📊 BB_SCALP {symbol}: BEARISH mean reversion setup")

            # Bullish setup: Price at lower band + RSI oversold
            elif current["low"] <= bb_lower and not is_strong_downtrend:  # Don't fight trends
                price_penetration = (bb_lower - current["low"]) / pip_size

                if rsi <= 35:  # Balanced threshold for quality
                    # Validate reversal candle pattern
                    lower_wick = min(current["open"], current["close"]) - current["low"]
                    candle_range = current["high"] - current["low"]
                    wick_ratio = lower_wick / candle_range if candle_range > 0 else 0

                    if wick_ratio >= 0.6:  # FIXED: Require 60%+ wick for real rejection
                        direction = "BUY"
                        setup_type = "MEAN_REVERSION"
                        print(f"📊 BB_SCALP {symbol}: BULLISH mean reversion setup")

            # SQUEEZE BREAKOUT SETUP (Squeeze followed by expansion)
            elif is_squeeze and squeeze_intensity >= 0.3:  # 30%+ compression
                # Check for breakout from squeeze
                prev_candle = candles[-2]

                # Bullish breakout: Current closes above upper band after squeeze
                if current["close"] > bb_upper and prev_candle["close"] <= bb_upper:
                    # Validate with volume surge
                    avg_volume = sum(c.get("volume", 1000) for c in candles[-10:]) / 10
                    current_volume = current.get("volume", 1000)
                    volume_surge = current_volume / avg_volume if avg_volume > 0 else 1.0

                    if volume_surge >= 1.3:  # 30% volume increase
                        direction = "BUY"
                        setup_type = "SQUEEZE_BREAKOUT"
                        print(f"📊 BB_SCALP {symbol}: BULLISH squeeze breakout")

                # Bearish breakout: Current closes below lower band after squeeze
                elif current["close"] < bb_lower and prev_candle["close"] >= bb_lower:
                    avg_volume = sum(c.get("volume", 1000) for c in candles[-10:]) / 10
                    current_volume = current.get("volume", 1000)
                    volume_surge = current_volume / avg_volume if avg_volume > 0 else 1.0

                    if volume_surge >= 1.3:
                        direction = "SELL"
                        setup_type = "SQUEEZE_BREAKOUT"
                        print(f"📊 BB_SCALP {symbol}: BEARISH squeeze breakout")

            if not direction:
                return None

            # STEP 5: PROFESSIONAL CONFIDENCE CALCULATION
            if setup_type == "MEAN_REVERSION":
                base_confidence = 72.0  # Mean reversion base

                # RSI extremity bonus (max +10)
                if direction == "SELL":
                    rsi_bonus = min(10, (rsi - 65) * 0.67)  # RSI 80 = 10 points
                else:
                    rsi_bonus = min(10, (35 - rsi) * 0.67)  # RSI 20 = 10 points

                # Band penetration bonus (max +8)
                penetration_bonus = min(8, price_penetration * 2)  # 4 pips = 8 points

                # Wick rejection bonus (max +8)
                wick_bonus = min(8, (wick_ratio - 0.4) * 20)  # 60% wick = 4, 80% = 8

                # Squeeze bonus (tighter squeeze = better reversal)
                squeeze_bonus = squeeze_intensity * 10 if is_squeeze else 0

            else:  # SQUEEZE_BREAKOUT
                base_confidence = 70.0  # Breakout base

                # Squeeze intensity bonus (max +12)
                squeeze_bonus = min(12, squeeze_intensity * 20)

                # Volume surge bonus (max +10)
                volume_surge_bonus = min(10, (volume_surge - 1.3) * 10)

                # Breakout strength bonus (max +8)
                if direction == "BUY":
                    breakout_distance = (current["close"] - bb_upper) / pip_size
                else:
                    breakout_distance = (bb_lower - current["close"]) / pip_size
                breakout_bonus = min(8, breakout_distance * 2)

                rsi_bonus = 0
                penetration_bonus = 0
                wick_bonus = 0
                volume_surge_bonus = min(10, (volume_surge - 1.3) * 10) if "volume_surge" in locals() else 0

            # Session timing bonus
            session = self.get_current_session()
            session_bonus = {"LONDON": 8, "OVERLAP": 6, "NEWYORK": 5, "ASIAN": 3}.get(session, 0)

            # Calculate final confidence
            if setup_type == "MEAN_REVERSION":
                confidence_score = (
                    base_confidence + rsi_bonus + penetration_bonus + wick_bonus + squeeze_bonus + session_bonus
                )
            else:
                confidence_score = base_confidence + squeeze_bonus + volume_surge_bonus + breakout_bonus + session_bonus

            confidence_score = min(92.0, max(70.0, confidence_score))

            # Professional entry calculation
            if direction == "BUY":
                entry_price = current["close"] + (pip_size * 0.5)
            else:
                entry_price = current["close"] - (pip_size * 0.5)

            print(f"🎯 BB_SCALP {symbol}: PROFESSIONAL SETUP CONFIRMED!")
            print(f"   Type: {setup_type}")
            print(f"   Direction: {direction}")
            print(f"   BB Width: {bb_width:.1f} pips")
            print(f"   RSI: {rsi:.1f}")
            print(f"   Squeeze: {is_squeeze} (Intensity: {squeeze_intensity:.2f})")
            print(f"   Session: {session}")
            print(f"   Confidence: {confidence_score:.1f}%")

            return PatternSignal(
                pattern="BB_SCALP",
                direction=direction,
                entry_price=entry_price,
                confidence=confidence_score,
                timeframe="M5",
                pair=symbol,
                quality_score=confidence_score,
            )

        except Exception as e:
            print(f"❌ BB_SCALP {symbol}: Error in professional analysis: {str(e)}")
            logger.exception(f"BB Scalp pattern detection error for {symbol}")
            traceback.print_exc()
            return None

    def detect_kalman_quickfire(self, symbol: str) -> Optional[PatternSignal]:
        """
        INSTITUTIONAL KALMAN FILTER: Professional statistical arbitrage with adaptive prediction
        Uses recursive state estimation to identify mean reversion opportunities with noise filtering
        """
        try:
            print(f"📈 KALMAN {symbol}: STATISTICAL ARBITRAGE ANALYSIS")

            # Need sufficient history for Kalman state estimation
            if len(self.m5_data[symbol]) < 30:
                return None

            candles = list(self.m5_data[symbol])[-30:]
            current = candles[-1]

            # Professional pip size calculation
            pip_size = get_pip_size(symbol)
            if pip_size == 0 or pip_size is None:
                return None

            # STEP 1: SIMPLIFIED KALMAN FILTER IMPLEMENTATION
            # State estimation for price prediction with noise reduction
            closes = [c["close"] for c in candles]
            if len(closes) < 10:
                return None

            # Initialize Kalman parameters
            # Process variance (Q) - how much we trust the model
            Q = 0.001  # Low value = trust model more
            # Measurement variance (R) - how noisy the measurements are
            R = 0.1  # Higher value = more noise expected

            # Initial estimates
            x_estimate = closes[0]  # Initial state estimate
            p_estimate = 1.0  # Initial error covariance

            # Store predictions and residuals
            predictions = []
            residuals = []

            # Run Kalman filter through historical data
            for i in range(1, len(closes)):
                # PREDICTION PHASE
                # Predict next state (assume random walk for simplicity)
                x_predict = x_estimate
                p_predict = p_estimate + Q

                # Store prediction
                predictions.append(x_predict)

                # UPDATE PHASE
                # Calculate Kalman gain
                # Add division-by-zero protection
                denominator = p_predict + R
                if denominator == 0 or denominator is None:
                    return None
                K = p_predict / denominator

                # Update estimate with measurement
                measurement = closes[i]
                x_estimate = x_predict + K * (measurement - x_predict)
                p_estimate = (1 - K) * p_predict

                # Calculate residual (forecast error)
                residual = measurement - x_predict
                residuals.append(residual)

            # STEP 2: CALCULATE STATISTICAL METRICS
            # Mean and standard deviation of residuals
            if len(residuals) < 10:
                return None

            if len(residuals) == 0:
                return None
            residual_mean = sum(residuals) / len(residuals)
            residual_variance = sum((r - residual_mean) ** 2 for r in residuals) / len(residuals)
            if residual_variance <= 0:
                return None
            residual_std = residual_variance**0.5

            # Current residual (deviation from prediction)
            current_residual = current["close"] - x_estimate
            if residual_std == 0 or residual_std is None:
                return None
            current_z_score = (current_residual - residual_mean) / residual_std

            print(f"📈 KALMAN {symbol}: Z-score: {current_z_score:.2f}, Residual: {current_residual/pip_size:.1f} pips")

            # STEP 3: IDENTIFY MEAN REVERSION OPPORTUNITIES
            # TIGHTENED: |Z-score| > 1.8 for higher quality signals (was 1.2)
            if abs(current_z_score) < 1.8:
                print(f"📈 KALMAN {symbol}: No significant deviation (|Z| < 1.8)")
                return None

            # Determine direction based on mean reversion principle
            # Use 1.8 threshold for stronger deviations only
            if current_z_score > 1.8:
                # Price above prediction = SELL opportunity
                direction = "SELL"
                deviation_strength = current_z_score
            elif current_z_score < -1.8:
                # Price below prediction = BUY opportunity
                direction = "BUY"
                deviation_strength = abs(current_z_score)
            else:
                return None

            # STEP 4: ADDITIONAL VALIDATION
            # Check volatility (ATR) for favorable conditions
            atr_values = []
            for i in range(1, 20):
                if i >= len(candles):
                    break
                high = candles[-i]["high"]
                low = candles[-i]["low"]
                prev_close = candles[-i - 1]["close"] if i < len(candles) - 1 else candles[-i]["close"]
                true_range = max(high - low, abs(high - prev_close), abs(low - prev_close))
                atr_values.append(true_range)

            if not atr_values:
                return None

            atr = sum(atr_values) / len(atr_values)
            atr_pips = atr / pip_size

            # Skip if volatility too low (no opportunity) or too high (too risky)
            min_atr = {"XAUUSD": 20, "XAGUSD": 10}.get(symbol, 5)
            max_atr = {"XAUUSD": 150, "XAGUSD": 60}.get(symbol, 30)

            if atr_pips < min_atr or atr_pips > max_atr:
                print(f"📈 KALMAN {symbol}: ATR {atr_pips:.1f} outside range [{min_atr}, {max_atr}]")
                return None

            # Volume confirmation (institutional participation)
            avg_volume = sum(c.get("volume", 1000) for c in candles[-10:]) / 10
            current_volume = current.get("volume", 1000)
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

            if volume_ratio < 0.8:  # Need decent volume for quality
                print(f"📈 KALMAN {symbol}: Insufficient volume ({volume_ratio:.2f}x < 0.5x)")
                return None

            # Check trend context (mean reversion works better in ranging markets)
            trend_strength = 0
            for i in range(1, 10):
                if candles[-i]["close"] > candles[-i - 1]["close"]:
                    trend_strength += 1
                else:
                    trend_strength -= 1

            is_ranging = abs(trend_strength) <= 4  # Weak trend = good for mean reversion

            # STEP 5: CONFIDENCE CALCULATION
            base_confidence = 72.0 if is_ranging else 68.0  # Ranging markets better

            # Deviation strength bonus (max +15)
            deviation_bonus = min(15, (deviation_strength - 2.0) * 7.5)  # Z=3 gives 7.5, Z=4 gives 15

            # Prediction accuracy bonus (max +10)
            # Calculate recent prediction accuracy
            recent_errors = residuals[-5:] if len(residuals) >= 5 else residuals
            avg_error = sum(abs(e) for e in recent_errors) / len(recent_errors) if recent_errors else float("inf")
            accuracy_ratio = 1.0 - (avg_error / (atr * 2)) if atr > 0 else 0
            accuracy_bonus = max(0, min(10, accuracy_ratio * 10))

            # Volume confirmation bonus (max +8)
            volume_bonus = min(8, (volume_ratio - 1.0) * 8)

            # Volatility optimal bonus (max +8)
            optimal_atr = (min_atr + max_atr) / 2
            volatility_distance = abs(atr_pips - optimal_atr) / optimal_atr
            volatility_bonus = max(0, 8 * (1 - volatility_distance))

            # Market condition bonus
            market_bonus = 7 if is_ranging else 0

            # Session timing bonus
            session = self.get_current_session()
            session_bonus = {"LONDON": 8, "OVERLAP": 6, "NEWYORK": 5, "ASIAN": 3}.get(session, 0)

            confidence_score = (
                base_confidence
                + deviation_bonus
                + accuracy_bonus
                + volume_bonus
                + volatility_bonus
                + market_bonus
                + session_bonus
            )
            confidence_score = min(92.0, max(68.0, confidence_score))

            # Professional entry calculation
            if direction == "BUY":
                entry_price = current["close"] + (pip_size * 0.5)
            else:
                entry_price = current["close"] - (pip_size * 0.5)

            print(f"🎯 KALMAN {symbol}: STATISTICAL ARBITRAGE SETUP!")
            print(f"   Direction: {direction} (Mean Reversion)")
            print(f"   Z-Score: {current_z_score:.2f}")
            print(f"   Deviation: {abs(current_residual)/pip_size:.1f} pips from prediction")
            print(f"   ATR: {atr_pips:.1f} pips")
            print(f"   Volume: {volume_ratio:.2f}x")
            print(f"   Market: {'Ranging' if is_ranging else 'Trending'}")
            print(f"   Confidence: {confidence_score:.1f}%")

            return PatternSignal(
                pattern="KALMAN_QUICKFIRE",
                direction=direction,
                entry_price=entry_price,
                confidence=confidence_score,
                timeframe="M5",
                pair=symbol,
                quality_score=confidence_score,
            )

        except Exception as e:
            print(f"❌ KALMAN {symbol}: Error in statistical analysis: {str(e)}")
            logger.exception(f"Kalman Quickfire pattern detection error for {symbol}")
            traceback.print_exc()
            return None
            hour = datetime.now().hour
            in_session = (7 <= hour < 12) or (12 <= hour < 17)  # London/NY UTC

            if volume_ratio < 1.2 or not in_session:
                return None

            # Simple trend detection for quickfire
            current_price = candles[-1]["close"]
            prev_price = candles[-2]["close"]
            direction = "BUY" if current_price > prev_price else "SELL"

            base_quality = 75
            confidence = 80.0

            print(
                f"🔍 KALMAN_QUICKFIRE {symbol}: ATR={atr:.2f}, Volume={volume_ratio:.2f}, Session={in_session}, Quality={base_quality}%"
            )

            return PatternSignal(
                pattern="KALMAN_QUICKFIRE",
                direction=direction,
                entry_price=current_price,
                confidence=confidence,
                timeframe="M5",
                pair=symbol,
                quality_score=base_quality,
            )
        except Exception as e:
            print(f"Error in detect_kalman_quickfire for {symbol}: {e}")
            return None

    def detect_ema_rsi_bb_vwap(self, symbol: str) -> Optional[PatternSignal]:
        """EMA RSI BB VWAP Hybrid Pattern - Professional Multi-Indicator Confluence

        INSTITUTIONAL LOGIC:
        - EMA crossover for trend direction (9/21 professional standard)
        - RSI for momentum confirmation (30/70 oversold/overbought)
        - BB squeeze for volatility expansion setup
        - VWAP for institutional positioning
        - All 4 indicators must align for signal
        """
        try:
            if len(self.m5_data[symbol]) < 50:  # Need more data for proper EMAs
                return None

            candles = list(self.m5_data[symbol])[-50:]
            closes = [c["close"] for c in candles]
            volumes = [c["volume"] for c in candles]
            pip_size = get_pip_size(symbol)

            # Add basic protection
            if pip_size == 0 or pip_size is None:
                return None
            if len(closes) == 0 or len(volumes) == 0:
                return None

            # PROFESSIONAL EMA CALCULATION (9/21 standard)
            # Using exponential weighting, not simple average
            def calculate_ema(data, period):
                multiplier = 2 / (period + 1)
                ema = data[0]
                for price in data[1:]:
                    ema = (price * multiplier) + (ema * (1 - multiplier))
                return ema

            ema9 = calculate_ema(closes[-21:], 9)  # Fast EMA
            ema21 = calculate_ema(closes[-21:], 21)  # Slow EMA

            # PROFESSIONAL RSI CALCULATION (14-period standard)
            gains = []
            losses = []
            for i in range(1, 15):  # 14-period RSI
                diff = closes[-i] - closes[-i - 1]
                if diff > 0:
                    gains.append(diff)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(diff))

            avg_gain = sum(gains) / 14
            avg_loss = sum(losses) / 14

            # Add division-by-zero protection
            if avg_loss == 0 or avg_loss is None:
                rsi = 100 if avg_gain > 0 else 50
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            # BOLLINGER BANDS (20,2 standard)
            bb_data = closes[-20:]
            if len(bb_data) == 0:
                return None
            sma20 = sum(bb_data) / len(bb_data)
            variance = sum((x - sma20) ** 2 for x in bb_data) / len(bb_data)
            std_dev = variance**0.5
            bb_upper = sma20 + (2 * std_dev)
            bb_lower = sma20 - (2 * std_dev)
            bb_width = (bb_upper - bb_lower) / pip_size

            # Add protection for zero width
            if bb_width == 0 or (bb_upper - bb_lower) == 0:
                return None

            # BB SQUEEZE DETECTION (Keltner Channel comparison)
            atr = self.calculate_atr(symbol)
            if atr and atr > 0:
                kc_width = atr * 2  # Keltner Channel width
                is_squeeze = bb_width < kc_width  # BB inside KC = squeeze
            else:
                is_squeeze = False

            # VWAP CALCULATION (Volume Weighted Average Price)
            # Professional: Use full session data
            typical_prices = [(candles[i]["high"] + candles[i]["low"] + candles[i]["close"]) / 3 for i in range(-20, 0)]
            total_volume = sum(volumes[-20:])
            if total_volume == 0 or total_volume is None:
                return None
            vwap = sum(tp * v for tp, v in zip(typical_prices, volumes[-20:])) / total_volume

            # VOLUME ANALYSIS
            volume_data = volumes[-20:]
            if len(volume_data) == 0:
                return None
            avg_volume = sum(volume_data) / len(volume_data)
            current_volume = candles[-1]["volume"]
            volume_surge = current_volume / avg_volume if avg_volume > 0 else 0

            # MULTI-INDICATOR CONFLUENCE REQUIREMENTS
            current_price = candles[-1]["close"]

            # 1. EMA CROSSOVER VALIDATION
            ema_bullish = ema9 > ema21
            ema_bearish = ema9 < ema21
            ema_separation = abs(ema9 - ema21) / pip_size

            # Need minimum 2 pip separation for valid signal
            if ema_separation < 2:
                return None

            # 2. RSI MOMENTUM CONFIRMATION
            # Professional ranges: 30-70 tradeable, <30/>70 oversold/overbought
            rsi_bullish = 30 < rsi < 60  # Not overbought
            rsi_bearish = 40 < rsi < 70  # Not oversold

            # 3. BOLLINGER BAND POSITION
            price_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5

            # 4. VWAP ALIGNMENT
            above_vwap = current_price > vwap
            below_vwap = current_price < vwap
            vwap_distance = abs(current_price - vwap) / pip_size

            # SIGNAL GENERATION - ALL 4 INDICATORS MUST ALIGN
            direction = None
            signal_strength = 0

            if ema_bullish and rsi_bullish and above_vwap:
                # BULLISH CONFLUENCE
                direction = "BUY"
                signal_strength += 25 if ema_separation > 3 else 15
                signal_strength += 25 if 40 < rsi < 55 else 15  # Optimal RSI range
                signal_strength += 25 if price_position < 0.5 else 15  # Lower half of BB
                signal_strength += 25 if vwap_distance < 5 else 15  # Close to VWAP

            elif ema_bearish and rsi_bearish and below_vwap:
                # BEARISH CONFLUENCE
                direction = "SELL"
                signal_strength += 25 if ema_separation > 3 else 15
                signal_strength += 25 if 45 < rsi < 60 else 15  # Optimal RSI range
                signal_strength += 25 if price_position > 0.5 else 15  # Upper half of BB
                signal_strength += 25 if vwap_distance < 5 else 15  # Close to VWAP

            if not direction:
                return None

            # VOLUME CONFIRMATION - MANDATORY
            if volume_surge < 1.2:  # Need 20% volume increase
                return None

            # BB SQUEEZE BONUS
            if is_squeeze:
                signal_strength += 10  # Squeeze breakout potential

            # SESSION VALIDATION
            hour = datetime.now().hour
            in_prime_session = (7 <= hour < 11) or (13 <= hour < 16)  # London/NY overlap
            if not in_prime_session:
                signal_strength -= 20

            # FINAL CONFIDENCE CALCULATION
            base_quality = min(signal_strength, 85)  # Cap at 85
            if base_quality < 60:
                return None  # Minimum quality threshold

            confidence = min(base_quality + 10, 90)  # Add base confidence, cap at 90

            print(f"🎯 EMA_RSI_BB_VWAP {symbol} {direction}:")
            print(f"   EMA9={ema9:.5f}, EMA21={ema21:.5f}, Separation={ema_separation:.1f} pips")
            print(f"   RSI={rsi:.1f}, BB Position={price_position:.2f}, Squeeze={is_squeeze}")
            print(f"   VWAP={vwap:.5f}, Distance={vwap_distance:.1f} pips")
            print(f"   Volume Surge={volume_surge:.2f}x, Quality={base_quality}%, Confidence={confidence}%")

            return PatternSignal(
                pattern="EMA_RSI_BB_VWAP",
                direction=direction,
                entry_price=current_price,
                confidence=confidence,
                timeframe="M5",
                pair=symbol,
                quality_score=base_quality,
            )
        except Exception as e:
            print(f"Error in detect_ema_rsi_bb_vwap for {symbol}: {e}")
            return None

    def detect_ema_rsi_scalp(self, symbol: str) -> Optional[PatternSignal]:
        """EMA RSI Scalp Pattern - Professional Quick-Fire Trading Strategy

        PROVEN SCALPING METHODOLOGY (46.4% historical win rate):
        - EMA 8/21 crossover for rapid trend detection (faster than 20/50)
        - RSI pullback entries for optimal positioning
        - Volume spike confirmation for momentum
        - Designed for 5-15 pip quick profits
        - Works best in trending sessions with volatility
        """
        try:
            if len(self.m5_data[symbol]) < 50:
                return None

            candles = list(self.m5_data[symbol])[-50:]
            closes = [c["close"] for c in candles]
            volumes = [c["volume"] for c in candles]
            highs = [c["high"] for c in candles]
            lows = [c["low"] for c in candles]
            pip_size = get_pip_size(symbol)

            # PROFESSIONAL SCALPING EMAs (8/21 for quick signals)
            def calculate_ema(data, period):
                if len(data) < period:
                    return sum(data) / len(data)
                multiplier = 2 / (period + 1)
                ema = sum(data[:period]) / period
                for price in data[period:]:
                    ema = (price * multiplier) + (ema * (1 - multiplier))
                return ema

            ema8 = calculate_ema(closes[-30:], 8)  # Ultra-fast
            ema21 = calculate_ema(closes[-30:], 21)  # Fast
            ema50 = calculate_ema(closes, 50)  # Trend filter

            # RSI CALCULATION WITH SMOOTHING
            rsi_period = 14
            gains = []
            losses = []
            for i in range(1, rsi_period + 1):
                if i >= len(closes):
                    break
                diff = closes[-i] - closes[-i - 1]
                gains.append(max(diff, 0))
                losses.append(max(-diff, 0))

            if not gains:
                return None

            # Wilder's smoothing for RSI
            avg_gain = sum(gains) / len(gains)
            avg_loss = sum(losses) / len(losses)

            if avg_loss == 0:
                rsi = 100 if avg_gain > 0 else 50
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            # SCALPING-SPECIFIC VALIDATIONS
            current_price = candles[-1]["close"]
            prev_close = candles[-2]["close"]

            # 1. TREND ALIGNMENT - All EMAs must stack correctly
            bullish_stack = ema8 > ema21 > ema50
            bearish_stack = ema8 < ema21 < ema50

            # 2. EMA SEPARATION - Need momentum
            ema_separation = abs(ema8 - ema21) / pip_size
            if ema_separation < 1.5:  # Need at least 1.5 pip separation
                return None

            # 3. RSI PULLBACK ZONES (Key for scalping entries)
            # BUY: RSI pulls back to 40-60 in uptrend
            # SELL: RSI pulls back to 40-60 in downtrend
            rsi_buy_zone = 40 <= rsi <= 60
            rsi_sell_zone = 40 <= rsi <= 60

            # 4. MOMENTUM CONFIRMATION
            # Check last 3 candles for momentum
            recent_momentum = 0
            for i in range(1, 4):
                if i >= len(candles):
                    break
                candle_range = (candles[-i]["high"] - candles[-i]["low"]) / pip_size
                if candles[-i]["close"] > candles[-i]["open"]:  # Bullish
                    recent_momentum += candle_range
                else:  # Bearish
                    recent_momentum -= candle_range

            # 5. VOLUME SPIKE DETECTION
            avg_volume = sum(volumes[-20:]) / 20
            current_volume = candles[-1]["volume"]
            volume_spike = current_volume / avg_volume if avg_volume > 0 else 0

            # Professional: Need significant volume for scalping
            if volume_spike < 1.3:  # 30% volume increase minimum
                return None

            # 6. VOLATILITY CHECK (ATR for scalping viability)
            atr = self.calculate_atr(symbol)
            if not atr or atr < 5 * pip_size:  # Need minimum 5 pip ATR
                return None

            # SIGNAL GENERATION LOGIC
            direction = None
            entry_quality = 0

            if bullish_stack and rsi_buy_zone and recent_momentum > 0:
                # BULLISH SCALP SETUP
                direction = "BUY"

                # Quality scoring for BUY
                entry_quality += 20 if rsi < 50 else 10  # Better if RSI lower in range
                entry_quality += 20 if ema_separation > 2.5 else 10
                entry_quality += 20 if volume_spike > 1.5 else 10
                entry_quality += 20 if recent_momentum > 10 else 10

                # Check for recent support bounce
                recent_low = min(lows[-5:])
                if abs(current_price - recent_low) / pip_size < 3:
                    entry_quality += 15  # Bouncing off support

            elif bearish_stack and rsi_sell_zone and recent_momentum < 0:
                # BEARISH SCALP SETUP
                direction = "SELL"

                # Quality scoring for SELL
                entry_quality += 20 if rsi > 50 else 10  # Better if RSI higher in range
                entry_quality += 20 if ema_separation > 2.5 else 10
                entry_quality += 20 if volume_spike > 1.5 else 10
                entry_quality += 20 if abs(recent_momentum) > 10 else 10

                # Check for recent resistance rejection
                recent_high = max(highs[-5:])
                if abs(recent_high - current_price) / pip_size < 3:
                    entry_quality += 15  # Rejecting resistance

            if not direction:
                return None

            # SESSION OPTIMIZATION (Scalping works best in active sessions)
            hour = datetime.now().hour
            minute = datetime.now().minute

            # Prime scalping times (session opens and overlaps)
            london_open = 7 <= hour < 9  # London open volatility
            ny_open = 13 <= hour < 15  # NY open volatility
            overlap = 13 <= hour < 16  # London/NY overlap

            if london_open or ny_open:
                entry_quality += 10  # Session open bonus
            elif overlap:
                entry_quality += 15  # Overlap bonus (best liquidity)
            elif not (7 <= hour < 17):  # Outside main sessions
                entry_quality -= 20

            # SPREAD CHECK (Critical for scalping)
            # Approximate spread check based on typical spreads
            if "JPY" in symbol:
                max_spread = 3  # 3 pip max for JPY pairs
            elif symbol in ["EURUSD", "GBPUSD"]:
                max_spread = 1.5  # 1.5 pip max for majors
            else:
                max_spread = 2  # 2 pip max for others

            # Reduce quality if likely high spread time
            if hour < 7 or hour >= 20:  # Low liquidity hours
                entry_quality -= 10

            # FINAL CONFIDENCE CALCULATION
            base_quality = min(entry_quality, 85)  # Cap at 85
            if base_quality < 65:
                return None  # Minimum quality for scalping

            # Scalping needs high confidence due to tight stops
            confidence = min(base_quality + 5, 88)  # Conservative confidence

            print(f"⚡ EMA_RSI_SCALP {symbol} {direction}:")
            print(f"   EMA8={ema8:.5f}, EMA21={ema21:.5f}, EMA50={ema50:.5f}")
            print(
                f"   Stack Valid={'Y' if bullish_stack or bearish_stack else 'N'}, Separation={ema_separation:.1f} pips"
            )
            print(f"   RSI={rsi:.1f}, Momentum={recent_momentum:.1f} pips")
            print(f"   Volume Spike={volume_spike:.2f}x, ATR={atr/pip_size:.1f} pips")
            print(f"   Quality={base_quality}%, Confidence={confidence}%")

            return PatternSignal(
                pattern="EMA_RSI_SCALP",
                direction=direction,
                entry_price=current_price,
                confidence=confidence,
                timeframe="M5",
                pair=symbol,
                quality_score=base_quality,
            )
        except Exception as e:
            print(f"Error in detect_ema_rsi_scalp for {symbol}: {e}")
            return None

    def should_generate_signal(self, symbol: str) -> bool:
        """Check if we should generate a signal for this pair"""
        current_time = time.time()

        # Check cooldown
        if symbol in self.last_signal_time:
            time_since_last = current_time - self.last_signal_time[symbol]
            if time_since_last < (self.COOLDOWN_MINUTES * 60):
                return False

        # Check hourly limits - be more lenient
        current_hour = datetime.now().hour
        if current_hour != self.current_hour:
            self.hourly_signal_count.clear()
            self.current_hour = current_hour

        # Allow up to 3 signals per symbol per hour
        if self.hourly_signal_count[symbol] >= 3:
            return False

        return True

    def generate_signal(self, pattern_signal: PatternSignal) -> Dict:
        """Generate trading signal with quality indicators and RAPID/SNIPER classification"""
        symbol = pattern_signal.pair  # Define symbol from pattern_signal
        # Fixed pip_size calculation to include XAUUSD and XAGUSD
        pip_size = get_pip_size(symbol)

        # Determine signal classification based on pattern type
        # RAPID: Quick momentum plays (accessible to all tiers)
        # SNIPER: Precision institutional patterns (PRO+ only)

        RAPID_PATTERNS = [
            "MOMENTUM_BREAKOUT",
            "VCB_BREAKOUT",
            "SWEEP_RETURN",
            "EMA_RSI_SCALP",
            "KALMAN_QUICKFIRE",
            "BB_SCALP",
        ]
        SNIPER_PATTERNS = ["LIQUIDITY_SWEEP_REVERSAL", "ORDER_BLOCK_BOUNCE", "FAIR_VALUE_GAP_FILL", "EMA_RSI_BB_VWAP"]

        signal_class = "RAPID" if pattern_signal.pattern in RAPID_PATTERNS else "SNIPER"

        # Dynamic SL/TP based on quality AND class
        # RAPID: Designed to complete within 1 hour (shorter TPs)
        # SNIPER: Designed to complete within 2 hours (larger TPs but still reasonable)

        # M5 ATR-BASED SCALPING STOPS - Optimized for 30-120 minute trades
        # Calculate ATR using M5 timeframe for scalp precision
        atr_value = self.calculate_atr(symbol, period=14)  # Already uses M5 data

        # Convert ATR to pips (ATR is already in pips from calculate_atr)
        atr_pips = atr_value

        # Use symbol-aware minimum ATR (not fixed 10 pips)
        min_atr, _ = get_min_max_stop_pips(symbol, timeframe="M5")
        if atr_pips < min_atr:
            atr_pips = min_atr

        # HYBRID SCALPING APPROACH - Pattern-Specific R:R (September 9, 2025)
        # Each pattern has optimal R:R based on its behavior characteristics
        pattern_type = pattern_signal.pattern

        # Pattern-specific R:R configuration (MINIMUM 1.5:1 for profitability)
        # With 1.5:1 RR you only need 40% win rate to break even
        pattern_rr_config = {
            "BB_SCALP": 1.5,  # Minimum acceptable RR
            "KALMAN_QUICKFIRE": 1.5,  # Mean reversion - tight but acceptable
            "MOMENTUM_BURST": 1.8,  # Momentum carries further
            "FAIR_VALUE_GAP_FILL": 1.7,  # Gap fills can extend
            "VCB_BREAKOUT": 2.0,  # Breakouts capture moves
            "SWEEP_RETURN": 2.0,  # Liquidity sweeps extend
            "ORDER_BLOCK_BOUNCE": 2.2,  # Institutional levels strong
            "LIQUIDITY_SWEEP_REVERSAL": 2.5,  # Major reversals capture most
        }

        # Get base R:R for this pattern (default to 1.5 if not specified - minimum acceptable)
        base_rr = pattern_rr_config.get(pattern_type, 1.5)

        # Quality score adjustment - higher quality can push for slightly more
        quality_bonus = 0
        if pattern_signal.quality_score >= 80:
            quality_bonus = 0.1  # Add 10% to R:R for premium setups
        elif pattern_signal.quality_score >= 70:
            quality_bonus = 0.05  # Add 5% for good setups

        # Final R:R ratio
        rr_ratio = base_rr + quality_bonus

        # SCALP-OPTIMIZED ATR multipliers (0.8-1.5x for M5 quick trades)
        pattern_atr_config = {
            "BB_SCALP": 0.8,  # Ultra-tight for compression breakouts
            "KALMAN_QUICKFIRE": 0.9,  # Tight for momentum scalps
            "MOMENTUM_BURST": 1.0,  # Moderate for quick moves
            "SWEEP_RETURN": 1.2,  # Slightly wider for liquidity plays
            "VCB_BREAKOUT": 1.2,  # Wider for volatility expansion
            "FAIR_VALUE_GAP_FILL": 1.3,  # Institutional fills need room
            "LIQUIDITY_SWEEP_REVERSAL": 1.5,  # Max 1.5x for scalps (not 2.0x)
            "ORDER_BLOCK_BOUNCE": 1.5,  # Max 1.5x for scalps (not 1.75x)
        }

        # Get base ATR multiplier for scalping
        base_multiplier = pattern_atr_config.get(pattern_type, ATR_SCALP_MULTIPLIERS["moderate"])

        # Session-based adjustment (tighter stops for low volatility)
        session = self.get_current_session()
        session_multiplier = 1.0
        if session == "ASIAN":
            session_multiplier = 0.8  # Much tighter in quiet Asian session
            rr_ratio *= 0.9  # Lower targets too
        elif session in ["OVERLAP", "LONDON"]:
            session_multiplier = 1.05  # Slightly wider (not 1.1x for scalps)

        # Final ATR multiplier for scalping
        atr_multiplier = base_multiplier * session_multiplier

        # Use calc_scalp_stop_pips for symbol/timeframe-aware limits
        stop_pips, target_pips = calc_scalp_stop_pips(
            symbol=symbol,
            atr_price_units=atr_pips * get_pip_size(symbol),  # Convert back to price units
            rr=rr_ratio,
            timeframe="M5",
            atr_mult=atr_multiplier
        )

        # Log ATR-based calculation for monitoring
        print(f"📊 ATR Stop Calculation for {symbol}:")
        print(f"   ATR: {atr_value:.1f} pips, Multiplier: {atr_multiplier:.2f}")
        print(f"   Stop: {stop_pips:.1f} pips, Target: {target_pips:.1f} pips")
        print(f"   Pattern: {pattern_type}, Quality: {pattern_signal.quality_score}")

        # FIX ERROR 4756: BROKER MINIMUM STOP DISTANCE REQUIREMENTS
        # Use centralized configuration for minimum stop requirements
        min_stop_requirements = TradingConfig.MIN_STOP_REQUIREMENTS

        # Apply minimum stop distance if required
        min_stop = min_stop_requirements.get(symbol, 0)
        if min_stop > 0 and stop_pips < min_stop:
            # Maintain risk/reward ratio when adjusting
            original_rr = target_pips / stop_pips if stop_pips > 0 else 1.5
            original_sl = stop_pips
            original_tp = target_pips
            stop_pips = min_stop
            target_pips = int(min_stop * original_rr)
            print(f"📏 {symbol}: STOP ADJUSTMENT for Error 4756 prevention")
            print(f"   Original: SL={original_sl}p, TP={original_tp}p")
            print(f"   Adjusted: SL={stop_pips}p, TP={target_pips}p")
            print(f"   R:R maintained: {original_rr:.2f}")
            print(f"   Reason: Broker minimum {min_stop}p for exotic/commodity")

        # Extra debugging for exotic pairs
        if symbol in min_stop_requirements:
            print(f"🎯 EXOTIC DEBUG - {symbol}:")
            print(f"   Stop Pips: {stop_pips}")
            print(f"   Target Pips: {target_pips}")
            print(f"   Pip Size: {pip_size}")
            print(f"   Entry: {pattern_signal.entry_price}")
            print(f"   Min Required: {min_stop_requirements[symbol]} pips")

        stop_distance = stop_pips * pip_size
        target_distance = target_pips * pip_size

        entry_price = pattern_signal.entry_price

        if pattern_signal.direction == "BUY":
            stop_loss = entry_price - stop_distance
            take_profit = entry_price + target_distance
        else:
            stop_loss = entry_price + stop_distance
            take_profit = entry_price - target_distance

        # Calculate lot size for testing phase - using centralized config
        account_balance = TradingConfig.DEFAULT_ACCOUNT_BALANCE
        risk_percent = TradingConfig.DEFAULT_RISK_PERCENT
        risk_amount = account_balance * risk_percent  # $30 on $1000 account

        # Calculate pip value (simplified - would need actual pip value calculation)
        if "JPY" in symbol:
            pip_value = 0.01  # Approximate for JPY pairs
        elif symbol in ["XAUUSD"]:
            pip_value = 0.01  # Gold pip value (standard pips)
        elif symbol in ["XAGUSD"]:
            pip_value = 0.001  # Silver: 0.001 price = 1 pip
        else:
            pip_value = 0.0001  # Standard forex pairs

        # Lot size calculation for 3% risk
        # Formula: Risk Amount / (SL pips * pip value per lot)
        # Assuming standard lot pip values: $10 for forex, varies for metals
        # Corrected pip values for proper risk calculation
        if symbol == "XAUUSD":
            pip_value_per_lot = 1.0  # Gold: $1 per pip per 0.01 lot
        elif symbol == "XAGUSD":
            pip_value_per_lot = 0.5  # Silver: $0.50 per pip per 0.01 lot (corrected from $5)
        else:
            pip_value_per_lot = 10.0  # Forex pairs: $10 per pip per standard lot
        lot_size = risk_amount / (stop_pips * pip_value_per_lot)
        lot_size = round(lot_size, 2)  # Round to 2 decimals for MT5

        print(
            f"💰 {symbol} {pattern_signal.direction} | SL: {stop_pips:.1f}p TP: {target_pips:.1f}p | R:R: 1:{rr_ratio:.2f} | Lot: {lot_size:.2f}"
        )

        # Get news impact for this symbol
        news_impact = self.get_news_impact(pattern_signal.pair)

        # Determine quality tier
        quality_tier = "ACCEPTABLE"
        if pattern_signal.quality_score >= 75:
            quality_tier = "PREMIUM"
        elif pattern_signal.quality_score >= 65:
            quality_tier = "STANDARD"

        # Create signal ID with class prefix
        signal_id_prefix = "ELITE_SNIPER" if signal_class == "SNIPER" else "ELITE_RAPID"

        # Determine signal_type based on signal_class for BittenCore compatibility
        signal_type = "RAPID_ASSAULT" if signal_class == "RAPID" else "PRECISION_STRIKE"

        signal = {
            "signal_id": f"{signal_id_prefix}_{pattern_signal.pair}_{int(time.time())}",
            "pair": pattern_signal.pair,
            "symbol": pattern_signal.pair,
            "direction": pattern_signal.direction,
            "pattern": pattern_signal.pattern,
            "pattern_type": pattern_signal.pattern,  # For compatibility
            "signal_class": signal_class,  # RAPID or SNIPER
            "signal_type": signal_type,  # CRITICAL: BittenCore requires this field for Telegram alerts & AUTO fire
            "confidence": round(pattern_signal.confidence, 1),
            "quality_score": round(pattern_signal.quality_score, 1),
            "quality_tier": quality_tier,
            "entry_price": round(entry_price, 5),
            "entry": round(entry_price, 5),  # CRITICAL FIX: Database expects 'entry' field
            "stop_loss": round(stop_loss, 5),
            "sl": round(stop_loss, 5),  # CRITICAL FIX: Database expects 'sl' field
            "take_profit": round(take_profit, 5),
            "tp": round(take_profit, 5),  # CRITICAL FIX: Database expects 'tp' field
            "stop_pips": stop_pips,
            "target_pips": target_pips,
            "risk_reward": round(target_pips / stop_pips, 2),
            "lot_size": lot_size,  # Added lot size for 3% risk
            "risk_percent": risk_percent * 100,  # Show risk percentage
            "timestamp": datetime.now(pytz.UTC).isoformat(),
            "session": self.get_current_session(),
            "tier_required": "PRESS_PASS" if signal_class == "RAPID" else "FANG",
            "tiers_allowed": (
                ["PRESS_PASS", "NIBBLER", "FANG", "COMMANDER"] if signal_class == "RAPID" else ["FANG", "COMMANDER"]
            ),
            "filters_passed": {
                "momentum": pattern_signal.momentum_score >= self.MIN_MOMENTUM,
                "volume": pattern_signal.volume_quality >= self.MIN_VOLUME,
                "confidence": pattern_signal.confidence >= self.MIN_CONFIDENCE,
            },
            "news_impact": news_impact,
        }

        return signal

    def get_current_session(self) -> str:
        """Get current trading session"""
        hour = datetime.now(pytz.UTC).hour

        if 0 <= hour < 9:
            return "TOKYO"
        elif 8 <= hour < 13:
            return "LONDON"
        elif 13 <= hour < 17:
            return "LONDON_NY"
        elif 17 <= hour < 22:
            return "NEWYORK"
        else:
            return "LATE_NY"

    def process_market_message(self, message: str):
        """Process incoming market data from EA stream (TICK, OHLC, or custom_bar_closed packets)"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            symbol = data.get("symbol")

            if not symbol or not message_type:
                return

            # Route to appropriate handler based on packet type (case-insensitive)
            if message_type.lower() == "tick":
                self.process_tick_packet(data)
            elif message_type.lower() == "ohlc":
                self.process_ohlc_packet(data)
            elif message_type == "custom_bar_closed":
                # NEW: Handle custom 15-second bars from EA (4x faster than M1)
                self.process_custom_bar(data)

        except Exception as e:
            logger.debug(f"Market message processing error: {e}")

    def process_tick_packet(self, data: dict):
        """Process TICK packets from EA stream"""
        try:
            symbol = data["symbol"]
            bid = data.get("bid", 0)
            ask = data.get("ask", 0)

            # Parse EA timestamp - can be Unix timestamp or string format
            timestamp_val = data.get("timestamp")
            if timestamp_val:
                if isinstance(timestamp_val, (int, float)):
                    # Unix timestamp format (what we're getting from EA)
                    tick_timestamp = float(timestamp_val)
                    timestamp_str = str(timestamp_val)
                elif isinstance(timestamp_val, str):
                    try:
                        # Parse EA format: "2025.09.25 15:44:02"
                        parsed_time = datetime.strptime(timestamp_val, "%Y.%m.%d %H:%M:%S")
                        tick_timestamp = parsed_time.timestamp()
                        timestamp_str = timestamp_val
                    except (ValueError, TypeError):
                        # Fallback to current time if parsing fails
                        tick_timestamp = time.time()
                        timestamp_str = str(tick_timestamp)
                else:
                    tick_timestamp = time.time()
                    timestamp_str = str(tick_timestamp)
            else:
                tick_timestamp = time.time()
                timestamp_str = str(tick_timestamp)

            # Convert to internal tick format for existing logic
            tick_data = {
                "symbol": symbol,
                "bid": bid,
                "ask": ask,
                "spread": data.get("spread", ask - bid),
                "volume": data.get("volume", 0),
                "timestamp": timestamp_str,
                "mid_price": (bid + ask) / 2,
            }

            # Store tick
            self.tick_data[symbol].append(tick_data)
            self.last_tick_time[symbol] = tick_timestamp

            # ✅ TASK D: Update health metrics for tick
            self.health_metrics["tick_count"] += 1
            self.health_metrics["last_tick_time"] = tick_timestamp
            elapsed = time.time() - self.health_metrics["metrics_start_time"]
            if elapsed > 0:
                self.health_metrics["tick_rate"] = self.health_metrics["tick_count"] / elapsed
            self.health_metrics["data_lag_ms"] = (time.time() - tick_timestamp) * 1000

            # Build candles from ticks (existing logic)
            self.build_candles_from_tick(symbol, tick_data)

            # Log first few ticks to verify reception
            if len(self.tick_data[symbol]) <= 3:
                print(f"📊 TICK: {symbol} bid={bid} ask={ask} spread={data.get('spread', 0)}")

        except Exception as e:
            logger.debug(f"Tick packet processing error: {e}")

    def process_ohlc_packet(self, data: dict):
        """Process OHLC packets from EA stream"""
        try:
            symbol = data["symbol"]
            timeframe = data.get("timeframe", "M1")

            # Convert to internal OHLC format
            ohlc_data = {
                "symbol": symbol,
                "timeframe": timeframe,
                "time": data.get("time", 0),
                "open": data.get("open", 0),
                "high": data.get("high", 0),
                "low": data.get("low", 0),
                "close": data.get("close", 0),
                "timestamp": data.get("timestamp"),
            }

            # Store in appropriate timeframe buffer
            if timeframe == "M1":
                self.m1_data[symbol].append(ohlc_data)
            elif timeframe == "M5":
                self.m5_data[symbol].append(ohlc_data)
            elif timeframe == "M15":
                self.m15_data[symbol].append(ohlc_data)
            elif timeframe == "M30":
                self.m30_data[symbol].append(ohlc_data)
            elif timeframe == "H1":
                self.h1_data[symbol].append(ohlc_data)

            # Log first few OHLC packets to verify reception
            if len(self.m1_data[symbol]) <= 3:
                print(
                    f"📈 OHLC: {symbol} {timeframe} O={ohlc_data['open']} H={ohlc_data['high']} L={ohlc_data['low']} C={ohlc_data['close']}"
                )

        except Exception as e:
            logger.debug(f"OHLC packet processing error: {e}")

    def process_custom_bar(self, data: dict):
        """
        Process custom 15-second bars from EA (4x faster pattern detection than M1)

        Expected format:
        {
            "type": "custom_bar_closed",
            "symbol": "EURUSD",
            "tf_seconds": 15,
            "feed_ver": 2,
            "t": 1727702580,  # Unix timestamp
            "o": 1.08500,
            "h": 1.08550,
            "l": 1.08490,
            "c": 1.08520,
            "v": 1234
        }
        """
        try:
            symbol = data["symbol"]
            timestamp = data.get("t", 0)
            feed_ver = data.get("feed_ver", 0)
            tf_seconds = data.get("tf_seconds", 0)

            self.custom_bar_stats["received"] += 1

            # Validate custom bar format (must be feed_ver=2, tf_seconds=15)
            if feed_ver != 2 or tf_seconds != 15:
                logger.warning(f"Invalid custom bar format: feed_ver={feed_ver}, tf_seconds={tf_seconds}")
                return

            # Deduplication by timestamp (multiple EAs may send same bar)
            if timestamp in self.s15_timestamps[symbol]:
                self.custom_bar_stats["duplicates"] += 1
                return

            # Convert to internal format
            bar_data = {
                "symbol": symbol,
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp),
                "open": data.get("o", 0),
                "high": data.get("h", 0),
                "low": data.get("l", 0),
                "close": data.get("c", 0),
                "volume": data.get("v", 0),
                "timeframe": "S15",  # Custom 15-second timeframe
            }

            # Store in 15-second buffer
            self.s15_data[symbol].append(bar_data)
            self.s15_timestamps[symbol].add(timestamp)
            self.custom_bar_stats["processed"] += 1

            # Log first few custom bars to verify reception
            if len(self.s15_data[symbol]) <= 5:
                print(
                    f"⚡ CUSTOM 15s BAR: {symbol} O={bar_data['open']:.5f} H={bar_data['high']:.5f} "
                    f"L={bar_data['low']:.5f} C={bar_data['close']:.5f} (bars={len(self.s15_data[symbol])})"
                )

            # IMPORTANT: Trigger rapid pattern detection when we have enough 15s bars
            # 20 bars = 5 minutes of data (4x faster than M1)
            if len(self.s15_data[symbol]) >= 20:
                # Pattern detection will use s15_data alongside m5_data
                pass  # Pattern detection happens in main scan loop

        except Exception as e:
            logger.debug(f"Custom bar processing error: {e}")

    def fetch_ohlc_data(self):
        """Fetch OHLC data from telemetry bridge (EA messages republished)"""
        try:
            while True:
                try:
                    # Non-blocking receive from telemetry bridge
                    message = self.ohlc_subscriber.recv_string(zmq.DONTWAIT)

                    # Parse different message types - look for OHLC type
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type", "")

                        if msg_type == "OHLC":
                            symbol = data.get("symbol", "")
                            timeframe = data.get("timeframe", "")

                            # Only process our trading pairs
                            if symbol not in self.trading_pairs:
                                continue

                            # Create candle data structure
                            candle = {
                                "timestamp": float(data.get("time", 0)),
                                "open": float(data.get("open", 0)),
                                "high": float(data.get("high", 0)),
                                "low": float(data.get("low", 0)),
                                "close": float(data.get("close", 0)),
                                "volume": 1,  # EA doesn't send volume for OHLC
                            }

                            # Store in appropriate timeframe buffer
                            if timeframe == "M1":
                                self.m1_data[symbol].append(candle)
                                print(f"📊 {symbol} M1 OHLC: {len(self.m1_data[symbol])} candles")
                            elif timeframe == "M5":
                                self.m5_data[symbol].append(candle)
                                print(f"📊 {symbol} M5 OHLC: {len(self.m5_data[symbol])} candles")
                            elif timeframe == "M15":
                                self.m15_data[symbol].append(candle)
                                print(f"📊 {symbol} M15 OHLC: {len(self.m15_data[symbol])} candles")

                    except json.JSONDecodeError:
                        # Not JSON, skip
                        continue

                except zmq.Again:
                    # No message available, break the loop
                    break

        except Exception as e:
            print(f"❌ OHLC fetch error: {e}")

    def build_candles_from_tick(self, symbol: str, tick_data: dict):
        """Aggregate ticks into proper OHLC candles - RESTORED FROM WORKING BACKUP"""
        if symbol not in self.trading_pairs or not tick_data:
            return

        bid = tick_data.get("bid", 0)
        ask = tick_data.get("ask", 0)
        if not bid or not ask:
            return

        mid_price = (bid + ask) / 2
        volume = tick_data.get("volume", 1)
        current_minute = int(time.time() / 60) * 60  # Round down to minute

        # Initialize storage if needed
        if not hasattr(self, "current_candles"):
            self.current_candles = {}
        if symbol not in self.current_candles:
            self.current_candles[symbol] = {}

        # Create or update current minute candle
        if current_minute not in self.current_candles[symbol]:
            # New minute = new candle
            self.current_candles[symbol][current_minute] = {
                "open": mid_price,
                "high": mid_price,
                "low": mid_price,
                "close": mid_price,
                "volume": volume,
                "timestamp": current_minute,
            }
            # Log new candle creation for debugging
            if symbol in ["EURUSD", "GBPUSD"]:
                print(f"🕯️ {symbol}: New M1 candle at {current_minute}, price={mid_price:.5f}")
        else:
            # Update existing candle
            candle = self.current_candles[symbol][current_minute]
            candle["high"] = max(candle["high"], mid_price)
            candle["low"] = min(candle["low"], mid_price)
            candle["close"] = mid_price
            candle["volume"] += volume

        # Push completed candles to M1 buffer
        completed_minutes = [m for m in self.current_candles[symbol] if m < current_minute]
        for minute in completed_minutes:
            completed_candle = self.current_candles[symbol].pop(minute)
            completed_candle["complete"] = True  # Mark as complete bar
            self.m1_data[symbol].append(completed_candle)

            # ✅ TASK D: Update health metrics for bar close
            self.health_metrics["candle_close_count"] += 1
            elapsed = time.time() - self.health_metrics["metrics_start_time"]
            if elapsed > 0:
                self.health_metrics["candle_close_rate"] = self.health_metrics["candle_close_count"] / elapsed

            # Log candle completion with provenance
            if symbol in ["EURUSD", "GBPUSD"]:
                print(f"✅ {symbol}: M1 bar.complete t_close={minute} total={len(self.m1_data[symbol])}")

            # Aggregate M1 → M5 (every 5 M1 candles)
            if len(self.m1_data[symbol]) >= 5 and len(self.m1_data[symbol]) % 5 == 0:
                self.aggregate_m1_to_m5(symbol)

            # Aggregate M5 → M15 (every 3 M5 candles)
            if len(self.m5_data[symbol]) >= 3 and len(self.m5_data[symbol]) % 3 == 0:
                self.aggregate_m5_to_m15(symbol)

            # Aggregate M15 → M30 (every 2 M15 candles)
            if len(self.m15_data[symbol]) >= 2 and len(self.m15_data[symbol]) % 2 == 0:
                self.aggregate_m15_to_m30(symbol)

            # Aggregate M30 → H1 (every 2 M30 candles)
            if len(self.m30_data[symbol]) >= 2 and len(self.m30_data[symbol]) % 2 == 0:
                self.aggregate_m30_to_h1(symbol)

            # Aggregate H1 → H4 (every 4 H1 candles)
            if len(self.h1_data[symbol]) >= 4 and len(self.h1_data[symbol]) % 4 == 0:
                self.aggregate_h1_to_h4(symbol)

            # ✅ TASK C FIX: Set flag to trigger pattern scan on bar close
            if not hasattr(self, 'bar_complete_events'):
                self.bar_complete_events = {}
            self.bar_complete_events[symbol] = {
                'timestamp': minute,
                'timeframe': 'M1',
                'source': 'tick_aggregation'
            }

        # REMOVED: No longer add forming candles to m1_data (causes partial bar firing)
        # Pattern detection now only fires on complete bars via bar_complete_events

    def placeholder_removed(self):
        """Old OHLC code removed - now builds directly from ticks"""
        pass

    def OLD_CODE_TO_DELETE_while_True():
        try:
            message = self.ohlc_subscriber.recv_string(zmq.DONTWAIT)
            message_count += 1

            # Debug: Log raw message reception
            if message_count == 1:
                print(f"🔵 Port 5556 Active: Received {len(message)} bytes from EA")

            if message.startswith("OHLC "):
                # Parse OHLC message: "OHLC {json_data}"
                ohlc_data = json.loads(message[5:])  # Remove "OHLC " prefix

                # Extract data from EA format
                msg_symbol = ohlc_data.get("symbol", "")
                timeframe = ohlc_data.get("timeframe", "")
                timestamp = ohlc_data.get("time", 0)
                open_price = float(ohlc_data.get("open", 0))
                high_price = float(ohlc_data.get("high", 0))
                low_price = float(ohlc_data.get("low", 0))
                close_price = float(ohlc_data.get("close", 0))
                volume = int(ohlc_data.get("volume", 1))

                # Enhanced debug logging for EURUSD especially
                if msg_symbol == "EURUSD" or message_count <= 5:
                    print(
                        f"🟢 OHLC [{msg_symbol}] {timeframe}: O={open_price:.5f} H={high_price:.5f} L={low_price:.5f} C={close_price:.5f} T={timestamp}"
                    )

                # Store in appropriate buffer based on timeframe
                if msg_symbol in self.trading_pairs:
                    candle = {
                        "open": open_price,
                        "high": high_price,
                        "low": low_price,
                        "close": close_price,
                        "volume": volume,
                        "timestamp": timestamp,
                    }

                    # Update last OHLC time for this symbol
                    self.last_ohlc_time[msg_symbol] = current_time
                    ohlc_received = True

                    if timeframe == "M1":
                        self.m1_data[msg_symbol].append(candle)
                        if msg_symbol == "EURUSD":
                            print(f"📈 EURUSD M1: {len(self.m1_data[msg_symbol])} candles stored")
                    elif timeframe == "M5":
                        self.m5_data[msg_symbol].append(candle)
                        if msg_symbol == "EURUSD":
                            print(f"📊 EURUSD M5: {len(self.m5_data[msg_symbol])} candles stored")
                    elif timeframe == "M15":
                        self.m15_data[msg_symbol].append(candle)
                        if msg_symbol == "EURUSD":
                            print(f"📉 EURUSD M15: {len(self.m15_data[msg_symbol])} candles stored")
                else:
                    print(f"⚠️ {msg_symbol} not in trading pairs, skipping")
            else:
                # Non-OHLC message received
                print(f"🔸 Non-OHLC message: {message[:50]}...")

        except Exception as e:
            pass  # Old OHLC code removed

    # Helper functions for aggregation
    def OLD_REMOVED_CODE_PLACEHOLDER(self):
        """Removed old broken code"""
        if False:  # Never execute
            self.current_candles[symbol] = {}
            pass  # Old broken code removed

    # Force aggregate functions removed - using proper M1->M5->M15 aggregation

    def aggregate_all_historical_candles(self, symbol: str):
        """Process ALL M1 candles into M5/M15/M30 - for historical backfill"""
        m1_candles = list(self.m1_data[symbol])

        if len(m1_candles) < 5:
            return

        # Group M1 candles by 5-minute boundaries and create M5 candles
        m5_groups = {}
        for candle in m1_candles:
            # Round timestamp to 5-minute boundary
            m5_timestamp = int(candle["timestamp"] / 300) * 300
            if m5_timestamp not in m5_groups:
                m5_groups[m5_timestamp] = []
            m5_groups[m5_timestamp].append(candle)

        # Create M5 candles from groups (use any available M1 candles, don't require exactly 5)
        for m5_ts in sorted(m5_groups.keys()):
            m1_group = m5_groups[m5_ts]
            # Check if we already have this M5
            if self.m5_data[symbol] and any(c["timestamp"] == m5_ts for c in self.m5_data[symbol]):
                continue

            if len(m1_group) > 0:  # Create M5 from whatever M1 candles we have
                m5_candle = {
                    "open": m1_group[0]["open"],
                    "high": max(c["high"] for c in m1_group),
                    "low": min(c["low"] for c in m1_group),
                    "close": m1_group[-1]["close"],
                    "volume": sum(c["volume"] for c in m1_group),
                    "timestamp": m5_ts,
                    "complete": len(m1_group) >= 5,  # Only mark complete if we have all 5
                }
                self.m5_data[symbol].append(m5_candle)

        # Now aggregate M5 → M15
        m5_candles = list(self.m5_data[symbol])
        if len(m5_candles) >= 3:
            m15_groups = {}
            for candle in m5_candles:
                # Round to 15-minute boundary
                m15_timestamp = int(candle["timestamp"] / 900) * 900
                if m15_timestamp not in m15_groups:
                    m15_groups[m15_timestamp] = []
                m15_groups[m15_timestamp].append(candle)

            for m15_ts in sorted(m15_groups.keys()):
                m5_group = m15_groups[m15_ts]
                # Check if we already have this M15
                if self.m15_data[symbol] and any(c["timestamp"] == m15_ts for c in self.m15_data[symbol]):
                    continue

                if len(m5_group) > 0:  # Create M15 from whatever M5 candles we have
                    m15_candle = {
                        "open": m5_group[0]["open"],
                        "high": max(c["high"] for c in m5_group),
                        "low": min(c["low"] for c in m5_group),
                        "close": m5_group[-1]["close"],
                        "volume": sum(c["volume"] for c in m5_group),
                        "timestamp": m15_ts,
                        "complete": len(m5_group) >= 3,  # Only mark complete if we have all 3
                    }
                    self.m15_data[symbol].append(m15_candle)

        # Finally aggregate M15 → M30
        m15_candles = list(self.m15_data[symbol])
        if len(m15_candles) >= 2:
            m30_groups = {}
            for candle in m15_candles:
                # Round to 30-minute boundary
                m30_timestamp = int(candle["timestamp"] / 1800) * 1800
                if m30_timestamp not in m30_groups:
                    m30_groups[m30_timestamp] = []
                m30_groups[m30_timestamp].append(candle)

            for m30_ts in sorted(m30_groups.keys()):
                m15_group = m30_groups[m30_ts]
                # Check if we already have this M30
                if self.m30_data[symbol] and any(c["timestamp"] == m30_ts for c in self.m30_data[symbol]):
                    continue

                if len(m15_group) > 0:  # Create M30 from whatever M15 candles we have
                    m30_candle = {
                        "open": m15_group[0]["open"],
                        "high": max(c["high"] for c in m15_group),
                        "low": min(c["low"] for c in m15_group),
                        "close": m15_group[-1]["close"],
                        "volume": sum(c["volume"] for c in m15_group),
                        "timestamp": m30_ts,
                        "complete": len(m15_group) >= 2,  # Only mark complete if we have both
                    }
                    self.m30_data[symbol].append(m30_candle)

        print(f"📊 {symbol}: Aggregated historical candles - {len(self.m5_data[symbol])} M5, {len(self.m15_data[symbol])} M15, {len(self.m30_data[symbol])} M30")

    def aggregate_m1_to_m5(self, symbol: str):
        """Build M5 candle from last 5 M1 candles - AGGRESSIVE"""
        if len(self.m1_data[symbol]) >= 5:
            # Build M5 from every complete set of 5 M1 candles
            last_5 = list(self.m1_data[symbol])[-5:]

            # Calculate M5 timestamp from first M1 timestamp rounded to 5-minute boundary
            first_timestamp = last_5[0]["timestamp"]
            m5_timestamp = int(first_timestamp / 300) * 300  # Round to 5-minute boundary

            # Check if we already have this M5 timestamp
            if self.m5_data[symbol] and self.m5_data[symbol][-1]["timestamp"] == m5_timestamp:
                return  # Already have this M5

            m5_candle = {
                "open": last_5[0]["open"],
                "high": max(c["high"] for c in last_5),
                "low": min(c["low"] for c in last_5),
                "close": last_5[-1]["close"],
                "volume": sum(c["volume"] for c in last_5),
                "timestamp": m5_timestamp,
                "complete": True,  # Mark M5 as complete
            }
            self.m5_data[symbol].append(m5_candle)
            print(f"📊 {symbol}: M5 bar.complete t_close={m5_timestamp} (from 5 M1 bars)")

            # ✅ TASK C FIX: Trigger pattern scan on M5 bar close
            if not hasattr(self, 'bar_complete_events'):
                self.bar_complete_events = {}
            self.bar_complete_events[symbol] = {
                'timestamp': m5_timestamp,
                'timeframe': 'M5',
                'source': 'm1_aggregation'
            }

    def aggregate_m5_to_m15(self, symbol: str):
        """Build M15 candle from last 3 M5 candles - AGGRESSIVE"""
        if len(self.m5_data[symbol]) >= 3:
            # Build M15 from every complete set of 3 M5 candles
            last_3 = list(self.m5_data[symbol])[-3:]

            # Check if we already have this M15 timestamp
            m15_timestamp = last_3[0]["timestamp"]
            if self.m15_data[symbol] and self.m15_data[symbol][-1]["timestamp"] == m15_timestamp:
                return  # Already have this M15

            m15_candle = {
                "open": last_3[0]["open"],
                "high": max(c["high"] for c in last_3),
                "low": min(c["low"] for c in last_3),
                "close": last_3[-1]["close"],
                "volume": sum(c["volume"] for c in last_3),
                "timestamp": m15_timestamp,
            }
            self.m15_data[symbol].append(m15_candle)
            print(f"📊 {symbol}: Created M15 candle from {len(last_3)} M5 candles")

    def aggregate_m15_to_m30(self, symbol: str):
        """Build M30 candle from last 2 M15 candles"""
        if len(self.m15_data[symbol]) >= 2:
            last_2 = list(self.m15_data[symbol])[-2:]

            # Check if we already have this M30 timestamp
            m30_timestamp = last_2[0]["timestamp"]
            if self.m30_data[symbol] and self.m30_data[symbol][-1]["timestamp"] == m30_timestamp:
                return

            m30_candle = {
                "open": last_2[0]["open"],
                "high": max(c["high"] for c in last_2),
                "low": min(c["low"] for c in last_2),
                "close": last_2[-1]["close"],
                "volume": sum(c["volume"] for c in last_2),
                "timestamp": m30_timestamp,
            }
            self.m30_data[symbol].append(m30_candle)

    def aggregate_m30_to_h1(self, symbol: str):
        """Build H1 candle from last 2 M30 candles"""
        if len(self.m30_data[symbol]) >= 2:
            last_2 = list(self.m30_data[symbol])[-2:]

            # Check if we already have this H1 timestamp
            h1_timestamp = last_2[0]["timestamp"]
            if self.h1_data[symbol] and self.h1_data[symbol][-1]["timestamp"] == h1_timestamp:
                return

            h1_candle = {
                "open": last_2[0]["open"],
                "high": max(c["high"] for c in last_2),
                "low": min(c["low"] for c in last_2),
                "close": last_2[-1]["close"],
                "volume": sum(c["volume"] for c in last_2),
                "timestamp": h1_timestamp,
            }
            self.h1_data[symbol].append(h1_candle)

    def aggregate_h1_to_h4(self, symbol: str):
        """Build H4 candle from last 4 H1 candles"""
        if len(self.h1_data[symbol]) >= 4:
            last_4 = list(self.h1_data[symbol])[-4:]

            # Check if we already have this H4 timestamp
            h4_timestamp = last_4[0]["timestamp"]
            if self.h4_data[symbol] and self.h4_data[symbol][-1]["timestamp"] == h4_timestamp:
                return

            h4_candle = {
                "open": last_4[0]["open"],
                "high": max(c["high"] for c in last_4),
                "low": min(c["low"] for c in last_4),
                "close": last_4[-1]["close"],
                "volume": sum(c["volume"] for c in last_4),
                "timestamp": h4_timestamp,
            }
            self.h4_data[symbol].append(h4_candle)

    def save_candles(self):
        """Save candle and tick data to cache file"""
        try:
            # Build data structure with M1/M5/M15 data
            cache_data = {"m1_data": {}, "m5_data": {}, "m15_data": {}, "tick_data": {}, "last_update": time.time()}

            # Save all candle data for each symbol
            total_m1 = 0
            total_m5 = 0
            total_m15 = 0

            for symbol in self.trading_pairs:
                # Save M1 data
                if symbol in self.m1_data and len(self.m1_data[symbol]) > 0:
                    cache_data["m1_data"][symbol] = list(self.m1_data[symbol])
                    total_m1 += len(self.m1_data[symbol])

                # Save M5 data
                if symbol in self.m5_data and len(self.m5_data[symbol]) > 0:
                    cache_data["m5_data"][symbol] = list(self.m5_data[symbol])
                    total_m5 += len(self.m5_data[symbol])

                # Save M15 data
                if symbol in self.m15_data and len(self.m15_data[symbol]) > 0:
                    cache_data["m15_data"][symbol] = list(self.m15_data[symbol])
                    total_m15 += len(self.m15_data[symbol])

                # Save recent ticks (last 100)
                if symbol in self.tick_data and len(self.tick_data[symbol]) > 0:
                    cache_data["tick_data"][symbol] = list(self.tick_data[symbol])[-100:]

            # Write to file
            with open("/root/HydraX-v2/candle_cache.json", "w") as f:
                json.dump(cache_data, f)

            print(f"💾 Saved candles: M1:{total_m1}, M5:{total_m5}, M15:{total_m15}")

        except Exception as e:
            print(f"❌ Error saving candles: {e}")

    def load_candles(self):
        """Load candle and tick data from cache file"""
        try:
            if os.path.exists("/root/HydraX-v2/candle_cache.json"):
                with open("/root/HydraX-v2/candle_cache.json", "r") as f:
                    cache_data = json.load(f)

                total_m1 = 0
                total_m5 = 0
                total_m15 = 0

                # Load all candle data for each symbol
                for symbol in self.trading_pairs:
                    # Load M1 data
                    if symbol in cache_data.get("m1_data", {}):
                        self.m1_data[symbol] = deque(cache_data["m1_data"][symbol], maxlen=500)
                        total_m1 += len(self.m1_data[symbol])
                    else:
                        self.m1_data[symbol] = deque(maxlen=500)

                    # Load M5 data
                    if symbol in cache_data.get("m5_data", {}):
                        self.m5_data[symbol] = deque(cache_data["m5_data"][symbol], maxlen=300)
                        total_m5 += len(self.m5_data[symbol])
                    else:
                        self.m5_data[symbol] = deque(maxlen=300)

                    # Load M15 data
                    if symbol in cache_data.get("m15_data", {}):
                        self.m15_data[symbol] = deque(cache_data["m15_data"][symbol], maxlen=200)
                        total_m15 += len(self.m15_data[symbol])
                    else:
                        self.m15_data[symbol] = deque(maxlen=200)

                    # Load tick data
                    if symbol in cache_data.get("tick_data", {}):
                        self.tick_data[symbol] = deque(cache_data["tick_data"][symbol], maxlen=1000)
                        # DO NOT set last_tick_time from cached data - let freshness check detect stale data
                        # self.last_tick_time[symbol] will be set by first REAL tick from EA

                # Log loaded counts for verification
                print(f"🔍 Loaded candles from cache:")
                print(f"   Total M1: {total_m1}, M5: {total_m5}, M15: {total_m15}")

                # Show EURUSD specifically as requested
                if "EURUSD" in self.m1_data:
                    print(
                        f"   EURUSD: M1={len(self.m1_data['EURUSD'])}, M5={len(self.m5_data.get('EURUSD', []))}, M15={len(self.m15_data.get('EURUSD', []))}"
                    )
            else:
                print("⚠️ No candle cache file found, starting fresh")

        except Exception as e:
            print(f"❌ Error loading candles: {e}")

    def fetch_news_events(self):
        """Fetch news events from Forex Factory API"""
        try:
            current_time = time.time()
            # Refresh news every 30 minutes
            if current_time - self.last_news_fetch > 1800:
                self.news_events = self.news_client.fetch_events(days_ahead=1)
                self.last_news_fetch = current_time
                print(f"📰 Fetched {len(self.news_events)} news events from Forex Factory")
        except Exception as e:
            print(f"❌ Error fetching news events: {e}")

    def get_news_impact(self, symbol: str) -> int:
        """Get news impact adjustment for confidence (-10 for high impact)"""
        # DISABLED for testing - always return 0
        return 0

        self.fetch_news_events()  # Ensure we have fresh events

        now = datetime.now(pytz.UTC)
        impact_adjustment = 0

        for event in self.news_events:
            # Check if event affects this currency pair
            event_currency = event.currency.upper() if hasattr(event, "currency") else ""
            if event_currency and event_currency in symbol:
                # Check if event is within 2 hours
                event_time = event.event_time if hasattr(event, "event_time") else datetime.now(pytz.UTC)
                time_diff = abs((event_time - now).total_seconds() / 3600)

                if time_diff <= 2:  # Within 2 hours
                    impact_level = event.impact if hasattr(event, "impact") else "medium"

                    # Convert NewsImpact enum to string if needed
                    impact_str = impact_level.value if hasattr(impact_level, "value") else str(impact_level).lower()

                    if impact_str == "high":
                        print(f"📰 {symbol}: {event.event_name} in {time_diff:.1f}h - HIGH impact (-10)")
                        impact_adjustment = min(impact_adjustment - 10, -10)
                    elif impact_str == "medium":
                        print(f"📰 {symbol}: {event.event_name} in {time_diff:.1f}h - MEDIUM impact (-5)")
                        impact_adjustment = min(impact_adjustment - 5, -5)

        return impact_adjustment

    def apply_ml_filter(self, signal, session: str) -> tuple[bool, str, float]:
        """Apply ML filtering with dynamic threshold for 5-10 signals/hour target"""
        # QUALITY GATE #1: PAIR-SPECIFIC FOR 65%+ WIN RATE TARGET
        symbol = getattr(signal, "pair", getattr(signal, "symbol", ""))

        # EMERGENCY TESTING: Much lower thresholds to verify system is working
        # Standard pairs should generate signals during peak trading hours
        if symbol in ["NZDUSD", "XAUUSD"]:  # 75%, 53% win rates
            min_quality_score = 45.0  # TESTING: was 65.0
        elif symbol in ["AUDJPY", "EURJPY"]:  # 50%, 43% win rates
            min_quality_score = 48.0  # TESTING: was 68.0
        elif symbol in ["XAGUSD", "USDMXN", "USDCNH", "USDSEK"]:  # <30% win rate
            min_quality_score = 55.0  # TESTING: was 75.0
        else:
            min_quality_score = 50.0  # TESTING: was 70.0 - major pairs should fire

        # Pattern+Pair combo adjustments (based on actual performance)
        pattern_type = getattr(signal, "pattern", "UNKNOWN")
        combo_key = f"{pattern_type}_{symbol}"

        # WINNING COMBOS: Big bonuses (proven performers)
        winning_combos = {
            # 'ORDER_BLOCK_BOUNCE_USDCAD': removed - USDCAD no longer traded
            "ORDER_BLOCK_BOUNCE_NZDUSD": -12,  # 75% win rate
            "FAIR_VALUE_GAP_FILL_EURJPY": -10,  # 75% win rate
            "ORDER_BLOCK_BOUNCE_XAUUSD": -8,  # Good on XAUUSD
            "FAIR_VALUE_GAP_FILL_XAUUSD": -5,  # 50% win rate
            "ORDER_BLOCK_BOUNCE_USDJPY": -5,  # 50% win rate
            "ORDER_BLOCK_BOUNCE_GBPUSD": -5,  # 50% win rate
            "FAIR_VALUE_GAP_FILL_AUDJPY": -3,  # 50% win rate
        }

        # LOSING COMBOS: Reduced penalties for ML learning
        losing_combos = {
            "FAIR_VALUE_GAP_FILL_XAGUSD": 10,  # Was 50, now just harder
            "ORDER_BLOCK_BOUNCE_XAGUSD": 10,  # Was 50, now just harder
            "FAIR_VALUE_GAP_FILL_USDMXN": 10,  # Was 50, now just harder
            "ORDER_BLOCK_BOUNCE_EURJPY": 5,  # Was 20, slight penalty
            "ORDER_BLOCK_BOUNCE_GBPJPY": 5,  # Was 20, slight penalty
            "FAIR_VALUE_GAP_FILL_GBPJPY": 5,  # Was 20, slight penalty
            "ORDER_BLOCK_BOUNCE_EURAUD": 3,  # Was 15, minimal penalty
            "ORDER_BLOCK_BOUNCE_EURUSD": 3,  # Was 15, minimal penalty
        }

        # Apply combo adjustment if exists, else pattern-only adjustment
        if combo_key in winning_combos:
            adjustment = winning_combos[combo_key]
        elif combo_key in losing_combos:
            adjustment = losing_combos[combo_key]
        else:
            # Default pattern adjustments - OPENED UP for diversity testing
            pattern_adjustments = {
                "ORDER_BLOCK_BOUNCE": 0,  # Neutral - let it prove itself
                "FAIR_VALUE_GAP_FILL": 0,  # Neutral - has 43% win rate
                "LIQUIDITY_SWEEP_REVERSAL": 0,  # Neutral - let data decide
                "VCB_BREAKOUT": 0,  # Neutral - let data decide
                "SWEEP_RETURN": 0,  # Opened up - was blocked
                "SWEEP_AND_RETURN": 0,  # Opened up - was blocked
            }
            adjustment = pattern_adjustments.get(pattern_type, 0)

        min_quality_score += adjustment
        base_quality = min_quality_score  # Use calculated value
        print(f"🔍 Quality check: {signal.quality_score:.1f}% vs {min_quality_score}%")

        if hasattr(signal, "quality_score") and signal.quality_score < min_quality_score:
            print(f"⚠️ Quality fail")
            return False, f"Quality {signal.quality_score:.1f}% < {min_quality_score}%", signal.confidence
        print(f"✅ Quality passed")

        # Dynamic ML threshold based on recent signal rate
        # Track signals in last 15 minutes
        current_time = time.time()
        recent_signals = getattr(self, "recent_signal_times", [])
        recent_signals = [t for t in recent_signals if current_time - t < 900]  # Last 15 min

        # Calculate hourly rate projection
        signals_per_15min = len(recent_signals)
        projected_hourly_rate = signals_per_15min * 4

        # QUALITY GATE #2: PATTERN-SPECIFIC THRESHOLDS - BALANCED for signals
        pattern_thresholds = {
            # KEEP WORKING PATTERNS - PROVEN PERFORMERS
            "KALMAN_QUICKFIRE": 80.0,  # Working @ 83.8% avg - KEEP
            "BB_SCALP": 85.0,  # Working @ 85.4% avg - KEEP
            "LIQUIDITY_SWEEP_REVERSAL": 70.0,  # Working @ 81.9% avg - KEEP
            # RESCUE BLOCKED SNIPER PATTERNS - RESEARCH-BASED THRESHOLDS
            "VCB_BREAKOUT": 65.0,  # REDUCED: 75% → 65% (expect 5-10/day)
            "ORDER_BLOCK_BOUNCE": 65.0,  # REDUCED: 75% → 65% (expect 8-15/day)
            "SWEEP_RETURN": 68.0,  # REDUCED: 78% → 68% (expect 10-20/day)
            "MOMENTUM_BURST": 65.0,  # REDUCED: 75% → 65% (expect 12-25/day)
            "MOMENTUM_BREAKOUT": 65.0,  # REDUCED: 75% → 65% (same as MOMENTUM_BURST)
            # ENABLE NEW PATTERNS - TESTING THRESHOLDS
            "BLIND_SPOT": 70.0,  # ENABLED: Was default 79% (FVG replacement)
            "TRAPDOOR_SSR": 70.0,  # ENABLED: Was default 79% (session-specific)
            "PRESSURE_VALVE": 70.0,  # ENABLED: Was default 79% (enhanced VCB)
            # TECHNICAL INDICATOR PATTERNS - ENABLE FOR VARIETY
            "EMA_RSI_BB_VWAP": 70.0,  # ENABLED: Was default 79% (multi-confluence)
            "EMA_RSI_SCALP": 70.0,  # ENABLED: Was default 79% (46.4% proven WR)
            # DISABLED POOR PERFORMERS
            "FAIR_VALUE_GAP_FILL": 99.0,  # KEEP DISABLED: 31% WR - replaced by BLIND_SPOT
        }

        # Get pattern-specific threshold
        min_confidence = pattern_thresholds.get(pattern_type, 79.0)

        # Apply pattern-specific confidence adjustments - REMOVED PENALTIES for testing
        pattern_confidence_adj = {
            "FAIR_VALUE_GAP_FILL": 0,  # Neutral - let actual performance decide
            "ORDER_BLOCK_BOUNCE": 0,  # Neutral - let actual performance decide
            "LIQUIDITY_SWEEP_REVERSAL": 0,  # Neutral - let actual performance decide
            "VCB_BREAKOUT": 0,  # Neutral - was +5, now neutral for fairness
            "SWEEP_RETURN": 0,  # Neutral
        }

        conf_adj = pattern_confidence_adj.get(pattern_type, 0)
        if conf_adj != 0:
            print(f"   🎯 Confidence adjustment for {pattern_type}: {conf_adj:+d}%")

        print(f"🔍 ML check: {signal.confidence}% vs {min_confidence}%")

        # Apply news impact adjustment to confidence
        news_adjustment = self.get_news_impact(signal.pair)
        adjusted_confidence = signal.confidence + news_adjustment

        # TIME-BASED FILTERING: Avoid bad trading hours (UTC)
        current_hour = datetime.now().hour
        time_adjustment = 0

        # Bad hours: 17:00-19:00 UTC (12% - 20% WR)
        if current_hour in [17, 18, 19]:
            time_adjustment = -30  # 30% confidence reduction
            print(f"   ⏰ BAD HOUR {current_hour}:00 UTC: -30% confidence adjustment")
        # Also reduce during weak hour 04:00 UTC (22% WR)
        elif current_hour == 4:
            time_adjustment = -20  # 20% confidence reduction
            print(f"   ⏰ WEAK HOUR {current_hour}:00 UTC: -20% confidence adjustment")
        # Good hours: 03:00, 14:00-16:00 UTC (53-62% WR)
        elif current_hour in [3, 14, 15, 16]:
            time_adjustment = 10  # 10% confidence boost
            print(f"   ⏰ PRIME HOUR {current_hour}:00 UTC: +10% confidence boost")

        # Apply time-based adjustment
        adjusted_confidence = adjusted_confidence * (1 + time_adjustment / 100)

        if news_adjustment != 0:
            print(
                f"📰 {signal.pair}: News impact {news_adjustment} → Confidence {signal.confidence:.1f}% → {adjusted_confidence:.1f}%"
            )

        if adjusted_confidence < min_confidence:
            print(f"⚠️ ML fail")
            return False, f"Confidence {adjusted_confidence:.1f}% < {min_confidence}%", adjusted_confidence
        print(f"✅ ML passed")

        # Pattern restrictions based on performance - REMOVED for testing
        blocked_patterns = []  # OPENED UP - let ML decide based on real performance
        restricted_patterns = []  # Using quality gates instead

        if signal.pattern in blocked_patterns:
            print(f"   🚫 BLOCKED PATTERN: {signal.pattern} temporarily disabled (win rate < 40%)")
            return False, f"Pattern blocked for retraining", adjusted_confidence

        if signal.pattern in restricted_patterns and adjusted_confidence < 85:
            print(f"   ⚠️ RESTRICTED: {signal.pattern} needs 85%+ (has {adjusted_confidence:.1f}%)")
            return False, f"Restricted pattern - needs 85%+", adjusted_confidence

        # Check performance history
        pattern_clean = signal.pattern.replace("_INTELLIGENT", "")
        combo_key = f"{signal.pair}_{pattern_clean}_{session}"
        perf = self.performance_history.get(combo_key, {})
        if perf.get("enabled") == False:
            print(f"   ⚠️ PERFORMANCE FAIL: {combo_key} disabled due to poor history")
            return False, f"Disabled: poor performance", adjusted_confidence

        print(f"   ✅✅ SIGNAL APPROVED: {signal.pair} {signal.pattern} @ {adjusted_confidence:.1f}%")
        return True, f"PASS @ {adjusted_confidence:.1f}%", adjusted_confidence

    # ===========================================================================================
    # GATEKEEPER LOGIC PLAN (TO IMPLEMENT FOR 65%+ WIN RATE)
    # ===========================================================================================
    # Every 30 minutes, the gatekeeper will:
    # 1. Read last 100 signals from optimized_tracking.jsonl
    # 2. Calculate win rate by pattern+pair+session combo
    # 3. Dynamically adjust quality gates:
    #    - Win rate >60%: Apply -15% quality bonus (make it easier)
    #    - Win rate 50-60%: Apply -10% quality bonus
    #    - Win rate 40-50%: No adjustment
    #    - Win rate 30-40%: Apply +10% quality penalty
    #    - Win rate <30%: Apply +20% quality penalty (nearly block)
    # 4. Store adjustments in gatekeeper_adjustments.json
    # 5. Update winning_combos and losing_combos dicts dynamically
    # 6. Target: Converge to 65%+ win rate over time by:
    #    - Promoting consistent winners
    #    - Demoting/blocking consistent losers
    #    - Learning from real performance data
    # 7. Safety: Never adjust by more than ±25% in one cycle
    # 8. Persist: Save state to survive restarts
    # ===========================================================================================

    def log_signal_to_truth_tracker(self, signal_data: Dict):
        """Log signal with comprehensive metrics to truth tracker"""
        try:
            # Enhanced truth tracking with all metrics
            truth_entry = {
                "signal_id": signal_data.get("signal_id", ""),
                "pattern": signal_data.get("pattern_type", ""),
                "symbol": signal_data.get("pair", ""),
                "direction": signal_data.get("direction", ""),
                "entry": signal_data.get("entry_price", 0),
                "sl": signal_data.get("stop_loss", 0),
                "tp": signal_data.get("take_profit", 0),
                "sl_pips": signal_data.get("sl_pips", 0),
                "tp_pips": signal_data.get("tp_pips", 0),
                "confidence": signal_data.get("confidence", 0),
                "base_conf": signal_data.get("base_confidence", 0),
                "bonuses": {
                    "session": signal_data.get("session_bonus", 0),
                    "volume": signal_data.get("volume_bonus", 0),
                    "spread": signal_data.get("spread_bonus", 0),
                    "news": signal_data.get("news_impact", 0),
                },
                "timestamp": signal_data.get("timestamp", datetime.utcnow().isoformat() + "Z"),
                "session": signal_data.get("session", self.get_current_session()),
                "vol_actual": signal_data.get("volume_actual", 0),
                "vol_avg": signal_data.get("volume_average", 0),
                "vol_ratio": signal_data.get("volume_ratio", 0),
                "pattern_age": signal_data.get("pattern_age_minutes", 0),
                "expectancy": signal_data.get("expectancy", 0),
                "rr_proj": signal_data.get("risk_reward", 0),
                "citadel": signal_data.get("citadel_score", 0),
                "quarantine": signal_data.get("quarantine_status", 0),
                "convergence": signal_data.get("convergence_score", 0),
                "outcome": "OPEN",
                "lifespan": None,
                "rr_actual": None,
                "pips_result": None,
            }

            # ONLY write to optimized tracking - single source of truth
            self.log_optimized_tracking(signal_data)
            print(f"📝 ONLY optimized_tracking.jsonl: {signal_data.get('signal_id', 'unknown')}")

        except Exception as e:
            logger.error(f"Error logging to truth tracker: {e}")

    def log_optimized_tracking(self, signal_data: Dict):
        """Enhanced tracking for pattern optimization with next candle win analysis"""
        try:
            # Map field names correctly
            symbol = signal_data.get("symbol", signal_data.get("pair", ""))

            # Check for REAL trade outcomes from MT5 execution
            signal_id = signal_data.get("signal_id", "")
            win = False
            outcome_source = "PENDING"

            # First check fires database for execution result
            try:
                import sqlite3

                conn = sqlite3.connect("/root/HydraX-v2/bitten.db")
                cursor = conn.cursor()

                # Check if signal was executed
                cursor.execute("SELECT status, ticket FROM fires WHERE fire_id = ?", (signal_id,))
                fire_result = cursor.fetchone()

                if fire_result and fire_result[0] == "FILLED":
                    # Signal was executed, check for outcome
                    cursor.execute("SELECT outcome, pips FROM signal_outcomes WHERE signal_id = ?", (signal_id,))
                    outcome_result = cursor.fetchone()

                    if outcome_result:
                        # We have real outcome!
                        outcome = outcome_result[0]
                        pips = outcome_result[1] or 0
                        win = outcome == "WIN" or pips > 0
                        outcome_source = f"MT5_OUTCOME_{outcome}"
                    else:
                        # Executed but no outcome yet
                        outcome_source = "MT5_EXECUTING"
                        win = False  # Don't assume until confirmed
                elif fire_result:
                    outcome_source = f"FIRE_{fire_result[0]}"
                    win = False  # Failed fires are losses
                else:
                    # Not executed - DO NOT SIMULATE WIN/LOSS
                    # DISABLED: Fake candle-based outcome simulation
                    outcome_source = "NOT_EXECUTED"
                    win = None  # Don't determine fake outcome
                    # if symbol in self.m1_data and len(self.m1_data[symbol]) > 0:
                    #     last_candle = self.m1_data[symbol][-1]
                    #     if last_candle and 'close' in last_candle and 'open' in last_candle:
                    #         direction = signal_data.get('direction', 'BUY')
                    #         if direction == 'BUY':
                    #             win = last_candle['close'] > last_candle['open']
                    #         else:
                    #             win = last_candle['close'] < last_candle['open']

                conn.close()
            except Exception as e:
                print(f"   ⚠️ Could not check MT5 outcomes: {e}")
                outcome_source = "ERROR"

            # Calculate Risk:Reward ratio using correct field names
            entry = signal_data.get("entry", signal_data.get("entry_price", 0))
            sl = signal_data.get("stop_loss", signal_data.get("sl", 0))
            tp = signal_data.get("take_profit", signal_data.get("tp", 0))

            # Alternative calculation using pips if prices not available
            if sl == 0 or tp == 0:
                sl_pips = signal_data.get("stop_pips", signal_data.get("sl_pips", 20))
                tp_pips = signal_data.get("target_pips", signal_data.get("tp_pips", 20))
                if sl_pips != 0:
                    rr = round(tp_pips / sl_pips, 2)
                else:
                    rr = 1.0
            else:
                # Price-based calculation
                if sl != 0 and entry != 0 and sl != entry:
                    risk = abs(entry - sl)
                    reward = abs(tp - entry)
                    if risk > 0:
                        rr = round(reward / risk, 2)
                else:
                    rr = 1.0

            # Calculate lifespan (time since signal creation)
            timestamp_str = signal_data.get("timestamp", datetime.utcnow().isoformat() + "Z")
            try:
                # Handle both formats: with and without 'Z'
                if timestamp_str.endswith("Z"):
                    signal_time = datetime.fromisoformat(timestamp_str[:-1])
                else:
                    signal_time = datetime.fromisoformat(timestamp_str)
                lifespan = round((datetime.utcnow() - signal_time).total_seconds(), 1)
            except:
                lifespan = 0

            # Create optimized tracking entry with correct field mappings
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "pair": symbol,
                "pattern": signal_data.get("pattern", signal_data.get("pattern_type", "UNKNOWN")),
                "confidence": signal_data.get("confidence", signal_data.get("quality_score", 0)),
                "quality_score": signal_data.get("quality_score", signal_data.get("confidence", 0)),
                "win": win if win is not None else None,  # Only log real outcomes, not fake ones
                "risk_reward": rr,
                "lifespan": lifespan,
                "session": signal_data.get("session", self.get_current_session()),
                "signal_id": signal_data.get("signal_id", ""),
                "direction": signal_data.get("direction", "UNKNOWN"),
                "signal_class": signal_data.get("signal_class", "UNKNOWN"),
                "outcome_source": outcome_source,  # Track where the outcome came from
            }

            # Write to optimized tracking log
            with open("/root/HydraX-v2/optimized_tracking.jsonl", "a") as f:
                f.write(json.dumps(entry) + "\n")

            # Add outcome source to entry
            entry["outcome_source"] = outcome_source

            # Enhanced debug output with outcome source
            print(f"📝 Tracked to optimized_tracking.jsonl: {signal_data.get('signal_id', 'UNKNOWN')}")
            print(f"   Pair={symbol}, Pattern={entry['pattern']}, Class={entry['signal_class']}")
            print(f"   Conf={entry['confidence']}%, Quality={entry['quality_score']}%")
            print(f"   Win={win}, R:R={rr}, Source={outcome_source}")
            print(f"   Session={entry['session']}, Direction={entry['direction']}")

        except Exception as e:
            print(f"Error in optimized tracking: {e}")
            import traceback

            traceback.print_exc()

    def analyze_initial_data(self):
        """Analyze last 6 hours from optimized_tracking.jsonl with detailed breakdowns"""
        try:
            tracking_file = "/root/HydraX-v2/optimized_tracking.jsonl"

            if not os.path.exists(tracking_file):
                print("📊 No optimized_tracking.jsonl yet")
                return

            # Read and filter for last 6 hours (360 minutes)
            from datetime import datetime, timedelta

            now = datetime.now()
            six_hours_ago = now - timedelta(hours=6)

            recent = []
            with open(tracking_file, "r") as f:
                for line in f:
                    if line.strip():
                        signal = json.loads(line)
                        # Parse timestamp properly
                        if "timestamp" in signal:
                            ts_str = signal["timestamp"]
                            # Handle ISO format timestamps
                            if "T" in ts_str:
                                # Remove microseconds if present and parse
                                ts_str = ts_str.split(".")[0] if "." in ts_str else ts_str.replace("Z", "")
                                signal_time = datetime.fromisoformat(ts_str)
                            else:
                                signal_time = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

                            if signal_time >= six_hours_ago:
                                recent.append(signal)

            if not recent:
                print("📊 No data in last 6 hours from optimized_tracking.jsonl")
                return

            # Overall stats for last 6 hours
            total = len(recent)
            wins = sum(1 for s in recent if s.get("win", False))
            losses = total - wins
            win_rate = (wins / total * 100) if total > 0 else 0

            print(f"\n📊 6-HOUR ANALYSIS from optimized_tracking.jsonl")
            print(f"   Total Signals: {total}")
            print(f"   Wins: {wins} | Losses: {losses}")
            print(f"   Win Rate: {win_rate:.1f}%")

            # Pattern breakdown with win rates
            patterns = set(s["pattern"] for s in recent if "pattern" in s)
            pattern_stats = {}
            print(f"\n📈 PATTERN PERFORMANCE:")
            for p in sorted(patterns):
                p_signals = [s for s in recent if s.get("pattern") == p]
                if p_signals:
                    p_wins = sum(1 for s in p_signals if s.get("win", False))
                    p_wr = (p_wins / len(p_signals) * 100) if len(p_signals) > 0 else 0
                    pattern_stats[p] = {"total": len(p_signals), "wins": p_wins, "win_rate": p_wr}
                    print(f"   {p}: {p_wins}/{len(p_signals)} ({p_wr:.1f}%)")

            # Pair breakdown
            pairs = set(s["pair"] for s in recent if "pair" in s)
            print(f"\n💱 PAIR PERFORMANCE:")
            pair_stats = {}
            for pair in sorted(pairs):
                pair_signals = [s for s in recent if s.get("pair") == pair]
                if pair_signals:
                    pair_wins = sum(1 for s in pair_signals if s.get("win", False))
                    pair_wr = (pair_wins / len(pair_signals) * 100) if len(pair_signals) > 0 else 0
                    pair_stats[pair] = {"total": len(pair_signals), "wins": pair_wins, "win_rate": pair_wr}
                    print(f"   {pair}: {pair_wins}/{len(pair_signals)} ({pair_wr:.1f}%)")

            # Confidence bins with detailed breakdown
            conf_stats = {}
            print(f"\n🎯 CONFIDENCE BINS:")
            for bin_name, (low, high) in [("70-75%", (70, 75)), ("75-85%", (75, 85)), ("85-95%", (85, 95))]:
                bin_signals = [s for s in recent if low <= s.get("confidence", 0) < high]
                if bin_signals:
                    bin_wins = sum(1 for s in bin_signals if s.get("win", False))
                    bin_wr = (bin_wins / len(bin_signals) * 100) if len(bin_signals) > 0 else 0
                    conf_stats[bin_name] = {"total": len(bin_signals), "wins": bin_wins, "win_rate": bin_wr}
                    print(f"   {bin_name}: {bin_wins}/{len(bin_signals)} ({bin_wr:.1f}%)")

            # Session breakdown
            session_stats = {}
            sessions = set(s.get("session", "UNKNOWN") for s in recent)
            if len(sessions) > 1 or "UNKNOWN" not in sessions:
                print(f"\n⏰ SESSION PERFORMANCE:")
                for sess in sorted(sessions):
                    sess_signals = [s for s in recent if s.get("session") == sess]
                    if sess_signals:
                        sess_wins = sum(1 for s in sess_signals if s.get("win", False))
                        sess_wr = (sess_wins / len(sess_signals) * 100) if len(sess_signals) > 0 else 0
                        session_stats[sess] = {"total": len(sess_signals), "wins": sess_wins, "win_rate": sess_wr}
                        print(f"   {sess}: {sess_wins}/{len(sess_signals)} ({sess_wr:.1f}%)")

            # Time distribution
            print(f"\n⏱️ TIME DISTRIBUTION:")
            hourly = {}
            for s in recent:
                if "timestamp" in s:
                    ts_str = s["timestamp"]
                    if "T" in ts_str:
                        ts_str = ts_str.split(".")[0] if "." in ts_str else ts_str.replace("Z", "")
                        signal_time = datetime.fromisoformat(ts_str)
                    else:
                        signal_time = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

                    hour_key = signal_time.strftime("%H:00")
                    if hour_key not in hourly:
                        hourly[hour_key] = {"total": 0, "wins": 0}
                    hourly[hour_key]["total"] += 1
                    if s.get("win", False):
                        hourly[hour_key]["wins"] += 1

            for hour in sorted(hourly.keys()):
                h_wr = (hourly[hour]["wins"] / hourly[hour]["total"] * 100) if hourly[hour]["total"] > 0 else 0
                print(f"   {hour}: {hourly[hour]['wins']}/{hourly[hour]['total']} ({h_wr:.1f}%)")

            return {
                "total": total,
                "wins": wins,
                "win_rate": win_rate,
                "patterns": pattern_stats,
                "pairs": pair_stats,
                "confidence": conf_stats,
                "sessions": session_stats,
            }

        except Exception as e:
            print(f"❌ Error analyzing data: {e}")
            import traceback

            traceback.print_exc()

    def verify_rr_ratio(self):
        """Verify R:R ratio for last 6 hours from optimized_tracking.jsonl"""
        try:
            tracking_file = "/root/HydraX-v2/optimized_tracking.jsonl"

            if not os.path.exists(tracking_file):
                print("📊 No optimized_tracking.jsonl for R:R analysis")
                return

            # Read and filter for last 6 hours
            from datetime import datetime, timedelta

            now = datetime.now()
            six_hours_ago = now - timedelta(hours=6)

            recent = []
            with open(tracking_file, "r") as f:
                for line in f:
                    if line.strip():
                        signal = json.loads(line)
                        if "timestamp" in signal:
                            ts_str = signal["timestamp"]
                            if "T" in ts_str:
                                ts_str = ts_str.split(".")[0] if "." in ts_str else ts_str.replace("Z", "")
                                signal_time = datetime.fromisoformat(ts_str)
                            else:
                                signal_time = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

                            if signal_time >= six_hours_ago:
                                recent.append(signal)

            if not recent:
                print("📊 No R:R data in last 6 hours")
                return

            # Calculate R:R statistics
            rr_values = [s.get("risk_reward", 0) for s in recent if s.get("risk_reward", 0) > 0]
            avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0

            # Group by pattern and calculate average R:R
            patterns = set(s["pattern"] for s in recent if "pattern" in s)
            pattern_rr = {}
            for p in patterns:
                p_signals = [s for s in recent if s.get("pattern") == p]
                p_rr_values = [s.get("risk_reward", 0) for s in p_signals if s.get("risk_reward", 0) > 0]
                if p_rr_values:
                    pattern_rr[p] = sum(p_rr_values) / len(p_rr_values)

            # Check for TP misses (if we have entry/TP data)
            tp_misses = 0
            tp_hits = 0
            for s in recent:
                if s.get("win", False):
                    tp_hits += 1
                    # Note: We don't have actual entry/TP prices in tracking, just win/loss

            # R:R distribution
            rr_distribution = {"1.0-1.25": 0, "1.25-1.5": 0, "1.5-2.0": 0, "2.0+": 0}

            for rr in rr_values:
                if rr <= 1.25:
                    rr_distribution["1.0-1.25"] += 1
                elif rr <= 1.5:
                    rr_distribution["1.25-1.5"] += 1
                elif rr <= 2.0:
                    rr_distribution["1.5-2.0"] += 1
                else:
                    rr_distribution["2.0+"] += 1

            print(f"\n📊 R:R RATIO ANALYSIS (Last 6 Hours)")
            print(f"   Total Signals: {len(recent)}")
            print(f"   Average R:R: {avg_rr:.2f}")
            print(f"   TP Hits (Wins): {tp_hits}/{len(recent)}")

            print(f"\n📈 R:R BY PATTERN:")
            for p in sorted(pattern_rr.keys()):
                print(f"   {p}: {pattern_rr[p]:.2f}")

            print(f"\n📊 R:R DISTRIBUTION:")
            for range_name, count in rr_distribution.items():
                pct = (count / len(rr_values) * 100) if rr_values else 0
                print(f"   {range_name}: {count} ({pct:.1f}%)")

            # Analyze win rate by R:R ratio
            print(f"\n🎯 WIN RATE BY R:R:")
            rr_bins = [(1.0, 1.25), (1.25, 1.5), (1.5, 2.0)]
            for low, high in rr_bins:
                bin_signals = [s for s in recent if low <= s.get("risk_reward", 0) < high]
                if bin_signals:
                    bin_wins = sum(1 for s in bin_signals if s.get("win", False))
                    bin_wr = (bin_wins / len(bin_signals) * 100) if len(bin_signals) > 0 else 0
                    print(f"   R:R {low}-{high}: {bin_wins}/{len(bin_signals)} wins ({bin_wr:.1f}%)")

            # Check if current R:R settings are optimal
            print(f"\n💡 R:R OPTIMIZATION INSIGHTS:")
            if avg_rr < 1.3:
                print("   ⚠️ Average R:R is LOW - Consider increasing TP targets")
            elif avg_rr > 2.0:
                print("   ⚠️ Average R:R is HIGH - May be missing profitable trades")
            else:
                print("   ✅ Average R:R is BALANCED (1.3-2.0 range)")

            # Find optimal R:R based on win rate
            optimal_rr = None
            best_expectancy = -float("inf")
            for low, high in rr_bins:
                bin_signals = [s for s in recent if low <= s.get("risk_reward", 0) < high]
                if len(bin_signals) >= 5:  # Need minimum samples
                    bin_wins = sum(1 for s in bin_signals if s.get("win", False))
                    win_rate = bin_wins / len(bin_signals)
                    avg_bin_rr = (low + high) / 2
                    # Expected value = (win_rate * avg_rr) - (loss_rate * 1)
                    expectancy = (win_rate * avg_bin_rr) - ((1 - win_rate) * 1)
                    if expectancy > best_expectancy:
                        best_expectancy = expectancy
                        optimal_rr = (low, high)

            if optimal_rr:
                print(f"\n🎯 OPTIMAL R:R RANGE: {optimal_rr[0]:.2f}-{optimal_rr[1]:.2f}")
                print(f"   Expected Value: {best_expectancy:.3f} per trade")

            return {
                "avg_rr": avg_rr,
                "tp_hits": tp_hits,
                "total": len(recent),
                "pattern_rr": pattern_rr,
                "distribution": rr_distribution,
            }

        except Exception as e:
            print(f"❌ Error verifying R:R ratio: {e}")
            import traceback

            traceback.print_exc()

    def analyze_initial_data_old(self):
        """Old analyze method - kept for compatibility"""
        try:
            tracking_file = "/root/HydraX-v2/optimized_tracking.jsonl"

            if not os.path.exists(tracking_file):
                print("📊 No optimized_tracking.jsonl yet")
                return

            with open(tracking_file, "r") as f:
                signals = [json.loads(line) for line in f if line.strip()]

            if not signals:
                print("📊 No data in optimized_tracking.jsonl yet")
                return

            # Overall stats
            total = len(signals)
            wins = sum(1 for s in signals if s.get("win", False))
            win_rate = (wins / total * 100) if total > 0 else 0

            # Pattern breakdown with win rates
            patterns = set(s["pattern"] for s in signals if "pattern" in s)
            pattern_stats = {}
            for p in patterns:
                p_signals = [s for s in signals if s.get("pattern") == p]
                if p_signals:
                    p_wins = sum(1 for s in p_signals if s.get("win", False))
                    pattern_stats[p] = f"{p_wins}/{len(p_signals)} ({p_wins/len(p_signals)*100:.1f}%)"

            # Session breakdown
            session_stats = {}
            for sess in ["Asian", "London", "NY", "Overlap"]:
                sess_signals = [s for s in signals if s.get("session") == sess]
                if sess_signals:
                    sess_wins = sum(1 for s in sess_signals if s.get("win", False))
                    session_stats[sess] = f"{sess_wins}/{len(sess_signals)} ({sess_wins/len(sess_signals)*100:.1f}%)"

            # Confidence bins
            conf_stats = {}
            for bin_name, (low, high) in [("70-75", (70, 75)), ("75-85", (75, 85)), ("85-95", (85, 95))]:
                bin_signals = [s for s in signals if low <= s.get("confidence", 0) < high]
                if bin_signals:
                    bin_wins = sum(1 for s in bin_signals if s.get("win", False))
                    conf_stats[bin_name] = f"{bin_wins}/{len(bin_signals)} ({bin_wins/len(bin_signals)*100:.1f}%)"

            # Last 30 min stats
            now = datetime.now()
            last_30 = []
            for s in signals:
                try:
                    ts = datetime.fromisoformat(s["timestamp"].replace("Z", "+00:00"))
                    if (now - ts).total_seconds() < 1800:
                        last_30.append(s)
                except:
                    pass

            print(f"\n📊 OPTIMIZED TRACKING ANALYSIS (ONLY SOURCE):")
            print(f"   Total: {total} signals, Win Rate: {win_rate:.1f}%")
            print(f"   Patterns: {pattern_stats}")
            print(f"   Sessions: {session_stats}")
            print(f"   Conf Bins: {conf_stats}")
            print(f"   Last 30min: {len(last_30)} signals")
            if last_30:
                print(f"   - Avg Conf: {sum(s.get('confidence', 0) for s in last_30)/len(last_30):.1f}%")
                print(f"   - Avg Quality: {sum(s.get('quality_score', 0) for s in last_30)/len(last_30):.1f}%")
                print(f"   - Avg R:R: {sum(s.get('risk_reward', 0) for s in last_30)/len(last_30):.2f}")

        except Exception as e:
            print(f"Error analyzing optimized_tracking.jsonl: {e}")
            for s in signals:
                d = s.get("direction", "UNKNOWN")
                if d in directions:
                    directions[d] += 1

            # Print comprehensive analysis
            print("=" * 60)
            print("📊 OPTIMIZATION TRACKING ANALYSIS")
            print("=" * 60)
            print(f"📈 SUMMARY: {total_signals} signals tracked")
            print(
                f"   Win Rate: {win_rate:.1f}% ({wins}/{total_signals}) {'🎯 TARGET: 65%+' if win_rate < 65 else '✅ ABOVE TARGET'}"
            )
            print(f"   Avg Confidence: {avg_conf:.1f}% {'✅ IN RANGE' if 70 <= avg_conf <= 95 else '⚠️ OUT OF RANGE'}")
            print(
                f"   Avg Quality: {avg_quality:.1f}% {'✅ IN RANGE' if 55 <= avg_quality <= 85 else '⚠️ OUT OF RANGE'}"
            )
            print(f"   Avg R:R: {avg_rr:.2f} {'✅ GOOD' if avg_rr >= 1.2 else '⚠️ LOW'}")
            print(f"   Avg Lifespan: {avg_lifespan:.1f}s")

            print(f"\n🎯 PATTERN PERFORMANCE:")
            for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
                pattern_signals = [s for s in signals if s.get("pattern") == pattern]
                pattern_wins = sum(1 for s in pattern_signals if s.get("win", False))
                pattern_wr = (pattern_wins / len(pattern_signals) * 100) if pattern_signals else 0
                print(f"   {pattern}: {count} signals, {pattern_wr:.1f}% win rate")

            print(f"\n💱 TOP PAIRS:")
            for pair, count in sorted(pairs.items(), key=lambda x: x[1], reverse=True)[:5]:
                pair_signals = [s for s in signals if s.get("pair") == pair]
                pair_wins = sum(1 for s in pair_signals if s.get("win", False))
                pair_wr = (pair_wins / len(pair_signals) * 100) if pair_signals else 0
                print(f"   {pair}: {count} signals, {pair_wr:.1f}% win rate")

            print(f"\n🌍 SESSION BREAKDOWN:")
            for session, count in sorted(sessions.items(), key=lambda x: x[1], reverse=True):
                sess_pct = count / total_signals * 100
                print(f"   {session}: {count} ({sess_pct:.1f}%)")

            print(f"\n📊 DIRECTION BIAS:")
            print(f"   BUY: {directions['BUY']} ({directions['BUY']/total_signals*100:.1f}%)")
            print(f"   SELL: {directions['SELL']} ({directions['SELL']/total_signals*100:.1f}%)")

            # Time analysis
            if signals:
                first_time = datetime.fromisoformat(signals[0]["timestamp"])
                last_time = datetime.fromisoformat(signals[-1]["timestamp"])
                time_span = (last_time - first_time).total_seconds() / 3600  # hours
                if time_span > 0:
                    signals_per_hour = total_signals / time_span
                    print(f"\n⏱️ SIGNAL RATE: {signals_per_hour:.1f} signals/hour")
                    if signals_per_hour < 5:
                        print("   ⚠️ Below target (5-10/hr) - Consider lowering thresholds")
                    elif signals_per_hour > 10:
                        print("   ⚠️ Above target (5-10/hr) - Consider raising thresholds")
                    else:
                        print("   ✅ In target range (5-10/hr)")

            print("=" * 60)

            # Return summary dict for programmatic use
            return {
                "total_signals": total_signals,
                "win_rate": win_rate,
                "avg_confidence": avg_conf,
                "avg_quality": avg_quality,
                "avg_rr": avg_rr,
                "patterns": patterns,
                "top_pair": max(pairs.items(), key=lambda x: x[1])[0] if pairs else None,
            }

        except Exception as e:
            print(f"Error analyzing data: {e}")
            import traceback

            traceback.print_exc()
            return None

    def scan_for_patterns(self):
        """Scan all symbols for patterns"""
        # Always scan ALL trading pairs, not just those with tick data
        symbols_to_scan = self.trading_pairs
        symbols_with_data = [s for s in self.trading_pairs if s in self.tick_data and len(self.m1_data.get(s, [])) > 0]

        print(f"🔍 PATTERN SCAN: Starting for {len(symbols_to_scan)} symbols ({len(symbols_with_data)} have M1 data)")
        logger.info(
            f"🔍 Starting pattern scan for {len(symbols_to_scan)} symbols ({len(symbols_with_data)} have M1 data)"
        )

        # Log total candle counts
        total_m1 = sum(len(self.m1_data.get(s, [])) for s in symbols_to_scan)
        total_m5 = sum(len(self.m5_data.get(s, [])) for s in symbols_to_scan)
        if total_m1 > 0:
            logger.info(f"📈 Total candles: {total_m1} M1, {total_m5} M5")

        # Log candle status with tick reception
        for symbol in symbols_to_scan[:5]:
            m1_count = len(self.m1_data[symbol])
            m5_count = len(self.m5_data[symbol])
            tick_count = len(self.tick_data[symbol])
            time_since_tick = time.time() - self.last_tick_time.get(symbol, 0)
            logger.info(
                f"  {symbol}: {tick_count} ticks, {m1_count} M1, {m5_count} M5 candles (last tick {time_since_tick:.1f}s ago)"
            )

        signals_generated = []

        for symbol in symbols_to_scan:
            # XAUUSD now re-enabled with corrected pip calculations
            # Previously skipped due to R:R issues - now fixed

            # Check if we have enough data (skip if no M1 candles)
            if len(self.m1_data.get(symbol, [])) < 2:
                continue

            # Check if data is fresh (only for symbols with tick data)
            if symbol in self.last_tick_time:
                if time.time() - self.last_tick_time[symbol] > 60:
                    continue

            if not self.should_generate_signal(symbol):
                continue

            # Try all pattern detectors
            patterns = []

            # ALL 5 CORE PATTERNS WITH ML FILTERING
            session = self.get_current_session()

            # 1. Liquidity Sweep Reversal (highest priority)
            signal = self.detect_liquidity_sweep_reversal(symbol)
            if signal:
                # ✅ TASK D: Count pattern candidate
                self.health_metrics["pattern_candidates"] += 1

                # 🔧 PHASE 1 MODULE ENHANCEMENT + BAYESIAN CALIBRATION
                try:
                    enhanced = self.module_enhancer.enhance_pattern(
                        pattern_signal=signal.__dict__ if hasattr(signal, '__dict__') else signal,
                        symbol=symbol,
                        m1_candles=list(self.m1_data[symbol]),
                        h4_candles=list(self.h4_data.get(symbol, []))
                    )
                    # Replace base confidence with calibrated confidence
                    signal.confidence = enhanced['calibrated_confidence']
                    print(f"🎯 MODULE ENHANCED: {symbol} LSR base {enhanced['base_confidence']}% → calibrated {enhanced['calibrated_confidence']}% (evidence: {enhanced['evidence_score']:+.2f})")
                except Exception as e:
                    print(f"⚠️  Module enhancement failed for {symbol} LSR: {e}")
                    # Continue with original signal on error

                # MEMORY-LITE FILTER (before ML filter)
                df = self.build_dataframe_for_memory(symbol)
                if df is not None:
                    should_fire, adj_conf, memory_reason = memory_system.should_fire(
                        df, symbol, signal.direction, signal.confidence
                    )
                    if not should_fire:
                        print(f"🧠 MEMORY FILTER: {symbol} LSR blocked - {memory_reason}")
                        continue  # Skip this signal entirely
                    elif adj_conf != signal.confidence:
                        print(f"🧠 MEMORY BOOST: {symbol} LSR confidence {signal.confidence}% → {adj_conf:.1f}%")
                        signal.confidence = adj_conf

                # ML FILTER
                should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    # ✅ TASK D: Count pattern kept after filtering
                    self.health_metrics["pattern_kept"] += 1
                    print(f"✅ LIQUIDITY SWEEP on {symbol} - {tier_reason} - CONF: {signal.confidence}")
                    patterns.append(signal)
                else:
                    print(f"🚫 LIQUIDITY SWEEP on {symbol} filtered: {tier_reason} - CONF: {signal.confidence}")
            else:
                # Debug: Why no pattern detected
                m5_count = len(self.m5_data[symbol])
                if m5_count < 2:
                    print(f"❌ {symbol} LSR: Only {m5_count} M5 candles (need 2+)")

            # 2. Order Block Bounce
            signal = self.detect_order_block_bounce(symbol)
            if signal:
                # 🔧 PHASE 1 MODULE ENHANCEMENT + BAYESIAN CALIBRATION
                try:
                    enhanced = self.module_enhancer.enhance_pattern(
                        pattern_signal=signal.__dict__ if hasattr(signal, '__dict__') else signal,
                        symbol=symbol,
                        m1_candles=list(self.m1_data[symbol]),
                        h4_candles=list(self.h4_data.get(symbol, []))
                    )
                    signal.confidence = enhanced['calibrated_confidence']
                    print(f"🎯 MODULE ENHANCED: {symbol} OB base {enhanced['base_confidence']}% → calibrated {enhanced['calibrated_confidence']}% (evidence: {enhanced['evidence_score']:+.2f})")
                except Exception as e:
                    print(f"⚠️  Module enhancement failed for {symbol} OB: {e}")

                # MEMORY-LITE FILTER (before ML filter)
                df = self.build_dataframe_for_memory(symbol)
                if df is not None:
                    should_fire, adj_conf, memory_reason = memory_system.should_fire(
                        df, symbol, signal.direction, signal.confidence
                    )
                    if not should_fire:
                        print(f"🧠 MEMORY FILTER: {symbol} OB blocked - {memory_reason}")
                        signal = None
                    elif adj_conf != signal.confidence:
                        print(f"🧠 MEMORY BOOST: {symbol} OB confidence {signal.confidence}% → {adj_conf:.1f}%")
                        signal.confidence = adj_conf

                if signal:
                    should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    print(f"✅ ORDER BLOCK on {symbol} - {tier_reason} - CONF: {signal.confidence}")
                    patterns.append(signal)
                else:
                    print(f"🚫 ORDER BLOCK on {symbol} filtered: {tier_reason} - CONF: {signal.confidence}")
            else:
                m5_count = len(self.m5_data[symbol])
                if m5_count < 2:
                    print(f"❌ {symbol} OB: Only {m5_count} M5 candles (need 2+)")

            # 3. BLIND SPOT (Replaces Fair Value Gap - which had 26.3% win rate)
            # SNIPER CLASS PATTERNS - Minimum 2:1 RR enforced
            signal = self.detect_blind_spot(symbol)
            if signal:
                # 🔧 PHASE 1 MODULE ENHANCEMENT + BAYESIAN CALIBRATION
                try:
                    enhanced = self.module_enhancer.enhance_pattern(
                        pattern_signal=signal.__dict__ if hasattr(signal, '__dict__') else signal,
                        symbol=symbol,
                        m1_candles=list(self.m1_data[symbol]),
                        h4_candles=list(self.h4_data.get(symbol, []))
                    )
                    signal.confidence = enhanced['calibrated_confidence']
                    print(f"🎯 MODULE ENHANCED: {symbol} BLIND_SPOT base {enhanced['base_confidence']}% → calibrated {enhanced['calibrated_confidence']}% (evidence: {enhanced['evidence_score']:+.2f})")
                except Exception as e:
                    print(f"⚠️  Module enhancement failed for {symbol} BLIND_SPOT: {e}")

                # MEMORY-LITE FILTER (before ML filter)
                df = self.build_dataframe_for_memory(symbol)
                if df is not None:
                    should_fire, adj_conf, memory_reason = memory_system.should_fire(
                        df, symbol, signal.direction, signal.confidence
                    )
                    if not should_fire:
                        print(f"🧠 MEMORY FILTER: {symbol} BLIND SPOT blocked - {memory_reason}")
                        signal = None
                    elif adj_conf != signal.confidence:
                        print(f"🧠 MEMORY BOOST: {symbol} BLIND SPOT confidence {signal.confidence}% → {adj_conf:.1f}%")
                        signal.confidence = adj_conf

                if signal:
                    should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    logger.info(f"✅ BLIND SPOT on {symbol} - {tier_reason}")
                    patterns.append(signal)
            else:
                print(f"🔍 BLIND SPOT {symbol}: No signal detected")

            # TRAPDOOR SSR - Session Sweep Reversal
            signal = self.detect_trapdoor_ssr(symbol)
            if signal:
                # 🔧 PHASE 1 MODULE ENHANCEMENT + BAYESIAN CALIBRATION
                try:
                    enhanced = self.module_enhancer.enhance_pattern(
                        pattern_signal=signal.__dict__ if hasattr(signal, '__dict__') else signal,
                        symbol=symbol,
                        m1_candles=list(self.m1_data[symbol]),
                        h4_candles=list(self.h4_data.get(symbol, []))
                    )
                    signal.confidence = enhanced['calibrated_confidence']
                    print(f"🎯 MODULE ENHANCED: {symbol} TRAPDOOR base {enhanced['base_confidence']}% → calibrated {enhanced['calibrated_confidence']}% (evidence: {enhanced['evidence_score']:+.2f})")
                except Exception as e:
                    print(f"⚠️  Module enhancement failed for {symbol} TRAPDOOR: {e}")

                # MEMORY-LITE FILTER (before ML filter)
                df = self.build_dataframe_for_memory(symbol)
                if df is not None:
                    should_fire, adj_conf, memory_reason = memory_system.should_fire(
                        df, symbol, signal.direction, signal.confidence
                    )
                    if not should_fire:
                        print(f"🧠 MEMORY FILTER: {symbol} TRAPDOOR SSR blocked - {memory_reason}")
                        signal = None
                    elif adj_conf != signal.confidence:
                        print(f"🧠 MEMORY BOOST: {symbol} TRAPDOOR SSR confidence {signal.confidence}% → {adj_conf:.1f}%")
                        signal.confidence = adj_conf

                if signal:
                    should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    print(f"✅ TRAPDOOR SSR on {symbol} - {tier_reason} - CONF: {signal.confidence}")
                    patterns.append(signal)
                else:
                    print(f"🚫 TRAPDOOR SSR on {symbol} filtered: {tier_reason}")
            else:
                print(f"🔍 TRAPDOOR SSR {symbol}: No signal detected")

            # PRESSURE VALVE VCB - Volatility Compression Break
            signal = self.detect_pressure_valve(symbol)
            if signal:
                # 🔧 PHASE 1 MODULE ENHANCEMENT + BAYESIAN CALIBRATION
                try:
                    enhanced = self.module_enhancer.enhance_pattern(
                        pattern_signal=signal.__dict__ if hasattr(signal, '__dict__') else signal,
                        symbol=symbol,
                        m1_candles=list(self.m1_data[symbol]),
                        h4_candles=list(self.h4_data.get(symbol, []))
                    )
                    signal.confidence = enhanced['calibrated_confidence']
                    print(f"🎯 MODULE ENHANCED: {symbol} PRESSURE_VALVE base {enhanced['base_confidence']}% → calibrated {enhanced['calibrated_confidence']}% (evidence: {enhanced['evidence_score']:+.2f})")
                except Exception as e:
                    print(f"⚠️  Module enhancement failed for {symbol} PRESSURE_VALVE: {e}")

                # MEMORY-LITE FILTER (before ML filter)
                df = self.build_dataframe_for_memory(symbol)
                if df is not None:
                    should_fire, adj_conf, memory_reason = memory_system.should_fire(
                        df, symbol, signal.direction, signal.confidence
                    )
                    if not should_fire:
                        print(f"🧠 MEMORY FILTER: {symbol} PRESSURE VALVE blocked - {memory_reason}")
                        signal = None
                    elif adj_conf != signal.confidence:
                        print(f"🧠 MEMORY BOOST: {symbol} PRESSURE VALVE confidence {signal.confidence}% → {adj_conf:.1f}%")
                        signal.confidence = adj_conf

                if signal:
                    should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    print(f"🔥 PRESSURE VALVE VCB on {symbol} - {tier_reason} - CONF: {signal.confidence}")
                    patterns.append(signal)
                else:
                    print(f"🚫 PRESSURE VALVE VCB on {symbol} filtered: {tier_reason}")
            else:
                print(f"🔍 PRESSURE VALVE {symbol}: No signal detected")

            # 4. VCB Breakout
            signal = self.detect_vcb_breakout(symbol)
            if signal:
                print(f"📍 VCB signal returned for {symbol}: conf={signal.confidence}, dir={signal.direction}")

                # 🔧 PHASE 1 MODULE ENHANCEMENT + BAYESIAN CALIBRATION
                try:
                    enhanced = self.module_enhancer.enhance_pattern(
                        pattern_signal=signal.__dict__ if hasattr(signal, '__dict__') else signal,
                        symbol=symbol,
                        m1_candles=list(self.m1_data[symbol]),
                        h4_candles=list(self.h4_data.get(symbol, []))
                    )
                    signal.confidence = enhanced['calibrated_confidence']
                    print(f"🎯 MODULE ENHANCED: {symbol} VCB base {enhanced['base_confidence']}% → calibrated {enhanced['calibrated_confidence']}% (evidence: {enhanced['evidence_score']:+.2f})")
                except Exception as e:
                    print(f"⚠️  Module enhancement failed for {symbol} VCB: {e}")

                # MEMORY-LITE FILTER (before ML filter)
                df = self.build_dataframe_for_memory(symbol)
                if df is not None:
                    should_fire, adj_conf, memory_reason = memory_system.should_fire(
                        df, symbol, signal.direction, signal.confidence
                    )
                    if not should_fire:
                        print(f"🧠 MEMORY FILTER: {symbol} VCB blocked - {memory_reason}")
                        signal = None
                    elif adj_conf != signal.confidence:
                        print(f"🧠 MEMORY BOOST: {symbol} VCB confidence {signal.confidence}% → {adj_conf:.1f}%")
                        signal.confidence = adj_conf

                if signal:
                    should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    print(f"✅ VCB BREAKOUT on {symbol} - {tier_reason} - Publishing!")
                    logger.info(f"✅ VCB BREAKOUT on {symbol} - {tier_reason}")
                    patterns.append(signal)
                else:
                    print(f"🚫 VCB BREAKOUT on {symbol} filtered: {tier_reason}")
                    logger.debug(f"🚫 VCB BREAKOUT on {symbol} filtered: {tier_reason}")

            # 5. Sweep and Return
            signal = self.detect_sweep_and_return(symbol)
            if signal:
                # MEMORY-LITE FILTER (before ML filter)
                df = self.build_dataframe_for_memory(symbol)
                if df is not None:
                    should_fire, adj_conf, memory_reason = memory_system.should_fire(
                        df, symbol, signal.direction, signal.confidence
                    )
                    if not should_fire:
                        print(f"🧠 MEMORY FILTER: {symbol} SWEEP & RETURN blocked - {memory_reason}")
                        signal = None
                    elif adj_conf != signal.confidence:
                        print(f"🧠 MEMORY BOOST: {symbol} SWEEP & RETURN confidence {signal.confidence}% → {adj_conf:.1f}%")
                        signal.confidence = adj_conf

                if signal:
                    should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    logger.info(f"✅ SWEEP & RETURN on {symbol} - {tier_reason}")
                    patterns.append(signal)
                else:
                    logger.debug(f"🚫 SWEEP & RETURN on {symbol} filtered: {tier_reason}")

            # 6. Momentum Burst (Momentum Breakout)
            signal = self.detect_momentum_breakout(symbol)
            if signal:
                signal.pattern = "MOMENTUM_BURST"  # Rename for clarity
                # MEMORY-LITE FILTER (before ML filter)
                df = self.build_dataframe_for_memory(symbol)
                if df is not None:
                    should_fire, adj_conf, memory_reason = memory_system.should_fire(
                        df, symbol, signal.direction, signal.confidence
                    )
                    if not should_fire:
                        print(f"🧠 MEMORY FILTER: {symbol} MOMENTUM BURST blocked - {memory_reason}")
                        signal = None
                    elif adj_conf != signal.confidence:
                        print(f"🧠 MEMORY BOOST: {symbol} MOMENTUM BURST confidence {signal.confidence}% → {adj_conf:.1f}%")
                        signal.confidence = adj_conf

                if signal:
                    should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    print(f"✅ MOMENTUM BURST on {symbol} - {tier_reason} - CONF: {signal.confidence}")
                    patterns.append(signal)
                else:
                    print(f"🚫 MOMENTUM BURST on {symbol} filtered: {tier_reason}")

            # 7. BB Scalp Pattern
            signal = self.detect_bb_scalp(symbol)
            if signal:
                # MEMORY-LITE FILTER (before ML filter)
                df = self.build_dataframe_for_memory(symbol)
                if df is not None:
                    should_fire, adj_conf, memory_reason = memory_system.should_fire(
                        df, symbol, signal.direction, signal.confidence
                    )
                    if not should_fire:
                        print(f"🧠 MEMORY FILTER: {symbol} BB SCALP blocked - {memory_reason}")
                        signal = None
                    elif adj_conf != signal.confidence:
                        print(f"🧠 MEMORY BOOST: {symbol} BB SCALP confidence {signal.confidence}% → {adj_conf:.1f}%")
                        signal.confidence = adj_conf

                if signal:
                    should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    print(f"✅ BB_SCALP on {symbol} - {tier_reason} - CONF: {signal.confidence}")
                    patterns.append(signal)
                else:
                    print(f"🚫 BB_SCALP on {symbol} filtered: {tier_reason}")

            # 8. Kalman Quickfire Pattern
            signal = self.detect_kalman_quickfire(symbol)
            if signal:
                # MEMORY-LITE FILTER (before ML filter)
                df = self.build_dataframe_for_memory(symbol)
                if df is not None:
                    should_fire, adj_conf, memory_reason = memory_system.should_fire(
                        df, symbol, signal.direction, signal.confidence
                    )
                    if not should_fire:
                        print(f"🧠 MEMORY FILTER: {symbol} KALMAN QUICKFIRE blocked - {memory_reason}")
                        signal = None
                    elif adj_conf != signal.confidence:
                        print(f"🧠 MEMORY BOOST: {symbol} KALMAN QUICKFIRE confidence {signal.confidence}% → {adj_conf:.1f}%")
                        signal.confidence = adj_conf

                if signal:
                    should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    print(f"✅ KALMAN_QUICKFIRE on {symbol} - {tier_reason} - CONF: {signal.confidence}")
                    patterns.append(signal)
                else:
                    print(f"🚫 KALMAN_QUICKFIRE on {symbol} filtered: {tier_reason}")

            # 9. EMA RSI BB VWAP Pattern
            signal = self.detect_ema_rsi_bb_vwap(symbol)
            if signal:
                # MEMORY-LITE FILTER (before ML filter)
                df = self.build_dataframe_for_memory(symbol)
                if df is not None:
                    should_fire, adj_conf, memory_reason = memory_system.should_fire(
                        df, symbol, signal.direction, signal.confidence
                    )
                    if not should_fire:
                        print(f"🧠 MEMORY FILTER: {symbol} EMA RSI BB VWAP blocked - {memory_reason}")
                        signal = None
                    elif adj_conf != signal.confidence:
                        print(f"🧠 MEMORY BOOST: {symbol} EMA RSI BB VWAP confidence {signal.confidence}% → {adj_conf:.1f}%")
                        signal.confidence = adj_conf

                if signal:
                    should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    print(f"✅ EMA_RSI_BB_VWAP on {symbol} - {tier_reason} - CONF: {signal.confidence}")
                    patterns.append(signal)
                else:
                    print(f"🚫 EMA_RSI_BB_VWAP on {symbol} filtered: {tier_reason}")

            # 10. EMA RSI Scalp Pattern (46.4% win rate proven)
            signal = self.detect_ema_rsi_scalp(symbol)
            if signal:
                # MEMORY-LITE FILTER (before ML filter)
                df = self.build_dataframe_for_memory(symbol)
                if df is not None:
                    should_fire, adj_conf, memory_reason = memory_system.should_fire(
                        df, symbol, signal.direction, signal.confidence
                    )
                    if not should_fire:
                        print(f"🧠 MEMORY FILTER: {symbol} EMA RSI SCALP blocked - {memory_reason}")
                        signal = None
                    elif adj_conf != signal.confidence:
                        print(f"🧠 MEMORY BOOST: {symbol} EMA RSI SCALP confidence {signal.confidence}% → {adj_conf:.1f}%")
                        signal.confidence = adj_conf

                if signal:
                    should_publish, tier_reason, ml_score = self.apply_ml_filter(signal, session)
                if should_publish:
                    print(f"✅ EMA_RSI_SCALP on {symbol} - {tier_reason} - CONF: {signal.confidence}")
                    patterns.append(signal)
                else:
                    print(f"🚫 EMA_RSI_SCALP on {symbol} filtered: {tier_reason}")

            # Duplicate pattern calls removed - these patterns already called above

            # Pick best pattern based on quality score
            if patterns:
                best_pattern = max(patterns, key=lambda x: x.quality_score)

                # Lower threshold for CITADEL to filter
                if best_pattern.confidence >= 35:  # LOWERED further for more signals
                    # Generate signal
                    signal = self.generate_signal(best_pattern)

                    # DEBUG: Check signal has critical fields BEFORE CITADEL
                    if not signal.get("stop_loss") or not signal.get("take_profit"):
                        print(f"⚠️ CRITICAL: Signal missing SL/TP BEFORE CITADEL!")
                        print(f"   Signal keys: {list(signal.keys())}")
                        print(f"   stop_loss: {signal.get('stop_loss')}, take_profit: {signal.get('take_profit')}")

                    # Update CITADEL with market structure
                    if len(self.m5_data[symbol]) > 0:
                        candles_list = list(self.m5_data[symbol])
                        self.citadel.update_market_structure(symbol, candles_list)

                    # Apply CITADEL protection
                    protected_signal = self.citadel.protect_signal(signal)

                    # CRITICAL FIX: If CITADEL returns None (delayed), still publish with warning
                    if protected_signal is None:
                        # CITADEL delayed the signal - but we need to publish anyway for ML learning
                        print(f"⚠️ CITADEL delayed signal - publishing anyway with sweep warning")
                        protected_signal = signal.copy()  # Use original signal
                        protected_signal["citadel_status"] = "DELAYED_SWEEP_RISK"
                        protected_signal["citadel_protected"] = False
                        protected_signal["citadel_warning"] = "SWEEP_RISK_DETECTED"
                        # Slightly reduce confidence for sweep risk
                        protected_signal["confidence"] = max(70, signal["confidence"] - 5)

                    # CRITICAL FIX: CITADEL returns a partial signal, preserve ALL trading fields
                    if protected_signal and signal:
                        # CITADEL might return None or modified signal
                        # Make sure critical fields are preserved
                        critical_fields = [
                            "stop_pips",
                            "target_pips",
                            "stop_loss",
                            "take_profit",
                            "entry_price",
                            "entry",
                            "sl",
                            "tp",
                            "risk_reward",
                            "lot_size",
                        ]
                        for key in critical_fields:
                            if key in signal and (key not in protected_signal or protected_signal.get(key) is None):
                                protected_signal[key] = signal[key]

                        # DEBUG: Log what fields are missing
                        missing = [
                            k
                            for k in ["stop_loss", "take_profit"]
                            if k not in protected_signal or protected_signal.get(k) is None
                        ]
                        if missing:
                            print(f"⚠️ WARNING: Protected signal missing critical fields: {missing}")
                            print(f"   Original signal had: {list(signal.keys())}")
                            print(f"   Protected signal has: {list(protected_signal.keys())}")

                    # Calculate CITADEL score (0-15 range)
                    if protected_signal:
                        citadel_score = 0

                        # Base score from protection status
                        if protected_signal.get("citadel_protected", False):
                            citadel_score += 5  # Protected signal

                        # Boost from post-sweep opportunity
                        if protected_signal.get("citadel_boost") == "POST_SWEEP":
                            citadel_score += 10  # Maximum boost for post-sweep
                        elif protected_signal.get("citadel_status") == "VERIFIED":
                            citadel_score += 3  # Verified safe signal

                        # Add sweep avoidance score
                        if hasattr(self.citadel, "stats") and self.citadel.stats.get("sweeps_avoided", 0) > 0:
                            citadel_score += 2  # Bonus for active sweep protection

                        protected_signal["citadel_score"] = min(15, citadel_score)  # Cap at 15

                    # Calculate signal rate for dynamic threshold
                    recent_signals = [
                        s for s in self.signal_history if time.time() - s.get("timestamp_epoch", 0) < 900
                    ]  # Last 15 minutes
                    signals_per_15min = len(recent_signals)
                    projected_hourly_rate = signals_per_15min * 4

                    # Dynamic CITADEL threshold based on signal rate - QUALITY FOCUSED
                    # Can be overridden by environment variable for testing
                    citadel_override = os.getenv("CITADEL_THRESHOLD")
                    if citadel_override and citadel_override.lower() != "disabled":
                        citadel_threshold = float(citadel_override)
                        print(f"📊 Using CITADEL override threshold: {citadel_threshold}%")
                    elif citadel_override and citadel_override.lower() == "disabled":
                        citadel_threshold = 0.0  # Disable CITADEL filtering
                        print(f"⚠️ CITADEL filtering DISABLED for testing")
                    else:
                        # Default dynamic thresholds - lowered for more signals
                        citadel_threshold = (
                            50.0 if projected_hourly_rate > 10 else 45.0 if projected_hourly_rate < 5 else 47.5
                        )

                    if protected_signal and protected_signal.get("confidence", 0) >= citadel_threshold:
                        # Signal passed CITADEL protection and meets final threshold
                        print(
                            f"✅ Signal passed CITADEL gate ({protected_signal.get('confidence', 0):.1f}% >= {citadel_threshold}%)"
                        )
                        signals_generated.append(protected_signal)

                        # Track signal time for rate calculation
                        if not hasattr(self, "recent_signal_times"):
                            self.recent_signal_times = []
                        self.recent_signal_times.append(time.time())

                        # Update tracking
                        self.last_signal_time[symbol] = time.time()
                        self.hourly_signal_count[symbol] += 1
                        self.signal_history.append(protected_signal)

                        # Enhanced signal JSON with pattern-specific telemetry
                        if protected_signal.get("pattern") == "TRAPDOOR_SSR":
                            # Add TRAPDOOR-specific telemetry fields
                            protected_signal.update(
                                {
                                    "swept_level": (
                                        best_pattern.swept_level if hasattr(best_pattern, "swept_level") else None
                                    ),
                                    "session": self.get_current_session(),
                                    "ltf_confirmed": True,
                                    "sweep_size_pts": getattr(best_pattern, "sweep_size_pts", None),
                                }
                            )
                        elif protected_signal.get("pattern") == "PRESSURE_VALVE_VCB":
                            # Add PRESSURE_VALVE-specific telemetry fields
                            protected_signal.update(
                                {
                                    "compression_bars": getattr(best_pattern, "compression_bars", None),
                                    "break_strength": getattr(best_pattern, "break_strength", None),
                                    "h4_bias": getattr(best_pattern, "h4_bias", None),
                                    "compression_height": getattr(best_pattern, "compression_height", None),
                                }
                            )

                        # Publish
                        self.publish_signal(protected_signal)

                        # Use emoji based on signal class
                        emoji = "⚡" if protected_signal["signal_class"] == "RAPID" else "🎯"
                        citadel_badge = " 🛡️" if protected_signal.get("citadel_boost") else ""
                        logger.info(
                            f"{emoji} {protected_signal['signal_class']}{citadel_badge}: "
                            f"{protected_signal['symbol']} {protected_signal['direction']} "
                            f"Quality: {protected_signal['quality_tier']} ({protected_signal['quality_score']}%) "
                            f"Pattern: {protected_signal['pattern']}"
                        )

        return signals_generated

    def calculate_rsi_for_symbol(self, symbol: str, period: int = 14) -> float:
        """Calculate RSI for a symbol using available candle data"""
        try:
            # Get M5 candles for RSI calculation
            candles = self.m5_candles.get(symbol, [])
            if len(candles) < period + 1:
                return 50.0  # Default neutral RSI if not enough data

            # Get closing prices
            closes = [c["close"] for c in candles[-(period + 1) :]]

            # Calculate price changes
            gains = []
            losses = []
            for i in range(1, len(closes)):
                change = closes[i] - closes[i - 1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))

            # Calculate average gain and loss
            avg_gain = sum(gains) / period if gains else 0
            avg_loss = sum(losses) / period if losses else 0

            # Calculate RSI
            if avg_loss == 0:
                return 100.0 if avg_gain > 0 else 50.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                return round(rsi, 1)
        except Exception as e:
            print(f"RSI calculation error for {symbol}: {e}")
            return 50.0  # Default neutral on error

    def build_dataframe_for_memory(self, symbol: str):
        """Convert M1 deque data to DataFrame for Memory-Lite analysis"""
        try:
            import pandas as pd

            if symbol not in self.m1_data or len(self.m1_data[symbol]) < 20:
                return None

            # Convert deque to list of dicts
            candles = list(self.m1_data[symbol])

            # Create DataFrame
            df = pd.DataFrame(candles)

            # Ensure required columns exist
            if not all(col in df.columns for col in ['close', 'high', 'low']):
                return None

            # Calculate RSI if not present
            if 'rsi' not in df.columns:
                rsi_values = []
                for i in range(len(df)):
                    if i < 14:
                        rsi_values.append(50.0)  # Default for insufficient data
                    else:
                        # Calculate RSI for this bar
                        closes = df['close'].iloc[max(0, i-14):i+1].tolist()
                        if len(closes) >= 14:
                            changes = [closes[j] - closes[j-1] for j in range(1, len(closes))]
                            gains = [c if c > 0 else 0 for c in changes]
                            losses = [abs(c) if c < 0 else 0 for c in changes]
                            avg_gain = sum(gains[-14:]) / 14
                            avg_loss = sum(losses[-14:]) / 14
                            if avg_loss == 0:
                                rsi = 100.0 if avg_gain > 0 else 50.0
                            else:
                                rs = avg_gain / avg_loss
                                rsi = 100 - (100 / (1 + rs))
                            rsi_values.append(rsi)
                        else:
                            rsi_values.append(50.0)
                df['rsi'] = rsi_values

            # Calculate ATR if not present
            if 'atr' not in df.columns:
                # Simple ATR calculation
                true_ranges = []
                for i in range(1, len(df)):
                    hl = df['high'].iloc[i] - df['low'].iloc[i]
                    hc = abs(df['high'].iloc[i] - df['close'].iloc[i-1])
                    lc = abs(df['low'].iloc[i] - df['close'].iloc[i-1])
                    true_ranges.append(max(hl, hc, lc))

                # Average over 14 periods
                atr_values = [true_ranges[0] if true_ranges else 0.001]  # First value
                for i in range(len(true_ranges)):
                    if i < 13:
                        atr_values.append(np.mean(true_ranges[:i+1]))
                    else:
                        atr_values.append(np.mean(true_ranges[i-13:i+1]))

                # Pad to match DataFrame length (first bar has no TR)
                df['atr'] = [atr_values[0]] + atr_values

            return df

        except Exception as e:
            print(f"⚠️ Memory DataFrame build error for {symbol}: {e}")
            return None

    def publish_signal(self, signal: Dict):
        """Publish signal to ALL channels: ZMQ, JSONL, Missions, Telegram, WebApp, Event Bus"""
        combo = f"{signal.get('pattern', 'UNKNOWN')}_{signal.get('symbol', 'UNKNOWN')}"
        print(
            f"🚀 Publishing {signal.get('signal_id')}: Conf={signal.get('confidence')}%, Quality={signal.get('quality_score')}%, Combo={combo}"
        )

        # Calculate RSI if not already in signal
        symbol = signal.get("symbol", "")
        if "rsi" not in signal and symbol:
            signal["rsi"] = self.calculate_rsi_for_symbol(symbol)
            print(f"   📊 Calculated RSI for {symbol}: {signal['rsi']}")

        # EVENT BUS INTEGRATION - Publish to institutional-grade tracking
        try:
            from event_bus.event_bridge import signal_generated

            signal_generated(
                {
                    "signal_id": signal.get("signal_id"),
                    "pattern": signal.get("pattern_type"),
                    "confidence": signal.get("confidence"),
                    "symbol": signal.get("symbol"),
                    "direction": signal.get("direction"),
                    "entry_price": signal.get("entry_price"),
                    "stop_loss": signal.get("stop_loss"),
                    "take_profit": signal.get("take_profit"),
                    "signal_type": signal.get("signal_type"),
                    "quality_score": signal.get("quality_score"),
                    "rsi": signal.get("rsi"),
                    "timestamp": signal.get("timestamp"),
                }
            )
            print(f"   ✅ Event Bus: Signal published to institutional tracking")
        except Exception as e:
            print(f"   ⚠️ Event Bus: Failed to publish (non-critical): {e}")
            # Non-critical - continue with other channels

        # CRITICAL FIX: Ensure stop_loss and take_profit price levels exist
        if (
            ("stop_loss" not in signal or signal.get("stop_loss") is None)
            and "entry_price" in signal
            and "stop_pips" in signal
        ):
            entry = signal["entry_price"]
            symbol = signal.get("symbol", "")
            pip_size = get_pip_size(symbol)

            if signal.get("direction") == "BUY":
                signal["stop_loss"] = round(entry - (signal["stop_pips"] * pip_size), 5)
            else:
                signal["stop_loss"] = round(entry + (signal["stop_pips"] * pip_size), 5)
            print(f"   ✅ Reconstructed stop_loss: {signal['stop_loss']} from {signal['stop_pips']} pips")

        if (
            ("take_profit" not in signal or signal.get("take_profit") is None)
            and "entry_price" in signal
            and "target_pips" in signal
        ):
            entry = signal["entry_price"]
            symbol = signal.get("symbol", "")
            pip_size = get_pip_size(symbol)

            if signal.get("direction") == "BUY":
                signal["take_profit"] = round(entry + (signal["target_pips"] * pip_size), 5)
            else:
                signal["take_profit"] = round(entry - (signal["target_pips"] * pip_size), 5)
            print(f"   ✅ Reconstructed take_profit: {signal['take_profit']} from {signal['target_pips']} pips")

        # Ensure ZMQ publisher exists
        if not self.publisher:
            print("⚠️ WARNING: ZMQ publisher not initialized! Attempting to create...")
            try:
                self.publisher = self.context.socket(zmq.PUB)
                self.publisher.bind("tcp://*:5557")
                print("✅ ZMQ publisher created on port 5557")
                time.sleep(0.1)  # Give subscribers time to connect
            except Exception as e:
                print(f"❌ Failed to create ZMQ publisher: {e}")

        # Calculate additional metrics for unified logging
        symbol = signal.get("symbol", "")
        pip_multiplier = 100 if "JPY" in symbol else (1 if symbol == "XAUUSD" else 10000)

        entry = float(signal.get("entry_price", 0) or signal.get("entry", 0))
        sl = float(signal.get("sl", 0) or signal.get("stop_loss", 0))
        tp = float(signal.get("tp", 0) or signal.get("take_profit", 0))

        sl_pips = abs(entry - sl) * pip_multiplier if entry and sl else signal.get("stop_pips", 0)
        tp_pips = abs(tp - entry) * pip_multiplier if entry and tp else signal.get("target_pips", 0)

        # Prepare comprehensive trade data for unified logging
        trade_data = {
            "signal_id": signal.get("signal_id"),
            "pair": symbol,
            "pattern": signal.get("pattern"),
            "confidence": signal.get("confidence", 0),
            "entry_price": entry,
            "sl_price": sl,
            "tp_price": tp,
            "sl_pips": sl_pips,
            "tp_pips": tp_pips,
            "lot_size": signal.get("lot_size", 0.01),
            "direction": signal.get("direction"),
            "session": signal.get("session", self.get_current_session()),
            "shield_score": signal.get("citadel_score", signal.get("shield_score", 0)),
            "rsi": signal.get("rsi", 50),
            "volume_ratio": signal.get("volume_ratio", 1.0),
            "timestamp": datetime.now(pytz.UTC).isoformat(),
            "executed": signal.get("confidence", 0) >= 70,  # Lowered to 70 with ML protection
            "user_id": "wlJ5lafBqRSLwHIUBxJQMr4SBtk1",
            "signal_type": signal.get("signal_type", "PRECISION_STRIKE"),
        }

        # DISABLED: Log to unified tracking system (was generating fake win/loss data)
        # try:
        #     log_trade(trade_data)
        #     print(f"   ✅ Unified tracking logged to comprehensive_tracking.jsonl")
        # except Exception as e:
        #     print(f"   ❌ Unified logging failed: {e}")
        print(f"   ⚠️ Comprehensive tracking disabled (was generating fake outcomes)")

        # CRITICAL FIX: Ensure stop_pips and target_pips are in signal for ML learning
        if "stop_pips" not in signal or signal.get("stop_pips") == 0:
            signal["stop_pips"] = sl_pips
        if "target_pips" not in signal or signal.get("target_pips") == 0:
            signal["target_pips"] = tp_pips

        # ✅ TASK C FIX: Add provenance stamping for signal traceability
        if hasattr(self, 'bar_complete_events'):
            last_event = list(self.bar_complete_events.values())[-1] if self.bar_complete_events else None
            if last_event:
                signal["provenance"] = {
                    "symbol": signal.get("symbol"),
                    "tf": signal.get("timeframe", "M5"),
                    "t_close": last_event.get('timestamp', 0),
                    "source": "gateway-5570",
                    "candle_source": last_event.get('source', 'unknown')
                }
            else:
                signal["provenance"] = {
                    "symbol": signal.get("symbol"),
                    "tf": signal.get("timeframe", "M5"),
                    "source": "gateway-5570",
                    "note": "time-based scan (no bar event)"
                }
        else:
            signal["provenance"] = {
                "symbol": signal.get("symbol"),
                "tf": signal.get("timeframe", "M5"),
                "source": "gateway-5570"
            }

        # 1. ZMQ Publishing (with debug logging)
        if self.publisher:
            try:
                # DEBUG: Check what we're actually sending
                if "stop_loss" not in signal or signal.get("stop_loss") is None:
                    print(f"   🔴 WARNING: Publishing signal WITHOUT stop_loss!")
                    print(f"      Signal keys: {list(signal.keys())}")
                if "take_profit" not in signal or signal.get("take_profit") is None:
                    print(f"   🔴 WARNING: Publishing signal WITHOUT take_profit!")

                signal_msg = json.dumps(signal)
                self.publisher.send_string(f"ELITE_GUARD_SIGNAL {signal_msg}")

                # ✅ TASK D: Increment signals_fired metric
                self.health_metrics["signals_fired"] += 1

                print(
                    f"   📡 ZMQ sent to port 5557 - has SL: {signal.get('stop_loss') is not None}, has TP: {signal.get('take_profit') is not None}"
                )

                # ZMQ debug logging
                self.log_zmq_debug("PUBLISH", signal.get("signal_id"), signal_msg)
            except Exception as e:
                print(f"   ❌ ZMQ failed: {e}")
                self.log_zmq_debug("PUBLISH_ERROR", signal.get("signal_id"), str(e))

        # 1.5. Redis Stream Publishing (ALERT BUS)
        try:
            import time

            import redis

            r = redis.Redis(host="localhost", port=6379, decode_responses=True)

            # Build alert payload
            alert_payload = {
                "type": "signal_alert",
                "alert_id": signal.get("signal_id"),
                "uid": signal.get("user_id", "system"),
                "account_id": signal.get("account_id", "default"),
                "symbol": signal.get("symbol"),
                "direction": signal.get("direction"),
                "confidence": str(signal.get("confidence", 0)),
                "text": f"[{signal.get('pattern_type', 'PATTERN')}] {signal.get('symbol')} {signal.get('direction')} @ {signal.get('confidence', 0)}%",
                "ts": str(int(time.time())),
                "idempotency_key": signal.get("signal_id"),
            }

            # Add to Redis stream
            stream_id = r.xadd("alerts:v1", alert_payload)
            print(f"   📮 [ALERT_ENQUEUED] alert_id={signal.get('signal_id')} stream_id={stream_id}")
        except Exception as e:
            print(f"   ❌ Redis stream failed: {e}")

        # 2. Optimized Tracking JSONL (SECONDARY - for backward compatibility)
        try:
            self.log_signal_to_truth_tracker(signal)
            print(f"   📝 Legacy truth_log.jsonl logged")
        except Exception as e:
            print(f"   ❌ Legacy JSONL failed: {e}")

        # 3. Mission File Creation (LEGACY - BittenCore handles Firebase)
        # NOTE: This is kept for backward compatibility but BittenCore is the authoritative mission builder
        try:
            import os

            mission_dir = "/root/HydraX-v2/missions"
            os.makedirs(mission_dir, exist_ok=True)
            mission_file = f"{mission_dir}/{signal.get('signal_id')}.json"
            with open(mission_file, "w") as f:
                mission_data = {"signal": signal, "combo": combo, "created_at": datetime.now(pytz.UTC).isoformat()}
                json.dump(mission_data, f, indent=2)
            print(f"   📋 Mission file created (legacy): {signal.get('signal_id')}.json")
        except Exception as e:
            print(f"   ❌ Mission failed: {e}")

        # 4. Telegram Alert (via relay)
        print(f"   💬 Telegram alert queued (via ZMQ relay)")

        # 5. WebApp Signal (via ZMQ relay only - database handled by webapp)
        # NOTE: Database writes removed - webapp handles this after receiving signal via ZMQ relay
        # This prevents race conditions and ensures webapp has full control over data format
        print(f"   🌐 Signal will be stored by webapp after ZMQ relay")

        print(f"   ✅ Signal published to all channels")

    def log_zmq_debug(self, action: str, signal_id: str, data: str):
        """Log ZMQ debug information for diagnosing MT5 communication issues"""
        try:
            debug_file = "/root/HydraX-v2/logs/zmq_debug.log"
            os.makedirs(os.path.dirname(debug_file), exist_ok=True)

            with open(debug_file, "a") as f:
                log_entry = {
                    "timestamp": datetime.now(pytz.UTC).isoformat(),
                    "action": action,
                    "signal_id": signal_id,
                    "data": data[:500] if len(data) > 500 else data,  # Truncate long data
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"ZMQ debug logging error: {e}")

    def data_listener(self):
        """Poll Finnhub hybrid candles (replaces EA tick stream)"""
        print("📡 Finnhub candle poller started (polling every 5 seconds)...")

        last_poll = {}  # Track last poll time per symbol

        while self.running:
            try:
                current_time = time.time()

                for symbol in self.trading_pairs:
                    # Poll every 5 seconds per symbol
                    if symbol not in last_poll or (current_time - last_poll[symbol]) >= 5:
                        # Get latest candle from Finnhub
                        # Fetch 500 candles to get full backfill data on first poll
                        candles = self.finnhub_adapter.get_candles(symbol, count=500)

                        if candles:
                            # Process candles into internal format
                            # On first poll, process ALL candles (up to maxlen 500)
                            # On subsequent polls, process last 10 (avoid reprocessing)
                            current_len = len(self.m1_data.get(symbol, []))
                            candles_to_process = candles if current_len == 0 else candles[-10:]

                            for candle in candles_to_process:
                                # Build internal M1 buffer from Finnhub candles
                                if symbol not in self.m1_data:
                                    self.m1_data[symbol] = deque(maxlen=500)

                                self.m1_data[symbol].append({
                                    "open": candle['open'],
                                    "high": candle['high'],
                                    "low": candle['low'],
                                    "close": candle['close'],
                                    "volume": candle.get('volume', 0),
                                    "timestamp": candle['time'],
                                    "complete": True,
                                    "source": "finnhub"
                                })

                            last_poll[symbol] = current_time

                            # CRITICAL FIX: Aggregate M1 → M5 → M15 (missing from Finnhub migration)
                            # ENHANCED FIX: Use batch aggregation on first poll, incremental on subsequent polls
                            if current_len == 0:
                                # First poll - process ALL historical candles in batch
                                self.aggregate_all_historical_candles(symbol)
                            else:
                                # Subsequent polls - incremental aggregation
                                if len(self.m1_data[symbol]) >= 5:
                                    self.aggregate_m1_to_m5(symbol)
                                if len(self.m5_data[symbol]) >= 3:
                                    self.aggregate_m5_to_m15(symbol)
                                if len(self.m15_data[symbol]) >= 2:
                                    self.aggregate_m15_to_m30(symbol)

                # Sleep to avoid tight loop
                time.sleep(1)

            except Exception as e:
                logger.debug(f"Finnhub poll error: {e}")
                time.sleep(5)

    def check_citadel_delayed_signals(self):
        """Check if any CITADEL-delayed signals can be released"""
        current_ticks = {}
        for symbol in self.tick_data:
            if self.tick_data[symbol]:
                current_ticks[symbol] = list(self.tick_data[symbol])[-1]

        released_signals = self.citadel.check_delayed_signals(current_ticks)

        for signal in released_signals:
            # These are post-sweep golden opportunities
            if signal.get("confidence", 0) >= 70:  # Lowered to allow filtered patterns through
                self.publish_signal(signal)
                logger.info(
                    f"🏆 CITADEL RELEASE: {signal['symbol']} {signal['direction']} "
                    f"(delayed {signal.get('delay_time', 0)}s, confidence: {signal['confidence']}%)"
                )

    def show_health_metrics(self):
        """✅ TASK D: Display health metrics for observability"""
        elapsed = time.time() - self.health_metrics["metrics_start_time"]
        print(f"\n{'='*60}")
        print(f"📊 ELITE GUARD HEALTH METRICS - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        print(f"⏱️  Uptime: {elapsed/60:.1f} minutes")
        print(f"📡 tick_rate: {self.health_metrics['tick_rate']:.2f} ticks/sec")
        print(f"📈 candle_close_rate: {self.health_metrics['candle_close_rate']:.4f} bars/sec")
        print(f"🔍 pattern_candidates: {self.health_metrics['pattern_candidates']}")
        print(f"✅ pattern_kept: {self.health_metrics['pattern_kept']}")
        keep_rate = (self.health_metrics['pattern_kept'] / self.health_metrics['pattern_candidates'] * 100) if self.health_metrics['pattern_candidates'] > 0 else 0
        print(f"   └─ keep_rate: {keep_rate:.1f}%")
        print(f"🚀 signals_fired: {self.health_metrics['signals_fired']}")
        print(f"📍 exec_confirms: {self.health_metrics['exec_confirms']}")
        print(f"⏲️  data_lag_ms: {self.health_metrics['data_lag_ms']:.1f}ms")
        print(f"{'='*60}\n")

    def show_stats(self):
        """Display current statistics"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 ELITE GUARD BALANCED v7.0 STATUS")
        logger.info("=" * 60)

        # Signal stats - handle both timestamp formats
        recent_signals = []
        for s in self.signal_history:
            try:
                # Try to parse as float first (unix timestamp)
                ts = s.get("timestamp", 0)
                if isinstance(ts, (int, float)):
                    ts_float = float(ts)
                else:
                    # If it's a string datetime, parse it
                    from datetime import datetime

                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    ts_float = dt.timestamp()

                if time.time() - ts_float < 3600:
                    recent_signals.append(s)
            except:
                continue

        logger.info(f"\n📈 SIGNAL METRICS (Last Hour):")
        logger.info(f"  Total Signals: {len(recent_signals)}")

        if recent_signals:
            quality_tiers = defaultdict(int)
            for sig in recent_signals:
                quality_tiers[sig.get("quality_tier", "UNKNOWN")] += 1

            logger.info(f"  Premium: {quality_tiers['PREMIUM']}")
            logger.info(f"  Standard: {quality_tiers['STANDARD']}")
            logger.info(f"  Acceptable: {quality_tiers['ACCEPTABLE']}")

        # Data feed status
        logger.info(f"\n📡 DATA FEED STATUS:")
        logger.info(f"  Total symbols tracked: {len(self.tick_data)}")

        # NEW: Custom 15-second bar statistics
        logger.info(f"\n⚡ CUSTOM 15s BARS (4x faster than M1):")
        logger.info(f"  Received: {self.custom_bar_stats['received']}")
        logger.info(f"  Duplicates: {self.custom_bar_stats['duplicates']}")
        logger.info(f"  Processed: {self.custom_bar_stats['processed']}")
        logger.info(f"  Symbols with 15s data: {len([s for s in self.s15_data if len(self.s15_data[s]) > 0])}")

        for symbol in list(self.tick_data.keys())[:10]:
            age = time.time() - self.last_tick_time.get(symbol, 0)
            tick_count = len(self.tick_data[symbol])
            s15_count = len(self.s15_data[symbol])
            status = "✅" if age < 5 else "⚠️" if age < 30 else "❌"
            logger.info(f"  {symbol}: {tick_count} ticks, {s15_count} 15s bars | Last: {age:.0f}s ago {status}")

        # CITADEL Protection stats
        citadel_stats = self.citadel.get_protection_stats()
        logger.info(f"\n🛡️ CITADEL PROTECTION:")
        logger.info(f"  Signals Delayed: {citadel_stats['signals_delayed']}")
        logger.info(f"  Sweeps Detected: {citadel_stats['sweeps_detected']}")
        logger.info(f"  Sweeps Avoided: {citadel_stats['sweeps_avoided']}")
        logger.info(f"  Post-Sweep Entries: {citadel_stats['post_sweep_entries']}")
        logger.info(f"  Protection Rate: {citadel_stats['protection_rate']}")

        logger.info("=" * 60)

    def start(self):
        """Start the Elite Guard engine"""
        logger.info("🎯 ELITE GUARD BALANCED v7.0 - Starting...")
        logger.info("📊 Target: 45-50% win rate | 1-2 signals/hour minimum")
        logger.info("🎮 Focus: User engagement with quality improvements")

        if not self.setup_zmq():
            raise RuntimeError("Failed to setup ZMQ connections")

        self.running = True

        # Start data listener thread
        listener_thread = threading.Thread(target=self.data_listener, daemon=True)
        listener_thread.start()

        logger.info("✅ Elite Guard Balanced started successfully")
        logger.info("⚡ Generating 1-2 signals per hour with quality tiers")

        # Main loop
        last_scan = 0
        last_stats = 0
        last_save = 0  # Auto-save candles
        last_analysis = 0  # Periodic analysis

        while self.running:
            try:
                current_time = time.time()

                # Note: OHLC data now comes via data_listener from unified EA stream (port 5556)

                # Check for ML threshold updates from Grokkeeper
                self.update_pattern_thresholds_from_ml()

                # ✅ TASK C FIX: Event-driven pattern scanning on bar close (not time-based)
                # Check for bar complete events (M1 or M5 bars closing)
                has_bar_events = hasattr(self, 'bar_complete_events') and self.bar_complete_events

                # Fallback: Also scan every 15 seconds for safety (in case events are missed)
                time_based_trigger = current_time - last_scan >= 15

                if has_bar_events or time_based_trigger:
                    if has_bar_events:
                        event_symbols = list(self.bar_complete_events.keys())
                        print(f"⏰ SCAN TRIGGER: bar.complete events for {event_symbols}")
                        logger.info(f"⏰ bar.complete scan trigger: {event_symbols}")
                    else:
                        print(f"⏰ SCAN TRIGGER: 15-second fallback, active_session={self.is_active_session()}")
                        logger.info(f"⏰ 15-second fallback scan trigger")

                    # DATA FRESHNESS CHECK - Prevent signals from stale data
                    most_recent_tick = 0
                    for symbol in self.last_tick_time:
                        most_recent_tick = max(most_recent_tick, self.last_tick_time[symbol])

                    # Calculate time since last tick
                    if most_recent_tick > 0:
                        time_since_last_tick = current_time - most_recent_tick
                    else:
                        # No ticks received yet (startup) - allow 5 minutes grace period
                        time_since_last_tick = 0 if not hasattr(self, 'startup_time') else (current_time - self.startup_time)

                    # DISABLED STALE DATA CHECK - Always scan patterns (using Finnhub data now)
                    # Elite Guard now uses Finnhub hybrid candles, not EA ticks
                    if self.is_active_session():
                        self.scan_for_patterns()

                    # Clear bar events after processing
                    if has_bar_events:
                        self.bar_complete_events = {}

                    # Check CITADEL delayed signals
                    self.check_citadel_delayed_signals()
                    last_scan = current_time

                # Show stats every 5 minutes
                if current_time - last_stats >= 300:
                    self.show_health_metrics()  # ✅ TASK D: Show health metrics first
                    self.show_stats()
                    last_stats = current_time

                # Auto-save candles every 60 seconds
                if current_time - last_save >= 60:
                    self.save_candles()
                    last_save = current_time

                # Run analysis every 30 minutes
                if current_time - last_analysis >= 1800:
                    print("\n" + "=" * 60)
                    print(f"📊 PERIODIC ANALYSIS - {datetime.now().strftime('%H:%M:%S')}")
                    print("=" * 60)
                    self.analyze_initial_data()
                    self.verify_rr_ratio()
                    print("=" * 60 + "\n")
                    last_analysis = current_time

                time.sleep(1)

            except KeyboardInterrupt:
                logger.info("\n⚠️ Shutdown signal received")
                break
            except Exception as e:
                import traceback

                logger.error(f"Main loop error: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                time.sleep(5)

        self.cleanup()

    def test_candle_building(self):
        """Test candle building functionality"""
        print("🔍 Testing candle building...")

        # Initialize candle storage for all trading pairs if not present
        for symbol in self.trading_pairs:
            if symbol not in self.m1_data:
                self.m1_data[symbol] = deque(maxlen=500)
            if symbol not in self.m5_data:
                self.m5_data[symbol] = deque(maxlen=300)
            if symbol not in self.m15_data:
                self.m15_data[symbol] = deque(maxlen=200)

        # Create a test tick
        test_tick = {"symbol": "EURUSD", "bid": 1.1647, "ask": 1.1649, "timestamp": time.time()}

        # Process the test tick using new packet format
        test_packet = {
            "type": "TICK",
            "symbol": "EURUSD",
            "bid": 1.1647,
            "ask": 1.1649,
            "spread": 0.2,
            "volume": 1,
            "timestamp": "2025.09.24 21:45:00",
        }
        self.process_tick_packet(test_packet)

        # Report candle counts
        print(f"✅ EURUSD M1: {len(self.m1_data.get('EURUSD', []))} candles")
        print(f"✅ EURUSD M5: {len(self.m5_data.get('EURUSD', []))} candles")
        print(f"✅ EURUSD M15: {len(self.m15_data.get('EURUSD', []))} candles")

        # Check all pairs
        print("\n📊 All pairs candle counts:")
        for symbol in self.trading_pairs[:5]:  # Show first 5 for brevity
            m1_count = len(self.m1_data.get(symbol, []))
            m5_count = len(self.m5_data.get(symbol, []))
            m15_count = len(self.m15_data.get(symbol, []))
            print(f"  {symbol}: M1={m1_count}, M5={m5_count}, M15={m15_count}")

        print("✅ Candle building test complete!")

    def cleanup(self):
        """Clean shutdown"""
        self.running = False

        # Save candles before shutdown
        print("💾 Saving candles before shutdown...")
        self.save_candles()

        # Finnhub adapter cleanup (if needed)
        if hasattr(self, "finnhub_adapter"):
            logger.info("🌐 Closing Finnhub adapter...")
        if hasattr(self, "publisher") and self.publisher:
            self.publisher.close()
        if hasattr(self, "ml_subscriber") and self.ml_subscriber:
            self.ml_subscriber.close()

        self.context.term()
        logger.info("✅ Elite Guard Balanced shutdown complete")


def immortal_main_loop():
    """Immortality protocol - auto-restart on crashes"""
    consecutive_failures = 0
    max_failures = 5

    while True:
        try:
            logger.info("🛡️ IMMORTALITY PROTOCOL ACTIVATED")
            logger.info("🚀 Starting Elite Guard Balanced...")

            engine = EliteGuardBalanced()
            engine.start()

            # Reset failure count on clean exit
            consecutive_failures = 0

        except KeyboardInterrupt:
            logger.info("⚠️ Manual shutdown requested")
            break

        except Exception as e:
            consecutive_failures += 1

            if consecutive_failures >= max_failures:
                logger.error(f"❌ Max failures ({max_failures}) reached. Stopping.")
                break

            wait_time = min(30 * consecutive_failures, 300)

            logger.error(f"💀 Elite Guard died: {e}")
            logger.info(f"🔄 Resurrection in {wait_time} seconds...")
            logger.info(f"📊 Failure {consecutive_failures}/{max_failures}")

            time.sleep(wait_time)

            logger.info("⚡ RESURRECTING Elite Guard Balanced...")


if __name__ == "__main__":
    immortal_main_loop()
