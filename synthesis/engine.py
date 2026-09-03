"""
Synthesis Engine
Combines research findings from multiple sources into coherent analysis
"""

from typing import Dict, Any, List
from datetime import datetime


# Source reliability tiers
SOURCE_TIERS = {
    "SEC EDGAR": 1,
    "sec_filing_search": 1,
    "Alpha Vantage": 2,
    "financial_data_api": 2,
    "Yahoo Finance": 2,
    "stock_price": 2,
    "company_profile": 2,
    "peer_comparison": 2,
    "earnings_transcript": 3,
    "Earnings Tool": 3,
    "NewsAPI": 4,
    "news_sentiment": 4,
    "Reuters": 4,
    "Bloomberg": 4,
    "Financial Times": 4,
    "web_search": 4,
    "DuckDuckGo": 4,
    "Social Media": 5
}


def synthesize_findings(
    gathered_data: Dict[str, Any],
    sources: List[Dict],
    query: str
) -> Dict[str, Any]:
    """
    Synthesize all research findings into a coherent analysis.

    Args:
        gathered_data: All tool results keyed by step
        sources: List of sources used
        query: Original research query

    Returns:
        Synthesis bundle with findings, conflicts, and narrative
    """

    # Step 1: Extract all data points
    data_points = _extract_data_points(gathered_data)

    # Step 2: Detect conflicts
    conflicts = _detect_conflicts(data_points)

    # Step 3: Resolve conflicts using source hierarchy
    resolved = _resolve_conflicts(conflicts, data_points)

    # Step 4: Calculate source diversity
    source_types = list(set([s.get("type", "unknown") for s in sources]))

    # Step 5: Build synthesis bundle
    synthesis = {
        "query": query,
        "data_points": data_points,
        "conflicts_detected": conflicts,
        "conflicts_resolved": resolved,
        "source_types_used": source_types,
        "source_diversity_score": len(source_types),
        "total_sources": len(sources),
        "synthesis_timestamp": datetime.now().isoformat(),
        "key_findings": _extract_key_findings(data_points),
        "data_quality": _assess_data_quality(data_points, sources)
    }

    return synthesis


def _extract_data_points(gathered_data: Dict[str, Any]) -> List[Dict]:
    """Extract individual data points from all tool results"""

    data_points = []

    for step_key, step_data in gathered_data.items():
        result = step_data.get("result", {})
        step = step_data.get("step", "")

        if not result or not isinstance(result, dict):
            continue

        source = result.get("source", "unknown")
        tier = SOURCE_TIERS.get(source, 4)
        is_mock = result.get("is_mock", False)

        # Extract key metrics based on data type
        if "totalRevenue" in str(result) or "reports" in result:
            reports = result.get("reports", [])
            if reports and isinstance(reports, list):
                for report in reports[:2]:
                    if isinstance(report, dict):
                        data_points.append({
                            "type": "financial",
                            "source": source,
                            "tier": tier,
                            "is_mock": is_mock,
                            "metric": "revenue",
                            "value": report.get("totalRevenue", "N/A"),
                            "period": report.get("fiscalDateEnding", "N/A"),
                            "step": step
                        })

        if "current_price" in result:
            data_points.append({
                "type": "market",
                "source": source,
                "tier": tier,
                "is_mock": is_mock,
                "metric": "stock_price",
                "value": result.get("current_price", "N/A"),
                "pe_ratio": result.get("pe_ratio", "N/A"),
                "market_cap": result.get("market_cap", "N/A"),
                "step": step
            })

        if "overall_sentiment" in result:
            data_points.append({
                "type": "sentiment",
                "source": source,
                "tier": tier,
                "is_mock": is_mock,
                "metric": "news_sentiment",
                "value": result.get("overall_sentiment", "neutral"),
                "score": result.get("average_sentiment", 0),
                "article_count": result.get("total_articles", 0),
                "step": step
            })

        if "filing_type" in result:
            data_points.append({
                "type": "regulatory",
                "source": source,
                "tier": tier,
                "is_mock": is_mock,
                "metric": "sec_filing",
                "value": result.get("filing_type", "N/A"),
                "filed_date": result.get("filed_date", "N/A"),
                "step": step
            })

        if "company_name" in result and "sector" in result:
            data_points.append({
                "type": "profile",
                "source": source,
                "tier": tier,
                "is_mock": is_mock,
                "metric": "company_info",
                "value": result.get("company_name", "N/A"),
                "sector": result.get("sector", "N/A"),
                "industry": result.get("industry", "N/A"),
                "step": step
            })

    return data_points


def _detect_conflicts(data_points: List[Dict]) -> List[Dict]:
    """Detect conflicts between data points from different sources"""

    conflicts = []

    # Group by metric type
    metric_groups: Dict[str, List] = {}
    for dp in data_points:
        metric = dp.get("metric", "unknown")
        if metric not in metric_groups:
            metric_groups[metric] = []
        metric_groups[metric].append(dp)

    # Check for conflicts within each metric group
    for metric, points in metric_groups.items():
        if len(points) < 2:
            continue

        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                p1 = points[i]
                p2 = points[j]

                # Skip if same source
                if p1["source"] == p2["source"]:
                    continue

                # Check for numerical conflicts
                v1 = str(p1.get("value", ""))
                v2 = str(p2.get("value", ""))

                if _values_conflict(v1, v2):
                    conflicts.append({
                        "metric": metric,
                        "source_1": p1["source"],
                        "value_1": v1,
                        "tier_1": p1["tier"],
                        "source_2": p2["source"],
                        "value_2": v2,
                        "tier_2": p2["tier"],
                        "resolution": "pending"
                    })

    return conflicts


def _values_conflict(v1: str, v2: str) -> bool:
    """Check if two values conflict significantly"""

    try:
        # Extract numbers from values
        import re
        nums1 = re.findall(r'[\d.]+', v1.replace(",", ""))
        nums2 = re.findall(r'[\d.]+', v2.replace(",", ""))

        if nums1 and nums2:
            n1 = float(nums1[0])
            n2 = float(nums2[0])

            if n1 == 0 or n2 == 0:
                return False

            # Conflict if values differ by more than 5%
            diff_pct = abs(n1 - n2) / max(n1, n2) * 100
            return diff_pct > 5

    except Exception:
        pass

    return False


def _resolve_conflicts(
    conflicts: List[Dict],
    data_points: List[Dict]
) -> List[Dict]:
    """Resolve conflicts using source reliability hierarchy"""

    resolved = []

    for conflict in conflicts:
        tier1 = conflict["tier_1"]
        tier2 = conflict["tier_2"]

        if tier1 < tier2:
            preferred = conflict["source_1"]
            preferred_value = conflict["value_1"]
            reason = f"Tier {tier1} source is more reliable than Tier {tier2}"
        elif tier2 < tier1:
            preferred = conflict["source_2"]
            preferred_value = conflict["value_2"]
            reason = f"Tier {tier2} source is more reliable than Tier {tier1}"
        else:
            preferred = conflict["source_1"]
            preferred_value = conflict["value_1"]
            reason = "Equal tier sources - using first source"

        resolved.append({
            **conflict,
            "resolution": "resolved",
            "preferred_source": preferred,
            "preferred_value": preferred_value,
            "resolution_reason": reason
        })

    return resolved


def _extract_key_findings(data_points: List[Dict]) -> List[str]:
    """Extract the most important findings"""

    findings = []

    for dp in data_points:
        if dp.get("is_mock"):
            continue

        metric = dp.get("metric", "")
        source = dp.get("source", "")
        value = dp.get("value", "")

        if metric == "stock_price":
            pe = dp.get("pe_ratio", "N/A")
            findings.append(
                f"Stock price: ${value} with P/E ratio of {pe} [Source: {source}]"
            )

        elif metric == "revenue":
            period = dp.get("period", "N/A")
            findings.append(
                f"Revenue: {value} for period {period} [Source: {source}]"
            )

        elif metric == "news_sentiment":
            score = dp.get("score", 0)
            count = dp.get("article_count", 0)
            findings.append(
                f"News sentiment: {value} (score: {score:.2f}) from {count} articles [Source: {source}]"
            )

        elif metric == "sec_filing":
            filed = dp.get("filed_date", "N/A")
            findings.append(
                f"SEC {value} filing dated {filed} [Source: {source}]"
            )

    return findings[:10]


def _assess_data_quality(
    data_points: List[Dict],
    sources: List[Dict]
) -> Dict[str, Any]:
    """Assess overall data quality"""

    total = len(data_points)
    mock_count = sum(1 for dp in data_points if dp.get("is_mock"))
    real_count = total - mock_count

    tier_1_count = sum(1 for dp in data_points if dp.get("tier") == 1)
    tier_2_count = sum(1 for dp in data_points if dp.get("tier") == 2)

    quality_score = 0.0
    if total > 0:
        quality_score = (real_count / total) * 0.6
        quality_score += min(len(sources) / 4, 1.0) * 0.2
        quality_score += min((tier_1_count + tier_2_count) / max(total, 1), 1.0) * 0.2

    return {
        "total_data_points": total,
        "real_data_points": real_count,
        "mock_data_points": mock_count,
        "quality_score": round(quality_score, 2),
        "has_tier_1_sources": tier_1_count > 0,
        "has_tier_2_sources": tier_2_count > 0,
        "source_diversity": len(set([s.get("type", "") for s in sources]))
    }