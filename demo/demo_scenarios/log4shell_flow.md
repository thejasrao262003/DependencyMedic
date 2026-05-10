# Demo Scenario: Log4Shell End-to-End Flow

## Trigger
Ingest CVE-2021-44228 (Log4Shell) into vuln_intelligence.

## Expected Flow

1. `vuln.discovered` — vuln_intelligence detects log4j-core < 2.15.0
2. `vuln.matched` — payment-service identified as affected (uses log4j-core 2.14.1)
3. `vuln.assessed` — reachability_analysis confirms vulnerable code path is reachable
4. `vuln.scored` — risk score 98, level critical
5. `patch.generated` — remediation_engine upgrades log4j-core to 2.17.1
6. `ci.started` — pipeline triggered on branch fix/cve-2021-44228
7. `ci.failed` — unit tests fail due to API change in log4j 2.17.1
8. `patch.retry_requested` — CI failure analysis agent recommends pinning log4j-api
9. `patch.generated` (attempt 2) — adjusted patch with log4j-api pinned
10. `patch.validated` — pipeline passes on second attempt
11. `mr.created` — MR opened, assigned to security-team for review

## Demo Narration Points

- Show the dashboard updating in real-time as events flow
- Highlight confidence scores on each agent decision
- Show the CI failure logs and agent root-cause analysis
- Emphasize: the system retried autonomously, no human intervention until MR review
