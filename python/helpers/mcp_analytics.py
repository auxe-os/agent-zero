"""
MCP Analytics and Management System for Agent Zero

This module provides comprehensive MCP server analytics, performance tracking,
and intelligent MCP tool management capabilities.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import threading
from pathlib import Path
import statistics
import asyncio

from python.helpers.print_style import PrintStyle


@dataclass
class MCPUsageRecord:
    """Record of MCP tool usage"""
    server_name: str
    tool_name: str
    agent_name: str
    timestamp: datetime
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    args: Optional[Dict[str, Any]] = None
    result_length: int = 0


@dataclass
class MCPServerMetrics:
    """Performance metrics for an MCP server"""
    server_name: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    avg_execution_time: float
    min_execution_time: float
    max_execution_time: float
    success_rate: float
    last_used: Optional[datetime]
    available_tools: List[str]
    most_used_tools: List[Tuple[str, int]]
    common_errors: Dict[str, int]
    uptime_percentage: float
    connection_type: str  # "stdio" or "remote"


class MCPAnalytics:
    """Main analytics class for MCP server usage tracking and insights"""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else Path("memory/mcp_analytics.json")
        self.usage_records: List[MCPUsageRecord] = []
        self.server_status: Dict[str, Dict[str, Any]] = {}
        self.server_capabilities: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        # Load existing data
        self.load_analytics_data()

    def record_mcp_usage(self, server_name: str, tool_name: str, agent_name: str,
                        execution_time: float, success: bool, error_message: Optional[str] = None,
                        args: Optional[Dict[str, Any]] = None, result_length: int = 0) -> None:
        """Record an MCP tool usage event"""
        with self._lock:
            record = MCPUsageRecord(
                server_name=server_name,
                tool_name=tool_name,
                agent_name=agent_name,
                timestamp=datetime.now(),
                execution_time=execution_time,
                success=success,
                error_message=error_message,
                args=args,
                result_length=result_length
            )
            self.usage_records.append(record)

            # Update server status
            if server_name not in self.server_status:
                self.server_status[server_name] = {
                    "first_seen": datetime.now(),
                    "last_seen": datetime.now(),
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0
                }

            self.server_status[server_name]["last_seen"] = datetime.now()
            self.server_status[server_name]["total_calls"] += 1
            if success:
                self.server_status[server_name]["successful_calls"] += 1
            else:
                self.server_status[server_name]["failed_calls"] += 1

            # Save periodically
            if len(self.usage_records) % 10 == 0:
                self.save_analytics_data()

    def get_server_metrics(self, server_name: str, days: int = 30) -> MCPServerMetrics:
        """Get performance metrics for a specific MCP server"""
        cutoff_date = datetime.now() - timedelta(days=days)
        relevant_records = [
            r for r in self.usage_records
            if r.server_name == server_name and r.timestamp >= cutoff_date
        ]

        if not relevant_records:
            return MCPServerMetrics(
                server_name=server_name,
                total_calls=0, successful_calls=0, failed_calls=0,
                avg_execution_time=0.0, min_execution_time=0.0, max_execution_time=0.0,
                success_rate=0.0, last_used=None, available_tools=[],
                most_used_tools=[], common_errors={}, uptime_percentage=0.0,
                connection_type="unknown"
            )

        successful_records = [r for r in relevant_records if r.success]
        failed_records = [r for r in relevant_records if not r.success]

        execution_times = [r.execution_time for r in relevant_records]
        tool_usage = Counter(r.tool_name for r in relevant_records)
        error_patterns = Counter(r.error_message for r in failed_records if r.error_message)

        # Calculate uptime percentage
        total_time = (datetime.now() - min(r.timestamp for r in relevant_records)).total_seconds()
        successful_time = sum(r.execution_time for r in successful_records)
        uptime_percentage = (successful_time / total_time * 100) if total_time > 0 else 0.0

        return MCPServerMetrics(
            server_name=server_name,
            total_calls=len(relevant_records),
            successful_calls=len(successful_records),
            failed_calls=len(failed_records),
            avg_execution_time=statistics.mean(execution_times),
            min_execution_time=min(execution_times),
            max_execution_time=max(execution_times),
            success_rate=len(successful_records) / len(relevant_records),
            last_used=max(r.timestamp for r in relevant_records),
            available_tools=self.server_capabilities.get(server_name, {}).get("tools", []),
            most_used_tools=tool_usage.most_common(10),
            common_errors=dict(error_patterns.most_common(10)),
            uptime_percentage=uptime_percentage,
            connection_type=self.server_capabilities.get(server_name, {}).get("type", "unknown")
        )

    def analyze_mcp_performance(self) -> Dict[str, Any]:
        """Analyze overall MCP performance and provide insights"""
        if not self.server_status:
            return {"message": "No MCP servers have been used yet"}

        analysis = {
            "summary": {
                "total_servers": len(self.server_status),
                "total_calls": sum(status["total_calls"] for status in self.server_status.values()),
                "overall_success_rate": 0.0,
                "most_active_server": None,
                "performance_trends": {}
            },
            "servers": {},
            "recommendations": []
        }

        # Calculate overall success rate
        total_successful = sum(status["successful_calls"] for status in self.server_status.values())
        total_calls = sum(status["total_calls"] for status in self.server_status.values())
        analysis["summary"]["overall_success_rate"] = (total_successful / total_calls * 100) if total_calls > 0 else 0.0

        # Find most active server
        most_active = max(self.server_status.items(), key=lambda x: x[1]["total_calls"])
        analysis["summary"]["most_active_server"] = most_active[0]

        # Analyze each server
        for server_name in self.server_status:
            metrics = self.get_server_metrics(server_name)
            analysis["servers"][server_name] = {
                "total_calls": metrics.total_calls,
                "success_rate": metrics.success_rate * 100,
                "avg_execution_time": metrics.avg_execution_time,
                "uptime_percentage": metrics.uptime_percentage,
                "available_tools": len(metrics.available_tools),
                "health_status": "healthy"
            }

            # Determine health status
            if metrics.success_rate < 0.8:
                analysis["servers"][server_name]["health_status"] = "unhealthy"
            elif metrics.success_rate < 0.95:
                analysis["servers"][server_name]["health_status"] = "degraded"

        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)

        return analysis

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations based on analysis"""
        recommendations = []

        # Overall success rate recommendations
        if analysis["summary"]["overall_success_rate"] < 80:
            recommendations.append(
                "⚠️ Overall MCP success rate is below 80%. Check server configurations and network connectivity."
            )
        elif analysis["summary"]["overall_success_rate"] < 95:
            recommendations.append(
                "ℹ️ MCP success rate could be improved. Monitor for recurring errors."
            )

        # Server-specific recommendations
        for server_name, server_data in analysis["servers"].items():
            if server_data["health_status"] == "unhealthy":
                recommendations.append(
                    f"🔴 Server '{server_name}' is unhealthy with {server_data['success_rate']:.1f}% success rate."
                )
            elif server_data["avg_execution_time"] > 5.0:
                recommendations.append(
                    f"⏱️ Server '{server_name}' has slow response times ({server_data['avg_execution_time']:.1f}s average)."
                )
            elif server_data["uptime_percentage"] < 80:
                recommendations.append(
                    f"📉 Server '{server_name}' has low uptime ({server_data['uptime_percentage']:.1f}%)."
                )

        # Tool usage recommendations
        total_tools = sum(server_data["available_tools"] for server_data in analysis["servers"].values())
        if total_tools < 5:
            recommendations.append(
                "🔧 Consider adding more MCP servers to expand tool capabilities."
            )

        if not recommendations:
            recommendations.append("✅ MCP system is performing well with no critical issues detected.")

        return recommendations

    def update_server_capabilities(self, server_name: str, capabilities: Dict[str, Any]) -> None:
        """Update server capabilities information"""
        self.server_capabilities[server_name] = {
            "last_updated": datetime.now(),
            "tools": [tool.get("name", "") for tool in capabilities.get("tools", [])],
            "type": capabilities.get("server_type", "unknown"),
            "version": capabilities.get("version", "unknown"),
            "capabilities": capabilities
        }

    def get_mcp_tool_recommendations(self, task_description: str,
                                   agent_name: str) -> List[Tuple[str, float, str]]:
        """Recommend MCP tools for a given task"""
        task_lower = task_description.lower()
        recommendations = []

        # Analyze available MCP tools
        for server_name, server_data in self.server_capabilities.items():
            tools = server_data.get("tools", [])
            for tool in tools:
                score = self._calculate_tool_score(task_lower, tool, server_name, agent_name)
                if score > 0.3:  # Only include meaningful matches
                    full_tool_name = f"{server_name}:{tool}"
                    reasoning = f"MCP tool from {server_name} server"
                    recommendations.append((full_tool_name, score, reasoning))

        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:5]

    def _calculate_tool_score(self, task_lower: str, tool_name: str,
                            server_name: str, agent_name: str) -> float:
        """Calculate score for how well an MCP tool matches the task"""
        score = 0.0
        tool_lower = tool_name.lower()

        # Keyword matching
        task_keywords = task_lower.split()
        tool_keywords = tool_lower.split('_')

        matches = sum(1 for tk in task_keywords for tk2 in tool_keywords if tk in tk2)
        if matches > 0:
            score += (matches / max(len(task_keywords), len(tool_keywords))) * 0.4

        # Function-based matching
        if any(word in tool_lower for word in ["search", "find", "query", "lookup"]):
            if any(word in task_lower for word in ["search", "find", "lookup", "research"]):
                score += 0.3

        if any(word in tool_lower for word in ["create", "make", "generate", "build"]):
            if any(word in task_lower for word in ["create", "make", "build", "generate"]):
                score += 0.3

        if any(word in tool_lower for word in ["read", "get", "fetch", "load"]):
            if any(word in task_lower for word in ["read", "get", "fetch", "load", "retrieve"]):
                score += 0.3

        # Server performance bonus
        if server_name in self.server_status:
            status = self.server_status[server_name]
            if status["total_calls"] > 0:
                success_rate = status["successful_calls"] / status["total_calls"]
                if success_rate > 0.9:
                    score += 0.2

        return min(score, 1.0)

    def save_analytics_data(self) -> None:
        """Save analytics data to persistent storage"""
        try:
            # Create directory if it doesn't exist
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert records to serializable format
            data = {
                "usage_records": [
                    {
                        "server_name": r.server_name,
                        "tool_name": r.tool_name,
                        "agent_name": r.agent_name,
                        "timestamp": r.timestamp.isoformat(),
                        "execution_time": r.execution_time,
                        "success": r.success,
                        "error_message": r.error_message,
                        "args": r.args,
                        "result_length": r.result_length
                    }
                    for r in self.usage_records
                ],
                "server_status": {
                    name: {
                        **status,
                        "first_seen": status["first_seen"].isoformat(),
                        "last_seen": status["last_seen"].isoformat()
                    }
                    for name, status in self.server_status.items()
                },
                "server_capabilities": {
                    name: {
                        **capabilities,
                        "last_updated": capabilities["last_updated"].isoformat()
                    }
                    for name, capabilities in self.server_capabilities.items()
                }
            }

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            PrintStyle(font_color="red", background_color="black", padding=True).print(
                f"Failed to save MCP analytics data: {e}"
            )

    def load_analytics_data(self) -> None:
        """Load analytics data from persistent storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)

                # Load usage records
                self.usage_records = [
                    MCPUsageRecord(
                        server_name=r["server_name"],
                        tool_name=r["tool_name"],
                        agent_name=r["agent_name"],
                        timestamp=datetime.fromisoformat(r["timestamp"]),
                        execution_time=r["execution_time"],
                        success=r["success"],
                        error_message=r.get("error_message"),
                        args=r.get("args"),
                        result_length=r.get("result_length", 0)
                    )
                    for r in data.get("usage_records", [])
                ]

                # Load server status
                for name, status in data.get("server_status", {}).items():
                    self.server_status[name] = {
                        "first_seen": datetime.fromisoformat(status["first_seen"]),
                        "last_seen": datetime.fromisoformat(status["last_seen"]),
                        "total_calls": status["total_calls"],
                        "successful_calls": status["successful_calls"],
                        "failed_calls": status["failed_calls"]
                    }

                # Load server capabilities
                for name, capabilities in data.get("server_capabilities", {}).items():
                    self.server_capabilities[name] = {
                        **capabilities,
                        "last_updated": datetime.fromisoformat(capabilities["last_updated"])
                    }

                PrintStyle(font_color="green", padding=True).print(
                    f"Loaded {len(self.usage_records)} MCP usage records for {len(self.server_status)} servers"
                )
        except Exception as e:
            PrintStyle(font_color="yellow", background_color="black", padding=True).print(
                f"Failed to load MCP analytics data: {e}. Starting fresh."
            )


# Global instance
_mcp_analytics: Optional[MCPAnalytics] = None


def get_mcp_analytics() -> MCPAnalytics:
    """Get the global MCP analytics instance"""
    global _mcp_analytics
    if _mcp_analytics is None:
        _mcp_analytics = MCPAnalytics()
    return _mcp_analytics


def record_mcp_usage(server_name: str, tool_name: str, agent_name: str,
                    execution_time: float, success: bool, error_message: Optional[str] = None,
                    args: Optional[Dict[str, Any]] = None, result_length: int = 0) -> None:
    """Convenience function to record MCP tool usage"""
    analytics = get_mcp_analytics()
    analytics.record_mcp_usage(
        server_name=server_name,
        tool_name=tool_name,
        agent_name=agent_name,
        execution_time=execution_time,
        success=success,
        error_message=error_message,
        args=args,
        result_length=result_length
    )


def update_mcp_capabilities(server_name: str, capabilities: Dict[str, Any]) -> None:
    """Convenience function to update MCP server capabilities"""
    analytics = get_mcp_analytics()
    analytics.update_server_capabilities(server_name, capabilities)