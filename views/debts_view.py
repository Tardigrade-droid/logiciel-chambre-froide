from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QLabel, QPushButton,
                             QDateEdit, QComboBox, QMessageBox, QFormLayout,
                             QLineEdit, QDoubleSpinBox, QProgressBar, QGroupBox)
from PySide6.QtCore import Qt, QDate
from database import (get_all_debts, update_debt_status, 
                      is_manager, get_debt_by_id,
                      get_remaining_amount_for_debt, record_payment,
                      get_payments_for_debt, get_total_paid_for_debt)


class DebtsView(QWidget):
    """Vue pour la gestion des dettes"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        
        self.setWindowTitle("Suivi des Dettes")
        self.setGeometry(100, 100, 1200, 600)
        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        main_layout = QVBoxLayout()
        
        # Titre
        title = QLabel("Suivi des Dettes Clients")
        title.setObjectName("title")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title)
        
        # Onglets
        self.tabs = QTabWidget()
        
        # Onglet 1 : Clients débiteurs
        self.tab_debtors = QWidget()
        self.setup_debtors_tab()
        self.tabs.addTab(self.tab_debtors, "👥 Clients Débiteurs")
        
        # Onglet 2 : Enregistrer un paiement (pour tous les utilisateurs)
        self.tab_record_payment = QWidget()
        self.setup_record_payment_tab()
        self.tabs.addTab(self.tab_record_payment, "💰 Enregistrer Paiement")
        
        # Onglet 3 : Gérer les dettes (manager seulement)
        if is_manager(self.current_user['id_ut']):
            self.tab_manage_debts = QWidget()
            self.setup_manage_debts_tab()
            self.tabs.addTab(self.tab_manage_debts, "⚙️ Gérer les Dettes")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
        
        # Charger les données
        self.refresh_debtors()
        if is_manager(self.current_user['id_ut']):
            self.refresh_manage_debts()

    def setup_debtors_tab(self):
        """Onglet des clients débiteurs"""
        layout = QVBoxLayout()
        
        # Filtres
        filters_layout = QHBoxLayout()
        
        self.filter_type = QComboBox()
        self.filter_type.addItems(["TOUS", "ARGENT", "CARTONS"])
        self.filter_type.currentTextChanged.connect(self.refresh_debtors)
        filters_layout.addWidget(QLabel("Type :"))
        filters_layout.addWidget(self.filter_type)
        
        self.filter_status = QComboBox()
        self.filter_status.addItems(["NON_SOLDE", "SOLDE", "TOUS"])
        self.filter_status.currentTextChanged.connect(self.refresh_debtors)
        filters_layout.addWidget(QLabel("Statut :"))
        filters_layout.addWidget(self.filter_status)
        
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.clicked.connect(self.refresh_debtors)
        filters_layout.addWidget(btn_refresh)
        filters_layout.addStretch()
        
        layout.addLayout(filters_layout)
        
        # Tableau
        self.table_debtors = QTableWidget()
        self.table_debtors.setColumnCount(9)
        self.table_debtors.setHorizontalHeaderLabels([
            "Client", "Téléphone", "Type Dette", "Montant Initial", "Montant Restant", "Date Échéance", "Statut", "Jours Restants", "Action"
        ])
        self.table_debtors.setColumnWidth(0, 200)
        self.table_debtors.setColumnWidth(1, 120)
        self.table_debtors.setColumnWidth(2, 100)
        self.table_debtors.setColumnWidth(3, 120)
        self.table_debtors.setColumnWidth(4, 120)
        self.table_debtors.setColumnWidth(5, 120)
        self.table_debtors.setColumnWidth(6, 100)
        self.table_debtors.setColumnWidth(7, 120)
        self.table_debtors.setColumnWidth(8, 100)
        
        layout.addWidget(self.table_debtors)
        
        self.tab_debtors.setLayout(layout)

    def setup_manage_debts_tab(self):
        """Onglet pour gérer les dettes (manager)"""
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Gérer les dettes (Manager)"))
        
        # Tableau des actions
        self.table_manage_debts = QTableWidget()
        self.table_manage_debts.setColumnCount(7)
        self.table_manage_debts.setHorizontalHeaderLabels([
            "ID Dette", "Client", "Montant", "Type", "Statut", "Date Échéance", "Action"
        ])
        self.table_manage_debts.setColumnWidth(0, 80)
        self.table_manage_debts.setColumnWidth(1, 200)
        self.table_manage_debts.setColumnWidth(2, 100)
        self.table_manage_debts.setColumnWidth(3, 100)
        self.table_manage_debts.setColumnWidth(4, 100)
        self.table_manage_debts.setColumnWidth(5, 120)
        self.table_manage_debts.setColumnWidth(6, 150)
        
        layout.addWidget(self.table_manage_debts)
        
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.clicked.connect(self.refresh_manage_debts)
        layout.addWidget(btn_refresh)
        
        self.tab_manage_debts.setLayout(layout)

    def setup_record_payment_tab(self):
        """Onglet pour enregistrer un paiement"""
        layout = QVBoxLayout()
        
        title = QLabel("Enregistrer un Paiement de Dette")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # Recherche de dette
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("ID Dette :"))
        self.payment_debt_id = QLineEdit()
        search_layout.addWidget(self.payment_debt_id)
        
        btn_search = QPushButton("Charger Dette")
        btn_search.clicked.connect(self.load_debt_for_payment)
        search_layout.addWidget(btn_search)
        search_layout.addStretch()
        
        layout.addLayout(search_layout)
        layout.addSpacing(10)
        
        # Infos dette (GroupBox)
        info_group = QGroupBox("Informations de la Dette")
        info_group_layout = QVBoxLayout()
        self.payment_info_layout = QFormLayout()
        info_group_layout.addLayout(self.payment_info_layout)
        info_group.setLayout(info_group_layout)
        layout.addWidget(info_group)
        
        layout.addSpacing(10)
        
        # Progression de paiement avec barre de progression
        progress_group = QGroupBox("Statut de Paiement")
        progress_layout = QVBoxLayout()
        
        progress_info_layout = QHBoxLayout()
        self.label_total_debt = QLabel("Montant total : 0.00 FC")
        self.label_paid = QLabel("Montant payé : 0.00 FC")
        self.label_remaining = QLabel("Montant restant : 0.00 FC")
        progress_info_layout.addWidget(self.label_total_debt)
        progress_info_layout.addWidget(self.label_paid)
        progress_info_layout.addWidget(self.label_remaining)
        progress_layout.addLayout(progress_info_layout)
        
        self.payment_progress = QProgressBar()
        self.payment_progress.setMinimum(0)
        self.payment_progress.setMaximum(100)
        self.payment_progress.setValue(0)
        progress_layout.addWidget(self.payment_progress)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        layout.addSpacing(10)
        
        # Historique des paiements
        payment_hist_group = QGroupBox("Historique des Paiements")
        payment_hist_layout = QVBoxLayout()
        
        self.table_payment_history = QTableWidget()
        self.table_payment_history.setColumnCount(3)
        self.table_payment_history.setHorizontalHeaderLabels(["Date", "Montant", "Solde Restant"])
        self.table_payment_history.setColumnWidth(0, 150)
        self.table_payment_history.setColumnWidth(1, 150)
        self.table_payment_history.setColumnWidth(2, 150)
        self.table_payment_history.setMaximumHeight(200)
        
        payment_hist_layout.addWidget(self.table_payment_history)
        payment_hist_group.setLayout(payment_hist_layout)
        layout.addWidget(payment_hist_group)
        
        layout.addSpacing(10)
        
        # Formulaire paiement
        payment_form_group = QGroupBox("Nouveau Paiement")
        payment_form = QFormLayout()
        
        self.payment_amount = QDoubleSpinBox()
        self.payment_amount.setMinimum(0)
        self.payment_amount.setMaximum(999999)
        self.payment_amount.setDecimals(2)
        payment_form.addRow("Montant à payer :", self.payment_amount)
        
        self.payment_date = QDateEdit()
        self.payment_date.setDate(QDate.currentDate())
        payment_form.addRow("Date du paiement :", self.payment_date)
        
        payment_form_group.setLayout(payment_form)
        layout.addWidget(payment_form_group)
        
        # Bouton enregistrer
        btn_record = QPushButton("✓ Enregistrer le Paiement")
        btn_record.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px;")
        btn_record.clicked.connect(self.record_debt_payment)
        layout.addWidget(btn_record)
        
        layout.addStretch()
        self.tab_record_payment.setLayout(layout)

    def refresh_debtors(self):
        """Actualise la liste des débiteurs"""
        debts = get_all_debts()
        
        # Appliquer les filtres
        type_filter = self.filter_type.currentText()
        status_filter = self.filter_status.currentText()
        
        filtered_debts = []
        for debt in debts:
            # Filtre par type
            if type_filter != "TOUS" and debt['type_dette'] != type_filter:
                continue
            # Filtre par statut
            if status_filter != "TOUS" and debt['statut_dette'] != status_filter:
                continue
            filtered_debts.append(debt)
        
        self.table_debtors.setRowCount(len(filtered_debts))
        
        today = QDate.currentDate()
        
        for row, debt in enumerate(filtered_debts):
            # Client
            self.table_debtors.setItem(row, 0, QTableWidgetItem(debt['client'] or "N/A"))
            # Téléphone
            self.table_debtors.setItem(row, 1, QTableWidgetItem(debt['tel_client'] or "N/A"))
            # Type
            self.table_debtors.setItem(row, 2, QTableWidgetItem(debt['type_dette']))
            # Montant initial
            self.table_debtors.setItem(row, 3, QTableWidgetItem(f"{debt['montant_total_dette']:.2f}"))
            # Montant restant
            remaining = get_remaining_amount_for_debt(debt['id_dette'])
            self.table_debtors.setItem(row, 4, QTableWidgetItem(f"{remaining:.2f}"))
            # Date échéance
            self.table_debtors.setItem(row, 5, QTableWidgetItem(str(debt['date_echeance'])))
            # Statut
            status_color = "green" if debt['statut_dette'] == "SOLDE" else "red"
            item = QTableWidgetItem(debt['statut_dette'])
            item.setForeground(Qt.green if debt['statut_dette'] == "SOLDE" else Qt.red)
            self.table_debtors.setItem(row, 6, item)
            
            # Jours restants
            date_ech = QDate.fromString(str(debt['date_echeance']), "yyyy-MM-dd")
            days_left = today.daysTo(date_ech)
            self.table_debtors.setItem(row, 7, QTableWidgetItem(f"{days_left} jours"))
            
            # Bouton action
            if debt['statut_dette'] == "NON_SOLDE":
                btn_action = QPushButton("Marquer Payée")
                btn_action.clicked.connect(lambda checked, did=debt['id_dette']: self.mark_as_paid(did))
            else:
                btn_action = QPushButton("Réactiver")
                btn_action.clicked.connect(lambda checked, did=debt['id_dette']: self.reopen_debt(did))
            
            self.table_debtors.setCellWidget(row, 8, btn_action)

    def refresh_manage_debts(self):
        """Actualise le tableau de gestion des dettes"""
        debts = get_all_debts()
        
        self.table_manage_debts.setRowCount(len(debts))
        
        for row, debt in enumerate(debts):
            # ID
            self.table_manage_debts.setItem(row, 0, QTableWidgetItem(str(debt['id_dette'])))
            # Client
            self.table_manage_debts.setItem(row, 1, QTableWidgetItem(debt['client'] or "N/A"))
            # Montant
            self.table_manage_debts.setItem(row, 2, QTableWidgetItem(f"{debt['montant_total_dette']:.2f}"))
            # Type
            self.table_manage_debts.setItem(row, 3, QTableWidgetItem(debt['type_dette']))
            # Statut
            self.table_manage_debts.setItem(row, 4, QTableWidgetItem(debt['statut_dette']))
            # Date échéance
            self.table_manage_debts.setItem(row, 5, QTableWidgetItem(str(debt['date_echeance'])))
            
            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            
            btn_mark_paid = QPushButton("✓ Payée")
            btn_mark_paid.clicked.connect(lambda checked, did=debt['id_dette']: self.mark_as_paid(did))
            
            btn_edit = QPushButton("✏️ Modifier")
            btn_edit.clicked.connect(lambda checked, did=debt['id_dette']: self.edit_debt(did))
            
            action_layout.addWidget(btn_mark_paid)
            action_layout.addWidget(btn_edit)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_widget.setLayout(action_layout)
            
            self.table_manage_debts.setCellWidget(row, 6, action_widget)

    def mark_as_paid(self, debt_id):
        """Marque une dette comme payée"""
        if update_debt_status(debt_id, "SOLDE"):
            QMessageBox.information(self, "Succès", "Dette marquée comme payée")
            self.refresh_debtors()
            if hasattr(self, 'table_manage_debts'):
                self.refresh_manage_debts()
        else:
            QMessageBox.critical(self, "Erreur", "Erreur lors de la mise à jour")

    def reopen_debt(self, debt_id):
        """Réouvre une dette"""
        if update_debt_status(debt_id, "NON_SOLDE"):
            QMessageBox.information(self, "Succès", "Dette réouverte")
            self.refresh_debtors()
        else:
            QMessageBox.critical(self, "Erreur", "Erreur lors de la mise à jour")

    def edit_debt(self, debt_id):
        """Édite une dette (manager)"""
        QMessageBox.information(self, "Info", f"Édition de la dette {debt_id} - À implémenter")

    def show_client_history(self, client_id):
        """Affiche l'historique d'un client"""
        QMessageBox.information(self, "Info", f"Historique client {client_id} - À implémenter")

    def load_debt_for_payment(self):
        """Charge une dette pour enregistrer un paiement"""
        debt_id_text = self.payment_debt_id.text().strip()
        
        if not debt_id_text:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un ID de dette")
            return
        
        try:
            debt_id = int(debt_id_text)
        except ValueError:
            QMessageBox.warning(self, "Erreur", "L'ID de dette doit être un nombre")
            return
        
        debt = get_debt_by_id(debt_id)
        if not debt:
            QMessageBox.warning(self, "Erreur", "Dette non trouvée")
            return
        
        if debt['statut_dette'] == 'SOLDE':
            QMessageBox.information(self, "Info", "Cette dette est déjà complètement payée")
            return
        
        # Nettoyer le layout précédent
        while self.payment_info_layout.count():
            self.payment_info_layout.takeAt(0).widget().deleteLater()
        
        # Afficher les infos
        remaining = get_remaining_amount_for_debt(debt_id)
        total_paid = get_total_paid_for_debt(debt_id)
        
        info_labels = [
            ("Client :", f"{debt['client']}"),
            ("Téléphone :", f"{debt['tel_client']}"),
            ("Type de dette :", f"{debt['type_dette']}"),
            ("Date échéance :", f"{debt['date_echeance']}"),
            ("Statut :", f"{debt['statut_dette']}"),
        ]
        
        for label, value in info_labels:
            self.payment_info_layout.addRow(QLabel(label), QLabel(value))
        
        # Mise à jour de la progression
        total = debt['montant_total_dette']
        self.label_total_debt.setText(f"Montant total : {total:.2f} FC")
        self.label_paid.setText(f"Montant payé : {total_paid:.2f} FC")
        self.label_remaining.setText(f"Montant restant : {remaining:.2f} FC")
        
        # Calculer le pourcentage
        if total > 0:
            percentage = int((total_paid / total) * 100)
            self.payment_progress.setValue(percentage)
        else:
            self.payment_progress.setValue(0)
        
        # Remplir montant avec le montant restant
        self.payment_amount.setValue(remaining)
        
        # Charger l'historique des paiements
        self.load_payment_history(debt_id, remaining)
        
        self.current_debt_id = debt_id
        self.current_vente_id = debt['id_vente']

    def load_payment_history(self, debt_id, current_remaining):
        """Charge l'historique des paiements pour une dette"""
        payments = get_payments_for_debt(debt_id)
        
        self.table_payment_history.setRowCount(len(payments))
        
        for row, payment in enumerate(payments):
            date = QTableWidgetItem(str(payment['date_pai']))
            amount = QTableWidgetItem(f"{payment['montant_pai']:.2f} FC")
            current_remaining += payment['montant_pai']  # Recalculate remaining backwards
            
            self.table_payment_history.setItem(row, 0, date)
            self.table_payment_history.setItem(row, 1, amount)
            self.table_payment_history.setItem(row, 2, QTableWidgetItem(f"{current_remaining:.2f} FC"))

    def record_debt_payment(self):
        """Enregistre un paiement pour une dette"""
        if not hasattr(self, 'current_debt_id'):
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord charger une dette")
            return
        
        montant = self.payment_amount.value()
        
        if montant <= 0:
            QMessageBox.warning(self, "Erreur", "Le montant doit être supérieur à 0")
            return
        
        # Vérifier que le montant ne dépasse pas le montant restant
        remaining = get_remaining_amount_for_debt(self.current_debt_id)
        if montant > remaining:
            reply = QMessageBox.question(
                self,
                "Montant supérieur",
                f"Le montant restant à payer est {remaining:.2f} FC.\nVoulez-vous quand même enregistrer {montant:.2f} FC ?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Enregistrer le paiement
        if record_payment(self.current_vente_id, montant, 
                         self.payment_date.date().toString("yyyy-MM-dd")):
            QMessageBox.information(self, "Succès", 
                                  f"Paiement de {montant:.2f} FC enregistré avec succès !")
            
            # Recharger les infos de la dette pour mettre à jour la progression
            self.load_debt_for_payment()
            self.payment_amount.setValue(0)
            
            # Actualiser les listes
            self.refresh_debtors()
            if hasattr(self, 'table_manage_debts'):
                self.refresh_manage_debts()
        else:
            QMessageBox.critical(self, "Erreur", "Erreur lors de l'enregistrement du paiement")
