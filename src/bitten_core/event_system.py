"""
Event System for HydraX
Manages special events, bonuses, and time-based features
"""

import asyncio
import random
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import pytz
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Types of events in the system"""
    HAPPY_HOUR = "happy_hour"
    MIDNIGHT_HAMMER = "midnight_hammer"
    WEEKEND_WARRIORS = "weekend_warriors"
    FANG_FRIDAY = "fang_friday"
    STUDY_SUNDAY = "study_sunday"
    CUSTOM = "custom"

class EventStatus(Enum):
    """Status of an event"""
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class Event:
    """Represents a single event"""
    id: str
    type: EventType
    name: str
    description: str
    start_time: datetime
    end_time: datetime
    status: EventStatus = EventStatus.SCHEDULED
    multipliers: Dict[str, float] = field(default_factory=dict)
    restrictions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    notifications_sent: List[str] = field(default_factory=list)

class EventScheduler:
    """Handles scheduling and management of events"""
    
    def __init__(self, timezone: str = "UTC"):
        self.timezone = pytz.timezone(timezone)
        self.events: Dict[str, Event] = {}
        self.active_events: List[Event] = []
        self.event_history: List[Event] = []
        self.subscribers: Dict[str, List[callable]] = {}
        self._running = False
        self._scheduler_task = None
        
    async def start(self):
        """Start the event scheduler"""
        if self._running:
            return
            
        self._running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
        
        # Schedule recurring events
        await self._schedule_recurring_events()
        
        logger.info("Event scheduler started")
        
    async def stop(self):
        """Stop the event scheduler"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Event scheduler stopped")
        
    async def _run_scheduler(self):
        """Main scheduler loop"""
        while self._running:
            try:
                current_time = datetime.now(self.timezone)
                
                # Check for events to activate
                for event_id, event in list(self.events.items()):
                    if event.status == EventStatus.SCHEDULED and event.start_time <= current_time:
                        await self._activate_event(event)
                        
                # Check for events to deactivate
                for event in list(self.active_events):
                    if event.end_time <= current_time:
                        await self._deactivate_event(event)
                        
                # Sleep for a short interval
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in event scheduler: {e}")
                await asyncio.sleep(60)  # Sleep longer on error
                
    async def _schedule_recurring_events(self):
        """Schedule all recurring events"""
        current_time = datetime.now(self.timezone)
        
        # Schedule Happy Hour events for the next week
        await self._schedule_happy_hours(current_time)
        
        # Schedule daily Midnight Hammer events
        await self._schedule_midnight_hammers(current_time)
        
        # Schedule Weekend Warriors
        await self._schedule_weekend_warriors(current_time)
        
        # Schedule FANG Friday
        await self._schedule_fang_fridays(current_time)
        
        # Schedule Study Sunday
        await self._schedule_study_sundays(current_time)
        
    async def _schedule_happy_hours(self, start_date: datetime):
        """Schedule random Happy Hour events (2x XP windows)"""
        for day in range(7):  # Schedule for next 7 days
            date = start_date + timedelta(days=day)
            
            # 2-3 happy hours per day at random times
            num_happy_hours = random.randint(2, 3)
            
            for _ in range(num_happy_hours):
                # Random hour between 9 AM and 9 PM
                hour = random.randint(9, 21)
                duration = random.randint(1, 2)  # 1-2 hours
                
                start = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                end = start + timedelta(hours=duration)
                
                event = Event(
                    id=f"happy_hour_{start.strftime('%Y%m%d_%H')}",
                    type=EventType.HAPPY_HOUR,
                    name="Happy Hour - 2X XP",
                    description="Earn double XP on all trades during this time!",
                    start_time=start,
                    end_time=end,
                    multipliers={"xp": 2.0},
                    metadata={"auto_scheduled": True}
                )
                
                await self.schedule_event(event)
                
    async def _schedule_midnight_hammers(self, start_date: datetime):
        """Schedule Midnight Hammer events (FANG+ only)"""
        for day in range(7):  # Schedule for next 7 days
            date = start_date + timedelta(days=day)
            
            # Midnight to 2 AM
            start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=2)
            
            event = Event(
                id=f"midnight_hammer_{start.strftime('%Y%m%d')}",
                type=EventType.MIDNIGHT_HAMMER,
                name="Midnight Hammer",
                description="Exclusive high-volatility signals for FANG+ members only!",
                start_time=start,
                end_time=end,
                restrictions={"min_tier": "FANG"},
                metadata={
                    "auto_scheduled": True,
                    "signal_types": ["high_volatility", "scalping"],
                    "signal_frequency_multiplier": 2.0
                }
            )
            
            await self.schedule_event(event)
            
    async def _schedule_weekend_warriors(self, start_date: datetime):
        """Schedule Weekend Warriors events (NIBBLER bonus signals)"""
        # Find next Saturday
        days_until_saturday = (5 - start_date.weekday()) % 7
        if days_until_saturday == 0 and start_date.hour >= 12:
            days_until_saturday = 7
            
        next_saturday = start_date + timedelta(days=days_until_saturday)
        
        # Schedule for Saturday and Sunday
        for day_offset in [0, 1]:
            date = next_saturday + timedelta(days=day_offset)
            start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            
            event = Event(
                id=f"weekend_warriors_{start.strftime('%Y%m%d')}",
                type=EventType.WEEKEND_WARRIORS,
                name="Weekend Warriors",
                description="NIBBLER members get bonus signals all weekend!",
                start_time=start,
                end_time=end,
                restrictions={"min_tier": "NIBBLER"},
                metadata={
                    "auto_scheduled": True,
                    "bonus_signals": 5,
                    "signal_quality_boost": 1.2
                }
            )
            
            await self.schedule_event(event)
            
    async def _schedule_fang_fridays(self, start_date: datetime):
        """Schedule FANG Friday events (exclusive signals)"""
        # Find next Friday
        days_until_friday = (4 - start_date.weekday()) % 7
        if days_until_friday == 0 and start_date.hour >= 18:
            days_until_friday = 7
            
        next_friday = start_date + timedelta(days=days_until_friday)
        
        start = next_friday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        event = Event(
            id=f"fang_friday_{start.strftime('%Y%m%d')}",
            type=EventType.FANG_FRIDAY,
            name="FANG Friday",
            description="Exclusive premium signals for FANG and FANG+ members!",
            start_time=start,
            end_time=end,
            restrictions={"min_tier": "FANG"},
            metadata={
                "auto_scheduled": True,
                "exclusive_signals": ["whale_trades", "institutional_flow"],
                "signal_accuracy_boost": 1.5
            }
        )
        
        await self.schedule_event(event)
        
    async def _schedule_study_sundays(self, start_date: datetime):
        """Schedule Study Sunday events (2x education XP)"""
        # Find next Sunday
        days_until_sunday = (6 - start_date.weekday()) % 7
        if days_until_sunday == 0 and start_date.hour >= 20:
            days_until_sunday = 7
            
        next_sunday = start_date + timedelta(days=days_until_sunday)
        
        start = next_sunday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        event = Event(
            id=f"study_sunday_{start.strftime('%Y%m%d')}",
            type=EventType.STUDY_SUNDAY,
            name="Study Sunday",
            description="Double XP on all educational activities and quiz completions!",
            start_time=start,
            end_time=end,
            multipliers={"education_xp": 2.0, "quiz_xp": 2.0},
            metadata={
                "auto_scheduled": True,
                "bonus_courses": ["advanced_ta", "risk_management"]
            }
        )
        
        await self.schedule_event(event)
        
    async def schedule_event(self, event: Event) -> bool:
        """Schedule a new event"""
        if event.id in self.events:
            logger.warning(f"Event {event.id} already scheduled")
            return False
            
        self.events[event.id] = event
        
        # Send scheduling notification
        await self._send_notification(event, "scheduled")
        
        logger.info(f"Scheduled event: {event.name} ({event.id})")
        return True
        
    async def cancel_event(self, event_id: str) -> bool:
        """Cancel a scheduled event"""
        if event_id not in self.events:
            return False
            
        event = self.events[event_id]
        event.status = EventStatus.CANCELLED
        
        # Remove from active events if active
        if event in self.active_events:
            self.active_events.remove(event)
            
        # Send cancellation notification
        await self._send_notification(event, "cancelled")
        
        # Move to history
        self.event_history.append(event)
        del self.events[event_id]
        
        return True
        
    async def _activate_event(self, event: Event):
        """Activate an event"""
        event.status = EventStatus.ACTIVE
        self.active_events.append(event)
        
        # Send activation notification
        await self._send_notification(event, "started")
        
        # Trigger event handlers
        await self._trigger_event_handlers(event, "start")
        
        logger.info(f"Activated event: {event.name}")
        
    async def _deactivate_event(self, event: Event):
        """Deactivate an event"""
        event.status = EventStatus.COMPLETED
        self.active_events.remove(event)
        
        # Send completion notification
        await self._send_notification(event, "ended")
        
        # Trigger event handlers
        await self._trigger_event_handlers(event, "end")
        
        # Move to history
        self.event_history.append(event)
        del self.events[event.id]
        
        logger.info(f"Deactivated event: {event.name}")
        
    async def _send_notification(self, event: Event, notification_type: str):
        """Send event notification"""
        notification_id = f"{event.id}_{notification_type}"
        
        if notification_id in event.notifications_sent:
            return
            
        # Build notification message
        if notification_type == "scheduled":
            message = f"📅 Event Scheduled: {event.name}\n{event.description}\nStarts: {event.start_time.strftime('%Y-%m-%d %H:%M %Z')}"
        elif notification_type == "started":
            message = f"🎉 Event Started: {event.name}\n{event.description}\nEnds: {event.end_time.strftime('%H:%M %Z')}"
        elif notification_type == "ended":
            message = f"✅ Event Ended: {event.name}\nThank you for participating!"
        elif notification_type == "cancelled":
            message = f"❌ Event Cancelled: {event.name}"
        else:
            message = f"Event Update: {event.name}"
            
        # Send notification through appropriate channels
        await self._broadcast_notification(event, message, notification_type)
        
        event.notifications_sent.append(notification_id)
        
    async def _broadcast_notification(self, event: Event, message: str, notification_type: str):
        """Broadcast notification to appropriate channels"""
        # This would integrate with your notification system
        # For now, just log it
        logger.info(f"Notification: {message}")
        
        # In production, this would:
        # - Send to Discord channels based on event restrictions
        # - Send push notifications to mobile app users
        # - Update website notifications
        # - Send emails for important events
        
    async def _trigger_event_handlers(self, event: Event, action: str):
        """Trigger registered event handlers"""
        handler_key = f"{event.type.value}_{action}"
        
        if handler_key in self.subscribers:
            for handler in self.subscribers[handler_key]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
                    
    def subscribe(self, event_type: EventType, action: str, handler: callable):
        """Subscribe to event notifications"""
        handler_key = f"{event_type.value}_{action}"
        
        if handler_key not in self.subscribers:
            self.subscribers[handler_key] = []
            
        self.subscribers[handler_key].append(handler)
        
    def get_active_events(self) -> List[Event]:
        """Get all currently active events"""
        return self.active_events.copy()
        
    def get_upcoming_events(self, hours: int = 24) -> List[Event]:
        """Get upcoming events within specified hours"""
        current_time = datetime.now(self.timezone)
        cutoff_time = current_time + timedelta(hours=hours)
        
        upcoming = [
            event for event in self.events.values()
            if event.status == EventStatus.SCHEDULED 
            and event.start_time <= cutoff_time
        ]
        
        return sorted(upcoming, key=lambda e: e.start_time)
        
    def get_event_multipliers(self, multiplier_type: str) -> float:
        """Get current multiplier for a specific type"""
        multiplier = 1.0
        
        for event in self.active_events:
            if multiplier_type in event.multipliers:
                multiplier *= event.multipliers[multiplier_type]
                
        return multiplier
        
    def check_user_eligibility(self, user_tier: str, event: Event) -> bool:
        """Check if a user is eligible for an event"""
        if "min_tier" not in event.restrictions:
            return True
            
        tier_hierarchy = ["HATCHLING", "NIBBLER", "FANG", "FANG+"]
        min_tier = event.restrictions["min_tier"]
        
        if min_tier not in tier_hierarchy:
            return True
            
        if user_tier not in tier_hierarchy:
            return False
            
        return tier_hierarchy.index(user_tier) >= tier_hierarchy.index(min_tier)
        
    async def create_custom_event(
        self,
        name: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        multipliers: Optional[Dict[str, float]] = None,
        restrictions: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Event:
        """Create a custom event"""
        event_id = f"custom_{int(start_time.timestamp())}"
        
        event = Event(
            id=event_id,
            type=EventType.CUSTOM,
            name=name,
            description=description,
            start_time=start_time,
            end_time=end_time,
            multipliers=multipliers or {},
            restrictions=restrictions or {},
            metadata=metadata or {}
        )
        
        await self.schedule_event(event)
        return event
        
    def export_event_schedule(self) -> Dict[str, Any]:
        """Export the event schedule as JSON"""
        schedule = {
            "active_events": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.type.value,
                    "start_time": e.start_time.isoformat(),
                    "end_time": e.end_time.isoformat(),
                    "multipliers": e.multipliers,
                    "restrictions": e.restrictions
                }
                for e in self.active_events
            ],
            "upcoming_events": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.type.value,
                    "start_time": e.start_time.isoformat(),
                    "end_time": e.end_time.isoformat(),
                    "multipliers": e.multipliers,
                    "restrictions": e.restrictions
                }
                for e in self.get_upcoming_events(168)  # Next week
            ]
        }
        
        return schedule

class EventManager:
    """High-level event management interface"""
    
    def __init__(self, timezone: str = "UTC"):
        self.scheduler = EventScheduler(timezone)
        self.event_stats: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize the event manager"""
        await self.scheduler.start()
        
        # Register default event handlers
        self._register_default_handlers()
        
    async def shutdown(self):
        """Shutdown the event manager"""
        await self.scheduler.stop()
        
    def _register_default_handlers(self):
        """Register default event handlers"""
        # Happy Hour handler
        async def happy_hour_start(event: Event):
            logger.info(f"Happy Hour started! 2X XP active until {event.end_time.strftime('%H:%M')}")
            
        self.scheduler.subscribe(EventType.HAPPY_HOUR, "start", happy_hour_start)
        
        # Midnight Hammer handler
        async def midnight_hammer_start(event: Event):
            logger.info("Midnight Hammer active! High-volatility signals available for FANG+ members")
            
        self.scheduler.subscribe(EventType.MIDNIGHT_HAMMER, "start", midnight_hammer_start)
        
    def get_current_xp_multiplier(self) -> float:
        """Get the current XP multiplier from active events"""
        return self.scheduler.get_event_multipliers("xp")
        
    def get_current_education_xp_multiplier(self) -> float:
        """Get the current education XP multiplier"""
        return self.scheduler.get_event_multipliers("education_xp")
        
    def is_user_eligible_for_active_events(self, user_tier: str) -> List[Event]:
        """Get active events the user is eligible for"""
        eligible_events = []
        
        for event in self.scheduler.get_active_events():
            if self.scheduler.check_user_eligibility(user_tier, event):
                eligible_events.append(event)
                
        return eligible_events
        
    async def get_event_calendar(self, days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """Get event calendar for specified number of days"""
        calendar = {}
        current_date = datetime.now(self.scheduler.timezone)
        
        for day in range(days):
            date = current_date + timedelta(days=day)
            date_str = date.strftime("%Y-%m-%d")
            
            calendar[date_str] = []
            
            # Get events for this day
            for event in self.scheduler.get_upcoming_events(days * 24):
                if event.start_time.date() == date.date():
                    calendar[date_str].append({
                        "name": event.name,
                        "type": event.type.value,
                        "start_time": event.start_time.strftime("%H:%M"),
                        "end_time": event.end_time.strftime("%H:%M"),
                        "description": event.description,
                        "restrictions": event.restrictions
                    })
                    
        return calendar
        
    def record_event_participation(self, event_id: str, user_id: str, metrics: Dict[str, Any]):
        """Record user participation in an event"""
        if event_id not in self.event_stats:
            self.event_stats[event_id] = {
                "participants": set(),
                "total_xp_earned": 0,
                "total_trades": 0,
                "metrics": {}
            }
            
        stats = self.event_stats[event_id]
        stats["participants"].add(user_id)
        
        # Update metrics
        for key, value in metrics.items():
            if key not in stats["metrics"]:
                stats["metrics"][key] = 0
            stats["metrics"][key] += value

# Example usage
async def main():
    """Example usage of the event system"""
    manager = EventManager(timezone="US/Eastern")
    await manager.initialize()
    
    # Get current XP multiplier
    xp_multiplier = manager.get_current_xp_multiplier()
    print(f"Current XP multiplier: {xp_multiplier}x")
    
    # Check upcoming events
    upcoming = manager.scheduler.get_upcoming_events(24)
    print(f"\nUpcoming events in next 24 hours:")
    for event in upcoming:
        print(f"- {event.name} at {event.start_time.strftime('%H:%M')}")
        
    # Get event calendar
    calendar = await manager.get_event_calendar(7)
    print(f"\nEvent calendar for next 7 days:")
    for date, events in calendar.items():
        if events:
            print(f"\n{date}:")
            for event in events:
                print(f"  - {event['name']} ({event['start_time']} - {event['end_time']})")
                
    # Create a custom event
    custom_event = await manager.scheduler.create_custom_event(
        name="Flash Sale - 3X XP",
        description="Limited time 3X XP boost!",
        start_time=datetime.now(manager.scheduler.timezone) + timedelta(hours=1),
        end_time=datetime.now(manager.scheduler.timezone) + timedelta(hours=2),
        multipliers={"xp": 3.0}
    )
    print(f"\nCreated custom event: {custom_event.name}")
    
    # Let it run for a bit
    await asyncio.sleep(5)
    
    await manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())