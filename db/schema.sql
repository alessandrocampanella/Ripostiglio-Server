-- Ripostiglio: schema PostgreSQL
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,              -- Argon2id
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE rooms (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE categories (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE items (
    id            SERIAL PRIMARY KEY,
    name          TEXT NOT NULL,
    category_id   INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    room_id       INTEGER REFERENCES rooms(id) ON DELETE SET NULL,
    container     TEXT,                        -- es. "Scatola coperchio giallo"
    position      TEXT,                        -- es. "Scaffale superiore"
    notes         TEXT,
    to_find       BOOLEAN NOT NULL DEFAULT FALSE,  -- oggetto ancora da trovare
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX items_room_idx ON items(room_id);
CREATE INDEX items_category_idx ON items(category_id);
