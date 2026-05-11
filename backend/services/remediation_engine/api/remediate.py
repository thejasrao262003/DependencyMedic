"""Internal trigger for manual remediation runs (used by api_gateway).

The normal entry point is the vuln.scored consumer — this endpoint exists so
the dashboard can request a remediation on demand without forging an event
under another service's domain.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Request
from pydantic import BaseModel

from shared.schemas.response import APIResponse

from ..services.patch_generator import PatchGenerationError, generate_patch

router = APIRouter(prefix="/remediate", tags=["remediate"])


class RemediateRequest(BaseModel):
    repository_id: str
    vulnerability_id: str
    correlation_id: str | None = None


@router.post("", response_model=APIResponse, status_code=202)
async def trigger_remediation(body: RemediateRequest, request: Request) -> APIResponse:
    publisher = request.app.state.publisher
    correlation_id = body.correlation_id or str(uuid.uuid4())
    try:
        patch_attempt_id = await generate_patch(
            repository_id=body.repository_id,
            vulnerability_id=body.vulnerability_id,
            correlation_id=correlation_id,
            publisher=publisher,
            attempt_number=1,
        )
    except PatchGenerationError as err:
        return APIResponse.fail("PATCH_GENERATION_FAILED", str(err))
    return APIResponse.ok(
        {
            "patch_attempt_id": patch_attempt_id,
            "correlation_id": correlation_id,
            "status": "generated",
        }
    )
