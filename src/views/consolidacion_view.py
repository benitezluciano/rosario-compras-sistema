import os
from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox, QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6 import uic

class ConsolidacionView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Obtiene la ruta absoluta de consolidacion.ui en esta misma carpeta
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "consolidacion.ui")
        
        # Carga el diseño .ui en esta instancia de QWidget
        uic.loadUi(ui_path, self)

    def abrir_dialogo_archivo(self):
        """
        Abre el cuadro de diálogo nativo del sistema operativo para seleccionar un archivo.
        Retorna la ruta absoluta del archivo seleccionado o None si el usuario cancela.
        """
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Planilla de Proveedor",
            "",
            "Archivos Excel/CSV (*.xlsx *.xls *.csv);;Todos los archivos (*)"
        )
        return ruta_archivo if ruta_archivo else None

    def actualizar_archivo_seleccionado(self, nombre_archivo):
        """Actualiza la etiqueta de la interfaz con el nombre o ruta del archivo."""
        self.lbl_archivo_seleccionado.setText(nombre_archivo)

    def cargar_tabla_previa(self, headers, filas):
        """
        Limpia la tabla_previa, define sus dimensiones y la puebla con
        las cabeceras y las primeras 10 filas en formato de solo lectura.
        """
        self.tabla_previa.clear()
        
        # Configurar dimensiones de la grilla
        self.tabla_previa.setColumnCount(len(headers))
        self.tabla_previa.setRowCount(len(filas))
        
        # Configurar títulos de las columnas
        self.tabla_previa.setHorizontalHeaderLabels(headers)
        
        # Rellenar cada celda con sus valores correspondientes
        for r, fila in enumerate(filas):
            for c, valor in enumerate(fila):
                item = QTableWidgetItem(str(valor))
                # Bloquear edición para que sea estrictamente de solo lectura
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tabla_previa.setItem(r, c, item)
                
        # Redimensionar columnas al tamaño de su contenido
        self.tabla_previa.resizeColumnsToContents()

    def mostrar_mensaje_exito(self, mensaje):
        """Muestra una ventana emergente indicando éxito."""
        QMessageBox.information(self, "Éxito", mensaje)

    def mostrar_mensaje_error(self, mensaje):
        """Muestra una ventana emergente indicando un error."""
        QMessageBox.critical(self, "Error", mensaje)
