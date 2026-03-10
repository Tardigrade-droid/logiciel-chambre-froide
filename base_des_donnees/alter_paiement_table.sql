-- Script pour ajouter la colonne id_vendeur_collecteur à la table paiement

USE chambre_froide;

-- Ajouter la colonne id_vendeur_collecteur
ALTER TABLE paiement
ADD COLUMN id_vendeur_collecteur INT NOT NULL;

-- Ajouter la contrainte de clé étrangère
ALTER TABLE paiement
ADD CONSTRAINT fk_paiement_collecteur
FOREIGN KEY (id_vendeur_collecteur) REFERENCES utilisateur(id_ut);

-- Mettre à jour les paiements existants avec le vendeur de la vente
UPDATE paiement p
JOIN vente v ON p.id_vente = v.id_vente
SET p.id_vendeur_collecteur = v.id_ut
WHERE p.id_vendeur_collecteur IS NULL OR p.id_vendeur_collecteur = 0;