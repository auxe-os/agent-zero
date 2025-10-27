from abc import abstractmethod
from dataclasses import dataclass
from typing import Any
import time
import inspect
from pathlib import Path

from agent import Agent, LoopData
from python.helpers.print_style import PrintStyle
from python.helpers.strings import sanitize_string
from python.helpers.tool_analytics import record_tool_usage


@dataclass
class Response:
    message:str
    break_loop: bool
    additional: dict[str, Any] | None = None


@dataclass
class ToolValidationResult:
    """Result of tool validation"""
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    recommendations: list[str]


class Tool:

    def __init__(self, agent: Agent, name: str, method: str | None, args: dict[str,str], message: str, loop_data: LoopData | None, **kwargs) -> None:
        self.agent = agent
        self.name = name
        self.method = method
        self.args = args
        self.loop_data = loop_data
        self.message = message
        self.execution_start_time = None
        self.tool_context = self.extract_task_context(message)
        self.validation_result = None

    def extract_task_context(self, message: str) -> str:
        """Extract task context from the message for analytics"""
        # Simple context extraction - can be enhanced with NLP
        if len(message) > 200:
            return message[:200] + "..."
        return message

    def validate_tool(self) -> ToolValidationResult:
        """
        Validate tool configuration and availability
        """
        errors = []
        warnings = []
        recommendations = []
        
        # Check if tool class is properly defined
        if not hasattr(self, 'execute'):
            errors.append("Tool class must implement execute method")
        
        # Check if execute method is async
        if hasattr(self, 'execute'):
            execute_method = getattr(self, 'execute')
            if not inspect.iscoroutinefunction(execute_method):
                errors.append("Tool execute method must be async")
        
        # Validate arguments
        if self.args and not isinstance(self.args, dict):
            errors.append("Tool args must be a dictionary")
        
        # Check for common tool issues
        if self.name == "unknown":
            warnings.append("Tool name is 'unknown' - tool may not be properly discovered")
        
        # Check if tool has proper documentation
        if not hasattr(self, '__doc__') or not self.__doc__:
            recommendations.append("Tool should have documentation")
        
        # Validate tool name format
        if '.' in self.name and not self.name.startswith(('mcp.', 'server.')):
            warnings.append("Tool name contains dots - may be MCP tool with incorrect format")
        
        is_valid = len(errors) == 0
        
        self.validation_result = ToolValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
        
        return self.validation_result

    def get_tool_metadata(self) -> dict[str, Any]:
        """
        Get comprehensive tool metadata for analytics and recommendations
        """
        return {
            "name": self.name,
            "method": self.method,
            "type": self.__class__.__name__,
            "module": self.__class__.__module__,
            "file_path": inspect.getfile(self.__class__),
            "has_docstring": bool(self.__doc__),
            "is_async": inspect.iscoroutinefunction(self.execute),
            "validation_result": self.validation_result,
            "args_count": len(self.args) if self.args else 0,
            "agent_name": self.agent.agent_name if self.agent else "unknown"
        }

    @abstractmethod
    async def execute(self,**kwargs) -> Response:
        pass

    async def before_execution(self, **kwargs):
        # Validate tool before execution
        validation = self.validate_tool()
        if not validation.is_valid:
            error_msg = f"Tool validation failed: {', '.join(validation.errors)}"
            PrintStyle(font_color="red", padding=True).print(error_msg)
            self.agent.context.log.log(type="error", content=error_msg)
            raise ValueError(error_msg)
        
        # Log warnings if any
        if validation.warnings:
            for warning in validation.warnings:
                PrintStyle(font_color="yellow").print(f"Tool warning: {warning}")
        
        self.execution_start_time = time.time()
        PrintStyle(font_color="#1B4F72", padding=True, background_color="white", bold=True).print(f"{self.agent.agent_name}: Using tool '{self.name}'")
        self.log = self.get_log_object()
        if self.args and isinstance(self.args, dict):
            for key, value in self.args.items():
                PrintStyle(font_color="#85C1E9", bold=True).stream(self.nice_key(key)+": ")
                PrintStyle(font_color="#85C1E9", padding=isinstance(value,str) and "\n" in value).stream(value)
                PrintStyle().print()

    async def after_execution(self, response: Response, **kwargs):
        execution_time = time.time() - self.execution_start_time if self.execution_start_time else 0

        text = sanitize_string(response.message.strip())
        self.agent.hist_add_tool_result(self.name, text, **(response.additional or {}))
        PrintStyle(font_color="#1B4F72", background_color="white", padding=True, bold=True).print(f"{self.agent.agent_name}: Response from tool '{self.name}'")
        PrintStyle(font_color="#85C1E9").print(text)
        self.log.update(content=text)

        # Record tool usage analytics
        try:
            record_tool_usage(
                tool_name=self.name,
                agent_name=self.agent.agent_name,
                execution_time=execution_time,
                success=True,  # Assume success if we got here
                error_message=None,
                args=self.args,
                result_length=len(text),
                task_context=self.tool_context
            )
        except Exception as e:
            # Don't let analytics errors break tool execution
            PrintStyle(font_color="yellow", background_color="black", padding=True).print(
                f"Analytics recording failed for {self.name}: {e}"
            )

    def get_log_object(self):
        if self.method:
            heading = f"icon://construction {self.agent.agent_name}: Using tool '{self.name}:{self.method}'"
        else:
            heading = f"icon://construction {self.agent.agent_name}: Using tool '{self.name}'"
        return self.agent.context.log.log(type="tool", heading=heading, content="", kvps=self.args)

    def nice_key(self, key:str):
        words = key.split('_')
        words = [words[0].capitalize()] + [word.lower() for word in words[1:]]
        result = ' '.join(words)
        return result
