#!/usr/bin/env python3
"""
Example usage of the HydraX Intelligence System
Demonstrates how to set up and use the intelligence components
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

from src.intelligence import (
    IntelligenceOrchestrator,
    IntelligenceComponent,
    Signal,
    SignalType,
    SignalStrength
)
from src.intelligence.core.base import SignalGenerator
from src.intelligence.ingestion.base import HTTPDataIngester
from src.intelligence.normalization.normalizer import NormalizedData


# Example custom signal generator
class ExampleSignalGenerator(SignalGenerator):
    """Example signal generator that creates signals from normalized data"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.data_buffer = []
        
    async def initialize(self) -> None:
        """Initialize the generator"""
        self.logger.info(f"Initializing {self.name}")
        
    async def start(self) -> None:
        """Start the generator"""
        self._running = True
        self.logger.info(f"Started {self.name}")
        
    async def stop(self) -> None:
        """Stop the generator"""
        self._running = False
        self.logger.info(f"Stopped {self.name}")
        
    async def process(self, data: Any) -> Any:
        """Process incoming data"""
        # Store data for analysis
        if isinstance(data, list):
            self.data_buffer.extend(data)
        else:
            self.data_buffer.append(data)
            
        # Keep buffer size manageable
        if len(self.data_buffer) > 1000:
            self.data_buffer = self.data_buffer[-1000:]
            
        return data
        
    async def analyze(self, data: Any = None) -> List[Signal]:
        """Analyze data and generate signals"""
        signals = []
        
        # Example: Generate signal based on recent data
        if len(self.data_buffer) >= 10:
            recent_data = self.data_buffer[-10:]
            
            # Simple example: look for price movements
            for item in recent_data:
                if isinstance(item, NormalizedData) and item.value:
                    # Example signal generation logic
                    if isinstance(item.value, dict) and 'price' in item.value:
                        price = item.value['price']
                        
                        # Generate buy signal if price is "low" (example only)
                        if price < 1.1000:  # Example threshold
                            signal = Signal(
                                type=SignalType.BUY,
                                strength=SignalStrength.STRONG,
                                symbol=item.symbol,
                                source=self.name,
                                confidence=0.75,
                                metadata={
                                    'price': price,
                                    'reason': 'Price below threshold'
                                }
                            )
                            signals.append(signal)
                            
        return signals
        
    async def filter_signals(self, signals: List[Signal]) -> List[Signal]:
        """Filter signals based on criteria"""
        # Example: filter out weak signals
        return [s for s in signals if s.strength.value >= SignalStrength.NEUTRAL.value]
        
    async def rank_signals(self, signals: List[Signal]) -> List[Signal]:
        """Rank signals by importance"""
        # Sort by confidence and strength
        return sorted(
            signals,
            key=lambda s: (s.confidence, s.strength.value),
            reverse=True
        )


async def main():
    """Main example function"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create orchestrator
    orchestrator = IntelligenceOrchestrator(config_path="config/intelligence")
    
    try:
        # Initialize orchestrator
        print("Initializing Intelligence System...")
        await orchestrator.initialize()
        
        # Add a mock data source
        print("Adding data sources...")
        await orchestrator.add_data_source(
            name="mock_market_data",
            source_type="http",
            config={
                "endpoint": "https://api.example.com/market",  # Replace with real endpoint
                "poll_interval": 30,
                "headers": {"Authorization": "Bearer YOUR_TOKEN"},
                "required_fields": ["symbol", "price", "timestamp"]
            }
        )
        
        # Add custom signal generator
        print("Adding signal generator...")
        generator = ExampleSignalGenerator("example_generator")
        await orchestrator.add_signal_generator(generator)
        
        # Start the system
        print("Starting Intelligence System...")
        await orchestrator.start()
        
        # Let it run for a while
        print("System running. Press Ctrl+C to stop.")
        
        # Periodically check for signals
        for i in range(10):  # Run for 10 iterations
            await asyncio.sleep(10)  # Wait 10 seconds
            
            # Get current signals
            signals = await orchestrator.get_signals()
            
            if signals:
                print(f"\n[{datetime.now()}] Found {len(signals)} signals:")
                for signal in signals[:5]:  # Show top 5
                    print(f"  - {signal.type.name} {signal.symbol} "
                          f"(strength: {signal.strength.name}, "
                          f"confidence: {signal.confidence:.2f})")
            else:
                print(f"\n[{datetime.now()}] No signals generated yet.")
                
            # Get system health
            health = await orchestrator.get_system_health()
            active_components = len([c for c in health['components'] if c['running']])
            print(f"System Health: {active_components}/{health['total_components']} components active")
            
            # Get cache stats
            if orchestrator.cache_manager:
                cache_stats = orchestrator.cache_manager.get_stats()
                print(f"Cache Stats: Hit rate: {cache_stats.get('hit_rate', 0):.1f}%")
                
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Graceful shutdown
        print("Shutting down Intelligence System...")
        await orchestrator.shutdown()
        print("Shutdown complete.")


# Example of using the system with context manager
async def example_with_context_manager():
    """Example using context manager for automatic lifecycle management"""
    
    async with IntelligenceOrchestrator(config_path="config/intelligence").managed_lifecycle() as orchestrator:
        # Add components
        await orchestrator.add_data_source(
            name="test_source",
            source_type="http",
            config={"endpoint": "https://api.example.com/data"}
        )
        
        # System is automatically started
        # Do work here...
        signals = await orchestrator.get_signals()
        print(f"Generated {len(signals)} signals")
        
    # System is automatically shut down when exiting context


if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())
    
    # Uncomment to run context manager example
    # asyncio.run(example_with_context_manager())