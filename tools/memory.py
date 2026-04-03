"""
Memory and report generation tools.
"""

import json
from datetime import datetime
from typing import Optional, Any
from pathlib import Path

from .base import tool


# In-memory store (would use SQLite/Redis in production)
_memory_store: dict[str, dict] = {}


@tool(
    name="store_memory",
    description="Store a fact or piece of information for later recall. Use for important data points that might be needed across questions.",
    parameters={
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "Unique key to identify this memory (e.g., 'eigenlayer_tvl_2024_04')"
            },
            "value": {
                "type": "object",
                "description": "The data to store (can be any JSON-serializable object)"
            },
            "source": {
                "type": "string",
                "description": "Source of this information (URL or description)"
            },
            "ttl_hours": {
                "type": "integer",
                "description": "Hours until this memory expires (0 for permanent)",
                "default": 24
            }
        },
        "required": ["key", "value"]
    }
)
def store_memory(
    key: str,
    value: Any,
    source: str = "",
    ttl_hours: int = 24
) -> dict:
    """
    Store information in memory.
    """
    global _memory_store
    
    _memory_store[key] = {
        "value": value,
        "source": source,
        "stored_at": datetime.utcnow().isoformat(),
        "ttl_hours": ttl_hours,
    }
    
    return {
        "status": "stored",
        "key": key,
        "expires": f"in {ttl_hours} hours" if ttl_hours > 0 else "never"
    }


@tool(
    name="recall_memory",
    description="Recall previously stored information. Use before searching the web to check if we already have this data.",
    parameters={
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "Key of the memory to recall"
            },
            "key_pattern": {
                "type": "string",
                "description": "Pattern to match multiple keys (e.g., 'eigenlayer_*')"
            }
        },
        "required": []
    }
)
def recall_memory(key: Optional[str] = None, key_pattern: Optional[str] = None) -> dict:
    """
    Recall information from memory.
    """
    global _memory_store
    
    if key:
        if key in _memory_store:
            memory = _memory_store[key]
            return {
                "found": True,
                "key": key,
                "value": memory["value"],
                "source": memory["source"],
                "stored_at": memory["stored_at"]
            }
        return {"found": False, "key": key}
    
    if key_pattern:
        # Simple wildcard matching
        pattern = key_pattern.replace("*", "")
        matches = {
            k: v for k, v in _memory_store.items()
            if pattern in k
        }
        return {
            "found": len(matches) > 0,
            "pattern": key_pattern,
            "matches": matches
        }
    
    # Return all memories
    return {
        "total_memories": len(_memory_store),
        "keys": list(_memory_store.keys())
    }


@tool(
    name="clear_memory",
    description="Clear stored memories. Use to reset state or remove outdated information.",
    parameters={
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "Specific key to clear (leave empty to clear all)"
            }
        },
        "required": []
    }
)
def clear_memory(key: Optional[str] = None) -> dict:
    """
    Clear memories.
    """
    global _memory_store
    
    if key:
        if key in _memory_store:
            del _memory_store[key]
            return {"status": "cleared", "key": key}
        return {"status": "not_found", "key": key}
    
    count = len(_memory_store)
    _memory_store.clear()
    return {"status": "cleared_all", "count": count}


@tool(
    name="generate_report",
    description="Generate a structured markdown report from collected data. Use after gathering all necessary information.",
    parameters={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Report title"
            },
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "heading": {"type": "string"},
                        "content": {"type": "string"},
                        "data": {"type": "object"}
                    }
                },
                "description": "Report sections"
            },
            "summary": {
                "type": "string",
                "description": "Executive summary (1-2 sentences)"
            },
            "sources": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of sources/URLs cited"
            },
            "format": {
                "type": "string",
                "enum": ["markdown", "json", "text"],
                "default": "markdown"
            }
        },
        "required": ["title", "sections"]
    }
)
def generate_report(
    title: str,
    sections: list[dict],
    summary: str = "",
    sources: Optional[list[str]] = None,
    format: str = "markdown"
) -> dict:
    """
    Generate a formatted report.
    """
    sources = sources or []
    
    if format == "json":
        return {
            "title": title,
            "summary": summary,
            "sections": sections,
            "sources": sources,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    # Build markdown report
    lines = [
        f"# {title}",
        "",
    ]
    
    if summary:
        lines.extend([
            "## Executive Summary",
            "",
            summary,
            "",
        ])
    
    for section in sections:
        heading = section.get("heading", "Section")
        content = section.get("content", "")
        data = section.get("data")
        
        lines.extend([
            f"## {heading}",
            "",
        ])
        
        if content:
            lines.append(content)
            lines.append("")
        
        if data:
            # Format data as table if it's a list of dicts
            if isinstance(data, list) and data and isinstance(data[0], dict):
                # Table header
                keys = list(data[0].keys())
                lines.append("| " + " | ".join(keys) + " |")
                lines.append("| " + " | ".join(["---"] * len(keys)) + " |")
                # Table rows
                for row in data:
                    values = [str(row.get(k, "")) for k in keys]
                    lines.append("| " + " | ".join(values) + " |")
                lines.append("")
            elif isinstance(data, dict):
                for k, v in data.items():
                    lines.append(f"- **{k}**: {v}")
                lines.append("")
    
    if sources:
        lines.extend([
            "## Sources",
            "",
        ])
        for i, source in enumerate(sources, 1):
            lines.append(f"{i}. {source}")
        lines.append("")
    
    lines.extend([
        "---",
        f"*Generated by Sentinel Agent on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*"
    ])
    
    report = "\n".join(lines)
    
    return {
        "format": format,
        "report": report,
        "sections_count": len(sections),
        "sources_count": len(sources)
    }
