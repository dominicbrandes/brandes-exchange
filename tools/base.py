"""
Tool system for Sentinel Agent.

Provides base class and registry for agent tools.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TypeVar, ParamSpec
from functools import wraps
import json
import asyncio
import traceback


P = ParamSpec('P')
T = TypeVar('T')

# Alias for backwards compatibility
Tool = 'ToolSpec'


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    def to_observation(self) -> str:
        """Convert to observation string for the agent."""
        if self.success:
            if isinstance(self.data, dict):
                return json.dumps(self.data, indent=2, default=str)
            return str(self.data)
        return f"Error: {self.error}"


@dataclass
class ToolSpec:
    """Specification for a tool."""
    name: str
    description: str
    parameters: dict  # JSON Schema
    func: Callable
    is_async: bool = False
    requires_confirmation: bool = False
    
    def to_anthropic_tool(self) -> dict:
        """Convert to Anthropic API tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


class ToolRegistry:
    """Registry of available tools."""
    
    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}
    
    def register(self, tool: ToolSpec) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[ToolSpec]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def get_all_specs(self) -> list[ToolSpec]:
        """Get all tool specifications."""
        return list(self._tools.values())
    
    def to_anthropic_tools(self) -> list[dict]:
        """Convert all tools to Anthropic API format."""
        return [tool.to_anthropic_tool() for tool in self._tools.values()]
    
    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name with given arguments."""
        tool = self.get(name)
        if tool is None:
            return ToolResult(
                success=False,
                data=None,
                error=f"Unknown tool: {name}"
            )
        
        try:
            if tool.is_async:
                result = await tool.func(**kwargs)
            else:
                # Run sync function in executor to not block
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: tool.func(**kwargs))
            
            return ToolResult(
                success=True,
                data=result,
                metadata={"tool": name}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"{type(e).__name__}: {str(e)}",
                metadata={"tool": name, "traceback": traceback.format_exc()}
            )


# Global registry
registry = ToolRegistry()


def tool(
    name: str,
    description: str,
    parameters: Optional[dict] = None,
    requires_confirmation: bool = False,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to register a function as a tool.
    
    Usage:
        @tool(
            name="web_search",
            description="Search the web for information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        )
        def web_search(query: str) -> dict:
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        # Determine if async
        is_async = asyncio.iscoroutinefunction(func)
        
        # Build parameter schema from function signature if not provided
        param_schema = parameters or {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Create and register tool spec
        spec = ToolSpec(
            name=name,
            description=description,
            parameters=param_schema,
            func=func,
            is_async=is_async,
            requires_confirmation=requires_confirmation,
        )
        registry.register(spec)
        
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Helper for creating parameter schemas
def param(
    type: str,
    description: str,
    enum: Optional[list] = None,
    default: Any = None,
) -> dict:
    """Helper to create parameter schema."""
    schema = {"type": type, "description": description}
    if enum:
        schema["enum"] = enum
    if default is not None:
        schema["default"] = default
    return schema
