from uuid import uuid4

from fastapi.testclient import TestClient


def test_reference_entities_persist_and_list(client: TestClient) -> None:
    cases = [
        ("organizations", {"name": "Example organization"}, "name"),
        ("users", {"display_name": "Example reviewer"}, "display_name"),
        ("developers", {"name": "Example developer"}, "name"),
    ]
    for route, body, field in cases:
        created = client.post(f"/api/v1/{route}", json=body)
        assert created.status_code == 201
        assert created.json()[field] == next(iter(body.values()))
        listed = client.get(f"/api/v1/{route}")
        assert created.json()["id"] in {row["id"] for row in listed.json()}
        retrieved = client.get(f"/api/v1/{route}/{created.json()['id']}")
        assert retrieved.status_code == 200
        assert retrieved.json()[field] == next(iter(body.values()))


def test_location_hierarchy_micro_market_and_project_references(client: TestClient) -> None:
    parent = client.post("/api/v1/locations", json={"name": "Example region"}).json()
    child = client.post(
        "/api/v1/locations",
        json={"name": "Example city", "parent_location_id": parent["id"]},
    )
    assert child.status_code == 201
    assert child.json()["parent_location_id"] == parent["id"]

    market = client.post(
        "/api/v1/micro-markets",
        json={"name": "Example market", "location_id": child.json()["id"]},
    )
    assert market.status_code == 201
    assert market.json()["location_id"] == child.json()["id"]

    developer = client.post("/api/v1/developers", json={"name": "Example builder"}).json()
    project = client.post(
        "/api/v1/projects",
        json={"name": "Example project", "developer_id": developer["id"], "location_id": child.json()["id"]},
    )
    assert project.status_code == 201
    assert project.json()["developer_id"] == developer["id"]
    assert project.json()["location_id"] == child.json()["id"]
    assert client.get(f"/api/v1/projects/{project.json()['id']}").json() == project.json()


def test_domain_relationships_reject_unknown_reference_ids(client: TestClient) -> None:
    response = client.post(
        "/api/v1/micro-markets",
        json={"name": "Orphan market", "location_id": str(uuid4())},
    )
    assert response.status_code == 404


def test_domain_names_are_trimmed_and_blank_names_rejected(client: TestClient) -> None:
    created = client.post("/api/v1/organizations", json={"name": "  Team  "})
    assert created.status_code == 201
    assert created.json()["name"] == "Team"
    assert client.post("/api/v1/projects", json={"name": "   "}).status_code == 422


def test_deal_property_contract_remains_unchanged(client: TestClient) -> None:
    created = client.post(
        "/api/v1/deals",
        json={"name": "Existing contract", "property": {"city": "Existing city"}},
    )
    assert created.status_code == 201
    assert set(created.json()) == {"id", "name", "status", "created_at", "property"}
    assert set(created.json()["property"]) == {
        "id", "address", "city", "asset_type", "area_value", "area_unit"
    }
    assert created.json()["property"]["city"] == "Existing city"
