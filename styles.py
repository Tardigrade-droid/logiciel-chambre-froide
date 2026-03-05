STYLE_SHEET = """
QMainWindow, QWidget {
    background-color: #f5f6fa;
    font-family: 'Segoe UI', Arial;
}
QPushButton {
    background-color: #2f3640;
    color: white;
    border-radius: 5px;
    padding: 10px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #718093;
}
QLineEdit {
    padding: 8px;
    border: 1px solid #dcdde1;
    border-radius: 4px;
    background: white;
}
QLabel#title {
    font-size: 20px;
    font-weight: bold;
    color: #2f3640;
}

/* specific styling for login page button */
QPushButton#loginButton {
    font-size: 16px;
    padding: 12px 20px;
    background-color: #027df8;
}

QCheckBox {
    font-size: 12px;
    color: #2f3640;
}

/* top menu buttons */
QPushButton[class="topMenu"] {
    background-color: transparent;
    border: none;
    padding: 8px 16px;
    font-size: 14px;
}
QPushButton[class="topMenu"] {
    background-color: transparent;
    border: none;
    padding: 8px 16px;
    font-size: 14px;
}
QPushButton[class="topMenu"][active="true"] {
    background-color: #3498db;
    color: white;
    border-radius: 4px;
}

/* side menu buttons */
QPushButton[class="sideMenu"] {
    background-color: transparent;
    border: none;
    text-align: left;
    padding: 6px 12px;
    font-size: 14px;
}
QPushButton[class="sideMenu"][active="true"] {
    background-color: #3498db;
    color: white;
    border-radius: 4px;
}
"""