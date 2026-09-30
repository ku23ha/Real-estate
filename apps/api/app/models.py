from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, JSON, Numeric, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = (CheckConstraint("length(trim(name)) > 0", name="ck_deals_name_not_blank"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft", server_default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    property_record: Mapped["Property"] = relationship(back_populates="deal", uselist=False)


class Property(Base):
    __tablename__ = "properties"
    __table_args__ = (
        UniqueConstraint("deal_id", name="uq_properties_deal_id"),
        CheckConstraint(
            "(area_value IS NULL AND area_unit IS NULL) OR "
            "(area_value IS NOT NULL AND area_unit IS NOT NULL)",
            name="ck_properties_area_value_unit_pair",
        ),
        CheckConstraint("area_value IS NULL OR area_value > 0", name="ck_properties_area_positive"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    deal_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("deals.id"), nullable=False
    )
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    area_value: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    area_unit: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deal: Mapped[Deal] = relationship(back_populates="property_record")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class User(Base):
    """A person record only; this model does not authenticate or authorize access."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Developer(Base):
    __tablename__ = "developers"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (Index("ix_locations_parent_location_id", "parent_location_id"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    parent_location_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("locations.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    parent: Mapped["Location | None"] = relationship(remote_side="Location.id")


class MicroMarket(Base):
    __tablename__ = "micro_markets"
    __table_args__ = (Index("ix_micro_markets_location_id", "location_id"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    location_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("locations.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    location: Mapped["Location | None"] = relationship()


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_developer_id", "developer_id"),
        Index("ix_projects_location_id", "location_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    developer_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("developers.id"), nullable=True
    )
    location_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("locations.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    developer: Mapped["Developer | None"] = relationship()
    location: Mapped["Location | None"] = relationship()


class EvidenceSource(Base):
    """Descriptive provenance for evidence origins; does not establish usage rights."""

    __tablename__ = "evidence_sources"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_evidence_sources_name_not_blank"),
        CheckConstraint("length(trim(source_type)) > 0", name="ck_evidence_sources_type_not_blank"),
        CheckConstraint("length(trim(rights_status)) > 0", name="ck_evidence_sources_rights_not_blank"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    rights_status: Mapped[str] = mapped_column(Text, nullable=False)
    rights_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Evidence(Base):
    """Append-only through the API; raw observation and its provenance are retained."""

    __tablename__ = "evidence"
    __table_args__ = (
        CheckConstraint("length(trim(evidence_type)) > 0", name="ck_evidence_type_not_blank"),
        Index("ix_evidence_deal_created", "deal_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    deal_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("deals.id"), nullable=False)
    source_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("evidence_sources.id"), nullable=False
    )
    evidence_type: Mapped[str] = mapped_column(Text, nullable=False)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_content: Mapped[dict] = mapped_column(JSON, nullable=False)
    normalized_content: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    provenance: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
