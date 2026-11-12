-- Oggetti pubblici/privati e colore fisso per utente.
-- Si può rieseguire senza danni: ripostiglio.sh la applica a ogni avvio.
ALTER TABLE items ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT TRUE;
-- Il default è valutato riga per riga: ogni utente esistente riceve una tinta casuale diversa.
ALTER TABLE users ADD COLUMN IF NOT EXISTS color_hue SMALLINT NOT NULL DEFAULT floor(random() * 360);
