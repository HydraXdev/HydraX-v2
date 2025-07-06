"""
🎯 Tests for BITTEN Volatility Manager
Ensure no wimpy position reductions - only higher standards
"""

import pytest
from datetime import datetime
import asyncio

from src.bitten_core.volatility_manager import (
    VolatilityManager, VolatilityLevel, VolatilityData
)
from src.bitten_core.volatility_integration import (
    VolatilityIntegration, check_trade_volatility, get_market_briefing
)
from src.bitten_core.fire_modes import FireMode


class TestVolatilityLevel:
    """Test volatility level enum functionality"""
    
    def test_tcs_requirements(self):
        """Test TCS requirement adjustments"""
        base_tcs = 72
        
        assert VolatilityLevel.NORMAL.get_tcs_requirement(base_tcs) == 72
        assert VolatilityLevel.ELEVATED.get_tcs_requirement(base_tcs) == 75
        assert VolatilityLevel.HIGH.get_tcs_requirement(base_tcs) == 80
        assert VolatilityLevel.EXTREME.get_tcs_requirement(base_tcs) == 85
    
    def test_stop_multipliers(self):
        """Test stop loss multipliers"""
        assert VolatilityLevel.NORMAL.get_stop_multiplier() == 1.0
        assert VolatilityLevel.ELEVATED.get_stop_multiplier() == 1.2
        assert VolatilityLevel.HIGH.get_stop_multiplier() == 1.5
        assert VolatilityLevel.EXTREME.get_stop_multiplier() == 2.0
    
    def test_confirmation_required(self):
        """Test confirmation requirements"""
        assert not VolatilityLevel.NORMAL.requires_confirmation()
        assert not VolatilityLevel.ELEVATED.requires_confirmation()
        assert VolatilityLevel.HIGH.requires_confirmation()
        assert VolatilityLevel.EXTREME.requires_confirmation()


class TestVolatilityManager:
    """Test volatility manager functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.manager = VolatilityManager()
    
    def test_calculate_normal_volatility(self):
        """Test normal market conditions"""
        data = VolatilityData(
            atr_current=0.0010,
            atr_average=0.0010,
            atr_percentile=50.0,
            spread_current=1.0,
            spread_normal=1.0,
            recent_gaps=[]
        )
        
        level = self.manager.calculate_volatility_level(data)
        assert level == VolatilityLevel.NORMAL
    
    def test_calculate_elevated_volatility_atr(self):
        """Test elevated volatility from ATR"""
        data = VolatilityData(
            atr_current=0.0013,  # 30% above average
            atr_average=0.0010,
            atr_percentile=65.0,
            spread_current=1.0,
            spread_normal=1.0,
            recent_gaps=[]
        )
        
        level = self.manager.calculate_volatility_level(data)
        assert level == VolatilityLevel.ELEVATED
    
    def test_calculate_high_volatility_spread(self):
        """Test high volatility from spread widening"""
        data = VolatilityData(
            atr_current=0.0010,
            atr_average=0.0010,
            atr_percentile=50.0,
            spread_current=3.5,  # 3.5x normal
            spread_normal=1.0,
            recent_gaps=[]
        )
        
        level = self.manager.calculate_volatility_level(data)
        assert level == VolatilityLevel.HIGH
    
    def test_calculate_extreme_volatility_vix(self):
        """Test extreme volatility from VIX"""
        data = VolatilityData(
            atr_current=0.0010,
            atr_average=0.0010,
            atr_percentile=50.0,
            spread_current=1.0,
            spread_normal=1.0,
            recent_gaps=[],
            vix_level=35.0  # VIX above 30
        )
        
        level = self.manager.calculate_volatility_level(data)
        assert level == VolatilityLevel.EXTREME
    
    def test_high_impact_news_detection(self):
        """Test news event triggers HIGH volatility"""
        data = VolatilityData(
            atr_current=0.0010,
            atr_average=0.0010,
            atr_percentile=50.0,
            spread_current=1.0,
            spread_normal=1.0,
            recent_gaps=[],
            news_events=['FOMC Meeting', 'GDP Release']
        )
        
        level = self.manager.calculate_volatility_level(data)
        assert level == VolatilityLevel.HIGH
    
    def test_gap_detection(self):
        """Test gap detection triggers HIGH volatility"""
        data = VolatilityData(
            atr_current=0.0010,
            atr_average=0.0010,
            atr_percentile=50.0,
            spread_current=1.0,
            spread_normal=1.0,
            recent_gaps=[60.0, 45.0]  # Large gaps
        )
        
        level = self.manager.calculate_volatility_level(data)
        assert level == VolatilityLevel.HIGH
    
    def test_mission_brief_generation(self):
        """Test mission brief for volatile conditions"""
        data = VolatilityData(
            atr_current=0.0016,
            atr_average=0.0010,
            atr_percentile=80.0,
            spread_current=3.5,
            spread_normal=1.0,
            recent_gaps=[],
            vix_level=28.0,
            news_events=['NFP Release']
        )
        
        brief = self.manager.get_mission_brief(
            VolatilityLevel.HIGH, data, 'EURUSD', 72
        )
        
        assert 'VOLATILITY ALERT - HIGH' in brief
        assert 'ATR: 160.0% of normal' in brief
        assert 'Required TCS: 80%' in brief
        assert 'Stop Width: 1.5x normal' in brief
        assert 'NFP Release' in brief
    
    def test_confirmation_message(self):
        """Test confirmation message generation"""
        msg = self.manager.get_confirmation_message(
            VolatilityLevel.HIGH, 'EURUSD', 'BUY'
        )
        
        assert '🚨 HIGH VOLATILITY CONFIRMATION 🚨' in msg
        assert 'BUY on EURUSD' in msg
        assert 'CONFIRM' in msg
        assert 'ABORT' in msg
    
    def test_should_block_trade(self):
        """Test trade blocking logic"""
        # Should block: TCS too low for volatility
        should_block, reason = self.manager.should_block_trade(
            VolatilityLevel.HIGH, 75.0, 'NIBBLER'
        )
        assert should_block
        assert '80%' in reason
        
        # Should allow: TCS meets requirement
        should_block, reason = self.manager.should_block_trade(
            VolatilityLevel.HIGH, 82.0, 'NIBBLER'
        )
        assert not should_block
        assert reason is None
    
    def test_calculate_adjusted_stop(self):
        """Test stop loss adjustment calculation"""
        base_stop = 100.0
        
        adjusted = self.manager.calculate_adjusted_stop(
            base_stop, VolatilityLevel.HIGH
        )
        assert adjusted == 150.0  # 1.5x multiplier
        
        adjusted = self.manager.calculate_adjusted_stop(
            base_stop, VolatilityLevel.EXTREME
        )
        assert adjusted == 200.0  # 2x multiplier


class TestVolatilityIntegration:
    """Test volatility integration with BITTEN core"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.integration = VolatilityIntegration()
    
    @pytest.mark.asyncio
    async def test_check_volatility_requirements(self):
        """Test checking volatility requirements for trade"""
        result = await self.integration.check_volatility_requirements(
            symbol='EURUSD',
            tcs=75.0,
            tier='NIBBLER',
            fire_mode=FireMode.SPRAY
        )
        
        assert 'allowed' in result
        assert 'level' in result
        assert 'adjusted_tcs' in result
        assert 'requires_confirmation' in result
        assert 'stop_multiplier' in result
    
    @pytest.mark.asyncio
    async def test_volatility_caching(self):
        """Test volatility level caching"""
        # First call should calculate
        result1 = await self.integration.check_volatility_requirements(
            'EURUSD', 75.0, 'NIBBLER', FireMode.SPRAY
        )
        
        # Second call should use cache
        result2 = await self.integration.check_volatility_requirements(
            'EURUSD', 75.0, 'NIBBLER', FireMode.SPRAY
        )
        
        # Levels should match
        assert result1['level'] == result2['level']
    
    def test_pending_confirmation_storage(self):
        """Test storing pending confirmations"""
        trade_details = {
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'tcs': 82.0
        }
        
        self.integration.store_pending_confirmation(123, trade_details)
        
        # Should retrieve
        pending = self.integration.get_pending_confirmation(123)
        assert pending == trade_details
        
        # Clear and verify gone
        self.integration.clear_pending_confirmation(123)
        pending = self.integration.get_pending_confirmation(123)
        assert pending is None
    
    @pytest.mark.asyncio
    async def test_process_confirmation_confirm(self):
        """Test processing CONFIRM response"""
        trade_details = {'symbol': 'EURUSD', 'direction': 'BUY'}
        self.integration.store_pending_confirmation(123, trade_details)
        
        result = await self.integration.process_volatility_confirmation(
            123, 'CONFIRM'
        )
        
        assert result['confirmed'] is True
        assert result['trade_details'] == trade_details
        assert 'Executing with adjusted parameters' in result['message']
    
    @pytest.mark.asyncio
    async def test_process_confirmation_abort(self):
        """Test processing ABORT response"""
        self.integration.store_pending_confirmation(123, {'symbol': 'EURUSD'})
        
        result = await self.integration.process_volatility_confirmation(
            123, 'ABORT'
        )
        
        assert result['confirmed'] is False
        assert 'Standing down' in result['message']
    
    def test_adjust_stop_loss(self):
        """Test stop loss adjustment"""
        # Cache a HIGH volatility level
        from datetime import datetime
        self.integration._volatility_cache['EURUSD'] = (
            VolatilityLevel.HIGH, datetime.utcnow()
        )
        
        adjusted, multiplier = self.integration.adjust_stop_loss(100.0, 'EURUSD')
        
        assert adjusted == 150.0  # 1.5x for HIGH
        assert multiplier == 1.5
    
    @pytest.mark.asyncio
    async def test_volatility_briefing(self):
        """Test market volatility briefing generation"""
        briefing = await self.integration.volatility_briefing(
            ['EURUSD', 'GBPUSD', 'USDJPY']
        )
        
        assert '📊 MARKET VOLATILITY BRIEFING' in briefing
        assert 'EURUSD' in briefing or 'All monitored symbols showing NORMAL' in briefing
    
    def test_get_volatility_status(self):
        """Test getting volatility status"""
        # Add some cached data
        self.integration._volatility_cache['EURUSD'] = (
            VolatilityLevel.HIGH, datetime.utcnow()
        )
        
        status = self.integration.get_volatility_status()
        
        assert 'timestamp' in status
        assert 'symbols' in status
        assert 'EURUSD' in status['symbols']
        assert status['symbols']['EURUSD']['level'] == 'HIGH'
        assert status['symbols']['EURUSD']['stop_multiplier'] == 1.5


@pytest.mark.asyncio
async def test_convenience_functions():
    """Test module-level convenience functions"""
    # Test check_trade_volatility
    result = await check_trade_volatility(
        'EURUSD', 75.0, 'NIBBLER', FireMode.SPRAY
    )
    assert 'allowed' in result
    
    # Test get_market_briefing
    briefing = await get_market_briefing(['EURUSD', 'GBPUSD'])
    assert 'MARKET VOLATILITY BRIEFING' in briefing


def test_no_position_size_reduction():
    """Ensure NO position size reduction in volatility"""
    manager = VolatilityManager()
    
    # Check all methods - none should mention position size
    data = VolatilityData(
        atr_current=0.002, atr_average=0.001, atr_percentile=90,
        spread_current=5.0, spread_normal=1.0, recent_gaps=[]
    )
    
    level = VolatilityLevel.EXTREME
    brief = manager.get_mission_brief(level, data, 'EURUSD', 72)
    
    # Should NOT contain any position size reduction language
    assert 'position size' not in brief.lower()
    assert 'reduce' not in brief.lower()
    assert 'smaller' not in brief.lower()
    
    # Should contain our philosophy
    assert 'Stop Width:' in brief  # Wider stops mentioned
    assert 'Required TCS:' in brief  # Higher TCS mentioned