"""RET-020 request and response schemas for evidence provenance."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _nonblank(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("value must not be blank")
    return value


class EvidenceSourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=300)
    source_type: str = Field(min_length=1, max_length=100)
    reference: str | None = None
    rights_status: str = Field(min_length=1, max_length=100)
    rights_notes: str | None = None

    @field_validator("name", "source_type", "rights_status")
    @classmethod
    def trim_nonempty(cls, value: str) -> str:
        return _nonblank(value)


class EvidenceSourceRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source_type: str
    reference: str | None
    rights_status: str
    rights_notes: str | None
    created_at: datetime


class EvidenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: UUID
    evidence_type: str = Field(min_length=1, max_length=100)
    observed_at: datetime | None = None
    raw_content: dict
    normalized_content: dict | None = None
    provenance: dict

    @field_validator("evidence_type")
    @classmethod
    def trim_nonempty(cls, value: str) -> str:
        return _nonblank(value)


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    deal_id: UUID
    source_id: UUID
    evidence_type: str
    observed_at: datetime | None
    raw_content: dict
    normalized_content: dict | None
    provenance: dict
    created_at: datetime
