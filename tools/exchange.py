"""
Exchange integration tools.

Connects the AI agent to the Brandes Exchange matching engine.
This is the key integration between the two systems.
"""

import httpx
from typing import Optional

from .base import tool


# Exchange API configuration
EXCHANGE_API_URL = "http://127.0.0.1:8000/api/v1"
SCALE = 1e8


@tool(
    name="exchange_query",
    description="Query the Brandes Exchange for real-time order book, trades, balances, and market data. Use this to analyze your own exchange's state.",
    parameters={
        "type": "object",
        "properties": {
            "query_type": {
                "type": "string",
                "enum": ["book", "trades", "balance", "spread", "depth", "stats"],
                "description": "Type of data to query"
            },
            "symbol": {
                "type": "string",
                "description": "Trading pair (e.g., 'BTC-USD')",
                "default": "BTC-USD"
            },
            "account_id": {
                "type": "string",
                "description": "Account ID for balance queries",
                "default": "Alice"
            },
            "depth": {
                "type": "integer",
                "description": "Number of price levels for book/depth queries",
                "default": 10
            }
        },
        "required": ["query_type"]
    }
)
def exchange_query(
    query_type: str,
    symbol: str = "BTC-USD",
    account_id: str = "Alice",
    depth: int = 10
) -> dict:
    """
    Query the local Brandes Exchange.
    
    Provides real-time access to:
    - Order book state
    - Recent trades
    - Account balances
    - Market statistics
    """
    try:
        with httpx.Client(timeout=5) as client:
            
            if query_type == "book":
                resp = client.get(f"{EXCHANGE_API_URL}/book/{symbol}")
                data = resp.json()
                
                bids = data.get("bids", [])[:depth]
                asks = data.get("asks", [])[:depth]
                
                return {
                    "query": "order_book",
                    "symbol": symbol,
                    "bids": [
                        {"price": b["price"] / SCALE, "quantity": b["quantity"] / SCALE}
                        for b in bids
                    ],
                    "asks": [
                        {"price": a["price"] / SCALE, "quantity": a["quantity"] / SCALE}
                        for a in asks
                    ],
                    "bid_levels": len(bids),
                    "ask_levels": len(asks),
                    "best_bid": bids[0]["price"] / SCALE if bids else None,
                    "best_ask": asks[0]["price"] / SCALE if asks else None,
                }
            
            elif query_type == "trades":
                resp = client.get(f"{EXCHANGE_API_URL}/trades/{symbol}")
                data = resp.json()
                trades = data.get("trades", [])[:20]
                
                return {
                    "query": "recent_trades",
                    "symbol": symbol,
                    "count": len(trades),
                    "trades": [
                        {
                            "price": t["price"] / SCALE,
                            "quantity": t["quantity"] / SCALE,
                            "value_usd": (t["price"] * t["quantity"]) / (SCALE * SCALE),
                            "buyer": t.get("buyer_account_id"),
                            "seller": t.get("seller_account_id"),
                        }
                        for t in trades
                    ],
                    "total_volume": sum(t["quantity"] for t in trades) / SCALE,
                }
            
            elif query_type == "balance":
                resp = client.get(f"{EXCHANGE_API_URL}/accounts/{account_id}/balances")
                data = resp.json()
                
                return {
                    "query": "account_balance",
                    "account_id": account_id,
                    "usd_available": data.get("usd", 0) / SCALE,
                    "usd_reserved": data.get("usd_reserved", 0) / SCALE,
                    "btc_available": data.get("btc", 0) / SCALE,
                    "btc_reserved": data.get("btc_reserved", 0) / SCALE,
                    "total_usd": (data.get("usd", 0) + data.get("usd_reserved", 0)) / SCALE,
                    "total_btc": (data.get("btc", 0) + data.get("btc_reserved", 0)) / SCALE,
                }
            
            elif query_type == "spread":
                resp = client.get(f"{EXCHANGE_API_URL}/book/{symbol}")
                data = resp.json()
                
                bids = data.get("bids", [])
                asks = data.get("asks", [])
                
                best_bid = bids[0]["price"] / SCALE if bids else None
                best_ask = asks[0]["price"] / SCALE if asks else None
                
                if best_bid and best_ask:
                    spread = best_ask - best_bid
                    spread_pct = (spread / best_ask) * 100
                    mid_price = (best_bid + best_ask) / 2
                else:
                    spread = None
                    spread_pct = None
                    mid_price = None
                
                return {
                    "query": "spread_analysis",
                    "symbol": symbol,
                    "best_bid": best_bid,
                    "best_ask": best_ask,
                    "spread_usd": spread,
                    "spread_percent": round(spread_pct, 4) if spread_pct else None,
                    "mid_price": mid_price,
                }
            
            elif query_type == "depth":
                resp = client.get(f"{EXCHANGE_API_URL}/book/{symbol}")
                data = resp.json()
                
                bids = data.get("bids", [])[:depth]
                asks = data.get("asks", [])[:depth]
                
                bid_depth = sum(b["quantity"] for b in bids) / SCALE
                ask_depth = sum(a["quantity"] for a in asks) / SCALE
                bid_value = sum(b["price"] * b["quantity"] for b in bids) / (SCALE * SCALE)
                ask_value = sum(a["price"] * a["quantity"] for a in asks) / (SCALE * SCALE)
                
                return {
                    "query": "market_depth",
                    "symbol": symbol,
                    "bid_depth_btc": bid_depth,
                    "ask_depth_btc": ask_depth,
                    "bid_value_usd": bid_value,
                    "ask_value_usd": ask_value,
                    "imbalance": round((bid_depth - ask_depth) / max(bid_depth + ask_depth, 0.001), 4),
                    "levels_analyzed": depth,
                }
            
            elif query_type == "stats":
                resp = client.get(f"{EXCHANGE_API_URL}/stats")
                data = resp.json()
                
                return {
                    "query": "exchange_stats",
                    "total_orders": data.get("total_orders", 0),
                    "total_trades": data.get("total_trades", 0),
                    "sequence": data.get("sequence", 0),
                    "status": "operational",
                }
            
            else:
                return {"error": f"Unknown query type: {query_type}"}
                
    except httpx.ConnectError:
        return {
            "error": "Exchange not running",
            "hint": "Start the exchange with: make api",
            "query_type": query_type
        }
    except Exception as e:
        return {
            "error": f"Query failed: {str(e)}",
            "query_type": query_type
        }


@tool(
    name="exchange_place_order",
    description="Place an order on the Brandes Exchange. Use with caution - this executes real trades on your exchange.",
    parameters={
        "type": "object",
        "properties": {
            "account_id": {
                "type": "string",
                "description": "Account placing the order"
            },
            "side": {
                "type": "string",
                "enum": ["BUY", "SELL"],
                "description": "Order side"
            },
            "price": {
                "type": "number",
                "description": "Limit price in USD"
            },
            "quantity": {
                "type": "number",
                "description": "Quantity in BTC"
            },
            "symbol": {
                "type": "string",
                "default": "BTC-USD"
            }
        },
        "required": ["account_id", "side", "price", "quantity"]
    }
)
def exchange_place_order(
    account_id: str,
    side: str,
    price: float,
    quantity: float,
    symbol: str = "BTC-USD"
) -> dict:
    """
    Place an order on the exchange.
    """
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.post(
                f"{EXCHANGE_API_URL}/orders",
                json={
                    "account_id": account_id,
                    "symbol": symbol,
                    "side": side,
                    "type": "LIMIT",
                    "price": int(price * SCALE),
                    "quantity": int(quantity * SCALE),
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                order = data.get("order", {})
                trades = data.get("trades", [])
                
                return {
                    "success": True,
                    "order_id": order.get("id"),
                    "status": order.get("status"),
                    "side": side,
                    "price": price,
                    "quantity": quantity,
                    "filled_qty": (order.get("quantity", 0) - order.get("remaining_qty", 0)) / SCALE,
                    "trades_executed": len(trades),
                }
            else:
                return {
                    "success": False,
                    "error": resp.text,
                    "status_code": resp.status_code
                }
                
    except httpx.ConnectError:
        return {"error": "Exchange not running"}
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="exchange_analyze",
    description="Perform analysis on the exchange's current state. Combines multiple queries into actionable insights.",
    parameters={
        "type": "object",
        "properties": {
            "analysis_type": {
                "type": "string",
                "enum": ["liquidity", "momentum", "opportunity", "summary"],
                "description": "Type of analysis to perform"
            },
            "symbol": {
                "type": "string",
                "default": "BTC-USD"
            }
        },
        "required": ["analysis_type"]
    }
)
def exchange_analyze(analysis_type: str, symbol: str = "BTC-USD") -> dict:
    """
    Perform market analysis on the exchange.
    """
    # Gather data
    book = exchange_query("book", symbol)
    trades = exchange_query("trades", symbol)
    depth = exchange_query("depth", symbol)
    spread = exchange_query("spread", symbol)
    
    if "error" in book:
        return book
    
    if analysis_type == "liquidity":
        return {
            "analysis": "liquidity",
            "symbol": symbol,
            "bid_liquidity_btc": depth.get("bid_depth_btc", 0),
            "ask_liquidity_btc": depth.get("ask_depth_btc", 0),
            "bid_liquidity_usd": depth.get("bid_value_usd", 0),
            "ask_liquidity_usd": depth.get("ask_value_usd", 0),
            "spread_bps": (spread.get("spread_percent", 0) or 0) * 100,
            "assessment": _assess_liquidity(depth, spread),
        }
    
    elif analysis_type == "momentum":
        trade_list = trades.get("trades", [])
        if len(trade_list) < 2:
            return {"analysis": "momentum", "note": "Not enough trades for momentum analysis"}
        
        recent_prices = [t["price"] for t in trade_list[:10]]
        avg_recent = sum(recent_prices) / len(recent_prices)
        
        if len(trade_list) >= 10:
            older_prices = [t["price"] for t in trade_list[10:20]]
            avg_older = sum(older_prices) / len(older_prices) if older_prices else avg_recent
            momentum = ((avg_recent - avg_older) / avg_older) * 100 if avg_older else 0
        else:
            momentum = 0
        
        return {
            "analysis": "momentum",
            "symbol": symbol,
            "recent_avg_price": avg_recent,
            "momentum_percent": round(momentum, 2),
            "trade_count": len(trade_list),
            "total_volume": trades.get("total_volume", 0),
            "signal": "BULLISH" if momentum > 0.5 else "BEARISH" if momentum < -0.5 else "NEUTRAL",
        }
    
    elif analysis_type == "opportunity":
        best_bid = spread.get("best_bid")
        best_ask = spread.get("best_ask")
        spread_pct = spread.get("spread_percent", 0) or 0
        imbalance = depth.get("imbalance", 0)
        
        opportunities = []
        
        if spread_pct > 0.5:
            opportunities.append({
                "type": "wide_spread",
                "description": f"Spread is {spread_pct:.2f}% - potential for market making",
                "action": "Place limit orders on both sides"
            })
        
        if imbalance > 0.3:
            opportunities.append({
                "type": "bid_heavy",
                "description": f"Order book {imbalance*100:.1f}% heavier on bid side",
                "action": "Bullish pressure - consider buying"
            })
        elif imbalance < -0.3:
            opportunities.append({
                "type": "ask_heavy", 
                "description": f"Order book {abs(imbalance)*100:.1f}% heavier on ask side",
                "action": "Bearish pressure - consider selling or waiting"
            })
        
        return {
            "analysis": "opportunity",
            "symbol": symbol,
            "opportunities": opportunities,
            "spread_percent": spread_pct,
            "book_imbalance": imbalance,
        }
    
    elif analysis_type == "summary":
        return {
            "analysis": "summary",
            "symbol": symbol,
            "best_bid": spread.get("best_bid"),
            "best_ask": spread.get("best_ask"),
            "mid_price": spread.get("mid_price"),
            "spread_percent": spread.get("spread_percent"),
            "bid_depth_btc": depth.get("bid_depth_btc"),
            "ask_depth_btc": depth.get("ask_depth_btc"),
            "recent_trades": trades.get("count", 0),
            "total_volume": trades.get("total_volume", 0),
        }
    
    return {"error": f"Unknown analysis type: {analysis_type}"}


def _assess_liquidity(depth: dict, spread: dict) -> str:
    """Generate liquidity assessment."""
    bid_depth = depth.get("bid_depth_btc", 0)
    ask_depth = depth.get("ask_depth_btc", 0)
    spread_pct = spread.get("spread_percent", 0) or 0
    
    total_depth = bid_depth + ask_depth
    
    if total_depth > 50 and spread_pct < 0.1:
        return "EXCELLENT - Deep liquidity, tight spread"
    elif total_depth > 20 and spread_pct < 0.3:
        return "GOOD - Adequate liquidity for most orders"
    elif total_depth > 5 and spread_pct < 1:
        return "MODERATE - May experience slippage on large orders"
    else:
        return "POOR - Thin liquidity, wide spread, exercise caution"
