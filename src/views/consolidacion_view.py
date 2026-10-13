import os
from PyQt6.QtWidgets import QWidget, QFileDialog, QMessageBox, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6 import uic

class ConsolidacionView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "consolidacion.ui")
        uic.loadUi(ui_path, self)
        
        self.tabla_consolidado.setAlternatingRowColors(True)
        self.tabla_consolidado.verticalHeader().setDefaultSectionSize(36)
        self.socios_actuales = []
        self.articulos_actuales = []
        
        # Conectar cambio de celda para recalcular la suma y detectar ajustes
        self.tabla_consolidado.itemChanged.connect(self.al_cambiar_celda)

    def cargar_proveedores(self, proveedores):
        """Puebla el ComboBox con los proveedores."""
        self.cmb_proveedor.blockSignals(True)
        self.cmb_proveedor.clear()
        for prov in proveedores:
            self.cmb_proveedor.addItem(f"🏢 {prov['nombre']}", prov['id_proveedor'])
        self.cmb_proveedor.blockSignals(False)

    def obtener_proveedor_seleccionado(self):
        """Retorna el id_proveedor seleccionado en el combo."""
        return self.cmb_proveedor.currentData()

    def cargar_matriz_proveedor(self, datos_matriz):
        """
        Renderiza la matriz consolidada por proveedor:
        Columnas: Código | Artículo / Producto | Precio Unit. | Total Cantidad (Suma) | [Columna por cada Socio]
        (Sin columna Rubro).
        """
        self.socios_actuales = datos_matriz.get('socios', [])
        self.articulos_actuales = datos_matriz.get('articulos', [])

        headers = ["Código", "Artículo / Producto", "Precio Unit.", "Total Cantidad (Suma)"]
        for s in self.socios_actuales:
            headers.append(f"👤 {s['nombre']}")

        self.tabla_consolidado.blockSignals(True)
        self.tabla_consolidado.clear()
        self.tabla_consolidado.setColumnCount(len(headers))
        self.tabla_consolidado.setRowCount(len(self.articulos_actuales))
        self.tabla_consolidado.setHorizontalHeaderLabels(headers)
        self.tabla_consolidado.setAlternatingRowColors(True)

        self.tabla_consolidado.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        font_bold = QFont()
        font_bold.setBold(True)

        for row, art in enumerate(self.articulos_actuales):
            id_art = art['id_articulo']
            precio = art['precio_unitario']
            total_cant = art['total_cantidad']

            # Col 0: Código
            item_cod = QTableWidgetItem(art['codigo'])
            item_cod.setFlags(item_cod.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_cod.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_consolidado.setItem(row, 0, item_cod)

            # Col 1: Detalle
            item_det = QTableWidgetItem(art['detalle'])
            item_det.setFlags(item_det.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_consolidado.setItem(row, 1, item_det)

            # Col 2: Precio Unitario
            item_pre = QTableWidgetItem(f"${precio:,.2f}")
            item_pre.setData(Qt.ItemDataRole.UserRole, precio)
            item_pre.setFlags(item_pre.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_pre.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla_consolidado.setItem(row, 2, item_pre)

            # Col 3: Total Cantidad (Suma) - Destacada visualmente
            item_tot = QTableWidgetItem(str(total_cant))
            item_tot.setFont(font_bold)
            item_tot.setForeground(QColor("#1e3a8a"))
            item_tot.setBackground(QColor("#eff6ff"))
            item_tot.setFlags(item_tot.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_tot.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_consolidado.setItem(row, 3, item_tot)

            # Col 4+: Columnas de cada Socio (Editables por el Ejecutivo)
            for idx_s, s in enumerate(self.socios_actuales):
                col_idx = 4 + idx_s
                s_id = s['id']
                info_s = art['cantidades_por_socio'].get(s_id, {'cantidad': 0, 'id_pedido': s['id_pedido']})
                cant_s = info_s['cantidad']
                id_ped = info_s.get('id_pedido', s['id_pedido'])

                item_s = QTableWidgetItem(str(cant_s) if cant_s > 0 else "")
                item_s.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Guardar metadatos para rastreo y auditoría
                meta = {
                    'id_articulo': id_art,
                    'detalle': art['detalle'],
                    'id_socio': s_id,
                    'id_pedido': id_ped,
                    'cant_original': cant_s
                }
                item_s.setData(Qt.ItemDataRole.UserRole, meta)
                
                if cant_s > 0:
                    item_s.setBackground(QColor("#f8fafc"))
                    item_s.setFont(font_bold)
                    
                self.tabla_consolidado.setItem(row, col_idx, item_s)

        self.tabla_consolidado.resizeColumnsToContents()
        self.tabla_consolidado.blockSignals(False)

        total_articulos_pedidos = sum(1 for a in self.articulos_actuales if a['total_cantidad'] > 0)
        self.lbl_info_pedidos.setText(
            f"📋 {total_articulos_pedidos} productos con demanda activa para este proveedor entre {len(self.socios_actuales)} socios con pedidos pendientes."
        )
        self.lbl_estado_ajustes.setText("")

    def al_cambiar_celda(self, item):
        """Al modificar una celda de socio (col >= 4), recalcula la columna suma (col 3) y marca cambios."""
        col = item.column()
        if col < 4:
            return

        row = item.row()
        meta = item.data(Qt.ItemDataRole.UserRole)
        if not meta:
            return

        texto = item.text().strip()
        try:
            cant_nueva = int(texto) if texto else 0
            if cant_nueva < 0:
                cant_nueva = 0
                item.setText("")
        except ValueError:
            cant_nueva = 0
            item.setText("")

        # Recalcular la suma de la fila (col 3)
        suma_fila = 0
        for c in range(4, self.tabla_consolidado.columnCount()):
            c_item = self.tabla_consolidado.item(row, c)
            if c_item and c_item.text().strip():
                try:
                    suma_fila += int(c_item.text().strip())
                except ValueError:
                    pass

        self.tabla_consolidado.blockSignals(True)
        item_tot = self.tabla_consolidado.item(row, 3)
        if item_tot:
            item_tot.setText(str(suma_fila))
            if suma_fila > 0:
                item_tot.setBackground(QColor("#eff6ff"))
            else:
                item_tot.setBackground(QColor("#ffffff"))

        # Marcar visualmente si difiere del valor original
        cant_orig = meta.get('cant_original', 0)
        if cant_nueva != cant_orig:
            item.setBackground(QColor("#fef3c7")) # Amarillo tenue de edición
            item.setForeground(QColor("#b45309"))
        else:
            item.setBackground(QColor("#ffffff") if cant_orig == 0 else QColor("#f8fafc"))
            item.setForeground(QColor("#1e293b"))

        self.tabla_consolidado.blockSignals(False)

        # Verificar si hay cambios en toda la tabla
        mods = self.obtener_modificaciones_pendientes()
        if mods:
            self.lbl_estado_ajustes.setText(f"⚠️ {len(mods)} ajuste(s) pendiente(s) de guardar.")
            self.lbl_estado_ajustes.setStyleSheet("color: #b45309; font-weight: bold;")
        else:
            self.lbl_estado_ajustes.setText("")

    def obtener_modificaciones_pendientes(self):
        """Retorna la lista de cambios realizados por el ejecutivo respecto a las cantidades originales."""
        modificaciones = []
        for row in range(self.tabla_consolidado.rowCount()):
            for col in range(4, self.tabla_consolidado.columnCount()):
                item = self.tabla_consolidado.item(row, col)
                if not item:
                    continue
                meta = item.data(Qt.ItemDataRole.UserRole)
                if not meta:
                    continue

                texto = item.text().strip()
                try:
                    cant_nueva = int(texto) if texto else 0
                except ValueError:
                    cant_nueva = 0

                cant_orig = meta.get('cant_original', 0)
                if cant_nueva != cant_orig:
                    modificaciones.append({
                        'id_pedido': meta['id_pedido'],
                        'id_socio': meta['id_socio'],
                        'id_articulo': meta['id_articulo'],
                        'detalle': meta['detalle'],
                        'cant_anterior': cant_orig,
                        'cant_nueva': cant_nueva
                    })
        return modificaciones

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
