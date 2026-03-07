from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QLabel, QPushButton, QLineEdit,
                             QComboBox, QMessageBox, QDialog, QFormLayout,
                             QSpinBox, QDateEdit)
from PySide6.QtCore import Qt, QDate
from database import (get_all_products, get_product_by_id, create_product, 
                      update_product, update_product_stock, is_manager, get_all_product_types)
from utils import format_currency


class StockView(QWidget):
    """Vue pour la gestion du stock"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        
        self.setWindowTitle("Gestion du Stock")
        self.setGeometry(100, 100, 1200, 600)
        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        main_layout = QVBoxLayout()
        
        # Titre
        title = QLabel("État du Stock")
        title.setObjectName("title")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title)
        
        # Filtres
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Filtrer par :"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom du produit...")
        self.search_input.textChanged.connect(self.filter_products)
        filters_layout.addWidget(self.search_input)
        
        filters_layout.addWidget(QLabel("Stock :"))
        self.stock_filter = QComboBox()
        self.stock_filter.addItems(["TOUS", "EN STOCK", "FAIBLE", "EPUISE"])
        self.stock_filter.currentTextChanged.connect(self.filter_products)
        filters_layout.addWidget(self.stock_filter)
        
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.clicked.connect(self.load_products)
        filters_layout.addWidget(btn_refresh)
        
        if is_manager(self.current_user['id_ut']):
            btn_add = QPushButton("➕ Ajouter Produit")
            btn_add.clicked.connect(self.open_add_product_dialog)
            filters_layout.addWidget(btn_add)
        
        filters_layout.addStretch()
        main_layout.addLayout(filters_layout)
        
        # Tableau des produits
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Type", "Prix Carton", "Stock", "Expiration", "Statut", "Actions"
        ])
        self.products_table.setColumnWidth(0, 50)
        self.products_table.setColumnWidth(1, 250)
        self.products_table.setColumnWidth(2, 100)
        self.products_table.setColumnWidth(3, 100)
        self.products_table.setColumnWidth(4, 80)
        self.products_table.setColumnWidth(5, 100)
        self.products_table.setColumnWidth(6, 100)
        self.products_table.setColumnWidth(7, 150)
        
        main_layout.addWidget(self.products_table)
        self.setLayout(main_layout)
        
        # Charger les données
        self.load_products()

    def load_products(self):
        """Charge tous les produits"""
        products = get_all_products()
        self.all_products = products  # Stocker pour le filtrage
        self.display_products(products)

    def display_products(self, products):
        """Affiche une liste de produits"""
        self.products_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            # ID
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product['id_pr'])))
            
            # Nom
            self.products_table.setItem(row, 1, QTableWidgetItem(product['nom_pr']))
            
            # Type
            self.products_table.setItem(row, 2, QTableWidgetItem(product['type'] or "N/A"))
            
            # Prix
            self.products_table.setItem(row, 3, QTableWidgetItem(format_currency(product['prix_carton'])))
            
            # Stock
            stock = product['en_stock']
            item_stock = QTableWidgetItem(str(stock))
            
            # Couleur selon le stock
            if stock == 0:
                item_stock.setForeground(Qt.red)
            elif stock < 10:
                item_stock.setForeground(Qt.darkRed)
            elif stock < 50:
                item_stock.setForeground(Qt.darkYellow)
            else:
                item_stock.setForeground(Qt.darkGreen)
            
            self.products_table.setItem(row, 4, item_stock)
            
            # Expiration
            exp_date = product['date_expiration'] or "N/A"
            self.products_table.setItem(row, 5, QTableWidgetItem(str(exp_date)))
            
            # Statut
            if stock == 0:
                statut = "EPUISE"
            elif stock < 10:
                statut = "FAIBLE"
            else:
                statut = "EN STOCK"
            
            self.products_table.setItem(row, 6, QTableWidgetItem(statut))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            
            btn_edit = QPushButton("✏️")
            btn_edit.setMaximumWidth(40)
            btn_edit.clicked.connect(lambda checked, pid=product['id_pr']: self.open_edit_product_dialog(pid))
            
            if is_manager(self.current_user['id_ut']):
                actions_layout.addWidget(btn_edit)
            
            btn_adjust = QPushButton("📊 Ajuster")
            btn_adjust.setMaximumWidth(80)
            btn_adjust.clicked.connect(lambda checked, pid=product['id_pr']: self.adjust_stock(pid))
            actions_layout.addWidget(btn_adjust)
            
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_widget.setLayout(actions_layout)
            
            self.products_table.setCellWidget(row, 7, actions_widget)

    def filter_products(self):
        """Filtre les produits selon les critères"""
        search_text = self.search_input.text().lower()
        stock_filter = self.stock_filter.currentText()
        
        filtered = []
        
        for product in self.all_products:
            # Filtre par nom
            if search_text and search_text not in product['nom_pr'].lower():
                continue
            
            # Filtre par stock
            stock = product['en_stock']
            if stock_filter == "EN STOCK" and stock == 0:
                continue
            elif stock_filter == "FAIBLE" and stock >= 10:
                continue
            elif stock_filter == "EPUISE" and stock > 0:
                continue
            
            filtered.append(product)
        
        self.display_products(filtered)

    def adjust_stock(self, product_id):
        """Permet d'ajuster le stock d'un produit"""
        product = get_product_by_id(product_id)
        if not product:
            QMessageBox.warning(self, "Erreur", "Produit non trouvé")
            return
        
        dialog = StockAdjustmentDialog(self, product)
        if dialog.exec() == QDialog.Accepted:
            self.load_products()

    def open_add_product_dialog(self):
        """Ouvre le dialogue pour ajouter un produit"""
        if not is_manager(self.current_user['id_ut']):
            QMessageBox.warning(self, "Accès refusé", 
                              "Seuls les managers peuvent ajouter des produits")
            return
        
        dialog = ProductDialog(self, mode="add")
        if dialog.exec() == QDialog.Accepted:
            self.load_products()

    def open_edit_product_dialog(self, product_id):
        """Ouvre le dialogue pour modifier un produit"""
        if not is_manager(self.current_user['id_ut']):
            QMessageBox.warning(self, "Accès refusé", 
                              "Seuls les managers peuvent modifier les produits")
            return
        
        product = get_product_by_id(product_id)
        if not product:
            QMessageBox.warning(self, "Erreur", "Produit non trouvé")
            return
        
        dialog = ProductDialog(self, mode="edit", product=product)
        if dialog.exec() == QDialog.Accepted:
            self.load_products()


class ProductDialog(QDialog):
    """Dialogue pour ajouter ou modifier un produit"""
    
    def __init__(self, parent=None, mode="add", product=None):
        super().__init__(parent)
        self.mode = mode
        self.product = product
        self.setWindowTitle("Ajouter un produit" if mode == "add" else "Modifier le produit")
        self.setGeometry(200, 200, 400, 300)
        self.setup_ui()
        
        if mode == "edit" and product:
            self.populate_fields(product)

    def setup_ui(self):
        """Configure le formulaire"""
        layout = QFormLayout()
        
        self.nom_input = QLineEdit()
        layout.addRow("Nom du produit :", self.nom_input)
        
        self.prix_input = QLineEdit()
        self.prix_input.setPlaceholderText("0.00")
        layout.addRow("Prix par carton :", self.prix_input)
        
        self.type_combo = QComboBox()
        # charger types depuis la base de données
        types = get_all_product_types()
        for t in types:
            # chaque élément est dict avec id_type et libelle_type
            self.type_combo.addItem(t['libelle_type'], t['id_type'])
        layout.addRow("Type :", self.type_combo)
        
        self.stock_input = QSpinBox()
        self.stock_input.setMinimum(0)
        self.stock_input.setMaximum(10000)
        layout.addRow("Quantité en stock :", self.stock_input)
        
        self.date_exp = QDateEdit()
        self.date_exp.setDate(QDate.currentDate().addMonths(6))
        layout.addRow("Date d'expiration :", self.date_exp)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        btn_save = QPushButton("Enregistrer")
        btn_save.clicked.connect(self.save_product)
        button_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)
        
        layout.addRow(button_layout)
        self.setLayout(layout)

    def populate_fields(self, product):
        """Remplir les champs avec les données du produit"""
        self.nom_input.setText(product['nom_pr'])
        self.prix_input.setText(str(product['prix_carton']))
        # sélectionner le type correspondant
        for i in range(self.type_combo.count()):
            if self.type_combo.itemText(i) == (product['type'] or ""):
                self.type_combo.setCurrentIndex(i)
                break
        self.stock_input.setValue(product['en_stock'])
        
        if product['date_expiration']:
            self.date_exp.setDate(QDate.fromString(str(product['date_expiration']), "yyyy-MM-dd"))

    def save_product(self):
        """Enregistre le produit"""
        nom = self.nom_input.text().strip()
        prix_text = self.prix_input.text().strip()
        
        if not nom or not prix_text:
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs")
            return
        type_id = self.type_combo.currentData()
        if type_id is None:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un type valide")
            return
        
        try:
            prix = float(prix_text)
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Le prix doit être un nombre")
            return
        
        if self.mode == "add":
            product_id = create_product(nom, prix, type_id, 
                                       self.stock_input.value(), 
                                       self.date_exp.date().toString("yyyy-MM-dd"))
            if product_id:
                QMessageBox.information(self, "Succès", "Produit créé avec succès")
                self.accept()
            else:
                QMessageBox.critical(self, "Erreur", "Erreur lors de la création")
        
        else:  # Edit
            type_id = self.type_combo.currentData()
            if update_product(self.product['id_pr'], nom=nom, prix=prix, id_type=type_id, en_stock=self.stock_input.value()):
                QMessageBox.information(self, "Succès", "Produit modifié avec succès")
                self.accept()
            else:
                QMessageBox.critical(self, "Erreur", "Erreur lors de la modification")


class StockAdjustmentDialog(QDialog):
    """Dialogue pour ajuster le stock"""
    
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Ajuster le stock")
        self.setGeometry(200, 200, 350, 150)
        self.setup_ui()

    def setup_ui(self):
        """Configure le formulaire"""
        layout = QFormLayout()
        
        layout.addRow(QLabel(f"Produit : {self.product['nom_pr']}"))
        layout.addRow(QLabel(f"Stock actuel : {self.product['en_stock']}"))
        
        self.adjustment_spinbox = QSpinBox()
        self.adjustment_spinbox.setMinimum(-10000)
        self.adjustment_spinbox.setMaximum(10000)
        self.adjustment_spinbox.setValue(0)
        layout.addRow("Ajustement :", self.adjustment_spinbox)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        btn_save = QPushButton("Appliquer")
        btn_save.clicked.connect(self.apply_adjustment)
        button_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)
        
        layout.addRow(button_layout)
        self.setLayout(layout)

    def apply_adjustment(self):
        """Applique l'ajustement au stock"""
        adjustment = self.adjustment_spinbox.value()
        
        if adjustment == 0:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer une valeur")
            return
        
        if update_product_stock(self.product['id_pr'], adjustment):
            QMessageBox.information(self, "Succès", "Stock ajusté avec succès")
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", "Erreur lors de l'ajustement")
