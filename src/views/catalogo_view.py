import os
from PyQt6.QtWidgets import (
    QWidget, QFileDialog, QMessageBox, QTableWidgetItem, QHeaderView,
    QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6 import uic

ESTILO_LISTA_HABILITADA = (
    "background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; "
    "border-radius: 6px; padding: 6px 10px; font-weight: bold;"
)
ESTILO_LISTA_CERRADA = (
    "background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; "
    "border-radius: 6px; padding: 6px 10px; font-weight: bold;"
)


class CatalogoView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catalogo.ui")
        uic.loadUi(ui_path, self)
        self.ruta_archivo_actual = None
        self.proveedores_info = {}  # {id_proveedor: dict}
        self.tabla_previa.setAlternatingRowColors(True)

        self._crear_fila_estado_lista()
        self.cmb_proveedor.currentIndexChanged.connect(self.actualizar_estado_lista)

    def _crear_fila_estado_lista(self):
        """Agrega, debajo del selector de proveedor, el estado de la lista y el botón Habilitar/Cerrar."""
        fila = QHBoxLayout()
        fila.setSpacing(10)

        self.lbl_estado_lista = QLabel()
        self.lbl_estado_lista.setWordWrap(True)
        fila.addWidget(self.lbl_estado_lista, 1)

        self.btn_toggle_lista = QPushButton()
        self.btn_toggle_lista.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_lista.setMinimumHeight(32)
        fila.addWidget(self.btn_toggle_lista)

        # Insertar inmediatamente después de la fila del selector de proveedor
        layout = self.verticalLayout
        indice = layout.count()
        for i in range(layout.count()):
            if layout.itemAt(i).layout() is self.layout_proveedor:
                indice = i + 1
                break
        layout.insertLayout(indice, fila)

    def cargar_proveedores(self, proveedores):
        """Puebla el ComboBox con los proveedores (conservando la selección) y su estado de lista."""
        seleccionado = self.cmb_proveedor.currentData()
        self.proveedores_info = {p['id_proveedor']: p for p in proveedores}

        self.cmb_proveedor.blockSignals(True)
        self.cmb_proveedor.clear()
        for prov in proveedores:
            icono = "🟢" if prov.get('lista_habilitada') else "🔒"
            self.cmb_proveedor.addItem(f"{icono} {prov['nombre']}", prov['id_proveedor'])
        idx = self.cmb_proveedor.findData(seleccionado)
        if idx >= 0:
            self.cmb_proveedor.setCurrentIndex(idx)
        self.cmb_proveedor.blockSignals(False)

        self.actualizar_estado_lista()

    def obtener_proveedor_seleccionado(self):
        """Retorna el id_proveedor seleccionado en el combo."""
        return self.cmb_proveedor.currentData()

    def obtener_info_proveedor_seleccionado(self):
        return self.proveedores_info.get(self.obtener_proveedor_seleccionado())

    def actualizar_estado_lista(self):
        """Muestra si la lista del proveedor seleccionado está habilitada o cerrada."""
        prov = self.obtener_info_proveedor_seleccionado()
        if not prov:
            self.lbl_estado_lista.setText("")
            self.btn_toggle_lista.setVisible(False)
            return

        self.btn_toggle_lista.setVisible(True)
        pendientes = prov.get('pedidos_pendientes', 0)
        if prov.get('lista_habilitada'):
            desde = prov.get('fecha_habilitacion') or '-'
            self.lbl_estado_lista.setText(
                f"🟢 Lista HABILITADA desde {desde}: los socios pueden cargar pedidos. "
                f"Pedidos pendientes: {pendientes}. Se cierra automáticamente al consolidar."
            )
            self.lbl_estado_lista.setStyleSheet(ESTILO_LISTA_HABILITADA)
            self.btn_toggle_lista.setText("🔒 Cerrar Lista")
        else:
            articulos = prov.get('total_articulos', 0)
            detalle = (f"{articulos} artículos cargados" if articulos
                       else "sin lista importada")
            self.lbl_estado_lista.setText(
                f"🔒 Lista CERRADA ({detalle}): los socios no la ven. "
                f"Importa una lista nueva o habilítala para abrir un nuevo ciclo de pedidos."
            )
            self.lbl_estado_lista.setStyleSheet(ESTILO_LISTA_CERRADA)
            self.btn_toggle_lista.setText("🟢 Habilitar Lista")

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
        """Muestra las filas leídas en la grilla de vista previa con alineación semántica."""
        self.tabla_previa.clear()
        self.tabla_previa.setColumnCount(len(headers))
        self.tabla_previa.setRowCount(len(filas))
        self.tabla_previa.setHorizontalHeaderLabels(headers)
        self.tabla_previa.setAlternatingRowColors(True)

        for r, fila in enumerate(filas):
            for c, val in enumerate(fila):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if c == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif c >= 3:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabla_previa.setItem(r, c, item)

        self.tabla_previa.resizeColumnsToContents()
        if len(headers) > 1:
            self.tabla_previa.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def limpiar_vista(self):
        """Limpia el archivo y la tabla."""
        self.ruta_archivo_actual = None
        self.lbl_archivo_seleccionado.setText("Ningún archivo seleccionado")
        self.tabla_previa.clear()
        self.tabla_previa.setRowCount(0)
        self.tabla_previa.setColumnCount(0)

    def confirmar_accion(self, titulo, mensaje):
        respuesta = QMessageBox.question(
            self, titulo, mensaje,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        return respuesta == QMessageBox.StandardButton.Yes

    def mostrar_mensaje_exito(self, mensaje):
        QMessageBox.information(self, "Operación Exitosa", mensaje)

    def mostrar_mensaje_error(self, mensaje):
        QMessageBox.critical(self, "Error", mensaje)
