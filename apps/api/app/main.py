from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from app.database import get_database_url, get_db, make_engine, make_session_factory
from app.models import Deal, Property


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    database_url = get_database_url()
    engine = make_engine(database_url)
    application.state.engine = engine
    application.state.session_factory = make_session_factory(engine)
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="Rethos API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class PropertyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address: str | None = None
    city: str | None = None
    asset_type: str | None = None
    area_value: float | None = Field(default=None, gt=0)
    area_unit: str | None = None

    @model_validator(mode="after")
    def area_requires_unit(self):
        if (self.area_value is None) != (self.area_unit is None):
            raise ValueError("area_value and area_unit must be supplied together")
        return self


class PropertyPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address: str | None = None
    city: str | None = None
    asset_type: str | None = None
    area_value: float | None = Field(default=None, gt=0)
    area_unit: str | None = None


class DealCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    property: PropertyInput = Field(default_factory=PropertyInput)

    @field_validator("name")
    @classmethod
    def trim_nonempty_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value


class PropertyRecord(PropertyInput):
    id: UUID


class DealRecord(BaseModel):
    id: UUID
    name: str
    status: str
    created_at: datetime
    property: PropertyRecord


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _to_record(deal: Deal) -> DealRecord:
    property_record = deal.property_record
    return DealRecord(
        id=deal.id,
        name=deal.name,
        status=deal.status,
        created_at=_as_utc(deal.created_at),
        property=PropertyRecord(
            id=property_record.id,
            address=property_record.address,
            city=property_record.city,
            asset_type=property_record.asset_type,
            area_value=property_record.area_value,
            area_unit=property_record.area_unit,
        ),
    )


def _to_property_record(property_record: Property) -> PropertyRecord:
    return PropertyRecord(
        id=property_record.id,
        address=property_record.address,
        city=property_record.city,
        asset_type=property_record.asset_type,
        area_value=property_record.area_value,
        area_unit=property_record.area_unit,
    )


@app.get("/health")
def health(request: Request, db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "persistence": request.app.state.engine.dialect.name}


@app.post("/api/v1/deals", response_model=DealRecord, status_code=201)
def create_deal(payload: DealCreate, db: Session = Depends(get_db)):
    deal = Deal(name=payload.name, status="draft")
    property_record = Property(**payload.property.model_dump())
    deal.property_record = property_record
    db.add(deal)
    db.commit()
    db.refresh(deal)
    db.refresh(property_record)
    return _to_record(deal)


@app.get("/api/v1/deals", response_model=list[DealRecord])
def list_deals(db: Session = Depends(get_db)):
    deals = db.scalars(
        select(Deal)
        .options(selectinload(Deal.property_record))
        .order_by(Deal.created_at.desc(), Deal.id.desc())
    ).all()
    return [_to_record(deal) for deal in deals]


@app.get("/api/v1/deals/{deal_id}", response_model=DealRecord)
def get_deal(deal_id: UUID, db: Session = Depends(get_db)):
    deal = db.scalar(
        select(Deal)
        .options(selectinload(Deal.property_record))
        .where(Deal.id == deal_id)
    )
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return _to_record(deal)


@app.post(
    "/api/v1/deals/{deal_id}/property",
    response_model=PropertyRecord,
)
def create_property(deal_id: UUID, payload: PropertyInput, db: Session = Depends(get_db)):
    deal = db.get(Deal, deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    property_record = db.scalar(select(Property).where(Property.deal_id == deal_id))
    if property_record is None:
        raise HTTPException(status_code=404, detail="Property not found")
    is_placeholder = all(
        getattr(property_record, field) is None
        for field in ("address", "city", "asset_type", "area_value", "area_unit")
    )
    if not is_placeholder:
        raise HTTPException(status_code=409, detail="Property already has details")

    for field, value in payload.model_dump().items():
        setattr(property_record, field, value)
    db.commit()
    db.refresh(property_record)
    return _to_property_record(property_record)


@app.get("/api/v1/deals/{deal_id}/property", response_model=PropertyRecord)
def get_property(deal_id: UUID, db: Session = Depends(get_db)):
    deal = db.get(Deal, deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    property_record = db.scalar(select(Property).where(Property.deal_id == deal_id))
    if property_record is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return _to_property_record(property_record)


@app.patch("/api/v1/deals/{deal_id}/property", response_model=PropertyRecord)
def update_property(
    deal_id: UUID,
    payload: PropertyPatch,
    db: Session = Depends(get_db),
):
    deal = db.get(Deal, deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    property_record = db.scalar(select(Property).where(Property.deal_id == deal_id))
    if property_record is None:
        raise HTTPException(status_code=404, detail="Property not found")

    updates = payload.model_dump(exclude_unset=True)
    merged = {
        "address": property_record.address,
        "city": property_record.city,
        "asset_type": property_record.asset_type,
        "area_value": property_record.area_value,
        "area_unit": property_record.area_unit,
        **updates,
    }
    try:
        validated = PropertyInput.model_validate(merged)
    except ValidationError as error:
        raise HTTPException(
            status_code=422,
            detail=error.errors(include_context=False, include_input=False),
        ) from error

    for field, value in validated.model_dump().items():
        setattr(property_record, field, value)
    db.commit()
    db.refresh(property_record)
    return _to_property_record(property_record)
