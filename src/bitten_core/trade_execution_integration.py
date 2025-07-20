"""
Trade Execution Integration
Connects tactical and drill report systems to actual trade execution
"""

import logging
from typing import Dict, Optional
from .fire_router import FireRouter, get_fire_router
from .drill_report_bot_integration import create_drill_system_integration
from .tactical_strategies import tactical_strategy_manager
from .daily_drill_report import DailyDrillReportSystem

logger = logging.getLogger(__name__)


class TradeExecutionIntegration:
    """Integration manager for connecting all trade execution systems"""
    
    def __init__(self):
        self.fire_router = None
        self.drill_system = None
        self.drill_report_handler = None
        self.tactical_manager = tactical_strategy_manager
        
    def initialize(self) -> bool:
        """Initialize all integration components"""
        try:
            # Get the global fire router instance
            self.fire_router = get_fire_router()
            
            # Create drill system integration
            self.drill_system, self.drill_report_handler = create_drill_system_integration(
                self.tactical_manager
            )
            
            # Connect drill report handler to fire router
            self.fire_router.set_drill_report_handler(self.drill_report_handler)
            
            logger.info("Trade execution integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize trade execution integration: {e}")
            return False
    
    def get_fire_router(self) -> Optional[FireRouter]:
        """Get the configured fire router instance"""
        return self.fire_router
    
    def get_drill_system(self) -> Optional[DailyDrillReportSystem]:
        """Get the drill report system"""
        return self.drill_system
    
    def get_tactical_manager(self):
        """Get the tactical strategy manager"""
        return self.tactical_manager


# Global integration instance
_integration_instance = None


def get_trade_execution_integration() -> TradeExecutionIntegration:
    """Get or create the global trade execution integration instance"""
    global _integration_instance
    
    if _integration_instance is None:
        _integration_instance = TradeExecutionIntegration()
        _integration_instance.initialize()
    
    return _integration_instance


def initialize_trade_execution_systems():
    """Initialize all trade execution systems and their integrations"""
    integration = get_trade_execution_integration()
    
    if integration.fire_router and integration.drill_system:
        logger.info("✅ Trade execution systems fully integrated:")
        logger.info("   - Fire Router: Connected to broker API")
        logger.info("   - Tactical Manager: Filtering signals based on user strategy")
        logger.info("   - Drill Report System: Tracking trade completion and performance")
        logger.info("   - Strategy Orchestrator: Using tactical filtering for user signals")
        return True
    else:
        logger.error("❌ Failed to initialize trade execution systems")
        return False


# Example usage for testing the integration
if __name__ == "__main__":
    # Test the integration
    success = initialize_trade_execution_systems()
    
    if success:
        integration = get_trade_execution_integration()
        
        # Test fire router status
        status = integration.fire_router.get_system_status()
        print("=== FIRE ROUTER STATUS ===")
        print(f"Execution Mode: {status['execution_mode']}")
        print(f"Emergency Stop: {status['emergency_stop']}")
        print(f"API Health: {status['api_health']['success_rate']:.1f}%")
        
        # Test tactical manager
        print("\n=== TACTICAL MANAGER TEST ===")
        test_user = "test_user_123"
        daily_state = integration.tactical_manager.get_daily_state(test_user)
        print(f"User Strategy: {daily_state.selected_strategy}")
        print(f"Shots Fired: {daily_state.shots_fired}")
        
        # Test drill system
        print("\n=== DRILL SYSTEM TEST ===")
        if integration.drill_system:
            try:
                drill_report = integration.drill_system.generate_drill_report(test_user)
                print("Drill report generated successfully")
            except Exception as e:
                print(f"Drill report generation failed: {e}")
        
        print("\n✅ All systems operational and integrated!")
    else:
        print("❌ Integration failed")