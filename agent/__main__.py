"""
Sentinel Agent CLI

Usage:
    python -m agent "Your question here"
    python -m agent --interactive
"""

import sys
import argparse
import os
from typing import Optional

from .core import Sentinel, create_agent
from .config import Config


def print_banner():
    """Print welcome banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗ ║
║   ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║ ║
║   ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║ ║
║   ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║ ║
║   ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
║   ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
║                                                               ║
║   Autonomous DeFi Research Agent                  v1.0.0      ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def run_interactive(agent: Sentinel):
    """Run in interactive mode."""
    print_banner()
    print("\nType 'exit' to quit, 'clear' to reset memory, 'stats' to see usage\n")
    
    while True:
        try:
            query = input("\033[94mYou:\033[0m ").strip()
            
            if not query:
                continue
            
            if query.lower() == "exit":
                print("\nGoodbye! 👋\n")
                break
            
            if query.lower() == "clear":
                agent.reset()
                print("Memory cleared.\n")
                continue
            
            if query.lower() == "stats":
                stats = agent.get_stats()
                print(f"\nStats: {stats}\n")
                continue
            
            print()
            response = agent.run(query)
            print(f"\n\033[92mSentinel:\033[0m\n{response}\n")
            print("─" * 60 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit' to quit.\n")
        except Exception as e:
            print(f"\n\033[91mError:\033[0m {e}\n")


def run_single(agent: Sentinel, query: str):
    """Run a single query."""
    print("\n" + "━" * 70)
    response = agent.run(query)
    print("\n" + "━" * 70)
    print(f"\n{response}\n")
    print("━" * 70 + "\n")
    
    stats = agent.get_stats()
    print(f"\033[2mStats: {stats['iterations']} iterations, {stats['tool_calls']} tool calls, {stats['total_tokens']} tokens\033[0m\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sentinel - Autonomous DeFi Research Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m agent "What is EigenLayer's current TVL?"
  python -m agent "Compare risks of Lido vs EigenLayer"
  python -m agent --interactive
  python -m agent --verbose "Analyze restaking strategies"
        """
    )
    
    parser.add_argument(
        "query",
        nargs="?",
        help="Query to run (omit for interactive mode)"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output including reasoning"
    )
    parser.add_argument(
        "-m", "--model",
        default="claude-sonnet-4-20250514",
        help="Model to use (default: claude-sonnet-4-20250514)"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum reasoning iterations (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n\033[91mError:\033[0m ANTHROPIC_API_KEY environment variable not set.")
        print("\nSet it with:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("\nGet your API key at: https://console.anthropic.com/\n")
        sys.exit(1)
    
    # Create agent
    config = Config(
        model=args.model,
        verbose=args.verbose,
        show_reasoning=args.verbose,
        color_output=not args.no_color,
        max_iterations=args.max_iterations,
    )
    
    try:
        agent = Sentinel(config)
    except Exception as e:
        print(f"\n\033[91mError creating agent:\033[0m {e}\n")
        sys.exit(1)
    
    # Run
    if args.interactive or not args.query:
        run_interactive(agent)
    else:
        run_single(agent, args.query)


if __name__ == "__main__":
    main()
