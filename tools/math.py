"""
Mathematical calculation tools.
"""

import math
import re
from typing import Optional

from .base import tool


@tool(
    name="calculate",
    description="Perform mathematical calculations. Supports basic arithmetic, percentages, financial formulas, and unit conversions.",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate (e.g., '15.3 * 1e9 / 3170', '((100 - 85) / 85) * 100')"
            },
            "precision": {
                "type": "integer",
                "description": "Decimal precision for result",
                "default": 4
            }
        },
        "required": ["expression"]
    }
)
def calculate(expression: str, precision: int = 4) -> dict:
    """
    Evaluate a mathematical expression safely.
    """
    try:
        # Sanitize input - only allow safe characters
        allowed_chars = set("0123456789+-*/().e ,")
        safe_expr = ''.join(c for c in expression.lower() if c in allowed_chars)
        
        # Replace common patterns
        safe_expr = safe_expr.replace(" ", "")
        
        # Evaluate using restricted builtins
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
        }
        
        result = eval(safe_expr, {"__builtins__": {}}, allowed_names)
        
        # Format result
        if isinstance(result, float):
            result = round(result, precision)
        
        return {
            "expression": expression,
            "result": result,
            "formatted": _format_number(result)
        }
        
    except Exception as e:
        return {
            "expression": expression,
            "error": f"Calculation error: {str(e)}"
        }


def _format_number(n: float) -> str:
    """Format number with appropriate suffix."""
    abs_n = abs(n)
    if abs_n >= 1e12:
        return f"{n/1e12:.2f}T"
    elif abs_n >= 1e9:
        return f"{n/1e9:.2f}B"
    elif abs_n >= 1e6:
        return f"{n/1e6:.2f}M"
    elif abs_n >= 1e3:
        return f"{n/1e3:.2f}K"
    elif abs_n < 0.01 and abs_n > 0:
        return f"{n:.6f}"
    else:
        return f"{n:.2f}"


@tool(
    name="calculate_apy",
    description="Calculate APY from APR or vice versa, with compounding frequency.",
    parameters={
        "type": "object",
        "properties": {
            "rate": {
                "type": "number",
                "description": "Interest rate as percentage (e.g., 5.5 for 5.5%)"
            },
            "from_type": {
                "type": "string",
                "enum": ["apr", "apy"],
                "description": "Type of input rate"
            },
            "compounds_per_year": {
                "type": "integer",
                "description": "Number of compounding periods per year (365 for daily, 12 for monthly)",
                "default": 365
            }
        },
        "required": ["rate", "from_type"]
    }
)
def calculate_apy(
    rate: float,
    from_type: str,
    compounds_per_year: int = 365
) -> dict:
    """
    Convert between APR and APY.
    """
    rate_decimal = rate / 100
    
    if from_type.lower() == "apr":
        # APR to APY
        apy = (1 + rate_decimal / compounds_per_year) ** compounds_per_year - 1
        return {
            "input_apr": rate,
            "output_apy": round(apy * 100, 4),
            "compounds_per_year": compounds_per_year,
            "formula": f"APY = (1 + {rate}%/{compounds_per_year})^{compounds_per_year} - 1"
        }
    else:
        # APY to APR
        apr = compounds_per_year * ((1 + rate_decimal) ** (1 / compounds_per_year) - 1)
        return {
            "input_apy": rate,
            "output_apr": round(apr * 100, 4),
            "compounds_per_year": compounds_per_year,
            "formula": f"APR = {compounds_per_year} * ((1 + {rate}%)^(1/{compounds_per_year}) - 1)"
        }


@tool(
    name="calculate_impermanent_loss",
    description="Calculate impermanent loss for a liquidity position given price change.",
    parameters={
        "type": "object",
        "properties": {
            "price_change_percent": {
                "type": "number",
                "description": "Percentage change in price ratio (e.g., 50 for 50% increase, -30 for 30% decrease)"
            },
            "initial_value": {
                "type": "number",
                "description": "Initial value of LP position in USD",
                "default": 10000
            }
        },
        "required": ["price_change_percent"]
    }
)
def calculate_impermanent_loss(
    price_change_percent: float,
    initial_value: float = 10000
) -> dict:
    """
    Calculate impermanent loss for a 50/50 LP position.
    """
    # Price ratio (new price / old price)
    price_ratio = 1 + (price_change_percent / 100)
    
    if price_ratio <= 0:
        return {"error": "Price cannot go to zero or negative"}
    
    # IL formula: 2 * sqrt(price_ratio) / (1 + price_ratio) - 1
    il = 2 * math.sqrt(price_ratio) / (1 + price_ratio) - 1
    il_percent = il * 100
    
    # Calculate values
    lp_value = initial_value * (1 + il)
    hold_value = initial_value * (1 + price_change_percent / 200)  # 50% exposed to price change
    loss_usd = hold_value - lp_value
    
    return {
        "price_change_percent": price_change_percent,
        "impermanent_loss_percent": round(il_percent, 4),
        "initial_value": initial_value,
        "lp_value_now": round(lp_value, 2),
        "hold_value_now": round(hold_value, 2),
        "loss_vs_holding": round(loss_usd, 2),
        "note": "IL is only realized when you withdraw. Fees earned may offset IL."
    }


@tool(
    name="convert_units",
    description="Convert between common crypto units (wei, gwei, ether, etc.)",
    parameters={
        "type": "object",
        "properties": {
            "value": {
                "type": "number",
                "description": "Value to convert"
            },
            "from_unit": {
                "type": "string",
                "enum": ["wei", "gwei", "ether", "eth"],
                "description": "Source unit"
            },
            "to_unit": {
                "type": "string",
                "enum": ["wei", "gwei", "ether", "eth"],
                "description": "Target unit"
            }
        },
        "required": ["value", "from_unit", "to_unit"]
    }
)
def convert_units(value: float, from_unit: str, to_unit: str) -> dict:
    """
    Convert between Ethereum units.
    """
    # Normalize unit names
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    if from_unit == "eth":
        from_unit = "ether"
    if to_unit == "eth":
        to_unit = "ether"
    
    # Conversion factors to wei
    to_wei = {
        "wei": 1,
        "gwei": 1e9,
        "ether": 1e18,
    }
    
    if from_unit not in to_wei or to_unit not in to_wei:
        return {"error": f"Unknown unit. Supported: wei, gwei, ether/eth"}
    
    # Convert via wei
    wei_value = value * to_wei[from_unit]
    result = wei_value / to_wei[to_unit]
    
    return {
        "input": value,
        "from_unit": from_unit,
        "to_unit": to_unit,
        "result": result,
        "formatted": _format_number(result)
    }
