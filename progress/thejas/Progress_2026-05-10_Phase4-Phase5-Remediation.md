# Session: Phase 4 + Phase 5 — Remediation & CI Failure Recovery

**Date:** 2026-05-10
**Developer:** Dev B (Remediation domain)
**Phases:** 4 (Patch Generation + GitLab Integration) and 5 (CI Failure Recovery)
**Status:** Code-complete, unit+integration tests green, not yet run end-to-end against `make up`

---

## What was done this session

### `remediation_engine` — owns `patch_attempts`, emits `patch.*`
- [x] `patchers/manifest_patcher.py` — deterministic mutation of `requirements.txt` and `package.json` (preserves `^`/`~` qualifiers)
- [x] `services/patch_generator.py` — orchestrator: load vuln + dep snapshot, choose fix version, patch manifest, write `patch_attempts` row, emit `patch.generated`. Stores patched manifest + path in the doc so `gitlab_integration` can commit without re-resolving.
- [x] `consumers/vuln_scored_consumer.py` — only acts on `risk_level >= medium`; idempotency through Redis consumer groups.
- [x] `consumers/ci_failed_consumer.py` — runs the CI Failure Analysis Agent, decides retry vs escalation against `MAX_RETRY_ATTEMPTS=2`.
- [x] `consumers/retry_consumer.py` — consumes `patch.retry_requested`, regenerates the patch with `attempt_number + 1` (so the branch name becomes `…-attempt-2`).
- [x] `agents/ci_failure_agent.py` — three-step LangGraph-shaped pipeline (parse → reason → recommend). LLM (Gemini via `langchain_google_genai`) is optional: when no `GEMINI_API_KEY` is set, the deterministic suggestion is used verbatim. Always emits `confidence_score`, persists run to `agent_runs`.
- [x] `ci_analysis/log_parser.py` — pure-function regex triage (`missing_dependency`, `dependency_conflict`, `api_breakage`, `test_failure`, `syntax_error`, `unknown`) with confidence scores.
- [x] `api/remediate.py` — `POST /api/v1/remediate` for the dashboard "trigger remediation now" path.
- [x] `main.py` — lifespan starts three consumer tasks + stashes publisher on `app.state`.

### `gitlab_integration` — owns `repositories`, `merge_requests`, `pipeline_runs`, emits `ci.*` / `mr.*` / `pipeline.completed`
- [x] `clients/protocol.py` — `GitLabClient` Protocol with `CommitFile`, `CommitResult`, `PipelineSnapshot`, `MergeRequestResult` dataclasses.
- [x] `clients/gitlab_client.py` — real GitLab REST v4 (httpx) covering branch/commit/pipeline trigger/get-pipeline+jobs/trace/MR.
- [x] `clients/mock_client.py` — deterministic in-process simulator. Branches ending `-attempt-1` always fail with a scripted dependency-conflict log; later attempts pass. This is what makes the Phase-5 demo reproducible without network access.
- [x] `clients/factory.py` — picks mock when `GITLAB_TOKEN` is empty, real otherwise.
- [x] `services/pipeline_runner.py` — branch + commit + trigger + poll-until-done + emit `ci.started`, `pipeline.completed`, then either `patch.validated` or `ci.failed`. Polling has a configurable timeout that converts to a synthetic failure.
- [x] `services/mr_creator.py` — opens MR with a generated description (CVE summary, risk score, dep changes, reachability evidence, rollback note), writes `merge_requests` row, emits `mr.created`.
- [x] `consumers/patch_generated_consumer.py` — entry into the GitLab side of the spine.
- [x] `consumers/patch_validated_consumer.py` — drives MR creation.
- [x] `main.py` — lifespan starts both consumers + initializes the GitLab client (logs which mode is active).

### `api_gateway`
- [x] `POST /api/v1/remediations/generate` — now proxies to `remediation_engine` instead of returning the placeholder. Falls back to a structured error envelope if remediation is unreachable.
- [x] `config.py` — added `remediation_engine_url`, `gitlab_integration_url`.

### `shared`
- [x] `utils/version.py` — `choose_fix_version`, `is_higher`. Picks the lowest fix > installed across `pypi`/`npm`-style version strings without pulling in `packaging`.

### Tests (all green via local venv)
- 18 unit + 4 integration = **22 passed**.
- `tests/unit/test_manifest_patcher.py` — pinned bumps, comment preservation, npm `^`/`~` preservation, missing-package short-circuit, invalid-JSON guard.
- `tests/unit/test_log_parser.py` — every classifier branch.
- `tests/unit/test_version_chooser.py` — version comparison + selection edge cases.
- `tests/unit/test_mock_gitlab_client.py` — fail-then-pass behaviour across attempt numbers.
- `tests/integration/test_patch_generator.py` — full DB-backed flow with `mongomock-motor`, asserts `patch.generated` event + persisted row.
- `tests/integration/test_pipeline_runner.py` — `attempt-1` branch produces `ci.failed`; `attempt-2` produces `patch.validated`. Validates events + `pipeline_runs` doc state.

### Dependencies
- [x] `requirements/dev.txt` — added `mongomock-motor==0.0.34`.

---

## What is NOT done

- **No live GitLab run.** All testing uses the `MockGitLabClient`. Once Varun seeds a real GitLab project we can flip `GITLAB_TOKEN` and exercise the real client.
- **Frontend pages for pipelines / merge-requests / remediations are still stubs** (Varun's note, not Dev B's surface — but the API gateway routes are live so the pages can be wired anytime).
- **No lockfile regeneration.** `requirements.txt` / `package.json` get version bumps; we never run `pip install` or `npm install` inside the remediation container. Spec acknowledges this is acceptable for MVP. Hook point: extend `services/patch_generator._apply_manifest_patch`.
- **Webhooks are not wired.** `gitlab_integration/webhooks/` is still empty — for the demo we poll. Real GitLab pipeline webhooks would replace the poller in `pipeline_runner._poll_until_done`.
- **Demo seed data needs `seed_manifests` field on each repo.** Patch generator now requires `repositories.seed_manifests[<path>]` so demo runs are reproducible without GitLab. Coordinate with Varun on `seed_demo.py` to add it.

---

## Key decisions made

- **Mock-first GitLab client.** `GITLAB_TOKEN=""` switches to a deterministic in-memory simulator. `attempt-1` branches fail with scripted logs, `attempt-2`+ pass — this is what gives Phase-5 a reliable demo without flakiness.
- **`POST /remediations/generate` proxies HTTP** (gateway → remediation engine `/remediate`) rather than forging a `vuln.scored` event under another service's domain. Respects the event ownership table in [docs/event_flow.md](../../docs/event_flow.md).
- **Patched manifest content is carried on the `patch_attempts` doc**, not on the `patch.generated` event. Keeps event payloads small and lets `gitlab_integration` re-read the manifest if a retry needs it.
- **CI Failure Agent works without LLM.** When `GEMINI_API_KEY` is empty the deterministic suggestion is the recommendation. Demo never fails because of a missing API key.
- **Branch name encodes attempt number** (`fix/<cve>-attempt-<n>`) — that's the contract the mock client keys off, and it makes pipeline_runs queryable by attempt without joining.
- **Confidence scores come from the deterministic triage**, not from the LLM. Keeps scores bounded and explainable per [docs/agents.md](../../docs/agents.md).

---

## Next session

- Wire frontend `RemediationsPage` / `PipelinesPage` / `MergeRequestsPage` to the live API gateway endpoints.
- Add `seed_manifests` to `seed_demo.py` (coordinate with Varun) so the demo flow runs end-to-end on a fresh `make up`.
- Run the live `vuln.scored → … → mr.created` flow once Varun's `vuln_intelligence` and `reachability_analysis` services are emitting `vuln.scored`. Validate `correlation_id` propagates the whole way.
- Optional: replace the polling in `pipeline_runner` with GitLab pipeline webhooks behind `webhooks/`.
- Optional: add E2E test under `backend/tests/e2e/` that spins MockGitLab + mongomock + an in-memory Redis stub and walks the full event chain.
