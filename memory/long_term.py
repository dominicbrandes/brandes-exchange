"""
Long-term memory for persistent facts and knowledge.

Persists across sessions using SQLite or JSON file storage.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Any, List
from dataclasses import dataclass


@dataclass
class MemoryRecord:
    """A persistent memory record."""
    key: str
    value: Any
    source: str
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    tags: list[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class LongTermMemory:
    """
    Persistent memory store for facts and knowledge.
    
    Features:
    - SQLite-backed persistent storage
    - Tagging and categorization
    - Source tracking for provenance
    - Access counting for relevance
    """
    
    def __init__(self, path: str = ".sentinel/memory.db"):
        """
        Initialize long-term memory.
        
        Args:
            path: Path to SQLite database file
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    source TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    tags TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tags ON memories(tags)
            """)
            conn.commit()
    
    def store(
        self,
        key: str,
        value: Any,
        source: str = "",
        tags: Optional[list[str]] = None
    ) -> MemoryRecord:
        """
        Store a fact in long-term memory.
        
        Args:
            key: Unique identifier for this memory
            value: The data to store (must be JSON-serializable)
            source: Where this information came from
            tags: Optional tags for categorization
            
        Returns:
            The stored memory record
        """
        tags = tags or []
        now = datetime.utcnow().isoformat()
        
        value_json = json.dumps(value, default=str)
        tags_json = json.dumps(tags)
        
        with sqlite3.connect(self.path) as conn:
            # Upsert
            conn.execute("""
                INSERT INTO memories (key, value, source, created_at, updated_at, access_count, tags)
                VALUES (?, ?, ?, ?, ?, 0, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    source = excluded.source,
                    updated_at = excluded.updated_at,
                    tags = excluded.tags
            """, (key, value_json, source, now, now, tags_json))
            conn.commit()
        
        return MemoryRecord(
            key=key,
            value=value,
            source=source,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
            tags=tags
        )
    
    def recall(self, key: str) -> Optional[MemoryRecord]:
        """
        Recall a specific memory by key.
        
        Args:
            key: The memory key to retrieve
            
        Returns:
            The memory record if found, None otherwise
        """
        with sqlite3.connect(self.path) as conn:
            # Increment access count
            conn.execute("""
                UPDATE memories SET access_count = access_count + 1
                WHERE key = ?
            """, (key,))
            
            cursor = conn.execute("""
                SELECT key, value, source, created_at, updated_at, access_count, tags
                FROM memories WHERE key = ?
            """, (key,))
            
            row = cursor.fetchone()
            if row:
                return MemoryRecord(
                    key=row[0],
                    value=json.loads(row[1]),
                    source=row[2],
                    created_at=datetime.fromisoformat(row[3]),
                    updated_at=datetime.fromisoformat(row[4]),
                    access_count=row[5],
                    tags=json.loads(row[6]) if row[6] else []
                )
        return None
    
    def search(
        self,
        query: str = "",
        tags: Optional[list[str]] = None,
        limit: int = 10
    ) -> list[MemoryRecord]:
        """
        Search memories by keyword or tag.
        
        Args:
            query: Keyword to search for in keys and values
            tags: Filter by tags
            limit: Maximum results to return
            
        Returns:
            List of matching memory records
        """
        conditions = []
        params = []
        
        if query:
            conditions.append("(key LIKE ? OR value LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
        
        if tags:
            for tag in tags:
                conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(f"""
                SELECT key, value, source, created_at, updated_at, access_count, tags
                FROM memories
                WHERE {where_clause}
                ORDER BY access_count DESC, updated_at DESC
                LIMIT ?
            """, (*params, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append(MemoryRecord(
                    key=row[0],
                    value=json.loads(row[1]),
                    source=row[2],
                    created_at=datetime.fromisoformat(row[3]),
                    updated_at=datetime.fromisoformat(row[4]),
                    access_count=row[5],
                    tags=json.loads(row[6]) if row[6] else []
                ))
            return results
    
    def delete(self, key: str) -> bool:
        """
        Delete a memory.
        
        Args:
            key: The memory key to delete
            
        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute("DELETE FROM memories WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0
    
    def clear(self) -> int:
        """
        Clear all memories.
        
        Returns:
            Number of memories deleted
        """
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute("DELETE FROM memories")
            conn.commit()
            return cursor.rowcount
    
    def list_keys(self, prefix: str = "") -> list[str]:
        """List all memory keys, optionally filtered by prefix."""
        with sqlite3.connect(self.path) as conn:
            if prefix:
                cursor = conn.execute(
                    "SELECT key FROM memories WHERE key LIKE ?",
                    (f"{prefix}%",)
                )
            else:
                cursor = conn.execute("SELECT key FROM memories")
            return [row[0] for row in cursor.fetchall()]
    
    def count(self) -> int:
        """Get total number of memories."""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM memories")
            return cursor.fetchone()[0]
    
    def export(self) -> dict:
        """Export all memories as a dictionary."""
        memories = self.search(limit=10000)
        return {
            m.key: {
                "value": m.value,
                "source": m.source,
                "tags": m.tags,
                "created_at": m.created_at.isoformat(),
                "access_count": m.access_count
            }
            for m in memories
        }
    
    def import_data(self, data: dict) -> int:
        """
        Import memories from a dictionary.
        
        Args:
            data: Dictionary of memories to import
            
        Returns:
            Number of memories imported
        """
        count = 0
        for key, info in data.items():
            self.store(
                key=key,
                value=info.get("value"),
                source=info.get("source", "import"),
                tags=info.get("tags", [])
            )
            count += 1
        return count
