from database import connect_db, hash_password

def create_admin():
    conn = connect_db()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO role_utilisateur (libelle) VALUES ('MANAGER')")
        cursor.execute("INSERT INTO role_utilisateur (libelle) VALUES ('VENDEUR')")
        conn.commit()  # Validez les changements pour les rôles

        cursor.execute("INSERT INTO type_produit(libelle_type) VALUES ('POISSON'), ('POULET')")
        conn.commit()  # Validez les changements pour les types de produits

        cursor.execute("INSERT INTO mode_paiement(libelle_mode) VALUES ('CASH'), ('DETTE')")
        conn.commit()  # Validez les changements pour les modes de paiement

        hashed_pwd = hash_password("12345")  # Mot de passe par défaut pour le manager
        # Insertion d'un rôle Manager et d'un utilisateur
        cursor.execute("""
            INSERT INTO utilisateur (prenom_ut, nom_ut, tel_ut, mot_de_passe, statut, id_role)
            VALUES ('David', 'Banza', '0812222222', %s, 'ACTIF', 1)
        """, (hashed_pwd,))
    conn.commit()
    print("Admin créé avec succès !")

if __name__ == "__main__":
    create_admin()