#!/usr/bin/env python3
"""
Script de migration pour harmoniser la base de données :
Ajoute des paiements automatiques pour toutes les ventes cash existantes
qui n'ont pas encore de paiement enregistré.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    connect_db, get_sale_by_id, record_payment
)


def migrate_cash_sales_payments():
    """
    Migration : Ajoute des paiements pour toutes les ventes cash sans paiement
    """
    print("🚀 Début de la migration des paiements cash...")

    conn = None
    try:
        conn = connect_db()
        print("✅ Connexion à la base de données établie")

        with conn.cursor() as cursor:
            # Vérifier que les tables nécessaires existent
            print("🔍 Vérification des tables...")
            cursor.execute("SHOW TABLES LIKE 'vente'")
            if not cursor.fetchone():
                raise Exception("Table 'vente' n'existe pas")

            cursor.execute("SHOW TABLES LIKE 'detail_vente'")
            if not cursor.fetchone():
                raise Exception("Table 'detail_vente' n'existe pas")

            cursor.execute("SHOW TABLES LIKE 'mode_paiement'")
            if not cursor.fetchone():
                raise Exception("Table 'mode_paiement' n'existe pas")

            cursor.execute("SHOW TABLES LIKE 'paiement'")
            if not cursor.fetchone():
                raise Exception("Table 'paiement' n'existe pas")

            print("✅ Toutes les tables nécessaires sont présentes")
            # Récupérer toutes les ventes avec leur mode de paiement
            sql = """
                SELECT v.id_vente, v.date_vente, v.id_mode,
                       SUM(dv.prix_vente * dv.quantite) as montant_total,
                       mp.libelle_mode as mode_paiement
                FROM vente v
                JOIN detail_vente dv ON v.id_vente = dv.id_vente
                JOIN mode_paiement mp ON v.id_mode = mp.id_mode
                GROUP BY v.id_vente, v.date_vente, v.id_mode, mp.libelle_mode
                ORDER BY v.date_vente DESC
            """
            print("🔍 Exécution de la requête de récupération des ventes...")
            cursor.execute(sql)
            sales = cursor.fetchall()
            print(f"📊 {len(sales)} ventes trouvées")

            migrated_count = 0
            skipped_count = 0

            for i, sale in enumerate(sales):
                if i % 10 == 0:  # Afficher la progression tous les 10 éléments
                    print(f"🔄 Traitement de la vente {i+1}/{len(sales)}...")

                sale_id = sale['id_vente']
                sale_date = sale['date_vente']
                payment_mode_id = sale['id_mode']
                total_amount = sale['montant_total']
                mode_libelle = sale['mode_paiement']

                # Vérifier si c'est une vente cash (pas une dette)
                if mode_libelle.upper() != 'DETTE':
                    # Vérifier si un paiement existe déjà pour cette vente
                    cursor.execute("SELECT COUNT(*) as count FROM paiement WHERE id_vente = %s", (sale_id,))
                    result = cursor.fetchone()
                    payment_exists = result['count'] > 0 if result else False

                    if not payment_exists:
                        # Créer le paiement avec la date de la vente
                        payment_date = sale_date
                        print(f"💰 Ajout paiement pour vente #{sale_id} - {total_amount}€ le {payment_date}")
                        record_payment(sale_id, float(total_amount), payment_date)
                        migrated_count += 1
                    else:
                        skipped_count += 1
                else:
                    print(f"⏭️ Vente #{sale_id} ignorée (dette)")

            print("💾 Validation des changements...")
            conn.commit()
            print(f"""
✅ Migration terminée !
📊 Ventes migrées : {migrated_count}
📊 Ventes ignorées (déjà payées) : {skipped_count}
📊 Total traité : {len(sales)}""")

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

    return True


def verify_migration():
    """
    Vérifie que la migration s'est bien déroulée
    """
    print("\n🔍 Vérification de la migration...")

    conn = None
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            # Compter les ventes cash (toutes les ventes sauf celles avec mode 'DETTE')
            sql_cash_sales = """
                SELECT COUNT(DISTINCT v.id_vente) as cash_count
                FROM vente v
                JOIN mode_paiement mp ON v.id_mode = mp.id_mode
                WHERE mp.libelle_mode != 'DETTE'
            """
            cursor.execute(sql_cash_sales)
            result = cursor.fetchone()
            cash_sales_count = result['cash_count'] if result else 0

            # Compter les paiements pour les ventes cash
            sql_payments = """
                SELECT COUNT(DISTINCT p.id_vente) as payment_count
                FROM paiement p
                JOIN vente v ON p.id_vente = v.id_vente
                JOIN mode_paiement mp ON v.id_mode = mp.id_mode
                WHERE mp.libelle_mode != 'DETTE'
            """
            cursor.execute(sql_payments)
            result = cursor.fetchone()
            payments_count = result['payment_count'] if result else 0

            print(f"📊 Ventes cash : {cash_sales_count}")
            print(f"📊 Paiements pour ventes cash : {payments_count}")

            if cash_sales_count == payments_count:
                print("✅ Migration réussie : Tous les paiements sont présents !")
                return True
            else:
                print(f"⚠️ Incohérence détectée : {cash_sales_count - payments_count} paiement(s) manquant(s)")
                return False

    except Exception as e:
        print(f"❌ Erreur lors de la vérification : {e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🔄 MIGRATION BASE DE DONNÉES - PAIEMENTS CASH")
    print("=" * 60)

    # Demander confirmation
    response = input("\n⚠️  Cette migration va ajouter des paiements pour toutes les ventes cash existantes.\n"
                     "   Voulez-vous continuer ? (oui/non) : ").strip().lower()

    if response not in ['oui', 'o', 'yes', 'y']:
        print("❌ Migration annulée.")
        sys.exit(0)

    # Exécuter la migration
    success = migrate_cash_sales_payments()

    if success:
        # Vérifier le résultat
        verify_migration()
        print("\n🎉 Migration terminée avec succès !")
    else:
        print("\n💥 Échec de la migration.")
        sys.exit(1)