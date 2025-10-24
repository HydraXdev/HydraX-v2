#!/usr/bin/env python3
"""
Finnhub Historical Data Backfill Script
========================================
Fetches historical M1 candles from Finnhub REST API and populates Redis cache.
This allows Elite Guard to instantly have M5/M15 data via aggregation instead
of waiting 30+ minutes for candles to accumulate organically.

Usage:
    python3 finnhub_backfill.py [--symbols EURUSD,GBPUSD,...] [--minutes 500]
"""

import argparse
import json
import time
from datetime import datetime, timedelta

import redis
import requests

# Finnhub configuration
FINNHUB_API_KEY = "d3rvpb1r01qldtrba440d3rvpb1r01qldtrba44g"
FINNHUB_REST_URL = "https://finnhub.io/api/v1/forex/candle"

# Redis configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Default symbols to backfill (Finnhub has data for these)
DEFAULT_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD",
    "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "EURGBP", "EURAUD",
    "GBPAUD", "XAUUSD", "XAGUSD", "USDCNH"
]

def convert_to_finnhub_symbol(mt5_symbol):
    """Convert MT5 symbol (EURUSD) to Finnhub format (OANDA:EUR_USD)"""
    if mt5_symbol.startswith('XAU'):
        return 'OANDA:XAU_USD'
    elif mt5_symbol.startswith('XAG'):
        return 'OANDA:XAG_USD'
    else:
        base = mt5_symbol[:3]
        quote = mt5_symbol[3:6]
        return f'OANDA:{base}_{quote}'

def fetch_historical_candles(symbol, minutes=500):
    """
    Fetch historical M1 candles from Finnhub REST API

    Args:
        symbol: MT5 symbol (e.g., 'EURUSD')
        minutes: Number of minutes to fetch (default 500 = ~8 hours)

    Returns:
        List of candle dicts or None if failed
    """
    finnhub_symbol = convert_to_finnhub_symbol(symbol)

    # Calculate time range (now - minutes)
    end_time = int(time.time())
    start_time = end_time - (minutes * 60)

    print(f"📡 Fetching {minutes} M1 candles for {symbol} ({finnhub_symbol})...")

    params = {
        'symbol': finnhub_symbol,
        'resolution': '1',  # 1 minute candles
        'from': start_time,
        'to': end_time,
        'token': FINNHUB_API_KEY
    }

    try:
        response = requests.get(FINNHUB_REST_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Check if we got data
        if data.get('s') != 'ok':
            print(f"⚠️  {symbol}: No data (status: {data.get('s')})")
            return None

        # Convert to our candle format
        candles = []
        for i in range(len(data['t'])):
            candle = {
                'time': data['t'][i],
                'open': data['o'][i],
                'high': data['h'][i],
                'low': data['l'][i],
                'close': data['c'][i],
                'volume': data.get('v', [0] * len(data['t']))[i],
                'source': 'finnhub_rest',
                'symbol': symbol
            }
            candles.append(candle)

        print(f"✅ {symbol}: Fetched {len(candles)} candles")
        return candles

    except requests.exceptions.RequestException as e:
        print(f"❌ {symbol}: Request failed - {e}")
        return None
    except Exception as e:
        print(f"❌ {symbol}: Error - {e}")
        return None

def store_candles_in_redis(symbol, candles):
    """
    Store candles in Redis using same format as WebSocket manager

    Args:
        symbol: MT5 symbol
        candles: List of candle dicts

    Returns:
        True if successful, False otherwise
    """
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

        # Store as JSON string in Redis key
        key = f'candle_1m_{symbol}_history'
        data = json.dumps(candles)
        r.set(key, data)

        # Also store the latest candle separately for quick access
        if candles:
            latest_key = f'candle_1m_{symbol}_latest'
            r.set(latest_key, json.dumps(candles[-1]))

        print(f"💾 {symbol}: Stored {len(candles)} candles in Redis")
        return True

    except Exception as e:
        print(f"❌ {symbol}: Redis storage failed - {e}")
        return False

def backfill_symbol(symbol, minutes=500):
    """
    Backfill historical data for a single symbol

    Args:
        symbol: MT5 symbol
        minutes: Number of minutes to fetch

    Returns:
        Number of candles stored, or 0 if failed
    """
    candles = fetch_historical_candles(symbol, minutes)

    if candles:
        if store_candles_in_redis(symbol, candles):
            return len(candles)

    return 0

def main():
    parser = argparse.ArgumentParser(description='Backfill Finnhub historical candle data')
    parser.add_argument('--symbols', type=str, help='Comma-separated list of symbols (default: all 17)')
    parser.add_argument('--minutes', type=int, default=500, help='Number of minutes to fetch (default: 500)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between API calls in seconds (default: 0.5)')

    args = parser.parse_args()

    # Parse symbols
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(',')]
    else:
        symbols = DEFAULT_SYMBOLS

    print(f"\n🚀 FINNHUB BACKFILL STARTED")
    print(f"=" * 60)
    print(f"Symbols: {len(symbols)} ({', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''})")
    print(f"Minutes: {args.minutes} (~{args.minutes/60:.1f} hours)")
    print(f"API Delay: {args.delay}s")
    print(f"=" * 60)
    print()

    # Backfill each symbol
    total_candles = 0
    successful = 0
    failed = 0

    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] Processing {symbol}...")

        count = backfill_symbol(symbol, args.minutes)

        if count > 0:
            total_candles += count
            successful += 1
        else:
            failed += 1

        # Rate limiting delay (except for last symbol)
        if i < len(symbols):
            time.sleep(args.delay)

        print()

    print(f"\n{'=' * 60}")
    print(f"✅ BACKFILL COMPLETE")
    print(f"=" * 60)
    print(f"Successful: {successful}/{len(symbols)}")
    print(f"Failed: {failed}/{len(symbols)}")
    print(f"Total candles stored: {total_candles:,}")
    print(f"\n📊 Next Steps:")
    print(f"1. Elite Guard will automatically aggregate M1 → M5 → M15 on next poll (~5s)")
    print(f"2. With {args.minutes} M1 candles, you'll get ~{args.minutes//5} M5 and ~{args.minutes//15} M15 candles")
    print(f"3. Patterns requiring M15 will activate immediately")
    print(f"4. Monitor: pm2 logs elite_guard | grep 'Total candles'")
    print()

if __name__ == '__main__':
    main()
