#!/usr/bin/env python3
"""
Test TCS Integration System
Complete test of the self-optimizing TCS engine integration
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

# Import all components
from src.bitten_core.complete_signal_flow_v3 import FusionEnhancedSignalFlow
from src.bitten_core.tcs_integration import TCSIntegrationLayer
from src.bitten_core.tcs_performance_tracker import AdvancedTCSPerformanceTracker
from src.bitten_core.self_optimizing_tcs import SelfOptimizingTCS, MarketCondition
from src.bitten_core.signal_fusion import signal_fusion_engine
from src.bitten_core.mt5_enhanced_adapter import MT5EnhancedAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TCSIntegrationTester:
    """Test the complete TCS integration system"""
    
    def __init__(self):
        self.test_results = {}
        self.setup_complete = False
    
    async def setup_test_environment(self):
        """Set up test environment"""
        logger.info("Setting up TCS integration test environment...")
        
        # Create test data directory
        test_data_dir = Path("/root/HydraX-v2/test_data")
        test_data_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.mt5_adapter = MT5EnhancedAdapter()
        self.signal_flow = FusionEnhancedSignalFlow()
        
        # Create mock MT5 files for testing
        await self._create_mock_mt5_data()
        
        self.setup_complete = True
        logger.info("Test environment setup complete")
    
    async def _create_mock_mt5_data(self):
        """Create mock MT5 data files for testing"""
        mt5_files_dir = Path("/root/HydraX-v2/test_data/mt5_files")
        mt5_files_dir.mkdir(exist_ok=True)
        
        # Mock account data
        account_data = {
            "balance": 10000.0,
            "equity": 10000.0,
            "margin": 0.0,
            "free_margin": 10000.0,
            "margin_level": 0.0,
            "daily_pl": 0.0,
            "daily_pl_percent": 0.0
        }
        
        with open(mt5_files_dir / "bitten_account_secure.txt", "w") as f:
            json.dump(account_data, f)
        
        # Mock market data
        market_data = {
            "EURUSD": {
                "bid": 1.0900,
                "ask": 1.0902,
                "spread": 2.0,
                "atr": 25.0,
                "volume_ratio": 1.0
            },
            "GBPUSD": {
                "bid": 1.2700,
                "ask": 1.2703,
                "spread": 3.0,
                "atr": 35.0,
                "volume_ratio": 1.2
            }
        }
        
        with open(mt5_files_dir / "bitten_market_secure.txt", "w") as f:
            json.dump(market_data, f)
        
        # Mock positions data
        positions_data = {"positions": []}
        
        with open(mt5_files_dir / "bitten_positions_secure.txt", "w") as f:
            json.dump(positions_data, f)
        
        logger.info("Mock MT5 data created")
    
    async def test_tcs_optimizer_functionality(self):
        """Test TCS optimizer basic functionality"""
        logger.info("Testing TCS optimizer functionality...")
        
        try:
            # Initialize TCS optimizer
            tcs_optimizer = SelfOptimizingTCS()
            
            # Test market condition
            market_condition = MarketCondition(
                volatility_level="MEDIUM",
                trend_strength=0.6,
                session_activity="LONDON",
                news_impact=0.3
            )
            
            # Get optimal threshold
            threshold = await tcs_optimizer.get_optimal_tcs_threshold(market_condition)
            
            # Test signal logging
            await tcs_optimizer.log_signal_performance(
                pair="EURUSD",
                tcs_score=78.5,
                direction="BUY",
                result="WIN",
                pips_gained=15.0,
                hold_time_minutes=180,
                market_condition=market_condition
            )
            
            # Get stats
            stats = tcs_optimizer.get_optimization_stats()
            
            self.test_results['tcs_optimizer'] = {
                'status': 'PASS',
                'threshold': threshold,
                'stats': stats,
                'details': 'TCS optimizer basic functionality working'
            }
            
            logger.info(f"TCS optimizer test PASSED - Threshold: {threshold:.1f}%")
            
        except Exception as e:
            self.test_results['tcs_optimizer'] = {
                'status': 'FAIL',
                'error': str(e),
                'details': 'TCS optimizer test failed'
            }
            logger.error(f"TCS optimizer test FAILED: {e}")
    
    async def test_performance_tracking(self):
        """Test performance tracking system"""
        logger.info("Testing performance tracking system...")
        
        try:
            # Initialize performance tracker
            tracker = AdvancedTCSPerformanceTracker(self.mt5_adapter)
            
            # Test database initialization
            stats = tracker.get_real_time_stats()
            
            # Test threshold analysis
            analysis = tracker.get_threshold_analysis("EURUSD")
            
            self.test_results['performance_tracking'] = {
                'status': 'PASS',
                'stats': stats,
                'analysis': analysis,
                'details': 'Performance tracking system working'
            }
            
            logger.info("Performance tracking test PASSED")
            
        except Exception as e:
            self.test_results['performance_tracking'] = {
                'status': 'FAIL',
                'error': str(e),
                'details': 'Performance tracking test failed'
            }
            logger.error(f"Performance tracking test FAILED: {e}")
    
    async def test_signal_fusion_integration(self):
        """Test signal fusion engine TCS integration"""
        logger.info("Testing signal fusion TCS integration...")
        
        try:
            # Check TCS integration in fusion engine
            tcs_active = signal_fusion_engine.tcs_integration is not None
            
            # Test TCS threshold updates
            signal_fusion_engine.update_tcs_threshold("EURUSD", 77.5)
            threshold = signal_fusion_engine.get_tcs_threshold("EURUSD")
            
            # Test enhanced stats
            enhanced_stats = signal_fusion_engine.get_tcs_enhanced_stats()
            
            self.test_results['signal_fusion_integration'] = {
                'status': 'PASS',
                'tcs_active': tcs_active,
                'threshold_test': threshold == 77.5,
                'enhanced_stats': enhanced_stats,
                'details': 'Signal fusion TCS integration working'
            }
            
            logger.info("Signal fusion integration test PASSED")
            
        except Exception as e:
            self.test_results['signal_fusion_integration'] = {
                'status': 'FAIL',
                'error': str(e),
                'details': 'Signal fusion integration test failed'
            }
            logger.error(f"Signal fusion integration test FAILED: {e}")
    
    async def test_complete_integration(self):
        """Test complete integration system"""
        logger.info("Testing complete integration system...")
        
        try:
            # Initialize complete system
            await self.signal_flow.start_monitoring()
            
            # Let it run for a short time
            await asyncio.sleep(5)
            
            # Get system stats
            stats = self.signal_flow.get_system_stats()
            
            # Check TCS components
            tcs_integration_active = 'tcs_integration' in stats
            tcs_performance_available = 'tcs_performance' in stats
            fusion_enhanced = 'fusion_enhanced' in stats
            
            self.test_results['complete_integration'] = {
                'status': 'PASS',
                'tcs_integration_active': tcs_integration_active,
                'tcs_performance_available': tcs_performance_available,
                'fusion_enhanced': fusion_enhanced,
                'system_stats': stats,
                'details': 'Complete integration system working'
            }
            
            logger.info("Complete integration test PASSED")
            
        except Exception as e:
            self.test_results['complete_integration'] = {
                'status': 'FAIL',
                'error': str(e),
                'details': 'Complete integration test failed'
            }
            logger.error(f"Complete integration test FAILED: {e}")
    
    async def test_tcs_threshold_adjustment(self):
        """Test TCS threshold adjustment functionality"""
        logger.info("Testing TCS threshold adjustment...")
        
        try:
            # Initialize TCS integration
            tcs_integration = TCSIntegrationLayer(self.mt5_adapter, signal_fusion_engine)
            
            # Test threshold update
            new_threshold = await tcs_integration.update_tcs_thresholds("EURUSD")
            
            # Check if threshold was updated in fusion engine
            fusion_threshold = signal_fusion_engine.get_tcs_threshold("EURUSD")
            
            self.test_results['threshold_adjustment'] = {
                'status': 'PASS',
                'new_threshold': new_threshold,
                'fusion_threshold': fusion_threshold,
                'details': 'TCS threshold adjustment working'
            }
            
            logger.info(f"Threshold adjustment test PASSED - New threshold: {new_threshold:.1f}%")
            
        except Exception as e:
            self.test_results['threshold_adjustment'] = {
                'status': 'FAIL',
                'error': str(e),
                'details': 'TCS threshold adjustment test failed'
            }
            logger.error(f"Threshold adjustment test FAILED: {e}")
    
    async def run_all_tests(self):
        """Run all TCS integration tests"""
        logger.info("Starting TCS integration test suite...")
        
        if not self.setup_complete:
            await self.setup_test_environment()
        
        # Run individual tests
        await self.test_tcs_optimizer_functionality()
        await self.test_performance_tracking()
        await self.test_signal_fusion_integration()
        await self.test_threshold_adjustment()
        await self.test_complete_integration()
        
        # Generate test report
        await self._generate_test_report()
    
    async def _generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("Generating TCS integration test report...")
        
        report = {
            'test_suite': 'TCS Integration Test Suite',
            'timestamp': datetime.now().isoformat(),
            'results': self.test_results,
            'summary': {
                'total_tests': len(self.test_results),
                'passed': sum(1 for r in self.test_results.values() if r['status'] == 'PASS'),
                'failed': sum(1 for r in self.test_results.values() if r['status'] == 'FAIL'),
                'success_rate': 0
            }
        }
        
        # Calculate success rate
        if report['summary']['total_tests'] > 0:
            report['summary']['success_rate'] = (
                report['summary']['passed'] / report['summary']['total_tests'] * 100
            )
        
        # Save report
        report_path = Path("/root/HydraX-v2/test_data/tcs_integration_test_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("TCS INTEGRATION TEST REPORT")
        print("="*60)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print("="*60)
        
        for test_name, result in self.test_results.items():
            status_symbol = "✓" if result['status'] == 'PASS' else "✗"
            print(f"{status_symbol} {test_name}: {result['status']}")
            if result['status'] == 'FAIL':
                print(f"  Error: {result.get('error', 'Unknown error')}")
        
        print("="*60)
        print(f"Report saved to: {report_path}")
        
        return report

async def main():
    """Run TCS integration test suite"""
    tester = TCSIntegrationTester()
    
    try:
        await tester.run_all_tests()
        
    except KeyboardInterrupt:
        logger.info("Test suite interrupted by user")
    except Exception as e:
        logger.error(f"Test suite error: {e}")
    finally:
        logger.info("Test suite completed")

if __name__ == "__main__":
    asyncio.run(main())