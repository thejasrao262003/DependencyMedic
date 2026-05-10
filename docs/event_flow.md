# DependencyMedic — Event Flow

# Purpose

This document defines the event-driven orchestration model for DependencyMedic.

The goals are:

* predictable service communication,
* loose coupling between workflows,
* replayable execution,
* observability,
* and deterministic orchestration.

All backend services must communicate through events whenever possible.

This document acts as:

> the workflow backbone of the system.

---

# Event Architecture Philosophy

DependencyMedic uses an event-driven architecture built on Redis Streams.

Services should:

* emit events,
* subscribe to events,
* react asynchronously,
* and avoid direct service coupling.

The system is intentionally designed around:

* workflow orchestration,
* agent collaboration,
* retryable execution,
* and observable autonomous behavior.

---

# Event Naming Convention

All events follow:

```text id="mjlwm2"
domain.action
```

Examples:

```text id="jlwm9q"
vuln.discovered
vuln.matched
vuln.assessed
patch.generated
ci.failed
mr.created
```

---

# Standard Event Structure

Every emitted event must follow:

```json id="jlwm7u"
{
  "event_id": "uuid",
  "event_type": "vuln.discovered",
  "timestamp": "ISO8601",
  "source_service": "vuln_intelligence",
  "correlation_id": "workflow_uuid",
  "payload": {}
}
```

---

# Event Lifecycle Overview

```text id="jlwm8x"
CVE Feed
    ↓
vuln.discovered
    ↓
vuln.matched
    ↓
vuln.assessed
    ↓
vuln.scored
    ↓
patch.generated
    ↓
ci.started
    ↓
pipeline.completed
    ↓
patch.validated
    ↓
mr.created
```

---

# Core Workflow Events

---

# 1. Vulnerability Discovery Flow

## Purpose

Triggered when a new CVE is ingested and normalized.

---

## Event: `vuln.discovered`

### Emitted By

```text id="tjlwm7"
vuln_intelligence
```

### Consumed By

```text id="1jlwm9"
reachability_analysis
frontend_notifications
audit_logger
```

### Example Payload

```json id="jlwm6n"
{
  "vulnerability_id": "uuid",
  "cve_id": "CVE-2026-1234",
  "severity": "critical",
  "affected_packages": [
    {
      "name": "lodash",
      "ecosystem": "npm"
    }
  ]
}
```

---

# 2. Repository Matching Flow

## Purpose

Triggered after affected repositories are identified.

---

## Event: `vuln.matched`

### Emitted By

```text id="jlwm4w"
vuln_intelligence
```

### Consumed By

```text id="jlwm3r"
reachability_analysis
```

### Example Payload

```json id="jlwm0d"
{
  "vulnerability_id": "uuid",
  "repository_ids": [
    "repo_1",
    "repo_2"
  ]
}
```

---

# 3. Reachability Analysis Flow

## Purpose

Triggered after exploitability analysis completes.

---

## Event: `vuln.assessed`

### Emitted By

```text id="jlwm8v"
reachability_analysis
```

### Consumed By

```text id="jlwm5x"
risk_scoring
remediation_engine
dashboard_service
```

### Example Payload

```json id="jlwm2n"
{
  "repository_id": "repo_uuid",
  "vulnerability_id": "vuln_uuid",
  "reachable": true,
  "confidence_score": 0.91,
  "evidence": [
    {
      "file": "app/service.py",
      "symbol": "lodash.merge"
    }
  ]
}
```

---

# 4. Risk Scoring Flow

## Purpose

Triggered after risk prioritization completes.

---

## Event: `vuln.scored`

### Emitted By

```text id="jlwm5m"
reachability_analysis
```

### Consumed By

```text id="jlwm1o"
remediation_engine
dashboard_service
```

### Example Payload

```json id="jlwm7k"
{
  "repository_id": "repo_uuid",
  "vulnerability_id": "vuln_uuid",
  "risk_score": 94,
  "risk_level": "critical",
  "recommended_action": "upgrade lodash"
}
```

---

# 5. Patch Generation Flow

## Purpose

Triggered when a remediation patch is successfully generated.

---

## Event: `patch.generated`

### Emitted By

```text id="jlwm9l"
remediation_engine
```

### Consumed By

```text id="jlwm6z"
gitlab_integration
pipeline_orchestrator
dashboard_service
```

### Example Payload

```json id="jlwm0p"
{
  "patch_attempt_id": "patch_uuid",
  "repository_id": "repo_uuid",
  "branch_name": "fix/cve-2026-1234",
  "dependency_changes": [
    {
      "package": "lodash",
      "from": "4.17.15",
      "to": "4.17.21"
    }
  ]
}
```

---

# 6. CI Pipeline Flow

## Purpose

Tracks CI lifecycle events.

---

## Event: `ci.started`

### Emitted By

```text id="jlwm1r"
gitlab_integration
```

### Consumed By

```text id="jlwm8s"
dashboard_service
audit_logger
```

---

## Event: `pipeline.completed`

### Emitted By

```text id="jlwm4p"
gitlab_integration
```

### Consumed By

```text id="jlwm3k"
remediation_engine
ci_failure_analysis
dashboard_service
```

### Example Payload

```json id="jlwm2q"
{
  "pipeline_run_id": "pipeline_uuid",
  "repository_id": "repo_uuid",
  "status": "failed",
  "failed_stage": "unit_tests"
}
```

---

# 7. CI Failure Recovery Flow

## Purpose

Triggered when CI validation fails.

---

## Event: `ci.failed`

### Emitted By

```text id="jlwm9v"
gitlab_integration
```

### Consumed By

```text id="jlwm5p"
ci_failure_analysis
remediation_engine
```

### Example Payload

```json id="jlwm7d"
{
  "pipeline_run_id": "pipeline_uuid",
  "failure_summary": "TypeError in auth validation",
  "logs_url": "https://gitlab.com/logs"
}
```

---

# 8. Patch Validation Flow

## Purpose

Triggered when remediation validation succeeds.

---

## Event: `patch.validated`

### Emitted By

```text id="jlwm0x"
remediation_engine
```

### Consumed By

```text id="jlwm6q"
gitlab_integration
dashboard_service
```

### Example Payload

```json id="jlwm1v"
{
  "patch_attempt_id": "patch_uuid",
  "repository_id": "repo_uuid",
  "validation_status": "passed"
}
```

---

# 9. Merge Request Flow

## Purpose

Triggered when a remediation MR is created.

---

## Event: `mr.created`

### Emitted By

```text id="jlwm8k"
gitlab_integration
```

### Consumed By

```text id="jlwm4n"
dashboard_service
notification_service
audit_logger
```

### Example Payload

```json id="jlwm2x"
{
  "merge_request_id": "mr_uuid",
  "repository_id": "repo_uuid",
  "title": "Fix CVE-2026-1234",
  "status": "opened"
}
```

---

# Correlation IDs

Every workflow execution must share a common:

```text id="jlwm5s"
correlation_id
```

This allows:

* full workflow tracing,
* debugging,
* event replay,
* and observability.

---

# Event Persistence

All emitted events must be:

* persisted to MongoDB,
* replayable,
* timestamped,
* queryable.

Events are stored inside:

```text id="jlwm7s"
events
```

collection.

---

# Retry Strategy

Event consumers must support:

* retryable execution,
* idempotent handling,
* exponential backoff,
* dead-letter logging.

---

# Idempotency Rules

Consumers must safely handle duplicate events.

Every event handler must:

* verify processing state,
* avoid duplicate writes,
* maintain deterministic outcomes.

---

# Event Ownership Rules

| Event Domain | Owning Service     |
| ------------ | ------------------ |
| vuln.*       | vuln_intelligence  |
| patch.*      | remediation_engine |
| ci.*         | gitlab_integration |
| mr.*         | gitlab_integration |

Only the owning service may emit events in its domain.

---

# Event Observability

All events must support:

* structured logging,
* workflow tracing,
* execution timing,
* replay debugging.

---

# Event Replay Philosophy

The architecture intentionally supports:

* replayable workflows,
* deterministic debugging,
* and demo reproducibility.

This is critical for:

* hackathon demos,
* debugging agent workflows,
* and failure recovery testing.

---

# MVP Event Scope

The MVP intentionally limits event complexity.

Included:

* vulnerability lifecycle,
* remediation lifecycle,
* CI lifecycle,
* MR lifecycle.

Excluded:

* distributed sagas,
* event versioning frameworks,
* complex orchestration engines,
* multi-region event replication.

---

# Event System Philosophy

The event system prioritizes:

* workflow clarity,
* observability,
* deterministic orchestration,
* and modular development.

The goal is:

> autonomous workflows without orchestration chaos.
