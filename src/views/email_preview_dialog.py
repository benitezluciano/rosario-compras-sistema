import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextBrowser, QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.services.email_service import EmailService

class EmailWorkerThread(QThread):
    """
    Hilo de trabajo seguro basado en QThread para procesar el envío de correos
    sin congelar la interfaz gráfica ni provocar violaciones entre hilos en Windows/PyQt6.
    """
    envio_terminado = pyqtSignal(bool, str)

    def __init__(self, email_service, destinatario, asunto, cuerpo_html, cuerpo_texto="", adjuntos=None, parent=None):
        super().__init__(parent)
        self.email_service = email_service
        self.destinatario = destinatario
        self.asunto = asunto
        self.cuerpo_html = cuerpo_html
        self.cuerpo_texto = cuerpo_texto
        self.adjuntos = adjuntos or []

    def run(self):
        exito, mensaje = self.email_service.enviar_correo_sync(
            destinatario=self.destinatario,
            asunto=self.asunto,
            cuerpo_html=self.cuerpo_html,
            cuerpo_texto=self.cuerpo_texto,
            adjuntos=self.adjuntos
        )
        self.envio_terminado.emit(exito, mensaje)

class EmailPreviewDialog(QDialog):
    def __init__(self, destinatario, asunto, cuerpo_html, adjuntos=None, parent=None):
        super().__init__(parent)
        self.destinatario = destinatario
        self.asunto = asunto
        self.cuerpo_html = cuerpo_html
        self.adjuntos = adjuntos or []
        self.email_service = EmailService.get_instance()
        self.resultado_exito = False
        self.resultado_mensaje = ""
        self.worker = None
        
        self.setWindowTitle("Emisión de Correo Electrónico - Rosario Compras")
        self.resize(650, 560)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # --- Cabecera con Estado SMTP ---
        header_layout = QHBoxLayout()
        lbl_titulo = QLabel("📧 Envío de Comunicación Formal")
        lbl_titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b;")
        header_layout.addWidget(lbl_titulo)
        
        header_layout.addStretch()
        
        # Badge de estado
        lbl_estado = QLabel()
        if self.email_service.esta_configurado():
            lbl_estado.setText("🟢 SMTP Conectado")
            lbl_estado.setStyleSheet("background-color: #dcfce7; color: #15803d; font-weight: bold; font-size: 11px; padding: 4px 8px; border-radius: 12px;")
        else:
            lbl_estado.setText("🟡 Modo Simulación (Log)")
            lbl_estado.setStyleSheet("background-color: #fef9c3; color: #a16207; font-weight: bold; font-size: 11px; padding: 4px 8px; border-radius: 12px;")
        header_layout.addWidget(lbl_estado)
        
        layout.addLayout(header_layout)
        
        # --- Formulario de Destinatario y Asunto ---
        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px;")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(8)
        
        # Destinatario
        row_dest = QHBoxLayout()
        row_dest.addWidget(QLabel("Para (Email):"))
        self.txt_destinatario = QLineEdit(self.destinatario)
        self.txt_destinatario.setPlaceholderText("correo@destinatario.com")
        row_dest.addWidget(self.txt_destinatario)
        form_layout.addLayout(row_dest)
        
        # Asunto
        row_asunto = QHBoxLayout()
        row_asunto.addWidget(QLabel("Asunto:"))
        self.txt_asunto = QLineEdit(self.asunto)
        row_asunto.addWidget(self.txt_asunto)
        form_layout.addLayout(row_asunto)
        
        if self.adjuntos:
            row_adj = QHBoxLayout()
            row_adj.addWidget(QLabel("Adjuntos:"))
            lbl_adj = QLabel(", ".join([os.path.basename(a) for a in self.adjuntos]))
            lbl_adj.setStyleSheet("color: #2563eb; font-weight: bold;")
            row_adj.addWidget(lbl_adj)
            row_adj.addStretch()
            form_layout.addLayout(row_adj)
            
        layout.addWidget(form_frame)
        
        # --- Vista Previa del Cuerpo HTML ---
        layout.addWidget(QLabel("Vista Previa del Contenido:"))
        self.preview_browser = QTextBrowser()
        self.preview_browser.setHtml(self.cuerpo_html)
        self.preview_browser.setStyleSheet("background-color: white; border: 1px solid #cbd5e1; border-radius: 6px;")
        layout.addWidget(self.preview_browser)
        
        # --- Botones ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("padding: 7px 14px; border-radius: 4px;")
        self.btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancelar)
        
        self.btn_enviar = QPushButton("🚀 Enviar Correo")
        self.btn_enviar.setStyleSheet("background-color: #2563eb; color: white; padding: 7px 20px; font-weight: bold; border-radius: 4px;")
        self.btn_enviar.clicked.connect(self.ejecutar_envio)
        btn_layout.addWidget(self.btn_enviar)
        
        layout.addLayout(btn_layout)

    def ejecutar_envio(self):
        destinatario = self.txt_destinatario.text().strip()
        asunto = self.txt_asunto.text().strip()
        
        if not destinatario:
            QMessageBox.warning(self, "Campo Vacío", "Debes ingresar una dirección de correo destinataria.")
            return
            
        if "@" not in destinatario or "." not in destinatario:
            QMessageBox.warning(self, "Email Inválido", "Ingresa una dirección de correo válida.")
            return
            
        self.btn_enviar.setEnabled(False)
        self.btn_enviar.setText("⏳ Enviando...")
        self.btn_cancelar.setEnabled(False)
        
        # Iniciar worker thread de Qt
        self.worker = EmailWorkerThread(
            email_service=self.email_service,
            destinatario=destinatario,
            asunto=asunto,
            cuerpo_html=self.cuerpo_html,
            adjuntos=self.adjuntos,
            parent=self
        )
        self.worker.envio_terminado.connect(self._al_finalizar_envio)
        self.worker.start()

    def _al_finalizar_envio(self, exito, mensaje):
        """
        Slot ejecutado de forma 100% segura en el Main GUI Thread
        gracias al mecanismo QueuedConnection de pyqtSignal.
        """
        self.resultado_exito = exito
        self.resultado_mensaje = mensaje
        
        if exito:
            self.accept()
        else:
            self.btn_enviar.setEnabled(True)
            self.btn_enviar.setText("🚀 Reintentar Enviar")
            self.btn_cancelar.setEnabled(True)
            QMessageBox.critical(self, "Error al Enviar", mensaje)
