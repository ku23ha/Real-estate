"""Insert one clearly synthetic, minimal local development fixture."""

from uuid import UUID

from app.database import get_database_url, make_engine, make_session_factory
from app.models import Deal, Property


SEED_DEAL_ID = UUID("45b5aa48-f740-4ac8-8e49-8c03f7da4420")
SEED_PROPERTY_ID = UUID("4c5a0471-5800-45a2-9dc6-9d396591a6e4")


def seed() -> bool:
    engine = make_engine(get_database_url())
    session_factory = make_session_factory(engine)
    try:
        with session_factory() as session:
            if session.get(Deal, SEED_DEAL_ID) is not None:
                return False
            deal = Deal(id=SEED_DEAL_ID, name="Synthetic local development fixture", status="draft")
            deal.property_record = Property(
                id=SEED_PROPERTY_ID,
                address="Synthetic example address",
            )
            session.add(deal)
            session.commit()
            return True
    finally:
        engine.dispose()


if __name__ == "__main__":
    inserted = seed()
    print("Inserted synthetic fixture." if inserted else "Synthetic fixture already exists.")
