"""
Tool Registry for ARA-1 Autonomous Financial Research Agent
Manages all tools available to the agent
"""

from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class ToolDefinition:
    """Defines a single tool in the registry"""
    name: str
    description: str
    function: Callable
    input_schema: Dict[str, Any]
    fallback_tools: list = field(default_factory=list)
    is_active: bool = True


class ToolRegistry:
    """
    Central registry of all tools available to the agent.
    Handles registration, lookup, and execution of tools.
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._call_counts: Dict[str, int] = {}
        self._failure_counts: Dict[str, int] = {}

    def register(
        self,
        name: str,
        description: str,
        function: Callable,
        input_schema: Dict[str, Any],
        fallback_tools: list = None
    ) -> None:
        """Register a tool in the registry"""
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            function=function,
            input_schema=input_schema,
            fallback_tools=fallback_tools or []
        )
        self._call_counts[name] = 0
        self._failure_counts[name] = 0
        print(f"[Registry] Registered tool: {name}")

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name"""
        return self._tools.get(name)

    def execute(self, name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name with given inputs"""
        tool = self.get_tool(name)

        if not tool:
            return {
                "success": False,
                "error": f"Tool '{name}' not found in registry",
                "data": None
            }

        if not tool.is_active:
            return {
                "success": False,
                "error": f"Tool '{name}' is currently inactive",
                "data": None
            }

        try:
            self._call_counts[name] += 1
            result = tool.function(**inputs)
            return {
                "success": True,
                "error": None,
                "data": result,
                "tool_used": name
            }
        except Exception as e:
            self._failure_counts[name] += 1
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "tool_used": name
            }

    def get_all_descriptions(self) -> str:
        """Returns all tool descriptions for injection into system prompt"""
        descriptions = []
        for name, tool in self._tools.items():
            if tool.is_active:
                descriptions.append(f"- {name}: {tool.description}")
        return "\n".join(descriptions)

    def get_stats(self) -> Dict[str, Any]:
        """Returns usage statistics for evaluation"""
        return {
            "total_tools": len(self._tools),
            "call_counts": self._call_counts.copy(),
            "failure_counts": self._failure_counts.copy()
        }

    def deactivate_tool(self, name: str) -> None:
        """Deactivate a tool (circuit breaker)"""
        if name in self._tools:
            self._tools[name].is_active = False
            print(f"[Registry] Deactivated tool: {name}")

    def activate_tool(self, name: str) -> None:
        """Reactivate a tool"""
        if name in self._tools:
            self._tools[name].is_active = True
            print(f"[Registry] Reactivated tool: {name}")

    def list_tools(self) -> list:
        """List all registered tool names"""
        return list(self._tools.keys())