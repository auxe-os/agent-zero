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
        else:
            return Response(
                message="Invalid action. Available actions: list_tools, check_mcp, test_tool, diagnose_issue",
                break_loop=False
            )
    
    async def _list_available_tools(self) -> Response:
        """List all available tools"""
        try:
            # Get local tools
            local_tools = []
            try:
                import os
                tools_dir = "python/tools"
                if os.path.exists(tools_dir):
                    for file in os.listdir(tools_dir):
                        if file.endswith('.py') and not file.startswith('_'):
                            tool_name = file.replace('.py', '')
                            local_tools.append(tool_name)
            except Exception as e:
                PrintStyle(font_color="yellow").print(f"Error listing local tools: {e}")
            
            # Get MCP tools
            mcp_tools = []
            try:
                import python.helpers.mcp_handler as mcp_helper
                mcp_config = mcp_helper.MCPConfig.get_instance()
                for server in mcp_config.servers:
                    tools = server.get_tools()
                    for tool in tools:
                        tool_name = tool.get('name', 'unknown')
                        mcp_tools.append(f"{server.name}.{tool_name}")
            except Exception as e:
                PrintStyle(font_color="yellow").print(f"Error listing MCP tools: {e}")
            
            # Get agent-specific tools
            agent_tools = []
            try:
                import os
                if self.agent.config.profile:
                    agent_tools_dir = f"agents/{self.agent.config.profile}/tools"
                    if os.path.exists(agent_tools_dir):
                        for file in os.listdir(agent_tools_dir):
                            if file.endswith('.py') and not file.startswith('_'):
                                tool_name = file.replace('.py', '')
                                agent_tools.append(tool_name)
            except Exception as e:
                PrintStyle(font_color="yellow").print(f"Error listing agent tools: {e}")
            
            tools_report = f"""
🔧 **Available Tools Diagnostic**

**Local Tools ({len(local_tools)}):**
{chr(10).join(f"  • {tool}" for tool in sorted(local_tools))}

**MCP Tools ({len(mcp_tools)}):**
{chr(10).join(f"  • {tool}" for tool in sorted(mcp_tools))}

**Agent-Specific Tools ({len(agent_tools)}):**
{chr(10).join(f"  • {tool}" for tool in sorted(agent_tools))}

**Total Tools Available:** {len(local_tools) + len(mcp_tools) + len(agent_tools)}
"""
            
            return Response(message=tools_report.strip(), break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"Error listing tools: {e}",
                break_loop=False
            )
    
    async def _check_mcp_tools(self) -> Response:
        """Check MCP tool configuration and availability"""
        try:
            mcp_status = []
            
            try:
                import python.helpers.mcp_handler as mcp_helper
                mcp_config = mcp_helper.MCPConfig.get_instance()
                
                mcp_status.append(f"**MCP Configuration Status:**")
                mcp_status.append(f"  • Servers configured: {len(mcp_config.servers)}")
                
                for server in mcp_config.servers:
                    tools = server.get_tools()
                    mcp_status.append(f"  • Server '{server.name}': {len(tools)} tools")
                    for tool in tools:
                        tool_name = tool.get('name', 'unknown')
                        tool_desc = tool.get('description', 'No description')[:50]
                        mcp_status.append(f"    - {tool_name}: {tool_desc}...")
                
            except ImportError:
                mcp_status.append("**MCP Status:** MCP helper module not found")
            except Exception as e:
                mcp_status.append(f"**MCP Status:** Error - {e}")
            
            # Check for google-scholar-mcp specifically
            google_scholar_found = False
            try:
                import python.helpers.mcp_handler as mcp_helper
                mcp_config = mcp_helper.MCPConfig.get_instance()
                for server in mcp_config.servers:
                    tools = server.get_tools()
                    for tool in tools:
                        tool_name = tool.get('name', '')
                        if "google-scholar" in tool_name.lower() or "scholar" in tool_name.lower():
                            google_scholar_found = True
                            mcp_status.append(f"  ✅ Found Google Scholar tool: {server.name}.{tool_name}")
            except:
                pass
            
            if not google_scholar_found:
                mcp_status.append("  ❌ Google Scholar MCP tool not found")
            
            mcp_report = f"""
🔍 **MCP Tools Diagnostic**

{chr(10).join(mcp_status)}

**Recommendations:**
- Ensure MCP servers are properly configured
- Check that google-scholar-mcp server is running
- Verify tool names match exactly (case-sensitive)
"""
            
            return Response(message=mcp_report.strip(), break_loop=False)
            
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
                    message="Tool name required. Use: test_tool with tool_name parameter",
                    break_loop=False
                )
            
            # Try to get the tool
            tool = None
            
            # Try MCP first
            try:
                import python.helpers.mcp_handler as mcp_helper
                mcp_tool = mcp_helper.MCPConfig.get_instance().get_tool(self.agent, tool_name)
                if mcp_tool:
                    tool = mcp_tool
            except Exception as e:
                PrintStyle(font_color="yellow").print(f"MCP tool lookup failed: {e}")
            
            # Try local tool
            if not tool:
                try:
                    tool = self.agent.get_tool(
                        name=tool_name, 
                        method=None, 
                        args={}, 
                        message="test", 
                        loop_data=None
                    )
                except Exception as e:
                    PrintStyle(font_color="yellow").print(f"Local tool lookup failed: {e}")
            
            if tool:
                tool_type = "MCP" if hasattr(tool, 'server') else "Local"
                return Response(
                    message=f"✅ Tool '{tool_name}' found ({tool_type} tool)",
                    break_loop=False
                )
            else:
                return Response(
                    message=f"❌ Tool '{tool_name}' not found",
                    break_loop=False
                )
                
        except Exception as e:
            return Response(
                message=f"Error testing tool: {e}",
                break_loop=False
            )
    
    async def _diagnose_tool_calling_issue(self) -> Response:
        """Diagnose common tool calling issues"""
        try:
            issues = []
            recommendations = []
            
            # Check if response tool is being used inappropriately
            issues.append("**Common Tool Calling Issues:**")
            issues.append("1. Using 'response' tool instead of intended tool")
            issues.append("2. Tool name mismatch (case-sensitive)")
            issues.append("3. MCP server not running or configured")
            issues.append("4. Tool not properly registered")
            
            recommendations.append("**Troubleshooting Steps:**")
            recommendations.append("1. Use 'tool_diagnostics' with action='list_tools' to see available tools")
            recommendations.append("2. Use 'tool_diagnostics' with action='check_mcp' to verify MCP tools")
            recommendations.append("3. Use 'tool_diagnostics' with action='test_tool' to test specific tool")
            recommendations.append("4. Check tool name spelling and case")
            recommendations.append("5. Verify MCP server configuration")
            
            # Check for google-scholar-mcp specifically
            google_scholar_issues = []
            try:
                import python.helpers.mcp_handler as mcp_helper
                mcp_config = mcp_helper.MCPConfig.get_instance()
                found_google_scholar = False
                for server in mcp_config.servers:
                    tools = server.get_tools()
                    for tool in tools:
                        tool_name = tool.get('name', '')
                        if "google-scholar" in tool_name.lower() or "scholar" in tool_name.lower():
                            found_google_scholar = True
                            google_scholar_issues.append(f"✅ Found: {server.name}.{tool_name}")
                
                if not found_google_scholar:
                    google_scholar_issues.append("❌ Google Scholar MCP tool not found")
                    google_scholar_issues.append("   - Check MCP server configuration")
                    google_scholar_issues.append("   - Verify server is running")
                    google_scholar_issues.append("   - Check tool name in server")
            except Exception as e:
                google_scholar_issues.append(f"❌ Error checking Google Scholar: {e}")
            
            diagnosis_report = f"""
🩺 **Tool Calling Issue Diagnosis**

{chr(10).join(issues)}

**Google Scholar MCP Status:**
{chr(10).join(google_scholar_issues)}

{chr(10).join(recommendations)}

**For Google Scholar specifically:**
- Tool name should be exactly as configured in MCP server
- Check if server name prefix is required (e.g., 'server.google-scholar-mcp')
- Verify MCP server is running and accessible
"""
            
            return Response(message=diagnosis_report.strip(), break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"Error diagnosing issue: {e}",
                break_loop=False
            )
