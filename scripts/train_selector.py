import argparse
from pathlib import Path

from autoskill.selector.train import train_model


def main() -> None:
    p = argparse.ArgumentParser(description="Train V10 SEL confidence data.")
    p.add_argument("--results-index", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(train_model(args.results_index, args.output))


if __name__ == "__main__":
    main()
