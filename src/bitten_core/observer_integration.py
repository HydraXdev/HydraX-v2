"""
Observer Bot Integration Module
Integrates Elon Observer Bot with BITTEN system for random UI appearances and insights
"""

import asyncio
import random
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from .observer_elon_bot import (
    ObserverElonBot, 
    get_elon_market_comment,
    get_elon_trader_feedback,
    get_random_elon_appearance
)
from .intel_bot_personalities import BotPersonality, BotResponse

logger = logging.getLogger(__name__)

@dataclass
class ObserverEvent:
    """Structure for observer bot events"""
    event_type: str  # 'market_comment', 'trader_feedback', 'random_appearance'
    data: Dict
    timestamp: datetime
    priority: int = 5  # 1-10, higher = more important

class ObserverIntegration:
    """
    Manages integration of Observer bots (like Elon) into the trading system
    Handles scheduling, context awareness, and UI notifications
    """
    
    def __init__(self):
        self.elon_bot = ObserverElonBot()
        self.event_queue: List[ObserverEvent] = []
        self.event_callbacks: List[Callable] = []
        self.last_appearance = datetime.now()
        self.appearance_cooldown = timedelta(minutes=15)  # Minimum time between appearances
        self.market_state_cache = "neutral"
        self.is_active = True
        
        # Appearance weights based on context
        self.context_weights = {
            'market_open': 0.8,
            'market_close': 0.9,
            'high_volatility': 0.95,
            'big_trade': 0.85,
            'streak_achieved': 0.9,
            'loss_taken': 0.7,
            'new_high': 0.95,
            'idle_time': 0.3
        }
    
    def register_callback(self, callback: Callable):
        """Register callback for observer events"""
        self.event_callbacks.append(callback)
    
    async def start_monitoring(self):
        """Start the observer monitoring loop"""
        logger.info("Observer Integration started - Elon is watching...")
        
        while self.is_active:
            try:
                # Check for random appearances
                await self._check_random_appearance()
                
                # Process any queued events
                await self._process_event_queue()
                
                # Sleep for a bit
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Observer monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _check_random_appearance(self):
        """Check if conditions are right for a random appearance"""
        now = datetime.now()
        
        # Check cooldown
        if now - self.last_appearance < self.appearance_cooldown:
            return
        
        # Calculate appearance probability based on context
        probability = self._calculate_appearance_probability()
        
        if random.random() < probability:
            event = await self._generate_random_event()
            if event:
                await self._notify_observers(event)
                self.last_appearance = now
    
    def _calculate_appearance_probability(self) -> float:
        """Calculate probability of appearance based on current context"""
        base_probability = 0.1  # 10% base chance per check
        
        # Adjust based on time of day
        hour = datetime.now().hour
        if 9 <= hour <= 16:  # Market hours
            base_probability *= 1.5
        elif hour < 6 or hour > 22:  # Late night/early morning
            base_probability *= 0.3
        
        return min(base_probability, 0.5)  # Cap at 50%
    
    async def _generate_random_event(self) -> Optional[ObserverEvent]:
        """Generate a random observer event"""
        event_types = [
            ('market_comment', 0.4),
            ('random_appearance', 0.6)
        ]
        
        # Choose event type based on weights
        event_type = self._weighted_choice(event_types)
        
        if event_type == 'market_comment':
            data = get_elon_market_comment(self.market_state_cache)
        else:
            data = get_random_elon_appearance()
        
        return ObserverEvent(
            event_type=event_type,
            data=data,
            timestamp=datetime.now(),
            priority=5
        )
    
    def _weighted_choice(self, choices: List[tuple]) -> str:
        """Make a weighted random choice"""
        total = sum(weight for _, weight in choices)
        r = random.uniform(0, total)
        upto = 0
        for choice, weight in choices:
            if upto + weight >= r:
                return choice
            upto += weight
        return choices[-1][0]
    
    async def _notify_observers(self, event: ObserverEvent):
        """Notify all registered callbacks of an event"""
        for callback in self.event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in observer callback: {e}")
    
    async def _process_event_queue(self):
        """Process any queued events"""
        if not self.event_queue:
            return
        
        # Sort by priority and timestamp
        self.event_queue.sort(key=lambda x: (-x.priority, x.timestamp))
        
        # Process up to 3 events
        events_to_process = self.event_queue[:3]
        self.event_queue = self.event_queue[3:]
        
        for event in events_to_process:
            await self._notify_observers(event)
    
    # Context-aware triggers
    
    async def on_market_update(self, market_state: str):
        """Called when market state changes"""
        self.market_state_cache = market_state
        
        # Higher chance of comment during significant market changes
        if market_state in ['volatile', 'bullish', 'bearish']:
            if random.random() < 0.3:  # 30% chance
                event = ObserverEvent(
                    event_type='market_comment',
                    data=get_elon_market_comment(market_state),
                    timestamp=datetime.now(),
                    priority=7
                )
                self.event_queue.append(event)
    
    async def on_trade_completed(self, trade_data: Dict):
        """Called when a trade is completed"""
        # Comment on significant trades
        profit = trade_data.get('profit', 0)
        risk_reward = trade_data.get('risk_reward_ratio', 1)
        
        should_comment = False
        priority = 5
        
        if abs(profit) > 100:  # Significant P&L
            should_comment = random.random() < 0.4
            priority = 8
        elif risk_reward > 3:  # Great risk/reward
            should_comment = random.random() < 0.5
            priority = 7
        elif profit < -50:  # Notable loss
            should_comment = random.random() < 0.3
            priority = 6
        
        if should_comment:
            observation = self.elon_bot.comment_on_trade(trade_data)
            event = ObserverEvent(
                event_type='trade_comment',
                data={
                    'type': 'elon_trade_comment',
                    'message': observation.message,
                    'mood': observation.mood.value,
                    'quote': observation.quote,
                    'trade_data': trade_data,
                    'emoji': self.elon_bot.emoji
                },
                timestamp=datetime.now(),
                priority=priority
            )
            self.event_queue.append(event)
    
    async def on_trader_behavior(self, behavior_type: str, context: Dict = None):
        """Called when specific trader behavior is detected"""
        # Always comment on extreme behaviors
        if behavior_type in ['reckless', 'fomo']:
            if random.random() < 0.7:  # 70% chance
                event = ObserverEvent(
                    event_type='trader_feedback',
                    data=get_elon_trader_feedback(behavior_type, context),
                    timestamp=datetime.now(),
                    priority=8
                )
                await self._notify_observers(event)  # Immediate notification
        
        elif behavior_type == 'disciplined':
            if random.random() < 0.3:  # 30% chance for positive reinforcement
                event = ObserverEvent(
                    event_type='trader_feedback',
                    data=get_elon_trader_feedback(behavior_type, context),
                    timestamp=datetime.now(),
                    priority=6
                )
                self.event_queue.append(event)
    
    async def on_milestone_achieved(self, milestone_type: str, data: Dict):
        """Called when user achieves a milestone"""
        # High chance of commenting on achievements
        if random.random() < 0.8:
            message = self._get_milestone_message(milestone_type, data)
            event = ObserverEvent(
                event_type='milestone_comment',
                data={
                    'type': 'elon_milestone',
                    'message': message,
                    'mood': 'visionary',
                    'milestone': milestone_type,
                    'data': data,
                    'emoji': self.elon_bot.emoji
                },
                timestamp=datetime.now(),
                priority=9
            )
            await self._notify_observers(event)
    
    def _get_milestone_message(self, milestone_type: str, data: Dict) -> str:
        """Generate milestone-specific message"""
        messages = {
            'profit_milestone': [
                f"Profit milestone achieved! {data.get('amount', 0)}. Remember: sustainable growth beats one-time wins.",
                f"Nice gains! But can you replicate this consistently? That's the real challenge.",
                f"Milestone unlocked! You're learning the game. Keep pushing the boundaries."
            ],
            'streak_milestone': [
                f"{data.get('streak', 0)} day streak! Consistency is the meta-skill of trading.",
                f"Streak achievement! Daily habits compound like interest. You're getting it.",
                f"Impressive consistency! This is how trading empires are built."
            ],
            'xp_milestone': [
                f"XP milestone! Knowledge compounds faster than capital. Keep learning.",
                f"Level up! Every XP point is a lesson learned. You're becoming dangerous.",
                f"Experience gained! The market is the best teacher, and you're a good student."
            ]
        }
        
        category_messages = messages.get(milestone_type, [
            "Achievement unlocked! Keep pushing forward.",
            "Milestone reached! The journey continues.",
            "Progress detected! Onwards and upwards."
        ])
        
        return random.choice(category_messages)
    
    async def get_daily_insight(self) -> Dict:
        """Get daily trading insight from Elon"""
        insights = [
            {
                'message': "Today's market reminds me of rocket engineering. Multiple failure points, but huge upside if executed correctly.",
                'focus': "Risk management is your heat shield. Don't enter the atmosphere without it."
            },
            {
                'message': "The algos are particularly active today. They're predictable if you understand their programming.",
                'focus': "Watch for patterns in the 5-minute timeframe. That's where they reveal themselves."
            },
            {
                'message': "Market's giving mixed signals? Perfect. Chaos is where the real opportunities hide.",
                'focus': "Reduce position size, increase selectivity. Quality over quantity today."
            },
            {
                'message': "Seeing some interesting dark pool activity. The smart money is positioning.",
                'focus': "Follow the institutional footprints, but don't chase. Let them come to you."
            },
            {
                'message': "Today's setup reminds me of early SpaceX days. High risk, higher reward potential.",
                'focus': "If you're going to take risks today, make sure the reward justifies it. 3:1 minimum."
            }
        ]
        
        insight = random.choice(insights)
        quote = random.choice(self.elon_bot.quotes['general'])
        
        return {
            'type': 'daily_insight',
            'insight': insight['message'],
            'focus': insight['focus'],
            'quote': quote,
            'emoji': self.elon_bot.emoji,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_market_efficiency_comment(self) -> str:
        """Get Elon's take on current market efficiency"""
        return self.elon_bot.get_market_efficiency_comment()
    
    def get_closing_thought(self) -> str:
        """Get Elon's closing thought for the day"""
        return self.elon_bot.get_closing_thought()
    
    def stop(self):
        """Stop the observer integration"""
        self.is_active = False
        logger.info("Observer Integration stopped")


# Singleton instance
_observer_integration = None

def get_observer_integration() -> ObserverIntegration:
    """Get or create the observer integration singleton"""
    global _observer_integration
    if _observer_integration is None:
        _observer_integration = ObserverIntegration()
    return _observer_integration


# Convenience functions for easy integration

async def notify_trade_completed(trade_data: Dict):
    """Notify observer of completed trade"""
    integration = get_observer_integration()
    await integration.on_trade_completed(trade_data)

async def notify_trader_behavior(behavior: str, context: Dict = None):
    """Notify observer of trader behavior"""
    integration = get_observer_integration()
    await integration.on_trader_behavior(behavior, context)

async def notify_market_update(market_state: str):
    """Notify observer of market state change"""
    integration = get_observer_integration()
    await integration.on_market_update(market_state)

async def notify_milestone(milestone_type: str, data: Dict):
    """Notify observer of milestone achievement"""
    integration = get_observer_integration()
    await integration.on_milestone_achieved(milestone_type, data)

def register_observer_callback(callback: Callable):
    """Register callback for observer events"""
    integration = get_observer_integration()
    integration.register_callback(callback)


# Example usage
if __name__ == "__main__":
    async def example_callback(event: ObserverEvent):
        print(f"Observer Event: {event.event_type}")
        print(f"Data: {event.data}")
        print(f"Priority: {event.priority}")
        print("-" * 50)
    
    async def run_example():
        # Get integration instance
        integration = get_observer_integration()
        
        # Register callback
        integration.register_callback(example_callback)
        
        # Start monitoring in background
        monitor_task = asyncio.create_task(integration.start_monitoring())
        
        # Simulate some events
        await asyncio.sleep(1)
        
        # Market update
        await integration.on_market_update("volatile")
        
        # Trade completed
        await integration.on_trade_completed({
            'profit': 250,
            'risk_reward_ratio': 4.2,
            'hold_time_minutes': 35
        })
        
        # Trader behavior
        await integration.on_trader_behavior("disciplined", {'streak': 5})
        
        # Milestone
        await integration.on_milestone_achieved("profit_milestone", {'amount': 1000})
        
        # Get daily insight
        insight = await integration.get_daily_insight()
        print(f"Daily Insight: {insight}")
        
        # Wait a bit
        await asyncio.sleep(5)
        
        # Stop
        integration.stop()
        await monitor_task
    
    # Run example
    asyncio.run(run_example())