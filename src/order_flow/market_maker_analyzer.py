# market_maker_analyzer.py
# Market Maker Behavior Analysis - Track Professional Liquidity Providers

import numpy as np
from typing import List, Dict, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class MarketMakerProfile:
    """Profile of detected market maker"""
    maker_id: str
    first_seen: datetime
    last_seen: datetime
    dominant_strategy: str  # 'passive', 'aggressive', 'adaptive'
    avg_spread: float
    quote_frequency: float  # Quotes per minute
    two_sided_percentage: float
    inventory_style: str  # 'balanced', 'directional', 'opportunistic'
    typical_quote_size: float
    participation_hours: List[int]  # Active hours

@dataclass
class MarketMakerAction:
    """Individual market maker action"""
    timestamp: datetime
    maker_id: str
    action_type: str  # 'quote', 'improve', 'fade', 'cross'
    side: str
    price: float
    size: float
    spread_context: float  # Spread at time of action
    inventory_pressure: float  # Estimated inventory imbalance

class MarketMakerAnalyzer:
    """
    MARKET MAKER BEHAVIOR ANALYSIS ENGINE
    
    Tracks and analyzes professional market maker patterns:
    - Spread provision strategies
    - Inventory management
    - Quote adjustment patterns
    - Competition dynamics
    - Liquidity provision quality
    """
    
    def __init__(self, symbol: str, tick_size: float = 0.0001):
        self.symbol = symbol
        self.tick_size = tick_size
        
        # Maker identification parameters
        self.min_quote_frequency = 10  # Quotes per minute
        self.min_two_sided_ratio = 0.6  # 60% two-sided quotes
        self.maker_id_counter = 0
        
        # Behavior tracking
        self.maker_profiles = {}  # maker_id -> MarketMakerProfile
        self.maker_actions = defaultdict(deque)  # maker_id -> deque of actions
        self.quote_patterns = defaultdict(lambda: defaultdict(list))
        
        # Market state
        self.current_spread = 2.0  # Default 2 pip spread
        self.market_volatility = 'normal'
        self.competition_level = 'moderate'
        
        # Statistical tracking
        self.spread_history = deque(maxlen=1000)
        self.maker_competition_events = deque(maxlen=100)
        
    def analyze_quote_update(self, timestamp: datetime, 
                           bid_price: float, bid_size: float,
                           ask_price: float, ask_size: float,
                           quote_id: Optional[str] = None) -> Optional[MarketMakerAction]:
        """
        Analyze quote update for market maker behavior
        
        Args:
            timestamp: Quote timestamp
            bid_price: Best bid price
            bid_size: Best bid size
            ask_price: Best ask price
            ask_size: Best ask size
            quote_id: Optional identifier for quote source
            
        Returns:
            MarketMakerAction if significant MM behavior detected
        """
        
        # Update market state
        self.current_spread = (ask_price - bid_price) / self.tick_size
        self.spread_history.append((timestamp, self.current_spread))
        
        # Identify market maker
        maker_id = self._identify_market_maker(
            timestamp, bid_price, bid_size, ask_price, ask_size, quote_id
        )
        
        if not maker_id:
            return None
        
        # Analyze action type
        action = self._analyze_maker_action(
            maker_id, timestamp, bid_price, bid_size, ask_price, ask_size
        )
        
        if action:
            # Update maker profile
            self._update_maker_profile(maker_id, action)
            
            # Store action
            self.maker_actions[maker_id].append(action)
            
            # Check for competition events
            self._check_maker_competition(action)
            
            logger.info(f"Market maker action: {action}")
            
        return action
    
    def _identify_market_maker(self, timestamp: datetime,
                             bid_price: float, bid_size: float,
                             ask_price: float, ask_size: float,
                             quote_id: Optional[str]) -> Optional[str]:
        """Identify market maker from quote characteristics"""
        
        # Use provided ID if available
        if quote_id:
            return f"MM_{quote_id}"
        
        # Otherwise, use pattern recognition
        # Look for consistent quote patterns
        quote_signature = self._calculate_quote_signature(
            bid_price, bid_size, ask_price, ask_size
        )
        
        # Match against known makers
        for maker_id, profile in self.maker_profiles.items():
            if self._matches_maker_pattern(maker_id, quote_signature, timestamp):
                return maker_id
        
        # Check if this could be a new market maker
        if self._is_market_maker_behavior(bid_price, bid_size, ask_price, ask_size):
            # Create new maker profile
            new_maker_id = f"MM_{self.maker_id_counter}"
            self.maker_id_counter += 1
            
            self.maker_profiles[new_maker_id] = MarketMakerProfile(
                maker_id=new_maker_id,
                first_seen=timestamp,
                last_seen=timestamp,
                dominant_strategy='unknown',
                avg_spread=self.current_spread,
                quote_frequency=0,
                two_sided_percentage=1.0,  # Started with two-sided
                inventory_style='unknown',
                typical_quote_size=(bid_size + ask_size) / 2,
                participation_hours=[]
            )
            
            return new_maker_id
        
        return None
    
    def _calculate_quote_signature(self, bid_price: float, bid_size: float,
                                 ask_price: float, ask_size: float) -> Dict[str, Any]:
        """Calculate quote signature for pattern matching"""
        
        spread = (ask_price - bid_price) / self.tick_size
        size_ratio = bid_size / ask_size if ask_size > 0 else 0
        total_size = bid_size + ask_size
        
        # Round sizes to identify common patterns
        bid_size_rounded = round(bid_size / 100) * 100
        ask_size_rounded = round(ask_size / 100) * 100
        
        return {
            'spread': spread,
            'size_ratio': size_ratio,
            'total_size': total_size,
            'bid_size_pattern': bid_size_rounded,
            'ask_size_pattern': ask_size_rounded,
            'is_symmetric': abs(size_ratio - 1.0) < 0.1
        }
    
    def _matches_maker_pattern(self, maker_id: str, signature: Dict[str, Any],
                             timestamp: datetime) -> bool:
        """Check if quote signature matches known maker pattern"""
        
        if maker_id not in self.quote_patterns:
            return False
        
        maker_patterns = self.quote_patterns[maker_id]
        
        # Check recent patterns
        recent_patterns = maker_patterns.get('recent', [])
        if not recent_patterns:
            return False
        
        # Compare with recent signatures
        for past_sig in recent_patterns[-5:]:
            spread_match = abs(signature['spread'] - past_sig['spread']) < 1
            size_match = abs(signature['total_size'] - past_sig['total_size']) / past_sig['total_size'] < 0.3
            
            if spread_match and size_match:
                return True
        
        return False
    
    def _is_market_maker_behavior(self, bid_price: float, bid_size: float,
                                ask_price: float, ask_size: float) -> bool:
        """Determine if quote exhibits market maker characteristics"""
        
        # Two-sided quote
        if bid_size == 0 or ask_size == 0:
            return False
        
        # Reasonable spread
        spread = (ask_price - bid_price) / self.tick_size
        if spread > 10 or spread < 0.5:  # Too wide or too tight
            return False
        
        # Meaningful size
        min_size = 1000  # Minimum professional size
        if bid_size < min_size and ask_size < min_size:
            return False
        
        # Size balance (not too skewed)
        size_ratio = min(bid_size, ask_size) / max(bid_size, ask_size)
        if size_ratio < 0.2:  # Too imbalanced
            return False
        
        return True
    
    def _analyze_maker_action(self, maker_id: str, timestamp: datetime,
                            bid_price: float, bid_size: float,
                            ask_price: float, ask_size: float) -> Optional[MarketMakerAction]:
        """Analyze market maker action type"""
        
        # Get maker's recent actions
        recent_actions = list(self.maker_actions[maker_id])[-10:] if maker_id in self.maker_actions else []
        
        # Determine action type
        action_type = 'quote'  # Default
        
        if recent_actions:
            last_action = recent_actions[-1]
            
            # Check for spread improvement
            last_spread = last_action.spread_context
            current_spread = (ask_price - bid_price) / self.tick_size
            
            if current_spread < last_spread:
                action_type = 'improve'
            elif current_spread > last_spread * 1.5:
                action_type = 'fade'
            
            # Check for crossing the spread
            if hasattr(last_action, 'price'):
                if (last_action.side == 'ask' and bid_price >= last_action.price) or \
                   (last_action.side == 'bid' and ask_price <= last_action.price):
                    action_type = 'cross'
        
        # Estimate inventory pressure
        inventory_pressure = self._estimate_inventory_pressure(
            maker_id, bid_size, ask_size
        )
        
        # Determine dominant side
        if bid_size > ask_size * 1.5:
            side = 'bid'
            price = bid_price
            size = bid_size
        elif ask_size > bid_size * 1.5:
            side = 'ask'
            price = ask_price
            size = ask_size
        else:
            side = 'both'
            price = (bid_price + ask_price) / 2
            size = (bid_size + ask_size) / 2
        
        return MarketMakerAction(
            timestamp=timestamp,
            maker_id=maker_id,
            action_type=action_type,
            side=side,
            price=price,
            size=size,
            spread_context=self.current_spread,
            inventory_pressure=inventory_pressure
        )
    
    def _estimate_inventory_pressure(self, maker_id: str, 
                                   bid_size: float, ask_size: float) -> float:
        """Estimate market maker's inventory pressure"""
        
        if maker_id not in self.maker_actions:
            return 0.0
        
        recent_actions = list(self.maker_actions[maker_id])[-20:]
        
        if not recent_actions:
            return 0.0
        
        # Calculate directional bias
        bid_volume = sum(a.size for a in recent_actions if a.side == 'bid')
        ask_volume = sum(a.size for a in recent_actions if a.side == 'ask')
        
        total_volume = bid_volume + ask_volume
        if total_volume == 0:
            return 0.0
        
        # Positive pressure = long inventory (wants to sell)
        # Negative pressure = short inventory (wants to buy)
        pressure = (ask_volume - bid_volume) / total_volume
        
        # Adjust for current quote skew
        current_skew = (ask_size - bid_size) / (ask_size + bid_size) if ask_size + bid_size > 0 else 0
        
        # Combine historical and current
        return pressure * 0.7 + current_skew * 0.3
    
    def _update_maker_profile(self, maker_id: str, action: MarketMakerAction):
        """Update market maker profile with new action"""
        
        if maker_id not in self.maker_profiles:
            return
        
        profile = self.maker_profiles[maker_id]
        
        # Update last seen
        profile.last_seen = action.timestamp
        
        # Update spread statistics
        if hasattr(self, 'spread_history') and self.spread_history:
            recent_spreads = [s[1] for s in list(self.spread_history)[-100:]]
            profile.avg_spread = np.mean(recent_spreads)
        
        # Update quote frequency
        if maker_id in self.maker_actions:
            actions = self.maker_actions[maker_id]
            if len(actions) > 1:
                time_span = (actions[-1].timestamp - actions[0].timestamp).total_seconds() / 60
                if time_span > 0:
                    profile.quote_frequency = len(actions) / time_span
        
        # Update strategy classification
        profile.dominant_strategy = self._classify_maker_strategy(maker_id)
        
        # Update inventory style
        profile.inventory_style = self._classify_inventory_style(maker_id)
        
        # Track participation hours
        current_hour = action.timestamp.hour
        if current_hour not in profile.participation_hours:
            profile.participation_hours.append(current_hour)
    
    def _classify_maker_strategy(self, maker_id: str) -> str:
        """Classify market maker's dominant strategy"""
        
        if maker_id not in self.maker_actions:
            return 'unknown'
        
        recent_actions = list(self.maker_actions[maker_id])[-50:]
        
        if not recent_actions:
            return 'unknown'
        
        # Count action types
        action_counts = defaultdict(int)
        for action in recent_actions:
            action_counts[action.action_type] += 1
        
        # Analyze spread behavior
        spreads = [a.spread_context for a in recent_actions]
        avg_spread = np.mean(spreads)
        spread_volatility = np.std(spreads)
        
        # Classify based on behavior
        if action_counts['improve'] > len(recent_actions) * 0.3:
            return 'aggressive'
        elif action_counts['fade'] > len(recent_actions) * 0.2:
            return 'defensive'
        elif spread_volatility > avg_spread * 0.3:
            return 'adaptive'
        else:
            return 'passive'
    
    def _classify_inventory_style(self, maker_id: str) -> str:
        """Classify market maker's inventory management style"""
        
        if maker_id not in self.maker_actions:
            return 'unknown'
        
        recent_actions = list(self.maker_actions[maker_id])[-100:]
        
        if len(recent_actions) < 20:
            return 'unknown'
        
        # Analyze inventory pressure patterns
        pressures = [a.inventory_pressure for a in recent_actions]
        avg_pressure = np.mean(pressures)
        pressure_volatility = np.std(pressures)
        
        # Check for directional bias
        if abs(avg_pressure) > 0.3:
            return 'directional'
        elif pressure_volatility > 0.4:
            return 'opportunistic'
        else:
            return 'balanced'
    
    def _check_maker_competition(self, action: MarketMakerAction):
        """Check for market maker competition events"""
        
        # Look for rapid spread improvements by different makers
        recent_window = timedelta(seconds=10)
        cutoff_time = action.timestamp - recent_window
        
        recent_improvements = []
        
        for maker_id, actions in self.maker_actions.items():
            maker_recent = [a for a in actions if a.timestamp >= cutoff_time 
                          and a.action_type == 'improve']
            recent_improvements.extend(maker_recent)
        
        if len(recent_improvements) >= 3:
            # Multiple makers improving spreads - competition event
            self.maker_competition_events.append({
                'timestamp': action.timestamp,
                'participant_count': len(set(a.maker_id for a in recent_improvements)),
                'spread_before': recent_improvements[0].spread_context,
                'spread_after': action.spread_context,
                'competition_type': 'spread_war'
            })
    
    def get_maker_rankings(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Get market maker rankings by various metrics"""
        
        rankings = []
        
        for maker_id, profile in self.maker_profiles.items():
            if maker_id not in self.maker_actions:
                continue
            
            actions = self.maker_actions[maker_id]
            if not actions:
                continue
            
            # Calculate metrics
            total_volume = sum(a.size for a in actions)
            avg_spread_provided = profile.avg_spread
            time_active = (profile.last_seen - profile.first_seen).total_seconds() / 3600  # Hours
            
            # Quality score
            quality_score = self._calculate_maker_quality_score(maker_id)
            
            rankings.append((maker_id, {
                'total_volume': total_volume,
                'avg_spread': avg_spread_provided,
                'quote_frequency': profile.quote_frequency,
                'hours_active': time_active,
                'strategy': profile.dominant_strategy,
                'quality_score': quality_score
            }))
        
        # Sort by quality score
        rankings.sort(key=lambda x: x[1]['quality_score'], reverse=True)
        
        return rankings
    
    def _calculate_maker_quality_score(self, maker_id: str) -> float:
        """Calculate quality score for market maker"""
        
        if maker_id not in self.maker_profiles or maker_id not in self.maker_actions:
            return 0.0
        
        profile = self.maker_profiles[maker_id]
        actions = self.maker_actions[maker_id]
        
        score = 0.0
        
        # Tighter spreads = higher quality
        if profile.avg_spread < 2.0:
            score += 30
        elif profile.avg_spread < 3.0:
            score += 20
        elif profile.avg_spread < 5.0:
            score += 10
        
        # Higher frequency = higher quality
        if profile.quote_frequency > 30:
            score += 20
        elif profile.quote_frequency > 15:
            score += 10
        
        # Two-sided quoting
        score += profile.two_sided_percentage * 20
        
        # Consistency (low spread volatility)
        if actions:
            spreads = [a.spread_context for a in list(actions)[-50:]]
            if len(spreads) > 10:
                spread_cv = np.std(spreads) / np.mean(spreads) if np.mean(spreads) > 0 else 1
                score += max(0, 20 - spread_cv * 20)
        
        # Participation during important hours
        important_hours = [8, 9, 10, 14, 15, 16]  # Market open/close
        important_participation = sum(1 for h in profile.participation_hours if h in important_hours)
        score += (important_participation / len(important_hours)) * 10 if important_hours else 0
        
        return min(100, score)
    
    def get_market_quality_metrics(self) -> Dict[str, Any]:
        """Get overall market quality metrics"""
        
        if not self.spread_history:
            return {
                'avg_spread': 0,
                'spread_volatility': 0,
                'maker_count': 0,
                'competition_level': 'low'
            }
        
        recent_spreads = [s[1] for s in list(self.spread_history)[-100:]]
        
        # Active makers
        active_makers = [m for m, p in self.maker_profiles.items()
                        if p.last_seen >= datetime.now() - timedelta(minutes=5)]
        
        # Competition level
        if len(active_makers) >= 5:
            competition = 'high'
        elif len(active_makers) >= 3:
            competition = 'moderate'
        else:
            competition = 'low'
        
        # Quote improvement frequency
        total_actions = sum(len(actions) for actions in self.maker_actions.values())
        improve_actions = sum(1 for actions in self.maker_actions.values()
                            for a in actions if a.action_type == 'improve')
        improvement_rate = improve_actions / total_actions if total_actions > 0 else 0
        
        return {
            'avg_spread': np.mean(recent_spreads),
            'spread_volatility': np.std(recent_spreads),
            'min_spread': np.min(recent_spreads),
            'max_spread': np.max(recent_spreads),
            'maker_count': len(active_makers),
            'competition_level': competition,
            'improvement_rate': improvement_rate,
            'recent_competition_events': len([e for e in self.maker_competition_events
                                            if e['timestamp'] >= datetime.now() - timedelta(minutes=30)])
        }
    
    def get_maker_impact_analysis(self, maker_id: str) -> Dict[str, Any]:
        """Analyze specific market maker's impact on market quality"""
        
        if maker_id not in self.maker_profiles or maker_id not in self.maker_actions:
            return {'error': 'Unknown market maker'}
        
        profile = self.maker_profiles[maker_id]
        actions = list(self.maker_actions[maker_id])
        
        if not actions:
            return {'error': 'No actions recorded'}
        
        # Time periods with and without this maker
        maker_timestamps = [a.timestamp for a in actions]
        
        # Spread impact
        spreads_with_maker = []
        spreads_without_maker = []
        
        for timestamp, spread in self.spread_history:
            # Check if maker was active
            maker_active = any(abs((timestamp - mt).total_seconds()) < 60 
                             for mt in maker_timestamps)
            
            if maker_active:
                spreads_with_maker.append(spread)
            else:
                spreads_without_maker.append(spread)
        
        # Calculate impact
        avg_spread_with = np.mean(spreads_with_maker) if spreads_with_maker else 0
        avg_spread_without = np.mean(spreads_without_maker) if spreads_without_maker else 0
        
        return {
            'maker_id': maker_id,
            'strategy': profile.dominant_strategy,
            'quality_score': self._calculate_maker_quality_score(maker_id),
            'avg_spread_provided': profile.avg_spread,
            'market_spread_with_maker': avg_spread_with,
            'market_spread_without_maker': avg_spread_without,
            'spread_improvement': avg_spread_without - avg_spread_with if avg_spread_without > 0 else 0,
            'total_quotes': len(actions),
            'improve_actions': sum(1 for a in actions if a.action_type == 'improve'),
            'fade_actions': sum(1 for a in actions if a.action_type == 'fade'),
            'inventory_style': profile.inventory_style
        }