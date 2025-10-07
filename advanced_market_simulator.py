#!/usr/bin/env python3
"""
📈 ADVANCED MARKET SIMULATOR
Simulates realistic market conditions for testing BITTEN signal flow
Creates realistic price movements, patterns, and trading scenarios
"""

import json
import math
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class MarketSimulator:
    """Advanced market data simulator for testing"""

    def __init__(self):
        self.base_prices = {
            "EURUSD": 1.0875,
            "GBPUSD": 1.2645,
            "USDJPY": 149.85,
            "USDCHF": 0.8745,
            "AUDUSD": 0.6598,
            "USDCAD": 1.3567,
            "NZDUSD": 0.6012,
            "EURJPY": 162.34,
            "GBPJPY": 189.23,
            "EURGBP": 0.8598,
            "AUDCAD": 0.8954,
            "AUDNZD": 1.0875,
            "EURAUD": 1.6498,
            "EURCHF": 0.9512,
            "GBPCHF": 1.1054,
        }

        self.pip_values = {
            "EURUSD": 0.0001,
            "GBPUSD": 0.0001,
            "USDJPY": 0.01,
            "USDCHF": 0.0001,
            "AUDUSD": 0.0001,
            "USDCAD": 0.0001,
            "NZDUSD": 0.0001,
            "EURJPY": 0.01,
            "GBPJPY": 0.01,
            "EURGBP": 0.0001,
            "AUDCAD": 0.0001,
            "AUDNZD": 0.0001,
            "EURAUD": 0.0001,
            "EURCHF": 0.0001,
            "GBPCHF": 0.0001,
        }

        # Market sessions with different volatility
        self.sessions = {
            "ASIAN": {"volatility": 0.5, "start": 0, "end": 8},
            "LONDON": {"volatility": 1.2, "start": 8, "end": 16},
            "NY": {"volatility": 1.0, "start": 13, "end": 22},
            "OVERLAP": {"volatility": 1.5, "start": 13, "end": 16},
        }

        self.current_prices = self.base_prices.copy()
        self.price_history = {pair: [] for pair in self.base_prices.keys()}

    def get_current_session(self) -> str:
        """Get current trading session based on UTC time"""
        current_hour = datetime.utcnow().hour

        if 13 <= current_hour <= 16:
            return "OVERLAP"
        elif 8 <= current_hour <= 16:
            return "LONDON"
        elif 13 <= current_hour <= 22:
            return "NY"
        else:
            return "ASIAN"

    def generate_realistic_movement(self, pair: str, session: str) -> float:
        """Generate realistic price movement based on session volatility"""
        volatility = self.sessions[session]["volatility"]
        pip_value = self.pip_values[pair]

        # Base movement: -2 to +2 pips with session volatility
        base_movement = random.uniform(-2, 2) * pip_value * volatility

        # Add trend component (slight bias)
        trend_factor = random.uniform(-0.5, 0.5) * pip_value

        # Add volatility spikes (10% chance)
        if random.random() < 0.1:
            spike = random.uniform(-5, 5) * pip_value * volatility
            base_movement += spike

        return base_movement

    def create_pattern_conditions(self, pair: str, pattern_type: str) -> Dict:
        """Create market conditions that would trigger specific patterns"""
        current_price = self.current_prices[pair]
        pip_value = self.pip_values[pair]

        if pattern_type == "LIQUIDITY_SWEEP_REVERSAL":
            # Create a quick spike then reversal
            spike_direction = random.choice([1, -1])
            spike_size = random.uniform(3, 8) * pip_value

            # Spike price
            spike_price = current_price + (spike_direction * spike_size)

            # Quick reversal
            reversal_size = random.uniform(5, 12) * pip_value
            reversal_price = spike_price - (spike_direction * reversal_size)

            return {
                "entry_price": reversal_price,
                "direction": "SELL" if spike_direction > 0 else "BUY",
                "confidence": random.uniform(75, 89),
                "stop_pips": int(random.uniform(15, 25)),
                "target_pips": int(random.uniform(20, 35)),
            }

        elif pattern_type == "VCB_BREAKOUT":
            # Volatility compression then breakout
            compression_size = random.uniform(2, 4) * pip_value
            breakout_direction = random.choice([1, -1])
            breakout_size = random.uniform(8, 15) * pip_value

            breakout_price = current_price + (breakout_direction * breakout_size)

            return {
                "entry_price": breakout_price,
                "direction": "BUY" if breakout_direction > 0 else "SELL",
                "confidence": random.uniform(70, 85),
                "stop_pips": int(random.uniform(12, 20)),
                "target_pips": int(random.uniform(15, 25)),
            }

        elif pattern_type == "ORDER_BLOCK_BOUNCE":
            # Price approaches support/resistance level
            bounce_direction = random.choice([1, -1])
            bounce_strength = random.uniform(8, 20) * pip_value

            bounce_price = current_price + (bounce_direction * bounce_strength)

            return {
                "entry_price": bounce_price,
                "direction": "BUY" if bounce_direction > 0 else "SELL",
                "confidence": random.uniform(72, 88),
                "stop_pips": int(random.uniform(18, 28)),
                "target_pips": int(random.uniform(25, 40)),
            }

        return {}

    def generate_signal_scenario(self, pairs: List[str] = None, pattern_types: List[str] = None) -> List[Dict]:
        """Generate realistic signal scenarios for testing"""
        if pairs is None:
            pairs = random.sample(list(self.base_prices.keys()), random.randint(2, 5))

        if pattern_types is None:
            pattern_types = [
                "LIQUIDITY_SWEEP_REVERSAL",
                "VCB_BREAKOUT",
                "ORDER_BLOCK_BOUNCE",
                "FAIR_VALUE_GAP_FILL",
                "SWEEP_RETURN",
                "MOMENTUM_BURST",
            ]

        current_session = self.get_current_session()
        signals = []

        for pair in pairs:
            # Update current price with realistic movement
            movement = self.generate_realistic_movement(pair, current_session)
            self.current_prices[pair] += movement

            # Store price history
            self.price_history[pair].append({"price": self.current_prices[pair], "timestamp": time.time()})

            # Keep only last 100 price points
            if len(self.price_history[pair]) > 100:
                self.price_history[pair] = self.price_history[pair][-100:]

            # 30% chance to generate a signal for this pair
            if random.random() < 0.3:
                pattern_type = random.choice(pattern_types)
                pattern_conditions = self.create_pattern_conditions(pair, pattern_type)

                if pattern_conditions:
                    signal = {
                        "signal_id": f"SIM_{pattern_type}_{pair}_{int(time.time())}",
                        "symbol": pair,
                        "direction": pattern_conditions["direction"],
                        "entry_price": round(pattern_conditions["entry_price"], 5),
                        "stop_pips": pattern_conditions["stop_pips"],
                        "target_pips": pattern_conditions["target_pips"],
                        "confidence": round(pattern_conditions["confidence"], 1),
                        "pattern_type": pattern_type,
                        "signal_type": "PRECISION_STRIKE" if pattern_conditions["confidence"] > 80 else "RAPID_ASSAULT",
                        "created_at": int(time.time()),
                        "expires_at": int(time.time()) + random.randint(600, 1800),  # 10-30 minutes
                        "session": current_session,
                        "citadel_score": round(random.uniform(6.0, 9.5), 1),
                        "simulated": True,
                    }
                    signals.append(signal)

        return signals

    def simulate_market_scenario(self, scenario_type: str) -> Dict:
        """Simulate specific market scenarios for testing"""
        scenarios = {
            "high_volatility": {
                "description": "Major news event causing high volatility",
                "pairs": ["EURUSD", "GBPUSD", "USDJPY"],
                "volatility_multiplier": 3.0,
                "signal_probability": 0.8,
            },
            "quiet_market": {
                "description": "Low volatility consolidation period",
                "pairs": ["USDCHF", "EURGBP", "AUDNZD"],
                "volatility_multiplier": 0.3,
                "signal_probability": 0.1,
            },
            "trend_day": {
                "description": "Strong trending market conditions",
                "pairs": ["EURUSD", "GBPJPY", "AUDUSD"],
                "volatility_multiplier": 1.5,
                "signal_probability": 0.6,
            },
            "asian_session": {
                "description": "Typical Asian session trading",
                "pairs": ["USDJPY", "AUDUSD", "NZDUSD"],
                "volatility_multiplier": 0.5,
                "signal_probability": 0.2,
            },
        }

        if scenario_type not in scenarios:
            scenario_type = random.choice(list(scenarios.keys()))

        scenario = scenarios[scenario_type]
        signals = []

        # Generate multiple signals over time for this scenario
        for i in range(random.randint(3, 8)):
            time.sleep(0.1)  # Small delay between signals

            if random.random() < scenario["signal_probability"]:
                pair_signals = self.generate_signal_scenario(
                    pairs=scenario["pairs"],
                    pattern_types=["LIQUIDITY_SWEEP_REVERSAL", "VCB_BREAKOUT", "MOMENTUM_BURST"],
                )
                signals.extend(pair_signals)

        return {
            "scenario": scenario_type,
            "description": scenario["description"],
            "signals": signals,
            "total_signals": len(signals),
        }


def main():
    """Demo the market simulator"""
    print("📈 ADVANCED MARKET SIMULATOR DEMO")
    print("=" * 50)

    simulator = MarketSimulator()

    # Generate some realistic signals
    print("🎯 Generating realistic signal scenarios...")
    signals = simulator.generate_signal_scenario()

    print(f"Generated {len(signals)} signals:")
    for signal in signals:
        print(f"  {signal['symbol']} {signal['direction']} - {signal['pattern_type']} ({signal['confidence']:.1f}%)")

    # Simulate a high volatility scenario
    print("\n🌪️ Simulating high volatility scenario...")
    scenario = simulator.simulate_market_scenario("high_volatility")

    print(f"Scenario: {scenario['description']}")
    print(f"Generated {scenario['total_signals']} signals in volatile conditions")

    # Show current market state
    print("\n📊 Current simulated market prices:")
    for pair, price in list(simulator.current_prices.items())[:5]:
        print(f"  {pair}: {price:.5f}")


if __name__ == "__main__":
    main()
