"""
pollers/account.py - Account polling system mirroring TypeScript logic
Polls account status every 3 seconds and publishes normalized account data
"""

import asyncio
import time
import logging
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)

async def poll_account(
    conn: Any,
    publish: Callable[[Dict[str, Any]], None],
    metrics: Dict[str, Any]
) -> None:
    """
    Poll account status every 3 seconds
    Mirrors TypeScript pollAccount() function exactly

    Args:
        conn: WebSocket connection with sendAndWait capability
        publish: Function to publish account data
        metrics: Metrics dictionary to update with timestamps
    """
    while True:
        try:
            # Request account status from broker
            if hasattr(conn, "send_and_wait"):
                a = await conn.send_and_wait({"op": "ACCOUNT_STATUS"})
            else:
                logger.warning("Connection doesnt support send_and_wait for account polling")
                await asyncio.sleep(3.0)
                continue

            # Normalize account data with defensive conversion
            def safe_float(value, default=0.0) -> float:
                """Safely convert to float with default"""
                try:
                    return float(value) if value is not None else default
                except (ValueError, TypeError):
                    return default

            def safe_string(value, default="") -> str:
                """Safely convert to string with default"""
                try:
                    return str(value) if value is not None else default
                except (ValueError, TypeError):
                    return default

            # Create normalized account object
            current_time = int(time.time() * 1000)
            out = {
                "balance": safe_float(a.get("balance")),
                "equity": safe_float(a.get("equity")),
                "margin": safe_float(a.get("margin")),
                "free_margin": safe_float(a.get("free_margin")),
                "leverage": safe_float(a.get("leverage")),
                "currency": safe_string(a.get("currency"), "USD"),
                "ts_epoch_ms": current_time,
                "src": "metasocket"
            }

            # Publish normalized account data
            publish(out)

            # Update metrics
            metrics["lastAccountTs"] = out["ts_epoch_ms"]

            logger.debug(
                f"📊 Account: {out[\"currency\"]} {out[\"balance\"]:.2f} "
                f"(equity: {out[\"equity\"]:.2f}, margin: {out[\"margin\"]:.2f})"
            )

        except Exception as e:
            logger.error(f"❌ Account polling error: {e}")
            # Continue loop even on error - dont break the polling cycle

        # Sleep for 3 seconds as per TypeScript implementation
        await asyncio.sleep(3.0)

class AccountPoller:
    """Account polling manager with lifecycle control"""

    def __init__(self):
        self.poll_task: Optional[asyncio.Task] = None
        self.account_callbacks = []
        self.metrics = {
            "lastAccountTs": 0,
            "accountPollErrors": 0,
            "accountPollSuccess": 0
        }
        self.running = False

    def add_account_callback(self, callback: Callable[[Dict], None]) -> None:
        """Add callback for account updates"""
        self.account_callbacks.append(callback)

    def publish_account_data(self, account_data: Dict[str, Any]) -> None:
        """Publish account data to all callbacks"""
        self.metrics["accountPollSuccess"] += 1

        for callback in self.account_callbacks:
            try:
                callback(account_data)
            except Exception as e:
                logger.error(f"❌ Account callback failed: {e}")

    async def start_polling(self, conn: Any) -> None:
        """Start account polling task"""
        if self.running:
            logger.warning("Account polling already running")
            return

        self.running = True

        async def polling_wrapper():
            """Wrapper to handle polling errors and update metrics"""
            try:
                await poll_account(conn, self.publish_account_data, self.metrics)
            except asyncio.CancelledError:
                raise  # Let cancellation propagate
            except Exception as e:
                logger.error(f"❌ Account polling task failed: {e}")
                self.metrics["accountPollErrors"] += 1
                self.running = False

        self.poll_task = asyncio.create_task(polling_wrapper())
        logger.info("🚀 Account polling started (3-second cycle)")

    async def stop_polling(self) -> None:
        """Stop account polling task"""
        if self.poll_task:
            self.poll_task.cancel()
            try:
                await self.poll_task
            except asyncio.CancelledError:
                pass

        self.running = False
        logger.info("🛑 Account polling stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get polling statistics"""
        current_time = int(time.time() * 1000)
        last_poll_age = current_time - self.metrics.get("lastAccountTs", 0)

        return {
            "running": self.running,
            "last_poll_age_ms": last_poll_age,
            "poll_success_count": self.metrics.get("accountPollSuccess", 0),
            "poll_error_count": self.metrics.get("accountPollErrors", 0),
            "callbacks_registered": len(self.account_callbacks)
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status for health endpoint"""
        current_time = int(time.time() * 1000)
        last_account_ts = self.metrics.get("lastAccountTs", 0)
        age_ms = current_time - last_account_ts if last_account_ts > 0 else float("inf")

        return {
            "account_heartbeat_age_ms": age_ms,
            "account_polling_active": self.running,
            "account_last_success": last_account_ts > 0
        }

# Example usage and testing
async def test_account_poller():
    """Test the account poller system"""
    print("🧪 Testing Account Poller System")
    print("=" * 40)

    # Mock connection for testing
    class MockConnection:
        def __init__(self):
            self.call_count = 0

        async def send_and_wait(self, request):
            self.call_count += 1
            # Simulate broker response
            return {
                "balance": 1000.50 + self.call_count,
                "equity": 1005.75 + self.call_count,
                "margin": 50.25,
                "free_margin": 955.50 + self.call_count,
                "leverage": 100,
                "currency": "USD"
            }

    # Create test setup
    mock_conn = MockConnection()
    poller = AccountPoller()

    received_accounts = []

    def account_handler(account_data):
        received_accounts.append(account_data)
        print(f"📊 Account Update: {account_data[currency]} {account_data[balance]:.2f}")

    poller.add_account_callback(account_handler)

    # Test short polling cycle
    print("🚀 Starting 5-second test polling...")
    await poller.start_polling(mock_conn)

    # Let it poll a few times
    await asyncio.sleep(7)  # Should get 2-3 polls

    await poller.stop_polling()

    # Verify results
    print(f"\n📊 Test Results:")
    print(f"  Polls received: {len(received_accounts)}")
    print(f"  Connection calls: {mock_conn.call_count}")

    if received_accounts:
        latest = received_accounts[-1]
        print(f"  Latest balance: {latest[balance]:.2f}")
        print(f"  Latest equity: {latest[equity]:.2f}")
        print(f"  Source: {latest[src]}")

    # Show stats
    stats = poller.get_stats()
    print(f"\n📈 Poller Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Show health status
    health = poller.get_health_status()
    print(f"\n💚 Health Status:")
    for key, value in health.items():
        print(f"  {key}: {value}")

    print("\n🎉 Account poller test completed!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_account_poller())
