"""
ARA-1 Main Entry Point
Run all 8 research challenges
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

CHALLENGES = {
    1: {
        "query": "Create a comprehensive profile of Microsoft Corporation including business overview, financial summary, key executives, and recent developments.",
        "file": "results/challenge_1.md"
    },
    2: {
        "query": "Analyze Apple Inc.'s most recent quarterly earnings. Compare actual results to consensus estimates and identify key takeaways from the earnings call.",
        "file": "results/challenge_2.md"
    },
    3: {
        "query": "Produce a comprehensive risk assessment for Tesla Inc. covering financial risks, operational risks, regulatory risks, and competitive risks.",
        "file": "results/challenge_3.md"
    },
    4: {
        "query": "Compare the cloud computing divisions of Amazon (AWS), Microsoft (Azure), and Google (GCP). Analyze revenue growth, market share, margins, and competitive advantages.",
        "file": "results/challenge_4.md"
    },
    5: {
        "query": "Research Palantir Technologies. Note: Recent news reports suggest the company is struggling, but their financial statements show strong growth. Investigate and explain the apparent contradiction.",
        "file": "results/challenge_5.md"
    },
    6: {
        "query": "What's happening with the banks?",
        "file": "results/challenge_6.md"
    },
    7: {
        "query": "Based on the companies you have already researched, what themes emerge across the technology sector? Identify cross-cutting risks and opportunities.",
        "file": "results/challenge_7.md"
    },
    8: {
        "query": "Produce a complete investment research report on NVIDIA Corporation. Note: The financial data API and SEC filing search tools are currently experiencing intermittent failures.",
        "file": "results/challenge_8.md"
    }
}


def run_challenge(number: int):
    """Run a specific challenge by number"""

    if number not in CHALLENGES:
        print(f"Challenge {number} not found. Choose 1-8.")
        return

    challenge = CHALLENGES[number]
    failure_rate = 0.5 if number == 8 else 0.0

    if failure_rate > 0:
        print(f"Challenge 8: Failure simulation at {failure_rate*100:.0f}%")

    from agent.core import run_agent
    import time

    start = time.time()
    result = run_agent(challenge["query"], failure_rate=failure_rate)
    duration = time.time() - start

    result["duration_seconds"] = duration

    report = result.get("final_report", "No report generated")
    if isinstance(report, list):
        report = report[0].text if hasattr(report[0], 'text') else str(report[0])
    report = str(report)

    os.makedirs("results", exist_ok=True)

    with open(challenge["file"], "w", encoding="utf-8") as f:
        f.write(report)

    # Run evaluation
    try:
        from evaluation.benchmark_runner import run_evaluation
        evaluation = run_evaluation(report, result, number, challenge["query"])

        eval_file = challenge["file"].replace(".md", "_eval.json")
        with open(eval_file, "w") as f:
            import json
            json.dump(evaluation, f, indent=2)

        print(f"\nEvaluation Score: {evaluation['overall_score']:.1%}")
        print(f"Metrics Passed: {evaluation['automated_metrics']['metrics_passed']}/22")

    except Exception as e:
        print(f"Evaluation error: {e}")

    print(f"\n{'='*60}")
    print(f"REPORT SAVED TO {challenge['file']}")
    print(f"{'='*60}")
    print(f"\nFirst 300 characters:")
    print(report[:300])

def run_all_evaluations():
    """Run all 8 challenges and generate master evaluation report"""

    import json
    from evaluation.benchmark_runner import generate_evaluation_report

    evaluations = []

    for i in range(1, 9):
        eval_file = CHALLENGES[i]["file"].replace(".md", "_eval.json")
        if os.path.exists(eval_file):
            with open(eval_file) as f:
                evaluations.append(json.load(f))

    if not evaluations:
        print("No evaluation files found. Run challenges first.")
        return

    report = generate_evaluation_report(evaluations)

    with open("results/evaluation_report.md", "w") as f:
        f.write(report)

    print(f"Evaluation report saved to results/evaluation_report.md")
    print(f"Challenges evaluated: {len(evaluations)}/8")

def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "eval":
            run_all_evaluations()
            return
        try:
            challenge_num = int(arg)
        except ValueError:
            challenge_num = 1
    else:
        challenge_num = 1

    run_challenge(challenge_num)


if __name__ == "__main__":
    main()