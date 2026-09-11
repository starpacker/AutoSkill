import argparse
from pathlib import Path

from autoskill.generalize import generalize_file
from autoskill.oracle import extract_oracle_skill, generate_template_bundle
from autoskill.prune import prune_file, render_oracle_skill_variant


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract, prune, or generalize a skill.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("extract")
    p.add_argument("--reference", type=Path, required=True)
    p.add_argument("--instruction", default="")
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("generate-bundle",
                        help="Generate the reference-compatible oracle bundle from task/std_code.")
    p.add_argument("--task-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--skill-name")
    p = sub.add_parser("prune")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--max-lines", type=int)
    p.add_argument("--drop-ops", nargs="*", default=[])
    p = sub.add_parser("render",
                        help="Render a solver-facing bundle variant by operation IDs.")
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--drop-ops", nargs="*", default=None)
    p.add_argument("--enabled-ops", nargs="*", default=None)
    p = sub.add_parser("generalize")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--target-type", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "extract":
        extract_oracle_skill(args.reference, args.instruction, args.output)
    elif args.command == "generate-bundle":
        print(generate_template_bundle(args.task_dir, args.output, args.skill_name))
    elif args.command == "prune":
        prune_file(args.input, args.output, args.max_lines, args.drop_ops)
    elif args.command == "render":
        print(render_oracle_skill_variant(
            args.bundle, args.output,
            enabled_operation_ids=args.enabled_ops,
            drop_operation_ids=args.drop_ops,
        ))
    else:
        generalize_file(args.input, args.output, args.target_type)


if __name__ == "__main__":
    main()
