"""
Heat Map Analytics for BITTEN
Visual TCS trend analysis for currency pairs
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from pathlib import Path
import statistics

logger = logging.getLogger(__name__)

class HeatLevel(Enum):
    """Heat levels for pairs"""
    FROZEN = "frozen"      # TCS < 50%
    COLD = "cold"          # TCS 50-60%
    NEUTRAL = "neutral"    # TCS 60-70%
    WARM = "warm"          # TCS 70-80%
    HOT = "hot"            # TCS 80-90%
    BLAZING = "blazing"    # TCS > 90%

@dataclass
class PairHeatData:
    """Heat data for a currency pair"""
    pair: str
    current_tcs: float
    average_tcs_24h: float
    average_tcs_7d: float
    trend_direction: str  # "up", "down", "stable"
    trend_strength: float  # 0-100%
    heat_level: HeatLevel
    signal_count_24h: int
    win_rate_24h: float
    last_updated: datetime
    historical_data: List[Tuple[datetime, float]] = field(default_factory=list)

@dataclass
class HeatMapSnapshot:
    """Complete heat map snapshot"""
    timestamp: datetime
    total_pairs: int
    hot_pairs: List[str]
    cold_pairs: List[str]
    trending_up: List[str]
    trending_down: List[str]
    pair_data: Dict[str, PairHeatData]
    market_sentiment: str  # "bullish", "bearish", "neutral"

class HeatMapAnalytics:
    """Analyzes and visualizes TCS trends across currency pairs"""
    
    # Major forex pairs to track
    TRACKED_PAIRS = [
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD",
        "NZDUSD", "EURGBP", "EURJPY", "GBPJPY"
    ]
    
    # Heat level thresholds
    HEAT_THRESHOLDS = {
        HeatLevel.FROZEN: (0, 50),
        HeatLevel.COLD: (50, 60),
        HeatLevel.NEUTRAL: (60, 70),
        HeatLevel.WARM: (70, 80),
        HeatLevel.HOT: (80, 90),
        HeatLevel.BLAZING: (90, 100)
    }
    
    # Colors for visualization
    HEAT_COLORS = {
        HeatLevel.FROZEN: "#0066CC",   # Deep blue
        HeatLevel.COLD: "#3399FF",     # Light blue
        HeatLevel.NEUTRAL: "#FFFF66",  # Yellow
        HeatLevel.WARM: "#FF9933",     # Orange
        HeatLevel.HOT: "#FF3333",      # Red
        HeatLevel.BLAZING: "#CC0000"   # Deep red
    }
    
    def __init__(self, data_dir: str = "data/heat_maps"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for pair data
        self.pair_cache: Dict[str, PairHeatData] = {}
        
        # Load historical data
        self._load_historical_data()
    
    def update_pair_tcs(self, pair: str, tcs_value: float, signal_result: Optional[bool] = None) -> None:
        """Update TCS data for a pair"""
        if pair not in self.pair_cache:
            self.pair_cache[pair] = PairHeatData(
                pair=pair,
                current_tcs=tcs_value,
                average_tcs_24h=tcs_value,
                average_tcs_7d=tcs_value,
                trend_direction="stable",
                trend_strength=0,
                heat_level=self._calculate_heat_level(tcs_value),
                signal_count_24h=0,
                win_rate_24h=0,
                last_updated=datetime.now(),
                historical_data=[]
            )
        
        pair_data = self.pair_cache[pair]
        
        # Update current TCS
        pair_data.current_tcs = tcs_value
        pair_data.last_updated = datetime.now()
        
        # Add to historical data
        pair_data.historical_data.append((datetime.now(), tcs_value))
        
        # Keep only last 7 days of data
        cutoff = datetime.now() - timedelta(days=7)
        pair_data.historical_data = [
            (ts, val) for ts, val in pair_data.historical_data 
            if ts > cutoff
        ]
        
        # Recalculate averages and trends
        self._recalculate_pair_metrics(pair_data)
        
        # Update heat level
        pair_data.heat_level = self._calculate_heat_level(pair_data.current_tcs)
        
        # Save updated data
        self._save_pair_data(pair)
    
    def get_heat_map(self, user_has_access: bool = True) -> Dict[str, Any]:
        """Get current heat map data"""
        if not user_has_access:
            return self._get_teaser_heat_map()
        
        # Create snapshot
        snapshot = self._create_snapshot()
        
        # Format for display
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "market_sentiment": snapshot.market_sentiment,
            "summary": {
                "total_pairs": snapshot.total_pairs,
                "hot_count": len(snapshot.hot_pairs),
                "cold_count": len(snapshot.cold_pairs),
                "trending_up_count": len(snapshot.trending_up),
                "trending_down_count": len(snapshot.trending_down)
            },
            "pairs": self._format_pairs_for_display(snapshot),
            "visual_grid": self._create_visual_grid(snapshot),
            "insights": self._generate_insights(snapshot)
        }
    
    def get_pair_details(self, pair: str, user_has_access: bool = True) -> Dict[str, Any]:
        """Get detailed analytics for a specific pair"""
        if not user_has_access:
            return {"error": "Heat Map access required", "upgrade_needed": True}
        
        if pair not in self.pair_cache:
            return {"error": "Pair not tracked"}
        
        pair_data = self.pair_cache[pair]
        
        # Get sparkline data
        sparkline = self._generate_sparkline(pair_data)
        
        return {
            "pair": pair,
            "current_tcs": pair_data.current_tcs,
            "heat_level": pair_data.heat_level.value,
            "heat_color": self.HEAT_COLORS[pair_data.heat_level],
            "averages": {
                "24h": round(pair_data.average_tcs_24h, 1),
                "7d": round(pair_data.average_tcs_7d, 1)
            },
            "trend": {
                "direction": pair_data.trend_direction,
                "strength": round(pair_data.trend_strength, 1),
                "description": self._describe_trend(pair_data)
            },
            "performance": {
                "signals_24h": pair_data.signal_count_24h,
                "win_rate_24h": round(pair_data.win_rate_24h, 1)
            },
            "sparkline": sparkline,
            "recommendation": self._get_pair_recommendation(pair_data)
        }
    
    def _calculate_heat_level(self, tcs: float) -> HeatLevel:
        """Calculate heat level from TCS value"""
        for level, (min_val, max_val) in self.HEAT_THRESHOLDS.items():
            if min_val <= tcs < max_val:
                return level
        return HeatLevel.BLAZING
    
    def _recalculate_pair_metrics(self, pair_data: PairHeatData) -> None:
        """Recalculate averages and trends"""
        now = datetime.now()
        
        # 24h average
        cutoff_24h = now - timedelta(hours=24)
        values_24h = [val for ts, val in pair_data.historical_data if ts > cutoff_24h]
        if values_24h:
            pair_data.average_tcs_24h = statistics.mean(values_24h)
        
        # 7d average
        values_7d = [val for ts, val in pair_data.historical_data]
        if values_7d:
            pair_data.average_tcs_7d = statistics.mean(values_7d)
        
        # Calculate trend
        if len(values_24h) >= 5:
            # Simple linear regression
            recent_values = values_24h[-10:]  # Last 10 readings
            if len(recent_values) >= 2:
                first_half = statistics.mean(recent_values[:len(recent_values)//2])
                second_half = statistics.mean(recent_values[len(recent_values)//2:])
                
                change = second_half - first_half
                if abs(change) < 2:
                    pair_data.trend_direction = "stable"
                    pair_data.trend_strength = 0
                elif change > 0:
                    pair_data.trend_direction = "up"
                    pair_data.trend_strength = min(abs(change) * 5, 100)
                else:
                    pair_data.trend_direction = "down"
                    pair_data.trend_strength = min(abs(change) * 5, 100)
    
    def _create_snapshot(self) -> HeatMapSnapshot:
        """Create current heat map snapshot"""
        hot_pairs = []
        cold_pairs = []
        trending_up = []
        trending_down = []
        
        for pair, data in self.pair_cache.items():
            if data.heat_level in [HeatLevel.HOT, HeatLevel.BLAZING]:
                hot_pairs.append(pair)
            elif data.heat_level in [HeatLevel.FROZEN, HeatLevel.COLD]:
                cold_pairs.append(pair)
            
            if data.trend_direction == "up" and data.trend_strength > 20:
                trending_up.append(pair)
            elif data.trend_direction == "down" and data.trend_strength > 20:
                trending_down.append(pair)
        
        # Determine market sentiment
        avg_tcs = statistics.mean([d.current_tcs for d in self.pair_cache.values()]) if self.pair_cache else 70
        if avg_tcs > 75:
            sentiment = "bullish"
        elif avg_tcs < 65:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        return HeatMapSnapshot(
            timestamp=datetime.now(),
            total_pairs=len(self.pair_cache),
            hot_pairs=hot_pairs,
            cold_pairs=cold_pairs,
            trending_up=trending_up,
            trending_down=trending_down,
            pair_data=self.pair_cache.copy(),
            market_sentiment=sentiment
        )
    
    def _format_pairs_for_display(self, snapshot: HeatMapSnapshot) -> List[Dict[str, Any]]:
        """Format pairs for display"""
        formatted = []
        
        for pair, data in snapshot.pair_data.items():
            formatted.append({
                "pair": pair,
                "tcs": round(data.current_tcs, 1),
                "heat_level": data.heat_level.value,
                "color": self.HEAT_COLORS[data.heat_level],
                "trend": f"{data.trend_direction} ({data.trend_strength:.0f}%)",
                "sparkline": self._generate_mini_sparkline(data)
            })
        
        # Sort by TCS descending
        formatted.sort(key=lambda x: x["tcs"], reverse=True)
        
        return formatted
    
    def _create_visual_grid(self, snapshot: HeatMapSnapshot) -> List[List[Dict[str, Any]]]:
        """Create visual grid layout for heat map"""
        grid = []
        pairs_list = list(snapshot.pair_data.values())
        
        # Sort by TCS for better visual
        pairs_list.sort(key=lambda x: x.current_tcs, reverse=True)
        
        # Create 3x4 grid
        for i in range(0, len(pairs_list), 4):
            row = []
            for j in range(4):
                if i + j < len(pairs_list):
                    pair_data = pairs_list[i + j]
                    row.append({
                        "pair": pair_data.pair,
                        "tcs": round(pair_data.current_tcs, 1),
                        "color": self.HEAT_COLORS[pair_data.heat_level],
                        "intensity": pair_data.current_tcs / 100,
                        "trend_icon": self._get_trend_icon(pair_data)
                    })
                else:
                    row.append(None)
            grid.append(row)
        
        return grid
    
    def _generate_insights(self, snapshot: HeatMapSnapshot) -> List[str]:
        """Generate actionable insights"""
        insights = []
        
        # Market sentiment insight
        if snapshot.market_sentiment == "bullish":
            insights.append("🔥 Market showing strong confidence - multiple pairs heating up!")
        elif snapshot.market_sentiment == "bearish":
            insights.append("❄️ Market cooling down - consider waiting for better setups")
        
        # Hot pairs insight
        if snapshot.hot_pairs:
            top_pairs = snapshot.hot_pairs[:3]
            insights.append(f"🎯 Focus on: {', '.join(top_pairs)} - showing strongest signals")
        
        # Trend insights
        if len(snapshot.trending_up) >= 3:
            insights.append(f"📈 {len(snapshot.trending_up)} pairs trending up - momentum building!")
        
        if len(snapshot.trending_down) >= 3:
            insights.append(f"📉 {len(snapshot.trending_down)} pairs cooling - be selective")
        
        # Time-based insight
        hour = datetime.now().hour
        if 6 <= hour <= 10:
            insights.append("⏰ Prime London session - expect increased volatility")
        elif 13 <= hour <= 17:
            insights.append("⏰ NY session overlap - high opportunity window")
        
        return insights
    
    def _get_teaser_heat_map(self) -> Dict[str, Any]:
        """Get teaser version for non-subscribers"""
        return {
            "locked": True,
            "message": "Unlock Heat Map with 1000 XP!",
            "preview": {
                "description": "See which pairs are HOT right now!",
                "sample_data": {
                    "EURUSD": {"status": "???", "trend": "???"},
                    "GBPUSD": {"status": "???", "trend": "???"},
                    "USDJPY": {"status": "???", "trend": "???"}
                },
                "benefits": [
                    "Real-time TCS heat levels",
                    "Trend direction & strength",
                    "7-day performance history",
                    "Actionable market insights"
                ]
            }
        }
    
    def _generate_sparkline(self, pair_data: PairHeatData) -> List[int]:
        """Generate sparkline data for pair"""
        if not pair_data.historical_data:
            return []
        
        # Get last 24 hours of data
        cutoff = datetime.now() - timedelta(hours=24)
        recent_data = [(ts, val) for ts, val in pair_data.historical_data if ts > cutoff]
        
        if not recent_data:
            return []
        
        # Normalize to 0-100 scale
        values = [val for _, val in recent_data]
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val > min_val else 1
        
        normalized = [int((val - min_val) / range_val * 100) for val in values]
        
        # Sample to max 20 points
        if len(normalized) > 20:
            step = len(normalized) // 20
            normalized = normalized[::step]
        
        return normalized
    
    def _generate_mini_sparkline(self, pair_data: PairHeatData) -> str:
        """Generate mini ASCII sparkline"""
        sparkline_data = self._generate_sparkline(pair_data)
        if not sparkline_data:
            return "—"
        
        # Use Unicode block characters for mini chart
        blocks = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        
        result = ""
        for value in sparkline_data[-8:]:  # Last 8 points
            idx = int(value / 100 * (len(blocks) - 1))
            result += blocks[idx]
        
        return result
    
    def _describe_trend(self, pair_data: PairHeatData) -> str:
        """Describe trend in human terms"""
        if pair_data.trend_direction == "stable":
            return "Holding steady"
        elif pair_data.trend_direction == "up":
            if pair_data.trend_strength > 50:
                return "Strongly rising! 🚀"
            else:
                return "Gradually improving"
        else:
            if pair_data.trend_strength > 50:
                return "Sharply falling! ⚠️"
            else:
                return "Slowly declining"
    
    def _get_trend_icon(self, pair_data: PairHeatData) -> str:
        """Get trend icon"""
        if pair_data.trend_direction == "up":
            return "↗️" if pair_data.trend_strength > 30 else "→"
        elif pair_data.trend_direction == "down":
            return "↘️" if pair_data.trend_strength > 30 else "→"
        else:
            return "→"
    
    def _get_pair_recommendation(self, pair_data: PairHeatData) -> str:
        """Get trading recommendation for pair"""
        if pair_data.heat_level == HeatLevel.BLAZING:
            return "🔥 PRIME OPPORTUNITY - Take position on next signal!"
        elif pair_data.heat_level == HeatLevel.HOT:
            return "✅ Good setup potential - Stay alert"
        elif pair_data.heat_level == HeatLevel.WARM:
            return "👀 Monitor closely - May heat up soon"
        elif pair_data.heat_level == HeatLevel.NEUTRAL:
            return "⏸️ Wait for better conditions"
        else:
            return "❄️ Avoid - Look for warmer pairs"
    
    def _save_pair_data(self, pair: str) -> None:
        """Save pair data to file"""
        if pair not in self.pair_cache:
            return
        
        pair_file = self.data_dir / f"{pair}_heat.json"
        pair_data = self.pair_cache[pair]
        
        # Convert to serializable format
        data = {
            "pair": pair_data.pair,
            "current_tcs": pair_data.current_tcs,
            "average_tcs_24h": pair_data.average_tcs_24h,
            "average_tcs_7d": pair_data.average_tcs_7d,
            "trend_direction": pair_data.trend_direction,
            "trend_strength": pair_data.trend_strength,
            "heat_level": pair_data.heat_level.value,
            "signal_count_24h": pair_data.signal_count_24h,
            "win_rate_24h": pair_data.win_rate_24h,
            "last_updated": pair_data.last_updated.isoformat(),
            "historical_data": [
                {"timestamp": ts.isoformat(), "tcs": val}
                for ts, val in pair_data.historical_data[-100:]  # Keep last 100 points
            ]
        }
        
        with open(pair_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_historical_data(self) -> None:
        """Load historical data from files"""
        for pair_file in self.data_dir.glob("*_heat.json"):
            try:
                with open(pair_file, 'r') as f:
                    data = json.load(f)
                
                # Reconstruct PairHeatData
                historical = [
                    (datetime.fromisoformat(item["timestamp"]), item["tcs"])
                    for item in data.get("historical_data", [])
                ]
                
                pair_data = PairHeatData(
                    pair=data["pair"],
                    current_tcs=data["current_tcs"],
                    average_tcs_24h=data["average_tcs_24h"],
                    average_tcs_7d=data["average_tcs_7d"],
                    trend_direction=data["trend_direction"],
                    trend_strength=data["trend_strength"],
                    heat_level=HeatLevel(data["heat_level"]),
                    signal_count_24h=data["signal_count_24h"],
                    win_rate_24h=data["win_rate_24h"],
                    last_updated=datetime.fromisoformat(data["last_updated"]),
                    historical_data=historical
                )
                
                self.pair_cache[data["pair"]] = pair_data
                
            except Exception as e:
                logger.error(f"Error loading heat data from {pair_file}: {e}")

# Example usage
if __name__ == "__main__":
    analytics = HeatMapAnalytics()
    
    # Simulate some TCS updates
    analytics.update_pair_tcs("EURUSD", 82.5)
    analytics.update_pair_tcs("GBPUSD", 91.2)
    analytics.update_pair_tcs("USDJPY", 68.4)
    analytics.update_pair_tcs("USDCAD", 95.8)
    
    # Get heat map
    heat_map = analytics.get_heat_map(user_has_access=True)
    
    print(f"Market Sentiment: {heat_map['market_sentiment']}")
    print(f"Hot Pairs: {heat_map['summary']['hot_count']}")
    print("\nTop Pairs:")
    for pair in heat_map['pairs'][:5]:
        print(f"  {pair['pair']}: {pair['tcs']}% ({pair['heat_level']}) {pair['trend']}")
    
    print("\nInsights:")
    for insight in heat_map['insights']:
        print(f"  {insight}")