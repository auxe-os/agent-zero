"""
Prompt Refinement API for Agent Zero

This API endpoint provides intelligent prompt refinement capabilities
to help users create more effective prompts for Agent Zero.
"""

import re
import json
from typing import Dict, List, Any, Optional
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.tool_recommendation import get_recommendation_engine
from python.helpers.tool_analytics import get_tool_analytics
from python.helpers.print_style import PrintStyle


class ApiPromptRefine(ApiHandler):
    """API handler for prompt refinement requests"""

    @classmethod
    def requires_auth(cls) -> bool:
        return False  # No web auth required

    @classmethod
    def requires_csrf(cls) -> bool:
        return False  # No CSRF required

    @classmethod
    def requires_api_key(cls) -> bool:
        return False  # No API key required (same as message API)

    async def process(self, input: dict, request: Request) -> dict | Response:
        """Process prompt refinement request"""

        # Extract parameters
        prompt = input.get("prompt", "").strip()
        context = input.get("context", "")
        agent_profile = input.get("agent_profile", "default")
        refinement_options = input.get("options", {})
        refine_mode = input.get("refine_mode", "standard")  # "standard" or "context_aware"

        if not prompt:
            return Response(
                json.dumps({"error": "Prompt is required"}),
                status=400,
                mimetype="application/json"
            )

        try:
            # Choose refinement method based on mode
            if refine_mode == "context_aware":
                # Context-aware refinement (slower but more comprehensive)
                refined_prompt = await self.refine_prompt_context_aware(
                    prompt, context, agent_profile, refinement_options
                )
                # Generate full analysis and suggestions using existing methods
                analysis = await self.analyze_prompt_improvements(
                    prompt, refined_prompt, agent_profile
                )
                suggestions = self.generate_suggestions(prompt, refined_prompt)
            else:
                # Fast standard refinement
                refined_prompt = await self.refine_prompt_standard(
                    prompt, context, agent_profile, refinement_options
                )
                # Generate analysis and suggestions for standard mode too
                analysis = await self.analyze_prompt_improvements(
                    prompt, refined_prompt, agent_profile
                )
                suggestions = self.generate_suggestions(prompt, refined_prompt)

            return Response(
                json.dumps({
                    "original_prompt": prompt,
                    "refined_prompt": refined_prompt,
                    "analysis": analysis,
                    "suggestions": suggestions,
                    "agent_profile": agent_profile,
                    "refinement_metadata": {
                        "original_length": len(prompt),
                        "refined_length": len(refined_prompt),
                        "improvements_count": analysis.get("improvements_count", 0),
                        "confidence_score": analysis.get("confidence_score", 0.0),
                        "refine_mode": refine_mode
                    }
                }),
                status=200,
                mimetype="application/json"
            )

        except Exception as e:
            PrintStyle(font_color="red", background_color="black", padding=True).print(
                f"Prompt refinement error: {str(e)}"
            )

            return Response(
                json.dumps({
                    "error": f"Failed to refine prompt: {str(e)}",
                    "original_prompt": prompt,
                    "refined_prompt": prompt  # Fallback to original
                }),
                status=500,
                mimetype="application/json"
            )

    async def _gather_agent_zero_context(self, agent_profile: str) -> str:
        """Gather comprehensive Agent Zero context for prompt refinement"""
        context_parts = []
        
        try:
            # Get available tools
            from python.helpers.extract_tools import discover_tools, validate_tool_discovery
            
            discovered_tools = discover_tools(agent_profile)
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
            
            context_parts.append(f"AVAILABLE TOOLS:")
            context_parts.append(f"- Local Tools ({len(local_tools)}): {', '.join(sorted(local_tools))}")
            if agent_tools:
                context_parts.append(f"- Agent-Specific Tools ({len(agent_tools)}): {', '.join(sorted(agent_tools))}")
            if mcp_tools:
                context_parts.append(f"- MCP Tools ({len(mcp_tools)}): {', '.join(sorted(mcp_tools))}")
            
        except Exception as e:
            context_parts.append(f"TOOLS: Error discovering tools: {e}")
        
        try:
            # Get agent profile information
            if agent_profile:
                context_parts.append(f"AGENT PROFILE: {agent_profile}")
                
                # Get agent-specific capabilities
                agent_capabilities = {
                    "developer": "Code execution, debugging, software development, testing, deployment",
                    "researcher": "Information gathering, analysis, documentation, knowledge synthesis",
                    "hacker": "Security testing, system exploration, vulnerability assessment, automation",
                    "agent0": "Coordination, orchestration, strategic planning, task delegation"
                }
                
                if agent_profile in agent_capabilities:
                    context_parts.append(f"AGENT CAPABILITIES: {agent_capabilities[agent_profile]}")
            else:
                context_parts.append("AGENT PROFILE: default (general purpose)")
                
        except Exception as e:
            context_parts.append(f"AGENT PROFILE: Error getting profile info: {e}")
        
        try:
            # Get system capabilities
            from python.helpers.settings import get_settings
            settings = get_settings()
            
            context_parts.append("SYSTEM CAPABILITIES:")
            context_parts.append("- Multi-agent coordination and delegation")
            context_parts.append("- Persistent memory with semantic search")
            context_parts.append("- Real-time web browsing and automation")
            context_parts.append("- Code execution (Python, Node.js, Terminal)")
            context_parts.append("- File system operations and management")
            context_parts.append("- External API integration via MCP")
            
            # Get model information
            chat_model = settings.get("chat_model_name", "unknown")
            context_parts.append(f"- AI Model: {chat_model}")
            
        except Exception as e:
            context_parts.append(f"SYSTEM CAPABILITIES: Error getting system info: {e}")
        
        # Note: Recent context could be added here if needed
        # For now, we focus on system capabilities and tools
        
        # Add optimization guidelines
        context_parts.append("OPTIMIZATION GUIDELINES:")
        context_parts.append("- Be specific about desired outcomes")
        context_parts.append("- Suggest relevant tools when appropriate")
        context_parts.append("- Include clear success criteria")
        context_parts.append("- Leverage Agent Zero's multi-agent capabilities")
        context_parts.append("- Consider the agent profile's strengths")
        context_parts.append("- Make tasks actionable and measurable")
        
        return "\n".join(context_parts)

    async def refine_prompt_standard(self, prompt: str, context: str, agent_profile: str,
                          options: Dict[str, Any]) -> str:
        """Fast standard prompt refinement without context gathering"""
        
        # Create the simple enhancement prompt template (like before)
        enhancement_prompt = f"""Generate an enhanced version of this prompt (reply with only the enhanced prompt - no conversation, explanations, lead-in, bullet points, placeholders, or surrounding quotes):

{prompt}"""

        # Use the utility model for prompt enhancement
        from python.helpers.settings import get_settings
        from python.helpers.call_llm import call_llm

        settings = get_settings()
        model_provider = settings["util_model_provider"]
        model_name = settings["util_model_name"]

        try:
            # Call the LLM to enhance the prompt
            from models import get_util_model
            model = get_util_model()

            response = await call_llm(
                system="",  # No system prompt for speed
                model=model,
                message=enhancement_prompt
            )

            # Clean up the response to get just the enhanced prompt
            enhanced_prompt = response.strip()

            # Remove any common unwanted prefixes/suffixes
            unwanted_prefixes = [
                "Here's an enhanced version:",
                "Enhanced prompt:",
                "Here is the enhanced prompt:",
                "The enhanced version is:",
                "Enhanced version:",
                "Here's a refined version:",
                "Refined prompt:"
            ]

            for prefix in unwanted_prefixes:
                if enhanced_prompt.lower().startswith(prefix.lower()):
                    enhanced_prompt = enhanced_prompt[len(prefix):].strip()

            # Remove quotes if the entire response is wrapped in quotes
            if (enhanced_prompt.startswith('"') and enhanced_prompt.endswith('"')) or \
               (enhanced_prompt.startswith("'") and enhanced_prompt.endswith("'")):
                enhanced_prompt = enhanced_prompt[1:-1].strip()

            return enhanced_prompt

        except Exception as e:
            PrintStyle(font_color="red", background_color="black", padding=True).print(
                f"Standard prompt refinement error: {str(e)}"
            )
            return prompt  # Return original prompt on error

    async def refine_prompt_context_aware(self, prompt: str, context: str, agent_profile: str,
                          options: Dict[str, Any]) -> str:
        """Context-aware prompt refinement logic using Agent Zero capabilities"""

        # Gather Agent Zero context
        agent_zero_context = await self._gather_agent_zero_context(agent_profile)
        
        # Create the context-aware enhancement prompt template
        enhancement_prompt = f"""Generate an enhanced version of this prompt tailored for Agent Zero (reply with only the enhanced prompt - no conversation, explanations, lead-in, bullet points, placeholders, or surrounding quotes):

AGENT ZERO CONTEXT:
{agent_zero_context}

ORIGINAL PROMPT:
{prompt}

ENHANCED PROMPT:"""

        # Use the utility model for prompt enhancement (same as chat model)
        from python.helpers.settings import get_settings
        from python.helpers.call_llm import call_llm

        settings = get_settings()
        model_provider = settings["util_model_provider"]
        model_name = settings["util_model_name"]

        try:
            # Call the LLM to enhance the prompt
            from models import get_util_model
            model = get_util_model()

            response = await call_llm(
                system="You are an Agent Zero prompt optimization expert. You specialize in creating prompts that leverage Agent Zero's specific capabilities, tools, and architecture. Focus on making prompts actionable, specific, and optimized for the available tools and agent profiles.",
                model=model,
                message=enhancement_prompt
            )

            # Clean up the response to get just the enhanced prompt
            enhanced_prompt = response.strip()

            # Remove any common unwanted prefixes/suffixes
            unwanted_prefixes = [
                "Here's an enhanced version:",
                "Enhanced prompt:",
                "Here is the enhanced prompt:",
                "The enhanced version is:",
                "Enhanced version:",
                "Here's a refined version:",
                "Refined prompt:"
            ]

            for prefix in unwanted_prefixes:
                if enhanced_prompt.lower().startswith(prefix.lower()):
                    enhanced_prompt = enhanced_prompt[len(prefix):].strip()

            # Remove quotes if the entire response is wrapped in quotes
            if (enhanced_prompt.startswith('"') and enhanced_prompt.endswith('"')) or \
               (enhanced_prompt.startswith("'") and enhanced_prompt.endswith("'")):
                enhanced_prompt = enhanced_prompt[1:-1].strip()

            return enhanced_prompt if enhanced_prompt else prompt

        except Exception as e:
            PrintStyle(font_color="red", background_color="black", padding=True).print(
                f"Prompt refinement failed: {e}"
            )
            # Return original prompt if enhancement fails
            return prompt

    def improve_clarity(self, prompt: str) -> str:
        """Improve prompt clarity and reduce ambiguity"""

        # Common clarification patterns
        clarifications = []

        # Add objective if missing
        if not any(word in prompt.lower() for word in ["create", "build", "write", "generate", "implement", "fix", "solve", "analyze"]):
            clarifications.append("Please clearly state what action you want me to take.")

        # Add scope if unclear
        if len(prompt.split()) < 10:
            clarifications.append("Please provide more specific details about what you want.")

        # Add constraints if missing
        if not any(word in prompt.lower() for word in ["don't", "avoid", "not", "except", "but"]):
            clarifications.append("Consider if there are any constraints or things to avoid.")

        # Apply clarifications
        if clarifications:
            refined = prompt
            for clarification in clarifications:
                refined += f"\n\n{clarification}"
            return refined

        return prompt

    def add_structure(self, prompt: str) -> str:
        """Add structure and organization to the prompt"""

        # Check if prompt already has structure
        has_structure = (
            "##" in prompt or
            "**" in prompt or
            "1." in prompt or
            "- " in prompt or
            any(prompt.count(char) > 3 for char in ["•", "●", "○"])
        )

        if has_structure:
            return prompt

        # Add basic structure
        lines = prompt.strip().split('\n')
        if len(lines) == 1:
            # Single line prompt - add structure
            return f"## Task\n{prompt.strip()}\n\n## Requirements\nPlease provide a complete solution with proper explanations."
        else:
            # Multi-line prompt - add headings
            return f"## Task\n{prompt.strip()}\n\n## Requirements\nPlease provide a complete solution with proper explanations."

    def add_context(self, prompt: str, context: str, agent_profile: str) -> str:
        """Add relevant context to the prompt"""

        context_section = ""

        # Add agent profile context
        if agent_profile != "default":
            profile_contexts = {
                "developer": "As a Master Developer agent, please provide production-ready code with proper error handling, testing considerations, and documentation.",
                "researcher": "As a researcher agent, please provide thorough analysis with citations, multiple perspectives, and balanced conclusions.",
                "hacker": "As a hacker agent, please focus on security analysis, vulnerability assessment, and defensive strategies.",
                "agent0": "As Agent Zero, please coordinate resources, delegate appropriately, and provide comprehensive oversight of the solution."
            }
            context_section += profile_contexts.get(agent_profile, "") + "\n\n"

        # Add conversation context if available
        if context and len(context.strip()) > 10:
            context_section += f"## Context\n{context.strip()}\n\n"

        # Add architecture awareness
        context_section += """## Agent Zero Architecture Context
You are Agent Zero, an autonomous AI system with:
- Multi-agent hierarchical coordination
- Advanced tool selection and usage capabilities
- Long-term memory and knowledge integration
- Performance optimization and learning systems
- MCP (Model Context Protocol) integration for external tools

Use your full capabilities to provide comprehensive solutions."""

        return f"{context_section.strip()}\n\n## Original Request\n{prompt.strip()}"

    def add_tool_suggestions(self, prompt: str, agent_profile: str) -> str:
        """Add tool usage suggestions based on task analysis"""

        try:
            # Use existing recommendation engine
            engine = get_recommendation_engine()
            recommendations = engine.recommend_tools(prompt, agent_profile, 3)

            if recommendations:
                tools_section = "## Suggested Tools\n"
                tools_section += "Based on the task, consider using these tools in your approach:\n\n"

                for i, rec in enumerate(recommendations, 1):
                    tools_section += f"{i}. **{rec.tool_name}** - {rec.confidence_score:.1%} confidence\n"
                    if rec.reasoning:
                        tools_section += f"   Reason: {', '.join(rec.reasoning[:2])}\n"
                    tools_section += "\n"

                return f"{prompt.strip()}\n\n{tools_section}"

        except Exception as e:
            PrintStyle(font_color="yellow", background_color="black", padding=True).print(
                f"Tool recommendation error: {str(e)}"
            )

        return prompt

    def add_examples(self, prompt: str) -> str:
        """Add relevant examples to the prompt"""

        # Detect task type and add appropriate examples
        prompt_lower = prompt.lower()

        examples_section = ""

        if any(word in prompt_lower for word in ["code", "implement", "function", "class", "api"]):
            examples_section = """## Example Code Structure
```python
# Include imports
import necessary_modules

# Define main function/class
def main_function():
    # Implementation here
    pass

# Add error handling
try:
    main_function()
except Exception as e:
    # Handle errors
    print(f"Error: {e}")
```"""

        elif any(word in prompt_lower for word in ["search", "research", "analyze", "investigate"]):
            examples_section = """## Research Approach Example
1. **Initial Research**: Use search_engine to gather current information
2. **Memory Check**: Search memory for relevant previous findings
3. **Analysis**: Compare and synthesize information from multiple sources
4. **Documentation**: Save findings to memory for future reference
5. **Verification**: Cross-check important facts and conclusions"""

        elif any(word in prompt_lower for word in ["plan", "design", "architecture", "strategy"]):
            examples_section = """## Planning Framework Example
1. **Requirements Analysis**: Clearly define objectives and constraints
2. **Architecture Design**: Outline system components and relationships
3. **Implementation Strategy**: Break down into manageable steps
4. **Risk Assessment**: Identify potential issues and mitigation strategies
5. **Success Criteria**: Define measurable outcomes and validation methods"""

        if examples_section:
            return f"{prompt.strip()}\n\n{examples_section}"

        return prompt

    def add_specificity(self, prompt: str) -> str:
        """Add specificity and detail requirements"""

        specificity_prompt = """## Specificity Requirements
Please ensure your response includes:
- Clear, actionable steps
- Specific examples and code snippets where applicable
- Consideration of edge cases and error handling
- Performance considerations and optimization suggestions
- Testing or validation approaches
- Documentation and maintenance considerations"""

        return f"{prompt.strip()}\n\n{specificity_prompt}"

    def final_cleanup(self, prompt: str) -> str:
        """Final cleanup and formatting of the refined prompt"""

        # Remove excessive whitespace
        prompt = re.sub(r'\n\s*\n\s*\n', '\n\n', prompt)

        # Ensure proper spacing around headings
        prompt = re.sub(r'\n#', '\n\n#', prompt)

        # Add closing if missing
        if not any(word in prompt.lower() for word in ["complete", "finish", "done", "provide", "deliver"]):
            prompt += "\n\nPlease provide a complete, well-structured response that addresses all aspects of this request."

        return prompt.strip()

    async def analyze_prompt_improvements(self, original: str, refined: str,
                                        agent_profile: str) -> Dict[str, Any]:
        """Analyze the improvements made to the prompt using simple enhancement approach"""

        improvements = []
        confidence_score = 0.5  # Base confidence

        # Check if prompt was actually enhanced
        if refined == original:
            return {
                "improvements": [],
                "improvements_count": 0,
                "confidence_score": 0.0,
                "agent_profile_optimized": False
            }

        # Length and detail analysis
        length_ratio = len(refined) / len(original) if len(original) > 0 else 1
        if length_ratio > 1.2:
            improvements.append("Enhanced with additional details and clarity")
            confidence_score += 0.1
        elif length_ratio > 1.5:
            improvements.append("Significantly expanded with comprehensive details")
            confidence_score += 0.2

        # Structure analysis - check for enhanced organization
        structure_indicators = [
            "step", "process", "workflow", "approach", "method",
            "consider", "include", "ensure", "specific", "detailed",
            "example", "scenario", "context", "requirement"
        ]

        structure_count = sum(1 for indicator in structure_indicators if indicator in refined.lower())
        if structure_count > 3:
            improvements.append("Improved structure and organization")
            confidence_score += 0.15

        # Clarity indicators
        clarity_indicators = [
            "specifically", "clearly", "precisely", "exactly",
            "please", "ensure", "make sure", "focus on"
        ]

        clarity_count = sum(1 for indicator in clarity_indicators if indicator in refined.lower())
        if clarity_count > 2:
            improvements.append("Enhanced clarity and specificity")
            confidence_score += 0.1

        # Professional tone indicators
        professional_indicators = [
            "professional", "comprehensive", "thorough", "detailed",
            "robust", "effective", "optimal", "best practice"
        ]

        professional_count = sum(1 for indicator in professional_indicators if indicator in refined.lower())
        if professional_count > 1:
            improvements.append("Professional tone and approach")
            confidence_score += 0.1

        # Agent profile optimization
        agent_optimized = agent_profile != "default" and any(
            profile_keyword in refined.lower()
            for profile_keyword in ["developer", "research", "analysis", "technical", "code"]
        )

        if agent_optimized:
            improvements.append("Optimized for agent capabilities")
            confidence_score += 0.1

        # Cap confidence score
        confidence_score = min(confidence_score, 0.95)

        return {
            "improvements": improvements,
            "improvements_count": len(improvements),
            "confidence_score": confidence_score,
            "agent_profile_optimized": agent_optimized
        }

    def generate_suggestions(self, original: str, refined: str) -> List[str]:
        """Generate suggestions for the user"""

        suggestions = []

        # Check original prompt quality
        if len(original) < 20:
            suggestions.append("Try to provide more detailed requirements for better results")

        if not any(word in original.lower() for word in ["please", "help", "create", "make", "build"]):
            suggestions.append("Start your prompt with a clear action word (e.g., 'Create', 'Build', 'Analyze')")

        if original.count('?') > original.count('.'):
            suggestions.append("Consider using statements rather than questions for more direct results")

        # Refinement suggestions
        if len(refined) > len(original) * 2:
            suggestions.append("The refined prompt is much more detailed - this should give you better results")

        # Learning suggestions
        suggestions.append("Use this refined prompt as a template for similar requests")
        suggestions.append("Pay attention to the structured format for future prompts")

        return suggestions