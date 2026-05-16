"""
Reachability Analysis Agent.

Three-step LangGraph-shaped pipeline (deterministic first, optional LLM last):
  parse  →  analyze  →  score

Works fully offline when GEMINI_API_KEY is absent — deterministic triage is the
primary path; Gemini adds an explanatory summary only when the key is present.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from shared.utils.mongo import get_database
from shared.constants import (
    COLLECTION_VULNERABILITIES,
    COLLECTION_REPOSITORIES,
    COLLECTION_DEPENDENCY_SNAPSHOTS,
)
from shared.logging import get_logger

logger = get_logger("reachability_analysis.agent")

# Minimum CVSS threshold to bother running remediation (same as vuln_scored_consumer)
_MIN_CVSS_FOR_HIGH = 7.0


@dataclass
class ReachabilityResult:
    vulnerability_id: str
    repository_id: str
    reachable: bool
    confidence_score: float
    evidence: list[dict] = field(default_factory=list)
    evidence_count: int = 0
    risk_score: int = 0
    risk_level: str = "low"
    recommended_action: str = ""
    analysis_summary: str = ""


async def run_reachability_agent(
    vulnerability_id: str,
    repository_id: str,
    correlation_id: str,
    *,
    gemini_api_key: str = "",
) -> ReachabilityResult:
    """
    Full three-step reachability analysis.
    Returns a populated ReachabilityResult ready to be persisted + published.
    """
    # ── Step 1: Parse ─────────────────────────────────────────────────────────
    vuln, repo, snapshot = await _load_context(vulnerability_id, repository_id)

    # ── Step 2: Analyze reachability ──────────────────────────────────────────
    reachable, confidence, evidence = _analyze(vuln, repo, snapshot)

    # ── Step 3: Score risk ────────────────────────────────────────────────────
    risk_score, risk_level = _score_risk(vuln, reachable, confidence)
    recommended_action = _build_recommendation(vuln, snapshot)

    # ── Optional: Gemini contextual summary ──────────────────────────────────
    analysis_summary = _deterministic_summary(vuln, repo, reachable, risk_score)
    if gemini_api_key:
        try:
            analysis_summary = await _gemini_summary(
                vuln, repo, evidence, risk_score, gemini_api_key
            )
        except Exception as exc:
            logger.warning(
                "Gemini summary failed, using deterministic fallback",
                extra={"error": str(exc), "correlation_id": correlation_id},
            )

    result = ReachabilityResult(
        vulnerability_id=vulnerability_id,
        repository_id=repository_id,
        reachable=reachable,
        confidence_score=confidence,
        evidence=evidence,
        evidence_count=len(evidence),
        risk_score=risk_score,
        risk_level=risk_level,
        recommended_action=recommended_action,
        analysis_summary=analysis_summary,
    )
    logger.info(
        "Reachability analysis complete",
        extra={
            "vulnerability_id": vulnerability_id,
            "repository_id": repository_id,
            "reachable": reachable,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "confidence_score": confidence,
            "correlation_id": correlation_id,
        },
    )
    return result


# ── Internal helpers ──────────────────────────────────────────────────────────


async def _load_context(
    vulnerability_id: str, repository_id: str
) -> tuple[dict, dict, dict]:
    """Load vulnerability, repository, and dependency snapshot from MongoDB."""
    db = get_database()

    vuln = await db[COLLECTION_VULNERABILITIES].find_one({"_id": vulnerability_id})
    if not vuln:
        raise ValueError(f"Vulnerability not found: {vulnerability_id}")

    repo = await db[COLLECTION_REPOSITORIES].find_one({"_id": repository_id})
    if not repo:
        raise ValueError(f"Repository not found: {repository_id}")

    # Snapshot written by vuln_intelligence.repo_matcher when vuln.matched was published
    snapshot = await db[COLLECTION_DEPENDENCY_SNAPSHOTS].find_one(
        {"repo_id": repository_id, "vuln_id": vulnerability_id}
    ) or {}

    return vuln, repo, snapshot


def _analyze(
    vuln: dict, repo: dict, snapshot: dict
) -> tuple[bool, float, list[dict]]:
    """
    Deterministic reachability analysis.

    Strategy: if the vulnerable package appears in the dependency snapshot's
    matched_packages list, the vulnerability IS reachable (package is imported).
    This is conservative (false-positive rather than false-negative) which is
    the correct tradeoff for a security tool.

    Evidence is the manifest file + package pin where the match was found.
    """
    matched_packages: list[dict] = snapshot.get("matched_packages", [])
    manifest_files: list[str] = snapshot.get("manifest_files", [])

    if not matched_packages:
        # No snapshot — fall back to seed_manifests in the repo doc
        seed_manifests: dict = repo.get("seed_manifests", {})
        if seed_manifests:
            # If we have manifests but no snapshot, the match wasn't done yet.
            # Mark as not-reachable with low confidence so we don't block the flow.
            return False, 0.4, []
        return False, 0.3, []

    # Build evidence from matched packages
    evidence: list[dict] = []
    for pkg in matched_packages:
        pkg_name = pkg.get("name", "")
        pkg_version = pkg.get("version", "")
        # Attribute evidence to the first manifest file (manifests are small for MVP)
        manifest_file = manifest_files[0] if manifest_files else "dependency file"
        symbol = f"{pkg_name}=={pkg_version}" if pkg_version else pkg_name
        evidence.append(
            {
                "type": "dependency",
                "file": manifest_file,
                "symbol": symbol,
            }
        )

    # Confidence: base 0.80 for a direct dep match
    confidence = 0.80
    cvss: float = vuln.get("cvss_score") or 0.0
    epss: float = vuln.get("epss_score") or 0.0

    # Boost confidence for well-known, highly exploited CVEs
    if cvss >= 9.0:
        confidence = min(0.95, confidence + 0.10)
    if epss >= 0.5:
        confidence = min(0.95, confidence + 0.05)

    return True, round(confidence, 3), evidence


def _score_risk(
    vuln: dict, reachable: bool, confidence: float
) -> tuple[int, str]:
    """
    Convert CVSS + EPSS + reachability into a 0-100 risk score.

    Formula:
      base = cvss_score * 10  (NVD is 0-10 scale → 0-100)
      epss_boost: +5 if EPSS > 0.5, +10 if EPSS > 0.9
      if not reachable: apply 0.5 dampening factor
      cap at 100
    """
    cvss: float = vuln.get("cvss_score") or 0.0
    epss: float = vuln.get("epss_score") or 0.0

    base = cvss * 10.0
    epss_boost = 0.0
    if epss >= 0.9:
        epss_boost = 10.0
    elif epss >= 0.5:
        epss_boost = 5.0

    raw_score = base + epss_boost
    if not reachable:
        raw_score *= 0.5

    risk_score = int(min(100, max(0, round(raw_score))))

    if risk_score >= 90:
        risk_level = "critical"
    elif risk_score >= 70:
        risk_level = "high"
    elif risk_score >= 40:
        risk_level = "medium"
    else:
        risk_level = "low"

    return risk_score, risk_level


def _build_recommendation(vuln: dict, snapshot: dict) -> str:
    """
    Generate a human-readable remediation recommendation.
    Matches matched_packages from the snapshot against fixed_versions in the vuln doc.
    """
    matched: list[dict] = snapshot.get("matched_packages", [])
    vuln_packages: list[dict] = vuln.get("affected_packages", [])

    # Build lookup: package_name → fixed_versions
    fix_map: dict[str, list[str]] = {}
    for pkg in vuln_packages:
        name = pkg.get("name", "").lower()
        fixed = pkg.get("fixed_versions", [])
        if name and fixed:
            fix_map[name] = fixed

    recommendations: list[str] = []
    for pkg in matched:
        name = pkg.get("name", "").lower()
        current = pkg.get("version", "")
        fixed_list = fix_map.get(name, [])
        if fixed_list:
            target = fixed_list[0]
            if current:
                recommendations.append(
                    f"Upgrade {name} from {current} to {target}"
                )
            else:
                recommendations.append(f"Upgrade {name} to {target}")
        elif name:
            recommendations.append(f"Review and update {name}")

    if not recommendations:
        cve_id = vuln.get("cve_id", "this vulnerability")
        return f"Review dependencies and apply patches for {cve_id}"

    return "; ".join(recommendations)


def _deterministic_summary(
    vuln: dict, repo: dict, reachable: bool, risk_score: int
) -> str:
    cve_id = vuln.get("cve_id", "Unknown CVE")
    repo_name = repo.get("repo_name", "the repository")
    severity = vuln.get("severity", "unknown")
    if reachable:
        return (
            f"{cve_id} ({severity}) is present in {repo_name}'s dependency tree. "
            f"Risk score: {risk_score}/100. Immediate patching recommended."
        )
    return (
        f"{cve_id} ({severity}) was found in the advisory database but does not "
        f"appear reachable in {repo_name}. Risk score: {risk_score}/100. "
        f"Monitor and patch at next maintenance window."
    )


async def _gemini_summary(
    vuln: dict,
    repo: dict,
    evidence: list[dict],
    risk_score: int,
    api_key: str,
) -> str:
    """Optional Gemini-powered contextual risk summary."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
    except ImportError:
        return _deterministic_summary(vuln, repo, bool(evidence), risk_score)

    os.environ.setdefault("GOOGLE_API_KEY", api_key)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key)

    evidence_text = (
        "\n".join(f"  - {e['file']}: {e['symbol']}" for e in evidence[:5])
        if evidence
        else "  (no direct evidence found)"
    )

    prompt = (
        f"Summarize the security risk in 2-3 sentences for a developer.\n\n"
        f"CVE: {vuln.get('cve_id')}\n"
        f"Severity: {vuln.get('severity')}, CVSS: {vuln.get('cvss_score')}\n"
        f"Summary: {vuln.get('summary', '')}\n"
        f"Repository: {repo.get('repo_name')}\n"
        f"Evidence:\n{evidence_text}\n"
        f"Risk score: {risk_score}/100\n\n"
        f"Be concise and actionable."
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return response.content.strip()
