# Brandes Exchange

A complete cryptocurrency trading infrastructure: high-performance C++ matching engine, REST API, real-time trading UI, and an autonomous AI research agent for DeFi analytics.

![C++](https://img.shields.io/badge/C++-17-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10+-green.svg)
![React](https://img.shields.io/badge/React-18-61DAFB.svg)
![Claude](https://img.shields.io/badge/AI-Claude-orange.svg)
![Tests](https://img.shields.io/badge/Tests-73%20passing-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

<p align="center">
  <img src="docs/assets/architecture.png" alt="Brandes Exchange Architecture" width="800"/>
</p>

## Performance

| Component | Metric | Value |
|-----------|--------|-------|
| **Matching Engine** | Throughput | **312 orders/sec** |
| | p50 Latency | **2.4ms** |
| | p95 Latency | **4.8ms** |
| **AI Agent** | Tools | **9 custom tools** |
| | Memory Tiers | **3-tier architecture** |
| | Reasoning | **ReAct pattern** |
| **Test Coverage** | Engine | 31 tests (100% matching logic) |
| | Agent | 42 tests |
| | **Total** | **73 tests** |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BRANDES EXCHANGE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐  │
│  │   React UI  │◄──►│   FastAPI       │◄──►│   C++ Matching Engine       │  │
│  │  (Charts,   │    │   REST API      │    │   • Price-Time Priority     │  │
│  │  Order Book,│    │   • /orders     │    │   • Event Sourcing          │  │
│  │  Trading)   │    │   • /book       │    │   • 312 orders/sec          │  │
│  └─────────────┘    │   • /trades     │    │   • 2.4ms p50 latency       │  │
│                     └────────┬────────┘    └─────────────────────────────┘  │
│                              │                                               │
│                              ▼                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        AI RESEARCH AGENT                               │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐    │  │
│  │  │   Planner   │───▶│  Executor   │───▶│  9 Custom Tools          │    │  │
│  │  │   (ReAct)   │    │  (Tools)    │    │  • exchange_query        │    │  │
│  │  └─────────────┘    └─────────────┘    │  • web_search            │    │  │
│  │         │                              │  • eth_call              │    │  │
│  │         ▼                              │  • risk_assess           │    │  │
│  │  ┌─────────────────────────────────┐   │  • calculate             │    │  │
│  │  │  3-Tier Memory                  │   └─────────────────────────┘    │  │
│  │  │  Short-Term │ Long-Term │ Episodic                                 │  │
│  │  └─────────────────────────────────┘                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Features

### Matching Engine (C++)
- **Price-time priority** order matching
- **Event sourcing** with deterministic state replay
- **Snapshot recovery** for fast restarts
- **Self-trade prevention**
- **Partial fills** across multiple orders

### Trading API (Python/FastAPI)
- RESTful endpoints for orders, book, trades
- Real-time balance tracking
- Prometheus metrics
- Admin controls (reset, snapshots)

### Trading UI (React)
- Real-time order book visualization
- Canvas-rendered price charts
- Account management
- Order placement with validation

### AI Research Agent (Python/Claude)
- **ReAct reasoning loop** — thinks, acts, observes, repeats
- **9 custom tools** — web search, Ethereum queries, risk assessment, exchange integration
- **3-tier memory** — short-term context, persistent facts (SQLite), session history
- **Exchange integration** — can query order book, analyze trades, assess market conditions

## Quick Start

### Prerequisites
- C++17 compiler (GCC 9+ or Clang 10+)
- Python 3.10+
- Node.js 18+
- Anthropic API key (for AI agent)

### Installation

```bash
# Clone
git clone https://github.com/dominicbrandes/brandes-exchange.git
cd brandes-exchange

# Build C++ engine
make build

# Install Python dependencies
pip install -r requirements.txt

# Install UI dependencies
cd ui && npm install && cd ..

# Set API key for AI agent
export ANTHROPIC_API_KEY="your-key"
```

### Run Everything

```bash
# Terminal 1: Start API server
make api

# Terminal 2: Start UI
make ui

# Terminal 3: Run AI agent
make agent QUERY="Analyze the current order book and suggest optimal entry points"
```

## Usage

### Trading

```bash
# Start the exchange
make run

# Open http://localhost:5173
# Place orders, watch the book update in real-time
```

### AI Agent

```bash
# Single query
python -m agent "What is EigenLayer's TVL and what are the slashing risks?"

# Interactive mode
python -m agent --interactive

# Query your own exchange
python -m agent "Analyze my exchange's current order book depth"
```

### Agent + Exchange Integration

```python
from agent import Sentinel

agent = Sentinel()

# The agent can query your running exchange
response = agent.run("""
    Look at my exchange's order book:
    1. What's the current spread?
    2. Where are the support/resistance levels?
    3. Is there enough liquidity for a 10 BTC market buy?
""")
```

## Project Structure

```
brandes-exchange/
├── engine/                    # C++ Matching Engine
│   ├── include/              # Headers
│   │   ├── order_book.hpp
│   │   ├── matching_engine.hpp
│   │   └── event_store.hpp
│   ├── src/                  # Implementation
│   │   ├── order_book.cpp
│   │   ├── matching_engine.cpp
│   │   └── main.cpp
│   └── tests/                # 31 unit tests
│       └── test_matching.cpp
├── api/                       # FastAPI Server
│   └── main.py
├── ui/                        # React Trading UI
│   └── src/
│       └── App.tsx
├── agent/                     # AI Research Agent
│   ├── core.py               # ReAct loop
│   ├── config.py             # Configuration
│   └── __main__.py           # CLI
├── tools/                     # Agent Tools (9 total)
│   ├── web.py                # web_search, fetch_url
│   ├── blockchain.py         # eth_call, get_token_price
│   ├── math.py               # calculate, calculate_apy
│   ├── risk.py               # assess_risk, compare_risks
│   ├── memory.py             # store/recall_memory
│   └── exchange.py           # exchange_query (NEW!)
├── memory/                    # 3-Tier Memory System
│   ├── short_term.py         # Conversation context
│   ├── long_term.py          # SQLite facts DB
│   └── episodic.py           # Session summaries
├── tests/                     # 73 total tests
│   ├── test_matching.cpp
│   └── test_agent.py
├── docs/
│   ├── architecture.md
│   ├── latency-report.md
│   └── tools.md
└── scripts/
    ├── demo.sh
    └── benchmark.sh
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/book/{symbol}` | Order book snapshot |
| GET | `/api/v1/trades/{symbol}` | Recent trades |
| POST | `/api/v1/orders` | Place order |
| DELETE | `/api/v1/orders/{id}` | Cancel order |
| GET | `/api/v1/accounts/{id}/balances` | Account balances |
| GET | `/metrics` | Prometheus metrics |

## Agent Tools

| Tool | Description |
|------|-------------|
| `web_search` | Search web for DeFi info |
| `fetch_url` | Retrieve webpage content |
| `eth_call` | Query Ethereum contracts |
| `get_token_price` | Get crypto prices |
| `calculate` | Math operations |
| `assess_risk` | Protocol risk scoring |
| `store_memory` | Save facts to DB |
| `recall_memory` | Retrieve stored facts |
| `exchange_query` | Query local exchange state |

## Testing

```bash
# Run all tests
make test

# C++ tests only
make test-engine

# Python tests only
make test-agent

# With coverage
make coverage
```

## Design Decisions

### Why C++ for the Engine?
- Predictable latency (no GC pauses)
- Cache-friendly memory layout
- Industry standard for trading systems

### Why Single-Threaded?
- Deterministic execution
- No lock contention
- Easier debugging and replay

### Why Event Sourcing?
- Complete audit trail
- Disaster recovery via replay
- Regulatory compliance

### Why ReAct for the Agent?
- Transparent reasoning
- Tool use is explicit
- Easy to debug and extend

## Roadmap

- [x] Core matching engine
- [x] REST API
- [x] Trading UI
- [x] AI research agent
- [x] Agent-Exchange integration
- [ ] WebSocket streaming
- [ ] Multi-symbol support
- [ ] FIX protocol
- [ ] Distributed deployment

## License

MIT License — see [LICENSE](LICENSE)

## Author

**Dominic Brandes**  
B.S. Computer Engineering, San Diego State University  
[LinkedIn](https://linkedin.com/in/dominic-r-brandes) • [GitHub](https://github.com/dominicbrandes)

---

*Matching engine built for performance. AI agent built for insight.*
