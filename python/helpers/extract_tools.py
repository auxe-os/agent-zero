import re, os, importlib, importlib.util, inspect
from types import ModuleType
from typing import Any, Type, TypeVar
from .dirty_json import DirtyJson
from .files import get_abs_path, deabsolute_path
import regex
from fnmatch import fnmatch

def json_parse_dirty(json:str) -> dict[str,Any] | None:
    if not json or not isinstance(json, str):
        return None

    ext_json = extract_json_object_string(json.strip())
    if ext_json:
        try:
            data = DirtyJson.parse_string(ext_json)
            if isinstance(data,dict): return data
        except Exception:
            # If parsing fails, return None instead of crashing
            return None
    return None

def extract_json_object_string(content):
    start = content.find('{')
    if start == -1:
        return ""

    # Find the first '{'
    end = content.rfind('}')
    if end == -1:
        # If there's no closing '}', return from start to the end
        return content[start:]
    else:
        # If there's a closing '}', return the substring from start to end
        return content[start:end+1]

def extract_json_string(content):
    # Regular expression pattern to match a JSON object
    pattern = r'\{(?:[^{}]|(?R))*\}|\[(?:[^\[\]]|(?R))*\]|"(?:\\.|[^"\\])*"|true|false|null|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'

    # Search for the pattern in the content
    match = regex.search(pattern, content)

    if match:
        # Return the matched JSON string
        return match.group(0)
    else:
        return ""

def fix_json_string(json_string):
    # Function to replace unescaped line breaks within JSON string values
    def replace_unescaped_newlines(match):
        return match.group(0).replace('\n', '\\n')

    # Use regex to find string values and apply the replacement function
    fixed_string = re.sub(r'(?<=: ")(.*?)(?=")', replace_unescaped_newlines, json_string, flags=re.DOTALL)
    return fixed_string


T = TypeVar('T')  # Define a generic type variable

def import_module(file_path: str) -> ModuleType:
    # Handle file paths with periods in the name using importlib.util
    abs_path = get_abs_path(file_path)
    module_name = os.path.basename(abs_path).replace('.py', '')
    
    # Create the module spec and load the module
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {abs_path}")
        
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_classes_from_folder(folder: str, name_pattern: str, base_class: Type[T], one_per_file: bool = True) -> list[Type[T]]:
    classes = []
    abs_folder = get_abs_path(folder)

    # Get all .py files in the folder that match the pattern, sorted alphabetically
    py_files = sorted(
        [file_name for file_name in os.listdir(abs_folder) if fnmatch(file_name, name_pattern) and file_name.endswith(".py")]
    )

    # Iterate through the sorted list of files
    for file_name in py_files:
        file_path = os.path.join(abs_folder, file_name)
        # Use the new import_module function
        module = import_module(file_path)

        # Get all classes in the module
        class_list = inspect.getmembers(module, inspect.isclass)

        # Filter for classes that are subclasses of the given base_class
        # iterate backwards to skip imported superclasses
        for cls in reversed(class_list):
            if cls[1] is not base_class and issubclass(cls[1], base_class):
                classes.append(cls[1])
                if one_per_file:
                    break

    return classes

def load_classes_from_file(file: str, base_class: type[T], one_per_file: bool = True) -> list[type[T]]:
    classes = []
    try:
        # Use the new import_module function
        module = import_module(file)
        
        # Get all classes in the module
        class_list = inspect.getmembers(module, inspect.isclass)
        
        # Filter for classes that are subclasses of the given base_class
        # iterate backwards to skip imported superclasses
        for cls in reversed(class_list):
            if cls[1] is not base_class and issubclass(cls[1], base_class):
                classes.append(cls[1])
                if one_per_file:
                    break
    except Exception as e:
        # Log the error for debugging
        from python.helpers.print_style import PrintStyle
        PrintStyle(font_color="yellow").print(f"Failed to load tool from {file}: {e}")
                    
    return classes


def discover_tools(agent_profile: str = None) -> dict[str, dict[str, Any]]:
    """
    Unified tool discovery system that finds all available tools
    Returns a dictionary with tool metadata for validation and recommendations
    """
    from python.helpers.print_style import PrintStyle
    from python.helpers.tool import Tool
    
    discovered_tools = {}
    
    # Discover local tools
    try:
        tools_dir = get_abs_path("python/tools")
        if os.path.exists(tools_dir):
            for file in os.listdir(tools_dir):
                if file.endswith('.py') and not file.startswith('_'):
                    tool_name = file.replace('.py', '')
                    file_path = f"python/tools/{tool_name}.py"
                    
                    classes = load_classes_from_file(file_path, Tool)
                    if classes:
                        tool_class = classes[0]
                        discovered_tools[tool_name] = {
                            "type": "local",
                            "class": tool_class,
                            "file_path": file_path,
                            "agent_specific": False,
                            "available": True,
                            "error": None
                        }
    except Exception as e:
        PrintStyle(font_color="red").print(f"Error discovering local tools: {e}")
    
    # Discover agent-specific tools
    if agent_profile:
        try:
            agent_tools_dir = get_abs_path(f"agents/{agent_profile}/tools")
            if os.path.exists(agent_tools_dir):
                for file in os.listdir(agent_tools_dir):
                    if file.endswith('.py') and not file.startswith('_'):
                        tool_name = file.replace('.py', '')
                        file_path = f"agents/{agent_profile}/tools/{tool_name}.py"
                        
                        classes = load_classes_from_file(file_path, Tool)
                        if classes:
                            tool_class = classes[0]
                            # Agent-specific tools override local tools
                            discovered_tools[tool_name] = {
                                "type": "agent_specific",
                                "class": tool_class,
                                "file_path": file_path,
                                "agent_specific": True,
                                "available": True,
                                "error": None
                            }
        except Exception as e:
            PrintStyle(font_color="red").print(f"Error discovering agent-specific tools: {e}")
    
    # Discover MCP tools
    try:
        import python.helpers.mcp_handler as mcp_helper
        mcp_config = mcp_helper.MCPConfig.get_instance()
        for server in mcp_config.servers:
            tools = server.get_tools()
            for tool in tools:
                tool_name = tool.get('name', 'unknown')
                mcp_tool_name = f"{server.name}.{tool_name}"
                discovered_tools[mcp_tool_name] = {
                    "type": "mcp",
                    "server": server.name,
                    "tool_name": tool_name,
                    "description": tool.get('description', ''),
                    "input_schema": tool.get('input_schema', {}),
                    "agent_specific": False,
                    "available": True,
                    "error": None
                }
    except Exception as e:
        PrintStyle(font_color="red").print(f"Error discovering MCP tools: {e}")
    
    return discovered_tools


def validate_tool_discovery(discovered_tools: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """
    Validate discovered tools and provide recommendations
    """
    validation_results = {
        "total_tools": len(discovered_tools),
        "local_tools": 0,
        "agent_specific_tools": 0,
        "mcp_tools": 0,
        "errors": [],
        "recommendations": []
    }
    
    for tool_name, tool_info in discovered_tools.items():
        tool_type = tool_info.get("type", "unknown")
        
        if tool_type == "local":
            validation_results["local_tools"] += 1
        elif tool_type == "agent_specific":
            validation_results["agent_specific_tools"] += 1
        elif tool_type == "mcp":
            validation_results["mcp_tools"] += 1
        
        # Check for common issues
        if not tool_info.get("available", False):
            validation_results["errors"].append(f"Tool {tool_name} is not available")
        
        if tool_info.get("error"):
            validation_results["errors"].append(f"Tool {tool_name} has error: {tool_info['error']}")
    
    # Generate recommendations
    if validation_results["mcp_tools"] == 0:
        validation_results["recommendations"].append("No MCP tools found - check MCP configuration")
    
    if validation_results["local_tools"] == 0:
        validation_results["recommendations"].append("No local tools found - check tool directory")
    
    return validation_results
