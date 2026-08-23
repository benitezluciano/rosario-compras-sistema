import os
from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox, QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6 import uic

class CatalogoView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catalogo.ui")
        uic.loadUi(ui_path, self)
        self.ruta_archivo_actual = None

    def cargar_proveedores(self, proveedores):
        """Puebla el ComboBox con los proveedores."""
        self.cmb_proveedor.clear()
        for prov in proveedores:
            self.cmb_proveedor.addItem(prov['nombre'], prov['id_proveedor'])

    def obtener_proveedor_seleccionado(self):
        """Retorna el id_proveedor seleccionado en el combo."""
        return self.cmb_proveedor.currentData()

    def abrir_dialogo_archivo(self):
        """Abre el diálogo para seleccionar la planilla."""
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Lista de Precios de Proveedor",
            "",
            "Archivos Excel/CSV (*.xlsx *.xls *.csv);;Todos los archivos (*)"
        )
        if ruta_archivo:
            self.ruta_archivo_actual = ruta_archivo
            self.lbl_archivo_seleccionado.setText(os.path.basename(ruta_archivo))
        return ruta_archivo

    def cargar_tabla_previa(self, headers, filas):
        """Muestra las filas leídas en la grilla de vista previa."""
        self.tabla_previa.clear()
        self.tabla_previa.setColumnCount(len(headers))
        self.tabla_previa.setRowCount(len(filas))
        self.tabla_previa.setHorizontalHeaderLabels(headers)
        
        for r, fila in enumerate(filas):
            for c, val in enumerate(fila):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tabla_previa.setItem(r, c, item)
                
        self.tabla_previa.resizeColumnsToContents()

    def limpiar_vista(self):
        """Limpia el archivo y la tabla."""
        self.ruta_archivo_actual = None
        self.lbl_archivo_seleccionado.setText("Ningún archivo seleccionado")
        self.tabla_previa.clear()
        self.tabla_previa.setRowCount(0)
        self.tabla_previa.setColumnCount(0)

    def mostrar_mensaje_exito(self, mensaje):
        QMessageBox.information(self, "Importación Exitosa", mensaje)

    def mostrar_mensaje_error(self, mensaje):
        QMessageBox.critical(self, "Error", mensaje)
