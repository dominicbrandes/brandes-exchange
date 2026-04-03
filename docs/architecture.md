# Architecture

## Overview

Sentinel is built on a modular, extensible architecture inspired by modern AI agent frameworks. The system uses the ReAct (Reasoning + Acting) pattern for autonomous task execution.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER INPUT                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                             SENTINEL CORE                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                         ReAct Loop                               │    │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐   │    │
│  │  │  Think   │───▶│   Act    │───▶│ Observe  │───▶│ Repeat/  │   │    │
│  │  │ (Reason) │    │  (Tool)  │    │ (Result) │    │  Answer  │   │    │
│  │  └──────────┘    └──────────┘    └──────────┘    └──────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│                                    ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        Tool Registry                             │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │    │
│  │  │  Web   │ │  ETH   │ │  Math  │ │  Risk  │ │ Memory │        │    │
│  │  │ Search │ │  Call  │ │  Calc  │ │ Assess │ │ Store  │        │    │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│                                    ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                       Memory System                              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │    │
│  │  │  Short-Term  │  │  Long-Term   │  │   Episodic   │           │    │
│  │  │  (Context)   │  │   (Facts)    │  │  (Sessions)  │           │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              RESPONSE                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Agent Core (`agent/core.py`)

The main orchestrator implementing the ReAct loop:

```python
while iteration < max_iterations:
    # 1. Send to LLM with tools
    response = llm.generate(messages, tools)
    
    # 2. If tool calls requested, execute them
    if response.has_tool_calls:
        results = execute_tools(response.tool_calls)
        messages.append(results)
        continue
    
    # 3. Otherwise, return final answer
    return response.text
```

**Key Features:**
- Configurable iteration limits
- Automatic retry on tool failures
- Token usage tracking
- Verbose/debug modes

### 2. Tool System (`tools/`)

Modular tool architecture using decorators:

```python
@tool(
    name="web_search",
    description="Search the web for information",
    parameters={...}
)
def web_search(query: str) -> dict:
    ...
```

**Available Tools:**
| Tool | Purpose |
|------|---------|
| `web_search` | Search web for information |
| `fetch_url` | Retrieve webpage content |
| `eth_call` | Query Ethereum contracts |
| `get_token_price` | Get crypto prices |
| `calculate` | Math operations |
| `assess_risk` | Risk evaluation |
| `store_memory` | Save facts |
| `recall_memory` | Retrieve facts |
| `generate_report` | Create reports |

### 3. Memory System (`memory/`)

Three-tier memory architecture:

#### Short-Term Memory
- Sliding window of recent messages
- Extracted facts from conversation
- Keyword-based search

#### Long-Term Memory
- SQLite-backed persistence
- Tagged fact storage
- Source tracking
- Access counting

#### Episodic Memory
- Session summaries
- Key facts extraction
- Topic tagging
- Relevance-based retrieval

## Data Flow

### Query Processing

```
1. User Query
   │
   ├─► Check episodic memory for relevant past sessions
   │
   ├─► Check long-term memory for known facts
   │
   └─► Inject context into prompt

2. ReAct Loop
   │
   ├─► LLM reasons about query
   │
   ├─► LLM decides on tool use
   │
   ├─► Tools execute and return results
   │
   └─► Loop until answer ready

3. Response
   │
   ├─► Update short-term memory
   │
   ├─► Extract and store new facts
   │
   └─► Return formatted response
```

### Tool Execution

```
1. Tool Call Request
   ├── name: "web_search"
   └── arguments: {"query": "EigenLayer TVL"}

2. Registry Lookup
   └── Find tool by name

3. Execution
   ├── Validate arguments
   ├── Execute function
   └── Catch errors

4. Result
   ├── success: true/false
   ├── data: {...}
   └── error: (if failed)
```

## Extension Points

### Adding New Tools

```python
from tools.base import tool

@tool(
    name="my_tool",
    description="What it does",
    parameters={
        "type": "object",
        "properties": {
            "arg1": {"type": "string"}
        }
    }
)
def my_tool(arg1: str) -> dict:
    return {"result": "..."}
```

### Custom Memory Backends

Implement the `LongTermMemory` interface with your preferred storage:

```python
class RedisMemory(LongTermMemory):
    def store(self, key, value, source, tags): ...
    def recall(self, key): ...
    def search(self, query, tags, limit): ...
```

## Performance Considerations

### Token Efficiency
- Context pruning for long conversations
- Selective fact inclusion
- Summary-based episodic retrieval

### Latency
- Async tool execution where possible
- Connection pooling for HTTP
- Memory caching

### Reliability
- Tool retry logic
- Graceful degradation
- Error handling at all layers

## Security

### API Key Protection
- Environment variable storage
- Never logged or displayed
- Separate keys per environment

### Input Validation
- Pydantic schemas for all tools
- SQL injection prevention in memory
- URL validation for fetching

### Output Sanitization
- No arbitrary code execution
- Safe math evaluation
- Limited file system access
