#!/usr/bin/env python3
"""
HydraSocket v1 Dual-Feed Parity Harness
Compares HydraSocket events with MetaSocket (legacy) for ≥99% end-state parity
"""

import json
import time
import asyncio
import sqlite3
import websockets
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TradeOutcome:
    """Trade outcome for parity comparison"""
    ticket: str
    symbol: str
    side: str
    volume: float
    open_price: float
    close_price: Optional[float]
    status: str  # open, closed, sl_hit, tp_hit
    pnl: Optional[float]
    timestamp: float

@dataclass
class PortfolioState:
    """Portfolio end-state for comparison"""
    open_positions: Dict[str, TradeOutcome]
    closed_positions: List[TradeOutcome]
    total_pnl: float
    balance: float
    equity: float

class HydraSocketCollector:
    """Collects events from HydraSocket"""

    def __init__(self, ws_url: str, api_key: str, account_id: str):
        self.ws_url = ws_url
        self.api_key = api_key
        self.account_id = account_id
        self.events = []
        self.portfolio = PortfolioState({}, [], 0.0, 0.0, 0.0)

    async def collect_events(self, duration_seconds: int = 300):
        """Collect events via WebSocket for specified duration"""
        uri = f"{self.ws_url}?account_id={self.account_id}&token={self.api_key}&types=events,account"

        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Connected to HydraSocket WebSocket")

                # Subscribe to events
                subscribe_msg = {
                    "type": "subscribe",
                    "topic": "events",
                    "account_id": self.account_id
                }
                await websocket.send(json.dumps(subscribe_msg))

                end_time = time.time() + duration_seconds
                while time.time() < end_time:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        event = json.loads(message)
                        self.events.append(event)
                        self._process_event(event)
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("HydraSocket connection closed")
                        break

        except Exception as e:
            logger.error(f"HydraSocket collection error: {e}")

    def _process_event(self, event: Dict[str, Any]):
        """Process individual event into portfolio state"""
        event_type = event.get("event_type")

        if event_type == "position_opened":
            ticket = event.get("ticket")
            trade = TradeOutcome(
                ticket=ticket,
                symbol=event.get("symbol"),
                side=event.get("side"),
                volume=event.get("volume"),
                open_price=event.get("price"),
                close_price=None,
                status="open",
                pnl=None,
                timestamp=event.get("timestamp", time.time())
            )
            self.portfolio.open_positions[ticket] = trade

        elif event_type in ["position_closed", "sl_hit", "tp_hit"]:
            ticket = event.get("ticket")
            if ticket in self.portfolio.open_positions:
                trade = self.portfolio.open_positions.pop(ticket)
                trade.close_price = event.get("price")
                trade.status = event_type
                trade.pnl = event.get("pnl", 0.0)
                self.portfolio.closed_positions.append(trade)
                self.portfolio.total_pnl += trade.pnl

        elif event_type == "account_summary":
            self.portfolio.balance = event.get("balance", 0.0)
            self.portfolio.equity = event.get("equity", 0.0)

class MetaSocketCollector:
    """Collects events from MetaSocket (legacy) - simulated for now"""

    def __init__(self, api_url: str, api_key: str, account_id: str):
        self.api_url = api_url
        self.api_key = api_key
        self.account_id = account_id
        self.events = []
        self.portfolio = PortfolioState({}, [], 0.0, 0.0, 0.0)

    async def collect_events(self, duration_seconds: int = 300):
        """Simulate MetaSocket event collection"""
        # For now, simulate with similar data to HydraSocket
        # In real implementation, this would connect to actual MetaSocket
        logger.info("Simulating MetaSocket collection (replace with real implementation)")

        end_time = time.time() + duration_seconds
        trade_counter = 0

        while time.time() < end_time:
            await asyncio.sleep(5)  # Simulate periodic events

            # Simulate some trade events
            if trade_counter < 20:  # Simulate 20 trades
                ticket = f"META_{trade_counter}"

                # Open position
                open_event = {
                    "event_type": "position_opened",
                    "ticket": ticket,
                    "symbol": "EURUSD",
                    "side": "buy",
                    "volume": 0.01,
                    "price": 1.1000 + (trade_counter * 0.0001),
                    "timestamp": time.time()
                }
                self.events.append(open_event)
                self._process_event(open_event)

                # Close position after 30 seconds
                await asyncio.sleep(30)
                close_event = {
                    "event_type": "position_closed",
                    "ticket": ticket,
                    "price": 1.1000 + (trade_counter * 0.0001) + 0.0010,  # +10 pips
                    "pnl": 10.0,
                    "timestamp": time.time()
                }
                self.events.append(close_event)
                self._process_event(close_event)

                trade_counter += 1

    def _process_event(self, event: Dict[str, Any]):
        """Process MetaSocket event (same logic as HydraSocket)"""
        event_type = event.get("event_type")

        if event_type == "position_opened":
            ticket = event.get("ticket")
            trade = TradeOutcome(
                ticket=ticket,
                symbol=event.get("symbol"),
                side=event.get("side"),
                volume=event.get("volume"),
                open_price=event.get("price"),
                close_price=None,
                status="open",
                pnl=None,
                timestamp=event.get("timestamp", time.time())
            )
            self.portfolio.open_positions[ticket] = trade

        elif event_type in ["position_closed", "sl_hit", "tp_hit"]:
            ticket = event.get("ticket")
            if ticket in self.portfolio.open_positions:
                trade = self.portfolio.open_positions.pop(ticket)
                trade.close_price = event.get("price")
                trade.status = event_type
                trade.pnl = event.get("pnl", 0.0)
                self.portfolio.closed_positions.append(trade)
                self.portfolio.total_pnl += trade.pnl

class ParityAnalyzer:
    """Analyzes parity between HydraSocket and MetaSocket"""

    def __init__(self, hydra_portfolio: PortfolioState, meta_portfolio: PortfolioState):
        self.hydra = hydra_portfolio
        self.meta = meta_portfolio

    def calculate_parity(self) -> Dict[str, Any]:
        """Calculate end-state parity percentage"""

        # Compare closed positions
        hydra_closed = {t.ticket: t for t in self.hydra.closed_positions}
        meta_closed = {t.ticket: t for t in self.meta.closed_positions}

        matching_trades = 0
        total_trades = max(len(hydra_closed), len(meta_closed))

        for ticket in hydra_closed:
            if ticket in meta_closed:
                hydra_trade = hydra_closed[ticket]
                meta_trade = meta_closed[ticket]

                # Check if outcomes match (allowing small tolerance)
                if (abs(hydra_trade.pnl - meta_trade.pnl) < 0.01 and
                    hydra_trade.status == meta_trade.status):
                    matching_trades += 1

        # Calculate parity percentage
        parity_percentage = (matching_trades / total_trades * 100) if total_trades > 0 else 100.0

        # Compare portfolio totals
        pnl_diff = abs(self.hydra.total_pnl - self.meta.total_pnl)
        balance_diff = abs(self.hydra.balance - self.meta.balance)

        return {
            "parity_percentage": parity_percentage,
            "matching_trades": matching_trades,
            "total_trades": total_trades,
            "pnl_difference": pnl_diff,
            "balance_difference": balance_diff,
            "hydra_summary": {
                "total_pnl": self.hydra.total_pnl,
                "balance": self.hydra.balance,
                "open_positions": len(self.hydra.open_positions),
                "closed_positions": len(self.hydra.closed_positions)
            },
            "meta_summary": {
                "total_pnl": self.meta.total_pnl,
                "balance": self.meta.balance,
                "open_positions": len(self.meta.open_positions),
                "closed_positions": len(self.meta.closed_positions)
            },
            "discrepancies": self._find_discrepancies(hydra_closed, meta_closed)
        }

    def _find_discrepancies(self, hydra_trades: Dict, meta_trades: Dict) -> List[Dict]:
        """Find specific trade discrepancies"""
        discrepancies = []

        # Trades in HydraSocket but not MetaSocket
        for ticket in hydra_trades:
            if ticket not in meta_trades:
                discrepancies.append({
                    "type": "missing_in_meta",
                    "ticket": ticket,
                    "trade": asdict(hydra_trades[ticket])
                })

        # Trades in MetaSocket but not HydraSocket
        for ticket in meta_trades:
            if ticket not in hydra_trades:
                discrepancies.append({
                    "type": "missing_in_hydra",
                    "ticket": ticket,
                    "trade": asdict(meta_trades[ticket])
                })

        # Trades with different outcomes
        for ticket in hydra_trades:
            if ticket in meta_trades:
                hydra_trade = hydra_trades[ticket]
                meta_trade = meta_trades[ticket]

                if (abs(hydra_trade.pnl - meta_trade.pnl) >= 0.01 or
                    hydra_trade.status != meta_trade.status):
                    discrepancies.append({
                        "type": "outcome_mismatch",
                        "ticket": ticket,
                        "hydra_trade": asdict(hydra_trade),
                        "meta_trade": asdict(meta_trade)
                    })

        return discrepancies

async def run_parity_test(duration_minutes: int = 5) -> Dict[str, Any]:
    """Run the dual-feed parity test"""

    duration_seconds = duration_minutes * 60
    test_id = str(uuid.uuid4())[:8]

    logger.info(f"Starting parity test {test_id} for {duration_minutes} minutes")

    # Initialize collectors
    hydra_collector = HydraSocketCollector(
        ws_url="ws://localhost:8888/socket.io/",
        api_key="test-api-key",
        account_id="TEST"
    )

    meta_collector = MetaSocketCollector(
        api_url="http://localhost:9999",  # Placeholder
        api_key="test-api-key",
        account_id="TEST"
    )

    # Run collection in parallel
    await asyncio.gather(
        hydra_collector.collect_events(duration_seconds),
        meta_collector.collect_events(duration_seconds)
    )

    # Analyze parity
    analyzer = ParityAnalyzer(hydra_collector.portfolio, meta_collector.portfolio)
    parity_results = analyzer.calculate_parity()

    # Generate report
    report = {
        "test_id": test_id,
        "timestamp": datetime.now().isoformat(),
        "duration_minutes": duration_minutes,
        "parity_results": parity_results,
        "hydra_events_count": len(hydra_collector.events),
        "meta_events_count": len(meta_collector.events),
        "pass_threshold": 99.0,
        "test_passed": parity_results["parity_percentage"] >= 99.0
    }

    return report

def save_parity_report(report: Dict[str, Any]):
    """Save parity report to artifacts directory"""
    date_str = datetime.now().strftime("%Y%m%d")
    test_id = report["test_id"]

    report_path = f"/root/HydraX-v2/artifacts/parity/{date_str}/report_{test_id}.json"

    # Ensure directory exists
    import os
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Parity report saved to: {report_path}")
    return report_path

if __name__ == "__main__":
    import sys

    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    # Run parity test
    report = asyncio.run(run_parity_test(duration))

    # Save report
    report_path = save_parity_report(report)

    # Print summary
    parity_pct = report["parity_results"]["parity_percentage"]
    passed = "✅ PASSED" if report["test_passed"] else "❌ FAILED"

    print(f"\n🎯 PARITY TEST SUMMARY")
    print(f"Test ID: {report['test_id']}")
    print(f"Parity: {parity_pct:.2f}% {passed}")
    print(f"Report: {report_path}")

    if not report["test_passed"]:
        print(f"Discrepancies: {len(report['parity_results']['discrepancies'])}")
        sys.exit(1)