from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ProjectRoot import getProjectRootPath


@dataclass
class SafetyPolicy:
    name: str = "default"
    block_patterns: list[str] = field(default_factory=list)
    protected_paths: list[str] = field(default_factory=list)
    require_approval: list[str] = field(default_factory=list)
    max_output_chars: int = 4000


def loadPolicy(name: str | None = None) -> SafetyPolicy:
    policyName = (name or "default").strip() or "default"
    policiesDir = getProjectRootPath().joinpath("conf", "policies")
    path = policiesDir.joinpath(f"{policyName}.json")
    if not path.exists():
        path = policiesDir.joinpath("default.json")
        policyName = "default"
    return _loadPolicyFile(path, policyName)


def _loadPolicyFile(path: Path, name: str) -> SafetyPolicy:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return SafetyPolicy(name=name)
    rules = data.get("rules") or {}
    return SafetyPolicy(
        name=name,
        block_patterns=list(rules.get("block_patterns") or []),
        protected_paths=list(rules.get("protected_paths") or []),
        require_approval=list(rules.get("require_approval") or []),
        max_output_chars=int(rules.get("max_output_chars") or 4000),
    )
