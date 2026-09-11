import argparse
from pathlib import Path

from my_claude import HarnessConfig, HarnessRunner, Skill, Task
from autoskill.transfer import run_arms, write_comparison


def main() -> None:
    p = argparse.ArgumentParser(description="Run the four AutoSkill evaluation arms.")
    p.add_argument("--task-id", required=True)
    p.add_argument("--task-dir", type=Path, required=True)
    p.add_argument("--oracle-skill", type=Path)
    p.add_argument("--selected-skill", type=Path)
    p.add_argument("--output", type=Path, default=Path("runs/comparison.json"))
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    task = Task(args.task_id, args.task_dir)
    oracle = Skill("oracle", args.oracle_skill.parent, args.oracle_skill.read_text()) if args.oracle_skill else None
    selected = Skill("selected", args.selected_skill.parent, args.selected_skill.read_text()) if args.selected_skill else None
    rows = run_arms(task, HarnessRunner(HarnessConfig()), oracle=oracle,
                    selected=selected, execute=args.execute)
    write_comparison(rows, args.output)
    for row in rows:
        print(f"{row.arm}: {row.status} reward={row.reward}")


if __name__ == "__main__":
    main()
