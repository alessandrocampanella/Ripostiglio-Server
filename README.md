# Ripostiglio — server

API (FastAPI + PostgreSQL) per sapere dove sono le cose di casa. Client: `ripostiglio-android`.

## Installazione sul Raspberry

```bash
sudo apt install postgresql python3-venv
sudo -u postgres psql -c "CREATE USER ripostiglio PASSWORD 'una-password'" -c "CREATE DATABASE ripostiglio OWNER ripostiglio"

git clone <url-repo> ~/ripostiglio-server && cd ~/ripostiglio-server
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env        # compila DATABASE_URL e JWT_SECRET

psql -h localhost -U ripostiglio ripostiglio -f db/schema.sql
.venv/bin/python -m app.cli create-user mario mario@example.com   # chiede la password
psql -h localhost -U ripostiglio ripostiglio -f db/seed.sql       # facoltativo: dati iniziali
```

Gli utenti si creano solo da riga di comando (`create-user`, `set-password`): non esiste registrazione pubblica.
Le password sono salvate come hash Argon2id.

## Avvio

```bash
sudo cp deploy/ripostiglio.service /etc/systemd/system/   # controlla utente e percorsi
sudo systemctl enable --now ripostiglio
curl http://127.0.0.1:8000/health
```

Il server ascolta solo su `127.0.0.1`: da fuori si raggiunge tramite Cloudflare Tunnel, senza porte aperte.

## Cloudflare Tunnel

Serve un dominio gestito da Cloudflare.

```bash
cloudflared tunnel login
cloudflared tunnel create ripostiglio
cloudflared tunnel route dns ripostiglio ripostiglio.tuodominio.it
sudo cp deploy/cloudflared-config.example.yml /etc/cloudflared/config.yml   # inserisci TUNNEL_ID e hostname
sudo cloudflared service install
```

## API

Documentazione interattiva su `/docs`. Tutto tranne `/health` e `/auth/login` richiede `Authorization: Bearer <token>`.

| Metodo | Percorso | Note |
|---|---|---|
| POST | `/auth/login` | username o email + password → token (valido `JWT_EXPIRE_DAYS` giorni) |
| GET | `/items` | filtri: `q`, `room_id`, `category_id`, `to_find` |
| POST / PUT / DELETE | `/items`, `/items/{id}` | autore e ultima modifica registrati dal token |
| GET / POST | `/rooms`, `/categories` | |
| GET | `/containers` | contenitori già usati, per i suggerimenti |

Dopo 5 login falliti l'accesso si blocca per 5 minuti.

## Test

Servono un PostgreSQL locale e un database vuoto dedicato (viene azzerato a ogni test):

```bash
.venv/bin/pip install -r requirements-dev.txt
TEST_DATABASE_DSN=postgresql://utente:password@localhost/ripostiglio_test .venv/bin/pytest
```
