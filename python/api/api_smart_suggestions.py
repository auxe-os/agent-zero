from python.helpers.api import ApiHandler, Request, Response
from python.helpers.errors import RepairableException
import json
import re

class ApiSmartSuggestions(ApiHandler):
    def __init__(self, app, thread_lock):
        super().__init__(app, thread_lock)
        self.endpoint = "/api_smart_suggestions"
        self.methods = ["POST"]

    async def process(self, input: dict, request: Request) -> dict:
        try:
            # Parse request data
            data = input 
            if not data:
                raise RepairableException("No JSON data provided")
            
            input_text = data.get("input", "").strip()
            context = data.get("context", "")
            max_suggestions = data.get("max_suggestions", 3)
            
            if not input_text:
                raise RepairableException("Input text is required")
            
            if len(input_text) < 2:
                return {"suggestions": []}
            
            # Generate smart suggestions
            suggestions = await self.generate_smart_suggestions(input_text, context, max_suggestions)
            
            return {
                "suggestions": suggestions,
                "input": input_text,
                "context_length": len(context)
            }
            
        except Exception as e:
            raise RepairableException(f"Smart suggestions error: {str(e)}")

    async def generate_smart_suggestions(self, input_text: str, context: str = "", max_suggestions: int = 3) -> list:
        """Generate smart suggestions based on input text and context"""
        
        # Create a focused prompt for smart suggestions
        prompt = f"""You are a helpful AI assistant that provides smart completion suggestions for user input.

User is typing: "{input_text}"

Recent conversation context:
{context if context else "No recent context"}

Provide {max_suggestions} smart completion suggestions that:
1. Complete the user's thought naturally
2. Are contextually relevant to the conversation
3. Are concise but helpful
4. Match the user's apparent intent

Format each suggestion as a complete, natural continuation of their input.
Return only the suggestions, one per line, without numbering or bullet points."""

        try:
            # Get agent context to call utility model
            agent_context = self.get_context("")
            agent = agent_context.agent0
            
            # Call utility model for fast suggestions
            response = await agent.call_utility_model(
                system="You are a helpful AI assistant that provides smart completion suggestions.",
                message=prompt,
                background=True
            )
            
            if not response:
                return self.get_fallback_suggestions(input_text)
            
            # Parse suggestions from response
            suggestions_lines = [line.strip() for line in response.split('\n') if line.strip()]
            
            # Clean and format suggestions
            suggestions = []
            for i, suggestion in enumerate(suggestions_lines[:max_suggestions]):
                if suggestion and len(suggestion) > len(input_text):
                    suggestions.append({
                        "id": f"suggestion_{i+1}",
                        "text": suggestion,
                        "title": self.get_suggestion_title(suggestion, input_text)
                    })
            
            # If we don't have enough suggestions, add fallbacks
            while len(suggestions) < max_suggestions:
                fallback = self.get_fallback_suggestion(input_text, len(suggestions))
                if fallback:
                    suggestions.append(fallback)
                else:
                    break
            
            return suggestions
            
        except Exception as e:
            print(f"Error generating smart suggestions: {e}")
            return self.get_fallback_suggestions(input_text)

    def get_fallback_suggestions(self, input_text: str) -> list:
        """Provide fallback suggestions when AI generation fails"""
        suggestions = []
        
        # Common completions based on input patterns
        if input_text.lower().startswith("how"):
            suggestions.append({
                "id": "fallback_1",
                "text": f"{input_text} can I help you with that?",
                "title": "Helpful Response"
            })
        elif input_text.lower().startswith("what"):
            suggestions.append({
                "id": "fallback_1", 
                "text": f"{input_text} would you like to know?",
                "title": "Question Completion"
            })
        elif input_text.lower().startswith("can you"):
            suggestions.append({
                "id": "fallback_1",
                "text": f"{input_text} help me with that?",
                "title": "Assistance Offer"
            })
        else:
            # Generic completions
            suggestions.append({
                "id": "fallback_1",
                "text": f"{input_text} please?",
                "title": "Polite Request"
            })
            
            suggestions.append({
                "id": "fallback_2", 
                "text": f"{input_text} and explain it clearly.",
                "title": "Detailed Explanation"
            })
        
        return suggestions[:3]

    def get_fallback_suggestion(self, input_text: str, index: int) -> dict:
        """Get a single fallback suggestion"""
        fallbacks = [
            f"{input_text} in detail.",
            f"{input_text} with examples.",
            f"{input_text} step by step.",
            f"{input_text} and provide context.",
            f"{input_text} clearly and concisely."
        ]
        
        if index < len(fallbacks):
            return {
                "id": f"fallback_{index+1}",
                "text": fallbacks[index],
                "title": "Completion"
            }
        return {}

    def get_suggestion_title(self, suggestion: str, input_text: str) -> str:
        """Generate a title for the suggestion based on its content"""
        suggestion_lower = suggestion.lower()
        
        if "?" in suggestion:
            return "Question"
        elif "please" in suggestion_lower or "could you" in suggestion_lower:
            return "Request"
        elif "explain" in suggestion_lower or "describe" in suggestion_lower:
            return "Explanation"
        elif "how" in suggestion_lower:
            return "How-to"
        elif "what" in suggestion_lower:
            return "Definition"
        elif "example" in suggestion_lower:
            return "Example"
        else:
            return "Suggestion"
