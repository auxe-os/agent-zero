"""
Tool Calling Improvements
Addresses specific issues with tool selection and calling
"""
import re
import json
from typing import Dict, Any, List, Optional
from python.helpers.print_style import PrintStyle


class ToolCallingImprovements:
    """Improvements for tool calling accuracy and performance"""
    
    def __init__(self):
        self._tool_aliases = {
            "google-scholar": ["google-scholar-mcp", "scholar", "google_scholar"],
            "web-search": ["web_search", "search", "websearch"],
            "code-execution": ["code_execution_tool", "code", "execute"],
            "knowledge": ["knowledge_tool", "search", "query"],
            "response": ["reply", "answer", "respond"]
        }
        self._mcp_tool_patterns = [
            r"google-scholar-mcp",
            r"scholar",
            r"web-search",
            r"file-system",
            r"database"
        ]
    
    def improve_tool_selection(self, user_message: str, available_tools: List[str]) -> Dict[str, Any]:
        """Improve tool selection based on user message analysis"""
        try:
            # Analyze user message for tool intent
            intent_analysis = self._analyze_user_intent(user_message)
            
            # Find best matching tool
            best_tool = self._find_best_tool_match(intent_analysis, available_tools)
            
            # Generate improved tool call
            improved_call = self._generate_improved_tool_call(intent_analysis, best_tool)
            
            return {
                "success": True,
                "original_intent": intent_analysis,
                "selected_tool": best_tool,
                "improved_call": improved_call,
                "confidence": self._calculate_confidence(intent_analysis, best_tool)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fallback": "response"
            }
    
    def _analyze_user_intent(self, user_message: str) -> Dict[str, Any]:
        """Analyze user message to determine tool intent"""
        message_lower = user_message.lower()
        
        intent = {
            "action": "unknown",
            "domain": "general",
            "keywords": [],
            "parameters": {}
        }
        
        # Google Scholar intent
        if any(keyword in message_lower for keyword in ["scholar", "academic", "research", "paper", "publication"]):
            intent["action"] = "search_academic"
            intent["domain"] = "scholar"
            intent["keywords"] = self._extract_keywords(user_message)
            
            # Extract search parameters
            if "year" in message_lower or "recent" in message_lower:
                intent["parameters"]["year_filter"] = True
            if "author" in message_lower:
                intent["parameters"]["author_filter"] = True
        
        # Web search intent
        elif any(keyword in message_lower for keyword in ["search", "find", "look up", "web"]):
            intent["action"] = "web_search"
            intent["domain"] = "web"
            intent["keywords"] = self._extract_keywords(user_message)
        
        # Code execution intent
        elif any(keyword in message_lower for keyword in ["code", "run", "execute", "python", "script"]):
            intent["action"] = "execute_code"
            intent["domain"] = "code"
            intent["keywords"] = self._extract_keywords(user_message)
        
        # Knowledge search intent
        elif any(keyword in message_lower for keyword in ["know", "information", "data", "query"]):
            intent["action"] = "knowledge_search"
            intent["domain"] = "knowledge"
            intent["keywords"] = self._extract_keywords(user_message)
        
        # General response intent
        else:
            intent["action"] = "general_response"
            intent["domain"] = "general"
            intent["keywords"] = self._extract_keywords(user_message)
        
        return intent
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        # Remove common words and extract meaningful terms
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "must"}
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords[:10]  # Limit to 10 most relevant keywords
    
    def _find_best_tool_match(self, intent: Dict[str, Any], available_tools: List[str]) -> Optional[str]:
        """Find the best matching tool for the intent"""
        if not available_tools:
            return None
        
        # Score tools based on intent matching
        tool_scores = {}
        
        for tool in available_tools:
            score = 0
            
            # Direct name matching
            if intent["domain"] in tool.lower():
                score += 10
            
            # Keyword matching
            for keyword in intent["keywords"]:
                if keyword in tool.lower():
                    score += 5
            
            # Action matching
            if intent["action"] == "search_academic" and "scholar" in tool.lower():
                score += 15
            elif intent["action"] == "web_search" and "search" in tool.lower():
                score += 15
            elif intent["action"] == "execute_code" and "code" in tool.lower():
                score += 15
            elif intent["action"] == "knowledge_search" and "knowledge" in tool.lower():
                score += 15
            
            # MCP tool preference
            if any(pattern in tool.lower() for pattern in self._mcp_tool_patterns):
                score += 5
            
            tool_scores[tool] = score
        
        # Return highest scoring tool
        if tool_scores:
            best_tool = max(tool_scores.items(), key=lambda x: x[1])
            if best_tool[1] > 0:
                return best_tool[0]
        
        return None
    
    def _generate_improved_tool_call(self, intent: Dict[str, Any], tool: Optional[str]) -> Dict[str, Any]:
        """Generate improved tool call based on intent and tool"""
        if not tool:
            return {
                "tool_name": "response",
                "tool_args": {
                    "message": "I understand you're looking for information, but I couldn't find the appropriate tool to help with your request."
                }
            }
        
        # Generate tool arguments based on intent
        tool_args = {}
        
        if intent["action"] == "search_academic" and "scholar" in tool.lower():
            tool_args = {
                "query": " ".join(intent["keywords"][:5]),  # Use top 5 keywords
                "numResults": 10
            }
            
            if intent["parameters"].get("year_filter"):
                tool_args["startYear"] = 2020
                tool_args["endYear"] = 2025
            
            if intent["parameters"].get("author_filter"):
                tool_args["author"] = True
        
        elif intent["action"] == "web_search" and "search" in tool.lower():
            tool_args = {
                "query": " ".join(intent["keywords"][:5]),
                "numResults": 10
            }
        
        elif intent["action"] == "execute_code" and "code" in tool.lower():
            tool_args = {
                "runtime": "python",
                "code": "# Add your code here",
                "session": 0
            }
        
        elif intent["action"] == "knowledge_search" and "knowledge" in tool.lower():
            tool_args = {
                "question": " ".join(intent["keywords"][:5])
            }
        
        else:
            tool_args = {
                "message": " ".join(intent["keywords"][:5])
            }
        
        return {
            "tool_name": tool,
            "tool_args": tool_args
        }
    
    def _calculate_confidence(self, intent: Dict[str, Any], tool: Optional[str]) -> float:
        """Calculate confidence score for tool selection"""
        if not tool:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on domain matching
        if intent["domain"] in tool.lower():
            confidence += 0.3
        
        # Increase confidence based on action matching
        if intent["action"] == "search_academic" and "scholar" in tool.lower():
            confidence += 0.2
        elif intent["action"] == "web_search" and "search" in tool.lower():
            confidence += 0.2
        elif intent["action"] == "execute_code" and "code" in tool.lower():
            confidence += 0.2
        elif intent["action"] == "knowledge_search" and "knowledge" in tool.lower():
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def get_tool_recommendations(self, user_message: str) -> List[str]:
        """Get tool recommendations based on user message"""
        recommendations = []
        
        message_lower = user_message.lower()
        
        if "scholar" in message_lower or "academic" in message_lower:
            recommendations.append("Use 'google-scholar-mcp' tool for academic searches")
            recommendations.append("Include query, numResults, and optional year filters")
        
        if "search" in message_lower or "find" in message_lower:
            recommendations.append("Use 'web-search' or 'knowledge_tool' for general searches")
            recommendations.append("Specify query and number of results")
        
        if "code" in message_lower or "run" in message_lower:
            recommendations.append("Use 'code_execution_tool' for code execution")
            recommendations.append("Specify runtime (python, nodejs, terminal) and code")
        
        if not recommendations:
            recommendations.append("Consider using 'knowledge_tool' for general information")
            recommendations.append("Use 'response' tool for direct answers")
        
        return recommendations


# Global tool calling improvements instance
_tool_improvements = ToolCallingImprovements()


def improve_tool_selection(user_message: str, available_tools: List[str]) -> Dict[str, Any]:
    """Improve tool selection for a user message"""
    return _tool_improvements.improve_tool_selection(user_message, available_tools)


def get_tool_recommendations(user_message: str) -> List[str]:
    """Get tool recommendations for a user message"""
    return _tool_improvements.get_tool_recommendations(user_message)
