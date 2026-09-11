"""LLM-assisted skill generalization with a deterministic fallback."""

import json
import os
import urllib.request
from pathlib import Path
from typing import Optional

from .prune import prune_skill


def _fallback(skill: str, target_type: str) -> str:
    return prune_skill(
        f"# Generalized Skill for {target_type}\n\n"
        "Apply the following reusable workflow to the target task. Replace "
        "task-specific names, paths, and numeric constants with values inferred "
        "from the target input.\n\n{skill}\n".format(skill=skill)
    )


def generalize_skill(skill: str, target_type: str, *, api_key: Optional[str] = None,
                     base_url: Optional[str] = None, model: Optional[str] = None) -> str:
    key = api_key or os.getenv("AUTOSKILL_LLM_API_KEY")
    if not key:
        return _fallback(skill, target_type)
    url = (base_url or os.getenv("AUTOSKILL_LLM_BASE_URL",
                                 "https://api.openai.com/v1")).rstrip("/") + "/chat/completions"
    payload = {
        "model": model or os.getenv("AUTOSKILL_LLM_MODEL", "gpt-4o-mini"),
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "Rewrite reusable agent skills. Never include target answers."},
            {"role": "user", "content": (
                f"Generalize this skill for unseen tasks of type '{target_type}'. "
                "Preserve workflow, checks, and output contracts; remove task-specific leakage.\n\n"
                + skill
            )},
        ],
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        body = json.loads(response.read().decode())
    content = body["choices"][0]["message"]["content"]
    return prune_skill(content)


def generalize_file(source: Path, output: Path, target_type: str, **kwargs) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generalize_skill(source.read_text(encoding="utf-8"),
                                       target_type, **kwargs), encoding="utf-8")
