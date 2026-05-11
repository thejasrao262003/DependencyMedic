"""Deterministic version selection from a vulnerability's fixed_versions list.

We intentionally avoid pulling in `packaging` for npm-style and ruby-style versions —
the demo runs against a controlled set of advisories where fixed_versions are
already concrete strings. We pick the lowest fix that is strictly greater than
the currently installed version, falling back to the first fix if comparison fails.
"""

from __future__ import annotations

import re

_VERSION_PART = re.compile(r"(\d+)")


def _parse(v: str) -> tuple[int, ...]:
    parts = _VERSION_PART.findall(v)
    return tuple(int(p) for p in parts) if parts else (0,)


def is_higher(candidate: str, baseline: str) -> bool:
    return _parse(candidate) > _parse(baseline)


def choose_fix_version(installed: str, fixed_versions: list[str]) -> str | None:
    """Pick the lowest fixed version strictly greater than `installed`.

    Returns None when no candidate is higher than the installed version.
    """
    if not fixed_versions:
        return None
    higher = [v for v in fixed_versions if is_higher(v, installed)]
    if not higher:
        return fixed_versions[0]
    return sorted(higher, key=_parse)[0]
