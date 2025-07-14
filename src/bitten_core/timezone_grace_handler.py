"""
Timezone and Grace Period Handler for BITTEN Daily Login Streak System
Advanced timezone handling and grace periods to maximize user retention
"""

import pytz
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class GracePeriodType(Enum):
    """Types of grace periods"""
    STANDARD = "standard"          # 6-hour grace period
    EXTENDED = "extended"          # 12-hour grace period for long streaks
    WEEKEND = "weekend"            # Special weekend grace period
    HOLIDAY = "holiday"            # Holiday grace period
    MAINTENANCE = "maintenance"    # System maintenance grace period


class TimezoneBehavior(Enum):
    """How to handle timezone changes"""
    STRICT = "strict"              # Must login in user's timezone
    FLEXIBLE = "flexible"          # Allow login in any timezone
    SMART = "smart"               # Smart detection of travel/timezone changes


@dataclass
class GracePeriodConfig:
    """Grace period configuration"""
    standard_hours: int = 6        # Standard 6-hour grace period
    extended_hours: int = 12       # Extended grace for long streaks
    weekend_hours: int = 8         # Weekend grace period
    holiday_hours: int = 24        # Holiday grace period
    maintenance_hours: int = 48    # Maintenance grace period
    
    # Streak thresholds for extended grace
    extended_grace_threshold: int = 30    # 30+ day streaks get extended grace
    maximum_grace_uses: int = 3           # Max grace uses per month


@dataclass
class TimezoneInfo:
    """User timezone information"""
    user_id: str
    current_timezone: str
    detected_timezone: str
    last_timezone_change: Optional[datetime]
    timezone_changes_count: int
    auto_detect_enabled: bool
    manual_override: bool


@dataclass
class GracePeriodStatus:
    """Grace period status for a user"""
    is_active: bool
    grace_type: GracePeriodType
    started_at: datetime
    ends_at: datetime
    hours_remaining: float
    uses_this_month: int
    can_extend: bool
    reason: str


class TimezoneGraceHandler:
    """Advanced timezone and grace period management for streak retention"""
    
    # Common timezone mappings for smart detection
    TIMEZONE_ALIASES = {
        'EST': 'America/New_York',
        'PST': 'America/Los_Angeles',
        'GMT': 'Europe/London',
        'CET': 'Europe/Paris',
        'JST': 'Asia/Tokyo',
        'AEST': 'Australia/Sydney',
        'IST': 'Asia/Kolkata',
        'MST': 'America/Denver',
        'CST': 'America/Chicago',
    }
    
    # Major trading market timezones
    TRADING_MARKET_TIMEZONES = {
        'london': 'Europe/London',
        'new_york': 'America/New_York',
        'tokyo': 'Asia/Tokyo',
        'sydney': 'Australia/Sydney',
        'hong_kong': 'Asia/Hong_Kong',
        'singapore': 'Asia/Singapore',
        'zurich': 'Europe/Zurich',
        'frankfurt': 'Europe/Berlin',
    }
    
    # Holiday periods that trigger extended grace
    HOLIDAY_PERIODS = {
        'christmas': {'start': '12-24', 'end': '12-26'},
        'new_year': {'start': '12-31', 'end': '01-02'},
        'thanksgiving': {'month': 11, 'week': 4, 'day': 4},  # 4th Thursday of November
        'easter': 'variable',  # Would need calculation
    }
    
    def __init__(self, grace_config: Optional[GracePeriodConfig] = None):
        self.config = grace_config or GracePeriodConfig()
        self.timezone_cache = {}  # Cache for timezone objects
        self.grace_period_storage = {}  # In-memory storage for grace periods
    
    def detect_user_timezone(self, user_id: str, client_timezone: str = None, 
                           ip_address: str = None) -> TimezoneInfo:
        """
        Detect and validate user timezone from multiple sources
        
        Args:
            user_id: User identifier
            client_timezone: Timezone from client (JavaScript)
            ip_address: User's IP address for geo-detection
            
        Returns:
            TimezoneInfo with detected timezone
        """
        # Priority order: manual override > client timezone > IP geolocation > default
        detected_timezone = "UTC"
        
        # 1. Check for manual override in user settings
        manual_override = self._get_user_timezone_override(user_id)
        if manual_override:
            detected_timezone = manual_override
            logger.info(f"Using manual timezone override for user {user_id}: {detected_timezone}")
        
        # 2. Use client-provided timezone
        elif client_timezone:
            validated_tz = self._validate_timezone(client_timezone)
            if validated_tz:
                detected_timezone = validated_tz
                logger.info(f"Using client timezone for user {user_id}: {detected_timezone}")
        
        # 3. IP-based geolocation (would integrate with geolocation service)
        elif ip_address:
            geo_timezone = self._detect_timezone_from_ip(ip_address)
            if geo_timezone:
                detected_timezone = geo_timezone
                logger.info(f"Using geo-detected timezone for user {user_id}: {detected_timezone}")
        
        # Get current timezone info
        current_timezone = self._get_current_user_timezone(user_id) or detected_timezone
        
        # Check for timezone changes
        timezone_change_detected = current_timezone != detected_timezone
        last_change = None
        change_count = 0
        
        if timezone_change_detected:
            change_count = self._increment_timezone_change_count(user_id)
            last_change = datetime.now(timezone.utc)
            logger.info(f"Timezone change detected for user {user_id}: {current_timezone} -> {detected_timezone}")
        
        return TimezoneInfo(
            user_id=user_id,
            current_timezone=current_timezone,
            detected_timezone=detected_timezone,
            last_timezone_change=last_change,
            timezone_changes_count=change_count,
            auto_detect_enabled=True,
            manual_override=manual_override is not None
        )
    
    def calculate_grace_period(self, user_id: str, current_streak: int, 
                             last_login: datetime, timezone_info: TimezoneInfo,
                             special_circumstances: List[str] = None) -> GracePeriodStatus:
        """
        Calculate available grace period for user based on multiple factors
        
        Args:
            user_id: User identifier
            current_streak: Current login streak
            last_login: Last login timestamp
            timezone_info: User's timezone information
            special_circumstances: Special circumstances (maintenance, holiday, etc.)
            
        Returns:
            GracePeriodStatus with grace period details
        """
        special_circumstances = special_circumstances or []
        
        # Check if grace period is already active
        active_grace = self._get_active_grace_period(user_id)
        if active_grace:
            return active_grace
        
        # Determine grace period type and duration
        grace_type, grace_hours, reason = self._determine_grace_period_type(
            current_streak, special_circumstances, timezone_info
        )
        
        # Check usage limits
        monthly_uses = self._get_monthly_grace_uses(user_id)
        can_use_grace = monthly_uses < self.config.maximum_grace_uses
        
        if not can_use_grace and grace_type == GracePeriodType.STANDARD:
            return GracePeriodStatus(
                is_active=False,
                grace_type=grace_type,
                started_at=datetime.now(timezone.utc),
                ends_at=datetime.now(timezone.utc),
                hours_remaining=0,
                uses_this_month=monthly_uses,
                can_extend=False,
                reason="Monthly grace period limit reached"
            )
        
        # Calculate grace period timing
        user_tz = pytz.timezone(timezone_info.current_timezone)
        now_user_tz = datetime.now(user_tz)
        
        # Grace period starts from last expected login time
        expected_login_time = self._calculate_next_expected_login(last_login, timezone_info)
        grace_start = expected_login_time
        grace_end = grace_start + timedelta(hours=grace_hours)
        
        # Check if we're currently in the grace period
        is_active = grace_start <= now_user_tz <= grace_end
        hours_remaining = max(0, (grace_end - now_user_tz).total_seconds() / 3600)
        
        # Can extend if it's a special circumstance or long streak
        can_extend = (
            grace_type in [GracePeriodType.HOLIDAY, GracePeriodType.MAINTENANCE] or
            current_streak >= self.config.extended_grace_threshold
        )
        
        return GracePeriodStatus(
            is_active=is_active,
            grace_type=grace_type,
            started_at=grace_start.astimezone(timezone.utc),
            ends_at=grace_end.astimezone(timezone.utc),
            hours_remaining=hours_remaining,
            uses_this_month=monthly_uses,
            can_extend=can_extend,
            reason=reason
        )
    
    def use_grace_period(self, user_id: str, grace_status: GracePeriodStatus) -> bool:
        """
        Activate a grace period for the user
        
        Args:
            user_id: User identifier
            grace_status: Grace period status to activate
            
        Returns:
            True if grace period was successfully activated
        """
        if not grace_status.is_active:
            return False
        
        # Record grace period usage
        self._record_grace_period_usage(user_id, grace_status)
        
        # Store active grace period
        self.grace_period_storage[user_id] = grace_status
        
        logger.info(f"Grace period activated for user {user_id}: {grace_status.grace_type.value} - {grace_status.reason}")
        return True
    
    def check_login_window(self, user_id: str, timezone_info: TimezoneInfo,
                          last_login: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Check if user is within valid login window (including grace periods)
        
        Args:
            user_id: User identifier
            timezone_info: User's timezone information
            last_login: Last login timestamp
            
        Returns:
            Dictionary with login window status
        """
        user_tz = pytz.timezone(timezone_info.current_timezone)
        now_user_tz = datetime.now(user_tz)
        today_user = now_user_tz.date()
        
        # Calculate expected login windows
        login_windows = self._calculate_login_windows(today_user, user_tz)
        
        # Check current window
        current_window = None
        in_valid_window = False
        
        for window in login_windows:
            if window['start'] <= now_user_tz <= window['end']:
                current_window = window
                in_valid_window = True
                break
        
        # Check grace period if not in valid window
        grace_available = False
        grace_info = None
        
        if not in_valid_window and last_login:
            # This would integrate with the full streak system
            current_streak = self._get_current_streak(user_id)  # Placeholder
            grace_status = self.calculate_grace_period(
                user_id, current_streak, last_login, timezone_info
            )
            
            if grace_status.is_active and grace_status.hours_remaining > 0:
                grace_available = True
                grace_info = grace_status
        
        return {
            'in_valid_window': in_valid_window,
            'current_window': current_window,
            'all_windows': login_windows,
            'grace_available': grace_available,
            'grace_info': grace_info,
            'user_timezone': timezone_info.current_timezone,
            'user_local_time': now_user_tz.isoformat(),
            'next_window': self._get_next_login_window(login_windows, now_user_tz)
        }
    
    def handle_timezone_change(self, user_id: str, old_timezone: str, 
                             new_timezone: str, reason: str = "user_change") -> Dict[str, Any]:
        """
        Handle user timezone changes intelligently
        
        Args:
            user_id: User identifier
            old_timezone: Previous timezone
            new_timezone: New timezone
            reason: Reason for change (travel, relocation, etc.)
            
        Returns:
            Dictionary with change handling results
        """
        # Validate new timezone
        if not self._validate_timezone(new_timezone):
            return {
                'success': False,
                'error': 'Invalid timezone',
                'suggested_timezone': self._suggest_similar_timezone(new_timezone)
            }
        
        # Calculate time difference
        old_tz = pytz.timezone(old_timezone)
        new_tz = pytz.timezone(new_timezone)
        now = datetime.now(timezone.utc)
        
        old_time = now.astimezone(old_tz)
        new_time = now.astimezone(new_tz)
        time_diff_hours = (new_time.utcoffset() - old_time.utcoffset()).total_seconds() / 3600
        
        # Determine if this is a reasonable change
        is_reasonable_change = self._is_reasonable_timezone_change(
            old_timezone, new_timezone, time_diff_hours, reason
        )
        
        # Handle the change
        change_result = {
            'success': True,
            'old_timezone': old_timezone,
            'new_timezone': new_timezone,
            'time_difference_hours': time_diff_hours,
            'is_reasonable': is_reasonable_change,
            'reason': reason,
            'grace_period_granted': False,
            'streak_protection_recommended': False
        }
        
        # Grant special grace period for travel/legitimate changes
        if is_reasonable_change and abs(time_diff_hours) >= 3:
            # Grant extended grace period for significant timezone changes
            special_grace = GracePeriodStatus(
                is_active=True,
                grace_type=GracePeriodType.EXTENDED,
                started_at=now,
                ends_at=now + timedelta(hours=self.config.extended_hours),
                hours_remaining=self.config.extended_hours,
                uses_this_month=self._get_monthly_grace_uses(user_id),
                can_extend=True,
                reason=f"Timezone change: {reason}"
            )
            
            self.grace_period_storage[user_id] = special_grace
            change_result['grace_period_granted'] = True
            change_result['grace_period_hours'] = self.config.extended_hours
        
        # Recommend streak protection for major changes
        if abs(time_diff_hours) >= 6:
            change_result['streak_protection_recommended'] = True
            change_result['protection_reason'] = "Major timezone change detected"
        
        # Update user timezone
        self._update_user_timezone(user_id, new_timezone, reason)
        
        logger.info(f"Timezone change handled for user {user_id}: {old_timezone} -> {new_timezone} ({reason})")
        return change_result
    
    def get_optimal_login_time(self, user_id: str, timezone_info: TimezoneInfo) -> Dict[str, Any]:
        """
        Calculate optimal login time for user to maintain streak
        
        Args:
            user_id: User identifier
            timezone_info: User's timezone information
            
        Returns:
            Dictionary with optimal login timing
        """
        user_tz = pytz.timezone(timezone_info.current_timezone)
        now_user_tz = datetime.now(user_tz)
        
        # Calculate today's optimal window (early in day but not too early)
        today = now_user_tz.date()
        optimal_start = user_tz.localize(datetime.combine(today, datetime.min.time().replace(hour=6)))
        optimal_end = user_tz.localize(datetime.combine(today, datetime.min.time().replace(hour=23)))
        
        # If it's past optimal time today, show tomorrow's window
        if now_user_tz > optimal_end:
            tomorrow = today + timedelta(days=1)
            optimal_start = user_tz.localize(datetime.combine(tomorrow, datetime.min.time().replace(hour=6)))
            optimal_end = user_tz.localize(datetime.combine(tomorrow, datetime.min.time().replace(hour=23)))
        
        # Calculate grace period cutoff
        grace_cutoff = optimal_end + timedelta(hours=self.config.standard_hours)
        
        return {
            'optimal_start': optimal_start.isoformat(),
            'optimal_end': optimal_end.isoformat(),
            'grace_cutoff': grace_cutoff.isoformat(),
            'current_time': now_user_tz.isoformat(),
            'timezone': timezone_info.current_timezone,
            'recommendations': self._generate_login_recommendations(now_user_tz, optimal_start, optimal_end)
        }
    
    def _determine_grace_period_type(self, current_streak: int, special_circumstances: List[str],
                                   timezone_info: TimezoneInfo) -> Tuple[GracePeriodType, int, str]:
        """Determine appropriate grace period type and duration"""
        
        # Check for special circumstances first
        if 'maintenance' in special_circumstances:
            return (GracePeriodType.MAINTENANCE, self.config.maintenance_hours, 
                   "System maintenance grace period")
        
        if 'holiday' in special_circumstances or self._is_holiday_period():
            return (GracePeriodType.HOLIDAY, self.config.holiday_hours,
                   "Holiday grace period")
        
        # Check for weekend
        user_tz = pytz.timezone(timezone_info.current_timezone)
        now_user = datetime.now(user_tz)
        if now_user.weekday() >= 5:  # Saturday or Sunday
            return (GracePeriodType.WEEKEND, self.config.weekend_hours,
                   "Weekend grace period")
        
        # Extended grace for long streaks
        if current_streak >= self.config.extended_grace_threshold:
            return (GracePeriodType.EXTENDED, self.config.extended_hours,
                   f"Extended grace for {current_streak}-day streak")
        
        # Standard grace period
        return (GracePeriodType.STANDARD, self.config.standard_hours,
               "Standard grace period")
    
    def _validate_timezone(self, timezone_str: str) -> Optional[str]:
        """Validate and normalize timezone string"""
        if not timezone_str:
            return None
        
        # Check aliases first
        if timezone_str.upper() in self.TIMEZONE_ALIASES:
            return self.TIMEZONE_ALIASES[timezone_str.upper()]
        
        # Try to create timezone object
        try:
            pytz.timezone(timezone_str)
            return timezone_str
        except pytz.exceptions.UnknownTimeZoneError:
            # Try to find similar timezone
            return self._suggest_similar_timezone(timezone_str)
    
    def _suggest_similar_timezone(self, invalid_timezone: str) -> Optional[str]:
        """Suggest a similar valid timezone"""
        invalid_lower = invalid_timezone.lower()
        
        # Check for common patterns
        for valid_tz in pytz.all_timezones:
            if invalid_lower in valid_tz.lower():
                return valid_tz
        
        # Check trading market timezones
        for market, tz in self.TRADING_MARKET_TIMEZONES.items():
            if market in invalid_lower:
                return tz
        
        return None
    
    def _calculate_login_windows(self, date, user_tz) -> List[Dict[str, Any]]:
        """Calculate valid login windows for a date"""
        # Main window: 6 AM to 11:59 PM
        main_start = user_tz.localize(datetime.combine(date, datetime.min.time().replace(hour=6)))
        main_end = user_tz.localize(datetime.combine(date, datetime.min.time().replace(hour=23, minute=59)))
        
        return [{
            'type': 'main',
            'start': main_start,
            'end': main_end,
            'description': 'Main login window'
        }]
    
    def _get_next_login_window(self, windows: List[Dict[str, Any]], current_time: datetime) -> Optional[Dict[str, Any]]:
        """Get the next available login window"""
        for window in windows:
            if window['start'] > current_time:
                return window
        return None
    
    def _is_holiday_period(self) -> bool:
        """Check if current date is in a holiday period"""
        now = datetime.now()
        month_day = f"{now.month:02d}-{now.day:02d}"
        
        for holiday, period in self.HOLIDAY_PERIODS.items():
            if isinstance(period, dict) and 'start' in period:
                if period['start'] <= month_day <= period['end']:
                    return True
        
        return False
    
    def _is_reasonable_timezone_change(self, old_tz: str, new_tz: str, 
                                     time_diff_hours: float, reason: str) -> bool:
        """Determine if timezone change is reasonable"""
        # Changes within same continent are usually reasonable
        old_continent = old_tz.split('/')[0] if '/' in old_tz else ''
        new_continent = new_tz.split('/')[0] if '/' in new_tz else ''
        
        # Same continent changes are typically reasonable
        if old_continent == new_continent:
            return True
        
        # Large time differences might indicate travel
        if abs(time_diff_hours) >= 6 and reason in ['travel', 'relocation', 'business_trip']:
            return True
        
        # Frequent small changes might be suspicious
        if abs(time_diff_hours) <= 1:
            return False
        
        return True
    
    def _generate_login_recommendations(self, current_time: datetime, 
                                      optimal_start: datetime, optimal_end: datetime) -> List[str]:
        """Generate personalized login recommendations"""
        recommendations = []
        
        if current_time < optimal_start:
            hours_until = (optimal_start - current_time).total_seconds() / 3600
            recommendations.append(f"Login opens in {hours_until:.1f} hours for today")
        elif current_time <= optimal_end:
            hours_remaining = (optimal_end - current_time).total_seconds() / 3600
            recommendations.append(f"Currently in optimal login window ({hours_remaining:.1f} hours remaining)")
        else:
            recommendations.append("Login window closed for today - grace period may be available")
        
        # Add streak-specific recommendations
        recommendations.append("Log in daily between 6 AM - 11 PM in your timezone for best experience")
        recommendations.append("Set a daily reminder to maintain your streak")
        
        return recommendations
    
    # Placeholder methods that would integrate with the full system
    def _get_user_timezone_override(self, user_id: str) -> Optional[str]:
        """Get manual timezone override from user settings"""
        return None  # Would query user settings database
    
    def _get_current_user_timezone(self, user_id: str) -> Optional[str]:
        """Get current timezone for user"""
        return "UTC"  # Would query user database
    
    def _increment_timezone_change_count(self, user_id: str) -> int:
        """Increment and return timezone change count"""
        return 1  # Would update user database
    
    def _get_active_grace_period(self, user_id: str) -> Optional[GracePeriodStatus]:
        """Get active grace period for user"""
        return self.grace_period_storage.get(user_id)
    
    def _get_monthly_grace_uses(self, user_id: str) -> int:
        """Get number of grace periods used this month"""
        return 0  # Would query database
    
    def _calculate_next_expected_login(self, last_login: datetime, timezone_info: TimezoneInfo) -> datetime:
        """Calculate when next login was expected"""
        user_tz = pytz.timezone(timezone_info.current_timezone)
        last_login_user_tz = last_login.astimezone(user_tz)
        next_day = last_login_user_tz.date() + timedelta(days=1)
        return user_tz.localize(datetime.combine(next_day, datetime.min.time()))
    
    def _record_grace_period_usage(self, user_id: str, grace_status: GracePeriodStatus):
        """Record grace period usage in database"""
        pass  # Would insert into database
    
    def _get_current_streak(self, user_id: str) -> int:
        """Get current streak for user"""
        return 0  # Would query streak database
    
    def _update_user_timezone(self, user_id: str, timezone: str, reason: str):
        """Update user timezone in database"""
        pass  # Would update user database
    
    def _detect_timezone_from_ip(self, ip_address: str) -> Optional[str]:
        """Detect timezone from IP address using geolocation service"""
        return None  # Would use geolocation API


# Example usage and testing
if __name__ == "__main__":
    # Initialize timezone grace handler
    handler = TimezoneGraceHandler()
    
    print("=== BITTEN Timezone & Grace Period Handler Demo ===\n")
    
    # Test timezone detection
    user_id = "test_user_123"
    timezone_info = handler.detect_user_timezone(
        user_id=user_id,
        client_timezone="America/New_York",
        ip_address="192.168.1.1"
    )
    
    print(f"Detected timezone: {timezone_info.current_timezone}")
    print(f"Auto-detect enabled: {timezone_info.auto_detect_enabled}")
    print(f"Manual override: {timezone_info.manual_override}")
    
    # Test login window check
    login_window = handler.check_login_window(user_id, timezone_info)
    print(f"\nIn valid window: {login_window['in_valid_window']}")
    print(f"User local time: {login_window['user_local_time']}")
    print(f"Grace available: {login_window['grace_available']}")
    
    # Test optimal login time
    optimal_time = handler.get_optimal_login_time(user_id, timezone_info)
    print(f"\nOptimal login start: {optimal_time['optimal_start']}")
    print(f"Optimal login end: {optimal_time['optimal_end']}")
    print(f"Recommendations: {optimal_time['recommendations'][:2]}")
    
    # Test timezone change handling
    change_result = handler.handle_timezone_change(
        user_id=user_id,
        old_timezone="America/New_York",
        new_timezone="Europe/London",
        reason="business_trip"
    )
    
    print(f"\nTimezone change successful: {change_result['success']}")
    print(f"Time difference: {change_result['time_difference_hours']} hours")
    print(f"Grace period granted: {change_result['grace_period_granted']}")
    print(f"Is reasonable change: {change_result['is_reasonable']}")
    
    print("\n=== Timezone & Grace Handler Ready! ===")