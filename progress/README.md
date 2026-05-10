# Progress Logs

Session-by-session logs for each developer. Append-only — one file per session.

## Structure

```
progress/
  varun/        ← Dev A (Threat Intelligence: vuln_intelligence, reachability_analysis)
  devb/         ← Dev B (Remediation: remediation_engine, gitlab_integration)
```

## File naming

```
Progress_YYYY-MM-DD_<brief-slug>.md
```

Examples:
- `Progress_2026-05-10_Phase1-Foundation.md`
- `Progress_2026-05-11_NVD-Ingestion.md`

## For Claude instances

Read logs in reverse chronological order (newest first) within each developer's folder to get current context.
The most recent file in each folder is what that developer is actively working on or just finished.
