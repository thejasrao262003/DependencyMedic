from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
import uuid


class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_service: str
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    payload: dict[str, Any] = Field(default_factory=dict)
