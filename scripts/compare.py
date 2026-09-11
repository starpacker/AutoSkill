import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Aggregate normalized arm results.")
    p.add_argument("inputs", nargs="+", type=Path)
    p.add_argument("--output", type=Path, default=Path("comparison_summary.json"))
    args = p.parse_args()
    values = defaultdict(list)
    for path in args.inputs:
        for row in json.loads(path.read_text(encoding="utf-8")):
            if isinstance(row.get("reward"), (int, float)):
                values[row["arm"]].append(row["reward"])
    summary = {arm: {"n": len(vals), "mean_reward": sum(vals) / len(vals)}
               for arm, vals in values.items() if vals}
    args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
