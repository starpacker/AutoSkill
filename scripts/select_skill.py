import argparse
import json
from pathlib import Path

from autoskill.selector import SelectorConfig, V10Selector


def main() -> None:
    p = argparse.ArgumentParser(description="Select a source skill with V10 SEL.")
    p.add_argument("--target", required=True)
    p.add_argument("--skills", type=Path, required=True,
                   help="JSON object mapping source task IDs to skill paths")
    p.add_argument("--results-index", type=Path)
    p.add_argument("--similarity", type=Path)
    p.add_argument("--model", type=Path)
    p.add_argument("--task-types", type=Path)
    args = p.parse_args()
    cfg = SelectorConfig(**{k: v for k, v in {
        "results_index": args.results_index, "similarity": args.similarity,
        "model": args.model, "task_types": args.task_types}.items() if v})
    source, score = V10Selector(cfg).select(args.target, json.loads(args.skills.read_text()))
    print(json.dumps({"target": args.target, "source": source, "score": score}))


if __name__ == "__main__":
    main()
