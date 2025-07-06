"""
News API Configuration Module

This module handles configuration for economic calendar and news API integrations.
"""

import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Provider Configuration
NEWS_API_PROVIDER = os.getenv('NEWS_API_PROVIDER', 'forexfactory')
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')

# Update intervals
NEWS_UPDATE_INTERVAL = int(os.getenv('NEWS_UPDATE_INTERVAL', '1800'))  # 30 minutes default
NEWS_CACHE_DURATION = int(os.getenv('NEWS_CACHE_DURATION', '3600'))   # 1 hour default

# API Endpoints by provider
API_ENDPOINTS = {
    'forexfactory': {
        'base_url': 'https://nfs.faireconomy.media',
        'calendar': '/ff_calendar_thisweek.json',
        'requires_key': False
    },
    'investing': {
        'base_url': 'https://api.investing.com',
        'calendar': '/api/financialdata/calendar/economic',
        'requires_key': True
    },
    'fxstreet': {
        'base_url': 'https://calendar-api.fxstreet.com',
        'calendar': '/en/api/v1/eventDates',
        'requires_key': True
    }
}

# Impact level mappings
IMPACT_MAPPINGS = {
    'forexfactory': {
        'high': ['High', 'HIGH', '3', 'Red'],
        'medium': ['Medium', 'MEDIUM', '2', 'Orange', 'Yellow'],
        'low': ['Low', 'LOW', '1', 'Green']
    },
    'investing': {
        'high': [3, '3', 'High'],
        'medium': [2, '2', 'Medium'],
        'low': [1, '1', 'Low']
    }
}

# Currency filters
MONITORED_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']

# High impact event types to monitor
HIGH_IMPACT_EVENTS = [
    'Non-Farm Payrolls',
    'NFP',
    'Interest Rate Decision',
    'Central Bank Rate',
    'CPI',
    'Consumer Price Index',
    'GDP',
    'Gross Domestic Product',
    'Unemployment Rate',
    'ECB Press Conference',
    'FOMC',
    'Federal Reserve',
    'Bank of England',
    'Bank of Japan',
    'European Central Bank',
    'Retail Sales',
    'PMI',
    'ISM',
    'Employment'
]

# Time buffer settings (minutes)
NEWS_BUFFER_BEFORE = 30  # Stop trading 30 minutes before high impact news
NEWS_BUFFER_AFTER = 30   # Resume trading 30 minutes after high impact news

def get_api_config() -> Dict:
    """Get configuration for the selected news API provider"""
    provider = NEWS_API_PROVIDER.lower()
    
    if provider not in API_ENDPOINTS:
        raise ValueError(f"Unknown news API provider: {provider}")
    
    config = API_ENDPOINTS[provider].copy()
    
    # Add API key if required
    if config.get('requires_key') and not NEWS_API_KEY:
        raise ValueError(f"API key required for {provider} but not provided")
    
    config['api_key'] = NEWS_API_KEY
    config['impact_mapping'] = IMPACT_MAPPINGS.get(provider, IMPACT_MAPPINGS['forexfactory'])
    
    return config

def is_high_impact_event(event_name: str) -> bool:
    """Check if an event is considered high impact based on its name"""
    event_name_upper = event_name.upper()
    return any(keyword.upper() in event_name_upper for keyword in HIGH_IMPACT_EVENTS)

def get_headers() -> Dict[str, str]:
    """Get headers for API requests"""
    headers = {
        'User-Agent': 'HydraX-BITTEN/2.0 (Trading System)',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'DNT': '1'
    }
    
    if NEWS_API_KEY and API_ENDPOINTS.get(NEWS_API_PROVIDER, {}).get('requires_key'):
        # Use custom header instead of Authorization to avoid confusion
        headers['X-API-Key'] = NEWS_API_KEY
    
    return headers