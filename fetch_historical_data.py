#!/usr/bin/env python3
"""
Fetch 9 Months of Historical Finnhub Data

PURPOSE:
    Download historical M1 and H4 candle data from Finnhub for backtesting
    the Phase 1 universal modules (Order Flow, Volume, Sentiment, MTF, Anomaly)

USAGE:
    python3 fetch_historical_data.py

OUTPUT:
    - /root/HydraX-v2/backtest_data/{SYMBOL}_M1.json (9 months of M1 candles)
    - /root/HydraX-v2/backtest_data/{SYMBOL}_H4.json (9 months of H4 candles)

REQUIREMENTS:
    - Finnhub API key (d3rvpb1r01qldtrba440d3rvpb1r01qldtrba44g)
    - 9 months = ~388,800 M1 candles per symbol
    - 7 major pairs = ~2.7M candles total
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List

# Finnhub API configuration
FINNHUB_API_KEY = 'd3rvpb1r01qldtrba440d3rvpb1r01qldtrba44g'
FINNHUB_BASE_URL = 'https://finnhub.io/api/v1'

# Major pairs for backtesting
MAJOR_PAIRS = [
    'OANDA:EUR_USD',
    'OANDA:GBP_USD',
    'OANDA:USD_JPY',
    'OANDA:AUD_USD',
    'OANDA:USD_CAD',
    'OANDA:EUR_JPY',
    'OANDA:GBP_JPY'
]

# Timeframe configuration
TIMEFRAMES = {
    'M1': '1',    # 1-minute candles
    'H4': '240'   # 4-hour candles
}

# Data directory
DATA_DIR = '/root/HydraX-v2/backtest_data'

class FinnhubDataFetcher:
    """Fetch historical candle data from Finnhub API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({'X-Finnhub-Token': api_key})

    def fetch_candles(
        self,
        symbol: str,
        resolution: str,
        from_ts: int,
        to_ts: int,
        retries: int = 3
    ) -> Dict:
        """
        Fetch candles from Finnhub API with retry logic

        Args:
            symbol: Finnhub symbol (e.g., 'OANDA:EUR_USD')
            resolution: Timeframe (1 for M1, 240 for H4)
            from_ts: Start timestamp (Unix)
            to_ts: End timestamp (Unix)
            retries: Number of retry attempts

        Returns:
            Dict with candle data or error
        """
        url = f"{FINNHUB_BASE_URL}/forex/candle"
        params = {
            'symbol': symbol,
            'resolution': resolution,
            'from': from_ts,
            'to': to_ts
        }

        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()

                    # Check if data returned
                    if data.get('s') == 'ok':
                        return {
                            'status': 'success',
                            'candles': len(data.get('t', [])),
                            'data': data
                        }
                    else:
                        return {
                            'status': 'no_data',
                            'error': f"Finnhub returned status: {data.get('s')}"
                        }

                elif response.status_code == 429:
                    # Rate limit - wait and retry
                    wait_time = (attempt + 1) * 2
                    print(f"   ⚠️  Rate limit hit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                else:
                    return {
                        'status': 'error',
                        'error': f"HTTP {response.status_code}: {response.text}"
                    }

            except Exception as e:
                if attempt < retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"   ⚠️  Error: {e}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    return {
                        'status': 'error',
                        'error': str(e)
                    }

        return {
            'status': 'error',
            'error': 'Max retries exceeded'
        }

    def fetch_range(
        self,
        symbol: str,
        resolution: str,
        start_date: datetime,
        end_date: datetime,
        chunk_days: int = 30
    ) -> List[Dict]:
        """
        Fetch data in chunks to avoid API limits

        Args:
            symbol: Finnhub symbol
            resolution: Timeframe (1 or 240)
            start_date: Start date
            end_date: End date
            chunk_days: Days per API call (default 30)

        Returns:
            List of candle dictionaries
        """
        all_candles = []
        current_start = start_date

        while current_start < end_date:
            # Calculate chunk end (30 days or end date)
            current_end = min(
                current_start + timedelta(days=chunk_days),
                end_date
            )

            # Convert to Unix timestamps
            from_ts = int(current_start.timestamp())
            to_ts = int(current_end.timestamp())

            print(f"   📥 Fetching {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}...")

            # Fetch chunk
            result = self.fetch_candles(symbol, resolution, from_ts, to_ts)

            if result['status'] == 'success':
                data = result['data']

                # Convert to candle dictionaries
                for i in range(len(data['t'])):
                    candle = {
                        'timestamp': data['t'][i],
                        'open': data['o'][i],
                        'high': data['h'][i],
                        'low': data['l'][i],
                        'close': data['c'][i],
                        'volume': data['v'][i] if 'v' in data else 0
                    }
                    all_candles.append(candle)

                print(f"   ✅ Got {len(data['t'])} candles")

            elif result['status'] == 'no_data':
                print(f"   ⚠️  No data available for this period")
            else:
                print(f"   ❌ Error: {result['error']}")

            # Move to next chunk
            current_start = current_end

            # Rate limiting - wait 1 second between API calls
            time.sleep(1)

        return all_candles


def main():
    """Fetch 9 months of historical data for all major pairs"""

    print("\n" + "="*80)
    print("📊 FETCHING 9 MONTHS OF HISTORICAL DATA FOR BACKTESTING")
    print("="*80 + "\n")

    # Create data directory
    os.makedirs(DATA_DIR, exist_ok=True)

    # Initialize fetcher
    fetcher = FinnhubDataFetcher(FINNHUB_API_KEY)

    # Calculate date range (9 months back from today)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=270)  # ~9 months

    print(f"📅 Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"📈 Pairs: {len(MAJOR_PAIRS)}")
    print(f"📊 Timeframes: M1 (1-minute), H4 (4-hour)")
    print(f"💾 Output: {DATA_DIR}/\n")

    # Summary statistics
    total_pairs = len(MAJOR_PAIRS)
    total_timeframes = len(TIMEFRAMES)
    total_fetches = total_pairs * total_timeframes
    completed = 0

    # Fetch data for each pair and timeframe
    for symbol in MAJOR_PAIRS:
        # Clean symbol name for filename
        clean_symbol = symbol.replace('OANDA:', '').replace('_', '')

        print(f"\n{'='*80}")
        print(f"📈 {clean_symbol} ({completed+1}/{total_fetches})")
        print(f"{'='*80}")

        for timeframe_name, resolution in TIMEFRAMES.items():
            completed += 1

            print(f"\n🔄 Fetching {timeframe_name} candles...")

            # Fetch candles
            candles = fetcher.fetch_range(
                symbol=symbol,
                resolution=resolution,
                start_date=start_date,
                end_date=end_date,
                chunk_days=30  # 30-day chunks
            )

            if candles:
                # Save to file
                output_file = f"{DATA_DIR}/{clean_symbol}_{timeframe_name}.json"

                with open(output_file, 'w') as f:
                    json.dump({
                        'symbol': clean_symbol,
                        'timeframe': timeframe_name,
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'candles': candles,
                        'count': len(candles)
                    }, f, indent=2)

                print(f"   💾 Saved {len(candles):,} candles to {output_file}")

                # Calculate data coverage
                expected_candles = {
                    'M1': 270 * 24 * 60,  # ~388,800 candles
                    'H4': 270 * 6         # ~1,620 candles
                }

                coverage = (len(candles) / expected_candles[timeframe_name]) * 100
                print(f"   📊 Coverage: {coverage:.1f}% of expected candles")

            else:
                print(f"   ❌ No candles fetched for {timeframe_name}")

            # Progress indicator
            progress = (completed / total_fetches) * 100
            print(f"\n   ⏳ Overall Progress: {completed}/{total_fetches} ({progress:.1f}%)")

    print("\n" + "="*80)
    print("✅ HISTORICAL DATA FETCH COMPLETE")
    print("="*80)
    print(f"\n📁 Data saved to: {DATA_DIR}/")
    print(f"📊 Total files: {len(os.listdir(DATA_DIR))}")
    print("\nNext step: Run validate_modules.py to test modules with this data\n")


if __name__ == '__main__':
    main()
