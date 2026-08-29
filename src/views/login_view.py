import os
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QFrame
from PyQt6.QtCore import Qt
from PyQt6 import uic

class LoginView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login.ui")
        uic.loadUi(ui_path, self)
        
        self._setup_quick_fill()

    def _setup_quick_fill(self):
        """Agrega botones de acceso rápido para facilitar el inicio de sesión durante pruebas."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 6px;
                margin-top: 8px;
            }
            QLabel {
                font-size: 11px;
                color: #475569;
                font-weight: bold;
                border: none;
            }
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #94a3b8;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 11px;
                font-weight: 500;
                color: #1e293b;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
                border-color: #64748b;
            }
            QPushButton:pressed {
                background-color: #cbd5e1;
            }
        """)
        
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(8, 6, 8, 6)
        frame_layout.setSpacing(6)
        
        lbl = QLabel("⚡ Autocompletar usuario de prueba:")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(lbl)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)
        
        credenciales = [
            ("👔 Ejecutivo", "ejecutivo@rosariocompras.com", "account123"),
            ("👑 Admin", "admin@rosariocompras.com", "admin123"),
            ("☕ Socio 1", "socio1@rosariocompras.com", "socio123"),
            ("🥖 Socio 2", "socio2@rosariocompras.com", "socio123"),
        ]
        
        for label, email, pwd in credenciales:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, e=email, p=pwd: self._cargar_credenciales(e, p))
            btn_layout.addWidget(btn)
            
        frame_layout.addLayout(btn_layout)
        self.mainLayout.addWidget(frame)

    def _cargar_credenciales(self, email, password):
        self.txt_email.setText(email)
        self.txt_password.setText(password)
        self.lbl_error.clear()

    def obtener_credenciales(self):
        """Retorna una tupla (email, password) limpiando espacios del email."""
        email = self.txt_email.text().strip()
        password = self.txt_password.text()
        return email, password

    def mostrar_error(self, mensaje):
        """Muestra un mensaje de error en la etiqueta correspondiente."""
        self.lbl_error.setText(mensaje)

    def limpiar_campos(self):
        """Limpia los campos del formulario y el mensaje de error."""
        self.txt_email.clear()
        self.txt_password.clear()
        self.lbl_error.clear()
