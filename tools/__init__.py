"""
Sentinel Agent Tools

Provides tools for web search, blockchain queries, calculations, risk assessment, and more.
"""

from .base import (
    Tool,
    ToolResult,
    ToolSpec,
    ToolRegistry,
    tool,
    param,
    registry,
)

# Import all tools to register them
from . import web
from . import blockchain
from . import math
from . import risk
from . import memory
from . import exchange

__all__ = [
    "Tool",
    "ToolResult",
    "ToolSpec",
    "ToolRegistry",
    "tool",
    "param",
    "registry",
]
