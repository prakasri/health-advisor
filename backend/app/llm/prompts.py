"""Loads versioned prompt files from specs/ai/prompts (AI-001 §6)."""

from dataclasses import dataclass
from functools import cache

import yaml

from app.config import settings

PROMPT_FILES = {
    "write_diet_plan": "diet_plan.v1.md",
    "write_lifestyle_plan": "lifestyle_plan.v1.md",
    "write_narrative": "narrative.v1.md",
    "safety_check": "safety_judge.v1.md",
}


@dataclass(frozen=True)
class Prompt:
    node: str
    name: str  # e.g. "diet_plan.v1"
    system: str


def _parse(path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    _, front, body = text.split("---", 2)
    return yaml.safe_load(front), body.strip()


@cache
def prompt(node: str) -> Prompt:
    filename = PROMPT_FILES[node]
    meta, body = _parse(settings.specs_dir / "ai/prompts" / filename)
    if meta["node"] != node:
        raise ValueError(f"{filename} declares node {meta['node']!r}, expected {node!r}")
    return Prompt(node=node, name=filename.removesuffix(".md"), system=body)


def prompt_version() -> str:
    """Stored in report.meta.prompt_version."""
    return "+".join(prompt(node).name for node in PROMPT_FILES)
