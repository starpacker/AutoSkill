from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_ratio_heatmap(substitution_ratios: pd.DataFrame, out_path: str | Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 12))
    image = ax.imshow(substitution_ratios.to_numpy(dtype=float), aspect="auto", cmap="magma", vmin=0.0)
    ax.set_title(title)
    ax.set_xlabel("Substitution type")
    ax.set_ylabel("Tumor sample")
    ax.set_xticks(range(len(substitution_ratios.columns)))
    ax.set_xticklabels([str(x) for x in substitution_ratios.columns], rotation=45, ha="right")
    ax.set_yticks(range(len(substitution_ratios.index)))
    ax.set_yticklabels([str(x) for x in substitution_ratios.index], fontsize=7)
    fig.colorbar(image, ax=ax, label="Ratio")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_stacked_ratios(substitution_ratios: pd.DataFrame, out_path: str | Path, title: str) -> None:
    ax = substitution_ratios.plot(kind="bar", stacked=True, figsize=(14, 7), width=0.85)
    ax.set_title(title)
    ax.set_xlabel("Tumor sample")
    ax.set_ylabel("Ratio")
    ax.set_ylim(0.0, 1.02)
    ax.legend(title="Substitution", bbox_to_anchor=(1.02, 1.0), loc="upper left")
    ax.figure.tight_layout()
    ax.figure.savefig(out_path, dpi=150)
    plt.close(ax.figure)
