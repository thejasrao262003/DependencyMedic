"""Deterministic manifest mutation.

We support `requirements.txt` (Python) and `package.json` (npm) for the MVP.
Other ecosystems return an unchanged manifest — the patch attempt is then marked
failed and never reaches CI. Lockfile regeneration is intentionally out of scope.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass
class ManifestPatch:
    path: str
    original: str
    patched: str
    package: str
    from_version: str
    to_version: str


_REQ_LINE = re.compile(
    r"^(?P<name>[A-Za-z0-9_.\-]+)\s*(?P<spec>==|>=|<=|~=|!=|>|<)\s*(?P<version>[0-9A-Za-z._\-+]+)"
)


def patch_requirements_txt(
    content: str, package: str, to_version: str
) -> tuple[str, str | None]:
    """Return (new_content, from_version) — from_version is None when package not found."""
    out_lines: list[str] = []
    found_from: str | None = None
    target = package.lower()
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            out_lines.append(raw)
            continue
        m = _REQ_LINE.match(line)
        if m and m.group("name").lower() == target:
            found_from = m.group("version")
            out_lines.append(f"{m.group('name')}=={to_version}")
        else:
            out_lines.append(raw)
    return "\n".join(out_lines) + ("\n" if content.endswith("\n") else ""), found_from


def patch_package_json(
    content: str, package: str, to_version: str
) -> tuple[str, str | None]:
    """Bump package version in dependencies / devDependencies.

    Preserves a leading caret/tilde range qualifier when present on the original
    spec (e.g. `^4.17.15` -> `^4.17.21`). Falls back to an exact pin otherwise.
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return content, None

    found_from: str | None = None
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        deps = data.get(section)
        if not isinstance(deps, dict) or package not in deps:
            continue
        existing = deps[package]
        prefix = ""
        if isinstance(existing, str) and existing[:1] in ("^", "~"):
            prefix = existing[0]
            found_from = existing[1:]
        elif isinstance(existing, str):
            found_from = existing
        deps[package] = f"{prefix}{to_version}"
        break

    if found_from is None:
        return content, None
    return json.dumps(data, indent=2) + "\n", found_from
