"""
MCP Manager Tool

Provides comprehensive MCP server management, analytics, and optimization capabilities
for Agent Zero agents.
"""

import asyncio
from python.helpers.tool import Tool, Response
from python.helpers.mcp_analytics import get_mcp_analytics, record_mcp_usage
from python.helpers.mcp_handler import MCPConfig
from python.helpers.print_style import PrintStyle


class MCPManager(Tool):
    """
    Tool for managing MCP servers, analyzing performance, and optimizing tool usage.
    """

    async def execute(self, **kwargs):
        operation = self.args.get("operation", "").lower().strip()

        if operation == "status":
            return await self.get_mcp_status()
        elif operation == "analytics":
            return await self.get_mcp_analytics()
        elif operation == "recommend_tools":
            return await self.recommend_mcp_tools()
        elif operation == "server_info":
            return await self.get_server_info()
        elif operation == "health_check":
            return await self.health_check()
        elif operation == "optimize":
            return await self.optimize_mcp_usage()
        else:
            return await self.show_help()

    async def get_mcp_status(self) -> Response:
        """Get current MCP server status and overview"""
        try:
            analytics = get_mcp_analytics()
            mcp_config = MCPConfig.get_instance()

            # Get server status from analytics
            server_status = analytics.server_status

            if not server_status:
                return Response(
                    message="No MCP servers have been used yet. Use MCP tools to populate this information.",
                    break_loop=False
                )

            result = "## MCP Server Status Overview\n\n"

            for server_name, status in server_status.items():
                success_rate = (status["successful_calls"] / status["total_calls"] * 100) if status["total_calls"] > 0 else 0
                last_seen = status["last_seen"].strftime("%Y-%m-%d %H:%M:%S")

                result += f"### 📡 {server_name}\n"
                result += f"**Total Calls:** {status['total_calls']}\n"
                result += f"**Success Rate:** {success_rate:.1f}%\n"
                result += f"**Last Used:** {last_seen}\n"
                result += f"**First Seen:** {status['first_seen'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            # Add overall statistics
            total_calls = sum(status["total_calls"] for status in server_status.values())
            total_successful = sum(status["successful_calls"] for status in server_status.values())
            overall_success_rate = (total_successful / total_calls * 100) if total_calls > 0 else 0

            result += f"### 📊 Overall Statistics\n"
            result += f"**Active Servers:** {len(server_status)}\n"
            result += f"**Total MCP Calls:** {total_calls}\n"
            result += f"**Overall Success Rate:** {overall_success_rate:.1f}%\n"

            return Response(message=result, break_loop=False)

        except Exception as e:
            return Response(
                message=f"Error getting MCP status: {str(e)}",
                break_loop=False
            )

    async def get_mcp_analytics(self) -> Response:
        """Get comprehensive MCP analytics and performance insights"""
        try:
            analytics = get_mcp_analytics()
            analysis = analytics.analyze_mcp_performance()

            if "message" in analysis:
                return Response(message=analysis["message"], break_loop=False)

            result = "## MCP Performance Analytics\n\n"

            # Summary section
            summary = analysis["summary"]
            result += f"### 📈 Summary\n"
            result += f"**Total Servers:** {summary['total_servers']}\n"
            result += f"**Total Calls:** {summary['total_calls']}\n"
            result += f"**Overall Success Rate:** {summary['overall_success_rate']:.1f}%\n"
            result += f"**Most Active Server:** {summary['most_active_server']}\n\n"

            # Server details
            result += "### 🖥️ Server Performance Details\n"
            for server_name, server_data in analysis["servers"].items():
                health_icon = "✅" if server_data["health_status"] == "healthy" else "⚠️" if server_data["health_status"] == "degraded" else "🔴"
                result += f"**{health_icon} {server_name}**\n"
                result += f"- Success Rate: {server_data['success_rate']:.1f}%\n"
                result += f"- Avg Response Time: {server_data['avg_execution_time']:.2f}s\n"
                result += f"- Uptime: {server_data['uptime_percentage']:.1f}%\n"
                result += f"- Available Tools: {server_data['available_tools']}\n"
                result += f"- Health Status: {server_data['health_status']}\n\n"

            # Recommendations
            if analysis["recommendations"]:
                result += "### 💡 Recommendations\n"
                for rec in analysis["recommendations"]:
                    result += f"- {rec}\n"

            return Response(message=result, break_loop=False)

        except Exception as e:
            return Response(
                message=f"Error getting MCP analytics: {str(e)}",
                break_loop=False
            )

    async def recommend_mcp_tools(self) -> Response:
        """Recommend MCP tools for a specific task"""
        task_description = self.args.get("task", "").strip()

        if not task_description:
            return Response(
                message="Please provide a task description for MCP tool recommendations.",
                break_loop=False
            )

        try:
            analytics = get_mcp_analytics()
            recommendations = analytics.get_mcp_tool_recommendations(task_description, self.agent.agent_name)

            if not recommendations:
                return Response(
                    message=f"No specific MCP tool recommendations found for: {task_description}",
                    break_loop=False
                )

            result = f"## MCP Tool Recommendations for: {task_description}\n\n"

            for i, (tool_name, score, reasoning) in enumerate(recommendations, 1):
                result += f"### {i}. {tool_name}\n"
                result += f"**Confidence:** {score:.1%}\n"
                result += f"**Reasoning:** {reasoning}\n\n"

            result += "💡 **Tip:** Use these tool names with the appropriate MCP server configuration."

            return Response(message=result, break_loop=False)

        except Exception as e:
            return Response(
                message=f"Error generating MCP tool recommendations: {str(e)}",
                break_loop=False
            )

    async def get_server_info(self) -> Response:
        """Get detailed information about a specific MCP server"""
        server_name = self.args.get("server", "").strip()

        if not server_name:
            return Response(
                message="Please specify a server name using the 'server' parameter.",
                break_loop=False
            )

        try:
            analytics = get_mcp_analytics()
            metrics = analytics.get_server_metrics(server_name)
            capabilities = analytics.server_capabilities.get(server_name, {})

            result = f"## MCP Server Details: {server_name}\n\n"

            # Performance metrics
            result += "### 📊 Performance Metrics\n"
            result += f"**Total Calls:** {metrics.total_calls}\n"
            result += f"**Successful Calls:** {metrics.successful_calls}\n"
            result += f"**Failed Calls:** {metrics.failed_calls}\n"
            result += f"**Success Rate:** {metrics.success_rate:.1%}\n"
            result += f"**Average Execution Time:** {metrics.avg_execution_time:.2f}s\n"
            result += f"**Min Execution Time:** {metrics.min_execution_time:.2f}s\n"
            result += f"**Max Execution Time:** {metrics.max_execution_time:.2f}s\n"
            result += f"**Uptime Percentage:** {metrics.uptime_percentage:.1f}%\n"
            result += f"**Connection Type:** {metrics.connection_type}\n"

            if metrics.last_used:
                result += f"**Last Used:** {metrics.last_used.strftime('%Y-%m-%d %H:%M:%S')}\n"

            result += "\n"

            # Available tools
            if metrics.available_tools:
                result += "### 🛠️ Available Tools\n"
                result += f"**Total Tools:** {len(metrics.available_tools)}\n\n"

                if metrics.most_used_tools:
                    result += "**Most Used Tools:**\n"
                    for i, (tool, count) in enumerate(metrics.most_used_tools[:10], 1):
                        result += f"{i}. {tool}: {count} uses\n"
                result += "\n"

            # Server capabilities
            if capabilities:
                result += "### 🔧 Server Capabilities\n"
                result += f"**Version:** {capabilities.get('version', 'Unknown')}\n"
                result += f"**Last Updated:** {capabilities.get('last_updated', 'Unknown')}\n"
                result += f"**Type:** {capabilities.get('type', 'Unknown')}\n\n"

            # Common errors
            if metrics.common_errors:
                result += "### ⚠️ Common Errors\n"
                for i, (error, count) in enumerate(list(metrics.common_errors.items())[:5], 1):
                    result += f"{i}. {error}: {count} occurrences\n"

            return Response(message=result, break_loop=False)

        except Exception as e:
            return Response(
                message=f"Error getting server info: {str(e)}",
                break_loop=False
            )

    async def health_check(self) -> Response:
        """Perform comprehensive health check of MCP servers"""
        try:
            analytics = get_mcp_analytics()
            analysis = analytics.analyze_mcp_performance()

            if "message" in analysis:
                return Response(message=analysis["message"], break_loop=False)

            result = "## MCP Health Check Report\n\n"

            # Overall health assessment
            overall_success = analysis["summary"]["overall_success_rate"]
            if overall_success >= 95:
                health_status = "✅ EXCELLENT"
                health_color = "green"
            elif overall_success >= 85:
                health_status = "✅ GOOD"
                health_color = "blue"
            elif overall_success >= 70:
                health_status = "⚠️ FAIR"
                health_color = "yellow"
            else:
                health_status = "🔴 POOR"
                health_color = "red"

            result += f"### 🏥 Overall Health Status: {health_status}\n"
            result += f"**Success Rate:** {overall_success:.1f}%\n"
            result += f"**Active Servers:** {analysis['summary']['total_servers']}\n\n"

            # Individual server health
            result += "### 🖥️ Server Health Details\n"
            unhealthy_servers = 0
            degraded_servers = 0

            for server_name, server_data in analysis["servers"].items():
                status = server_data["health_status"]
                if status == "unhealthy":
                    unhealthy_servers += 1
                    result += f"🔴 **{server_name}**: UNHEALTHY (Success: {server_data['success_rate']:.1f}%)\n"
                elif status == "degraded":
                    degraded_servers += 1
                    result += f"⚠️ **{server_name}**: DEGRADED (Success: {server_data['success_rate']:.1f}%)\n"
                else:
                    result += f"✅ **{server_name}**: HEALTHY (Success: {server_data['success_rate']:.1f}%)\n"

            # Health summary
            result += f"\n### 📋 Health Summary\n"
            result += f"**Healthy Servers:** {analysis['summary']['total_servers'] - unhealthy_servers - degraded_servers}\n"
            result += f"**Degraded Servers:** {degraded_servers}\n"
            result += f"**Unhealthy Servers:** {unhealthy_servers}\n"

            # Recommendations based on health
            result += f"\n### 💡 Health Recommendations\n"
            if unhealthy_servers > 0:
                result += "- 🔴 Immediate attention required for unhealthy servers\n"
            if degraded_servers > 0:
                result += "- ⚠️ Monitor degraded servers for performance issues\n"
            if overall_success < 90:
                result += "- 📉 Consider reviewing MCP server configurations\n"
            if analysis['summary']['total_servers'] < 3:
                result += "- 🔧 Consider adding more MCP servers for redundancy\n"

            return Response(message=result, break_loop=False)

        except Exception as e:
            return Response(
                message=f"Error performing health check: {str(e)}",
                break_loop=False
            )

    async def optimize_mcp_usage(self) -> Response:
        """Provide optimization recommendations for MCP usage"""
        try:
            analytics = get_mcp_analytics()
            analysis = analytics.analyze_mcp_performance()

            if "message" in analysis:
                return Response(message=analysis["message"], break_loop=False)

            result = "## MCP Usage Optimization Report\n\n"

            # Usage patterns analysis
            result += "### 📊 Usage Pattern Analysis\n"
            total_calls = analysis["summary"]["total_calls"]

            if total_calls == 0:
                result += "No MCP usage data available. Start using MCP tools to generate optimization insights.\n"
                return Response(message=result, break_loop=False)

            # Server usage distribution
            result += "**Server Usage Distribution:**\n"
            for server_name, server_data in analysis["servers"].items():
                usage_percentage = (server_data["total_calls"] / total_calls * 100)
                result += f"- {server_name}: {usage_percentage:.1f}% ({server_data['total_calls']} calls)\n"

            result += "\n"

            # Performance optimization opportunities
            result += "### 🚀 Optimization Opportunities\n"

            # Identify slow servers
            slow_servers = [
                (name, data) for name, data in analysis["servers"].items()
                if data["avg_execution_time"] > 3.0
            ]

            if slow_servers:
                result += "**⏱️ Slow Performing Servers:**\n"
                for server_name, server_data in slow_servers:
                    result += f"- {server_name}: {server_data['avg_execution_time']:.2f}s average\n"
                result += "\n"

            # Identify unreliable servers
            unreliable_servers = [
                (name, data) for name, data in analysis["servers"].items()
                if data["success_rate"] < 0.9
            ]

            if unreliable_servers:
                result += "**🔴 Unreliable Servers:**\n"
                for server_name, server_data in unreliable_servers:
                    result += f"- {server_name}: {server_data['success_rate']:.1%} success rate\n"
                result += "\n"

            # Underutilized servers
            underutilized = [
                (name, data) for name, data in analysis["servers"].items()
                if data["total_calls"] < 10
            ]

            if underutilized:
                result += "**📉 Underutilized Servers:**\n"
                for server_name, server_data in underutilized:
                    result += f"- {server_name}: Only {server_data['total_calls']} calls\n"
                result += "\n"

            # Recommendations
            result += "### 💡 Optimization Recommendations\n"
            recommendations = analysis.get("recommendations", [])
            for rec in recommendations:
                result += f"- {rec}\n"

            # Best practices
            result += "\n### ✨ Best Practices\n"
            result += "- Monitor MCP server performance regularly\n"
            result += "- Use MCP tools for tasks that require external integrations\n"
            result += "- Balance load between multiple MCP servers\n"
            result += "- Set up alerts for server health degradation\n"
            result += "- Document successful MCP tool patterns for reuse\n"

            return Response(message=result, break_loop=False)

        except Exception as e:
            return Response(
                message=f"Error generating optimization report: {str(e)}",
                break_loop=False
            )

    async def show_help(self) -> Response:
        """Show help information for the MCP Manager tool"""
        help_text = """
## MCP Manager Tool

This tool provides comprehensive MCP server management, analytics, and optimization capabilities.

### Available Operations:

1. **status** - Get current MCP server status and overview
   - No parameters required

2. **analytics** - Get comprehensive MCP analytics and performance insights
   - No parameters required

3. **recommend_tools** - Recommend MCP tools for a specific task
   - task: Description of the task you need to accomplish

4. **server_info** - Get detailed information about a specific MCP server
   - server: Name of the MCP server

5. **health_check** - Perform comprehensive health check of MCP servers
   - No parameters required

6. **optimize** - Provide optimization recommendations for MCP usage
   - No parameters required

### Examples:

**Get MCP status:**
```json
{
  "operation": "status"
}
```

**Get performance analytics:**
```json
{
  "operation": "analytics"
}
```

**Get tool recommendations:**
```json
{
  "operation": "recommend_tools",
  "task": "Search for web development tutorials and save them to memory"
}
```

**Get server information:**
```json
{
  "operation": "server_info",
  "server": "filesystem"
}
```

**Perform health check:**
```json
{
  "operation": "health_check"
}
```

**Get optimization recommendations:**
```json
{
  "operation": "optimize"
}
```

Use this tool to monitor MCP server health, analyze usage patterns, and optimize your MCP tool integration strategy.
        """

        return Response(message=help_text, break_loop=False)