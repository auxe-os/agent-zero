"""
Performance Monitoring and Optimization System
Provides real-time performance monitoring and optimization recommendations
"""
import asyncio
import time
import psutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from python.helpers.tool_cache import get_tool_cache_stats
from python.helpers.extension_cache import get_extension_cache_stats
from python.helpers.optimized_tool_execution import get_tool_performance_stats
from python.helpers.print_style import PrintStyle


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    tool_cache_stats: Dict[str, Any] = field(default_factory=dict)
    extension_cache_stats: Dict[str, Any] = field(default_factory=dict)
    tool_execution_stats: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class PerformanceMonitor:
    """Real-time performance monitoring and optimization"""
    
    def __init__(self):
        self._metrics_history: List[PerformanceMetrics] = []
        self._max_history = 100
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def start_monitoring(self, interval_seconds: float = 5.0):
        """Start performance monitoring"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval_seconds))
        PrintStyle(font_color="green").print("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        PrintStyle(font_color="yellow").print("Performance monitoring stopped")
    
    async def _monitor_loop(self, interval_seconds: float):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                metrics = await self._collect_metrics()
                self._metrics_history.append(metrics)
                
                # Keep only recent history
                if len(self._metrics_history) > self._max_history:
                    self._metrics_history.pop(0)
                
                # Generate recommendations
                recommendations = self._generate_recommendations(metrics)
                if recommendations:
                    PrintStyle(font_color="cyan").print("Performance Recommendations:")
                    for rec in recommendations:
                        PrintStyle(font_color="cyan").print(f"  • {rec}")
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                PrintStyle(font_color="red").print(f"Performance monitoring error: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        # System metrics
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Cache statistics
        tool_cache_stats = get_tool_cache_stats()
        extension_cache_stats = get_extension_cache_stats()
        tool_execution_stats = get_tool_performance_stats()
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            tool_cache_stats=tool_cache_stats,
            extension_cache_stats=extension_cache_stats,
            tool_execution_stats=tool_execution_stats
        )
    
    def _generate_recommendations(self, metrics: PerformanceMetrics) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # CPU usage recommendations
        if metrics.cpu_usage > 80:
            recommendations.append("High CPU usage detected - consider reducing concurrent operations")
        elif metrics.cpu_usage > 60:
            recommendations.append("Moderate CPU usage - monitor for potential bottlenecks")
        
        # Memory usage recommendations
        if metrics.memory_usage > 85:
            recommendations.append("High memory usage - consider clearing caches or reducing cache sizes")
        elif metrics.memory_usage > 70:
            recommendations.append("Moderate memory usage - monitor memory growth")
        
        # Cache performance recommendations
        tool_cache = metrics.tool_cache_stats
        if tool_cache.get('hit_rate', '0%').replace('%', '') != '0%':
            hit_rate = float(tool_cache.get('hit_rate', '0%').replace('%', ''))
            if hit_rate < 50:
                recommendations.append(f"Low tool cache hit rate ({hit_rate:.1f}%) - consider preloading frequently used tools")
            elif hit_rate > 90:
                recommendations.append(f"Excellent tool cache hit rate ({hit_rate:.1f}%) - system is well optimized")
        
        extension_cache = metrics.extension_cache_stats
        if extension_cache.get('hit_rate', '0%').replace('%', '') != '0%':
            hit_rate = float(extension_cache.get('hit_rate', '0%').replace('%', ''))
            if hit_rate < 50:
                recommendations.append(f"Low extension cache hit rate ({hit_rate:.1f}%) - consider preloading extensions")
        
        # Tool execution performance
        tool_exec = metrics.tool_execution_stats
        if 'avg_execution_time' in tool_exec:
            avg_time = float(tool_exec['avg_execution_time'].replace('s', ''))
            if avg_time > 2.0:
                recommendations.append(f"Slow tool execution ({avg_time:.2f}s) - consider optimizing tool implementations")
            elif avg_time < 0.5:
                recommendations.append(f"Fast tool execution ({avg_time:.2f}s) - system is well optimized")
        
        return recommendations
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get current performance metrics"""
        if not self._metrics_history:
            return None
        return self._metrics_history[-1]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        if not self._metrics_history:
            return {"message": "No metrics available"}
        
        recent_metrics = self._metrics_history[-10:]  # Last 10 measurements
        
        avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        
        return {
            "monitoring_active": self._monitoring,
            "metrics_count": len(self._metrics_history),
            "avg_cpu_usage": f"{avg_cpu:.1f}%",
            "avg_memory_usage": f"{avg_memory:.1f}%",
            "current_cpu": f"{recent_metrics[-1].cpu_usage:.1f}%" if recent_metrics else "N/A",
            "current_memory": f"{recent_metrics[-1].memory_usage:.1f}%" if recent_metrics else "N/A",
            "tool_cache_stats": recent_metrics[-1].tool_cache_stats if recent_metrics else {},
            "extension_cache_stats": recent_metrics[-1].extension_cache_stats if recent_metrics else {},
            "tool_execution_stats": recent_metrics[-1].tool_execution_stats if recent_metrics else {}
        }
    
    def clear_history(self):
        """Clear metrics history"""
        self._metrics_history.clear()


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()


async def start_performance_monitoring(interval_seconds: float = 5.0):
    """Start performance monitoring"""
    await _performance_monitor.start_monitoring(interval_seconds)


async def stop_performance_monitoring():
    """Stop performance monitoring"""
    await _performance_monitor.stop_monitoring()


def get_performance_summary() -> Dict[str, Any]:
    """Get performance summary"""
    return _performance_monitor.get_metrics_summary()


def clear_performance_history():
    """Clear performance history"""
    _performance_monitor.clear_history()


def get_current_performance_metrics() -> Optional[PerformanceMetrics]:
    """Get current performance metrics"""
    return _performance_monitor.get_current_metrics()
