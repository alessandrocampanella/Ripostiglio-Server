from pathlib import Path

import psycopg

from tests.conftest import TEST_DSN


def test_login_with_username_or_email(client):
    for identifier in ("mario", "MARIO@example.com"):
        response = client.post("/auth/login", json={"username": identifier, "password": "password123"})
        assert response.status_code == 200
        assert response.json()["username"] == "mario"


def test_login_wrong_password_then_locked(client):
    for _ in range(5):
        assert client.post("/auth/login", json={"username": "mario", "password": "x"}).status_code == 401
    assert client.post("/auth/login", json={"username": "mario", "password": "password123"}).status_code == 429


def test_unknown_user_rejected(client):
    assert client.post("/auth/login", json={"username": "nessuno", "password": "x"}).status_code == 401


def test_endpoints_require_token(client):
    assert client.get("/items").status_code == 401
    assert client.get("/items", headers={"Authorization": "Bearer finto"}).status_code == 401


def test_item_lifecycle_records_author(client, auth):
    room = client.post("/rooms", json={"name": "Ripostiglio"}, headers=auth).json()
    category = client.post("/categories", json={"name": "Campeggio"}, headers=auth).json()
    created = client.post(
        "/items",
        json={"name": " Tenda ", "room_id": room["id"], "category_id": category["id"], "position": "Sopra a tutto", "notes": ""},
        headers=auth,
    )
    assert created.status_code == 201
    item = created.json()
    assert item["name"] == "Tenda"
    assert item["notes"] is None
    assert item["created_by"] == "mario"
    assert item["room_name"] == "Ripostiglio"
    assert item["category_name"] == "Campeggio"

    updated = client.put(f"/items/{item['id']}", json={"name": "Tenda", "container": "Scatola blu"}, headers=auth).json()
    assert updated["container"] == "Scatola blu"
    assert updated["room_id"] is None
    assert updated["updated_by"] == "mario"
    assert client.get("/containers", headers=auth).json() == ["Scatola blu"]

    assert client.delete(f"/items/{item['id']}", headers=auth).status_code == 204
    assert client.get("/items", headers=auth).json() == []
    assert client.delete(f"/items/{item['id']}", headers=auth).status_code == 404


def test_search_and_filters(client, auth):
    bagno = client.post("/rooms", json={"name": "Bagno"}, headers=auth).json()
    client.post("/items", json={"name": "Scarpe bici", "room_id": bagno["id"], "container": "Scarpiera bagno"}, headers=auth)
    client.post("/items", json={"name": "Scarpe pioggia", "to_find": True}, headers=auth)
    client.post("/items", json={"name": "Tenda"}, headers=auth)

    def names(**params):
        return [item["name"] for item in client.get("/items", params=params, headers=auth).json()]

    assert names(q="scarpe") == ["Scarpe bici", "Scarpe pioggia"]
    assert names(q="scarpiera BICI") == ["Scarpe bici"]
    assert names(room_id=bagno["id"]) == ["Scarpe bici"]
    assert names(to_find=True) == ["Scarpe pioggia"]
    assert names(q="100%") == []


def test_validation(client, auth):
    assert client.post("/items", json={"name": "  "}, headers=auth).status_code == 422
    assert client.post("/items", json={"name": "X", "room_id": 999}, headers=auth).status_code == 422
    # Una stanza con lo stesso nome non viene duplicata.
    first = client.post("/rooms", json={"name": "Bagno"}, headers=auth).json()
    assert client.post("/rooms", json={"name": "bagno"}, headers=auth).json()["id"] == first["id"]


def test_seed_loads(client, auth):
    seed = (Path(__file__).parent.parent / "db" / "seed.sql").read_text()
    with psycopg.connect(TEST_DSN, autocommit=True) as conn:
        conn.execute(seed)
    items = client.get("/items", headers=auth).json()
    assert len(items) == 35
    assert all(item["created_by"] == "mario" for item in items)
    tazzine = next(item for item in items if item["name"] == "Tazzine Darwin")
    assert (tazzine["room_name"], tazzine["category_name"]) == ("Soggiorno", "Cucina")
