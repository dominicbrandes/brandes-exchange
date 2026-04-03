"""
Sentinel Agent Configuration
"""

from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class Config:
    """Agent configuration with sensible defaults."""
    
    # LLM settings
    model: str = "claude-sonnet-4-20250514"
    api_key: Optional[str] = None
    temperature: float = 0
    max_tokens: int = 4096
    
    # Agent settings
    max_iterations: int = 10
    max_tool_retries: int = 3
    timeout_seconds: int = 30
    
    # Memory settings
    short_term_limit: int = 20  # messages
    long_term_persist: bool = True
    memory_path: str = ".sentinel/memory"
    
    # Tool settings
    enabled_tools: list[str] = field(default_factory=lambda: [
        "web_search",
        "fetch_url", 
        "eth_call",
        "get_token_price",
        "calculate",
        "assess_risk",
        "store_memory",
        "recall_memory",
        "generate_report",
    ])
    
    # Network settings
    ethereum_rpc_url: str = "https://eth.llamarpc.com"
    
    # Output settings
    verbose: bool = False
    show_reasoning: bool = True
    color_output: bool = True
    
    def __post_init__(self):
        """Load from environment if not provided."""
        if self.api_key is None:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if env_rpc := os.getenv("ETHEREUM_RPC_URL"):
            self.ethereum_rpc_url = env_rpc
        
        if env_model := os.getenv("SENTINEL_MODEL"):
            self.model = env_model


# Default configuration
DEFAULT_CONFIG = Config()


# System prompt for the agent
SYSTEM_PROMPT = """You are Sentinel, an autonomous AI agent specialized in DeFi research and analysis. You have access to tools for searching the web, querying blockchain data, performing calculations, and generating reports.

## Your Capabilities
- Research DeFi protocols, yields, risks, and mechanisms
- Query on-chain data from Ethereum and L2s
- Analyze smart contract interactions and token flows
- Assess risks: smart contract, economic, slashing, liquidity
- Generate structured reports with citations
- Remember facts across conversations

## How You Work
You use a Thought → Action → Observation loop:
1. THOUGHT: Reason about what you need to do next
2. ACTION: Call a tool with specific parameters
3. OBSERVATION: Analyze the tool's output
4. Repeat until you have enough information
5. FINAL ANSWER: Synthesize a comprehensive response

## Guidelines
- Always cite your sources with URLs when possible
- Be precise with numbers and calculations
- Acknowledge uncertainty when data is incomplete
- Break complex queries into smaller steps
- Use memory to avoid redundant searches
- Provide actionable insights, not just data

## Output Format
For complex analyses, structure your response with:
- Executive summary (1-2 sentences)
- Key findings (bullet points)
- Detailed analysis (with sections)
- Risk considerations
- Sources

You are helpful, accurate, and thorough. Begin!"""
