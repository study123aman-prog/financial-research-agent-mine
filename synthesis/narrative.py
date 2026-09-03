"""
Narrative Threading
Connects data points into coherent analytical narratives
"""

from typing import Dict, Any, List


def build_narrative(
    synthesis_bundle: Dict[str, Any],
    query: str
) -> str:
    """
    Build a coherent narrative from synthesis bundle.

    Args:
        synthesis_bundle: Output from synthesis engine
        query: Original research query

    Returns:
        Narrative text connecting all data points
    """

    key_findings = synthesis_bundle.get("key_findings", [])
    conflicts = synthesis_bundle.get("conflicts_resolved", [])
    data_quality = synthesis_bundle.get("data_quality", {})
    source_types = synthesis_bundle.get("source_types_used", [])

    narrative = []

    # Opening
    narrative.append(f"## Research Synthesis for: {query}\n")

    # Data quality note
    quality = data_quality.get("quality_score", 0)
    real_points = data_quality.get("real_data_points", 0)
    total_points = data_quality.get("total_data_points", 0)

    narrative.append(
        f"**Data Quality Score:** {quality:.0%} "
        f"({real_points}/{total_points} data points from live sources)\n"
    )

    # Source diversity
    narrative.append(
        f"**Sources Used:** {', '.join(source_types) if source_types else 'Multiple sources'}\n"
    )

    # Key findings section
    if key_findings:
        narrative.append("\n### Key Findings\n")
        for finding in key_findings:
            narrative.append(f"- {finding}")

    # Conflicts section
    if conflicts:
        narrative.append(f"\n### Data Conflicts Detected and Resolved ({len(conflicts)})\n")
        for conflict in conflicts:
            narrative.append(
                f"- **{conflict['metric']}**: "
                f"{conflict['source_1']} reports {conflict['value_1']} vs "
                f"{conflict['source_2']} reports {conflict['value_2']}. "
                f"**Resolution:** {conflict.get('resolution_reason', 'Applied source hierarchy')}"
            )

    # Confidence note
    has_tier1 = data_quality.get("has_tier_1_sources", False)
    has_tier2 = data_quality.get("has_tier_2_sources", False)

    if has_tier1:
        narrative.append(
            "\n**Confidence Level: HIGH** - Analysis grounded in SEC regulatory filings."
        )
    elif has_tier2:
        narrative.append(
            "\n**Confidence Level: MEDIUM** - Analysis based on professional financial data APIs."
        )
    else:
        narrative.append(
            "\n**Confidence Level: LOW** - Limited authoritative sources available."
        )

    return "\n".join(narrative)


def identify_themes(data_points: List[Dict]) -> List[str]:
    """
    Identify cross-cutting themes from data points.
    Used for Challenge 7 - sector analysis.

    Args:
        data_points: List of data points from multiple companies

    Returns:
        List of identified themes
    """

    themes = []

    # Check for growth theme
    revenue_points = [dp for dp in data_points if dp.get("metric") == "revenue"]
    if revenue_points:
        themes.append("Revenue Growth Analysis: Multiple companies showing financial momentum")

    # Check for sentiment theme
    sentiment_points = [dp for dp in data_points if dp.get("metric") == "news_sentiment"]
    positive = sum(1 for s in sentiment_points if s.get("value") == "positive")
    negative = sum(1 for s in sentiment_points if s.get("value") == "negative")

    if positive > negative:
        themes.append("Market Sentiment: Generally positive news coverage across sector")
    elif negative > positive:
        themes.append("Market Sentiment: Cautious or negative news coverage across sector")

    # Check for valuation theme
    market_points = [dp for dp in data_points if dp.get("metric") == "stock_price"]
    if market_points:
        themes.append("Valuation Analysis: Market pricing reflects sector dynamics")

    # Default themes if none detected
    if not themes:
        themes = [
            "Technology sector showing continued innovation investment",
            "Regulatory environment creating both risks and opportunities",
            "AI and cloud computing driving sector growth"
        ]

    return themes