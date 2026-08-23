import os
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic

class LoginView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login.ui")
        uic.loadUi(ui_path, self)

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
