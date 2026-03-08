from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QLabel, QDateEdit, QPushButton,
                             QGroupBox, QFrame, QComboBox)
from PySide6.QtCore import Qt, QDate
from database import (get_sales_by_vendor_id, get_all_sales_detailed,
                      get_remaining_amount_for_debt, get_total_paid_for_debt,
                      get_all_users, is_manager)
from utils import format_currency
from datetime import datetime


class SalesHistoryView(QWidget):
    """Vue d'historique des ventes pour les vendeurs avec KPIs"""

    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.is_manager = is_manager(current_user['id_ut'])
        self.setWindowTitle("Historique des Ventes")
        self.setGeometry(100, 100, 1200, 700)
        self.setup_ui()
        self.load_sales_history()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        main_layout = QVBoxLayout()

        # Titre
        title_text = "Historique des Ventes" if self.is_manager else "Historique de mes Ventes"
        title = QLabel(title_text)
        title.setObjectName("title")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title)

        # Filtres
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Période :"))

        self.date_start = QDateEdit()
        self.date_start.setDate(QDate.currentDate().addMonths(-1))
        self.date_start.dateChanged.connect(self.load_sales_history)
        filters_layout.addWidget(self.date_start)

        filters_layout.addWidget(QLabel("à"))

        self.date_end = QDateEdit()
        self.date_end.setDate(QDate.currentDate())
        self.date_end.dateChanged.connect(self.load_sales_history)
        filters_layout.addWidget(self.date_end)

        # Filtre par vendeur (seulement pour les managers)
        if self.is_manager:
            filters_layout.addWidget(QLabel("Vendeur :"))
            self.vendor_filter = QComboBox()
            self.vendor_filter.addItem("TOUS LES VENDEURS", "")
            # Charger la liste des vendeurs
            users = get_all_users()
            for user in users:
                if user['statut'] == 'ACTIF':
                    full_name = f"{user['prenom_ut']} {user['nom_ut']}"
                    self.vendor_filter.addItem(full_name, user['id_ut'])
            self.vendor_filter.currentIndexChanged.connect(self.load_sales_history)
            filters_layout.addWidget(self.vendor_filter)

        btn_refresh = QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.load_sales_history)
        filters_layout.addWidget(btn_refresh)

        filters_layout.addStretch()
        main_layout.addLayout(filters_layout)

        # KPIs
        self.kpis_widget = QWidget()
        kpis_layout = QHBoxLayout(self.kpis_widget)

        # KPI 1: Montant total sans dette
        kpi1_group = QGroupBox("Montant Total Sans Dette")
        kpi1_layout = QVBoxLayout()
        self.label_total_no_debt = QLabel("0,00 FC")
        self.label_total_no_debt.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #27ae60;
                text-align: center;
            }
        """)
        self.label_total_no_debt.setAlignment(Qt.AlignCenter)
        kpi1_layout.addWidget(self.label_total_no_debt)
        kpi1_group.setLayout(kpi1_layout)
        kpis_layout.addWidget(kpi1_group)

        # KPI 2: Montant total avec dette
        kpi2_group = QGroupBox("Montant Total Avec Dette")
        kpi2_layout = QVBoxLayout()
        self.label_total_with_debt = QLabel("0,00 FC")
        self.label_total_with_debt.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #e74c3c;
                text-align: center;
            }
        """)
        self.label_total_with_debt.setAlignment(Qt.AlignCenter)
        kpi2_layout.addWidget(self.label_total_with_debt)
        kpi2_group.setLayout(kpi2_layout)
        kpis_layout.addWidget(kpi2_group)

        # KPI 3: Montant total avec sans dettes et avances
        kpi3_group = QGroupBox("Total Réel (Sans Dette + Avances)")
        kpi3_layout = QVBoxLayout()
        self.label_total_real = QLabel("0,00 FC")
        self.label_total_real.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #3498db;
                text-align: center;
            }
        """)
        self.label_total_real.setAlignment(Qt.AlignCenter)
        kpi3_layout.addWidget(self.label_total_real)
        kpi3_group.setLayout(kpi3_layout)
        kpis_layout.addWidget(kpi3_group)

        main_layout.addWidget(self.kpis_widget)

        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # Tableau des ventes
        self.table_sales = QTableWidget()
        if self.is_manager:
            self.table_sales.setColumnCount(9)
            self.table_sales.setHorizontalHeaderLabels([
                "Date", "Vendeur", "Client", "Mode Paiement", "Montant Total",
                "Montant Payé", "Reste à Payer", "Statut Dette", "Actions"
            ])
            self.table_sales.setColumnWidth(0, 100)
            self.table_sales.setColumnWidth(1, 150)
            self.table_sales.setColumnWidth(2, 200)
            self.table_sales.setColumnWidth(3, 120)
            self.table_sales.setColumnWidth(4, 120)
            self.table_sales.setColumnWidth(5, 120)
            self.table_sales.setColumnWidth(6, 120)
            self.table_sales.setColumnWidth(7, 120)
            self.table_sales.setColumnWidth(8, 150)
        else:
            self.table_sales.setColumnCount(8)
            self.table_sales.setHorizontalHeaderLabels([
                "Date", "Client", "Mode Paiement", "Montant Total",
                "Montant Payé", "Reste à Payer", "Statut Dette", "Actions"
            ])
            self.table_sales.setColumnWidth(0, 100)
            self.table_sales.setColumnWidth(1, 200)
            self.table_sales.setColumnWidth(2, 120)
            self.table_sales.setColumnWidth(3, 120)
            self.table_sales.setColumnWidth(4, 120)
            self.table_sales.setColumnWidth(5, 120)
            self.table_sales.setColumnWidth(6, 120)
            self.table_sales.setColumnWidth(7, 150)

        main_layout.addWidget(self.table_sales)

        self.setLayout(main_layout)

    def load_sales_history(self):
        """Charge l'historique des ventes selon les filtres"""
        start_date = self.date_start.date().toString("yyyy-MM-dd")
        end_date = self.date_end.date().toString("yyyy-MM-dd")

        # Récupérer les ventes selon le contexte
        if self.is_manager:
            # Manager : peut filtrer par vendeur ou voir tous
            selected_vendor_id = self.vendor_filter.currentData()
            if selected_vendor_id:
                # Manager a choisi un vendeur spécifique
                all_sales = get_sales_by_vendor_id(selected_vendor_id, start_date, end_date)
            else:
                # Manager voit tous les vendeurs
                all_sales = get_all_sales_detailed()
        else:
            # Vendeur : ne voit que ses propres ventes
            all_sales = get_sales_by_vendor_id(self.current_user['id_ut'], start_date, end_date)

        # Filtrage supplémentaire par dates si on a récupéré toutes les ventes
        if self.is_manager and not self.vendor_filter.currentData():
            # Manager voit tous les vendeurs - filtrer par dates
            filtered_sales = []
            for sale in all_sales:
                sale_date = str(sale.get('date_vente', ''))
                if start_date <= sale_date <= end_date:
                    filtered_sales.append(sale)
        else:
            # Déjà filtré par vendeur et dates
            filtered_sales = all_sales

        # Calculer les KPIs seulement si c'est un vendeur ou si le manager regarde un vendeur spécifique
        show_kpis = not self.is_manager or (self.is_manager and self.vendor_filter.currentData())

        if show_kpis:
            # Calculer les KPIs
            total_no_debt = 0  # Ventes payées immédiatement (sans dette)
            total_with_debt = 0  # Montant total des ventes avec dette
            total_real = 0  # Total réel = sans dette + avances sur dettes

            for sale in filtered_sales:
                sale_amount = float(sale.get('montant_total', 0) or 0)
                debt_id = sale.get('id_dette')

                if debt_id:
                    # Vente avec dette
                    total_with_debt += sale_amount
                    remaining = get_remaining_amount_for_debt(debt_id)
                    paid = get_total_paid_for_debt(debt_id)
                    total_real += float(paid)  # Avances payées sur la dette
                else:
                    # Vente sans dette (payée immédiatement)
                    total_no_debt += sale_amount
                    total_real += sale_amount

            # Mettre à jour les KPIs
            self.label_total_no_debt.setText(format_currency(total_no_debt))
            self.label_total_with_debt.setText(format_currency(total_with_debt))
            self.label_total_real.setText(format_currency(total_real))

            # Afficher les KPIs
            self.kpis_widget.show()
        else:
            # Masquer les KPIs pour les managers qui voient tous les vendeurs
            self.kpis_widget.hide()

        # Remplir le tableau
        self.table_sales.setRowCount(len(filtered_sales))

        for row, sale in enumerate(filtered_sales):
            # Date (toujours colonne 0)
            self.table_sales.setItem(row, 0, QTableWidgetItem(str(sale.get('date_vente', ''))))

            # Calcul du décalage pour les colonnes suivantes
            col_offset = 1 if self.is_manager else 0

            # Vendeur (seulement pour les managers - colonne 1)
            if self.is_manager:
                vendor_name = sale.get('vendeur', 'N/A')
                self.table_sales.setItem(row, 1, QTableWidgetItem(vendor_name))

            # Client (colonne 1 + col_offset)
            client_name = sale.get('client', 'N/A')
            self.table_sales.setItem(row, 1 + col_offset, QTableWidgetItem(client_name))

            # Mode de paiement (colonne 2 + col_offset)
            payment_mode = sale.get('mode_paiement', 'N/A')
            self.table_sales.setItem(row, 2 + col_offset, QTableWidgetItem(payment_mode))

            # Montant total (colonne 3 + col_offset)
            total_amount = float(sale.get('montant_total', 0) or 0)
            self.table_sales.setItem(row, 3 + col_offset, QTableWidgetItem(format_currency(total_amount)))

            debt_id = sale.get('id_dette')
            if debt_id:
                # Vente avec dette
                paid_amount = float(get_total_paid_for_debt(debt_id))
                remaining_amount = float(get_remaining_amount_for_debt(debt_id))

                self.table_sales.setItem(row, 4 + col_offset, QTableWidgetItem(format_currency(paid_amount)))
                self.table_sales.setItem(row, 5 + col_offset, QTableWidgetItem(format_currency(remaining_amount)))
                self.table_sales.setItem(row, 6 + col_offset, QTableWidgetItem("EN COURS"))
            else:
                # Vente sans dette
                self.table_sales.setItem(row, 4 + col_offset, QTableWidgetItem(format_currency(total_amount)))
                self.table_sales.setItem(row, 5 + col_offset, QTableWidgetItem(format_currency(0)))
                self.table_sales.setItem(row, 6 + col_offset, QTableWidgetItem("PAYÉ"))

            # Actions (colonne 7 + col_offset)
            action_widget = QWidget()
            action_layout = QHBoxLayout()

            btn_invoice = QPushButton("📄 Facture")
            btn_invoice.clicked.connect(lambda checked, sid=sale.get('id_vente'): self.show_invoice(sid))
            action_layout.addWidget(btn_invoice)

            action_layout.setContentsMargins(0, 0, 0, 0)
            action_widget.setLayout(action_layout)
            self.table_sales.setCellWidget(row, 7 + col_offset, action_widget)

    def show_invoice(self, sale_id):
        """Affiche la facture d'une vente"""
        try:
            from invoice_generator import open_invoice
            # Générer le nom de fichier de la facture
            invoice_filename = f"factures/vente_{sale_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            # Essayer d'ouvrir la facture existante ou en générer une nouvelle
            import os
            if os.path.exists(f"factures/vente_{sale_id}.pdf"):
                open_invoice(f"factures/vente_{sale_id}.pdf")
            else:
                # Pour une vraie implémentation, il faudrait récupérer les données de vente
                # et générer la facture. Pour l'instant, on affiche juste un message
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Facture",
                                      f"Facture pour la vente #{sale_id}\nFonctionnalité à implémenter")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", f"Impossible d'ouvrir la facture: {str(e)}")