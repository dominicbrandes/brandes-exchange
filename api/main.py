#!/usr/bin/env python3
"""
Brandes Exchange API Server

Production-ready FastAPI server with in-memory matching engine.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import time

app = FastAPI(
    title="Brandes Exchange",
    description="High-performance limit order book matching engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCALE = 100_000_000


class Exchange:
    """In-memory matching engine with price-time priority."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.orders: Dict[int, dict] = {}
        self.trades: List[dict] = []
        self.balances: Dict[str, dict] = {}
        self.bids: Dict[int, List[dict]] = {}
        self.asks: Dict[int, List[dict]] = {}
        self.next_order_id = 1
        self.next_trade_id = 1
        self.sequence = 0
    
    def get_balance(self, account_id: str) -> dict:
        if account_id not in self.balances:
            self.balances[account_id] = {
                "usd": 100_000 * SCALE,
                "btc": 10 * SCALE,
                "usd_reserved": 0,
                "btc_reserved": 0,
            }
        return self.balances[account_id]
    
    def place_order(self, account_id: str, symbol: str, side: str, price: int, quantity: int) -> dict:
        bal = self.get_balance(account_id)
        
        # Balance check
        if side == "BUY":
            cost = (price * quantity) // SCALE
            if bal["usd"] < cost:
                return {"order": {"status": "REJECTED", "reject_reason": "INSUFFICIENT_BALANCE"}, "trades": []}
            bal["usd"] -= cost
            bal["usd_reserved"] += cost
        else:
            if bal["btc"] < quantity:
                return {"order": {"status": "REJECTED", "reject_reason": "INSUFFICIENT_BALANCE"}, "trades": []}
            bal["btc"] -= quantity
            bal["btc_reserved"] += quantity
        
        self.sequence += 1
        order = {
            "id": self.next_order_id,
            "account_id": account_id,
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "price": price,
            "quantity": quantity,
            "remaining_qty": quantity,
            "status": "NEW",
            "timestamp_ns": time.time_ns(),
        }
        self.next_order_id += 1
        self.orders[order["id"]] = order
        
        trades = self._match(order)
        
        if order["remaining_qty"] > 0 and order["status"] != "REJECTED":
            book = self.bids if side == "BUY" else self.asks
            if price not in book:
                book[price] = []
            book[price].append(order)
        
        return {"order": order, "trades": trades}
    
    def _match(self, order: dict) -> List[dict]:
        trades = []
        book = self.asks if order["side"] == "BUY" else self.bids
        prices = sorted(book.keys()) if order["side"] == "BUY" else sorted(book.keys(), reverse=True)
        
        for price in prices:
            if order["remaining_qty"] <= 0:
                break
            
            price_ok = (order["side"] == "BUY" and price <= order["price"]) or \
                       (order["side"] == "SELL" and price >= order["price"])
            if not price_ok:
                break
            
            level = book[price]
            i = 0
            while i < len(level) and order["remaining_qty"] > 0:
                resting = level[i]
                
                # Self-trade prevention
                if resting["account_id"] == order["account_id"]:
                    order["status"] = "REJECTED"
                    order["reject_reason"] = "SELF_TRADE"
                    bal = self.get_balance(order["account_id"])
                    if order["side"] == "BUY":
                        cost = (order["price"] * order["quantity"]) // SCALE
                        bal["usd"] += cost
                        bal["usd_reserved"] -= cost
                    else:
                        bal["btc"] += order["quantity"]
                        bal["btc_reserved"] -= order["quantity"]
                    return trades
                
                fill_qty = min(order["remaining_qty"], resting["remaining_qty"])
                fill_price = resting["price"]
                
                trade = {
                    "id": self.next_trade_id,
                    "symbol": order["symbol"],
                    "price": fill_price,
                    "quantity": fill_qty,
                    "timestamp_ns": time.time_ns(),
                    "buyer_account_id": order["account_id"] if order["side"] == "BUY" else resting["account_id"],
                    "seller_account_id": order["account_id"] if order["side"] == "SELL" else resting["account_id"],
                }
                self.next_trade_id += 1
                trades.append(trade)
                self.trades.append(trade)
                
                order["remaining_qty"] -= fill_qty
                resting["remaining_qty"] -= fill_qty
                
                self._settle(trade)
                
                if order["remaining_qty"] == 0:
                    order["status"] = "FILLED"
                else:
                    order["status"] = "PARTIAL"
                
                if resting["remaining_qty"] == 0:
                    resting["status"] = "FILLED"
                    level.pop(i)
                else:
                    resting["status"] = "PARTIAL"
                    i += 1
            
            if not level:
                del book[price]
        
        return trades
    
    def _settle(self, trade: dict):
        value = (trade["price"] * trade["quantity"]) // SCALE
        
        buyer = self.get_balance(trade["buyer_account_id"])
        buyer["usd_reserved"] -= value
        buyer["btc"] += trade["quantity"]
        
        seller = self.get_balance(trade["seller_account_id"])
        seller["btc_reserved"] -= trade["quantity"]
        seller["usd"] += value
    
    def cancel_order(self, order_id: int) -> Optional[dict]:
        if order_id not in self.orders:
            return None
        
        order = self.orders[order_id]
        if order["status"] not in ("NEW", "PARTIAL"):
            return None
        
        self.sequence += 1
        
        book = self.bids if order["side"] == "BUY" else self.asks
        price = order["price"]
        if price in book:
            book[price] = [o for o in book[price] if o["id"] != order_id]
            if not book[price]:
                del book[price]
        
        bal = self.get_balance(order["account_id"])
        if order["side"] == "BUY":
            cost = (order["price"] * order["remaining_qty"]) // SCALE
            bal["usd"] += cost
            bal["usd_reserved"] -= cost
        else:
            bal["btc"] += order["remaining_qty"]
            bal["btc_reserved"] -= order["remaining_qty"]
        
        order["status"] = "CANCELLED"
        return order
    
    def get_book(self, symbol: str) -> dict:
        bid_levels = []
        cumulative = 0
        for price in sorted(self.bids.keys(), reverse=True)[:20]:
            qty = sum(o["remaining_qty"] for o in self.bids[price])
            cumulative += qty
            bid_levels.append({"price": price, "quantity": qty, "total": cumulative})
        
        ask_levels = []
        cumulative = 0
        for price in sorted(self.asks.keys())[:20]:
            qty = sum(o["remaining_qty"] for o in self.asks[price])
            cumulative += qty
            ask_levels.append({"price": price, "quantity": qty, "total": cumulative})
        
        return {"symbol": symbol, "bids": bid_levels, "asks": ask_levels, "sequence": self.sequence}


exchange = Exchange()


class OrderRequest(BaseModel):
    account_id: str
    symbol: str
    side: str
    type: str = "LIMIT"
    price: int
    quantity: int


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "engine_connected": True}


@app.get("/api/v1/book/{symbol}")
async def get_book(symbol: str):
    return exchange.get_book(symbol)


@app.get("/api/v1/trades/{symbol}")
async def get_trades(symbol: str, limit: int = 100):
    trades = [t for t in reversed(exchange.trades) if t["symbol"] == symbol][:limit]
    return {"trades": trades}


@app.get("/api/v1/accounts/{account_id}/balances")
async def get_balances(account_id: str):
    return exchange.get_balance(account_id)


@app.post("/api/v1/orders")
async def place_order(req: OrderRequest):
    result = exchange.place_order(req.account_id, req.symbol, req.side, req.price, req.quantity)
    if result["order"].get("status") == "REJECTED":
        raise HTTPException(400, result["order"].get("reject_reason", "REJECTED"))
    return result


@app.delete("/api/v1/orders/{order_id}")
async def cancel_order(order_id: int):
    result = exchange.cancel_order(order_id)
    if result is None:
        raise HTTPException(404, "ORDER_NOT_FOUND")
    return result


@app.post("/api/v1/admin/reset")
async def reset():
    exchange.reset()
    return {"ok": True}


@app.get("/api/v1/stats")
async def stats():
    return {
        "total_orders": len(exchange.orders),
        "total_trades": len(exchange.trades),
        "sequence": exchange.sequence,
    }


@app.get("/metrics")
async def metrics():
    return f"""# Brandes Exchange Metrics
brandes_orders_total {len(exchange.orders)}
brandes_trades_total {len(exchange.trades)}
brandes_sequence {exchange.sequence}
"""


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("Brandes Exchange API")
    print("=" * 50)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
