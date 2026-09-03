"""
Basic smoke tests for all tools
Run with: pytest tests/test_tools.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import create_registry


def test_registry_creates_successfully():
    registry = create_registry()
    assert registry is not None
    print("Registry created successfully")


def test_all_tools_registered():
    registry = create_registry()
    tools = registry.list_tools()
    expected = [
        "sec_filing_search",
        "financial_data_api",
        "stock_price",
        "news_sentiment",
        "web_search",
        "company_profile",
        "earnings_transcript",
        "peer_comparison",
        "calculation_engine",
        "fact_checker",
        "vector_db_search",
        "report_generator"
    ]
    for tool in expected:
        assert tool in tools, f"Missing tool: {tool}"
    print(f"All {len(expected)} tools registered")


def test_sec_edgar_mock():
    registry = create_registry()
    result = registry.execute("sec_filing_search", {
        "ticker": "AAPL",
        "filing_type": "10-K"
    })
    assert result["success"] == True
    assert result["data"]["ticker"] == "AAPL"
    print("SEC EDGAR tool works")


def test_calculator_growth_rate():
    registry = create_registry()
    result = registry.execute("calculation_engine", {
        "calculation_type": "growth_rate",
        "inputs": {
            "current_value": 394000000000,
            "previous_value": 365000000000
        }
    })
    assert result["success"] == True
    assert "growth_rate_percent" in result["data"]["result"]
    print(f"Growth rate: {result['data']['result']['growth_rate_percent']}%")


def test_company_profile_mock():
    registry = create_registry()
    result = registry.execute("company_profile", {
        "ticker": "MSFT"
    })
    assert result["success"] == True
    print(f"Company: {result['data']['company_name']}")


def test_fact_checker():
    registry = create_registry()
    result = registry.execute("fact_checker", {
        "claim": "Apple revenue was $394 billion in 2023",
        "sources": ["SEC 10-K", "Alpha Vantage"]
    })
    assert result["success"] == True
    assert "confidence_score" in result["data"]
    print(f"Confidence: {result['data']['confidence_score']}")


def test_registry_stats():
    registry = create_registry()
    registry.execute("company_profile", {"ticker": "AAPL"})
    stats = registry.get_stats()
    assert stats["total_tools"] == 12
    print(f"Registry stats: {stats['total_tools']} tools registered")