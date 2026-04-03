"""
Sentinel Agent Memory System

Three-tier memory architecture:
- Short-term: Current conversation context
- Long-term: Persistent facts database
- Episodic: Session summaries and experiences
"""

from .short_term import ShortTermMemory, ContextItem
from .long_term import LongTermMemory, MemoryRecord
from .episodic import EpisodicMemory, Episode


class MemorySystem:
    """
    Unified memory system combining all memory tiers.
    """
    
    def __init__(self, base_path: str = ".sentinel"):
        """
        Initialize the complete memory system.
        
        Args:
            base_path: Base directory for persistent storage
        """
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(f"{base_path}/memory.db")
        self.episodic = EpisodicMemory(f"{base_path}/episodes.json")
    
    def get_context_for_query(self, query: str) -> str:
        """
        Get all relevant context for a query.
        
        Combines short-term context, long-term facts, and episodic memories.
        """
        sections = []
        
        # Short-term context
        short_context = self.short_term.get_context_string(max_tokens=1000)
        if short_context:
            sections.append(short_context)
        
        # Episodic context
        episodic_context = self.episodic.get_context_for_query(query, max_episodes=2)
        if episodic_context:
            sections.append(episodic_context)
        
        # Long-term relevant facts
        relevant_facts = self.long_term.search(query, limit=5)
        if relevant_facts:
            fact_lines = ["Relevant stored facts:"]
            for fact in relevant_facts:
                fact_lines.append(f"  • {fact.key}: {fact.value}")
            sections.append("\n".join(fact_lines))
        
        return "\n\n".join(sections)
    
    def save_session_summary(
        self,
        summary: str,
        key_facts: list[str],
        topics: list[str],
        stats: dict
    ) -> None:
        """Save the current session to episodic memory."""
        self.episodic.save_session(
            summary=summary,
            key_facts=key_facts,
            topics=topics,
            tool_calls=stats.get("tool_calls", 0),
            tokens_used=stats.get("tokens", 0)
        )
    
    def clear_all(self) -> dict:
        """Clear all memory systems."""
        return {
            "short_term": "cleared",
            "long_term": self.long_term.clear(),
            "episodic": self.episodic.clear()
        }


__all__ = [
    "MemorySystem",
    "ShortTermMemory",
    "LongTermMemory",
    "EpisodicMemory",
    "ContextItem",
    "MemoryRecord",
    "Episode",
]
