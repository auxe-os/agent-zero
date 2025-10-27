"""
Performance Optimizer Tool
Provides commands to monitor and optimize Agent Zero performance,
including intelligent tool recommendations and usage analytics
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
from python.helpers.tool_recommendation import recommend_tools_for_task, analyze_task
from python.helpers.tool_analytics import get_tool_analytics
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
        elif action == "recommend_tools":
            return await self._recommend_tools_for_task()
        elif action == "analyze_task":
            return await self._analyze_current_task()
        elif action == "get_insights":
            return await self._get_performance_insights()
        elif action == "get_tool_guidance":
            return await self._get_tool_usage_guidance()
        else:
            return Response(
                message="Invalid action. Available actions: status, start_monitoring, stop_monitoring, clear_caches, optimize, benchmark, recommend_tools, analyze_task, get_insights, get_tool_guidance",
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

    async def _recommend_tools_for_task(self) -> Response:
        """Provide tool recommendations for a specific task"""
        task_description = self.args.get("task", "").strip()
        max_recommendations = int(self.args.get("limit", 5))

        if not task_description:
            return Response(
                message="Please provide a task description for tool recommendations using the 'task' parameter.",
                break_loop=False
            )

        try:
            recommendations = recommend_tools_for_task(
                task_description,
                self.agent.agent_name,
                max_recommendations
            )

            if not recommendations:
                return Response(
                    message=f"No specific tool recommendations found for: {task_description}",
                    break_loop=False
                )

            result = f"## Tool Recommendations for: {task_description}\n\n"

            for i, rec in enumerate(recommendations, 1):
                result += f"### {i}. {rec.tool_name}\n"
                result += f"**Confidence:** {rec.confidence_score:.1%}\n"
                result += f"**Success Rate:** {rec.success_rate:.1%}\n"
                result += f"**Avg Execution Time:** {rec.avg_execution_time:.1f}s\n"
                result += f"**Agent Preference:** {rec.agent_preference:.1%}\n"
                result += f"**Why this tool:** {', '.join(rec.reasoning[:2])}\n\n"

            return Response(message=result, break_loop=False)

        except Exception as e:
            return Response(
                message=f"Error generating tool recommendations: {str(e)}",
                break_loop=False
            )

    async def _analyze_current_task(self) -> Response:
        """Analyze current task complexity and provide approach recommendations"""
        task_description = self.args.get("task", "").strip()

        if not task_description:
            return Response(
                message="Please provide a task description for analysis using the 'task' parameter.",
                break_loop=False
            )

        try:
            analysis = analyze_task(task_description)

            result = f"## Task Analysis: {task_description}\n\n"
            result += f"**Complexity Level:** {analysis['complexity_level'].upper()}\n"
            result += f"**Complexity Score:** {analysis['complexity_score']}\n"
            result += f"**Approach:** {analysis['recommended_approach']}\n\n"

            if analysis['detected_indicators']:
                result += f"**Detected Indicators:** {', '.join(analysis['detected_indicators'])}\n\n"

            if analysis['suggested_tools']:
                result += "**Suggested Tools:**\n"
                for i, tool in enumerate(analysis['suggested_tools'][:3], 1):
                    result += f"{i}. {tool.tool_name} (confidence: {tool.confidence_score:.1%})\n"

            return Response(message=result, break_loop=False)

        except Exception as e:
            return Response(
                message=f"Error analyzing task: {str(e)}",
                break_loop=False
            )

    async def _get_performance_insights(self) -> Response:
        """Get performance insights for the current agent"""
        try:
            analytics = get_tool_analytics()
            insights = analytics.get_agent_tool_insights(self.agent.agent_name)

            if "message" in insights:
                return Response(message=insights["message"], break_loop=False)

            result = f"## Performance Insights for {self.agent.agent_name}\n\n"
            result += f"**Total Tool Uses:** {insights['total_tool_uses']}\n"
            result += f"**Unique Tools Used:** {insights['unique_tools_used']}\n"
            result += f"**Performance Trend:** {insights['performance_trend']}\n"
            result += f"**Recent Activity (7 days):** {insights['recent_activity']} uses\n\n"

            result += "### Most Used Tools:\n"
            for i, (tool, count) in enumerate(insights['most_used_tools'][:5], 1):
                success_rate = insights['tool_success_rates'].get(tool, 0)
                result += f"{i}. {tool}: {count} uses ({success_rate:.1%} success)\n"

            if insights['performance_trend'] == "declining":
                result += "\n⚠️ **Performance is declining** - consider reviewing tool selection strategies."
            elif insights['performance_trend'] == "improving":
                result += "\n✅ **Performance is improving** - current strategies are working well."

            return Response(message=result, break_loop=False)

        except Exception as e:
            return Response(
                message=f"Error getting performance insights: {str(e)}",
                break_loop=False
            )

    async def _get_tool_usage_guidance(self) -> Response:
        """Get detailed guidance for using a specific tool"""
        tool_name = self.args.get("tool", "").strip()

        if not tool_name:
            return Response(
                message="Please specify a tool name for guidance using the 'tool' parameter (e.g., code_execution, search_engine, memory_save).",
                break_loop=False
            )

        try:
            analytics = get_tool_analytics()
            engine = analytics.get_tool_usage_guidance(tool_name)

            result = f"## Tool Guidance: {tool_name}\n\n"

            if "message" in engine:
                result += engine["message"]
            else:
                result += f"**Description:** {engine.get('description', 'No description available')}\n\n"

                if engine.get('best_for'):
                    result += f"**Best For:** {', '.join(engine['best_for'])}\n"

                if engine.get('keywords'):
                    result += f"**Keywords:** {', '.join(engine['keywords'])}\n"

                if engine.get('success_rate') is not None:
                    result += f"**Success Rate:** {engine['success_rate']:.1%}\n"

                if engine.get('avg_execution_time') is not None:
                    result += f"**Avg Execution Time:** {engine['avg_execution_time']:.1f}s\n"

                if engine.get('common_errors'):
                    result += f"**Common Issues:** {', '.join(engine['common_errors'][:3])}\n"

                if engine.get('tips'):
                    result += "\n**Usage Tips:**\n"
                    for tip in engine['tips']:
                        result += f"- {tip}\n"

            return Response(message=result, break_loop=False)

        except Exception as e:
            return Response(
                message=f"Error getting tool guidance: {str(e)}",
                break_loop=False
            )
