"""
Sentinel Agent Test Suite

Run with: pytest tests/ -v
"""

import pytest
import asyncio
import json
from datetime import datetime
from pathlib import Path
import tempfile
import os

# Import modules to test
from tools.base import ToolResult, ToolRegistry, tool, registry
from tools.web import web_search, fetch_url
from tools.blockchain import eth_call, get_token_price, get_gas_price
from tools.math import calculate, calculate_apy, calculate_impermanent_loss, convert_units
from tools.risk import assess_risk, compare_risks
from tools.memory import store_memory, recall_memory, clear_memory, generate_report

from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from memory.episodic import EpisodicMemory


# ============================================================================
# Tool Tests
# ============================================================================

class TestWebTools:
    """Test web search and fetch tools."""
    
    def test_web_search_returns_results(self):
        result = web_search("EigenLayer restaking")
        assert "results" in result
        assert len(result["results"]) > 0
        assert "query" in result
    
    def test_web_search_respects_limit(self):
        result = web_search("DeFi", num_results=3)
        assert len(result["results"]) <= 3
    
    def test_web_search_result_structure(self):
        result = web_search("Lido staking")
        for r in result["results"]:
            assert "title" in r
            assert "url" in r
            assert "snippet" in r
    
    def test_fetch_url_handles_errors(self):
        result = fetch_url("https://invalid-url-that-does-not-exist.xyz")
        assert "error" in result


class TestBlockchainTools:
    """Test blockchain query tools."""
    
    def test_eth_call_known_contract(self):
        result = eth_call(
            contract="eigenlayer_strategy_manager",
            method="totalSupply"
        )
        assert "result" in result or "decoded" in result
    
    def test_get_token_price_known_token(self):
        result = get_token_price("ETH")
        assert "price_usd" in result
        assert result["price_usd"] > 0
    
    def test_get_token_price_with_metadata(self):
        result = get_token_price("ETH", include_metadata=True)
        assert "market_cap" in result
        assert "volume_24h" in result
    
    def test_get_token_price_unknown_token(self):
        result = get_token_price("UNKNOWN_TOKEN_XYZ")
        assert "error" in result
    
    def test_get_gas_price(self):
        result = get_gas_price()
        assert "base_fee_gwei" in result
        assert "estimates" in result


class TestMathTools:
    """Test calculation tools."""
    
    def test_calculate_basic(self):
        result = calculate("2 + 2")
        assert result["result"] == 4
    
    def test_calculate_complex(self):
        result = calculate("(15.3 * 1e9) / 3170")
        assert "result" in result
        assert result["result"] > 0
    
    def test_calculate_percentage(self):
        result = calculate("((100 - 85) / 85) * 100")
        assert abs(result["result"] - 17.6471) < 0.01
    
    def test_calculate_formats_large_numbers(self):
        result = calculate("15.3 * 1e9")
        assert "formatted" in result
        assert "B" in result["formatted"]
    
    def test_calculate_apy_from_apr(self):
        result = calculate_apy(5.0, "apr", 365)
        assert "output_apy" in result
        assert result["output_apy"] > 5.0  # APY > APR with compounding
    
    def test_calculate_apy_from_apy(self):
        result = calculate_apy(5.12, "apy", 365)
        assert "output_apr" in result
        assert result["output_apr"] < 5.12  # APR < APY
    
    def test_impermanent_loss_positive(self):
        result = calculate_impermanent_loss(100)  # 100% price increase
        assert result["impermanent_loss_percent"] < 0  # IL is negative
    
    def test_impermanent_loss_negative(self):
        result = calculate_impermanent_loss(-50)  # 50% price decrease
        assert result["impermanent_loss_percent"] < 0
    
    def test_convert_units_eth_to_wei(self):
        result = convert_units(1, "ether", "wei")
        assert result["result"] == 1e18
    
    def test_convert_units_gwei_to_eth(self):
        result = convert_units(1e9, "gwei", "eth")
        assert result["result"] == 1


class TestRiskTools:
    """Test risk assessment tools."""
    
    def test_assess_risk_known_protocol(self):
        result = assess_risk("EigenLayer")
        assert "overall_score" in result
        assert "risks" in result
        assert len(result["risks"]) > 0
    
    def test_assess_risk_all_types(self):
        result = assess_risk("Lido", ["all"])
        risk_types = [r["type"] for r in result["risks"]]
        assert "smart_contract" in risk_types
        assert "economic" in risk_types
    
    def test_assess_risk_specific_type(self):
        result = assess_risk("Aave", ["smart_contract", "liquidity"])
        risk_types = [r["type"] for r in result["risks"]]
        assert "smart_contract" in risk_types
        assert "slashing" not in risk_types
    
    def test_assess_risk_unknown_protocol(self):
        result = assess_risk("UnknownProtocol123")
        assert result["overall_score"] >= 5  # Should be high risk
    
    def test_compare_risks(self):
        result = compare_risks(["EigenLayer", "Lido", "Aave"])
        assert "comparison" in result
        assert len(result["comparison"]) == 3
        assert "safest" in result


class TestMemoryTools:
    """Test memory and report tools."""
    
    def test_store_and_recall(self):
        store_memory("test_key", {"value": 123}, "test")
        result = recall_memory("test_key")
        assert result["found"] == True
        assert result["value"]["value"] == 123
    
    def test_recall_nonexistent(self):
        result = recall_memory("nonexistent_key_xyz")
        assert result["found"] == False
    
    def test_clear_memory(self):
        store_memory("temp_key", {"data": "test"})
        clear_memory("temp_key")
        result = recall_memory("temp_key")
        assert result["found"] == False
    
    def test_generate_report_markdown(self):
        result = generate_report(
            title="Test Report",
            sections=[
                {"heading": "Section 1", "content": "Test content"}
            ],
            summary="This is a test report"
        )
        assert result["format"] == "markdown"
        assert "# Test Report" in result["report"]
    
    def test_generate_report_json(self):
        result = generate_report(
            title="Test Report",
            sections=[{"heading": "Data", "content": "Info"}],
            format="json"
        )
        assert "title" in result
        assert result["title"] == "Test Report"


# ============================================================================
# Memory System Tests
# ============================================================================

class TestShortTermMemory:
    """Test short-term memory."""
    
    def test_add_and_retrieve(self):
        mem = ShortTermMemory(max_items=5)
        mem.add("Test message", "user")
        recent = mem.get_recent(1)
        assert len(recent) == 1
        assert recent[0].content == "Test message"
    
    def test_max_items_limit(self):
        mem = ShortTermMemory(max_items=3)
        for i in range(5):
            mem.add(f"Message {i}")
        assert mem.size == 3
    
    def test_facts_storage(self):
        mem = ShortTermMemory()
        mem.add_fact("tvl", "$15.3B")
        assert "tvl" in mem.facts
    
    def test_search(self):
        mem = ShortTermMemory()
        mem.add("EigenLayer has $15B TVL")
        mem.add("Lido is a liquid staking protocol")
        results = mem.search("EigenLayer")
        assert len(results) == 1
    
    def test_context_string(self):
        mem = ShortTermMemory()
        mem.add("User asked about restaking", "user")
        mem.add_fact("protocol", "EigenLayer")
        context = mem.get_context_string()
        assert "EigenLayer" in context


class TestLongTermMemory:
    """Test long-term memory with temp database."""
    
    @pytest.fixture
    def temp_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield LongTermMemory(f"{tmpdir}/test.db")
    
    def test_store_and_recall(self, temp_db):
        temp_db.store("test_key", {"value": 42}, "test")
        result = temp_db.recall("test_key")
        assert result is not None
        assert result.value["value"] == 42
    
    def test_recall_nonexistent(self, temp_db):
        result = temp_db.recall("nonexistent")
        assert result is None
    
    def test_search(self, temp_db):
        temp_db.store("eigenlayer_tvl", 15.3, tags=["defi", "tvl"])
        temp_db.store("lido_tvl", 28.4, tags=["defi", "tvl"])
        results = temp_db.search("tvl")
        assert len(results) == 2
    
    def test_delete(self, temp_db):
        temp_db.store("to_delete", "data")
        assert temp_db.delete("to_delete") == True
        assert temp_db.recall("to_delete") is None
    
    def test_export_import(self, temp_db):
        temp_db.store("key1", "value1")
        temp_db.store("key2", "value2")
        exported = temp_db.export()
        
        temp_db.clear()
        temp_db.import_data(exported)
        
        assert temp_db.count() == 2


class TestEpisodicMemory:
    """Test episodic memory."""
    
    @pytest.fixture
    def temp_episodic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield EpisodicMemory(f"{tmpdir}/episodes.json")
    
    def test_save_session(self, temp_episodic):
        ep = temp_episodic.save_session(
            summary="Discussed EigenLayer TVL",
            key_facts=["TVL is $15.3B"],
            topics=["eigenlayer", "tvl"]
        )
        assert ep.session_id is not None
    
    def test_search_by_topic(self, temp_episodic):
        temp_episodic.save_session(
            summary="Talked about Lido",
            key_facts=["Lido has $28B TVL"],
            topics=["lido", "staking"]
        )
        results = temp_episodic.search(topics=["lido"])
        assert len(results) == 1
    
    def test_relevance_scoring(self, temp_episodic):
        temp_episodic.save_session(
            summary="EigenLayer restaking analysis",
            key_facts=["Restaking lets you stake ETH twice"],
            topics=["eigenlayer", "restaking"]
        )
        results = temp_episodic.search("EigenLayer restaking")
        assert len(results) > 0


# ============================================================================
# Tool Registry Tests
# ============================================================================

class TestToolRegistry:
    """Test tool registration and execution."""
    
    def test_registry_has_tools(self):
        assert len(registry.list_tools()) > 0
    
    def test_registry_get_tool(self):
        tool_spec = registry.get("web_search")
        assert tool_spec is not None
        assert tool_spec.name == "web_search"
    
    def test_anthropic_format(self):
        tools = registry.to_anthropic_tools()
        assert len(tools) > 0
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
    
    @pytest.mark.asyncio
    async def test_execute_tool(self):
        result = await registry.execute("calculate", expression="1+1")
        assert result.success == True
        assert result.data["result"] == 2
    
    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        result = await registry.execute("unknown_tool_xyz")
        assert result.success == False


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_research_workflow(self):
        """Simulate a research workflow."""
        # Search for info
        search_result = web_search("EigenLayer TVL")
        assert len(search_result["results"]) > 0
        
        # Get token price
        price = get_token_price("ETH")
        assert price["price_usd"] > 0
        
        # Calculate TVL in ETH terms
        tvl_usd = 15.3e9
        eth_price = price["price_usd"]
        calc_result = calculate(f"{tvl_usd} / {eth_price}")
        assert calc_result["result"] > 0
        
        # Assess risks
        risk = assess_risk("EigenLayer")
        assert risk["overall_score"] > 0
        
        # Generate report
        report = generate_report(
            title="EigenLayer Analysis",
            sections=[
                {"heading": "TVL", "content": f"${tvl_usd/1e9}B"},
                {"heading": "Risk", "content": f"Score: {risk['overall_score']}/10"}
            ]
        )
        assert "# EigenLayer Analysis" in report["report"]
    
    def test_memory_persistence(self):
        """Test memory across operations."""
        # Store data
        store_memory("research_tvl", {"eigenlayer": 15.3, "lido": 28.4})
        
        # Recall and verify
        recalled = recall_memory("research_tvl")
        assert recalled["found"] == True
        assert recalled["value"]["eigenlayer"] == 15.3
        
        # Clean up
        clear_memory("research_tvl")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
