"""
Example Usage of Order Flow Analysis System

Demonstrates how to integrate all components for real-time order flow analysis.
"""

import asyncio
import logging
from datetime import datetime
import json

# Import all components
from .exchange_manager import ExchangeManager, ExchangeConfig, RateLimitConfig
from .order_book_reader import OrderBookReader
from .imbalance_detector import ImbalanceDetector
from .absorption_detector import AbsorptionPatternDetector
from .liquidity_void_detector import LiquidityVoidDetector
from .cumulative_delta import CumulativeDeltaCalculator
from .dark_pool_scanner import DarkPoolActivityScanner
from .order_flow_scorer import OrderFlowScorer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrderFlowAnalysisSystem:
    """Complete order flow analysis system"""
    
    def __init__(self):
        # Initialize components
        self.exchange_manager = ExchangeManager()
        self.order_book_reader = OrderBookReader(self.exchange_manager)
        
        # Initialize detectors
        self.imbalance_detector = ImbalanceDetector(
            levels_to_analyze=20,
            imbalance_threshold=1.5
        )
        
        self.absorption_detector = AbsorptionPatternDetector(
            min_volume_threshold=50.0,
            max_price_movement=0.002,
            min_duration=30.0
        )
        
        self.liquidity_detector = LiquidityVoidDetector(
            min_gap_percentage=0.001,
            min_volume_threshold=10.0,
            levels_to_analyze=50
        )
        
        self.delta_calculator = CumulativeDeltaCalculator(
            bar_period=60,  # 1-minute bars
            lookback_bars=100
        )
        
        self.dark_pool_scanner = DarkPoolActivityScanner(
            min_print_size=50000,  # $50k minimum
            large_print_multiplier=10
        )
        
        self.order_flow_scorer = OrderFlowScorer(
            min_confidence=0.6,
            lookback_periods=20
        )
        
        # State
        self.running = False
        self.tasks = []
    
    async def setup_exchanges(self):
        """Setup exchange connections"""
        
        # Add Binance
        await self.exchange_manager.add_exchange(ExchangeConfig(
            name='binance',
            rate_limits=RateLimitConfig(
                requests_per_second=10,
                requests_per_minute=1200,
                burst_capacity=20
            )
        ))
        
        # Add Kraken
        await self.exchange_manager.add_exchange(ExchangeConfig(
            name='kraken',
            rate_limits=RateLimitConfig(
                requests_per_second=1,
                requests_per_minute=60,
                burst_capacity=5
            )
        ))
        
        logger.info("Exchange connections established")
    
    async def analyze_symbol(self, symbol: str):
        """Main analysis loop for a symbol"""
        
        logger.info(f"Starting analysis for {symbol}")
        
        while self.running:
            try:
                # Get order book snapshot
                order_book = await self.order_book_reader.get_order_book(symbol)
                
                if not order_book:
                    await asyncio.sleep(1)
                    continue
                
                # Get recent trades
                trades = await self.exchange_manager.get_trades(symbol, limit=100)
                
                # Update market price for dark pool scanner
                self.dark_pool_scanner.update_market_price(symbol, order_book.get_mid_price())
                
                # Run all detections
                imbalance = self.imbalance_detector.detect_imbalance(order_book)
                
                absorption = self.absorption_detector.analyze_snapshot(order_book, trades)
                
                liquidity = self.liquidity_detector.analyze_liquidity(order_book)
                
                # Process trades for delta
                self.delta_calculator.process_trades_batch(
                    symbol.split('/')[0],  # Base currency
                    'aggregated',
                    trades
                )
                delta_info = self.delta_calculator.get_current_delta(
                    symbol.split('/')[0],
                    'aggregated'
                )
                
                # Scan for dark pool activity
                dark_prints = self.dark_pool_scanner.scan_for_activity(symbol, trades)
                dark_flow = self.dark_pool_scanner.get_flow_analysis(symbol, '1h')
                
                # Calculate overall score
                score = self.order_flow_scorer.calculate_score(
                    symbol,
                    'aggregated',
                    order_book=order_book,
                    imbalance=imbalance,
                    absorption=absorption if hasattr(absorption, 'pattern_type') else None,
                    liquidity=liquidity,
                    delta_info=delta_info,
                    dark_pool=dark_flow
                )
                
                # Log results
                self._log_analysis_results(symbol, score, imbalance, liquidity, dark_flow)
                
                # Check for alerts
                self._check_alerts(symbol, score)
                
                # Sleep before next iteration
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                await asyncio.sleep(5)
    
    def _log_analysis_results(self, symbol, score, imbalance, liquidity, dark_flow):
        """Log analysis results"""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Analysis Update - {symbol} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*60}")
        
        # Score summary
        logger.info(f"Composite Score: {score.composite_score:.1f} | "
                   f"Signal: {score.signal_strength.value} | "
                   f"Confidence: {score.confidence:.2%}")
        
        # Component scores
        logger.info(f"Component Scores:")
        logger.info(f"  - Imbalance: {score.imbalance_score:.0f}/100")
        logger.info(f"  - Absorption: {score.absorption_score:.0f}/100")
        logger.info(f"  - Liquidity: {score.liquidity_score:.0f}/100")
        logger.info(f"  - Delta: {score.delta_score:.0f}/100")
        logger.info(f"  - Dark Pool: {score.dark_pool_score:.0f}/100")
        
        # Key metrics
        if imbalance:
            logger.info(f"\nImbalance: {imbalance.direction} ({imbalance.strength}) - "
                       f"Ratio: {imbalance.imbalance_ratio:.2f}")
        
        if liquidity:
            logger.info(f"Liquidity Score: {liquidity.liquidity_score:.0f}/100 - "
                       f"Voids: {liquidity.bid_void_count} bid, {liquidity.ask_void_count} ask")
        
        if dark_flow.total_volume > 0:
            logger.info(f"Dark Pool Flow: {dark_flow.flow_score:.1f} - "
                       f"Volume: ${dark_flow.total_volume:,.0f}")
        
        # Insights
        if score.insights:
            logger.info("\nInsights:")
            for insight in score.insights:
                logger.info(f"  • {insight}")
        
        # Warnings
        if score.warnings:
            logger.info("\nWarnings:")
            for warning in score.warnings:
                logger.info(f"  ⚠ {warning}")
    
    def _check_alerts(self, symbol: str, score):
        """Check for alert conditions"""
        
        # Strong signals with high confidence
        if score.confidence > 0.8:
            if score.signal_strength.value in ['strong_buy', 'strong_sell']:
                logger.warning(f"\n🚨 ALERT: Strong {score.signal_strength.value} signal "
                             f"for {symbol} with {score.confidence:.0%} confidence!")
                
                # Get recent opportunities
                opportunities = self.order_flow_scorer.get_recent_opportunities(symbol, 'aggregated', 1)
                if opportunities:
                    opp = opportunities[0]
                    logger.warning(f"   Type: {opp.opportunity_type}")
                    logger.warning(f"   Entry: {opp.entry_price:.2f}")
                    logger.warning(f"   Stop: {opp.stop_loss:.2f}")
                    logger.warning(f"   Targets: {', '.join(f'{tp:.2f}' for tp in opp.take_profit)}")
                    logger.warning(f"   Risk/Reward: {opp.risk_reward_ratio:.2f}")
    
    async def start(self, symbols: list):
        """Start the analysis system"""
        
        logger.info("Starting Order Flow Analysis System...")
        
        # Setup exchanges
        await self.setup_exchanges()
        
        # Subscribe to order book updates
        for symbol in symbols:
            await self.order_book_reader.subscribe(symbol)
        
        self.running = True
        
        # Start analysis tasks for each symbol
        for symbol in symbols:
            task = asyncio.create_task(self.analyze_symbol(symbol))
            self.tasks.append(task)
        
        logger.info(f"Analysis started for {len(symbols)} symbols")
    
    async def stop(self):
        """Stop the analysis system"""
        
        logger.info("Stopping Order Flow Analysis System...")
        
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close connections
        await self.order_book_reader.close()
        await self.exchange_manager.close_all()
        
        logger.info("System stopped")
    
    def get_current_analysis(self, symbol: str) -> dict:
        """Get current analysis state for a symbol"""
        
        # Get latest scores
        scores = self.order_flow_scorer.get_score_history(symbol, 'aggregated', 1)
        if not scores:
            return {'status': 'no_data'}
        
        latest_score = scores[0]
        
        # Get component statistics
        imbalance_stats = self.imbalance_detector.get_statistics(symbol, 'aggregated')
        absorption_stats = self.absorption_detector.get_statistics(symbol, 'aggregated')
        liquidity_stats = self.liquidity_detector.get_statistics(symbol, 'aggregated')
        delta_profile = self.delta_calculator.get_delta_profile(symbol, 'aggregated')
        dark_pool_stats = self.dark_pool_scanner.get_statistics(symbol)
        
        return {
            'timestamp': latest_score.timestamp,
            'symbol': symbol,
            'current_score': latest_score.to_dict(),
            'statistics': {
                'imbalance': imbalance_stats,
                'absorption': absorption_stats,
                'liquidity': liquidity_stats,
                'delta': delta_profile['statistics'] if 'statistics' in delta_profile else {},
                'dark_pool': dark_pool_stats
            },
            'recent_opportunities': [
                opp.to_dict() for opp in 
                self.order_flow_scorer.get_recent_opportunities(symbol, 'aggregated', 5)
            ]
        }


async def main():
    """Example main function"""
    
    # Create analysis system
    system = OrderFlowAnalysisSystem()
    
    # Symbols to analyze
    symbols = ['BTC/USDT', 'ETH/USDT']
    
    try:
        # Start analysis
        await system.start(symbols)
        
        # Run for a while
        await asyncio.sleep(300)  # 5 minutes
        
        # Get final analysis
        for symbol in symbols:
            analysis = system.get_current_analysis(symbol)
            
            print(f"\nFinal Analysis for {symbol}:")
            print(json.dumps(analysis, indent=2, default=str))
        
    finally:
        # Stop system
        await system.stop()


if __name__ == "__main__":
    asyncio.run(main())