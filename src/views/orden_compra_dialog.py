import os
import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QUrl, QProcess
from PyQt6.QtGui import QDesktopServices


def fecha_legible(fecha):
    """'AAAA-MM-DD HH:MM:SS' → 'DD/MM/AAAA HH:MM'."""
    if not fecha or len(fecha) < 10:
        return fecha or ""
    hora = f" {fecha[11:16]}" if len(fecha) >= 16 else ""
    return f"{fecha[8:10]}/{fecha[5:7]}/{fecha[0:4]}{hora}"


class OrdenCompraDialog(QDialog):
    """
    Muestra una orden de compra emitida y permite abrir su archivo Excel, abrir la carpeta
    o enviarla por correo al proveedor.

    obtener_ruta(): callback que devuelve la ruta del archivo (regenerándolo si hace falta).
    enviar(orden, parent): callback que abre el envío por correo; devuelve la orden actualizada
                           si se envió, o None si se canceló o falló.
    """

    def __init__(self, orden, obtener_ruta, enviar, titulo="✅ Orden de Compra generada", parent=None):
        super().__init__(parent)
        self.orden = orden
        self.obtener_ruta = obtener_ruta
        self.enviar = enviar

        self.setWindowTitle(f"Orden de Compra {orden.get('codigo', '')} - Rosario Compras")
        self.setMinimumWidth(560)
        self._construir(titulo)
        self._actualizar_estado_envio()

    def _construir(self, titulo):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("font-size: 17px; font-weight: bold; color: #1e3a8a;")
        lbl_titulo.setWordWrap(True)
        layout.addWidget(lbl_titulo)

        marco = QFrame()
        marco.setStyleSheet("QFrame { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; }"
                            "QLabel { border: none; }")
        grilla = QGridLayout(marco)
        grilla.setContentsMargins(14, 12, 14, 12)
        grilla.setHorizontalSpacing(18)
        grilla.setVerticalSpacing(6)

        o = self.orden
        filas = [
            ("N° de Orden:", o.get('codigo', '')),
            ("Proveedor:", o.get('proveedor', {}).get('nombre', '')),
            ("Fecha de emisión:", fecha_legible(o.get('fecha', ''))),
            ("Pedidos consolidados:", str(o.get('cantidad_pedidos', 0))),
            ("Artículos:", str(len(o.get('items', [])))),
            ("Total:", f"${o.get('total', 0.0):,.2f}"),
            ("Archivo:", o.get('archivo') or "(se generará al abrirlo)"),
        ]
        for i, (etiqueta, valor) in enumerate(filas):
            lbl_e = QLabel(etiqueta)
            lbl_e.setStyleSheet("color: #475569; font-weight: bold;")
            lbl_v = QLabel(valor)
            lbl_v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl_v.setWordWrap(True)
            if etiqueta in ("N° de Orden:", "Total:"):
                lbl_v.setStyleSheet("color: #1e3a8a; font-weight: bold;")
            grilla.addWidget(lbl_e, i, 0, Qt.AlignmentFlag.AlignTop)
            grilla.addWidget(lbl_v, i, 1)
        grilla.setColumnStretch(1, 1)
        layout.addWidget(marco)

        self.lbl_envio = QLabel()
        self.lbl_envio.setWordWrap(True)
        layout.addWidget(self.lbl_envio)

        botones = QHBoxLayout()
        botones.setSpacing(8)
        self.btn_abrir = QPushButton("📂 Abrir archivo")
        self.btn_abrir.clicked.connect(self.abrir_archivo)
        self.btn_carpeta = QPushButton("📁 Abrir carpeta")
        self.btn_carpeta.clicked.connect(self.abrir_carpeta)
        self.btn_enviar = QPushButton("✉️ Enviar al proveedor")
        self.btn_enviar.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 14px;")
        self.btn_enviar.clicked.connect(self.enviar_orden)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)

        botones.addWidget(self.btn_abrir)
        botones.addWidget(self.btn_carpeta)
        botones.addStretch()
        botones.addWidget(self.btn_enviar)
        botones.addWidget(btn_cerrar)
        layout.addLayout(botones)

    def _actualizar_estado_envio(self):
        if self.orden.get('fecha_envio_email'):
            self.lbl_envio.setText(
                f"✉️ Enviada a {self.orden.get('email_destino', '')} el {fecha_legible(self.orden['fecha_envio_email'])}."
            )
            self.lbl_envio.setStyleSheet("color: #15803d; font-weight: bold;")
            self.btn_enviar.setText("✉️ Reenviar al proveedor")
        else:
            self.lbl_envio.setText("⏳ Pendiente de envío al proveedor.")
            self.lbl_envio.setStyleSheet("color: #b45309; font-weight: bold;")
            self.btn_enviar.setText("✉️ Enviar al proveedor")

    def _ruta(self):
        try:
            return self.obtener_ruta()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener el archivo de la orden:\n{e}")
            return None

    def abrir_archivo(self):
        ruta = self._ruta()
        if ruta and not QDesktopServices.openUrl(QUrl.fromLocalFile(ruta)):
            QMessageBox.warning(self, "Abrir archivo", f"No se pudo abrir el archivo automáticamente.\nUbicación:\n{ruta}")

    def abrir_carpeta(self):
        ruta = self._ruta()
        if not ruta:
            return
        if sys.platform.startswith("win"):
            # Abre el Explorador con el archivo seleccionado
            QProcess.startDetached("explorer", [f"/select,{os.path.normpath(ruta)}"])
        elif not QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(ruta))):
            QMessageBox.warning(self, "Abrir carpeta", f"No se pudo abrir la carpeta.\nUbicación:\n{os.path.dirname(ruta)}")

    def enviar_orden(self):
        actualizada = self.enviar(self.orden, self)
        if actualizada:
            self.orden = actualizada
            self._actualizar_estado_envio()
