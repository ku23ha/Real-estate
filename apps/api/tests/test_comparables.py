from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.golden_deal import (
    GOLDEN_AS_OF,
    GOLDEN_CURRENCY,
    GOLDEN_DEAL_ID,
    GOLDEN_DEAL_NAME,
    seed_golden_deal,
)


def _deal(client: TestClient, *, city: str = "Synthetic Market A") -> str:
    response = client.post(
        "/api/v1/deals",
        json={
            "name": "Comparable test deal",
            "property": {
                "city": city,
                "asset_type": "Residential apartment",
                "area_value": 1000,
                "area_unit": "sqft",
            },
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _evidence(client: TestClient, deal_id: str, *, rights_status: str = "synthetic") -> str:
    source = client.post(
        "/api/v1/evidence-sources",
        json={
            "name": "Comparable test source",
            "source_type": "test_fixture",
            "rights_status": rights_status,
        },
    )
    assert source.status_code == 201
    evidence = client.post(
        f"/api/v1/deals/{deal_id}/evidence",
        json={
            "source_id": source.json()["id"],
            "evidence_type": "comparable_transaction",
            "raw_content": {
                "transaction_date": "2026-06-01",
                "reported_price": "10000000",
                "currency_code": "INR",
                "property_type": "Residential apartment",
                "area_value": "1000",
                "area_unit": "sqft",
                "location_label": "Synthetic Market A",
            },
            "provenance": {"method": "test_fixture"},
        },
    )
    assert evidence.status_code == 201
    return evidence.json()["id"]


def _comparable_payload(evidence_id: str, **overrides) -> dict:
    return {
        "evidence_id": evidence_id,
        "transaction_date": "2026-06-01",
        "reported_price": "10000000",
        "currency_code": "INR",
        "property_type": "Residential apartment",
        "area_value": "1000",
        "area_unit": "sqft",
        "location_label": "Synthetic Market A",
        **overrides,
    }


def test_golden_deal_comparable_valuation_is_traceable_and_reproducible(client: TestClient) -> None:
    with client.app.state.session_factory() as db:
        deal = seed_golden_deal(db)
        assert deal.id == GOLDEN_DEAL_ID
        assert deal.name == GOLDEN_DEAL_NAME

    comparables = client.get(f"/api/v1/deals/{GOLDEN_DEAL_ID}/comparables")
    assert comparables.status_code == 200
    rows = comparables.json()
    assert len(rows) == 5
    assert all(row["price_per_area"] for row in rows)
    assert all(row["evidence_id"] for row in rows)

    payload = {"currency_code": GOLDEN_CURRENCY, "as_of": GOLDEN_AS_OF}
    first = client.post(f"/api/v1/deals/{GOLDEN_DEAL_ID}/valuation", json=payload)
    second = client.post(f"/api/v1/deals/{GOLDEN_DEAL_ID}/valuation", json=payload)
    assert first.status_code == 200
    result = first.json()
    assert result == second.json()
    assert result["comparable_count"] == 5
    assert len(result["comparable_ids"]) == 5
    assert result["unit_rate_low"] == "9500.0000"
    assert result["unit_rate_central"] == "10000.0000"
    assert result["unit_rate_high"] == "11000.0000"
    assert result["valuation_low"] == "9500000.00"
    assert result["valuation_central"] == "10000000.00"
    assert result["valuation_high"] == "11000000.00"


def test_manual_comparable_requires_same_deal_evidence_and_rejects_duplicates(client: TestClient) -> None:
    deal_id = _deal(client)
    other_deal_id = _deal(client, city="Another Synthetic Market")
    evidence_id = _evidence(client, deal_id)
    payload = _comparable_payload(evidence_id)
    created = client.post(f"/api/v1/deals/{deal_id}/comparables", json=payload)
    assert created.status_code == 201
    assert Decimal(created.json()["reported_price"]) == Decimal("10000000")
    assert created.json()["price_per_area"] == "10000.0000"
    assert client.post(f"/api/v1/deals/{deal_id}/comparables", json=payload).status_code == 409
    altered = {**payload, "reported_price": "11000000"}
    assert client.post(f"/api/v1/deals/{deal_id}/comparables", json=altered).status_code == 422
    assert client.post(f"/api/v1/deals/{other_deal_id}/comparables", json=payload).status_code == 404
    assert client.get(f"/api/v1/deals/{deal_id}/comparables").json()[0]["evidence_id"] == evidence_id


def test_csv_import_preserves_raw_rows_and_rejects_bad_headers(client: TestClient) -> None:
    deal_id = _deal(client)
    csv_payload = {
        "source_name": "Authorized pilot file",
        "source_type": "customer_provided_file",
        "rights_status": "authorized",
        "source_reference": "pilot-batch-001",
        "csv_content": (
            "transaction_date,reported_price,currency_code,property_type,area_value,area_unit,location_label,project_name\n"
            "2026-06-01,10000000,INR,Residential apartment,1000,sqft,Synthetic Market A,Sample Project\n"
        ),
    }
    imported = client.post(f"/api/v1/deals/{deal_id}/comparables/import", json=csv_payload)
    assert imported.status_code == 201
    assert imported.json()[0]["price_per_area"] == "10000.0000"
    evidence = client.get(f"/api/v1/deals/{deal_id}/evidence").json()
    assert len(evidence) == 1
    assert evidence[0]["raw_content"]["reported_price"] == "10000000"
    assert evidence[0]["provenance"] == {"method": "csv_import", "row_number": 2}

    malformed = {**csv_payload, "csv_content": "date,price\n2026-01-01,1\n"}
    assert client.post(f"/api/v1/deals/{deal_id}/comparables/import", json=malformed).status_code == 422


def test_valuation_exact_filters_and_source_rights_gate(client: TestClient) -> None:
    deal_id = _deal(client)
    evidence_id = _evidence(client, deal_id, rights_status="unknown")
    payload = _comparable_payload(evidence_id)
    assert client.post(f"/api/v1/deals/{deal_id}/comparables", json=payload).status_code == 201
    response = client.post(
        f"/api/v1/deals/{deal_id}/valuation",
        json={"currency_code": "INR", "as_of": "2026-09-30"},
    )
    assert response.status_code == 422
    assert "No eligible exact-match" in response.json()["detail"]


def test_csv_duplicate_fingerprint_is_rejected_atomically(client: TestClient) -> None:
    deal_id = _deal(client)
    csv_payload = {
        "source_name": "Synthetic import",
        "source_type": "synthetic_fixture",
        "rights_status": "synthetic",
        "csv_content": (
            "transaction_date,reported_price,currency_code,property_type,area_value,area_unit,location_label\n"
            "2026-06-01,10000000,INR,Residential apartment,1000,sqft,Synthetic Market A\n"
            "2026-06-01,10000000,INR,Residential apartment,1000,sqft,Synthetic Market A\n"
        ),
    }
    response = client.post(f"/api/v1/deals/{deal_id}/comparables/import", json=csv_payload)
    assert response.status_code == 409
    assert client.get(f"/api/v1/deals/{deal_id}/comparables").json() == []
    assert client.get(f"/api/v1/deals/{deal_id}/evidence").json() == []


def test_valuation_rejects_missing_property_and_no_matching_comparables(client: TestClient) -> None:
    no_property = client.post("/api/v1/deals", json={"name": "No property"}).json()["id"]
    payload = {"currency_code": "INR", "as_of": "2026-09-30"}
    assert client.post(f"/api/v1/deals/{no_property}/valuation", json=payload).status_code == 422
    deal_id = _deal(client)
    assert client.post(f"/api/v1/deals/{deal_id}/valuation", json=payload).status_code == 422
    assert client.get(f"/api/v1/deals/{uuid4()}/comparables").status_code == 404
