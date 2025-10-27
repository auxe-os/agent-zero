"""
Tool Analytics and Performance Tracking System for Agent Zero

This module provides comprehensive tool usage tracking, performance monitoring,
and intelligent tool selection recommendations.
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

from python.helpers.print_style import PrintStyle


@dataclass
class ToolUsageRecord:
    """Record of a single tool usage event"""
    tool_name: str
    agent_name: str
    timestamp: datetime
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    args: Optional[Dict[str, Any]] = None
    result_length: int = 0
    task_context: Optional[str] = None


@dataclass
class ToolPerformanceMetrics:
    """Performance metrics for a specific tool"""
    total_uses: int
    successful_uses: int
    failed_uses: int
    avg_execution_time: float
    min_execution_time: float
    max_execution_time: float
    success_rate: float
    last_used: Optional[datetime]
    most_used_by_agents: List[Tuple[str, int]]
    common_error_patterns: Dict[str, int]
    avg_result_length: float


@dataclass
class ToolCategory:
    """Tool categorization and metadata"""
    name: str
    description: str
    keywords: List[str]
    capabilities: List[str]
    typical_use_cases: List[str]
    agent_preferences: Dict[str, float]  # agent name -> preference score
    prerequisites: List[str]  # tools that should be used before this one
    related_tools: List[str]
    complexity_score: float  # 0-1, higher = more complex


class ToolAnalytics:
    """Main analytics class for tool usage tracking and insights"""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else Path("memory/tool_analytics.json")
        self.usage_records: List[ToolUsageRecord] = []
        self.tool_categories: Dict[str, ToolCategory] = {}
        self.agent_preferences: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._lock = threading.Lock()

        # Load existing data
        self.load_analytics_data()
        self.initialize_tool_categories()

    def record_tool_usage(self, tool_name: str, agent_name: str, execution_time: float,
                         success: bool, error_message: Optional[str] = None,
                         args: Optional[Dict[str, Any]] = None, result_length: int = 0,
                         task_context: Optional[str] = None) -> None:
        """Record a tool usage event"""
        with self._lock:
            record = ToolUsageRecord(
                tool_name=tool_name,
                agent_name=agent_name,
                timestamp=datetime.now(),
                execution_time=execution_time,
                success=success,
                error_message=error_message,
                args=args,
                result_length=result_length,
                task_context=task_context
            )
            self.usage_records.append(record)

            # Update agent preferences
            if success:
                self.agent_preferences[agent_name][tool_name] += 1.0

            # Save periodically
            if len(self.usage_records) % 10 == 0:
                self.save_analytics_data()

    def get_tool_metrics(self, tool_name: str, days: int = 30) -> ToolPerformanceMetrics:
        """Get performance metrics for a specific tool"""
        cutoff_date = datetime.now() - timedelta(days=days)
        relevant_records = [
            r for r in self.usage_records
            if r.tool_name == tool_name and r.timestamp >= cutoff_date
        ]

        if not relevant_records:
            return ToolPerformanceMetrics(
                total_uses=0, successful_uses=0, failed_uses=0,
                avg_execution_time=0.0, min_execution_time=0.0, max_execution_time=0.0,
                success_rate=0.0, last_used=None, most_used_by_agents=[],
                common_error_patterns={}, avg_result_length=0.0
            )

        successful_records = [r for r in relevant_records if r.success]
        failed_records = [r for r in relevant_records if not r.success]

        execution_times = [r.execution_time for r in relevant_records]
        agent_usage = Counter(r.agent_name for r in relevant_records)
        error_patterns = Counter(r.error_message for r in failed_records if r.error_message)
        result_lengths = [r.result_length for r in successful_records]

        return ToolPerformanceMetrics(
            total_uses=len(relevant_records),
            successful_uses=len(successful_records),
            failed_uses=len(failed_records),
            avg_execution_time=statistics.mean(execution_times),
            min_execution_time=min(execution_times),
            max_execution_time=max(execution_times),
            success_rate=len(successful_records) / len(relevant_records),
            last_used=max(r.timestamp for r in relevant_records),
            most_used_by_agents=agent_usage.most_common(5),
            common_error_patterns=dict(error_patterns.most_common(10)),
            avg_result_length=statistics.mean(result_lengths) if result_lengths else 0.0
        )

    def recommend_tools_for_task(self, task_description: str, agent_name: str,
                                limit: int = 5) -> List[Tuple[str, float]]:
        """Recommend tools for a given task based on historical usage and tool categories"""
        task_lower = task_description.lower()
        tool_scores = defaultdict(float)

        # Score based on tool categories and keywords
        for tool_name, category in self.tool_categories.items():
            score = 0.0

            # Keyword matching
            for keyword in category.keywords:
                if keyword in task_lower:
                    score += 0.3

            # Capability matching
            for capability in category.capabilities:
                if capability in task_lower:
                    score += 0.2

            # Use case matching
            for use_case in category.typical_use_cases:
                if use_case in task_lower:
                    score += 0.4

            # Agent preference
            agent_pref = self.agent_preferences[agent_name].get(tool_name, 0)
            if agent_pref > 0:
                # Normalize agent preference
                max_pref = max(self.agent_preferences[agent_name].values()) if self.agent_preferences[agent_name] else 1
                score += (agent_pref / max_pref) * 0.3

            # Tool performance bonus
            metrics = self.get_tool_metrics(tool_name)
            if metrics.success_rate > 0.8:
                score += 0.2
            if metrics.avg_execution_time < 5.0:
                score += 0.1

            tool_scores[tool_name] = score

        # Sort by score and return top recommendations
        recommendations = sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)
        return recommendations[:limit]

    def get_agent_tool_insights(self, agent_name: str) -> Dict[str, Any]:
        """Get insights about an agent's tool usage patterns"""
        agent_records = [r for r in self.usage_records if r.agent_name == agent_name]

        if not agent_records:
            return {"message": "No tool usage records found for this agent"}

        # Tool usage frequency
        tool_usage = Counter(r.tool_name for r in agent_records)

        # Success rates by tool
        tool_success_rates = {}
        for tool_name in tool_usage:
            tool_records = [r for r in agent_records if r.tool_name == tool_name]
            successful = sum(1 for r in tool_records if r.success)
            tool_success_rates[tool_name] = successful / len(tool_records)

        # Performance patterns
        recent_records = [r for r in agent_records if r.timestamp >= datetime.now() - timedelta(days=7)]
        performance_trend = "stable"
        if len(recent_records) >= 10:
            recent_success_rate = sum(1 for r in recent_records if r.success) / len(recent_records)
            overall_success_rate = sum(1 for r in agent_records if r.success) / len(agent_records)
            if recent_success_rate > overall_success_rate + 0.1:
                performance_trend = "improving"
            elif recent_success_rate < overall_success_rate - 0.1:
                performance_trend = "declining"

        return {
            "total_tool_uses": len(agent_records),
            "unique_tools_used": len(tool_usage),
            "most_used_tools": tool_usage.most_common(10),
            "tool_success_rates": tool_success_rates,
            "performance_trend": performance_trend,
            "recent_activity": len(recent_records)
        }

    def initialize_tool_categories(self) -> None:
        """Initialize default tool categories based on available tools"""
        default_categories = {
            "code_execution": ToolCategory(
                name="Code Execution",
                description="Execute code in various runtime environments",
                keywords=["code", "execute", "run", "python", "node", "terminal", "bash"],
                capabilities=["code_execution", "file_operations", "system_commands"],
                typical_use_cases=[
                    "run python code", "execute script", "run terminal command",
                    "compile code", "test program", "debug code"
                ],
                agent_preferences={
                    "developer": 0.9,
                    "hacker": 0.8,
                    "researcher": 0.6,
                    "agent0": 0.5
                },
                prerequisites=[],
                related_tools=["search_engine", "memory_save"],
                complexity_score=0.7
            ),

            "search_engine": ToolCategory(
                name="Search Engine",
                description="Search the web for information",
                keywords=["search", "web", "find", "lookup", "google", "information"],
                capabilities=["web_search", "information_retrieval", "research"],
                typical_use_cases=[
                    "search online", "find information", "research topic",
                    "look up documentation", "find examples"
                ],
                agent_preferences={
                    "researcher": 0.9,
                    "developer": 0.7,
                    "hacker": 0.6,
                    "agent0": 0.8
                },
                prerequisites=[],
                related_tools=["memory_save", "code_execution"],
                complexity_score=0.3
            ),

            "memory_load": ToolCategory(
                name="Memory Retrieval",
                description="Retrieve information from long-term memory",
                keywords=["memory", "recall", "remember", "load", "retrieve"],
                capabilities=["memory_search", "information_retrieval", "knowledge_recall"],
                typical_use_cases=[
                    "recall previous information", "load memories", "search memory",
                    "retrieve knowledge", "access past conversations"
                ],
                agent_preferences={
                    "agent0": 0.9,
                    "researcher": 0.8,
                    "developer": 0.7,
                    "hacker": 0.6
                },
                prerequisites=[],
                related_tools=["memory_save", "search_engine"],
                complexity_score=0.2
            ),

            "memory_save": ToolCategory(
                name="Memory Storage",
                description="Save information to long-term memory",
                keywords=["save", "store", "memorize", "remember"],
                capabilities=["memory_storage", "information_persistence", "knowledge_retention"],
                typical_use_cases=[
                    "save important information", "store knowledge", "memorize",
                    "keep for later", "save to memory"
                ],
                agent_preferences={
                    "agent0": 0.9,
                    "researcher": 0.8,
                    "developer": 0.7,
                    "hacker": 0.6
                },
                prerequisites=[],
                related_tools=["memory_load", "search_engine"],
                complexity_score=0.2
            ),

            "call_subordinate": ToolCategory(
                name="Agent Delegation",
                description="Delegate tasks to specialized subordinate agents",
                keywords=["delegate", "subordinate", "agent", "assign", "help"],
                capabilities=["task_delegation", "agent_orchestration", "parallel_processing"],
                typical_use_cases=[
                    "delegate task", "get help", "use specialized agent",
                    "parallel processing", "divide and conquer"
                ],
                agent_preferences={
                    "agent0": 0.9,
                    "developer": 0.8,
                    "researcher": 0.7,
                    "hacker": 0.6
                },
                prerequisites=[],
                related_tools=["memory_save", "search_engine"],
                complexity_score=0.8
            ),

            "browser": ToolCategory(
                name="Browser Automation",
                description="Automate web browser interactions",
                keywords=["browser", "web", "scrape", "click", "navigate", "selenium"],
                capabilities=["web_automation", "browser_control", "web_scraping"],
                typical_use_cases=[
                    "automate browser", "scrape website", "fill forms",
                    "navigate web pages", "take screenshots"
                ],
                agent_preferences={
                    "hacker": 0.9,
                    "researcher": 0.8,
                    "developer": 0.7,
                    "agent0": 0.6
                },
                prerequisites=[],
                related_tools=["search_engine", "memory_save"],
                complexity_score=0.8
            )
        }

        self.tool_categories.update(default_categories)

    def save_analytics_data(self) -> None:
        """Save analytics data to persistent storage"""
        try:
            # Create directory if it doesn't exist
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert records to serializable format
            data = {
                "usage_records": [
                    {
                        "tool_name": r.tool_name,
                        "agent_name": r.agent_name,
                        "timestamp": r.timestamp.isoformat(),
                        "execution_time": r.execution_time,
                        "success": r.success,
                        "error_message": r.error_message,
                        "args": r.args,
                        "result_length": r.result_length,
                        "task_context": r.task_context
                    }
                    for r in self.usage_records
                ],
                "agent_preferences": dict(self.agent_preferences)
            }

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            PrintStyle(font_color="red", background_color="black", padding=True).print(
                f"Failed to save analytics data: {e}"
            )

    def load_analytics_data(self) -> None:
        """Load analytics data from persistent storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)

                # Load usage records
                self.usage_records = [
                    ToolUsageRecord(
                        tool_name=r["tool_name"],
                        agent_name=r["agent_name"],
                        timestamp=datetime.fromisoformat(r["timestamp"]),
                        execution_time=r["execution_time"],
                        success=r["success"],
                        error_message=r.get("error_message"),
                        args=r.get("args"),
                        result_length=r.get("result_length", 0),
                        task_context=r.get("task_context")
                    )
                    for r in data.get("usage_records", [])
                ]

                # Load agent preferences
                self.agent_preferences = defaultdict(lambda: defaultdict(float))
                for agent_name, preferences in data.get("agent_preferences", {}).items():
                    self.agent_preferences[agent_name] = defaultdict(float, preferences)

                PrintStyle(font_color="green", padding=True).print(
                    f"Loaded {len(self.usage_records)} tool usage records"
                )
        except Exception as e:
            PrintStyle(font_color="yellow", background_color="black", padding=True).print(
                f"Failed to load analytics data: {e}. Starting fresh."
            )


# Global instance
_tool_analytics: Optional[ToolAnalytics] = None


def get_tool_analytics() -> ToolAnalytics:
    """Get the global tool analytics instance"""
    global _tool_analytics
    if _tool_analytics is None:
        _tool_analytics = ToolAnalytics()
    return _tool_analytics


def record_tool_usage(tool_name: str, agent_name: str, execution_time: float,
                     success: bool, error_message: Optional[str] = None,
                     args: Optional[Dict[str, Any]] = None, result_length: int = 0,
                     task_context: Optional[str] = None) -> None:
    """Convenience function to record tool usage"""
    analytics = get_tool_analytics()
    analytics.record_tool_usage(
        tool_name=tool_name,
        agent_name=agent_name,
        execution_time=execution_time,
        success=success,
        error_message=error_message,
        args=args,
        result_length=result_length,
        task_context=task_context
    )