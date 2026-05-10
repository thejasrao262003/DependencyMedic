# DependencyMedic — Prompt Engineering Guide

# Purpose

This document defines the standardized prompts, AI interaction patterns, and prompting rules used during development of DependencyMedic.

The goals are:

* consistent AI-generated code,
* architecture stability,
* reduced hallucinations,
* predictable implementations,
* and high-quality vibe coding workflows.

This document acts as:

> the AI collaboration operating manual.

---

# Prompt Engineering Philosophy

AI coding agents perform best when:

* context is structured,
* scope is constrained,
* architecture is explicit,
* and output expectations are deterministic.

The project intentionally uses:

# spec-driven AI development

instead of:

# freeform prompting.

---

# Golden Rules

Every implementation prompt must:

* reference existing architecture,
* define exact scope boundaries,
* specify affected files,
* request deterministic behavior,
* and forbid architectural deviations.

---

# Mandatory Context Files

Before implementing any feature, always provide Claude with:

```text id="jlwm1h"
project_overview.md
engineering_guidelines.md
architecture.md
repo_structure.md
database_schema.md
event_flow.md
agents.md
api_contracts.md
workflows.md
implementation_plan.md
```

---

# Prompting Hierarchy

Prompts should follow this hierarchy:

```text id="’wini3h"
1. Architecture Context
2. Workflow Context
3. Service Scope
4. File Scope
5. Input/Output Expectations
6. Constraints
7. Deliverables
```

---

# Core Prompt Template

Use this template for all feature implementation tasks.

---

## Standard Feature Prompt

```text id="’wini5h"
You are implementing a feature for DependencyMedic.

Read and strictly follow:
- architecture.md
- engineering_guidelines.md
- repo_structure.md
- event_flow.md
- workflows.md
- database_schema.md

Task:
[FEATURE DESCRIPTION]

Requirements:
- Follow repository structure exactly.
- Do not introduce new architectural patterns.
- Reuse shared schemas where possible.
- Use structured logging.
- Emit events according to event_flow.md.
- Keep functions small and composable.
- Add proper typing everywhere.
- Add unit tests.
- Add integration-safe error handling.
- Do not generate placeholder code.
- Do not skip implementation details.

Output:
- complete file implementations
- updated imports
- tests
- required schemas
- event producers/consumers
```

---

# Service-Specific Prompt Templates

---

# Vulnerability Intelligence Prompt

```text id="’wini7h"
Implement the vulnerability ingestion workflow for DependencyMedic.

Context:
- architecture.md
- workflows.md
- event_flow.md
- database_schema.md

Requirements:
- Poll NVD API
- Normalize CVEs
- Deduplicate advisories
- Persist vulnerabilities
- Emit vuln.discovered event

Constraints:
- Async Python only
- FastAPI compatible
- MongoDB persistence
- Redis Streams events
- Structured logging mandatory

Deliverables:
- ingestion service
- schemas
- DB models
- event publisher
- tests
```

---

# Reachability Analysis Prompt

```text id="’wini9h"
Implement the reachability analysis workflow.

Requirements:
- Generate SBOM
- Build dependency graph
- Match vulnerable packages
- Compute exploitability confidence
- Emit vuln.assessed and vuln.scored

Constraints:
- Prefer deterministic analysis first
- LLM usage only for contextual reasoning
- Persist assessments to MongoDB
- Add confidence scoring

Deliverables:
- analyzers
- graph traversal
- scoring engine
- tests
```

---

# Patch Generation Prompt

```text id="’wini1i"
Implement the remediation engine.

Requirements:
- Create remediation branch
- Update dependency versions
- Regenerate lockfiles
- Commit patch changes
- Emit patch.generated

Constraints:
- GitLab API only
- No direct merge to main
- Retry-safe execution
- Idempotent workflows

Deliverables:
- patch generators
- git helpers
- dependency updaters
- tests
```

---

# CI Failure Analysis Prompt

```text id="’wini3i"
Implement the CI failure analysis workflow.

Requirements:
- Parse GitLab CI logs
- Extract stack traces
- Identify probable root causes
- Recommend retry actions
- Trigger retry workflow

Constraints:
- Deterministic parsing first
- LLM only for reasoning
- Maximum 2 retries
- Persist retry metadata

Deliverables:
- log parsers
- retry engine
- failure classifier
- tests
```

---

# Frontend Prompt Template

```text id="’wini5i"
Implement the frontend dashboard feature for DependencyMedic.

Requirements:
- React + TypeScript
- TailwindCSS
- Use existing API contracts
- Show loading/error states
- Responsive layout

Constraints:
- No mock APIs
- No inline hardcoded data
- Use typed API clients
- Keep components modular

Deliverables:
- pages
- components
- hooks
- API integration
```

---

# Debugging Prompt Template

```text id="’wini7i"
Analyze the following issue in DependencyMedic.

Context:
[PASTE ERROR]

Requirements:
- Identify root cause
- Explain architectural impact
- Propose minimal fix
- Avoid unrelated refactors
- Preserve event contracts

Output:
- root cause
- affected services
- exact code changes
- regression risks
```

---

# Refactoring Prompt Template

```text id="’wini9i"
Refactor the following implementation.

Goals:
- improve readability
- reduce coupling
- improve typing
- preserve behavior

Constraints:
- no architecture changes
- no new abstractions unless necessary
- preserve existing event contracts
- preserve API compatibility

Output:
- updated implementation
- explanation of changes
```

---

# Rules for Large Features

Large implementations must be split into:

# incremental prompts

Never ask Claude to:

* implement entire services at once,
* generate massive files blindly,
* or redesign architecture mid-implementation.

---

# Recommended Prompt Size

Optimal prompt scope:

```text id="’wini1j"
1 workflow
OR
1 service
OR
1 feature slice
```

Avoid:

```text id="’wini3j"
entire backend generation
```

---

# Mandatory Constraints

Every implementation prompt should include:

```text id="’wini5j"
Do not introduce unnecessary abstractions.
Do not overengineer.
Do not redesign architecture.
Follow existing event contracts.
Reuse shared modules.
Keep implementations production-readable.
```

---

# Anti-Hallucination Rules

Always explicitly specify:

* framework versions,
* expected libraries,
* folder paths,
* event names,
* schema names,
* and API contracts.

Never assume Claude will infer them correctly.

---

# Recommended AI Workflow

Recommended vibe coding workflow:

```text id="’wini7j"
Read docs
   ↓
Implement small feature
   ↓
Run locally
   ↓
Fix integration issues
   ↓
Commit
   ↓
Repeat
```

---

# Commit Strategy

Recommended commit pattern:

```text id="’wini9j"
feat(vuln-intelligence): add NVD ingestion workflow
feat(remediation): implement patch generation
fix(events): resolve duplicate event emission
```

---

# Context Window Strategy

Do NOT paste:

* entire repositories,
* huge files,
* or unnecessary logs.

Instead provide:

* exact files,
* exact interfaces,
* exact errors,
* and exact expectations.

---

# Preferred Development Style

Preferred implementation style:

* modular
* typed
* observable
* deterministic
* composable
* workflow-oriented

Avoid:

* magic abstractions
* premature optimization
* excessive inheritance
* hidden side effects

---

# Prompt Failure Recovery

If Claude starts:

* changing architecture,
* introducing unnecessary complexity,
* or hallucinating integrations,

reset by providing:

```text id="’wini1k"
Follow architecture.md strictly.
Do not redesign the system.
Only implement the requested feature.
```

---

# MVP AI Usage Philosophy

The project uses AI for:

* implementation acceleration,
* structured reasoning,
* and orchestration assistance.

The project does NOT use AI for:

* uncontrolled architecture evolution,
* hidden automation,
* or replacing deterministic engineering practices.

---

# Final Philosophy

Good prompting is:

# architecture enforcement.

The goal is:

> using AI to accelerate implementation without losing system coherence.
