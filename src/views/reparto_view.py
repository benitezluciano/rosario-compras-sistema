import os
from PyQt6.QtWidgets import QWidget, QMessageBox, QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6 import uic

class RepartoView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reparto_automatico.ui")
        uic.loadUi(ui_path, self)

    def cargar_articulos_recepcion(self, articulos):
        """Puebla la tabla_recepcion con las cantidades demandadas y el stock actual."""
        headers = ["ID Art.", "Artículo / Detalle", "Proveedor", "Cant. Demandada", "Stock Actual", "Stock Físico Recibido (Editable)"]
        self.tabla_recepcion.clear()
        self.tabla_recepcion.setColumnCount(len(headers))
        self.tabla_recepcion.setRowCount(len(articulos))
        self.tabla_recepcion.setHorizontalHeaderLabels(headers)

        for row, art in enumerate(articulos):
            id_art = art['id_articulo']
            
            # Col 0: ID
            item_id = QTableWidgetItem(str(id_art))
            item_id.setFlags(item_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_recepcion.setItem(row, 0, item_id)
            
            # Col 1: Detalle
            item_det = QTableWidgetItem(art['articulo_detalle'])
            item_det.setData(Qt.ItemDataRole.UserRole, id_art)
            item_det.setFlags(item_det.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_recepcion.setItem(row, 1, item_det)
            
            # Col 2: Proveedor
            item_prov = QTableWidgetItem(art.get('proveedor_nombre', ''))
            item_prov.setFlags(item_prov.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_recepcion.setItem(row, 2, item_prov)
            
            # Col 3: Cantidad Demandada
            item_dem = QTableWidgetItem(str(art['cantidad_demandada']))
            item_dem.setFlags(item_dem.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_dem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_recepcion.setItem(row, 3, item_dem)
            
            # Col 4: Stock Actual
            item_stk = QTableWidgetItem(str(art['cantidad_stock']))
            item_stk.setFlags(item_stk.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_stk.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_recepcion.setItem(row, 4, item_stk)
            
            # Col 5: Stock Físico Recibido (Editable, por defecto inicializado con la cantidad demandada)
            item_rec = QTableWidgetItem(str(art['cantidad_demandada']))
            item_rec.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_recepcion.setItem(row, 5, item_rec)

        self.tabla_recepcion.resizeColumnsToContents()

    def obtener_stock_ingresado(self):
        """Retorna un dict {id_articulo: cantidad_recibida}."""
        stock_map = {}
        for row in range(self.tabla_recepcion.rowCount()):
            item_det = self.tabla_recepcion.item(row, 1)
            item_rec = self.tabla_recepcion.item(row, 5)
            if item_det and item_rec:
                id_art = item_det.data(Qt.ItemDataRole.UserRole)
                try:
                    cant = int(item_rec.text().strip())
                    if cant < 0:
                        cant = 0
                except ValueError:
                    cant = 0
                stock_map[id_art] = cant
        return stock_map

    def cargar_pedidos(self, lista_pedidos):
        """Puebla la tabla_pedidos con los pedidos consolidados."""
        self.tabla_pedidos.setRowCount(len(lista_pedidos))
        for row, pedido in enumerate(lista_pedidos):
            item_id = QTableWidgetItem(str(pedido['id_pedido']))
            item_id.setFlags(item_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_pedidos.setItem(row, 0, item_id)
            
            item_socio = QTableWidgetItem(pedido['socio_nombre'])
            item_socio.setFlags(item_socio.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_pedidos.setItem(row, 1, item_socio)
            
            item_articulos = QTableWidgetItem(pedido['resumen_articulos'] or "Sin detalles")
            item_articulos.setFlags(item_articulos.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_pedidos.setItem(row, 2, item_articulos)
            
            item_estado = QTableWidgetItem(pedido['estado'])
            item_estado.setFlags(item_estado.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_estado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_pedidos.setItem(row, 3, item_estado)

        self.tabla_pedidos.resizeColumnsToContents()

    def mostrar_alerta_discrepancias(self, discrepancias):
        """Muestra diálogo modal con los ajustes calculados."""
        mensaje = "Se detectó faltante de stock físico para los siguientes artículos:\n\n"
        for d in discrepancias:
            mensaje += f"• {d['detalle']}: Solicitado: {d['solicitado']} | Físico disponible: {d['disponible']}\n"
        mensaje += "\nEl sistema aplicará el prorrateo proporcional equitativo.\n¿Deseas confirmar la emisión de remitos con estos ajustes?"

        respuesta = QMessageBox.question(
            self,
            "Alerta de Faltante de Stock - Prorrateo",
            mensaje,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        return respuesta == QMessageBox.StandardButton.Yes

    def mostrar_mensaje_exito(self, mensaje):
        QMessageBox.information(self, "Reparto Exitoso", mensaje)

    def mostrar_mensaje_error(self, mensaje):
        QMessageBox.critical(self, "Error", mensaje)
