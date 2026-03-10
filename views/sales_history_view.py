from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QLabel, QDateEdit, QPushButton,
                             QGroupBox, QFrame, QComboBox)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QBrush, QFont
from database import (get_sales_by_vendor_id, get_all_sales_detailed,
                      get_remaining_amount_for_debt, get_total_paid_for_debt,
                      get_all_users, is_manager, get_sale_by_id)
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

        # (KPIs supprimés - section enlevée)
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

        # Les KPI ayant été supprimés, procéder directement au remplissage du tableau
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
                
                item_reste = QTableWidgetItem(format_currency(remaining_amount))
                font = QFont()
                font.setBold(True)
                item_reste.setFont(font)
                color = QColor("#e74c3c") if remaining_amount > 0 else QColor("#27ae60")
                item_reste.setForeground(QBrush(color))
                self.table_sales.setItem(row, 5 + col_offset, item_reste)
                
                statut = "EN COURS" if remaining_amount > 0 else "PAYÉ"
                item_statut = QTableWidgetItem(statut)
                item_statut.setFont(font)
                item_statut.setForeground(QBrush(color))
                self.table_sales.setItem(row, 6 + col_offset, item_statut)
            else:
                # Vente sans dette
                self.table_sales.setItem(row, 4 + col_offset, QTableWidgetItem(format_currency(total_amount)))
                self.table_sales.setItem(row, 5 + col_offset, QTableWidgetItem(format_currency(0)))
                
                item_statut = QTableWidgetItem("PAYÉ")
                font = QFont()
                font.setBold(True)
                item_statut.setFont(font)
                item_statut.setForeground(QBrush(QColor("#27ae60")))
                self.table_sales.setItem(row, 6 + col_offset, item_statut)

            # Actions (colonne 7 + col_offset)
            action_widget = QWidget()
            action_layout = QHBoxLayout()

            btn_details = QPushButton("👁️ Voir")
            btn_details.setStyleSheet("background-color: #9b59b6; color: white;")
            btn_details.clicked.connect(lambda checked, sid=sale.get('id_vente'): self.show_sale_details(sid))
            action_layout.addWidget(btn_details)

            action_layout.setContentsMargins(0, 0, 0, 0)
            action_widget.setLayout(action_layout)
            self.table_sales.setCellWidget(row, 7 + col_offset, action_widget)

    def show_sale_details(self, sale_id):
        """Affiche les détails d'une vente dans une boîte de dialogue"""
        try:
            # Importer SaleDetailsDialog depuis sales_view
            from .sales_view import SaleDetailsDialog
            dialog = SaleDetailsDialog(sale_id, self)
            dialog.exec()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", f"Impossible d'afficher les détails: {str(e)}")