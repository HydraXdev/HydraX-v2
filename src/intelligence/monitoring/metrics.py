"""
Metrics collection and monitoring system
Tracks performance, health, and business metrics
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum, auto
import asyncio
import time
from collections import deque, defaultdict
import statistics
import json
from pathlib import Path
import aiohttp
from abc import ABC, abstractmethod

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = auto()
    GAUGE = auto()
    HISTOGRAM = auto()
    SUMMARY = auto()
    RATE = auto()

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class Metric:
    """Metric definition"""
    name: str
    type: MetricType
    description: str = ""
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    retention_period: timedelta = field(default=timedelta(hours=24))

class MetricStore:
    """In-memory metric storage with retention"""
    
    def __init__(self, max_points_per_metric: int = 10000):
        self._data: Dict[str, deque] = {}
        self._metrics: Dict[str, Metric] = {}
        self.max_points = max_points_per_metric
        
    def register_metric(self, metric: Metric) -> None:
        """Register a new metric"""
        if metric.name not in self._metrics:
            self._metrics[metric.name] = metric
            self._data[metric.name] = deque(maxlen=self.max_points)
            
    def add_point(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Add a data point to metric"""
        if metric_name not in self._data:
            raise ValueError(f"Metric {metric_name} not registered")
            
        point = MetricPoint(
            timestamp=datetime.utcnow(),
            value=value,
            tags=tags or {}
        )
        self._data[metric_name].append(point)
        
    def get_points(self, metric_name: str, since: Optional[datetime] = None) -> List[MetricPoint]:
        """Get metric points since timestamp"""
        if metric_name not in self._data:
            return []
            
        points = list(self._data[metric_name])
        if since:
            points = [p for p in points if p.timestamp >= since]
            
        return points
        
    def get_latest(self, metric_name: str) -> Optional[MetricPoint]:
        """Get latest metric point"""
        if metric_name not in self._data or not self._data[metric_name]:
            return None
        return self._data[metric_name][-1]
        
    def cleanup(self) -> None:
        """Remove old data points based on retention"""
        for metric_name, metric in self._metrics.items():
            if metric_name in self._data:
                cutoff = datetime.utcnow() - metric.retention_period
                # Remove old points
                while self._data[metric_name] and self._data[metric_name][0].timestamp < cutoff:
                    self._data[metric_name].popleft()

class MetricCollector:
    """Collects and aggregates metrics"""
    
    def __init__(self, store: MetricStore):
        self.store = store
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric"""
        self._counters[name] += value
        self.store.add_point(name, self._counters[name], tags)
        
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value"""
        self._gauges[name] = value
        self.store.add_point(name, value, tags)
        
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram value"""
        self._histograms[name].append(value)
        self.store.add_point(name, value, tags)
        
    def record_rate(self, name: str, tags: Optional[Dict[str, str]] = None) -> None:
        """Record an event for rate calculation"""
        self._rates[name].append(time.time())
        # Calculate rate (events per second over last minute)
        now = time.time()
        recent_events = [t for t in self._rates[name] if now - t <= 60]
        rate = len(recent_events) / 60.0 if recent_events else 0
        self.store.add_point(name, rate, tags)
        
    def get_counter_value(self, name: str) -> float:
        """Get current counter value"""
        return self._counters.get(name, 0)
        
    def get_gauge_value(self, name: str) -> Optional[float]:
        """Get current gauge value"""
        return self._gauges.get(name)
        
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics"""
        values = self._histograms.get(name, [])
        if not values:
            return {}
            
        return {
            'count': len(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'stddev': statistics.stdev(values) if len(values) > 1 else 0,
            'p95': statistics.quantiles(values, n=20)[18] if len(values) > 20 else max(values),
            'p99': statistics.quantiles(values, n=100)[98] if len(values) > 100 else max(values)
        }

class MetricsExporter(ABC):
    """Base class for metrics exporters"""
    
    @abstractmethod
    async def export(self, metrics: Dict[str, Any]) -> None:
        """Export metrics to external system"""
        pass

class PrometheusExporter(MetricsExporter):
    """Export metrics in Prometheus format"""
    
    def __init__(self, pushgateway_url: Optional[str] = None):
        self.pushgateway_url = pushgateway_url
        
    async def export(self, metrics: Dict[str, Any]) -> None:
        """Export metrics to Prometheus pushgateway"""
        if not self.pushgateway_url:
            return
            
        # Format metrics in Prometheus format
        lines = []
        for metric_name, metric_data in metrics.items():
            if isinstance(metric_data, dict):
                for key, value in metric_data.items():
                    lines.append(f'{metric_name}_{key} {value}')
            else:
                lines.append(f'{metric_name} {metric_data}')
                
        payload = '\\n'.join(lines)
        
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(
                    f"{self.pushgateway_url}/metrics/job/intelligence_system",
                    data=payload,
                    headers={'Content-Type': 'text/plain'}
                )
            except Exception as e:
                # Log error but don't fail
                pass

class JSONExporter(MetricsExporter):
    """Export metrics to JSON file"""
    
    def __init__(self, output_dir: str = "metrics"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def export(self, metrics: Dict[str, Any]) -> None:
        """Export metrics to JSON file"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"metrics_{timestamp}.json"
        
        export_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

class MetricsMonitor:
    """Main metrics monitoring system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.store = MetricStore()
        self.collector = MetricCollector(self.store)
        self.exporters: List[MetricsExporter] = []
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # Register default metrics
        self._register_default_metrics()
        
    def _register_default_metrics(self) -> None:
        """Register default system metrics"""
        # Performance metrics
        self.store.register_metric(Metric("request_count", MetricType.COUNTER, "Total requests"))
        self.store.register_metric(Metric("request_duration", MetricType.HISTOGRAM, "Request duration", "ms"))
        self.store.register_metric(Metric("error_count", MetricType.COUNTER, "Total errors"))
        
        # System metrics
        self.store.register_metric(Metric("cpu_usage", MetricType.GAUGE, "CPU usage", "%"))
        self.store.register_metric(Metric("memory_usage", MetricType.GAUGE, "Memory usage", "MB"))
        self.store.register_metric(Metric("active_connections", MetricType.GAUGE, "Active connections"))
        
        # Business metrics
        self.store.register_metric(Metric("signals_generated", MetricType.COUNTER, "Signals generated"))
        self.store.register_metric(Metric("signal_accuracy", MetricType.GAUGE, "Signal accuracy", "%"))
        self.store.register_metric(Metric("data_ingestion_rate", MetricType.RATE, "Data ingestion rate", "msg/s"))
        
    def add_exporter(self, exporter: MetricsExporter) -> None:
        """Add metrics exporter"""
        self.exporters.append(exporter)
        
    async def start(self) -> None:
        """Start metrics monitoring"""
        self._running = True
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._tasks.append(cleanup_task)
        
        # Start export task
        export_task = asyncio.create_task(self._export_loop())
        self._tasks.append(export_task)
        
    async def stop(self) -> None:
        """Stop metrics monitoring"""
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
    async def _cleanup_loop(self) -> None:
        """Periodically clean up old metrics"""
        while self._running:
            try:
                self.store.cleanup()
                await asyncio.sleep(3600)  # Cleanup every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue
                await asyncio.sleep(60)
                
    async def _export_loop(self) -> None:
        """Periodically export metrics"""
        export_interval = self.config.get('export_interval', 60)  # Default 1 minute
        
        while self._running:
            try:
                # Collect current metrics
                metrics = await self._collect_metrics()
                
                # Export to all exporters
                export_tasks = [exporter.export(metrics) for exporter in self.exporters]
                await asyncio.gather(*export_tasks, return_exceptions=True)
                
                await asyncio.sleep(export_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue
                await asyncio.sleep(export_interval)
                
    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect all current metrics"""
        metrics = {}
        
        # Add counter values
        for name, value in self.collector._counters.items():
            metrics[name] = value
            
        # Add gauge values
        for name, value in self.collector._gauges.items():
            metrics[name] = value
            
        # Add histogram stats
        for name in self.collector._histograms:
            stats = self.collector.get_histogram_stats(name)
            metrics[f"{name}_stats"] = stats
            
        # Add latest rates
        for name in self.collector._rates:
            latest = self.store.get_latest(name)
            if latest:
                metrics[f"{name}_rate"] = latest.value
                
        return metrics
        
    def record_request(self, duration: float, status: str = "success", endpoint: Optional[str] = None) -> None:
        """Record API request metrics"""
        tags = {'status': status}
        if endpoint:
            tags['endpoint'] = endpoint
            
        self.collector.increment_counter("request_count", tags=tags)
        self.collector.record_histogram("request_duration", duration * 1000, tags=tags)
        
        if status == "error":
            self.collector.increment_counter("error_count", tags=tags)
            
    def record_signal(self, signal_type: str, symbol: str, strength: float) -> None:
        """Record signal generation metrics"""
        tags = {
            'type': signal_type,
            'symbol': symbol,
            'strength': str(strength)
        }
        self.collector.increment_counter("signals_generated", tags=tags)
        
    def update_system_metrics(self, cpu: float, memory: float, connections: int) -> None:
        """Update system resource metrics"""
        self.collector.set_gauge("cpu_usage", cpu)
        self.collector.set_gauge("memory_usage", memory)
        self.collector.set_gauge("active_connections", connections)