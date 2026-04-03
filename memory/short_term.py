"""
Short-term memory for conversation context.

Maintains recent messages and extracted facts within a single session.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from collections import deque


@dataclass
class ContextItem:
    """A single item in short-term memory."""
    content: str
    role: str  # "user", "assistant", "system"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


class ShortTermMemory:
    """
    Manages conversation context within a session.
    
    Features:
    - Fixed-size sliding window of recent messages
    - Extracted facts from conversation
    - Query-relevant context retrieval
    """
    
    def __init__(self, max_items: int = 20):
        """
        Initialize short-term memory.
        
        Args:
            max_items: Maximum number of items to retain
        """
        self.max_items = max_items
        self._messages: deque[ContextItem] = deque(maxlen=max_items)
        self._facts: dict[str, Any] = {}
        self._session_start = datetime.utcnow()
    
    def add(self, content: str, role: str = "assistant", **metadata) -> None:
        """
        Add an item to memory.
        
        Args:
            content: The content to remember
            role: Who produced this content
            **metadata: Additional metadata
        """
        item = ContextItem(
            content=content,
            role=role,
            metadata=metadata
        )
        self._messages.append(item)
    
    def add_fact(self, key: str, value: Any) -> None:
        """
        Store an extracted fact.
        
        Args:
            key: Fact identifier
            value: Fact value
        """
        self._facts[key] = {
            "value": value,
            "extracted_at": datetime.utcnow().isoformat()
        }
    
    def get_recent(self, n: int = 5) -> list[ContextItem]:
        """Get the n most recent items."""
        items = list(self._messages)
        return items[-n:] if len(items) >= n else items
    
    def get_context_string(self, max_tokens: int = 2000) -> str:
        """
        Get context as a formatted string for injection into prompts.
        
        Args:
            max_tokens: Approximate max tokens (4 chars per token)
        """
        lines = []
        char_limit = max_tokens * 4
        
        # Add facts first
        if self._facts:
            lines.append("Known facts from this conversation:")
            for key, data in self._facts.items():
                lines.append(f"- {key}: {data['value']}")
            lines.append("")
        
        # Add recent messages
        lines.append("Recent conversation:")
        for item in self.get_recent(10):
            role_label = {"user": "User", "assistant": "Agent", "system": "System"}.get(item.role, item.role)
            content_preview = item.content[:200] + "..." if len(item.content) > 200 else item.content
            lines.append(f"[{role_label}]: {content_preview}")
        
        context = "\n".join(lines)
        
        # Truncate if too long
        if len(context) > char_limit:
            context = context[:char_limit] + "\n... [truncated]"
        
        return context
    
    def search(self, query: str) -> list[ContextItem]:
        """
        Search memory for relevant items.
        
        Simple keyword matching - could be enhanced with embeddings.
        """
        query_lower = query.lower()
        keywords = query_lower.split()
        
        results = []
        for item in self._messages:
            content_lower = item.content.lower()
            if any(kw in content_lower for kw in keywords):
                results.append(item)
        
        return results
    
    def clear(self) -> None:
        """Clear all short-term memory."""
        self._messages.clear()
        self._facts.clear()
        self._session_start = datetime.utcnow()
    
    @property
    def size(self) -> int:
        """Number of items in memory."""
        return len(self._messages)
    
    @property
    def facts(self) -> dict[str, Any]:
        """Get all stored facts."""
        return self._facts.copy()
    
    def to_dict(self) -> dict:
        """Serialize memory state."""
        return {
            "messages": [
                {
                    "content": item.content,
                    "role": item.role,
                    "timestamp": item.timestamp.isoformat(),
                    "metadata": item.metadata
                }
                for item in self._messages
            ],
            "facts": self._facts,
            "session_start": self._session_start.isoformat()
        }
