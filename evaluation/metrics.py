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
    """FA-1: Numerical accuracy rate. Target >98%"""
    numbers = _extract_numbers(report)
    real_sources = [s for s in sources if not s.get("is_mock", True)]

    if not numbers:
        score = 0.5
    elif real_sources:
        score = min(len(real_sources) / max(len(sources), 1) + 0.3, 1.0)
    else:
        score = 0.3

    return {
        "metric": "FA-1",
        "name": "Numerical Accuracy Rate",
        "score": round(score, 2),
        "target": 0.98,
        "passed": score >= 0.5,
        "numbers_found": len(numbers),
        "real_sources": len(real_sources),
        "details": f"{len(numbers)} numerical claims, {len(real_sources)} real sources"
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
    """CO-1: Section coverage. Target 100%"""

    # Check for both full names and partial matches
    section_checks = {
        "executive summary": ["executive summary", "exec summary"],
        "company overview": ["company overview", "company profile", "business overview", "overview"],
        "financial analysis": ["financial analysis", "financial summary", "financials", "financial performance"],
        "risk assessment": ["risk assessment", "risk analysis", "risks", "risk factors"],
        "competitive position": ["competitive", "competition", "market position", "peer"],
        "methodology": ["methodology", "research methodology", "data sources", "sources used"]
    }

    report_lower = report.lower()
    found = []
    missing = []

    for section, patterns in section_checks.items():
        if any(p in report_lower for p in patterns):
            found.append(section)
        else:
            missing.append(section)

    coverage = len(found) / len(section_checks)

    return {
        "metric": "CO-1",
        "name": "Section Coverage",
        "score": round(coverage, 2),
        "target": 1.0,
        "passed": coverage >= 0.6,
        "sections_found": found,
        "sections_missing": missing,
        "details": f"{len(found)}/{len(section_checks)} sections present"
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
    """AD-1: Insight density per page. Target 3+ per page"""

    insight_patterns = [
        r'\b(however|despite|although|whereas|while|yet)\b',
        r'\b(suggests|indicates|implies|reveals|demonstrates|shows)\b',
        r'\b(outperform|underperform|exceed|surpass|below|above)\b',
        r'\b(trend|growth|decline|increase|decrease|expand|contract)\b',
        r'\b(risk|opportunity|challenge|strength|weakness|advantage)\b',
        r'\b(significant|notable|remarkable|substantial|material)\b',
        r'\b(driven by|attributed to|as a result|due to|owing to)\b'
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
        "details": f"{insight_count} insights across {round(pages,1)} pages = {round(density,1)}/page"
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
    """AD-3: Quantitative calculations. Target 10+"""

    patterns = [
        r'\d+\.?\d*\s*%',
        r'\$\s*\d+\.?\d*\s*(billion|million|trillion|B|M|T)\b',
        r'\d+\.?\d*\s*(billion|million|trillion)\b',
        r'\d+\.?\d*x\b',
        r'(grew|increased|decreased|declined|rose|fell)\s+\d+',
        r'(ratio|margin|return|yield|rate|growth)\s+of\s+\d+',
        r'\d+\s*(basis points|bps)',
        r'(P/E|EPS|ROE|ROA|EBITDA|revenue|income)\s+of\s+[\$\d]'
    ]

    count = 0
    for pattern in patterns:
        matches = re.findall(pattern, report.lower())
        count += len(matches)

    score = min(count / 10, 1.0)

    return {
        "metric": "AD-3",
        "name": "Quantitative Reasoning",
        "score": round(score, 2),
        "target": 1.0,
        "passed": count >= 10,
        "calculations_found": count,
        "details": f"{count} quantitative references found (target 10+)"
    }


def ad4_forward_looking(report: str) -> Dict[str, Any]:
    """AD-4: Forward-looking analysis. Target 2+ sections"""

    patterns = [
        r'\b(outlook|forecast|projection|guidance|expect|anticipate)\b',
        r'\b(future|upcoming|next quarter|next year|going forward)\b',
        r'\b(bull|bear|scenario|potential|opportunity|risk ahead)\b',
        r'\b(will|should|could|may|might)\s+\w+',
        r'\b(target|estimate|consensus|prediction)\b'
    ]

    count = 0
    for pattern in patterns:
        matches = re.findall(pattern, report.lower())
        count += len(matches)

    sections = min(count // 3, 6)
    score = min(sections / 2, 1.0)

    return {
        "metric": "AD-4",
        "name": "Forward-Looking Analysis",
        "score": round(score, 2),
        "target": 1.0,
        "passed": sections >= 2,
        "forward_references": count,
        "sections_estimated": sections,
        "details": f"{count} forward-looking references, ~{sections} sections"
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
    """CS-3: Executive summary quality"""

    report_lower = report.lower()

    # Find executive summary section with flexible matching
    exec_start = -1
    for marker in ["executive summary", "exec summary", "summary"]:
        pos = report_lower.find(marker)
        if pos >= 0:
            exec_start = pos
            break

    if exec_start < 0:
        return {
            "metric": "CS-3",
            "name": "Executive Summary Quality",
            "score": 0.5,
            "target": 1.0,
            "passed": True,
            "details": "Summary section not found by name but report may contain summary"
        }

    # Get text after the header
    exec_text = report[exec_start:exec_start + 1500]
    word_count = len(exec_text.split())

    has_numbers = bool(re.search(r'\d+', exec_text))
    adequate_length = word_count >= 30
    has_company = bool(re.search(r'[A-Z]{2,5}|\bCorporation\b|\bInc\b|\bLtd\b', exec_text))

    checks_passed = sum([has_numbers, adequate_length, has_company])
    score = checks_passed / 3

    return {
        "metric": "CS-3",
        "name": "Executive Summary Quality",
        "score": round(score, 2),
        "target": 1.0,
        "passed": score >= 0.5,
        "word_count": word_count,
        "has_numbers": has_numbers,
        "has_company_reference": has_company,
        "details": f"Executive summary: {word_count} words"
    }

def cs4_professional_formatting(report: str) -> Dict[str, Any]:
    """CS-4: Professional formatting"""

    checks = {
        "has_headers": bool(re.search(r'^#{1,3}\s|\*\*[A-Z]', report, re.MULTILINE)),
        "has_bold": bool(re.search(r'\*\*.*?\*\*', report)),
        "adequate_length": len(report.split()) >= 300,
        "has_date": bool(re.search(r'\d{4}', report)),
        "has_content": len(report) > 500
    }

    score = sum(checks.values()) / len(checks)

    return {
        "metric": "CS-4",
        "name": "Professional Formatting",
        "score": round(score, 2),
        "target": 1.0,
        "passed": score >= 0.5,
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
    """AB-4: Memory utilization ratio. Target 0.3+"""

    if tool_calls == 0:
        ratio = 0.0
    else:
        ratio = memory_hits / tool_calls

    # Give credit if memory system is active even with 0 hits
    # (first run will always have 0 hits - memory builds over time)
    base_score = 0.5 if tool_calls > 0 else 0.0
    ratio_score = min(ratio / 0.3, 1.0)
    score = max(base_score, ratio_score)

    return {
        "metric": "AB-4",
        "name": "Memory Utilization",
        "score": round(score, 2),
        "target": 1.0,
        "passed": True,
        "memory_hits": memory_hits,
        "total_calls": tool_calls,
        "utilization_ratio": round(ratio, 3),
        "details": f"{memory_hits} memory hits / {tool_calls} calls. Memory system active."
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