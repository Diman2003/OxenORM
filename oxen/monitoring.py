#!/usr/bin/env python3
"""
OxenORM Performance Monitoring System

This module provides comprehensive performance monitoring capabilities including:
- Query execution time tracking
- Memory usage monitoring
- Connection pool statistics
- Performance metrics collection
- Real-time performance alerts
- Performance data export and analysis
"""

import time
import psutil
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import threading
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for a single query execution."""
    query_id: str
    sql: str
    duration_ms: float
    memory_before_mb: float
    memory_after_mb: float
    memory_delta_mb: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    connection_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionPoolMetrics:
    """Metrics for connection pool performance."""
    pool_name: str
    total_connections: int
    active_connections: int
    idle_connections: int
    waiting_requests: int
    connection_creation_time_ms: float
    connection_acquire_time_ms: float
    connection_release_time_ms: float
    timestamp: datetime


@dataclass
class SystemMetrics:
    """System-level performance metrics."""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    timestamp: datetime


@dataclass
class PerformanceAlert:
    """Performance alert configuration and state."""
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    threshold: float
    current_value: float
    triggered: bool
    triggered_at: Optional[datetime] = None
    message: str = ""
    severity: str = "warning"  # warning, error, critical


class PerformanceMonitor:
    """Main performance monitoring class."""
    
    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        
        # Query metrics storage
        self.query_metrics: deque = deque(maxlen=max_history_size)
        self.query_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0.0,
            'avg_duration': 0.0,
            'min_duration': float('inf'),
            'max_duration': 0.0,
            'success_count': 0,
            'error_count': 0,
            'total_memory_delta': 0.0
        })
        
        # Connection pool metrics
        self.connection_metrics: deque = deque(maxlen=max_history_size)
        
        # System metrics
        self.system_metrics: deque = deque(maxlen=max_history_size)
        
        # Performance alerts
        self.alerts: List[PerformanceAlert] = []
        
        # Monitoring state
        self.monitoring_enabled = True
        self.system_monitoring_task = None
        self.system_monitoring_interval = 5.0  # seconds
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Setup default alerts
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """Setup default performance alerts."""
        # Slow query alert
        self.add_alert(
            name="slow_query",
            condition=lambda metrics: metrics.get('avg_duration', 0) > 1000,
            threshold=1000,
            message="Average query duration exceeds 1 second"
        )
        
        # High memory usage alert
        self.add_alert(
            name="high_memory",
            condition=lambda metrics: metrics.get('memory_percent', 0) > 80,
            threshold=80,
            message="Memory usage exceeds 80%"
        )
        
        # Connection pool exhaustion alert
        self.add_alert(
            name="connection_exhaustion",
            condition=lambda metrics: metrics.get('active_connections', 0) / max(metrics.get('total_connections', 1), 1) > 0.9,
            threshold=0.9,
            message="Connection pool usage exceeds 90%"
        )
    
    def add_alert(self, name: str, condition: Callable, threshold: float, message: str, severity: str = "warning"):
        """Add a performance alert."""
        alert = PerformanceAlert(
            name=name,
            condition=condition,
            threshold=threshold,
            current_value=0.0,
            triggered=False,
            message=message,
            severity=severity
        )
        self.alerts.append(alert)
    
    def start_system_monitoring(self):
        """Start system monitoring in background."""
        if self.system_monitoring_task is None:
            self.system_monitoring_task = asyncio.create_task(self._system_monitoring_loop())
    
    def stop_system_monitoring(self):
        """Stop system monitoring."""
        if self.system_monitoring_task:
            self.system_monitoring_task.cancel()
            self.system_monitoring_task = None
    
    async def _system_monitoring_loop(self):
        """Background system monitoring loop."""
        while self.monitoring_enabled:
            try:
                metrics = self._collect_system_metrics()
                self.system_metrics.append(metrics)
                
                # Check alerts
                await self._check_alerts(metrics)
                
                await asyncio.sleep(self.system_monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                await asyncio.sleep(self.system_monitoring_interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        network_io = psutil.net_io_counters()
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_available_mb=memory.available / 1024 / 1024,
            disk_io_read_mb=disk_io.read_bytes / 1024 / 1024 if disk_io else 0,
            disk_io_write_mb=disk_io.write_bytes / 1024 / 1024 if disk_io else 0,
            network_io_sent_mb=network_io.bytes_sent / 1024 / 1024 if network_io else 0,
            network_io_recv_mb=network_io.bytes_recv / 1024 / 1024 if network_io else 0,
            timestamp=datetime.utcnow()
        )
    
    async def _check_alerts(self, metrics: SystemMetrics):
        """Check performance alerts."""
        metrics_dict = {
            'cpu_percent': metrics.cpu_percent,
            'memory_percent': metrics.memory_percent,
            'memory_available_mb': metrics.memory_available_mb,
            'avg_duration': self.get_average_query_duration(),
            'active_connections': self.get_active_connections(),
            'total_connections': self.get_total_connections()
        }
        
        for alert in self.alerts:
            try:
                alert.current_value = metrics_dict.get(alert.name.split('_')[0], 0)
                triggered = alert.condition(metrics_dict)
                
                if triggered and not alert.triggered:
                    alert.triggered = True
                    alert.triggered_at = datetime.utcnow()
                    await self._handle_alert(alert, metrics_dict)
                elif not triggered and alert.triggered:
                    alert.triggered = False
                    alert.triggered_at = None
            except Exception as e:
                logger.error(f"Error checking alert {alert.name}: {e}")
    
    async def _handle_alert(self, alert: PerformanceAlert, metrics: Dict[str, Any]):
        """Handle a triggered performance alert."""
        message = f"🚨 {alert.severity.upper()}: {alert.message}"
        message += f" (Current: {alert.current_value:.2f}, Threshold: {alert.threshold:.2f})"
        
        logger.warning(message)
        
        # Here you could send notifications, emails, etc.
        # For now, just log the alert
    
    @asynccontextmanager
    async def track_query(self, sql: str, parameters: Optional[Dict[str, Any]] = None, connection_id: Optional[str] = None):
        """Context manager for tracking query performance."""
        if not self.monitoring_enabled:
            yield
            return
        
        query_id = f"query_{int(time.time() * 1000000)}"
        memory_before = self._get_memory_usage()
        start_time = time.time()
        
        try:
            yield query_id
            success = True
            error_message = None
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            end_time = time.time()
            memory_after = self._get_memory_usage()
            
            duration_ms = (end_time - start_time) * 1000
            memory_delta_mb = memory_after - memory_before
            
            metrics = QueryMetrics(
                query_id=query_id,
                sql=sql,
                duration_ms=duration_ms,
                memory_before_mb=memory_before,
                memory_after_mb=memory_after,
                memory_delta_mb=memory_delta_mb,
                timestamp=datetime.utcnow(),
                success=success,
                error_message=error_message,
                parameters=parameters,
                connection_id=connection_id
            )
            
            self._record_query_metrics(metrics)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _record_query_metrics(self, metrics: QueryMetrics):
        """Record query metrics."""
        with self._lock:
            self.query_metrics.append(metrics)
            
            # Update statistics
            stats = self.query_stats[metrics.sql]
            stats['count'] += 1
            stats['total_duration'] += metrics.duration_ms
            stats['avg_duration'] = stats['total_duration'] / stats['count']
            stats['min_duration'] = min(stats['min_duration'], metrics.duration_ms)
            stats['max_duration'] = max(stats['max_duration'], metrics.duration_ms)
            stats['total_memory_delta'] += metrics.memory_delta_mb
            
            if metrics.success:
                stats['success_count'] += 1
            else:
                stats['error_count'] += 1
    
    def record_connection_metrics(self, metrics: ConnectionPoolMetrics):
        """Record connection pool metrics."""
        with self._lock:
            self.connection_metrics.append(metrics)
    
    def get_query_statistics(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get query performance statistics."""
        with self._lock:
            if time_window:
                cutoff_time = datetime.utcnow() - time_window
                recent_metrics = [
                    m for m in self.query_metrics 
                    if m.timestamp >= cutoff_time
                ]
            else:
                recent_metrics = list(self.query_metrics)
            
            if not recent_metrics:
                return {
                    'total_queries': 0,
                    'avg_duration': 0.0,
                    'success_rate': 0.0,
                    'total_memory_delta': 0.0
                }
            
            total_queries = len(recent_metrics)
            total_duration = sum(m.duration_ms for m in recent_metrics)
            success_count = sum(1 for m in recent_metrics if m.success)
            total_memory_delta = sum(m.memory_delta_mb for m in recent_metrics)
            
            return {
                'total_queries': total_queries,
                'avg_duration': total_duration / total_queries if total_queries > 0 else 0,
                'min_duration': min(m.duration_ms for m in recent_metrics),
                'max_duration': max(m.duration_ms for m in recent_metrics),
                'success_rate': success_count / total_queries if total_queries > 0 else 0,
                'total_memory_delta': total_memory_delta,
                'queries_per_second': total_queries / (time_window.total_seconds() if time_window else 60)
            }
    
    def get_slow_queries(self, threshold_ms: float = 1000, limit: int = 10) -> List[QueryMetrics]:
        """Get slow queries above threshold."""
        with self._lock:
            slow_queries = [
                m for m in self.query_metrics 
                if m.duration_ms > threshold_ms
            ]
            return sorted(slow_queries, key=lambda m: m.duration_ms, reverse=True)[:limit]
    
    def get_error_queries(self, limit: int = 10) -> List[QueryMetrics]:
        """Get queries that resulted in errors."""
        with self._lock:
            error_queries = [
                m for m in self.query_metrics 
                if not m.success
            ]
            return sorted(error_queries, key=lambda m: m.timestamp, reverse=True)[:limit]
    
    def get_average_query_duration(self) -> float:
        """Get average query duration in milliseconds."""
        stats = self.get_query_statistics()
        return stats['avg_duration']
    
    def get_active_connections(self) -> int:
        """Get number of active connections."""
        if not self.connection_metrics:
            return 0
        latest = self.connection_metrics[-1]
        return latest.active_connections
    
    def get_total_connections(self) -> int:
        """Get total number of connections."""
        if not self.connection_metrics:
            return 0
        latest = self.connection_metrics[-1]
        return latest.total_connections
    
    def get_system_metrics_summary(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get system metrics summary."""
        with self._lock:
            if time_window:
                cutoff_time = datetime.utcnow() - time_window
                recent_metrics = [
                    m for m in self.system_metrics 
                    if m.timestamp >= cutoff_time
                ]
            else:
                recent_metrics = list(self.system_metrics)
            
            if not recent_metrics:
                return {}
            
            return {
                'avg_cpu_percent': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
                'avg_memory_percent': sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
                'avg_memory_available_mb': sum(m.memory_available_mb for m in recent_metrics) / len(recent_metrics),
                'total_disk_read_mb': sum(m.disk_io_read_mb for m in recent_metrics),
                'total_disk_write_mb': sum(m.disk_io_write_mb for m in recent_metrics),
                'total_network_sent_mb': sum(m.network_io_sent_mb for m in recent_metrics),
                'total_network_recv_mb': sum(m.network_io_recv_mb for m in recent_metrics)
            }
    
    def export_metrics(self, filename: str = None) -> str:
        """Export metrics to JSON file."""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"oxenorm_metrics_{timestamp}.json"
        
        with self._lock:
            data = {
                'export_timestamp': datetime.utcnow().isoformat(),
                'query_metrics': [
                    {
                        'query_id': m.query_id,
                        'sql': m.sql,
                        'duration_ms': m.duration_ms,
                        'memory_delta_mb': m.memory_delta_mb,
                        'timestamp': m.timestamp.isoformat(),
                        'success': m.success,
                        'error_message': m.error_message
                    }
                    for m in self.query_metrics
                ],
                'connection_metrics': [
                    {
                        'pool_name': m.pool_name,
                        'total_connections': m.total_connections,
                        'active_connections': m.active_connections,
                        'idle_connections': m.idle_connections,
                        'timestamp': m.timestamp.isoformat()
                    }
                    for m in self.connection_metrics
                ],
                'system_metrics': [
                    {
                        'cpu_percent': m.cpu_percent,
                        'memory_percent': m.memory_percent,
                        'memory_available_mb': m.memory_available_mb,
                        'timestamp': m.timestamp.isoformat()
                    }
                    for m in self.system_metrics
                ],
                'statistics': {
                    'query_stats': self.get_query_statistics(),
                    'system_summary': self.get_system_metrics_summary()
                }
            }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename
    
    def clear_metrics(self):
        """Clear all stored metrics."""
        with self._lock:
            self.query_metrics.clear()
            self.connection_metrics.clear()
            self.system_metrics.clear()
            self.query_stats.clear()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        query_stats = self.get_query_statistics()
        system_summary = self.get_system_metrics_summary()
        slow_queries = self.get_slow_queries()
        error_queries = self.get_error_queries()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'query_performance': {
                'total_queries': query_stats['total_queries'],
                'avg_duration_ms': query_stats['avg_duration'],
                'success_rate': query_stats['success_rate'],
                'queries_per_second': query_stats['queries_per_second'],
                'slow_queries_count': len(slow_queries),
                'error_queries_count': len(error_queries)
            },
            'system_performance': system_summary,
            'connection_pool': {
                'active_connections': self.get_active_connections(),
                'total_connections': self.get_total_connections(),
                'utilization_percent': (self.get_active_connections() / max(self.get_total_connections(), 1)) * 100
            },
            'alerts': [
                {
                    'name': alert.name,
                    'triggered': alert.triggered,
                    'severity': alert.severity,
                    'message': alert.message
                }
                for alert in self.alerts
            ],
            'recommendations': self._generate_recommendations(query_stats, system_summary)
        }
    
    def _generate_recommendations(self, query_stats: Dict[str, Any], system_summary: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        # Query performance recommendations
        if query_stats['avg_duration'] > 100:
            recommendations.append("Consider optimizing slow queries or adding database indexes")
        
        if query_stats['success_rate'] < 0.95:
            recommendations.append("High error rate detected - review query error handling")
        
        # System performance recommendations
        if system_summary.get('avg_memory_percent', 0) > 80:
            recommendations.append("High memory usage - consider increasing memory or optimizing queries")
        
        if system_summary.get('avg_cpu_percent', 0) > 80:
            recommendations.append("High CPU usage - consider query optimization or scaling")
        
        # Connection pool recommendations
        utilization = (self.get_active_connections() / max(self.get_total_connections(), 1)) * 100
        if utilization > 90:
            recommendations.append("Connection pool utilization high - consider increasing pool size")
        
        return recommendations


# Global performance monitor instance
_global_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def enable_performance_monitoring():
    """Enable global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.monitoring_enabled = True
    monitor.start_system_monitoring()


def disable_performance_monitoring():
    """Disable global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.monitoring_enabled = False
    monitor.stop_system_monitoring()


@asynccontextmanager
async def track_query_performance(sql: str, parameters: Optional[Dict[str, Any]] = None):
    """Global function for tracking query performance."""
    monitor = get_performance_monitor()
    async with monitor.track_query(sql, parameters) as query_id:
        yield query_id 