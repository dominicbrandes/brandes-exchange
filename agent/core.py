"""
Sentinel Agent Core

The main agent class implementing the ReAct reasoning loop.
"""

import asyncio
import json
import re
from typing import Optional, AsyncIterator
from dataclasses import dataclass, field

import anthropic

from .config import Config, DEFAULT_CONFIG, SYSTEM_PROMPT
from tools import registry, ToolResult


@dataclass
class Message:
    """A message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)


@dataclass 
class AgentState:
    """Current state of the agent."""
    messages: list[Message] = field(default_factory=list)
    iteration: int = 0
    total_tokens: int = 0
    tool_calls_made: int = 0


class Sentinel:
    """
    Autonomous DeFi research agent.
    
    Uses ReAct (Reasoning + Acting) pattern to decompose queries,
    gather information via tools, and synthesize responses.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the agent."""
        self.config = config or DEFAULT_CONFIG
        
        if not self.config.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY env var or pass in config."
            )
        
        self.client = anthropic.Anthropic(api_key=self.config.api_key)
        self.state = AgentState()
        
        # Colors for output
        self.colors = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "dim": "\033[2m",
            "blue": "\033[94m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "red": "\033[91m",
            "cyan": "\033[96m",
        } if self.config.color_output else {k: "" for k in ["reset", "bold", "dim", "blue", "green", "yellow", "red", "cyan"]}
    
    def _print(self, msg: str, color: str = "reset", prefix: str = "") -> None:
        """Print with optional color."""
        if self.config.verbose or self.config.show_reasoning:
            c = self.colors.get(color, "")
            r = self.colors["reset"]
            print(f"{c}{prefix}{msg}{r}")
    
    def _get_tools(self) -> list[dict]:
        """Get tool definitions for the API."""
        return registry.to_anthropic_tools()
    
    async def _execute_tool(self, name: str, arguments: dict) -> ToolResult:
        """Execute a tool and return the result."""
        self._print(f"Calling {name}({json.dumps(arguments, default=str)[:100]}...)", "cyan", "🔧 ")
        result = await registry.execute(name, **arguments)
        return result
    
    async def _run_loop(self, query: str) -> str:
        """
        Main agent loop using ReAct pattern.
        
        1. Send query to LLM with tool definitions
        2. If LLM wants to use tools, execute them
        3. Send tool results back to LLM
        4. Repeat until LLM provides final answer
        """
        messages = [{"role": "user", "content": query}]
        
        self.state = AgentState()
        
        while self.state.iteration < self.config.max_iterations:
            self.state.iteration += 1
            
            if self.config.verbose:
                self._print(f"Iteration {self.state.iteration}/{self.config.max_iterations}", "dim", "")
            
            # Call LLM
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=SYSTEM_PROMPT,
                tools=self._get_tools(),
                messages=messages,
            )
            
            self.state.total_tokens += response.usage.input_tokens + response.usage.output_tokens
            
            # Process response
            assistant_content = []
            tool_calls = []
            final_text = ""
            
            for block in response.content:
                if block.type == "text":
                    final_text += block.text
                    assistant_content.append({"type": "text", "text": block.text})
                    
                    # Show reasoning if enabled
                    if self.config.show_reasoning and block.text.strip():
                        self._print(block.text[:200] + "..." if len(block.text) > 200 else block.text, "dim", "💭 ")
                        
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
            
            messages.append({"role": "assistant", "content": assistant_content})
            
            # If no tool calls, we're done
            if not tool_calls:
                return final_text
            
            # Execute tools
            tool_results = []
            for tc in tool_calls:
                self.state.tool_calls_made += 1
                result = await self._execute_tool(tc["name"], tc["input"])
                
                # Show result preview
                result_preview = result.to_observation()[:200]
                if len(result.to_observation()) > 200:
                    result_preview += "..."
                self._print(result_preview, "green" if result.success else "red", "   → ")
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc["id"],
                    "content": result.to_observation()
                })
            
            messages.append({"role": "user", "content": tool_results})
        
        # Max iterations reached
        return f"⚠️ Reached maximum iterations ({self.config.max_iterations}). Partial response:\n\n{final_text}"
    
    def run(self, query: str) -> str:
        """
        Run the agent synchronously.
        
        Args:
            query: The user's question or request
            
        Returns:
            The agent's response
        """
        return asyncio.run(self._run_loop(query))
    
    async def arun(self, query: str) -> str:
        """
        Run the agent asynchronously.
        
        Args:
            query: The user's question or request
            
        Returns:
            The agent's response
        """
        return await self._run_loop(query)
    
    def reset(self) -> None:
        """Reset agent state."""
        self.state = AgentState()
    
    def get_stats(self) -> dict:
        """Get agent statistics."""
        return {
            "iterations": self.state.iteration,
            "tool_calls": self.state.tool_calls_made,
            "total_tokens": self.state.total_tokens,
        }


def create_agent(
    model: str = "claude-sonnet-4-20250514",
    verbose: bool = False,
    **kwargs
) -> Sentinel:
    """
    Create a Sentinel agent with the specified configuration.
    
    Args:
        model: Model to use
        verbose: Show detailed output
        **kwargs: Additional config options
        
    Returns:
        Configured Sentinel agent
    """
    config = Config(model=model, verbose=verbose, **kwargs)
    return Sentinel(config)
