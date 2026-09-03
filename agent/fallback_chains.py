"""
Fallback Chains
Defines fallback strategies for every tool
"""

from typing import Dict, Any, List, Optional, Callable
from agent.circuit_breaker import get_circuit_registry


# Fallback chain definitions
# Each tool has ordered list of fallbacks to try
FALLBACK_CHAINS = {
    "financial_data_api": ["stock_price", "vector_db_search"],
    "sec_filing_search": ["web_search", "vector_db_search"],
    "news_sentiment": ["web_search", "vector_db_search"],
    "stock_price": ["financial_data_api", "vector_db_search"],
    "earnings_transcript": ["web_search", "vector_db_search"],
    "company_profile": ["financial_data_api", "vector_db_search"],
    "peer_comparison": ["financial_data_api", "vector_db_search"],
    "web_search": ["vector_db_search"],
    "vector_db_search": [],
    "calculation_engine": [],
    "fact_checker": [],
    "report_generator": []
}


def execute_with_fallback(
    tool_name: str,
    inputs: Dict[str, Any],
    registry,
    failure_rate: float = 0.0
) -> Dict[str, Any]:
    """
    Execute a tool with automatic fallback chain.

    Args:
        tool_name: Primary tool to execute
        inputs: Tool inputs
        registry: Tool registry instance
        failure_rate: Simulated failure rate (0.0 to 1.0) for testing

    Returns:
        Result from primary tool or fallback
    """

    import random
    circuit = get_circuit_registry()
    fallbacks_tried = []

    # Check circuit breaker
    if not circuit.can_execute(tool_name):
        print(f"[Fallback] {tool_name} circuit is OPEN. Skipping to fallback.")
        return _try_fallbacks(tool_name, inputs, registry, fallbacks_tried)

    # Simulate failure for testing (Challenge 8)
    if failure_rate > 0 and random.random() < failure_rate:
        print(f"[Fallback] Simulated failure for {tool_name}")
        circuit.record_failure(tool_name)
        return _try_fallbacks(tool_name, inputs, registry, fallbacks_tried)

    # Try primary tool
    try:
        result = registry.execute(tool_name, inputs)

        if result.get("success"):
            circuit.record_success(tool_name)
            return {
                **result.get("data", {}),
                "tool_used": tool_name,
                "used_fallback": False,
                "fallbacks_tried": []
            }
        else:
            print(f"[Fallback] {tool_name} returned error: {result.get('error', 'unknown')}")
            circuit.record_failure(tool_name)
            return _try_fallbacks(tool_name, inputs, registry, fallbacks_tried)

    except Exception as e:
        print(f"[Fallback] {tool_name} exception: {str(e)[:80]}")
        circuit.record_failure(tool_name)
        return _try_fallbacks(tool_name, inputs, registry, fallbacks_tried)


def _try_fallbacks(
    original_tool: str,
    inputs: Dict[str, Any],
    registry,
    fallbacks_tried: List[str]
) -> Dict[str, Any]:
    """Try each fallback in the chain"""

    chain = FALLBACK_CHAINS.get(original_tool, [])
    circuit = get_circuit_registry()

    for fallback_tool in chain:
        if fallback_tool in fallbacks_tried:
            continue

        if not circuit.can_execute(fallback_tool):
            print(f"[Fallback] {fallback_tool} circuit also OPEN. Skipping.")
            continue

        fallbacks_tried.append(fallback_tool)

        try:
            # Adapt inputs for fallback tool
            adapted_inputs = _adapt_inputs(fallback_tool, inputs)
            result = registry.execute(fallback_tool, adapted_inputs)

            if result.get("success"):
                circuit.record_success(fallback_tool)
                print(f"[Fallback] Success with fallback: {fallback_tool}")
                return {
                    **result.get("data", {}),
                    "tool_used": fallback_tool,
                    "used_fallback": True,
                    "original_tool": original_tool,
                    "fallbacks_tried": fallbacks_tried,
                    "confidence_reduced": True
                }
            else:
                circuit.record_failure(fallback_tool)

        except Exception as e:
            print(f"[Fallback] {fallback_tool} also failed: {str(e)[:50]}")
            circuit.record_failure(fallback_tool)

    # All fallbacks exhausted
    print(f"[Fallback] All fallbacks exhausted for {original_tool}")
    return {
        "success": False,
        "tool_used": original_tool,
        "used_fallback": True,
        "fallbacks_tried": fallbacks_tried,
        "graceful_degradation": True,
        "message": f"Data unavailable: {original_tool} and all fallbacks failed. This section may be incomplete.",
        "source": "Graceful Degradation",
        "reliability_tier": 5
    }


def _adapt_inputs(
    fallback_tool: str,
    original_inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Adapt inputs from primary tool format to fallback tool format.
    Different tools have different input schemas.
    """

    ticker = original_inputs.get("ticker", "")
    query = original_inputs.get("query", ticker)

    if fallback_tool == "web_search":
        return {
            "query": f"{ticker} {query} financial data",
            "num_results": 5
        }

    if fallback_tool == "vector_db_search":
        return {
            "query": f"{ticker} {query}",
            "top_k": 3
        }

    if fallback_tool == "stock_price":
        return {
            "ticker": ticker,
            "period": "1y"
        }

    if fallback_tool == "financial_data_api":
        return {
            "ticker": ticker,
            "statement_type": "income",
            "period": "annual",
            "years": 3
        }

    return original_inputs


def simulate_tool_failures(failure_rate: float = 0.5):
    """
    Enable failure simulation for stress testing.
    Used for Challenge 8.

    Args:
        failure_rate: Probability of failure per tool call (0.0 to 1.0)
    """
    print(f"[Fallback] Failure simulation enabled: {failure_rate*100:.0f}% failure rate")
    return failure_rate


def get_fallback_stats() -> Dict[str, Any]:
    """Get statistics about fallback usage"""
    circuit = get_circuit_registry()
    status = circuit.get_all_status()

    open_circuits = [
        name for name, s in status.items()
        if s["state"] == "open"
    ]

    return {
        "total_tools_monitored": len(status),
        "open_circuits": open_circuits,
        "circuit_states": {
            name: s["state"]
            for name, s in status.items()
        }
    }