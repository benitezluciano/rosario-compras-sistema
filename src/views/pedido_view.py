import os
from PyQt6.QtWidgets import QWidget, QMessageBox, QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6 import uic

class PedidoView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Obtiene la ruta absoluta de carga_pedido.ui en esta misma carpeta
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "carga_pedido.ui")
        
        # Carga el diseño .ui en esta instancia de QWidget
        uic.loadUi(ui_path, self)

        # Conectar la señal de cambio de ítem para calcular totales dinámicamente
        self.tabla_articulos.itemChanged.connect(self.calcular_totales)

    def obtener_id_socio(self):
        """
        Retorna el ID del socio actual del formulario.
        En este caso de uso inicial, retorna un ID fijo 1 (Socio por defecto).
        """
        return 1 

    def cargar_articulos(self, lista_articulos):
        """
        Configura y llena la tabla_articulos con el catálogo recibido.
        Configura la columna 'Cantidad' como editable y las demás como de solo lectura.
        """
        # Bloquear señales para evitar cálculos innecesarios mientras cargamos los datos
        self.tabla_articulos.blockSignals(True)
        
        self.tabla_articulos.setRowCount(len(lista_articulos))
        
        for row, articulo in enumerate(lista_articulos):
            # Columna 0: Artículo (Detalle)
            item_articulo = QTableWidgetItem(articulo['detalle'])
            # Guardamos el id_articulo de forma oculta en UserRole
            item_articulo.setData(Qt.ItemDataRole.UserRole, articulo['id_articulo'])
            item_articulo.setFlags(item_articulo.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_articulos.setItem(row, 0, item_articulo)
            
            # Columna 1: Rubro
            item_rubro = QTableWidgetItem(articulo.get('rubro') or 'General')
            item_rubro.setFlags(item_rubro.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_articulos.setItem(row, 1, item_rubro)
            
            # Columna 2: Precio
            precio = articulo['precio_final']
            item_precio = QTableWidgetItem(f"${precio:.2f}")
            # Guardamos el precio numérico para cálculos futuros
            item_precio.setData(Qt.ItemDataRole.UserRole, precio)
            item_precio.setFlags(item_precio.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_articulos.setItem(row, 2, item_precio)
            
            # Columna 3: Cantidad (Editable)
            item_cantidad = QTableWidgetItem("0")
            item_cantidad.setFlags(item_cantidad.flags() | Qt.ItemFlag.ItemIsEditable)
            self.tabla_articulos.setItem(row, 3, item_cantidad)
            
            # Columna 4: Subtotal (De solo lectura, inicializado a 0.00)
            item_subtotal = QTableWidgetItem("$0.00")
            item_subtotal.setFlags(item_subtotal.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_articulos.setItem(row, 4, item_subtotal)
            
        self.tabla_articulos.blockSignals(False)

    def calcular_totales(self, item):
        """
        Se ejecuta cada vez que cambia una celda. Si es de la columna 'Cantidad' (3),
        calcula el subtotal (Precio * Cantidad) y actualiza el total general estimado.
        """
        # Solo actuar cuando se modifica la columna de Cantidad (columna 3)
        if item.column() != 3:
            return
            
        row = item.row()
        item_precio = self.tabla_articulos.item(row, 2)
        item_subtotal = self.tabla_articulos.item(row, 4)
        
        if not item_precio or not item_subtotal:
            return
            
        # Obtener el precio guardado
        precio = item_precio.data(Qt.ItemDataRole.UserRole)
        
        # Validar la cantidad ingresada
        try:
            cantidad_texto = item.text().strip()
            cantidad = int(cantidad_texto) if cantidad_texto else 0
            if cantidad < 0:
                raise ValueError()
        except ValueError:
            # Si el valor ingresado es inválido o negativo, restablecer a 0
            cantidad = 0
            self.tabla_articulos.blockSignals(True)
            item.setText("0")
            self.tabla_articulos.blockSignals(False)
            
        # Calcular y actualizar subtotal de la fila
        subtotal = precio * cantidad
        
        self.tabla_articulos.blockSignals(True)
        item_subtotal.setText(f"${subtotal:.2f}")
        self.tabla_articulos.blockSignals(False)
        
        # Calcular y actualizar el Total Estimado general
        total_general = 0.0
        for r in range(self.tabla_articulos.rowCount()):
            item_sub = self.tabla_articulos.item(r, 4)
            if item_sub:
                try:
                    valor_sub = float(item_sub.text().replace('$', ''))
                    total_general += valor_sub
                except ValueError:
                    pass
                    
        self.lbl_total.setText(f"Total Estimado: ${total_general:.2f}")

    def obtener_articulos_seleccionados(self):
        """
        Recorre la tabla de artículos y devuelve aquellos cuya cantidad sea mayor que 0.
        Retorna una lista de diccionarios con formato:
            {
                'id_articulo': int, 
                'cantidad': int, 
                'detalle': str
            }
        """
        articulos_seleccionados = []
        for row in range(self.tabla_articulos.rowCount()):
            item_cantidad = self.tabla_articulos.item(row, 3)
            if item_cantidad:
                try:
                    cantidad = int(item_cantidad.text().strip())
                except ValueError:
                    cantidad = 0
                    
                if cantidad > 0:
                    item_articulo = self.tabla_articulos.item(row, 0)
                    id_articulo = item_articulo.data(Qt.ItemDataRole.UserRole)
                    detalle = item_articulo.text()
                    
                    articulos_seleccionados.append({
                        'id_articulo': id_articulo,
                        'cantidad': cantidad,
                        'detalle': detalle
                    })
        return articulos_seleccionados

    def mostrar_mensaje_exito(self, mensaje):
        """Muestra un pop-up informativo de éxito."""
        QMessageBox.information(self, "Éxito", mensaje)

    def mostrar_mensaje_error(self, mensaje):
        """Muestra un pop-up de advertencia o error."""
        QMessageBox.warning(self, "Error de Validación", mensaje)

    def limpiar_formulario(self):
        """
        Restablece todas las cantidades a '0', actualiza los subtotales a '$0.00'
        y el total general a '$0.00'.
        """
        self.tabla_articulos.blockSignals(True)
        for row in range(self.tabla_articulos.rowCount()):
            item_cantidad = self.tabla_articulos.item(row, 3)
            if item_cantidad:
                item_cantidad.setText("0")
            item_subtotal = self.tabla_articulos.item(row, 4)
            if item_subtotal:
                item_subtotal.setText("$0.00")
        self.tabla_articulos.blockSignals(False)
        self.lbl_total.setText("Total Estimado: $0.00")
