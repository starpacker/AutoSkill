import argparse
from pathlib import Path

from autoskill.generalize import generalize_file
from autoskill.oracle import extract_oracle_skill
from autoskill.prune import prune_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract, prune, or generalize a skill.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("extract")
    p.add_argument("--reference", type=Path, required=True)
    p.add_argument("--instruction", default="")
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("prune")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--max-lines", type=int)
    p = sub.add_parser("generalize")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--target-type", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "extract":
        extract_oracle_skill(args.reference, args.instruction, args.output)
    elif args.command == "prune":
        prune_file(args.input, args.output, args.max_lines)
    else:
        generalize_file(args.input, args.output, args.target_type)


if __name__ == "__main__":
    main()
