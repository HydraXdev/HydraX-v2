"""
Deployment Script for Daily Drill Report System
Integrates drill reports with existing BITTEN infrastructure
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.bitten_core.daily_drill_report import DailyDrillReportSystem, DailyTradingStats
from src.bitten_core.drill_report_bot_integration import register_drill_report_handlers, create_drill_system_integration
from src.bitten_core.tactical_strategies import tactical_strategy_manager

logger = logging.getLogger(__name__)


class DrillReportDeployment:
    """Complete drill report system deployment"""
    
    def __init__(self):
        self.drill_system = None
        self.integration_handler = None
        self.is_deployed = False
    
    def deploy_system(self, telegram_bot_app=None):
        """Deploy the complete drill report system"""
        
        try:
            logger.info("🚀 Deploying Daily Drill Report System...")
            
            # 1. Initialize drill report system
            self.drill_system = DailyDrillReportSystem()
            logger.info("✅ Drill report database initialized")
            
            # 2. Create tactical system integration
            drill_system, trade_completion_handler = create_drill_system_integration(tactical_strategy_manager)
            self.drill_system = drill_system
            
            # Store the handler for use in tactical system
            self.trade_completion_handler = trade_completion_handler
            logger.info("✅ Tactical system integration created")
            
            # 3. Register with Telegram bot if provided
            if telegram_bot_app:
                self.integration_handler = register_drill_report_handlers(telegram_bot_app, self.drill_system)
                logger.info("✅ Telegram bot handlers registered")
            
            # 4. Test system with sample data
            self._test_system()
            logger.info("✅ System testing completed")
            
            self.is_deployed = True
            logger.info("🎯 Daily Drill Report System DEPLOYED successfully!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            return False
    
    def _test_system(self):
        """Test drill report system with sample data"""
        
        # Test data
        test_stats = DailyTradingStats(
            user_id="deployment_test",
            date="2025-07-22",
            trades_taken=3,
            wins=2,
            losses=1,
            net_pnl_percent=4.2,
            strategy_used="FIRST_BLOOD",
            xp_gained=8,
            shots_remaining=1,
            max_shots=4,
            consecutive_wins=2,
            consecutive_losses=0,
            best_trade_pnl=2.8,
            worst_trade_pnl=-0.6,
            total_pips=31
        )
        
        # Test recording stats
        success = self.drill_system.record_daily_stats("deployment_test", test_stats)
        assert success, "Failed to record test stats"
        
        # Test report generation
        drill_message = self.drill_system.generate_drill_report("deployment_test")
        assert drill_message.header, "Failed to generate drill message"
        
        # Test Telegram formatting
        telegram_report = self.drill_system.format_telegram_report(drill_message, "deployment_test")
        assert len(telegram_report) > 0, "Failed to format Telegram report"
        
        logger.info("📊 Sample drill report generated successfully")
    
    def get_integration_guide(self) -> str:
        """Get integration guide for existing systems"""
        
        return """
🎯 DRILL REPORT SYSTEM - INTEGRATION GUIDE

## 1. TACTICAL SYSTEM INTEGRATION

In your tactical strategy manager, add this call when trades complete:

```python
# After trade execution in tactical_strategies.py
def fire_shot(self, user_id: str, signal_data: Dict, trade_result: str):
    # ... existing code ...
    
    # ADD THIS: Record trade for drill report
    if hasattr(self, 'drill_report_handler'):
        trade_info = {
            'pnl_percent': calculated_pnl,
            'xp_gained': xp_awarded,
            'pips': pip_result
        }
        self.drill_report_handler(user_id, trade_info)
    
    return result
```

## 2. TELEGRAM BOT INTEGRATION

In your main bot file (bitten_production_bot.py):

```python
from src.bitten_core.drill_report_bot_integration import register_drill_report_handlers
from src.bitten_core.daily_drill_report import DailyDrillReportSystem

# After bot initialization
drill_system = DailyDrillReportSystem()
register_drill_report_handlers(application, drill_system)
```

## 3. SCHEDULER SETUP

Add to your scheduler or cron:

```bash
# Daily drill reports at 6 PM
0 18 * * * python3 -c "from src.bitten_core.drill_report_bot_integration import DrillReportBotIntegration; DrillReportBotIntegration.send_daily_reports()"
```

## 4. NEW BOT COMMANDS

Users can now use:
- `/drill` - Get today's drill report
- `/weekly` - Get weekly performance summary  
- `/drill_settings` - Configure report preferences

## 5. DATABASE TABLES CREATED

- `daily_trading_stats` - Performance tracking
- `drill_report_history` - Report history
- `drill_preferences` - User preferences

## 6. AUTOMATIC FEATURES

✅ Daily 6 PM reports (configurable)
✅ Performance-based drill sergeant tone
✅ Achievement integration
✅ Weekly summaries
✅ Comeback detection
✅ Tactical strategy integration

🎖️ DRILL SERGEANT READY FOR DUTY! 🪖
"""
    
    def show_sample_reports(self):
        """Show sample drill reports for different scenarios"""
        
        scenarios = [
            {
                "name": "OUTSTANDING DAY",
                "stats": DailyTradingStats(
                    user_id="sample", date="2025-07-22", trades_taken=5, wins=5, losses=0,
                    net_pnl_percent=8.4, strategy_used="TACTICAL_COMMAND", xp_gained=15,
                    shots_remaining=1, max_shots=6, consecutive_wins=5, consecutive_losses=0,
                    best_trade_pnl=2.1, worst_trade_pnl=1.2, total_pips=67
                )
            },
            {
                "name": "ROUGH DAY", 
                "stats": DailyTradingStats(
                    user_id="sample", date="2025-07-22", trades_taken=4, wins=1, losses=3,
                    net_pnl_percent=-3.2, strategy_used="LONE_WOLF", xp_gained=2,
                    shots_remaining=0, max_shots=4, consecutive_wins=0, consecutive_losses=2,
                    best_trade_pnl=1.8, worst_trade_pnl=-2.1, total_pips=-23
                )
            },
            {
                "name": "NO TRADES",
                "stats": None  # This will trigger no-action report
            }
        ]
        
        print("=" * 60)
        print("🎯 SAMPLE DRILL REPORTS")
        print("=" * 60)
        
        for scenario in scenarios:
            print(f"\n{'=' * 20} {scenario['name']} {'=' * 20}")
            
            if scenario['stats']:
                self.drill_system.record_daily_stats("sample", scenario['stats'])
                drill_message = self.drill_system.generate_drill_report("sample")
            else:
                # No trades scenario
                drill_message = self.drill_system.generate_drill_report("sample_no_trades")
            
            report = self.drill_system.format_telegram_report(drill_message, "sample")
            print(report)
            print()


def main():
    """Main deployment function"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🪖 BITTEN DAILY DRILL REPORT SYSTEM")
    print("=" * 50)
    
    # Deploy system
    deployment = DrillReportDeployment()
    success = deployment.deploy_system()
    
    if success:
        print("\n✅ DEPLOYMENT SUCCESSFUL!")
        print("\n📋 Integration Guide:")
        print(deployment.get_integration_guide())
        
        print("\n📊 Sample Reports:")
        deployment.show_sample_reports()
        
        print("\n🎯 NEXT STEPS:")
        print("1. Integrate with tactical_strategies.py (add trade completion calls)")
        print("2. Register handlers in bitten_production_bot.py")
        print("3. Set up 6 PM daily scheduler")
        print("4. Test with real users")
        print("\n🪖 DRILL SERGEANT REPORTING FOR DUTY! 🎖️")
        
    else:
        print("\n❌ DEPLOYMENT FAILED!")
        print("Check logs for details.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)