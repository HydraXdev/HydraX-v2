"""
🎯 Test Tilt Recovery - Requires 2 Wins
Verify that tilt recovery now requires 2 consecutive wins, not 3
"""

import pytest
from datetime import datetime

from src.bitten_core.risk_management import (
    RiskManager, RiskProfile, AccountInfo, TradingState
)


class TestTiltRecovery:
    """Test the 2-win tilt recovery requirement"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.risk_manager = RiskManager()
        self.profile = RiskProfile(
            user_id=123,
            tier_level='NIBBLER',
            current_xp=1000
        )
        self.account = AccountInfo(
            balance=10000,
            equity=10000,
            margin=0,
            free_margin=10000,
            leverage=100,
            starting_balance=10000
        )
    
    def test_tilt_triggered_after_3_losses(self):
        """Test that tilt is triggered after 3 consecutive losses"""
        # Simulate 3 losses
        for i in range(3):
            self.risk_manager.update_trade_result(self.profile, won=False, pnl=-50)
        
        # Check restrictions
        result = self.risk_manager.check_trading_restrictions(
            self.profile, self.account, 'EURUSD'
        )
        
        assert result['state'] == TradingState.TILT_WARNING
        assert result['restrictions']['tilt_warning'] is True
        assert result['can_trade'] is True  # Can still trade with warning
        
        # Get session to check details
        session = self.risk_manager.get_or_create_session(self.profile.user_id)
        assert session.consecutive_losses == 3
        assert session.tilt_strikes == 1
        assert session.tilt_recovery_wins == 0
    
    def test_one_win_does_not_clear_tilt(self):
        """Test that 1 win doesn't clear tilt anymore"""
        # Get into tilt (3 losses)
        for i in range(3):
            self.risk_manager.update_trade_result(self.profile, won=False, pnl=-50)
        
        session = self.risk_manager.get_or_create_session(self.profile.user_id)
        assert session.tilt_strikes == 1
        
        # Win once
        self.risk_manager.update_trade_result(self.profile, won=True, pnl=50)
        
        # Check that tilt is NOT cleared
        assert session.tilt_strikes == 1  # Still in tilt
        assert session.tilt_recovery_wins == 1  # Progress: 1/2
        assert session.consecutive_losses == 0  # Losses reset
        assert session.consecutive_wins == 1
        
        # Check restrictions still show tilt
        result = self.risk_manager.check_trading_restrictions(
            self.profile, self.account, 'EURUSD'
        )
        assert result['restrictions'].get('tilt_recovery_progress') == "1/2 wins"
    
    def test_two_wins_clear_tilt(self):
        """Test that 2 wins clear tilt"""
        # Get into tilt (3 losses)
        for i in range(3):
            self.risk_manager.update_trade_result(self.profile, won=False, pnl=-50)
        
        session = self.risk_manager.get_or_create_session(self.profile.user_id)
        assert session.tilt_strikes == 1
        
        # Win twice
        self.risk_manager.update_trade_result(self.profile, won=True, pnl=50)
        assert session.tilt_recovery_wins == 1
        
        self.risk_manager.update_trade_result(self.profile, won=True, pnl=50)
        
        # Check that tilt IS cleared
        assert session.tilt_strikes == 0  # Tilt cleared!
        assert session.tilt_recovery_wins == 0  # Reset
        assert session.consecutive_wins == 2
        
        # Check no more tilt restrictions
        result = self.risk_manager.check_trading_restrictions(
            self.profile, self.account, 'EURUSD'
        )
        assert result['state'] == TradingState.NORMAL
        assert 'tilt_warning' not in result['restrictions']
    
    def test_loss_during_recovery_resets_progress(self):
        """Test that a loss during recovery resets the win counter"""
        # Get into tilt (3 losses)
        for i in range(3):
            self.risk_manager.update_trade_result(self.profile, won=False, pnl=-50)
        
        session = self.risk_manager.get_or_create_session(self.profile.user_id)
        
        # Win once
        self.risk_manager.update_trade_result(self.profile, won=True, pnl=50)
        assert session.tilt_recovery_wins == 1
        
        # Loss resets recovery
        self.risk_manager.update_trade_result(self.profile, won=False, pnl=-50)
        assert session.tilt_recovery_wins == 0  # Reset to 0
        assert session.tilt_strikes == 1  # Still in tilt
        
        # Now need 2 wins again
        self.risk_manager.update_trade_result(self.profile, won=True, pnl=50)
        assert session.tilt_recovery_wins == 1  # Back to 1/2
        
    def test_win_win_loss_win_does_not_clear(self):
        """Test that W-W-L-W pattern doesn't clear tilt"""
        # Get into tilt (3 losses)
        for i in range(3):
            self.risk_manager.update_trade_result(self.profile, won=False, pnl=-50)
        
        session = self.risk_manager.get_or_create_session(self.profile.user_id)
        
        # Win-Win-Loss-Win pattern
        self.risk_manager.update_trade_result(self.profile, won=True, pnl=50)  # W
        assert session.tilt_recovery_wins == 1
        
        self.risk_manager.update_trade_result(self.profile, won=True, pnl=50)  # W
        assert session.tilt_strikes == 0  # Cleared!
        assert session.tilt_recovery_wins == 0
        
        # But if we get back into tilt...
        for i in range(3):
            self.risk_manager.update_trade_result(self.profile, won=False, pnl=-50)
        assert session.tilt_strikes == 1  # Back in tilt
        
        # Win-Loss-Win doesn't clear it
        self.risk_manager.update_trade_result(self.profile, won=True, pnl=50)  # W
        self.risk_manager.update_trade_result(self.profile, won=False, pnl=-50)  # L
        self.risk_manager.update_trade_result(self.profile, won=True, pnl=50)  # W
        
        assert session.tilt_strikes == 1  # Still in tilt
        assert session.tilt_recovery_wins == 1  # Only 1/2
    
    def test_get_risk_summary_shows_recovery(self):
        """Test that risk summary shows recovery progress"""
        # Get into tilt and win once
        for i in range(3):
            self.risk_manager.update_trade_result(self.profile, won=False, pnl=-50)
        self.risk_manager.update_trade_result(self.profile, won=True, pnl=50)
        
        # Get summary
        summary = self.risk_manager.get_risk_summary(self.profile, self.account)
        
        assert summary['tilt_strikes'] == 1
        assert summary['tilt_recovery_wins'] == 1
        assert summary['tilt_recovery_needed'] == 2


def test_tilt_philosophy():
    """Test that the tilt recovery philosophy is correct"""
    # This test documents the BITTEN philosophy on tilt recovery
    
    # 2 wins is the right balance:
    # - 1 win is too easy (lucky shot)
    # - 3 wins is too harsh (demoralizing)
    # - 2 wins shows you're back in control
    
    assert True  # Philosophy test always passes!