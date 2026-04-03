"""
Risk assessment tools for DeFi protocols.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

from .base import tool


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskFactor:
    name: str
    score: float  # 1-10
    level: RiskLevel
    description: str
    mitigations: list[str]


@tool(
    name="assess_risk",
    description="Assess risks for a DeFi protocol or strategy. Evaluates smart contract, economic, slashing, liquidity, and centralization risks.",
    parameters={
        "type": "object",
        "properties": {
            "protocol": {
                "type": "string",
                "description": "Protocol name to assess (e.g., 'EigenLayer', 'Lido', 'Aave')"
            },
            "risk_types": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["smart_contract", "economic", "slashing", "liquidity", "centralization", "all"]
                },
                "description": "Types of risks to assess",
                "default": ["all"]
            },
            "context": {
                "type": "string",
                "description": "Additional context (e.g., 'restaking strategy', 'LP position')",
                "default": ""
            }
        },
        "required": ["protocol"]
    }
)
def assess_risk(
    protocol: str,
    risk_types: Optional[list[str]] = None,
    context: str = ""
) -> dict:
    """
    Comprehensive risk assessment for a protocol.
    """
    risk_types = risk_types or ["all"]
    if "all" in risk_types:
        risk_types = ["smart_contract", "economic", "slashing", "liquidity", "centralization"]
    
    protocol_lower = protocol.lower()
    
    # Get risk data for known protocols
    risks = _get_protocol_risks(protocol_lower)
    
    # Filter by requested types
    filtered_risks = [r for r in risks if r["type"] in risk_types]
    
    # Calculate overall score
    if filtered_risks:
        overall_score = sum(r["score"] for r in filtered_risks) / len(filtered_risks)
    else:
        overall_score = 5.0
    
    # Determine overall level
    if overall_score <= 3:
        overall_level = "low"
    elif overall_score <= 5:
        overall_level = "medium"
    elif overall_score <= 7:
        overall_level = "high"
    else:
        overall_level = "critical"
    
    return {
        "protocol": protocol,
        "context": context,
        "overall_score": round(overall_score, 1),
        "overall_level": overall_level,
        "risks": filtered_risks,
        "recommendations": _get_recommendations(overall_level, filtered_risks),
        "disclaimer": "This is an automated assessment. Always do your own research and consider consulting experts."
    }


def _get_protocol_risks(protocol: str) -> list[dict]:
    """Get risk data for known protocols."""
    
    risk_db = {
        "eigenlayer": [
            {
                "type": "smart_contract",
                "score": 3.5,
                "level": "medium",
                "description": "Audited by multiple firms (Sigma Prime, Consensys Diligence). Complex restaking logic introduces some risk. No major exploits to date.",
                "mitigations": [
                    "Multiple audits completed",
                    "Bug bounty program active",
                    "Gradual rollout with caps"
                ]
            },
            {
                "type": "economic",
                "score": 4.0,
                "level": "medium",
                "description": "Novel economic model with restaking. EIGEN token still early. Dependency on ETH price and staking rewards.",
                "mitigations": [
                    "Aligned incentives with ETH stakers",
                    "Gradual AVS onboarding",
                    "Slashing insurance being developed"
                ]
            },
            {
                "type": "slashing",
                "score": 5.5,
                "level": "medium",
                "description": "Slashing conditions vary by AVS. Operators can be slashed for misbehavior. Max slash up to 50% in some AVSs.",
                "mitigations": [
                    "Choose reputable operators",
                    "Diversify across operators",
                    "Monitor AVS slashing conditions"
                ]
            },
            {
                "type": "liquidity",
                "score": 4.5,
                "level": "medium",
                "description": "Restaked assets have withdrawal delays (7 days). LST restaking provides better liquidity than native restaking.",
                "mitigations": [
                    "Use liquid restaking tokens (LRTs)",
                    "Maintain emergency reserves",
                    "Understand withdrawal timelines"
                ]
            },
            {
                "type": "centralization",
                "score": 4.0,
                "level": "medium",
                "description": "Early stage with significant team/VC token holdings. Operator set growing but concentrated. Governance still centralizing.",
                "mitigations": [
                    "Progressive decentralization planned",
                    "Multiple operators available",
                    "Community governance roadmap"
                ]
            }
        ],
        "lido": [
            {
                "type": "smart_contract",
                "score": 2.5,
                "level": "low",
                "description": "Battle-tested since 2020. Multiple audits. $28B+ TVL with no major exploits. Mature codebase.",
                "mitigations": [
                    "Extensive audit history",
                    "Large bug bounty",
                    "Formal verification on critical paths"
                ]
            },
            {
                "type": "economic",
                "score": 3.0,
                "level": "low",
                "description": "Proven liquid staking model. stETH maintains peg well. Revenue from staking fees is sustainable.",
                "mitigations": [
                    "Diversified node operator set",
                    "Insurance fund",
                    "Stable tokenomics"
                ]
            },
            {
                "type": "slashing",
                "score": 3.0,
                "level": "low",
                "description": "Standard Ethereum validator slashing. Distributed across 30+ node operators. Insurance covers slashing losses.",
                "mitigations": [
                    "Node operator vetting",
                    "Slashing insurance",
                    "Diversification"
                ]
            },
            {
                "type": "liquidity",
                "score": 2.0,
                "level": "low",
                "description": "stETH highly liquid on DEXs. Can exit via Curve, 1inch, or native withdrawal. Deep liquidity pools.",
                "mitigations": [
                    "Multiple exit routes",
                    "Native withdrawals enabled",
                    "wstETH for DeFi composability"
                ]
            },
            {
                "type": "centralization",
                "score": 4.0,
                "level": "medium",
                "description": "~30% of all staked ETH. Node operator concentration concerns. DAO governance operational.",
                "mitigations": [
                    "Self-limiting discussions ongoing",
                    "DVT adoption planned",
                    "Governance active"
                ]
            }
        ],
        "aave": [
            {
                "type": "smart_contract",
                "score": 2.0,
                "level": "low",
                "description": "Industry-leading security. Multiple audits per version. Active security team. Proven over years.",
                "mitigations": [
                    "Formal verification",
                    "Gradual rollouts",
                    "Security council"
                ]
            },
            {
                "type": "economic",
                "score": 3.0,
                "level": "low",
                "description": "Overcollateralized lending model. Liquidation mechanisms work well. Safety module provides backstop.",
                "mitigations": [
                    "Conservative LTV ratios",
                    "Liquidation incentives",
                    "Safety module"
                ]
            },
            {
                "type": "liquidity",
                "score": 2.5,
                "level": "low",
                "description": "Highly liquid markets. Can withdraw instantly if utilization allows. Multi-chain deployment.",
                "mitigations": [
                    "Utilization caps",
                    "Interest rate curves",
                    "Emergency procedures"
                ]
            },
            {
                "type": "centralization",
                "score": 3.5,
                "level": "medium",
                "description": "DAO-governed. Guardian multisig for emergencies. Active governance participation.",
                "mitigations": [
                    "Timelock on changes",
                    "Active DAO",
                    "Guardian oversight"
                ]
            }
        ]
    }
    
    # Return risks for known protocol or generate generic assessment
    if protocol in risk_db:
        return risk_db[protocol]
    
    # Generic assessment for unknown protocols
    return [
        {
            "type": "smart_contract",
            "score": 6.0,
            "level": "high",
            "description": f"Unknown protocol '{protocol}'. Smart contract risk cannot be assessed without audit information.",
            "mitigations": ["Verify audit reports", "Check for bug bounty", "Start with small amounts"]
        },
        {
            "type": "economic",
            "score": 6.0,
            "level": "high",
            "description": "Economic model not evaluated. Research tokenomics and sustainability.",
            "mitigations": ["Study tokenomics", "Understand revenue model", "Check team background"]
        }
    ]


def _get_recommendations(level: str, risks: list[dict]) -> list[str]:
    """Generate recommendations based on risk assessment."""
    recommendations = []
    
    if level in ["high", "critical"]:
        recommendations.append("⚠️ Consider reducing exposure or avoiding this protocol")
        recommendations.append("Only invest what you can afford to lose")
    
    # Add specific recommendations based on high-scoring risks
    for risk in risks:
        if risk["score"] >= 5:
            if risk["type"] == "smart_contract":
                recommendations.append("Wait for additional audits before increasing position")
            elif risk["type"] == "slashing":
                recommendations.append("Diversify across multiple operators to reduce slashing risk")
            elif risk["type"] == "liquidity":
                recommendations.append("Maintain reserves outside this protocol for emergencies")
            elif risk["type"] == "centralization":
                recommendations.append("Monitor governance proposals and team actions closely")
    
    if not recommendations:
        recommendations.append("Risk profile is acceptable for most users")
        recommendations.append("Continue monitoring for changes in risk factors")
    
    return recommendations


@tool(
    name="compare_risks",
    description="Compare risks between multiple protocols or strategies.",
    parameters={
        "type": "object",
        "properties": {
            "protocols": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of protocols to compare"
            },
            "risk_type": {
                "type": "string",
                "enum": ["smart_contract", "economic", "slashing", "liquidity", "centralization", "overall"],
                "description": "Specific risk type to compare, or 'overall' for aggregate",
                "default": "overall"
            }
        },
        "required": ["protocols"]
    }
)
def compare_risks(protocols: list[str], risk_type: str = "overall") -> dict:
    """
    Compare risks across multiple protocols.
    """
    comparisons = []
    
    for protocol in protocols:
        assessment = assess_risk(protocol, ["all"])
        
        if risk_type == "overall":
            score = assessment["overall_score"]
            level = assessment["overall_level"]
        else:
            matching = [r for r in assessment["risks"] if r["type"] == risk_type]
            if matching:
                score = matching[0]["score"]
                level = matching[0]["level"]
            else:
                score = None
                level = "unknown"
        
        comparisons.append({
            "protocol": protocol,
            "score": score,
            "level": level
        })
    
    # Sort by score (lower is better)
    comparisons.sort(key=lambda x: x["score"] or 10)
    
    return {
        "risk_type": risk_type,
        "comparison": comparisons,
        "safest": comparisons[0]["protocol"] if comparisons else None,
        "riskiest": comparisons[-1]["protocol"] if comparisons else None
    }
