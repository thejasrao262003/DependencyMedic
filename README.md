# DependencyMedic

> The AI Security Engineer that never sleeps.

DependencyMedic is an autonomous AI-powered software supply chain defense system built for the Google Cloud Rapid Agent Hackathon.

The system continuously monitors vulnerability feeds, identifies impacted repositories, performs exploitability reasoning, generates dependency remediation patches, validates fixes through GitLab CI/CD pipelines, and orchestrates secure merge request workflows with human approval gates.

This is not a chatbot.
This is not another vulnerability dashboard.

DependencyMedic is designed to behave like an autonomous security engineer operating inside a modern software organization.

---

# Why DependencyMedic Exists

Modern software systems depend heavily on open-source packages.

A single application may contain:

* hundreds of direct dependencies,
* thousands of transitive dependencies,
* and a constantly evolving security attack surface.

When new vulnerabilities (CVEs) are discovered, engineering teams face several major problems:

* Security tools generate overwhelming alert noise.
* Most vulnerabilities are never properly triaged.
* Dependency updates frequently break CI pipelines.
* Patching workflows are slow and expensive.
* Critical vulnerabilities remain unresolved for weeks or months.

Existing tools typically stop at:

> “This dependency is vulnerable.”

DependencyMedic goes much further.

---

# What DependencyMedic Does

DependencyMedic autonomously orchestrates the full remediation workflow:

```text id="7rph9r"
CVE Feed
   ↓
Vulnerability Detection
   ↓
Repository Matching
   ↓
Reachability Analysis
   ↓
Risk Scoring
   ↓
Patch Generation
   ↓
GitLab CI Validation
   ↓
CI Failure Recovery
   ↓
Merge Request Creation
   ↓
Human Approval
```

---

# Core Capabilities

## Vulnerability Intelligence

* Monitor NVD, OSV.dev, and GitHub Security Advisories
* Normalize and deduplicate CVEs
* Track exploitability metadata

## Repository & Dependency Analysis

* Analyze GitLab repositories
* Generate and maintain SBOMs
* Build dependency relationships

## Exploitability Reasoning

* Determine whether vulnerable code paths are actually reachable
* Combine deterministic tooling with LLM-assisted contextual reasoning
* Reduce false-positive security noise

## Autonomous Patch Generation

* Generate dependency upgrade patches
* Update manifests and lockfiles
* Attempt compatibility fixes automatically

## GitLab CI/CD Orchestration

* Trigger GitLab pipelines
* Analyze CI failures
* Retry remediation attempts automatically
* Generate remediation summaries

## Merge Request Automation

* Open GitLab merge requests
* Attach reasoning traces and rollback guidance
* Assign reviewers automatically

## Human-Supervised Safety

* Human approval required before merges
* Confidence scoring for autonomous actions
* Full audit trail for every decision

---

# Why This Is Different

Most dependency security tools:

* scan,
* alert,
* and maybe open basic upgrade PRs.

DependencyMedic is designed as an:

> autonomous remediation orchestrator.

The novelty lies in:

* exploitability reasoning,
* workflow orchestration,
* CI self-healing,
* autonomous remediation retries,
* and event-driven agent coordination.

The goal is not just identifying vulnerabilities.

The goal is:

> autonomously driving secure remediation workflows end-to-end.

---

# Technology Stack

## Backend

* FastAPI
* Python 3.11+

## Frontend

* React
* TailwindCSS

## AI / Agent Framework

* Gemini
* LangGraph

## Infrastructure

* Docker Compose
* Redis Streams
* MongoDB

## CI/CD & Integrations

* GitLab APIs
* GitLab CI/CD

## Deployment

* Google Cloud Run

---

# Project Architecture

```text id="prxg1i"
services/
│
├── vuln-intelligence/
├── remediation-engine/
├── shared/
├── frontend/
└── infra/
```

---

# Hackathon MVP Scope

The MVP focuses on a narrow but highly demonstrable workflow.

Included:

* CVE ingestion
* GitLab integration
* SBOM generation
* Reachability analysis
* Autonomous dependency patch generation
* GitLab MR orchestration
* CI validation and retry logic
* Demo-ready vulnerable microservices

Excluded:

* Autonomous production deployment
* Kubernetes orchestration
* Runtime container security
* Multi-tenant SaaS architecture
* First-party vulnerability remediation

---

# Demo Vision

The demo simulates a modern software organization with:

* multiple vulnerable microservices,
* GitLab repositories,
* CI/CD pipelines,
* vulnerability feeds,
* and autonomous remediation workflows.

Expected demo flow:

```text id="rck7ux"
Critical CVE Published
   ↓
DependencyMedic Detects Vulnerability
   ↓
Affected Repositories Identified
   ↓
Exploitability Analysis Executed
   ↓
Patch Generated Automatically
   ↓
GitLab CI Triggered
   ↓
CI Failure Diagnosed & Retried
   ↓
Merge Request Opened
   ↓
Human Approval Workflow
```

The focus of the demo is:

* visible orchestration,
* autonomous workflows,
* explainability,
* and operational intelligence.

---

# Engineering Philosophy

DependencyMedic is built around:

* modular architecture,
* event-driven workflows,
* human-supervised autonomy,
* deterministic validation,
* and AI-assisted iterative development.

The project prioritizes:

* workflow reliability,
* observability,
* implementation clarity,
* and demo realism over production-scale complexity.

---

# Status

🚧 Currently under active hackathon development.
