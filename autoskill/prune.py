"""Section-aware pruning for skill documents."""

from pathlib import Path
from typing import Iterable, Optional


DEFAULT_DROP_HEADERS = {
    "reference evidence", "examples", "appendix", "change log", "notes",
}


def prune_skill(text: str, max_lines: Optional[int] = None,
                drop_headers: Iterable[str] = DEFAULT_DROP_HEADERS) -> str:
    drops = {h.strip().lower().lstrip("#").strip() for h in drop_headers}
    lines = text.splitlines()
    kept = []
    skipping = False
    for line in lines:
        if line.startswith("#"):
            header = line.lstrip("#").strip().lower()
            skipping = header in drops
        if not skipping:
            kept.append(line.rstrip())
    while kept and not kept[-1]:
        kept.pop()
    if max_lines and len(kept) > max_lines:
        kept = kept[:max_lines]
        while kept and kept[-1].startswith("#"):
            kept.pop()
    result = "\n".join(kept).strip() + "\n"
    if not result.lstrip().startswith("#"):
        result = "# Skill\n\n" + result
    return result


def prune_file(source: Path, output: Path, max_lines: Optional[int] = None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(prune_skill(source.read_text(encoding="utf-8"), max_lines),
                      encoding="utf-8")
