from uuid import uuid4

from fastapi.testclient import TestClient


def _deal(client: TestClient) -> str:
    response = client.post("/api/v1/deals", json={"name": "Evidence test deal"})
    assert response.status_code == 201
    return response.json()["id"]


def _source(client: TestClient, rights_status: str = "unknown") -> dict:
    response = client.post(
        "/api/v1/evidence-sources",
        json={
            "name": "Founder supplied example",
            "source_type": "user_input",
            "reference": None,
            "rights_status": rights_status,
            "rights_notes": "Rights status recorded without a usability decision.",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_evidence_retains_raw_and_provenance_and_is_deal_scoped(client: TestClient) -> None:
    deal_id = _deal(client)
    source = _source(client)
    payload = {
        "source_id": source["id"],
        "evidence_type": "property_observation",
        "observed_at": "2026-09-30T10:00:00Z",
        "raw_content": {"area": "1200", "unit": "as supplied"},
        "normalized_content": None,
        "provenance": {"capture_method": "manual", "captured_by": "local_fixture"},
    }
    created = client.post(f"/api/v1/deals/{deal_id}/evidence", json=payload)
    assert created.status_code == 201
    record = created.json()
    assert record["raw_content"] == payload["raw_content"]
    assert record["normalized_content"] is None
    assert record["provenance"] == payload["provenance"]
    assert record["source_id"] == source["id"]

    listed = client.get(f"/api/v1/deals/{deal_id}/evidence")
    assert listed.status_code == 200
    assert [row["id"] for row in listed.json()] == [record["id"]]
    assert client.get(f"/api/v1/deals/{deal_id}/evidence/{record['id']}").json() == record

    # RET-020 exposes no mutation routes; evidence observations are append-only via the API.
    assert client.put(f"/api/v1/deals/{deal_id}/evidence/{record['id']}").status_code == 405
    assert client.patch(f"/api/v1/deals/{deal_id}/evidence/{record['id']}").status_code == 405
    assert client.delete(f"/api/v1/deals/{deal_id}/evidence/{record['id']}").status_code == 405


def test_evidence_rejects_missing_references_and_blank_type(client: TestClient) -> None:
    deal_id = _deal(client)
    source = _source(client)
    base = {
        "source_id": source["id"],
        "evidence_type": "valid_type",
        "raw_content": {"raw": True},
        "provenance": {"method": "manual"},
    }
    missing_source = {**base, "source_id": str(uuid4())}
    assert client.post(f"/api/v1/deals/{deal_id}/evidence", json=missing_source).status_code == 404
    blank_type = {**base, "evidence_type": "   "}
    assert client.post(f"/api/v1/deals/{deal_id}/evidence", json=blank_type).status_code == 422
    assert client.get(f"/api/v1/deals/{uuid4()}/evidence").status_code == 404


def test_source_rights_status_is_recorded_without_classification(client: TestClient) -> None:
    source = _source(client, "OPEN DATA / LEGAL REVIEW — BLOCKED")
    assert source["rights_status"] == "OPEN DATA / LEGAL REVIEW — BLOCKED"
    assert client.get(f"/api/v1/evidence-sources/{source['id']}").json() == source


def test_evidence_requires_source_and_raw_and_provenance(client: TestClient) -> None:
    deal_id = _deal(client)
    incomplete = {"evidence_type": "note"}
    assert client.post(f"/api/v1/deals/{deal_id}/evidence", json=incomplete).status_code == 422
