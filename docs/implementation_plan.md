# DependencyMedic — Implementation Plan

# Purpose

This document defines the implementation roadmap for DependencyMedic.

The goals are:

* predictable execution,
* parallel development,
* stable integrations,
* rapid MVP delivery,
* and reduced implementation chaos.

This document acts as:

> the execution blueprint for the project.

---

# Implementation Philosophy

The MVP is designed around:

* rapid iteration,
* visible workflows,
* demo reliability,
* and incremental integration.

The priority is NOT:

* production-scale architecture,
* enterprise-grade abstractions,
* or perfect infrastructure.

The priority is:

> building a believable autonomous remediation system end-to-end.

---

# Core MVP Goal

The MVP is considered successful if it can demonstrate:

```text id="jlwm1p"
Critical CVE
    ↓
Affected Repository Detection
    ↓
Reachability Analysis
    ↓
Patch Generation
    ↓
GitLab CI Validation
    ↓
CI Failure Recovery
    ↓
Merge Request Creation
```

Everything in the implementation plan exists to support this demo flow.

---

# Team Ownership Model

The project uses:

# feature-based vertical ownership

Each developer owns:

* backend,
* database,
* events,
* frontend,
* testing,
* and integration

for their workflow domain.

---

# Ownership Split

---

# Developer A — Threat Intelligence Domain

## Owns

* vulnerability ingestion
* CVE normalization
* repository matching
* SBOM generation
* reachability analysis
* risk scoring
* vulnerability dashboard
* vulnerability event flows

---

## Primary Services

```text id="jlwm3p"
vuln_intelligence
reachability_analysis
```

---

## Primary Events

```text id="jlwm5p"
vuln.discovered
vuln.matched
vuln.assessed
vuln.scored
```

---

# Developer B — Remediation Domain

## Owns

* patch generation
* dependency upgrades
* CI orchestration
* GitLab integration
* merge request creation
* retry logic
* remediation dashboard
* remediation workflows

---

## Primary Services

```text id="jlwm7p"
remediation_engine
gitlab_integration
```

---

## Primary Events

```text id="’wini9p"
patch.generated
ci.failed
patch.validated
mr.created
```

---

# Shared Ownership

The following areas are shared:

| Area                | Responsibility |
| ------------------- | -------------- |
| shared schemas      | both           |
| event contracts     | both           |
| repo structure      | both           |
| Docker Compose      | both           |
| demo scenarios      | both           |
| integration testing | both           |

---

# Development Phases

The implementation is divided into:

# 6 phases

Each phase should produce:

* runnable code,
* observable workflows,
* and testable outputs.

---

# Phase 1 — Foundation Setup

# Goal

Establish the shared development foundation.

---

# Deliverables

## Repository Setup

* GitHub mono repo
* branch protection
* README
* docs structure

---

## Infrastructure

* Docker Compose
* MongoDB
* Redis
* backend skeleton
* frontend skeleton

---

## Shared Modules

* event schemas
* shared DTOs
* logging utilities
* environment config

---

## Local Tooling

* Makefile
* linting
* formatting
* pytest setup
* frontend tooling

---

# Exit Criteria

* project boots locally,
* MongoDB connected,
* Redis connected,
* frontend loads,
* backend API reachable.

---

# Phase 2 — Vulnerability Intelligence

# Goal

Implement CVE ingestion and repository impact detection.

---

# Deliverables

## Vulnerability Feed Ingestion

* NVD ingestion
* OSV ingestion
* normalization
* deduplication

---

## Repository Management

* GitLab repo registration
* repository metadata sync

---

## Dependency Analysis

* SBOM generation
* dependency extraction
* repository matching

---

## Dashboard

* vulnerabilities table
* repository list
* severity filtering

---

## Events

* vuln.discovered
* vuln.matched

---

# Exit Criteria

Demo should show:

```text id="’wini1q"
New CVE
   ↓
Stored in DB
   ↓
Affected repositories identified
```

---

# Phase 3 — Reachability & Risk Analysis

# Goal

Determine exploitability and prioritize remediation.

---

# Deliverables

## Reachability Analysis

* dependency graph traversal
* reachable package detection
* evidence generation

---

## Risk Scoring

* CVSS integration
* EPSS scoring
* confidence scoring

---

## Dashboard

* risk visualization
* exploitability details
* evidence display

---

## Events

* vuln.assessed
* vuln.scored

---

# Exit Criteria

Demo should show:

```text id="’wini3q"
Critical CVE
   ↓
Reachability analysis
   ↓
Risk score generated
```

---

# Phase 4 — Patch Generation & GitLab Integration

# Goal

Generate remediation patches and orchestrate GitLab workflows.

---

# Deliverables

## Patch Generation

* dependency upgrades
* manifest updates
* lockfile regeneration

---

## GitLab Integration

* branch creation
* commit automation
* MR creation
* pipeline triggering

---

## Dashboard

* remediation status
* branch visualization
* MR tracking

---

## Events

* patch.generated
* ci.started

---

# Exit Criteria

Demo should show:

```text id="
```


Continue from the previous section like this:

```text id="’wini5q"
Critical CVE
   ↓
Patch generated
   ↓
GitLab branch created
   ↓
Pipeline triggered
```

---

# Phase 5 — CI Failure Recovery

# Goal

Implement autonomous CI failure analysis and retry orchestration.

This phase is:

# the most impressive part of the demo.

---

# Deliverables

## CI Failure Analysis

* GitLab log collection
* stack trace extraction
* failure classification

---

## Retry Engine

* retry orchestration
* adjusted patch generation
* retry pipeline triggering

---

## Agent Reasoning

* root cause summaries
* retry recommendations
* confidence scoring

---

## Dashboard

* pipeline timeline
* retry visualization
* failure analysis UI

---

## Events

* ci.failed
* patch.retry_requested
* pipeline.completed

---

# Exit Criteria

Demo should show:

```text id="’wini7q"
Pipeline fails
    ↓
Agent analyzes logs
    ↓
Retry patch generated
    ↓
Pipeline succeeds
```

---

# Phase 6 — Demo Readiness & Polish

# Goal

Prepare a stable, reproducible, and visually impressive hackathon demo.

---

# Deliverables

## Demo Environment

* seeded vulnerabilities
* intentionally vulnerable repos
* deterministic workflows
* demo fixtures

---

## Frontend Polish

* workflow timeline
* event visualization
* pipeline status indicators
* remediation dashboards

---

## Observability

* structured logs
* workflow tracing
* correlation IDs
* event inspection

---

## Demo Scripts

* walkthrough flow
* narration points
* failure simulation scenarios

---

## Video Preparation

* demo recording setup
* prepared demo script
* deterministic replayable flows

---

# Exit Criteria

Demo should reliably execute:

```text id="’wini9q"
CVE
  ↓
Repository Match
  ↓
Risk Analysis
  ↓
Patch Generation
  ↓
CI Validation
  ↓
Retry Recovery
  ↓
MR Creation
```

without manual debugging during presentation.

---

# Recommended Development Order

The recommended implementation order is:

```text id="’wini1r"
1. Infrastructure Setup
2. Shared Schemas & Events
3. Vulnerability Ingestion
4. Repository Management
5. SBOM Generation
6. Reachability Analysis
7. Risk Scoring
8. Patch Generation
9. GitLab Integration
10. CI Validation
11. Retry Engine
12. Frontend Polish
13. Demo Preparation
```

---

# Daily Development Workflow

Each developer should follow:

```text id="’wini3r"
Pull latest changes
    ↓
Develop feature vertically
    ↓
Run local integration tests
    ↓
Validate emitted events
    ↓
Push branch
    ↓
Daily integration sync
```

---

# Integration Strategy

Integration should happen:

# continuously

not:

# at the end.

---

# Integration Rules

Every feature must:

* emit valid events,
* respect shared schemas,
* support Docker Compose execution,
* and remain independently testable.

---

# Testing Strategy

The implementation prioritizes:

# workflow testing

over excessive isolated unit testing.

---

# Required Test Categories

## Unit Tests

* scoring logic
* event validation
* parsers

---

## Integration Tests

* Redis + Mongo workflows
* service communication
* event orchestration

---

## E2E Tests

* CVE → MR flow
* CI retry workflow
* remediation pipeline

---

# Demo-First Development

All development decisions should prioritize:

* demo reliability,
* visual orchestration,
* workflow clarity,
* and reproducibility.

If a feature does not improve:

* demo realism,
* workflow quality,
* or orchestration visibility,

it should be deprioritized.

---

# Scope Control Rules

The following must NOT be added during MVP development:

* Kubernetes
* Kafka
* Multi-tenancy
* Production deployment automation
* Runtime production agents
* Complex RBAC systems
* Advanced distributed systems abstractions

---

# Risk Management

## Major Risks

| Risk                   | Mitigation                     |
| ---------------------- | ------------------------------ |
| GitLab API instability | Local retry logic + mocks      |
| CI unpredictability    | Controlled demo repos          |
| LLM hallucinations     | Deterministic validation gates |
| Integration failures   | Event contracts frozen early   |
| Scope explosion        | Strict MVP boundaries          |

---

# Demo Philosophy

The goal of the demo is NOT:

> “fully autonomous production remediation.”

The goal is:

> demonstrating believable AI-driven remediation orchestration.

The demo should feel:

* operational,
* intelligent,
* observable,
* and realistic.

---

# Success Criteria

The MVP is successful if it can:

* ingest real vulnerabilities,
* identify impacted repositories,
* generate remediation patches,
* trigger GitLab pipelines,
* recover from at least one CI failure,
* create remediation merge requests,
* and demonstrate end-to-end orchestration live.

---

# Final Philosophy

This implementation plan prioritizes:

* rapid execution,
* integration stability,
* workflow realism,
* and hackathon demo quality.

The goal is:

> a believable autonomous remediation system built fast without architectural chaos.
