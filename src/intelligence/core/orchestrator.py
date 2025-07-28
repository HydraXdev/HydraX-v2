"""
Intelligence System Orchestrator
Coordinates all intelligence components and manages data flow
"""

import asyncio
from typing import Dict, List, Optional, Any, Set, Type
from datetime import datetime
from collections import defaultdict
import signal
from contextlib import asynccontextmanager

from .base import (
    IntelligenceComponent, 
    DataSource, 
    Signal, 
    DataIngestionComponent,
    SignalGenerator,
    IntelligenceError
)
from ..config.manager import ConfigManager
from ..cache.cache_manager import CacheManager
from ..monitoring.logger import LoggerManager, IntelligenceLogger
from ..monitoring.metrics import MetricsMonitor, PrometheusExporter, JSONExporter
from ..ingestion.base import BaseDataIngester
from ..normalization.normalizer import DataNormalizer, NormalizerFactory

class ComponentRegistry:
    """Registry for intelligence components"""
    
    def __init__(self):
        self._components: Dict[str, IntelligenceComponent] = {}
        self._component_types: Dict[Type, List[str]] = defaultdict(list)
        
    def register(self, component: IntelligenceComponent) -> None:
        """Register a component"""
        name = component.name
        if name in self._components:
            raise ValueError(f"Component {name} already registered")
            
        self._components[name] = component
        self._component_types[type(component)].append(name)
        
    def unregister(self, name: str) -> None:
        """Unregister a component"""
        if name in self._components:
            component = self._components.pop(name)
            # Remove from type registry
            for comp_type, names in self._component_types.items():
                if name in names:
                    names.remove(name)
                    
    def get(self, name: str) -> Optional[IntelligenceComponent]:
        """Get component by name"""
        return self._components.get(name)
        
    def get_by_type(self, component_type: Type) -> List[IntelligenceComponent]:
        """Get all components of a specific type"""
        names = self._component_types.get(component_type, [])
        return [self._components[name] for name in names if name in self._components]
        
    def get_all(self) -> List[IntelligenceComponent]:
        """Get all registered components"""
        return list(self._components.values())

class DataPipeline:
    """Manages data flow between components"""
    
    def __init__(self, logger: IntelligenceLogger):
        self.logger = logger
        self._routes: Dict[str, List[str]] = defaultdict(list)
        self._processors: Dict[str, List[IntelligenceComponent]] = defaultdict(list)
        
    def add_route(self, source: str, destination: str) -> None:
        """Add data route from source to destination"""
        self._routes[source].append(destination)
        self.logger.logger.info(f"Added route: {source} -> {destination}")
        
    def add_processor(self, route: str, processor: IntelligenceComponent) -> None:
        """Add processor to route"""
        self._processors[route].append(processor)
        self.logger.logger.info(f"Added processor {processor.name} to route {route}")
        
    async def process_data(self, source: str, data: Any) -> Dict[str, Any]:
        """Process data through pipeline"""
        results = {}
        
        # Get destinations for source
        destinations = self._routes.get(source, [])
        
        for destination in destinations:
            route_key = f"{source}->{destination}"
            processors = self._processors.get(route_key, [])
            
            # Process data through each processor
            processed_data = data
            for processor in processors:
                try:
                    processed_data = await processor.process(processed_data)
                except Exception as e:
                    self.logger.log_error(e, {'processor': processor.name, 'route': route_key})
                    continue
                    
            results[destination] = processed_data
            
        return results

class IntelligenceOrchestrator:
    """Main orchestrator for the intelligence system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigManager(config_path)
        self.logger = LoggerManager.get_logger("intelligence.orchestrator")
        self.registry = ComponentRegistry()
        self.pipeline = DataPipeline(self.logger)
        
        # Core components
        self.cache_manager: Optional[CacheManager] = None
        self.metrics_monitor: Optional[MetricsMonitor] = None
        
        # State
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
    async def initialize(self) -> None:
        """Initialize the orchestrator and all components"""
        self.logger.logger.info("Initializing Intelligence Orchestrator")
        
        try:
            # Load configuration
            await self.config_manager.load_config()
            
            # Validate configuration
            issues = await self.config_manager.validate_config()
            if issues:
                self.logger.logger.warning(f"Configuration issues: {issues}")
                
            # Initialize cache manager
            cache_config = self.config_manager.get_cache_config()
            if cache_config.enabled:
                self.cache_manager = CacheManager(cache_config)
                await self.cache_manager.initialize()
                
            # Initialize metrics monitor
            monitoring_config = self.config_manager.get_monitoring_config()
            if monitoring_config.metrics_enabled:
                self.metrics_monitor = MetricsMonitor()
                
                # Add exporters
                prometheus_url = self.config_manager.get('metrics.prometheus_url')
                if prometheus_url:
                    self.metrics_monitor.add_exporter(PrometheusExporter(prometheus_url))
                    
                self.metrics_monitor.add_exporter(JSONExporter())
                
                await self.metrics_monitor.start()
                
            # Setup signal handlers
            self._setup_signal_handlers()
            
            self.logger.logger.info("Intelligence Orchestrator initialized successfully")
            
        except Exception as e:
            self.logger.log_error(e, {'phase': 'initialization'})
            raise
            
    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown handlers"""
        def signal_handler(sig, frame):
            self.logger.logger.info(f"Received signal {sig}, initiating shutdown")
            asyncio.create_task(self.shutdown())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def register_component(self, component: IntelligenceComponent) -> None:
        """Register and initialize a component"""
        self.logger.logger.info(f"Registering component: {component.name}")
        
        # Add cache manager if available
        if self.cache_manager and hasattr(component, 'cache_manager'):
            component.cache_manager = self.cache_manager
            
        # Initialize component
        await component.initialize()
        
        # Register
        self.registry.register(component)
        
        # Setup callbacks for data ingestion components
        if isinstance(component, DataIngestionComponent):
            async def data_callback(data):
                await self.pipeline.process_data(component.name, data)
            component.add_callback(data_callback)
            
    async def add_data_source(self, name: str, source_type: str, config: Dict[str, Any]) -> None:
        """Add a new data source"""
        # Create data source
        data_source = DataSource(
            name=name,
            type=source_type,
            config=config
        )
        
        # Create ingester based on type
        ingester_class = self._get_ingester_class(source_type)
        ingester = ingester_class(
            name=f"{name}_ingester",
            data_source=data_source,
            config=config
        )
        
        # Create normalizer
        normalizer = NormalizerFactory.create_normalizer(
            source_type=source_type,
            name=f"{name}_normalizer",
            config=config
        )
        
        # Register components
        await self.register_component(ingester)
        await self.register_component(normalizer)
        
        # Setup pipeline
        self.pipeline.add_route(ingester.name, normalizer.name)
        
    def _get_ingester_class(self, source_type: str) -> Type[BaseDataIngester]:
        """Get ingester class for source type"""
        # Import here to avoid circular imports
        from ..ingestion.base import HTTPDataIngester, WebSocketDataIngester
        
        ingester_map = {
            'http': HTTPDataIngester,
            'websocket': WebSocketDataIngester,
            # Add more as needed
        }
        
        return ingester_map.get(source_type, HTTPDataIngester)
        
    async def add_signal_generator(self, generator: SignalGenerator) -> None:
        """Add a signal generator to the system"""
        await self.register_component(generator)
        
        # Connect normalizers to signal generators
        normalizers = self.registry.get_by_type(DataNormalizer)
        for normalizer in normalizers:
            self.pipeline.add_route(normalizer.name, generator.name)
            
    async def start(self) -> None:
        """Start the orchestrator and all components"""
        if self._running:
            self.logger.logger.warning("Orchestrator already running")
            return
            
        self.logger.logger.info("Starting Intelligence Orchestrator")
        self._running = True
        
        try:
            # Start all components
            components = self.registry.get_all()
            start_tasks = [component.start() for component in components]
            await asyncio.gather(*start_tasks, return_exceptions=True)
            
            # Start monitoring task
            monitor_task = asyncio.create_task(self._monitor_loop())
            self._tasks.append(monitor_task)
            
            self.logger.logger.info(f"Started {len(components)} components")
            
        except Exception as e:
            self.logger.log_error(e, {'phase': 'startup'})
            await self.stop()
            raise
            
    async def stop(self) -> None:
        """Stop the orchestrator and all components"""
        if not self._running:
            return
            
        self.logger.logger.info("Stopping Intelligence Orchestrator")
        self._running = False
        
        try:
            # Stop all components
            components = self.registry.get_all()
            stop_tasks = [component.stop() for component in components]
            await asyncio.gather(*stop_tasks, return_exceptions=True)
            
            # Cancel monitoring tasks
            for task in self._tasks:
                task.cancel()
            await asyncio.gather(*self._tasks, return_exceptions=True)
            
            # Stop metrics monitor
            if self.metrics_monitor:
                await self.metrics_monitor.stop()
                
            # Close cache manager
            if self.cache_manager:
                await self.cache_manager.close()
                
            self.logger.logger.info("Intelligence Orchestrator stopped")
            
        except Exception as e:
            self.logger.log_error(e, {'phase': 'shutdown'})
            
    async def shutdown(self) -> None:
        """Graceful shutdown"""
        self.logger.logger.info("Initiating graceful shutdown")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Stop orchestrator
        await self.stop()
        
        # Save configuration
        try:
            await self.config_manager.save_config()
        except Exception as e:
            self.logger.log_error(e, {'phase': 'config_save'})
            
    async def _monitor_loop(self) -> None:
        """Monitor system health and performance"""
        while self._running:
            try:
                # Collect health checks
                health_data = await self.get_system_health()
                
                # Log health status
                self.logger.log_event('health_check', health_data)
                
                # Update metrics
                if self.metrics_monitor:
                    active_components = len([c for c in health_data['components'] if c['running']])
                    self.metrics_monitor.collector.set_gauge('active_components', active_components)
                    
                # Check for unhealthy components
                unhealthy = [c for c in health_data['components'] if not c['running']]
                if unhealthy:
                    self.logger.logger.warning(f"Unhealthy components: {[c['name'] for c in unhealthy]}")
                    
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.log_error(e, {'phase': 'monitoring'})
                await asyncio.sleep(60)
                
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        components_health = []
        
        for component in self.registry.get_all():
            try:
                health = await component.health_check()
                components_health.append(health)
            except Exception as e:
                components_health.append({
                    'name': component.name,
                    'running': False,
                    'error': str(e)
                })
                
        cache_stats = self.cache_manager.get_stats() if self.cache_manager else {}
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'running': self._running,
            'components': components_health,
            'cache_stats': cache_stats,
            'total_components': len(self.registry.get_all())
        }
        
    async def get_signals(self, filters: Optional[Dict[str, Any]] = None) -> List[Signal]:
        """Get signals from all generators"""
        all_signals = []
        
        generators = self.registry.get_by_type(SignalGenerator)
        for generator in generators:
            try:
                # Get signals from generator
                signals = await generator.analyze(None)  # Generators should have internal data
                
                # Apply filters if provided
                if filters:
                    signals = await generator.filter_signals(signals)
                    
                all_signals.extend(signals)
                
            except Exception as e:
                self.logger.log_error(e, {'generator': generator.name})
                
        # Rank all signals
        if all_signals and generators:
            all_signals = await generators[0].rank_signals(all_signals)
            
        return all_signals
        
    @asynccontextmanager
    async def managed_lifecycle(self):
        """Context manager for orchestrator lifecycle"""
        try:
            await self.initialize()
            await self.start()
            yield self
        finally:
            await self.shutdown()

# Example usage
async def create_intelligence_system(config_path: Optional[str] = None) -> IntelligenceOrchestrator:
    """Factory function to create and initialize intelligence system"""
    orchestrator = IntelligenceOrchestrator(config_path)
    await orchestrator.initialize()
    return orchestrator