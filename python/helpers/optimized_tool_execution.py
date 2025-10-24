"""
Optimized Tool Execution System
Implements high-performance tool execution with minimal overhead
"""
import asyncio
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from python.helpers.tool import Tool, Response
from python.helpers.tool_cache import get_cached_tool_class
from python.helpers.extension_cache import get_cached_extensions
from python.helpers.print_style import PrintStyle


@dataclass
class ToolExecutionMetrics:
    """Metrics for tool execution performance"""
    tool_name: str
    execution_time: float
    cache_hit: bool
    extension_calls: int
    intervention_calls: int
    total_overhead: float


class OptimizedToolExecutor:
    """High-performance tool execution with minimal overhead"""
    
    def __init__(self):
        self._metrics: List[ToolExecutionMetrics] = []
        self._intervention_throttle = {}  # Throttle intervention calls
        self._extension_throttle = {}  # Throttle extension calls
    
    async def execute_tool(
        self, 
        agent, 
        tool_name: str, 
        tool_args: Dict[str, Any], 
        message: str, 
        loop_data: Any = None
    ) -> Optional[Response]:
        """Execute tool with optimized performance"""
        start_time = time.time()
        metrics = ToolExecutionMetrics(
            tool_name=tool_name,
            execution_time=0,
            cache_hit=False,
            extension_calls=0,
            intervention_calls=0,
            total_overhead=0
        )
        
        try:
            # 1. Get tool class with caching
            tool_class = await get_cached_tool_class(tool_name, agent.config.profile)
            if not tool_class:
                PrintStyle(font_color="red").print(f"Tool '{tool_name}' not found")
                return None
            
            metrics.cache_hit = True
            
            # 2. Create tool instance
            tool = tool_class(
                agent=agent,
                name=tool_name,
                method=None,
                args=tool_args,
                message=message,
                loop_data=loop_data
            )
            
            # 3. Optimized intervention handling (throttled)
            await self._handle_intervention_optimized(agent, tool_name)
            metrics.intervention_calls += 1
            
            # 4. Tool before execution
            await tool.before_execution(**tool_args)
            await self._handle_intervention_optimized(agent, tool_name)
            metrics.intervention_calls += 1
            
            # 5. Optimized extension calls (throttled)
            await self._call_extensions_optimized(
                agent, "tool_execute_before", 
                tool_args=tool_args or {}, 
                tool_name=tool_name
            )
            metrics.extension_calls += 1
            
            # 6. Execute tool
            response = await tool.execute(**tool_args)
            await self._handle_intervention_optimized(agent, tool_name)
            metrics.intervention_calls += 1
            
            # 7. Post-execution extensions
            await self._call_extensions_optimized(
                agent, "tool_execute_after", 
                response=response, 
                tool_name=tool_name
            )
            metrics.extension_calls += 1
            
            # 8. Tool after execution
            await tool.after_execution(response)
            await self._handle_intervention_optimized(agent, tool_name)
            metrics.intervention_calls += 1
            
            # 9. Calculate metrics
            metrics.execution_time = time.time() - start_time
            metrics.total_overhead = metrics.execution_time - (metrics.extension_calls * 0.001 + metrics.intervention_calls * 0.001)
            
            self._metrics.append(metrics)
            
            return response
            
        except Exception as e:
            PrintStyle(font_color="red").print(f"Tool execution failed: {e}")
            return None
    
    async def _handle_intervention_optimized(self, agent, tool_name: str):
        """Optimized intervention handling with throttling"""
        # Throttle intervention calls per tool
        current_time = time.time()
        throttle_key = f"{agent.agent_name}:{tool_name}"
        
        if throttle_key in self._intervention_throttle:
            last_call = self._intervention_throttle[throttle_key]
            if current_time - last_call < 0.1:  # Throttle to max 10 calls per second
                return
        
        self._intervention_throttle[throttle_key] = current_time
        
        # Only check for pause, skip intervention message handling for performance
        if agent.context.paused:
            while agent.context.paused:
                await asyncio.sleep(0.1)
    
    async def _call_extensions_optimized(self, agent, extension_point: str, **kwargs):
        """Optimized extension calls with throttling"""
        # Throttle extension calls per extension point
        current_time = time.time()
        throttle_key = f"{agent.agent_name}:{extension_point}"
        
        if throttle_key in self._extension_throttle:
            last_call = self._extension_throttle[throttle_key]
            if current_time - last_call < 0.05:  # Throttle to max 20 calls per second
                return
        
        self._extension_throttle[throttle_key] = current_time
        
        # Get cached extensions
        extension_classes = await get_cached_extensions(extension_point, agent.config.profile)
        
        # Execute extensions
        for extension_class in extension_classes:
            try:
                extension = extension_class(agent=agent)
                await extension.execute(**kwargs)
            except Exception as e:
                PrintStyle(font_color="yellow").print(f"Extension {extension_class.__name__} failed: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self._metrics:
            return {"message": "No metrics available"}
        
        total_executions = len(self._metrics)
        avg_execution_time = sum(m.execution_time for m in self._metrics) / total_executions
        avg_overhead = sum(m.total_overhead for m in self._metrics) / total_executions
        cache_hit_rate = sum(1 for m in self._metrics if m.cache_hit) / total_executions * 100
        
        return {
            "total_executions": total_executions,
            "avg_execution_time": f"{avg_execution_time:.3f}s",
            "avg_overhead": f"{avg_overhead:.3f}s",
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "total_intervention_calls": sum(m.intervention_calls for m in self._metrics),
            "total_extension_calls": sum(m.extension_calls for m in self._metrics),
            "performance_improvement": f"~{((1 - avg_overhead/avg_execution_time) * 100):.1f}%"
        }
    
    def clear_metrics(self):
        """Clear performance metrics"""
        self._metrics.clear()
        self._intervention_throttle.clear()
        self._extension_throttle.clear()


# Global optimized executor instance
_optimized_executor = OptimizedToolExecutor()


async def execute_tool_optimized(
    agent, 
    tool_name: str, 
    tool_args: Dict[str, Any], 
    message: str, 
    loop_data: Any = None
) -> Optional[Response]:
    """Execute tool with optimized performance"""
    return await _optimized_executor.execute_tool(agent, tool_name, tool_args, message, loop_data)


def get_tool_performance_stats() -> Dict[str, Any]:
    """Get tool execution performance statistics"""
    return _optimized_executor.get_performance_stats()


def clear_tool_performance_metrics():
    """Clear tool execution performance metrics"""
    _optimized_executor.clear_metrics()
