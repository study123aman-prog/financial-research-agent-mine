"""
Conflict Resolver
Handles contradictory data between sources
"""

from typing import Dict, Any, List


def resolve_data_conflicts(
    data: Dict[str, Any],
    source_hierarchy: Dict[str, int] = None
) -> Dict[str, Any]:
    """
    Resolve conflicts in research data using source hierarchy.

    Args:
        data: Research data with potential conflicts
        source_hierarchy: Custom source reliability tiers

    Returns:
        Resolved data with conflict notes
    """

    if not source_hierarchy:
        source_hierarchy = {
            "SEC EDGAR": 1,
            "Alpha Vantage": 2,
            "Yahoo Finance": 2,
            "Earnings Call": 3,
            "NewsAPI": 4,
            "Web Search": 4
        }

    conflicts_found = []
    resolved_data = {}

    # Protocol: identify, assess, check temporal, check restatements,
    # apply highest tier rule, document

    for key, values in data.items():
        if not isinstance(values, list) or len(values) < 2:
            resolved_data[key] = values
            continue

        # Multiple values for same metric - potential conflict
        sorted_values = sorted(
            values,
            key=lambda x: source_hierarchy.get(x.get("source", ""), 5)
        )

        # Use the highest tier (lowest number) source
        preferred = sorted_values[0]
        others = sorted_values[1:]

        conflict_note = None
        if others:
            conflict_note = {
                "metric": key,
                "preferred_value": preferred.get("value"),
                "preferred_source": preferred.get("source"),
                "conflicting_values": [
                    {
                        "value": o.get("value"),
                        "source": o.get("source")
                    }
                    for o in others
                ],
                "resolution": "Applied highest-tier source rule"
            }
            conflicts_found.append(conflict_note)

        resolved_data[key] = preferred

    return {
        "resolved_data": resolved_data,
        "conflicts_found": conflicts_found,
        "total_conflicts": len(conflicts_found),
        "resolution_method": "Source reliability hierarchy (Tier 1-5)"
    }


def check_sentiment_fact_alignment(
    sentiment_data: Dict[str, Any],
    financial_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Check if news sentiment aligns with financial facts.
    Misalignment is itself an analytical finding.

    Args:
        sentiment_data: News sentiment results
        financial_data: Financial statement results

    Returns:
        Alignment analysis
    """

    sentiment = sentiment_data.get("overall_sentiment", "neutral")
    sentiment_score = sentiment_data.get("average_sentiment", 0)

    reports = financial_data.get("reports", [])
    financial_trend = "unknown"

    if reports and len(reports) >= 2:
        try:
            current = float(reports[0].get("totalRevenue", 0) or 0)
            previous = float(reports[1].get("totalRevenue", 0) or 0)

            if previous > 0:
                growth = (current - previous) / previous
                if growth > 0.05:
                    financial_trend = "positive"
                elif growth < -0.05:
                    financial_trend = "negative"
                else:
                    financial_trend = "neutral"
        except (ValueError, TypeError):
            financial_trend = "unknown"

    # Check alignment
    aligned = True
    alignment_note = ""

    if sentiment == "positive" and financial_trend == "negative":
        aligned = False
        alignment_note = "WARNING: Positive news sentiment contradicts negative financial trend. Management may be projecting optimism despite deteriorating financials."

    elif sentiment == "negative" and financial_trend == "positive":
        aligned = False
        alignment_note = "NOTE: Negative news sentiment contradicts positive financial trend. Market concerns may not yet be reflected in reported financials."

    else:
        alignment_note = f"Sentiment ({sentiment}) aligns with financial trend ({financial_trend})."

    return {
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "financial_trend": financial_trend,
        "aligned": aligned,
        "alignment_note": alignment_note,
        "is_analytical_finding": not aligned
    }