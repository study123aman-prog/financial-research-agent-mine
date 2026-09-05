"""
Evaluation Metrics
22 metrics across 5 categories for ARA-1 research quality assessment
"""

import re
import os
from typing import Dict, Any, List
from datetime import datetime


# ─── Category 1: Factual Accuracy (5 metrics) ────────────────────────────────

def fa1_numerical_accuracy(report: str, sources: List[Dict]) -> Dict[str, Any]:
    """
    FA-1: Percentage of numerical claims that match authoritative sources.
    Target: >98%
    """
    numbers_in_report = _extract_numbers(report)
    
    if not numbers_in_report:
        return {
            "metric": "FA-1",
            "name": "Numerical Accuracy Rate",
            "score": 1.0,
            "target": 0.98,
            "passed": True,
            "details": "No numerical claims found to verify"
        }

    # Check how many numbers appear to come from real sources
    real_source_count = sum(
        1 for s in sources
        if not s.get("is_mock", True)
    )

    accuracy = min(real_source_count / max(len(sources), 1), 1.0)

    return {
        "metric": "FA-1",
        "name": "Numerical Accuracy Rate",
        "score": round(accuracy, 2),
        "target": 0.98,
        "passed": accuracy >= 0.98,
        "numbers_found": len(numbers_in_report),
        "real_sources": real_source_count,
        "details": f"Found {len(numbers_in_report)} numerical claims, {real_source_count} real sources"
    }


def fa2_citation_accuracy(report: str, sources: List[Dict]) -> Dict[str, Any]:
    """
    FA-2: Percentage of cited sources that are real and accessible.
    Target: 100%
    """
    source_names = [s.get("name", "") for s in sources]
    cited_in_report = []

    for name in source_names:
        if name and name.lower() in report.lower():
            cited_in_report.append(name)

    mock_sources = [s for s in sources if s.get("is_mock", False)]
    real_sources = [s for s in sources if not s.get("is_mock", False)]

    accuracy = len(real_sources) / max(len(sources), 1)

    return {
        "metric": "FA-2",
        "name": "Citation Accuracy",
        "score": round(accuracy, 2),
        "target": 1.0,
        "passed": accuracy >= 0.8,
        "total_sources": len(sources),
        "real_sources": len(real_sources),
        "mock_sources": len(mock_sources),
        "cited_in_report": cited_in_report,
        "details": f"{len(real_sources)}/{len(sources)} sources are real"
    }


def fa3_temporal_accuracy(report: str) -> Dict[str, Any]:
    """
    FA-3: Whether report correctly identifies time periods.
    Target: 100%
    """
    year_pattern = r'\b(20\d{2})\b'
    years_found = re.findall(year_pattern, report)

    current_year = datetime.now().year
    future_years = [y for y in years_found if int(y) > current_year]
    valid_years = [y for y in years_found if int(y) <= current_year]

    has_temporal_context = len(valid_years) > 0
    no_future_dates = len(future_years) == 0

    score = 1.0 if (has_temporal_context and no_future_dates) else 0.5

    return {
        "metric": "FA-3",
        "name": "Temporal Accuracy",
        "score": score,
        "target": 1.0,
        "passed": score >= 0.8,
        "years_referenced": list(set(valid_years)),
        "future_years_found": future_years,
        "details": f"Found {len(valid_years)} valid year references, {len(future_years)} future dates"
    }


def fa4_entity_accuracy(report: str, expected_companies: List[str]) -> Dict[str, Any]:
    """
    FA-4: Whether company names and tickers are correct.
    Target: 100%
    """
    if not expected_companies:
        return {
            "metric": "FA-4",
            "name": "Entity Accuracy",
            "score": 1.0,
            "target": 1.0,
            "passed": True,
            "details": "No expected companies to verify"
        }

    found = []
    missing = []

    for company in expected_companies:
        if company.upper() in report.upper():
            found.append(company)
        else:
            missing.append(company)

    accuracy = len(found) / len(expected_companies)

    return {
        "metric": "FA-4",
        "name": "Entity Accuracy",
        "score": round(accuracy, 2),
        "target": 1.0,
        "passed": accuracy >= 0.8,
        "entities_found": found,
        "entities_missing": missing,
        "details": f"{len(found)}/{len(expected_companies)} expected entities found in report"
    }


def fa5_hallucination_rate(report: str, gathered_data: Dict) -> Dict[str, Any]:
    """
    FA-5: Number of claims not traceable to retrieved sources.
    Target: 0
    """
    numbers_in_report = _extract_numbers(report)

    source_text = str(gathered_data)
    traceable = []
    untraced = []

    for num in numbers_in_report:
        clean_num = re.sub(r'[,$%]', '', num).strip()
        if clean_num and (clean_num in source_text or len(clean_num) < 3):
            traceable.append(num)
        else:
            untraced.append(num)

    hallucination_rate = len(untraced) / max(len(numbers_in_report), 1)
    score = 1.0 - hallucination_rate

    return {
        "metric": "FA-5",
        "name": "Hallucination Rate",
        "score": round(score, 2),
        "target": 1.0,
        "passed": hallucination_rate < 0.02,
        "total_claims": len(numbers_in_report),
        "untraced_claims": len(untraced),
        "hallucination_rate": round(hallucination_rate, 3),
        "details": f"{len(untraced)} potentially unverified numerical claims"
    }


# ─── Category 2: Completeness (4 metrics) ────────────────────────────────────

def co1_section_coverage(report: str) -> Dict[str, Any]:
    """
    CO-1: Whether report includes all required sections.
    Target: 100%
    """
    required_sections = [
        "executive summary",
        "company overview",
        "financial analysis",
        "risk assessment",
        "competitive position",
        "methodology"
    ]

    report_lower = report.lower()
    found = [s for s in required_sections if s in report_lower]
    missing = [s for s in required_sections if s not in report_lower]

    coverage = len(found) / len(required_sections)

    return {
        "metric": "CO-1",
        "name": "Section Coverage",
        "score": round(coverage, 2),
        "target": 1.0,
        "passed": coverage >= 0.8,
        "sections_found": found,
        "sections_missing": missing,
        "details": f"{len(found)}/{len(required_sections)} required sections present"
    }


def co2_source_diversity(sources: List[Dict]) -> Dict[str, Any]:
    """
    CO-2: Number of distinct source types used.
    Target: >=4 source types
    """
    source_types = list(set([
        s.get("type", s.get("name", "unknown"))
        for s in sources
    ]))

    count = len(source_types)
    score = min(count / 4, 1.0)

    return {
        "metric": "CO-2",
        "name": "Data Source Diversity",
        "score": round(score, 2),
        "target": 1.0,
        "passed": count >= 4,
        "source_count": count,
        "source_types": source_types,
        "details": f"{count} distinct source types used (target: 4+)"
    }


def co3_temporal_coverage(report: str) -> Dict[str, Any]:
    """
    CO-3: Whether report covers 3+ years of historical data.
    Target: >=3 years
    """
    year_pattern = r'\b(20\d{2})\b'
    years = list(set(re.findall(year_pattern, report)))
    years = [int(y) for y in years if int(y) <= datetime.now().year]

    if not years:
        return {
            "metric": "CO-3",
            "name": "Temporal Coverage",
            "score": 0.0,
            "target": 1.0,
            "passed": False,
            "details": "No year references found in report"
        }

    year_range = max(years) - min(years) + 1
    score = min(year_range / 3, 1.0)

    return {
        "metric": "CO-3",
        "name": "Temporal Coverage",
        "score": round(score, 2),
        "target": 1.0,
        "passed": year_range >= 3,
        "years_found": sorted(years),
        "year_range": year_range,
        "details": f"Covers {year_range} years from {min(years)} to {max(years)}"
    }


def co4_risk_factor_coverage(report: str) -> Dict[str, Any]:
    """
    CO-4: Percentage of material risk factors identified.
    Target: >=80%
    """
    risk_keywords = [
        "competition", "regulatory", "market", "operational",
        "financial", "technology", "cybersecurity", "supply chain",
        "geopolitical", "currency", "interest rate", "litigation"
    ]

    report_lower = report.lower()
    found_risks = [r for r in risk_keywords if r in report_lower]
    coverage = len(found_risks) / len(risk_keywords)

    return {
        "metric": "CO-4",
        "name": "Risk Factor Coverage",
        "score": round(coverage, 2),
        "target": 0.8,
        "passed": coverage >= 0.8,
        "risks_identified": found_risks,
        "total_risk_categories": len(risk_keywords),
        "details": f"{len(found_risks)}/{len(risk_keywords)} risk categories covered"
    }


# ─── Category 3: Analytical Depth (4 metrics) ────────────────────────────────

def ad1_insight_density(report: str) -> Dict[str, Any]:
    """
    AD-1: Non-obvious analytical observations per page.
    Target: >=3 per page
    """
    insight_patterns = [
        r'\b(however|despite|although|whereas|contrary|paradox)\b',
        r'\b(suggests|indicates|implies|reveals|demonstrates)\b',
        r'\b(outperform|underperform|exceed|below|above expectation)\b',
        r'\b(trend|pattern|trajectory|momentum|acceleration)\b',
        r'\b(risk|opportunity|threat|strength|weakness)\b'
    ]

    insight_count = 0
    for pattern in insight_patterns:
        matches = re.findall(pattern, report.lower())
        insight_count += len(matches)

    word_count = len(report.split())
    pages = max(word_count / 500, 1)
    density = insight_count / pages
    score = min(density / 3, 1.0)

    return {
        "metric": "AD-1",
        "name": "Insight Density",
        "score": round(score, 2),
        "target": 1.0,
        "passed": density >= 3,
        "insight_count": insight_count,
        "estimated_pages": round(pages, 1),
        "density_per_page": round(density, 1),
        "details": f"{insight_count} analytical insights across {round(pages,1)} pages"
    }


def ad2_cross_source_synthesis(report: str, sources: List[Dict]) -> Dict[str, Any]:
    """
    AD-2: Instances where report connects information from multiple sources.
    Target: >=5 per report
    """
    synthesis_patterns = [
        r'\b(confirms|corroborates|aligns with|consistent with)\b',
        r'\b(contradicts|conflicts with|disagrees|inconsistent)\b',
        r'\b(according to.*and|both.*show|across.*sources)\b',
        r'\b(while.*reports|although.*indicates|despite.*shows)\b'
    ]

    synthesis_count = 0
    for pattern in synthesis_patterns:
        matches = re.findall(pattern, report.lower())
        synthesis_count += len(matches)

    score = min(synthesis_count / 5, 1.0)

    return {
        "metric": "AD-2",
        "name": "Cross-Source Synthesis",
        "score": round(score, 2),
        "target": 1.0,
        "passed": synthesis_count >= 5,
        "synthesis_instances": synthesis_count,
        "details": f"{synthesis_count} cross-source synthesis instances (target: 5+)"
    }


def ad3_quantitative_reasoning(report: str) -> Dict[str, Any]:
    """
    AD-3: Original calculations derived from retrieved data.
    Target: >=10 calculations
    """
    calc_patterns = [
        r'\d+\.?\d*\s*%',
        r'\$\d+\.?\d*\s*(billion|million|B|M)',
        r'\d+\.?\d*x\b',
        r'(grew|increased|decreased|declined)\s+by\s+\d+',
        r'(ratio|margin|return|yield)\s+of\s+\d+'
    ]

    calc_count = 0
    for pattern in calc_patterns:
        matches = re.findall(pattern, report.lower())
        calc_count += len(matches)

    score = min(calc_count / 10, 1.0)

    return {
        "metric": "AD-3",
        "name": "Quantitative Reasoning",
        "score": round(score, 2),
        "target": 1.0,
        "passed": calc_count >= 10,
        "calculations_found": calc_count,
        "details": f"{calc_count} quantitative calculations found (target: 10+)"
    }


def ad4_forward_looking(report: str) -> Dict[str, Any]:
    """
    AD-4: Whether report includes forward-looking analysis.
    Target: >=2 forward-looking sections
    """
    forward_patterns = [
        r'\b(outlook|forecast|projection|guidance|expect)\b',
        r'\b(future|upcoming|anticipated|planned|strategy)\b',
        r'\b(growth opportunity|risk ahead|next quarter|next year)\b',
        r'\b(bull case|bear case|scenario|potential)\b'
    ]

    forward_count = 0
    for pattern in forward_patterns:
        matches = re.findall(pattern, report.lower())
        forward_count += len(matches)

    sections_detected = min(forward_count // 3, 5)
    score = min(sections_detected / 2, 1.0)

    return {
        "metric": "AD-4",
        "name": "Forward-Looking Analysis",
        "score": round(score, 2),
        "target": 1.0,
        "passed": sections_detected >= 2,
        "forward_references": forward_count,
        "sections_estimated": sections_detected,
        "details": f"{forward_count} forward-looking references across ~{sections_detected} sections"
    }


# ─── Category 4: Coherence and Structure (4 metrics) ─────────────────────────

def cs1_logical_flow(report: str) -> Dict[str, Any]:
    """
    CS-1: Whether sections follow logical progression.
    Assessed by checking section order.
    """
    section_order = [
        "executive summary",
        "company overview",
        "financial",
        "risk",
        "competitive",
        "methodology"
    ]

    report_lower = report.lower()
    positions = []

    for section in section_order:
        pos = report_lower.find(section)
        if pos >= 0:
            positions.append(pos)

    if len(positions) < 2:
        score = 0.5
    else:
        in_order = all(
            positions[i] < positions[i+1]
            for i in range(len(positions)-1)
        )
        score = 1.0 if in_order else 0.5

    return {
        "metric": "CS-1",
        "name": "Logical Flow",
        "score": score,
        "target": 1.0,
        "passed": score >= 0.8,
        "sections_found": len(positions),
        "details": f"Sections appear in {'correct' if score == 1.0 else 'incorrect'} order"
    }


def cs2_internal_consistency(report: str) -> Dict[str, Any]:
    """
    CS-2: Whether report contains self-contradictions.
    Target: 0 contradictions
    """
    contradiction_patterns = [
        (r'strong growth', r'declining revenue'),
        (r'profitable', r'net loss'),
        (r'market leader', r'losing market share'),
        (r'low debt', r'highly leveraged'),
        (r'positive outlook', r'negative guidance')
    ]

    contradictions = []
    report_lower = report.lower()

    for pos_pattern, neg_pattern in contradiction_patterns:
        has_pos = bool(re.search(pos_pattern, report_lower))
        has_neg = bool(re.search(neg_pattern, report_lower))
        if has_pos and has_neg:
            contradictions.append(f"{pos_pattern} vs {neg_pattern}")

    score = 1.0 if not contradictions else max(0.5 - len(contradictions) * 0.1, 0)

    return {
        "metric": "CS-2",
        "name": "Internal Consistency",
        "score": round(score, 2),
        "target": 1.0,
        "passed": len(contradictions) == 0,
        "contradictions_found": contradictions,
        "details": f"{len(contradictions)} potential contradictions detected"
    }


def cs3_executive_summary_quality(report: str) -> Dict[str, Any]:
    """
    CS-3: Whether executive summary captures key findings.
    """
    exec_pattern = r'(?i)executive summary(.*?)(?=##|\Z)'
    exec_match = re.search(exec_pattern, report, re.DOTALL)

    if not exec_match:
        return {
            "metric": "CS-3",
            "name": "Executive Summary Quality",
            "score": 0.0,
            "target": 1.0,
            "passed": False,
            "details": "No executive summary found"
        }

    exec_text = exec_match.group(1).strip()
    word_count = len(exec_text.split())

    has_numbers = bool(re.search(r'\d+', exec_text))
    adequate_length = 50 <= word_count <= 300
    has_company = bool(re.search(r'[A-Z]{2,5}|Corporation|Inc|Ltd', exec_text))

    score = sum([has_numbers, adequate_length, has_company]) / 3

    return {
        "metric": "CS-3",
        "name": "Executive Summary Quality",
        "score": round(score, 2),
        "target": 1.0,
        "passed": score >= 0.6,
        "word_count": word_count,
        "has_numbers": has_numbers,
        "has_company_reference": has_company,
        "details": f"Executive summary: {word_count} words, includes numbers: {has_numbers}"
    }


def cs4_professional_formatting(report: str) -> Dict[str, Any]:
    """
    CS-4: Whether report follows professional formatting standards.
    """
    checks = {
        "has_headers": bool(re.search(r'^#{1,3}\s', report, re.MULTILINE)),
        "has_bold": bool(re.search(r'\*\*.*?\*\*', report)),
        "adequate_length": len(report.split()) >= 500,
        "has_date": bool(re.search(r'\d{4}-\d{2}-\d{2}', report)),
        "has_source_attribution": any(
            term in report.lower()
            for term in ["source:", "[source", "according to", "per "]
        )
    }

    score = sum(checks.values()) / len(checks)

    return {
        "metric": "CS-4",
        "name": "Professional Formatting",
        "score": round(score, 2),
        "target": 1.0,
        "passed": score >= 0.6,
        "checks": checks,
        "details": f"{sum(checks.values())}/{len(checks)} formatting checks passed"
    }


# ─── Category 5: Agent Behaviour (5 metrics) ─────────────────────────────────

def ab1_tool_efficiency(tool_calls: int, sources: List[Dict]) -> Dict[str, Any]:
    """
    AB-1: Ratio of useful tool calls to total tool calls.
    Target: >=70%
    """
    useful_calls = len([s for s in sources if s.get("name")])
    efficiency = useful_calls / max(tool_calls, 1)
    score = min(efficiency / 0.7, 1.0)

    return {
        "metric": "AB-1",
        "name": "Tool Efficiency",
        "score": round(score, 2),
        "target": 1.0,
        "passed": efficiency >= 0.7,
        "total_calls": tool_calls,
        "useful_calls": useful_calls,
        "efficiency_rate": round(efficiency, 2),
        "details": f"{useful_calls}/{tool_calls} tool calls were useful ({efficiency:.0%})"
    }


def ab2_error_recovery_rate(errors: List[Dict], fallbacks: List[str]) -> Dict[str, Any]:
    """
    AB-2: Percentage of errors successfully recovered from.
    Target: >=90%
    """
    total_errors = len(errors)
    recovered = len(fallbacks)

    if total_errors == 0:
        recovery_rate = 1.0
    else:
        recovery_rate = min(recovered / total_errors, 1.0)

    score = min(recovery_rate / 0.9, 1.0)

    return {
        "metric": "AB-2",
        "name": "Error Recovery Rate",
        "score": round(score, 2),
        "target": 1.0,
        "passed": recovery_rate >= 0.9 or total_errors == 0,
        "total_errors": total_errors,
        "recovered": recovered,
        "recovery_rate": round(recovery_rate, 2),
        "details": f"Recovered from {recovered}/{total_errors} errors"
    }


def ab3_planning_quality(plan: List[str]) -> Dict[str, Any]:
    """
    AB-3: Whether agent plan covers necessary research steps.
    """
    good_plan_keywords = [
        "profile", "financial", "sec", "news",
        "price", "peer", "earnings", "ratio"
    ]

    plan_text = " ".join(plan).lower()
    covered = [k for k in good_plan_keywords if k in plan_text]

    coverage = len(covered) / len(good_plan_keywords)
    has_enough_steps = 5 <= len(plan) <= 10
    score = (coverage * 0.7) + (0.3 if has_enough_steps else 0)

    return {
        "metric": "AB-3",
        "name": "Planning Quality",
        "score": round(score, 2),
        "target": 1.0,
        "passed": score >= 0.6,
        "plan_steps": len(plan),
        "keywords_covered": covered,
        "details": f"{len(plan)} step plan covering {len(covered)}/{len(good_plan_keywords)} key areas"
    }


def ab4_memory_utilization(memory_hits: int, tool_calls: int) -> Dict[str, Any]:
    """
    AB-4: Ratio of memory hits to total API calls.
    Target: >=0.3
    Note: Correct formula is memory_hits / total_api_calls (division not multiplication)
    """
    if tool_calls == 0:
        ratio = 0.0
    else:
        ratio = memory_hits / tool_calls

    score = min(ratio / 0.3, 1.0)

    return {
        "metric": "AB-4",
        "name": "Memory Utilization",
        "score": round(score, 2),
        "target": 1.0,
        "passed": ratio >= 0.3 or memory_hits > 0,
        "memory_hits": memory_hits,
        "total_calls": tool_calls,
        "utilization_ratio": round(ratio, 3),
        "details": f"{memory_hits} memory hits out of {tool_calls} total calls"
    }


def ab5_latency(duration_seconds: float, query_type: str = "single") -> Dict[str, Any]:
    """
    AB-5: Total time from query to report delivery.
    Target: <5 minutes for single company
    """
    target_seconds = 300

    score = max(0, 1.0 - (duration_seconds / target_seconds))
    passed = duration_seconds < target_seconds

    return {
        "metric": "AB-5",
        "name": "Latency",
        "score": round(score, 2),
        "target": 1.0,
        "passed": passed,
        "duration_seconds": round(duration_seconds, 1),
        "target_seconds": target_seconds,
        "details": f"Completed in {duration_seconds:.0f}s (target: <{target_seconds}s)"
    }


# ─── Helper Functions ─────────────────────────────────────────────────────────

def _extract_numbers(text: str) -> List[str]:
    """Extract numerical values from text"""
    pattern = r'\$?[\d,]+\.?\d*\s*(?:billion|million|thousand|percent|%|B|M|K)?'
    return re.findall(pattern, text, re.IGNORECASE)


# ─── Run All Metrics ──────────────────────────────────────────────────────────

def run_all_metrics(
    report: str,
    state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run all 22 metrics on a research report.

    Args:
        report: Final report text
        state: Agent final state

    Returns:
        Complete evaluation results
    """

    sources = state.get("sources", [])
    companies = state.get("companies", [])
    errors = state.get("errors", [])
    fallbacks = state.get("fallbacks_used", [])
    tool_calls = state.get("tool_calls", 0)
    memory_hits = state.get("memory_hits", 0)
    plan = state.get("plan", [])
    gathered_data = state.get("gathered_data", {})
    duration = state.get("duration_seconds", 0)

    results = {}

    # Category 1: Factual Accuracy
    results["FA-1"] = fa1_numerical_accuracy(report, sources)
    results["FA-2"] = fa2_citation_accuracy(report, sources)
    results["FA-3"] = fa3_temporal_accuracy(report)
    results["FA-4"] = fa4_entity_accuracy(report, companies)
    results["FA-5"] = fa5_hallucination_rate(report, gathered_data)

    # Category 2: Completeness
    results["CO-1"] = co1_section_coverage(report)
    results["CO-2"] = co2_source_diversity(sources)
    results["CO-3"] = co3_temporal_coverage(report)
    results["CO-4"] = co4_risk_factor_coverage(report)

    # Category 3: Analytical Depth
    results["AD-1"] = ad1_insight_density(report)
    results["AD-2"] = ad2_cross_source_synthesis(report, sources)
    results["AD-3"] = ad3_quantitative_reasoning(report)
    results["AD-4"] = ad4_forward_looking(report)

    # Category 4: Coherence and Structure
    results["CS-1"] = cs1_logical_flow(report)
    results["CS-2"] = cs2_internal_consistency(report)
    results["CS-3"] = cs3_executive_summary_quality(report)
    results["CS-4"] = cs4_professional_formatting(report)

    # Category 5: Agent Behaviour
    results["AB-1"] = ab1_tool_efficiency(tool_calls, sources)
    results["AB-2"] = ab2_error_recovery_rate(errors, fallbacks)
    results["AB-3"] = ab3_planning_quality(plan)
    results["AB-4"] = ab4_memory_utilization(memory_hits, tool_calls)
    results["AB-5"] = ab5_latency(duration)

    # Calculate overall score
    scores = [r["score"] for r in results.values()]
    overall = sum(scores) / len(scores)
    passed = sum(1 for r in results.values() if r["passed"])

    return {
        "metrics": results,
        "overall_score": round(overall, 3),
        "metrics_passed": passed,
        "total_metrics": len(results),
        "pass_rate": round(passed / len(results), 2),
        "evaluated_at": datetime.now().isoformat()
    }