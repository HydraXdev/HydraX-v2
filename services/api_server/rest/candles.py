"""
Historical Candles API - Serve OHLC data for forex charts
Grok-Enhanced Implementation - October 19, 2025

Features:
- Load M1 data from candle cache
- Resample to any timeframe (M1/M5/M15/H1/H4/D1)
- Return last 200 candles in lightweight-charts format
- CORS support for Firebase hosting frontend
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
import pandas as pd
import json
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/candles", tags=["candles"])


# ============================================================================
# MODELS & ENUMS
# ============================================================================

class Timeframe(str, Enum):
    """Supported timeframes"""
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"


class Candle(BaseModel):
    """Individual candle data"""
    time: int  # Unix timestamp in seconds
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = 0.0


class CandleArrayResponse(BaseModel):
    """Lightweight-charts compatible array format"""
    success: bool = True
    symbol: str
    timeframe: str
    count: int
    candles: List[Candle] = []


class SymbolsResponse(BaseModel):
    """Available symbols response"""
    success: bool = True
    symbols: List[str]
    count: int


# ============================================================================
# CONSTANTS
# ============================================================================

CANDLE_CACHE_PATH = "/root/HydraX-v2/candle_cache.json"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_candle_cache() -> dict:
    """Load the candle cache JSON file."""
    try:
        if not os.path.exists(CANDLE_CACHE_PATH):
            logger.error(f"Candle cache not found at {CANDLE_CACHE_PATH}")
            raise HTTPException(
                status_code=500,
                detail="Candle cache file not found"
            )

        with open(CANDLE_CACHE_PATH, 'r') as f:
            data = json.load(f)

        # Extract m1_data if structure is {"m1_data": {...}}
        if 'm1_data' in data and isinstance(data['m1_data'], dict):
            data = data['m1_data']

        logger.info(f"Loaded candle cache with {len(data)} symbols")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Invalid candle cache format"
        )
    except Exception as e:
        logger.error(f"Error loading candle cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load candle cache: {str(e)}"
        )


def parse_m1_candles(m1_data: list) -> pd.DataFrame:
    """Parse M1 candle data into pandas DataFrame."""
    try:
        df = pd.DataFrame(m1_data)

        # Check required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            # Try alternative 'time' field
            if 'time' in df.columns:
                df['timestamp'] = df['time']
            else:
                raise ValueError(f"Missing required columns: {missing_cols}")

        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('datetime', inplace=True)

        # Convert price columns to float
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Add volume if missing (default 0 for forex)
        if 'volume' not in df.columns:
            df['volume'] = 0.0
        else:
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0.0)

        # Sort by datetime
        df.sort_index(inplace=True)

        # Drop rows with NaN values in OHLC
        df.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)

        return df

    except Exception as e:
        logger.error(f"Error parsing M1 candles: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid M1 data format: {str(e)}"
        )


def resample_candles(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample M1 data to requested timeframe using OHLC aggregation."""
    try:
        # Define resampling rules
        resample_rules = {
            "M1": None,  # No resampling needed
            "M5": "5min",
            "M15": "15min",
            "H1": "1H",
            "H4": "4H",
            "D1": "1D",
        }

        rule = resample_rules.get(timeframe)
        if rule is None:
            if timeframe == "M1":
                return df  # Return M1 data as-is
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        # Resample using OHLC aggregation
        resampled = df.resample(rule).agg({
            'open': 'first',   # First price in period
            'high': 'max',     # Highest price in period
            'low': 'min',      # Lowest price in period
            'close': 'last',   # Last price in period
            'volume': 'sum'    # Sum of volume in period
        }).dropna()

        return resampled

    except Exception as e:
        logger.error(f"Error resampling candles: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Resampling failed: {str(e)}"
        )


def format_for_response(df: pd.DataFrame, symbol: str, timeframe: str, limit: int = 200) -> CandleArrayResponse:
    """Format DataFrame as lightweight-charts compatible response."""
    try:
        # Take last N candles
        df_limited = df.tail(limit)

        # Convert to list of Candle objects
        candles = []
        for idx, row in df_limited.iterrows():
            candles.append(Candle(
                time=int(idx.timestamp()),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=float(row.get('volume', 0.0))
            ))

        return CandleArrayResponse(
            success=True,
            symbol=symbol,
            timeframe=timeframe,
            count=len(candles),
            candles=candles
        )

    except Exception as e:
        logger.error(f"Error formatting response: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Formatting failed: {str(e)}"
        )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/{symbol}", response_model=CandleArrayResponse)
async def get_candles(
    symbol: str,
    timeframe: Timeframe = Query(..., description="Timeframe: M1, M5, M15, H1, H4, D1"),
    limit: int = Query(200, ge=1, le=1000, description="Number of candles to return")
):
    """
    Get historical forex candle data for a given symbol and timeframe.

    - **symbol**: Forex pair (e.g., EURUSD, GBPUSD)
    - **timeframe**: Requested timeframe (M1, M5, M15, H1, H4, D1)
    - **limit**: Number of candles to return (default: 200, max: 1000)

    Returns candles in lightweight-charts compatible format with:
    - time: Unix timestamp in seconds
    - open, high, low, close: OHLC prices
    - volume: Trading volume (0 for forex pairs)
    """
    try:
        logger.info(f"📊 Candle request: {symbol} {timeframe} (limit: {limit})")

        # Load cache
        cache_data = load_candle_cache()

        # Get M1 data for symbol
        if symbol not in cache_data:
            logger.warning(f"Symbol {symbol} not found in cache")
            raise HTTPException(
                status_code=404,
                detail=f"Symbol {symbol} not found in candle cache"
            )

        m1_data = cache_data[symbol]
        if not m1_data:
            raise HTTPException(
                status_code=404,
                detail=f"No M1 data available for symbol {symbol}"
            )

        # Parse M1 data
        df = parse_m1_candles(m1_data)
        logger.info(f"Parsed {len(df)} M1 candles for {symbol}")

        # Resample if needed
        if timeframe == "M1":
            df_final = df
        else:
            df_final = resample_candles(df, timeframe.value)
            logger.info(f"Resampled to {timeframe}: {len(df_final)} candles")

        if len(df_final) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No data available for {symbol} {timeframe}"
            )

        # Format response
        result = format_for_response(df_final, symbol, timeframe.value, limit)
        logger.info(f"✅ Returning {result.count} {timeframe} candles for {symbol}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in get_candles: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("", response_model=SymbolsResponse)
async def get_available_symbols():
    """
    Get list of available symbols in the candle cache.

    Returns all forex pairs currently available for charting.
    """
    try:
        cache_data = load_candle_cache()
        symbols = sorted(list(cache_data.keys()))

        logger.info(f"📋 Returning {len(symbols)} available symbols")

        return SymbolsResponse(
            success=True,
            symbols=symbols,
            count=len(symbols)
        )

    except Exception as e:
        logger.error(f"❌ Error getting available symbols: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get available symbols"
        )
