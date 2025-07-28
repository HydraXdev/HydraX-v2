"""
BITTEN Integration Module - Seamlessly integrate CITADEL with existing infrastructure

This module provides the integration layer between CITADEL Shield System and
the existing BITTEN signal generation and distribution infrastructure.
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import asyncio
import json

from .citadel_analyzer import CitadelAnalyzer, get_citadel_analyzer

logger = logging.getLogger(__name__)


class CitadelBittenIntegration:
    """
    Integration layer for CITADEL Shield System with BITTEN infrastructure.
    
    This class handles:
    - Signal interception from VENOM v7
    - Market data preparation
    - Shield analysis coordination
    - Result integration with BittenProductionBot
    - WebApp/HUD data provision
    """
    
    def __init__(self):
        self.citadel = get_citadel_analyzer()
        self.signal_queue = asyncio.Queue()
        self.result_callbacks = []
        
        # Market data cache for efficiency
        self.market_data_cache = {}
        self.cache_ttl = 60  # 1 minute
        
        logger.info("CITADEL-BITTEN Integration initialized")
    
    def enhance_venom_signal(self, venom_signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance VENOM v7 signal with CITADEL shield analysis.
        
        This method should be called from apex_venom_v7_unfiltered.py
        after signal generation.
        
        Args:
            venom_signal: Raw signal from VENOM v7
            
        Returns:
            Enhanced signal with shield analysis
        """
        try:
            # Prepare signal format for CITADEL
            citadel_signal = self._prepare_signal_for_citadel(venom_signal)
            
            # Get or fetch market data
            pair = citadel_signal['pair']
            market_data = self._get_market_data(pair)
            
            # Perform CITADEL analysis
            shield_analysis = self.citadel.analyze_signal(
                citadel_signal,
                market_data
            )
            
            # Merge shield analysis with original signal
            enhanced_signal = {
                **venom_signal,
                'citadel_shield': {
                    'score': shield_analysis['shield_score'],
                    'classification': shield_analysis['classification'],
                    'emoji': shield_analysis['emoji'],
                    'label': shield_analysis['label'],
                    'explanation': shield_analysis['explanation'],
                    'recommendation': shield_analysis['recommendation'],
                    'risk_factors': shield_analysis.get('risk_factors', []),
                    'quality_factors': shield_analysis.get('quality_factors', [])
                }
            }
            
            # Trigger callbacks for real-time updates
            self._trigger_callbacks(enhanced_signal)
            
            return enhanced_signal
            
        except Exception as e:
            logger.error(f"Failed to enhance signal with CITADEL: {str(e)}")
            # Return original signal if enhancement fails
            return venom_signal
    
    def format_mission_with_shield(self, signal: Dict[str, Any], 
                                 existing_mission: str) -> str:
        """
        Enhance existing mission briefing with shield analysis.
        
        This should be called from BittenProductionBot.generate_mission()
        
        Args:
            signal: Signal with citadel_shield data
            existing_mission: Current mission briefing text
            
        Returns:
            Enhanced mission briefing
        """
        shield_data = signal.get('citadel_shield', {})
        
        if not shield_data:
            return existing_mission
        
        # Add shield section to mission
        shield_section = f"\n\n{shield_data['emoji']} **CITADEL SHIELD ANALYSIS**\n"
        shield_section += f"Protection Score: {shield_data['score']}/10\n"
        shield_section += f"Status: {shield_data['label']}\n"
        
        # Add key insights
        if shield_data.get('explanation'):
            shield_section += f"\n_{shield_data['explanation']}_"
        
        # Add recommendation if not approved
        if shield_data['classification'] != 'SHIELD_APPROVED':
            shield_section += f"\n\n💡 {shield_data.get('recommendation', 'Exercise caution')}"
        
        return existing_mission + shield_section
    
    def get_hud_shield_data(self, signal_id: str) -> Dict[str, Any]:
        """
        Get shield data formatted for WebApp HUD display.
        
        Args:
            signal_id: Signal identifier
            
        Returns:
            Shield data for HUD
        """
        # Try to get from recent analyses
        insight = self.citadel.get_shield_insight(signal_id)
        
        return {
            'shield_available': bool(insight),
            'insight_preview': insight[:200] + '...' if len(insight) > 200 else insight,
            'tap_for_details': True
        }
    
    def register_shield_callback(self, callback):
        """
        Register callback for real-time shield updates.
        
        Args:
            callback: Function to call with enhanced signals
        """
        self.result_callbacks.append(callback)
    
    async def process_signal_stream(self, signal_generator):
        """
        Process stream of signals with CITADEL enhancement.
        
        Args:
            signal_generator: Async generator yielding signals
        """
        async for signal in signal_generator:
            enhanced = self.enhance_venom_signal(signal)
            await self.signal_queue.put(enhanced)
    
    def log_fire_execution(self, signal_id: str, user_id: int, 
                          executed: bool) -> None:
        """
        Log whether user executed trade based on shield recommendation.
        
        Args:
            signal_id: Signal identifier
            user_id: User who made the decision
            executed: Whether trade was executed
        """
        # This will be called when outcome is known
        # For now, just track the decision
        logger.info(f"User {user_id} {'executed' if executed else 'skipped'} "
                   f"signal {signal_id}")
    
    def _prepare_signal_for_citadel(self, venom_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Convert VENOM signal format to CITADEL format."""
        return {
            'signal_id': venom_signal.get('signal_id'),
            'pair': venom_signal.get('symbol', venom_signal.get('pair')),
            'direction': venom_signal.get('direction'),
            'entry_price': float(venom_signal.get('entry', 0)),
            'sl': float(venom_signal.get('stop_loss', venom_signal.get('sl', 0))),
            'tp': float(venom_signal.get('take_profit', venom_signal.get('tp', 0))),
            'signal_type': venom_signal.get('signal_type', 'UNKNOWN')
        }
    
    def _get_market_data(self, pair: str) -> Dict[str, Any]:
        """
        Get market data for pair.
        
        In production, this would fetch from MT5 or market data provider.
        """
        # Check cache first
        cache_key = f"{pair}_{datetime.now().minute}"
        if cache_key in self.market_data_cache:
            return self.market_data_cache[cache_key]
        
        # In production, fetch real market data
        # For now, return mock data structure
        market_data = {
            'recent_candles': self._fetch_recent_candles(pair),
            'timeframes': self._fetch_timeframe_data(pair),
            'recent_high': 0,
            'recent_low': 0,
            'atr': 0,
            'atr_history': []
        }
        
        # Cache it
        self.market_data_cache[cache_key] = market_data
        
        # Clean old cache entries
        if len(self.market_data_cache) > 50:
            self.market_data_cache.clear()
        
        return market_data
    
    def _fetch_recent_candles(self, pair: str) -> List[Dict]:
        """Fetch recent candles - implement with actual data source."""
        # This would connect to MT5 or data provider
        # Returning empty for now
        return []
    
    def _fetch_timeframe_data(self, pair: str) -> Dict[str, Dict]:
        """Fetch multi-timeframe data - implement with actual data source."""
        # This would fetch M5, M15, H1, H4 data
        # Returning empty for now
        return {}
    
    def _trigger_callbacks(self, enhanced_signal: Dict[str, Any]):
        """Trigger registered callbacks with enhanced signal."""
        for callback in self.result_callbacks:
            try:
                callback(enhanced_signal)
            except Exception as e:
                logger.error(f"Callback error: {str(e)}")


# Integration functions for easy patching into existing code

def patch_venom_signal_generation():
    """
    Patch function to add to apex_venom_v7_unfiltered.py
    
    Add this after signal generation:
    ```python
    from citadel_core.bitten_integration import enhance_signal_with_citadel
    
    # After generating signal
    signal = self.generate_venom_signal(pair, timestamp)
    signal = enhance_signal_with_citadel(signal)  # Add this line
    ```
    """
    pass


def patch_bitten_bot_mission():
    """
    Patch function to add to bitten_production_bot.py
    
    In generate_mission method:
    ```python
    from citadel_core.bitten_integration import format_mission_with_citadel
    
    # After creating mission text
    mission_text = self._format_mission_briefing(signal)
    mission_text = format_mission_with_citadel(signal, mission_text)  # Add this line
    ```
    """
    pass


def patch_webapp_hud():
    """
    Patch function to add to webapp_server_optimized.py
    
    In HUD endpoint:
    ```python
    from citadel_core.bitten_integration import get_citadel_shield_data
    
    # Add shield data to response
    shield_data = get_citadel_shield_data(signal_id)
    response['shield'] = shield_data
    ```
    """
    pass


# Singleton integration instance
_integration_instance = None

def get_integration() -> CitadelBittenIntegration:
    """Get singleton integration instance."""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = CitadelBittenIntegration()
    return _integration_instance


# Convenience functions for patching

def enhance_signal_with_citadel(signal: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance signal with CITADEL analysis."""
    integration = get_integration()
    return integration.enhance_venom_signal(signal)


def format_mission_with_citadel(signal: Dict[str, Any], mission: str) -> str:
    """Add CITADEL shield to mission briefing."""
    integration = get_integration()
    return integration.format_mission_with_shield(signal, mission)


def get_citadel_shield_data(signal_id: str) -> Dict[str, Any]:
    """Get shield data for HUD."""
    integration = get_integration()
    return integration.get_hud_shield_data(signal_id)


# Example integration code
if __name__ == "__main__":
    # Example of how to integrate with existing signal
    
    # Mock VENOM signal
    venom_signal = {
        'signal_id': 'VENOM_UNFILTERED_EURUSD_000123',
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'signal_type': 'RAPID_ASSAULT',
        'confidence': 89.5,
        'quality': 'platinum',
        'entry': 1.0850,
        'stop_loss': 1.0820,
        'take_profit': 1.0910,
        'target_pips': 60,
        'stop_pips': 30,
        'risk_reward': 2.0
    }
    
    # Enhance with CITADEL
    enhanced = enhance_signal_with_citadel(venom_signal)
    
    print("=== ENHANCED SIGNAL ===")
    print(json.dumps(enhanced['citadel_shield'], indent=2))
    
    # Format mission
    original_mission = "📍 EURUSD BUY @ 1.0850\n🎯 TP: 60 pips | 🛑 SL: 30 pips"
    enhanced_mission = format_mission_with_citadel(enhanced, original_mission)
    
    print("\n=== ENHANCED MISSION ===")
    print(enhanced_mission)