"""
BITTEN Analytics Tracker
Tracks conversion events, user behavior, and A/B testing metrics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import redis
import requests
from collections import defaultdict
import hashlib
import os

# Configure logging
logger = logging.getLogger(__name__)

# Redis configuration for real-time analytics
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=3, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connected for analytics")
except Exception as e:
    logger.warning(f"Redis not available for analytics: {e}")
    redis_client = None

# Analytics configuration
GA_MEASUREMENT_ID = os.getenv('GA_MEASUREMENT_ID', '')
GA_API_SECRET = os.getenv('GA_API_SECRET', '')
FB_PIXEL_ID = os.getenv('FB_PIXEL_ID', '')
FB_ACCESS_TOKEN = os.getenv('FB_ACCESS_TOKEN', '')
MIXPANEL_TOKEN = os.getenv('MIXPANEL_TOKEN', '')

class AnalyticsTracker:
    """Centralized analytics tracking"""
    
    def __init__(self):
        self.event_queue = []
        self.ab_tests = {}
        self.conversion_funnels = self._init_funnels()
    
    def _init_funnels(self) -> Dict[str, List[str]]:
        """Initialize conversion funnels"""
        return {
            'press_pass': [
                'landing_page_view',
                'email_form_focus',
                'email_form_submit',
                'press_pass_claimed',
                'email_opened',
                'telegram_clicked',
                'press_pass_activated',
                'first_trade',
                'tier_upgrade'
            ],
            'direct_signup': [
                'landing_page_view',
                'cta_clicked',
                'telegram_start',
                'tier_selected',
                'payment_initiated',
                'payment_completed',
                'first_trade'
            ]
        }
    
    def track_event(self, event_name: str, properties: Dict[str, Any] = None) -> None:
        """Track an analytics event"""
        try:
            properties = properties or {}
            
            # Add timestamp and session info
            event_data = {
                'event': event_name,
                'timestamp': datetime.utcnow().isoformat(),
                'properties': properties,
                'session_id': properties.get('session_id', self._get_session_id()),
                'user_id': properties.get('user_id'),
                'client_id': properties.get('client_id', self._get_client_id())
            }
            
            # Store in Redis for real-time processing
            if redis_client:
                # Add to event stream
                redis_client.xadd('analytics:events', event_data)
                
                # Update real-time metrics
                self._update_real_time_metrics(event_name, properties)
                
                # Track funnel progress
                self._track_funnel_progress(event_name, properties)
            
            # Queue for batch sending to external services
            self.event_queue.append(event_data)
            
            # Send to external services if queue is large enough
            if len(self.event_queue) >= 10:
                self._flush_events()
            
        except Exception as e:
            logger.error(f"Error tracking event {event_name}: {e}")
    
    def track_page_view(self, page_url: str, page_title: str, properties: Dict = None) -> None:
        """Track page view"""
        properties = properties or {}
        properties.update({
            'page_url': page_url,
            'page_title': page_title,
            'referrer': properties.get('referrer', ''),
            'user_agent': properties.get('user_agent', '')
        })
        
        self.track_event('page_view', properties)
    
    def track_conversion(self, conversion_type: str, value: float = 0, properties: Dict = None) -> None:
        """Track conversion event"""
        properties = properties or {}
        properties.update({
            'conversion_type': conversion_type,
            'value': value,
            'currency': 'USD'
        })
        
        self.track_event(f'conversion_{conversion_type}', properties)
        
        # Update conversion metrics in Redis
        if redis_client:
            today = datetime.utcnow().strftime('%Y-%m-%d')
            redis_client.hincrby(f'conversions:{today}', conversion_type, 1)
            redis_client.hincrbyfloat(f'conversion_value:{today}', conversion_type, value)
    
    def track_ab_test(self, test_name: str, variant: str, properties: Dict = None) -> None:
        """Track A/B test exposure"""
        properties = properties or {}
        properties.update({
            'test_name': test_name,
            'variant': variant
        })
        
        self.track_event('ab_test_exposure', properties)
        
        # Store variant assignment
        if redis_client:
            client_id = properties.get('client_id', self._get_client_id())
            redis_client.hset(f'ab_tests:{client_id}', test_name, variant)
    
    def get_ab_test_metrics(self, test_name: str) -> Dict[str, Any]:
        """Get A/B test performance metrics"""
        try:
            if not redis_client:
                return {}
            
            metrics = {
                'test_name': test_name,
                'variants': {},
                'statistical_significance': False
            }
            
            # Get variant performance
            variants = ['A', 'B']  # TODO: Make this dynamic
            
            for variant in variants:
                exposures = int(redis_client.get(f'ab_test:{test_name}:{variant}:exposures') or 0)
                conversions = int(redis_client.get(f'ab_test:{test_name}:{variant}:conversions') or 0)
                
                conversion_rate = (conversions / exposures * 100) if exposures > 0 else 0
                
                metrics['variants'][variant] = {
                    'exposures': exposures,
                    'conversions': conversions,
                    'conversion_rate': round(conversion_rate, 2)
                }
            
            # Calculate statistical significance
            # TODO: Implement proper statistical test
            if all(v['exposures'] > 100 for v in metrics['variants'].values()):
                metrics['statistical_significance'] = True
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting A/B test metrics: {e}")
            return {}
    
    def get_funnel_metrics(self, funnel_name: str, date_range: int = 7) -> Dict[str, Any]:
        """Get conversion funnel metrics"""
        try:
            if not redis_client or funnel_name not in self.conversion_funnels:
                return {}
            
            funnel_steps = self.conversion_funnels[funnel_name]
            metrics = {
                'funnel_name': funnel_name,
                'steps': [],
                'overall_conversion': 0
            }
            
            # Get metrics for each step
            for i, step in enumerate(funnel_steps):
                step_count = 0
                
                # Sum up counts for date range
                for days_ago in range(date_range):
                    date = (datetime.utcnow() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                    count = int(redis_client.hget(f'funnel:{funnel_name}:{date}', step) or 0)
                    step_count += count
                
                # Calculate drop-off rate
                if i > 0 and metrics['steps'][i-1]['count'] > 0:
                    conversion_rate = (step_count / metrics['steps'][i-1]['count']) * 100
                else:
                    conversion_rate = 100 if i == 0 else 0
                
                metrics['steps'].append({
                    'name': step,
                    'count': step_count,
                    'conversion_rate': round(conversion_rate, 2)
                })
            
            # Calculate overall conversion
            if metrics['steps'] and metrics['steps'][0]['count'] > 0:
                last_step_count = metrics['steps'][-1]['count']
                first_step_count = metrics['steps'][0]['count']
                metrics['overall_conversion'] = round((last_step_count / first_step_count) * 100, 2)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting funnel metrics: {e}")
            return {}
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for dashboard"""
        try:
            if not redis_client:
                return {}
            
            now = datetime.utcnow()
            today = now.strftime('%Y-%m-%d')
            current_hour = now.strftime('%Y-%m-%d:%H')
            
            metrics = {
                'timestamp': now.isoformat(),
                'daily': {
                    'page_views': int(redis_client.get(f'metrics:{today}:page_views') or 0),
                    'signups': int(redis_client.get(f'metrics:{today}:signups') or 0),
                    'conversions': int(redis_client.get(f'metrics:{today}:conversions') or 0),
                    'revenue': float(redis_client.get(f'metrics:{today}:revenue') or 0)
                },
                'hourly': {
                    'page_views': int(redis_client.get(f'metrics:{current_hour}:page_views') or 0),
                    'signups': int(redis_client.get(f'metrics:{current_hour}:signups') or 0)
                },
                'active_users': redis_client.scard('active_users') or 0,
                'press_pass_remaining': int(redis_client.get('press_pass:daily_remaining') or 0)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {}
    
    def _update_real_time_metrics(self, event_name: str, properties: Dict) -> None:
        """Update real-time metrics in Redis"""
        try:
            if not redis_client:
                return
            
            now = datetime.utcnow()
            today = now.strftime('%Y-%m-%d')
            current_hour = now.strftime('%Y-%m-%d:%H')
            
            # Update event counts
            redis_client.incr(f'metrics:{today}:{event_name}')
            redis_client.incr(f'metrics:{current_hour}:{event_name}')
            
            # Update specific metrics
            if event_name == 'page_view':
                redis_client.incr(f'metrics:{today}:page_views')
                redis_client.incr(f'metrics:{current_hour}:page_views')
            
            elif event_name == 'press_pass_claimed':
                redis_client.incr(f'metrics:{today}:signups')
                redis_client.incr(f'metrics:{current_hour}:signups')
            
            elif event_name.startswith('conversion_'):
                redis_client.incr(f'metrics:{today}:conversions')
                value = properties.get('value', 0)
                if value > 0:
                    redis_client.incrbyfloat(f'metrics:{today}:revenue', value)
            
            # Track active users
            client_id = properties.get('client_id', self._get_client_id())
            redis_client.sadd('active_users', client_id)
            redis_client.expire('active_users', 300)  # 5 minute window
            
        except Exception as e:
            logger.error(f"Error updating real-time metrics: {e}")
    
    def _track_funnel_progress(self, event_name: str, properties: Dict) -> None:
        """Track funnel progress"""
        try:
            if not redis_client:
                return
            
            today = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Check each funnel
            for funnel_name, steps in self.conversion_funnels.items():
                if event_name in steps:
                    redis_client.hincrby(f'funnel:{funnel_name}:{today}', event_name, 1)
                    
                    # Track user's funnel progress
                    client_id = properties.get('client_id', self._get_client_id())
                    step_index = steps.index(event_name)
                    redis_client.hset(f'user_funnel:{client_id}', funnel_name, step_index)
            
        except Exception as e:
            logger.error(f"Error tracking funnel progress: {e}")
    
    def _flush_events(self) -> None:
        """Send queued events to external analytics services"""
        try:
            if not self.event_queue:
                return
            
            # Send to Google Analytics
            if GA_MEASUREMENT_ID and GA_API_SECRET:
                self._send_to_google_analytics(self.event_queue)
            
            # Send to Facebook
            if FB_PIXEL_ID and FB_ACCESS_TOKEN:
                self._send_to_facebook(self.event_queue)
            
            # Send to Mixpanel
            if MIXPANEL_TOKEN:
                self._send_to_mixpanel(self.event_queue)
            
            # Clear queue
            self.event_queue = []
            
        except Exception as e:
            logger.error(f"Error flushing events: {e}")
    
    def _send_to_google_analytics(self, events: List[Dict]) -> None:
        """Send events to Google Analytics 4"""
        try:
            url = f"https://www.google-analytics.com/mp/collect?measurement_id={GA_MEASUREMENT_ID}&api_secret={GA_API_SECRET}"
            
            for event in events:
                payload = {
                    'client_id': event['client_id'],
                    'events': [{
                        'name': event['event'],
                        'params': event['properties']
                    }]
                }
                
                response = requests.post(url, json=payload)
                if response.status_code != 204:
                    logger.warning(f"GA tracking failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error sending to Google Analytics: {e}")
    
    def _get_session_id(self) -> str:
        """Get or create session ID"""
        # In a real implementation, this would use cookies or session storage
        return hashlib.md5(f"{datetime.utcnow().date()}".encode()).hexdigest()[:16]
    
    def _get_client_id(self) -> str:
        """Get or create client ID"""
        # In a real implementation, this would use cookies or device fingerprinting
        return hashlib.md5(f"client_{datetime.utcnow().date()}".encode()).hexdigest()[:16]

# Singleton instance
analytics_tracker = AnalyticsTracker()

# Convenience function
def track_event(event_name: str, properties: Dict[str, Any] = None) -> None:
    """Track an analytics event"""
    analytics_tracker.track_event(event_name, properties)