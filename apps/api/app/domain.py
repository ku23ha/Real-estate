"""RET-010 API schemas for persistent reference-domain entities."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NameInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def trim_nonempty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value


class UserInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=200)

    @field_validator("display_name")
    @classmethod
    def trim_nonempty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("display_name must not be blank")
        return value


class LocationInput(NameInput):
    parent_location_id: UUID | None = None


class MicroMarketInput(NameInput):
    location_id: UUID | None = None


class ProjectInput(NameInput):
    developer_id: UUID | None = None
    location_id: UUID | None = None


class NamedRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime


class UserRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    created_at: datetime


class LocationRecord(NamedRecord):
    parent_location_id: UUID | None


class MicroMarketRecord(NamedRecord):
    location_id: UUID | None


class ProjectRecord(NamedRecord):
    developer_id: UUID | None
    location_id: UUID | None
