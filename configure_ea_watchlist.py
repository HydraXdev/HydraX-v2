#!/usr/bin/env python3
"""
Configure EA watchlist for market data feed

Sends configure_feed command to EA via HydraSocket router to set up
symbols and timeframes for market data streaming.

Usage:
    python3 configure_ea_watchlist.py --account 843859
"""

import socket
import json
import time
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger('ConfigureWatchlist')

# Default symbols for Elite Guard patterns (20 pairs)
DEFAULT_SYMBOLS = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD',
    'NZDUSD', 'EURJPY', 'GBPJPY', 'EURGBP', 'AUDJPY', 'EURAUD',
    'EURCHF', 'AUDNZD', 'NZDJPY', 'GBPAUD', 'GBPCAD', 'GBPCHF',
    'EURCAD', 'AUDCAD'
]

# Timeframes for pattern detection
DEFAULT_TIMEFRAMES = ['M1', 'M5', 'M15']


def send_configure_feed(account_id, symbols=None, timeframes=None, lookback=200,
                       host='127.0.0.1', port=5555, timeout=10.0):
    """
    Send configure_feed command to EA

    Args:
        account_id: EA account ID
        symbols: List of symbols (default: 20 major pairs)
        timeframes: List of timeframes (default: M1, M5, M15)
        lookback: Number of candles to load (default: 200)
        host: Router host
        port: Command port (5555)
        timeout: Response timeout
    """

    if symbols is None:
        symbols = DEFAULT_SYMBOLS
    if timeframes is None:
        timeframes = DEFAULT_TIMEFRAMES

    try:
        # Connect to command router
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.settimeout(timeout)

        # Create configure_feed command (EA format)
        command = {
            'type': 'configure_feed',
            'request_ref': f'config-{account_id}-{int(time.time())}',
            'account_id': account_id,  # For router routing
            'symbols': ','.join(symbols),
            'tfs': ','.join(timeframes),
            'lookback': lookback,
            'midbar': False,  # Disable mid-bar snapshots
            'midsec': 0
        }

        # Send as JSONL
        payload = json.dumps(command) + '\n'
        sock.send(payload.encode('utf-8'))

        logger.info(f"📡 Sent configure_feed to account {account_id}")
        logger.info(f"   Symbols: {len(symbols)} pairs")
        logger.info(f"   Timeframes: {', '.join(timeframes)}")
        logger.info(f"   Lookback: {lookback} candles")

        # Wait for response
        response_data = b''
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk

                # Check if we have complete JSON
                if b'\n' in response_data:
                    break
            except socket.timeout:
                break

        sock.close()

        if response_data:
            try:
                response = json.loads(response_data.decode('utf-8').strip())
                if response.get('status') == 'success':
                    logger.info(f"✅ Configuration successful")
                    logger.info(f"   Response: {response.get('info', 'OK')}")
                    return True
                else:
                    logger.warning(f"⚠️ EA response: {response.get('message', 'Unknown')}")
                    return False
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON response: {e}")
                logger.error(f"   Raw: {response_data[:200]}")
                return False
        else:
            logger.warning(f"⏱️ No response within {timeout}s (command may still be processing)")
            logger.info(f"   Check /var/log/hydrasocket_universal_bridge.log for confirmation")
            return None

    except ConnectionRefusedError:
        logger.error(f"❌ Connection refused to {host}:{port}")
        logger.error(f"   Is HydraSocket router running?")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to configure EA: {e}")
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Configure EA watchlist for market data'
    )
    parser.add_argument('--account', type=str, required=True,
                       help='Account ID to configure')
    parser.add_argument('--symbols', type=str,
                       help='Comma-separated symbol list (default: 20 major pairs)')
    parser.add_argument('--timeframes', type=str,
                       help='Comma-separated timeframes (default: M1,M5,M15)')
    parser.add_argument('--lookback', type=int, default=200,
                       help='Candles to load (default: 200)')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                       help='Router host')
    parser.add_argument('--port', type=int, default=5555,
                       help='Router command port')
    parser.add_argument('--timeout', type=float, default=10.0,
                       help='Response timeout in seconds')

    args = parser.parse_args()

    # Parse symbol list if provided
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]

    # Parse timeframe list if provided
    timeframes = None
    if args.timeframes:
        timeframes = [tf.strip() for tf in args.timeframes.split(',')]

    print("=" * 60)
    print("🔧 HydraSocket EA Watchlist Configuration")
    print("=" * 60)
    print()

    result = send_configure_feed(
        args.account,
        symbols=symbols,
        timeframes=timeframes,
        lookback=args.lookback,
        host=args.host,
        port=args.port,
        timeout=args.timeout
    )

    print()
    if result is True:
        print("✅ Configuration complete!")
        print()
        print("📊 Next steps:")
        print("  1. Monitor Universal Bridge: tail -f /var/log/hydrasocket_universal_bridge.log")
        print("  2. Check Elite Guard data: pm2 logs elite-guard --lines 20")
        print("  3. Wait 1-2 minutes for candle building to complete")
        print("  4. Verify pattern scanning starts with 20 symbols")
    elif result is False:
        print("❌ Configuration failed")
        exit(1)
    else:
        print("⏱️ Command sent, response pending")
        print("   Check logs to verify")
