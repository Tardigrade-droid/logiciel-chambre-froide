#!/usr/bin/env python3
"""
Script de migration pour ajouter id_vendeur_collecteur aux paiements existants
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import connect_db


def migrate_payment_collectors():
    """
    Migration : Ajoute id_vendeur_collecteur aux paiements existants
    Utilise le vendeur de la vente comme collecteur par défaut
    """
    print("🚀 Début de la migration des collecteurs de paiement...")

    conn = None
    try:
        conn = connect_db()
        print("✅ Connexion à la base de données établie")

        with conn.cursor() as cursor:
            # Vérifier que la colonne existe
            cursor.execute("SHOW COLUMNS FROM paiement LIKE 'id_vendeur_collecteur'")
            if not cursor.fetchone():
                raise Exception("Colonne 'id_vendeur_collecteur' n'existe pas dans la table paiement")

            print("✅ Colonne id_vendeur_collecteur présente")

            # Compter les paiements sans collecteur
            cursor.execute("SELECT COUNT(*) as count FROM paiement WHERE id_vendeur_collecteur IS NULL")
            result = cursor.fetchone()
            null_count = result['count'] if result else 0

            if null_count == 0:
                print("ℹ️ Tous les paiements ont déjà un collecteur défini")
                return True

            print(f"📊 {null_count} paiements à migrer")

            # Mettre à jour les paiements avec le vendeur de la vente
            sql_update = """
                UPDATE paiement p
                JOIN vente v ON p.id_vente = v.id_vente
                SET p.id_vendeur_collecteur = v.id_ut
                WHERE p.id_vendeur_collecteur IS NULL
            """
            cursor.execute(sql_update)
            updated_count = cursor.rowcount

            conn.commit()
            print(f"✅ Migration terminée : {updated_count} paiements mis à jour")

            # Vérification
            cursor.execute("SELECT COUNT(*) as count FROM paiement WHERE id_vendeur_collecteur IS NULL")
            result = cursor.fetchone()
            remaining_null = result['count'] if result else 0

            if remaining_null == 0:
                print("✅ Vérification réussie : Aucun paiement sans collecteur")
                return True
            else:
                print(f"⚠️ Vérification échouée : {remaining_null} paiements encore sans collecteur")
                return False

    except Exception as e:
        print(f"❌ Erreur lors de la migration : {e}")
        import traceback
        print("🔍 Détails de l'erreur :")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
            print("🔌 Connexion fermée")


if __name__ == "__main__":
    print("=" * 60)
    print("🔄 MIGRATION PAIEMENTS - AJOUT COLLECTEURS")
    print("=" * 60)

    # Demander confirmation
    response = input("\n⚠️  Cette migration va définir le vendeur de chaque vente comme collecteur\n"
                     "   pour tous les paiements existants.\n"
                     "   Voulez-vous continuer ? (oui/non) : ").strip().lower()

    if response not in ['oui', 'o', 'yes', 'y']:
        print("❌ Migration annulée.")
        sys.exit(0)

    # Exécuter la migration
    success = migrate_payment_collectors()

    if success:
        print("\n🎉 Migration terminée avec succès !")
    else:
        print("\n💥 Échec de la migration.")
        sys.exit(1)