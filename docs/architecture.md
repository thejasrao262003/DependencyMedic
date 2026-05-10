# DependencyMedic — Architecture

# System Overview

DependencyMedic is an event-driven autonomous remediation orchestration system designed to monitor software supply chain vulnerabilities and coordinate secure remediation workflows across GitLab repositories.

The architecture is intentionally:

* modular,
* observable,
* locally runnable,
* AI-assisted-development friendly,
* and optimized for hackathon implementation speed.

The system is NOT designed as:

* a distributed enterprise platform,
* a Kubernetes-native system,
* or a massively scalable SaaS architecture.

The focus is:

> reliable orchestration of autonomous remediation workflows.

---

# Architectural Principles

1. Event-driven workflows over tightly coupled services.
2. Specialized agents over monolithic orchestration.
3. Deterministic tooling before LLM reasoning.
4. Human-supervised autonomy over unrestricted automation.
5. Shared contracts over implicit integrations.
6. Local-first development and testing.
7. Simplicity over premature scalability.

---

# High-Level Architecture

```text id="vhl7pa"
                    ┌────────────────────┐
                    │ Vulnerability Feeds │
                    │ NVD / OSV / GHSA   │
                    └─────────┬──────────┘
                              │
                              ▼
                 ┌────────────────────────┐
                 │ Vulnerability Service  │
                 │  - CVE ingestion       │
                 │  - normalization       │
                 │  - repo matching       │
                 └─────────┬──────────────┘
                           │
                           ▼
                  ┌──────────────────────┐
                  │ Redis Event Streams  │
                  └─────────┬────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼

┌──────────────────────┐          ┌────────────────────────┐
│ Reachability Agent   │          │ Remediation Engine     │
│ - SBOM analysis      │          │ - patch generation     │
│ - exploitability     │          │ - dependency upgrades  │
│ - risk scoring       │          │ - CI retry logic       │
└──────────┬───────────┘          └──────────┬─────────────┘
           │                                  │
           ▼                                  ▼

   ┌─────────────────┐             ┌────────────────────┐
   │ MongoDB         │             │ GitLab Integration │
   │ vulnerabilities │             │ pipelines / MRs    │
   │ repositories    │             │ CI/CD orchestration│
   └─────────────────┘             └─────────┬──────────┘
                                              │
                                              ▼

                                 ┌────────────────────┐
                                 │ React Dashboard    │
                                 │ - vulnerabilities  │
                                 │ - pipelines        │
                                 │ - merge requests   │
                                 └────────────────────┘
```

---

# Core Services

The backend is split into modular services with clearly defined ownership boundaries.

---

# 1. Vulnerability Intelligence Service

## Responsibilities

* ingest CVEs from feeds,
* normalize vulnerability data,
* deduplicate advisories,
* map CVEs to repositories,
* generate vulnerability events.

## Inputs

* NVD feed
* OSV feed
* GitHub Security Advisories

## Outputs

Events:

```text id="2j5i0v"
vuln.discovered
vuln.matched
```

## Database Ownership

Collections:

```text id="9lr4cw"
vulnerabilities
repositories
dependency_snapshots
```

---

# 2. Reachability & Risk Analysis Service

## Responsibilities

* generate SBOMs,
* analyze dependency graphs,
* perform reachability analysis,
* compute exploitability confidence,
* generate risk scores.

## Tooling

* Syft
* govulncheck
* pip-audit
* npm audit

## Outputs

Events:

```text id="rqqsbl"
vuln.assessed
vuln.scored
```

## Notes

This service should prefer deterministic analysis before invoking LLM reasoning.

LLMs are used only for:

* contextual interpretation,
* remediation explanation,
* and confidence augmentation.

---

# 3. Remediation Engine

## Responsibilities

* generate dependency upgrade patches,
* update manifests and lockfiles,
* trigger GitLab CI pipelines,
* analyze CI failures,
* retry remediation attempts.

## Outputs

Events:

```text id="i6mqnf"
patch.generated
ci.started
ci.failed
patch.validated
```

## Retry Strategy

* maximum retry attempts: 2
* exponential backoff
* deterministic fixes first
* LLM-assisted retry second

---

# 4. GitLab Integration Service

## Responsibilities

* repository synchronization,
* pipeline triggering,
* merge request creation,
* branch management,
* webhook handling.

## GitLab Operations

* create remediation branches
* push commits
* open merge requests
* fetch CI logs
* assign reviewers

## Outputs

Events:

```text id="nxxu7h"
mr.created
mr.updated
pipeline.completed
```

---

# 5. API Gateway

## Responsibilities

* expose REST APIs,
* aggregate service responses,
* handle frontend communication,
* expose dashboard endpoints.

## APIs

Examples:

```text id="u5jkt9"
GET /vulnerabilities
GET /repositories
GET /merge-requests
POST /approve-remediation
```

---

# 6. Frontend Dashboard

## Responsibilities

* display vulnerabilities,
* show remediation progress,
* visualize pipelines,
* display merge request status,
* provide approval workflows.

## Technology

* React
* TailwindCSS

---

# Event-Driven Architecture

The entire system communicates using Redis Streams.

Services must:

* publish events,
* consume events,
* avoid direct coupling.

---

# Event Flow Example

```text id="9n8yur"
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
patch.validated
        ↓
mr.created
```

---

# Why Event-Driven?

The event-driven approach enables:

* loose coupling,
* independent feature ownership,
* parallel development,
* replayable workflows,
* and easier AI-assisted implementation.

This architecture is intentionally optimized for:

* two-person collaboration,
* feature isolation,
* and incremental integration.

---

# Database Architecture

MongoDB is used as the primary operational datastore.

## Why MongoDB?

* schema flexibility,
* rapid iteration,
* easy event storage,
* AI-development friendliness,
* JSON-native structures.

---

# Primary Collections

```text id="pb41o9"
vulnerabilities
repositories
dependency_snapshots
risk_assessments
patch_attempts
pipeline_runs
merge_requests
events
```

---

# Shared Module Architecture

Shared schemas, DTOs, and event definitions must live inside:

```text id="36wzgo"
backend/services/shared/
```

Shared modules include:

* event payloads
* API schemas
* database models
* enums
* utility types

---

# Agent Architecture

The system uses specialized agents instead of a single orchestrator agent.

## Current Agent Types

### Vulnerability Intelligence Agent

Handles:

* CVE ingestion
* normalization
* repository matching

---

### Reachability Agent

Handles:

* dependency analysis
* exploitability reasoning
* confidence scoring

---

### Patch Generation Agent

Handles:

* dependency upgrades
* lockfile generation
* compatibility remediation

---

### CI Failure Analysis Agent

Handles:

* CI log parsing
* retry reasoning
* patch adjustment recommendations

---

# AI Usage Boundaries

LLMs are allowed to:

* summarize vulnerabilities,
* explain remediation,
* analyze CI failures,
* suggest compatibility fixes.

LLMs are NOT trusted for:

* deterministic dependency matching,
* guaranteed exploitability proofs,
* unrestricted autonomous deployment,
* direct production merges.

---

# Deployment Architecture

The MVP uses Docker Compose for all local orchestration.

## Local Services

```text id="qhbv42"
frontend
backend
mongodb
redis
```

---

# Cloud Deployment

Deployment target:

* Google Cloud Run

Deployment scope:

* single environment only
* single organization demo
* non-production infrastructure

---

# Demo Architecture

The demo environment contains:

* multiple intentionally vulnerable microservices,
* GitLab repositories,
* seeded dependency vulnerabilities,
* CI pipelines,
* and remediation workflows.

The architecture prioritizes:

* visible orchestration,
* reproducible demos,
* deterministic workflows,
* and operational clarity.

---

# Service Ownership Strategy

The architecture is intentionally designed for feature-based ownership.

## Feature Domain 1

### Vulnerability Intelligence

Owns:

* ingestion
* SBOMs
* reachability
* risk scoring

---

## Feature Domain 2

### Remediation Orchestration

Owns:

* patch generation
* CI workflows
* GitLab integration
* merge requests

---

# Non-Goals

The MVP architecture intentionally avoids:

* Kubernetes orchestration,
* distributed service mesh,
* multi-region scaling,
* multi-tenant SaaS complexity,
* advanced infrastructure automation,
* runtime production deployment automation.

The focus is:

> delivering a believable and impressive autonomous remediation workflow.
