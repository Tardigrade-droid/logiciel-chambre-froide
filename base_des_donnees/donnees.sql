INSERT INTO role_utilisateur(libelle) VALUES('VENDEUR'),('MANAGER');

INSERT INTO utilisateur(prenom_ut, nom_ut, tel_ut, mot_de_passe, statut, id_role) VALUES
('Sam', 'Nkulu', '0894567890', '123456789', 'actif', 1),
('Paul', 'Tshilu', '0990345678', '0557799', 'inactif', 1),
('Gregoire', 'Bola', '0823467890', '12340987', 'actif', 2);

INSERT INTO type_produit(libelle_type) VALUES ('POISSON'),('POULET');

INSERT INTO produit(nom_pr, prix_carton, en_stock, id_type, date_expiration) VALUES
('CARTON POISSON', 100000, 20, 1, '2028-08-18'),
('CARTON POULET', 150000, 20, 1, '2028-08-18');

INSERT INTO client(prenom_client, nom_client, tel_client) VALUES
('Romain', 'Banza', '0999007755'),
('Chimelle', 'Kongo', '08934221188'),
('Francois', 'Ntambwe', '0999722565');

INSERT INTO mode_paiement(libelle_mode) VALUES ('CASH'), ('DETTE'), ('RECUPERER');

INSERT INTO vente(date_vente, id_mode, id_client, id_ut) VALUES
('2026-02-28', 1, 1, 1),
('2026-03-30', 2, 2, 1);

INSERT INTO detail_vente(id_vente, id_pr, prix_vente, quantite) VALUES 
(1, 2, 150000, 2),
(1, 1, 100000, 1),
(2, 1, 100000, 3);

INSERT INTO paiement(date_pai, montant_pai, id_vente) VALUES
('2026-02-28', 400000, 1),
('2026-02-30', 200000, 2);