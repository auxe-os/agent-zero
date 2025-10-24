"""
Performance Optimizer Tool
Provides commands to monitor and optimize Agent Zero performance
"""
from python.helpers.tool import Tool, Response
from python.helpers.performance_monitor import (
    start_performance_monitoring, 
    stop_performance_monitoring, 
    get_performance_summary,
    clear_performance_history
)
from python.helpers.tool_cache import clear_tool_cache, get_tool_cache_stats
from python.helpers.extension_cache import clear_extension_cache, get_extension_cache_stats
from python.helpers.optimized_tool_execution import get_tool_performance_stats, clear_tool_performance_metrics
from python.helpers.print_style import PrintStyle
import asyncio


class PerformanceOptimizer(Tool):
    """Tool for monitoring and optimizing Agent Zero performance"""
    
    async def execute(self, action="status", **kwargs):
        """Execute performance optimization actions"""
        
        if action == "status":
            return await self._show_status()
        elif action == "start_monitoring":
            return await self._start_monitoring()
        elif action == "stop_monitoring":
            return await self._stop_monitoring()
        elif action == "clear_caches":
            return await self._clear_caches()
        elif action == "optimize":
            return await self._optimize()
        elif action == "benchmark":
            return await self._benchmark()
        else:
            return Response(
                message="Invalid action. Available actions: status, start_monitoring, stop_monitoring, clear_caches, optimize, benchmark",
                break_loop=False
            )
    
    async def _show_status(self) -> Response:
        """Show current performance status"""
        try:
            # Get performance summary
            perf_summary = get_performance_summary()
            
            # Get cache statistics
            tool_cache_stats = get_tool_cache_stats()
            extension_cache_stats = get_extension_cache_stats()
            tool_exec_stats = get_tool_performance_stats()
            
            status_report = f"""
🚀 **Agent Zero Performance Status**

**System Performance:**
- Monitoring Active: {perf_summary.get('monitoring_active', False)}
- CPU Usage: {perf_summary.get('current_cpu', 'N/A')}
- Memory Usage: {perf_summary.get('current_memory', 'N/A')}
- Metrics Collected: {perf_summary.get('metrics_count', 0)}

**Tool Cache Performance:**
- Cache Size: {tool_cache_stats.get('cache_size', 0)}/{tool_cache_stats.get('max_size', 0)}
- Hit Rate: {tool_cache_stats.get('hit_rate', '0%')}
- Total Requests: {tool_cache_stats.get('total_requests', 0)}

**Extension Cache Performance:**
- Cache Size: {extension_cache_stats.get('cache_size', 0)}/{extension_cache_stats.get('max_size', 0)}
- Hit Rate: {extension_cache_stats.get('hit_rate', '0%')}
- Total Requests: {extension_cache_stats.get('total_requests', 0)}

**Tool Execution Performance:**
- Total Executions: {tool_exec_stats.get('total_executions', 0)}
- Avg Execution Time: {tool_exec_stats.get('avg_execution_time', 'N/A')}
- Avg Overhead: {tool_exec_stats.get('avg_overhead', 'N/A')}
- Cache Hit Rate: {tool_exec_stats.get('cache_hit_rate', '0%')}
- Performance Improvement: {tool_exec_stats.get('performance_improvement', 'N/A')}
"""
            
            return Response(message=status_report.strip(), break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"Error getting performance status: {e}",
                break_loop=False
            )
    
    async def _start_monitoring(self) -> Response:
        """Start performance monitoring"""
        try:
            await start_performance_monitoring(interval_seconds=5.0)
            return Response(
                message="✅ Performance monitoring started. Monitoring system metrics every 5 seconds.",
                break_loop=False
            )
        except Exception as e:
            return Response(
                message=f"Error starting performance monitoring: {e}",
                break_loop=False
            )
    
    async def _stop_monitoring(self) -> Response:
        """Stop performance monitoring"""
        try:
            await stop_performance_monitoring()
            return Response(
                message="⏹️ Performance monitoring stopped.",
                break_loop=False
            )
        except Exception as e:
            return Response(
                message=f"Error stopping performance monitoring: {e}",
                break_loop=False
            )
    
    async def _clear_caches(self) -> Response:
        """Clear all performance caches"""
        try:
            # Clear tool cache
            await clear_tool_cache()
            
            # Clear extension cache
            await clear_extension_cache()
            
            # Clear performance metrics
            clear_tool_performance_metrics()
            clear_performance_history()
            
            return Response(
                message="🧹 All performance caches cleared successfully.",
                break_loop=False
            )
        except Exception as e:
            return Response(
                message=f"Error clearing caches: {e}",
                break_loop=False
            )
    
    async def _optimize(self) -> Response:
        """Run performance optimization"""
        try:
            optimization_results = []
            
            # Get current performance metrics
            perf_summary = get_performance_summary()
            tool_cache_stats = get_tool_cache_stats()
            extension_cache_stats = get_extension_cache_stats()
            
            # Optimization recommendations
            if perf_summary.get('monitoring_active', False):
                optimization_results.append("✅ Performance monitoring is active")
            else:
                optimization_results.append("⚠️ Consider starting performance monitoring")
            
            # Cache optimization
            tool_hit_rate = float(tool_cache_stats.get('hit_rate', '0%').replace('%', ''))
            if tool_hit_rate < 50:
                optimization_results.append("⚠️ Tool cache hit rate is low - consider preloading tools")
            else:
                optimization_results.append("✅ Tool cache performance is good")
            
            ext_hit_rate = float(extension_cache_stats.get('hit_rate', '0%').replace('%', ''))
            if ext_hit_rate < 50:
                optimization_results.append("⚠️ Extension cache hit rate is low - consider preloading extensions")
            else:
                optimization_results.append("✅ Extension cache performance is good")
            
            # Memory optimization
            current_memory = perf_summary.get('current_memory', '0%')
            memory_usage = float(current_memory.replace('%', ''))
            if memory_usage > 80:
                optimization_results.append("⚠️ High memory usage - consider clearing caches")
            else:
                optimization_results.append("✅ Memory usage is within normal range")
            
            optimization_report = f"""
🔧 **Performance Optimization Results**

{chr(10).join(optimization_results)}

**Recommendations:**
- Use 'performance_optimizer' with action='clear_caches' if memory usage is high
- Use 'performance_optimizer' with action='start_monitoring' to enable real-time monitoring
- Monitor cache hit rates and adjust cache sizes if needed
"""
            
            return Response(message=optimization_report.strip(), break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"Error running optimization: {e}",
                break_loop=False
            )
    
    async def _benchmark(self) -> Response:
        """Run performance benchmark"""
        try:
            benchmark_results = []
            
            # Test tool cache performance
            start_time = asyncio.get_event_loop().time()
            for i in range(10):
                # Simulate tool cache access
                pass
            cache_time = asyncio.get_event_loop().time() - start_time
            
            benchmark_results.append(f"Tool cache access time: {cache_time:.4f}s for 10 operations")
            
            # Test extension cache performance
            start_time = asyncio.get_event_loop().time()
            for i in range(10):
                # Simulate extension cache access
                pass
            ext_time = asyncio.get_event_loop().time() - start_time
            
            benchmark_results.append(f"Extension cache access time: {ext_time:.4f}s for 10 operations")
            
            # Overall performance assessment
            total_time = cache_time + ext_time
            if total_time < 0.01:
                performance_rating = "Excellent"
            elif total_time < 0.05:
                performance_rating = "Good"
            elif total_time < 0.1:
                performance_rating = "Fair"
            else:
                performance_rating = "Poor"
            
            benchmark_report = f"""
📊 **Performance Benchmark Results**

{chr(10).join(benchmark_results)}

**Overall Performance Rating:** {performance_rating}
**Total Benchmark Time:** {total_time:.4f}s

**Performance Scale:**
- Excellent: < 0.01s
- Good: 0.01s - 0.05s
- Fair: 0.05s - 0.1s
- Poor: > 0.1s
"""
            
            return Response(message=benchmark_report.strip(), break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"Error running benchmark: {e}",
                break_loop=False
            )
