### tool_diagnostics

diagnose and fix tool calling issues, check MCP tool availability, and troubleshoot tool selection problems

usage:

1 list all available tools

~~~json
{
    "thoughts": [
        "Need to see what tools are available...",
        "I can use the tool diagnostics to list all tools...",
        "This will help identify which tools are accessible..."
    ],
    "headline": "Listing all available tools",
    "tool_name": "tool_diagnostics",
    "tool_args": {
        "action": "list_tools"
    }
}
~~~

2 check MCP tool configuration

~~~json
{
    "thoughts": [
        "Need to check MCP tool configuration...",
        "This will show me which MCP tools are available...",
        "I can use the tool diagnostics to check MCP status..."
    ],
    "headline": "Checking MCP tool configuration",
    "tool_name": "tool_diagnostics",
    "tool_args": {
        "action": "check_mcp"
    }
}
~~~

3 test a specific tool

~~~json
{
    "thoughts": [
        "Need to test if a specific tool is working...",
        "I can use the tool diagnostics to test the tool...",
        "This will verify if the tool is accessible..."
    ],
    "headline": "Testing specific tool",
    "tool_name": "tool_diagnostics",
    "tool_args": {
        "action": "test_tool",
        "tool_name": "google-scholar-mcp"
    }
}
~~~

4 diagnose tool calling issues

~~~json
{
    "thoughts": [
        "Need to diagnose why tools aren't working properly...",
        "I can use the tool diagnostics to identify issues...",
        "This will help troubleshoot tool calling problems..."
    ],
    "headline": "Diagnosing tool calling issues",
    "tool_name": "tool_diagnostics",
    "tool_args": {
        "action": "diagnose_issue"
    }
}
~~~
