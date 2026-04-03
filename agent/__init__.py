"""
Sentinel: Autonomous DeFi Research Agent

A production-grade AI agent for researching DeFi protocols, analyzing on-chain data,
assessing risks, and generating insights.

Example:
    from agent import Sentinel
    
    agent = Sentinel()
    response = agent.run("What is EigenLayer's TVL and how does restaking work?")
    print(response)
"""

from .config import Config, DEFAULT_CONFIG
from .core import Sentinel, create_agent

__version__ = "1.0.0"
__author__ = "Dominic Brandes"

__all__ = [
    "Sentinel",
    "Config",
    "create_agent",
    "DEFAULT_CONFIG",
]
