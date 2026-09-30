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
from app.evidence import (
    EvidenceCreate,
    EvidenceRecord,
    EvidenceSourceCreate,
    EvidenceSourceRecord,
)
from app.domain import (
    LocationInput,
    LocationRecord,
    MicroMarketInput,
    MicroMarketRecord,
    NamedRecord,
    NameInput,
    ProjectInput,
    ProjectRecord,
    UserInput,
    UserRecord,
)
from app.models import (
    Deal,
    Developer,
    Evidence,
    EvidenceSource,
    Location,
    MicroMarket,
    Organization,
    Project,
    Property,
    User,
)


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


def _reference_or_404(db: Session, model, record_id: UUID, label: str):
    row = db.get(model, record_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return row


@app.post("/api/v1/organizations", response_model=NamedRecord, status_code=201)
def create_organization(payload: NameInput, db: Session = Depends(get_db)):
    row = Organization(name=payload.name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/api/v1/organizations", response_model=list[NamedRecord])
def list_organizations(db: Session = Depends(get_db)):
    return db.scalars(select(Organization).order_by(Organization.created_at, Organization.id)).all()


@app.get("/api/v1/organizations/{record_id}", response_model=NamedRecord)
def get_organization(record_id: UUID, db: Session = Depends(get_db)):
    return _reference_or_404(db, Organization, record_id, "Organization")


@app.post("/api/v1/users", response_model=UserRecord, status_code=201)
def create_user(payload: UserInput, db: Session = Depends(get_db)):
    row = User(display_name=payload.display_name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/api/v1/users", response_model=list[UserRecord])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.created_at, User.id)).all()


@app.get("/api/v1/users/{record_id}", response_model=UserRecord)
def get_user(record_id: UUID, db: Session = Depends(get_db)):
    return _reference_or_404(db, User, record_id, "User")


@app.post("/api/v1/developers", response_model=NamedRecord, status_code=201)
def create_developer(payload: NameInput, db: Session = Depends(get_db)):
    row = Developer(name=payload.name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/api/v1/developers", response_model=list[NamedRecord])
def list_developers(db: Session = Depends(get_db)):
    return db.scalars(select(Developer).order_by(Developer.created_at, Developer.id)).all()


@app.get("/api/v1/developers/{record_id}", response_model=NamedRecord)
def get_developer(record_id: UUID, db: Session = Depends(get_db)):
    return _reference_or_404(db, Developer, record_id, "Developer")


@app.post("/api/v1/locations", response_model=LocationRecord, status_code=201)
def create_location(payload: LocationInput, db: Session = Depends(get_db)):
    if payload.parent_location_id:
        _reference_or_404(db, Location, payload.parent_location_id, "Parent location")
    row = Location(name=payload.name, parent_location_id=payload.parent_location_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/api/v1/locations", response_model=list[LocationRecord])
def list_locations(db: Session = Depends(get_db)):
    return db.scalars(select(Location).order_by(Location.created_at, Location.id)).all()


@app.get("/api/v1/locations/{record_id}", response_model=LocationRecord)
def get_location(record_id: UUID, db: Session = Depends(get_db)):
    return _reference_or_404(db, Location, record_id, "Location")


@app.post("/api/v1/micro-markets", response_model=MicroMarketRecord, status_code=201)
def create_micro_market(payload: MicroMarketInput, db: Session = Depends(get_db)):
    if payload.location_id:
        _reference_or_404(db, Location, payload.location_id, "Location")
    row = MicroMarket(name=payload.name, location_id=payload.location_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/api/v1/micro-markets", response_model=list[MicroMarketRecord])
def list_micro_markets(db: Session = Depends(get_db)):
    return db.scalars(select(MicroMarket).order_by(MicroMarket.created_at, MicroMarket.id)).all()


@app.get("/api/v1/micro-markets/{record_id}", response_model=MicroMarketRecord)
def get_micro_market(record_id: UUID, db: Session = Depends(get_db)):
    return _reference_or_404(db, MicroMarket, record_id, "Micro-market")


@app.post("/api/v1/projects", response_model=ProjectRecord, status_code=201)
def create_project(payload: ProjectInput, db: Session = Depends(get_db)):
    if payload.developer_id:
        _reference_or_404(db, Developer, payload.developer_id, "Developer")
    if payload.location_id:
        _reference_or_404(db, Location, payload.location_id, "Location")
    row = Project(
        name=payload.name,
        developer_id=payload.developer_id,
        location_id=payload.location_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/api/v1/projects", response_model=list[ProjectRecord])
def list_projects(db: Session = Depends(get_db)):
    return db.scalars(select(Project).order_by(Project.created_at, Project.id)).all()


@app.get("/api/v1/projects/{record_id}", response_model=ProjectRecord)
def get_project(record_id: UUID, db: Session = Depends(get_db)):
    return _reference_or_404(db, Project, record_id, "Project")


@app.post("/api/v1/evidence-sources", response_model=EvidenceSourceRecord, status_code=201)
def create_evidence_source(payload: EvidenceSourceCreate, db: Session = Depends(get_db)):
    row = EvidenceSource(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/api/v1/evidence-sources", response_model=list[EvidenceSourceRecord])
def list_evidence_sources(db: Session = Depends(get_db)):
    return db.scalars(
        select(EvidenceSource).order_by(EvidenceSource.created_at, EvidenceSource.id)
    ).all()


@app.get("/api/v1/evidence-sources/{source_id}", response_model=EvidenceSourceRecord)
def get_evidence_source(source_id: UUID, db: Session = Depends(get_db)):
    return _reference_or_404(db, EvidenceSource, source_id, "Evidence source")


@app.post(
    "/api/v1/deals/{deal_id}/evidence",
    response_model=EvidenceRecord,
    status_code=201,
)
def create_evidence(deal_id: UUID, payload: EvidenceCreate, db: Session = Depends(get_db)):
    if db.get(Deal, deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    if db.get(EvidenceSource, payload.source_id) is None:
        raise HTTPException(status_code=404, detail="Evidence source not found")
    row = Evidence(deal_id=deal_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/api/v1/deals/{deal_id}/evidence", response_model=list[EvidenceRecord])
def list_evidence(deal_id: UUID, db: Session = Depends(get_db)):
    if db.get(Deal, deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return db.scalars(
        select(Evidence)
        .where(Evidence.deal_id == deal_id)
        .order_by(Evidence.created_at, Evidence.id)
    ).all()


@app.get(
    "/api/v1/deals/{deal_id}/evidence/{evidence_id}",
    response_model=EvidenceRecord,
)
def get_evidence(deal_id: UUID, evidence_id: UUID, db: Session = Depends(get_db)):
    row = db.scalar(
        select(Evidence).where(Evidence.deal_id == deal_id, Evidence.id == evidence_id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return row
