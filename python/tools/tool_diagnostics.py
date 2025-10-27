"""
Tool Diagnostics Tool
Helps diagnose and fix tool calling issues
"""
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
import json
from typing import Dict, Any, List


class ToolDiagnostics(Tool):
    """Tool for diagnosing tool calling issues"""
    
    async def execute(self, action="list_tools", **kwargs):
        """Execute tool diagnostics actions"""
        
        if action == "list_tools":
            return await self._list_available_tools()
        elif action == "check_mcp":
            return await self._check_mcp_tools()
        elif action == "test_tool":
            tool_name = kwargs.get("tool_name", "")
            return await self._test_tool(tool_name)
        elif action == "diagnose_issue":
            return await self._diagnose_tool_calling_issue()
        elif action == "validate_tools":
            return await self._validate_all_tools()
        elif action == "validate_instructions":
            return await self._validate_tool_instructions()
        else:
            return Response(
                message="Invalid action. Available actions: list_tools, check_mcp, test_tool, diagnose_issue, validate_tools, get_recommendations, validate_instructions",
                break_loop=False
            )
    
    async def _list_available_tools(self) -> Response:
        """List all available tools using unified discovery"""
        try:
            from python.helpers.extract_tools import discover_tools, validate_tool_discovery
            
            # Use unified tool discovery
            discovered_tools = discover_tools(self.agent.config.profile)
            validation = validate_tool_discovery(discovered_tools)
            
            # Categorize tools
            local_tools = []
            agent_tools = []
            mcp_tools = []
            
            for tool_name, tool_info in discovered_tools.items():
                if tool_info["type"] == "local":
                    local_tools.append(tool_name)
                elif tool_info["type"] == "agent_specific":
                    agent_tools.append(tool_name)
                elif tool_info["type"] == "mcp":
                    mcp_tools.append(tool_name)
            
            tools_report = f"""
🔧 **Enhanced Tool Discovery Report**

**Local Tools ({len(local_tools)}):**
{chr(10).join(f"  • {tool}" for tool in sorted(local_tools))}

**Agent-Specific Tools ({len(agent_tools)}):**
{chr(10).join(f"  • {tool}" for tool in sorted(agent_tools))}

**MCP Tools ({len(mcp_tools)}):**
{chr(10).join(f"  • {tool}" for tool in sorted(mcp_tools))}

**Total Tools Available:** {validation['total_tools']}

**Validation Results:**
- Local Tools: {validation['local_tools']}
- Agent-Specific Tools: {validation['agent_specific_tools']}
- MCP Tools: {validation['mcp_tools']}

**Errors Found:** {len(validation['errors'])}
{chr(10).join(f"  • {error}" for error in validation['errors'])}

**Recommendations:**
{chr(10).join(f"  • {rec}" for rec in validation['recommendations'])}
"""
            
            return Response(message=tools_report.strip(), break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"Error listing tools: {e}",
                break_loop=False
            )
    
    async def _validate_all_tools(self) -> Response:
        """Validate all discovered tools"""
        try:
            from python.helpers.extract_tools import discover_tools
            
            discovered_tools = discover_tools(self.agent.config.profile)
            validation_results = []
            
            for tool_name, tool_info in discovered_tools.items():
                if tool_info["type"] in ["local", "agent_specific"]:
                    try:
                        tool_class = tool_info.get("class")
                        if tool_class:
                            # Create a temporary tool instance for validation
                            temp_tool = tool_class(
                                agent=self.agent,
                                name=tool_name,
                                method=None,
                                args={},
                                message="",
                                loop_data=None
                            )
                            validation = temp_tool.validate_tool()
                            
                            validation_results.append({
                                "tool": tool_name,
                                "valid": validation.is_valid,
                                "errors": validation.errors,
                                "warnings": validation.warnings,
                                "recommendations": validation.recommendations
                            })
                    except Exception as e:
                        validation_results.append({
                            "tool": tool_name,
                            "valid": False,
                            "errors": [f"Failed to validate: {e}"],
                            "warnings": [],
                            "recommendations": []
                        })
            
            # Format validation report
            report_lines = ["🔍 **Tool Validation Report**\n"]
            
            valid_count = sum(1 for r in validation_results if r["valid"])
            invalid_count = len(validation_results) - valid_count
            
            report_lines.append(f"**Summary:** {valid_count} valid, {invalid_count} invalid\n")
            
            for result in validation_results:
                status = "✅" if result["valid"] else "❌"
                report_lines.append(f"{status} **{result['tool']}**")
                
                if result["errors"]:
                    report_lines.append("  Errors:")
                    for error in result["errors"]:
                        report_lines.append(f"    • {error}")
                
                if result["warnings"]:
                    report_lines.append("  Warnings:")
                    for warning in result["warnings"]:
                        report_lines.append(f"    • {warning}")
                
                if result["recommendations"]:
                    report_lines.append("  Recommendations:")
                    for rec in result["recommendations"]:
                        report_lines.append(f"    • {rec}")
                
                report_lines.append("")
            
            return Response(message="\n".join(report_lines), break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"Error validating tools: {e}",
                break_loop=False
            )
    
    async def _get_tool_recommendations(self) -> Response:
        """Get intelligent tool recommendations"""
        try:
            from python.helpers.tool_recommendation import ToolRecommendationEngine
            
            engine = ToolRecommendationEngine()
            
            # Get recommendations for common tasks
            common_tasks = [
                "search for information online",
                "execute Python code",
                "save information to memory",
                "load previous information from memory",
                "delegate a complex task to a specialist",
                "browse a website"
            ]
            
            recommendations_report = ["🎯 **Tool Recommendations for Common Tasks**\n"]
            
            for task in common_tasks:
                recs = engine.recommend_tools(task, self.agent.agent_name, max_recommendations=3)
                
                recommendations_report.append(f"**Task:** {task}")
                for rec in recs:
                    recommendations_report.append(f"  • **{rec.tool_name}** (confidence: {rec.confidence_score:.2f})")
                    recommendations_report.append(f"    Reasoning: {', '.join(rec.reasoning[:2])}")
                recommendations_report.append("")
            
            return Response(message="\n".join(recommendations_report), break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"Error getting recommendations: {e}",
                break_loop=False
            )
    
    async def _check_mcp_tools(self) -> Response:
        """Check MCP tool configuration and availability"""
        try:
            mcp_status = []
            
            try:
                import python.helpers.mcp_handler as mcp_helper
                mcp_config = mcp_helper.MCPConfig.get_instance()
                
                for server in mcp_config.servers:
                    server_name = server.name
                    tools = server.get_tools()
                    error = server.get_error()
                    
                    status = {
                        "server": server_name,
                        "connected": len(tools) > 0,
                        "tool_count": len(tools),
                        "error": error,
                        "tools": [tool.get('name', 'unknown') for tool in tools]
                    }
                    mcp_status.append(status)
                    
            except Exception as e:
                mcp_status.append({
                    "server": "MCP System",
                    "connected": False,
                    "tool_count": 0,
                    "error": f"MCP system error: {e}",
                    "tools": []
                })
            
            # Format MCP status report
            report_lines = ["🔌 **MCP Tools Status Report**\n"]
            
            for status in mcp_status:
                connection_status = "✅ Connected" if status["connected"] else "❌ Disconnected"
                report_lines.append(f"**Server:** {status['server']}")
                report_lines.append(f"**Status:** {connection_status}")
                report_lines.append(f"**Tools:** {status['tool_count']}")
                
                if status["error"]:
                    report_lines.append(f"**Error:** {status['error']}")
                
                if status["tools"]:
                    report_lines.append("**Available Tools:**")
                    for tool in status["tools"]:
                        report_lines.append(f"  • {tool}")
                
                report_lines.append("")
            
            return Response(message="\n".join(report_lines), break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"Error checking MCP tools: {e}",
                break_loop=False
            )
    
    async def _test_tool(self, tool_name: str) -> Response:
        """Test a specific tool"""
        try:
            if not tool_name:
                return Response(
                    message="Please provide a tool_name to test",
                    break_loop=False
                )
            
            # Try to get the tool
            tool = self.agent.get_tool(
                name=tool_name,
                method=None,
                args={},
                message="test",
                loop_data=None
            )
            
            if tool:
                # Get tool metadata
                metadata = tool.get_tool_metadata()
                
                # Validate the tool
                validation = tool.validate_tool()
                
                test_report = f"""
🧪 **Tool Test Report for '{tool_name}'**

**Tool Metadata:**
- Type: {metadata['type']}
- Module: {metadata['module']}
- File Path: {metadata['file_path']}
- Has Documentation: {metadata['has_docstring']}
- Is Async: {metadata['is_async']}
- Agent: {metadata['agent_name']}

**Validation Results:**
- Valid: {'✅ Yes' if validation.is_valid else '❌ No'}

**Errors:**
{chr(10).join(f"  • {error}" for error in validation.errors) if validation.errors else "  None"}

**Warnings:**
{chr(10).join(f"  • {warning}" for warning in validation.warnings) if validation.warnings else "  None"}

**Recommendations:**
{chr(10).join(f"  • {rec}" for rec in validation.recommendations) if validation.recommendations else "  None"}
"""
                
                return Response(message=test_report.strip(), break_loop=False)
            else:
                return Response(
                    message=f"Tool '{tool_name}' could not be loaded",
                    break_loop=False
                )
                
        except Exception as e:
            return Response(
                message=f"Error testing tool '{tool_name}': {e}",
                break_loop=False
            )
    
    async def _diagnose_tool_calling_issue(self) -> Response:
        """Diagnose common tool calling issues"""
        try:
            from python.helpers.extract_tools import discover_tools, validate_tool_discovery
            
            discovered_tools = discover_tools(self.agent.config.profile)
            validation = validate_tool_discovery(discovered_tools)
            
            diagnosis_report = ["🔍 **Tool Calling Issue Diagnosis**\n"]
            
            # Check for common issues
            issues_found = []
            
            if validation["total_tools"] == 0:
                issues_found.append("No tools discovered - check tool directories and MCP configuration")
            
            if validation["local_tools"] == 0:
                issues_found.append("No local tools found - check python/tools/ directory")
            
            if validation["mcp_tools"] == 0:
                issues_found.append("No MCP tools found - check MCP server configuration")
            
            if validation["errors"]:
                issues_found.extend(validation["errors"])
            
            if issues_found:
                diagnosis_report.append("**Issues Found:**")
                for issue in issues_found:
                    diagnosis_report.append(f"  • {issue}")
                diagnosis_report.append("")
            else:
                diagnosis_report.append("✅ **No major issues detected**\n")
            
            # Provide recommendations
            if validation["recommendations"]:
                diagnosis_report.append("**Recommendations:**")
                for rec in validation["recommendations"]:
                    diagnosis_report.append(f"  • {rec}")
                diagnosis_report.append("")
            
            # Tool discovery summary
            diagnosis_report.append("**Tool Discovery Summary:**")
            diagnosis_report.append(f"  • Total Tools: {validation['total_tools']}")
            diagnosis_report.append(f"  • Local Tools: {validation['local_tools']}")
            diagnosis_report.append(f"  • Agent-Specific Tools: {validation['agent_specific_tools']}")
            diagnosis_report.append(f"  • MCP Tools: {validation['mcp_tools']}")
            
            return Response(message="\n".join(diagnosis_report), break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"Error diagnosing tool calling issues: {e}",
                break_loop=False
            )
    
    async def _validate_tool_instructions(self) -> Response:
        """Validate tool instruction files"""
        try:
            from python.helpers.tool_instruction_validator import validate_tool_instructions
            
            report = validate_tool_instructions()
            return Response(message=report, break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"Error validating tool instructions: {e}",
                break_loop=False
            )