# DependencyMedic — API Contracts

# Purpose

This document defines all public and internal API contracts used by DependencyMedic.

The goals are:

* predictable service interfaces,
* frontend/backend consistency,
* stable integration contracts,
* and simplified AI-assisted development.

All APIs must:

* follow REST conventions,
* return structured responses,
* support observability,
* and remain backward compatible during MVP development.

---

# API Philosophy

The API layer is intentionally:

* thin,
* predictable,
* strongly typed,
* and frontend-oriented.

Business logic should live inside:

* services,
* workflows,
* and agents.

APIs should primarily:

* expose workflows,
* aggregate state,
* and orchestrate user interactions.

---

# Base URL Structure

## Local Development

```text id="jlwm2c"
http://localhost:8000/api/v1
```

---

# Standard Response Format

All responses must follow:

```json id="jlwm5c"
{
  "success": true,
  "data": {},
  "error": null
}
```

---

# Standard Error Format

```json id="jlwm7c"
{
  "success": false,
  "data": null,
  "error": {
    "code": "PIPELINE_FAILED",
    "message": "Pipeline validation failed"
  }
}
```

---

# Authentication (MVP)

The MVP uses:

* simple API token authentication,
* environment-configured admin access,
* and optional GitLab OAuth later.

Production-grade RBAC is intentionally excluded from MVP scope.

---

# API Categories

```text id="jlwm9c"
1. Vulnerability APIs
2. Repository APIs
3. Risk Assessment APIs
4. Patch & Remediation APIs
5. Pipeline APIs
6. Merge Request APIs
7. Event APIs
8. Health & System APIs
```

---

# 1. Vulnerability APIs

Handles:

* CVE visibility,
* vulnerability browsing,
* filtering,
* and details retrieval.

---

## GET `/vulnerabilities`

### Purpose

Fetch all vulnerabilities.

---

### Query Parameters

| Parameter | Type   | Description        |
| --------- | ------ | ------------------ |
| severity  | string | Filter by severity |
| status    | string | active/resolved    |
| page      | int    | Pagination         |
| limit     | int    | Page size          |

---

### Example Request

```http id="jlwm1c"
GET /api/v1/vulnerabilities?severity=critical
```

---

### Example Response

```json id="jlwm3c"
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "cve_id": "CVE-2026-1234",
        "severity": "critical",
        "summary": "Prototype pollution in lodash",
        "published_at": "2026-05-10T12:00:00Z"
      }
    ],
    "total": 1
  },
  "error": null
}
```

---

## GET `/vulnerabilities/{vulnerability_id}`

### Purpose

Fetch detailed vulnerability information.

---

### Example Response

```json id="jlwm6c"
{
  "success": true,
  "data": {
    "id": "uuid",
    "cve_id": "CVE-2026-1234",
    "severity": "critical",
    "cvss_score": 9.8,
    "epss_score": 0.92,
    "affected_packages": [],
    "references": []
  },
  "error": null
}
```

---

# 2. Repository APIs

Handles:

* monitored repositories,
* repository metadata,
* dependency state.

---

## GET `/repositories`

### Purpose

Fetch monitored repositories.

---

### Example Response

```json id="jlwm8c"
{
  "success": true,
  "data": [
    {
      "id": "repo_uuid",
      "repo_name": "payment-service",
      "languages": [
        "python"
      ],
      "status": "active"
    }
  ],
  "error": null
}
```

---

## POST `/repositories`

### Purpose

Register a new repository.

---

### Example Request

```json id="jlwm0c"
{
  "repo_url": "https://gitlab.com/org/payment-service"
}
```

---

### Example Response

```json id="jlwm2d"
{
  "success": true,
  "data": {
    "repository_id": "repo_uuid"
  },
  "error": null
}
```

---

# 3. Risk Assessment APIs

Handles:

* exploitability analysis,
* risk scoring,
* and reachability results.

---

## GET `/repositories/{repository_id}/risks`

### Purpose

Fetch repository risk assessments.

---

### Example Response

```json id="jlwm4d"
{
  "success": true,
  "data": [
    {
      "vulnerability_id": "vuln_uuid",
      "risk_score": 94,
      "risk_level": "critical",
      "reachable": true,
      "confidence_score": 0.91
    }
  ],
  "error": null
}
```

---

# 4. Patch & Remediation APIs

Handles:

* remediation generation,
* patch workflows,
* retry orchestration.

---

## POST `/remediations/generate`

### Purpose

Trigger remediation patch generation.

---

### Example Request

```json id="jlwm6d"
{
  "repository_id": "repo_uuid",
  "vulnerability_id": "vuln_uuid"
}
```

---

### Example Response

```json id="jlwm8d"
{
  "success": true,
  "data": {
    "patch_attempt_id": "patch_uuid",
    "status": "started"
  },
  "error": null
}
```

---

## GET `/remediations/{patch_attempt_id}`

### Purpose

Fetch remediation attempt status.

---

### Example Response

```json id="jlwm0d"
{
  "success": true,
  "data": {
    "patch_attempt_id": "patch_uuid",
    "status": "validated",
    "branch_name": "fix/cve-2026-1234",
    "confidence_score": 0.87
  },
  "error": null
}
```

---

# 5. Pipeline APIs

Handles:

* GitLab CI visibility,
* pipeline tracking,
* retry inspection.

---

## GET `/pipelines`

### Purpose

Fetch pipeline runs.

---

### Example Response

```json id="jlwm2e"
{
  "success": true,
  "data": [
    {
      "pipeline_id": "pipeline_uuid",
      "repository_id": "repo_uuid",
      "status": "failed",
      "failed_stage": "unit_tests"
    }
  ],
  "error": null
}
```

---

## GET `/pipelines/{pipeline_id}`

### Purpose

Fetch detailed pipeline information.

---

### Example Response

```json id="jlwm4e"
{
  "success": true,
  "data": {
    "pipeline_id": "pipeline_uuid",
    "status": "failed",
    "logs_url": "https://gitlab.com/logs",
    "retry_attempted": true
  },
  "error": null
}
```

---

# 6. Merge Request APIs

Handles:

* remediation MRs,
* approval workflows,
* merge visibility.

---

## GET `/merge-requests`

### Purpose

Fetch remediation merge requests.

---

### Example Response

```json id="jlwm6e"
{
  "success": true,
  "data": [
    {
      "merge_request_id": "mr_uuid",
      "title": "Fix CVE-2026-1234",
      "status": "opened",
      "approved": false
    }
  ],
  "error": null
}
```

---

## POST `/merge-requests/{merge_request_id}/approve`

### Purpose

Approve remediation merge request.

---

### Example Response

```json id="jlwm8e"
{
  "success": true,
  "data": {
    "approved": true
  },
  "error": null
}
```

---

# 7. Event APIs

Handles:

* workflow observability,
* event inspection,
* debugging support.

---

## GET `/events`

### Purpose

Fetch emitted system events.

---

### Query Parameters

| Parameter      | Type   |
| -------------- | ------ |
| event_type     | string |
| correlation_id | string |

---

### Example Response

```json id="jlwm0e"
{
  "success": true,
  "data": [
    {
      "event_type": "patch.generated",
      "timestamp": "ISO8601",
      "source_service": "remediation_engine"
    }
  ],
  "error": null
}
```

---

# 8. Health & System APIs

Handles:

* service health,
* observability,
* readiness checks.

---

## GET `/health`

### Purpose

System health check.

---

### Example Response

```json id="jlwm2f"
{
  "success": true,
  "data": {
    "status": "healthy",
    "services": {
      "mongodb": "healthy",
      "redis": "healthy",
      "gitlab": "healthy"
    }
  },
  "error": null
}
```

---

# Internal Service APIs

Internal services may expose:

* private APIs,
* internal webhooks,
* orchestration endpoints.

These APIs:

* must remain undocumented externally,
* must not be consumed directly by frontend clients.

---

# API Versioning

All APIs must use:

```text id="jlwm4f"
/api/v1
```

Future breaking changes require:

```text id="jlwm6f"
/api/v2
```

---

# Pagination Rules

All list APIs must support:

* page
* limit

Default:

```text id="jlwm8f"
page=1
limit=20
```

Maximum:

```text id="jlwm0f"
limit=100
```

---

# Error Handling Philosophy

APIs should:

* fail visibly,
* fail consistently,
* provide actionable messages,
* avoid leaking internal implementation details.

---

# API Observability

All APIs must support:

* structured request logging,
* request timing,
* correlation IDs,
* error tracing.

---

# OpenAPI / Swagger

FastAPI auto-generated Swagger documentation must remain enabled during MVP development.

Available at:

```text id="jlwm2g"
/docs
```

---

# API Philosophy

The API layer prioritizes:

* frontend consistency,
* integration simplicity,
* observability,
* and predictable workflows.

The goal is:

> stable interfaces without unnecessary backend complexity.
