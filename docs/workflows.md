# DependencyMedic — Workflows

# Purpose

This document defines the core operational workflows of DependencyMedic.

The goals are:

* deterministic orchestration,
* predictable workflow execution,
* modular implementation,
* reproducible demos,
* and simplified AI-assisted development.

This document acts as:

> the implementation truth source for workflow behavior.

---

# Workflow Philosophy

DependencyMedic is fundamentally:

# a workflow orchestration system

The value of the system comes from:

* coordinating multiple agents,
* sequencing remediation steps,
* handling failures safely,
* and maintaining explainable execution paths.

Workflows must:

* be event-driven,
* observable,
* retry-safe,
* and independently testable.

---

# Workflow Categories

The MVP contains five major workflows:

```text id="jlwm1w"
1. Vulnerability Discovery Workflow
2. Reachability & Risk Analysis Workflow
3. Patch Generation Workflow
4. CI Failure Recovery Workflow
5. Merge Request Approval Workflow
```

---

# Shared Workflow Rules

All workflows must:

* emit events at each major stage,
* persist execution metadata,
* support replayability,
* maintain correlation IDs,
* and expose observable state transitions.

---

# Shared Workflow Lifecycle

```text id="jlwm3w"
Trigger
   ↓
Validation
   ↓
Execution
   ↓
Event Emission
   ↓
Persistence
   ↓
Retry / Completion
```

---

# 1. Vulnerability Discovery Workflow

# Purpose

Detect and normalize new vulnerabilities from external feeds.

This workflow acts as:

> the system entry point.

---

# Trigger

Triggered every:

```text id="jlwm5w"
5 minutes
```

via scheduled feed polling.

---

# Inputs

Sources:

* NVD
* OSV.dev
* GitHub Security Advisories

---

# Workflow Steps

```text id="jlwm7w"
Poll vulnerability feeds
        ↓
Fetch new CVEs
        ↓
Normalize vulnerability format
        ↓
Deduplicate advisories
        ↓
Extract affected packages
        ↓
Store vulnerability document
        ↓
Emit vuln.discovered
```

---

# Services Involved

| Service           | Responsibility   |
| ----------------- | ---------------- |
| vuln_intelligence | feed ingestion   |
| mongodb           | persistence      |
| redis_streams     | event publishing |

---

# Outputs

Events:

```text id="jlwm9w"
vuln.discovered
```

Database writes:

```text id="jlwm2x"
vulnerabilities
```

---

# Failure Handling

If feed parsing fails:

* log structured error,
* retry with exponential backoff,
* preserve raw payload for debugging.

---

# 2. Reachability & Risk Analysis Workflow

# Purpose

Determine whether the vulnerability is actually exploitable inside a repository.

This workflow reduces:

> alert fatigue and false positives.

---

# Trigger

Triggered by:

```text id="jlwm4x"
vuln.discovered
```

---

# Workflow Steps

```text id="jlwm6x"
Receive vuln.discovered
        ↓
Find affected repositories
        ↓
Generate or fetch SBOM
        ↓
Build dependency graph
        ↓
Perform reachability analysis
        ↓
Compute exploitability confidence
        ↓
Generate risk score
        ↓
Persist assessment
        ↓
Emit vuln.assessed
        ↓
Emit vuln.scored
```

---

# Services Involved

| Service               | Responsibility          |
| --------------------- | ----------------------- |
| reachability_analysis | exploitability analysis |
| vuln_intelligence     | repository matching     |
| mongodb               | persistence             |

---

# Outputs

Events:

```text id="jlwm8x"
vuln.assessed
vuln.scored
```

Database writes:

```text id="jlwm0x"
dependency_snapshots
risk_assessments
```

---

# Deterministic vs LLM Usage

## Deterministic

* dependency resolution,
* graph traversal,
* package matching.

## LLM Usage

* contextual exposure reasoning,
* risk explanation,
* remediation summaries.

---

# Failure Handling

If SBOM generation fails:

* mark repository as analysis_failed,
* emit warning event,
* continue workflow for other repositories.

---

# 3. Patch Generation Workflow

# Purpose

Generate and validate remediation patches automatically.

This workflow acts as:

> the autonomous remediation engine.

---

# Trigger

Triggered by:

```text id="jlwm2y"
vuln.scored
```

Only executes if:

```text id="jlwm4y"
risk_level >= medium
```

---

# Workflow Steps

```text id="jlwm6y"
Receive vuln.scored
        ↓
Resolve fixed dependency version
        ↓
Create remediation branch
        ↓
Update manifests
        ↓
Regenerate lockfiles
        ↓
Commit patch
        ↓
Persist patch attempt
        ↓
Emit patch.generated
```

---

# Services Involved

| Service            | Responsibility   |
| ------------------ | ---------------- |
| remediation_engine | patch generation |
| gitlab_integration | branch creation  |
| mongodb            | persistence      |

---

# Outputs

Events:

```text id="jlwm8y"
patch.generated
```

Database writes:

```text id="jlwm0y"
patch_attempts
```

---

# Failure Handling

If dependency resolution fails:

* mark patch_attempt as failed,
* store failure summary,
* emit remediation_failed event.

---

# 4. CI Validation Workflow

# Purpose

Validate generated remediation patches using GitLab CI.

This workflow ensures:

> generated patches are actually deployable.

---

# Trigger

Triggered by:

```text id="jlwm2z"
patch.generated
```

---

# Workflow Steps

```text id="jlwm4z"
Receive patch.generated
        ↓
Push remediation branch
        ↓
Trigger GitLab pipeline
        ↓
Wait for pipeline completion
        ↓
Collect pipeline results
        ↓
Persist pipeline metadata
        ↓
If success:
    Emit patch.validated
Else:
    Emit ci.failed
```

---

# Services Involved

| Service            | Responsibility         |
| ------------------ | ---------------------- |
| gitlab_integration | pipeline orchestration |
| remediation_engine | workflow coordination  |
| mongodb            | persistence            |

---

# Outputs

Events:

```text id="jlwm6z"
ci.started
pipeline.completed
patch.validated
ci.failed
```

Database writes:

```text id="jlwm8z"
pipeline_runs
```

---

# Failure Handling

If GitLab API fails:

* retry request,
* preserve execution state,
* avoid duplicate pipeline creation.

---

# 5. CI Failure Recovery Workflow

# Purpose

Attempt autonomous recovery from CI failures.

This workflow demonstrates:

> adaptive remediation orchestration.

---

# Trigger

Triggered by:

```text id="jlwm0z"
ci.failed
```

---

# Workflow Steps

```text id="jlwm2a"
Receive ci.failed
        ↓
Fetch CI logs
        ↓
Parse stack traces
        ↓
Identify probable failure cause
        ↓
Generate remediation adjustment
        ↓
Apply retry patch
        ↓
Trigger retry pipeline
        ↓
Persist retry attempt
```

---

# Services Involved

| Service             | Responsibility      |
| ------------------- | ------------------- |
| ci_failure_analysis | failure reasoning   |
| remediation_engine  | retry orchestration |
| gitlab_integration  | pipeline retry      |

---

# Outputs

Events:

```text id="jlwm4a"
patch.retry_requested
pipeline.completed
```

Database writes:

```text id="jlwm6a"
patch_attempts
pipeline_runs
agent_runs
```

---

# Retry Rules

Maximum retry attempts:

```text id="jlwm8a"
2
```

If retries exhausted:

* escalate to human review,
* mark workflow as requires_human_intervention.

---

# 6. Merge Request Workflow

# Purpose

Create human-reviewable remediation merge requests.

This workflow provides:

> safe human-supervised remediation approval.

---

# Trigger

Triggered by:

```text id="jlwm0a"
patch.validated
```

---

# Workflow Steps

```text id="jlwm2b"
Receive patch.validated
        ↓
Generate MR summary
        ↓
Attach risk assessment
        ↓
Attach CI results
        ↓
Open GitLab MR
        ↓
Assign reviewers
        ↓
Persist MR metadata
        ↓
Emit mr.created
```

---

# Services Involved

| Service            | Responsibility      |
| ------------------ | ------------------- |
| gitlab_integration | MR creation         |
| remediation_engine | remediation context |
| mongodb            | persistence         |

---

# Outputs

Events:

```text id="jlwm4b"
mr.created
```

Database writes:

```text id="jlwm6b"
merge_requests
```

---

# Human Approval Workflow

```text id="jlwm8b"
MR Opened
    ↓
Security Review
    ↓
Engineering Review
    ↓
Approval
    ↓
Manual Merge
```

---

# Workflow Correlation IDs

Every workflow execution must include:

```text id="jlwm0b"
correlation_id
```

This allows:

* end-to-end tracing,
* workflow replay,
* debugging,
* and observability.

---

# Workflow Persistence

All workflow stages must persist:

* state transitions,
* execution timing,
* emitted events,
* retry attempts,
* reasoning summaries.

---

# Workflow Retry Philosophy

Retries must:

* be idempotent,
* preserve workflow integrity,
* avoid duplicate side effects,
* and expose observable retry state.

---

# Workflow Observability

All workflows must support:

* structured logs,
* event tracing,
* execution timing,
* failure debugging,
* and replayable execution.

---

# Workflow State Philosophy

Workflows should:

* fail visibly,
* recover safely,
* and remain explainable.

The architecture prioritizes:

* orchestration clarity,
* deterministic execution,
* and reproducible demos.

---

# MVP Workflow Scope

Included:

* vulnerability ingestion,
* exploitability analysis,
* patch generation,
* CI validation,
* CI retry orchestration,
* MR creation.

Excluded:

* autonomous production deployment,
* production rollback automation,
* runtime exploit detection,
* self-healing production infrastructure.

---

# Workflow System Philosophy

The workflow layer prioritizes:

* orchestration clarity,
* deterministic execution,
* observability,
* and safe autonomous remediation.

The goal is:

> believable autonomous workflows without operational chaos.
