import os
from PyQt6.QtWidgets import (
    QWidget, 
    QMessageBox, 
    QTableWidget, 
    QTableWidgetItem, 
    QGroupBox, 
    QVBoxLayout, 
    QLabel,
    QHeaderView,
    QStyledItemDelegate,
    QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6 import uic

class CantidadDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return editor

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
        self.id_pedido_vigente = None
        self.codigo_pedido_vigente = None

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

    def establecer_pedido_vigente(self, pedido_vigente):
        """
        Carga el pedido vigente del socio si existe, permitiéndole modificarlo,
        o resetea el modo a nuevo pedido.
        """
        self.carrito.clear()
        
        if pedido_vigente:
            self.id_pedido_vigente = pedido_vigente['id_pedido']
            self.codigo_pedido_vigente = pedido_vigente.get('codigo_comercial', f"#{self.id_pedido_vigente}")
            
            # Poblar carrito con los ítems del pedido vigente
            items_pedidos = pedido_vigente.get('items', {})
            for art in self.catalogo_completo:
                id_art = art['id_articulo']
                if id_art in items_pedidos:
                    cant = items_pedidos[id_art]
                    self.carrito[id_art] = {
                        'id_articulo': id_art,
                        'cantidad': cant,
                        'precio': art['precio_final'],
                        'detalle': art['detalle']
                    }
                    
            self.lbl_banner_vigente.setText(
                f"📝 Modificando Pedido Vigente {self.codigo_pedido_vigente} (Estado: {pedido_vigente['estado']}). "
                f"Ajusta tus cantidades y presiona 'Guardar Modificaciones'."
            )
            self.lbl_banner_vigente.setStyleSheet(
                "background-color: #fef3c7; color: #92400e; border: 1px solid #fde68a; border-radius: 6px; padding: 8px 12px; font-weight: bold; font-size: 13px;"
            )
            self.btn_confirmar.setText("💾 Guardar Modificaciones del Pedido")
        else:
            self.id_pedido_vigente = None
            self.codigo_pedido_vigente = None
            self.lbl_banner_vigente.setText(
                "✨ No tienes pedidos pendientes. Ingresa las cantidades deseadas para emitir tu nuevo pedido."
            )
            self.lbl_banner_vigente.setStyleSheet(
                "background-color: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; border-radius: 6px; padding: 8px 12px; font-weight: bold; font-size: 13px;"
            )
            self.btn_confirmar.setText("🛒 Confirmar y Enviar Nuevo Pedido")

        # Actualizar celdas en todas las tablas de proveedores
        self.sincronizar_cantidades_en_tablas()
        self.calcular_totales()

    def cargar_articulos(self, lista_articulos):
        """Organiza y renderiza el catálogo segmentado con una tabla separada por cada Proveedor."""
        self.catalogo_completo = lista_articulos
        self.renderizar_tablas_por_proveedor(lista_articulos)

    def renderizar_tablas_por_proveedor(self, lista_articulos):
        """Crea dinámicamente un QGroupBox y un QTableWidget por cada proveedor."""
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
            tabla.verticalHeader().setDefaultSectionSize(36)
            tabla.setItemDelegateForColumn(3, CantidadDelegate(tabla))
            tabla.setStyleSheet("""
                QTableWidget {
                    background-color: #ffffff;
                    gridline-color: #e2e8f0;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                }
                QHeaderView::section {
                    background-color: #f1f5f9;
                    color: #334155;
                    font-weight: bold;
                    padding: 6px;
                    border: none;
                    border-bottom: 2px solid #cbd5e1;
                    border-right: 1px solid #e2e8f0;
                }
                QHeaderView::section:vertical {
                    background-color: #f8fafc;
                    color: #64748b;
                    font-weight: 600;
                    font-size: 11px;
                    padding: 4px;
                    border: none;
                    border-right: 1px solid #cbd5e1;
                    border-bottom: 1px solid #e2e8f0;
                }
                QTableCornerButton::section {
                    background-color: #f1f5f9;
                    border: none;
                    border-bottom: 2px solid #cbd5e1;
                    border-right: 1px solid #e2e8f0;
                }
                QTableWidget QLineEdit {
                    background-color: #ffffff;
                    color: #0f172a;
                    selection-background-color: #2563eb;
                    selection-color: #ffffff;
                    border: 2px solid #2563eb;
                    border-radius: 4px;
                    padding: 0px 4px;
                    margin: 0px;
                    font-size: 13px;
                    font-weight: bold;
                }
            """)

            tabla.blockSignals(True)
            for row, art in enumerate(articulos):
                id_art = art['id_articulo']
                precio = art['precio_final']

                item_art = QTableWidgetItem(art['detalle'])
                item_art.setData(Qt.ItemDataRole.UserRole, id_art)
                item_art.setFlags(item_art.flags() & ~Qt.ItemFlag.ItemIsEditable)
                tabla.setItem(row, 0, item_art)

                item_rub = QTableWidgetItem(art.get('rubro') or 'General')
                item_rub.setFlags(item_rub.flags() & ~Qt.ItemFlag.ItemIsEditable)
                tabla.setItem(row, 1, item_rub)

                item_pre = QTableWidgetItem(f"${precio:,.2f}")
                item_pre.setData(Qt.ItemDataRole.UserRole, precio)
                item_pre.setFlags(item_pre.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item_pre.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tabla.setItem(row, 2, item_pre)

                cant_actual = self.carrito.get(id_art, {}).get('cantidad', 0)
                item_cant = QTableWidgetItem(str(cant_actual) if cant_actual > 0 else "")
                item_cant.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tabla.setItem(row, 3, item_cant)

                subtot = cant_actual * precio
                item_sub = QTableWidgetItem(f"${subtot:,.2f}")
                item_sub.setFlags(item_sub.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item_sub.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tabla.setItem(row, 4, item_sub)

            tabla.blockSignals(False)
            tabla.itemChanged.connect(lambda item, t=tabla: self.al_cambiar_celda(t, item))

            self.tablas_proveedores[prov_id] = tabla
            layout_gb.addWidget(tabla)
            self.layout_tablas_proveedores.addWidget(group_box)

        self.layout_tablas_proveedores.addStretch()
        self.calcular_totales()

    def sincronizar_cantidades_en_tablas(self):
        """Actualiza los valores de las celdas de cantidad y subtotal según self.carrito."""
        for tabla in self.tablas_proveedores.values():
            tabla.blockSignals(True)
            for row in range(tabla.rowCount()):
                item_art = tabla.item(row, 0)
                item_pre = tabla.item(row, 2)
                item_cant = tabla.item(row, 3)
                item_sub = tabla.item(row, 4)
                
                if item_art and item_pre and item_cant and item_sub:
                    id_art = item_art.data(Qt.ItemDataRole.UserRole)
                    precio = item_pre.data(Qt.ItemDataRole.UserRole) or 0.0
                    cant = self.carrito.get(id_art, {}).get('cantidad', 0)
                    
                    item_cant.setText(str(cant) if cant > 0 else "")
                    item_sub.setText(f"${cant * precio:,.2f}")
            tabla.blockSignals(False)

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

    def cargar_historial_pedidos(self, historial):
        """Puebla la grilla de historial de pedidos para el socio."""
        headers = ["N° Pedido (Código)", "Fecha", "Estado", "Productos Solicitados", "Unidades", "Total Estimado ($)"]
        self.tabla_historial.clear()
        self.tabla_historial.setColumnCount(len(headers))
        self.tabla_historial.setRowCount(len(historial))
        self.tabla_historial.setHorizontalHeaderLabels(headers)
        self.tabla_historial.setAlternatingRowColors(True)

        self.tabla_historial.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        for row, ped in enumerate(historial):
            cod = ped.get('codigo_comercial') or f"RC-ORD-{ped['id_pedido']}"
            item_cod = QTableWidgetItem(cod)
            item_cod.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_historial.setItem(row, 0, item_cod)

            item_fec = QTableWidgetItem(str(ped.get('fecha', '-')))
            item_fec.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_historial.setItem(row, 1, item_fec)

            # Estado con color
            est = ped.get('estado', 'Pendiente')
            item_est = QTableWidgetItem(est)
            item_est.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if est == 'Pendiente':
                item_est.setForeground(QColor("#d97706"))
            elif est == 'Consolidado':
                item_est.setForeground(QColor("#2563eb"))
            elif est in ['Procesado', 'Repartido']:
                item_est.setForeground(QColor("#16a34a"))
            self.tabla_historial.setItem(row, 2, item_est)

            resumen = ped.get('resumen_productos') or f"{ped.get('cantidad_articulos', 0)} productos"
            item_res = QTableWidgetItem(str(resumen))
            self.tabla_historial.setItem(row, 3, item_res)

            item_uni = QTableWidgetItem(str(ped.get('total_unidades', 0)))
            item_uni.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_historial.setItem(row, 4, item_uni)

            tot = ped.get('total_estimado', 0.0)
            item_tot = QTableWidgetItem(f"${tot:,.2f}")
            item_tot.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla_historial.setItem(row, 5, item_tot)

        self.tabla_historial.resizeColumnsToContents()
        if len(historial) == 0:
            self.lbl_info_historial.setText("📋 Aún no posees pedidos registrados en el historial.")
        else:
            self.lbl_info_historial.setText(f"📋 Total de pedidos en tu historial: {len(historial)}")

    def limpiar_formulario(self):
        """Limpia el carrito y resetea las tablas."""
        self.carrito.clear()
        self.id_pedido_vigente = None
        self.codigo_pedido_vigente = None
        self.sincronizar_cantidades_en_tablas()
        self.calcular_totales()

    def mostrar_mensaje_exito(self, mensaje):
        QMessageBox.information(self, "Operación Exitosa", mensaje)

    def mostrar_mensaje_error(self, mensaje):
        QMessageBox.critical(self, "Error", mensaje)
