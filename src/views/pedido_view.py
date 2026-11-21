import os
from PyQt6.QtWidgets import (
    QWidget,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QHeaderView,
    QStyledItemDelegate,
    QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6 import uic


class CantidadDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return editor


ESTILO_TABLA = """
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
"""

ESTILO_ESTADO_VIGENTE = (
    "background-color: #fef3c7; color: #92400e; border: 1px solid #fde68a; "
    "border-radius: 6px; padding: 6px 10px; font-weight: bold; font-size: 12px;"
)
ESTILO_ESTADO_NUEVO = (
    "background-color: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; "
    "border-radius: 6px; padding: 6px 10px; font-weight: bold; font-size: 12px;"
)
ESTILO_BTN_HOJA = (
    "QPushButton { background-color: #0f766e; color: #ffffff; font-weight: bold; "
    "padding: 7px 16px; border-radius: 6px; }"
    "QPushButton:hover { background-color: #115e59; }"
)


class PedidoView(QWidget):
    """
    Portal del socio: una hoja (pestaña inferior estilo Excel) por cada lista habilitada.
    Cada hoja es un pedido independiente para ese proveedor. El socio puede enviar
    hoja por hoja o usar "Enviar todo" (que igual genera pedidos separados por proveedor).
    """

    # Emitida al presionar "Enviar pedido de esta hoja" (argumento: id_proveedor)
    enviar_hoja_solicitado = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "carga_pedido.ui")
        uic.loadUi(ui_path, self)

        self.id_socio_actual = 1
        self.nombre_socio_actual = "Socio"
        self.rol_usuario_actual = "socio"
        self.catalogo_completo = []
        self.carrito = {}  # {id_articulo: {'id_articulo', 'cantidad', 'precio', 'detalle', 'id_proveedor'}}
        self.tablas_proveedores = {}  # {id_proveedor: QTableWidget}
        # Hojas por proveedor: orden de pestañas, nombres, precios, widgets auxiliares
        self.ids_hojas = []            # [id_proveedor] en el orden de las pestañas
        self.nombres_hojas = {}        # {id_proveedor: nombre}
        self.precios_por_hoja = {}     # {id_proveedor: {id_articulo: precio}}
        self.lbl_subtotales_hoja = {}  # {id_proveedor: QLabel}
        self.lbl_estado_hoja = {}      # {id_proveedor: QLabel}
        self.btn_enviar_hoja = {}      # {id_proveedor: QPushButton}
        self.pedidos_vigentes = {}     # {id_proveedor: pedido 'Pendiente'}

        self.btn_confirmar.setText("🛒 Enviar Todo (un pedido por proveedor)")

    # ------------------------------------------------------------------
    # Socio actual
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Pedidos vigentes (uno por proveedor)
    # ------------------------------------------------------------------

    def establecer_pedidos_vigentes(self, pedidos_vigentes):
        """
        Carga en el carrito los pedidos 'Pendiente' del socio (uno por proveedor)
        para que pueda modificarlos, y actualiza el estado de cada hoja.
        """
        self.pedidos_vigentes = pedidos_vigentes or {}
        self.carrito.clear()

        for art in self.catalogo_completo:
            id_art = art['id_articulo']
            ped = self.pedidos_vigentes.get(art['id_proveedor'])
            if ped and id_art in ped.get('items', {}):
                self.carrito[id_art] = {
                    'id_articulo': id_art,
                    'cantidad': ped['items'][id_art],
                    'precio': art['precio_final'],
                    'detalle': art['detalle'],
                    'id_proveedor': art['id_proveedor'],
                }

        # Banner general
        vigentes_visibles = [p for pid, p in self.pedidos_vigentes.items() if pid in self.ids_hojas]
        if vigentes_visibles:
            self.lbl_banner_vigente.setText(
                f"📝 Tienes {len(vigentes_visibles)} pedido(s) pendiente(s). Puedes modificarlos hasta que el "
                f"Ejecutivo los consolide. Cada hoja es un pedido independiente para ese proveedor."
            )
            self.lbl_banner_vigente.setStyleSheet(ESTILO_ESTADO_VIGENTE.replace("12px", "13px"))
        else:
            self.lbl_banner_vigente.setText(
                "✨ No tienes pedidos pendientes. Carga cantidades en la hoja de cada proveedor y "
                "envía hoja por hoja o todo junto."
            )
            self.lbl_banner_vigente.setStyleSheet(ESTILO_ESTADO_NUEVO.replace("12px", "13px"))

        # Estado y botón de cada hoja
        for prov_id in self.ids_hojas:
            ped = self.pedidos_vigentes.get(prov_id)
            lbl = self.lbl_estado_hoja.get(prov_id)
            btn = self.btn_enviar_hoja.get(prov_id)
            if ped:
                if lbl:
                    lbl.setText(
                        f"📝 Pedido vigente {ped['codigo_comercial']} (Estado: {ped['estado']}). "
                        f"Modifica las cantidades y guarda los cambios. Si dejas todo en 0, el pedido se anula."
                    )
                    lbl.setStyleSheet(ESTILO_ESTADO_VIGENTE)
                if btn:
                    btn.setText(f"💾 Guardar Cambios del Pedido {ped['codigo_comercial']}")
            else:
                if lbl:
                    lbl.setText("✨ Sin pedido para este proveedor. Ingresa cantidades para emitir uno nuevo.")
                    lbl.setStyleSheet(ESTILO_ESTADO_NUEVO)
                if btn:
                    btn.setText("📤 Enviar Pedido de esta Hoja")

        self.sincronizar_cantidades_en_tablas()
        self.calcular_totales()

    def obtener_cambios_por_hoja(self, id_proveedor=None):
        """
        Compara el carrito contra los pedidos vigentes y devuelve las hojas con cambios:
        {id_proveedor: {'accion': 'nuevo'|'modificar'|'anular', 'items': [(id_articulo, cantidad)],
                        'nombre': str, 'total': float, 'codigo': str|None}}
        Si se indica id_proveedor, solo evalúa esa hoja.
        """
        hojas = [id_proveedor] if id_proveedor is not None else list(self.ids_hojas)
        cambios = {}
        for prov_id in hojas:
            precios = self.precios_por_hoja.get(prov_id, {})
            items = []
            total = 0.0
            for id_art, precio in precios.items():
                cant = self.carrito.get(id_art, {}).get('cantidad', 0)
                if cant > 0:
                    items.append((id_art, cant))
                    total += cant * precio

            vigente = self.pedidos_vigentes.get(prov_id)
            items_vigentes = dict(vigente['items']) if vigente else {}

            if vigente and not items:
                accion = 'anular'
            elif vigente and dict(items) != items_vigentes:
                accion = 'modificar'
            elif not vigente and items:
                accion = 'nuevo'
            else:
                continue  # Sin cambios en esta hoja

            cambios[prov_id] = {
                'accion': accion,
                'items': items,
                'nombre': self.nombres_hojas.get(prov_id, "Proveedor"),
                'total': total,
                'codigo': vigente['codigo_comercial'] if vigente else None,
            }
        return cambios

    def hoja_tiene_pedido_vigente(self, id_proveedor):
        return id_proveedor in self.pedidos_vigentes

    # ------------------------------------------------------------------
    # Hojas por proveedor
    # ------------------------------------------------------------------

    def cargar_articulos(self, lista_articulos):
        """Organiza y renderiza el catálogo con una hoja por cada lista habilitada."""
        self.catalogo_completo = lista_articulos
        self.renderizar_tablas_por_proveedor(lista_articulos)

    def renderizar_tablas_por_proveedor(self, lista_articulos):
        """Crea dinámicamente una hoja (pestaña inferior estilo Excel) por cada proveedor."""
        # Recordar la hoja visible para restaurarla tras el re-renderizado
        idx_previo = self.tabs_proveedores.currentIndex()
        prov_previo = self.ids_hojas[idx_previo] if 0 <= idx_previo < len(self.ids_hojas) else None

        while self.tabs_proveedores.count():
            hoja = self.tabs_proveedores.widget(0)
            self.tabs_proveedores.removeTab(0)
            hoja.deleteLater()

        self.tablas_proveedores.clear()
        self.ids_hojas = []
        self.nombres_hojas.clear()
        self.precios_por_hoja.clear()
        self.lbl_subtotales_hoja.clear()
        self.lbl_estado_hoja.clear()
        self.btn_enviar_hoja.clear()

        # Agrupar artículos por Proveedor
        por_proveedor = {}
        for art in lista_articulos:
            prov_id = art.get('id_proveedor', 0)
            por_proveedor.setdefault(prov_id, {
                'nombre': art.get('proveedor_nombre', 'General'),
                'articulos': []
            })['articulos'].append(art)

        headers = ["Artículo / Producto", "Rubro", "Precio Unitario", "Cantidad a Pedir", "Subtotal"]

        if not por_proveedor:
            hoja_vacia = QWidget()
            layout_vacia = QVBoxLayout(hoja_vacia)
            lbl_vacia = QLabel("📭 No hay listas de precios habilitadas en este momento.\n"
                               "Recibirás una notificación cuando el Ejecutivo habilite una nueva lista.")
            lbl_vacia.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_vacia.setStyleSheet("color: #64748b; font-size: 13px; font-weight: bold;")
            layout_vacia.addWidget(lbl_vacia)
            self.tabs_proveedores.addTab(hoja_vacia, "Sin listas habilitadas")

        for prov_id, prov_data in por_proveedor.items():
            prov_nombre = prov_data['nombre']
            articulos = prov_data['articulos']

            hoja = QWidget()
            layout_hoja = QVBoxLayout(hoja)
            layout_hoja.setContentsMargins(10, 10, 10, 8)
            layout_hoja.setSpacing(6)

            lbl_titulo_hoja = QLabel(f"🏢 Lista de Precios: {prov_nombre}")
            lbl_titulo_hoja.setStyleSheet("font-size: 13px; font-weight: bold; color: #1e3a8a;")
            layout_hoja.addWidget(lbl_titulo_hoja)

            lbl_estado = QLabel()
            lbl_estado.setWordWrap(True)
            layout_hoja.addWidget(lbl_estado)

            tabla = QTableWidget()
            tabla.setColumnCount(len(headers))
            tabla.setRowCount(len(articulos))
            tabla.setHorizontalHeaderLabels(headers)
            tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            for col in range(1, len(headers)):
                tabla.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
            tabla.verticalHeader().setDefaultSectionSize(36)
            tabla.setItemDelegateForColumn(3, CantidadDelegate(tabla))
            tabla.setStyleSheet(ESTILO_TABLA)

            self.precios_por_hoja[prov_id] = {}

            tabla.blockSignals(True)
            for row, art in enumerate(articulos):
                id_art = art['id_articulo']
                precio = art['precio_final']
                self.precios_por_hoja[prov_id][id_art] = precio

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

                item_sub = QTableWidgetItem(f"${cant_actual * precio:,.2f}")
                item_sub.setFlags(item_sub.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item_sub.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tabla.setItem(row, 4, item_sub)

            tabla.blockSignals(False)
            tabla.itemChanged.connect(lambda item, t=tabla, p=prov_id: self.al_cambiar_celda(t, item, p))
            layout_hoja.addWidget(tabla)

            # Pie de la hoja: subtotal + botón de envío individual
            pie = QHBoxLayout()
            btn_hoja = QPushButton("📤 Enviar Pedido de esta Hoja")
            btn_hoja.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_hoja.setStyleSheet(ESTILO_BTN_HOJA)
            btn_hoja.clicked.connect(lambda _checked=False, p=prov_id: self.enviar_hoja_solicitado.emit(p))
            pie.addWidget(btn_hoja)
            pie.addStretch()
            lbl_subtotal = QLabel()
            lbl_subtotal.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl_subtotal.setStyleSheet("font-size: 12px; font-weight: bold; color: #334155; padding: 2px 4px;")
            pie.addWidget(lbl_subtotal)
            layout_hoja.addLayout(pie)

            self.tablas_proveedores[prov_id] = tabla
            self.lbl_subtotales_hoja[prov_id] = lbl_subtotal
            self.lbl_estado_hoja[prov_id] = lbl_estado
            self.btn_enviar_hoja[prov_id] = btn_hoja
            self.nombres_hojas[prov_id] = prov_nombre
            self.ids_hojas.append(prov_id)
            self.tabs_proveedores.addTab(hoja, prov_nombre)

        if prov_previo in self.ids_hojas:
            self.tabs_proveedores.setCurrentIndex(self.ids_hojas.index(prov_previo))

        self.btn_confirmar.setEnabled(bool(self.ids_hojas))
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

    def al_cambiar_celda(self, tabla, item, id_proveedor):
        """Maneja el ingreso de cantidades en la tabla correspondiente."""
        if item.column() != 3:
            return

        row = item.row()
        item_art = tabla.item(row, 0)
        item_pre = tabla.item(row, 2)
        if not (item_art and item_pre):
            return

        id_articulo = item_art.data(Qt.ItemDataRole.UserRole)
        precio = item_pre.data(Qt.ItemDataRole.UserRole) or 0.0
        texto_cant = item.text().strip()

        try:
            cant = int(texto_cant) if texto_cant else 0
            cant = max(cant, 0)
        except ValueError:
            cant = 0

        if cant > 0:
            self.carrito[id_articulo] = {
                'id_articulo': id_articulo,
                'cantidad': cant,
                'precio': precio,
                'detalle': item_art.text(),
                'id_proveedor': id_proveedor,
            }
        else:
            self.carrito.pop(id_articulo, None)

        self.sincronizar_cantidades_en_tablas()
        self.calcular_totales()

    def calcular_totales(self):
        """Calcula el total general y, por cada hoja, su subtotal y el contador de productos cargados."""
        total = sum(item['cantidad'] * item['precio'] for item in self.carrito.values())
        self.lbl_total.setText(f"Total General Estimado: ${total:,.2f}")

        for idx, prov_id in enumerate(self.ids_hojas):
            precios = self.precios_por_hoja.get(prov_id, {})
            cantidad_productos = 0
            subtotal_hoja = 0.0
            for id_art, precio in precios.items():
                cant = self.carrito.get(id_art, {}).get('cantidad', 0)
                if cant > 0:
                    cantidad_productos += 1
                    subtotal_hoja += cant * precio

            nombre = self.nombres_hojas.get(prov_id, "Proveedor")
            prefijo = "📝 " if prov_id in self.pedidos_vigentes else ""
            etiqueta = f"{prefijo}{nombre} ({cantidad_productos})" if cantidad_productos > 0 else f"{prefijo}{nombre}"
            self.tabs_proveedores.setTabText(idx, etiqueta)

            lbl_sub = self.lbl_subtotales_hoja.get(prov_id)
            if lbl_sub:
                lbl_sub.setText(f"Subtotal de esta hoja: ${subtotal_hoja:,.2f}")

    # ------------------------------------------------------------------
    # Mensajes
    # ------------------------------------------------------------------

    def confirmar_accion(self, titulo, mensaje):
        respuesta = QMessageBox.question(
            self, titulo, mensaje,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        return respuesta == QMessageBox.StandardButton.Yes

    def mostrar_mensaje_info(self, mensaje):
        QMessageBox.information(self, "Información", mensaje)

    def mostrar_mensaje_exito(self, mensaje):
        QMessageBox.information(self, "Operación Exitosa", mensaje)

    def mostrar_mensaje_error(self, mensaje):
        QMessageBox.critical(self, "Error", mensaje)
