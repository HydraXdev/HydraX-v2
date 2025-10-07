"""
web/healthz.py - Health endpoint handler mirroring TypeScript logic
Provides comprehensive health monitoring for MetaSocket integration
"""

import json
import time
from typing import Any, Callable, Dict


def healthz_handler(metrics: Dict[str, Any]) -> Callable:
    """
    Create health endpoint handler
    Mirrors TypeScript healthzHandler() function exactly

    Args:
        metrics: Metrics dictionary with timing data

    Returns:
        Handler function for HTTP requests
    """

    def handler(request=None, response=None) -> Dict[str, Any]:
        """
        Health check handler function
        Returns comprehensive system health status

        Args:
            request: HTTP request object (framework-agnostic)
            response: HTTP response object (framework-agnostic)

        Returns:
            Health status dictionary with metrics
        """
        now = int(time.time() * 1000)

        # Calculate tick ages for each symbol
        last_tick_ts = metrics.get("lastTickTs", {})
        tick_ages = {}

        for symbol, ts in last_tick_ts.items():
            if isinstance(ts, (int, float)) and ts > 0:
                tick_ages[symbol] = now - int(ts)
            else:
                tick_ages[symbol] = float("inf")  # No data available

        # Calculate last event age (maximum of all event ages)
        event_ages = []

        # Add tick ages
        if tick_ages:
            event_ages.extend(tick_ages.values())

        # Add position event age
        last_position_ts = metrics.get("lastPositionTs", 0)
        if last_position_ts > 0:
            event_ages.append(now - last_position_ts)

        # Add account event age
        last_account_ts = metrics.get("lastAccountTs", 0)
        if last_account_ts > 0:
            event_ages.append(now - last_account_ts)

        # Calculate maximum event age (0 if no events)
        last_event_age_ms = max([0] + [age for age in event_ages if age != float("inf")])

        # Check tick rates - each symbol should have >= 0.5 ticks/second
        tick_rate_per_symbol = metrics.get("tickRatePerSymbol", {})
        ok_tick_rates = True

        for symbol, rate in tick_rate_per_symbol.items():
            if rate is None or rate < 0.5:
                ok_tick_rates = False
                break

        # Check event freshness - last event should be < 5 seconds ago
        ok_ages = last_event_age_ms < 5000

        # Determine overall health status
        status_code = 200 if (ok_tick_rates and ok_ages) else 503
        status_text = "healthy" if status_code == 200 else "degraded"

        # Build comprehensive health response
        health_data = {
            "status": status_text,
            "status_code": status_code,
            "last_event_age_ms": last_event_age_ms,
            "event_lag_ms_p95": metrics.get("p95LagMs", 0),
            "tick_rate_per_symbol": tick_rate_per_symbol,
            "account_heartbeat_age_ms": now - last_account_ts if last_account_ts > 0 else float("inf"),
            "position_heartbeat_age_ms": now - last_position_ts if last_position_ts > 0 else float("inf"),
            "subscriptions": metrics.get("subscriptions", []),
            "timestamp": now,
            "checks": {
                "tick_rates_ok": ok_tick_rates,
                "event_ages_ok": ok_ages,
                "symbols_active": len([s for s, age in tick_ages.items() if age < 10000]),
                "total_symbols": len(tick_ages),
            },
        }

        # Set response status if response object provided
        if response is not None:
            if hasattr(response, "status_code"):
                response.status_code = status_code
            elif hasattr(response, "status"):
                response.status(status_code)

        return health_data

    return handler


class HealthMonitor:
    """Health monitoring system for MetaSocket integration"""

    def __init__(self):
        self.metrics = {
            "lastTickTs": {},  # symbol -> timestamp
            "lastPositionTs": 0,  # last position event timestamp
            "lastAccountTs": 0,  # last account poll timestamp
            "tickRatePerSymbol": {},  # symbol -> ticks per second
            "p95LagMs": 0,  # 95th percentile lag
            "subscriptions": [],  # active subscriptions
            "connectionStartTime": int(time.time() * 1000),
            "totalTicksReceived": 0,
            "totalPositionEvents": 0,
            "totalAccountPolls": 0,
        }
        self.tick_windows = {}  # For calculating tick rates
        self.window_size = 60  # 60 second window for rate calculation

    def update_tick_metrics(self, symbol: str, timestamp: int = None) -> None:
        """Update tick-related metrics"""
        if timestamp is None:
            timestamp = int(time.time() * 1000)

        # Update last tick timestamp
        self.metrics["lastTickTs"][symbol] = timestamp
        self.metrics["totalTicksReceived"] += 1

        # Update tick rate calculation
        if symbol not in self.tick_windows:
            self.tick_windows[symbol] = []

        # Add current timestamp to window
        self.tick_windows[symbol].append(timestamp)

        # Remove timestamps older than window_size seconds
        cutoff = timestamp - (self.window_size * 1000)
        self.tick_windows[symbol] = [ts for ts in self.tick_windows[symbol] if ts > cutoff]

        # Calculate tick rate (ticks per second)
        tick_count = len(self.tick_windows[symbol])
        rate = tick_count / self.window_size if self.window_size > 0 else 0
        self.metrics["tickRatePerSymbol"][symbol] = rate

    def update_position_metrics(self, timestamp: int = None) -> None:
        """Update position event metrics"""
        if timestamp is None:
            timestamp = int(time.time() * 1000)

        self.metrics["lastPositionTs"] = timestamp
        self.metrics["totalPositionEvents"] += 1

    def update_account_metrics(self, timestamp: int = None) -> None:
        """Update account polling metrics"""
        if timestamp is None:
            timestamp = int(time.time() * 1000)

        self.metrics["lastAccountTs"] = timestamp
        self.metrics["totalAccountPolls"] += 1

    def update_subscription_list(self, subscriptions: list) -> None:
        """Update active subscription list"""
        self.metrics["subscriptions"] = subscriptions.copy()

    def set_lag_metrics(self, p95_lag_ms: float) -> None:
        """Set lag metrics"""
        self.metrics["p95LagMs"] = p95_lag_ms

    def get_handler(self) -> Callable:
        """Get health endpoint handler"""
        return healthz_handler(self.metrics)

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        return self.metrics.copy()

    def get_uptime_ms(self) -> int:
        """Get system uptime in milliseconds"""
        return int(time.time() * 1000) - self.metrics["connectionStartTime"]


# Flask integration helper
def create_flask_health_endpoint(app, monitor: HealthMonitor, path: str = "/healthz"):
    """
    Create Flask health endpoint

    Args:
        app: Flask application instance
        monitor: HealthMonitor instance
        path: Endpoint path (default: /healthz)
    """

    @app.route(path)
    def health_check():
        handler = monitor.get_handler()
        result = handler()

        from flask import jsonify

        response = jsonify(result)
        response.status_code = result["status_code"]
        return response


# FastAPI integration helper
def create_fastapi_health_endpoint(app, monitor: HealthMonitor, path: str = "/healthz"):
    """
    Create FastAPI health endpoint

    Args:
        app: FastAPI application instance
        monitor: HealthMonitor instance
        path: Endpoint path (default: /healthz)
    """

    @app.get(path)
    async def health_check():
        handler = monitor.get_handler()
        result = handler()

        from fastapi import Response
        from fastapi.responses import JSONResponse

        return JSONResponse(content=result, status_code=result["status_code"])


# Example usage and testing
def test_health_monitor():
    """Test the health monitoring system"""
    print("🧪 Testing Health Monitor System")
    print("=" * 40)

    monitor = HealthMonitor()

    # Simulate some metrics
    current_time = int(time.time() * 1000)

    # Add tick data for multiple symbols
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    for i, symbol in enumerate(symbols):
        # Simulate different tick rates
        for j in range(i + 1):  # EURUSD=1 tick, GBPUSD=2 ticks, USDJPY=3 ticks
            monitor.update_tick_metrics(symbol, current_time - (j * 1000))

    # Add position and account data
    monitor.update_position_metrics(current_time - 2000)  # 2 seconds ago
    monitor.update_account_metrics(current_time - 1000)  # 1 second ago

    # Update subscriptions
    monitor.update_subscription_list(["EURUSD", "GBPUSD", "USDJPY"])

    # Set lag metrics
    monitor.set_lag_metrics(150.5)  # 150ms p95 lag

    # Test health handler
    handler = monitor.get_handler()
    health_result = handler()

    print(f"📊 Health Check Results:")
    print(f"  Status: {health_result['status']} ({health_result['status_code']})")
    print(f"  Last event age: {health_result['last_event_age_ms']}ms")
    print(f"  Account age: {health_result['account_heartbeat_age_ms']}ms")
    print(f"  Position age: {health_result['position_heartbeat_age_ms']}ms")
    print(f"  P95 lag: {health_result['event_lag_ms_p95']}ms")

    print(f"\n📈 Tick Rates:")
    for symbol, rate in health_result["tick_rate_per_symbol"].items():
        print(f"  {symbol}: {rate:.2f} ticks/sec")

    print(f"\n✅ Health Checks:")
    for check, status in health_result["checks"].items():
        print(f"  {check}: {status}")

    print(f"\n📋 Subscriptions: {health_result['subscriptions']}")

    # Test unhealthy scenario
    print(f"\n🚨 Testing Unhealthy Scenario:")
    # Make ticks very old
    old_time = current_time - 10000  # 10 seconds ago
    for symbol in symbols:
        monitor.update_tick_metrics(symbol, old_time)

    unhealthy_result = handler()
    print(f"  Status: {unhealthy_result['status']} ({unhealthy_result['status_code']})")
    print(f"  Last event age: {unhealthy_result['last_event_age_ms']}ms")
    print(f"  Ages OK: {unhealthy_result['checks']['event_ages_ok']}")

    print("\n🎉 Health monitor test completed!")


if __name__ == "__main__":
    test_health_monitor()
