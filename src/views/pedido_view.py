import os
from PyQt6.QtWidgets import QWidget, QMessageBox, QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6 import uic

class PedidoView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "carga_pedido.ui")
        uic.loadUi(ui_path, self)

        self.id_socio_actual = 1
        self.nombre_socio_actual = "Socio"
        self.catalogo_completo = []
        self.carrito = {} # {id_articulo: {'cantidad': int, 'precio': float, 'detalle': str}}

        # Conectar señal de cambio de ítem
        self.tabla_articulos.itemChanged.connect(self.al_cambiar_celda)

    def establecer_socio_actual(self, id_socio, nombre_socio=""):
        """Establece el socio actual conectado."""
        self.id_socio_actual = id_socio
        self.nombre_socio_actual = nombre_socio or f"Socio #{id_socio}"

    def obtener_id_socio(self):
        return self.id_socio_actual

    def cargar_proveedores_filtro(self, proveedores):
        """Puebla el ComboBox con los proveedores disponibles."""
        self.cmb_filtro_proveedor.blockSignals(True)
        self.cmb_filtro_proveedor.clear()
        self.cmb_filtro_proveedor.addItem("🔍 Todos los Proveedores", None)
        for p in proveedores:
            self.cmb_filtro_proveedor.addItem(p['nombre'], p['id_proveedor'])
        self.cmb_filtro_proveedor.blockSignals(False)

    def cargar_articulos(self, lista_articulos):
        """
        Guarda el catálogo recibido y puebla la tabla respetando las cantidades en carrito.
        """
        self.catalogo_completo = lista_articulos
        self.renderizar_tabla(lista_articulos)

    def renderizar_tabla(self, lista_articulos):
        """Dibuja las filas del catálogo en la tabla_articulos."""
        self.tabla_articulos.blockSignals(True)
        self.tabla_articulos.setRowCount(len(lista_articulos))
        
        for row, articulo in enumerate(lista_articulos):
            id_art = articulo['id_articulo']
            
            # Columna 0: Artículo (Detalle)
            item_articulo = QTableWidgetItem(articulo['detalle'])
            item_articulo.setData(Qt.ItemDataRole.UserRole, id_art)
            item_articulo.setFlags(item_articulo.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_articulos.setItem(row, 0, item_articulo)
            
            # Columna 1: Rubro
            item_rubro = QTableWidgetItem(articulo.get('rubro') or 'General')
            item_rubro.setFlags(item_rubro.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_articulos.setItem(row, 1, item_rubro)
            
            # Columna 2: Proveedor
            item_prov = QTableWidgetItem(articulo.get('proveedor_nombre') or 'General')
            item_prov.setFlags(item_prov.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_articulos.setItem(row, 2, item_prov)
            
            # Columna 3: Precio
            precio = articulo['precio_final']
            item_precio = QTableWidgetItem(f"${precio:,.2f}")
            item_precio.setData(Qt.ItemDataRole.UserRole, precio)
            item_precio.setFlags(item_precio.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_precio.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla_articulos.setItem(row, 3, item_precio)
            
            # Columna 4: Cantidad (Editable)
            cant_actual = self.carrito.get(id_art, {}).get('cantidad', 0)
            item_cantidad = QTableWidgetItem(str(cant_actual) if cant_actual > 0 else "")
            item_cantidad.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_articulos.setItem(row, 4, item_cantidad)
            
            # Columna 5: Subtotal
            subtotal = cant_actual * precio
            item_subtotal = QTableWidgetItem(f"${subtotal:,.2f}")
            item_subtotal.setFlags(item_subtotal.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_subtotal.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla_articulos.setItem(row, 5, item_subtotal)

        self.tabla_articulos.resizeColumnsToContents()
        self.tabla_articulos.blockSignals(False)
        self.calcular_totales()

    def al_cambiar_celda(self, item):
        """Captura cambios en la columna de Cantidad y actualiza el carrito."""
        if item.column() != 4:
            return
            
        row = item.row()
        item_articulo = self.tabla_articulos.item(row, 0)
        item_precio = self.tabla_articulos.item(row, 3)
        item_subtotal = self.tabla_articulos.item(row, 5)
        
        if not item_articulo or not item_precio or not item_subtotal:
            return
            
        id_articulo = item_articulo.data(Qt.ItemDataRole.UserRole)
        precio = item_precio.data(Qt.ItemDataRole.UserRole)
        texto_cant = item.text().strip()
        
        try:
            cant = int(texto_cant) if texto_cant else 0
            if cant < 0:
                cant = 0
                item.setText("")
        except ValueError:
            cant = 0
            item.setText("")

        if cant > 0:
            self.carrito[id_articulo] = {
                'id_articulo': id_articulo,
                'cantidad': cant,
                'precio': precio,
                'detalle': item_articulo.text()
            }
        else:
            self.carrito.pop(id_articulo, None)
            
        subtotal = cant * precio
        self.tabla_articulos.blockSignals(True)
        item_subtotal.setText(f"${subtotal:,.2f}")
        self.tabla_articulos.blockSignals(False)
        
        self.calcular_totales()

    def calcular_totales(self):
        """Calcula y muestra el monto acumulado del carrito."""
        total = sum(item['cantidad'] * item['precio'] for item in self.carrito.values())
        self.lbl_total.setText(f"Total Estimado: ${total:,.2f}")

    def obtener_articulos_seleccionados(self):
        """Devuelve los artículos del carrito con cantidad > 0."""
        return [
            {
                'id_articulo': item['id_articulo'],
                'cantidad': item['cantidad'],
                'detalle': item['detalle']
            }
            for item in self.carrito.values() if item['cantidad'] > 0
        ]

    def limpiar_formulario(self):
        """Vacía el carrito y restablece la tabla."""
        self.carrito.clear()
        self.renderizar_tabla(self.catalogo_completo)

    def mostrar_mensaje_exito(self, mensaje):
        QMessageBox.information(self, "Pedido Confirmado", mensaje)

    def mostrar_mensaje_error(self, mensaje):
        QMessageBox.critical(self, "Error", mensaje)
