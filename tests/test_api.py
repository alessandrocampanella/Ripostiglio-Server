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


def test_private_items_only_visible_to_author(client, auth, other_auth):
    private = client.post("/items", json={"name": "Regalo", "container": "Scatola segreta", "is_public": False}, headers=auth).json()
    public = client.post("/items", json={"name": "Tenda"}, headers=auth).json()
    assert (private["is_public"], public["is_public"]) == (False, True)

    def names(headers):
        return [item["name"] for item in client.get("/items", headers=headers).json()]

    assert names(auth) == ["Regalo", "Tenda"]
    assert names(other_auth) == ["Tenda"]
    assert client.get("/containers", headers=other_auth).json() == []

    # Per gli altri l'oggetto privato non esiste: né modifica né eliminazione.
    url = f"/items/{private['id']}"
    assert client.put(url, json={"name": "Mio"}, headers=other_auth).status_code == 404
    assert client.delete(url, headers=other_auth).status_code == 404
    assert names(auth) == ["Regalo", "Tenda"]


def test_only_author_changes_visibility(client, auth, other_auth):
    item = client.post("/items", json={"name": "Tenda"}, headers=auth).json()
    url = f"/items/{item['id']}"

    # Un altro utente può modificare un oggetto pubblico, ma non renderlo privato.
    assert client.put(url, json={"name": "Tenda blu"}, headers=other_auth).json()["updated_by"] == "lucia"
    assert client.put(url, json={"name": "Tenda blu", "is_public": False}, headers=other_auth).status_code == 403

    assert client.put(url, json={"name": "Tenda blu", "is_public": False}, headers=auth).json()["is_public"] is False
    assert client.get("/items", headers=other_auth).json() == []


def test_author_color_is_fixed_per_user(client, auth, other_auth):
    mine = [client.post("/items", json={"name": name}, headers=auth).json() for name in ("Uno", "Due")]
    hue = client.get("/me", headers=auth).json()["color_hue"]
    assert 0 <= hue < 360
    assert [item["created_by_hue"] for item in mine] == [hue, hue]
    listed = client.get("/items", headers=other_auth).json()
    assert {(item["created_by"], item["created_by_hue"]) for item in listed} == {("mario", hue)}


def test_migration_upgrades_old_database(client, auth):
    migration = (Path(__file__).parent.parent / "db" / "migrations" / "001_visibilita_e_colore_utente.sql").read_text()
    with psycopg.connect(TEST_DSN, autocommit=True) as conn:
        conn.execute("ALTER TABLE items DROP COLUMN is_public; ALTER TABLE users DROP COLUMN color_hue;")
        conn.execute("INSERT INTO items (name) VALUES ('Vecchio')")
        for _ in range(2):  # rieseguibile
            conn.execute(migration)
        assert conn.execute("SELECT count(*) FROM users WHERE color_hue BETWEEN 0 AND 359").fetchone()[0] == 2
    assert [item["is_public"] for item in client.get("/items", headers=auth).json()] == [True]


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
