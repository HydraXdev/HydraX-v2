"""
Squad Radar for BITTEN
See what your top squad members are trading with privacy controls
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class PrivacyLevel(Enum):
    """Privacy settings for squad members"""
    PUBLIC = "public"          # Full visibility
    SQUAD_ONLY = "squad_only"  # Only squad can see
    ANONYMOUS = "anonymous"    # Hide identity, show trades
    PRIVATE = "private"        # Completely hidden


class TradeVisibility(Enum):
    """What parts of trade are visible"""
    FULL = "full"              # All details
    PARTIAL = "partial"        # Pair and direction only
    RESULTS_ONLY = "results"   # Win/loss only
    HIDDEN = "hidden"          # Not visible


@dataclass
class SquadMemberProfile:
    """Squad member profile with privacy settings"""
    user_id: str
    username: str
    rank: str
    privacy_level: PrivacyLevel = PrivacyLevel.SQUAD_ONLY
    trade_visibility: TradeVisibility = TradeVisibility.PARTIAL
    allow_copy_trading: bool = False
    anonymous_id: Optional[str] = None  # For anonymous members
    last_active: Optional[datetime] = None
    trust_score: float = 0.0  # 0-100, based on performance


@dataclass
class SquadTrade:
    """Active or recent trade from squad member"""
    trade_id: str
    member_id: str
    member_display: str  # Username or "Anonymous Trader"
    pair: str
    direction: str
    entry_time: datetime
    entry_price: Optional[float] = None
    current_status: str  # "active", "won", "lost"
    profit_pips: Optional[float] = None
    confidence_level: Optional[float] = None  # TCS if shared
    is_following_signal: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SquadRadarData:
    """Squad radar snapshot"""
    timestamp: datetime
    viewing_user_id: str
    total_squad_size: int
    active_traders: int
    visible_trades: List[SquadTrade]
    squad_performance: Dict[str, Any]
    trending_pairs: List[Tuple[str, int]]  # (pair, count)
    squad_sentiment: str  # "bullish", "bearish", "mixed"


class SquadRadar:
    """Manages squad visibility and trade sharing"""
    
    def __init__(self, data_dir: str = "data/squad_radar"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Member profiles
        self.member_profiles: Dict[str, SquadMemberProfile] = {}
        
        # Active trades
        self.active_trades: Dict[str, List[SquadTrade]] = {}
        
        # Squad relationships (who recruited who)
        self.squad_trees: Dict[str, Set[str]] = {}
        
        # Privacy preferences
        self.privacy_settings: Dict[str, Dict[str, Any]] = {}
        
        # Load data
        self._load_squad_data()
    
    def get_radar_view(
        self,
        user_id: str,
        has_radar_access: bool = True
    ) -> Dict[str, Any]:
        """Get squad radar view for a user"""
        if not has_radar_access:
            return self._get_teaser_view()
        
        # Get user's squad members
        squad_members = self._get_squad_members(user_id)
        
        # Get visible trades
        visible_trades = self._get_visible_trades(user_id, squad_members)
        
        # Sort by relevance
        top_trades = self._rank_trades_by_relevance(visible_trades, user_id)[:3]
        
        # Create radar snapshot
        snapshot = SquadRadarData(
            timestamp=datetime.now(),
            viewing_user_id=user_id,
            total_squad_size=len(squad_members),
            active_traders=len(set(t.member_id for t in visible_trades)),
            visible_trades=top_trades,
            squad_performance=self._calculate_squad_performance(squad_members),
            trending_pairs=self._get_trending_pairs(visible_trades),
            squad_sentiment=self._analyze_squad_sentiment(visible_trades)
        )
        
        # Format for display
        return self._format_radar_display(snapshot)
    
    def update_member_privacy(
        self,
        user_id: str,
        privacy_level: PrivacyLevel,
        trade_visibility: TradeVisibility,
        allow_copy_trading: bool = False
    ) -> bool:
        """Update member's privacy settings"""
        if user_id not in self.member_profiles:
            self.member_profiles[user_id] = SquadMemberProfile(
                user_id=user_id,
                username=f"Trader_{user_id[:6]}",
                rank="RECRUIT"
            )
        
        profile = self.member_profiles[user_id]
        profile.privacy_level = privacy_level
        profile.trade_visibility = trade_visibility
        profile.allow_copy_trading = allow_copy_trading
        
        # Generate anonymous ID if needed
        if privacy_level == PrivacyLevel.ANONYMOUS and not profile.anonymous_id:
            profile.anonymous_id = self._generate_anonymous_id(user_id)
        
        # Save settings
        self._save_privacy_settings(user_id)
        
        logger.info(f"Updated privacy settings for {user_id}: {privacy_level.value}")
        return True
    
    def register_trade(
        self,
        user_id: str,
        trade_data: Dict[str, Any]
    ) -> None:
        """Register a new trade for squad visibility"""
        # Check if user allows sharing
        profile = self.member_profiles.get(user_id)
        if not profile or profile.privacy_level == PrivacyLevel.PRIVATE:
            return
        
        # Create trade record
        trade = SquadTrade(
            trade_id=trade_data["trade_id"],
            member_id=user_id,
            member_display=self._get_display_name(user_id),
            pair=trade_data["pair"],
            direction=trade_data["direction"],
            entry_time=datetime.now(),
            entry_price=trade_data.get("entry_price") if profile.trade_visibility == TradeVisibility.FULL else None,
            current_status="active",
            confidence_level=trade_data.get("tcs") if profile.allow_copy_trading else None,
            is_following_signal=trade_data.get("is_signal", True)
        )
        
        # Add to active trades
        if user_id not in self.active_trades:
            self.active_trades[user_id] = []
        
        self.active_trades[user_id].append(trade)
        
        # Keep only recent trades (last 24h)
        self._cleanup_old_trades()
    
    def update_trade_result(
        self,
        user_id: str,
        trade_id: str,
        result: str,
        profit_pips: Optional[float] = None
    ) -> None:
        """Update trade result"""
        if user_id not in self.active_trades:
            return
        
        for trade in self.active_trades[user_id]:
            if trade.trade_id == trade_id:
                trade.current_status = result
                if profit_pips and self._can_show_profit(user_id):
                    trade.profit_pips = profit_pips
                break
    
    def _get_squad_members(self, user_id: str) -> Set[str]:
        """Get all squad members for a user"""
        members = set()
        
        # Direct recruits
        if user_id in self.squad_trees:
            members.update(self.squad_trees[user_id])
        
        # Add recruiter (upline)
        for recruiter, recruits in self.squad_trees.items():
            if user_id in recruits:
                members.add(recruiter)
                # Add squad siblings
                members.update(recruits)
        
        return members
    
    def _get_visible_trades(self, viewer_id: str, squad_members: Set[str]) -> List[SquadTrade]:
        """Get trades visible to viewer"""
        visible_trades = []
        
        for member_id in squad_members:
            if member_id not in self.active_trades:
                continue
            
            profile = self.member_profiles.get(member_id)
            if not profile:
                continue
            
            # Check privacy settings
            if profile.privacy_level == PrivacyLevel.PRIVATE:
                continue
            
            if profile.privacy_level == PrivacyLevel.SQUAD_ONLY and viewer_id not in squad_members:
                continue
            
            # Add visible trades
            for trade in self.active_trades[member_id]:
                if self._is_trade_visible(trade, profile, viewer_id):
                    visible_trades.append(trade)
        
        return visible_trades
    
    def _is_trade_visible(
        self,
        trade: SquadTrade,
        profile: SquadMemberProfile,
        viewer_id: str
    ) -> bool:
        """Check if trade is visible to viewer"""
        # Always hide if trade visibility is hidden
        if profile.trade_visibility == TradeVisibility.HIDDEN:
            return False
        
        # Check if still active or recent (last 4 hours)
        if trade.current_status == "active":
            return True
        
        time_since = datetime.now() - trade.entry_time
        return time_since < timedelta(hours=4)
    
    def _rank_trades_by_relevance(
        self,
        trades: List[SquadTrade],
        user_id: str
    ) -> List[SquadTrade]:
        """Rank trades by relevance to user"""
        # Score each trade
        scored_trades = []
        
        for trade in trades:
            score = 0
            
            # Active trades score higher
            if trade.current_status == "active":
                score += 50
            
            # Winning trades score higher
            if trade.current_status == "won":
                score += 30
            
            # Recent trades score higher
            time_since = (datetime.now() - trade.entry_time).total_seconds() / 3600
            score += max(0, 20 - time_since * 2)
            
            # High confidence trades score higher
            if trade.confidence_level:
                score += trade.confidence_level / 10
            
            # Trusted members score higher
            member_profile = self.member_profiles.get(trade.member_id)
            if member_profile:
                score += member_profile.trust_score / 10
            
            scored_trades.append((score, trade))
        
        # Sort by score descending
        scored_trades.sort(key=lambda x: x[0], reverse=True)
        
        return [trade for _, trade in scored_trades]
    
    def _calculate_squad_performance(self, squad_members: Set[str]) -> Dict[str, Any]:
        """Calculate overall squad performance"""
        total_trades = 0
        winning_trades = 0
        total_pips = 0.0
        
        for member_id in squad_members:
            if member_id not in self.active_trades:
                continue
            
            for trade in self.active_trades[member_id]:
                if trade.current_status in ["won", "lost"]:
                    total_trades += 1
                    if trade.current_status == "won":
                        winning_trades += 1
                    if trade.profit_pips:
                        total_pips += trade.profit_pips
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 1),
            "total_pips": round(total_pips, 1),
            "active_traders": len([m for m in squad_members if m in self.active_trades])
        }
    
    def _get_trending_pairs(self, trades: List[SquadTrade]) -> List[Tuple[str, int]]:
        """Get trending pairs in squad"""
        pair_counts = {}
        
        for trade in trades:
            if trade.current_status == "active":
                pair_counts[trade.pair] = pair_counts.get(trade.pair, 0) + 1
        
        # Sort by count
        trending = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)
        
        return trending[:5]  # Top 5
    
    def _analyze_squad_sentiment(self, trades: List[SquadTrade]) -> str:
        """Analyze overall squad sentiment"""
        if not trades:
            return "neutral"
        
        buy_count = sum(1 for t in trades if t.direction.lower() == "buy" and t.current_status == "active")
        sell_count = sum(1 for t in trades if t.direction.lower() == "sell" and t.current_status == "active")
        
        total = buy_count + sell_count
        if total == 0:
            return "neutral"
        
        buy_ratio = buy_count / total
        
        if buy_ratio > 0.65:
            return "bullish"
        elif buy_ratio < 0.35:
            return "bearish"
        else:
            return "mixed"
    
    def _format_radar_display(self, snapshot: SquadRadarData) -> Dict[str, Any]:
        """Format radar data for display"""
        display_trades = []
        
        for trade in snapshot.visible_trades:
            display_trade = {
                "member": trade.member_display,
                "pair": trade.pair,
                "direction": trade.direction.upper(),
                "status": self._format_status(trade.current_status),
                "time_ago": self._format_time_ago(trade.entry_time)
            }
            
            # Add optional fields based on visibility
            if trade.profit_pips is not None:
                display_trade["profit"] = f"{trade.profit_pips:+.1f} pips"
            
            if trade.confidence_level is not None:
                display_trade["confidence"] = f"{trade.confidence_level:.0f}%"
            
            display_trades.append(display_trade)
        
        # Format trending pairs
        trending_display = []
        for pair, count in snapshot.trending_pairs:
            trending_display.append({
                "pair": pair,
                "traders": count,
                "heat": "🔥" * min(count, 3)
            })
        
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "squad_size": snapshot.total_squad_size,
            "active_traders": snapshot.active_traders,
            "trades": display_trades,
            "performance": {
                "win_rate": f"{snapshot.squad_performance['win_rate']:.1f}%",
                "total_pips": f"{snapshot.squad_performance['total_pips']:+.1f}",
                "sentiment": self._format_sentiment(snapshot.squad_sentiment)
            },
            "trending": trending_display,
            "insights": self._generate_insights(snapshot)
        }
    
    def _get_teaser_view(self) -> Dict[str, Any]:
        """Get teaser view for non-subscribers"""
        return {
            "locked": True,
            "message": "Unlock Squad Radar with 500 XP!",
            "preview": {
                "description": "See what your top squad members are trading!",
                "sample_display": {
                    "trades": [
                        {"member": "???", "pair": "???", "status": "🔥 Active"},
                        {"member": "???", "pair": "???", "status": "✅ Won"},
                        {"member": "???", "pair": "???", "status": "🔥 Active"}
                    ]
                },
                "benefits": [
                    "See top 3 squad trades in real-time",
                    "Track squad performance metrics",
                    "Identify trending pairs in your network",
                    "Optional: Share your trades with squad"
                ]
            }
        }
    
    def _get_display_name(self, user_id: str) -> str:
        """Get display name based on privacy settings"""
        profile = self.member_profiles.get(user_id)
        
        if not profile:
            return "Unknown Trader"
        
        if profile.privacy_level == PrivacyLevel.ANONYMOUS:
            return f"Trader_{profile.anonymous_id[:8]}"
        
        return profile.username
    
    def _can_show_profit(self, user_id: str) -> bool:
        """Check if profit can be shown"""
        profile = self.member_profiles.get(user_id)
        if not profile:
            return False
        
        return profile.trade_visibility in [TradeVisibility.FULL, TradeVisibility.PARTIAL]
    
    def _generate_anonymous_id(self, user_id: str) -> str:
        """Generate anonymous ID for user"""
        return hashlib.sha256(f"{user_id}_anonymous".encode()).hexdigest()
    
    def _format_status(self, status: str) -> str:
        """Format trade status for display"""
        status_map = {
            "active": "🔥 Active",
            "won": "✅ Won",
            "lost": "❌ Lost"
        }
        return status_map.get(status, status)
    
    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format time ago string"""
        delta = datetime.now() - timestamp
        
        if delta.total_seconds() < 60:
            return "just now"
        elif delta.total_seconds() < 3600:
            minutes = int(delta.total_seconds() / 60)
            return f"{minutes}m ago"
        elif delta.total_seconds() < 86400:
            hours = int(delta.total_seconds() / 3600)
            return f"{hours}h ago"
        else:
            days = int(delta.total_seconds() / 86400)
            return f"{days}d ago"
    
    def _format_sentiment(self, sentiment: str) -> str:
        """Format sentiment with emoji"""
        sentiment_map = {
            "bullish": "📈 Bullish",
            "bearish": "📉 Bearish",
            "mixed": "🔄 Mixed",
            "neutral": "➡️ Neutral"
        }
        return sentiment_map.get(sentiment, sentiment)
    
    def _generate_insights(self, snapshot: SquadRadarData) -> List[str]:
        """Generate squad insights"""
        insights = []
        
        # Activity insight
        if snapshot.active_traders >= 3:
            insights.append(f"🔥 {snapshot.active_traders} squad members actively trading!")
        
        # Performance insight
        win_rate = snapshot.squad_performance["win_rate"]
        if win_rate > 70:
            insights.append(f"💪 Squad crushing it with {win_rate}% win rate!")
        elif win_rate < 40:
            insights.append(f"⚠️ Squad struggling - share strategies!")
        
        # Trending insight
        if snapshot.trending_pairs:
            top_pair = snapshot.trending_pairs[0]
            insights.append(f"🎯 {top_pair[0]} is hot - {top_pair[1]} traders on it!")
        
        # Sentiment insight
        if snapshot.squad_sentiment == "bullish":
            insights.append("📈 Squad sentiment: Strongly bullish")
        elif snapshot.squad_sentiment == "bearish":
            insights.append("📉 Squad sentiment: Bearish - be cautious")
        
        return insights
    
    def _cleanup_old_trades(self) -> None:
        """Remove old trades from memory"""
        cutoff = datetime.now() - timedelta(hours=24)
        
        for user_id in list(self.active_trades.keys()):
            # Keep only recent trades
            self.active_trades[user_id] = [
                trade for trade in self.active_trades[user_id]
                if trade.entry_time > cutoff or trade.current_status == "active"
            ]
            
            # Remove empty lists
            if not self.active_trades[user_id]:
                del self.active_trades[user_id]
    
    def _save_privacy_settings(self, user_id: str) -> None:
        """Save user privacy settings"""
        settings_file = self.data_dir / f"privacy_{user_id}.json"
        profile = self.member_profiles.get(user_id)
        
        if not profile:
            return
        
        data = {
            "user_id": user_id,
            "privacy_level": profile.privacy_level.value,
            "trade_visibility": profile.trade_visibility.value,
            "allow_copy_trading": profile.allow_copy_trading,
            "anonymous_id": profile.anonymous_id
        }
        
        with open(settings_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_squad_data(self) -> None:
        """Load squad data from files"""
        # Load privacy settings
        for settings_file in self.data_dir.glob("privacy_*.json"):
            try:
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                
                user_id = data["user_id"]
                self.member_profiles[user_id] = SquadMemberProfile(
                    user_id=user_id,
                    username=f"Trader_{user_id[:6]}",
                    rank="RECRUIT",
                    privacy_level=PrivacyLevel(data["privacy_level"]),
                    trade_visibility=TradeVisibility(data["trade_visibility"]),
                    allow_copy_trading=data["allow_copy_trading"],
                    anonymous_id=data.get("anonymous_id")
                )
                
            except Exception as e:
                logger.error(f"Error loading privacy settings: {e}")


# Example usage
if __name__ == "__main__":
    radar = SquadRadar()
    
    # Set up some test members
    radar.squad_trees["commander"] = {"member1", "member2", "member3"}
    
    # Register some trades
    radar.register_trade("member1", {
        "trade_id": "T001",
        "pair": "EURUSD",
        "direction": "buy",
        "entry_price": 1.0850,
        "tcs": 85.5
    })
    
    radar.register_trade("member2", {
        "trade_id": "T002",
        "pair": "GBPUSD",
        "direction": "sell",
        "entry_price": 1.2650,
        "tcs": 92.0
    })
    
    # Get radar view
    view = radar.get_radar_view("commander", has_radar_access=True)
    
    print("Squad Radar View:")
    print(f"Active Traders: {view['active_traders']}/{view['squad_size']}")
    print("\nVisible Trades:")
    for trade in view['trades']:
        print(f"  {trade['member']}: {trade['pair']} {trade['direction']} - {trade['status']}")
    
    print(f"\nSquad Performance: {view['performance']['win_rate']} win rate")
    print("\nInsights:")
    for insight in view['insights']:
        print(f"  {insight}")