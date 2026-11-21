import os
from PyQt6.QtWidgets import QWidget, QMessageBox, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6 import uic


class HistorialView(QWidget):
    """Pantalla independiente con el historial de pedidos del socio."""

    def __init__(self, parent=None):
        super().__init__(parent)

        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historial_pedidos.ui")
        uic.loadUi(ui_path, self)

    def cargar_historial_pedidos(self, historial):
        """Puebla la grilla de historial de pedidos para el socio."""
        headers = ["N° Pedido (Código)", "Fecha", "Proveedor", "Estado", "Productos Solicitados", "Unidades", "Total Estimado ($)"]
        self.tabla_historial.clear()
        self.tabla_historial.setColumnCount(len(headers))
        self.tabla_historial.setRowCount(len(historial))
        self.tabla_historial.setHorizontalHeaderLabels(headers)
        self.tabla_historial.setAlternatingRowColors(True)

        for row, ped in enumerate(historial):
            cod = ped.get('codigo_comercial') or f"RC-ORD-{ped['id_pedido']}"
            item_cod = QTableWidgetItem(cod)
            item_cod.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_historial.setItem(row, 0, item_cod)

            item_fec = QTableWidgetItem(str(ped.get('fecha', '-')))
            item_fec.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_historial.setItem(row, 1, item_fec)

            item_prov = QTableWidgetItem(ped.get('proveedor_nombre') or '-')
            self.tabla_historial.setItem(row, 2, item_prov)

            # Estado con color
            est = ped.get('estado', 'Pendiente')
            item_est = QTableWidgetItem(est)
            item_est.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if est == 'Pendiente':
                item_est.setForeground(QColor("#d97706"))
            elif est == 'Consolidado':
                item_est.setForeground(QColor("#2563eb"))
            elif est in ['Procesado', 'Repartido']:
                item_est.setForeground(QColor("#16a34a"))
            self.tabla_historial.setItem(row, 3, item_est)

            resumen = ped.get('resumen_productos') or f"{ped.get('cantidad_articulos', 0)} productos"
            item_res = QTableWidgetItem(str(resumen))
            self.tabla_historial.setItem(row, 4, item_res)

            item_uni = QTableWidgetItem(str(ped.get('total_unidades', 0)))
            item_uni.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_historial.setItem(row, 5, item_uni)

            tot = ped.get('total_estimado', 0.0)
            item_tot = QTableWidgetItem(f"${tot:,.2f}")
            item_tot.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla_historial.setItem(row, 6, item_tot)

        self.tabla_historial.resizeColumnsToContents()
        self.tabla_historial.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        if len(historial) == 0:
            self.lbl_info_historial.setText("📋 Aún no posees pedidos registrados en el historial.")
        else:
            self.lbl_info_historial.setText(f"📋 Total de pedidos en tu historial: {len(historial)}")

    def mostrar_mensaje_error(self, mensaje):
        QMessageBox.critical(self, "Error", mensaje)
