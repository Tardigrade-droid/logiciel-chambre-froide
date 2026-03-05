from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QDialog, QLabel, 
                             QLineEdit, QComboBox, QMessageBox, QFormLayout)
from PySide6.QtCore import Qt, Signal
from database import (get_all_users, get_all_roles, create_user, update_user, 
                      delete_user, get_user_by_id, is_manager, update_user_password)


class UsersView(QWidget):
    """Vue pour la gestion des utilisateurs (Manager uniquement)"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        
        # Vérifier si l'utilisateur est manager
        if not is_manager(current_user['id_ut']):
            QMessageBox.warning(self, "Accès refusé", 
                              "Seuls les managers peuvent gérer les utilisateurs")
            self.parent().close()
            return
        
        self.setWindowTitle("Gestion des Utilisateurs")
        self.setGeometry(100, 100, 900, 600)
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        main_layout = QVBoxLayout()
        
        # Titre
        title = QLabel("Gestion des Utilisateurs")
        title.setObjectName("title")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title)
        
        # Tableau des utilisateurs
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels([
            "Prénom", "Nom", "Téléphone", "Rôle", "Statut", "Actions"
        ])
        self.users_table.setColumnWidth(0, 120)
        self.users_table.setColumnWidth(1, 120)
        self.users_table.setColumnWidth(2, 120)
        self.users_table.setColumnWidth(3, 100)
        self.users_table.setColumnWidth(4, 100)
        self.users_table.setColumnWidth(5, 150)
        main_layout.addWidget(self.users_table)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        btn_add = QPushButton("Ajouter un utilisateur")
        btn_add.clicked.connect(self.open_add_user_dialog)
        buttons_layout.addWidget(btn_add)
        
        btn_edit = QPushButton("Modifier")
        btn_edit.clicked.connect(self.edit_selected_user)
        buttons_layout.addWidget(btn_edit)
        
        btn_delete = QPushButton("Supprimer")
        btn_delete.clicked.connect(self.delete_selected_user)
        buttons_layout.addWidget(btn_delete)
        
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.clicked.connect(self.load_users)
        buttons_layout.addWidget(btn_refresh)
        
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def load_users(self):
        """Charge et affiche la liste des utilisateurs"""
        users = get_all_users()
        self.users_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            # Prénom
            self.users_table.setItem(row, 0, QTableWidgetItem(user['prenom_ut']))
            # Nom
            self.users_table.setItem(row, 1, QTableWidgetItem(user['nom_ut']))
            # Téléphone
            self.users_table.setItem(row, 2, QTableWidgetItem(user['tel_ut']))
            # Rôle
            self.users_table.setItem(row, 3, QTableWidgetItem(user['role']))
            # Statut
            self.users_table.setItem(row, 4, QTableWidgetItem(user['statut']))
            
            # Boutons d'action (Edit & Delete)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            
            btn_edit = QPushButton("✏️")
            btn_edit.setMaximumWidth(40)
            btn_edit.clicked.connect(lambda checked, u_id=user['id_ut']: self.open_edit_dialog(u_id))
            
            btn_del = QPushButton("🗑️")
            btn_del.setMaximumWidth(40)
            btn_del.clicked.connect(lambda checked, u_id=user['id_ut']: self.confirm_delete(u_id))
            
            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_del)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_widget.setLayout(actions_layout)
            
            self.users_table.setCellWidget(row, 5, actions_widget)

    def open_add_user_dialog(self):
        """Ouvre le dialogue pour ajouter un nouvel utilisateur"""
        dialog = UserDialog(self, mode="add")
        if dialog.exec() == QDialog.Accepted:
            self.load_users()

    def open_edit_dialog(self, user_id):
        """Ouvre le dialogue pour modifier un utilisateur"""
        user = get_user_by_id(user_id)
        if user:
            dialog = UserDialog(self, mode="edit", user=user)
            if dialog.exec() == QDialog.Accepted:
                self.load_users()

    def edit_selected_user(self):
        """Modifie l'utilisateur sélectionné"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un utilisateur")
            return
        
        # Récupérer l'ID de l'utilisateur (nous devons le stocker)
        # Pour maintenant, on va récupérer tous les users et matcher par indice
        users = get_all_users()
        if current_row < len(users):
            self.open_edit_dialog(users[current_row]['id_ut'])

    def delete_selected_user(self):
        """Supprime l'utilisateur sélectionné"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un utilisateur")
            return
        
        users = get_all_users()
        if current_row < len(users):
            self.confirm_delete(users[current_row]['id_ut'])

    def confirm_delete(self, user_id):
        """Demande confirmation avant suppression"""
        user = get_user_by_id(user_id)
        if not user:
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer {user['prenom_ut']} {user['nom_ut']} ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = delete_user(user_id)
            if success:
                QMessageBox.information(self, "Succès", message)
                self.load_users()
            else:
                QMessageBox.critical(self, "Erreur", message)


class UserDialog(QDialog):
    """Dialogue pour ajouter ou modifier un utilisateur"""
    
    def __init__(self, parent=None, mode="add", user=None):
        super().__init__(parent)
        self.mode = mode
        self.user = user
        self.setWindowTitle("Ajouter un utilisateur" if mode == "add" else "Modifier l'utilisateur")
        self.setGeometry(150, 150, 400, 500)
        self.setup_ui()
        
        if mode == "edit" and user:
            self.populate_fields(user)

    def setup_ui(self):
        """Configure le formulaire"""
        layout = QFormLayout()
        
        # Prénom
        self.prenom_input = QLineEdit()
        layout.addRow("Prénom :", self.prenom_input)
        
        # Nom
        self.nom_input = QLineEdit()
        layout.addRow("Nom :", self.nom_input)
        
        # Téléphone
        self.phone_input = QLineEdit()
        layout.addRow("Téléphone :", self.phone_input)
        
        # Rôle
        self.role_combo = QComboBox()
        roles = get_all_roles()
        for role in roles:
            self.role_combo.addItem(role['libelle'], role['id_role'])
        layout.addRow("Rôle :", self.role_combo)
        
        # Statut
        self.statut_combo = QComboBox()
        self.statut_combo.addItems(["ACTIF", "INACTIF"])
        layout.addRow("Statut :", self.statut_combo)
        
        # Mot de passe (seulement en création)
        if self.mode == "add":
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            layout.addRow("Mot de passe :", self.password_input)
            
            self.confirm_password_input = QLineEdit()
            self.confirm_password_input.setEchoMode(QLineEdit.Password)
            layout.addRow("Confirmer :", self.confirm_password_input)
        else:
            self.password_input = None
            label = QLabel("Pour changer le mot de passe, utilisez l'option dédiée")
            layout.addRow(label)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        btn_save = QPushButton("Enregistrer")
        btn_save.clicked.connect(self.save_user)
        buttons_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)
        
        layout.addRow(buttons_layout)
        self.setLayout(layout)

    def populate_fields(self, user):
        """Remplit les champs avec les données de l'utilisateur"""
        self.prenom_input.setText(user['prenom_ut'])
        self.nom_input.setText(user['nom_ut'])
        self.phone_input.setText(user['tel_ut'])
        
        # Sélectionner le rôle
        for i in range(self.role_combo.count()):
            if self.role_combo.itemData(i) == user['id_role']:
                self.role_combo.setCurrentIndex(i)
                break
        
        # Sélectionner le statut
        self.statut_combo.setCurrentText(user['statut'])

    def save_user(self):
        """Enregistre les données du formulaire"""
        prenom = self.prenom_input.text().strip()
        nom = self.nom_input.text().strip()
        phone = self.phone_input.text().strip()
        role_id = self.role_combo.currentData()
        statut = self.statut_combo.currentText()
        
        # Validation
        if not all([prenom, nom, phone, role_id]):
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs obligatoires")
            return
        
        if self.mode == "add":
            password = self.password_input.text()
            confirm_password = self.confirm_password_input.text()
            
            if not password:
                QMessageBox.warning(self, "Erreur", "Le mot de passe est obligatoire")
                return
            
            if password != confirm_password:
                QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas")
                return
            
            if create_user(prenom, nom, phone, password, role_id, statut):
                QMessageBox.information(self, "Succès", "Utilisateur créé avec succès")
                self.accept()
            else:
                QMessageBox.critical(self, "Erreur", "Erreur lors de la création (téléphone déjà utilisé ?)")
        
        else:  # Edit mode
            if update_user(self.user['id_ut'], prenom=prenom, nom=nom, 
                          telephone=phone, id_role=role_id, statut=statut):
                QMessageBox.information(self, "Succès", "Utilisateur modifié avec succès")
                self.accept()
            else:
                QMessageBox.critical(self, "Erreur", "Erreur lors de la modification")
