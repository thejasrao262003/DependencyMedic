from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
import uuid


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BaseDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    created_by: str = "system"
    version: int = 1

    model_config = {"populate_by_name": True}

    def to_mongo(self) -> dict[str, Any]:
        data = self.model_dump(by_alias=True)
        return data

    @classmethod
    def from_mongo(cls, data: dict[str, Any]) -> "BaseDocument":
        if data and "_id" in data and not isinstance(data["_id"], str):
            data["_id"] = str(data["_id"])
        return cls(**data)
