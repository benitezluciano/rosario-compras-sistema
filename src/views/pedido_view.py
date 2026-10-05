import os
from PyQt6.QtWidgets import (
    QWidget, 
    QMessageBox, 
    QTableWidget, 
    QTableWidgetItem, 
    QGroupBox, 
    QVBoxLayout, 
    QLabel,
    QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6 import uic

class PedidoView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "carga_pedido.ui")
        uic.loadUi(ui_path, self)

        self.id_socio_actual = 1
        self.nombre_socio_actual = "Socio"
        self.rol_usuario_actual = "socio"
        self.catalogo_completo = []
        self.carrito = {} # {id_articulo: {'cantidad': int, 'precio': float, 'detalle': str}}
        self.tablas_proveedores = {} # {id_proveedor: QTableWidget}

    def establecer_socio_actual(self, id_socio, nombre_socio="", rol="socio"):
        """Establece el usuario actual y ajusta la visibilidad del selector de socio."""
        self.id_socio_actual = id_socio
        self.nombre_socio_actual = nombre_socio or f"Socio #{id_socio}"
        self.rol_usuario_actual = rol

        if rol == 'socio':
            self.lbl_socio_actual.setText(f"👤 Socio: {self.nombre_socio_actual}")
            self.cmb_socio_seleccion.setVisible(False)
        else:
            self.lbl_socio_actual.setText("👤 Cargar Pedido en nombre de Socio:")
            self.cmb_socio_seleccion.setVisible(True)

    def cargar_socios_selector(self, socios):
        """Puebla el ComboBox con los socios disponibles para el Ejecutivo."""
        self.cmb_socio_seleccion.blockSignals(True)
        self.cmb_socio_seleccion.clear()
        for s in socios:
            self.cmb_socio_seleccion.addItem(f"{s['nombre']} ({s['email']})", s['id'])
        
        # Seleccionar por defecto el socio actual si existe
        idx = self.cmb_socio_seleccion.findData(self.id_socio_actual)
        if idx >= 0:
            self.cmb_socio_seleccion.setCurrentIndex(idx)
        self.cmb_socio_seleccion.blockSignals(False)

    def obtener_id_socio(self):
        """Retorna el ID del socio al que se le cargará el pedido."""
        if self.rol_usuario_actual in ['ejecutivo', 'admin'] and self.cmb_socio_seleccion.isVisible():
            socio_id = self.cmb_socio_seleccion.currentData()
            if socio_id:
                return socio_id
        return self.id_socio_actual

    def cargar_articulos(self, lista_articulos):
        """
        Organiza y renderiza el catálogo segmentado con una lista/tabla separada por cada Proveedor.
        """
        self.catalogo_completo = lista_articulos
        self.renderizar_tablas_por_proveedor(lista_articulos)

    def renderizar_tablas_por_proveedor(self, lista_articulos):
        """
        Crea dinámicamente un QGroupBox y un QTableWidget por cada proveedor.
        """
        # Limpiar layout anterior
        while self.layout_tablas_proveedores.count():
            child = self.layout_tablas_proveedores.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.tablas_proveedores.clear()

        # Agrupar artículos por Proveedor
        por_proveedor = {}
        for art in lista_articulos:
            prov_nom = art.get('proveedor_nombre', 'General')
            prov_id = art.get('id_proveedor', 0)
            if prov_id not in por_proveedor:
                por_proveedor[prov_id] = {
                    'nombre': prov_nom,
                    'articulos': []
                }
            por_proveedor[prov_id]['articulos'].append(art)

        headers = ["Artículo / Producto", "Rubro", "Precio Unitario", "Cantidad a Pedir", "Subtotal"]

        for prov_id, prov_data in por_proveedor.items():
            prov_nombre = prov_data['nombre']
            articulos = prov_data['articulos']

            # Crear contenedor GroupBox para este Proveedor
            group_box = QGroupBox(f"🏢 Lista de Precios: {prov_nombre}")
            group_box.setStyleSheet("""
                QGroupBox {
                    font-size: 13px;
                    font-weight: bold;
                    color: #1e3a8a;
                    border: 2px solid #cbd5e1;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 15px;
                    background-color: #ffffff;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 4px 10px;
                    background-color: #e0e7ff;
                    border-radius: 4px;
                }
            """)

            layout_gb = QVBoxLayout(group_box)
            layout_gb.setContentsMargins(10, 15, 10, 10)

            # Crear Tabla para este Proveedor
            tabla = QTableWidget()
            tabla.setColumnCount(len(headers))
            tabla.setRowCount(len(articulos))
            tabla.setHorizontalHeaderLabels(headers)
            tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            tabla.setMinimumHeight(45 + (len(articulos) * 36))
            tabla.setStyleSheet("""
                QTableWidget {
                    gridline-color: #e2e8f0;
                    border: 1px solid #e2e8f0;
                    border-radius: 4px;
                }
                QHeaderView::section {
                    background-color: #f1f5f9;
                    font-weight: bold;
                    padding: 4px;
                    border: 1px solid #cbd5e1;
                }
            """)

            tabla.blockSignals(True)
            for row, art in enumerate(articulos):
                id_art = art['id_articulo']
                precio = art['precio_final']

                # Col 0: Artículo
                item_art = QTableWidgetItem(art['detalle'])
                item_art.setData(Qt.ItemDataRole.UserRole, id_art)
                item_art.setFlags(item_art.flags() & ~Qt.ItemFlag.ItemIsEditable)
                tabla.setItem(row, 0, item_art)

                # Col 1: Rubro
                item_rub = QTableWidgetItem(art.get('rubro') or 'General')
                item_rub.setFlags(item_rub.flags() & ~Qt.ItemFlag.ItemIsEditable)
                tabla.setItem(row, 1, item_rub)

                # Col 2: Precio Unit.
                item_pre = QTableWidgetItem(f"${precio:,.2f}")
                item_pre.setData(Qt.ItemDataRole.UserRole, precio)
                item_pre.setFlags(item_pre.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item_pre.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tabla.setItem(row, 2, item_pre)

                # Col 3: Cantidad (Editable)
                cant_actual = self.carrito.get(id_art, {}).get('cantidad', 0)
                item_cant = QTableWidgetItem(str(cant_actual) if cant_actual > 0 else "")
                item_cant.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tabla.setItem(row, 3, item_cant)

                # Col 4: Subtotal
                subtot = cant_actual * precio
                item_sub = QTableWidgetItem(f"${subtot:,.2f}")
                item_sub.setFlags(item_sub.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item_sub.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tabla.setItem(row, 4, item_sub)

            tabla.blockSignals(False)

            # Conectar cambio de celda
            tabla.itemChanged.connect(lambda item, t=tabla: self.al_cambiar_celda(t, item))

            self.tablas_proveedores[prov_id] = tabla
            layout_gb.addWidget(tabla)
            self.layout_tablas_proveedores.addWidget(group_box)

        self.layout_tablas_proveedores.addStretch()
        self.calcular_totales()

    def al_cambiar_celda(self, tabla, item):
        """Maneja el ingreso de cantidades en la tabla correspondiente."""
        if item.column() != 3:
            return

        row = item.row()
        item_art = tabla.item(row, 0)
        item_pre = tabla.item(row, 2)
        item_sub = tabla.item(row, 4)

        if not (item_art and item_pre and item_sub):
            return

        id_articulo = item_art.data(Qt.ItemDataRole.UserRole)
        precio = item_pre.data(Qt.ItemDataRole.UserRole) or 0.0
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
                'detalle': item_art.text()
            }
        else:
            self.carrito.pop(id_articulo, None)

        subtotal = cant * precio
        tabla.blockSignals(True)
        item_sub.setText(f"${subtotal:,.2f}")
        tabla.blockSignals(False)

        self.calcular_totales()

    def calcular_totales(self):
        """Calcula y muestra el total acumulado de todos los proveedores."""
        total = sum(item['cantidad'] * item['precio'] for item in self.carrito.values())
        self.lbl_total.setText(f"Total General Estimado: ${total:,.2f}")

    def obtener_articulos_seleccionados(self):
        """Devuelve los artículos seleccionados con cantidad > 0 de todos los proveedores."""
        return [
            {
                'id_articulo': item['id_articulo'],
                'cantidad': item['cantidad'],
                'detalle': item['detalle']
            }
            for item in self.carrito.values() if item['cantidad'] > 0
        ]

    def limpiar_formulario(self):
        """Limpia el carrito y las cantidades de todas las tablas."""
        self.carrito.clear()
        for tabla in self.tablas_proveedores.values():
            tabla.blockSignals(True)
            for r in range(tabla.rowCount()):
                item_cant = tabla.item(r, 3)
                item_sub = tabla.item(r, 4)
                if item_cant:
                    item_cant.setText("")
                if item_sub:
                    item_sub.setText("$0.00")
            tabla.blockSignals(False)
        self.calcular_totales()

    def mostrar_mensaje_exito(self, mensaje):
        QMessageBox.information(self, "Pedido Confirmado", mensaje)

    def mostrar_mensaje_error(self, mensaje):
        QMessageBox.critical(self, "Error", mensaje)
