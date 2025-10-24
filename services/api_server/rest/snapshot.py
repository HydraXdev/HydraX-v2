"""
Chart Snapshot API - Generate professional MT5-quality forex chart images
Grok-Enhanced Version - October 19, 2025
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/snapshot", tags=["snapshot"])


# ============================================================================
# PROFESSIONAL MT5-QUALITY CHART GENERATION (GROK-ENHANCED)
# ============================================================================

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplfinance as mpf
import pandas as pd
import numpy as np
import base64
import io
from datetime import datetime


def generate_mt5_quality_chart(symbol, bars, entry, sl, tp, pattern_type, direction):
    """
    Generate professional MetaTrader 5 quality forex chart snapshot.

    Based on Grok AI consultation October 19, 2025 for maximum visual polish.

    Parameters:
    - symbol (str): Forex symbol (e.g., 'EURUSD')
    - bars (list of dicts): OHLC data with keys 'time', 'open', 'high', 'low', 'close'
    - entry (float): Entry price level
    - sl (float): Stop loss price level
    - tp (float): Take profit price level
    - pattern_type (str): Pattern type (e.g., 'ORDER_BLOCK_BOUNCE')
    - direction (str): Trade direction ('BUY' or 'SELL')

    Returns:
    - str: Base64-encoded PNG image with 'data:image/png;base64,' prefix
    """
    try:
        # Validate inputs
        if not isinstance(bars, list) or not bars:
            raise ValueError("Bars must be a non-empty list of dictionaries.")
        if direction not in ['BUY', 'SELL']:
            raise ValueError("Direction must be 'BUY' or 'SELL'.")

        # Convert bars to DataFrame
        df = pd.DataFrame(bars)
        df['time'] = pd.to_datetime(df['time'], errors='raise', unit='s')
        df.set_index('time', inplace=True)
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close'
        }, inplace=True)

        # Add volume column if missing (required by mplfinance)
        if 'Volume' not in df.columns:
            df['Volume'] = np.random.randint(1000, 10000, len(df))

        # MT5-inspired style configuration
        mt5_colors = mpf.make_marketcolors(
            up='#00aa00',      # Green bullish candles
            down='#aa0000',    # Red bearish candles
            edge='inherit',
            wick='inherit',
            volume={'up': '#00aa0033', 'down': '#aa000033'},
            alpha=0.85
        )

        mt5_style = mpf.make_mpf_style(
            marketcolors=mt5_colors,
            figcolor='#1a1a26',      # Very dark background
            facecolor='#1f1f2e',     # Panel background
            edgecolor='#333338',     # Panel edges
            gridcolor='#404045',     # Grid color
            gridstyle='-',
            gridaxis='both',
            rc={
                'font.size': 9,
                'font.family': ['DejaVu Sans', 'Arial', 'sans-serif'],
                'axes.labelsize': 10,
                'axes.titlesize': 12,
                'xtick.labelsize': 8,
                'ytick.labelsize': 8,
                'axes.linewidth': 0.8,
                'axes.edgecolor': '#4d4d55',
                'xtick.color': '#999999',
                'ytick.color': '#999999',
            }
        )

        # Prepare horizontal lines for entry/SL/TP
        hlines = dict(
            hlines=[entry, sl, tp],
            colors=['#0066ff', '#ff0000', '#00ff00'],
            linestyle=['-', '--', '--'],
            linewidths=[2, 1.5, 1.5],
            alpha=0.8
        )

        # Create the professional chart (1200x600px at 100 DPI = 12x6 inches)
        fig, axes = mpf.plot(
            df,
            type='candle',
            style=mt5_style,
            volume=False,  # No volume panel for cleaner look
            figsize=(12, 6),
            title=f'{symbol} - {pattern_type}',
            ylabel=f'{symbol} Price',
            hlines=hlines,
            returnfig=True,
            tight_layout=True,
            scale_padding=dict(left=0.02, right=0.15, top=0.05, bottom=0.05),
            panel_ratios=(1,)
        )

        ax_main = axes[0]

        # Professional grid system
        ax_main.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='#404045')
        ax_main.set_axisbelow(True)

        # Position price axis on right (MT5 style)
        ax_main.yaxis.set_label_position("right")
        ax_main.yaxis.tick_right()

        # Enhanced horizontal lines with labels
        # Entry line (blue)
        ax_main.axhline(y=entry, color='#0066ff', linestyle='-', linewidth=2, alpha=0.8, zorder=5)
        ax_main.annotate('ENTRY', xy=(0.02, entry), xycoords=('axes fraction', 'data'),
                        color='#0066ff', fontsize=9, fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='#0066ff20',
                                 edgecolor='#0066ff', linewidth=1),
                        ha='left', va='center')

        # Stop Loss line (red dashed)
        ax_main.axhline(y=sl, color='#ff0000', linestyle='--', linewidth=1.5, alpha=0.7, zorder=4)
        ax_main.annotate('SL', xy=(0.02, sl), xycoords=('axes fraction', 'data'),
                        color='#ff0000', fontsize=9, fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='#ff000020',
                                 edgecolor='#ff0000', linewidth=1),
                        ha='left', va='center')

        # Take Profit line (green dashed)
        ax_main.axhline(y=tp, color='#00ff00', linestyle='--', linewidth=1.5, alpha=0.7, zorder=4)
        ax_main.annotate('TP', xy=(0.02, tp), xycoords=('axes fraction', 'data'),
                        color='#00ff00', fontsize=9, fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='#00ff0020',
                                 edgecolor='#00ff00', linewidth=1),
                        ha='left', va='center')

        # Add shaded zone for ORDER_BLOCK pattern (between SL and entry)
        if pattern_type == 'ORDER_BLOCK_BOUNCE':
            ax_main.axhspan(min(sl, entry), max(sl, entry),
                           facecolor='#3b82f6', alpha=0.15, zorder=1)

        # Add shaded TP target zone (between entry and midpoint to TP)
        midpoint = (entry + tp) / 2
        ax_main.axhspan(min(entry, midpoint), max(entry, midpoint),
                       facecolor='#eab308', alpha=0.2, zorder=1)

        # Pattern name annotation in top-left
        pattern_display = pattern_type.replace('_', ' ')
        ax_main.annotate(f"{direction} {pattern_display}",
                        xy=(0.02, 0.98), xycoords='axes fraction',
                        fontsize=11, color='#ffffff', fontweight='bold',
                        va='top', ha='left',
                        bbox=dict(boxstyle="round,pad=0.4", facecolor='#2d2d3a',
                                 edgecolor='#0066ff', linewidth=1.5, alpha=0.9))

        # Direction arrow on entry line (right side)
        arrow_color = '#00ff00' if direction == 'BUY' else '#ff0000'
        arrow_style = '^' if direction == 'BUY' else 'v'
        ax_main.annotate('', xy=(0.98, entry), xycoords=('axes fraction', 'data'),
                        xytext=(0.95, entry), textcoords=('axes fraction', 'data'),
                        arrowprops=dict(arrowstyle='->', color=arrow_color,
                                      linewidth=2.5, alpha=0.9))

        # Format price labels (5 decimal places for forex precision)
        ax_main.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.5f}'))

        # Format time labels
        ax_main.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M\n%d-%b'))
        plt.setp(ax_main.xaxis.get_majorticklabels(), rotation=0, ha='center')

        # Add timestamp watermark
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
        fig.text(0.98, 0.02, f'Generated: {timestamp}',
                ha='right', va='bottom', fontsize=7, color='#666666', alpha=0.7)

        # Save to BytesIO with professional quality
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                   facecolor='#1a1a26', edgecolor='none')
        buf.seek(0)

        # Close plot to free memory
        plt.close(fig)

        # Encode to base64
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return f'data:image/png;base64,{img_base64}'

    except Exception as e:
        raise RuntimeError(f"Error generating MT5-quality chart: {str(e)}")


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class SnapshotBar(BaseModel):
    time: int  # Unix timestamp
    open: float
    high: float
    low: float
    close: float


class SnapshotRequest(BaseModel):
    signal_id: str
    symbol: str
    bars: List[Dict]  # List of OHLC dicts
    entry: float
    sl: float
    tp: float
    pattern_type: str
    direction: str  # BUY or SELL
    created_at: str | None = None  # ISO8601 timestamp


class SnapshotResponse(BaseModel):
    success: bool
    image_base64: str | None = None
    width: int = 1200
    height: int = 600
    error: str | None = None


# ============================================================================
# API ENDPOINT
# ============================================================================

@router.post("", response_model=SnapshotResponse)
async def create_snapshot(request: SnapshotRequest):
    """
    Generate professional MT5-quality chart snapshot for Mission Brief.

    Enhanced with Grok AI consultation for maximum visual polish:
    - MetaTrader 5 dark theme
    - Professional grid system
    - Clean candlesticks with proper wicks
    - Price labels on right axis
    - Time labels on bottom
    - Entry/SL/TP annotations
    - Pattern overlays (shaded zones)
    - Direction arrows

    Returns Base64-encoded PNG image (1200x600px) ready for <img src="..." />.
    """
    try:
        logger.info(f"📸 Generating MT5-quality snapshot for {request.signal_id} ({request.symbol})")

        # Validate input
        if not request.bars or len(request.bars) == 0:
            raise HTTPException(status_code=400, detail="Bars array cannot be empty")

        if request.entry == 0 or request.sl == 0 or request.tp == 0:
            raise HTTPException(status_code=400, detail="Entry, SL, and TP must be non-zero")

        # Generate professional MT5-quality chart
        image_base64 = generate_mt5_quality_chart(
            symbol=request.symbol,
            bars=request.bars,
            entry=request.entry,
            sl=request.sl,
            tp=request.tp,
            pattern_type=request.pattern_type,
            direction=request.direction.upper()
        )

        logger.info(f"✅ MT5-quality snapshot generated for {request.signal_id}")

        return SnapshotResponse(
            success=True,
            image_base64=image_base64,
            width=1200,
            height=600
        )

    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        return SnapshotResponse(
            success=False,
            error=f"Validation error: {str(e)}"
        )
    except RuntimeError as e:
        logger.error(f"❌ Chart generation error: {e}")
        return SnapshotResponse(
            success=False,
            error=f"Chart generation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        return SnapshotResponse(
            success=False,
            error=f"Internal server error: {str(e)}"
        )
