# DependencyMedic — Agents

# Purpose

This document defines all autonomous agents used inside DependencyMedic.

The goals are:

* deterministic orchestration,
* predictable AI behavior,
* modular agent ownership,
* explainable workflows,
* and safe autonomous execution.

Each agent must:

* have a clearly defined responsibility,
* consume structured inputs,
* produce structured outputs,
* emit observable events,
* and avoid hidden side effects.

This document acts as:

> the behavioral specification for the AI system.

---

# Agent Philosophy

DependencyMedic uses:

# specialized workflow agents

instead of:

# a single monolithic AI orchestrator.

This architecture improves:

* observability,
* reliability,
* debuggability,
* testing,
* and parallel development.

Agents are designed to:

* reason,
* analyze,
* summarize,
* and orchestrate workflows.

Agents are NOT trusted for:

* unrestricted production actions,
* direct production merges,
* deterministic security guarantees,
* or hidden autonomous execution.

---

# Core Agent Lifecycle

Every agent follows the same execution lifecycle:

```text id="jlwm8b"
Input
  ↓
Validation
  ↓
Tool Execution
  ↓
LLM Reasoning
  ↓
Structured Output
  ↓
Confidence Scoring
  ↓
Event Emission
  ↓
Persistence
```

---

# Shared Agent Rules

All agents must:

* produce structured JSON outputs,
* generate confidence scores,
* support retry-safe execution,
* log reasoning traces,
* persist execution metadata,
* and emit observable events.

---

# Shared Agent Output Structure

```json id="jlwm5b"
{
  "status": "completed",
  "confidence_score": 0.91,
  "summary": "Generated remediation patch successfully",
  "actions_taken": [],
  "recommendations": [],
  "requires_human_review": false
}
```

---

# Agent Categories

DependencyMedic currently uses four primary agent categories:

```text id="jlwm2b"
1. Vulnerability Intelligence Agents
2. Reachability & Risk Agents
3. Remediation Agents
4. CI Failure Analysis Agents
```

---

# 1. Vulnerability Intelligence Agent

## Purpose

Responsible for:

* CVE ingestion,
* normalization,
* vulnerability enrichment,
* repository matching.

This agent acts as:

> the entry point into the remediation pipeline.

---

## Responsibilities

* ingest vulnerability feeds,
* normalize advisory data,
* deduplicate CVEs,
* extract affected packages,
* identify impacted repositories,
* emit vulnerability lifecycle events.

---

## Inputs

```json id="jlwm4b"
{
  "source": "NVD",
  "raw_vulnerability_data": {}
}
```

---

## Outputs

```json id="jlwm6b"
{
  "vulnerability_id": "uuid",
  "cve_id": "CVE-2026-1234",
  "severity": "critical",
  "affected_repositories": [
    "payment-service"
  ]
}
```

---

## Events Emitted

```text id="jlwm1b"
vuln.discovered
vuln.matched
```

---

## Tools Used

* NVD API
* OSV.dev
* GitHub Security Advisories
* MongoDB
* Dependency matcher

---

## Deterministic vs LLM Usage

### Deterministic

* CVE parsing
* package extraction
* repository matching

### LLM Usage

* vulnerability summarization
* remediation explanation
* enrichment reasoning

---

# 2. Reachability Analysis Agent

## Purpose

Responsible for:

* dependency analysis,
* exploitability reasoning,
* risk scoring,
* confidence estimation.

This agent determines:

> whether the vulnerability is actually dangerous for the repository.

---

## Responsibilities

* generate SBOMs,
* analyze dependency graphs,
* perform reachability analysis,
* compute exploitability confidence,
* generate evidence traces,
* calculate remediation priority.

---

## Inputs

```json id="jlwm8n"
{
  "repository_id": "repo_uuid",
  "vulnerability_id": "vuln_uuid"
}
```

---

## Outputs

```json id="jlwm0b"
{
  "reachable": true,
  "confidence_score": 0.92,
  "risk_score": 94,
  "evidence": [
    {
      "file": "payments/service.py",
      "symbol": "lodash.merge"
    }
  ]
}
```

---

## Events Emitted

```text id="jlwm7b"
vuln.assessed
vuln.scored
```

---

## Tools Used

* Syft
* govulncheck
* pip-audit
* npm audit
* Dependency graph analyzers

---

## Deterministic vs LLM Usage

### Deterministic

* SBOM generation
* dependency graphing
* package resolution
* vulnerability matching

### LLM Usage

* contextual exploitability reasoning
* exposure interpretation
* risk summarization

---

# 3. Patch Generation Agent

## Purpose

Responsible for:

* autonomous remediation patch generation,
* dependency upgrades,
* compatibility adjustments,
* remediation orchestration.

This agent acts as:

> the autonomous security remediation engineer.

---

## Responsibilities

* identify patched versions,
* update manifests,
* regenerate lockfiles,
* create remediation branches,
* generate patch summaries,
* prepare CI validation workflows.

---

## Inputs

```json id="jlwm2m"
{
  "repository_id": "repo_uuid",
  "vulnerability_id": "vuln_uuid",
  "recommended_fix_version": "4.17.21"
}
```

---

## Outputs

```json id="jlwm4m"
{
  "branch_name": "fix/cve-2026-1234",
  "dependency_changes": [
    {
      "package": "lodash",
      "from": "4.17.15",
      "to": "4.17.21"
    }
  ],
  "patch_generated": true
}
```

---

## Events Emitted

```text id="jlwm9m"
patch.generated
```

---

## Tools Used

* GitLab API
* package managers
* dependency lockfile generators
* Git operations
* LangGraph orchestration

---

## Deterministic vs LLM Usage

### Deterministic

* dependency version resolution
* manifest updates
* lockfile regeneration

### LLM Usage

* migration reasoning
* compatibility guidance
* remediation explanations

---

# 4. CI Failure Analysis Agent

## Purpose

Responsible for:

* CI failure interpretation,
* remediation retry analysis,
* compatibility debugging,
* retry recommendations.

This agent determines:

> why the remediation patch failed.

---

## Responsibilities

* analyze CI logs,
* identify root causes,
* suggest retry strategies,
* generate adjusted patches,
* recommend escalation paths.

---

## Inputs

```json id="jlwm5n"
{
  "pipeline_run_id": "pipeline_uuid",
  "failure_logs": "..."
}
```

---

## Outputs

```json id="jlwm1m"
{
  "failure_type": "dependency_conflict",
  "recommended_action": "pin transitive package version",
  "retry_recommended": true,
  "confidence_score": 0.83
}
```

---

## Events Emitted

```text id="jlwm3m"
ci.failed
patch.retry_requested
```

---

## Tools Used

* GitLab CI logs
* log parsers
* dependency analyzers
* remediation retry engine

---

## Deterministic vs LLM Usage

### Deterministic

* stack trace parsing
* pipeline status analysis
* log extraction

### LLM Usage

* root cause reasoning
* remediation suggestions
* retry strategy generation

---

# Human Approval Philosophy

Agents may:

* generate patches,
* trigger CI,
* open merge requests.

Agents may NOT:

* merge directly to production branches,
* bypass review gates,
* override security approvals.

Human approval is mandatory before merge.

---

# Agent Communication Model

Agents communicate through:

# Redis Stream events

Agents must:

* consume events,
* process workflows,
* emit structured outputs,
* and remain independently testable.

---

# Agent State Persistence

All agent executions must be persisted inside:

```text id="jlwm6m"
agent_runs
```

collection.

Stored metadata includes:

* execution inputs,
* outputs,
* confidence scores,
* retry counts,
* execution duration,
* reasoning summaries.

---

# Confidence Scoring

Every agent must emit:

```text id="jlwm8m"
confidence_score
```

Range:

```text id="jlwm0m"
0.0 → 1.0
```

Confidence scoring helps:

* prioritize review,
* support explainability,
* trigger escalation paths.

---

# Retry Philosophy

Agents must support:

* idempotent execution,
* retry-safe workflows,
* deterministic replay,
* and exponential backoff.

Maximum retry attempts:

```text id="jlwm2l"
2
```

---

# Agent Observability

Every agent must:

* emit structured logs,
* persist execution traces,
* expose execution timing,
* and support debugging.

---

# Agent Failure Philosophy

Failures are expected.

Agents should:

* fail visibly,
* fail safely,
* and provide actionable reasoning.

The architecture prioritizes:

* explainability,
* traceability,
* and recovery over silent automation.

---

# Future Agent Expansion

Future versions may introduce:

* rollout analysis agents,
* rollback orchestration agents,
* production observability agents,
* autonomous remediation planning agents.

These are intentionally excluded from the MVP.

---

# MVP Agent Scope

Included:

* vulnerability ingestion,
* exploitability analysis,
* remediation generation,
* CI failure analysis.

Excluded:

* production deployment autonomy,
* runtime exploit detection,
* self-learning autonomous agents,
* unsupervised production remediation.

---

# Agent System Philosophy

The agent system prioritizes:

* workflow clarity,
* deterministic orchestration,
* explainability,
* observability,
* and safe autonomous execution.

The goal is:

> autonomous remediation without autonomous chaos.
