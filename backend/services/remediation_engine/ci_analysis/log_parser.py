"""Deterministic CI log triage."""

from __future__ import annotations

import re
from dataclasses import dataclass

_TRACE_LINES = re.compile(
    r"(?P<line>(?:Traceback|TypeError|ImportError|ModuleNotFoundError|AttributeError|"
    r"AssertionError|SyntaxError|ERROR|FAILED).+)"
)


@dataclass
class LogTriage:
    failure_type: str
    error_lines: list[str]
    suggestion: str  # one-line deterministic guess
    confidence: float


def classify(logs: str) -> LogTriage:
    if not logs:
        return LogTriage(
            failure_type="unknown",
            error_lines=[],
            suggestion="Re-run the pipeline; no logs were captured.",
            confidence=0.2,
        )

    matches = [m.group("line").strip() for m in _TRACE_LINES.finditer(logs)]
    head = matches[:5]

    text = "\n".join(matches).lower()
    if "modulenotfounderror" in text or "no module named" in text:
        return LogTriage(
            failure_type="missing_dependency",
            error_lines=head,
            suggestion="Add the missing transitive dependency to the manifest.",
            confidence=0.85,
        )
    if "importerror" in text:
        return LogTriage(
            failure_type="dependency_conflict",
            error_lines=head,
            suggestion="Pin the conflicting transitive package to a compatible version.",
            confidence=0.85,
        )
    if "typeerror" in text or "attributeerror" in text:
        return LogTriage(
            failure_type="api_breakage",
            error_lines=head,
            suggestion=(
                "Upgrade may have changed the API surface; pin to the previous "
                "minor or apply a small code shim."
            ),
            confidence=0.75,
        )
    if "syntaxerror" in text:
        return LogTriage(
            failure_type="syntax_error",
            error_lines=head,
            suggestion="Patch contained malformed manifest syntax; regenerate.",
            confidence=0.65,
        )
    if matches:
        return LogTriage(
            failure_type="test_failure",
            error_lines=head,
            suggestion="Existing test suite caught a regression; consider a smaller version bump.",
            confidence=0.55,
        )
    return LogTriage(
        failure_type="unknown",
        error_lines=head,
        suggestion="Logs did not match any known failure shape; escalate to human review.",
        confidence=0.2,
    )
