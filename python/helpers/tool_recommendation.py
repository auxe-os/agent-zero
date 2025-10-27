"""
Tool Recommendation System for Agent Zero

This module provides intelligent tool selection and recommendation capabilities
to help agents choose the most appropriate tools for their tasks.
"""

import re
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from python.helpers.tool_analytics import get_tool_analytics
from python.helpers.print_style import PrintStyle


@dataclass
class ToolRecommendation:
    """Tool recommendation with reasoning"""
    tool_name: str
    confidence_score: float
    reasoning: List[str]
    success_rate: float
    avg_execution_time: float
    agent_preference: float


class ToolRecommendationEngine:
    """Engine for providing intelligent tool recommendations"""

    def __init__(self):
        self.analytics = get_tool_analytics()
        self.tool_patterns = self._initialize_tool_patterns()

    def _initialize_tool_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize tool matching patterns and heuristics"""
        return {
            "code_execution": {
                "keywords": ["execute", "run", "code", "python", "script", "terminal", "bash", "command"],
                "patterns": [r"\brun\s+(?:python|node|bash|script)\b", r"\bexecute\s+\w+\b", r"\bcode\s+(?:execution|run|play)\b"],
                "contexts": ["programming", "development", "testing", "debugging"],
                "indicators": ["file.py", "file.js", "import", "def ", "function", "class "],
                "weight": 0.9
            },
            "search_engine": {
                "keywords": ["search", "find", "lookup", "research", "web", "online", "information", "documentation"],
                "patterns": [r"\bsearch\s+(?:for|the|web|online)\b", r"\bfind\s+(?:information|about|on)\b", r"\blook\s+up\b"],
                "contexts": ["research", "information gathering", "learning", "documentation"],
                "indicators": ["what is", "how to", "documentation", "tutorial", "example"],
                "weight": 0.8
            },
            "memory_load": {
                "keywords": ["remember", "recall", "previous", "earlier", "memory", "past", "history", "before"],
                "patterns": [r"\bwhat\s+(?:did|was)\b", r"\bprevious\s+(?:conversation|discussion|task)\b", r"\bremember\s+when\b"],
                "contexts": ["context recall", "information retrieval", "continuity"],
                "indicators": ["as I mentioned", "earlier we", "previously", "in the past"],
                "weight": 0.7
            },
            "memory_save": {
                "keywords": ["save", "store", "remember", "memorize", "keep", "record", "note"],
                "patterns": [r"\bsave\s+(?:this|that|information)\b", r"\bremember\s+(?:this|for\s+later)\b", r"\bstore\s+(?:this|information)\b"],
                "contexts": ["information storage", "knowledge retention", "future reference"],
                "indicators": ["important", "for later", "don't forget", "keep in mind"],
                "weight": 0.6
            },
            "call_subordinate": {
                "keywords": ["delegate", "help", "specialist", "expert", "subordinate", "assistant", "collaborate"],
                "patterns": [r"\bneed\s+(?:help|assistance|support)\b", r"\bdelegate\s+(?:task|work)\b", r"\bspecialist\s+(?:help|needed|required)\b"],
                "contexts": ["task delegation", "specialized expertise", "parallel processing"],
                "indicators": ["complex task", "specialized knowledge", "multiple steps", "different domain"],
                "weight": 0.8
            },
            "browser": {
                "keywords": ["browser", "web", "website", "page", "click", "navigate", "scrape", "selenium"],
                "patterns": [r"\bopen\s+(?:website|web\s+page|url)\b", r"\bclick\s+(?:button|link|element)\b", r"\bnavigate\s+(?:to|through)\b"],
                "contexts": ["web interaction", "browser automation", "web scraping"],
                "indicators": ["http", "www.", "website", "web page", "form", "button"],
                "weight": 0.8
            }
        }

    def recommend_tools(self, task_description: str, agent_name: str,
                        max_recommendations: int = 5) -> List[ToolRecommendation]:
        """Recommend tools for a given task and agent"""
        task_lower = task_description.lower()
        recommendations = []

        # Analyze task for each tool category
        for tool_name, pattern_info in self.tool_patterns.items():
            score = self._calculate_tool_score(task_lower, tool_name, agent_name, pattern_info)

            if score > 0.1:  # Only include tools with meaningful scores
                metrics = self.analytics.get_tool_metrics(tool_name)
                agent_pref = self.analytics.agent_preferences.get(agent_name, {}).get(tool_name, 0)
                max_pref = max(self.analytics.agent_preferences.get(agent_name, {}).values()) if self.analytics.agent_preferences.get(agent_name) else 1

                recommendation = ToolRecommendation(
                    tool_name=tool_name,
                    confidence_score=score,
                    reasoning=self._generate_reasoning(task_lower, tool_name, pattern_info),
                    success_rate=metrics.success_rate if metrics.total_uses > 0 else 0.5,
                    avg_execution_time=metrics.avg_execution_time if metrics.total_uses > 0 else 1.0,
                    agent_preference=agent_pref / max_pref if max_pref > 0 else 0
                )
                recommendations.append(recommendation)

        # Sort by confidence score and return top recommendations
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
        return recommendations[:max_recommendations]

    def _calculate_tool_score(self, task_lower: str, tool_name: str, agent_name: str,
                            pattern_info: Dict[str, Any]) -> float:
        """Calculate score for how well a tool matches the task"""
        score = 0.0

        # Keyword matching
        keyword_matches = sum(1 for keyword in pattern_info["keywords"] if keyword in task_lower)
        if keyword_matches > 0:
            score += (keyword_matches / len(pattern_info["keywords"])) * 0.3

        # Pattern matching
        pattern_matches = sum(1 for pattern in pattern_info["patterns"] if re.search(pattern, task_lower))
        if pattern_matches > 0:
            score += (pattern_matches / len(pattern_info["patterns"])) * 0.4

        # Context matching
        context_matches = sum(1 for context in pattern_info["contexts"] if context in task_lower)
        if context_matches > 0:
            score += (context_matches / len(pattern_info["contexts"])) * 0.2

        # Indicator matching
        indicator_matches = sum(1 for indicator in pattern_info["indicators"] if indicator in task_lower)
        if indicator_matches > 0:
            score += (indicator_matches / len(pattern_info["indicators"])) * 0.1

        # Apply tool-specific weight
        score *= pattern_info["weight"]

        # Agent preference bonus
        agent_pref = self.analytics.agent_preferences.get(agent_name, {}).get(tool_name, 0)
        if agent_pref > 0:
            max_pref = max(self.analytics.agent_preferences.get(agent_name, {}).values())
            if max_pref > 0:
                score += (agent_pref / max_pref) * 0.2

        # Historical performance bonus
        metrics = self.analytics.get_tool_metrics(tool_name)
        if metrics.total_uses > 0:
            if metrics.success_rate > 0.8:
                score += 0.1
            if metrics.avg_execution_time < 3.0:
                score += 0.05

        return min(score, 1.0)  # Cap at 1.0

    def _generate_reasoning(self, task_lower: str, tool_name: str,
                          pattern_info: Dict[str, Any]) -> List[str]:
        """Generate reasoning for why a tool is recommended"""
        reasoning = []

        # Check keyword matches
        matched_keywords = [kw for kw in pattern_info["keywords"] if kw in task_lower]
        if matched_keywords:
            reasoning.append(f"Task contains relevant keywords: {', '.join(matched_keywords[:3])}")

        # Check pattern matches
        for pattern in pattern_info["patterns"]:
            if re.search(pattern, task_lower):
                reasoning.append(f"Task matches known pattern for {tool_name}")
                break

        # Check agent preferences
        # This would need the agent_name parameter, so we'll skip this in the general reasoning

        # Check performance
        metrics = self.analytics.get_tool_metrics(tool_name)
        if metrics.total_uses > 0:
            if metrics.success_rate > 0.9:
                reasoning.append(f"High success rate ({metrics.success_rate:.1%}) with this tool")
            if metrics.avg_execution_time < 2.0:
                reasoning.append(f"Fast execution time ({metrics.avg_execution_time:.1f}s)")

        if not reasoning:
            reasoning.append(f"General capability match for {tool_name}")

        return reasoning

    def get_tool_usage_guidance(self, tool_name: str) -> Dict[str, Any]:
        """Get detailed guidance for using a specific tool"""
        if tool_name in self.tool_patterns:
            pattern_info = self.tool_patterns[tool_name]
            metrics = self.analytics.get_tool_metrics(tool_name)

            return {
                "description": pattern_info.get("description", f"Tool for {tool_name}"),
                "best_for": pattern_info.get("contexts", []),
                "keywords": pattern_info.get("keywords", []),
                "success_rate": metrics.success_rate if metrics.total_uses > 0 else None,
                "avg_execution_time": metrics.avg_execution_time if metrics.total_uses > 0 else None,
                "common_errors": list(metrics.common_error_patterns.keys())[:3] if metrics.total_uses > 0 else [],
                "tips": self._generate_tool_tips(tool_name, pattern_info)
            }

        return {"message": f"No detailed guidance available for {tool_name}"}

    def _generate_tool_tips(self, tool_name: str, pattern_info: Dict[str, Any]) -> List[str]:
        """Generate usage tips for a tool"""
        tips = []

        if tool_name == "code_execution":
            tips.extend([
                "Use for running Python scripts and terminal commands",
                "Specify runtime: 'python', 'nodejs', or 'terminal'",
                "Use session parameter to maintain state across commands"
            ])
        elif tool_name == "search_engine":
            tips.extend([
                "Be specific in your search queries for better results",
                "Use quotes for exact phrases: \"exact phrase\"",
                "Combine keywords for targeted searches"
            ])
        elif tool_name == "memory_load":
            tips.extend([
                "Use lower threshold (0.5-0.6) for broader searches",
                "Use filter parameter to search by metadata fields",
                "Set appropriate limit to avoid information overload"
            ])
        elif tool_name == "call_subordinate":
            tips.extend([
                "Clearly define the role and task for the subordinate",
                "Use specialized profiles for domain-specific tasks",
                "Set reset='true' for new subordinates, 'false' for continuing"
            ])

        return tips

    def analyze_task_complexity(self, task_description: str) -> Dict[str, Any]:
        """Analyze task complexity and suggest approach"""
        task_lower = task_description.lower()

        # Complexity indicators
        complexity_indicators = {
            "high": ["complex", "multiple", "several", "various", "integrate", "system", "architecture"],
            "medium": ["implement", "create", "build", "develop", "design"],
            "low": ["simple", "basic", "quick", "single", "individual"]
        }

        complexity_score = 0
        detected_indicators = []

        for level, indicators in complexity_indicators.items():
            matches = [ind for ind in indicators if ind in task_lower]
            if matches:
                weight = {"high": 3, "medium": 2, "low": 1}[level]
                complexity_score += len(matches) * weight
                detected_indicators.extend(matches)

        # Determine complexity level
        if complexity_score >= 5:
            complexity_level = "high"
            approach = "Consider breaking into subtasks and using call_subordinate"
        elif complexity_score >= 2:
            complexity_level = "medium"
            approach = "Use appropriate tools and consider memory for important information"
        else:
            complexity_level = "low"
            approach = "Direct tool usage should be sufficient"

        return {
            "complexity_level": complexity_level,
            "complexity_score": complexity_score,
            "detected_indicators": detected_indicators,
            "recommended_approach": approach,
            "suggested_tools": self.recommend_tools(task_description, "agent0", 3)
        }


# Global instance
_recommendation_engine: Optional[ToolRecommendationEngine] = None


def get_recommendation_engine() -> ToolRecommendationEngine:
    """Get the global recommendation engine instance"""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = ToolRecommendationEngine()
    return _recommendation_engine


def recommend_tools_for_task(task_description: str, agent_name: str,
                            max_recommendations: int = 5) -> List[ToolRecommendation]:
    """Convenience function to get tool recommendations"""
    engine = get_recommendation_engine()
    return engine.recommend_tools(task_description, agent_name, max_recommendations)


def analyze_task(task_description: str) -> Dict[str, Any]:
    """Analyze task complexity and get recommendations"""
    engine = get_recommendation_engine()
    return engine.analyze_task_complexity(task_description)