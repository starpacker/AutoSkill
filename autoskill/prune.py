"""Oracle-skill variant rendering and lifecycle pruning primitives.

The server implementation prunes operation blocks, not arbitrary Markdown
headings. Generated skills contain ``ORACLE_OP_START/END`` markers and a
manifest records the assets owned by each operation.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Iterable, Optional

_BLOCK = re.compile(
    r"\n?<!--\s*ORACLE_OP_START\s+([A-Za-z0-9_-]+)\s*-->.*?"
    r"<!--\s*ORACLE_OP_END\s+\1\s*-->\n?",
    re.DOTALL,
)
_OP_ID = re.compile(r"\bop_[0-9]{3}[A-Za-z0-9_-]*\b")


def _manifest(bundle_dir: Path) -> dict:
    path = bundle_dir / "oracle_skill_manifest.json"
    if not path.exists():
        raise FileNotFoundError(f"oracle skill manifest not found: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version") != 1 or not value.get("operations"):
        raise ValueError("invalid oracle skill manifest")
    return value


def _enabled(manifest: dict, enabled: Optional[Iterable[str]] = None,
             drop: Optional[Iterable[str]] = None) -> tuple[list[dict], list[dict]]:
    if enabled is not None and drop is not None:
        raise ValueError("enabled_operation_ids and drop_operation_ids are mutually exclusive")
    operations = manifest["operations"]
    known = {op["id"] for op in operations}
    defaults = [op["id"] for op in operations if op.get("enabled_by_default") is True]
    if drop is not None:
        drop_ids = list(dict.fromkeys(drop))
        if not drop_ids:
            raise ValueError("drop operation ids must be non-empty")
        for op_id in drop_ids:
            if op_id not in known:
                raise ValueError(f"Unknown oracle operation id: {op_id}")
            if op_id not in defaults:
                raise ValueError(
                    f"Oracle operation is not enabled by default and cannot be dropped: {op_id}"
                )
        requested = [op_id for op_id in defaults if op_id not in set(drop_ids)]
    else:
        requested = list(enabled) if enabled is not None else defaults
        unknown = [op_id for op_id in requested if op_id not in known]
        if unknown:
            raise ValueError(f"Unknown oracle operation id: {unknown[0]}")
    enabled_set = set(requested)
    enabled_ops = [op for op in operations if op["id"] in enabled_set]
    disabled = [
        {"id": op["id"], "reason": "disabled_by_request" if (enabled is not None or drop is not None) else "disabled_by_default"}
        for op in operations if op["id"] not in enabled_set
    ]
    return enabled_ops, disabled


def _remove_blocks(markdown: str, disabled_ids: set[str]) -> str:
    return _BLOCK.sub(lambda m: "" if m.group(1) in disabled_ids else m.group(0), markdown)


def _sanitize(markdown: str, operation_ids: Iterable[str]) -> str:
    markdown = re.sub(r"^<!--\s*ORACLE_OP_(?:START|END)\s+[^>]+-->\s*$", "", markdown, flags=re.M)
    markdown = re.sub(r"^#{1,6}\s+op_[A-Za-z0-9_-]+\s*$", "", markdown, flags=re.M)
    markdown = re.sub(r"^\s*(?:data flow|pipeline(?:\s+overview)?)\s*:.*$", "", markdown,
                      flags=re.I | re.M)
    markdown = re.sub(r"\bablatable\b", "", markdown, flags=re.I)
    markdown = _OP_ID.sub("the related step", markdown)
    for op_id in operation_ids:
        if op_id in markdown:
            raise ValueError(f"rendered oracle skill contains operation id {op_id}")
    return re.sub(r"\n{3,}", "\n\n", markdown).strip() + "\n"


def _replace_assets(content: str, aliases: dict[str, str]) -> str:
    for old, new in aliases.items():
        content = content.replace(old, new).replace(old.replace("/", "\\"), new)
        content = content.replace(Path(old).name, Path(new).name)
    return content


def render_oracle_skill_variant(
    bundle_dir: Path,
    output_dir: Path,
    *,
    enabled_operation_ids: Optional[Iterable[str]] = None,
    drop_operation_ids: Optional[Iterable[str]] = None,
    variant_manifest_path: Optional[Path] = None,
) -> dict:
    """Render a solver-facing variant from a bundle manifest."""
    bundle_dir, output_dir = bundle_dir.resolve(), output_dir.resolve()
    if bundle_dir == output_dir or bundle_dir in output_dir.parents:
        raise ValueError("refusing to render a variant over/inside its source bundle")
    manifest = _manifest(bundle_dir)
    enabled_ops, disabled_ops = _enabled(manifest, enabled_operation_ids, drop_operation_ids)
    skill_name = manifest["skill_name"]
    source_root = bundle_dir / "skills" / skill_name
    source_md = source_root / "SKILL.md"
    if not source_md.exists():
        raise FileNotFoundError(f"skill markdown not found: {source_md}")
    markdown = _remove_blocks(source_md.read_text(encoding="utf-8"), {x["id"] for x in disabled_ops})
    if output_dir.exists():
        shutil.rmtree(output_dir)
    out_skill = output_dir / "skills" / skill_name
    out_skill.mkdir(parents=True, exist_ok=True)

    resources = sorted({a for op in enabled_ops for a in op.get("resources", [])})
    scripts = sorted({a for op in enabled_ops for a in op.get("scripts", [])})
    aliases: dict[str, str] = {}
    for index, asset in enumerate(resources, 1):
        aliases[asset] = f"resources/resource_{index:03d}{Path(asset).suffix}"
    for index, asset in enumerate(scripts, 1):
        aliases[asset] = f"scripts/script_{index:03d}{Path(asset).suffix}"
    markdown = _sanitize(_replace_assets(markdown, aliases),
                         [op["id"] for op in manifest["operations"]])
    (out_skill / "SKILL.md").write_text(markdown, encoding="utf-8")
    for asset in resources + scripts:
        source = source_root / asset
        if not source.exists():
            raise FileNotFoundError(f"operation asset not found: {source}")
        content = source.read_text(encoding="utf-8")
        content = _replace_assets(content, aliases)
        destination = out_skill / aliases[asset]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(_OP_ID.sub("the related step", content), encoding="utf-8")

    variant = {
        "schema_version": 1,
        "source_bundle": str(bundle_dir),
        "skill_name": skill_name,
        "enabled_ops": [op["id"] for op in enabled_ops],
        "disabled_ops": disabled_ops,
        "copied_resources": [aliases[a] for a in resources],
        "copied_scripts": [aliases[a] for a in scripts],
    }
    manifest_path = variant_manifest_path or output_dir.parent / "metadata" / "variants" / f"{output_dir.name}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(variant, indent=2) + "\n", encoding="utf-8")
    (manifest_path.parent / f"{manifest_path.stem}.eval_command.txt").write_text(
        f"--enable-skills --skills-dir {out_skill.parent.as_posix()} --skill-name {skill_name}\n",
        encoding="utf-8",
    )
    return variant


def prune_skill(text: str, max_lines: Optional[int] = None,
                drop_operation_ids: Optional[Iterable[str]] = None) -> str:
    """Compatibility helper: remove explicit operation blocks only."""
    if drop_operation_ids:
        text = _remove_blocks(text, set(drop_operation_ids))
    text = _sanitize(text, [])
    if max_lines is not None and len(text.splitlines()) > max_lines:
        lines = text.splitlines()[:max_lines]
        while lines and lines[-1].startswith("#"):
            lines.pop()
        text = "\n".join(lines).rstrip() + "\n"
    return text


def prune_file(source: Path, output: Path, max_lines: Optional[int] = None,
               drop_operation_ids: Optional[Iterable[str]] = None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(prune_skill(source.read_text(encoding="utf-8"), max_lines, drop_operation_ids),
                      encoding="utf-8")
