"""
Episodic memory for session summaries and experiences.

Stores summaries of past conversations for reference in future sessions.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class Episode:
    """A summarized conversation episode."""
    session_id: str
    timestamp: datetime
    summary: str
    key_facts: list[str]
    topics: list[str]
    tool_calls: int
    tokens_used: int
    user_queries: list[str] = field(default_factory=list)
    
    def relevance_score(self, query: str) -> float:
        """Calculate relevance of this episode to a query."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Check topic overlap
        topic_words = set()
        for topic in self.topics:
            topic_words.update(topic.lower().split())
        
        topic_overlap = len(query_words & topic_words) / max(len(query_words), 1)
        
        # Check fact overlap
        fact_text = " ".join(self.key_facts).lower()
        fact_words = set(fact_text.split())
        fact_overlap = len(query_words & fact_words) / max(len(query_words), 1)
        
        # Check summary
        summary_words = set(self.summary.lower().split())
        summary_overlap = len(query_words & summary_words) / max(len(query_words), 1)
        
        return (topic_overlap * 0.4 + fact_overlap * 0.4 + summary_overlap * 0.2)


class EpisodicMemory:
    """
    Stores episode summaries from past conversations.
    
    Features:
    - Session summaries with key facts
    - Topic tagging for retrieval
    - Relevance-based search
    - Persistent JSON storage
    """
    
    def __init__(self, path: str = ".sentinel/episodes.json"):
        """
        Initialize episodic memory.
        
        Args:
            path: Path to JSON storage file
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._episodes: dict[str, Episode] = {}
        self._load()
    
    def _load(self) -> None:
        """Load episodes from disk."""
        if self.path.exists():
            try:
                with open(self.path, "r") as f:
                    data = json.load(f)
                for session_id, info in data.items():
                    self._episodes[session_id] = Episode(
                        session_id=session_id,
                        timestamp=datetime.fromisoformat(info["timestamp"]),
                        summary=info["summary"],
                        key_facts=info.get("key_facts", []),
                        topics=info.get("topics", []),
                        tool_calls=info.get("tool_calls", 0),
                        tokens_used=info.get("tokens_used", 0),
                        user_queries=info.get("user_queries", [])
                    )
            except (json.JSONDecodeError, KeyError):
                self._episodes = {}
    
    def _save(self) -> None:
        """Save episodes to disk."""
        data = {}
        for session_id, episode in self._episodes.items():
            data[session_id] = {
                "timestamp": episode.timestamp.isoformat(),
                "summary": episode.summary,
                "key_facts": episode.key_facts,
                "topics": episode.topics,
                "tool_calls": episode.tool_calls,
                "tokens_used": episode.tokens_used,
                "user_queries": episode.user_queries
            }
        
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)
    
    def save_session(
        self,
        summary: str,
        key_facts: list[str],
        topics: Optional[list[str]] = None,
        tool_calls: int = 0,
        tokens_used: int = 0,
        user_queries: Optional[list[str]] = None,
        session_id: Optional[str] = None
    ) -> Episode:
        """
        Save a session summary.
        
        Args:
            summary: Natural language summary of the conversation
            key_facts: Important facts extracted from the conversation
            topics: Topics discussed
            tool_calls: Number of tool calls made
            tokens_used: Total tokens used
            user_queries: List of user queries in the session
            session_id: Optional custom session ID
            
        Returns:
            The saved episode
        """
        if session_id is None:
            # Generate session ID from timestamp and summary hash
            now = datetime.utcnow()
            hash_input = f"{now.isoformat()}{summary}"
            session_id = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        episode = Episode(
            session_id=session_id,
            timestamp=datetime.utcnow(),
            summary=summary,
            key_facts=key_facts,
            topics=topics or [],
            tool_calls=tool_calls,
            tokens_used=tokens_used,
            user_queries=user_queries or []
        )
        
        self._episodes[session_id] = episode
        self._save()
        
        return episode
    
    def get_session(self, session_id: str) -> Optional[Episode]:
        """Retrieve a specific session."""
        return self._episodes.get(session_id)
    
    def search(
        self,
        query: str = "",
        topics: Optional[list[str]] = None,
        limit: int = 5,
        min_relevance: float = 0.1
    ) -> list[Episode]:
        """
        Search for relevant past sessions.
        
        Args:
            query: Search query
            topics: Filter by topics
            limit: Maximum results
            min_relevance: Minimum relevance score
            
        Returns:
            List of relevant episodes
        """
        candidates = list(self._episodes.values())
        
        # Filter by topics
        if topics:
            candidates = [
                ep for ep in candidates
                if any(t.lower() in [x.lower() for x in ep.topics] for t in topics)
            ]
        
        # Score and filter by relevance
        if query:
            scored = [(ep, ep.relevance_score(query)) for ep in candidates]
            scored = [(ep, score) for ep, score in scored if score >= min_relevance]
            scored.sort(key=lambda x: x[1], reverse=True)
            candidates = [ep for ep, _ in scored[:limit]]
        else:
            # Sort by recency
            candidates.sort(key=lambda x: x.timestamp, reverse=True)
            candidates = candidates[:limit]
        
        return candidates
    
    def get_recent(self, n: int = 5) -> list[Episode]:
        """Get n most recent episodes."""
        episodes = sorted(
            self._episodes.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )
        return episodes[:n]
    
    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._episodes:
            del self._episodes[session_id]
            self._save()
            return True
        return False
    
    def clear(self) -> int:
        """Clear all episodes."""
        count = len(self._episodes)
        self._episodes.clear()
        self._save()
        return count
    
    def count(self) -> int:
        """Get total number of episodes."""
        return len(self._episodes)
    
    def get_context_for_query(self, query: str, max_episodes: int = 3) -> str:
        """
        Get relevant past context for a new query.
        
        Args:
            query: The new user query
            max_episodes: Maximum past episodes to include
            
        Returns:
            Formatted context string
        """
        relevant = self.search(query, limit=max_episodes)
        
        if not relevant:
            return ""
        
        lines = ["Relevant information from past conversations:"]
        for ep in relevant:
            lines.append(f"\n[{ep.timestamp.strftime('%Y-%m-%d')}] {ep.summary}")
            if ep.key_facts:
                for fact in ep.key_facts[:3]:
                    lines.append(f"  • {fact}")
        
        return "\n".join(lines)
