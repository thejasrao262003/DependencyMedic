from enum import StrEnum


class VulnStatus(StrEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class RepoStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SCANNING = "scanning"


class PatchStatus(StrEnum):
    PENDING = "pending"
    GENERATING = "generating"
    GENERATED = "generated"
    VALIDATING = "validating"
    VALIDATED = "validated"
    FAILED = "failed"
    ESCALATED = "escalated"


class PipelineStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MRStatus(StrEnum):
    OPENED = "opened"
    APPROVED = "approved"
    MERGED = "merged"
    CLOSED = "closed"


class AgentRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
