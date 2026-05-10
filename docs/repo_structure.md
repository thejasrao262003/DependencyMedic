# DependencyMedic — Repository Structure

# Purpose

This document defines the canonical repository structure for DependencyMedic.

The goal is to:

* keep the codebase modular,
* support feature-based ownership,
* prevent architectural drift,
* simplify AI-assisted development,
* and ensure predictable code organization.

All contributors and AI coding agents must follow this structure.

---

# High-Level Repository Structure

```text id="3y9rj1"
dependency-medic/
│
├── backend/
├── frontend/
├── infra/
├── docs/
├── demo/
├── scripts/
├── .github/
├── docker-compose.yml
├── .env.example
├── README.md
└── Makefile
```

---

# Root Directory Structure

## `/backend`

Contains all backend services, agents, APIs, event consumers, shared schemas, and testing infrastructure.

---

## `/frontend`

Contains the React dashboard application.

---

## `/infra`

Contains infrastructure configuration and deployment-related files.

---

## `/docs`

Contains all specification-driven development documents.

---

## `/demo`

Contains demo-specific repositories, fixtures, vulnerable projects, and seeded workflows.

---

## `/scripts`

Contains utility scripts for setup, seeding, local development, and automation.

---

## `docker-compose.yml`

Defines the entire local orchestration environment.

---

## `.env.example`

Defines all required environment variables.

---

## `Makefile`

Provides simplified local development commands.

Examples:

```bash id="7yx0s0"
make up
make test
make lint
make seed-demo
```

---

# Backend Structure

```text id="kqk5eu"
backend/
│
├── services/
├── shared/
├── tests/
├── scripts/
├── requirements/
└── pyproject.toml
```

---

# `/backend/services`

Each service owns a specific workflow domain.

Services must:

* be independently runnable,
* expose APIs/events,
* and avoid direct coupling.

---

# Backend Services Structure

```text id="f0y3uk"
backend/services/
│
├── vuln_intelligence/
├── reachability_analysis/
├── remediation_engine/
├── gitlab_integration/
└── api_gateway/
```

---

# 1. `/vuln_intelligence`

Handles:

* CVE ingestion,
* feed normalization,
* vulnerability matching,
* repository impact detection.

Structure:

```text id="8i6f5g"
vuln_intelligence/
│
├── api/
├── services/
├── consumers/
├── producers/
├── models/
├── schemas/
├── agents/
├── utils/
├── config/
└── main.py
```

---

# 2. `/reachability_analysis`

Handles:

* SBOM generation,
* dependency graphing,
* exploitability analysis,
* risk scoring.

Structure:

```text id="wvcr0f"
reachability_analysis/
│
├── analyzers/
├── scanners/
├── agents/
├── services/
├── models/
├── schemas/
├── utils/
└── main.py
```

---

# 3. `/remediation_engine`

Handles:

* patch generation,
* dependency upgrades,
* lockfile updates,
* CI retry workflows.

Structure:

```text id="rbn3z9"
remediation_engine/
│
├── patchers/
├── retry_engine/
├── ci_analysis/
├── agents/
├── services/
├── models/
├── schemas/
├── utils/
└── main.py
```

---

# 4. `/gitlab_integration`

Handles:

* GitLab APIs,
* pipeline orchestration,
* MR creation,
* branch management,
* webhook processing.

Structure:

```text id="7mrkq7"
gitlab_integration/
│
├── clients/
├── webhooks/
├── pipelines/
├── merge_requests/
├── services/
├── models/
├── schemas/
├── utils/
└── main.py
```

---

# 5. `/api_gateway`

Handles:

* frontend-facing APIs,
* aggregated responses,
* auth middleware,
* API routing.

Structure:

```text id="0ubq4w"
api_gateway/
│
├── routes/
├── middleware/
├── dependencies/
├── services/
├── schemas/
├── utils/
└── main.py
```

---

# Shared Backend Modules

```text id="jlwmk1"
backend/shared/
│
├── events/
├── schemas/
├── models/
├── enums/
├── utils/
├── constants/
└── logging/
```

---

# Shared Module Responsibilities

## `/events`

Shared event payload definitions.

Examples:

```text id="4qsk8z"
vuln_discovered.py
patch_generated.py
mr_created.py
```

---

## `/schemas`

Shared Pydantic DTOs.

Examples:

```text id="9h3u8h"
vulnerability.py
pipeline_result.py
patch_result.py
```

---

## `/models`

Shared database models.

---

## `/enums`

Shared enums and constants.

---

## `/utils`

Shared helper functions.

---

# Frontend Structure

```text id="hij1ga"
frontend/
│
├── src/
├── public/
├── tests/
├── package.json
└── vite.config.ts
```

---

# Frontend Source Structure

```text id="2z0g0v"
src/
│
├── components/
├── pages/
├── hooks/
├── services/
├── stores/
├── types/
├── utils/
├── layouts/
└── routes/
```

---

# Frontend Directory Responsibilities

## `/components`

Reusable UI components.

Examples:

```text id="t4pdnr"
VulnerabilityCard.tsx
PipelineStatusPanel.tsx
MergeRequestTimeline.tsx
```

---

## `/pages`

Top-level dashboard pages.

Examples:

```text id="1ph3d3"
DashboardPage.tsx
VulnerabilityDetailsPage.tsx
```

---

## `/hooks`

Frontend hooks.

Examples:

```text id="cwt5fu"
useVulnerabilities.ts
usePipelineStatus.ts
```

---

## `/services`

Frontend API clients.

---

## `/stores`

Global frontend state.

---

# Tests Structure

```text id="fg03gu"
backend/tests/
│
├── unit/
├── integration/
├── e2e/
├── fixtures/
└── mocks/
```

---

# Test Categories

## `/unit`

Isolated service tests.

---

## `/integration`

Cross-service workflow tests.

---

## `/e2e`

Full remediation workflow tests.

Example:

```text id="jlwmnh"
CVE → Patch → CI → MR
```

---

## `/fixtures`

Static demo/test data.

Examples:

```text id="ps6t7x"
critical_cve.json
failed_pipeline_logs.txt
vulnerable_repo/
```

---

# Demo Structure

```text id="o9f0s0"
demo/
│
├── vulnerable_services/
├── demo_scenarios/
├── seed_data/
└── scripts/
```

---

# Demo Responsibilities

## `/vulnerable_services`

Contains intentionally vulnerable microservices used during the demo.

Examples:

```text id="m6r9s0"
payment-service
auth-service
inventory-service
```

---

## `/demo_scenarios`

Contains reproducible demo workflows.

Examples:

```text id="0u3i8x"
critical_log4j_flow.md
broken_pipeline_retry.md
```

---

# Infrastructure Structure

```text id="h04dga"
infra/
│
├── docker/
├── cloud_run/
├── monitoring/
└── nginx/
```

---

# Scripts Structure

```text id="mq5k0m"
scripts/
│
├── setup/
├── seed/
├── migrations/
└── dev/
```

---

# Naming Rules

## Files

Use:

```text id="p9n7j3"
snake_case
```

---

## React Components

Use:

```text id="9jv3e4"
PascalCase
```

---

## Test Files

Use:

```text id="xvnz4r"
test_<feature>.py
```

Examples:

```text id="5vdf0z"
test_patch_generation.py
test_ci_retry_flow.py
```

---

# Forbidden Patterns

The following are NOT allowed:

* deeply nested utility folders
* duplicate schemas across services
* service-to-service DB access
* circular imports
* random scripts outside `/scripts`
* unstructured event payloads
* undocumented shared modules

---

# Repository Philosophy

The repository structure prioritizes:

* rapid implementation,
* low integration friction,
* feature ownership,
* observability,
* and AI-assisted maintainability.

The goal is:

> predictable evolution without architectural chaos.
