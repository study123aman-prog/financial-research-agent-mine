import json
import os

for i in range(1, 9):
    path = f"results/challenge_{i}_eval.json"
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        metrics = data["automated_metrics"]["metrics"]
        print(f"\nChallenge {i} - Overall: {data['overall_score']:.1%}")
        for k, v in metrics.items():
            status = "PASS" if v["passed"] else "FAIL"
            print(f"  {k}: {v['score']:.0%} [{status}] - {v['name']}")