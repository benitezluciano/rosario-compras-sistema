import os
from PyQt6.QtWidgets import QWidget, QMessageBox, QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6 import uic

class RepartoView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reparto_automatico.ui")
        uic.loadUi(ui_path, self)

        # Conectar cambios de celdas para validar diferencias en tiempo real
        self.tabla_recepcion.itemChanged.connect(self.al_cambiar_celda)

    def cargar_proveedores(self, proveedores):
        """Puebla el ComboBox con los proveedores."""
        self.cmb_proveedor_recepcion.blockSignals(True)
        self.cmb_proveedor_recepcion.clear()
        self.cmb_proveedor_recepcion.addItem("🔍 Todos los Proveedores", None)
        for p in proveedores:
            self.cmb_proveedor_recepcion.addItem(p['nombre'], p['id_proveedor'])
        self.cmb_proveedor_recepcion.blockSignals(False)

    def cargar_articulos_control(self, articulos):
        """Puebla la tabla de recepción con el doble control (compras y logística)."""
        headers = [
            "ID Art.", 
            "Artículo / Detalle", 
            "Proveedor", 
            "Cant. Pedida", 
            "Cant. Recibida (Logística)", 
            "Precio Pactado", 
            "Precio Facturado (Compras)", 
            "Control / Estado"
        ]
        self.tabla_recepcion.blockSignals(True)
        self.tabla_recepcion.clear()
        self.tabla_recepcion.setColumnCount(len(headers))
        self.tabla_recepcion.setRowCount(len(articulos))
        self.tabla_recepcion.setHorizontalHeaderLabels(headers)

        for row, art in enumerate(articulos):
            id_art = art['id_articulo']
            cant_ped = art['cantidad_demandada']
            prec_pact = art['precio_pactado']
            
            # Col 0: ID
            item_id = QTableWidgetItem(str(id_art))
            item_id.setData(Qt.ItemDataRole.UserRole, id_art)
            item_id.setFlags(item_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_recepcion.setItem(row, 0, item_id)
            
            # Col 1: Detalle
            item_det = QTableWidgetItem(art['articulo_detalle'])
            item_det.setFlags(item_det.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_recepcion.setItem(row, 1, item_det)
            
            # Col 2: Proveedor
            item_prov = QTableWidgetItem(art.get('proveedor_nombre', ''))
            item_prov.setFlags(item_prov.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_recepcion.setItem(row, 2, item_prov)
            
            # Col 3: Cantidad Pedida (Sólo lectura)
            item_ped = QTableWidgetItem(str(cant_ped))
            item_ped.setData(Qt.ItemDataRole.UserRole, cant_ped)
            item_ped.setFlags(item_ped.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_ped.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_recepcion.setItem(row, 3, item_ped)
            
            # Col 4: Cantidad Recibida (Editable por Logística, por defecto inicializada con lo pedido)
            item_rec = QTableWidgetItem(str(cant_ped))
            item_rec.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_recepcion.setItem(row, 4, item_rec)
            
            # Col 5: Precio Pactado (Sólo lectura)
            item_pact = QTableWidgetItem(f"${prec_pact:,.2f}")
            item_pact.setData(Qt.ItemDataRole.UserRole, prec_pact)
            item_pact.setFlags(item_pact.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_pact.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla_recepcion.setItem(row, 5, item_pact)
            
            # Col 6: Precio Facturado (Editable por Compras, por defecto igual al pactado)
            item_fact = QTableWidgetItem(f"{prec_pact:.2f}")
            item_fact.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla_recepcion.setItem(row, 6, item_fact)
            
            # Col 7: Control / Estado
            item_estado = QTableWidgetItem("✅ OK")
            item_estado.setFlags(item_estado.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_estado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_recepcion.setItem(row, 7, item_estado)

        self.tabla_recepcion.resizeColumnsToContents()
        self.tabla_recepcion.blockSignals(False)

    def al_cambiar_celda(self, item):
        """Monitorea modificaciones en columnas 4 (Cant. Recibida) y 6 (Precio Facturado)."""
        if item.column() not in [4, 6]:
            return
            
        row = item.row()
        item_ped = self.tabla_recepcion.item(row, 3)
        item_rec = self.tabla_recepcion.item(row, 4)
        item_pact = self.tabla_recepcion.item(row, 5)
        item_fact = self.tabla_recepcion.item(row, 6)
        item_estado = self.tabla_recepcion.item(row, 7)
        
        if not (item_ped and item_rec and item_pact and item_fact and item_estado):
            return

        try:
            cant_ped = item_ped.data(Qt.ItemDataRole.UserRole) or 0
            cant_rec = int(item_rec.text().strip()) if item_rec.text().strip() else 0
            prec_pact = item_pact.data(Qt.ItemDataRole.UserRole) or 0.0
            
            raw_fact = item_fact.text().replace('$', '').replace(' ', '').replace(',', '.')
            prec_fact = float(raw_fact) if raw_fact else 0.0
        except ValueError:
            return

        alertas = []
        if cant_rec < cant_ped:
            alertas.append(f"⚠️ Faltan {cant_ped - cant_rec}u")
        elif cant_rec > cant_ped:
            alertas.append(f"➕ Excedente {cant_rec - cant_ped}u")

        if abs(prec_fact - prec_pact) > 0.01:
            dif = prec_fact - prec_pact
            signo = "+" if dif > 0 else ""
            alertas.append(f"💲 Dif. Precio ({signo}${dif:,.2f})")

        self.tabla_recepcion.blockSignals(True)
        if alertas:
            item_estado.setText(" | ".join(alertas))
            item_estado.setForeground(QColor("#c0392b"))
        else:
            item_estado.setText("✅ OK")
            item_estado.setForeground(QColor("#27ae60"))
        self.tabla_recepcion.blockSignals(False)

    def obtener_items_para_asentar(self):
        """Retorna los datos de los renglones cargados en la tabla."""
        items = []
        for row in range(self.tabla_recepcion.rowCount()):
            item_id = self.tabla_recepcion.item(row, 0)
            item_ped = self.tabla_recepcion.item(row, 3)
            item_rec = self.tabla_recepcion.item(row, 4)
            item_pact = self.tabla_recepcion.item(row, 5)
            item_fact = self.tabla_recepcion.item(row, 6)
            
            if item_id and item_ped and item_rec and item_pact and item_fact:
                id_art = item_id.data(Qt.ItemDataRole.UserRole)
                cant_ped = item_ped.data(Qt.ItemDataRole.UserRole)
                
                try:
                    cant_rec = int(item_rec.text().strip()) if item_rec.text().strip() else 0
                except ValueError:
                    cant_rec = 0
                    
                prec_pact = item_pact.data(Qt.ItemDataRole.UserRole)
                try:
                    raw_fact = item_fact.text().replace('$', '').replace(' ', '').replace(',', '.')
                    prec_fact = float(raw_fact) if raw_fact else prec_pact
                except ValueError:
                    prec_fact = prec_pact
                    
                items.append({
                    'id_articulo': id_art,
                    'cantidad_pedida': cant_ped,
                    'cantidad_recibida': cant_rec,
                    'precio_pactado': prec_pact,
                    'precio_facturado': prec_fact
                })
        return items

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
            mensaje += f"• {d['detalle']}: Solicitado: {d['solicitado']} | Físico recibido: {d['disponible']}\n"
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
        QMessageBox.information(self, "Operación Exitosa", mensaje)

    def mostrar_mensaje_error(self, mensaje):
        QMessageBox.critical(self, "Error", mensaje)
