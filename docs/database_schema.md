# DependencyMedic — Database Schema

# Purpose

This document defines the MongoDB database structure for DependencyMedic.

The goals are:

* schema consistency,
* predictable service ownership,
* clear relationships between entities,
* simplified AI-assisted development,
* and prevention of unstructured data growth.

The database design prioritizes:

* rapid iteration,
* observability,
* event traceability,
* and hackathon implementation speed.

---

# Database Philosophy

MongoDB is used as the primary operational datastore.

The schema design intentionally favors:

* denormalized documents,
* JSON-native structures,
* fast iteration,
* event traceability,
* and developer simplicity.

The MVP does NOT optimize for:

* massive scale,
* extreme normalization,
* or multi-tenant isolation.

---

# Database Overview

## Primary Collections

```text id="q2u5g1"
vulnerabilities
repositories
dependency_snapshots
risk_assessments
patch_attempts
pipeline_runs
merge_requests
events
agent_runs
```

---

# Common Metadata Fields

Every collection document must contain:

```json id="0k2tvw"
{
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "created_by": "service_name",
  "version": 1
}
```

---

# 1. vulnerabilities

Stores normalized vulnerability information from external feeds.

---

## Purpose

* track CVEs,
* store severity metadata,
* maintain normalized advisory data,
* support repository matching.

---

## Example Document

```json id="fwn4x2"
{
  "_id": "uuid",

  "cve_id": "CVE-2026-1234",

  "aliases": [
    "GHSA-xxxx",
    "OSV-xxxx"
  ],

  "summary": "Prototype pollution vulnerability in lodash",

  "description": "Detailed vulnerability description",

  "severity": "critical",

  "cvss_score": 9.8,

  "epss_score": 0.92,

  "published_at": "2026-05-10T12:00:00Z",

  "affected_packages": [
    {
      "name": "lodash",
      "ecosystem": "npm",
      "affected_versions": "<4.17.21",
      "fixed_versions": [
        "4.17.21"
      ]
    }
  ],

  "references": [
    "https://nvd.nist.gov/..."
  ],

  "source": "NVD",

  "status": "active",

  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "created_by": "vuln_intelligence",
  "version": 1
}
```

---

## Indexes

```text id="0vjf6y"
cve_id (unique)
severity
published_at
affected_packages.name
```

---

# 2. repositories

Stores GitLab repository metadata.

---

## Purpose

* track monitored repositories,
* maintain GitLab configuration,
* map repos to vulnerabilities.

---

## Example Document

```json id="08h8x5"
{
  "_id": "uuid",

  "repo_name": "payment-service",

  "gitlab_project_id": "12345",

  "default_branch": "main",

  "languages": [
    "python"
  ],

  "repo_url": "https://gitlab.com/org/payment-service",

  "ci_enabled": true,

  "last_scanned_commit": "abc123",

  "status": "active",

  "tags": [
    "critical-service",
    "payments"
  ],

  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "created_by": "gitlab_integration",
  "version": 1
}
```

---

## Indexes

```text id="qjjx7m"
repo_name
gitlab_project_id (unique)
status
```

---

# 3. dependency_snapshots

Stores SBOM snapshots and dependency trees.

---

## Purpose

* track repository dependencies,
* support vulnerability matching,
* enable reachability analysis.

---

## Example Document

```json id="r55w7v"
{
  "_id": "uuid",

  "repository_id": "repo_uuid",

  "commit_sha": "abc123",

  "ecosystem": "npm",

  "dependencies": [
    {
      "name": "lodash",
      "version": "4.17.15",
      "direct": false,
      "path": [
        "express",
        "lodash"
      ]
    }
  ],

  "sbom_format": "cyclonedx",

  "generated_at": "ISO8601",

  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "created_by": "reachability_analysis",
  "version": 1
}
```

---

## Indexes

```text id="xokx4n"
repository_id
commit_sha
dependencies.name
dependencies.version
```

---

# 4. risk_assessments

Stores exploitability and risk analysis results.

---

## Purpose

* store reachability analysis,
* maintain confidence scores,
* support remediation prioritization.

---

## Example Document

```json id="mw0ixv"
{
  "_id": "uuid",

  "repository_id": "repo_uuid",

  "vulnerability_id": "vuln_uuid",

  "reachable": true,

  "confidence_score": 0.91,

  "risk_score": 94,

  "risk_level": "critical",

  "evidence": [
    {
      "type": "function_call",
      "file": "payments/service.py",
      "symbol": "lodash.merge"
    }
  ],

  "analysis_summary": "Vulnerable function reachable from public API endpoint",

  "recommended_action": "upgrade lodash to 4.17.21",

  "assessed_by": "reachability_agent",

  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "created_by": "reachability_analysis",
  "version": 1
}
```

---

## Indexes

```text id="2o9fwe"
repository_id
vulnerability_id
risk_level
reachable
```

---

# 5. patch_attempts

Stores autonomous remediation attempts.

---

## Purpose

* track generated patches,
* maintain retry history,
* support auditability.

---

## Example Document

```json id="fqsf8k"
{
  "_id": "uuid",

  "repository_id": "repo_uuid",

  "vulnerability_id": "vuln_uuid",

  "branch_name": "fix/cve-2026-1234",

  "dependency_changes": [
    {
      "package": "lodash",
      "from_version": "4.17.15",
      "to_version": "4.17.21"
    }
  ],

  "attempt_number": 1,

  "status": "validated",

  "llm_used": true,

  "confidence_score": 0.87,

  "retry_reason": null,

  "patch_summary": "Updated lodash and regenerated package-lock.json",

  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "created_by": "remediation_engine",
  "version": 1
}
```

---

## Indexes

```text id="w2v6l2"
repository_id
vulnerability_id
status
branch_name
```

---

# 6. pipeline_runs

Stores GitLab CI/CD execution details.

---

## Purpose

* track CI validation,
* store pipeline outcomes,
* support retry analysis.

---

## Example Document

```json id="0kjlwm"
{
  "_id": "uuid",

  "repository_id": "repo_uuid",

  "patch_attempt_id": "patch_uuid",

  "gitlab_pipeline_id": "98765",

  "status": "failed",

  "duration_seconds": 143,

  "failed_stage": "unit_tests",

  "failure_summary": "TypeError in payment validation tests",

  "logs_url": "https://gitlab.com/...",

  "retry_attempted": true,

  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "created_by": "gitlab_integration",
  "version": 1
}
```

---

## Indexes

```text id="tjlwm3"
repository_id
patch_attempt_id
status
gitlab_pipeline_id
```

---

# 7. merge_requests

Stores remediation merge request metadata.

---

## Purpose

* track remediation MRs,
* maintain approval status,
* support audit workflows.

---

## Example Document

```json id="djlwm0"
{
  "_id": "uuid",

  "repository_id": "repo_uuid",

  "patch_attempt_id": "patch_uuid",

  "gitlab_mr_id": "54321",

  "title": "Fix CVE-2026-1234 - Upgrade lodash",

  "status": "opened",

  "reviewers": [
    "security-team"
  ],

  "approval_required": true,

  "approved": false,

  "mergeable": true,

  "mr_url": "https://gitlab.com/...",

  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "created_by": "gitlab_integration",
  "version": 1
}
```

---

## Indexes

```text id="jlwm8r"
repository_id
patch_attempt_id
status
gitlab_mr_id
```

---

# 8. events

Stores emitted system events.

---

## Purpose

* audit event flow,
* support debugging,
* enable replayable workflows.

---

## Example Document

```json id="jlwm92"
{
  "_id": "uuid",

  "event_type": "patch.generated",

  "source_service": "remediation_engine",

  "payload": {
    "repository_id": "repo_uuid",
    "patch_attempt_id": "patch_uuid"
  },

  "processing_status": "completed",

  "timestamp": "ISO8601",

  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "created_by": "event_bus",
  "version": 1
}
```

---

## Indexes

```text id="jlwm4t"
event_type
timestamp
processing_status
```

---

# 9. agent_runs

Stores AI agent execution metadata.

---

## Purpose

* maintain reasoning traces,
* support debugging,
* track LLM usage,
* measure confidence and retries.

---

## Example Document

```json id="jlwm7w"
{
  "_id": "uuid",

  "agent_name": "ci_failure_analysis_agent",

  "workflow_id": "workflow_uuid",

  "input_summary": "Pipeline failed due to TypeError",

  "output_summary": "Suggested dependency pinning fix",

  "confidence_score": 0.81,

  "tokens_used": 4321,

  "execution_time_ms": 5230,

  "status": "completed",

  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "created_by": "langgraph_runtime",
  "version": 1
}
```

---

## Indexes

```text id="jlwm5v"
agent_name
workflow_id
status
```

---

# Relationship Overview

```text id="jlwm1k"
repositories
    ↓
dependency_snapshots
    ↓
risk_assessments
    ↓
patch_attempts
    ↓
pipeline_runs
    ↓
merge_requests
```

---

# Database Ownership Rules

Each service owns specific collections.

| Service               | Owned Collections                      |
| --------------------- | -------------------------------------- |
| vuln_intelligence     | vulnerabilities                        |
| gitlab_integration    | repositories, merge_requests           |
| reachability_analysis | dependency_snapshots, risk_assessments |
| remediation_engine    | patch_attempts                         |
| event_system          | events                                 |
| langgraph_runtime     | agent_runs                             |

No service may directly modify another service’s collections outside approved workflows.

---

# Schema Evolution Rules

For MVP:

* additive schema changes preferred,
* avoid destructive migrations,
* preserve backward compatibility,
* use version fields for major structure updates.

---

# Database Philosophy

The database schema prioritizes:

* observability,
* auditability,
* explainability,
* and rapid development speed.

The goal is:

> predictable workflows without unnecessary database complexity.
