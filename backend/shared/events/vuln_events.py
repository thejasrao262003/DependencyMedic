from pydantic import BaseModel
from ..enums import Severity


class VulnDiscoveredPayload(BaseModel):
    vulnerability_id: str
    cve_id: str
    severity: Severity
    source: str
    summary: str


class VulnMatchedPayload(BaseModel):
    vulnerability_id: str
    cve_id: str
    repository_ids: list[str]
    affected_packages: list[str]


class VulnAssessedPayload(BaseModel):
    vulnerability_id: str
    repository_id: str
    reachable: bool
    confidence_score: float
    evidence_count: int


class VulnScoredPayload(BaseModel):
    vulnerability_id: str
    repository_id: str
    risk_score: int
    risk_level: Severity
    recommended_action: str
