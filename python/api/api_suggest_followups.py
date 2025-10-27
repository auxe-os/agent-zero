"""
Follow-up Suggestions API for Agent Zero

This API endpoint generates contextual follow-up prompt suggestions
based on agent responses to help users continue conversations effectively.
"""

import json
from typing import Dict, List, Any, Optional
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.print_style import PrintStyle


class ApiSuggestFollowups(ApiHandler):
    """API handler for follow-up suggestion requests"""

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
        """Process follow-up suggestion request"""

        # Extract parameters
        message_id = input.get("message_id", "")
        message_content = input.get("message_content", "").strip()
        context = input.get("context", "")
        agent_profile = input.get("agent_profile", "default")

        if not message_content:
            return Response(
                json.dumps({"error": "Message content is required"}),
                status=400,
                mimetype="application/json"
            )

        try:
            # Generate follow-up suggestions using utility model
            suggestions = await self.generate_followup_suggestions(
                message_content, context, agent_profile
            )

            return Response(
                json.dumps({
                    "message_id": message_id,
                    "suggestions": suggestions,
                    "agent_profile": agent_profile,
                    "context_length": len(context)
                }),
                status=200,
                mimetype="application/json"
            )

        except Exception as e:
            PrintStyle(font_color="red", background_color="black", padding=True).print(
                f"Follow-up suggestions error: {str(e)}"
            )

            return Response(
                json.dumps({
                    "error": f"Failed to generate suggestions: {str(e)}",
                    "suggestions": []
                }),
                status=500,
                mimetype="application/json"
            )

    async def generate_followup_suggestions(self, message_content: str, context: str, agent_profile: str) -> List[Dict[str, str]]:
        """Generate 3 contextual follow-up suggestions using utility model"""

        # Create the follow-up generation prompt
        followup_prompt = f"""Based on this agent response, generate exactly 3 follow-up prompt suggestions that would naturally continue the conversation. Each suggestion should be a complete, actionable prompt that builds on what was just discussed.

AGENT RESPONSE:
{message_content}

CONVERSATION CONTEXT:
{context[:1000] if context else "No previous context"}

Generate 3 follow-up suggestions in this exact JSON format:
{{
  "suggestions": [
    {{
      "title": "Brief descriptive title",
      "prompt": "Complete follow-up prompt text"
    }},
    {{
      "title": "Brief descriptive title", 
      "prompt": "Complete follow-up prompt text"
    }},
    {{
      "title": "Brief descriptive title",
      "prompt": "Complete follow-up prompt text"
    }}
  ]
}}

Make the suggestions:
- Specific and actionable
- Build naturally on the agent's response
- Vary in approach (clarification, deeper dive, related topic, implementation)
- Be concise but complete prompts
- Focus on what the user would likely want to ask next

Respond with ONLY the JSON, no other text."""

        try:
            # Use the utility model for follow-up generation
            from python.helpers.settings import get_settings
            from python.helpers.call_llm import call_llm

            settings = get_settings()

            # Call the LLM to generate follow-up suggestions
            from models import get_util_model
            model = get_util_model()

            response = await call_llm(
                system="You are an expert at generating natural conversation follow-ups. You understand context and create prompts that help users continue productive conversations with AI agents.",
                model=model,
                message=followup_prompt
            )

            # Parse the JSON response
            try:
                suggestions_data = json.loads(response.strip())
                suggestions = suggestions_data.get("suggestions", [])
                
                # Validate and clean suggestions
                validated_suggestions = []
                for i, suggestion in enumerate(suggestions[:3]):  # Ensure max 3
                    if isinstance(suggestion, dict) and "title" in suggestion and "prompt" in suggestion:
                        validated_suggestions.append({
                            "id": f"suggestion_{i+1}",
                            "title": suggestion["title"].strip(),
                            "prompt": suggestion["prompt"].strip()
                        })
                
                # Ensure we have exactly 3 suggestions
                while len(validated_suggestions) < 3:
                    validated_suggestions.append({
                        "id": f"suggestion_{len(validated_suggestions)+1}",
                        "title": f"Follow-up {len(validated_suggestions)+1}",
                        "prompt": f"Please provide more details about this topic."
                    })
                
                return validated_suggestions[:3]

            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                PrintStyle(font_color="yellow", background_color="black", padding=True).print(
                    "Failed to parse follow-up suggestions JSON, using fallback"
                )
                return self.generate_fallback_suggestions(message_content)

        except Exception as e:
            PrintStyle(font_color="red", background_color="black", padding=True).print(
                f"Follow-up generation error: {str(e)}"
            )
            return self.generate_fallback_suggestions(message_content)

    def generate_fallback_suggestions(self, message_content: str) -> List[Dict[str, str]]:
        """Generate fallback suggestions when AI generation fails"""
        
        # Simple fallback suggestions based on content analysis
        suggestions = []
        
        # Check for common patterns and generate appropriate follow-ups
        content_lower = message_content.lower()
        
        if any(word in content_lower for word in ["code", "function", "class", "implementation"]):
            suggestions.extend([
                {
                    "id": "suggestion_1",
                    "title": "Show me the code",
                    "prompt": "Can you show me the complete code implementation?"
                },
                {
                    "id": "suggestion_2", 
                    "title": "Explain the approach",
                    "prompt": "Can you explain the approach and reasoning behind this solution?"
                },
                {
                    "id": "suggestion_3",
                    "title": "Test the solution",
                    "prompt": "How would I test this solution? Can you provide test cases?"
                }
            ])
        elif any(word in content_lower for word in ["analysis", "research", "findings", "results"]):
            suggestions.extend([
                {
                    "id": "suggestion_1",
                    "title": "Dive deeper",
                    "prompt": "Can you provide more detailed analysis on this topic?"
                },
                {
                    "id": "suggestion_2",
                    "title": "Related topics",
                    "prompt": "What are some related topics I should explore?"
                },
                {
                    "id": "suggestion_3",
                    "title": "Practical application",
                    "prompt": "How can I apply these findings in practice?"
                }
            ])
        else:
            # Generic follow-ups
            suggestions.extend([
                {
                    "id": "suggestion_1",
                    "title": "More details",
                    "prompt": "Can you provide more details about this?"
                },
                {
                    "id": "suggestion_2",
                    "title": "Examples",
                    "prompt": "Can you give me some examples?"
                },
                {
                    "id": "suggestion_3",
                    "title": "Next steps",
                    "prompt": "What should I do next?"
                }
            ])
        
        return suggestions[:3]
