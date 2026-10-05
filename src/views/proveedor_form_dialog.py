from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt

class ProveedorFormDialog(QDialog):
    def __init__(self, ejecutivos, proveedor=None, id_ejecutivo_actual=None, parent=None):
        """
        Diálogo para crear o editar un proveedor.
        - ejecutivos: lista de dicts [{'id': 2, 'nombre': 'Luciano...', ...}]
        - proveedor: dict con datos del proveedor si se está editando, o None si es nuevo.
        """
        super().__init__(parent)
        self.proveedor = proveedor
        self.ejecutivos = ejecutivos
        self.id_ejecutivo_actual = id_ejecutivo_actual
        
        modo = "Editar Proveedor" if self.proveedor else "Nuevo Proveedor"
        self.setWindowTitle(modo)
        self.resize(460, 360)
        
        self.setup_ui()
        if self.proveedor:
            self.cargar_datos()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(12)
        
        # Título
        titulo_texto = "✏️ Modificar Proveedor" if self.proveedor else "➕ Registrar Nuevo Proveedor"
        lbl_titulo = QLabel(titulo_texto)
        lbl_titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b;")
        layout.addWidget(lbl_titulo)
        
        # Campo: Nombre
        layout.addWidget(QLabel("Nombre de la Empresa / Razón Social: *"))
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Distribuidora Central S.R.L.")
        layout.addWidget(self.txt_nombre)
        
        # Campo: Email
        layout.addWidget(QLabel("Correo Electrónico (para solicitudes y órdenes):"))
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("ventas@proveedor.com")
        layout.addWidget(self.txt_email)
        
        # Campo: Teléfono
        layout.addWidget(QLabel("Teléfono de Contacto:"))
        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("(0341) 482-9000")
        layout.addWidget(self.txt_telefono)
        
        # Campo: Dirección
        layout.addWidget(QLabel("Dirección / Localidad:"))
        self.txt_direccion = QLineEdit()
        self.txt_direccion.setPlaceholderText("Av. Pellegrini 1500, Rosario")
        layout.addWidget(self.txt_direccion)
        
        # Campo: Ejecutivo Responsable
        layout.addWidget(QLabel("Ejecutivo de Cuentas Responsable:"))
        self.cmb_ejecutivo = QComboBox()
        for ejec in self.ejecutivos:
            self.cmb_ejecutivo.addItem(f"{ejec['nombre']} ({ejec['role']})", ejec['id'])
            
        # Si es nuevo y hay un ejecutivo logueado, preseleccionarlo
        if not self.proveedor and self.id_ejecutivo_actual:
            for idx in range(self.cmb_ejecutivo.count()):
                if self.cmb_ejecutivo.itemData(idx) == self.id_ejecutivo_actual:
                    self.cmb_ejecutivo.setCurrentIndex(idx)
                    break
        layout.addWidget(self.cmb_ejecutivo)
        
        # Botones
        layout_btn = QHBoxLayout()
        layout_btn.setSpacing(10)
        layout_btn.addStretch()
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("padding: 6px 14px; border-radius: 4px;")
        self.btn_cancelar.clicked.connect(self.reject)
        layout_btn.addWidget(self.btn_cancelar)
        
        self.btn_guardar = QPushButton("Guardar Proveedor")
        self.btn_guardar.setStyleSheet("background-color: #2563eb; color: white; padding: 6px 18px; font-weight: bold; border-radius: 4px;")
        self.btn_guardar.clicked.connect(self.validar_y_guardar)
        layout_btn.addWidget(self.btn_guardar)
        
        layout.addLayout(layout_btn)

    def cargar_datos(self):
        self.txt_nombre.setText(self.proveedor.get("nombre", ""))
        self.txt_email.setText(self.proveedor.get("email", "") or "")
        self.txt_telefono.setText(self.proveedor.get("telefono", "") or "")
        self.txt_direccion.setText(self.proveedor.get("direccion", "") or "")
        
        id_user = self.proveedor.get("id_user")
        for idx in range(self.cmb_ejecutivo.count()):
            if self.cmb_ejecutivo.itemData(idx) == id_user:
                self.cmb_ejecutivo.setCurrentIndex(idx)
                break

    def validar_y_guardar(self):
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Campo Obligatorio", "Debes ingresar el nombre del proveedor.")
            self.txt_nombre.setFocus()
            return
            
        email = self.txt_email.text().strip()
        if email and ("@" not in email or "." not in email):
            QMessageBox.warning(self, "Email Inválido", "Por favor ingresa una dirección de correo válida.")
            self.txt_email.setFocus()
            return
            
        self.accept()

    def obtener_datos(self):
        return {
            "nombre": self.txt_nombre.text().strip(),
            "email": self.txt_email.text().strip(),
            "telefono": self.txt_telefono.text().strip(),
            "direccion": self.txt_direccion.text().strip(),
            "id_user": self.cmb_ejecutivo.currentData()
        }
