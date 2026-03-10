CREATE DATABASE chambre_froide;
USE chambre_froide;

CREATE TABLE role_utilisateur(
    id_role INT AUTO_INCREMENT NOT NULL,
    libelle VARCHAR(30) NOT NULL,
    PRIMARY KEY(id_role)
);

CREATE TABLE utilisateur(
    id_ut INT AUTO_INCREMENT NOT NULL,
    prenom_ut VARCHAR(50) NOT NULL,
    nom_ut VARCHAR(50) NOT NULL,
    tel_ut VARCHAR(15) NOT NULL UNIQUE,
    mot_de_passe VARCHAR(255) NOT NULL,
    statut VARCHAR(30) NOT NULL,
    id_role INT NOT NULL,
    PRIMARY KEY(id_ut),
    CONSTRAINT fk_role_utilisateur FOREIGN KEY(id_role) REFERENCES role_utilisateur(id_role)
);

CREATE TABLE type_produit(
    id_type INT AUTO_INCREMENT NOT NULL,
    libelle_type VARCHAR(30) NOT NULL,
    PRIMARY KEY (id_type)
);

CREATE TABLE produit(
    id_pr INT AUTO_INCREMENT NOT NULL,
    nom_pr VARCHAR(50) NOT NULL,
    prix_carton DECIMAL(15,2) NOT NULL,
    en_stock INT NOT NULL,
    id_type INT NOT NULL,
    date_expiration DATE ,
    PRIMARY KEY(id_pr),
    CONSTRAINT fk_type_produit FOREIGN KEY(id_type) REFERENCES type_produit(id_type)
);

CREATE TABLE client(
    id_client INT AUTO_INCREMENT NOT NULL,
    nom_client VARCHAR(50) NOT NULL,
    prenom_client VARCHAR(50) NOT NULL,
    tel_client VARCHAR(15),
    PRIMARY KEY(id_client)
);

CREATE TABLE mode_paiement(
    id_mode INT AUTO_INCREMENT NOT NULL,
    libelle_mode VARCHAR(30) NOT NULL,
    PRIMARY KEY(id_mode)
);

CREATE TABLE vente(
    id_vente INT AUTO_INCREMENT NOT NULL,
    date_vente DATE NOT NULL,
    id_mode INT NOT NULL,
    id_client INT NOT NULL,
    id_ut INT NOT NULL,
PRIMARY KEY(id_vente),
CONSTRAINT fk_vente_client FOREIGN KEY(id_client) REFERENCES client(id_client),
CONSTRAINT fk_mode_vente FOREIGN KEY(id_mode) REFERENCES mode_paiement(id_mode),
CONSTRAINT fk_vent_utilisateur FOREIGN KEY(id_ut) REFERENCES utilisateur(id_ut)
);

CREATE TABLE detail_vente(
    id_vente INT NOT NULL,
    id_pr INT NOT NULL,
    prix_vente DECIMAL(15,2) NOT NULL,
    quantite INT NOT NULL,
    PRIMARY KEY(id_vente, id_pr),
    CONSTRAINT fk_vente_detail FOREIGN KEY(id_vente) REFERENCES vente(id_vente),
    CONSTRAINT fk_produit_detail FOREIGN KEY(id_pr) REFERENCES produit(id_pr)
);

CREATE TABLE paiement(
    id_pai INT AUTO_INCREMENT NOT NULL,
    date_pai DATE NOT NULL,
    montant_pai DECIMAL(15,2) NOT NULL,
    id_vente INT NOT NULL,  -- Lien vers la vente
    id_vendeur_collecteur INT NOT NULL,  -- Nouveau : vendeur qui a perçu le paiement
    PRIMARY KEY(id_pai),
    CONSTRAINT fk_paiement_vente FOREIGN KEY(id_vente) REFERENCES vente(id_vente),  -- Connexion préservée
    CONSTRAINT fk_paiement_collecteur FOREIGN KEY(id_vendeur_collecteur) REFERENCES utilisateur(id_ut)
);

-- 1. Ajout du post-nom pour le client
ALTER TABLE client ADD COLUMN postnom_client VARCHAR(50) AFTER prenom_client;

-- 2. Gestion spécifique des dettes (Exigence section 3 & 4.3)
CREATE TABLE dette (
    id_dette INT AUTO_INCREMENT PRIMARY KEY,
    id_vente INT NOT NULL,
    montant_total_dette DECIMAL(15,2) NOT NULL, -- Montant initial ou nombre de cartons
    type_dette ENUM('ESPECES', 'CARTONS') NOT NULL, -- 
    date_echeance DATE NOT NULL, -- [cite: 26, 96]
    statut_dette VARCHAR(20) DEFAULT 'NON_SOLDE',
    CONSTRAINT fk_dette_vente FOREIGN KEY(id_vente) REFERENCES vente(id_vente)
);

-- 3. Gestion du retrait ultérieur (Exigence section 1 pt 10)
ALTER TABLE vente ADD COLUMN statut_retrait ENUM('IMMEDIAT', 'ULTERIEUR') DEFAULT 'IMMEDIAT';
ALTER TABLE vente ADD COLUMN date_retrait_effective DATE NULL;