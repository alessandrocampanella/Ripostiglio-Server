#!/bin/bash
# Avvio di Ripostiglio: aggiorna il codice da GitHub e lancia il server.
# Pensato per partire all'avvio del Raspberry in un terminale.

cd "$(dirname "$(readlink -f "$0")")" || exit 1

# All'avvio la rete può non essere ancora pronta: aspetta fino a 60 secondi.
for _ in $(seq 30); do
    git ls-remote -q origin >/dev/null 2>&1 && break
    sleep 2
done

git pull --ff-only || echo "!! git pull non riuscito: avvio la versione già presente"

[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt || echo "!! aggiornamento dipendenze non riuscito"

echo "Ripostiglio in ascolto su http://127.0.0.1:8000"
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

# Se il server si ferma, il terminale resta aperto per leggere l'errore.
read -rp "Server fermo. Premi Invio per chiudere..."
