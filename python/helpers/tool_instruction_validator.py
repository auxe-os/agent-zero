"""
Tool Instruction Validation System
Validates tool instruction files for consistency and completeness
"""
import os
import re
from typing import Dict, List, Any
from pathlib import Path
from python.helpers.print_style import PrintStyle


class ToolInstructionValidator:
    """Validates tool instruction files for consistency"""
    
    def __init__(self):
        self.validation_results = []
        self.tool_files = {}
        self.instruction_files = {}
    
    def discover_tool_files(self) -> Dict[str, str]:
        """Discover all tool files and their class names"""
        tool_files = {}
        
        # Discover local tools
        tools_dir = "python/tools"
        if os.path.exists(tools_dir):
            for file in os.listdir(tools_dir):
                if file.endswith('.py') and not file.startswith('_'):
                    tool_name = file.replace('.py', '')
                    file_path = os.path.join(tools_dir, file)
                    
                    # Extract class name from file
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            # Look for class definition
                            class_match = re.search(r'class\s+(\w+)\(Tool\):', content)
                            if class_match:
                                class_name = class_match.group(1)
                                tool_files[tool_name] = {
                                    "file_path": file_path,
                                    "class_name": class_name,
                                    "type": "local"
                                }
                    except Exception as e:
                        PrintStyle(font_color="yellow").print(f"Error reading tool file {file_path}: {e}")
        
        # Discover agent-specific tools
        agents_dir = "agents"
        if os.path.exists(agents_dir):
            for agent_name in os.listdir(agents_dir):
                agent_tools_dir = os.path.join(agents_dir, agent_name, "tools")
                if os.path.exists(agent_tools_dir):
                    for file in os.listdir(agent_tools_dir):
                        if file.endswith('.py') and not file.startswith('_'):
                            tool_name = file.replace('.py', '')
                            file_path = os.path.join(agent_tools_dir, file)
                            
                            try:
                                with open(file_path, 'r') as f:
                                    content = f.read()
                                    class_match = re.search(r'class\s+(\w+)\(Tool\):', content)
                                    if class_match:
                                        class_name = class_match.group(1)
                                        tool_files[tool_name] = {
                                            "file_path": file_path,
                                            "class_name": class_name,
                                            "type": "agent_specific",
                                            "agent": agent_name
                                        }
                            except Exception as e:
                                PrintStyle(font_color="yellow").print(f"Error reading agent tool file {file_path}: {e}")
        
        return tool_files
    
    def discover_instruction_files(self) -> Dict[str, str]:
        """Discover all tool instruction files"""
        instruction_files = {}
        
        # Discover default instruction files
        prompts_dir = "prompts"
        if os.path.exists(prompts_dir):
            for file in os.listdir(prompts_dir):
                if file.startswith('agent.system.tool.') and file.endswith('.md'):
                    tool_name = file.replace('agent.system.tool.', '').replace('.md', '')
                    file_path = os.path.join(prompts_dir, file)
                    instruction_files[tool_name] = {
                        "file_path": file_path,
                        "type": "default"
                    }
        
        # Discover agent-specific instruction files
        agents_dir = "agents"
        if os.path.exists(agents_dir):
            for agent_name in os.listdir(agents_dir):
                agent_prompts_dir = os.path.join(agents_dir, agent_name, "prompts")
                if os.path.exists(agent_prompts_dir):
                    for file in os.listdir(agent_prompts_dir):
                        if file.startswith('agent.system.tool.') and file.endswith('.md'):
                            tool_name = file.replace('agent.system.tool.', '').replace('.md', '')
                            file_path = os.path.join(agent_prompts_dir, file)
                            instruction_files[tool_name] = {
                                "file_path": file_path,
                                "type": "agent_specific",
                                "agent": agent_name
                            }
        
        return instruction_files
    
    def validate_instruction_file(self, tool_name: str, instruction_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single instruction file"""
        validation_result = {
            "tool_name": tool_name,
            "file_path": instruction_info["file_path"],
            "type": instruction_info["type"],
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        try:
            with open(instruction_info["file_path"], 'r') as f:
                content = f.read()
            
            # Check if file has content
            if not content.strip():
                validation_result["errors"].append("Instruction file is empty")
                validation_result["valid"] = False
                return validation_result
            
            # Check for tool name in header
            header_match = re.search(r'^###\s+(\w+)', content, re.MULTILINE)
            if not header_match:
                validation_result["errors"].append("Missing tool name header (### tool_name)")
                validation_result["valid"] = False
            else:
                header_tool_name = header_match.group(1)
                if header_tool_name != tool_name:
                    validation_result["warnings"].append(f"Header tool name '{header_tool_name}' doesn't match file name '{tool_name}'")
            
            # Check for tool_name in JSON examples
            json_matches = re.findall(r'"tool_name":\s*"([^"]+)"', content)
            if not json_matches:
                validation_result["errors"].append("No tool_name found in JSON examples")
                validation_result["valid"] = False
            else:
                for json_tool_name in json_matches:
                    if json_tool_name != tool_name:
                        validation_result["warnings"].append(f"JSON tool_name '{json_tool_name}' doesn't match file name '{tool_name}'")
            
            # Check for usage examples
            if '~~~json' not in content:
                validation_result["recommendations"].append("Add JSON usage examples")
            
            # Check for description
            if len(content.split('\n')) < 5:
                validation_result["recommendations"].append("Add more detailed description")
            
        except Exception as e:
            validation_result["errors"].append(f"Error reading file: {e}")
            validation_result["valid"] = False
        
        return validation_result
    
    def validate_all(self) -> Dict[str, Any]:
        """Validate all tool instructions"""
        self.tool_files = self.discover_tool_files()
        self.instruction_files = self.discover_instruction_files()
        
        validation_results = {
            "total_tools": len(self.tool_files),
            "total_instructions": len(self.instruction_files),
            "valid_instructions": 0,
            "invalid_instructions": 0,
            "missing_instructions": [],
            "extra_instructions": [],
            "validation_details": []
        }
        
        # Validate each instruction file
        for tool_name, instruction_info in self.instruction_files.items():
            validation = self.validate_instruction_file(tool_name, instruction_info)
            validation_results["validation_details"].append(validation)
            
            if validation["valid"]:
                validation_results["valid_instructions"] += 1
            else:
                validation_results["invalid_instructions"] += 1
        
        # Find missing instructions
        for tool_name in self.tool_files:
            if tool_name not in self.instruction_files:
                validation_results["missing_instructions"].append(tool_name)
        
        # Find extra instructions
        for tool_name in self.instruction_files:
            if tool_name not in self.tool_files:
                validation_results["extra_instructions"].append(tool_name)
        
        return validation_results
    
    def generate_report(self) -> str:
        """Generate a comprehensive validation report"""
        validation = self.validate_all()
        
        report_lines = ["📋 **Tool Instruction Validation Report**\n"]
        
        # Summary
        report_lines.append("**Summary:**")
        report_lines.append(f"  • Total Tools: {validation['total_tools']}")
        report_lines.append(f"  • Total Instructions: {validation['total_instructions']}")
        report_lines.append(f"  • Valid Instructions: {validation['valid_instructions']}")
        report_lines.append(f"  • Invalid Instructions: {validation['invalid_instructions']}")
        report_lines.append("")
        
        # Missing instructions
        if validation["missing_instructions"]:
            report_lines.append("**Missing Instructions:**")
            for tool_name in validation["missing_instructions"]:
                report_lines.append(f"  • {tool_name}")
            report_lines.append("")
        
        # Extra instructions
        if validation["extra_instructions"]:
            report_lines.append("**Extra Instructions (no corresponding tool):**")
            for tool_name in validation["extra_instructions"]:
                report_lines.append(f"  • {tool_name}")
            report_lines.append("")
        
        # Detailed validation results
        report_lines.append("**Detailed Validation Results:**")
        for detail in validation["validation_details"]:
            status = "✅" if detail["valid"] else "❌"
            report_lines.append(f"{status} **{detail['tool_name']}** ({detail['type']})")
            
            if detail["errors"]:
                report_lines.append("  Errors:")
                for error in detail["errors"]:
                    report_lines.append(f"    • {error}")
            
            if detail["warnings"]:
                report_lines.append("  Warnings:")
                for warning in detail["warnings"]:
                    report_lines.append(f"    • {warning}")
            
            if detail["recommendations"]:
                report_lines.append("  Recommendations:")
                for rec in detail["recommendations"]:
                    report_lines.append(f"    • {rec}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)


def validate_tool_instructions() -> str:
    """Main function to validate all tool instructions"""
    validator = ToolInstructionValidator()
    return validator.generate_report()
