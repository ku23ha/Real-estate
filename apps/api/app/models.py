from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
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
