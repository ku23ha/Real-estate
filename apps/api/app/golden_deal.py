"""Canonical synthetic Golden Deal fixture for local MVP demonstration only."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.comparables import ComparableFacts, comparable_fingerprint
from app.models import Comparable, Deal, Evidence, EvidenceSource, Property


GOLDEN_DEAL_ID = UUID("bad3d41f-3178-4a6a-9137-03053ca73100")
GOLDEN_PROPERTY_ID = UUID("bad3d41f-3178-4a6a-9137-03053ca73101")
GOLDEN_SOURCE_ID = UUID("bad3d41f-3178-4a6a-9137-03053ca73102")
GOLDEN_DEAL_NAME = "Golden synthetic apartment acquisition"
GOLDEN_EVIDENCE_IDS = [
    UUID(f"bad3d41f-3178-4a6a-9137-03053ca73{index:03d}") for index in range(103, 108)
]
GOLDEN_COMPARABLE_IDS = [
    UUID(f"bad3d41f-3178-4a6a-9137-03053ca73{index:03d}") for index in range(108, 113)
]
GOLDEN_AS_OF = "2026-09-30"
GOLDEN_CURRENCY = "INR"
GOLDEN_PROPERTY = {
    "address": "Synthetic Golden Deal 001",
    "city": "Synthetic Market A",
    "asset_type": "Residential apartment",
    "area_value": "1000",
    "area_unit": "sqft",
}
GOLDEN_COMPARABLES = [
    {
        "transaction_date": "2026-04-01",
        "reported_price": "10000000",
        "currency_code": "INR",
        "property_type": "Residential apartment",
        "area_value": "1000",
        "area_unit": "sqft",
        "location_label": "Synthetic Market A",
        "project_name": "Synthetic Project A",
    },
    {
        "transaction_date": "2026-05-01",
        "reported_price": "9000000",
        "currency_code": "INR",
        "property_type": "Residential apartment",
        "area_value": "900",
        "area_unit": "sqft",
        "location_label": "Synthetic Market A",
        "project_name": "Synthetic Project B",
    },
    {
        "transaction_date": "2026-06-01",
        "reported_price": "12100000",
        "currency_code": "INR",
        "property_type": "Residential apartment",
        "area_value": "1100",
        "area_unit": "sqft",
        "location_label": "Synthetic Market A",
        "project_name": "Synthetic Project C",
    },
    {
        "transaction_date": "2026-07-01",
        "reported_price": "9500000",
        "currency_code": "INR",
        "property_type": "Residential apartment",
        "area_value": "1000",
        "area_unit": "sqft",
        "location_label": "Synthetic Market A",
        "project_name": "Synthetic Project D",
    },
    {
        "transaction_date": "2026-08-01",
        "reported_price": "10500000",
        "currency_code": "INR",
        "property_type": "Residential apartment",
        "area_value": "1050",
        "area_unit": "sqft",
        "location_label": "Synthetic Market A",
        "project_name": "Synthetic Project E",
    },
]


def seed_golden_deal(db: Session) -> Deal:
    existing = db.get(Deal, GOLDEN_DEAL_ID)
    if existing is not None:
        count = len(db.scalars(select(Comparable.id).where(Comparable.deal_id == GOLDEN_DEAL_ID)).all())
        if count != len(GOLDEN_COMPARABLES):
            raise RuntimeError("Golden Deal exists without its comparable fixture.")
        return existing

    deal = Deal(
        id=GOLDEN_DEAL_ID,
        name=GOLDEN_DEAL_NAME,
        status="draft",
        property_record=Property(id=GOLDEN_PROPERTY_ID, **GOLDEN_PROPERTY),
    )
    source = EvidenceSource(
        id=GOLDEN_SOURCE_ID,
        name="Rethos synthetic Golden Deal fixture",
        source_type="synthetic_fixture",
        reference="golden-deal-v1",
        rights_status="synthetic",
        rights_notes="Generated solely for local demonstration and tests.",
    )
    db.add_all([deal, source])
    for index, raw in enumerate(GOLDEN_COMPARABLES):
        facts = ComparableFacts.model_validate(raw)
        evidence = Evidence(
            id=GOLDEN_EVIDENCE_IDS[index],
            deal_id=GOLDEN_DEAL_ID,
            source_id=GOLDEN_SOURCE_ID,
            evidence_type="comparable_transaction",
            raw_content={**raw, "fixture_version": "golden-deal-v1"},
            provenance={"method": "synthetic_fixture", "fixture_version": "golden-deal-v1"},
        )
        comparable = Comparable(
            id=GOLDEN_COMPARABLE_IDS[index],
            deal_id=GOLDEN_DEAL_ID,
            evidence_id=GOLDEN_EVIDENCE_IDS[index],
            fingerprint=comparable_fingerprint(facts),
            **facts.model_dump(),
        )
        db.add_all([evidence, comparable])
    db.commit()
    return deal


def seed() -> bool:
    from app.database import get_database_url, make_engine, make_session_factory

    engine = make_engine(get_database_url())
    try:
        with make_session_factory(engine)() as db:
            existing = db.get(Deal, GOLDEN_DEAL_ID)
            if existing is not None:
                return False
            seed_golden_deal(db)
            return True
    finally:
        engine.dispose()


if __name__ == "__main__":
    print("Inserted synthetic Golden Deal." if seed() else "Synthetic Golden Deal already exists.")
