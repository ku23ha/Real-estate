from fastapi.testclient import TestClient

from app.main import app


def test_create_deal_persists_property(client: TestClient) -> None:
    response = client.post(
        "/api/v1/deals",
        json={
            "name": "Test acquisition",
            "property": {
                "address": "Example address",
                "city": "Example city",
                "asset_type": "Residential",
                "area_value": 1250,
                "area_unit": "sqft",
            },
        },
    )

    assert response.status_code == 201
    deal = response.json()
    assert deal["name"] == "Test acquisition"
    assert deal["status"] == "draft"
    assert deal["property"]["address"] == "Example address"
    assert deal["property"]["area_value"] == 1250
    assert deal["property"]["area_unit"] == "sqft"
    assert deal["id"]
    assert deal["property"]["id"]


def test_retrieve_deal(client: TestClient) -> None:
    created = client.post("/api/v1/deals", json={"name": "Retrieve me"}).json()

    response = client.get(f"/api/v1/deals/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_retrieve_missing_deal_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/deals/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 404


def test_blank_deal_name_is_rejected(client: TestClient) -> None:
    response = client.post("/api/v1/deals", json={"name": "   "})

    assert response.status_code == 422


def test_list_deals(client: TestClient) -> None:
    first = client.post("/api/v1/deals", json={"name": "First"}).json()
    second = client.post("/api/v1/deals", json={"name": "Second"}).json()

    response = client.get("/api/v1/deals")

    assert response.status_code == 200
    returned = {deal["id"]: deal for deal in response.json()}
    assert returned[first["id"]]["property"]["id"] == first["property"]["id"]
    assert returned[second["id"]]["name"] == "Second"


def test_property_survives_new_session(client: TestClient) -> None:
    created = client.post(
        "/api/v1/deals",
        json={"name": "Property persistence", "property": {"city": "Example city"}},
    ).json()

    retrieved = client.get(f"/api/v1/deals/{created['id']}").json()

    assert retrieved["property"]["id"] == created["property"]["id"]
    assert retrieved["property"]["city"] == "Example city"


def test_deal_and_property_survive_api_restart(database_url: str) -> None:
    with TestClient(app) as first_client:
        created = first_client.post(
            "/api/v1/deals",
            json={
                "name": "Restart persistence",
                "property": {"address": "Persistent address", "area_value": 800, "area_unit": "sqm"},
            },
        ).json()

    with TestClient(app) as restarted_client:
        response = restarted_client.get(f"/api/v1/deals/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Restart persistence"
    assert response.json()["property"]["id"] == created["property"]["id"]
    assert response.json()["property"]["address"] == "Persistent address"


def test_health_reports_active_database(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "persistence": "sqlite"}


def test_create_and_retrieve_property_independently(client: TestClient) -> None:
    deal = client.post("/api/v1/deals", json={"name": "Property workflow"}).json()
    payload = {
        "address": "Example address",
        "city": "Example city",
        "asset_type": "Residential",
        "area_value": 120,
        "area_unit": "sqm",
    }

    created = client.post(f"/api/v1/deals/{deal['id']}/property", json=payload)

    assert created.status_code == 200
    property_record = created.json()
    assert property_record["address"] == payload["address"]
    assert property_record["area_value"] == payload["area_value"]
    assert property_record["area_unit"] == payload["area_unit"]
    assert property_record["id"]
    assert client.get(f"/api/v1/deals/{deal['id']}/property").json() == property_record

    nested_deal = client.get(f"/api/v1/deals/{deal['id']}").json()
    assert nested_deal["property"]["id"] == property_record["id"]
    assert nested_deal["property"]["city"] == payload["city"]


def test_property_patch_merges_fields_and_preserves_area_pair(client: TestClient) -> None:
    deal = client.post(
        "/api/v1/deals",
        json={"name": "Property update", "property": {"area_value": 120, "area_unit": "sqm"}},
    ).json()

    updated = client.patch(
        f"/api/v1/deals/{deal['id']}/property",
        json={"city": "Example city", "area_value": 125},
    )

    assert updated.status_code == 200
    assert updated.json()["city"] == "Example city"
    assert updated.json()["area_value"] == 125
    assert updated.json()["area_unit"] == "sqm"


def test_property_patch_rejects_incomplete_area_pair(client: TestClient) -> None:
    deal = client.post(
        "/api/v1/deals",
        json={"name": "Area validation", "property": {"area_value": 120, "area_unit": "sqm"}},
    ).json()

    response = client.patch(
        f"/api/v1/deals/{deal['id']}/property",
        json={"area_value": None},
    )

    assert response.status_code == 422
    assert client.get(f"/api/v1/deals/{deal['id']}/property").json()["area_value"] == 120


def test_property_endpoints_report_missing_deal_and_populated_property(client: TestClient) -> None:
    deal = client.post("/api/v1/deals", json={"name": "Property endpoint errors"}).json()
    missing_deal_id = "00000000-0000-0000-0000-000000000001"

    assert client.get(f"/api/v1/deals/{missing_deal_id}/property").status_code == 404

    first = client.post(f"/api/v1/deals/{deal['id']}/property", json={"city": "Example"})
    second = client.post(f"/api/v1/deals/{deal['id']}/property", json={"city": "Another"})

    assert first.status_code == 200
    assert second.status_code == 409
