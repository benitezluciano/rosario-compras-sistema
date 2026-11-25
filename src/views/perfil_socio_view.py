from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from src.models.perfil_model import CONDICIONES_IVA


class PerfilSocioView(QWidget):
    """Pantalla para que el socio cargue o actualice sus datos fiscales y domicilio."""

    def __init__(self, parent=None):
        super().__init__(parent)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(20, 15, 20, 20)
        raiz.setSpacing(14)

        titulo = QLabel("🏢 Mis Datos Fiscales y Domicilio")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold;")
        raiz.addWidget(titulo)

        subtitulo = QLabel(
            "Estos datos se utilizan como destinatario en tus Notas de Pedido y Remitos de entrega."
        )
        subtitulo.setStyleSheet("color: #64748b;")
        subtitulo.setWordWrap(True)
        raiz.addWidget(subtitulo)

        tarjeta = QFrame()
        tarjeta.setFrameShape(QFrame.Shape.StyledPanel)
        tarjeta.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; }"
        )
        tarjeta_layout = QVBoxLayout(tarjeta)
        tarjeta_layout.setContentsMargins(22, 20, 22, 20)
        tarjeta_layout.setSpacing(14)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setSpacing(12)

        self.lbl_email = QLabel("-")
        self.lbl_email.setStyleSheet("color: #475569; font-weight: bold; border: none;")
        form.addRow("Correo electrónico:", self.lbl_email)

        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre o Razón Social del socio")
        form.addRow("Nombre / Razón Social *:", self.txt_nombre)

        self.txt_cuit_dni = QLineEdit()
        self.txt_cuit_dni.setPlaceholderText("Ej: 20-12345678-9 o 35123456")
        form.addRow("C.U.I.T. / D.N.I. *:", self.txt_cuit_dni)

        self.cmb_condicion_iva = QComboBox()
        self.cmb_condicion_iva.addItems(CONDICIONES_IVA)
        form.addRow("Condición frente al IVA *:", self.cmb_condicion_iva)

        self.txt_domicilio = QLineEdit()
        self.txt_domicilio.setPlaceholderText("Calle, número, localidad y provincia")
        form.addRow("Domicilio de entrega *:", self.txt_domicilio)

        tarjeta_layout.addLayout(form)

        ayuda = QLabel("Formato aceptado: CUIT (XX-XXXXXXXX-X u 11 dígitos) o DNI (7 u 8 dígitos).")
        ayuda.setStyleSheet("color: #64748b; font-size: 12px; border: none;")
        tarjeta_layout.addWidget(ayuda)

        fila_btn = QHBoxLayout()
        fila_btn.addStretch()
        self.btn_guardar = QPushButton("💾 Guardar Datos Fiscales")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setStyleSheet(
            "QPushButton { background-color: #0f766e; color: #ffffff; font-weight: bold; "
            "padding: 8px 18px; border-radius: 6px; }"
            "QPushButton:hover { background-color: #115e59; }"
        )
        fila_btn.addWidget(self.btn_guardar)
        tarjeta_layout.addLayout(fila_btn)

        raiz.addWidget(tarjeta)
        raiz.addStretch()

    def cargar_datos(self, perfil):
        if not perfil:
            return
        self.lbl_email.setText(perfil.get("email") or "-")
        self.txt_nombre.setText(perfil.get("nombre") or "")
        self.txt_cuit_dni.setText(perfil.get("cuit_dni") or "")
        self.txt_domicilio.setText(perfil.get("domicilio") or "")
        cond = perfil.get("condicion_iva") or ""
        idx = self.cmb_condicion_iva.findText(cond)
        self.cmb_condicion_iva.setCurrentIndex(idx if idx >= 0 else 0)

    def obtener_datos_formulario(self):
        return {
            "nombre": self.txt_nombre.text(),
            "cuit_dni": self.txt_cuit_dni.text(),
            "condicion_iva": self.cmb_condicion_iva.currentText(),
            "domicilio": self.txt_domicilio.text(),
        }

    def mostrar_exito(self, mensaje):
        QMessageBox.information(self, "Datos actualizados", mensaje)

    def mostrar_error(self, mensaje):
        QMessageBox.warning(self, "Validación de datos", mensaje)
