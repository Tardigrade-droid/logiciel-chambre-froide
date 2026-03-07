from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QLabel, QPushButton,
                             QDateEdit, QComboBox, QMessageBox, QFormLayout,
                             QLineEdit, QDoubleSpinBox, QProgressBar, QGroupBox)
from PySide6.QtCore import Qt, QDate
from database import (get_all_debts, update_debt_status, 
                      is_manager, get_debt_by_id,
                      get_remaining_amount_for_debt, record_payment,
                      get_payments_for_debt, get_total_paid_for_debt, get_sale_by_id)
from utils import format_currency
from invoice_generator import generate_invoice, open_invoice
from datetime import datetime
import os


class DebtsView(QWidget):
    """Vue pour la gestion des dettes"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        
        self.setWindowTitle("Suivi des Dettes")
        self.setGeometry(100, 100, 1400, 900)
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
        self.table_debtors.setColumnCount(8)
        self.table_debtors.setHorizontalHeaderLabels([
            "Client", "Téléphone", "Montant Initial", "Montant Restant", "Date Échéance", "Statut", "Jours Restants", "Action"
        ])
        self.table_debtors.setColumnWidth(0, 200)
        self.table_debtors.setColumnWidth(1, 120)
        self.table_debtors.setColumnWidth(2, 120)
        self.table_debtors.setColumnWidth(3, 120)
        self.table_debtors.setColumnWidth(4, 120)
        self.table_debtors.setColumnWidth(5, 100)
        self.table_debtors.setColumnWidth(6, 120)
        self.table_debtors.setColumnWidth(7, 150)
        
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
        self.label_total_debt = QLabel("Montant total : 0,00 FC")
        self.label_paid = QLabel("Montant payé : 0,00 FC")
        self.label_remaining = QLabel("Montant restant : 0,00 FC")
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
        self.table_payment_history.setMinimumHeight(100)
        
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
            # Montant initial
            self.table_debtors.setItem(row, 2, QTableWidgetItem(format_currency(debt['montant_total_dette'])))
            # Montant restant
            remaining = get_remaining_amount_for_debt(debt['id_dette'])
            self.table_debtors.setItem(row, 3, QTableWidgetItem(format_currency(remaining)))
            # Date échéance
            self.table_debtors.setItem(row, 4, QTableWidgetItem(str(debt['date_echeance'])))
            # Statut
            status_color = "green" if debt['statut_dette'] == "SOLDE" else "red"
            item = QTableWidgetItem(debt['statut_dette'])
            item.setForeground(Qt.green if debt['statut_dette'] == "SOLDE" else Qt.red)
            self.table_debtors.setItem(row, 5, item)
            
            # Jours restants
            date_ech = QDate.fromString(str(debt['date_echeance']), "yyyy-MM-dd")
            days_left = today.daysTo(date_ech)
            self.table_debtors.setItem(row, 6, QTableWidgetItem(f"{days_left} jours"))
            
            # Bouton action
            if debt['statut_dette'] == "NON_SOLDE":
                btn_action = QPushButton("💰 Verser Paiement")
                btn_action.clicked.connect(lambda checked, did=debt['id_dette']: self.navigate_to_payment(did))
            else:
                btn_action = QPushButton("📋 Historique")
                btn_action.clicked.connect(lambda checked, did=debt['id_dette']: self.show_payment_history(did))
            
            self.table_debtors.setCellWidget(row, 7, btn_action)

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
            self.table_manage_debts.setItem(row, 2, QTableWidgetItem(format_currency(debt['montant_total_dette'])))
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

    def navigate_to_payment(self, debt_id):
        """Navigate vers l'onglet de paiement avec la dette pré-chargée"""
        # Charger la dette dans l'onglet de paiement
        self.payment_debt_id.setText(str(debt_id))
        self.load_debt_for_payment()
        # Changer vers l'onglet de paiement (index 1)
        self.tabs.setCurrentIndex(1)

    def mark_as_paid(self, debt_id):
        """Marque une dette comme payée"""
        if update_debt_status(debt_id, "SOLDE"):
            QMessageBox.information(self, "Succès", "Dette marquée comme payée")
            self.refresh_debtors()
            if hasattr(self, 'table_manage_debts'):
                self.refresh_manage_debts()
        else:
            QMessageBox.critical(self, "Erreur", "Erreur lors de la mise à jour")

    def show_payment_history(self, debt_id):
        """Affiche l'historique des paiements d'une dette"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
        
        debt = get_debt_by_id(debt_id)
        if not debt:
            QMessageBox.warning(self, "Erreur", "Dette non trouvée")
            return
        
        payments = get_payments_for_debt(debt_id)
        
        # Créer une boîte de dialogue
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Historique des Paiements - Dette #{debt_id}")
        dialog.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout()
        
        # Informations de la dette
        info_label = QLabel(f"Client: {debt['client']} | Montant Total: {format_currency(debt['montant_total_dette'])} | Statut: {debt['statut_dette']}")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Tableau des paiements
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Date", "Montant Payé", "Solde Restant Après"])
        table.setColumnWidth(0, 150)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 200)
        
        # Calculer le solde restant progressif
        running_remaining = float(debt['montant_total_dette'])
        table.setRowCount(len(payments))
        
        for row, payment in enumerate(payments):
            date_item = QTableWidgetItem(str(payment['date_pai']))
            amount_item = QTableWidgetItem(format_currency(payment['montant_pai']))
            
            running_remaining -= float(payment['montant_pai'])
            remaining_item = QTableWidgetItem(format_currency(running_remaining))
            
            table.setItem(row, 0, date_item)
            table.setItem(row, 1, amount_item)
            table.setItem(row, 2, remaining_item)
        
        layout.addWidget(table)
        
        # Total payé
        total_paid = float(get_total_paid_for_debt(debt_id))
        remaining = float(get_remaining_amount_for_debt(debt_id))
        
        summary_label = QLabel(f"Total payé: {format_currency(total_paid)} | Restant à payer: {format_currency(remaining)}")
        summary_label.setStyleSheet("margin-top: 10px;")
        layout.addWidget(summary_label)
        
        dialog.setLayout(layout)
        dialog.exec()

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
        
        # Nettoyer le layout précédent
        while self.payment_info_layout.count():
            widget = self.payment_info_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        # Afficher les infos
        remaining = float(get_remaining_amount_for_debt(debt_id))
        total_paid = float(get_total_paid_for_debt(debt_id))
        
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
        total = float(debt['montant_total_dette'])
        self.label_total_debt.setText(f"Montant total : {format_currency(total)}")
        self.label_paid.setText(f"Montant payé : {format_currency(total_paid)}")
        self.label_remaining.setText(f"Montant restant : {format_currency(remaining)}")
        
        # Calculer le pourcentage
        if total > 0:
            percentage = int((float(total_paid) / float(total)) * 100)
            self.payment_progress.setValue(percentage)
        else:
            self.payment_progress.setValue(0)
        
        # Remplir montant avec le montant restant - convertir en float
        self.payment_amount.setValue(float(remaining))
        
        # Charger l'historique des paiements
        self.load_payment_history(debt_id, remaining)
        
        # Afficher un message si dette est complètement payée
        if debt['statut_dette'] == 'SOLDE':
            self.payment_amount.setEnabled(False)
            info_msg = QMessageBox()
            info_msg.setWindowTitle("Paiement Complet")
            info_msg.setText("Cette dette est maintenant complètement payée ✓")
            info_msg.setStandardButtons(QMessageBox.Ok)
            info_msg.exec()
        else:
            self.payment_amount.setEnabled(True)
        
        self.current_debt_id = debt_id
        self.current_vente_id = debt['id_vente']

    def load_payment_history(self, debt_id, current_remaining):
        """Charge l'historique des paiements pour une dette"""
        payments = get_payments_for_debt(debt_id)
        
        debt = get_debt_by_id(debt_id)
        if not debt:
            return
            
        # Pour afficher le solde restant à chaque étape, on commence par le montant total
        # et on soustrait les paiements au fur et à mesure
        # Convertir en float pour éviter problèmes de type Decimal
        running_remaining = float(debt['montant_total_dette'])
        
        self.table_payment_history.setRowCount(len(payments))
        
        for row, payment in enumerate(payments):
            date = QTableWidgetItem(str(payment['date_pai']))
            amount = QTableWidgetItem(format_currency(payment['montant_pai']))
            # Soustraire le paiement du total pour obtenir le solde restant après ce paiement
            # Convertir montant_pai en float
            running_remaining -= float(payment['montant_pai'])
            
            self.table_payment_history.setItem(row, 0, date)
            self.table_payment_history.setItem(row, 1, amount)
            self.table_payment_history.setItem(row, 2, QTableWidgetItem(format_currency(running_remaining)))

    def record_debt_payment(self):
        """Enregistre un paiement pour une dette"""
        try:
            print("\n=== DEBUT ENREGISTREMENT PAIEMENT ===")
            
            if not hasattr(self, 'current_debt_id'):
                QMessageBox.warning(self, "Erreur", "Veuillez d'abord charger une dette")
                return
            
            print(f"Debt ID: {self.current_debt_id}, Vente ID: {self.current_vente_id}")
            
            montant = self.payment_amount.value()
            print(f"Montant à payer: {montant}")
            
            if montant <= 0:
                QMessageBox.warning(self, "Erreur", "Le montant doit être supérieur à 0")
                return
            
            # Vérifier que le montant ne dépasse pas le montant restant
            remaining = float(get_remaining_amount_for_debt(self.current_debt_id))
            print(f"Montant restant avant paiement: {remaining}")
            
            if montant > remaining:
                reply = QMessageBox.question(
                    self,
                    "Montant supérieur",
                    f"Le montant restant à payer est {format_currency(remaining)}.\nVoulez-vous quand même enregistrer {format_currency(montant)} ?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # Enregistrer le paiement
            print(f"Appel record_payment({self.current_vente_id}, {montant}, ...)")
            payment_recorded = record_payment(self.current_vente_id, montant, 
                             self.payment_date.date().toString("yyyy-MM-dd"))
            print(f"Résultat: {payment_recorded}")
            
            if payment_recorded:
                print("Paiement enregistré avec succès en BD")
                
                # Actualiser les listes IMMÉDIATEMENT après l'enregistrement
                print("Rafraîchissement des tableaux...")
                self.refresh_debtors()
                print("✓ refresh_debtors() OK")
                
                if hasattr(self, 'table_manage_debts'):
                    self.refresh_manage_debts()
                    print("✓ refresh_manage_debts() OK")
                
                # Recharger les infos de la dette pour mettre à jour la progression
                print("Rechargement des infos de la dette...")
                self.load_debt_for_payment()
                print("✓ load_debt_for_payment() OK")
                
                self.payment_amount.setValue(0)
                print("✓ Montant remis à 0")
                
                # Générer une facture de paiement (optionnel, ne pas bloquer si erreur)
                print("\nTentative de génération de facture...")
                try:
                    print(f"Récupération données vente: {self.current_vente_id}")
                    sale_data = get_sale_by_id(self.current_vente_id)
                    print(f"Sale data: {sale_data is not None}")
                    
                    if sale_data and 'articles' in sale_data:
                        print(f"Données de vente valides, {len(sale_data.get('articles', []))} articles")
                        
                        # Recuperer les infos de paiement mises à jour
                        total_paid = float(get_total_paid_for_debt(self.current_debt_id))
                        # Convertir remaining en float pour éviter erreur Decimal - float
                        new_remaining = float(remaining) - float(montant)
                        
                        print(f"Total payé: {total_paid}, Nouveau restant: {new_remaining}")
                        
                        sale_data['montant_paye'] = total_paid
                        sale_data['montant_restant'] = new_remaining
                        # montant du paiement courant pour la facture
                        sale_data['paiement_courant'] = float(montant)
                        
                        os.makedirs("factures", exist_ok=True)
                        invoice_filename = f"factures/paiement_dette_{self.current_debt_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        print(f"Génération: {invoice_filename}")
                        if generate_invoice(sale_data, invoice_filename):
                            print(f"✓ Facture générée: {invoice_filename}")
                            reply = QMessageBox.question(
                                self,
                                "Facture générée",
                                "Facture de paiement générée avec succès !\n\nVoulez-vous l'ouvrir ?",
                                QMessageBox.Yes | QMessageBox.No
                            )
                            if reply == QMessageBox.Yes:
                                open_invoice(invoice_filename)
                        else:
                            print("❌ Erreur: Impossible de générer la facture PDF")
                    else:
                        print(f"❌ Erreur: Données de vente incomplètes (sale_data={sale_data}, articles={'articles' in (sale_data or {})})")
                except Exception as e:
                    import traceback
                    print(f"❌ Erreur lors de la génération de facture:")
                    print(traceback.format_exc())
                
                print("\n=== AFFICHAGE MESSAGE DE SUCCES ===")
                QMessageBox.information(self, "Succès", 
                                      f"Paiement de {format_currency(montant)} enregistré avec succès !")
                print("=== FIN ENREGISTREMENT PAIEMENT (SUCCES) ===\n")
            else:
                print("❌ Paiement non enregistré en BD")
                QMessageBox.critical(self, "Erreur", "Erreur lors de l'enregistrement du paiement")
        
        except Exception as e:
            import traceback
            print(f"\n❌ ERREUR PRINCIPALE:")
            print(traceback.format_exc())
            print("=== FIN ENREGISTREMENT PAIEMENT (ERREUR) ===\n")
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {str(e)}")
