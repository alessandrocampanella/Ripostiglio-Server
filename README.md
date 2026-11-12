# Ripostiglio — server

API (FastAPI + PostgreSQL) per sapere dove sono le cose di casa. Client: `ripostiglio-android`.

## Installazione sul Raspberry

Richiede Python 3.10 o superiore. Il progetto va in `~/servers/Ripostiglio-Server`.

```bash
sudo apt install postgresql python3-venv
sudo -u postgres psql -c "CREATE USER ripostiglio PASSWORD 'una-password'" -c "CREATE DATABASE ripostiglio OWNER ripostiglio"

cd ~/servers
git clone https://github.com/alessandrocampanella/Ripostiglio-Server.git
cd Ripostiglio-Server
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
~/servers/Ripostiglio-Server/ripostiglio.sh
```

Lo script fa `git pull`, aggiorna le dipendenze e avvia il server su `127.0.0.1:8000`.
Per farlo partire all'accensione, registralo come gli altri server in `~/servers`.
Il `git pull` all'avvio richiede che git sul Raspberry abbia le credenziali salvate (chiave SSH o credential helper).

Il server ascolta solo su `127.0.0.1`: da fuori si raggiunge tramite Tailscale Funnel, senza porte aperte.

## Accesso da internet: Tailscale Funnel

Funnel pubblica il server su un indirizzo HTTPS fisso (`https://<macchina>.<tailnet>.ts.net`) senza aprire porte.

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
sudo tailscale funnel --bg 8000
```

`--bg` rende la configurazione permanente: dopo un riavvio Funnel riparte da solo.
Nella console di Tailscale disattiva la scadenza della chiave per il Raspberry (Machines → ⋯ → Disable key expiry).

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
