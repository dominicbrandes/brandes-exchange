# Tools Reference

Complete reference for all Sentinel agent tools.

## Web Tools

### `web_search`

Search the web for information.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `num_results` | integer | No | Results to return (1-10, default 5) |

**Returns:**
```json
{
  "query": "EigenLayer TVL",
  "num_results": 3,
  "results": [
    {
      "title": "EigenLayer - Restaking Protocol",
      "url": "https://eigenlayer.xyz",
      "snippet": "EigenLayer enables restaking..."
    }
  ]
}
```

**Example:**
```
Searching for "EigenLayer restaking tutorial"...
```

---

### `fetch_url`

Fetch content from a URL.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `url` | string | Yes | URL to fetch |
| `extract_json` | boolean | No | Parse as JSON (default false) |

**Returns:**
```json
{
  "url": "https://example.com",
  "type": "text",
  "content": "Page content...",
  "length": 4523
}
```

---

## Blockchain Tools

### `eth_call`

Query Ethereum smart contract state.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contract` | string | Yes | Address or known name |
| `method` | string | Yes | Method to call |
| `args` | array | No | Method arguments |
| `block` | string | No | Block number or "latest" |

**Known Contracts:**
- `eigenlayer_strategy_manager`
- `eigenlayer_delegation_manager`
- `lido_steth`
- `weth`
- `usdc`

**Returns:**
```json
{
  "contract": "0x...",
  "method": "totalSupply",
  "result": "4823000000000000000000000",
  "decoded": {
    "value": 4823000,
    "unit": "ETH"
  }
}
```

---

### `get_token_price`

Get current token price in USD.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `token` | string | Yes | Token symbol (ETH, BTC, etc) |
| `include_metadata` | boolean | No | Include market cap, volume |

**Supported Tokens:**
- ETH, BTC, STETH, EIGEN, USDC, USDT

**Returns:**
```json
{
  "token": "ETH",
  "price_usd": 3170.42,
  "change_24h_percent": 2.3,
  "market_cap": 381000000000,
  "volume_24h": 12500000000
}
```

---

### `get_gas_price`

Get current Ethereum gas prices.

**Parameters:** None

**Returns:**
```json
{
  "base_fee_gwei": 12.5,
  "priority_fee_gwei": 1.5,
  "total_gwei": 14.0,
  "estimates": {
    "transfer_eth": {"gas": 21000, "cost_usd": 0.94},
    "uniswap_swap": {"gas": 150000, "cost_usd": 6.71}
  }
}
```

---

## Math Tools

### `calculate`

Perform mathematical calculations.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `expression` | string | Yes | Math expression |
| `precision` | integer | No | Decimal places (default 4) |

**Supported Operations:**
- Basic: `+`, `-`, `*`, `/`
- Powers: `**`
- Functions: `sqrt`, `log`, `exp`
- Constants: `pi`, `e`

**Returns:**
```json
{
  "expression": "15.3 * 1e9 / 3170",
  "result": 4826498.42,
  "formatted": "4.83M"
}
```

---

### `calculate_apy`

Convert between APR and APY.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `rate` | number | Yes | Interest rate (percentage) |
| `from_type` | string | Yes | "apr" or "apy" |
| `compounds_per_year` | integer | No | Compounding periods (default 365) |

**Returns:**
```json
{
  "input_apr": 5.0,
  "output_apy": 5.127,
  "compounds_per_year": 365
}
```

---

### `calculate_impermanent_loss`

Calculate IL for liquidity positions.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `price_change_percent` | number | Yes | Price change (%) |
| `initial_value` | number | No | Initial position value |

**Returns:**
```json
{
  "price_change_percent": 100,
  "impermanent_loss_percent": -5.72,
  "lp_value_now": 14142.13,
  "hold_value_now": 15000.00
}
```

---

## Risk Tools

### `assess_risk`

Comprehensive protocol risk assessment.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `protocol` | string | Yes | Protocol name |
| `risk_types` | array | No | Types to assess |
| `context` | string | No | Additional context |

**Risk Types:**
- `smart_contract`
- `economic`
- `slashing`
- `liquidity`
- `centralization`
- `all` (default)

**Returns:**
```json
{
  "protocol": "EigenLayer",
  "overall_score": 4.3,
  "overall_level": "medium",
  "risks": [
    {
      "type": "smart_contract",
      "score": 3.5,
      "level": "medium",
      "description": "...",
      "mitigations": ["..."]
    }
  ],
  "recommendations": ["..."]
}
```

---

### `compare_risks`

Compare risks across protocols.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `protocols` | array | Yes | Protocols to compare |
| `risk_type` | string | No | Specific type or "overall" |

**Returns:**
```json
{
  "risk_type": "overall",
  "comparison": [
    {"protocol": "Lido", "score": 3.0, "level": "low"},
    {"protocol": "EigenLayer", "score": 4.3, "level": "medium"}
  ],
  "safest": "Lido",
  "riskiest": "EigenLayer"
}
```

---

## Memory Tools

### `store_memory`

Store information for later recall.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `key` | string | Yes | Unique identifier |
| `value` | object | Yes | Data to store |
| `source` | string | No | Information source |
| `ttl_hours` | integer | No | Time to live (0=permanent) |

---

### `recall_memory`

Retrieve stored information.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `key` | string | No | Specific key to recall |
| `key_pattern` | string | No | Pattern to match (e.g., "eigen*") |

---

### `generate_report`

Generate formatted reports.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `title` | string | Yes | Report title |
| `sections` | array | Yes | Report sections |
| `summary` | string | No | Executive summary |
| `sources` | array | No | Source URLs |
| `format` | string | No | "markdown" or "json" |

**Section Format:**
```json
{
  "heading": "Section Title",
  "content": "Text content",
  "data": {"key": "value"}
}
```
