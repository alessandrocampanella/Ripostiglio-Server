-- Dati iniziali. Eseguire DOPO aver creato il primo utente:
-- gli oggetti vengono attribuiti all'utente con id più basso.
INSERT INTO rooms (name) VALUES ('Soggiorno'), ('Ripostiglio'), ('Bagno'), ('Balcone');
INSERT INTO categories (name) VALUES
    ('Vestiti'), ('Scarpe'), ('Cucina'), ('Campeggio'), ('Vinted'),
    ('Elettrodomestici'), ('Travestimenti'), ('Elettronica');

INSERT INTO items (name, category_id, room_id, container, position, notes, to_find, created_by_id, updated_by_id)
SELECT v.name, c.id, r.id, v.container, v.position, v.notes, v.to_find, u.id, u.id
FROM (VALUES
    ('Maglie a mezze maniche', 'Vestiti', NULL, 'Scatola coperchio giallo', NULL, NULL, FALSE),
    ('Tuta Arena nera', 'Vestiti', NULL, 'Scatola coperchio giallo', NULL, 'Vinted', FALSE),
    ('Cose sportive Sergio', 'Vestiti', NULL, 'Scatola coperchio giallo', NULL, 'Vinted/Leo', FALSE),
    ('Canotte', 'Vestiti', NULL, 'Scatola coperchio giallo', NULL, NULL, FALSE),
    ('Vestiti estivi per casa', 'Vestiti', NULL, 'Scatola coperchio giallo', NULL, NULL, FALSE),
    ('Pantaloncini estivi per uscire', 'Vestiti', NULL, 'Scatola cobalto', NULL, NULL, FALSE),
    ('Canotte casa e per uscire', 'Vestiti', NULL, 'Scatola cobalto', NULL, NULL, FALSE),
    ('Polo', 'Vestiti', NULL, 'Scatola cobalto', NULL, NULL, FALSE),
    ('Felpe invernali', 'Vestiti', NULL, 'Scatole mamma', NULL, NULL, FALSE),
    ('Felpe invernali per casa', 'Vestiti', NULL, 'Scatole mamma', NULL, NULL, FALSE),
    ('Tazzine Darwin', 'Cucina', 'Soggiorno', 'Cubo in soggiorno', 'Secondo cubo a destra partendo da terra', NULL, FALSE),
    ('Scarpe pioggia', 'Scarpe', NULL, NULL, NULL, NULL, TRUE),
    ('Stivaletti pioggia', 'Scarpe', NULL, NULL, NULL, 'Esistono?', TRUE),
    ('Altre scarpe', 'Scarpe', NULL, NULL, NULL, 'Forse negli scatoli in ripostiglio a sinistra', TRUE),
    ('Scarpe lavoro papi blu scuro', 'Scarpe', 'Bagno', 'Scarpiera bagno', NULL, NULL, FALSE),
    ('Scarpe lavoro papi grigie', 'Scarpe', 'Bagno', 'Scarpiera bagno', NULL, 'A lavare', FALSE),
    ('Scarpe bianche generiche', 'Scarpe', 'Bagno', 'Scarpiera bagno', NULL, 'A lavare', FALSE),
    ('Scarpe bici evidenziatore', 'Scarpe', 'Bagno', 'Scarpiera bagno', NULL, NULL, FALSE),
    ('Puma nere e bianche', 'Scarpe', 'Ripostiglio', 'Scarpiera ripostiglio', NULL, 'Lavoro/uscite', FALSE),
    ('Diadora nere e rosse', 'Scarpe', 'Ripostiglio', 'Scarpiera ripostiglio', NULL, NULL, FALSE),
    ('Scarpe bici Puma arancioni e blu', 'Scarpe', 'Ripostiglio', 'Scarpiera ripostiglio', NULL, NULL, FALSE),
    ('Puma bianche e blu laurea', 'Scarpe', 'Ripostiglio', 'Scatole ripostiglio principali', 'Scaffale superiore', NULL, FALSE),
    ('Scarpe nere e bordeaux', 'Scarpe', 'Ripostiglio', 'Scatole ripostiglio principali', 'Scaffale superiore', NULL, FALSE),
    ('Scarpe Bear blu scuro', 'Scarpe', 'Ripostiglio', 'Scatole ripostiglio principali', 'Scaffale superiore', 'Mie o di Fabi?', FALSE),
    ('Pantofole varie primavera e inverno', 'Scarpe', 'Ripostiglio', 'Scatole ripostiglio principali', 'Scaffale inferiore', NULL, FALSE),
    ('Nike nere 18 anni', 'Scarpe', 'Ripostiglio', 'Scatole ripostiglio a sinistra', NULL, NULL, FALSE),
    ('Tenda', 'Campeggio', 'Ripostiglio', NULL, 'Sopra a tutto', NULL, FALSE),
    ('Allaccio elettrico', 'Campeggio', 'Balcone', 'Mobile fuori al balcone', 'Sopra a tutto, in busta bianca', NULL, FALSE),
    ('Saponi di Marsiglia', 'Campeggio', 'Balcone', 'Mobile fuori al balcone', 'Sopra a tutto, in busta bianca', NULL, FALSE),
    ('Shampoo secco', 'Campeggio', 'Balcone', 'Mobile fuori al balcone', 'Sopra a tutto, in busta bianca', NULL, FALSE),
    ('Sacco a pelo', 'Campeggio', 'Balcone', 'Mobile fuori al balcone', 'Al centro, in busta rossa', NULL, FALSE),
    ('Cose Vinted', 'Vinted', 'Balcone', 'Mobile fuori al balcone', 'Sopra a tutto', NULL, FALSE),
    ('Ventilatori a torre', 'Elettrodomestici', 'Ripostiglio', NULL, 'In alto', NULL, FALSE),
    ('Travestimenti', 'Travestimenti', 'Ripostiglio', 'Scatolo a scacchi', NULL, NULL, FALSE),
    ('Cellulari vecchi', 'Elettronica', 'Soggiorno', 'Mobile Ikea', 'Cassetto Londra, in basso a dx', NULL, FALSE)
) AS v(name, category, room, container, position, notes, to_find)
LEFT JOIN categories c ON c.name = v.category
LEFT JOIN rooms r ON r.name = v.room
LEFT JOIN (SELECT id FROM users ORDER BY id LIMIT 1) u ON TRUE;
