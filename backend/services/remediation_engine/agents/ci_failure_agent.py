"""CI Failure Analysis Agent.

LangGraph state machine: parse → reason → recommend.
- `parse` runs the deterministic log triage.
- `reason` calls Gemini for contextual root-cause when an API key is configured.
  Otherwise it copies the deterministic suggestion verbatim.
- `recommend` produces the structured output expected by docs/agents.md.

Every run is persisted to `agent_runs` with confidence + reasoning summary.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, TypedDict

from shared.constants import COLLECTION_AGENT_RUNS
from shared.enums import AgentRunStatus
from shared.logging import get_logger
from shared.utils.mongo import get_database

from ..ci_analysis.log_parser import LogTriage, classify

logger = get_logger("remediation_engine.ci_failure_agent")


class AgentState(TypedDict, total=False):
    pipeline_run_id: str
    patch_attempt_id: str
    correlation_id: str
    logs: str
    triage: LogTriage
    llm_summary: str | None
    llm_used: bool
    output: dict[str, Any]


class CiFailureAgent:
    def __init__(self, *, gemini_api_key: str = "") -> None:
        self._gemini_api_key = gemini_api_key
        self._llm = None
        if gemini_api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                self._llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    google_api_key=gemini_api_key,
                    temperature=0.1,
                )
            except Exception as err:  # noqa: BLE001
                logger.warning("Gemini init failed; falling back", extra={"error": str(err)})
                self._llm = None

    async def run(
        self,
        *,
        pipeline_run_id: str,
        patch_attempt_id: str,
        correlation_id: str,
        logs: str,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        state: AgentState = {
            "pipeline_run_id": pipeline_run_id,
            "patch_attempt_id": patch_attempt_id,
            "correlation_id": correlation_id,
            "logs": logs,
            "llm_used": False,
            "llm_summary": None,
        }
        state["triage"] = self._parse_node(state)
        state["llm_summary"], state["llm_used"] = await self._reason_node(state)
        state["output"] = self._recommend_node(state)

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        await self._persist_run(state, elapsed_ms=elapsed_ms)
        return state["output"]

    def _parse_node(self, state: AgentState) -> LogTriage:
        return classify(state["logs"])

    async def _reason_node(self, state: AgentState) -> tuple[str | None, bool]:
        triage = state["triage"]
        if not self._llm:
            return triage.suggestion, False
        prompt = (
            "You are a CI failure analyst for a software supply chain remediation tool.\n"
            "Given the failure summary below, return a SINGLE short sentence explaining "
            "the most likely root cause and recommended retry strategy. Stay under 240 chars.\n\n"
            f"Failure type: {triage.failure_type}\n"
            f"Error lines:\n{chr(10).join(triage.error_lines) or '(none)'}\n\n"
            "Recommendation:"
        )
        try:
            resp = await self._llm.ainvoke(prompt)
            content = (resp.content if hasattr(resp, "content") else str(resp)).strip()
            return content[:240] or triage.suggestion, True
        except Exception as err:  # noqa: BLE001
            logger.warning(
                "Gemini call failed; using deterministic suggestion",
                extra={"error": str(err), "correlation_id": state["correlation_id"]},
            )
            return triage.suggestion, False

    def _recommend_node(self, state: AgentState) -> dict[str, Any]:
        triage = state["triage"]
        retry_recommended = triage.failure_type in {
            "missing_dependency",
            "dependency_conflict",
            "api_breakage",
            "test_failure",
        }
        return {
            "status": "completed",
            "confidence_score": triage.confidence,
            "summary": state.get("llm_summary") or triage.suggestion,
            "failure_type": triage.failure_type,
            "actions_taken": [
                "deterministic log triage",
                "llm root-cause inference" if state.get("llm_used") else "deterministic-only verdict",
            ],
            "recommendations": [triage.suggestion],
            "retry_recommended": retry_recommended,
            "requires_human_review": not retry_recommended,
        }

    async def _persist_run(self, state: AgentState, *, elapsed_ms: int) -> None:
        db = get_database()
        now = datetime.now(timezone.utc)
        triage = state["triage"]
        await db[COLLECTION_AGENT_RUNS].insert_one(
            {
                "_id": str(uuid.uuid4()),
                "agent_name": "ci_failure_analysis_agent",
                "workflow_id": state["correlation_id"],
                "input_summary": (
                    f"pipeline {state['pipeline_run_id']} for patch "
                    f"{state['patch_attempt_id']} failed: {triage.failure_type}"
                ),
                "output_summary": state["output"]["summary"],
                "confidence_score": state["output"]["confidence_score"],
                "tokens_used": 0,
                "execution_time_ms": elapsed_ms,
                "status": AgentRunStatus.COMPLETED.value,
                "llm_used": state["llm_used"],
                "correlation_id": state["correlation_id"],
                "created_at": now,
                "updated_at": now,
                "created_by": "remediation_engine",
                "version": 1,
            }
        )
