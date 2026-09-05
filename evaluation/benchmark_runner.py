"""
Benchmark Runner
Runs all 8 challenges and produces evaluation scorecard
"""

import os
import json
import time
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def run_evaluation(
    report: str,
    state: Dict[str, Any],
    challenge_num: int,
    query: str
) -> Dict[str, Any]:
    """
    Run full evaluation on a single challenge output.
    """

    from evaluation.metrics import run_all_metrics
    from evaluation.scorer import llm_judge_report

    print(f"\n[Evaluator] Running evaluation for Challenge {challenge_num}...")

    if "duration_seconds" not in state:
        state["duration_seconds"] = state.get("total_time", 0)

    metrics_result = run_all_metrics(report, state)
    sources = state.get("sources", [])
    llm_scores = llm_judge_report(report, query, sources)

    evaluation = {
        "challenge": challenge_num,
        "query": query,
        "automated_metrics": metrics_result,
        "llm_judge_scores": llm_scores,
        "overall_score": round(
            (metrics_result["overall_score"] * 0.6) +
            (llm_scores.get("analytical_depth", 0.7) * 0.15) +
            (llm_scores.get("narrative_quality", 0.7) * 0.15) +
            (llm_scores.get("actionability", 0.7) * 0.10),
            3
        ),
        "evaluated_at": datetime.now().isoformat()
    }

    print(f"[Evaluator] Challenge {challenge_num} score: {evaluation['overall_score']:.1%}")
    print(f"[Evaluator] Metrics passed: {metrics_result['metrics_passed']}/{metrics_result['total_metrics']}")

    return evaluation


def generate_evaluation_report(evaluations: List[Dict]) -> str:
    """
    Generate a comprehensive evaluation report for all challenges.
    """

    report = f"""# ARA-1 Evaluation Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Agent:** ARA-1 Autonomous Financial Research Agent
**Author:** Aman Singh

---

## Overall Performance Summary

"""

    if evaluations:
        avg_score = sum(e["overall_score"] for e in evaluations) / len(evaluations)
        total_passed = sum(
            e["automated_metrics"]["metrics_passed"]
            for e in evaluations
        )
        total_metrics = sum(
            e["automated_metrics"]["total_metrics"]
            for e in evaluations
        )

        report += f"**Average Score:** {avg_score:.1%}\n"
        report += f"**Total Metrics Passed:** {total_passed}/{total_metrics}\n"
        report += f"**Challenges Evaluated:** {len(evaluations)}/8\n\n"

        report += "| Challenge | Score | Metrics Passed | LLM Judge |\n"
        report += "|---|---|---|---|\n"

        for e in evaluations:
            ch = e["challenge"]
            score = e["overall_score"]
            passed = e["automated_metrics"]["metrics_passed"]
            total = e["automated_metrics"]["total_metrics"]
            llm = e["llm_judge_scores"].get("analytical_depth", 0)
            report += f"| C{ch} | {score:.1%} | {passed}/{total} | {llm:.1%} |\n"

    report += "\n---\n\n## Detailed Metric Results\n\n"

    for e in evaluations:
        ch = e["challenge"]
        report += f"### Challenge {ch}\n"
        report += f"**Query:** {e['query'][:100]}\n"
        report += f"**Overall Score:** {e['overall_score']:.1%}\n\n"

        metrics = e["automated_metrics"]["metrics"]

        report += "| Metric | Name | Score | Passed |\n"
        report += "|---|---|---|---|\n"

        for metric_id, result in metrics.items():
            score = result["score"]
            passed = "✓" if result["passed"] else "✗"
            name = result["name"]
            report += f"| {metric_id} | {name} | {score:.0%} | {passed} |\n"

        llm = e["llm_judge_scores"]
        report += f"\n**LLM Judge Feedback:** {llm.get('feedback', 'N/A')}\n\n"
        report += "---\n\n"

    report += """## Metric Definitions

### Category 1: Factual Accuracy
- FA-1: Numerical Accuracy Rate (target >98%)
- FA-2: Citation Accuracy (target 100%)
- FA-3: Temporal Accuracy (target 100%)
- FA-4: Entity Accuracy (target 100%)
- FA-5: Hallucination Rate (target 0)

### Category 2: Completeness
- CO-1: Section Coverage (target 100%)
- CO-2: Data Source Diversity (target 4+ types)
- CO-3: Temporal Coverage (target 3+ years)
- CO-4: Risk Factor Coverage (target 80%+)

### Category 3: Analytical Depth
- AD-1: Insight Density (target 3+ per page)
- AD-2: Cross-Source Synthesis (target 5+ per report)
- AD-3: Quantitative Reasoning (target 10+ calculations)
- AD-4: Forward-Looking Analysis (target 2+ sections)

### Category 4: Coherence and Structure
- CS-1: Logical Flow
- CS-2: Internal Consistency (target 0 contradictions)
- CS-3: Executive Summary Quality
- CS-4: Professional Formatting

### Category 5: Agent Behaviour
- AB-1: Tool Efficiency (target 70%+)
- AB-2: Error Recovery Rate (target 90%+)
- AB-3: Planning Quality
- AB-4: Memory Utilization (target 0.3+)
- AB-5: Latency (target <5 minutes)
"""

    return report