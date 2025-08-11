#!/usr/bin/env python3
"""
BITTEN Crypto Data Fusion Engine v1.0
=====================================

Multi-source data fusion system for crypto signals that integrates:
- Twitter/X sentiment analysis
- Whale Alert transaction monitoring  
- CoinGecko news & market data
- Multi-broker price validation
- On-chain metrics analysis

Integrates with Elite Guard signal generation via ZMQ architecture.
All scores normalized to 0-100 scale for ML feature integration.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import zmq
import zmq.asyncio
from dataclasses import dataclass, asdict
import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np

# Import our specialized modules
from crypto_sentiment_analyzer import CryptoSentimentAnalyzer
from whale_alert_monitor import WhaleAlertMonitor
from coingecko_integration import CoinGeckoIntegration
from multi_source_validator import MultiSourceValidator


@dataclass
class CryptoDataFusion:
    """Consolidated crypto market intelligence data"""
    timestamp: float
    symbol: str
    
    # Sentiment Scores (0-100)
    twitter_sentiment: float = 0.0
    twitter_volume_score: float = 0.0
    musk_influence_score: float = 0.0
    social_momentum: float = 0.0
    
    # Whale Activity Scores (0-100)
    whale_activity_score: float = 0.0
    large_tx_frequency: float = 0.0
    whale_direction_bias: float = 50.0  # 0=sell, 50=neutral, 100=buy
    
    # News & Market Data (0-100)
    news_sentiment: float = 50.0
    fear_greed_index: float = 50.0
    market_cap_momentum: float = 50.0
    volume_anomaly_score: float = 0.0
    
    # Price Validation (0-100)
    price_consensus_score: float = 0.0
    spread_quality_score: float = 0.0
    manipulation_risk: float = 0.0
    execution_quality: float = 0.0
    
    # On-Chain Metrics (0-100)
    network_activity: float = 50.0
    exchange_flow_score: float = 50.0
    holder_behavior: float = 50.0
    network_health: float = 50.0
    
    # Composite Scores
    overall_bullish_score: float = 50.0
    data_confidence: float = 0.0
    signal_strength: float = 0.0


class CryptoDataFusionEngine:
    """
    Main engine for multi-source crypto data fusion
    Integrates with Elite Guard via ZMQ for enhanced signal generation
    """
    
    def __init__(self, config_path: str = "crypto_fusion_config.json"):
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)
        
        # ZMQ Context and sockets
        self.zmq_context = zmq.asyncio.Context()
        self.data_publisher = None
        self.command_subscriber = None
        
        # Data source modules
        self.sentiment_analyzer = None
        self.whale_monitor = None
        self.coingecko = None
        self.price_validator = None
        
        # Threading and async management
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.running = False
        self.data_cache = {}
        self.last_update = {}
        
        # Crypto symbols to monitor
        self.crypto_symbols = ['BTCUSD', 'ETHUSD', 'DOGEUSD', 'XRPUSD', 'ADAUSD']
        
        # Rate limiting
        self.rate_limits = {
            'twitter': {'requests': 0, 'reset_time': time.time() + 900},  # 15 min
            'whale_alert': {'requests': 0, 'reset_time': time.time() + 3600},  # 1 hour
            'coingecko': {'requests': 0, 'reset_time': time.time() + 60},  # 1 min
        }
        
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        logger = logging.getLogger('CryptoDataFusion')
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler('/root/HydraX-v2/logs/crypto_fusion.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration with fallback defaults"""
        default_config = {
            "zmq_ports": {
                "data_publisher": 5561,
                "command_subscriber": 5562
            },
            "api_keys": {
                "twitter_bearer_token": "",
                "whale_alert_api_key": "",
                "coingecko_api_key": ""
            },
            "update_intervals": {
                "sentiment": 300,      # 5 minutes
                "whale_alerts": 600,   # 10 minutes
                "news": 900,          # 15 minutes
                "price_validation": 60 # 1 minute
            },
            "cache_ttl": 300,
            "rate_limits": {
                "twitter_per_15min": 100,
                "whale_alert_per_hour": 500,
                "coingecko_per_minute": 50
            }
        }
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            self.logger.warning(f"Config file {config_path} not found, using defaults")
            return default_config
    
    async def initialize(self):
        """Initialize all data source modules and ZMQ connections"""
        try:
            self.logger.info("Initializing Crypto Data Fusion Engine...")
            
            # Initialize ZMQ sockets
            await self._setup_zmq()
            
            # Initialize data source modules
            await self._initialize_data_sources()
            
            self.logger.info("Crypto Data Fusion Engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            raise
    
    async def _setup_zmq(self):
        """Setup ZMQ publisher and subscriber sockets"""
        try:
            # Publisher for sending fused data to Elite Guard
            self.data_publisher = self.zmq_context.socket(zmq.PUB)
            pub_port = self.config['zmq_ports']['data_publisher']
            self.data_publisher.bind(f"tcp://*:{pub_port}")
            
            # Subscriber for receiving commands
            self.command_subscriber = self.zmq_context.socket(zmq.SUB)
            sub_port = self.config['zmq_ports']['command_subscriber']
            self.command_subscriber.connect(f"tcp://localhost:{sub_port}")
            self.command_subscriber.setsockopt(zmq.SUBSCRIBE, b"CRYPTO_FUSION_CMD")
            
            self.logger.info(f"ZMQ setup complete - Publisher: {pub_port}, Subscriber: {sub_port}")
            
        except Exception as e:
            self.logger.error(f"ZMQ setup failed: {e}")
            raise
    
    async def _initialize_data_sources(self):
        """Initialize all data source modules"""
        try:
            # Twitter/X Sentiment Analyzer
            self.sentiment_analyzer = CryptoSentimentAnalyzer(
                bearer_token=self.config['api_keys']['twitter_bearer_token'],
                rate_limit=self.config['rate_limits']['twitter_per_15min']
            )
            await self.sentiment_analyzer.initialize()
            
            # Whale Alert Monitor
            self.whale_monitor = WhaleAlertMonitor(
                api_key=self.config['api_keys']['whale_alert_api_key'],
                rate_limit=self.config['rate_limits']['whale_alert_per_hour']
            )
            await self.whale_monitor.initialize()
            
            # CoinGecko Integration
            self.coingecko = CoinGeckoIntegration(
                api_key=self.config['api_keys'].get('coingecko_api_key'),
                rate_limit=self.config['rate_limits']['coingecko_per_minute']
            )
            await self.coingecko.initialize()
            
            # Multi-Source Price Validator
            self.price_validator = MultiSourceValidator()
            await self.price_validator.initialize()
            
            self.logger.info("All data source modules initialized")
            
        except Exception as e:
            self.logger.error(f"Data source initialization failed: {e}")
            raise
    
    async def start_fusion_engine(self):
        """Start the main fusion engine loop"""
        self.running = True
        self.logger.info("Starting Crypto Data Fusion Engine...")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._data_collection_loop()),
            asyncio.create_task(self._fusion_processing_loop()),
            asyncio.create_task(self._command_handler_loop()),
            asyncio.create_task(self._health_monitor_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Fusion engine error: {e}")
            self.running = False
            raise
    
    async def _data_collection_loop(self):
        """Main data collection loop for all sources"""
        while self.running:
            try:
                collection_tasks = []
                
                for symbol in self.crypto_symbols:
                    # Check if we need to update each data source
                    if self._should_update('sentiment', symbol):
                        collection_tasks.append(
                            self._collect_sentiment_data(symbol)
                        )
                    
                    if self._should_update('whale_alerts', symbol):
                        collection_tasks.append(
                            self._collect_whale_data(symbol)
                        )
                    
                    if self._should_update('news', symbol):
                        collection_tasks.append(
                            self._collect_news_data(symbol)
                        )
                    
                    if self._should_update('price_validation', symbol):
                        collection_tasks.append(
                            self._collect_price_validation(symbol)
                        )
                
                # Execute all collection tasks concurrently
                if collection_tasks:
                    await asyncio.gather(*collection_tasks, return_exceptions=True)
                
                await asyncio.sleep(30)  # 30 second collection cycle
                
            except Exception as e:
                self.logger.error(f"Data collection error: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    def _should_update(self, data_type: str, symbol: str) -> bool:
        """Check if data source needs updating based on intervals"""
        key = f"{data_type}_{symbol}"
        last_update = self.last_update.get(key, 0)
        interval = self.config['update_intervals'][data_type]
        
        return time.time() - last_update > interval
    
    async def _collect_sentiment_data(self, symbol: str):
        """Collect Twitter/X sentiment data"""
        try:
            if not self._check_rate_limit('twitter'):
                return
            
            # Map crypto symbols to search terms
            search_terms = self._get_search_terms(symbol)
            
            sentiment_data = await self.sentiment_analyzer.analyze_crypto_sentiment(
                symbol=symbol,
                search_terms=search_terms
            )
            
            if sentiment_data:
                self._update_cache('sentiment', symbol, sentiment_data)
                self.last_update[f"sentiment_{symbol}"] = time.time()
                
        except Exception as e:
            self.logger.error(f"Sentiment collection error for {symbol}: {e}")
    
    async def _collect_whale_data(self, symbol: str):
        """Collect whale transaction data"""
        try:
            if not self._check_rate_limit('whale_alert'):
                return
            
            whale_data = await self.whale_monitor.get_whale_activity(symbol)
            
            if whale_data:
                self._update_cache('whale', symbol, whale_data)
                self.last_update[f"whale_alerts_{symbol}"] = time.time()
                
        except Exception as e:
            self.logger.error(f"Whale data collection error for {symbol}: {e}")
    
    async def _collect_news_data(self, symbol: str):
        """Collect news and market data"""
        try:
            if not self._check_rate_limit('coingecko'):
                return
            
            news_data = await self.coingecko.get_comprehensive_data(symbol)
            
            if news_data:
                self._update_cache('news', symbol, news_data)
                self.last_update[f"news_{symbol}"] = time.time()
                
        except Exception as e:
            self.logger.error(f"News data collection error for {symbol}: {e}")
    
    async def _collect_price_validation(self, symbol: str):
        """Collect multi-source price validation"""
        try:
            validation_data = await self.price_validator.validate_prices(symbol)
            
            if validation_data:
                self._update_cache('price_validation', symbol, validation_data)
                self.last_update[f"price_validation_{symbol}"] = time.time()
                
        except Exception as e:
            self.logger.error(f"Price validation error for {symbol}: {e}")
    
    def _get_search_terms(self, symbol: str) -> List[str]:
        """Get Twitter search terms for each crypto symbol"""
        term_map = {
            'BTCUSD': ['Bitcoin', 'BTC', '$BTC', 'Elon Musk crypto', 'Bitcoin pump'],
            'ETHUSD': ['Ethereum', 'ETH', '$ETH', 'Ethereum news', 'ETH price'],
            'DOGEUSD': ['Dogecoin', 'DOGE', '$DOGE', 'Elon Musk DOGE', 'Doge pump'],
            'XRPUSD': ['Ripple', 'XRP', '$XRP', 'XRP news', 'Ripple SEC'],
            'ADAUSD': ['Cardano', 'ADA', '$ADA', 'Cardano news', 'ADA price']
        }
        return term_map.get(symbol, [symbol])
    
    def _check_rate_limit(self, source: str) -> bool:
        """Check if we're within rate limits for a data source"""
        limit_info = self.rate_limits.get(source)
        if not limit_info:
            return True
        
        current_time = time.time()
        
        # Reset counter if time window passed
        if current_time > limit_info['reset_time']:
            limit_info['requests'] = 0
            # Set next reset time based on source
            if source == 'twitter':
                limit_info['reset_time'] = current_time + 900  # 15 min
            elif source == 'whale_alert':
                limit_info['reset_time'] = current_time + 3600  # 1 hour
            elif source == 'coingecko':
                limit_info['reset_time'] = current_time + 60  # 1 min
        
        # Check if under limit
        max_requests = self.config['rate_limits'].get(f"{source}_per_15min", 100)
        if source == 'whale_alert':
            max_requests = self.config['rate_limits'].get(f"{source}_per_hour", 500)
        elif source == 'coingecko':
            max_requests = self.config['rate_limits'].get(f"{source}_per_minute", 50)
        
        if limit_info['requests'] >= max_requests:
            return False
        
        limit_info['requests'] += 1
        return True
    
    def _update_cache(self, data_type: str, symbol: str, data: Dict):
        """Update data cache with timestamp"""
        cache_key = f"{data_type}_{symbol}"
        self.data_cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    async def _fusion_processing_loop(self):
        """Main loop for processing and fusing all data sources"""
        while self.running:
            try:
                for symbol in self.crypto_symbols:
                    # Fuse all available data for this symbol
                    fused_data = await self._fuse_symbol_data(symbol)
                    
                    if fused_data:
                        # Publish fused data via ZMQ
                        await self._publish_fused_data(fused_data)
                
                await asyncio.sleep(60)  # Process every minute
                
            except Exception as e:
                self.logger.error(f"Fusion processing error: {e}")
                await asyncio.sleep(60)
    
    async def _fuse_symbol_data(self, symbol: str) -> Optional[CryptoDataFusion]:
        """Fuse all available data sources for a symbol"""
        try:
            # Get cached data for all sources
            sentiment_data = self._get_cached_data('sentiment', symbol)
            whale_data = self._get_cached_data('whale', symbol)
            news_data = self._get_cached_data('news', symbol)
            price_data = self._get_cached_data('price_validation', symbol)
            
            # Create fusion object
            fusion = CryptoDataFusion(
                timestamp=time.time(),
                symbol=symbol
            )
            
            # Fuse sentiment data
            if sentiment_data:
                fusion.twitter_sentiment = sentiment_data.get('sentiment_score', 0)
                fusion.twitter_volume_score = sentiment_data.get('volume_score', 0)
                fusion.musk_influence_score = sentiment_data.get('musk_influence', 0)
                fusion.social_momentum = sentiment_data.get('momentum_score', 0)
            
            # Fuse whale data
            if whale_data:
                fusion.whale_activity_score = whale_data.get('activity_score', 0)
                fusion.large_tx_frequency = whale_data.get('tx_frequency', 0)
                fusion.whale_direction_bias = whale_data.get('direction_bias', 50)
            
            # Fuse news and market data
            if news_data:
                fusion.news_sentiment = news_data.get('news_sentiment', 50)
                fusion.fear_greed_index = news_data.get('fear_greed', 50)
                fusion.market_cap_momentum = news_data.get('market_momentum', 50)
                fusion.volume_anomaly_score = news_data.get('volume_anomaly', 0)
            
            # Fuse price validation data
            if price_data:
                fusion.price_consensus_score = price_data.get('consensus_score', 0)
                fusion.spread_quality_score = price_data.get('spread_quality', 0)
                fusion.manipulation_risk = price_data.get('manipulation_risk', 0)
                fusion.execution_quality = price_data.get('execution_quality', 0)
            
            # Calculate composite scores
            fusion = self._calculate_composite_scores(fusion)
            
            return fusion
            
        except Exception as e:
            self.logger.error(f"Data fusion error for {symbol}: {e}")
            return None
    
    def _get_cached_data(self, data_type: str, symbol: str) -> Optional[Dict]:
        """Get cached data if still valid"""
        cache_key = f"{data_type}_{symbol}"
        cached = self.data_cache.get(cache_key)
        
        if not cached:
            return None
        
        # Check if data is still valid
        age = time.time() - cached['timestamp']
        if age > self.config['cache_ttl']:
            return None
        
        return cached['data']
    
    def _calculate_composite_scores(self, fusion: CryptoDataFusion) -> CryptoDataFusion:
        """Calculate composite scores from all data sources"""
        
        # Overall bullish score (weighted average)
        bullish_components = [
            (fusion.twitter_sentiment, 0.15),
            (fusion.social_momentum, 0.10),
            (fusion.whale_direction_bias, 0.20),
            (fusion.news_sentiment, 0.15),
            (100 - fusion.fear_greed_index if fusion.fear_greed_index > 50 else fusion.fear_greed_index, 0.10),
            (fusion.market_cap_momentum, 0.10),
            (fusion.price_consensus_score, 0.15),
            (100 - fusion.manipulation_risk, 0.05)
        ]
        
        weighted_sum = sum(score * weight for score, weight in bullish_components)
        fusion.overall_bullish_score = min(max(weighted_sum, 0), 100)
        
        # Data confidence (based on data availability and quality)
        confidence_factors = []
        if fusion.twitter_sentiment > 0:
            confidence_factors.append(fusion.twitter_volume_score / 100)
        if fusion.whale_activity_score > 0:
            confidence_factors.append(0.8)
        if fusion.news_sentiment != 50:
            confidence_factors.append(0.7)
        if fusion.price_consensus_score > 0:
            confidence_factors.append(fusion.price_consensus_score / 100)
        
        fusion.data_confidence = (sum(confidence_factors) / len(confidence_factors) * 100) if confidence_factors else 0
        
        # Signal strength (combination of bullish score and confidence)
        if fusion.data_confidence > 60:
            if fusion.overall_bullish_score > 75:
                fusion.signal_strength = 90
            elif fusion.overall_bullish_score > 60:
                fusion.signal_strength = 75
            elif fusion.overall_bullish_score < 25:
                fusion.signal_strength = 80  # Strong bearish signal
            elif fusion.overall_bullish_score < 40:
                fusion.signal_strength = 65  # Moderate bearish signal
            else:
                fusion.signal_strength = 30  # Neutral/weak signal
        else:
            fusion.signal_strength = fusion.data_confidence * 0.5  # Low confidence = low signal
        
        return fusion
    
    async def _publish_fused_data(self, fusion: CryptoDataFusion):
        """Publish fused data via ZMQ to Elite Guard"""
        try:
            message = {
                'type': 'CRYPTO_FUSION_DATA',
                'timestamp': fusion.timestamp,
                'data': asdict(fusion)
            }
            
            await self.data_publisher.send_string(json.dumps(message))
            
            # Log significant signals
            if fusion.signal_strength > 70:
                self.logger.info(
                    f"Strong {fusion.symbol} signal: "
                    f"Bullish={fusion.overall_bullish_score:.1f}, "
                    f"Confidence={fusion.data_confidence:.1f}, "
                    f"Strength={fusion.signal_strength:.1f}"
                )
                
        except Exception as e:
            self.logger.error(f"Failed to publish fused data: {e}")
    
    async def _command_handler_loop(self):
        """Handle incoming commands via ZMQ"""
        while self.running:
            try:
                # Check for commands with timeout
                if await self.command_subscriber.poll(timeout=1000):
                    message = await self.command_subscriber.recv_string()
                    await self._process_command(message)
                    
            except Exception as e:
                self.logger.error(f"Command handler error: {e}")
                await asyncio.sleep(1)
    
    async def _process_command(self, message: str):
        """Process incoming commands"""
        try:
            if message.startswith("CRYPTO_FUSION_CMD"):
                cmd_data = json.loads(message[18:])  # Remove prefix
                
                if cmd_data.get('command') == 'get_status':
                    await self._send_status_response()
                elif cmd_data.get('command') == 'force_update':
                    symbol = cmd_data.get('symbol', 'ALL')
                    await self._force_data_update(symbol)
                    
        except Exception as e:
            self.logger.error(f"Command processing error: {e}")
    
    async def _send_status_response(self):
        """Send system status response"""
        status = {
            'type': 'CRYPTO_FUSION_STATUS',
            'timestamp': time.time(),
            'running': self.running,
            'symbols_monitored': len(self.crypto_symbols),
            'cache_entries': len(self.data_cache),
            'data_sources': {
                'sentiment': self.sentiment_analyzer is not None,
                'whale_alert': self.whale_monitor is not None,
                'coingecko': self.coingecko is not None,
                'price_validator': self.price_validator is not None
            }
        }
        
        await self.data_publisher.send_string(json.dumps(status))
    
    async def _force_data_update(self, symbol: str):
        """Force immediate data update for symbol(s)"""
        symbols = [symbol] if symbol != 'ALL' else self.crypto_symbols
        
        for sym in symbols:
            # Reset last update times to force refresh
            for data_type in ['sentiment', 'whale_alerts', 'news', 'price_validation']:
                self.last_update[f"{data_type}_{sym}"] = 0
    
    async def _health_monitor_loop(self):
        """Monitor system health and performance"""
        while self.running:
            try:
                # Check data source health
                health_status = await self._check_system_health()
                
                # Log health summary every 5 minutes
                if int(time.time()) % 300 == 0:
                    self.logger.info(f"System health: {health_status}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(60)
    
    async def _check_system_health(self) -> Dict:
        """Check health of all system components"""
        health = {
            'overall': 'healthy',
            'components': {},
            'cache_size': len(self.data_cache),
            'uptime': time.time() - getattr(self, 'start_time', time.time())
        }
        
        # Check each data source
        if self.sentiment_analyzer:
            health['components']['sentiment'] = await self.sentiment_analyzer.health_check()
        
        if self.whale_monitor:
            health['components']['whale_alert'] = await self.whale_monitor.health_check()
        
        if self.coingecko:
            health['components']['coingecko'] = await self.coingecko.health_check()
        
        if self.price_validator:
            health['components']['price_validator'] = await self.price_validator.health_check()
        
        # Determine overall health
        component_statuses = [comp.get('status', 'error') for comp in health['components'].values()]
        if 'error' in component_statuses:
            health['overall'] = 'degraded'
        elif 'warning' in component_statuses:
            health['overall'] = 'warning'
        
        return health
    
    async def shutdown(self):
        """Graceful shutdown of the fusion engine"""
        self.logger.info("Shutting down Crypto Data Fusion Engine...")
        self.running = False
        
        # Close ZMQ sockets
        if self.data_publisher:
            self.data_publisher.close()
        if self.command_subscriber:
            self.command_subscriber.close()
        
        # Shutdown data sources
        if self.sentiment_analyzer:
            await self.sentiment_analyzer.shutdown()
        if self.whale_monitor:
            await self.whale_monitor.shutdown()
        if self.coingecko:
            await self.coingecko.shutdown()
        if self.price_validator:
            await self.price_validator.shutdown()
        
        # Close thread pool
        self.executor.shutdown(wait=True)
        
        # Terminate ZMQ context
        self.zmq_context.term()
        
        self.logger.info("Crypto Data Fusion Engine shutdown complete")


# === EXCHANGE DATA HELPERS ===

from typing import Dict
from crypto_consensus import compute_consensus
import time

def top_of_book(exchange_manager, symbol:str) -> Dict[str,dict]:
    """
    Return {venue: {'bid':..., 'ask':..., 'mid':..., 'spread_bps':..., 'depth5bps_usd':...}}
    Implement using exchange_manager websocket snapshots; fallback to REST if needed.
    """
    quotes = {}
    for venue in exchange_manager.connected():
        q = exchange_manager.best_quote(venue, symbol)  # implement in manager
        if not q: continue
        bid, ask = q["bid"], q["ask"]
        mid = (bid + ask)/2.0
        spread_bps = (ask - bid)/mid * 10000.0
        depth = q.get("depth5bps_usd", 0.0)
        quotes[venue] = {"bid":bid,"ask":ask,"mid":mid,"spread_bps":spread_bps,"depth5bps_usd":depth}
    return quotes

def order_book_imbalance(imbalance_detector, venue:str, symbol:str) -> float:
    # Return ratio bid_depth/ask_depth near top; implement in imbalance_detector
    return imbalance_detector.top_imbalance(venue, symbol) or 1.0

def consensus_snapshot(exchange_manager, symbol:str):
    quotes = top_of_book(exchange_manager, symbol)
    cons = compute_consensus(quotes)
    return cons, quotes


async def main():
    """Main entry point for the fusion engine"""
    engine = CryptoDataFusionEngine()
    
    try:
        await engine.initialize()
        engine.start_time = time.time()
        await engine.start_fusion_engine()
    except KeyboardInterrupt:
        print("\nReceived shutdown signal...")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        await engine.shutdown()


if __name__ == "__main__":
    # Ensure logs directory exists
    import os
    os.makedirs('/root/HydraX-v2/logs', exist_ok=True)
    
    # Run the fusion engine
    asyncio.run(main())