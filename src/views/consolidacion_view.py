import os
from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox, QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6 import uic

class ConsolidacionView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "consolidacion.ui")
        uic.loadUi(ui_path, self)

    def abrir_dialogo_guardar(self):
        """Abre cuadro de diálogo para guardar la planilla general."""
        ruta_archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Planilla Consolidada General",
            "Planilla_Consolidada_General.xlsx",
            "Archivos Excel (*.xlsx);;Archivos CSV (*.csv);;Todos los archivos (*)"
        )
        return ruta_archivo if ruta_archivo else None

    def abrir_dialogo_carpeta(self):
        """Abre cuadro de diálogo para seleccionar la carpeta donde exportar las órdenes."""
        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Carpeta para Órdenes por Proveedor"
        )
        return carpeta if carpeta else None

    def cargar_tabla_consolidado(self, items):
        """Puebla la tabla_consolidado con el resumen de demanda."""
        headers = ["ID Art.", "Artículo / Detalle", "Rubro", "Proveedor", "Cant. Total", "Precio Unit.", "Total Estimado", "Desglose Socios"]
        
        self.tabla_consolidado.clear()
        self.tabla_consolidado.setColumnCount(len(headers))
        self.tabla_consolidado.setRowCount(len(items))
        self.tabla_consolidado.setHorizontalHeaderLabels(headers)
        
        for r, item in enumerate(items):
            valores = [
                str(item.get('id_articulo', '')),
                str(item.get('articulo_detalle', '')),
                str(item.get('rubro', '')),
                str(item.get('proveedor_nombre', '')),
                str(item.get('cantidad_total', 0)),
                f"${item.get('precio_unitario', 0.0):,.2f}",
                f"${item.get('total_estimado', 0.0):,.2f}",
                str(item.get('detalle_socios', ''))
            ]
            
            for c, val in enumerate(valores):
                t_item = QTableWidgetItem(val)
                t_item.setFlags(t_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if c in [0, 4]:
                    t_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif c in [5, 6]:
                    t_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabla_consolidado.setItem(r, c, t_item)
                
        self.tabla_consolidado.resizeColumnsToContents()
        self.lbl_info_pedidos.setText(f"Artículos demandados en pedidos pendientes: {len(items)}")

    def confirmar_accion(self, titulo, mensaje):
        respuesta = QMessageBox.question(
            self,
            titulo,
            mensaje,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        return respuesta == QMessageBox.StandardButton.Yes

    def mostrar_mensaje_exito(self, mensaje):
        QMessageBox.information(self, "Operación Exitosa", mensaje)

    def mostrar_mensaje_error(self, mensaje):
        QMessageBox.critical(self, "Error", mensaje)
