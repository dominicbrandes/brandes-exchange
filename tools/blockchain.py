"""
Blockchain tools for querying on-chain data.
"""

import json
from typing import Optional
import httpx

from .base import tool


# Common contract addresses
KNOWN_CONTRACTS = {
    "eigenlayer_strategy_manager": "0x858646372CC42E1A627fcE94aa7A7033e7CF075A",
    "eigenlayer_delegation_manager": "0x39053D51B77DC0d36036Fc1fCc8Cb819df8Ef37A",
    "eigenlayer_avs_directory": "0x135DDa560e946695d6f155dACaFC6f1F25C1F5AF",
    "lido_steth": "0xae7ab96520DE3A18E5e111B5EaijbBe020F29C785",
    "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "eigen_token": "0xec53bF9167f50cDEB3Ae105f56099aaaB9061F83",
}

# ABI fragments for common calls
COMMON_ABIS = {
    "balanceOf": "function balanceOf(address) view returns (uint256)",
    "totalSupply": "function totalSupply() view returns (uint256)",
    "decimals": "function decimals() view returns (uint8)",
    "symbol": "function symbol() view returns (string)",
    "name": "function name() view returns (string)",
}


@tool(
    name="eth_call",
    description="Make a read-only call to an Ethereum smart contract. Can query balances, state variables, and other on-chain data.",
    parameters={
        "type": "object",
        "properties": {
            "contract": {
                "type": "string",
                "description": "Contract address (0x...) or known name (eigenlayer_strategy_manager, lido_steth, etc.)"
            },
            "method": {
                "type": "string",
                "description": "Method to call (e.g., 'balanceOf', 'totalSupply', 'getOperatorShares')"
            },
            "args": {
                "type": "array",
                "description": "Arguments for the method call",
                "items": {"type": "string"},
                "default": []
            },
            "block": {
                "type": "string",
                "description": "Block number or 'latest'",
                "default": "latest"
            }
        },
        "required": ["contract", "method"]
    }
)
def eth_call(
    contract: str,
    method: str,
    args: Optional[list] = None,
    block: str = "latest"
) -> dict:
    """
    Query Ethereum contract state.
    """
    args = args or []
    
    # Resolve contract name to address
    if not contract.startswith("0x"):
        contract = KNOWN_CONTRACTS.get(contract.lower(), contract)
    
    # For demo purposes, return mock data for known contracts/methods
    return _get_mock_eth_data(contract, method, args)


def _get_mock_eth_data(contract: str, method: str, args: list) -> dict:
    """Return mock data for common queries."""
    
    # EigenLayer Strategy Manager
    if contract.lower() == KNOWN_CONTRACTS["eigenlayer_strategy_manager"].lower():
        if method == "totalSupply" or method == "getTotalStaked":
            return {
                "contract": contract,
                "method": method,
                "result": "4823000000000000000000000",  # 4.823M ETH in wei
                "decoded": {
                    "value": 4823000,
                    "unit": "ETH",
                    "usd_value": 15300000000  # ~$15.3B at $3,170/ETH
                }
            }
    
    # Lido stETH
    if "ae7ab96520" in contract.lower():
        if method == "totalSupply":
            return {
                "contract": contract,
                "method": method,
                "result": "9200000000000000000000000",
                "decoded": {
                    "value": 9200000,
                    "unit": "stETH",
                    "usd_value": 28400000000
                }
            }
    
    # Generic balance query
    if method == "balanceOf":
        return {
            "contract": contract,
            "method": method,
            "args": args,
            "result": "1000000000000000000",
            "decoded": {
                "value": 1.0,
                "unit": "tokens"
            }
        }
    
    # Generic total supply
    if method == "totalSupply":
        return {
            "contract": contract,
            "method": method,
            "result": "1000000000000000000000000",
            "decoded": {
                "value": 1000000,
                "unit": "tokens"
            }
        }
    
    return {
        "contract": contract,
        "method": method,
        "args": args,
        "result": None,
        "note": "Method not found in mock data. Use web_search for more info."
    }


@tool(
    name="get_token_price",
    description="Get current price of a token in USD. Supports ETH, BTC, stETH, EIGEN, and other major tokens.",
    parameters={
        "type": "object",
        "properties": {
            "token": {
                "type": "string",
                "description": "Token symbol (ETH, BTC, EIGEN, stETH, etc.) or contract address"
            },
            "include_metadata": {
                "type": "boolean",
                "description": "Include market cap, volume, and other metadata",
                "default": False
            }
        },
        "required": ["token"]
    }
)
def get_token_price(token: str, include_metadata: bool = False) -> dict:
    """
    Get current token price.
    """
    token_upper = token.upper()
    
    # Mock price data
    prices = {
        "ETH": {
            "price": 3170.42,
            "change_24h": 2.3,
            "market_cap": 381000000000,
            "volume_24h": 12500000000,
        },
        "BTC": {
            "price": 67234.18,
            "change_24h": 1.8,
            "market_cap": 1320000000000,
            "volume_24h": 28900000000,
        },
        "STETH": {
            "price": 3165.80,
            "change_24h": 2.2,
            "market_cap": 29100000000,
            "volume_24h": 45000000,
        },
        "EIGEN": {
            "price": 3.82,
            "change_24h": -1.2,
            "market_cap": 642000000,
            "volume_24h": 89000000,
            "fdv": 6400000000,
        },
        "USDC": {
            "price": 1.00,
            "change_24h": 0.0,
            "market_cap": 33000000000,
            "volume_24h": 5200000000,
        },
        "USDT": {
            "price": 1.00,
            "change_24h": 0.0,
            "market_cap": 112000000000,
            "volume_24h": 45000000000,
        },
    }
    
    if token_upper in prices:
        data = prices[token_upper]
        result = {
            "token": token_upper,
            "price_usd": data["price"],
            "change_24h_percent": data["change_24h"],
        }
        if include_metadata:
            result["market_cap"] = data.get("market_cap")
            result["volume_24h"] = data.get("volume_24h")
            result["fdv"] = data.get("fdv")
        return result
    
    return {
        "token": token,
        "error": "Token not found. Try using the token symbol (ETH, BTC, etc.)"
    }


@tool(
    name="get_gas_price",
    description="Get current Ethereum gas prices (base fee, priority fee, estimated costs).",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def get_gas_price() -> dict:
    """
    Get current gas prices.
    """
    # Mock gas data
    return {
        "base_fee_gwei": 12.5,
        "priority_fee_gwei": 1.5,
        "total_gwei": 14.0,
        "estimates": {
            "transfer_eth": {"gas": 21000, "cost_usd": 0.94},
            "erc20_transfer": {"gas": 65000, "cost_usd": 2.91},
            "uniswap_swap": {"gas": 150000, "cost_usd": 6.71},
            "contract_deploy": {"gas": 1000000, "cost_usd": 44.73},
        },
        "network": "ethereum",
        "block": "latest"
    }
