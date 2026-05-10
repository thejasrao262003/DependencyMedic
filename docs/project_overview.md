# DependencyMedic — Project Overview

## Overview

DependencyMedic is an autonomous AI-powered software supply chain defense system built for the Google Cloud Rapid Agent Hackathon.

The system continuously monitors vulnerability feeds, identifies impacted GitLab repositories, performs exploitability reasoning, generates dependency remediation patches, validates fixes through GitLab CI/CD pipelines, and orchestrates secure merge request workflows with human approval gates.

DependencyMedic is designed to behave like an AI Security Engineer operating inside a modern software organization.

This is not:

* a chatbot,
* a vulnerability dashboard,
* or a simple dependency updater.

The focus of the project is autonomous orchestration of software security remediation workflows.

---

# Problem Statement

Modern software systems depend heavily on open-source packages and transitive dependencies.

A typical application may contain:

* hundreds of direct dependencies,
* thousands of transitive dependencies,
* and a constantly evolving security attack surface.

When new vulnerabilities (CVEs) are discovered, engineering teams face several major problems:

* Security tools generate overwhelming alert noise.
* Most vulnerabilities are never properly triaged.
* Dependency updates frequently break CI pipelines.
* Patching workflows are slow and expensive.
* Critical vulnerabilities remain unresolved for weeks or months.

Existing tools mostly stop at:

> “This dependency is vulnerable.”

Very few systems:

* reason about exploitability,
* validate fixes autonomously,
* retry failed CI pipelines,
* or coordinate remediation workflows end-to-end.

DependencyMedic aims to solve this.

---

# Core Vision

DependencyMedic acts as an autonomous remediation orchestrator.

The system should:

* monitor vulnerabilities continuously,
* understand whether services are truly impacted,
* generate remediation patches,
* validate fixes automatically,
* coordinate GitLab workflows,
* and maintain human-supervised operational safety.

The project should feel like:

> “An AI teammate for software supply chain security.”

---

# Core Capabilities

## Vulnerability Intelligence

* Monitor NVD, OSV.dev, and GitHub Security Advisories
* Normalize and deduplicate vulnerability data
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

## Merge Request Automation

* Open GitLab merge requests
* Attach reasoning traces and rollback guidance
* Assign reviewers automatically

## Human-Supervised Safety

* Human approval required before merges
* Confidence scoring for autonomous actions
* Full audit trail for every decision

---

# Hackathon MVP Scope

The MVP intentionally focuses on a narrow but highly demonstrable workflow.

## Included in MVP

* GitLab integration
* Vulnerability ingestion
* SBOM generation
* Reachability analysis
* Dependency patch generation
* GitLab MR creation
* CI validation
* CI failure retry logic
* Web dashboard
* Demo-ready vulnerable repositories

## Excluded from MVP

* Autonomous production deployment
* Kubernetes orchestration
* Runtime container security
* First-party code vulnerability remediation
* Multi-tenant SaaS architecture
* Large-scale distributed infrastructure

---

# Architectural Philosophy

DependencyMedic is designed around the following principles:

1. Human-supervised autonomy over unrestricted automation.
2. Event-driven orchestration over tightly coupled workflows.
3. Specialized agents over monolithic AI systems.
4. Deterministic validation before LLM reasoning whenever possible.
5. Explainability and auditability for all autonomous actions.
6. Demo realism over production-scale complexity.
7. Modular architecture optimized for AI-assisted iterative development.

---

# High-Level Workflow

```text id="7g2xqs"
CVE Feed
   ↓
Vulnerability Ingestion
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

# Primary User Personas

## Security Engineer

Needs:

* actionable remediation,
* exploitability reasoning,
* reduced alert fatigue.

## Backend Engineer

Needs:

* tested patches,
* minimal CI breakage,
* simple review workflows.

## Engineering Manager

Needs:

* visibility into remediation timelines,
* SLA tracking,
* operational reporting.

---

# Technology Stack

## Backend

* FastAPI
* Python 3.11+

## Frontend

* React
* TailwindCSS

## Agent Framework

* LangGraph

## Database

* MongoDB

## Event System

* Redis Streams

## CI/CD Platform

* GitLab

## LLM

* Gemini

## Infrastructure

* Docker Compose
* Google Cloud Run

---

# AI Usage Philosophy

LLMs are used for:

* remediation reasoning,
* CI failure interpretation,
* migration assistance,
* summarization,
* workflow orchestration support.

LLMs are NOT trusted for:

* deterministic dependency analysis,
* guaranteed exploitability proofs,
* direct production deployment decisions,
* unrestricted autonomous actions.

---

# Demo Vision

The hackathon demo will simulate a realistic software organization with multiple interconnected microservices and intentionally vulnerable dependencies.

The demo flow should show:

1. A new critical CVE being discovered.
2. DependencyMedic identifying impacted services.
3. Exploitability reasoning execution.
4. Autonomous patch generation.
5. GitLab CI pipeline execution.
6. CI failure recovery attempts.
7. Merge request creation with detailed reasoning.
8. Human approval workflow.

The demo should emphasize:

* visible orchestration,
* operational intelligence,
* explainability,
* and autonomous workflow coordination.

---

# Success Criteria

The MVP is considered successful if it can:

* detect vulnerabilities automatically,
* identify impacted repositories,
* generate working dependency remediation patches,
* pass CI validation for at least some repositories,
* open GitLab merge requests autonomously,
* and demonstrate end-to-end autonomous remediation workflows during the live demo.

---

# Repository Philosophy

The codebase should be:

* modular,
* highly readable,
* AI-assisted-development friendly,
* event-driven,
* and optimized for rapid iteration during the hackathon.

The architecture should prioritize:

* implementation speed,
* clarity,
* observability,
* and demo stability over production-scale optimization.