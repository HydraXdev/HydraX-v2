# HydraX Intelligence System v2.0

## Overview

The HydraX Intelligence System is a scalable, modular architecture for ingesting, processing, and analyzing data from multiple sources to generate high-quality trading signals. It's designed to handle real-time data feeds, normalize heterogeneous data formats, and provide intelligent signal generation with advanced caching and monitoring capabilities.

## Architecture

### Core Components

1. **Data Ingestion Layer** (`ingestion/`)
   - Base classes for various data source types (HTTP, WebSocket, Stream)
   - Built-in rate limiting and retry logic
   - Asynchronous data processing with configurable buffers

2. **Data Normalization Layer** (`normalization/`)
   - Standardizes data from different sources into common format
   - Extensible normalizer factory for custom data types
   - Data quality scoring and validation

3. **Caching System** (`cache/`)
   - Multi-tier caching (Memory, Redis, Hybrid)
   - Configurable TTL for different data types
   - LRU eviction and memory management

4. **Monitoring & Logging** (`monitoring/`)
   - Structured JSON logging
   - Performance metrics collection
   - Prometheus and JSON exporters
   - Circuit breaker pattern for fault tolerance

5. **Configuration Management** (`config/`)
   - Centralized configuration with environment variable support
   - Encrypted storage for sensitive data (API keys)
   - Runtime configuration validation

6. **Intelligence Orchestrator** (`core/orchestrator.py`)
   - Manages component lifecycle
   - Coordinates data flow between components
   - Health monitoring and graceful shutdown

## Quick Start

### 1. Configuration

Create a `.env` file in the project root:

```bash
# API Keys
API_KEY_MARKET_DATA=your_market_data_key
API_KEY_NEWS_FEED=your_news_api_key
API_KEY_SOCIAL_MEDIA=your_social_media_key

# Environment
INTELLIGENCE_ENV=development
INTELLIGENCE_DEBUG=false
INTELLIGENCE_ENCRYPTION_KEY=your_encryption_key
```

### 2. Basic Usage

```python
from src.intelligence import IntelligenceOrchestrator
from src.intelligence.ingestion.base import HTTPDataIngester
from src.intelligence.core.base import SignalGenerator

# Create orchestrator
orchestrator = IntelligenceOrchestrator(config_path="config/intelligence")

# Initialize
await orchestrator.initialize()

# Add data sources
await orchestrator.add_data_source(
    name="market_data",
    source_type="http",
    config={
        "endpoint": "https://api.example.com/market",
        "poll_interval": 60,
        "headers": {"Authorization": "Bearer token"}
    }
)

# Add signal generator
generator = YourSignalGenerator("my_generator")
await orchestrator.add_signal_generator(generator)

# Start system
await orchestrator.start()

# Get signals
signals = await orchestrator.get_signals()

# Graceful shutdown
await orchestrator.shutdown()
```

### 3. Creating Custom Components

#### Custom Data Ingester

```python
from src.intelligence.ingestion.base import BaseDataIngester

class CustomIngester(BaseDataIngester):
    async def _initialize(self):
        # Custom initialization
        pass
        
    async def _ingestion_loop(self):
        while self._running:
            # Fetch data from your source
            data = await self.fetch_data()
            
            # Ingest data
            await self.ingest_data(data)
            
            # Wait before next fetch
            await asyncio.sleep(60)
```

#### Custom Normalizer

```python
from src.intelligence.normalization.normalizer import DataNormalizer

class CustomNormalizer(DataNormalizer):
    def _get_field_mappings(self):
        return {
            'symbol': 'ticker',
            'timestamp': 'time',
            'value': 'price'
        }
        
    async def _enrich_single(self, data):
        # Add custom enrichment
        data.metadata['custom_field'] = 'custom_value'
        return data
```

#### Custom Signal Generator

```python
from src.intelligence.core.base import SignalGenerator, Signal, SignalType

class CustomSignalGenerator(SignalGenerator):
    async def analyze(self, data):
        signals = []
        
        # Your signal generation logic
        if self.should_generate_signal(data):
            signal = Signal(
                type=SignalType.BUY,
                symbol=data.symbol,
                strength=SignalStrength.STRONG,
                confidence=0.85
            )
            signals.append(signal)
            
        return signals
```

## Configuration Reference

### Main Configuration (`config.yaml`)

- `system`: System-wide settings
- `cache`: Cache backend configuration
- `monitoring`: Logging and metrics settings
- `processing`: Data processing parameters
- `performance`: Performance tuning options

### API Configuration (`apis.yaml`)

Define external API configurations with:
- API keys and secrets
- Base URLs
- Rate limits
- Retry settings

### Data Sources (`data_sources.yaml`)

Configure data sources with:
- Source type (http, websocket, etc.)
- Connection parameters
- Update intervals
- Priority levels

## Monitoring & Debugging

### Health Check

```python
health = await orchestrator.get_system_health()
print(f"System status: {health['running']}")
print(f"Active components: {health['total_components']}")
```

### Metrics

Access metrics through the metrics monitor:

```python
if orchestrator.metrics_monitor:
    stats = orchestrator.metrics_monitor.collector.get_counter_value("signals_generated")
    print(f"Signals generated: {stats}")
```

### Logging

Logs are structured in JSON format and saved to `logs/intelligence/`:
- `intelligence.log`: All logs
- `intelligence_errors.log`: Error logs only

## Performance Optimization

1. **Caching Strategy**
   - Use hybrid cache for best performance
   - Configure appropriate TTLs for different data types
   - Monitor cache hit rates

2. **Batch Processing**
   - Adjust `batch_size` based on data volume
   - Use appropriate buffer sizes

3. **Concurrency**
   - Configure `max_workers` for parallel processing
   - Use rate limiting to avoid overwhelming APIs

4. **Memory Management**
   - Set appropriate cache size limits
   - Enable log rotation
   - Monitor memory usage

## Security

1. **API Key Management**
   - Use environment variables for sensitive data
   - Enable encryption for stored configurations
   - Rotate keys regularly

2. **Data Protection**
   - All sensitive configuration data is encrypted at rest
   - Use secure connections (HTTPS/WSS)

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Check API credentials
   - Verify network connectivity
   - Review rate limits

2. **Memory Issues**
   - Reduce cache size
   - Decrease batch sizes
   - Enable more aggressive eviction

3. **Performance Issues**
   - Check metrics for bottlenecks
   - Review log files for errors
   - Optimize data pipeline routes

## Development

### Running Tests

```bash
# Run all tests
pytest src/intelligence/tests/

# Run with coverage
pytest --cov=src.intelligence src/intelligence/tests/
```

### Adding New Features

1. Create component in appropriate module
2. Register with orchestrator
3. Add configuration
4. Write tests
5. Update documentation

## License

This system is part of the HydraX v2 project. See main project license for details.